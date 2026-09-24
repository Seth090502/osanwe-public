#!/usr/bin/env bash
set -euo pipefail

# Path guard hook: block agent writes to protected vault layers
# Fires on PreToolUse for Write|Edit|MultiEdit
# Exit 2 with stderr message to block the tool call
#
# Protected paths (per CLAUDE.md + Okhlopkov reader stance):
#   .raw/          — immutable raw-notes layer (voice/clips/meetings)
#   private/       — personal data (never read or written by agents)
#   finance/       — reserved path for sensitive financial records
#   credentials/   — reserved path for secrets/tokens
#
# Atlas/ is soft-guarded by convention (reader/writer stance) — NOT hook-enforced.

input=$(cat)

# Extract file path from tool_input JSON (handles Write/Edit/MultiEdit shapes)
file_path=$(echo "$input" | python -c "
import json, sys
try:
    d = json.load(sys.stdin)
    ti = d.get('tool_input') or {}
    fp = ti.get('file_path')
    if fp is None:
        fp = ti.get('path')
    print(fp if fp is not None else '')
except Exception:
    pass
" 2>/dev/null || true)
[ -z "$file_path" ] && exit 0

# Normalize backslashes to forward slashes (Windows paths)
file_path=$(echo "$file_path" | sed 's/\\/\//g')

# Match protected path segments (leading slash to avoid matching substrings like "myprivate/")
if [[ "$file_path" =~ /\.raw/ ]]; then
    echo "guard-paths: BLOCKED — .raw/ is immutable (Okhlopkov raw-notes rule). Path: $file_path" >&2
    exit 2
fi

if [[ "$file_path" =~ /private/ ]]; then
    echo "guard-paths: BLOCKED — private/ contains personal data; agent writes require explicit user confirmation. Path: $file_path" >&2
    exit 2
fi

if [[ "$file_path" =~ /finance/ ]]; then
    echo "guard-paths: BLOCKED — finance/ is a reserved protected path. Path: $file_path" >&2
    exit 2
fi

if [[ "$file_path" =~ /credentials/ ]]; then
    echo "guard-paths: BLOCKED — credentials/ contains secrets. Path: $file_path" >&2
    exit 2
fi

# --- X26 config/hook/settings write-guard (tenfold-t1, 2026-07-03) ---
# Blocks tool-layer writes to the security-load-bearing config surface unless ARMED.
# Empirical basis: a rogue fork wrote ~/.claude/settings.json unauthorized (2026-07-02).
# Arm deliberately from the main loop:  touch /path/to/vault/.claude/state/config-edit-armed
# The flag is CONSUMED by the first allowed write (one write per arm); every allow is
# logged to .claude/state/bypasses-<date>.log. Known residual: Bash-layer writes bypass
# PreToolUse entirely (X30 class) -- this guard targets the implicit agent-write path.
config_guard=false
case "$file_path" in
    */.claude/hooks/*) config_guard=true ;;
    */.claude/settings.json|*/.claude/settings.local.json) config_guard=true ;;
    */.claude.json) config_guard=true ;;
    # AGENTS.md is the root contract and root CLAUDE.md is its one-line import
    # stub; editing either changes what every session loads, and
    # .claude/skills/CLAUDE.md exists too -- so every one of these names stays guarded.
    */CLAUDE.md|*/CLAUDE.local.md|*/AGENTS.md) config_guard=true ;;
    */tools/session-start.sh|*/tools/vault-score-check.py|*/tools/pre-write-validator.py|*/tools/wikilink-check.py|*/tools/frontmatter-check.py|*/tools/orphan-check.py|*/tools/hot-md-check.py|*/tools/bump-updated.sh) config_guard=true ;;
    # 2026-08-13 (staged via apply-sota-config): the launcher/lane security surface.
    # The env jail and the append-only ledger guard were rewritable by a plain
    # tool-layer Write with no arm and no log line (handoff v2 sec 6.2).
    */tools/claude-shim.ps1|*/tools/claude-launcher.ps1|*/tools/lane-arm.ps1|*/tools/append-only-check.py|*/tools/cc-statusline.sh) config_guard=true ;;
    # 2026-08-17 (operator-approved by name, this exact set): the relay-lane
    # containment stack + two pre-existing gaps. relay_exec/relay_mcp/relay_schema
    # ARE the worker's containment; relay-apply verdicts feed frontier Edits;
    # relay-batch applies overrides + writes the scheduled surface.
    */tools/relay.py|*/tools/lib/relay_exec.py|*/tools/lib/relay_mcp.py|*/tools/lib/relay_schema.py|*/tools/relay-apply.py|*/tools/relay-batch.py|*/tools/delegate.py|*/tools/mode3-normalize-proxy.py) config_guard=true ;;
    # D11 cross-harness extension (2026-08-10, same commit as path creation):
    # the .agents security surface + generated harness configs are config-class.
    */.agents/mcp/*) config_guard=true ;;
    */.agents/scripts/*) config_guard=true ;;
    */.agents/hooks/*) config_guard=true ;;
    */.mcp.json) config_guard=true ;;
    */opencode.json) config_guard=true ;;
    */.codex/config.toml) config_guard=true ;;
esac
if [ "$config_guard" = true ]; then
    ARM_FLAG="/path/to/vault/.claude/state/config-edit-armed"
    guard_log_dir="/path/to/vault/.claude/state"
    if [ -f "$ARM_FLAG" ]; then
        # Redteam M4 (2026-08-10): the arm is PATH-BOUND. The flag file must
        # contain a substring of the target path (typically the basename or the
        # repo-relative path). An empty flag or a mismatch blocks AND consumes
        # the flag -- an injected write can no longer ride a pending arm.
        arm_target=$(head -c 300 "$ARM_FLAG" 2>/dev/null | tr -d '\r\n')
        rm -f "$ARM_FLAG" 2>/dev/null || true
        mkdir -p "$guard_log_dir" 2>/dev/null || true
        if [ -n "$arm_target" ] && [[ "$file_path" == *"$arm_target"* ]]; then
            echo "$(date -Iseconds) guard-paths CONFIG-EDIT allowed (armed for '$arm_target', flag consumed): $file_path" >> "$guard_log_dir/bypasses-$(date +%Y-%m-%d).log" 2>/dev/null || true
        else
            echo "$(date -Iseconds) guard-paths CONFIG-EDIT REFUSED (arm '$arm_target' does not match; flag consumed): $file_path" >> "$guard_log_dir/bypasses-$(date +%Y-%m-%d).log" 2>/dev/null || true
            echo "guard-paths: BLOCKED — arm flag did not name this target (X26/M4 path-bound arming). Arm with: printf '%s' '<target basename>' > /path/to/vault/.claude/state/config-edit-armed  then retry. Path: $file_path" >&2
            exit 2
        fi
    else
        echo "guard-paths: BLOCKED — config/hook/settings surface (X26). Deliberate main-loop edit: printf '%s' '<target basename>' > /path/to/vault/.claude/state/config-edit-armed and retry (one PATH-BOUND write per arm; allows are logged). Path: $file_path" >&2
        exit 2
    fi
fi

exit 0
