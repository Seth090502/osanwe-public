import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {randomUUID} from 'node:crypto';
import {createDevelopment,call,correctSubmission} from '../service/development.mjs';
import {verifyReceipt,grade,validateSubmission,canonical,digest,LIMITS,admissionCoverage,ADMISSION_CASES_BY_FAMILY} from '../service/worker.mjs';

const CASES=JSON.parse(readFileSync(new URL('../development_cases.json',import.meta.url),'utf8')).cases;
async function ready(d,index=0) {
  const reserve=await call(d,'reserve',d.assignments[index]); assert.equal(reserve.status,200);
  const id=reserve.body.attempt_id;
  const issue=await call(d,'issue',{attempt_id:id}); assert.equal(issue.status,200);
  return id;
}
async function complete(d,index=0,c=CASES[0],change) {
  const id=await ready(d,index),s=correctSubmission(c,d.resourceDigest); if(change) change(s);
  assert.equal((await call(d,'submit',{attempt_id:id,submission:s})).status,200);
  const result=await call(d,'score',{attempt_id:id}); assert.equal(result.status,200);
  assert.deepEqual(Object.keys(result.body).sort(),['attempt_id','state']);
  return id;
}
async function withDev(options,fn) { const d=await createDevelopment({cases:[CASES[0]],arms:['baseline'],...options}); try {await fn(d);} finally {d.close();} }
async function sealAll(d) {
  for(let i=0;i<60;i++) { const r=await call(d,'seal',{batch_id:'dev-batch'});assert.equal(r.status,200);if(r.body.state==='sealed')return; }
  assert.fail('bounded sealing did not terminate');
}

