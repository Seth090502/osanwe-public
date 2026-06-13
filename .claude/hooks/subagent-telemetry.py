#!/usr/bin/env python3
"""
subagent-telemetry.py -- SubagentStart + SubagentStop JSONL logger (Feature 7).

Subagent dispatch is the most expensive runtime operation in this vault
(Explore, Plan, and 15 custom agents like thesis-critic, decision-critic,
vault-classifier-sweep, corpus-extractor). This hook gives us a structured
per-day trail of dispatches with Start/Stop correlation via tool_use_id and
duration_seconds.

CLI:
  python subagent-telemetry.py --event start    # fires on SubagentStart
  python subagent-telemetry.py --event stop     # fires on SubagentStop

Behavior:
  --event start
    1) Sweep orphan marker files (.claude/state/subagent-active-*.tmp older
       than 1 hour). Closes the orphan risk when SubagentStop never fires
       due to crash, kill, network drop, or harness restart.
    2) Append one "start" JSON line to telemetry log.
    3) Write a marker file at .claude/state/subagent-active-<tool_use_id>.tmp
       containing the start timestamp -- used by Stop branch to compute
       duration_seconds.

  --event stop
    1) Append one "stop" JSON line to telemetry log. duration_seconds is
       computed from the marker file if present; otherwise null.
    2) Delete the marker file (best-effort).

Both branches always exit 0 (telemetry must not block real work). SubagentStop
CAN block in principle (per Claude Code docs) but we explicitly choose not to.

Source: native Claude Code lifecycle events (code.claude.com/docs/en/hooks)
        verified 2026-05-21. No external code copied.
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", os.getcwd()))
STATE_DIR = VAULT_ROOT / ".claude" / "state"
ORPHAN_THRESHOLD_SECONDS = 3600  # 1 hour


def parse_payload() -> dict:
    """Read hook JSON from stdin. Returns {} on empty / unparseable input.

    Uses explicit sys.stdin.read() + json.loads(raw) rather than json.load(sys.stdin)
    because the latter shows intermittent zero-byte reads under Git Bash on Windows
    (incremental buffered reads can return early before pipe payload arrives).
    """
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return {}
        return json.loads(raw) or {}
    except (json.JSONDecodeError, ValueError, OSError):
        return {}


def telemetry_path() -> Path:
    return STATE_DIR / f"subagent-telemetry-{datetime.now().date().isoformat()}.jsonl"


def marker_path(tool_use_id: str) -> Path:
    # Sanitize tool_use_id to filesystem-safe chars
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in tool_use_id)[:80] or "unknown"
    return STATE_DIR / f"subagent-active-{safe}.tmp"


def sweep_orphans() -> int:
    """Delete subagent-active-*.tmp files older than ORPHAN_THRESHOLD_SECONDS.
    Best-effort; returns count of files swept."""
    if not STATE_DIR.exists():
        return 0
    swept = 0
    now = time.time()
    for p in STATE_DIR.glob("subagent-active-*.tmp"):
        try:
            if now - p.stat().st_mtime > ORPHAN_THRESHOLD_SECONDS:
                p.unlink()
                swept += 1
        except OSError:
            pass  # best-effort; transient FS errors swallowed
    return swept


def append_jsonl(record: dict) -> None:
    """Append one JSON line to today's telemetry log. Best-effort."""
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with telemetry_path().open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def handle_start(payload: dict) -> int:
    # 1) Orphan sweep BEFORE writing any new state
    swept = sweep_orphans()

    tool_use_id = payload.get("tool_use_id", "") or payload.get("session_id", "unknown")
    matcher = payload.get("matcher", "") or payload.get("agent_type", "")
    now = datetime.now()

    record = {
        "ts": now.isoformat(timespec="milliseconds"),
        "event": "start",
        "tool_use_id": tool_use_id,
        "agent_type": matcher,
        "session_id": payload.get("session_id", ""),
        "cwd": payload.get("cwd", ""),
    }
    if swept:
        record["orphans_swept"] = swept
    append_jsonl(record)

    # 2) Write the start-time marker for the Stop branch to read
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        marker_path(tool_use_id).write_text(now.isoformat(timespec="milliseconds"), encoding="utf-8")
    except OSError:
        pass
    return 0


def handle_stop(payload: dict) -> int:
    tool_use_id = payload.get("tool_use_id", "") or payload.get("session_id", "unknown")
    matcher = payload.get("matcher", "") or payload.get("agent_type", "")
    now = datetime.now()

    # Read marker file to compute duration_seconds
    duration_seconds = None
    marker = marker_path(tool_use_id)
    if marker.exists():
        try:
            start_iso = marker.read_text(encoding="utf-8").strip()
            start_dt = datetime.fromisoformat(start_iso)
            duration_seconds = round((now - start_dt).total_seconds(), 3)
        except (OSError, ValueError):
            duration_seconds = None
        try:
            marker.unlink()
        except OSError:
            pass

    record = {
        "ts": now.isoformat(timespec="milliseconds"),
        "event": "stop",
        "tool_use_id": tool_use_id,
        "agent_type": matcher,
        "session_id": payload.get("session_id", ""),
        "cwd": payload.get("cwd", ""),
        "duration_seconds": duration_seconds,
    }
    append_jsonl(record)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Subagent telemetry hook")
    parser.add_argument("--event", choices=("start", "stop"), required=True,
                        help="Which lifecycle event this invocation handles")
    args = parser.parse_args()
    payload = parse_payload()
    if args.event == "start":
        return handle_start(payload)
    return handle_stop(payload)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Outer safety net: never block subagent dispatch on telemetry bugs.
        sys.exit(0)
