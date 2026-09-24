---
name: fin-risk-transfer
aliases: [fin-risk-transfer]
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
  - topic/insurance
  - topic/risk-management
aliases:
  - risk transfer framework
related:
  - "[[fin-cash-flow-framework]]"
  - "fin-retirement-planning"
  - "[[fin-tax-aware-investing]]"

---

# Risk Transfer Framework

Method document for insurance and risk-transfer decisions. Structure
only; all `<OPERATOR_INPUT>` slots filled at use time. ASCII only.

## 0. Scope and philosophy

Risk transfer covers the low-frequency / high-severity quadrant only:

```
            HIGH severity
                 |
   TRANSFER      |      TRANSFER or
   (insurance)   |      AVOID/REDUCE
                 |
 LOW freq -------+------- HIGH freq
                 |
   RETAIN        |      REDUCE/PREVENT
   (deductibles, |      (maintenance,
    self-insure) |       habits)
                 |
            LOW severity
```

Principles:

1. Insure ruins, not inconveniences. Never insure the small stuff
   (extended warranties, trip insurance for cheap flights).
2. Highest-deductible sustainable structure + premium savings routed to
   dedicated reserves beats low deductibles with fat premiums, IF the
   reserve is actually funded ([[fin-cash-flow-framework]] sinking funds).
3. Coverage adequacy is reviewed on LIFE EVENTS, not calendar drift:
   marriage, children, home purchase, income jumps, business formation.
4. Every policy here interacts with the E-lines of the cash flow model;
   premiums are essential spend (E4), benefits adjust emergency fund
   multiplier M.

## 1. Insurance coverage adequacy methodology

### 1.1 Exposure inventory template

```
| # | Exposure | Severity if uninsured | Frequency est. | Current transfer | Gap? |
|---|----------|----------------------|----------------|------------------|------|
| 1 | Death of earner <OI> | catastrophic | low | life policy <OI> | <OI> |
| 2 | Long-term disability <OI> | catastrophic | moderate (~1-in-4 career odds of 90d+ disability commonly cited) | LTD <OI> | <OI> |
| 3 | Lawsuit beyond auto/home limits | severe | very low | umbrella <OI> | <OI> |
| 4 | Total home loss | severe | low | HO dwelling <OI> | <OI> |
| 5 | Auto liability/at-fault total | moderate-severe | low-moderate | auto limits <OI> | <OI> |
| 6 | Major medical event | catastrophic | low | health plan OOP max <OI> | <OI> |
| 7 | LTC need 2+yrs | severe | moderate at older ages | <OI: none/LTC/Hybrid> | <OI> |
| 8 | Identity/cyber/fraud | low-moderate | moderate | retain + hygiene | usually N/A |
| 9 | Pet/vision/dental/warranties | low | high | self-insure | N/A by design |
```

### 1.2 Adequacy tests per line

```
T1 RUIN TEST: could this exposure alone cut net worth > 25% or force
   liquidation of core assets at a bad time? If YES -> must be
   transferred or explicitly accepted in writing.
T2 LIMITS TEST: current limit >= worst plausible single-event loss?
   (home: full rebuild cost incl. code upgrade/ordinance coverage;
    auto liability: assets-at-risk based; health: OOP max is the
    true exposure number.)
T3 DEDUCTIBLE TEST: can cash flow absorb deductible from checking +
   Tier 1 EF without touching investments? If no -> deductible too
   high OR reserves underfunded.
T4 EXCLUSION AUDIT: read exclusions annually (flood/quake/sewer
   backup/business use are classic silent gaps). Endorse where the
   ruin test fires.
T5 PREMIUM EFFICIENCY: shop P&C every 2-3 years; loyalty pricing
   decays. Log quotes; switch only on identical-coverage comparison.
```

## 2. Life insurance needs calculation

### 2.1 Needs-based method (primary)

```
Capital needed at death = D1 + D2 + D3 - A

D1 Income replacement:
   years_to_support x annual support need (after-tax basis)
   Use present value at real discount rate r_real
   (factor store DFII10 = 2.35% context as base; sensitivity +-1%).
D2 Lump-sum obligations: mortgage payoff choice, education fund,
   final expenses, debt payoff, emergency buffer top-up for survivor.
D3 Liquidity for estate/taxes (large IRAs/401ks to non-spouse heirs
   create compressed tax events -- see [[fin-retirement-planning]]).

A  Available resources:
   survivor's own income, SS survivor benefits (model via claiming
   framework logic), existing coverage, liquid assets earmarked.

Coverage gap = Capital needed - existing resources
```

