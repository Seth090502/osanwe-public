---
categories:
  - wiki
type: research
created: 2026-08-24
status: complete
confidence: high
tags:
  - topic/semiconductors
  - topic/equity-research
  - topic/industry-framework
related: ["[[edu-macro-analysis]]", "[[edu-energy-power-markets]]"]
---

# Semiconductor Industry Analysis Framework (edu)

Generated: 2026-08-24
Purpose: Complete analytical framework for semiconductor equity research.
Scope: Value chain, foundry economics, memory cycles, equipment, fabless vs IDM,
advanced nodes, export controls, per-segment metrics.
Status: Education/reference corpus. Numbers are illustrative magnitudes for
teaching, not live quotes. Re-pull current data before any investment decision.

---

## 1. Industry Map and Why Structure Beats Forecasting

### 1.1 The core analytical claim

Semiconductors are not one industry; they are six or seven industries sharing
a supply chain. Each link has different:

- Capital intensity (capex as % of revenue)
- Cyclicality (revenue beta to unit demand)
- Concentration (number of credible suppliers)
- Pricing power (ability to hold ASP through a downturn)
- Customer structure (concentrated vs fragmented)

The single most common analytical error is treating "semis" as one trade.
An EDA vendor (persistent revenue) and a DRAM producer (violent cycle) can be
at opposite points of their own cycles in the same quarter.

### 1.2 Chain map with representative exposure

```
EDA SOFTWARE        IP LICENSING       FABLESS DESIGN      IDMs
Synopsys           Arm                Nvidia              Intel (logic+memory)
Cadence            Synopsys IP        AMD                 Samsung (logic+mem)
Siemens EDA        Rambus             Qualcomm            TI (analog)
                   CEVA               Broadcom            STMicro (IDM-ish)
                   SiFive             Marvell             Micron (memory IDM)
                       |                  |                   |
                       v                  v                   v
                   FOUNDRY / MANUFACTURE ----------------------------------
                   TSMC (dominant leading edge)          Samsung Foundry
                   SMIC (China trailing edge)            GlobalFoundries
                   UMC / PSMC (mature nodes)             Tower / X-FAB (specialty)
                                        |
                                        v
                   ASSEMBLY / TEST / PACKAGING (OSAT)
                   ASE, Amkor, JCET (China), Powertech
                   Advanced packaging: CoWoS at TSMC, TSMC SoIC, Intel EMIB/Foveros
                                        |
                                        v
                   EQUIPMENT (WFE = wafer fab equipment)
                   Deposition: AMAT, LRCX, TEL     Litho: ASML (EUV monopoly)
                   Etch: LRCX, AMAT, TEL           Metrology: KLA
                   CMP: AMAT                        Ion implant: AXTL
                   Test: TER, ATR (Advantest)      Socket/handler: Cohu, FormFactor
                                        |
                                        v
                   MATERIALS
                   Wafers: WOLF (defunct brand), Shin-Etsu, SUMCO, GlobalWafers
                   Gases: Linde, Air Products, AXT (compound semis)
                   Photoresist: JSR, TOK, Shin-Etsu   Masks: Toppan, DNP, Photronics
                                        |
                                        v
                   DISTRIBUTION
                   Arrow, Avnet (broadline); regional specialists
                   Direct sales dominate above ~$100M annual customer spend
```

### 1.3 Structural characteristics by segment (approximate ranges)

| Segment | Capex % rev | Gross margin | Cycle length | Concentration |
|---|---|---|---|---|
| EDA | 10-15 | 80-90 | Low (subscription) | Very high (3 players) |
| IP licensing | 15-25 | 85-95 | Low | High (Arm dominant CPU IP) |
| Fabless design | 5-20 | 40-65 | Medium-high | Fragmented by end market |
| Leading-edge foundry | 60-75 | 50-58 | Medium | Extreme (TSMC >85% advanced) |
| Mature-node foundry | 30-45 | 25-40 | High (oversupply risk) | Moderate |
| Memory (DRAM/NAND) | 50-70 (NAND higher) | -20 to +60 swing | 3-4 years classic | Oligopoly (3 DRAM firms) |
| Equipment (WFE) | 8-12 | 42-48 | High but secular growth | Very high per tool niche |
| OSAT | 20-30 | 15-25 | High | Moderate |
| Distribution | 3-6 (opex light) | 10-14 gross | Tracks book-to-bill | Duopoly broadline |

### 1.4 The two demand engines

End demand splits into structurally distinct engines; classify every company's
revenue into these before modeling:

1. **Smartphone** (~25% of industry units): mature, replacement-cycle driven,
   unit-flat but content-growing (camera, AI NPUs, modem).
2. **PC/client compute**: same dynamics as phone post-COVID normalization.
3. **Data center / AI accelerators**: the secular growth engine since 2023;
   hyperscaler capex is the single most important input variable today.
