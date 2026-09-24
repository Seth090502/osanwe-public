/* Small deterministic assessment/control service. No model inference or prose judge.
 * Deployment credentials and signing key must be in independent custody.
 * The source/case DB can be restored; the independent witness must not be rolled back.
 */
export const LIMITS = Object.freeze({bodyBytes: 8192, obligations: 16, batchSize: 216, sealSize: 4, cohortChunks: 32});
const encoder = new TextEncoder();
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const DIGEST = /^[0-9a-f]{64}$/;
const TERMINAL = new Set(['scored', 'released', 'failed', 'abandoned']);
class Refusal extends Error { constructor(code, status=409) { super(code); this.code=code; this.status=status; } }
function requireThat(ok, code, status=409) { if (!ok) throw new Refusal(code, status); }
export function canonical(value) {
  if (value === null || typeof value === 'boolean' || typeof value === 'string') return JSON.stringify(value);
  if (typeof value === 'number') { requireThat(Number.isFinite(value), 'nonfinite_number', 400); return JSON.stringify(value); }
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  requireThat(value && Object.getPrototypeOf(value) === Object.prototype, 'invalid_json', 400);
  return '{' + Object.keys(value).sort().map(k => JSON.stringify(k) + ':' + canonical(value[k])).join(',') + '}';
}
export async function digest(value) {
  const bytes = typeof value === 'string' ? encoder.encode(value) : value;
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(b=>b.toString(16).padStart(2,'0')).join('');
}
function exact(obj, keys) {
  requireThat(obj && !Array.isArray(obj) && typeof obj === 'object' && Object.keys(obj).length === keys.length && keys.every(k=>Object.hasOwn(obj,k)), 'invalid_payload', 400);
}
function b64(bytes) { return btoa(String.fromCharCode(...new Uint8Array(bytes))); }
function unb64(s) { return Uint8Array.from(atob(s), c=>c.charCodeAt(0)); }
async function signed(payload, env) {
  const key = await crypto.subtle.importKey('pkcs8', unb64(env.SIGNING_KEY_PKCS8), {name:'Ed25519'}, false, ['sign']);
  const message = canonical(payload);
  return {payload, payload_sha256: await digest(message), algorithm:'Ed25519', key_id:env.SIGNING_KEY_ID,
    signed_payload:b64(encoder.encode(message)),
    signature:b64(await crypto.subtle.sign('Ed25519', key, encoder.encode(message)))};
}
export async function verifyReceipt(receipt, spki) {
  try {
    if (receipt.algorithm !== 'Ed25519' || receipt.payload_sha256 !== await digest(canonical(receipt.payload))) return false;
    if (new TextDecoder().decode(unb64(receipt.signed_payload))!==canonical(receipt.payload)) return false;
    if (receipt.payload.artifact_manifest_sha256 && await digest(canonical(receipt.artifact_manifest))!==receipt.payload.artifact_manifest_sha256) return false;
    const key = await crypto.subtle.importKey('spki', unb64(spki), {name:'Ed25519'}, false, ['verify']);
    return await crypto.subtle.verify('Ed25519', key, unb64(receipt.signature), encoder.encode(canonical(receipt.payload)));
  } catch { return false; }
}
async function one(db, sql, ...params) { return db.prepare(sql).bind(...params).first(); }
async function all(db, sql, ...params) { return (await db.prepare(sql).bind(...params).all()).results; }
async function run(db, sql, ...params) { return db.prepare(sql).bind(...params).run(); }
function now(env) { return env.TEST_NOW || new Date().toISOString(); }
async function body(request) {
  requireThat(request.headers.get('content-type')?.split(';')[0] === 'application/json', 'json_required', 415);
  const reader = request.body?.getReader();
  requireThat(reader, 'invalid_payload', 400);
  let chunks=[], length=0;
  while (true) {
    const {done,value}=await reader.read(); if(done) break;
    length+=value.length;
    if(length>LIMITS.bodyBytes) { await reader.cancel(); throw new Refusal('payload_too_large',413); }
    chunks.push(value);
  }
  const bytes=new Uint8Array(length); let offset=0;
  for(const chunk of chunks) { bytes.set(chunk,offset); offset+=chunk.length; }
  try { return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes)); }
  catch { throw new Refusal('invalid_json',400); }
}
async function authenticate(request, env) {
  requireThat(env.SUBMISSION_TOKEN_SHA256 && env.WITNESS && env.DB && env.EXPECTED_WITNESS_GENERATION, 'service_unconfigured',503);
  requireThat(env.RESTORE_LOCK!=='true','restore_lock_active',503);
  const token=request.headers.get('authorization') || '';
  requireThat(token.startsWith('Bearer ') && token.length<=256, 'unauthorized',401);
  // Fixed-length hash comparison avoids a direct token-length/timing comparison.
  const actual=await digest(token.slice(7)); let delta=0;
  for(let i=0;i<64;i++) delta|=actual.charCodeAt(i)^env.SUBMISSION_TOKEN_SHA256.charCodeAt(i);
  requireThat(delta===0,'unauthorized',401);
}
export async function batchSnapshot(env,batch) {
  const rows=await all(env.DB,'SELECT a.*,c.family,c.scenario_family,c.source_family,c.case_digest FROM assignments a JOIN cases c ON c.id=a.case_id WHERE a.batch_id=? ORDER BY a.ordinal LIMIT ?',batch.id,LIMITS.batchSize+1);
  requireThat(rows.length===batch.expected_count && rows.length<=LIMITS.batchSize && rows.every((r,i)=>r.ordinal===i),'restored_or_changed_plan',503);
  const value={batch,assignments:rows};
  requireThat(encoder.encode(canonical(value)).length<=196608,'cohort_plan_oversized',503);
  return value;
}
async function cohortContext(env,id) {
  const cohort=await one(env.WITNESS,'SELECT * FROM cohort_plans WHERE id=?',id);
  const freeze=await one(env.WITNESS,'SELECT * FROM cohort_freezes WHERE cohort_id=?',id);
  requireThat(cohort && freeze,'cohort_not_frozen',503);
  const slot=await one(env.WITNESS,'SELECT * FROM analysis_slots WHERE campaign_id=? AND analysis_index=?',cohort.campaign_id,cohort.analysis_index);
  requireThat(slot?.owner_kind==='cohort' && slot.owner_id===id,'analysis_slot_mismatch',503);
  const members=await all(env.WITNESS,'SELECT * FROM cohort_members WHERE cohort_id=? ORDER BY ordinal LIMIT ?',id,LIMITS.cohortChunks+1);
  requireThat(members.length===cohort.expected_batches && members.length<=LIMITS.cohortChunks && members.every((m,i)=>m.ordinal===i) &&
    members.reduce((n,m)=>n+m.expected_count,0)===cohort.expected_count && members.reduce((n,m)=>n+m.family_count,0)===cohort.required_families &&
    await digest(canonical({cohort,members}))===freeze.manifest_digest,'cohort_freeze_mismatch',503);
  return {cohort,members,freeze};
}
async function context(env, batchId) {
  const batch=await one(env.DB, 'SELECT * FROM batches WHERE id=?',batchId);
  requireThat(batch,'unknown_assignment',404);
  const campaign=await one(env.DB,'SELECT * FROM campaigns WHERE id=?',batch.campaign_id);
  const witness=await one(env.WITNESS,'SELECT * FROM custody WHERE id=?',campaign?.witness_id);
  const quota=await one(env.WITNESS,'SELECT * FROM quotas WHERE campaign_id=?',campaign?.id);
  const admitted=await one(env.WITNESS,'SELECT * FROM batch_plans WHERE batch_id=?',batch.id);
  requireThat(campaign && campaign.status==='frozen' && witness && quota,'custody_unavailable',503);
  requireThat(witness.generation===env.EXPECTED_WITNESS_GENERATION && quota.epoch===campaign.epoch && quota.plan_digest===campaign.protocol_digest && admitted && admitted.campaign_id===campaign.id && admitted.batch_index===batch.batch_index && admitted.plan_digest===batch.plan_digest,'restore_or_freeze_mismatch',503);
  requireThat(batch.expected_count<=LIMITS.batchSize,'plan_invalid',503);
  const member=await one(env.WITNESS,'SELECT * FROM cohort_members WHERE batch_id=?',batch.id);
  let cohort=null;
  if(member) {
    requireThat(env.EVAL_WITNESS_V2===env.WITNESS,'cohort_requires_versioned_witness_binding',503);
    ({cohort}=await cohortContext(env,member.cohort_id));
    requireThat(cohort.campaign_id===campaign.id && member.expected_count===batch.expected_count &&
      member.snapshot_digest===await digest(canonical(await batchSnapshot(env,batch))),'cohort_member_changed',503);
  } else {
    const slot=await one(env.WITNESS,'SELECT * FROM analysis_slots WHERE campaign_id=? AND analysis_index=?',campaign.id,batch.batch_index);
    requireThat(slot?.owner_kind==='batch' && slot.owner_id===batch.id,'analysis_slot_mismatch',503);
  }
  if(campaign.evidence_class==='independent-admission') {
    requireThat(env.CUSTODY_VERIFIED==='true' && DIGEST.test(campaign.custody_receipt_digest || '') && env.CUSTODY_RECEIPT_DIGEST===campaign.custody_receipt_digest && DIGEST.test(env.RELEASE_CODE_SHA256 || ''),'independent_custody_unverified',503);
    if(!cohort || cohort.purpose!=='confirmation') {
    const families=await all(env.DB,'SELECT c.family,COUNT(DISTINCT c.id) n,COUNT(*) assignments FROM assignments a JOIN cases c ON c.id=a.case_id WHERE a.batch_id=? GROUP BY c.family',batch.id);
    const arms=JSON.parse(batch.arms_json);
    requireThat(admissionCoverage(families,arms,batch.expected_count),'admission_coverage_incomplete',503);
    }
  }
  return {batch,campaign,cohort};
}

