---
categories: [sources]
type: reference
created: 2026-06-09
updated: 2026-06-09
status: active
confidence: high
tags:
  - topic/investment-analysis
  - topic/dynamic-workflows
  - topic/concurrency
  - topic/adversarial-verification
related:
  - "[[invest]]"
  - "[[ref-analysis-template]]"
  - "[[ref-entity-update-semantics]]"
  - "[[ref-scoring-models]]"
  - "[[doctrine.template]]"
  - "[[calibration-monitor]]"
---

# ref-dw-topology -- /invest vNEXT Tier-A Dynamic-Workflows specification

Read-on-demand companion to `.claude/skills/invest/SKILL.md` (same pattern as
ref-analysis-template.md, which Phase K.2 reads). Loaded at Phase A.7/D.8 when
TOPOLOGY = dw. This file owns the Tier-A detail: worker contracts, schemas,
tool grants, WebSearch caps, convergence semantics, skeptic specs, budgets,
resume protocol, shadow-run protocol, and gap-closure test cases.

**Authority rule:** the Tier-B sequential phase text in SKILL.md (Phases E-I,
J-bis, K-bis) is the AUTHORITATIVE definition of every analytical surface.
Worker contracts here REFERENCE those phases; they never redefine them. The
verdict spine (K-bis.5 + TIER PRECEDENCE + THESIS-STATUS + SOLVENCY-RUNWAY +
conviction modulation + post-redesign calibration tripwire + Phase Q ceilings + Phase R) is
NEVER touched by topology -- the topology feeds the spine, period.

## 1. Two-layer topology detection

- SHELL LAYER (advisory): `tools/lib/capability-detect.sh` exports
  `OSANWE_ENGINE` + `OSANWE_DW_HINT` (claude -> capable; codex/headless ->
  sequential). A shell script cannot see the session tool surface.
- SKILL LAYER (authoritative, Phase A.7): TOPOLOGY = `dw` iff the Workflow
  tool is present in the orchestrator's session tool surface; else
  `sequential`. Ambiguity -> `sequential` (safe). Never halts. No behavior
  EVER branches on model identity; `orchestrator_model` is logged passively
  (Phase B print, analysis frontmatter, calibration-monitor column) for the
  Phase-R stratified Brier only.

## 2. Two-invocation architecture (structural; strategist-ratified D4)

Workflows cannot pause for mid-run parent synthesis, and thesis-critic needs
the composite draft (main-loop K-bis.2/3 work). Therefore:

1. `.claude/workflows/invest-research.js` -- Phase(Price) + Wave 1 + Wave 2a.
   Invoked by the main loop after Phase D. Returns the research bundle.
2. MAIN LOOP -- the verdict spine, verbatim: J (hybrid live positions) -> J.5
   -> J-bis integration (positioning bundle) -> K-bis.2 framework rotation ->
   K-bis.3 composite -> K-bis.4/5 verdict -> K.5 thesis-critic (Agent tool,
   contract unchanged) -> Wave-3 gate -> K compose -> L claim-distributor
   (Agent tool, contract unchanged) -> M -> O.
3. `.claude/workflows/invest-verify.js` -- Wave 3 skeptics, conditional.

All 5 fleet contracts run UNCHANGED: price-fetcher, forensic-scorer,
institutional-positioning-scout via workflow agentType; thesis-critic,
claim-distributor via Agent tool exactly as Tier-B. N/A-is-success and
DEVIATION semantics are identical across tiers.

## 3. Wave 1 -- research fan-out (replaces sequential E-I EXECUTION, not spec)

Six workers, concurrency <= 6. The 13-WebSearch budget is DISTRIBUTED, never
expanded. Caps are CONTRACT text in worker prompts (self-reported via
`ws_calls_made`; audited by the Wave-3 provenance skeptic + Phase P).

| Worker | Kind | Tier-B surface covered | Tools (contract) | WS cap |
|---|---|---|---|---|
| quote-technicals | agentType: price-fetcher (v4) | E.0 + G price/momentum seed + H.2 inputs | Bash, Read, mcp robinhood quotes | 0 |
| identity-structure | template | Phase E | WebSearch, WebFetch, Read, mcp robinhood search | 2 |
| fundamentals | template | Phase F | mcp edgar {company,trends,read}, mcp openinsider dilution_filings, WebSearch, Read | 4 |
| filings-integrity | template | Phase H subset + red-flag layer | mcp edgar {search,filing,text_search,read,proxy}, mcp openinsider late_filings | 0 |
| competitive-macro-risk | template | Phases I + H remainder + G context | mcp edgar compare, mcp fred, WebSearch, WebFetch, Read | 6 |
| positioning | agentType: institutional-positioning-scout | Phase J-bis | per its contract + mcp edgar {ownership,fund} | 1 |

