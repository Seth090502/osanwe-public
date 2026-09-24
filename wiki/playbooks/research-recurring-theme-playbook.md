---
categories: [wiki]
type: synthesis
status: active
created: 2026-05-24
updated: 2026-07-10
tags: [topic/consolidation, topic/playbook]
related:
  - "*hot* (not published)"
---

# Research (recurring theme) Playbook

## Pattern
Invariant: A research run's durable, downstream-reusable value is fixed when its prompt/output-contract is composed -- output format, extraction schema, target_path placement, right-sized length/citation floors, and the evidence-grade gate that will cap confidence -- and cannot be recovered at read time by re-summarizing or adding sources; a mis-composed run is recomposed and rerun, never salvaged, and source count is a floor to clear rather than the deliverable.

The vault built the entire /deep skill around exactly this claim: it composes a claude.ai Research-mode prompt that bakes in canonical frontmatter, a target_path placement field (zero slug drift through /enrich -> /ingest), an entity-claim extraction schema, and MANDATORY length/citation floors precisely so downstream value is decided before the run rather than reconstructed after (.claude/skills/deep/SKILL.md). The proof by failure is 2026-04-26: an over-constrained v1 prompt (14 H2 + 6,500-word floor + 100+ citations + TASK-FAILURE framing) failed three times in Research mode and was fixed by RECOMPOSING a relaxed v2 (9 H2 + 5,000w + 50+ citations + natural prose), never by salvaging the failed output at read time (sessions-log.md:817). Source count is explicitly demoted from the early invest-max 150-250-source maximalism (2026-04-06, sessions-log.md:46-54) to "source-target as FLOOR not ceiling" (2026-04-29, :104,:592) and the 50-75 norm, after which confidence is capped by evidence GRADE (ref-evidence-hierarchy.md), not by how many sources were pulled -- and AI-emitted source/word counts are themselves aspirational and must be recomputed post-hoc (2026-04-22, :593,:598,:599). The prompt is the cheap point of leverage; read-time is the expensive one.

Confidence: 73% -- the invariant is corpus-converged across independent methodology sessions (04-22/04-26/04-29) and architecturally embodied by the /deep skill itself; discounted because 2 of 5 stub anchors (the 2026-05-04 sessions) are incidental-token noise rather than research-method learnings, and three dated counter-cases show a complementary post-run verification lever the single invariant does not fully subsume.

## Evidence
- 2026-05-04: theme 'research'
- 2026-04-06: theme 'research'
- 2026-04-08: theme 'research'
- 2026-04-09: theme 'research'
- 2026-04-05: theme 'research'
- Threshold cleared: >= 3 distinct sessions share theme (observed 12).

## Counter-cases

- 2026-04-22 -- Pattern 21 inline-fallback: topic-opacity (deliberately private platform data) made Deep Research fail 3x, and the response was NOT recompose-and-rerun but ABANDON the external run and compose the ref inline -- an explicit exception where no prompt recomposition helps (Calendar/decisions/sessions-log.md:634,:669)
- 2026-06-08 -- deterministic-quant layer: a post-run correlation/stress quant materially changed the verdict (proved a decorrelation claim the LLM research could only assert; downgraded AVGO, elevated APH) -- decision-grade value accrued at a POST-run verification gate, not at composition (sessions-log.md:3582,:3604)
- 2026-06-13 -- research-agent confabulation hygiene: a cloud research workflow returned plausible-but-unverifiable specifics, and the fix was READ-time subtractive stripping of the unverifiable model-physics (sessions-log.md:4121)

These three mark the boundary, not a refutation: composition-time dominates for the extraction contract + placement + confidence cap, but topic-opacity can defeat any prompt (switch to inline), and a post-run verification/grade gate is a second, complementary value lever -- which is why the recommendation folds that gate back into composition time.

## Recommendation

Reconcile /deep's hardcoded MANDATORY OUTPUT FORMAT with the two composition-time lessons the corpus proved but the skill has not fully absorbed. In .claude/skills/deep/SKILL.md Steps 3-4 (slug/target_path derivation + prompt composition): (1) make the length/citation floors right-sized rather than fixed -- gate the >=6000-word / >=100-citation floor on the Step 2.5 source-aggregator candidate-corpus signal and topic-opacity, relaxing to the proven 2026-04-26 v2 levels (~5,000w / ~50 citations / natural prose) for thin or opaque corpora so the over-constraint failure mode cannot recur; (2) add an explicit post-run gate line: confidence on any /deep-derived doc is capped by its worst load-bearing evidence grade per .claude/skills/brief/ref-evidence-hierarchy.md, and source count is a floor-to-clear, never the deliverable; (3) name the intended verification layer (deterministic check or adversarial re-read) inside the composed prompt's output contract so the post-run value lever is designed in, not bolted on. Ratify via /decide research-composition-gate.

## Apply-when

Before launching any research run (/deep Research-mode prompt, /invest source sweep, or a docs/skill research leg): confirm the prompt already fixes output format + extraction schema + target_path placement + a named confidence/verification gate, and that its length/citation floors are right-sized to the topic's source corpus (not maxed). Self-check: "Is the deliverable's shape and confidence-cap decided in this prompt, or am I hoping to recover it after?" -- if the latter, recompose before running.

## Related
- *hot* (not published) -- session cache; this playbook is surfaced in the consolidation digest
- [[meta-skill-infrastructure-decisions-playbook]]
- *investing-decisions-playbook* (not published)
- *`<private-file>`* (not published)
