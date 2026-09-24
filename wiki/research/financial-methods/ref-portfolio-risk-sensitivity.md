---
aliases: [portfolio uncertainty and decision sensitivity]
categories: [wiki]
type: reference
tags: [topic/investing]
status: active
created: 2026-09-13
updated: 2026-09-13
related: ["[[institutional-methods]]", "[[ref-performance-attribution]]", "[[ref-household-tax-retirement]]"]
---

# Portfolio uncertainty and decision sensitivity

Public/synthetic method, version 1. Portfolio weights need reconciled account
scope at use time; the examples below are invented. A covariance matrix alone
does not define suitable risk, expected returns or a household objective.

## R1. Estimation and comparison

Align observations, return basis, currency, horizon and missing-data treatment.
Check symmetry and positive semidefiniteness. Compare sample covariance with the
existing applicable shrinkage estimators; do not assume any estimator dominates
every regime. QIS is a published covariance estimator, not a proprietary discovery
or evidence of return predictability. [Ledoit and Wolf (2022), abstract and section 1](https://www.econ.uzh.ch/dam/jcr:27e9ffa4-578e-4d6f-84d9-7707c98cedb0/bernoulli_2022.pdf)

Black-Litterman combines an equilibrium prior with supplied views; record the
view covariance, overlapping information and shared horizon. Subjective view
confidence does not become a calibrated return distribution by being entered
into the model. [Goldman Sachs, Black-Litterman model history](https://www.goldmansachs.com/our-firm/history/moments/1990-black-litterman-model)

## R2. Synthetic covariance and stress

Two assets have annual variances 0.04 and 0.01 and covariance 0.005. At equal
weights, portfolio variance is 0.015 and annual volatility is 12.247449%.
Ignoring covariance incorrectly yields variance 0.0125. Under perfect positive
correlation, covariance is 0.02 and portfolio volatility becomes 15%.
With joint asset shocks of -40% and -10%, the equal-weight loss is 25%, before
fees, taxes or rebalancing. The covariance estimate cannot rule out that scenario.

Use `tools/fis/covariance.py`, `risk_engine.portfolio_risk` and
`allocation.optimize_allocation`. Compare no action and a simple feasible
allocation using identical costs, return assumptions and constraints. Report
which joint scenarios reverse a proposed preference. Numerical solver accuracy
does not validate expected returns, cash feasibility or suitability.

## R3. Kelly and execution counterexamples

For a synthetic even-payoff repeated bet with win probability 0.6, the full
Kelly fraction is 0.2. Its expected log growth is 0.020135514 per bet; using
fraction 0.1 gives 0.015041902, a ratio about 0.747033, not exactly 0.75.
This calculation assumes the stated probability/payoff distribution; it does
not supply one for a stock. Narrative scenario weights cannot fill that gap.

A stop order becomes a market order when triggered, and execution can differ
from the stop price. A stop-limit can remain unfilled. Thus an intended stop
does not establish a loss bound or justify larger Kelly sizing.
[SEC, Trading Basics, stop and stop-limit orders, PDF p. 2](https://www.sec.gov/investor/alerts/trading101basics.pdf)

R2/R3 arithmetic is checked in `tools/fis/test_corpus_examples.py`. Correlated
drawdowns, liquidity demands and personal cash constraints still require the
owning portfolio/household workflows. Existing doctrine bands are unchanged.

prov: script:synthetic annual covariance, joint shocks and per-bet log growth;
web:bounded original-method and execution passages inspected 2026-09-13.
