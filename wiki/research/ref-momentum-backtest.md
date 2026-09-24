---
categories:
  - wiki
type: research
created: 2026-08-24
updated: 2026-08-24
status: active
confidence: MEDIUM
tags:
  - topic/backtesting
  - topic/momentum
related:
  - "*ref-factor-lens* (not published)"
---

# Ref: Monthly Momentum Backtest vs SPY (baseline, untuned)

Generated 2026-08-24T23:17:35Z by `tools/backtest-strategy.py` from `Efforts/osanwe-v2-overhaul/_work/factors.db`. Store window 2021-08-24..2026-08-24; evaluated window 2021-08-24..2026-08-24 (first ~4 months consumed by the 63-bar warm-up).

## Methodology

- Universe: ALL 107 tickers in the factor store, no exclusions.
- Signal: at each month-end (last SPY session of the month) rank every
  ticker by trailing 63-trading-bar return over its OWN bars, computed
  strictly from bars dated <= the rebalance date (zero lookahead).
- Portfolio: top 5 equal weight; hold ~1 month; rebalance.
- Execution: rebalance-date close proxy (spec-permitted); no intraday fills.
- Costs: 10 bps per ROUND TRIP (5 bps/side) charged on traded notional;
  a full 100 pct portfolio replacement costs 0.1 pct of NAV.
- Skips: fewer than 64 own bars up to the rebalance date, or latest bar
  older than 7 calendar days (stale/delisted).
- Weights drift intra-month (true buy-and-hold between rebalances);
  a name that stops printing is frozen at its last close (no recovery).

## Results (first honest run -- NOT parameter-tuned)

| Metric | Momentum Top-5 | SPY |
|---|---|---|
| Total return | +818.15% | +82.70% |
| CAGR | +55.82% | +12.81% |
| Sharpe (daily, rf=0) | 1.06 | 0.79 |
| Max drawdown | -46.24% | -24.50% |

- Months strategy beat SPY: 57.4% (35 of 61 months)
- Avg one-way turnover per rebalance: 56.4% of NAV
- Verdict: **BEAT SPY** on total return.

## Monthly returns (strategy / SPY / excess)

| Month | Strategy | SPY | Excess |
|---|---|---|---|
| 2021-08 | +0.00% | +0.80% | -0.80% |
| 2021-09 | +0.00% | -4.66% | +4.66% |
| 2021-10 | +0.00% | +7.02% | -7.02% |
| 2021-11 | -0.05% | -0.80% | +0.75% |
| 2021-12 | -8.51% | +4.62% | -13.13% |
| 2022-01 | -11.56% | -5.27% | -6.29% |
| 2022-02 | +0.11% | -2.95% | +3.06% |
| 2022-03 | +2.37% | +3.76% | -1.39% |
| 2022-04 | -19.28% | -8.78% | -10.50% |
| 2022-05 | +5.60% | +0.23% | +5.38% |
| 2022-06 | -14.45% | -8.25% | -6.21% |
| 2022-07 | +7.80% | +9.21% | -1.41% |
| 2022-08 | +3.98% | -4.08% | +8.06% |
| 2022-09 | -5.68% | -9.24% | +3.56% |
| 2022-10 | +12.18% | +8.13% | +4.05% |
| 2022-11 | -5.39% | +5.56% | -10.95% |
| 2022-12 | -8.34% | -5.76% | -2.58% |
| 2023-01 | +6.85% | +6.29% | +0.56% |
| 2023-02 | +0.70% | -2.51% | +3.22% |
| 2023-03 | +3.16% | +3.71% | -0.55% |
| 2023-04 | -7.61% | +1.60% | -9.21% |
| 2023-05 | +27.92% | +0.46% | +27.46% |
| 2023-06 | +8.46% | +6.48% | +1.98% |
| 2023-07 | +15.58% | +3.27% | +12.31% |
| 2023-08 | +9.01% | -1.63% | +10.63% |
| 2023-09 | -12.25% | -4.74% | -7.51% |
| 2023-10 | -7.54% | -2.17% | -5.36% |
| 2023-11 | +21.36% | +9.13% | +12.23% |
| 2023-12 | +25.92% | +4.57% | +21.35% |
| 2024-01 | -21.07% | +1.59% | -22.66% |
| 2024-02 | +33.56% | +5.22% | +28.34% |
| 2024-03 | +8.37% | +3.27% | +5.10% |
| 2024-04 | -12.37% | -4.03% | -8.34% |
| 2024-05 | +28.88% | +5.06% | +23.82% |
| 2024-06 | -9.07% | +3.53% | -12.60% |
| 2024-07 | -11.94% | +1.21% | -13.15% |
| 2024-08 | -2.56% | +2.34% | -4.89% |
| 2024-09 | +15.68% | +2.10% | +13.58% |
| 2024-10 | +10.14% | -0.89% | +11.03% |
| 2024-11 | +77.81% | +5.96% | +71.85% |
| 2024-12 | -21.22% | -2.41% | -18.82% |
| 2025-01 | +14.89% | +2.69% | +12.21% |
| 2025-02 | -15.46% | -1.27% | -14.19% |
| 2025-03 | -24.30% | -5.57% | -18.73% |
| 2025-04 | -0.05% | -0.87% | +0.82% |
| 2025-05 | +4.59% | +6.28% | -1.69% |
| 2025-06 | +7.49% | +5.14% | +2.35% |
| 2025-07 | +15.25% | +2.30% | +12.95% |
| 2025-08 | -3.77% | +2.05% | -5.83% |
| 2025-09 | +28.78% | +3.56% | +25.21% |
| 2025-10 | +32.89% | +2.38% | +30.51% |
| 2025-11 | -10.19% | +0.19% | -10.38% |
| 2025-12 | +3.96% | +0.08% | +3.88% |
| 2026-01 | +40.93% | +1.47% | +39.45% |
| 2026-02 | +20.82% | -0.86% | +21.68% |
| 2026-03 | -4.16% | -4.94% | +0.78% |
| 2026-04 | +67.03% | +10.51% | +56.53% |
| 2026-05 | +18.15% | +5.26% | +12.89% |
| 2026-06 | +18.02% | -1.03% | +19.05% |
| 2026-07 | -36.69% | +0.03% | -36.72% |
| 2026-08 | +5.00% | +2.40% | +2.60% |

## Bias disclosure

1. **Lookahead**: prevented by construction -- signal window ends at
   t-1, queries filter date <= as_of, entry is the t close proxy.
2. **Survivorship (RESIDUAL)**: the store contains only tickers listed
   TODAY (ingested 2026-08-24). Names that delisted before ingestion
   are absent, so results likely OVERSTATE achievable returns. All
   107 present tickers were included, including recent IPOs with short
   histories (which simply sit out until they clear the warm-up).
3. **Transaction costs**: flat 10 bps round trip; real slippage on the
   small-caps and crypto names here would likely exceed this.
4. **No hindsight selection**: purely mechanical ranking; parameters
   (top-5, 63-bar lookback, monthly cadence) were fixed ex ante.
5. **Close-proxy fills** ignore open-price execution and gaps.
6. **Frozen-price delistings**: if a held name stops printing, it is
   carried at its last close (no bankruptcy recovery modeled).
7. **Sharpe uses rf=0** and daily returns annualized by sqrt(252);
   crypto constituents trade weekends and are valued on SPY sessions.

## Reproduce

```
python tools/backtest-strategy.py --write-md
```

Machine-readable results: `Efforts/osanwe-v2-overhaul/_work/backtest-momentum-results.json`.
