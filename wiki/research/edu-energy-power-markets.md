---
categories:
  - wiki
type: research
created: 2026-08-24
status: complete
confidence: high
tags:
  - topic/energy
  - topic/power-markets
  - topic/equity-research
related: ["[[edu-semiconductor-industry]]", "[[edu-macro-analysis]]"]
---

# Energy and Electricity Markets Analysis Framework (edu)

Generated: 2026-08-24
Purpose: Analytical framework for power generation, grid infrastructure,
data-center electricity demand, PPAs, IPP vs utility structures, and commodity
exposure.
Scope: LCOE/dispatch economics, nuclear, renewables+storage, transmission,
data centers, PPAs, IPPs vs regulated utilities, commodities.
Status: Education/reference corpus. Figures are illustrative magnitudes for
teaching, not live quotes. Re-pull current market data before any decision.

---

## 1. Electricity Market Fundamentals

### 1.1 The physics that creates the market structure

Electricity differs from every other commodity in three ways:

1. **Non-storability (mostly):** supply and demand must balance every second at
   grid frequency (60 Hz US / 50 Hz EU). Deviation shows up as frequency drift;
   sustained imbalance is blackout territory.
2. **Grid-path dependency:** power flows physically along the path of least
   impedance, not along the contract path. Transmission constraints create
   localized prices (congestion).
3. **Inelastic short-run demand:** most consumers see no real-time price.
   Demand barely responds to price within a day; elasticity comes only from
   long-term fuel switching, efficiency, and (newly) demand response.

Consequence: wholesale prices are set by the marginal unit's offer cost and can
swing from near-zero (high renewables) to thousands of $/MWh (scarcity) within
hours. This is why capacity markets, scarcity pricing, and hedges exist.

### 1.2 Market layers

```
ENERGY MARKETS      Day-ahead + real-time (5-min) locational prices ($/MWh)
CAPACITY MARKETS    Payment for being AVAILABLE ($/MW-day) -- PJM/ISO-NE/NYISO/
                    MISO construct; ERCOT uses scarcity pricing instead
ANCILLARY SERVICES  Frequency regulation, spinning reserve, voltage support
FTRs/CRRs           Financial transmission rights hedging congestion
RECs/ECO-ATTRIBUTES Renewable energy credits, clean peak certificates
CAP/FLOOR/COLLARS   Long-term hedge instruments on hub power prices
```

Key hubs to know (US): PJM West (AEP-Dayton), ERCOT North/Houston,
CAISO NP15/SP15, MISO Indiana, ISO-NE Mass Hub, Mid-Columbia (Pacific NW),
Palo Verde (Southwest), Henry Hub is gas not power but drives power.

### 1.3 Merit order / dispatch stack

Economic dispatch runs cheapest-offer first until demand is met:

```
        COST/MWh OFFER (illustrative)
   low | Nuclear          ~$5-15    (marginal cost = fuel + O&M)
       | Wind/Solar      ~$0-5     (zero fuel; must-take often)
       | Hydro            ~$5-20
       | Coal             ~$20-40   (fuel-dependent)
       | CCGT gas         ~$25-45   (= gas price / heat rate + VOM)
       | Gas peaker (CT)  ~$50-90   (less efficient)
       | Battery discharge ~variable (charges on cheap, bids scarcity)
   high| Oil/distillate   ~$150-300 (rare, islands/emergencies)
```

The marginal unit sets price for ALL inframarginal units. When gas sets the
margin (most US hours), power price ~= gas price x heat rate + variable O&M.
This "spark spread" relationship is the single most important cross-commodity
link in the sector.

Definitions:
- **Heat rate:** MMBtu of gas per MWh produced. Modern CCGT ~6.5-7.0; older CT
  ~9.5-11. Lower is better. Implied heat rate = power price / gas price.
- **Spark spread:** power price - (gas price x heat rate). A generator's gross
  margin proxy before fixed costs.
- **Dark spread:** equivalent for coal units. Clean spark/dark spreads add CO2
  cost where carbon is priced.

### 1.4 LCOE: levelized cost of energy

LCOE = total lifecycle cost / total lifetime MWh, discounted. Use it for
cross-technology comparison, but KNOW ITS LIMITS:

| Technology | Unsubsidized LCOE band ($/MWh, illustrative 2024-26) | Capacity factor |
|---|---|---|
| Solar PV (utility) | 25-60 | 15-35% (site-dependent) |
| Onshore wind | 27-75 | 25-45% |
| Offshore wind | 70-140 | 40-55% |
| CCGT (new build) | 45-80 (gas-price dependent) | 55-65% |
| Coal (existing) | 30-70 | 50-85% |
| Nuclear (new build Western) | 140-220 | 90%+ |
| Nuclear (existing fleet) | 30-45 (marginal) | 90%+ |
| Battery storage (4-hr) | 60-130 per discharged MWh | cycles-dependent |
| Geothermal | 60-100 | 70-90% |
| Hydro (existing) | 20-50 | 40-60% |

LCOE blind spots (why investors must look past it):
1. **Value deflation:** solar output clusters midday; as solar share grows,
   midday prices fall toward zero (duck curve). Same LCOE, less revenue.
2. **Firmness mismatch:** a 35%-CF wind farm is not interchangeable with a
   90%-CF nuclear plant. Compare on SYSTEM value (cost to serve load 24/7),
   not plant-level LCOE.
3. **System costs:** backup, balancing, transmission, curtailment are excluded
   from plant LCOE but paid somewhere.
4. Financing-weighted: LCOE moves with WACC more than with steel prices --
   renewables' cost advantage is largely a capital-cost story, hence rate-
   sensitive.

Better metric: **system LACE** (levelized avoided cost of energy) or full
"cost to serve load" modeling. For equity work, what matters is each asset's
realized capture price vs its cost structure, not generic LCOE tables.

---

## 2. Nuclear Power

### 2.1 Operating characteristics

- Baseload king: 92-94% capacity factor industry-wide; refueling outages every
  18-24 months are planned years ahead.
- Marginal cost $5-15/MWh: nearly all fixed. Revenue certainty matters more
  than spot exposure -- hence the PPA/regulated-revenue emphasis below.
- Ramping capability exists (French fleet load-follows) but US economics favor
  flat output because opportunity cost of lost MWh is high relative to fuel
  savings.
- Plant lives: 60-year licenses standard now, 80-year (subsequent license
  renewals) being granted; this extends an already cheap marginal asset's
  tail -- arguably the best cash-flow duration in the sector.

### 2.2 Regulatory framework (US)

- NRC licenses construction, operation, decommissioning funding adequacy.
- Decommissioning trust funds must cover end-of-life teardown; utilities collect
  from ratepayers during operation.
- Post-Fukushima modifications (FLEX equipment, spent-fuel hardening) raised
  operating costs modestly.
- Price-Anderson Act caps/nets liability insurance structure.
- State intervention precedent: NY/ZILM subsidies (Zero Emission Credits),
  Illinois/MIRA and Illinois CMC (carbon mitigation credits) rescued
  uneconomic fleets 2016-2021 -- political risk cuts both ways.
- Export regime: 123 Agreements govern uranium/enrichment trade partners.

Analytical point: existing nuclear revenue security improved structurally
2022-2026 via (a) state ZEC-type programs, (b) IRA's nuclear PTC (production
tax credit ~$15/MWh floor mechanism with revenue tiers), and (c) hyperscaler
PPAs/co-location deals. The asset class repriced from "stranded baseload" to
"firm clean premium product."

### 2.3 New-build economics (the hard part)

Western new-build history is grim: Vogtle 3&4 landed ~$34B+ for two AP1000s vs
$14B original estimate; Flamanville (France) and Hinkley Point C (UK) similar
overruns. Cost drivers: first-of-a-kind engineering, supply-chain atrophy,
craft-labor learning loss, licensing rework, financing during decade builds.

Why it may change: SMRs (small modular reactors, 50-300 MW modules) aim to
move work into factories. Watch list: NuScale (first design certified; first
project cancelled 2023 on cost), GE-Hitachi BWRX-300 (Ontario/TVA builds),
X-energy, TerraPower (Natrium, sodium-cooled, backed by Gates), Oklo
(fast micro-reactors). Key diligence questions for any SMR developer:
1. FOAK vs NOAK honesty: which costs are first-unit-only?
2. Fuel supply: HALEU enrichment is a bottleneck (Russia ban); who secures it?
3. Licensing pathway maturity (Part 50 vs Part 52 combined license).
4. Offtake: signed PPAs or MOUs? MOUs are marketing.
5. Government cost-share structure (DOE programs de-risk but slow things).

