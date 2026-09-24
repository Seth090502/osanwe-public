---
categories: [sources]
type: reference
target_path: Atlas/sources/investing/ref-theme-alpha.md
created: 2026-04-22
updated: 2026-07-16
status: active
confidence: medium
tags:
  - topic/theme-alpha
  - topic/semiconductor-cycles
  - topic/data-center-capex
  - topic/hbm
  - topic/hyperscaler-spending
  - topic/power-grid-constraints
  - topic/advanced-packaging
  - topic/export-controls
  - ticker/NVDA
  - ticker/AMD
  - ticker/MU
  - ticker/SNDK
  - ticker/MSFT
  - ticker/AMZN
  - ticker/GOOGL
  - ticker/META
  - ticker/AVGO
  - ticker/VRT
  - ticker/AMAT
  - ticker/LRCX
  - ticker/DTCR
  - thesis/theme-alpha
aliases:
  - theme-alpha stack
  - semiconductor stack
  - theme-alpha framework
related:
  - "*investing-moc* (not published)"
  - "*thesis-theme-alpha* (not published)"
  - "[[ref-macro-landscape]]"
  - "*ref-sector-benchmarks* (not published)"
  - "[[ref-scoring-models]]"
  - "*ref-portfolio-doctrine* (not published)"
  - "[[ref-monitoring-rules]]"
  - "*nvda-analysis* (not published)"
  - "*amd-analysis* (not published)"
  - "*mu-analysis* (not published)"
  - "*dtcr-analysis* (not published)"
  - "*msft-analysis* (not published)"
  - "*amzn-analysis* (not published)"
  - "*AVGO* (not published)"
  - "*VRT* (not published)"
  - "*ANET* (not published)"
  - "*MRVL* (not published)"
  - "*CSCO* (not published)"
  - "*ETN* (not published)"
  - "*ABB* (not published)"
  - "*KLAC* (not published)"
  - "*ASML* (not published)"
  - "*TSM* (not published)"
  - "*DLR* (not published)"
  - "*EQIX* (not published)"
  - "*GEV* (not published)"
  - "[[ref-theme-alpha-ingest-2026-04-22]]"
  - "*ref-ai-supply-chain-deep-dive* (not published)"
  - "*ref-memory-storage-cycle-deep-dive* (not published)"
  - "[[ref-ai-power-grid-deep-dive]]"
  - "*CXMT* (not published)"
  - "*YMTC* (not published)"
  - "[[ref-theme-alpha-ingest-2026-07-16]]"
---

# theme-alpha Deep-Dive Framework

1. Stack decomposition by economic layer
2. Supply/demand dynamics per layer
3. 2026-2028 hyperscaler capex trajectory
4. Bottleneck analysis
5. Comparative valuation framework across layers
6. Cycle precedents and structured bear case
7. Geopolitical and regulatory overlay
8. Portfolio application -- decision framework

## 1. Stack decomposition by economic layer

**Grading convention for Sections 1-5, stated once.** Grade A attaches ONLY to a literal string quoted from a primary retrieved this pass. A figure read from a table in a filed primary, or from XBRL company facts, is **Grade B-filed**: filed data, but a table read is not a quotation. Arithmetic on quoted primaries is "[Grade A components; derived]"; on table reads, "[Grade B-filed; derived]". An analyst estimate (IDC, Omdia, TrendForce) is **Grade B even when quoted verbatim and even when reproduced inside a filing** -- verbatim-ness and primacy are different axes. The rule is symmetric across jurisdictions: IDC-inside-an-F-1/A and Omdia-inside-a-prospectus both grade B.

Ten discrete economic layers, each with distinct revenue drivers, margin structures, and cycle sensitivity. Treating them as a single trade is the 2025-era mistake; treating them as a correlated-but-separable rotation is the 2026-era edge. [Grade C -- framework judgment preserved from the 2026-04-22 taxonomy, not a sourced claim.] Rows are deliberately unnumbered: an ordinal column would create a sixth document-wide numbered series with no owner and no external citer. Cite layers by NAME. Companies are enumerated in *ref-ai-supply-chain-deep-dive* (not published); power is owned by [[ref-ai-power-grid-deep-dive]].

| Layer | Revenue driver | Margin structure | Cycle sensitivity |
|---|---|---|---|
| Compute | Accelerator/rack ASP x units | 75%-class GM at steady state, highest in semis | Early-cycle; late-cycle on inventory |
| Memory (HBM + conventional DRAM/NAND) | Bit demand x contract price; HBM contracted forward, conventional re-priced quarterly | Caps near 40% op margin historically, cycles below zero; current cycle atypical | Mid-cycle; asymmetric downside once HBM supply catches demand |
| Advanced packaging (CoWoS, HBM stacking) | Allocation of interposer/substrate capacity | Blended into foundry economics; scarcity rent to the allocator | Binding constraint (Section 4); rotates on capacity catch-up |
| Networking | Bandwidth transitions (400G -> 800G -> 1.6T), port count | 60-65% switching silicon; 40-50% optics | Coincident with compute, lagging ~1 quarter |
| Power and electrical | Electrical content per MW delivered | 20-25% op margin at peak; 12-18 months backlog visibility | Mid-cycle, backlog-protected; cannot cut in step with compute |
| Cooling | Rack density above the air-cooling cap | Capital-solvable on a 6-12 month build; binds at site level | Coincident with the liquid-cooled compute ramp |
| Semiconductor equipment | WFE spend plus installed-base service | Recurring service revenue shields the downside | Mid-cycle; 18-24 month order lead |
| Foundry | Leading-edge wafer starts | High fixed cost, node-ramp gated | Defensive inside the cycle; offensive as the constraint tightens |
| Data center REITs | Leased kW and rental escalators | Cap-rate spread; leverage is the risk vector | Defensive-to-mid; long leases mute cyclicality |
| Hyperscalers | Cloud revenue less capex routed through depreciation | 35-45% cloud op margin | The cycle itself -- they are the customer |

[Grade C: preserved framework, not a 2026 re-derivation. Spot readings that would date the rows were removed rather than refreshed; per-name levels live in Section 5 and refetch at run time.]

### Memory share: two metrics, never one

**Metric 1 -- HBM revenue share.** SK hynix's registration statement states, verbatim: "In the HBM market, we were ranked first globally based on revenue with a market share of 56.4% in the first quarter of 2026, according to IDC." (Source: SK hynix Form F-1/A, accession 0001193125-26-295501, CIK 2120882, filed 2026-07-06) [**Grade A as to the filed TEXT**; **Grade B as to the NUMBER** -- 56.4% is IDC's estimate, and reproducing it inside a registration statement does not make it a filed measurement.] The legacy "roughly 59/20/20 per TrendForce" was an HBM share and is directionally consistent (SK hynix leading, eroding as Samsung and Micron qualify), but that release was not retrievable this pass and it survives only as Grade C legacy. The residual ~43.6% is reported unavailable, not estimated.

**Metric 2 -- total-DRAM revenue share, INCLUDING HBM.** 1Q26, verbatim: Samsung "driving quarterly revenue up 93.4% QoQ to $37.32 billion and increasing market share to 38.5%"; SK hynix "revenue of $27.98 billion, up 62.5% QoQ, ranking second with a 28.8% market share"; Micron "quarterly revenue surging 81.6% QoQ to $21.75 billion, while maintaining a stable 22.4% market share" -- on industry revenue of $97 billion, +81% QoQ (Source: TrendForce 20260601-13070, 2026-06-01) [Grade B -- verbatim, but analyst estimate]. Residual = 100 - 89.7 = ~10.3% [Grade B; derived]. IDC independently puts SK hynix at "a market share of 29.1% in the first quarter of 2026" in "the DRAM market that includes HBM" (Source: SK hynix F-1/A, 2026-07-06) [Grade A as to filed text; **Grade B as to the number**] -- a 0.3pt cross-check confirming both series measure the same object.

**The definitional correction that matters:** no retrievable source publishes a conventional-DRAM-only (ex-HBM) revenue share. The metric that exists is total-DRAM INCLUDING HBM. Labelling the 38.5/28.8/22.4 series "conventional DRAM share" repeats the exact scope error this row exists to fix -- a "conventional-DRAM revenue-share row" cannot be sourced, because the metric does not exist.

