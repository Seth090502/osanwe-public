#!/usr/bin/env python3
"""entity-triage.py -- A4: classify the 39 stale ticker entities.

For each ticker entity untouched >60d: cross-references store price activity,
inbound links (from the vault corpus via simple grep), and whether it appears in
any recent analysis. Emits a triage table:
  KEEP-WATCH  -- held/watched, levels referenced, or linked recently
  HISTORICAL  -- no recent refs; candidate for archive review (NOT auto-archived)
"""

import glob
import os
import re
import subprocess
import sqlite3
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CUTOFF_DAYS = 60


def main():
    db = ROOT / "Efforts/osanwe-v2-overhaul/_work/factors.db"
    con = sqlite3.connect(str(db)) if db.is_file() else None
    cutoff = time.time() - CUTOFF_DAYS * 86400
    rows = []
    for f in sorted(glob.glob(str(ROOT / "wiki/entities/tickers/*.md"))):
        p = Path(f)
        mtime = os.path.getmtime(f)
        stale = mtime < cutoff
        if not stale:
            continue
        t = p.stem.upper()
        has_price = False
        if con:
            r = con.execute("SELECT MAX(date) FROM bars WHERE ticker=?", (t,)).fetchone()
            has_price = bool(r and r[0])
        # inbound references outside the entities dir + archive
        cnt = 0
        try:
            out = subprocess.run(
                ["git", "grep", "-l", f"[[{t}", "--", "wiki", "Calendar", "Atlas",
                 "Efforts", "docs"],
                cwd=str(ROOT), capture_output=True, text=True)
            files = [x for x in out.stdout.splitlines()
                     if "/entities/" not in x and "_archive" not in x]
            cnt = len(files)
        except Exception:
            pass
        verdict = "KEEP-WATCH" if (has_price or cnt >= 2) else "ARCHIVE-REVIEW"
        rows.append((t, verdict, has_price, cnt))

    tri = [r for r in rows if r[1] == "KEEP-WATCH"]
    arc = [r for r in rows if r[1] == "ARCHIVE-REVIEW"]
    lines = ["---",
             "aliases: []",
             "categories: [wiki]",
             "type: report",
             "status: active",
             f"created: {date.today().isoformat()}",
             f"updated: {date.today().isoformat()}",
             "tags: []",
             'related: []',
             "---", "",
             "# Stale entity triage (60d+ untouched)", "",
             f"{len(rows)} stale entities of the ticker set.",
             f"- KEEP-WATCH: {len(tri)} (store-priced or referenced)",
             f"- ARCHIVE-REVIEW: {len(arc)} (no price, <2 external refs) -- human call", ""]
    if tri:
        lines.append("## Keep-watch")
        lines += [f"- {t}" for t, _, _, _ in tri]
    if arc:
        lines.append("")
        lines.append("## Archive-review candidates")
        lines += [f"- {t} (refs={c})" for t, _, _, c in arc]

    out = ROOT / "wiki/maintenance/surveillance/entity-triage.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"-> {out.relative_to(ROOT)}")
    print(f"keep-watch={len(tri)} archive-review={len(arc)}")
    con.close()
    return 0


if __name__ == "__main__":
    import subprocess  # noqa: F401  (used inline)
    sys.exit(main())