4. **Automotive**: long qualification cycles (3-5 yr), low cyclicality,
   rising silicon content per vehicle ($500 to $1,400+ per car trend).
5. **Industrial**: inventory-sensitive, high margin, multi-source qualified.
6. **IoT/consumer**: lowest margin, most commoditized.

Rule of thumb: AI data-center exposure drives multiple re-ratings; auto/
industrial exposure drives earnings stability. Portfolio construction should
mix both deliberately rather than accidentally.

---

## 2. Value Chain Deep Dive

### 2.1 EDA (Electronic Design Automation)

**What it is:** software used to design chips. Synthesis, place-and-route,
verification, simulation, signoff, manufacturing yield analysis.

**Why it matters analytically:**
- Revenue is ~70-80% recurring (time-based licenses, maintenance).
- It is a toll booth on ALL chip design activity regardless of who wins.
- Switching costs are extreme: a full-flow migration costs 1-2 years of
  engineering productivity, so customers license all three vendors' tools.

**Key metrics:**
- Backlog / remaining performance obligations (RPO) growth vs revenue growth.
- Non-GAAP operating margin (should exceed 35-40%).
- China revenue % (export-control sensitive; was ~10-15% of Cadence/Synopsys).
- Renewal rate (>95% expected).

**Moat test:** does the vendor own a step that cannot be skipped? Emulation/
hardware verification (Cadence Palladium, Synopsys ZeBu) and lithography-aware
signoff (ASML-Synopsys relationship) are the stickiest positions.

**Risk model:** EDA is the FIRST thing hit by design activity slowdowns with a
~2-4 quarter lag, but the last thing hit in absolute terms because licenses
prepaid. Watch bookings deceleration as the leading signal.

### 2.2 Semiconductor IP licensing

**Business models within IP:**
- License fee (one-time, recognized upfront) + royalty per shipped unit (2-4%
  of chip ASP typical for CPU/GPU core IP).
- Arm: ~$0.03-$0.30 per unit on low-end royalty contracts, several dollars on
  high-end server licenses plus upfront license fees in tens/hundreds of $M.
- GPU/AI accelerator IP, interface IP (SerDes, DDR PHY), foundational IP.

**Analytical frame:** value the royalty stream like a perpetual bond with unit-
growth coupling. Royalty revenue lags license bookings by 2-4 years (design
wins take that long to ship). License bookings lead; royalties lag. Model both
separately.

**Key metrics:** royalty units (Arm reports chips shipped), royalty revenue per
unit (mix shift toward premium cores), backlog of license agreements.

### 2.3 Chip design (fabless and IDM design teams)

Design cost escalation is the hidden story of modern semis:

| Node generation | Approximate design cost (fully loaded, incl. SW/IP) |
|---|---|
| 28nm | ~$50M |
| 16nm | ~$100M |
| 7nm | ~$300M |
| 5nm | ~$550M |
| 3nm | ~$700M-1B |

Consequences:
- Only companies shipping >10-20M high-end units/year can amortize leading-edge
  design. This is why the number of leading-edge fabless designers keeps
  shrinking (dozens, not hundreds).
- Design starts at mature nodes (28nm+) keep growing because cost stays low;
  mature-node overcapacity risk lives here.
- IP reuse and chiplet architectures exist partly to amortize design cost.

### 2.4 Wafer fabrication

See sections 3 and 6 for depth. Core facts:
- A leading-edge fab costs $15-25B (TSMC Arizona complex ~$65B across phases,
  2024-announced scale). Equipment is 70-80% of that cost.
- Construction takes ~2 years from groundbreaking; tool install another year;
  yield ramp another 2-4 quarters. Lead time from decision to revenue: 3-5 years.
- Depreciation life: 5-7 years straight-line typical, which front-loads losses
  during ramps and flatters margins at mature fabs running fully depreciated
  tools.

### 2.5 Assembly, test, and packaging (OSAT) and advanced packaging

- Traditional OSAT: labor-intensive, thin margins, located in Taiwan/SE Asia/
  China. Commodity service, price-taker economics.
- Advanced packaging is the strategic exception: TSMC's CoWoS (chip-on-wafer-on-
  substrate) capacity constrained AI accelerator shipments in 2023-2025; HBM
  stacking (with SK hynix, Samsung, Micron) is memory-side packaging value add.
- Analytical point: when an AI GPU sells for $20-40K, packaging and substrate
  become trivial cost but binding constraint. Capacity allocation (who gets
  CoWoS slots) is real competitive information.

### 2.6 Distribution

- Broadline distributors (Arrow, Avnet) hold inventory, provide credit, and
  aggregate demand from thousands of small OEMs.
- Distributor inventory months is a classic cycle indicator: 8-10 weeks healthy;
  >13 weeks signals correction; <6 weeks signals shortage pricing ahead.
