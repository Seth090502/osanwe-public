#!/usr/bin/env bash
# F11 orchestrator (bash wrapper) -- cascade-aware management of
# .claude/state/auto-commit-disabled. Mirrors tools/lib/f11_orchestrator.py.
#
# Usage:
#   source "${VAULT_ROOT:-$(pwd)}/tools/lib/f11_orchestrator.sh"
#   f11_begin "my-skill-cascade" parent
#     f11_checkpoint "phase-c-edit-start"
#     # ... edits + commits ...
#     f11_commit_boundary "phase-j-commit-1"
#     f11_commit_boundary "phase-j-commit-2"
#   f11_end "my-skill-cascade" parent
#
# Roles:
#   leaf    (default) Independent invocation; set on begin; clear on end.
#           Collide-HALT (return 2) if flag already present.
#   parent  Top of a cascade; same as leaf but signals intent.
#   child   Within a cascade; detect parent flag; do NOT set/clear our own.
#           If parent flag absent, behave like leaf.
#
# F.halt: if a script sources this and exits abnormally, F11 stays set
# (no auto-clear). User must inspect or manually rm to recover.

VAULT_ROOT="${CLAUDE_VAULT_ROOT:-${VAULT_ROOT:-$(pwd)}}"
F11_PATH="$VAULT_ROOT/.claude/state/auto-commit-disabled"

_f11_history_path() {
    local d
    d=$(date +%Y-%m-%d)
    printf '%s/.claude/state/f11-history-%s.jsonl' "$VAULT_ROOT" "$d"
}

_f11_log_event() {
    local event="$1"
    local reason="$2"
    local role="${3:-leaf}"
    local data="${4:-{}}"
    local hp ts
    hp=$(_f11_history_path)
    mkdir -p "$VAULT_ROOT/.claude/state" 2>/dev/null || return 0
    ts=$(date -Iseconds 2>/dev/null || date +"%Y-%m-%dT%H:%M:%S")
    # Best-effort JSON line; never fails the caller
    printf '{"ts":"%s","event":"%s","reason":"%s","cascade_role":"%s","data":%s}\n' \
        "$ts" "$event" "$reason" "$role" "$data" >> "$hp" 2>/dev/null || true
}

f11_begin() {
    local reason="${1:-bash-session}"
    local role="${2:-leaf}"
    if [ -f "$F11_PATH" ]; then
        case "$role" in
            child)
                _f11_log_event "child_join" "$reason" "$role" '{"parent_flag_present":true}'
                export F11_WE_OWN=0
                return 0
                ;;
            *)
                _f11_log_event "collision" "$reason" "$role" '{"flag_already_set":true}'
                echo "[f11] COLLISION: F11 already set ($F11_PATH); HALT" >&2
                return 2
                ;;
        esac
    fi
    mkdir -p "$VAULT_ROOT/.claude/state"
    touch "$F11_PATH"
    _f11_log_event "set" "$reason" "$role" "{\"path\":\"$F11_PATH\"}"
    export F11_WE_OWN=1
    return 0
}

f11_checkpoint() {
    local label="${1:-checkpoint}"
    local role="${2:-leaf}"
    _f11_log_event "checkpoint" "$label" "$role" '{}'
}

f11_commit_boundary() {
    local label="${1:-commit}"
    local role="${2:-leaf}"
    _f11_log_event "commit_boundary" "$label" "$role" "{\"label\":\"$label\"}"
}

f11_end() {
    local reason="${1:-end}"
    local role="${2:-leaf}"
    if [ "${F11_WE_OWN:-0}" = "1" ]; then
        rm -f "$F11_PATH"
        _f11_log_event "clear" "$reason" "$role" '{}'
        unset F11_WE_OWN
    else
        _f11_log_event "child_leave" "$reason" "$role" '{}'
    fi
    return 0
}

f11_status() {
    if [ -f "$F11_PATH" ]; then
        echo "F11 set ($F11_PATH)"
        return 0
    fi
    echo "F11 not set"
    return 1
}
