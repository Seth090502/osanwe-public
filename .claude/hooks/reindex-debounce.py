#!/usr/bin/env python3
"""Optional Claude write hint for the existing admitted-source index scheduler.

The scheduler independently compares the admission registry and approved source
hashes, including changes made through Codex, shells and editors. This hook only
delays a rebuild while writes settle; it neither admits a file nor proves freshness.
Canonical .agents sources are considered; generated .claude mirrors are omitted.
"""
import sys
import json
from pathlib import Path

MARKER = Path(r"/path/to/home\.vault-substrate\.debounce-marker")
INDEXED_PREFIXES = (
    "c://path/to/vault/wiki/",
    "c://path/to/vault/calendar/",
    "c://path/to/vault/atlas/",           # TENFOLD-T5 X17 (R3 index-scope parity)
    "c://path/to/vault/efforts/",         # TENFOLD-T5 X16/X17
    "c://path/to/vault/docs/",            # TENFOLD-T5 X16/X17
    "c://path/to/vault/.agents/skills/",  # canonical sources only
    "c://path/to/vault/.agents/roles/",
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
