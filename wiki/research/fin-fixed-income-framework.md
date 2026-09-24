---
name: fin-fixed-income-framework
aliases: [fin-fixed-income-framework]
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
  - topic/fixed-income
  - topic/bonds
aliases:
  - fixed income framework
related:
  - "[[fin-cash-flow-framework]]"
  - "[[fin-tax-aware-investing]]"
  - "fin-retirement-planning"

---

# Fixed Income Allocation Framework

Method document; populate `<OPERATOR_INPUT>` slots with live figures at
use time. Rate inputs come from the vault's factor store
(`tools/factor-store.py`, mcp:fred DGS10/DGS30/DFII10 series), never from
hardcoded literals in prose. ASCII only.

## 0. Current rate context (factor store)

Reference snapshot at last vault refresh (2026-07/08 window):

```
DGS10  = 4.69%   percentile: 99.0 all-history / 97.2 trailing-1y
DGS30  = 5.23%   percentile: ~99.8 all-history
DFII10 = 2.35%   percentile: ~98.7 all-history
Implied 10y breakeven inflation ~= DGS10 - DFII10 ~= 2.34%
```

Usage rules:

1. Discount rates, breakevens, and ladder yield assumptions MUST be
   pulled fresh via `python tools/factor-store.py --query-bars DGS10`
   (and siblings) before any computation; the numbers above are context,
   not inputs.
2. Doctrine note (research-dgs10-band-2026-07-18): the 10Y LEVEL is
   a weak return predictor; use it here only for what it directly
   prices -- bond math, discounting, and reinvestment assumptions --
   not as an equity timing gate.
3. At 4.69% nominal / 2.35% real on the 10y, the term structure pays
   genuinely positive real yield out to a decade: this changes default
   answers vs the zero-rate era (cash and duration are no longer
   dead weight).

## 1. Bond ladder construction methodology

### 1.1 Purpose

Convert capital into scheduled maturities so that (a) liabilities are
paid with principal arriving on time, (b) reinvestment risk is spread
across maturities rather than bet on one date, (c) no single rate move
reprices the whole sleeve.

### 1.2 Design parameters

```
INPUTS:
  L  = liability schedule (from [[fin-cash-flow-framework]] sinking
       funds + EF Tier 3 + [[fin-retirement-planning]] cash wedge)
       <OPERATOR_INPUT: list of (date, amount) pairs>
  W  = ladder width = longest maturity needed by L
  N  = number of rungs (default: one rung per year of width)
  C  = credit quality policy (section 6)
CONSTRUCTION:
  For each rung year y in [1..N]:
    target_amount(y) = sum of liabilities due in year y
                       + reinvestment ballast if funding lump today
  If funding a level-spend goal instead of dated liabilities:
    equal-weight rungs: amount(y) = Total / N
```

### 1.3 Reinvestment rule

Each maturing rung is EITHER consumed by its liability OR rolled to the
new long end of the ladder (maintaining N rungs). Decision made at
maturity, never in advance; roll amount = principal + accrued coupon.
This is the mechanical implementation of "spread reinvestment risk":
in a rising-rate world each roll captures new higher yields; in a
falling-rate world the long rungs already locked today's yields.

### 1.4 Worked sizing example (synthetic)

```
Goal: bridge $40,000/yr of spending for years 1-5 (retirement gap).
Ladder: T-bills yr1 $40k; 2y note yr2; 3y; 4y; 5y note yr5.
At current curve shape (DGS10 4.69%, front end similar or higher),
blended locked yield ~4.5% -> coupon offsets part of each year's
draw; recompute exact coupons at execution from live quotes.
```

## 2. Duration matching to liabilities

### 2.1 When matching beats laddering

A ladder staggers maturity; duration MATCHING immunizes present value
against parallel rate moves for a known future obligation. Use matching
when the liability has ONE date (e.g., tuition in 7 years); laddering
when it is a stream.

### 2.2 Procedure

```
For liability PV_L due in T years:
  choose instrument/portfolio whose modified duration D satisfies:
    D_portfolio ~= horizon T (Macaulay convention for immunization)
  Immunized value change check:
    dPV = -D x P x dy + 0.5 x Conv x P x dy^2
  Rebalance when |D - T| > tolerance (default 0.5yr).
Funding-ratio form (stream version):
  D_assets = sum(w_i x D_i) must equal
  D_liabilities = sum(PV_j x T_j) / sum(PV_j)
```

### 2.3 Rate-risk quantification using factor store data

