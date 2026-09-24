---
name: fin-tax-aware-investing
aliases: [fin-tax-aware-investing]
categories: [wiki]
type: reference
status: active
created: 2026-08-25
updated: 2026-09-13
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
  - topic/tax
  - topic/investing
aliases:
  - tax-aware investing framework
related:
  - "[[fin-cash-flow-framework]]"
  - "[[fin-fixed-income-framework]]"
  - "fin-retirement-planning"
  - "[[fin-risk-transfer]]"

---

# Tax-Aware Investing Framework

Method document. All `<OPERATOR_INPUT>` slots are filled at use time from
operator records; this file stores no private figures. ASCII only.
Historical 2026 tax labels below do not establish verified current law. At use
time, inspect authoritative guidance for the applicable tax year, jurisdiction,
account and transaction; record the publication edition and effective date.
The earlier no-network assumption is obsolete. An annual checklist supplements,
but cannot replace, current verification for a consequential conclusion. The
2026-09-13 review inspected IRS Publication 550 (2025 edition) and Revenue Ruling
2008-5 for wash-sale scope only; it did not certify all thresholds in this file.
See [[ref-household-tax-retirement]] for that bounded source review and synthetic
counterexamples. Keep other unsupported tax-dependent conclusions unavailable.

## 0. Scope and governing principles

1. After-tax return is the objective; pre-tax alpha gained and given back
   to the tax code is not alpha.
2. Tax decisions are SECOND-ORDER: never let a tax tail wag the portfolio
   dog. The doctrine and calibration engine decide WHAT to own and in what
   bands; this framework decides WHERE (location), WHEN to realize
   (harvesting/gains planning), and WHICH LOT to sell.
3. Bracket arbitrage is the biggest lever: fill low-bracket years
   (Roth conversions, gain harvesting) and unload high-bracket years.
4. Every rule here is US federal unless stated; state treatment gets an
   OPERATOR_INPUT check.

## 1. Asset location optimization

### 1.1 Account inventory template

```
| Account | Type | Balance | Basis | Owner | Contribution room status |
|---------|------|---------|-------|-------|--------------------------|
| ACC-01 | taxable brokerage | <OPERATOR_INPUT> | <OI> | <OI> | n/a |
| ACC-02 | Roth IRA         | <OI> | n/a | <OI> | <OI> |
| ACC-03 | traditional/401k | <OI> | n/a | <OI> | <OI> |
| ACC-04 | HSA              | <OI> | n/a | <OI> | <OI> |
| ACC-05 | 529 / other      | <OI> | <OI> | <OI> | <OI> |
```

### 1.2 Tax-efficiency ranking of asset classes

Rank assets by how much of their total return would be destroyed by
annual taxation if held in a fully-taxable account:

```
Rank 1 (most tax-toxic -> shelter FIRST):
  - Corporate/high-yield bonds, bank loan funds (ordinary income coupons)
  - REITs (non-qualified dividends, ordinary + 199A partial)
  - Active strategies with high turnover (short-term gains)
  - Commodities/MLPs with K-1 ordinary income

Rank 2:
  - Broad active equity funds with moderate turnover
  - International equity WITH foreign tax credit eligibility
    (note: FTC only claimable on taxable accounts)

Rank 3 (most tax-friendly -> taxable accounts are fine):
  - Broad index equity ETFs (in-kind redemptions, low distributions)
  - Individual stocks held long-term, buy-and-hold
  - Municipal bonds for high brackets
  - TIPS held via ETF vs direct: direct T-bill/TIPS interest is state-
    exempt; fund wrappers vary -- check per holding
```

### 1.3 Placement decision procedure

