#!/usr/bin/env python3
"""
post-compact-reinject.py -- PostCompact hot.md re-injection (Feature 3).

Claude Code compacts conversation context when the window fills. Hook-injected
SessionStart context (wiki/hot.md head) does NOT survive compaction. This
hook fires after compaction completes and re-emits hot.md head bytes to
stdout for context re-injection on the next turn.

Best-effort + advisory:
- Always exits 0 (the PostCompact event cannot block; no point trying).
- Silent on every error (missing hot.md, IO failure, JSON parse glitch).
- Bounded output (8 KiB threshold to match session-start.sh).

Reads stdin JSON (PostCompact payload: hook_event_name, matcher, session_id,
transcript_path, cwd) but treats it as opaque - only hot.md is emitted.

Source pattern: AgriciDaniel/claude-obsidian@75d3b6feb77b96c6bb16599c4550cc9703553d87
  hooks/hooks.json PostCompact handler (MIT licensed; verified 2026-05-21).
  Adapted from "prompt"-type to "command"-type to match the vault's
  SessionStart hot.md emission pattern in tools/session-start.sh.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", os.getcwd()))
# Defaults are the production paths. The env overrides exist only for hermetic
# testing and never change runtime behavior when unset.
HOT_PATH = Path(os.environ.get("POSTCOMPACT_HOT_PATH", str(VAULT_ROOT / "wiki" / "hot.md")))
SMART_EMIT = Path(os.environ.get("POSTCOMPACT_SMART_EMIT", str(VAULT_ROOT / "tools" / "hot-md-emit-smart.py")))
MAX_BYTES = 8192


def main() -> int:
    # Drain stdin (consume the PostCompact JSON payload; we do not use its fields).
    try:
        sys.stdin.read()
    except (OSError, ValueError):
        pass

    if not HOT_PATH.exists():
        return 0

    try:
        data = HOT_PATH.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 0

    # If hot.md fits the budget, emit it whole (unchanged behavior).
    if len(data.encode("utf-8")) <= MAX_BYTES:
        sys.stdout.write(data)
        return 0

    # hot.md exceeds the budget. Prefer the smart priority-ordered subset
    # (frontmatter + Last Session + Active Context + Pending-Items summary) so the
    # in-flight ## Active Context survives compaction even though it sits far past
    # the raw MAX_BYTES head. Fall back to raw-head truncation on ANY failure
    # (non-zero exit, empty output, missing helper, timeout, exception) so a
    # PostCompact recovery is NEVER lost -- the prior behavior is byte-preserved.
    smart = ""
    try:
        proc = subprocess.run(
            [sys.executable, str(SMART_EMIT),
             "--input", str(HOT_PATH), "--max-bytes", str(MAX_BYTES)],
            capture_output=True, text=True, timeout=10,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            smart = proc.stdout
    except Exception:
        smart = ""

    if smart.strip():
        sys.stdout.write(smart)
        return 0

    # Fallback: raw-head truncation on a byte boundary (original behavior, byte-preserved).
    head_bytes = data.encode("utf-8")[:MAX_BYTES]
    try:
        head = head_bytes.decode("utf-8")
    except UnicodeDecodeError:
        head = head_bytes.decode("utf-8", errors="ignore")
    sys.stdout.write(head)
    sys.stdout.write("\n\n[hot.md truncated at 8 KiB; full file at wiki/hot.md]\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
