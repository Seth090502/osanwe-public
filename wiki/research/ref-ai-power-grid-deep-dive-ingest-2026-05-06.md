---
categories:
  - wiki
type: ingest
created: 2026-05-06
updated: 2026-05-06
status: active
confidence: high
tags:
  - topic/ai-power-demand
  - topic/datacenter-power
  - topic/grid-infrastructure
  - topic/nuclear-restart
  - topic/independent-power-producers
  - topic/bess-storage
  - thesis/theme-gamma
  - thesis/theme-alpha
  - ticker/AEP
  - ticker/NRG
  - ticker/NEE
  - ticker/DUK
  - ticker/SO
  - ticker/PPL
  - ticker/FLNC
related:
  - "[[ref-ai-power-grid-deep-dive]]"
  - "AEP"
  - "NRG"
  - "NEE"
  - "DUK"
  - "SO"
  - "PPL"
  - "FLNC"
  - "investing-moc"
  - "thesis-theme-gamma"
---

# Ingested: ref-ai-power-grid-deep-dive

## Source

- **Path:** `Atlas/sources/investing/ref-ai-power-grid-deep-dive.md`
- **Body sha256:** `4d930b76cca4941a103a7cfd03b2501aadadef77489006309e7e04e189a74513`
- **Body bytes:** 47,407 (7,428 words)
- **Source confidence:** HIGH (claude.ai Research-mode synthesis; FERC + DOE + EIA + utility-IR + EPRI + LBNL primary corroboration; secondary trade press for hyperscaler-PPA color)
- **Onboarded by /enrich:** commit `bd92c91` (2026-05-06)
- **Ingested at:** 2026-05-06

## Phase summary (PRAGMATIC SCOPE REDUCTION)

This /ingest run executed Phase A-G with the same pragmatic scope reduction pattern as the memory-storage-cycle ingest (`6364039`). Phase F.1 entity-update Edits across 14 existing entities (VST, CEG, TLN, BWXT, SMR, OKLO, GEV, ETN, ABB, HUBB, DTCR, VOLT, Hitachi-Energy, Siemens-Energy) are **DEFERRED to round-2 application** -- the source's depth and breadth (7,428 words; 74.2 markers/1000w; 20+ entities with >=3 mentions) warrants careful claim-distributor dispatch + Tier-2 reconciliation rather than autonomous batch.

Phase F.2 entity creates (7 net-new) + F.3 MOC + F.4 source-audit-chain + F.5 ingest report executed normally as atomic batch.

## Claims extracted summary

~150 atomic claims distributed across 21 in-scope entities (7 created in this commit; 14 deferred for round-2). Decomposed from thematic sections in source: AI power demand magnitudes / data-center capex maps / nuclear restart pipeline (Three Mile Island, Palisades, Duane Arnold, Holtec) / SMR landscape (BWXT, NuScale SMR, Oklo, NNE) / IPP economics (VST, CEG, TLN, NRG, AES, BEPC, CWEN) / regulated utility maps (AEP, NEE, SO, DUK, PPL, FE, ETR, ES, XEL, WEC, EIX, PCG, OGE, EXC, PSEG, D, SRE) / electrical equipment (GEV, ETN, ABB, HUBB, POWL, CAT, CMI) / BESS storage (FLNC, STEM) / construction-EPCs (PWR, MTZ, PRIM) / geothermal (ORA) / interconnect-queue mechanics / FERC regulatory / transformer + skilled-labor shortages.

T1 fact density: 74.2 markers/1000w (5x HIGH threshold; highest of any source ingested this session).

## Entity actions

### Created (7 net-new entities; applied in this commit)

| Entity | Sector | Anchor signal |
|---|---|---|
| `wiki/entities/tickers/AEP.md` | Utility / Regulated T&D | PJM data-center capacity planner; 20 mentions |
| `wiki/entities/tickers/NRG.md` | IPP + Retail Energy | ERCOT hyperscaler PPA counterparty; 15 mentions |
| `wiki/entities/tickers/NEE.md` | Renewables + Florida regulated | World's largest US renewables operator; 15 mentions |
| `wiki/entities/tickers/DUK.md` | Regulated T&D + Generation | Carolinas + Florida data-center hot spots; 11 mentions |
| `wiki/entities/tickers/SO.md` | Regulated + Vogtle nuclear | Only US new-nuclear operator; 12 mentions |
| `wiki/entities/tickers/PPL.md` | PJM regulated utility | Central PA data-center pipeline; 13 mentions |
| `wiki/entities/tickers/FLNC.md` | Grid-scale BESS | Pure-play battery energy storage; 11 mentions |

### Updates DEFERRED to round-2 (14 entities)

Subagent dispatches not run for context-efficiency. Round-2 should dispatch claim-distributor for each:

| Entity | Mention count | Round-2 priority |
|---|---|---|
| SMR | 26 | HIGH (24+ subsections; existing entity needs deepening) |
| VST | 23 | HIGH (Susquehanna data-center co-location; existing entity) |
| GEV | 19 | HIGH (gas + nuclear turbine pipeline; existing entity) |
| CEG | 15 | HIGH (Constellation; Three Mile Island restart; existing entity) |
| TLN | 12 | HIGH (Talen / Susquehanna SSES; existing entity) |
| BWXT | 9 | MEDIUM (naval reactor + commercial SMR; existing entity) |
| ETN | 11 | MEDIUM (electrical equipment; existing entity) |
| ABB | (in source) | MEDIUM (Hitachi/Siemens peer; existing entity) |
| HUBB | (in source) | MEDIUM (electrical infrastructure; existing entity) |
| OKLO | 7 | MEDIUM (advanced nuclear; existing entity) |
| DTCR | (thesis-tagged ETF) | MEDIUM (basket exposure metric updates) |
| VOLT | (thesis-tagged ETF) | MEDIUM (basket exposure metric updates) |
| Hitachi-Energy | (in source) | MEDIUM (transformer + grid; company entity) |
| Siemens-Energy | (in source) | MEDIUM (turbine + transformer; company entity) |

## Sub-threshold deferred (~25 entities; not auto-created)

| Category | Tickers | Deferral reason |
|---|---|---|
| Regulated utilities (Tier-2) | FE (10 mentions), ETR (8), ES, XEL, WEC, EIX, PCG, OGE, SRE, EXC, PSEG, D (8) | Mentioned but specialized regional context; defer to round-2 if portfolio focus emerges |
| Renewable IPPs | BEPC (12), CWEN, AES (8) | Brookfield/Clearway/AES; track if PPA-counterparty thesis sharpens |
| Equipment / EPCs | CAT (12), CMI, GNRC (9), POWL (7), PWR (9), MTZ, PRIM | Ancillary to GEV/ETN/ABB/HUBB primary set |
| Specialty | ORA (10; geothermal), STEM (BESS), NNE (Nano Nuclear) | Niche thesis exposure |
| Storage / private | (none specifically flagged) | -- |

## Contradictions ledger

Not computed for this run (deferred entity-update phase). Round-2 claim-distributor dispatches will surface Tier-1/2/3 findings as in prior ingests.

## MOC back-link applied (Phase F.3)

- `Atlas/_MOCs/investing-moc.md`: `related:` extended with 7 new ticker stems (AEP, NRG, NEE, DUK, SO, PPL, FLNC)

## Source audit-chain closure (Phase F.4)

- `Atlas/sources/investing/ref-ai-power-grid-deep-dive.md` `related:` extended with 7 new entity stems + ingest-report stem (8 total)

## Follow-ups

1. **Round-2 entity updates** (14 entities) -- highest priority: SMR (26 mentions), VST (23), GEV (19), CEG (15), TLN (12). The Susquehanna SSES Talen-AWS co-location precedent + Three Mile Island Constellation-Microsoft restart are the highest-leverage claims for VST/CEG/TLN deepening.

2. **Round-2 promote-to-entity candidates** (sub-threshold + Tier-2):
   - FE, ETR, BEPC for IPP+regulated breadth
   - CAT, CMI for gas-peaker on-site generation
   - NNE for advanced-nuclear small-cap

3. **Research implications** -- this ref-doc supports single-name analysis of AEP / NEE / SO / DUK / FLNC. The 7 new entity stubs serve as accretion points for subsequent /invest analyses.

4. **Cross-domain compounding** -- ref-ai-power-grid-deep-dive complements ref-ai-supply-chain-deep-dive (compute layer) + ref-memory-storage-cycle-deep-dive (memory bottleneck) -- the AI thesis now has full vault coverage across compute / memory / power / networking / storage layers.

## Phase metadata

- Phase A pre-flight: PASS
- Phase D extraction: ~150 claims across 21 entities
- Phase E.0 claim-distributor dispatch: SKIPPED for context efficiency (DEVIATION; round-2 will dispatch)
- Phase F.0 vault-classifier-sweep: SKIPPED (relied on prior /enrich audit score 95)
- Phase F.1 entity updates: DEFERRED to round-2 (14 entities)
- Phase F.2 entity creates: 7 SUCCESS (orphan-on-create resolved by F.3 immediately)
- Phase F.3 MOC back-link: investing-moc.md `related:` extended with 7 ticker stems
- Phase F.4 source related: extension: 7 entity stems + ingest-report stem
- Phase F.5 ingest report: this file
- Phase G atomic commit: pending
- Phase K F11 clear: pending

## Round-2 Application (appended 2026-05-06)

Round-2 invocation re-ran /ingest on the same source. Phase E.0 dispatched `claim-distributor` for all 14 deferred entities in parallel; Phase F.1 atomically applied returned Edit operations.

### Round-2 dispatch outcomes (14/14 SUCCESS)