```
Duration budget table per $100k sleeve (parallel shift):
  +100bp: 2y note -1.9% | 5y -4.3% | 10y -8.5%* | 30y -14.5%
  (*duration approximations; compute exactly from holdings)
Interest-rate risk budget:
  IB_max = max tolerable 12-month mark-to-market drawdown on the FI
           sleeve <OPERATOR_INPUT, e.g., 5%>
  => weighted avg duration cap = IB_max / 1.00 (per 100bp)
Example: 5% drawdown tolerance caps portfolio duration at ~5.0.
Current-context caveat: with yields at p97+ percentiles, the ASYMMETRY
favors duration (downside repricing room smaller than upside);
a duration ABOVE naive budget may be justified -- record any override
as an explicit decision, do not drift into it.
```

## 3. TIPS vs nominal decision tree

```
Q1. Is the liability REAL (indexed to inflation: lifestyle spending,
    healthcare) or NOMINAL (fixed debt payoff, fixed annuity purchase)?
    REAL  -> go Q2
    NOMINAL -> nominals are CORRECT; TIPS mismatch adds risk, skip.
Q2. Is real yield acceptable?
    Read DFII10 from factor store (currently 2.35%, p98.7).
    Real >= operator's hurdle <OPERATOR_INPUT, default 1.5%> -> YES.
    NO  -> prefer short nominals / T-bills until real yields improve;
           record decision date and trigger to revisit (DFII10 level).
Q3. Tax account placement available?
    Taxable-only -> WARNING: TIPS phantom income (annual inflation
    accretion taxed as received, cash paid only at maturity/coupon)
    creates negative carry for high brackets. Mitigate: hold TIPS in
    traditional/Roth ([[fin-tax-aware-investing]] sec 1); in taxable
    prefer T-bills (state-exempt, no phantom income) unless bracket
    low <OPERATOR_INPUT>.
Q4. Horizon vs liquidity?
    <= 2y -> T-bills dominate operationally (deepest market, simple).
    2-10y -> TIPS ladder rungs (TreasuryDirect buys at auction).
    > 10y -> long TIPS or accept nominal DGS30 5.23% if operator
             judges long-run inflation < breakeven (~2.3-2.4%).
DECISION OUTPUT: instrument, wrapper, maturity, amount, revisit trigger.
```

Breakeven logic: nominal vs TIPS is a bet that realized CPI averages
below/above the breakeven (DGS10 - DFII10 ~= 2.34% now). Framework
stance: match INSTRUMENT to LIABILITY nature first (real->TIPS),
speculate on inflation only deliberately and separately.

## 4. Municipal bond evaluation

### 4.1 Taxable-equivalent yield

```
TEY_muni = Y_muni / (1 - marginal_rate_fed)
TEY_tsy  = Y_treasury / (1 - marginal_rate_fed_state_combined_if_state_taxable)
Compare TEYs net of state treatment:
  In-state muni: exempt fed AND state -> strongest for high-state-tax
  Treasury interest: state-exempt, federally taxable
Rule: munis win when TEY_muni > treasury yield after credit adjustment.
Worked frame at assumed 32% federal <OPERATOR_INPUT>:
  muni 3.60% -> TEY 5.29%; Treasury at DGS10-like 4.69% (state-exempt
  raises its effective edge in high-tax states). Muni wins on pure
  yield IF single-A or better AND in-state.
```

### 4.2 Credit and structure screens

```
Ratings floor: investment grade only (>= BBB-); ladder design keeps
average >= A. No high-yield inside the LIABILITY-matching sleeve.
Structure preferences: general obligation or essential-service revenue;
avoid callables near par with 10d/1mo extraordinary calls; avoid
deep-discount de minimis tax traps (>0.25 de minimis rule for market-
discount munis bought cheap).
Insurance wrap: unnecessary at IG ratings; treat wrapped paper as the
WRAPPER's credit.
Liquidity: small-issue munis trade wide; size positions >= $25k blocks
and expect retail spreads 20-50bp. ETF route (section 5) solves this.
```

### 4.3 Bank-qualification and AMT notes

Private-activity munis CAN hit AMT (<OPERATOR_INPUT: relevant only if
AMT-exposed per [[fin-tax-aware-investing]] sec 5.2) -- screen holdings
if AMT applies.

## 5. TreasuryDirect vs ETF implementation

### 5.1 Decision matrix

