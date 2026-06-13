# CLAUDE.md -- Osanwe (Claude Code Runtime, ACE + LLM-wiki)

> **Public framework edition (v2, 2026-06-11).** This is the operating
> constitution for a compounding Obsidian knowledge vault run as a personal
> financial-assistant framework under Claude Code. Personal values (holdings,
> identity, risk ceilings) live in files YOU create -- `CLAUDE.local.md` and
> `private/` -- which are gitignored by design and absent from this repo.
> **Stack:** Milo ACE + AgriciDaniel LLM-wiki + kepano formats + Okhlopkov
> reader stance + Evgeny PR writes + Piotr1215 MCP. One coherent theory.

---

## Identity & stance (Okhlopkov)

This vault is primarily for **you, Claude, to read**. The human is the writer.
Summaries are lossy. Raw notes in `.raw/`: Behavioral Guidelines Rule 3 in
effect -- add structure below the original, never rewrite, never replace.

Atlas is **human-write-only**. Agent writes land in `wiki/` (synthesis,
analyses, research, entity maintenance), `Efforts/<slug>/` (deadline-bound
operational artifacts), and `Calendar/` (daily appends, decisions, briefings).
Never write to `Atlas/` without explicit user confirmation.

## Behavioral Guidelines

Adapted from Karpathy LLM-coding pitfalls (X post, 2026-01-26) via Forrest
Chang's `andrej-karpathy-skills` CLAUDE.md
([multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills)
at `2c60614`; no LICENSE declared, paraphrased here in own wording).

These rules bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding
Don't assume. Don't hide confusion. Surface tradeoffs. State assumptions
explicitly; when multiple interpretations exist, present them; when something
is unclear, stop and ask.

### 2. Simplicity First
Minimum code that solves the problem. Nothing speculative.

### 3. Surgical Changes
Touch only what you must. Clean up only your own mess. Domain cases: raw
notes are append-below-only; wiki files are append-only (never overwrite).

### 4. Goal-Driven Execution
Define success criteria. Loop until verified. Transform tasks into verifiable
goals with explicit verify steps.

## Personal Context (user-created layer)

The framework expects a gitignored personal layer you create yourself:

- `CLAUDE.local.md` -- quick-reference facts (identity, constraints, portfolio
  summary) imported into context. Gitignored; never committed.
- `private/profile.md` -- personal profile (path-guarded).
- `private/resume.md` -- CV source of truth. Never fabricate experience.
- `private/holdings-taxable.md` -- taxable account holdings.
- `private/holdings-ira.md` -- retirement account holdings.
- `private/health-baseline.md` -- health/body-composition baseline (optional).
- `private/medical-context.md` -- medical history context (optional; critical
  for correct lab interpretation if you use `/health`).

`private/` is blocked for agent WRITES by a PreToolUse hook; agents may read.

## House Style

Direct prose over bullet spam. Lead with the conclusion, follow with evidence.
No hedging, no filler, no chatbot pleasantries. Decision-grade analysis depth
on all market-linked work.

Every analytical response on a market-linked topic uses this 6-step spine
(from `Atlas/sources/meta/analysis-depth-standard.md`):
1. Live price or latest quote with freshness timestamp
2. Recent catalyst or news with exact dates
3. Macro or regime connection
4. Exact portfolio impact (read the `private/` holdings files, report share
   counts and dollar impact)
5. Thesis status: CONFIRM, CHALLENGE, or NEUTRAL with evidence
6. Action recommendation with conviction level: HIGH, MEDIUM, or LOW

Numbers over narrative. Tables over paragraphs. Financial shorthand always
(DCF, ROIC, FCF yield, EV/EBITDA, NTM, TTM, HBM, TAM, SBC -- never define
these). Bad news stated directly with numbers first. Empty sections skipped,
not padded. Clear recommendations, not menus of options. Expert level; never
explain basic concepts.

All analytical reports include a Confidence Rating: HIGH, MEDIUM, or LOW.
After completing research or analysis, append to relevant wiki files. Wiki
files: Behavioral Guidelines Rule 3 in effect -- never overwrite.

## File conventions (kepano + Okhlopkov)

