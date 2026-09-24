// Frozen, offline development comparison. Reports outcomes; never asserts a winner.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdtempSync,mkdirSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve,dirname,basename} from 'node:path';
import vm from 'node:vm';
import {specification,comparisonDocuments,comparisonCases} from './retrieval-comparison-fixtures.mjs';
import {sha,canonical,buildGeneration,publishGeneration,queryGeneration} from './retrieval-core.mjs';
import {provider} from 'file:////path/to/home/.vault-substrate/retrieval-provider.mjs';

const legacyDirectory=process.argv.slice(2).find(x=>!x.startsWith('--')) || '/path/to/vault/.checkpoints/financial-corpus-20260913T184023Z/retrieval-before';
const fixturePath=new URL('./retrieval-comparison-fixtures.mjs',import.meta.url);
const frozen={specification_sha256:sha(readFileSync(fixturePath)),
  original_fixtures_sha256:sha(readFileSync(new URL('./retrieval-fixtures.mjs',import.meta.url))),
  comparator_sha256:sha(readFileSync(new URL(import.meta.url))),
  legacy_indexer_sha256:sha(readFileSync(join(legacyDirectory,'index-vault.mjs'))),
  legacy_server_sha256:sha(readFileSync(join(legacyDirectory,'server.py'))),
  core_sha256:sha(readFileSync(new URL('./retrieval-core.mjs',import.meta.url))),
  provider_sha256:sha(readFileSync('/path/to/home/.vault-substrate/retrieval-provider.mjs'))};