### 2.2 Worked skeleton (synthetic)

```
Survivor needs $60k/yr after-tax for 18 yrs -> PV at 2.35% real ~ $880k
Education lump sum $200k. Mortgage NOT paid off (survivor keeps house
affordably) -> $0. Final/debt $50k. Emergency top-up $25k.
Needs ~ $1,155k.
Resources: survivor salary covers own spending fully; SS survivors'
benefit ~$28k/yr until kids out -> PV ~ $380k; existing group life
1x salary $120k; taxable assets partly earmarked $150k.
Resources ~ $650k. GAP ~ $505k term face amount target.
```

### 2.3 Product selection decision tree

```
Q1 Is the need TEMPORARY (ends when dependents grow/mortgage shrinks)?
   YES (typical working years) -> LEVEL TERM, length = years_to_support.
   NO (permanent estate liquidity, special-needs dependent, business
   buy-sell) -> permanent product justified; compare whole life vs
   guaranteed universal life vs GUL+separate investing honestly.
Q2 Group vs individual: group life is portable rarely -> treat as
   SUPPLEMENT only; underwrite individually while healthy.
Q3 Laddering: multiple term policies (10y large + 20y smaller)
   match declining needs and cut total premium ~20-30% vs one long
   level block.
Q4 Rider audit: avoid gimmick riders; consider waiver-of-premium and
   child terms only after cost check.
Beneficiary hygiene: primary AND contingent named (never "estate" --
   forces probate and creditor exposure); review after every life event.
Trust ownership where minors/disabled beneficiaries exist.
```

### 2.4 Wind-down criteria

Life insurance demand declines with: independent children, paid home,
portfolio crossing the capital-needed threshold, retirement onset
(replacement need falls). Review at each guardrail; lapse/convert
decisions recorded like any portfolio decision.

## 3. Disability evaluation criteria

### 3.1 Why it outranks life insurance statistically

Probability of a long disability during working years exceeds death
probability for most ages, yet coverage is usually weaker. Priority:
disability FIRST, then life, when building the stack from zero.

### 3.2 Policy evaluation checklist (the definitions ARE the policy)

```
C1 Definition of disability:
   OWN-OCCUPATION (any occupation modifier noted) is the standard to
   demand for professional/specialist earners. "Any occupation" or
   "gainful occupation" policies pay far less often -- price their
   weakness explicitly before accepting.
C2 Benefit period: to the 65th birthday minimum; 2y/5y periods leave tail risk.
C3 Elimination period: 90d typical; must fit EF sizing (CF framework
   sec 4.2 gives -0.5 multiplier adjustment when coverage replaces
   >60% income -- conversely long elimination periods require bigger EF).
C3 Replacement ratio: target 60% of gross (taxable analysis below);
   cannot insure >100% (moral hazard caps); stack employer LTD +
   individual DI to reach ratio without exceeding insurable income.
C4 Residual/partial disability rider: ESSENTIAL for variable-income
   and professionals (allows partial payment while working reduced).
C5 Non-cancelable + guaranteed renewable: both, no exceptions.
C6 COLA rider on benefits (post-disability inflation); evaluate
   future-increase option (FIO) while young/healthy.
C7 Offset language: list what offsets (SSDI, workers comp, other
   coverage) so expectations match reality.
```

### 3.2 Taxability rule (load-bearing)

```
Benefits are TAX-FREE if the operator paid premiums with AFTER-TAX
dollars (including via payroll deduction post-tax).
Benefits are TAXABLE as ordinary income if EMPLOYER paid (or pre-tax
via cafeteria plan).
=> Employer-paid free LTD is taxed at payout; compute NET replacement:
   60% gross benefit taxed at marginal rate may net ~42-45% -- the gap
   justifies an individual supplement sized to close it.
<OPERATOR_INPUT: how current premiums are paid>
```

### 3.3 Underwriting and timing discipline

Buy individual DI EARLY (young + healthy locks occupation class and
rates); medical records requests are normal; disclose accurately.
Re-evaluate limits after income jumps using FIO rather than new
policies where available. Specialty limits (e.g., physicians) preserved
by own-occ definitions matter enormously -- verify contract language,
not marketing summaries.

## 4. Umbrella policy sizing based on net worth

### 4.1 Sizing formula

