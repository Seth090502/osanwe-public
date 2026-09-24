# Frontmatter Canonicalization — Migration Playbook

Preserved record of the Group 25 frontmatter migration. Primary purpose is the methodology-findings section below — applicable patterns for future mechanical operations on vault content. Script and rollback details secondary, documented here for rollback or similar-migration authoring.

## Purpose

`group-25-frontmatter-canonicalize.py` was the executing script for the canonical frontmatter migration across 204 vault files on 2026-04-19. It strips `domain:` fields, inserts `categories:` per a path-aware routing table, rewrites `type:` per canonical subtype mapping, strips forbidden tag prefixes, and refreshes the `updated:` field — while byte-preserving the body and conservatively leaving absent fields absent.

Canonical migration landed at commit **`5e45ff0`**. Trailing-newline preservation fix landed at **`e36d491`**. Rollback anchor: **`pre-group-25` tag at `a75b419`**.

## Prerequisites

- **Python 3.10+** (checked at runtime)
- **ruamel.yaml** (`pip install ruamel.yaml`) — checked at import with informative error
- **Run from vault root.** Paths resolve relative to `cwd` for routing-rule string comparisons. Running from elsewhere produces wrong routing via the fallback branch (stderr warning will fire).
- Filesystem layout: `Atlas/`, `Calendar/`, `Efforts/`, `wiki/`, `private/`, `_templates/`, `docs/` at vault root.

## Canonical form (emission reference)

| Element | Rule |
|---|---|
| Key order | Original preserved; `categories:` inserted immediately before `type:`, or at position 0 if `type:` absent |
| Lists | Plural keys; block style; 2-space indent for list markers; empty as flow `[]` |
| Dates | Bare ISO `YYYY-MM-DD` (unquoted); Templater placeholders (`<% ... %>`) preserved verbatim |
| Strings | Quote style from source preserved (`preserve_quotes=True`); wikilinks `"[[X]]"` retain quotes |
| Tags | `domain/*` and `type/*` prefixes stripped; remaining namespaces preserved in original order |
| Line endings | LF enforced (normalized from CRLF on input per `.gitattributes`) |
| BOM | Preserved if present at input; not introduced |
| Trailing newlines | Exact count preserved (1 if file ended in `\n`, 2 if `\n\n`, etc.) |
| Body | Byte-preserved verbatim; sha256 pre/post must match |

## Scope query

The 204 scope files were identified by: git-tracked `*.md` files where the frontmatter YAML-parses as a dict containing `type:` but not `categories:`.

```python
# Run from vault root
import subprocess, yaml
from pathlib import Path
tracked = subprocess.check_output(['git','ls-files','*.md']).decode().splitlines()
scope = []
for rel in tracked:
    text = Path(rel).read_text(encoding='utf-8', errors='replace')
    if not text.startswith('---'): continue
    end = text.find('\n---', 3)
    if end < 0: continue
    fm = text[3:end+1].strip('\n')
    try: d = yaml.safe_load(fm)
    except yaml.YAMLError: continue
    if isinstance(d, dict) and 'type' in d and 'categories' not in d:
        scope.append(rel)
```

**Out of scope (intentional exclusions):**
- 2 malformed-YAML files (deferred to case-by-case work)
- 11 already-canonical files from prior work (have `categories:` already)
- Script-level: files detected as already-canonical skip automatically with `status: skipped_already_canonical`

## Idempotency — verification protocol for any future re-run

```bash
# Copy target dir to avoid committing to two runs
cp -r target target-copy
cd target-copy
python <script> <files>
# Capture per-file sha256 → sha1
sha256sum $(find . -name '*.md') > /tmp/sha1.txt
python <script> <files>     # Run 2 on same files (now canonical)
sha256sum $(find . -name '*.md') > /tmp/sha2.txt
diff /tmp/sha1.txt /tmp/sha2.txt    # Must be empty
```

Idempotency depends on:
1. `updated:` handler — conditional, only writes today's date if not already today's
2. Already-canonical skip (prevents running mutations on already-canonical files)
3. Deterministic routing (`derive_mapping` is pure)

Empirically verified at 204-file scale during Group 25 Step (d.2). Zero mismatches.

## Rollback

**Emergency (destructive):**
```bash
git reset --hard pre-group-25
```
Wipes Group 25 + trailing-newline-fix commits. Tag `pre-group-25` is permanent anchor at `a75b419`.

**Non-destructive:**
```bash
git revert e36d491 5e45ff0
```
Creates revert commits. Preserves history.

## Methodology findings — applicable patterns

Five patterns surfaced during Group 25 execution. Written for future-you (or future-agent) running a similar migration 6-12 months later in a different context. Each is stated as a **detection signal** + **fix pattern** + **when NOT to apply** + **example context** (minimal historical reference).

---

