---
name: fin-cash-flow-framework
aliases: [fin-cash-flow-framework]
categories: [wiki]
type: reference
status: active
created: 2026-08-25
updated: 2026-08-25
tags:
  - topic/finance
related: []
---

categories: [wiki]
type: research-framework
created: 2026-08-24
updated: 2026-08-24
status: active
confidence: HIGH
tags:
  - topic/personal-finance
  - topic/cash-flow
  - topic/planning-template
aliases:
  - cash flow framework
related:
  - "[[fin-tax-aware-investing]]"
  - "[[fin-fixed-income-framework]]"
  - "*fin-retirement-planning* (not published)"
  - "[[fin-risk-transfer]]"

---

# Personal Cash Flow Modeling Framework

Method document. Every `<OPERATOR_INPUT>` slot must be filled with actual
figures before any output from this framework is relied upon. Until filled,
this document defines METHOD ONLY and produces no advice.

ASCII-only. No private figures are stored in this file; private values live
under `.raw/private/finance/` and are never copied here (see
[[fin-compliance-boundaries]]).

## 0. Purpose and scope

This document defines the STRUCTURE for:

1. Modeling income and expenses at monthly resolution.
2. Sinking funds for irregular, predictable liabilities.
3. Sizing the emergency fund from first principles.
4. Forecasting cash flow forward 12-24 months.
5. The integration point where net free cash flow feeds the portfolio's
   deployment band decisions (the calibration engine consumes this output).

It does NOT contain operator figures. It does not read credentials or
account balances directly; it specifies what inputs the operator supplies.

## 1. Income statement template (monthly view)

Fill every slot with trailing-12-month averages unless noted.

```
INCOME (monthly average, trailing 12m)
  A1 Salary, gross .............. <OPERATOR_INPUT>
     (per-paycheck gross x pay periods / 12)
  A2 Bonus, expected ............ <OPERATOR_INPUT>
     (conservative case: historical hit rate x target amount)
  A3 RSU/equity vesting ......... <OPERATOR_INPUT>
     (shares vesting/mo x price x (1 - withholding rate))
     Rule: value at VEST-date price, never grant-date price.
     Vest = income event; hold-vs-sell is a separate decision.
     Never double-count: if sold immediately, income is net proceeds.
  A4 Rental net ................. <OPERATOR_INPUT>
     (gross rent - P&I - taxes - insurance - maintenance reserve)
     Maintenance reserve convention: 1%/yr of property value / 12.
  A5 Business/self-employment ... <OPERATOR_INPUT>
     (net AFTER SE-tax accrual: gross x (1 - 0.9235 x 0.153 x 0.5 approx))
  A6 Interest/dividends (taxable)  <OPERATOR_INPUT>
     (fed back from the investment engine each quarter)
  A7 Other ...................... <OPERATOR_INPUT>
  ------------------------------------------------------------------
  A  TOTAL GROSS INCOME ......... sum(A1..A7)

DEDUCTIONS AND TAXES (monthly average)
  B1 Federal withholding ........ <OPERATOR_INPUT>
  B2 FICA ....................... <OPERATOR_INPUT>
  B3 State/local ................ <OPERATOR_INPUT>
  B4 Pre-tax deductions (401k/HSA/premiums) <OPERATOR_INPUT>
  B5 Estimated tax payments ..... <OPERATOR_INPUT>
  ------------------------------------------------------------------
  B  TOTAL DEDUCTIONS ........... sum(B1..B5)

  N  NET TAKE-HOME .............. A - B
```

### 1.1 Income stability classification

Each income line gets a stability class that later feeds the emergency
fund multiplier (section 3):

| Class | Definition | Examples |
|-------|-----------|----------|
| S1 | Contractual, multi-year | Tenured salary, pension |
| S2 | Stable but replaceable | Standard at-will salary |
| S3 | Variable, positive skew | Bonus, overtime |
| S4 | Volatile both ways   | Business income, rentals w/ vacancy risk |
| S5 | Market-linked        | RSU value, taxable dividends |

Rule: for planning use the CONSERVATIVE case of each class --
S3 at hit-rate-weighted value, S4 at P10 of trailing distribution,
S5 at vest-date-realized only.

