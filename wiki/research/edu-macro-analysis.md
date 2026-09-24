---
categories:
  - wiki
type: research
created: 2026-08-24
status: complete
confidence: high
tags:
  - topic/macro
  - topic/equity-research
  - topic/business-cycles
related: ["[[edu-semiconductor-industry]]", "[[edu-energy-power-markets]]"]
---

# Macroeconomic Analysis for Equity Investors (edu)

Generated: 2026-08-24
Purpose: Working framework connecting macro data to equity decisions.
Scope: GDP and leading indicators, inflation measurement, monetary policy
transmission, fiscal policy, currencies, business cycle dating, geopolitical
risk assessment.
Status: Education/reference corpus. Figures are illustrative magnitudes for
teaching, not live quotes or forecasts. Re-pull current data before decisions.

---

## 1. Why Equity Investors Need Macro (and How Much)

### 1.1 The honest decomposition

Equity returns decompose roughly into:
Total return = dividend yield + earnings growth + multiple change.

Macro matters through all three, but its dominant channel is the MULTIPLE and
the CYCLE TIMING of earnings. Over short horizons (<2 years), macro explains a
majority of cross-sectional market variance; over 20-year horizons, valuation
discipline and business quality dominate. Practical stance:

1. Use macro for positioning and risk budgeting (how much beta to carry).
2. Use it for sequencing (which sectors benefit next).
3. Do NOT use macro forecasts as the primary input for single-stock theses --
   company-specific execution usually swamps the macro at 3-5 year horizons.

### 1.2 The three-clock model

Track three clocks that move on different frequencies:

| Clock | Frequency | Key instruments | Drives |
|---|---|---|---|
| Business cycle clock | 3-7 yrs | ISM, claims, payrolls | Earnings direction |
| Liquidity/credit clock | 6-18 mo cycles inside the above | Fed funds, bank credit, yield curve | Multiples, risk appetite |
| Secular regime clock | 10-40 yrs | Demographics, debt/GDP, productivity, inflation regime | Long-horizon real returns |

Most investor errors come from reading one clock and applying it to another:
e.g., extrapolating a liquidity-driven multiple expansion into a permanent
earnings assumption (1999, 2021), or assuming secular stagnation from a normal
inventory cycle (2015).

---

## 2. GDP: Components, Structure, and Reading It Properly

### 2.1 The identity

GDP = C + I + G + NX (consumption + private investment + government +
net exports). US approximate shares: C ~68%, I ~18%, G ~17%, NX ~-3%.
Volatility ranking is the reverse of size: I is small but swings hardest;
C is big and stable; G is policy-variable; NX is mostly a residual that
reflects domestic demand strength relative to foreign.

### 2.2 What each component tells you

**Consumption (~68%):**
- Split goods (~22% of GDP) vs services (~46%). Goods consumption is the
  inventory-cycle engine; services follow employment with a lag.
- Real disposable income growth is the primary driver: C growth tracks
  after-tax real income plus/minus changes in saving rate.
- Excess-savings dynamics matter in unusual periods (2021-2024 pandemic
  accumulation/drawdown distorted every naive model).

**Investment (~18%, but ~100% of recessions):**
- Fixed investment splits: equipment, intellectual property products (now the
  largest slice -- software/R&D capitalized), structures.
- Inventory investment is tiny quarterly but THE swing factor in recessions;
  most post-war recessions feature an inventory liquidation phase.
- Housing is the classic leading component (see 2.4).

**Government (~17%):**
- Watch composition: transfers (which support C) vs direct purchases (which
  are direct GDP). Deficit SIZE and COMPOSITION have different multipliers.

**Net exports:** mostly tell you about domestic appetite; a widening deficit
during expansions is normal, not a warning by itself.

### 2.3 Leading indicators toolkit

**ISM Manufacturing PMI (monthly, first business day-ish):**
- Diffusion index: >50 expanding, <50 contracting; direction of change matters
  more than level. New Orders minus Inventories spread is the internal
  signal (positive spread = restocking ahead).
