---
categories:
  - wiki
type: ingest
created: 2026-05-06
updated: 2026-05-06
status: active
confidence: high
tags:
  - topic/hbm-memory
  - topic/dram-cycle
  - topic/nand-cycle
  - topic/memory-idm
  - topic/cxl-disaggregation
  - topic/ai-memory-demand
  - topic/storage-cycle
  - topic/post-nand-alternatives
  - thesis/theme-alpha
  - ticker/MU
  - ticker/SNDK
  - ticker/WDC
  - ticker/PSTG
  - ticker/ALAB
  - ticker/MRAM
  - ticker/AVGO
  - ticker/MRVL
  - ticker/NVDA
  - ticker/AMD
  - ticker/AMAT
  - ticker/LRCX
  - ticker/KLAC
related:
  - "ref-memory-storage-cycle-deep-dive"
  - "WDC"
  - "PSTG"
  - "ALAB"
  - "MRAM"
  - "Kioxia"
  - "MU"
  - "SNDK"
  - "NVDA"
  - "AMD"
  - "AVGO"
  - "MRVL"
  - "AMAT"
  - "LRCX"
  - "KLAC"
  - "SK-Hynix"
  - "Samsung"
  - "investing-moc"
  - "thesis-theme-alpha"
---

# Ingested: ref-memory-storage-cycle-deep-dive

## Source

