---
name: retro
description: "Session retrospective: close out and capture this session atomically. Use when ending substantive work, when asked to log what was decided before shutting down, or to judge if a session is retro-worthy or already captured. One atomic commit across sessions-log (schema owner) + decision-log + daily note + hot.md; substantive-threshold extraction; empty session HALTs. Modes --preview, --confirm, --continuity-check, --since. Not a past-log lookup or old-decision review."
metadata:
  categories: monitoring
  osanwe-risk: "safe"
  osanwe-effort: "max"
  osanwe-arguments: ""
  osanwe-argument-hint: "[--preview] [--confirm] [--continuity-check] [--since `<date-or-sha>`]"
  osanwe-allowed-tools: "Read Write Edit Grep Glob Bash mcp__robinhood-trading__get_equity_orders"
  osanwe-categories: "meta"
  osanwe-type: "skill"
  osanwe-status: "active"
  osanwe-created: "2026-04-18"
  osanwe-updated: "2026-08-10"
---
# /retro -- session retrospective with atomic multi-file discipline (v2 final)

Capture the current session's substantive decisions + methodology learnings + follow-ups + insights. Persist to 4 target files as single atomic commit with body-preservation invariants.

## When to use / not

Use: session end after substantive work. Not for: trivial sessions, mid-session pauses, time-bound briefings (use /brief).

### Mode routing (Pattern 6 deterministic; invocation modes)

| Syntax | Behavior |
|---|---|
| /retro | Default: extract + persist to 4 target files + atomic commit |
| /retro --preview | Dry-run; show planned extractions + target-section insertions; no write |
| /retro --confirm | Per-item confirmation before apply |
| /retro --continuity-check | Detect gap between last retro and current; warn if >=14 days |
| /retro --since `<date-or-sha>` | Override session boundary (default: since last /retro commit, or last 12h if none) |

## Process

### Phase A -- Pre-flight state verification (v2 final)

Check before any action:

1. HEAD is a commit (not detached): `git rev-parse --verify HEAD`
2. F11 flag not already set: `ls .claude/state/auto-commit-disabled 2>&1` expects absent
3. Target files exist:
   - `Calendar/decisions/sessions-log.md` (MUST exist; fail loud if absent)
   - `Calendar/decisions/decision-log.md` (MUST exist)
   - `wiki/hot.md` (MUST exist)
   - `Calendar/daily/<today>.md` (auto-created by SessionStart hook; create if absent)
4. Inspect changes on the four targets. Preserve unrelated changes and checkpoint the baseline. Changes authored by this same authorized session belong in its atomic close; do not force an extra commit or permission loop. Unattributable changes require reconciliation before writing.
5. Load vault indexes: TICKERS, COMPANIES, MOC_STEMS, THESIS_STEMS, ALL_BASENAMES (for Related wikilinks derivation)
6. Compute pre-edit sha256 for each of the 4 target files (baseline for body preservation)
7. **Fills-reconcile gate (X47p, MANDATORY when orders exist):** if this session placed, staged, or modified any equity order (a broker order tool was invoked, a staged-order JSON exists under the T11 action-staircase convention, or an execute-or-decline row whose action is a trade execution flipped this session), reconcile fills FIRST -- query `get_equity_orders` (the broker read MCP) for executed state and record each fill (price, qty, timestamp) into the relevant execute-or-decline Resolution + the position/entity note BEFORE composing the session record. An unreconciled fill is the dead-`reconcile-orders`-organ failure (X47): a placed trade with no artifact. If NO order was touched this session this check is a no-op -- do not fabricate a reconcile line.

### Phase B -- Session boundary detection (v2.1 ordered fallback)

Determine "this session's" lower temporal bound via three-tier ordered fallback:

**Tier 1 (canonical): most recent /retro commit**

    git log --grep='^retro:' --format='%H %ad' --date=short HEAD -- | head -1

If a match is found: use that commit SHA as the lower bound. This is the normal case after the first /retro has landed -- all subsequent retros chain from the previous retro.

**Tier 2 (first-retro bootstrap): most recent reachable tag**

Only evaluated if Tier 1 returns no match. Execute:

    git describe --tags --abbrev=0 HEAD

