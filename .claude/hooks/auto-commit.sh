#!/usr/bin/env bash
set -euo pipefail

# Compatibility no-op for existing PostToolUse Write|Edit|MultiEdit bindings.
# Per-edit staging/commits were retired 2026-09-12. Agents now prepare meaningful,
# validated milestone commits manually on main or an explicit feature branch,
# with the normal commit hooks and checks intact. This hook performs no Git or
# filesystem operations and does not parse the tool payload.

exit 0
