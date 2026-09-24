---
aliases: [financial research validation and base rates]
categories: [wiki]
type: reference
tags: [topic/investing]
status: active
created: 2026-09-13
updated: 2026-09-13
related: ["[[institutional-methods]]", "[[ref-financial-statement-evidence]]", "[[ref-performance-attribution]]"]
---

# Empirical research: what survives selection and costs

Public/synthetic method, version 1. This is method-use guidance for existing
backtest and evaluator owners, not a new promotion rule or an alternative
route to sealed cases.

## Q1. Preserve the experiment and its information set

Before testing, specify population, available information, signal, fill rule,
cost model, comparison, independent sampling unit, resource budget and failure
handling. Record all attempted variants, including renamed or abandoned ones.
The probability-of-backtest-overfitting literature explains why selecting the
best of many trials creates misleading historical success; a fresh dataset
does not by itself erase adaptive choice.
[Bailey et al. (2015), abstract and section 1](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)

Keep security history, corporate actions, publication lags, unavailable records
and revision policy. For factor data record format and vintage: French's library
changed U.S. research-return inputs from CRSP FIZ to CIZ beginning January 2025.
Do not silently splice vintages or assume their construction is identical.
[French Data Library, introductory change notice](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)

## Q2. Synthetic multiple-testing and reliability counterexamples

If 20 independent null tests each have false-positive probability 0.05, the
chance of at least one false positive is 1-(1-0.05)^20 = 64.151408%. Dependence
changes that number; it does not make the selected best result automatically
valid. This is a probability identity, not an estimate of this vault's error rate.

Even zero failures in 10 independent Bernoulli case families gives the one-sided
95% exact upper failure-rate bound 1-0.05^(1/10) = 25.886555%. Repeated variants
of one scenario do not become 10 independent observations. For a production
claim use the prespecified protocol and its actual sampling unit, denominators,
confidence procedure and multiple-comparison correction.

## Q3. Economic and negative controls

Compare applicable simple baselines under the same prices, scope, constraints
and costs. Show where a sophisticated method loses. Shuffle or lag eligible
features, inject unavailable later revisions, remove a necessary input, and
include a true no-edge process. A control failure invalidates the affected
comparison, even if its headline Sharpe ratio is high.

Use `tournament_runner.simulate_target_weights` through its existing owner for
causal fills and accounting, and the canonical evaluator gateway for protected
assessment. `tools/fis/test_corpus_examples.py` checks Q2 arithmetic only. A
passing software example proves neither an implemented PBO estimator nor
positive expected returns. Preserve the existing preregistration, holdouts,
campaign accounting and prospective promotion requirements unchanged.

prov: script:synthetic independent-test probability identities;
web:original backtest-selection paper and French change notice inspected 2026-09-13.