If a tag name is returned: resolve to commit SHA via `git rev-parse '<tag>^{}'` (F13 deref) and use that SHA as the lower bound. For this vault's current state (as of v2.1 composition), this returns `rebuild-complete` at `d15c700`, which is the correct bootstrap boundary -- captures everything done since rebuild closure.

If no tags are reachable from HEAD (edge case for new repos or untagged work): proceed to Tier 3.

**Tier 3 (last resort): 12h window**

Only evaluated if Tiers 1 and 2 both return nothing. Use `git log --since='12 hours ago' --format='%H'` as the commit set.

**User override (any tier)**

If `--since <date-or-sha>` flag is provided, bypass all tiers and use the explicit value. Accept YYYY-MM-DD dates or commit SHAs.

**Boundary reporting (required; auditable)**

In the /retro report output AND the commit body, document which tier was used:

    Session boundary: `<boundary-description>`
      Tier fired: <1|2|3|user-override>
      Lower bound: `<commit-SHA>` (<tier-specific context>)
      Artifacts in range: <N> commits, <M> files modified

Example outputs:

- Tier 1: `Session boundary: since last /retro commit; Tier fired: 1; Lower bound: abc1234 (retro: prior-session-title); Artifacts in range: 5 commits, 8 files modified.`
- Tier 2: `Session boundary: first-retro bootstrap via most recent reachable tag; Tier fired: 2; Lower bound: d15c700 (tag: rebuild-complete); Artifacts in range: 18 commits, 47 files modified.`
- Tier 3: `Session boundary: 12h fallback (no prior /retro, no reachable tags); Tier fired: 3; Lower bound: <12h-ago-commit>; Artifacts in range: 3 commits, 4 files modified.`
- User override: `Session boundary: explicit override via --since; Tier fired: user-override; Lower bound: <user-provided>; Artifacts in range: N commits, M files modified.`

Collect session artifacts from the resolved lower bound:

- Commits: `git log <lower>..HEAD --format='%H %s'`
- Files modified: `git log <lower>..HEAD --name-only`

**B.5 -- GATE-B detective check (judgment-gates kit, 2026-07-06):** if the files-modified list contains NEW files (`git log <lower>..HEAD --diff-filter=A --name-only`) under `.agents/skills/` (the CANON skill tree; its generated `.claude/skills/` mirror does not double-count) or `tools/` (excluding `_archive/` and `.precheck/`), a GATE-B sheet dated inside the session window must exist in `wiki/research/gates/`. If none exists: HALT and write the backfill sheet FIRST via the GATE-B procedure (`.agents/skills/gate/ref-gate-tables.md` -- markers with provenance, `gate-eval.py --compute`, sheet, `--check`, registry row). A retroactive SHIP-FIRST or DECLINE verdict is recorded as-is (decline-as-artifact; the honest record IS the point) -- the build already happened, the sheet makes the tradeoff visible and feeds the calibrate lane. No new runtime files -> no-op; do not fabricate a gate line.

### Phase C -- F11 flag set (MANDATORY)

Create `.claude/state/auto-commit-disabled` BEFORE any Edit/Write on tracked files. Single flag covers entire invocation.

### Phase D -- Deterministic extraction with substantive thresholds (v2 final)

Scan current conversation. Classify each identified item with substantive criteria:

**Decision** (ratified ruling affecting future work):

- REQUIRED: (a) explicit ratification language ("let's", "ruling:", "decision:", "we'll ship", "ratified:", confirmed yes/no exchange); AND (b) has stakes (affects future work, not incidental); AND (c) novel (not restating a prior decision already in sessions-log for any date within past 90 days) -- this is the `ratification + stakes + novelty` substantive triad
- Classify tier: Ratified | Proposed | Deferred
- Required fields: decision text (<=2 sentences), rationale (<=1 sentence), source (specific conversation turn reference or commit SHA), tier

**Methodology learning** (pattern-level insight):

- REQUIRED: (a) pattern-level (applicable across future work, not single-instance); AND (b) explicit learning language ("the pattern is", "this taught us", "principle:", "gap surfaced", "when X we should Y", "finding F<N>") OR inferrable from commit messages
- Required fields: learning text (<=2 sentences), context (which work surfaced it)

**Follow-up** (specific actionable item deferred):

