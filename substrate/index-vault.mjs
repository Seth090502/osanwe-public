// Phase 3 vault indexer: bge-base-en-v1.5 embeddings -> persistent HNSW index.
// Scope: VAULT_ROOT/{wiki,Calendar,private}. Out-of-vault output.
import { pipeline, env } from '@xenova/transformers';
import hnswlib from 'hnswlib-node';
import { readFileSync, writeFileSync, statSync, readdirSync, mkdirSync } from 'node:fs';
import { join, relative } from 'node:path';

const { HierarchicalNSW } = hnswlib;
const ROOT = process.env.VAULT_ROOT || process.cwd();
const SCAN = ['wiki', 'Calendar', 'private'].map(d => join(ROOT, d));
const OUT_DIR = process.env.INDEX_OUT_DIR || require('node:path').join(process.env.SUBSTRATE_ROOT || require('node:os').homedir() + '/.vault-substrate', 'index');
const MODEL = 'Xenova/bge-base-en-v1.5';
const DIM = 768;
const EXCLUDE_DIRS = new Set(['test-tmp', '.precheck', '_archive', '.obsidian', 'node_modules', '.git']);
const CHUNK_CHARS = 1200, MAX_CHARS = 1800;

env.cacheDir = (process.env.SUBSTRATE_ROOT || require('node:os').homedir() + '/.vault-substrate') + '/.models';
env.allowRemoteModels = true;
mkdirSync(OUT_DIR, { recursive: true });

function walk(dir, acc = []) {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    if (e.isDirectory()) { if (!EXCLUDE_DIRS.has(e.name)) walk(join(dir, e.name), acc); }
    else if (e.isFile() && e.name.toLowerCase().endsWith('.md')) acc.push(join(dir, e.name));
  }
  return acc;
}

function stripFrontmatter(text) {
  if (text.startsWith('---')) {
    const end = text.indexOf('\n---', 3);
    if (end !== -1) { const nl = text.indexOf('\n', end + 1); return { body: text.slice(nl + 1), offset: text.slice(0, nl + 1).split('\n').length - 1 }; }
  }
  return { body: text, offset: 0 };
}

// Greedy paragraph packing into ~CHUNK_CHARS chunks; track approx start line.
function chunkFile(path) {
  const raw = readFileSync(path, 'utf8');
  const { body, offset } = stripFrontmatter(raw);
  const paras = body.split(/\n\s*\n/);
  const chunks = [];
  let buf = '', bufStartLine = offset + 1, lineCursor = offset + 1;
  const flush = () => { const t = buf.trim(); if (t.length >= 20) chunks.push({ line: bufStartLine, text: t }); buf = ''; };
  for (const p of paras) {
    const pLines = p.split('\n').length;
    if (p.length > MAX_CHARS) {
      flush();
      for (let i = 0; i < p.length; i += MAX_CHARS) chunks.push({ line: lineCursor, text: p.slice(i, i + MAX_CHARS).trim() });
    } else if ((buf + '\n\n' + p).length > CHUNK_CHARS && buf) {
      flush(); buf = p; bufStartLine = lineCursor;
    } else { if (!buf) bufStartLine = lineCursor; buf += (buf ? '\n\n' : '') + p; }
    lineCursor += pLines + 1;
  }
  flush();
  return chunks;
}

const t0 = Date.now();
console.log('[index] scanning', SCAN.join(', '));
const files = SCAN.flatMap(d => walk(d));
console.log('[index] files found:', files.length);

const meta = [];
for (const f of files) {
  const rel = relative(ROOT, f).replace(/\\/g, '/');
  for (const c of chunkFile(f)) meta.push({ path: rel, line: c.line, text: c.text });
}
console.log('[index] chunks:', meta.length);

console.log('[index] loading model', MODEL);
const extractor = await pipeline('feature-extraction', MODEL);
const tModel = Date.now();

const index = new HierarchicalNSW('cosine', DIM);
index.initIndex(meta.length, 16, 200, 100);
const BATCH = 32;
let done = 0;
for (let i = 0; i < meta.length; i += BATCH) {
  const batch = meta.slice(i, i + BATCH).map(m => m.text);
  const out = await extractor(batch, { pooling: 'mean', normalize: true });
  const rows = out.data; // flat Float32Array, batch.length * DIM
  for (let r = 0; r < batch.length; r++) {
    const v = Array.from(rows.subarray(r * DIM, (r + 1) * DIM));
    index.addPoint(v, i + r);
  }
  done += batch.length;
  if (i % (BATCH * 20) === 0 || done === meta.length) console.log(`[index] embedded ${done}/${meta.length}`);
}
index.setEf(100);

const idxPath = join(OUT_DIR, 'vault.hnsw');
index.writeIndexSync(idxPath);
// store previews to keep meta.json modest
const metaOut = meta.map((m, i) => ({ label: i, path: m.path, line: m.line, preview: m.text.replace(/\s+/g, ' ').slice(0, 300) }));
const metaPath = join(OUT_DIR, 'vault-meta.json');
writeFileSync(metaPath, JSON.stringify({ model: MODEL, dim: DIM, builtAt: new Date().toISOString(), count: meta.length, files: files.length, chunks: metaOut }));

const idxBytes = statSync(idxPath).size, metaBytes = statSync(metaPath).size;
console.log('--- G7 REPORT ---');
console.log('files indexed   :', files.length);
console.log('chunks (vectors):', meta.length);
console.log('model           :', MODEL, '(quantized ONNX) dim', DIM);
console.log('index file      :', idxPath, (idxBytes / 1024 / 1024).toFixed(2), 'MB');
console.log('meta file       :', metaPath, (metaBytes / 1024 / 1024).toFixed(2), 'MB');
console.log('model load ms   :', tModel - t0 - 0, '(approx, incl scan+chunk)');
console.log('total build ms  :', Date.now() - t0);
console.log('excluded dirs   :', [...EXCLUDE_DIRS].join(', '));