### 2.4 Nuclear PPA structures

Recent deal archetypes (2023-2026 wave):
1. **Co-location behind-the-meter:** data center sited AT the plant takes power
   directly, avoiding grid fees/congestion (Talen-Amazon Susquehanna template;
   FERC scrutiny on interconnection amendments is the key regulatory watch).
2. **Front-of-meter PPA:** utility-scale contract from the plant through the
   grid to the buyer (Microsoft-Constellation Crane restart style).
3. **Restart deals:** shuttered plants revived under long contracts (Palisades,
  Duane Arnold class). Economics: capex per MW far below new build, but
   single-site execution risk.
4. **Up-rate + PPA combos:** squeeze extra MW from existing plants, sell firm.

Credit implications: 10-20 year fixed-price PPAs from investment-grade buyers
transform project financeability; watch escalators (CPI-linked?), contract
tenor vs remaining license life, and termination payments.

---

## 3. Renewables Intermittency and Storage

### 3.1 The intermittency problem stated precisely

Solar/wind output is weather-driven and non-dispatchable. System operators must
cover residual load (load minus renewables) with dispatchable resources. As
renewable penetration rises:

- **Net-load duck curve:** midday solar depresses net load; sunset creates a
  3-hour steep ramp (California ramps ~13-17 GW in evening). Ramps stress
  flexible resources and price volatility spikes.
- **Capture-price deflation:** solar-heavy hours clear cheap; a solar farm's
  weighted average realized price falls below hub average ("capture rate"
  declines with penetration -- observed in Spain, Germany, California, South
  Australia).
- **Seasonal mismatch:** summer solar surplus vs winter evenings (northern
  Europe); multi-day lulls ("Dunkelflaute") need firm backup regardless of how
  many batteries are built for daily cycling.

Investor translation: renewables revenue models must include capture-rate
decay curves, curtailment expectations (rising beyond ~10-15% local
penetration), and cannibalization effects. Flat-price PPA assumptions are
where renewable developer write-offs come from.

### 3.2 Storage technology ladder

| Duration | Technology | Best use | Cost trend |
|---|---|---|---|
| Seconds-minutes | Flywheels, supercaps | Frequency response | Niche |
| 1-8 hours | Li-ion (LFP dominant) | Daily arbitrage, ramping | Falling fast |
| 8-100 hours | Flow batteries, Fe-air, CAES, thermal | Multi-day resilience | Pre-commercial |
| Seasonal | Hydrogen (electrolysis->power round trip ~30-40%), pumped hydro | Rare deep lulls | Expensive; policy-driven |

Li-ion economics today: 4-hour system installed cost roughly $200-350/kWh
(2024-26 range, falling); revenue stacks = energy arbitrage + ancillary
services + capacity payment. Ancillary markets saturate quickly (small GW
needs); long-run storage economics depend on arbitrage spreads widening via
volatility -- which rising renewables deliver.

Pumped hydro: 90%+ of world storage capacity historically, 70-85% round-trip
efficiency, 40-80 year lives, but siting/licensing brutal. Existing assets are
gold; new builds scarce in US.

Analytical rule: model storage as PRICE-VOLATILITY HARVESTERS. Their margins
expand when gas prices spike and renewables oversupply midday; their worst case
is flat price shapes with no spread. Check merchant storage exposure vs
contracted tolling agreements (increasingly common with utilities/hyperscalers).

### 3.3 Firm-clean portfolio math (worked example)

Serving 500 MW of 24/7 load with 90% clean target (illustrative):
- 900 MW solar (CF 28%) + 600 MW wind (CF 38%) covers annual energy ~2x load
  but leaves gaps on winter nights/lulls.
- Plus 800 MW / 3,200 MWh batteries bridges daily gaps, NOT multi-day lulls.
- Plus 150-250 MW firm dispatchable (CCGT or recip engines) covers lulls --
  this small firm block is what makes the whole bundle bankable.
