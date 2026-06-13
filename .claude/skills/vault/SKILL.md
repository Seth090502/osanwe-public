---
name: vault
risk: critical
description: Run vault maintenance and audit. Use when daily integrity scan is due, after substantive multi-file refactors, before /retro session-end ratification, weekly stats dashboard refresh, or pre-/deep invocation for ref-doc staleness check. Obsidian vault maintenance with deterministic mode routing (Pattern 6) wrapping tools/vault-audit.py for 9 audit classifiers (broken-wikilinks, missing-frontmatter, frontmatter-schema, orphan-detection, stale-refs, deprecated-skill-references, daily-continuity, template-drift, MOC-coverage), 18-statistic dashboard with Brier-style continuity scoring across runs, idempotent daily-note manager with schema-drift detection (9-section canonical), confirmation-required repair mutation mode with SAFE-AUTO vs NEEDS-CONFIRM classification + per-fix preview + body-preservation sha256 invariants on every Edit, ref-doc freshness ranker with thesis-importance weighting, atomic-multi-file discipline matching /retro v2.1, FOLLOWUPS:skills coordination block surfacing /retro + /enrich + /ingest + /spark + /deep candidates with concrete one-line rationale and time-to-decision triggers, meta.json sidecar for machine-readable audit + cross-run vault-health calibration, same-day -HHMM collision handling preserving archival rule, F11 Phase C atomic-commit + F14 narrow stage + F17 Co-Authored-By verify, ASCII-only new content (Pattern 22), 18-item Pre-Output HALT gate, mid-batch F.halt on partial-failure, deprecation-aware exclude-list (does not flag _archive/ skills as orphans). 5 modes: audit (default, integrity scan) / stats (quantitative dashboard) / daily (today's note manager) / repair (--apply <ids>, mutation) / refresh (ref-doc staleness ranker). Reads broadly across Atlas/wiki/Calendar/Efforts/private; never deletes (move-to-archive only). Writes to wiki/maintenance/audit-<date>[-HHMM].md + stats-<date>[-HHMM].md + repair-<date>[-HHMM].md + refresh-<date>[-HHMM].md plus sidecars. Coordinates with /retro (FOLLOWUPS:skills feeding session-end), /enrich (frontmatter-schema fix candidates), /spark (vault-health pattern detection), /deep (ref-doc refresh candidates).
arguments: [mode]
argument-hint: "audit | stats | daily [--append <text>] | repair --apply <ids> | refresh [--scope <domain>]"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, Agent]
effort: max
user-invocable: true
---

## Quality Standards

- Audit operations are READ-ONLY. Repair operations require explicit user confirmation per fix.
- NEVER delete files. Move-to-archive only (`<ARCHIVE_ROOT>/` per vault convention).
- Reports include severity classification, not just enumeration: CRITICAL / WARNING / INFO.
- All findings cite specific files + line numbers; no vague "some files have issues".
- Continuity scoring uses Brier-style calibration across runs (read prior 3 stats reports for trend).
- Daily-note operations are idempotent: same input -> same output -> zero diff on re-run.
- Repair-mode classification is conservative: anything ambiguous routes to NEEDS-CONFIRM, not SAFE-AUTO.
- **Subagent dispatch is MANDATORY when specified by phase** (audit MODE Phase D dispatches `vault-classifier-sweep`). Pre-emptive skip based on judgment ("script will probably work fine inline", "JSON parsing not worth the dispatch overhead") is FORBIDDEN. The subagent wraps `tools/vault-audit.py --json` and returns a structured findings JSON; the parent skill dispatches and validates the return. Legitimate fallback fires ONLY on (a) contract violation -- subagent return missing required JSON keys, OR (b) actual dispatch failure -- timeout, rate limit, tool-denial, hard subagent crash. Pre-emptive skip surfaces in Phase L audit report as **DEVIATION** (not "fallback"). Quality preserved by additive design: the direct script invocation remains as fallback for legitimate dispatch failures.

## When to use / not

Use: post-deprecation health check (after major skill changes), weekly vault-integrity sweep, before-/-after substantial multi-file refactors, ref-doc staleness audit pre-/deep invocation, daily-note schema verification.

Not for: cross-domain pattern recognition (use /spark), session-end retrospective (use /retro), morning briefing (use /brief), document onboarding (use /enrich), claim extraction (use /ingest), task-list rollup (use /tasks).

Output is diagnostic + recommended fixes; mutation requires explicit `repair --apply <ids>` after audit.

## Invocation modes (Pattern 6 deterministic routing)

