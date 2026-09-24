/* Local D1 behavioral adapter, not a security enclave or Cloudflare benchmark. */
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {createServer} from 'node:http';
import {randomUUID} from 'node:crypto';
import worker,{canonical,digest} from './worker.mjs';
import {freezeCohort} from './cohort-freeze.mjs';

export class LocalD1 {
  constructor(path=':memory:') { this.db=new DatabaseSync(path); this.calls=0; this.failOn=null; }
  check() { this.calls++; if(this.failOn===this.calls) throw new Error('injected storage failure'); }
  exec(sql) { this.db.exec(sql); }
  prepare(sql) {
    const owner=this;
    function statement(values=[]) {
      return {
        sql,values,
        bind(...v) { return statement(v); },
        async first() { owner.check(); const row=owner.db.prepare(sql).get(...values);return row?{...row}:null; },
        async all() { owner.check(); return {results:owner.db.prepare(sql).all(...values).map(row=>({...row}))}; },
        async run() { owner.check(); const result=owner.db.prepare(sql).run(...values); return {meta:{changes:Number(result.changes)}}; }
      };
    }
    return statement();
  }
  async batch(statements) {
    this.check(); this.db.exec('BEGIN IMMEDIATE');
    try {
      const result=statements.map(s=>{this.check(); return {meta:{changes:Number(this.db.prepare(s.sql).run(...s.values).changes)}};});
      this.db.exec('COMMIT'); return result;
    } catch(error) { this.db.exec('ROLLBACK'); throw error; }
  }
  close() { this.db.close(); }
}

export async function createDevelopment({cases, arms=['baseline','revised_no_library','revised_library'], quota, database, witness, cohortChunkCases=null, freezeCohortPlan=true}={}) {
  const DB=new LocalD1(database),WITNESS=new LocalD1(witness);
  DB.exec(readFileSync(new URL('./schema.sql',import.meta.url),'utf8'));
  WITNESS.exec(readFileSync(new URL('./witness.sql',import.meta.url),'utf8'));
  const key=await crypto.subtle.generateKey('Ed25519',true,['sign','verify']);
  const token=randomUUID()+randomUUID();
  const to64=b=>Buffer.from(b).toString('base64');
  const env={DB,WITNESS,SUBMISSION_TOKEN_SHA256:await digest(token),SIGNING_KEY_ID:'ephemeral-development-only',
    SIGNING_KEY_PKCS8:to64(await crypto.subtle.exportKey('pkcs8',key.privateKey)),
    EXPECTED_WITNESS_GENERATION:randomUUID(),TEST_NOW:'2026-09-13T00:00:00.000Z',CUSTODY_VERIFIED:'false'};
  const publicKey=to64(await crypto.subtle.exportKey('spki',key.publicKey));
  const protocolDigest=await digest('synthetic-development-protocol-v1');
  const resourceDigest=await digest('Opus5-xhigh-identical-budget-development-v1');
  const dataDigest=await digest(canonical(cases));
  const planDigest=await digest(canonical({cases:cases.map(c=>c.id),arms,resourceDigest,protocolDigest}));
  DB.db.prepare('INSERT INTO campaigns VALUES(?,?,?,?,?,?,?,?)').run('dev-campaign',protocolDigest,dataDigest,'dev-epoch','dev-witness','development',null,'frozen');
  WITNESS.db.prepare('INSERT INTO custody VALUES(?,?)').run('dev-witness',env.EXPECTED_WITNESS_GENERATION);
  WITNESS.db.prepare('INSERT INTO quotas VALUES(?,?,?,?)').run('dev-campaign','dev-epoch',quota || cases.length*arms.length,protocolDigest);
  if(cohortChunkCases!==null && (!Number.isInteger(cohortChunkCases) || cohortChunkCases<1 || cohortChunkCases>72)) throw new Error('bounded chunk size required');
  const chunks=cohortChunkCases===null?[cases]:Array.from({length:Math.ceil(cases.length/cohortChunkCases)},(_,i)=>cases.slice(i*cohortChunkCases,(i+1)*cohortChunkCases));
  const batchIds=chunks.map((_,i)=>cohortChunkCases===null?'dev-batch':`dev-chunk-${i}`);
  for(let i=0;i<chunks.length;i++) {
    const id=batchIds[i],hash=cohortChunkCases===null?planDigest:await digest(canonical({planDigest,id,cases:chunks[i].map(c=>c.id)}));
    DB.db.prepare('INSERT INTO batches VALUES(?,?,?,?,?,?,?,?,?)').run(id,'dev-campaign',hash,chunks[i].length*arms.length,i+1,'2026-09-14T00:00:00.000Z',JSON.stringify(arms),resourceDigest,dataDigest);
    WITNESS.db.prepare('INSERT INTO batch_plans VALUES(?,?,?,?)').run(id,'dev-campaign',i+1,hash);
  }
  if(cohortChunkCases===null) WITNESS.db.prepare('INSERT INTO analysis_slots VALUES(?,?,?,?)').run('dev-campaign',1,'batch','dev-batch');
  const assignments=[];
  for(let ci=0;ci<cases.length;ci++) {
    const c=cases[ci],batchId=batchIds[cohortChunkCases===null?0:Math.floor(ci/cohortChunkCases)];
    const input=canonical(c.input),oracle=canonical(c.oracle),hash=await digest(input),oracleHash=await digest(oracle);
    DB.db.prepare('INSERT INTO cases VALUES(?,?,?,?,?,?,?,?,?,?)').run(c.id,c.family,c.scenario_family,c.source_family,c.version,hash,oracleHash,c.privacy,input,oracle);
    for(const arm of arms) {
      const id=`${c.id}-${arm}`,candidate=await digest(`development-${arm}`),ordinal=cohortChunkCases===null?assignments.length:(ci%cohortChunkCases)*arms.length+arms.indexOf(arm);
      DB.db.prepare('INSERT INTO assignments VALUES(?,?,?,?,?,?,?)').run(id,batchId,c.id,arm,candidate,ordinal,oracleHash);
      assignments.push({assignment_id:id,candidate_digest:candidate,protocol_digest:protocolDigest,idempotency_key:randomUUID()});
    }
  }
  if(cohortChunkCases!==null) {
    env.EVAL_WITNESS_V2=WITNESS;
    if(freezeCohortPlan) await freezeCohort(env,{id:'dev-cohort',campaign_id:'dev-campaign',analysis_index:1,batch_ids:batchIds,required_families:cases.length});
  }
  return {env,token,publicKey,assignments,resourceDigest,batchIds,cohortId:cohortChunkCases===null?null:'dev-cohort',close(){DB.close();WITNESS.close();}};
}