Implication: firming capacity retains strategic value even in high-renewables
scenarios; existing dispatchable assets earn scarcity rents during transitions.
This is the core bull logic for well-sited gas fleets and existing nuclear.

---

## 4. Grid Infrastructure

### 4.1 Why transmission became the binding constraint

- US transmission grew slowly for decades (line-miles ~1%/yr growth); load
  growth stalled 2005-2020 so nobody built. Then AI datacenters, theme-gamma,
  and renewables siting arrived simultaneously.
- Interconnection queues: proposed generation+storage projects waiting for
  grid connection studies exceeded 2 TW nationally by mid-decade (vs ~1.3 TW
  installed). Typical queue wait: 4-7 years; cancellation rates high.
- Queue reform (cluster study processes, ready-to-build standards) helps at the
  margin but the physical constraint -- transformer lead times (now 2-4 years),
  HVDC converter lead times, line permitting (10+ yr for big lines) -- persists.

### 4.2 Congestion economics

When the cheapest generation cannot reach load, local prices diverge:
Congestion rent = sum over lines of (price difference x flow). Investors see it
as:
- Basis risk between hub and node for generators/load.
- FTR allocations can be windfall or wipeout depending on auction results.
- Persistent congestion zones attract new build (and higher land values);
  e.g., Virginia Data Center Alley's load growth strained PJM westward flows,
  lifting local capacity prices (PJM 2025/26 capacity auction cleared at
  ~$270/MW-day vs ~$29 prior year -- a structural signal, whatever the exact
  future numbers).

### 4.3 Utility capex supercycle frame

Regulated utility capex plans across the US ran to ~$1.1T+ over 2025-2029
(aggregate of major IOUs), driven by: distribution hardening, transmission for
renewables/datacenters, wildfire mitigation (CA), meter/grid modernization.
Equity translation:
- Rate base growth ~6-9%/yr for well-positioned names -> EPS growth without
  multiple expansion IF regulators grant fair returns.
- Dilution risk: utilities fund capex partly via equity issuance; watch
  "financing plan" credibility in guidance.
- The trade-off table: bigger capex = more growth = more financing risk =
  more regulatory lag exposure.

### 4.4 Who wins in the wires value chain

- Regulated T&D utilities: guaranteed ROE on rate base (9-11% authorized ROEs
  typical), inflation-plus growth.
- Equipment: transformers (long backlogs: GE Vernova, Siemens Energy, Hitachi
  Energy, plus Korean entrants), HVDC systems, switchgear, cable (Prysmian,
  Nexans, NKT -- multiyear order books).
- EPC/services: Quanta, MYR, MasTec -- labor-constrained, backlog visibility
  strong.
- Grid software: OSI/Hexware-type SCADA/DERMS vendors, plus trading/analytics.

---

## 5. Data Center Power Demand

### 5.1 Sizing arithmetic (the MW-to-rack chain)

Worked example, AI training campus:
- Modern GPU rack (8 accelerators, liquid-cooled): 80-130 kW/rack (vs 5-15 kW
  conventional air-cooled enterprise rack).
- 100 MW IT load = ~800-1,200 GPU racks (at ~100 kW average).
- Overhead: cooling + power conversion adds ~25-40% (PUE 1.25-1.4 air-cooled;
  1.1-1.2 good liquid-cooled). So 100 MW IT = 125-140 MW facility draw.
- Utilization diversity ~0.85-0.95 for training (runs hot continuously),
  lower for inference bursts.
- Rule of thumb: 1 GW of datacenter campus ~= 7,000-9,000 GPU-class racks and
  needs roughly one large-ish power plant dedicated to it.

Campus scale benchmarks (order of magnitude, verify current): individual AI
campuses announced at 1-5 GW; aggregate US datacenter load moved from ~2-3% of
US electricity toward 6-10% projections by 2030. Growth rates cited: datacenter
load growing ~15-25%/yr while total US load grows <1%/yr baseline.

### 5.2 Cooling requirements

- Air cooling ceiling: ~30-40 kW/rack practical; above that liquid required.
- Direct-to-chip cold plates: current mainstream for AI racks.
- Immersion (single/two-phase): highest density, niche deployment, facility
  redesign.