| Syntax | Behavior |
|---|---|
| `/vault` or `/vault audit` | Default; read-only integrity audit; 9 classifiers; report + sidecar |
| `/vault stats` | Quantitative dashboard; 18 statistics; Brier-style continuity score |
| `/vault daily` | Today's daily-note presence + schema verification; report state to stdout |
| `/vault daily --append "<text>"` | Append text to today's `## Sessions Run` section (sha256-preserved) |
| `/vault repair --apply <issue-id-list>` | Mutation; consumes most recent audit report; per-fix confirmation |
| `/vault refresh` | Ref-doc staleness ranker; thesis-weighted priority report |
| `/vault refresh --scope <domain>` | Narrow refresh to one domain (`investing` / `career` / `health` / `golf` / `meta`) |
| `--preview` (modal flag) | Phases A-N in memory; render to stdout; SKIP all writes; F11 never set |
| `--confirm` | Block before each Write |
| `--since <date-or-sha>` | (audit/stats only) Explicit baseline override for stats deltas |
| `--scope <path>` | (audit/refresh) Narrow scan to one top-level subtree |
| `--no-peripheral` | Write report file + sidecar only; skip Phase P peripheral updates |

Default with no arguments: `audit`.

## Process

Audit mode is the canonical reference. Stats / daily / repair / refresh modes share Phase A/B/C/L/N/O scaffolding; mode-specific logic in Phase D-K.

### MODE: audit (default) -- 15 atomic operations

#### Phase A -- Pre-flight

1. Parse args + flags.
2. Resolve today's ISO date.
3. Resolve `OUTPUT_PATH` = `wiki/maintenance/audit-<today>.md`.
4. Same-day collision check: if exists, default `-HHMM` variant; `--replace` reserved.
5. F11 collision check (`.claude/state/auto-commit-disabled` exists -> HALT).

#### Phase B -- State-transition print (BEFORE F11)

Emit planned reads + planned writes + collision-handled output path to stdout. Format:

    /vault audit -- planned state transition:
      reads: tools/vault-audit.py output (5 classifiers); .claude/skills/_archive/ (deprecation exclude-list);
        Calendar/daily/ (continuity check); _templates/daily.md (drift check); knowledge-moc.md (MOC-coverage)
      writes:
        - wiki/maintenance/audit-<today>[-HHMM].md (NEW)
        - wiki/maintenance/audit-<today>[-HHMM]-meta.json (NEW sidecar)
        - Calendar/decisions/sessions-log.md (append)
        - wiki/hot.md (last_audit frontmatter bump if any CRITICAL findings)
      F11 set after this print

#### Phase C -- F11 set + parallel context load

1. `touch .claude/state/auto-commit-disabled` BEFORE any Write.
2. Build `EXPECTED_ARCHIVED` set: list `.claude/skills/_archive/` folders (currently includes /research, /review, plus prior version-bumped tombstones).
3. Build `KNOWN_DEPRECATIONS` set: parse `Calendar/decisions/decision-log.md` for entries containing "Deprecate" / "deprecated" / "moved to _archive".
4. Build `CANONICAL_DAILY_SCHEMA`: 9 sections per CLAUDE.md sec 4.5: Market Pulse / Observations / Decisions / Commitments / Insights / Sessions Run / Cross-References / Tasks / Log.
5. Build `CANONICAL_FRONTMATTER_FIELDS`: categories (plural list), type (optional), tags (plural), status (enum), created (ISO), updated (ISO), related (wikilinks).
6. Build `FORBIDDEN_FRONTMATTER_FIELDS`: `domain` (stripped per CLAUDE.md schema), legacy fields.
7. Build `FORBIDDEN_TAG_NAMESPACES`: `domain/*`, `type/*`.

#### Phase D -- Classifiers 1-5 (DELEGATED dispatch + script fallback)

**Phase D.0: DELEGATED dispatch to `vault-classifier-sweep` subagent (PREFERRED path; Phase C wiring 2026-05-02)**

**MANDATORY** (per Quality Standards): dispatch first, no pre-emptive skip. The subagent (Sonnet max for compute discipline) wraps `tools/vault-audit.py --json` and returns structured findings JSON keyed by classifier with severity tier per finding plus composite score.

Use the Agent tool with subagent_type `vault-classifier-sweep`. Pass input: `{scope: "<--scope value or 'all'>"}`. Expected return: JSON with keys `broken_wikilinks`, `missing_frontmatter`, `frontmatter_schema`, `orphan_detection`, `stale_refs`, `deprecated_skill_refs`, `daily_continuity`, `template_drift`, `moc_coverage`, `totals`, `score`, `score_floor_check`, `failures`.

