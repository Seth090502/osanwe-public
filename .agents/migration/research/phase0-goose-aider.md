# Phase 0 research: Goose + Aider rows (worker report, verbatim)

Provenance: opus/max Explore worker, retrieved 2026-08-10. Persisted from session context 2026-08-10. Row IDs: GS-1..GS-10, AI-1..AI-10.

## Goose

*(Block -> Agentic AI Foundation / Linux Foundation; repo migrated block/goose -> aaif-goose/goose, docs -> goose-docs.ai)*

| Cell | Finding | Source | Retrieved |
|---|---|---|---|
| GS-1 AGENTS.md | **Native.** Reads `AGENTS.md` **and** `.goosehints` by default. **Nested: yes** -- hierarchical loading cwd up to git root at session start; nested hint files discovered as goose reads/modifies files there, remain active for the session. Global: `~/.config/goose/.goosehints`. Customizable via `CONTEXT_FILE_NAMES` (JSON array). Requires Developer extension. **Size cap: none documented.** | goose-docs.ai/docs/guides/context-engineering/using-goosehints/ | 2026-08-10 |
| GS-2 Agent Skills | **Native.** Built-in Skills platform extension, enabled by default, auto-discovers at startup. Invocation: auto-match on description; explicit ("Use the code-review skill"); slash `/skills <name>`; `goose skills list` (token counts + source locations). **Auto-activation two-stage**: names+descriptions injected at session start; full SKILL.md loads on match (progressive disclosure). | goose-docs.ai/docs/guides/context-engineering/using-skills/ ; goose-cli-commands | 2026-08-10 |
| GS-3 `.agents/skills/` | **Yes -- auto-discovered, no config.** Scanned: `~/.agents/skills/` (global), `./.agents/skills/` (project, portable), `~/.agents/plugins/<plugin>/` (plugin-provided). Back-compat also scanned: `./.goose/skills/`, `./.claude/skills/`, `~/.claude/skills/`, platform config dirs. `.agents/skills/` is the **recommended standard**. Confirmed in Rust source (crates/goose/src/skills/mod.rs, sources.rs). | using-skills ; GitHub code search ".agents/skills" repo:aaif-goose/goose (12 hits) | 2026-08-10 |
| GS-4 MCP | **MCP is the core extension architecture** -- goose extensions ARE MCP servers. Config: `~/.config/goose/config.yaml`, `extensions:` map (name, cmd, args, enabled, envs, type, timeout). **Transports: stdio, Streamable HTTP, Docker.** CLI: `goose configure`, `goose mcp <name>`, `goose session --with-extension <cmd>`, `--with-streamable-http-extension <URL>`, `--with-builtin <id>`. Built-ins: Developer, Computer Controller, Memory, Tutorial. | using-extensions ; goose-cli-commands | 2026-08-10 |
| GS-5 Hooks | **Yes -- Open Plugins hooks spec.** Events: SessionStart, SessionEnd, Stop, UserPromptSubmit, PreToolUse, PostToolUse, PostToolUseFailure, BeforeReadFile, AfterFileEdit, BeforeShellExecution, AfterShellExecution. Config: `~/.agents/plugins/<name>/hooks/hooks.json` (user) or `<project>/.agents/plugins/<name>/hooks/hooks.json` (project); schema `{"hooks":{"<Event>":[{"matcher":"<regex>","hooks":[{"type":"command","command":"${PLUGIN_ROOT}/..."}]}]}}`. **Blocking pre-tool interception: YES** -- PreToolUse denial (PR #9304): hooks run in order, stop at first explicit deny via **exit code 2** or `{"decision":"block",...}` on stdout; denial returns a tool result flagged error. Separate built-in permission layer: GooseMode + per-tool permissions + Smart Approval. Plugin mgmt: `goose plugin install [--auto-update] <URL>`. **Toolshim:** `GOOSE_TOOLSHIM=true` = tool-call interpretation for models lacking native tool calling; `GOOSE_TOOLSHIM_OLLAMA_MODEL` sets interpreter. | goose-docs.ai/blog/2026/05/14/goose-hooks/ ; open-plugins.com hooks ; PR #9304 ; environment-variables | 2026-08-10 |
| GS-6 Subagents | **Both, experimental.** Subrecipes: recipe YAML `sub_recipes:` array; one tool per subrecipe; isolated session; no nesting; sequential default, parallel supported. Subagents: ad-hoc via `platform__create_task` / `platform__execute_tasks`, separate goose Agent instances, aggregated to parent. Docs: "experimental feature in active development." | recipes/subrecipes ; goose-cli-commands | 2026-08-10 |
| GS-7 Precedence | Context files: **AGENTS.md checked before .goosehints**; local overrides global; root loads first, nested accumulate + persist. Skills: project > personal > extension on collision. `GOOSE_MOIM_MESSAGE_TEXT`/`_FILE` (64 KB cap) inject every turn. Docs conflict on default CONTEXT_FILE_NAMES array order (see UNVERIFIED). | using-goosehints ; using-skills ; environment-variables | 2026-08-10 |
| GS-8 Local models | Ollama via `goose configure` (OLLAMA_HOST) or `GOOSE_PROVIDER=ollama` + `GOOSE_MODEL`. OpenAI-/Anthropic-/Ollama-compatible custom providers; auth optional (vLLM/local). Ramalama, Docker Model Runner, **built-in llama.cpp** in-process provider. Caveat: goose relies heavily on tool calling; models without it = chat only, extensions disabled. | providers ; blog 2026-04-24 | 2026-08-10 |
| GS-9 Windows | **Native Windows supported and recommended** (WSL explicitly "not recommended"). Git Bash (recommended), MSYS2, or PowerShell. CLI installer script (Git Bash/MSYS2) or download_cli.ps1. PATH: `$env:USERPROFILE\.local\bin`. Desktop = portable zip. Build x86_64-pc-windows-msvc; `GOOSE_WINDOWS_VARIANT` standard|cuda. Historical partial-Windows state resolved. | installation ; download_cli.sh | 2026-08-10 |
| GS-10 Liveness | **Very active.** v1.45.0 (2026-07-29); v1.44.0 (07-23), 1.43.0 (07-14), 1.42.0 (07-13), 1.41.0 (07-03) -> multiple releases/week. pushed_at 2026-08-10, 52,614 stars, not archived. AAIF (LF) announced 2025-12-09 with MCP + goose + AGENTS.md as anchors; migration completed 2026-04-07; Block active maintainer. Apache-2.0. | GitHub API ; goose blog ; LF press | 2026-08-10 |

## Aider

*(Aider-AI/aider)*

| Cell | Finding | Source | Retrieved |
|---|---|---|---|
| AI-1 AGENTS.md / CONVENTIONS.md | **AGENTS.md: NOT native, now or ever.** Code search `AGENTS.md repo:Aider-AI/aider` -> total_count: 0 (control `CONVENTIONS.md` -> 4 hits). CONVENTIONS.md is a naming convention, not a hardcoded default -- must be loaded explicitly (`/read-only CONVENTIONS.md`, `aider --read`, `.aider.conf.yml read:`). No auto-discovery, no nesting, no size cap documented. Issue #4363 (asking for a docs recommendation of AGENTS.md) opened 2025-07-19, still open. | code search ; aider.chat conventions/commands docs ; issue #4363 | 2026-08-10 |
| AI-2 Agent Skills | **None.** Code search `SKILL.md` -> 0. No skills concept in docs or release history. | code search ; HISTORY | 2026-08-10 |
| AI-3 `.agents/skills/` | **None documented.** No skill-directory scanning of any kind. | code search ; docs | 2026-08-10 |
| AI-4 MCP | **Never shipped MCP. Not a client, not a server.** Code search `mcp` -> 1 hit, false positive (requirements comment re pywin32). Third-party unofficial wrappers expose Aider AS an MCP server (disler/, sengokudaikon/aider-mcp-server). Claims of recent MCP client support are contradicted by the source tree. | code search + requirements.in ; HISTORY | 2026-08-10 |
| AI-5 Hooks | **None documented.** No hook events, no plugin API, no pre-tool interception. Closest: unofficial Python scripting API (Coder.create/run -- "not officially supported"), subclass a coder, CLI batch via --message/--yes. | scripting.html ; faq ; issue #2900 | 2026-08-10 |
| AI-6 Subagents | **Architect/editor mode only** -- two sequential LLM calls, not spawned subagents. `--architect`, `--editor-model`, `editor-diff`/`editor-whole`. No isolated sessions, no parallelism, no delegation primitives. | modes.html | 2026-08-10 |
| AI-7 Precedence | **No instruction-file hierarchy.** Ordering by context role: /add editable; /read-only reference+cacheable; `.aider.conf.yml read:` auto-load list. Nothing auto-discovered by filename. | conventions ; commands | 2026-08-10 |
| AI-8 Local models | Ollama: `OLLAMA_API_BASE`, model prefix `ollama_chat/` (recommended over `ollama/`); 2k default ctx silently discards overflow -> `OLLAMA_CONTEXT_LENGTH` or per-model num_ctx. OpenAI-compatible: OPENAI_API_BASE + `openai/` prefix. | aider.chat/docs/llms/ollama ; openai-compat | 2026-08-10 |
| AI-9 Windows | Fully native (pure Python 3.9-3.12). `powershell -ExecutionPolicy ByPass -c "irm https://aider.chat/install.ps1 | iex"`; pip/uv/pipx variants. Gotcha: `python -m aider` on command-not-found. | install.html | 2026-08-10 |
| AI-10 Liveness | **STALE, DISQUALIFIED.** Last tagged release v0.86.0 = **2025-08-09, exactly 12 months ago, zero since** (PyPI 0.86.2). Last commit to main 2026-05-22 (~2.5 months); only 10 merged PRs in all of 2026; recent commits are model-list janitorial only. Not archived; 48,087 stars; 1,785 open issues climbing. **Verdict: maintenance-mode/near-dormant; treat as frozen. Do not build adapter work against it.** | GitHub API ; PyPI | 2026-08-10 |

## UNVERIFIED -- Goose

- Default `CONTEXT_FILE_NAMES` array order -- official docs contradict themselves (goosehints guide: ["AGENTS.md",".goosehints"]; env-vars reference: [".goosehints","AGENTS.md"]). Prose precedence consistent; literal order needs the Rust constant.
- AGENTS.md/.goosehints size cap or truncation -- undocumented (only the MOIM 64 KB cap exists, different mechanism).
- Skill precedence for `~/.agents/plugins/` vs back-compat dirs (.claude/.goose placement in the ordering).
- `GOOSE_LEAD_MODEL` / `GOOSE_LEAD_TURNS` -- third-party writeups only; NOT in the official env-vars reference. Do not cite as official.
- Docker as an MCP "transport" (packaging mode vs wire transport ambiguity; SSE unmentioned).
- **PreToolUse blocking semantics sourced from PR #9304, not the hooks guide -- confirm the PR is in v1.45.0 before relying on it.**
- Skills token/size limits undocumented.

## UNVERIFIED -- Aider

- `--conventions-file` flag -- third-party claim, not in official docs. Treat as false unless proven.
- "Recent Aider releases add MCP client support" -- disproved lead (contradicted by code search + HISTORY).
- "Aider reads AGENTS.md natively" (blog roundups) -- contradicted by code search; likely propagated from open issue #4363.
- Full config precedence chain (only `.aider.conf.yml read:` verified).
- Whether a maintained community fork exists.
- Repo-map / context-file size caps.