- Markdown only. Prefer `[[wikilinks]]` for navigation over paths.
- Keep notes under ~150 lines; split with `[[links]]` when longer.
  **Exception:** `Atlas/sources/*/ref-*.md` reference docs are deliberately
  comprehensive and exempt.
- YAML frontmatter: plural list keys (`tags:`, `aliases:`, `categories:`);
  ISO dates (`YYYY-MM-DD`). Full schema below.
- Structured views: **always use Bases (`.base`), never Dataview**.
- **Tasks:** use the obsidian-tasks plugin for cross-file checkbox roll-up;
  `/tasks` is a thin wrapper over its query syntax.
- Skills: progressive disclosure. Main `SKILL.md` aspirationally <= 263 lines,
  but institutional-grade skills with multi-phase workflows preserve full
  content inline; the audit's X2 classifier fires HARD DRIFT only above 900
  lines. Details may split into one-level-deep `ref-*.md` files when content
  is genuinely modular. "The context window is a public good."

## Where things go (ACE + AgriciDaniel routing)

- **Raw voice / clippings / meetings** -> `.raw/{voice,clips,meetings}/`.
  **Never edit `.raw/`.** PreToolUse hook blocks writes.
- **Timeless concepts (human-authored)** -> `Atlas/concepts/<domain>/`.
  - `Atlas/concepts/investing/theses/` -- your thesis essays (demo:
    [[thesis-orbital-compute]]; authoring template `_templates/thesis.md`)
  - `Atlas/concepts/investing/` -- [[doctrine.template]] (copy, fill
    USER_SET values, ratify), watchlist, macro outlook, research log
- **People** -> `Atlas/people/`.
- **External sources** (reference docs, books, papers) -> `Atlas/sources/<domain>/`.
- **Maps of Content** -> `Atlas/_MOCs/` (one per domain; `knowledge-moc.md`
  is the index of indexes).
- **Daily state** -> `Calendar/daily/YYYY-MM-DD.md` (auto-created by the
  SessionStart hook; 9-section schema below).
- **Decisions, briefings, session log** -> `Calendar/decisions/`:
  `decision-log.md` (append-only), `sessions-log.md` (append-only),
  `briefings/briefing-YYYY-MM-DD.md` (from `/brief`).
- **Active deadline-bound work** -> `Efforts/<slug>/`.
- **Agent-maintained LLM-wiki (AgriciDaniel)** -> `wiki/`:
  - `wiki/hot.md` -- SessionStart/Stop cache (highest-leverage continuity
    mechanism; schema `hot-md-v2`, validated by `tools/hot-md-check.py`)
  - `wiki/entities/tickers/<TICKER>.md` -- agent-maintained ticker entities
    (UPPER filenames); `wiki/entities/companies/<Name>.md` (TitleCase)
  - `wiki/research/{prompts,dumps,challenges,sparks}/` -- agent research
  - `wiki/investing/{analyses,snapshots,calibration-monitor.md}` -- `/invest`
    + `/networth` outputs + the prediction-scoring call log
  - `wiki/insight-stream.md` -- append-only cross-domain patterns
  - `wiki/maintenance/` -- `/vault` + `/telemetry` reports
  - `wiki/playbooks/` -- `/consolidate` outputs
- **Private / sensitive** -> `private/`. **Never write here.** Hook-blocked.

**Atlas vs wiki test:** if the skill writes it, `wiki/` (or `Efforts/`). If a
human writes it, `Atlas/`. No exceptions without explicit user confirmation.

## Vault Governance

### Prevention architecture

The vault enforces a **95/100 honest floor invariant** via tier-weighted
scoring (GATE / HARD DRIFT / SOFT DRIFT) backed by mechanical write-time
gates. GATE-class issues (broken wikilinks, missing frontmatter on new
wiki/Calendar/Efforts files, forbidden frontmatter fields, template drift)
block at PreToolUse/PostToolUse before auto-commit; if any GATE finding ever
surfaces in audit, the score hard-caps at 90 to make hook-bypass visible.

- `tools/pre-write-validator.py` -- PreToolUse: simulates the post-edit
  content in a tmp file, runs `vault-audit.py --scope --json`, exits 2 to
  BLOCK the write before disk mutation (CAT-3: block-before-write).
