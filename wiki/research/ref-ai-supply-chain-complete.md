---
categories: [wiki]
type: reference
status: active
created: 2026-08-25
updated: 2026-08-25
confidence: high
generated: 2026-08-25 by supply-chain dependency-graph subagent (vault refs + entity-note claims only, no network)
tags:
  - topic/investing
  - topic/theme-alpha
  - topic/supply-chain
  - topic/semiconductors
related: ["[[ref-semiconductor-value-chain]]", "ref-supply-chain-dependency", "[[ref-datacenter-infrastructure]]", "[[ref-energy-power-complex]]", "ref-memory-storage-cycle-deep-dive"]
---

# AI Supply Chain -- Complete Dependency Graph (Tier 0-7)

GENERATED: 2026-08-25. Sources: [[ref-semiconductor-value-chain]] (the 20-name
semiconductor reference), ref-supply-chain-dependency (edge-level map),
[[ref-datacenter-infrastructure]] (server OEMs, networking, DC REITs, neo-clouds),
[[ref-energy-power-complex]] (power layer). Entity-note claims are carried through
with their grade (HIGH/MEDIUM/LOW); anything computed in this document is labeled
DERIVED. No network sources used. No .raw/private/finance reads.

Reading convention: every "$" figure traces to an entity note or ref cited in the
source documents above; where the corpus carries conflicting figures captured at
different dates (e.g. hyperscaler capex $640B vs $750B), they are shown as a band,
not reconciled by hand.

---

## Tier 0-7 Supply Chain Map

Chain definition used throughout this file:

```
Tier 0  Raw Materials & Substrates      wafers, gases, chemicals, substrates
Tier 1  Equipment                       litho, deposition/etch, metrology, WFE
Tier 2  Design/IP & EDA                 toolchains, CPU ISA, simulation IP
Tier 3  Fabrication                     leading-edge foundry + memory IDMs
Tier 4  Chip Design (fabless/IDM)       GPUs, XPUs, switch ASICs, CPUs, HBM die design
Tier 5  Assembly / Test / Packaging     CoWoS, hybrid bonding, OSAT, module assembly
Tier 6  System Integration              servers, switches, optics, cabling, racks
Tier 7  Data Center Operations          hyperscalers, neo-clouds, colo REITs, power
```

### Tier 0 -- Raw Materials & Substrates

| Node | Companies | Role | Key dependencies |
|---|---|---|---|
| Silicon wafers | Shin-Etsu, SUMCO, GlobalWafers | 300mm prime wafers feed every fab | polysilicon (Hemlock, Wacker, GCL); quartz crucibles |
| Photomasks/blanks | Toppan, Hoya, Photronics | pattern masks for every node | ultra-pure fused silica (Corning-class); EUV blank duopoly w/ ASML-linked supply |
| Photoresists | JSR, TOK, Shin-Etsu | EUV/DUV resists | EUV resist chemistry is Japan-concentrated |
| Specialty gases | Linde, Air Liquide, Air Products | etch/deposition precursors, NF3, WF6 | rare fluorine chemistry; some Chinese-sourced raw feeds |
| CMP slurries/pads | Cabot Microelectronics (CMC), DuPont | wafer planarization every layer | colloidal silica; polyurethane pads |
| ABF substrate | Ajinomoto (ABF film), Ibiden, Unimicron, Shinko | package substrates under every large GPU/XPU | ABF film effectively sole-sourced from Ajinomoto; substrate capacity gates CoWoS |
| Rare earths / sputter targets | Lynas, Matterhorn-type processors; Honeywell targets | magnet, deposition-target inputs | China refining concentration |

CORPUS STATUS: none of these names carry entity notes or XBRL pulls in this vault
-- this tier is mapped structurally (DERIVED from role descriptions in the source
refs) and is the file's largest DATA GAP. The one corpus-anchored upstream fact:
ASML depends on a Zeiss-class optics supply web (ASML, Section 13.6 of
[[ref-semiconductor-value-chain]]) -- i.e. even Tier 1 equipment has a Tier 0-style
upstream chokepoint inside it.

Why Tier 0 matters anyway (DERIVED): the ABF-substrate line is the physical gate on
CoWoS expansion (Tier 5) -- TSMC cannot double CoWoS wafers/month without substrate
supply doubling behind it. Treat substrate lead times as a falsifiable monitor even
without entity coverage.

### Tier 1 -- Wafer-Fab Equipment (WFE)

| Node | Companies | Role | Key dependencies |
|---|---|---|---|
| Lithography (EUV/DUV) | ASML | SOLE EUV supplier on earth; High-NA EUV EUR 350M+/tool | Zeiss-class optics; every 1-alpha/1-beta DRAM node AND every leading-edge logic node routes through it (ASML, HIGH) |
| Deposition/etch (broadline) | AMAT | largest installed base; dep/etch/inspection; HBM TSV etch+dep named in ENT[AMAT] | subcomponents, precision optics; memory-IDM capex cycle |
| Deposition/etch (memory-weighted) | LRCX | cleanest WFE beta to the HBM/DRAM shortage; cryogenic NAND etch | memory IDM capex (~$65B 2026 aggregate, HIGH); captures ~$8B per $100B incremental DC investment (MEDIUM) |
| Process control / metrology | KLAC | inspection intensity rises every node transition and with hybrid bonding | N2 ramp at TSMC pulls inspection (KLAC catalyst list) |
| Advanced-packaging instruments | ONTO | hybrid-bonding metrology/inspection pure play -- direct instrument on the CoWoS bottleneck | TSM CoWoS expansion schedule |

Key dependencies (tier level):
- Demand comes from two capex streams: TSM capex FY26 $60-64B (raised from
  $52-56B at the 2026-07-16 Q2 print, HIGH, ENT[TSM]) plus memory IDM capex
  ~$65B 2026 (SK hynix $20.5B + Samsung $20B + Micron ~$20B + Kioxia/SanDisk
  $4.5B, HIGH, via ref-supply-chain-dependency Edge 4).
- Industry-wide WFE guided to ~$135B CY2026 from ~$110B 2025, +23%
  (LRCX guide, HIGH; AMAT cites same figure).
- Backlog visibility through 2027-2028 (LRCX/AMAT).
- Policy tail: China export controls clamp both tool sales (ASML China mix 33%
  2025 -> ~20% 2026 guided, HIGH) and indigenous substitution risk
  (NAURA/AMEC absorbing sockets, wave-S-AMAT).

### Tier 2 -- Design/IP & EDA

| Node | Companies | Role | Key dependencies |
|---|---|---|---|
| EDA #1 | SNPS (~31-46% share by methodology, ENT[SNPS]) | every tape-out at TSM/GFS and every design at NVDA/AMD/AVGO/MRVL/QCOM licenses its toolchains; Ansys adds multiphysics simulation | design-start volumes; export controls on China tool sales |
| EDA #2 | CDNS (~35-36% share, ENT[CDNS]; FY24 rev $4.64B +13%) | same tollgate function; 100% retention, 80-85% recurring revenue | same |
| CPU ISA / IP | ARM | instruction-set gravity for hyperscaler CPUs: Graviton (AMZN), Cobalt (MSFT), Axion (GOOGL); cores built into AVGO/MRVL custom XPUs | royalty leverage to every hyperscaler custom-CPU fleet; competes with x86/RISC-V per-workload but not at fleet scale (DERIVED) |

Key dependencies:
- Combined EDA duopoly share ~70-74% (MEDIUM/DERIVED across ENT[SNPS]/ENT[CDNS]).
  Nothing ships without their signoff -- including every custom-silicon program
  that threatens NVIDIA's merchant share.
- ARM sits upstream of Tier 3 tape-outs that implement Arm cores.
- Risk vector is design-cycle deceleration, not share loss; both EDA names also
  carry the China-tooling export-control policy tail.

### Tier 3 -- Fabrication (Foundry + Memory IDMs)

