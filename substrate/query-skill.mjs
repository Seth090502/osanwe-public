// Phase 3.6 skill-level semantic retrieval: multi-query, configurable depth + path-prefix filter.
// Input  (stdin JSON, primary): {"queries":[...], "top_k":N, "threshold":F, "filter_path_prefix":"wiki/..."}
//        (argv fallback)       : node query-skill.mjs "query one" "query two"   (defaults top_k=5 threshold=0.5)
// Output (stdout)              : JSON array [{path,line,score,text}] sorted by score desc, deduped by chunk.
// Self-contained: reuses the Phase 3 index + bge-base model (read-only; concurrent-safe during reindex
// atomic-swap). Always emits valid JSON; emits [] and exits 0 on any error (never crashes the caller).
import { pipeline, env } from '@xenova/transformers';
import hnswlib from 'hnswlib-node';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const { HierarchicalNSW } = hnswlib;
const INDEX_DIR = process.env.SUBSTRATE_ROOT ? require('node:path').join(process.env.SUBSTRATE_ROOT, 'index') : require('node:path').join(require('node:os').homedir(), '.vault-substrate', 'index');
const MODEL = 'Xenova/bge-base-en-v1.5';
const DIM = 768;
const QUERY_PREFIX = 'Represent this sentence for searching relevant passages: ';
env.cacheDir = (process.env.SUBSTRATE_ROOT || require('node:os').homedir() + '/.vault-substrate') + '/.models';

function readStdin() {
  try { return readFileSync(0, 'utf8'); } catch { return ''; }
}

async function main() {
  // Input: stdin JSON primary; argv queries fallback.
  let input = {};
  const raw = readStdin();
  if (raw && raw.trim()) { try { input = JSON.parse(raw); } catch { input = {}; } }
  if (!Array.isArray(input.queries)) input = { ...input, queries: process.argv.slice(2) };
  const queries = Array.isArray(input.queries) ? input.queries.filter(q => q && q.trim()) : [];
  const top_k = Number.isFinite(input.top_k) ? input.top_k : 5;
  const threshold = Number.isFinite(input.threshold) ? input.threshold : 0.5;
  const filter = typeof input.filter_path_prefix === 'string' && input.filter_path_prefix ? input.filter_path_prefix : null;
  if (!queries.length) { process.stdout.write('[]'); return; }

  const meta = JSON.parse(readFileSync(join(INDEX_DIR, 'vault-meta.json'), 'utf8'));
  const index = new HierarchicalNSW('cosine', DIM);
  index.readIndexSync(join(INDEX_DIR, 'vault.hnsw'));
  index.setEf(64);
  const total = meta.chunks.length;

  // hnswlib has no native pre-filter: over-fetch then post-filter. Larger K when a restrictive
  // path-prefix filter is set (tickers subtree is ~2% of the index).
  const K = Math.min(total, filter ? Math.max(top_k * 20, 500) : Math.max(top_k * 8, 200));

  const extractor = await pipeline('feature-extraction', MODEL);
  const best = new Map(); // label -> {path,line,score,text}; keep highest score across queries
  for (const q of queries) {
    const o = await extractor(QUERY_PREFIX + q, { pooling: 'mean', normalize: true });
    const v = Array.from(o.data);
    const { distances, neighbors } = index.searchKnn(v, K);
    for (let i = 0; i < neighbors.length; i++) {
      const label = neighbors[i];
      const score = 1 - distances[i];
      if (score < threshold) continue;
      const m = meta.chunks[label];
      if (!m) continue;
      if (filter && !m.path.startsWith(filter)) continue;
      const prev = best.get(label);
      if (!prev || score > prev.score) {
        best.set(label, { path: m.path, line: m.line, score: Number(score.toFixed(4)), text: m.preview });
      }
    }
  }

  const results = [...best.values()].sort((a, b) => b.score - a.score).slice(0, top_k);
  process.stdout.write(JSON.stringify(results));
}

main().catch(() => { process.stdout.write('[]'); process.exit(0); });