```
Umbrella_limit >= NetWorth_x + FutureIncomeAtRisk_y - underlying_limits_z

x = current net worth (lawsuits target accumulated assets)
    <OPERATOR_INPUT from balance sheet, updated annually>
y = capitalized future earnings exposure for high-income operators:
    ~ years_to_retirement x annual gross x judgment-exposure factor
    (use 0.5 conservative default; higher for public-facing/
    landlord/board roles)
z = underlying auto/home bodily-injury + property limits (umbrella
    sits EXCESS over required minimums)

Standard bands: $1M floor whenever NW > ~$250k or any teen drivers /
rentals / dogs of litigious breeds / trampoline pool etc.; step to
$2M-$5M as NW crosses $1M-$3M. Marginal cost per extra $1M band is
small ($50-150/yr typically) -- under-buying saves little.
```

### 4.2 Requirement: underlying limits schedule

```
Umbrellas REQUIRE minimums on underlying policies (commonly
$250k/$500k BI + $100k PD auto; $300k homeowner liability).
Schedule audit annually BEFORE renewal; gaps void excess coverage
above deficient underlying limits.
```

### 4.3 What umbrella does NOT cover

Professional malpractice (needs E&O), business liabilities beyond
scheduled LLCs, intentional acts, contractual assumptions. Business
exposure -> separate structure review; rental properties -> require
LLC ownership + proper policy classification (landlord policy),
umbrella endorsement listing the entity.

## 5. Long-term care planning considerations

### 5.1 Exposure framing

```
Rough incidence: ~half of those reaching 65 will need some paid care;
most spells short; tail risk is multi-year nursing care at
$100k+/yr (regional <OPERATOR_INPUT>). The ruin scenario is the LONG
TAIL: 3-5+ year cognitive-care durations.
Self-insure math alternative: earmarked portfolio slice covering
5yr tail cost, invested conservatively. Compare expected cost vs
hybrid premium outlay; decide on BOTH tails (premiums wasted if never
needed vs portfolio depleted if care runs long).
```

### 5.2 Instrument landscape and decision tree

```
Traditional standalone LTC: use-it-or-lose-it, premiums have history
of steep increases; market has largely exited. Only consider strong-
rate-stability carriers with partnership-program eligibility.
Hybrid life+LTC (asset-based): return-of-premium death benefit;
premium fixed; LTC acceleration riders. Currently the practical
default IF transferring. Compare against SELF-INSURE slice honestly.
Medicaid-planning path: spend-down strategy only for genuinely modest
estates; involves lookback rules (5yr) and irrevocable trust structures
-- legal counsel territory; do NOT DIY.
Decision order:
  Q1 Portfolio size vs tail cost? If NW comfortably > 8-10x annual
     care cost -> self-insure viable; still stress-test dual-spouse
     concurrent scenarios.
  Q2 Family longevity/cognitive history elevated? -> tilts toward
     hybrid purchase earlier (cheaper younger, lock health).
  Q3 Cash flow supports hybrid premium without crowding retirement
     contributions? -> else defer, revisit at milestones.
Integration: LTC decision adjusts EF multiplier M slightly downward
only when coverage is IN FORCE; planned-but-unpurchased coverage gets
NO adjustment (aspiration is not coverage). See CF sec 4.2 and
[[fin-retirement-planning]] healthcare lines.
Timing note: hybrids funded from taxable assets in low-income years
(bridge window) can be efficient; coordinate with conversion budgets
([[fin-tax-aware-investing]] sec 6).
```

## 6. Integration points

### 6.1 With cash flow framework

Premium totals land in E4 (essential). Disability/LTC coverage in
force adjusts EF multiplier M (sec 4.2 table). Deductible levels set
the sinking fund accrual lines L1/L3/L4 floors.

### 6.2 With retirement framework

Annuity/LTC floors change withdrawal guardrail aggressiveness;
life wind-down at retirement; Medicare/Medigap decisions live in
fin-retirement-planning sec 5 but premium lines originate here.

### 6.3 With calibration engine

Exports annually: `coverage_stack {line, limit, deductible, premium,
beneficiary_review_date}`, `net_worth_for_umbrella`, `disability_net_
replacement_ratio`. Engine flags when net-worth moves cross umbrella
band thresholds (sec 4.1) or when portfolio growth obsoletes life
coverage (sec 2.4).

## 7. Failure modes catalog

