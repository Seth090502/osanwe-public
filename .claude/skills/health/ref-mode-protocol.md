# Health /protocol mode

Phase-by-phase execution contract for `/health protocol`. SKILL.md imperatively Reads this before executing protocol mode. Extracted 2026-04-18 (Group 23b).

---

Active peptide protocol titration management.

## Phase 1: Protocol Status
Read peptide-protocol.md: current dose, day, injection history, side effects, weight response.

## Phase 2: Clinical Context (1-2 searches)
Search for latest active peptide protocol data:
- Phase 2/3 trial updates
- Known side effects at current dose level
- GLP-1/GIP/glucagon interactions with current stack

## Phase 3: Titration Assessment
- Is titration on track with trial protocol?
- Side effect severity assessment (GI, administration site, appetite, energy)
- Next dose recommendation with timing and confidence
- Dose ceiling based on body weight and response

## Phase 4: Supplement-Peptide Interaction Review
- Berberine + GLP-1 agonist: additive hypoglycemia risk? Evidence?
- Gastric emptying delay: absorption timing changes for morning stack?
- GLP-1 appetite effects: is protein intake adequate for lean mass?
- Taurine + GLP-1: beta-cell synergy?

## Phase 5: Output
Write to `<VAULT_ROOT>/Efforts/health-protocol/analyses/protocol-review-YYYY-MM-DD.md`:

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

## Protocol Status
Day: XX | Dose: Xmg/week | Duration: X weeks
Weight: XXX.X lbs | Delta: -X.X lbs | Expected (Phase 2): -X.X%

## Titration Plan
| Week | Dose | Status | Side Effects | Weight |

## Next Dose Recommendation
[specific, with confidence and evidence]

## Side Effect Assessment
| Effect | Severity (1-5) | Trend | Action |

## Supplement-Peptide Interactions
[full stack check against GLP-1 mechanism]

## Protein & Nutrition
[intake vs >=1.2g/kg target, lean mass preservation strategy]

## Monitoring Schedule
[next labs, weigh-in, side effect log]
```