- `tools/wikilink-check.py` + `tools/frontmatter-check.py` +
  `tools/orphan-check.py` -- PostToolUse validators (CAT-2).
- `.claude/hooks/auto-commit.sh` -- refuses commits with gate findings
  (CAT-1 backstop); suppressed during atomic multi-file skill writes by the
  F11 flag (`.claude/state/auto-commit-disabled`).
- `tools/vault-audit.py` -- 12 classifiers (3 GATE + 4 HARD DRIFT + 5 SOFT DRIFT); `--scope`,
  `--changed-only`, `--json`; tier-weighted score (GATE -5/cap-10 + 90-cap on
  any gate finding; HARD DRIFT -1/cap-5; SOFT DRIFT advisory).
- `tools/vault-score-check.py` -- SessionStart injects the current score.
- `tools/test-prevention-arch.sh` -- T1-T38 adversarial test harness for the
  whole prevention stack. Run it after modifying any hook or validator.
- Bypasses (`CLAUDE_VAULT_BYPASS_VALIDATOR=1`, `CLAUDE_VAULT_LAX_ORPHAN=1`)
  are logged to `.claude/state/bypasses-<date>.log` for retrospective audit.
- Hooks MUST NOT invoke `claude` directly (infinite-loop risk: the spawned
  session inherits the same hook chain).

### Frontmatter schema (canonical)

```yaml
---
aliases: []                      # plural list, may be empty
categories: [<axis>]             # REQUIRED. Plural list. Primary organizing axis.
type: <subtype>                  # OPTIONAL. Only when category has genuine subtypes.
tags: []                         # plural. topical/ticker/company/thesis. NO domain/* or type/*
status: active                   # enum: active | paused | done | dropped | stub | deprecated | draft | complete | stale
created: YYYY-MM-DD
updated: YYYY-MM-DD
related: []                      # wikilinks to connected notes (house-style)
---
```

**Not in schema:** `domain:`. Stripped unconditionally; skills filter by path.

### Category vocabulary

| `categories:` | Subtypes (`type:`) | Canonical path |
|---|---|---|
| `[concepts]` | optional: thesis \| playbook \| strategy | `Atlas/concepts/` |
| `[sources]` | book \| paper \| article \| reference | `Atlas/sources/` |
| `[people]` | profile \| stakeholder | `Atlas/people/` |
| `[moc]` | -- | `Atlas/_MOCs/` |
| `[daily]` | -- | `Calendar/daily/` |
| `[decisions]` | briefing \| session-log \| decision-log \| decision | `Calendar/decisions/` |
| `[efforts]` | index \| tracker \| tasks \| ideas \| output \| analysis \| operational \| research | `Efforts/<slug>/` |
| `[entity]` | ticker \| company | `wiki/entities/` |
| `[wiki]` | analysis \| research \| challenge \| spark \| prompt \| synthesis \| snapshot \| ingest \| report | `wiki/` (non-entity) |
| `[meta]` | config \| rule | CLAUDE.md |

### Tag taxonomy

Discovery signals. Do NOT duplicate frontmatter fields.
- `topic/*` -- primary discovery (lowercase-kebab)
- `ticker/*` -- UPPER (`ticker/NVDA`)
- `company/*` -- lowercase-kebab
- `thesis/*` -- lowercase-kebab (e.g. `thesis/orbital-compute`)
- **Forbidden:** `domain/*`, `type/*`

### Linking rules

- Internal: `[[wikilinks]]`, resolved by filename. External: `[text](https://...)`.
- Every file has a `related:` field. Daily notes include `## Cross-References`.
- MOCs enumerate every file in their domain (target 100%).
- Entity notes accumulate backlinks -- don't manually maintain incoming lists.

### Archival rules

- Research outputs (`wiki/research/`): dated records, not maintained after
  insight extraction.
- Analyses: new-analysis = new-file, never overwrite. Same-day collision ->
  `-HHMM` suffix.
- Daily notes: never archived, continuous timeline.

### Daily note schema (9 sections)

