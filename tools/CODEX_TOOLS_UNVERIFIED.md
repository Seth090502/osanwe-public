# CODEX_TOOLS_UNVERIFIED.md

> **Mission Four artifact (2026-05-15).** Codex CLI tool-name equivalence to Claude's native tool registry has not been verified against documentation. This file enumerates the tool names that appear in `.claude/agents/*.md` frontmatter and tracks empirical Codex-side validation.

## Tool names appearing across the 14 Claude subagents

| Tool | Used by N agents | Codex equivalent (verified?) |
|------|------------------|------------------------------|
| Bash | 4 | UNKNOWN -- assumed identical (Codex has `codex sandbox` for shell exec) |
| WebFetch | 8 | UNKNOWN -- Codex docs do not enumerate tool names; assumed identical |
| WebSearch | 8 | UNKNOWN -- assumed identical |
| Read | 14 | UNKNOWN -- presumed available (universal file-read primitive) |
| Grep | 12 | UNKNOWN -- presumed available |
| Glob | 5 | UNKNOWN -- presumed available |
| Write | 0 (all 5 listing it use disallowedTools) | UNKNOWN |
| Edit | 0 (same as Write) | UNKNOWN |
| NotebookEdit | 0 (same as Write) | UNKNOWN |

## Verification protocol (Phase 0.5/Phase 5 deferred)

When a Codex session is empirically available:

1. Run `codex --help` and `codex features list` to discover tool registry
2. Probe `codex exec "list available tools"` and capture the response
3. For each tool name above, verify Codex-side equivalence (same name, renamed, or unsupported)
4. Update this table with VERIFIED status + any rename map needed
5. If any rename is required, update `tools/gen-codex-agents.py` MODEL_MAP-style translation table

## Honest degradation (Phase 5 capability JSON entry)

Until verification completes:
- `.codex/agents/*.toml` files emit tool names verbatim from Claude source
- Codex sessions may error on unknown tool names; if so, populate the rename map
- The 5 agents declaring `disallowedTools` (thesis-critic, vault-researcher, claim-distributor, decision-critic, pattern-class-scout) had that field DROPPED in the generator (no documented Codex equivalent); their `tools` whitelist remains restrictive enough to provide equivalent constraint via positive enumeration

## File status

This file is read-only at runtime; updated only by manual verification work. No tooling depends on it.