export async function call(dev,operation,payload,options={}) {
  const req=new Request('http://localhost/v1/'+operation,{method:'POST',headers:{'content-type':'application/json',authorization:'Bearer '+dev.token},body:JSON.stringify(payload),...options});
  const response=await worker.fetch(req,dev.env);
  return {status:response.status,body:await response.json()};
}

export function correctSubmission(c,resourceDigest) {
  return {privacy:c.privacy,answers:c.oracle.obligations.map(o=>({id:o.id,status:o.answerable?'answered':'withheld',value:o.value,evidence_ids:o.source_sets[0]})),
    execution:{model_id:'claude-opus-5',effort:'xhigh',session_nonce:randomUUID(),resource_digest:resourceDigest,status:'completed'}};
}

if(process.argv[1]===fileURLToPath(import.meta.url)) {
  const cases=JSON.parse(readFileSync(new URL('../development_cases.json',import.meta.url),'utf8')).cases;
  const dev=await createDevelopment({cases});
  // Only loopback, ephemeral DBs and ephemeral key. No upstream credential is read.
  const server=createServer(async(req,res)=>{
    const url='http://127.0.0.1'+req.url;
    const request=new Request(url,{method:req.method,headers:req.headers,body:req.method==='POST'?req:undefined,duplex:'half'});
    const response=await worker.fetch(request,dev.env);
    res.writeHead(response.status,Object.fromEntries(response.headers)); res.end(Buffer.from(await response.arrayBuffer()));
  });
  server.listen(0,'127.0.0.1',()=>{
    // Do not write credentials, even ephemeral ones, to logs. A caller embedding
    // createDevelopment can put the token directly in its child environment.
    process.stdout.write(JSON.stringify({status:'development-only',endpoint:`http://127.0.0.1:${server.address().port}`,credential:'available only through embedded API',assignments:dev.assignments.length})+'\n');
  });
}
