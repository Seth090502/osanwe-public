---
name: brief
description: "Institutional-grade daily morning briefing -- today's market setup, premarket catalysts, regime. Use when starting the trading day, before the open, ahead of FOMC/CPI/earnings, on a weekend, or when the prior briefing aged past 24h. PDB BLUF/Counter/Alternative, thesis status board, net-liquidity + insider overlays, evidence-grade confidence caps, Brier-scored meta.json sidecar in Calendar/decisions/briefings/. Not a lookup in an old briefing, not a topic explainer."
metadata:
  categories: monitoring
  osanwe-risk: "safe"
  osanwe-effort: "max"
  osanwe-arguments: ""
  osanwe-argument-hint: "[--preview] [--confirm] [--replace] [--quick] [--refresh `<path>`] [--no-peripheral]"
  osanwe-allowed-tools: "WebSearch WebFetch Read Write Edit Bash Glob Grep Agent"
  osanwe-categories: "meta"
  osanwe-type: "skill"
  osanwe-status: "active"
  osanwe-created: "2026-04-18"
  osanwe-updated: "2026-09-12"
---

Financial evidence contract: `docs/financial-analysis-contract.md` governs source
quality, temporal/basis semantics and missing-data handling across harnesses.
For material numeric batches, run `python tools/fis/evidence.py <envelope.json>`
before output, or disclose manual review and any unverified semantics.
Plugin interoperability: `.agents/skills/finance-data/SKILL.md` owns typed
evidence intake and portable Finance/Data handoffs. This skill retains its
financial procedure and gates. Probe callable tools at run time; installed
plugin metadata alone does not establish a usable connector or source schema.


# /brief -- institutional-grade morning briefing with PDB discipline (v2 final)

Take today's market state, produce an institutional-grade morning briefing that lands in the vault atomically: compose a canonical briefing file at `Calendar/decisions/briefings/briefing-<date>[-HHMM].md` with PDB-style BLUF + Counter + Alternative Analysis + day-regime + macro-regime + cross-asset-coherence + thesis status board + evidence-graded portfolio impact + Warning Problems + Intelligence Gaps + FOLLOWUPS:skills coordination + machine-readable meta.json sidecar; update daily note Market Pulse summary + linkback; bump hot.md last_briefing; append sessions-log entry; symmetric back-link to materially-discussed entities; commit atomically.

## When to use

Daily trading-day morning use to set the day's decision frame. Weekend variant produces "Week in Review" framing with expanded calendar + scenario bar. Fed Week, earnings week, and crisis regimes auto-expand relevant sections.

## Not for

- Portfolio refresh / live-price snapshot (use `/networth`)
- Thesis stress-test without a specific event (use `/challenge thesis-<slug>`)
- Investment decision on a single ticker (use `/invest <ticker>` then `/decide` if action proposed)
- Ad-hoc price check (direct script call: `python tools/fetch-prices.py --equities <list>`)
- Session retrospective (use `/retro`)

### Mode routing (Pattern 6 deterministic; invocation modes)

- `--executive` / `--format executive` -> produce the EXECUTIVE brief format
  (ref-brief-executive.md): 5-10 importance-ranked narrative paragraphs with
  per-category portfolio effect. Replaces v2 body sections 4-19; frontmatter,
  BLUF block, FOLLOWUPS, and meta sidecar unchanged (sidecar gains
  `"format": "executive"`). Default remains v2 tables format.

| Syntax | Behavior |
|---|---|
| `/brief` | Full 16-phase A-P briefing; atomic commit across 5 targets + N entity back-links |
| `/brief --preview` | Phases A-N in memory; render briefing + meta + audit to stdout; SKIP O-P; F11 never set |
| `/brief --confirm` | Block at Phase B for `yes`; block before each of the 6 Phase P writes |
| `/brief --replace` | Same-date collision overwrites `briefing-<date>.md` without `-HHMM` suffix; explicit user intent (sidecar overwrites too) |
| `/brief --quick` | Compressed: Markets + Signal Dashboard + Portfolio Movers + FOLLOWUPS only; skip G/I/K/L and most of M; Phase H runs H-lite (machine-trigger evaluator + alert emission only, no prose board -- the T4 scheduled-lane alerting spine); <=200 words body; sidecar still written |
| `/brief --refresh <path>` | Additive merge into existing briefing: mutate Alerts + FOLLOWUPS only; body outside byte-exact (sha256-verified); `updated:` bumps; append to existing meta.json `web_searches` + `followup_skills` arrays; no peripheral writes |
| `/brief --no-peripheral` | Phase O briefing + sidecar only; SKIP Phase P entirely (composition test) |

## Execution Rules

- **Tier-A/Tier-B split (DW port, brief-vnext 2026-07-04)**: Phase A.7 detects topology. TOPOLOGY=dw is **Tier-A** and requires the harness to expose a Workflow tool -- it routes Phases C.2/D/E.0 data acquisition through the `brief-research` workflow (`.claude/workflows/brief-research.js`) per Phase A.8. TOPOLOGY=sequential is the **Tier-B spine and the PERMANENT UNIVERSAL FALLBACK**: every harness without a Workflow tool -- and every harness without an Agent tool at all -- executes the phases sequentially exactly as written, at full quality and with no loss of contract. No merging either way. Use WebSearch only when explicitly authorized per phase (target: 0-3 web searches per run TOTAL, distributed -- not expanded -- across DW workers; script provides everything else).
- **Harness-conditional dispatch (binds EVERY dispatching phase: A.8 wave routing, D.0 `price-fetcher`, J.0 `institutional-positioning-scout`, the A.8 lite data-integrity skeptic, P.0 `vault-classifier-sweep`)**: dispatch the named workflow/subagent WHEN the harness exposes the corresponding Workflow/Agent tool; when it does NOT, execute that phase's documented inline fallback VERBATIM as the NORMAL path -- reported `topology: sequential (no Workflow tool)` / `mode: inline (no Agent tool)`, a harness capability gap, NEVER a DEVIATION. The WORK is mandatory either way; only the mechanism varies. Skipping a dispatch where the tool DOES exist remains a DEVIATION. No phase conditions its behavior on model identity.
- **F11 Phase C discipline**: set `.claude/state/auto-commit-disabled` at Phase C, BEFORE any Edit/Write. Phase B state-transition print runs BEFORE F11 so user can abort pre-writes. Clear flag only after Phase P post-commit verification passes.
- **Path-guards mechanical**. NEVER write to: `private/`, `.raw/`, `_quarantine/`, `finance/`, `credentials/`, `.git/`, `.claude/hooks/`, `.claude/state/` (except the F11 flag + append-only `alerts-delivered.log` per Phase H alert emission). NEVER read `.raw/`, `private/`, `finance/`, `credentials/`, `.env*`, `auth.json`, or `*.local.md` into context. Account facts require current-session broker read evidence. Phase 15 portfolio refresh from /brief v1 is RETIRED -- portfolio mutations belong to /networth scope.
- **Tag vocabulary canonical**: emit only `topic/market-brief` on briefing frontmatter (no ticker/company/thesis tags unless briefing is itself thesis-centric, rare/explicit). HALT on namespace drift.
- **Binary decisions default**: thesis HEALTHY/WATCH/STRESSED/INVALIDATED; coherence coherent-on/coherent-off/divergent; followup skill EMIT/SKIP. NEUTRAL only when signal genuinely absent both directions.
- **Confidence vs Conviction are DISTINCT fields**. Confidence (epistemic, 0-100%) capped by evidence-grade mix. Conviction (low/medium/high actionable) reported separately.
- **Body-preservation sha256** on every UPDATE in Phase P (daily note, hot.md, entity notes). Pre/post sha256 with strictly-additive-outside-insertion-sites assertion.
- **Symmetric back-linking**: every wikilink in briefing `related:` (3-7 typical) gets reciprocal `[[briefing-<date>[-HHMM]]]` on the target file's Recent section.
- **Mid-batch failure**: immediate HALT (Phase P F.halt), F11 stays on, no partial commit, structured report.
- **Commit discipline**: ASCII-only title + body, Co-Authored-By SUPPRESSED (F17 verify), F14 narrow staging (explicit pathspecs only).
- **Same-day collision**: if `briefing-<today>.md` exists AND no `--replace`, default to `briefing-<today>-<HHMM>.md` (HHMM from clock). If same-HHMM file also exists, HALT (sub-minute re-run is ambiguous intent).
- **Subagent dispatch is MANDATORY when specified by phase AND the harness exposes an Agent tool** (Phase D.0 dispatches `price-fetcher` for live quotes; Phase J.0 conditionally dispatches `institutional-positioning-scout` per held position with fresh institutional signal; Phase P.0 dispatches `vault-classifier-sweep` pre-commit gate). Pre-emptive skip based on judgment ("script will work fine direct", "no fresh institutional signal worth checking", "audit not necessary today") is FORBIDDEN. The subagents decide applicability via their own N/A return contracts (e.g., institutional-positioning-scout returns N/A on crypto tickers gracefully). Legitimate fallback fires ONLY on (a) contract violation -- subagent return missing required fields, OR (b) actual dispatch failure -- timeout, rate limit, tool-denial, hard subagent crash. Pre-emptive skip surfaces in Phase P audit as **DEVIATION** (not "fallback"). Quality preserved by additive design: existing inline `tools/fetch-prices.py` invocation + manual portfolio impact + direct `tools/vault-audit.py` invocation remain intact as legitimate-failure fallbacks. `--quick` mode SHOULD skip Phase J.0 + P.0 dispatches (sub-30s target precludes the 5-15s dispatch overhead per call); that's a documented skip, not deviation. A harness with NO Agent tool runs those same inline paths (`tools/fetch-prices.py`, manual portfolio impact, direct `tools/vault-audit.py`) as its NORMAL path, reported `mode: inline (no Agent tool)` -- a capability gap, not a DEVIATION.