### Finding 1 — Three-source reconciliation for schema vocabulary

**Detection signal.** Schema vocabulary is defined in multiple documentation sources — a migration plan, a mechanics/spec doc, and a primary runtime config (e.g. an agent's instructions file). Uncertainty about which is authoritative; vocabulary elements present in some but not others.

**Fix pattern.**
1. Enumerate every vocabulary element across all sources.
2. Produce a matrix: element / source-A value / source-B value / source-C value / SAME or DRIFT.
3. For known-DRIFT rows: decide per-row which source is authoritative; update the others to match before migration execution.
4. For "present in A, absent in B" ambiguity: default to conservative preservation in the migration; flag for post-migration schema clarification.
5. For vocabulary gaps (migration identifies a needed element no source has): treat as a new entry; add to all sources atomically with the migration.

**When NOT to apply.** Single authoritative source of schema truth. Overhead isn't justified if one document unambiguously wins.

**Example context (Group 25).** Three-way reconciliation across migration-plan.md, mechanics.md, and CLAUDE.md surfaced two vocabulary extensions needed (`operational` + `research` as `[efforts]` subtypes) and one underspecification (`related:` field's required-vs-optional status).

---

### Finding 2 — Windows path-separator normalization in routing logic

**Detection signal.** A script doing string-prefix path checks that must work on Windows. `pathlib.Path(relative_path)` produces backslash-separated strings on Windows. Naive prefix checks with forward-slash patterns fail silently — the check returns False, routing falls through to a default/fallback branch, and files are misclassified.

**Fix pattern.**
```python
rp = str(path_relative).replace('\\', '/')
if rp.startswith('Atlas/concepts/'):
    ...
```
Apply unconditionally before any path-prefix logic. When the script may run across multiple filesystem roots (production vs scratch-dir copies), combine with a multi-anchor resolution that tries each known root:
```python
for anchor in [VAULT_ROOT, SCRATCH_DRYRUN, SCRATCH_IDEM]:
    try:
        rel = str(p.relative_to(anchor)).replace('\\', '/')
        break
    except ValueError:
        continue
```

**When NOT to apply.** Scripts confirmed POSIX-only (pathlib on POSIX produces forward-slash natively). Cross-platform scripts should still apply — on POSIX the `replace('\\', '/')` is a no-op, on Windows it's load-bearing.

**Example context.** Group 25 Step (c) dry-run caught this bug by running the migration on 4 representative files chosen for routing-rule coverage. Would have mis-routed ~19 production files. Operational-priority dry-run selection (stress the routing logic, don't pick at random) is what exposed it.

---

### Finding 3 — Path aggregation precision in scope queries

**Detection signal.** A scope query reports type distributions aggregated by top-level path (e.g., "operational distributed across: `Atlas/` 11 + `Efforts/` 9 + ..."). The type actually lives in multiple subdirectories with different semantic classifications that require distinct routing rules. Fallback branches in the migration script trigger silently on the unhandled subdirectories.

**Fix pattern.**
1. Break scope queries down by full subdirectory path (`Atlas/concepts/`, `Atlas/sources/tech/`, `Atlas/sources/meta/`) rather than by top-level (`Atlas/`). Enumerate every observed subdirectory explicitly.
2. Routing rules must cover every enumerated subdirectory. No "handled by fallback" acceptance.
3. Fallback branches in the script must emit a `stderr` WARN on trigger. Treat fallback firing as a scope-miss bug, not an acceptable default.
4. Post-migration: validate aggregate routing distribution. Expected per-category count (from the scope + routing table) must match actual per-category count. Any delta → investigate specific files.

**When NOT to apply.** Types with single semantic class regardless of path (e.g., a `daily` type is only ever `Calendar/daily/`). Path aggregation precision is unnecessary when path is irrelevant to routing.

**Example context.** Group 25 Q12 at Step (d.2) — two `Atlas/sources/tech/` files carrying `type: operational` fell through the `Atlas/concepts/` → `[concepts]` rule and hit the fallback `[efforts]+operational`. Original scope query reported "Atlas/ 11 operational" which aggregated two distinct subdirectories (`Atlas/concepts/` 9 + `Atlas/sources/tech/` 2). Resolution: add explicit `Atlas/sources/` routing rule, harden script with stderr WARN on fallback.

---

### Finding 4 — Git rename-detection on small-file migrations

**Detection signal.** The migration modifies a substantial portion of small files (< ~1KB, majority frontmatter). Post-migration cumulative-diff count exceeds prediction by +1 per affected file. `git log --follow` shows an `R` classification pre-migration and `A` + `D` post.

**Fix pattern.**
- Anticipate `R`→`A`+`D` reclassification in post-operation cumulative-diff predictions. Add +1 per small file whose content changes materially.
- Document as git-metadata reality, not a content issue. Verify via `body_sha_match` — if body bytes match pre/post and the only change is classification, no action needed.
- `git log --follow <path>` still traces history correctly across the reclassification.

**When NOT to apply.** Migrations on large files where frontmatter changes are a small percentage of total file size. Similarity stays above git's default 50% threshold and classification is stable.

**Example context.** Group 25 Step (d.4) cumulative diff was 297 vs predicted 296. Investigation: `_templates/entity.md` (~500 bytes) shifted `R`→`A`+`D` because the frontmatter rewrite exceeded the 50% similarity threshold.

---

### Finding 5 — Byte-equivalence vs semantic-equivalence verification gates

**Detection signal.** A post-migration byte-comparison gate flags changes that are whitespace-only, line-ending-only, BOM-only, or trailing-newline-count-only. The flagged files have no semantic content change; the content displays identically to end users.

**Fix pattern — classification framework.**

| Category | Examples | Action |
|---|---|---|
| **Semantic-significant** | Field modified; content added/removed; tags changed outside declared scope; character encoding change | Revert and re-execute. Byte-gate is correct. |
| **Semantic-null** | Trailing whitespace normalization; CRLF→LF line-ending conversion per `.gitattributes`; BOM presence/absence; trailing-newline count variance | Document; fix root cause in script; targeted patch to restore exact bytes if needed. Do NOT revert. |

**Distinction principle.** "Meaningful content mutation" is the actual concern. Byte-equivalence is the default proxy. When they diverge on whitespace/encoding edge cases, semantic equivalence wins.

**Root cause pattern for trailing-newline collapse specifically:**
```python
# Bug (collapses n→1):
trailing_nl = text.endswith('\n')          # boolean
text_stripped = text.rstrip('\n')          # strips ALL
# ... rebuild file ...
if trailing_nl and not new_text.endswith('\n'):
    new_text += '\n'                       # adds only ONE

# Fix (preserves exact count):
trailing_count = len(text) - len(text.rstrip('\n'))
text_stripped = text.rstrip('\n')
# ... rebuild file ...
new_text = new_text.rstrip('\n') + ('\n' * trailing_count)
```

**When NOT to apply.** Scripts whose contract is byte-exact preservation (checksum-sensitive content, forensic workflows, signed files). For those, any byte difference is a contract violation regardless of semantic null-ness.

**Example context.** Group 25 Step (e.3) flagged 2 files where trailing-newline count collapsed from 2 to 1. Initial spec required revert. Recalibration distinguished semantic-null case; targeted patch commit (`e36d491`) restored exact bytes without wiping the Group 25 atomic.

---

### Finding 6 — Vocabulary-to-emission pipeline drift

**Detection signal.** Canonical vocabulary defined across documentation sources (spec, mechanics, runtime config) may reconcile clean, while the pipeline that EMITS canonical content — skills' YAML templates, automated generators, hooks — drifts independently. A documentation-only reconciliation (F1) misses emission-source drift; scope planning undercounts the blast radius.

**Fix pattern.**
1. Extend three-source reconciliation (F1) to include every emission source, not just documentation.
2. Enumerate all places that emit canonical vocabulary: skill YAML templates (`tags:`, `categories:`, `type:` fields at known line ranges), hook scripts that write frontmatter, Templater templates, any automated generator.
2a. Before §1 reconciliation, grep all emission sources for every non-canonical namespace in the planned strip list. Example (Group 26): `grep -rn "^- review/\|^- health/\|^- [a-z]" .claude/skills/*/SKILL.md` surfaces every skill emitting a namespace slated for removal. Output is the scope-expansion candidate set; reconciliation verifies each.
3. For each emission source, match emitted content against the canonical vocabulary matrix. Flag drifts as in-scope scope expansions.
4. Pair every vault-content cleanup with the corresponding emission-source update in the same atomic. Without this pairing, post-migration drift recurs on the next emission-source invocation.

**When NOT to apply.** Vocabulary has no automated emission path (pure human-authored content); or the migration explicitly defers emission-source updates to a separate commit with documented rationale.

**Example context (Group 26).** §1 planning initially scoped only `/review` SKILL.md for emission source update (matching the `review/weekly` tag in `_templates/weekly-review.md`). Reconciliation pass against all 17 skill templates surfaced six additional skills (`/challenge`, `/decide`, `/deep`, `/ingest`, `/networth`, `/spark`) with bare or non-canonical tag emissions. Scope expanded from 1 skill to 7 skills. Without this pass, post-Group-26 drift would have recurred on the next invocation of each affected skill.

---

### Finding 7 — Shared extraction logic parity across verification gates

**Detection signal.** Multiple verification scripts in a multi-phase migration (planning census → pre-flight → post-commit verification) implement the same extraction logic (frontmatter parsing, byte-slicing, SHA computation) independently. Minor differences in slice boundaries, line inclusion, or byte handling produce byte-different outputs that look like drift when they are actually extraction artifacts.

**Fix pattern.**
1. Designate a single canonical implementation of extraction logic (typically the census script that produced the baseline).
2. All downstream verification scripts import or copy the canonical extraction byte-exact. No independent re-derivation.
3. If extraction must be re-implemented (e.g., in a different language or environment), verify parity via a round-trip test: run both implementations on a representative sample; SHAs must match per file.
4. When verification fails with a mass-mismatch pattern across files that the migration did not touch, extraction parity is the first hypothesis to rule out before assuming content drift.

**When NOT to apply.** Verification is single-phase with no downstream re-implementation. But even a single-phase migration benefits if it re-uses extraction between dry-run and production verification gates.

**Example context (Group 26).** Step (b) initial drift-detect script used `text[3:end+1]` byte-slicing while the §3.C census used `"".join(lines[1:end_idx])`. Both produce valid-looking frontmatter strings, but the first includes a leading `\n` after the opening `---` fence while the second excises it. Result: 33/33 vault files reported non-tag SHA mismatch (false-positive HALT) until step-b's extraction was re-synced to match §3.C byte-exact. Zero actual drift.

---

### Finding 8 — Idempotency-safe sentinel identifiers

**Detection signal.** A migration or verification script identifies a target block by matching on content that the migration itself modifies. Post-migration, the sentinel is absent and identification fails on Run 2. Idempotency contract breaks — the script aborts on already-migrated files instead of skipping them.

**Fix pattern.**
1. Choose a sentinel that is preserved byte-exact by the migration, observable both pre- and post-migration.
2. For embedded-region identification (e.g., skill SKILL.md layer-2 templates): pair a stable structural marker (`tags:` key at line start — preserved regardless of emptying) with a stable value marker (`type:` subtype value — out of migration scope per preservation declaration).
3. Verify uniqueness in both states: count matches against the sentinel pattern pre-migration AND simulate post-migration; both must yield exactly 1.
4. When idempotency fails, check the sentinel first — silent migration-of-own-sentinel is the most common cause.

**When NOT to apply.** Non-idempotent migrations that are single-use and have no re-run path. Even there, if verification gates re-execute against post-migration state, sentinel stability matters.

**Example context (Group 26).** Step (c) initial sentinel was the source emission tag (e.g., `- challenge` for `/challenge` SKILL.md layer-2 template identification). Post-STRIP on Run 1, the tag was removed; Run 2 sentinel-extraction returned `no_match` and aborted. Refactored to `type: <subtype>` compound-matched with `tags:` key presence (stable across STRIP-to-empty AND across REPLACE). Idempotency passed 40/40 in Step (d.2) full-scale proof.

---

### Finding 9 — Batch atomicity for multi-file migrations

**Detection signal.** Migration script processes N files via per-file temp-rename inside a transform loop. Mid-batch abort (Python exception, I/O failure, validation error on file 15 of 40) leaves partial state on disk: some files renamed to production paths, others not yet written. Rollback requires manual file-by-file reconciliation against git history; pre-migration invariance is not guaranteed.

**Fix pattern.** Two-phase execution:
1. **Phase 1 — compute.** Load all N files, apply transforms in memory, validate each result (SHA checks, tags-key presence, schema invariants). Collect `(dst_path, new_content, result_metadata)` tuples. Abort on any failure produces zero on-disk changes.
2. **Phase 2 — write.** Only after Phase 1 validates all N, write all N via temp-rename. If Phase 2 errors after some writes landed, report the N written before the error for explicit manual reconciliation — Phase 2 I/O failures are rare at small scale but must be surfaced, not silently absorbed.

   Before Phase 2 writes begin, capture per-destination-path pre-migration SHA-256 into a `phase2-backup-manifest.json` artifact. On Phase 2 I/O failure, the manifest gives deterministic rollback via `git show pre-group-N:<path>` per listed file. Surfacing alone is insufficient; recovery must be mechanical, not manual.

This gives batch atomicity: either all N write or none did (excluding Phase 2 I/O, which is rare and always surfaced).

**When NOT to apply.** Single-file migrations. Checkpointed workflows where each file is independently committed and partial success is acceptable. Migrations where in-memory accumulation of N file contents is prohibitive (very large corpus; rarely an issue at vault scale).

**Example context (Group 26).** Step (d) pre-flight step 3 flagged the initial per-file-no-rollback atomicity model as HALT per anti-pattern. Refactored to in-memory-compute-then-write with explicit `pending_writes` list and Phase 1/Phase 2 separation. Phase 1 validates all 40 files' transforms + SHA identity; Phase 2 writes all 40 via `.group-26-tmp` rename pattern. Mid-Phase-1 abort produces zero file changes; mid-Phase-2 I/O error would report `{N written}` to stderr with manual rollback instructions. Production execution on 40 files: zero partial-state risk.

---

### Finding 10 — File-class-aware extraction in verification gates

**Detection signal.** Verification gate uses a single-region extraction model (e.g., "body = bytes after closing frontmatter fence") on files that have multi-region structure (skill SKILL.md with layer-1 frontmatter + layer-2 embedded template; multi-document YAML; other composite file formats). Gate flags scope-expected in-scope changes as body-divergence, producing false-positive FAIL on correct migrations.

**Fix pattern.**
1. Verification extraction must be aware of file-class structure. For multi-region files, define "body" as `file_bytes[:region_open] + file_bytes[region_close:]` — bytes outside the migration's write-target region. Locate `region_open` and `region_close` via an idempotency-safe sentinel (F8).
2. Combine with independent evidence paths to protect against over-wide automated bounds:
   - (a) outside-region SHA-256 pre=post — direct scope-containment proof
   - (b) size-delta identity — full-file Δ == in-region Δ, an arithmetic check independent of SHA
   - (c) diff-region containment using change-lines only (`+`/`-`), excluding git context-line artifacts that may extend past region close
3. Convergence of all three paths is sturdier than any one alone. Divergence across paths indicates either the sentinel is unstable (F8) or the extraction model is wrong (this finding) — debug before accepting.

**When NOT to apply.** File class is strictly single-region (vault markdown with frontmatter + body and no embedded migration targets) AND migration scope is confined to one region. In that case, the single-region extraction in Group 25's §3.C is correct.

**Extends F7.** F7 covers divergent implementations of the same extraction logic (step-b byte-slice vs §3.C census extraction). F10 covers the wrong extraction MODEL for the file class (single-region vs multi-region). Sister findings; apply both in any vocabulary-normalization group that touches multi-region files.

**Depends on F8.** The outside-region evidence path in this finding is only as strong as the sentinel identifying region bounds. An unstable or non-unique sentinel silently invalidates all three evidence paths simultaneously — outside-region SHA matches on wrong bounds, size-delta identity holds on wrong bounds, diff-region containment checks wrong bounds. F10 without F8 is not a gate; it is a confidence illusion. Apply both.

**Example context (Group 26).** Step (e) e.3 body-equivalence. Spec's single-region extraction flagged 7/7 skill SKILL.md files as body-different — scope-expected §2.B layer-2 template modifications appeared as divergence because the spec's "body" (bytes after first `---...---` pair) included the layer-2 template. Three-path evidence classified as scope-expected, not semantic-significant: outside-layer-2 SHA pre=post (7/7); full-file Δ == layer-2 Δ (7/7); diff-region change-lines inside visually-determined layer-2 bounds (7/7). Atomic `ca8f7f24` preserved; spec amended for future groups touching multi-region files.

---

### Finding 11 — Auto-commit flag discipline for steps with a planned commit body

**Detection signal.** A step performs Edit/Write tool invocations on tracked files AND has a specific planned commit body (from spec, handoff, or prompt). The `auto-commit.sh` PostToolUse hook fires per invocation, producing `agent: update <path>` commits before `git commit` with the planned body ever runs. Content lands correctly on disk but the intended commit — the one carrying findings, forward-flags, rollback references, scope rationale — never materializes.

**Fix pattern.**
1. Create `.claude/state/auto-commit-disabled` BEFORE the first Edit/Write on any tracked file.
2. Verify flag present before proceeding.
3. Perform all Edit/Write invocations with flag active.
4. Stage explicitly and commit with the planned body.
5. Remove the flag only after post-commit verification passes.
6. Encode the flag-create/verify/remove sequence as explicit steps in any prompt specifying a commit body.

**When NOT to apply.** Steps performing no Edit/Write invocations on tracked files (pure verification; Bash-subprocess file writes, which bypass the PostToolUse Edit/Write matcher).

**Extends F9.** F9 covers atomicity within a migration script's write phase. F11 covers atomicity between the spec's "write files" step and the spec's "commit with planned body" step — the gap where an unflagged hook interposes generic commits. Both are batch-atomicity concerns at different layers.

**Example context (Group 26 Step f).** Phase 2 spec omitted the flag-create step. Two Edit invocations on `tools/migrations/README.md` (F6–F10 insertion, applicability-table rows) produced two auto-commits with `agent: update tools/migrations/README.md` bodies before the drafted commit body reached `git commit`. Recovery via soft reset to atomic parent + re-commit with planned body + F11 encoded inline. Content on disk was byte-correct throughout; failure was purely in commit-history shape. Step (d.3) got the flag discipline right via explicit flag-create at d.3.1; Phase 2 spec omitted the analog and recurred the failure mode.

---

## Canonical numbering reconciliation

The Group 26 atomic commit body (`ca8f7f24`) used a local numbering scheme that preceded the canonical Part VII assignment in this README. The atomic encoded three findings — local F6 (§3.C extraction parity, now canonical F7), local F7 (idempotency-safe sentinel, now canonical F8), local F8 (batch atomicity, now canonical F9) — and omitted vocabulary-to-emission pipeline drift (canonical F6) and file-class-aware extraction (canonical F10). Canonical Part VII numbering in this README is authoritative for all future reference. The divergence is preserved as an audit artifact of the atomic's time-of-landing context and is NOT corrected via commit amendment (17.6 audit-trail preservation). Any future cross-reference or dependency on a methodology finding should cite this README, not the commit body.

---

## Applying findings to future mechanical groups

| Finding | Applicability |
|---|---|
| 1 (three-source reconciliation) | Any migration with vocabulary/schema defined across multiple source documents. E.g., tag consolidation if canonical tag list exists in multiple locations. |
| 2 (path-separator normalization) | Any Python script doing path-prefix routing on Windows or cross-platform. Apply unconditionally in new scripts. |
| 3 (path aggregation precision) | Any migration whose routing depends on subdirectory semantic. Scope queries should break by full subdirectory; script should stderr-WARN on fallback. |
| 4 (small-file reclassification) | Any migration modifying substantial frontmatter percentage on small files. Predict + accept; not a bug. |
| 5 (semantic vs byte equivalence) | Any post-migration verification gate. Distinguish the two upfront in gate spec; define semantic-null vs semantic-significant edge cases for the specific migration. |
| 6 (vocabulary-to-emission drift) | Any vocabulary-normalization migration whose target vocabulary has automated emission sources (skill YAML templates, generators, hooks). Extend F1 reconciliation to enumerate every emission source; pair vault cleanup with emission-source update in the same atomic. |
| 7 (extraction logic parity) | Any multi-phase migration with census → pre-flight → post-commit verification scripts. Designate a canonical extraction implementation; all downstream re-use byte-exact. Rule out parity drift before assuming content drift on mass-mismatch. |
| 8 (idempotency-safe sentinel) | Any migration or verification script that identifies a target block by content matching. Choose a sentinel preserved byte-exact by the migration itself; verify uniqueness in both pre- and post-migration states. |
| 9 (batch atomicity) | Any multi-file migration (N ≥ 2). Use two-phase in-memory-compute-then-write; capture Phase 2 backup manifest for deterministic rollback on I/O failure. Per-file temp-rename inside a transform loop is unacceptable atomicity. |
| 10 (file-class-aware extraction) | Any verification gate operating on multi-region files (skill SKILL.md with layer-1 + layer-2 template; multi-document YAML; composite formats). Pair file-class-aware body extraction with three independent evidence paths. Depends on F8 for sentinel stability. |
| 11 (auto-commit flag discipline) | Any step with a planned commit body that performs Edit/Write on tracked files. |

## Known edge cases (Group-25-specific, non-generalizable)

- `_templates/entity.md`: `R`→`A`+`D` reclassification per finding 4. Content integrity preserved.
- `Calendar/daily/2026-04-15.md` + `2026-04-16.md`: trailing-newline count restored via `e36d491` per finding 5.
- `wiki/hot.md`: only vault file with inline YAML comment on frontmatter. ruamel preserves inline comments (verified empirically).
- 5 `private/` files: authorized Python-subprocess bypass for structural migration — the agent-write path-guard blocks Claude-tool writes but subprocess execution is the legitimate non-tool channel when authorized. Not a precedent for future operations; each such bypass requires explicit authorization.

## Script invocation

```bash
# Basic (from vault root):
python tools/migrations/group-25-frontmatter-canonicalize.py <file>...

# Re-run safely on already-canonical files:
# Script detects via (categories: present, no domain:) → skips with status message

# With env-guard for auto-commit hook suppression:
touch .claude/state/auto-commit-disabled
python tools/migrations/group-25-frontmatter-canonicalize.py <files>
rm .claude/state/auto-commit-disabled
```

## Related commits

- `5e45ff0` — Group 25 canonical migration (atomic, 206 files: 204 scope + CLAUDE.md + create-skill/SKILL.md vocabulary hygiene)
- `e36d491` — Trailing-newline preservation fix (2 daily files restored)
- `pre-group-25` tag at `a75b419` — permanent rollback anchor
- `a75b419` — Group 24.5 hook fixes (enabled execution environment: jq→python, pre-compact path)
- `c204742` — Auto-commit env-guard capability (env var + file flag)
- `7030cfd` — Group 24 hook rebuild (session-branch, auto-commit, log-prompt, pre-compact, stop-pr)

## Context pointers

- Migration reasoning: `<LOCAL_PATH>\migration-plan.md` Group 25 section
- Methodology findings record (detailed): `<LOCAL_PATH>\STATE.md` Runtime behaviors section
- Schema sources: `<LOCAL_PATH>\mechanics.md` + project root `CLAUDE.md` Category vocabulary table


## Group 27 -- quarantine (closed 2026-04-20)

Atomic commit: `bc0b5412538e12c990bfc09a6e3a280db3b59126`
Preservation commit: this commit
Rollback anchor: `pre-group-27` tag

Scope: 17 files quarantined into `_quarantine/`.
Distribution: stale=2, deprecated=3, superseded=0, broken-fragment=12, other=0.
Collisions resolved via top-dir prefix: 0.
Structural exclusions (6): CLAUDE.md, HOME.md, USER.md, plans/README.md, reviews/README.md, tools/migrations/README.md.
Excluded (Group 29 deferrals): 8 files.

Preserved scripts:
- `tools/migrations/group-27-shared.py` (F7 source of truth; STRUCTURAL_EXCLUSIONS + sentinel_present_in_dst)
- `tools/migrations/group-27-quarantine.py` (F8/F9/F12 — idempotent Run-2 via dst-sentinel; write-before-rename)
- `tools/migrations/group-27-verify.py` (body/fm equivalence audit per §3 census)

Findings applied: F1, F2, F4, F5, F7, F8 extended, F9, F11, F12, F13, F14.

### F12 — Write-before-stage for rename-with-modify
Detect: `git mv src dst` then `dst.write_bytes()` stages pure rename; modifications stay unstaged in worktree. Commit shows 100% similarity rename; post-tree shows M entries.
Fix: Reverse order — write to src first, THEN git mv. git mv reads src's current worktree content and stages rename+modification as one operation.
Emerged: Group 27 Phase F d.3 halt 5. Commit `6cea611` had 20 pure renames with 0 insertions/deletions; 20 files unstaged M with quarantined-date frontmatter. Clean rollback + script fix + re-execution was the recovery path.

### F13 — Git reference type awareness
Detect: `git rev-parse <tag>` on annotated tags returns tag-object SHA, not target commit SHA. Comparison to expected commit SHA fails.
Fix: Use `git rev-parse 'refname^{}'` to dereference. Safe no-op on non-tag refs.
Emerged: Group 27 Phase E d.1 halt 3. Annotated tag pre-group-27 had tag-object SHA 2b79bed; dereferenced commit SHA was 2cc0d61 (baseline).

### F14 — Stage operation scope narrowness
Detect: `git add -A` after git mv sweeps coincidentally-present untracked files into stage. Validation flags unexpected entries.
Fix: Never use `git add -A` or `git add .` in migration scripts. Rely on specific git operations' automatic staging; use narrow path specs only when additional stage needed.
Emerged: Group 27 Phase F d.3 halt 4. Two SessionStart Calendar/daily auto-creates swept into stage after 20 git-mv renames staged correctly.

### F15 — Composition-execution asymmetry (meta-finding)
Detect: Script passes read-review but fails at execution. Multiple consecutive halts on same-script composition bugs in same session.
Fix: (1) Model execution-time state transitions explicitly at composition time; (2) Run novel git-heavy scripts against safe target before production; (3) Two-halt handoff threshold: after two halts on composition bugs in same script same session, pause and compose handoff rather than emitting third corrected script; (4) Add throwaway-repo dryrun gate for git-heavy scripts (shutil.move dryrun validates frontmatter logic but not git semantics).
Emerged: Group 27 halts 3-5 collectively (three consecutive git-idiom bugs: F13, F14, F12).

## Group 28 -- Wikilink repair (2026-04-21)

**Script:** `group-28-normalize.py`

**Scope:** 22 files, 69 wikilink operations. REMOVE_BRACKETS for quarantined/skill/ticker/invocation references (57); RETARGET for path-qualified and aliased navigation links (8). 65 unique edits deduped from 77 orphans discovered in Step 0 scan of 351 vault markdown files.

**Design:**
- Byte-level string replacement per exact (before_string, after_string) pairs from step-2-mapping.json.
- Offset-tracking forward splice preserves regions-outside-edit byte-exact.
- Alias tail treated as opaque bytes; Markdown table pipe-escapes (\|) survive retarget.
- Per-file occurrence-count gate before mutation; idempotency gate after.
- Subprocess calls use capture_output without text=True (F16 Windows cp1252 safety).

**Validation:**
- Step 0 discovery: 1677 wikilinks scanned, 95.41% resolution rate, 77 orphans.
- Step 1/1b reconciliation: 77 -> 65 auto-dispositions + 12 manual, all resolved against on-disk evidence.
- Step 2 re-mapping: dedupe by before_string, detect cross-row after_string conflicts.
- Sample validation: 3 files (sessions-log, HOME, personal-retarget daily), 4 gates (before-absent, byte-delta, offset-based regions-equality, idempotent).
- Full dry-run: 22 files, all 4 gates pass.

**Findings applied/closed:**
- F11 flag discipline (set pre-edit, cleared post-gates).
- F14 narrow staging (no `-A` or `.`).
- F15 two-halt threshold invoked on halt #2 (Gate 3 design); override documented, hardened via offset-based reconstruction.
- F16 bytes compare throughout.
- F17 `--format=''` header-stripping on git log name-status regex gates.

**F12/F18 N/A:** Group 28 is in-place content editing; no file moves or renames.

## Group 29 -- Deferred residue resolution (2026-04-21)

**Script:** `group-29-residue-resolution.py`

**Scope:** 9 unique files across 4 execution classes (+ 1 class ruled no-op).

b1 (atomic): 7 in-place frontmatter repairs
- Q11 non-canonical status -> canonical enum (4 files)
- FF13 missing date fields -> derived from filename (2 files)
- MALFORMED YAML repair + Group 25/26 transforms (1 file)

b2 (atomic): 2 FF14 quarantines via F12 pattern 2
- plans/README.md -> _quarantine/plans--README.md
- reviews/README.md -> _quarantine/reviews--README.md
- Prefix-rename convention per v13 section 9.1

TOPIC_ATS class (4 files) ruled KEEP_AS_IS: topic/* is canonical namespace.

**F12 empirical validation:** pattern 2 validated in isolated throwaway
git repo before production (Phase 0 inline).

**Findings applied:** F11, F12 pattern 2, F13, F14, F15, F16, F17, F18, F19.

## Group 30 -- Verification capstone + closure (2026-04-21)

**Scripts:**
- `group-30-verification.py` -- read-only invariant scanner (I1-I6)
- `group-30-1-interstitial.py` -- add missing `categories:` to one file
- `group-30-2-interstitial.py` -- `<private-file>` canonicalization (3 transforms)
- `group-30-3-interstitial.py` -- sessions-log wikilink remove-brackets

**Verification invariants (I1-I6):**

| Invariant | Rule |
|---|---|
| I1 Canonical schema | Per-file `categories:` single canonical value; `type:` constraints per category; forbidden `domain:` field; `status:` enum; ISO dates |
| I2 Tag taxonomy | Namespaces `topic/*`, `ticker/*`, `company/*`, `thesis/*`; `ticker/*` UPPER; no bare tags; no `domain/*`, `type/*`, `health/*`, `review/*` |
| I3 _quarantine integrity | Exactly 19 files; each has `quarantined-date` + `quarantined-reason` (enum); Group 27 intersection = 17; Group 29 b2 additions present |
| I4 Wikilink resolution | All `[[...]]` spans resolve to existing .md or .base files; _templates exempt |
| I5 Hook behavioral | SessionStart, UserPromptSubmit, PreToolUse, PostToolUse (x2), Stop, PreCompact registered + scripts present; targeted behavioral checks (Group 24.5 methodology) |
| I6 FF9 log-prompt E2E | Today's daily note `## Log` section has real UserPromptSubmit-originated entries |

**Scan scope:**
- In-scope: 198 .md files (all canonical top-level dirs except excluded infrastructure)
- _quarantine (I3): 19 files
- Excluded: 136 (git/Claude/raw/private/tools/docs/_templates/node_modules + gitignored dirs + root infrastructure)

**Scope correction:** .checkpoints/, `<other-tool>`/, .obsidian/, .smart-env/, data/ added to exclusion set post-first-run. All five are `.gitignore`-listed (plugin state, nested repos, local data) -- categorically not vault content. Clarification, not expansion.

**Initial verification produced 3 discrete drift classes** (1 pre-declared + 2 unexpected), each closed atomically:

30.1 @ `553600b` `rebuild(frontmatter): Group 30.1 -- close Group 29 R2 scope-boundary`
- Pre-declared deferral from Group 29 b1 R2 ruling
- Add `categories: [efforts]` to `<private-file>`.md

30.2 @ `bee0103` `rebuild(frontmatter): Group 30.2 -- <private-file> canonicalization`
- Post-malformed Group 25/26 transforms (file escaped both groups while MALFORMED per FF18 history)
- Add `categories: [efforts]`; strip the forbidden top-level `domain:` field and `domain/*` + `type/*` tags

30.3 @ `cc6d514` `rebuild(links): Group 30.3 -- sessions-log <private-file> remove-brackets`
- Group 28 Step 1b ruling propagated to a post-atomic session-log retrospective span

**Closure commit @ `dac5852` `rebuild(verify): Group 30 -- rebuild complete`** confirms all 6 invariants PASS unconditionally post-interstitials.

**Findings applied:** F11, F14, F16, F17, F18, F19. F12/F13 N/A (no renames in Group 30 scope; read-only verification).

**Groups 1-30 closed. Vault rebuild complete.**
