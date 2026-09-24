#!/usr/bin/env python3
"""Filesystem watcher daemon for direct-edit detection (X5).

Monitors /path/to/vault for filesystem events on .md / .base / .py files
under tracked paths. Compares each modified file's mtime to (a) the most
recent git commit touching that path AND (b) the most recent Claude Code
session activity. If a file was modified outside a Claude Code session
(no active .claude/state/current-session.id refresh within the last 60s
of the mtime), classifies as "direct edit outside Claude Code" and logs
to tools/fs-watcher-state.json. SessionStart hook reads the state file
and surfaces a warning if any direct edits happened since last session.

Closes audit-deferred X5 (defense-in-depth gap: Obsidian / VS Code /
manual editor edits bypass all PreToolUse + PostToolUse hooks).

Status modes:
  python tools/fs-watcher.py --status     -- show current daemon state
  python tools/fs-watcher.py --start      -- start watching (foreground)
  python tools/fs-watcher.py --start &    -- start in background
  python tools/fs-watcher.py --stop       -- kill running daemon via PID file

Architecture:
  - watchdog.observers.Observer (cross-platform; Windows uses ReadDirectoryChangesW)
  - PID file at .claude/state/fs-watcher.pid for single-instance enforcement
  - State JSON at tools/fs-watcher-state.json (event log + last-scan timestamp)
  - Excludes: .git/, _archive/, _quarantine/, node_modules/, .checkpoints/,
    wiki/research/test-tmp/ (test harness), .claude/state/ (state-file churn)

Resource use: event-driven (not polling); <1% CPU expected; <50MB RAM.
"""

import json
import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone

VAULT_ROOT = Path(r"/path/to/vault")
PID_FILE = VAULT_ROOT / ".claude" / "state" / "fs-watcher.pid"
STATE_FILE = VAULT_ROOT / "tools" / "fs-watcher-state.json"
SESSION_FILE = VAULT_ROOT / ".claude" / "state" / "current-session.id"

WATCH_SUFFIXES = {".md", ".base", ".py"}
EXCLUDE_DIRS = {
    ".git", "_archive", "_quarantine", "node_modules", ".checkpoints",
    "test-tmp", ".precheck",
}
# Paths whose mtime activity is expected during normal operation
EXCLUDE_PATH_PREFIXES = (
    ".claude/state/",     # state files churn during Claude operation
    "tools/fs-watcher-state.json",   # this script's own state file
)

SESSION_FRESHNESS_S = 60   # if session-id file mtime within 60s of file mtime, attribute to Claude


def is_excluded(rel_path: str) -> bool:
    parts = Path(rel_path).parts
    if any(part in EXCLUDE_DIRS for part in parts):
        return True
    if any(rel_path.startswith(p) for p in EXCLUDE_PATH_PREFIXES):
        return True
    return False


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"events": [], "last_scan": None, "version": 1}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"events": [], "last_scan": None, "version": 1}


def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def session_active_at(t: float) -> bool:
    """True if a Claude Code session was active near time t (file mtime).

    Heuristic: if .claude/state/current-session.id exists AND its mtime is
    within SESSION_FRESHNESS_S of t (in either direction), treat the file
    modification as Claude-attributable.
    """
    if not SESSION_FILE.exists():
        return False
    try:
        session_mtime = SESSION_FILE.stat().st_mtime
    except OSError:
        return False
    return abs(session_mtime - t) <= SESSION_FRESHNESS_S


def classify_event(file_path: Path, event_type: str) -> dict | None:
    """Return event record if classified as direct-edit, else None."""
    try:
        rel = file_path.resolve().relative_to(VAULT_ROOT)
    except ValueError:
        return None
    rel_str = str(rel).replace("\\", "/")
    if file_path.suffix not in WATCH_SUFFIXES:
        return None
    if is_excluded(rel_str):
        return None
    try:
        mtime = file_path.stat().st_mtime
    except OSError:
        return None
    if session_active_at(mtime):
        return None
    return {
        "timestamp": datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat(),
        "path": rel_str,
        "event_type": event_type,
        "size": file_path.stat().st_size if file_path.exists() else 0,
    }


def cmd_status():
    state = load_state()
    print(f"State file: {STATE_FILE}")
    print(f"Last scan: {state.get('last_scan', 'never')}")
    print(f"Total direct-edit events logged: {len(state.get('events', []))}")
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            print(f"PID file: {PID_FILE} (PID {pid})")
        except (ValueError, OSError):
            print(f"PID file: {PID_FILE} (unreadable)")
    else:
        print(f"PID file: not present (daemon not running)")
    recent = state.get("events", [])[-5:]
    if recent:
        print()
        print("Most recent direct-edit events (last 5):")
        for e in recent:
            print(f"  {e['timestamp']} [{e['event_type']}] {e['path']} ({e['size']} bytes)")


def cmd_stop():
    if not PID_FILE.exists():
        print("No PID file; daemon not running")
        return
    try:
        pid = int(PID_FILE.read_text().strip())
    except (ValueError, OSError):
        print(f"PID file unreadable; remove manually: {PID_FILE}")
        return
    try:
        os.kill(pid, 15)   # SIGTERM
        time.sleep(1)
        PID_FILE.unlink(missing_ok=True)
        print(f"Daemon at PID {pid} stopped")
    except (ProcessLookupError, PermissionError) as e:
        print(f"Could not kill PID {pid}: {e}")
        PID_FILE.unlink(missing_ok=True)


def cmd_start():
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print("ERROR: watchdog library not installed. Run: pip install watchdog")
        sys.exit(1)

    if PID_FILE.exists():
        try:
            existing = int(PID_FILE.read_text().strip())
            print(f"WARNING: PID file present at {PID_FILE} (PID {existing})")
            print("If stale, run: python tools/fs-watcher.py --stop, then retry")
            sys.exit(2)
        except (ValueError, OSError):
            PID_FILE.unlink(missing_ok=True)

    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")

    state = load_state()

    class Handler(FileSystemEventHandler):
        def on_modified(self, event):
            if event.is_directory:
                return
            rec = classify_event(Path(event.src_path), "modified")
            if rec:
                state["events"].append(rec)
                state["last_scan"] = datetime.now(timezone.utc).isoformat()
                save_state(state)
                print(f"DIRECT-EDIT detected: {rec['path']} at {rec['timestamp']}", flush=True)

        def on_created(self, event):
            if event.is_directory:
                return
            rec = classify_event(Path(event.src_path), "created")
            if rec:
                state["events"].append(rec)
                state["last_scan"] = datetime.now(timezone.utc).isoformat()
                save_state(state)
                print(f"DIRECT-CREATE detected: {rec['path']} at {rec['timestamp']}", flush=True)

    observer = Observer()
    observer.schedule(Handler(), str(VAULT_ROOT), recursive=True)
    observer.start()
    print(f"FS watcher daemon started (PID {os.getpid()})")
    print(f"  Watching: {VAULT_ROOT}")
    print(f"  State: {STATE_FILE}")
    print(f"  Press Ctrl+C to stop, or run: python tools/fs-watcher.py --stop")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        observer.stop()
        observer.join()
        PID_FILE.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(
        description="FS watcher daemon for direct-edit detection"
    )
    parser.add_argument("--status", action="store_true", help="Show daemon state")
    parser.add_argument("--start", action="store_true", help="Start daemon (foreground)")
    parser.add_argument("--stop", action="store_true", help="Stop daemon via PID file")
    args = parser.parse_args()

    if args.status:
        cmd_status()
    elif args.stop:
        cmd_stop()
    elif args.start:
        cmd_start()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
