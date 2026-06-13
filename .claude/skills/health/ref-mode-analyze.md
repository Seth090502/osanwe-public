# Health /analyze mode

Phase-by-phase execution contract for `/health analyze`. SKILL.md imperatively Reads this before executing analyze mode. Extracted 2026-04-18 (Group 23b).

---

Full stack analysis -- the flagship mode. Cross-references everything.

## Phase 1: Goal-Stack Alignment Audit (0-1 searches)

For each supplement in current-stack.md, produce a Goal Relevance Matrix:

| Supplement | Dose | Goal-A | Goal-B | Goal-C | Goal-D | Evidence Floor | Risk |
|-----------|------|--------|--------|--------|--------|---------------|------|

Goal column labels (Goal-A through Goal-D) correspond to the user-ranked health goals defined in the private layer. Score relevance: **A** (direct, T1-T2), **B** (supportive, T2-T3), **C** (peripheral, T3-T4), **D** (speculative, T5-T6), **X** (not relevant). Evidence Floor = lowest evidence tier supporting the primary claim.

## Phase 2: Interaction Matrix Scan (1-2 searches)

Cross-reference every compound pair. Check from ref-interactions.md + fresh searches:
- Synergies with mechanism: e.g., Vitamin D + K2 calcium routing
- Antagonisms with mechanism: e.g., Zinc and Copper compete at DMT1/ZIP4 transporters
- Timing conflicts: e.g., calcium blocks iron absorption within 2hr window
- GLP-1 class-specific: GLP-1 delays gastric emptying 20-40% -> changed absorption kinetics for ALL oral supplements
- Hepatotoxicity stacking: NAC + curcumin + GLP-1 agonist combined hepatic load

Output interaction summary with NatMed severity grades (Major/Moderate/Minor).

## Phase 3: Dosing Audit (2-3 searches)

For each supplement, verify against literature:
- Therapeutic range from RCTs (cite)
- Current dose position: BELOW / WITHIN / ABOVE range
- Dose-response curve shape (linear, U-shaped, ceiling)
- Upper Tolerable Intake Level (UL) from IOM/EFSA
- **CRITICAL FLAG:** Vitamin D at [HIGH_DOSE_IU] = 3.75x UL. Requires toxicity risk assessment, hypercalcemia monitoring, 25(OH)D target 60-80 ng/mL, toxicity >100 ng/mL.

## Phase 4: Biomarker Prediction (1-2 searches)

For each supplement, list from ref-biomarkers.md + fresh data:
- Target biomarker and expected direction
- the user's optimized zone (3-tier)
- Expected magnitude and timeline to change
- Current lab value (if available) vs prediction

## Phase 5: Risk Dashboard

Produce tiered risk assessment:
- **CRITICAL:** Vitamin D toxicity risk at [HIGH_DOSE_IU] (until 25(OH)D confirmed <100)
- **ELEVATED:** Hepatotoxicity stacking (NAC + curcumin + GLP-1 agonist)
- **MONITOR:** Zinc/copper ratio (verify current ratio against target 8-15:1)
- **MONITOR:** GLP-1 agonist + berberine additive hypoglycemia
- **LOW:** Everything else with adequate evidence and safe dosing

## Phase 6: Intelligence Gaps

Flag what's missing:
- Bloodwork values (CRITICAL gap -- cannot assess safety without 25(OH)D)
- Multi-ingredient supplement overlap (possible double-dosing with standalone supplements)
- Cognitive recovery phase (defined in private layer -- required for neuroplasticity prioritization)
- Body composition precision (DEXA vs visual estimate)
- Baseline cognitive scores (no benchmark for neuroplasticity tracking)

## Phase 7: Synthesis and Output

Write to `<VAULT_ROOT>/Efforts/health-protocol/analyses/stack-analysis-YYYY-MM-DD.md`:

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

## Decision Sheet
Stack: XX compounds | Est. Monthly Cost: $XXX
Critical Flags: [list]
Highest-Priority Action: [single most important thing]
Confidence: XX% -- [basis]

## Goal Alignment Matrix
[table from Phase 1]

## Interaction Summary
[Major and Moderate only -- Minor in appendix]

## Dosing Audit
| Supplement | Current | Therapeutic Range | Position | Action |
[one row per compound]

## Risk Dashboard
[tiered: CRITICAL / ELEVATED / MONITOR / LOW]

## Biomarker Predictions
| Supplement | Target Marker | Direction | the user's Zone | Timeline |

## Stack Optimization
### Immediate Actions (>=60% confidence only)
### Evaluate (40-59% -- monitor, don't act)
### Speculative (<40% -- noted but excluded)
### Pending Labs (cannot assess until bloodwork entered)

## Intelligence Gaps
[what we don't know that matters]

## Sources & Reasoning
[audit trail: recommendation -> evidence chain]
```

## Phase 8: Self-Verification

- [ ] Every supplement has evidence tier cited?
- [ ] All pairwise interactions checked?
- [ ] GLP-1 agent interactions addressed for every oral supplement?
- [ ] Vitamin D toxicity flagged with lab monitoring schedule?
- [ ] Biomarker predictions include 3-tier ranges and timelines?
- [ ] Dose-response data cited for every recommendation?
- [ ] Hepatotoxicity stacking assessed?
- [ ] Multi-ingredient overlap flagged as intelligence gap?
- [ ] Confidence gating enforced (>=60% in actions, rest excluded)?
- [ ] Protein adequacy flagged (>=1.2g/kg/day)?
- [ ] Cognitive recovery phase noted?
- [ ] 90-day retest triggers checked?