| Dimension | Direct (TreasuryDirect/broker bids) | ETF/Fund |
|---|---|---|
| Maturity certainty | Exact rung dates | Rolling book, no dates |
| State tax | Interest state-exempt | Passes through (usually) |
| Phantom income (TIPS funds) | Manageable direct | Fund accrues+taxable too |
| Liquidity intraday | Auction/secondary only | Instant |
| Spread/cost | None at auction; secondary bid/ask | ER 3-15bp + NAV premium/discount |
| Ladder precision | Perfect | Approximate |
| Estate/account logistics | TreasuryDirect clunky (transfer hoops) | Brokerage-native |
| Small balances | Minimum $100 (TD) / $1k units broker | Any size |

### 5.2 Standing policy

```
P1 Liability-dated rungs (EF Tier 3, sinking fund horizons,
   retirement bridge): DIRECT instruments -- bills/notes/TIPS at
   auction. Dates matter more than convenience.
P2 Duration-expression or tactical exposure: ETFs acceptable.
P3 All direct Treasury purchases at auction where possible
   (non-competitive bids guarantee average auction yield).
P4 Broker-held over TreasuryDirect when the account will be traded/
   inherited/bequeathed; TD acceptable for buy-and-hold-to-maturity
   simplicity. <OPERATOR_INPUT: choose one primary venue>
P5 I-bonds: savings-rate niche ($10k/yr/person cap); evaluate only
   vs T-bill+lockup cost; fixed-rate component vs DFII10 comparison
   at purchase time.
```

## 6. Credit quality ladder design

### 6.1 Two-axis quality framework

The FI sleeve separates SAFETY capital from RETURN-seeking credit:

```
Tier S (safety, liability-backed):
  Treasuries, TIPS, agency debentures, FDIC CDs within limits, IG munis
  in-state. Purpose: pay liabilities regardless of cycle. Default-free
  or near; NO reach for yield permitted here.
Tier R (credit carry, optional satellite):
  IG corporates (BBB+/A-), securitized (agency MBS), preferreds in
  moderation. Purpose: extra 50-150bp over Treasuries. Sized so that a
  2008-grade credit spread blowout (IG spreads +350bp, HY +1500bp)
  costs <= <OPERATOR_INPUT, default 2%> of total FI sleeve.
High-yield: belongs to the RISK asset budget, NOT to fixed income.
  If held at all, count it against equity risk allocation in the
  doctrine's band math.
```

### 6.2 Quality ladder construction

```
For a sleeve of size X with liability coverage requirement C:
  Step 1: fully fund ALL dated liabilities with Tier S instruments
          (sections 1, 2). This amount is untouchable.
  Step 2: surplus above C may enter Tier R up to the drawdown budget.
  Step 3: within Tier R, diversify: >= 15 issuers or an IG corporate
          ETF; sector caps 20%; single-issuer cap 5% of sleeve.
Review: credit tier boundaries re-tested annually and whenever the
factor store shows spreads regime shifts (track OAS series if added
to the store).
```

## 7. Integration points

### 7.1 With deployment bands ([[fin-cash-flow-framework]] sec 6)

Band C (hold-cash) accumulation lands HERE: the T-bill sleeve is the
FI ladder's front end. DeployableFCF parked during band C earns the
front-end rate; when bands reopen, rungs mature into equity purchases
on schedule without forced sales.

### 7.2 With calibration engine

Exports monthly: `fi_sleeve_duration`, `fi_yield_locked_blended`,
`fi_maturity_cashflow_schedule` (the L input of section 1.2), plus
current DGS10/DGS30/DFII10 pulls. The engine uses these for
opportunity-cost pricing (deferral value at 4.69% context, see
[[fin-tax-aware-investing]] sec 6.3) and for band multiplier
calibration -- NOT for equity timing gates (doctrine research cited
above).

### 7.3 With retirement planning

The withdrawal cash wedge fin-retirement-planning is implemented as
this document's ladder sections 1-2; sequence-of-returns defense equals
rungs covering 1-3 years of withdrawals.

## 8. Failure modes catalog

| Failure | Consequence | Guard |
|---|---|---|
| Hardcoded yield assumptions | Stale ladder economics | Factor store pull each session |
| Callable bonds silently retired early | Reinvestment at worse rates | Screen structures (4.2) |
| TIPS in taxable, high bracket | Phantom income drag | Placement rule sec 3 Q3 |
| HY counted as fixed income | Risk double-count vs equity | Sec 6.1 routing |
| Ladder built then ignored at maturities | Drift to accidental duration | Roll-or-consume rule 1.3 |
| Duration override without record | Silent risk growth | Explicit-decision rule 2.3 |
| TreasuryDirect orphan accounts | Estate/admin friction | Venue policy 5.2 P4 |

