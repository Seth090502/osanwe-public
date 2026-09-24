---
categories: [sources]
type: reference
target_path: Atlas/sources/investing/ref-ai-power-grid-deep-dive.md
created: 2026-05-06
updated: 2026-05-06
status: active
confidence: high
tags:
  - topic/ai-power-demand
  - topic/datacenter-power
  - topic/grid-infrastructure
  - topic/nuclear-restart
  - topic/small-modular-reactors
  - topic/independent-power-producers
  - topic/gas-peaker-economics
  - topic/transformer-shortage
  - topic/interconnect-queue
  - topic/utility-scale-renewables
  - topic/ppa-structure
  - topic/ferc-regulatory
  - topic/theme-gamma-thesis
  - topic/bess-storage
  - topic/geothermal-baseload
  - ticker/VST
  - ticker/CEG
  - ticker/TLN
  - ticker/NRG
  - ticker/D
  - ticker/AEP
  - ticker/SO
  - ticker/DUK
  - ticker/NEE
  - ticker/EXC
  - ticker/PPL
  - ticker/SRE
  - ticker/FE
  - ticker/ETR
  - ticker/PSEG
  - ticker/ES
  - ticker/XEL
  - ticker/WEC
  - ticker/EIX
  - ticker/PCG
  - ticker/OGE
  - ticker/BWXT
  - ticker/SMR
  - ticker/OKLO
  - ticker/NNE
  - ticker/GEV
  - ticker/ETN
  - ticker/ABB
  - ticker/HUBB
  - ticker/POWL
  - ticker/CAT
  - ticker/CMI
  - ticker/GNRC
  - ticker/FLNC
  - ticker/STEM
  - ticker/ORA
  - ticker/AES
  - ticker/BEPC
  - ticker/CWEN
  - ticker/PWR
  - ticker/MTZ
  - ticker/PRIM
  - ticker/DTCR
  - ticker/VOLT
  - thesis/theme-gamma
  - thesis/theme-alpha
aliases:
  - ai power supply chain
  - ai power grid enumeration
  - ai power grid deep dive
  - theme-gamma supply-side
related:
  - "investing-moc"
  - "thesis-theme-gamma"
  - "thesis-theme-alpha"
  - "[[ref-theme-alpha]]"
  - "ref-ai-supply-chain-deep-dive"
  - "ref-portfolio-doctrine"
  - "[[ref-macro-landscape]]"
  - "ref-sector-benchmarks"
  - "[[ref-investor-frameworks-2026]]"
  - "VST"
  - "CEG"
  - "TLN"
  - "BWXT"
  - "SMR"
  - "OKLO"
  - "GEV"
  - "ETN"
  - "ABB"
  - "HUBB"
  - "DTCR"
  - "VOLT"
  - "Hitachi-Energy"
  - "Siemens-Energy"
  - "AEP"
  - "NRG"
  - "NEE"
  - "DUK"
  - "SO"
  - "PPL"
  - "FLNC"
  - "[[ref-ai-power-grid-deep-dive-ingest-2026-05-06]]"
---

# AI Power + Grid Infrastructure -- Exhaustive Company Enumeration

Cross-reference: this is the SUPPLY-SIDE companion to ref-ai-supply-chain-deep-dive (DEMAND-side compute / silicon / networking / cooling / REITs / neoclouds). Together the two refs map the full AI value chain from electrons to inference. This document enumerates every meaningful public utility, IPP, nuclear operator, SMR developer, gas-peaker OEM, transformer/grid-equipment vendor, BESS pure-play, geothermal/emerging-baseload company, and ISO/RTO market participant relevant to AI datacenter power buildout. Scope spans 22 layers from hyperscaler demand profile through emerging displacers + bottlenecks. Every public company carries ticker; private companies with >$200M cumulative funding receive structured H3s.

## 1. Hyperscaler power demand profile

The seven hyperscalers driving AI power demand collectively contracted >70 GW of new generation between 2024 and Q1-2026. The IEA Electricity 2026 forecast pegs global datacenter electricity demand at 945 TWh by 2030; EPRI Powering Intelligence 2026 and DOE-LBNL 2024 place US datacenter share at 9-17% of US load by 2030. Hyperscaler 2026 capex is operator-confirmed at $725B (+77% YoY) per supply-chain ref. The binding constraint is electrons + grid, not silicon.

### MSFT power profile
#### Position in chain
Microsoft is the largest single corporate power offtaker globally; it has signed the world's largest single PPA (Brookfield 10.5 GW) and the most prominent nuclear restart PPA (CEG Crane 835 MW). Its strategy emphasizes 24/7 carbon-free matching by 2030.
#### Financial signals
- MSFT: total contracted renewable energy 40 GW across 26 countries 2026-02 (per Microsoft Carbon Negative blog 2026-02-18)
- MSFT: 19 GW renewable online of 40 GW contracted; balance over next 5yr (per Microsoft Carbon Negative blog 2026-02-18)
- MSFT: Brookfield framework 10.5 GW new renewables 2026-2030 US/EU; ~$10B investment (per Brookfield IR 2024-05-01)
- MSFT: CEG Crane Clean Energy Center 835 MW 20yr PPA TMI Unit 1 restart 2028 ~$16B contract value (per Constellation 8-K 2024-09-20)
- MSFT: 6 partners with >1 GW contracted each; 20+ partners with 5+ projects each (per Microsoft 2026-02-18)
#### Thesis Fit
Largest single demand counterparty for IPPs (CEG, BEPC) and renewables developers (NEE Energy Resources). Sets the price benchmark for nuclear PPAs (~$110-130/MWh range implied at TMI). Cross-ref: see ref-ai-supply-chain-deep-dive §1 for compute/Azure context.
#### Risks
2025 100% match goal achieved via offsets, not 24/7 physical matching; carbon-negative 2030 path requires CDR scale-up. Reported emissions rose 23.4% since 2020 baseline per 2025 Sustainability Report.
#### Catalysts
TMI Unit 1 NRC license renewal application; additional restart announcements (Duane Arnold rumored). FY27 Brookfield delivery cadence.
#### Recent
- 2026-02-18: Carbon Negative milestone; 40 GW contracted disclosure
- 2024-09-20: 20yr Crane PPA signed
- 2024-05-01: Brookfield 10.5 GW framework

### AWS power profile
#### Position in chain
AWS is the second-largest hyperscaler power buyer with a uniquely concentrated nuclear-via-PPA strategy after the FERC ruling rejected its Susquehanna behind-the-meter co-location. Pivoted to FOM (front-of-meter) PPAs.
#### Financial signals
- AWS: TLN Susquehanna 1.92 GW front-of-meter PPA through 2042; 840-1,200 MW by 2029 ramping to 1,680-1,920 MW by 2032; ~$18B life-of-contract revenue to Talen (per Talen IR 2025-06; Utility Dive 2025-06)
- AWS: VST Comanche Peak 1.2 GW 20yr PPA delivery start Q4-27 full capacity 2032 (per Vistra 8-K 2025-09-29)
- AWS: Entergy Mississippi $10B AWS data center investment Madison County (per Entergy IR 2024)
- AWS: $38B multi-year cloud deal with OpenAI 2025 (per DCD 2025)
#### Thesis Fit
TLN is the highest-purity AWS nuclear proxy. VST diversifies AWS exposure into ERCOT. Cross-ref: see ref-ai-supply-chain-deep-dive §1.
#### Risks
FERC continues reviewing co-location framework; Fifth Circuit appeal pending. Susquehanna full ramp depends on transmission upgrades.
#### Catalysts
FERC co-location final rule expected 2026; Comanche Peak first delivery Q4-27.
#### Recent
- 2025-09: VST Comanche Peak 1.2 GW PPA
- 2025-06: TLN Susquehanna FOM restructured PPA

### META power profile
#### Position in chain
Meta announced in January 2026 a 6.6 GW nuclear-track strategy with VST/Oklo/TerraPower as the signature pivot. Adds 300 MW geothermal (Sage + XGS) and supplements with PJM-zone gas via Entergy.
#### Financial signals
- META: VST 2,609 MW 20yr PPA across Perry/Davis-Besse/Beaver Valley nuclear plants, 433 MW from uprates (per Vistra 8-K 2026-01-09)
- META: Oklo 1.2 GW Aurora Pike County Ohio target online 2030, full 1.2 GW by 2034 (per Oklo IR 2026-01-09)
- META: Entergy 2 GW Richland Parish Louisiana data center; $10B investment; 3 new gas plants $3B (per Entergy CEO interview 2025)
- META: Sage Geosystems 150 MW geothermal first phase 2027 east-of-Rockies (per Sage IR 2024-08-26)
- META: XGS Energy + Sage combined 300 MW geothermal 2026 PPAs (per Utility Dive 2026)
#### Thesis Fit
Most diversified hyperscaler portfolio across nuclear restart (VST), advanced reactor (Oklo), gas (Entergy), geothermal (Sage/XGS). Highest narrative-shift potential.
#### Risks
Oklo NRC licensing 2026-29 critical path; Sage/XGS technology risk (first-of-kind EGS).
#### Catalysts
Oklo NRC custom COL acceptance; VST PJM PPAs start 2027.
#### Recent
- 2026-01-13: 6.6 GW nuclear announcement

