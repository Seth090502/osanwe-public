#!/usr/bin/env bash
set -euo pipefail

# PreToolUse Write|Edit|MultiEdit: ordinary work on main and named feature
# branches is allowed. The former mandatory session-branch rule was retired
# 2026-09-12. Refuse detached writes without creating or switching branches.

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd -- "$script_dir/../.."
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    exit 0
fi

if ! git symbolic-ref --quiet --short HEAD >/dev/null 2>&1; then
    echo "session-branch: detached or unreadable HEAD -- refusing file write." >&2
    echo "session-branch: preserve this commit on a named branch with git switch -c codex/describe-work, or deliberately return to an existing branch with git switch main." >&2
    exit 2
fi

exit 0