## Appendix A. Factor store query cookbook

All rate inputs pulled live; never transcribe stale values into new
computations. Primary tool: `python tools/factor-store.py`.

```
# Current 10y nominal (context: 4.69% at p99-all / p97.2-1y, Jul-Aug 2026)
python tools/factor-store.py --query-bars DGS10 --days 30
python tools/factor-store.py --stats

# Long end (context: DGS30 5.23%, ~p99.8)
python tools/factor-store.py --query-bars DGS30 --days 30

# Real yield for TIPS decisions and discounting
python tools/factor-store.py --query-bars DFII10 --days 30

# As-of historical pulls for backtests / decision reviews
python tools/factor-store.py --query-bars DGS10 --as-of <YYYY-MM-DD>
```

Derived quantities used by this framework:

```
breakeven_10y = DGS10 - DFII10          # ~2.34% current context
real_yield_10y = DFII10                 # 2.35% context
duration_drawdown(d, dy) ~= -d * dy    # per-unit price change est.
deferral_value(1yr) = tax_deferred * (1 + short_rate)  # sec 7 note
```

Doctrine caution (repeat of sec 0): these series price BONDS; they are
not equity timing signals (research-dgs10-band-2026-07-18).

## Appendix B. CD and savings-rate comparison module

Bank products compete with Treasuries for the front rungs:

```
Compare on after-tax, state-adjusted yield:
  TEY_cd = Y_cd * (1 - combined_rate)               # fully taxable
  TEY_treasury = Y_tsy * (1 - fed_rate)             # state-exempt
Break-even: Y_cd >= Y_tsy * (1 - fed_rate) / (1 - combined_rate)
to beat the Treasury.
At high state rates the Treasury wins by construction unless the CD
pays a large spread. FDIC limit ($250k/bank/owner category) vs full-
faith-and-credit Treasuries: no cap. Callable/brokered CDs with
surprisingly high yields carry early-redemption risk at the ISSUER's
option -- read before buying; usually reject.
HYSA: convenience tier only (EF Tier 2); never the ladder body.
I-bonds: annual cap $10k/person, 12-month lockout + 3mo interest
forfeit years 1-5; compare fixed component vs DFII10 at purchase.
```

## Appendix C. Agency / MBS evaluation notes (Tier R detail)

```
Agency debentures: credit near-Treasury, modest spread pickup; fine
at the Tier S margin.
Agency MBS: negative convexity -- extends when rates rise (low coupons
persist) and prepays accelerate when rates fall (reinvest lower).
Duration is a MOVING TARGET:
  - budget with OAS-based effective duration, not static maturity
  - rebalance duration contribution monthly when held directly;
    ETF wrappers handle this mechanically.
Spread risk: MBS spreads widen sharply in risk-off; treat as Tier R.
Size rule: total negative-convexity exposure <= 25% of FI sleeve
<OPERATOR_INPUT override permitted with recorded rationale>.
```

## Appendix D. Ladder maintenance calendar

```
MONTHLY: factor store pull logged (DGS10/DGS30/DFII10); duration vs
         budget check (sec 2.3); roll-or-consume queue review.
QUARTERLY: sinking fund register reconciliation feeds rung targets;
         EF Tier 3 refill purchases executed if triggered.
SEMIANNUAL: muni holdings credit re-screen (rating actions, call
         schedules); CD/HYSA rate sweep (Appendix B).
ANNUAL: full ladder rebuild projection against updated liability map;
        quality tier boundary test (sec 6.1); venue policy P4 check;
        I-bond purchase decision window evaluated.
EVENT-DRIVEN: large liability added/removed -> immediate re-ladder;
        band-state change to C -> confirm T-bill sleeve capacity for
        expected DeployableFCF accumulation ([[fin-cash-flow-framework]]
        sec 6.2).
```

## Appendix E. Curve-shape playbook

The ladder's roll decisions depend on where the front end sits relative
to the long end at each maturity date. Standing interpretations:

```
E1 STEEP curve (long >> short, e.g., 2s10s spread wide):
   Ladder construction is FAVORED -- rolling maturing rungs out the
   long end captures higher yields; barbell alternative considered.
   Current context: with DGS30 5.23% vs short rates near it, curve is
   relatively flat-to-inverted-normalizing; re-read live before use.
E2 INVERTED curve (short > long):
   Extending duration locks LOWER yields than cash pays -> hold rungs
   SHORT; roll within bills until inversion resolves. The ladder
   naturally "waits in cash" -- this is a feature, not drift.
E3 FLAT curve:
   Neutral; default equal-weight ladder stands.
E4 BULL steepener underway (front falling fast):
   Maturing bill proceeds reinvested per schedule anyway -- never
   chase yield by extending early; schedule discipline outranks
   rate views (same anti-timing stance as the doctrine research).
```

