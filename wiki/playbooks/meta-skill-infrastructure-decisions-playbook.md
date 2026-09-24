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

# Meta skill infrastructure decisions Playbook

## Pattern
Invariant: A meta/skill-infrastructure decision in this vault reaches ratified status only when it is bound at decision time to a referent that already exists -- a dated case it was extracted from, an at-scale empirical validation, or a fail-closed mechanical artifact -- and names the on-disk file it writes to; a decision justified only by anticipated future utility is built speculatively and gets reverted, deprecated, or killed instead.

The 33 rows are two rituals sharing one gate. The 8 "pattern codified" rows (2026-04-30 + 2026-05-04) each extract a named pattern from ONE dated case (AMD 4/30, GOOGL 4/30, /retro 5/04), test it for cross-domain reach, and write it to a named ref-doc (ref-research-insights.md) with a commit hash -- an observation that fails the generalization test never gets codified. The infrastructure rows ratify on empirical validation at scale (8/8 Phase-L/Phase-F idempotency across 6 tickers; VOO scored 91/100; marker-sig zero-diff) or on fail-closed mechanical enforcement (vault-audit.py, the SessionStart hook). The vault states its own failure mechanism in a post-mortem -- a skill "lacks operational forcing function -> amortizes to zero" -- which is exactly why the speculative builds (Codex CLI dual-tool v1, /research, /review, the OpenClaude fork) were unwound while every referent-anchored decision held. Mining artifact worth knowing: 8 of the 9 rows tagged meta/skill-infrastructure are investing-methodology patterns written to Atlas/sources/investing/, so the genuine skill-architecture population is ~25, not 33.

Confidence: 73% -- full population read (33/33 rows at decision-log.md:23-97, not a sample), all counter-cases resolve to exact lines, and the mechanism is quoted from the vault's own amortizes-to-zero post-mortem; discounted because the invariant is a union of two rituals and partly restates existing GATE-B / Simplicity-First doctrine, so a sharper single-rule cut may exist.

## Evidence
- 2026-05-04: KINETIC-AS-ENTRY-TIMING-NOT-HEDGE pattern codified
- 2026-05-04: ANALYST-OUTLIER-PT-DOES-NOT-INVALIDATE-DOCTRINE pattern codified
- 2026-05-04: STACKED-CONVICTION-BETS-COMPOUNDING-TAIL-RISK pattern codified
- 2026-04-30: 8/8 same-day Phase L<->Phase F idempotency milestone validated (compounding-loop architecture mature at scale)
- 2026-04-30: 5-VECTOR-INSTITUTIONAL-BEARISH-CLUSTERING pattern codified
- Threshold cleared: >= 3 ratified decisions in domain (observed 33).

## Counter-cases

- 2026-04-26 -- Codex CLI dual-tool migration built (8 commits) then REVERTED "for strategic optionality," then RE-ADOPTED 2026-07-08 as the AGENTS.md-inverted canonical dual-engine router (Calendar/decisions/decision-log.md:89; docs/Osanwe Vault Codex.md:2434): the same infra decision flipped abandon -> re-adopt as the present referent (a live second engine) materialized -- speculative when reverted, referent-backed when re-adopted
- 2026-04-28 -- prevention-arch H2 body-length refactor REVERTED days after adoption for quality preservation; tag prevention-arch-v8 re-marks the quality-preserving state (Calendar/decisions/decision-log.md:466,482-483) -- a validated-seeming change unwound the moment the regression proved out against the real referent
- 2026-04-26 -- /research + /review deprecated unused; post-mortem: a skill "lacks operational forcing function -> amortizes to zero" (Calendar/decisions/decision-log.md:293,924; OpenClaude fork KILLED at :74) -- the measured mechanism behind the invariant
- (no in-window falsifier found -- searched the full 33-row table plus the decision-log narrative for any ratified row lacking a referent+artifact, or any reverted row that had both; every reversal traces to a missing or failed referent)

## Recommendation

The enforcement point already exists on disk: /gate b (build-vs-ship; .claude/skills/gate/SKILL.md; verdicts from tools/gate-eval.py). Route every future meta/skill-infrastructure BUILD proposal through /gate b BEFORE it consumes implementation budget, and require the ratifying /decide row to name (a) its present referent -- dated case, at-scale empirical run, or fail-closed mechanical artifact -- and (b) the on-disk destination file; absent either, stamp it speculative, not ratified. Secondary: fix the consolidator's domain normalization (tools/consolidator.py _norm_domains) so the 8 investing-methodology pattern-codified rows written to Atlas/sources/investing/ref-research-insights.md count under investing -- the 33-largest-cluster figure is inflated by ~8 mis-domained rows.

## Apply-when

Before logging a new meta/skill-infrastructure decision as ratified: in one line, name the concrete referent it was proven against (a dated case, an at-scale empirical run, or a fail-closed mechanical artifact) AND the on-disk file it writes to. If either is blank, it is a speculative build -- route it through /gate b and do NOT stamp it ratified.

## Related
- *hot* (not published) -- session cache; this playbook is surfaced in the consolidation digest
- [[bash-exit-code-1-playbook]]
- [[bash-exit-code-2-playbook]]
- [[read-unclassified-playbook]]
