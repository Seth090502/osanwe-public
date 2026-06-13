// Phase 3.5 hook wrapper: read hook JSON from stdin, extract the prompt,
// semantic-search the Phase 3 vault index, emit JSON [{path,line,score,text}].
// Self-contained (reuses the Phase 3 index + bge-base model; does not touch query-vault.mjs).
// Always emits valid JSON; emits [] and exits 0 on any error (never breaks the hook chain).
import { pipeline, env } from '@xenova/transformers';
import hnswlib from 'hnswlib-node';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const { HierarchicalNSW } = hnswlib;
const INDEX_DIR = process.env.SUBSTRATE_ROOT ? require('node:path').join(process.env.SUBSTRATE_ROOT, 'index') : require('node:path').join(require('node:os').homedir(), '.vault-substrate', 'index');
const MODEL = 'Xenova/bge-base-en-v1.5';
const DIM = 768;
const K = 5;
const QUERY_PREFIX = 'Represent this sentence for searching relevant passages: ';
env.cacheDir = (process.env.SUBSTRATE_ROOT || require('node:os').homedir() + '/.vault-substrate') + '/.models';

function readStdin() {
  try { return readFileSync(0, 'utf8'); } catch { return ''; }
}

async function main() {
  const raw = readStdin();
  let prompt = '';
  try { const j = JSON.parse(raw); prompt = j.prompt || j.message || j.user_prompt || ''; } catch { prompt = ''; }
  if (!prompt || !prompt.trim()) { process.stdout.write('[]'); return; }

  const meta = JSON.parse(readFileSync(join(INDEX_DIR, 'vault-meta.json'), 'utf8'));
  const index = new HierarchicalNSW('cosine', DIM);
  index.readIndexSync(join(INDEX_DIR, 'vault.hnsw'));
  index.setEf(64);

  const extractor = await pipeline('feature-extraction', MODEL);
  const o = await extractor(QUERY_PREFIX + prompt, { pooling: 'mean', normalize: true });
  const v = Array.from(o.data);
  const { distances, neighbors } = index.searchKnn(v, K);
  const hits = neighbors.map((label, i) => {
    const m = meta.chunks[label];
    return { path: m.path, line: m.line, score: Number((1 - distances[i]).toFixed(4)), text: m.preview };
  });
  process.stdout.write(JSON.stringify(hits));
}

main().catch(() => { process.stdout.write('[]'); process.exit(0); });
