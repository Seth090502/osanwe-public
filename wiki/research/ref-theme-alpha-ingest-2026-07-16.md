---
categories: [wiki]
type: ingest
created: 2026-07-16
updated: 2026-07-16
status: active
confidence: medium
tags:
  - topic/ai-infrastructure
  - topic/memory-storage-cycle
  - topic/hyperscaler-spending
  - topic/china-semiconductors
related:
  - "[[ref-theme-alpha]]"
  - "*MU* (not published)"
  - "*SNDK* (not published)"
  - "*MSFT* (not published)"
  - "*GOOGL* (not published)"
  - "*AMZN* (not published)"
  - "*META* (not published)"
  - "*NVDA* (not published)"
  - "*AMD* (not published)"
  - "*TSM* (not published)"
  - "*CXMT* (not published)"
  - "*YMTC* (not published)"
---

# Ingested: ref-theme-alpha (2026-07-16 rewrite)

## Source
- Path: `Atlas/sources/investing/ref-theme-alpha.md`
- Body sha256: `c0650716cae2882b105bcb55efec2418cbbe110e093896d67fe087fa3ea21f0b`
- Word count: 12,571 | Confidence: medium (majority Grade B-filed / derived; a few Grade A verbatim; several Grade C inferences)
- Onboarded via /enrich (commit c993d78) immediately prior; this is the paired /ingest half.

## Claims extracted summary
40 net-new claims distributed across 11 entity sections; the large majority of the source's per-entity figures deduped against existing entity-note content (the notes were already dense from prior /invest + /ingest passes). Distribution was done by 9 parallel `claim-distributor` subagents (one per existing entity) under a hard fidelity contract: never upgrade certainty, preserve every grade label and caveat verbatim, skip perishable market-levels.