- ISM Services PMI now matters more structurally (services economy); watch its
  prices-paid component as an inflation diffusion check.
- Lead time: turns lead industrial production by ~2-4 months; false signals
  occur when manufacturing is a small share of the economy.

**Initial jobless claims (WEEKLY, highest frequency reliable cyclical signal):**
- Level thresholds are regime-dependent (labor force growth shifts them);
  use the 4-week moving average and year-over-year change.
- Claims turning up persistently = layoffs accelerating; historically claims
  rising ~15-20%+ off cycle lows preceded recessions with few false positives
  (Sahm-rule adjacent logic).
- Continued claims reveal whether layoffs translate into prolonged
  unemployment (hiring-rate question).

**Housing starts/permits (monthly):**
- Permits lead starts; starts lead residential investment; housing leads the
  cycle by 9-18 months via multiplier chains (construction labor, durables,
  wealth effects).
- Rate-sensitive: mortgage rates drive affordability; existing-home turnover
  collapses then recovers around rate inflections ("lock-in effect" delays
  supply response).
- Single-family vs multifamily split matters (multifamily responds to
  commercial credit conditions).

**Other essentials:**
- Philadelphia Fed / Empire State (early-month regional PMI proxies).
- Chicago Fed National Activity Index (broad diffusion, zero = trend).
- Conference Board LEI (leading economic index): ten-component composite;
  watch 6-month annualized change, not headline level.
- Yield curve (10y-3m, 10y-2y): inversion precedes recession by 8-18 months
  historically; the SIGNAL is dis-inversion + rapid normalization, which
  coincides more closely with recession onset than inversion itself.
- Truck tonnage, rail carloads: physical confirmation of goods cycle.
- Small business optimism (NFIB): hiring/plans components.

### 2.4 Building a simple recession-probability dashboard

Weighted checklist approach (each scored monthly):
1. Claims trend (weight high; weekly frequency).
2. ISM new orders minus inventories + supplier deliveries.
3. Yield curve shape AND its rate-of-change.
4. Housing permits YoY.
5. Bank lending standards (SLOOS) tightening breadth.
6. Real income growth momentum.
Score persistence across >=4 of 6 deteriorating simultaneously before calling
regime change; single-indicator alarms (inverted curve alone) have long,
unprofitable lead times. This mirrors NBER's philosophy: breadth and depth,
not single series.

---

## 3. Inflation Measurement: CPI vs PCE vs PPI

### 3.1 The three measures defined

| Property | CPI-U | PCE deflator | PPI |
|---|---|---|---|
| Publisher | BLS | BEA | BLS |
| Purpose | Cost-of-living (urban consumers) | Economy-wide deflator | Producer receipts |
| Coverage basket | Out-of-pocket consumer purchases | ALL consumption incl. govt/Medicaid-paid | Domestic production, final demand + stages |
| Formula | Laspeyres-ish (fixed basket, updated biennially) | Fisher chain-weighted | Laspeyres chain-type |
| Shelter weight | ~34-36% | ~15-16% | none |
| Health care treatment | Premiums/OOP paid by consumers | Full insurer+govt+consumer spend | producer side |
| Monthly volatility | Higher | Lower (smoother) | Highest (energy inputs) |

Why the Fed targets PCE: broader coverage (includes what insurance/government
pays), chain-weighting reflects substitution behavior, and historical
consistency. CPI runs ~30-50 bps above PCE over time on average.

### 3.2 What each one actually tells you

**CPI:**
- Drives social security COLAs, TIPS principal, tax brackets -> it is the
  POLITICAL and CONTRACTUAL inflation. Markets trade CPI surprises hardest
  because of indexation and because shelter dominates its stickiness story.
- Core CPI (ex food/energy) is noisy month to month due to shelter sampling
  mechanics: OER/rents reflect leases signed 6-12 months ago -> CPI shelter
  LAGS real-time market rents (Zillow/AST class data) substantially. This lag
  created the famous 2022-2024 "shelter will fall" debate; new-lease rent
  indices led core CPI deceleration by ~a year.

