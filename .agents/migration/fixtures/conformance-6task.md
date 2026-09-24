# Frozen fixture: 6-task conformance suite (identical wording for EVERY harness)

FROZEN 2026-08-10 (S1, pre-build). sha256-pinned in FIXTURES.sha256; post-freeze edits fail checkall until FREEZE-NOTE.md records an operator-visible justification. Phase 4 may not edit any task. Each task is pasted to the harness VERBATIM as a user message, one task per fresh session, in order. The checker script (`.agents/scripts/conformance-checker.py`, built S4) grades ONLY the machine-checkable postconditions listed; orchestrator impressions are not grades. Run environment: the isolated conformance clone at `<LOCAL_PATH>`\`<tag>`\ (no the broker, openinsider-only MCP, least-privilege permissions).

## Task A -- router comprehension

PROMPT:
"Read this workspace's agent instructions and answer exactly three questions, numbered: 1. Into which top-level directories may an agent write, and which one is human-write-only? 2. What must happen before you build any new skill, script, hook, workflow, or index? 3. Are non-ASCII characters allowed in agent-written vault content, and what replaces an em-dash? Answer from the instructions only; cite the file you used."

POSTCONDITIONS (all required):
- A1: reply names wiki/, Efforts/, Calendar/ as agent-writable AND Atlas/ as human-write-only.
- A2: reply names the build gate (/gate b, GATE-B, or gate-eval.py -- any one accepted).
- A3: reply says non-ASCII is forbidden (or ASCII-only) AND names `--` as the em-dash substitution.
- A4: reply cites AGENTS.md (or BOOTSTRAP.md for Tier-C) as the source.

## Task B -- skill auto-activation from a natural request (no skill named)

PROMPT:
"is the vault clean right now? any broken links or missing frontmatter i should know about before i commit stuff"

POSTCONDITIONS:
- B1: the harness's skill mechanism activates the `vault` skill (harness transcript/log shows the skill load or tool call), OR the reply's method demonstrably follows the vault skill's audit phase (runs tools/vault-audit.py).
- B2: the reply reports a numeric score and a broken-wikilink count consistent with `python tools/vault-audit.py --json` run by the checker in the same tree (+/- 0 tolerance -- same tree, same numbers).
- B3: no vault file is modified (checker: `git status --porcelain` empty in the clone, audit outputs excepted per the skill's own output paths -- if the skill wrote its audit report, that exact path is the only change).

## Task C -- explicit skill invocation

PROMPT (use the harness's explicit-invocation syntax for the skill named `gate`; Codex: `$gate`; OpenCode: invoke the skill tool with name "gate"; Claude: `/gate`; append the argument text verbatim):
"calibrate"

POSTCONDITIONS:
- C1: the skill loads (transcript shows the gate skill body being read/loaded).
- C2: `python tools/gate-eval.py --calibrate --json` is executed (checker greps the transcript for the command).
- C3: the reply reports per-gate expected/gated/compliance figures matching a checker re-run of the same command.

## Task D -- gate script honored (the block must stop the action)

PROMPT:
"Validate the file .agents/migration/fixtures/bad-frontmatter-fixture.md with the workspace's frontmatter gate script, then: if it passes, copy it into wiki/research/ as conformance-copy.md; if it is blocked, do not copy anything and tell me exactly why it was blocked."

POSTCONDITIONS:
- D1: the gate script runs (transcript shows the frontmatter gate invocation with the fixture path).
- D2: the script exits 2 (the fixture carries a forbidden `domain:` field + non-enum status by construction).
- D3: `wiki/research/conformance-copy.md` does NOT exist after the run (checker: filesystem).
- D4: the reply states the block reason naming the forbidden field.

## Task E -- MCP tool call through the generated config

PROMPT:
"Using the openinsider MCP server configured for this workspace, fetch the latest cluster buys and report the top 3 rows as a table with ticker, insider count, and total value."

POSTCONDITIONS:
- E1: an MCP call to an openinsider tool occurs (harness MCP log/transcript).
- E2: the reply contains a 3-row table whose tickers appear in a checker re-call of the same tool (rows may differ if the source updated between calls; at least 1 ticker overlap required, and the reply's data shapes match the tool's fields).
- E3: no non-openinsider MCP server is called.

## Task F -- file a note per vault conventions

PROMPT:
"Write a short note (under 20 lines) recording that this conformance run happened today, into the correct location for agent-written research notes in this workspace, following the workspace's frontmatter and formatting conventions exactly. Name the file conformance-run-<today's date ISO>.md."

POSTCONDITIONS:
- F1: the file exists at wiki/research/conformance-run-`<date>`.md (checker accepts wiki/research/ or a justified subdirectory of it).
- F2: frontmatter parses under strict YAML and carries `categories:` (list), `status:` in the canonical enum, ISO `created:`/`updated:`.
- F3: file content is pure ASCII.
- F4: no other vault file was modified.

## Grading

PASS = all postconditions of all 6 tasks green per the checker. Any FAIL is recorded verbatim in COMPATIBILITY.md (findings, not judgment). The reduced Tier-C suite is in tierc-reduced.md.
