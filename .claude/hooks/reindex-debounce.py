#!/usr/bin/env python3
"""PostToolUse hook: touch the reindex debounce marker on vault content writes.

Fires on Write/Edit/MultiEdit. If the written path is under an INDEXED subtree
(wiki / Calendar / private -- the Phase 3 index scope), it updates the debounce
marker's mtime; a Task-Scheduler-polled reindex-runner.mjs rebuilds the index
~5 min after writes settle. Writes outside the indexed subtrees (Atlas, .claude,
tools, .agents, out-of-vault) are ignored -- they cannot change index contents.

Instant + never blocks: exit 0 on every path, including errors. Phase 3.7.
"""
import sys
import json
import os
from pathlib import Path

SUBSTRATE_ROOT = Path(os.environ.get("SUBSTRATE_ROOT",
                                     str(Path.home() / ".vault-substrate")))
MARKER = SUBSTRATE_ROOT / ".debounce-marker"

VAULT_ROOT = os.environ.get("VAULT_ROOT", os.getcwd()).lower().replace("\\", "/")
if not VAULT_ROOT.endswith("/"):
    VAULT_ROOT += "/"

INDEXED_SUFFIXES = ("wiki/", "calendar/", "private/")


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
    # Check if path is under vault root + an indexed subtree
    if not norm.startswith(VAULT_ROOT):
        return 0
    rel = norm[len(VAULT_ROOT):]
    if not any(rel.startswith(s) for s in INDEXED_SUFFIXES):
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
