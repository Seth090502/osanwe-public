---
aliases: [valuation applicability and cash flow bridge]
categories: [wiki]
type: reference
tags: [topic/investing]
status: active
created: 2026-09-13
updated: 2026-09-13
related: ["[[institutional-methods]]", "[[ref-financial-statement-evidence]]", "[[ref-scoring-models]]", "[[ref-valuation-methodology]]"]
---

# Valuation applicability and a reproducible enterprise-to-equity bridge

Public/synthetic method, version 1. Model selection precedes arithmetic. No
current market prices, recommended positions or calibrated success probabilities
are supplied by this note.

## V1. Choose the claim being valued

Operating-company FCFF discounts cash available to enterprise capital providers
at WACC, then reconciles cash, debt and other claims to equity. Revenue times an
operating margin is operating income, not enterprise value. Require taxes,
reinvestment, forecast timing and a supported continuing-value treatment.
Terminal growth must fund reinvestment: terminal reinvestment rate = g / ROIC,
and terminal FCFF = terminal NOPAT * (1 - g / ROIC). Require g < terminal WACC.
[Damodaran, Excess Returns and Terminal Value, firm cash-flow discussion](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/valquestions/termvalueexreturns.htm)

For banks and insurers, debt and reinvestment have different economic meanings.
Inspect regulatory capital and asset quality, and choose supported equity cash
flow, dividend or excess-return models. A general operating-FCFF calculation is
not a substitute. [Damodaran, Valuing Financial Service Firms (2009), pp. 1-2, 5](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/finfirm09.pdf)

Losses alone do not make original Piotroski scores undefined. Positive
profitability is a scored condition in a high book-to-market population; the
paper includes loss firms. Local routing and score weights remain separately
owned policy. [Piotroski, Selected Paper 84, printed p. 7, footnote 3 and section 2.3.1](https://www.chicagobooth.edu/~/media/FE874EE65F624AAEBD0166B1974FD74D)

## V2. Synthetic valuation and falsifier

Use annual synthetic USD millions: revenue 1,000; growth zero; operating margin
20%; tax rate 25%; reinvestment zero; WACC 10%. Stable terminal growth is zero,
terminal ROIC 15%, terminal margin/tax/WACC unchanged. One explicit year gives
FCFF 150 and terminal value 1,500 at year-end; their discounted sum is EV 1,500.
Cash 100 minus debt 300 minus other claims 50 gives equity 1,250. With 100 million
diluted shares, value is USD 12.50 per share.

Holding those assumptions fixed, an illustrative USD 15 price requires EV 1,750,
hence FCFF 175 and operating margin 23.333333%. This is a computed price-implied
requirement, not a forecast. A decision based on 20% margins must explain that gap.
For an explicitly assumed non-GAAP EBIT 240 that excludes SBC 40 and has no other
adjustments, GAAP EBIT is 200. Adding SBC again gives the wrong direction. Avoid
double-counting SBC costs across modeled dilution, cash flow and equity claims.

## V3. Use and counterexamples

The executable owner is `tools/fis/valuation.py`: `OperatingDCF`, `operating_dcf`
and `implied_operating_margin`. Preserve exact input IDs and results. V2 is
checked against an independent rational-number oracle by
`tools/fis/test_corpus_examples.py`. Distress, leases, NOLs, pensions and evolving
dilution require supported adjustments or a different model; the CLI cannot
infer them from a ticker.

An impressive fit to historical multiples is not an intrinsic-value proof.
Keep all predictors, units and snapshot dates when using a fitted regression.
An uncalibrated execution haircut is a scenario assumption. Compare coupled
growth/margin/reinvestment/discount scenarios and a simple applicable alternative;
do not average incompatible methods into false certainty.

prov: script:synthetic V2 annual USD valuation and independent arithmetic;
web:the named original passages inspected 2026-09-13. This scope does not certify
an entire textbook, issuer model, local score calibration or investment outcome.