### Quality Rules

- **BLUF first**: opening sentence is a judgment with numbers + dollar impact, not a summary. Bad: "Markets are mixed". Good: "`<ticker>` -4.2% on China export rumors, $`<amount>` portfolio impact across <N> combined shares."
- **Counter line (Tenth Man, PDB ICD 203)**: one sentence arguing the opposite case with cited evidence. Not canned bear-vs-bull -- specific evidence-grounded dissent.
- **Alternative Analysis (PDB ICD 203)**: a third-order scenario distinct from BLUF and Counter. One line. The non-obvious third path that becomes obvious in hindsight.
- **Priced-In line**: state market expectations + what would surprise. If nothing material today, skip the line entirely (do not pad). Each priced-in call goes into frontmatter `priced_in_calls:` as structured list for tomorrow's Brier scoring.
- **What / So What / Now What**: every portfolio mover answers all three. Raw data without interpretation is noise. Now What is one of: NO ACTION / MONITOR `<trigger>` / ADD @$X / TRIM @$X / REVIEW THESIS. ADD/TRIM gets copy-paste-ready order block.
- **Dollar impacts EXACT** from `shares_held * (price - prev_close)`. Cross-account holdings combined (a name held in more than one account is summed once, never double-counted). Beta-adjusted impact for thesis-level events. Never estimate, never "about".
- **Regime classification drives expansion**: Crisis/Risk-off expand portfolio + geo + alerts. Risk-on/Rotation contract alerts; expand calendar + deployment. Fed Week expand calendar + scenario bar.
- **Calibrated % confidence on forward-looking**: percentages, not HIGH/MEDIUM/LOW. Capped by Pre-Output gate evidence-grade rule.
- **Inline evidence grading on material claims**: `[Grade A | source | date]`. A = primary (SEC, IR, FRED). B = Tier 1 wire (Reuters, CNBC, AP). C = aggregator/analytical. D = sentiment. F = unverifiable. STALE (>7d) auto-downgrades one letter.
- **Temporal anchoring**: every data point has its date. No "recently / today / currently" without timestamp.
- **Intelligence Gaps vs Warning Problems**: Gaps = "I don't know X (impact, resolve)". Warnings = "I know X and it matters but is below trigger threshold (base rate, escalation trigger)". Distinct sections; do not conflate.
- **3-minute rule**: briefing body <=650 words. >650 = padding defect. Quick mode <=200 words.
- **CFA 3-stage geo filter**: event detection -> transmission mapping -> SUPPLY (include) or SENTIMENT (skip unless FLASH). Sentiment-only events excluded without mention.
- **Basis-integrity caveat**: never report P&L for a position whose cost basis is not positively established. Without positively established basis, omit P&L. Report supported current-value changes separately from realized/unrealized P&L and disclose any transfer or corporate-action caveat.
- **Cross-account holdings combined**: derive overlap from current-session broker read evidence; reconcile every covered account before claiming combined exposure.
- **Corporate actions**: verify dated split/dividend adjustments and consistent share/price basis before reporting returns or dollar impact; do not reuse a historical adjustment assumption.
- **Quiet-day suppression**: if all 7 quiet conditions from ref-monitoring-rules.md sec 2 are met, BLUF redirects to vault priorities; FOLLOWUPS empty-case renders `(no followup skills recommended)`.
- **ASCII-only NEW content (Pattern 22)**: em-dash -> `--`; curly quotes -> `"`/`'`; arrows -> `->` / `<-`; `<=` / `>=`; ellipsis -> `...`; euro -> `EUR`; NBSP -> space; middle dot -> `-`. Byte-scan; HALT on any byte > 127.

## Phase 0: Vault context retrieval (NEW; Phase 3.6d -- runs BEFORE Phase A; read-only; runs in --preview; SKIP on --quick)

Read-only retrieval uses explicitly approved non-sensitive sources. A semantic adapter must enforce its corpus allowlist and protected-path exclusions BEFORE result text enters context; post-retrieval filtering is insufficient. Scope Phase 0 to public-research/method sources, never account histories, snapshots, dailies, logs or raw broker output. Named narrative reads in later phases retain their own scope.

0.0 -- Mode gate: if invocation includes `--quick`, SKIP Phase 0 (emit `Phase 0 -- skipped (--quick fast path)`) and proceed to Phase A. All other modes (normal, --preview, --confirm, --replace, --refresh, --no-peripheral) RUN Phase 0.

0.1 -- Derive 13 query subjects across 4 groups from current vault state:
- PORTFOLIO (up to 4): use current broker-read positions to choose the largest known holdings for retrieval queries. If unavailable, use named thesis entities for context and mark account relevance UNVERIFIED; never consult private/ or *.local.md.
- THESIS (5): from `Atlas/concepts/investing/theses/thesis-*.md` (5 essays: theme-alpha, theme-epsilon, theme-gamma, theme-beta, theme-delta). Query = `"<thesis-name> thesis"`.
- CATALYST (2): from `Atlas/sources/investing/ref-market-calendar.md` next-7-day events (FOMC / CPI / earnings / etc.). Query = `"upcoming <event> catalyst impact"`.
- CROSS-CUTTING (2): from the 2 most-recent `wiki/research/challenges/*.md` filenames. Query = `"<challenge-topic> findings"`.
If any source is empty, fall back to a generic subject for that slot (never emit an empty query).

0.2 -- Use the verified adapter on an explicit approved source set for the four
groups. If no enforced safe adapter is available, use `rg -n --fixed-strings --
<subject> <approved-file> ...` on named entity/public-research/method files after
checking their scope. Exclude protected paths, `.env*`, `auth.json`, `*.local.md`
and personal financial snapshots before content is read. No broad `wiki/`,
`Calendar/` or `wiki/investing/` query; do not assume a filter parameter enforces
this boundary on an unverified external index.

0.3 -- Dedup results by `path:line`; tag each approved hit with portfolio,
thesis, catalyst or cross-cutting. Retain semantic scores only if supplied by
the adapter; lexical matches have no invented score. Store method and scope in
VAULT_CONTEXT and disclose the lexical fallback when used.

0.4 -- EMIT a visible summary (MANDATORY), GROUPED by derivation source:

    Phase 0 -- derived-subject vault context (N distinct paths total)
    PORTFOLIO    (P hits): [score] path:line -- ~60 chars   (up to 4)
    THESIS       (T hits): ...
    CATALYST     (C hits): ...
    CROSS-CUTTING (X hits): ...

If no approved hits are available: emit `Phase 0 -- no vault context retrieved`
with the cause and continue. NEVER HALT on Phase 0 alone.

0.5 -- Downstream consumers (phases A-P UNCHANGED; consult VAULT_CONTEXT by group):
- Phase D/E (markets + portfolio movers): portfolio-group context informs each mover's "So What".
- Phase F/G (thesis status board): thesis-group context seeds HEALTHY/WATCH/STRESSED/INVALIDATED priors.
- Phase H/I (catalysts + calendar): catalyst-group context anchors the priced-in calls.
- Phase K/L (FOLLOWUPS:skills + Counter/AA): approved cross-cutting context surfaces cross-skill connections.

Cite any used chunk inline as `(vault: path:line)` -- plain text, NO wikilink syntax.

## Phase A: Pre-flight (NO F11 yet)

**U1 residency gate (orchestration economics, AGENTS.md).** Run
`python tools/run-share.py --current-context` FIRST. Exit 1 means the session is
carrying more resident context than this run should re-pay on every turn: report
the number, recommend `/clear` + re-invoke in a fresh session, and proceed only if
the operator says to. Cost basis: cache_read is ~82% of frontier cost and equals
the sum over turns of the resident prefix, so a heavy run started at 500K residency
costs multiples of the same run started fresh. This is a RECOMMENDATION, not a HALT
-- never block work the operator asked for; make the price visible before it is paid.


A.1 -- Parse args: `--preview`, `--confirm`, `--replace`, `--quick`, `--refresh <path>`, `--no-peripheral`. Validate combinations (e.g., `--refresh` requires path; `--replace` and `--quick` are exclusive of `--refresh`).

A.2 -- Resolve today's ISO date from system clock (`date +%Y-%m-%d`); never from prior session memory or context.

A.3 -- F11 collision check: if `.claude/state/auto-commit-disabled` exists, HALT: "F11 already set by another skill. Either another skill is running concurrently or a prior crash left an orphaned flag. Manually `rm .claude/state/auto-commit-disabled` to clear, then re-invoke."

A.4 -- Broker coverage: discover available read tools and obtain current-session
account/asset evidence. Record read time and covered scope; unavailable coverage
sets `BROKERAGE_WARN = "UNVERIFIED: <missing scope>"` for the header and
Intelligence Gaps. Public-market briefing work continues, but affected dollar
impact, P&L and whole-book claims remain unavailable; no saved-file fallback.