Worker-specific standing steps (additive to the Tier-B surface):
- fundamentals: `edgar_trends` multi-period revenue/GM/share-count (feeds the
  share-count >1.5x rule); `dilution_filings` shelf pipeline on negative-EPS
  names; reports `ttm_operating_income` + `scoring_path` (the routing input).
- filings-integrity: NT-10-K/Q; 8-K Items 4.02, 4.01, 2.02, 1.01, 5.02;
  RISK-FACTOR DIFF vs prior 10-K; SBC + comp via `edgar_proxy`; cross-check
  `late_filings`. Any NT-accounting/4.02/4.01 within 24mo -> integrity flag +
  confidence cap MED (mirrors forensic-scorer Tier 0a).
- competitive-macro-risk: `edgar_compare` peer-XBRL table (margins/growth/
  leverage vs 3-5 comps); FRED series confirmed via `fred_search` BEFORE any
  fetch; monthly series keep the output_type=4 backtest rule.
- positioning: `edgar_fund` named-manager 13F pulls (de-risking cluster).

Wave-1 prompt preamble (every worker): read-only; N/A-is-success; every
quantitative claim returned as the 8-field object (Section 7); blocked
domains per CLAUDE.md; evidence grades [A|B|C|D] with freshness downgrades.

## 4. Wave 2 -- convergence + main-loop spine

- BARRIER: forensic-scorer + positioning dispatch AFTER Wave 1 returns --
  forensic-scorer needs `fundamentals.scoring_path` (a loss-maker must never
  run the standard composite; MASTER INVARIANT).
- J and J.5 are ORCHESTRATOR-side: they read private/ files (path-guarded;
  workers never touch private/) and the live Robinhood positions (Section 8).
- thesis-critic (K.5) + claim-distributor (L.0): Agent-tool dispatches from
  the main loop, contracts byte-unchanged from Tier-B.

Convergence gate (deterministic, per worker): validate required JSON fields.
N/A returns = SUCCESSFUL dispatch (propagate verbatim). Missing fields OR
dispatch failure -> ONE re-dispatch -> documented inline fallback (the Tier-B
phase text IS the fallback; J-bis inline fallback lives in Section 10 below).
Pre-emptive skip = DEVIATION in Phase P (discipline breach + sessions-log).

## 5. Wave 3 -- adversarial verification (conditional)

Formalizes the 28-agent bridge battery (wf_991e83f5-37c, 2026-06-07) into a
standing wave via `.claude/workflows/invest-verify.js`.

FIRES when ANY of: draft verdict >= BUY; thesis-status CHANGE vs prior entity
state; composite within +/-5 of a tier boundary (20/40/60/80); `--verify`.
SKIPS on non-boundary HOLD/SELL without --verify (TIER PRECEDENCE makes
bearish the safe direction -- this is the cost lever, ~40% token saving).

Four read-only skeptics, parallel, each prompted to REFUTE; fail-closed (a
skeptic that cannot return its contract counts as a refutation):
1. data-integrity -- re-derives 5 sampled composite inputs from primary
   sources; share-count rule: shares outstanding +>1.5x over the 4-FY
   lookback (edgar_trends) -> REFUTATION unless explained by split/
   acquisition (closes residual gap 5; also runs inline on Tier-B).
2. R/R -- re-computes (target-entry)/(entry-stop); BUY >= 3:1, STRONG BUY
   >= 4:1 hard gates; arithmetic consistency on HOLD/SELL.
3. routing -- verifies scoring_path vs MASTER INVARIANT incl. STEP 2a
   (cyclical-still-profitable -> positive-eps-standard + MANDATORY mid-cycle
   note; note absent -> refutation) + solvency/pre-revenue gates.
4. provenance -- every quantitative claim carries `prov:` (>10% missing ->
   refutation); every price matches quote-technicals within 2%.

ANY refutation -> main loop executes Phase N HALT: F11 stays set, ZERO
writes, refutation surfaced. There is no auto-override.

## 6. Resume protocol

Mid-run interruption (either workflow): re-invoke with
`Workflow({scriptPath: ".claude/workflows/invest-<research|verify>.js",
resumeFromRunId: "<wf_id>"})` -- completed agent() calls return cached.
NEVER re-run a finished wave; never re-spend. Scripts contain no
Date.now()/Math.random() (resume safety); `run_timestamp` rides args.

## 7. Provenance -- the 8th INGEST-tuple field