## 2. Expense model template

### 2.1 Essential vs discretionary split (load-bearing)

The essential/discretionary boundary is THE most consequential modeling
decision in this document: it drives emergency fund size, the floor of the
deployment band ladder, and retirement target math. Define it once, review
annually, do not let categories drift across the line opportunistically.

```
ESSENTIAL (E) -- obligations that persist through a job loss and
must be paid to preserve health, housing, legal standing:
  E1 Housing: rent/mortgage P&I + tax + insurance <OPERATOR_INPUT>
  E2 Utilities + connectivity baseline <OPERATOR_INPUT>
  E3 Groceries (baseline basket, not dining) <OPERATOR_INPUT>
  E4 Insurance premiums: health/auto/life/umbrella <OPERATOR_INPUT>
  E5 Minimum debt service (all loans, minimums only) <OPERATOR_INPUT>
  E6 Transportation baseline (commute fuel/transit) <OPERATOR_INPUT>
  E7 Childcare/support obligations <OPERATOR_INPUT>
  E8 Medical out-of-pocket baseline (see fin-risk-transfer) <OPERATOR_INPUT>
  ------------------------------------------------------------------
  E  MONTHLY ESSENTIAL TOTAL ....... sum(E1..E8)

DISCRETIONARY (D) -- cuttable within 30 days without breach:
  D1 Dining out, entertainment <OPERATOR_INPUT>
  D2 Subscriptions (audit list annually) <OPERATOR_INPUT>
  D3 Travel <OPERATOR_INPUT>
  D4 Gifts/donations above committed floors <OPERATOR_INPUT>
  D5 Hobby/sport spend <OPERATOR_INPUT>
  D6 Extra principal paydown (reclassified as savings below) <OPERATOR_INPUT>
  ------------------------------------------------------------------
  D  MONTHLY DISCRETIONARY TOTAL ... sum(D1..D6)

IRREGULAR / LUMPY (L) -- handled by sinking funds, section 3:
  L1 Annual premiums (paid monthly into sinking fund) <OPERATOR_INPUT>
  L2 Property tax installment equivalents <OPERATOR_INPUT>
  L3 Vehicle maintenance/replacement accrual <OPERATOR_INPUT>
  L4 Home maintenance accrual (1%/yr of value) <OPERATOR_INPUT>
  L5 Travel planned-but-lumpy <OPERATOR_INPUT>
  L6 Known future events (weddings, moves) <OPERATOR_INPUT>

COMMITTED SAVINGS (S):
  S1 Retirement contributions (beyond payroll pre-tax) <OPERATOR_INPUT>
  S2 Taxable investing transfer (deployment feed) <OPERATOR_INPUT>
  S3 Emergency fund top-up until target met <OPERATOR_INPUT>
  S4 Sinking fund contributions (sum of L accruals) <OPERATOR_INPUT>
```

### 2.2 Budget identity (the constraint that must always hold)

```
N (net take-home) >= E + D + S + (cash sinking-fund contributions)

Free Cash Flow available for deployment:
  FCF = N - E - D - S1 - S3 - (S4 if funded from checking)

If FCF < 0 for two consecutive months: STOP deployment transfers,
diagnose which block leaked (compare actuals vs template), fix the
template before resuming.
```

### 2.3 Actuals capture loop

Monthly close procedure (30 minutes):

1. Export all account transactions to CSV.
2. Tag each transaction E/D/L/S per section 2.1 definitions.
3. Compare tagged totals vs template on a variance report:
   - Any E-line > 110% of template two months running -> re-baseline it.
   - Any D-line > 130% of template one month -> note cause, no re-baseline.
4. Recompute FCF and log to the cash-flow ledger (append-only).
5. Feed quarterly average FCF to the deployment band logic (section 6).

## 3. Sinking fund methodology

A sinking fund converts an irregular liability into level monthly accruals
held in cash/near-cash, so lumpy spending never collides with the
emergency fund or forces untimely asset sales.

### 3.1 Accrual formula

