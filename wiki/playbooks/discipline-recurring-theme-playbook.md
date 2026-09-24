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

# Discipline (recurring theme) Playbook

## Pattern
Invariant: A discipline rule changes the agent's in-session behavior durably only where a mechanical artifact evaluates it as a binding gate at the point of mutation (block-before-write, fail-closed validator, immutable authoritative variable, commit-halt, exit-2) -- a rule delivered as prose reverts silently even when MANDATORY-labeled and even immediately after a manual cleanup, and a mechanism whose own invocation is prose-governed drifts the same way; but mechanization can only bind where an in-session mutation point exists, so when the rule's terminal act is out-of-session, stacking more mechanism only relocates the gap (that axis belongs to *execution-gap-playbook* (not published)).

The corpus's cleanest proof is a one-day natural experiment: the 04-26 Vault SOTA arc cleared forbidden strings by hand (score 60 -> 100), then 04-27 retro commits silently reintroduced them and dropped the score to 35/100 with no gate at the write point (sessions-log.md:1006-1012); the fix that held was the 04-28 PreToolUse pre-write-validator blocking the mutation before disk (:1022). The same shape recurs across unrelated substrates -- invest-max phase drift ended only when --phase prose became the immutable PHASE_NUMBER variable (:66); cc-coach's advice changed behavior 0/8 times as advisory stdout and bound only once redelivered as a binding system-reminder (:963-964); hot-md-check blocked nothing until its exit code moved 1 -> 2 (:1873). The load-bearing variable is never the rule's content or its MANDATORY label -- it is whether the rule is evaluated as a binding instruction at the exact mutation point; naming a doctrine ceiling a "gate" in prose (:967) did not make it one, only tools/gate-eval.py later did.

Confidence: 83% -- all 5 evidence rows resolve and converge across independent substrates (phase variable, frontmatter gate, hook delivery-mode, exit-code, F11 timing) with a clean 100->35 one-day natural experiment; discounted because the Codex instruction-honored posture is a designed-but-untested exception to the strong form and the binding-vs-advisory refinement rests largely on the single sharp cc-coach case.

## Evidence
- 2026-05-04: theme 'discipline'
- 2026-04-08: theme 'discipline'
- 2026-04-22: theme 'discipline'
- 2026-04-26: theme 'discipline'
- 2026-04-27: theme 'discipline'
- Threshold cleared: >= 3 distinct sessions share theme (observed 12).

## Counter-cases

- 2026-04-27 -- cc-coach Layer D scored 0/8 lifetime compliance: a mechanical hook that FIRED all 8 times yet changed behavior zero times, because it injected advice as advisory stdout rather than a binding instruction. Bounds the invariant -- mechanical per se is insufficient; binding-delivery-at-the-decision-point is the operative condition (Calendar/decisions/sessions-log.md:963-964)
- 2026-04-22 -> 2026-05-04 -- F11 timing: the auto-commit-suppression mechanism existed and worked, but its invocation timing was prose-governed and drifted repeatedly (7 micro-commits vs 2 planned on 05-04) until the invocation itself was encoded in tools/lib/f11_orchestrator.py -- a mechanism with a prose-governed trigger drifts exactly like prose (sessions-log.md:537,:1886; Atlas/sources/meta/ref-execution-discipline.md:48-64)
- 2026-04-26 -- the Codex CLI posture is instruction-honored BY DESIGN (session branch + per-write commit + PR-on-Stop honored by instruction where Claude Code enforces via hooks): the one genuine same-discipline-without-a-hook case -- honest caveat: designed but NOT stress-tested at scale in the corpus (sessions-log.md:234,:241)
- 2026-07-05 -- mechanical gates ARE overridden, but the override is itself mechanically gated and logged (.claude/state/bypasses-2026-07-05.log: guard-paths CONFIG-EDITs "armed, flag consumed"; GATE bypasses only on test-tmp/ harness paths) -- the escape hatch is a logged mechanism, not silent drift

## Recommendation

Extend Atlas/sources/meta/ref-execution-discipline.md (which today scopes ONLY F11 + cascade -- F11 is one instance of the general rule) with an "Enforcement-point placement" section stating this invariant plus the 3-step test in Apply-when; Atlas is human-write-only, so the amendment rides /decide ratification. Do NOT rebuild what already gates at a mutation point (pre-write-validator, the 95-floor vault-audit GATE, ASCII byte-scan, guard-paths.sh, doctrine-lint, gate-eval.py, pretrade-token-gate + D-SEC-1 deny, PHASE_NUMBER, f11_orchestrator). The one residual in-session item still prose-enforced is the MANDATORY subagent-dispatch discipline (sessions-log.md:1822; it empirically failed under context pressure 2026-05-06, :2366/:2401) -- route it through /decide dispatch-discipline-gate (build-vs-accept; the PreToolUse hook fix is already named). For any rule whose terminal act is out-of-session, add NO in-session gate -- defer to *execution-gap-playbook* (not published).

## Apply-when

Before writing or ratifying any new discipline mechanism (rule, MANDATORY marker, ref-doc paragraph, checklist): (1) locate the rule's mutation point; (2) if it is an in-session tool/commit call, confirm a hook/script/immutable-variable evaluates it there as a block (exit-2 / fail-closed / binding system-reminder), never advisory prose -- if none, place the gate first; (3) if the terminal act is out-of-session (broker order, send, apply, book, elevated shell), STOP -- no in-session mechanism will bind it.

## Related
- *hot* (not published) -- session cache; this playbook is surfaced in the consolidation digest
- [[meta-skill-infrastructure-decisions-playbook]]
- *investing-decisions-playbook* (not published)
- *`<private-file>`* (not published)