- Direct-to-hyperscaler sales increasingly bypass distribution at the top of the
  market; distribution remains essential below it.

---

## 3. Foundry Business Model

### 3.1 The foundry contract structure

Foundry revenue mechanics:
- **Prepayment/deposits:** customers pay deposits reserving capacity slots.
- **Take-or-pay elements (post-2021):** after the shortage, major customers
  committed multi-year minimum purchases. This shifted some demand risk from
  foundry to customer -- a structural improvement worth valuing.
- **Pricing:** wafer price set per node per technology, negotiated annually or
  per-generation. Leading-edge wafers carry 30-50% price premiums per node jump.

Illustrative wafer ASP ladder (per 300mm-equivalent wafer):
- 28nm-class: ~$2,500-4,000
- 16/12nm: ~$5,000-7,000
- 7nm: ~$9,000-11,000
- 5nm: ~$14,000-17,000
- 3nm: ~$18,000-22,000+
- 2nm target: ~$28,000-30,000+

### 3.2 TSMC's moat decomposition

List each moat source separately because they erode at different rates:

1. **Process leadership cadence:** first-to-next-node by 6-12 months over
   Samsung, more over Intel. Customers pay up for time-to-market.
2. **Yield learning curve:** TSMC's yields at new nodes ramp faster. Yield is a
   compounding advantage: better yield -> lower effective cost -> more volume ->
   more learning -> better yield. Intel's 10nm struggles (2016-2021) show what
   happens when this loop breaks.
3. **Ecosystem lock-in:** EDA reference flows, IP libraries, design kits all
   certified against TSMC processes first and best. A designer targeting N3 has
   richer PDK support than any alternative.
4. **Customer concentration reciprocity:** Apple/Nvidia/AMD/Qualcomm/Broadcom
   are simultaneously TSMC's largest customers AND its strongest advocates --
   they funded capacity expansion via deposits and take-or-pay. Competing
   foundries lack equivalent anchor tenants.
5. **Scale in capex:** ~$30-40B/year capital program cannot be matched except
   by Samsung (which splits attention with memory) and Intel (which struggled
   financially to match it).
6. **Pure-play trust:** TSMC never competes with its customers (no products),
   unlike Samsung or historically Intel. For Apple this is disqualifying logic
   against Samsung Foundry.

**Moat erosion vectors:** geopolitical tail risk (Taiwan), US CHIPS-funded
alternatives (Intel Foundry, TSMC-Arizona itself), and eventual physics limits
pushing everyone to similar gate-all-around architectures where differentiation
narrows to yield and packaging.

### 3.3 Capacity utilization economics

This is the heart of foundry P&L modeling. Fixed costs (depreciation, facility,
labor base) dominate; marginal wafer cost is mostly materials + variable energy.

Illustrative mature-fab model (normalized):

| Utilization | Gross margin |
|---|---|
| 100% | ~55% |
| 90% | ~47% |
| 80% | ~38% |
| 70% | ~28% |
| 60% | ~17% |

Rough sensitivity: each 5 points of utilization moves gross margin ~2-3 points
at leading-edge fabs (higher fixed-cost share), less at older fabs.

Implications:
- Utilization guidance changes matter more than revenue beats/misses for margin
  trajectory. Track quarterly utilization commentary religiously.
- Pricing holds only when utilization >85%; discounting appears quickly below.
- The 2022-2023 smartphone downturn showed the reverse: TSMC absorbed a 20%+
  revenue decline in some segments while holding gross margin in the mid-50s,
  aided by mix (HPC share rising) and prior price increases.

### 3.4 Foundry competitive dynamics checklist

For ANY foundry (not just TSMC) ask:
1. What fraction of capacity is pre-committed (take-or-pay)?
2. What is the node mix trajectory? (Mix-up offsets cyclical softness.)
3. What specialty technologies (RF, embedded NVM, power BCD, image sensors)
   provide pricing insulation?
4. Who funds the next capex wave, and what ROIC does the incremental node need?
5. Government subsidy dependency: CHIPS Act grants/I-loans de-risk returns but
   introduce political conditionality (profit-sharing clauses, capacity caps).

---

## 4. Memory Cycle Theory

### 4.1 Why memory is hyper-cyclical

Memory (DRAM, NAND) is commodity-like because:
1. Product is standardized (a DDR5 DIMM is fungible across brands).
2. Capacity additions are lumpy ($10-25B fabs, 2-3 year lead times).
3. Demand is growing but volatile around trend.
4. Supply response is asymmetric: adding capacity is fast once committed;
   cutting it means idling depreciated-but-cheap tools.

Result: classic cobweb/pork-cycle dynamics. High prices -> record profits ->
capex boom -> supply lands 2 years later -> glut -> prices below cash cost ->
capex cuts -> shortage -> repeat.

