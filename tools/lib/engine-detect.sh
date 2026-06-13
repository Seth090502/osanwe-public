#!/bin/bash
# tools/lib/engine-detect.sh -- Mission Four (2026-05-15)
#
# Engine fingerprint wrapper. Detects whether the current invocation is under
# Claude Code or OpenAI Codex CLI; exports OSANWE_ENGINE accordingly. Then
# execs the wrapped hook script (passing through stdin + args).
#
# V8 empirical resolution (Phase 0.5 probe):
#   Claude markers (any one is definitive):
#     CLAUDECODE=1
#     AI_AGENT starts with "claude-code"
#     CLAUDE_CODE_SESSION_ID present
#   Codex markers (any one is definitive):
#     CODEX_VERSION present (assumed; not docs-confirmed; verify Phase 5)
#     CODEX_ prefix env var present
#     parent process named "codex" or "codex-cli"
#   Default: claude (safer; codex-side gets explicitly identified)
#
# Usage from settings.json or .codex/config.toml:
#   "command": "bash ${VAULT_ROOT}/tools/lib/engine-detect.sh python ${VAULT_ROOT}/tools/wikilink-check.py"
#
# Hook scripts can read $OSANWE_ENGINE to branch behavior. Most hooks need not branch;
# tools/lib/hook_payload.py handles stdin schema differences via defensive parsing.
#
# Exit code: passes through the wrapped command's exit code.

set -uo pipefail

# Detect Claude (any one signal is definitive)
if [ "${CLAUDECODE:-}" = "1" ]; then
    export OSANWE_ENGINE="claude"
elif [[ "${AI_AGENT:-}" == claude-code* ]]; then
    export OSANWE_ENGINE="claude"
elif [ -n "${CLAUDE_CODE_SESSION_ID:-}" ]; then
    export OSANWE_ENGINE="claude"
# Detect Codex
elif [ -n "${CODEX_VERSION:-}" ]; then
    export OSANWE_ENGINE="codex"
elif env | grep -q "^CODEX_"; then
    export OSANWE_ENGINE="codex"
else
    # Process ancestry fallback (Windows + msys-bash compatible)
    parent_comm="$(ps -o comm= -p $PPID 2>/dev/null | head -1 | tr -d '[:space:]')"
    if echo "$parent_comm" | grep -qiE '^codex(-cli)?$'; then
        export OSANWE_ENGINE="codex"
    else
        export OSANWE_ENGINE="claude"
    fi
fi

# Pass through to wrapped command (stdin inherited; args forwarded; exit code preserved).
# Source-guard (invest vNEXT 2026-06-09): when SOURCED (e.g. by capability-detect.sh),
# export OSANWE_ENGINE and return without exec'ing -- the caller continues.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    exec "$@"
fi