```
For each asset class A in rank order 1..3:
  Step 1. Compute total desired exposure from the allocation engine.
  Step 2. Place A into accounts in this order until filled:
     Rank 1 assets -> traditional/pre-tax first (defers ordinary-type
                      income), then HSA, then Roth ONLY if pre-tax full,
                      taxable last.
     Rank 2 assets -> split by FTC need: international slice in taxable
                      to capture FTC if operator bracket makes FTC
                      valuable <OPERATOR_INPUT: marginal bracket>;
                      remainder follows Rank 1 logic but may land taxable.
     Rank 3 assets -> taxable account absorbs them; they are the
                      "location shock absorber".
  Step 3. Constraint checks:
     C1 Do NOT create wash-sale interactions between accounts when
        harvesting (section 2) -- location changes must respect the
        30-day windows across ALL accounts including IRAs.
     C2 RMD-bearing accounts (traditional) should not be loaded with
        the highest-growth assets IF projected RMDs will push the
        operator into higher brackets late-life <OPERATOR_INPUT:
        projected balance>. This is the classic "Roth holds growth"
        counterargument to naive rank ordering; resolve by projecting.
     C3 Estate flexibility: appreciated taxable lots get step-up at
        death; ultra-long-horizon appreciators therefore lean taxable.
```

### 1.4 Location value estimate (method)

Approximate annual value of correct placement:

```
V_location = exposure_tax_toxic x (yield_ordinary x marginal_rate)
           + equity_exposure x turnover_drag x LTC_rate_differential
Defaults: yield_ordinary ~ current DGS10-informed coupon environment;
with the factor store reading DGS10 at 4.69%, new-quality bond coupons
sit near 4.5-5.0% nominal, so a Rank 1 bond sleeve in a 32% bracket
burns roughly 150 bps/yr if mislocated to taxable -- quantify with
<OPERATOR_INPUT: actual yields and bracket>.
```

## 2. Tax-loss harvesting protocol

### 2.1 Trigger discipline

Harvesting runs as a scheduled weekly scan during high-volatility
regimes and monthly otherwise, not ad-hoc:

```
Scan rule: for each taxable lot,
  unrealized_loss_pct = (cost_basis - price) / cost_basis
  Harvest candidate if loss_pct >= threshold_t
  threshold_t default 10%, or absolute loss >= $500, whichever hits
  first. Tighten thresholds in calm markets; loosen in drawdowns
  (the calibration engine's volatility state sets the cadence).
```

### 2.2 Wash sale rules (hard constraints)

```
W1 No purchase of "substantially identical" security within -30 days
   through +30 days around the sale date, in ANY account (taxable,
   IRA, Roth, spouse's accounts).
W2 Replacement-window protocol: freeze BUY orders on the sold ticker
   (and any proxy) for 61 days calendar; automated dividend reinvest
   must be DISABLED on the sold ticker before the sale settles.
W3 Loss disallowed on the sale is added to replacement-lot basis; if
   replaced in an IRA the loss is PERMANENTLY lost (Rev. Rul.
   2008-5). Never replace harvested positions inside an IRA.
W4 Substantially identical test: same CUSIP is always identical.
   Different index funds tracking different indices are generally
   NOT identical; same-index-different-provider is gray -> use pairs
   that track DIFFERENT indices to stay clearly safe (pair table 2.4).
W5 Selling all shares of a ticker then buying back after 31 days is
   safe even if the pair trade was imperfect.
```

### 2.3 Harvest execution template

```
INPUT: lot list meeting 2.1 threshold
FOR each candidate:
  1. Confirm no open buy orders / DRIP on ticker or pair partner.
  2. Select LOTS: highest-basis lots first among losers (HIFO within
     losses maximizes realized loss; see section 3).
  3. Execute sell; SAME DAY execute buy of pair security (minimize
     market exposure gap; intraday is fine).
  4. Log: date, ticker, lots, realized loss, pair bought, un-freeze
     date = sale+31 days.
  5. Calendar entry to review re-conversion at day 31: optional swap
     back (resets nothing new) or hold pair.
Pair selection table (illustrative, verify current tracking):
  S&P 500 broad      <-> Total-market-slice or large-value blend
  NASDAQ-100 proxy   <-> Large-growth different-index fund
  International dev  <-> Global ex-US different provider/index
```