Historical cycle skeleton (DRAM):
- Peak-to-trough ASP declines of 40-70% have repeated roughly every 3-4 years
  (2008-09, 2011-12, 2015-16, 2018-19, 2022-23).
- Bottoms marked by: industry-wide cash-cost breaches, capex cuts of 20-40%,
  production cut announcements (Samsung historically last to cut).
- Tops marked by: bit-supply growth < demand growth for 4+ quarters, record
  inventories at PC/OEMs actually LOW (not high), and supplier balance sheets
  repaired enough to fund the next round.

### 4.2 Reading the cycle: the four-quadrant dashboard

| Quadrant | Prices | Inventories | Bit growth | Action posture |
|---|---|---|---|---|
| Recovery | Rising off bottom | Falling | Below demand | Best entry window |
| Boom | Rising/peak | Low-normal | Constrained | Hold; watch capex announcements |
| Slowdown | Falling | Building at OEMs | Above demand | Trim; sell capex-exposed names first |
| Trough | Below cash cost | Forced destocking | Cut hard | Accumulate survivors |

Leading indicators ranked by usefulness:
1. Supplier capex guidance revisions (lead 4-6 quarters to supply effect).
2. Contract price direction (monthly DRAMeXchange/TrendForce data).
3. Server DRAM demand (largest single DRAM segment).
4. NAND wafer starts commentary (harder to cut than DRAM).
5. PC/smartphone unit forecasts (lagging; use to confirm, not anticipate).

### 4.3 Structural changes weakening (but not killing) the cycle

- Consolidation: DRAM now 3 players (Samsung, SK hynix, Micron) vs 8+ in the
  1990s. Rationality improves at the margin; Qorvo-style discipline still fails
  under competitive pressure though.
- Technology barriers rising: 1-alpha/beta/gamma DRAM nodes use EUV; transition
  costs slow capacity adds and raise the bar for Chinese entrants (CXMT stuck
  generations behind at DDR4/DDR5 entry levels through mid-2020s).
- HBM (high bandwidth memory): see 4.4.
- NAND remains the least disciplined market (more players, easier conversion
  between layers); expect deeper and longer NAND troughs than DRAM.

### 4.4 HBM transition analysis

HBM = stacked DRAM dies with wide interface, bonded to GPU/accelerator. Key
facts:
- HBM consumes ~3x the wafer area per bit versus standard DDR (die size penalty
  from TSV/bonding + yield loss + redundancy overhead). One HBM stack uses
  roughly the wafer capacity of three conventional modules of equal bits.
- HBM ASP per GB runs 3-5x conventional DRAM. Mix shift toward HBM mechanically
  lifts industry revenue even at flat bit shipments.
- Supply is effectively triopolistic with SK hynix holding the majority share
  (first mover with Nvidia), Samsung catching up after qualification delays,
  Micron ramping aggressively.
- Analytical consequence: track "HBM bit share" and "HBM revenue share"
  separately per company. HBM share of DRAM industry revenue passed 20-30%+
  during 2024-2025 and kept climbing; whoever wins HBM sockets captures
  outsized profit pools even if total industry bits grow modestly.
- Watch for: HBM4 specification adoption timing, hybrid bonding replacing
  MR-MUF/TC-NCP bonding approaches, and whether custom HBM (per-customer specs)
  breaks the commodity framing entirely.

### 4.5 Memory valuation method

Do NOT use P/E at cycle peaks (trough multiples look cheap at peak earnings).
Preferred toolkit:
1. Normalized earnings through full cycle (use mid-cycle margins: DRAM GM
   ~40%, NAND ~30% as anchors).
2. P/book at troughs (Micron historically bottoms near or below 1x book).
3. EV/replacement cost: compare market cap against estimated cost to rebuild
   the fab fleet (replacement cost sets a soft floor in oligopolies).
4. Free cash flow resilience: can the company fund capex + dividend through
   two down years without dilution?

---

## 5. Equipment Intensity: Cyclical but Secularly Growing

### 5.1 The apparent paradox

Equipment makers (ASML, Lam Research, Applied Materials, KLA, Tokyo Electron,
Teradyne) show violent revenue swings, yet each cycle trough sits above the
last. Both facts trace to the same driver: WFE spending = installed-base
expansion + technology-driven replacement/refit.

Components of WFE demand:
1. **Capacity purchases** (new fabs for more wafers): purely cyclical, tracks
   end demand with a lag, cancels hardest in downturns.
2. **Technology transitions** (node migration forces tool refits): semi-sticky;
   EUV insertion, gate-all-around transistor swaps, backside power delivery
   each force fleets of new tools even at flat wafer output.
3. **Density upgrades in memory** (layer counts in NAND, cell shrinks in DRAM):
   quasi-cyclical but persistent; etch/deposition intensity rises with layer
   counts (3D NAND going 128 -> 232 -> 400 layers raises process steps ~linearly).

