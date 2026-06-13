---
categories: [meta]
status: active
created: 2026-05-25
updated: 2026-05-25
tags: [topic/observability, topic/claude-code]
related: []
---

# claudewatch install runbook (morning, ~5 min)

Two commands. Step 1 installs the binary + registers the read-only MCP server
(MCP-ONLY: no global behavioral rules, no blocking hook). Step 2 wires the vault
(docs + test + memory) behind 16 verify gates and commits only on full pass.

Built 2026-05-25 as a deferred-execution pipeline because auto-mode (correctly) will
not download + run a third-party binary unattended. You run the binary step by hand.

Both scripts are idempotent and halt-on-fail. Read them first if you like:
`tools/install-claudewatch.ps1` (PowerShell) and `tools/wire-claudewatch-vault.py` (Python).

## Step 1 -- install the binary + register MCP (you run this)

    powershell -ExecutionPolicy Bypass -File tools/install-claudewatch.ps1

What it does (each step echoes EXPECT vs ACTUAL and halts on first mismatch):
1. `gh release download` v0.15.0 windows_amd64.zip + checksums.txt.
2. SHA256-verify the zip against checksums.txt (HALT on mismatch -- refuses to extract).
3. Extract + place `claudewatch.exe` in `~/.local/bin/` (already on PATH).
4. Smoke `claudewatch --version`.
5. Register the MCP server MCP-ONLY: primary `claudewatch install --mcp-only`; if that
   flag is absent in this build, surgical fallback `claude mcp add -s user claudewatch
   -- <bin> mcp`. Backs up `~/.claude.json` first. GUARDS that zero
   `~/.claude/rules/claudewatch-*.md` were written (MCP-only invariant) -- HALTS if a
   full install leaked global rules.
6. Best-effort (non-fatal): add `<VAULT_ROOT>/` to `~/.config/claudewatch/config.yaml`
   scan paths. Vault sessions are covered via `~/.claude/projects` transcripts
   regardless, so this step only warns if it cannot find the schema.

Expect: a final `=== install-claudewatch.ps1 COMPLETE ===` and exit 0.
Dry-run first if you want to read the logic with no side effects:

    powershell -ExecutionPolicy Bypass -File tools/install-claudewatch.ps1 -DryRun

## Step 2 -- wire the vault + verify + commit (you run this)

    python tools/wire-claudewatch-vault.py

What it does:
- PRE-FLIGHT (no writes): G1 binary present + G6/G15/G16 confirm MCP-only (no global
  rules/hooks). If any fail it writes NOTHING and exits 1 -- it will not document a
  state that is not real.
- WRITE PHASE (D6-D10, transactional): hot.md drift pointer; `tools/test-claudewatch.py`;
  CLAUDE.md `## Observability` section; `/telemetry` SKILL.md see-also + `.agents` mirror;
  `tool_claudewatch.md` memory; demote claudewatch in `cc_community_patterns_2026.md`;
  MEMORY.md index (Tools 23 -> 24 + claudewatch line + cc refresh).
- VERIFY PHASE: 16 named gates (G1-G16) printed PASS/FAIL/SKIP/WARN with rationale.
- COMMIT: only if every BLOCKING gate passed -- F11 atomic commit of the vault files
  (no push). Memory files are out-of-tree (not committed).

Expect: `STATUS: MISSION_COMPLETE` and exit 0.
Dry-run first to see the plan with no writes:

    python tools/wire-claudewatch-vault.py --dry-run

## If a script fails

- It HALTS and tells you which step/gate failed. No partial state: Step 2 rolls back
  every write (vault + memory) on any blocking-gate failure and does not commit.
- Both scripts are idempotent -- fix the root cause and re-run.
- Common cases:
  - Step 1 step 5 HALT "MCP-only invariant BROKEN": a full install wrote global rules.
    Delete `~/.claude/rules/claudewatch-*.md` (and any claudewatch entry from
    `~/.claude/settings.json` hook arrays), then re-run Step 1.
  - Step 2 G3/G4 FAIL (MCP not reachable): the registered MCP subcommand may be wrong.
    Run `claude mcp list` and `claudewatch --help` to find the right `mcp` invocation,
    re-register, re-run Step 2.
  - Step 2 G7 FAIL (vault audit): read the audit findings; the wiring rolled back, so
    the vault is unchanged. Fix and re-run.

## Notes

- claudewatch is MIT/Apache-2.0, local-only, read-only MCP (no network, no API keys).
- The SQLite DB lives out-of-tree at `~/.config/claudewatch/claudewatch.db` -- never
  under <VAULT_ROOT>/, never auto-committed. No built-in retention; prune manually if
  it grows large.
- DEFERRED on purpose (revisit after ~1 week of baseline data): the global behavioral
  rules and the blocking PostToolUse hook. They would collide with the vault's
  11-command PostToolUse chain and override the SessionStart protocol.
- Codex parity: N/A (claudewatch is a Claude-Code-specific binary + MCP client).
