import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {randomUUID} from 'node:crypto';
import {createDevelopment,call,correctSubmission} from '../service/development.mjs';
import {freezeCohort} from '../service/cohort-freeze.mjs';
import {verifyReceipt,LIMITS} from '../service/worker.mjs';
import oldWorker from '../reports/native-pilot-runtime-2026-09-13/service/worker.mjs';

const CASES=JSON.parse(readFileSync(new URL('../development_cases.json',import.meta.url),'utf8')).cases;
async function withCohort(fn) {const d=await createDevelopment({cases:CASES.slice(0,2),cohortChunkCases:1});try {await fn(d);}finally {d.close();}}
async function complete(d,i) {
  const r=await call(d,'reserve',d.assignments[i]);assert.equal(r.status,200,JSON.stringify(r));
  const attempt_id=r.body.attempt_id;assert.equal((await call(d,'issue',{attempt_id})).status,200);
  assert.equal((await call(d,'submit',{attempt_id,submission:correctSubmission(CASES[Math.floor(i/3)],d.resourceDigest)})).status,200);
  assert.equal((await call(d,'score',{attempt_id})).status,200);return attempt_id;
}
async function seal(d,batch_id) {
  assert.equal((await call(d,'close',{batch_id})).status,200);
  let r;do {r=await call(d,'seal',{batch_id});assert.equal(r.status,200,JSON.stringify(r));}while(r.body.state!=='sealed');
  const out=await call(d,'cohort-seal',{batch_id});assert.equal(out.status,200,JSON.stringify(out));
  assert.equal(JSON.stringify(out).includes('useful_completions'),false);
}

test('cohort chunks cannot peek; a single fixed denominator and alpha survive missing chunks',async()=>withCohort(async d=>{
  for(let i=0;i<3;i++)await complete(d,i);
  await seal(d,d.batchIds[0]);
  assert.equal((await call(d,'release',{batch_id:d.batchIds[0]})).body.error,'cohort_not_closed');
  assert.equal((await call(d,'cohort-release',{cohort_id:d.cohortId})).body.error,'cohort_not_closed');
  assert.equal((await call(d,'cohort-close',{cohort_id:d.cohortId})).body.error,'cohort_incomplete');
  d.env.TEST_NOW='2026-09-15T00:00:00.000Z';await seal(d,d.batchIds[1]);
  const closes=await Promise.all([call(d,'cohort-close',{cohort_id:d.cohortId}),call(d,'cohort-close',{cohort_id:d.cohortId})]);
  assert.ok(closes.every(r=>r.status===200));
  const results=await Promise.all([call(d,'cohort-release',{cohort_id:d.cohortId}),call(d,'cohort-release',{cohort_id:d.cohortId})]);
  assert.deepEqual(results[0],results[1]);const receipt=results[0].body;
  assert.equal(await verifyReceipt(receipt,d.publicKey),true);assert.equal(receipt.payload.assigned,6);
  assert.equal(receipt.payload.required_families,2);assert.equal(receipt.payload.batch_alpha,.025);
  for(const arm of Object.values(receipt.payload.arms)) {assert.equal(arm.assigned,2);assert.equal(arm.useful_completions,1);assert.equal(arm.missing_or_failed,1);}
  for(const batch_id of d.batchIds) {
    const r=await call(d,'release',{batch_id});assert.equal(r.status,200);assert.equal(r.body.payload.batch_alpha,.025);
    assert.equal(r.body.payload.analysis_index,1);assert.match(r.body.payload.alpha_scope,/whole cohort/);
  }
  assert.equal(d.env.WITNESS.db.prepare('SELECT COUNT(*) n FROM analysis_slots').get().n,1);
  receipt.payload.required_families=1;assert.equal(await verifyReceipt(receipt,d.publicKey),false);
}));

test('cohort freeze is idempotent, immutable, and cannot reset alpha by renaming',async()=>withCohort(async d=>{
  const plan={id:d.cohortId,campaign_id:'dev-campaign',analysis_index:1,batch_ids:d.batchIds,required_families:2};
  const results=await Promise.all([freezeCohort(d.env,plan),freezeCohort(d.env,plan)]);
  assert.ok(results.every(r=>r.replayed));
  await assert.rejects(()=>freezeCohort(d.env,{...plan,required_families:1}),/sample mismatch/);
  await assert.rejects(()=>freezeCohort(d.env,{...plan,id:'renamed-hypothesis'}));
  assert.throws(()=>d.env.WITNESS.db.exec('DELETE FROM cohort_members'),/immutable/);
  assert.throws(()=>d.env.WITNESS.db.exec('UPDATE cohort_plans SET required_families=1'),/immutable/);
  assert.throws(()=>d.env.WITNESS.db.exec("INSERT INTO cohort_members VALUES('dev-cohort','new-chunk',2,3,1,'fake')"),/locked/);
  d.env.WITNESS.exec(readFileSync(new URL('../service/witness.sql',import.meta.url),'utf8'));
  assert.equal(d.env.WITNESS.db.prepare('SELECT COUNT(*) n FROM analysis_slots').get().n,1);
}));

