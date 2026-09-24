---
aliases: [conformance-hermes]
categories: [meta]
type: report
status: complete
created: 2026-08-23
updated: 2026-08-23
tags: [topic/meta]
related: ["[[COMPATIBILITY]]", "*osanwe-v2-hermes-mission* (not published)"]
---

# Conformance record -- Hermes Desktop (OSANWE-V2-2026-08)

verification: EXECUTED-IN-PART (this document IS the record; produced by the first
long-form Hermes session in this vault, mission OSANWE-V2-2026-08, model
x-preview-f-free via provider opencode-free). Harness: Hermes Desktop, Windows 11,
agent runtime v0.20.x-class. Session window: 2026-08-23 ~05:25 ET onward.

## What was exercised live (VERIFIED in-session)

| surface | result | evidence |
|---|---|---|
| AGENTS.md chain | LOADED via direct disk read (130/130 lines); NOT auto-injected as context file on this profile -- deviation logged (probe.md #9) | Efforts/osanwe-v2-overhaul/_work/probe.md |
| Terminal discipline | Git Bash; background+wait OK; script-file invocations pass approvals; `bash -c` complex one-liners gate | FINDINGS F-010 |
| Gate CLIs | tools/gate-eval.py x7 computes, verdicts transcribed into sheets + registry | wiki/research/gates/gate-b-* |
| Pre-commit cage | core.hooksPath=.githooks active for Hermes commits; 14/14 tests; blocked its own author twice (working as designed) | tools/test-precommit.py runs |
| delegate_task | fan-out verified (probe child wrote deliverable); census legs partially killed by provider HTTP 503s -> self-run fallback per A4.4 | _work/dead-weight-sweep.py etc. |
| Vault writes | canonical frontmatter enforced on every new note; cage R1-R6 live across 40+ commits | CHANGES.md commit chain |
| Generated organs | gen-ledger-views byte-identical cutover; gen-hot checker-green; usage/resident/census tools shipped and run | W3 commits |
| Calibration engine | backtest-prediction.py graded 54 point-in-time predictions vs verifiable prices; calibration-report.py emitted confidence-calibration + factor-attribution report (checker-clean) | wiki/maintenance/calibration/ |

## Cross-harness end-to-end proof (2026-08-23 evening)

Claude Code headless smoke (`claude -p`, plan mode) on the SAME repo state: session
booted through the (fixed) hook chain, relayed overdue open-loops FIRST per rule 2,
quoted AGENTS.md heading, reported `Score: 95/100` -- i.e. both harnesses now verify
against identical architecture state. The smoke ALSO exposed one more instance of the
MSYS-path bug class (semantic-context-inject.py hook registered with /c/... path,
blocking every Claude prompt); fixed in .claude/settings.json (25 command paths
normalized to C:/...). Evidence: _work/claude-smoke.txt (pre-fix failure),
_work/claude-smoke2.txt (post-fix success).

## Known losses / unverified cells under Hermes

- the broker read MCP absent -> share counts UNVERIFIED in Hermes sessions (D-SEC-1
  unchanged: no order tools by registry default-refuse).
- pretrade-token-gate portable:NO -- absent by design (COMPATIBILITY behavioral gates).
- SessionStart hook surface does not fire (Claude-side); BOOTSTRAP.md substitutes --
  VERIFIED adequate: this session ran the BOOTSTRAP command list manually at start.
- HERMES_WRITE_SAFE_ROOT enforcement UNCONFIRMED on this profile (F-005).
- Skills discovery of .agents/skills requires `hermes skills trust` (pending operator);
  canon skill invocation test therefore performed CLI-equivalently (gate CLIs + checkall),
  not via /skill activation.
- Cron/gateway unattended-run behavior on Windows: PROBE PENDING (HERMES_CRON_PROBE=1;
  deferred to operator-present window).

## Verdict

Hermes is a competent Tier-B writer in this vault UNDER THE CAGE: every invariant that
matters held mechanically (zero protected-path violations, zero ledger rewrites, ASCII
clean on authored bytes) while the flexible surfaces (context injection, approvals,
skills trust) degraded exactly as COMPATIBILITY predicted. Recommend Tier-B listing
with the five cells above marked unverified/pending.