### GOOGL power profile
#### Position in chain
Google has built the broadest small-reactor + geothermal portfolio: Kairos Hermes 2 (TVA), Fervo Cape Station Nevada, NextEra hub strategy, and a 6-7 site Stargate-rival via TPU-backed Anthropic compute.
#### Financial signals
- GOOGL: Kairos Power 500 MW 6-7 reactor commitment by 2035; first 50 MW TVA Hermes 2 PPA Oak Ridge online 2030 (per Kairos/TVA 2025-08-18)
- GOOGL: Fervo Energy 115 MW Nevada geothermal NV Energy data center PPA (per Fervo)
- GOOGL: $40B Texas data center investment through 2027; 36 GW AEP Texas large-load Q4-25 attributable (per Utility Dive 2026-02-12)
- GOOGL: Ormat 150 MW 15yr Nevada geothermal portfolio PPA new capacity 2028-2030 (per Ormat Q4-25 release 2026-02-26)
#### Thesis Fit
Highest-diversity power strategy with deepest advanced-tech tilt (Kairos, Fervo, Ormat). Cross-ref: ref-ai-supply-chain-deep-dive §1.
#### Risks
Kairos Hermes 2 first-of-a-kind 2030 schedule; Fervo Cape Station phase II execution.
#### Catalysts
Hermes 2 NRC construction milestone; Fervo Cape Station Phase I commercial operation Oct-2026.
#### Recent
- 2025-08-18: Kairos/TVA Hermes 2 PPA
- 2026: Ormat 150 MW Nevada PPA

### OpenAI power profile
#### Position in chain
Stargate is the largest AI infrastructure commitment in history at $500B / 10 GW by 2029. Oracle leads 4.5 GW; SoftBank 1.5 GW; flagship Abilene 1.2 GW operational mid-2026.
#### Financial signals
- OpenAI: Stargate $500B / 10 GW commitment over 4 years (per OpenAI 2025-01-21)
- OpenAI: 5 new sites Sept 2025 brings planned capacity to ~7 GW; $400B investment 3yr (per OpenAI 2025-09-23)
- OpenAI: Oracle 4.5 GW $300B+ 5yr partnership (per OpenAI 2025-07)
- OpenAI: JPMorgan $2.3B Abilene project loan May 2025 (per Wikipedia/news)
- OpenAI: Abilene Stargate I 1.2 GW; first GB200 racks delivered Jun-2025 (per OpenAI/IntuitionLabs)
#### Thesis Fit
Power buyer of last resort -- but no public equity. Indirect plays: ORCL (compute landlord), CRWV/Vantage (campus operators), Bloom Energy fuel cells, NRG/AEP power supply.
#### Risks
$500B financing not fully arranged; Bloomberg reported funding gap Aug-2025. SoftBank limited partner appetite uncertain.
#### Catalysts
Lordstown Ohio operations 2026; Wisconsin Vantage site disclosure.
#### Recent
- 2025-09-23: Five-site expansion to ~7 GW

### Anthropic power profile
Anthropic relies on Google Cloud TPU and AWS infrastructure with no direct PPAs disclosed. Reported 1 GW Google TPU commitment per ref-ai-supply-chain-deep-dive. Indirect counterparty to GOOGL/AMZN power deals.

### Apple power profile
Apple's ACDC datacenter strategy is narrower in scope; 100% renewable since 2018 but uses smaller-scale renewable PPAs. Less material to AI-power thesis than the top six.

### Oracle power profile
#### Position in chain
Oracle is both Stargate operator (4.5 GW) and a hyperscaler in its own right. Power procurement is the gating constraint.
#### Financial signals
- ORCL: $300B+ Stargate 5yr OpenAI deal (per OpenAI 2025-07)
- ORCL: $523B RPO backlog Q3-FY26 driven by AI cloud (per public reporting 2026)
- ORCL: 4.5 GW Stargate sites Texas/New Mexico/Midwest (per OpenAI 2025-09-23)
- ORCL: DTE Energy Michigan 1.4 GW data center approved (per DTE 8-K 2026)
#### Thesis Fit
Cross-ref: ref-ai-supply-chain-deep-dive §1 for compute backlog.

## 2. Independent Power Producers

The IPP tier captures the unregulated competitive-power layer that has captured the largest 2024-26 share of hyperscaler nuclear and gas PPAs. Vistra, Constellation, Talen are the "big three" nuclear-tilted; NRG, AES, BEPC, CWEN add gas and renewables breadth.

### VST
#### Position in chain
Largest US competitive nuclear+gas IPP post-Energy Harbor. PJM and ERCOT footprint with 6.4 GW nuclear + 5.5 GW Cogentrix gas pending.
#### Financial signals
- VST: 2026 Adjusted EBITDA guide $6.8-7.6B; Adjusted FCFbG $3.925-4.725B (per Vistra Q4-25 release 2026-02-26)
- VST: 2025 Adjusted EBITDA $5.912B; FCFbG ~$3.6B (per Vistra Q4-25 2026-02-26)
- VST: ~3,800 MW PPAs with AWS Comanche Peak + Meta PJM nuclear (per Vistra 8-K 2026)
- VST: Meta 2,609 MW 20yr PPA across Perry/Davis-Besse/Beaver Valley + 433 MW uprates (per PRNewswire 2026-01-09)
- VST: AWS Comanche Peak 1.2 GW 20yr PPA delivery Q4-27 to 2032; option +20yr extension (per Vistra 8-K 2025-09-29)
- VST: 2027 Ongoing Ops Adj EBITDA midpoint $7.4-7.8B excluding Cogentrix/Meta upside (per Q4-25 2026-02-26)
- VST: Cogentrix 5,500 MW gas portfolio acquisition pending (per Q4-25 2026-02-26)
#### Thesis Fit
Highest-purity AI-nuclear IPP with both PJM and ERCOT exposure. Hedged book + 2.3x leverage target by YE-27. Highly contracted nuclear portfolio with subsequent license renewal pathway extending operations into 2050s/2060s.
#### Risks
ERCOT system reliability issues Q3-25 caused PPA timing concerns (Jefferies). Comanche Peak licensing/uprate execution. Cogentrix close-out risk.
#### Catalysts
Up to additional 3.2 GW nuclear capacity opportunity at Beaver Valley/Comanche Peak per CEO Burke; ~200 MW Comanche uprate.
#### Recent
- 2026-02-26: Q4-25 record results; 2026 guide initiated
- 2026-01-09: Meta 2.6 GW PJM PPA
- 2025-09-29: Comanche Peak 1.2 GW PPA

### CEG
#### Position in chain
Largest US unregulated nuclear operator (~22 GW capacity). MSFT TMI restart and pursuing additional restarts/uprates.
#### Financial signals
- CEG: Crane Clean Energy Center 835 MW restart 2028 with 20yr MSFT PPA (per Constellation 2025 10-K filed 2026-02-24)
- CEG: TMI restart capex $1.6B; license renewal target 2054 (per DCD 2024-09)
- CEG: TVA + ENTRA1 Energy nonbinding MOU up to 6 GW NuScale SMR fleet (per NuScale Q4-25 2026-02-26)
- CEG: ~$16B life-of-contract MSFT PPA estimated value (per industry reports)
#### Thesis Fit
Highest-quality nuclear baseload counterparty for hyperscalers; pricing power on subsequent license renewals. Cross-ref: ref-ai-supply-chain-deep-dive §10 for thin-stub reference.
#### Risks
TMI 2028 restart schedule (transmission interconnection); subsequent renewal timing.
#### Catalysts
Additional restart announcements (Clinton uprates); SMR MOU progressing to LOI.
#### Recent
- 2026-02-24: 2025 10-K filing

