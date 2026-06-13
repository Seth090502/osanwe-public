// Phase 3.7 reindex runner -- Task-Scheduler-polled (every 2 min).
// Rebuilds the vault index into a temp dir, then atomic-swaps it over the live
// index ~5 min after writes settle (debounce). Lockfile prevents overlapping runs.
// Live index is untouched during the ~6.3 min build; only the two renames are the
// danger window (sub-ms), covered by the query side's graceful [] on read error.
// Out-of-vault; no commit. ASCII only.
import { existsSync, statSync, writeFileSync, readFileSync, unlinkSync, renameSync, mkdirSync, appendFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';

const BASE = process.env.SUBSTRATE_ROOT || require('node:path').join(require('node:os').homedir(), '.vault-substrate');
const MARKER = join(BASE, '.debounce-marker');
const LOCK = join(BASE, '.reindex.lock');
const LOG = join(BASE, '.reindex.log');
const LIVE = join(BASE, 'index');
const TMP = join(BASE, 'index.tmp');
const INDEXER = join(BASE, 'index-vault.mjs');
const DEBOUNCE_MS = 5 * 60 * 1000;
const STALE_LOCK_MS = 20 * 60 * 1000;
const RETRIES = 5, BACKOFF_MS = 200;

const now = Date.now();
const log = (m) => { try { appendFileSync(LOG, `${new Date().toISOString()} ${m}\n`); } catch {} };
const ageMs = (p) => now - statSync(p).mtimeMs;
const sleepSync = (ms) => { try { Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms); } catch {} };

function swap(src, dst) {
  for (let i = 0; i < RETRIES; i++) {
    try { renameSync(src, dst); return; }
    catch (e) {
      if (i === RETRIES - 1) {                 // last resort: remove target then rename
        try { if (existsSync(dst)) unlinkSync(dst); renameSync(src, dst); return; }
        catch (e2) { log(`SWAP FAILED ${dst}: ${e2.message}`); throw e2; }
      }
      sleepSync(BACKOFF_MS * (i + 1));          // brief backoff if target is read-locked by a query
    }
  }
}

// 1. lock check -- another reindex in progress (stale lock auto-ignored after 20 min)
if (existsSync(LOCK) && ageMs(LOCK) < STALE_LOCK_MS) process.exit(0);
// 2. debounce gate
if (!existsSync(MARKER)) process.exit(0);       // no pending writes
if (ageMs(MARKER) < DEBOUNCE_MS) process.exit(0); // writes still settling

// 3. acquire lock + snapshot marker (to detect writes DURING the build)
writeFileSync(LOCK, `${process.pid} ${new Date().toISOString()}`);
const markerAtStart = statSync(MARKER).mtimeMs;
const t0 = Date.now();
try {
  mkdirSync(TMP, { recursive: true });
  // 4. build to TMP (live index untouched)
  const r = spawnSync('node', [INDEXER], { env: { ...process.env, INDEX_OUT_DIR: TMP }, encoding: 'utf8' });
  if (r.status !== 0) { log(`BUILD FAILED status=${r.status} ${(r.stderr || '').slice(0, 300)}`); process.exit(0); }
  // 5. atomic swap (hnsw then meta)
  swap(join(TMP, 'vault.hnsw'), join(LIVE, 'vault.hnsw'));
  swap(join(TMP, 'vault-meta.json'), join(LIVE, 'vault-meta.json'));
  // 6. clear marker ONLY if no writes arrived during the build; else leave it for the next poll
  let cleared = false;
  if (existsSync(MARKER) && statSync(MARKER).mtimeMs <= markerAtStart) { try { unlinkSync(MARKER); cleared = true; } catch {} }
  let cnt = '?'; try { cnt = JSON.parse(readFileSync(join(LIVE, 'vault-meta.json'), 'utf8')).count; } catch {}
  log(`REINDEX OK dur=${((Date.now() - t0) / 1000).toFixed(1)}s chunks=${cnt} marker_cleared=${cleared}`);
} catch (e) {
  log(`REINDEX ERROR ${e.message}`);
} finally {
  try { unlinkSync(LOCK); } catch {}
}