Each quarterly review records current curve shape + playbook state.

## Appendix F. Liability mapping worked example (synthetic)

```
Liability map from CF framework sinking funds:
  SF-02 property tax .......... $6,000 due Nov 1  -> T-bill maturing Oct
  SF-05 vehicle replacement ... $22k net, ~36mo   -> 3y note rung
  EF Tier 3 ................... $12k rolling      -> 4-8wk bill stagger
  Bridge years 1-5 (retire) ... $40k/yr          -> notes years 1-5
Construction:
  Total dated need year 1 = 6000 + 12000(rolling) + 40000 = $58k
  Year 2 = 40000 (+property tax rolls) etc.
  Funding lump today at blended ~4.4% assumed yield:
    PV of stream ~= sum(CF_t / (1+y)^t); compute exactly at execution.
  Rungs purchased at auction (policy P3), broker-held (P4).
Roll decision at each maturity: consume if liability due that month,
else extend to new N-year point and log the new yield locked.
```

## Appendix F. Bond math reference card

Formulas used throughout, stated once for consistency:

```
F1 Price-yield (annual coupon, N years):
   P = C * [1 - (1+y)^-N]/y + F*(1+y)^-N
F2 Macaulay duration (approximation for small coupons):
   D ~= (1+y)/y * [1 - (1+y)^-N] - ... use tooling for exact;
   rule: zero-coupon D = maturity; low-coupon D slightly under it.
F3 Modified duration: D_mod = D_mac / (1 + y/n)
F4 Convexity adjustment: dP/P ~= -D_mod*dy + 0.5*C*dy^2
F5 Current yield vs YTM: CY = C/P understates YTM when P < F.
F6 After-tax yield comparison (fed rate t_f, state t_s):
   Treasury:  Y * (1 - t_f)
   Muni (in-state):  Y * 1.0            [both exemptions]
   Muni (out-of-state): Y * (1 - t_f)
   Corporate/CD: Y * (1 - t_f - t_s*(1-t_f)) approx
F7 Breakeven inflation: BEI_y = Y_nominal(y) - Y_real(y) at same tenor.
```

## Appendix G. Historical percentile discipline

The factor store reports percentiles (DGS10 p99-all / p97.2-1y etc.).
Standing rules for their use:

```
G1 Percentiles inform EXPECTATIONS (how unusual today's yields are),
   never mechanical triggers on their own.
G2 All-history percentiles overstate "expensiveness" of yield because
   the sample is dominated by the pre-1994 high-rate era and the
   2010s ZIRP tail; trailing-decade percentiles are the secondary
   lens. Report BOTH when recording a decision.
G3 For ladder decisions what matters is ABSOLUTE locked real yield
   vs liability needs -- p99 nominal context is commentary.
G4 Any use of yield levels to gate EQUITY actions is out of scope
   here and contradicted by [[research-dgs10-band-2026-07-18]]; if a
   proposal appears, route it to that research before adoption.
```

## Appendix H. Real-rate regime table (decision aid)

```
DFII10 zone      | TIPS posture            | Nominal posture | Cash
< -0.5% (real    | avoid long TIPS         | prefer nominals | neutral
  negative)      | (expensive insurance)   |                 |
-0.5% to +1.0%   | standard real matching  | standard        | neutral
+1.0% to +2.0%   | favorable               | fine            | ok
> +2.0% (rare;   | strongly favorable --   | lock long       | cheap
  current 2.35%) | max real matching       | nominals here   |
Context: current DFII10 2.35% sits in the rare top row -- historically
one of the better environments to fund REAL liabilities with TIPS and
to lock long nominal DGS30 5.23%. This is regime context for ladder
construction, NOT an equity signal (doctrine research, sec 0).
```

## 9. Cross-references

- [[edu-fixed-income]]: educational foundations (convexity, curve
  mechanics) backing the formulas used here.
- research-dgs10-band-2026-07-18: why the 10Y level is not used
  as an equity gate; valuation-conditional replacement evidence.
- [[fin-cash-flow-framework]]: liability schedule source; band-C cash
  destination.
- [[fin-tax-aware-investing]]: TEY math details, AMT/private-activity
  screening, phantom income handling.
- fin-retirement-planning: cash wedge consumption sequencing.
