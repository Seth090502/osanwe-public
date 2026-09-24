# UNVERIFIED cells register (design degrades around each; never assumed supported)

Consolidated from all Phase-0 workers, 2026-08-10. An UNVERIFIED cell is treated as UNSUPPORTED in the architecture until empirically resolved; Phase-4 empirical results supersede these entries. Update this file when a cell resolves (state the evidence + date).

## Architecture-relevant (each has a stated degradation in the plan)

| # | Cell | Impact if the optimistic reading is wrong | Degradation in place |
|---|---|---|---|
| U1 | Codex `project_doc_max_bytes` per-file vs combined semantics; truncation warning behavior | Router chain could truncate silently at 32 KiB in unconfigured Codex homes | Root router kept <=20 KB; repo config sets 65536; validate size budgets |
| U2 | Codex `allowed-tools` skill-frontmatter enforcement | Advisory-only = no skill-level tool restriction on Codex | Not relied on; enforcement = enabled_tools + hooks + sandbox |
| U3 | OpenCode duplicate-skill precedence across .agents/.claude trees | Double-listing / ambiguous invocation | OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1 in quickstart; DoD-5a asserts 15 entries |
| U4 | OpenCode bundled ref-file (references/*.md) support | Skills' progressive disclosure fails on OpenCode | Bodies instruct explicit relative-path reads (any harness with a read tool works) |
| U5 | Goose blocking PreToolUse presence in SHIPPED v1.45.0 (sourced from PR #9304) | Goose gate recipes would be aspirational | Goose is adapters-only (no conformance run); recipe cites the PR + marks version-gated |
| U6 | Crush user-defined agent roles | Role-prompt salvage unusable on Crush | Roles target OpenCode + Codex (both verified); Crush recorded as fixed-role |
| U7 | Pi below-cwd AGENTS.md loading | None material (Pi is B-minus, adapters-only) | Documented only |
| U8 | Claude @import aggregate size cap | Shim chain could silently cap | Chain is tiny (996 B + imports); InstructionsLoaded hook can verify empirically |
| U9 | Claude plugin skills-path containment/namespacing for "./.agents/skills/" | Branch P (plugin delivery) unusable | S2 spike decides; Branch G fully specified as default |
| U10 | Cline `.agents/skills/` support (source-only, absent from docs) | Cline silently loses canon skills on a future release | Cline is adapters-only; COMPATIBILITY marks the fragility + cites source line |
| U11 | Cline hooks on Windows (.ps1 in source; 2025 blog said macOS/Linux-only) | Cline gate recipes unusable on Windows | Adapters-only; recipe marked UNVERIFIED-on-Windows |
| U12 | OpenHands CLI-facing sub-agents; user-vs-repo hooks.json precedence | None (disqualified for this machine) | Matrix row only |
| U13 | GLM-4.7-Flash KV size under Ollama (compressed latent vs materialized = ~10x) | Runner-up model may not fit 128K ctx | Top pick qwen3.6:27b has verified fit math from config.json |
| U14 | Ollama RTX 5090 Windows issues (#13338 0-VRAM fallback, #13083 utilization) -- surfaced, not status-checked | Local rung could underperform silently | S5 verifies `ollama ps` shows GPU + set context before the Tier-C run |
| U15 | Effective effort levels per Claude model (per-model matrix unpublished) | None material | Session effort pinned explicitly where it matters |
| U16 | agentskills spec version pinning (no version identifier exists) | Cannot cite "spec vN" in docs | COMPATIBILITY cites retrieval date + skills-ref version instead |
| U17 | Which platforms honor `allowed-tools` (spec names none) | None -- kept out of canon | Re-materialized Claude-side only |
| U18 | npx skills global universal path on Windows (two conflicting source definitions) | None -- tool unused | Documented for operators who later adopt it |
| U19 | Whether junction creation fails on this specific setup (silent copy-fallback would mask) | None -- junctions rejected for in-repo use anyway | Generated-copies strategy |
| U20 | the broker remote MCP surface stability (grew 45 -> 54 tools under a static config) | New mutators appear ungated | Live-surface canary in checkall FAILs on unknown names (D9) |

## Resolution log

- (empty -- append entries as Phase-4 empirical runs resolve cells; format: `U<n> RESOLVED <date>: <evidence>`)