| Node | Companies | Role | Key dependencies |
|---|---|---|---|
| Leading-edge foundry | TSM | 70.2% foundry share Q2-25 (ENT[TSM]); monopoly leading edge; N2 volume production Q4-2025 at ~65-75% yields, N2P H2-26, A16 backside-power H2-26 (all HIGH) | ASML EUV/High-NA (sole supplier; TSM is FIRST High-NA volume customer); AMAT/LRCX/KLAC/ONTO tooling; Taiwan geographic concentration |
| Trailing-edge/specialty foundry | GFS | power-management ICs, silicon photonics SOI (via Tower Semi) | auto/industrial cycles; NOT in the leading-edge AI compute path |
| DRAM/HBM | MU (+ SK hynix, Samsung as unlisted co-duopolists) | HBM leader; FQ2-26 revenue $23.86B beat 28%, GM 74.9%, DRAM +90% QoQ record (MU analysis log); LQ $41.46B +345.7% YoY (FIN) | EUV-gated nodes (every HBM die requires 1-alpha/1-beta DRAM); TSM base-die partnership for HBM4 with SK Hynix; capex/revenue 42.4% FY25, FY26 raised $20B -> $25B |
| NAND/SSD | SNDK (+ Kioxia JV) | NAND complement inside AI storage stacks; Kioxia 14% stake re-rated 14x | cryogenic etch tooling (LRCX); sold-out posture |
| Nearline HDD | WDC | AI training/inference archive demand; "sold out for all of 2026" (ENT[WDC], HIGH); 1y total return +860% at claim date | component chains; decoupled from DRAM cycle (rho 0.73 max) |

Key dependencies:
- The memory trio (SK hynix + Samsung + Micron) is a three-source oligopoly with
  ~$65B combined 2026 capex; SK hynix 'One Team' >50% of NVDA HBM share 2026;
  CY26 HBM supply locked (HIGH).
- Demand concentration: OpenAI Stargate demand ~900K DRAM wafers/month (~40% of
  global DRAM) concentrates the demand book into one credit (Samsung insert,
  ref-memory-storage ingest).
- TSM customer concentration: NVIDIA #1 at ~19-22% of revenue (passing Apple
  ~17-18%), MediaTek 9%, Qualcomm 8%, AMD 7%; top-10 customers 76% of revenue.
- Geopolitical binary: market prices roughly a 20% multiple discount on TSM for
  the Taiwan tail; substitutable-capacity thesis "implausible through 2028"
  (HIGH, ENT[TSM]); wave estimate 7%/12mo kinetic probability with CATASTROPHIC
  cascade.

### Tier 4 -- Chip Design (Compute, Custom Silicon, Networking Silicon)

