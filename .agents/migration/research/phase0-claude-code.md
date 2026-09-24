# Phase 0 research: Claude Code row (worker report, verbatim)

Provenance: opus/max Explore worker, retrieved 2026-08-10; empirical probes run on this machine (Windows 11, Claude Code 2.1.226 installed). Persisted from session context 2026-08-10 (scratchpad task outputs were empty). Row IDs: CC-1..CC-10.

## Claude Code

Harness: Claude Code (Anthropic CLI). Installed on this machine: **2.1.226**. All web sources retrieved **2026-08-10**; all empirical commands run on `<VAULT_ROOT>`, Windows 11.

| # | Cell | Finding | Source URL | Retrieved |
|---|---|---|---|---|
| CC-1 | AGENTS.md support | **NOT read natively.** Docs state verbatim: "Claude Code reads `CLAUDE.md`, not `AGENTS.md`." No nested-AGENTS.md discovery either (nesting applies only to `CLAUDE.md`/`CLAUDE.local.md`). Sanctioned workarounds: (a) `@AGENTS.md` import inside CLAUDE.md; (b) `ln -s AGENTS.md CLAUDE.md` -- docs explicitly say **on Windows use the `@AGENTS.md` import instead** (symlink needs Admin/Developer Mode). One-time copy paths only: `/init` with `CLAUDE_CODE_NEW_INIT=1` reads AGENTS.md; `claude import`/`/import` (requires **v2.1.213+**) appends a one-time copy of AGENTS.md into the matching CLAUDE.md. **Size cap on CLAUDE.md: none** -- "CLAUDE.md files are loaded in full regardless of length"; the 200-line figure is guidance, and the 200-line/25KB hard limit applies to auto-memory `MEMORY.md` only. **Import limits: max depth of four hops**, relative-to-importing-file resolution, code spans/fences skipped; external (outside-cwd) imports trigger a one-time approval dialog. No documented byte or count cap on imports. | https://code.claude.com/docs/en/memory | 2026-08-10 |
| CC-2 | Agent Skills | Scanned locations: enterprise/managed, `~/.claude/skills/<name>/SKILL.md`, `.claude/skills/<name>/SKILL.md` (walked up from cwd to repo root), plugin `<plugin>/skills/<name>/SKILL.md`, legacy `.claude/commands/*.md`, **nested** `.claude/skills/` below cwd (lazy -- load only after Claude reads/edits a file in that subdir), and `.claude/skills/` inside any `--add-dir`/`/add-dir` directory. Name precedence: enterprise > personal > project > bundled; plugin skills namespaced. Symlinked skill dirs are followed and de-duplicated. Invocation: `/skill-name`; nested collision -> `/apps/web:deploy`; plugin -> `/plugin:skill`. Auto-activation = model matching on `description` + `when_to_use`, **combined text truncated at 1,536 chars** in the listing (`skillListingMaxDescChars`), listing budget via `skillListingBudgetFraction` / `SLASH_COMMAND_TOOL_CHAR_BUDGET`; `paths:` globs gate auto-load; `disable-model-invocation: true` makes it manual-only. **No setting adds extra skill directories** -- `--add-dir` is the only mechanism, and docs state `permissions.additionalDirectories` in settings.json "grants file access only and does not load skills." Related settings: `skillOverrides`, `disableBundledSkills`, `disableSkillShellExecution`. Live change detection re-scans without restart; `/reload-skills`. | https://code.claude.com/docs/en/skills | 2026-08-10 |
| CC-3 | `.agents/skills/` auto-discovery | **NO -- GO/NO-GO = NO-GO.** Zero support. Triple-confirmed: (a) `grep -c ".agents/"` over the full upstream `CHANGELOG.md` -> **0 hits** (also 0 for `AGENTS.md`); (b) `.agents` / `AGENTS.md` -> **0 hits** across `skills.md`, `sub-agents.md`, `settings.md`, `cli-reference.md`, `plugins-reference.md`, `features-overview.md`; (c) **empirical** -- `grep -a -o -F ".agents/" claude.exe` on the installed 2.1.226 binary -> **0 occurrences**, against a control of **92** occurrences of `.claude/skills`. Nothing shipped Jul-Aug 2026 changes this. | https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md ; https://code.claude.com/docs/en/skills ; empirical binary probe | 2026-08-10 |
| CC-4 | MCP | Config locations: project `.mcp.json` (repo root, committed, requires per-project approval); user/local scope in `~/.claude.json`; session-only via `--mcp-config <files|json>` (+ `--strict-mcp-config`); plugin-provided `.mcp.json` at plugin root or inline in `plugin.json`. Scope flag `-s/--scope` = `local` | `project` | `user`. Transports: **stdio** (default when entry has no `type`), **http** (`type` accepts `streamable-http` as alias), **sse** (documented as **deprecated**, use HTTP), **ws** (WebSocket -- config-only; `--transport` does not accept `ws`). Entry with `url` but no `type` is a hard config error. Per-server fields: `command`/`args`/`env` (stdio); `url`/`headers`/`headersHelper`/`timeout`/`alwaysLoad` (http/sse/ws). CLI: `claude mcp add | add-json | add-from-claude-desktop | get | list | login | logout | remove | reset-project-choices | serve`; flags `--transport/-t`, `--header/-H`, `--env/-e`, `--scope/-s`, `--` separator for stdio argv. | https://code.claude.com/docs/en/mcp ; empirical `claude mcp --help` | 2026-08-10 |
| CC-5 | Hooks | The 9-event prior list is stale; the **current list is far larger (~30 events)**: `SessionStart`, `Setup`, `SessionEnd`, `UserPromptSubmit`, `UserPromptExpansion`, `Stop`, `StopFailure`, `PreToolUse`, `PermissionRequest`, `PermissionDenied`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `TeammateIdle`, `InstructionsLoaded`, `ConfigChange`, `CwdChanged`, `DirectoryAdded`, `FileChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`, `Elicitation`, `ElicitationResult`, `Notification`, `MessageDisplay`. **PreToolUse CAN block**, two contracts: exit **2** -> tool call blocked, stdout ignored, **stderr text used as the blocking reason**; or exit **0** + stdout JSON `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"|"deny"|"ask"|"defer","permissionDecisionReason":"..."}}` (plus `updatedInput`, `additionalContext`). Any other exit code = non-blocking, action proceeds. Config: `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`, managed policy, plugin `hooks/hooks.json`, and skill/agent frontmatter `hooks:` -- entries **merge** across levels. **Windows: `shell: powershell` is NOT required.** The `shell` field is optional and accepts `"bash"` | `"powershell"`; on Windows the default is **bash (Git Bash) if installed, otherwise powershell**. Exec form (with `args`) bypasses the shell and won't resolve `.cmd`/`.bat` shims. `${CLAUDE_PROJECT_DIR}` / `${CLAUDE_PLUGIN_ROOT}` behave identically on Windows. Hooks run with no controlling terminal. | https://code.claude.com/docs/en/hooks | 2026-08-10 |
| CC-6 | Subagents | `.claude/agents/*.md` frontmatter: `name` (req; no `:`), `description` (req), `tools`, `disallowedTools`, `model`, `permissionMode`, `skills`, `memory`, `effort`, `background`, `isolation`, `color`, `hooks`, `maxTurns`, `initialPrompt`, `mcpServers` (`prompt` in `--agents` JSON). **`model` accepts `sonnet` | `opus` | `haiku` | `fable` | full model ID (e.g. `claude-opus-5`) | `inherit`; defaults to `inherit`** -- all four aliases including `fable` confirmed. **`effort`: `low` | `medium` | `high` | `xhigh` | `max`** (availability model-dependent). `skills:` preloads **full skill content** (not just description) at subagent startup. **Per-invocation model override: YES** -- resolution order is `CLAUDE_CODE_SUBAGENT_MODEL` env -> per-invocation `model` parameter -> frontmatter `model` -> main conversation model; the per-invocation value persists across resume (v2.1.211+). **Spawn depth limit: 3 layers below main by default**, tunable via `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` (was 5 in v2.1.172-216; 1 in v2.1.217-218; raised to 3 in v2.1.219). **Concurrency limit: 20 running**, error `Concurrent subagent limit reached`, tunable via `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` (v2.1.217+); ultracode sessions exempt. **Background is the default** as of v2.1.198; background subagents get a reduced built-in tool set. Scan order: managed > `--agents` > `.claude/agents/` (walked up, nearest wins) > `~/.claude/agents/` > plugin `agents/`; recursive subfolders; `--add-dir` `.claude/agents/` also scanned. | https://code.claude.com/docs/en/sub-agents | 2026-08-10 |
| CC-7 | Instruction-file precedence | **Settings precedence (highest->lowest): managed/policy -> CLI args -> `.claude/settings.local.json` -> `.claude/settings.json` -> `~/.claude/settings.json`.** Managed paths: `/Library/Application Support/ClaudeCode/managed-settings.json` (macOS), `/etc/claude-code/managed-settings.json` (Linux/WSL), `<PROGRAM_FILES>\ClaudeCode\managed-settings.json` (Windows), plus MDM/`HKLM\SOFTWARE\Policies\ClaudeCode` and a `managed-settings.d/` drop-in dir. Permission rules **merge** rather than override. **CLAUDE.md is different -- files are concatenated, not overridden.** Load order broad->specific: managed policy CLAUDE.md -> `~/.claude/CLAUDE.md` -> `./CLAUDE.md` or `./.claude/CLAUDE.md` -> `./CLAUDE.local.md`. Across the tree, filesystem-root->cwd; **within each directory `CLAUDE.local.md` is appended after `CLAUDE.md`**. Nested CLAUDE.md below cwd load **lazily** when Claude reads a file there, and are **not re-injected after `/compact`** (project-root CLAUDE.md is). `~/.claude/rules/` loads before `.claude/rules/`; unconditional rules rank with `.claude/CLAUDE.md`. `claudeMdExcludes` skips files by glob at any layer -- **except managed policy CLAUDE.md, which cannot be excluded.** | https://code.claude.com/docs/en/memory ; https://code.claude.com/docs/en/settings | 2026-08-10 |
| CC-8 | Local-model support | **No.** Official docs document only Claude models across six deployment surfaces. Redirection is supported **only as a gateway/proxy in front of those providers**: `ANTHROPIC_BASE_URL`, `ANTHROPIC_BEDROCK_BASE_URL`, `ANTHROPIC_AWS_BASE_URL`, `ANTHROPIC_VERTEX_BASE_URL`, `ANTHROPIC_FOUNDRY_BASE_URL`, with `CLAUDE_CODE_USE_{BEDROCK,VERTEX,FOUNDRY}` and `CLAUDE_CODE_SKIP_{BEDROCK,VERTEX}_AUTH`; corporate proxy via `HTTPS_PROXY`/`HTTP_PROXY`. Model pinning via `ANTHROPIC_DEFAULT_{FABLE,OPUS,SONNET,HAIKU}_MODEL`. **Ollama, llama.cpp, open-weight, or any non-Anthropic model: zero mentions in official docs.** An Anthropic-API-compatible shim behind `ANTHROPIC_BASE_URL` is a community pattern, not an official capability. | https://code.claude.com/docs/en/third-party-integrations ; https://code.claude.com/docs/en/llm-gateway | 2026-08-10 |
| CC-9 | Windows install | Native (recommended) -- PowerShell: `irm https://claude.ai/install.ps1 | iex` ; CMD: `curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd`. WinGet: `winget install Anthropic.ClaudeCode` (no auto-update). npm: `npm install -g @anthropic-ai/claude-code` (Node 22+ as of v2.1.198; ships the same native binary). Pinned/stable variants documented. Requirements: Windows 10 1809+ / Server 2019+, 4 GB+ RAM, x64/ARM64. No Administrator required. Git for Windows optional -- with it, the Bash tool uses Git Bash; without it, PowerShell tool. Native installs auto-update in the background. | https://code.claude.com/docs/en/setup | 2026-08-10 |
| CC-10 | Liveness | **Latest = 2.1.226**, published **2026-08-08T01:53:22Z** (npm registry). `stable` dist-tag = 2.1.220 (2026-07-24); `next` = 2.1.226. Release cadence ~daily. Upstream CHANGELOG carries no dates; dates from npm registry. Actively maintained. | https://registry.npmjs.org/@anthropic-ai/claude-code ; https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md | 2026-08-10 |

