---
aliases: [strategy-variant-backtests, backtest-variants-2026-08-24]
categories: [wiki]
type: research
tags: []
status: active
created: 2026-08-24
updated: 2026-08-24
---

# Strategy variant backtests: V1 / V2 / V3 vs baseline momentum vs SPY

Date: 2026-08-24. Runner:
`Efforts/osanwe-v2-overhaul/_work/backtests/variants-20260824.py`.
Raw metrics JSON:
`Efforts/osanwe-v2-overhaul/_work/backtests/variant-results-20260824.json`.

SIMULATION ONLY. Every number below is hypothetical, computed offline from the
point-in-time factor store (`Efforts/osanwe-v2-overhaul/_work/factors.db`,
src=yfinance-5y, 1,255 equity trading days, 2021-08-24..2026-08-24) plus local
XBRL filing snapshots under `wiki/investing/filings/`. Past performance does
not guarantee future results.

Note: the task referenced `tools/backtest-strategy.py`, which does not exist in
the vault. The framework used is the canonical one: the `/backtest` skill plus
`ref-backtest-methodology.md` (same directory as its SKILL.md), whose pattern
is implemented by `tools/backtest-offline.py`, `tools/sector-alpha.py`, and
`tools/factor-store.py`. The runner follows that pattern exactly.

## Anti-lookahead safeguards applied (same as framework)

1. KNOWN_AS_OF: every signal query sees only rows with `date <= as_of`. No
   unbounded reads inside any signal loop.
2. Point-in-time fundamentals: revenue growth uses ONLY XBRL rows with
   `filed <= as_of` (latest known quarter vs same fiscal-period quarter one
   year earlier). What was knowable on rebalance day is what was used.
3. OFFLINE: zero network calls during the run; store + local snapshots only.
4. Fill timing (L3, conservative): signals computed at close of month-end day
   T, executed at close of the NEXT trading day T+1. Same-bar fills are the
   optimistic default the methodology flags; they were NOT used.
5. Sector labels come from CURRENT entity notes (L2 mild lookahead), coarse
   normalized into 11 buckets; flagged wherever V3 appears.
6. Costs are ZERO everywhere (no slippage/commission/tax; cash earns nothing);
   rf = 0 for all Sharpe ratios. Equal weight, fractional shares, fully
   invested among names with a tradable T+1 close.

## Strategies tested

- BASE momentum (framework Mode 1, lookback=63): rank all tickers with >= 68
  bars of history by trailing 63-trading-day return; buy top 10 equal weight;
  rebalance monthly (last trading day signal).
- V1 value-momentum-hybrid: composite z(3m return) * 0.5 + z(revenue growth
  YoY from XBRL) * 0.5; buy top 5; monthly rebalance.
- V2 low-vol-quality: universe restricted to names with positive YoY revenue
  growth (XBRL, point-in-time); rank by Sharpe of daily returns over trailing
  126 trading days; buy top 5; monthly rebalance.
- V3 sector-rotation (framework Mode 3): equal-weight mean 3-month return per
  sector bucket; rotate into the single best sector; hold 1 month. Months with
  no investable sector fall back to SPY (early window only).
- Benchmark: SPY buy-and-hold over each strategy's own fill window.

## Summary table (all strategies + baseline + SPY)

Sharpe = daily-return Sharpe, rf = 0, annualized. Win rate = share of monthly
holding periods beating SPY over the identical span.

| Strategy | Window | Total ret | Annualized | MaxDD | Sharpe | Win vs SPY |
|---|---|---|---|---|---|---|
| BASE momentum top-10 3m | 2021-12 .. 2026-07 (56 mo) | +598.8% | +52.0% | -45.8% | 1.10 | 57% (32/56) |
| V1 value-momentum hybrid top-5 | 2021-12 .. 2026-07 (56 mo) | +638.9% | +53.8% | -43.6% | 1.17 | 61% (34/56) |
| V2 low-vol quality top-5 | 2022-04 .. 2026-07 (52 mo) | +378.3% | +43.8% | -42.8% | 1.11 | 63% (33/52) |
| V3 sector rotation (best sector) | 2021-09 .. 2026-07 (59 mo) | +80.0% | +12.8% | -50.0% | 0.49 | 47% (28/59) |
| SPY buy-and-hold (V3 window) | 2021-09 .. 2026-07 | +76.9% | +13.1% | -24.5% | 0.76 | -- |

