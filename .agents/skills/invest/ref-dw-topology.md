---
categories: [sources]
type: reference
created: 2026-06-09
updated: 2026-07-11
status: active
confidence: high
tags:
  - topic/investment-analysis
  - topic/dynamic-workflows
  - topic/concurrency
  - topic/adversarial-verification
related:
  - "*invest* (not published)"
  - "[[ref-analysis-template]]"
  - "[[ref-entity-update-semantics]]"
  - "[[ref-scoring-models]]"
  - "*ref-portfolio-doctrine* (not published)"
  - "*calibration-monitor* (not published)"
---

Current evidence authority: docs/financial-analysis-contract.md. Every quantity,
basis and account-total claim requires runtime broker evidence. Unavailable data
is UNVERIFIED. Harness identity never exempts data-quality checks.


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
conviction modulation + SINGLE-NAME-BUY tripwire + Phase Q ceilings + Phase R) is
NEVER touched by topology -- the topology feeds the spine, period.

## 1. Two-layer topology detection

- SHELL LAYER (advisory): `tools/lib/capability-detect.sh` exports
  `OSANWE_DW_HINT` (definitive Claude Code marker -> capable; any other
  harness or headless -> sequential). A shell script cannot see the session
  tool surface.
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
| quote-technicals | agentType: price-fetcher (v5) | E.0 + G price/momentum seed + H.2 inputs + deterministic technicals panel | Bash, Read, mcp the broker quotes + historicals | 0 |
| identity-structure | template | Phase E | WebSearch, WebFetch, Read, mcp the broker search | 2 |
| fundamentals | template | Phase F | mcp edgar {company,trends,read}, mcp openinsider dilution_filings, WebSearch, Read | 4 |
| filings-integrity | template | Phase H subset + red-flag layer | mcp edgar {search,filing,text_search,read,proxy}, mcp openinsider late_filings | 0 |
| competitive-macro-risk | template | Phases I + H remainder + G context | mcp edgar compare, mcp fred, WebSearch, WebFetch, Read | 6 |
| positioning | agentType: institutional-positioning-scout | Phase J-bis | per its contract + mcp edgar {ownership,fund} | 1 |

Worker-specific standing steps (additive to the Tier-B surface):
- quote-technicals (v5, 2026-07-11): the workflow passes
  `include_technicals: true` (+ optional `correlation_basket`) into the
  dispatch input; the agent pulls `get_equity_historicals` (target + SPY +
  basket, ONE <=10-symbol call, ~420d) and returns the `tools/technicals.py`
  panel under a `technicals` key (+ `correlation_matrix`), which the
  convergence gate REQUIRES when the flag is set (a degraded panel returns
  `technicals: null` + a failures[] entry, never a silent omit). The panel's
  `returns_pct.5_session` is the GATE-F `move_5d_pct` prov source; its
  `vol_annualized_pct.trailing_63s` is the Phase K-ter realized-vol input.
  Field contract: ref-analysis-template Section 2.9. /brief + /networth omit
  the flag -> byte-identical v4 behavior.
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
domains per AGENTS.md; evidence grades [A|B|C|D] with freshness downgrades.

**Robinhood-first hard rule (rung 0; donor rule-15 port 2026-07-11), every
worker:** any price, quote, market cap, share count for cap math, 52-week
range, volume, price history, or options quote for a US-listed name -- the
TARGET, its PEERS, and the BENCHMARK alike -- comes from the broker MCP
when its tools are present (batched: `get_equity_quotes` <=20,
`get_equity_fundamentals` <=10, `get_equity_historicals` <=10). Never
web-search a price the broker can serve; a web-sourced market figure is a
last resort after an MCP failure or a non-covered asset, and carries a
per-figure source+date disclosure. Scope: MARKET data only -- filing-derived
accounting stays EDGAR; forward estimates stay FMP/proxy (ref-analysis-
template Sections 2.9/2.10).

## 4. Wave 2 -- convergence + main-loop spine

- BARRIER: forensic-scorer + positioning dispatch AFTER Wave 1 returns --
  forensic-scorer needs `fundamentals.scoring_path` (a loss-maker must never
  run the standard composite; MASTER INVARIANT).
- J and J.5 remain ORCHESTRATOR-side: use current-session broker read
  evidence and explicitly permitted research references (Section 8). No
  participant reads protected files; workers receive only the minimum permitted
  evidence for their task, with account identifiers excluded from research artifacts.
- thesis-critic (K.5) + claim-distributor (L.0): Agent-tool dispatches from
  the main loop, contracts byte-unchanged from Tier-B.

Convergence gate (deterministic, per worker): validate required JSON fields.
N/A returns = SUCCESSFUL dispatch (propagate verbatim). Missing fields OR
dispatch failure -> ONE re-dispatch -> documented inline fallback (the Tier-B
phase text IS the fallback; J-bis inline fallback lives in Section 10 below).
Pre-emptive skip = DEVIATION in Phase P (discipline breach + sessions-log).

