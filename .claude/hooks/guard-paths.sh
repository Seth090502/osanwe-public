#!/usr/bin/env bash
set -euo pipefail

# Path guard hook: block agent writes to protected vault layers
# Fires on PreToolUse for Write|Edit|MultiEdit
# Exit 2 with stderr message to block the tool call
#
# Protected paths (per vault convention + Okhlopkov reader stance):
#   .raw/          -- immutable raw-notes layer (voice/clips/meetings)
#   private/       -- personal data (profile, holdings, health-baseline, medical-context)
#   finance/       -- reserved path for sensitive financial records
#   credentials/   -- reserved path for secrets/tokens
#
# Atlas/ is soft-guarded by convention (reader/writer stance) -- NOT hook-enforced.

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
file_path=$(echo "$file_path" | sed 's/\/\//g')

# Match protected path segments (leading slash to avoid matching substrings like "myprivate/")
if [[ "$file_path" =~ /\.raw/ ]]; then
    echo "guard-paths: BLOCKED -- .raw/ is immutable (Okhlopkov raw-notes rule). Path: $file_path" >&2
    exit 2
fi

if [[ "$file_path" =~ /private/ ]]; then
    echo "guard-paths: BLOCKED -- private/ contains personal data; agent writes require explicit user confirmation. Path: $file_path" >&2
    exit 2
fi

if [[ "$file_path" =~ /finance/ ]]; then
    echo "guard-paths: BLOCKED -- finance/ is a reserved protected path. Path: $file_path" >&2
    exit 2
fi

if [[ "$file_path" =~ /credentials/ ]]; then
    echo "guard-paths: BLOCKED -- credentials/ contains secrets. Path: $file_path" >&2
    exit 2
fi

exit 0