SPY over the common Dec-2021..Jul-2026 window (BASE/V1): +73.2% total,
8.3% ann., -24.5% maxDD, Sharpe 0.75. SPY over the Apr-2022..Jul-2026 window
(V2): +74.8% total, -21.3% maxDD, Sharpe 0.84.

Most recent holdings (2026-07-01 rebalance), provenance sample:
BASE -> ALAB, AMD, CRDO, DELL, INTC, MRAM, MRVL, MU, NBIS, SNDK;
V1 -> ALAB, CRDO, MRVL, MU, SNDK;
V2 -> AMAT, INTC, MKSI, MU, SNDK;
V3 -> 22-name Semis bucket (ALAB ... WDC).

## Honest verdicts

- BASE momentum BEATS SPY on total return (+525.6 pp over its window) and on
  Sharpe (1.10 vs 0.75). It also drew down -45.8%, nearly double SPY's -24.5%.
- V1 value-momentum hybrid BEATS SPY (+562.1 pp; Sharpe 1.17 vs 0.75) and is
  the best of the four on both raw and risk-adjusted terms. MaxDD still deep:
  -43.6%.
- V2 low-vol quality BEATS SPY (+303.5 pp; Sharpe 1.11 vs 0.84 on its own
  window) and has the best win rate (63%). Its Sharpe advantage over BASE is
  within noise; its maxDD (-42.8%) shows the "low-vol" label did not actually
  deliver low drawdown in this tech-heavy universe.
- V3 sector rotation BEATS SPY on total return by only +3.1 pp and LOSES on
  every risk-adjusted measure: Sharpe 0.49 vs 0.76, win rate 47%, worst maxDD
  of the group (-50.0%). On this universe it is effectively concentrated
  semis-beta with extra churn -- "tech went up" (bias S3), not an edge.

## Why every number above must be discounted

- S1 survivorship (applies to ALL rows): the ~107 tickers are TODAY'S curated
  watchlist. Delisted/acquired losers are absent, so cross-sectional winners
  are overrepresented. Treat all excess returns as upper bounds; the true
  out-of-sample edge is materially lower.
- S2 period bias: one 2021-2026 window dominated by a single tech/AI regime.
  Nothing here was tested across a bear/regime change beyond 2022.
- S3 composition bias: the universe is tech/semi/power-infrastructure heavy by
  design. V3's result is mostly this artifact.
- L2 lookahead: sector buckets derive from current entity notes.
- L4/costs: closes are adjusted (yfinance auto-adjust ingest), but costs are
  zero. Monthly top-5/top-10 churn at retail all-in costs of roughly
  0.05-0.20% per side would shave several points per year off the leaders.
- Multiple testing: four strategies were tried against one benchmark; expect
  out-of-sample decay in whichever looks best.
- Small samples: 52-59 monthly observations per strategy; win-rate differences
  of a few points are not significant.

## Which strategy would we actually use

Ranked on risk-adjusted return (the only ranking that matters here), not raw
return:

1. V1 value-momentum hybrid (Sharpe 1.17) -- the pick. Momentum does the heavy
   lifting; the point-in-time revenue-growth half adds a measurable Sharpe and
   drawdown improvement over BASE for free, and it degrades gracefully when a
   pure price screener would chase junk rallies.
2. V2 low-vol quality (Sharpe 1.11) -- defensible defensive alternate. Best
   win rate (63%), comparable Sharpe to BASE, and its fundamental filter makes
   it the least dependent on price-chasing behavior. But do not trust the
   "low-vol" name for drawdown protection: it still fell ~43% peak-to-trough.
3. BASE momentum (Sharpe 1.10) -- keep as the control/benchmark inside the
   vault; no reason to prefer it over V1 given V1 dominates it on every metric
   in-window.
4. V3 sector rotation (Sharpe 0.49, below SPY's 0.76-0.84) -- reject. The only
   variant worse than holding SPY risk-adjusted, with the deepest drawdown and
   a coin-flip win rate. On this curated universe, sector-level rotation adds
   concentration risk without adding information.

Caveat that outranks the ranking: after survivorship discounting and realistic
costs, the honest expectation for ANY of these live is "meaningfully less than
the table shows," and none of this constitutes advice. The verdict belongs to
the human operator.
