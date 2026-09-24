# Example 1 -- an end-to-end equity analysis

> As of 2026-09-20. Published as an example of the system's output.
> Not investment advice, not a recommendation, and not a statement of anyone's positions.

A full `/invest` run that ended in HOLD/AVOID rather than a purchase. It shows the evidence grading, the bear-case pass and the falsifiers the system requires before a verdict.

**Reading guide.** The run is labelled with the names of the `/invest` procedure it followed
([`.agents/skills/invest/SKILL.md`](../.agents/skills/invest/SKILL.md)):

- **Phases.** J is portfolio fit; J.5 compares the run with earlier analyses and holds the prior-calls
  scoreboard and drift table; K-bis is the quantitative scoring and the TRADING DECISION block; K.5 is the
  thesis critic's pass, which produces the variant view and the conviction arithmetic; K-ter is the options
  layer; L updates the company's note; Q checks coherence with the rest of the book; R is the calibration
  monitor, which logs the rating the old logic would have given (the shadow rating) beside the new one.
- **FM1 to FM5** are the failure modes the critic named, each with a probability, a cascade weight (HIGH,
  MED or LOW) and whether it is detectable in time. **ITT** is the critic's own score for how fairly it
  argued the other side (an Ideological Turing Test, out of 10).
- **Grades A to F** rate each claim's source: A is a primary filing or audited financials, B tier-1
  institutional or industry primary data, C attributed third-party analysis, D sentiment or unverified
  commentary, F unverifiable. The confidence a run may state is capped by the grades it cites.