export const ADMISSION_CASES_BY_FAMILY=Object.freeze({valuation:7,earnings:7,portfolio:7,historical:7,
  macro:7,cycles:7,judgment:7,liquidity:7,household:8,account_scope:8});
export function admissionCoverage(families,arms,expectedCount) {
  // Shape is necessary, never proof of independent curation or meaningful cases.
  return expectedCount===216 && families.length===10 && new Set(families.map(f=>f.family)).size===10 &&
    families.every(f=>Object.hasOwn(ADMISSION_CASES_BY_FAMILY,f.family) &&
      f.n===ADMISSION_CASES_BY_FAMILY[f.family] && f.assignments===3*f.n) &&
    arms.length===3 && ['baseline','revised_no_library','revised_library'].every(a=>arms.includes(a));
}
async function assignment(env,id) {
  const item=await one(env.DB,'SELECT * FROM assignments WHERE id=?',id);
  requireThat(item,'unknown_assignment',404);
  return {item,...await context(env,item.batch_id)};
}
async function latest(env,id) { return one(env.WITNESS,'SELECT * FROM events WHERE attempt_id=? ORDER BY seq DESC LIMIT 1',id); }
async function attempt(env,id) {
  requireThat(UUID.test(id),'invalid_payload',400);
  const burn=await one(env.WITNESS,'SELECT * FROM burns WHERE id=?',id);
  requireThat(burn,'unknown_attempt',404);
  const ctx=await assignment(env,burn.assignment_id);
  requireThat(ctx.campaign.id===burn.campaign_id && ctx.campaign.epoch===burn.epoch,'restore_or_freeze_mismatch',503);
  return {burn,event:await latest(env,id),...ctx};
}
async function appendEvent(env,id,kind,payloadDigest) {
  const old=await one(env.WITNESS,'SELECT * FROM events WHERE attempt_id=? AND kind=?',id,kind);
  if(old) { requireThat(old.payload_digest===payloadDigest,'idempotency_conflict'); return; }
  try { await run(env.WITNESS,'INSERT INTO events(attempt_id,kind,payload_digest,created_at) VALUES(?,?,?,?)',id,kind,payloadDigest,now(env)); }
  catch {
    const replay=await one(env.WITNESS,'SELECT * FROM events WHERE attempt_id=? AND kind=?',id,kind);
    requireThat(replay && replay.payload_digest===payloadDigest,'transition_conflict');
  }
}
async function isClosed(env,batchId) { return one(env.WITNESS,'SELECT * FROM batch_closures WHERE batch_id=?',batchId); }
async function reserve(env,p) {
  exact(p,['assignment_id','candidate_digest','protocol_digest','idempotency_key']);
  requireThat(UUID.test(p.idempotency_key),'invalid_payload',400);
  const {item,batch,campaign}=await assignment(env,p.assignment_id);
  requireThat(p.candidate_digest===item.candidate_digest && p.protocol_digest===campaign.protocol_digest,'candidate_or_protocol_mismatch');
  const requestDigest=await digest(canonical(p));
  let old=await one(env.WITNESS,'SELECT * FROM burns WHERE campaign_id=? AND request_key=?',campaign.id,p.idempotency_key);
  if(old) {
    requireThat(old.request_digest===requestDigest,'idempotency_conflict');
    requireThat(await latest(env,old.id),'interrupted_reservation_spent',503);
    return {attempt_id:old.id,state:(await latest(env,old.id)).kind,replayed:true};
  }
  requireThat(!await isClosed(env,batch.id) && now(env)<batch.closes_at,'batch_closed');
  const id=crypto.randomUUID();
  try {
    await env.WITNESS.batch([
      env.WITNESS.prepare('INSERT INTO burns(id,campaign_id,epoch,batch_id,assignment_id,request_key,request_digest,created_at) VALUES(?,?,?,?,?,?,?,?)').bind(id,campaign.id,campaign.epoch,batch.id,item.id,p.idempotency_key,requestDigest,now(env)),
      env.WITNESS.prepare("INSERT INTO events(attempt_id,kind,payload_digest,created_at) VALUES(?,'reserved',?,?)").bind(id,requestDigest,now(env))
    ]);
  } catch {
    old=await one(env.WITNESS,'SELECT * FROM burns WHERE campaign_id=? AND request_key=?',campaign.id,p.idempotency_key);
    if(old && old.request_digest===requestDigest) return {attempt_id:old.id,state:(await latest(env,old.id))?.kind || 'failed',replayed:true};
    throw new Refusal('reservation_unavailable_or_spent');
  }
  return {attempt_id:id,state:'reserved',replayed:false};
}
async function issue(env,p) {
  exact(p,['attempt_id']);
  const ctx=await attempt(env,p.attempt_id);
  requireThat(ctx.event && ['reserved','issued'].includes(ctx.event.kind),'invalid_transition');
  requireThat(!await isClosed(env,ctx.batch.id) && now(env)<ctx.batch.closes_at,'batch_closed');
  const item=await one(env.DB,'SELECT * FROM cases WHERE id=?',ctx.item.case_id);
  requireThat(item && ['public','synthetic'].includes(item.privacy),'case_unavailable',503);
  requireThat(await digest(item.input_json)===item.case_digest,'source_snapshot_changed',503);
  // The committed issuance precedes task disclosure. Hidden oracle is never returned.
  await appendEvent(env,p.attempt_id,'issued',item.case_digest);
  return {attempt_id:p.attempt_id,state:'issued',task:JSON.parse(item.input_json),case_digest:item.case_digest,
    arm:ctx.item.arm,resource_digest:ctx.batch.resource_digest,evidence_class:ctx.campaign.evidence_class};
}
export function validateSubmission(submission,input,oracle) {
  exact(submission,['privacy','answers','execution']);
  requireThat(submission.privacy===input.privacy && ['public','synthetic'].includes(submission.privacy),'privacy_rejected',400);
  exact(submission.execution,['model_id','effort','session_nonce','resource_digest','status']);
  const ex=submission.execution;
  requireThat(ex.model_id==='claude-opus-5' && ex.effort==='xhigh' && UUID.test(ex.session_nonce) && DIGEST.test(ex.resource_digest),'execution_contract_mismatch',400);
  requireThat(['completed','timeout','failed'].includes(ex.status),'invalid_payload',400);
  requireThat(Array.isArray(submission.answers) && submission.answers.length<=LIMITS.obligations,'invalid_payload',400);
  const known=new Map(oracle.obligations.map(x=>[x.id,x])); const seen=new Set();
  const sources=new Set(input.sources.map(x=>x.id));
  for(const answer of submission.answers) {
    exact(answer,['id','status','value','evidence_ids']);
    requireThat(known.has(answer.id) && !seen.has(answer.id),'unknown_or_duplicate_obligation',400); seen.add(answer.id);
    requireThat(['answered','withheld'].includes(answer.status),'invalid_payload',400);
    const o=known.get(answer.id);
    requireThat(answer.value===null || typeof answer.value==='boolean' || (typeof answer.value==='number' && Number.isFinite(answer.value) && Math.abs(answer.value)<=1e15) || (typeof answer.value==='string' && input.answer_vocabulary.includes(answer.value)),'privacy_or_answer_type_rejected',400);
    requireThat(Array.isArray(answer.evidence_ids) && answer.evidence_ids.length<=8 && new Set(answer.evidence_ids).size===answer.evidence_ids.length && answer.evidence_ids.every(x=>sources.has(x)),'unknown_source',400);
    requireThat(o,'invalid_oracle',503);
  }
  return submission;
}
export function grade(submission,oracle) {
  const byId=new Map(submission.answers.map(x=>[x.id,x]));
  let correct=0,supported=0,answeredSupported=0,materialErrors=0,critical=0,sourceSupported=0,numericCorrect=0,numericTotal=0,justified=0;
  for(const o of oracle.obligations) {
    const a=byId.get(o.id);
    if(o.answerable) supported++;
    if(o.answerable && a?.status==='answered') answeredSupported++;
    let valueCorrect=false;
    if(a) {
      if(!o.answerable) valueCorrect=a.status==='withheld' && a.value===null;
      else if(a.status==='answered') {
        valueCorrect=typeof o.value==='number' ? typeof a.value==='number' && Math.abs(a.value-o.value)<=o.tolerance : (o.alternatives || [o.value]).includes(a.value);
      }
    }
    const sourceOk=!!a && (o.source_sets || [[]]).some(group=>group.every(x=>a.evidence_ids.includes(x)));
    if(sourceOk && a?.status==='answered') sourceSupported++;
    if(o.answerable && typeof o.value==='number') { numericTotal++; if(valueCorrect) numericCorrect++; }
    const ok=valueCorrect && sourceOk;
    if(ok) { correct++; if(!o.answerable) justified++; }
    else if(a?.status==='answered' && ['major','critical'].includes(o.severity)) { materialErrors++; if(o.severity==='critical') critical++; }
  }
  const completed=submission.execution.status==='completed';
  return {useful_completion:Number(completed && correct===oracle.obligations.length),correct_obligations:correct,total_obligations:oracle.obligations.length,
    supported_obligations:supported,answered_supported:answeredSupported,material_errors:materialErrors,critical_incidents:critical,
    source_supported:sourceSupported,numeric_correct:numericCorrect,numeric_total:numericTotal,justified_abstentions:justified,
    execution_completed:Number(completed),prose_review:'not_assessed'};
}
async function submit(env,p) {
  exact(p,['attempt_id','submission']);
  const ctx=await attempt(env,p.attempt_id);
  requireThat(ctx.event && ['issued','submitted','scored'].includes(ctx.event.kind),'invalid_transition');
  const c=await one(env.DB,'SELECT * FROM cases WHERE id=?',ctx.item.case_id);
  requireThat(c,'case_unavailable',503);
  validateSubmission(p.submission,JSON.parse(c.input_json),JSON.parse(c.oracle_json));
  requireThat(p.submission.execution.resource_digest===ctx.batch.resource_digest,'resource_mismatch');
  const bytes=canonical(p.submission),hash=await digest(bytes);
  const recorded=await one(env.WITNESS,"SELECT * FROM events WHERE attempt_id=? AND kind='submitted'",p.attempt_id);
  if(recorded) {
    requireThat(recorded.payload_digest===hash,'submission_locked');
    const artifact=await one(env.DB,'SELECT * FROM artifacts WHERE attempt_id=?',p.attempt_id);
    requireThat(artifact && artifact.submission_digest===hash && await digest(artifact.submission_json)===hash,'restored_or_missing_artifact',503);
    return {state:ctx.event.kind,attempt_id:p.attempt_id,replayed:true};
  }
  requireThat(!await isClosed(env,ctx.batch.id) && now(env)<ctx.batch.closes_at,'batch_closed');
  // Witness commits the submitted bytes first. A crash cannot allow a new answer.
  await appendEvent(env,p.attempt_id,'submitted',hash);
  await run(env.DB,'INSERT INTO artifacts(attempt_id,batch_id,submission_digest,submission_json) VALUES(?,?,?,?) ON CONFLICT(attempt_id) DO NOTHING',p.attempt_id,ctx.batch.id,hash,bytes);
  const persisted=await one(env.DB,'SELECT * FROM artifacts WHERE attempt_id=?',p.attempt_id);
  requireThat(persisted?.submission_digest===hash,'restored_or_missing_artifact',503);
  return {state:'submitted',attempt_id:p.attempt_id,replayed:false};
}
async function score(env,p) {
  exact(p,['attempt_id']); const ctx=await attempt(env,p.attempt_id);
  requireThat(ctx.event && ['submitted','scored'].includes(ctx.event.kind),'invalid_transition');
  const artifact=await one(env.DB,'SELECT * FROM artifacts WHERE attempt_id=?',p.attempt_id);
  const submitted=await one(env.WITNESS,"SELECT * FROM events WHERE attempt_id=? AND kind='submitted'",p.attempt_id);
  requireThat(artifact && submitted && artifact.submission_digest===submitted.payload_digest && await digest(artifact.submission_json)===submitted.payload_digest,'restored_or_missing_artifact',503);
  const c=await one(env.DB,'SELECT * FROM cases WHERE id=?',ctx.item.case_id);
  requireThat(c && await digest(c.oracle_json)===ctx.item.oracle_digest,'oracle_snapshot_changed',503);
  const result=grade(JSON.parse(artifact.submission_json),JSON.parse(c.oracle_json));
  const bytes=canonical(result),hash=await digest(bytes);
  await appendEvent(env,p.attempt_id,'scored',hash);
  await run(env.DB,'UPDATE artifacts SET score_json=?,score_digest=? WHERE attempt_id=? AND submission_digest=?',bytes,hash,p.attempt_id,submitted.payload_digest);
  // No correctness bit, error detail, bucket score, or label escapes before close.
  return {attempt_id:p.attempt_id,state:'scored'};
}
async function finish(env,p) {
  exact(p,['attempt_id','outcome']); requireThat(['failed','abandoned'].includes(p.outcome),'invalid_payload',400);
  const ctx=await attempt(env,p.attempt_id);
  requireThat(!await isClosed(env,ctx.batch.id),'batch_closed');
  await appendEvent(env,p.attempt_id,p.outcome,await digest(p.outcome));
  return {attempt_id:p.attempt_id,state:p.outcome};
}
async function batchState(env,batch) {
  const rows=await all(env.DB,'SELECT a.*,c.oracle_json FROM assignments a JOIN cases c ON c.id=a.case_id WHERE a.batch_id=? ORDER BY a.ordinal',batch.id);
  requireThat(rows.length===batch.expected_count,'restored_or_changed_plan',503);
  const burns=await all(env.WITNESS,'SELECT b.*,e.kind,e.payload_digest FROM burns b LEFT JOIN events e ON e.seq=(SELECT MAX(seq) FROM events WHERE attempt_id=b.id) WHERE b.batch_id=?',batch.id);
  const byAssignment=new Map(burns.map(b=>[b.assignment_id,b]));
  return rows.map(a=>({...a,burn:byAssignment.get(a.id) || null}));
}
async function close(env,p) {
  exact(p,['batch_id']); const {batch}=await context(env,p.batch_id);
  const old=await isClosed(env,batch.id); if(old) return {state:'closed',batch_id:batch.id,replayed:true};
  const rows=await batchState(env,batch);
  requireThat(rows.every(x=>TERMINAL.has(x.burn?.kind)) || now(env)>=batch.closes_at,'batch_incomplete');
  const bytes=canonical(rows.map(x=>({assignment:x.id,attempt:x.burn?.id || null,state:x.burn?.kind || 'missing',digest:x.burn?.payload_digest || null})));
  const hash=await digest(bytes);
  await run(env.WITNESS,'INSERT INTO batch_closures(batch_id,plan_digest,closed_at,closure_digest,state_json) VALUES(?,?,?,?,?) ON CONFLICT(batch_id) DO NOTHING',batch.id,batch.plan_digest,now(env),hash,bytes);
  return {state:'closed',batch_id:batch.id,replayed:false};
}
async function seal(env,p) {
  exact(p,['batch_id']); const {batch,campaign}=await context(env,p.batch_id);
  const closure=await isClosed(env,batch.id); requireThat(closure,'batch_not_closed');
  const count=(await one(env.WITNESS,'SELECT COUNT(*) n FROM seals WHERE batch_id=?',batch.id)).n;
  if(count===batch.expected_count) return {state:'sealed',batch_id:batch.id,sealed:count,expected:batch.expected_count};
  const rows=await all(env.DB,'SELECT a.*,c.oracle_json FROM assignments a JOIN cases c ON c.id=a.case_id WHERE a.batch_id=? AND a.ordinal>=? ORDER BY a.ordinal LIMIT ?',batch.id,count,LIMITS.sealSize);
  requireThat(rows.length>0 && rows.every((r,i)=>r.ordinal===count+i),'restored_or_changed_plan',503);
  requireThat(await digest(closure.state_json)===closure.closure_digest,'closure_changed',503);
  const frozen=new Map(JSON.parse(closure.state_json).map(x=>[x.assignment,x]));
  // Late completion cannot change the closed denominator or become a success.
  for(const row of rows) {
    const state=frozen.get(row.id); requireThat(state,'restored_or_changed_plan',503);
    row.burn=state.attempt ? {id:state.attempt,kind:state.state,payload_digest:state.digest} : null;
  }
  const ids=rows.map(r=>r.burn?.id).filter(Boolean), slots=ids.map(()=>'?').join(',');
  const artifacts=ids.length ? await all(env.DB,`SELECT * FROM artifacts WHERE attempt_id IN (${slots})`,...ids) : [];
  const byAttempt=new Map(artifacts.map(x=>[x.attempt_id,x]));
  const scoredEvents=ids.length ? await all(env.WITNESS,`SELECT * FROM events WHERE attempt_id IN (${slots}) AND kind='scored'`,...ids) : [];
  const scoreByAttempt=new Map(scoredEvents.map(x=>[x.attempt_id,x]));
  const fragments=[];
  for(const row of rows) {
    const out={assigned:1,useful_completions:0,missing_or_failed:0,material_errors:0,critical_incidents:0,numeric_correct:0,numeric_total:0,correct_obligations:0,total_obligations:0};
    requireThat(await digest(row.oracle_json)===row.oracle_digest,'oracle_snapshot_changed',503);
    const oracle=JSON.parse(row.oracle_json); out.total_obligations+=oracle.obligations.length;
    const item={assignment_id:row.id,attempt_id:row.burn?.id || null,state:row.burn?.kind || 'missing'};
    fragments.push({ordinal:row.ordinal,arm:row.arm,metrics:out,manifest:item,oracle_digest:row.oracle_digest});
    if(!['scored','released'].includes(row.burn?.kind)) { out.missing_or_failed++; continue; }
    const art=byAttempt.get(row.burn.id);
    const scored=scoreByAttempt.get(row.burn.id);
    requireThat(art?.score_json && scored && await digest(art.score_json)===scored.payload_digest && await digest(art.submission_json)===art.submission_digest,'restored_or_missing_artifact',503);
    const s=JSON.parse(art.score_json); out.useful_completions+=s.useful_completion;
    for(const key of ['material_errors','critical_incidents','numeric_correct','numeric_total','correct_obligations']) out[key]+=s[key];
    if(!s.execution_completed) out.missing_or_failed++;
    item.submission_digest=art.submission_digest; item.score_digest=scored.payload_digest;
  }
  // Four small fragments per request. Atomic witness commit, with deterministic
  // bytes and fixed ordinals, makes concurrent sealing/retries harmless.
  await env.WITNESS.batch(fragments.map(f=>env.WITNESS.prepare('INSERT INTO seals(batch_id,ordinal,fragment_json) VALUES(?,?,?) ON CONFLICT(batch_id,ordinal) DO NOTHING').bind(batch.id,f.ordinal,canonical(f))));
  const next=(await one(env.WITNESS,'SELECT COUNT(*) n FROM seals WHERE batch_id=?',batch.id)).n;
  return {state:next===batch.expected_count?'sealed':'sealing',batch_id:batch.id,sealed:next,expected:batch.expected_count};
}
async function sealedBatch(env,batch) {
  const sealed=await all(env.WITNESS,'SELECT * FROM seals WHERE batch_id=? ORDER BY ordinal',batch.id);
  requireThat(sealed.length===batch.expected_count && sealed.every((s,i)=>s.ordinal===i),'batch_not_sealed');
  const arms=Object.fromEntries(JSON.parse(batch.arms_json).map(a=>[a,{assigned:0,useful_completions:0,missing_or_failed:0,material_errors:0,critical_incidents:0,numeric_correct:0,numeric_total:0,correct_obligations:0,total_obligations:0}]));
  const manifest=[];
  for(const s of sealed) {
    const f=JSON.parse(s.fragment_json),out=arms[f.arm]; requireThat(out,'plan_invalid',503);
    for(const key of Object.keys(out)) out[key]+=f.metrics[key]; manifest.push(f.manifest);
  }
  return {arms,manifest};
}
async function cohortReleaseGate(env,cohort) {
  if(!cohort) return null;
  const closure=await one(env.WITNESS,'SELECT * FROM cohort_closures WHERE cohort_id=?',cohort.id);
  requireThat(closure,'cohort_not_closed');
  requireThat(await digest(closure.state_json)===closure.closure_digest,'cohort_closure_changed',503);
  return closure;
}
async function release(env,p) {
  exact(p,['batch_id']); const {batch,campaign,cohort}=await context(env,p.batch_id);
  const closure=await isClosed(env,batch.id); requireThat(closure,'batch_not_closed');
  const cohortClosure=await cohortReleaseGate(env,cohort);
  requireThat(env.SIGNING_KEY_PKCS8 && env.SIGNING_KEY_ID,'signing_unavailable',503);
  const old=await one(env.DB,'SELECT * FROM releases WHERE batch_id=?',batch.id);
  if(old) {
    const receipt=JSON.parse(old.receipt_json);
    requireThat(receipt.payload?.batch_id===batch.id && receipt.payload?.campaign_id===campaign.id && receipt.payload?.epoch===campaign.epoch && receipt.payload?.plan_digest===batch.plan_digest &&
      (!cohort || receipt.payload?.cohort_id===cohort.id && receipt.payload?.cohort_closure_digest===cohortClosure.closure_digest),'restored_receipt_mismatch',503);
    return receipt;
  }
  const {arms,manifest}=await sealedBatch(env,batch);
  const payload={schema:'osanwe.reasoning-receipt/1',campaign_id:campaign.id,batch_id:batch.id,epoch:campaign.epoch,
    protocol_digest:campaign.protocol_digest,dataset_digest:batch.dataset_digest,plan_digest:batch.plan_digest,
    witness_id:campaign.witness_id,witness_generation:env.EXPECTED_WITNESS_GENERATION,closure_digest:closure.closure_digest,
    evidence_class:campaign.evidence_class,custody_verified:campaign.evidence_class==='independent-admission',
    release_code_sha256:env.RELEASE_CODE_SHA256 || null,
    batch_alpha:0.05/(2**(cohort?.analysis_index || batch.batch_index)),arms,artifact_manifest_sha256:await digest(canonical(manifest)),
    local_execution:'client-reported Claude Opus 5 / xhigh; not provider-attested',
    assessment_scope:'bounded structured obligations; no financial prose or expert certification',
    released_at:closure.closed_at};
  if(cohort) Object.assign(payload,{cohort_id:cohort.id,cohort_plan_digest:cohort.plan_digest,cohort_closure_digest:cohortClosure.closure_digest,
    required_families:cohort.required_families,cohort_assignments:cohort.expected_count,
    analysis_index:cohort.analysis_index,alpha_scope:'whole cohort, shared by all chunks; apply Holm once',purpose:cohort.purpose});
  const receipt=await signed(payload,env);
  receipt.artifact_manifest=manifest;
  await run(env.DB,'INSERT INTO releases(batch_id,receipt_json) VALUES(?,?) ON CONFLICT(batch_id) DO NOTHING',batch.id,canonical(receipt));
  return JSON.parse((await one(env.DB,'SELECT * FROM releases WHERE batch_id=?',batch.id)).receipt_json);
}
async function cohortSeal(env,p) {
  exact(p,['batch_id']); const {batch,cohort}=await context(env,p.batch_id);
  requireThat(cohort,'not_a_cohort_member');
  const closure=await isClosed(env,batch.id); requireThat(closure,'batch_not_closed');
  const member=await one(env.WITNESS,'SELECT * FROM cohort_members WHERE batch_id=?',batch.id);
  const old=await one(env.WITNESS,'SELECT * FROM cohort_fragments WHERE cohort_id=? AND ordinal=?',cohort.id,member.ordinal);
  if(old) return {state:'cohort_member_sealed',batch_id:batch.id,replayed:true};
  const {arms,manifest}=await sealedBatch(env,batch);
  const fragment={batch_id:batch.id,ordinal:member.ordinal,plan_digest:batch.plan_digest,closure_digest:closure.closure_digest,
    snapshot_digest:member.snapshot_digest,family_count:member.family_count,arms,artifact_manifest_sha256:await digest(canonical(manifest))};
  await run(env.WITNESS,'INSERT INTO cohort_fragments(cohort_id,ordinal,fragment_json) VALUES(?,?,?) ON CONFLICT(cohort_id,ordinal) DO NOTHING',cohort.id,member.ordinal,canonical(fragment));
  return {state:'cohort_member_sealed',batch_id:batch.id,replayed:false};
}
async function cohortClose(env,p) {
  exact(p,['cohort_id']); const {cohort,members,freeze}=await cohortContext(env,p.cohort_id);
  await context(env,members[0].batch_id);
  const old=await one(env.WITNESS,'SELECT * FROM cohort_closures WHERE cohort_id=?',cohort.id);
  if(old) return {state:'cohort_closed',cohort_id:cohort.id,replayed:true};
  const fragments=await all(env.WITNESS,'SELECT * FROM cohort_fragments WHERE cohort_id=? ORDER BY ordinal LIMIT ?',cohort.id,LIMITS.cohortChunks+1);
  requireThat(fragments.length===cohort.expected_batches && fragments.every((f,i)=>f.ordinal===i),'cohort_incomplete');
  for(let i=0;i<fragments.length;i++) {
    const f=JSON.parse(fragments[i].fragment_json),member=members[i];
    requireThat(f.batch_id===member.batch_id && f.snapshot_digest===member.snapshot_digest && f.family_count===member.family_count &&
      Object.values(f.arms).reduce((n,a)=>n+a.assigned,0)===member.expected_count,'cohort_fragment_mismatch',503);
  }
  const bytes=canonical({manifest_digest:freeze.manifest_digest,fragments:fragments.map(f=>JSON.parse(f.fragment_json))});
  await run(env.WITNESS,'INSERT INTO cohort_closures(cohort_id,closure_digest,state_json,closed_at) VALUES(?,?,?,?) ON CONFLICT(cohort_id) DO NOTHING',cohort.id,await digest(bytes),bytes,now(env));
  return {state:'cohort_closed',cohort_id:cohort.id,replayed:false};
}
async function cohortRelease(env,p) {
  exact(p,['cohort_id']);const {cohort,members}=await cohortContext(env,p.cohort_id);
  const {campaign}=await context(env,members[0].batch_id);
  const closure=await cohortReleaseGate(env,cohort);
  requireThat(env.SIGNING_KEY_PKCS8 && env.SIGNING_KEY_ID,'signing_unavailable',503);
  const old=await one(env.WITNESS,'SELECT * FROM cohort_releases WHERE cohort_id=?',cohort.id);
  if(old) return JSON.parse(old.receipt_json);
  const state=JSON.parse(closure.state_json),arms={},manifest=[];
  for(const f of state.fragments) {
    for(const [arm,metrics] of Object.entries(f.arms)) {
      const out=(arms[arm] ||= Object.fromEntries(Object.keys(metrics).map(k=>[k,0])));
      for(const k of Object.keys(out)) out[k]+=metrics[k];
    }
    manifest.push({batch_id:f.batch_id,plan_digest:f.plan_digest,closure_digest:f.closure_digest,
      snapshot_digest:f.snapshot_digest,artifact_manifest_sha256:f.artifact_manifest_sha256});
  }
  requireThat(Object.values(arms).reduce((n,a)=>n+a.assigned,0)===cohort.expected_count,'cohort_denominator_mismatch',503);
  const payload={schema:'osanwe.reasoning-cohort-receipt/1',campaign_id:campaign.id,cohort_id:cohort.id,epoch:campaign.epoch,
    protocol_digest:campaign.protocol_digest,plan_digest:cohort.plan_digest,dataset_digest:cohort.dataset_digest,
    required_families:cohort.required_families,assigned:cohort.expected_count,chunks:cohort.expected_batches,
    analysis_index:cohort.analysis_index,batch_alpha:0.05/(2**cohort.analysis_index),
    alpha_scope:'whole cohort, shared by all chunks; apply Holm once',purpose:cohort.purpose,
    witness_id:campaign.witness_id,witness_generation:env.EXPECTED_WITNESS_GENERATION,closure_digest:closure.closure_digest,
    evidence_class:campaign.evidence_class!=='development' && cohort.purpose==='confirmation'?'independent-confirmation':campaign.evidence_class,custody_verified:campaign.evidence_class!=='development',
    release_code_sha256:env.RELEASE_CODE_SHA256 || null,arms,artifact_manifest_sha256:await digest(canonical(manifest)),
    local_execution:'client-reported Claude Opus 5 / xhigh; not provider-attested',
    assessment_scope:'bounded structured obligations; no financial prose, guaranteed power or expert certification',released_at:closure.closed_at};
  const receipt=await signed(payload,env);receipt.artifact_manifest=manifest;
  await run(env.WITNESS,'INSERT INTO cohort_releases(cohort_id,receipt_json) VALUES(?,?) ON CONFLICT(cohort_id) DO NOTHING',cohort.id,canonical(receipt));
  return JSON.parse((await one(env.WITNESS,'SELECT * FROM cohort_releases WHERE cohort_id=?',cohort.id)).receipt_json);
}
async function acknowledge(env,p) {
  exact(p,['attempt_id']); const ctx=await attempt(env,p.attempt_id);
  const release=await one(env.DB,'SELECT receipt_json FROM releases WHERE batch_id=?',ctx.batch.id);
  await cohortReleaseGate(env,ctx.cohort);
  requireThat(release && await isClosed(env,ctx.batch.id),'batch_not_released');
  const receipt=JSON.parse(release.receipt_json);
  await appendEvent(env,p.attempt_id,'released',receipt.payload_sha256);
  return {state:'released',attempt_id:p.attempt_id};
}
export default {
  async fetch(request,env) {
    // Keep this versioned binding on a code rollback. A pre-cohort Worker sees no
    // WITNESS binding and refuses service; it cannot accidentally bypass gating.
    if(env.EVAL_WITNESS_V2) env={...env,WITNESS:env.EVAL_WITNESS_V2};
    try {
      requireThat(request.method==='POST','method_not_allowed',405);
      await authenticate(request,env);
      const routes={'/v1/reserve':reserve,'/v1/issue':issue,'/v1/submit':submit,'/v1/score':score,'/v1/finish':finish,'/v1/close':close,'/v1/seal':seal,'/v1/release':release,'/v1/acknowledge':acknowledge,
        '/v1/cohort-seal':cohortSeal,'/v1/cohort-close':cohortClose,'/v1/cohort-release':cohortRelease};
      const route=routes[new URL(request.url).pathname]; requireThat(route,'not_found',404);
      const result=await route(env,await body(request));
      return Response.json(result,{headers:{'cache-control':'no-store'}});
    } catch(error) {
      // Never include request bytes, SQL errors, hidden answers, credentials, or stack traces.
      return Response.json({status:'refused',error:error instanceof Refusal ? error.code : 'internal_failure'},
        {status:error instanceof Refusal ? error.status : 503,headers:{'cache-control':'no-store'}});
    }
  }
};