### 2.4 Loss ledger and carryforward management

```
Maintain: capital_loss_carryforward_st (short-term) and _lt (long-term),
updated each filing year from Schedule D / Form 8949 results.
Use priority: ST losses offset ST gains first, LT offset LT; netting
order ST-first then cross-offset. When realizing GAINS deliberately
(section 4), spend carryforwards before they expire conceptually --
they do not expire federally, but their USE has opportunity cost.
$3,000/yr ordinary-income offset applies to net negative.
```

## 3. Tax lot management

### 3.1 Lot method decision table

```
Situation                                   -> Method
Realizing LOSSES (harvest/rebalance down)    -> HIFO (highest basis)
                                                or Specific ID of max-loss lots
Small GAINS, low bracket year                -> HIFO to minimize gain, OR
                                                specific-ID lots with highest basis
Large gain realization planned               -> Specific ID: pick lowest-basis
                                                LONG-TERM lots (maximize LTC
                                                treatment AND minimize nominal gain)
Raising basis intentionally (low-income year)-> sell LOWEST basis lots
                                                (gain harvest resets basis UP)
Default standing instruction at broker       -> Specific ID (NOT FIFO, NOT avg)
                                                <OPERATOR_INPUT: confirm broker
                                                default changed to SpecID>
```

Rule: average-cost is acceptable ONLY where lot-level ID is unavailable
(some ESPP/RSU plans); switch to specific-ID at first transfer out.

### 3.2 Lot hygiene procedures

1. At every purchase record: date, shares, price, fees, account.
2. At every vest (RSU): basis = FMV at vest (income already taxed);
   note vest-date FMV in the ledger immediately -- brokers sometimes
   show zero basis for supplemental shares.
3. Quarterly: reconcile broker lot data vs local ledger; drift means
   a missed corporate action (spinoff, merger) -- resolve before next
   sale.
4. Mutual funds: confirm the fund's declared method once; changing
   methods requires IRS consent for some structures.

### 3.3 Holding-period clock discipline

```
Long-term threshold: > 1 year + 1 day. Standing checklist before ANY
gain sale:
  [ ] Days-held >= 366? If 360-365, delay sale past the line unless
      thesis risk outweighs ~15-20pt rate differential.
  [ ] Any pending corporate action that could alter lots?
  [ ] Wash-sale window clear for paired tickers?
Rate differential input (2026 schedule, single/MFJ verify):
  0%   bracket up to ~$48k single / ~$96k MFJ taxable income
  15%  middle brackets up to ~$533k/$600k
  20%  above
  +3.8% NIIT over the NIIT threshold (section 5)
Effective spread ST-vs-LT at top: 37% + 3.8% vs 20% + 3.8% => ~17pts.
```

## 4. Long vs short-term capital gains planning

### 4.1 Gain realization planner

Each year between October 1 and December 15 run the projection:

```
ProjectedTaxableIncome_y = wages + interest + dividends + realized
                           gains YTD + other <OPERATOR_INPUT fills>
Then compute headroom to each LTC breakpoint:
  H0 = headroom to 0% LTC bracket ceiling
  H15 = headroom to 15%->20% boundary
  HNIIT = headroom to NIIT threshold ($200k single / $250k MFJ MAGI)
Actions available in headroom (priority):
  1. Realize LTC gains up to H0 at ZERO federal rate (rebases basis
     up; pairs perfectly with future loss harvesting).
  2. Roth conversion up to bracket headroom (see retirement doc
     integration, [[fin-retirement-planning]] sec 6).
  3. Defer remaining realizations to future years if ST/LT clock
     allows; else accept 15%.
December trap: mutual fund capital-gains distributions land in Q4;
check published CGE estimates in November BEFORE finalizing
realizations -- an unplanned distribution can consume your H0/H15
headroom retroactively.
```

