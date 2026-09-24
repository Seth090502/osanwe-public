---
categories: [wiki]
type: reference
status: active
created: 2026-08-24
updated: 2026-08-24
confidence: high
tags:
  - topic/investing
  - topic/energy
  - topic/ai-power
related: ["[[ref-financial-statements]]", "[[ref-ai-power-grid-deep-dive]]", "[[ref-theme-alpha]]", "[[ref-semiconductor-value-chain]]", "[[ref-datacenter-infrastructure]]"]
---

# Energy / AI-Power Complex Reference

GENERATED: 2026-08-24 by sector-reference enrichment wave.
REGENERATE: re-run the EDGAR XBRL aggregation over
wiki/investing/filings/`<TICKER>`/`<TICKER>`-xbrl.json (method in
[[ref-financial-statements]]), re-pull technical stats from the factor store
(Efforts/osanwe-v2-overhaul/_work/factors.db bars table), and re-read entity
signals from wiki/entities/tickers/<T>.md. Do not hand-edit numbers; regenerate.
DGS10 sensitivity is a rolling regression on stored factor/bars data (method in
Section 5); re-run it after each factor-store refresh.

## 0. Method and source keys

- FIN[n], TECH[n], ENT[k]: same conventions as [[ref-semiconductor-value-chain]]
  Section 0. Bars end 2026-08-21; DGS10 series ends 2026-08-20.
- RATE[n] = DERIVED weekly regression, Sep-2024 through Aug-2026 (98 weeks):
  each stock's 5-day return regressed on the concurrent change in FRED DGS10
  from the factor store (factor table). "beta per +100bp" = modeled % price
  change for a +1.0pt yield move, all else equal. Correlations are modest
  (|r| 0.04-0.40) -- treat as sensitivity ordering, not precise multipliers.
- PPA[n] = DERIVED arithmetic on corpus-stated contract terms; capacity-factor
  assumption stated per line. No network sources used anywhere in this file.

## 1. Generation / IPPs (CEG / VST / TLN / NRG)

| Name | Rev/LQ (YoY) | NI margin TTM | Price 8/21 | off hi | 1y return |
|---|---|---|---|---|---|
| CEG | $7.5B (+23.0%) FIN | 11.1% FIN | $272.88 TECH | -32.1% | -12.7% |
| VST | $4.0B (-5.5%) FIN | 11.6% FIN | $136.21 TECH | -37.2% | -29.0% |
| TLN | $747M (+18.6%) FIN | -5.1% FIN | $314.46 TECH | -29.5% | -12.7% |
| NRG | $7.5B (+11.0%) FIN | 2.6% FIN | $113.11 TECH | -38.1% | -22.7% |

### 1.1 Contract book (the nuclear premium's substance)

- CEG: Microsoft Crane Clean Energy Center (TMI restart) 837 MW 20-year PPA,
  ~$16B estimated life-of-contract value; TMI restart capex $1.6B, license
  renewal target 2054; Calpine acquisition closed 2026-01-07 taking fleet to
  ~55 GW; CyrusOne 380 MW agreement Feb-2026; ~22 GW nuclear, largest US
  unregulated nuclear operator (all ENT[CEG] via ref-ai-supply-chain /
  ref-ai-power-grid deep dives, HIGH unless noted).
- VST: AWS Comanche Peak 1,200 MW 20-year PPA (delivery Q4-27 to 2032, +20yr
  extension option); Meta 2,609 MW PJM nuclear PPAs across Perry /
  Davis-Besse / Beaver Valley plus 433 MW uprates; ~3,800 MW total PPAs;
  Cogentrix $4.7B acquisition adds 5,500 MW gas; 2026 Adj EBITDA guide
  $6.8-7.6B; 2027 Ongoing Ops midpoint $7.4-7.8B ex-Cogentrix/Meta upside;
  2.3x leverage target YE-27 (all ENT[VST], HIGH).
- TLN: AWS Susquehanna 1,920 MW PPA through 2042, ~$18B revenue over contract
  life; 840-1,200 MW delivery 2029 ramping to 1,680-1,920 MW by 2032; Brandon
  Shores + Wagner RMR through May 2029 (all ENT[TLN], HIGH).
- NRG: ERCOT-heavy IPP with retail smoothing (Reliant/Direct); positioned as
  primary Texas co-location PPA counterparty; catalysts = ERCOT co-location
  announcements + hyperscaler long-duration pricing visibility (ENT[NRG]).

### 1.2 Nuclear premium analysis (DERIVED from cited contracts)

Implied contract economics, flat-revenue split, stated capacity factor:

- CEG-MSFT Crane: ~$16B / (835.5 MW x 20 yr x 8,760h x ~92% CF) ~= $119/MWh
  (~$957k/MW-yr) [DERIVED; CF assumed 92%, typical US nuclear fleet EIA norm -corpus carries no explicit CF figure].
- TLN-AWS: ~$18B / (1,920 MW x 16 yr x 8,760h x ~92% CF) ~= $73/MWh
  (~$586k/MW-yr) [DERIVED, same CF assumption].
- Read-through: hyperscaler nuclear PPAs clear at roughly $70-120/MWh depending
  on vintage, restart-premium content (Crane includes first-ever restart capex)
  and tenor -- versus wholesale PJM/ERCOT baseload prints historically in the
  $30-50s. The premium is the price of firm, carbon-free, behind-the-meter-ish
  capacity with 16-20yr certainty. This spread IS the "nuclear premium" the
  market capitalizes into CEG/VST/TLN equity.
- Cross-check vs market: the premium is already priced -- CEG -32%, VST -37%,
  NRG -38% off highs with negative 1y returns despite record contract books
  (TECH), i.e. multiples de-rated while fundamentals compounded. RATE regression
  (S5) shows these are now high-beta growth names (VST +25%/100bp), not bond
  proxies.

### 1.3 Capacity factors

Corpus carries no explicit measured CF numbers; analysis uses the industry-
standard 92% assumption flagged above [DERIVED]. Nuclear fleet CF is the single
most important un-catalogued input in this file -- populate via /invest when a
primary source lands.

## 2. Grid equipment (GEV / ETN / HUBB)

| Name | Rev/LQ (YoY) | NI margin TTM | Price 8/21 | vs MA200 |
|---|---|---|---|---|
| GEV | $11.1B (+21.9%) FIN | 23.0% FIN | $956.85 TECH | +10.3% |
| ETN | $8.5B (+21.4%) FIN | 12.7% FIN | $419.20 TECH | +11.1% |
| HUBB | n/a (sparse xbrl, 12 pts) FIN | n/a FIN | $470.03 TECH | -2.8% |

- GEV: total backlog $163.3B (vs $123.4B YoY) (HIGH); gas backlog + slot
  reservations 83 -> 100 GW in Q1-26, expecting 110 GW YE-26 (HIGH);
  theme-gamma orders $7.1B Q1-26 ~2x YoY, NA/Asia ~3x; $2.4B data-center
  equipment orders Q1-26 alone -- more than all of 2025 (HIGH); Prolec GE
  consolidation added ~$5B backlog (HIGH) (all ENT[GEV]).
- ETN: total backlog $22.8B, ~68% deliverable within 12 months (HIGH);
  data-center orders +240% Q1, negotiations pipeline +81% YoY; Electrical
  Americas margin 25.6% Q1-26 targeting 32% by 2030; Boyd Thermal $9.55B +
  Ultra PCS $1.53B acquisitions pull cooling in-house (all ENT[ETN], HIGH).
- HUBB: Utility Solutions transformers/meters/grid controls serves utility
  rate-base growth (LOW-grade claims only, ENT[HUBB]); domestic transformer
  manufacturing footprint is the thesis; Ecolab-CoolIT $4.75B deal (29x NTM
  EBITDA) cited as the cooling-consolidation comparable (ENT[HUBB] overview).
- Backlog signal synthesis (DERIVED): GEV+ETN backlog growth rates (32% and
  record levels respectively) are the cleanest leading indicator that the
  binding AI constraint has moved from chips to electrons; transformer/
  switchgear lead times are structural (grid interconnection queues 5-7 years
  per ENT[VRT]/ENT[ETN]) -- equipment makers hold pricing power until queues
  clear.

## 3. Regulated utilities (NEE / AEP / DUK / PPL / SO)

| Name | Rev/LQ | NI margin TTM | Price 8/21 | off hi |
|---|---|---|---|---|
| NEE | $4.4B (2013Q3 label -- STALE corpus row) FIN | n/a | $83.65 TECH | -13.9% |
| AEP | $6.0B (+10.2%) FIN | n/a | $120.94 TECH | -12.1% |
| DUK | $5.9B (2018Q1 label -- STALE) FIN | n/a | $119.85 TECH | -8.6% |
| PPL | $2.8B (+10.8%) FIN | 13.1% FIN | $34.38 TECH | -12.9% |
| SO | $8.4B (+8.0%) FIN | 14.5% FIN | $88.94 TECH | -8.8% |