```
monthly_accrual(liability) = expected_total_cost / months_until_due
                             adjusted for cost inflation:
                             = C_now x (1 + i)^n / n_months

where:
  C_now      = today's estimate of the cost  [OPERATOR_INPUT per line]
  i          = category inflation assumption
               vehicles 4%, home repairs 5%, healthcare 6%,
               travel 3% (defaults; override per line)
  n_months   = months until the expense hits
```

Worked example (method illustration, not a recommendation):

```
Roof reserve: current replacement quote $18,000, useful life remaining
12 years. Accrual = 18000 x (1.05)^12 / 144 = ~$212/month.
Vehicle: replacement in 5 years at today's $35,000, i=4% ->
35000 x 1.2167 / 60 = ~$710/month (offset by sale of current vehicle;
use NET cost = replacement - expected trade value).
```

### 3.2 Funding hierarchy and placement

Priority order when cash is scarce:

1. Sinking funds for items due within 90 days (they are effectively
   near-term liabilities, not reserves).
2. Items due within 365 days.
3. Multi-year accruals (roof, vehicle replacement).

Placement rules:

| Horizon | Vehicle |
|---------|---------|
| <= 90 days | Checking or standard savings |
| 91 days - 2 years | High-yield savings / T-bills (4-week rollover) |
| 2 years + | T-bill ladder matching maturity (see [[fin-fixed-income-framework]]) |

Constraint: sinking funds are NEVER invested in equities. They are
liabilities with dates, not capital seeking return.

### 3.3 Sinking fund register template

```
| ID | Item | Target date | Target cost | Inflated cost | Monthly accrual | Balance | Gap |
|----|------|-------------|-------------|---------------|-----------------|---------|-----|
| SF-01 | <OPERATOR_INPUT> | <date> | <amt> | <amt> | <amt> | <amt> | <amt> |
```

Reconciliation rule: balance >= inflated_cost x (months_elapsed /
months_total). If behind for two consecutive reviews, either raise the
accrual or move the date. Never silently underfund.

## 4. Emergency fund sizing formula

### 4.1 Core formula

```
EmergencyFund_target = E_monthly x M

where:
  E_monthly = MONTHLY ESSENTIAL TOTAL from section 2.1
              (includes minimum debt service and sinking-fund floor
              for items due <= 90 days)
  M         = months multiplier, chosen from the table below
```

### 4.2 Multiplier selection table

Start at base, then add/subtract adjustments. Floor 3.0, cap 6.0
(exceptions in notes).

| Factor | Condition | Adjustment |
|--------|-----------|------------|
| Base | single earner, S2 income | 4.5 |
| Base | dual earner, independent industries | 3.5 |
| Base | single earner + dependents | 5.5 |
| Adj | income includes S3/S4 classes > 25% of total | +0.5 |
| Adj | income includes S5 (RSU-heavy) > 40% of total | +0.5 |
| Adj | high volatility industry (layoff cyclicality known) | +0.5 |
| Adj | stable demand profession (healthcare licensure, etc.) | -0.5 |
| Adj | disability coverage replaces > 60% of income | -0.5 |
| Adj | mortgage or other fixed obligations > 35% of N | +0.5 |
| Adj | self-employed (S4 primary) | +0.5 |

Notes:

- Below 3.0 the plan loses its ability to bridge a normal job search;
  treat sub-3.0 as transitional only (e.g., while aggressively funding
  a known obligation), never steady state.
- Above 6.0 there is an opportunity-cost problem: excess belongs in the
  taxable investment engine, not cash. If genuine uncertainty demands
  more than 6 months, solve it with disability/LTC coverage structure
  ([[fin-risk-transfer]]) rather than more cash.
- Retirees/coasters: the emergency fund merges into the cash wedge of
  the withdrawal strategy (*fin-retirement-planning* (not published) section 2).

### 4.3 Tiered construction

Do not build it as one lump; tier it so early dollars are usable early:

```
Tier 1 (first 1 month of E): checking buffer, same-day access.
Tier 2 (next 2 months of E): HYSA, next-day access.
Tier 3 (remainder):          T-bill ladder, <= 5 business day access.
                               rung maturities staggered ~4 weeks apart.
```

Rebuild priority after any draw: Tier 1 first, then Tier 2, then Tier 3.
While rebuilding, pause S2 (taxable deployment transfers); keep employer
match capture (free money outranks rebuild speed).