### 4.2 Short-term gain policy

Standing policy: ST gains are realized only when (a) required by the
deployment doctrine's band actions, (b) covered by existing loss
carryforwards, or (c) thesis exit demands it. Otherwise apply the
clock discipline of 3.3. Quantify the ask: an ST realization costs
~17 points vs waiting -- the position must have >17pt expected
deterioration risk to justify early exit on tax grounds alone.

## 5. NIIT and AMT awareness

### 5.1 NIIT (Net Investment Income Tax, 3.8%)

```
Applies to net investment income when MAGI > threshold:
  $200k single/HoH, $250k MFJ (NOT indexed for inflation).
NII includes: interest, dividends, LTCG, royalties, passive rental.
Excludes: wages, SE income, distributions from qualified plans/Roths,
active-passive-election real estate professional income.
Management levers:
  L1 Shift bond coupons to municipal or pre-tax accounts near the
     threshold (location interacts with sec 1).
  L2 Spread large one-time gains (home sale beyond 250/500k
     exclusion, business sale) across years where possible.
  L3 Installment sales push NII forward; model with discount rate =
     DGS10 4.69% context (a dollar deferred at 4.69% nominal
     discount needs ~1.05x next year just to break even nominally).
  L4 Max pre-tax deferrals reduce MAGI directly (401k, HSA, SEP).
```

### 5.2 AMT awareness

```
AMT triggers for typical investors:
  - Large ISO exercises (spread = AMT preference item)
  - High state-tax deductions post-TCJA cap (SALT cap interplay)
Protocol for ISO grants <OPERATOR_INPUT: if applicable>:
  1. Before exercising, compute AMT crossover shares (shares whose
     exercise keeps tentative AMT <= regular tax).
  2. Exercise up to crossover; hold >= 2y from grant AND 1y from
     exercise for QSBS-style LTC treatment on the ISO spread.
  3. If AMT is paid on ISO exercise, AMT credit (Form 8801) refunds
     it in later non-AMT years -- model the timing, don't fear it.
  4. Same-year sale of exercised ISOs = disqualifying disposition ->
     converts spread to ordinary comp; usually fine if price fell
     below exercise (avoids paying tax on phantom gain).
Annual check: run Form 6251 estimate whenever ISO exercises, large
K-1 items, or big municipal-bond private-activity interest appear.
```

## 6. Calibration engine integration

The calibration engine (doctrine in fin-governance-framework;
bands referenced by [[fin-cash-flow-framework]] sec 6) consumes tax
state as CONSTRAINTS and INPUTS, not as objectives:

### 6.1 Interface contract

```
EXPORTS from tax module (quarterly refresh):
  T1 loss_carryforward {st, lt}            # offsets rebalancing gains
  T2 ytd_realized {st_gain, lt_gain, st_loss, lt_loss}
  T3 projected_MAGI and headroom map (H0, H15, HNIIT)
  T4 lot_clock_risk: positions 300-365 days held with embedded gains
  T5 location_drift: % of Rank-1 assets sitting in taxable

IMPORTS from engine:
  E1 target allocation deltas (what rebalances are wanted)
  E2 band state (A/B/C) controlling action urgency
  E3 volatility regime setting harvest scan cadence
```

### 6.2 Decision routing table

| Engine wants | Tax module routes to |
|---|---|
| Sell overweight asset | Sec 3: specific-ID lowest-basis LT lots; check T4 clocks |
| Buy underweight asset while holding losses elsewhere | Sec 2: harvest loser, fund purchase with pair swap |
| Rebalance in band A (calm) | Prefer directing NEW DeployableFCF ([[fin-cash-flow-framework]]) instead of selling -> zero tax |
| Rebalance in band B/C | Selling allowed; harvest simultaneously; use carryforwards (T1) |
| Engine flags valuation-driven trim | Check H15 headroom (T3); stage trim across Dec-Jan to split tax years |

