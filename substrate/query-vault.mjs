// Phase 3 vault semantic query: load HNSW index + bge-base, return top-K hits.
// Usage: node query-vault.mjs ["query one" "query two" ...]   (defaults to 3 smoke queries)
import { pipeline, env } from '@xenova/transformers';
import hnswlib from 'hnswlib-node';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const { HierarchicalNSW } = hnswlib;
const OUT_DIR = process.env.SUBSTRATE_ROOT ? require('node:path').join(process.env.SUBSTRATE_ROOT, 'index') : require('node:path').join(require('node:os').homedir(), '.vault-substrate', 'index');
const MODEL = 'Xenova/bge-base-en-v1.5';
const DIM = 768;
const K = 3;
// bge s2p retrieval: prepend instruction to the QUERY only (not documents).
const QUERY_PREFIX = 'Represent this sentence for searching relevant passages: ';

env.cacheDir = (process.env.SUBSTRATE_ROOT || require('node:os').homedir() + '/.vault-substrate') + '/.models';

const queries = process.argv.slice(2);
const smoke = ['investment thesis', 'career decision', 'supplement protocol'];
const toRun = queries.length ? queries : smoke;

const meta = JSON.parse(readFileSync(join(OUT_DIR, 'vault-meta.json'), 'utf8'));
const index = new HierarchicalNSW('cosine', DIM);
index.readIndexSync(join(OUT_DIR, 'vault.hnsw'));
index.setEf(64);
console.log(`[query] index loaded: ${index.getCurrentCount()} vectors, dim ${index.getNumDimensions()}, model ${meta.model}`);

const extractor = await pipeline('feature-extraction', MODEL);
async function embed(text) { const o = await extractor(text, { pooling: 'mean', normalize: true }); return Array.from(o.data); }

for (const q of toRun) {
  const v = await embed(QUERY_PREFIX + q);
  const { distances, neighbors } = index.searchKnn(v, K);
  console.log(`\n=== "${q}" ===`);
  for (let i = 0; i < neighbors.length; i++) {
    const m = meta.chunks[neighbors[i]];
    const sim = (1 - distances[i]).toFixed(4);
    console.log(`  [${sim}] ${m.path}:${m.line}`);
    console.log(`         ${m.preview}`);
  }
}
