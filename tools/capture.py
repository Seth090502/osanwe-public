#!/usr/bin/env python3
"""capture.py -- prefix-capture lane (TENFOLD T8; X53 + X42).

Smallest-viable domain-action capture: log a real-world action to today's daily
note with one command, so per-domain actions accrue without a full skill run.
This is the sustainable feeder for the Domain-pulse scoreboard metric (per-domain
logged actions/week) and the daily-note human layer (X42).

BUILD-gated (roadmap doctrine a): ships read-only-append, wired to nothing.
Promotion review ~2026-08-03 (30-day gate): keep if the daily notes show captures,
delete if unused. A future promotion can route lanes to their domain log tables
(other domain logs); this v1 stays minimal.

Usage:
  python tools/capture.py <lane> "<note>"
    <lane>: a domain label -- research | ops | invest | <any>
  Examples:
    python tools/capture.py <lane> "<note>"
    python tools/capture.py research "<activity-log-entry>"
    python tools/capture.py ops "<note>"

Appends `- [HH:MM] <lane>: <note>` under today's daily note ## Observations (the
sanctioned daily-note line format). Append-only; never rewrites existing lines.
NON-FATAL: prints a message and exits 0 on any problem (never blocks the caller).
"""

from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path

VAULT = Path("/path/to/vault")
DAILY_DIR = VAULT / "Calendar" / "daily"
SECTION = "## Observations"


def main() -> int:
    if len(sys.argv) < 3:
        print('usage: python tools/capture.py <lane> "<note>"')
        return 0
    lane = sys.argv[1].rstrip(":").strip().lower()
    note = " ".join(sys.argv[2:]).strip()
    if not lane or not note:
        print("capture: empty lane or note; nothing logged")
        return 0
    p = DAILY_DIR / f"{date.today().isoformat()}.md"
    if not p.exists():
        print(f"capture: today's daily note {p.name} not found (SessionStart creates it); nothing logged")
        return 0
    row = f"- [{datetime.now().strftime('%H:%M')}] {lane}: {note}"
    try:
        lines = p.read_text(encoding="utf-8").splitlines()
        out, inserted = [], False
        for ln in lines:
            out.append(ln)
            if not inserted and ln.strip() == SECTION:
                out.append("")
                out.append(row)
                inserted = True
        if not inserted:  # no Observations section -> append at end
            out.append(row)
        p.write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"captured -> {p.name} ## Observations: {row}")
    except Exception as e:  # append must never crash the caller
        print(f"capture: non-fatal error ({e}); nothing logged")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # non-fatal by contract