| Failure | Consequence | Guard |
|---|---|---|
| Relying on employer life/DI only | Coverage lost at job change | Individual base while healthy |
| Any-occ disability bought unknowingly | Claim denied despite impairment | C1 definition audit |
| Umbrella without underlying-limit audit | Void above deficiency | Annual schedule 4.2 |
| Beneficiary listed as estate | Probate + creditors | Hygiene rule 2.3 |
| Extended warranties purchased | Premium waste (low severity) | Quadrant map sec 0 |
| LTC aspiration counted as coverage | EF undersized | Timing note 5.2 |
| Flood/quake exclusion unexamined | Uninsured total loss | T4 exclusion audit |
| Post-tax vs pre-tax premium confusion | Wrong tax-free expectation | Rule 3.2 |

## Appendix A. Health insurance deep detail (pre-Medicare years)

### A.1 HDHP + HSA stack evaluation

```
HDHP wins when: healthy baseline utilization, cash available to fund
HSA, and premiums savings > expected OOP increase.
HSA triple advantage: deductible contribution, tax-free growth,
tax-free qualified withdrawals -- the best wrapper in the code
(see [[fin-tax-aware-investing]] location ranking; HSA holds Rank-1
assets ideally).
Rules to respect: HSA requires HDHP-qualified coverage ALL month;
Medicare enrollment lookback (6 months, [[fin-retirement-planning]]
5.2); after 65 HSA works as a regular IRA for medical costs only.
Invest-vs-spend decision: pay current medical from cash flow when
possible; bank receipts (reimbursement can be claimed ANY later year)
-- the receipt bank is a legitimate tax-free conversion tool at
retirement. Keep receipts with the ledger (outside wiki).
```

### A.2 COBRA vs ACA worked comparison frame

```
For each option compute: annual premium + expected OOP + subsidy lost.
COBRA: full group premium +2%; network continuity; no subsidy.
ACA: benchmark silver minus PTC (MAGI-dependent); plan network may
change; income management (retirement sec 5.1) directly lowers cost.
Decision rule: choose lower TOTAL cost subject to network adequacy
for known conditions <OPERATOR_INPUT: providers that must remain>.
Special cases: late-year job loss -> COBRA retroactive election lets
you wait and see (60-day window) before committing; pregnancy/known
upcoming care -> verify coverage continuity FIRST, optimize second.
```

## Appendix B. Property & casualty structure review

```
B1 Dwelling: insured at FULL REBUILD cost, not market value; include
   ordinance-and-law endorsement (code upgrades), inflation guard;
   rebuild estimate refreshed every 2 years with local construction
   inflation (recent years argue 6-8%/yr, above CPI).
B2 Contents: replacement-cost endorsement (not ACV); scheduled
   floaters for jewelry/instruments/art above sublimits <OPERATOR_INPUT>.
B3 Loss-of-use: 12+ months; verify, this is what makes a total loss
   survivable financially.
B4 Auto: liability limits sized by umbrella schedule 4.2; collision/
   comprehensive dropped when vehicle value < ~10x the premium delta
   (self-insure quadrant); gap insurance ONLY on new financed cars.
B5 Water/flood split: sewer-backup endorsement cheap and commonly
   needed; flood = NFIP/private separate policy whenever any ruin-test
   exposure exists (even outside mapped zones -- most flood claims
   occur outside them).
B6 Earthquake/wind deductibles in exposed regions are PERCENTAGE
   deductibles (10-20% of dwelling) -- size reserves accordingly or
   transfer via separate quake policy.
B7 Home business / short-term-rental use voids standard HO policies:
   disclose and endorse or restructure.
```

## Appendix C. Life insurance underwriting preparation

```
C1 Medical prep: schedule exam morning, hydrate, no alcohol 48h,
   fast if required; untreated minor items (BP, lipids) materially
   move offers -- address before applying when time allows.
C2 Table-shopping: impaired risk goes to BROKER quoting across
   carriers; offer tables vary wildly for identical profiles.
C3 Timing: lock insurability EARLY (see DI priority rule 3.1 note);
   re-entry after diagnoses is expensive or impossible -- coverage is
   bought with health, not money.
C4 Ownership structures: individual vs ILIT (estate tax exposure
   cases), business buy-sell funding with cross-purchase/entity
   redemption -- legal counsel signs off; framework records intent.
C5 Conversion privilege: term policies with strong conversion riders
   preserve optionality if health degrades mid-term -- prefer carriers
   with longer/no conversion windows at equal price.
```

## Appendix D. Claim process playbooks

Insurance bought is only half the structure; the claim side needs a
standing plan:

```
D1 Property claim protocol:
   - Home video/photo inventory maintained EXTERNALLY (cloud), updated
     annually; policy + endorsement copies stored with it.
   - On loss: mitigate further damage (duty to mitigate), document
     BEFORE cleanup, file promptly, keep a claim-expense log
     (loss-of-use is reimbursable -- many claimants forget).
   - Adjuster negotiation: obtain independent contractor estimates;
     public adjuster considered only for large losses (fee 5-10%).
D2 Disability claim protocol:
   - File EARLY (elimination clock starts at disability onset, not at
     paperwork completion); attending-physician statements are the
     hinge -- brief the doctor on the POLICY'S definition, not just
     the diagnosis.
   - Own-occ claims must document occupation duties specifically.
   - Keep working-income records clean; residual claims pro-rate on
     documented loss of income.
D3 Life claim kit (survivor-facing, prepared now):
   one-page index: carrier, policy numbers, agent contacts,
   beneficiary designations, where certificates live. Stored with
   estate documents, reviewed annually.
D4 Liability/umbrella claim:
   - Notify carrier of ANY incident potentially exceeding underlying
     limits IMMEDIATELY (late notice can void excess coverage).
   - No admissions at scene; tender defense to carrier early.
```

## Appendix E. Coverage review triggers (event-driven audit list)

```
[ ] Marriage / divorce / death in household -> beneficiaries, limits
[ ] Child born/adopted -> life gap recompute, DI ratio check
[ ] Home purchase/sale/remodel -> dwelling coverage, umbrella NW input
[ ] Income jump > 20% -> DI FIO exercise, life replacement recompute
[ ] Business formed / rental acquired -> entity + policy structure
[ ] Teen driver added -> auto limits, umbrella band check
[ ] Net worth crosses $1M / $3M / $5M -> umbrella step-ups (sec 4.1)
[ ] Health diagnosis in household -> underwriting windows closing;
    convert/lock options reviewed before they lapse
[ ] Employer change -> group coverage portability deadlines (usually
    31 days for life conversion, immediate for new-plan effective)
[ ] Annual January sweep regardless of events: full inventory table
    sec 1.1 refreshed; premium efficiency test T5 run on P&C lines.
```

## Appendix F. Coverage adequacy scoring worksheet

Annual one-page scorecard; any FAIL forces an action item:

```
| Line            | Ruin T1 | Limits T2 | Deduct T3 | Exclusions T4 | Score |
|-----------------|---------|-----------|-----------|---------------|-------|
| Life (earners)  |   P/F   |    P/F    |   n/a     |     n/a       |       |
| Disability      |   P/F   |    P/F    |    P/F    |      P/F      |       |
| Umbrella        |   P/F   |    P/F    |   n/a     |      P/F      |       |
| Homeowners      |   P/F   |    P/F    |    P/F    |      P/F      |       |
| Auto liability  |   P/F   |    P/F    |    P/F    |      P/F      |       |
| Health OOP max  |   P/F   |    P/F    |    P/F    |      P/F      |       |
| LTC posture     |   P/F   |    P/F    |   n/a     |      P/F      |       |
Scoring: each line PASS only if all applicable tests pass.
Any FAIL -> action item with owner + deadline, logged in the ledger
notes for the quarter ([[fin-cash-flow-framework]] Appendix B).
Two consecutive years of the SAME failure -> escalate to a ratified
decision record rather than another deferred action item.
```

## Appendix G. Self-insurance reserve sizing (retain quadrant)

For risks deliberately retained, the reserve is a priced decision:

```
Reserve(deductible d) = d per occurrence, held in the sinking fund
  register as its own line (SF-ID "SI-xx"), NOT inside the emergency
  fund (different purpose; EF is income-loss coverage).
Retention ceiling rule: retain only exposures whose worst plausible
  single-year aggregate cost <= 2% of net worth AND <= one month of
  gross income. Above that line the ruin test T1 fires and transfer
  becomes mandatory.
Premium-vs-reserve break-even: if annual premium for transferring a
  retained exposure exceeds ~1.5x its expected annual cost (frequency
  x severity) plus loading tolerance, retention is economically sound;
  below it, transfer. Record the comparison when the decision is made.
```

## 8. Cross-references

- [[fin-cash-flow-framework]]: premiums, deductibles, EF multiplier.
- fin-retirement-planning: Medicare bridge, annuity floors,
  healthcare cost modeling.
- [[fin-tax-aware-investing]]: premium funding source taxability;
  HSA interplay with HDHP choices.
- fin-governance-framework: acceptance decisions (self-insured
  risks) ratified and logged there.
