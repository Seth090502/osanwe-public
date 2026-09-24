---
aliases: [cash flow aware performance and attribution]
categories: [wiki]
type: reference
tags: [topic/investing]
status: active
created: 2026-09-13
updated: 2026-09-13
related: ["[[ref-financial-statement-evidence]]", "[[ref-portfolio-risk-sensitivity]]", "[[ref-etf-implementation]]"]
---

# Performance measurement and attribution that reconcile

Public/synthetic method, version 1. Portfolio balances, external cash flows,
fees and benchmarks must be complete for the claimed scope. The arithmetic
below is independently checked; it is not GIPS compliance or manager validation.

## P1. Select the return question

True time-weighted return requires valuations at external cash flows and links
subperiod returns geometrically. Money-weighted return reflects the timing and
size of external flows. Label period, annualization, fee/tax basis and treatment
of flows; a method name cannot repair missing valuations.
[GIPS Handbook for Firms, Input Data and Calculation Methodology, TWR/MWR discussion](https://www.gipsstandards.org/standards/gips-standards-for-firms/gips-standards-handbook-for-firms/)

For exact cash-flow boundaries, TWR = product(1 + subperiod return) - 1. For
annual cash-flow dates in P2, IRR r solves 100*(1+r)^2 + 90*(1+r) = 180.
For arbitrary dates state the day-count convention. Some flow patterns have
multiple IRRs or no economically meaningful root; report that ambiguity. If
intermediate valuations are missing, a true TWR may be unavailable while a
clearly scoped MWR is supported. A Dietz estimate is not an exact TWR.

## P2. Synthetic cash-flow trap

Start with USD 100 at year zero. It grows to 110 at year one, immediately before
an external deposit of 90; year two ends at 180. The two investment subperiods
return +10% and -10%: cumulative TWR is -1%, annualized TWR is -0.501256%, and
annual IRR is about -3.490283%. Net investment dollars are -10. Reporting an
80% return from 180/100 - 1 incorrectly counts the deposit as performance.

## P3. Synthetic attribution and currency reconciliation

For segments A/B, portfolio weights 60%/40%, returns 10%/2%, benchmark weights
50%/50% and returns 8%/4% give portfolio return 6.8%, benchmark return 6% and
active return 0.8 percentage points. Using the explicit three-effect convention:
allocation = 0.4 points, selection = 0, interaction = 0.4 points. The sum must
equal active return; retain unexplained residuals rather than assigning them
to skill. This one-period identity is checked against `calcs_ledger.brinson_attribution`.

An asset returning +10% in its local currency with that currency losing 5%
against the reporting currency returns (1.10*0.95)-1 = 4.5% in reporting currency,
assuming no flows/hedging. Adding 10%-5%=5% omits the interaction. Benchmark
currency, total-return convention and economic exposure must match the question.
Sector attribution is descriptive and does not prove causal skill or factor alpha.

## P4. Workflow limits

Use `tools/fis/calcs_ledger.py` for existing reconciliation, currency conversion
and Brinson calculations; `tools/fis/test_corpus_examples.py` checks P2/P3 with
independent arithmetic. These examples do not create a production TWR/MWR
pipeline. Until the owning workflow verifies such a pipeline, label manually
reproduced calculations and their data coverage explicitly. Never infer missing
deposits, taxes, distributions or account transfers from changes in balance.

prov: script:synthetic USD annual cash flows, one-period attribution and FX;
web:GIPS methodology passage inspected 2026-09-13, without compliance certification.