The closed-oligopoly critique attaches HERE, to the DRAM revenue layer, not to HBM. CXMT competes in the residual with no HBM presence; SK hynix names it: "Our major competitors in the DRAM market include Samsung Electronics Co., Ltd. ... Micron Technology, Inc. ... and ChangXin Memory Technologies ('CXMT')" (Source: SK hynix F-1/A, 2026-07-06; ellipses elide defined-term parentheticals) [Grade A -- the issuer's own statement, quoted verbatim]. TrendForce's second tier resolves part of that residual -- **Nanya $1.55 billion (+60% QoQ)**, Winbond ~$568 million, PSMC $43 million in 1Q26, together ~$2.16 billion of the ~$10 billion residual -- and does not break CXMT out (Source: TrendForce, 2026-06-01) [Grade B]. Roughly a fifth of the residual is named; the entrant sits in the unnamed remainder. An incumbent's registration statement names a Chinese entrant a major DRAM competitor while that entrant sits at zero HBM share: a supply event in the residual is not a supply event in HBM. Section 7 tests whether CXMT's disclosures support the shock the market priced.

**The operating insight (preserved):** no layer below hyperscalers grows sustainably faster than hyperscaler capex grows, and each layer's share of hyperscaler capex dollars rotates as the binding constraint moves. Which layer captures the marginal dollar is a Section 4 question.

## 2. Supply/demand dynamics per layer

**Capacity physics: HBM capex cannot scale independently of lithography throughput.** Every HBM die needs a 1-alpha or 1-beta DRAM node; those nodes require EUV, so HBM supply is a derivative of ASML shipments. The 2026-07-15 6-K reads: "we are planning to add 30% to our 2026 low NA EUV capacity of around 65 for 2027... Similarly, we plan to add 30% to our 2026 DUV immersion capacity of around 130 for 2027" [Grade A -- quoted verbatim] (Source: ASML Form 6-K, accession 0001628280-26-048235, 2026-07-15). The source states no unit for "around 65"; reading those as SYSTEMS is an interpretation [Grade C -- inference]. Relief lands in 2027; 2026 output is committed.

**The HBM premium: mechanism right, projection void.** The durable claim survives -- the HBM premium is durable only while DDR5 is ample; once commodity DRAM tightens symmetrically, HBM's relative premium narrows even as absolute HBM pricing rises. Any projected compression "to 1-2x by end-2026" is void: the premium did not compress, it INVERTED. "HBM wafer revenue was overtaken by DDR5 64GB RDIMM in 1Q26. This has led HBM profitability to also fall below that of DDR5 64GB RDIMM since 1Q26" [Grade B -- verbatim and retrieved, but an analyst estimate; the release states the finding is "estimated using die size, yield rates, and per-Gb pricing"] (Source: TrendForce 20260602-13074, 2026-06-02). Wafer revenue and profitability are distinct claims; the release asserts both. This supersedes the vault's carry at mu-analysis-2026-07-06.md:268 on wording, not grade -- both are B.

**The inversion is a CYCLE event, not a regime change -- the same source expects it to unwind.** That release is titled, in part, "HBM Contract Prices Expected to Surge Multiples Higher in 2027" [Grade B -- verbatim title; analyst forecast]. HBM is negotiated annually, so conventional DRAM repriced faster in a squeeze that hit both. TrendForce puts HBM at 30% of 2027 DRAM wafer starts, intensifying crowd-out. An inversion its own source forecasts to reverse is not a structural de-rate. The tell is reallocation: "Consequently, suppliers are expected to adjust production allocation between HBM and conventional DRAM depending on HBM pricing outcomes" [Grade B -- verbatim; analyst forecast] (Source: TrendForce, 2026-06-02).

> **DELETED FABRICATION -- memorialized by description, not reproduced.** A sentence beginning "the memory manufacturers can simply..." was once carried in a Grade-A slot attributed to the 2026-06-02 release. It appears ZERO times in either cited TrendForce release (mechanically confirmed in both); it tracks a search-engine summary's paraphrase. It is deleted, not re-graded, and the full string is deliberately NOT reproduced so a grep or claim-extractor cannot re-harvest it from inside its own negation. The underlying idea is real and is carried above in the release's actual words at Grade B.

> **PERISHABLE -- series: TrendForce DRAM/NAND contract prices, as of 2026-07-15. REFETCH BEFORE USE; DO NOT INHERIT.** [Grade B throughout -- analyst estimate.] The conventional and SERVER series are DIFFERENT series that coincide at 3Q26. Never chain across them; the deceleration is base effect plus LTA caps, not demand.
> - CONVENTIONAL DRAM q/q: 1Q26 actual +93-98%; 2Q26 forecast +58-63% (TrendForce, 2026-06-01); 3Q26 forecast +13-18% (TrendForce, 2026-07-03).
> - SERVER DRAM q/q: 3Q26 +13-18%, RDIMM bit supply growing "only 15-20% YoY" against LTAs capping price rises to US CSP clients (TrendForce, 2026-07-09).
> - NAND q/q: 3Q26 +10-15% (TrendForce, 2026-07-03).

**Two vault claims resolved against source.** The ">4:1 HBM wafer-per-bit trade ratio" is REFUTED; drop it. HBM wafer input runs "approximately 18%, 22%, and 30% of total DRAM wafer input by the end of 2025, 2026, and 2027" against bit supply of "approximately 8%, 9%, and 13%" [Grade B -- verbatim; analyst estimate] (Source: TrendForce, 2026-06-02). Against non-HBM output, (w/b) x ((1-b)/(1-w)) = ~2.5x / 2.85x / 2.9x [Grade B; derived] -- nothing reaches 4:1. MU's 10-Q confirms direction, not magnitude: HBM "requires a higher number of wafers... to produce the same number of bits as conventional DRAM in the same technology node" [Grade A -- quoted verbatim] (Source: MU 10-Q Item 1A, accession 0000723125-26-000015, filed 2026-06-25). Second, "equipment spend +29% to $52B bought only +2.4% wpm" is a CONFLATION; cut it. SEMI puts memory 300mm equipment at +29% to $52B in 2026 and capacity at 4.1M wpm (2026) -> 4.2M wpm (2027) = +2.4% (Source: SEMI 300mm Fab Outlook 2Q26, 2026-06-29) [Grade B]. The spend is a 2026 figure, the +2.4% a 2026->2027 delta; they do not divide. SEMI's qualitative point survives: dollars buy node complexity, not wafer starts.

China memory is owned by Section 7; the consequence here is narrow. A DDR5 entrant with zero HBM presence pressures the CONVENTIONAL-DRAM layer -- which just out-earned HBM per wafer -- not the HBM layer. Cycle mechanics: *ref-memory-storage-cycle-deep-dive* (not published).

### MU -- Micron Technology

*Filed figures below are Grade B-filed table reads from the cited 10-Q unless a quoted string is marked.*

#### Financial signals
- MU: 9-month capex $19,602M vs $10,199M, +92.2% y/y 2026-05-28 (per MU 10-Q filed 2026-06-25) [+92.2% derived]
- MU: DRAM ASP +~140%, NAND ASP +~130%, 9M FY2026 y/y (per MU 10-Q Item 1A, 2026-06-25) [paraphrase of a filed sentence; the verbatim string was not lifted this pass]

#### Thesis Fit
Pure-play exposure to the layer where the inversion happened: earnings now lean on conventional DRAM, the residual of HBM allocation. INTERPRETATION, not disclosure -- MU does not break out HBM versus conventional DRAM revenue in the 10-Q [Grade C]. The +140% 9M DRAM ASP confirms price, not units, is doing the work.

#### Risks
- MU: Item 1A discloses capacity shifting from HBM back to conventional DRAM "could result in a significant increase in conventional DRAM supply" and downward pricing pressure (per MU 10-Q) [Grade A on the quoted fragment]
- MU: capex +92.2% y/y against a price series decelerating to +13-18% q/q -- 2027-28 capacity funded past the q/q peak (per MU 10-Q; TrendForce 2026-07-03) [Grade C -- inference]
- MU: five-year annual DRAM ASP band spans a low-40% increase to a high-40% decrease (per MU 10-Q)

#### Catalysts
- MU: FQ4 print ~2026-09-22, TENTATIVE (per broker earnings calendar, 2026-07-15) [Grade C] -- the dominant binary for the memory layer
- MU: 2027 HBM contract negotiations forecast to surge multiples higher, un-inverting the mix (per TrendForce, 2026-06-02) [Grade B -- analyst forecast]

#### Recent
- MU: Singapore HBM advanced-packaging capacity expands from 1H CY2027 (per MU 10-Q)

### SNDK -- Sandisk Corporation

*All FQ3/FQ4 figures below: Grade B-filed table reads from SNDK 8-K Ex-99.1, 2026-04-30.*

#### Financial signals
- SNDK: FQ3-26 revenue $5,950M, +97% q/q, +251% y/y 2026-04-03
- SNDK: FQ3-26 GAAP gross margin 78.4%, +55.9pp y/y
- SNDK: FQ3-26 Datacenter revenue $1,467M, +233% q/q, +645% y/y
- SNDK: FQ4-26 guide revenue $7,750-8,250M, non-GAAP gross margin 79.0-81.0%

#### Thesis Fit
NAND-pure, one layer off the DRAM/HBM allocation fight: NAND does not compete for the EUV-constrained DRAM wafer. That decoupling is why SNDK need not track MU [Grade C -- structural inference].

#### Risks
- SNDK: NBM terms widely reported as $42B minimum revenue and >$11B guarantees are CALL-AND-PRESS sourced; the filed Ex-99.1 confirms only three NBM agreements by end-FQ3 plus two in FQ4 [Grade B on dollar terms; Grade B-filed on the count]. The vault carries the dollar terms at ref-memory-storage-cycle-deep-dive.md:312 as if filed -- a live mis-grading a later pass should correct.
- SNDK: NAND prices decelerate to +10-15% q/q in 3Q26 (per TrendForce, 2026-07-03) [Grade B] -- variable-pricing exposure inside NBM persists if supply catches demand
- SNDK: YMTC capacity expansion is the named structural downside catalyst for NAND supply (see Section 7)

#### Catalysts
- SNDK: FQ4-26 print expected late July / early August 2026 [Grade C -- inferred from the fiscal calendar, not broker-confirmed]; the metric that matters is NBM bit-coverage, not headline revenue

#### Recent
- SNDK: industry 300mm 3D NAND equipment spend +28% to $14B in 2026 (per SEMI, 2026-06-29) [Grade B] -- the supply-side counterweight to the NBM backlog

## 3. 2026-2028 hyperscaler capex trajectory

**Baseline.** Big-4 CY2026 capex guidance aggregates to ~$695-725B, midpoint ~$710B [Grade B aggregate -- no single primary publishes it]. MSFT ~$190B [Grade B -- call-only]; GOOGL $180-190B, raised from $175-185B for the Intersect acquisition [Grade B] (Source: CNBC, 2026-04-29); META $125-145B [Grade A -- quoted below]; AMZN ~$200B, set on the Q4 2025 call, unchanged at Q1 [Grade B] (same source).

**Units versus price -- a first-class analytical object.** A capex trigger denominated in DOLLARS cannot distinguish demand collapse from price deflation: DRAM reversion would cut capex dollars with unit demand unchanged, firing a theme-alpha invalidation when the true event is a memory-MARGIN story. The trigger is sign-inverting on the live scenario, so every reading below is decomposed or marked undecomposable. **Where the decomposition is unavailable, the rung does not advance.**

The filed evidence is asymmetric, and the asymmetry is the finding. META's 8-K Ex-99.1 states verbatim: "We anticipate 2026 capital expenditures, including principal payments on finance leases, to be in the range of $125-145 billion, increased from our prior range of $115-135 billion. This reflects our expectations for higher component pricing this year and, to a lesser extent, additional data center costs to support future year capacity." [Grade A -- quoted verbatim] (Source: META Form 8-K Ex-99.1, accession 0001628280-26-028364, 2026-04-29). Meta attributes the RAISE to price, never the price content of the LEVEL. It says "higher component pricing this year", not "particularly memory" -- that wording is Jassy's at AMZN and must never be cross-attributed.

Microsoft's ~$25B is CALL-ONLY, and the proven absence is the point. On the call: "For calendar year 2026, we expect to invest roughly $190 billion in capital expenditures which includes approximately $25 billion from the impact of higher component pricing" [Grade B -- verbatim against the transcript, but a call is not a filed primary; it sits outside filing liability and is re-cuttable without a filed correction] (Source: Microsoft IR, FY26 Q3 call transcript, 2026-04-29). Its filed Ex-99.1, read end to end this pass, carries no capex guidance at all: "component" 0 occurrences, "pricing" 0, "capital expenditure" 0 [**Grade B-filed** -- a mechanical count is a measurement OF the document, not a quotation FROM it]. The exhibit says only "Microsoft will provide forward-looking guidance in connection with this quarterly earnings announcement on its earnings conference call and webcast." [Grade A -- quoted verbatim] (Source: MSFT Form 8-K Ex-99.1, accession 0001193125-26-191457, 2026-04-29). The single largest quantified price wedge in the complex has no filed existence.

Alphabet's raise is attributed to an acquisition, not components [Grade B]. Amazon quantifies nothing; Jassy said only that "the cost of components, particularly memory, has skyrocketed" [Grade C -- call reporting, transcript not retrieved] (Source: CNBC, 2026-04-29). Net: ~$25B of ~$710B (~3.5%) is DISCLOSED as price; Microsoft's own ratio is ~13% of its $190B. Aggregate price content is NOT computable from disclosure and must not be asserted. Nebius attributed its raise to contracted 2027 demand, "not the cost pressure" [Grade C -- transcript via secondary; wording internally ambiguous] (Source: Nebius Q1 2026 call, 2026-05-13).

**CY2025 Big-4 OCF -- $580.5B. Stated once here and owned here; Sections 6 and 8 cite and never re-derive.** The fiscal-year trap: MSFT's fiscal year ends June 30, so its FY2025 OCF ($136,162M) covers Jul 2024 - Jun 2025 and is NOT calendar-2025 -- an aggregate that uses it is mis-based. MSFT calendar-2025 OCF is reconstructed from filed quarterly XBRL: $37,044M + ($136,162M FY less $93,515M nine-month) $42,647M + $45,057M + $35,758M = **$160,506M** (Source: SEC XBRL company facts, us-gaap:NetCashProvidedByUsedInOperatingActivities, retrieved 2026-07-15) [Grade B-filed components; derived aggregate]:

| Issuer | CY2025 OCF | Basis |
|---|---|---|
| GOOGL | $164,713M | FY2025 = calendar 2025 |
| AMZN | $139,514M | FY2025 = calendar 2025 |
| META | $115,800M | FY2025 = calendar 2025 |
| MSFT | $160,506M | reconstructed; FY ends June 30 |
| **Big-4 total** | **$580,533M (~$580.5B)** | calendar-aligned |

Any use of this aggregate must state the constituent set and that MSFT is calendar-reconstructed.

**Capex-growth threshold (feeds the Exit Ladder via Section 8). Stated once: +81% to +89%.** Basis is the whole problem: META guides "including principal payments on finance leases"; MSFT's ~$190B is lease-inclusive total spend; the cash-flow line is narrower than both. Derived like-for-like on cash PP&E plus finance-lease principal (Source: SEC XBRL company facts, us-gaap:PaymentsToAcquirePropertyPlantAndEquipment / PaymentsToAcquireProductiveAssets / FinanceLeasePrincipalPayments, retrieved 2026-07-15) [Grade B-filed components; derived aggregate]:

| Issuer | CY2025 cash PP&E | + Fin-lease principal | Total |
|---|---|---|---|
| MSFT | $83,094M (calendar-reconstructed) | $2,341M | $85,435M |
| GOOGL | $91,447M | $1,988M | $93,435M |
| AMZN | $131,819M | $1,557M | $133,376M |
| META | $69,691M | $2,524M | $72,215M |
| **Big-4 total** | **$376,051M** | **$8,410M** | **$384,461M (~$384.5B)** |

Against guidance: $695B / $384.5B - 1 = **+80.8%**; $725B / $384.5B - 1 = **+88.6%**. Basis risk is named, not hidden: the guidance aggregate is itself mixed-convention. The conclusion is robust to it -- under every basis constructible from the filings (+67% through +89%), guided growth sits far above the "aggregate growth below 20%" trigger. Section 8 cites this range and this caveat.

**Capex-to-US-GDP.** CY2025 nominal GDP averaged $30,762B (Source: FRED series GDP, retrieved 2026-07-15) [Grade B-filed -- API series read]; $384.5B / $30,762B = **~1.25%**. CY2026 at ~$710B over ~$32.2T = **~2.2%** [Grade B; the 2026 denominator is a forward estimate]. The payload is a ~0.95pt one-year step, and 2.2% sits materially above the dot-com broadband peak (~1.2%) and Apollo (~0.6%) [Grade C -- comparators carried forward, not re-sourced]. Honest note: on the re-derived base, CY2025 at ~1.25% sits roughly AT the broadband peak rather than above it. The 2026 step carries the argument.

**OCF coverage.** Third-party "~90% (BofA) / ~100% (UBS) vs 10-year average 40%" attributions are Dec-2025 reads, NOT re-sourced, and withdrawn rather than silently re-stamped. Computed independently, TTM through 2026-03-31: aggregate OCF ~$617B against ~$434B PP&E-only capex = **~70%** (GOOGL 63.0%, MSFT 57.2%, META 61.1%, AMZN **101.7%**) [Grade B-filed components from the four Q1-2026 8-K exhibits plus MSFT/META FY2025 cash-flow statements; ~70% is DERIVED]. On the calendar-aligned CY2025 base, capex/OCF ran $384.5B / $580.5B = **66.2%**, and guided 2026 capex is **120-125%** of that prior-year OCF base -- the crossover Section 6 describes.

**Scenario A.** Aggregate 2026 lands ~$423B (+10% on $384.5B) versus guided $695-725B: a **~39% to ~42% shortfall**, not readable as a demand event on dollars alone. Were Microsoft's ~13% price content to generalize, full reversion of 2026 component inflation removes ~$94B with ZERO unit change, so a ~$620B print is consistent with FLAT units [Grade D -- extrapolation of one issuer's ratio; not a measured aggregate]. Scenario A requires a print far BELOW that price-only floor to read as demand rather than a memory-price artifact.