test('first cohort freeze commits atomically under concurrency; interrupted preparation cannot disclose',async()=>{
  const d=await createDevelopment({cases:CASES.slice(0,2),cohortChunkCases:1,freezeCohortPlan:false});
  try {
    const plan={id:d.cohortId,campaign_id:'dev-campaign',analysis_index:1,batch_ids:d.batchIds,required_families:2};
    assert.equal((await call(d,'reserve',d.assignments[0])).body.error,'analysis_slot_mismatch');
    const original=d.env.WITNESS.batch.bind(d.env.WITNESS);d.env.WITNESS.batch=async()=>{throw new Error('injected preparation interruption');};
    await assert.rejects(()=>freezeCohort(d.env,plan));
    assert.equal(d.env.WITNESS.db.prepare('SELECT COUNT(*) n FROM analysis_slots').get().n,0);
    d.env.WITNESS.batch=original;
    const results=await Promise.all([freezeCohort(d.env,plan),freezeCohort(d.env,plan)]);
    assert.equal(results.filter(r=>r.replayed===false).length,1);
    assert.equal(d.env.WITNESS.db.prepare('SELECT COUNT(*) n FROM analysis_slots').get().n,1);
    assert.equal((await call(d,'reserve',d.assignments[0])).status,200);
  }finally {d.close();}
});

test('code-only rollback retains versioned witness binding and cannot bypass cohort release',async()=>withCohort(async d=>{
  const deploymentEnv={...d.env};delete deploymentEnv.WITNESS;
  const request=new Request('http://localhost/v1/release',{method:'POST',headers:{'content-type':'application/json',authorization:'Bearer '+d.token},body:JSON.stringify({batch_id:d.batchIds[0]})});
  const result=await oldWorker.fetch(request,deploymentEnv);
  assert.equal((await result.json()).error,'service_unconfigured');
  const legacyEnv={...d.env};delete legacyEnv.EVAL_WITNESS_V2;
  const original=d.env;d.env=legacyEnv;
  assert.equal((await call(d,'reserve',d.assignments[0])).body.error,'cohort_requires_versioned_witness_binding');d.env=original;
}));

test('primary plan edits fail before disclosure; freeze never grants attempts again',async()=>withCohort(async d=>{
  const id=await complete(d,0);
  d.env.DB.db.prepare('UPDATE assignments SET candidate_digest=? WHERE id=?').run('f'.repeat(64),d.assignments[1].assignment_id);
  assert.equal((await call(d,'reserve',d.assignments[1])).body.error,'cohort_member_changed');
  d.env.DB.db.prepare('UPDATE assignments SET candidate_digest=? WHERE id=?').run(d.assignments[1].candidate_digest,d.assignments[1].assignment_id);
  d.env.DB.db.exec('DELETE FROM artifacts');
  assert.equal((await call(d,'score',{attempt_id:id})).body.error,'restored_or_missing_artifact');
  assert.equal((await call(d,'reserve',{...d.assignments[0],idempotency_key:randomUUID()})).status,409);
  assert.equal(d.env.WITNESS.db.prepare('SELECT spent FROM quota_usage').get().spent,1);
}));

test('quota projection is atomic, monotone and preserved by migration without full-history scans',async()=>withCohort(async d=>{
  const first=await call(d,'reserve',d.assignments[0]);assert.equal(first.status,200);
  const replay=await Promise.all([call(d,'reserve',d.assignments[0]),call(d,'reserve',d.assignments[0])]);assert.ok(replay.every(r=>r.status===200));
  assert.equal(d.env.WITNESS.db.prepare('SELECT spent FROM quota_usage').get().spent,1);
  assert.throws(()=>d.env.WITNESS.db.exec('UPDATE quota_usage SET spent=0'),/immutable/);
  assert.throws(()=>d.env.WITNESS.db.exec('DELETE FROM quota_usage'),/immutable/);
  const original=d.env.WITNESS.prepare.bind(d.env.WITNESS);
  d.env.WITNESS.prepare=sql=>original(sql.startsWith('INSERT INTO events(attempt_id,kind,payload_digest,created_at) VALUES(?,')?sql.replace("'reserved'","'scored'"):sql);
  assert.equal((await call(d,'reserve',d.assignments[1])).status,409);
  d.env.WITNESS.prepare=original;
  assert.equal(d.env.WITNESS.db.prepare('SELECT spent FROM quota_usage').get().spent,1);
  assert.equal(d.env.WITNESS.db.prepare('SELECT COUNT(*) n FROM burns').get().n,1);
  d.env.WITNESS.exec(readFileSync(new URL('../service/witness.sql',import.meta.url),'utf8'));
  assert.equal(d.env.WITNESS.db.prepare('SELECT spent FROM quota_usage').get().spent,1);
  const trigger=d.env.WITNESS.db.prepare("SELECT sql FROM sqlite_master WHERE type='trigger' AND name='burn_guard'").get().sql;
  assert.ok(!trigger.includes('COUNT(*) FROM burns'));
  assert.equal((await call(d,'reserve',d.assignments[1])).status,200);
  assert.equal(d.env.WITNESS.db.prepare('SELECT spent FROM quota_usage').get().spent,2);
}));

