"""Run one blinded reviewer-control session through native Opus 5 / xhigh.

The oracle is never copied into the reviewer workspace. Preserve the first
attempt, including malformed judgments and timeout; this is client-reported
native evidence, not hosted/custodian attestation.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

from native_pilot import EXE,MODEL,EFFORT,safe_path,exclusive_json
from reviewer_controls import score


def run(controls,output,timeout=480):
    source=safe_path(controls);target=safe_path(output)
    if not 30<=timeout<=900:raise ValueError('bounded timeout required')
    target.mkdir(parents=True,exist_ok=False)
    exclusive_json(target/'reserved.json',{'reserved_at':dt.datetime.now(dt.timezone.utc).isoformat(),'source_class':'public-synthetic-reviewer-controls'})
    stage=target/'workspace';stage.mkdir()
    for name in ('tasks.json','prompt.txt','response-schema.json'):(stage/name).write_bytes((source/'reviewer-input'/name).read_bytes())
    settings={'disableAllHooks':True,'autoMemoryEnabled':False,'effortLevel':EFFORT,
              'permissions':{'defaultMode':'dontAsk','blockReadsOutsideWorkingDirectories':True}}
    exclusive_json(target/'settings.json',settings);exclusive_json(target/'empty-mcp.json',{'mcpServers':{}})
    env=os.environ.copy()
    overrides={'CLAUDE_CODE_EFFORT_LEVEL':EFFORT,'CLAUDE_CODE_DISABLE_AUTO_MEMORY':'1','CLAUDE_CODE_DISABLE_BACKGROUND_TASKS':'1',
               'CLAUDE_CODE_DISABLE_CRON':'1','CLAUDE_CODE_DISABLE_CLAUDE_MDS':'1'}
    env.update(overrides)
    for key in ('ANTHROPIC_BASE_URL','ANTHROPIC_API_KEY','ANTHROPIC_AUTH_TOKEN','CLAUDE_CODE_USE_BEDROCK','CLAUDE_CODE_USE_VERTEX','CLAUDE_CODE_USE_FOUNDRY'):env.pop(key,None)
    auth=subprocess.run([str(EXE),'auth','status'],env=env,capture_output=True,text=True,timeout=30)
    try:state=json.loads(auth.stdout)
    except ValueError:state={}
    if auth.returncode or state.get('loggedIn') is not True or state.get('apiProvider')!='firstParty' or state.get('authMethod') not in ('claude.ai','oauth'):
        exclusive_json(target/'receipt.json',{'status':'failed','reason':'first_party_subscription_unverified'})
        return {'status':'failed','reason':'first_party_subscription_unverified'}
    cmd=[str(EXE),'--restricted','-p','--model',MODEL,'--effort',EFFORT,'--tools','Read','--allowedTools','Read',
         '--permission-mode','dontAsk','--disable-slash-commands','--strict-mcp-config','--mcp-config',str(target/'empty-mcp.json'),
         '--settings',str(target/'settings.json'),'--no-session-persistence','--max-turns','12','--output-format','stream-json','--verbose']
    help_result=subprocess.run([str(EXE),'--help'],capture_output=True,text=True,timeout=30)
    if help_result.returncode or '--json-schema' not in help_result.stdout:
        exclusive_json(target/'receipt.json',{'status':'failed','reason':'structured_output_cli_unavailable'})
        return {'status':'failed','reason':'structured_output_cli_unavailable'}
    cmd.extend(['--json-schema',(stage/'response-schema.json').read_text(encoding='ascii')])
    started=dt.datetime.now(dt.timezone.utc).isoformat();timer=time.monotonic();models=set();reads=[];texts=[];result={};errors=[];stderr_bytes=0
    def stdout_reader(stream):
        nonlocal result
        for line in stream:
            if len(line)>2_000_000:errors.append('oversized_provider_event');continue
            try:event=json.loads(line)
            except ValueError:errors.append('malformed_provider_event');continue
            if event.get('type')=='assistant':
                msg=event.get('message',{})
                if msg.get('model'):models.add(msg['model'])
                for block in msg.get('content',[]):
                    if block.get('type')=='text':texts.append(block.get('text',''))
                    elif block.get('type')=='tool_use' and block.get('name')=='Read':
                        path=Path(block.get('input',{}).get('file_path',''))
                        path=(stage/path).resolve() if not path.is_absolute() else path.resolve()
                        reads.append(path.name if path.is_relative_to(stage) and path.name in ('tasks.json','prompt.txt','response-schema.json') else 'outside_input_read_attempt')
            elif event.get('type')=='result':result={k:event.get(k) for k in ('result','structured_output','is_error','modelUsage','num_turns','subtype')}
    def stderr_reader(stream):
        nonlocal stderr_bytes
        for part in iter(lambda:stream.read(8192),b''):stderr_bytes+=len(part)
    process=subprocess.Popen(cmd,cwd=stage,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out=threading.Thread(target=stdout_reader,args=(process.stdout,),daemon=True);err=threading.Thread(target=stderr_reader,args=(process.stderr,),daemon=True)
    out.start();err.start();process.stdin.write((stage/'prompt.txt').read_bytes());process.stdin.close()
    print(json.dumps({'status':'native-reviewer-running','pid':process.pid,'model':MODEL,'effort':EFFORT,'timeout_seconds':timeout}),flush=True)
    try:process.wait(timeout=timeout);status='completed' if process.returncode==0 else 'failed'
    except subprocess.TimeoutExpired:process.kill();process.wait();status='timeout'
    out.join(timeout=10);err.join(timeout=10)
    if out.is_alive():status='failed';errors.append('unclosed_provider_stream')
    if not models or any(m!=MODEL for m in models):status='failed';errors.append('model_unverified_or_substituted')
    if 'outside_input_read_attempt' in reads:status='failed';errors.append('reviewer_boundary_violation')
    if result.get('is_error'):status='failed';errors.append('provider_reported_error')
    answer=result.get('result') or (texts[-1] if texts else '')
    receipt={'schema':'osanwe.native-reviewer-attempt/1','status':status,'started_at':started,'ended_at':dt.datetime.now(dt.timezone.utc).isoformat(),
             'elapsed_seconds':time.monotonic()-timer,'returncode':process.returncode,'model_ids':sorted(models),'requested_model':MODEL,'requested_effort':EFFORT,
             'provider_effort_attested':False,'custody':'local client reported','source_class':'public-synthetic','binary_sha256':hashlib.sha256(EXE.read_bytes()).hexdigest(),
             'input_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in stage.iterdir()},'reads':reads,
             'usage':result.get('modelUsage'),'num_turns':result.get('num_turns'),'stderr_bytes_omitted':stderr_bytes,'errors':errors,'delivered_text':answer,
             'structured_output':result.get('structured_output'),'producer_version':2,'exact_output_schema':True,
             'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    exclusive_json(target/'receipt.json',receipt)
    # Only after the native session ends may the parent scorer load its oracle.
    if status=='completed':
        try:
            verdict=result.get('structured_output')
            if not isinstance(verdict,dict):raise ValueError('schema-conforming provider output missing')
            scored=score(json.loads((source/'oracle.json').read_text()),verdict)
            exclusive_json(target/'verdict.json',verdict);exclusive_json(target/'calibration.json',scored)
            return {'status':status,'controls_pass':scored['controls_pass'],'correct':scored['correct'],'total':48,'output':str(target)}
        except (ValueError,TypeError,KeyError):
            exclusive_json(target/'calibration.json',{'controls_pass':False,'status':'malformed_verdict','total':48,'correct':0})
            return {'status':'malformed_verdict','controls_pass':False,'total':48,'output':str(target)}
    exclusive_json(target/'calibration.json',{'controls_pass':False,'status':status,'total':48,'correct':0})
    return {'status':status,'controls_pass':False,'total':48,'output':str(target)}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--controls',required=True);p.add_argument('--output',required=True);p.add_argument('--timeout',type=int,default=480)
    a=p.parse_args();r=run(a.controls,a.output,a.timeout);print(json.dumps(r,sort_keys=True));sys.exit(0 if r.get('controls_pass') else 2)