**Telecom precedent (preserved).** US telecom invested >$500B in five years after the 1996 Telecom Act; FCC Chairman Michael Powell's July 30, 2002 Senate testimony put industry debt at ~$1 trillion "much of which will never be repaid" [Grade A -- quoted verbatim from the primary written statement] (Source: FCC, docs.fcc.gov/public/attachments/DOC-224797A1.pdf).

| Ticker | Peak | Trough | Drawdown | Recovery |
|---|---|---|---|---|
| CSCO | $80.06 Mar 27 2000 | $8.60 Oct 8 2002 | -89% | Dec 10 2025 ($80.25) -- 25 years |
| NT (Nortel) | C$124 Jul 2000 (38% of TSE) | C$0.47 Aug 2002 | -99.6% | Ch.11 Jan 14 2009 |
| LU (Lucent) | $84 in 1999 | $0.55 Oct 2002 | ~-99% | Merged 2006 Alcatel; Nokia 2016 |
| JDSU | $108.66 Aug 2000 | $1.10 Oct 2002 | ~-99% | Split to VIAV/LITE Aug 2015 |
| GLW (Corning) | ~$113 Aug/Sep 2000 | <$2 in 2002 | ~-98% | Recrossed $113 2024-2025 |

David Cahn's "$600B Question" (Sequoia, June 2024) remains the payback frame; that is an essay title, not a capex level.

**Customer-concentration debunk (preserved).** The bear anchor "4 customers = 60% of revenue" is NOT sourced from NVDA's FY2025 10-K -- that filing disclosed three direct customers at 12%/11%/11% = 34%. The 61% figure comes from the Q3 FY2026 10-Q. Concentration did rise materially through FY2026; the misquote attributes 61% to the wrong document.

### MSFT -- Microsoft Corporation

#### Financial signals
- MSFT: CY2026 capex guidance ~$190 bn, incl. ~$25 bn from component pricing, 2026-04-29 (per FY26 Q3 call) [Grade B -- call-only; absent from the filed 8-K]
- MSFT: 9M FY26 OCF $127.494 bn vs PP&E additions $80.146 bn, 62.9%, 2026-03-31 (per MSFT 8-K Ex-99.1) [Grade B-filed; derived]
- MSFT: CY2025 OCF $160.506 bn, calendar-reconstructed (per SEC XBRL company facts, 2026-07-15) [Grade B-filed; derived]
- MSFT: Azure +40% (+39% cc); commercial RPO $627 bn, +99%, 2026-03-31 (per MSFT 8-K Ex-99.1) [Grade B-filed]
- MSFT: AI business annual revenue run rate $37 bn, +123% y/y, 2026-03-31 (per MSFT 8-K Ex-99.1) [Grade B-filed]

#### Thesis Fit
- MSFT: sole issuer quantifying the price wedge, and it does so outside the filing [Grade C]

#### Risks
- MSFT: ~$25B attribution sits on a call, outside filing liability, re-cuttable without a filed correction; absence from the filed Ex-99.1 established by end-to-end read [Grade B-filed -- mechanical count]

#### Catalysts
- MSFT: FQ4 FY26 print 2026-07-29 pm -- is the price wedge re-quantified, raised, or dropped? [Grade B]

### GOOGL -- Alphabet Inc.

#### Financial signals
- GOOGL: 2026 capex guidance $180-190 bn, raised from $175-185 bn for Intersect, 2026-04-29 (per CNBC) [Grade B -- transcript not retrieved end to end]
- GOOGL: TTM PP&E $109.924 bn vs TTM OCF $174.353 bn, 63.0%, 2026-03-31 (per GOOGL 8-K Ex-99.1) [Grade B-filed; derived]
- GOOGL: CY2025 OCF $164.713 bn; CY2025 cash PP&E $91.447 bn (per GOOGL FY2025 10-K) [Grade B-filed]
- GOOGL: Q1 2026 FCF $10.116 bn vs $24.551 bn in Q4 2025 (per GOOGL 8-K Ex-99.1) [Grade B-filed]

#### Thesis Fit
- GOOGL: counter-example to the price narrative -- raise attributed to M&A, not components; best OCF coverage of the four [Grade C]

#### Risks
- GOOGL: backlog conversion is management-estimated, not contracted-and-filed; 2027 capex guided to rise significantly [Grade B]

#### Catalysts
- GOOGL: Q2 2026 print 2026-07-22 -- does the range move, and on what stated cause? [Grade A -- date quoted verbatim at Section 8]

### AMZN -- Amazon.com, Inc.

#### Financial signals
- AMZN: 2026 capex guidance ~$200 bn, set 2026-02, unchanged at Q1 (per CNBC, 2026-04-29) [Grade B]
- AMZN: TTM PP&E $151.003 bn vs TTM OCF $148.531 bn, 101.7%, 2026-03-31 (per AMZN 8-K Ex-99.1) [Grade B-filed; derived]
- AMZN: CY2025 OCF $139.514 bn; CY2025 productive-asset purchases $131.819 bn (per AMZN FY2025 10-K) [Grade B-filed]
- AMZN: TTM PP&E +$59.3 bn y/y, "primarily reflects investments in artificial intelligence"; TTM FCF $1.2 bn vs $25.9 bn y/y (per AMZN 8-K Ex-99.1) [Grade A on the quoted fragment; Grade B-filed on the figures]

#### Thesis Fit
- AMZN: OCF coverage above 100% on filed trailing actuals before the ~$200B guide is spent; further raises are debt- or lease-financed [Grade C -- inference]

#### Risks
- AMZN: zero price/unit decomposition disclosed -- a dollar cut here cannot advance a rung alone

#### Catalysts
- AMZN: Q2 2026 print 2026-07-30 pm (tentative) -- FCF trajectory, any capex re-guide [Grade D -- date unconfirmed]

### META -- Meta Platforms, Inc.

