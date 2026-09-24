---
categories: [sources]
type: reference
target_path: Atlas/sources/investing/ref-macro-landscape.md
created: 2026-04-05
updated: 2026-08-24
status: active
confidence: medium
tags:
  - topic/macro
  - topic/fed-policy
  - topic/inflation
  - topic/rates
  - topic/fiscal
aliases:
  - macro landscape
  - macro regime primer
related:
  - "*investing-moc* (not published)"
  - "*ref-portfolio-doctrine* (not published)"
  - "[[ref-regime-taxonomy]]"
  - "[[ref-monitoring-rules]]"
  - "*ref-market-calendar* (not published)"
  - "*ref-sector-benchmarks* (not published)"
  - "*ref-geopolitical-framework* (not published)"
  - "[[ref-evidence-hierarchy]]"
  - "[[ref-briefing-structure]]"
  - "[[ref-theme-alpha]]"
  - "*ref-ai-supply-chain-deep-dive* (not published)"
  - "[[ref-ai-power-grid-deep-dive]]"
  - "*ref-theme-beta-institutional-crypto-deep-dive* (not published)"
  - "*ref-defense-aerospace-space-economy-deep-dive* (not published)"
  - "*geopolitics-playbook* (not published)"
  - "*macro-outlook* (not published)"
---

# Macroeconomic Landscape Reference

1. Current macro regime classification
2. The Federal Reserve under Chair Kevin Warsh
3. Inflation
4. Labor market
5. Economic growth
6. Yield curve and fixed income
7. Equity market positioning
8. Sector rotation and relative strength
9. Global macro and geopolitical
10. Fiscal policy and government
11. Thematic macro trends
12. Risk matrix
13. Scenarios (bull / base / bear)
14. Macro-to-portfolio transmission map
15. Fed policy plumbing (GENERATED from the vault factor store)
16. Yen and global carry (GENERATED from the vault factor store)
17. Rates complex, store-computed expansion (GENERATED)
18. Credit, store-computed expansion (GENERATED)

## 1. Current macro regime classification

Class definitions are owned by [[ref-regime-taxonomy]]; this section states the live READ only.

### Late-cycle vs Mid-cycle, resolved

**Mid-cycle**, matching the live briefing's `macro_regime: Mid-cycle` (Source: briefing-2026-07-14) and superseding the predecessor's "Late-cycle with stagflationary overlay". The taxonomy names five cycle-phase diagnostics -- 10Y-3M, unemployment trend, HY OAS, PMI, LEI. **Four were checked this pass; the fifth, LEI, was NOT scored.** All four checked read Mid and none reads Late: the curve sits in the Mid band (50-150bp), not the Late band (under 50bp); HY OAS is tight, not "widening from tight"; the ISM manufacturing composite prints above 50, inside the Mid band; unemployment is near its cycle low with the real-time Sahm indicator falling. The tally is **4-of-4-CHECKED, not 4-of-5**. Grade B inputs (per the owning blocks); Grade D on the aggregate call.

**LEI: NOT SCORED, stated rather than implied.** The Conference Board LEI 6-month annualized rate was not retrieved or scored against the taxonomy's "flat positive" (Mid) vs "flat or turning negative" (Late) bands this pass. If a refresh scores LEI Late, the tally becomes 4-1 and the Mid call weakens without breaking; if Mid, it strengthens (Grade D, absence).

Two reusable error classes produced the superseded call and both recur. **Falsified premise:** it rested on the now-dead Iran/Hormuz oil shock (Section 9) -- a classification does not outlive its load-bearing input. **Category error:** it read "inflation is high" as "the cycle is late," but the taxonomy's phase table has no inflation column; phase and inflation are ORTHOGONAL axes, and "stagflationary" additionally requires deteriorating growth and labor, which is absent. (Grade D)

### Six axes, each with its flip condition

| Axis | Live classification | Grade | Observation that flips it |
|---|---|---|---|
| Cycle phase | Mid-cycle | D | Any ONE of: 10Y-3M under 50bp; HY OAS over 350bp; ISM under 50; Sahm >= 0.50 |
| Growth | At trend; re-accelerated off the Q4-2025 trough | B | Two consecutive sub-1% real GDP quarters, or a Sahm trigger |
| Inflation | Reflation -- core above target, re-accelerating | B | Three consecutive core PCE prints <= 0.17% MoM (the 2%-annualized pace) |
| Monetary policy | Restrictive, on hold, hawkish bias | B | A cut delivered, or the June SEP hike dots clearing |
| Market | Divergent (Source: briefing-2026-07-14) | B | Cross-asset coherence resolving either way |
| Liquidity | Ample but structurally thinning; easing at the margin | D | TGA rebuild after the debt-ceiling X-date (Section 10) |

The liquidity axis is the one most often reasoned backwards. Net liquidity has been RISING: the TGA drained across four Wednesday levels against a flat balance sheet, and ON RRP is a dead term. "QT ended, therefore liquidity is tight" has the marginal sign wrong. Section 6 owns the composite, its specification defects and its correct construction. (Grade D)

Growth at trend and tight credit are Mid-cycle facts; core inflation re-accelerating against a Fed carrying hike dots is not -- hence divergent coherence, and `confidence: medium` as the honest document-level value.

```
PERISHABLE -- POINTER TABLE. REFETCH BEFORE USE; DO NOT INHERIT
This section states NO level it does not solely own. Every diagnostic below resolves
against a live pull of the named series, in the block that owns it. One series, one
owning block, one as-of stamp.

Series / diagnostic          Owning block   Role in the Mid-cycle tally
BAMLH0A0HYM2  HY OAS         Section 6      credit-band check (tight, not widening)
ISM Mfg PMI + Employment     Section 5      PMI band check (above 50) + the verbatim
                                            Grade-A ISM release quotation
UNRATE                       Section 4      unemployment-trend check
SAHMREALTIME                 Section 4      Sahm trigger (threshold 0.50)
GDPC1 (pca)                  Section 5      growth-axis check
PCEPILFE (pc1)               Section 3      inflation-axis check
WALCL / WDTGAL / RRPONTSYD   Section 6      liquidity-axis check
DFEDTARU / DFEDTARL          Section 2      policy-axis check

SOLELY OWNED BY THIS SECTION -- as of 2026-07-15 (FRED):
T10Y3M          +0.72        2026-07-15   Mid band 50-150bp; Late band under 50bp
Conference Board LEI          NOT RETRIEVED this pass -- score before use
```

## 2. The Federal Reserve under Chair Kevin Warsh

### The evidentiary base

Kevin Warsh was confirmed as Chair on 2026-05-13 by a recorded 54-45 vote (Record Vote 120, 119th Congress 2nd Session) on the question "On the Nomination (Confirmation: Kevin Warsh, of Florida, to be Chairman of the Board of Governors, Federal Reserve Board)", nomination PN855-1, with 1 not voting [Grade A] (Source: U.S. Senate roll-call vote 120, 2026-05-13). He took office 2026-05-22, succeeding Jerome Powell, who remains on the Board as a Governor [Grade B] (Source: Federal Reserve Board membership table, updated 2026-05-28).

**Warsh has given zero speeches as Chair.** The Board's 2026 speech index runs 2026-01-07 to 2026-07-15 and lists entries by Powell, Bowman, Waller, Barr, Cook, Jefferson and Miran -- and none by Warsh [Grade B] (Source: federalreserve.gov 2026 speech index, retrieved 2026-07-15 and again 2026-07-16). **The entry COUNT is not reproducible and is therefore not stated:** three retrievals of the same page returned three different totals (51, 53, 58), so any specific count here would be a number no verifier could reproduce. What DOES reproduce on every retrieval is the load-bearing fact -- zero Warsh entries and the same seven speakers.

His entire public reaction-function record as Chair is three documents: the 2026-06-17 FOMC statement, the 2026-06-17 press conference, and the Semiannual Monetary Policy Report testimony of 2026-07-14 (House Financial Services) and 2026-07-15 (Senate Banking). **The thinness of that base is itself the finding:** any characterization of Warsh beyond those documents is inference about a person, not evidence about a reaction function, and a consuming model must not upgrade the former into the latter. This claim expires the moment he speaks; re-check the speech index before relying on it.

### The reaction function: two axes that diverge

**Warsh reads CONSTRUCTIVE on AI capex and HAWKISH on rates.** These are separate axes; a model that collapses them into a single "Warsh is hawkish" gradient will mis-price AI-infrastructure exposure.