Validate subagent return:
- All 9 classifier keys present (even if empty arrays)
- `totals` object with `gate`, `hard_drift`, `soft_drift` counts
- `score` integer 0-100
- `score_floor_check` in {`PASS`, `WARN`, `BREACH`}
- ISO timestamp present
- Severity tier strict: `GATE | HARD DRIFT | SOFT DRIFT` (uppercase) per finding

On contract violation OR dispatch failure: fall through to inline script invocation below. Surface fallback in Phase L audit report.

On dispatch success: parse the returned JSON; classifiers 1-5 are populated by the script. Phases E-I below populate classifiers 6-9 inline (they are not part of the script). Skip the inline `python tools/vault-audit.py` invocation.

**Phase D.1: Direct script invocation (FALLBACK; runs ONLY if Phase D.0 failed)**

Execute `python tools/vault-audit.py` (existing script handles 5 of 9 classifiers):

1. **Broken wikilinks** (CRITICAL) -- regex extract `[[target]]`; verify target file exists; report unresolved
2. **Missing frontmatter** (CRITICAL) -- check first line `---`; report files lacking frontmatter
3. **Orphan detection** (WARNING) -- entity files with <2 inbound wikilinks; exclude templates + archive folders
4. **Stale refs** (WARNING) -- `Atlas/sources/*/ref-*.md` with `updated:` >30 days; thesis-weighted annotation
5. **MOC-coverage gaps** (INFO) -- files in domain subtree NOT linked from corresponding MOC

Capture script output; parse into structured findings list.

#### Phase E -- Classifier 6: Frontmatter-schema violations (NEW; INLINE)

Glob `**/*.md` (excluding `.git/`, `node_modules/`, `_archive/`, `.checkpoints/`, `.obsidian/`, `.smart-env/`):
- Extract frontmatter; check `categories` is a plural LIST (not scalar string)
- Check forbidden `domain:` field absent
- Check tags do NOT use forbidden namespaces (`domain/*`, `type/*`)
- Check `status:` value within enum (active/paused/done/dropped/stub/deprecated/draft/complete/stale)
- Severity: WARNING

#### Phase F -- Classifier 7: Deprecated-skill references (NEW; INLINE)

Grep vault for active-skill-list deprecations (currently `/research`, `/review` post-2026-04-26). Exclude:
- `.claude/skills/_archive/` (expected-archived)
- `docs/VAULT-HANDOFF-V*.md` (institutional history)
- `Calendar/decisions/decision-log.md` (decision audit trail)
- `CLAUDE.md` historical sections

Pattern: `\b/(research|review)\b` plus skill-invocation form `(use /research)` etc. Report any matches outside excluded paths. Severity: INFO (not breaking; cleanup candidate).

#### Phase G -- Classifier 8: Daily-note continuity (NEW; INLINE)

List `Calendar/daily/*.md` for past 30 days; sort by date; detect missing dates in sequence:
- Day-of-week awareness: weekend gaps acceptable IF no `Sessions Run` activity expected
- Sample known good cadence from prior 90 days for baseline
- Severity: INFO; report gap dates + count

#### Phase H -- Classifier 9: Template-drift (NEW; INLINE)

Read `_templates/daily.md`; verify all 9 canonical sections present (Market Pulse / Observations / Decisions / Commitments / Insights / Sessions Run / Cross-References / Tasks / Log). Severity: WARNING if any missing.

(Current state at 2026-04-26: template has 7 sections; missing Commitments, Cross-References, Log. Audit will surface this.)

#### Phase I -- Severity rollup + FOLLOWUPS:skills emission

Group findings by severity (CRITICAL / WARNING / INFO); for each, generate concrete one-line FOLLOWUPS entry tied to specific file paths. Block bounded to <=8 entries total. Examples:

    <!-- FOLLOWUPS:skills -->
    - [CRITICAL] /vault repair --apply L1-L7 -- 7 broken wikilinks in wiki/entities/tickers/ (trigger: NOW)
    - [WARNING] /enrich candidate -- 12 files missing categories: field; batch-add via /vault repair --apply F1-F12 (trigger: EOW)
    - [WARNING] /vault repair --apply T1 -- _templates/daily.md missing 3 canonical sections (Commitments, Cross-References, Log) (trigger: NOW)
    - [INFO] /retro candidate -- 7 daily-note continuity gaps in past 21 days; consider session-cadence retro (trigger: EOW)
    - [INFO] /vault repair --apply D1-D3 -- 3 deprecated-skill references outside expected paths; safe-auto cleanup (trigger: EOW)
    <!-- /FOLLOWUPS:skills -->

