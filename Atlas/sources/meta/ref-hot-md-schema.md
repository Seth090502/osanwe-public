---
categories: [sources]
type: reference
created: 2026-05-02
updated: 2026-06-11
status: active
confidence: high
tags:
  - topic/vault-architecture
  - topic/skill-infrastructure
  - topic/hot-md-schema
aliases: [hot-md-schema, hot-schema]
related:
  - "[[ref-research-methodology]]"
---

# Reference: hot.md Schema (v2)

Last updated: 2026-05-02
Source: SOTA overhaul v2 single-atomic-commit (commit f8a1c80 + this commit)

Canonical specification for `wiki/hot.md` -- the highest-leverage continuity mechanism in Project Osanwe. Replaces implicit v1 schema (drifted to 17 stacked Last Session blocks before remediation). Enforced by `tools/hot-md-check.py` PostToolUse hook + /retro Phase J.0 pre-commit gate + /vault audit 10th classifier.

## 1. Purpose & lifecycle position

`wiki/hot.md` serves as the agent-side continuity anchor: SessionStart hook (`tools/session-start.sh`) injects it into every Claude session; `/brief`, `/spark`, `/retro`, `/decide`, `/vault`, `/networth` read or write it. It is NOT a chronological archive -- that role belongs to `Calendar/decisions/sessions-log.md` (append-only). Hot.md is a **rolling window** + active state cache.

The 2026-05-02 SOTA overhaul (Phase A migration audit at `wiki/maintenance/hot-md-migration-audit-2026-05-02.md`) trimmed hot.md from 552 lines / 17 Last Session blocks to ~290 lines / 2 Last Session blocks, after byte-equivalence verification confirmed sessions-log holds canonical archive. Going forward, /retro v2.2 demote-AND-DELETE invariant maintains <=3 Last Session blocks indefinitely.

## 2. Section structure & canonical headings

```
[frontmatter L1-N: 24 canonical fields per sec 3]
# Session Cache

## Last Session                          (current; mandatory)
## Last Session -- Previous              (1 prior; mandatory)
[OPTIONAL] ## Last Session -- Previous-Older  (1 older; max)
## Pending Items                         (live; cap 60 active items)
[OPTIONAL] ## Pending Items -- Recently Completed (last 14d)  (rolling buffer; cap 10)
[OPTIONAL] ## Pending Items -- Cold Storage   (auto-archived >30d; cap 30)
## Active Context                        (mandatory; per sec 4.3)
Related: ... (mandatory footer; wikilinks)
```

INVARIANTS enforced by hot-md-check.py:
- Last Session block count: exactly 1 current + 0-1 Previous + 0-1 Previous-Older = max 3 total
- Required H2 sections present: Last Session, Pending Items, Active Context
- Total hot.md size target: <8KB (fits SessionStart hook context budget without smart-emit invocation)

## 3. Frontmatter schema (24 canonical fields)

| Field | Type | Owner skill (write-path) | Constraint |
|---|---|---|---|
| `categories` | list | static | == ["wiki"] |
| `type` | string | static | == "synthesis" |
| `created` | date | bootstrap | immutable; YYYY-MM-DD |
| `updated` | date | every writer | bumped to today on every retro/brief/vault/spark/networth |
| `status` | string | static | == "active" |
| `tags` | list | static | == [] (hot.md is operational state, not topical content) |
| `aliases` | list | static | == ["session cache", "hot"] |
| `related` | list | /retro Phase E + /vault refresh | 5-12 wikilinks; load-bearing for symmetric back-link discovery |
| `last_briefing` | date | /brief Phase P | YYYY-MM-DD; staleness WARN >2d |
| `last_audit` | date | /vault audit | YYYY-MM-DD; WARN >7d |
| `last_audit_score` | int | /vault audit | 0-100 |
| `last_audit_run` | date | /vault audit | YYYY-MM-DD |
| `last_audit_trend` | string | /vault audit | freeform enum (e.g., "stable-at-floor-recovered") |
| `last_audit_milestone` | string | /vault audit | freeform |
| `last_stats` | date | /vault stats | YYYY-MM-DD |
| `last_stats_calibration_score_30d` | num/null | /vault stats | 0-1 (Brier-style) or null |
| `last_refresh` | date | /vault refresh | YYYY-MM-DD |
| `last_refresh_top_qualitative` | string | /vault refresh | wikilink-stem |
| `last_refresh_top_formula` | string | /vault refresh | wikilink-stem |
| `last_repair` | date | /vault repair | YYYY-MM-DD |
| `last_repair_outcome` | string | /vault repair | freeform enum |
| `last_spark` | date | /spark | YYYY-MM-DD |
| `last_networth` | date/null | /networth Phase Q | YYYY-MM-DD; consumed by Active Context Portfolio Snapshot subsection; WARN >7d |
| `schema_version` | string | bootstrap | == "hot-md-v2"; rejecting any other value |