#### Financial signals
- META: 2026 capex guidance $125-145 bn, raised from $115-135 bn on "higher component pricing this year", 2026-04-29 (per META 8-K Ex-99.1, accession 0001628280-26-028364) [Grade A -- quoted verbatim in full above]
- META: Q1 2026 capex incl. finance-lease principal $19.84 bn vs OCF $32.226 bn, 61.6% (per META 8-K Ex-99.1) [Grade B-filed; derived]
- META: CY2025 OCF $115.800 bn; CY2025 cash PP&E $69.691 bn + finance-lease principal $2.524 bn (per META FY2025 10-K) [Grade B-filed]
- META: Q1 2026 revenue $56.311 bn, +33% y/y; Q1 FCF $12.386 bn vs $10.334 bn y/y (per META 8-K Ex-99.1) [Grade B-filed]

#### Thesis Fit
- META: only issuer whose price attribution sits inside a FILED document, anchoring the decomposition; cleanest tension case -- no cloud-customer revenue layer monetizes the build [Grade C]

#### Risks
- META: raise attributed to price while 2026 total expenses guided $162-169 bn, "unchanged from our prior outlook" [Grade A -- quoted verbatim] -- both cannot hold if component inflation reaches opex

#### Catalysts
- META: Q2 2026 print 2026-07-29 pm -- does the component-pricing language survive into the next filed Ex-99.1? [Grade B]

## 4. Bottleneck analysis

The single most valuable framework in this document: at any moment in an infrastructure super-cycle, one layer is binding, and the stock in that layer compounds earnings faster than any other layer -- until the constraint rotates. Naming the current binding constraint and the next one is the operating game.

**The binding constraint as of 2026-07-15 is MEMORY, not CoWoS packaging** -- a rotation from the April 2026 reading, on two series moving opposite ways.

Packaging is loosening. The CoWoS gap "is expected to narrow significantly from around 20% currently to about 10% by the end of 2026" (Source: TrendForce, 2026-06-15) **[Grade C -- and this section SETTLES the grade for this series document-wide, so no other section may exceed it.** The chain is TrendForce relaying Economic Daily News citing unnamed institutional investors: a relayed analyst estimate is C, not B. TSMC discloses capacity and capex direction but never utilization, so no better grade is constructible for any CoWoS utilization or gap series.] A gap halving inside two quarters rotates OUT.

Memory is tightening on reported margin. Micron FQ3-26 (ended 2026-05-28) printed 84.6% GAAP gross margin on $41.5B revenue against $9.3B a year prior [Grade B-filed], and guided FQ4-26 to "Gross margin Approximately 86%" [Grade A -- quoted verbatim from the Business Outlook table] (Source: MU Form 8-K Ex-99.1, accession 0000723125-26-000013, filed 2026-06-24). Margin expanded **~10 points sequentially** -- the confirmed 4Q GAAP GM chain runs 44.7 -> 56.0 -> 74.4 -> 84.6, i.e. +10.2pt (MU.md:265). Expansion of that size inside the layer under question is the inverse of the rotation-out tell; "server DRAM will remain undersupplied in the third quarter" (Grade B -- TrendForce 2026-07-03) confirms the physical read.

Two qualifications. Memory binds through PRICE more than units: conventional DRAM prices decelerate to +13-18% q/q in 3Q26 from ~+90% in 1Q26, so the tightening RATE already slows while the level stays extreme -- that deceleration, not a margin break, is the leading edge of rotation-out. And compute is not compressing: NVDA held GM flat while absorbing that memory inflation, passing input cost through rather than eating it.

Power is the next constraint up the queue and the longest to reset; it is owned in full by [[ref-ai-power-grid-deep-dive]] and never restated here. Rotation cadence: memory every 18-24 months (one node transition), equipment every 24-36 months (WFE order lead), foundry with node ramp (3-4 years), power on the 5-7 year interconnect queue. Buy-the-bottleneck works until the constraint is over-supplied; the signal is gross-margin compression in the bottleneck name while the next-layer name's backlog accelerates.

> **PERISHABLE -- binding-constraint panel, as of 2026-07-15. REFETCH BEFORE USE; DO NOT INHERIT.** (Rows are "panel row N", NOT the Section 8 rotation signals; never collide the two.)

| Panel row | Series ID | Reading | Read |
|---|---|---|---|
| 1 | MU consolidated GM, FQ3-26 / FQ4-26 guide | 84.6% / ~86% | Memory BINDING (Grade A on the quoted ~86% guide; Grade B-filed on 84.6%) |
| 2 | NVDA non-GAAP GM, Q1 FY27 / Q2 FY27 guide | 75.0% / 75.0% | Compute intact (Grade B -- filing not retrieved directly) |
| 3 | TSMC CoWoS supply-demand gap | ~20% -> ~10% end-2026 | Packaging rotating OUT (Grade C -- relayed estimate) |
| 4 | LRCX non-GAAP GM, Mar-26 vs Sep-25 record | 49.9% vs 50.6% | Equipment flat-to-soft (Grade B-filed, LRCX 8-K 2026-04-22) |

The power layer has no panel row by design: [[ref-ai-power-grid-deep-dive]] owns it, and a re-derived VRT figure here would duplicate or contradict that document.

"Buy the bottleneck" breaks down in two named ways. First, when customer concentration inverts -- hyperscalers absorbing the bottleneck via captive custom silicon (TPU/Trainium/MTIA) faster than the merchant market can reset pricing. Second, when the bottleneck is replaced by a cheaper substitute (Ethernet displacing InfiniBand is this pattern already in progress). The operational hedge is to hold the one-layer-up and one-layer-down names alongside the bottleneck name, so rotation does not require perfect timing.

### NVDA -- NVIDIA Corporation

*Honest absence, binding on every line below: the sec.gov-hosted 8-K returned HTTP 403 to direct retrieval this pass. These figures come from a search-result rendering, not a verbatim pull; Ex-99.1 was NOT read end to end and no string here is quoted. All cap at Grade B. A future pass should re-pull it directly.*

#### Financial signals
- NVDA: Q1 FY27 revenue $81.6B, +85% y/y, 2026-05-20 (per NVDA Form 8-K)
- NVDA: Q1 FY27 Data Center revenue $75.2B, +92% y/y, 2026-05-20 (per NVDA Form 8-K)
- NVDA: Q1 FY27 non-GAAP GM 75.0%; Q2 FY27 guide $91.0B +/- 2% at GM 75.0% (per NVDA Form 8-K)
- NVDA: Q1 FY27 free cash flow $48.6B, 2026-05-20 (per NVDA Form 8-K)

#### Thesis Fit
- NVDA: compute; incumbent bottleneck name whose constraint rotated to memory. Flat GM through the sharpest memory-price shock on record evidences pass-through pricing power -- bottleneck-adjacent, not bottleneck-binding [Grade C -- inference]

#### Risks
- NVDA: customer concentration -- the layer's first named breakdown mode -- runs live (Section 3 carries the filing-level correction)

#### Catalysts
- NVDA: Q2 FY27 print; Rubin ramp meeting CoWoS catch-up; Hyperscale-vs-ACIE reporting change alters how concentration reads [Grade C]

### AMD -- Advanced Micro Devices

*Honest absence, binding on every line below: read via a sec.gov search result, not re-pulled verbatim; nothing here is quoted. All cap at Grade B.*

#### Financial signals
- AMD: Q1 2026 revenue $10.3B, +38% y/y, 2026-05-05 (per AMD Form 8-K)
- AMD: Q1 2026 non-GAAP gross margin 55%, GAAP 53%, 2026-05-05 (per AMD Form 8-K)
- AMD: Q1 2026 Data Center revenue $5.8B, +57% y/y, 2026-05-05 (per AMD Form 8-K)
- AMD: MI350-series and 5th-gen EPYC named Q1 2026 Data Center growth drivers, 2026-05-05 (per AMD 8-K)

#### Thesis Fit
- AMD: mid-layer compute; the overlap that rotates before bottleneck-layer positions. 55% GM vs NVDA 75.0% is the structural gap -- a price-taker in the shared layer, least-protected if memory cost outruns accelerator ASP [Grade C -- inference]

#### Risks
- AMD: MI450/Helios is 2H 2026 -- revenue guided, not booked; HBM4 for MI455X rides a Samsung collaboration, i.e. direct exposure to the currently-binding layer [Grade B]

#### Catalysts
- AMD: MI450 1-GW OpenAI rollout 2H 2026; OCI Helios cluster, 50,000 GPUs deploying Q3 2026 [Grade B]

### TSM -- Taiwan Semiconductor Manufacturing

*All figures below: Grade B-filed table reads from TSMC Form 6-K, accession 0001046179-26-000199, 2026-04-16.*

#### Financial signals
- TSM: Q1 2026 revenue $35.90B, +40.6% y/y
- TSM: Q1 2026 gross margin 66.2%
- TSM: Q2 2026 guide revenue $39.0-40.2B, GM 65.5-67.5%
- TSM: 2026 capex guided $52-56B
- TSM: advanced technologies (7nm and below) 74% of Q1 2026 wafer revenue

#### Thesis Fit
Foundry and packaging -- the April 2026 bottleneck, now rotating out on the CoWoS gap series. On demand direction: "Our business in the first quarter was supported by strong demand for our leading-edge process technologies," said Wendell Huang, Senior VP and Chief Financial Officer of TSMC (Form 6-K, 2026-04-16) [Grade A -- retrieved and quoted verbatim]. Leading-edge wafers (N2/A16) remain the constraint benefiting TSM exclusively rather than a diversified basket.

#### Risks
- TSM: Taiwan concentration is the binary tail (Section 7); TSM is also most exposed to its own bottleneck resolving -- as CoWoS supply catches demand, allocation stops being a moat for its customers [Grade C]

#### Catalysts
- TSM: Q2 2026 results 2026-07-16 -- nearest dated test of the capex trajectory and the advanced-packaging allocation split [Grade B]

## 5. Comparative valuation framework across layers

This section APPLIES the valuation method owned by [[ref-valuation-methodology]]; it does not re-derive it, and **it states no level anywhere in its body.** A frozen per-name price grid, built on a value that was wrong on its own stated date, can prime months of analysis before anyone notices -- which is precisely why no level appears here, not even as a quarantined example. **This section carries a METHOD and a table SHAPE, never an inventory. No numeric cell below is authoritative.**

> **PERISHABLE -- ALL VALUES REFETCH BEFORE USE; DO NOT INHERIT. Populate from the broker/quote source at run time.**
> Series: `theme-alpha-valuation-dashboard`; as of 2026-07-15 (shape only, zero values).

| Name | Price | Fwd P/E | TTM P/E | 5yr Avg P/E | P/S | EV/EBITDA | Notes |
|---|---|---|---|---|---|---|---|
| MU | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | deep cyclical -- normalize per S6 of the method ref |
| SNDK | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | post-spin; 5yr history incomplete by construction |
| NVDA | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | check non-cash mark contribution to E |
| AMD | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | |
| TSM | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | ADR; Taiwan-risk discount is inside the multiple |
| MSFT | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | |
| GOOGL | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | check non-cash mark contribution to E |
| AMZN | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | |
| META | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | capex/revenue is the tension variable, not the multiple |
| AVGO | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | software mix -- 5yr average spans a pre-VMware firm |
| VRT | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | `<REFETCH>` | backlog coverage, not the multiple, is the floor |