### 6.3 Rate-context note

With DGS10 at 4.69% (factor store, p97-all percentile), the opportunity
cost of tax-deferral timing math changes: deferring a tax payment one
year saves cash that can now earn ~4.7% riskless short-term. This
raises the value of DEFERRAL tactics (pre-tax contributions, installment
gains, avoiding premature realizations) relative to the zero-rate era.
Conversely DFII10 at 2.35% says the REAL discount rate is moderate;
do not over-extrapolate nominal deferral benefits into real terms.

## 7. Worked example (synthetic numbers)

```
Operator: MFJ, projected MAGI $210k, no YTD realizations.
Headroom: HNIIT exhausted ($210k > $250k? NO -> $40k left);
H15: taxable income far below 15->20 boundary (~$600k) -> ample.
Illustrative holdings: <ticker-1> lot -$12k loss (LT), target trim on <ticker-2> +$30k LT gain.
Action: harvest <ticker-1> -$12k into pair <ticker-1-alt> same day; realize <ticker-2> LT
+$12k of lowest-basis lots (net gain $0); remaining $18k trim staged
to January (splits tax years, preserves H15 for next year's plan).
Freeze: <ticker-1> buys blocked 61 days incl. DRIP-off confirmation.
Carryforward unchanged; NIIT avoided on netted amount.
```

## 8. Failure modes catalog

| Failure | Consequence | Guard |
|---|---|---|
| DRIP left on during harvest | Wash sale | Pre-sale checklist W2 |
| Replacement bought in IRA | Permanent loss (RR 2008-5) | W3 hard ban |
| FIFO default at broker | Wrong lots sold, excess gain | Confirm Specific-ID quarterly |
| Sale at 364 days | ~17pt rate penalty | T4 clock report weekly |
| December CGE surprise | Consumed headroom | November CGE check |
| ISO exercise without AMT calc | Surprise AMT bill | Sec 5.2 protocol |
| Harvesting in band C panic | Tax churn without doctrine cover | Routing table 6.2 |

## Appendix A. RSU / equity compensation tax module

### A.1 Lifecycle and the double-tax trap

```
Events:
  Grant  -> generally no taxable event (ISO) or FMV-subject-to-forfeit
            (NQSO rules vary; RSUs: nothing yet).
  Vest   -> TAXABLE at FMV on vest date (RSU/NQSO): W-2 income.
            Basis = FMV already taxed. THE TRAP: brokers often report
            cost basis ZERO on supplemental info -> selling immediately
            after vest realizes ~zero ADDITIONAL gain/loss, not a full
            gain. Record vest-date FMV per lot (sec 3.2 rule 2).
  Sale   -> capital gain/loss = proceeds - vest-date basis ONLY.
  ESPP   -> disqualifying disposition converts holding-period spread
            to ordinary income; qualifying disposition gets favorable
            treatment; track both clocks from purchase date.
```

### A.2 Sell-at-vest standing policy evaluation

```
Sell-at-vest pros: eliminates single-stock concentration instantly;
income event already taxed; rebalances without wash-sale complexity
(if repurchasing broad funds).
Hold-at-vest pros: defers nothing (tax already owed) -- the only real
argument is expected outperformance; treat as ACTIVE bet against
doctrine diversification, size it explicitly:
  max_concentration = x% of net worth in employer stock <OPERATOR_INPUT,
  common discipline 10%; above that, sell down regardless of view.
10b5-1 hygiene: if operator is an insider, all sales via pre-set plan;
never discretionary around earnings windows.
```

### A.3 Withholding shortfall management

Employer supplemental withholding is frequently BELOW the true marginal
rate (flat 22% federal supplemental rate vs 32%+ bracket). Protocol:
project annual vest income in January; compute true liability; make
quarterly estimates or increase W-4 withholding to cover the gap --
underpayment penalties are avoidable with safe-harbor (110%/100% of
prior-year tax).