| Node | Companies | Role | Key dependencies |
|---|---|---|---|
| Merchant accelerators | NVDA | system-level integrator; FY26 revenue $215.9B +65%, GAAP GM 75.0%; Q1-FY27 guide $78B +/-2% (SEC 8-K Feb 25 2026, HIGH); 85% AI compute share (NVDA via ref-supply-chain-dependency) | TSM N3/N4 wafers (#1 customer ~19-22%); CoWoS-L >50% booked through 2027 (HIGH); SK hynix/Micron HBM ('One Team' >50%); four direct customers = 61% of Q3-FY26 revenue (10-Q, up from 34% Q1-FY25) |
| Challenger accelerator + server CPU | AMD | MI350/EPYC growth drivers; MI450/Helios 2H-2026 guided-not-booked; MI455X HBM4 rides SAMSUNG (MEDIUM); CoWoS allocation ~105K wafers 2026 = 11% of demand vs NVDA ~60% (amd-analysis in ENT[TSM]) | TSM wafers + allocation queue; Samsung HBM4 (direct exposure to binding memory layer); Alibaba MI308 order 40-50K units @192GB HBM3 (Reuters, HIGH); Oracle 50K MI450 Q3-26 |
| Custom XPU house #1 | AVGO | six named hyperscaler XPU customers: Google Ironwood TPU v7 + partial Meta MTIA + ByteDance + unnamed $10B 4th + OpenAI 10GW + unspecified; Q1-FY26 AI revenue $8.4B +106%; $73B AI backlog disclosed (8-K Mar 4 2026, HIGH) | TSM wafers + CoWoS; custom-ASIC HBM demand +82% YoY 2026 -> ~1/3 of HBM market per Goldman (ENT[AVGO]); Anthropic 1GW->3.5GW TPU facilitation |
| Custom XPU house #2 | MRVL | Amazon Trainium anchor (Project Rainier live Oct 29 2025, ~500K Trainium2 scaling >1M by year-end; Trainium3 first 3nm AI accelerator shipping); 400G->800G->1.6T optical DSP curve; datacenter 76% of FQ1-FY27 revenue | TSM 3nm + CoWoS; MU/SKH HBM; single-program concentration (Trainium) |
| Server/mobile CPU | INTC | foundry turnaround + CPU; 18A ramp 2025-26 with external-customer traction unresolved; Intel-NVIDIA custom DC/PC collaboration with NVLink announced Q3-FY26 (ENT[INTC]) | own fabs (the only IDM in tier); still loss-making (-$11.0B NI LQ, FIN) |
| Mobile/auto SoC, DC entry | QCOM | mobile annuity flattening (-4.0% YoY, FIN); Snapdragon Ride + Dec-2025-reported hyperscaler custom-chip entry (TrendForce via ENT[QCOM]) | TSM trailing nodes; hyperscaler custom-program optionality |

Key dependencies:
- Everything in this tier funnels through exactly two upstream gates: TSM
  fabrication (Tier 3) and SNPS/CDNS/ARM tooling (Tier 2).
- Displacement vector: custom silicon (TPU v7 + Trainium 3 + Maia 200 + MTIA)
  growing 44.6% CAGR displaces merchant GPUs toward ~75% share by late 2026
  (AMD via NVDA risks); counterweight AMD-Meta $60B MI450 deal +
  MI455X parity (NVDA).
- Vendor-financing circularity: ~$1.15T OpenAI-linked commitment chain across
  Broadcom $350B / Oracle $300B / MSFT $250B / NVDA $100B / AMD $90B, >$800B
  estimated circular; WSJ reported the NVDA tranche "stalled" Feb-2026
  (challenge-thesis-theme-alpha-2026-07-10 on ENT[NVDA]).

### Tier 5 -- Assembly / Test / Packaging

| Node | Companies | Role | Key dependencies |
|---|---|---|---|
| Advanced packaging (CoWoS) | TSM (advanced-packing arm) | THE system-level binding constraint: 75-80K wafers/month exiting 2025 targeting 120-130K end-2026 (HIGH, ENT[TSM]); sold out >1yr; NVDA CoWoS-L >50% booked through 2027 | ONTO inspection/metrology tools; ABF substrates (Tier 0); KLAC hybrid-bonding process control; every accelerator and XPU queues here |
| Packaging metrology/instruments | ONTO | pure-play instrument beneficiary of the CoWoS bottleneck ($343M LQ, +35.3%; vol21 113.3%) | CoWoS expansion schedule |
| Hybrid bonding process control | KLAC | intensity rises with hybrid-bonding adoption | same |
| Optical-module assembly | FN (Fabrinet) | NVIDIA optical-module assembly partner; also assembles for Coherent + Lumentum; $1.3B LQ +44.6% | COHR/LITE components; NVIDIA platform decisions (63d -37.9% shows the concentration whiplash) |
| Traditional OSAT | ASE, Amkor (not in corpus) | commodity test/packaging | substitutable within layer on 1-3yr horizons (DERIVED) |

Key dependencies:
- CoWoS capacity is where chip demand becomes physical product. Every GPU, XPU,
  and HBM stack passes through advanced packaging concentrated in one geography.
- The two most falsifiable chokepoint metrics in the whole chain live here:
  CoWoS wafers/month and EML laser supply-demand balance (corollary section 10,
  [[ref-semiconductor-value-chain]]).

### Tier 6 -- System Integration (Servers, Fabrics, Optics, Copper)

| Node | Companies | Role | Key dependencies |
|---|---|---|---|
| AI server OEMs | DELL | Q4-FY26 AI-server revenue $8.95B +342%; FY27 AI-server target $50B; $43B AI backlog entering FY27 (247wallst via ref-ai-supply-chain-deep-dive on ENT[DELL]) | NVDA/AMD silicon allocation; hyperscaler credit (thin margins: NI 5.3% TTM, FIN) |
| AI server OEMs | HPE | Cray/Apollo HPC + Juniper networking (merger closed 2025); Q2-FY26 guide $9.6-10B | same |
| Liquid-cooled specialist | SMCI | ~40-50% AI server share 2024 (Mizuho est., MEDIUM); LQ $10.2B +122.7%; legal/accounting overhang lingering | GB200 rack allocations; governance risk |
| Switch systems (Ethernet) | ANET | merchant Ethernet switching on AVGO silicon; AI networking $1.5B (2025) -> $3.25B guided (2026) = 2.17x; total guide $11.25B +25%; Ethernet taking InfiniBand fabric share | AVGO Tomahawk/Jericho silicon; MSFT/META cloud-titan concentration; memory-driven cost inflation flagged in its own 2026 guide |
| Incumbent systems | CSCO | discipline anchor, fwd P/E ~16x; re-crossed dot-com peak only 2025-12-10 | campus/enterprise mix |
| Transceivers | COHR | ~25% transceiver share; NVIDIA 800G procurement ~20% wallet; top-5 suppliers ~50% of 2025 transceiver revenue (all ENT[COHR] via ref-ai-supply-chain-deep-dive); named NVIDIA silicon-photonics collaborator for Spectrum-X | LITE EML lasers inside every 200G/lane lane; Innolight/Chinese module competition |
| EML lasers | LITE | 50-60% global EML share; 200G/lane EML demand EXCEEDS SUPPLY by 25-30% (ENT[LITE]) -- gating input on the entire 800G->1.6T transition | cloud/datacom 50.2% of FY25 revenue ($1.85B of $3.69B); Q2-FY26 guide $630-670M |
| Connectors/cable assemblies | APH | IT-datacom 41% of revenue, +99% YoY AI-driven; Q1-26 orders $9.4B, book-to-bill 1.24; CommScope/Andrew closed Q1-26 | within-rack copper + interconnect content per generation |
| Within-rack copper | CRDO | ~75% AEC share; ~200% YoY revenue at profiling; NI margin 35.4% TTM; insider selling pattern noted (35 Form-4s, all sells) | NVLink-generation rack architectures |
| Optical DSP | MRVL | 400G->800G->1.6T ladder second engine | hyperscaler optical roadmaps |

Key dependencies:
- Speed-transition frame: each speed doubling (400G->800G->1.6T) shifts the
  optics boundary deeper into the rack -- why CRDO (AEC) and LITE (EML) are the
  highest-growth lines ([[ref-datacenter-infrastructure]] S3 synthesis).
- Profit pool sits upstream (GPUs) and around (power/cooling), not in assembly:
  DELL 5.3% / HPE 4.0% / SMCI 3.7% net margins TTM (FIN).
- Whole section is levered to a handful of platform decisions per year (NVIDIA
  wallet-share claims at COHR/FN/CRDO; six XPU programs at AVGO/MRVL).

### Tier 7 -- Data Center Operations

| Node | Companies | Role | Key dependencies |
|---|---|---|---|
| Hyperscalers | MSFT, GOOGL, AMZN, META | 2026 capex: AMZN $200B, GOOGL $175-185B, META $115-145B, MSFT ~$150B annualized (NVDA catalysts); Big-4 ~$640B confirmed across all four prints (TSM); $725B total per NVDA; $750B +67% incl. Oracle $50B per MU -- rising band, different capture dates | everything above; grid interconnection queues 5-7 YEARS structural (VRT/ETN) |
| Oracle (neo-hyperscale) | ORCL | RPO $638B +363% YoY; OCI +93% to $5.8B Q4-FY26; FY27 guide ~$90B; BUT FCF -$23.7B FY26 on $55.7B capex, debt $108B -> $124B trajectory, ~$300B (~47%) of RPO estimated tracing to OpenAI (BofA est.) | NVDA/AMD allocation; IG credit access |
| Neo-clouds | CRWV, NBIS | CRWV: contracted backlog $66.8B, 2026 guide $12-13B, capex $30-35B, 850MW active end-2025 targeting >1.7GW end-2026, NVIDIA $2B strategic investment Jan-2026; NBIS: TTM rev $873.5M +442%, deferred revenue $4.78B = 5.4x TTM, Altman Z 2.29 GREY | GPU supply; debt/prepayment financing constructs |
| Colo REITs | DLR, EQIX | DLR: record 2025 bookings $1.2B, AI-ready capacity ~60% rate premium ($150-200/kW/mo vs $100-120 hist.), vacancy 1.4%, 92% of construction pre-committed; EQIX: xScale JV off-balance-sheet shells, Baa1 upgrade 2026-03-05 | bypass risk: hyperscaler self-build (Microsoft 2GW cancellation precedent, MEDIUM) |
| Power + cooling | VRT, ETN, GEV | VRT: backlog $15.0B +109% YoY, book-to-bill ~2.9x, Q4 organic orders +252%, air-cooling caps ~30-40kW/rack vs GB200 NVL72 ~120kW forcing liquid (HIGH/MEDIUM); ETN: backlog $22.8B, DC orders +240% Q1, Boyd Thermal $9.55B acquisition; GEV: total backlog $163.3B (vs $123.4B YoY), gas slot reservations 83 -> 100 GW Q1-26 expecting 110 GW YE-26, $2.4B DC equipment orders Q1-26 alone > all of 2025 (all HIGH) | transformer/switchgear lead times; interconnection queues monetize THEIR pricing power while capping DC energization |
| Firm power / IPPs | CEG, VST, TLN, NRG | CEG: Microsoft Crane 837MW 20-yr PPA ~$16B life-of-contract, TMI restart capex $1.6B, Calpine closed 2026-01-07 -> ~55GW fleet; VST: AWS Comanche Peak 1,200MW + Meta 2,609MW PJM nuclear PPAs (~3,800MW total); TLN: AWS Susquehanna 1,920MW PPA through 2042, ~$18B contract life; NRG: ERCOT co-location pipeline | implied PPA clearing band ~$70-120/MWh [DERIVED, 92% CF assumption] vs wholesale baseload historically $30-50s -- the spread IS the nuclear premium |
| Grid utilities | AEP, PPL, DUK, SO, NEE | AEP $54B+ 2026-2030 capex ~75% T&D, central PJM DC planner; PPL Susquehanna footprint; SO Vogtle new-build experience; rate-base capture | regulatory cycles; load growth currently dominating duration (RATE betas near zero or positive over Sep-24..Aug-26 window) |
| Storage/BESS | FLNC | $3B+ multi-year backlog; peak-shaving + UPS-replacement vectors; distressed multiple (-64.8% off high) | CATL/BYD cost pressure; IRA 45X phase-out |

Key dependencies:
- The binding constraint has MOVED FROM CHIPS TO ELECTRONS: GEV+ETN backlog
  growth (32% and record levels) is the cleanest leading indicator
  ([[ref-energy-power-complex]] S2 synthesis).
- Buyer-side stress signal: FM1 resolution window showed MSFT Azure +43% CC with
  capex HELD and META RAISING FY26 capex ~$136.7B while the MARKET punished the
  buyer (-7.4%) and rewarded arms dealers (TSM thesis-fit log).
- Financing fragility concentrates at Tier 7: ORCL leverage trigger ~0.2x away
  from downgrade, NBIS grey-zone Altman Z, CRWV negative margins -- the demand
  engine itself runs on credit.

---

## Bottleneck Scores

Scale: 1 = trivially replaceable/unconstrained, 10 = monopoly-grade constraint.
Time-to-replace is expressed as a score where 10 = decade-scale, 1 = months.
Current utilization reflects corpus-stated sold-out/backlog states (DERIVED from
cited claims; no direct utilization telemetry exists in the vault -- treat as an
order-of-magnitude read, not a measurement).

Scores are DERIVED judgments anchored to the graded claims listed in the map
above; ranking judgment follows Section 10 of [[ref-semiconductor-value-chain]]
and the chokepoint register of ref-supply-chain-dependency.

| # | Node (owner) | Irreplaceability | Capacity-constraint severity | Time-to-replace | Current utilization | Composite (avg) |
|---|---|---|---|---|---|---|
| 1 | EUV litho (ASML) | 10 -- sole supplier, decade moat | 9 -- EUR 38.8B backlog, High-NA EUR 350M+/tool | 10 -- no substitute path visible | 8 -- booked out through guidance horizon | 9.25 |
| 2 | Leading-edge foundry + CoWoS (TSM) | 10 -- 70-80% advanced nodes; substitution implausible thru 2028 | 10 -- CoWoS 75-80K wpm vs 120-130K target, sold out >1yr | 9 -- multi-site multi-year, unproven | 9 -- every accelerator queues here | 9.50 |
| 3 | HBM supply (SKH/Samsung/MU trio) | 8 -- three sources exist but CY26 allocation locked | 9 -- CY26 locked; Stargate pull ~40% of global DRAM | 7 -- new fabs 3-5yr + EUV gated | 9 -- conventional DRAM margins surpassing HBM (cycle-top hallmark flagged) | 8.50 |
| 4 | EDA duopoly (SNPS+CDNS) | 9 -- combined ~73-74%, nothing ships without them | 6 -- software, scales with compute not fabs | 10 -- decade-scale switching cost | 5 -- utilization n/a; risk is design-start deceleration not saturation | 7.50 |
| 5 | EML lasers (LITE) | 8 -- 50-60% share at 200G/lane | 9 -- demand exceeds supply 25-30% | 6 -- capacity adds possible in 12-24mo | 10 -- explicit shortage stated | 8.25 |
| 6 | Merchant accelerator ecosystem (NVDA) | 7 -- silicon replaceable, CUDA/software layer not quickly | 8 -- top-4 customers 61% of revenue fight for allocation | 6 -- ASIC displacement path exists (44.6% CAGR) | 8 -- $62.3B quarterly DC revenue run-rate | 7.25 |
| 7 | Custom XPU co-design (AVGO) | 6 -- per-program replaceable over 2-3yr, aggregate not | 7 -- $73B AI backlog, six programs live | 5 | 8 -- line of sight to $100B AI chips 2027/28 | 6.50 |
| 8 | Arm ISA royalties (ARM) | 7 -- Graviton/Cobalt/Axion all license one ISA | 5 | 6 -- x86/RISC-V per-workload alternatives | 5 | 5.75 |
| 9 | Broadline WFE (AMAT/LRCX/KLAC/ONTO) | 5 -- multiplexed vendors per step except niches | 7 -- riding $135B CY26 WFE, backlog thru 2027-28 | 4 -- several vendors per process step | 8 -- order books full; second-derivative risk | 6.00 |
| 10 | ABF substrates / packaging materials | 8 (structural, Ajinomoto-class sole sourcing) | 7 -- gates CoWoS expansion physically | 7 | 8 [DERIVED, low corpus visibility -- DATA GAP] | 7.50 |
| 11 | AI server OEMs (DELL/HPE/SMCI) | 2 -- fungible integrators | 5 -- constrained by GPU allocation not own capacity | 2 -- months to switch vendor | 8 -- DELL $43B backlog; thin margins show zero pricing power | 4.25 |
| 12 | Ethernet switching systems (ANET/CSCO) | 4 -- merchant silicon inside, systems swappable | 5 | 3 | 7 | 4.75 |
| 13 | Optics modules (COHR/FN) | 4 -- top-5 vendors ~50% share, competition real | 7 -- 800G transition absorbing supply | 4 | 8 | 5.75 |
| 14 | Within-rack copper (CRDO/APH) | 5 -- CRDO 75% AEC share is real but socket-contestable | 6 | 4 | 8 | 5.75 |
| 15 | Colo space (DLR/EQIX) | 5 -- scarcity premium real but self-build bypass documented | 6 -- vacancy 1.4%, 92% pre-committed | 4 | 8 | 5.75 |
| 16 | Power + cooling equipment (VRT/ETN/GEV) | 6 -- Boyd Thermal consolidation, few qualified suppliers | 9 -- backlogs 109-109%+ YoY, 2.9x book-to-bill | 6 -- capacity expansion underway | 9 | 7.50 |
| 17 | Firm clean power (CEG/VST/TLN nuclear fleets) | 8 -- existing nuclear irreplaceable fast; SMRs post-2030 only | 9 -- 20-yr PPAs signed years ahead; queues 5-7yr | 9 -- grid + nuclear timelines are structural | 9 -- contract books fully committed into 2030s | 8.75 |
| 18 | Grid delivery (AEP/PPL/DUK/SO/NEE) | 6 -- franchise monopolies locally | 8 -- PJM queue concentration | 8 -- transmission build is decade-scale | 7 | 7.25 |

Composite ranking (chokepoints first):

```
1. TSM foundry + CoWoS ............ 9.50   <- blast radius x absence of substitute
2. ASML EUV ....................... 9.25   <- compounds with #1 (Taiwan-tail event hits both)
3. Nuclear firm power ............. 8.75   <- the NEW chokepoint (moved from chips to electrons)
4. HBM trio ....................... 8.50
5. LITE EML lasers ................ 8.25
6. EDA duopoly .................... 7.50
7. ABF substrates ................. 7.50   [low corpus visibility]
8. Power/cooling equipment ........ 7.50
9. Grid delivery .................. 7.25
10. NVDA ecosystem ................ 7.25
```

Chokepoints 1+2 compound: TSMC is simultaneously ASML's first High-NA volume
customer AND the only outlet for the designs -- a Taiwan-tail event hits edges
1, 2, and 7 at once (a small tail hedge is one possible response,
per tsm-analysis-2026-04-30).

---

## ASCII Dependency Diagram

Full-chain flow, Tier 0 -> Tier 7. Arrows read "feeds / enables".

```
                          TIER 0  RAW MATERIALS
    [Si wafers] [photoresists] [gases] [CMP] [ABF SUBSTRATE] [rare earths]
         |            |           |       |         |
         v            v           v       v         v
    =====================================================================
                              TIER 1  EQUIPMENT
    [ASML: sole EUV / High-NA]----+----(Zeiss-class optics web upstream)
    [AMAT broadline dep/etch]     |
    [LRCX memory-weighted etch]   |   demand: TSM capex $60-64B FY26
    [KLAC metrology/process ctl]  |         + memory IDM capex ~$65B 2026
    [ONTO adv-pkg metrology]      |         + industry WFE ~$135B CY26
         |                        |
         v                        v
    =====================================================================
                    TIER 2  DESIGN / IP / EDA                TIER 3  FABRICATION
    [SNPS ~38%][CDNS ~36%]  EDA duopoly               [TSM: 70-80% advanced nodes]
         |             |        |                      |   N2 Q4-25, N2P/A16 H2-26
         |   every tape-out     |                      |   CoWoS: 75-80K wpm -> 120-130K
         +------+------+--------+                      |   sold out >1yr
                |                                      |
    [ARM ISA: Graviton/Cobalt/Axion]                   v
                |                            +---------------------------+
                |                            | LEADING-EDGE WAFERS       |
                |                            +---------------------------+
                |                                      |
    ============|======================================|==================
                v                                      v
                          TIER 4  CHIP DESIGN
    [NVDA 85% AI compute share]---needs--->[HBM: SKH One Team>50% of NVDA]
    [AMD MI450/Helios]------------needs--->[Samsung HBM4 for MI455X]
    [AVGO 6 XPU customers,$73B bklog]      [MU: CY26 locked, TAM $35B->$100B]
    [MRVL Trainium + 1.6T DSP]             [Stargate pull ~900K DRAM wpm]
    [INTC 18A turnaround][QCOM DC entry]   (~40% of global DRAM)
         |                                      ^
         |  all designs funnel back down:       |
         +-------------------> TIER 3 <---------+
                                (fab + HBM stacking)
         |
         v
    =====================================================================
                          TIER 5  ASSEMBLY / TEST / PACKAGING
              +-----------------------------------------------+
              | TSM CoWoS / CoWoS-L (NVDA >50% booked thru'27)|
              | AMD allocation ~105K wafers 2026 (11%)        |
              | ONTO + KLAC instruments; ABF substrates below |
              +-----------------------------------------------+
         |                         |
         v                         v
    [FN optical-module assembly]   [traditional OSAT: ASE/Amkor]
         |
         v
    =====================================================================
                          TIER 6  SYSTEM INTEGRATION
    SERVERS: [DELL $43B AI backlog][HPE Cray+Juniper][SMCI liquid-cooled]
    FABRICS: [ANET AI-net $1.5B->$3.25B][CSCO] on [AVGO Tomahawk6/Jericho3-AI]
    OPTICS:  [COHR ~25% share]<--EML lasers--[LITE 50-60% share, SHORT 25-30%]
    COPPER:  [CRDO AECs ~75% share][APH connectors, B2B 1.24]
         |
         v
    =====================================================================
                          TIER 7  DATA CENTER OPERATIONS
    BUYERS:  [MSFT][GOOGL][AMZN $200B][META $115-145B] capex $640-750B band
             [ORCL RPO $638B][CRWV bklg $66.8B][NBIS prepaid 5.4x TTM]
    SPACE:   [DLR vacancy 1.4%][EQIX xScale]
    POWER:   [VRT $15B bklg, BB 2.9x][ETN $22.8B bklg][GEV $163.3B bklg]
    FIRM MW: [CEG MSFT 837MW/$16B][VST AWS+Meta 3.8GW][TLN AWS 1.92GW/$18B]
             [NRG ERCOT]  <-- PPA clearing ~$70-120/MWh [DERIVED]
    GRID:    [AEP $54B plan][PPL][SO Vogtle][NEE]
```

Feedback loops the diagram makes visible:

```
LOOP A (capex flywheel, the demand engine):
  Tier 7 budgets --> Tier 4 orders --> Tier 3 wafers --> Tier 1 tool orders
  --> Tier 3 capacity --> more Tier 4 product --> more Tier 7 builds
  QUANTIFIED: $640-750B hyperscaler capex -> TSM $60-64B + memory $65B
  -> WFE $135B CY26.

LOOP B (memory spiral, cycle-top watch):
  AI packaging -> HBM demand -> DRAM ASP shock (MU rev +345.7% YoY LQ)
  -> conventional DRAM margins surpass HBM (flagged cycle-top hallmark)
  -> IDM capex surge ($65B) -> 2027-28 synchronized oversupply risk 35%
  (wave1-MU probability).

LOOP C (electron gate, the moved constraint):
  Every rack built needs firm MW -> interconnection queues 5-7yr ->
  nuclear PPAs 16-20yr tenors at $70-120/MWh -> power equipment backlogs
  explode (GEV $163.3B, ETN $22.8B, VRT $15B) -> DC energization pace,
  NOT chip supply, now sets how fast Tier 7 capex converts to revenue.

LOOP D (custom-silicon displacement):
  Hyperscalers design own silicon (TPU/Trainium/Maia/MTIA) -> AVGO/MRVL
  win the sockets -> erodes NVDA merchant share 80-90% -> ~75% by late 2026
  -> but ALL of it still fabs at TSM and still eats HBM and still tapes
  out through SNPS/CDNS -- displacement moves profit pools, not chokepoints.

LOOP E (vendor-financing circularity, the fragile edge):
  OpenAI commitments: AVGO $350B / ORCL $300B / MSFT $250B / NVDA $100B /
  AMD $90B ~= $1.15T chain, >$800B circular. NVDA tranche reported
  "stalled" Feb-2026. A default anywhere propagates to Tier 4 revenue
  recognition and Tier 7 credit spreads simultaneously.
```

Interruption propagation rule: an outage at any single-box layer propagates to
everything downstream; the graph's narrowest boxes are TSM (fab + CoWoS), ASML
(EUV), the HBM trio, LITE (EML), the EDA duopoly, and (newly) firm clean power.

---

## Quantified Edges

Every edge below carries a dollar/wafer/megawatt figure traced to the cited
entity note or reference. Bands reflect different capture dates, not
contradictions (per caveats in ref-supply-chain-dependency).

### Edge 1: Hyperscaler budgets -> accelerator demand (THE revenue edge)

| Edge | Magnitude | Source |
|---|---|---|
| AMZN 2026 capex | $200B | ENT[NVDA] catalysts |
| GOOGL 2026 capex | $175-185B | ENT[NVDA] catalysts |
| META 2026 capex | $115-145B (FY26 raised ~$136.7B) | ENT[NVDA]; TSM thesis-fit log |
| MSFT 2026 capex | ~$150B annualized | ENT[NVDA] catalysts |
| Big-4 aggregate | ~$640B confirmed across 4 prints; $725B total per NVDA; $750B +67% YoY incl. Oracle $50B per MU | band, see above |
| NVDA revenue conversion | FY26 $215.9B +65%; Q4-FY26 DC revenue $62.3B +75%; Q1-FY27 guide $78B | SEC 8-K Feb 25 2026 via ENT[NVDA], HIGH |
| NVDA concentration | top-4 customers = 61% of Q3-FY26 revenue (from 34% in Q1-FY25); kill criterion: 2 consecutive hyperscaler capex cuts | 10-Q basis, ENT[NVDA] |
| AMD counterweight | Meta $60B MI450 deal; Alibaba MI308 40-50K units @192GB HBM3; Oracle 50K MI450 Q3-26 | Reuters HIGH; ENT[AMD] |

### Edge 2: Foundry capex -> equipment orders

| Edge | Magnitude | Source |
|---|---|---|
| TSM FY26 capex | $60-64B (raised 30%+ -> 40%+ from $52-56B at 2026-07-16 Q2 print) | ENT[TSM], HIGH |
| TSM revenue guide | FY26 raised to 40%+ growth; Q1-26 rev $35.9B +40.6% @66.2% GM record | ENT[TSM] via ref-theme-alpha, HIGH |
| Memory IDM capex 2026 | ~$65B aggregate: SK hynix $20.5B + Samsung $20B + Micron ~$20B + Kioxia/SanDisk $4.5B | LRCX/AMAT per memory-storage deep dive |
| Industry WFE CY2026 | ~$135B from ~$110B 2025 (+23%) | LRCX guide, HIGH |
| ASML bookings/backlog | Q4-25 bookings EUR 13.2B (EUR 7.4B EUV); YE backlog EUR 38.8B; 2026 guide EUR 36-40B | ENT[ASML] via ref-theme-alpha, HIGH |
| SK hynix EUV buy | ~$8B for ~30 EUV systems by Dec-2027 | ENT[ASML] |
| High-NA tool price | EUR 350M+/tool, TSMC first volume customer | ENT[ASML], HIGH |
| MU own capex | FY26 raised $20B -> $25B (Mar 18 2026 call); 9-month FY26 $19.6B +92.2% YoY; capex/revenue 42.4% FY25 | ENT[MU]; FIN-S4 |
| SK hynix total commitment | $410B cited as demand engine | LRCX wave file |

### Edge 3: Chips -> memory (HBM)

| Edge | Magnitude | Source |
|---|---|---|
| HBM TAM | $35B 2025 -> $100B 2028 (Micron disclosure, +40% CAGR pulled forward 2 yrs); BofA $54.6B CY26 | ENT[MU], HIGH |
| Custom-ASIC HBM demand | +82% YoY 2026 -> ~1/3 of HBM market (Goldman est.) | ENT[AVGO] |
| MU revenue inflection | quarterly ladder ... 13.6 -> 23.9 -> 41.5 $B; ASP-driven vertical takeoff, bit growth low-to-mid single digits | FIN[MU] S2 |
| NVDA pricing pass-through | NVDA flat GM through sharpest memory-price shock on record reads as Micron pass-through pricing power | ref-theme-alpha 2026-07-16 on ENT[NVDA] |
| Demand concentration | OpenAI Stargate ~900K DRAM wafers/month ~= 40% of global DRAM | Samsung insert, memory-storage ingest |
| AMD HBM exposure | MI455X HBM4 rides Samsung = direct exposure to binding layer; MI400 432GB HBM4 ladder | ENT[AMD], MEDIUM |

### Edge 4: Packaging bottleneck

| Edge | Magnitude | Source |
|---|---|---|
| CoWoS capacity ramp | 75-80K wafers/month exiting 2025 -> 120-130K target end-2026; sold out >1yr | ENT[TSM], HIGH |
| NVDA CoWoS-L lock | >50% booked through 2027 | ENT[NVDA], HIGH |
| AMD CoWoS allocation | ~105K wafers 2026 = 11% of demand vs NVDA ~60% | amd-analysis-2026-04-30 in ENT[TSM] |

### Edge 5: Custom silicon -> design services/IP

| Edge | Magnitude | Source |
|---|---|---|
| AVGO AI backlog | $73B disclosed (8-K Mar 4 2026); management "line of sight" to $100B AI chip revenue 2027/28 | HIGH / MEDIUM |
| AVGO AI revenue | Q1-FY26 $8.4B +106% YoY; six XPU customers incl. OpenAI 10GW (first-gen deliveries late 2026, up to $300B revenue potential) | ENT[AVGO] extended log |
| MRVL anchor program | Project Rainier live Oct 29 2025: ~500K Trainium2 scaling >1M by year-end; Trainium3 first 3nm AI accelerator shipping; datacenter 76% of FQ1-FY27 revenue | ENT[MRVL] |
| EDA scale | SNPS FY-guide era LQ $2.3B +41.9%; CDNS FY24 $4.64B +13%, FY25 guide ~$5.23B; combined ~73-74% share | FIN; ENT[CDNS] |
| Displacement CAGR | custom silicon growing 44.6% CAGR toward ~75% compute share by late 2026 | AMD via NVDA risks |

### Edge 6: Networking/optics speed transition

| Edge | Magnitude | Source |
|---|---|---|
| ANET AI networking | $1.5B (2025) -> $3.25B (2026 guided) = 2.17x; total guide $11.25B +25% | ENT[ANET], HIGH |
| LITE EML shortage | 200G EML demand exceeds supply by 25-30%; cloud/datacom 50.2% of FY25 revenue ($1.85B) | ENT[LITE] |
| COHR NVIDIA wallet | 800G procurement ~20% of NVIDIA wallet; top-5 transceiver suppliers ~50% of 2025 revenue | ENT[COHR] via ref-ai-supply-chain-deep-dive |
| CRDO growth | ~200% YoY at profiling; ~75% AEC share; LQ $437M +157% | FIN; crdo analysis |
| APH orders | Q1-26 $9.4B, book-to-bill 1.24; IT-datacom 41% of revenue +99% YoY | ENT[APH], corrections logged |
| AVGO SerDes roadmap | 200G -> 400G in 2028, co-packaged optics beyond | ENT[AVGO], MEDIUM |
| Tomahawk 6 | 102 Tb/s switching silicon capturing hyperscale fabric | ref-supply-chain-dependency register #7 |

### Edge 7: Servers/racks -> buildings

| Edge | Magnitude | Source |
|---|---|---|
| DELL AI backlog | $43B entering FY27; FY27 AI-server target $50B; Q4-FY26 AI server rev $8.95B +342% | 247wallst via deep-dive on ENT[DELL] |
| VRT backlog | $15.0B +109% YoY; book-to-bill ~2.9x; Q4 organic orders +252%; 2026 guide $13.25-13.75B | Vertiv 8-K Feb 11 2026, HIGH |
| ETN backlog | $22.8B, ~68% deliverable within 12mo; DC orders +240% Q1; Boyd Thermal $9.55B acquisition | ENT[ETN], HIGH |
| GEV backlog | $163.3B total (vs $123.4B YoY); gas slots 83 -> 100 GW Q1-26 -> 110 GW YE-26 expected; $2.4B DC equipment orders in Q1-26 alone > all of 2025 | ENT[GEV], HIGH |
| Rack density forcing | air-cooling caps ~30-40 kW/rack; GB200 NVL72 ~120 kW forces direct-to-chip liquid | ENT[VRT], MEDIUM/HIGH |

### Edge 8: Buildings -> electrons

| Edge | Magnitude | Source |
|---|---|---|
| Interconnection queues | 5-7 YEARS structural | ENT[VRT]/ENT[ETN], structural |
| CEG-Microsoft Crane | 837MW, 20-yr PPA, ~$16B life-of-contract; restart capex $1.6B; Calpine closed -> ~55GW fleet | ENT[CEG], HIGH |
| VST contracts | AWS Comanche Peak 1,200MW 20-yr + Meta 2,609MW PJM nuclear (~3,800MW total); Cogentrix $4.7B adds 5,500MW gas | ENT[VST], HIGH |
| TLN-AWS | Susquehanna 1,920MW PPA through 2042, ~$18B revenue over contract life | ENT[TLN], HIGH |
| Implied PPA price band | ~$70-120/MWh [DERIVED at 92% CF] vs wholesale baseload historically $30-50s | energy-power complex S1.2 |
| AEP grid capex | $54B+ 2026-2030, ~75% T&D, central PJM DC planner | ENT[AEP], HIGH |
| OKLO/Meta timeline | Pike County 1.2GW: pre-construction 2026, first phase 2030, full 1.2GW by 2034 -- SMR relief arrives post-2030 only | ENT[OKLO], HIGH |

### Edge 9: Downstream financing constructs (demand-engine fragility)

| Edge | Magnitude | Source |
|---|---|---|
| ORCL RPO | $638B +363% YoY; ~$300B (~47%) estimated tracing to OpenAI; FCF -$23.7B FY26; debt $108B -> $124B | orcl-analysis-2026-06-12, Grade A; BofA est. |
| CRWV backlog | $66.8B contracted; capex $30-35B 2026; NVIDIA $2B strategic investment Jan-2026 | CRWV Q4-25 call via deep-dive |
| NBIS prepayments | deferred revenue $4.78B = 5.4x TTM revenue; first covenant debt $775M (SOFR+250, DSCR 1.15) | nbis-analysis-2026-07-29, Grade A EDGAR |
| OpenAI commitment chain | ~$1.15T across AVGO $350B / ORCL $300B / MSFT $250B / NVDA $100B / AMD $90B; >$800B circular; NVDA tranche "stalled" Feb-2026 | challenge-thesis-theme-alpha-2026-07-10 on ENT[NVDA] |
| DLR/EQIX funding | DLR ~5.1x net-debt/EBITDA; EQIX Baa1 upgrade 2026-03-05 validates buildout financing | ENT[DLR] MEDIUM; ENT[EQIX] |
| Cascade sizing | "NVDA -15% would drag AMD -8-10% and semiconductor ETFs -2-4%" | NVDA risk-cascade anchor |

### Edge magnitudes at a glance (one-line ledger)

```
$640-750B   hyperscaler 2026 capex band (capture-date dependent)
 $215.9B    NVDA FY26 revenue (+65%)
  $135B     industry WFE CY26 (+23% YoY)
  $73B      AVGO AI backlog alone
  $64B      TSM FY26 capex ceiling
  $65B      memory IDM capex aggregate 2026
  $43B      DELL AI-server backlog
  $35B->$100B  HBM TAM 2025 -> 2028
 $163.3B    GEV total backlog
  $38.8B    ASML year-end backlog (EUR)
  $22.8B    ETN backlog
  $15.0B    VRT backlog
  $16B      CEG-Microsoft Crane life-of-contract (~$119/MWh implied)
  $18B      TLN-AWS Susquehanna life-of-contract (~$73/MWh implied)
 $638B      ORCL RPO (~47% est. OpenAI-linked)
  $66.8B    CRWV contracted backlog
  $1.15T    OpenAI-linked commitment chain (> $800B circular)
 900K wpm   Stargate DRAM pull ~= 40% of global DRAM
 120-130K   CoWoS wafers/month target end-2026 (from 75-80K)
  5-7 yrs   grid interconnection queues (the electron gate)
 25-30%     EML laser shortfall vs demand
 61%        NVDA revenue from 4 customers
 76%        TSM revenue from top-10 customers
```

### Score justification per node (evidence anchors)

| Node | Score rationale (corpus anchor) |
|---|---|
| TSM fab + CoWoS | 70.2% foundry share Q2-25; substitution "implausible through 2028" (HIGH); CoWoS sold out >1yr with 120-130K wpm target vs 75-80K current -- the only node where BOTH capacity severity AND irreplaceability max out. Blast radius: every Tier 4 name ships from this one island. |
| ASML EUV | Sole supplier, EUR 38.8B backlog; binding constraint stated TWICE in the corpus -- on leading-edge logic (TSM N2/A16) and independently on HBM (every 1-alpha/1-beta DRAM node). No substitute path visible at any horizon the corpus discusses. |
| Nuclear firm power | The NEW chokepoint: PPAs are 16-20yr tenors signed years ahead ($16B CEG-MSFT, $18B TLN-AWS); queues 5-7yr structural; SMR relief arrives post-2030 only (OKLO Meta phase-1 2030). Existing fleets cannot be replicated on any AI-relevant timescale. |
| HBM trio | Three sources exist (why irreplaceability is 8 not 10) but CY26 allocation is locked, SKH 'One Team' >50% of NVDA, and demand concentration (Stargate ~=40% of global DRAM) means no spot relief valve. Cycle-top hallmarks already flagged -- the constraint is real but cyclical. |
| LITE EML | Only explicit supply SHORTFALL quantified in the corpus (+25-30% excess demand); every 200G/lane lane needs its lasers; but capacity adds are a 12-24mo problem, unlike EUV's decade. |
| EDA duopoly | Highest time-to-replace (decade-scale switching costs, ~73-74% combined share) but software scales elastically -- no physical saturation. Risk is design-start deceleration, which would show up as bookings, not shortages. |
| ABF substrates | Structural sole-sourcing (Ajinomoto-class film); physically gates CoWoS expansion; scored from industry structure because corpus coverage is absent -- flagged DATA GAP. |
| Power/cooling equipment | Book-to-bill 2.9x (VRT), backlogs +109%/+32% YoY (VRT/GEV); qualified-supplier concentration (Boyd Thermal $9.55B consolidation = few credible alternatives). Replaceable eventually, not inside build schedules. |
| Grid delivery | Local franchise monopolies; PJM queue concentration; decade-scale transmission builds; but utilities are many and rate-base regulated -- pricing power exists without monopoly rents. |
| NVDA ecosystem | Silicon replaceable (custom ASICs at 44.6% CAGR displacement), CUDA/software moat is not quickly; top-4 customers = 61% of revenue cuts both ways -- allocation-constrained yet buyer-concentrated. |
| AVGO XPU | Per-program switching 2-3yr; six concurrent programs make aggregate replacement implausible near-term; $73B backlog is contracted demand evidence. |
| Broadline WFE | Several qualified vendors per process step except KLAC process-control and ONTO hybrid-bonding niches (why composite splits them out below); order books full through 2027-28 but second-derivative risk -- they correct before foundry/memory P&Ls do. |
| Server OEMs | Lowest scores in the file for a reason: NI margins DELL 5.3% / HPE 4.0% / SMCI 3.7% (FIN) prove zero pricing power -- profit pool sits upstream and around, not here. |
| Colo REITs | Scarcity premium real (AI-ready ~60% rate uplift, vacancy 1.4%) but self-build bypass documented (Microsoft 2GW cancellation precedent) caps the chokepoint grade. |
| Optics modules | Top-5 vendors ~50% share with Chinese competition (Innolight) compressing module assembly -- the layer where chokepoint rents are already eroding. |

### Cross-tier dependency matrix

Rows = tier that DEPENDS on the column tier. Cell = the binding dependency
(quantified where the corpus carries a figure). "-" = no material dependency.

```
DEPENDS ON ->   T0     T1      T2      T3      T4      T5      T6      T7
T1 Equipment    optics |  --    design  fab     --      --      --      capex*
                web    |        tools   capex
T2 EDA/IP        -     |   -     --      tape-   --      --      --      --
                                              out
T3 Fab          wafer/ EUV+    EDA+    --      --      --      --      --
                gas/   WFE     ISA
                subst.
T4 Chip design   -     |   -     EDA+    wafers+ --      --      --      demand
                                      CoWoS                   signal
T5 Assembly/    subst. ONTO/   --      TSM     --      --      --      --
   Test                KLAC            CoWoS
T6 Systems       -     |   -      -     silicon+ --      pkg     --      demand
                                      HBM             (FN)
T7 DC ops        -     |   -      -      chips   racks   servers+ power+
                                                                optics  cooling

* T1's ultimate demand source is T7 budgets flowing through T3/T4 orders:
  $640-750B (T7) -> $60-64B TSM + ~$65B memory IDM (T3) -> ~$135B WFE (T1).
```

Reading rules for the matrix:

- Column T3 is densest: every tier from equipment to data centers ultimately
  hangs off fabrication capacity -- consistent with its #1 composite score.
- Column T7 appears at BOTH ends of the chain: it is the terminal buyer AND,
  via capex expectations, the origin of Tier 1 order books (the Loop A flywheel).
- T0 dependencies are structural but un-instrumented in this vault (DATA GAP);
  the substrate row is the one likely to surprise.

---

## Cascade Scenarios

Three documented propagation paths with corpus-stated magnitudes.

### Scenario A: Taiwan kinetic event (probability est. 7%/12mo, wave1-TSM)

```
TRIGGER: Taiwan strait disruption
   |
   +--> TSM fabs offline ............ ENTIRE Tier 3 leading edge gone
   |      |                            (substitutable-capacity thesis
   |      |                             'implausible through 2028')
   |      +--> NVDA/AMD/AVGO/MRVL all stop shipping (Tier 4)
   |      +--> ASML loses first High-NA volume customer;
   |             EUR 38.8B backlog re-prices (Tier 1)
   |      +--> CoWoS gone -> FN assembly starves -> optics chain halts
   |
   +--> Market impact: ~20% multiple discount ALREADY priced is the
        FLOOR case, not the shock case. A small tail hedge is one possible response.
```

### Scenario B: Memory cycle rollover (DOI checklist already 2-3/5)

```
TRIGGER: conventional DRAM margins sustain above HBM (flagged cycle-top
hallmark, Q4-25 insert) OR FY27 GM cliff/pricing roll (wave1-MU: 40% prob)
   |
   +--> MU revenue ladder reverses (7.8->...->41.5 $B run unwinds)
   |      +--> MU capex $25B FY26 becomes oversupply seed:
   |             synchronized 2027-28 oversupply risk 35%
   |      +--> LRCX (memory-weighted) takes the WFE hit first --
   |             equipment corrects BEFORE memory P&L does
   |      +--> NVDA GM finally dents if Micron pass-through breaks
   |             (flat-GM-through-shock currently reads as pass-through)
   |
   +--> SNDK/WDC decouple partially (HDD rho 0.73 max) -- archive
        demand runs its own clock
```

### Scenario C: Demand-engine credit event (the fragile edge)

```
TRIGGER: OpenAI-linked circularity snaps (>$800B circular of $1.15T chain;
NVDA tranche reported 'stalled' Feb-2026)
   |
   +--> ORCL: $300B (~47%) RPO OpenAI-linked; leverage ~0.2x from
   |      downgrade trigger; FCF already -$23.7B FY26
   +--> CRWV: negative margins, capex $30-35B against prepaid backlog
   +--> NBIS: Altman Z 2.29 GREY; serial dilution thesis open
   +--> AVGO: $73B backlog includes OpenAI 10GW tranche
   +--> NVDA: four customers = 61% of revenue; documented cascade
          "NVDA -15% drags AMD -8-10% and semiconductor ETFs -2-4%"
   |
   +--> Propagation shape: Tier 4 revenue recognition and Tier 7 credit
        spreads deteriorate SIMULTANEOUSLY -- no diversification between
        them (a concentrated book behaves like a much smaller number of independent bets,
        ref-correlation-matrix-full).
```

---

## Falsifiable Monitors

The chokepoint thesis dies if any of these resolve the wrong way:

| Monitor | Current state | Chokepoint invalidated if... |
|---|---|---|
| CoWoS wafers/month | 75-80K -> 120-130K target end-2026 | Target met early AND queue clears (sold-out ends) |
| EML supply-demand balance | Short 25-30% | Balance restored via LITE/competitor capacity adds |
| HBM allocation | CY26 locked | Spot HBM availability opens; conventional DRAM margin premium over HBM persists 2+ qtrs |
| Hyperscaler capex prints | Rising band $640-750B | Two consecutive Big-4 capex cuts = NVDA's literal kill criterion |
| NVDA customer concentration | Top-4 = 61%, kill line 45%-top-2 approaching (top-2 = 37%) | Concentration stabilizes or custom ASICs stall (<44.6% CAGR) |
| Grid interconnection queues | 5-7 years structural | Queue reform compresses timelines materially (power chokepoint weakens) |
| SMR COD dates | Post-2030 realistic band | Any SMR delivers fleet-relevant GW before 2030 (nuclear scarcity premium erodes) |
| WFE orders | ~$135B CY26 guide | Book-to-bill <1 for two quarters = ASML de-rate trigger; named-IDM capex cuts >10% |
| OpenAI commitment chain | $1.15T nominal, >$800B circular | Any tranche beyond NVDA's stalls/cancels -- check AVGO/ORCL next |
| Substrate lead times | [DATA GAP] | N/A until entity coverage lands; absence of coverage is itself the gap |

---

## Caveats and Data Gaps

- Tier 0 (raw materials/substrates) has NO entity coverage in the corpus; the
  ABF-substrate bottleneck score rests on structural reasoning, not vault
  claims. Populate via entity-note ingestion when a primary source lands.
- Utilization scores are DERIVED from sold-out/backlog statements, not measured
  utilization telemetry; treat as ordinal, not cardinal.
- Capex aggregates ($640B / $660-690B / $725B / $750B) were captured at
  different dates with different scope; treated as a rising band throughout.
- No xbrl json for ARM, ASML, CDNS, GFS, TSM, NBIS -- those revenue lines come
  from entity-note claims instead (see [[ref-financial-statements]] S7).
- Suspect-margin aggregator flags apply to MU, NVDA, SNDK, WDC rows upstream.
- Factor-store closes end 2026-08-21; later developments invisible here.
- This file maps DEPENDENCY STRUCTURE, not valuation; correlation
  quantification lives in [[ref-correlation-matrix-full]].

## Cross-references

- Semiconductor-layer detail and per-company profiles:
  [[ref-semiconductor-value-chain]].
- Edge-level dependency map with portfolio mapping:
  ref-supply-chain-dependency.
- Downstream buyers, server OEMs, neo-clouds: [[ref-datacenter-infrastructure]].
- Power/grid gating layer: [[ref-energy-power-complex]].
- Memory cycle mechanics: [[ref-memory-storage-cycle-deep-dive-ingest-2026-05-06]].
- Claim provenance: wiki/entities/tickers/<T>.md.

---

## Appendix A -- Per-Tier Financial Anchors

Revenue = latest reported quarter in corpus with YoY; NI margin = TTM (FIN basis,
[[ref-financial-statements]] conventions; suspect-margin flags carried). These
anchors let each tier's chokepoint rents be checked against its P&L.

| Tier | Name | Role | Rev/LQ | YoY | NI margin TTM |
|---|---|---|---|---|---|
| 2 EDA/IP | SNPS | EDA #1 (~31-46%) | $2.3B | +41.9% | 8.9%* (Ansys deal-accounting distortion, NI -95% YoY) |
| 2 EDA/IP | CDNS | EDA #2 (~35-36%) | FY24 $4.64B | +13% | n/a (no xbrl json) |
| 2 EDA/IP | ARM | CPU ISA royalties | n/a (no xbrl json) | -- | n/a |
| 1 Equip | ASML | sole EUV | EUR 32.7B FY25 | Q1-26 ~+66% DERIVED | n/a (no xbrl json) |
| 1 Equip | AMAT | broadline dep/etch | $9.1B | +24.8% | 30.1% |
| 1 Equip | LRCX | memory-weighted etch/dep | $6.7B | +30.0% | 31.3% |
| 1 Equip | KLAC | process control | $3.7B | +15.2% | 35.6% (tier best) |
| 1 Equip | ONTO | adv-pkg metrology | $343M | +35.3% | 13.9% |
| 3 Foundry | TSM | leading edge | $40.2B Q2-26 | +33.7% | NPM 50.5% Q1-26 (ENT) |
| 3 Foundry | GFS | specialty nodes | n/a (no xbrl json) | -- | n/a |
| 3 Memory | MU | DRAM/HBM | $41.5B | +345.7% | 55.9%* (suspect flag) |
| 3 Memory | SNDK | NAND pure-play | $9.0B | +371.6% | 56.5%* (suspect flag) |
| 3 Storage | WDC | nearline HDD | $3.7B | n/m** (derived artifact) | 72.9%* (suspect flag) |
| 4 Compute | NVDA | accelerator incumbent | $81.6B | +85.2% | 53.4%* (suspect flag; LQ print 71.5%) |
| 4 Compute | AMD | challenger | $11.5B | +50.1% | 15.6% |
| 4 Compute | INTC | IDM turnaround | $16.1B | +25.4% | -19.8% (still loss-making) |
| 4 Compute | QCOM | mobile/auto SoC | $9.9B | -4.0% | 21.0% |
| 4 Custom | AVGO | XPU co-design #1 | $22.2B | +47.9% | n/a (EBITDA 68%, ENT HIGH) |
| 4 Custom | MRVL | Trainium + DSPs | $2.4B | +27.6% | 26.5% |
| 5 Packaging | TSM CoWoS | adv packaging | (inside TSM above) | sold out >1yr | -- |
| 5 Assembly | FN | optical-module assembly | $1.3B | +44.6% | 10.2% |
| 6 Servers | DELL | AI server OEM | $43.8B | +87.5% | 5.3% |
| 6 Servers | HPE | HPC + Juniper | $10.7B | +40.0% | 4.0% |
| 6 Servers | SMCI | liquid-cooled | $10.2B | +122.7% | 3.7% |
| 6 Fabrics | ANET | Ethernet switching | $3.0B | +37.7% | 37.7% |
| 6 Optics | COHR | transceivers ~25% share | $2.0B | +33.7% | 11.3% |
| 6 Lasers | LITE | EML monopoly-adjacent | $481M (FY25Q4d lag) | -- | n/a |
| 6 Copper | CRDO | AECs ~75% share | $437M | +157.0% | 35.4% |
| 6 Connectors | APH | connectors/cables | $8.8B | +55.0% | 17.4% |
| 7 Colo | DLR | colo REIT | $1.6B | +16.2% | 21.9% |
| 7 Colo | EQIX | interconnection REIT | $2.6B | +16.4% | 15.6% |
| 7 Power eq | VRT | power + cooling | $3.3B LQ | +24.1% | 14.0% |
| 7 Grid eq | ETN | electrical equipment | $8.5B | +21.4% | 12.7% |
| 7 Turbines | GEV | gas/grid equipment | $11.1B | +21.9% | 23.0% |
| 7 Nuclear | CEG | firm power IPP | $7.5B | +23.0% | 11.1% |
| 7 Nuclear | VST | firm power IPP | $4.0B | -5.5% | 11.6% |
| 7 Nuclear | TLN | nuclear IPP | $747M | +18.6% | -5.1% |
| 7 Neo-cloud | ORCL | OCI/RPO giant | $19.2B | +20.6% | 25.4% (FCF -$23.7B FY26) |
| 7 Neo-cloud | CRWV | GPU cloud | $2.6B | +112.5% | -23.3% |

(*) aggregator suspect-margin flag -- verify against cited filing before use.
(**) WDC YoY rides a derived-Q4 artifact; level valid, growth print is noise.

Margin-gradient observation (DERIVED): net margin RISES as you move upstream
through the chokepoints and FALLS toward assembly/integration --

```
chokepoint layer        margin band      substitutable layer    margin band
ASML/KLAC/LRCX          30-36%           server OEMs             3.7-5.3%
TSM                     NPM ~50%         module assembly (FN)    10.2%
NVDA                    53-72%           transceivers (COHR)     11.3%
MU (cycle peak)         57-68%           colo REITs              15-22%

The market's chokepoint hierarchy and the P&L agree: rents concentrate
exactly where the dependency graph has single boxes.
```

---

## Appendix B -- Source Traceability

Every claim class used in this file and where to re-verify it:

| Claim class | Source key | Re-verify via |
|---|---|---|
| Quarterly revenue / margins / capex | FIN[n] | wiki/investing/filings/<T>/<T>-xbrl.json |
| Prices / returns / vol / drawdowns | TECH[n] | factors.db bars table (ends 2026-08-21) |
| Backlogs, PPAs, capacity ramps, customer shares | ENT[<T>] | wiki/entities/tickers/<T>.md (grades carried) |
| Edge structure | ref-supply-chain-dependency Sections "Edge 1-5" | regenerate per that file's header |
| Chokepoint ranking method | [[ref-semiconductor-value-chain]] Section 10 | same |
| Server/optics/colo/neo-cloud detail | [[ref-datacenter-infrastructure]] S1-S4 | same |
| Power contracts, queues, SMR timelines | [[ref-energy-power-complex]] S1-S7 | same |
| Anything labeled DERIVED | computed this session | arithmetic shown inline; assumptions stated |

GENERATED: 2026-08-25 by supply-chain dependency-graph subagent from vault refs
and entity notes only (no network, no .raw/private reads).
