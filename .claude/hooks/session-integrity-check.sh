#!/usr/bin/env bash
# session-integrity-check.sh -- tenfold-t1 (2026-07-03)
# X26 settings snapshot-hash + X56 root-contract asserts + X30 dirty-count line.
#
# X77 doctrine: EVERY check here is NON-FATAL. This script never exits nonzero,
# never blocks a session, and is registered as its OWN SessionStart entry after
# session-start.sh so a failure here cannot kill the main context-injection chain
# (the set -e lesson from the commitment organ). Detection, never prevention.

# Default is the live vault; OSANWE_VAULT_ROOT lets the suites exercise this
# hook against a worktree copy without touching the live tree.
VAULT="${OSANWE_VAULT_ROOT:-/path/to/vault}"
STATE="$VAULT/.claude/state"
mkdir -p "$STATE" 2>/dev/null || true

# --- X56: root-contract assertions (AGENTS.md only, 2026-09-24) ---
# AGENTS.md is the contract and the only instruction file; no CLAUDE.md is tracked.
# Claude Code reads AGENTS.md natively only when the project root carries none of
# CLAUDE.md, .claude/CLAUDE.md or CLAUDE.local.md (measured 2026-09-22 on Claude Code
# 2.1.280: AGENTS.md beside a CLAUDE.local.md loaded only the local file), so a
# per-machine CLAUDE.local.md must begin with the line '@AGENTS.md', which imports
# the contract. A session with no contract has no financial boundaries, so each
# failure gets a loud line; every check stays non-fatal per X77: this script
# detects, it never blocks.
#   a. AGENTS.md is missing or opens with the wrong first line. The qwen36 local
#      lane used to swap a model profile over the root contract, and a launcher
#      crash could leave it in place; this still catches that shape.
#   b. CLAUDE.md, .claude/CLAUDE.md or .claude/skills/CLAUDE.md exists: a second
#      set of rules beside the contract -- a restored stub or mirror, a
#      swapped-in profile.
#   c. CLAUDE.local.md exists but its first line is not '@AGENTS.md', so Claude
#      Code loads the local file and not the contract. Only that line is read.
EXPECTED='# Project Osanwe -- universal agent contract'
first_line=$(head -1 "$VAULT/AGENTS.md" 2>/dev/null || echo "")
if [ "$first_line" != "$EXPECTED" ]; then
    echo "INTEGRITY ALERT (X56a): $VAULT/AGENTS.md is missing, or its first line is not the contract title -- this session may be running under a local-model profile left behind by a launcher crash, or with no contract at all. Inspect: git -C $VAULT status AGENTS.md; git -C $VAULT diff AGENTS.md"
fi
# Same path list as tools/router-check.py and tools/precommit.py; a dangling symlink
# counts, a directory named CLAUDE.md does not (it is never loaded).
for extra in CLAUDE.md .claude/CLAUDE.md .claude/skills/CLAUDE.md; do
    if [ -f "$VAULT/$extra" ] || [ -L "$VAULT/$extra" ]; then
        echo "INTEGRITY ALERT (X56b): $VAULT/$extra exists -- a second set of rules beside AGENTS.md, which is the only contract. Remove it; a per-machine CLAUDE.local.md imports the contract instead."
    fi
done
if [ -f "$VAULT/CLAUDE.local.md" ]; then
    local_first=$(head -1 "$VAULT/CLAUDE.local.md" 2>/dev/null | tr -d '\r')
    if [ "$local_first" != "@AGENTS.md" ]; then
        echo "INTEGRITY ALERT (X56c): $VAULT/CLAUDE.local.md does not begin with the line '@AGENTS.md'. A root CLAUDE.local.md stops Claude Code reading AGENTS.md natively, so this session may have no contract. Make '@AGENTS.md' its first line."
    fi
fi