Rate-base growth and franchise anchors (all ENT, ref-ai-power-grid-deep-dive):

- NEE: world's largest utility-scale renewables operator (>70 GW owned +
  contracted); NEER signs long-duration hyperscaler PPAs; FPL ~5.8M accounts;
  Miami/Tampa/Jacksonville DC load growth (HIGH).
- AEP: ~5.5M customers, ~26 GW generation, ~40k miles transmission; $54B+
  2026-2030 capex plan, ~75% T&D; central PJM DC planner with queue
  concentrated in AEP-Ohio + AEP-Indiana; FERC transmission ROE 10.5%+ (HIGH).
- DUK: ~8.4M customers, ~50 GW; ~$73B 2024-2028 capex ~80% T&D/clean; Carolinas
  emerging Tier-1 DC hot spot; Florida franchise complements NEE/FPL (HIGH).
- PPL: ~3.6M customers PA/KY/RI; $14B+ 5-yr capex ~80% T&D; Susquehanna
  co-location precedent in-footprint (HIGH).
- SO: ~9M customers; Vogtle 3+4 (2.2 GW) the only new US nuclear build in
  decades -> unique new-build-nuclear execution experience for any SMR/AP1000
  scenario (HIGH).

### Rate sensitivity, quantified (RATE[n], Sep-2024..Aug-2026 weekly)

| Name | beta per +100bp DGS10 | corr | interpretation |
|---|---|---|---|
| NEE | +2.2% | +0.09 | rate-insensitive in this window |
| AEP | +4.8% | +0.19 | mild positive -- load-growth narrative dominating duration |
| DUK | -0.7% | -0.04 | classic weak bond-proxy signature |
| PPL | +1.9% | +0.09 | rate-insensitive |
| SO | -0.9% | -0.05 | classic weak bond-proxy signature |

DERIVED conclusion: the AI-load story has broken the sector's historical
inverse-rate behavior -- over this window DGS10 rose ~43bp (4.26% Aug-2025 ->
4.69% Aug-2026, range 3.97-4.75%; 2025 average 4.29%) while utilities fell only
mid-single-digits off highs (TECH) with betas near zero or positive. Duration
risk is currently secondary to load-growth capture. A regime where yields back
up >100bp fast would re-arm duration risk roughly at DUK/SO > NEE/AEP/PPL per
the sign pattern above.

## 4. Nuclear SMR timeline (BWXT / OKLO / SMR)

| Name | Revenue reality | Price 8/21 | off hi | vol21 |
|---|---|---|---|---|
| BWXT | $860M LQ +26.1% (real, profitable) FIN | $156.78 TECH | -34.1% | 42.8% |
| OKLO | $1M LQ (pre-revenue) FIN | $42.09 TECH | -75.8% | 98.9% |
| SMR (NuScale) | $75K LQ (-99.1% artifact) FIN | $9.40 TECH | -82.4% | 91.5% |

Realistic COD dates vs market expectations (corpus claims):

- OKLO: Aurora fast reactor; INL deployment targeted late-2027/early-2028
  commercial; Meta Pike County OH 1.2 GW agreement -- pre-construction 2026,
  FIRST PHASE 2030, full 1.2 GW by 2034; NRC custom COL application accepted
  under accelerated review (all ENT[OKLO]). Market expectation embedded in a
  $7.8B mkt cap on $1M revenue (FIN) prices success well before 2030 -- the gap
  between INL demo (2027/28) and revenue-scale Meta phase (2030+) is the core
  timing risk. Cash ~$2.2B, runway 7-15yr (oklo-analysis-2026-06-07); SI
  20.16% rising; 700+ MWe IOI pipeline (HIGH).
- NuScale (SMR): only NRC-certified SMR design (50 MWe Jan-2023; 77 MWe SDA
  approved ahead of schedule); RoPower Romania 462 MWe FEED Phase 2 complete,
  FID 2026, operations 2030; KGHM Poland VOYGR-12 by 2029 (target); TVA/ENTRA1
  MOU up to 6 GW (nonbinding); Standard Power LOIs 1.85 GW status pending
  (all ENT[SMR]). Realistic first US COD: early-2030s at best; Fluor full exit
  ~$1.83B removes anchor-customer halo (smr-analysis-2026-06-07).
- BWXT: the picks-and-shovels way to own the theme TODAY -- BWRX-300 components
  ~$100M revenue/reactor over ~4-year programs; Project Pele microreactor INL
  delivery 2026, testing through 2028; Rolls-Royce SMR steam-generator contract
  (all ENT[BWXT], HIGH). Profitable now ($91M NI LQ, FIN); revenue compounds
  with every SMR design win regardless of which designer wins.
- Timeline verdict (DERIVED): fleet-relevant SMR power before 2030 is unlikely;
  2030-2034 is the realistic first meaningful COD band (Romania 2030, Meta
  phase-1 2030, Poland 2029-31 targets). Equities price 2027-28 narratives;
  BWXT is the only name of the three whose financials do not require that
  narrative to land on time.

## 5. Storage / BESS (FLNC)

- FLNC: pure-play grid-scale BESS integrator; $3B+ multi-year backlog (HIGH);
  rev $650M LQ +7.9% but NI -$33M TTM (-3.1% margin, FIN); price $11.34,
  -64.8% off high, vol21 87.6% (TECH) -- distressed-multiple territory.
- Data-center BESS demand vector: peak-shaving + UPS-replacement use cases
  emerging alongside renewables-firming hybrids; 4-hour grid-scale storage now
  LCOE-competitive vs gas peakers in many markets (all ENT[FLNC], HIGH).
- Risks carried: CATL/BYD competitive pressure on systems margins; IRA 45X
  phase-out trajectory; project-execution compression vs Tier-1 Chinese
  competitors (MEDIUM, ENT[FLNC]).
- Positioning read (DERIVED): FLNC is the highest-torque way to express
  data-center BESS demand but carries China-cost-curve execution risk; the
  BESS demand itself is corroborated indirectly by GEV's $2.4B Q1-26 DC
  equipment orders and ETN's order book.

## 6. Data-center power / cooling (VRT)

- VRT: 2025 revenue $10.2B; Q4 organic orders +252% YoY; backlog $15.0B +109%
  YoY; book-to-bill ~2.9x; 2026 guide $13.25-13.75B, adj EPS $5.97-6.07 +43%
  at midpoint (Vertiv 8-K Feb 11 2026 via ENT[VRT]/ref-theme-alpha, HIGH).
- Liquid-cooling transition tied to rack density: air-cooling caps out around
  30-40 kW/rack; GB200 NVL72-class racks run ~120 kW and force direct-to-chip
  liquid; VRT captures both power distribution and the cooling transition
  (MEDIUM/HIGH, ENT[VRT]); ETN's Boyd Thermal acquisition ($9.55B) is the
  competitive response (ENT[ETN]).
- Constraint framing: backlog monetization depends on grid interconnection
  (5-7 year queues structural); VRT is ref-theme-alpha's highest-confidence
  compute-to-power rotation candidate; valuation was flagged "priced for
  perfection" at 49x fwd (Apr snapshot) and now sits -30.4% off its high at
  $261.95 with vs-MA200 +3.5% (TECH) -- multiple partially reset.
- Balance sheet context: cash $2.8B vs LTD $2.9B = ~1.0x cover (FIN S6);
  TTM NI margin 14.0%, rev $3.3B LQ +24.1% (FIN).

## 7. Power-layer dependency graph (text form)

```
AI data-center load (see [[ref-datacenter-infrastructure]] for the demand side)
   |
   +-- FIRM CAPACITY CONTRACTS: hyperscaler PPAs
   |      CEG (Crane/MSFT 837MW; CyrusOne 380MW)   VST (AWS 1.2GW; Meta 2.6GW)
   |      TLN (AWS 1.92GW)                          NRG (ERCOT co-location pipeline)
   |           -> implied $70-120/MWh band [DERIVED S1.2]
   |
   +-- GRID DELIVERY: utilities capture via rate base
   |      AEP ($54B capex, PJM queues)  PPL (Susquehanna footprint)
   |      DUK/SO (Carolinas/Atlanta hot spots; SO = Vogtle new-build experience)
   |      NEE (renewables PPAs via NEER + FPL load)
   |
   +-- EQUIPMENT THE ELECTRONS FLOW THROUGH:
   |      GEV ($163B backlog; gas turbines 110GW slots; transformers via Prolec)
   |      ETN ($23B backlog; switchgear; busway)   HUBB (transformers, meters)
   |
   +-- SITE POWER QUALITY + HEAT:  VRT (UPS/busway/liquid cooling, 2.9x b2b)
   |                                  FLNC (BESS peak-shave alternative)
   |
   +-- POST-2030 FIRMING: SMR layer (BWXT components today; OKLO/NuScale CODs
          realistically 2030-2034 [DERIVED]; SO holds AP1000 execution record)
```

## 8. Key risks summary

