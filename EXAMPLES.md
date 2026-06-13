---
categories: [meta]
type: examples
status: active
created: 2026-05-11
updated: 2026-05-11
tags:
  - topic/goal-loops
  - topic/autonomous-mission
---

# Worked /goal examples

`/goal` is the autonomous-loop primitive in the vault: a Haiku evaluator pattern-matches `PASS:` / `FAIL:` lines emitted by Opus during execution, and the loop continues until all named conditions hold simultaneously or a stop clause fires (turn budget exhausted, N-consecutive-failure, etc.). The pattern works because the conditions are stated as transcript-text predicates rather than internal-state assertions -- Haiku evaluates the visible output, not the agent's hidden cognition.

Below are three worked examples that exercise different parts of the loop: a code migration, a structural discipline check, and a self-referential audit loop.

---

## Example 1: Pydantic v1 to v2 migration across a sub-tree

**Condition string:**

```
/goal Migrate Pydantic v1 to v2 across src/models/. All conditions:
(A) Every file in src/models/ that previously imported pydantic.v1.BaseModel now imports pydantic.BaseModel and uses v2 ConfigDict.
(B) `python -m pytest tests/models/` exits 0 -- PASS line: "pytest passed N tests across M modules"
(C) `mypy src/models/` exits 0 -- PASS line: "mypy clean across N files"
(D) No `Config` inner class remains; all converted to `model_config = ConfigDict(...)`.
(E) Frozen / extra / validate_assignment settings preserved byte-equivalent across the migration.

STOP after 25 turns OR 3-consecutive-fail.
```

**Simulated 8-turn transcript outline** (the actual run produces more, but this shows the evaluator-friendly structure):

| Turn | Agent action | Surface text Haiku evaluator reads |
|---:|---|---|
| 1 | Scan src/models/ for v1 imports; emit count | `FOUND: 14 files import pydantic.v1.BaseModel; 9 use inner Config class; estimated 23 conversions` |
| 2 | Apply v1->v2 codemod to `user.py` | `MIGRATED: src/models/user.py -- 2 conversions (BaseModel + Config)` |
| 3 | Apply codemod to `order.py` + `invoice.py` (parallel Edit) | `MIGRATED: 2 files -- 3 conversions` |
| 4 | Apply codemod to remaining 11 files | `MIGRATED: 11 files -- 18 conversions; total now 23/23` |
| 5 | Run pytest on the migrated subtree | `PARTIAL FAIL: pytest passed 47 / failed 3 tests -- field_validator signature change in OrderLineItem` |
| 6 | Fix `field_validator` usage (3 sites) | `MIGRATED: 3 validator sites updated to v2 signature` |
| 7 | Re-run pytest + mypy in parallel | `PASS: pytest passed 50 tests across 14 modules`; `PASS: mypy clean across 14 files` |
| 8 | Final structural check + emit closure | `PASS: Pydantic v1->v2 migration complete; conditions A-E all hold` |

Haiku at turn 8 confirms five `PASS:` predicates, stops the loop, and surfaces the closure summary. The full transcript would have been 50-80 turns of actual editing + test-running, but only the 5 `PASS:` lines mattered for loop-termination decision.

**Tradeoffs observed:**

`/goal` shines when the end-state is mechanically verifiable. Pydantic migration meets that bar -- the test suite + mypy + codemod-result count gives unambiguous condition-met signals. Where it would have failed: if the condition were "the migration is high-quality" or "the code reads better", Haiku would have no surface-text signal to match on, and the loop would either thrash or stop wrong.

The Phase 5 partial-fail at turn 5 is also instructive -- `/goal` does NOT require all conditions to hold every turn. It just requires all conditions to hold at SOME turn before the stop clause fires. The fix-loop ran one more turn, then closure.

---

## Example 2: All Python files in tools/ stay under 500 lines

**Condition string:**

