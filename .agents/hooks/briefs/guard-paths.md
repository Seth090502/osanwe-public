# Porting brief: guard-paths (protected-path write guard)

COLD BRIEF -- written without sight of the manifest test blocks; the executable `test:` in
`.agents/hooks/manifest.yaml` is the acceptance criterion, not this prose. Audience: an agent in
Codex CLI / OpenCode / Goose / Crush / Cline who has never seen this repo.
Criticality: SAFETY-CRITICAL (top port priority). Portable: YES.

## (a) What the gate must guarantee

Before any file-writing tool call reaches disk, the target path is checked against two classes of
protected surface. On match the tool call is REFUSED (the write never happens) and a human-readable
reason is returned to the agent.

1. DATA SURFACE -- absolute block, no override at this layer. Any path containing the directory
   segments `.raw/`, `private/`, `finance/`, or `credentials/`. Rationale: `.raw/` is an immutable
   human raw-notes layer; `private/` holds personal data; the other two are
   reserved secret paths.
2. CONFIG SURFACE (the "X26 guard") -- block-unless-armed. Security-load-bearing config is writable
   only when the operator has deliberately armed a one-shot flag. Membership: anything under a
   `.claude/hooks/` dir; `.claude/settings.json` and `.claude/settings.local.json`; `.claude.json`;
   `CLAUDE.md`, `CLAUDE.local.md`, `AGENTS.md`; nine named guard scripts under `tools/`
   (session-start.sh, vault-score-check.py, pre-write-validator.py, wikilink-check.py,
   frontmatter-check.py, orphan-check.py, hot-md-check.py, bump-updated.sh, .agents/scripts/sync.py); and the
   cross-harness surface `.agents/mcp/*`, `.agents/scripts/*`, `.agents/hooks/*`, `.mcp.json`,
   `opencode.json`, `.codex/config.toml`.

Empirical basis for class 2: on 2026-07-02 a rogue process wrote `~/.claude/settings.json` without
authorization. The guard exists so a compromised or confused agent cannot silently rewrite its own
safety rails.

## (b) Reference implementation + load-bearing facts

Reference: `.claude/hooks/guard-paths.sh` (bash, ~93 lines).

1. THE ARM FLAG IS CONSUMED PER WRITE. The flag is the existence of the file
   `<repo>/.claude/state/config-edit-armed`. On an allowed config write the guard DELETES the flag
   before allowing, so one arm buys exactly one write. A port that treats the flag as a session-long
   mode is WRONG.
2. EVERY ARMED ALLOW IS LOGGED: append an ISO-8601 timestamp + the allowed path to
   `<repo>/.claude/state/bypasses-<YYYY-MM-DD>.log`. Logging failure must not break the allow.
3. PATH NORMALIZATION FIRST: backslashes -> forward slashes (Windows hosts emit
   `C:\...\private\x.md`). Data-surface matching is on `/<segment>/` WITH the leading slash, so
   `myprivate/` does not false-positive.
4. NO PATH IN THE PAYLOAD => ALLOW. Unparseable JSON or an unknown tool shape exits allow. Fail-OPEN
   here is deliberate: this is a path filter, not a payload validator; other gates fail closed.
5. THE DATA SURFACE HAS NO ARM ESCAPE. Arming affects class 2 only; no env var and no flag permits a
   `private/` or `.raw/` write through the tool layer. Corrections go to the human instead.
6. ORDERING: data-surface checks run BEFORE the config check, so a path that is both (e.g.
   `private/.claude/settings.json`) is refused outright, not merely gated.

## (c) Where to bind it

Abstract lifecycle: `pre-tool-use (blocking)`, matcher = the harness's file-writing tools (Claude
Code: Write|Edit|MultiEdit). Per the event table in `.agents/hooks/README.md`, row
`pre-tool-use (blocking)`: Codex CLI `pre_tool_use`; OpenCode plugin throw / `permission.ask` deny;
Goose pre-tool event with decision-block; Crush `PreToolUse` exit 2/49 or JSON deny; Cline
`mode: blocking` + `fail_closed`. Crush caveat: PreToolUse is the ONLY interception point Crush
offers -- which is exactly what this gate needs, making guard-paths the one safety-critical hook
that ports to Crush with zero loss.

## (d) Input shape

A single JSON object on stdin. Only two fields matter: `tool_name` (string, used only to scope the
matcher if the harness does not scope it for you) and `tool_input` (object) whose file path is at
`tool_input.file_path`, with `tool_input.path` as a fallback alias; absent/empty => allow.
Block convention: nonzero blocking exit (Claude Code: exit 2) plus one stderr line naming the class
and the offending path. Allow: exit 0, no output required.

## (e) Non-goals and known residuals

- X30 (documented, accepted): PreToolUse sees TOOL-layer writes only. A shell command
  (`bash -c 'echo x > private/foo.md'`) bypasses this guard entirely. Do not claim shell coverage;
  if the harness exposes a shell pre-hook, covering it is a SEPARATE gate.
- `Atlas/` is deliberately NOT hook-enforced -- human-write-only by convention. Adding it would break
  the Pattern-20 stamp paths the human ratifies.
- No content inspection, no frontmatter validation, no vault scoring: separate hooks own those.
- The arm-flag path is hardcoded to the repo root in the reference. A port SHOULD resolve it from
  the repo root it is bound to rather than copying the literal `...` string.
- STALE MEMBERSHIP (noted 2026-09-21; the brief body is left as the cold record it was written as).
  The config-surface list in (a) class 2 names nine guard scripts and stops there. The reference
  implementation has grown twice since: on 2026-08-13 it added the launcher and lane surface
  (`tools/claude-shim.ps1`, `claude-launcher.ps1`, `lane-arm.ps1`, `append-only-check.py`,
  `cc-statusline.sh`) and on 2026-08-17 the relay containment stack (`tools/relay.py`,
  `lib/relay_exec.py`, `lib/relay_mcp.py`, `lib/relay_schema.py`, `relay-apply.py`,
  `relay-batch.py`, `delegate.py`, `mode3-normalize-proxy.py`). Read the case list in
  `.claude/hooks/guard-paths.sh` for the current membership; a port built from this brief alone
  would leave thirteen security-load-bearing files unguarded. Also note that the ninth "tools/"
  script in that list, `.agents/scripts/sync.py`, is not under `tools/`.