### 4.4 What counts and what does not

Counts toward target: cash, HYSA, T-bills held expressly for emergencies.
Does NOT count: Roth contribution basis (it is accessible but raiding it
destroys retirement compounding -- treat as last-resort layer documented
in *fin-retirement-planning* (not published), never as the plan), HELOC capacity
(a lender can freeze it exactly when needed), brokerage margin, RSUs
(unvested), sinking funds (they have owners).

## 5. Cash flow forecasting model

### 5.1 Structure: 12-month rolling, monthly resolution

```
For month t in [now .. now+11]:
  OpeningCash(t) = OpeningCash(t-1) + NetFlow(t-1)

  NetFlow(t) = IN(t) - OUT(t)
    IN(t)  = sum over income lines of scheduled amounts
             (salary per calendar; bonus at historical months;
              RSU vests from the vest schedule table; dividends from
              ex-div calendar x yield on current holdings)
    OUT(t) = E(t) + D(t) + S(t) + L_scheduled(t)

  L_scheduled(t): sinking fund ACCRUALS flow monthly; actual lump
  payouts appear on their target dates from the register (sec 3.3).
```

### 5.2 Scenario overlays

Run three scenarios each quarter; record all three, act on the median:

```
BASE:     income at conservative case, expenses at template.
STRESS-1: primary income -100% for 4 months starting month 2;
          D cut to 20% of template immediately.
          Pass criterion: min(OpeningCash) stays > 0 without touching
          investments. If it fails, the gap tells you how many months
          of E the emergency fund must cover -- cross-check vs sec 4.
STRESS-2: one lumpy shock (roof/vehicle/medical deductible) of size
          <OPERATOR_INPUT> lands month 3, income intact.
          Pass criterion: sinking funds absorb it; emergency fund
          untouched. Failure means accrual rates are too low.
```

### 5.3 Dividend and interest feedback

Quarterly, pull actual taxable interest/dividends into line A6 using:

```
expected_monthly_dividends = sum(holdings_i x shares_i x yield_i) / 12
refresh yields from the broker export; do not forecast price appreciation
into cash flow -- only realized distributions are cash.
```

### 5.4 Forecast ledger schema

Append-only CSV maintained alongside this document (values live outside
the wiki; path recorded as pointer only):

```
month, scenario, opening_cash, income_actual, income_fcst,
ess_actual, ess_fcst, disc_actual, disc_fcst, sav_deployed,
sf_balance_total, ef_balance_total, fcf_actual, notes
```

## 6. Integration point: cash flow -> deployment bands

This section is the interface contract between personal cash flow and the
portfolio engine (calibration engine, deployment bands, doctrine in
*fin-governance-framework* (not published)).

### 6.1 The handoff quantity

The cash flow module exports ONE number to the portfolio engine each
quarter:

```
DeployableFCF_q = median monthly FCF over trailing 3 months x 3
                  minus any emergency-fund shortfall vs sec 4 target
                  minus any sinking fund gaps flagged in sec 3.3
```

Rules:

- If EF < target: DeployableFCF_q routes FIRST to EF rebuild, remainder
  (if any) deploys.
- If any SF gap exists for items due <= 365 days: same priority.
- DeployableFCF_q <= 0 means no new capital enters band decisions this
  quarter. Existing holdings are unaffected -- this gate governs NEW
  money only.

### 6.2 How DeployableFCF interacts with deployment bands

The vault's deployment doctrine (decision record
0197-2026-07-06 invest-kernel-doctrine ratification; see also
*research-dgs10-band-2026-07-18* (not published)) scales tranche sizes by regime state.
New-money flow integrates as follows:

```
tranche_size(state) = DeployableFCF_q x band_multiplier(state)

Band multiplier schedule (structural, from doctrine):
  band A (full deployment):   1.00
  band B (partial):           0.50
  band C (hold-cash):         0.00 (accumulate in T-bill sleeve)
  R/R override lane (>= 4:1): may exceed band schedule per doctrine
```