- IPP cohort (CEG/VST/TLN/NRG): all four de-rated 29-38% off highs with the
  contract books intact (TECH) -- risk is multiple/regime, not demand; watch
  PJM capacity auctions and ERCOT reliability events (VST Q3-25 precedent,
  ENT[VST]).
- TLN single-customer AWS concentration + Fifth Circuit co-location appeal
  (ENT[TLN]); CEG Crane 2028 restart schedule + 835-vs-837 MW reconciliation
  flag (ENT[CEG]).
- Utilities: duration re-arms if DGS10 gaps >100bp (sign pattern S3); NEE/DUK
  corpus rows are stale (2013/2018 labels) -- do not quote their FIN lines.
- Equipment: backlog cancellation/deflation if a compute air-pocket hits
  hyperscaler budgets; ETN/GEV priced well above 5-yr averages (ENT[ETN]).
- SMR: equity timelines run 2-4 years ahead of engineering timelines (S4).

## 9. Cross-references

- Demand side (who buys the power): [[ref-datacenter-infrastructure]].
- Upstream silicon demand driver: [[ref-semiconductor-value-chain]].
- Method + caveats: [[ref-financial-statements]]. Claim provenance:
  wiki/entities/tickers/<T>.md; deep dives ref-ai-power-grid-deep-dive-ingest
  (2026-05-06), ref-theme-alpha-ingest (2026-04-22, 2026-07-16).

## 10. Data gaps

- No xbrl json: none missing in this tier set, but NEE/DUK latest rows are
  years stale (FIN S7) and HUBB/GEV corpora are sparse (<45 points).
- Capacity factors: no primary figures in corpus; 92% assumption used (S1.2).
- EPS: zero points corpus-wide; omitted (FIN S7).
- Factor-store closes end 2026-08-21; DGS10 ends 2026-08-20.
## 11. Per-company deep profiles (16-name expansion, 2026-08-24)

Method: FIN = EDGAR XBRL from wiki/investing/filings/<T>/<T>-xbrl.json using the
same conventions as [[ref-financial-statements]] (latest-filed dedupe; FY 10-K
periods converted to discrete Q4d where Q1-Q3 exist; TTM = last 4 reported
quarters spanning 240-400 days; YoY = same fiscal quarter prior year). TECH =
factor-store bars through 2026-08-24 (DGS10 through 2026-08-20). ENT/WAVE =
wiki/entities/tickers/<T>.md + the latest wave analysis named in that entity's
Data layers block. All derived stats recomputable; do not hand-edit numbers.
Known XBRL quirks carried with each line: TLN/FLNC FY 10-K revenue rows are
corrupt in the JSONs (negative FY values), so their TTM cells are n/a; NEE/DUK
revenue corpora are stale (2013/2018) -- NI rows are current but never quote
their revenue lines.

### 11.0 Cohort technical summary table

| T | Px 8/24 | off hi (date) | vs MA50 | vs MA200 | vol21 ann. | 5y tot | max DD |
|---|---|---|---|---|---|---|---|
| CEG | $271.70 | -32.4% (2025-10-15) | +3.2% | -9.0% | 34.7% | +572% | -50.7% |
| VST | $136.35 | -37.2% (2025-09-22) | -11.0% | -14.4% | 50.6% | +711% | -48.8% |
| TLN | $306.73 | -31.2% (2025-10-08) | -16.3% | -15.1% | 60.2% | +560%* | -33.8% |
| NRG | $111.38 | -39.1% (2026-02-24) | -15.1% | -24.8% | 80.8% | +189% | -39.1% |
| GEV | $939.50 | -20.0% (2026-06-30) | -9.3% | +8.1% | 52.2% | +619%* | -38.3% |
| ETN | $410.17 | -10.8% (2026-08-12) | -1.4% | +8.7% | 54.6% | +162% | -34.5% |
| HUBB | $469.35 | -15.6% (2026-04-23) | -5.1% | -2.9% | 38.9% | +148% | -32.6% |
| VRT | $254.39 | -32.4% (2026-05-14) | -13.2% | +0.4% | 89.3% | +829% | -71.2% |
| FLNC | $11.03 | -70.7% (2021-11-15) | -31.0% | -40.2% | 87.0% | -68% | -90.4% |
| BE | $203.88 | -41.1% (2026-06-22) | -15.5% | +9.1% | 115.6% | +861% | -75.9% |
| AEP | $120.90 | -12.2% (2026-06-26) | -6.9% | -3.3% | 19.1% | +62% | -29.6% |
| DUK | $121.03 | -7.7% (2026-03-16) | -2.8% | -1.0% | 18.4% | +40% | -24.2% |
| PPL | $34.78 | -11.9% (2026-04-09) | -2.8% | -3.4% | 17.5% | +42% | -24.7% |
| SO | $89.75 | -7.9% (2026-03-16) | -4.2% | -1.4% | 14.9% | +64% | -23.3% |
| NEE | $83.63 | -13.9% (2026-04-30) | -4.0% | -4.0% | 12.5% | +13% | -45.0% |
| BWXT | $151.83 | -36.1% (2026-04-15) | -15.4% | -21.6% | 45.2% | +180% | -36.1% |

(* = shorter history: TLN bars start 2023-06-02, GEV 2024-03-27; "5y tot" is
total return since first stored bar, not a true 5y figure for those two.)
TECH[DERIVED] throughout this section. SPY same-window horizons for reference:
+3.5% / +2.9% / +12.7% / +21.7%.

### 11.1 CEG -- Constellation Energy

- FIN: rev LQ 2026Q2 $7.50B (+23.0% YoY); TTM rev $31.27B; TTM NI $3.46B =
  11.1% margin; NI-LQ $513M (-38.9% YoY); cash $697M @2026-06-30 vs LTD $7.40B
  (@FY25); capex FY25 $2.95B (FIN S7).
- TECH: $271.70, hi $401.70 @2025-10-15 (-32.4%); +3.2%/MA50, -9.0%/MA200;
  52w range position 21%; vol21 34.7%; horizons 1m -0.8% / 3m -7.5% / 6m -7.1%
  / 1y -12.6% vs SPY +21.7%; 5y total +572%, max drawdown -50.7%.
- ENT/WAVE: largest US unregulated nuclear operator (~22 GW); Calpine closed
  2026-01-07 ($16.4B, fleet to ~55 GW); MSFT Crane PPA 837 MW x 20yr (~$16B);
  CyrusOne 380 MW Feb-2026; TMI restart capex $1.6B, license target 2054;
  835-vs-837 MW reconciliation flag open (ENT[CEG]). WaveE-ceg-analysis:
  HOLD conf 66 -- bounced +15.6% off the 7/01 low and back above MA50, but
  -8.7% below a falling MA200; hold band [+18,-18]% vs $272.88.
- Role: anchor nuclear-premium asset; thesis lives or dies on restart
  execution (Crane 2028) and follow-on hyperscaler PPAs, not on load growth.

### 11.2 VST -- Vistra

- FIN: rev LQ 2026Q2 $4.02B (-5.5% YoY); TTM rev $19.21B; TTM NI $2.22B =
  11.6% margin; NI-LQ $305M; cash $435M @2026-06-30 vs LTD $19.59B (heaviest
  IPP balance sheet of the four); capex FY25 $2.75B (FIN S7).
- TECH: $136.35, hi $217.02 @2025-09-22 (-37.2%); below every MA
  (-11.0%/MA50, -14.4%/MA200); 52w position 2%; vol21 50.6%; horizons 1m
  -16.5% / 3m -12.6% / 6m -18.5% / 1y -28.0%; 5y total +711%, max DD -48.8%.
- ENT/WAVE: AWS Comanche Peak 1,200 MW x 20yr PPA; Meta 2,609 MW PJM nuclear
  PPAs + 433 MW uprates; ~3,800 MW contracted; Cogentrix $4.7B adds 5,500 MW
  gas; 2026 Adj EBITDA guide $6.8-7.6B; 2.3x leverage target YE-27 (ENT[VST]).
  waveE-vst-analysis: HOLD conf 55, RSI14 26.1 after -19.4%/21d vs SPY +3.7%;
  no entry below MA50; hold band [+16,-12]%.
- Role: highest-torque contracted-nuclear compounder; deepest de-rate of the
  cohort despite the most diversified contract book -- the market is pricing
  leverage + ERCOT regime risk, not demand (S8).

### 11.3 TLN -- Talen Energy

- FIN: rev LQ 2026Q2 $747M (+18.6% YoY); TTM rev n/a (FY 10-K revenue row
  corrupt in xbrl json); TTM NI n/a (same quirk); NI-LQ -$92M; cash $231M
  @2026-06-30 vs LTD $9.57B; capex FY25 $98M (FIN S7).
- TECH: $306.73, hi $445.84 @2025-10-08 (-31.2%); -16.3%/MA50, -15.1%/MA200;
  52w position 3%; vol21 60.2% (highest IPP); horizons 1m -14.8% / 3m -17.6%
  / 6m -16.6% / 1y -14.3%; since 2023-06 +560%, max DD -33.8%.
