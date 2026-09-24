---
categories: [wiki]
type: ingest
created: 2026-06-10
updated: 2026-06-10
status: active
confidence: HIGH
tags:
  - topic/earnings-mechanics
  - topic/pead
  - topic/memory
aliases:
  - earnings playbook ingest
related:
  - "[[ref-earnings-playbook]]"
  - "MU"
  - "AVGO"
  - "SNDK"
  - "NVDA"
  - "META"
  - "AMZN"
  - "GOOGL"
  - "MSFT"
  - "SK-Hynix"
---

# Ingested: ref-earnings-playbook (Earnings Playbook)

## Source

- Path: Atlas/sources/investing/ref-earnings-playbook.md
- Body sha256: 2e45e2de69de217b16a6179c58689b0c80428ca850966bcd6cc5c639b2afff32
- Word count: 7,340 (body)
- Source confidence: HIGH (academic-cited reference doc; vNEXT Section 11 NOW set, onboarded via /enrich 2026-06-10 commit 37da9f7)

## Claims extracted summary

28 entity-scoped claims across 9 entities (12-section earnings-mechanics reference; Section 12E pre-formatted extractable facts + body claims). Distribution executed via 9 claim-distributor dispatches (5 parallel batches). General/methodology claims (PEAD attenuation base rates, CBOE 72% implied-greater-than-actual, IV crush 30-60 percent, guidance-spread tiers, combined hyperscaler capex ~$725B +77 percent) are NOT entity-distributable -- they live in the ref doc itself as thresholds-as-data.

## Claims by entity

### MU (10 received: 8 applied, 1 deduped, 1 Tier-3 rejected)
- Earnings-reaction history CY2024-Mar2026, 5 quarters detailed (HIGH) -- section: Claims block -- ref: sec. 8
- FQ1-2026 beat-and-RISE print detail (HIGH) -- section: Claims block -- ref: sec. 6
- FQ2-2026 EPS/revenue beat detail (HIGH) -- section: Claims block -- ref: sec. 1
- FQ2-2026 next-day -4 percent reaction (HIGH) -- section: Recent -- ref: sec. 1
- Beat-and-drop base rate ~56 percent modal reaction (HIGH) -- section: Claims block -- ref: sec. 8
- 720 percent 2025 rally + most-bought retail stock (MEDIUM) -- section: Claims block -- ref: sec. 1/3
- Forward P/E ~6.3x at cyclical strength (MEDIUM) -- section: Claims block -- ref: sec. 10
- Revision momentum +22.38 percent/60d mid-2025 (MEDIUM) -- section: Claims block -- ref: sec. 2
- DEDUPED: FQ3-2026 guide $33.5B/$19.15 (present in 3 prior analysis blocks)
- TIER-3 REJECTED: "-13 percent on 2026-06-05" vs entity's broker-anchored -7.74 percent close same date (see Contradictions)

### AVGO (5 received: 2 applied, 3 deduped)
- FQ2-2026 ACTUALS $22.2B/+48 percent, EPS $2.44 (HIGH) -- section: Financial signals -- ref: sec. 8
- Sector-readthrough: 6/05 guide-below-whisper -> cohort reassessment (HIGH) -- section: Thesis Fit -- ref: sec. 9
- DEDUPED: AI rev $10.8B+143 percent; Q3 guide $29.4B/FY26 AI $56B/FY27 $100B; AI-guide-miss narrative (all in avgo-analysis-2026-06-07 Recent block)

### SK-Hynix (5 received: 4 applied incl. 1 Tier-2-with-note, 1 partial-dedup)
- Q1 2026 op profit KRW 37.6103T absolute (HIGH) -- section: Financial signals -- ref: sec. 9
- Q1 2026 DRAM ASP +mid-60 percent / NAND +mid-70 percent QoQ (HIGH) -- section: Financial signals -- ref: sec. 9
- 3-yr HBM demand-exceeds-supply call claim + cycle-aware skepticism note (HIGH) -- section: Thesis Fit -- ref: sec. 9/10
- MU lead-lag ~6-8 weeks formalized, ASP correlation ~1.0 (MEDIUM) -- section: Thesis Fit -- ref: sec. 9
- Q4-2025 Samsung DRAM-revenue-lead + 57 percent HBM share, Tier-2 inline note (HIGH) -- section: Recent -- ref: sec. 9
- PARTIAL DEDUP: Q1 revenue 52.58T + 72 percent margin already present

### NVDA (1 received: 1 applied)
- Earnings-reaction class: guidance-vs-whisper dominates; mega-cap PEAD ~zero post-2006 (MEDIUM) -- section: Thesis fit (section created) -- ref: sec. 5/7

### SNDK (2 received: 2 deduped -- zero-new-claims short-circuit; entity untouched)
### MSFT (1 received: 1 deduped -- $190B capex present; entity untouched)
### GOOGL (1 received: 1 deduped -- $190B capex present; entity untouched)
### AMZN (1 received: 1 deduped -- $200B capex present; entity untouched)
### META (2 received: 0 applied -- 1 Tier-2 held, 1 Tier-3 rejected; entity untouched)

## Contradictions

### Tier 1 auto-resolved (0)
(none)

### Tier 2 flagged (2)
- SK-Hynix HBM share: incoming 57 percent (Counterpoint, Q4-2025, revenue/shipment basis) vs existing ~50 percent global HBM bit output (TrendForce, 2026 annual). Different metric/source/period -- BOTH STAND; applied with inline NOTE in the entity Recent section. Normalize which tracker is authoritative.
- META 2026 capex range: incoming $115-145B re-instates the $115B lower bound that the entity SUPERSEDED on 2026-04-30 ($125-145B per Q1 CY26 call, Tier-1 settled). HELD -- no write; verify whether the playbook's range pre-dates the Apr-29 raise (likely). Settled $125-145B stands.

### Tier 3 rejected (2)
- MU 2026-06-05 decline: incoming "~-13 percent" vs entity's broker-anchored -7.74 percent close-to-close same date (entity also records ~-11 percent two-day from the $1,079 peak). The -13 percent likely conflates a different measurement window; broker-anchored figure stands.
- META capex-raise reaction: incoming "-9.25 percent" vs entity's yfinance-verified -8.55 percent close (2026-04-30, Inconsistency-Log-confirmed). Verified figure stands.

## Entity actions

- Created: (none -- all 9 entities pre-existed)
- Updated: MU (+8), AVGO (+2), SK-Hynix (+4), NVDA (+1, Thesis fit section created)
- Unchanged (zero-new-claims short-circuit): SNDK, MSFT, GOOGL, AMZN, META
- Sub-threshold (deferred): Samsung (2 mentions; the Q4-2025 DRAM-lead claim landed on SK-Hynix instead)

## Follow-ups

- Reconcile the MU 6/05 "-13 percent" vs -7.74 percent window discrepancy if the playbook's figure is ever load-bearing (it is narrative color; broker close stands).
- SK-Hynix HBM-share metric normalization (57 percent Counterpoint vs 50 percent TrendForce) -- candidate for the next SK-Hynix-touching /invest or /ingest run.
- The playbook's pre-print checklist (sec. 3) gets first live use on MU FQ3-2026 (print 2026-06-24) -- now wired into /invest Phase D.3 (commit bc03a4b).