Secular growth comes from items 2 and 3 compounding faster than item 1
declines in each downturn. Additionally, the AI buildout added a fourth leg:
packaging/co-packaging optics/test capacity for accelerators.

### 5.2 Company positioning map

| Company | Dominant niches | Monopoly degree | Cycle lever |
|---|---|---|---|
| ASML | Photolithography (DUV+EUV) | EUV 100%; DUV ~90% immersion | Node transitions; China DUV pull-ins |
| AMAT | Deposition, CMP, etch, implant | Broad portfolio leader | Foundry/logic capacity |
| LRCX | Etch, deposition (memory-heavy) | Plasma etch co-leader | NAND layer count races |
| KLA | Process control/metrology | ~55%+ process control | Yield-ramp intensity |
| TEL | Coater/developer (~90%), etch | Japan champion | Balanced foundry/memory mix |
| TER | ATE test (mobile/HPC) | Duopoly with Advantest | New device introductions |

### 5.3 Book-to-bill and backlog analytics

- Book-to-bill >1 signals expansion; sustained <0.9 signals contraction.
- ASML's backlog model (multi-quarter visibility, ~$35-40B range through
  mid-2020s) makes it the most forecastable; short-cycle names (TER, form-factor
  adjacent) are the fastest indicators.
- Deferred revenue and RPO trends reveal order momentum earlier than bookings
  headlines.

### 5.4 China exposure calculus

Post-Oct-2022 controls restrict advanced-node tools to China. Consequences:
- Chinese fabs stockpiled DUV and non-restricted tools; 2023-2024 saw China
  rise to 25-45% of several US toolmakers' revenue (pull-forward).
- This creates a medium-term air pocket: pull-forward demand borrowed from
  future quarters. Model China WFE reverting to structural (lower) levels.
- SMIC's 7nm-class production via DUV multi-patterning shows workarounds exist
  but at cost/yield penalties; each workaround consumes MORE tools per wafer
  (paradoxically boosting certain tool categories).

### 5.5 Equipment valuation approach

- Mid-cycle framework again: normalize WFE revenue to a view of steady-state
  industry demand (wafer starts growth + tech-transition intensity).
- Service/installed-base revenue (ASML Installed Base Management, AMAT AGS,
  KLA services) grows monotonically and deserves a separate, higher multiple.
  It is typically 20-25% of revenue at 55-60%+ gross margin.
- Optionality framing: each technology inflection (High-NA EUV, GAA, backside
  power, advanced packaging) is a call option on share gains; position sizing
  should reflect how much of that option is already priced.

---

## 6. Fabless vs IDM: Capital Efficiency Comparison

### 6.1 Definitions

- **Fabless:** designs chips, contracts manufacturing (Nvidia, AMD, Qualcomm,
  Broadcom, Marvell, MediaTek).
- **IDM:** designs AND manufactures (Intel, Samsung, TI, STMicro, Infineon,
  onsemi, Micron for memory).
- **Fab-lite hybrids:** IDM keeping leading edge outsourced while retaining
  specialty fabs (e.g., some RF/power players).

### 6.2 The financial comparison

| Metric | Fabless (typical) | IDM (typical) |
|---|---|---|
| Gross margin | 45-75% (AI leaders top) | 30-55% |
| Capex/revenue | 2-8% | 20-40% |
| Asset turns | High (2-5x) | Low (<0.5x) |
| ROIC spread | Wide positive in good design | Narrow; node-timing dependent |
| Operating leverage | To volumes (outsourcing absorbs) | Brutal both directions |
| Margin floor in downturn | Higher (variable wafer cost passes through) | Lower (fixed depreciation sticks) |
| Strategic control | Less (capacity allocation risk) | Full (process optimization freedom) |

Fabless ROIC math intuition: paying TSMC's ~55% gross margin embedded in wafer
prices buys out of a $20B-per-node capital commitment. That is rational when
design wins are uncertain; it becomes expensive rent when volumes are massive
and predictable -- which is exactly why the biggest fabless players periodically
flirt with owning capacity (and why TSMC offers them joint-venture structures,
prepayments, and take-or-pay discounts to prevent defection).

### 6.3 When IDM wins

IDM logic dominates where:
- Products are analog/mixed-signal where process-product codesign matters more
  than node scaling (TI's 300mm analog fabs print money at 28-130nm on old,
  fully-depreciated equipment).
- Automotive/industrial qualification demands supply-chain control.
- Proprietary process devices (power GaN, SiC, MEMS, image sensors) lack
  merchant foundry alternatives at acceptable quality.
- Memory: integration from design to process is mandatory (no merchant model
  exists for DRAM design separate from manufacture).

TI is the canonical case study: sub-scale leading-edge ambition, disciplined
capital returns, 300mm analog strategy, and counter-cyclical capex. Its equity
story is industrial-economics compounding, not technology racing.

