/* Local CPU/query bounds only. This does NOT certify Cloudflare free-tier CPU. */
import {readFileSync} from 'node:fs';
import {createDevelopment,call,correctSubmission} from './service/development.mjs';
import {LIMITS} from './service/worker.mjs';
const publicCases=JSON.parse(readFileSync(new URL('development_cases.json',import.meta.url),'utf8')).cases;
// Duplicates are solely load fixtures, never new independent capability cases.
const cases=[...publicCases,...publicCases.map(c=>({...structuredClone(c),id:c.id+'-load-copy'}))];
const dev=await createDevelopment({cases});
const measurements={};
async function measured(op,payload) {
  const before=process.cpuUsage(),start=performance.now();const queries=dev.env.DB.calls+dev.env.WITNESS.calls;
  const result=await call(dev,op,payload);const cpu=process.cpuUsage(before);
  (measurements[op] ||= []).push({cpu_ms:(cpu.user+cpu.system)/1000,wall_ms:performance.now()-start,queries:dev.env.DB.calls+dev.env.WITNESS.calls-queries});
  if(result.status!==200) throw new Error(op+' rejected in load probe');
  return result.body;
}
try {
  for(let i=0;i<dev.assignments.length;i++) {
    const r=await measured('reserve',dev.assignments[i]);await measured('issue',{attempt_id:r.attempt_id});
    await measured('submit',{attempt_id:r.attempt_id,submission:correctSubmission(cases[Math.floor(i/3)],dev.resourceDigest)});
    await measured('score',{attempt_id:r.attempt_id});
  }
  await measured('close',{batch_id:'dev-batch'});
  while((await measured('seal',{batch_id:'dev-batch'})).state!=='sealed') {}
  await measured('release',{batch_id:'dev-batch'});
  const report=Object.fromEntries(Object.entries(measurements).map(([phase,values])=>{
    const cpu=values.map(x=>x.cpu_ms).sort((a,b)=>a-b);
    return [phase,{samples:values.length,max_queries:Math.max(...values.map(x=>x.queries)),
      p95_local_process_cpu_ms:cpu[Math.min(cpu.length-1,Math.ceil(cpu.length*.95)-1)],max_local_process_cpu_ms:Math.max(...cpu)}];
  }));
  process.stdout.write(JSON.stringify({schema:'osanwe.worker-local-resource-probe/1',verified_at:new Date().toISOString(),node:process.version,
    assignments:216,limits:LIMITS,phases:report,query_bound_pass:Object.values(report).every(x=>x.max_queries<=50),
    cloudflare_cpu_fit:'UNVERIFIED: Node process CPU and local SQLite are not Workers CPU/D1 telemetry',
    inference_performed:false,quality_evidence:false})+'\n');
} finally {dev.close();}