### TLN
#### Position in chain
Pure-play unregulated nuclear (Susquehanna 2.5 GW) + gas peaker fleet. AWS counterparty for the largest single hyperscaler nuclear PPA in MW terms.
#### Financial signals
- TLN: AWS Susquehanna 1.92 GW front-of-meter PPA post-FERC ruling 2025; ~$18B life-of-contract revenue (per Talen IR 2025-06)
- TLN: Brandon Shores + H.A. Wagner RMR through May 2029 FERC-approved (per Talen 8-K 2025-05-08)
- TLN: 840-1,200 MW delivery 2029; 1,680-1,920 MW 2032 ramp (per Utility Dive 2025-06)
#### Thesis Fit
Most leveraged single-customer nuclear IPP. RMR settlement provides Maryland/Baltimore reliability bridge through 2029. Cross-ref: ref-ai-supply-chain-deep-dive §10 thin stub.
#### Risks
Single-customer (AWS) concentration. Fifth Circuit appeal pending re: prior co-location FERC ruling.
#### Catalysts
First Susquehanna delivery 2029; potential additional uprates.
#### Recent
- 2025-06: AWS FOM PPA restructure
- 2025-05-01: FERC RMR approval

### NRG
#### Position in chain
ERCOT/PJM gas + retail platform with 5.4 GW data-center pipeline via GE Vernova + Kiewit JV.
#### Financial signals
- NRG: 5.4 GW gas-fired CCGT pipeline through 2032 with GEV + Kiewit (per NRG 8-K 2025-Q4)
- NRG: 1.2 GW slot reservation GE 7HA turbines secured (per NRG)
- NRG: 445 MW data center contracted across ERCOT/PJM Q3-25 (per NRG Q3-25 earnings call)
- NRG: 19 GW LS Power gas-fired + DR acquisition; FERC approved (per Utility Dive Nov-2025)
- NRG: Letters of Intent with Menlo Equities + PowLan up to 6.5 GW data center development (per 8-K)
#### Thesis Fit
Cleanest "BYOG" (bring-your-own-generation) IPP play; highest leverage to ERCOT data-center load. Promote-to-entity: yes (eligible).
#### Risks
"Zero interest" CEO posture re: speculative capacity build = constrained unless customer signed. Texas Energy Fund capital allocation.
#### Catalysts
2026 first data-center new-build agreement disclosure expected per CEO Coben.

### AES
#### Position in chain
Global IPP with US renewable + Latin American gas. Heavy Google data center renewables PPA exposure.
#### Financial signals
- AES: ~16 GW renewable backlog 2025 (per AES IR)
- AES: Multi-year hyperscaler PPA pipeline with Google/Microsoft
Promote-to-entity: yes.

### BEPC (Brookfield Renewable)
#### Position in chain
World's largest renewables platform via Brookfield Asset Management; sole 10.5 GW MSFT framework counterparty.
#### Financial signals
- BEPC: MSFT 10.5 GW framework 2026-2030 ~$10B (per Brookfield IR 2024-05-01)
- BEPC: Duke Florida 19.7% acquisition $6B at 2.0x rate base (per Duke Energy 8-K 2025)
- BEPC: TNC partnership for V.C. Summer Westinghouse SMR development
- BEPC: ~30 GW operating + 200 GW pipeline globally
#### Thesis Fit
Highest-purity renewables MSFT-counterparty; hybrid public/private structure (BEPC C-corp / BEP LP). Promote-to-entity: yes.

### CWEN (Clearway Energy)
Yieldco renewable owner; 6 GW operating with steady DPS growth. Promote-to-entity: yes.

### ORA (Ormat)
#### Position in chain
Largest pure-play geothermal IPP globally; 1,340 MW operating.
#### Financial signals
- ORA: 2026 revenue guide $1,110-1,160M (+14.6% midpoint) (per Ormat Q4-25 2026-02-26)
- ORA: 2025 revenue $989.6M (+12.5% YoY); Adjusted EBITDA $582M (+5.7%) (per Q4-25)
- ORA: Google 150 MW 15yr Nevada portfolio PPA new capacity 2028-2030 (per Q4-25 2026-02-26)
- ORA: ~200 MW data-center PPAs at attractive prices (per Q4-25)
- ORA: 101 MW geothermal under development through 2027 across 9 projects
- ORA: 2.6-2.8 GW capacity target by 2028
#### Thesis Fit
Only pure-play public geothermal at scale; SLB strategic alliance accelerates EGS. Cross-ref: §11.
#### Catalysts
EGS pilot validation; additional data-center hyperscaler PPAs.

## 3. Regulated utilities

The regulated tier captures rate-base growth at the largest US utilities driven by data-center load. S&P projects $1.3T US utility capex 2026-30. Geographic concentration: Northern Virginia (D), Texas (AEP, ETR), Atlanta (SO), Carolinas (DUK), Florida (NEE FPL), Phoenix (PNW), Pacific NW (PCG, AVA), Mid-Atlantic (FE, EXC, PPL).

### D (Dominion)
- D: 5-yr capex plan $64.7B 2026-2030 ($54.8B Virginia, $7.6B SC) (per Dominion Q4-25 release 2026-02; Utility Dive 2026)
- D: 48.5 GW data center contracted Dec-2025; 26 GW substation engineering letters (per DCD 2026)
- D: 450+ data centers from 50+ customers; 82% investment-grade; 76% contracts ≥10yr (per Q4-25)
- D: 2 new 500kV transmission lines enabling 6 GW Eastern Loudoun additional capacity
Promote-to-entity: yes.

### AEP
- AEP: $78B 5yr capex plan 2026-2030 (raised from $72B) (per AEP Q1-26 2026-05-05)
- AEP: 63 GW contracted incremental load by 2030 (+7 GW Q1-26) (per Q1-26)
- AEP: Texas large-load pipeline 36 GW; ~50%+ hyperscaler in ERCOT (per Q4-25 2026-02-12)
- AEP: 7-9% operating EPS CAGR through 2030; >9% midpoint
- AEP: 2026 EPS guide $6.15-6.45 (per Q1-26)
- AEP: 190 GW interconnection queue (per Q1-26 transcript)
- AEP: SB Energy 10 GW Piketon Ohio campus announced (per Q1-26)
- AEP: $10B incremental opportunity beyond $78B plan
Promote-to-entity: yes.

### SO (Southern)
- SO: 5-yr capex $81B 2026-2030 (raised from $76B) (per Southern Q4-25 2026-02-20; Utility Dive)
- SO: 11 GW contracted large-load Q1-26 (10 GW Q4-25); 28 projects (per Utility Dive 2026-05-01)
- SO: 75 GW data-center pipeline interest
- SO: $20B Georgia AI data-center buildout proposal; 80% projected Georgia demand serves AI (per Southern DEF 14A 2026)
- SO: Q1-26 data center power +42% YoY; commercial sales +4.5% weather-adj
- SO: DOE $26.5B loan -- 5 GW new gas (per Utility Dive 2026)
- SO: 14.3 GW data-center withdrawn last quarter (per DEF 14A) -- explicit downside flag
- SO: 10% sales growth target through end of decade
Promote-to-entity: yes.

### DUK (Duke)
- DUK: 5-yr capex plan $103B (raised from $87B) 2026-2030; rate base $84B → $120B by 2030 (per Duke 2025 ARS)
- DUK: 4.5 GW data-center load secured ESAs incl. Microsoft + Amazon
- DUK: 14 GW capacity additions + 4.5 GW storage by 2031
- DUK: $30B+ economic-development pipeline; 29,000 jobs
- DUK: 2025 net income $4.96B (vs $4.52B 2024); 5-7% EPS CAGR through 2030
- DUK: $10B equity issuance 2027-2030 layered
- DUK: Brookfield 19.7% Duke FL acquisition $6B at 2.0x rate base 2026 close
Promote-to-entity: yes.

### NEE
- NEE: Q1-26 adjusted EPS $1.09 (+10% YoY); 2026 guide $3.92-4.02 high-end target (per NEE Q1-26 2026-04-23)
- NEE: NEE Resources 33 GW renewables + storage backlog (+4 GW Q1-26; +1.3 GW BESS) (per Q1-26)
- NEE: FPL $90-100B capex through 2032; 12 GW advanced large-load discussions (per Q1-26)
- NEE: US-Japan 9.5 GW gas-fired generation Commerce mandate (capital-light)
- NEE: 110 GW battery storage pipeline; 76.6-107.6 GW total dev 2026-2032
- NEE: 30% backlog hyperscaler / 70% utility cooperative (per Q1-26 transcript)
- NEE: 8%+ adj EPS CAGR through 2032
Promote-to-entity: yes.

### EXC (Exelon)
- EXC: Maryland/PJM data-center pipeline; transmission-heavy capex post-Constellation spin
- EXC: PJM RTEP exposure
Promote-to-entity: yes.

