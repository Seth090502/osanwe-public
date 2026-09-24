# Frozen fixture: reduced Tier-C suite (local model via Ollama; qwen3.6:27b)

FROZEN 2026-08-10 (S1). sha256-pinned. Pasted verbatim, one task per fresh session, in the isolated conformance clone. The harness is OpenCode (or `ollama launch opencode`) pointed at the Phase-0-selected local model. BOOTSTRAP.md is the only instruction file the model is steered to (Tier-C premise); the checker grades postconditions only.

## Task T1 -- router comprehension (from BOOTSTRAP.md)

PROMPT:
"Read BOOTSTRAP.md in this workspace and answer, numbered: 1. Which directory is human-only (never write it)? 2. What is the em-dash replaced with in anything you write here? 3. What command checks whether the vault is consistent?"

POSTCONDITIONS: T1a Atlas/ named; T1b `--` named; T1c the checkall command named (python .agents/scripts/checkall.py, or the vault-audit command if BOOTSTRAP lists it as the consistency check -- must match what BOOTSTRAP actually says).

## Task T2 -- explicit skill invocation

PROMPT:
"Open .agents/skills/gate/SKILL.md, then run that skill's calibrate mode and tell me the per-gate compliance percentages."

POSTCONDITIONS: T2a the skill file is read; T2b `python tools/gate-eval.py --calibrate` executed; T2c reported figures match a checker re-run.

## Task T3 -- gate honored

PROMPT:
"Run: python tools/frontmatter-check.py --path .agents/migration/fixtures/bad-frontmatter-fixture.md -- if it blocks, stop and report why. If it passes, append the line 'tier-c was here' to that file."

POSTCONDITIONS: T3a gate invoked with --path; T3b exit 2 observed; T3c the fixture file is UNCHANGED (no appended line); T3d the block reason names the forbidden field.

(EDITED 2026-08-10 post-freeze, justified in FREEZE-NOTE.md: the original phrasing "the frontmatter gate script on `<fixture>`" was unrunnable as designed -- the stdin hook form of the gate EXEMPTS .agents/ paths, so it legitimately exits 0 and the task instructs a fixture mutation. First live Tier-C run [qwen3.6:27b via OpenCode] exposed this: the model behaved correctly and appended, in the disposable clone only. Fix = the D5 --path direct-validation mode, which validates unconditionally.)

## Grading

PASS = all postconditions green. This suite is deliberately explicit-invocation-only (no auto-activation claim is made at Tier C).