- ENT/WAVE: AWS Susquehanna 1,920 MW PPA through 2042 (~$18B life-of-contract);
  840-1,200 MW delivery 2029 ramping to full by 2032; single-customer AWS
  concentration + Fifth Circuit co-location appeal are the standing risks
  (ENT[TLN]). waveE-tln-analysis: HOLD conf 62 after the 8/18 -11.0% flush;
  hold band $270-$370.
- Role: purest single-asset nuclear premium proxy; smallest diversification,
  cleanest read on co-location jurisprudence.

### 11.4 NRG -- NRG Energy

- FIN: rev LQ 2026Q2 $7.48B (+11.0% YoY); TTM rev $33.12B; TTM NI $849M = 2.6%
  margin (thinnest of the IPP cohort); NI-LQ $506M; cash $162M @2026-06-30 vs
  LTD $23.39B; capex FY25 $1.15B (FIN S7).
- TECH: $111.38, hi $182.82 @2026-02-24 (-39.1% = cohort-worst off-high);
  -15.1%/MA50, -24.8%/MA200; 52w position 0%; vol21 80.8% (cohort-worst);
  horizons 1m -20.7% / 3m -18.8% / 6m -36.5% / 1y -22.7%; 5y total +189%.
- ENT/WAVE: ERCOT-concentrated IPP with Reliant/Direct retail smoothing;
  positioned as primary Texas co-location counterparty; catalysts = ERCOT DC
  co-location announcements + long-duration pricing visibility (ENT[NRG]; no
  dedicated wave file yet -- entity note only).
- Role: option on the Texas co-location cycle without a signed hyperscaler
  mega-PPA yet; retail book cushions but does not de-risk the multiple.

### 11.5 GEV -- GE Vernova

- FIN: rev LQ 2026Q2 $11.10B (+21.9% YoY); TTM rev $41.37B; TTM NI $9.53B =
  23.0% margin (note: FY26 Q4d NI $3.66B carries one-off items -- treat the
  TTM margin as flattered); NI-LQ $668M (+30.0% YoY); cash/LTD absent from
  xbrl json (FIN S7). Corpus sparse: 36 points.
- TECH: $939.50, hi $1,174.86 @2026-06-30 (-20.0%); -9.3%/MA50 but +8.1%
  above MA200; 52w position 63%; vol21 52.2%; horizons 1m -7.4% / 3m -9.5% /
  6m +13.1% / 1y +55.4% -- only equipment name positive over 6m.
- ENT/WAVE: total backlog $163.3B (vs $123.4B YoY); gas backlog + slot
  reservations 83 -> 100 GW Q1-26 targeting 110 GW YE-26; theme-gamma
  orders $7.1B ~2x YoY; $2.4B data-center equipment orders in Q1-26 alone --
  more than all of 2025; Prolec GE consolidation added ~$5B backlog
  (ENT[GEV]). waveE-gev-analysis: first-ever kernel, HOLD conf 45; hold band
  [+23,-10]%.
- Role: the two scarcest AI-power supply chains at once -- heavy gas turbines
  (multi-year slot wall) and grid theme-gamma equipment.

### 11.6 ETN -- Eaton

- FIN: rev LQ 2026Q2 $8.53B (+21.4% YoY); TTM rev $30.02B; TTM NI $3.83B =
  12.7% margin; NI-LQ $821M (-16.4% YoY); cash $483M @2026-06-30 vs LTD
  $18.52B; capex FY25 $919M (FIN S7).
- TECH: $410.17, hi $459.96 @2026-08-12 (-10.8%, shallowest equipment-cohort
  drawdown); -1.4%/MA50, +8.7%/MA200; 52w position 66%; vol21 54.6%; horizons
  1m +1.8% / 3m +5.1% / 6m +14.2% / 1y +20.1%; 5y total +162%, max DD -34.5%.
- ENT/WAVE: backlog $22.8B, ~68% deliverable within 12 months; DC orders
  +240% Q1, negotiations pipeline +81% YoY; Electrical Americas margin 25.6%
  targeting 32% by 2030; Boyd Thermal $9.55B + Ultra PCS $1.53B pull cooling
  in-house (ENT[ETN], HIGH). WaveE-etn-analysis: BUY conf 62 -- the only BUY
  rating in the 16-name set.
- Role: shortest-cycle electrical equipment exposure; converts DC orders to
  revenue inside 12 months while GEV slots run years.

### 11.7 HUBB -- Hubbell

- FIN: xbrl json carries NO revenue/NI points (12 LongTermDebt rows only, LTD
  $1.44B @2025-09-30) -- all financial cells n/a by construction (FIN S7).
- TECH: $469.35, hi $556.18 @2026-04-23 (-15.6%); -5.1%/MA50, -2.9%/MA200;
  52w position 43%; vol21 38.9%; horizons 1m -3.4% / 3m -0.9% / 6m -8.7% /
  1y +11.1%; 5y total +148%, max DD -32.6%.
- ENT/WAVE: Utility Solutions transformers/meters/grid controls serves utility
  rate-base growth (LOW-grade claims only, ENT[HUBB]); domestic transformer
  footprint is the thesis; Ecolab-CoolIT $4.75B deal cited as the cooling-
  consolidation comparable (ENT[HUBB] overview). No wave analysis exists.
- Role: lowest-beta rate-base compounder of the equipment trio -- the
  "boring transformer" leg; corpus coverage is thin, flag for /invest.

### 11.8 VRT -- Vertiv

- FIN: rev LQ 2026Q2 $3.27B (+24.1% YoY); TTM rev $11.48B; TTM NI $1.61B =
  14.0% margin; NI-LQ $498M; cash $2.81B @2026-06-30 vs LTD $2.94B (~1.0x
  cover); capex FY25 $220M (asset-light integrator) (FIN S6/S7).
- TECH: $254.39, hi $376.15 @2026-05-14 (-32.4%); -13.2%/MA50, +0.4%/MA200;
  52w position 52%; vol21 89.3%; horizons 1m -12.4% / 3m -22.3% / 6m +3.7% /
  1y +101.2%; 5y total +829%, max DD -71.2% (deepest historical drawdown in
  the 16-name set).
- ENT/WAVE: 2025 revenue $10.2B; Q4 organic orders +252% YoY; backlog $15.0B
  +109% YoY; book-to-bill ~2.9x; 2026 guide $13.25-13.75B, adj EPS
  $5.97-6.07 +43% at midpoint (Vertiv 8-K Feb 11 2026 via ENT[VRT]/ref-theme-alpha,
  HIGH). waveE-vrt-analysis: HOLD conf 66; hold band [+10,-15]% vs $261.95.
- Role: inside-the-fence power train + liquid cooling; the direct rack-density
  play as GB200-class racks force direct-to-chip cooling.

### 11.9 FLNC -- Fluence Energy

- FIN: rev LQ 2026Q2 $650M (+7.9% YoY); TTM rev n/a (FY 10-K revenue row
  corrupt: negative FY value in xbrl json); TTM NI n/a (same quirk); NI-LQ
  -$33M; cash $339M @2026-06-30; capex FY25 $6M (FIN S7).
- TECH: $11.03, -70.7% below its 2021-11-15 IPO-era high $37.61 (the only
  name whose all-time high predates the AI cycle); -31.0%/MA50, -40.2%/MA200;
  52w position 17%; vol21 87.0%; horizons 1m -17.9% / 3m -48.7% / 6m -31.3% /
  1y +61.3%; 5y total -68%, max DD -90.4%.
- ENT/WAVE: pure-play grid-scale BESS integrator; $3B+ multi-year backlog
  (HIGH); CATL/BYD cost-curve pressure, IRA 45X phase-out trajectory,
  Tier-1 Chinese execution compression (MEDIUM, ENT[FLNC]).
  waveU-flnc-analysis: SELL conf 55 -- avoid-initiation stance.
- Role: torque on DC peak-shave/firming demand with China-cost execution
  risk; the only SELL-rated name in the set.

### 11.10 BE -- Bloom Energy

- FIN: NO revenue points in xbrl json (12 NetIncome rows, all negative,
  ending -$47M @FY2023) -- financial cells n/a by construction; the corpus
  cannot yet see Bloom's post-2023 inflection (FIN S7).
- TECH: $203.88, hi $345.85 @2026-06-22 (-41.1%); -15.5%/MA50, +9.1%/MA200;
  52w position 52%; vol21 115.6% (highest in the entire 16-name set);
  horizons 1m +10.3% / 3m -32.6% / 6m +27.2% / 1y +354.8% (largest 1y move in
  either direction across the set); max DD -75.9%.
- ENT/WAVE: Oracle 2.8 GW MSA + 1.2 GW already-contracted deployments; Nebius
  master fuel-cell capacity agreement up to $2.6B / three 10-yr phases,
  phase-1 328 MW live 2026; Brookfield $5B partnership; 2 GW annual capacity
  target end-2026; 800 VDC architecture deployments H2-2026 (ENT[BE],
  be-analysis-2026-06-18). waveU-be-analysis: HOLD conf 50; wide hold band
  [+72,-19]% reflecting the vol.
