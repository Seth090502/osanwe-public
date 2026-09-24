---
name: backtest
description: "Use when asked to backtest hypothetical momentum, mean-reversion, sector-rotation or custom rules against the local factor store. Verify coverage and availability, use next-close fills and explicit costs, and compare net results to buy-and-hold SPY. Report survivorship, timing and selection limits; a historical simulation cannot establish alpha or production eligibility."
metadata:
  categories: analysis
  osanwe-risk: "low"
  osanwe-effort: "medium"
  osanwe-arguments: "strategy [params]"
  osanwe-argument-hint: "momentum `<lookback_days>` | meanreversion `<rsi_threshold>` | sector-rotation | custom \"<rule description>\""
  osanwe-allowed-tools: "Read Write Edit Bash Glob Grep"
  osanwe-categories: "meta"
  osanwe-type: "skill"
  osanwe-status: "active"
  osanwe-created: "2026-08-24"
  osanwe-updated: "2026-09-12"
---

Current causal simulation and comparison contract: `docs/institutional-methods.md`.
Frozen historical tournaments remain archival; the old full-run entry refuses
unregistered reruns. New simulations must declare decision/fill timing, costs,
universe availability, complete candidate lists and failure accounting. Only the
explicit synthetic sandbox may use the legacy firewall; locked evaluation is
available solely through the canonical gateway when a reviewed backend exists.

Plugin interoperability: `.agents/skills/finance-data/SKILL.md` owns typed
evidence intake and portable Finance/Data handoffs. This skill retains its
financial procedure and gates. Probe callable tools at run time; installed
plugin metadata alone does not establish a usable connector or source schema.

# /backtest -- hypothetical strategy simulation against the factor store

Run a rule-based strategy over historical bars from the point-in-time factor store,
report standardized performance metrics, benchmark against buy-and-hold SPY, and
flag methodological bias. This is a SIMULATION tool. Past performance does not
guarantee future results. Every number produced here is hypothetical.

## When to use

- "Backtest momentum with a 90-day lookback" -- does top-N momentum beat SPY?
- "Test mean reversion below RSI 30" -- what is the win rate on dip buys?
- "Would rotating into the best sector have worked?" -- quarterly-style rotation.
- "Backtest custom: buy when VIX > 25 and sell after 10 up days" -- any rule the
  store's data can express (bars: ticker/date/close; factors: FRED series).
- Calibrating a thesis before promoting it to /invest or a live position decision.

## Not for

- Live trading or order placement (read-only simulation; no broker tools allowed)
- Portfolio snapshot (use `/networth`) or single-name analysis (use `/invest`)
- Grading past /invest calls (that is `tools/backtest-v2.py`, prediction calibration)
- Any claim of predictive power -- output is descriptive history, never advice

### Mode routing

| Request | Mode | Parameters |
|---|---|---|
| momentum | Mode 1 | lookback trading days, default 90 |
| meanreversion | Mode 2 | RSI threshold, default 30 |
| sector-rotation | Mode 3 | monthly decision schedule and dated sector map |
| custom | Mode 4 | explicit rules, sizing and exit schedule |

### Phase A -- Data and preregistration

Store: `Efforts/osanwe-v2-overhaul/_work/factors.db` via `python tools/factor-store.py`.
The historical inventory recorded ~130k bar rows across ~107 tickers (daily closes, roughly 2021-08 .. 2026-08;
crypto goes back to 2015-class depth where ingested) plus factor observations
(VIXCLS, UNRATE, TREAST, WALCL, WRESBAL from FRED snapshots). SPY is present --
it is both tradable candidate and benchmark.

Refresh those coverage counts from --stats; they are not current verification.
Contracts you MUST honor:

1. KNOWN_AS_OF: every query passes an `as_of` date; the store returns only rows
   with `date <= as_of`. This date filter alone does not establish publication
   availability, historical revisions, or a point-in-time universe. Require those
   timestamps for a causal claim; absent metadata means exploratory-only results.
   Never use an unbounded signal query. Use tools/pit/pit_join.py for availability.
2. OFFLINE: no network calls during a backtest. The store is already ingested.
   If data is missing, report coverage gaps instead of fetching.
3. PROVENANCE: keep the `src` column through any export; cite it in outputs.

Inspect coverage first: `python tools/factor-store.py --stats`.

### Phase B -- Execution rules

Use tools/fis/tournament_runner.py simulate_target_weights for accounting.
If a driver is required, keep it under Efforts/osanwe-v2-overhaul/_work/backtests/.
Before viewing scores, register the full candidate set, window, universe, input
hashes, costs, timing, metrics and failure handling. Preserve every result and
failed run; corrections get a new receipt. Do not change the store or ingest.
Signals at close T fill at the next calendar close T+1, after existing holdings
are marked. Entry/rebalance/exit costs and cash must reconcile. Overlapping
cohorts share finite capital; never count the same cash twice. A terminal signal
without another price cannot fill. Missing held/fill prices cause refusal.
Never read `.raw/`, `private/`, `finance/`, `credentials/`, `.env*`,
`auth.json`, or `*.local.md`; nothing here needs account data.

