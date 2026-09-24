#!/usr/bin/env python3
"""ledger-query.py -- single-entry structured query over the atomized ledgers.

ADR-02 promised halved ledger-query cost; this is the delivery. One command
answers the common decision questions that previously took 2-3 hops (which
organ? which section? which column?):

  --overdue N        open EOD loops past escalation by >= N days (default 30)
  --ticker TICKER    all decisions/loops/insights mentioning a ticker
  --verdicts         recent analysis verdicts (from analyses dir listing)
  --since YYYY-MM-DD entries on/after date (sessions + decisions)
  --limit N          max rows printed (default 20)

Every invocation prints a HOPS: line (organ touches used) so retrieval cost is
self-measuring. Sources are the NODE dirs (fast) falling back to views.
"""

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def hops(n):
    print(f"HOPS: {n}")


def read(p):
    return p.read_text(encoding="utf-8", errors="replace")


def iter_nodes(d):
    if not d.is_dir():
        return
    for f in sorted(d.glob("*.md")):
        if f.name != "INDEX.md":
            yield f


def node_date(fname):
    """Extract YYYY-MM-DD from a sequence-prefixed node name (0001-2026-04-29-x)
    or a plain dated name. Returns None if absent."""
    m = re.search(r"(\d{4}-\d{2}-\d{2})", fname)
    return m.group(1) if m else None


def cmd_overdue(n_days, limit):
    """Open EOD rows past escalation. ONE touch: loop nodes.
    Exit 0 clean, 1 if any loops are overdue (alert semantics for cron)."""
    today = date.today()
    rows = []
    for f in iter_nodes(ROOT / "Calendar" / "decisions" / "loops"):
        text = read(f)
        m = re.search(r"^\|(.+)\|\s*$", text, re.M)
        if not m:
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        if len(cells) < 4:
            continue
        esc = cells[3] if len(cells) > 3 else ""
        status = cells[-2] if len(cells) > 4 else "?"
        if not re.match(r"\d{4}-\d{2}-\d{2}", esc):
            continue
        if status.lower() not in ("pending", "open", ""):
            continue
        try:
            days = (today - date.fromisoformat(esc)).days
        except ValueError:
            continue
        if days >= n_days:
            what = cells[1] if len(cells) > 1 else ""
            rows.append((days, cells[0], what[:110], f.stem))
    rows.sort(reverse=True)
    for days, rid, what, node in rows[:limit]:
        print(f"- [{rid}] {days}d past escalation -- {what} ([[{node}]])")
    print(f"({len(rows)} open loops >= {n_days}d overdue)")
    hops(1)
    return 1 if rows else 0


def cmd_ticker(ticker, limit):
    """Decisions + loops + insights mentioning ticker. THREE touches max."""
    pat = re.compile(r"\b" + re.escape(ticker.upper()) + r"\b")
    out = []
    d = ROOT / "Calendar" / "decisions" / "records"
    for f in iter_nodes(d):
        t = read(f)
        if pat.search(t):
            m = re.search(r"^### .+$", t, re.M)
            out.append(("decision", f.stem, (m.group(0)[4:] if m else f.stem)[:100]))
    l = ROOT / "Calendar" / "decisions" / "loops"
    for f in iter_nodes(l):
        t = read(f)
        if pat.search(t):
            row = next((ln for ln in t.splitlines() if ln.strip().startswith("|")), "")
            out.append(("loop", f.stem, row.strip("| ")[:100]))
    i = ROOT / "wiki" / "insights"
    for f in iter_nodes(i):
        t = read(f)
        if pat.search(t):
            row = next((ln for ln in t.splitlines() if ln.strip().startswith("|")), "")
            out.append(("insight", f.stem, row.strip("| ")[:100]))
    for kind, stem, snip in out[:limit]:
        print(f"- [{kind}] [[{stem}]] {snip}")
    print(f"({len(out)} nodes mention {ticker.upper()})")
    hops(3)
    return 0 if out else 2  # 2 = no matches (distinct from error)


def cmd_since(since, limit):
    n = 0
    for d_rel in ("sessions", "decisions/records"):
        d = ROOT / "Calendar" / d_rel
        for f in iter_nodes(d):
            ndate = node_date(f.name)
            if ndate and ndate >= since:
                title = f.stem
                title = re.sub(r"^\d{4}-", "", title)  # strip seq prefix
                print(f"- {ndate} [[{f.stem}]] {title[11:101]}")
                n += 1
                if n >= limit:
                    break
        if n >= limit:
            break
    hops(2)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--overdue", type=int, metavar="DAYS")
    ap.add_argument("--ticker", metavar="T")
    ap.add_argument("--since", metavar="YYYY-MM-DD")
    ap.add_argument("--verdicts", action="store_true")
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()

    if args.overdue is not None:
        sys.exit(cmd_overdue(args.overdue, args.limit))
    if args.ticker:
        sys.exit(cmd_ticker(args.ticker, args.limit))
    if args.since:
        sys.exit(cmd_since(args.since, args.limit))
    if args.verdicts:
        ad = ROOT / "wiki" / "investing" / "analyses"
        for f in sorted(ad.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)[:args.limit]:
            t = read(f)
            m = (re.search(r"^rating:\s*\"?([A-Za-z ]+)", t, re.M)
                 or re.search(r"\*\*Rating\*\*:?\s*([A-Z][A-Z ]{2,12})", t))
            d = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d")
            print(f"- {d} {f.stem[:40]:<42} {m.group(1).strip() if m else '?'}")
        hops(1)
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