- Liquid cooling shifts opex: chilled-water plants shrink; CDUs (coolant
  distribution units), pumps, heat exchangers grow. Facility water usage drops
  (closed loops) unless evaporative towers used -- water rights matter for
  siting in arid regions (Phoenix, Texas debates).
- Heat reuse: Nordic datacenters sell waste heat to district heating; a
  nascent revenue line worth noting in European analyses.

### 5.3 Where the power comes from (procurement hierarchy)

Datacenter operators secure power in rough priority:
1. Existing interconnection capacity at brownfield sites (fastest; scarce).
2. Behind-the-meter co-location with generation (nuclear/gas; regulatory fights
   ongoing about cost allocation).
3. New PPAs (renewables dominate volume; nuclear/firm for 24/7 claims).
4. Utility tariff arrangements (large-load tariffs with demand charges,
   ramp clauses, minimum-take provisions).
5. On-site generation + bridging (fuel cells, gas turbines awaiting grid).

Utility/regulatory flashpoint: who pays for grid upgrades triggered by
hyperscaler load? Large-load tariffs increasingly impose minimum bills and
exit fees to protect other ratepayers. Watch FERC/state dockets -- outcomes
shift billions between ratepayer classes and affect datacenter siting speed.

### 5.4 Investment mapping

Direct beneficiaries ranked by torque:
- IPPs with uncontracted capacity near constrained hubs (ERCOT/PJM): merchant
  upside on scarcity pricing (see Vistra/NRG archetype analysis).
- Utilities with service territories attracting campuses: load growth ->
  rate base growth (GA Power/AEP/Dominion archetypes).
- Nuclear owners with co-location options (Constellation/Talen/Vistra
  archetypes): premium PPAs.
- Equipment: gas turbines (backlog into late-decade; GE Vernova/Siemens
  Energy/Mitsubishi Power), grid gear (section 4.4), cooling/CDU suppliers,
  backup gensets (Cummins/Caterpillar), busway/switchgear.
- Efficiency/liquid-cooling tech inside the rack.

Risks to monitor: AI capex digestion (any hyperscaler capex pause hits all of
the above simultaneously), efficiency gains reducing MW/token (algorithmic),
local moratoria on datacenter water/power use, and interconnection delays
pushing revenue right.

---

## 6. Power Purchase Agreements (PPAs)

### 6.1 Structure taxonomy

| Type | Mechanism | Risk holder |
|---|---|---|
| Physical PPA (fixed price) | Buyer takes delivery at node | Volume+shape on buyer |
| Financial (virtual/cf d) PPA | Fixed strike vs settled hub price; cash-settled | Both hedge; no physical delivery |
| Sleeved PPA | Utility intermediates delivery | Utility credit intermediary |
| Tolling agreement | Buyer operates/bears dispatch of the PLANT | Buyer holds merchant ops |
| Capacity contract | Pay $/MW-month for availability | Availability risk seller |
| Retail supply agreement | Bundled energy+capacity+REC at retail | Simplified buyer side |

Virtual PPAs dominate corporate procurement: buyer pays/receives the
difference between fixed strike and floating hub settlement; used by
Microsoft/Google/etc to claim clean energy and lock power costs.

### 6.2 Pricing anatomy of a PPA

Fixed-for-floating 12-yr solar PPA at $45/MWh hub strike, illustrative:
- Underlying capture expectation: $38/MWh (solar shape discount).
- Green attribute value: $4-8/MWh (state REC mandates or voluntary).
- Developer margin + development premium: remainder.
Key terms to scrutinize (each moves NPV materially):
1. **Tenor:** 10-20 yrs typical; longer = cheaper financing.
2. **Escalator:** flat vs 1-2%/yr vs CPI-capped.
3. **Settlement node vs generation node basis risk** (who owns congestion
   difference?).
4. **Volume structure:** as-generated (seller keeps shape risk) vs
   baseload-shaped (seller must firm -- expensive).
5. **Curtailment allocation:** economic curtailment (negative prices) risk
   usually shared/specified.
6. **Credit support:** parent guarantees, LCs, termination payments sized to
   mark-to-market at default.
