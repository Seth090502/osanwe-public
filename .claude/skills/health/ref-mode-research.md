# Health /research mode

Phase-by-phase execution contract for `/health research <compound>`. SKILL.md imperatively Reads this before executing research mode. Extracted 2026-04-18 (Group 23b).

---

Deep-dive a single compound with PubMed-grade evidence.

## Phase 1: Compound Identification (1 search)
Chemical identity, class, mechanism, half-life, metabolism pathway, bioavailability.

## Phase 2: Evidence Review (3-5 searches)
For each of the user's goals (defined in private layer):
1. Search systematic reviews / meta-analyses
2. Search RCTs
3. Search safety + toxicity data + UL
4. Search GLP-1 agonist interactions specifically
5. Search dose-response studies

Record per finding: evidence tier, GRADE, source, year, n, duration, effect size, CI when available.

## Phase 3: Stack Integration
- How does this interact with EVERY item in current-stack.md?
- Does it duplicate anything already taken?
- Optimal timing window? Conflicts with existing schedule?
- GLP-1 agonist interaction?

## Phase 4: Output
Write to `<VAULT_ROOT>/Efforts/health-protocol/analyses/research-<compound-slug>-YYYY-MM-DD.md`:

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

## Compound Profile
Name | Class | Half-life | Metabolism | Bioavailability

## Mechanism of Action
[cited primary literature]

## Evidence by Goal
### 1. Cognitive Health / Neuroplasticity
[GRADE-mapped evidence]
### 2. Body Composition
### 3. Longevity / Anti-Aging
### 4. Performance / Motor Learning

## Dose-Response
| Dose | Population | Outcome | Effect Size | Tier | Source |

## Safety Profile
Therapeutic range | UL | Known ADRs | Contraindications | GLP-1 agonist interaction

## Stack Fit Assessment
Synergies | Conflicts | Timing | Duplicates?

## Verdict
**Add to stack?** ADD (>=60%) / EVALUATE (40-59%) / NO (<40%)
**Confidence:** XX% -- [basis]
**Dose:** XXmg (range: XX-XXmg based on [source])
**Timing:** [window and why]
**Monitoring:** [biomarkers to track]
**GLP-1 notes:** [any]
```

## Phase 5: KB Updates
1. Append to research-log.md
2. If verdict is ADD, note in current-stack.md under "Under Evaluation"
3. Update ref-interactions.md if new interaction data found
4. Update ref-evidence-base.md with this compound's evidence summary
5. Append to Calendar/decisions/sessions-log.md