**PCE:**
- The Fed's target gauge (2% symmetric). Core PCE is the operative number.
- Because healthcare/government components dominate differences vs CPI, PCE
  can diverge when medical costs or fiscal programs surge.
- Smoothing makes it better for TREND identification; worse for trading
  surprise reactions.

**PPI:**
- Pipeline pressure indicator: goods PPI leads core goods CPI by months
  (retail margins absorb some pass-through).
- Watch stage-of-processing spreads; final-demand services PPI components
  (transportation, warehousing) reveal supply-chain tightness.
- Caveat: PPI excludes imports directly -- a dollar surge suppresses imported
  inflation invisible to PPI.

### 3.3 Decomposition discipline

Split every print into: energy/food shock vs core goods vs core services ex-
shelter vs shelter.
- Core goods: globalization + dollar + chip/commodity cycles (deflationary
  drift historically, tariff-sensitive recently).
- Shelter: backward-looking rental contracts; modelable from market-rent
  series with ~12-mo lag.
- Services ex-shelter: WAGE-DRIVEN (labor share of these costs ~60-70%);
  this is the component the Fed watches to judge "restrictive enough."
Supercore (core services ex-shelter) is the pivot variable in Fedspeak.

### 3.4 Expectations and credibility channels

- Market-based: 10y breakevens (TIPS), 5y5y forward inflation swap -- the
  latter approximates the Fed's implicit credibility gauge.
- Survey-based: UMich vs NY Fed SCE household expectations (UMich skews to gas
  price salience); SPF/Survey of Professional Forecasters for consensus
  anchor; Livingston for history.
- Wage trackers: Atlanta Fed Wage Growth Tracker (better composition control
  than AHE), ECI (cleanest wage measure, quarterly), quits rate as bargaining
  power proxy.
Rule: expectations UNANCHOR only when wage settlements and pricing language
shift together; headline spikes alone rarely do it (1970s lesson took years
of oil shocks + accommodative policy, not one event).

### 3.5 Deflation/disinflation asymmetry

Disinflation (falling inflation RATE) supports multiples; outright deflation
raises REAL debt burdens and delays spending -> historically worse for equities
than moderate inflation. The equity-optimal zone empirically sits near low
single-digit positive inflation; both extremes compress valuations.

---

## 4. Monetary Policy Transmission Mechanism

### 4.1 From fed funds to Main Street: the five channels

The Fed sets overnight rates; transmission to the real economy flows through:

```
FED FUNDS TARGET
      |
      v
[1] MONEY MARKET PASS-THROUGH        SOFR/EFFR track target within days
      |
      v
[2] CREDIT/LENDING CHANNEL           banks reprice loans; SLOOS shows standards
      |                              shifting BEFORE volumes do (2-3 qtrs)
      v
[3] INTEREST-RATE CHANNEL            mortgage/auto/corporate rates reprice;
      |                              housing reacts first (6-12 mo lags)
      v
[4] ASSET-PRICE CHANNEL              discount-rate effect on equities/homes ->
      |                              wealth effect on consumption (~3-5c per $)
      v
[5] EXCHANGE-RATE CHANNEL            rate differentials move USD -> net exports,
                                     import prices, EM stress
      +
[R] EXPECTATIONS CHANNEL             forward guidance shapes the WHOLE curve
                                     before any actual move (dominant channel
                                     since ~2000)
```

Lag structure: peak impact of a policy change on inflation/output arrives
roughly 12-24 months later ("long and variable lags"). Markets front-run this
via asset prices within minutes; Main Street feels it via refinancing waves
and credit availability quarters later. Equity implication: by the time rate
cuts arrive, earnings weakness often ALREADY priced; cutting cycles coincide
with falling multiples early (fear) and recovering multiples late (relief).

### 4.2 The balance sheet (QT/QE) channel

- QE compresses term premium (portfolio balance channel); QT reverses it
  gradually. Empirically QE's marginal effects concentrate in risk premia and
  housing, not bank lending directly.
