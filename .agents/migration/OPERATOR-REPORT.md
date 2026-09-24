# Cross-harness migration -- operator report (plain language)

Written 2026-08-10, end of the overnight S2-S5 run. Everything below is committed on
branch `cross-harness-migration`. Two things need YOUR action (bottom of this file).

## What exists now

- **Your 15 skills live in ONE canonical place:** `.agents/skills/<name>/`. Six other
  agent tools (Codex, OpenCode, Goose, Crush, Cline, Pi) read that folder natively.
  Claude Code keeps working exactly as before -- it reads generated copies in
  `.claude/skills/`, rebuilt from canon by a script. You never edit the copies.
- **Every skill description was compressed** (the invest one went from 4,848
  characters to 454). Result: ALL 15 skills now fit Claude's listing budget --
  before tonight, most were invisible to auto-routing ("name-only"). Three test
  phrases that never routed before now route correctly every time.
- **Safety got tighter, not looser:** 2 previously-unguarded broker option-exercise
  tools are now denied (18 -> 20); the pretrade hook now actually sees every broker
  tool (its defense branches were unreachable dead code before); brokerage tools are
  NEVER given to any non-Claude harness (they are omitted from those configs entirely,
  not just "denied"); your name+email were removed from the committed Codex config.
- **A second harness ran the whole stack tonight**: OpenCode + the local qwen model
  (no cloud account, no cost) read the rules, listed exactly 15 skills, ran the gate
  skill correctly, pulled live insider data through the generated config, and was
  BLOCKED by the ported write-guard when told to write into private/. The local
  Tier-C model also passed its 3-task suite.
- **One consistency command:** `python .agents/scripts/checkall.py` -- run it any
  time; if something is wrong it prints WHAT BROKE / WHAT IT MEANS / WHAT TO DO /
  WHAT TO PASTE BACK in plain language.

## What did NOT change

Claude Code daily use: same skills, same hooks, same gates. The full regression suite
matches its baseline cell-for-cell (the one known pre-existing failure, T9, is
unchanged). All 6 neutral test suites green. The weak-model comprehension test of the
rewritten rulebook scored 10/10 on the first run.

## Per-harness quickstarts

- **Claude Code:** nothing to do. (Next session start picks up the new `.mcp.json`.)
- **Codex CLI (0.147.0, upgraded tonight):** `codex login`, then run `codex` in
  the vault root once and ACCEPT the trust prompt (loads `.codex/config.toml`).
  Brokerage tools are absent until a verification probe passes -- deliberate.
- **OpenCode (1.18.16, installed tonight):** works today with the local model:
  `set OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` then `opencode` in the vault. That env
  var stops skills being listed twice (15, not 30). For a cloud model:
  `opencode auth login` with any compliant key -- NEVER the Claude subscription.
- **Goose / Crush / Cline / Pi:** configs and porting briefs ship; none has been run
  yet (honestly marked UNRUN in docs/compatibility.md).
- **Local-only (Tier C):** point any harness at Ollama `qwen3.6:27b` (pulled tonight,
  17 GB; Ollama upgraded to 0.32.6). The standalone rulebook is `BOOTSTRAP.md`.

## What you lose per tier (full table: docs/compatibility.md)

Off Claude: no subagent fleet or parallel workflows (each skill runs its documented
inline path instead -- same steps, sequential), no auto-commit/PR (you commit
yourself, same message format), no session-start auto-surface (BOOTSTRAP lists the
4 commands). Pi additionally has no MCP data tools. The pretrade order-execution
hook does NOT travel by design -- other harnesses simply never get order tools.

## Routine workflows now

- **Add/edit a skill:** edit `.agents/skills/<name>/` (rules: `.agents/skills/AGENTS.md`),
  run `python .agents/scripts/sync.py`, then `checkall.py`, commit both trees together.
- **Add an MCP server:** add it to `.agents/mcp/servers.json` (env var NAMES only,
  mark read/write surface), run `python .agents/scripts/gen-mcp-configs.py`, commit.
  Write-capable servers are auto-refused from harness configs until proven -- that is
  the point.
- **Add a harness:** read docs/compatibility.md tiers; give it AGENTS.md + `.agents/skills/`
  + a generated MCP config; port hooks from `.agents/hooks/briefs/` if it supports them.

## The two things waiting on YOU

1. **Routing-delta approval (typed, default REJECT):** open
   `.agents/migration/baselines/smoke-post/DELTA-REVIEW-TABLE.md`. 26/31 phrases
   identical; 3 pure improvements; 2 rows changed within noise (CP1: one "exit `<coin>`"
   run routed to /gate instead of /decide -- arguably correct discipline; CP5: /spark
   activated 2/3 instead of 3/3). Nothing mis-routes to a WRONG skill. Cutover's
   final step waits for your explicit approval line.
2. **Credentials (optional):** `.agents/migration/CREDENTIALS-ASK.md` unchanged.
   Without them, 4 DoD items stay BLOCKED with receipts
   (`.agents/migration/verification/BLOCKED-RECEIPTS.md`) -- nothing else is held up.

## Rollback

Everything pre-cutover is additive commits on the branch: any batch reverts with one
`git revert` of its commit. The conformance clone at `` cannot reach
the real vault (separate object store, no remotes, hooks neutralized). Installs
tonight (uninstallable): OpenCode 1.18.16 (npm), Ollama 0.32.6 (winget), qwen3.6:27b
(`ollama rm qwen3.6:27b` frees 17 GB), Codex upgrade (npm), skills-ref (pip).
