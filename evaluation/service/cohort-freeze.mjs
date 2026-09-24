/* Custodian-only preparation helper, never a Worker route or research client API.
 * Freeze all members before any reservation. A primary DB restore cannot edit
 * the resulting witness commitment. Case independence still needs real review.
 */
import {canonical,digest,batchSnapshot,LIMITS} from './worker.mjs';

const ARMS=['baseline','revised_no_library','revised_library'];
function check(ok,message) { if(!ok) throw new Error(message); }
async function one(db,sql,...p) {return db.prepare(sql).bind(...p).first();}

export async function freezeCohort(env,{id,campaign_id,analysis_index,batch_ids,required_families,purpose='development'}) {
  check(typeof id==='string' && /^[a-zA-Z0-9_-]{1,80}$/.test(id),'bounded cohort identity required');
  check(Number.isInteger(analysis_index) && analysis_index>0 && analysis_index<1024,'valid campaign analysis index required');
  check(['development','confirmation'].includes(purpose),'invalid cohort purpose');
  check(Array.isArray(batch_ids) && batch_ids.length>=1 && batch_ids.length<=LIMITS.cohortChunks && new Set(batch_ids).size===batch_ids.length,'bounded unique chunks required');
  check(Number.isInteger(required_families) && required_families>0 && required_families<=2304,'fixed family sample required');
  const old=await one(env.WITNESS,'SELECT * FROM cohort_plans WHERE id=?',id);
  const snapshots=[],members=[],candidate={},scenarios=new Set(),sources=new Set();
  let resources=null,total=0,families=0;
  for(let ordinal=0;ordinal<batch_ids.length;ordinal++) {
    const batch=await one(env.DB,'SELECT * FROM batches WHERE id=?',batch_ids[ordinal]);
    check(batch?.campaign_id===campaign_id,'cohort campaign mismatch');
    const admission=await one(env.WITNESS,'SELECT * FROM batch_plans WHERE batch_id=?',batch.id);
    check(admission?.campaign_id===campaign_id && admission.plan_digest===batch.plan_digest && admission.batch_index===batch.batch_index,'unadmitted chunk');
    check(JSON.stringify(JSON.parse(batch.arms_json).slice().sort())===JSON.stringify(ARMS.slice().sort()),'three paired arms required');
    check(resources===null || resources===batch.resource_digest,'unequal resource budgets');resources=batch.resource_digest;
    const snapshot=await batchSnapshot(env,batch),byCase=new Map();
    for(const a of snapshot.assignments) {
      check(ARMS.includes(a.arm) && /^[0-9a-f]{64}$/.test(a.candidate_digest),'invalid candidate');
      check(!candidate[a.arm] || candidate[a.arm]===a.candidate_digest,'candidate changed across chunks');candidate[a.arm]=a.candidate_digest;
      const group=(byCase.get(a.case_id) || []);group.push(a);byCase.set(a.case_id,group);
    }
    // One representative scenario/source family per paired case. Duplicate or
    // related case metadata are rejected; renaming tickers/numbers adds no units.
    for(const group of byCase.values()) {
      check(group.length===3 && new Set(group.map(a=>a.arm)).size===3,'incomplete paired case');
      const c=group[0];
      check(c.scenario_family && c.source_family && !scenarios.has(c.scenario_family) && !sources.has(c.source_family),'shared source or scenario is not an independent family');
      scenarios.add(c.scenario_family);sources.add(c.source_family);
    }
    const member={cohort_id:id,batch_id:batch.id,ordinal,expected_count:batch.expected_count,family_count:byCase.size,
      snapshot_digest:await digest(canonical(snapshot))};
    members.push(member);snapshots.push(snapshot);total+=batch.expected_count;families+=byCase.size;
  }
  check(families===required_families && total===3*required_families,'fixed family sample mismatch');
  const definition={id,campaign_id,analysis_index,purpose,required_families,members,candidates:candidate,resource_digest:resources};
  const cohort={id,campaign_id,analysis_index,plan_digest:await digest(canonical(definition)),expected_batches:members.length,
    expected_count:total,required_families,arms_json:canonical(ARMS),resource_digest:resources,
    dataset_digest:await digest(canonical(snapshots.map(s=>s.assignments.map(a=>({case_id:a.case_id,case_digest:a.case_digest,oracle_digest:a.oracle_digest}))))),purpose};
  const manifest=await digest(canonical({cohort,members}));
  if(old) {
    const freeze=await one(env.WITNESS,'SELECT * FROM cohort_freezes WHERE cohort_id=?',id);
    check(canonical(old)===canonical(cohort) && freeze?.manifest_digest===manifest,'cohort freeze is immutable');
    return {cohort_id:id,manifest_digest:manifest,replayed:true};
  }
  for(const m of members) {
    check(!await one(env.WITNESS,'SELECT 1 FROM burns WHERE batch_id=? LIMIT 1',m.batch_id),'cannot freeze exposed attempts');
    check(!await one(env.WITNESS,'SELECT 1 FROM analysis_slots WHERE owner_kind=? AND owner_id=?','batch',m.batch_id),'standalone analysis slot already spent');
    check(!await one(env.DB,'SELECT 1 FROM releases WHERE batch_id=?',m.batch_id),'cannot regroup released results');
  }
  const statements=[env.WITNESS.prepare('INSERT INTO analysis_slots VALUES(?,?,?,?)').bind(campaign_id,analysis_index,'cohort',id),
    env.WITNESS.prepare('INSERT INTO cohort_plans VALUES(?,?,?,?,?,?,?,?,?,?,?)').bind(...Object.values(cohort))];
  // The order above matches the explicit cohort_plans schema. All preparation
  // writes, including the final freeze marker, commit together or not at all.
  for(const m of members) statements.push(env.WITNESS.prepare('INSERT INTO cohort_members VALUES(?,?,?,?,?,?)').bind(...Object.values(m)));
  statements.push(env.WITNESS.prepare('INSERT INTO cohort_freezes VALUES(?,?)').bind(id,manifest));
  try {await env.WITNESS.batch(statements);}
  catch(error) {
    const replay=await one(env.WITNESS,'SELECT * FROM cohort_freezes WHERE cohort_id=?',id);
    if(replay?.manifest_digest===manifest) return {cohort_id:id,manifest_digest:manifest,replayed:true};
    throw error;
  }
  return {cohort_id:id,manifest_digest:manifest,replayed:false};
}