- Reserves regime: ample-reserves system means fed funds is administered
  (IORB/ON RRP floors) rather than scarce-reserves open-market operations.
  Watch ON RRP usage and reserves distribution as plumbing health checks;
  reserve scarcity episodes (Sept 2019 repo spike) show plumbing can bite
  independently of policy intent.

### 4.3 Reading the Fed correctly

Parse the dual mandate tension in every statement:
- "Maximum employment" assessment drives timing of pivots.
- Inflation projection revisions (SEP dots) drive terminal-rate expectations.
- Communication hierarchy: FOMC statement < press conference < minutes <
  speeches. Dots are projections, NOT commitments; markets repeatedly misprice
  dot-following.
- Financial-stability shadow mandate: emergency facilities (2020, 2023 banking)
  reveal the third implicit mandate. Asset classes reprice when facilities
  appear -- liquidity backstops are bullish risk assets even amid distress.

Practical playbook: build a simple reaction function regression in your head:
policy path ~= f(core PCE trajectory, unemployment gap, financial conditions
index). When market pricing deviates far from that function, either a regime
break is coming (rare) or an opportunity exists (common).

### 4.4 Transmission blockers (when the mechanism fails)

- Lock-in effects: households holding 2-3% mortgages mute rate-INCREASE
  transmission into housing turnover (2022-2024 US anomaly).
- Fixed-rate corporate debt towers delay interest expense resets ~3-5 years
  (maturity walls) -> corporate pain arrives LATER than textbook models say.
- Fiscal dominance episodes: large deficits offset restrictive policy
  (2023-24 debate) -> r-star questions, higher-for-longer curves.
- Credit nonbanks: private credit growth bypasses bank-lending channel ->
  SLOOS reads weaker as transmission gauge than pre-2010.

---

## 5. Fiscal Policy: Deficits, Issuance, Crowding Out

### 5.1 Accounting frame

Deficit = outlays - receipts. Structural vs cyclical split matters: automatic
stabilizers (unemployment insurance, progressive taxes) widen deficits in
recessions legitimately; structural deterioration is the policy choice to
watch. Debt dynamics identity:
Debt/GDP change ~= (r - g) x prior debt ratio - primary balance.
When g > r, debt ratios shrink without primary surpluses (post-WWII US, much
of 2010s); when r > g (2023+ era rates), stabilization requires primary
balance attention. Rising r-star + persistent 6-7% peacetime deficits is the
modern concern combo.

### 5.2 Treasury issuance mechanics investors must know

- Bill/note/bond mix: heavy bill issuance (short-duration funding) when
  deficits balloon; TGA (Treasury General Account) swings drain/add reserves
  mechanically (TGA rebuild = liquidity drain, akin to mild QT).
- Auction cycle: monthly refunding announcements (quarterly refunding
  statements) set sizes; watch auction tails (bid-to-cover, primary dealer
  takeup) as demand-health gauges. Weak auctions raise term premium ->
  higher long yields WITHOUT any Fed action.
- Duration supply wave math: each $1T extra issuance shifted toward coupons
  forces duration absorption by leveraged funds/mutual funds/households once
  bank/Fed demand is absent -> convexity-driven selloffs amplify.

### 5.3 Crowding out vs crowding in -- the practical version

Textbook crowding out: government borrowing raises r, displacing private
investment. Modern nuance set:
1. Open capital account: US borrows globally; crowding out shows up as
   currency strength + current-account widening more than domestic r spike.
2. Sectoral balances identity: government deficit = private surplus +
   external deficit. Big fiscal deficits SUPPORT private income (crowding IN
   cash flow) while borrowing costs compete -- both true simultaneously.
3. Productive vs consumptive composition: deficits funding infrastructure/
   R&D raise g (helping debt math); transfer-heavy deficits raise C without
   capacity gains (worsen inflation if near full employment).
4. Crowding out today concentrates where rates bind hardest: housing,
   small-cap credit, commercial real estate -- sectoral displacement beats
   aggregate narratives.

### 5.4 Fiscal-monetary interaction regimes

