# FS Watcher Daemon (X5)

Defense-in-depth: detect file modifications that bypass Claude Code's PreToolUse + PostToolUse hook chain (e.g., Obsidian inline edits, VS Code save, manual nano/vim, third-party tools, file syncs).

## Why this exists

The vault prevention architecture (validators, GATE classifiers, F11 Phase C, atomic-commit discipline) only fires when files are written via Claude Code's Write/Edit/MultiEdit tools. Edits made outside Claude Code skip every gate. The audit's S5 governance fragility list calls this out as item 4: "Direct file edits outside Claude Code -- bypasses ALL hooks. SessionStart score-check is only surface."

The FS watcher closes this gap by:
1. Monitoring vault filesystem events in real time via watchdog (Windows: ReadDirectoryChangesW; Linux: inotify; macOS: FSEvents).
2. Classifying each event by attribution: Claude-Code-attributable (within 60s of current-session.id mtime) vs. direct-edit (no active session at event time).
3. Logging direct edits to tools/fs-watcher-state.json.
4. Surfacing warnings at next SessionStart so operators can review what changed outside session boundaries.

## Activation (one-time, user-interactive)

### 1. Install watchdog

    pip install watchdog

### 2. Start daemon

    python tools/dev/fs-watcher.py --start

Foreground mode is best for first run (you'll see direct-edit events as they happen). Press Ctrl+C to stop.

### 3. Background activation (production)

On Windows, hidden Start-Process or Task Scheduler at-logon:

    Start-Process -WindowStyle Hidden python -ArgumentList "tools\dev\fs-watcher.py","--start"

Or Task Scheduler trigger At-log-on with action: python.exe with args "tools\dev\fs-watcher.py --start"

Linux/macOS systemd user service: TBD; vault is currently Windows-primary.

### 4. Status check

    python tools/dev/fs-watcher.py --status

Output: state file path, last scan timestamp, total direct-edit events logged, PID file path (or "not running" if absent), most recent 5 direct-edit events.

### 5. Stop daemon

    python tools/dev/fs-watcher.py --stop

Reads PID file, sends SIGTERM, removes PID file.

## What it watches

- Files matching suffixes: .md, .base, .py
- Under the vault root, recursive
- Excludes: .git/, _archive/, _quarantine/, node_modules/, .checkpoints/, wiki/research/test-tmp/, .claude/state/ (state files churn during normal operation; would generate noise)

## What gets logged

Each direct-edit event:

    {
      "timestamp": "2026-04-28T18:45:00+00:00",
      "path": "Calendar/daily/2026-04-28.md",
      "event_type": "modified",
      "size": 12345
    }

Stored in tools/fs-watcher-state.json as a JSON list under the events key. last_scan is the ISO timestamp of the most recent event.

## SessionStart integration

The vault's .claude/hooks/session-start.sh will read tools/fs-watcher-state.json at session start and surface a warning if direct-edit events occurred since the previous session. Implementation deferred; the daemon writes the state, the hook reads it.

## Resource use

- watchdog is event-driven (not polling); CPU usage is near zero between events
- Memory: <50MB
- State file growth: ~200 bytes per event; rotate at 10K events (TBD; not yet implemented)

## Known limitations

- Heuristic attribution: "session active" check is a 60s window around the current-session.id file mtime. Aggressive concurrent direct-edits during a Claude Code session may be misclassified as Claude-attributable.
- Network filesystem support: tested on local NTFS only. SMB / SyncThing / Dropbox / OneDrive may generate spurious events.
- Permissions: daemon needs read access to all watched paths; no special privileges otherwise.

## Status as of 2026-04-28

- Helper script tools/dev/fs-watcher.py shipped (moved from tools/ in F2 2026-05-21)
- Documentation docs/fs-watcher.md shipped (this file)
- SessionStart hook integration deferred to follow-up commit
- Activation requires user runs pip install watchdog + python tools/dev/fs-watcher.py --start once
