// Shared integrity layer for the existing vault-search runtime. No new service.
// Inputs are admitted PUBLIC/SYNTHETIC documents, never a whole-vault crawl.
import {createHash, randomUUID} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {existsSync, lstatSync, mkdirSync, readFileSync, readdirSync, realpathSync,
  renameSync, statSync, writeFileSync, openSync, fsyncSync, closeSync, unlinkSync} from 'node:fs';
import {join, relative, resolve, isAbsolute, sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {allowedRelativePath, readApprovedMarkdownBytes} from './index-scope.mjs';

export const SCHEMA = 'osanwe.retrieval-generation/1';
export const RESULT_SCHEMA = 'osanwe.retrieval-result/1';
export const HEALTH_SCHEMA = 'osanwe.retrieval-health/1';
export const CHUNKER = 'exact-lines-table-context/2';
export const CODE_ROOT = fileURLToPath(new URL('../', import.meta.url));
const ID = /^[a-zA-Z0-9][a-zA-Z0-9_-]{0,100}$/;
const HASH = /^[a-f0-9]{64}$/;
export const sha = (x) => createHash('sha256').update(x).digest('hex');
export function canonical(value) {
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  return '{' + Object.keys(value).filter(k => value[k] !== undefined).sort().map(k => JSON.stringify(k) + ':' + canonical(value[k])).join(',') + '}';
}
export class RetrievalError extends Error {
  constructor(state, reason) { super(reason); this.state = state; this.reason = reason; }
}
const fail = (state, reason) => { throw new RetrievalError(state, reason); };
const requireValue = (yes, reason) => { if (!yes) fail('unavailable', reason); };
const same = (left, right) => canonical(left) === canonical(right);
const string = (x) => typeof x === 'string' && x.length > 0;

function regular(path, maximum = 128 * 1024 * 1024) {
  const st = lstatSync(path);
  requireValue(st.isFile() && !st.isSymbolicLink() && st.nlink === 1 && st.size <= maximum,
    'unsafe-runtime-artifact');
  return st;
}
export function readJSON(path, maximum) {
  regular(path, maximum);
  return JSON.parse(readFileSync(path, 'utf8'));
}
function writeNew(path, bytes) {
  const fd = openSync(path, 'wx');
  try { writeFileSync(fd, bytes); fsyncSync(fd); } finally { closeSync(fd); }
}
export function atomicJSON(path, value) {
  const temporary = path + '.pending-' + randomUUID();
  writeNew(temporary, canonical(value) + '\n');
  // Never unlink the old pointer to make a failed replacement look successful.
  renameSync(temporary, path);
}

export function acquireBuildLock(base) {
  const lock = join(base, '.admitted-reindex.lock'), recovery = join(base, '.admitted-reindex.recovery.lock');
  const owner = canonical({pid:process.pid, owner_id:'run-' + randomUUID(), started_at:new Date().toISOString()});
  let descriptor;
  try { descriptor = openSync(lock, 'wx'); }
  catch (error) {
    if (error.code !== 'EEXIST') fail('unavailable', 'reindex-lock-unavailable');
    let guard;
    try { guard = openSync(recovery, 'wx'); }
    catch { fail('unavailable', 'reindex-recovery-already-running'); }
    try {
      const prior = readJSON(lock, 4096);
      requireValue(Number.isInteger(prior.pid) && prior.pid > 0 && ID.test(prior.owner_id) &&
        string(prior.started_at) && Number.isFinite(Date.parse(prior.started_at)), 'invalid-reindex-owner');
      let alive = true;
      try { process.kill(prior.pid, 0); }
      catch (probe) { if (probe.code === 'ESRCH') alive = false; }
      if (alive) fail('unavailable', 'admitted-reindex-already-running');
      const history = join(base, 'index/lock-history'); mkdirSync(history, {recursive:true});
      // Preserve the abandoned owner record; recovery never rewrites a spent
      // scheduler opportunity or treats an elapsed TTL as proof of a dead owner.
      renameSync(lock, join(history, 'abandoned-' + randomUUID() + '.json'));
      descriptor = openSync(lock, 'wx');
    } finally { closeSync(guard); unlinkSync(recovery); }
  }
  writeFileSync(descriptor, owner); fsyncSync(descriptor);
  return () => {
    closeSync(descriptor);
    requireValue(readFileSync(lock, 'utf8') === owner, 'reindex-owner-changed');
    unlinkSync(lock);
  };
}

export function loadAdmission({root, registry, python = '/path/to/python/python.exe'}) {
  requireValue(string(root) && string(registry), 'admission-location-required');
  try { regular(registry, 32 * 1024 * 1024); }
  catch { fail('unavailable', 'document-registry-unavailable'); }
  const registryHash = sha(readFileSync(registry));
  let value;
  try {
    const output = execFileSync(python, [join(CODE_ROOT, 'tools/pit/dataset_registry.py'),
      '--documents-manifest', '--documents-registry', registry, '--root', root],
    {cwd: root, timeout: 30000, maxBuffer: 32 * 1024 * 1024, windowsHide: true, encoding: 'utf8'});
    value = JSON.parse(output);
  } catch { fail('unavailable', 'document-admission-unavailable'); }
  requireValue(registryHash === sha(readFileSync(registry)), 'registry-changed-during-admission');
  requireValue(value?.schema === 'osanwe.financial-document-manifest/1' &&
    HASH.test(value.manifest_sha256) && Array.isArray(value.documents), 'invalid-admission-manifest');
  return {...value, registry_sha256: registryHash};
}

export function admittedDocuments(manifest, root) {
  requireValue(manifest?.schema === 'osanwe.financial-document-manifest/1' &&
    HASH.test(manifest.manifest_sha256) && Array.isArray(manifest.documents), 'invalid-admission-manifest');
  const paths = new Set(), ids = new Set();
  return manifest.documents.map(doc => {
    requireValue(doc?.eligible === true && ['PUBLIC', 'SYNTHETIC'].includes(doc.classification),
      'document-not-publicly-admitted');
    requireValue(string(doc.document_id) && string(doc.source_version) && string(doc.source_origin_id) &&
      Array.isArray(doc.approved_use) && doc.approved_use.length > 0 && HASH.test(doc.sha256), 'invalid-document-identity');
    requireValue(string(doc.source_path) && allowedRelativePath(doc.source_path) && !isAbsolute(doc.source_path),
      'document-outside-approved-scope');
    const normalized = doc.source_path.replace(/\\/g, '/').toLowerCase();
    requireValue(!paths.has(normalized) && !ids.has(doc.document_id), 'duplicate-canonical-document');
    paths.add(normalized); ids.add(doc.document_id);
    // Eligibility is checked before opening the source. Hashing never scans an
    // UNKNOWN/MIXED record or excluded path.
    let bytes;
    try { bytes = readApprovedMarkdownBytes(root, resolve(root, doc.source_path)); }
    catch { fail('stale', 'admitted-source-unavailable'); }
    if (sha(bytes) !== doc.sha256) fail('stale', 'admitted-source-version-changed');
    requireValue(bytes.length <= 8 * 1024 * 1024, 'admitted-document-too-large');
    const raw = new TextDecoder('utf-8', {fatal: true, ignoreBOM: true}).decode(bytes);
    requireValue(Array.isArray(doc.chunks) && doc.chunks.length > 0, 'approved-passages-required');
    return {doc, raw};
  });
}

function sourceLines(raw) {
  const lines = [];
  const regexp = /[^\n]*(?:\n|$)/g;
  let match;
  while ((match = regexp.exec(raw)) && match[0]) {
    lines.push({start: match.index, end: regexp.lastIndex, text: match[0]});
  }
  return lines;
}
function span(raw, lines, a, b, role) {
  const start = lines[a].start, end = lines[b].end;
  return {role, start, end, start_byte: Buffer.byteLength(raw.slice(0, start)),
    end_byte: Buffer.byteLength(raw.slice(0, end)), start_line: a + 1, end_line: b + 1,
    text: raw.slice(start, end)};
}
function headingsBefore(raw, lines, until, allowedStart) {
  const stack = [];
  for (let i = allowedStart; i <= until; i++) {
    const m = lines[i].text.match(/^(#{1,6})\s+(.+?)\s*\r?\n?$/);
    if (!m) continue;
    stack.length = m[1].length - 1;
    stack[m[1].length - 1] = span(raw, lines, i, i, 'heading');
  }
  return stack.filter(Boolean);
}
const isTable = (s) => /^\s*\|.*\|\s*$/.test(s.trim());
const isSeparator = (s) => /^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*$/.test(s.trim());

export function chunkDocument(doc, raw, maximum = 2400) {
  const lines = sourceLines(raw), result = [], seen = new Set();
  for (const approved of doc.chunks) {
    const loc = approved.locator;
    requireValue(loc && Number.isInteger(loc.start_line) && Number.isInteger(loc.end_line) &&
      loc.start_line > 0 && loc.end_line >= loc.start_line && loc.end_line <= lines.length &&
      string(approved.chunk_id), 'invalid-approved-locator');
    const a = loc.start_line - 1, b = loc.end_line - 1;
    const admittedSpan = span(raw, lines, a, b, 'admitted');
    for (const key of ['start_byte', 'end_byte']) if (approved[key] !== undefined)
      requireValue(approved[key] === admittedSpan[key], 'approved-locator-byte-offset-mismatch');
    const emit = (start, end, context = []) => {
      const exact = span(raw, lines, start, end, 'passage');
      if (!exact.text.trim() || seen.has(exact.start + ':' + exact.end)) return;
      seen.add(exact.start + ':' + exact.end);
      const surrounding = [...headingsBefore(raw, lines, start, a), ...context]
        .filter((s, i, all) => !(s.start >= exact.start && s.end <= exact.end) &&
          all.findIndex(x => x.start === s.start && x.end === s.end) === i);
      const chunkId = sha(canonical([doc.document_id, doc.source_version, doc.sha256,
        approved.chunk_id, exact.start, exact.end, CHUNKER]));
      result.push({chunk_id: chunkId, admission_chunk_id: approved.chunk_id, document_id: doc.document_id,
        source_version: doc.source_version, source_sha256: doc.sha256, source_origin_id: doc.source_origin_id,
        supporting_origin_ids: doc.supporting_origin_ids ?? [], supporting_sources: doc.supporting_sources ?? [],
        source_uri: doc.source_uri, source_path: doc.source_path, classification: doc.classification,
        kind: doc.kind, source_kind: doc.source_kind, status: doc.status, approved_use: approved.approved_use ?? doc.approved_use,
        applicability: doc.applicability, available_at: doc.available_at, published_at: doc.published_at,
        reviewed_at: doc.reviewed_at, supersedes: doc.supersedes ?? [], claim_ids: approved.claim_ids ?? [],
        heading: loc.heading ?? '', source_span: exact, context_spans: surrounding,
        text: exact.text, lexical_text: surrounding.map(x => x.text).join('\n') + '\n' + exact.text});
    };
    let start = a;
    while (start <= b) {
      if (!lines[start].text.trim()) { start++; continue; }
      if (isTable(lines[start].text) && start + 1 <= b && isSeparator(lines[start + 1].text)) {
        let tableEnd = start + 1;
        while (tableEnd + 1 <= b && isTable(lines[tableEnd + 1].text)) tableEnd++;
        const context = [span(raw, lines, start, start + 1, 'table_header')];
        // Keep complete adjacent unit notes and footnotes inside the approved interval.
        let before = start - 1;
        while (before >= a && !lines[before].text.trim()) before--;
        let beforeStart = before;
        while (beforeStart > a && lines[beforeStart - 1].text.trim() && !/^#/.test(lines[beforeStart - 1].text)) beforeStart--;
        if (before >= a) context.push(span(raw, lines, beforeStart, before, 'table_lead'));
        let after = tableEnd + 1;
        while (after <= b && !lines[after].text.trim()) after++;
        let afterEnd = after;
        while (afterEnd < b && lines[afterEnd + 1].text.trim() && !/^#/.test(lines[afterEnd + 1].text)) afterEnd++;
        if (after <= b && !/^#/.test(lines[after].text)) context.push(span(raw, lines, after, afterEnd, 'table_note'));
        for (let row = start; row <= tableEnd;) {
          let end = row;
          while (end < tableEnd && lines[end + 1].end - lines[row].start <= maximum) end++;
          emit(row, end, context); row = end + 1;
        }
        start = tableEnd + 1;
      } else {
        let end = start;
        // Keep the heading, adjacent paragraphs and caveats together when their
        // complete source interval fits. Blank lines are layout, not independent
        // evidence: indexing each heading as a separate vote displaced substance.
        while (end < b && !isTable(lines[end + 1].text) &&
          !/^#{1,6}\s/.test(lines[end + 1].text) && lines[end + 1].end - lines[start].start <= maximum) end++;
        emit(start, end); start = end + 1;
      }
    }
  }
  return result;
}

function checkVectors(vectors, count, dimension) {
  requireValue(Array.isArray(vectors) && vectors.length === count && vectors.every(v =>
    Array.isArray(v) && v.length === dimension && v.every(Number.isFinite)), 'invalid-provider-vectors');
}
export async function buildGeneration({root, base, admission, provider, runtimeIdentity, now = new Date().toISOString()}) {
  const admitted = admittedDocuments(admission, root);
  requireValue(admitted.length > 0, 'no-admitted-documents');
  const chunks = admitted.flatMap(({doc, raw}) => chunkDocument(doc, raw));
  requireValue(chunks.length > 0, 'no-admitted-passages');
  const generationId = 'g-' + randomUUID();
  const generations = join(base, 'index/generations');
  mkdirSync(generations, {recursive: true});
  const pending = join(generations, '.' + generationId + '.pending');
  mkdirSync(pending);
  const vectors = [];
  for (let i = 0; i < chunks.length; i += 32) {
    const batch = await provider.embed(chunks.slice(i, i + 32).map(c => c.lexical_text));
    checkVectors(batch, Math.min(32, chunks.length - i), provider.identity.dimension);
    vectors.push(...batch);
  }
  await provider.write(join(pending, 'vault.hnsw'), vectors);
  writeNew(join(pending, 'passages.json'), canonical({generation_id: generationId, chunks}) + '\n');
  writeNew(join(pending, 'admission.json'), canonical(admission) + '\n');
  // Recheck the admitted source bytes after embedding: changes during the build
  // invalidate the candidate; they never silently enter a completed generation.
  admittedDocuments(admission, root);
  const files = {};
  for (const name of ['vault.hnsw', 'passages.json', 'admission.json']) {
    const bytes = readFileSync(join(pending, name)); files[name] = {sha256: sha(bytes), bytes: bytes.length};
  }
  const manifest = {schema: SCHEMA, generation_id: generationId, built_at: now, chunker: CHUNKER,
    character_offsets: 'UTF-16 code units; UTF-8 byte offsets also provided',
    classification: 'PUBLIC_OR_SYNTHETIC_ONLY', provider: provider.identity, runtime_identity: runtimeIdentity,
    admission_sha256: admission.manifest_sha256, registry_sha256: admission.registry_sha256 ?? null,
    document_count: admitted.length, passage_count: chunks.length, files};
  writeNew(join(pending, 'manifest.json'), canonical(manifest) + '\n');
  const final = join(generations, generationId);
  renameSync(pending, final);
  return {generation_id: generationId, manifest_sha256: sha(readFileSync(join(final, 'manifest.json'))), manifest};
}

export function pinGeneration(base, pointerOverride) {
  let pointer;
  try { pointer = pointerOverride ?? readJSON(join(base, 'index/current.json'), 4096); }
  catch { fail('unavailable', 'no-admitted-generation'); }
  requireValue(pointer?.schema === 'osanwe.retrieval-pointer/1' && ID.test(pointer.generation_id) &&
    HASH.test(pointer.manifest_sha256), 'invalid-generation-pointer');
  const generations = realpathSync(join(base, 'index/generations'));
  const directory = join(generations, pointer.generation_id);
  requireValue(!lstatSync(directory).isSymbolicLink() && realpathSync(directory) === directory,
    'unsafe-generation-directory');
  const manifestPath = join(directory, 'manifest.json');
  regular(manifestPath, 32768);
  requireValue(sha(readFileSync(manifestPath)) === pointer.manifest_sha256, 'generation-manifest-tampered');
  const manifest = readJSON(manifestPath, 32768);
  requireValue(manifest.schema === SCHEMA && manifest.generation_id === pointer.generation_id &&
    manifest.chunker === CHUNKER && manifest.classification === 'PUBLIC_OR_SYNTHETIC_ONLY' &&
    same(Object.keys(manifest.files).sort(), ['admission.json', 'passages.json', 'vault.hnsw']), 'invalid-generation-manifest');
  for (const [name, expected] of Object.entries(manifest.files)) {
    regular(join(directory, name));
    const bytes = readFileSync(join(directory, name));
    requireValue(bytes.length === expected.bytes && sha(bytes) === expected.sha256, 'generation-artifact-tampered');
  }
  const passages = readJSON(join(directory, 'passages.json'));
  requireValue(passages.generation_id === pointer.generation_id && passages.chunks.length === manifest.passage_count,
    'generation-passages-mismatch');
  return {pointer, directory, manifest, chunks: passages.chunks};
}

export function validatePin(pin, {root, admission, providerIdentity, runtimeIdentity}) {
  if (pin.manifest.admission_sha256 !== admission.manifest_sha256 ||
    pin.manifest.registry_sha256 !== (admission.registry_sha256 ?? null)) fail('stale', 'admission-version-changed');
  if (!same(pin.manifest.provider, providerIdentity)) fail('stale', 'embedding-model-version-changed');
  if (!same(pin.manifest.runtime_identity, runtimeIdentity)) fail('stale', 'retrieval-runtime-version-changed');
  const documents = admittedDocuments(admission, root);
  const expected = documents.flatMap(({doc, raw}) => chunkDocument(doc, raw));
  if (!same(pin.chunks, expected)) fail('stale', 'approved-passages-no-longer-match');
  return pin;
}

export function publishGeneration({base, candidate, root, admission, providerIdentity, runtimeIdentity}) {
  const pointer = {schema: 'osanwe.retrieval-pointer/1', generation_id: candidate.generation_id,
    manifest_sha256: candidate.manifest_sha256};
  const pin = pinGeneration(base, pointer);
  validatePin(pin, {root, admission, providerIdentity, runtimeIdentity});
  // One pointer swap publishes all immutable artifacts. Old generations remain
  // available for already pinned requests and historical replay/rollback checks.
  atomicJSON(join(base, 'index/current.json'), pointer);
  return pointer;
}

const tokenize = (text) => String(text).toLowerCase().match(/[\p{L}\p{N}_]+/gu) ?? [];
export function lexicalRanks(chunks, query) {
  const terms = [...new Set(tokenize(query))];
  const docs = chunks.map(c => tokenize(c.lexical_text)), n = docs.length;
  const avg = docs.reduce((s, d) => s + d.length, 0) / (n || 1);
  const df = Object.fromEntries(terms.map(t => [t, docs.filter(d => d.includes(t)).length]));
  return docs.map((words, label) => {
    let score = 0;
    for (const term of terms) {
      const f = words.filter(x => x === term).length;
      if (f) score += Math.log(1 + (n - df[term] + .5) / (df[term] + .5)) * f * 2.5 /
        (f + 1.5 * (.25 + .75 * words.length / (avg || 1)));
    }
    return {label, score};
  }).filter(x => x.score > 0).sort((a, b) => b.score - a.score || a.label - b.label);
}

export async function queryGeneration({root, base, admission, provider, runtimeIdentity, query, topK = 8,
  scope = null, maximumChars = 24000, pin = null, beforeReturn = null, mode = 'lexical'}) {
  requireValue(string(query) && query.length <= 8000 && Number.isInteger(topK) && topK > 0 && topK <= 20 &&
    Number.isInteger(maximumChars) && maximumChars >= 100 && maximumChars <= 100000 &&
    (scope === null || string(scope)) &&
    ['hybrid', 'lexical', 'dense'].includes(mode), 'invalid-query-contract');
  pin = pin ?? pinGeneration(base);
  validatePin(pin, {root, admission, providerIdentity: provider.identity, runtimeIdentity});
  const eligible = new Set(pin.chunks.map((c, i) => !scope || c.approved_use.includes(scope) ? i : -1).filter(i => i >= 0));
  const lexical = lexicalRanks(pin.chunks, query).filter(x => eligible.has(x.label));
  let dense = [];
  if (mode !== 'lexical') {
    const [vector] = await provider.embedQuery(query);
    checkVectors([vector], 1, provider.identity.dimension);
    dense = await provider.search(join(pin.directory, 'vault.hnsw'), vector, Math.min(50, pin.chunks.length));
    requireValue(dense.every(x => Number.isInteger(x.label) && pin.chunks[x.label] && Number.isFinite(x.score)),
      'invalid-search-provider-output');
    dense = dense.filter(x => eligible.has(x.label));
  }
  const scores = new Map();
  if (mode !== 'dense') lexical.slice(0, 50).forEach((x, i) => scores.set(x.label, (scores.get(x.label) ?? 0) + 1 / (61 + i)));
  if (mode !== 'lexical') dense.forEach((x, i) => scores.set(x.label, (scores.get(x.label) ?? 0) + 1 / (61 + i)));
  const ordered = [...scores.entries()].sort((a, b) => b[1] - a[1] || a[0] - b[0]);
  const hits = [], seenPassages = new Set(); let used = 0, omitted = 0;
  for (const [label, score] of ordered) {
    const chunk = pin.chunks[label];
    const key = chunk.source_origin_id + ':' + sha(chunk.text);
    if (seenPassages.has(key)) continue;
    seenPassages.add(key);
    const cost = chunk.text.length + chunk.context_spans.reduce((s, x) => s + x.text.length, 0);
    if (used + cost > maximumChars) { omitted++; continue; }
    hits.push({...chunk, rank_score: score, generation_id: pin.pointer.generation_id});
    used += cost;
    if (hits.length === topK) break;
  }
  if (beforeReturn) await beforeReturn();
  // A replaced current pointer does not affect a pinned in-flight query. Source
  // mutation does: no text leaves the runtime after the source version changes.
  validatePin(pinGeneration(base, pin.pointer), {root, admission, providerIdentity: provider.identity, runtimeIdentity});
  return {schema: RESULT_SCHEMA, state: hits.length ? 'passed' : (omitted ? 'unavailable' : 'no_matches'),
    reason: hits.length ? 'admitted-passages' : (omitted ? 'output-budget-insufficient' : 'no-eligible-matches'),
    generation_id: pin.pointer.generation_id, admission_sha256: admission.manifest_sha256,
    classification: 'PUBLIC_OR_SYNTHETIC_ONLY', ranking: mode + '-rrf',
    embedding_use: mode === 'lexical' ? 'not-used-generation-identity-only' : 'native-provider',
    ranking_evidence: mode === 'lexical' ? 'lexical-baseline' : 'experimental-no-general-quality-benefit-established',
    verification_scope: 'source version and passage integrity; relevance is not financial truth',
    evidence_coverage: 'retrieved-subset-not-complete-answer-evidence', source_text_truncated:false,
    candidate_limit_reached: hits.length === topK && ordered.length > topK,
    omitted_for_budget: omitted, returned_characters: used, hits};
}

export function inspectRuntime({root, base, admission, providerIdentity, runtimeIdentity}) {
  const at = new Date().toISOString();
  const coverage = {admitted_document_count:admission.documents.length,
    excluded_document_count:admission.exclusions?.length ?? 0, corpus_coverage:'explicitly-admitted-subset-only'};
  if (!admission.documents.length) return {schema:HEALTH_SCHEMA, state:'unavailable', reason:'no-admitted-documents',
    needs_rebuild:false, generation_id:null, observed_at:at, receipt_path:null, ...coverage};
  try {
    const pin = pinGeneration(base);
    validatePin(pin, {root, admission, providerIdentity, runtimeIdentity});
    return {schema: HEALTH_SCHEMA, state: 'passed', reason: 'current-admitted-generation', needs_rebuild: false,
      generation_id: pin.pointer.generation_id, observed_at: at, document_count: pin.manifest.document_count,
      passage_count: pin.manifest.passage_count, receipt_path: join(pin.directory, 'manifest.json'), ...coverage};
  } catch (error) {
    return failureResult(error, HEALTH_SCHEMA, {observed_at: at, needs_rebuild: error.state === 'stale' ||
      error.reason === 'no-admitted-generation', generation_id: null, receipt_path: null, ...coverage});
  }
}
export function failureResult(error, schema = RESULT_SCHEMA, extra = {}) {
  return {schema, state: error instanceof RetrievalError ? error.state : 'unavailable',
    reason: error instanceof RetrievalError ? error.reason : 'retrieval-runtime-unavailable', ...extra, hits: []};
}

export function modelFileIdentity(base) {
  const modelRoot = join(base, '.models/Xenova/bge-base-en-v1.5');
  requireValue(existsSync(modelRoot), 'embedding-model-cache-unavailable');
  const files = {};
  function walk(dir) {
    requireValue(!lstatSync(dir).isSymbolicLink(), 'unsafe-model-cache');
    for (const e of readdirSync(dir, {withFileTypes: true}).sort((a, b) => a.name.localeCompare(b.name))) {
      const path = join(dir, e.name);
      if (e.isDirectory()) walk(path);
      else { regular(path, 1024 * 1024 * 1024); files[relative(modelRoot, path).replace(/\\/g, '/')] = sha(readFileSync(path)); }
    }
  }
  walk(modelRoot);
  requireValue(files['config.json'] && files['tokenizer.json'] && Object.keys(files).some(x => x.endsWith('.onnx')),
    'embedding-model-cache-incomplete');
  return {name: 'Xenova/bge-base-en-v1.5', dimension: 768, artifact_sha256: sha(canonical(files)),
    kind: 'native-local-embedding', pooling: 'mean', normalize: true,
    long_passage_policy:'exact-character-token-windows-weighted-mean/1', maximum_model_tokens:512,
    query_prefix: 'Represent this sentence for searching relevant passages: '};
}

export function tokenWindows(text, tokenCount, limit = 512) {
  requireValue(string(text) && text.length <= 100000 && Number.isInteger(limit) && limit >= 8,
    'embedding-passage-budget-exceeded');
  const chars = Array.from(text), windows = []; let start = 0;
  while (start < chars.length) {
    let lo = 1, hi = Math.min(chars.length - start, 4096), best = 0;
    while (lo <= hi) {
      const middle = Math.floor((lo + hi) / 2), value = chars.slice(start,start+middle).join('');
      if (tokenCount(value) <= limit) { best = middle; lo = middle + 1; } else hi = middle - 1;
    }
    requireValue(best > 0, 'single-character-token-budget-exceeded');
    const value = chars.slice(start,start+best).join(''), tokens = tokenCount(value);
    requireValue(Number.isInteger(tokens) && tokens > 0 && tokens <= limit, 'embedding-token-count-invalid');
    windows.push({text:value,tokens}); start += best;
  }
  requireValue(windows.map(x=>x.text).join('') === text, 'embedding-window-coverage-gap');
  return windows;
}