| Regime | Signature | Equity posture |
|---|---|---|
| Easy money + easy fiscal | 2020-21 | Everything rally, inflation follows |
| Tight money + easy fiscal | 2023-25 | Barbell: cash yields + real assets; duration punished |
| Easy money + tight fiscal | 2010s | Bond bull, slow growth, multiple-led equity gains |
| Tight money + tight fiscal | 1937, 1938 analogs | Historically worst combos; rare politically |

Watch fiscal impulse (change in deficit contribution to GDP growth) as the
leading variable: fiscal cliff/injection quarters routinely whipsaw GDP prints
and earnings comparisons independent of private-sector health.

---

## 6. Currency Markets

### 6.1 Exchange rate regimes spectrum

- Floating (USD, EUR, JPY, GBP): market-set, central banks occasionally lean.
- Managed float (CNY band, INR smoothing): heavy intervention behind the scenes.
- Crawling pegs / bands (historical examples vary).
- Hard pegs / currency boards (HKD 7.75-7.85 convertibility zone backed by
  aggregate balance sheet; SAR Hong Kong).
- Dollarized/de facto (Ecuador, Panama; much of Gulf pegged to USD via
  oil-invoicing inertia).
Trilemma (impossible trinity): fixed FX + free capital flow + independent
monetary policy -- pick two. Analyze every country position on this triangle
before predicting policy responses.

### 6.2 Valuation and flow models

Long-run anchors:
- PPP (absolute and relative): useful at 3-5 year horizons; deviations can
  persist decades (Big Mac index as intuition pump, not model).
- Real effective exchange rate (REER) vs own history: mean-reversion tendency
  with wide error bars.
Medium-run drivers (the ones that trade):
1. Interest differentials adjusted for expected inflation (real rate gaps) --
   the workhorse since 2014; USD strength episodes map to real-rate gap
   widenings.
2. Terms of trade (commodity currencies: CAD/AUD/BRL/CLP correlate with their
   export baskets).
3. Growth differential surprises.
4. Risk sentiment: USD/JPY/CHF bid in global deleveraging (safe-haven flows
   override carry logic temporarily).
5. Capital flow regimes: FDI/portfolio rebalancing, reserve manager behavior
   (de-dollarization debates: observe ICE share data, gold buying by CBs, not
   rhetoric).

### 6.3 Carry trades: anatomy of the strategy that dies violently

Mechanics: borrow low-yield currency (JPY classic), invest in high-yield
currency (AUD, MXN, TRY-era), earn the differential IF spot doesn't move
against you. Forward premium bias (uncovered interest parity failure) makes
carry profitable on average -- with NEGATIVE SKEW: years of grinding gains,
then crashes in weeks (Aug 2024 yen-carry unwind episode as template; 1998,
2008 analogs).

Risk markers to monitor:
- Positioning estimates (CFTC futures, options skew, dealer gamma surveys).
- Volatility regime: carry dies when realized vol jumps; vol-targeting funds'
  de-grossing amplifies (vol spiral).
- Funding-currency policy shifts: BoJ hawkish surprises are the canonical
  trigger; watch JGB yields and MOF intervention lines in sand (past
  intervention levels get tested repeatedly).
Equity linkage: carry unwinds transmit via (a) Japanese institutions
repatriating, (b) vol-targeted equity de-risking, (c) EM funding squeeze.
Correlations jump toward 1 in these windows -- diversification fails exactly
when needed.

### 6.4 Intervention: how it works and how to read it

- Sterilized vs unsterilized: modern interventions are mostly sterilized
  (offset bond injections), signaling INTENT rather than changing money
  supply; effectiveness comes from positioning pain + coordination, not raw
  volume.
- Signs of intervention: abrupt 1-2% moves in illiquid hours (Tokyo lunch,
  London fix windows), BOJ checking rates calls reported by media, MOF
  confirmation same-day.
- One-way bets against credible central banks defending fundamentals-aligned
  levels eventually lose (SNB 2015 floor abandonment as the catastrophic
  counter-example; HKD peg defense as the durable example backed by full
  reserves backing).
