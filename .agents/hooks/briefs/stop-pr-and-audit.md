# Porting brief: stop-pr-and-audit (session-end audit gate + PR)

COLD BRIEF -- written without sight of the manifest test blocks; the executable `test:` in
`.agents/hooks/manifest.yaml` is the acceptance criterion, not this prose. Audience: an agent in
Codex CLI / OpenCode / Goose / Crush / Cline who has never seen this repo. Criticality:
SAFETY-CRITICAL. Portable: HYBRID -- the audit gate ports cleanly; the "refuse to stop" delivery is
Claude-shaped.

## (a) What the gate must guarantee

Two guarantees at session end, in strict order.

1. AUDIT GATE (the portable half). A session may not be declared finished while the repository is
   below its quality floor. Run the repository audit; if it reports ANY GATE-tier finding, or a
   composite score below 95/100, the session does NOT end quietly -- the agent is told to fix the
   findings and the PR half is SKIPPED. The message must name the score, the GATE count, and the
   concrete remedies (run the audit skill, run repair, or set the logged bypass env var).
2. PUBLICATION (the conditional half). Only on a clean audit: if the session branch has commits
   ahead of its remote tracking branch, push it and open a pull request against the default branch.
   Agent work is published for review; it is never merged by the agent.

Both halves are best-effort on infrastructure: a missing audit script, missing `gh`, unauthenticated
`gh`, or no remote must degrade to a printed instruction -- never a crash, never a false "clean".

## (b) Reference implementation + load-bearing facts

Reference: `.claude/hooks/stop-pr-and-audit.sh` (bash, ~85 lines).

1. RE-ENTRY GUARD IS MANDATORY. The payload carries `stop_hook_active`; if true, exit 0 immediately.
   Without it, a hook that blocks Stop and thereby causes another Stop loops forever. Any port to a
   harness with a blocking session-end event MUST reproduce an equivalent guard (a state file or a
   once-per-process latch if no flag is provided).
2. THE FLOOR IS 95 AND THE GATE COUNT IS 0 -- both block: `gate_count > 0 OR score < 95`. Source of
   truth is `tools/vault-audit.py --json`; read `tiers.gate.count` and `score` from the JSON. Do NOT
   regex the human-readable output: an earlier version did, and it under-counted because it only saw
   broken-wikilinks and missed missing-frontmatter, schema, and template-drift.
3. AUDIT FAILURE DEFAULTS ARE PERMISSIVE, DELIBERATELY. If the audit subprocess or the JSON parse
   fails, the reference substitutes `gate_count=0` and `score=100` -- it does not block the session
   on broken tooling. This is a conscious asymmetry against the pre-write validator (which fails
   CLOSED). Keep it: a session-end hook that fails closed on tooling breakage traps the agent.
4. THE BLOCK IS DELIVERED AS JSON, NOT AN EXIT CODE: print `{"continue": true, "reason": "..."}` on
   stdout and exit 0. `continue: true` means "keep the agent going and hand it this reason" -- the
   Claude-bound half of the hybrid. A port must map it onto whatever "return control to the model
   with a message" primitive the harness offers.
5. PUSH PRECONDITIONS, IN ORDER: branch not main/master and not detached -> `git fetch origin
   <branch>` -> `git rev-list --count origin/<branch>..<branch>` > 0 -> `gh` present ->
   `gh auth status` ok -> `git push -u origin HEAD` -> `gh pr create --fill --base main`. Any
   precondition failing exits 0 with a stderr note; none of them is an error.
6. THIS REPO CURRENTLY HAS NO REMOTE, so the PR lane is INERT in practice. Ports must still be
   correct, but conformance evidence for the PR half cannot be collected on this machine -- say so
   rather than claiming a verified push path.

## (c) Where to bind it

Abstract lifecycle: `session-end`. Per `.agents/hooks/README.md`, row `session-end`: Claude Code
`Stop`; Codex CLI `session_end`; OpenCode plugin event; Goose session events; Crush NONE (Crush
intercepts PreToolUse only -- a Crush port CANNOT run this gate, and that loss must be stated, not
papered over); Cline hook config. Harnesses whose session-end event is non-blocking can still port
half 1 as a LOUD warning plus a nonzero process exit for CI, but cannot reproduce "the model keeps
working until the vault is clean". Document which one you got.

## (d) Input shape

Stdin: harness session-end JSON. Only field consumed: `stop_hook_active` (boolean; any parse failure
is treated as false, i.e. proceed). Environment: `git`, `python`, the audit script, optionally `gh`;
the working directory must be forced to the repo root. Outputs -- clean with nothing to push: exit 0
silent. Audit failure: the continue-with-reason JSON on stdout, exit 0. Infrastructure gaps: a
human-readable note on stderr, exit 0.

## (e) Non-goals and known residuals

- NEVER merge, never push to main/master, never force-push. The gate publishes for human review;
  that is the whole point of the main-is-reviewed-state invariant.
- No commit creation here. This brief was written when a separate post-tool-use hook made a
  commit per write. The Claude Code copy of that hook was RETIRED on 2026-09-12 and is a no-op;
  the Codex copy (`.codex/hooks/auto-commit.sh`) still stages and commits every edit with
  `--no-verify` on any branch other than main or master, unless disabled (audit defect D31), and the
  scheduled weekday
  `/brief` run commits its own outputs. A port must not add commit creation to this hook.
- The bypass named in the block message (`CLAUDE_VAULT_BYPASS_VALIDATOR=1`) is a pointer to the wider
  bypass registry; this hook does not read it. Do not invent a new bypass var for the port.
- Score thresholds drift with doctrine (95 today). Treat them as parameters, not as literals baked
  into the port's tests.
