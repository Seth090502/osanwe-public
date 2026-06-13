---
categories:
  - wiki
type: report
created: 2026-06-11
updated: 2026-06-11
status: active
tags:
  - topic/calibration
aliases: [calibration-monitor]
related:
  - "[[investing-moc]]"
  - "[[ORBC-DEMO-analysis-2026-06-11]]"
---

# Calibration Monitor -- DEMO

> **DEMO CONTENT.** One row per `/invest` verdict (Phase R append,
> marker-signature dedup on date+ticker). `tools/score-outcomes.py` backfills
> realized returns at the 1/3/6-month horizons and computes rolling Brier
> scores (new-rating vs shadow-rating, pooled and topology-stratified) once
> n >= 5. The rows below are synthetic seeds showing the schema.

## Call Log

| date | ticker | new_rating | shadow_rating(old-logic) | conviction% | R/R | composite | thesis_status | ret_1mo | ret_3mo | ret_6mo | orchestrator_model | topology |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-06-11 | ORBC-DEMO | HOLD | HOLD | 62 | 2.4 | 6.1 | HEALTHY | | | | demo | sequential |
| 2026-06-11 | LNCH-DEMO | WATCH | WATCH | 55 | 1.9 | 5.4 | HEALTHY | | | | demo | sequential |

## Rollback assessment

Not armed (demo seed; floor is 8 realized calls at >= 3 months).