Rate-context note: the store currently reads DGS10 at 4.69%
(p97.2 percentile over all history, p99.0 over trailing 1y) and
DFII10 at 2.35%. Whatever band the regime module selects, the CASH
accumulated in band C sits in the T-bill/Treasury sleeve described in
[[fin-fixed-income-framework]], earning the short rate rather than idle
checking rates. Cash-flow forecasting (sec 5) treats that sleeve's
interest as income line A6 feedback.

Consistency guardrail from the DGS10 band research: the hard
"DGS10 > 4.40 -> 0.0x" level gate was found NOT well-founded as a
return predictor (yield LEVEL fails out-of-sample; valuation carries
the signal). This framework therefore treats cash accumulation during
band C as a liquidity-planning outcome, NOT as a market-timing opinion.
The band selection itself belongs to the calibration engine.

### 6.3 Reverse integration: portfolio events that hit cash flow

The interface runs both directions. The portfolio engine must notify the
cash flow model of:

| Event | Cash flow treatment |
|-------|--------------------|
| Realized gains distributed (fund cap-gains) | A6 income, taxed per [[fin-tax-aware-investing]] |
| Margin/borrowing against portfolio | NEVER modeled as income; modeled as liability with amortization in E5 |
| Option premium received | Income S5-classed; conservative case = 50% haircut |
| Forced sale to cover a cash shortfall | Red flag: sec 4/3 failures upstream; fix cash side, do not normalize raids |

### 6.4 Quarterly review checklist

1. Fill all new OPERATOR_INPUT slots that changed (raises, new debts,
   premium changes).
2. Re-run three scenarios (5.2); log pass/fail.
3. Recompute EF target vs actual; set rebuild pace if short.
4. Recompute DeployableFCF_q; publish to the deployment module.
5. Audit sinking fund register for new lumpy liabilities discovered
   during the quarter.
6. Confirm the E/D boundary still matches reality (drift audit).

## 7. Worked end-to-end example (synthetic numbers)

Illustration only; all numbers fictional and rounded.

```
Income (conservative case): N = $8,000/mo take-home
Essentials E = $4,200  Discretionary D = $1,300
Committed savings S1(retirement)=$800  S4(sinking)= $700
FCF = 8000 - 4200 - 1300 - 800 - 700 = $1,000/mo

EF target: single earner + dependents base 5.5, S5 income >40% (+0.5),
stable profession (-0.5) => M = 5.5
EF target = 4200 x 5.5 = $23,100
Current EF $14,000 -> shortfall $9,100 -> rebuild pace $750/mo
=> DeployableFCF_q = 1000 x 3 - 2250 = $750/quarter routed to markets.

Stress-1 test: income zero months 3-6, D cut to $260.
Burn = 4200 + 260 + 700(SF) = $5,160/mo x 4 = $20,640 vs EF+cash tiers
$16,000 -> FAILS -> either raise M via coverage (disability) or accept
documented reliance on the Roth basis layer (last resort).
Decision recorded; EF rebuild continues before any deployment increase.
```

## 8. Failure modes catalog

| Failure | Detection | Correction |
|---------|-----------|------------|
| E/D boundary drift | annual drift audit | re-tag categories, recompute EF |
| RSU double-count | audit A3 vs brokerage sales | value-at-vest OR proceeds, never both |
| Bonus counted at 100% | variance report | switch to hit-rate weighting |
| Sinking fund raided silently | register reconciliation | restore + raise accrual 10% |
| EF sized off GROSS income | review sec 4.1 | essentials-based only |
| Deployment feed ignores SF gaps | quarterly checklist step 4 | enforce priority order |
| Forecast uses appreciated prices as cash | 5.3 rule | realized distributions only |

## Appendix A. Category boundary adjudication rules

The E/D/L/S tagging in section 2.1 will generate disputes. Resolve them
with these standing rules rather than case-by-case judgment:

```
R1 Debt principal vs interest: minimum INTEREST is essential (E5);
   EXTRA principal paydown is savings (S-class), never essential.
R2 Child activities: baseline school costs essential; competitive/
   travel teams discretionary unless a documented commitment exists
   (then L, sinking-funded).
R3 Pets: food/routine vet = E or D per operator's declared standard
   of care; emergency vet = sinking fund or EF draw -- decide BEFORE
   acquiring the animal and record it.
R4 Charitable giving: recurring committed gifts are S (a contract,
   not consumption); spontaneous generosity is D.
R5 Home repairs: under $500 routine -> D; planned items -> L accrual;
   true emergencies -> EF. The 1%/yr L4 accrual exists precisely so
   "emergency" roof/HVAC events stop hitting the EF.
R6 Healthcare: premiums E4; routine OOP E8; elective procedures D;
   deductible-sized shocks -> EF per design.
R7 Groceries vs dining: the boundary is WHERE, not quality. Any
   restaurant/delivery transaction is D1 even if it replaces groceries.
R8 Insurance deductibles themselves: not separate lines; they size
   the reserves ([[fin-risk-transfer]] T3 test).
```

Disputes not covered here get a written rule added to this appendix --
the appendix grows only by decision, never by silent drift.

## Appendix B. Cash-flow ledger implementation notes

### B.1 File layout

```
finance-ledger/            (lives OUTSIDE wiki, pointer recorded here)
  ledger.csv               append-only actuals (schema sec 5.4)
  forecast.csv             monthly forecast snapshots w/ run date
  scenarios/YYYY-QN.csv    stress-test outputs
  registers/sinking.csv    section 3.3 register, machine-readable twin
```

Privacy compliance: none of these files may be copied into the wiki;
see [[fin-compliance-boundaries]]. The wiki holds METHOD + schemas only.

### B.2 Automation hooks

```
Monthly close script responsibilities (operator-run):
  1. Ingest broker/bank CSV exports from the export directory.
  2. Apply the tag dictionary (rules-based first pass; ambiguous rows
     queued for manual tagging).
  3. Emit variance report vs template.
  4. Append ledger row; recompute FCF; update register balances.
  5. On quarter-end: emit DeployableFCF_q computation with full
     audit trail of subtractions (EF shortfall, SF gaps).
Idempotency: every ingestion keyed on (account, txn_id) to make
re-runs safe.
```

## Appendix C. Emergency fund edge cases

```
C1 Dual-income couple, both incomes needed for E coverage:
   treat as single-earner base (5.5), not dual-independent (3.5).
C2 RSU cliff concentration (large vest scheduled): pre-cliff window
   counts as elevated risk (+0.5) until vest completes and diversifies.
C3 Visa/job-tied residency: job loss may force relocation -- add
   relocation reserve as its own sinking fund line, M floor 6.0.
C4 Known large future liability (lawsuit defense, tax dispute):
   NOT an emergency-fund matter; create a dedicated sinking fund with
   counsel-informed sizing.
C5 Post-retirement transition: EF target steps down as bucket 1
   ramps up; document the crossover month so both balances never
   double-count the same dollar.
```

## Appendix D. Quarterly deployment-band handoff record template

The interface artifact of section 6, filled each quarter:

```
QUARTER: <YYYY-QN>
E_monthly (current): <OI>      EF target/actual: <OI>/<OI>
SF gaps flagged: <list IDs or NONE>
FCF trailing 3mo: <m1> <m2> <m3>; median: <OI>
DeployableFCF_q: <OI>
Band state (from calibration engine): <A/B/C + date read>
Band multiplier applied: <1.00/0.50/0.00>
Tranche authorized: <OI or ZERO - reason code>
Rate context pulled: DGS10=<OI> DFII10=<OI> (factor store, <date>)
Deviations from doctrine: <NONE or decision-record link>
Signatures/review dates: <OI>
```

## 10. Cross-references

- [[fin-tax-aware-investing]]: tax treatment of A6/A3 income flows,
  lot decisions when rebalancing the deployment sleeve.
- [[fin-fixed-income-framework]]: T-bill ladder mechanics for EF Tier 3
  and sinking fund placement; DGS10/DGS30 context from the factor store.
- *fin-retirement-planning* (not published): what happens to E, EF, and FCF at the
  retirement transition; withdrawal sequencing replaces FCF accumulation.
- [[fin-risk-transfer]]: disability and life coverage adjust M (sec 4.2);
  premium costs are E4 lines.
- [[fin-compliance-boundaries]]: privacy rules governing where actual
  figures may be stored.