`hot-md-check.py` enforces: every field present (or null where allowed), no rogue fields outside this set, exact `schema_version` literal match.

## 4. Lifecycle rules

### 4.1 Last Session demote-cycle (per /retro Phase I v2.2)

Read hot.md. Capture body sha256. Apply 4 sequential Edits:

```
EDIT-I.1 (delete prior Previous-Older if present):
  old_string: "\n## Last Session -- Previous-Older\n" + <body through next "## " H2 non-inclusive>
  new_string: "\n"
  Skip if no Previous-Older heading present.

EDIT-I.2 (demote Previous to Previous-Older):
  old_string: "## Last Session -- Previous\n"
  new_string: "## Last Session -- Previous-Older\n"
  Assert: 1 occurrence pre-edit; 1 post-edit.

EDIT-I.3 (demote current Last Session to Previous):
  old_string: "## Last Session\n"
  new_string: "## Last Session -- Previous\n"
  Assert: 1 occurrence pre-edit; 1 post-edit.

EDIT-I.4 (insert new Last Session above former Last Session):
  old_string: "## Last Session -- Previous\n- **Date:** "
  new_string: "## Last Session\n" + <new block> + "\n## Last Session -- Previous\n- **Date:** "
```

POST-EDIT VALIDATION: count "## Last Session" headings = 1; "## Last Session -- Previous" = 1; "## Last Session -- Previous-Older" <= 1; total Last Session blocks <= 3. Run hot-md-check.py; HALT on any GATE.

### 4.2 Pending Items prune protocol

**Item insertion format (mandatory in all writers post-2026-05-02):**
```
- [ ] **<title>** -- <body> (<domain>; trigger: <date|condition>; **age_seed: YYYY-MM-DD**; from /retro YYYY-MM-DD)
```

**Per-/retro processing rules:**

1. **Auto-prune to Recently Completed**: items containing `[x]` checked OR explicit `completed: YYYY-MM-DD` OR `superseded: YYYY-MM-DD` markers move from live `## Pending Items` to `## Pending Items -- Recently Completed (last 14d)` rolling buffer (cap 10; items aged >14d in buffer drop; sessions-log retains audit chain).

2. **Auto-flag stale**: items with `today - age_seed > 14d` get a leading `(STALE Nd)` marker prepended. /brief consumes for "Stale follow-ups: N items >14d" BLUF line.

3. **Auto-archive to Cold Storage**: items with `age_seed > 30d` AND no execution markers AND no edits in 7d demoted to `## Pending Items -- Cold Storage` (cap 30; oldest evicted to sessions-log).

4. **Hard caps**: live <=60; Recently Completed <=10; Cold Storage <=30. Overflow evicts oldest to sessions-log atomically.

**Grandfather marker**: existing pre-v2.2 items without age_seed are tolerated when `MIGRATED-AGE-PENDING` banner present at top of `## Pending Items`. Validator skips strict per-item age_seed enforcement until next /retro cycles each item with explicit age_seed.

### 4.3 Active Context refresh windows + boundary doctrine

Active Context contains 5 v2 subsections (legacy `### Operational state` retired):

| Subsection | Owner skill (writes) | Refresh window | Allowed content + cap |
|---|---|---|---|
| `### Vault tooling state` | /vault refresh + /retro Phase I.6 | 7d | SOTA-skill list, ref-doc count, hook-state, audit-score |
| `### Rebuild status` | /retro Phase I.6 | event-only | Phase, milestone tag, next gates |
| `### Portfolio Snapshot` | /networth Phase Q ONLY | 24h | combined + cash + largest position + thesis-exposure-pct (4 fields exact) |
| `### Active Blockers` | /retro + /career + /invest | 7d | <=3 entries; trigger + owner + age; auto-prune on resolution |
| `### Watch Triggers` | /brief + /invest | session | calendared events <14d (earnings, FOMC, expiry); auto-prune past dates |