- Role: bridge-power / on-site generation pure-play when the grid cannot
  deliver MW fast enough; the highest-variance expression in the set.

### 11.11 AEP -- American Electric Power

- FIN: rev LQ 2026Q1 $6.02B (+10.2% YoY); TTM rev $22.43B; TTM NI n/a (NI
  series has a hole -- latest NI row 2024Q3); NI-LQ n/a; cash $306M
  @2026-03-31 vs LTD $49.55B; capex FY25 n/a (stale 2018-2021 rows) (FIN S7).
- TECH: $120.90, hi $137.64 @2026-06-26 (-12.2%); -6.9%/MA50, -3.3%/MA200;
  52w position 51%; vol21 19.1%; horizons 1m -10.1% / 3m -7.4% / 6m -7.1% /
  1y +10.2%; 5y total +62%, max DD -29.6%.
- ENT/WAVE: ~5.5M customers, ~26 GW, ~40k miles transmission; $54B+ 2026-2030
  capex plan ~75% T&D; central PJM DC planner, queue concentrated in
  AEP-Ohio + AEP-Indiana; FERC transmission ROE 10.5%+ (HIGH, ENT[AEP]).
  waveU-aep-analysis: HOLD conf 45; hold band [+13,-15]%.
- Role: the purest regulated DC-load-growth capture -- PJM queue monetized
  through rate base rather than PPAs.

### 11.12 DUK -- Duke Energy

- FIN: revenue corpus STALE (latest row 2018Q1 $5.93B -- never quote it);
  current-side NI rows exist: NI-LQ 2026Q1 $1.55B; FY25 NI $4.97B raw; cash
  $2.14B @2026-03-31 vs LTD $87.21B @2025-12-31; capex FY25 $14.02B (FIN S7).
- TECH: $121.03, hi $131.16 @2026-03-16 (-7.7%, shallowest drawdown among
  power names); -2.8%/MA50, -1.0%/MA200; 52w position 50%; vol21 18.4%;
  horizons 1m -6.5% / 3m -2.8% / 6m -3.6% / 1y +0.9%; 5y total +40%, max DD
  -24.2%.
- ENT/WAVE: ~8.4M customers, ~50 GW; ~$73B 2024-2028 capex ~80% T&D/clean;
  Carolinas emerging Tier-1 DC hot spot; Florida franchise complements FPL
  (HIGH, ENT[DUK]). waveU-duk-analysis: HOLD conf 45; hold band [+10,-7]%.
- Role: Carolinas DC boom via rate base; classic low-vol bond-proxy profile
  (see Section 13 sign pattern).

### 11.13 PPL -- PPL Corp

- FIN: rev LQ 2026Q1 $2.77B (+10.8% YoY); TTM rev $9.31B; TTM NI $1.22B =
  13.1% margin; NI-LQ $452M; cash $1.24B @2026-03-31 vs LTD $18.89B; capex
  FY25 $4.03B (FIN S7).
- TECH: $34.78, hi $39.49 @2026-04-09 (-11.9%); -2.8%/MA50, -3.4%/MA200; 52w
  position 30%; vol21 17.5% (lowest of the five utilities); horizons 1m -4.0%
  / 3m -3.5% / 6m -5.2% / 1y -2.3%; 5y total +42%, max DD -24.7%.
- ENT/WAVE: ~3.6M customers PA/KY/RI; $14B+ 5-yr capex ~80% T&D; Susquehanna
  co-location precedent in-footprint (HIGH, ENT[PPL]).
  waveU-ppl-analysis: HOLD conf 45; hold band [+15,-5]%, tightest downside
  band in the utility set.
- Role: most direct Pennsylvania DC pipeline + the TLN/AWS co-location
  precedent sits inside its territory.

### 11.14 SO -- Southern Company

- FIN: rev LQ 2026Q1 $8.40B (+8.0% YoY); TTM rev $30.18B; TTM NI $4.36B =
  14.5% margin; NI-LQ $1.36B; cash $981M @2026-03-31; LTD absent from xbrl
  json; capex FY25 $12.74B (FIN S7).
- TECH: $89.75, hi $97.49 @2026-03-16 (-7.9%); -4.2%/MA50, -1.4%/MA200; 52w
  position 50%; vol21 14.9% (lowest of all 16 names); horizons 1m -6.9% /
  3m -4.3% / 6m -4.1% / 1y -2.0%; 5y total +64%, max DD -23.3%.
- ENT/WAVE: ~9M customers; Vogtle 3+4 (2.2 GW) the only new US nuclear build
  in decades -- unique AP1000 execution record for any SMR/new-build scenario
  (HIGH, ENT[SO]). waveU-so-analysis: HOLD conf 45; hold band [+10,-8]%.
- Role: Atlanta DC hot spot + the new-build-nuclear execution credential;
  lowest-volatility carrier of the AI-power theme.

### 11.15 NEE -- NextEra Energy

- FIN: revenue corpus STALE (latest row 2013Q3 $4.39B -- never quote it);
  current NI rows exist: NI-LQ 2026Q1 $2.18B; FY25 NI $6.84B raw; cash $2.00B
  @2026-03-31; LTD absent from xbrl json (FIN S7).
- TECH: $83.63, hi $97.17 @2026-04-30 (-13.9%); -4.0%/MA50, -4.0%/MA200; 52w
  position 53%; vol21 12.5%; horizons 1m -6.9% / 3m -4.9% / 6m -9.8% /
  1y +13.1%; 5y total +13% (weakest 5y of the 16), max DD -45.0% (2022 rate
  shock legacy).
- ENT/WAVE: world's largest utility-scale renewables operator (>70 GW owned +
  contracted); NEER signs long-duration hyperscaler PPAs; FPL ~5.8M accounts;
  Miami/Tampa/Jacksonville DC load growth (HIGH, ENT[NEE]).
  waveE-nee-analysis: HOLD conf 45 citing 33 GW NEER backlog (+4 GW Q1-26);
  hold band [+16,-8]%.
- Role: renewables-firming route to the same DC demand; NEER PPA machine is
  the differentiated asset vs the four wire-bound peers.

### 11.16 BWXT -- BWX Technologies

- FIN: rev LQ 2026Q1 $860M (+26.1% YoY); TTM rev n/a (quarter gap in Revenue
  series breaks the 240-400 day span rule); TTM NI n/a (same gap); NI-LQ $91M
  (+20.7% YoY per ref-financial-statements); cash $512M @2026-03-31; LTD
  stale ($300M @2015); capex FY25 $185M (FIN S7).
- TECH: $151.83, hi $237.73 @2026-04-15 (-36.1%, AT the 52-week low at wave
  time); -15.4%/MA50, -21.6%/MA200; 52w position 0%; vol21 45.2%; horizons
  1m -12.9% / 3m -25.1% / 6m -23.1% / 1y -7.6%; 5y total +180%, max DD -36.1%.
- ENT/WAVE: BWRX-300 components ~$100M revenue/reactor over ~4-year programs;
  Project Pele microreactor INL delivery 2026, testing through 2028;
  Rolls-Royce SMR steam-generator contract; profitable now ($91M NI-LQ)
  (ENT[BWXT], HIGH). waveE-bwxt-analysis: HOLD conf 55, kernel rejected on
  stop-inside-noise-band; hold band [+22,-22]%.
- Role: picks-and-shovels SMR supplier paid on components today regardless of
  which designer wins -- the only SMR-chain name whose financials do not
  require a 2030s COD to land on schedule (S4).

### 11.17 Cross-profile synthesis [DERIVED]

- The 2025-26 tape split the complex in two: equipment + utilities held
  (GEV 1y +55%, ETN +20%, AEP +10%) while every signed-contract IPP fell
  (CEG -13%, TLN -14%, NRG -23%, VST -28%) -- multiples de-rated into intact
  fundamentals (WAVE, all six wave files, 2026-08-24).
- Volatility ordering maps exactly to business-model distance from regulated
  cash flows: SO 14.9% < PPL 17.5% < DUK 18.4% < AEP 19.1% << CEG 34.7% <
  HUBB 38.9% < GEV 52.2% < ETN 54.6% < TLN 60.2% << NRG 80.8% < VRT 89.3% <
  FLNC 87.0% < BE 115.6% (annualized vol21).
- Coverage gaps to close via /invest: no wave files for NRG/HUBB; BE/HUBB
  xbrl jsons carry no usable revenue; TLN/FLNC/BWXT TTM blocked by corrupt or
  gapped quarters; NEE/DUK revenue lines stale.

### 11.18 Quarterly revenue trajectory (last 6 reported quarters, $B)

Same-quarter YoY in parentheses where computable; Q4d-derived cells marked *.
Quirks per S11 headers apply (TLN/FLNC/BWXT TTM blocked; NEE/DUK stale).