test('interrupted cohort fragment commit is retriable without early results',async()=>withCohort(async d=>{
  d.env.TEST_NOW='2026-09-15T00:00:00.000Z';
  const original=d.env.WITNESS.prepare.bind(d.env.WITNESS);
  d.env.WITNESS.prepare=sql=>{if(sql.startsWith('INSERT INTO cohort_fragments'))throw new Error('PRIVATE_CRASH_CANARY');return original(sql);};
  const batch_id=d.batchIds[0];await call(d,'close',{batch_id});await call(d,'seal',{batch_id});
  const failed=await call(d,'cohort-seal',{batch_id});assert.equal(failed.body.error,'internal_failure');assert.ok(!JSON.stringify(failed).includes('CANARY'));
  d.env.WITNESS.prepare=original;
  await seal(d,batch_id);await seal(d,d.batchIds[1]);await call(d,'cohort-close',{cohort_id:d.cohortId});
  const before=await call(d,'cohort-release',{cohort_id:d.cohortId});assert.equal(before.status,200);
  d.env.DB.db.exec('DELETE FROM releases;DELETE FROM artifacts');
  assert.deepEqual(await call(d,'cohort-release',{cohort_id:d.cohortId}),before);
  assert.equal((await call(d,'reserve',d.assignments[0])).body.error,'batch_closed');
}));

test('1141-family load mechanics fit bounded chunks without manufacturing independent cases',async t=>{
  // These renamed clones are LOAD ONLY. The independent-family metadata supplied
  // by a real custodian still requires external source/distribution validation.
  const cases=Array.from({length:1141},(_,i)=>({...structuredClone(CASES[i%CASES.length]),id:`load-${i}`,scenario_family:`load-scenario-${i}`,source_family:`load-source-${i}`}));
  const d=await createDevelopment({cases,cohortChunkCases:72});
  try {
    assert.equal(d.batchIds.length,16);assert.equal(d.assignments.length,3423);
    d.env.TEST_NOW='2026-09-15T00:00:00.000Z';
    let maxQueries=0;
    for(const batch_id of d.batchIds) {
      for(const op of ['close','seal']) {
        let r;do {const start=d.env.DB.calls+d.env.WITNESS.calls;r=await call(d,op,{batch_id});maxQueries=Math.max(maxQueries,d.env.DB.calls+d.env.WITNESS.calls-start);assert.equal(r.status,200,JSON.stringify(r));}while(op==='seal' && r.body.state!=='sealed');
      }
      const start=d.env.DB.calls+d.env.WITNESS.calls;const r=await call(d,'cohort-seal',{batch_id});maxQueries=Math.max(maxQueries,d.env.DB.calls+d.env.WITNESS.calls-start);assert.equal(r.status,200);
    }
    await call(d,'cohort-close',{cohort_id:d.cohortId});
    const start=d.env.DB.calls+d.env.WITNESS.calls;const r=await call(d,'cohort-release',{cohort_id:d.cohortId});maxQueries=Math.max(maxQueries,d.env.DB.calls+d.env.WITNESS.calls-start);
    assert.equal(r.status,200);assert.equal(r.body.payload.assigned,3423);assert.equal(r.body.payload.required_families,1141);
    for(const arm of Object.values(r.body.payload.arms)){assert.equal(arm.assigned,1141);assert.equal(arm.missing_or_failed,1141);}
    assert.ok(maxQueries<=50,`bounded request D1 query budget: ${maxQueries}`);assert.ok(d.batchIds.length<=LIMITS.cohortChunks);
    assert.equal(await verifyReceipt(r.body,d.publicKey),true);
    t.diagnostic(JSON.stringify({load_only:true,assignments:3423,chunks:16,max_queries_per_request:maxQueries,hosted_cpu:'unverified',outcomes:'all missing, fixed denominator retained'}));
  }finally {d.close();}
});