**Column provenance at run time.** Price: the broker read MCP; anchor threshold math to the regular-session close. Fwd P/E, TTM P/E, P/S and EV/EBITDA are published per ticker as "Forward PE", "PE Ratio", "PS Ratio" and "EV / EBITDA" (Source: stockanalysis.com per-ticker statistics page, retrieved 2026-07-15) [Grade B -- authoritative secondary]. **5yr Avg P/E is published by no permitted source** -- that line item does not exist on the statistics page (verified by retrieval, 2026-07-15) [Grade B]. Derive it from the per-ticker quarterly ratio history, which carries "PE Ratio" and "PB Ratio" across 20 quarters (same site, financial-ratios page, quarterly view) [Grade B]; twenty quarters sits at the edge of a true five-year window, so state the window actually used. **Honest absence: column coverage was verified on the MU ticker page only**; the layout is uniform but no other ticker page was opened this pass. Where the average cannot be derived, leave `<REFETCH>` -- never a cross-sector figure, never a model prior.

**The comparison axis, preserved.** Each name is compared against ITS OWN five-year average, never a cross-sector median: the ten layers of Section 1 carry structurally different margin profiles and cycle sensitivities, so a cross-layer median compares nothing, while a name's own history holds layer economics constant and isolates re-rating. Two qualifications: a five-year window spanning a firm's own structural change (a spin-off, a large software acquisition) is not like-for-like and must be flagged rather than averaged; and for deep cyclicals the earnings multiple inverts -- trough earnings screen expensive, peak earnings screen cheap -- so P/E-versus-own-average is actively misleading without normalization (Source: [[ref-valuation-methodology]] Section 6, citing Damodaran 2009) [Grade B].

**Cycle-position read, as a method rather than a number.** Pull the quarterly "PB Ratio" series for the memory name, construct its own five-year range, and read the current print against it. **This section states neither the range nor the reading: both live in the Section 8 PERISHABLE MU P/B block, which owns that series.** A reading far above the top of a name's own range is the cycle-position signal that a holder is paying a peak-cycle price on peak-cycle book; where the range is breached widely, the P/B-versus-ROE justified framework (method ref Section 6) is the cross-check, and the cycle-position assumption -- mid-cycle versus cycle-top -- must be stated explicitly, because it flips the verdict.

**Freshness gate.** This table is usable by an analysis run ONLY after every `<REFETCH>` cell has been populated in that run, from that run's own fetch, with an as-of stamp. An unpopulated or inherited dashboard is not evidence and carries no grade.

## 6. Cycle precedents and structured bear case

**Telecom precedent: Section 3 owns it.** Section 3 carries the >$500B 1996-2001 US telecom capex figure, FCC Chairman Michael Powell's July 30 2002 Senate testimony putting industry debt at ~$1 trillion "much of which will never be repaid" [Grade A -- quoted verbatim] (Source: FCC, docs.fcc.gov/public/attachments/DOC-224797A1.pdf), and the peak-to-trough drawdown table (CSCO -89%, NT -99.6%, LU ~-99%, JDSU ~-99%, GLW ~-98%). This section cites that record and does not restate it. This pass additionally confirms ~$2T of market value extinguished and ~500,000 jobs lost, both stated verbatim in the SAME Powell July 30, 2002 written statement: "This is an industry where nearly 500,000 people in the United States alone have lost their jobs and approximately $2 trillion of market value has been lost in the last two years." [Grade A -- quoted verbatim] (Source: FCC, docs.fcc.gov/public/attachments/DOC-224797A1.pdf).

Structural similarities to 2026: capex supercycle priced for projected demand; equity multiples sustained on hyper-growth; debt-funded buildout. Structural differences: (1) cloud is recurring-revenue against telecom's one-time equipment -- hyperscalers are sticky customers through bad quarters in ways CLECs were not; (2) AI training/inference has measurable productivity payback, and end-revenue actuals now print at a scale dark fiber never reached (Anthropic run-rate crossed $47B in May 2026, Grade A; OpenAI ~$25B annualized February 2026, Grade C); (3) hyperscalers are the customer, not the telcos -- the Big-4 CY2025 aggregate OCF, against WorldCom/Global Crossing's negative free cash flows, is the load-bearing contrast.

**On that OCF figure: one number, one place.** Section 3 owns the Big-4 CY2025 OCF aggregate, derives it from the four filed cash-flow statements, and states its constituent set and its fiscal-year-convention caveat. This section CITES it and never re-derives it; any use of the aggregate must carry the constituent set Section 3 names. Independent cross-check, and a distinct claim rather than a restatement of the level: Epoch AI computes hyperscaler operating cash flow growing ~23%/yr against cash capex growing ~70%/yr, with aggregate capex overtaking OCF around Q3 2026 (Source: Epoch AI, "Hyperscaler Capex vs Cash Flow", 2026) [Grade B]. That crossover -- not a coverage ratio -- is the durable form of the bear's cash-flow spine.

**Base rates.** MU peak-to-trough: 2000-2002 ~75%; 2007-2009 ~80%; 2018-2019 ~45%; 2021-2022 ~50% [corrected this pass from ~55%: closing-basis drawdown (96.34-48.88)/96.34 = 49.3%, intraday-extreme (98.45-48.43)/98.45 = 50.8%, re-derived from split-adjusted primary price data -- Grade B, derived]. AMAT: 2000-2002 ~75%; 2018-2019 ~40%; 2021-2022 ~40%. NVDA's 2022 drawdown ran ~66% peak-to-trough in nine months [confirmed this pass: closing-basis (33.376-11.227)/33.376 = 66.4%, re-derived from split-adjusted primary price data -- Grade B, derived]. These will not apply linearly to the current cycle, but they cap the "this time is different" argument. [Grade C -- carried forward for AMAT's three cycles and MU's other three cycles (2000-02, 2007-09, 2018-19), none re-pulled this pass. The two most load-bearing amplitudes -- MU 2021-22 and NVDA 2022 -- were re-derived this pass from split-adjusted primary price data: Grade B, derived.]

**Cycle-peak signals to monitor (cycle-peak signal 1-6).** The series label is load-bearing: these are **cycle-peak signals**, a Section 6 series. They are NOT the Section 8 **rotation signals** (1-4), NOT the Section 8 **structural exit criteria** (1-5), and NOT Section 4's **panel rows** (1-4). A bare "signal 4" resolves to a different object in each series; always name the series.

1. **Cycle-peak signal 1 -- customer-concentration inflection**: top-4 NVDA customer concentration crossing back down from 61% toward 40% (see Section 3).
2. **Cycle-peak signal 2 -- inventory/channel fill**: AVGO, AMD, MRVL days-of-inventory crossing above 100 days.
3. **Cycle-peak signal 3 -- order cancellations**: CoWoS allocation cancellations, typically leaked before disclosed.
4. **Cycle-peak signal 4 -- gross-margin compression**: NVDA DC GM below 73% for two consecutive quarters.
5. **Cycle-peak signal 5 -- hyperscaler guide-cuts**: any of MSFT/AMZN/GOOGL/META cutting FY capex intra-year.
6. **Cycle-peak signal 6 -- capex-growth-rate deceleration**: trigger unchanged at **aggregate annual growth below 20%**. **Section 3 owns the 2025->2026 growth rate and its baseline; this section cites that figure and never re-derives it** -- a document correcting a baseline error must not ship two baselines. Warning carried forward: the predecessor's **+45%** understated distance-to-trigger by roughly half and biased the ladder toward premature harvest. Epoch AI corroborates Section 3's re-derivation by an independent method, parsing XBRL tags from EDGAR 10-Q/10-K filings rather than call commentary (Source: Epoch AI, "Hyperscaler capex has quadrupled since GPT-4's release", 2026) [Grade B]. Per Section 3 this signal reads only on **units-vs-price-decomposed** capex: a DRAM-deflation-driven decline in capex dollars is not a demand cut, and where the decomposition is unavailable the rung does not advance.

**Bear case decomposition.**

**Scenario A (baseline and arithmetic owned by Section 3).** The scenario is a 10% capex growth print against the guided range; Section 3 states the resulting aggregate, the shortfall to the guide, and the price-only floor below which a shortfall reads as demand rather than as a memory-price artifact. This section supplies only the layer transmission: NVDA DC revenue decelerates toward the 2022-H2 arc (+61% Q2 CY22 -> +11% Q4 CY22 -> -11% Q1 CY23); AVGO backlog conversion stretches; MU contracted 2026 HBM volumes hold while 2027 pricing softens; VRT backlog holds with book-to-bill falling toward ~1.5x. **No equity-impact chain is stated here**: it requires forward multiples, and Section 5 emits `<REFETCH>` placeholders by design. Compute compression at run time against each name's own 5-year range. [Grade C]

**Scenario B (superseded premise; re-specified).** The predecessor's premise -- ChatGPT ARR plateauing at $30B and Anthropic at $35B -- is refuted by realized data: Anthropic disclosed "our run-rate revenue crossed $47 billion earlier this month" (Source: Anthropic, Series H announcement, 2026-05-28) [Grade A], and OpenAI ran ~$25B annualized in February 2026 (Source: Sacra, 2026) [Grade C]. Combined ~$72B **already exceeds structural exit criterion 2's $60B combined-plateau bar**, a live input to Section 8. The bear does not die; it relocates to a higher level, and the only actual plateau evidence in the set is reporting of an OpenAI run-rate flatline near $25B across February-April 2026 [Grade D -- secondary, not re-confirmed]. Two definitional cautions: these are run-rate, not TTM actuals; and Anthropic books partner-channel revenue gross, so the figure is not comparable to a public-company revenue line. A third-party July 2026 estimate of ~$69B is analyst-derived [Grade C].

**Scenario C: export controls tighten** -- H20/MI308 licenses reversed or denied; ~5% revenue impact at NVDA/AMD, contained, but accelerates Chinese indigenous substitution (Section 7). **Scenario D: Taiwan disruption** -- a binary tail, not a cyclical case; no substitutable leading-edge capacity inside 18 months. **Scenario E: power-grid binding delays 18-24 months** -- compute orders hold but utilization drops and capex shifts from GPUs toward electrical/cooling/site infrastructure; the most portfolio-relevant tail, hurting compute modestly while benefiting the power layer (see [[ref-ai-power-grid-deep-dive]]). [all Grade C]