Every quantitative claim written to the vault carries:

    prov: mcp:<server>:<key> | script:yfinance | web:<domain>+<grade>

Examples: `mcp:edgar:OperatingIncomeLoss`, `mcp:robinhood:last_trade_price`,
`mcp:fred:DGS10`, `script:yfinance`, `web:stockanalysis.com+B`.

The INGEST:claims tuple extends 7 -> 8: (entity, metric, value, date, grade,
section, text, prov). The marker-signature dedup key stays the 4-tuple
(entity, metric, value, date) -- prov is pass-through for /ingest and
claim-distributor (additive; no schema break; legacy 7-field claims remain
parseable). Enforcement: Wave-3 provenance skeptic at verdict time +
vault-audit X8 (SOFT, advisory, cutoff-scoped created >= 2026-06-10; the 65
legacy analyses are structurally exempt).

## 8. Live-positions hybrid rule (7.4; Phase J + Phase Q)

- EQUITY SHARE COUNTS: live `mcp__robinhood-trading__get_equity_positions`
  at run time (main loop, Phase J). Kills the manual-refresh staleness.
- THRESHOLD MATH: Phase J sizing + Phase Q concentration percentages are
  computed on regular_market_close prices from quote-technicals, per the
  ratified extended-hours doctrine ([[doctrine.template]]: concentration
  math anchors to regular close, NEVER live/AH). Live intraday values may be
  DISPLAYED with an as-of stamp; they never feed a doctrine threshold.
- CRYPTO: NOT in the Robinhood equity read set. The book is HYBRID: equities
  live via MCP + crypto quantities from private/holdings-taxable.md priced via
  fetch-prices.py. An equity-only total would SHRINK the denominator and
  FALSELY INFLATE thesis-exposure % toward doctrine ceilings -- the hybrid
  rule exists to prevent exactly that failure.
- RECONCILIATION ASSERT: hybrid total + per-name share counts cross-checked
  against private/holdings-taxable.md + private/holdings-ira.md each run. Divergence
  (>0.5% of book value OR any share-count mismatch) -> surfaced flag in
  Phase P, NEVER silent. On first live call, check whether positions return
  average cost basis: if yes, cross-check vs private/ and flag divergence;
  if no, private/ stays authoritative for basis. private/ files are the
  INTERPRETATION LAYER (cost-basis narrative, account doctrine, caveats) --
  never deleted, no longer the equity share-count source of record.
- D-SEC-1 untouched: read-only tools only; order tools stay deny-listed.

## 9. Token and cost governance

- Concurrency <= 6 (under the Workflow cap; tuned for rate limits + host).
- INVEST_DW_TOKEN_BUDGET env var: 750K full run / 500K when Wave 3 skips.
  CALIBRATED 2026-06-10 from the 3 production Tier-A runs (596K / 555K /
  715K total-run actuals; the 715K run carried the first production Wave-3
  fire, +213K; acceptance shadows averaged ~410K research + ~172K verify).
  750K covers the observed max with ~5% headroom; the 800K bridge-battery
  placeholder is RETIRED (was ~46K/agent x 28 agents, low-moderate conf).
  The workflow sandbox has NO process.env -- the MAIN LOOP reads
  the env var (default 750000) and passes `args.token_budget` for logging.
- MODEL POLICY (user-ratified): template workers + skeptics
  INHERIT the session model (omit the model option). Fleet agents dispatched
  via agentType run their own ratified definitions (opus/xhigh). No skill
  logic ever branches on model identity.

## 10. Tier-B J-bis inline fallback (relocated from SKILL.md; R3)

Runs ONLY when the J-bis.0 / positioning dispatch fails after one re-dispatch
(both tiers point here; reachability asserted by the acceptance pack's
fallback spot-exercise).

J-bis.1 -- Renowned-investor 13F overlay via Dataroma:
- WebFetch `https://www.dataroma.com/m/stock.php?sym={TICKER}` (free,
  no-auth, 65 superinvestor coverage; Q+45d update lag)
- Parse: renowned investors holding the ticker, share count, %-of-manager-
  AUM, recent activity (Buy/Add/Reduce/Closed/New)
- Decision threshold: 3+ superinvestors holding with stable/increasing
  weights = Grade-B confirmation; 5+ actively ADDING most-recent quarter =
  Grade-A confirmation; 5+ REDUCING = Grade-A caution flag
- Coverage gap fallback: if ticker not in Dataroma's 65-manager set OR data
  stale, supplement via SEC EDGAR direct using Bash + curl with User-Agent:
  `curl -A "OsanweResearch contact@email" "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=13F-HR&dateb=&owner=include&count=40"`.
  Cross-reference filings within last 90 days.