A.5 -- Same-day collision detection: if `Calendar/decisions/briefings/briefing-<today>.md` exists AND no `--replace`, default output to `briefing-<today>-<HHMM>.md` (HHMM from clock). If same-HHMM file also exists, HALT (sub-minute re-run ambiguous; ask `<owner>`).

A.6 -- Validate `tools/fetch-prices.py` exists; HALT if missing (script is load-bearing for Phase D).

A.7 -- **Topology detection** (mirror of /invest A.7): `TOPOLOGY=dw` iff the Workflow tool is present in the session tool surface; else `TOPOLOGY=sequential`. Ambiguity -> sequential. `capability-detect.sh` is ADVISORY only -- the tool-surface check is authoritative. ALSO record `AGENT_TOOL = present|absent` (does this harness expose an Agent/subagent tool? `dw` implies present): `AGENT_TOOL=absent` routes every dispatching phase (D.0, J.0, the A.8 lite skeptic, P.0) to its documented inline path as the NORMAL path, reported `mode: inline (no Agent tool)`. Record `ORCHESTRATOR_MODEL` (passive logging only -- NO behavior branches on model identity, per Topology & Data Doctrine). `--quick` FORCES sequential (sub-30s target precludes workflow spin-up; documented skip, not deviation). Frontmatter + sidecar gain `topology:` + `orchestrator_model:` (passive).

A.8 -- **Wave routing**:
- `TOPOLOGY=sequential` (Tier-B; every harness with no Workflow tool): Phases C.2/D/E.0 run verbatim as written below -- zero behavioral difference; the PERMANENT UNIVERSAL FALLBACK, reported `topology: sequential (no Workflow tool)` and never a DEVIATION. With `AGENT_TOOL=present` the D.0 / J.0 / P.0 Agent dispatches still fire inside this spine; with `AGENT_TOOL=absent` each falls through to its documented inline path (`mode: inline (no Agent tool)`).
- `TOPOLOGY=dw` (Tier-A; ONLY where the harness exposes a Workflow tool): invoke the `brief-research` workflow (`.claude/workflows/brief-research.js`; Workflow tool, `{scriptPath}`) with args `{equities, crypto, held_tickers, thesis_slugs, run_date, token_budget}`. ONE wave, concurrency <=6, of independent READ-ONLY acquirers: (1) `price-fetcher` agentType (existing contract incl. extended-hours fields; replaces the Phase D.0 Agent-tool dispatch), (2) FRED macro worker (Phase E.0 series set incl. net-liquidity rows; availability-guarded N/A return; also carries the Phase J.6 openinsider pair), (3) entity+challenge recency worker (git log + targeted Reads; returns Phase C.2 recency summaries), (4) continuity worker (last-3 briefings parse + brier-ledger read + `python tools/score-outcomes.py --dry-run --json`; returns the calibration block), (5) an optional personal worker that is not included in this copy. Main loop RETAINS: current-session broker reconciliation (workers receive only the minimum permitted evidence needed for their task; no protected-file reads), regime CLASSIFICATION (tables unchanged; workers only fetch inputs), all composition phases F-N, all writes O-P. Convergence gate identical to /invest: N/A = success; missing fields -> one re-dispatch -> documented inline fallback; pre-emptive skip = DEVIATION in Phase P audit.
- Token budget: `BRIEF_DW_TOKEN_BUDGET` env var, default 150K (PLACEHOLDER -- recalibrate after 3 instrumented runs, same protocol as INVEST_DW_TOKEN_BUDGET). Main loop reads env and passes `args.token_budget` (the workflow sandbox has no process.env).
- **Adversarial wave (lite; conditional -- NO standing Wave-3)**: a single data-integrity skeptic (read-only Agent dispatch, ~15-20K tokens) fires ONLY when (a) any ADD/TRIM order block is emitted, (b) any thesis shifts to STRESSED/INVALIDATED, or (c) portfolio_health is D/F. It re-derives the dollar math (`shares x (price - prev_close)`), checks order-block prices against quotes, and validates the shift's trigger citation. Fail-closed: refutation -> fix data or downgrade the line to MONITOR + Warning Problems entry; never override (Wave-3 rule). Expected fire rate <20% of mornings. Fires in BOTH topologies (sequential included) since it needs the composed draft; runs between Phase N gate and Phase O writes. Harness-conditional: on `AGENT_TOOL=absent` the main loop performs the SAME re-derivation inline -- recompute `shares x (price - prev_close)`, re-check every order-block price against the Phase D quotes, re-verify the shift's trigger citation -- with identical fail-closed semantics, reported `skeptic: inline (no Agent tool)`; never a DEVIATION.

## Phase B: State-transition model (print only, BEFORE F11)

Emit to stdout the planned state transition. User can abort here pre-F11; zero writes will have occurred.

```
## /brief v2 -- planned state transition

MODE:                [normal|preview|confirm|quick|refresh|no-peripheral]
DATE:                <YYYY-MM-DD>
OUTPUT:              Calendar/decisions/briefings/briefing-<date>[-HHMM].md
COLLISION:           [none|-HHMM variant|--replace overwrite]
MARKET STATUS:       <resolving in Phase D from script last_trading_day>
BROKER COVERAGE:     <read time + covered scope|UNVERIFIED: missing scope>

READS:
  - Current-session broker read evidence (covered accounts/assets + time)
  - Atlas/sources/investing/ref-{monitoring-rules,portfolio-doctrine,geopolitical-framework,market-calendar,macro-landscape}.md
  - Atlas/concepts/investing/{macro-outlook,watchlist,investing-research-log}.md
  - Atlas/concepts/investing/theses/thesis-*.md (5 theses; for invalidation triggers)
  - wiki/hot.md (full body)
  - wiki/entities/tickers/*.md modified <7d (N files; surface entity-level changes)
  - wiki/research/challenges/*.md modified <14d (N files; surface invalidation verdicts)
  - Calendar/decisions/briefings/ last 3 (continuity audit; Brier scoring)
  - Calendar/daily/<today>.md (Phase P pre-write race handling)

WRITES (ATOMIC):
  1. Calendar/decisions/briefings/briefing-<date>[-HHMM].md           [NEW]
  2. Calendar/decisions/briefings/briefing-<date>[-HHMM]-meta.json    [NEW; sidecar]
  3. Calendar/daily/<today>.md (## Market Pulse + linkback)           [UPDATE; sha256-gated outside section]
  4. wiki/hot.md (last_briefing bump + additive pending merge)        [UPDATE; sha256-gated]
  5. Calendar/decisions/sessions-log.md (append entry)                [UPDATE; strictly-additive]
  6. wiki/entities/tickers/<T>.md for each entity in related: (3-7)   [UPDATE; sha256-gated additive]
  7. Calendar/decisions/briefings/brier-ledger.json (append calls; resolve matured) [UPDATE|NEW; machine-owned JSON]

SCRIPT: python tools/fetch-prices.py --equities <list> --crypto <list>

PROCEED? Abort now = pre-F11, zero writes.
```

If `--preview`: stop after Phase N (composition complete in memory); render briefing + meta + audit to stdout; SKIP O-P; F11 never set; exit clean.

If `--confirm`: block for `<owner>` `yes` before Phase C; also block before each Phase P write.

Else: autonomously proceed.

## Phase C: F11 set + Context Load

C.1 -- `mkdir -p .claude/state && touch .claude/state/auto-commit-disabled`. Single flag covers entire invocation.

C.2 -- Parallel context load (READ-only):

- **Portfolio**: obtain current {ticker, shares, cost_basis, account} from available broker read tools. Reconcile account coverage and overlapping positions; unavailable basis/quantities stay UNVERIFIED. Apply corporate-action normalization only when supported by dated evidence. Never read private/ or *.local.md.
- **Constraints/caveats**: current-session user instructions and dated authoritative corporate-action/basis evidence; unresolved basis means no P&L.
- **Refs**: `Atlas/sources/investing/ref-{macro-landscape,monitoring-rules,portfolio-doctrine,geopolitical-framework,market-calendar}.md`. Macro outlook + watchlist + investing-research-log from `Atlas/concepts/investing/`.
- **Theses**: all 5 `Atlas/concepts/investing/theses/thesis-*.md` essays. Extract per-thesis invalidation-triggers list. HALT Phase H if any thesis file missing (structural gap; ask `<owner>`).
- **hot.md**: full body. Extract Last Session + Pending Items + Active Context. Capture `last_briefing:` ISO for continuity context.
- **Entity recency**: `git log --since='7 days ago' --name-only -- 'wiki/entities/tickers/*.md' | sort -u`. For each, Read; extract any thesis-status shifts in body + recent Financial signals entries. Surface in Phase H input.
- **Challenge recency**: `git log --since='14 days ago' --name-only -- 'wiki/research/challenges/*.md' | sort -u`. For each, Read; extract invalidation verdict.
- **Continuity audit (brier-ledger wiring, brief-vnext 2026-07-04)**: Read the WHOLE machine-owned ledger `Calendar/decisions/briefings/brier-ledger.json` (single source of truth for scorable calls; NOT just last-3) plus the last 3 briefings (Glob `Calendar/decisions/briefings/briefing-*.md` sorted; take 3 most recent) for narrative context. For each open ledger call, classify CONFIRMED/SURPRISED/PENDING against today's market state. Brier score `BS = mean((forecast_prob - outcome)^2)`: n>=5 resolved calls in rolling 30d -> full display; n>=3 -> provisional display (`Brier 0.XX (provisional, n=3)`); below 3 -> null. Carry forward `prior_brier_score_30d` (sourced from the ledger) into today's frontmatter; emit calibration footer ("Yesterday: priced-in CPI 3.0-3.3% base 55%; actual 3.1% -> Base HIT"). Ledger absent -> create it in Phase P with today's calls (first-run bootstrap; null Brier). ALSO run `python tools/score-outcomes.py --dry-run --json` (read-only; offline-safe; absent script -> skip silently) and surface `brier_new` / `brier_shadow` / `n_scored` as one footer line: `Invest-side calibration: Brier(new)=0.XX vs shadow 0.XX over n=N`.

