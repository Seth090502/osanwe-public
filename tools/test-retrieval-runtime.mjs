// Deterministic admitted-corpus controls. Synthetic provider != semantic quality.
import assert from 'node:assert/strict';
import {mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync, existsSync, unlinkSync, symlinkSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {spawnSync} from 'node:child_process';
import {join, resolve, dirname, basename} from 'node:path';
import {fixtures} from './retrieval-fixtures.mjs';
import {sha, canonical, chunkDocument, admittedDocuments, buildGeneration, publishGeneration, pinGeneration,
  queryGeneration, inspectRuntime, failureResult, lexicalRanks, RetrievalError, acquireBuildLock, tokenWindows} from './retrieval-core.mjs';

const root = mkdtempSync(join(tmpdir(), 'osanwe-retrieval-control-'));
const base = join(root, 'runtime'), runtimeIdentity = {sha256:sha('frozen synthetic runtime')};
mkdirSync(join(root, 'wiki'), {recursive:true}); mkdirSync(base);
const outcomes = [];
function record(name, check) { check(); outcomes.push(name); }
async function control(name, check) { await check(); outcomes.push(name); }
const countLines = text => text.split('\n').length - (text.endsWith('\n') ? 1 : 0);
function document(id, text, change = {}) {
  const path = 'wiki/' + id + '.md'; writeFileSync(join(root, path), text);
  return {document_id:id, source_version:'1', source_origin_id:'synthetic:' + id, source_path:path,
    sha256:sha(Buffer.from(text)), classification:'SYNTHETIC', status:'admitted', eligible:true, kind:'method',
    source_uri:'synthetic://' + id, approved_use:['research'], applicability:'Synthetic method controls only',
    available_at:'2026-09-01T00:00:00Z', published_at:'2026-09-01T00:00:00Z', reviewed_at:'2026-09-13T00:00:00Z',
    supersedes:[], chunks:[{chunk_id:id + '-passage', locator:{start_line:1, end_line:countLines(text), heading:'Control'},
      approved_use:['research'], claim_ids:[id + '-claim']}], ...change};
}
function manifest(docs, version = '1') {
  return {schema:'osanwe.financial-document-manifest/1', generated_at:'2026-09-13T00:00:00Z',
    manifest_sha256:sha(canonical({docs, version})), registry_sha256:sha(version), documents:docs, exclusions:[]};
}
let embeds = 0;
const vectors = texts => texts.map(text => {
  const bytes = Buffer.from(sha(text).slice(0, 8), 'hex');
  const v = [...bytes].map(x => x / 255), norm = Math.hypot(...v); return v.map(x => x / norm);
});
const provider = {identity:{name:'frozen-hash-control', dimension:4, kind:'SYNTHETIC_NO_INFERENCE'},
  embed:async texts => { embeds++; return vectors(texts); }, embedQuery:async text => vectors([text]),
  write:async(path, rows) => writeFileSync(path, JSON.stringify(rows)),
  search:async(path, vector, k) => JSON.parse(readFileSync(path)).map((row, label) =>
    ({label, score:row.reduce((s, x, i) => s + x * vector[i], 0)})).sort((a,b) => b.score - a.score).slice(0,k)};
try {
  const docs = [document('late', fixtures.lateTerm), document('table', fixtures.longTable), document('lines', fixtures.exactLines)];
  let admission = manifest(docs);
  const args = () => ({root, base, admission, provider, runtimeIdentity});
  record('unknown classification refused before nonexistent file read', () => {
    const unknown = {...docs[0], classification:'UNKNOWN', source_path:'wiki/not-there.md'};
    assert.throws(() => admittedDocuments(manifest([unknown]), root), /document-not-publicly-admitted/);
    assert.equal(embeds,0);
  });
  record('mixed and protected paths cannot be admitted', () => {
    assert.throws(() => admittedDocuments(manifest([{...docs[0], classification:'MIXED'}]), root), /not-publicly-admitted/);
    assert.throws(() => admittedDocuments(manifest([{...docs[0], source_path:'private/secret.md'}]), root), /outside-approved-scope/);
    assert.throws(() => admittedDocuments(manifest([{...docs[0], source_path:'.claude/skills/copy.md'}]), root), /outside-approved-scope/);
  });
  record('canonical duplicate path or identity rejected', () => {
    assert.throws(() => admittedDocuments(manifest([docs[0], {...docs[0], document_id:'duplicate'}]), root), /duplicate-canonical-document/);
  });
  record('active build owner prevents overlap without changing its lock',()=>{
    const release=acquireBuildLock(base), path=join(base,'.admitted-reindex.lock'), before=readFileSync(path);
    assert.throws(()=>acquireBuildLock(base),/admitted-reindex-already-running/);
    assert.deepEqual(readFileSync(path),before); release();
  });
  record('dead build owner is archived before one recovery acquires the lock',()=>{
    const dead=spawnSync(process.execPath,['-e',''],{timeout:5000,windowsHide:true}); assert.equal(dead.status,0);
    writeFileSync(join(base,'.admitted-reindex.lock'),JSON.stringify({pid:dead.pid,owner_id:'run-synthetic-dead',started_at:'2026-09-13T00:00:00Z'}));
    const release=acquireBuildLock(base);
    assert(existsSync(join(base,'index/lock-history'))); release();
  });
  record('complete lexical passage retains late financial limitation', () => {
    const chunks = chunkDocument(docs[0], fixtures.lateTerm);
    assert(lexicalRanks(chunks, 'UNIQUE_COST_FOOTNOTE').length > 0);
    assert(chunks.some(c => c.text.includes('turnover and market impact')));
  });
  record('headings and adjoining financial limitations do not consume separate votes',()=>{
    const raw='# Synthetic margin\n\nRevenue less costs gives operating income.\n\nMargin alone does not establish a return on capital.\n';
    const doc={...docs[0],chunks:[{chunk_id:'cohesive',locator:{start_line:1,end_line:countLines(raw)},approved_use:['research']}]};
    const chunks=chunkDocument(doc,raw);
    assert.equal(chunks.length,1);assert.equal(chunks[0].text,raw);
    assert(chunks[0].text.includes('does not establish'));
  });
  record('token windows preserve every character and respect the model limit',()=>{
    const text=fixtures.longTable+' Unicode \u03b1 \ud83d\ude00.';
    const windows=tokenWindows(text,s=>Array.from(s).length+2,128);
    assert(windows.length>1); assert.equal(windows.map(x=>x.text).join(''),text);
    assert(windows.every(x=>x.tokens<=128 && !/[\ud800-\udbff]$/.test(x.text)));
  });
  record('table continuation preserves header units footnote and distinct offsets', () => {
    const chunks = chunkDocument(docs[1], fixtures.longTable, 1200);
    const last = chunks.find(c => c.text.includes('| 1989 |'));
    assert(last); assert(last.source_span.start_line > 6);
    assert(last.context_spans.some(s => s.text.includes('| Year | Revenue | Operating income |')));
    assert(last.context_spans.some(s => s.text.includes('USD millions')));
    assert(last.context_spans.some(s => s.text.includes('negative operating income is a loss')));
  });
  record('exact offsets round trip across blank lines CRLF and Unicode', () => {
    for (const raw of [fixtures.exactLines, fixtures.exactLines.replaceAll('\n','\r\n'), '\ufeff# Unicode\n\nAmount \u03b1 \ud83d\ude00 is synthetic.\n']) {
      const doc = {...docs[2], chunks:[{...docs[2].chunks[0], locator:{start_line:1,end_line:countLines(raw)}}]};
      for (const c of chunkDocument(doc, raw)) for (const s of [c.source_span, ...c.context_spans]) {
        assert.equal(raw.slice(s.start,s.end), s.text);
        assert.equal(Buffer.from(raw).subarray(s.start_byte,s.end_byte).toString('utf8'),s.text);
        assert.equal(raw.slice(0,s.start).split('\n').length,s.start_line);
      }
    }
  });
  record('approved locator prevents adjacent non-approved context disclosure', () => {
    const raw = 'SYNTHETIC_UNAPPROVED_CONTEXT\n\n# Allowed\n\nOnly approved method text.\n';
    const doc = {...docs[0],chunks:[{chunk_id:'limited',locator:{start_line:3,end_line:5},approved_use:['research']}]};
    assert(!canonical(chunkDocument(doc,raw)).includes('SYNTHETIC_UNAPPROVED_CONTEXT'));
  });
  record('legacy contaminated index is never read as an admitted generation', () => {
    mkdirSync(join(base,'index'),{recursive:true});
    writeFileSync(join(base,'index/vault-meta.json'),fixtures.secret);
    const health=inspectRuntime({...args(),providerIdentity:provider.identity});
    assert.equal(health.state,'unavailable'); assert.equal(health.reason,'no-admitted-generation');
    assert(!canonical(health).includes(fixtures.secret));
  });
  const first=await buildGeneration(args());
  record('candidate build remains unpublished',()=>assert(!existsSync(join(base,'index/current.json'))));
  publishGeneration({...args(),candidate:first,providerIdentity:provider.identity});
  record('published generation validates metadata and every artifact',()=>{
    const health=inspectRuntime({...args(),providerIdentity:provider.identity});
    assert.equal(health.state,'passed'); assert.equal(health.generation_id,first.generation_id);
  });
  await control('late term returns full inspected passage and source version',async()=>{
    const result=await queryGeneration({...args(),query:'UNIQUE_COST_FOOTNOTE',mode:'lexical'});
    assert.equal(result.state,'passed'); assert(result.hits[0].text.includes('turnover and market impact'));
    assert.equal(result.hits[0].source_sha256,docs[0].sha256);
  });
  await control('empty and scope-bound query states are genuine no_matches',async()=>{
    assert.equal((await queryGeneration({...args(),query:'NO_SUCH_SYNTHETIC_TERM',mode:'lexical'})).state,'no_matches');
    assert.equal((await queryGeneration({...args(),query:'income',scope:'not-approved',mode:'lexical'})).state,'no_matches');
  });
  await control('lexical retrieval needs no embedding provider methods',async()=>{
    const r=await queryGeneration({...args(),provider:{identity:provider.identity},query:'UNIQUE_COST_FOOTNOTE',mode:'lexical'});
    assert.equal(r.state,'passed'); assert.equal(r.embedding_use,'not-used-generation-identity-only');
    assert.equal(r.evidence_coverage,'retrieved-subset-not-complete-answer-evidence');
    assert.equal(r.source_text_truncated,false);
  });
  await control('insufficient complete-passage output budget is not no_matches',async()=>{
    const r=await queryGeneration({...args(),query:'UNIQUE_COST_FOOTNOTE',mode:'lexical',maximumChars:100});
    assert.equal(r.state,'unavailable'); assert.equal(r.reason,'output-budget-insufficient'); assert.deepEqual(r.hits,[]);
  });
  const second=await buildGeneration(args());
  await control('vector mutation during query invalidates before returning evidence',async()=>{
    const pinned=pinGeneration(base), path=join(pinned.directory,'vault.hnsw'), before=readFileSync(path);
    await assert.rejects(queryGeneration({...args(),query:'UNIQUE_COST_FOOTNOTE',mode:'lexical',beforeReturn:()=>
      writeFileSync(path,'tampered synthetic vectors')}),/generation-artifact-tampered/);
    writeFileSync(path,before);
  });
  await control('in-flight query pins old generation across atomic replacement',async()=>{
    const pinned=pinGeneration(base);
    const r=await queryGeneration({...args(),pin:pinned,query:'1989',mode:'lexical',beforeReturn:()=>
      publishGeneration({...args(),candidate:second,providerIdentity:provider.identity})});
    assert.equal(r.generation_id,first.generation_id); assert.equal(pinGeneration(base).pointer.generation_id,second.generation_id);
    assert(r.hits.every(h=>h.generation_id===first.generation_id));
  });
  record('complete history permits compatible rollback without rewriting generations',()=>{
    publishGeneration({...args(),candidate:first,providerIdentity:provider.identity});
    assert(existsSync(join(base,'index/generations',second.generation_id,'manifest.json')));
  });
  record('crash leaves pending generation unservable and prior pointer intact',()=>{
    mkdirSync(join(base,'index/generations/.g-interrupted.pending'));
    writeFileSync(join(base,'index/generations/.g-interrupted.pending/vault.hnsw'),'incomplete');
    assert.equal(pinGeneration(base).pointer.generation_id,first.generation_id);
  });
  record('changed provider model or runtime expires readiness',()=>{
    assert.equal(inspectRuntime({...args(),providerIdentity:{...provider.identity,name:'different'}}).reason,'embedding-model-version-changed');
    assert.equal(inspectRuntime({...args(),providerIdentity:provider.identity,runtimeIdentity:{sha256:sha('changed')}}).reason,'retrieval-runtime-version-changed');
  });
  record('registry mutation invalidates without a Claude write marker',()=>{
    const changed=manifest(docs,'2');
    assert.equal(inspectRuntime({...args(),admission:changed,providerIdentity:provider.identity}).reason,'admission-version-changed');
    assert.throws(()=>publishGeneration({...args(),admission:changed,candidate:second,providerIdentity:provider.identity}),/admission-version-changed/);
  });
  await control('source change during query returns no content',async()=>{
    await assert.rejects(queryGeneration({...args(),query:'UNIQUE_COST_FOOTNOTE',mode:'lexical',beforeReturn:()=>
      writeFileSync(join(root,docs[0].source_path),fixtures.lateTerm+'Changed source.\n')}),/source-version-changed/);
    assert.equal(inspectRuntime({...args(),providerIdentity:provider.identity}).state,'stale');
    writeFileSync(join(root,docs[0].source_path),fixtures.lateTerm);
  });
  await control('source change while embedding cannot publish a candidate',async()=>{
    const changedProvider={...provider,embed:async texts=>{
      writeFileSync(join(root,docs[0].source_path),fixtures.lateTerm+'Changed while embedding.\n'); return vectors(texts);}};
    await assert.rejects(buildGeneration({...args(),provider:changedProvider}),/source-version-changed/);
    assert.equal(pinGeneration(base).pointer.generation_id,first.generation_id);
    writeFileSync(join(root,docs[0].source_path),fixtures.lateTerm);
  });
  record('deleted source and link replacement expire current eligibility',()=>{
    const path=join(root,docs[0].source_path); unlinkSync(path);
    assert.equal(inspectRuntime({...args(),providerIdentity:provider.identity}).reason,'admitted-source-unavailable');
    const target=join(root,'wiki/linked.md'); writeFileSync(target,fixtures.lateTerm);
    symlinkSync(target,path); assert.equal(inspectRuntime({...args(),providerIdentity:provider.identity}).state,'stale');
    unlinkSync(path); writeFileSync(path,fixtures.lateTerm);
  });
  record('tampered generation content is refused without content-bearing errors',()=>{
    const path=join(base,'index/generations',first.generation_id,'passages.json');
    writeFileSync(path,fixtures.secret);
    const health=inspectRuntime({...args(),providerIdentity:provider.identity});
    assert.equal(health.state,'unavailable'); assert.equal(health.reason,'generation-artifact-tampered');
    assert(!canonical(health).includes(fixtures.secret));
  });
  record('failure adapter exposes only bounded reason codes',()=>{
    assert(!canonical(failureResult(new Error(fixtures.secret))).includes(fixtures.secret));
    assert.deepEqual(failureResult(new RetrievalError('stale','source-version-changed')).hits,[]);
  });
  console.log(JSON.stringify({schema:'osanwe.retrieval-controls/1',state:'passed',cases:outcomes.length,
    classification:'SYNTHETIC',fixture_sha256:sha(readFileSync(new URL('./retrieval-fixtures.mjs',import.meta.url))),
    outcomes,scope:'isolated admitted generations and synthetic vector provider; no live corpus, native embedding quality or financial advantage claim'}));
} finally {
  assert.equal(resolve(dirname(root)),resolve(tmpdir()));
  assert(basename(root).startsWith('osanwe-retrieval-control-'));
  rmSync(root,{recursive:true,force:true});
}
