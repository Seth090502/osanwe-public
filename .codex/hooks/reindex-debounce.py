#!/usr/bin/env python3
"""PostToolUse hook: touch the reindex debounce marker on vault content writes.

Fires on Write/Edit/MultiEdit. If the written path is under an INDEXED subtree
(wiki / Calendar / private / Atlas / Efforts / docs / .claude/skills -- the Phase 3
index scope), it updates the debounce marker's mtime; a Task-Scheduler-polled
reindex-runner.mjs rebuilds the index ~5 min after writes settle. Writes outside the
indexed subtrees (tools, .agents, other .claude/, out-of-vault) are ignored -- they
cannot change index contents.

Atlas + Efforts + docs + .claude/skills added 2026-07-04 (TENFOLD-T5 X16/X17): R3 put
Atlas into the index SCAN but never into these debounce prefixes, so Atlas (and the new
T5 dirs) never triggered a reindex -- the freshness leak this closes. Prefixes MUST stay
in lockstep with index-vault.mjs SCAN.

Instant + never blocks: exit 0 on every path, including errors. Phase 3.7.
"""
import sys
import json
from pathlib import Path

MARKER = Path(r"/path/to/home\.vault-substrate\.debounce-marker")
INDEXED_PREFIXES = (
    "c://path/to/vault/wiki/",
    "c://path/to/vault/calendar/",
    "c://path/to/vault/private/",
    "c://path/to/vault/atlas/",           # TENFOLD-T5 X17 (R3 index-scope parity)
    "c://path/to/vault/efforts/",         # TENFOLD-T5 X16/X17
    "c://path/to/vault/docs/",            # TENFOLD-T5 X16/X17
    "c://path/to/vault/.claude/skills/",  # TENFOLD-T5 X16/X17
)


def main():
    raw = sys.stdin.read()
    if not raw or not raw.strip():
        return 0
    try:
        d = json.loads(raw)
    except Exception:
        return 0
    if d.get("tool_name") not in ("Write", "Edit", "MultiEdit"):
        return 0
    ti = d.get("tool_input") or {}
    fp = ti.get("file_path") or ti.get("path") or ""
    if not fp:
        return 0
    norm = fp.replace("\\", "/").lower()
    if norm.startswith("/c/"):           # MSYS form -> drive form
        norm = "c:/" + norm[3:]
    if not any(norm.startswith(p) for p in INDEXED_PREFIXES):
        return 0
    try:
        MARKER.touch()                   # update mtime to now
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Never block a write on hook failure.
        sys.exit(0)
