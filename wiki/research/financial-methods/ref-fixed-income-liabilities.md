---
aliases: [fixed income and liability matching method]
categories: [wiki]
type: reference
tags: [topic/investing]
status: active
created: 2026-09-13
updated: 2026-09-13
related: ["[[fin-fixed-income-framework]]", "[[ref-household-tax-retirement]]", "[[ref-portfolio-risk-sensitivity]]"]
---

# Fixed income matched to cash needs

Public/synthetic method, version 1. A liability has a date, currency, nominal or
real basis and permitted uncertainty. Match those before comparing quoted yields.
No current rate, credit recommendation or household liability is embedded here.

## B1. Discount the actual cash flows

For annual-pay fixed cash flows, price = sum(CF_t/(1+y)^t). Coupon is not yield,
and a clean quote excludes accrued interest. State settlement date, day count,
frequency and price basis. A flat-yield calculation is not a yield-curve model.
For multiple maturities use appropriately dated discount factors and examine
nonparallel curve shocks; duration matching alone cannot remove credit, liquidity,
reinvestment or convexity risk. Calls and prepayments need state-dependent cash flows.

## B2. Synthetic bond, inflation and liability examples

A synthetic two-year bond, face USD 100 with annual coupon 5, is worth 100 at
5% yield. At 6% it is 5/1.06 + 105/1.06^2 = 98.166607. A separate certain USD 100
liability due in two years has PV 100/1.05^2 = 90.702948 under the stated flat 5%
discount assumption. Buying a bond fund with a similar duration is not a promise
to deliver that exact liability amount on its due date.

For synthetic TIPS original principal USD 1,000, index ratio 1.03 and annual
coupon 1%, adjusted principal is 1,030 and the semiannual coupon is 5.15.
TreasuryDirect explains inflation adjustment and the maturity principal floor;
this floor does not protect a purchaser's secondary-market price or an early
sale. Nominal yield 5% and real yield 2% imply a simplified compounded inflation
break-even of 1.05/1.02-1 = 2.941176%, rather than exactly 3%. Observed spreads also
reflect risks/frictions; the arithmetic is not an inflation forecast.
[TreasuryDirect, TIPS, principal adjustment and interest](https://www.treasurydirect.gov/marketable-securities/tips/)

## B3. Use and limits

Use `tools/fis/calcs_core.py` for the supported bond, present-value, accrued
interest and duration calculations. `tools/fis/test_corpus_examples.py` checks
B2 against independent rational arithmetic. These checks cover fixed coupon-date
examples, not all settlement conventions or stochastic credit models. Preserve
separate source evidence for issuer terms, call schedules, default recoveries,
taxability and current curves.

Compare a cash reserve, a matched maturity ladder and a fund under the same
liability horizon and tax assumptions. Test a rate rise together with income
loss or forced-sale demand. A high yield can compensate for risk rather than
provide a free improvement. Existing allocation and execution gates remain owned
by their current workflows.

prov: script:synthetic annual USD fixed cash flows and explicitly assumed inflation;
web:TreasuryDirect TIPS mechanics inspected 2026-09-13.
