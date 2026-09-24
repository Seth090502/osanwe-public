---
aliases: []
categories: [meta]
type: config
tags: []
status: active
created: 2026-06-09
updated: 2026-06-09
related: []
---

# Synthetic calibration-monitor fixture (score-outcomes.py test)

Synthetic rows with pre-filled ret_3mo so Brier computes without network.
Expected values (pre-computed, asserted by T-harness):
- pooled new Brier = 0.223 (n=5; rows AAA/BBB/CCC/FFF/GGG; HOLD+NR excluded)
- pooled shadow Brier = 0.173125 (n=4; rows BBB/CCC/DDD/FFF)
- stratum sequential new = 0.200833 (n=3: AAA/BBB/FFF)
- stratum dw new n=1 (insufficient, < 3)
- stratum sequential-legacy new n=1 (insufficient; legacy 11-cell row GGG)
- rollback: realized_at_3mo=6, armed=false (floor 8)

## Call Log

| date | ticker | new_rating | shadow_rating(old-logic) | conviction% | R/R | composite | thesis_status | ret_1mo | ret_3mo | ret_6mo | orchestrator_model | topology |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-01-02 | AAA | BUY | HOLD | 50 | 3.2:1 | 70 | CONFIRM | +5.0% | +10.0% | | claude-opus | sequential |
| 2026-01-03 | BBB | SELL | SELL | 40 | 0.8:1 | 30 | CHALLENGE | -2.0% | +4.0% | | claude-opus | sequential |
| 2026-01-04 | CCC | STRONG BUY | BUY | 60 | 4.5:1 | 85 | CONFIRM | +8.0% | +15.0% | | claude-opus | dw |
| 2026-01-05 | DDD | HOLD | SELL | 45 | 1.5:1 | 50 | CONFIRM | | -6.0% | | claude-opus | dw |
| 2026-01-06 | EEE | NR | N/A (excl Brier) | N/A | N/A | N/A (pre-rev) | narrative | | +9.9% | | claude-opus | dw |
| 2026-01-07 | FFF | STRONG SELL | STRONG SELL | 30 | 0.5:1 | 15 | INVALIDATE | -10.0% | -20.0% | | claude-opus | sequential |
| 2026-01-08 | GGG | BUY | HOLD | 55 | 3.5:1 | 65 | CONFIRM | +1.0% | -3.0% | |

## Notes

Row GGG is deliberately 11 cells (legacy shape) to exercise short-row padding ->
sequential-legacy stratum. Row EEE (NR) must be excluded from Brier even though
ret_3mo is filled. Row DDD (new=HOLD) is excluded from the NEW Brier but its
shadow SELL counts in the SHADOW Brier.