| Entity | Path | Claims in | Claims new | Claims deduped | Tier-1 supersedes | Tier-3 rejects |
|---|---|---|---|---|---|---|
| VST | wiki/entities/tickers/VST.md | 11 | 11 | 0 | 0 | 0 |
| CEG | wiki/entities/tickers/CEG.md | 8 | 7 | 0 | 0 | 1 (Crane MW 835 vs 837) |
| TLN | wiki/entities/tickers/TLN.md | 7 | 6 | 1 (1.92 GW PPA) | 0 | 0 |
| SMR | wiki/entities/tickers/SMR.md | 10 | 10 | 0 | 0 | 0 |
| BWXT | wiki/entities/tickers/BWXT.md | 6 | 6 | 0 | 0 | 0 |
| OKLO | wiki/entities/tickers/OKLO.md | 8 | 8 | 0 | 0 | 0 |
| GEV | wiki/entities/tickers/GEV.md | 12 | 12 | 0 | 0 | 0 |
| ETN | wiki/entities/tickers/ETN.md | 8 | 8 | 0 | 1 (DC order growth) | 0 |
| ABB | wiki/entities/tickers/ABB.md | 2 | 2 | 0 | 0 | 0 |
| HUBB | wiki/entities/tickers/HUBB.md | 2 | 2 | 0 | 0 | 0 |
| DTCR | wiki/entities/tickers/DTCR.md | 2 | 2 | 0 | 0 | 0 |
| VOLT | wiki/entities/tickers/VOLT.md | 2 | 2 | 0 | 0 | 0 |
| Hitachi-Energy | wiki/entities/companies/Hitachi-Energy.md | 10 | 10 | 0 | 0 | 0 |
| Siemens-Energy | wiki/entities/companies/Siemens-Energy.md | 7 | 7 | 0 | 0 | 0 |

**Aggregate:** 95 claims in / 93 claims applied / 1 deduped / 1 Tier-1 supersede / 1 Tier-3 reject.

### Tier-1 supersede (auto-resolved)

- **ETN data-center order growth**: prior claim "Data center order growth >40% (MEDIUM, per [[ref-theme-alpha]])" superseded by "Data-center orders +240% Q1; revenue +50%; negotiations pipeline +81% YoY (HIGH, per [[ref-ai-power-grid-deep-dive]])". Newer date (2026-05-04 Q1-26 print) + higher grade (HIGH > MEDIUM) + same metric. Prior annotated in-place with `(superseded 2026-05-04 per [[ref-ai-power-grid-deep-dive]])`.

### Tier-3 reject (flagged for human reconciliation)

- **CEG Crane Clean Energy Center MW capacity**: existing line in CEG.md states 837 MW (per ref-ai-supply-chain-deep-dive HIGH); incoming claim states 835 MW (per Constellation 2025 10-K filed 2026-02-24 via [[ref-ai-power-grid-deep-dive]] HIGH). Both HIGH-grade primary sources; +/-2 MW likely reflects post-FERC interconnection adjustment. Both claims retained until human reconciles against canonical primary source. CEG.md `## Risks` section has explicit reconciliation flag inserted.

### Tier-1 augment notes (no reject; section-target distinct)

- **VST AWS Comanche Peak 1.2 GW PPA**: existing in `## Financial signals`; incoming routed to `## Catalysts` with delivery window + extension option detail. Both retained -- complementary precision in different sections.
- **VST Meta 2,609 MW PJM nuclear PPA**: existing approximate `>2,600 MW` in Financial signals; incoming precise `2,609 MW + 433 MW uprates` with plant-by-plant breakdown in Catalysts. Both retained.
- **VST Cogentrix 5,500 MW gas portfolio**: existing in Financial signals (closed deal); incoming routed to Catalysts (forward-looking pending close). Section-target distinct.

### Drift observations (out-of-scope; flagged for /vault repair)

1. **Section heading capitalization drift**: 4 entities use `## Thesis Fit` (capital F) vs canonical `## Thesis fit`: SMR, OKLO, BWXT, ETN, GEV, ABB, VST, CEG, TLN, HUBB, Hitachi-Energy, Siemens-Energy. Preserved as-is to avoid byte-mutation outside insertion windows. Recommend vault-wide normalization sweep.
2. **Frontmatter tag drift on SMR.md line 18 + OKLO.md line 18**: malformed indentation `  -   - topic/nuclear-restart` (extra hyphen + indent). Out-of-scope for claim-distributor; flag for /vault repair.

### Round-2 Phase metadata

- Phase A pre-flight: PASS (source body sha256 unchanged from round-1; prior report idempotency check confirms continued applicability)
- Phase B state-transition print: PASS (round-2 mode auto-detected from prior report's "DEFERRED to round-2" annotation)
- Phase C F11 set: PASS (`.claude/state/auto-commit-disabled` confirmed)
- Phase D extraction: REUSED round-1 extraction (no re-run; claims passed verbatim to claim-distributor dispatches)
- Phase E.0 claim-distributor dispatch: 14/14 SUCCESS (parallel; no fallback to inline logic)
- Phase F.0 vault-classifier-sweep: pending (next step)
- Phase F.1 entity Edits: 14/14 applied (with body-preservation per Edit tool old_string/new_string atomic match)
- Phase F.5 ingest report amendment: this section
- Phase G atomic commit: pending
- Phase K F11 clear: pending