| Name | Q-5 | Q-4 | Q-3 | Q-2 | Q-1 | LQ |
|---|---|---|---|---|---|---|
| CEG | 25Q1 6.79 | 25Q2 6.10 | 25Q3 6.57 | 25Q4* 6.07 | 26Q1 11.12 | 26Q2 7.50 |
| VST | 25Q1 3.93 | 25Q2 4.25 | 25Q3 4.97 | 25Q4* 4.58 | 26Q1 5.64 | 26Q2 4.02 |
| NRG | 25Q1 8.59 | 25Q2 6.74 | 25Q3 7.63 | 25Q4* 7.75 | 26Q1 10.26 | 26Q2 7.48 |
| GEV | 25Q1 8.03 | 25Q2 9.11 | 25Q3 9.97 | 25Q4* 10.96 | 26Q1 9.34 | 26Q2 11.10 |
| ETN | 25Q1 6.38 | 25Q2 7.03 | 25Q3 6.99 | 25Q4* 7.05 | 26Q1 7.45 | 26Q2 8.53 |
| PPL | 24Q4* 2.21 | 25Q1 2.50 | 25Q2 2.02 | 25Q3 2.24 | 25Q4* 2.27 | 26Q1 2.77 |
| SO | 24Q4* 6.34 | 25Q1 7.78 | 25Q2 6.97 | 25Q3 7.82 | 25Q4* 6.98 | 26Q1 8.40 |
| AEP | 24Q4* 4.70 | 25Q1 5.46 | 25Q2 5.09 | 25Q3 6.01 | 25Q4* 5.32 | 26Q1 6.02 |
| VRT | 25Q1 2.04 | 25Q2 2.64 | 25Q3 2.68 | 25Q4* 2.88 | 26Q1 2.65 | 26Q2 3.27 |

Reads [DERIVED]: CEG's 26Q1 step-up ($11.12B vs $6.79B yr-ago) is Calpine
consolidation, not organic -- strip it and the underlying run-rate is closer
to +23% on like-for-like quarters (the 26Q2 +23.0% YoY is post-consolidation
and cleaner). VST's LQ decline (-5.5%) is the only revenue contraction in the
set; GEV/VRT/ETN compound >21% into their backlogs. Utility lines grow a
steady 8-11% (rate-base cadence), exactly the low-beta profile Section 13's
regressions assign them.

### 11.19 Source coverage ledger (what was read per name)

xbrl pts = usable rows in <T>-xbrl.json after latest-filed dedupe; ENT lines =
entity-note line count at read time; wave = analysis file named in the
entity's Data layers block (rating/confidence); annex = benchmark profile +
data annex pair under wiki/investing/benchmarks/.

| T | xbrl pts | ENT lines | Wave file (rating/conf) | Annex |
|---|---|---|---|---|
| CEG | 64 | 63 | waveE-ceg-analysis (HOLD/66) | yes |
| VST | 70 | 75 | waveE-vst-analysis (HOLD/55) | yes |
| TLN | 77 | 66 | waveE-tln-analysis (HOLD/62) | yes |
| NRG | 84 | 61 | none -- entity only | yes |
| GEV | 36 | 93 | waveE-gev-analysis (HOLD/45) | yes |
| ETN | 78 | 79 | waveE-etn-analysis (BUY/62) | yes |
| HUBB | 12 | 57 | none -- entity only | yes |
| VRT | 78 | 76 | waveE-vrt-analysis (HOLD/66) | yes |
| FLNC | 60 | 72 | waveU-FLNC-analysis (SELL/55) | yes |
| BE | 12 | 127 | waveU-BE-analysis (HOLD/50) | yes |
| AEP | 71 | 72 | waveU-AEP-analysis (HOLD/45) | yes |
| DUK | 61 | 70 | waveU-DUK-analysis (HOLD/45) | yes |
| PPL | 72 | 70 | waveU-PPL-analysis (HOLD/45) | yes |
| SO | 48 | 70 | waveU-SO-analysis (HOLD/45) | yes |
| NEE | 36 | 71 | waveE-nee-analysis (HOLD/45) | yes |
| BWXT | 76 | 72 | waveE-bwxt-analysis (HOLD/55) | yes |

## 12. Nuclear premium quantified (CEG/TLN/NRG/VST vs AEP/DUK/PPL/SO)

All returns price-to-price from factor-store bars, anchor close 2026-08-24.
NUKE = equal-weight CEG/VST/TLN/NRG (EW index rebased 2023-06-02, common TLN
history); UTIL = equal-weight AEP/DUK/PPL/SO (EW index from 2021-08-24).
Spread = NUKE minus UTIL in percentage points. TECH[DERIVED].

### 12.1 Single-name horizon returns (%)

| Name | 1m | 3m | 6m | 1y |
|---|---|---|---|---|
| CEG | -0.8 | -7.5 | -7.1 | -12.6 |
| VST | -16.5 | -12.6 | -18.5 | -28.0 |
| TLN | -14.8 | -17.6 | -16.6 | -14.3 |
| NRG | -20.7 | -18.8 | -36.5 | -22.7 |
| AEP | -10.1 | -7.4 | -7.1 | +10.2 |
| DUK | -6.5 | -2.8 | -3.6 | +0.9 |
| PPL | -4.0 | -3.5 | -5.2 | -2.3 |
| SO | -6.9 | -4.3 | -4.1 | -2.0 |
| SPY | +3.5 | +2.9 | +12.7 | +21.7 |

### 12.2 Cohort spread table (pp)

| Horizon | NUKE EW | UTIL EW | Spread | Verdict |
|---|---|---|---|---|
| 1m | -14.5% | -7.0% | -7.5pp | premium INVERTED |
| 3m | -14.8% | -4.7% | -10.1pp | inverted, widening |
| 6m | -20.5% | -5.8% | -14.7pp | inverted, widest |
| 1y | -20.2% | +3.3% | -23.5pp | deeply inverted |

Per-name spreads (name minus UTIL-EW, pp): 1m: CEG +6.2 / TLN -7.8 / VST -9.5
/ NRG -13.7. 3m: CEG -2.8 / TLN -12.9 / VST -7.9 / NRG -14.1. 6m: CEG -1.3 /
TLN -10.8 / VST -12.7 / NRG -30.7. 1y: CEG -15.9 / TLN -17.6 / VST -31.3 /
NRG -26.0.

### 12.3 Read-through [DERIVED]

- The "nuclear premium" has flipped sign in price space: owning contracted
  nuclear cash flows cost you 7.5pp (1m) to 23.5pp (1y) versus plain regulated
  wires over every measured horizon. Combined with S1.2 (contract economics
  still clearing $70-120/MWh vs $30-50 wholesale prints), this is a multiple
  reset, not a fundamental break -- the contracts did not reprice down, the
  equities did.
- Within NUKE the hierarchy preserved quality order: CEG (largest fleet,
  Calpine diversification) fell least at 3-6m; NRG (no signed hyperscaler
  mega-PPA) fell most; VST worst at 1y (-31.3pp vs UTIL) as leverage met the
  de-rate.
- UTIL side context: even the wires gained almost nothing absolute (1y UTIL
  +3.3% vs SPY +21.7%) -- the whole complex lagged the index; the spread
  measures relative pain inside a lagging sector, not absolute strength.
- Mean-reversion setup framing (not a forecast): the 1y spread sits ~2 sigma
  outside its trailing relationship given unchanged contract books; the
  falsifier is contract-book damage (PJM auction resets, Fifth Circuit ruling
  against co-location, AWS/Meta/MSFT renegotiation headlines), not further
  multiple drift.

### 12.4 Monthly cohort path, Jul-2025..Aug-2026 (EW index month-end returns, %)

| Month | NUKE | UTIL | Spread (pp) |
|---|---|---|---|
| 2025-07 | +12.9 | +5.0 | +7.9 |
| 2025-08 | -7.3 | +0.2 | -7.5 |
| 2025-09 | +8.5 | +2.0 | +6.5 |
| 2025-10 | 0.0 | +1.1 | -1.1 |
| 2025-11 | -2.7 | +0.7 | -3.4 |
| 2025-12 | -6.2 | -5.2 | -1.0 |
| 2026-01 | -7.3 | +3.3 | -10.6 |
| 2026-02 | +11.5 | +9.8 | +1.7 |
| 2026-03 | -15.0 | -1.1 | -13.9 |
| 2026-04 | +10.2 | +0.6 | +9.6 |
| 2026-05 | -2.4 | -5.3 | +2.9 |
| 2026-06 | -0.8 | +4.8 | -5.6 |
| 2026-07 | -7.7 | -3.1 | -4.6 |
| 2026-08 | -8.2 | -3.3 | -4.9 |

