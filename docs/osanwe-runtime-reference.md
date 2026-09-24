---
aliases: [osanwe-runtime-reference]
categories: [meta]
type: reference
tags: [topic/vault-architecture, topic/claude-code]
status: active
created: 2026-06-28
updated: 2026-09-21
related: ["[[knowledge-moc]]", "vault-prevention-architecture-2026-04-27"]
---


## Blocked financial sources

Preserved source policy from the pre-recovery universal router. These domains
are excluded from retrieval even if a historical grading example names them.

<!-- blocked-domains:start -->
bloomberg.com, investopedia.com, macrotrends.net, fintel.io, wsj.com, ft.com,
barrons.com, morningstar.com, seekingalpha.com, statista.com, tipranks.com,
gurufocus.com, simplywall.st, businessquant.com, spglobal.com, factset.com,
pitchbook.com, capitaliq.com, finance.yahoo.com, marketbeat.com, fool.com,
zacks.com, tradingview.com.
<!-- blocked-domains:end -->

## Current scope (2026-09-13)

The existing financial dataset registry now exposes document admission via
`python tools/pit/dataset_registry.py --documents-manifest`. It admits exact
reviewed source spans with applicability, version, origin, computation and reuse
evidence. Unknown/mixed material is excluded before indexing. The metadata-only
inventory is discovery evidence and cannot supply text or approve itself.

The active external owners remain
`~/.vault-substrate/index-vault.mjs`, `qsearch.mjs`,
`reindex-runner.mjs`, and `vault-search/server.py`.
`tools/retrieval-core.mjs` owns immutable generation construction/validation;
`retrieval-provider.mjs` at the external substrate owns native embedding behavior.
Each query binds lexical records, metadata, model identity and vectors to the same
manifest. Its default lexical path runs without loading embeddings. Hybrid stays
explicit experimental; old preview benchmarks are historical development only.

`node ~/.vault-substrate/reindex-runner.mjs --inspect` is read-only
and returns passed, stale or unavailable with generation/dependency identity.
The existing scheduled reindex owner detects edits from all harnesses. It preserves
missed-slot history, bounded execution and one current catch-up. checkall adds
deterministic corpus/index controls; monitoring schedules no inference or account
polling. A passing index check proves the admitted subset, not the whole vault.
External source rollback bytes and current validation receipts are retained with
the dated financial-corpus release. Older already-running MCP processes need a
separate current-process observation before their state can be upgraded.

Root AGENTS.md is the single universal contract and no CLAUDE.md is tracked; a per-machine CLAUDE.local.md imports it with the first line `@AGENTS.md`. This file
provides adapter details and reference policies. Historical model/tier labels and
mechanism descriptions below are not permission rules or current runtime receipts.
Select capabilities by task and risk; preserve existing local-lane ratification.
Financial semantics and missing-data handling: docs/financial-analysis-contract.md.
Never follow an old private-file holdings fallback or model-specific exemption.

Finance/Data handoffs are owned by [[finance-data-integration]] and the canonical
finance-data skill. The installed Finances/Data metadata receipt is distinct from
live account verification. Reuse the source-bearing stateless packet and existing
financial model owners; compile the reviewed portable subset with
`tools/package-finance-data.py`. No imported copy receives implicit account,
execution, storage or full-vault permissions. The dated integration report records
the actual local Data runtime build and portable replay acceptance.

Current host capability evidence: HOST-CAPABILITIES-2026-09-13. Companion
report review is owned by `tools/fis/report_review.py` through the existing
workbench. Hosted reasoning evaluation is documented in [[REASONING-EVALUATOR]];
local development scoring is not independent custody. Runtime observation is
owned by `tools/runtime-health.py` and the existing scheduled-job manifest.
Structured checkall results distinguish failed, stale and unavailable evidence.
An expired local observation cannot establish current host health or successful
notification delivery. Current program acceptance remains in STATE.

The September 13 runtime repair uses `tools/scheduled-job.py` as a waiting,
bounded wrapper for nightly health, weekly calibration and vault reindexing.
It verifies required fresh artifacts in addition to exit codes. Reindexing uses
an approved source traversal boundary, a shared process-owned lock and a bounded
long-build lock heartbeat; exclusions occur before text ingestion. Exact task XML,
missed-run snapshots, failed attempts and safe-build receipts are preserved in
the mission checkpoint. A successful no-op poll is distinct from a fresh rebuild.
Downstream retrieval answers and old caches need their own validation.

The Codex heartbeat `osanwe-daily-research-health` runs at 08:00
US/Eastern, with deeper Sunday deterministic checks. It records current
scheduled opportunities, one catch-up after resume, missed intervals, incidents,
recovery and notification status separately. It performs no model research,
evaluation submissions or personal-account pulls. Seven actual scheduled cycles
including Sunday are still required; manual tests do not count. Readiness expires
after 25 hours. An offline machine cannot establish current health or delivery;
any remote missing-heartbeat observer remains a separate unverified capability.


# Osanwe Runtime Reference (detail relocated from the root contract)

> Relocated from the root contract on 2026-06-28 (best-practices audit R4) to keep the
> always-loaded contract lean. AGENTS.md retains the operational summary of each item
> below and points here. (The contract lived in CLAUDE.md, latterly as a byte-identical mirror of AGENTS.md, until CLAUDE.md became a one-line import stub on 2026-09-22; the stub was removed on 2026-09-24 and the import moved into the per-machine CLAUDE.local.md.)
> Nothing was dropped -- this is the full detail, Read on demand. These mechanisms are
> MECHANICALLY ENFORCED BY HOOKS regardless of whether this prose is in context, so relocating
> the documentation does not change runtime behavior.

## Vault Governance -- Prevention architecture (full)

### Prevention architecture (2026-04-27, post-100->35 regression)

The vault enforces a **95/100 honest floor invariant** via tier-weighted scoring (GATE / HARD DRIFT / SOFT DRIFT) backed by mechanical write-time gates. GATE-class issues (broken wikilinks, missing frontmatter on new wiki/Calendar/Efforts files, forbidden frontmatter fields, template-drift) are blocked at PostToolUse before auto-commit; if any GATE finding ever surfaces in audit, the score is hard-capped at 90 to make hook-bypass visible. SOFT DRIFT (deprecated-skill mentions, daily-continuity gaps, MOC-coverage thinness) surfaces in audit + FOLLOWUPS:skills with zero score impact. Pattern modeled on SonarQube quality-gates + Vault Physician + CodeClimate maintainability ratio.

