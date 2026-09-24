/* Build a reviewable DEVELOPMENT D1 load. Never produce sealed admission data. */
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,join} from 'node:path';
import {randomUUID} from 'node:crypto';
import {canonical,digest} from './service/worker.mjs';

const root=new URL('.',import.meta.url);
const out=process.argv[2];
if(!out) { process.stderr.write('Usage: node evaluation/prepare_deployment.mjs <new-output-directory>\n'); process.exit(2); }
const directory=resolve(out);
if(directory.split(/[\\/]/).some(s=>['private','finance','credentials','.raw','holdout','holdouts','hidden','locked'].includes(s.toLowerCase()))) throw new Error('protected destination');
mkdirSync(directory,{recursive:false});
const pack=JSON.parse(readFileSync(new URL('development_cases.json',root),'utf8'));
if(pack.admission_eligible || pack.cases.length!==36) throw new Error('development-only pack required');
const arms=['baseline','revised_no_library','revised_library'];
const resource={model:'claude-opus-5',effort:'xhigh',inference:'local first-party subscription',timeout_seconds:240,max_turns:12};
const protocol=await digest(readFileSync(new URL('reasoning_protocol.json',root)));
const dataset=await digest(canonical(pack));
const resources=await digest(canonical(resource));
const campaign='osanwe-reasoning-development-v1',batch='development-batch-1',epoch=randomUUID(),generation=randomUUID();
const candidate=Object.fromEntries(await Promise.all(arms.map(async arm=>[arm,await digest('REPLACE_WITH_REVIEWED_FROZEN_CANDIDATE_'+arm)])));
const assignments=[];
for(const c of pack.cases) for(const arm of arms) assignments.push({id:randomUUID(),case_id:c.id,arm,candidate_digest:candidate[arm]});
// Fisher-Yates with crypto entropy: order is fixed by the emitted signed-plan
// candidate artifact, not chosen in response to any outcome.
for(let i=assignments.length-1;i>0;i--) { const v=new Uint32Array(1);crypto.getRandomValues(v);const j=v[0]%(i+1);[assignments[i],assignments[j]]=[assignments[j],assignments[i]]; }
const plan={campaign_id:campaign,batch_id:batch,batch_index:1,protocol_digest:protocol,dataset_digest:dataset,
  resource_digest:resources,arms,candidates:candidate,assignments,evidence_class:'development',
  production_eligible:false,required_setup:'Replace candidate placeholders with reviewed native freeze; independent custody remains unverified.'};
const planDigest=await digest(canonical(plan));
const q=v=>v===null?'NULL':typeof v==='number'?String(v):"'"+String(v).replaceAll("'","''")+"'";
const insert=(table,values)=>`INSERT INTO ${table} VALUES(${values.map(q).join(',')});`;
const db=[readFileSync(new URL('service/schema.sql',root),'utf8')];
db.push(insert('campaigns',[campaign,protocol,dataset,epoch,'custodian-witness', 'development',null,'frozen']));
db.push(insert('batches',[batch,campaign,planDigest,assignments.length,1,new Date(Date.now()+86400000).toISOString(),canonical(arms),resources,dataset]));
for(const c of pack.cases) {
  const input=canonical(c.input),oracle=canonical(c.oracle);
  db.push(insert('cases',[c.id,c.family,c.scenario_family,c.source_family,c.version,await digest(input),await digest(oracle),c.privacy,input,oracle]));
}
for(let i=0;i<assignments.length;i++) {
  const a=assignments[i],c=pack.cases.find(c=>c.id===a.case_id);
  db.push(insert('assignments',[a.id,batch,a.case_id,a.arm,a.candidate_digest,i,await digest(canonical(c.oracle))]));
}
const witness=[readFileSync(new URL('service/witness.sql',root),'utf8'),
  insert('custody',['custodian-witness',generation]),insert('quotas',[campaign,epoch,assignments.length,protocol]),
  insert('batch_plans',[batch,campaign,1,planDigest]),insert('analysis_slots',[campaign,1,'batch',batch])];
writeFileSync(join(directory,'case-database.sql'),db.join('\n')+'\n');
writeFileSync(join(directory,'witness-database.sql'),witness.join('\n')+'\n');
writeFileSync(join(directory,'public-plan.json'),canonical({...plan,plan_digest:planDigest,epoch,witness_generation:generation})+'\n');
writeFileSync(join(directory,'bundle-manifest.json'),canonical({schema:'osanwe.evaluator-load/1',evidence_class:'development',
  files:Object.fromEntries(['case-database.sql','witness-database.sql','public-plan.json'].map(name=>[name,readFileSync(join(directory,name)).length])),
  private_keys_generated:false,hosted_deployment_performed:false,placeholder_candidates:true})+'\n');
process.stdout.write(canonical({status:'development-load-prepared',directory,assignments:assignments.length,production_eligible:false})+'\n');
