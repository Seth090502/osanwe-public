---
categories: [wiki]
type: reference
status: active
created: 2026-08-24
updated: 2026-08-24
confidence: high
tags:
  - topic/investing
  - topic/semiconductors
  - topic/ai-supply-chain
related: ["[[ref-financial-statements]]", "ref-ai-supply-chain-deep-dive", "ref-memory-storage-cycle-deep-dive", "[[ref-datacenter-infrastructure]]", "[[ref-energy-power-complex]]"]
---

# Semiconductor Value Chain Reference

GENERATED: 2026-08-24 by sector-reference enrichment wave.
REGENERATE: re-run the EDGAR XBRL aggregation over
wiki/investing/filings/`<TICKER>`/`<TICKER>`-xbrl.json (method documented in
[[ref-financial-statements]]), re-pull technical stats from the factor store
(Efforts/osanwe-v2-overhaul/_work/factors.db, bars table, via
tools/factor-store.py --query-bars), and re-read entity signals from
wiki/entities/tickers/<T>.md. Do not hand-edit numbers; regenerate or annotate.
Do NOT hand-edit this file -- it is a derived view of the corpus.

## 0. Method and source keys

- FIN[n] = EDGAR XBRL pull, file wiki/investing/filings/<T>/<T>-xbrl.json;
  quarterly flow figures, latest reported quarter ("LQ") with fiscal quarter
  label; YoY compares same fiscal quarter one year earlier (330-400d window);
  NI margin is TTM net-income margin. Full method + caveats:
  [[ref-financial-statements]] Sections 0 and 7.
- TECH[n] = factor store daily closes (factors.db bars table, src=yfinance),
  window ending 2026-08-21 (499 obs for most names). ret20d/63d/126d/252d are
  simple price returns over trading-day offsets; MA50/MA200; off_hi = distance
  from trailing-window high; vol21 = annualized stdev of last 21 daily returns.
- ENT[k] = vault entity note wiki/entities/tickers/<T>.md, claim grade carried
  through where the note assigns one (HIGH/MEDIUM/LOW).
- DERIVED = arithmetic performed in this document on cited inputs; assumptions
  stated inline. No network sources were used anywhere in this file.
- Known XBRL gaps honored: ARM, ASML, CDNS, GFS, NBIS, TSM have NO xbrl json in
  the corpus (FIN = n/a by construction, see [[ref-financial-statements]]
  Section 7). EPS is n/a corpus-wide (zero points scraped).

## 1. Tier map (one-line-per-layer)

```
Tier 0  IP/EDA          SNPS CDNS ARM            (design tooling + CPU IP royalties)
Tier 1  Equipment       ASML AMAT LRCX KLAC ONTO (litho/deposition/etch/metrology)
Tier 2  Foundry         TSM GFS                  (leading-edge + trailing-edge manufacturing)
Tier 3  Memory          MU SNDK WDC MRAM         (DRAM/HBM, NAND, HDD, emerging NVM)
Tier 4  Compute silicon NVDA AMD INTC QCOM      (GPU/accelerator/CPU/mobile SoC)
Tier 5  Networking      AVGO MRVL ANET CSCO      (switch silicon, custom ASICs, fabrics)
Tier 6  Optical         COHR LITE                (transceivers, EML lasers, photonics)
Downstream consumers: hyperscalers -> see [[ref-datacenter-infrastructure]].
Upstream power/cooling constraints -> see [[ref-energy-power-complex]].
```

## 2. Tier 0 -- EDA and IP (SNPS / CDNS / ARM)

| Name | Role | Rev/LQ (YoY) | NI margin TTM | Price 8/21 | off 52w-hi |
|---|---|---|---|---|---|
| SNPS | EDA #1 (~31-46% share depending on methodology, ENT[SNPS]) | $2.3B (+41.9%) FIN | 8.9% FIN (distorted; NI $17M LQ, -95% YoY) | $397.87 TECH | -35.0% |
| CDNS | EDA #2 (~35-36% share, ENT[CDNS]) | n/a (no xbrl json) FIN | n/a | $319.02 TECH | -23.4% |
| ARM | CPU IP license/royalty (Graviton/Cobalt/Axion base, ENT[ARM]) | n/a (no xbrl json) FIN | n/a | $243.32 TECH | -44.6% |

Per-name detail:

- SNPS: LQ revenue $2.3B +41.9% YoY (FIN, period 2026-04-30 10-Q). NI $17M,
  -95.0% YoY (FIN) -- margin line distorted by acquisition accounting post-Ansys
  close (2024, ENT[SNPS]). Technicals: below both MAs (vs MA200 -10.8%), 1y
  return -33.8%, vol21 30.6% (TECH) -- the de-rated name of the tier.
- CDNS: FY25 revenue guide ~$5.23B; 100% retention, 80-85% recurring revenue
  (ENT[CDNS], ainvest/arvy 2026). Technicals: vs MA200 -2.5%, 1y -7.7%, vol21
  26.0% (TECH).
- ARM: royalty leverage to hyperscaler Arm CPUs (ENT[ARM]). Technicals: +93.8%
  126d but -44.6% off high, vol21 90.3% (TECH) -- highest-beta name in tier.
- Key risks (tier-level): EDA is a duopoly tollgate -- risk is design-cycle
  deceleration, not share loss; export controls on China tooling sales are the
  policy tail both EDA names carry.

## 3. Tier 1 -- Wafer-fab equipment (ASML / AMAT / LRCX / KLAC / ONTO)

| Name | Role | Rev/LQ (YoY) | NI margin TTM | Price 8/21 | 1y return | vs MA200 |
|---|---|---|---|---|---|---|
| ASML | Sole EUV supplier | n/a (no xbrl) FIN | n/a | $1,763.76 TECH | +136.9% | +22.3% |
| AMAT | Broadline dep/etch/inspection | $9.1B (+24.8%) FIN | 30.1% FIN | $492.32 TECH | +208.4% | +24.7% |
| LRCX | Deposition/etch (memory-weighted) | $6.7B (+30.0%) FIN | 31.3% FIN | $314.00 TECH | +218.4% | +23.9% |
| KLAC | Process control/metrology | $3.7B (+15.2%) FIN | 35.6% FIN | $183.99 TECH | +110.6% | +9.4% |
| ONTO | Hybrid bonding / advanced packaging | $343M (+35.3%) FIN | 13.9% FIN | $293.33 TECH | +176.9% | +25.3% |

- ASML: 2025 revenue EUR 32.7B; Q4-25 bookings EUR 13.2B (EUR 7.4B EUV);
  year-end backlog EUR 38.8B; 2026 guidance raised to EUR 36-40B; China mix
  33% (2025) guided to ~20% (2026) (all ENT[ASML] via ref-theme-alpha, HIGH).
  High-NA EUV tools EUR 350M+ favor TSMC as first volume customer (ENT[ASML]).
  Every HBM die requires 1-alpha/1-beta DRAM node which requires EUV -- ASML
  throughput is a binding constraint on HBM capex scaling independent of
  HBM-specific tooling (ENT[ASML], HIGH).
- AMAT: capex-cycle torque with broadest installed base; R&D $4.0B TTM = 12.9%
  of revenue (FIN Section 5). vol21 81.5% -- equipment has traded like the
  memory upcycle it feeds (TECH).
- LRCX: memory-weighted mix makes it the cleanest WFE beta to the HBM/DRAM
  shortage; cash $5.6B vs LTD $3.7B = 1.5x cover (FIN Section 6).
- KLAC: highest NI margin in tier at 35.6% TTM (FIN); process-control intensity
  rises with every node transition and with hybrid-bonding packaging.
- ONTO: pure-play on advanced-packaging metrology/inspection -- the CoWoS
  bottleneck's direct instrument beneficiary; smallest revenue base ($343M LQ),
  highest vol21 of tier at 113.3% (TECH).
- Key risks: China revenue clamp-downs (ASML already guiding mix down, ENT);
  WFE order lumpiness; equipment names are second-derivative plays -- they
  correct before the foundry/memory P&L does.

## 4. Tier 2 -- Foundry (TSM / GFS)

| Name | Role | Rev/LQ (YoY) | NI margin TTM | Price 8/21 | vs MA200 |
|---|---|---|---|---|---|
| TSM | Leading-edge monopoly (70.2% foundry share Q2-25, ENT[TSM]) | n/a (no xbrl) FIN | n/a | $418.95 TECH | +14.7% |
| GFS | Trailing-edge / specialty (power mgmt, photonics SOI) | n/a (no xbrl) FIN | n/a | $48.05 TECH | -8.8% |

- TSM: Q1-26 revenue $35.9B +40.6% YoY at 66.2% gross margin (ENT[TSM] via
  ref-theme-alpha, Digitimes Apr 18 2026, HIGH). HPC 61% of revenue vs 46% in
  Q1-24. 2026 capex raised to $52-56B (HIGH). NVIDIA is the #1 customer at 19%
  of 2025 revenue, passing Apple at 17% (HIGH). CoWoS packaging is the current
  system-level binding constraint: 75-80k wafers/month exiting 2025 targeting
  120-130k end-2026 (HIGH). N2 volume production Q4-2025 at ~65-75% yields;
  N2P H2-26; A16 backside-power H2-26 (HIGH). Substitutable-capacity thesis for
  Taiwan risk implausible through 2028 (HIGH).
- GFS: not in the leading-edge AI compute path; critical for power-management
  ICs and (via Tower Semi) silicon photonics (ENT[GFS]).
- Key risks: TSM carries the binary geopolitical tail -- market prices roughly a
  20% multiple discount for it (ENT[TSM]); Arizona ramp drag. GFS: cyclical
  auto/industrial demand; technical state weakest in this file (63d -40.8%,
  off-high -46.5%, TECH).

## 5. Tier 3 -- Memory and storage (MU / SNDK / WDC / MRAM)

| Name | Product | Rev/LQ (YoY) | NI margin TTM | Price 8/21 | 1y return | vs MA200 |
|---|---|---|---|---|---|---|
| MU | DRAM + HBM leader | $41.5B (+345.7%) FIN | 55.9% FIN* | $966.78 TECH | +726.2% | +69.3% |
| SNDK | NAND pure-play (post-spin) | $9.0B (+371.6%) FIN | 56.5% FIN* | $1,596.08 TECH | +3,494.8% | +69.9% |
| WDC | HDD pure-play (post-spin) | $3.7B (YoY n/m**) FIN | 72.9% FIN* | $459.44 TECH | +509.0% | +28.3% |
| MRAM | MRAM pure-play (small cap) | $19M (+41.9%) FIN | -7.2% FIN | $17.11 TECH | +187.6% | +13.0% |

(*) NI margin flagged suspect by the aggregator (NI within 45d of LQ > 55% of
LQ revenue; likely YTD row mislabeled quarterly) -- verify against cited filing
before use (FIN Section 7). (**) WDC YoY rides a derived Q4 artifact (-186.9%
printed); treat level ($3.7B LQ) as valid, growth print as noise (FIN S7).

- MU: the cycle center of the whole chain. Revenue ladder last 8 reported
  quarters: 7.8 / 8.7 / 8.1 / 9.3 / 11.3 / 13.6 / 23.9 / 41.5 $B (FIN Section
  2) -- an ASP-driven vertical takeoff (bit shipments grew only low-to-mid
  single digits while revenue exploded, per mu-analysis). HBM TAM $35B 2025 ->
  $100B 2028 per Micron disclosure (+40% CAGR pulled forward two years,
  ENT[MU], HIGH); BofA $54.6B CY26 estimate (mu-analysis). CY26 HBM supply
  locked; NVIDIA One Team >50% of NVDA HBM share 2026 (ref-memory-storage-
  cycle ingest). Balance sheet strongest in company history: net cash $6.5B,
  Cash/LTD 2.8x (FIN S6), Altman Z 6.94-11.81 (mu-analysis-2026-04-28). Capex/
  revenue 42.4% FY25 (FIN S4) -- the demand signal is being capitalized into
  supply. NVDA flat GM through the sharpest memory-price shock on record reads
  as Micron pass-through pricing power (ref-theme-alpha 2026-07-16 claim on
  ENT[NVDA]).
- SNDK: NAND pure-play; sold-out posture mirrors WDC; Kioxia 14% stake re-rated
  14x (ref-memory-storage ingest). vol21 150.9% -- highest realized vol of any
  large name in this file (TECH).
- WDC: post-spin pure-HDD; nearline AI-archive demand; "sold out for all of
  2026"; 1y total return +860% at the time of that claim (ENT[WDC] via
  ref-memory-storage-cycle-deep-dive, HIGH).
- MRAM: only public pure-play MRAM; Toggle + 1Gb 28nm STT device; defense +
  edge positioning (ENT[MRAM], HIGH). Micro-cap: $417M mkt cap (FIN).
- Key risks: this tier is a classic commodity cycle wearing an AI costume --
  peak-cycle signature already 2-3/5 on the DOI checklist (SNDK round-2
  inserts); conventional DRAM margins surpassing HBM was flagged as the
  cycle-top hallmark (Q4-25 insert, ref-memory-storage ingest). OpenAI Stargate
  demand of ~900K DRAM wafers/month (~40% of global DRAM) concentrates the
  demand book into one credit (Samsung insert, same ingest).

## 6. Tier 4 -- Compute silicon (NVDA / AMD / INTC / QCOM)

| Name | Role | Rev/LQ (YoY) | NI margin TTM | Price 8/21 | vs MA200 | off hi |
|---|---|---|---|---|---|---|
| NVDA | Accelerator incumbent | $81.6B (+85.2%) FIN | 53.4% FIN* | $214.72 TECH | +10.0% | -8.8% |
| AMD | Challenger accelerator + server CPU | $11.5B (+50.1%) FIN | 15.6% FIN | $473.25 TECH | +43.5% | -18.5% |
| INTC | Foundry turnaround + CPU | $16.1B (+25.4%) FIN | -19.8% FIN | $90.07 TECH | +26.0% | -36.1% |
| QCOM | Mobile/auto SoC, DC entry | $9.9B (-4.0%) FIN | 21.0% FIN | $160.75 TECH | -3.9% | -35.7% |

(*) NVDA NI margin flagged suspect by aggregator (verify; FIN S7).