**Bull case rebuttals**: agent adoption is inflecting rather than plateauing (Anthropic's trajectory to a $47B run-rate is the cleanest evidence, Grade A); enterprise pilot-to-production friction is easing as vendor-buy beats build; sovereign AI adds demand orthogonal to hyperscaler capex; physical AI/robotics is a second wave outside current data-center assumptions [Grade C-D]. The disciplined read: the base rates above are the constraint on all four rebuttals -- none of them has ever repealed a memory cycle.

## 7. Geopolitical and regulatory overlay

Export controls moved from predictable annual tightening to transactional bilateral deals. History: Oct 2022 initial BIS rules; Oct 2023 tightening; Dec 2024 further restrictions; Jan 2025 "AI Diffusion Rule" 3-tier country framework; April 2025 H20 and MI308 shipments blocked; July 2025 reversal, Commerce approving H20/MI308 licenses contingent on 15% of China revenue remitted to the US government -- the first revenue-sharing condition in US export-control history [Grade C -- preserved, not re-pulled].

**Policy state, re-established 2026-07-15** (any "as of April 2026" snapshot is void; the direction of travel reversed). Verbatim: "BIS will now review export license applications for the Nvidia H200, AMD MI325X, and similar chips on a case-by-case basis provided certain security requirements are met" (Source: BIS press release, 2026-01) [Grade A -- retrieved and quoted verbatim], effective immediately on Federal Register publication, conditional on no reduction in capacity available to US customers, purchaser compliance screening, and third-party testing [Grade A, same release]. Blackwell-class parts reportedly stay under presumption of denial, thresholds reported at 21,000 TPP / 6,500 GB/s [Grade C -- NOT confirmed against the Federal Register text]. BIS guidance of 2026-05-31 ties licensing to a purchaser's ULTIMATE PARENT rather than its address, closing the Singapore/Malaysia/UAE subsidiary channel [Grade C]. The binary risk is unchanged in kind -- legislative override of an executive accommodation (AI OVERWATCH Act, H.R. 6875, Grade C) -- but now cuts both ways.

CHIPS Act implementation ($52B: $39B manufacturing, $13B R&D): TSMC Arizona $6.6B; Samsung Texas $4.75B; Intel $7.86B; Micron $6.1B; GlobalFoundries $1.5B [Grade C, preserved]. The AZ/TX/OH/NY/ID delegations have resisted wholesale unwind.

**Taiwan remains the dominant tail.** TSMC produces ~90% of global leading-edge (3nm and below); substitutable capacity runs 2028-2030 at earliest; NVIDIA was 19% of TSMC 2025 revenue, Apple 17% [Grade C, preserved]. The wartime path requires Samsung 2nm and Intel 18A to ramp -- 3-5 years. Binary tail, not a cyclical case. ASML remains the sole EUV supplier, making every HBM node migration downstream of one company in one country [Grade B]. The Japanese materials basket -- Shin-Etsu and SUMCO (wafers), TEL (coater/developer), JSR (photoresists) -- is the secondary single-point-of-failure and is not diversifiable by holding more names [Grade C, preserved].

Antitrust: NOT re-established this pass. Structure only, Grade D pending refresh -- an NVIDIA DOJ/FTC inquiry opened 2024 without advancing to suit; EU DMA designations on MSFT/AMZN/GOOGL/META constrain bundling without materially impairing theme-alpha economics. REFETCH BEFORE USE.

**The China-memory entrant: the operative prospectus reverses the benign reading.** The 2026-07-15 memory drawdown priced a Chinese supply shock. The prospectus filed 2025-12-30, against which an earlier pass judged that shock unsupported, is **SUPERSEDED and was not retrievable.** The operative disclosure is the updated STAR Market prospectus, SSE document `002170_20260517_MGLN.pdf`, 370 pages, retrieved and text-extracted 2026-07-15. Read against it, four prior findings survive and three reverse -- and the reversals are the ones the synthesis rested on.

**A grading convention, stated once and applied to every CXMT claim below.** The prospectus is a filed regulatory primary, but it is written in Chinese, and this document is ASCII-only. A verbatim quotation from it cannot be rendered here, and a translation is not a primary quotation -- verbatim-ness and primacy are different axes, and a translated string is neither. The figures below are also numeric table reads, not quoted strings. **Every CXMT prospectus claim therefore caps at Grade B-filed** -- filed-primary, Chinese-language, read from the named page -- and none may occupy a Grade-A slot. This is a ceiling imposed by the rendering rule, not a doubt about the source. **Independent verification, closed 2026-07-16: a second fetch of `002170_20260517_MGLN.pdf`, re-extracted via two engines (pdftotext -layout and PyMuPDF), confirms every cited CXMT figure below exactly** -- utilization 87.06%/92.46%/95.73%, production-to-sales 99.45%/97.94%/90.67%, the zero-count for HBM (reproduced independently on both engines), the DDR4-ceased-end-2024 footnote, the 97.49%/97.21% China+HK geography split, the RMB 22.1B brownfield equipment tool spend, and the no-new-land use-of-proceeds language at all three sited projects. The grade ceiling stays Grade B-filed per the Chinese-language/table-read convention above -- independent verification confirms the figures, it does not promote a table read to Grade A.**

**What survives.** HBM appears **ZERO times across all 370 pages** (mechanical count on the extracted text, 2026-07-15) [Grade B-filed -- a mechanical count is a measurement of the document, not a quotation from it] -- the single most load-bearing finding, and it survives the update intact. The raise buys no greenfield fab: all three use-of-proceeds projects are sited inside existing plant, each carrying an affirmative no-new-land statement at 1-1-367, 1-1-368 and 1-1-369 [Grade B-filed] -- a claim the prior pass could only report as an unproven negative. Revenue remains overwhelmingly China + Hong Kong. Utilization sits near ceiling.

**What reverses.** First, **the mix is no longer a mobile story with a rounding-error server line.** DDR-series revenue share ran 20.16% -> 13.26% -> **31.87%** across FY2023-FY2025 while LPDDR ran 74.54% -> 82.74% -> **66.43%** (1-1-152, 1-1-214) [Grade B-filed]; DDR revenue grew RMB 3.174B -> RMB 19.531B, **+515% y/y** [Grade B-filed components; derived]. The superseded document's "LPDDR 69.74% / DDR 27.82%" 1H2025 split does not appear in the operative filing. Second, **CXMT is in server DDR5 mass production now, not on a 2027-2029 fuse.** The competitive product table at 1-1-147, stated as of 2025-12-31, marks CXMT at mass production across the entire server row -- DDR4 32GB and below, DDR4 above 32GB, DDR5 below 64GB, DDR5 64GB, DDR5 above 64GB -- matching Samsung, SK hynix and Micron on every cell, and ahead of Nanya, still in development on DDR5 64GB and above [Grade B-filed]. Third, **share roughly doubled.** Omdia FY2025 DRAM revenue share runs Samsung 33.96% / SK hynix 34.48% / Micron 23.41%, together above 90%; CXMT's own share "increased to 7.67%" on 4Q2025 DRAM revenue, **fourth globally and first in China** (1-1-26, 1-1-138) [Grade B-filed, Omdia-derived -- an analyst tally reproduced inside a filing, which does not make it a filed measurement]. The superseded reading carried 3.97% at 2Q2025; that figure does not appear in the operative document.

**The counter-case, not suppressed.** Three facts cut against the alarmist read. The entrant's own sell-through fell as it ramped: capacity utilization rose 87.06% -> 92.46% -> **95.73%** (FY2023-FY2025, 1-1-151) while the production-to-sales ratio on a capacity basis fell 99.45% -> 97.94% -> **90.67%** [Grade B-filed] -- roughly a tenth of FY2025 output went to inventory rather than to a customer, which is what a ramp outrunning its own demand looks like. ASP did the earnings work, not share: main DRAM product unit price moved **+55.08% (2024) and +33.69% (2025)** y/y (1-1-18) [Grade B-filed], and the issuer's own sensitivity table assumes 2026 average price BELOW the September 2025 actual (1-1-234). And the "raise buys no wafers" framing is too strong even where the no-greenfield finding holds: equipment purchase and installation is 62.22% of project 1's RMB 7.500B and 96.67% of project 2's RMB 18.000B, so roughly **RMB 22.1B of the RMB 34.5B program is tool purchase inside existing shells** [Grade B-filed components; derived]. Brownfield tools inside a built fab add bits. So does node migration at constant wafer count.

**Synthesis, rebuilt on the operative document.** The entrant is a conventional-DRAM competitor with **zero HBM presence** -- that half of the prior conclusion is confirmed by mechanical count and is the half that matters most for the HBM layer. But it is **not** a mobile-only story and **not** a 2027-2029 event: server DDR5 at 64GB and above is in mass production today, DDR is the fastest-growing line in the mix, and share went to fourth globally inside a year. The prior synthesis -- "the mix is mobile, not server", "not a 2026 server-DRAM event" -- rested on superseded 1H2025 figures and is **withdrawn**. The corrected read: the entrant pressures **conventional DRAM including its server tier**, on a horizon that has already started, and conventional DRAM is precisely the sub-layer that just out-earned HBM per wafer (Section 2). The closed-oligopoly critique (Section 1) therefore attaches to the conventional-DRAM layer with more force than this document previously allowed, and still does not transfer to HBM. Consequence for reading the rout: re-rating **HBM-levered** exposure on this IPO remains a correlation event; re-rating **conventional-DRAM-levered earnings** on it is not. The test is unchanged and still the right one -- whether HBM contract pricing moves, not whether the entrant's share moves -- but it now answers a narrower question than it was asked to answer.

### CXMT -- ChangXin Memory Technologies (Changxin Technology Group Co., Ltd.)

*All prospectus claims below: SSE `002170_20260517_MGLN.pdf`, retrieved 2026-07-15, Grade B-filed per the convention above. The 2025-12-30 filing previously cited here is SUPERSEDED and was not retrievable.*

#### Financial signals
- CXMT: capacity utilization 87.06% / 92.46% / 95.73%, FY2023-FY2025 (1-1-151)
- CXMT: production-to-sales ratio 99.45% / 97.94% / 90.67%, FY2023-FY2025, capacity basis (1-1-151)
- CXMT: FY2025 revenue mix LPDDR 66.43% / DDR 31.87% / other 1.70%; FY2024 LPDDR 82.74% / DDR 13.26% (1-1-152, 1-1-214)
- CXMT: FY2025 main-business gross margin 41.02% vs 5.00% FY2024, -2.19% FY2023 (1-1-219)
- CXMT: FY2025 net profit attributable to parent RMB 1.875B, first profitable year, vs -RMB 7.145B FY2024 (1-1-18)
- CXMT: China + Hong Kong 97.49% of FY2024 main-business revenue (domestic 29.34% + HK 68.15%) and 97.21% of FY2025 (domestic 42.79% + HK 54.42%) (geography table, 1-1-216) **[Grade B-filed components; derived** -- the totals are a derivation of two filed cells, and under this section's Chinese-language/table-read convention cannot be labelled "Grade A components; derived"**]**

#### Thesis Fit
Conventional DRAM only, and now including its server tier -- the layer where Samsung/SK hynix/Micron held above 90% share (Omdia FY2025: 34.48% SK hynix / 33.96% Samsung / 23.41% Micron, 1-1-26) [Grade B-filed, Omdia-derived]. **No HBM presence: zero mentions across 370 pages.** Its absence from the Section 1 HBM share row is CORRECT, not a defect. Its presence in the conventional-DRAM residual is now materially larger than this document previously carried.

#### Risks
- CXMT: global DRAM revenue share 7.67% on 4Q2025, fourth globally and first in China (1-1-138, 1-1-147) [Omdia-derived]. The superseded 3.97% (2Q2025) is not in the operative document.
- CXMT: server product table 1-1-147 marks mass production across DDR5 below 64GB, 64GB, and above 64GB as of 2025-12-31, matching Samsung/SK hynix/Micron and ahead of Nanya -- the fact that killed the "not a server event" reading
- CXMT: IPO proceeds fund three technology-upgrade and R&D projects, RMB 29.5B of a RMB 34.5B program, zero greenfield fabs, each affirmatively sited on existing land (1-1-30, 1-1-367 to 1-1-369); equipment purchase ~RMB 22.1B of that program [components; derived] -- brownfield tools, not R&D alone
- CXMT: capex (cash paid for fixed/intangible/other long-term assets) RMB 43.658B / 71.230B / 49.739B FY2023-FY2025, funded outside the raise; RMB 17.129B signed-but-unperformed long-term asset purchase commitments at FY2025 end (1-1-264, 1-1-266)
- CXMT: main DRAM ASP y/y +55.08% (2024), +33.69% (2025); issuer warns performance suffers if the cycle turns, and its sensitivity table assumes 2026 average price below the September 2025 actual (1-1-18, 1-1-234)

#### Catalysts
- CXMT: HBM mentioned ZERO times across the 370-page operative prospectus (mechanical count on extracted text, 2026-07-15) [Grade B-filed -- a mechanical count is a measurement of the document, not a quotation from it]
- CXMT: own DDR4 production ceased since end-2024, note 2 to the product tables at 1-1-147 and 1-1-148 [Grade B-filed -- **DOWNGRADED from an earlier Grade A.** The filing states this in Chinese; an English translation in a Grade-A slot is the paraphrase-hardened-into-citation failure this document exists to prevent. Substance confirmed at the named pages; only the grade moves.]
- CXMT: H1 2026 revenue guided RMB 110-120B (1-1-29) -- the near-term test of whether the DDR ramp holds
- CXMT: Entity List designation reportedly cleared interagency review but was held pending trade talks [Grade C]

#### Recent
- CXMT: Apple reportedly lobbied for assurance CXMT will NOT be added to the Entity List, to contract DRAM supply; Apple is not currently barred from buying (per FT via secondary, 2026-06) [Grade C -- FT primary not retrieved. Framing this as a waiver request is WRONG: the ask is forward-looking non-designation assurance.]

PERISHABLE -- series: CXMT STAR IPO pricing, as of 2026-07-15. REFETCH BEFORE USE; DO NOT INHERIT. Reported RMB 8.66/share, ticker 688825, subscription 2026-07-16 [Grade C].

### YMTC -- Yangtze Memory Technologies (Yangtze Memory Technologies Holding Co., Ltd.)

#### Financial signals
- YMTC: global NAND share 11.8% in 2025 (per UBS via Reuters); a separate reading of ~13% (Q1 2026, up from an 8% Q1 2025 base) is sourced to Counterpoint Research via TechNode, 2026-06-22 [Grade C -- ANALYST ESTIMATE, twice-relayed, not a disclosure; 11.8% and ~13% are different bases (2025 full-year vs Q1 2026), so treat them as a range, not one figure.]
- YMTC: two Wuhan fabs at ~200K wafers/month; three further fabs at 100K wpm each would reach ~500K wpm (per Reuters via secondary, 2026-04) [Grade C]
- YMTC: Phase 3 operations expected late 2026, ramping to ~50K wpm by 2027 [Grade C]

#### Thesis Fit
NAND, not DRAM and not HBM: the storage layer, not the memory-bandwidth bottleneck. Its expansion is the primary structural risk to NAND pricing durability on a 2027-2029 fuse. NAND share figures are analyst estimates BY CONSTRUCTION -- YMTC files no 10-Q equivalent and has no prospectus yet -- so every share figure here caps at Grade B/C until a STAR filing lands.

#### Risks
- YMTC: on the BIS Entity List since December 2022 [Grade B]
- YMTC: >50% of Phase 3 tooling domestically sourced; overall domestic-tool adoption ~45%, highest of any Chinese fab [Grade C]. Phase 3 tests whether Chinese tools sustain 3D NAND yield at volume; if it passes, the export-control lever loses force on NAND.

#### Catalysts
- YMTC: pre-IPO tutoring filing accepted by the CSRC Hubei bureau 2026-05-19 (CITIC + China Securities as tutors); first progress report 2026-07-10 [Grade B]. CSRC rules set tutoring at 3-12 months, so acceptance is possible from ~August 2026; submission, inquiry, listing-committee review and registration all still follow.
- YMTC: company target ~15% global NAND share by end-2026; Yole projects 15% only by 2028 [Grade C]. That two-year gap IS the honest state of this number -- never report the target as a forecast.

#### Recent
- YMTC: Wuhan Xinxin withdrew its STAR application the same day as the tutoring filing, consistent with a shift from spin-off to group-level listing [Grade C]

## 8. Portfolio application -- decision framework

This section is CITED BY ORDINAL from outside this document. **It carries THREE independent numbered series that must never be collided:**

| Series | Ordinals | Canonical label to use in every citation | Known external citers |
|---|---|---|---|
| **A** | 1-5 | **"structural exit criterion N"** | four sites in *ref-portfolio-doctrine* (not published); a ratified decision record; a live challenge document |
| **B** | 1-4 | **"rotation signal N"** | the doctrine's signal-vocabulary repair targets rotation signal 4, NOT structural exit criterion 4 |
| **C** | 1-2 | **"rotation sequence step N"** | cited as "the Section 8 sequence" by `ref-portfolio-doctrine.md:169` and `decision-theme-alpha-concentration-doctrine-2026-06-08.md:34`, which have no other referent |

"Structural exit criterion 4" (training-efficiency breakthrough), "rotation signal 4" (CoWoS utilization) and "rotation sequence step 2" (mid-layer before bottleneck-layer) are three different objects with three different owners. **The bare word "criterion" WOULD be ambiguous across series A and B, and the bare word "sequence" is the only handle series C has.** Every external citer was checked: they use "criterion" exclusively for series A (`ref-portfolio-doctrine.md:163`, `:169`; challenge `:49`) and "signal" for series B (coherence decision `:100`). The ambiguity is latent, not realized -- which is the reason to keep the labels, not a reason to relax them. Every external reference must name the series, not just the ordinal. Renumbering, merging, splitting or reordering any of the three silently breaks four doctrine sites, a ratified decision, and a live challenge -- **and nothing in the system detects prose section-number rot.**

**Full document-wide ordinal inventory** (three more series share these ordinal ranges and none is a Section 8 series): Section 4's **panel rows** (1-4); Section 6's **cycle-peak signals** (1-6); and Section 1's **layer column** (1-10), which is unlabelled and is the sixth series -- external citers reference the layers by name, not by number (`ref-portfolio-doctrine.md:147`), so its collision risk is latent rather than live; either label it or strip the `#` column at the next structural pass. "Signal 4" resolves to a different object in each of four series.

**Exposure is read at run time, never from this document.** A book running this doctrine uses a dual basis -- an EFFECTIVE reading (hyperscalers half-weighted, thematic infrastructure funds excluded) and a STRICT reading (all constituents full-weight) -- and the two can straddle the same doctrine line. Pull both from the broker at regular-market close before any threshold math. The bands live in *ref-portfolio-doctrine* (not published): theme-alpha tiered 60% amber / 70% red with an interim 50% amber phase-in, single-name 30/35 on combined value. This document supplies the rotation logic; the doctrine supplies the thresholds.

**The doctrine-compliant answer to elevated theme-alpha exposure is not a mechanical cut.** It is to reclassify exposure by layer correlation and rotate into layers that decorrelate under stress. Hyperscaler positions in a theme-alpha book overlap the thesis but decorrelate partially -- ad, retail and enterprise revenue diversifies cashflow regardless of the AI outcome [Grade C, structural inference].

**Rotation sequence (series C; ordinals 1-2; the referent for external "Section 8 sequence" citations):**
1. **Rotation sequence step 1: trim hyperscaler overlap before trimming pure-infra.**
2. **Rotation sequence step 2: trim mid-layer overlaps (e.g. AMD alongside NVDA) before trimming bottleneck-layer positions.**

**Correlation under stress:** in the 2022-H2 decline NVDA/AMD/MU moved together at -50% or worse while MSFT/AMZN/GOOGL fell roughly 30%; VRT decoupled on backlog, DLR acted as a partial bond proxy [Grade C, retrospective price history]. Under stress NVDA ~= AMD ~= MU in direction and magnitude.

### Layer construction targets

Per-layer target weights are set in the doctrine and read at run time.

**Construction-target status:** these per-layer sizes are **CONSTRUCTION TARGETS for building a diversified theme-alpha allocation -- NOT risk-flag escalation triggers.** The only hard doctrine flags are the single-name 30/35 ceiling and the theme-alpha 60/70 cap with its interim-50 phase-in, per *ref-portfolio-doctrine* (not published). The superseded target's attached memory-layer P/B condition is long breached and is dead as a trigger; the P/B read now sits an order of magnitude outside the 5-year range, which makes it a cycle-position observation, not a sizing rule.

> **PERISHABLE -- series: MU P/B (ratio, price-to-book). Reading 11.02 vs 5-year range 1.26-2.53, as of 2026-07-15. REFETCH BEFORE USE; DO NOT INHERIT.** (Grade C -- system-internal computation, not a filed figure.)

### Rotation signals (series B; ordinals 1-4)

1. **Rotation signal 1 -- NVDA data-center gross margin and sequential growth**: the compute-bottleneck-intact tell. Rotation-out signal is GM compression in the bottleneck name while the next layer's backlog accelerates. REFETCH at each print.
2. **Rotation signal 2 -- WFE spend guidance**: the equipment-bottleneck tell, currently HBM-driven. REFETCH at LRCX/AMAT prints.
3. **Rotation signal 3 -- VRT book-to-bill and backlog**: power-bottleneck tightening or loosening. REFETCH at each print.
4. **Rotation signal 4 -- CoWoS UTILIZATION** (kind-changed 2026-07-15; formerly a capacity target). **Be explicit about what is knowable: TSMC discloses capacity direction and capex, never utilization. Any utilization figure is a third-party estimate, and for this series Grade C is the CEILING, not a floor** -- the chain is TrendForce relaying Economic Daily News relaying unnamed institutional investors, which is why Section 4 states categorically that no better grade exists for it. The usable proxy is the supply-demand gap: "the CoWoS supply-demand gap is expected to narrow significantly from around 20% currently to about 10% by the end of 2026" (Grade C -- verbatim wording, but an estimate relayed through two intermediaries; Source: TrendForce, 2026-06-15). A narrowing gap is the packaging-bottleneck rotation-out signal. **Capacity is retained as CONTEXT, not as the signal:** "TSMC's monthly CoWoS capacity could reach a record 120,000 to 140,000 wafers in 2026" plus 50,000-60,000 OSAT wafers (**Grade C -- DOWNGRADED from Grade B this pass:** the capacity figure carries the SAME relayed attribution chain as the gap and is not TrendForce's own estimate, so Section 4's document-wide C-ceiling binds it too. TrendForce's own contribution in that release is the separate 2027-moderation forecast. Source: TrendForce, 2026-06-15). **Changed-value flag:** the predecessor carried 120,000-130,000; the upper bound moved to 140,000 with no change note. A capacity target says nothing about whether the capacity is absorbed; only the gap does.

### Hyperscaler earnings protocol -- July 2026 cycle

Live dates: **GOOGL 7/22**, **MSFT + META 7/29**, **AMZN 7/30 (tentative)**. Grade A -- verbatim: "Alphabet Inc. (NASDAQ: GOOG, GOOGL) will hold its quarterly conference call to discuss second quarter 2026 financial results on Wednesday, July 22, at 1:30pm Pacific Time (4:30pm Eastern Time)." (Source: Alphabet Investor Relations, 2026). META confirmed for 7/29 after close (Grade B, Source: Meta IR via StockTitan, 2026); MSFT 7/29 fiscal-Q4 (Grade B, Source: Microsoft Investor Relations, 2026); AMZN 7/30 unconfirmed at time of writing (Grade D).

**The raw-dollar capex threshold is DELETED:** a trigger reading "any revision below $X = trim signal" is sign-inverting on the live scenario, because DRAM deflation cuts capex dollars with unit demand unchanged and would fire an AI-infrastructure invalidation on a memory-margin event. The asymmetry between the two quantifying issuers is itself the finding:

- **META -- filed, and re-confirmed verbatim this pass.** The 8-K Ex-99.1 states: "We anticipate 2026 capital expenditures, including principal payments on finance leases, to be in the range of $125-145 billion, increased from our prior range of $115-135 billion. This reflects our expectations for higher component pricing this year and, to a lesser extent, additional data center costs to support future year capacity." [Grade A] (Source: META Form 8-K Ex-99.1, accession 0001628280-26-028364, 2026-04-29). Note what the filing does NOT say: the phrase "particularly memory" belongs to Amazon's Jassy on a call and must never be cross-attributed. Meta attributes the RAISE to price, never the price content of the LEVEL.
- **MSFT -- call-only, and proven ABSENT from the filed 8-K.** Verbatim from the FY26 Q3 call: "For calendar year 2026, we expect to invest roughly $190 billion in capital expenditures which includes approximately $25 billion from the impact of higher component pricing" (Source: Microsoft IR, FY26 Q3 call transcript, 2026-04-29). **Grade B, and deliberately so:** the quotation is verbatim from a company primary, but the filed Ex-99.1 read end to end carries no capex guidance and zero occurrences of "component" or "pricing" (Section 3 establishes the absence). Guidance living only on a call sits outside filing liability and is re-cuttable without a filed correction -- verbatim-ness does not promote it.
- **GOOGL -- also call-only, and proven ABSENT from the filed 10-Q and Q1 2026 earnings 8-K.** The 10-Q's only capex-forward language is qualitative: "In 2026, we expect to significantly increase, relative to 2025, our investment in our technical infrastructure, including servers and network equipment and data centers." (Source: GOOGL Form 10-Q, accession 0001652044-26-000048, period ended 2026-03-31). No dollar figure and no Intersect-driven raise appears in either filed document -- the 10-Q or the Q1 2026 earnings 8-K Ex-99.1 (accession 0001652044-26-000043, 2026-04-29) [Grade B -- call-only].

**Replacement condition (units-vs-price decomposed, per Section 3):** a capex revision advances a rung only when the decomposition shows **UNIT** (wafer, rack, megawatt) demand falling. A revision explained by component-price movement does not advance any rung in either direction. **Where the decomposition is unavailable, the rung does not advance.** Per name, the qualitative tells remain: cloud-segment growth rate, backlog direction, and whether management attributes the capex delta to capacity or to price. META remains the cleanest tension case -- it has no hyperscale customer-revenue layer to monetize the infrastructure against and must ship AI products directly [Grade C, structural].

### Structural exit criteria (series A; ordinals 1-5) -- thesis-invalidating, as distinct from cyclical sell signals

1. **Structural exit criterion 1:** Four consecutive quarters of hyperscaler aggregate capex cuts measured on **REPORTED ACTUAL SPEND, not forward guidance** (2027 signal at earliest).
2. **Structural exit criterion 2:** OpenAI + Anthropic combined ARR plateau at $60B or below for two consecutive quarters (would indicate end-revenue insufficient to clear infrastructure). **Evidence refreshed:** Anthropic states "our run-rate revenue crossed $47 billion earlier this month" (Grade A -- verbatim, Source: Anthropic, 2026-05-28); OpenAI is reported near a $25B annualized run rate mid-2026 (Grade C -- secondary, no primary disclosure; OpenAI's S-1 is confidential and its figures unaudited). Combined ~$72B on those readings, above the $60B line and rising, not plateauing. Run-rate is a monthly figure annualized and overstates during rapid growth -- the criterion requires **two consecutive quarters**, which is what defends it against a single distorted print.
3. **Structural exit criterion 3:** Taiwan kinetic disruption (binary tail).
4. **Structural exit criterion 4:** Technology breakthrough in training efficiency reducing compute needs 10x (no such breakthrough exists at frontier scale; MoE and test-time-compute argue the other direction).
5. **Structural exit criterion 5:** Severe regulatory action -- US or EU legislation materially restricting AI model deployment.

**Why structural exit criterion 1 is measured on actuals.** Reported actuals lag guidance by roughly 1-2 quarters. That lag is the point, not a defect: this is deliberately the harder bar, because a guidance-based rung compels only a review, while this criterion triggers **automatic rotation**. A trigger with automatic consequences must sit on the least-revisable evidence available.

**Exit-ladder linkage:** structural exit criterion 1 (four consecutive quarters of hyperscaler aggregate capex cuts measured on REPORTED ACTUAL SPEND, not forward guidance) is the DEFENSIVE auto-revert trigger in the *ref-portfolio-doctrine* (not published) Exit Ladder -- revert theme-alpha toward the doctrine band via managed rotation into a diversified index ETF. Earlier capex-cut signals map to that ladder's AMBER escalations (3 of 4 hyperscalers cutting guidance in a single quarter; or 2 consecutive quarters of cuts -> arm + /decide review). The OFFENSIVE harvest legs reuse the rotation signals (series B) + the rotation sequence (series C) above. **The two systems are ONE escalation, not parallel; capex DECELERATION (positive, slowing) is the offensive harvest signal, capex CUTS (negative) are the defensive health signal.**

### Hedging and pair-trade candidates

Short-side pure-play theme-alpha expression is thin; pair trades express rotation with less net sector exposure. The structurally motivated pairs are **long power / short compute** (captures the constraint migrating from packaging toward grid and electrical, where backlog gives 12-18 months visibility) and **long leading-edge equipment / short lagging foundry** (captures WFE strength against foundry share loss). Protective puts on the bottleneck name are the direct hedge; their cost-effectiveness is a function of implied vol at the time and must be priced at run time, never from this document. No strike, premium or expiry is recorded here.

*Conclusion.* The operating claim is unchanged: one layer binds at a time, the bottleneck name compounds fastest until the constraint rotates, and the sequence for reducing exposure is hyperscaler-overlap first, mid-layer second, bottleneck-layer last. The telecom precedent Section 3 owns -- an 89% CSCO drawdown and a 25-year recovery -- is not a prediction; it is the discipline that justifies why the invalidation bar is set high and measured on REPORTED ACTUAL SPEND, and why the harvest signal and the health signal are one ladder rather than two.

## Related

*investing-moc* (not published) | *thesis-theme-alpha* (not published) | [[ref-macro-landscape]] | *ref-sector-benchmarks* (not published) | [[ref-scoring-models]] | *ref-portfolio-doctrine* (not published) | [[ref-monitoring-rules]] | *nvda-analysis* (not published) | *amd-analysis* (not published) | *mu-analysis* (not published) | *dtcr-analysis* (not published) | *msft-analysis* (not published) | *amzn-analysis* (not published) | *AVGO* (not published) | *VRT* (not published) | *ANET* (not published) | *MRVL* (not published) | *CSCO* (not published) | *ETN* (not published) | *ABB* (not published) | *KLAC* (not published) | *ASML* (not published) | *TSM* (not published) | *DLR* (not published) | *EQIX* (not published) | *GEV* (not published) | [[ref-theme-alpha-ingest-2026-04-22]] | *ref-ai-supply-chain-deep-dive* (not published) | *ref-memory-storage-cycle-deep-dive* (not published) | [[ref-ai-power-grid-deep-dive]]

## Sources

Inline `(Source: ...)` citations throughout; this is the deduped bibliography.

1. SK hynix Form F-1/A, accession 0001193125-26-295501, CIK 2120882, filed 2026-07-06
2. TrendForce 20260601-13070, 2026-06-01
3. SK hynix F-1/A, 2026-07-06
4. SK hynix F-1/A, 2026-07-06; ellipses elide defined-term parentheticals
5. TrendForce, 2026-06-01
6. ASML Form 6-K, accession 0001628280-26-048235, 2026-07-15
7. TrendForce 20260602-13074, 2026-06-02
8. TrendForce, 2026-06-02
9. MU 10-Q Item 1A, accession 0000723125-26-000015, filed 2026-06-25
10. SEMI 300mm Fab Outlook 2Q26, 2026-06-29
11. CNBC, 2026-04-29
12. META Form 8-K Ex-99.1, accession 0001628280-26-028364, 2026-04-29
13. Microsoft IR, FY26 Q3 call transcript, 2026-04-29
14. MSFT Form 8-K Ex-99.1, accession 0001193125-26-191457, 2026-04-29
15. Nebius Q1 2026 call, 2026-05-13
16. SEC XBRL company facts, us-gaap:NetCashProvidedByUsedInOperatingActivities, retrieved 2026-07-15
17. SEC XBRL company facts, us-gaap:PaymentsToAcquirePropertyPlantAndEquipment / PaymentsToAcquireProductiveAssets / FinanceLeasePrincipalPayments, retrieved 2026-07-15
18. FRED series GDP, retrieved 2026-07-15
19. TrendForce, 2026-06-15
20. MU Form 8-K Ex-99.1, accession 0000723125-26-000013, filed 2026-06-24
21. stockanalysis.com per-ticker statistics page, retrieved 2026-07-15
22. [[ref-valuation-methodology]] Section 6, citing Damodaran 2009
23. Epoch AI, "Hyperscaler Capex vs Cash Flow", 2026
24. Epoch AI, "Hyperscaler capex has quadrupled since GPT-4's release", 2026
25. Anthropic, Series H announcement, 2026-05-28
26. Sacra, 2026
27. BIS press release, 2026-01
28. Alphabet Investor Relations, 2026