Empty case: `(no followup skills recommended; vault clean)`.

#### Phase J -- Composite vault-health score (v2.2 -- 95-floor)

Tier-weighted score (0-100; 95-floor architecture per Plan #2 in
`wiki/research/vault-prevention-architecture-2026-04-27.md`):

**GATE classifiers** (must-be-zero; broken-wikilinks, missing-frontmatter,
frontmatter-schema, template-drift):
- per finding: -5; cap -10
- if any GATE finding present, score hard-clamped to <= 90 (surfaces hook-bypass)

**HARD DRIFT classifiers** (orphan-detection, stale-refs):
- per finding: -1; cap -5

**SOFT DRIFT classifiers** (deprecated-skill-references, daily-continuity, MOC-coverage):
- per finding: 0  (advisory only; surfaced in INFO section + FOLLOWUPS:skills + meta.json
  soft_drift_count field; ZERO score impact)

**Continuity adjustment:** +/-2 (declining/improving trend across prior 3 audits);
suppressed when raw_pre_trend < 97 OR any GATE finding (avoids double-counting drift
already conveyed by HARD DRIFT and prevents trend penalty pulling clean state below 95).

**Major-rehabilitation bonus: REMOVED** (was a v2.1 calibration-era band-aid;
the new 95 floor makes it unnecessary).

**Floor invariant:** 95/100 in steady state. The only path below 95 is a GATE breach,
which surfaces as a 90-cap. Industry pattern: SonarQube quality gates separate must-be-zero
gate metrics from headline maintainability rating; CodeClimate weights findings by
remediation-effort (GATE=seconds, HARD=minutes, SOFT=hours-to-never); Vault Physician
0-100 gauge with color-coded green/yellow/red based on weighted classifier severity.

**Formula:**

    raw_pre_trend = 100 + max(GATE_n * -5, -10) + max(HARD_n * -1, -5) + 0
    if raw_pre_trend >= 97 AND GATE_n == 0:
        raw = raw_pre_trend + trend(+/-2)
    else:
        raw = raw_pre_trend
    score = clamp(0, 100, raw)
    if GATE_n > 0: score = min(score, 90)

**Calibration history:**
- v2.1 (post-2026-04-26): canonical -10/-3/-1 weights, +5/+10 trend bonuses, -50/-25/-10
  caps. Mathematical floor under that scheme was ~80/100 with full GATE blocking
  because INFO-class drift could accrue -10 cap.
- v2.2 (post-2026-04-28): tier-weighted (GATE/HARD DRIFT/SOFT DRIFT). SOFT DRIFT exerts
  zero score gravity, raising the floor to 95. Aligns with industry practice (SonarQube
  quality gate, Vault Physician 0-100 gauge, CodeClimate technical-debt ratio).

**SOFT DRIFT findings still emit FOLLOWUPS:skills entries with [SOFT-DRIFT] severity tag.**
The score does not punish them, but the action recommendation is preserved. This separates
"how clean is the vault" (the score) from "what should be cleaned next" (FOLLOWUPS).

#### Phase K -- Pre-Output HALT gate (18-item invariant check)

1. F11 set
2. `OUTPUT_PATH` collision resolved (`-HHMM` if needed)
3. Frontmatter complete and schema-compliant on report
4. >=1 finding category populated OR explicit "vault clean" rendered
5. All findings reference specific file paths (not vague "some files")
6. Severity classification on every finding (CRITICAL / WARNING / INFO)
7. FOLLOWUPS:skills block syntactically valid; tied to specific issue IDs
8. Vault-health composite score computed; rationale included
9. Continuity comparison vs prior audit (when prior exists) populated
10. EXPECTED_ARCHIVED exclude-list applied (no false-positive deprecation flags)
11. CANONICAL_DAILY_SCHEMA reference embedded for template-drift Classifier 9
12. ASCII-only on report body + sidecar (Pattern 22)
13. `related:` field has 3-5 wikilinks ([[hot]], [[knowledge-moc]], peer audit reports if any)
14. Symmetric back-link plan ([[hot]] last_audit bump; sessions-log entry)
15. Path-guard: no proposed Write targets `.raw/`, `private/`, `finance/`, `credentials/`
16. Sessions-log entry composed per canonical schema
17. hot.md `last_audit` field present (add if missing)
18. F17 Co-Authored-By absent in planned commit

#### Phase L -- ASCII pre-write scan (Pattern 22)