### PPL
- PPL: 5-yr capex $23B (raised 15%) (per Utility Dive 2026-02-23)
- PPL: PPL-Blackstone JV (51/49) gas CCGT for data centers; PA service territory data-center interest >60 GW; 13 GW advanced; 6 GW PPL-EU shortfall expected (per PPL/Blackstone 2025-07-15)
- PPL: Blackstone $25B PA data-center infrastructure commitment (per POWER 2025-07)
- PPL: Alternative generation 2028-29 timeframe vs CCGT 2031-32
Promote-to-entity: yes.

### SRE (Sempra)
- SRE: California + Texas footprint via Oncor; Texas SB 6 implementation Dec-2026
- SRE: ERCOT 765 kV backbone Oncor Longshore-Drill Hole 180-mi line (Dec-2028 energization)
Promote-to-entity: yes.

### FE (FirstEnergy)
- FE: 5-yr capex $36B 2026-2030 (raised 30%) (per FE Q1-26 2026-04-28)
- FE: $19B transmission segment (+35%)
- FE: 2035 contracted data-center demand 4.3 GW (+47% YoY); pipeline 14.9 GW (+15% since Feb 2026)
- FE: Ohio 7 GW total 2035 (900 MW contracted); MD 5.4 GW 2035 (1.5 GW contracted)
- FE: 6-8% EPS CAGR through 2029
- FE: Energize365 program $28B
Promote-to-entity: yes.

### ETR (Entergy)
- ETR: AWS Madison County MS $10B + 2 additional campuses
- ETR: Meta Richland Parish 2 GW 24/7; 4M sqft Meta's largest ever; 3 new gas plants $3B
- ETR: $1.2B 100-mile 500kV transmission line for Meta load (Dec-2026 completion)
- ETR: $7B total customer savings 2024-25 across AR/LA/MS
Promote-to-entity: yes.

### PSEG, ES, XEL, WEC, EIX, PCG, OGE, CMS, ED, DTE
Each has material data-center pipeline exposure with regional concentration:
- PSEG: NJ data-center transmission play
- ES (Eversource): New England transmission backlog
- XEL: Iowa/MN data-center hub corridor
- WEC: Wisconsin Microsoft Mt Pleasant + Stargate Wisconsin
- EIX (Edison Intl): SoCal data center buildout
- PCG (PG&E): Bay Area + Central Valley AI campuses
- OGE: Oklahoma + AR data-center hub
- DTE Energy: Oracle 1.4 GW Michigan approved + Google 1 GW exec; ~5 GW additional pipeline; ~$5B incremental capex through 2032 (per DTE 8-K 2026-Q1)
- CMS: Michigan data-center transmission
- ED (Con Edison): NYC + Westchester
Promote-to-entity: yes (each).

## 4. Nuclear incumbents + restart pipeline

The US has ~94 GW operating nuclear; the AI demand cycle has triggered the first commercial restart pipeline since the 1979 TMI accident. Operating fleet captured by CEG (~22 GW), VST (~6.4 GW post-Energy Harbor), TLN (Susquehanna 2.5 GW), DUK + SO + ETR + Xcel + PSEG + various.

### Restart pipeline
- TMI Unit 1 / CEG / 835 MW / 2028 / MSFT 20yr (per Constellation 2024-09-20)
- Palisades / Holtec / 800-805 MW / Q1-2026 / Wolverine + Hoosier coops (per Holtec/DOE LPO 2024-09-30; Michigan Public 2025-12-17)
  - $1.52B DOE loan; $335M+ disbursed by Q3-25
  - First US restart of decommissioned reactor
- Duane Arnold / NextEra / 615 MW / 2028-29 target (rumored; not formally announced)
- Diablo Canyon / PG&E / 2.2 GW / extended through 2030 (state action)

### Vistra PJM nuclear (Perry, Davis-Besse, Beaver Valley)
2,176 MW operating + 433 MW uprates contracted to Meta. Subsequent license renewals into 2050s-2060s.

### Comanche Peak / VST
2.4 GW; AWS 1.2 GW PPA + ~200 MW uprate potential.

## 5. Small Modular Reactors

The SMR layer remains overwhelmingly pre-revenue with the exception of NuScale (NRC certified); customer LOIs and design approvals are the primary catalysts.

### NuScale (SMR)
#### Position in chain
First and only NRC-certified SMR design (50 MWe Jan-2023; 77 MWe SDA approved May-2025). VOYGR-12 924 MWe configuration.
#### Financial signals
- SMR: ENTRA1+TVA up to 6 GW SMR deployment MOU Tennessee Valley (per NuScale Q4-25 2026-02-26)
- SMR: RoPower Doiceşti Romania 462 MWe FEED Phase 2 complete; FID 2026 target operations 2030 (per Q4-25)
- SMR: KGHM Polska VOYGR-12 924 MWe by 2029 (Poland)
- SMR: Estonia Fermi Energia MOU 2031 deployment evaluation
- SMR: 77 MWe SDA approval ahead of original timeline
#### Thesis Fit
First-mover NRC certification advantage; international order book primary near-term revenue path. Cross-ref: ref-ai-supply-chain-deep-dive §10.
#### Risks
US first deployment customer commitment unresolved; commercial scale-up risk.

### Oklo (OKLO)
#### Position in chain
Aurora fast-spectrum microreactor (15-75 MWe scalable to 100+ MWe). Sells power directly via long-term agreements vs licensing tech.
#### Financial signals
- OKLO: Meta 1.2 GW Pike County Ohio agreement; pre-construction 2026, first phase 2030, full 2034 (per Oklo IR 2026-01-09)
- OKLO: NRC custom COL application first advanced reactor submission
- OKLO: DOE INL site use permit; Idaho National Lab fuel award
- OKLO: 700+ MWe non-binding indications of interest
#### Thesis Fit
Highest-narrative SMR equity post-Meta deal; lithium-cooled design differentiates from PWR-based peers. Cross-ref: ref-ai-supply-chain-deep-dive §10.
#### Risks
Pre-revenue; cash burn flagged; NRC custom COL review timeline.
#### Catalysts
NRC application acceptance review; additional hyperscaler LOI.

### BWXT
#### Position in chain
Nuclear fuel + components manufacturer; Project Pele DoD microreactor; supplier to GE Hitachi BWRX-300, Rolls-Royce SMR, TerraPower.
#### Financial signals
- BWXT: Project Pele 1.5 MW DoD microreactor; INL delivery 2026; testing through 2028 (per BWXT 2025-08; ANS Aug-2025)
- BWXT: BWRX-300 revenue per reactor estimate $100M; ~4-yr program per order (per Q2-25 transcript)
- BWXT: Rolls-Royce SMR steam generator design contract Q3-25 + manufacturing agreement
- BWXT: ~$300M Pele original cost contract
#### Thesis Fit
Picks-and-shovels nuclear-component play; broadest customer set across SMR designs. Cross-ref: ref-ai-supply-chain-deep-dive §10.

### NNE (NANO Nuclear)
Pre-revenue micro-reactor developer; primarily narrative trade. Promote-to-entity: yes.

### X-energy / TerraPower / Kairos / Westinghouse / Holtec / Last Energy (private)
- TerraPower: Natrium 345 MWe; Wyoming first deployment; $4B+ funded; Bill Gates-backed
- X-energy: Xe-100 80 MWe; Dow chemical Texas demo; Amazon $500M investment Oct-2024
- Kairos Power: Hermes 50 MW operations 2030; Google 500 MW LOI; Hermes 1 NRC construction May-2025
- Westinghouse AP300: 300 MWe LWR-derivative; TNC + Brookfield JV per Power-Eng 2026
- Holtec SMR-300: dual-unit 680 MWe at Palisades site; DOE Tier 1 First Mover $400M; CPA Part 1 NRC review by Dec-2026
- Last Energy: 20 MW micro; Texas + Eastern Europe pilots

## 6. Gas turbine + peaker OEMs

The gas turbine OEM tier captures the most-utilized AI-power equipment layer. GEV, Siemens Energy, Mitsubishi Heavy Industries are the big three. Slot reservation agreements through 2030+.

### GEV (GE Vernova)
#### Position in chain
Largest US gas-turbine OEM + Prolec GE transformer integration post-Q1-26.
#### Financial signals
- GEV: Gas backlog + slot reservations 83 → 100 GW Q1-26; expects 110 GW YE-26 (per GEV Q1-26 2026-04-22)
- GEV: 21 GW new gas equipment contracts Q1-26 (19 GW slot, 2 GW orders); 6 GW conversions
- GEV: $2.4B grid-segment data-center equipment orders Q1 alone -- more than all of 2025 (per Q1-26)
- GEV: Total backlog $163.3B (vs $123.4B YoY)
- GEV: Q1-26 revenue $9.3B (+16% / +7% organic); Adj EBITDA $0.9B (margin 9.6%, +390 bps)
- GEV: Net income $4.7B incl. $4.5B Prolec GE M&A gains
- GEV: grid-segment orders $7.1B total (~2x YoY); North America/Asia ~3x
- GEV: NRG-Kiewit JV 5.4 GW gas through 2032
- GEV: Total grid-segment + gas data-center backlog visibility through 2030
#### Thesis Fit
Highest-leverage AI gas + grid equipment play. Prolec consolidation = transformer pricing power. 20% of 100 GW gas backlog explicit data-center support. Cross-ref: ref-ai-supply-chain-deep-dive §11.