Path read [DERIVED]: the premium was still POSITIVE as recently as Sep-2025
(+6.5pp); the regime flipped in Nov-2025-Jan-2026 and only Feb/Apr/May 2026
printed spreads in NUKE's favor. Seven of the last eight months carried a
negative spread -- this is an established trend, not a one-month air pocket.
The two worst NUKE months (-15.0% Mar-26, -8.2% Aug-26) bracket the wave-E/W
review window; both were contract-book-intact de-rates (WAVE).

### 12.5 Spread falsifiers and re-closing conditions [DERIVED]

The inverted premium (S12.2-S12.4) is a positioning fact, not a law. It closes
on any of:

- Contract-book validation events: Crane restart milestone hit on schedule
  (2028 gate), VST Meta PPAs reaching first delivery (Q4-27 window), TLN
  2029 ramp step confirmed -- each converts feared renegotiation into cash.
- Legal clarity: Fifth Circuit co-location ruling upheld for co-location (or
  FERC framework settles), removing the discount applied to TLN/PPL complex.
- Multiple mean-reversion without news: NUKE basket trading below ~10x
  forward EBITDA-type multiples on intact $70-120/MWh contract economics is
  historically a re-rating zone (corpus precedent: the 2024 pre-PPA base).
- Re-opening risk (spread widens further): PJM capacity auction reset capping
  merchant revenue share, AWS/Meta/MSFT renegotiation headlines, ERCOT market
  redesign penalizing firm capacity (NRG/VST specific), Calpine integration
  slippage (CEG).

## 13. Data center power demand chain (capex -> construction -> MW -> suppliers)

Corpus-stated figures; grades carried from source notes. No network sources.

### 13.0 Chain map (text form)

```
[HYPERSCALER CAPEX BUDGETS]
 MSFT CY26 ~$190B calendar (raised from $154.6B on 4/30; Q4 cash capex >$40B
   guided; finance-lease additions +$23.7B TTM on top)
 AMZN FY26 ~$200B guided (Jassy Feb-5 call; 2025 actual $131.8B)
 META FY26 $125-145B guide quoted verbatim in 10-Q Liquidity; raised >$10B to
   ~$136.7B mid-year; capex/revenue heading to hyperscaler-highest intensity
 GOOGL FY26 $195-205B (third raise; Q2 FCF -$5.9B first ever)
 => Big-4 observable budget ~$700-730B CY26; entity-note aggregate "$750B
    (+67% YoY)" consistent [ENT[BE]]
      |
      v
[DC CONSTRUCTION PIPELINE]
 32 GW US data-center capacity under construction; 70% AI-dedicated; 228 GW
   effective backlog at 2025 build rate ~= 12 years of work queued
   [ref-ai-power-grid-deep-dive, HIGH]
      |
      v
[MW DEMAND ON THE GRID]  (binding constraint moves here)
 PJM: AEP-Ohio + AEP-Indiana queues dominate (AEP $54B 2026-30 plan)
 PA: Susquehanna co-location precedent (PPL footprint; TLN-AWS 1,920 MW)
 TX: ERCOT co-location pipeline (NRG positioned; VST Comanche Peak AWS PPA)
 Southeast: Carolinas (DUK $73B plan) + Florida (NEE/FPL, SO Atlanta)
 Behind-the-fence alternatives when queues bind: BE fuel cells (Oracle 2.8 GW
   MSA), FLNC BESS peak-shave, VRT on-site power train
      |
      v
[SUPPLIER LAYERS]
 Grid delivery (rate base): AEP PPL DUK SO NEE  -- vol 12-19%, beta-to-rates
   mildly negative (S13)
 Electrons' hardware (backlog): GEV $163.3B total backlog / 110 GW gas slots;
   ETN $22.8B, 68% shippable <12m; HUBB transformers/meters (rate-base)
 Site power + heat: VRT $15.0B backlog, b2b 2.9x, liquid cooling forced by
   ~120 kW racks; ETN counters via Boyd Thermal $9.55B
 Firming/bridge: FLNC BESS ($3B+ backlog), BE fuel cells (Nebius $2.6B,
   Brookfield $5B), then post-2030 SMR layer (BWXT components now)
```

### 13.1 Supplier-layer exposure map (corpus figures per name)

| Layer | Names | Corpus anchor | 2026 status |
|---|---|---|---|
| Turbine / slots | GEV | $163.3B backlog; gas slots 83 -> 100 GW Q1-26, 110 GW YE-26 target | sold out years deep |
| Electrical hardware | ETN, HUBB | ETN $22.8B book, 68% <12m; HUBB Utility Solutions rate-base | ETN converts fast; HUBB rides utility capex |
| Site power train + cooling | VRT (+ETN via Boyd) | VRT backlog $15.0B +109%, b2b ~2.9x; air caps ~30-40 kW/rack vs ~120 kW GB200 racks | liquid-cooling transition forced |
| Bridge / on-site power | BE, FLNC | BE Oracle 2.8 GW MSA + Nebius $2.6B; FLNC $3B+ BESS backlog | called when queues bind |
| Contracted firm energy | CEG, VST, TLN, NRG | S1.1 PPAs: MSFT 837 MW, AWS 1.2+1.92 GW, Meta 2.6 GW | premium intact, equities de-rated (S12) |
| Wire delivery (rate base) | AEP, PPL, DUK, SO, NEE | AEP $54B / DUK $73B / PPL $14B+ plans | 5-7 yr queues = moat and bottleneck |
| Post-2030 nuclear layer | BWXT (+SO execution) | BWXT ~$100M/reactor BWRX-300 content; Pele 2026 | paid on components today |

### 13.2 Layer economics and pass-through [DERIVED]

- Budget layer: hyperscalers are spending 40-60% of operating cash flow on
  capex (MSFT capex-paid framing; GOOGL first-ever negative Q2 FCF; AMZN CFO
  $148.5B vs capex ~$151B). Demand signal is real but FCF-constrained -- two
  independent kill-switches live in the waves: >=2 hyperscalers guiding capex
  down sequentially (currently 0-of-3), or MSFT FY27 capex <$210B (bull leg).
- Construction layer: 228 GW backlog at ~32 GW/yr pace = multi-decade
  visibility for whoever holds slots/backlog (GEV gas slots to 110 GW, ETN
  68%-within-12-months book). Equipment makers hold pricing power until
  queues clear (S2 synthesis, unchanged).
- MW layer: interconnection queues 5-7 years make delivered-MW timing the
  scarce input, which is precisely why behind-the-meter contracts cleared at
  $70-120/MWh (S1.2) and why bridge power (BE) and storage (FLNC) get
  called before new wires do.
- Supplier layer margin map: GEV 23.0% TTM net margin (flattered by FY26 Q4d
  one-offs), ETN 12.7%, VRT 14.0%, SO 14.5%, PPL 13.1%, NRG 2.6% -- the
  margin pool sits in equipment and site infrastructure, not in merchant
  generation ex-contracts.
- Single-point-of-failure watch items along the chain: MSFT FY27 capex
  verification (wave1-msft kill criteria), META OM <38% repeat (FM1 verdict
  at Q3 print), AMZN FY26 guide <~$180B, Fifth Circuit co-location ruling
  (TLN/PPL), PJM capacity auction resets (CEG/VST).

### 13.3 Demand-side kill dashboard (from wave kill criteria)

Aggregated tripwires already codified in the hyperscaler waves; if two fire
inside a quarter, the S13 supplier-layer backlog thesis is impaired:

1. >=2 of MSFT/META/AMZN guiding capex DOWN sequentially (wave2-amzn theme-alpha
   trigger; currently 0-of-3).
2. AMZN FY26 capex guide revised below ~$180B without an explicit offset
   (wave2-amzn).
3. MSFT FY27/CY27 capex verified <= $210B (bull leg) vs >= $230B (kill leg);
   transcript verification unfinished (wave1-msft).
4. META FY26 guide raised above $145B, or FY27 initial guide implying
   capex/revenue > 70% -- note this kills the EQUITY first, demand signal
   stays intact near-term (wave2-meta FM1).
5. GOOGL FY27 capex commitment withdrawn (wave2-googl).
6. Compute-side corroboration: TSM/NVDA/AMD order books rolling over would
   hit the construction layer 6-12 months later ([[ref-semiconductor-value-chain]] linkage).

## 14. Rate sensitivity matrix (DGS10 regression, regenerated)

METHOD (supersedes Section 3 numbers where they differ): weekly window
Sep-2024 through Aug-2026 (102 weekly DGS10 changes, 101 paired obs per name
after alignment). Each stock's 5-bar return ending at the week date is
regressed on the concurrent week-over-week change in FRED DGS10 from the
factor store (MACRO ticker, factor DGS10, ends 2026-08-20). beta/100bp =
modeled % price change for a +1.0pt yield move, all else equal. Regenerated
2026-08-24 per the header instruction; correlations modest -- treat as a
sensitivity ORDERING, not precise multipliers. Offset check: shifting the
return window +/-1 week flips small-correlation signs (e.g. DUK concurrent
-722.7/+116.2 fwd), so only |corr| >= 0.15 rows should be treated as stable.

