#!/usr/bin/env bash
set -euo pipefail

# Log-prompt hook: append every UserPromptSubmit to today's daily note ## Log section
# Fires on UserPromptSubmit
# Format: "- <ISO8601> :: <prompt>"  (Donbavand audit pattern)
#
# Creates daily note with canonical 9-section template if missing
# (mirrors session-start.sh template to keep schema consistent).

input=$(cat)

# Extract prompt text from JSON (field name may be 'prompt' or 'message' depending on event schema)
prompt=$(echo "$input" | python -c "
import json, sys
try:
    d = json.load(sys.stdin)
    v = d.get('prompt')
    if v is None:
        v = d.get('message')
    if v is None:
        v = d.get('user_prompt')
    print(v if v is not None else '')
except Exception:
    pass
" 2>/dev/null || true)
[ -z "$prompt" ] && exit 0

# Collapse CR + newlines to spaces for a single-line log entry.
# vault-hygiene 2026-05-29 Fix-A: bare CR (\r) bytes were left intact by `tr '\n'`, and
# vault-audit extract_wikilinks uses str.splitlines() which splits on \r too -- fracturing
# the backtick-wrapped entry so an interior [[wikilink]] escaped the inline-code strip and
# registered as a broken wikilink (GATE). tr '\r\n' '  ' collapses both terminators.
prompt_oneline=$(echo "$prompt" | tr '\r\n' '  ' | sed 's/  */ /g' | sed 's/^ *//;s/ *$//')

# Truncate to 500 chars to keep daily note readable (full prompt is in Claude transcript)
if [ ${#prompt_oneline} -gt 500 ]; then
    prompt_oneline="${prompt_oneline:0:500}..."
fi

TODAY=$(date +%Y-%m-%d)
DAILY="${OSANWE_TEST_DAILY:-/path/to/vault/Calendar/daily/${TODAY}.md}"  # env override for hermetic testing only; default unchanged
ISO=$(date -Iseconds 2>/dev/null || date +"%Y-%m-%dT%H:%M:%S%z")

# Create daily note if missing (minimal template — SessionStart hook will fill carried-forward block separately)
if [ ! -f "$DAILY" ]; then
    mkdir -p /path/to/vault/Calendar/daily
    cat > "$DAILY" << TMPL
---
aliases: []
categories: [daily]
tags: []
status: active
created: ${TODAY}
updated: ${TODAY}
related: []
---

# ${TODAY} $(date +%A)

## Market Pulse

## Observations

## Decisions

| Domain | Decision | Why |
|--------|----------|-----|

## Commitments
- [ ]

## Insights

## Sessions Run

## Cross-References

## Tasks
- [ ]

## Log

TMPL
fi

# Append prompt under ## Log section
# CRIT-3 fix: wrap prompt in inline backticks to escape any [[wikilink]] syntax.
# Without this, user prompts containing [[broken-target]] would propagate verbatim
# into daily note ## Log, then trigger PostToolUse wikilink-check.py on subsequent
# Edits to the daily note (blocking legitimate edits for the day).
# Inline-backtick wrapping makes vault-audit.py extract_wikilinks skip the content
# (per INLINE_CODE regex strip-before-scan in v2.1.1).

# Replace any existing backticks in the prompt with single-quotes to avoid
# breaking out of the inline-code wrap (defense against backtick injection), AND
# escape [[ -> [ [ so an Obsidian wikilink marker can never form in the ## Log even
# when the backtick wrap is broken by a backtick in the prompt (vault-hygiene 2026-05-29
# Fix-B; wrap-independent belt -- the failure mode that cost the floor).
prompt_safe=$(echo "$prompt_oneline" | sed "s/\`/'/g" | sed 's/\[\[/[ [/g')

# The log line is passed through the ENVIRONMENT, not `awk -v`. POSIX awk processes
# backslash escapes in a -v assignment, so any prompt containing a Windows path turned
# `\0` into a literal NUL, `\t` into a tab, and so on. A NUL makes git classify the daily
# note as BINARY -- it stops diffing the file entirely, and the corruption is invisible in
# an editor. Observed 2026-08-12: two NULs landed from task-notification paths of the form
# ...\C--/path/to/vault\09c8a54c-... ENVIRON[] does no escape processing.
tmpfile=$(mktemp)
OSANWE_LOG_LINE="- ${ISO} :: \`${prompt_safe}\`" awk '
    /^## Log$/ {
        print
        getline
        print
        print ENVIRON["OSANWE_LOG_LINE"]
        next
    }
    { print }
' "$DAILY" > "$tmpfile" && mv "$tmpfile" "$DAILY"

exit 0