## 5. Wave 3 -- adversarial verification

Formalizes the 28-agent bridge battery (wf_991e83f5-37c, 2026-06-07) into a
standing wave via `.claude/workflows/invest-verify.js`.

STATUS (verified 2026-09-21): the dispatch below does not currently happen.
`invest-verify.js` returns `status: withheld`, `any_refutation: true`,
`dispatched_agents: 0` and `blockers: ['mechanical_read_only_boundary_unavailable']`
for every valid call, because the installed Workflow agent API exposes no
verified per-call read-only restriction and the guard refuses to dispatch
unrestricted reviewers. The rest of this section is the contract the lenses
resume under once such a boundary exists. Until then every Tier-A call of the
gate resolves to the Phase N withheld-acceptance path in SKILL.md K.5 STEP 4,
which is unchanged. COMPATIBILITY.md ("Validation profiles") records the same
boundary.

FIRES for every material STRONG BUY, BUY, HOLD, SELL or STRONG SELL conclusion.
Thesis-status CHANGE, composite within +/-5 of a tier boundary (20/40/60/80),
and `--verify` also require review. A bearish direction does not establish safe
financial reasoning. Final delivered-artifact review remains separate and must
cover the actual final bytes; see SKILL.md K.5 Step 4 and the financial contract.

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

    prov: mcp:`<server>`:`<key>` | script:`<name>` | web:`<domain>`+`<grade>`

Examples: `mcp:edgar:OperatingIncomeLoss`, `mcp:robinhood:last_trade_price`,
`mcp:fred:DGS10`, `script:yfinance`, `script:technicals` (the deterministic
panel, 2026-07-11), `web:stockanalysis.com+B`.

The INGEST:claims tuple extends 7 -> 8: (entity, metric, value, date, grade,
section, text, prov). The marker-signature dedup key stays the 4-tuple
(entity, metric, value, date) -- prov is pass-through for /ingest and
claim-distributor (additive; no schema break; legacy 7-field claims remain
parseable). Enforcement: Wave-3 provenance skeptic at verdict time +
vault-audit X8 (SOFT, advisory, cutoff-scoped created >= 2026-06-10; the 65
legacy analyses are structurally exempt).

## 8. Runtime holdings and denominator integrity (Phase J + Phase Q)

- Quantities and basis require successful broker reads for every included account
  and asset class. Missing coverage stays UNVERIFIED; no private-file fallback.
- Threshold math remains anchored to regular_market_close per canonical doctrine.
  Intraday/extended-hours values may be displayed with their session/as-of stamp,
  but do not silently feed regular-close doctrine thresholds.
- Crypto coverage depends on actual available tools. A verified broker aggregate
  does not establish per-coin quantities. Never shrink a whole-book denominator
  to known equities and call the resulting concentration doctrine-comparable.
- Reconcile per-name/account values and totals from the same runtime snapshot.
  Surface material discrepancies and scope limitations. Basis unavailable means
  P&L and tax implications are unverified, not supplied by a historical note.
- D-SEC-1 remains unchanged: broker read tools only, no financial execution.

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
- MODEL POLICY (`<owner>`-ratified 2026-06-09): template workers + skeptics
  INHERIT the session model (omit the model option). Fleet agents dispatched
  via agentType run their own ratified definitions (opus/max). No skill
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
- Use HTTPS with normal certificate verification. If the aggregator cannot
  be retrieved securely, use the corresponding official SEC Form 4 filings
  or report the overlay unavailable. Never disable TLS verification or
  downgrade transport to evade a certificate failure.
- Filter: open-market purchases ONLY (xp=1); discount 10b5-1 scheduled
  trades (noise per Cohen-Malloy-Pomorski 2012)
- Cluster threshold: 3+ distinct C-suite/board insiders within 30 days,
  $250K+ aggregate = Grade-A signal (8-11ppt 12-month excess returns)
- Mixed pattern: surface CEO-vs-CFO context

J-bis.4 -- Mandatory output table for Decision Sheet integration:

    | Source | Signal | Magnitude | Direction | Grade |
    |---|---|---|---|---|
    | Dataroma | `<count>` superinvestors hold | <total %-of-AUM> | <Add/Reduce/New/Closed/Hold> | <A or B per threshold> |
    | CapitolTrades | `<count>` politician trades 90d | <$ volume> | <Buy/Sell/Mixed> | B (STOCK Act, 45d lag) |
    | OpenInsider | `<count>` insider cluster buys 30d | <$ value> | <Open-market vs 10b5-1 ratio> | <A if cluster threshold met, B if mixed> |

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
   (MU recommended; SINGLE-NAME-BUY tripwire is the built-in safety) -> routing trace
   shows STEP 2a -> positive-eps-standard + mid-cycle-margin note present.
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