- REQUIRED: (a) imperative framing or explicit TODO/`[ ]` marker; AND (b) specific agent + action + domain (not vague "think about X"); AND (c) not already in hot.md Pending Items
- Classify by domain: /enrich candidate | /ingest candidate | /invest candidate | /challenge candidate | /brief candidate | /ingest-SOTA-upgrade candidate | /consolidate-telemetry candidate | general
- Required fields: actionable text (imperative), domain tag

**Telemetry auto-follow-up enrichment (A3 integration)**:

After conversation-derived extraction, dispatch one Bash call to surface signals from the hook telemetry sinks:

    python tools/telemetry_analyzer.py --followups-block

The analyzer returns either a single signal line of the form `[telemetry] orphan_count=N; top_cluster: <tool>::<error_class> x<count>; outliers: <agent_type>(p95=<sec>s)`, OR the literal string `[telemetry] no signals above threshold in window`.

Threshold rules (any one fires inclusion as an auto-follow-up):

- orphan_count >= 1 (Stop with no paired Start; primary surfaced bug)
- top failure cluster count >= 3 (recurring brittle-tool pattern)
- any agent_type with p95 > p50 * 3 (latency outlier)

If the analyzer returns the no-signals string, SKIP inclusion (audit-trail only; not noise). If a signal line is returned, include it verbatim as ONE additional follow-up entry tagged `/consolidate-telemetry candidate`, with the analyzer-output string as the actionable text. Domain tag: `/consolidate telemetry` (the telemetry mode, formerly /telemetry). The line is treated as auto-generated and bypasses the conversation-derived `imperative framing` requirement above (it is structurally actionable: investigate the named signal).

Codex-side fallback: if Codex CLI is the active engine, the analyzer reads an empty `.claude/state/` sink set (no Codex telemetry events) and returns the no-signals string. The integration is no-op under Codex; no /retro failure mode.

**Trade-reconciliation auto-follow-up (Phase D.5; invest vNEXT 2026-06-09; OPTIONAL)**:

If `wiki/research/test-tmp/fills-cache-<today>.json` exists (written this session by an in-session `mcp__robinhood-trading__get_equity_orders` read -- dispatch it at retro start when reviewing a trading week; read-only, D-SEC-1 untouched): run `python tools/reconcile-orders.py --fills wiki/research/test-tmp/fills-cache-<today>.json --json`. Each unmatched fill becomes ONE follow-up entry tagged `/invest candidate` with text "Unmatched fill: `<ticker>` `<side>` `<qty>` @ $`<price>` on `<date>` -- no decision record within +/-3d (FOMO-pattern flag)". If the cache file is absent, SKIP silently (not an error; the fetch is optional). The cache path is gitignored; never write fills data to `.claude/state/` (path-guard).

**Insight** (cross-domain or non-obvious observation):

- REQUIRED: (a) cross-domain OR non-obvious recurring theme; AND (b) explicit insight language ("interesting that", "pattern across", "recurring", "emergence") OR inferrable from structural work
- Required fields: insight text (<=2 sentences)

**Body-scope wikilink validation (v2.2 -- 95-floor architecture)**:

Conversation transcripts often contain `[[X]]` wikilink syntax in prose (e.g., `[[Project-Osanwe]]` referring to the vault codename, a link naming an auto-memory file). When extracted decision/learning/follow-up/insight text is composed verbatim into sessions-log + decision-log, those wikilinks become broken references in the audit-trail files. This was the primary regression vector in the 04-27 incident (vault score 100 -> 35 in 24h).