Byte-scan all NEW content. HALT on byte >127. Replace em-dash, smart quotes, ellipsis with ASCII.

#### Phase M -- Compose audit report + meta.json sidecar

Per `ref-output-templates.md` schema. Body sections:
1. H1 + Generated stamp + audit scope
2. Executive Summary (composite score + finding-count-by-severity)
3. CRITICAL Findings (with file paths, line numbers, fix recommendations)
4. WARNING Findings
5. INFO Findings
6. Continuity vs Prior Audit (when applicable)
7. FOLLOWUPS:skills block
8. Footer (calibration line)

#### Phase N -- Final verification

Re-read composed body; re-run gate items 4, 7, 12; confirm internal references.

#### Phase O -- Atomic write

1. Write `OUTPUT_PATH` (audit report).
2. Write `OUTPUT_PATH-meta.json` (sidecar).
3. F14 narrow stage: `git add` exactly these 2 files.
4. F.halt: if either fails, HALT IMMEDIATELY; F11 stays on; structured report; no partial commit.

#### Phase P -- Peripheral updates (skip if `--no-peripheral`)

1. **Sessions-log entry:**

       ### YYYY-MM-DD -- /vault audit -- score <N>/100
       - **Domain:** meta/skill-infrastructure
       - **Findings:** <C> CRITICAL, <W> WARNING, <I> INFO
       - **Followup skills:** <count> (<comma-list>)
       - **Artifacts:** [[audit-<date>[-HHMM]]]
       - **Related:** [[hot]] | [[knowledge-moc]]

2. **hot.md frontmatter bump:** `last_audit: <today>` (add if absent).

3. **hot.md `last_audit_score: <N>`** field (NEW; tracks vault-health continuity).

4. F14 narrow-stage all touched files; atomic commit `vault: audit -- score <N>/100 -- <C>C/<W>W/<I>I`.

5. F17 verify: post-commit `git log -1 --format=%B | grep -c Co-Authored-By` MUST be 0.

6. F11 clear: `rm .claude/state/auto-commit-disabled`.

### MODE: stats -- 10 atomic operations

Same Phase A/B/C/K/L/N/O/P scaffolding. Mode-specific Phases D-J:

#### Phase D-J: 18 statistic blocks per ref-stats-catalog.md

1. file-counts-by-top-level-path (Atlas / Calendar / Efforts / wiki / private / docs / .claude/skills active / .claude/skills/_archive)
2. word-counts-by-top-level-path (with kepano 150-line exception annotation)
3. entity-coverage (held tickers vs entity-note presence)
4. ref-doc-coverage (Built vs stub from knowledge-moc table vs frontmatter status)
5. freshness-distribution (<7d / <30d / <90d / >90d per top-level path)
6. career-pipeline-by-status (READY_TO_SUBMIT / SUBMITTED / INTERVIEWING / OFFERED / REJECTED / CLOSED)
7. session-log-entry-count (rolling 30d)
8. daily-note-continuity-score (1.0 = no gaps; weighted by day-of-week expectations)
9. skill-invocation-frequency (parsed from session-log entries)
10. brier-calibration-carry (prior 30d /vault stats predictions vs current state)
11. avg-wikilinks-per-file
12. outbound-link-orphans (files with 0 outbound)
13. inbound-link-orphans (files with 0 inbound; excluding templates/archives)
14. MOC-coverage-percentage (per MOC: linked-files / total-domain-files)
15. thesis-essay-activity (mention count per `tag/thesis-*`)
16. archive-skill-count (read-only sanity)
17. active-vs-archived-skill-ratio
18. tools-script-inventory (count + last-modified per tool)

Each statistic with formula in `ref-stats-catalog.md`; thesis-importance weights for prioritization.

#### Continuity Brier scoring (NEW; mirrors /brief)

Read prior `wiki/maintenance/stats-*.md` last 3 reports. Each report's meta.json includes `predicted_30d_trend` field. Score current state against predictions: `(predicted - actual)^2`. Surface `calibration_score_30d` in stats report header.

Output: `wiki/maintenance/stats-<today>[-HHMM].md` + sidecar; sessions-log entry; hot.md `last_stats: <today>` bump.

### MODE: daily -- 8 atomic operations

#### Phase A: Pre-flight (presence check)
- `Calendar/daily/<today>.md` exists?
- If absent: HALT with diagnostic `Daily note for <today> missing -- bash tools/session-start.sh should have created. Run manually OR restart session.` Do NOT recreate from /vault (canonical creation path is the SessionStart hook).