### Siemens Energy
- SIE: Q1 FY26 orders €17.6B (+34% YoY); record (per Siemens Energy Q1 FY26 2026-02-11)
- SIE: Order backlog €146B record (book-to-bill 1.82)
- SIE: Gas Services 102 turbines / ~13 GW Q1; profit margin 16.6%
- SIE: Grid Technologies orders +21.8% YoY; 17.6% margin
- SIE: FY26 revenue +11-13% guide; 9-11% margin; €3-4B net income; €4-5B FCF
- SIE: Q1 region: 40% US / 35% Europe / 15% MidEast+China
Cross-ref: ref-ai-supply-chain-deep-dive §11.

### Mitsubishi Heavy Industries (MHI)
Third largest gas turbine OEM globally; Texas Energy Fund participation; Fervo Series E investor.

### Solar Turbines (CAT subsidiary)
Smaller industrial gas turbines for distributed/peaker; covered under CAT §7.

## 7. Heavy-equipment / standby gensets

### CAT (Caterpillar)
- CAT: AIP Corp Monarch 2 GW G3516 fast-response gas gensets; Sept-2026 to Aug-2027 deliveries (per CAT IR 2026-01-28)
- CAT: AIP Monarch targets 8 GW total capacity; 7-second 0-to-full ramp
- CAT: Hunt Energy 1+ GW multi-year initiative (Texas first project)
- CAT: Caterpillar Financial vendor financing
- CAT: Boyd CAT regional dealer integration
Promote-to-entity: yes (high-leverage candidate).

### CMI (Cummins)
- CMI: HSK78G 4.5 MW gensets data-center backup; multi-year visibility
- CMI: Wartsila + CMI dual-leader large-engine genset market
Promote-to-entity: yes.

### GNRC (Generac)
- GNRC: Enercon Engineering acquisition Q2-26 close; switchgear + enclosures (per Generac IR 2026)
- GNRC: EPC Power partnership AI data-center BESS + gensets (per GNRC 2026-03-05)
- GNRC: SBE Block batteries + ARC Controller + EPC Power M-System inverters
- GNRC: PowerPlay (BESS) + Ageto (microgrid) + Enercon (switchgear) acquisition trajectory
- GNRC: 2025 stock +62% YTD; ~$13B market cap
Promote-to-entity: yes (high-leverage candidate).

### Wartsila / Capstone Green Energy / Bloom Energy
- Wartsila: large-engine peakers
- Capstone Green Energy: microturbines
- Bloom Energy: solid oxide fuel cells; AEP Ohio 1 GW agreement; AWS + Cologix on-site fuel cells

## 8. Transformer + grid-equipment manufacturers

The transformer + grid-equipment tier is the binding bottleneck of AI-power buildout.
- POWER MAGAZINE: power transformer lead time 128 weeks; GSU 144 weeks Q2-25 (per Wood Mackenzie via POWER 2026)
- Some GSUs >210 weeks (per POWER Jan-2026)
- 30% supply shortfall power transformers; 10% distribution 2025-26 (per Wood Mackenzie)
- Demand growth since 2019: GSU +274%, power transformer +116%, distribution +34%
- Transformer prices 4-6x 2022 levels (per T&D World)
- 2030 narrowing: ~5% power transformer shortfall, 140 GSU units by 2030 vs 700+ 2025

### ETN (Eaton)
- ETN: Q1-26 net sales $7.45B (+17% YoY); record (per Eaton Q1-26 2026-05-04)
- ETN: 2026 organic growth guide raised to 10% from 8%; adj EPS $13.05-13.50
- ETN: Total backlog $22.8B; ~68% deliverable in 12 months
- ETN: Boyd Thermal $9.55B + Ultra PCS $1.53B Q1-26 acquisitions
- ETN: 32 GW US data-center capacity under construction; 70% AI; 228 GW backlog at 2025 build rate (per Q1-26 transcript)
- ETN: Data-center orders +240% Q1; revenue +50%; negotiations pipeline +81% YoY
- ETN: Electrical Americas 25.6% margin Q1; 32% target by 2030
- ETN: 12-year data-center backlog at current build rates
Cross-ref: ref-ai-supply-chain-deep-dive §11.

### Hitachi Energy (private; Hitachi 6501.T parent)
- Hitachi Energy: $1B+ US grid-infrastructure investment Sept-2025 (per Hitachi Energy 2025-09-04)
- $457M South Boston VA new large-power-transformer factory; largest US facility; operational 2028
- $106M Alamo TN bushings expansion (per Hitachi 2025-08)
- $195M (CAD $270M) Varennes Quebec triple capacity (per 2025-09-29)
- 825 new VA jobs; 96 workforce-housing units
- Part of $9B+ global investment program
- $250M+ March-2025 component-manufacturing expansion
- Hitachi DOC MoU Oct-2025 (Japan-US strategic investment)
- Order backlog 3x+ since 2020
Cross-ref: ref-ai-supply-chain-deep-dive §11.

### ABB (private ADR ABBNY)
Global power-electronics + grid-automation leader. Cross-ref: ref-ai-supply-chain-deep-dive §11 thin stub.

### HUBB (Hubbell)
- HUBB: Utility Solutions transformer + meter + grid-controls business
- HUBB: Aclara distribution products
Cross-ref: ref-ai-supply-chain-deep-dive §11 thin stub.

### POWL (Powell Industries)
- POWL: Q1 FY26 revenue $251.2M; net income $41.4M (per Powell 10-Q 2025-12-31)
- POWL: $100M+ data-center orders Q1-FY26 incl. single $75M project (per Q1)
- POWL: FY25 backlog $1.4B; new orders Q4 FY25 $271M ($1.2B FY)
- POWL: Q4 FY25 record orders $439M incl. $100M LNG + $75M data center
- POWL: Data-center repetitive "design-one, build-many" strategy
Promote-to-entity: yes.

### Schneider Electric (SU.PA / SBGSY)
European grid + datacenter UPS leader. Cross-ref: ref-ai-supply-chain-deep-dive §11.

### Hammond Power Solutions (HPS.TO)
Canadian distribution-transformer manufacturer; Q3-25 backlog growth.
Promote-to-entity: yes.

### Sungrow / Jinpan (JST) / Mitsubishi Electric
Asian transformer + inverter exporters. Mitsubishi Electric $86M switchgear factory Dec-2024. JST distribution-transformer trade-aggregator.

### Prolec GE (now 100% GE Vernova)
- Prolec: $5B backlog contribution Q1-26 GEV consolidation
Cross-ref: §6.

### Quanta Services (PWR; transmission contractor)
- PWR: Q1-26 revenue $7.9B; record backlog $48.5B; 2026 revenue guide $34.7-35.2B (per Quanta Q1-26 2026-04-30)
- PWR: $500-700M investment program doubling power-transformer capacity; 6.7M sqft off-site manufacturing target
- PWR: 765 kV transmission MSA awarded Q1-26
- PWR: First meaningful AEP-related opportunity
Promote-to-entity: yes (high-leverage).

## 9. Energy storage / BESS

### FLNC (Fluence)
- FLNC: FY25 revenue $2.3B; Q4 $1.0B; backlog $5.3B record (per Fluence FY25 2025-11-24)
- FLNC: FY26 revenue guide $3.2-3.6B (+50%); 85% backlog-covered
- FLNC: FY25 ARR $148M; FY26 target $180M
- FLNC: Q4 order intake $1.4B record
- FLNC: 30+ GWh data-center pipeline; 80% originated since Sept-2025
- FLNC: Smartstack 7.5 MWh/unit, 500+ MWh/acre; 20-25% higher density
- FLNC: $8.5B data-center opportunity through 2030 (Q3 FY25 estimate)
- FLNC: 41% revenue concentration top-2 customers FY25
- FLNC: ~$200M FY26 capex incl. $100M domestic supply chain
Cross-ref: ref-ai-supply-chain-deep-dive §11.

### STEM (Stem Inc)
Smaller AI-software-tilted BESS player. Promote-to-entity: yes.

### Tesla Megapack
Largest BESS deployer; private to Tesla auto thesis -- AI-power-attribution opaque.

### CATL / LG Energy Solution / Samsung SDI / BYD / Sungrow
Asian battery cell + BESS integrator giants; export risk + tariff exposure.