**Hard rules** (hot-md-check.py enforces):
- Legacy `### Operational state` MUST NOT exist (HARD-fail if present)
- Portfolio Snapshot field count <=4
- Watch Triggers entries: each entry must contain a date >=today; past-date HARD-fail
- Active Blockers <=3 entries
- Vault tooling state staleness >7d -> WARN; >14d -> SOFT
- Portfolio Snapshot staleness >7d -> WARN to /networth refresh

**Architectural correction (2026-05-02 v2):** portfolio-snapshot data lives in `/networth` outputs at `Calendar/networth/networth-<date>.md`; hot.md Active Context inherits only the 4-field summary line via /networth Phase Q write-back. This retires the dual-purpose-stale-data-dump pattern of v1 Operational state.

## 5. Integration contracts (per-skill matrix)

### 5.1 /retro
- Phase I.1-I.4: 4-edit demote-AND-DELETE sequence (sec 4.1)
- Phase I.5: Pending Items additive merge (sec 4.2)
- Phase I.6: Active Context refresh (Vault tooling state + Rebuild status; v2 subsections)
- Frontmatter: bumps `updated:` only

### 5.2 /brief
- Phase P: bumps `last_briefing:` to today's ISO
- Reads Pending Items count + oldest age (smart-emit summary line); surfaces "Stale follow-ups: N items >14d" in BLUF if oldest >14d
- Never writes Pending Items section
- Watch Triggers: writes calendared catalysts <14d; auto-prunes past dates

### 5.3 /vault (per mode)
- audit: bumps `last_audit`, `last_audit_score`, `last_audit_run`, `last_audit_trend`, `last_audit_milestone`
- stats: bumps `last_stats`, `last_stats_calibration_score_30d`
- refresh: bumps `last_refresh`, `last_refresh_top_qualitative`, `last_refresh_top_formula`; refreshes Vault tooling state subsection
- repair: bumps `last_repair`, `last_repair_outcome`
- 10th audit classifier `hot-md-schema-drift`: runs hot-md-check.py; surfaces findings in audit JSON; score weights GATE -10, HARD -3, SOFT -1, WARN 0
- Never touches Last Session blocks or Pending Items

### 5.4 /spark
- Phase N Update 3: bumps `last_spark:` to today's ISO
- Reads hot.md for cross-domain pattern detection
- Never writes Pending Items

### 5.5 /decide
- Phase J: appends to Pending Items with `age_seed:` field per sec 4.2 format
- Marker-signature de-dup against existing Pending Items
- Never writes Last Session or Active Context

### 5.6 /networth (NEW Phase Q write-back)
- After computing portfolio snapshot: writes 4-field Portfolio Snapshot subsection to hot.md Active Context
- Bumps `last_networth:` to today's ISO
- Body-preservation sha256 invariants matching /retro Phase I rigor
- Never writes other hot.md sections

### 5.7 Read-only consumers
- /career, /invest, /enrich, /ingest, /challenge, /tasks, /golf, /health, /create-skill: read hot.md as context only; never mutate

## 6. SessionStart hook emission protocol

Hook script: `tools/session-start.sh` lines 17-32.
Smart-emit helper: `tools/hot-md-emit-smart.py` (~120 LOC).

**Threshold logic:**
- If `wc -c hot.md` <= 8192 bytes: emit raw (full hot.md).
- Else: invoke `hot-md-emit-smart.py --input hot.md --max-bytes 8192`.
- On smart-emit failure: fall back to raw cat. Telemetry to stderr (`# hot-md emit: full|smart-mode|fallback-to-raw N bytes`).

**Smart-emit priority order:**
1. Always full: frontmatter (24 fields).
2. Always full: `## Last Session` block.
3. Always full: `## Active Context` (all subsections).
4. Pending Items: 1-line summary banner + first N=15 active items + full Recently Completed buffer.
5. Skip: `## Last Session -- Previous` and `Previous-Older` blocks (banner with date hint pointing to sessions-log).
6. Always: `Related:` footer.