if (process.argv.includes('--freeze')) { console.log(JSON.stringify({schema:'osanwe.retrieval-comparison-freeze/1',...frozen,specification})); process.exit(0); }
globalThis.fetch=()=>{throw new Error('network-disabled-in-synthetic-comparison');};
const started=Date.now(), root=mkdtempSync(join(tmpdir(),'osanwe-retrieval-comparison-')),base=join(root,'candidate');
mkdirSync(join(root,'wiki')); mkdirSync(base);
const normalized=text=>text.replace(/\s+/g,' ').toLowerCase();
const cost=h=>h.text.length+(h.context_spans??[]).reduce((n,s)=>n+s.text.length,0);
function budget(hits) {
  const selected=[]; let characters=0;
  for (const hit of hits) if(selected.length<specification.top_k && characters+cost(hit)<=specification.maximum_characters) {
    selected.push(hit); characters+=cost(hit);
  }
  return {hits:selected,characters};
}
function score(test,hits) {
  const evidence=normalized(hits.map(h=>[h.text,...(h.context_spans??[]).map(x=>x.text)].join('\n')).join('\n'));
  const outcomes=test.obligations.map((o,i)=>({obligation:i+1,kind:o.kind,passed:o.contains.every(x=>evidence.includes(normalized(x)))}));
  return {outcomes,supported:outcomes.filter(x=>x.passed).length,total:outcomes.length,complete:outcomes.every(x=>x.passed)};
}
function legacyBM25(chunks,query) {
  const tokens=s=>s.toLowerCase().match(/[a-z0-9]+/g)??[], rows=chunks.map(c=>tokens(c.preview));
  const terms=[...new Set(tokens(query))], n=rows.length, avg=rows.reduce((s,r)=>s+r.length,0)/n;
  const df=Object.fromEntries(terms.map(t=>[t,rows.filter(r=>r.includes(t)).length]));
  return rows.map((row,label)=>({label,score:terms.reduce((sum,t)=>{
    const f=row.filter(x=>x===t).length;return sum+(f?Math.log(1+(n-df[t]+.5)/(df[t]+.5))*f*2.5/(f+1.5*(.25+.75*row.length/(avg||1))):0);
  },0)})).filter(x=>x.score>0).sort((a,b)=>b.score-a.score||a.label-b.label).slice(0,25);
}
try {
  const rawLegacy=readFileSync(join(legacyDirectory,'index-vault.mjs'),'utf8');
  const pureLegacy=rawLegacy.slice(rawLegacy.indexOf('function stripFrontmatter('),rawLegacy.indexOf('const t0 = Date.now();'));
  assert(pureLegacy.startsWith('function stripFrontmatter('));
  const legacyChunks=[];
  const documents=comparisonDocuments.map(row=>{
    const path='wiki/'+row.id+'.md';writeFileSync(join(root,path),row.text);
    const old=vm.runInNewContext(pureLegacy+'\nchunkFile("wiki/synthetic.md")',{
      ROOT:'synthetic',CHUNK_CHARS:1200,MAX_CHARS:1800,readApprovedMarkdown:()=>row.text});
    for(const part of old) legacyChunks.push({...part,document_id:row.id,scope:row.scope,
      preview:part.text.replace(/\s+/g,' ').slice(0,300)});
    return {document_id:row.id,source_version:'1',source_origin_id:'synthetic:'+row.id,source_path:path,
      sha256:sha(row.text),classification:'SYNTHETIC',status:'admitted',eligible:true,kind:'method',
      source_uri:'synthetic://'+row.id,approved_use:[row.scope],applicability:'Synthetic development control only',
      published_at:'2026-09-01T00:00:00Z',available_at:'2026-09-01T00:00:00Z',reviewed_at:'2026-09-13T00:00:00Z',
      supersedes:[],chunks:[{chunk_id:row.id,locator:{start_line:1,end_line:row.text.split('\n').length-1,heading:'Synthetic'},
        approved_use:[row.scope],claim_ids:[]}]};
  });
  const native=await provider('/path/to/home/.vault-substrate');
  const {pipeline,env}=await import('file:////path/to/home/.vault-substrate/node_modules/@xenova/transformers/src/transformers.js');
  env.allowRemoteModels=false;env.localModelPath='/path/to/home/.vault-substrate/.models/';
  env.cacheDir='/path/to/home/.vault-substrate/.models';
  const legacyExtractor=await pipeline('feature-extraction',native.identity.name);
  const legacyEmbed=async texts=>{
    const output=await legacyExtractor(texts,{pooling:'mean',normalize:true});
    return texts.map((_,i)=>Array.from(output.data.subarray(i*768,(i+1)*768)));
  };
  const buildStart=Date.now();
  const admission={schema:'osanwe.financial-document-manifest/1',documents,exclusions:[],
    manifest_sha256:sha(canonical(documents)),registry_sha256:sha('frozen-synthetic-comparison-registry')};
  const runtimeIdentity={sha256:sha(canonical(frozen))}, args={root,base,admission,provider:native,runtimeIdentity};
  const candidate=await buildGeneration(args);publishGeneration({...args,candidate,providerIdentity:native.identity});
  const repairedBuildMs=Date.now()-buildStart;
  const legacyBuildStart=Date.now(),legacyVectors=await legacyEmbed(legacyChunks.map(x=>x.text));
  const legacyIndex=join(root,'legacy-synthetic.hnsw');native.write(legacyIndex,legacyVectors);
  const legacyBuildMs=Date.now()-legacyBuildStart;
  // Warm both query paths once without looking at a graded query or returned hits.
  await native.embedQuery('ungraded synthetic warmup');await legacyEmbed([native.identity.query_prefix+'ungraded synthetic warmup']);
  async function oldQuery(test) {
    const local=legacyChunks.map((x,label)=>({...x,label})).filter(x=>x.scope===test.scope);
    const lexical=legacyBM25(local,test.query).map(x=>({...x,label:local[x.label].label}));
    const [queryVector]=await legacyEmbed([native.identity.query_prefix+test.query]);
    // Favorable legacy scope control: apply the same scope before the top-25 limit.
    const dense=native.search(legacyIndex,queryVector,legacyChunks.length).filter(x=>legacyChunks[x.label].scope===test.scope).slice(0,25);
    const ranks=new Map();
    for(const list of [dense,lexical]) list.forEach((x,i)=>ranks.set(x.label,(ranks.get(x.label)??0)+1/(61+i)));
    const fused=[...ranks.entries()].sort((a,b)=>b[1]-a[1]);
    const reranked=fused.slice(0,12).map(([label])=>({label,score:Number(legacyVectors[label].reduce((s,x,i)=>s+x*queryVector[i],0).toFixed(4))})).sort((a,b)=>b.score-a.score);
    const selected=reranked.slice(0,specification.top_k).map(x=>legacyChunks[x.label]);
    return {delivered:budget(selected.map(x=>({...x,text:x.preview}))),expanded:budget(selected)};
  }
  let seed=specification.seed;
  const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
  const schedule=comparisonCases.flatMap(test=>specification.comparison.map(variant=>({test,variant,order:random()}))).sort((a,b)=>a.order-b.order);
  const rows=[];
  for(const {test,variant} of schedule) {
    const queryStart=Date.now(); let output,state='passed';
    if(variant==='legacy-preview-hybrid') output=await oldQuery(test);
    else {
      const response=await queryGeneration({...args,query:test.query,scope:test.scope,
        mode:variant==='narrow-lexical'?'lexical':'hybrid',topK:specification.top_k,maximumChars:specification.maximum_characters});
      state=response.state;const view=budget(response.hits);output={delivered:view,expanded:view};
    }
    const queryMs=Date.now()-queryStart;
    for(const [view,value] of [['as-delivered',output.delivered],['common-full-passage-expansion',output.expanded]]) {
      assert(value.hits.length<=specification.top_k && value.characters<=specification.maximum_characters);
      rows.push({case_id:test.id,family:test.family,variant,view,state,query_ms:queryMs,characters:value.characters,
        selected_documents:value.hits.map(x=>x.document_id),...score(test,value.hits)});
    }
  }
  native.verify();
  const metrics=specification.comparison.flatMap(variant=>specification.evidence_views.map(view=>{
    const subset=rows.filter(r=>r.variant===variant&&r.view===view),supported=subset.reduce((s,r)=>s+r.supported,0),total=subset.reduce((s,r)=>s+r.total,0);
    return {variant,view,queries:subset.length,complete_tasks:subset.filter(r=>r.complete).length,obligations_supported:supported,
      obligations_total:total,sufficiency_fraction:supported/total,query_ms_total:subset.reduce((s,r)=>s+r.query_ms,0),
      returned_characters:subset.reduce((s,r)=>s+r.characters,0),failures:subset.filter(r=>!r.complete).map(r=>r.case_id)};
  }));
  console.log(JSON.stringify({schema:'osanwe.retrieval-development-comparison/1',state:'completed',classification:'SYNTHETIC',
    frozen,specification,model:native.identity,documents:documents.length,independent_scenario_families:6,queries:comparisonCases.length,
    legacy_passages:legacyChunks.length,repaired_passages:candidate.manifest.passage_count,build_ms:{legacy:legacyBuildMs,repaired:repairedBuildMs},
    embedding:native.diagnostics(),metrics,rows,elapsed_ms:Date.now()-started,network_access:false,live_index_modified:false,
    conclusion:'Development retrieval mechanics and evidence sufficiency only. Lexical remains default; hybrid experimental. No model answer, real-vault, independent financial, alpha, or production quality claim.',
    limitations:['Small authored public synthetic controls; related queries share six scenarios and are not independent trials.',
      'Obligation checks detect literal evidence presence, not correct interpretation, adequate answers, expert review, or absence of contradictions.',
      'Legacy reconstruction is deliberately favorable: matched scope, common native cache, one query embedding, optional full selected chunk expansion.',
      'Complete table contexts differ from historical split chunks; compare repaired lexical and hybrid to isolate ranking on identical repaired passages.',
      'Warm within-process latency includes generation integrity checks only on repaired paths; it is diagnostic, not an operational latency benchmark.',
      'No statistical significance, independent holdout or bank-equivalence inference is supported.']}));
} finally {
  assert.equal(resolve(dirname(root)),resolve(tmpdir()));assert(basename(root).startsWith('osanwe-retrieval-comparison-'));
  rmSync(root,{recursive:true,force:true});
}
