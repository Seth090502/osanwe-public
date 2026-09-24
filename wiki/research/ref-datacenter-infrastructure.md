---
categories: [wiki]
type: reference
status: active
created: 2026-08-24
updated: 2026-08-24
confidence: high
tags:
  - topic/investing
  - topic/datacenter
  - topic/theme-alpha
related: ["[[ref-financial-statements]]", "[[ref-theme-alpha]]", "ref-ai-supply-chain-deep-dive", "[[ref-semiconductor-value-chain]]", "[[ref-energy-power-complex]]"]
---

# Data-Center Infrastructure Reference

GENERATED: 2026-08-24 by sector-reference enrichment wave.
REGENERATE: re-run the EDGAR XBRL aggregation over
wiki/investing/filings/`<TICKER>`/`<TICKER>`-xbrl.json (method in
[[ref-financial-statements]]), re-pull technical stats from the factor store
(Efforts/osanwe-v2-overhaul/_work/factors.db bars table), and re-read entity
signals from wiki/entities/tickers/<T>.md. Do not hand-edit numbers; regenerate.

## 0. Method and source keys

- FIN[n], TECH[n], ENT[k]: same conventions as [[ref-semiconductor-value-chain]]
  Section 0. Bars end 2026-08-21. AFFO/FFO metrics are NOT in the XBRL concept
  set -- they appear only where an entity note carries a company-guidance
  figure, labeled ENT below ("where computable" per scope).
- No network sources used anywhere in this file.

## 1. Colocation REITs (DLR / EQIX)

| Name | Rev/LQ (YoY) | NI margin TTM | Price 8/21 | off hi | vs MA200 |
|---|---|---|---|---|---|
| DLR | $1.6B (+16.2%) FIN | 21.9% FIN | $190.62 TECH | -5.9% | +8.2% |
| EQIX | $2.6B (+16.4%) FIN | 15.6% FIN | $1,065.39 TECH | -4.1% | +13.4% |

### Digital Realty (DLR)

- Colocation + hyperscale leasing: record 2025 bookings $1.2B (70% above prior
  five-year average); hyperscale leasing >$800M at a claimed 100% share of the
  largest deals; >1 MW renewals repriced +19.9% cash rental increases (Q4-25)
  (all HIGH, ENT[DLR] via ref-theme-alpha).
- AI-ready capacity commands ~60% rate premium: $150-200/kW/month vs $100-120
  historical (ENT[DLR]); vacancy 1.4% record low with 92% of construction
  pre-committed (CBRE H2-2025, HIGH).
- Balance sheet is the risk vector: ~5.1x net-debt/EBITDA (MEDIUM); P/FFO ~11x,
  EV/EBITDA ~25x (Apr 17-20 2026 snapshot, MEDIUM).
- Core FFO growth guided +8% FY2026E (dtcr-analysis).

### Equinix (EQIX)

- Interconnection moat: cross-connect economics unavailable to pure-colo peers
  (HIGH); xScale JV funds hyperscale shells off balance sheet (MEDIUM).
- AFFO metrics (computable from guidance): FY2026 revenue $10.1-10.2B (+10-11%);
  AFFO/share $41.93-42.74 (+9-12%) (company guidance via dtcr-analysis, Grade A).
- Moody's upgrade to Baa1 (2026-03-05) validates balance sheet amid buildout
  (ENT[EQIX]); P/AFFO ~26x vs DLR ~24x, upper end of historical ranges but
  supported by 8-12% growth vs REIT average 3-5% (dtcr-analysis).
- Structural risk: hyperscaler self-build bypass -- Microsoft 2GW cancellation
  precedent cited (MEDIUM).

### Rate sensitivity, quantified

RATE regression (weekly, Sep-2024..Aug-2026, n=98, method as in
[[ref-energy-power-complex]] S0):

