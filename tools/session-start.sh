#!/usr/bin/env bash
set -euo pipefail

# Osanwe vault hook: SessionStart context injection
# 1. Outputs hot.md content for Claude context injection
# 2. Creates today's daily note from template if missing
# 3. Carries forward unchecked commitments from yesterday's daily note

HOT="/path/to/vault/wiki/hot.md"
TODAY=$(date +%Y-%m-%d)
DAILY="/path/to/vault/Calendar/daily/${TODAY}.md"
# X05 fix (tenfold-t1): walk back to the MOST RECENT existing daily note (up to 30d),
# not exactly-yesterday -- an idle day used to break the carry-forward chain silently.
YESTERDAY=""
YESTERDAY_DAILY=""
for _i in $(seq 1 30); do
    _d=$(date -d "-${_i} day" +%Y-%m-%d 2>/dev/null || true)
    [ -n "$_d" ] || continue
    if [ -f "/path/to/vault/Calendar/daily/${_d}.md" ]; then
        YESTERDAY="$_d"
        YESTERDAY_DAILY="/path/to/vault/Calendar/daily/${_d}.md"
        break
    fi
done

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
        smart_output=$(python tools/hot-md-emit-smart.py --input "$HOT" --max-bytes "$HOT_THRESHOLD" 2>/dev/null || true)
        if [ -n "$smart_output" ]; then
            context="$smart_output"
            # X22p honest emit (TENFOLD T2): report REAL emitted bytes, never an unmeasured "compressed" claim.
            smart_bytes=$(printf %s "$smart_output" | wc -c | tr -d ' ')
            echo "# hot-md emit: smart-mode raw ${HOT_BYTES} -> emitted ${smart_bytes} bytes (budget ${HOT_THRESHOLD})" >&2
        else
            context=$(cat "$HOT")
            echo "# hot-md emit: fallback-to-raw ${HOT_BYTES} bytes (smart-emit failed or unavailable)" >&2
        fi
    fi
fi

# Inject Atlas/_MOCs/ listing (plan spec — shared-context orientation)
mocs_listing=""
if [ -d "/path/to/vault/Atlas/_MOCs" ]; then
    for moc in /path/to/vault/Atlas/_MOCs/*.md; do
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

# Inject git status (plan spec — working-tree awareness)
git_status=""
if command -v git >/dev/null 2>&1; then
    git_status=$(cd /path/to/vault 2>/dev/null && git status --short 2>/dev/null | head -20) || git_status=""
fi
if [ -n "$git_status" ]; then
    context="${context}

[git status (vault-rebuild-20260416, top 20 lines)]
${git_status}"
fi

# Inject fs-watcher direct-edit warnings (last 24h, top 5)
# Reads tools/fs-watcher-state.json; silent if file absent/empty/zero recent events.
# Python3 inline parser (no jq dep on Win11). Graceful degradation on any error.
FS_WATCHER_STATE="/path/to/vault/tools/fs-watcher-state.json"
if [ -f "$FS_WATCHER_STATE" ] && [ -s "$FS_WATCHER_STATE" ]; then
    fs_events=$(python3 - <<'PY' 2>/dev/null || true
import json, sys
from datetime import datetime, timezone, timedelta
try:
    with open("/path/to/vault/tools/fs-watcher-state.json", encoding="utf-8") as f:
        state = json.load(f)
except Exception:
    sys.exit(0)
events = state.get("events", []) or []
cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
recent = []
for e in events:
    ts = e.get("timestamp", "")
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        continue
    if dt >= cutoff:
        recent.append((dt, e.get("path", "?")))
recent.sort(key=lambda x: x[0], reverse=True)
for dt, path in recent[:5]:
    print(f"DIRECT-EDIT WARNING: {path} at {dt.isoformat()}")
PY
    )
    if [ -n "$fs_events" ]; then
        context="${context}

[fs-watcher direct-edit events (last 24h, top 5)]
${fs_events}"
    fi
fi

# Inject stale commitments warnings (note-date window 365d, top 10)
# Scans Calendar/daily/*.md for unchecked - [ ] entries with ESCALATION_DATE in past.
# Python3 inline parser; silent if zero stale entries.
# X05 fix (tenfold-t1): stem cutoff was 14d -- any open older than two weeks became
# permanently invisible. Widened to 365d (all operational-era notes).
stale_commits=$(python3 - <<'PY' 2>/dev/null || true
import os, re, sys
from datetime import date, datetime, timedelta
from pathlib import Path
DAILY = Path("/path/to/vault/Calendar/daily")
if not DAILY.exists():
    sys.exit(0)
today = date.today()
cutoff = today - timedelta(days=365)
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

[stale commitments past escalation date (365d window, top 10)]
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
        # X05 fix (tenfold-t1): require non-empty body -- the template's blank
        # "- [ ]" placeholder used to be carried forward as a phantom commitment.
        if $in_commitments && echo "$line" | grep -q "^\- \[ \][[:space:]]*[^[:space:]]"; then
            carried="${carried}
${line}"
        fi
    done < "$YESTERDAY_DAILY"
fi

# Create daily note if missing
if [ ! -f "$DAILY" ]; then
    mkdir -p /path/to/vault/Calendar/daily

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

# --- local delegation lane: today's consumption, one line ---------------------------
# render_report is a PURE LEDGER READ -- no daemon contact, no network, works with Ollama
# stopped. This exists because the lane's pre-registered falsifier (2026-09-11) is
# adjudicated from that ledger and NOTHING else surfaces it: open-loops.py never reads the
# gates registry, and the decision-log entry it would key on is bold-form, which the
# digest's regex misses. Seeing the count every session is what keeps the check honest in
# both directions. Failure here is silent by design; a status line must never block boot.
LANE_LINE=$(python tools/delegate.py --report --since "$TODAY" 2>/dev/null | tail -1 || true)
if [ -n "$LANE_LINE" ]; then
    context="${context}
[local lane today] ${LANE_LINE}"
fi

# Output context for Claude injection.
#
# MODE-3 GATE (2026-08-15). Under CLAUDE_LANE_MODE=local the session is driven by a local
# 27B, and this emission is the largest injected block in its prompt: MEASURED at 15,716
# bytes here, inside a 44,360-char SessionStart aggregate (~12,300 tok) that was 63% of a
# 19,379-token mode-3 prompt after the tool-surface diet. A local model cannot act on an
# open-loops digest or a distillate index; it does mechanical file work.
#
# Everything ABOVE this line still runs -- daily-note creation and commitment carry-forward
# are side effects modes 1/2 depend on and are NOT skipped. Only the injection is replaced,
# by a pointer the model can follow if it ever needs the real thing.
# Modes 1 and 2 are byte-for-byte unchanged. Tier signal proven to reach hook subprocesses
# by the 2026-08-14 red team. Revert = delete this if-branch.
if [ "${CLAUDE_LANE_MODE:-}" = "local" ]; then
    echo "[session-start] suppressed for CLAUDE_LANE_MODE=local (local-model context budget)."
    echo "  Full surface on demand: wiki/hot.md, tools/open-loops.py, Atlas/_MOCs/."
    exit 0
fi

if [ -n "$context" ]; then
    echo "$context"
fi

exit 0