## Appendix B. State tax overlay template

```
S1 Resident state + rate structure <OPERATOR_INPUT>.
S2 States taxing municipal interest from other states: affects muni
   selection ([[fin-fixed-income-framework]] sec 4.1 in-state rule).
S3 Treasury interest state exemption value: at high state rates this
   materially lifts TEY of Treasuries vs bank CDs/corporates.
S4 Move-year planning: part-year residency allocates income; large
   realizations/conversions timed relative to move dates need counsel.
S5 No-income-tax states: location math simplifies; munis lose their
   state kicker -> Treasuries/TIPS often win outright.
```

## Appendix C. Charitable giving integration

```
G1 Appreciated-stock-first rule: gifts funded with LT appreciated
   shares (basis lots chosen by specific-ID to give away HIGHEST
   basis? NO -- gift the LOWEST-basis lots: deduction = FMV, embedded
   gain never realized). Keep highest-basis lots for future sales.
G2 DAF bunching: multi-year giving budget front-loaded into peak-
   bracket years; distributions to charities over time.
G3 QCD handoff at 70.5+: see [[fin-retirement-planning]] sec 4.3;
   QCDs replace cash gifts FIRST, stock gifts remain for larger sums.
G4 Wash-sale note: donating a losing lot does NOT harvest the loss
   usefully for shares gifted directly (no sale); if harvesting AND
   giving, sell+harvest then gift cash, or gift the loser to charity
   (charity gets basis too -- usually gift WINNERS instead).
Decision default: winners to charity, losers harvested, cash from the
resulting proceeds.
```

## Appendix D. Tax calendar (recurring obligations)

```
JAN: prior-year forms inventory starts (1099s arrive Feb);
     confirm carryforward balances.
APR/JUN/SEP: quarterly estimate checkpoints (if applicable); safe
     harbor review each APR.
OCT: extension deadline if filed; begin Q4 headroom planning.
NOV: mutual fund CGE estimates pulled; final harvest scan of year.
DEC 15: realization freeze (sec 4.1 window closes); last conversions.
JAN (new yr): prior-year realization split check; IRMAA lookback
     refresh [[fin-retirement-planning]] R5.
```

## Appendix E. Glossary anchors

```
MAGI ........ modified AGI; drives NIIT, IRMAA, PTC, SS taxation.
HIFO ........ highest-in-first-out lot selection.
Wash sale ... loss disallowance on substantially identical repurchase
              within +-30 days (sec 2.2).
TEY ......... taxable-equivalent yield comparison basis (muni math).
CGE ......... capital gains estimate (fund's planned Q4 distribution).
QCD ......... qualified charitable distribution from IRA, sec 6 of
              [[fin-retirement-planning]].
FTC ......... foreign tax credit (international fund dividends).
De minimis .. market-discount rule affecting cheap munis (FI doc 4.2).
```

## 9. Annual verification tasks (operator)

1. Verify brackets/LTC breakpoints/NIIT thresholds vs current IRS rev.
2. Pull 1099 composite estimates in Nov; rerun headroom map.
3. Confirm carryforward balances vs prior-year Schedule D.
4. Re-run location drift report (T5); fix worst offender only.
5. Confirm broker default lot method still Specific-ID.

## 10. Cross-references

- [[fin-cash-flow-framework]]: DeployableFCF feeds band actions;
  dividends/interest lines feed MAGI projection.
- [[fin-fixed-income-framework]]: muni vs Treasury placement detail;
  TIPS wrapper taxation (phantom income) handling.
- fin-retirement-planning: Roth conversions, QCDs, RMD-MAGI
  interaction with IRMAA and NIIT.
- [[fin-risk-transfer]]: insurance premiums and P&C structure do not
  generate NII; disability benefit taxability depends on who paid
  premiums (employer-paid = taxable).
- [[fin-compliance-boundaries]]: storage rules for returns/tax docs.