### 6.4 Intel as the cautionary IDM tale

Framework lessons from Intel 2016-2025:
- Missing/stumbling a node transition (10nm delays) breaks BOTH the product
  roadmap AND the factory economics simultaneously -- correlated failure unique
  to IDM.
- Internal-foundry transfer pricing is unsolvable politics: product groups
  resent subsidizing the fab, the fab resents captive demand hiding its
  competitiveness. Intel's external-foundry push required creating a genuine
  internal market.
- Once ecosystem flows (packaging, IP, design kits) consolidate around a rival
  foundry, switching costs bind customers to the rival, not to you.

---

## 7. Advanced Node Economics

### 7.1 Cost explosion drivers at 3nm/2nm

Per-wafer cost inflation sources:
1. **Tool counts per wafer:** EUV layers multiply (N7 ~5-8 EUV layers; N3
   ~15-20+; N2 gate-all-around pushes further). Each EUV layer adds litho cost
   and throughput bottlenecks. High-NA EUV tools (~$350-400M each) enter at
   Intel 18A/TSMC A14-era roadmaps, raising the ante again.
2. **Yield learning cost:** early yields of 50-60% mean effective cost per GOOD
   die nearly doubles printed-die cost. Learning happens in volume; someone
   pays for the ramp (usually split among anchor customers via pricing).
3. **Materials/process steps:** total process steps rose from ~500 (28nm) to
   1,000+ (3nm). Every step is deposition/etch/clean/metrology cost.
4. **Facility complexity:** extreme purity, vibration control, power density.
5. **R&D amortization:** node development costs run $5-10B+ per generation;
   foundries recover via wafer pricing premiums.

### 7.2 Transistor economics: the shrinking die question

Cost per TRANSISTOR may keep falling while cost per WAIFER explodes. Whether a
product should move to the newest node depends on:
- Die area shrink available (logic-dense designs benefit most).
- Whether the chip is die-size-limited (big GPUs) or pad/IO limited (many MCUs
  gain nothing from 3nm).
- Volume: design cost amortization requires millions of units.
- Performance/power: AI accelerators gain revenue directly from performance/watt;
  washing machines do not.

Practical rule: leading-edge nodes make sense for high-volume, performance-
priced silicon (phones flagship SoCs, GPUs/accelerators, server CPUs) and make
NO sense for most everything else. The industry bifurcates: a few giant leading-
edge products and a long tail of mature-node parts. Invest accordingly: mature
node capacity is NOT obsolete; it serves the long tail profitably.

### 7.3 Advanced packaging as node substitute

Chiplets + advanced packaging (CoWoS, InFO, EMIB, Foveros, SoIC) let designers
mix nodes: leading-edge compute die + mature-node I/analog dies. Economic
implications:
- Total package cost falls versus monolithic 3nm equivalents.
- Known-good-die testing requirements boost test equipment demand.
- Interconnect (UCIe standard) and substrate supply chains become strategic.
- Hybrid bonding (bumpless Cu-Cu) is the next frontier, enabling HBM stacks
  beyond ~16-high and 3D cache scaling.

### 7.4 Modeling a node transition (worked framework)

For a foundry moving to a new node:
1. Estimate installed capacity (wafers/month) planned at ramp maturity.
2. Apply a yield ramp curve (quarter 1: 40-50%; quarters 2-3: 60-75%; mature:
   80%+ for mobile-class, lower for huge AI dies).
3. Compute good dies per wafer at each stage; multiply by die ASP for revenue.
4. Layer in wafer ASP premium and depreciation step-up; early quarters usually
   show gross-margin drag of 200-400 bps until utilization+yield cross ~70%.
5. Anchor-customer concentration determines revenue variance (one phone launch
   slipping moves a quarter).

---

## 8. Export Controls: Segment-by-Segment Impact Map

### 8.1 Control architecture (US framework, evolving)

- **Entity List:** named Chinese entities barred from receiving US-origin
  tech (Huawei since 2019-2020; later SMIC-adjacent, supercomputer programs,
  many AI-chip buyers).
- **Advanced-compute rules (Oct 2022, tightened Oct 2023, Dec 2024):**
  performance-density thresholds restrict AI GPU/TPU exports to China; US-
  persons rules restrict Americans supporting Chinese advanced fabs.
- **Equipment/tool restrictions:** advanced-node WFE barred to specified fabs;
  licensing requirements with presumption of denial.
- **Allied coordination:** Japan/Netherlands aligned on advanced litho/tools
  (2023+), though scope narrower than US rules.
- **Reciprocal Chinese measures:** gallium/germanium/graphite/antimony export
  licensing (2023-2025) hitting materials upstream.

### 8.2 Impact grid