#### Phase B-D: Schema verification
- Read body; verify all 9 canonical sections present
- Drift detection: report missing sections; offer `/vault repair --apply S1` style fix codes

#### Phase E: State surface
- Count items per section
- Show oldest unchecked Commitment age (if any)
- Show Cross-References count

#### Phase F-G: --append flag handling (only when present)
- F11 Phase C set
- Body-preservation sha256 capture
- Append `[HH:MM] <text>` to `## Sessions Run` section
- sha256 verify content outside that section unchanged
- Atomic commit; F11 clear

#### Phase H: Stdout state report

Output: stdout state report (no file write unless `--append`).

### MODE: repair -- 12 atomic operations (mutation discipline)

#### Recommended `/goal` wrapper (B1 integration; v2.1.139+ feature)

When fixing the vault back to floor (`score >= 95 AND tiers.gate.count == 0`) requires multiple audit-repair cycles -- common when a repair fix introduces a new finding, or when NEEDS-CONFIRM rejections leave residual GATE -- wrap the entire repeat-invocation pattern in `/goal`. This makes the loop EXPLICIT and AUDITABLE via transcript evidence, and the Haiku-class evaluator enforces a structured halt condition that resists worker-text fabrication.

Canonical condition string (insert verbatim; do NOT regress to a weaker variant; R8 mitigation):

> Halt only when a Bash `tool_result` block (paired by `tool_use_id` to a Bash `tool_use` that invoked `python tools/vault-audit.py --json`) appears in the transcript AND that tool_result's content contains JSON with `"score": N` where N >= 95 AND `"tiers": {"gate": {"count": 0, ...}}`. Worker-generated text claiming the audit passed is INSUFFICIENT; only a paired (`tool_use_id` -> `tool_result`) block counts as evidence. Each iteration must produce a fresh Bash `tool_use` invocation of `python tools/vault-audit.py --json` and a corresponding `tool_result` block. Do not stop on partial progress; do not stop on inferred-pass without the structured `tool_result` block visible. The Haiku-class evaluator reads the structured transcript representation (tool_use/tool_result objects with paired `tool_use_id`), not rendered text.

Anti-gaming primitive: harness-emitted `tool_use_id` / `tool_result` pairing CANNOT be fabricated by the worker (only the harness emits those records). A worker that fabricates a passing audit in prose cannot also fabricate the paired tool_result block. This closes the R8 condition-gaming risk where a Haiku-class evaluator might accept "appears done" text without true verification.

Recommended invocation shape (user-side):

    /goal "<canonical condition string above>" Iterate /vault audit + /vault repair --apply <ids> cycles until clean

The repair mode below remains single-pass-atomic per invocation. /goal sits ABOVE the skill, orchestrating multiple skill invocations until the structured evidence condition fires.

#### Phase A: Pre-flight
- Verify `--apply <issue-id-list>` arg present; if absent HALT with usage hint
- Build `MOST_RECENT_AUDIT_PATH` via `Glob wiki/maintenance/audit-*.md` sort by mtime descending

#### Phase B: Load most recent audit report; parse issue IDs from FOLLOWUPS:skills + classifier sections

#### Phase C: Match requested IDs
- HALT if any ID not found
- Warn if audit is >7 days old (state may have drifted)

#### Phase D: Classify each fix by safety
- **SAFE-AUTO:** missing frontmatter field add, `updated:` bump, wikilink correction WHEN target unambiguous (single-candidate basename), template-drift fix
- **NEEDS-CONFIRM:** file rename, file move, content modification, MOC link insertion, batch frontmatter rewrite
- **BLOCKED:** any deletion (move-to-archive only via `<ARCHIVE_ROOT>/`)

#### Phase E: Per-fix preview
- Each fix shows diff (current state vs proposed state)
- SAFE-AUTO fixes batched into single preview block
- NEEDS-CONFIRM fixes presented individually

#### Phase F: Explicit user confirmation
- One prompt per NEEDS-CONFIRM
- One batch-yes for all SAFE-AUTO

#### Phase G: F11 set (only AFTER user confirmation, BEFORE any Write)

#### Phase H: Atomic apply
- Execute all confirmed fixes as single atomic commit
- Body-preservation sha256 invariants on every Edit
- Path-guard mechanical check on every Write target (defense in depth)

#### Phase I: Mid-batch F.halt
- If any Edit fails, IMMEDIATE HALT, F11 stays on
- Structured report (succeeded / failed / not-attempted)
- No partial commit

#### Phase J: Repair audit log
- Write `wiki/maintenance/repair-<date>[-HHMM].md`
- List each issue ID, classification, action, before/after sha256
- F14 narrow-stage all touched files

