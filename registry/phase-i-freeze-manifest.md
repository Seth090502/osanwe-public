---
aliases: []
categories: [decisions]
status: complete
created: 2026-08-25
updated: 2026-08-25
tags: [fis]
related: ["[[phase-i-freeze-manifest]]"]
---

# Phase I Baseline Freeze Manifest

## Version
- Tag: `phase-i-final`
- Commit: `30068147`
- Branch: `cross-harness-migration`
- Frozen: 2026-08-25T05:00:00Z

## Dataset State
| Item | Path | Type |
|---|---|---|
| Factor store | Efforts/osanwe-v2-overhaul/_work/factors.db | SQLite (bars + factors) |
| Wave analyses | Efforts/osanwe-v2-overhaul/_work/wave*-analysis.md | 127 markdown files |
| Benchmark profiles | wiki/investing/benchmarks/*-benchmark.md | ~124 files |
| Data annexes | wiki/investing/benchmarks/*-data-annex.md | ~124 files |
| Reference docs | wiki/research/ref-*.md | 42 files |
| Education corpus | wiki/research/edu-*.md | 10 files |
| Finance frameworks | wiki/research/fin-*.md | 11 files |
| Entity notes | wiki/entities/tickers/*.md | ~108 files |
| Calibration outputs | wiki/maintenance/calibration/ | Multiple JSON/MD |
| Decision attribution | wiki/maintenance/calibration/decision-attribution.md | Single MD |

## Claimed Metrics (to be independently verified)
| # | Claim | Value | Status |
|---|---|---|---|
| C1 | Instruments in factor store | 125 | PENDING AUDIT |
| C2 | Total bars | 153,084 | PENDING AUDIT |
| C3 | Macro series | 52 | PENDING AUDIT |
| C4 | Wave analysis files | 127 | PENDING AUDIT |
| C5 | EDGAR companies scraped | 95 | PENDING AUDIT |
| C6 | Entity notes with Data Layers | 105/108 | PENDING AUDIT |
| C7 | Momentum strategy edge vs SPY | +0.8pp CAGR | PENDING INDEPENDENT REPRODUCTION |
| C8 | Calibration sample size | 54 predictions | PENDING AUDIT |
| C9 | Confidence overstatement | ~45 points at 70-79% bin | PENDING AUDIT |
| C10 | Selection alpha | (withheld) | PENDING AUDIT |
| C11 | HOOD data gap | Zero bars in store | PENDING AUDIT |
| C12 | Scheduled tasks live | 7 | PENDING AUDIT |

## Known Limitations at Freeze
1. Survivorship bias: universe is today's listings, not historical constituents
2. No bear market in sample (5y window covers 2021-2026 bull + correction)
3. Calibration n=54 is statistically underpowered
4. Momentum result not tested on true out-of-sample data
5. No corporate action adjustments verified
6. Some entity note fundamentals stale (May-June 2026)
7. PSTG delisted from Yahoo (404) -- excluded from store

## Reproduction Audit Assignments
| Audit ID | Agent | Scope | Status |
|---|---|---|---|
| V1-V3 | Independent | Data claims (C1-C4) | DISPATCHED |
| V4 | Independent | Momentum reproduction (C7) | DISPATCHED |
| V5-V7 | Independent | Calibration + attribution (C8-C10) | DISPATCHED |
| V8-V9 | Independent | Graph linking + look-ahead bias (C6) | DISPATCHED |
| V10-V12 | Independent | Survivorship + timestamps + jobs (C5,C11,C12) | DISPATCHED |