| Segment | Direction | Mechanism | Net assessment |
|---|---|---|---|
| US AI accelerators (NVDA/AMD) | Revenue loss (China DC ~5-15% of data center rev) | Product bans force derivate SKUs (H20-class) with successive bans | Manageable so far; watch cumulative tightening |
| EDA | Moderate loss | Advanced-design tool bans; China localization push (Empyrean) | Recurring base cushions; China self-sufficiency is slow |
| Equipment | Mixed | Lost advanced China sales OFFSET by stockpiling/DUV multipatterning intensity | Air-pocket risk 2025-2026 as pull-forward digests |
| Foundry (Taiwan) | Indirect | Cannot serve restricted Chinese advanced demand; benefits as non-China design migrates to compliant supply | Net positive share shift |
| Chinese foundry (SMIC etc.) | Constrained | Stuck at DUV-era nodes; heavy state capex inflates mature capacity | Price pressure on global mature nodes |
| Memory | Emerging | CXMT ramp in DDR4/LPDDR4 pressures legacy pricing; HBM out of reach near-term | Legacy DRAM/NAND ASP risk |
| Materials (Ga/Ge/Sb) | Cost/availability | Chinese licensing regimes | Modest cost inflation; strategic stockpiling |
| Auto/industrial semis | Minimal direct | Mostly mature nodes outside control scope | Secondary effect via mature-node oversupply |

### 8.3 Second-order effects to monitor

1. **China mature-node capacity surge:** subsidized fabs adding 28nm+ capacity
   could crush mature-node pricing globally by late decade -- the biggest
   quiet risk to UMC, PSMC, GF, and even TSMC's mature mix, plus analog IDMs.
2. **Dual supply chain formation:** "trusted" supply chains (US/allied) command
   procurement premiums (defense, government clouds) -- margin tailwind for
   compliant producers.
3. **Innovation forcing functions:** restrictions accelerated Huawei's Ascend
   ecosystem, SMIC N+2 workarounds, and domestic tool/EDA funding. Controls
   buy time, not permanent exclusion; assume catch-up horizons of 5-10 years,
   not infinity.
4. **Enforcement leakage:** third-country transshipment and gray-market flows
   blur measured effectiveness; treat reported China revenue shares cautiously.

---

## 9. Metrics Playbook by Subsegment

### 9.1 Universal metrics

- Revenue growth vs guided range; beat/miss persistence.
- Gross margin trajectory and drivers (price, mix, utilization, FX).
- Inventory days and channel inventory (supplier + distributor + customer).
- Capex and its destination (capacity vs technology vs facilities).
- Customer concentration disclosures (top-10 customer % of revenue).
- Geographic revenue mix (China % especially).
- Headcount productivity trends (revenue/employee as efficiency proxy).

### 9.2 Segment-specific dashboards

**Foundry (TSMC et al.):**
- Wafer shipments (12-inch equiv units) Q/Q.
- Revenue by node (% advanced <7nm share; target trajectory).
- Revenue by platform (HPC/smartphone/auto/IoT) -- HPC mix is THE margin lever.
- Utilization statements; gross margin guide vs utilization guide.
- Monthly revenue releases (Taiwan-listed firms report monthly!) give
  intra-quarter visibility -- use them.

**Memory:**
- Bit shipment growth Q/Q and Y/Y; ASP change Q/Q (the two multiply to revenue).
- Inventory weeks at suppliers; contract vs spot price spreads (spot leads).
- Capex plans vs prior commitments; wafer start adjustments.
- HBM: bit share targets, qualification milestones with anchor customers.
- NAND: layer counts in production, SSD vs mobile vs enterprise mix.

**Equipment:**
- Bookings/backlog/RPO; book-to-bill; deferred revenue deltas.
- China revenue % and commentary on license pipeline.
- Systems vs installed-base-service revenue split.
- New technology adoption metrics: EUV shipments (units/quarter), High-NA
  pilot tools, GAA-related tool intensity commentary.

**Fabless:**
- End-market revenue splits; design win announcements (2-4 yr lead).
- Inventory days (they own inventory risk despite outsourcing).
- Customer concentration (hyperscalers often >10% each at AI leaders).
- Gross margin bridge: new node ramp costs, product mix, pricing actions.

**OSAT/distribution (cycle bellwethers):**
- Revenue Q/Q (fast-turn business reads the cycle earliest).
- Capacity utilization; capex restraint signals.
- Distributor book-to-bill and inventory months (see 2.6).

### 9.3 Indicator hierarchy (what leads what)