### Mode 1: momentum

`/backtest momentum <lookback_days>` (default 90 if omitted)

- Universe: all tickers with bars at the entry date (state the count).
- At entry: rank by trailing `<lookback_days>`-day return computed ONLY from
  bars dated <= entry (KNOWN_AS_OF); buy top N=10, equal weight.
- Hold exactly `<lookback_days>` trading days, then close all and re-enter
  (rolling overlapping cohorts are fine; state which you used).
- Report strategy equity curve vs SPY buy-and-hold over the identical window.

### Mode 2: meanreversion

`/backtest meanreversion <rsi_threshold>` (default 30 if omitted)

- Compute RSI(14) from daily closes (Wilder smoothing); this is derived from
  bars, not read from the factors table.
- Entry: first day RSI drops below `<rsi_threshold>`; buy one equal-sized unit.
- Exit: first day RSI rises above 70, OR after 63 trading days (time stop),
  whichever comes first. State the time stop.
- One position per ticker at a time; cash otherwise earns nothing.
- Primary metrics are win rate and average gain per trade; still report the
  full metric block vs SPY.

### Mode 3: sector-rotation

`/backtest sector-rotation`

- Map tickers to sectors using a dated classification. The current `sector:`
  line under `wiki/entities/` is an exploratory fallback with lookahead disclosed. Tickers
  without a sector label go to `unknown` and are excluded; say how many.
- On the first trading day of each month: compute each sector's trailing
  3-month (~63 trading days) mean return from bars <= that day; hold the best
  sector's members equally weighted until next rebalance.
- If the best sector has zero investable members that month, stay in SPY and
  note it.

### Mode 4: custom

`/backtest custom "<plain-English rules>"`

- Restate the rules as pseudocode BEFORE running; get the user's confirmation
  if any ambiguity could change results materially (entry timing, exits,
  position sizing).
- Implement only what bars/factors support. If a rule needs data the store
  lacks (fundamentals, intraday, options), say so and stop -- do not silently
  substitute a proxy without flagging it.
- Same metric block, same SPY benchmark, same bias flags.

## Assumptions to state in EVERY run (verbatim section)

- Entry timing: signals computed at close T, filled at the next calendar close T+1.
- Position sizing: state target weights, cap, overlapping-cohort funding and cash.
- Costs: explicit one-way cost assumptions charged on entry, rebalance and exit;
  include a higher-cost sensitivity. Zero cost is a labeled idealized control.
  Taxes, borrow and market impact are excluded unless separately supported.
- Data: report adjusted/raw price basis, split/dividend treatment, availability
  and lifecycle coverage. Source labels alone do not verify adjustment semantics.
- Cash earns nothing between trades.

### Phase C -- Output format (fixed block, then prose)

```
== BACKTEST REPORT: <mode> <params> ==
Window:        <first trade date> .. <last trade date> (<n> trading days)
Universe:      <n> tickers (<m> excluded: <reason>)
Trades:        <count> round trips
Total return:  <x>%   (SPY same window: <y>%, excess: <z> pp)
Annualized:    <x>%   (SPY: <y>%)
Max drawdown:  <x>%   (SPY: <y>%)
Sharpe (rf=0): <x.x>   (SPY: <x.x>)
Win rate:      <x>%   (<wins>/<trades>)
Avg gain/win:  <x>%   Avg loss: <y>%   Profit factor: <z>

Assumptions: next-calendar-close fills, <sizing>, <costs and stress costs>,
<tax/borrow exclusions>, zero cash interest, <price basis> per <provenance>.
Bias flags:
- Survivorship: <see ref-backtest-methodology.md S1-S3; name which apply>
- Lookahead:   <confirm as_of discipline held; name any exception>
SIMULATION ONLY -- past performance does not guarantee future results.
```

Follow with <=5 bullets of interpretation. Never upgrade this into advice;
the verdict belongs to the human.

### Quality Rules

Every report MUST carry both lines, even when clean:

- Survivorship: a present-day curated watchlist is not the historical investable
  universe. Report selection and missing-delisting coverage; neither the size
  nor the direction of bias is established by a warning or a date filter.
- Lookahead: record signal cutoffs, actual availability/revision metadata,
  classification dates and first eligible fill. Unknown availability remains
  unknown. A current sector map cannot certify a historical classification.
- Keep all candidates and failures, same-window baselines and net-cost metrics.
  Do not invent significance or omit a losing regime. Follow the canonical
  promotion gateway; a completed synthetic run never authorizes promotion.

Full treatment: `ref-backtest-methodology.md` (same directory).

## Failure modes

- Empty result set: report coverage gap from `--stats`, do not fabricate.
- Fewer than 60 trading days in window: refuse, window too short for annualize/
  drawdown stats to mean anything.
- Script crashes mid-run: retain the failed receipt, diagnose, freeze the corrected
  source and rerun under a disclosed new receipt. Never hand-transcribe partial
  numbers as a successful run or tune the rules after viewing their scores.