#### Phase K: Atomic commit
- Prefix `vault: repair -- <X> SAFE-AUTO + <Y> CONFIRMED applied`
- F17 verify

#### Phase L: F11 clear

### MODE: refresh -- 8 atomic operations

#### Phase A: Pre-flight (same as audit)

#### Phase B: State-transition print

#### Phase C: F11 set + load all `Atlas/sources/*/ref-*.md` AND `.claude/skills/*/ref-*.md`

#### Phase D: Compute staleness (days since `updated:`)

#### Phase E: Compute path-activity-since-update
- For each ref doc, count files in same domain subtree created/modified after ref-doc's `updated:` date
- Signals ref doc may be missing recent findings

#### Phase F: Compute priority score
- `priority = days_stale * path_activity * thesis_importance_weight`
- Weights from `ref-stats-catalog.md`: orbital-compute=1.5, tokenized-settlement=1.2, grid-storage=1.0, platform-moats=1.0, core-index=0.8, career=1.3, golf=0.7, supplements=0.5, meta=1.1

#### Phase G: Compose ranked refresh report
- Output: `wiki/maintenance/refresh-<today>[-HHMM].md`
- FOLLOWUPS:skills block emits `/deep` candidates for top-3 priority refs (Pattern 21 candidates)

#### Phase H: Atomic write + Phase P peripheral

## Audit classifier reference

9 classifiers with detection rules + severity tiers + safe vs needs-confirm repair patterns in `ref-audit-classifiers.md` (~600-900 lines). SKILL.md Phase D-H lists classifier names + severity; ref doc holds full detection logic + repair-classification rules + worked examples per classifier.

## Statistics catalog reference

18 statistics with formulas + thesis-importance weights + Brier-score calibration mechanics in `ref-stats-catalog.md` (~400-600 lines). SKILL.md stats mode Phase D-J lists statistic names; ref doc holds computation logic + freshness-bucket boundaries.

## Output schema reference

Canonical frontmatter + body section order + meta.json schema for audit / stats / refresh / repair reports + daily-note 9-section schema in `ref-output-templates.md` (~300-400 lines). All output paths and formats specified there.

## Migration note (v1 -> v2)

| v1 element | v2 fate |
|---|---|
| `wiki/meta/vault-*.md` output path | DEPRECATED -- new path `wiki/maintenance/`. Old reports left in place; v2 audit skips reading them. |
| `/vault health` (mode name) | RENAMED `/vault audit`; old name accepted as alias with deprecation warning |
| `/vault report` (mode name) | RENAMED `/vault stats` |
| `/vault fix` (mode name) | RENAMED `/vault repair --apply <ids>`; explicit issue IDs replace open-ended interactive |
| 7-step health scan | EXPANDED to 9 classifiers; Classifiers 6-9 NEW (frontmatter-schema, deprecated-references, daily-continuity, template-drift) |
| Thesis weights inline in /vault refresh | MOVED to `ref-stats-catalog.md` |
| Daily template recreate (v1 step in `/vault daily`) | REMOVED -- canonical creation path is `tools/session-start.sh`; /vault daily HALTs if missing rather than recreating (avoid divergence) |

## Coordination with other skills

- **/retro** -- session-end retro consumes /vault FOLLOWUPS:skills; sessions-log entry parsed for continuity
- **/enrich** -- /vault audit surfaces frontmatter-schema fixes as /enrich candidates; /enrich's onboarding can introduce broken back-links that /vault audit detects
- **/spark** -- /vault stats output feeds /spark Class 8 (tool-skill usage pattern) detection; /spark FOLLOWUPS may surface /vault candidates for meta-pattern detection
- **/deep** -- /vault refresh top-3 priority refs become /deep candidates (Pattern 21 Deep Research recomposition)
- **/brief** -- /vault stats vault-health-score read by /brief Phase B as one input to overall-state assessment
- **/ingest** -- distinct skill (transformational); /vault is preservational + diagnostic
- **/career**, **/invest**, **/health**, **/golf** -- /vault audit checks their output paths for orphans + frontmatter compliance

## Path-guards (mechanical)

NEVER write to: `.raw/`, `private/`, `finance/`, `credentials/`. NEVER delete (move-to-archive only via `<ARCHIVE_ROOT>/`). All writes route through `wiki/maintenance/` (audit/stats/refresh/repair reports), `Calendar/decisions/sessions-log.md` (append), `Calendar/daily/` (today only, Sessions Run section append for `--append`), `wiki/hot.md` (last_audit/last_stats frontmatter bump), `_templates/daily.md` (template-drift repair only via /vault repair --apply T1).