DGS10 path context: early-Sep-2024 ~3.77% -> 4.69% (2026-08-20); window range
3.63-4.79%; 2025 average 4.29%; trailing-1y avg 4.29%. Yields ROSE ~90bp over
the regression window -- negative betas mean yields were a headwind that
load-growth narratives partially absorbed.

### 14.1 Matrix (sorted by beta, most negative first)

| Name | beta per +100bp | corr | n | interpretation |
|---|---|---|---|---|
| AEP | -74.9% | -0.31 | 101 | strongest duration sensitivity of the set |
| DUK | -72.3% | -0.35 | 101 | classic bond proxy, strongest corr |
| PPL | -59.1% | -0.26 | 101 | bond proxy |
| SO | -36.3% | -0.18 | 101 | mild duration |
| NEE | -37.0% | -0.12 | 101 | mild, less stable corr |
| TLN | -105.7% | -0.14 | 101 | unstable sign (offset-flip) -- ignore level, note direction |
| NRG | -34.6% | -0.05 | 101 | unstable sign -- treat as ~zero |
| VST | +18.0% | +0.02 | 101 | decoupled from rates |
| BE | +17.2% | +0.01 | 101 | decoupled |
| HUBB | +1.4% | 0.00 | 101 | zero sensitivity |
| CEG | +64.3% | +0.09 | 101 | weak positive -- equity-vol dominated |
| VRT | +46.3% | +0.06 | 101 | weak positive |
| ETN | +32.2% | +0.08 | 101 | weak positive |
| BWXT | +52.2% | +0.10 | 101 | weak positive |
| GEV | +76.5% | +0.12 | 101 | trades like high-beta industrial, not utility |
| FLNC | +149.3% | +0.10 | 101 | unstable magnitude (low corr) |

Cohort-level betas (equal-weight indices): NUKE-IPPs -192.6%/100bp (r -0.03),
UTILS-5 -581.5%/100bp (r -0.30), EQUIP-3 +509.8%/100bp (r +0.10), DC-PWR-4
+494.1%/100bp (r +0.07), SPY +145.6%/100bp (r +0.07).

### 14.2 Beta stability: two sub-windows (yr1 = Sep-24..Aug-25, yr2 = Sep-25..Aug-26)

Sign of beta/100bp by window (%/100bp shown):

| Name | yr1 | yr2 | Sign-stable? |
|---|---|---|---|
| AEP | -570 | -1428 | YES (both negative, corr -0.37 both) |
| DUK | -721 | -847 | YES (-0.45 / -0.29) |
| PPL | -344 | -1347 | YES (-0.20 / -0.40) |
| SO | -281 | -626 | YES (-0.20 / -0.21) |
| NEE | -306 | -659 | YES (-0.11 / -0.19) |
| HUBB | +578 | -1538 | no (flip) |
| CEG | +2199 | -3559 | no (sign flip, yr1 driven by one big yield-drop week) |
| VST | +1371 | -3025 | no (flip) |
| TLN | +107 | -4072 | no |
| NRG | +345 | -2156 | no |
| GEV | +1131 | -536 | partial (positive yr1, weakly negative yr2) |
| ETN | +905 | -1254 | no (flip) |
| BWXT | +962 | -616 | partial |
| BE | +723 | -1196 | no (low |corr| throughout) |
| VRT | +1346 | -2206 | no (flip) |
| FLNC | +1290 | +1833 | YES-positive (but corr < 0.15 both windows) |

Stability read [DERIVED]: the five regulated wires are negative-to-yields in
BOTH sub-windows with consistent correlations -- that is the only robust rate
signal in the complex. Every growth-layer name flipped sign between windows,
confirming their full-window betas are regime artifacts, not exposures. The
full-window positive equipment-cohort beta (+510%/100bp) should therefore be
read as "rode a rising-yield, rising-narrative regime," NOT as structural
yield benefit.

### 14.3 Scenario grid (modeled % move, full-window beta x yield shock)

| Name / basket | +50bp | +100bp | +200bp |
|---|---|---|---|
| AEP | -37.4% | -74.9% | -149.7% |
| DUK | -36.1% | -72.3% | -144.5% |
| PPL | -29.5% | -59.1% | -118.2% |
| SO | -18.2% | -36.3% | -72.6% |
| NEE | -18.5% | -37.0% | -74.0% |
| UTILS-5 EW basket | -290.8%* | -581.5%* | -1163.0%* |
| NUKE-IPP EW basket | -96.3%* | -192.6%* | -385.2%* |
| EQUIP-3 EW basket | +255.0%* | +509.8%* | +1019.5%* |
| DC-PWR-4 EW basket | +247.0%* | +494.1%* | +988.2%* |

(* basket figures are the regression output on the equal-weight INDEX itself,
not averages of member betas; they represent the modeled index move, useful
for pair sizing -- e.g. long-wires/short-equipment duration hedge ratio is
roughly 1:1 notional on these betas.)

Largest observed weekly DGS10 move in-window: +47bp (next largest +26bp), so
the +100bp column has NO in-window precedent -- treat it as stress arithmetic
on an ordering, exactly as the header warns.

### 14.4 Reading the matrix [DERIVED]

- Sign pattern confirmed and sharpened vs S3: regulated wires carry ALL the
  negative-rate sensitivity (UTILS-5 -581%/100bp as a basket) while the
  equipment/DC-supply layer trades POSITIVE to yields (+494 to +510%/100bp) --
  the complex now spans both sides of the duration trade, so it internally
  hedges only if you pair the layers deliberately.
- The AI-load story has NOT fully broken wire-duration: AEP/DUK/PPL show the
  strongest stable negative betas of the 16 (corr -0.26 to -0.35), contrary
  to S3's near-zero reading. Reconciliation: S3 used a different pairing
  convention; under both conventions the ORDERING (DUK/SO most bond-like)
  survives, but the magnitudes here are the regenerated ones.
- Duration re-arm scenario quantified: a +100bp fast backup hits the UTIL
  basket ~-5.8% modeled (beta-weighted), roughly twice any single IPP's
  modeled hit; >150bp would push wire drawdowns toward the -8 to -11% zone
  the cohort just printed on idiosyncratic flows. Watch DGS10 gaps >50bp/wk
  as the tripwire (window max weekly move +47bp).
- Positive-beta names (GEV/BWXT/VRT/ETN/CEG) behave as yield-CURVE-steepening
  beneficiaries / growth proxies: rising yields accompanied their demand
  narrative (nominal growth) rather than discounting it -- they are not rate
  hedges within the complex.
- Caveats: 101 weekly observations, one macro regime (yields 3.6-4.8%), no
  rate-cut episode in-window; betas will re-estimate materially when a cut
  cycle enters the sample. Regenerate after every factor-store refresh.

### 14.5 Method notes and regeneration

- Series: factors.db MACRO/DGS10 weekly last-print; stock side bars[t] daily
  closes through 2026-08-24. Pairing rule: week-date must exist verbatim in
  the stock's date index; return window is the 5 TRADING bars ending at that
  index position. Names whose week-date is absent (holidays) drop that obs --
  hence n=101 not 102.
- Reproduction snippet (sqlite3 + stdlib): pull `SELECT date,value FROM
  factors WHERE factor='DGS10'`, bucket by ISO week keeping the latest print,
  difference consecutive weeks inside 2024-09-01..2026-08-31, then OLS of
  5-bar % returns on those deltas. Cohort betas: rebase each member to 1.0
  at cohort start, average daily, regress the index series identically.
- Regeneration triggers: any factor-store ingest-bars run (weekly calibration
  job), any new 10-Q/10-K xbrl pull, or a DGS10 print beyond the 3.63-4.79%
  window band (invalidates out-of-window stress claims).
- Known limitations: single macro regime (no cut cycle in sample); weekly
  granularity misses intraweek yield shocks; beta instability documented in
  S14.2 means only wire-cohort sign should be quoted in prose.

## 15. Expansion data gaps

- No wave analyses exist for NRG and HUBB; both profiles rest on entity notes
  only (S11.4, S11.7). First-baseline kernels recommended via /invest.
- BE and HUBB xbrl jsons carry no revenue points (S11.10, S11.7) -- their FIN
  columns are n/a by construction until an edgar-scraper re-pull widens
  concept coverage.
- Corrupt/gapped series blocking TTMs: TLN and FLNC FY 10-K revenue rows
  (negative FY values), BWXT quarter gap (Revenue span 455 days), AEP NI hole
  (latest row 2024Q3). Re-pull candidates for tools/edgar-scraper.py.
- Stale corpora never to quote: NEE revenue (2013Q3 label), DUK revenue
  (2018Q1 label), BWXT LTD ($300M @2015). NI/balance-sheet rows are current;
  revenue lines are not (S11.12, S11.15).
- GEV cash/LTD and SO LTD absent from xbrl jsons despite current flow rows.
- Rate matrix: no Fed-cut regime in sample (S14.5); re-estimate after the
  next factor-store refresh regardless.
