# Health /progress mode

Phase-by-phase execution contract for `/health progress`. SKILL.md imperatively Reads this before executing progress mode. Extracted 2026-04-18 (Group 23b).

---

Longitudinal tracking with intervention timeline overlay.

## Phase 1: Data Collection
Read health-baseline.md (weight history, subjective scores), bloodwork.md (lab trends), peptide-protocol.md (dose history, side effects), prior progress reports from Efforts/health-protocol/analyses/.

## Phase 2: Trend Analysis
For each tracked metric:
- Current value vs baseline
- Rate of change (weekly/monthly)
- Trajectory: accelerating, linear, plateauing, reversing
- Comparison to expected outcomes (active peptide protocol trial data for weight)

## Phase 3: Intervention Timeline Overlay (causal inference model)
Map supplement start/stop dates against biomarker changes:
- "NAC started [date] -> ALT [value] on [date] = [direction]"
- "Active peptide protocol started [date] -> weight [value] on [date] = [delta] vs expected [expected]"
This is the causal inference layer -- without it, you can't tell what's working.

## Phase 4: Cognitive Recovery Milestone Check
Compare cognitive recovery start date (defined in private layer) against evidence-based timelines:
- Dopamine receptor density: expected recovery by [date]
- Executive function: expected normalization by [date]
- Full cognitive recovery: expected by [date]
- Current phase: [which milestone are we in?]

## Phase 5: Subjective Assessment
Prompt user for 1-10 scores: Cognitive, Focus, Energy, Sleep, Mood. Compare to prior entries.

## Phase 6: Output
Write to `<VAULT_ROOT>/Efforts/health-protocol/analyses/progress-YYYY-MM-DD.md`:

```markdown
---
categories: [efforts]
type: analysis
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
tags: []
related: []
---

## Progress Dashboard
Day XX of active peptide protocol | Dose: Xmg/week | Weight: XXX.X lbs (delta: +/-X.X)
Est BF%: XX% | BMI: XX.X | Cognitive recovery phase: [phase]

## Biometric Trends
| Metric | Baseline | Current | Delta | Trend | Target |

## Active Peptide Protocol Response
[dose history, weight trajectory, expected vs actual]

## Intervention Timeline
[supplement start/stop dates overlaid on biomarker changes]

## Cognitive Recovery
| Domain | Baseline | Current | Recovery Milestone | Status |

## Subjective Scores
| Date | Cognitive | Focus | Energy | Sleep | Mood |

## Lab Trends
[if multiple dates: directional movement per marker]

## 90-Day Retest Flags
[any interventions approaching 90-day mark]

## Recommended Adjustments
[confidence-gated, evidence-backed]
```
