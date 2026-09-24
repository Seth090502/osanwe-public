#!/usr/bin/env python3
"""entity-surveillance.py -- GAP-4: grade trigger blocks across ALL ticker entities.

108 entities carry structured `trigger:` frontmatter blocks that were never
checked mechanically. This tool:
  1. parses each entity's triggers + current price from the factor store
  2. evaluates proximity to each trigger (distance %)
  3. emits wiki/maintenance/surveillance/entity-triggers-<date>.md ranked by
     proximity -- the standing watchlist with measured distances

Trigger grammar accepted (from observed corpus):
  - "reduce if close < $X" / "trim above $Y" style lines with $ levels
  - plain "$X" references (nearest-level semantics)
"""

import argparse
import re
import sqlite3
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def last_price(con, ticker):
    r = con.execute("SELECT close FROM bars WHERE ticker=? ORDER BY date DESC LIMIT 1",
                    (ticker.upper(),)).fetchone()
    return r[0] if r else None


def parse_triggers(text):
    """Return [(direction, level, kind)] from entity-note level references.

    Verified corpus grammar (scanned 108 entities): LIMIT orders, entry/
    re-entry/accumulate zones, MA50/MA200 anchors, kill-stops. Frontmatter
    trigger: blocks are rare in entities (they live in analyses).
    """
    out = []
    for m in re.finditer(r"LIMIT\s+\$(\d{2,4}(?:\.\d+)?)", text, re.I):
        out.append(("limit-buy", float(m.group(1)), "LIMIT"))
    for m in re.finditer(
            r"(?:re-entry|entry|accumulate)[^\n]{0,30}zone[^\n]{0,30}\$(\d{2,4})", text, re.I):
        out.append(("near-zone", float(m.group(1)), "zone"))
    for m in re.finditer(r"(?:kill[- ]?stop|stop loss)[^\n]{0,25}\$(\d{2,4})", text, re.I):
        out.append(("below", float(m.group(1)), "kill-stop"))
    for m in re.finditer(r"MA(50|200)\s+\$?(\d{2,4}(?:\.\d+)?)", text):
        out.append((f"MA{m.group(1)}-anchor", float(m.group(2)), f"MA{m.group(1)}"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "Efforts/osanwe-v2-overhaul/_work/factors.db"))
    ap.add_argument("--proximity", type=float, default=10.0,
                    help="report triggers within this pct of last price")
    ap.add_argument("--out")
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    ed = ROOT / "wiki/entities/tickers"
    watch = []
    checked = parsed = 0
    for f in sorted(ed.glob("*.md")):
        t = f.stem.upper()
        price = last_price(con, t)
        if not price:
            continue
        checked += 1
        text = f.read_text(encoding="utf-8", errors="replace")
        triggers = parse_triggers(text)
        if not triggers:
            continue
        parsed += 1
        seen_lvls = set()
        for direction, level, kind in triggers:
            if level in seen_lvls:
                continue
            seen_lvls.add(level)
            dist = (level - price) / price * 100
            near = abs(dist) <= args.proximity
            if near:
                watch.append({"ticker": t, "price": round(price, 2),
                              "direction": f"{direction} ({kind})", "level": level,
                              "dist_pct": round(dist, 1)})

    watch.sort(key=lambda w: abs(w["dist_pct"]))
    lines = ["---",
             "aliases: []",
             "categories: [wiki]",
             "type: report",
             "status: active",
             f"created: {date.today().isoformat()}",
             f"updated: {date.today().isoformat()}",
             "tags: []",
             'related: ["[[hot]]"]',
             "---", "",
             "# Entity trigger surveillance (GENERATED)", "",
             f"Checked {checked} entities with store prices; {parsed} carry parseable "
             f"trigger levels; {len(watch)} triggers within {args.proximity:.0f}% "
             "of last price.", "",
             "| ticker | last | trigger | level | distance |", "|---|---|---|---|---|"]
    for w in watch[:40]:
        lines.append(f"| {w['ticker']} | {w['price']} | {w['direction']} | "
                     f"{w['level']} | {w['dist_pct']:+.1f}% |")

    out = Path(args.out) if args.out else (
        ROOT / "wiki/maintenance/surveillance" /
        f"entity-triggers-{date.today().isoformat()}.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"-> {out.relative_to(ROOT)}")
    print(f"checked {checked}, parsed {parsed}, within {args.proximity:.0f}%: {len(watch)}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