### ESS Inc (GWH) / Energy Vault (NRGV)
Pure-play long-duration BESS; iron-flow + gravity respectively. Pre-scale.

### Meta Orsted Arizona 1,200 MWh template
4-hour BESS firming AI data centers; standardized template now replicated by Microsoft (Arizona, Sweden), Google (Nevada).

## 10. Renewables developers + utility-scale

### NEE Energy Resources (under NEE §3)
33 GW backlog; primary US utility-scale developer.

### BEPC (under §2)
10.5 GW MSFT framework anchor.

### AES Corp (under §2)
~16 GW pipeline; Google Texas-OK PPAs.

### Pattern Energy (private)
Acquired by Brookfield 2024; private now.

### CWEN (under §2)

### First Solar (FSLR)
- FSLR: Largest US thin-film module producer; AI-data-center solar PPAs
- FSLR: Domestic manufacturing scale 14 GW US capacity 2026
Promote-to-entity: yes.

### Enphase (ENPH) / SunPower
Distributed solar + microinverters; AI-DC-attribution low.

## 11. Geothermal + emerging baseload

### ORA (Ormat) -- see §2

### Sage Geosystems (private)
- Sage: Meta 150 MW PPA first phase 2027 east-of-Rockies (per Sage IR 2024-08-26)
- Sage: 8 MW operational 2027; scale to 150 MW within 36-48 mo
- Sage: 3 MW Christine TX with San Miguel Coop ERCOT first geothermal
- Sage: Ormat investor; partnership for operations
- Sage: $17M February 2024 round + add-ons
Promote-to-entity: yes (private).

### Fervo Energy (private)
- Fervo: Cape Station Phase I 100 MW commercial Oct-2026; Phase II +400 MW 2028; full 500 MW; permitted to 2 GW (per Fervo IR 2025-06-11)
- Fervo: Series E $462M Dec-2025 led by B Capital + Google + Mitsui (per Fervo 2025-12-10)
- Fervo: $421M non-recourse project debt March-2026 (per Fervo 2026-03-19)
- Fervo: $206M June-2025 ($100M Breakthrough Energy preferred + Mercuria + XRA)
- Fervo: ~$1.5B raised since 2017
- Fervo: Devon Energy $244M earlier round
- Fervo: NV Energy 115 MW Google PPA Nevada 3.5 MW pilot operational Nov-2023
Promote-to-entity: yes (private).

### XGS Energy (private)
- XGS: Meta 150 MW New Mexico PPA 2026 (per Utility Dive 2026)

### Eavor Technologies / Quaise / GreenFire (private)
Closed-loop and hybrid EGS startups in TRL 5-7 range.

## 12. Fusion (NARRATIVE-TRACKING ONLY)

All pre-revenue private equity:
- Commonwealth Fusion Systems (CFS): SPARC at MIT; $2B+ raised; ARC commercial 2030s; Microsoft offtake LOI
- TAE Technologies: $1B+ raised; field-reversed configuration
- Helion: Microsoft 50 MW PPA target 2028 (aspirational)
- Tokamak Energy / General Fusion / ZAP Energy / Avalanche / SHINE / Realta / Marvel: each <$500M raised
Track for narrative-shift triggers; no investable equity layer.

## 13. ISO/RTO market structure

PJM auction price-cap signals + ERCOT 410 GW queue are the two most-watched market signals.

### PJM
- PJM 2026/2027 BRA cleared at price cap $329.17/MW-day all zones (per PJM 2025-07-22)
- PJM 2027/2028 BRA cleared at $333.44/MW-day; 6,623 MW reliability shortfall (per PJM 2025-12-17)
- PJM cleared $16.4B; data-center 40% of capacity costs per market monitor
- PJM peak-load forecast 2026/27 +5,400 MW; 2027/28 +5,250 MW (5,100 MW data-center)
- PJM data-center 63% of 2025/26 price increase ($9.3B ratepayer cost) per Monitoring Analytics
- PJM 30,000 MW transition queue remaining; 170,000 MW processed since 2023
- 22% YoY 2026/27 price; 833% YoY 2025/26 prior

### ERCOT
- ERCOT large-load queue 410 GW April 2026 (~87% data centers); was 233 GW Dec-2025 (per RTO Insider 2026-04-01; ERCOT 2025-12-09)
- ERCOT generation interconnection queue 432 GW (176 GW storage, 158 GW solar, 48 GW gas)
- ERCOT 23 GW new generation 2024-25; 9 GW expected early 2026
- ERCOT 138 GW large-loads expected 2030
- Texas SB 6 large-load interconnection rules effective March-2026; PUCT rulemaking complete Dec-2026
- ERCOT 8.8 GW new gas by end-2029 (TEF-incentivized); 18 TEF projects = 7+ GW in FIS

### MISO / SPP / CAISO / NYISO / ISO-NE
- MISO: 43% YoY load growth since 2020 fastest US per FERC; AEP-Berkshire $1.2B 765-kV award
- SPP: load-centric interconnection lane PAL; April-2026 western expansion live
- CAISO: PG&E + SCE service territories; California PUC AB 205 large-load tariffs
- NYISO: ≥10 MW @ ≥115 kV interconnection threshold
- ISO-NE: Eversource transmission emphasis

## 14. Transmission build-out

- PJM RTEP $11.8B 2026 expansion plan
- FERC Order 1920 long-term planning final rule (per FERC explainer)
- FERC Order 2023 first-ready/first-served interconnection (per FERC)
- DOE Speed-to-Power initiative Sept-2025: target 3-20 GW incremental load via 1,000+ MVA interregional transmission

### Quanta Services (PWR) -- see §8 above; $48.5B backlog

### MasTec (MTZ)
Transmission + renewables EPC; Quanta's nearest peer.
Promote-to-entity: yes.

### Primoris Services (PRIM)
Sub-tier transmission + utility EPC.
Promote-to-entity: yes.

### MYR Group (MYRG)
Mid-size transmission contractor.
Promote-to-entity: yes.

## 15. PPA structures + hyperscaler-utility deal templates

PPA template taxonomy emerging:
- **BTM (behind-the-meter)**: original AWS Susquehanna; FERC-rejected → migrating to FOM
- **FOM (front-of-the-meter)**: AWS-Talen 1.92 GW 2025-06; CEG-MSFT TMI; new dominant template
- **Sleeved PPA**: Brookfield-MSFT 10.5 GW framework
- **Energy Services Agreement (ESA)**: PPL-Blackstone JV template for Pennsylvania CCGT
- **Prepayment + capital**: Oklo-Meta novel structure (Meta funds early Aurora + nuclear fuel)
- **Uprate-inclusive**: VST-Meta 433 MW uprates within 2,609 MW total
- **Take-or-pay tariff**: AEP's PJM ESAs (90%+ contracted-load is take-or-pay)

## 16. Datacenter-grid co-location strategies

DLR / EQIX / IRM / Vantage / CyrusOne (KKR/Stonepeak) / QTS (Blackstone) / Switch (DigitalBridge) / Aligned / Compass private peers:
- Cross-ref: ref-ai-supply-chain-deep-dive §6 for REIT power-shell vs power-skip strategy detail
- QTS-Blackstone backed PPL CCGTs across Pennsylvania
- DLR ringfences power via developer-led PPAs in Northern VA
- EQIX retail colocation power-skip / customer-owned power
- Vantage Wisconsin Stargate site (SoftBank-led)

## 17. Cooling-water + drought + siting constraints

Concentrated risks:
- Loudoun County VA: zoning moratorium + Substation 64 capacity limit; 6 GW Eastern Loudoun Dominion 500-kV unlock pending
- Phoenix Salt River Project: drought + cooling-water permits; 95F+ peak load risk
- Columbia River (Oregon): liquid cooling + temperature limits
- Mississippi watersheds: AWS/Meta gas-cooled deployments
- TX/AZ/VA drought triple-overlap with grid-stress

## 18. Backup / standby power

CAT / CMI / GNRC / Kohler (private) lead the standby-power layer for AI DC. EPA PSD permits emerging as bottleneck. Major lead times 18-24 months for 2-3 MW gensets in early 2026.

## 19. Workforce / labor

Critical labor shortages:
- IBEW transmission line-worker shortage (~10K+ shortfall 2026)
- Nuclear-trained operator pipeline (TMI restart needs 600 operators)
- Ironworkers + electricians for substation buildout (Quanta vertical integration response)
- Nuclear-NDT inspector shortage flagged at NEI conference 2026

## 20. Permitting + regulatory