7. **Change-of-control, assignment rights** (crucial when either side gets
   acquired).

### 6.3 Credit implications

For the SELLER (generator):
- Investment-grade corporate buyer PPA -> enables non-recourse project finance
  at 60-75% leverage, compresses cost of capital ~200-400 bps vs merchant.
- Merchant projects must be sized to survive downside scenarios (see 6.4);
  lenders advance less debt, require reserves (DSRA 6-12 months debt service),
  and impose distribution locks when coverage ratios slip.

For the BUYER (corporate offtaker):
- A VPPA is a derivative: accounting under ASC 815 (mark-to-market unless
  normal-purchase exemption applies); negative settlements hit earnings.
- Credit rating agencies treat long-dated PPA obligations as committed
  purchases; large cumulative MW commitments can pressure metrics if struck
  above market.
- Termination/liability: breaking a 15-yr PPA early triggers MTM damages that
  can reach hundreds of $millions for large volumes.

### 6.4 Merchant vs contracted revenue mix (the central risk dial)

Rank generator business models by revenue certainty:
1. Regulated cost-of-service (utility-owned): statutory recovery. Lowest risk.
2. Contracted with IG offtakers (nuclear PPAs, utility tolls): near-bond-like.
3. Partially contracted hybrids: blend; check % contracted per year in
   disclosures ("hedged through 2028 at $XX").
4. Fully merchant: exposed to spark spreads/scarcity. Highest variance.
Merchant valuation approach: forward curve for year 1-3 (observable), then
normalized spark-spread scenarios; apply probability weights; discount at
levered equity rates 10-14%. NEVER extrapolate spot spikes as terminal.

---

## 7. IPPs vs Regulated Utilities

### 7.1 Business model contrast

| Dimension | Regulated utility | IPP |
|---|---|---|
| Revenue basis | Cost of service + authorized ROE on rate base | Market prices + contracts |
| Return driver | Rate base growth x allowed ROE | Spread capture, contract origination |
| Regulatory risk | High (rate cases, disallowances) | Low (but permitting/market-rule risk) |
| Commodity risk | Passed to customers | Retained (unless hedged) |
| Demand risk | Shared (decoupling in many states) | Real (volume/price) |
| Capital structure | 45-55% debt typical, IG ratings targeted | Project-level 60-75%, holdco leveraged |
| Dividend policy | High payout (60-70%) | Variable/buybacks preferred |
| Equity beta | ~0.5-0.7 (rates-driven valuation) | ~1.0-1.8 (commodity-driven) |

### 7.2 Valuation frameworks differ accordingly

- Regulated utility: P/E anchored to rate-base growth and allowed ROE gap vs
  cost of equity. Fair multiple ~= f(growth, ROE spread, bond yields). When
  10-yr Treasury rises 100 bps, utility multiples compress mechanically
  (duration trade). Track: authorized-vs-earned ROE gap, equity needs,
  regulatory docket calendar.
- IPP: SOTP of contracted assets (DCF at project discount rates) + merchant
  fleet (scenario EV/EBITDA on normalized spreads) + growth pipeline. Watch:
  hedge book disclosures (% hedged by year), capacity auction results,
  generation availability (outages move EBITDA directly).

### 7.3 Hybrid structures blurring the line

- **Genco carve-outs** (former utility generation in merchant markets).
- **Contracted IPP growth** via utility-style bilateral deals (Vistra's
  Comanche Peak nuclear discussions, datacenter deals generally push IPP books
  toward quasi-contracted).
