#!/bin/bash
# tools/lib/capability-detect.sh -- /invest vNEXT Dynamic-Workflows (2026-06-09)
#
# LAYER SEPARATION (read before editing):
#   This script = SHELL LAYER. Exports OSANWE_ENGINE (via engine-detect.sh) and
#   OSANWE_DW_HINT. OSANWE_DW_HINT is ADVISORY -- NOT authoritative.
#
#   The AUTHORITATIVE topology decision is the in-skill check: "is the Workflow
#   tool present in the orchestrator's current session tool surface?" A shell
#   script cannot see the session tool surface, so it can never make that call.
#   OSANWE_DW_HINT=capable does NOT guarantee Workflow availability (permission-
#   restricted sessions, subagent contexts without Workflow, headless runs).
#   Skills MUST treat ambiguity as TOPOLOGY=sequential (the safe fallback).
#
# OSANWE_DW_HINT values:
#   capable     -- engine is Claude Code; Workflow tool LIKELY available in full sessions
#   sequential  -- engine is Codex/headless; Workflow tool NEVER available
#
# Usage:
#   source tools/lib/capability-detect.sh          (caller continues; both vars exported)
#   bash tools/lib/capability-detect.sh <command>  (wrapper: exports vars, execs command)
#
# Consumers: .claude/skills/invest/ref-dw-topology.md documents the two-layer
# contract; hook scripts that want the hint wrap with this instead of
# engine-detect.sh (this sources engine-detect.sh internally).
#
# Exit code (wrapper mode): passes through the wrapped command's exit code.

set -uo pipefail

# Engine detection (sourced; engine-detect.sh's source-guard skips its exec)
source "$(dirname "${BASH_SOURCE[0]}")/engine-detect.sh"

# Defense: assert the sourced detection actually exported the variable
if [ -z "${OSANWE_ENGINE:-}" ]; then
    echo "ERROR: capability-detect.sh: OSANWE_ENGINE not set after sourcing engine-detect.sh" >&2
    exit 1
fi

# Derive the advisory DW hint from the engine
if [ "${OSANWE_ENGINE}" = "claude" ]; then
    export OSANWE_DW_HINT="capable"
else
    export OSANWE_DW_HINT="sequential"
fi

# Wrapper mode: exec the wrapped command. Sourced mode: return to caller.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    exec "$@"
fi