Approximate lead/lag ordering observed across cycles:
1. Customer capex announcements & foundry monthly revenues (lead 1-2 qtrs).
2. Equipment orders/book-to-bill (coincident-to-leading).
3. Fabless inventory corrections (leading at turn-downs).
4. Foundry utilization/pricing (coincident).
5. Memory spot->contract prices (spot leads contract ~1-2 qtrs).
6. Reported segment revenue/eps (lagging confirmation).
7. Consensus estimate revisions (most lagging; fade them, don't chase).

---

## 10. Putting It Together: A Research Workflow

### 10.1 Step sequence for analyzing any semi name

1. Classify the segment(s) and demand-engine exposures (section 1.4).
2. Locate the company on its OWN cycle (utilization, pricing, inventory).
3. Identify the 2-3 variables that explain 80% of earnings variance
   (e.g., hyperscaler capex for AI fabless; NAND pricing for SanDisk-class
   memory; China pull-forward digestion for US tools).
4. Build bear/base/bull on those variables only -- resist 20-driver models.
5. Stress-test balance sheet through a 2008-style or 2018-style downcycle.
6. Check export-control exposure quantitatively (revenue at risk, mitigation).
7. Value on normalized earnings (mid-cycle margins) + scenario multiples;
   sanity-check against P/book (memory/foundry) or P/S bands (fabless/EDA).

### 10.2 Common analytical traps

- Extrapolating peak memory earnings as sustainable.
- Treating mature-node capacity as stranded when it compounds quietly.
- Ignoring monthly Taiwan revenue prints in favor of stale quarterly guides.
- Assuming export controls are static (they ratchet in both directions).
- Modeling AI datacenter demand without hyperscaler capex guidance as the
  primary input.
- Valuing equipment on trailing WFE instead of forward technology-intensity.

### 10.3 Cross-links

- Macro overlay for the demand side: [[edu-macro-analysis]] (ISM, capex cycles,
  rates transmission into consumer electronics demand).
- Power/energy constraints on fab and datacenter growth:
  [[edu-energy-power-markets]] (grid interconnection is becoming a real
  constraint on AI datacenter siting, hence on accelerator demand).

---

## Appendix A: Glossary

- **ASP:** average selling price.
- **ATE:** automated test equipment.
- **Bit growth:** % increase in memory bits supplied per period.
- **Book-to-bill:** orders divided by shipments; >1 expanding.
- **CD:** critical dimension; smallest feature size printed.
- **CoWoS:** TSMC chip-on-wafer-on-substrate advanced packaging.
- **DUV/EUV:** deep ultraviolet / extreme ultraviolet lithography.
- **GAA:** gate-all-around transistor (successor to FinFET).
- **HBM:** high bandwidth memory; stacked DRAM beside/under the processor.
- **IDM:** integrated device manufacturer (designs and fabricates).
- **OSAT:** outsourced semiconductor assembly and test.
- **PDK:** process design kit; foundry's recipe book for designers.
- **RPO:** remaining performance obligations (backlog proxy).
- **TSV:** through-silicon via; vertical connection in stacked die.
- **Utilization:** % of installed wafer capacity actively processing.
- **WFE:** wafer fab equipment spending.

## Appendix B: Data Sources (offline reference list)

- TSMC monthly revenue releases and quarterly management reports.
- SEMI billings reports (global semi sales, WFE estimates).
- TrendForce / DRAMeXchange summaries for memory pricing structure.
- SIA industry factbook for end-market splits.
- Company 10-Ks: capacity tables, customer concentration, geographic mix.
- BIS (US Commerce) Federal Register notices for control-rule evolution.


---

## Related vault data

Vault references implementing this framework on the live watchlist:

- [[ref-semiconductor-value-chain]] -- Section 2's value chain rendered as
  a generated reference with per-name exposure mapping.
- ref-supply-chain-dependency -- chokepoints and margin transfer;
  who earns the system-level margin Sections 2 and 3 describe.
- [[ref-ai-supply-chain-complete]] -- the Tier 0-7 dependency graph that
  extends Section 2's value chain across the full AI buildout stack.
- [[ref-financial-statements]] -- capacity tables, customer concentration,
  and geographic mix pulled from filings for Section 9's metrics playbook.
- ref-earnings-analysis-framework -- post-print rerun workflow over
  the covered semis; Section 10's step sequence in production.
- [[ref-memory-storage-cycle-deep-dive-ingest-2026-05-06]] -- Section 4's
  memory-cycle theory archived against HBM/DRAM/NAND evidence.
- [[ref-ai-supply-chain-deep-dive-ingest-2026-05-06]] -- AI demand chain
  archive feeding Section 1.4's demand engines.
- ref-defense-aerospace-space-economy-deep-dive-ingest-2026-05-06 --
  export-control and defense-electronics context for Section 8.
- ref-cross-analysis-synthesis -- all wave-S and semi refresh verdicts
  synthesized; consensus vs contrarian read.
- Companion frameworks: [[edu-macro-analysis]] (ISM, capex cycle, policy)
  and [[edu-energy-power-markets]] (power constraints on fab buildouts).

*Corpus note: Part 3 of the finance education series. Companion files cover
macro analysis and energy/power markets.*