`Calendar/daily/YYYY-MM-DD.md`, auto-created by the SessionStart hook:
1. `## Market Pulse` -- `/brief` fills
2. `## Observations` -- free-form human-signal notes
3. `## Decisions` -- table: Domain | Decision | Why
4. `## Commitments` -- checkboxes; unchecked items carry forward via hook
5. `## Insights` -- cross-domain patterns
6. `## Sessions Run` -- one line per session
7. `## Cross-References` -- wikilinks to entities/skills/files touched
8. `## Tasks` -- open items
9. `## Log` -- raw prompts from the UserPromptSubmit hook

### Sessions-log + decision-log schemas

`Calendar/decisions/sessions-log.md`: append-only; one entry per session with
Domain, Skills invoked, Decisions ratified, Methodology learnings, Follow-ups,
Insights, Session boundary (commit range), Confidence/Model/Sources fields.

`Calendar/decisions/decision-log.md`: append-only pipe table:

```
| Date | Domain | Decision | Reversibility | Stakes | Confidence | Review trigger |
```

Reversibility: REVERSIBLE | NEAR-IRREVERSIBLE | ONE-WAY. Confidence carries a
calibrated % (e.g., "HIGH 80%"). `/decide` is the canonical append path.

### ASCII Pattern 22

All new agent-written content (commit bodies, skill outputs, JSON, log rows,
daily appends) MUST be ASCII-clean. Byte-scan gate at each `git commit`; any
byte > 127 halts the commit. Canonical substitutions: em-dash -> `--`,
en-dash -> `-`, curly quotes -> straight, `->` for arrows, `<=`/`>=` for
inequality glyphs, `...` for ellipsis, `x` for multiplication, `+/-` for
plus-minus, ` deg` for degrees, regular space for NBSP.

## Prediction scoring + calibration loop

Every `/invest` verdict appends a row to `wiki/investing/calibration-monitor.md`
(date, ticker, rating, shadow rating, conviction %, R/R, topology). Offline:
- `tools/score-outcomes.py` backfills realized 1/3/6-month returns and
  computes rolling Brier scores (new-logic vs shadow-logic, pooled AND
  topology-stratified), surfacing a pre-committed rollback trigger.
- `tools/reconcile-orders.py` cross-checks broker fills against decision-log
  records -- a fill with no decision record is, by definition, the FOMO
  pattern the architecture exists to catch.
- `/spark` scores its own falsifiable predictions (vault-observable tests)
  and feeds a 2x-weighted calibration component.

## Semantic retrieval (substrate)

Local HNSW vector index over `wiki/` + `Calendar/` (bge-base-en-v1.5 ONNX,
dim 768), living OUT-OF-TREE at `~/.vault-substrate/`. Setup + scripts ship
in this repo's `substrate/` directory. Wired via:
- UserPromptSubmit hook `semantic-context-inject.py` -- injects top-5 chunks
  above similarity 0.6 (suppressed for skills that do their own Phase 0).
- PostToolUse `reindex-debounce.py` + scheduler-driven `reindex-runner.mjs`
  -- debounced incremental reindex with lockfile + atomic swap.
- Phase 0 skill-level retrieval (`query-skill.mjs`) in `/brief` `/invest`
  `/spark` `/decide` `/challenge`. Atlas/ is NOT indexed -- read refs directly.

## Topology & Data Doctrine

- Skills with Dynamic-Workflow worker contracts (/invest, /spark) detect
  topology at runtime; the sequential spine is the universal fallback. No
  skill conditions behavior on model identity; orchestrator_model + topology
  are logged passively on every rated output.
- Fan-out concurrency <= 6; budgets via `<SKILL>_DW_TOKEN_BUDGET` env vars;
  adversarial verification wave per skill spec (4-lens, fail-closed).
- Provenance: every quantitative claim written to the vault carries `prov:`
  (mcp:* > script:* > web:*).
- Live-positions rule: share counts come from the broker's read-only MCP at
  run time; doctrine threshold math anchors to regular_market_close; the
  `private/` files are the interpretation layer, not the count source.

## Preferred Financial Data Sources

