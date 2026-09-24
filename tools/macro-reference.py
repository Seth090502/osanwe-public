#!/usr/bin/env python3
"""macro-reference.py -- fill macro-regime-tables.md from the factor store.

Computes, per FRED series: latest value + as-of, 90d/1y-ago values, direction,
90d average and percentile-in-window for vol/credit. Writes the mechanical
regime read. Everything between the MACRO-TABLES markers is regenerated; the
rest of the file is preserved.
"""

import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "wiki/investing/benchmarks/macro-regime-tables.md"
SERIES = {
    "DGS10": "10Y Treasury", "T10Y3M": "10Y-3M spread", "T10Y2Y": "10Y-2Y spread",
    "BAMLH0A0HYM2": "HY OAS", "VIXCLS": "VIX", "FEDFUNDS": "Fed funds",
    "UNRATE": "Unemployment", "CPIAUCSL": "CPI index", "DFII10": "10Y TIPS real",
}


def series(con, sid):
    return con.execute("SELECT date,value FROM factors WHERE factor=? ORDER BY date",
                       (sid,)).fetchall()


def latest(rows):
    return rows[-1] if rows else (None, None)


def ago(rows, days):
    cutoff = (datetime.strptime(latest(rows)[0], "%Y-%m-%d").date()
              - __import__("datetime").timedelta(days=days)).isoformat()
    prior = [r for r in rows if r[0] <= cutoff]
    return prior[-1] if prior else (None, None)


def pct_rank(rows, value):
    vals = [v for _, v in rows if v is not None]
    if not vals or value is None:
        return None
    below = sum(1 for v in vals if v <= value)
    return round(below / len(vals) * 100)


def main():
    con = sqlite3.connect(str(ROOT / "Efforts/osanwe-v2-overhaul/_work/factors.db"))
    curve = []
    volcredit = []
    labor = []

    # curve table
    dgs = series(con, "DGS10")
    t3 = series(con, "T10Y3M")
    l_d, l_v = latest(dgs)
    p90 = ago(dgs, 90)
    p365 = ago(dgs, 365)
    dirn = "rising" if (l_v is not None and p90[1] is not None and l_v > p90[1]) else "falling"
    curve.append(f"| DGS10 | {l_v} | {l_d} | {p90[1]} | {p365[1]} | {dirn} |")
    for sid in ("T10Y3M", "T10Y2Y"):
        s = series(con, sid)
        ld, lv = latest(s)
        inverted = "INVERTED" if (lv is not None and lv < 0) else "positive"
        curve.append(f"| {SERIES[sid]} ({sid}) | {lv} | {ld} | -- | -- | {inverted} |")

    # vol & credit
    for sid in ("VIXCLS", "BAMLH0A0HYM2"):
        s = series(con, sid)
        ld, lv = latest(s)
        vals = [v for _, v in s[-180:] if v is not None]
        avg90 = round(sum(vals) / len(vals), 2) if vals else None
        rank = pct_rank(s, lv)
        volcredit.append(f"| {SERIES[sid]} ({sid}) | {lv} | {ld} | {avg90} | {rank}th pct |")

    # labor & inflation
    un = series(con, "UNRATE")
    lu, uu = latest(un)
    pu = ago(un, 180)
    trend_u = "rising" if (uu is not None and pu[1] is not None and uu > pu[1]) else \
              "falling" if (uu is not None and pu[1] is not None) else "--"
    labor.append(f"| UNRATE | {uu} | {lu} | {trend_u} (6m) |")
    cpi = series(con, "CPIAUCSL")
    if len(cpi) >= 13:
        latest_idx = cpi[-1][1]
        yoy_base = cpi[-13][1]
        yoy = round((latest_idx / yoy_base - 1) * 100, 1) if yoy_base else None
        labor.append(f"| CPI YoY | {yoy}% | {cpi[-1][0]} | computed from index |")
    ff = series(con, "FEDFUNDS")
    lf, vf = latest(ff)
    labor.append(f"| FEDFUNDS | {vf} | {lf} | policy rate |")

    # mechanical regime read
    vixrow = latest(series(con, "VIXCLS"))
    oasrow = latest(series(con, "BAMLH0A0HYM2"))
    reads = []
    if vixrow[1] is not None:
        reads.append(f"vol {'ELEVATED' if vixrow[1] >= 20 else 'contained'} (VIX {vixrow[1]})")
    if oasrow[1] is not None:
        reads.append(f"credit {'STRESSED' if oasrow[1] >= 4.5 else 'orderly'} (HY OAS {oasrow[1]})")
    t3l = latest(series(con, "T10Y3M"))
    if t3l[1] is not None:
        reads.append(f"curve {'INVERTED' if t3l[1] < 0 else 'positively sloped'} ({t3l[1]})")

    block = f"""
## Yield curve state (DGS10 / T10Y3M / T10Y2Y)

| series | latest | as-of | 90d ago | 1y ago | direction |
|---|---|---|---|---|---|
{chr(10).join(curve)}

## Volatility & credit (VIXCLS / BAMLH0A0HYM2)

| series | latest | as-of | 90d avg | percentile-in-window |
|---|---|---|---|---|
{chr(10).join(volcredit)}

## Labor & inflation (UNRATE / CPIAUCSL yoy / FEDFUNDS)

| series | latest | as-of | trend |
|---|---|---|---|
{chr(10).join(labor)}

## Regime read (mechanical, from the tables above)

{"; ".join(reads)}.
"""
    t = TARGET.read_text(encoding="utf-8")
    a = t.find("<!-- MACRO-TABLES:BEGIN -->") + len("<!-- MACRO-TABLES:BEGIN -->")
    b = t.find("<!-- MACRO-TABLES:END -->")
    t = t[:a] + "\n" + block + "\n" + t[b:]
    t = t.replace("updated: 2026-08-23", f"updated: {date.today().isoformat()}")
    TARGET.write_text(t, encoding="utf-8", newline="\n")
    print(f"-> {TARGET.relative_to(ROOT)} updated")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