```
/goal Bring every Python file in tools/ under 500 lines via extract-to-lib refactoring. All conditions:
(A) `wc -l tools/*.py tools/lib/*.py` shows every file <= 500 lines -- PASS line: "all-under-500-line check OK; max=X"
(B) `python -m pytest tests/` exits 0 -- PASS line: "pytest passed N tests"
(C) Public API surface unchanged: every function/class previously importable from `tools.<module>` is still importable.
(D) No `from .lib import *` star-imports introduced; only explicit named imports.
(E) Atomic commit on completion with subject "refactor(tools): file-size discipline -- N files split into M lib modules", no Co-Authored-By footer.

STOP after 30 turns OR 3-consecutive-fail OR if file count grows beyond +6 from baseline.
```

**Turn-level evaluator behavior:**

| Turn | Surface text | Evaluator decision |
|---:|---|---|
| 1 | `BASELINE: 7 files over 500 lines; max=1037 (vault-audit.py)` | continue |
| 2-7 | per-file extractions emit `EXTRACTED: <orig> -> <orig> + lib/<helper>; <orig> now N lines` | continue |
| 8 | Run pytest in parallel | `PASS: pytest passed 142 tests` -- (B) holds |
| 9 | Run wc check | `PASS: all-under-500-line check OK; max=487` -- (A) holds |
| 10 | API surface check via importable-symbol grep | `PASS: every previously-importable symbol still resolves` -- (C) holds |
| 11 | Star-import check | `PASS: no star-imports introduced; explicit named imports only` -- (D) holds |
| 12 | Commit with narrow staging | `PASS: commit a1b2c3d "refactor(tools): file-size discipline -- 7 files split into 4 lib modules", no Co-Authored-By footer` -- (E) holds |

Five `PASS:` lines across the transcript = condition met. Loop terminates.

**The interesting bit:** condition (E) is more demanding than it looks. Haiku has to confirm a single commit SHA, the right subject line, AND the absence of a Co-Authored-By footer. The way the agent satisfies this in transcript is to run `git log --format=full -1 HEAD | tee` and pipe the output -- Haiku then sees the full commit metadata in the surface text and matches three sub-predicates in one block. The trick is making the surface text dense enough that one well-shaped command emits multiple `PASS:`-able fragments at once.

**Where this would fail:** if the refactor produced a file that's 501 lines (just over budget) and the test suite is green, Haiku still reports `FAIL: max=501`. The agent then has to find ONE more extraction in that file and re-emit. Three consecutive turns of "max=501 still" would trigger the stop-clause, indicating the budget needs adjustment or the file genuinely can't be split. The non-decreasing-finding-count heuristic is what saves the loop from grinding forever.

---

## Example 3: vault-audit returns score >= 95 (self-referential)

**Condition string:**

```
/goal Bring the vault to score >= 95 with gate=0. All conditions:
(A) `python tools/vault-audit.py --json` final-turn output contains "score":N where N >= 95.
(B) Same output contains "gate_breach": false.
(C) The first prerequisite -- broken_wikilinks array length == 0 -- PASS line: "broken_wikilinks check: 0".
(D) The second prerequisite -- files_missing_frontmatter array length == 0 -- PASS line: "missing_frontmatter check: 0".
(E) hot.md schema validates -- PASS line: "hot-md-check.py: PASS schema-valid".

STOP after 40 turns OR 3-consecutive-fail OR if score regresses two turns in a row.
```

**Why this is self-referential:** `/goal` is asking the vault-audit tool -- a `tools/vault-audit.py` Python file IN THE VAULT -- to declare the vault sound. The audit IS the evaluator's source of truth here. Haiku's job is to pattern-match the audit's `PASS:` / `FAIL:` lines as proxies for "loop should continue / terminate". The agent's job is to identify which findings are blocking the score, fix them, and re-run.

**Typical resolution path:**

1. Run vault-audit; capture `score`, `gate_breach`, and the per-classifier finding lists.
2. If `gate_breach`, prioritize: `broken_wikilinks` first (each is -5 capped at -10), then `missing_frontmatter` (same penalty), then `forbidden_frontmatter`.
3. For broken-wikilink findings, dispatch `wikilink-rewriter.py` (the 2-arg form with source vault for full classification) to convert `[BROKEN-LINK]` to `[REMOVED-PRIVATE]` or `[SCAFFOLD-EXAMPLE]` or `[BROKEN-LINK]` text per source-aware policy.
4. For missing-frontmatter findings, prepend the canonical frontmatter block to each file with appropriate `categories: [audit-log|meta|reference]` + `type:` + `status:` + dates.
5. Re-run vault-audit. Repeat until `gate_breach: false`.
6. After gate is clean, HARD DRIFT (orphans + stale-refs + count-fact drift) typically caps at -5, so a clean gate + uncapped HARD generally lands at 95 exactly.

**The agent's mental model:** -- the score is non-linear because of the GATE cap and the per-tier penalty caps. A single broken wikilink (-5) AND the implicit gate-breach cap (-10 total) means the maximum recoverable score from a non-clean gate is 90. Until the gate is zero, the agent's only meaningful work is gate-clearing. After zero, the agent can choose between (a) chasing HARD findings to push score above 95, or (b) declaring done at 95 if the remaining HARD findings are legitimate operational state (e.g., audit-log files that are correctly orphan because nothing wikilinks to them).

This example demonstrates the deeper `/goal` pattern: the conditions don't have to be independent. They can BE the audit tool. The evaluator just confirms the surface text matches; whatever the agent does to make the audit report green is fine, as long as it doesn't regress the OTHER conditions (which is why E was added -- to prevent the agent from silently breaking hot.md while chasing score).

---

## Patterns that recur across all three examples

**EXPLICIT-PASS-FAIL-FOR-EVALUATOR.** Every condition produces a transcript line starting with `PASS:` or `FAIL:`. Haiku pattern-matches text; it doesn't infer from exit codes or evaluate side effects. The agent's job is to emit unambiguous surface text after every meaningful state change. A condition with no `PASS:` line is a condition the evaluator can't reason about.

**Conditions are independent predicates, not workflow steps.** None of the three examples care about HOW the agent achieved the condition -- they only care that the condition holds at SOME turn. This decouples the loop control from the migration / refactor / repair sequence; the agent can backtrack, retry, parallelize, or completely change tactics, and the evaluator doesn't notice as long as the closure predicates eventually all hold.

**Stop-clauses are the second-most-important part of the spec.** "STOP after 25 turns" is the budget cap. "OR 3-consecutive-fail" is the diagnostic for thrash. "OR if score regresses two turns in a row" is the regression-detector. Without these, a `/goal` loop can run forever burning context. With them, the loop self-terminates with a clear failure mode that maps onto a manual recovery path.

**The condition spec IS the artifact.** Writing the conditions takes 5-15 minutes; running the loop takes 30-90 minutes; reviewing the closure summary takes 5 minutes. Bad condition specs (ambiguous predicates, missing stop-clauses, conditions that fight each other) produce loops that thrash or finish wrong-by-construction. Good condition specs produce shipped work. The leverage is in the spec.