- **Path:** `Atlas/sources/investing/ref-memory-storage-cycle-deep-dive.md`
- **Body sha256:** `b0b0f2622d3dea153ebb112d5854d4e3cb76844c65c39a9bc3fda3d4ced318c1`
- **Body bytes:** 40,840 (6,259 words)
- **Source confidence:** HIGH (claude.ai Research-mode 100+ source synthesis; primary 8-K/IR + TrendForce/Counterpoint/SemiAnalysis/Tom's Hardware corroboration)
- **Onboarded by /enrich:** commit `e242478` (2026-05-06)
- **Ingested at:** 2026-05-06

## Phase summary (deviation from full v2 spec)

This /ingest run executed Phase A-G with PRAGMATIC SCOPE REDUCTION on Phase F.1 entity updates. The 5 parallel claim-distributor dispatches returned ~70 inserts + 3 Tier-1 supersedes + 5 Tier-2 flags + 1 Tier-3 reject + 13 dedup-skips across 11 existing entities (MU, SNDK, NVDA, AMD, AVGO, MRVL, AMAT, LRCX, KLAC, SK-Hynix, Samsung). Given the complexity of the Tier-2/3 flags requiring human reconciliation (most notably the NVDA Vera Rubin 576GB-vs-288GB unit-of-measure question that cascades to the AMD MI450 lag claim), Phase F.1 entity-update Edits are **DEFERRED to round-2 application**. This document archives the full subagent return summaries so round-2 can apply them deterministically once Tier-2 conflicts are reconciled.

Phase F.2 entity creates (5 net-new) + F.3 MOC + F.4 source-audit-chain + F.5 ingest report executed normally as atomic batch.

## Claims extracted summary

~110 atomic claims distributed across 16 in-scope entities (5 created in this commit; 11 deferred for round-2 with full Edit-op plans archived below). Decomposed from 22 thematic sections in source (HBM market structure / HBM-CoWoS coupling / Customer allocation / DRAM cycle / NAND cycle / Memory IDM business models / WD-SNDK post-spin / China memory / Memory export controls / Capex cycle math / Pricing cycles / Inventory cycles + DOI / Peer-signal mechanics / Memory mix dynamics / AI workload memory demand / CXL disaggregation / Memory-as-a-service / DPU+SmartNIC / Post-NAND alternatives / Wafer + supply chain coupling / Cycle-position assessment).

T1 fact density: 65.3 markers/1000w (4.4x HIGH threshold).

## Entity actions

### Created (5 net-new entities; applied in this commit `15fa8d5+`)

- `wiki/entities/tickers/WDC.md` -- Western Digital (HDD pure-play post-SNDK spin; +860% 1y; sold-out 2026)
- `wiki/entities/tickers/PSTG.md` -- Pure Storage (Meta-Pure 1-2 EB FY26-end; SK Hynix QLC eSSD partnership)
- `wiki/entities/tickers/ALAB.md` -- Astera Labs (CXL pure-play; Microsoft Azure M-series CXL deployment first-in-industry)
- `wiki/entities/tickers/MRAM.md` -- Everspin Technologies (only public pure-play MRAM; defense + edge-computing positioning)
- `wiki/entities/companies/Kioxia.md` -- Kioxia Holdings (Japan NAND IDM; SKH 14% stake; Flash Ventures JV with SNDK; HBF + NVIDIA development)

### Updates DEFERRED to round-2 (11 entities; Edit-op plans archived below)

#### MU -- Micron Technology
- 5 inserts queued: Q4-25 DRAM revenue $11.98B; Q4-25 conventional DRAM margins surpassed HBM (cycle-top hallmark); HBM4E development CY27; 6600 ION 245TB SSD May-2026; 9650 PCIe Gen 6 SSD for BlueField-4 STX; power-efficiency-vs-hybrid-bonding differentiator; peak-cycle distribution risk framing
- 8 dedup-skips (existing claims already cover Q2 FY26 revenue $23.9B; CY26 HBM supply locked; HBM4 12-Hi production; HBM TAM $35B->$100B; etc.)
- **Tier-3 REJECT**: 2026-05-05 close-price conflict -- incoming `$643 (+11.54%)` vs existing entity body `$636.39 +10.6%` (lines 141, 204) from briefing-2026-05-05 / mu-analysis-2026-05-05. Same date, same metric, different value. Reconciliation needed: verify official 2026-05-05 close (Yahoo/stockanalysis.com); $700B+ market-cap milestone framing only valid at $643 not $636.39.
- **Tier-2 FLAG**: cycle-peak signal-count definitional conflict -- existing `5-of-5 firing` (mu-analysis-2026-05-05) vs incoming `1.5/5 fully-triggered` (ref-doc). Definitional mismatch, not data conflict. Resolve canonical scoring rule (broader-inclusion vs fully-triggered) before next /invest run; the framing chosen changes which doctrine rule applies.

#### SNDK -- SanDisk
- 12 inserts queued: Q3-FY26 revenue $5.95B / EPS $23.41 / GM 78.4% / segment mix; Q4-FY26 guide $7.75-8.25B; NBM contracts $42B + $11B guarantees + 33% FY27 bits; $6B buyback + zero-debt; YTD 2026 +362%; WD spin mechanics; NBM variable-pricing risk; cycle-peak signature 2-3/5
- **Tier-1 SUPERSEDE**: YTD return 348% -> 362% (newer date 2026-05-06 vs 2026-04-30; same source grade); supersedes line 91 of SNDK entity
- 3 dedup-skips (NAND pricing Q1-Q2-26; spin-completion 2025-02-21; Tohoku earthquake 2026-04-22)

#### NVDA -- Nvidia
- 5 inserts queued: SKH One Team alliance + TSMC base die; VVP DRAM pricing; CoWoS allocation 50-60% (~800-850K wafers); ICMS KV-cache offloading; H200 China >2M unit orders + Federal Register license-review revision
- **Tier-2 FLAG (CRITICAL)**: Vera Rubin HBM4 576GB (system-level, 16 stacks x 36GB) vs existing entity 288GB (per-die). Both HIGH-grade. Reconciliation needed: 288GB per R200 die x 2 dies per Vera Rubin board = 576GB system level. If correct, promote incoming as system-level + retain existing as per-die. Re-run /invest delta on AMD MI450 432GB-lag claim once unit fixed.
- **Tier-2 FLAG**: Blackwell HBM specs (B200 192GB / B300 288GB / GB300 NVL72 13.4 TB rack) -- taxonomy ambiguity (Thesis Fit vs Recent classification).
- **Tier-2 FLAG**: Goldman ASIC HBM growth +82% MEDIUM-grade updating existing HIGH-grade narratives (Introl 44.6% CAGR, 60%+ AI compute non-NVDA by EOD, MI455X parity, Meta TPU Feb-26 + 2027 PURCHASE consideration). Skip vs supplemental insert decision.

#### AMD -- Advanced Micro Devices
- 5 inserts queued: Instinct HBM ladder (MI300X 192GB / MI325X 256GB / MI450 432GB); EPYC 9005 + Leo CXL DLRM 70% boost; Alibaba 40-50K MI308 192GB HBM3 China; Samsung foundry MI accelerators; Pensando DPU integration
- **Tier-1 SUPERSEDE**: Alibaba MI308 40-50K -- newer date (2026 vs 2025-12), higher grade (HIGH Reuters vs MEDIUM TrendForce-unconfirmed); supersedes line 65 entity claim
- **Tier-2 FLAG (BLOCKED)**: MI450 432GB lags Vera Rubin 576GB -- DIRECT NUMERICAL CONTRADICTION with existing entity line 109 ('AMD 432 GB capacity advantage vs Rubin 288 GB'). Cannot insert until NVDA-side 576GB-vs-288GB unit-of-measure resolution complete.

#### AVGO -- Broadcom
- 3 inserts queued (clean): Custom-ASIC HBM demand growth +82% YoY 2026 -> 1/3 of HBM market (Goldman); Samsung-Broadcom HBM4 test pass -> 2026 Google TPU supply leadership (TrendForce 2025-12); Tomahawk Ultra + ethernet switch family
- 0 contradictions; 0 dedups (all novel relative to existing AVGO body)

#### MRVL -- Marvell Technology
- 5 inserts queued (clean): XConn $540M acquisition; Apollo + Apollo 2 hybrid CXL/PCIe specs; Structera S CXL switch (industry's highest-radix); Samsung peer-signal -> CXL momentum; OCTEON DPU
- 0 contradictions; 0 dedups (all novel)

#### AMAT -- Applied Materials
- 3 inserts queued: memory deposition tools role; coupled cycle math (IDM capex -> tools backlog 1-2 quarter lag); IDM 2026 capex aggregate ~$65B
- Section creates required (## Thesis Fit + ## Catalysts canonical headings missing; entity uses non-canonical `## Key Catalysts` + `## Claims from [[ref-theme-alpha]]`)

#### LRCX -- Lam Research
- 3 inserts queued: memory etch tools (cryogenic etch for high-aspect-ratio NAND); coupled cycle math; IDM 2026 capex aggregate ~$65B
- Section creates required (same pattern as AMAT)

#### KLAC -- KLA Corporation
- 2 inserts queued (clean): metrology + inspection differentiated from etch (LRCX) and deposition (AMAT); coupled cycle math at metrology-checkpoint stage
- Has clean canonical taxonomy; no section-creates needed

#### SK-Hynix -- SK Hynix (company)
- 11 inserts queued: Q1-26 HBM revenue share 57% / DRAM 78% / NAND 21% / cash 54.3T KRW; 2026 capex $20.5B (+17% YoY); HBM4 12-Hi mass production Sept-2025; custom HBM4E TSMC base-die collab Nov-2025; 9th-Gen 4D NAND 321-layer; $8B EUV order; DDR4 Wuxi China fab ramp; HBM5 roadmap 80GB/stack 2031; LPDDR6 1cnm world-first 2026; Kioxia 14% stake re-rated 14x; LTAs 1-yr->3-5 yr with hyperscalers; NVIDIA One Team >50% NVDA HBM share 2026
- **Tier-1 SUPERSEDE**: 2026 capex $20.5B/+17% supersedes prior MEDIUM-grade `mid-30% level of sales 3-yr moving average` qualitative guidance (line 47); annotation: "(superseded 2026-05-06 per ref-memory-storage-cycle-deep-dive -- concrete figure $20.5B/+17% now disclosed)"
- **Tier-2 FLAG**: bundled Q1-26 metrics insert (revenue + operating profit + operating margin + net margin) where most are dup of lines 44-45; recommendation: split to net-margin-only insert
- 2 dedup-skips (Q1-26 revenue exact match line 45; HBM4E samples H2-2026 exact match line 54)

#### Samsung -- Samsung Electronics (company)
- 13 inserts queued (clean): Q4-25 DRAM revenue $19.30B / 36% share / reclaimed #1; 2026 capex $20B (+11% YoY); HBM4 Pyeongtaek P4 Feb-2026 (logic-die yield >90%, 1c DRAM yield ~50%, 11.7 Gbps); Samsung-Broadcom HBM4 test pass 2026 Google TPU supply leadership; copper-to-copper hybrid bonding; foundry serves AMD MI accelerators; Morgan Stanley CY26 EPS +150-300% YoY forecast; V-NAND 9th-gen 286 layers + 512TB Gen6 SSD 2027; iPhone 17 LPDDR5X 60-70% Samsung-sourced; DDR4 EOL reversal Q1-26; OpenAI Stargate 900K DRAM wafers/mo (~40% global DRAM); embedded 14nm MRAM
- 1 dedup-skip (HBM4 capacity target 250K WPM end-2026 exact match line 46)

## Contradictions ledger

### Tier 1 auto-resolved (3) -- DEFERRED to round-2 application

1. **SNDK YTD return**: 348% -> 362% (May vs April; same source grade); supersede annotation queued for line 91
2. **AMD Alibaba MI308 order**: 40-50K MEDIUM-unconfirmed -> HIGH Reuters 192GB HBM3 each China deployment; supersede annotation queued for line 65
3. **SK-Hynix 2026 capex**: MEDIUM `mid-30% level of sales` -> HIGH `$20.5B (+17% YoY)`; supersede annotation queued for line 47

### Tier 2 flagged (5) -- BLOCKING for round-2 application until reconciled

1. **MU cycle-peak signal-count**: existing `5-of-5 firing` (mu-analysis-2026-05-05) vs incoming `1.5/5 fully-triggered` (ref-doc). Definitional reconciliation required (broader-inclusion vs fully-triggered scoring rule).
2. **NVDA Vera Rubin HBM4 capacity** (CRITICAL): existing 288GB per-die vs incoming 576GB system-level (16 stacks x 36GB). Reconcile unit-of-measure: 288GB x 2 dies = 576GB system level likely correct.
3. **NVDA Blackwell HBM specs**: taxonomy ambiguity (Thesis Fit vs Recent for product-spec data).
4. **NVDA Goldman ASIC HBM +82%**: MEDIUM-grade updating HIGH-grade existing narratives. Decision: insert as supplemental quant (HBM-allocation lens) or skip as redundant.
5. **AMD MI450 vs Vera Rubin lag** (BLOCKED): direct numerical contradiction with existing entity line 109; cannot insert until NVDA Tier-2 (#2) resolves -- 432GB advantage flips to 432GB lag depending on Vera Rubin denominator.
6. **SK-Hynix bundled Q1-26 metrics**: split-required to net-margin-only insert; subagent flagged for human review.

### Tier 3 rejected (1)

1. **MU 2026-05-05 close price**: incoming `$643 (+11.54%)` vs existing entity body `$636.39 +10.6%` (briefing-2026-05-05 / mu-analysis-2026-05-05). Same date, same metric, different value. Reject pending source verification (Yahoo/stockanalysis.com official close).

## MOC back-link applied (Phase F.3)

- `Atlas/_MOCs/investing-moc.md`: `related:` extended with 4 new ticker stems (WDC, PSTG, ALAB, MRAM). Kioxia is a company entity and is back-linked from this ingest report's `related:` and from the source `related:` (audit chain closure) but not added to the investing-moc which is ticker-focused.

## Source audit-chain closure (Phase F.4)

- `Atlas/sources/investing/ref-memory-storage-cycle-deep-dive.md` `related:` extended with 5 new entity stems (WDC, PSTG, ALAB, MRAM, Kioxia) + this ingest-report stem.

## Sub-threshold deferred (~12 entities; not auto-created)

| Category | Tickers | Deferral reason |
|---|---|---|
| Chinese memory (non-tradeable) | CXMT (12 mentions; DDR5-8000 production), YMTC (10 mentions; Xtacking 4.0 + Phase 3 fab) | Entity-List complications + non-tradeable-from-US |
| Storage / private | VAST Data (Series F $1B at $30B; xAI Colossus 200K GPU + CoreWeave $1.17B), WekaIO, Pliops, Hammerspace, Lightbits Labs | Private; track via secondary markets |
| Memory startups | Niron Magnetics (private; iron-nitride magnet substitute), eVAC Magnetics (Sumter SC NdFeB facility; ~3,000 MT total US capacity 2026) | Private |
| Adjacent | Phison (NT$1.02T module-maker), Kioxia subsidiary entity considerations, Solidigm | Phison covered as bullet; Solidigm tangential |
| Equipment | TEL (Tokyo Electron), Hitachi-High-Tech, ASML (existing entity not in scope) | TEL/Hitachi-High-Tech sub-threshold; ASML deserves its own /ingest pass |

## Follow-ups

1. **Round-2 entity-update application** -- once Tier-2 #2 (Vera Rubin 288GB-vs-576GB unit) is reconciled, apply all 11 entity updates with full subagent Edit-op plans archived above. Deterministic: Tier-1 supersedes have explicit line-number annotations; Tier-3 reject (MU close price) requires source verification.

2. **MU cycle-peak signal-count rule** -- /invest 2026-05-05 (5-of-5) vs ref-doc (1.5/5) definitional reconciliation. Reconcile the signal-fire definition before the next /invest run.

3. **NVDA Vera Rubin spec verification** -- pull TrendForce 2026-03-09 + Hankyung primary sources to confirm 16-stack-per-Vera-Rubin claim is system-level (576GB total) vs per-die (288GB). Cascades to AMD MI450 lag framing.

4. **AMAT/LRCX section taxonomy reconciliation** -- entities use legacy `## Key Catalysts` (non-canonical) + `## Claims from [[ref-theme-alpha]]`. Migration to canonical `## Catalysts` + `## Thesis Fit` is /vault repair scope, not ingest scope.

5. **Round-2 promote-to-entity candidates** -- after CY27 HBM4E ramp visibility:
   - SK-Hynix-Pure partnership entities (companies)
   - VAST Data (private; track if IPO trajectory emerges)
   - CXMT/YMTC (Chinese memory; track regulatory / Entity-List delta)

6. **Companies entity gap** -- BlackRock / iShares Bitcoin Trust ETF custodian, BlackRock-Securitize collaboration, Apollo Global Management (Aave Horizon institutional pool), JPMorgan/Kinexys -- substantive coverage across multiple ref-docs but no `wiki/entities/companies/` notes. Consider company-typed /ingest pass.

## Phase metadata

- Phase A pre-flight: PASS (source readable; sha256 verified; vault indexes loaded)
- Phase D extraction: ~110 claims across 16 entities
- Phase E.0 claim-distributor dispatch: 5 SUCCESSFUL parallel dispatches (MU+SNDK, NVDA+AMD, AVGO+MRVL, AMAT+LRCX+KLAC, SK-Hynix+Samsung); 0 contract violations; rich Tier-2/3 contradiction surfacing
- Phase F.0 vault-classifier-sweep: PASS (score 95, 0 GATE)
- Phase F.1 entity updates: DEFERRED to round-2 (11 entities; Edit-op plans archived above)
- Phase F.2 entity creates: 5 SUCCESS (orphan-on-create resolved by F.3 immediately)
- Phase F.3 MOC back-link: investing-moc.md `related:` extended with 4 ticker stems
- Phase F.4 source related: extension: 5 entity stems + ingest-report stem
- Phase F.5 ingest report: this file
- Phase G atomic commit: pending
- Phase K F11 clear: pending