stockanalysis.com, sec.gov/cgi-bin/browse-edgar, cnbc.com, reuters.com,
etf.com, fred.stlouisfed.org, macroaxis.com, companiesmarketcap.com,
coinmarketcap.com, company IR sites, dataroma.com (renowned-investor 13F,
Q+45d), capitoltrades.com (congressional STOCK Act disclosures),
openinsider.com (Form 4 with 10b5-1 filter; use curl with User-Agent).
Extended-hours pricing via yfinance `prepost=True` (`tools/fetch-prices.py`).

**Structured-data MCP tier (read-only local-stdio):** FRED (macro series),
EDGAR/edgartools (XBRL financials + filing provenance), OpenInsider
(cluster buys / Form 4 / short interest), plus an optional read-only broker
MCP for live positions. Mutating broker order tools are mechanically denied
in `.claude/settings.json` (`permissions.deny`).

## Blocked Domains (paywalled/bot-blocked -- do not fetch)

bloomberg.com, investopedia.com, macrotrends.net, fintel.io, wsj.com, ft.com,
barrons.com, morningstar.com, seekingalpha.com, statista.com, tipranks.com,
gurufocus.com, simplywall.st, businessquant.com, spglobal.com, factset.com,
pitchbook.com, capitaliq.com, finance.yahoo.com, marketbeat.com, fool.com,
zacks.com, tradingview.com

## Tool Use Rules

- WebFetch SSL failures: fall back to `curl -sk [url]` via Bash. Don't retry
  WebFetch more than once.
- Bash paths: Unix-style relative to the vault root.

## Permissions

Never ask permission to: fetch web pages; read any file in the vault; write
to allowed paths (Atlas excepted -- confirm before human-layer writes); run
bash commands. Proceed autonomously unless the action is destructive outside
the vault.

**Path guards (PreToolUse hook):** never write `.raw/`, `private/`,
`finance/`, `credentials/`. Atlas writes require confirmation (soft rule).
Never run destructive bash without confirmation. Never `git push` to main --
session branch + PR-on-Stop only.

**MCP guards:** never call broker order tools (mechanically denied; second
layer requires a literal `EXECUTE ORDER` phrase in the user's latest message
even if the deny were lifted). Never co-load an email connector with
browser/web-fetch tools in one session (lethal-trifecta isolation).

## Write discipline (Evgeny hybrid)

- On first meaningful write in a session: `git switch -c claude/<YYYYMMDD-HHMM>`
  (hook-enforced by `session-branch.sh`).
- PostToolUse auto-commit on the session branch, prefix `agent: <verb> <scope>`.
- **Never push to main.** The Stop hook runs the audit gate and (if a remote
  is configured) opens a PR; the human reviews and merges.
- **F11 atomic-commit suppression** (`.claude/state/auto-commit-disabled`):
  set once per skill invocation before the first write (Phase C), cleared
  post-commit; multi-skill cascades hold one F11 window via
  `tools/lib/f11_orchestrator.py` (`cascade_role="parent"|"child"`).
- F14: stage by named pathspec only (never `git add -A`), preceded by the
  audit gate (gate_count 0 AND score >= 95). F17: Co-Authored-By suppressed.

## Session Protocol

### On Session Start
The SessionStart hook injects `wiki/hot.md` head, the MOC listing, vault
score, and `git status`; creates today's daily note (9 sections) if missing.

### During Session
- On completing analysis / decisions / insights: append a one-line entry to
  today's daily note under the appropriate section, format `- [HH:MM] <action>`.
- The UserPromptSubmit hook auto-appends raw prompts to `## Log`.
- PostToolUse auto-commits on the session branch.

### On Session End (significant work)
1. Update `wiki/hot.md`: replace the Last Session block, update Pending Items
   and Active Context (schema enforced by `hot-md-check.py`).
2. Append a structured entry to `Calendar/decisions/sessions-log.md`.
3. Update entity notes for any tickers/companies analyzed.
4. Session end is user-invoked via `/retro` -- the Stop hook gates on audit
   score but does not automate session-end.

## Observability

- **Post-hoc:** `/telemetry` + `tools/telemetry_analyzer.py` read the
  `.claude/state/*.jsonl` sinks (SubagentStart/Stop, PostToolUseFailure,
  PostCompact) into a derived SQLite index -- failure clusters, orphan pairs,
  duration outliers.
