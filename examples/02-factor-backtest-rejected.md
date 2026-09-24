# Example 2 -- a factor backtest that was rejected

> As of 2026-09-20. Published as an example of the system's output.
> Not investment advice, not a recommendation, and not a statement of anyone's positions.

READ THIS FIRST: this report and its own code disagree. The Method section says missing components enter the composite at z = 0 (neutral) rather than excluding the name; the code at `tools/research/quality-factor.py:289-290` skips those names instead. The report's conclusion (REJECT) is unaffected in direction, but any number in it that depends on universe size is computed on a smaller universe than the text describes. It is published as an example of a rejected experiment, and of a documentation-versus-code defect found by audit.

---

<details>
<summary>Metadata the system recorded for this run</summary>

```yaml
aliases: []
categories: [decisions]
status: complete
created: 2026-08-25
updated: 2026-09-21
tags: [fis]
related: ["[[phase-i-freeze-manifest]]"]
```

</details>


# Experiment: Quality Factor (EDGAR XBRL fundamentals)

- Date run: 2026-08-25
- Code: `tools/research/quality-factor.py`
- Data: `wiki/investing/filings/<T>/<T>-xbrl.json` + `bars` table in
  `Efforts/osanwe-v2-overhaul/_work/factors.db` (yfinance adj closes).
- Question: do high-quality companies (profitable, low leverage, stable
  earnings) outperform low-quality ones?

## Method

- Quarterly rebalance on the first trading day of Mar/Jun/Sep/Dec.
- POINT-IN-TIME: only filings with `filed <= rebalance date`; restatements
  deduped keeping the first-filed value per (concept, period); prices are
  last close on/before the rebalance date.
- Quality composite = equal-weight mean of cross-sectional z-scores of:
  1. Profitability: TTM NetIncome / TTM Revenue (net margin)
  2. Low leverage: -(LongTermDebt / TTM Revenue)
  3. Earnings stability: -(std of last up-to-8 quarterly NI / mean|NI|),
     minimum 4 quarters required. CORRECTION (2026-09-21): only the
     leverage component can enter the composite at z = 0. A name whose
     margin or earnings-stability metric is missing is skipped entirely
     before scoring, so it is excluded rather than neutralised.
- Quintiles formed per rebalance (Q5 = highest quality = LONG leg).
- Baselines: SPY buy-and-hold over the same span; equal-weight (EW) all
  scored tickers.

### Metric adaptations (data limitation, stated up front)

The vault XBRL store contains only {Revenue(s), NetIncome, Cash, Capex,
R&D, LongTermDebt}. **No GrossProfit, TotalAssets, or StockholdersEquity**
concepts exist, therefore:
- Gross profitability (GP/TA) was substituted with net margin (TTM NI /
  TTM Rev) per the task's 'or Revenue as proxy' allowance.
- ROE (NI/equity) could NOT be computed and was omitted.
- Leverage used Debt/Revenue instead of Debt/Equity.
- Quarterly NI series have fiscal-year-end gaps in this store; TTM values
  use the freshest-filed source (trailing-4-qtr window vs latest FY row).

**DATA COVERAGE NOTE:** most tickers' XBRL rows only begin in 2024-2026.
A strict >=15-name floor leaves ONE usable rebalance (2026-03), which is
far too few periods for any statistical claim. Two passes are reported:
(a) PRIMARY with the strict floor, and (b) SENSITIVITY with a >=8-name
floor that reaches further back but has thin quintiles. Both fail the
task's own quality bar; treat all numbers below as descriptive only.

## PRIMARY pass (floor >=15 scored names)

- Rebalances used: 1 (2026-03-02 -> 2026-06-01)
- Names scored per rebalance: min 49, max 49.
- Span: 0.25 years.

| Bucket | N qtrs | Total ret | CAGR* | Sharpe* |
|---|---|---|---|---|
| Q1 | 1 | +81.5% | +986.0% | n/m |
| Q2 | 1 | +22.7% | +127.0% | n/m |
| Q3 | 1 | +28.9% | +176.0% | n/m |
| Q4 | 1 | +46.1% | +355.6% | n/m |
| Q5 | 1 | +9.2% | +42.3% | n/m |
| EW | 1 | +35.9% | +241.2% | n/m |
| SPY B&H | - | +10.8% | +51.0% | - |

*CAGR annualizes very short spans and is explosive/unstable;
Sharpe is n/m (not meaningful) with fewer than 2 quarters.

- Q5 - Q1 mean quarterly spread: -72.31%
- Paired t-stat: NOT COMPUTABLE (n=1 quarter).
- CAGR rank order (worst->best): Q5 < Q2 < Q3 < Q4 < Q1
- Monotonic Q1<Q2<Q3<Q4<Q5: NO
- Q5 beats Q1 on CAGR: NO

## SENSITIVITY pass (floor >=8 scored names)

- Rebalances used: 5 (2025-03-03 -> 2026-06-01)
- Names scored per rebalance: min 8, max 49.
- Span: 1.25 years.

| Bucket | N qtrs | Total ret | CAGR* | Sharpe* |
|---|---|---|---|---|
| Q1 | 5 | +225.4% | +157.0% | 1.77 |
| Q2 | 5 | +352.8% | +234.8% | 1.65 |
| Q3 | 5 | +35.7% | +27.7% | 0.87 |
| Q4 | 5 | +97.0% | +72.0% | 1.73 |
| Q5 | 5 | +39.1% | +30.2% | 1.00 |
| EW | 5 | +159.3% | +114.3% | 2.69 |
| SPY B&H | - | +31.8% | +24.8% | - |

*CAGR annualizes very short spans and is explosive/unstable;
Sharpe is n/m (not meaningful) with fewer than 2 quarters.

- Q5 - Q1 mean quarterly spread: -22.49%
- Paired t-stat (Q5 vs Q1, n=5): -1.64
- CAGR rank order (worst->best): Q3 < Q5 < Q4 < Q1 < Q2
- Monotonic Q1<Q2<Q3<Q4<Q5: NO
- Q5 beats Q1 on CAGR: NO

## Verdict

**REJECT -- factor NOT established**
- Failure criterion hit: Q5 (high quality) does not outperform Q1.
- Failure criterion hit: only 1 rebalance(s) clear the >=15-name floor (need >=12 for meaningful stats).

## Caveats (read before trading this)

- SURVIVORSHIP: the universe is today's watchlist; delisted names absent.
- FUNDAMENTAL DEPTH: XBRL coverage starts ~2024-2026 for most names, so
  the point-in-time sample is 1-7 quarters deep, far below what any
  factor study needs. The t-stat cannot be computed on the primary pass.
- Small cross-section makes quintile edges thin (top/bottom ~10 names).
- Metric substitutions above weaken fidelity to the canonical quality
  factor (Novy-Marx GP/TA, ROE).
- Quarterly granularity ignores intra-quarter timing; no transaction
  costs modeled.
