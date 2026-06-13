#!/usr/bin/env bash
set -euo pipefail

# Session-branch hook: switch to claude/<YYYYMMDD-HHMM> branch on first meaningful write
# Fires on PreToolUse for Write|Edit|MultiEdit
# No-op if already on a claude/ branch or a rebuild branch (vault-rebuild-*)
# No-op on first fire of a session that starts on main (operator will switch manually)
#
# Evgeny hybrid write discipline -- agent writes land on session branch; main is human-reviewed state.

VAULT_ROOT="${VAULT_ROOT:-$(pwd)}"

# Only runs in repo -- skip otherwise
cd "$VAULT_ROOT" 2>/dev/null || exit 0
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    exit 0
fi

current_branch=$(git symbolic-ref --short HEAD 2>/dev/null || echo "")
[ -z "$current_branch" ] && exit 0

# Skip if already on a claude/ branch or a rebuild branch
if [[ "$current_branch" == claude/* ]] || [[ "$current_branch" == vault-rebuild-* ]]; then
    exit 0
fi

# Refuse to write on main -- abort with guidance
if [[ "$current_branch" == "main" ]] || [[ "$current_branch" == "master" ]]; then
    echo "session-branch: agent write attempted on $current_branch -- refusing." >&2
    echo "session-branch: switch to a claude/<date> branch first via: git switch -c claude/$(date +%Y%m%d-%H%M)" >&2
    exit 2
fi

# Any other branch -- leave alone. Future extension: auto-create claude/<timestamp> if none exists.
exit 0