## Claims by entity (net-new; deduped claims not relisted)
- **MU** (+9): 9M FY26 capex $19,602M (+92.2% y/y, per 10-Q); Item 1A verbatim oversupply risk (Grade A fragment); 5yr DRAM ASP band; 2027 HBM contract surge (TrendForce); Singapore packaging from 1H CY2027; FQ4 print ~2026-09-22 (tentative). The conventional-vs-HBM-breakout interpretation carried as Grade C.
- **SNDK** (+5): NBM provenance correction (see Contradictions); NAND +10-15% q/q 3Q26 (TrendForce); SEMI 300mm 3D NAND equip +28% to $14B 2026; NAND-pure/EUV-decoupling structural read.
- **MSFT** (+4): 9M FY26 OCF/PP&E 62.9% coverage; CY2025 OCF $160.506B; ~$25B component-pricing sits on the call OUTSIDE the filing (absence confirmed by end-to-end Ex-99.1 read) -- provenance risk + sole-issuer comparative.
- **GOOGL** (+7): TTM PP&E/OCF 63.0%; CY2025 OCF $164.713B; Q1 2026 FCF $10.116B; capex raise attributed to M&A (Intersect) not components; Q2 print 2026-07-22.
- **AMZN** (+4): CY2025 OCF $139.514B; TTM PP&E +$59.3B "primarily reflects investments in artificial intelligence" (Grade A fragment); OCF-coverage-above-100% inference; Q2 print ~2026-07-30 (Grade D, unconfirmed).
- **META** (+5): Q1 capex/OCF 61.6%; CY2025 OCF $115.800B + finance-lease principal $2.524B; Q1 FCF $12.386B; 2026 total-expense guide $162-169B "unchanged" (Grade A verbatim) as the opex-vs-component tension; Q2 print 2026-07-29.
- **NVDA** (+1): single Grade-C thesis-fit inference (pass-through pricing power, bottleneck-adjacent-not-binding). All four source financials deduped -- source self-capped at Grade B (8-K not read verbatim; sec.gov 403) vs the note's existing HIGH.
- **AMD** (+3): 8-K DC growth-driver attribution (MI350/EPYC); shared-layer price-taker inference (~55% GM vs NVDA 75%); MI450/Helios guided-not-booked + Samsung HBM4 binding-layer exposure. Source section self-capped Grade B (read via sec.gov search, not verbatim).
- **TSM** (+2): CFO Wendell Huang demand quote (Grade A verbatim, Form 6-K 2026-04-16); Q2 2026 results 2026-07-16 dated catalyst. All five financials deduped (note already carries them; source adds a primary 6-K citation vs the note's Digitimes secondary).

## Contradictions
### Tier 1 -- grade correction (1)
- **SNDK NBM dollar terms.** SNDK.md currently carries the $42B minimum-revenue and >$11B guarantee figures at HIGH/"as if filed" (per *ref-memory-storage-cycle-deep-dive* (not published)). ref-theme-alpha establishes those dollar figures are CALL-AND-PRESS sourced, NOT filed (Grade B); the filed 8-K Ex-99.1 (2026-04-30) confirms only the COUNT (three NBM agreements by end-FQ3 + two in FQ4 = 5 total). The VALUE is not disputed -- only the grade/provenance. Captured as a correcting claim in the new SNDK claims block (append-only); the surgical downgrade of the existing line is deferred to a follow-up (below) rather than done as an in-place edit this pass.

### Tier 3 -- rejected (2)
- **MSFT FQ4 print date.** Incoming 2026-07-29 rejected; the note's IR-confirmed 2026-07-28 (which already flagged 7/29 as an erroneous prior reference) stands -- higher authority. Not distributed.
- **AMD Q1 gross margin.** Incoming 55% rejected; that equals the note's GUIDE, not the 52.82% ACTUAL print (amd-analysis-2026-05-06, HIGH). Source was Grade-B / sec.gov-search-snippet vs the note's HIGH actual. Not distributed.

## Entity actions
- **Updated (9):** MU (+9), SNDK (+5), MSFT (+4), GOOGL (+7), AMZN (+4), META (+5), NVDA (+1), AMD (+3), TSM (+2). Each got a dated `## Claims from [[ref-theme-alpha]] (2026-07-16)` block (append-only; strictly additive; body sha256 preserved on the pre-existing content; `updated:` bumped to 2026-07-16).
- **Created (2):** *CXMT* (not published) + *YMTC* (not published) as `type: company` competitive-intelligence entities (foreign, non-tradeable; the China-memory oversupply bear case on *MU* (not published) / *SNDK* (not published)). Dedicated-section threshold met in source. Symmetric back-links: investing-moc + mutual CXMT<->YMTC.
- **Sub-threshold / not created:** none (the source's two China-memory entities both cleared the dedicated-section bar).

## Follow-ups
- [ ] **Grade correction (targeted, deferred):** downgrade SNDK.md line ~168 NBM dollar terms from HIGH/filed to Grade B / call-and-press, annotating that only the 3+2=5 count is filed. Same correction applies to `ref-memory-storage-cycle-deep-dive.md:312` (flagged by the source doc as a live mis-grading). Do as a deliberate `/decide` or narrow-edit pass, not smuggled into this ingest.
- [ ] **Pattern-22 cleanup:** SNDK.md contains 4 pre-existing non-ASCII `->` arrows (U+2192) -- a latent GATE risk, left untouched this pass per surgical discipline. Sweep in a dedicated /vault pass.
- [ ] **Macro ref-doc ingest DELIBERATELY SKIPPED:** `ref-macro-landscape.md` carries only 2 entity claims (CXMT + YMTC IPO facts), both duplicated in this theme-alpha doc's dedicated sections; a separate macro ingest would be redundant. Its value is the topic framework, correctly not entity claims.

## Provenance note
Every distributed claim carries `(per [[ref-theme-alpha]])` and preserves the source's own grade label ([Grade A/B/C/D], "derived", "reportedly", "analyst estimate", "not verbatim") inside the claim text. The one perishable market-level in scope (MU's TrendForce 3Q26 q/q DRAM price figure) was NOT distributed as a durable fact -- flagged refetch/do-not-inherit per the perishable-tier discipline.