- For equity investors: intervention regimes create mean-reversion zones in
  exporter/importer earnings translations -- model revenue translation bands
  rather than point FX assumptions for multinationals.

### 6.5 Currency exposure in equity portfolios

Translation vs transaction exposure distinction:
- Translation: overseas earnings converted home (weak USD lifts S&P EPS ~2-3%
  per 10% USD depreciation, mechanical estimate).
- Transaction: competitive position effects (strong USD hurts US exporters,
  helps importers, squeezes EM dollar-debtors).
Hedging reality: most large-cap multinationals hedge transaction exposure 6-18
months out only; beyond that, FX flows through. Build currency sensitivity
tables per portfolio name from geographic disclosures (10-K segment data).

---

## 7. Business Cycle Dating

### 7.1 NBER methodology (the official referee)

NBER Business Cycle Dating Committee declares peaks/troughs MONTHS later, using:
- Definition: significant decline in activity spread across the economy,
  lasting more than a few months, visible in production, employment, real
  income, sales.
- Primary series: real personal income less transfers, nonfarm payroll
  employment, civilian employment (household survey), real consumer spending,
  retail sales, industrial production -- weighted judgmentally, NO formula.
- Depth-diffusion-duration criteria replace the old "two consecutive negative
  GDP quarters" folk rule (which fails on e.g., 2001-style shallow recessions
  and 2020-style two-month collapse; also 2022 GDP quirk where GDI/GDP
  diverged with no recession declared).
- Announcement lags: troughs typically called 7-15 months AFTER they occur.
  Investment implication: official dating is for archives, not trading.

### 7.2 Practical real-time dating stack

Build your own nowcast with these layers:
1. Weekly: claims (layoff pulse), rail/truck data (goods flow).
2. Monthly: payroll + unemployment rate trend (Sahm rule: 3-month average
   unemployment rising 0.50pp above trailing 12-month low -- historically
   reliable, watch for false-positive contexts like immigration-distorted
   labor supply), ISM composite, retail sales control group, housing.
3. Quarterly: GDI vs GDP average (GDI captures income side; 2022 divergence
   taught the value of averaging), corporate profit trends (after-tax profits
   fall in nearly every recession).
4. Market-based: curve un-inversion speed, HY spreads >450-500bps territory,
   copper/gold ratio, equity breadth (equal-weight vs cap-weight divergence).
Confluence rule: act when >=3 independent layers deteriorate together; treat
any single alarm as noise otherwise.

### 7.3 Cycle phases and asset behavior (practical mapping)

| Phase | Macro signature | Equity style leadership |
|---|---|---|
| Early recovery | Cuts landing, credit easing, claims falling | Cyclicals, small caps, high beta, financials |
| Mid expansion | Steady growth, stable inflation | Quality growth, broad market |
| Late cycle | Tightening, curve flat/inverted, margins peaked | Energy/materials, defensive quality, value tilt |
| Recession | Falling claims->rising, profit contraction | Staples/healthcare/utilities; cash builds; quality moats |

Rotation trades fail when executed on headlines instead of the claims/credit/
curve triad. Late-cycle duration mismatch: earnings estimates keep rising
while multiples compress -- the classic bull trap signature (2007, 2021-22).

### 7.4 Inventory cycle overlay (Kitchin rhythm)

3-4 year inventory oscillations ride inside longer cycles. Track ISM
customer inventories vs own inventories, auto dealer days-supply, semiconductor
channel fills (cross-ref [[edu-semiconductor-industry]] section 9.3), retail
inventory/sales ratios. Equity tactic: buy cyclicals when customer inventories
are LOW while end-demand stabilizes; avoid them when both inventories and
demand roll over.

---

## 8. Geopolitical Risk Assessment Frameworks

### 8.1 Structuring the unstructured

Geopolitical analysis fails when done as narrative. Convert to structured
inputs:

Step 1 -- Classify the event type:
- Supply-shock (commodity chokepoint, embargo, war damage): inflationary,
  growth-negative, hits specific chains.
- Demand-shock (sanctions retaliation, migration, tourism halt): mixed.
- Financial-contagion (capital flight, sovereign default, payment-system
  exclusion): risk-off correlated.