C.3 -- Build internal checklist:
- Holdings list with combined-account totals
- Equity/ETF tickers + crypto tickers for Phase D script call
- Per-thesis invalidation criteria (5 lists)
- 7-day catalyst set (FOMC/CPI/earnings/crypto-reg)
- position sensitivity matrix (positions resolved at run time)
- hot.md pending-items count + oldest age
- Entity recency summary; challenge recency summary
- Prior-briefing continuity signal (Brier carry-forward + outstanding priced-in calls)

C.4 -- Today's daily note: do NOT compute `daily_before_sha256` here. Recompute immediately before Phase P Update 1 to handle UserPromptSubmit hook race (hook may append to `## Log` between Phase C and Phase P).

## Phase D: Live Data Fetch

### Phase D.0: DELEGATED dispatch to `price-fetcher` (PREFERRED path; Phase C wiring 2026-05-02)

**MANDATORY** (per Execution Rules; SKIPPED in `--quick` mode per documented exception): dispatch first, no pre-emptive skip outside `--quick`. Subagent wraps `tools/fetch-prices.py` and falls back to per-ticker WebSearch on script failure internally.

**Harness-conditional:** dispatch `price-fetcher` when the harness exposes an Agent tool; when it does NOT, the D.1/D.2 inline `python tools/fetch-prices.py` invocation IS the normal path (reported `mode: inline (no Agent tool)`, not a DEVIATION). On TOPOLOGY=dw the `price-fetcher` leg inside the `brief-research` workflow satisfies this dispatch.

Use the Agent tool with subagent_type `price-fetcher`. Pass input: `{equities: [<EQUITIES from D.1>], crypto: [<CRYPTO from D.1>]}`. Expected return: structured JSON quotes map with `timestamp`, `quotes` (per-ticker `price`, `currency`, `source`, `freshness`, `caveat?`, plus extended-hours fields: `extended_hours_last`, `extended_hours_change_pct`, `extended_hours_volume`, `extended_hours_last_timestamp`, `market_session`, `ah_source`), top-level `extended_hours_movers[]` aggregation, `failures` array.

Validate return: every held ticker present in `quotes` OR `failures`; any transferred-basis entry has a `caveat: "no_pnl"` field; every quote has `market_session` field (pre-market | regular | after-hours | closed); `extended_hours_movers` is always a list (empty when no AH movers above AH_MOVER_THRESHOLD_PCT default 3.0%).

On contract violation OR dispatch failure: fall through to D.2 inline `python tools/fetch-prices.py` invocation. Surface fallback in Phase P audit report.

On dispatch success: skip D.2 inline script invocation; proceed directly to D.3 schema validation using subagent's returned JSON.

### D.1: Inline data prep (always runs)

D.1 -- Build ticker lists from Phase C portfolio + watchlist:
- `EQUITIES = [<dedup equity + ETF tickers across all covered accounts + watchlist>]`
- `CRYPTO = [<dedup crypto tickers without -USD suffix>]`

D.2 -- Execute (Windows: `python`, never `python3`):

```
python <VAULT_ROOT>/tools/fetch-prices.py \
  --equities "<comma-separated EQUITIES>" \
  --crypto "<comma-separated CRYPTO>"
```

D.3 -- Parse JSON. Assert schema presence:
- `indices`: SPX, NASDAQ, DOW, VIX (with `term_structure`), 10Y, DXY, GOLD, OIL
- `equities[]`: price, prev_close, change_pct, rsi14, ma50, ma200, beta, short_ratio, pct_from_52wk_high, next_earnings
- `crypto[]`: price, change_pct
- `signals`: oversold/overbought/below_ma50/below_ma200/earnings_within_10d/high_short_ratio
- `market_status`: open|closed|pre_market|post_market
- `last_trading_day`: ISO date

If schema drift (any field missing): HALT. Do not infer.

D.4 -- Market-hours branching:
- `closed` + weekend (Saturday/Sunday) -> header `Weekend Brief -- data as of <last_trading_day> close`; skip Overnight Earnings; expand Calendar + Scenario Bar; include "Week in Review" one-liner under BLUF
- `closed` + weekday -> `Holiday Brief -- data as of <last_trading_day> close`; treat last_trading_day as frozen
- `pre_market` -> note "Pre-market; prices as of last close"; ONE web search authorized for futures
- `open` / `post_market` -> normal flow

D.5 -- Fallback: if errors array contains >50% of EQUITIES tickers, set `SCRIPT_FALLBACK = true`; web-search for missing prices; annotate "Script fallback -- lower precision" in Intelligence Gaps; force confidence cap to 60% in Phase N.

D.6 -- Compute `script_output_hash = sha256(stdout)` for meta.json.

## Phase E: Regime Detection (day + macro, two-tier)

### Phase E.0: FRED macro fetch (ADD-NOW 2026-06-05; authoritative regime inputs; availability-guarded)

Before classifying, fetch the regime input set from the FRED MCP per `ref-macro-data-sources.md` (sibling of this file): `mcp__fred__fred_get_series` for DGS10, T10Y3M, T10Y2Y, BAMLH0A0HYM2 (HY OAS), VIXCLS, UNRATE (latest + 2-3 prior for trend), CPILFESL (units=pc1), FEDFUNDS, WALCL + RRPONTSYD + WTREGEN (net-liquidity composite, 4wk trend), DTWEXBGS (broad dollar index; the Grade-A macro-regime dollar input -- script DXY stays in the Markets one-liner). Tag provenance `FRED:<series_id> asof <obs_date>` + freshness. The classification TABLES below are UNCHANGED -- FRED only replaces the prior web-search source for the credit/curve/unemployment inputs. **Availability-guard:** on MCP absence/error, SKIP FRED silently and fall back to the Phase D script 10Y/VIX + ONE web search for HY OAS (contract byte-stable; NEVER HALT). Additive DATA-SOURCING only -- does NOT change any regime classification rule or briefing verdict.

**Day regime** (tactical, 6-class). Source VIX from FRED `VIXCLS` + Phase D term-structure, credit from FRED `BAMLH0A0HYM2` (bps); the prior web-search-for-OAS is now the FRED fallback only (VIX > 25 = Risk-off regardless of OAS):

| Regime | VIX | Term | Credit | Section action |
|---|---|---|---|---|
| Crisis | >30 | Backwardation | HY OAS >500bps | Expand portfolio/geo/alerts |
| Risk-off | 20-30 | Flat/Backwardation | OAS widening | Expand portfolio movers + geo |
| Earnings | any | any | normal | Expand earnings |
| Fed Week | any | any | sensitive | Expand calendar + scenario bar |
| Risk-on | <16 | Contango | tightening | Contract alerts; expand deployment |
| Rotation | 16-20 | Contango | stable | Normal; note flow direction |

Report classification + which markers matched (Pattern 11 auditable): `VIX 24.3 [contango], OAS +12bps [widening], XLU/XLP rel-strength +0.8% -> Risk-off`.

**Macro regime** (cycle, 4-class) from yield curve (FRED `T10Y3M`/`T10Y2Y`) + unemployment trend (FRED `UNRATE` latest + priors) + credit spreads (FRED `BAMLH0A0HYM2`) + ISM if available (ISM is NOT on FRED per cap-matrix C6 -- web only; curve+unemployment+credit carry the classification):

| Phase | 10Y-3M | Unemployment | Credit | Leadership |
|---|---|---|---|---|
| Early-cycle | Steep | Falling | Tight/tightening | Cyclicals, small-caps |
| Mid-cycle | Normal | Stable low | Stable | Balanced |
| Late-cycle | Flat/inverted | Stable low | Tight but widening | Defensives, quality |
| Contraction | Re-steepening | Rising | Wide/widening | Bond proxies, gold |

Both regimes go to frontmatter (`regime:` + `macro_regime:`). Transition flag: if `macro_regime` differs from prior-3-briefings mode, mark `macro_regime_transition: true` and surface in Warning Problems.

## Phase F: Signal Dashboard + Markets one-liner

**Markets one-liner** (single line, all from Phase D script):

```
S&P $X,XXX (+/-X.X%) | Nasdaq $XX,XXX (+/-X.X%) | 10Y X.XX% [+/-Xbps] | BTC $XX,XXX (+/-X.X%) | DXY XX.X | VIX XX.X [cont|bkwd] | Oil $XX (+/-X.X%) | Gold $X,XXX
NetLiq $X.XXT [4wk +/-$XXB] | Broad$ XXX.X
```

(NetLiq line from FRED WALCL - RRPONTSYD - WTREGEN per ref-macro-data-sources.md; reported context only -- NOT a regime axis; a legal Warning Problems input when 4wk delta < -$150B. Skip the line silently on FRED absence.)

**Signal Dashboard** (compact table over held equity/ETF positions, 8-12 lines max including header):

