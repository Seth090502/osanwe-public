---
aliases: [household constraints tax and sequence risk]
categories: [wiki]
type: reference
tags: [topic/investing]
status: active
created: 2026-09-13
updated: 2026-09-13
related: ["[[fin-cash-flow-framework]]", "[[fin-tax-aware-investing]]", "fin-retirement-planning", "[[ref-fixed-income-liabilities]]"]
---

# Household constraints, tax scope and sequence risk

Public/synthetic method, version 1. All figures are invented. Personal inputs
must remain inside their authorized host. U.S. source scope here is limited to
wash-sale treatment and SSA delayed-retirement credits; this is not a review of
all current tax, benefit, estate or healthcare rules.

## H1. Reconcile cash needs before allocating

Synthetic monthly income 5,000 minus essential spending 3,000, scheduled debt
500 and committed sinking-fund contribution 500 leaves 1,000 before investing.
A 20% income reduction leaves zero. An internal transfer of 1,000 from checking
to savings changes neither total household income nor expenses. Reconcile the
two sides before computing a savings rate. A synthetic liquid reserve 9,000 and
monthly essential need 3,000 gives three months; adequacy still depends on the
household's risks and access restrictions.

## H2. Tax-loss harvesting is not automatically a current tax saving

IRS Publication 550 (2025 edition), chapter 4, Wash Sales, describes substantially
identical replacement purchases within 30 days before or after a loss sale and
replacement-basis treatment. Account and related-party coverage matter.
[IRS Publication 550](https://www.irs.gov/publications/p550)

Synthetic basis 1,000, sale proceeds 800 and taxable replacement cost 850 within
the applicable window give loss 200 and, assuming the entire loss is disallowed,
adjusted replacement basis 1,050. This defers recognition; it does not create
an immediate deduction. If the replacement instead occurs through the taxpayer's
IRA/Roth IRA under Revenue Ruling 2008-5, the ruling disallows the loss without
increasing IRA basis. A taxable-basis adjustment cannot be copied to the IRA.
[IRS Revenue Ruling 2008-5, holding on PDF p. 4](https://www.irs.gov/pub/irs-drop/rr-08-05.pdf)

Verify jurisdiction, tax year, lot identification, related accounts, replacement
security facts and future tax assumptions before comparing after-tax alternatives.
Different tickers alone do not prove that investments are not substantially
identical. The inspected publication is the 2025 edition; it is not a blanket
certification of 2026 thresholds or future law.

## H3. Synthetic sequence risk and benefit scope

Start with 100, withdraw 10 at each year's start, then apply returns. Returns
-20% then +25% leave 77.5 after two years; the reversed order leaves 82. Both
return paths have the same no-withdrawal product. A constant-average-return
projection hides the timing effect. Couple adverse markets with spending,
inflation and income changes; report shortfalls, not only ending wealth.

SSA states that delayed-retirement credits stop at the 70th birthday and depend on birth
year; its table gives 8% per year for 1943 or later. This is a benefit rule, not
a risk-free investment return or a complete claiming optimum. Household longevity,
survivor benefits, taxes, liquidity and healthcare require separate evidence.
[SSA, Delayed Retirement Credits, rate table](https://www.ssa.gov/benefits/retirement/planner/delayret.html)

## H4. Use and limits

Use the existing cashflow workflow, `tools/fis/calcs_household.py` and
`tools/fis/calcs_ledger.py` within their stated scope. H1-H3 arithmetic has
independent synthetic checks in `tools/fis/test_corpus_examples.py`. The household
engine's withdrawal order is a configurable computational default; it is not a
universal tax optimum. Model-simulated success frequency depends on the supplied
return, inflation and survival model and must not be labelled calibrated merely
because many simulations ran. Missing personal scope cannot be repaired by
exporting private account data to an unsupported host.

prov: script:synthetic monthly USD cash needs, wash-sale arithmetic and two-year
withdrawal paths; web:narrow IRS/SSA originals inspected 2026-09-13.