- NVDA: FY26 revenue $215.9B +65% YoY, GAAP GM 75.0%; Q1-FY27 guide $78B +/-2%
  (SEC 8-K Feb 25 2026 via ENT[NVDA], HIGH). Q4-FY26 DC revenue $62.3B +75%
  (compute $51.3B + networking $11.0B). Four direct customers ~61% of revenue
  in Q3-FY26 10-Q, up from 34% in Q1-FY25 (HIGH) -- concentration materially
  increased through FY26. CoWoS-L >50% booked through 2027 (HIGH). Vera Rubin:
  HBM4 288GB per die / 576GB system-level reconciliation open
  (ref-memory-storage ingest Tier-2 FLAG). Circular vendor-financing fragility:
  ~$1.15T OpenAI-linked commitment chain across Broadcom $350B / Oracle $300B /
  MSFT $250B / NVDA $100B / AMD $90B, >$800B estimated circular; WSJ reported
  the NVDA tranche "stalled" Feb-2026 (challenge-thesis-theme-alpha-2026-07-10 on
  ENT[NVDA]). Forward P/E 22.4x at 2026-06-03 vs 10-year median ~55x (ENT).
- AMD: MI350-series + EPYC named the Q1-26 growth drivers (8-K read via sec.gov,
  Grade B, MEDIUM). MI450/Helios is 2H-2026 guided-not-booked; HBM4 for MI455X
  rides Samsung = direct exposure to the binding memory layer (MEDIUM).
  Structural gap: ~55% GM vs NVDA 75% -- price-taker in the shared compute
  layer, least protected if memory cost outruns accelerator ASP (Grade C
  inference, LOW). Alibaba MI308 order 40-50K units, 192GB HBM3 each (Reuters,
  HIGH).
- INTC: still loss-making (-$11.0B NI LQ, FIN) despite revenue re-acceleration
  (+25.4%); 18A ramp 2025-26 with external-customer traction unresolved
  (ENT[INTC]); Intel-NVIDIA custom DC/PC collaboration with NVLink announced
  Q3-FY26 (ENT[INTC]); SambaNova acquisition claim DISPUTED in corpus
  (FinancialContent says closed; TSG Invest says talks did not materialize,
  $350M Series E instead -- treat as disputed, ENT[INTC]).
- QCOM: mobile annuity flattening (rev -4.0% YoY, FIN); Snapdragon Ride +
  December-2025-reported hyperscaler custom-chip entry (TrendForce via
  ENT[QCOM]) are the optionality.
- Key risks (tier): customer concentration at the top (NVDA 4 customers = 61%);
  vendor-financing circularity; AMD's HBM dependency; INTC execution.

## 7. Tier 5 -- Networking silicon and systems (AVGO / MRVL / ANET / CSCO)

| Name | Role | Rev/LQ (YoY) | NI margin TTM | Price 8/21 | 1y return |
|---|---|---|---|---|---|
| AVGO | Switch ASIC + hyperscaler custom XPU | $22.2B (+47.9%) FIN | n/a (NI sparse) FIN | $368.45 TECH | +27.5% |
| MRVL | Custom ASIC (Trainium) + optical DSP | $2.4B (+27.6%) FIN | 26.5% FIN | $237.04 TECH | +233.5% |
| ANET | Merchant Ethernet switching systems | $3.0B (+37.7%) FIN | 37.7% FIN | $188.65 TECH | +43.5% |
| CSCO | Incumbent campus/data-center networking | $15.8B (+12.0%) FIN | 19.7% FIN | $111.04 TECH | +68.9% |

- AVGO: Q1-FY26 AI revenue $8.4B +106% YoY; $73B AI backlog disclosed (8-K Mar
  4 2026, HIGH); management "line of sight to $100B AI chip revenue by
  2027/2028" (MEDIUM). Six named hyperscaler XPU customers incl. Google + Meta +
  ByteDance + a 4th $10B mystery customer + OpenAI 10GW (Oct 13 2025) + one
  unspecified; OpenAI first-gen XPU deliveries late 2026 with up to $300B
  revenue potential; Anthropic 1GW->3.5GW TPU facilitation (avgo-analysis-
  2026-04-30 extension on ENT[AVGO]). Software mix ~35% post-VMware, EBITDA
  margin 68% (HIGH). Valuation whiplash documented: fwd P/E 27x (Apr snapshot)
  then 36.94x after +32% month rally, 53% above 10-yr PE average (supersede
  note, ENT[AVGO]).
- MRVL: FY26 revenue $8.195B +42.1%, GM 51.0% (~17pp below AVGO 67.8%); FQ1-FY27
  record $2.418B +28%, data center 76% of revenue; TTM FCF $1.85B = 0.73%
  yield, EV/Sales ~22x fwd (mrvl-analysis-2026-06-18 on ENT[MRVL]). Amazon
  Trainium custom silicon is the anchor program; 400G -> 800G -> 1.6T optical
  DSP curve is the second engine (ENT[MRVL]).
- ANET: 2025 closed at $9.0B +28.6%; 2026 guidance raised to $11.25B (+25%) with
  AI networking specifically $1.5B (2025) -> $3.25B (2026) = 2.17x (HIGH).
  Ethernet taking share from InfiniBand in hyperscaler fabrics; coincident with
  compute, lagging one quarter (both ENT[ANET]).
- CSCO: the discipline anchor, not an AI growth name: -89% dot-com drawdown,
  25 years to re-cross its 2000 peak (re-crossed 2025-12-10) (ENT[CSCO], HIGH);
  fwd P/E ~16x vs ANET ~38x (Apr snapshots, ENT).
- Key risks: AVGO/MRVL single-program concentration (OpenAI/Trainium); ANET
  memory-driven cost inflation already flagged in 2026 guidance (ENT[ANET]);
  CSCO relevance decay.

## 8. Tier 6 -- Optical (COHR / LITE)

| Name | Role | Rev/LQ (YoY) | NI margin TTM | Price 8/21 | vol21 |
|---|---|---|---|---|---|
| COHR | Transceivers + photronics (#2 share ~25%) | $2.0B (+33.7%) FIN | 11.3% FIN | $289.52 TECH | 134.3% |
| LITE | EML laser monopoly (200G/lane) | $481M LQ (FY25 Q4d) FIN | n/a FIN | $866.71 TECH | 119.8% |

- COHR: FY25 revenue $5.81B +23%; ~25% transceiver share; NVIDIA 800G
  procurement ~20% wallet; top-5 suppliers (Coherent, Lumentum, Broadcom,
  Accelink, Innolight) ~50% of 2025 transceiver revenue (all ENT[COHR] via
  ref-ai-supply-chain-deep-dive). Named NVIDIA silicon-photonics collaborator
  for Spectrum-X (ENT[COHR]).
- LITE: cloud/datacom 50.2% of FY25 revenue ($1.85B of $3.69B); Q2-FY26
  components $444M +68%, systems $222M +60%; Q2-FY26 guide $630-670M; 50-60%
  global EML share; 200G EML demand exceeds supply by 25-30% (all ENT[LITE]).
  EML scarcity is the gating input on the entire 800G -> 1.6T transition.
- Key risks: extreme realized volatility (vol21 >119% both, TECH); Innolight /
  Chinese transceiver competition compressing module assembly share; LITE
  reports on a June FY so its "latest" XBRL row lags peers by two quarters
  (2025Q2 label, FIN).

## 9. Supply-chain dependency graph (text form)

```
Hyperscaler capex (see [[ref-datacenter-infrastructure]])
   |
   v
NVDA / AMD accelerators ---------------------- needs HBM (MU) ---- needs EUV (ASML)
   |                                                    |              |
   |                                                     \             +-- WFE: AMAT/LRCX/KLAC
   |                                                      \                  (memory-node intensity)
   +-- needs CoWoS packaging (TSM) ---- ONTO inspection/metrology tools
   |        ^
   |        +-- leading-edge wafers also need EUV + High-NA (ASML)
   |
   +-- rack fabric: NVDA NVLink/InfiniBand vs Ethernet (ANET/CSCO on
   |     merchant silicon AVGO Tomahawk/Jericho; MRVL DSPs; CRDO AECs
   |     within-rack; APH connectors; FN assembly)
   |
   +-- optics: 800G/1.6T transceivers (COHR modules; LITE EML lasers
         inside every 200G/lane lane; MKSI lasers adjacency)
   |
   +-- every GPU needs power + cooling (see [[ref-energy-power-complex]]:
         VRT/ETN/GEV layer, grid interconnection queues)
Memory sub-graph:
   MU HBM -> NVDA/AMD accelerators (supply locked CY26)
   MU/SNDK/WDC -> training/inference storage archives (nearline HDD sold out 2026)
Design sub-graph (everything upstream starts here):
   SNPS/CDNS EDA + ARM IP -> every TSM/GFS tape-out -> all tiers above
Trailing-edge sub-graph:
   GFS specialty nodes -> power-management ICs + silicon photonics support
```

Reading rules: an interruption at any single-box layer propagates everywhere
downstream; the graph's narrowest boxes are ASML (sole EUV), TSM (CoWoS +
leading edge), LITE (EML), MU (locked CY26 HBM), and the EDA duopoly.

## 10. Chokepoint hierarchy -- most irreplaceable first

Ranked by substitutability (time-to-replace and capacity uniqueness), using
corpus claims; grades are the source claims', ranking judgment is DERIVED.

1. ASML -- sole EUV supplier; every leading-edge logic AND every HBM DRAM node
   requires EUV; EUR 38.8B backlog (HIGH, ENT[ASML]). Replacement: none.
   Decade-scale moat.
2. TSM -- 70.2% foundry share, monopoly leading edge, CoWoS the system-binding
   constraint; substitutable-capacity thesis "implausible through 2028" (HIGH,
   ENT[TSM]). Replacement: multi-year, multi-site, unproven.
3. SNPS/CDNS (EDA duopoly, combined ~70%+ share) -- nothing ships without their
   toolchains; switching costs are decade-scale (share figures MEDIUM,
   ENT[SNPS]/ENT[CDNS]; duopoly status DERIVED).
4. MU -- CY26 HBM effectively locked; NVIDIA One Team >50% share of NVDA HBM
   (HIGH, ref-memory ingest); HBM TAM compounding 40%/yr to $100B 2028 (Micron,
   HIGH). Replacement: Samsung/SK Hynix exist but allocation is committed.
5. LITE -- 200G EML demand exceeds supply 25-30%; 50-60% global EML share
   (HIGH/MEDIUM, ENT[LITE]). Every 1.6T lane needs these lasers.
6. NVDA -- not irreplaceable at the silicon layer (ASICs rising) but
   irreplaceable at the CUDA/software ecosystem layer; 75% GM evidences
   bottleneck-adjacent pricing power (ref-theme-alpha 2026-07-16 framing).
7. AVGO -- custom-XPU co-design partner of record to six hyperscalers; $73B AI
   backlog (HIGH, ENT[AVGO]). Replaceable per-program over 2-3 yrs, not in
   aggregate.
8. ARM -- instruction-set gravity for hyperscaler CPUs (Graviton/Cobalt/Axion);
   replaceable per-workload (x86/RISC-V) but not at fleet scale quickly
   (MEDIUM, DERIVED from ENT[ARM]).
9. AMAT/LRCX/KLAC/ONTO -- critical but multiplexed: several vendors per process
   step except ONTO's hybrid-bonding niche and KLAC's process-control lead
   (DERIVED from role descriptions, ENT).
10. ANET/MRVL/COHR/CSCO/GFS/QCOM/INTC/SNDK/WDC/MRAM -- substitutable within
    their layers on 1-3yr horizons (judgment DERIVED; per-name evidence above).

Corollary (DERIVED): chokepoint rents concentrate where the dependency graph
has single boxes -- long-duration outperformance should be expected to persist
in ASML/TSM/MU/LITE relative to layer-peers unless capacity or technology
substitutes emerge; monitor CoWoS wafers/month and EML supply-demand balance as
the two most falsifiable chokepoint metrics.

## 11. Cross-references

- Downstream buyers and the 800G/1.6T transition detail:
  [[ref-datacenter-infrastructure]].
- Power/cooling constraint that gates all of the above:
  [[ref-energy-power-complex]].
- Statement-level financial method and caveats: [[ref-financial-statements]].
- Memory cycle mechanics: [[ref-memory-storage-cycle-deep-dive-ingest-2026-05-06]].
- Entity notes with full claim provenance: wiki/entities/tickers/<T>.md.

## 12. Data gaps

- No xbrl json: ARM, ASML, CDNS, GFS, TSM (and NBIS, outside this file) --
  revenue lines for those names come from entity-note claims instead (FIN S7).
- EPS: zero points corpus-wide; not shown anywhere (FIN S7).
- Suspect-margin flags apply to MU, NVDA, SNDK, WDC rows (FIN S7).
- Factor-store closes end 2026-08-21; anything after that date is invisible to
  TECH[n] cites here.

---------------------------------------------------------------
APPENDIX (2026-08-24 expansion wave): Sections 13-17 below are a
deep-dive layer generated from the same sources as Sections 0-12
plus the wave-analysis corpus. Existing content above is preserved
verbatim; nothing in Sections 0-12 was altered.
---------------------------------------------------------------

## 13. Per-company deep profiles (EDGAR XBRL + factor store bars + entity notes)

Format per profile: quarterly revenue table (last 12 reported fiscal quarters
from <T>-xbrl.json where the file exists; entity-note anchors for TSM/ASML/
CDNS/ARM/GFS which have no xbrl json), computed YoY, net-margin trajectory,
R&D intensity, technical state (5y ann return / vol / Sharpe(rf=0) / maxDD /
beta(252d) / corr-vs-SPY(252d) / price vs MA50/MA200 / RSI14 at 2026-08-21),
drawdown episodes >=20% from bars, supply-chain role with upstream/downstream
dependencies from ENT[<T>], and key risks from the latest wave analysis file
in Efforts/osanwe-v2-overhaul/_work/ (rating + confidence quoted). All numbers
DERIVED this session from the cited stores; no network used.


### 13.1 NVDA -- NVIDIA Corporation (Tier 4 compute)
Sources: FIN[NVDA]=wiki/investing/filings/NVDA/NVDA-xbrl.json | TECH=factors.db bars
1255 obs 2021-08-24..2026-08-24 | ENT[NVDA]=wiki/entities/tickers/NVDA.md |
WAVE=Efforts/osanwe-v2-overhaul/_work/wave1-nvda-analysis.md (HOLD, conf 70).