| Ticker | Price | Chg% | AH/PM | RSI | vs 50MA | vs 52wk H | Beta | Signal |

The **AH/PM** column renders when ANY held position has `market_session != "regular"` (i.e., AH session active globally) OR when individual ticker has non-null `extended_hours_change_pct`. Format:
- `+X.X% AH` (after-hours change_pct, signed; AH session)
- `+X.X% PM` (pre-market change_pct, signed; PM session)
- `$X (untraded)` (market_session in AH/PM but `extended_hours_volume == 0`; rare; signal = ticker has AH session but untraded that minute)
- `-` (regular session OR market closed; column dropped if NO held position has AH/PM data globally)

Signal logic:
- RSI <30 AND price > 200MA -> `OVERSOLD` (cite ~73% bounce base rate when regime is non-bear)
- RSI >70 -> `OVERBOUGHT`
- price < 50MA AND price < 200MA -> `WEAK`
- earnings <=10 trading days -> `PRE-EARN Nd`
- short_ratio >5 -> `HIGH-SHORT`
- `ah_movers` ticker (i.e., abs(extended_hours_change_pct) >= 3%) -> `AH-MOVER` (combines with other signals: `AH-MOVER + PRE-EARN 2d`)
- multi-signal -> combine: `WEAK + PRE-EARN 7d`
- else -> `NEUTRAL`

Section budget: 8-12 lines. If >8 held positions, only render non-NEUTRAL rows; else render all (no hiding).

## Phase G: Cross-Asset Coherence Check

Classify session as one of three:

- **coherent-risk-on**: equities up, credit tight/tightening, rates up (growth bid), USD down, gold down, VIX down, BTC up
- **coherent-risk-off**: equities down, credit wide/widening, rates down (flight to safety), USD up, gold up, VIX up, BTC down
- **divergent**: any material dissent between signals

If divergent: emit Warning Problems entry with specifics. Example: `Equity up, credit widening, gold up -- dissent between equity rally and risk signals; idiosyncratic sector move OR regime transition in progress`.

Frontmatter field: `cross_asset_coherence: <coherent-on|coherent-off|divergent>`. Divergent sessions historically precede regime shifts; flagging is the point.

## Phase H: Thesis Status Board (NEW v2; binary per-thesis)

For each of the 5 active theses (theme-alpha, theme-beta, theme-gamma, theme-delta, theme-epsilon), evaluate status against invalidation triggers from `Atlas/concepts/investing/theses/thesis-<slug>.md` (loaded Phase C):

| Thesis | Status | Evidence |
|---|---|---|
| theme-alpha | HEALTHY / WATCH / STRESSED / INVALIDATED | <specific trigger state, one line; when a capex-cut exit-ladder leg is armed, append `exit-ladder: <tier>` per ref-portfolio-doctrine> |
| theme-beta | ... | ... |
| theme-gamma | ... | ... |
| theme-delta | ... | ... |
| theme-epsilon | ... | ... |

Binary per Pattern 7. Definitions:
- **HEALTHY**: no invalidation signals; thesis confirmed by recent data
- **WATCH**: signal present but below trigger threshold
- **STRESSED**: trigger threshold crossed, pre-invalidation
- **INVALIDATED**: thesis premise broken

**Machine-trigger evaluator (thesis machine-triggers schema v1; ratified Block A 2026-07-04)**: when a thesis essay carries a `triggers:` frontmatter block, evaluate BEFORE judgment-layer prose reasoning:
- Parse `triggers:` (kill/red/amber/manual rows; schema v1 per proposal-thesis-machine-triggers-2026-06-10). Evaluate every kill/red/amber whose `source` resolves from data already in hand (Phase D script quotes, E.0 FRED, J.6 openinsider). `manual:` rows are never evaluated.
- Status FLOOR derivation (floors combine with prose judgment; judgment may worsen but never improve below the floor): any kill fired -> STRESSED minimum (INVALIDATED stays a human call via /challenge); >=1 red fired -> WATCH minimum + Warning Problems entry; >=1 amber fired -> WATCH candidate.
- Render per-trigger state in the Status Board Evidence cell (e.g. `<trigger-id>: FIRED <date>, /decide pending`) + a staleness line per thesis: `manual: N unevaluated (oldest review <date>)`.
- **Write-back of `fired:` is Pattern-20-gated**: /brief NEVER edits Atlas. A newly-observed fire emits a FOLLOWUPS:skills line (`/decide -- trigger <id> fired; ratify fired-date write-back`) and the write lands in the confirmed session. Evaluation itself is read-only.
- Back-compat: thesis essay without a `triggers:` block -> prose-judgment evaluation exactly as before (zero behavior change).
- **GATE-T adjudication (judgment-gates kit, 2026-07-06)**: `manual:` rows and evidence-interpretation triggers (`source: manual` / `window: earnings_window`) are never machine-evaluated. When the prose judgment layer proposes a thesis-status change (either direction) resting on such a trigger, a same-day GATE-T sheet is REQUIRED: run the GATE-T procedure per `.agents/skills/gate/ref-gate-tables.md` (fill evidence markers with provenance, `python <VAULT_ROOT>/tools/gate-eval.py --compute` -- never judge the verdict -- write the sheet to `wiki/research/gates/`, `--check`, registry row), and cite the sheet in the Evidence cell. FIRED backs the status floor (the `fired:` write-back stays Pattern-20-gated via /decide FOLLOWUP; the sheet is its evidence record). INSUFFICIENT-EVIDENCE -> status unchanged + evidence-collection EOD row. NOT-FIRED -> status unchanged; the sheet prevents re-litigating the same evidence daily. N/A in --quick (H-lite has no prose judgment layer). Enforced by HALT item 22a.

**Alert emission (T4 push channel one; 2026-07-04)**: after trigger evaluation, compute `alerts_fired` = newly-observed fires ONLY (condition evaluates true AND no `fired:` date recorded in the essay frontmatter; recorded-fired rows re-render in the board but NEVER re-alert -- alarm-fatigue guard). For each entry `{id: "<thesis>-<trigger-id>-<YYYY-MM-DD>", trigger, thesis, class, detail, push}`:
- Send PushNotification: one line, trigger id + thesis + observed value vs threshold (+ dollar exposure when in hand). Tool unavailable/failed -> `push: "failed"`, continue (never HALT the briefing on the alert leg). Interactive sessions may return not-sent/terminal-active (harness dedup; the alert reaches the user in-session) -> `push: "skipped-active"`, delivery-equivalent.
- Append `<ISO-8601> <id> push=<requested|failed|skipped-active> <detail>` to `.claude/state/alerts-delivered.log` (the X75 delivery receipt; `tools/open-loops.py` matches on the id substring against this file).
- `alerts_fired` lands in meta.json (schema v2 field). Empty list when no new fires: no push, log untouched.

**H-lite (--quick mode)**: `--quick` runs ONLY the machine-trigger evaluator + alert emission from this phase -- no prose Thesis Status Board body section; `thesis_statuses` frontmatter + sidecar still emitted (floor-derived where triggers resolve, prior-briefing carry-forward elsewhere, carry-forward rows suffixed `(carry)`). Triggers whose `source` data is not in hand under the quick fast path (E.0 FRED skipped, J.6 skipped) render `not-evaluated (quick)` and are NEVER treated as fired. This is the scheduled pre-market lane's alerting spine (`tools/run-morning-brief.cmd`).

Frontmatter: `thesis_statuses: {theme-alpha: HEALTHY, theme-beta: WATCH, ...}`.

Action: any thesis shifting HEALTHY -> WATCH (or worse) emits `/challenge thesis-<slug>` to FOLLOWUPS:skills + Warning Problems entry.

Failure: all 5 thesis files missing -> HALT Phase H with explicit error; ask `<owner>` (structural gap).

## Phase I: Overnight Earnings + Geopolitical (conditional; skip when absent)

**Overnight Earnings**: skip section entirely if no held/watchlist position reported. For each reporter:
- EPS actual vs consensus, surprise %
- Revenue actual vs consensus, surprise %
- Guidance: raised/maintained/lowered vs prior + vs consensus
- Pre-market reaction %
- Thesis implication: CONFIRM or CHALLENGE (NEUTRAL only when truly absent both ways)
- PEAD direction (5-60d post-earnings drift magnitude per academic literature)
- Peer-constellation signal (e.g., "SK Hynix beat -> positive PEAD signal for MU")

**Geopolitical**: CFA 3-stage filter from ref-geopolitical-framework.md:
1. Event detection
2. Transmission mapping (`EVENT -> POLICY -> MARKET -> SECTOR -> POSITION`)
3. Classification: SUPPLY (include) or SENTIMENT (skip unless FLASH-level)

Cross-reference position sensitivity matrix (positions resolved at run time). Skip section entirely if nothing survives both filter and threshold.

## Phase J: Portfolio Impact

### Extended-Hours Movers (subsection; renders BEFORE regular movers when `extended_hours_movers[]` non-empty)

When the price-fetcher subagent returns top-level `extended_hours_movers[]` non-empty, render a dedicated table BEFORE the regular Portfolio Impact table:

| Ticker | Session | AH Move | $ Impact (regular close -> AH last) | So What | Now What |

