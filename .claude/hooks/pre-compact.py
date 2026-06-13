#!/usr/bin/env python3
"""Pre-compact hook: archive transcript + wiki/hot.md snapshot before compaction.

Fires on PreCompact event. Writes two artifacts to .claude/transcripts/:
  1. transcript-<ISO>.json -- full stdin (the transcript payload Claude Code passes)
  2. hot-snapshot-<ISO>.md -- copy of wiki/hot.md at compaction moment

Compaction loses conversational memory; the snapshot preserves the state that
Claude was operating under. Future session-continuity reconstruction can read
these artifacts to recover context the summary may have lost.

Exit 0 always (archive is best-effort; never block compaction).
"""

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


def iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H-%M-%S%z")


def main() -> int:
    vault_root = Path(os.environ.get("VAULT_ROOT", os.getcwd()))
    archive_dir = Path(os.environ.get("PRECOMPACT_ARCHIVE_DIR",
                                      str(vault_root / ".claude" / "transcripts")))
    archive_dir.mkdir(parents=True, exist_ok=True)

    stamp = iso_now()

    # Archive stdin (the transcript payload from Claude Code)
    payload = sys.stdin.read()
    if payload.strip():
        transcript_path = archive_dir / f"transcript-{stamp}.json"
        try:
            # Try to pretty-print if it parses as JSON; fall back to raw
            parsed = json.loads(payload)
            transcript_path.write_text(json.dumps(parsed, indent=2, ensure_ascii=False))
        except (json.JSONDecodeError, TypeError):
            transcript_path.write_text(payload)

    # Snapshot wiki/hot.md
    hot = Path(os.environ.get("PRECOMPACT_HOT_PATH",
                               str(vault_root / "wiki" / "hot.md")))
    if hot.exists():
        snapshot_path = archive_dir / f"hot-snapshot-{stamp}.md"
        shutil.copy2(hot, snapshot_path)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Never block compaction on hook failure -- archive is advisory, not critical
        sys.exit(0)
