# docs/CODEX-COMPATIBILITY.md -- OpenAI Codex CLI runbook for Project Osanwe

> **Mission Four artifact (2026-05-15).** Companion to root `AGENTS.md`. Covers installation, model mapping, hook differences, troubleshooting, and verification protocols for running Project Osanwe under OpenAI Codex CLI. Claude Code remains the primary engine; Codex is the parallel engine.

---

## 1. Installation

**REQUIRED VERSION: codex-cli >= 0.130.0** (per docs-review 2026-05-16).

**Why the floor:** Codex 0.118.0 ships an `apply_patch` hook coverage bug ([Issue #16732](https://github.com/openai/codex/issues/16732)) where the PostToolUse hook chain may not fire on `apply_patch` tool calls. Fix shipped in [PR #18391](https://github.com/openai/codex/pull/18391) as part of release v0.130.0. Running Osanwe under 0.118.0 leaves the 10-script PostToolUse chain (wikilink-check, frontmatter-check, orphan-check, skill-precheck, hot-md-check, bump-updated, auto-count-sync, sync-skills, auto-commit) silently inoperative on `apply_patch` operations -- write-time validation gates are bypassed, breaking the 95/100 floor invariant.

Current install on this machine (as of Mission Four; UPGRADE REQUIRED):
- Binary: `~/npm-global/codex`
- Version: `codex-cli 0.118.0` (UNDER FLOOR; upgrade before first Codex session)

For a fresh machine OR upgrade:
```bash
# Check current Codex availability + version
codex --version  # require codex-cli >= 0.130.0

# Install or upgrade
npm install -g @openai/codex-cli@latest   # pulls latest published; verify >= 0.130.0

# OR explicit pin
npm install -g @openai/codex-cli@^0.130.0
```

After install, **verify the apply_patch bug is fixed:**
```bash
codex --version | python -c "
import sys, re
v = re.search(r'(\d+)\.(\d+)\.(\d+)', sys.stdin.read())
maj, mnr, pch = map(int, v.groups())
ok = (maj, mnr, pch) >= (0, 130, 0)
print('OK' if ok else f'UNDER FLOOR: {maj}.{mnr}.{pch} < 0.130.0')
"
```

## 2. Architecture: shared body + dual shell

Project Osanwe runs on shared content with engine-specific configuration:

| Layer | Claude Code | OpenAI Codex |
|---|---|---|
| Instruction file | `CLAUDE.md` (root) | `AGENTS.md` (root; mirror) |
| Local overrides | `CLAUDE.local.md` (gitignored, `@`-imported) | `AGENTS.override.md` (gitignored; REPLACES `AGENTS.md` entirely when present) |
| Skills | `.claude/skills/<name>/SKILL.md` | `.agents/skills/<name>/SKILL.md` (synced from Claude source) |
| Subagents | `.claude/agents/<name>.md` (YAML frontmatter) | `.codex/agents/<name>.toml` (generated) |
| Hooks config | `.claude/settings.json` | `.codex/config.toml` (generated) |
| Codex-specific hooks | -- | `.codex/hooks/stop.sh` (PreCompact workaround) |

**Generators (idempotent; re-run after editing Claude source):**

```bash
# Sync skill bodies (Claude -> Codex), with frontmatter adapter
python tools/sync-skills.py

# Generate subagent TOML files (.claude/agents/*.md -> .codex/agents/*.toml)
python tools/gen-codex-agents.py

# Generate Codex hook config (.claude/settings.json -> .codex/config.toml)
python tools/gen-codex-config.py

# Verify idempotency (exit 1 on divergence)
python tools/sync-skills.py --check
python tools/gen-codex-agents.py --check
python tools/gen-codex-config.py --check
```

**Auto-fire:** `sync-skills.py --hook` is registered in `.claude/settings.json` PostToolUse chain, so editing any `.claude/skills/**/*.md` from a Claude session automatically re-syncs the affected skill to `.agents/skills/`. No manual sync needed during routine skill maintenance.

## 3. Model mapping

**HONEST DEGRADATION:** Codex docs publish no Claude -> Codex model mapping. The following mapping is empirically chosen for Mission Four; refine in Mission Four-bis after Codex-side validation.

| Claude model | Codex model (Mission Four mapping) | Rationale |
|---|---|---|
| opus | gpt-5.5 | Most-capable Codex model; conservative match for institutional-grade agents (thesis-critic, decision-critic, etc.) |
| sonnet | gpt-5.4 | General-purpose Codex model; matches Claude sonnet's mechanical-task profile (vault-classifier-sweep, frontmatter-linter, price-fetcher) |
| haiku | gpt-5.4-mini | (No haiku agents currently; placeholder for future) |

Available Codex models (per `developers.openai.com/codex/cli/features`):
- gpt-5.5 (default, recommended)
- gpt-5.4 (previous standard)
- gpt-5.4-mini
- gpt-5.3-codex (code-specialized; reserved for future Mission tuning)
- gpt-5.3-codex-spark (research preview; ChatGPT Pro tier)
- gpt-5.2 (legacy)

**Tuning per-agent:** edit `.codex/agents/<name>.toml` `model` field directly (will be overwritten on next `gen-codex-agents.py` run; update source `.claude/agents/<name>.md` if persistent override needed).

## 4. Hook chain differences

**Lifecycle event coverage:** Codex supports 5 of Claude's 6 lifecycle events (PreCompact missing) AND adds 1 event Claude lacks (PermissionRequest). Net: Codex has 6 events, Claude has 6 events, with one differing event on each side. The total dual-engine event surface is 7 distinct events; each engine covers 6 of those 7.

| Lifecycle event | Claude | Codex | Notes |
|---|---|---|---|
| SessionStart | YES | YES | Same chain via `.codex/config.toml` |
| PreToolUse | YES | YES | Exit 2 = HALT supported on both |
| PermissionRequest | NO (Claude lacks) | YES (Codex-bonus) | Auto-approve pattern documented in AGENTS.md "Codex-specific notes" section; reference implementation deferred to Mission Four-bis |
| PostToolUse | YES | YES | Exit 2 = HALT supported on both. **Risk:** Codex subagent runs may skip PostToolUse (Codex docs ambiguous). Compensating control: Stop-hook vault audit catches GATE breaches at session end |
| PostToolUseFailure | YES (Claude has, added Feature 4 2026-05-21) | NO (Codex lacks) | **Forensics gap.** Claude side: `.claude/hooks/post-tool-use-failure.py` appends one JSON line per failure to `.claude/state/failures-YYYY-MM-DD.jsonl` (gitignored; privacy-safe -- logs `tool_input_keys` not values). Codex side: no failure-event surface, so failure-pattern analysis requires manual scrape of `.codex/transcripts/`. Cannot block on either side. |
| SubagentStart | YES (Claude has, added Feature 7 2026-05-21) | NO (Codex lacks) | **Telemetry gap.** Claude side: `.claude/hooks/subagent-telemetry.py --event start` appends one JSON line per dispatch to `.claude/state/subagent-telemetry-YYYY-MM-DD.jsonl` (gitignored). Writes `.claude/state/subagent-active-<tool_use_id>.tmp` marker so Stop can compute `duration_seconds`. Each Start also sweeps orphan marker files (>1h old) from prior crashed sessions. Codex side: no subagent-start event surface; equivalent telemetry requires manual scrape of `.codex/transcripts/`. Cannot block (per docs). |
| SubagentStop | YES (Claude has, added Feature 7 2026-05-21) | NO (Codex lacks) | **Telemetry gap.** Claude side: `.claude/hooks/subagent-telemetry.py --event stop` reads the Start marker to compute `duration_seconds`, appends a stop record to the same JSONL log, deletes the marker. SubagentStop CAN block in principle (exit 2 prevents subagent stop) but Osanwe explicitly chooses not to block -- telemetry is advisory. Codex side: no subagent-stop event surface. |
| UserPromptSubmit | YES | YES | Same chain |
| PreCompact | YES (Claude has) | NO (Codex lacks) | **Workaround:** `.codex/hooks/stop.sh` invokes `pre-compact.py` first (archive transcript + hot.md snapshot), then delegates to `stop-pr-and-audit.sh` |
| PostCompact | YES (Claude has, added Feature 3 2026-05-21) | NO (Codex lacks) | **Known continuity gap (no workaround).** Claude side: `.claude/hooks/post-compact-reinject.py` emits `wiki/hot.md` head (8 KiB threshold) to stdout for context re-injection after compaction. Codex side: no compaction event surface, so if Codex compacts mid-session, hot.md context is lost until next SessionStart. SessionStart hot.md load remains symmetric via `tools/session-start.sh`. Revisit if Codex publishes compaction docs. |
| Stop | YES | YES | Routed via `.codex/hooks/stop.sh` to enable PreCompact-equivalent ordering |

**Engine detection in hooks:** `tools/lib/engine-detect.sh` is a shell wrapper that exports `OSANWE_ENGINE=claude|codex` based on env-var fingerprint (CLAUDECODE=1 for Claude; CODEX_* family for Codex; process-ancestry fallback). All Codex hook commands in `.codex/config.toml` are wrapped with this script. Claude-side hooks invoke scripts directly (OSANWE_ENGINE defaults to claude when wrapper absent).

**Defensive payload parsing:** `tools/lib/hook_payload.py` provides `parse_hook_payload(raw_text) -> HookPayload` that tries Claude's `tool_input.file_path` schema first, then falls back to candidate Codex schemas (`name.input.path`, `tool.parameters.path`). Schema misses are logged to `.claude/state/codex-schema-probe-<date>.jsonl` for empirical population from real Codex traffic.

## 5. PreCompact workaround details

Codex lacks a PreCompact lifecycle event. The Claude vault relies on PreCompact to archive transcripts + `wiki/hot.md` snapshots before context compaction.

**Workaround:** `.codex/hooks/stop.sh` is a 2-line orchestrator:
1. `echo $STDIN | python pre-compact.py` -- archive at session end (best-effort; exits 0 always)
2. `echo $STDIN | bash stop-pr-and-audit.sh` -- canonical Stop chain (vault audit + gh PR)

**Timing difference:** Under Claude, PreCompact fires BEFORE compaction (transcript still in window). Under Codex, the equivalent archive fires at Stop (after final tool call, before session terminates). The archived blob is the Stop event payload, not a transcript -- functionally equivalent for continuity reconstruction since `wiki/hot.md` snapshot is captured at the same end-of-session moment.

**To disable:** edit `.codex/config.toml` `[[hooks.Stop]]` `command` to invoke `stop-pr-and-audit.sh` directly (skip the wrapper). Loses archive; gains 100ms latency reduction.

## 6. Tool name verification protocol

`tools/CODEX_TOOLS_UNVERIFIED.md` enumerates 9 tool names appearing in subagent specs. Codex tool registry has not been verified against documentation.

**To verify when a Codex session is available:**
```bash
# In a Codex shell:
codex features list   # may enumerate tool registry
codex exec "list available tools"   # ask the model directly
```

Update `tools/CODEX_TOOLS_UNVERIFIED.md` with VERIFIED status per tool. If any rename is required, add a `TOOL_RENAME_MAP` to `tools/gen-codex-agents.py` and regenerate `.codex/agents/*.toml`.

## 7. Troubleshooting

### Codex doesn't see AGENTS.md
- Verify path: `<VAULT_ROOT>\AGENTS.md` exists at git root.
- Cold-start Codex in `<VAULT_ROOT>` (not a subdirectory).
- Check no `AGENTS.override.md` exists (would REPLACE base file entirely).

### Codex doesn't see skills
- Run `python tools/sync-skills.py --check` -- if exit 1, run `python tools/sync-skills.py` to sync.
- Verify path: `.agents/skills/<name>/SKILL.md` exists.
- Codex skills are discovered on session start; restart Codex if just synced.

### Codex subagent dispatch fails on unknown tool name
- Run `tools/CODEX_TOOLS_UNVERIFIED.md` verification protocol.
- If tool needs rename, add to `gen-codex-agents.py` TOOL_RENAME_MAP and regenerate.

### Hook script errors under Codex
- Check `.claude/state/codex-schema-probe-<date>.jsonl` for unrecognized stdin schemas.
- Run hook script standalone: `echo '<test-json>' | bash tools/lib/engine-detect.sh python tools/wikilink-check.py`
- If `OSANWE_ENGINE` isn't set when invoked directly (without wrapper), the script defaults to claude-schema parsing (safe fallback).

### Windows symlink errors
- Mission Four uses sync-script approach (no symlinks). If you see symlink errors, you may have manually created one -- delete it and re-run `python tools/sync-skills.py`.
- To enable symlinks: Settings > System > For Developers > Developer Mode = On. Then optionally migrate.

### `max_threads` bottleneck on parallel dispatch
- Default is 6 (V2 documented). To raise temporarily for a single session: `codex exec -c agents.max_threads=9 "<prompt>"`
- For persistent override: edit `.codex/config.toml` `[agents] max_threads = N`. The generator will overwrite this; if persistent, also update `tools/gen-codex-config.py` line setting `max_threads = 6`.

### gh pr create silently fails
- Verify gh CLI authenticated: `gh auth status`
- The Codex Stop hook calls `gh pr create` via shell subprocess; Codex's permission model may differ from Claude's. Check `.codex/transcripts/` for stderr output.
- Fallback: manually `git push -u origin HEAD && gh pr create --fill --base main` after Codex session ends.

## 8. Mission Four-bis backlog (deferred items)

Track 2 deliverables deferred to keep Mission Four ABORT-gate buffer:

1. **OSANWE_* OR-clause additions** to 14 hook scripts (CLAUDE_*_BYPASS_* gets parallel OSANWE_*_BYPASS_*). Additive, low-risk; Mission Four ships with CLAUDE_* prefix only.
2. **engine-detect.sh wrapping** in `.claude/settings.json` hook chain (Claude side currently invokes scripts directly; works because OSANWE_ENGINE defaults to claude).
3. **PermissionRequest hook adoption** -- documented in AGENTS.md as a Codex-bonus; full auto-approve pattern adoption pending.
4. **UAP custom adapter** -- UAP skill (no frontmatter, scripts/+agent-definitions/) excluded from `.agents/skills/` mount; needs Codex-side empirical execution test to design proper adapter.
5. **PermissionRequest hook integration** documented but not wired.

## 9. Mission Four artifacts

- AGENTS.md (root): 326 lines
- AGENTS.override.md.template: 50 lines
- .agents/skills/: 16 SKILL.md + 26 ref files
- .codex/agents/*.toml: 14 files (11 gpt-5.5 + 3 gpt-5.4)
- .codex/config.toml: 17 hooks across 5 events
- .codex/hooks/stop.sh: PreCompact workaround
- tools/sync-skills.py + gen-codex-agents.py + gen-codex-config.py: 3 generators
- tools/lib/engine-detect.sh + hook_payload.py: shared dual-engine plumbing
- tools/CODEX_TOOLS_UNVERIFIED.md: 9-tool probe checklist
- 5 hook scripts updated with .agents+.codex EXEMPT_DIRS + AGENTS family EXEMPT_PATHS

Capability baselines at `.claude/state/capability-baseline-{claude,codex}-2026-05-15-{pre,post}.json` (gitignored audit artifacts).