- **Session**: pre-market | after-hours
- **AH Move**: signed magnitude_pct from quote (e.g., `+5.4% AH`); include `last_timestamp` parenthetical if recent (e.g., `+5.4% AH (19:59 ET)`)
- **$ Impact**: `shares_held * (extended_hours_last - regular_close)` EXACT; cross-account combined only from verified quantities; current-value change is distinct from P&L and carries basis caveats
- **So What**: thesis CONFIRM/CHALLENGE/NEUTRAL using AH price as evidence; cite specific invalidation trigger if CHALLENGE
- **Now What**: NO ACTION (AH transient) / MONITOR pre-open / REVIEW THESIS at open. Order blocks NOT embedded for AH movers (AH liquidity thin; defer to regular-session execution unless user explicitly requests AH limit order)

**Quiet-day suppression interaction**: if any `extended_hours_movers[]` entry has `abs(magnitude_pct) >= 5.0`, suppress the regular quiet-day BLUF redirect (AH-quiet != regular-quiet); render full briefing.

**Pre-Output explicit-absence**: if `market_session != "regular"` for ALL held positions AND `extended_hours_movers[]` is empty, render: `[Extended-hours session active: no material movers above 3.0% threshold across held positions]`.

### Regular session table (positions moving >1%):

| Ticker | What ($ impact, exact) | So What (thesis CONFIRM/CHALLENGE) | Now What |

- **Dollar impact**: `shares_held * (price - prev_close)` EXACT. Cross-account positions combined.
- **Beta-adjusted impact** for thesis-level events: `position_impact * beta`.
- **So What**: thesis status; if CHALLENGE, cite specific invalidation trigger from ref-portfolio-doctrine.md.
- **Now What**: NO ACTION / MONITOR `<trigger>` / ADD @$X / TRIM @$X / REVIEW THESIS. If ADD or TRIM, embed copy-paste-ready order block:

```
ORDER (confirm at broker):
SELL <N> shares <TICKER> @ $<price> LIMIT
```

Crypto movers carrying the `no_pnl` caveat report current value-delta only: `<SYMBOL> $X.XX (+X.X%): ~$X delta on N tokens. P&L NOT REPORTED -- cost basis not established.`

Any mover with a recent split: report pre-split + post-split prices; share count uses post-split.

**Portfolio Health grade** (A-F):
- **A**: all theses HEALTHY, no concentration issues
- **B**: 1 thesis WATCH OR minor concentration drift
- **C**: 2+ theses WATCH OR notable concentration
- **D**: any thesis STRESSED
- **F**: any thesis INVALIDATED OR crisis-level drawdown

Frontmatter: `portfolio_health: <A|B|C|D|F>`.

### Phase J.6: Insider overlay (openinsider; NEW brief-vnext 2026-07-04)