**Fence-awareness pin (HI-4 fix; Reviewer C F4):** the body-scope scan MUST mirror tools/vault-audit.py v2.1.1 extract_wikilinks() semantics: code-fence-aware (skip lines inside ` ``` ` fenced blocks; up to 3 spaces of indent allowed before fence open per CommonMark), inline-backtick-aware (strip ` `inline code` ` spans before scanning), 4-space-indent code-block-aware (skip wikilinks inside indented code blocks). Wikilinks inside fenced or inline code are PRESERVED verbatim (they are illustrative, not navigational). This prevents over-stripping of decision-text examples that legitimately reference wikilink syntax.

For EACH extracted item, scan its body text for `[[<target>]]` patterns:

- If `<target>` resolves in ALL_BASENAMES (rebuild from `git ls-files -- '*.md' '*.base'`): keep wikilink (legitimate vault reference).
- If `<target>` matches MEMORY_PREFIXES (`memory/`, `memory:`, `feedback_`, `auto_`, `user_`): rewrite as `[[memory:<stem>]]` grammar (visually distinct, machine-detectable, exempt from broken-wikilink checks).
- If `<target>` matches placeholder syntax (`<X>`, `...`, bare `X`, etc.): leave unchanged (script filters these).
- Otherwise: **strip the wikilink brackets, leaving plain text reference**. Log the strip to per-item provenance (`wikilink-stripped: <count>` field).

After stripping, post-validation invariant: each extracted item body must contain ZERO unresolved wikilinks. This is field-scoped across all 4 item categories (decision, learning, follow-up, insight), not just the `Related:` field.

This mechanism converts conversation context into safe persisted text. The 04-26 Phase 3 mechanical de-link of `[[Project-Osanwe]]` is the canonical example; v2.2 makes it automatic for all wikilink classes.

**Threshold cap**: if >20 items total extracted across all four categories, filter to top-15 by (stakes-weight + novelty-weight) and flag the remainder in report as "below-substantive-threshold; not persisted".

**Empty-session safeguard (v2 final)**: If total extracted items = 0:

- HALT with message: "/retro: no substantive items extracted. Session may be too brief or primarily casual. No commit."
- Clear F11 flag
- Do NOT proceed to Phase D-H

### Phase E -- Derive metadata for sessions-log entry

**Title (v2 final Session title derivation rule)**: LLM-synthesize 3-7 word title from session's dominant theme. Examples:

- "Skill SOTA development (3 skills)"
- "Group 29 Phase beta closure"
- "/retro v2 upgrade"
- "theme-alpha Research onboarding"

If the skill can't converge on a clear theme (multi-topic session with no dominant focus), prompt user: "Session title? Suggest: `<fallback>`". Fallback = "Multi-topic session `<YYYY-MM-DD>`".

**Domain (v2 final Primary domain auto-detection rule)**: Auto-detect:

- Most-invoked skill's domain (scan conversation for `/skill-name` patterns + tool invocations; count occurrences)
- Mixed (multiple domains, no dominant): "cross-domain"

**Related wikilinks derivation rule (v2 final)**: Wikilink list derived from:

- Files modified in session commits (extract basenames; map to wikilinks)
- Domain MOCs matching primary domain (e.g., `investing-moc` for investing session)
- Thesis essay stems matching any `thesis/*` tag in decisions/learnings
- Entity note stems for tickers/companies substantively mentioned (>=3 mentions or dedicated discussion)

Apply guardrails:

- Each wikilink target must exist in ALL_BASENAMES (drop prospective links)
- Emit `- "[[<stem>]]"` per canonical v15 schema
- Dedup; canonical ordering (MOCs -> theses -> entities -> peer files)

### Phase F -- Compose sessions-log entry append

Canonical sessions-log schema:

    ### `<YYYY-MM-DD>` -- `<title>`

    **Domain:** `<primary-domain>`
    **Focus:** <1-2 sentence session summary>

    **Decisions ratified:**
    - `<decision>`: `<rationale>`
    ...

    **Decisions proposed (not yet executed):**
    - `<decision>`
    ...

    **Methodology learnings:**
    - `<learning>` (context: <where surfaced>)
    ...

    **Follow-ups:**
    - [ ] `<actionable>` (`<domain>`)
    ...

    **Skills invoked:** /`<skill-1>`, /`<skill-2>`, ...

    **Artifacts:**
    - Commit `<SHA>`: `<subject>`
    ...

    **Related:** `<link-1>`, `<link-2>`, ...

Find end of sessions-log.md as insertion anchor. Compose and append new entry with blank-line separator.

**v2 strangler note (OSANWE-V2 ADR-02):** after the append, run
`python tools/gen-ledger-views.py --ledger sessions --ingest` (node lands in
`Calendar/sessions/`; ledger stays byte-exact; REQUIRED).

Per-file body preservation gate:

- `before_sha256 != after_sha256` (edit happened)
- All content before new entry's insertion position byte-exact (strictly additive)
- New entry's `### YYYY-MM-DD -- <title>` header appears exactly once post-edit
- New content appended at end of file (no modification to prior entries)

### Phase G -- Compose decision-log append

For each RATIFIED decision (not Proposed, not Deferred): append to `decision-log.md`.

Entry format:

    ### `<YYYY-MM-DD>` -- `<decision-title>`
    - **Domain:** `<domain>`
    - **Decision:** <decision text>
    - **Rationale:** `<rationale>`
    - **Source:** `<session-title>`; commit `<SHA-if-applicable>`
    - **Related:** `<wikilinks>`

Find end of decision-log.md; append. Per-file body preservation gate same as Phase F.

**v2 strangler note (OSANWE-V2 ADR-02):** after the append, run
`python tools/gen-ledger-views.py --ledger decisions --ingest` (node lands in
`Calendar/decisions/records/`; ledger stays byte-exact; REQUIRED).

Skip if no Ratified decisions (decision-log not modified; stage excludes it).

### Phase H -- Compose daily note updates

Read `Calendar/daily/<today>.md`. Locate 3 target sections:

- `## Sessions Run`
- `## Decisions`
- `## Insights`

Append within each:

`## Sessions Run`:

    - [HH:MM] /retro -- `<title>` (commit `<SHA-post-retro>`; <N> decisions, <M> learnings, <P> follow-ups)

`## Decisions` (one row per Ratified decision):

    | `<domain>` | `<decision-text-short>` | `<rationale-short>` |

`## Insights` (one line per Insight):

    - <insight text> (from `<session-title>`)

Per-subsection body preservation gate:

- `before_sha256 != after_sha256`
- All content outside the 3 target sections byte-exact
- Within each target section: strictly additive (new lines appended; no prior content modified)

### Phase I -- Generate the session cache (current node architecture)

After Phases F/G append and ingest the relevant ledgers, explicitly regenerate
those views and verify physical history preservation plus node-derived text equality.
Add the actual new session/decision node links to today's Cross-References. Before
replacing hot.md, give its previous Last Session node a durable daily backlink if
it has none; changing the cache must not orphan yesterday's history. Then run:

    python tools/gen-hot.py --apply
    python tools/hot-md-check.py

hot.md is a generated cache, not a manually curated three-session ledger. Its
sources are session nodes and the resolution-aware action ledger. Never demote,
delete, or edit historical node bodies to refresh this view. Corrections and
resolutions remain append-only. The generator must not invent health or an
in-flight phase; current mission authority is STATE.md. Record test evidence and
remaining limitations in the new session entry before generating the cache.

Validate required sections, date parsing and the existing byte budget. A failure
is a content/generator defect to fix, not permission to hand-edit a green cache.

### Phase J.0 -- Pre-commit /vault audit gate (v2.2 -- 95-floor)

After Phase F-I compose their text in memory but BEFORE Phase J atomic write to disk:

1. Write each composed file to a tmp dir (e.g., `/tmp/retro-precheck/sessions-log.md`, `decision-log.md`, daily note, `hot.md`).
2. Run `python tools/vault-audit.py --scope <tmp-path> --json --quick` for each tmp file.
3. Parse JSON output. Tally GATE findings introduced by /retro relative to pre-edit state.
4. Gate logic:
   - 0 GATE findings: proceed to Phase J.
   - >=1 GATE finding: HALT. Report each with file:line and proposed fix. Auto-repair pathway: re-run Phase D body-scope wikilink validation with stricter mechanical de-link, then re-attempt gate. If re-run still fails, surface the diagnostic and halt for user input.
5. Gate also fails on:
   - new orphans introduced (any new file or any file with 0 inbound after composition)
   - body-preservation sha256 violation in append-mode files (content outside insertion window changed)

This is defense-in-depth on top of the PostToolUse `wikilink-check.py` + `frontmatter-check.py` + `orphan-check.py` validators that fire on every Edit. The Phase J.0 gate prevents broken composition from reaching disk in the first place; the PostToolUse validators are the second line of defense.

Bypass: skill-level emergency override via `CLAUDE_VAULT_BYPASS_VALIDATOR=1` env var (logged to `.claude/state/bypasses-<date>.log`).

### Phase F.halt -- Mid-batch failure handling (v2 final)

If any Edit/Write in Phases F, G, H, or I fails (assertion failure, old_string mismatch, path-guard block, sha256 mismatch, ruamel parse failure):

- IMMEDIATE HALT. Do not proceed to remaining Edits.
- F11 flag STAYS ON.
- Any already-applied Edits remain in working tree UNSTAGED. Do NOT commit.
- Report to user:
  - Which phases succeeded (list + file paths)
  - Which phase failed (with failure reason)
  - Which phases were not attempted
  - Current working tree state (file-level diffs of applied Edits)
- User options:
  - `git checkout -- <paths>` to roll back partial applies
  - Fix the failure root cause and re-invoke /retro (idempotency dedup skips successful partial applies via marker signatures)

### Phase J -- Atomic commit

If all phases succeeded without halt:

Narrow-stage (F14) exactly 3 or 4 paths:

- `Calendar/decisions/sessions-log.md`
- `Calendar/decisions/decision-log.md` (if Ratified decisions present; else skip)
- `Calendar/daily/<today>.md`
- `wiki/hot.md`

Assert `git diff --cached --name-only` matches expected set.

Commit body (ASCII only):

    retro: `<session-title>`

    Session captured with SOTA atomic discipline:
    - <N> ratified decisions -> sessions-log + decision-log (if any)
    - `<N-P>` proposed decisions -> sessions-log only
    - <M> methodology learnings -> sessions-log
    - <Q> follow-ups flagged -> sessions-log + hot.md Pending Items
    - <R> insights -> sessions-log + daily note Insights
    - hot.md Last Session refreshed; prior demoted to Previous; Pending
      Items additive-only (no removals triggered this session); Active
      Context refreshed
    - daily note Sessions Run + Decisions + Insights updated

    Domain: `<primary-domain>`
    Skills invoked: /`<skill-1>`, /`<skill-2>`, ...
    Session artifacts: <K> commits since last /retro (`<previous-retro-SHA>`..`<HEAD-before-this-retro>`)

    Preserves: all file content outside insertion sites byte-exact
    (per-file before/after sha256 gates).

    Findings applied: F11, F14, F17.

### Phase K -- F11 clear

Unlink `.claude/state/auto-commit-disabled`. Assert absence.

## Idempotency (v2 spec requirement)

Re-running /retro on same session + same vault state produces zero diff:

- Marker signature per decision: `(session-date, first-80-chars-of-decision-text-normalized)`
- Pre-persist check Phase F: for each proposed decision, check if signature already present in sessions-log for any date in past 7 days. If present, SKIP (log "already captured").
- If ALL items already captured: no Edits composed; no commit; report "/retro: idempotent on this session; already captured at `<prior-commit-SHA>`."

Property: /retro twice in same session produces zero diff after first run.

## Continuity check (--continuity-check)

- Find most recent entry date in sessions-log.md (last `### YYYY-MM-DD` heading)
- Compare to most recent commit date: `git log -1 --format=%ad --date=short HEAD`
- If gap >= 14 days: WARN with gap stats and commit count in gap
- Diagnostic only; no writes

### Quality Rules

- **Path-guards (mechanical):** NEVER write to: `.raw/`, `private/`, `_quarantine/`, `finance/`, `credentials/`, `.git/`, `.claude/hooks/`, `.claude/state/`. Defense-in-depth; retro targets should never be in these zones.
- **Tag vocabulary guardrail:** If /retro emits any tags (e.g., in hot.md Active Context updates that introduce tags): ALLOWED_TAG_NAMESPACES = {topic, ticker, company, thesis}. HALT on drift.
- **Write paths are exactly four:** `Calendar/decisions/sessions-log.md`, `Calendar/decisions/decision-log.md`, `Calendar/daily/<today>.md`, `wiki/hot.md`. Nothing else is ever written; decision-log is skipped entirely when no Ratified decision exists.
- **Body preservation on every target:** `before_sha256 != after_sha256` AND all content outside the insertion sites byte-exact. A violation is a Phase F.halt, never a commit.
- **ASCII only** in every composed entry and commit body (Pattern 22); Co-Authored-By suppressed (F17-verified); F14 narrow staging; F11 Phase C discipline mandatory.
- **Substantive thresholds are the filter:** an empty session HALTs (no commit, no noise); idempotent re-runs produce zero diff via marker signatures.

## Coordination with other skills

Shared infrastructure:

- Vault indexes (TICKERS, COMPANIES, MOC_STEMS, THESIS_STEMS, ALL_BASENAMES) for Related wikilinks derivation
- BACKLINKABLE_CATEGORIES (unused directly; /retro doesn't create back-links outside its 4 targets)
- F11 Phase C discipline
- Tag vocabulary guardrail
- ASCII-only commit bodies
- Co-Authored-By suppressed
- F14 narrow staging

/retro runs AFTER session work; produces Follow-ups tagged by candidate skill so downstream users know which skill to invoke for each follow-up.

## Examples

### Example 1: Skill SOTA development session (this-conversation shape)

Session scope: 3 skill upgrades (/enrich v1->v9, /ingest v1->v2 final, /deep v1->v2), 2 real skill runs (geo enrich + ingest), 18 commits post-rebuild-complete, handoff v15 composed.

Phase D extracts (with thresholds applied):

- 10+ Ratified decisions (MAYBE collapses to binary; target_path custom field; symmetric back-linking principle; marker-signature dedup; claim-to-section mapping; per-fact provenance format; F11 Phase C timing; 20 SOTA patterns catalog; pressure-test-before-ship discipline; compose-time miscalibration lesson)
- 5-7 Methodology learnings (VERBATIM-reference pitfall; loose line-count estimates; v9 retro pattern across /enrich and /retro; autonomous-placement vs explicit-target-override precedence; skill-coordination-via-shared-infrastructure)
- 15+ Follow-ups (15 remaining skills for SOTA polish in Tier-priority order; verify unknown commits b02af8f + 4c5d03c; retroactive geo audit-chain fix; weekly /review rhythm; quarterly ref-doc refresh cadence)
- 3-5 Insights (vault compounding philosophy; deterministic-rule over probabilistic-scoring; /enrich-and-/ingest as complementary preservational/transformational; SOTA iteration pattern generalizable across all skills)

Phase E derives:

- Title: "Skill SOTA development (/enrich v9 + /ingest v2 + /deep v2)"
- Domain: meta/skill-infrastructure
- Related: [[knowledge-moc]], hot, sessions-log, decision-log, geopolitics-playbook, LMT, RTX, investing-moc, ...

Phases F-I apply atomically. Phase J commits 4-file atomic. Phase K clears F11.

### Example 2: --preview

Runs A-E, emits plan (extractions + target-section insertions for each of 4 files + proposed title + domain), halts before F. User reviews plan; reinvokes without --preview if acceptable.

### Example 3: Empty session

Short session: "what time does MSFT report?" answered, no decisions or accomplishments. Phase D extracts 0 substantive items. HALT with message; no writes; F11 cleared.

### Example 4: Idempotent re-run

/retro twice in same session. Second run Phase D extracts same items; Phase F dedup via marker signatures matches all; no Edits composed; no commit. Report: idempotent.

### Example 5: Mid-batch failure

Phase F (sessions-log append) succeeds; Phase G (decision-log append) fails because old_string anchor changed since Phase A pre-flight. IMMEDIATE HALT. F11 stays on. Report: sessions-log applied (unstaged in working tree); decision-log failed; daily note + hot.md not attempted. User `git checkout -- sessions-log.md` to rollback, or fixes decision-log root cause and re-invokes /retro.

### Example 6: --continuity-check

Diagnostic: last sessions-log entry 2026-04-03; most recent commit 2026-04-22. Gap 19 days, 42 commits in gap. Warning emitted; user decides whether to manually reconstruct (low ROI per v15 handoff guidance) or accept.

## Related skills

- `/brief` -- morning briefing using sessions-log context from recent /retros
- `/challenge` -- stress-tests decisions captured in decision-log
- `/spark` v2 -- pattern detection over decision-log + sessions-log + briefings histories with 5 modes + continuity audit + FOLLOWUPS:skills feeding /retro
- `/vault` v2 -- vault-integrity audit + stats with Brier continuity + repair mutation + ref-doc refresh; FOLLOWUPS:skills feeds /retro for session-end cleanup follow-up
- `/enrich`, `/ingest` -- skills whose invocations /retro captures under Skills invoked