Quarterly revenue, last 12 reported fiscal quarters (11 points in corpus; Q4d =
derived FY-10-K minus three 10-Q quarters, aggregator convention):
| # | Fiscal period | Revenue $B | YoY | NI $B | NI margin |
|---|---|---|---|---|---|
| 1 | 2023-07-30 | 13.51 | n/a | 6.19 | 45.8% |
| 2 | 2023-10-29 | 18.12 | n/a | 9.24 | 51.0% |
| 3 | 2024-04-28 | 26.04 | n/a | 14.88 | 57.1% |
| 4 | 2024-07-28 | 30.04 | +122.4% | 16.60 | 55.3% |
| 5 | 2024-10-27 | 35.08 | +93.6% | 19.31 | 55.0% |
| 6 | 2025-01-26 (Q4d) | 39.33 | n/a | n/a | n/a |
| 7 | 2025-04-27 | 44.06 | +69.2% | 18.77 | 42.6% |
| 8 | 2025-07-27 | 46.74 | +55.6% | 26.42 | 56.5% |
| 9 | 2025-10-26 | 57.01 | +62.5% | 31.91 | 56.0% |
| 10 | 2026-01-25 (Q4d) | 68.13 | +73.2% | n/a | n/a |
| 11 | 2026-04-26 | 81.61 | +85.2% | 58.32 | 71.5% |

- Cross-check: the four FY26 quarters (44.06 + 46.74 + 57.01 + 68.13) sum to
  $215.9B, matching the FY26 revenue $215.9B +65% quoted in ENT[NVDA] (8-K,
  HIGH). LQ NI margin 71.5% carries the aggregator SUSPECT flag (FIN S7);
  verify against the 10-Q before trading on it.
- R&D: $20.8B TTM = 8.2% of revenue (FIN-S5, TTM ending 2026-04-26). Lowest
  R&D intensity of any profiled design name -- the moat is ecosystem, not
  spend. Capex/revenue: n/a (no FY capex+revenue pair in corpus, FIN S4);
  NVDA is asset-light -- capacity is bought via TSM CoWoS allocation and MU
  HBM purchase commitments, not own fabs.
- Technical state (TECH): 5y ann return 57.8% | ann vol 51.4% |
  Sharpe(rf=0) 0.89 | maxDD -66.3% | beta(252d) 1.89 | corr vs SPY(252d) 0.66.
  Price 8/21 $214.72: +3.4% vs MA50, +10.0% vs MA200, RSI14 59.
  Drawdowns >=20% (TECH):
  - 2021-11-29 @33.27 -> 2022-10-14 @11.2 = -66.3%; recovered 2023-05-25
  - 2024-06-18 @135.36 -> 2024-08-07 @98.75 = -27.1%; recovered 2024-10-14
  - 2025-01-06 @149.21 -> 2025-04-04 @94.18 = -36.9%; recovered 2025-06-25
  - 2025-10-29 @206.78 -> 2026-03-30 @164.98 = -20.2%; recovered 2026-04-24
- Supply-chain role and dependencies (ENT[NVDA], existing file Sections 6/9):
  system-level integrator. Upstream: TSM leading-edge wafers (N3/N4 class;
  NVDA is TSM #1 customer at ~19-22%) + CoWoS-L packaging (>50% booked
  through 2027, HIGH); HBM from SK Hynix/Micron (SKH 'One Team' >50% of NVDA
  HBM share 2026, HIGH); ETLA toolchains upstream-of-design; 800G optics via
  COHR/LITE components in its rack fabrics. Downstream: hyperscaler capex --
  four direct customers = 61% of Q3-FY26 revenue (10-Q, up from 34% in
  Q1-FY25); NBIS Meta $27B 5-yr deal; OpenAI 10GW / $100B linkage.
- Key risks (WAVE1-NVDA, probabilities as stated there): cohort multiple
  de-rate on rate gravity 45%/HIGH (FCF yield ~2.4% vs DGS10 above band);
  Rubin/HBM4 execution air-pocket 40%/HIGH, partially realized;
  custom-silicon structural displacement 35% in-window / 52% structural.
  Tail from ENT: ~$1.15T OpenAI-linked vendor-financing chain with the NVDA
  tranche reported 'stalled' Feb-2026 (challenge-thesis-theme-alpha-2026-07-10).
### 13.2 TSM -- Taiwan Semiconductor Manufacturing (Tier 2 foundry)
Sources: no <T>-xbrl.json in corpus (FIN = n/a by construction; foreign private
issuer files 20-F/6-K which the EDGAR-XBRL pipeline does not capture). FY-level
XBRL exists at wiki/investing/filings/TSM/TSM-xbrl-extended.json (generated
2026-08-24 from SEC data.sec.gov company-concept API) -- 20-F annual rows only.
TECH=factors.db bars 1255 obs 2021-08-24..2026-08-24 |
ENT[TSM]=wiki/entities/tickers/TSM.md | WAVE=wave1-tsm-analysis.md (HOLD, conf 74).

Quarterly revenue: NOT in the standard xbrl corpus. Entity-note quarterly ladder
instead (ENT[TSM], grades as carried there):
| # | Quarter | Revenue $B | YoY | GM | Source grade |
|---|---|---|---|---|---|
| 1 | Q1-2025 | ~25.5 (implied by FY25 $122B split) | -- | -- | DERIVED, do not use standalone |
| 2 | Q4-2025 (FY25 total) | 122.0 FY (+35.9% USD) | -- | 59.9% | HIGH per tsm-analysis-2026-04-30 |
| 3 | Q1-2026 | 35.9 | +40.6% | 66.2% record | HIGH, Digitimes Apr 18 2026 via ref-theme-alpha |
| 4 | Q2-2026 | 40.2 | +33.7% | 67.72% record | HIGH, tsm-analysis-2026-07-16 (Q2 print) |
| 5 | Q3-2026 guide | 44.6-45.8 | -- | 65-67% guide-down | HIGH, tsm-analysis-2026-07-16 |

- Net-margin trajectory (entity-note claims, HIGH): NPM 50.5% Q1-26; OM 56-58%
  band guided Q3-26; FY25 ROIC 52.18% NOPAT/IC convention (re-pinned 7/30).
- R&D: n/a in corpus (no xbrl json; not scraped for 20-F filers).
- Annual XBRL anchors (TSM-xbrl-extended.json, 20-F rows): op income 30.09B
  (FY23) -> 40.32B (FY24); capex 31.02B (FY23) -> 29.16B (FY24); FCF computed
  9.54B (FY23) -> 26.54B (FY24); OCF 55.69B FY24.
- Technical state (TECH): 5y ann return 31.9% | ann vol 38.3% | Sharpe 0.72 |
  maxDD -56.5%. Beta(252d) 2.19, corr vs SPY 0.69. Price 8/21 $418.95: -1.3%
  vs MA50, +14.7% vs MA200, RSI14 59. Drawdowns >=20% (TECH):

  - 2022-01-14 @130.73 -> 2022-11-03 @56.91 = -56.5%; recovered 2024-03-04
  - 2024-07-10 @186.26 -> 2024-08-05 @144.24 = -22.6%; recovered 2024-10-11
  - 2025-01-23 @220.49 -> 2025-04-08 @139.31 = -36.8%; recovered 2025-06-26
  - 2026-06-30 @477.57 -> 2026-07-29 @374.67 = -21.6%; **STILL OPEN**