- TOPOLOGY=dw: folded into the Wave-1 FRED/macro worker as a second tool-call pair. Sequential: two direct MCP calls.
- `mcp__openinsider__top_buys` + `mcp__openinsider__top_sells` (window: trailing week), INTERSECT against held + watchlist tickers only. Render 0-3 lines max inside Portfolio Impact: `INSIDER: <TICKER> cluster buy $X.XM by N insiders [Grade B | openinsider | date] -> <one-phrase So What>`. Empty intersection -> render nothing (quiet-day discipline; no padding).
- Availability-guard: MCP absent/error -> skip silently; note in Intelligence Gaps only if a held ticker had a known pending Form-4 storyline. `--quick` skips. This is the /brief-scale sibling of /invest Phase J-bis -- deliberately NOT dispatching institutional-positioning-scout daily (cost discipline; the scout remains /invest's depth tool).

## Phase K: Calendar (7d) + Pre-Earnings Monitor + Scenario Bar

**Calendar (7 days)**: from ref-market-calendar.md + script `earnings_within_10d` + 0-1 web search for gaps. Each event:
- Date + name
- Conditional framing: `If hot X -> implication A; if soft Y -> implication B`
- Historical one-liner: avg move last 3 occurrences if data available

Include FOMC, CPI/PPI/jobs, held/watchlist earnings, corporate-action dates, crypto regulatory dates.

**Pre-Earnings Monitor**: for each held with earnings <=10 trading days (script signals.earnings_within_10d):
- Countdown: `[TICKER] earnings in X trading days (<date>)`
- Consensus: EPS $X.XX, Revenue $X.XB
- 30-day analyst revision trend (up/down/flat)
- Historical pattern from ref-portfolio-doctrine.md (e.g., a name's historical post-earnings pattern)
- Implied move from options if findable
- PEAD peer signal direction

**Scenario Bar** (ONLY for highest-conviction catalyst within 7d; SINGLE, not multiple):

```
SCENARIO BAR: CPI Mar (2026-04-15)
Bull (25%): <3.0% -> 10Y to 4.15%, <fund> +$XX
Base (55%): 3.0-3.3% -> muted, +/-$XX
Bear (20%): >3.3% -> 10Y to 4.50%, <fund> -$XX
Expected Value: +$XX
```

Probabilities sum to 100%. Dollar impacts from actual share counts. EV = probability-weighted sum.

Each scenario writes to frontmatter `priced_in_calls:` as structured list:

```yaml
priced_in_calls:
  - event: "CPI Mar 2026"
    date: 2026-04-15
    bull_prob: 25
    base_prob: 55
    bear_prob: 20
    trigger_level: "3.0-3.3% YoY core"
```

This is the input for tomorrow's Brier scoring (Phase C continuity audit).

If no material catalyst within 7d: skip section entirely.

## Phase L: Intelligence Gaps + Warning Problems

**Intelligence Gaps** (known unknowns; 1-3 bullets max). Format: `GAP: <unknown>. Impact: <why it matters>. Resolve: <how to fix>`.

Skip section entirely on quiet days (suppression triggers met). Only emit "No material intelligence gaps." when truly absent (not as filler).

**Warning Problems** (IC convention; NEW v2). Distinct from Gaps:
- Gaps = "I don't know X"
- Warnings = "I know X and it matters, but it's below the trigger"

Emit Warning Problems for:
- Divergent cross-asset coherence (from Phase G)
- Macro regime transition (from Phase E)
- Thesis moving HEALTHY -> WATCH (from Phase H)
- Concentration drift past doctrine trigger (theme-alpha >60% amber / >70% red [interim 50% phase-in]; any other thesis >40%; any single name >30% -- per ref-portfolio-doctrine.md)
- Any Phase D script error affecting >1 held position

Format: `WARNING: <signal>. Base rate: <historical context>. Trigger: <what would escalate to action>`.

## Phase M: Optionality Map + Today's Focus + FOLLOWUPS:skills

**Optionality Map** (concrete deployable optionality):
- Available cash: `$X per covered account (current-session broker read)`
- Positions at action zones: `<ticker at $X vs entry zone $Y-Z from watchlist.md>`
- Pre-registered watch zones (DISPLAY ONLY, 2026-07-30): render the `watch_zone:` block from each name's LATEST `wiki/investing/analyses/<ticker>-analysis-*.md` frontmatter as one line each -- `<TICKER> watch zone <low>-<high> (set <date>, expires <date>); spot <px> <inside|above|below>`. No evaluator, no alert, no artifact: /brief displays the zone, it never fires on it (contract: ref-analysis-template 6.1.3).
- Pending decisions from hot.md: count + oldest age
- Yesterday's commitments: `X/Y completed` from prior daily-note `## Commitments` checkbox count; list any carried forward

**Today's Focus** (1-3 specific actions tied to what THIS briefing surfaced). Each with time-to-decision marker: `WITHIN 30 MIN OF OPEN` / `BEFORE FOMC 2PM` / `EOW`. No generic advice.

**FOLLOWUPS:skills block** (Pattern 18 coordination; analog to /invest INGEST:claims):

```markdown
<!-- FOLLOWUPS:skills -->
- /invest <ticker> -- export-control signal pressures the theme-alpha thesis (trigger: WITHIN 48H if confirmed by Commerce Dept)
- /challenge thesis-theme-alpha -- theme-alpha effective exposure <pct> approaching the interim amber (trigger: EOW)
- /networth -- portfolio value delta >5% since last snapshot; refresh recommended
- /decide -- a trim trigger fired; structured decision record if action taken
- /retro -- queue at session end if substantive trades/decisions emerge
<!-- /FOLLOWUPS:skills -->
```

Empty case: render `(no followup skills recommended)` between tags. Do NOT emit a skill without a concrete one-line rationale tied to briefing body. Downstream /retro must be able to parse this block.

## Phase N: Pre-Output HALT Gate (22-item)

Assert each item below before any Write. Any failure -> HALT, report which item failed, no writes, no commit, F11 stays on. Gate runs in memory; Phase O does the writing.

1. BLUF is a judgment with numbers + dollar impact, not a summary
2. Counter line present (Tenth Man; specific evidence cited, not canned opposite)
3. Priced-In line states expectations + what would surprise, OR explicitly skipped (nothing material)
4. Alternative Analysis present -- a third-order scenario with evidence (not just bear vs bull)
5. Dollar impacts computed from `shares_held * (price - prev_close)` exact; no estimates
6. Signal Dashboard uses exact Phase D data
7. Every data point has explicit date; no bare "recently / today / currently"
8. Day regime classified via Phase E table; markers cited
9. Macro regime classified; transition flagged if shifted
10. Cross-asset coherence classified (coherent-on/coherent-off/divergent)
11. Thesis Status Board complete (all 5 theses; binary statuses)
12. >=1 contradictory/risk item surfaced if any position moves >2%
13. Evidence grades on material claims `[Grade A-F | source | date]`
14. Geopolitical items passed CFA 3-stage filter (or correctly excluded)
15. Forward-looking uses % confidence, not HIGH/MEDIUM/LOW
16. Empty sections skipped entirely; no "nothing to report" padding
17. Intelligence Gaps flagged if any Phase D error OR >1d stale data
18. Warning Problems emitted if any divergent / transition / thesis-shift / script-error triggered
19. Pre-Earnings Monitor for all positions <=10 trading days (script signals)
20. P&L NOT reported for any `no_pnl`-flagged position (cost basis not established)
21. Cross-account holdings report combined exposure (the roster is read from the broker at run time)
22. Total briefing body <=650 words (3-minute rule); --quick mode <=200 words
22a. GATE-T adjudication (Phase H): every thesis-status change resting on a manual/evidence trigger carries a same-day GATE-T sheet (checked via gate-eval.py, cited in the Evidence cell). No such change -> N/A; --quick -> N/A.

**Evidence-grade confidence cap (separate precondition on frontmatter `confidence:`)**:
- >30% of inline grades are Grade C -> cap 70%
- Any Grade-D in body -> cap 60%
- >2 STALE data points (>7d) driving decision -> cap 65%
- Script fallback mode active -> cap 60%
- Price provenance (C5 mirror of /invest Pre-Output Gate 6a): if the quote feeding any dollar-impact line was non-broker (price-fetcher `broker_authoritative: false`) during `market_session == regular` -> cap 60% + flag "price-unconfirmed (non-broker)" in the briefing header. N/A outside regular session; applies to every harness with a regular-session quote.

If frontmatter `confidence:` exceeds applicable cap: HALT; `<owner>` must authorize override explicitly.

**ASCII pre-write scan (Pattern 22)**: apply Part III sec 3.4 replacement table to all NEW content; byte-scan; HALT on any byte > 127 (modulo pre-existing legacy in unmodified body sections).

**FOLLOWUPS:skills sanity**: each emitted skill has concrete one-line rationale tied to briefing body; no skill without body evidence.

**Priced-in calls schema**: each scenario probability + trigger present in frontmatter structured list (input for tomorrow's Brier scoring).

## Phase O: Compose briefing + meta.json sidecar

O.1 -- Read `ref-output-template.md` (sibling of this file) for canonical frontmatter schema, body section order, and meta.json sidecar spec. Do not emit until ref loaded.

O.2 -- Write briefing to `Calendar/decisions/briefings/briefing-<YYYY-MM-DD>[-HHMM].md`.

**Canonical frontmatter** (full schema):

```yaml
---
categories: [decisions]
type: briefing
date: YYYY-MM-DD
regime: <day classification>
macro_regime: <cycle phase>
macro_regime_transition: <true|false>
cross_asset_coherence: <coherent-on|coherent-off|divergent>
portfolio_health: <A|B|C|D|F>
confidence: <integer 0-100>
confidence_cap_rule: <none|grade-c-30pct|grade-d-any|stale-2plus|script-fallback|price-unconfirmed>
conviction: <low|medium|high>
topology: <dw|sequential>
orchestrator_model: <resolved model id; passive>
thesis_statuses:
  theme-alpha: <HEALTHY|WATCH|STRESSED|INVALIDATED>
  theme-beta: <...>
  theme-gamma: <...>
  theme-delta: <...>
  theme-epsilon: <...>
priced_in_calls:
  - event: <name>
    date: YYYY-MM-DD
    bull_prob: <int>
    base_prob: <int>
    bear_prob: <int>
    trigger_level: <number with unit>
prior_brier_score_30d: <float or null; SOURCED FROM brier-ledger.json; n>=3 provisional, n>=5 full>
positions_at_action_zones: [<ticker>@<price>, ...]
followup_skills_count: <int>
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: complete
tags: [topic/market-brief]
related: [[hot]], [[<materially-discussed-entities-3-7>]], [[<thesis-slugs-invoked>]]
---
```

**Body section order** (skip empty sections entirely; conform to ref-output-template.md updated for v2):

1. H1 title + Generated stamp + flags (Weekend|Holiday|Pre-Market|Intraday) + BROKERAGE_WARN if applicable
2. BLUF / Counter / Alternative
3. Day Regime / Macro Regime / Cross-Asset Coherence / Portfolio Health / Priced In
4. Markets one-liner
5. Signal Dashboard
6. Thesis Status Board
7. Overnight Earnings (conditional)
8. Portfolio Movers (What/SoWhat/NowWhat; copy-paste order blocks if action)
9. Pre-Earnings Monitor (conditional)
10. Geopolitical (conditional; CFA-filtered)
11. Alerts (FLASH/PRIORITY per ref-monitoring-rules.md)
12. Calendar (7 days)
13. Scenario Bar (conditional; highest-conviction only)
14. Intelligence Gaps
15. Warning Problems
16. (Reserved: a personal section not included in this copy)
17. Vault
18. Optionality Map
19. Today's Focus (1-3 with time-to-decision markers)
20. FOLLOWUPS:skills block
21. Footer: Prior-day calibration line (one line from continuity audit) if Brier scoring active

O.3 -- Write meta.json sidecar at `Calendar/decisions/briefings/briefing-<YYYY-MM-DD>[-HHMM]-meta.json`:

```json
{
  "schema_version": 2,
  "briefing_date": "YYYY-MM-DD",
  "generated_at": "YYYY-MM-DDTHH:MM:SS",
  "mode": "<normal|quick|refresh|...>",
  "topology": "<dw|sequential>",
  "orchestrator_model": "<resolved model id; passive>",
  "net_liquidity": {"walcl": null, "rrp": null, "tga": null, "composite_t": null, "delta_4wk_b": null},
  "insider_overlay": [<0-3 rendered INSIDER lines as objects; [] when empty/skipped>],
  "alerts_fired": [<newly-observed machine-trigger fires this run: {id, trigger, thesis, class, detail, push}; [] when none -- X75 pairs each id against .claude/state/alerts-delivered.log>],
  "priced_in_outcomes": [<resolved ledger calls this run: {event, outcome, brier_contrib}>],
  "script_output_hash": "<sha256 of fetch-prices.py stdout>",
  "indices_snapshot": {<indices block from script>},
  "equities_snapshot": [<equities block>],
  "crypto_snapshot": [<crypto block>],
  "web_searches": [{"query": "...", "url": "...", "grade": "B"}],
  "regime_markers": {"vix": 24.3, "term": "contango", "oas_bps": 412, "classification": "risk-off"},
  "macro_regime_markers": {"yield_curve_10y_3m_bps": -8, "unemployment_trend": "stable_low", "credit_spreads": "tightening", "classification": "late-cycle"},
  "thesis_statuses": {"theme-alpha": "HEALTHY", "...": "..."},
  "priced_in_calls": [<structured list; tomorrow's Brier scoring input>],
  "confidence": 75,
  "confidence_cap_rule": "none",
  "followup_skills": [<structured list>],
  "phases_timing_ms": {"A": 12, "B": 3, "...": 0},
  "pre_output_gate_results": {"item_1_bluf_judgment": "PASS", "...": "PASS"}
}
```

Sidecar enables machine-parseable retrospective scoring + calibration feedback + audit by future /retro runs. Always written alongside briefing.

O.4 -- ASCII pre-write pass on briefing body + sidecar; HALT on any byte >127 in NEW content.

## Phase P: Peripheral atomic updates + Commit + F11 clear + Audit Report

### Phase P.0: DELEGATED pre-commit dispatch to `vault-classifier-sweep` (PREFERRED gate; Phase C wiring 2026-05-02)

**MANDATORY** (per Execution Rules; SKIPPED in `--quick` mode per documented exception): dispatch first, no pre-emptive skip outside `--quick`. **Harness-conditional:** when the harness exposes no Agent tool, run `python tools/vault-audit.py --json` inline as the NORMAL path against the identical score/gate thresholds (reported `mode: inline (no Agent tool)`, not a DEVIATION).

Use the Agent tool with subagent_type `vault-classifier-sweep`. Pass input: `{scope: "all"}`. Expected return: JSON with 9 classifier keys + `totals` + `score` + `score_floor_check`. If `score_floor_check: BREACH` (<90) OR `gate >0`: HALT before atomic apply; surface findings; user must repair before /brief peripheral writes can proceed.

Validate subagent return per its contract; on failure fall through to direct `python tools/vault-audit.py` invocation as fallback gate. Surface dispatch outcome in Phase P audit.

### Phase P.1: Peripheral atomic updates (continues unchanged below)

All four non-briefing updates MUST succeed. Mid-batch failure -> Pattern 13 F.halt: abort remaining writes, F11 stays on, structured report (succeeded / failed / not-attempted), `<owner>` decides (rollback via `git checkout -- <paths>` or fix-and-retry with idempotency).

**Update 1: `Calendar/daily/<today>.md` `## Market Pulse` section**

- Re-Read AT THIS MOMENT (UserPromptSubmit hook may have appended `## Log` entries since Phase C)
- Compute `daily_before_sha256` (from re-read body)
- Replace entire `## Market Pulse` section body with: `**BLUF:** <BLUF>. **Regime:** <day>/<macro>. **Coherence:** <class>. **Health:** <grade>. **Confidence:** <N>%. Full briefing: [[briefing-<date>[-HHMM]]]`
- Compute `daily_after_sha256`
- Assert: body outside `## Market Pulse` section byte-exact (compare non-section segments)

**Update 2: `wiki/hot.md`**

- Read; `hot_before_sha256`
- Bump `last_briefing:` to today's ISO
- Merge pending items additively: any FOLLOWUPS:skills entries with concrete triggers not already present in Pending Items get appended (no removals; Pattern 12 idempotency aligned with /retro spec)
- Bump `updated:` to today
- Compute `hot_after_sha256`; assert diff is strictly-additive outside frontmatter field bumps

**Update 3: `Calendar/decisions/sessions-log.md`**

Append structured entry (canonical schema):

```
### YYYY-MM-DD[-HHMM] -- /brief
Domain: investing
Day regime: <class>
Macro regime: <phase>
Portfolio Health: <grade>
Confidence: <N>%
BLUF: <one-line>
Thesis shifts: <list of HEALTHY->WATCH transitions OR "none">
Followup skills: <count>
Artifact: [[briefing-<date>[-HHMM]]]
```

**Update 4: `wiki/entities/tickers/<T>.md` for each entity in briefing `related:`**

- SCOPE: only entities in briefing `related:` field (3-7 typical), NOT every ticker mentioned in body. Keeps fan-out bounded; consistent with /invest analysis-to-entity back-link discipline.
- For each entity:
  - Read; `entity_before_sha256`
  - Append under Recent section (create if absent): `- [YYYY-MM-DD] Mentioned in [[briefing-<date>[-HHMM]]] -- <one-phrase context>`
  - Bump `updated:` to today
  - Compute `entity_after_sha256`; assert strictly-additive diff

**Update 5: `Calendar/decisions/briefings/brier-ledger.json` (machine-owned; brief-vnext 2026-07-04)**

- Schema: `{calls: [{event, date, bull_prob, base_prob, bear_prob, trigger_level, source_briefing, outcome: null|bull|base|bear, resolved_date, brier_contrib}], rolling_30d: float|null}`. Create file on first run.
- APPEND today's new `priced_in_calls` entries (source_briefing = today's briefing stem; outcome null).
- RESOLVE any open call whose event date has passed: score outcome from Phase D actuals (CPI prints, FOMC, earnings reactions); resolution is a one-line judgment with the evidence cited in the sidecar; set `resolved_date` + `brier_contrib`; recompute `rolling_30d`.
- Machine-owned JSON (precedent: meta.json sidecars already live under Calendar/); body-preservation N/A; stdlib-json parse gate before write.

```
brief(daily): YYYY-MM-DD[-HHMM] -- <regime> day, <macro_regime> macro, <health> health

Briefing at Calendar/decisions/briefings/briefing-<date>[-HHMM].md
Meta sidecar at briefing-<date>[-HHMM]-meta.json

BLUF: <one-line>
Day regime: <class> (VIX <X> [cont|bkwd], OAS <Xbps>, ...)
Macro regime: <phase> (<curve, unemp, credit>)
Cross-asset coherence: <class>
Portfolio Health: <grade>
Confidence: <N>% (cap: <rule or none>)
Conviction: <level>
Thesis statuses: theme-alpha=<X>, theme-beta=<X>, theme-gamma=<X>, theme-delta=<X>, theme-epsilon=<X>
Followup skills: <count>
Prior 30d Brier score: <float or n/a>

Peripheral atomic updates:
 - Calendar/daily/<today>.md  (Market Pulse summary + linkback)
 - wiki/hot.md  (last_briefing bump; additive pending merge)
 - Calendar/decisions/sessions-log.md  (structured entry)
 - wiki/entities/tickers/*.md  (<N> symmetric back-links)
```

**F14 narrow stage** each file explicitly. **Never** `git add -A` / `git add .`.

**Post-commit F17 verify**: `git log -1 --format='%B' HEAD | grep -c '^Co-Authored-By:'` must equal 0. If found, HALT; ask `<owner>` (do NOT silently proceed).

**Clear F11**: `rm .claude/state/auto-commit-disabled`. Assert absence.

**Audit Report** (stdout to `<owner>`):

```
## /brief v2 run complete

Briefing:           briefing-<date>[-HHMM].md
Meta sidecar:       briefing-<date>[-HHMM]-meta.json
Day regime:         <class> (markers: VIX=X term=X OAS=X)
Macro regime:       <phase> (curve=X unemp=X credit=X)
Cross-asset:        <coherent-on|coherent-off|divergent>
Portfolio Health:   <grade> (<justification>)
Confidence:         <N>% (cap rule: <none|grade-c-30pct|grade-d-any|stale-2plus|script-fallback>)
Conviction:         <level>
Thesis statuses:    theme-alpha=<X>, theme-beta=<X>, theme-gamma=<X>, theme-delta=<X>, theme-epsilon=<X>
Thesis shifts:      <list or "none">

Files written:      5 + 1 sidecar + <N> entity back-links = <total>
Entity back-links:  <list of tickers>
Followup skills:    <count> (<skill names>)

Script status:      <ok|fallback|errors on: X,Y>
Web searches:       <count>
Pre-Output gate:    22/22 PASS
F11:                cleared
F17:                Co-Authored-By absent
Working tree:       clean

Prior-day calibration: <one-line from continuity audit, or "n/a (insufficient prior calls)">
```

## Pattern 21 / Standing Rule 16 -- companion refs (created)

The following ref docs EXIST on disk as SIBLINGS of this file, as companion reference material (each 60-77KB, built via Deep Research per Standing Rule 16). Consult them when the inline procedural depth is insufficient for a deep-dive:

- `ref-regime-taxonomy.md` -- full day + macro regime taxonomy, transition matrices, historical base rates
- `ref-evidence-hierarchy.md` -- Grade A-F evidence rubric, freshness tiers, contradiction tiering
- `ref-briefing-structure.md` -- PDB ICD 203 + hedge fund morning note structural taxonomy

SKILL.md v2 covers their content inline at procedural depth: 6-regime table in Phase E, 4-class macro table also Phase E, Grade A-F rubric in Quality Rules (formerly Quality Standards), briefing structure in ref-output-template. Keep procedural depth inline as the operative path; the companion refs carry the extended taxonomy for deep-dives.

## Failure Taxonomy -- see ref-brief-operations.md Section 2. HALT semantics (F.halt, F11-stays-on, F17) are normative there.

## Coordination -- see ref-brief-operations.md Section 3 (shared infra + division-of-concerns matrix + consumers)

## Examples -- see ref-brief-operations.md Section 1 (8 worked mode examples)

## Ref docs (all siblings of this file unless pathed)

- `ref-output-template.md` (v2; consumed in Phase O for canonical frontmatter + body section order + meta.json sidecar spec + daily-note linkback pattern)
- `ref-macro-data-sources.md` (ADD-NOW 2026-06-05; consumed in Phase E.0 for the FRED series catalog incl. net-liquidity composite + day/macro regime mappings + availability-guard pattern + C6/C8 caveats)
- `ref-brief-operations.md` (brief-vnext Diff 1 extraction 2026-07-04; Section 1 worked examples, Section 2 failure taxonomy [HALT semantics normative], Section 3 coordination matrix + consumers)
- `.claude/workflows/brief-research.js` (TOPOLOGY=dw Wave-1 acquirer bundle; invoked per Phase A.8)

Companion reference docs (Pattern 21; siblings of this file -- extended taxonomy consulted when inline procedural depth is insufficient):
- `ref-regime-taxonomy.md` (day + macro regime taxonomy, transition matrices, base rates)
- `ref-evidence-hierarchy.md` (Grade A-F rubric, freshness tiers, contradiction tiering)
- `ref-briefing-structure.md` (PDB ICD 203 + morning-note structural taxonomy)

## Related skills

- `/networth` -- portfolio snapshot complement (Phase 15 portfolio refresh from /brief v1 retired here)
- `/invest <ticker>` -- per-ticker analysis triggered by FOLLOWUPS
- `/challenge thesis-<slug>` -- thesis stress-test triggered by status shift in Phase H
- `/decide` -- structured decision record if action proposed in Phase J Now What
- `/retro` -- session-end retrospective consumes /brief sessions-log entry


## Phase O.0 -- Pre-commit /vault audit gate (v2.0; CAT-3 prevention-architecture parity)

After composing all target file modifications IN MEMORY but BEFORE atomic write:
1. Write each composed file to a tmp dir under `wiki/research/test-tmp/.precheck/brief-<slug>/`
2. Run `python tools/skill-precheck.py <tmp-files...> --skill /brief`
3. Parse exit code: 0 -> proceed; 2 -> HALT with diagnostic
4. Body-scope wikilink validation: per /retro v2.2 Phase D pattern, scan composed body text for unresolved `[[<target>]]` and mechanically de-link unresolved targets (vault-resolved keep / MEMORY_PREFIXES rewrite as `[[memory:<stem>]]` / placeholder leave / else strip). Fence-aware (skip ``` fenced + `inline code`).
5. Bypass: `CLAUDE_VAULT_BYPASS_VALIDATOR=1` (logged to `.claude/state/bypasses-`<date>`.log`)

Defense-in-depth on top of PreToolUse pre-write-validator.py + PostToolUse wikilink-check.py / frontmatter-check.py / orphan-check.py. The Phase O.0 gate prevents broken composition from reaching disk in the first place.

**/brief-specific risk:** /brief writes to ~5 append-mode files daily (sessions-log + hot.md + daily + 3-7 entity back-links) -- highest write-fanout among HIGH-risk skills.
