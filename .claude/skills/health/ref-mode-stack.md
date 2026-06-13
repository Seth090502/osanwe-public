# Health /stack mode

Phase-by-phase execution contract for `/health stack`. SKILL.md imperatively Reads this before executing stack mode. Extracted 2026-04-18 (Group 23b).

---

Timing optimization and stack efficiency.

## Phase 1: Timing Audit (1-2 searches)
Map every supplement to optimal window:
- Fed vs fasted absorption
- Circadian alignment (cortisol curve, melatonin onset)
- Interaction timing (zinc/copper separation, fat-soluble co-admin)
- Active peptide protocol injection timing and 24-48h peak GLP-1 window
- Caffeine interactions

## Phase 2: Absorption Optimization (1-2 searches)
- Curcumin: requires piperine or fat? Current formulation?
- Magnesium glycinate: elemental mg vs salt mg?
- Omega-3: triglyceride vs ethyl ester form?
- Lion's Mane: hot water vs dual extraction (beta-glucan content)?
- GLP-1 delayed gastric emptying: which supplements are absorption-sensitive?

## Phase 3: Redundancy & Gap Analysis
- Multi-ingredient supplement overlap (flag if unknown)
- Stack gaps relative to goals with T1-T3 evidence: creatine? (neuroplasticity + performance + recomposition -- strong evidence, commonly absent)
- Cost-per-benefit ranking
- Compounds that could be dropped (T5-T6 evidence only, no measurable benefit)

## Phase 4: Output
Write to `<VAULT_ROOT>/Efforts/health-protocol/analyses/stack-review-YYYY-MM-DD.md`:

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

## Optimized Timing Schedule
| Time | Supplement | Dose | Fed/Fasted | Notes |

## Absorption Issues
[specific problems with current administration]

## Redundancies
[double-dosing risks, ingredient overlap]

## Stack Gaps
| Missing Compound | Goal | Evidence | Priority |

## Deprioritize (weak evidence)
[compounds that could be dropped]

## Recommended Changes
### Immediate (no risk, >=60% confidence)
### Evaluate (needs data)
### Deprioritize (T5-T6 only)
```
