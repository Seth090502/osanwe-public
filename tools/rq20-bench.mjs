// rq20-bench.mjs -- TENFOLD-T5 frozen RQ20 retrieval benchmark runner. Read-only; out-of-vault tooling.
// Scores Engine A (dense bge-base HNSW) and Engine B (hybrid: dense25 + BM25-25 over previews + RRF K=60
// + dense-cosine rerank top-12) against any INDEX_DIR. Engine B replicates /path/to/local/vault-search/server.py.
// Spec (durable, vault-tracked): /path/to/vault/tools/rq20-benchmark.json.
// Usage: node rq20-bench.mjs --index <dir> --engine A|B|both [--spec <json>]
import { pipeline, env } from '@xenova/transformers';
import hnswlib from 'hnswlib-node';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const { HierarchicalNSW } = hnswlib;
const MODEL = 'Xenova/bge-base-en-v1.5';
const DIM = 768;
const QP = 'Represent this sentence for searching relevant passages: ';
const TOPK = 5, RRF_K = 60, DENSE_CAND = 25, BM25_CAND = 25, RERANK_N = 12;
env.cacheDir = '/path/to/home/.vault-substrate/.models';

const AV = process.argv.slice(2);
const arg = (k, d) => { const i = AV.indexOf(k); return i >= 0 && AV[i + 1] ? AV[i + 1] : d; };
const INDEX_DIR = arg('--index', '/path/to/home/.vault-substrate/index');
const ENGINE = arg('--engine', 'both');
const SPEC = arg('--spec', '/path/to/vault/tools/rq20-benchmark.json');

const spec = JSON.parse(readFileSync(SPEC, 'utf8'));
const meta = JSON.parse(readFileSync(join(INDEX_DIR, 'vault-meta.json'), 'utf8'));
const CH = meta.chunks; const N = CH.length;
const index = new HierarchicalNSW('cosine', DIM);
index.readIndexSync(join(INDEX_DIR, 'vault.hnsw'));
index.setEf(128);

// --- BM25 tables over previews (mirrors server.py exactly) ---
const TOKRE = /[a-z0-9]+/g;
const toks = (s) => (String(s).toLowerCase().match(TOKRE) || []);
const DOC = CH.map((c) => toks(c.preview || ''));
const DLEN = DOC.map((t) => t.length);
const AVGDL = N ? DLEN.reduce((a, b) => a + b, 0) / N : 0;
const DF = new Map();
for (const dt of DOC) for (const w of new Set(dt)) DF.set(w, (DF.get(w) || 0) + 1);
const IDF = new Map();
for (const [w, df] of DF) IDF.set(w, Math.log(1 + (N - df + 0.5) / (df + 0.5)));
const TF = DOC.map((dt) => { const m = new Map(); for (const w of dt) m.set(w, (m.get(w) || 0) + 1); return m; });
function bm25(query, cand = BM25_CAND, k1 = 1.5, b = 0.75) {
  const q = [...new Set(toks(query))].filter((w) => IDF.has(w));
  if (!q.length) return [];
  const sc = [];
  for (let i = 0; i < N; i++) {
    const tf = TF[i], dl = DLEN[i]; let s = 0;
    for (const w of q) { const f = tf.get(w) || 0; if (f) s += IDF.get(w) * (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / (AVGDL || 1))); }
    if (s > 0) sc.push([i, s]);
  }
  sc.sort((a, b) => b[1] - a[1]);
  return sc.slice(0, cand).map((x) => x[0]);
}

const denseTop = (v, k) => { const { distances, neighbors } = index.searchKnn(v, k); return neighbors.map((lab, i) => [lab, 1 - distances[i]]); };

function hybrid(qstr, qvec) {
  const dlist = denseTop(qvec, DENSE_CAND);   // [[lab,score]]
  const blist = bm25(qstr, BM25_CAND);        // [lab]
  const rrf = new Map();
  dlist.forEach(([lab], r) => rrf.set(lab, (rrf.get(lab) || 0) + 1 / (RRF_K + r + 1)));
  blist.forEach((lab, r) => rrf.set(lab, (rrf.get(lab) || 0) + 1 / (RRF_K + r + 1)));
  const fused = [...rrf.entries()].sort((a, b) => b[1] - a[1]).slice(0, RERANK_N);
  const reranked = fused.map(([lab]) => {
    let dot = -1; try { const v = index.getPoint(lab); dot = 0; for (let i = 0; i < DIM; i++) dot += qvec[i] * v[i]; } catch { dot = -1; }
    return [lab, dot];
  }).sort((a, b) => b[1] - a[1]);
  return reranked.slice(0, TOPK).map(([lab]) => lab);
}

const pathsOf = (labs) => labs.map((l) => (CH[l] ? CH[l].path : '?'));
const isHit = (paths, canon) => canon.length > 0 && paths.some((p) => canon.some((c) => p.toLowerCase().includes(String(c).toLowerCase())));

async function main() {
  const extractor = await pipeline('feature-extraction', MODEL);
  const rows = [];
  let aPass = 0, bPass = 0;
  for (const q of spec.questions) {
    const o = await extractor(QP + q.query, { pooling: 'mean', normalize: true });
    const qvec = Array.from(o.data);
    const row = { id: q.id, topic: q.topic };
    if (ENGINE === 'A' || ENGINE === 'both') {
      const ap = pathsOf(denseTop(qvec, TOPK).map(([l]) => l));
      const ah = isHit(ap, q.canonical); if (ah) aPass++;
      row.A = { hit: ah, top5: ap };
    }
    if (ENGINE === 'B' || ENGINE === 'both') {
      const bp = pathsOf(hybrid(q.query, qvec));
      const bh = isHit(bp, q.canonical); if (bh) bPass++;
      row.B = { hit: bh, top5: bp };
    }
    rows.push(row);
    const af = row.A ? (row.A.hit ? 'A:HIT ' : 'A:miss') : '';
    const bf = row.B ? (row.B.hit ? 'B:HIT ' : 'B:miss') : '';
    process.stderr.write(`${q.id} ${af} ${bf}  ${q.topic}\n`);
  }
  const total = spec.questions.length;
  const summary = { index: INDEX_DIR, chunks: N, builtAt: meta.builtAt, engine: ENGINE, total,
    A_pass: (ENGINE === 'B' ? null : aPass), B_pass: (ENGINE === 'A' ? null : bPass) };
  process.stderr.write(`\nINDEX=${INDEX_DIR} chunks=${N} builtAt=${meta.builtAt}\n`);
  if (ENGINE !== 'B') process.stderr.write(`Engine A (dense)  : ${aPass}/${total}\n`);
  if (ENGINE !== 'A') process.stderr.write(`Engine B (hybrid) : ${bPass}/${total}\n`);
  process.stdout.write(JSON.stringify({ summary, rows }, null, 2));
}
main().catch((e) => { process.stderr.write('BENCH ERROR: ' + (e && e.stack || e) + '\n'); process.exit(1); });
