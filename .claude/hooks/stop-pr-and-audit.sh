#!/usr/bin/env bash
set -euo pipefail

# Stop hook (Phase 5 of prevention-architecture):
# 1. Run vault-audit.py --quick to check current state
# 2. If score <90 OR any CRITICAL, emit reason via JSON output forcing Claude to
#    address findings before Stop completes (per ref-claude-code-mastery sec 4)
# 3. Otherwise: open PR via gh (or fallback echo when gh not installed)
# 4. ALWAYS check $stop_hook_active to avoid stop-resume loop

# Read stop_hook_active from stdin (PostStop JSON input)
input=$(cat)
stop_hook_active=$(echo "$input" | python -c "import json, sys; d = json.load(sys.stdin); print(d.get('stop_hook_active', False))" 2>/dev/null || echo "False")

if [ "$stop_hook_active" = "True" ]; then
    # Re-entry; do not loop
    exit 0
fi

VAULT_ROOT="${VAULT_ROOT:-$(pwd)}"
cd "$VAULT_ROOT" 2>/dev/null || exit 0
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    exit 0
fi

# Run vault audit; capture all GATE classifier counts (HI-6: not just broken-wikilinks)
audit_output=$(python "${VAULT_ROOT}/tools/vault-audit.py" --json 2>/dev/null || true)

# Parse JSON via python (more robust than regex grep against markdown output)
gate_count=$(echo "$audit_output" | python -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('tiers', {}).get('gate', {}).get('count', 0))
except Exception:
    print(0)
" 2>/dev/null || echo "0")
gate_count=${gate_count:-0}

score=$(echo "$audit_output" | python -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('score', 100))
except Exception:
    print(100)
" 2>/dev/null || echo "100")
score=${score:-100}

if [ "$gate_count" -gt 0 ] || [ "$score" -lt 95 ]; then
    # Emit JSON to block Stop completion (per ref-claude-code-mastery sec 4)
    # Covers ALL GATE classifiers (broken-wikilinks, missing-frontmatter, schema, template-drift)
    cat << EOF
{"continue": true, "reason": "vault-audit blocked Stop: score $score/100 with $gate_count GATE finding(s) present (floor invariant 95). Run /vault audit, /vault repair --apply <ids>, or set CLAUDE_VAULT_BYPASS_VALIDATOR=1 to override."}
EOF
    exit 0
fi

# Vault is clean. Proceed with PR logic (or fallback).
current_branch=$(git symbolic-ref --short HEAD 2>/dev/null || echo "")
case "$current_branch" in
    main|master|"")
        exit 0
        ;;
esac

# Only push if there are commits ahead of origin's tracking branch
git fetch origin "$current_branch" 2>/dev/null || true
ahead=$(git rev-list --count "origin/$current_branch..$current_branch" 2>/dev/null || echo "0")
[ "$ahead" -gt 0 ] || exit 0

if ! command -v gh >/dev/null 2>&1; then
    echo "stop-pr: gh not installed; vault clean at audit. Push with 'git push -u origin HEAD' and open PR manually." >&2
    exit 0
fi

if ! gh auth status >/dev/null 2>&1; then
    echo "stop-pr: gh not authenticated; run 'gh auth login' to enable PR-on-stop." >&2
    exit 0
fi

git push -u origin HEAD 2>&1 | head -5 >&2 || true
gh pr create --fill --base main 2>&1 | head -5 >&2 || true

exit 0