- **`tools/wikilink-check.py`** -- PostToolUse hook on Write/Edit/MultiEdit. Runs `vault-audit.py --scope <file>`; exits 2 with detailed broken-target list if any present.
- **`tools/frontmatter-check.py`** -- PostToolUse hook validating canonical schema (categories list, ISO dates, no `domain:`, no `domain/*` or `type/*` tag namespaces, canonical status enum).
- **`tools/orphan-check.py`** -- PostToolUse hook on Write only; soft-blocks new-file-create with 0 inbound wikilinks (bypass: `CLAUDE_VAULT_LAX_ORPHAN=1`).
- **`tools/pre-write-validator.py`** -- PreToolUse hook on Write/Edit/MultiEdit. Simulates post-edit content via tmp file, runs `vault-audit.py --scope --json`, exits 2 to BLOCK the tool call before disk mutation. Closes the catastrophic race condition where PostToolUse exit-2 could not roll back the write. True block-before-write per ref-claude-code-mastery sec 4. Honors EXEMPT_PATHS (AGENTS.md, docs/VAULT-HANDOFF-V16.md, etc.) to avoid path-remap self-blocking.
- **`tools/vault-audit.py` v2.2** -- code-fence-aware extraction; MEMORY_PREFIXES exemption; bash double-bracket detection; `--scope`, `--changed-only`, `--quick`, `--json` CLI flags; tier-weighted score block (GATE -5/cap-10, HARD DRIFT -1/cap-5, SOFT DRIFT 0).
- **`tools/vault-score-check.py`** -- SessionStart injects current vault score into Claude's context; warns when below floor.
- **`tools/hot-md-check.py`** -- PostToolUse hook on Write/Edit/MultiEdit; validates `wiki/hot.md` schema_version=hot-md-v2, section count <=3 Last Session blocks, Pending Items lifecycle, Active Context boundary doctrine. Canonical schema at [[ref-hot-md-schema]]. Bypass: `CLAUDE_HOT_MD_BYPASS_CHECK=1`. (Note: as of 2026-06-27 audit R1 this hook early-exits when the written file is not wiki/hot.md.)
- **`tools/hot-md-emit-smart.py`** -- SessionStart helper; when hot.md exceeds 8KB threshold, emits priority-ordered subset (frontmatter + current Last Session + Active Context + Pending Items summary) skipping bulk archive blocks (which live in sessions-log).
- **`.claude/hooks/stop-pr-and-audit.sh`** -- Stop hook runs audit; blocks PR creation via `{"continue": true, "reason": ...}` JSON if any GATE finding present.
- **Bypass mechanisms:** `CLAUDE_VAULT_BYPASS_VALIDATOR=1` (wikilink/frontmatter), `CLAUDE_VAULT_LAX_ORPHAN=1` (orphan-on-create) -- both logged to `.claude/state/bypasses-<date>.log` for retrospective audit.
- **Score formula:** GATE per-finding -5 (cap -10, gate-breach hard-cap 90); HARD DRIFT per-finding -1 (cap -5); SOFT DRIFT 0 (advisory). Trend +/-2 suppressed when raw < 97. Floor: 95/100 in steady state.
- **Reference:** `wiki/research/vault-prevention-architecture-2026-04-27.md` (Plan #1 root-cause); Plan #2 95-floor revision.
- **Hook recursion constraint:** hooks MUST NOT invoke `claude` directly (would infinite-loop because the spawned session inherits the same hook chain). If a future hook needs to spawn Claude, pass `--settings no-hooks.json` with `{"disableAllHooks": true}` per ref-claude-code-mastery sec 4 anti-pattern. All current hooks use pure-Python or shell-only paths -- no recursion possible.
- **Recovery point:** git tag `prevention-arch-v3` at commit `6550d54` (convention-based immutability; unsigned; reflog protects ~90 days locally). Future tags `prevention-arch-vN` mark subsequent ratified states. Trust model: solo-developer convention, not cryptographically enforced. To upgrade to GPG-signed tags: `git config --global user.signingkey <key>` + `git tag -s prevention-arch-v<N> -m "..."` -- requires GPG key configured.
- **PostToolUse hook chain semantics:** validators (wikilink-check + frontmatter-check + orphan-check) run sequentially before bump-updated.sh and auto-commit.sh per observed harness behavior. The auto-commit GATE backstop (auto-commit.sh runs `vault-audit.py --scope --json` and refuses commits with gate_count > 0) provides defense-in-depth even if the harness ever changed to parallel execution.

## Growth + Archival Thresholds (X67, tenfold-t10 2026-07-05)

The vault grows monotonically -- entity notes, analyses, research dumps, daily notes, and dated snapshots accumulate and never shrink. A naive staleness metric (any file with `updated:` > 30d = drift) therefore only ever RISES, measuring vault growth rather than decay: the honesty target "uncapped HARD falling to <60" would be structurally unreachable. Two thresholds keep the growth honest without a new sweeper organ (30-day built-then-dead gate: this is documentation + an existing-classifier refinement, not a new mechanism):

- **Staleness horizon (30d)** -- `STALE_THRESHOLD_DAYS` in `tools/vault-audit.py`. A living file un-touched past this is a real-decay HARD finding.
- **Archival-by-design exclusion (X37/X72)** -- `ARCHIVAL_STALE_EXEMPT_PREFIXES` in `tools/vault-audit.py`. Paths that are dated-and-frozen by doctrine (wiki/research, wiki/investing/analyses + snapshots, Calendar/daily + weekly + briefings + dated decision records, wiki/maintenance, `_archive/`, dated archival paths) are EXCLUDED from the stale HARD count -- a stale `updated:` there is *correct*, not decay. The count is reported separately (audit `honesty.archival_exempt_stale` + the "Stale files (archival-exempt)" summary row) so the exclusion is auditable and can never silently swallow real decay (X72: living paths -- Atlas refs, MOCs, entity notes, trackers, playbooks -- stay counted; the 2026-06-22 remediation package confirmed those decays are real, not archival).
- **Archival trigger (policy, >=2 quarters ~= 180d)** -- a `wiki/investing/analyses/*.md` older than ~2 quarters is an archival candidate: it is superseded by later new-file-per-run analyses of the same ticker and no longer thesis-current. Disposition when a domain sweep touches it: leave in place (archival exclusion already keeps it out of the HARD count) OR, if the directory grows unwieldy, move to `wiki/investing/analyses/_archive/` leaving a one-line pointer stub. No autonomous mover is scheduled -- archival is opportunistic on domain-maintenance passes, consistent with the no-standing-sweeper doctrine. The same >=2-quarter horizon applies to `wiki/research/dumps` and dated `snapshots`.
- **Honesty metric (uncapped HARD)** -- the audit's `honesty.uncapped_hard_real_decay` (orphans + living-stale + session-gaps + skill-length) is the tracked trend; the -5 HARD penalty cap conceals it in the score, so it is surfaced explicitly. tenfold-t10 rebased it to the real-decay basis (~175 at close) from the archival-inclusive ~368 raw baseline. Target: falling via ongoing living-file hygiene (entity-note + Atlas-ref refresh), not via widening the exclusion set.

## Sessions-log schema (8 canonical fields per row)

`Calendar/decisions/sessions-log.md` is a single Markdown table; each row is one session entry. Canonical schema (pipe-delimited):

```
| Date | Topic | Outcome | Files Created/Updated |
```

The `Outcome` cell is an inline-prose synthesis covering 8 fields (no sub-headers; comma/period-separated):
1. **Domain** -- primary classification (investing | meta/skill-infrastructure | etc.)
2. **Skills invoked** -- skill names with versions where applicable
3. **Decisions ratified** -- count + sentinel for decision-log entries (e.g., "2 to decision-log")
4. **Methodology learnings** -- pattern-level insights (NEW vs RE-CONFIRM)
5. **Follow-ups** -- specific actionable items with imperative voice + trigger condition
6. **Insights** -- cross-domain observations
7. **Session boundary** -- commit-range lower-bound SHA + commit count + paths modified
8. **Confidence/Conviction/Model/Sources_count** -- meta fields

The `Files Created/Updated` cell is pipe-separated `Created: <paths>. Modified: <paths>.` entries with wikilinks where they exist. (The `/retro` skill is the canonical append path and embeds this schema.)

## Table-ledger append recovery

`tools/gen-ledger-views.py` ingests newly appended EOD and insight rows only
against independently preserved pre-append bytes and their recorded SHA256:
`--ledger eod --ingest --apply --ingest-baseline <checkpoint-file>
--ingest-baseline-sha256 <recorded-digest>` (use `insights` for that ledger).
Capture those bytes and the digest before appending; do not manufacture a shorter
baseline after a failure. An unchanged table may use the existing no-op ingest.
Heading-ledger ingestion and historical verification retain their existing form.

The table path verifies the physical prefix, original node identities and bodies,
and every expected suffix before exclusively creating new nodes. Missing original
nodes, altered prefixes, unknown nodes, changed suffix bytes and sequence holes
are refused. Exact already-created suffix nodes can be resumed without rewriting
history. The inherited node scaffold includes the current `updated` date, so an
interruption resumed on a later date may safely refuse; this is an explicit
recovery limit, not permission to backdate metadata or weaken collision checks.
The original failure and current scoped recovery evidence are retained with the
September 13 AVGO research record. This mechanism does not attest independent
custody or protect evaluation credits; those have their own ledger owner.

## Decision-log schema (pipe-table; append-only)

`Calendar/decisions/decision-log.md` is a single Markdown table; each row is one ratified decision. Canonical schema:

```
| Date | Domain | Decision | Reversibility | Stakes | Confidence | Review trigger |
```

- **Reversibility**: REVERSIBLE | NEAR-IRREVERSIBLE | ONE-WAY
- **Stakes**: dollar-impact OR scope keyword (vault-architecture | thesis-status | life-change)
- **Confidence**: HIGH | MEDIUM | LOW + calibrated % (e.g., "HIGH 80%")
- **Review trigger**: specific condition that fires re-evaluation (e.g., "`<TICKER>` Q<n> print", "`<TICKER>` -`<pct>` from $`<price>` stop", "30d post-deploy")

The `/decide` skill is the canonical append path; manual edits permitted only for triggered-review status updates.

## ASCII Pattern 22 enumerated rules (full)

All new content written by the agent (commit bodies, skill output text, JSON outputs, sessions-log rows, decision-log rows, daily-note appends, AGENTS.md edits) MUST be ASCII-clean per Pattern 22. Byte-scan gate fires at each `git commit` boundary; any byte > 127 halts the commit.

Canonical substitutions (apply before commit):

| Source character | UTF-8 bytes | ASCII replacement |
|---|---|---|
| em-dash (E2 80 94) | E2 80 94 | `--` (two ASCII hyphens) |
| en-dash (E2 80 93) | E2 80 93 | `-` (one ASCII hyphen) |
| curly left quote (E2 80 9C) | E2 80 9C | `"` (straight quote) |
| curly right quote (E2 80 9D) | E2 80 9D | `"` (straight quote) |
| curly left apostrophe (E2 80 98) | E2 80 98 | `'` (straight apostrophe) |
| curly right apostrophe (E2 80 99) | E2 80 99 | `'` (straight apostrophe) |
| arrow (E2 86 92) | E2 86 92 | `->` |
| less-or-equal (E2 89 A4) | E2 89 A4 | `<=` |
| greater-or-equal (E2 89 A5) | E2 89 A5 | `>=` |
| ellipsis (E2 80 A6) | E2 80 A6 | `...` |
| Euro (E2 82 AC) | E2 82 AC | `EUR` |
| non-breaking space (NBSP) | C2 A0 | regular space |
| middle dot (C2 B7) | C2 B7 | `-` (bullet marker) |
| degree (C2 B0) | C2 B0 | ` deg` |
| times (C3 97) | C3 97 | `x` |
| plus-minus (C2 B1) | C2 B1 | `+/-` |

Verification snippet (run before commit):

```python
import sys
data = sys.stdin.read()
bad = [(i, c, hex(ord(c))) for i, c in enumerate(data) if ord(c) > 127]
print(f'{len(bad)} non-ASCII chars' if bad else 'ASCII-CLEAN')
```

PowerShell equivalent: `git log --format=%B -1 HEAD | python -c "import sys; data=sys.stdin.read(); bad=[c for c in data if ord(c)>127]; print('NON-ASCII' if bad else 'ASCII-CLEAN')"`

## Reference Documents (full enumeration)

Pre-researched context docs at `Atlas\sources\`. Load relevant ones BEFORE web searches to prime analysis. Knowledge index (read on demand; not globally imported): `Atlas/_MOCs/knowledge-moc.md`.

### Investing
- `Atlas/sources/investing/ref-macro-landscape.md` (6,299w) -- Macro environment, rates, Fed policy
- `Atlas/sources/investing/ref-scoring-models.md` (5,814w) -- Piotroski, Altman Z, Beneish M, DCF frameworks
- `Atlas/sources/investing/ref-etf-evaluation.md` (6,046w) -- ETF analysis framework
- `Atlas/sources/investing/ref-sector-benchmarks.md` (6,633w) -- Sector comparison
- `Atlas/sources/investing/ref-crypto-landscape.md` (6,146w) -- Crypto, theme-beta thesis
- `Atlas/sources/investing/ref-research-insights.md` (763w) -- Cumulative findings
- `Atlas/sources/investing/ref-portfolio-doctrine.md` (1,506w) -- Thesis tracking, invalidation, earnings protocol
- `Atlas/sources/investing/ref-monitoring-rules.md` (1,176w) -- Alert thresholds, briefing architecture
- `Atlas/sources/investing/ref-geopolitical-framework.md` (385w) -- Transmission mapping
- `Atlas/sources/investing/ref-market-calendar.md` (994w) -- FOMC, CPI, earnings, crypto regs
- `Atlas/sources/investing/ref-theme-alpha.md` -- theme-alpha thesis source
- (plus the additional investing refs enumerated in knowledge-moc.md: ai-supply-chain, theme-beta-institutional-crypto, defense-aerospace-space-economy, memory-storage-cycle, ai-power-grid, earnings-playbook, valuation-methodology, factor-lens)

### Cross-domain
- `Atlas/sources/meta/ref-research-methodology.md` (1,861w)
- `Atlas/sources/meta/analysis-depth-standard.md` -- the 6-step analytical spine source
- `Atlas/sources/meta/ref-claude-code-mastery.md` -- load on demand or explicit @-import when needed

## Orchestration economics (measured 2026-08-17; GATE-B gate-b-orchestration-economics-2026-08-17)

**The cost law.** `frontier_cost = cache_read + 12.5*cache_creation + 50*output`,
measured 81.6 / 6.9 / 11.4 on a full `/invest` run. And `cache_read` is the SUM OVER
TURNS of the resident context. So the bill is **turn count x residency**. Bytes
admitted to context are charged once as cache_creation and then re-charged on every
later turn -- which is why "read fewer bytes" is a small lever and "take fewer turns
at a smaller residency" is a large one.

**Where the money is** (all sessions, deduped by message id). Main loop 7,866M
weighted: unattributed session work **69.2%**, invest 11.7%, retro 7.7%, brief 4.3%,
all other skills 7.1%. Subagent fleet 2,038M across 829 dispatches, of which the
exploration/planning apparatus (general-purpose, Explore, Plan, claude, fork) is
**81%** and the entire domain agent fleet is 14%. Per dispatch: general-purpose
4.43M, claude 4.96M, Plan 3.46M vs Explore 1.80M, thesis-critic 1.30M,
claim-distributor 0.79M, price-fetcher 0.60M.

**Measurement.** `python tools/run-share.py` -- per-skill, per-agent, and
unattributed attribution for a session; `--current-context` for the live residency
gate; `--all-sessions` for the system rollup; `--emit-ledger` writes the real
`kind:"local-share"` row. Three traps it exists to avoid, all of which made every
earlier number wrong: subagent turns are NOT in the session transcript (they live in
`<session>/subagents/agent-*.jsonl`; `isSidechain` is always false and claudewatch
shares the blind spot, so it is not an independent cross-check); usage rows must be
deduped by message id (streaming repeats the same usage object -- 12-50x inflation);
and the four token classes differ ~50x in price, so they are never summed.

**No share metric.** `frontier/(frontier+worker)` mixes currencies (it excluded
prompt re-read on the frontier side while including the local model's re-evaluated
prompt on the worker side) and is MAXIMISED BY WASTE -- adding useless worker legs
lowers it while making the run more expensive. Worker tokens are reported standalone
with their convention printed. Report the cost law's own units instead: weighted
cost, turns, mean resident context, and weighted-per-VERIFIED-claim.

**The relay lane is not a token lever.** Driving 8 relay legs cost the orchestrator
65 turns -- 37.4% of that run, ~8 turns per leg. Synchronous delegation of work a
one-turn grep already answers is net negative. The lane's value is quality
(containment, grounding, verification) and off-frontier capacity: a SCHEDULED leg
costs the frontier zero turns, which is the shape to reach for.

## Observability (full)

Two complementary layers (claudewatch never writes inside the vault root):

- **Post-hoc -- `/synthesis consolidate` telemetry mode + `tools/telemetry_analyzer.py`:** the standalone `/telemetry` skill was merged into `/consolidate` on 2026-07-06 and `/consolidate` into `/synthesis` on 2026-08-23, so neither skill directory exists any more. It reads the vault's `.claude/state/*.jsonl` sinks (SubagentStart/Stop + PostToolUseFailure + PostCompact) into a derived SQLite index; answers "what failed in the last N days" (orphan pairs, failure clusters, duration outliers). Offline, vault-local.
- **Live -- claudewatch (MCP-only):** a local Go binary (github.com/blackwell-systems/claudewatch, MIT/Apache-2.0) that reads `~/.claude/projects` transcripts into an out-of-tree SQLite DB at `~/.config/claudewatch/claudewatch.db` and exposes 32 MCP tools (`get_drift_signal`, `get_session_dashboard`, `get_project_health`, ...): 31 read plus one session-labelling write, `set_session_project`, counted from `.agents/mcp/servers.json` and confirmed against the live session tool listing on 2026-09-21 so Claude can query its own mid-session metrics; answers "am I drifting right now". Installed 2026-05-25 MCP-ONLY: the global behavioral rules and the blocking PostToolUse hook are DEFERRED -- they would collide with the PostToolUse chain and override the SessionStart protocol. No network, no API keys. Codex parity: N/A (CC-specific binary + MCP). Install/runbook: `tools/INSTALL-CLAUDEWATCH.md`.

## Cross-harness note (2026-08-10 cutover; supersedes the Mission Four dual-engine note)

This vault is cross-harness. `/AGENTS.md` is the single canonical instruction layer for EVERY harness and the only copy of it (Claude Code 2.1.277 and later, Codex CLI, OpenCode, Goose, Crush, Cline and Pi read it natively; because a per-machine CLAUDE.local.md suppresses Claude Code's native read, that file's first line is `@AGENTS.md`, which imports the contract; no CLAUDE.md is tracked). Canon skills live at `.agents/skills/<name>/SKILL.md` (native discovery for the non-Claude harnesses); `.claude/skills/` holds sync-generated derived copies (`python .agents/scripts/sync.py`). MCP configs are generated from the `.agents/mcp/servers.json` registry via `.agents/scripts/gen-mcp-configs.py` (default-refuse for write-capable servers). Per-tier capability + losses: `docs/compatibility.md`; Tier-C local-model primer: `BOOTSTRAP.md` (generated, hash-pinned). One consistency command: `python .agents/scripts/checkall.py`. The Mission Four generator layer (Codex TOML subagent mirror, per-engine detection shims, mirror-direction skill sync) was deleted at the cutover; single-revert restore point is the isolated deletion commit in main history; the retired branch tip is recorded in GIT-RECOVERY-REPORT-2026-09-12.md.

## Preferred Financial Data Sources -- full detail

For a user-requested headless financial acceptance run, use the actual native
binary with an explicit model and effort; inspect runtime model metadata and
retain failures and permission denials. A wrapper name or model self-description
does not establish provider identity. Session-only settings must not repin a
persistent local lane or silently substitute another model. Keep configured
effort distinct from server attestation when the runtime does not expose it.

The 2026-09-12 Opus 5 acceptance used --restricted, a read-only tool set, explicit
selected context, no-session-persistence, hooks/automatic memory disabled and
an empty strict MCP configuration. A synthetic canary verified the file boundary.
This permits repeatable public/synthetic reasoning tests while protecting the
locked evaluator and personal data. It does not test native auto-discovery,
unrestricted hooks, account access or live cross-host plugin execution. Preserve
the baseline, frozen criteria, input hashes and per-case outcomes; label reused
cases as regression and new development cases separately. Exact commands and
evidence are in OPUS5-FINANCE-ACCEPTANCE-2026-09-12.md and its evidence archive.
This explicitly authorized one-off test creates no scheduled lane and does not
change the existing scheduled-lane decisions below.

For the installed 2.1.270 binary, `--max-turns` limits provider round trips;
the successful `num_turns` field counts the initial input plus emitted user
messages, including individual tool results. Parallel tools can make these
counts differ. Declare the counter before inference and meter actual events
with `NativeReviewAttempt.record_turns`; a CLI flag alone is insufficient.
Reserve tool-result capacity as stream tool blocks arrive and terminate on
observed excess. In-flight actions cannot be synchronously revoked, so the
unchanged final-count and process-deadline gates remain mandatory. Schema
corrections consume the same fixed attempt and budget. The original native06
24-turn failure remains WITHHELD despite the diagnosed counter mismatch.
NATIVE-REVIEW-TURN-CONTROLS-2026-09-13.json records ten accounting and five
containment controls against binary SHA-256
fd7f35ec7761195ab5ba4eff423e48a78a7849e78f60d93ec31256cdb1a9ec7e.
These are loopback synthetic-provider mechanics, not subscription inference.
Compact inline evidence may reduce redundant Reads; freeze its byte size,
coverage and source bindings before launch, keeping originals inspectable.

stockanalysis.com, sec.gov/cgi-bin/browse-edgar, cnbc.com, reuters.com, etf.com, fred.stlouisfed.org, macroaxis.com, companiesmarketcap.com, coinmarketcap.com, company IR sites, dataroma.com (renowned-investor 13F aggregation, 65 managers, free no-auth, Q+45d update), capitoltrades.com (congressional STOCK Act trade disclosures, 3-yr history, free), openinsider.com (Form 4 corporate-insider transactions with 10b5-1 filter; cluster-buy detection per ref-investor-frameworks-2026; use curl with User-Agent, not WebFetch). Dataroma + CapitolTrades + OpenInsider integrated into /invest Phase J-bis institutional-positioning workflow per [[ref-investor-frameworks-2026]] (audit 2026-04-28 5th-pass). **Extended-hours pricing** (pre-market 04:00-09:30 ET + after-hours 16:00-20:00 ET) integrated 2026-05-05 via yfinance prepost=True; surfaced in fetch-prices.py + price-fetcher subagent + /brief + /networth (Mission Three; see ref-monitoring-rules "Extended-hours signal thresholds" section); ah_mover signal at `AH_MOVER_THRESHOLD_PCT` env var (default 3.0%); `extended_hours_movers[]` aggregation. /invest dispatch queued for Mission Four-bis; concentration math + trim trigger evaluation REMAIN regular_market_close anchored per ref-portfolio-doctrine doctrine note.

**Structured-data MCP tier (2026-06-05, read-only local-stdio; tools register at session start -- a mid-session `claude mcp add` needs a reload):** FRED (`fred_get_series` macro series -- 10Y/DGS10, CPI, etc.; runs via a node launcher that works around a Windows main-guard bug in `fred-mcp-server@1.0.2`), EDGAR/edgartools (`edgar_company` XBRL financials + `recent_filings` accession_number/CIK provenance -- NOT a literal sec.gov URL), OpenInsider (`cluster_buys` / Form 4 / 13D / short interest) are installed as MCP servers feeding /invest (forensic-scorer + institutional-positioning-scout Tier-0), /brief macro, and /networth. CoinGecko DEFERRED (v6.0.0 routes through a Stainless-hosted remote code-execution sandbox; re-eval via a CoinGecko REST helper, fetch-prices.py-style, for niche tokens the primary quote source does not cover + market-cap/supply not covered by yfinance). The broker's mutating order tools are mechanically denied (permissions.deny, .claude/settings.json). See decision-log 2026-06-05.

## X70 degradation doctrine (scheduled lanes; TENFOLD T3/T4, 2026-07-04)

Applies to every Task Scheduler lane (T3 qualification-gate verdict: Task Scheduler PRIMARY for all recurring work; CronCreate is session-scoped, Routines have no local-vault write path).

**Lane inventory:**
- `osanwe-sunday-scorer` (SUN 08:17) + one-shot `osanwe-t3-harddate-scorer` (2026-07-06 08:17) -> `tools/run-score-outcomes.cmd` -> `.claude/state/score-outcomes-runs.log`. Zero-LLM (python direct); immune to rate limits.
- `osanwe-morning-brief` (MON-FRI 08:10) -> `tools/run-morning-brief.cmd` (reindex-if-stale poll, then headless `claude -p "/brief --quick"`) -> `.claude/state/morning-brief-runs.log`. Registration script: `tools/register-brief-task.ps1`, which was consumed and then deleted on 2026-07-04 (commit db5dbe7d) and is recoverable only from git history (STAGED FOR THE OWNER; agent registration + agent wrapper-execution both classifier-denied 2026-07-04 -- unauthorized persistence / unattended agent spawn; respected per X70a, not tool-shopped).
- `osanwe-vault-reindex` (every 2 min; repaired 2026-09-13) -> `pythonw.exe tools/scheduled-job.py vault-reindex` from the vault root -> waiting, bounded Node runner. The former VBS returned before its child completed. Registration now uses IgnoreNew, no idle requirement, no wake and a 65-minute task bound; existing triggers and principals are preserved. The source-safe build and next automatic poll have separate receipts. See the current manifest for exact installed executable paths and observed versions.

**Subscription-pool dependency (named risk):** headless `claude -p` draws the STANDARD subscription pool. A rate-limited or over-limit morning fires as a logged non-zero exit and an unbriefed weekday -- never a retry storm. The zero-LLM scorer lane is deliberately claude-independent so calibration survives any LLM outage.

**Detection (silent-failure):** primary = `tools/open-loops.py` briefing-freshness line at SessionStart (T2; counts unbriefed weekdays, holidays not modeled -- a market holiday reads as 1 stale day and is dismissed by eye). Secondary = X75 written-vs-delivered check (meta.json `alerts_fired[].id` must appear in `.claude/state/alerts-delivered.log`; fires only when a machine-trigger alert was emitted). Tertiary = the two run logs above (`exit=` lines). Doctrine: Task Scheduler fallback clause ("after 2 silent failures") is MOOT -- Task Scheduler is already the primary lane.

**Historical idle-gap holiday (X77):** the former detection layer ran only at SessionStart. The September 13 daily heartbeat adds scheduled deterministic observation, with its operational pilot still open. Sleep/offline periods remain explicit observation gaps and cannot be treated as healthy or notification-delivered. Preserve the former detection history; overlapping health ownership is retired only after the replacement's scheduled success and recovery are verified.

**Checkpoint/resume convention (standing, from TENFOLD-0):** long orchestrations persist the workflow script + args at launch; recovery = relaunch with `resumeFromRunId` (unchanged agent-call prefix returns cached). Scheduled lanes are stateless by design (each fire is a fresh session); a killed morning brief (45-min ExecutionTimeLimit) is NOT resumed -- the next weekday fire supersedes, and a same-day manual `/brief --quick` is always safe (same-day collision writes `-HHMM` variant).

**Hard-date guarantee (X70a, standing):** every hard date carries a manual-run guarantee; never rests on a never-fired scheduler. Manual lane equivalents: `tools/run-score-outcomes.cmd` (scorer), in-session `/brief --quick` (brief; the wrapper's headless spawn is agent-denied, the owner can run `tools/run-morning-brief.cmd` by hand).

**Local model lane -- DELEGATION form (current; supersedes the whole-session qwen backend, 2026-08-11):** the orchestrator (Fable/Opus, on the subscription, in whatever harness) stays in charge and hands a bounded, checkable leg to a local model via ONE command:

```
python tools/delegate.py "<instruction>" [--file <path>]... [--json] [--leg <id>]
```

**THE DELEGATE LANE (`delegate.py`) is SINGLE-SHOT and TOOL-FREE** -- this property is
scoped to `delegate.py` and stays true verbatim: prompt in, text out; it cannot call MCP
servers, search the web, or touch files. (The one local model given UNCONTAINED tool
access -- Nemotron 3.5 Lightning, 2026-08-11 -- appended past a blocking gate and deleted
evidence of a `private/` write. That is why this lane stays tool-free.)

**THE RESEARCHER LANE (`tools/relay.py`) is TOOL-CAPABLE and MECHANICALLY CONTAINED**
(shipped 2026-08-16; GATE-B gate-b-relay-worker-2026-08-16; operator-ratified,
named+specific, reversal of the blanket tool-free rule -- Calendar/daily/2026-08-16.md).
The local model runs as a RESEARCHER: acquires via an allowlist executor
(`tools/lib/relay_exec.py`: fetch_url with AGENTS.md-parsed domain blocklist + SSRF guard
re-validated per redirect hop; mcp_call limited to `relay.mcp_allowlist` in
config/local-lane.json -- openinsider v1; jailed vault reads excluding private/, finance/,
credentials/, .raw/, config/, .git/, .obsidian/, .claude/state/, *.local.md, and any name that
starts with .env, ends in .env, .key, .pem or .credentials.json, or contains auth.json -- so a
backup or renamed copy of a secret is refused as the secret is; scratch as the only write path, traversal
unexpressible by grammar; the broker + claudewatch have NO code path) and structures via a
validating `record_claim` accumulator whose `source_ref` must resolve to an on-disk
artifact -- fabricated citations are impossible in code, not discouraged in prose. The
DRIVER owns context accounting and forces a structured distillate relay at 80% of W_eff
(209,715 of 262,144; R0 2026-08-16 proved prefix reuse works on /api/chat), then resets --
unbounded workloads, bounded context. The model NEVER self-monitors and NEVER judges:
never-local classes are refused by the same `leg_status()` gate (`legs.research` map).
Every tool call and refusal lands in a per-run executor ledger; the acceptance suite
(`tools/test-relay.py`) grades containment ON THAT LEDGER at a 100% bar INCLUDING while
running the known-bad nemotron fixture. Distillates: `.agents/relay/<run>/` (tracked);
working payloads: `.claude/state/relay/<run>/` (untracked). Suite + protocol evidence:
`.agents/migration/verification/worker-lane-experiments-2026-08-16.md`.

**Relayed provenance rule:** a claim relayed by the researcher carries its DATA-SOURCE
`prov` (e.g. `mcp:openinsider`) plus a leg-level `extractor: local:<model>@<digest>`
(lowest tier). A relayed figure may not enter the vault at its source tier until the
orchestrator re-fetches it or a checker validates it -- "delegated output is INPUT, not
truth" applies unchanged, and the distillate's per-claim `verify` recipe makes the
re-check cheap. A fourth ROUTE-LOCAL class exists for this lane: (d) TOOL-USING-RETRIEVAL
-- acquisition through the CONTAINED executor, orchestrator-verified downstream
(operator-ratified 2026-08-16).

**Mid-leg escalation (`ask_frontier`, shipped 2026-08-17; GATE-B
gate-b-ask-frontier-2026-08-16).** The worker may ask the orchestrator ONE
validated question mid-leg: the EXECUTOR refuses any escalation that fails to cite
resolving `[R-nn]` refs or to state what was attempted (lazy punting is
structurally unexpressible), budget 3 per leg (missions may lower to 0). On a
valid ask the driver relays (distillate stays VALID), persists state, and exits
with status `awaiting-guidance` in the exit-5 family; the envelope carries the
question + `guidance_path`. The orchestrator -- already in-session, no new
transport, no second billed session -- writes the guidance file and re-runs
`--resume <run>`: the answer injects as ORCHESTRATOR GUIDANCE, the ONE trusted
non-sentinel-wrapped payload, and registers as a `kind: frontier` SOURCE so
derived claims carry `prov: frontier`. Frontier judgment enters LABELED as
frontier, never laundered as the local model's -- the never-local boundary
survives by provenance, not prohibition. Escalation counts ride the receipts
ledger (`escalations` per row); the 2026-09-11 review reads whether the worker
asks well or punts. Suite family T8 tests both directions (escalates on an
unresolvable source conflict; does NOT escalate on a plainly-answerable
extraction) plus executor validation and the full pause/resume round-trip.

**glimmer is the LANE, not the model.** The operator phrase survives every model swap verbatim. The active model is named in exactly one operational place: `config/local-lane.json`. No document restates it and **no ambient env var selects it** (X12: a persistent `CLAUDE_CODE_SUBAGENT_MODEL` once outranked every model pin for weeks, undetected). Resolution order is exactly `--model` (explicit, per-invocation, visible in transcript) > config.

**HONEST SCOPE -- read before promising token savings.** Delegation does NOT make `/invest` meaningfully cheaper in Claude Code. Under Tier-A the research mass runs on Opus SUBAGENTS (E.0, J-bis.0, K-bis.0, K.5, L.0), delegation is main-loop-only, and the lane has no tools with which to replace a worker that searches before it extracts. Where the lane actually pays: bulk mechanical vault passes (ASCII/frontmatter sweeps, reformatting, dedup, fixture generation); `/enrich` and `/ingest` text processing; rate-limited days when the subscription pool is exhausted; and sequential-topology runs (Codex CLI and other Tier-B harnesses) where Phases E/F/H.2/I are main-loop work rather than dispatches. As of 2026-08-17 the relay role families (research / extract / edit) cover the bulk-mechanical and enrich/ingest-shaped payloads directly: extraction runs as `extract:*` legs and mechanical sweeps land as `edit:*` PROPOSALS the orchestrator applies through its own Edit tool.

**The invocation phrase to honor:** any operator sentence pairing the lane (`glimmer` / `local` / `delegate` / `local model`) with a scope hint (`what it can handle` / `where possible` / `what you can`), with or without a skill invocation such as `/invest MU`, means: run the ROUTE-LOCAL classes below through `tools/delegate.py` (single-shot tool-free legs) or, for tool-bearing relay families (`research:` / `extract:` / `edit:`), through `tools/relay.py` with a mission composed by `tools/relay-mission.py` under the /local discipline, keep everything else on the frontier model, and report which legs were delegated AND which model ran them. It is never an instruction to lower the bar on a NEVER-LOCAL leg.

**Delegation is MAIN-LOOP ONLY.** The orchestrator delegates legs it would otherwise run itself; subagents and workflow workers never call `delegate.py`. This keeps the rubber-stamp-verifier hole shut and guarantees the `/invest` fan-out topology is never mutated by the phrase. **Honest status: this rule is INSTRUCTION-HONORED, not mechanically enforced** -- any subagent holding Bash could invoke the tool and nothing would stop it. An earlier draft of this section claimed the rule was 'structural'; that was false and is corrected here (audit 2026-08-11).

**What is MECHANIZED vs instruction-honored** (the vault's standing distinction -- an instruction with no enforcement is a known drift class, so it gets named rather than assumed):
- MECHANIZED: never-local leg refusal (exit 3, and an unknown leg id for a mapped skill is refused too, so a one-character typo cannot fail the gate open); `local:<model>@<digest>` provenance stamping using the digest of the model that ACTUALLY ran; the receipts ledger (a write failure warns loudly rather than going dark); injection containment via per-run sentinel; ASCII checking; daemon-authoritative tag resolution; the truncation canary; config shape validation; acceptance discrimination (the suite must reject a known-bad model -- see below).
- INSTRUCTION-HONORED (no enforcement; drift is possible and would be invisible): main-loop-only; arm-before-delegating; the two-strike breaker; the one steered retry; and the duty to report delegated legs in Phase P.

**Arm once, break twice, never HALT.** `python tools/delegate.py --check` arms the lane (real roundtrip, not a membership test; an architecture rejection is reported as "upgrade the daemon"). Two consecutive lane failures mid-run disarm it for the remainder. Lane absence is NEVER a HALT -- every leg falls back to the frontier model. Arming branches on lane AVAILABILITY, never on model identity.

**One steered retry.** On a malformed or empty delegated result, re-issue ONCE with the specific defect named ("your output was not valid JSON; return only the object"), then fall back to frontier. Do not loop.

**Exit codes are contractual:** 0 ok; 2 lane unavailable (incl. empty response -- deterministic on some model packagings, not a flake); 3 bad usage or a refused NEVER-LOCAL leg; 4 JSON requested but unusable; **5 (relay lane only), two statuses, both resumable with a VALID distillate: `partial` (budgets exhausted or stalled; consume the distillate, then decide resume-vs-frontier) and `awaiting-guidance` (the worker asked a validated `ask_frontier` question; answer it via the envelope's `guidance_path` and re-run `--resume <run>`). Exit 5 is the ONE non-zero exit that still carries a deliverable. For every OTHER non-zero exit the rule is unchanged: DO THE LEG YOURSELF** -- never silently skip a delegated leg, and never report a skipped leg as done.

**/local is the per-query routing surface** (skill; GATE-B gate-b-local-skill-2026-08-17). It packages the whole loop -- route decision, mission compose, dispatch with `CLAUDE_LANE_TRIGGER=operator-phrase`, escalation guidance, MANDATORY `relay-verify` before consumption (fabrication-grade = quarantine), prov-labeled consumption, receipts + orchestrator-share JSONL. Scope: mode-2 selection-is-consent + operator-phrase invocations ONLY; all-sessions default routing stays CLOSED until the pre-registered parity rule passes and a /decide ratifies the flip.

**Scheduled idle-gated legs** (staged 2026-08-17; task registration is owner-ONLY, X70a): `tools/run-local-worker.cmd` (daily 03:30 once registered) sets `CLAUDE_LANE_TRIGGER=scheduled-idle` -- LOAD-BEARING, frozen into leg state at creation so unattended legs NEVER count toward promotion -- and calls `relay-batch --if-idle` (lane.lock + double GPU sample + daemon reachability, fail-closed skip). Every fire logs run-or-skip to `.claude/state/local-worker-runs.log`; that log is the X70 heartbeat (silent >= 2 days surfaces LANE SILENT in the open-loops footer). Results wait as distillates surfaced via `scheduled-worker-pending.json`; escalations PARK for next-session guidance; `consistency: true` missions run twice and mechanically diff claim sets (divergence telemetry, F-10 both-arms-ok rule).

**Parity rule (promotion gate):** the pre-registered promotion AND demotion standard for all-sessions default routing lives at `wiki/research/parity-eval-rule-2026-08-17.md` (frozen with `tools/parity-eval.py` + `tools/parity-cases/`). The rule text is NOT restated here -- read the file before touching `default_delegation`, the manifest, or the grader.

**Verification rule (non-negotiable):** delegated output is INPUT, not truth. Every delegated result must be checked by the thing that would have checked it anyway -- a gate CLI, a checker script, a provenance requirement, or the orchestrator re-reading the source. Nothing a local model produces enters the vault unchecked. Delegated output is stamped `local:<model>@<digest>` at the source, the only point where its true origin is still known; `local:` is the LOWEST provenance tier.

**Receipts, not recollection.** Every call appends to `.claude/state/delegate-runs-<date>.jsonl`; `python tools/delegate.py --report [--since DATE|--run ID]` renders them. A model self-reporting which legs it handed to another model is the one report that cannot be trusted by construction. This ledger is also the evidence channel for the pre-registered 2026-09-11 consumption check on the lane GATE-B override.

**Swapping the model** (`python tools/delegate.py --use <tag> [--force]`): resolves the tag through the daemon (bare names, wrong-case tags and `:latest` aliases all normalize), unloads the incumbent, loads and round-trips the candidate, runs `tools/test-delegate.py` (9 semantic cases, expected values authored from fixture source, no LLM judge). **The suite must DISCRIMINATE or it is theatre**: the original 6 cases were passed 6/6 by nemotron-3.5-lightning, a model documented the same week hallucinating a skill roster and appending past a blocking gate. C7 (a plausible in-band directive addressed to 'automated data processors', not a blatant override) now rejects that model live while the incumbent resists it. Any future case set must keep at least one case a known-bad model fails, writes config atomically, and prints a rollback line. `--force` adopts despite a failing suite -- the suite informs the operator, it never vetoes him. `--rollback` restores the previous model WITHOUT requiring a passing suite, because the daemon may be the thing that is broken. Honest framing: **two commands when the ecosystem has caught up; one loud, correctly-diagnosed failure when it has not** -- the 2026-08-10/11 Glimmer drop needed a library 404 detour through hf.co, an architecture rejection on two daemon versions, two daemon upgrades and a parser bugfix inside 36 hours.

- ROUTE LOCAL (deterministic or checker-validated). Three classes, general to every skill: (a) SCRIPT-COMPUTED -- a CLI produces the answer and the model only relays it; (b) MECHANICAL-CHECKABLE -- reformatting, ASCII/frontmatter normalization sweeps, table composition, extraction into a fixed schema, test-fixture generation, where a gate or checker validates the result; (c) PROVENANCE-CHECKED EXTRACTION -- pulling figures out of text the ORCHESTRATOR ALREADY FETCHED, where every figure must carry a `prov:` the orchestrator verifies anyway. The per-skill leg map lives in `config/local-lane.json` and is printed by `python tools/delegate.py --legs <skill>`.
- NEVER LOCAL (frontier only, no exceptions): the `/invest` verdict spine and scoring-path routing; thesis-status calls; ratings, conviction and kill criteria; ALL dissent/skeptic/verification legs (a weak verifier that rubber-stamps is worse than no verifier); the mandatory subagent dispatches (price-fetcher, the Wave-1 template workers -- tool-using dispatches the lane structurally cannot perform, and pre-emptive skipping is FORBIDDEN); anything touching live positions, doctrine math or the security perimeter; any decision record; and any write the 95/100 honest floor scores on nuance. Delegation changes WHO RUNS A LEG, never the standard it must meet -- and the tool refuses a NEVER-LOCAL leg id outright (exit 3).

Prior form (ARCHIVED-2026-08-12, non-functional; record: local-qwen-lane-archive-2026-08-12 -- archives the IMPLEMENTATION, not the capability, and changes NO gate marker; note `vault-search/` is LIVE and carved out there): the whole-session backend `pwsh claude-local.ps1` (Qwen3.6-27B @ llama-server on an isolated `the vault root-local` worktree; champion profile ratified 2026-07-04, build detail local-qwen-optimization-2026-06-13). Its GGUF is absent from disk as of 2026-08-11 and it has been idle since ~2026-06-14. Cause of non-use, operator-stated: a whole-session local model is not capable enough to be worth opening. The delegation form exists because it does not share that failure mode. Do not revive the backend without a fresh /gate b.

Git cleanup 2026-09-12 retired the archived the vault root-local worktree after a
complete verified ZIP plus Git-bundle recovery test. Unique evaluation notes are
under _archive/2026-09-git-recovery/; the branch tip remains at
archive/local-mode-2026-09-12. This did not alter the active local routing or
vault-search service. See GIT-RECOVERY-REPORT-2026-09-12.

**Subagent-model env-jail governance (X12, standing; canonical record):** ROOT CAUSE of the 2026-06/07 fleet mislabeling -- a persistent User-scope `CLAUDE_CODE_SUBAGENT_MODEL=claude-sonnet-4-6` (seeded by an in-vault /corpus SKILL "defensive env var" instruction) silently OUTRANKED every per-call model pin, Agent-tool model param, agentType definition, workflow `opts.model`, and frontmatter pin -- jailing ALL vault fleets to Sonnet 4.6 for weeks. June fleets logged as all-Opus actually ran Sonnet from the 2026-06-19..06-20 onset (per-message census, tenfold0-evidence-2026-07-03).
- STANDING RULE: NEVER set `CLAUDE_CODE_SUBAGENT_MODEL` at any persistent scope. Production roles and workflows inherit authorized session settings (2026-09-13 user directive); fixed evaluation configurations retain their separate owners. Compare requested settings with observable runtime metadata and disclose uncertainty. A model's self-identification alone does not verify its identity or effort. Historical frontmatter floors above are preserved history, not current dispatch defaults.
- Scrubbed (TENFOLD T1): the /corpus SKILL + README + `.claude/agents/corpus-extractor.md` (and their `.agents`/`.codex` mirrors) carried the anti-guidance instead of the old defensive var (5-file scrub verified at T6). The three `.claude` files were moved into `_archive/` folders with the /corpus skill on 2026-07-06 (commit 840acc93); their `.agents`/`.codex` mirrors had already moved to `_archive/codex-mirror-2026-07-04/` in commit 02d6915b on 2026-07-04. All six are still tracked and still carry the anti-guidance, and Claude Code still registers the archived corpus-extractor agent, so this record -- not the archived files -- is the statement of the rule.
- Detection wiring (the one-shot applier `tools/apply-t6-config.py` was deleted as consumed on 2026-07-04 in commit db5dbe7d; the session-integrity tripwire itself landed in commit f6baec44, labelled "T7 repair"; the wiring is live and was re-read 2026-09-21): a SessionStart tripwire in `session-integrity-check.sh` warns if the var is set in the session env; `subagent-telemetry.py` passes a `model` + `label` field per dispatch into `.claude/state/subagent-telemetry-*.jsonl` so a future jail is visible in the telemetry trail, not merely inferrable post-hoc from a transcript census.