Key tracks:
- FERC Order 2023 + 1920 implementation
- State PUC datacenter rate cases (TX SB 6, OH HB 15, VA SB 1, NJ A4929)
- NRC Combined Operating License (CPA) process (Holtec SMR-300 Dec-2026)
- EPA PSD permits for backup gensets
- Texas SB 6 large-load curtailment rules
- One Big Beautiful Bill Act (OBBBA) - reduced wind/solar PTC; FEOC sourcing for transformers
- Section 232 tariff restructuring April-2026 (15% grid-equipment temporary)

## 21. Financing structures

- DOE Office of Energy Dominance (formerly LPO): $1.52B Holtec Palisades; $26.5B Southern; conditional commitments rising
- DOE Tier-1 First Mover: Holtec SMR-300 $400M
- Section 45U / 45X tax credits for nuclear PTC + manufacturing
- ITC/PTC for renewables (OBBBA-truncated by 2030)
- Private credit infrastructure funds: Blackstone $25B PA commitment; KKR / Brookfield $25B+ transition fund; Stonepeak utility allocations
- Muni bonds + utility green bonds (~$50B 2026 issuance pace)
- Fervo $421M non-recourse project debt March-2026 = template

## 22. Emerging displacers + bottlenecks

Top-priority bottlenecks:
1. **Transformer shortage**: 128-week / 144-week lead times; Hitachi Energy + GEV-Prolec doubling capacity but supply-demand gap persists to 2030
2. **PJM capacity-cap**: $329-333/MW-day caps mask further upside; 6,623 MW reliability shortfall in 2027/28
3. **NRC SMR licensing pace**: only NuScale fully certified; Oklo custom COL pioneer
4. **ERCOT large-load queue**: 410 GW vs 23 GW recent additions = phantom-load risk
5. **Gas turbine slot reservations**: GEV / Siemens Energy / MHI through 2030+; new orders 2027 delivery earliest
6. **Geothermal scale**: Fervo + Sage + XGS at TRL 7-8; need 5-10 GW by 2030 to materially shift baseload mix
7. **Fusion narrative-shift trigger**: CFS SPARC net energy gain demonstration (target 2027) = potential displacer

Emerging displacers to monitor:
- **Gas + battery hybrids vs pure gas**: AIP Monarch + Caterpillar G3516 + BESS template
- **BTM nuclear vs grid-tied**: post-Talen FERC ruling shift to FOM accelerates grid investment
- **Geothermal vs SMR for baseload**: Fervo/Sage 2026-30 commercial timeline beats most SMRs (NuScale RoPower 2030 only)
- **Transformer reshoring vs Chinese imports**: Section 232 tariff + BABA = 2-3 yr reshoring lag
- **HVDC vs HVAC long-haul**: SOO Green HVDC IL-IA + Grain Belt Express templates
- **Bloom solid-oxide fuel cells**: AEP Ohio 1 GW + AWS Cologix on-site = standby-to-primary path

## Competitive landscape summary tables

### Hyperscaler-PPA matrix (selected, GW contracted)
| Hyperscaler | Nuclear | Renewables | Gas/Other | Geothermal | Total disclosed |
|---|---|---|---|---|---|
| MSFT | 0.835 (CEG) + ~5 target | 19+ online of 40 contracted; +10.5 (BEPC) | -- | -- | ~50 |
| AWS | 1.92 (TLN) + 1.2 (VST) | ~5 | -- | -- | ~8 |
| META | 2.609 (VST) + 1.2 (Oklo) + 0.5 (TerraPower-incl) | several | 2 (Entergy) | 0.3 (Sage+XGS) | ~6.6 nuclear / ~10 total |
| GOOGL | 0.5 (Kairos by 2035) | broad | -- | 0.265 (Fervo+ORA) | ~6 |
| OpenAI/Stargate | -- | -- | grid + gas | -- | 10 (target 2029) |
| Oracle | -- | -- | grid | -- | 4.5 (Stargate Oracle) |

### IPP fleet by fuel mix (operating GW disclosed)
| IPP | Nuclear | Gas | Renewables | Total |
|---|---|---|---|---|
| VST | ~6.4 | ~32 | minor | ~41 |
| CEG | ~22 | ~10 | minor | ~33 |
| TLN | 2.5 | ~5 | -- | ~10 |
| NRG | -- | ~25 (post-LS) | -- | ~30 |
| AES | 1.7 | ~10 | ~16 | ~27 |
| BEPC | -- | minor | ~30 op + 200 pipeline | ~30 op |

### SMR licensing pipeline
| Design | MWe | NRC status | First COD | Customer LOI |
|---|---|---|---|---|
| NuScale 77 MWe | 77 | SDA approved May-25 | 2030 (RoPower) | TVA-ENTRA1 6 GW |
| Oklo Aurora | 15-75 | Custom COL submitted | 2030 | Meta 1.2 GW |
| Kairos Hermes | 50 | Hermes 1 construction permit | 2030 | Google 500 MW |
| TerraPower Natrium | 345 | Wyoming construction | 2030 | Bill Gates / DOE |
| X-energy Xe-100 | 80 | construction permit progress | 2030 | Amazon $500M / Dow |
| Westinghouse AP300 | 300 | early NRC | 2031+ | Brookfield/TNC V.C. Summer |
| Holtec SMR-300 | 340 | CPA Part 1 Dec-26 | 2030+ | Palisades dual + Pickering Canada |

### Transformer manufacturing capacity by vendor (US-relevant)
| Vendor | Investment 2024-26 | New capacity | Online | AI-data-center alignment |
|---|---|---|---|---|
| Hitachi Energy | $1B+ | VA new factory | 2028 | Largest US large-power transformer |
| GEV Prolec | Q1-26 consolidation | $5B backlog acquired | 2026 | Already shipping data-center class |
| Siemens Energy | grid-tech +21.8% orders | global | 2027+ | Strong US data-center orders Q1 |
| Quanta PWR | $500-700M | doubling power transformer | 2027 | Vertical integration |

### ISO/RTO interconnect queue length (GW, large-load + generation, late 2025/early 2026)
| ISO/RTO | Generation queue | Large-load queue | Capacity-auction price |
|---|---|---|---|
| PJM | ~63K MW remaining 2025-26 | 26 GW transition + ~190 GW pipeline | $329-333/MW-day cap |
| ERCOT | 432 GW | 410 GW (87% DC) | n/a (energy-only) |
| MISO | rapid growth +43% YoY | growing | various |
| SPP | growing | new PAL service | rising |
| CAISO | constrained | growing | rising |

## Footnotes

[^1]: Vistra Q4-25 release, 2026-02-26 (sec.gov 8-K)
[^2]: Constellation 2025 10-K filed 2026-02-24
[^3]: Talen Energy IR statement / Utility Dive 2025-06
[^4]: GE Vernova Q1-26 release 2026-04-22
[^5]: Brookfield Renewable IR / SEC 6-K 2024-05-01
[^6]: Microsoft Carbon Negative blog 2026-02-18
[^7]: Oklo 8-K 2026-01-09 (Meta agreement)
[^8]: NextEra Q1-26 release 2026-04-23
[^9]: AEP Q1-26 release 2026-05-05
[^10]: Southern Q4-25 release 2026-02-20; Utility Dive 2026-02-20
[^11]: Dominion Q4-25 release 2026-02; Utility Dive
[^12]: Duke Energy 2025 ARS / 8-K 2025
[^13]: PJM 2026/2027 BRA Report 2025-07-22; 2027/2028 BRA Report 2025-12-17
[^14]: Wood Mackenzie Q2-25 transformer survey via POWER Magazine Jan-2026
[^15]: ERCOT Large Load Update April 2026 / RTO Insider 2026-04-01
[^16]: Hitachi Energy IR 2025-09-04
[^17]: Siemens Energy Q1 FY26 release 2026-02-11
[^18]: Eaton Q1-26 release 2026-05-04
[^19]: Quanta Services Q1-26 release 2026-04-30
[^20]: NRG 8-K 2025-Q4; Q3-25 earnings call
[^21]: PPL/Blackstone IR 2025-07-15
[^22]: Holtec / DOE LPO 2024-09-30; Michigan Public 2025-12-17
[^23]: Fluence FY25 release 2025-11-24
[^24]: Caterpillar IR 2026-01-28 (AIP Monarch)
[^25]: Generac IR 2026; PRNewswire 2026-03-05
[^26]: Powell Industries 10-Q FY26 Q1
[^27]: Fervo Energy IR 2025-06-11; 2025-12-10; 2026-03-19
[^28]: Sage Geosystems / Meta BusinessWire 2024-08-26
[^29]: NuScale Q4-25 release 2026-02-26
[^30]: BWXT Q2-25 transcript; ANS Aug-2025
[^31]: Kairos Power / TVA / Google 2025-08-18
[^32]: Ormat Q4-25 release 2026-02-26
[^33]: FirstEnergy Q1-26 8-K 2026-04-28
[^34]: Entergy IR / DCD; Yahoo Finance 2025
[^35]: OpenAI Stargate announcements 2025-01-21; 2025-07; 2025-09-23
[^36]: IEA Electricity 2026
[^37]: EPRI Powering Intelligence 2026
[^38]: DOE-LBNL 2024 Data Center Energy Usage Report
[^39]: FERC Order 2023 / 1920 explainers (ferc.gov)
[^40]: DTE Energy 8-K 2026-Q1 (Oracle 1.4 GW + Google 1 GW)