# --- X12/X77: subagent-model env-jail tripwire (SessionStart model-assert) ---
# The 2026-06/07 env-jail (TENFOLD X12): a persistent User-scope
# CLAUDE_CODE_SUBAGENT_MODEL silently outranked every per-call/frontmatter pin and
# jailed ALL vault fleets to one model for weeks. A freshly launched session inherits
# any persistent User-scope value into its process env; this asserts it is clean. Non-fatal.
if [ -n "${CLAUDE_CODE_SUBAGENT_MODEL:-}" ]; then
    echo "INTEGRITY WARN (X12): CLAUDE_CODE_SUBAGENT_MODEL is set to '${CLAUDE_CODE_SUBAGENT_MODEL}' in this session env -- a persistent override jails ALL vault fleets to one model regardless of per-call/frontmatter pins. Unset it at User scope unless deliberately pinning (env-jail governance: docs/osanwe-runtime-reference.md, X12)."
fi

# --- launcher env-jail presence tripwire (same failure class as X12) ---
# tools/claude-shim.ps1 scrubs the ANTHROPIC_*/OPENAI_*/CLAUDE_CODE_* namespaces before
# launching and exports CLAUDE_LANE_JAIL=1 for the child. The shim FAILS OPEN by design
# (a missing launcher must never stop `claude` from starting) and it is installed via a
# sentinel in the OneDrive-synced PS7 profile -- so a sync rollback, a conflict copy, or
# a hand-edit silently returns every session to an unjailed state while every document
# still says the jail exists. That is the X12 shape: invisible for weeks. Non-fatal.
if [ -z "${CLAUDE_LANE_JAIL:-}" ]; then
    echo "INTEGRITY WARN (launcher): CLAUDE_LANE_JAIL is not set -- this session did NOT come through tools/claude-shim.ps1, so the env jail did not run and stale HKCU vars (OPENAI_*, OLLAMA_MODEL) are live in this process. Expected for a session started by other means; investigate if you launched via 'claude' in PS7 (check the sentinel block in the OneDrive PowerShell profile and for a *-<PC>.ps1 conflict copy)."
fi

# --- X26: settings snapshot-hash lines (tamper EVIDENCE, not prevention) ---
# Hashes the two attack-relevant, rarely-legitimately-edited config files (project
# settings.json carries the deny list + hook registry; the global file was the
# empirical rogue-fork write target 2026-07-02). settings.local.json is excluded:
# it accumulates permission approvals by design and would warn-fatigue.
for f in "$VAULT/.claude/settings.json" "/path/to/home/.claude/settings.json"; do
    [ -f "$f" ] || continue
    tag=$(echo "$f" | sed 's|/path/to/home|global|; s|/path/to/vault|project|; s|/|-|g')
    cur=$(sha256sum "$f" 2>/dev/null | awk '{print $1}' || echo "")
    [ -n "$cur" ] || continue
    snap_file="$STATE/settings-hash${tag}.sha256"
    prev=$(cat "$snap_file" 2>/dev/null || echo "")
    if [ -n "$prev" ] && [ "$prev" != "$cur" ]; then
        echo "INTEGRITY WARN (X26): $f hash changed since last session (was ${prev:0:12}.., now ${cur:0:12}..). If no config edit was sanctioned, inspect it before proceeding."
    fi
    echo "$cur" > "$snap_file" 2>/dev/null || true
done

# --- X90: router integrity (canonical AGENTS.md layer) -- 2026-07-10 router pass ---
# tools/router-check.py --quick prints ONE warn line only when the router layer has
# findings (broken pointers, shim drift, adapter drift, size breach, orchestration-
# section defects) and ALWAYS exits 0 (X77 doctrine). Full FAIL mode (exit 1) is the
# manual/pre-commit surface: python tools/router-check.py
python "$VAULT/tools/router-check.py" --quick 2>/dev/null || true

# --- X30: dirty-count line (S4 Integrity scoreboard measure, target <5) ---
dirty=$(cd "$VAULT" 2>/dev/null && git status --porcelain 2>/dev/null | wc -l | tr -d ' ' || echo "?")
echo "[integrity] dirty files at session start: ${dirty:-?} (S4 target <5)"

exit 0