test('36 openly exposed cases cover nine families and distinct underlying scenarios',()=>{
  assert.equal(CASES.length,36); assert.equal(new Set(CASES.map(c=>c.family)).size,9);
  assert.equal(new Set(CASES.map(c=>c.scenario_family)).size,36);
  for(const c of CASES) assert.equal(grade(correctSubmission(c,'0'.repeat(64)),c.oracle).useful_completion,1,c.id);
});
test('prospective admission requires ten families, exact 72-case allocation and three arms',()=>{
  const protocol=JSON.parse(readFileSync(new URL('../reasoning_protocol.json',import.meta.url),'utf8'));
  assert.deepEqual(ADMISSION_CASES_BY_FAMILY,protocol.admission.cases_by_family);
  const families=Object.entries(ADMISSION_CASES_BY_FAMILY).map(([family,n])=>({family,n,assignments:3*n}));
  const arms=['baseline','revised_no_library','revised_library'];
  assert.equal(admissionCoverage(families,arms,216),true); // Shape only, no admission or independence claim.
  assert.equal(admissionCoverage(families.filter(f=>f.family!=='account_scope').map(f=>({...f,n:8,assignments:24})),arms,216),false);
  assert.equal(admissionCoverage(families.map(f=>f.family==='household'?{...f,n:7,assignments:21}:f.family==='account_scope'?{...f,n:9,assignments:27}:f),arms,216),false);
  assert.equal(admissionCoverage(families,['baseline','baseline','revised_library'],216),false);
});
test('separate account-scope supplement accepts supported controls and rejects planted scope errors',()=>{
  const pack=JSON.parse(readFileSync(new URL('../account_scope_development_v1.json',import.meta.url),'utf8'));
  assert.equal(pack.admission_eligible,false);assert.equal(pack.native_tested,false);assert.equal(pack.cases.length,4);
  for(const c of pack.cases) {
    const correct=correctSubmission(c,'0'.repeat(64));validateSubmission(correct,c.input,c.oracle);
    assert.equal(grade(correct,c.oracle).useful_completion,1,c.id);
    const index=c.oracle.obligations.findIndex(o=>o.value===false),wrong=structuredClone(correct);
    wrong.answers[index].value=true;validateSubmission(wrong,c.input,c.oracle);
    assert.equal(grade(wrong,c.oracle).useful_completion,0,c.id);
    assert.ok(grade(wrong,c.oracle).material_errors>0,c.id);
  }
});
test('reservation commits before input disclosure; issued output excludes oracle',async()=>withDev({},async d=>{
  const reserved=await call(d,'reserve',d.assignments[0]); assert.equal(reserved.body.state,'reserved'); assert.ok(!('task' in reserved.body));
  const events=d.env.WITNESS.db.prepare('SELECT kind FROM events').all(); assert.deepEqual(events.map(e=>e.kind),['reserved']);
  const issued=await call(d,'issue',{attempt_id:reserved.body.attempt_id});
  assert.equal(issued.body.task.case_id,CASES[0].id); assert.ok(!JSON.stringify(issued.body).includes('source_sets'));
}));
test('concurrent idempotent reservations consume exactly one credit',async()=>withDev({},async d=>{
  const results=await Promise.all(Array.from({length:12},()=>call(d,'reserve',d.assignments[0])));
  assert.ok(results.every(r=>r.status===200)); assert.equal(new Set(results.map(r=>r.body.attempt_id)).size,1);
  assert.equal(d.env.WITNESS.db.prepare('SELECT COUNT(*) n FROM burns').get().n,1);
}));
test('renamed request and candidate cannot restore a spent assignment',async()=>withDev({},async d=>{
  await call(d,'reserve',d.assignments[0]);
  const changed={...d.assignments[0],idempotency_key:randomUUID()};
  assert.equal((await call(d,'reserve',changed)).status,409);
  assert.equal((await call(d,'reserve',{...changed,candidate_digest:'0'.repeat(64)})).body.error,'candidate_or_protocol_mismatch');
}));
test('quota and duplicate checks are atomic across different reservations',async()=>withDev({arms:['baseline','revised_no_library'],quota:1},async d=>{
  const results=await Promise.all(d.assignments.map(x=>call(d,'reserve',x)));
  assert.equal(results.filter(x=>x.status===200).length,1);
  assert.equal(d.env.WITNESS.db.prepare('SELECT COUNT(*) n FROM burns').get().n,1);
}));
test('changed bytes under the same idempotency key are rejected',async()=>withDev({arms:['baseline','revised_no_library']},async d=>{
  await call(d,'reserve',d.assignments[0]);
  const p={...d.assignments[1],idempotency_key:d.assignments[0].idempotency_key};
  assert.equal((await call(d,'reserve',p)).body.error,'idempotency_conflict');
}));
test('submission locks exact bytes, retries do not regrade an altered answer',async()=>withDev({},async d=>{
  const id=await ready(d),s=correctSubmission(CASES[0],d.resourceDigest);
  assert.equal((await call(d,'submit',{attempt_id:id,submission:s})).status,200);
  assert.equal((await call(d,'submit',{attempt_id:id,submission:s})).body.replayed,true);
  s.answers[0].value=999;
  assert.equal((await call(d,'submit',{attempt_id:id,submission:s})).body.error,'submission_locked');
}));
test('no batch release before closure or while unfinished before deadline',async()=>withDev({arms:['baseline','revised_no_library']},async d=>{
  await complete(d);
  assert.equal((await call(d,'release',{batch_id:'dev-batch'})).body.error,'batch_not_closed');
  assert.equal((await call(d,'close',{batch_id:'dev-batch'})).body.error,'batch_incomplete');
}));
test('signed receipt binds correct scoring and released lifecycle; replay stable',async()=>withDev({},async d=>{
  const id=await complete(d); assert.equal((await call(d,'close',{batch_id:'dev-batch'})).status,200);
  assert.equal((await call(d,'release',{batch_id:'dev-batch'})).body.error,'batch_not_sealed');
  await sealAll(d);
  const r=await call(d,'release',{batch_id:'dev-batch'}); assert.equal(r.status,200);
  assert.equal(await verifyReceipt(r.body,d.publicKey),true);
  assert.equal(r.body.payload.evidence_class,'development'); assert.equal(r.body.payload.custody_verified,false);
  assert.equal(r.body.payload.arms.baseline.useful_completions,1);
  assert.equal((await call(d,'acknowledge',{attempt_id:id})).body.state,'released');
  assert.equal((await call(d,'acknowledge',{attempt_id:id})).body.state,'released');
  assert.deepEqual((await call(d,'release',{batch_id:'dev-batch'})).body,r.body);
  r.body.payload.arms.baseline.useful_completions=99;
  assert.equal(await verifyReceipt(r.body,d.publicKey),false);
}));
test('missing arms and timed-out output stay in the full denominator',async()=>withDev({arms:['baseline','revised_no_library','revised_library']},async d=>{
  await complete(d,0,CASES[0],s=>s.execution.status='timeout');
  d.env.TEST_NOW='2026-09-15T00:00:00.000Z';
  assert.equal((await call(d,'close',{batch_id:'dev-batch'})).status,200);
  await sealAll(d);
  const r=(await call(d,'release',{batch_id:'dev-batch'})).body;
  for(const a of Object.values(r.payload.arms)) { assert.equal(a.assigned,1); assert.equal(a.useful_completions,0); assert.equal(a.missing_or_failed,1); }
  assert.equal((await call(d,'reserve',d.assignments[1])).body.error,'batch_closed');
}));
test('abandoning/failed attempts cannot be reissued or regain credit',async()=>withDev({},async d=>{
  const id=await ready(d); assert.equal((await call(d,'finish',{attempt_id:id,outcome:'failed'})).status,200);
  assert.equal((await call(d,'issue',{attempt_id:id})).body.error,'invalid_transition');
  assert.equal((await call(d,'reserve',{...d.assignments[0],idempotency_key:randomUUID()})).status,409);
}));
test('crash after durable submission does not permit a different answer',async()=>withDev({},async d=>{
  const id=await ready(d),s=correctSubmission(CASES[0],d.resourceDigest);
  const original=d.env.DB.prepare.bind(d.env.DB);
  d.env.DB.prepare=(sql)=>{if(sql.startsWith('INSERT INTO artifacts')) throw new Error('private canary MUST_NOT_ESCAPE'); return original(sql);};
  const r=await call(d,'submit',{attempt_id:id,submission:s}); assert.equal(r.body.error,'internal_failure');
  assert.ok(!JSON.stringify(r).includes('MUST_NOT_ESCAPE'));
  d.env.DB.prepare=original;
  assert.equal((await call(d,'submit',{attempt_id:id,submission:s})).body.error,'restored_or_missing_artifact');
  s.answers[0].value=1; assert.equal((await call(d,'submit',{attempt_id:id,submission:s})).body.error,'submission_locked');
}));
test('primary database restore cannot restore witness credits',async()=>withDev({},async d=>{
  const id=await complete(d); d.env.DB.db.exec('DELETE FROM artifacts');
  assert.equal((await call(d,'score',{attempt_id:id})).body.error,'restored_or_missing_artifact');
  assert.equal((await call(d,'reserve',{...d.assignments[0],idempotency_key:randomUUID()})).status,409);
}));
test('witness generation or epoch mismatch locks service',async()=>withDev({},async d=>{
  d.env.EXPECTED_WITNESS_GENERATION=randomUUID();
  assert.equal((await call(d,'reserve',d.assignments[0])).body.error,'restore_or_freeze_mismatch');
}));
test('production-class evaluation refuses unverified custody even when declared by DB',async()=>withDev({},async d=>{
  d.env.DB.db.exec("UPDATE campaigns SET evidence_class='independent-admission'");
  assert.equal((await call(d,'reserve',d.assignments[0])).body.error,'independent_custody_unverified');
}));
test('custody declarations cannot label an incomplete case set as 72-case admission',async()=>withDev({},async d=>{
  d.env.CUSTODY_VERIFIED='true';d.env.CUSTODY_RECEIPT_DIGEST='1'.repeat(64);d.env.RELEASE_CODE_SHA256='2'.repeat(64);
  d.env.DB.db.prepare("UPDATE campaigns SET evidence_class='independent-admission',custody_receipt_digest=?").run(d.env.CUSTODY_RECEIPT_DIGEST);
  assert.equal((await call(d,'reserve',d.assignments[0])).body.error,'admission_coverage_incomplete');
}));
test('witness mutations and invalid state jumps fail at database boundary',async()=>withDev({},async d=>{
  const id=(await call(d,'reserve',d.assignments[0])).body.attempt_id;
  assert.throws(()=>d.env.WITNESS.db.exec('DELETE FROM burns'),/immutable/);
  assert.throws(()=>d.env.WITNESS.db.exec('UPDATE quotas SET max_attempts=999'),/immutable/);
  assert.throws(()=>d.env.WITNESS.db.prepare('INSERT INTO events(attempt_id,kind,payload_digest,created_at) VALUES(?,?,?,?)').run(id,'scored','fake','now'),/invalid_transition/);
}));
test('arbitrary personal prose, unexpected fields and unknown sources never persist',async()=>withDev({},async d=>{
  const id=await ready(d),s=correctSubmission(CASES[0],d.resourceDigest);
  s.answers[0].value='PRIVATE_ACCOUNT_CANARY_927416';
  let r=await call(d,'submit',{attempt_id:id,submission:s}); assert.equal(r.status,400);
  assert.ok(!JSON.stringify(r).includes('927416'));
  s.answers[0].value=100; s.account_number='PRIVATE_ACCOUNT_CANARY_927416';
  assert.equal((await call(d,'submit',{attempt_id:id,submission:s})).status,400);
  assert.equal(d.env.DB.db.prepare('SELECT COUNT(*) n FROM artifacts').get().n,0);
}));
test('maximum request bytes are bounded before JSON parsing and logs',async()=>withDev({},async d=>{
  const r=await call(d,'reserve',{canary:'P'.repeat(LIMITS.bodyBytes)});
  assert.equal(r.status,413); assert.equal(r.body.error,'payload_too_large');
}));
test('model/effort downgrade is refused rather than recorded as requested model',async()=>withDev({},async d=>{
  const id=await ready(d),s=correctSubmission(CASES[0],d.resourceDigest); s.execution.effort='high';
  assert.equal((await call(d,'submit',{attempt_id:id,submission:s})).body.error,'execution_contract_mismatch');
}));
test('tampered source snapshot and grader cannot silently change scoring',async()=>withDev({},async d=>{
  const id=await ready(d),s=correctSubmission(CASES[0],d.resourceDigest);
  await call(d,'submit',{attempt_id:id,submission:s});
  d.env.DB.db.prepare('UPDATE cases SET oracle_json=?').run('{}');
  assert.equal((await call(d,'score',{attempt_id:id})).body.error,'oracle_snapshot_changed');
}));
test('blanket refusal fails answerable controls; wrong interpretation fails correct arithmetic',()=>{
  const c=CASES.find(c=>c.scenario_family==='operating-expense-label'),s=correctSubmission(c,'0'.repeat(64));
  s.answers[0].value=1020; assert.equal(grade(s,c.oracle).useful_completion,0); assert.equal(grade(s,c.oracle).material_errors,1);
  for(const a of s.answers) {a.status='withheld';a.value=null;}
  assert.equal(grade(s,c.oracle).useful_completion,0);
});
test('complete 36-case three-arm mechanical run keeps counts and bounded release queries',async()=>withDev({cases:CASES,arms:['baseline','revised_no_library','revised_library']},async d=>{
  for(let i=0;i<d.assignments.length;i++) await complete(d,i,CASES[Math.floor(i/3)]);
  await call(d,'close',{batch_id:'dev-batch'});
  await sealAll(d);
  d.env.DB.calls=0;d.env.WITNESS.calls=0;
  const r=await call(d,'release',{batch_id:'dev-batch'}); assert.equal(r.status,200);
  assert.equal(await verifyReceipt(r.body,d.publicKey),true);
  for(const arm of Object.values(r.body.payload.arms)) {assert.equal(arm.assigned,36);assert.equal(arm.useful_completions,36);}
  assert.ok(d.env.DB.calls+d.env.WITNESS.calls<=20,'release query fanout exceeds bounded budget');
}));