On rates, from the **2026-07-14 Semiannual Monetary Policy Report testimony** [all Grade A; ASCII substitution applied to the source's em-dash] (Source: Warsh testimony, federalreserve.gov, 2026-07-14):

- "The members of our Committee have no tolerance for persistently elevated inflation."
- "This was the focus of our June meeting, at which we decided to hold the target range for the federal funds rate at 3-1/2 to 3-3/4 percent."

On AI capex, **same testimony document, same authority** [Grade A]:

- "The rapid pace--which appears to be accelerating--reflects, in large part, the construction of data centers and the immense demand for the AI-related equipment and software that fill them."
- "Investment in equipment overall increased about 8 percent for the year ending in the first quarter. Within that category, high-tech spending logged an especially impressive growth rate of nearly 25 percent on a four-quarter basis."

On the balance sheet, **same testimony**: "The second task force will review the Fed's balance sheet policies, including the ample-reserves regime and the composition of asset holdings." [Grade A]. Those are the five 2026-07-14 quotations. **Anti-collision:** the sixth Grade-A Warsh string in this document comes from a DIFFERENT primary at a different URL -- the **2026-06-17 press-conference transcript**, cited in Section 13, not here. The two documents must never be merged into one citation.

The tone difference is the signal: "no tolerance" is prohibitive language about inflation; "immense demand" and "especially impressive" are descriptive-positive language about the capex cycle. Warsh is not treating AI investment as an inflationary excess to be suppressed [Grade D, inference from tone].

The 2026-06-17 statement was declarative rather than data-dependent -- "The Committee will deliver price stability" -- and passed 12-0 with no dissents [Grade B] (Source: FOMC statement, 2026-06-17). That sentence departs from the Powell-era "carefully assess incoming data" construction and is the strongest hawkish tell in the record.

### The pre-chairmanship record, and a correction

Warsh's long-standing written position separates the two instruments: "There are two monetary policy instruments. One is setting of interest rates...the other...we call it QE, we call it the Central Bank's balance sheet," and a quieter balance sheet buys lower policy rates -- "If we would run the printing press a little quieter, we could then have lower interest rates" -- an approach he labels "practical monetarism" [Grade B; ellipses in source; interview recorded 2025-05-28] (Source: Hoover Institution, "Inflation Is a Choice: Kevin Warsh on Fixing the Federal Reserve", 2025-07-08). This makes the balance-sheet task force the higher-information item: a balance-sheet hawk who is a rates dove on the same theory is coherent, and it is the one lane in which Warsh could ease without abandoning "no tolerance."

**Correction to a widely-repeated claim:** Warsh cast **no formal dissent** during his 2006-2011 Governor tenure. He voted for QE2 while objecting in deliberations and in a November 2010 op-ed [Grade C] (Source: Wikipedia, Kevin Warsh, retrieved 2026-07-15). Citing "Warsh's Governor-era dissents" as evidence of hawkishness is a factual error; he dissented rhetorically while voting with the Committee -- weaker evidence of hawkish behavior under institutional pressure, not stronger.

### June 2026 SEP

The 2026 median fed funds projection moved from **3.4% (March) to 3.8% (June)** -- a hawkish revision [Grade B -- primary-table retrieval from the SEP, no quoted prose] (Source: FOMC Summary of Economic Projections, Table 1, 2026-06-17).

The 2026 dot distribution, all 18 participants: 3.375% (1), 3.625% (8), 3.875% (3), 4.125% (5), 4.375% (1) [Grade B -- HTML table-cell read, not prose; the dots render as chart geometry in the PDF view, but the underlying Figure 2 HTML table publishes each 2026 count as text]. **The top dot's level is RESOLVED:** a direct HTML read of the primary table (not a rendering/summarization pass) confirms the top 2026 dot is 4.375% with 1 participant; the 4.500% row has zero 2026 participants (it is populated only for 2027, where it carries 1) (Source: FOMC Summary of Economic Projections, Table/Figure 2 dot-plot, fomcprojtabl20260617.htm, retrieved 2026-07-16) [Grade B -- HTML table-cell read]. The earlier UNRESOLVED disclosure -- two independent retrievals returning 4.375% and 4.500% -- traced to a fast-model summarization pass that misread the 4.500% row's 2027 count as a 2026 entry; the direct HTML table read refutes that misreading. Nothing downstream turned on the earlier ambiguity: the dot is above the current target range under either reading. The 3.375% low dot IS corroborated arithmetically -- without it, the 9th and 10th sorted dots both sit at 3.875%, publishing a 3.9% median rather than the published 3.8%.

Against the current 3.625% midpoint, **9 of 18 participants project a 2026 hike**, 8 project a hold, and 1 projects a cut [Grade B, arithmetic on the primary distribution; unaffected by the top-dot ambiguity]. June medians: core PCE 3.3%, headline PCE 3.6%, GDP 2.2%, unemployment 4.3%; longer-run fed funds 3.1% [Grade B -- primary-table retrieval; same source]. No Grade-A slot is claimed anywhere in this subsection: every figure is a table read, and a table read is not a quotation.

### Rate-cycle history (durable)

| Phase | Date | Change (bps) | Target Range |
|---|---|---|---|
| Hike 1 | Mar 16, 2022 | +25 | 0.25-0.50% |
| Hike 2 | May 4, 2022 | +50 | 0.75-1.00% |
| Hike 3 | Jun 15, 2022 | +75 | 1.50-1.75% |
| Hike 4 | Jul 27, 2022 | +75 | 2.25-2.50% |
| Hike 5 | Sep 21, 2022 | +75 | 3.00-3.25% |
| Hike 6 | Nov 2, 2022 | +75 | 3.75-4.00% |
| Hike 7 | Dec 14, 2022 | +50 | 4.25-4.50% |
| Hike 8 | Feb 1, 2023 | +25 | 4.50-4.75% |
| Hike 9 | Mar 22, 2023 | +25 | 4.75-5.00% |
| Hike 10 | May 3, 2023 | +25 | 5.00-5.25% |
| Hike 11 | Jul 26, 2023 | +25 | 5.25-5.50% |
| Hold | Sep 2023 - Jul 2024 | 0 (8 meetings) | 5.25-5.50% |
| Cut 1 | Sep 18, 2024 | -50 | 4.75-5.00% |
| Cut 2 | Nov 7, 2024 | -25 | 4.50-4.75% |
| Cut 3 | Dec 18, 2024 | -25 | 4.25-4.50% |
| Hold | Jan-Jul 2025 | 0 (5 meetings) | 4.25-4.50% |
| Cut 4 | Sep 17, 2025 | -25 | 4.00-4.25% |
| Cut 5 | Oct 29, 2025 | -25 | 3.75-4.00% |
| Cut 6 | Dec 10, 2025 | -25 | 3.50-3.75% |
| Hold | Jan 28, 2026 | 0 (vote 10-2) | 3.50-3.75% |
| Hold | Mar 18, 2026 | 0 (vote 11-1) | 3.50-3.75% |
| Hold | Jun 17, 2026 | 0 (vote 12-0) | 3.50-3.75% (Warsh's first meeting) |

Totals: 11 hikes (+525bp), 6 cuts (-175bp), net +350bp from zero. The dissent count falling 10-2 -> 11-1 -> 12-0 across the handover is durable and worth watching [Grade B; only the 12-0 count was verified at the primary statement, the other two are carried from the predecessor] (Source: FOMC statements, 2026-01-28 / 2026-03-18 / 2026-06-17).

### R-star (durable; all four models)

| Model | Neutral Rate |
|---|---|
| FOMC longer-run median (June 2026 SEP) | 3.1% (nominal) |
| Holston-Laubach-Williams (NY Fed; REAL rate) | ~0.90% REAL (2025Q2, current vintage); ~1.06% REAL (2026Q1, latest available) |
| Zaman (Cleveland Fed, nominal, Q2 2025) | ~3.7% (nominal) |
| Lubik-Matthes (Richmond Fed; REAL rate, Q1 2026, page updated 2026-06-10) | 1.74% REAL |

**Units note:** this table mixes real and nominal estimates. HLW and Lubik-Matthes publish REAL short-term neutral rates by each model's own definition; only the FOMC longer-run median and Zaman are nominal. The predecessor's ~2.84% HLW figure was an undocumented real-to-nominal conversion of a now-superseded (~0.84%) vintage of the real estimate; that conversion is dropped rather than carried forward. Do not compare a real HLW/Lubik-Matthes reading directly against the 3.625% NOMINAL policy midpoint without adding back an inflation-target adjustment (+~2%) first.

The FOMC row was re-verified against the June 2026 SEP: the longer-run median is 3.1%, and the SEP's own March-projection row also shows 3.1% -- the row is not stale [Grade B -- primary-table retrieval]. Zaman's nominal estimate is now Grade A, verbatim (Source: Cleveland Fed, Economic Commentary EC 2025-08, published 2025-09-02): *"As of 2025:Q2, the new model's estimate of the nominal neutral interest rate is 3.7 percent, with a 68 percent coverage interval spanning 2.9 percent through 4.5 percent."* Lubik-Matthes is corrected from the predecessor's unsourced ~4.2% to a verified 1.74% real, Grade A, verbatim (Source: Richmond Fed, "Natural Rate of Interest," page updated 2026-06-10): *"The median estimate for the Lubik-Matthes Natural Rate of Interest was 1.74 percent as of the first quarter of 2026."* At 1.74% real, Lubik-Matthes no longer reads as the accommodative outlier the predecessor claimed -- on a real-rate basis it reads restrictive against the 3.625% nominal midpoint, the same directional read as HLW's ~0.90-1.06% real. **With Lubik-Matthes corrected, the FOMC longer-run median, HLW, and Lubik-Matthes all read current policy as restrictive; only Zaman's nominal 3.7% sits near the current 3.625% stance.** No single r-star estimate can carry a policy inference, but the correction strengthens rather than weakens the restrictive-policy read that anchors the hawkish-Warsh thesis. [Grade B on the multi-model synthesis; HLW and Lubik-Matthes vintages independently re-verified 2026-07-16; Zaman promoted to Grade A this pass.]

### Balance sheet

QT ended December 2025 after removing roughly $2.4T from a ~$9T peak; Reserve Management Purchases of up to $40B/month in short-term Treasuries began December 2025 and are explicitly not QE; ON RRP has drained from a >$2.5T peak to effectively zero [Grade B, durable regime facts; the H.4.1 release and the December 2025 implementation note were not re-fetched this pass, so the citation is a category pointer rather than a retrieved document -- only the ON RRP near-zero level was independently confirmed] (Source: Federal Reserve H.4.1 / FOMC materials).

The consuming system's net-liquidity composite (`WALCL - RRP - TGA`) is mis-specified. **Section 6 owns that finding in full** -- correct construction, worked arithmetic, perishable legs -- and it is deliberately not restated here.

```
PERISHABLE -- REFETCH BEFORE USE; DO NOT INHERIT
as of 2026-07-15
FRED DFEDTARU / DFEDTARL: target range upper 3.75 / implied range 3.50-3.75 (2026-07-15)
Net-liquidity legs (WALCL, WDTGAL, RRPONTSYD): Section 6 block owns them.
Inflation series: Section 3 block owns them.
```

### Remaining 2026 FOMC meetings

**July 28-29 | September 15-16 (SEP) | October 27-28 | December 8-9 (SEP)** [Grade B] (Source: federalreserve.gov FOMC calendar, retrieved 2026-07-15). Calendar ownership sits with *ref-market-calendar* (not published); deployment bands and the regime halt sit with *ref-portfolio-doctrine* (not published). Nothing in this section authorizes a trade.

## 3. Inflation

### The inflation fight is not won

CPI accelerated from February through a May peak before partially retracing in June -- the series was rising, not declining (Grade B; Source: FRED CPIAUCSL, 2026-07-15). The durable method rule: CPIAUCSL, CPILFESL, PCEPI and PCEPILFE publish as INDEX LEVELS, and a year-over-year read requires the `units=pc1` transform. Reading an index level as a rate is the standard misread.

```
PERISHABLE -- REFETCH BEFORE USE; DO NOT INHERIT
as of 2026-07-15 (PCEPILFE re-pulled 2026-07-16). This block owns every inflation
level in this document; Sections 1, 2 and 12 point here rather than restating.

Measure                          FRED ID                 Transform  Latest      As of
Headline CPI YoY                 CPIAUCSL                pc1        3.46        2026-06
  (May peak 4.17; Feb 2.43)
Core CPI YoY                     CPILFESL                pc1        2.57        2026-06
  (range 2.47-2.82 since Jan)
Headline PCE YoY                 PCEPI                   pc1        4.07        2026-05
Core PCE YoY                     PCEPILFE                pc1        3.412       2026-05
  full pc1 path: Oct 2.755 | Nov 2.829 | Dec 2.971 | Jan 3.105 | Feb 3.049
                 Mar 3.254 | Apr 3.319 | May 3.412
Energy CPI YoY                   CPIENGSL                pc1        15.45       2026-06
  (May peak 22.97)
Food CPI YoY                     CPIUFDSL                pc1        2.99        2026-06
Median CPI, annualized MoM       MEDCPIM158SFRBCLE       lin        2.11        2026-06
  (Apr 4.93, May 3.66)
16% trimmed-mean CPI, ann. MoM   TRMMEANCPIM158SFRBCLE   lin        0.13        2026-06
  (Apr 5.23, May 3.18)
UMich 1-year expectations        MICH                    lin        4.8         2026-05
  (3.4 in Feb)
5y5y forward breakeven           T5YIFR                  lin        2.21        2026-07-15
WTI MONTHLY AVERAGE              DCOILWTICO              m avg      84.81 Jun   2026-06
  (May 102.13; Jan 60.04) -- this is the MONTHLY-AVERAGE construct.
  Section 9 owns the SPOT construct. Different constructs, both labelled.

DERIVED, equally perishable: core PCE minus core CPI = +84bp at these vintages
(3.41 May print less 2.57 June print). The legs are one month apart by construction
-- PCE lags CPI on the release calendar -- so this is an approximate cross-vintage
spread, not a same-month wedge. Recompute on every refetch; never inherit.
```

### The energy mechanism is not dead -- it is lagged

The claim that oil's reversal broke the energy mechanism rests on a vintage mismatch: it compares SPOT oil today against CPI prints from months when oil averaged far more. Monthly-average WTI peaked in May and headline CPI peaked in May; both fell in June, and energy CPI fell with them (Grade B; Source: FRED DCOILWTICO and CPIENGSL, 2026-07-15). Headline's round trip is an energy round trip, with core CPI never leaving a ~2.5-2.8 band throughout. Spot below the June average therefore implies further mechanical headline disinflation, absent a fresh energy shock. Energy is a level effect on headline, not a persistent core impulse (Grade D, inference).

### The real anomaly: the core PCE / core CPI wedge

**Core PCE sits materially ABOVE core CPI, inverting the normal sign** -- core PCE typically runs BELOW core CPI, largely on lower shelter weight and broader scope (Grade B; Source: BLS, "Differences between the CPI and the PCE Price Index"). The sign inversion is the durable finding; the magnitude is perishable and lives only in the block above.

**Trajectory.** Core PCE is rising in direction but WITHOUT an unbroken monthly streak -- one month in the last seven declined, so the run is broken and any "N consecutive months" phrasing is false [Grade B, arithmetic on the block above; FRED `PCEPILFE units=pc1`]. State the direction; compute the magnitude and the run length from the block, and inherit neither.

Core CPI has not shown the same drift. This points the pressure at components PCE prices but CPI does not weight comparably -- medical care, insurance and financial services (Grade D, inference; not independently confirmed -- a BEA Table 2.4.4U component pull would settle it). Core PCE is the Fed's target variable, so this wedge, not headline, is what a hawkish reaction function reads.

### Tariff pass-through: the live candidate mechanism

The NY Fed finding concerns IMPORT prices, not consumer prices. Verbatim: *"Given that the average tariff in December was 13 percent (see the first chart), our results imply that U.S. import prices for goods subject to the average tariff increased by 11 percent (13 times 0.86) more than those for goods not subject to tariffs."* (Grade A; Source: NY Fed Liberty Street Economics, 2026-02-12).

More is queued. Verbatim, re-fetched at source on 2026-07-15 [ASCII substitution applied to the source's em-dash]: *"That leaves 47 percent of service firms and 44 percent of manufacturers that paid tariffs directly saying they have more tariff-induced price increases to come--shown by the two shades of gold bars in the chart."* (Grade A; Source: NY Fed Liberty Street Economics, "More Tariff Pass-Through Is in the Pipeline", 2026-07-08). The pass-through builds *"over the better part of a year rather than all at once"* (Grade A, same source). This is a persistent core impulse and the leading explanation for core PCE's drift.

### The breadth lens and the anchoring frame

The Cleveland Fed median and trimmed-mean series carry a trap: `MEDCPIM158SFRBCLE` and `TRMMEANCPIM158SFRBCLE` are ANNUALIZED MONTHLY rates, not 12-month rates, and are correspondingly volatile -- April-May printed broad-based pressure, June collapsed (Grade B; Source: Cleveland Fed / FRED, 2026-07-15). Single months carry little signal; the 3-month average is the usable read. Their Apr-May spike indicates the surge was briefly broad, not purely outlier-driven -- median CPI does not prove the central tendency is near target.

Anchoring is two-tiered: near-term expectations are unanchoring (UMich 1-year has risen sharply since February) while 5y5y forward sits near its historical range, implying markets treat the impulse as transitory (Grade B; Source: FRED MICH and T5YIFR, 2026-07-15).

**What flips this read:** core PCE printing below 3.0 for two consecutive months (impulse fading); or 5y5y breaking above ~2.5 (medium-term anchor failing, the more consequential signal).

## 4. Labor market

Method and baseline follow; every level sits in the block below.

**Regime: low-hire, low-fire (Grade B, JOLTS via FRED).** Hires and quits sit near post-2020 lows alongside low layoffs -- the market is not shedding workers, it has stopped churning. A quits rate sustained below 2.0% signals workers do not believe outside options exist (Grade D -- interpretive mechanism claim, not a sourced finding). This is why weak hiring and a low unemployment rate coexist without contradiction, and why layoff-based recession signals stay quiet while the hiring rate does the deteriorating.

**PRESERVE -- the 2025 benchmark revision is the baseline for reading any 2026 print.** The annual benchmark cut March-2025 total nonfarm employment by -898,000 (-0.6%) and restated 2025 payroll growth from +584K to +181,000 for the year, roughly +15,000/month (Grade B: BLS CES national benchmark, released with the January 2026 data on 2026-02-11; bls.gov returned HTTP 403 to this fetcher, so this rests on secondary corroboration, not a retrieved quotation -- not Grade A). The consequence is mechanical: against a ~15K/month trend, a +150K print is a large upside surprise, not merely "solid". Section 11 owns the breakeven-employment figure, which the predecessor's ~75-90K/month no longer reliably represents.

**PRESERVE -- decompose U-3 before calling it good news.** The standard, kept as method: a U-3 decline came "partly on a 396,000 decline in labor force -- not robust hiring." The pattern recurs in the latest print, where U-3 fell while the labor force contracted and both headline and prime-age participation dropped (Grade D inference; the arithmetic is below, the interpretation is not). U-3 falling on a shrinking denominator is a labor-supply event, not a labor-demand event, and is never strength. Standing diagnostic: prime-age at or above pre-pandemic levels alongside a depressed headline rate is demographic aging, not discouragement.

**Openings-per-unemployed.** JTSJOL / UNEMPLOY on matched vintages: near 1:1 balance, above ~1.2 tight, below 1 slack. Compute from the block; never carry a stale ratio. **Sahm rule:** threshold 0.50pp on SAHMREALTIME; re-read status every run, never inherit it.

**Wage-series discipline (Grade B, FRED series definitions).** Use CES0500000003 (all private employees, 2006+), the Employment Situation headline, for wage-inflation work; AHETPI covers production and nonsupervisory workers only (1964+), a different population with a longer history. A rule calibrated on one is not valid on the other; every wage claim must name its series.

**AI displacement.** Brynjolfsson, Chandar and Chen (Stanford Digital Economy Lab, ADP payroll microdata; version dated 2025-11-13). Two consecutive sentences from the abstract, quoted verbatim [Grade A; publication page retrieved 2026-07-16]:

- *"We find that since the widespread adoption of generative AI, early-career workers (ages 22-25) in the most AI-exposed occupations have experienced a 16 percent relative decline in employment even after controlling for firm-level shocks."*
- *"In contrast, employment for workers in less exposed fields and more experienced workers in the same occupations has remained stable or continued to grow."*

Both sentences are reproduced exactly; a Grade-A slot admits only a string that exists at the source, and a paraphrase inside quotation marks is the same failure class as a fabricated filing clause.

**FIX:** the vault credits this finding to "Stanford/Deutsche Bank" -- Deutsche Bank is not an author and the underlying data are ADP's; drop that attribution. Tufts Digital Planet's American AI Jobs Risk Index puts 9.3M US jobs vulnerable on a median adoption path (range 2.7M-19.5M) over two to five years (Grade C -- a model projection, not observed displacement, and sourced from search summaries rather than a direct fetch of the Tufts page); the 2027-2030 concentration of effects remains forecast (Grade D). None of this is visible in aggregate payrolls yet; it is a composition story inside them.

```
PERISHABLE -- REFETCH BEFORE USE; DO NOT INHERIT
Retrieved 2026-07-15 via FRED; SAHMREALTIME re-pulled 2026-07-16. JOLTS lags payrolls
by one month; match vintages before computing ratios.

Series ID              Value                                          As of
PAYEMS (chg)           +57K; prior +129K, +148K, +214K, -156K         2026-06
UNRATE                 4.2 (4.3 in 05)                                2026-06
CLF16OV                169,358K vs 170,078K in 05 = -720K             2026-06
CIVPART                61.5 (61.8 in 05)                              2026-06
LNS11300060 (prime-age LFPR) 83.3 (83.9 in 05)                              2026-06
UNEMPLOY               7,094K (7,307K in 05)                          2026-06
JTSJOL                 7,594K                                         2026-05
JTSQUR / JTSHIR        1.9 / 3.3                                      2026-05
ICSA                   215,000                                        wk end 2026-07-04
SAHMREALTIME           0.07; immediate prior 0.10 (May 2026)          2026-06
  history: 0.43 Nov 2025 | 0.35 Dec | 0.30 Jan 2026 | 0.27 Feb
           0.20 Mar | 0.13 Apr | 0.10 May | 0.07 Jun
  threshold 0.50 NOT triggered. Section 1's pointer table routes here; this is the
  document's SOLE authority on this series.
Openings/unemployed    7,594 / 7,307 = 1.04                           2026-05 matched

REFETCH BEFORE USE; DO NOT INHERIT
```

## 5. Economic growth

### Durable: the method, not the levels

Real GDP is reported quarter-over-quarter at a seasonally adjusted annual rate. **BEA revises: no GDPC1 level is a settled actual.** Q4 2025 printed +0.7% at second estimate and now reads +0.48%. The quarterly record is therefore not stated in prose here; every level is perishable and lives in the block below.

The shape is volatility around trend, not a trend break: a Q1 2025 tariff-front-running import distortion, Q2-Q3 payback, a shutdown-depressed Q4, a Q1 2026 return to trend (Grade D -- inference; the front-running and payback attributions are a standard read of the 2025 net-exports swing but were not sourced to a BEA release this pass). Revision discipline: treating a single quarter's first print as a regime signal is reading noise.

### Nowcasts are never inherited

A frozen nowcast becomes an active falsehood within weeks. GDPNow is a running estimate, not a forecast, and must be pulled at run time from the Atlanta Fed page (atlantafed.org/research-and-data/data/gdpnow) or FRED series GDPNOW. Durable calibration: since tracking began in 2011 its final-forecast average absolute error is 0.77pp, RMSE 1.17pp (Source: Atlanta Fed GDPNow methodology page, 2026, via search summary rather than a direct fetch) [Grade C]. A nowcast within ~0.8pp of trend carries no signal.

### PRESERVE -- Q4 2025 household credit stress (closed release)

The NY Fed reported that "total household debt increased by $191 billion, 1.0%, in Q4 2025, to $18.8 trillion" (Source: Federal Reserve Bank of New York, 2026-02-10) [Grade A]. Percent of balance 90+ days delinquent, Q4 2025 -- a fixed historical release (Source: NY Fed Consumer Credit Panel/Equifax, HHDC 2025Q4 workbook) [Grade B]:

| Category | 90+ days delinquent |
|---|---|
| Credit cards | 12.70% |
| Auto loans | 5.21% |
| Student loans | 9.57% |
| All debt | 3.12% |

This is the K-shaped consumer, and the source states the asymmetry itself: deterioration is "concentrated in lower-income areas and in areas with declining home prices" (Source: Wilbert van der Klaauw, NY Fed, 2026-02-10) [Grade A]. Aggregate spending can stay firm while the lower half defaults; headline consumption is a poor proxy for household health. Two measures are routinely conflated: 3.12% of balances are 90+ days delinquent, while 4.8% are in some stage of delinquency (Source: NY Fed, 2026-02-10) [Grade B -- table read, not a quotation].

### The ISM divergence (durable diagnostic)

A composite in expansion while its employment sub-index contracts means output held up by productivity and hours rather than headcount, which historically precedes hiring weakness rather than confirming strength (Grade D -- inference; no base-rate study sourced). The diagnostic is durable; its reading is not -- as of mid-2026 the divergence has narrowed. Check both sub-indexes, never the headline.

```
PERISHABLE -- REFETCH BEFORE USE; DO NOT INHERIT
as of 2026-07-15. Every level below expires. This block is the document's SOLE
authority on GDPC1 and on the ISM series; Section 1's pointer table routes here.

GDPC1 (pca), quarter-over-quarter SAAR -- BEA REVISES; not settled:
  Q1 2025 -0.65% | Q2 2025 +3.84% | Q3 2025 +4.38% | Q4 2025 +0.48% | Q1 2026 +2.09%
  Q4 2025 read +0.7% at second estimate before revision to +0.48%; the prior-vintage
  figure is carried from the predecessor, not re-pulled from an ALFRED vintage.
  (Source: BEA via FRED GDPC1, re-pulled 2026-07-16) [Grade B -- primary series
  retrieval, no quoted prose]

GDPNOW (FRED) Q2 2026     last seen 2026-07-08 -- refetch at run time, never inherit
PSAVERT                   3.0%    2026-05
Cards / auto 90+ delinq.  13.12% / 5.60%   NY Fed HHDC 2026Q1

ISM Mfg / Employment      53.3 / 49.7      ISM Report on Business, June 2026
  Grade A, verbatim, from ISM's own release, retrieved 2026-07-16 [ASCII
  substitution: the source's registered-trademark symbol after "PMI" is dropped]:
    "The Manufacturing PMI registered 53.3 percent in June, 0.7 percentage point
     lower than in May."
    "The Employment Index registered 49.7 percent, up 1.1 percentage points from
     May's figure of 48.6 percent."
  (Source: ISM June 2026 Manufacturing PMI Report on Business, issued 2026-07-01
   via ISM's PR Newswire release distribution; ismworld.org itself was not fetched.)

ISM Services / Employment 54 / 51.2      ISM Report on Business, June 2026
  Grade A, verbatim, from ISM's own release, retrieved 2026-07-16 [ASCII
  substitution: registered-trademark symbol dropped]:
    "In June, the Services PMI registered 54 percent, a decrease of 0.5
     percentage point compared to May's figure of 54.5 percent."
    "The Employment Index expanded for the first time in four months with a
     reading of 51.2 percent, a 3.3-percentage point increase from the 47.9
     percent recorded in May."
  (Source: ISM June 2026 Services PMI Report on Business, issued 2026-07-06
   via ISM's PR Newswire release distribution; ismworld.org itself was not
   fetched -- redirected to an SSO login wall.)

REFETCH BEFORE USE; DO NOT INHERIT
```

Retrieval status, stated rather than implied: both the manufacturing and services legs now carry verbatim Grade-A strings re-fetched directly from ISM's own release distribution (manufacturing issued 2026-07-01; services issued 2026-07-06, re-fetched 2026-07-16). The asymmetry is resolved by retrieval, not by relabelling.

Durable read: the saving rate sits near a third of its long-run average, and both credit-stock delinquency rates are still rising into Q1 2026. That ratio judgment, not the level, is the live tension against a return-to-trend GDP read (Grade B -- FRED PSAVERT annual-average 1959-2025, computed mean 8.41%, retrieved and computed 2026-07-16; current PSAVERT 3.0% (2026-05) is 35.7% of that mean, i.e. "near a third" is confirmed, not merely inherited. Recompute on refresh -- the mean shifts as new years append.).

## 6. Yield curve and fixed income

This is the section that mechanically drives the portfolio. The 10-year Treasury yield is a named input to the deployment bands in `ref-portfolio-doctrine`, which decide whether any capital may be deployed at all. That document owns the bands, the `halt-dgs10` regime halt, and the exit ladder; this section states the rate read and points there for the thresholds, never restating the band table as its own authority.

**Rule: one 10Y, one source (FRED `DGS10`), one as-of stamp, perishable tier, refetched every run.** Any yield appearing in prose anywhere in this document -- including in this section, which owns the series -- is a defect. The predecessor carried two unreconciled stale 10Y marks twelve lines apart; a stale mark is not a rounding problem, because the doctrine band table returns a materially different deployment multiplier at a stale level and a model primed on it reasons "deploy at reduced size" while deployment is in fact shut (Grade D, inference from the design failure).

```
PERISHABLE -- rates and credit. REFETCH BEFORE USE; DO NOT INHERIT
All levels FRED, as of 2026-07-14 close unless noted. Retrieved 2026-07-15.
This block is the document's SOLE authority on every series named in it.

DGS10        10Y nominal CMT                   4.58   2026-07-14
DGS2         2Y nominal CMT                    4.18   2026-07-14
DGS30        30Y nominal CMT                   5.08   2026-07-14
T10Y2Y       10Y-2Y spread                    +0.40   2026-07-14
DFII10       10Y TIPS real yield               2.33   2026-07-14
T10YIE       10Y breakeven                     2.25   2026-07-14
THREEFYTP10  Kim-Wright 10Y term premium       0.78   2026-07-10
BAMLH0A0HYM2 HY OAS                            2.72   2026-07-14
BAMLC0A0CM   IG corporate OAS                  0.79   2026-07-14
SOFR         Secured overnight financing rate  3.63   2026-07-14

Decomposition check at this vintage: DGS10 - DFII10 = T10YIE (4.58 - 2.33 = 2.25).
Re-run the check on every refetch; it is not inheritable.

DGS10 run above 4.50, six consecutive published sessions:
  2026-07-07 4.55 | 07-08 4.56 | 07-09 4.54 | 07-10 4.56 | 07-13 4.62 | 07-14 4.58
The run breaks at 2026-07-06 (4.48). The 07-13 print of 4.62 is superseded by 07-14
and is not the latest value. (Grade B: FRED DGS10 series, retrieved 2026-07-15.)
```

**Decomposition method (durable).** Nominal = real + breakeven; `DGS10` minus `DFII10` should reproduce `T10YIE`, and does at the stamped vintage. Check it on every refetch. A rise carried by the real leg is a discount-rate event for long-duration equity; a rise carried by the breakeven leg is an inflation-credibility event. The two demand different responses and are routinely conflated (Grade D, standard fixed-income decomposition).

**Curve shape and the un-inversion base rate.** The curve is positively sloped and has been steepening off a prolonged 2022-2024 inversion. The durable base rate, preserved verbatim from the predecessor (`:308`): *"Historical pattern: recession risk increases AFTER un-inversion."* This is counterintuitive and routinely misread as an all-clear. Attempts to source it to a primary failed: the Fed research literature (Estrella-Mishkin 1996, the NY Fed probit model) is built on *inversion* as the predictor, not un-inversion, and the refinement appears to be a practitioner observation without primary standing (Source: NY Fed / Federal Reserve yield-curve research, search-level attribution only; the NY Fed FAQ PDF returned HTTP 403 and could not be read). It is retained and graded honestly: **Grade D**. Un-inversion is ambiguous by construction -- bull steepening (front end falling as the Fed cuts into weakness) and bear steepening (long end rising on supply and term premium) look identical on a slope chart and mean opposite things. The current episode is bear-steepening-flavored, the long end leading: an inference from the `DGS30`-versus-`DGS2` spread and the term-premium direction in the block above, not a sourced institutional call (Grade D).

**Term premium (durable frame).** Term premium is rising on deficits, Treasury supply and fiscal uncertainty, and sits below its ~1.5% long-term historical average (Grade C on the historical average -- carried from the predecessor and not independently sourced this pass; the Kim-Wright level is in the block above, Grade B: FRED `THREEFYTP10`). Rising term premium is the analytically important case: it raises long yields without any improvement in growth expectations.

**Credit spreads.** Both IG and HY sit historically tight, which the predecessor read as benign. The durable base rate preserved verbatim from `:352`: *"When HY spreads are below 3%, historical forward 12-month outperformance vs. Treasuries only 39% of the time."* This traces to Charles Schwab's 2026 Corporate Credit Outlook, measuring the Bloomberg US Corporate High-Yield index against Treasuries on daily data 2005-11-28 to 2025-11-28 (Source: Charles Schwab, 2026 Corporate Credit Outlook). The page is authorization-gated and the sentence could not be re-pulled verbatim, so this is **Grade C, not Grade A** -- the attribution is search-level. It is live-binding: HY OAS is inside the sub-3% bucket at the stamped vintage, meaning credit is priced for a benign outcome that historically follows less than half the time. Tight spreads are a statement about compensation, not about safety.

**Bond-versus-equity disagreement (durable lens).** Across the vintages the bond signal repriced and the equity read did not adjust. When the two disagree, this document's prior is to weight the bond signal and to treat the equity signal as the one requiring justification. The rate levels that establish the repricing live in the block above and nowhere else.

**Treasury auction diagnostic (durable method).** Auction quality is the cleanest real-time read on structural demand for US debt. Check three things per auction: bid-to-cover against its 6-month average, primary-dealer absorption (elevated dealer takedown means end demand failed to clear the paper), and the tail (stop-out above the when-issued yield). Deteriorating auctions alongside a rising term premium is the signature of a supply/fiscal-driven yield rise rather than a growth-driven one (Grade D, method). The predecessor's specific March-2026 auction figures are dropped as stale perishables rather than carried.

### The net-liquidity composite is mis-specified -- correct construction

This section OWNS the net-liquidity treatment for the whole document; no other section restates it. The consuming system computes net liquidity as `WALCL - RRP - TGA`. It is **wrong** in four ways. All four were confirmed against the FRED API on 2026-07-15 (**Grade B**: FRED series metadata and observations -- an API metadata field is a retrieval, not a quotation from a primary document, and no Grade-A slot is claimed).

1. **Unit and frequency: the trap is `WTREGEN`, not `RRPONTSYD`.** The intuition runs the wrong way here, which is why the error is worth stating. `RRPONTSYD` IS denominated in billions -- its FRED units field reads "Billions of US Dollars" -- so it is the one leg that genuinely needs a x1000 scale, and it is the leg most likely to be flagged. `WTREGEN` is the trap: it reads "Millions of U.S. Dollars" and publishes "Weekly, Ending Wednesday", so any construction that treats it as billions, or as daily, is wrong on both axes. Treating its ~774,062 as billions subtracts roughly $774T from a ~$6.7T balance sheet -- not a rounding error but a 1000x annihilation of the composite. **Read the metadata field for every leg; never inherit a units label.** That is the durable rule, and it is the failure class that recurs.
2. **Basis mismatch.** `WALCL` is a Wednesday point-in-time level; `WTREGEN` is a *week average*; `RRPONTSYD` is daily. **Use `WDTGAL` (TGA Wednesday Level), not `WTREGEN`**, to match WALCL's basis. The two diverge materially on any given Wednesday; the stamped divergence sits in the block below.
3. **Vintage skew.** `RRPONTSYD` publishes daily while `WALCL` and `WDTGAL` publish weekly-Wednesday. A same-day composite silently subtracts a t+7 RRP from a t+0 balance sheet. **The composite is only coherent on Wednesday-aligned dates**; all three legs must be pinned to the same Wednesday.
4. **Dead term.** ON RRP has drained to a rounding error against its ~$2.5T peak. Net-liquidity variance is now effectively **`WALCL - TGA`**, and the TGA is the live driver. Any framing that treats ON RRP as an active drain/release valve is describing a 2022-23 regime that no longer exists.

Correct construction (durable), all legs in millions, Wednesday-aligned:

`net_liquidity = WALCL - WDTGAL - (RRPONTSYD * 1000)`

```
PERISHABLE -- net-liquidity legs. REFETCH BEFORE USE; DO NOT INHERIT
Series: WALCL, WDTGAL, WTREGEN, RRPONTSYD (FRED). Retrieved 2026-07-15.
Grade B -- primary series retrieval and API metadata, no quoted prose.

WALCL      Fed total assets, Wednesday level     6,735,609  MILLIONS  2026-07-08
WDTGAL     TGA, Wednesday level                    749,244  MILLIONS  2026-07-08
WTREGEN    TGA, week average (WRONG BASIS)         774,062  MILLIONS  2026-07-08
                                                            weekly, ending Wednesday
RRPONTSYD  ON RRP                                    3.347  BILLIONS  2026-07-08
RRPONTSYD  ON RRP                                    0.151  BILLIONS  2026-07-15

Worked, correct, Wednesday-aligned at 2026-07-08:
  6,735,609 - 749,244 - (3.347 x 1000 = 3,347) = 5,983,018 ($5.983T)

Worked, NAIVE UNSCALED SUBTRACTION -- what a model gets if it subtracts the raw
printed numbers without reading any units field. This is NOT what the corrected
spec says; it is the error shape the units discipline exists to prevent:
  6,735,609 - 774,062 - 3.347 = 5,961,544 ($5.962T)
Gap vs correct: roughly $21.5B -- the net of a $24.8B basis error (WTREGEN vs
WDTGAL) and a $3.3B RRP unit error running in opposite directions. Modest at this
vintage ONLY because ON RRP is near zero; structural at any vintage where it is not.
Recompute; never inherit.
```

## 7. Equity market positioning

Method first, because the levels below expire and the method does not. Equity positioning is read on three independent axes -- valuation, breadth, sentiment -- each scored against ITS OWN history, never against a cross-sector median and never collapsed with the other two. The multi-metric valuation panel is preserved in design for exactly this reason: forward P/E and CAPE are built to disagree (one discounts 12 months of analyst estimates, the other averages ten years of realized inflation-adjusted earnings), and a panel that averages them into a single "valuation" verdict destroys the disagreement that carries the signal (Grade D, method).

Durable structural anchors that survive any refresh: CAPE's long-run mean is 17.39; S&P 500 price-to-sales has a historical mean of 1.81 and median 1.64; price-to-book mean 3.16, median 2.91 (Source: multpl.com, 2026-07-15) -- Grade C, aggregator. The claim that CAPE's all-time high sits in the dot-com era is inherited framing and was not re-verified against a primary Shiller series this pass (Grade D). AAII's own historical averages are bullish 37.5%, neutral 31.5%, bearish 31.0%, and the survey publishes each Thursday (Source: AAII Sentiment Survey, 2026-07) -- Grade B.

```
PERISHABLE -- equity positioning. REFETCH BEFORE USE; DO NOT INHERIT
as of 2026-07-15. This block is the document's SOLE authority on the S&P 500
level and on every other mark named in it. Section 13 references this block
and states no index level of its own.

SP500 (FRED)       7,572.40   close, 2026-07-15 -- the latest published FRED print
  anchor: 2025-12-31 close 6,845.50 (FRED SP500) -> +10.6% YTD (computed)
NASDAQCOM (FRED)  26,107.01   close, 2026-07-14
VIXCLS (FRED)         16.50   close, 2026-07-14
  anchor: below the ~19-20 long-run mean (Grade D -- widely used, but NOT
  re-derived from VIXCLS history this pass)
Shiller CAPE          42.18   2026-07-15  multpl.com (Grade C)
  anchor: own mean 17.39 (~2.4x)
S&P 500 P/S            3.74   2026-07-15  multpl.com (Grade C)
  anchor: mean 1.81; ABOVE the prior max 3.35 (Dec 2025)
S&P 500 P/B            6.01   2026-07-15  multpl.com (Grade C)
  anchor: mean 3.16; ABOVE the prior max 5.39 (Dec 2025)
AAII bull/neutral/bear   36.3% / 26.5% / 37.2%   week published 2026-07-09
  aaii.com (Grade B); anchor: 37.5 / 31.5 / 31.0
  Two AAII-hosted retrievals agreed on the three values and DISAGREED on the
  week-ending stamp (2026-07-09 vs 2026-07-11). The ambiguity is unresolved.
```

NOT SOURCED, stated rather than guessed: percent of S&P 500 constituents above their 200-day and 50-day moving averages could not be retrieved from any permitted source at compile time; the breadth read is therefore ABSENT, not neutral. Refetch `$SPXA200R` / `$SPXA50R` before any breadth claim. Forward 12-month P/E is likewise absent -- its usual publisher is on the blocked list (Grade D, absence). Magnificent-7 share of S&P 500 market cap is omitted rather than refreshed: no permitted source was retrievable.

Two live inferences worth carrying (Grade D). First, P/S and P/B both printing above their own December-2025 maxima while CAPE sits near 2.4x its mean means the valuation axis is at record extension even though the VIX axis is calm -- calm is not cheap. Second, and load-bearing: AAII bearishness above average is a positioning observation, not a buy trigger. Read as "contrarian bullish" while a regime halt is active, it manufactures conviction the doctrine forbids. Sentiment extremes are inputs to [[ref-regime-taxonomy]], never to a deployment decision.

## 8. Sector rotation and relative strength

**Durable method.** Leadership is relative strength versus the benchmark, not absolute return: a sector up 6% in a market up 10% is a laggard. Phase-to-sector mapping is a prior to check, never an attribution. Fidelity's business-cycle sector framework states of late cycle that "Inflationary pressures may build in these phases, which can lead to outperformance from companies in the energy and basic materials sectors" and that defensive sectors "have the potential to outperform the market"; of mid cycle, "Information technology stocks have historically earned strong returns during this phase" alongside the warning that "there can often be a lack of clear sector leadership in these environments" (Grade A -- verbatim from Fidelity's HTML Learning Center page, retrieved 2026-07-15; the stronger Fidelity AART research PDF fetched as unparseable binary, so its 1962-2020 return study is omitted rather than cited). The counter-evidence belongs directly beside it: Molchanov et al. tested sectors across every cycle stage and reported no systematic or persistent phase-conditional return differences (Grade C -- International Journal of Finance and Economics, 2024; surfaced via search summary, abstract not fetched directly).

**Attribution discipline.** Standing rule: no causal attribution to a sector move unless the named event is dated inside the measured return window and explains the cross-section rather than one sector. The predecessor's map failed it twice -- keyed to an "Iran war / oil at $111" premise, and crediting Technology's move to the January-2025 "DeepSeek shock" some eighteen months after the fact; both attributions are deleted, not refreshed. Intra-sector dispersion is routinely mistaken for rotation: a same-session memory-name drawdown against rising hyperscalers is a supply event inside one sector, not a rotation signal (Grade D -- inference).

```
PERISHABLE -- sector relative strength. REFETCH BEFORE USE; DO NOT INHERIT
Source: sector SPDR YTD total returns, aggregator table, as of 2026-07-15 (Grade C).
Series: XLE, XLK, XLI, XLB, XLRE, XLP, XLU, XLF, XLV, XLY, XLC vs SPY.
Vintages across aggregators disagreed by >5pt during compilation: one first-half
recap read XLK +33 / XLE +21 / XLI +20; one tracker read XLK +25.80 / XLC -9.80.
No primary index-provider source was reachable (spglobal.com blocked; etfdb.com
bot-blocked). All figures are approximate. REFETCH; do not reconcile from here.

Approximate 2026 YTD, as of 2026-07-15:
  XLE ~+26%   XLK ~+26%   XLI ~+16%   XLB ~+11%   XLRE ~+10%   SPY ~+11%
  XLP  ~+7%   XLU  ~+6%   XLF  ~+3%   XLV  ~+2%   XLY  ~-2%    XLC  ~-4%

Breadth of leadership: roughly 2 of 11 sectors above SPY -- the aggregator's own
count, NOT independently recomputed (Grade C).
```

**Read.** Leadership is narrow, and the YTD ranking records H1 conditions rather than a live signal -- energy's position was earned under an oil premise that has since reversed (Grade C; Section 9 owns the energy state and sources it independently). Nothing here supports a broad value/defensive rotation call. Regime classification belongs to [[ref-regime-taxonomy]]; benchmark tables to *ref-sector-benchmarks* (not published).

## 9. Global macro and geopolitical

Transmission METHOD is owned by `ref-geopolitical-framework`; this section carries STATE only.

### Energy and the Strait of Hormuz

The disruption is real and currently acute; what is void is the assumed PRICE consequence, which is the leg every inherited model gets wrong.

Durable structure, Grade A -- both sentences verbatim (Source: US EIA, Today in Energy no. 65504, retrieved 2026-07-15): *"In 2024, oil flow through the strait averaged 20 million barrels per day (b/d), or the equivalent of about 20% of global petroleum liquids consumption."* On the bypass constraint, same page, same grade: *"We estimate that about 2.6 million b/d of capacity from the Saudi and UAE pipelines could be available to bypass the Strait of Hormuz in the event of a supply disruption."*

Sequence, Grade B: war opened 2026-02-28; a US-Iran memorandum on 2026-06-17 pulled crude sharply down -- but **NOT to pre-conflict levels**, and the distinction is the section's point. The post-memorandum trough sits materially ABOVE the pre-conflict average, so "crude round-tripped the war" is false; the levels and the exact gap are stamped in the block below (both legs FRED `DCOILWTICO`; Section 3's block owns the monthly-average series). Compute the gap from the block; do not restate it from memory. The ceasefire collapsed 2026-07-08; Iran declared the strait closed 2026-07-12; a US naval blockade was reinstated 2026-07-14. Transits fell from 45 on 2026-07-06 to 5 across 07-08/09 (Source: Al Jazeera, 2026-07-13). The transit counts are relayed reporting, not primary AIS/vessel-tracking data, which was not retrieved; the apparent originating wire is on the blocked list and is never cited here.

Grade D inference, this section's central claim: transit volume is no longer a sufficient statistic for crude price. EIA's own April 2026 forecast expected Brent to peak far above where crude actually printed. Verbatim (Grade A; Source: EIA press release 586, eia.gov, 2026-04-07): *"we expect it to peak in the second quarter of 2026 (2Q26) at $115/b before easing as production shut-ins slowly abate."* Realized WTI spot never approached that level even at its 2026-07-13 spike print (block below); the forecast used Brent while this document's block tracks WTI, so the two series are not directly comparable level-for-level, but the forecast's risk-premium logic -- and its overshoot relative to the actual de-escalation path -- is the load-bearing point. Models mapping Hormuz headlines to an oil spike are mis-specified; Sections 3, 8, 12, 13 and 14 must not inherit an oil-shock transmission.

```
PERISHABLE -- energy and FX. REFETCH BEFORE USE; DO NOT INHERIT
Series: DCOILWTICO, DTWEXBGS (FRED). Retrieved 2026-07-15. Grade B.

DCOILWTICO  WTI spot                   79.20    2026-07-13
  CAUTION: this is a spike print, not a settled level -- the series ran
  72.45 on 2026-07-10 to 79.20 on 2026-07-13. It is not a band marker
  and must not be treated as one.
  Post-memorandum trough for the pre-conflict comparison: 69.60, 2026-07-06.
DTWEXBGS    nominal broad dollar      120.5046  2026-07-10
```

### China

```
PERISHABLE -- China activity prints. REFETCH BEFORE USE; DO NOT INHERIT
as of 2026-07-15. Grade C throughout: the NBS primary release at stats.gov.cn
returned HTTP 404 on fetch; every figure below is relayed via CNN Business. The
cited URL is dated 2026-07-14 while the NBS release is reported as Wednesday
2026-07-15 -- the release date is ambiguous and UNRECONCILED. No figure here was
confirmed against NBS. This block is the document's sole authority on these levels.

Real GDP, YoY                4.3%     Q2 2026 (weakest since Q4 2022)
Real GDP, YoY                4.7%     H1 2026
Exports, YoY                 +27%     Q2 2026
Retail sales, YoY            +1%      Jun 2026
Property investment, YoY     -18%     H1 2026
Official 2026 growth target  4.5-5.0%
```

Durable read: Q2 is the first miss of the official target since the Covid era, and the composition is the signal -- an export-led quarter carried against a stalled domestic consumer and a property sector still contracting at a double-digit rate. Export strength of that shape is not evidence of domestic demand repair; it is the offset to its absence, and it is the leg most exposed to tariff policy. Late-July Politburo is the next fiscal catalyst (Grade D).

### China memory-industrial policy

Both rows Grade C -- aggregator summaries of exchange filings; no primary SSE/CSRC filing was retrieved.

- CXMT: STAR IPO priced 8.66 yuan/share 2026-07-14, raising ~57.9B yuan gross, listing ~2026-07-27. **Yuan is the stated basis for this raise throughout this document, including the Section 12 marker row.** At the ~7.1 CNY/USD the vault carries, that is ~$8.15B. A Reuters relay of the same raise carried ~$8.55B, implying either ~6.77 CNY/USD or a different gross/net basis; NOT reconciled this pass -- the USD figure is not authoritative.
- YMTC: CSRC first-phase IPO tutoring report disclosed 2026-07-10.

State-financed DRAM and NAND capacity is reaching public markets -- a supply-side risk to memory pricing orthogonal to Fed policy. The attribution of the 2026-07-15 memory drawdown to this rather than to a rate event is **Grade D**: inference layered on an assertion supplied to this document, not a causal finding retrieved from any source this pass. Mechanism: `ref-theme-alpha`.

### Europe and Japan

The ECB raised its three key rates 25bp effective 2026-06-17, taking the deposit facility rate to 2.25%. Rate, size, date, rationale and growth path are Grade A -- all verbatim (Source: ECB monetary policy decisions, 2026-06-11): *"The Governing Council decided to raise the three key ECB interest rates by 25 basis points"*; *"the interest rates on the deposit facility, the main refinancing operations and the marginal lending facility will be increased to 2.25%, 2.40% and 2.65% respectively, with effect from 17 June 2026."*; *"The war in the Middle East is generating inflation pressures, and the decision to raise rates is robust across a range of scenarios mapping out how the shock might evolve and affect the medium-term outlook for the euro area."*; *"The baseline sees economic growth at an average of 0.8% in 2026, 1.2% in 2027 and 1.5% in 2028."* The characterization "a first hike in nearly three years" appears nowhere in the release; it is derived from rate history and was not re-verified this pass (Grade D).

The BOJ took its overnight call rate to around 1.0% on 2026-06-16, 7-1, Asada dissenting -- highest since 1995 (Grade B; the BOJ primary PDF returned unreadable binary on fetch, so this is wire-sourced, not primary-quoted).

Both tightened INTO the energy shock. Durable read: the 2026 global policy impulse is synchronized-hawkish, removing the offsetting-easing cushion a US-only cycle would leave.

## 10. Fiscal policy and government

Durable structure: the fiscal stance is expansionary and the debt path is driven by interest cost, not program growth. CBO's February 2026 baseline projects an FY2026 deficit of $1.9T (5.8% of GDP) against a 50-year average of 3.8%, with debt held by the public rising from 101% of GDP in 2026 to 120% by 2036, surpassing the 106% record set in 1946. Net interest goes from $1.0T (3.3% of GDP) in 2026 to $2.1T (4.6%) in 2036 while the primary deficit stays at or below 2.6% of GDP throughout. The OBBBA (P.L. 119-21, enacted 2025-07-04) adds $4.7T to 2026-2035 deficits, partly offset by roughly $3T of tariff revenue. (All Grade B; Source: CBO, Budget and Economic Outlook 2026-2036, 2026-02-11 -- reported via secondary summaries; **cbo.gov returned HTTP 403 to every fetch route this pass, so no CBO document was retrieved and no CBO prose is quoted anywhere in this section**.) Mechanism over levels: the deficit trajectory is largely a function of the same 10Y yield Section 6 tracks -- rates and fiscal are one problem, not two.

### The debt-ceiling X-date: the inherited premise is falsified, not merely stale

The predecessor carried "Bipartisan Policy Center projects August-early October 2026." That figure is dead. P.L. 119-21 sec. 72001 raised the ceiling to roughly $41.1T: *"The limitation under section 3101(b) of title 31, United States Code, as most recently increased by section 401(b) of Public Law 118-5 (31 U.S.C. 3101 note), is increased by $5,000,000,000,000."* (Grade A, verbatim; Source: 31 U.S.C. 3101 note). BPC now projects the U.S. *"will most likely reach the debt limit once again sometime between late winter and mid-summer of 2027"*, after which *"Those resources are expected to last roughly six to nine months, at which point the federal government would reach the X Date"* (Grade B; Source: Bipartisan Policy Center, "When Will We Reach the Debt Limit (Again)?", published 2026-06-04, updated 2026-06-17 -- quotations retrieved verbatim from BPC, which is a secondary analyst, not the primary). The X-date is a late-2027-into-2028 event, not a 2-to-11-week catalyst.

**What was sourced, and what could not be.** Neither CBO nor Treasury carries a live X-date projection: no CBO projection exists for this cycle, and Treasury has issued no debt-limit letter to Congress since the ceiling was raised -- there is nothing to source because there is no live limit to project against. Treasury's own debt-limit page (home.treasury.gov, retrieved 2026-07-16, Grade B) lists letters by year with an explicit year-header for 2025, 2024, 2023...; no 2026 year-header or letter entry exists, directly confirming (not merely inferring) that no debt-limit letter has been sent to Congress since the ceiling was raised. CBO customarily issues an X-date projection only after Treasury formally begins extraordinary measures (Grade D, inference from observed practice, not a sourced CBO policy statement). The BPC projection above is therefore the only sourced projection available, and it is Grade B, not A. A model inheriting a 2026 X-date is pricing a non-event.

### Section 48D: a begin-construction cliff, not placed-in-service

*"The credit allowed under this section shall not apply to property the construction of which begins after December 31, 2026."* (Grade A, verbatim; Source: 26 U.S.C. 48D(e)). The trigger is BEGIN CONSTRUCTION: a fab breaking ground on 2026-12-31 keeps the credit through completion; one starting a day later gets nothing. The rate is 35%, raised from 25% by P.L. 119-21 for property placed in service after 2025-12-31 (Grade B; Source: 48D amendment notes as relayed by the fetch layer, not a clean verbatim string of 48D(a) itself) -- the two subsections use different triggers, and conflating them misdates every fab decision in the AI supply chain. Falsifier: any extension enacted before year-end.

### Tariff revenue: the fiscal item actually inside the window

The Supreme Court struck down the IEEPA tariffs on 2026-02-20 and CBP is administering refunds of *"as much as $166 billion, plus interest"* (Grade B; Source: Bipartisan Policy Center, published 2026-06-04, updated 2026-06-17 -- verbatim from BPC, a secondary analyst). Of the Section 122 replacement surcharge the same source states: *"these new tariffs as currently written expire at the end of July"* (Grade B, verbatim, same source). The commonly cited 150-day statutory cap on Section 122 was NOT confirmed against the proclamation or the Trade Act text this pass and does not appear in the BPC source; it is not asserted here (Grade D, absence). This, not the debt ceiling, is the fiscal catalyst in the window, and it drives the Section 3 pass-through.

```
PERISHABLE -- REFETCH BEFORE USE; DO NOT INHERIT
Series: MTSDS133FMS (FRED) | Primary: Treasury Monthly Treasury Statement, FY2026 through 2026-06-30
as of 2026-07-15 (June MTS released 2026-07-13)
FY2026 YTD deficit -1,366,508 ($ mn); prior-year period -1,337,372
Receipts 4,151,410; outlays 5,517,918 (Grade B -- primary table retrieval, no quoted prose)
Next release: July MTS, 2026-08-12
```

## 11. Thematic macro trends

Five structural forces, all slower-moving than the rate cycle. Section 1 carries the cyclical read; this section carries what survives it.

**AI capex cycle** (macro altitude only; stack mechanism belongs to [[ref-theme-alpha]]). The durable facts are direction and intensity, not level: Big-4 CY2026 guidance has been revised UP at every 2026 earnings cycle, so any inherited $660-690B baseline is stale on the low side. Capex-to-revenue ratios of roughly 25-54% across the Big-4 make this the most capital-intensive corporate investment cycle in decades, and all four report supply constraint rather than demand constraint (Source: aggregator tallies of company guidance, 2026-06) [Grade C].

```
PERISHABLE -- REFETCH BEFORE USE; DO NOT INHERIT
Release: Big-4 CY2026 capex guidance (per-company 8-K/10-Q + earnings calls). as of 2026-07-15.
3 RAISE / 1 HOLD at the last cycle. Revises quarterly. All components [Grade C].
  - AMZN:  CY2026 capex guidance ~$200B (per aggregator tally, 2026-06)
  - GOOGL: CY2026 capex guidance $175-185B (same)
  - META:  CY2026 capex guidance $115-135B (same)
  - MSFT:  ~$190B calendar basis; ~$205B fiscal-year basis (same)

AGGREGATE -- two bases, both stated, because the spread IS the fiscal/calendar artifact:
  Calendar basis (MSFT ~$190B): $680-710B, midpoint ~$695B  [Grade C components; derived]
  Fiscal basis  (MSFT ~$205B): $695-725B, midpoint ~$710B  [Grade C components; derived]
Tallies quoting "~$695-725B" are on the fiscal basis; the $15B step is MSFT alone.
Recompute from the components on every refetch; never inherit an aggregate.
```

The two bases reconcile with the parallel [[ref-theme-alpha]] rewrite rather than contradicting it: that document re-derives a like-for-like CY2025 base of $384.5B growing +81-89%, which lands on the fiscal-basis aggregate above. Growth of that order, not the level, is the macro fact. [Grade C components; derived]

**Energy transition and grid capacity.** Power availability remains the #1 bottleneck for AI infrastructure [Grade C]. US data-center demand is projected at 75.8 GW (2026) rising to 134.4 GW (2030) (451 Research/S&P Global, carried from the predecessor; spglobal.com is on the blocked-domain list, so the figure could NOT be verified at its originating publisher) [Grade C]; EPRI projects data centers at 9-17% of US electricity by 2030 versus roughly 4% today (Source: EESI, 2026) [Grade C]. The constraint is physical, not financial: about 16 GW is slated for 2026 against roughly 5 GW under construction, leaving ~11 GW announced with no visible build, and 30-50% of 2026 projects are projected to slip (Source: Sightline Climate, Data Center Outlook, 2026) [Grade B]. SemiAnalysis disputes the under-construction count as understated -- the dispersion is itself the signal [Grade C].

**Commercial real estate refinancing wall.** CMBS office delinquency **set an all-time record in January 2026** (Source: Trepp via Multi-Housing News, 2026) [Grade C]; the record-setting level sits in the block below and nowhere else. Its subsequent retreat is extension and modification, not credit repair -- roughly 70% of newly delinquent balances are nonperforming matured balloons, so the series oscillates rather than heals [Grade C]. On maturities, use MBA's own survey figure: $875B maturing in 2026, 17% of $5.0T outstanding (Source: MBA CREF loan-maturity survey, 2026) [Grade B]. The widely-circulated $936B figure is industry commentary, NOT sourced to a primary, and should not be inherited [Grade D].

```
PERISHABLE -- REFETCH BEFORE USE; DO NOT INHERIT
Release: Trepp CMBS Delinquency Report (monthly). as of 2026-07-15 -- last observed print June 2026.
This block is the document's sole authority on the CMBS office delinquency level.
  CMBS office delinquency, record print   12.34%   Jan 2026 (Grade C, Trepp relay)
Office delinquency and the overall rate both move monthly; refetch before any credit-regime read.
```

**Private credit.** AUM estimates span $1.3T (US only) to $2T+ and rising toward $4T by 2030, with no harmonised definition across authorities -- the measurement gap is the durable finding (Source: FSB, Report on Vulnerabilities in Private Credit, 2026) [Grade C -- title/date confirmed, body not machine-readable at fetch, so no quotation was retrieved]. Standards weakened in the 2021-22 vintages via covenant-lite terms, PIK income, NAV lending and EBITDA add-backs [Grade C]. Default estimates diverge: 2.73% (Proskauer index, Q1 2026) versus 1.6-4.7% (Moody's, 2025) [Grade C]; the circulating "~5% true default" figure sits above that range and is not independently confirmed [Grade D].

**Demographics.** The most durable content in this document, and the correct lens for reading every payroll print: net immigration collapsed from about 2.7M (year to July 2024) toward roughly 320K projected for 2026 (Source: Federal Reserve Board FEDS Notes, 2026-04-02, citing Census) [Grade C]. Breakeven employment is correspondingly reset: current estimates run 15K-87K/month (Source: St. Louis Fed, 2026-03) [Grade C], or 50K and possibly negative (Source: Brookings/AEI, 2026-01) [Grade C] -- the older ~75-90K/month anchor is void. A +50K print that reads weak against the old lens reads at or above breakeven against the new one. Section 4 points here for this figure; this section owns it.

No Grade A claim appears in this section: no verbatim quotation from a primary document was retrievable for any Section 11 claim within budget, and nothing was paraphrased into a Grade-A slot.

## 12. Risk matrix

Eleven rows, every probability rebuilt from zero. Two binding disciplines. First, each row names a resolution DATE and a mechanically checkable MARKER, so it can be Brier-scored later -- an unscored probability column is how a top row survives months after its premise dies. Second, the probability is calibrated author judgment, Grade D by construction; evidential weight sits in the marker, whose own grade is stated.

**On the Impact column, stated so it cannot be misread.** It is an ordinal **magnitude of consequence conditional on the row firing**, and carries no probability or confidence content whatsoever -- probability lives in its own column, confidence in the marker grade. Bands, so the column is anchored rather than free-floating [Grade D -- inference from mechanism], never a return estimate: *Medium* = alters one thesis' earnings path, trips no doctrine gate; *Medium-high* = same, plus a plausible second-order credit or supply channel; *High* = trips a doctrine gate (deployment band or regime halt per *ref-portfolio-doctrine* (not published)) or re-rates the whole long-duration complex; *Very high* = impairs Treasury-market function itself, so the discount rate for every row moves at once; *Extreme* = both of the above plus a physical supply-chain break with no financial offset.

| Risk | Probability by date | Falsifiable resolution marker | Impact magnitude IF FIRED (ordinal; not a probability) | Marker grade |
|---|---|---|---|---|
| Fed hikes >=25bp | 45% by 2026-12-09 | `DFEDTARU` prints >3.75 at or before the Dec 8-9 FOMC | High, all duration | B -- June SEP 2026 median 3.8% (3.4% in March), 9 of 18 dots above the current range, 17 of 18 seeing upside inflation risk (Source: Federal Reserve, 2026-06-17; Section 2 owns the SEP) |
| Core inflation re-accelerates | 40% by 2026-12-31 | `PCEPILFE` (`units=pc1`) >=3.75% on any release | High | B -- SEP 2026 core PCE median raised to 3.3% (Source: Federal Reserve, 2026-06-17) |
| Regime halt still binding at quarter-end | 55% by 2026-09-30 | `DGS10` closes >=4.50 on 2026-09-30 | High -- mechanical: gates deployment size via `ref-portfolio-doctrine` | C -- six consecutive closes >=4.50, 7/07-7/14 (Source: FRED DGS10; Section 6 owns the levels) |
| Memory downcycle on Chinese DRAM capacity | 35% by 2027-06-30 | Any Big-3 DRAM supplier guides a sequential ASP decline | High, concentrated | C -- CXMT STAR IPO priced 2026-07-14 raising ~57.9B yuan gross, listing ~2026-07-27. Section 9 owns this citation, its yuan basis and the unreconciled USD relay; do not re-denominate it here |
| Big-4 hyperscaler cuts CY2026 capex guidance | 20% by 2026-12-31 | A downward CY2026 capex revision in a Big-4 8-K or 10-Q | High | D |
| US recession begins | 25% by 2027-06-30 | NBER-dated peak, or `SAHMREALTIME` >=0.50 | High | D |
| Section 48D construction cliff binds | 90% by 2026-12-31 | No statutory extension enacted | Medium, fab-capex timing | A -- 26 U.S.C. 48D(e): "The credit allowed under this section shall not apply to property the construction of which begins after December 31, 2026." (Source: uscode.house.gov) |
| High-yield credit repricing | 20% by 2026-12-31 | `BAMLH0A0HYM2` >=4.50 on any close | High | C |
| CRE / regional-bank credit event | 15% by 2027-06-30 | FDIC failure of a >$10B-asset bank citing CRE concentration | Medium-high | D |
| Debt-ceiling disruption inside CY2026 | 5% by 2026-12-31 | A Treasury letter declaring extraordinary measures in CY2026 | Very high | B -- REFUTES the inherited "Aug-early Oct 2026": BPC projects the limit is reached "sometime between late winter and mid-summer of 2027", measures then lasting "roughly six to nine months". Section 10 owns this citation and its vintage; do not re-date it here |
| China/Taiwan military escalation | 5% by 2027-06-30 | A US ordered-departure notice for Taiwan, or a declared PLA exclusion zone | Extreme | D |

No hedge or mitigation column exists: that would issue action recommendations, which this document may not.

```
PERISHABLE -- risk-matrix marker series
Series: DGS10, BAMLH0A0HYM2, PCEPILFE (units=pc1), DFEDTARU, SAHMREALTIME | as of 2026-07-14
REFETCH BEFORE USE; DO NOT INHERIT. Every row resolves against a live pull, never against a
level quoted anywhere in this document. Owning blocks: DGS10 + BAMLH0A0HYM2 = Section 6;
PCEPILFE = Section 3; DFEDTARU = Section 2; SAHMREALTIME = Section 4.
```

## 13. Scenarios (bull / base / bear)

### This section confers no action authority

Partial satisfaction of any scenario below is NOT an action recommendation. Scenario markers do not override, relax, or substitute for the deployment bands, the concentration bands, or an active regime halt defined in *ref-portfolio-doctrine* (not published), which is the sole authority on deployment size. A scenario reading "bull" while a regime halt is active means the halt binds and the scenario is commentary. This document primes analysis; it never authorizes a trade. (House rule -- a governing constraint on this document, not an evidentiary claim; the Grade A-D scale applies to external evidence and does not apply here.)

### The superseded bull case, scored

The superseded bull case stated **SIX conditions**. Its "S&P 500 range: 7,200-7,800" was a **separate line and a PREDICTED OUTCOME, not a condition** -- promoting it into the condition list is the error being scored here, and it is not counted as one below. The table carries VERDICT and MECHANISM only; every level it turns on lives in the owning section's perishable block and is refetched there, never inherited from this table.

| # | Bull condition | Live status | Evidence (levels by reference only) |
|---|---|---|---|
| 1 | Iran ceasefire holds within weeks | FALSIFIED | Ceasefire collapsed 2026-07-08; strait declared closed 07-12; blockade reinstated 07-14. Section 9 owns the sequence (Grade B) |
| 2 | Oil drops to $70-80 | LEVEL SATISFIED, MECHANISM INVERTED | WTI reached the band from ABOVE as the conflict de-escalated, not on the predicted benign path, and sits ~15% above the pre-conflict level rather than at it. Levels and both vintages: Section 9's and Section 3's blocks (Grade B) |
| 3 | Core PCE decelerates toward 2.5% by year-end | FALSIFIED, WRONG SIGN | Core PCE has RISEN across the measured window: six of its last seven prints rose (February dipped), for a net rise since October 2025. Section 3's block owns every level and the computation (Grade B -- derived from FRED `PCEPILFE`, `units=pc1`) |
| 4 | Fed delivers 2-3 cuts in H2 2026 | FALSIFIED, WRONG SIGN | The June FOMC held the target range; the June SEP's 2026 median policy path was revised UP from March, pointing to a hike rather than cuts (Grade B -- SEP Table 1 read plus inference from the path revision, no quoted prose; inference is never Grade A. Section 2 owns the SEP) |
| 5 | Earnings growth accelerates on AI monetization | **NOT ASSESSED** | No S&P 500 earnings-growth or forward-EPS series was retrieved this pass -- the usual publisher is on the blocked-domain list and Section 7 records forward P/E as likewise absent. This condition is neither confirmed nor refuted here; a refresh must score it before the tally below is treated as complete (Grade D, absence) |
| 6 | Consumer resilience sustained by real wage gains | **NOT ASSESSED** | A real-wage test requires `CES0500000003` deflated by CPI on matched vintages; that pull was not run this pass. Section 5's rising credit-stock delinquencies and depressed saving rate are adjacent counter-evidence but are NOT a real-wage test and are not scored as one (Grade D, absence) |
| -- | *S&P 500 range 7,200-7,800* -- **predicted OUTCOME, not a condition** | Band printed | Section 7's perishable block is the sole authority on the S&P level, its source and its as-of; this section states no index level (Grade B) |

Tally: **of six conditions, one is satisfied on level only with its mechanism inverted, three are falsified, and two were not assessed.** The predicted outcome band printed anyway.

The reusable rule: **a scenario whose outcome bands print while its causal triggers fail has not come true -- it has been falsified and is being read backwards from its outputs.** A model pattern-matching on the printed band infers a bull regime from the scenario's own predicted consequence while every driver it could check runs the opposite way, and emits a confident BUY into a book under an absolute deployment halt (Grade D).

On the Fed leg, Chair Warsh stated at the 2026-06-17 press conference: *"The median participant judges that the appropriate federal funds rate to be at 3.8 percent at the end of this year and 3.6 at the end of next"* (Grade A, verbatim; Federal Reserve transcript, 2026-06-17). Section 2 owns the SEP table reads that corroborate it (Grade B).

The second defect is causal, not calibrational. That bull case predicted *"Tech/semis rally sharply"* while containing no term for Chinese memory industrial policy -- on 2026-07-15 memory names fell sharply on CXMT's STAR Market IPO pricing while hyperscalers rose the same session (Grade B), so the model could not represent the variable that moved the tape. The scenarios below therefore name their predicted consequences as well as their triggers, so the causal model is falsifiable.

```
PERISHABLE -- scenario markers. REFETCH BEFORE USE; DO NOT INHERIT
as of 2026-07-15
This block carries NO levels by design: every scenario marker below is a THRESHOLD (durable)
resolved against a live pull of the series named here, in the block that owns it. One series,
one owning block, one as-of stamp -- a level restated here would be a second vintage.

Series            Owning block   Resolves
DGS10 (FRED)      Section 6      bear/base band tests; regime-halt threshold
PCEPILFE (pc1)    Section 3      all three scenarios' core-inflation markers
DCOILWTICO (FRED) Section 9      energy-mechanism cross-check
DFEDTARU/DFEDTARL Section 2      hike/cut/hold markers
S&P 500 close     Section 7      index-band reference for the scoring table ONLY; not a live marker
```

### The three scenarios

All probabilities resolve on a single date, **2027-01-15**, so they are Brier-scorable. Each names dated markers, the consequences that must follow, and the observation that invalidates it.

**Bear -- policy trap (40%).** Mechanism: the Fed is caught between mandates and holds or is forced to hike. Markers: core PCE (`PCEPILFE`, pc1) >= 3.4% on any print through 2026-12-31; any hike at the 2026-07-29, 09-16, 10-28 or 12-09 FOMC; `DGS10` sustained >= 4.50%. Consequences that must follow: long-duration and high-multiple equities de-rate; credit spreads widen from tights. Invalidation: two consecutive core PCE prints <= 2.9% with no hike delivered.

**Base -- sticky inflation, Fed on hold (45%).** Markers: core PCE 3.0-3.5%; fed funds unchanged at 3.50-3.75% through 2026-12-09; `DGS10` in 4.30-4.75%. Consequences: index-level range trading with dispersion driven by supply-side events rather than by Fed policy. Invalidation: any 2026 cut, or core PCE outside 3.0-3.5% for two consecutive prints.

**Bull -- genuine disinflation (15%).** Requires TRIGGERS, not outcomes. Markers, all required: three consecutive core PCE prints decelerating with the latest <= 2.9%; at least one cut delivered by 2026-12-09; Hormuz transit volumes normalized for 30+ consecutive days (the consuming model must name its transit source at evaluation time -- no authoritative series is specified here). Consequences that must follow: `DGS10` < 4.40% and breadth broadening beyond mega-cap. Invalidation: any hike, or core PCE >= 3.4% on any print. Under this construction the bull case is currently **0-of-3 on triggers**.

Probabilities are calibrated judgment, not a market-implied distribution (Grade D). They are recorded to be scored.

## 14. Macro-to-portfolio transmission map

A METHOD, not an inventory: how each macro variable reaches each of the five theses, the sign and rough magnitude of the sensitivity, and the observation that would falsify the mapping. **It names no position, no share count and no dollar amount by design** -- a consuming model reads the causal wiring here, then pulls live holdings and weights from the broker at run time. [Grade D -- design judgment]

### Perishable inputs -- REFETCH BEFORE USE; DO NOT INHERIT

No level appears in this section's prose. Each variable is read from its series at run time:

| Variable | Series ID | Units (verified) |
|---|---|---|
| Real rate / nominal 10Y / breakeven | `DFII10`, `DGS10`, `T10YIE` | Percent, daily |
| Broad dollar | `DTWEXBGS` | Index Jan 2006=100, daily |
| Oil | `DCOILWTICO` | USD/bbl, daily |
| Net liquidity | `WALCL` - `WDTGAL` - (`RRPONTSYD` x 1000) | Millions; RRP prints in BILLIONS, must be scaled; Wednesday-aligned only |
| Credit spread | `BAMLH0A0HYM2` | Percent OAS, daily close |
| Labor trend | `PAYEMS`, `SAHMREALTIME` | Thousands; index; monthly |

as of 2026-07-15, series metadata verified at fred.stlouisfed.org. [Grade B] Units were individually re-verified this session for `DFII10`, `DGS10`, `DTWEXBGS`, `WALCL`, `WDTGAL`, `RRPONTSYD` and `BAMLH0A0HYM2`; units for `T10YIE`, `DCOILWTICO`, `PAYEMS` and `SAHMREALTIME` were NOT individually re-pulled and are stated from standard FRED conventions -- confirm them before trusting this table verbatim.

### Rates bind the whole book -- never a neutral, position-scoped factor

`DGS10` is a mechanical doctrine input: it drives the deployment band and the regime halt defined in `ref-portfolio-doctrine`, which govern whether ANY capital may be deployed into ANY thesis. Under an active absolute halt the rate variable dominates every row below -- not by flipping a thesis sign, but by setting the size multiplier to zero across all five at once. A model treating rates as one factor among seven mis-ranks the constraint set. One variable, two transmissions, not to be collapsed: bands throttle deployment SIZE immediately; the discount-rate channel reaches valuation gradually. Analysis and rating are never gated. [Grade B -- `ref-portfolio-doctrine`, a named vault-internal authority; not externally verifiable, and the doctrine file was not opened this pass]

### Transmission table

Sign: + = thesis benefits from a RISE in the variable. Magnitude is ordinal, not a beta. All sign/magnitude cells are [Grade D -- inference over the thesis map] unless the row is sourced below.

| Variable | Channel | theme-alpha | theme-delta | theme-gamma | theme-beta | theme-epsilon | Falsifier |
|---|---|---|---|---|---|---|---|
| Real rate `DFII10` | Discount rate on distant cash flows | strong - | strong - | moderate - | strong - | moderate - | Real rates rise; long-duration outperforms short-duration |
| Breakeven `T10YIE` | Pricing power vs. input pass-through | weak +/- | weak + | moderate + | moderate + | weak + | Breakevens widen; gross margins compress |
| Dollar `DTWEXBGS` | Revenue translation; EM export competitiveness | moderate - | moderate - | weak - | moderate - | weak - | Dollar strengthens; non-US revenue growth accelerates |
| Oil `DCOILWTICO` | Consumer purchasing power; input costs | weak - | weak - | ambiguous | weak - | moderate - | Oil spikes; cyclical earnings hold |
| Net liquidity | Marginal risk appetite; binds hardest at the speculative end | moderate + | weak + | moderate + | strong + | weak + | Liquidity contracts; highest-beta sleeve outperforms |
| Credit spread `BAMLH0A0HYM2` | Financing cost for capital-intensive buildouts | strong - | weak - | strong - | moderate - | moderate - | Spreads widen materially; no capex-plan revision |
| Labor `PAYEMS` | Aggregate demand; Fed reaction function | weak + | moderate + | weak + | weak + | moderate + | Payrolls deteriorate; broad market rises on cut expectations alone |

The dollar row carries the strongest external support. NY Fed research finds "a 10 percent appreciation of the U.S. dollar is associated with a 2.6 percent drop in real export values over the year" and that "the net export contribution to GDP growth over the year is 0.5 percentage point lower than it would have been without the appreciation and a cumulative 0.7 percentage point lower after two years" (Source: NY Fed Liberty Street Economics, 2015-07-17). [Grade A -- verbatim] Its Imperial Circle framing supplies the EM channel: "A stronger dollar therefore creates a competitive disadvantage for emerging market economies", and "These same forces will also lead to a drop in commodity prices and world trade" (Source: NY Fed Liberty Street Economics, 2023-03-01). [Grade A -- verbatim] The dollar reaches an Asia-manufactured supply chain through a channel unrelated to US demand.

Labor is the only genuinely two-sided sign: it transmits directly through demand and indirectly through the Fed reaction function back into the rate variable that binds everything. Weak payrolls are a demand negative and a rate positive at once; which dominates depends on whether the Fed is constrained by the inflation leg of its mandate -- see Section 2. [Grade D -- inference]

### The undamped-shock test (durable method)

Run at read time against a live broker pull, never inherited: **if the pull shows no explicit energy, commodity, gold, or defensive sleeve, then every negative sign in the table above is an UNHEDGED negative** -- an oil shock, a commodity squeeze, or a flight-to-safety episode transmits to the growth complex entirely undamped, because no offsetting sleeve rises against it. The mapping's severity is conditional on that test's answer, and the answer changes the moment a defensive sleeve is added or removed. [Grade D -- structural inference; conditional by construction]

If a falsifier is observed, revise the mapping here -- never override the doctrine bands.

## 15. Fed policy plumbing (GENERATED from the vault factor store)

**Provenance and method.** Every figure in Sections 15-18 is computed from
`Efforts/osanwe-v2-overhaul/_work/factors.db` (sqlite; tables `bars`, `factors`),
the same point-in-time store ingested by `tools/bulk-data-pull.py` and read by
`tools/macro-reference.py` for *macro-regime-tables* (not published). Computed 2026-08-24.
Series coverage in the store: daily factors from 2015-01-02 (SOFR from 2018-04-03;
HY OAS from 2023-08-22) to their as-of dates below. "Percentile" means rank of the
latest value within that full stored history, unless a shorter window is named.
These sections state levels and mechanics only; interpretation authority stays
with Sections 1-6 and no threshold here overrides a doctrine gate.

### Balance-sheet trajectory: WALCL

| Metric | Value | As of |
|---|---|---|
| WALCL latest | $6,745.7B | 2026-08-19 |
| Change vs 4 weeks | -$1.7B | vs 2026-07-22 |
| Change vs 13 weeks | +$32.1B | vs 2026-05-20 |
| Change vs 26 weeks | +$132.3B | vs 2026-02-18 |
| Change vs 52 weeks | +$102.1B | vs 2025-08-13 |

QT ended December 2025 (Section 2), so the weekly WALCL delta now measures the
Reserve Management Purchases regime plus noise rather than runoff. The last four
weekly deltas were -9.2B, +10.4B, +11.4B, -14.3B ($B) and the 13-week average is
+$2.5B/week -- oscillation around a mildly rising path, not a drain. The last four
weeks are net flat (-$1.7B), which is consistent with RMP cadence, not QT.

### Liquidity drain where it binds: WRESBAL bank reserves

| Metric | Value | As of |
|---|---|---|
| WRESBAL latest | $2,935.3B | 2026-08-19 |
| Change vs 4 weeks | -$126.9B | vs 2026-07-22 |
| Change vs 13 weeks | -$194.3B | vs 2026-05-20 |
| Change vs 26 weeks | -$14.5B | vs 2026-02-18 |
| Change vs 52 weeks | -$384.8B | vs 2025-08-13 |

Reserves are falling while total assets rise -- Treasury is rebuilding cash at the
Fed and absorbing the RMP. The series is noisy week to week (it has ranged roughly
$2.90T-$3.14T since January 2026), so treat single prints as noise; the 13-week
and 52-week slopes are the signal. Reserves near $2.9T against a ~$6.75T balance
sheet keep the system in ample-reserves territory, but the direction is the one
that eventually tests it.

### ON RRP drawdown state: RRPONTSYD

| Metric | Value | As of |
|---|---|---|
| Latest | $0.20B | 2026-08-21 |
| 90-day average / max | $2.41B / $26.90B | window ending 2026-08-21 |
| One year ago | $25.4B | 2025-08-21 |
| Two years ago | $321.3B | 2024-08-14 |
| Percentile in stored history (2015-) | 7.9th | computed 2026-08-24 |

The facility is dead as an active valve, confirming Section 6's finding: the
>$2.5T peak drained years ago and the residual is rounding-error scale. Net
liquidity variance therefore lives in `WALCL - TGA`, exactly as Section 6 owns it.

### Corridor position: SOFR vs policy rate

| Metric | Value | As of |
|---|---|---|
| SOFR latest | 3.63% | 2026-08-20 |
| SOFR 30-day average | 3.638% | window ending 2026-08-20 |
| FEDFUNDS effective | 3.63% | 2026-07-01 |

**IORB is NOT in the factor store**, so a true SOFR-IORB corridor position cannot
be computed here; the honest available proxy is SOFR versus the effective fed
funds rate, which sits at 0.0bp (both 3.63%). Money-market plumbing is orderly:
no funding stress premium is visible at this vintage. The store also carries the
St. Louis Fed Financial Stress Index (`STLFSI4`, latest 2026-08-14) for a
cross-check when needed.

Read-through for risk assets: balance sheet flat-to-rising, reserves draining
slowly, reverse repo empty, funding rates pinned to policy. Plumbing is not the
binding constraint today; the risk case is a continued reserve slide into a
repo-market test, which would show up first as SOFR detaching above the policy
rate -- watch that spread, not headlines.

## 16. Yen and global carry (GENERATED from the vault factor store)

Computed 2026-08-24 from DEXJPUS (yen per USD; LOWER = stronger yen).

| Metric | Value | As of |
|---|---|---|
| USDJPY latest | 159.21 | 2026-08-14 |
| 90 days ago | 158.69 | 2026-05-15 |
| One year ago | 147.69 | 2025-08-14 |
| Two years ago | 146.86 | 2024-08-14 |
| YTD change in yen terms | yen -1.6% (from 156.72) | since 2026-01-02 |
| Percentile in stored history (2015-) | 97.1st weakest | computed 2026-08-24 |
| 52-week range | 146.36 - 163.86 | window ending 2026-08-14 |

The yen sits at the 97th percentile of its eleven-year history in WEAKNESS terms,
roughly 12 yen weaker than a year ago despite BOJ policy at its highest since
1995 (Section 9). That gap is what makes carry relevant again.

**Mechanism -- why the yen carry trade is a tail risk for US equities.** Investors
borrow yen at the developed world's lowest policy rate and buy higher-yielding or
higher-momentum assets abroad, typically US equities and Treasuries. The position
is implicitly SHORT yen volatility. It unwinds mechanically: any catalyst that
narrows the rate differential or lifts the yen forces leveraged holders to buy
back yen, which strengthens it further, which forces more unwinding -- a convex
feedback loop that transmits directly into US assets because the funded leg IS
US assets. The exposure is size-dependent on positioning, not on the yen level
itself, which is why a strong-trend yen market can persist for quarters and then
reverse violently in weeks.

**Historical episode, measured from the store:** between 2024-07-10 and
2024-08-05 the yen strengthened from 161.73 to 143.95 (about -11%), VIXCLS
printed 38.57 on 2024-08-05, and global equities took one of the sharpest
drawdowns of the cycle -- the classic carry-unwind signature. Both legs are in
this factor store and re-computable.

**Live tail gauge (computed 2026-08-24):** the yen is more extended than at the
2024 unwind trigger (97th-percentile weakness now vs the 99.2nd-percentile
WEAKNESS extreme of 161.73 printed 2024-07-10 -- i.e., today sits just inside the
historical extreme zone that preceded the last unwind), while the volatility
backdrop is far calmer (VIXCLS 16.01, 44th percentile, as of
2026-08-20). Extended funding currency + calm vol = the standard pre-unwind
configuration; it is a tail, not a base case, and Section 12's matrix does not
currently carry it as a row.

## 17. Rates complex, store-computed expansion (GENERATED)

Computed 2026-08-24. Section 6 remains the sole owner of live FRED refetches;
this section adds the store's distributional context (percentiles over the full
stored history, 2015-01-02 onward).

| Series | Latest | As of | 90d ago | 1y ago | Pctile (full history) |
|---|---|---|---|---|---|
| DGS10 nominal 10Y | 4.69 | 2026-08-20 | 4.57 | 4.29 | 98.8th |
| DFII10 real 10Y | 2.35 | 2026-08-20 | 2.18 | 1.94 | 98.5th |
| T10Y3M curve | +0.86 | 2026-08-21 | 0.88 | 0.01 | 54.6th |
| T10Y2Y curve | +0.50 | 2026-08-21 | 0.43 | 0.54 | 49.0th |
| DGS30 nominal 30Y | 5.23 | 2026-08-20 | -- | 4.89 | -- |

The term structure story in three lines:

- **Level:** both the nominal and real 10Y sit in the top 2% of their
  eleven-year histories, and the 30Y at 5.23% is up ~34bp year-over-year --
  long-end-led tightness, consistent with Section 6's bear-steepening-flavored
  read. DGS10's 52-week range is 3.97-4.75%, with the six most recent closes all
  >= 4.63%; the doctrine's `halt-dgs10` band stays mechanically binding here.
- **Curve:** both spreads are positive but mid-distribution (50th-55th pctile)
  -- the curve has normalized OUT of inversion without signaling late-cycle
  flattening. 10Y-3M at +86bp sits inside the taxonomy's Mid-cycle band (50-150bp),
  corroborating Section 1's tally from the store side.
- **Decomposition check:** implied breakeven = DGS10 - DFII10 = 4.69 - 2.35 =
  2.34% at this vintage. The store carries `T5YIE` (latest 2.28%, 2026-08-21);
  the 6bp wedge between the 10Y-implied construct and the 5y5y-forward-family
  proxy reflects tenor mismatch, not bad data. Real yields carried the move
  (+41bp YoY) versus breakevens (+20bp YoY): a discount-rate event for
  long-duration equity per Section 6's decomposition rule.

## 18. Credit, store-computed expansion (GENERATED)

Computed 2026-08-24 from BAMLH0A0HYM2 (store coverage begins 2023-08-22, n=787
daily observations -- percentiles below are relative to THAT window, not to a
multi-decade history; stated so nobody inherits a false precision).

| Metric | Value | As of |
|---|---|---|
| HY OAS latest | 2.75 | 2026-08-20 |
| 90 days ago | 2.78 | 2026-05-21 |
| One year ago | 2.94 | 2025-08-20 |
| Percentile (2023-08-22 onward) | 15.1st | computed 2026-08-24 |
| Window median / p75 / p90 | 3.08 / 3.29 / 3.83 | same window |
| Window min / max | 2.59 (2025-01-22) / 4.61 (2025-04-07) | same window |
| HY option-adjusted yield (store: BAMLH0A0HYM2EY) | 7.09% | 2026-08-20 |

Distributional facts: the current 2.75 print sits BELOW every quartile of its own
three-year window and only 79 of 787 sessions have ever exceeded the window p90
of 3.83. The two prior spikes to the 4.4-4.6 zone (Oct-Nov 2023, Apr 2025) both
recovered fully within months -- widening episodes in this window have so far
been buying opportunities, a base rate that itself embeds bull-market bias.

Widening thresholds and what they would signal, anchored on this window's own
distribution rather than folklore:

| Threshold | Store frequency | Signal if crossed |
|---|---|---|
| > 3.00 (window median) | 54% of days historically | Spread leaves the tightest decile-and-a-half; early de-risking, not yet stress |
| > 3.29 (p75) | 25% of days | Compensation regime shifts; leverage trades and credit-funded capex repriced |
| > 3.83 (p90) | 79 of 787 days | Growth-scare pricing; historically paired with equity vol -- cross-check VIXCLS and STLFSI4 |
| > 4.50 | 5 days ever (Apr 2025) | Stress regime; trips the Section 12 high-yield-repricing marker |

Section 12's existing marker (`BAMLH0A0HYM2 >= 4.50`) resolves against these
same data. At 2.75 with a 15th-percentile rank, credit is priced for benign
outcomes -- the Schwab sub-3% forward-return caveat in Section 6 still governs
the interpretation, and nothing here changes a doctrine gate.

## Related

*investing-moc* (not published) | *ref-portfolio-doctrine* (not published) | [[ref-regime-taxonomy]] | [[ref-monitoring-rules]] | *ref-market-calendar* (not published) | *ref-sector-benchmarks* (not published) | *ref-geopolitical-framework* (not published) | [[ref-evidence-hierarchy]] | [[ref-briefing-structure]] | [[ref-theme-alpha]] | *ref-ai-supply-chain-deep-dive* (not published) | [[ref-ai-power-grid-deep-dive]] | *ref-theme-beta-institutional-crypto-deep-dive* (not published) | *ref-defense-aerospace-space-economy-deep-dive* (not published) | *geopolitics-playbook* (not published) | *macro-outlook* (not published)

## Sources

Inline `(Source: ...)` citations throughout; this is the deduped bibliography.

1. briefing-2026-07-14
2. U.S. Senate roll-call vote 120, 2026-05-13
3. Federal Reserve Board membership table, updated 2026-05-28
4. federalreserve.gov 2026 speech index, retrieved 2026-07-15 and again 2026-07-16
5. Warsh testimony, federalreserve.gov, 2026-07-14
6. FOMC statement, 2026-06-17
7. Hoover Institution, "Inflation Is a Choice: Kevin Warsh on Fixing the Federal Reserve", 2025-07-08
8. Wikipedia, Kevin Warsh, retrieved 2026-07-15
9. FOMC Summary of Economic Projections, Table 1, 2026-06-17
10. FOMC statements, 2026-01-28 / 2026-03-18 / 2026-06-17
11. Federal Reserve H.4.1 / FOMC materials
12. federalreserve.gov FOMC calendar, retrieved 2026-07-15
13. Atlanta Fed GDPNow methodology page, 2026, via search summary rather than a direct fetch
14. Federal Reserve Bank of New York, 2026-02-10
15. NY Fed Consumer Credit Panel/Equifax, HHDC 2025Q4 workbook
16. Wilbert van der Klaauw, NY Fed, 2026-02-10
17. NY Fed, 2026-02-10
18. BEA via FRED GDPC1, re-pulled 2026-07-16
19. ISM June 2026 Manufacturing PMI Report on Business, issued 2026-07-01 via ISM's PR Newswire release distribution; ismworld.org itself was not fetched
20. NY Fed / Federal Reserve yield-curve research, search-level attribution only; the NY Fed FAQ PDF returned HTTP 403 and could not be read
21. Charles Schwab, 2026 Corporate Credit Outlook
22. multpl.com, 2026-07-15
23. AAII Sentiment Survey, 2026-07
24. US EIA, Today in Energy no. 65504, retrieved 2026-07-15
25. Al Jazeera, 2026-07-13
26. ECB monetary policy decisions, 2026-06-11
27. aggregator tallies of company guidance, 2026-06
28. EESI, 2026
29. Sightline Climate, Data Center Outlook, 2026
30. Trepp via Multi-Housing News, 2026
31. MBA CREF loan-maturity survey, 2026
32. FSB, Report on Vulnerabilities in Private Credit, 2026
33. Federal Reserve Board FEDS Notes, 2026-04-02, citing Census
34. St. Louis Fed, 2026-03
35. Brookings/AEI, 2026-01
36. Federal Reserve, 2026-06-17; Section 2 owns the SEP
37. Federal Reserve, 2026-06-17
38. FRED DGS10; Section 6 owns the levels
39. uscode.house.gov
40. NY Fed Liberty Street Economics, 2015-07-17
41. NY Fed Liberty Street Economics, 2023-03-01