- DLR: beta +11.0% price move per +100bp DGS10, corr +0.35.
- EQIX: beta +9.6% per +100bp, corr +0.32.
- DERIVED read: both traded POSITIVELY correlated to yields over this window --
  they behaved as growth/scarcity assets, not bond proxies. dtcr-analysis makes
  the same qualitative point ("market treats DC REITs as rate-sensitive
  instruments when they are increasingly scarcity-premium infrastructure assets
  with pricing power"). Caveat: a fast >100bp yield shock would likely restore
  traditional duration behavior given 5.1x (DLR) leverage; EQIX's Baa1 gives it
  more cushion.

## 2. Server OEMs (DELL / HPE / SMCI)

| Name | Rev/LQ (YoY) | NI margin TTM | Price 8/21 | off hi |
|---|---|---|---|---|
| DELL | $43.8B (+87.5%) FIN | 5.3% FIN | $442.08 TECH | -10.6% |
| HPE | $10.7B (+40.0%) FIN | 4.0% FIN | $53.45 TECH | -10.6% |
| SMCI | $10.2B (+122.7%) FIN | 3.7% FIN | $37.24 TECH | -36.5% |

- DELL: Q4-FY26 AI-optimized server revenue $8.95B +342% YoY; FY27 AI-server
  target $50B; $43B AI backlog entering FY27 (per 247wallst via
  ref-ai-supply-chain-deep-dive on ENT[DELL]). Total revenue ladder last 4
  quarters 23.4 / 29.8 / 27.0 / 33.4* -> 43.8 ($B; * derived quarter, FIN S2 --
  one negative artifact quarter printed -47.7 from the derivation, treat level
  series carefully). NI margin 5.3% TTM (FIN): the volume winner's thin-slice
  profile.
- HPE: Q2-FY26 guide $9.6-10B; Cray/Apollo HPC + Juniper networking (merger
  closed 2025) (ENT[HPE]). NI margin 4.0% TTM (FIN). Highest-momentum chart in
  tier: 63d +57.8%, 126d +152.5%, vol21 53.1% (TECH).
- SMCI: liquid-cooled AI server specialist; ~40-50% AI server share 2024
  (Mizuho est., MEDIUM); FY24 revenue $14.9B vs $3.6B FY21 (ENT[SMCI]);
  legal/accounting overhang lingering (ENT[SMCI]); LQ prints 2026Q1 so its row
  lags peers by a quarter (FIN). Rebounding: 20d +23.7% (TECH).
- Margin profiles compared (FIN NI margins TTM): DELL 5.3% / HPE 4.0% /
  SMCI 3.7% -- all three monetize the AI-server wave at single-digit net
  margins; the profit pool of the rack sits upstream (GPUs) and around
  (power/cooling), not in assembly. Working-capital intensity is structural:
  OEMs carry GPU inventory + receivables against hyperscaler/neo-cloud credits;
  corpus does not carry DSO/DIO tables for these three [gap -- populate via
  /invest]; the ORCL/NBIS analogues elsewhere in this file show how
  capex/receivable-heavy AI infrastructure finance strains working capital.
- Trajectory verdict (DERIVED): DELL's $43B backlog + $50B target make it the
  clearest AI-server revenue compounder; HPE is the turnaround/Juniper option;
  SMCI is the high-beta liquid-cooling pure play with governance hair.

## 3. Networking for AI fabrics (ANET / AVGO / MRVL / COHR / LITE / CSCO / APH / FN / CRDO)

Speed-transition frame (corpus-wide): 400G -> 800G shipping now, 1.6T ramping
with Tomahawk 6-class silicon and 200G-per-lane EML lasers; AVGO SerDes roadmap
200G -> 400G in 2028 with co-packaged optics beyond (ENT[AVGO], MEDIUM).

| Name | Layer | Rev/LQ (YoY) | NI margin TTM | Price 8/21 | 63d return |
|---|---|---|---|---|---|
| ANET | Switch systems (merchant Ethernet) | $3.0B (+37.7%) FIN | 37.7% FIN | $188.65 | +27.0% |
| AVGO | Switch ASIC + custom XPU | $22.2B (+47.9%) FIN | n/a FIN | $368.45 | -11.0% |
| MRVL | Custom ASIC + optical DSP | $2.4B (+27.6%) FIN | 26.5% FIN | $237.04 | +24.3% |
| COHR | Transceivers (~25% share) | $2.0B (+33.7%) FIN | 11.3% FIN | $289.52 | -23.4% |
| LITE | EML lasers (50-60% share) | $481M LQ FIN | n/a FIN | $866.71 | -10.1% |
| CSCO | Incumbent systems (AI adj.) | $15.8B (+12.0%) FIN | 19.7% FIN | $111.04 | -5.7% |
| APH | Connectors/cable assemblies | $8.8B (+55.0%) FIN | 17.4% FIN | $157.01 | +25.9% |
| FN | Contract manufacturing (optics) | $1.3B (+44.6%) FIN | 10.2% FIN | $436.67 | -37.9% |
| CRDO | AECs/SerDes within-rack | $437M (+157.0%) FIN | 35.4% FIN | $230.57 | +19.2% |

Per-name notes:

- ANET: AI networking revenue $1.5B (2025) -> $3.25B (2026 guided) = 2.17x;
  total guide $11.25B +25%; Ethernet winning fabric share from InfiniBand;
  timing coincident-with-compute lagging one quarter; memory-driven cost
  inflation flagged in guidance (all ENT[ANET]).
- AVGO: $73B AI backlog; six hyperscaler XPU customers incl OpenAI 10GW;
  Tomahawk 6 102 Tb/s; full detail in [[ref-semiconductor-value-chain]] S7.
- MRVL: Trainium anchor + 1.6T DSP curve; GM structurally ~17pp under AVGO
  (mrvl-analysis-2026-06-18).
- COHR: NVIDIA 800G wallet ~20%; top-5 transceiver vendors ~50% of 2025 revenue
  -> module-level concentration (ENT[COHR]).
- LITE: EML demand exceeds supply 25-30% -- the transition's hardest input
  constraint (ENT[LITE]); June-FY reporting lags calendar (FIN).
- CSCO: discipline reference (-89% dot-com drawdown, 25-yr recovery), fwd P/E
  ~16x (ENT[CSCO]).
- APH: IT-datacom 41% of revenue, +99% YoY AI-driven; Q1-26 orders $9.4B,
  1.24 book-to-bill; CommScope/Andrew closed Q1-26 pushing net-debt/EBITDA to
  ~1.86x with 18-24mo deleveraging path; ROIC 25.4% FY25; Piotroski 6/9,
  Beneish clean (all ENT[APH], corrections logged 2026-06-09 / 2026-07-04).
- FN: NVIDIA optical-module assembly partner (also assembles for Coherent +
  Lumentum); FY25 10-K period-end 2025-06-27 (ENT[FN]); weakest tape in this
  section: 63d -37.9%, vol21 112.9% (TECH).
- CRDO: ~75% AEC share = within-rack copper toll-road; ~200% YoY revenue growth
  at profiling date; Beneish -1.49 above the -1.78 flag line = CAUTION;
  distribution-pattern insider selling (35 Form-4s, all sells) (crdo entity +
  2026-06-08 analysis).
- Customer concentration (section-level synthesis, DERIVED from cited claims):
  NVDA-related demand dominates COHR (20% wallet claim), FN (assembly partner),
  CRDO (NVLink-generation racks); hyperscaler XPU programs dominate AVGO/MRVL;
  top-5 module vendors ~50% of market concentrates COHR/FN pricing power
  further. The whole section is effectively levered to a handful of platform
  decisions per year.
- 800G/1.6T positioning summary (DERIVED): silicon ready (AVGO TH6), lasers
  scarce (LITE), modules consolidating (COHR/FN), copper inside the rack
  (CRDO/APH) vs optics between racks -- each speed doubling shifts the
  optics boundary deeper into the rack, which is why CRDO (AEC) and LITE (EML)
  are the two highest-growth-rate lines in the table.

## 4. Software / AI platforms (PLTR / NOW / ORCL / CRWV / NBIS)

| Name | Rev/LQ (YoY) | NI margin TTM | Price 8/21 | off hi | 20d return |
|---|---|---|---|---|---|
| PLTR | $1.9B (+92.8%) FIN | 44.4% FIN | $179.94 | -13.1% | +46.4% |
| NOW | $4.0B (+24.0%) FIN | 11.2% FIN | $128.48 | -33.2% | +30.1% |
| ORCL | $19.2B (+20.6%) FIN | 25.4% FIN | $146.47 | -54.9% | +27.4% |
| CRWV | $2.6B (+112.5%) FIN | -23.3% FIN | $87.85 | -38.6% | +22.2% |
| NBIS | n/a (no xbrl json) FIN | n/a | $219.13 | -23.6% | +16.7% |

Enterprise-AI adoption evidence, per name:

- PLTR: AIP commercial adoption acceleration is the thesis engine (ENT[PLTR]);
  rev +92.8% YoY at 44.4% TTM net margin (FIN); US-commercial >=40% YoY and NRR
  >130% are the tracked moat gates vs agentic-AI commoditization (pltr-analysis-
  2026-06-23); valuation paradox documented: P/S ~54.8x, negative ~375bps ERP
  vs 4.45% 10Y at the June print, SBC ~14% of revenue, forensically pristine
  (Piotroski 8/9, Beneish clean, net cash $7.8B).
- NOW: the cleanest enterprise-AI adoption read in the cohort: Q1-26 revenue
  $3,770M +22.1%; cRPO $12.64B +22.5%; 16 deals >$5M net-new ACV +80% YoY;
  FY26 subscription guide raised to $15.735-15.775B (now-analysis-2026-06-12,
  Grade A). Adoption cost side: GAAP subscription GM 77.5% vs 81.5% year ago
  (-400bps/4Q, accelerating) as AI inference costs land in COGS -- the live
  test of whether agentic AI is accretive or dilutive to per-seat SaaS.
  Forensics clean (Altman Z 5.90, Beneish -2.906); Armis acquisition added
  ~$8B debt ending the net-cash era (est ~$400M annual interest).
- ORCL: demand confirmed by backlog: RPO $638B +363% YoY (+$85B seq), OCI +93%
  to $5.8B in Q4-FY26; FY26 revenue $67.4B +17.4%; FY27 guide ~$90B +27-29%
  (orcl-analysis-2026-06-12, Grade A). But equity thesis challenged by the
  balance sheet: FCF -$23.7B FY26 on $55.7B capex (82.7% of revenue), ~$108B ->
  $124B debt trajectory, Baa2/BBB negative outlook, S&P downgrade trigger ~0.2x
  leverage away; ~$300B (~47%) of RPO estimated tracing to OpenAI =
  unprecedented single-customer concentration for an IG issuer (BofA estimate
  cited). Stock -54.9% off high despite the beat (TECH).
- CRWV: neo-cloud adoption proxy: 2025 revenue $5.1B +168%; Q4-25 $1.57B +110%;
  contracted backlog $66.8B; 2026 guide $12-13B (~140% mid); capex $30-35B
  2026; 850 MW active end-2025 across 43 DCs targeting >1.7 GW active
  end-2026; NVIDIA $2B strategic investment Jan-2026 (CRWV Q4-25 call via
  ref-ai-supply-chain-deep-dive). XBRL shows the cost of that growth: NI
  -$626M LQ, -23.3% margin (FIN); vol21 145.1% (TECH).
- NBIS: TTM revenue $873.5M +442% (corrected figure); first positive adjusted
  EBITDA Q1-26 +$129.5M; economic gross-margin correction: headline 74% GM was
  depreciation-excluded -- incl-D&A basis turned positive (+20.85%) for the
  first time only in Q1-26; CFO -$940M ex-deferred-revenue prepayments
  ($3.2B prepayment inflow embedded); deferred revenue $4.78B = 5.4x TTM;
  first secured covenant debt $775M (SOFR+250, DSCR 1.15) July-2026; Altman Z
  2.29 GREY on manufacturing variant vs 3.80 SAFE non-manufacturing; net debt
  roughly neutral after net-cash correction; serial-dilution thesis open
  (nbis-analysis-2026-07-29 / 07-12, Grade A EDGAR provenance).
- Adoption-rate synthesis (DERIVED): the enterprise layer splits into
  (a) application platforms monetizing adoption through software spend
  (PLTR +93%, NOW +24% with ACV acceleration) and (b) infrastructure platforms
  monetizing it through debt-funded capacity (ORCL RPO $638B, CRWV backlog
  $66.8B, NBIS prepayments 5.4x TTM revenue). Group (b) grows faster but its
  numbers are financing constructs as much as demand signals -- every figure in
  group (b) should be read next to the credit line beneath it.

## 5. Stack dependency graph (text form)

```
AI application demand (enterprise adoption: PLTR AIP, NOW workflows)
   |
   v
Cloud/platform capacity decision: self-build vs rent
   |-- RENT: CRWV / NBIS neo-clouds (GPU-as-a-service, prepaid contracts)
   |-- BUILD: hyperscalers on ORCL OCI/RPO-scale commitments
   |        both consume -> SERVERS: DELL ($43B backlog) HPE (Cray+Juniper) SMCI
   |
   +-- every rack needs the fabric:  ANET/CSCO boxes on AVGO/MRVL silicon
   |     optics between racks (COHR/LITE modules, FN assembly)
   |     copper inside racks (CRDO AECs, APH connectors)
   |
   +-- every building needs: colo shell + interconnection (DLR/EQIX xScale)
         power + cooling (see [[ref-energy-power-complex]])
```

Falsifiable monitors: DLR renewal spreads (>1 MW cash marks), EQIX AFFO/share
guide vs print, DELL AI-book conversion rate, ANET AI-networking run-rate vs
$3.25B guide, CRWV MW energized vs 1.7 GW target, NBIS incl-D&A GM staying
positive, ORCL leverage vs the 3.5x trigger.

## 6. Cross-references

- Silicon feeding these racks: [[ref-semiconductor-value-chain]].
- Power/cooling gating layer: [[ref-energy-power-complex]].
- Method + caveats: [[ref-financial-statements]]. Claim provenance:
  wiki/entities/tickers/<T>.md and wiki/investing/analyses/`<name>`-analysis*.md.

## 7. Data gaps

- No xbrl json: NBIS (revenue figures come from analyses with EDGAR provenance).
- AFFO for DLR not directly carried in corpus (only core FFO growth % and
  P/FFO multiples from snapshots); EQIX AFFO is guidance-based.
- EPS: zero points corpus-wide; omitted everywhere (FIN S7).
- Working-capital intensity (DSO/DIO/inventory turns) for DELL/HPE/SMCI not
  present in corpus [flagged gap].
- Factor-store closes end 2026-08-21; later moves invisible here.
