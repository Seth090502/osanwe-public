# Phase 0 research: OpenCode row (worker report, verbatim)

Provenance: opus/max Explore worker, retrieved 2026-08-10. Persisted from session context 2026-08-10. Row IDs: OC-1..OC-10.

**Identity note (affects every source URL):** the repo was renamed `sst/opencode` -> **`anomalyco/opencode`** (company rebrand to "Anomaly", announced by Dax Raad ~2026-01-02). Old sst/opencode URLs redirect. Docs remain at opencode.ai.

| # | Cell | Finding | Source | Retrieved |
|---|---|---|---|---|
| OC-1 | AGENTS.md | **Native.** Lookup order: (1) local `AGENTS.md` / `CLAUDE.md` / `CONTEXT.md` (deprecated) found by findUp from cwd -> worktree root; (2) global `~/.config/opencode/AGENTS.md`; (3) `~/.claude/CLAUDE.md`. "The first matching file wins in each category" -- source comment: "The first project-level match wins so we don't stack AGENTS.md/CLAUDE.md from every ancestor." **Nested = yes, but lazily:** resolve() walks up from a file being read and attaches nearby instruction files, deduped once per message. **CLAUDE.md fallback = yes.** Disable via env: `OPENCODE_DISABLE_CLAUDE_CODE=1`, `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1`, `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1`. **Size cap: none found** in docs or instruction.ts. | opencode.ai/docs/rules/ ; packages/opencode/src/session/instruction.ts | 2026-08-10 |
| OC-2 | Agent Skills | **Native**, first-class `skill` tool. Frontmatter: `name` (req, 1-64 ch, `^[a-z0-9]+(-[a-z0-9]+)*$`), `description` (req, 1-1024 ch), `license`, `compatibility`, `metadata`. Invocation: `skill({ name: "git-release" })`. **Auto-activation = metadata-only, model-decided**: names+descriptions injected in `<available_skills>` XML; model chooses to call the tool. Extra roots via config `skills.paths` (array) and `skills.urls`. | opencode.ai/docs/skills/ ; packages/web/src/content/docs/skills.mdx | 2026-08-10 |
| OC-3 | `.agents/skills/` auto-discovery | **YES -- confirmed in repo doc source, verbatim:** "Project agent-compatible: `.agents/skills/<name>/SKILL.md`" and "Global agent-compatible: `~/.agents/skills/<name>/SKILL.md`". Full scan set: `.opencode/skill(s)/`, `.claude/skills/`, `.agents/skills/` (project, walked up to git worktree root) + `~/.config/opencode/skill(s)/`, `~/.claude/skills/`, `~/.agents/skills/` (global). Singular and plural both accepted. | skills.mdx ; packages/core/src/plugin/skill/customize-opencode.md | 2026-08-10 |
| OC-4 | MCP | Config: `opencode.json` / `opencode.jsonc` (project) or `~/.config/opencode/opencode.json` (global), key `"mcp"`. **Local stdio:** `{"type":"local","command":["npx","-y","pkg"],"cwd","environment","timeout"}`. **Remote:** `{"type":"remote","url","headers","oauth":{}|false,"timeout"}`. **Per-server enable/disable:** `"enabled": true|false`. Tool-level gating via `"tools": {"mcp-name": false, "pattern*": false}` with glob `*`/`?`, overridable per-agent under `agent.<name>.tools`. | opencode.ai/docs/mcp-servers/ | 2026-08-10 |
| OC-5 | Hooks / plugin API | **Exact Hooks interface (packages/plugin/src/index.ts):** dispose, event, config, tool (custom ToolDefinitions), auth, provider, chat.message, chat.params, chat.headers, **permission.ask** (mutate `output.status = "ask"|"deny"|"allow"`), command.execute.before, **tool.execute.before** (input {tool,sessionID,callID}, output {args}), tool.execute.after. **VETO: two mechanisms** -- (a) `throw new Error()` inside tool.execute.before blocks execution (docs' .env protection example); (b) permission.ask forces deny programmatically. tool.execute.before receives MUTABLE output.args -> argument rewriting possible. PluginInput: {client, project, directory, worktree, serverUrl, $ (Bun shell)}. Locations: `.opencode/plugin/` or `plugins/`; global `~/.config/opencode/plugins/`; npm plugins auto-installed via Bun. Read-only event bus incl. session.*, message.*, file.edited, permission.asked/replied, tui.*. Custom commands: `.opencode/command(s)/<name>.md` (frontmatter description/agent/model/subtask; $ARGUMENTS, shell injection, @file refs). Rules files: `"instructions": [...]` globs + remote URLs. | packages/plugin/src/index.ts ; opencode.ai/docs/plugins/ ; /commands/ ; /rules/ | 2026-08-10 |
| OC-6 | Subagents / agent roles | **Two modes: primary** (Tab-cycled: Build = all tools; Plan = edit/bash default ask) **and subagent** (built-ins: General, Explore read-only, Scout read-only). **Files:** `.opencode/agent(s)/<name>.md`; global `~/.config/opencode/agent(s)/`. Filename = agent id. **Frontmatter:** description, mode, model, temperature, top_p, prompt, tools, permission, disable, color. JSON equivalent under `agent.<name>`. **Invocation:** Tab / @-mention (`@general help me search`) / spawned by the **task tool**. **Nesting cap:** `subagent_depth` (default 1). Port note: role-prompt subagents map cleanly (prompt + tools + permission per file). | opencode.ai/docs/agents/ ; /config/ ; task.ts | 2026-08-10 |
| OC-7 | Instruction/config precedence | Configs **merge, not replace**; later overrides earlier. Order (low->high): remote .well-known/opencode; global opencode.json; OPENCODE_CONFIG env path; project opencode.json; .opencode/ dirs; OPENCODE_CONFIG_CONTENT inline; managed files; macOS MDM. **AGENTS.md is a separate axis**: first-match-wins per category; `"instructions"` files are combined with AGENTS.md, not overriding. | opencode.ai/docs/config/ ; /rules/ | 2026-08-10 |
| OC-8 | Local models | **75+ providers** via Vercel AI SDK + models.dev registry. Local/OpenAI-compatible: `provider.<id>.npm = "@ai-sdk/openai-compatible"` + `options.baseURL` + explicit models map. Ollama `http://localhost:11434/v1`; LM Studio :1234; llama.cpp :8080. `/v1/responses` endpoints -> use @ai-sdk/openai. blacklist/whitelist model filters; disabled_providers/enabled_providers. | opencode.ai/docs/providers/ | 2026-08-10 |
| OC-9 | Windows install | Package **`opencode-ai`**. `npm install -g opencode-ai` (also bun/pnpm/yarn). Windows-specific: `choco install opencode`, `scoop install opencode`, mise, Docker, GH binaries. **No winget documented.** **Known Windows issues:** docs recommend **WSL** "for the best experience on Windows"; native-Windows sluggishness, file-access and terminal problems cited; Desktop needs WebView2. Windows paths: `%USERPROFILE%\.config\opencode\opencode.jsonc`, `.local\share\opencode`, `.cache\opencode`. | opencode.ai/docs/ ; /troubleshooting/ | 2026-08-10 |
| OC-10 | Liveness | **v1.18.15, published 2026-08-07.** Last push 2026-08-10T03:37Z. ~195,500 stars, 25,066 forks, 4,997 open issues, MIT, not archived. ~10 releases in 11 days. Maintainer state healthy; org moved sst -> anomalyco (Anomaly); Dax Raad core. | gh api repos/anomalyco/opencode ; releases ; x.com/thdxr | 2026-08-10 |

## Extras

**(a) Frontier auth + Anthropic OAuth status**

- Auth: `/connect` (API key paste or browser OAuth); env vars; provider settings.apiKey; baseURL proxies.
- **Anthropic Pro/Max OAuth: BLOCKED / removed. Do not plan on it.** OpenCode docs verbatim: "There are plugins that allow you to use your Claude Pro/Max models with OpenCode. Anthropic explicitly prohibits this. Previous versions of OpenCode came bundled with these plugins but that is no longer the case as of 1.3.0". Anthropic-side: subscriptions are for native Anthropic apps + Claude Code; third-party access = API key via Console or supported cloud. Ban risk real: issue #6930 "Using opencode with Anthropic OAuth violates ToS & Results in Ban" (2026-01-05, closed) reports an account ban. **-> Use an Anthropic API key (or Bedrock/Vertex) in OpenCode.**
- Subscriptions that DO work zero-setup: **ChatGPT Plus, GitHub Copilot, GitLab Duo** (browser OAuth).
- First-party gateway: **OpenCode Zen** (pay-as-you-go; Claude/GPT/Gemini/open models; auto-reload $20 when balance <$5). Also OpenCode Go subscription.

**(b) Permission system -- least-privilege: STRONG**

- `"permission"` in opencode.json; wildcard `"*"` default + per-tool overrides; values **allow / ask / deny**.
- Gatable tools: read, edit (incl. write/patch), glob, grep, bash, task (subagent launch), skill, lsp, question, webfetch, websearch, external_directory, doom_loop.
- Per-agent overrides ("agent rules take precedence").
- Bash pattern matching against parsed command with globs: `"git *": "allow"`, `"git commit *": "deny"`; same for skill/read/grep.
- **Defaults permissive** -- most tools allow; doom_loop + external_directory ask; read blocks .env by default. Conformance runs must set explicit `"*": "ask"`/deny baseline.
- permission.ask plugin hook = policy-as-code above static config.

## UNVERIFIED

- AGENTS.md size cap (no documented limit; downstream context-assembly truncation not audited).
- winget support (absence of documentation).
- Nested AGENTS.md exact trigger set (read only? edit/glob too?).
- Anthropic enforcement TIMELINE dates (secondary press) -- primary-confirmed: docs' prohibition + removal as of 1.3.0, support-article API-key requirement, issue #6930.
- Consumer-terms revision text (retrieved version predates the reported change).
- `/connect` menu prose internally inconsistent post-removal (live menu not exercised -- read-only audit).
- Skill bundled/nested resource files (references/*.md under a skill dir) -- support unconfirmed.
- SST/Anomaly team commitments (no primary statement retrieved).
- `.agents/skills/` vs `.claude/skills/` precedence when the same name exists in both -- ordering not documented.
