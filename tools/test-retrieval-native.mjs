// Native cached BGE/HNSW adapter check against frozen synthetic documents only.
import assert from 'node:assert/strict';
import {mkdtempSync, mkdirSync, writeFileSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join, resolve, dirname, basename} from 'node:path';
import {fixtures} from './retrieval-fixtures.mjs';
import {sha, canonical, buildGeneration, publishGeneration, queryGeneration} from './retrieval-core.mjs';
import {provider} from 'file:////path/to/home/.vault-substrate/retrieval-provider.mjs';
const root=mkdtempSync(join(tmpdir(),'osanwe-retrieval-native-')), base=join(root,'candidate');
mkdirSync(join(root,'wiki')); mkdirSync(base);
const started=Date.now();
// Any accidental HTTP fetch makes this isolated native control fail.
globalThis.fetch=()=>{throw new Error('network-disabled-in-native-fixture-control');};
try {
  const documents=Object.entries({late:fixtures.lateTerm,table:fixtures.longTable}).map(([id,raw])=>{
    const path='wiki/'+id+'.md'; writeFileSync(join(root,path),raw);
    return {document_id:id,source_version:'1',source_origin_id:'synthetic:'+id,source_path:path,
      sha256:sha(raw),classification:'SYNTHETIC',status:'admitted',eligible:true,kind:'method',
      source_uri:'synthetic://'+id,approved_use:['research'],applicability:'Synthetic adapter control',
      available_at:'2026-09-01T00:00:00Z',published_at:'2026-09-01T00:00:00Z',reviewed_at:'2026-09-13T00:00:00Z',
      supersedes:[],chunks:[{chunk_id:id,locator:{start_line:1,end_line:raw.split('\n').length-1,heading:'Synthetic'},
        approved_use:['research'],claim_ids:[id]}]};
  });
  const admission={schema:'osanwe.financial-document-manifest/1',documents,exclusions:[],
    manifest_sha256:sha(canonical(documents)),registry_sha256:sha('synthetic-native-fixture-registry')};
  const native=await provider('/path/to/home/.vault-substrate');
  const runtimeIdentity={sha256:sha('isolated-native-fixture-adapter')};
  const args={root,base,admission,provider:native,runtimeIdentity};
  const candidate=await buildGeneration(args);
  publishGeneration({...args,candidate,providerIdentity:native.identity});
  const result=await queryGeneration({...args,query:'UNIQUE_COST_FOOTNOTE',mode:'hybrid'});
  assert.equal(result.state,'passed');
  assert(result.hits.some(h=>h.text.includes('turnover and market impact')));
  assert(result.hits.every(h=>h.generation_id===candidate.generation_id));
  native.verify();
  const embedding=native.diagnostics();
  assert(embedding.windows>embedding.passages);
  assert(embedding.maximum_window_tokens<=512);
  console.log(JSON.stringify({schema:'osanwe.retrieval-native-control/1',state:'passed',
    classification:'SYNTHETIC',provider:native.identity,documents:2,passages:candidate.manifest.passage_count,
    embedding,network_access:false,live_index_modified:false,elapsed_ms:Date.now()-started,
    scope:'cached native model and HNSW round trip on isolated synthetic candidate; not financial retrieval-quality validation'}));
} finally {
  assert.equal(resolve(dirname(root)),resolve(tmpdir())); assert(basename(root).startsWith('osanwe-retrieval-native-'));
  rmSync(root,{recursive:true,force:true});
}