## Quantified power-complex dashboard (GENERATED 2026-08-24)

**All figures computed from point-in-time daily closes in the vault factor store
(`Efforts/osanwe-v2-overhaul/_work/factors.db`, table `bars`). Regenerate via
tools/bulk-data-pull.py + gen-reference-expansion.py.**

Method and window, stated so nothing is inherited blindly:

- Window: 1-year = 252 trading sessions 2025-08-21 through 2026-08-21 for ALL 16
  names plus SPY (verified equal-length windows; no survivorship truncation).
  6-month figures use the trailing 183-day cut of the same series.
- Beta vs SPY: daily-close return covariance/variance on common dates within the
  1y window. Volatility: annualized std of daily returns (x sqrt(252)).
  MaxDD: peak-to-trough within the 1y window only.
- RSI14: Wilder smoothing over the last ~130 sessions of each full price series.
- Sub-sector labels: gen (CEG/VST/TLN/NRG), equipment (GEV/ETN/HUBB/ABBNY/VRT/
  FLNC), utility (NEE/AEP/DUK/PPL/SO), nuclear-components (BWXT).

### Per-ticker performance (1y window ending 2026-08-21)

| Ticker | Sub-sector | 1y ret | 6m ret | Ann vol | Beta vs SPY | MaxDD 1y | vs 52w high | RSI14 |
|---|---|---|---|---|---|---|---|---|
| VRT | equipment | +107.2% | +7.8% | 65.6% | 2.71 | -40.7% | -30.4% | 42 |
| FLNC | equipment | +65.8% | -31.5% | 128.3% | 4.37 | -64.8% | -64.8% | 35 |
| GEV | equipment | +58.3% | +14.8% | 52.4% | 2.05 | -24.6% | -18.6% | 41 |
| ABBNY | equipment | +54.0% | +13.1% | 32.0% | 1.60 | -16.0% | -8.7% | 49 |
| ETN | equipment | +22.7% | +12.0% | 37.9% | 1.74 | -18.3% | -8.9% | 47 |
| NEE | utility-hybrid | +13.1% | -7.4% | 21.5% | 0.15 | -14.5% | -13.9% | 32 |
| HUBB | equipment | +11.3% | -10.2% | 31.8% | 1.22 | -17.4% | -15.5% | 40 |
| AEP | utility | +10.2% | -4.4% | 19.1% | -0.04 | -12.1% | -12.1% | 31 |
| DUK | utility | -0.1% | -3.5% | 15.9% | -0.30 | -10.9% | -8.6% | 37 |
| SO | utility | -2.9% | -4.9% | 17.1% | -0.25 | -15.0% | -8.8% | 31 |
| PPL | utility | -3.4% | -5.6% | 17.6% | -0.02 | -13.3% | -12.9% | 37 |
| BWXT | nuclear-components | -4.6% | -24.7% | 43.9% | 1.93 | -34.2% | -34.1% | 34 |
| TLN | gen-nuclear | -12.1% | -17.3% | 54.5% | 1.94 | -32.0% | -29.5% | 37 |
| CEG | gen-nuclear | -12.2% | -6.0% | 47.0% | 1.35 | -41.2% | -32.1% | 53 |
| NRG | gen-gas | -21.5% | -34.9% | 48.1% | 1.39 | -38.1% | -38.1% | 39 |
| VST | gen-nuclear | -28.0% | -20.8% | 49.5% | 1.50 | -38.0% | -37.2% | 37 |
| SPY | benchmark | +21.8% | -- | -- | 1.00 | -8.9% | -1.6% | -- |

### Load-growth thesis quantification: who carries the AI-power narrative

Group means over the same 1y window (momentum used as the narrative-beta proxy):

| Group | 1y ret (mean) | Ann vol | Beta vs SPY | MaxDD | vs 52w high |
|---|---|---|---|---|---|
| Equipment (6 names) | +53.2% | 58.0% | 2.28 | -30.3% | -24.5% |
| Regulated utilities (AEP/DUK/PPL/SO) | +0.9% | 17.4% | -0.15 | -12.8% | -10.6% |
| Generators incl gas (CEG/VST/TLN/NRG) | -18.5% | 49.8% | 1.54 | -37.3% | -34.2% |
| Nuclear components (BWXT) | -4.6% | 43.9% | 1.93 | -34.2% | -34.1% |

Narrative-momentum ranking, highest to lowest: VRT (+107%), FLNC (+66%),
GEV (+58%), ABBNY (+54%), ETN (+23%), NEE (+13%), HUBB (+11%), AEP (+10%),
DUK (-0.1%), SO (-3%), PPL (-3%), BWXT (-5%), TLN (-12%), CEG (-12%),
NRG (-22%), VST (-28%).

The load-growth story is being monetized in EQUIPMENT, not generation: five of
the top six narrative-beta names are grid/equipment vendors, at 2-3x market beta
and 50%+ realized vol, while every unregulated generator underperformed cash-like
SPY by 30+ points over the window. Two caveats from the data itself: FLNC's 1y
figure is carried entirely by stale momentum (6m -31.5%, still -64.8% off its
high), and VRT's own 6m (+7.8%) shows even the leader's impulse decaying --
the group's 1y numbers embed an H2-2025 burst, not a current trend.

### Valuation-free technical state (per name; columns in the table above)

- No name is overbought: highest RSI14 is CEG at 53; 12 of 16 sit in the low-30s
  to mid-40s band. The whole complex is washed out on momentum, not extended.
- Deepest drawdown states: FLNC -64.8% (still AT its 1y low region), NRG -38.1%
  (at low), VST -38.0%, VRT -40.7%, CEG -41.2%. All four nuclear-tilted
  generators remain 29-38% below their 52-week highs.
- Most repaired: ABBNY (-8.7% from high), ETN (-8.9%), DUK (-8.6%) -- the
  equipment majors and regulated defensives never fully unwound.
- Utilities cluster at RSI 31-37 with -9% to -13% drawdowns: orderly
  consolidation, no capitulation signature, consistent with their negative betas
  (-0.30 to +0.15) acting as the complex's ballast while generators de-rated.

### The nuclear premium: quantified, and currently NEGATIVE

The thesis says hyperscaler PPA enthusiasm should re-rate unregulated nuclear
operators ahead of regulated peers. Over this 1y window the market priced the
opposite:

| Measure | Nuclear IPPs (CEG/TLN/VST) | Regulated (AEP/DUK/PPL/SO) |
|---|---|---|
| 1y return (mean) | -17.4% | +0.9% |
| PPA-enthusiasm spread | **-18.4 pts** | -- |
| Beta vs SPY | 1.60 | -0.15 |
| Ann vol | 50.3% | 17.4% |
| Drawdown from 52w high | -32.9% | -10.6% |

Per name: VST -28.0%, CEG -12.2%, TLN -12.1% versus AEP +10.2%, DUK -0.1%,
PPL -3.4%, SO -2.9%. Despite signing the largest hyperscaler nuclear PPAs in the
enumeration above (AWS-Talen 1.92 GW, AWS-VST 1.2 GW, META-VST 2.6 GW,
MSFT-CEG 835 MW), the IPP tier delivered regulated-utility downside with
double-plus equity beta. Read: the PPA revenue is contracted years out
(deliveries mostly 2027-2032 per Sections 1-2), so the market is currently paying
for regulated rate-base VISIBILITY and discounting IPP optionality -- the
premium is deferred, not destroyed, and flips sign only when PPA deliveries
convert to EBITDA. This is a single-window measurement; re-run it before
treating the negative spread as a regime fact.

Data gaps, stated rather than papered over: ABB has no primary listing row in
the factor store -- its US ADR (ABBNY) is used throughout and labeled as such;
D/EXC/SRE/FE/ETR and the SMR developers (OKLO/SMR/NNE) are in the store but
outside the 16-name scope specified for this dashboard; bars carry no dividends,
so total-return figures would run slightly higher than the price returns shown.
[^40]: DTE Energy 8-K 2026-Q1 (Oracle 1.4 GW + Google 1 GW)