- Supply-chain role and dependencies: the chain's manufacturing hub.
  Upstream: ASML EUV/High-NA (sole supplier), AMAT/LRCX/KLAC/ONTO WFE,
  MU/SK Hynix HBM sits downstream of its packaging, GFS absent from its path.
  Downstream: NVDA (~19-22% of revenue, #1 customer passing Apple ~17-18%),
  Apple, MediaTek 9%, Qualcomm 8%, AMD 7%; top-10 customers 76% of revenue.
  CoWoS 75-80k wpm exiting 2025 -> 120-130k end-2026 target; sold out >1yr.
- Key risks (WAVE1-TSM + ENT): margin normalization FM3 55% FIRING (Q3-26 GM
  guide-down on 2nm+Arizona dilution); rates/multiple compression FM4 45%;
  Taiwan kinetic tail 7%/12mo with CATASTROPHIC cascade (market prices ~20%
  multiple discount; ADR-basis measurement wedge ~10% documented 7/30);
  Section 301 tariffs 10-12.5% mature-node-weighted effective 7/24/26.

### 13.3 AVGO -- Broadcom (Tier 5 networking)
Sources: FIN[AVGO]=wiki/investing/filings/AVGO/AVGO-xbrl.json | TECH bars 1255
obs | ENT[AVGO] | WAVE=waveN-avgo-analysis.md (HOLD, conf 76).

Quarterly revenue, last 12 reported (11 points; Q4d derived):
| # | Fiscal period | Revenue $B | YoY | NI $B | NI margin |
|---|---|---|---|---|---|
| 1 | 2023-07-30 | 8.88 | n/a | n/a | n/a |
| 2 | 2024-02-04 | 11.96 | n/a | n/a | n/a |
| 3 | 2024-05-05 | 12.49 | n/a | n/a | n/a |
| 4 | 2024-08-04 | 13.07 | +47.3% | n/a | n/a |
| 5 | 2024-11-03 (Q4d) | 14.05 | n/a | n/a | n/a |
| 6 | 2025-02-02 | 14.92 | +24.7% | n/a | n/a |
| 7 | 2025-05-04 | 15.00 | +20.2% | n/a | n/a |
| 8 | 2025-08-03 | 15.95 | +22.0% | n/a | n/a |
| 9 | 2025-11-02 (Q4d) | 18.02 | +28.2% | n/a | n/a |
| 10 | 2026-02-01 | 19.31 | +29.5% | n/a | n/a |
| 11 | 2026-05-03 | 22.19 | +47.9% | n/a | n/a |

- Net-margin trajectory: NI rows are sparse/garbled in this ticker's scrape
  (NI = n/a throughout; FIN S7) -- use entity-note EBITDA margin ~68%, software
  mix ~35% post-VMware (HIGH, ENT[AVGO]) instead of scraped net income.
- R&D: $12.0B TTM = 15.9% of revenue (FIN-S5, TTM ending 2026-05-03).
  Capex/revenue just 1.0% FY-end 2025-11-02 (FIN-S4) -- asset-light designer.
- Technical state (TECH): 5y ann return 52.9% | vol 43.9% | Sharpe 0.97 (best
  risk-adjusted in the whole 20-name set) | maxDD -41.1%. Beta(252d) 2.16,
  corr vs SPY 0.57. Price 8/21 $368.45: -5.1% vs MA50, +0.04% vs MA200
  (sitting exactly ON it), RSI14 39. Drawdowns >=20%:

  - 2024-06-17 @178.94 -> 2024-08-07 @133.75 = -25.2%; recovered 2024-10-09
  - 2024-12-16 @246.19 -> 2025-04-04 @144.88 = -41.1%; recovered 2025-06-02
  - 2025-12-10 @410.67 -> 2026-03-30 @292.95 = -28.7%; recovered 2026-04-22
  - 2026-06-02 @480.81 -> 2026-07-02 @360.45 = -25.0%; **STILL OPEN**
- Supply-chain role and dependencies: merchant switch silicon (Tomahawk 6
  102 Tb/s, Jericho3-AI) + custom XPU co-design to SIX hyperscaler customers
  (Google Ironwood TPU v7, Meta MTIA partial, ByteDance, a 4th $10B customer,
  OpenAI 10GW first-gen deliveries late 2026, one unspecified). Upstream: TSM
  leading-edge wafers + CoWoS; MU/SKH HBM (custom-ASIC HBM demand +82% YoY
  2026 -> ~1/3 of HBM market per Goldman, ENT[AVGO]); EDA upstream-of-design.
  Downstream: hyperscaler capex directly; ANET/CSCO boxes ride its silicon.
- Key risks (WAVE-N-AVGO): rate-regime multiple compression 55%;
  Google/MediaTek custom-silicon fragmentation 55%; VMware integration debt +
  EU regulatory tail 42%. Valuation whiplash documented (fwd P/E 27x -> 36.9x
  in 8 days, ENT[AVGO]).
### 13.4 AMD -- Advanced Micro Devices (Tier 4 compute)
Sources: FIN[AMD]=wiki/investing/filings/AMD/AMD-xbrl.json | TECH 1255 obs |
ENT[AMD] | WAVE=wave2-amd-analysis.md (HOLD, conf 68).

Quarterly revenue, last 12 reported (11 points; Q4d derived; one stale 2017
row exists in-file and is dropped by the window filter):
| # | Fiscal period | Revenue $B | YoY | NI $B | NI margin |
|---|---|---|---|---|---|
| 1 | 2023-09-30 | 5.80 | n/a | 0.30 | 5.2% |
| 2 | 2024-03-30 | 5.47 | n/a | 0.12 | 2.2% |
| 3 | 2024-06-29 | 5.83 | n/a | 0.27 | 4.5% |
| 4 | 2024-09-28 | 6.82 | +17.6% | 0.77 | 11.3% |
| 5 | 2024-12-28 (Q4d) | 7.66 | n/a | n/a | n/a |
| 6 | 2025-03-29 | 7.44 | +35.9% | 0.71 | 9.5% |
| 7 | 2025-06-28 | 7.68 | +31.7% | 0.87 | 11.3% |
| 8 | 2025-09-27 | 9.25 | +35.6% | 1.24 | 13.4% |
| 9 | 2025-12-27 (Q4d) | 10.27 | +34.1% | n/a | n/a |
| 10 | 2026-03-28 | 10.25 | +37.8% | 1.38 | 13.5% |
| 11 | 2026-06-27 | 11.54 | +50.1% | 2.30 | 19.9% |

- Net-margin trajectory: 5.2% -> 11.3% -> 13.4% -> 19.9% LQ -- structurally
  rising but still ~1/3 of NVDA's level. The 2025-12-27 Q4d row has no
  comparable NI point (Q4d derivation only covers revenue).
- R&D: $9.4B TTM = 22.7% of revenue (FIN-S5) -- second-highest R&D intensity
  in this file after SNPS. Capex light: FY24 capex $0.64B on $25.8B revenue.
- Technical state (TECH): 5y ann return 33.8% | vol 56.6% | Sharpe 0.51 |
  maxDD -65.4%. Beta(252d) 3.16 (highest of the compute tier), corr vs SPY
  0.57. Price 8/21 $473.25: -7.2% vs MA50, +43.5% vs MA200, RSI14 47.
  Drawdowns >=20%:

  - 2021-11-29 @161.91 -> 2022-10-14 @55.94 = -65.5%; recovered 2024-01-18
  - 2024-03-07 @211.38 -> 2025-04-08 @78.21 = -63.0%; recovered 2025-10-07
  - 2025-10-29 @264.33 -> 2026-03-03 @190.95 = -27.8%; recovered 2026-04-16
  - 2026-06-30 @580.91 -> 2026-07-29 @429.56 = -26.1%; **STILL OPEN**
- Supply-chain role and dependencies: challenger accelerator + server CPU.
  Upstream: TSM N3P/N2 wafers + CoWoS allocation ~105K wafers 2026 (11% of
  demand vs NVDA ~60%, per amd-analysis-2026-04-30 in ENT[TSM]); HBM4 for
  MI455X rides SAMSUNG -- direct exposure to the binding memory layer
  (MEDIUM); MI400 432GB HBM4 ladder documented in ENT[AMD]. Downstream:
  Alibaba 40-50K MI308 order at 192GB HBM3 each (Reuters, HIGH); Oracle 50K
  MI450 Q3-26; hyperscaler EPYC fleets.
- Key risks (WAVE2-AMD): valuation compression FM2 50%/HIGH (fwd P/E 59-70x,
  FCF yield ~1% FAIL vs rate band); MI450/Helios ramp slippage 40%/HIGH
  (guided-not-booked; Samsung HBM4 dependency); custom-silicon displacement
  45% structural / 25% in-window. Structural GM gap ~55% vs NVDA 75% =
  price-taker if memory cost outruns accelerator ASP (Grade C inference, LOW).

### 13.5 MU -- Micron Technology (Tier 3 memory)
Sources: FIN[MU]=wiki/investing/filings/MU/MU-xbrl.json | TECH 1255 obs |
ENT[MU] | WAVE=wave1-mu-analysis.md (HOLD, conf 55).

Quarterly revenue, last 12 reported (11 points; Q4d derived):
| # | Fiscal period | Revenue $B | YoY | NI $B | NI margin |
|---|---|---|---|---|---|
| 1 | 2023-11-30 | 4.73 | n/a | -1.23 | -26.1% |
| 2 | 2024-02-29 | 5.82 | n/a | 0.79 | 13.6% |
| 3 | 2024-05-30 | 6.81 | n/a | 0.33 | 4.9% |
| 4 | 2024-08-29 (Q4d) | 7.75 | n/a | n/a | n/a |
| 5 | 2024-11-28 | 8.71 | +84.3% | 1.87 | 21.5% |
| 6 | 2025-02-27 | 8.05 | +38.3% | 1.58 | 19.7% |
| 7 | 2025-05-29 | 9.30 | +36.6% | 1.89 | 20.3% |
| 8 | 2025-08-28 (Q4d) | 11.31 | +46.0% | n/a | n/a |
| 9 | 2025-11-27 | 13.64 | +56.7% | 5.24 | 38.4% |
| 10 | 2026-02-26 | 23.86 | +196.3% | 13.79 | 57.8% |
| 11 | 2026-05-28 | 41.46 | +345.7% | 28.24 | 68.1% |

- Net-margin trajectory: -26.1% -> +21.5% -> 38.4% -> 57.8% -> 68.1% LQ --
  the steepest margin inflection in the file. LQ margins carry the aggregator
  SUSPECT flag (>55% of revenue within 45d of LQ; FIN S7) -- consistent with
  entity-note NBM contract economics (~80% GM floors) but verify against the
  10-Q before trading.
- R&D: $4.8B TTM = 5.3% of revenue (FIN-S5, TTM ending 2026-05-28) -- lowest
  R&D intensity in the file; memory R&D scales with nodes not headcount.
  Capex/revenue 42.4% FY-end 2025-08-28 ($15.86B capex / $37.38B rev,
  FIN-S4); FY26 capex raised $20B -> $25B (Mar 18 2026 call, HIGH); 9-month
  FY26 capex $19.6B +92.2% YoY (ref-theme-alpha on 10-Q filed 6/25).
  Cash/LTD 2.8x, net cash $6.5B (FIN-S6).
- Technical state (TECH): 5y ann return 67.4% (best CAGR in set) | vol 56.2%
  | Sharpe 0.92 | maxDD -57.6%. Beta(252d) 3.37, corr vs SPY 0.54. Price 8/21
  $966.78: +0.2% vs MA50, +69.3% vs MA200, RSI14 69. Drawdowns >=20%:

  - 2024-06-18 @152.36 -> 2025-04-04 @64.56 = -57.6%; recovered 2025-09-12
  - 2025-11-10 @253.05 -> 2025-11-20 @201.17 = -20.5%; recovered 2025-12-10
  - 2026-03-18 @461.47 -> 2026-03-30 @321.75 = -30.3%; recovered 2026-04-14
  - 2026-06-25 @1213.37 -> 2026-07-29 @739.0 = -39.1%; **STILL OPEN**
- Supply-chain role and dependencies: the cycle center. Upstream: ASML EUV
  (every 1-alpha/1-beta DRAM node), AMAT/LRCX deposition+etch (TSV, cryogenic
  NAND channels), TSM base-die for HBM4 with SK Hynix. Downstream: NVDA/AMD
  accelerators (CY26 supply locked; SKH 'One Team' >50% NVDA share), AVGO/
  MRVL custom ASICs (+82% HBM demand growth), OpenAI Stargate ~900K DRAM
  wafers/month demand concentration (~40% of global DRAM).
- Key risks (WAVE1-MU): beat-and-drop positioning unwind into FQ4 print 55%
  (>=10% drawdown prob); GM cliff/pricing roll into FY27 40%; 2027-28
  synchronized oversupply 35%. Cycle-top hallmarks already flagged: DOI
  checklist 2-3/5; conventional DRAM margins surpassing HBM (ref-memory ingest).
### 13.6 ASML -- ASML Holding (Tier 1 equipment)
Sources: no xbrl json (only a legacy SC 13G list in wiki/investing/filings/
ASML/) -- fundamentals from ENT[ASML] via ref-theme-alpha 6-K reads (grades
carried). TECH bars 1255 obs. WAVE=waveS-asml-analysis.md (HOLD, conf 70).

Quarterly revenue: n/a in XBRL corpus. Entity-note anchors instead:
- FY2025 revenue EUR 32.7B; Q1-2026 EUR 8.8B at 53.0% GM (6-K 4/15, HIGH).
- Q4-25 bookings record EUR 13.2B (EUR 7.4B EUV); YE2025 backlog EUR 38.8B.
- 2026 guidance RAISED to EUR 36-40B; China mix 33% (2025) -> ~20% (2026).
- YoY on the Q1 anchor: EUR 8.8B vs EUR 5.29B Q1-25 = +66% [DERIVED from
  entity-note FY figures; treat as indicative, not filing-grade].
- Net margin / R&D %: not in corpus (no scraped NI or R&D rows for 20-F/6-K
  filers). Capex flow INTO ASML is its bookings line above.
- Technical state (TECH): 5y ann return 17.9% | vol 43.4% | Sharpe 0.38 |
  maxDD -56.9%. Beta(252d) 2.30, corr vs SPY 0.64. Price 8/21 $1763.76:
  -0.9% vs MA50, +22.3% vs MA200, RSI14 63. Drawdowns >=20%:

  - 2021-09-15 @848.49 -> 2022-10-14 @366.02 = -56.9%; recovered 2024-01-25
  - 2024-07-10 @1078.84 -> 2025-04-08 @588.16 = -45.5%; recovered 2025-12-01
  - 2026-06-30 @1986.87 -> 2026-07-29 @1550.69 = -21.9%; **STILL OPEN**
- Supply-chain role and dependencies: sole EUV supplier on earth; every
  leading-edge logic node AND every HBM DRAM node routes through Veldhoven.
  Upstream: Zeiss-class optics supply web. Downstream: TSM (High-NA first
  volume customer), Samsung, Intel, SK Hynix (~$8B for ~30 EUV systems by
  Dec-2027), MU. Low-NA capacity ~65 systems 2026, +30% planned 2027; DUV
  immersion ~130 (+30% 2027) per 6-K quote (system-count reading Grade C).
- Key risks (WAVE-S-ASML): China export-control tightening ~40%/12mo (ratchet
  history Oct22->Oct23->Dec24->Jan25->Apr25 H20 block->Jul25 reversal with
  15%-of-China-revenue remit); WFE cycle turn ~35% (book-to-bill <1 for two
  quarters = de-rate trigger); Taiwan kinetic tail ~7% CATASTROPHIC cascade.
  High-NA adoption concentration (TSMC-first) is a listed execution risk.

### 13.7 AMAT -- Applied Materials (Tier 1 equipment)
Sources: FIN[AMAT]=wiki/investing/filings/AMAT/AMAT-xbrl.json | TECH 1255 obs
| ENT[AMAT] | WAVE=waveS-amat-analysis.md (HOLD, conf 55).

Quarterly revenue, last 12 reported (11 points; Q4d derived):
| # | Fiscal period | Revenue $B | YoY | NI $B | NI margin |
|---|---|---|---|---|---|
| 1 | 2024-01-28 | 6.71 | n/a | 2.02 | 30.1% |
| 2 | 2024-04-28 | 6.65 | n/a | 1.72 | 25.9% |
| 3 | 2024-07-28 | 6.78 | n/a | 1.71 | 25.2% |
| 4 | 2024-10-27 (Q4d) | 7.04 | n/a | n/a | n/a |
| 5 | 2025-01-26 | 7.17 | +6.8% | 1.19 | 16.5% |
| 6 | 2025-04-27 | 7.10 | +6.8% | 2.14 | 30.1% |
| 7 | 2025-07-27 | 7.30 | +7.7% | 1.78 | 24.4% |
| 8 | 2025-10-26 (Q4d) | 6.80 | +-3.5% | n/a | n/a |
| 9 | 2026-01-25 | 7.01 | +-2.1% | 2.03 | 28.9% |
| 10 | 2026-04-26 | 7.91 | +11.4% | 2.81 | 35.5% |
| 11 | 2026-07-26 | 9.12 | +24.8% | 2.54 | 27.8% |

- Net-margin trajectory: 16.5% trough quarter (2025-01-26, $1.19B NI on
  $7.17B rev) back to 28-35% band; LQ 27.8%. TTM NI margin 30.1% (FIN).
- R&D: $3.96B TTM = 12.8% of revenue (FIN-S5 computed; FIN-S5 doc shows
  12.9% on same TTM window ending 2026-07-26 -- rounding). Capex FY24
  $1.19B (10-K period 2024-10-27).
- Technical state (TECH): 5y ann return 31.0% | vol 47.0% | Sharpe 0.58 |
  maxDD -55.1%. Beta(252d) 2.76, corr vs SPY 0.60. Price 8/21 $492.32:
  -12.1% vs MA50, +24.7% vs MA200, RSI14 44. Drawdowns >=20%:

  - 2022-01-14 @160.49 -> 2022-10-17 @72.0 = -55.1%; recovered 2023-12-26
  - 2024-07-10 @250.48 -> 2025-04-04 @125.53 = -49.9%; recovered 2025-11-28
  - 2026-06-30 @722.23 -> 2026-07-29 @435.98 = -39.6%; **STILL OPEN**
- Supply-chain role and dependencies: broadline deposition/etch/inspection
  with the largest installed base; HBM through-silicon-via etch+deposition
  tools named in ENT[AMAT]. Upstream: subcomponents, precision optics.
  Downstream: every IDM/foundry -- TSM capex $52-56B (raised to $60-64B on
  the Q2 print), memory IDMs ~$65B aggregate 2026, WFE 2026 ~$135B (LRCX
  guide, HIGH).
- Key risks (WAVE-S-AMAT): capex-cycle rollover / 2027 memory digestion
  25-30%/24mo (WFE turns LAST but falls hardest); multiple mean-reversion at
  85% vol 30-35%; China export-control escalation + indigenous substitution
  20-25% (NAURA/AMEC absorbing sockets); Taiwan tail unranked but complex-wide.
### 13.8 LRCX -- Lam Research (Tier 1 equipment)
Sources: FIN[LRCX]=wiki/investing/filings/LRCX/LRCX-xbrl.json | TECH 1255 obs
| ENT[LRCX] | WAVE=waveS-lrcx-analysis.md (HOLD, conf 50).

Quarterly revenue, last 12 reported (11 points; Q4d derived; one stale 2012
row in-file is dropped by the window filter):
| # | Fiscal period | Revenue $B | YoY | NI $B | NI margin |
|---|---|---|---|---|---|
| 1 | 2023-09-24 | 3.48 | n/a | 0.89 | 25.5% |
| 2 | 2023-12-24 | 3.76 | n/a | 0.95 | 25.4% |
| 3 | 2024-03-31 | 3.79 | n/a | 0.97 | 25.5% |
| 4 | 2024-09-29 | 4.17 | +19.7% | 1.12 | 26.8% |
| 5 | 2024-12-29 | 4.38 | +16.4% | 1.19 | 27.2% |
| 6 | 2025-03-30 | 4.72 | +24.4% | 1.33 | 28.2% |
| 7 | 2025-06-29 (Q4d) | 5.17 | n/a | n/a | n/a |
| 8 | 2025-09-28 | 5.32 | +27.7% | 1.57 | 29.5% |
| 9 | 2025-12-28 | 5.34 | +22.1% | 1.59 | 29.8% |
| 10 | 2026-03-29 | 5.84 | +23.8% | 1.83 | 31.2% |
| 11 | 2026-06-28 (Q4d) | 6.72 | +30.0% | n/a | n/a |

- Net-margin trajectory: steady climb 25.5% -> 31.2%; LQ (Q4d) has no NI
  point by construction. TTM NI margin 31.3% (FIN).
- R&D: $2.26B TTM computed = 9.7% of revenue (FIN-S5 doc prints 10.2%/2.4B on
  its window ending 2026-06-28 -- same source, window-edge difference).
  Capex points absent from corpus (no Capex concept rows scraped, FIN S7).
  Balance sheet: cash $5.6B vs LTD $3.7B = 1.5x cover (FIN-S6).
- Technical state (TECH): 5y ann return 40.9% | vol 49.1% | Sharpe 0.70 |
  maxDD -56.4%. Beta(252d) 3.27, corr vs SPY 0.66. Price 8/21 $314.00:
  -6.9% vs MA50, +23.9% vs MA200, RSI14 57. Drawdowns >=20%:

  - 2022-01-14 @69.6 -> 2022-10-14 @30.35 = -56.4%; recovered 2023-07-28
  - 2024-07-10 @110.82 -> 2025-04-04 @58.62 = -47.1%; recovered 2025-09-11
  - 2026-02-25 @249.01 -> 2026-03-06 @199.19 = -20.0%; recovered 2026-04-09
  - 2026-06-30 @433.33 -> 2026-07-29 @252.35 = -41.8%; **STILL OPEN**
- Supply-chain role and dependencies: deposition/etch with memory weighting --
  the cleanest WFE beta to the HBM/DRAM shortage; cryogenic etch for
  high-aspect-ratio NAND channels (ENT[LRCX]); captures ~$8B per $100B
  incremental DC investment (MEDIUM). Upstream: subcomponents. Downstream:
  memory IDM capex aggregate ~$65B 2026 (SKH $20.5B...), WFE ~$135B CY26.
- Key risks (WAVE-S-LRCX): cycle-timing/multiple compression 25% of another
  >=15% down-leg in 63d horizon; export-control step-up 25% within two
  quarters (new BIS SME rule); memory capex digestion / order air-pocket 20%
  (named-IDM cuts >10% or WFE <$120B CY26). SK Hynix $410B commitment cited
  as the demand engine on file.

### 13.9 KLAC -- KLA Corporation (Tier 1 equipment)
Sources: FIN[KLAC]=wiki/investing/filings/KLAC/KLAC-xbrl.json | TECH 1255 obs
| ENT[KLAC] | WAVE=waveS-klac-analysis.md (HOLD, conf 50).

Quarterly revenue, last 12 reported (11 points; Q4d derived):
| # | Fiscal period | Revenue $B | YoY | NI $B | NI margin |
|---|---|---|---|---|---|
| 1 | 2023-09-30 | 2.40 | n/a | 0.74 | 30.9% |
| 2 | 2023-12-31 | 2.49 | n/a | 0.58 | 23.4% |
| 3 | 2024-03-31 | 2.36 | n/a | 0.60 | 25.5% |
| 4 | 2024-06-30 (Q4d) | 2.57 | n/a | n/a | n/a |
| 5 | 2024-09-30 | 2.84 | +18.5% | 0.95 | 33.3% |
| 6 | 2024-12-31 | 3.08 | +23.7% | 0.82 | 26.8% |
| 7 | 2025-03-31 | 3.06 | +29.8% | 1.09 | 35.5% |
| 8 | 2025-06-30 (Q4d) | 3.17 | +23.6% | n/a | n/a |
| 9 | 2025-09-30 | 3.21 | +13.0% | 1.12 | 34.9% |
| 10 | 2025-12-31 | 3.30 | +7.2% | 1.15 | 34.7% |
| 11 | 2026-03-31 | 3.42 | +11.5% | 1.20 | 35.2% |
| 12 | 2026-06-30 (Q4d) | 3.66 | +15.2% | n/a | n/a |

- Net-margin trajectory: the tier's most profitable franchise -- 30-36%
  quarterly net margins throughout, LQ (Q4d) n/a; TTM 35.6% (FIN), highest
  NI margin among the five equipment names.
- R&D: $1.47B TTM computed = 10.8% of revenue (FIN-S5 doc prints 11.3%/1.5B,
  window ending 2026-06-30). Capex FY24 $0.28B; Cash/LTD 0.3x ($1.6B/$5.9B,
  FIN-S6) -- leveraged but cash-generative.
- Technical state (TECH): 5y ann return 42.2% | vol 46.4% | Sharpe 0.76 |
  maxDD -43.6%. Beta(252d) 2.84, corr vs SPY 0.61. Price 8/21 $183.99:
  -16.3% vs MA50 (deepest MA50 breach in the equipment tier), +9.4% vs MA200,
  RSI14 51. Drawdowns >=20%:

  - 2022-01-14 @42.5 -> 2022-10-17 @25.38 = -40.3%; recovered 2023-05-26
  - 2024-07-10 @87.75 -> 2025-04-04 @57.08 = -34.9%; recovered 2025-06-16
  - 2026-01-29 @167.85 -> 2026-02-04 @130.24 = -22.4%; recovered 2026-04-09
  - 2026-06-30 @301.37 -> 2026-07-29 @170.0 = -43.6%; **STILL OPEN**
- Supply-chain role and dependencies: process control / metrology monopoly-
  adjacent -- intensity rises with every node transition and with hybrid-
  bonding packaging; N2 ramp at TSMC pulls inspection (ENT[KLAC]). Downstream:
  every fab; upstream: photonics/e-beam components.
- Key risks (WAVE-S-KLAC): WFE 2027 digestion / capex air-pocket 40%;
  China export-control escalation 30%; trend/momentum continuation 45%
  (>=10% further leg). The 2026-07 drawdown (-43.6% top-to-trough, still open
  at the file's data cutoff) already prices a partial digestion scenario.
### 13.10 SNPS -- Synopsys (Tier 0 EDA)
Sources: FIN[SNPS]=wiki/investing/filings/SNPS/SNPS-xbrl.json | TECH 1255 obs
| ENT[SNPS] | WAVE=waveS-snps-analysis.md (HOLD, conf 55).

Quarterly revenue, last 12 reported (11 points; Q4d derived; one stale FY2018
row dropped by window filter):
| # | Fiscal period | Revenue $B | YoY | NI $B | NI margin |
|---|---|---|---|---|---|
| 1 | 2023-07-31 | 1.35 | n/a | 0.34 | 24.8% |
| 2 | 2024-01-31 | 1.51 | n/a | 0.45 | 29.7% |
| 3 | 2024-04-30 | 1.45 | n/a | 0.29 | 20.1% |
| 4 | 2024-07-31 | 1.53 | +12.7% | 0.41 | 26.7% |
| 5 | 2024-10-31 (Q4d) | 1.64 | n/a | n/a | n/a |
| 6 | 2025-01-31 | 1.46 | +-3.7% | 0.30 | 20.3% |
| 7 | 2025-04-30 | 1.60 | +10.3% | 0.35 | 21.5% |
| 8 | 2025-07-31 | 1.74 | +14.0% | 0.24 | 13.9% |
| 9 | 2025-10-31 (Q4d) | 2.25 | +37.8% | n/a | n/a |
| 10 | 2026-01-31 | 2.41 | +65.5% | 0.06 | 2.7% |
| 11 | 2026-04-30 | 2.28 | +41.9% | 0.02 | 0.8% |

- Net-margin trajectory: structurally ~20-30% pre-Ansys; the collapse to
  13.9% -> 2.7% -> 0.8% across the last three reported quarters is the
  acquisition-accounting distortion documented in the existing file (NI $17M
  LQ, -95% YoY) -- a deal-amortization artifact, not an operating collapse.
- R&D: $2.59B TTM computed = 29.9% of revenue (FIN-S5 doc prints 32.1%/2.8B,
  window ending 2026-04-30) -- highest R&D intensity in this file. Cash/LTD
  0.2x ($2.4B/$10.0B post-Ansys debt, FIN-S6).
- Technical state (TECH): 5y ann return just 3.7% -- worst in the set despite
  the AI boom | vol 42.7% | Sharpe 0.09 | maxDD -42.3%. Beta(252d) 1.65
  (lowest of the 20), corr vs SPY 0.34. Price 8/21 $397.87: -5.3% vs MA50,
  -10.8% vs MA200 (only names below MA200: SNPS, CDNS, GFS), RSI14 54.
  Drawdowns >=20%:

  - 2021-12-27 @375.59 -> 2022-05-11 @260.83 = -30.6%; recovered 2022-08-10
  - 2022-08-15 @390.45 -> 2022-10-12 @276.19 = -29.3%; recovered 2023-05-18
  - 2024-07-05 @621.3 -> 2025-04-07 @380.9 = -38.7%; recovered 2025-07-29
  - 2025-07-30 @645.35 -> 2026-07-30 @372.33 = -42.3%; **STILL OPEN**
- Supply-chain role and dependencies: EDA #1 (~31-46% share by methodology).
  Upstream of EVERY tape-out at TSM/GFS and every design at NVDA/AMD/AVGO/
  MRVL/QCOM -- nothing ships without its toolchains. Ansys acquisition closed
  2024 adds simulation multiphysics upstream of signoff.
- Key risks (WAVE-S-SNPS): trend continuation / further multiple compression
  ~40%; design-start deceleration reaching EDA bookings ~20-25%; stale-data
  mispricing risk ~15% (vault-specific). Export controls on China tool sales
  are the policy tail carried tier-wide.

### 13.11 CDNS -- Cadence Design Systems (Tier 0 EDA)
Sources: NO xbrl json in corpus (FIN = n/a by construction). TECH bars 1255
obs 2021-08-24..2026-08-24. ENT[CDNS]=wiki/entities/tickers/CDNS.md (sparse:
~35-36% EDA share, FY24 revenue $4.6413B +13% YoY per matrixbcq claim).
No wave-analysis file exists for CDNS -- no latest-wave risk block available;
risks below are DERIVED from entity note + tier-level statements.

Quarterly revenue table: NOT COMPUTABLE from corpus (no xbrl json). The only
revenue anchors on file: FY24 $4.64B +13% YoY (ENT[CDNS]); FY25 guide ~$5.23B
(existing file Section 2); 100% retention, 80-85% recurring revenue.

- Net margin / R&D % / capex: not computable from corpus for this ticker.
- Technical state (TECH): 5y ann return 14.7% | vol 36.6% | Sharpe 0.37 |
  maxDD -29.6% (shallowest maxDD of the 20 -- the defensive profile of the
  file). Beta(252d) 1.62, corr vs SPY 0.52. Price 8/21 $319.02: -9.8% vs
  MA50, -2.5% vs MA200, RSI14 31 (most oversold name in the set).
  Drawdowns >=20%:

  - 2021-12-27 @191.65 -> 2022-02-18 @134.95 = -29.6%; recovered 2022-08-15
  - 2022-08-15 @193.09 -> 2022-11-04 @142.41 = -26.2%; recovered 2023-02-14
  - 2024-06-18 @326.5 -> 2025-04-08 @231.64 = -29.0%; recovered 2025-07-03
  - 2025-09-22 @373.37 -> 2026-04-10 @265.66 = -28.8%; recovered 2026-05-22
  - 2026-06-02 @416.39 -> 2026-08-20 @313.59 = -24.7%; **STILL OPEN**
- Supply-chain role and dependencies: EDA #2 (~35-36% share); with SNPS forms
  the duopoly gatekeeping every tape-out (combined ~70%+ share, MEDIUM/DERIVED).
- Key risks (DERIVED, no wave file): same tier-level exposures as SNPS --
  design-cycle deceleration, China tool-sale export controls; plus
  idiosyncratic: RSI 31 + below both MAs = momentum broken even as
  fundamentals (retention, recurring mix) stay intact per entity claims.
### 13.12 ARM -- Arm Holdings (Tier 0 IP)
Sources: NO xbrl json in corpus (FIN = n/a). TECH bars 738 obs only
2023-09-14..2026-08-24 (IPO 2023) -- 5y stats below run on the available
window (~2.9y), NOT a full 5y; flagged per-row. ENT[ARM] |
WAVE=waveS-arm-analysis.md (HOLD, conf 58).

Quarterly revenue: n/a from XBRL. FY2025 20-F filed (SEC archive per ENT[ARM]);
no scraped revenue points. Royalty-model anchors: CPU IP for hyperscaler Arm
CPUs (Graviton/Cobalt/Axion); royalty leverage to every hyperscaler custom CPU.

- Net margin / R&D %: not computable from corpus.
- Technical state (TECH, ~2.9y window -- treat CAGR as since-IPO):
  ann return 57.0% since IPO | vol 74.5% (highest realized vol of any name
  here except SNDK) | Sharpe 0.61 | maxDD -54.0%. Beta(252d) 3.27, corr vs
  SPY 0.56. Price 8/21 $243.32: -19.5% vs MA50 (deepest MA50 breach in the
  file), +23.4% vs MA200, RSI14 52. Drawdowns >=20%:

  - 2024-02-12 @148.97 -> 2024-04-19 @87.19 = -41.5%; recovered 2024-06-12
  - 2024-07-10 @186.46 -> 2025-04-08 @85.82 = -54.0%; recovered 2026-04-22
  - 2026-06-03 @411.83 -> 2026-06-10 @307.43 = -25.4%; recovered 2026-06-15
  - 2026-06-18 @439.46 -> 2026-07-29 @224.89 = -48.8%; **STILL OPEN**
- Supply-chain role and dependencies: instruction-set gravity for hyperscaler
  CPUs. Upstream of TSM/GFS tape-outs that implement Arm cores; competes with
  x86 (INTC/AMD) and RISC-V at the workload level but not at fleet scale.
  Downstream: AWS Graviton, Azure Cobalt, GCP Axion fleets; AVGO/MRVL build
  its cores into custom XPUs.
- Key risks (WAVE-S-ARM): multiple compression / rate-regime persistence 60%;
  China / Arm-China concentration plus SoftBank supply overhang 40%; ISA
  displacement / royalty-rate dispute creep 30%. The 6/18->7/29 drawdown of
  -48.8% is still open at data cutoff.

### 13.13 MRVL -- Marvell Technology (Tier 5 networking)
Sources: FIN[MRVL]=wiki/investing/filings/MRVL/MRVL-xbrl.json | TECH 1255 obs
| ENT[MRVL] | WAVE=waveN-mrvl-analysis.md (HOLD, conf 65).

Quarterly revenue, last 12 reported (11 points; Q4d derived):
| # | Fiscal period | Revenue $B | YoY | NI $B | NI margin |
|---|---|---|---|---|---|
| 1 | 2023-07-29 | 1.34 | n/a | -0.21 | -15.5% |
| 2 | 2023-10-28 | 1.42 | n/a | -0.16 | -11.6% |
| 3 | 2024-05-04 | 1.16 | n/a | -0.22 | -18.6% |
| 4 | 2024-08-03 | 1.27 | +-5.1% | -0.19 | -15.2% |
| 5 | 2024-11-02 | 1.52 | +6.9% | -0.68 | -44.6% |
| 6 | 2025-02-01 (Q4d) | 1.82 | n/a | n/a | n/a |
| 7 | 2025-05-03 | 1.90 | +63.3% | 0.18 | 9.4% |
| 8 | 2025-08-02 | 2.01 | +57.6% | 0.19 | 9.7% |
| 9 | 2025-11-01 | 2.07 | +36.8% | 1.90 | 91.7% |
| 10 | 2026-01-31 (Q4d) | 2.22 | +22.1% | n/a | n/a |
| 11 | 2026-05-02 | 2.42 | +27.6% | 0.03 | 1.4% |

- Net-margin trajectory: negative through FY24-FY25 (-15% to -45%), swung
  positive mid-2025 (+9.4%), then two distorted prints: 91.7% on 2025-11-01
  ($1.90B NI on $2.07B rev = one-time tax/deferred item, aggregator SUSPECT
  class) and 1.4% LQ. Use entity-note operating metrics instead: FY26 GM
  51.0%, OM 16.1% (HIGH).
- R&D: $2.19B TTM computed = 25.1% of revenue (FIN-S5 doc prints 25.5%/2.2B,
  window ending 2026-05-02). Capex just 4.3% of revenue FY-end 2026-01-31
  (FIN-S4); Cash/LTD 0.8x (FIN-S6). TTM FCF $1.85B = 0.73% yield,
  EV/Sales ~22x fwd (mrvl-analysis-2026-06-18).
- Technical state (TECH): 5y ann return 30.1% | vol 63.8% | Sharpe 0.41 |
  maxDD -61.9%. Beta(252d) 3.07, corr vs SPY 0.50. Price 8/21 $237.04:
  +1.4% vs MA50, +63.5% vs MA200, RSI14 65. Drawdowns >=20%:

  - 2021-12-07 @89.91 -> 2023-01-05 @34.27 = -61.9%; recovered 2024-11-06
  - 2025-01-23 @125.55 -> 2025-04-04 @49.23 = -60.8%; recovered 2026-04-10
  - 2026-06-04 @316.35 -> 2026-07-29 @163.4 = -48.4%; **STILL OPEN**
- Supply-chain role and dependencies: #2 custom-silicon house -- Amazon
  Trainium anchor program (Project Rainier live Oct 29 2025 with ~500K
  Trainium2 chips scaling >1M by year-end; Trainium3 first 3nm AI accelerator
  shipping); optical DSP ladder 400G->800G->1.6T second engine. Upstream: TSM
  3nm/CoWoS, MU/SKH HBM. Downstream: AMZN capex directly; hyperscaler fabrics.
- Key risks (WAVE-N-MRVL): FM-A negative Aug-27 binary / socket-erosion
  confirmation 45%/HIGH (channel checks say Trainium3/4 share at risk); the
  +45% rally INTO the print makes a miss asymmetric; FM-B multiple compression
  / rates 50%/HIGH (fwd non-GAAP P/E ~42-59x band cited).
### 13.14 ANET -- Arista Networks (Tier 5 networking systems)
Sources: FIN[ANET]=wiki/investing/filings/ANET/ANET-xbrl.json | TECH 1255 obs
| ENT[ANET] | WAVE=waveN-anet-analysis.md (HOLD, conf 62).

Quarterly revenue, last 12 reported (11 points; Q4d derived):
| # | Fiscal period | Revenue $B | YoY | NI $B | NI margin |
|---|---|---|---|---|---|
| 1 | 2023-09-30 | 1.51 | n/a | 0.55 | 36.1% |
| 2 | 2024-03-31 | 1.57 | n/a | 0.64 | 40.6% |
| 3 | 2024-06-30 | 1.69 | n/a | 0.67 | 39.4% |
| 4 | 2024-09-30 | 1.81 | +20.0% | 0.75 | 41.3% |
| 5 | 2024-12-31 (Q4d) | 1.93 | n/a | n/a | n/a |
| 6 | 2025-03-31 | 2.00 | +27.6% | 0.81 | 40.6% |
| 7 | 2025-06-30 | 2.20 | +30.4% | 0.89 | 40.3% |
| 8 | 2025-09-30 | 2.31 | +27.5% | 0.85 | 37.0% |
| 9 | 2025-12-31 (Q4d) | 2.49 | +28.9% | n/a | n/a |
| 10 | 2026-03-31 | 2.71 | +35.1% | 1.02 | 37.8% |
| 11 | 2026-06-30 | 3.04 | +37.7% | 1.21 | 40.0% |

- Net-margin trajectory: the steadiest compounder in the file -- 36-41%
  quarterly net margins in every reported quarter, no acquisition noise,
  LQ (Q4d) n/a. TTM 37.7%.
- R&D: $1.31B TTM computed = 12.5% of revenue (FIN-S5 doc prints 13.0%/1.4B
  on window ending 2026-06-30). No LongTermDebt points in corpus (FIN-S6
  unranked list); capex de minimis (~$0.05B latest FY row).
- Technical state (TECH): 5y ann return 52.1% | vol 48.6% | Sharpe 0.86 |
  maxDD -50.4%. Beta(252d) 2.05, corr vs SPY 0.48 (lowest beta*corr product
  among growth names -- partial diversifier within the complex). Price 8/21
  $188.65: +6.4% vs MA50 (one of few above), +26.6% vs MA200, RSI14 52.
  Drawdowns >=20%:

  - 2023-03-23 @42.35 -> 2023-05-03 @33.18 = -21.6%; recovered 2023-05-26
  - 2025-01-22 @129.82 -> 2025-04-04 @64.37 = -50.4%; recovered 2025-08-06
  - 2025-10-29 @162.03 -> 2026-03-30 @116.13 = -28.3%; recovered 2026-04-17
  - 2026-04-22 @177.73 -> 2026-05-11 @136.43 = -23.2%; recovered 2026-07-08
- Supply-chain role and dependencies: merchant Ethernet switching SYSTEMS on
  merchant silicon (AVGO Tomahawk/Jericho inside; own FEOS stack). Ethernet
  taking share from InfiniBand in hyperscaler backends; AI networking revenue
  $1.5B (2025) -> $3.25B guided (2026) = 2.17x (HIGH). Upstream: AVGO/MRVL
  silicon, optics from COHR/LITE ecosystem. Downstream: MSFT/META fleets --
  cloud-titan concentration is THE structural exposure.
- Key risks (WAVE-N-ANET): cloud-titan customer concentration 55%/MEDIUM-HIGH
  structural; high-multiple de-rate in high-beta complex 45%/HIGH (~38x fwd
  April basis); memory-driven cost-inflation margin squeeze / guidance risk
  30%/MEDIUM (flagged inside its own 2026 guide).

### 13.15 COHR -- Coherent Corp (Tier 6 optical)
Sources: FIN[COHR]=wiki/investing/filings/COHR/COHR-xbrl.json | TECH 1255 obs
| ENT[COHR] | WAVE=waveN-cohr-analysis.md (HOLD, conf 50).

Quarterly revenue, last 12 reported (11 points; Q4d derived):
| # | Fiscal period | Revenue $B | YoY | NI $B | NI margin |
|---|---|---|---|---|---|
| 1 | 2023-09-30 | 1.05 | n/a | -0.07 | -6.4% |
| 2 | 2023-12-31 | 1.13 | n/a | -0.03 | -2.4% |
| 3 | 2024-03-31 | 1.21 | n/a | -0.01 | -1.1% |
| 4 | 2024-06-30 (Q4d) | 1.31 | n/a | n/a | n/a |
| 5 | 2024-09-30 | 1.35 | +28.0% | 0.03 | 1.9% |
| 6 | 2024-12-31 | 1.43 | +26.8% | 0.10 | 7.2% |
| 7 | 2025-03-31 | 1.50 | +23.9% | 0.02 | 1.0% |
| 8 | 2025-06-30 (Q4d) | 1.53 | +16.4% | n/a | n/a |
| 9 | 2025-09-30 | 1.58 | +17.3% | 0.23 | 14.3% |
| 10 | 2025-12-31 | 1.69 | +17.5% | 0.15 | 8.7% |
| 11 | 2026-03-31 | 1.81 | +20.5% | 0.19 | 10.6% |
| 12 | 2026-06-30 (Q4d) | 2.05 | +33.7% | n/a | n/a |

- Net-margin trajectory: negative through FY24 (-6% to -1%), inflected 2024-09
  (+1.9%), now 8-14% band -- an operating-leverage story mid-climb. LQ (Q4d)
  n/a; TTM 11.3%.
- R&D: $723M TTM = 10.2% of revenue (FIN-S5, window ending 2026-06-30).
  Capex stepped up hard: FY25 $0.44B -> FY26 $1.10B (latest 10-K period
  2026-06-30) = ~19% of LQ annualized revenue -- capacity race with Innolight.
  Cash/LTD 0.4x ($1.2B/$3.2B, FIN-S6) -- most levered balance sheet in the
  optical tier.
- Technical state (TECH): 5y ann return 34.6% | vol 65.5% | Sharpe 0.45 |
  maxDD -62.9%. Beta(252d) 3.39 (highest of the 20), corr vs SPY 0.52.
  Price 8/21 $289.52: -12.2% vs MA50, +7.3% vs MA200, RSI14 50.
  Drawdowns >=20%:

  - 2024-12-04 @112.02 -> 2025-04-04 @50.58 = -54.9%; recovered 2025-08-07
  - 2025-08-12 @116.56 -> 2025-08-20 @86.55 = -25.8%; recovered 2025-10-08
  - 2026-03-02 @298.91 -> 2026-03-30 @219.65 = -26.5%; recovered 2026-04-10
  - 2026-06-02 @426.89 -> 2026-07-29 @222.05 = -48.0%; **STILL OPEN**
- Supply-chain role and dependencies: transceivers ~25% share (#2) + NVIDIA's
  named silicon-photonics collaborator for Spectrum-X; NVIDIA 800G procurement
  ~20% wallet share. Upstream: LITE EML lasers INSIDE its modules (and its own
  InP capacity), MKSI lasers adjacency. Downstream: NVDA/hyperscaler fabrics;
  top-5 suppliers ~50% of 2025 transceiver revenue industry-wide.
- Key risks (WAVE-N-COHR): volatility/structure risk 55% (another >=15%
  down-leg; beta 2.75-3.6 at 137%-of-SMA200 peak); format-transition/share
  risk at the 1.6T handoff 35% (Innolight share loss); concentration +
  FCF-condition failure 30% (negative-FCF print would fail its own gate).
### 13.16 LITE -- Lumentum Holdings (Tier 6 optical)
Sources: FIN[LITE]=wiki/investing/filings/LITE/LITE-xbrl.json (June FY --
latest XBRL row lags peers by ~2 quarters, 2025Q2 label) | TECH 1255 obs |
ENT[LITE] | no wave file -- risks from ENT + existing file Section 8.

Quarterly revenue, last 12 reported (11 points; Q4d derived; note the FY-June
calendar makes these the OLDEST prints of the 20):
| # | Fiscal period | Revenue $B | YoY | NI $B | NI margin |
|---|---|---|---|---|---|
| 1 | 2022-10-01 | 0.51 | n/a | n/a | n/a |
| 2 | 2022-12-31 | 0.51 | n/a | n/a | n/a |
| 3 | 2023-04-01 | 0.38 | n/a | n/a | n/a |
| 4 | 2023-07-01 (Q4d) | 0.37 | n/a | n/a | n/a |
| 5 | 2023-09-30 | 0.32 | +-37.3% | -0.07 | -21.4% |
| 6 | 2023-12-30 | 0.37 | +-27.5% | -0.10 | -27.0% |
| 7 | 2024-03-30 | 0.37 | +-4.4% | -0.13 | -34.7% |
| 8 | 2024-09-28 | 0.34 | +6.1% | -0.08 | -24.5% |
| 9 | 2024-12-28 | 0.40 | +9.7% | -0.06 | -15.1% |
| 10 | 2025-03-29 | 0.43 | +16.0% | -0.04 | -10.4% |
| 11 | 2025-06-28 (Q4d) | 0.48 | n/a | n/a | n/a |

- Net-margin trajectory: deeply negative through FY24 (-21% to -35%), still
  negative but narrowing (-10.4% by 2025-03-29). The fresher entity-note
  figures (Q2-FY26 components $444M +68%, systems $222M +60%; Q2-FY26 guide
  $630-670M vs the $481M XBRL LQ) imply an inflection NOT yet visible in the
  scraped rows -- a two-quarter staleness wedge to respect.
- R&D: $325M TTM computed on stale window = 19.9% of revenue (FIN-S5 class);
  treat as directional only given calendar lag.
- Technical state (TECH): 5y ann return 57.2% | vol 63.3% | Sharpe 0.71 |
  maxDD -66.5% (deepest maxDD of the 20). Beta(252d) 3.00, corr vs SPY 0.40
  (low market coupling -- trades on its own EML cycle). Price 8/21 $866.71:
  +6.4% vs MA50, +32.8% vs MA200, RSI14 56. Drawdowns >=20%:

  - 2022-01-11 @107.61 -> 2023-10-27 @36.07 = -66.5%; recovered 2025-07-29
  - 2026-03-02 @783.25 -> 2026-03-06 @558.44 = -28.7%; recovered 2026-03-24
  - 2026-05-11 @1053.09 -> 2026-07-29 @602.35 = -42.8%; **STILL OPEN**
- Supply-chain role and dependencies: THE chokepoint supplier of the optical
  tier -- 50-60% global EML share; 200G/lane EML demand exceeds supply by
  25-30%; every 800G->1.6T transceiver lane needs its lasers. Upstream: InP
  wafer capacity. Downstream: COHR modules, Innolight/Accelink assemblies,
  ultimately every NVDA rack fabric.
- Key risks (ENT + existing file): extreme realized volatility (vol21 119.8%);
  Innolight vertical integration compressing module assembly share upstream
  of it; fiscal-calendar staleness means the market sees fresher numbers than
  this corpus does; single-product-family concentration (EML).

### 13.17 SNDK -- Sandisk (Tier 3 memory/NAND)
Sources: FIN[SNDK]=wiki/investing/filings/SNDK/SNDK-xbrl.json | TECH bars only
383 obs 2025-02-13..2026-08-24 (post-spin listing) -- "5y" stats below run on
~1.5y and are flagged per-row. ENT[SNDK] | WAVE=wave1-sndk-analysis.md
(SELL, conf 60 -- the only SELL rating in the set).

Quarterly revenue, last 12 reported (9 points exist post-spin; Q4d derived;
pre-spin quarters are carve-out artifacts):
| # | Fiscal period | Revenue $B | YoY | NI $B | NI margin |
|---|---|---|---|---|---|
| 1 | 2024-03-29 | 1.71 | n/a | 0.03 | 1.6% |
| 2 | 2024-09-27 | 1.88 | n/a | 0.21 | 11.2% |
| 3 | 2024-12-27 | 1.88 | n/a | 0.10 | 5.5% |
| 4 | 2025-03-28 | 1.70 | +-0.6% | -1.93 | -114.0% |
| 5 | 2025-06-27 (Q4d) | 1.90 | n/a | n/a | n/a |
| 6 | 2025-10-03 | 2.31 | +22.6% | 0.11 | 4.9% |
| 7 | 2026-01-02 | 3.02 | +61.2% | 0.80 | 26.5% |
| 8 | 2026-04-03 | 5.95 | +251.0% | 3.62 | 60.8% |
| 9 | 2026-07-03 (Q4d) | 8.96 | +371.6% | n/a | n/a |

- Net-margin trajectory: ~0-11% through 2024 -> -114.0% print on 2025-03-28
  (one-time charge quarter) -> 4.9% -> 26.5% -> 60.8% LQ -- the NAND price
  cycle at full torque. Margins >55% carry aggregator SUSPECT flags (FIN S7);
  wave file frames NBM contract floors near 80% GM with blended GM
  compressing toward 80 as NBM grows (~half FY27 bits).
- R&D: $1.26B TTM = 6.2% of revenue (FIN-S5, window ending 2026-07-03).
  Capex/revenue just 0.9% FY-end 2026-07-03 (FIN-S4) -- fab capex sits at
  Kioxia JV partner; Kioxia/SNDK capex +41% per wave FM1. No LTD points.
- Technical state (TECH, since-IPO-only window): ann return +1062.9%/yr
  (+4023% cumulative since 2025-02-13 -- the most violent re-rating in the
  file) | vol 105.9% | Sharpe 2.32 | maxDD -56.5%. Beta(252d) 4.35 (highest
  of the 20), corr vs SPY 0.48. Price 8/21 $1596.08: -3.5% vs MA50, +69.9%
  vs MA200, RSI14 63. Drawdowns >=20%:

  - 2025-11-12 @283.1 -> 2025-12-03 @194.38 = -31.3%; recovered 2026-01-06
  - 2026-02-03 @695.51 -> 2026-03-06 @527.33 = -24.2%; recovered 2026-03-16
  - 2026-03-19 @772.09 -> 2026-03-30 @572.5 = -25.9%; recovered 2026-04-08
  - 2026-06-25 @2335.0 -> 2026-07-29 @1015.89 = -56.5%; **STILL OPEN**
- Supply-chain role and dependencies: NAND pure-play post-WDC spin. Upstream:
  Kioxia JV fabs (Japan; Apr 22 2026 earthquake tightened supply), BiCS10 QLC
  adds bits with zero new wafer starts. Downstream: enterprise SSD became the
  largest NAND segment for the first time in 2026 (datacenter +233% QoQ /
  +645% YoY Q3-FY26); CSP long-term agreements; NVDA ICMS KV-cache offload
  could consume >10% of total NAND supply (ref-memory ingest claim).
- Key risks (WAVE1-SNDK UPDATED ASSESSMENT -- nothing resolved since 8/17):
  FM5 margin ceiling as NBM grows; FM2 informed-flow split (Tepper exited
  SNDK 100% while keeping MU); insider silence (zero open-market buys across
  400d); FM1 TrendForce supply>demand through 2027 with rebalance 2H27; kill
  criterion #4 LIVE: consumer -32% seq in FQ4 is leg one of a two-leg
  sequential-decline trigger the 11/06 print can fire. Rating SELL conf 60.
### 13.18 WDC -- Western Digital (Tier 3 storage/HDD)
Sources: FIN[WDC]=wiki/investing/filings/WDC/WDC-xbrl.json (no R&D points
scraped, FIN S7) | TECH 1255 obs | ENT[WDC] | no wave file -- risks from
ENT + ref-memory-storage-cycle-deep-dive claims carried in it.

Quarterly revenue, last 12 reported (7 points post-spin; Q4d derived; the
-4.3B artifact quarter from FIN S2 is EXCLUDED here as documented noise):
| # | Fiscal period | Revenue $B | YoY | NI $B | NI margin |
|---|---|---|---|---|---|
| 1 | 2024-09-27 | 2.21 | n/a | 0.49 | 22.3% |
| 2 | 2024-12-27 | 2.41 | n/a | 0.59 | 24.7% |
| 3 | 2025-03-28 | 2.29 | n/a | 0.52 | 22.7% |
| 4 | 2025-10-03 | 2.82 | +27.4% | 1.18 | 41.9% |
| 5 | 2026-01-02 | 3.02 | +25.2% | 1.84 | 61.1% |
| 6 | 2026-04-03 | 3.34 | +45.5% | 3.21 | 96.0% |
| 7 | 2026-07-03 (Q4d) | 3.75 | n/a | n/a | n/a |

- Net-margin trajectory: 22-25% pre-breakout -> 41.9% -> 61.1% -> 96.0% LQ.
  The 96.0% LQ print carries the aggregator SUSPECT flag hard (FIN S7 lists
  WDC netmargin_latest=0.853 and rev_yoy_extreme=-1.87 on the derived Q4) --
  likely a YTD-row mislabel; verify against the 10-K before use. Direction is
  real (HDD pricing power, sold-out 2026), magnitude unverified.
- R&D: n/a in corpus (zero R&D points scraped for WDC, FIN S7). Capex/revenue
  3.2% FY-end 2026-07-03 ($418M/$12.9B FY pair, FIN-S4). Cash/LTD 1.5x.
- Technical state (TECH): 5y ann return 57.1% | vol 52.7% | Sharpe 0.86 |
  maxDD -55.3%. Beta(252d) 3.10, corr vs SPY 0.50. Price 8/21 $459.44:
  -16.2% vs MA50, +28.3% vs MA200, RSI14 40. Drawdowns >=20%:

  - 2024-07-10 @60.37 -> 2025-04-04 @30.4 = -49.6%; recovered 2025-06-24
  - 2025-11-10 @173.95 -> 2025-11-21 @138.98 = -20.1%; recovered 2025-12-10
  - 2026-03-19 @316.85 -> 2026-03-30 @251.6 = -20.6%; recovered 2026-04-08
  - 2026-06-18 @746.23 -> 2026-08-24 @432.87 = -42.0%; **STILL OPEN**
- Supply-chain role and dependencies: post-spin pure-HDD; nearline AI-archive
  demand ("sold out for all of 2026", HIGH, ENT via ref-memory deep dive;
  1y total return was +860% at claim time). Upstream: recording heads/media,
  HAMR/MAMR component ramps unlocking 50TB+ drives. Downstream: hyperscaler
  training/inference archives -- the cold tier under every GPU fleet.
- Key risks (ENT): flash encroachment on HDD long-term (30+TB cold niche
  defensible through 2030, contested after); same memory-cycle-top signature
  as MU/SNDK; margin-print credibility gap until the 10-K reconciles.

### 13.19 ONTO -- Onto Innovation (Tier 1 equipment/packaging)
Sources: FIN[ONTO]=wiki/investing/filings/ONTO/ONTO-xbrl.json | TECH 1255 obs
| ENT[ONTO] (thin note, created 2026-06-08) | no wave file.

Quarterly revenue, last 12 reported (11 points; Q4d derived):
| # | Fiscal period | Revenue $B | YoY | NI $B | NI margin |
|---|---|---|---|---|---|
| 1 | 2023-09-30 | 0.21 | n/a | 0.04 | 17.3% |
| 2 | 2024-03-30 | 0.23 | n/a | 0.05 | 20.5% |
| 3 | 2024-06-29 | 0.24 | n/a | 0.05 | 21.9% |
| 4 | 2024-09-28 | 0.25 | +21.7% | 0.05 | 21.0% |
| 5 | 2024-12-28 (Q4d) | 0.26 | n/a | n/a | n/a |
| 6 | 2025-03-29 | 0.27 | +16.5% | 0.06 | 24.0% |
| 7 | 2025-06-28 | 0.25 | +4.7% | 0.03 | 13.4% |
| 8 | 2025-09-27 | 0.22 | +-13.5% | 0.03 | 12.9% |
| 9 | 2026-01-03 (Q4d) | 0.27 | +1.1% | n/a | n/a |
| 10 | 2026-03-31 | 0.29 | +9.5% | 0.03 | 11.6% |
| 11 | 2026-06-30 | 0.34 | +35.3% | 0.06 | 17.5% |

- Net-margin trajectory: 13-24% band throughout; dipped to 11.6-12.9% in the
  2025H2 CoWoS digestion quarters, recovering to 17.5% LQ. TTM 13.9%.
- R&D: $141M TTM computed = 12.7% of revenue (small-cap scale). Capex points
  exist but stale-debt exclusion applies to balance-sheet ranking (FIN-S6);
  latest capex row ~$0.03B/yr class -- asset-light instruments maker.
  Forensics per ENT: Piotroski 7/9, Altman Z 43.97, Beneish clean.
- Technical state (TECH): 5y ann return 32.0% | vol 59.3% | Sharpe 0.47 |
  maxDD -62.8%. Beta(252d) 3.15, corr vs SPY 0.58. Price 8/21 $293.33:
  -3.7% vs MA50, +25.3% vs MA200, RSI14 56. Drawdowns >=20%:

  - 2022-01-14 @105.96 -> 2022-10-14 @59.04 = -44.3%; recovered 2023-05-26
  - 2023-10-12 @143.04 -> 2023-10-25 @111.16 = -22.3%; recovered 2023-12-11
  - 2024-07-16 @238.04 -> 2025-05-09 @88.5 = -62.8%; recovered 2026-04-08
  - 2026-06-30 @378.45 -> 2026-07-29 @218.31 = -42.3%; **STILL OPEN**
- Supply-chain role and dependencies: pure-play advanced-packaging metrology/
  inspection (Dragonfly) -- the inspection toll on every HBM/CoWoS package;
  benefits directly from CoWoS scaling toward ~170K wpm by 2027 (ENT). The
  smallest-revenue, highest-purity instrument read on packaging intensity.
- Key risks (DERIVED from entity note + existing file Section 3): smallest
  revenue base of the equipment names -> highest operating leverage both ways
  (vol21 113.3%, highest of tier); WFE second-derivative exposure -- corrects
  before foundry/memory P&L does; single-product-family concentration in
  packaging inspection if CoWoS allocation rotates or HBM4 shifts to
  hybrid-bond alternatives its tools do not cover.

### 13.20 GFS -- GlobalFoundries (Tier 2 foundry, trailing edge)
Sources: NO xbrl json in corpus (FIN = n/a). TECH bars 1209 obs starting
2021-10-28 (~4.9y window -- flagged per-row). ENT[GFS] (thin note). No wave
file -- risks DERIVED from entity note + technical state.

Quarterly revenue: n/a from XBRL corpus. Role anchors only: trailing-edge /
specialty foundry -- power-management ICs and silicon photonics (via Tower
Semiconductor acquisition); NOT in the leading-edge AI compute path but
adjacent-critical to power delivery and optical transceivers.

- Net margin / R&D % / capex: not computable from corpus.
- Technical state (TECH, ~4.9y): ann return ~0.0%/yr -- a lost half-decade |
  vol 51.7% | Sharpe -0.00 (worst risk-adjusted outcome of the 20) |
  maxDD -61.5%. Beta(252d) 2.20, corr vs SPY 0.48. Price 8/21 $48.05:
  -24.2% vs MA50 (deepest in file), -8.8% vs MA200, RSI14 46.
  Drawdowns >=20%:

  - 2021-11-29 @70.44 -> 2022-01-27 @44.65 = -36.6%; recovered 2022-03-17
  - 2022-03-25 @78.83 -> 2025-04-08 @30.33 = -61.5%; recovered 2026-05-21
  - 2026-05-26 @89.83 -> 2026-08-24 @46.25 = -48.5%; **STILL OPEN**
- Supply-chain role and dependencies: specialty-node foundry OUTSIDE the AI
  accelerator path. Upstream: none of the chokepoint inputs (no EUV).
  Downstream: power-management ICs feeding GPU rack power delivery; silicon
  photonics wafers supporting the 800G/1.6T optics transition; auto/
  industrial cyclicals. Its value-chain relevance is supportive, not core --
  the file's clearest contrast case against TSM.
- Key risks (DERIVED): weakest technical state in this file (63d -40.8%,
  off-high -46.5% per existing file; still-open -48.5% drawdown from
  2026-05-26 top); cyclical auto/industrial demand without an AI torque
  offset; customer concentration in specialty programs; strategic question of
  whether Tower photonics converts to AI-optics revenue at scale.
## 14. Cross-company correlation subsets (90d, factors.db bars)

Method: Pearson correlation of daily log returns over the last 90 common
trading days ending 2026-08-24, computed from factors.db bars (src=yfinance-
5y) in this session; window = max overlap per pair. SPY context row computed
identically. These are DERIVED numbers from store bars -- recompute after any
store refresh. Read with the tier map: within-tier correlations near +0.9 mean
the tier trades as ONE position regardless of name count.

### 14.1 Equipment tier: ASML / AMAT / LRCX / KLAC

| Pair | corr90 | | Pair vs SPY | corr90 |
|---|---|---|---|---|
| ASML-AMAT | +0.808 | | ASML-SPY | +0.630 |
| ASML-LRCX | +0.862 | | AMAT-SPY | +0.593 |
| ASML-KLAC | +0.822 | | LRCX-SPY | +0.663 |
| AMAT-LRCX | +0.920 | | KLAC-SPY | +0.604 |
| AMAT-KLAC | +0.890 | | | |
| LRCX-KLAC | +0.880 | | | |

Reading (DERIVED): six pairwise correlations all >= +0.81; AMAT-LRCX at +0.920
is effectively one instrument. A four-name equipment "basket" carries almost
no diversification -- size it as a single WFE-beta line. KLAC's -16.3% MA50
breach did NOT decouple it from peers (corr held), so its drawdown is
tier-wide de-rating, not idiosyncratic process-control loss.

### 14.2 Memory tier: MU / SNDK / WDC

| Pair | corr90 | | Pair vs SPY | corr90 |
|---|---|---|---|---|
| MU-SNDK | +0.845 | | MU-SPY | +0.546 |
| MU-WDC | +0.719 | | SNDK-SPY | +0.490 |
| SNDK-WDC | +0.740 | | WDC-SPY | +0.498 |

Reading (DERIVED): the DRAM/NAND pair (MU-SNDK) correlates harder than either
pair involving HDD -- the commodity-memory factor dominates. WDC adds modest
diversification (+0.72/+0.74) because nearline-HDD pricing runs on a different
supply discipline than semiconductor bits.

### 14.3 Compute tier: NVDA / AMD / QCOM

| Pair | corr90 | | Pair vs SPY | corr90 |
|---|---|---|---|---|
| NVDA-AMD | +0.460 | | NVDA-SPY | +0.637 |
| NVDA-QCOM | +0.144 | | AMD-SPY | +0.667 |
| AMD-QCOM | +0.582 | | QCOM-SPY | +0.528 |

Reading (DERIVED): the striking result is NVDA-QCOM +0.144 -- the lowest pair
in this whole section. QCOM's mobile-annuity cash flows decouple it from the
accelerator complex; an accelerator-basket hedge using QCOM is hedging
something else entirely. NVDA-AMD +0.46 is far below their shared-supply-chain
logic (both buy TSM CoWoS + HBM) -- the divergence is custom-silicon-vs-
merchant-GPU narrative rotation, not fundamentals independence.

### 14.4 Networking/optical: AVGO / MRVL / ANET / COHR / LITE

| Pair | corr90 | | Pair vs SPY | corr90 |
|---|---|---|---|---|
| AVGO-MRVL | +0.557 | | AVGO-SPY | +0.577 |
| AVGO-ANET | +0.532 | | MRVL-SPY | +0.558 |
| AVGO-COHR | +0.478 | | ANET-SPY | +0.408 |
| AVGO-LITE | +0.401 | | COHR-SPY | +0.523 |
| MRVL-ANET | +0.443 | | LITE-SPY | +0.403 |
| MRVL-COHR | +0.735 | | | |
| MRVL-LITE | +0.629 | | | |
| ANET-COHR | +0.485 | | | |
| ANET-LITE | +0.507 | | | |
| COHR-LITE | +0.856 | | | |

Reading (DERIVED): two clusters inside the tier. (1) The optics axis --
COHR-LITE +0.856, plus MRVL's high coupling to both (+0.735/+0.629) via the
1.6T DSP-and-laser chain -- trades as one optical-systems bet. (2) AVGO sits
looser against everything (+0.40 to +0.56) because VMware software revenue
dilutes its silicon beta. ANET-LITE +0.507 despite zero supplier-customer
linkage shows a shared "AI fabric buildout" factor dominating fundamentals.

## 15. Chokepoint hierarchy expanded -- irreplaceability ranking of all 20

Question answered per name: if this company disappeared TOMORROW, how badly
would AI infrastructure be disrupted? Ranking judgment DERIVED from corpus
claims (grades carried); time-to-replace and capacity uniqueness are the
criteria. SPOF = single point of failure (no substitute exists at any price
on a <2yr horizon).

| Rank | Ticker | Disappearance impact on AI infra | Time-to-replace | SPOF? |
|---|---|---|---|---|
| 1 | ASML | TOTAL upstream stop: every leading-edge logic node AND every HBM DRAM node needs EUV; no second supplier exists | decade-scale; Canon NIL + Chinese tools attack DUV niches only | YES -- the file's #1 |
| 2 | TSM | CATASTROPHIC: ~72% foundry share (Q1-26 TrendForce), ~90% leading edge, CoWoS sold out >1yr; NVDA/AMD/AVGO/MRVL silicon vanishes from the schedule | multi-year multi-site unproven; substitutable-capacity thesis 'implausible through 2028' (HIGH) | YES |
| 3 | SNPS+CDNS | DESIGN ARREST: combined EDA duopoly ~70%+ share gates every tape-out; chips already in fab continue, nothing new starts | decade-scale switching costs (MEDIUM share figures) | YES (as a pair; each alone survivable-ish) |
| 4 | MU | SEVERE: CY26 HBM supply locked; NVIDIA One Team >50% share of NVDA HBM; Samsung/SKH exist but allocation is committed -- spot-market chaos, 2026 GPU builds slip quarters | 12-24mo for reallocation at scale | NO (3 HBM suppliers) but allocation-locked |
| 5 | LITE | SEVERE at the optics layer: 50-60% global EML share; 200G/lane demand already exceeds supply 25-30%; 800G->1.6T transition stalls | 18-36mo for second-source qualification (COHR InP, Mitsubishi) | YES at 200G/lane EML class |
| 6 | ARM | HIGH but gradual: instruction-set gravity for Graviton/Cobalt/Axion fleets; existing silicon keeps shipping, new designs pause | fleet-scale ISA migration 5yr+ | NO (x86/RISC-V exist) |
| 7 | NVDA | HIGH: ~75-80% of AI accelerator shipments vanish; ASICs cannot absorb the volume in-year; CUDA ecosystem gap hits every framework | 18-48mo per workload via AVGO/MRVL XPUs | NO at silicon layer, YES-ish at ecosystem layer |
| 8 | ONTO | MODERATE-LOCAL: packaging inspection instruments; rivals (KLAC, CAMTEK) can backfill with capacity lead times | 6-18mo | NO |
| 9 | AVGO | MODERATE-HIGH: Tomahawk/Jericho merchant switch silicon + 6-hyperscaler XPU programs stall; Cisco/SiliconOne + MRVL absorb some; $73B backlog redistributes | 12-30mo per program | NO |
| 10 | KLAC | MODERATE: process-control intensity falls back; yields degrade economy-wide (more excursions, slower nodes) rather than lines stopping | 6-12mo partial via AMAT/Onto/Hitachi | NO |
| 11 | AMAT | MODERATE: broadline dep/etch absorbed by LRCX/TEL across most steps; installed-base spares keep fabs running | 6-12mo reallocation | NO |
| 12 | LRCX | MODERATE: memory-weighted etch/dep -- the HBM/DRAM ramp slows hardest here; AMAT/TEL backfill partially | 6-12mo | NO |
| 13 | COHR | MODERATE at layer: ~25% transceiver share lost; Innolight/Accelink/Eoptolink absorb module demand; silicon-photonics program with NVDA pauses | 6-12mo | NO |
| 14 | MRVL | MODERATE: Amazon Trainium program loses its house (~500K->1M chips/yr), 1.6T DSP roadmap slips a year; AVGO/ALAB absorb | 12-24mo | NO |
| 15 | ANET | LOW-MODERATE: Ethernet switching systems replaceable by CSCO/NVIDIA Spectrum-X white-box; software stack (EOS) is the switching cost | 6-12mo hardware, longer EOS re-validation | NO |
| 16 | GFS | LOW for AI core: no leading-edge role; power-management ICs and photonics SOI re-sourced to TSMC specialty/UMC/others | 3-9mo | NO |
| 17 | SNDK | LOW-MODERATE: NAND supply tightens further (already shortage through 2027-28 per TrendForce claims); Kioxia/Samsung/SKYHAIYN absorb bit growth | 3-6mo price adjustment | NO |
| 18 | WDC | LOW: HDD archive capacity shortfall absorbed by Seagate/Toshiba over quarters; prices spike | 2-4 quarters | NO |
| 19 | CDNS alone | see rank 3 (duopoly member) | -- | co-SPOF |
| 20 | QCOM* | LOW for AI infra specifically: mobile/auto annuity irrelevant to datacenter; hyperscaler custom-chip entry was optionality, not load-bearing | n/a | NO |

(*) QCOM included by task instruction though outside the original tier tables;
its profile data comes from the same sources (existing file Section 6).

Corollary (extends existing Section 10): the top of this ranking is unchanged
by the expansion -- ASML, TSM, the EDA duopoly remain the true SPOFs; the
expansion promotes LITE into the explicit SPOF set at the 200G/lane EML class
(demand already exceeds supply 25-30%, HIGH) and confirms that below rank 5,
disappearance is a quarter-or-two repricing event, not a systemic break.
Monitor: EUV bookings, CoWoS wpm, EML supply-demand balance, HBM allocation
windows -- the four falsifiable chokepoint gauges.

## 16. Capex flow map -- whose capex drives whose revenue

Quantified where entity-note facts carry dollar amounts; grades carried.
Direction: downstream capex -> upstream revenue. This is the demand ledger
of the entire file.

### 16.1 The root node: hyperscaler capex

- Big-4 FY26 capex ~$640B confirmed across all four prints (GOOG $175-185B +
  META $125-145B + AMZN $200B + MSFT $125B) -- HIGH, ENT[TSM] via
  tsm-analysis-2026-04-30.
- Later revisions pushed the aggregate to $725B (+77% YoY cohort prints:
  MSFT $190B + AMZN $200B + GOOGL $180-190B + META ~$137B) -- HIGH/MEDIUM,
  ENT[AVGO]/ENT[AMD]/ENT[MU]; waveS-asml cites mid ~$710B on its window.
  Oracle $50B named separately (ENT[MU]); MU note carries the widest print:
  "$750B (+67% YoY)" including ORCL $50B (MEDIUM, Futurum + CreditSights).
- Reconciliation note (DERIVED): $640B (Apr block) vs $710-750B (Jun-Jul
  blocks) differ by revision vintage, not error. Use $700-750B CY26 with the
  date-of-quote attached.

### 16.2 Flow edges, quantified where possible

| Spender | Amount (source) | Flows to (revenue recipients) |
|---|---|---|
| Hyperscalers (Big-4+ORCL) | ~$700-750B CY26 (HIGH, above) | NVDA accelerators+racks (largest single line), AVGO XPUs, MRVL Trainium, ANET AI networking ($3.25B 2026 guide), COHR/LITE optics, DELL/HPE/FN assembly, power/cooling layer (see ref-energy-power-complex) |
| NVDA | buys capacity, not capex: CoWoS-L >50% booked through 2027 (HIGH); OpenAI-linked commitment chain ~$1.15T incl. AVGO $350B / ORCL $300B / MSFT $250B (challenge doc; WSJ reports NVDA tranche stalled Feb-26) | TSM (wafers+packaging; NVDA = #1 customer ~19-22%), MU/SKH (HBM), COHR/LITE (rack optics), ANET/CSCO (fabrics) |
| TSM | 2026 capex guided $52-56B, RAISED to $60-64B on the Q2-26 print (both HIGH, ENT[TSM]) | ASML (EUV/High-NA), AMAT/LRCX/KLAC (WFE ~$135B CY26 total market, LRCX guide HIGH), ONTO (packaging inspection toward ~170K wpm 2027) |
| SK Hynix | ~$8B for ~30 EUV systems by Dec-2027 (Grade B, waveS-asml); memory IDM 2026 capex aggregate ~$65B (HIGH, ENT[LRCX]) | ASML, LRCX (etch/dep weight), AMAT, KLAC |
| Kioxia/SanDisk | NAND capex +41% (wave FM1, MEDIUM) | WFE names' NAND lines (LRCX cryogenic etch), not ASML-heavy |
| MU | FY25 capex $15.86B on $37.38B rev = 42.4% (FIN-S4); FY26 raised $20B->$25B (HIGH); 9-mo FY26 $19.6B +92.2% (HIGH) | ASML (DRAM EUV layers), AMAT/LRCX/KLAC/ONTO |
| AVGO | capex/revenue just 1.0% FY25 (FIN-S4) -- its $73B AI BACKLOG (8-K Mar 4 2026, HIGH) is the real demand instrument, funded BY hyperscaler capex | TSM (XPU wafers), MU/SKH (ASIC HBM +82% YoY 2026, Goldman via ENT[AVGO]) |
| AMD | asset-light similarly (FY24 capex $0.64B, FIN scrape) | TSM N2/N3P + CoWoS ~105K wafer allocation 2026, Samsung HBM4 |
| COHR | FY26 capex $1.10B (FIN scrape, period 2026-06-30) vs $0.44B FY25 -- capacity race | its own InP/laser supply web; equipment vendors |
| ANET | capex de minimis (~$0.05B) | none material upstream -- pure assembly/software margin |

### 16.3 Second-order flows (DERIVED structure)

- Memory-IDM capex (~$65B) -> WFE orders (18-24mo lead) -> tool shipments
  2027-2028 (coupled-cycle math, HIGH, ENT[LRCX]/ENT[KLAC]) -- equipment
  revenue today IS memory capex yesterday; equipment corrections lead
  foundry/memory P&L corrections (existing file Section 3).
- NVDA system revenue -> rack-level pulls: CRDO AECs, APH connectors,
  VRT/ETN power-cooling (outside this file's tickers; see cross-refs).
- The circularity flag stands: >$800B of the ~$1.15T OpenAI-linked chain is
  estimated circular (challenge-thesis-theme-alpha-2026-07-10) -- capex flowing
  INTO the chain is increasingly financed BY the chain's own equity stories.
  Treat the $700-750B aggregate as gross demand, not net external funding.

## 17. Appendix -- computation log and reproducibility

- All quarterly tables: parsed from wiki/investing/filings/<T>/<T>-xbrl.json
  in-session (rows = form/concept/period/value/filed). Dedup rule: latest
  filed row wins per (concept, period). Q4d = FY 10-K revenue minus sum of
  the three preceding 10-Q quarters inside a 15..340-day window; marked
  "(Q4d)". YoY = same-quarter prior year within 330-400 days, direct ratio.
  Anchors verified against the existing document: NVDA +85.2%, MU +345.7%,
  AMD +50.1%, ANET +37.7% all reproduce exactly.
- NI margins = quarterly NetIncomeLoss / same-period revenue; SUSPECT flags
  (>55%) carried from FIN S7 convention and repeated per-row above.
- Technical stats: factors.db bars (src yfinance-5y), window ending
  2026-08-24 intraday close where present (8/21 close for MA/RSI rows).
  CAGR/vol/Sharpe(rf=0)/maxDD use full available history per ticker (1255
  obs standard; ARM 738 since 2023-09 IPO; SNDK 383 since 2025-02 spin;
  GFS 1209 since 2021-10). Beta/corr = daily log returns, 252d and 90d
  windows as labeled. RSI14 = Wilder. Drawdown episodes = peak-to-trough
  <= -20% closes; "OPEN" = unrecovered at data cutoff.
- Correlation subsets (Section 14): 90 common trading days ending 2026-08-24.
- No network access used anywhere in Sections 13-17; every number traces to
  vault files cited inline. Regenerate by re-running the XBRL aggregation +
  factor-store queries documented in [[ref-financial-statements]] Section 0.


---

> **STALE CLAIM (2026-08-25): mean-reversion statistics cited below are from
> quarantined entry FIS-MR-001 -- NO surviving edge under corrected finite-
> capital accounting (base CAGR -4.4% stress / -1.7% standard costs; best
> variant fails BH q=0.117). See
> research/experiments/failed-strategies-registry.md. Figures kept only for
> historical traceability; do not use for any current decision.**