- **Live (optional):** claudewatch (github.com/blackwell-systems/claudewatch,
  MIT/Apache-2.0) as an MCP-only install -- ~23 read-only metric tools over
  an out-of-tree transcript DB. Install runbook: `tools/INSTALL-CLAUDEWATCH.md`.

## Active Skills (22)

| Skill | What it does | Writes to |
|---|---|---|
| `/brief` | Institutional-grade morning briefing (16-phase, PDB-style BLUF, thesis status board, meta.json sidecar, Brier continuity) | `Calendar/decisions/briefings/` |
| `/invest` | Investment analysis: dual-topology research waves, forensic scoring, institutional positioning, verdict spine, adversarial verify, calibration row | `wiki/investing/analyses/` |
| `/networth` | Live portfolio snapshot (broker MCP -> script -> fallback tiers; extended-hours aware) | `wiki/investing/snapshots/` |
| `/challenge` | Thesis stress test (bear-case-first evidence discipline) | `wiki/research/challenges/` |
| `/decide` | Structured decision framework: first principles, pre-mortem, reversibility, smallest-possible-bet | `Calendar/decisions/` |
| `/deep` | Deep Research prompt generator for claude.ai Research mode (target_path contract feeds /enrich) | `wiki/research/prompts/` |
| `/spark` | Cross-domain pattern recognition: 9-class taxonomy, dual topology, 4-lens adversarial verify, falsifiable-prediction scoring | `wiki/research/sparks/` |
| `/enrich` | Onboard a document with canonical frontmatter + symmetric back-links (byte-exact body, sha256-verified) | varies by placement |
| `/ingest` | Extract claims from a source, distribute across the entity graph with contradiction tiers | `wiki/entities/`, `wiki/research/` |
| `/retro` | Session retrospective: 4-file atomic (sessions-log, decision-log, daily, hot.md) | `Calendar/decisions/` |
| `/vault` | Vault maintenance: 9-classifier audit, stats, daily, repair, refresh | `wiki/maintenance/` |
| `/consolidate` | Mine the operational record into durable playbooks | `wiki/playbooks/` |
| `/telemetry` | Analyze hook telemetry sinks (failure clusters, orphan pairs) | `wiki/maintenance/` |
| `/career` | Job-search pipeline: scan, evaluate, packets, tracker | `Efforts/career-search/` |
| `/health` | 6-mode health advisory (GRADE evidence tiers, interaction matrices) | `Efforts/health-protocol/` |
| `/golf` | Practice plans, swing research, drills | `Efforts/golf-practice/` |
| `/corpus` | Mass-document analysis pipeline (wave-based extraction + 7-pass synthesis) | per-corpus workspace |
| `/create-skill` | Scaffold new skills with progressive disclosure | `.claude/skills/` |
| `/tasks` | Cross-file task roll-up (obsidian-tasks syntax) | reads-only |
| `/caveman` | Ultra-compressed output mode | none |
| `/diagnose` | Disciplined bug/perf diagnosis loop | varies |
| `/tdd` | Red-green-refactor TDD loop | code |

## Workflow layer commitment

This vault adopts **AgriciDaniel's Karpathy LLM-wiki pattern** (hot.md +
wiki/entities + SessionStart/Stop hooks). One theory. The Dynamic-Workflow
layer (`.claude/workflows/*.js`) adds deterministic fan-out orchestration for
/invest and /spark with adversarial verification waves; the sequential spine
remains the universal fallback.

## Local import (create your own)

Once you create `CLAUDE.local.md`, add an `@`-import line for it here -- the
import is deliberately not live in the public edition so a fresh clone does
not error on a missing file.

## Dual-engine note

This vault is dual-engine capable. Codex CLI mirror via `tools/sync-skills.py`
(skills -> `.agents/skills/`), `tools/gen-codex-agents.py` (agents ->
`.codex/agents/*.toml`), `tools/gen-codex-config.py` (hooks -> `.codex/config.toml`).
See `docs/CODEX-COMPATIBILITY.md` for installation, model mapping, hook
differences, troubleshooting.
