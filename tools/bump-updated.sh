#!/usr/bin/env bash
set -euo pipefail

# Osanwe vault hook: auto-bump frontmatter 'updated' field
# Fires on PostToolUse for Write|Edit operations
# Only touches .md files in vault content directories

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

# Normalize backslashes to forward slashes
file_path=$(echo "$file_path" | sed 's/\\/\//g')

# Only process markdown files
[[ ! "$file_path" =~ \.(md|MD)$ ]] && exit 0

# Only process vault content directories (ACE canonical -- post-rebuild 2026-04-18 Group 24)
[[ ! "$file_path" =~ /(Atlas|Calendar|Efforts|wiki|private)/ ]] && exit 0

# Skip templates directory (current vault uses _templates/ prefix)
[[ "$file_path" =~ /_templates/ ]] && exit 0

# Skip raw immutable layer (Okhlopkov raw-notes rule)
[[ "$file_path" =~ /\.raw/ ]] && exit 0

# Skip if file doesn't exist
[ ! -f "$file_path" ] && exit 0

# Only bump if file has YAML frontmatter
if head -1 "$file_path" 2>/dev/null | grep -q "^---$"; then
    TODAY=$(date +%Y-%m-%d)
    # Only replace if 'updated:' field exists in frontmatter (within first 20 lines)
    if head -20 "$file_path" | grep -q "^updated:"; then
        sed -i "s/^updated: .*/updated: $TODAY/" "$file_path"
    fi
fi

exit 0