- **Yieldcos:** contracted renewables portfolios paying out most cash flow
  (NEE's NEER legacy structure, BEP etc.) -- valued like infrastructure
  until contract rollover risk appears.
- **Utility-owned IPP subsidiaries** (Southern Power): contracted fleet inside
  a regulated parent, funded at parent credit.

### 7.4 What breaks each model

Utilities break via: major disallowances (wildfire liabilities -- PG&E
bankruptcy lesson; nuclear decommissioning shortfalls; storm cost disputes),
equity dilution outrunning growth, regulatory lag in inflationary periods.
IPP break via: unhedged commodity crashes (2002-03 merchant power crisis,
Calpine near-death), over-levered holdco structures in rate upcycles,
single-plant outage concentration, capacity market rule changes.

---

## 8. Commodity Price Exposure

### 8.1 Natural gas: the swing fuel that prices everything

- Henry Hub sets the reference; regional basis (Waha, SoCal, Algonquin) can
  decouple wildly on pipeline constraints (Waha went NEGATIVE repeatedly on
  Permian takeaway glut).
- Power-sector gas burn is elastic in aggregate: coal-to-gas switching caps
  power burns above ~$4-5/MMBtu (region dependent); LNG exports link US gas to
  global (JKM/TTF) prices post-2022 -- structural floor-raiser.
- Storage cycle: injection season Apr-Oct, withdrawal Nov-Mar; watch weekly
  EIA storage vs 5-yr band; extreme deviations drive volatility (and storage-
  asset value).
- Volatility products: summer hurricanes (Gulf production), winter freezes
  (demand spikes) create option-value windows; merchant generators ARE long
  embedded volatility.

### 8.2 Uranium

Fuel is tiny in nuclear opex (front-end fuel ~5-8 $/MWh) BUT the uranium
market itself repriced 2023-2026:
- Supply concentrated: Kazakhstan (~40%+), Canada, Australia; enrichment even
  more concentrated (Rosatom ~40%+ global enrichment pre-sanctions).
- Russian Suspension Agreement bans and Section 232-style import restrictions
  forced Western utilities to rebuild western conversion/enrichment contracting
  -> term contract price appreciation (spot vs long-term price divergence is
  the tell of utility restocking).
- Equities: miners (CCJ et al.), enrichers (LEU/centrifuge buildouts, Orano,
  Urenco), fuel fabricators. Note utility inventory overhang dampens urgency;
  term contracting cycles drive the equity narrative more than spot.
- Investor trap: conflating spot price with producer realized prices; term
  books lag spot by years.

### 8.3 Carbon credits/markets

- Compliance markets: EU ETS (allowances ~EUR 60-90/t range recent years),
  UK ETS, California Cap-and-Trade (+ Quebec linkage, auctions quarterly,
  floor price escalates ~5%/yr + CPI), RGGI (Northeast power-sector CO2
  auctions), China national ETS (intensity-based, expanding to more sectors).
- Carbon price transmission: EU power marginal pricing embeds carbon fully
  (clean dark/spark spreads quoted daily); California carbon passes to retail
  with lag; RGGI modest impact.
- Voluntary markets (offsets) are separate, quality-crisis-ridden, mostly
  irrelevant to power equities -- keep them distinct analytically.
- Policy risk dominates: allowance glidepaths (EU MSR, CA post-2030 targets)
  matter more than annual emissions wiggles.

### 8.4 Cross-commodity dashboard (what to track weekly/monthly)

Weekly: EIA gas storage, HH prompt + 12-month strip, PJM/ERCOT forwards,
uranium spot/term quotes.
Monthly: EIA STEO revisions, generation mix stats (gas vs coal vs renewables
share), CPI-linked escalator inputs, capacity auction results when scheduled.
Quarterly: utility rate-case outcomes, IPP hedge percentages disclosed,
datacenter interconnection queue updates, SMR milestone announcements.

### 8.5 Hedging literacy for reading filings

Terms you must parse correctly in 10-Qs/annual reports:
- "Hedged X% of expected generation through YYYY" -> revenue certainty window.
- Heat-rate-neutral hedges / spark-spread collars: floors protect downside,
  caps surrender upside; note strike levels vs current curves.
- Basis swaps: lock location differential; reveals congestion outlook.
- Weather-normalization: some contracts settle on degree-days; reduces
  variance but also caps upside.

---

## 9. Synthesis: Sector Research Workflow

### 9.1 Standard sequence

1. Map the asset's position: technology, region/node, contracted %, remaining
   PPA tenor.
2. Build the revenue line: contracted portion (mechanical DCF) + merchant
   portion (forward curve then normalized scenarios).
3. Stress test: gas +/-50%, capture-rate decay, outage year, interest rate
   +/-150 bps (for levered/yieldco structures).
4. Regulatory overlay: rate case calendar (utilities), market redesign risks
   (capacity market changes, co-location rules), subsidy phase-downs.
5. Financing check: equity needs, covenant headroom, refinancing walls at
   current curves.
6. Relative value: compare implied returns across the risk ladder (section
   7.1) rather than absolute multiples.

### 9.2 Current-era themes checklist (verify recency)

- AI load growth durability vs hyperscaler capex digestion.
- Co-location regulatory resolution (FERC dockets) unlocking nuclear/gas
  premium deals.
- Gas turbine backlog length -> new-build delivery slots priced at premiums.
- Interconnection/transmission reform pace vs load arrival dates.
- Storage economics as volatility expands with renewables share.
- SMR milestone credibility (fuel, licensing, first concrete dates).

### 9.3 Cross-links

- Semiconductor/AI demand side feeding datacenter power:
  [[edu-semiconductor-industry]].
- Rates/inflation driving yieldco and utility valuations:
  [[edu-macro-analysis]] (monetary transmission section).

---

## Appendix A: Glossary

- **Basis:** regional price differential vs benchmark hub.
- **Capacity factor:** actual output / max possible output over a period.
- **Capture rate:** a plant's realized price / hub average price.
- **CCGT:** combined-cycle gas turbine.
- **CDU:** coolant distribution unit (liquid-cooled datacenters).
- **Decoupling:** utility revenue mechanism severing profit from volume.
- **Duck curve:** net-load shape showing midday dip and evening ramp.
- **FTR/CRR:** financial transmission right; congestion hedge instrument.
- **HALEU:** high-assay low-enriched uranium (advanced reactor fuel).
- **Heat rate:** fuel energy per MWh generated; inverse of thermal efficiency.
- **IPP:** independent power producer (merchant generator).
- **ISO/RTO:** independent system operator / regional transmission org (PJM,
  ERCOT, CAISO, MISO, ISO-NE, NYISO, SPP).
- **LCOE:** levelized cost of energy (see limits, section 1.4).
- **PUE:** power usage effectiveness; total facility energy / IT energy.
- **REC:** renewable energy certificate.
- **Spark spread:** power price minus gas cost at given heat rate.
- **VPPA:** virtual power purchase agreement (financial/cfd style).
- **ZEC:** zero emission credit (state nuclear support program).

## Appendix B: Primary Data Sources (offline reference list)

- EIA: Short-Term Energy Outlook, Electric Power Monthly, Weekly Natural Gas
  Storage Report, Form 860/923 plant databases.
- FERC/ISO market reports: PJM State of the Market (Monitoring Analytics),
  ERCOT monthly load reports, CAISO price maps.
- NRC ADAMS database for licensing dockets; state PUC docket portals for rate
  cases.
- Company disclosures: 10-K generation tables, hedge percentage schedules,
  rate base rollforwards.
- World Nuclear Association / UxC summaries for fuel-cycle structure.
- IEA Electricity Reports and LCOE methodology notes (with caveats from 1.4).


---

## Related vault data

Measured references pairing with each framework block above:

- [[ref-energy-power-complex]] -- the generated reference for this exact
  complex: generators, IPPs, utilities, fuel supply, PPA economics.
- [[ref-datacenter-infrastructure]] -- demand-side counterpart: capacity
  pipeline and power density driving Sections 5 and 6.
- [[ref-fed-policy-complete]] -- rate path behind yieldco discount rates
  and the levered-structure sensitivity in Section 7.
- [[ref-inflation-rates-complex]] -- real-rate and breakeven context for
  regulated return-setting and long-duration power assets.
- ref-scenario-stress-test -- gas-shock and rate-shock scenarios applied
  to the energy sleeve of a covered book; Section 7 stress tests made concrete.
- ref-portfolio-risk-decomposition -- how much of current risk sits in
  this complex after the wave-E additions.
- ref-cross-analysis-synthesis -- cross-file read of every wave-E and
  wave-U verdict referenced throughout.
- Companion theory: [[edu-semiconductor-industry]] (demand side) and
  [[edu-macro-analysis]] (rates, growth, and commodity cycles).

*Corpus note: Part 3 of the finance education series. Companion files cover
semiconductor industry analysis and macroeconomic frameworks.*
