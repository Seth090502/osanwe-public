#!/bin/bash
# tools/lib/capability-detect.sh -- /invest vNEXT Dynamic-Workflows (2026-06-09;
# self-contained since the 2026-08-10 cross-harness cutover retired the engine-fingerprint shim)
#
# LAYER SEPARATION (read before editing):
#   This script = SHELL LAYER. Exports OSANWE_DW_HINT (ADVISORY -- NOT authoritative).
#
#   The AUTHORITATIVE topology decision is the in-skill check: "is the Workflow
#   tool present in the orchestrator's current session tool surface?" A shell
#   script cannot see the session tool surface, so it can never make that call.
#   OSANWE_DW_HINT=capable does NOT guarantee Workflow availability (permission-
#   restricted sessions, subagent contexts without Workflow, headless runs).
#   Skills MUST treat ambiguity as TOPOLOGY=sequential (the safe fallback).
#
# OSANWE_DW_HINT values:
#   capable     -- definitive Claude Code marker present; Workflow tool LIKELY
#                  available in full sessions
#   sequential  -- any other harness (Codex/OpenCode/Goose/Crush/Cline/Pi/local)
#                  or no marker; Workflow tool NEVER available there
#
# Usage:
#   source tools/lib/capability-detect.sh          (caller continues; vars exported)
#   bash tools/lib/capability-detect.sh <command>  (wrapper: exports vars, execs command)
#
# Consumers: .agents/skills/invest/ref-dw-topology.md documents the two-layer contract.
#
# Exit code (wrapper mode): passes through the wrapped command's exit code.

set -uo pipefail

# Claude Code detection, inlined (V8 markers; any one is definitive).
# Cross-harness posture: every non-Claude harness gets the sequential hint --
# no per-harness fingerprinting needed because sequential is the safe fallback.
if [ "${CLAUDECODE:-}" = "1" ] \
   || [[ "${AI_AGENT:-}" == claude-code* ]] \
   || [ -n "${CLAUDE_CODE_SESSION_ID:-}" ]; then
    export OSANWE_DW_HINT="capable"
else
    export OSANWE_DW_HINT="sequential"
fi

# Wrapper mode: exec the wrapped command. Sourced mode: return to caller.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    exec "$@"
fi
