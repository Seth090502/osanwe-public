"""Frozen, public-development-only native Opus 5 / xhigh comparison runner.

No sealed admission material, brokerage data, original holdout, model fallback,
server independence claim, or repeated failed attempt. Local receipts are mutable
client evidence and cannot establish independent evaluation custody.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parent
ARMS = ('baseline', 'revised_no_library', 'revised_library')
MODEL = 'claude-opus-5'
EFFORT = 'xhigh'
EXE = Path('/path/to/home/.local/bin/claude.exe')
USAGE_COUNTERS = ('inputTokens','cacheCreationInputTokens','cacheReadInputTokens','outputTokens','thinkingTokens','webSearchRequests')


def dump(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def safe_path(path):
    value=Path(path).resolve()
    bad={'.raw','private','finance','credentials','holdout','holdouts','hidden','locked'}
    if any(x.lower() in bad for x in value.parts) or value.name.lower().startswith('.env') or value.name.lower()=='auth.json' or value.name.lower().endswith('.local.md'):
        raise ValueError('protected path is outside the native pilot input contract')
    return value


def exclusive_json(path, value):
    with path.open('x',encoding='ascii',newline='\n') as handle:
        handle.write(dump(value)+'\n'); handle.flush(); os.fsync(handle.fileno())


def prepare(config_path, output):
    cfg=json.loads(safe_path(config_path).read_text(encoding='utf-8'))
    if set(cfg) != {'arms','timeout_seconds','max_turns','seed'} or set(cfg['arms']) != set(ARMS):
        raise ValueError('config must define all three frozen arms and equal resource limits')
    if not 30 <= cfg['timeout_seconds'] <= 900 or not 1 <= cfg['max_turns'] <= 24 or not isinstance(cfg['seed'],int):
        raise ValueError('invalid frozen resource limits')
    pack=json.loads((ROOT/'development_cases.json').read_text(encoding='ascii'))
    if pack['admission_eligible'] or len(pack['cases']) != 36:
        raise ValueError('runner accepts only the public 36-case development pack')
    target=safe_path(output); target.mkdir(parents=True,exist_ok=False)
    assets={}; arms={}
    for arm in ARMS:
        entry=cfg['arms'][arm]
        if set(entry) != {'instructions','library'} or not entry['instructions']:
            raise ValueError('each arm needs explicit instruction and library file lists')
        if arm=='revised_no_library' and entry['library']:
            raise ValueError('no-library arm may not receive library files')
        directory=target/'frozen'/arm; directory.mkdir(parents=True)
        instructions=[]; libraries=[]
        for kind, dest in [('instructions',instructions),('library',libraries)]:
            for index,source in enumerate(entry[kind]):
                path=safe_path(source)
                if not path.is_file() or path.stat().st_size>512000:
                    raise ValueError('frozen inputs must be explicit bounded public files')
                data=path.read_bytes()
                relative=f'frozen/{arm}/{kind}-{index:02}-{path.name}'
                (target/relative).write_bytes(data); assets[relative]=sha(data); dest.append(relative)
        arms[arm]={'instructions':instructions,'library':libraries}
    opportunities=[]
    for c in pack['cases']:
        for arm in ARMS:
            opportunities.append({'case_id':c['id'],'family':c['family'],'scenario_family':c['scenario_family'],
                                  'source_family':c['source_family'],'arm':arm,'id':uuid.uuid4().hex})
    random.Random(cfg['seed']).shuffle(opportunities)
    # Snapshot both public tasks and exposed oracle into parent-only frozen storage.
    # A run copies input alone into its child workspace.
    exclusive_json(target/'development_cases.json',pack)
    manifest={'schema':'osanwe.native-development-pilot/1','created_at':now(),'model_id':MODEL,'effort':EFFORT,
              'evidence_class':'public-development-client-reported','admission_eligible':False,
              'timeout_seconds':cfg['timeout_seconds'],'max_turns':cfg['max_turns'],'seed':cfg['seed'],
              'arms':arms,'assets':assets,'cases_sha256':sha((target/'development_cases.json').read_bytes()),
              'runner_sha256':sha(Path(__file__).read_bytes()),'binary_sha256':sha(EXE.read_bytes()) if EXE.is_file() else None,
              'grader_sha256':sha((ROOT/'service/worker.mjs').read_bytes()),
              'grade_bridge_sha256':sha((ROOT/'score_native.mjs').read_bytes()),
              'opportunities':opportunities,'denominator':108,
              'inference_input_contract':'task input plus arm instructions and approved library only; no oracle',
              'limits':'public exposed controls; no independent performance or production eligibility'}
    exclusive_json(target/'manifest.json',manifest)
    # Keep the exact version executable for historical validation after future
    # producer/service changes. This does not modify or refund old opportunities.
    for relative in ('native_pilot.py','score_native.mjs','service/worker.mjs'):
        archived=target/'runtime'/relative;archived.parent.mkdir(parents=True,exist_ok=True)
        archived.write_bytes((ROOT/relative).read_bytes())
    (target/'attempts').mkdir()
    return {'status':'frozen','path':str(target/'manifest.json'),'opportunities':108,'manifest_sha256':sha((target/'manifest.json').read_bytes())}


def validate_plan(target):
    target=safe_path(target); m=json.loads((target/'manifest.json').read_text())
    if m['schema']!='osanwe.native-development-pilot/1' or m['admission_eligible'] or m['model_id']!=MODEL or m['effort']!=EFFORT or len(m['opportunities'])!=108:
        raise ValueError('invalid frozen pilot')
    for path,expected in m['assets'].items():
        p=safe_path(target/path)
        if not p.is_relative_to(target) or sha(p.read_bytes())!=expected:
            raise ValueError('frozen instructions changed')
    if sha((target/'development_cases.json').read_bytes())!=m['cases_sha256'] or sha(Path(__file__).read_bytes())!=m['runner_sha256']:
        raise ValueError('frozen tasks or runner changed; keep original failed campaign and freeze a new candidate')
    if sha((ROOT/'service/worker.mjs').read_bytes())!=m['grader_sha256'] or sha((ROOT/'score_native.mjs').read_bytes())!=m['grade_bridge_sha256']:
        raise ValueError('frozen grading code changed')
    return target,m


def run_one(target,m,opportunity):
    directory=target/'attempts'/opportunity['id']
    directory.mkdir(exist_ok=False)
    # Reservation is durable before any child receives input. Existing attempt
    # directories cannot be retried; a crash is an interrupted spent opportunity.
    exclusive_json(directory/'reserved.json',{'opportunity':opportunity,'reserved_at':now(),'manifest_sha256':sha((target/'manifest.json').read_bytes())})
    stage=directory/'workspace'; stage.mkdir()
    pack=json.loads((target/'development_cases.json').read_text())
    c=next(c for c in pack['cases'] if c['id']==opportunity['case_id'])
    exclusive_json(stage/'task.json',c['input'])
    arm=m['arms'][opportunity['arm']]
    sections=[]; approved={'task.json'}
    for path in arm['instructions']:
        sections.append((target/path).read_text(encoding='utf-8'))
    (stage/'contract.txt').write_text('\n\n'.join(sections),encoding='utf-8')
    approved.add('contract.txt')
    library=[]
    for index,path in enumerate(arm['library']):
        name=f'library-{index:02}{Path(path).suffix}'
        (stage/name).write_bytes((target/path).read_bytes()); library.append(name); approved.add(name)
    settings={'disableAllHooks':True,'autoMemoryEnabled':False,'effortLevel':EFFORT,
              'permissions':{'defaultMode':'dontAsk','blockReadsOutsideWorkingDirectories':True}}
    exclusive_json(directory/'settings.json',settings); exclusive_json(directory/'empty-mcp.json',{'mcpServers':{}})
    prompt=("This is a public synthetic financial reasoning task. Read task.json. Use the frozen instructions where applicable. "
            "Read relevant available library files only if useful. Available library files: "+dump(library)+". "
            "No outside files, web requests, account access, actions or persistent writes are permitted. "
            "Answer every supported obligation; withhold only unsupported parts. Return ONE JSON object with keys answers and report. "
            "answers is a list of objects with exactly id, status (answered or withheld), value (number, boolean, null or a task vocabulary item), "
            "and evidence_ids (source IDs inspected). Withheld values must be null. report is a concise financial explanation, including limitations "
            "and which assumptions would change the answer. Do not output a numeric answer inside a string. No Markdown fences.")
    (directory/'prompt.txt').write_text(prompt,encoding='ascii')
    command=[str(EXE),'--restricted','-p','--model',MODEL,'--effort',EFFORT,'--tools','Read','--allowedTools','Read',
             '--permission-mode','dontAsk','--disable-slash-commands','--strict-mcp-config','--mcp-config',str(directory/'empty-mcp.json'),
             '--settings',str(directory/'settings.json'),'--no-session-persistence','--max-turns',str(m['max_turns']),
             '--output-format','stream-json','--verbose','--append-system-prompt-file',str(stage/'contract.txt')]
    env=os.environ.copy()
    overrides={'CLAUDE_CODE_EFFORT_LEVEL':EFFORT,'CLAUDE_CODE_DISABLE_AUTO_MEMORY':'1','CLAUDE_CODE_DISABLE_BACKGROUND_TASKS':'1',
               'CLAUDE_CODE_DISABLE_CRON':'1','CLAUDE_CODE_DISABLE_CLAUDE_MDS':'1'}
    env.update(overrides)
    # Require subscription routing; inherited alternate-provider/API variables
    # must not silently turn the pilot into paid or proxy model inference.
    for key in ('ANTHROPIC_BASE_URL','ANTHROPIC_API_KEY','ANTHROPIC_AUTH_TOKEN','CLAUDE_CODE_USE_BEDROCK','CLAUDE_CODE_USE_VERTEX','CLAUDE_CODE_USE_FOUNDRY'):
        env.pop(key,None)
    started=now(); monotonic=time.monotonic(); texts=[]; models=set(); reads=[]; result={}; errors=[]
    process=None; status='failed'; stderr_size=0
    def drain_stdout(stream):
        nonlocal result
        for line in stream:
            if len(line)>2_000_000: errors.append('oversized_provider_event'); continue
            try: event=json.loads(line)
            except ValueError: errors.append('malformed_provider_event'); continue
            if event.get('type')=='assistant':
                message=event.get('message',{}); model=message.get('model')
                if model: models.add(model)
                for block in message.get('content',[]):
                    if block.get('type')=='text': texts.append(block.get('text',''))
                    elif block.get('type')=='tool_use' and block.get('name')=='Read':
                        raw=block.get('input',{}).get('file_path','')
                        try:
                            path=Path(raw); path=(stage/path).resolve() if not path.is_absolute() else path.resolve()
                            relative=str(path.relative_to(stage)).replace('\\','/')
                            reads.append(relative if relative in approved else 'unapproved_read_attempt')
                        except ValueError: reads.append('unapproved_read_attempt')
            elif event.get('type')=='result':
                result={k:event.get(k) for k in ('subtype','is_error','result','modelUsage','num_turns','duration_ms')}
    def drain_stderr(stream):
        nonlocal stderr_size
        for chunk in iter(lambda:stream.read(8192),b''): stderr_size+=len(chunk)
    try:
        process=subprocess.Popen(command,cwd=stage,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout=threading.Thread(target=drain_stdout,args=(process.stdout,),daemon=True)
        stderr=threading.Thread(target=drain_stderr,args=(process.stderr,),daemon=True)
        stdout.start();stderr.start();process.stdin.write(prompt.encode('ascii'));process.stdin.close()
        try: process.wait(timeout=m['timeout_seconds']); status='completed' if process.returncode==0 else 'failed'
        except subprocess.TimeoutExpired: process.kill();process.wait();status='timeout'
        stdout.join(timeout=10);stderr.join(timeout=10)
        if stdout.is_alive(): status='failed';errors.append('stream_did_not_close')
    except Exception:
        errors.append('native_launch_or_transport_failed')
        if process and process.poll() is None: process.kill();process.wait()
    answer_text=result.get('result') or (texts[-1] if texts else '')
    if not models or any(model!=MODEL for model in models): status='failed';errors.append('native_model_unverified_or_substituted')
    if result.get('is_error'): status='failed';errors.append('provider_reported_error')
    try:
        answer=json.loads(answer_text)
        if not isinstance(answer,dict) or set(answer)!={'answers','report'} or not isinstance(answer['answers'],list) or not isinstance(answer['report'],str): raise ValueError()
    except (ValueError,TypeError): answer=None;errors.append('malformed_answer')
    receipt={'schema':'osanwe.native-pilot-attempt/1','opportunity':opportunity,'status':status,
             'started_at':started,'ended_at':now(),'elapsed_seconds':time.monotonic()-monotonic,
             'returncode':process.returncode if process else None,'model_ids':sorted(models),
             'requested_model':MODEL,'requested_effort':EFFORT,'provider_effort_attested':False,
             'execution_custody':'local client reported','binary_sha256':m['binary_sha256'],
             'prompt_sha256':sha(prompt.encode('ascii')),'environment_overrides':overrides,
             'read_files':reads,'library_reads':[x for x in reads if x.startswith('library-')],
             'library_available':library,'usage':result.get('modelUsage'), 'num_turns':result.get('num_turns'),
             'stderr_bytes_omitted':stderr_size,'errors':errors,'answer':answer,
             'delivered_text':answer_text[:100000],'delivered_text_truncated':len(answer_text)>100000,
             'financial_prose_assessment':'not yet independently reviewed'}
    exclusive_json(directory/'receipt.json',receipt)
    return {'id':opportunity['id'],'status':status,'completed_receipt':True}


def run(target,limit=None,workers=1):
    target,m=validate_plan(target)
    if (target/'closed-incomplete.json').exists():
        raise ValueError('closed batch cannot resume or gain new outcomes')
    if not EXE.is_file() or sha(EXE.read_bytes())!=m['binary_sha256']:
        raise ValueError('native binary unavailable or changed since freeze')
    if not 1<=workers<=3:
        raise ValueError('worker count must be 1..3')
    pending=[x for x in m['opportunities'] if not (target/'attempts'/x['id']).exists()]
    if limit is not None:
        if limit<1: raise ValueError('positive run scheduling limit required')
        pending=pending[:limit]
    lock=target/'run.lock'
    with lock.open('x',encoding='ascii') as handle:
        handle.write(dump({'pid':os.getpid(),'started_at':now()}))
    try:
        auth=subprocess.run([str(EXE),'auth','status'],capture_output=True,text=True,timeout=30)
        try: state=json.loads(auth.stdout)
        except ValueError: state={}
        if auth.returncode or state.get('loggedIn') is not True or state.get('apiProvider')!='firstParty' or state.get('authMethod') not in ('claude.ai','oauth'):
            raise ValueError('native first-party subscription authentication was not established')
        # No scores or per-answer results print during execution.
        with ThreadPoolExecutor(max_workers=workers) as executor:
            for result in executor.map(lambda o:run_one(target,m,o),pending): print(dump(result),flush=True)
    finally:
        lock.unlink()
    return {'status':'scheduled_opportunities_finished','attempted_this_call':len(pending),'denominator':108}


def summarize(target,close_incomplete=False):
    target,m=validate_plan(target)
    if (target/'run.lock').exists():
        return {'status':'batch_running_no_score_release','denominator':108}
    unfinished=[o for o in m['opportunities'] if not (target/'attempts'/o['id']/'receipt.json').exists()]
    already_closed=(target/'closed-incomplete.json').exists()
    if unfinished and not close_incomplete and not already_closed:
        return {'status':'batch_open_no_score_release','pending_or_interrupted':len(unfinished),'denominator':108}
    if close_incomplete and not already_closed:
        exclusive_json(target/'closed-incomplete.json',{'closed_at':now(),'missing':len(unfinished),'denominator':108})
    pack=json.loads((target/'development_cases.json').read_text()); cases={c['id']:c for c in pack['cases']}
    by_arm={a:{'assigned':36,'useful_completions':0,'missing_or_failed':0,'material_errors':0,'library_reads':0,
               'observed_receipts':0,'elapsed_seconds_total':0,'read_calls':0,'usage':{k:0 for k in USAGE_COUNTERS}} for a in ARMS}
    records=[];grading=[]
    for o in m['opportunities']:
        path=target/'attempts'/o['id']/'receipt.json'
        r=json.loads(path.read_text()) if path.exists() else None
        if r and r['status']=='completed' and r['answer']:
            grading.append({'id':o['id'],'case':cases[o['case_id']],
                            'submission':{'privacy':'synthetic','answers':r['answer']['answers'],
                                          'execution':{'model_id':MODEL,'effort':EFFORT,'session_nonce':str(uuid.UUID(hex=o['id'])),
                                                       'resource_digest':'0'*64,'status':'completed'}}})
    scored=subprocess.run(['node',str(ROOT/'score_native.mjs')],input=dump({'schema':'osanwe.native-grading-input/1','records':grading}),capture_output=True,text=True,timeout=30)
    if scored.returncode:
        raise ValueError('shared deterministic grader unavailable; no scores released')
    scores={row['id']:row for row in json.loads(scored.stdout)}
    for o in m['opportunities']:
        path=target/'attempts'/o['id']/'receipt.json'; out=by_arm[o['arm']]
        r=json.loads(path.read_text()) if path.exists() else None
        # Observed work remains in overhead even when format, timeout, or grading
        # fails. Absent receipts remain explicitly unobserved, never zero-cost.
        if r:
            out['observed_receipts']+=1
            out['library_reads']+=len(r.get('library_reads',[]))
            out['read_calls']+=len(r.get('read_files',[]))
            out['elapsed_seconds_total']+=r.get('elapsed_seconds',0)
            for usage in (r.get('usage') or {}).values():
                for key in USAGE_COUNTERS:
                    out['usage'][key]+=usage.get(key,0) or 0
        if not r or r['status']!='completed' or not r['answer']:
            out['missing_or_failed']+=1; records.append({'id':o['id'],'useful_completion':0,'state':'missing_or_failed'});continue
        score=scores[o['id']]
        out['useful_completions']+=score['useful_completion'];out['material_errors']+=score['material_errors']
        if score['validation']!='valid':out['missing_or_failed']+=1
        records.append({'id':o['id'],'useful_completion':score['useful_completion'],'state':r['status'],'validation':score['validation']})
    return {'schema':'osanwe.native-pilot-summary/2','status':'development_scored','denominator':108,
            'overhead_scope':'All observed receipts, including malformed and failed outputs; missing receipts have unobserved overhead. Thinking tokens may be a subset of output tokens.',
            'arms':by_arm,'opportunities':records,'limits':'Exposed synthetic development; structured answer grading only; no independent prose assessment or improvement claim.'}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    prep=sub.add_parser('prepare');prep.add_argument('--config',required=True);prep.add_argument('--output',required=True)
    go=sub.add_parser('run');go.add_argument('--plan',required=True);go.add_argument('--limit',type=int);go.add_argument('--workers',type=int,default=1)
    report=sub.add_parser('summarize');report.add_argument('--plan',required=True);report.add_argument('--close-incomplete',action='store_true')
    args=p.parse_args(argv)
    try:
        result=prepare(args.config,args.output) if args.command=='prepare' else run(args.plan,args.limit,args.workers) if args.command=='run' else summarize(args.plan,args.close_incomplete)
        print(dump(result));return 0
    except Exception as exc:
        print(dump({'status':'refused','error':type(exc).__name__,'detail':str(exc) if isinstance(exc,ValueError) else 'filesystem or native prerequisite unavailable'}));return 2


if __name__=='__main__':
    sys.exit(main())