J-bis.2 -- Congressional STOCK Act overlay via CapitolTrades:
- WebFetch `https://www.capitoltrades.com/issuers/{numeric-id}?txDate=last-90-days`
  (free, no-auth, 3-year history)
- Issuer numeric ID required (not ticker symbol); embedded resolver for top
  50 tickers OR fallback to ticker-search URL
- Surface as anomaly signal only ("3 House members bought NVDA last 30
  days"); NOT decision-grade evidence on its own
- Tag direction: net-buy (cluster bullish-bias), net-sell (anomalous), mixed

J-bis.3 -- Insider cluster-buy detection via OpenInsider:
- Bash + curl (NOT WebFetch; http:// URL fails on TLS):
  `curl -sk -A "Mozilla/5.0" "http://openinsider.com/screener?s={TICKER}&xp=1&xs=1&cnt=100"`
- Filter: open-market purchases ONLY (xp=1); discount 10b5-1 scheduled
  trades (noise per Cohen-Malloy-Pomorski 2012)
- Cluster threshold: 3+ distinct C-suite/board insiders within 30 days,
  $250K+ aggregate = Grade-A signal (8-11ppt 12-month excess returns)
- Mixed pattern: surface CEO-vs-CFO context

J-bis.4 -- Mandatory output table for Decision Sheet integration:

    | Source | Signal | Magnitude | Direction | Grade |
    |---|---|---|---|---|
    | Dataroma | <count> superinvestors hold | <total %-of-AUM> | <Add/Reduce/New/Closed/Hold> | <A or B per threshold> |
    | CapitolTrades | <count> politician trades 90d | <$ volume> | <Buy/Sell/Mixed> | B (STOCK Act, 45d lag) |
    | OpenInsider | <count> insider cluster buys 30d | <$ value> | <Open-market vs 10b5-1 ratio> | <A if cluster threshold met, B if mixed> |

## 11. WebSearch allocation (preserved 13, distributed)

| Worker | WS | Tier-B equivalent |
|---|---|---|
| quote-technicals | 0 | E.0 (broker/script) |
| identity-structure | 2 | Phase E (2) |
| fundamentals | 4 | Phase F (4) |
| filings-integrity | 0 | SEC-direct subset of H |
| competitive-macro-risk | 6 | Phase I (3) + Phase H (2) + Phase G context (1) |
| positioning | 1 | J-bis coverage-gap fallback |
| TOTAL | 13 | identical to Tier-B |

## 12. Shadow-run protocol + gap-closure test cases

SHADOW RUNS (S7 write isolation -- A/B validation only): invoke with
`--no-entity --no-peripheral`; stage the composed analysis to
`wiki/research/test-tmp/shadow/<ticker>-<date>/` (gitignored) instead of
wiki/investing/analyses/; F11 held; Phase O short-circuits (nothing staged).
EVERY staged .md file MUST carry canonical frontmatter (status: draft) --
the shadow dir is gitignored but FILESYSTEM-VISIBLE to vault-audit; a
frontmatter-less stage file is a GATE finding that breaches the 95 floor
(empirically hit + fixed 2026-06-09; harness fixtures follow the same rule).
ZERO entity writes, ZERO calibration-monitor rows, ZERO hot.md touches --
the Brier population must contain no A/B artifacts. Predict the exact output
file set BEFORE each run; diff after (verdict / composite +/-5 / conviction
+/-10 / R/R +/-0.15 / kill criteria / scoring_path).

GAP-CLOSURE ACCEPTANCE CASES (behavioral; trigger must demonstrably fire):
1. STEP 2a cyclical-still-profitable: live shadow on a recovered cyclical
   -> routing trace shows STEP 2a -> positive-eps-standard + mid-cycle-margin
   note present. If a calibration tripwire is configured, it will HALT on the
   configured ticker.
2. SOLVENCY <4Q HOLD-cap: synthetic fixture (bridge path, runway 3.5Q, no
   committed financing, composite 65, pre-gate BUY) -> rating capped HOLD.
3. SOLVENCY <2Q SELL: synthetic fixture (runway 1.5Q) -> SELL (distress).
4. Pre-revenue <12mo SELL: synthetic fixture (revenue <$20M, runway 10mo)
   -> NR escalates to SELL.
5. Share-count >1.5x: data-integrity-skeptic fixture (current shares 1.8x
   the FY-2 baseline, no split/acquisition explanation) -> refutation: true.

Synthetic fixtures are reasoning-pass demonstrations against the K-bis.5
Step-1f text (never live distressed names -- they would pollute the vault).
Evidence lands in the acceptance pack.
