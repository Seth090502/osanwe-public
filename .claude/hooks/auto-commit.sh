#!/usr/bin/env bash
set -euo pipefail

# Auto-commit hook: stage + commit agent writes on session branch
# Fires on PostToolUse for Write|Edit|MultiEdit
# Refuses to commit on main/master; refuses to commit outside a git repo
# Commit prefix: "agent: <verb> <scope>"
#
# Evgeny hybrid write discipline -- each edit lands its own commit on the session branch.
# Main branch always represents reviewed state; session branch is agent-write trail.
#
# Env-guard (two mechanisms -- either suppresses auto-commit):
#   1. CLAUDE_DISABLE_AUTO_COMMIT=1     -- env var; works if propagated to hook subprocess
#   2. .claude/state/auto-commit-disabled -- flag file; robust across subprocess boundaries
# Used for bulk migrations where per-file auto-commit stream would overwhelm
# the atomic-commit discipline.

[ "${CLAUDE_DISABLE_AUTO_COMMIT:-}" = "1" ] && exit 0

VAULT_ROOT="${VAULT_ROOT:-$(pwd)}"
[ -f "${VAULT_ROOT}/.claude/state/auto-commit-disabled" ] && exit 0

input=$(cat)

# Extract file path from tool_input JSON
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

# Normalize backslashes
file_path=$(echo "$file_path" | sed 's/\/\//g')

# Only process files inside the vault repo
vault_norm=$(echo "$VAULT_ROOT" | sed 's/\/\//g')
case "$file_path" in
    "${vault_norm}/"*) ;;
    *) exit 0 ;;
esac

cd "$VAULT_ROOT" 2>/dev/null || exit 0
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    exit 0
fi

current_branch=$(git symbolic-ref --short HEAD 2>/dev/null || echo "")
# Refuse on main/master (Evgeny rule: never push to main)
if [[ "$current_branch" == "main" ]] || [[ "$current_branch" == "master" ]]; then
    echo "auto-commit: refusing to auto-commit on $current_branch. Switch to a session branch first." >&2
    exit 0
fi

# Skip if no changes to that file
if ! git diff --quiet "$file_path" 2>/dev/null || [ -n "$(git ls-files --others --exclude-standard "$file_path" 2>/dev/null)" ]; then
    # CAT-1 defense-in-depth: refuse to commit files with GATE findings.
    # PreToolUse pre-write-validator.py is the primary block-before-write gate.
    # This is a backstop in case pre-write-validator silently exited or was bypassed.
    rel_path=$(echo "$file_path" | sed "s|^${vault_norm}/||")

    case "$file_path" in
        *.md|*.base)
            # Only audit markdown/base files; other files (json, py, sh) skip
            if [ "${CLAUDE_VAULT_BYPASS_VALIDATOR:-}" != "1" ]; then
                gate_count=$(python "${VAULT_ROOT}/tools/vault-audit.py" --scope "$rel_path" --json 2>/dev/null | python -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('tiers', {}).get('gate', {}).get('count', 0))
except Exception:
    print(0)
" 2>/dev/null || echo "0")
                if [ "${gate_count:-0}" -gt 0 ]; then
                    echo "auto-commit: REFUSED -- $rel_path has $gate_count GATE finding(s); commit blocked." >&2
                    echo "auto-commit: file is on disk but NOT in git. Address findings or set CLAUDE_VAULT_BYPASS_VALIDATOR=1." >&2
                    log_dir="${VAULT_ROOT}/.claude/state"
                    log_file="$log_dir/bypasses-$(date +%Y-%m-%d).log"
                    mkdir -p "$log_dir"
                    echo "$(date -Iseconds) auto-commit BLOCKED $rel_path: $gate_count GATE findings" >> "$log_file"
                    exit 0
                fi
            fi
            ;;
    esac

    # Determine verb based on whether file existed in HEAD
    if git cat-file -e "HEAD:$(git ls-files --full-name "$file_path" 2>/dev/null || echo "$file_path")" 2>/dev/null; then
        verb="update"
    else
        verb="add"
    fi

    git add "$file_path" 2>/dev/null || exit 0
    git commit -m "agent: $verb $rel_path" --no-verify >/dev/null 2>&1 || true
fi

exit 0
