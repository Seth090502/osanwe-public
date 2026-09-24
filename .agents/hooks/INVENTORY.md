# Tier-3 hook inventory (convenience / Claude-bound) -- D6, 2026-08-10

One row each; honest "Claude-only, no Tier-B equivalent required" where true. Hooks
whose SAFETY PRECONDITIONS do not travel carry `port: DO-NOT` + reason. Tier-1/2
entries live in manifest.yaml; event mapping in README.md.

| Hook | Event | What it does | Port verdict |
|---|---|---|---|
| session-start.sh | SessionStart | Injects hot.md head + MOC listing + git status surface | scriptable; Tier-B runs the BOOTSTRAP command list instead |
| vault-score-check.py | SessionStart | Prints vault health summary + bypass-log count | scriptable; Tier-B runs it manually (BOOTSTRAP lists it) |
| inject-`<private-file>`.py | (deregistered) | RETIRED 2026-08-23 (commit 85950703, "distillate injection retired"); that commit moved the script to `_archive/2026-08-overhaul/hooks/`, and no SessionStart entry for it remains in .claude/settings.json | n/a |
| open-loops.py | SessionStart | Overdue-item digest (6 weighted scanners, top 5) | scriptable (cleanest port); BOOTSTRAP lists it as a session-start command |
| seed-commitment.py | PostToolUse | Auto-seeds escalation dates for new decision records | scriptable; Tier-B loss = manual escalation seeding; acceptable |
| bump-updated.sh | PostToolUse | sed-bumps `updated:` frontmatter on edits | scriptable; loss = stale updated: fields; vault-audit catches |
| auto-commit.sh | PostToolUse | Claude Code copy RETIRED 2026-09-12: a compatibility no-op, no staging or commits. The Codex copy (`.codex/hooks/auto-commit.sh`, registered in `.codex/hooks.json`) was not retired and still stages and commits every edit with `--no-verify` off main and master unless disabled (D31) | No port needed. Claude Code sessions prepare validated milestone commits manually; a Codex session on a branch other than main or master would still auto-commit, if Codex runs the hook (D31). Disposable no-op tests live in tools/test-router-contract.py BranchPolicy |
| reindex-debounce.py | PostToolUse | Touches the vector-index debounce marker | Claude-only wiring; index refresh is manual anyway (idle-gated by design) |
| log-prompt.sh | UserPromptSubmit | Appends prompts to the daily-note Log section | Claude-only, no Tier-B equivalent required (section 9 is hook-owned; Tier-B must NOT hand-write it) |
| semantic-context-inject.py | UserPromptSubmit | Auto-injects vault-search top-K into context | Claude-only; Tier-B calls the vault-search MCP/CLI explicitly |
| post-tool-use-failure.py | PostToolUseFailure | Telemetry sink for tool failures | Claude-only telemetry; /consolidate telemetry mode degrades to zero off-Claude (documented in the skill) |
| subagent-telemetry.py (x2 entries) | SubagentStart/Stop | Subagent telemetry sink | Claude-only (no subagent fleet off-Claude), no equivalent required |
| pre-compact.py | PreCompact | Archives transcript + hot snapshot before compaction | Claude-only (compaction is a Claude mechanism) |
| post-compact-reinject.py | PostCompact | Re-injects Active Context after compaction | Claude-only (same) |
| gen-codex-skill-adapters.py --hook | (deregistered) | RETIRED 2026-08-10 (S2 disarm; redteam F1) -- write modes refuse; deleted at S6 | n/a |
