#!/usr/bin/env bash
set -euo pipefail

VAULT_ROOT="${VAULT_ROOT:-$(pwd)}"

# Osanwe vault hook: SessionStart context injection
# 1. Outputs hot.md content for Claude context injection
# 2. Creates today's daily note from template if missing
# 3. Carries forward unchecked commitments from yesterday's daily note

HOT="${VAULT_ROOT:-$(pwd)}/wiki/hot.md"
TODAY=$(date +%Y-%m-%d)
DAILY="${VAULT_ROOT:-$(pwd)}/Calendar/daily/${TODAY}.md"
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d 2>/dev/null || echo "")
YESTERDAY_DAILY="${VAULT_ROOT:-$(pwd)}/Calendar/daily/${YESTERDAY}.md"

context=""

# Inject hot.md if it exists (with smart-emit threshold per ref-hot-md-schema)
HOT_THRESHOLD=8192   # bytes; comfortably fits single context-window slice
if [ -f "$HOT" ]; then
    HOT_BYTES=$(wc -c < "$HOT" 2>/dev/null || echo 0)
    if [ "$HOT_BYTES" -le "$HOT_THRESHOLD" ]; then
        context=$(cat "$HOT")
        echo "# hot-md emit: full ${HOT_BYTES} bytes" >&2
    else
        # Try smart-emit; fall back to raw cat on failure
        smart_output=$(python "${VAULT_ROOT:-$(pwd)}/tools/hot-md-emit-smart.py" --input "$HOT" --max-bytes "$HOT_THRESHOLD" 2>/dev/null || true)
        if [ -n "$smart_output" ]; then
            context="$smart_output"
            echo "# hot-md emit: smart-mode ${HOT_BYTES} bytes (raw) -> compressed (threshold ${HOT_THRESHOLD})" >&2
        else
            context=$(cat "$HOT")
            echo "# hot-md emit: fallback-to-raw ${HOT_BYTES} bytes (smart-emit failed or unavailable)" >&2
        fi
    fi
fi

# Inject Atlas/_MOCs/ listing (plan spec -- shared-context orientation)
mocs_listing=""
if [ -d "${VAULT_ROOT:-$(pwd)}/Atlas/_MOCs" ]; then
    for moc in "${VAULT_ROOT:-$(pwd)}/Atlas/_MOCs"/*.md; do
        [ -e "$moc" ] || continue
        mocs_listing="${mocs_listing}- $(basename "$moc")
"
    done
fi
if [ -n "$mocs_listing" ]; then
    context="${context}

[Atlas/_MOCs/]
${mocs_listing}"
fi

# Inject git status (plan spec -- working-tree awareness)
git_status=""
if command -v git >/dev/null 2>&1; then
    git_status=$(cd "${VAULT_ROOT:-$(pwd)}" 2>/dev/null && git status --short 2>/dev/null | head -20) || git_status=""
fi
if [ -n "$git_status" ]; then
    context="${context}

[git status (vault-rebuild-20260416, top 20 lines)]
${git_status}"
fi

# fs-watcher direct-edit events: not included in public mirror

# Inject stale commitments warnings (last 14 days, top 10)
# Scans Calendar/daily/*.md for unchecked - [ ] entries with ESCALATION_DATE in past.
# Python3 inline parser; silent if zero stale entries.
stale_commits=$(python3 - <<'PY' 2>/dev/null || true
import os, re, sys
from datetime import date, datetime, timedelta
from pathlib import Path
DAILY = Path(os.environ.get("VAULT_ROOT", os.getcwd())) / "Calendar" / "daily"
if not DAILY.exists():
    sys.exit(0)
today = date.today()
cutoff = today - timedelta(days=14)
pat_esc = re.compile(r"ESCALATION_DATE:\s*(\d{4}-\d{2}-\d{2})")
findings = []
for p in sorted(DAILY.glob("*.md")):
    try:
        stem_date = datetime.strptime(p.stem, "%Y-%m-%d").date()
    except ValueError:
        continue
    if stem_date < cutoff:
        continue
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        continue
    in_commit = False
    for line in text.splitlines():
        s = line.strip()
        if s == "## Commitments":
            in_commit = True
            continue
        if in_commit and s.startswith("## "):
            in_commit = False
            continue
        if in_commit and s.startswith("- [ ]"):
            m = pat_esc.search(line)
            if m:
                try:
                    esc = datetime.strptime(m.group(1), "%Y-%m-%d").date()
                except ValueError:
                    continue
                if esc < today:
                    days_overdue = (today - esc).days
                    body = line.split("(TRIGGER:")[0].strip()
                    body = re.sub(r"<!-- seeded-from:.*?-->", "", body).strip()
                    body = body.lstrip("- [ ]").strip()
                    findings.append((days_overdue, body[:120]))
findings.sort(reverse=True)
for days, body in findings[:10]:
    print(f"STALE COMMITMENT ({days}d overdue): {body}")
PY
)
if [ -n "$stale_commits" ]; then
    context="${context}

[stale commitments past escalation date (last 14d, top 10)]
${stale_commits}"
fi

# Carry forward unchecked commitments from yesterday
carried=""
if [ -n "$YESTERDAY" ] && [ -f "$YESTERDAY_DAILY" ]; then
    # Extract unchecked items from ## Commitments section
    in_commitments=false
    while IFS= read -r line; do
        if echo "$line" | grep -q "^## Commitments"; then
            in_commitments=true
            continue
        fi
        if $in_commitments && echo "$line" | grep -q "^## "; then
            break
        fi
        if $in_commitments && echo "$line" | grep -q "^\- \[ \]"; then
            carried="${carried}
${line}"
        fi
    done < "$YESTERDAY_DAILY"
fi

# Create daily note if missing
if [ ! -f "$DAILY" ]; then
    mkdir -p "${VAULT_ROOT:-$(pwd)}/Calendar/daily"

    # Build carried forward section
    carried_section=""
    if [ -n "$carried" ]; then
        carried_section="## Carried Forward (from ${YESTERDAY})
${carried}
"
    fi

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

${carried_section}
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
    context="${context}
[Daily note created: Calendar/daily/${TODAY}.md]"
    if [ -n "$carried" ]; then
        context="${context}
[Carried forward from ${YESTERDAY}:${carried}]"
    fi
fi

# Output context for Claude injection
if [ -n "$context" ]; then
    echo "$context"
fi

exit 0