- Policy-regime (alliance restructuring, tariffs-as-permanent): reprices
  whole industries' cost structures permanently.

Step 2 -- Score dimensions (1-5 each):
- Probability of occurrence (base case, not tail-only).
- Economic blast radius (which commodities/channels).
- Persistence (one-off vs structural).
- Policy response space (can central banks/fiscal offset?).
- Market embeddedness (is it already priced in positioning/vol?).

Step 3 -- Map to portfolios explicitly: name the tickers/chains exposed per
scenario; vague hedging is no hedging.

### 8.2 Chokepoint inventory (memorize the map)

Physical chokepoints and their exposure shares (approximate, verify current):
- Strait of Hormuz: ~20-25% of global oil, major LNG.
- Strait of Malacca: ~25-30% of seaborne trade; Asia energy lifeline.
- Taiwan Strait: semiconductors ([[edu-semiconductor-industry]] sections 3.2,
  8.2-8.3), the single largest concentration of advanced-node capacity.
- Suez/Red Sea corridor: Europe-Asia container routing; reroutes via Cape add
  10-14 days and absorb fleet capacity (freight-rate spikes).
- Panama Canal: drought-constrained transits (2023-24 episode) hitting US Gulf
  LNG/grain flows.
- Danish straits/Bosporus: Russian exports; sanctions enforcement geography.
Each chokepoint maps to specific equity exposures: tanker owners BENEFIT from
route disruption (ton-miles expand), refiners/regional utilities suffer input
costs, defense/logistics names re-rate on persistence.

### 8.3 Sanctions and export-control analytics

Sanctions taxonomy: comprehensive (Iran, NK, Cuba) vs list-based (SDN
designations, Entity Lists) vs secondary sanctions (third-country exposure --
the real teeth). Analysis steps:
1. Identify designated entities' counterparties among investables.
2. Estimate wind-down timelines (general licenses define grace periods).
3. Price enforcement risk: penalties scale with willfulness; banks de-risk by
   wholesale relationship termination.
4. Track evasion architecture: shadow fleets, transshipment hubs (UAE/Turkey/
   Central Asia routes), crypto rails -- enforcement effectiveness decays with
   time as workarounds professionalize (see [[edu-semiconductor-industry]]
   8.3 leakage discussion).
Export controls differ from sanctions: they restrict technology TRANSFER even
between willing parties -- slower-burn, industry-structure-changing (chip
controls reshaped toolmakers' China revenue; see edu-semi section 8).

### 8.4 Scenario planning discipline (probabilities, not stories)

- Maintain 4-6 named scenarios per major flashpoint with explicit
  probabilities summing to 100%; force yourself to update on evidence, not
  vibes (calibration tracking: log predictions, score them quarterly --
  base-rate discipline beats intuition per forecasting literature).
- Pre-commit responses: for each scenario, write the trigger level and the
  pre-agreed portfolio action BEFORE the event (crisis-time decision quality
  collapses otherwise).
- Distinguish price-the-news moments (immediate repricing, fade opportunity
  when blast radius small) from regime-change moments (persistent correlation
  shifts requiring de-grossing).
Historical calibration anchors: markets historically shrug isolated events
(9/11 recovered in weeks; Cuban Missile Crisis days) but reprice sustained
cost structures (1973 embargo -> decade inflation regime; 2022 Russia sanctions
-> European energy industry restructured permanently). Ask always: does this
event change CAPACITY or just FLOWS?

---

## 9. Integration: The Weekly Investor Macro Routine

### 9.1 The cadence

Daily (10 min): claims Thursday, auction results when scheduled, Fed speakers
with vote status, notable geopolitical triggers from your watchlist.
Weekly (30 min): update dashboard scores (section 2.4), gas storage + power
forwards (cross-ref [[edu-energy-power-markets]] 8.4), credit spreads (HY OAS),
breadth measures, positioning proxies.
Monthly (half day): full CPI/PPI/PCE decomposition drill (section 3.3),
payrolls internals (participation, breadth of gains, temp help), ISM details,
housing suite, SLOOS read, Treasury refunding statement review.
Quarterly: revise scenario probabilities, recalibrate recession dashboard
weights, review earnings-revision breadth as macro confirmation, update
currency sensitivity tables.

### 9.2 Common macro-investing errors (checklist)

- Trading the forecast instead of the surprise (markets price consensus).
- Confusing level with momentum in indicators (claims at 250k falling differs
  from claims at 210k rising).
- Extrapolating liquidity-driven multiple expansion into earnings (2021).
- Ignoring fiscal impulse while obsessing over Fed (2023).
- Single-indicator recession calls (curve inversion alone).
- Treating NBER declarations as tradable events (they lag by quarters).
- Narrative-driven geopolitics without probability scoring (section 8.4).
- Applying one country's transmission lags globally (US mortgage structure
  vs UK/Canada reset structures produce very different rate-pain timings).