## 7. Validation tooling

**File:** `tools/hot-md-check.py` (~250 LOC).
**Hook:** PostToolUse on Write|Edit|MultiEdit with `${CLAUDE_FILE_PATH}` filter on `wiki/hot.md`.
**Position:** after wikilink-check + frontmatter-check, before auto-commit.

**12 validators (rule catalog):**

| Rule | Severity tier | Trigger |
|---|---|---|
| `check_frontmatter_schema` | GATE/HARD | missing critical fields OR rogue field OR schema_version mismatch |
| `check_section_count` | GATE | >3 Last Session blocks OR != 1 current OR >1 Previous |
| `check_section_presence` | GATE | missing required H2 (Last Session / Pending Items / Active Context) |
| `check_pending_items_age_seed` | HARD | items lack age_seed AND no MIGRATED-AGE-PENDING banner |
| `check_pending_items_cap` | HARD | live count > 60 |
| `check_pending_items_completed_pruned` | SOFT | [x] item in live section instead of Recently Completed |
| `check_active_context_subsections` | SOFT | missing Portfolio Snapshot OR other v2 subsection |
| `check_no_operational_state` | HARD | legacy "Operational state" subsection present |
| `check_portfolio_snapshot_field_count` | HARD | >4 fields |
| `check_watch_triggers_dates_future` | HARD | entry with date <today |
| `check_active_blockers_cap` | HARD | >3 entries |
| `check_<last_*>_age` | WARN/SOFT | staleness threshold breach (last_audit / last_briefing / last_networth) |

**Output format**: structured JSON with `ok`, `section_sha256` (per-section hash for body-preservation audit), `findings`, `stats`. Exit code 0 on ok==true; 1 on GATE; 2 on infrastructure error.

**Bypass**: `CLAUDE_HOT_MD_BYPASS_CHECK=1` env var; logged to `.claude/state/bypasses-<date>.log`.

## 8. Migration history

- 2026-05-02 commit f8a1c80 (Phase A-C-F-lite urgent-fix subset):
  - hot.md trimmed 552 -> 290 lines (47% reduction); 17 -> 2 Last Session blocks
  - /retro Phase I rewrite v2.2 with demote-AND-DELETE invariant
  - Frontmatter additions: `schema_version: hot-md-v2`, `last_networth: null`
  - Pre-rollback tag `pre-hot-md-v2-2026-05-02`
  - Pre-migration backup at `wiki/_archive/hot-2026-05-02-pre-v2.md`
- 2026-05-02 commit (this commit; Phases D-E-G-H-I-J structural):
  - tools/hot-md-check.py validator (12 rules + structured JSON output)
  - tools/hot-md-emit-smart.py + session-start.sh threshold upgrade (8KB)
  - Atlas/sources/meta/ref-hot-md-schema.md (this doc)
  - hot.md Active Context restructure (retire Operational state; add Portfolio Snapshot + Active Blockers + Watch Triggers placeholders)
  - hot.md Pending Items grandfather banner (MIGRATED-AGE-PENDING)
  - .claude/settings.json PostToolUse hook registration
  - /brief + /vault + /networth + /decide SKILL.md updates
  - CLAUDE.md schema reference

## 9. Failure modes & rollback

**Common failure modes:**
- /retro Phase I.4 Edit fails: anchor mismatch on "## Last Session -- Previous\n- **Date:** "; F.halt protocol per /retro spec; F11 stays on; user runs `git checkout -- wiki/hot.md` and re-invokes.
- hot-md-check.py false-positive: bypass via `CLAUDE_HOT_MD_BYPASS_CHECK=1`; investigate validator rule + open a remediation task.
- /networth Phase Q write-back fails: Active Context Portfolio Snapshot stale; WARN at 7d via validator; user runs /networth manually.

**Rollback to pre-overhaul state:**
```
git reset --hard pre-hot-md-v2-2026-05-02   # if commit is HEAD
# OR
git revert <commit-sha>                      # safer; preserves history
```
Or copy `wiki/_archive/hot-2026-05-02-pre-v2.md` back to `wiki/hot.md` for manual restore.

## Related

hot.md | [[knowledge-moc]] | [[ref-research-methodology]]