- **Topology.** `dw` (also called Tier-A) runs the research as parallel waves of subagents; `sequential`
  (Tier-B) runs the same phases one after another. **Wave-3** is an adversarial verification wave; it was
  skipped here, and in this copy it cannot run at all (see the README's limitations).
- **R/R** is reward-to-risk; a new position must clear 3:1. **GATE-F** is the trade-discipline gate run
  before any add, trim or exit. Names shown as plain text, not links, are notes that are not published.

---

<details>
<summary>Metadata the system recorded for this run</summary>

```yaml
categories:
  - wiki
type: analysis
ticker: MRVL
created: 2026-07-16
updated: 2026-07-16
status: complete
trigger: "3-day refresh of the 7/13 HOLD/AVOID at $216. MRVL down another ~20% to $188.48 live ($206.26 7/15 anchor) on a cohort-wide semis de-rate (TSMC capex-reset 7/16 + Micron-China 7/15), breaking below the prior $195 watch line INTO the air pocket the 7/13 run pre-specified. The buyable-vs-idiosyncratic crux and the improving R/R need a fresh read; the AVOID must be re-tested lower."
confidence: 70
conviction: 22
sources_count: 40
scoring_path: positive-eps-standard
rating: HOLD
price_at_analysis: 206.26
rr_ratio: "0.75:1"
position_size_pct: null
doctrine_version: "pd-1/fb-1"
doctrine_fingerprint: "pd-34ad8054/fb-48ee1308"
deployment_band: "above-4.40:0.0"
deployment_override: false
gate_f: null
kill_criteria:
  - "Aug 27 FQ2 FY27 call names a specific Trainium3-gen OR Maia200-gen COMPUTE-die win with dated volume (not attach) OR a net-new flagship compute socket -> FM1 bull-convert; reiterated >$10B FY29 custom target with NO named replacement socket OR CY26 XPU held ~+20% while AVGO custom accelerates -> FM1 bear-confirm"
  - "Two consecutive closes < $170 on cohort risk-off -> air-pocket confirmed / deep-value re-test live (price already breached the $195 watch line intraday; $170 is the next real swing-low support); reclaim + hold > $250 for 10+ sessions -> air-pocket vacated"
  - "FQ2 FY27 non-GAAP GM guide < 58.25% (below guided floor) OR DC sequential guide < +8% QoQ OR DSRI/AR expands a 3rd straight quarter -> negative-binary / quality erosion"
  - ">= 2 sell-side downgrades within 30d of the Aug 27 print (currently 1 of 2 -- Erste 7/14, no PT cut; KeyBanc raised same window) OR a fresh discretionary open-market insider sell at higher prices -> revision wave"
  - "BULL-CONVERT (staged-BUY) requires ALL THREE: (a) ~$170-179 or below on a stabilizing/reclaiming tape so R/R clears 3:1, (b) deployment band reopens (DGS10 < 4.40), (c) Aug 27 names a compute-die win not attach; OR a reclaim > $290 pre-print on interconnect + 3P-Trainium"
thesis_line: "MRVL is a genuine optical-interconnect leader and the structural #2 in custom AI silicon whose price has now reset into the deep-value re-test zone on a buyable cohort de-rate -- three of four 7/13 bear vectors have eased -- but the disciplined R/R still fails 3:1 at the $206.26 anchor, the ~40% air pocket is now open below, the custom-compute-socket question stays unresolved until the Aug 27 binary, and the DGS10 4.58% hold-cash band sizes any entry to $0: HOLD/AVOID-INITIATING, sharpened to a conditional-accumulation WATCH, not a catch here."
topology: dw
orchestrator_model: "claude-opus-4-8"
thesis:
  - theme-alpha
tags:
  - ticker/MRVL
  - thesis/theme-alpha
  - topic/custom-silicon
  - topic/networking-silicon
aliases:
  - MRVL analysis 2026-07-16
related:
  - "MRVL"
  - "mrvl-analysis-2026-07-13"
  - "mrvl-analysis-2026-06-18"
  - "AVGO"
  - "watchlist"
  - "investing-research-log"
  - "investing-moc"
  - "thesis-theme-alpha"
  - "ref-portfolio-doctrine"
  - "[[ref-theme-alpha]]"
  - "calibration-monitor"
```

</details>


# MRVL Investment Analysis -- 2026-07-16

**Date:** 2026-07-16 (Thursday; broker-authoritative anchor = $206.26 7/15 regular close; LIVE $188.48 -8.62% intraday at ~14:21 ET, broker_authoritative, displayed as-of -- today's regular session not yet closed, so ALL threshold math anchors to $206.26 per doctrine J.0b).
**Model:** Claude Opus 4.8 (/effort high) | **Topology:** dw (Tier-A; price-fetcher + forensic-scorer + institutional-positioning-scout + thesis-critic dispatched as direct parallel research legs; claim-distributor at Phase L). Executed as a 3-day refresh scope, not the full 13-WebSearch spine.
**Analysis Depth:** institutional refresh (40 sources / 12+ domains this run, leveraging the mrvl-analysis-2026-07-13 42-source baseline; 4 mandatory subagents dispatched + a live broker read + FRED macro + EDGAR primary). Refresh of mrvl-analysis-2026-07-13 (3d prior; FRESH) and mrvl-analysis-2026-06-18.

## TRADING DECISION

**Rating**: **HOLD** -- AVOID INITIATING at $188.48 (live) / $206.26 (7/15 anchor). Three of four bear vectors from 7/13 have genuinely eased -- positioning de-escalated, valuation reset further, and the drop is confirmed cohort-driven (buyable-kind) not idiosyncratic -- and the name has fallen INTO the deep-value re-test zone the 7/13 run pre-specified. But the disciplined R/R still fails 3:1 at the anchor (0.75:1), the ~40% air pocket is now open below (support broke at 201-206; next real support ~$170 then ~$158), the custom-compute-socket question stays unresolved until the Aug 27 binary, and the DGS10 4.58% hold-cash band sizes any entry to $0. The correct evolution is a SHARPER, conditional-accumulation WATCH -- not a buy.
**Action**: **Do NOT initiate at $188.48.** WATCH (conditional-accumulation). No live order -- the deployment band is 0.0x (DGS10 4.58% > 4.40 hold-cash line), so any entry sizes to $0 regardless of conviction, and the Aug 27 FQ2 FY27 print is an unresolved binary. Convert WATCH -> staged-BUY only on ALL THREE together: (a) ~$170-179 or below on a stabilizing/reclaiming tape (R/R clears 3:1), (b) the deployment band reopens (DGS10 < 4.40), (c) the Aug 27 print names a specific compute-die win (not Ethernet/attach) or a net-new flagship socket. Absent all three, WATCH. If capital must deploy now, a diversified index fund or the cheaper ~77.5%-GM custom-silicon leader AVGO -- both dominate a MRVL initiation here, and a MRVL add is redundant cohort beta on any already-concentrated theme-alpha book.
**Confidence**: 70% (Grade-A EDGAR forensics + broker-authoritative price + FRED macro + Tier-A insider Form-4; capped at 70% by material Grade-C reliance on the socket-erosion analyst channel checks (Alchip/Global UniChip/SemiAnalysis), the ~20-25% custom-ASIC share figure, and the consensus PT that drive the moat + valuation read). Drops to ~50% if the Aug 27 print names a compute-die win (the AVOID would look too cautious); rises to ~85% if a 2nd downgrade + a soft custom-XPU guide confirm socket erosion.
**Conviction**: 22% (conviction_base 60 minus 38.36 K.5 failure-mode penalty across 5 modes; not floored. LOW -- appropriately, and DOWN from 28% on 7/13: this is now a genuinely close, mechanically-gated call. The AVOID is held by three Grade-A gates (R/R, deployment band, open air pocket + unresolved binary), not by a conviction that the business is bad. Separate from confidence per Quality Standards).
**Time Horizon**: 12mo; rating reviewable at the FQ2 FY27 print (Aug 27, 2026 expected -- the customer-concentration binary, FM1/FM3).
**Risk/Reward**: **~0.75:1** at the $206.26 anchor (target = MIN(model, analyst median $242.50) = $242.50, +17.6% over the close; stop = $158 nearest real swing-low support, -23.4%, inside the 25% doctrine cap of $154.70). At the live $188.48: **~1.77:1** (target $242.50 +28.7% / stop $158 -16.2%). **FAILS the 3:1 BUY hurdle** at the anchor by ~4x; below the 2:1 rejected-as-BUY floor at the anchor. The R/R has IMPROVED materially vs 7/13 (0.33:1) as the price fell -- BUY-eligibility on R/R alone arrives near ~$179 -- but "close" is not "cleared," and the anchor basis still fails.
**Composite Quality Score**: 68/100 (forensic 70 quality-strong/priced-for-perfection + framework 66 Lynch-borderline-PASS; weighted 50/50). Unchanged vs 7/13's 68 -- the valuation sub-leg improved with the -13% price move (PEG ~1.0 now clean-passes Lynch, EY 0.84% up from 0.73%), but not enough to round the composite up. Squarely in the BUY band, R/R-demoted to HOLD (the AVGO-precedent mechanism, per ref-portfolio-doctrine).
**Scoring path**: positive-eps-standard (TTM GAAP operating income positive all 4 trailing quarters; forward-earnings bridge INERT; NBIS-trap check PASSED -- GAAP NI positive but inflated by the one-time +$1,830.4M disposition gain, op-income stands on its own; SOLVENCY-RUNWAY GATE inert).

**Summary**: Marvell is the structural #2 in custom AI silicon and a genuine leader in 1.6T optical interconnect, with real numbers -- FY27 guide ~$11.5B/+40%, FY28 ~$16.5B/+45%, data center 76% of revenue, an NVIDIA $2B strategic alignment, and clean forensics (Altman Z 12.1 SAFE, Greenblatt ROC ~60% top-decile, filing integrity CLEAN, no new SEC filing 7/13-7/16). Since the 7/13 AVOID at $216 the stock has fallen another ~13-20% to $188.48 -- and today's -8.6% is decisively COHORT-driven (TSMC's 7/16 capex-reset triggered an AI-capex-digestion / multiple-compression scare across the whole semis complex: SOXX -4.4%, AVGO -4.3%, AMD -6.0%, ARM -6.7%; VOO only -0.4%, VIX 16), amplified ~2x because MRVL is the highest-multiple, highest-beta name. Three of four 7/13 bear vectors eased: positioning DE-ESCALATED (the insider kill-criterion is NOT tripped -- the only new post-6/23 Form 4 is a mechanical 10b5-1 sale; the "$65M CFO sale" was a holdings misread; SI 3.90% and falling), valuation reset further (PEG ~1.0, median PT $242.50 now +28.7% ABOVE live), and the drop is the buyable cohort kind. But the AVOID holds on three Grade-A gates: R/R still fails 3:1 at the $206.26 anchor (0.75:1), the ~40% air pocket is open (support broke, next real floor ~$170 then ~$158, SMA200 $129), and the DGS10 4.58% hold-cash band sizes any entry to $0 -- with the dominant structural risk (custom-compute-socket erosion: Trainium3/4 reportedly to Alchip, Maia200 to Global UniChip per Grade-C channel checks) still unresolved until the Aug 27 binary. HOLD / AVOID INITIATING -- the pullback the prior analysis anticipated has arrived and the business is excellent, but the disciplined move is a conditional-accumulation WATCH: build only on the ~$170-179 R/R-clear + a band reopen + an Aug-27 socket-resolution, not initiation at $188 into a multiple-compression regime that structurally targets this exact 1%-FCF-yield profile.

### Framework Rotation Audit (Phase K-bis)

**Category**: Fast Grower (semis, +40% FY27-guide revenue growth, GARP-priced -- after the further ~13% de-rate the "RP" has returned more)
**Primary Framework**: Lynch (fast grower) -- **3.5/5, borderline PASS** (PEG ~1.0 now comfortably PASSES the <=1.5 ceiling -- down from 1.47 on 7/13 and 1.67 on 6/18, driven entirely by the price reset against ~42% EPS growth; EPS growth PASS; debt low-but-rose-for-M&A PARTIAL; explainable business PASS; AR +112% vs rev +42% DSO-expansion quality flag PARTIAL)
**Secondary Framework**: Greenblatt (magic formula) -- 2.5/5 (ROC ~60% top-decile PASS, but EBIT/EV earnings yield 0.84% bottom-decile FAIL; the two-factor screen still FAILS on the rich EV vs the operating-EBIT base -- though EY improved from 0.73% at $216)
**Tertiary Framework**: Cohen (catalyst) -- 4.0/5 (FY27/FY28 guide RAISED + KeyBanc PT hike $385->$400 on 7/14 = upward-revision momentum PASS; Aug 27 print + Trainium ramp + Celestial-AI/XConn photonics/CXL closes + NVIDIA milestones = catalyst calendar PASS; semis-inflection PASS; but the tape is mid-de-rate, -43% off the high)
**Composite Quality Score**: 68/100 (framework-rotation 66 [0.5x70 Lynch + 0.3x50 Greenblatt + 0.2x80 Cohen] reconciled 50/50 with forensic-quantitative 70)
**Forensic-Scoring Agreement**: Piotroski 7/9 (8/9 ex-gain); Altman Z 12.1 SAFE; Beneish M -1.60 raw / -1.92 adj GREY (DSRI 1.50 AR flag) -- forensic QUALITY agrees BUY-ish, forensic VALUATION (EY 0.84%, FCF yield ~1.0%, EV/EBIT ~119x) agrees AVOID; the two legs split exactly on quality-vs-price, the entire thesis. No material disagreement (forensic 70 vs framework 66 = 4pt spread, well under the 30pt bar).
**Reconciliation**: Both legs independently conclude high-quality business, price with thin-to-no margin of safety even after the de-rate. Directional read HOLD, gated to AVOID-INITIATING by the failed R/R and the open air pocket.

## Thesis Statement

Marvell is a genuine secular winner in the durable layer of the AI buildout -- 1.6T optical interconnect, SerDes/electro-optics, scale-up switching, CXL memory-fabric, and hyperscaler custom-ASIC co-design -- and the raised FY27/FY28 guide is real because the INTERCONNECT engine (guided +70%) is carrying it regardless of which vendor owns the compute dies. The 2026-07-16 question is not whether the market underrates the business; it is whether, at $188 after a two-week ~40%-off-the-high de-rate, the still-open air pocket to the ~$129 SMA200 and a still-unresolved custom-compute-socket erosion (Trainium3/4 reportedly to Alchip, Maia200 to Global UniChip per Grade-C channel checks) justify catching a 2.8-beta, 1%-FCF-yield name into a multiple-compression regime that structurally targets exactly that valuation profile, with a binary Aug 27 print ahead. The disciplined answer is to own the theme-alpha thesis through cheaper, higher-margin vehicles and hold a SHARPENED conditional-accumulation WATCH: build only on the ~$170-179 R/R-clear + a deployment-band reopen + an Aug-27 socket-resolution.

## Variant View (thesis-critic K.5; ITT 8/10; conviction modulation auditable)

The differentiated BULL variant (FM5, ~35% probability -- the WAIT-NO-LONGER read): the drop is demonstrably cohort/technical, not idiosyncratic -- no MRVL-specific 8-K, no fresh socket headline, no customer-loss break, just the whole semis complex red on TSMC read-through (SOXX -4.4%, AVGO -4.3%, AMD -6.0%). This is the buyable kind of drop, and the sell-side agrees: median PT $242.50 (+28.7% above live), 43 analysts at 30 Strong-Buy/7 Buy/6 Hold, and in the last three days KeyBanc RAISED to $400 against a single no-PT-cut downgrade (Erste). The one bear leg that was hardening on 7/13 -- insider distribution -- has collapsed on inspection (kill-criterion NOT tripped; only new post-6/23 Form 4 is a mechanical 10b5-1 sale; SI 3.90% falling). The business is clean and compounding (Altman Z 12.1, ROC ~60%, GM +177bps 4Q, net-debt/EBITDA 0.42x, composite 68 BUY-band), the durable interconnect engine (+70%) carries FY27/FY28 regardless of the compute dies, and the name is down 43% off its high in the accumulation zone the prior analysis pre-specified. This is genuinely differentiated and it is the real cost of AVOID.

It is dominated, though, on three Grade-A grounds -- and this is the honest adjudication: (1) the very catalyst lowering the price -- the TSMC-led, FCF-focus multiple-compression regime -- is the structural MRVL-killer; a ~1%-FCF-yield, 2.8-beta name is the cohort's maximum-exposure name to exactly this de-rate, so "buyable cohort drop" understates the risk for THIS name (the cohort catalyst IS the idiosyncratic-valuation risk). (2) The R/R still fails 3:1 at the anchor (0.75:1) and the deployment band sizes any entry to $0. (3) The socket crux rides a coin-flip binary six weeks out with a ~40% air pocket and no valuation floor beneath it. Variant acknowledged; the setup has genuinely improved and the STANCE sharpens from static-avoid to conditional-accumulation WATCH -- but the verdict does not flip to BUY.

**Conviction modulation (deterministic, auditable):**
- conviction_base = 60 (composite 68 BUY-band; R/R deeply negative vs hurdle at the anchor -> supports AVOID; the valuation reset + genuine two-sidedness cap the base)
- FM1 socket-erosion: 0.55 x 40 (HIGH cascade, thesis-structural crux) x 0.70 (detectable Aug 27) = 15.40
- FM2 multiple-compression / air-pocket: 0.50 x 40 (HIGH cascade -- UPGRADED from MED on 7/13: the TSMC regime now actively drags the whole theme-alpha cohort -- the largest cohort-wide cascade this analysis models) x 0.70 = 14.00
- FM3 Aug-27 negative-binary: 0.40 x 20 (MED) x 0.70 = 5.60
- FM4 insider->revision wave (DE-ESCALATED from 7/13's 40%): 0.25 x 8 (LOW) x 0.70 = 1.40
- FM5 melt-up (Type-II, opportunity-cost only): 0.35 x 8 (LOW) x 0.70 = 1.96
- Total penalty 38.36; behavioral penalty 0 (no GATE-F / no FOMO-SUSPECT gate run on a HOLD)
- **conviction = 60 - 38.36 = 21.64 -> 22%** (not floored at 20; down from 28% on 7/13 as the AVOID became more marginal)

## Mispricing Decomposition

There is still no clean long-side edge, but the balance has shifted toward two-sided. Constructive (stronger than 7/13): the consensus median PT $242.50 now sits +28.7% ABOVE the live spot (mean $252.56, 43 analysts, 30 Strong-Buy / 7 Buy / 6 Hold, zero Sell), PTs are UNCHANGED-to-UP through a -20%-in-a-week price move (KeyBanc raised to $400 7/14), and the valuation screens have compressed with the price (PEG ~1.0, EY 0.84%, fwd non-GAAP P/E ~42-46x from ~48x). Bearish (also stronger): the chart broke the 201-206 shelf into a confirmed air pocket with nearest real support ~$170 (-9.7%) then ~$158 (-16%) then the $128.80 SMA200 (~-32%), and the multiple-compression regime that opened today is precisely the one that targets a 1%-FCF-yield profile. The custom-compute-socket moat question is unchanged-unresolved (no fresh data this week -- the drop was macro, not socket). Net: the stock is now held between a real +28.7% median-PT upside and a real ~16-32% air-pocket downside with a binary print between them -- a genuinely two-sided setup that resolves to WATCH, not a decisive long. If anything is mispriced it is still the DURABILITY of the #2-vendor custom-ASIC margin premium against a customer base whose entire reason to go custom is to escape vendor margin -- a SHORT-side question, not a long-side edge, and not one to express on a clean-forensic, 2.8-beta name.

## Business Model and Competitive Position

Marvell designs custom AI accelerators (XPUs/ASICs) co-developed with hyperscalers PLUS the high-speed connectivity that stitches AI racks together: 1.6T optical DSPs, SerDes/electro-optics IP, scale-up/scale-out switching, CXL memory-fabric (post the $540M XConn acquisition), and silicon photonics (the Celestial AI acquisition). Data center is 76% of revenue ($1.833B of $2.418B in FQ1 FY27, +27% YoY) [Grade A | EDGAR FQ1 FY27 10-Q].

The moat read is UNCHANGED vs 7/13 (no fresh socket data this week): NARROWING on the compute dies, WIDENING on interconnect. Grade-C analyst channel checks (Benchmark/Cody Acree Buy->Hold 2025-12; BNP Paribas; SemiAnalysis "AWS Trainium3 Deep Dive") report the Trainium3/4 backend went to Alchip (root cause: MRVL's own Trainium2 execution problems -- RDL interposer, timeline slip; PCIe SerDes reportedly licensed from Synopsys) and the Maia 200 main die is likely Global UniChip with MRVL relegated to Ethernet-ASIC attach -- so on two of three flagship logos MRVL is reportedly moving from compute-die owner to attach supplier [Grade C | SemiAnalysis / Benchmark / BNP via search | 2026-06/07]. Management's guide was nonetheless RAISED because interconnect (+70% guided) is the real engine and a genuine MRVL moat; XPU was guided only ~+20% CY26, and management is silent on the contested CY27/CY28 2nm node. GAAP gross margin ~51.5% TTM sits ~17-19pp below AVGO's ~77.5% -- a direct quantification of the weaker pricing power of the #2 [Grade A | EDGAR FY26 10-K + FQ1 FY27 10-Q]. NVIDIA's $2B strategic collaboration (custom-XPU co-dev + scale-up chiplet + silicon photonics; convertible-preferred converts ~21.78M sh at $91.84, deep in-the-money) deepens the ecosystem tie. Honest 2026-07 label: interconnect/optical LEADER + custom-ASIC ATTACH provider, with the "structural #2 custom silicon" tag partially eroding pending the Aug 27 print.

## Valuation

Rich but progressively reset -- three consecutive analyses have watched the multiple compress with the price (price basis: $188.48 live / $206.26 anchor; mcap ~$165B live / ~$181B anchor):
- Forward non-GAAP P/E ~42-46x (was ~48x at $216 on 7/13, ~64x at $289 on 6/18); trailing GAAP P/E ~65x reported is UNDERSTATED (the one-time gain inflated EPS -- ex-gain GAAP P/E ~170x); do not value on headline GAAP.
- EV/Sales ~14x TTM (was ~16x / ~22x); EV/EBIT ~119x; EV/EBITDA ~70-81x; P/B ~9x.
- FCF yield ~1.0% (was 0.98% / 0.73%) -- still bottom-decile, below MRVL's own 5Y avg 1.84%; Greenblatt earnings yield 0.84% (was 0.73% / 0.55%).
- PEG ~1.0 (fwd P/E ~42-46x over ~42% growth) -- now comfortably UNDER the Lynch 1.5 ceiling (the clean pass).
- Target basis for the R/R gate = MIN(model fair value, analyst median $242.50) = $242.50; the median is +17.6% over the $206.26 close (+28.7% over the live $188.48). The high end ($385) is the bull case, not the doctrine target basis.

Buffett-compounder BORDERLINE-FAIL (~6% reported ROIC on total capital, ~$3.7B stock issued for FQ1-FY27 M&A, SBC 7.5%, zero absolute margin of safety), Lynch borderline PASS (PEG ~1.0), Greenblatt FAIL (top-decile ROC, bottom-decile EY), Burry FAIL (expensive on every absolute metric even -43% off the high). Three of four fail on price; the quality is conceded by all four.

## Forensic Screen and Quality Scorecard (forensic-scorer, K-bis.0 DISPATCHED)

Strong and clean; the valuation is the only problem, and it improved with the price. No new periodic filing since 7/13 (latest 10-Q = FQ1 FY27; next print 8/27); no new 8-K 7/13-7/16 (verified: MRVL absent from the full 8-K feed):
- Piotroski F 7/9 reported (8/9 ex-gain) [Grade A | 10-K FY26 vs FY25] -- the reported miss is the accrual test (CFO $1,750.5M < GAAP NI, which embeds the gain) + the leverage test (debt $4.06B -> $4.47B); ex-gain the operating quality is strong-tier.
- Altman Z 12.1 -- SAFE (fortress; no distress; ~13.83 on 7/13 -- the move is live-cap/EV re-mark, both SAFE).
- Beneish M raw -1.60 FLAG / **adjusted -1.92 GREY** -- the flag is benign drivers (the +$1,830.4M disposition gain spikes TATA; SGI 1.42 on +42% revenue; DSRI 1.50 on AR +112% vs rev +42%, DSO ~65 -> ~97d at FY26 close, eased to ~78d by FQ1'27), NOT fraud (GMI 0.81 / AQI 0.83 argue against manipulation). Still not <-2.22 clean purely because of hyper-growth + gain optics; DSRI 1.50 AR/DSO flag is the live quality-watch.
- Greenblatt ROC ~60% ex-cash top-decile (asset-light fabless); ROIC ~6.1% reported / ~21.7% ex-goodwill -- the gap is the ~$13.9B serial-M&A goodwill (Cavium/Inphi lineage + the FQ1-FY27 stock+cash deal that pushed goodwill $11.1B -> $13.9B).
- FCF yield ~1.0%; SBC 7.5% of revenue (5-10% band; FQ1'27 SBC $207.6M vs ~$142-153M prior -- watch-item on the acquisition RSU assumption); GM trend EXPANDING +177bps over 4Q (50.4% -> 52.2%); capex/rev ~4.5% (fabless-light); net debt/EBITDA 0.42x (gross 1.86x); accruals +2.0% reported / -4.6% ex-gain CLEAN.
- **Filing integrity CLEAN** [Grade A | EDGAR]: no NT-10-K/10-Q, no Item 4.02 non-reliance, no Item 4.01 auditor change; the 8-K 2026-07-09 is the benign 424B7 XConn-resale registration (no proceeds); NO new MRVL 8-K 7/13-7/16 -> today's drop has zero company-specific filing behind it. **No confidence cap applied on filing integrity.**

## Technicals and Momentum (price-fetcher; script:technicals as-of 7/15, live 7/16)

The materialized 7/13 risk -- the air pocket is now open. As-of the $206.26 7/15 close: SMA50 $234.66 (price -12.1%), SMA200 $128.80 (price +60.1% -- the stock ran off a $61.44 52wk low), golden cross intact, RSI-14 39.1 (live ~35.6 -- NOT yet <30 oversold, room to fall), MACD deeply bearish (line -7.69 << signal +1.76, histogram -9.45), 63d annualized vol 107.7% (extreme), beta 2.82 (SPY) / 2.2 (yfinance), max drawdown -34.82% to the 7/15 close (-40.4% to the live $188.48; peak 2026-06-04), 52wk high $329.88 (6/18) off -37.5% (close) / -42.9% (live).
**Support/resistance (the crux, live 188.48) [prov script:price-fetcher supplement]:** MRVL broke BELOW the 201-206 shelf (7/15 low $201.22 + prior close $206.26 now OVERHEAD resistance); the SMA50 $234.66 is heavier overhead. Below, the nearest supports are the 4/24 former-high shelf ~$170.84 (-9.4%), then the 5/12 swing low ~$157.96 (-16.2%), then ~$146.85 (-22.1%), then the $128.80 SMA200 (~-32%). This is a thin, near-vertical zone (the Apr-Jun melt-up transited it almost without stopping), which is why a stop placed at real support (~$158) is ~-16% away -- inside the 25% doctrine cap but wide, and precisely why the R/R fails even after the drop.
**Correlation:** MRVL against the comparison set: all pairwise correlations < 0.7 -- MRVL is the least-correlated name in the set at the daily-return level (a diversifier of daily noise). NOTE: low daily-return correlation does NOT equal factor diversification -- see Phase Q (the TSMC de-rate today dragged the whole semis cohort, confirming the factor-identity read dominates in a stress event).

## Management and Governance

CEO Matt Murphy. **Insider signal DE-ESCALATED vs 7/13 (HIGH-confidence reversal)** [Grade A | SEC Form 4]: the ONLY new post-6/23 filing is COO/Pres Chris Koopmans' 7/01 sale (10,000 sh @ $281.92 = $2.82M), CONFIRMED 10b5-1 (plan adopted 2026-01-05), routine monthly cadence (4/06, 5/01, 6/01, 7/01) -- NOT the fresh discretionary top-tick sell the kill-criterion was hunting. The sole genuinely discretionary sale remains Durn's small 6/23 print ($632K, new-CFO liquidity). The 7/13 "outgoing CFO Meintjes ~$65M sale" was a MISREAD -- ~$65M is the value of his remaining ~226,675-share stake at June prices, not a transaction (his actual Form-4 sales were $4.02M on 4/15 + $701K on 5/15). Trailing 6mo: 18 sells / 0 open-market buys / ~$38.3M gross, but the C-suite sells under Dec-2025/Jan-2026 10b5-1 plans (calendar timing near the highs, not top-calling). Short interest 3.90% (6/30), DTC ~1.0, -13.3% off the 6/15 peak, off the threshold list, no FTD pressure -> no conviction-bearish positioning. Governance-independence watch persists (Durn, ex-Audit-Committee-Chair, took the CFO seat during an AI ramp with expanding DSO) -- a continuity/quality watch item, not a defect; filings clean.

## Catalysts

- **FQ2 FY27 print -- Aug 27, 2026 (Thu), EXPECTED (stockanalysis.com / StockStory; not yet company-confirmed) -- the binary.** Q2 guide $2.70B +/-5% (~+35% YoY), non-GAAP EPS $0.93 +/-0.05, non-GAAP GM 58.25-59.25%. The market needs DC re-acceleration AND a named multi-year / compute-die PO to kill the socket-loss narrative [Grade B | Marvell IR | 2026-05-27].
- **Custom TAM + roadmap:** >50 custom-XPU designs across >10 customers; Reuters: custom-chip revenue targeted >$10B by FY29; Amazon exploring 3rd-party Trainium sales with MRVL as lead design/mfg partner (TAM expansion) [Grade B/C | Reuters + Bloomberg/VivaTech | 2026-06].
- **M&A closes:** Celestial AI (silicon photonics) + XConn (CXL memory-fabric) integrate the optical/memory-fabric roadmap; NVIDIA $2B collaboration milestones [Grade A | SEC 424B7 + 8-K].
- **Analyst momentum (last 3 days):** KeyBanc PT RAISE $385 -> $400 reaffirm Overweight (7/14); Erste DOWNGRADE Buy -> Hold, no PT cut (7/14, on stretched valuation + ~82% top-10-customer concentration) -- 1 of the 2-downgrade kill-criterion, NOT tripped [Grade B/C | stockanalysis analyst actions | 2026-07-14].
- **Product:** Teralynx T100 102.4 Tbps AI switch; S&P 500 inclusion landed 6/22 (passive bid) [Grade B].

## Risks (thesis-critic K.5 failure modes)

- **FM1 -- custom-compute socket erosion (55%, the dominant thesis risk; UNCHANGED -- no fresh data this week).** [Grade C | SemiAnalysis/Benchmark/BNP | 2026] Trainium3/4 backend reportedly to Alchip (root cause MRVL Trainium2 execution) and Maia200 main die to Global UniChip -> MRVL relegated to attach on 2 of 3 flagship logos; the >$10B FY29 custom target now needs NET-NEW sockets. Detectable HIGH (Aug 27 call), recoverability LOW for the terminal bull case, MED for the stock (interconnect +70% carries FY27/FY28). Counter: AWS multi-gen supply agreement, RBC "key supplier >50% SAM," NVIDIA $2B.
- **FM2 -- multiple-compression regime through the air pocket (50%; cascade UPGRADED to HIGH).** [Grade A | TSMC via Reuters/StockStory | 2026-07-16] The TSMC capex-reset ($60-64B from a $56B ceiling; "focus shifts to cash generation") opened an FCF-focus de-rate that structurally targets MRVL's 1%-FCF-yield, 2.8-beta profile. $201-206 broke; nearest real support ~$170 then ~$158, no floor to $129 (-32%); RSI 35.6 not oversold. This is a sector-wide cascade -- it drags the semis cohort whether or not MRVL is touched. R/R ~0.75:1 at the anchor.
- **FM3 -- Aug 27 FQ2 negative binary (40%).** Flat ~59% GM guide (vs AVGO ~77.5%), DSRI 1.50 AR/pull-forward flag (3rd straight DSO expansion would confirm), or a soft custom-XPU guide -> single-print 15-25% gap through the open air pocket; earnings-confounded IV means it cannot be cheaply hedged. Counter: Q2 outlook reaffirmed 6/11.
- **FM4 -- insider distribution -> revision wave (25%; DE-ESCALATED from 40% on 7/13).** Kill-criterion NOT tripped (only new Form 4 is Koopmans 7/01 10b5-1); the "$65M CFO sale" was a holdings misread; SI 3.90% and falling; 1-of-2 downgrades (Erste) against a KeyBanc raise. The bear leg that was hardening on 7/13 has genuinely weakened. Watch for a 2nd downgrade into the print.
- **FM5 -- Type-II (HOLD too cautious), cohort melt-up (35%).** See Variant View. Opportunity cost only; doctrine sizes any entry to $0.
- **Macro / beta.** Beta 2.8; a rate/sector risk-off hits MRVL ~2.8x the market. DGS10 4.58% (>4.40 hold-cash band; 4 of last 5 sessions >4.50 -- toward the sustained-5 absolute regime-halt line), VIX 16.3 benign.

## Kill Criteria (bull-case invalidation + monitoring thresholds; from the K.5 failure modes)

- **Aug 27 FQ2 FY27 call names a specific Trainium3-gen OR Maia200-gen COMPUTE-die win with dated volume (not attach)** OR a net-new flagship compute socket -> FM1 bull-convert. Reiterated >$10B FY29 custom target with NO named replacement socket, OR CY26 XPU held ~+20% while AVGO custom accelerates -> FM1 bear-confirm.
- **Two consecutive closes < $170 on cohort risk-off** -> air-pocket confirmed / deep-value re-test live (price already breached the $195 watch line intraday; $170 is the next real swing-low support). Reclaim + hold > $250 for 10+ sessions -> air-pocket vacated.
- **FQ2 FY27 non-GAAP GM guide < 58.25%** (below the guided floor) OR DC sequential guide < +8% QoQ OR DSRI/AR expands a 3rd straight quarter -> negative-binary / quality erosion.
- **>= 2 sell-side downgrades within 30d of the Aug 27 print** (currently 1 of 2 -- Erste 7/14, no PT cut) OR a fresh discretionary open-market insider sell at higher prices -> revision wave.
- **BULL-CONVERT (staged-BUY) requires ALL THREE:** (a) ~$170-179 or below on a stabilizing/reclaiming tape so R/R clears 3:1, (b) the deployment band reopens (DGS10 < 4.40), (c) Aug 27 names a compute-die win (not attach); OR a reclaim > $290 pre-print on interconnect + 3P-Trainium.

## Position Sizing and Portfolio Fit (Phase J)

**No position is modelled for this name** -- position state is established at run time by a live broker read, never assumed. **Position-sizing worksheet SKIPPED** (K-bis.7): the no-position HOLD/AVOID path -> no BINDING or HOLD-STATE sizing. Even hypothetically the edge is negative (R/R fails 3:1 at the anchor) so Half-Kelly returns ~zero, AND the deployment band is 0.0x (DGS10 4.58 hold-cash) so any entry sizes to $0 regardless. **Best alternative use of capital (priced live 7/16):** VOO $690.40 (-0.5%; a diversified index alternative outside the theme) or the cheaper ~77.5%-GM custom-silicon LEADER AVGO $376.81 (-4.4%; itself down in the same de-rate, so a cheaper entry into the leader) -- both dominate a MRVL initiation at $188.48. R/R hurdle FAILED (0.75:1 anchor << 3:1) -> not a BUY by construction. No tax-lot pass (that pass fires only on a trim or exit).

## Cross-Position Coherence (Phase Q)

- theme-alpha effective concentration is read at run time and checked against the interim 50% amber phase-in through ~2026-09-08 (60% target amber / 70% red); this document states no level. A sector-wide de-rate moves a concentration ratio's numerator and denominator together (the semiconductor complex fell with MRVL that session, roughly -2% to -6% across large-cap names), so the ratio is not materially moved by this event; a full reprice belongs to /networth and is not decision-relevant to an AVOID.
- Post-recommendation (AVOID INITIATING): **UNCHANGED** -- the verdict adds nothing to the cohort. Compliant.
- A hypothetical MRVL add would be REDUNDANT cohort beta, not a diversifier: the factor lens reads MRVL as the same growth-momentum semis factor as the large-cap semis complex. MRVL's low pairwise daily-return correlation to the rest of the cohort (0.17-0.49) is a daily-NOISE diversifier only -- today's TSMC de-rate dragged the whole semis complex simultaneously (MRVL -8.6% alongside SOXX -4.4%), confirming the factor-identity read dominates the low-correlation read in exactly the stress event that matters.
- **Doctrine-ceiling verdict: COMPLIANT (no action).** Q is informational; it reinforces the AVOID.

## Inconsistencies vs Prior Research (Phase J.5) + PRIOR CALLS SCOREBOARD

**PRIOR CALLS SCOREBOARD** (mechanical extraction; newest first):

| date | rating | price_at_analysis | ret_3mo | verdict |
|---|---|---|---|---|
| 2026-07-13 | HOLD | 235.81 | open (3d elapsed; -12.5% to $206.26 close / -20.1% to $188.48 live) | n/a (HOLD -> n/a per RATING_PROB_MAP; tracking correct) |
| 2026-06-18 | HOLD | 289.54 | open (28d elapsed; -28.7% to $206.26 / -34.9% to $188.48) | n/a (HOLD -> n/a; informally VINDICATED -- AVOID-at-$289.54 is -35% in 28d) |

Both prior AVOID-INITIATING calls are tracking correct (stock -20% since 7/13, -35% since 6/18) -- a clean, consistent calibration signal for the R/R-gate + hold-cash-band discipline. Neither is yet at the 3mo realization horizon; the MECHANISM-VALIDATED window remains open.

**Drift table (3-day window):**

| Date | Prior Source | Prior Claim | Current Finding | Drift | Severity | Action |
|---|---|---|---|---|---|---|
| 2026-07-13 | mrvl-analysis | HOLD/AVOID @ $216 live/$235.81; R/R 0.33:1; median PT $240 (+11% above live) | HOLD/AVOID @ $188.48/$206.26; R/R 0.75:1 anchor / 1.77:1 live; median PT $242.50 (+28.7% above live) | Price -12.5%/-20%; R/R IMPROVING; PT-upside widened | Material | Confirm AVOID; note improving setup + air pocket materialized |
| 2026-07-13 | mrvl-analysis | Both CFOs selling; Durn 6/23 discretionary; "$65M CFO sale" | DE-ESCALATED: only new Form 4 is Koopmans 7/01 10b5-1 (mechanical); "$65M" was a holdings misread; SI 3.90% falling | Positioning eased materially; FM4 40% -> 25% | Material | Risks/Recent/Management update |
| 2026-07-13 | mrvl-analysis | Drop framed cohort de-rate (Samsung/DeepSeek/rates) | Cohort de-rate CONFIRMED + pinned to TSMC capex-reset (7/16) + Micron-China (7/15); semis complex red; no MRVL idiosyncratic catalyst | Crux RESOLVED: cohort-driven, buyable-kind | High | Confirm "buyable" framing; caveat the catalyst IS a multiple-compression regime |
| 2026-07-13 | mrvl-analysis | PEG 1.47; fwd P/E ~48x | PEG ~1.0; fwd P/E ~42-46x | Valuation eased further with price | Minor | Confirm value-screen improvement |
| NEW | -- | Aug print "~late Aug" | Aug 27, 2026 (dated; stockanalysis/StockStory; not yet company-confirmed) | Date precision | -- | Catalysts |

## Contradictory Sources (steel-manned bull; thesis-critic ITT 8/10)

The strongest bull is now stronger than 7/13: the drop is cohort/technical not idiosyncratic (TSMC capex-reset, whole complex red, no MRVL-specific catalyst); the median PT $242.50 sits +28.7% above spot with PTs UP through the fall (KeyBanc $400); the insider-distribution leg collapsed on inspection (kill-criterion not tripped, mechanical 10b5-1, SI falling); interconnect (+70%) carries FY27/FY28 regardless of the compute dies; forensics are clean (Altman 12.1, ROC ~60%, integrity CLEAN); PEG ~1.0; and the name is -43% off its high in the accumulation zone the prior analysis pre-specified. The honest concession: if the Aug 27 print names a compute-die win + multi-year POs, this AVOID looks too cautious and the missed upside is ~30-50%. It still resolves to AVOID-INITIATING because that bull outcome is ~35%, dominated by the FM2 multiple-compression cascade (50%, HIGH) + the unresolved FM1 socket (55%) with far worse recoverability if bought at spot, the R/R fails 3:1 at the anchor, and the hold-cash rate band sizes any entry to $0.

## Open Questions

- Does the Aug 27 FQ2 print disclose a named Trainium3/Maia200-generation COMPUTE-die win (not attach), or confirm MRVL is now the attach/interconnect supplier on those logos? (The dispositive FM1 question.)
- Does the TSMC-led multiple-compression regime deepen (a further leg toward the ~$158-170 support / SMA200 $129), or V-reclaim as the June AVGO-led rout did? (The FM2 timing/depth question.)
- Does DSO normalize (DSRI < 1.0) next quarter, or does AR keep outpacing revenue post the CFO transition? (Quality-of-earnings watch.)
- Does a 2nd sell-side downgrade land within 30d of the print (tripping the revision-wave kill-criterion), or do PTs hold/rise as they did the last 3 days?

## Options-Structure Layer (Phase K-ter)

**NO_TRADE (earnings_confounded).** options_layer_enabled=true (MRVL has listed options; the account's option-approval level is read at run time). The Aug 27 FQ2 FY27 print (the socket-loss binary) falls within any tradeable horizon, so ATM IV is dominated by event premium and is not a clean rich/cheap read: selling premium sells the event, buying premium pays the event tax. Compounding screens also fail: account-scale (DGS10 4.58 hold-cash band -> no CSP-to-acquire intent) and the HOLD verdict (no directional structure to express). No structure; a discipline_record is logged to the append-only options-ledger.jsonl. PAPER-only layer by contract -- never an order.

## Subagent Audit

- **price-fetcher** (DISPATCHED): broker-authoritative live $188.48 (regular session ~14:21 ET, broker_authoritative=true, -8.62% intraday); 7/15 regular close $206.26 anchors all threshold math (J.0b); full technicals panel + MACD/S-R supplement + correlation matrix (MRVL least-correlated basket member, no pair >0.7); next_earnings null at deterministic tier (Aug 27 carried from stockanalysis/IR).
- **forensic-scorer** (DISPATCHED): 13-metric scorecard, Altman Z 12.1 SAFE, Greenblatt ROC ~60%, Beneish adj -1.92 GREY (DSRI 1.50), Buffett/Lynch/Greenblatt/Burry = borderline-FAIL/borderline-PASS/FAIL/FAIL; filing integrity CLEAN, NO new MRVL 8-K 7/13-7/16, no new periodic filing since 7/13 (next print 8/27); composite confidence HIGH.
- **institutional-positioning-scout** (DISPATCHED): insider signal DE-ESCALATED (kill-criterion NOT tripped; only new post-6/23 Form 4 is Koopmans 7/01 confirmed-10b5-1; the "$65M CFO" was a holdings misread); SI 3.90% off 4.49% peak, DTC ~1, off threshold list; Dataroma thin 2/65 Q1-stale; congressional noise; positioning NEUTRAL (not bearish); freshness MED; confidence HIGH on the kill-criterion answer.
- **thesis-critic** (DISPATCHED): ITT 8/10; 5 failure modes (FM1 socket 55% / FM2 multiple-compression 50% HIGH-cascade / FM3 Aug-binary 40% / FM4 insider->revision 25% DE-ESCALATED / FM5 melt-up 35% Type-II); verdict HOLD/AVOID-INITIATING correct at the anchor, stance sharpened to conditional-accumulation WATCH, NOT a BUY; honestly downgraded its own FM4.
- **claim-distributor** (DISPATCHED Phase L): entity UPDATE branch (see commit).
- **Recency scan** (general-purpose, DISPATCHED): resolved the cohort-vs-idiosyncratic crux -- PREDOMINANTLY COHORT/SECTOR-driven (TSMC capex-reset 7/16 + Micron-China 7/15), HIGH confidence on cohort-as-primary-driver, MED that it is cleanly "buyable"; consensus PT $242.50 median unchanged/up; Aug 27 print date; 1-of-2 downgrade kill-criterion.
- **Wave-3 adversarial gate: SKIPPED** -- non-boundary HOLD (composite 68 is 8 pts from the 60 boundary, outside +/-5), no thesis-status flip to INVALIDATE, no --verify; TIER PRECEDENCE makes bearish the safe direction (the cost lever). The load-bearing NEW claim (FM2 regime read) is Grade-A (TSMC print); the socket-erosion channel checks are Grade-C by construction and NOT verdict-load-bearing -- the AVOID rests on the Grade-A R/R failure + broker price + EDGAR forensics + the 0.0x deployment band.
- **Phase R**: **shadow_rating = SELL vs new_rating = HOLD (DIVERGENCE -- first for MRVL).** The old-logic veto (any K.5 FM with prob >40% AND HIGH cross-position cascade -> downgrade one tier) fires this run because FM2 (50%, HIGH cross-position cascade) clears the bar (it did not on 7/13, when the drop was not yet pinned to a sector-wide catalyst) -> old logic would downgrade HOLD -> SELL. The NEW logic holds HOLD and routes the bear case to conviction (22%) + kill-criteria. This is the calibration monitor's designed signal: the old veto would over-bearishly SELL a cohort-de-rated, clean-forensic, de-escalated-positioning quality name the sell-side has at +28.7% upside. Logged to calibration-monitor.md; R.3 rollback trigger evaluates at n>=8 realized-at-3mo (not armed). SINGLE-NAME-BUY tripwire N/A (this is MRVL, HOLD).

<!-- INGEST:claims -->
:::ingest:claims
- entity: MRVL
  metric: trading-decision
  value: "HOLD / AVOID INITIATING"
  date: 2026-07-16
  grade: A
  section: recent
  text: "/invest 2026-07-16 (Tier-A dw refresh): HOLD / AVOID INITIATING at $188.48 live ($206.26 7/15 anchor). Composite 68/100; R/R ~0.75:1 anchor / 1.77:1 live fails 3:1 (median PT $242.50 +28.7% above live; ~40% air pocket open, support broke at 201-206, next real floor ~$170 then ~$158/SMA200 $129); conviction 22% / confidence 70%; thesis CONFIRM(interconnect)/CHALLENGE(custom-socket-moat unresolved + valuation still no MoS). Stock -20% since the 7/13 AVOID at $216 on a confirmed COHORT de-rate (TSMC capex-reset 7/16). Three of four bear vectors eased (positioning de-escalated, valuation reset, drop is buyable-cohort). Sharpened conditional-accumulation WATCH: build only on ~$170-179 R/R-clear + DGS10<4.40 band reopen + Aug-27 compute-die win. Deployment band 0.0x hold-cash."
  source: "wiki/investing/analyses/mrvl-analysis-2026-07-16.md"
  prov: "script:invest"
- entity: MRVL
  metric: price
  value: 188.48
  date: 2026-07-16
  grade: A
  section: recent
  text: "Live $188.48 (broker-authoritative, -8.62% intraday 7/16); 7/15 regular close $206.26; -37.5% off the $329.88 52wk high (close) / -42.9% (live). Broke below the 201-206 shelf into the air pocket; nearest real support ~$170.84 then ~$157.96, SMA200 $128.80. RSI ~35.6 (not yet oversold), MACD deeply bearish, 63d annualized vol 107.7%, beta 2.82 (SPY). MRVL is the least-correlated name in the analysed set."
  source: "mcp:robinhood-trading:get_equity_quotes"
  prov: "mcp:robinhood-trading"
- entity: MRVL
  metric: cohort-de-rate-driver
  value: "TSMC capex-reset 7/16 + Micron-China 7/15"
  date: 2026-07-16
  grade: A
  section: risks
  text: "The 7/16 -8.6% drop is COHORT-driven (crux resolved, HIGH conf): TSMC Q2 (record beat but capex raised to $60-64B from a $56B ceiling + Q3 op-margin ~70bps light + H2 GM dilution) triggered an AI-capex-digestion / multiple-compression scare across the semis complex (SOXX -4.4%, AVGO -4.3%, AMD -6.0%, ARM -6.7%, NVDA -2.6%; VOO -0.4%, VIX 16.3). No MRVL-specific catalyst, no 8-K, no fresh socket headline. MRVL amplifies ~2x as the highest-multiple/highest-beta name -- factor amplification. Caveat: the FCF-focus regime structurally targets MRVL's ~1%-FCF-yield profile (the cohort catalyst IS the idiosyncratic-valuation risk)."
  source: "web:reuters+stockstory+robinhood-mcp"
  prov: "web:multiple"
- entity: MRVL
  metric: consensus-price-target
  value: 242.50
  date: 2026-07-16
  grade: C
  section: financial-signals
  text: "Consensus PT median $242.50 (+28.7% above live $188.48) / mean $252.56 / high $385 / low $110; 43 analysts, 30 Strong-Buy / 7 Buy / 6 Hold / 0 Sell. UNCHANGED-to-UP through a -20%-in-a-week price move (targets stale/unrevised). Last 3 days: KeyBanc PT RAISE $385->$400 (7/14, Overweight reaffirm) + Erste DOWNGRADE Buy->Hold no-PT-cut (7/14) = downgrade kill-criterion 1 of 2, NOT tripped."
  source: "web:stockanalysis.com+C"
  prov: "web:stockanalysis.com"
- entity: MRVL
  metric: insider-positioning
  value: "DE-ESCALATED; kill-criterion NOT tripped"
  date: 2026-07-16
  grade: A
  section: risks
  text: "Insider signal DE-ESCALATED vs 7/13 (HIGH conf reversal): the only new post-6/23 Form 4 is COO Koopmans 7/01 (10,000 sh @ $281.92 = $2.82M), CONFIRMED 10b5-1 (plan adopted 2026-01-05), routine monthly cadence -- NOT discretionary. The 7/13 'outgoing CFO Meintjes ~$65M sale' was a MISREAD (that is his remaining-stake VALUE, not a transaction; actual sales $4.02M 4/15 + $701K 5/15). 18 sells/0 buys 6mo but under Dec-25/Jan-26 10b5-1 plans (calendar timing, not top-calling). SI 3.90% (6/30), DTC ~1, -13.3% off the 6/15 peak, off threshold list. Positioning NEUTRAL, not bearish."
  source: "mcp:openinsider:MRVL+sec-form4"
  prov: "mcp:openinsider"
- entity: MRVL
  metric: forensic-scorecard
  value: "Piotroski 7/9; Altman 12.1; Beneish -1.92 adj GREY; ROC ~60%"
  date: 2026-07-16
  grade: A
  section: financial-signals
  text: "Forensics strong/clean, valuation improved with price: Piotroski 7/9 (8/9 ex-gain), Altman Z 12.1 SAFE, Beneish M adj -1.92 GREY (DSRI 1.50 AR flag, DSO 65->97d easing to ~78d), Greenblatt ROC ~60% top-decile / EY 0.84% bottom-decile, ROIC ~6.1% reported / ~21.7% ex-GW ($13.9B M&A goodwill), FCF yield ~1.0%, PEG ~1.0 (Lynch clean-pass), GM +177bps 4Q, net-debt/EBITDA 0.42x, SBC 7.5%. Filing integrity CLEAN; NO new 8-K 7/13-7/16; no new periodic filing since 7/13; next print Aug 27 2026."
  source: "script:forensic-scorer"
  prov: "script:forensic-scorer"
- entity: MRVL
  metric: deployment-band
  value: "0.0x hold-cash"
  date: 2026-07-16
  grade: A
  section: thesis-fit
  text: "Macro deployment band 0.0x (DGS10 4.58% > 4.40 hold-cash line; FRED 7/14); 4 of last 5 sessions >4.50 toward the sustained-5 absolute regime-halt line; VIX 16.3 benign. Rating never band-gated (doctrine scope); the band sizes any entry to $0. Doctrine fingerprint pd-34ad8054/fb-48ee1308 (lint exit 0; byte-identical to the 7/13 run)."
  source: "mcp:fred:DGS10"
  prov: "mcp:fred"
:::

---
*Analysis generated 2026-07-16 via /invest (Tier-A dw topology; 4 mandatory subagents dispatched + a recency-scan worker + a live broker read + FRED macro + EDGAR primary; Wave-3 skipped on a non-boundary HOLD). Broker-authoritative price anchor $206.26 (7/15 close); live $188.48 displayed as-of (session open). 3-day refresh of mrvl-analysis-2026-07-13. Not investment advice; decision-support for the owner's vault. Per ref-portfolio-doctrine + [[ref-theme-alpha]] + mrvl-analysis-2026-07-13 + mrvl-analysis-2026-06-18.*