### 9.3 Cross-links

- [[edu-semiconductor-industry]]: AI capex cycle as both macro driver and
  macro-sensitive demand; export-control geopolitics deep dive.
- [[edu-energy-power-markets]]: commodity channels, electricity load growth
  as new macro input, utility duration behavior vs rates.

---

## Appendix A: Glossary

- **AHE:** average hourly earnings.
- **Breakeven:** nominal Treasury yield minus TIPS yield = implied inflation.
- **ECI:** employment cost index.
- **GDI:** gross domestic income; GDP's income-side twin.
- **NFIB:** National Federation of Independent Business survey.
- **OER:** owners' equivalent rent (CPI shelter component).
- **ON RRP:** overnight reverse repo facility.
- **QT/QE:** quantitative tightening/easing (balance sheet policy).
- **REER:** real effective exchange rate.
- **r-star:** neutral real rate consistent with stable output/inflation.
- **SEP:** Summary of Economic Projections (Fed quarterly).
- **SLOOS:** Senior Loan Officer Opinion Survey.
- **SPF:** Survey of Professional Forecasters.
- **Supercore:** core services inflation excluding shelter.
- **TGA:** Treasury General Account.
- **Trilemma:** fixed FX / free capital flows / independent money -- pick two.

## Appendix B: Data Sources (offline reference list)

- BLS: CPI detailed tables, PPI, employment situation, JOLTS.
- BEA: GDP/GDI by component, PCE detail, state personal income.
- Federal Reserve Board: H.4.1, H.8, Z.1 flow of funds, SEP materials.
- FRED (St. Louis Fed) for series retrieval conventions.
- NBER working papers and cycle dating committee memos (methodology).
- ISM manufacturing/services reports; Conference Board LEI documentation.
- Treasury: monthly refunding statements, TGA statements, auction data.
- CFTC Commitments of Traders; BIS triennial FX survey (structure reference).


---

## Related vault data

Measured macro references consuming the frameworks above:

- [[ref-fed-policy-complete]] -- Section 4's transmission chain rendered in
  observed funds-rate, balance-sheet, and guidance data.
- [[ref-fed-liquidity-engine]] -- net-liquidity model (QT, reserves, repo);
  the operational layer beneath Sections 4 and 5.
- [[ref-inflation-rates-complex]] -- CPI/PCE/breakeven series behind
  Section 3's measurement discussion.
- ref-yen-carry-global-liquidity -- Section 6's currency channel in
  full: carry anatomy, episode census, equity transmission.
- [[ref-market-regime-detector]] -- Section 7's cycle dating implemented
  mechanically over 1,056 classified sessions.
- ref-scenario-stress-test -- six macro shocks wired to the book; what
  each Section 2 through 8 signal does to positions.
- [[ref-energy-power-complex]] and [[ref-semiconductor-value-chain]] --
  sector demand engines keyed to ISM, capex cycles, and power load growth.
- ref-cross-analysis-synthesis -- where macro triggers meet the 51-file
  analysis corpus in one playbook.

*Corpus note: Part 3 of the finance education series. Companion files cover
semiconductor industry analysis and energy/power markets frameworks.*