## Extra verifications

### Empirical: `claude --version` (outranks docs)

```
2.1.226 (Claude Code)
```
Binary: `<HOME>\.local\bin\claude.exe` (287,053,472 bytes, mtime 2026-08-09 23:26). Version dirs under `%USERPROFILE%\.local\share\claude\versions\`: 2.1.223, 2.1.224, 2.1.226 -- native install auto-updated onto `latest`, 6 releases ahead of `stable`. Installed == npm `latest`; no doc/empirical divergence on any cell.

### Empirical: `claude --help` -- flags relevant to skills dirs / AGENTS.md / instruction files

**No flag anywhere in `--help` references AGENTS.md, a skills directory, or an instruction-file path.** Relevant set:
- `--add-dir <directories...>` -- the **only** way to add a skill-discovery root (docs confirm `.claude/skills/` inside an added dir is loaded as an explicit exception to the access-only rule).
- `--setting-sources <sources>` -- comma-separated `user,project,local`.
- `--settings <file-or-json>`, `--agents <json>`, `--agent <agent>`, `--plugin-dir <path>`, `--plugin-url <url>`, `--mcp-config`, `--strict-mcp-config`.
- `--system-prompt`, `--append-system-prompt`.
- `--bare` -- skips hooks, LSP, plugin sync, attribution, auto-memory, background prefetches, keychain reads, **and CLAUDE.md auto-discovery**; skills still resolve via `/skill-name`.
- `--safe-mode` -- disables CLAUDE.md, skills, plugins, hooks, MCP servers, custom commands/agents; managed policy still applies.
- `--disable-slash-commands` -- "Disable all skills."
- `--model` help text confirms alias set: fable / opus / sonnet or full name.
- `--effort <level>` -- low, medium, high, xhigh, max.
- Subcommands: agents, auth, auto-mode, doctor, gateway, import, install, mcp, plugin, project, setup-token, ultrareview, update.

### Empirical: binary string probe (2.1.226, 287 MB)

| String | Occurrences | Reading |
|---|---|---|
| `.agents/skills` | **0** | No `.agents/skills` code path exists |
| `.agents/` | **0** | No `.agents/` discovery of any kind |
| `.claude/skills` | 92 | Control -- probe method sound |
| `CLAUDE.local.md` | 34 | Control |
| `AGENTS.md` | 11 | All in copy/scan paths (claude import codex; /init scan list), never memory loading |
| `skillDirectories` / `additionalSkillDirectories` / `extraSkillDirs` / `skillPaths` | 0 each | No hidden settings key for extra skill dirs |

Context on the 11 `AGENTS.md` hits: `claude import codex` copies AGENTS.md -> CLAUDE.md (project + user scopes); an unsupported-setting notice ("Claude Code hardcodes CLAUDE.md / AGENTS.md discovery"); the `/init` codebase-scan prompt list. `claude import --help`: source = codex | gemini; --dry-run, --yes.

### Empirical: hook event names present in the 2.1.226 binary

All quoted-literal counts non-zero: PreToolUse 31, PostToolUse 42, UserPromptSubmit 20, SessionStart 26, SessionEnd 7, Stop 52, SubagentStop 29, PreCompact 6, Notification 8, InstructionsLoaded 6, PostCompact 6, SubagentStart 13, PermissionRequest 21, TeammateIdle 10, Setup 19. **Migration note:** plan for ~30 events; `InstructionsLoaded` is the purpose-built hook for logging which instruction files loaded (useful for validating any AGENTS.md shim).

### Empirical: this machine's own migration state

- `<VAULT_ROOT>\CLAUDE.md` line 1 is literally `@AGENTS.md` -- the documented Windows-safe workaround, already in place. `<private-file>.md` import follows.
- `<VAULT_ROOT>\.agents\skills\` exists, 15 skill dirs, each a single SKILL.md (Codex pointer-adapters from `tools/gen-codex-skill-adapters.py`).
- `<VAULT_ROOT>\.claude\skills\` holds the same 15 names as real directories, not symlinks, plus `_archive/`.
- Skills active in this session load from `.claude/skills/`, NOT `.agents/skills/`. The two trees are an independent mirror pair. No settings key will make Claude Code read `.agents/skills/` directly; supported options are symlinked skill dirs (needs elevation on Windows; junctions practical) or continued generation.
- Other `.agents` dirs: `<other-tool>/.agents`, `_archive/codex-mirror-2026-07-04/.agents`.
- No `.mcp.json` at `<VAULT_ROOT>` -- MCP servers are user/local scope in `~/.claude.json`.

### Cross-harness notes

- Claude Code accepts ~20 skill frontmatter fields, but only six are agentskills.io spec -- `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. Non-spec fields (e.g. `argument-hint`) hard-error on claude.ai upload / Skills API / package_skill.py, not silent-ignore. Restrict traveling skills to the six.
- Skills do not travel to Cowork/cloud/routines from `~/.claude/skills/` -- those load claude.ai-account skills plus repo-committed `.claude/skills/`.
- `claude gateway` subcommand exists (enterprise auth/telemetry gateway).

## UNVERIFIED cells

1. Official release DATE for 2.1.226 from an Anthropic-owned source (npm timestamp only; CHANGELOG undated).
2. Aggregate size/count cap on `@` imports (only depth <=4 documented).
3. Effective `effort` values per model (per-model matrix unpublished).
4. The 14 `skillsDir` binary hits -- internal identifier, no settings schema exposes it; not usable as a supported mechanism.
5. Behavior of an Anthropic-API-compatible local shim behind `ANTHROPIC_BASE_URL` (undocumented, untested here).
6. AGENTS.md support in non-CLI surfaces (Desktop, Cowork, cloud, SDK).