## Tag vocabulary guardrail

Audit report tags: `topic/vault-maintenance`, `topic/integrity`, `topic/<mode-stem>` (e.g., `topic/audit`). Forbidden: `domain/*`, `type/*`. Frontmatter MUST have `categories: [wiki]` and `type: report`.

## Failure taxonomy

| Failure | Phase | Symptom | Recovery |
|---|---|---|---|
| F11 collision | A | another skill in-flight | Wait OR `rm .claude/state/auto-commit-disabled` if confirmed orphan |
| Same-day collision | A | OUTPUT_PATH exists | Default `-HHMM`; user can `--replace` |
| vault-audit.py failure | D (audit) | script exits non-zero | HALT; surface stderr; suggest manual classifier 1-5 fallback (rare; script is stable) |
| Audit too old for repair | C (repair) | most-recent audit >7d | Warn; user explicitly confirms or runs fresh /vault audit first |
| Issue ID not found in audit | C (repair) | `--apply <id>` doesn't match any audit finding | HALT; show valid IDs from audit |
| Pre-Output gate failure | K | any of 18 invariants violated | HALT with item-specific diagnostic; F11 stays on |
| ASCII byte >127 | L | non-ASCII in NEW content | Replace and retry; do NOT proceed |
| Mid-batch Write failure | O | first Write succeeded, second failed | F.halt; F11 stays on; structured report; user `git checkout -- <orphan>` or fix-and-retry |
| Body-preservation sha256 violation | H (repair) | Edit changed content outside intended insertion site | F.halt; back out the Edit; sha256-preserving retry |
| Daily-note absent | A (daily) | today's daily missing | HALT with diagnostic; do NOT recreate (canonical path is session-start.sh) |
| Schema-drift on today's daily | D (daily) | <9 sections present | report; offer /vault repair --apply S1 |
| F17 verify fail | P | Co-Authored-By in commit body | `git commit --amend` to remove |

## Examples

### Example 1: default audit (post-deprecation health check)

`/vault` -> reads vault state including `_archive/` deprecation list; runs 9 classifiers (5 wrapped from script + 4 inline); composes audit report + sidecar; surfaces FOLLOWUPS for any CRITICAL/WARNING findings; updates sessions-log + hot.md last_audit + last_audit_score. Use after major skill changes (like the 2026-04-26 /research + /review deprecation).

### Example 2: stats with continuity scoring

`/vault stats` -> computes 18 statistics; reads prior 3 stats reports for Brier calibration; reports vault-health trend (improving / stable / declining); writes `wiki/maintenance/stats-2026-04-26.md`. Use weekly for vault-health continuity tracking.

### Example 3: daily-note schema verification

`/vault daily` -> reports today's note state; flags missing canonical sections; surfaces /vault repair candidates for schema fixes. No file write unless `--append`.

### Example 4: repair after audit

`/vault audit` -> finds 7 broken wikilinks (L1-L7) + 12 missing frontmatter (F1-F12) + 3 deprecated-references (D1-D3) + 1 template-drift (T1).
Then: `/vault repair --apply L1-L3,F1-F12,T1` -> classifies (L1-L3 mixed; F1-F12 SAFE-AUTO; T1 SAFE-AUTO); per-fix preview; user confirms NEEDS-CONFIRM individually + batch-yes for SAFE-AUTO; atomic apply; repair audit log written.

### Example 5: refresh ranking

`/vault refresh` -> reads all 23 ref docs; computes staleness * path-activity * thesis-weight; ranks; FOLLOWUPS surfaces /deep candidates for top-3 priority. Use before next /deep invocation to choose highest-leverage Pattern 21 onboarding target.

### Example 6: scoped audit

`/vault audit --scope Atlas/concepts/investing/theses/` -> narrows scan to thesis essays only; useful for thesis-evolution-aware audits before /challenge invocations.

## Related skills

- `/retro` -- session-end retrospective; consumes /vault FOLLOWUPS
- `/enrich` -- consumes /vault FOLLOWUPS frontmatter-schema fix candidates
- `/spark` -- consumes /vault stats vault-health-score; surfaces /vault FOLLOWUPS for meta-pattern detection
- `/deep` -- consumes /vault refresh top-3 ref docs (Pattern 21 candidates)
- `/brief` -- reads /vault stats vault-health-score as one input
- `/tasks` -- distinct skill (Tasks-plugin wrapper); not vault-integrity
