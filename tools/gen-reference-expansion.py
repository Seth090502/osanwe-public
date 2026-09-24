#!/usr/bin/env python3
"""gen-reference-expansion.py -- expand the /invest reference layer with
VERIFIABLE, store-derived quantitative sections (roadmap: reference expansion).

For each ticker with bars in the factor store, generate/refresh a compact
DATA-ANNEX appended to (or created beside) the benchmark profile:

  wiki/investing/benchmarks/<ticker>-data-annex.md

Contents (all computed from the point-in-time store; every number traceable):
  - return distribution: best/worst day, % days up, 1y monthly returns table
  - drawdown episodes >10% (start/trough/recover dates + depth)
  - volatility term structure: 20d vs 60d realized vol (regime signal)
  - volume-less note + provenance block

Also emits wiki/investing/benchmarks/REFERENCE-INDEX.md listing every annex.

These annexes are ADDITIVE to ref-sector-benchmaps-style prose refs (which carry
qualitative context) -- they put verifiable numbers underneath them.
"""

import argparse
import json
import sqlite3
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "wiki/investing/benchmarks"


def load_series(con, ticker):
    rows = con.execute("SELECT date, close FROM bars WHERE ticker=? ORDER BY date",
                       (ticker,)).fetchall()
    dates = [r[0] for r in rows]
    closes = [r[1] for r in rows]
    return dates, closes


def ret_stats(closes):
    rets = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
    if not rets:
        return {}
    up = sum(1 for r in rets if r > 0)
    return {"n_days": len(rets), "pct_up": round(up / len(rets) * 100, 1),
            "best_day_pct": round(max(rets) * 100, 2),
            "worst_day_pct": round(min(rets) * 100, 2)}


def realized_vol(closes, window):
    if len(closes) < window + 1:
        return None
    rets = [closes[-window + i] / closes[-window + i - 1] - 1
            for i in range(1, window)]
    mean = sum(rets) / len(rets)
    var = sum((x - mean) ** 2 for x in rets) / (len(rets) - 1)
    return round((var ** 0.5) * (252 ** 0.5) * 100, 1)


def drawdown_episodes(dates, closes, threshold=10.0):
    """Episodes where price fell >= threshold% peak-to-trough, with recovery."""
    eps = []
    peak = closes[0]
    peak_d = dates[0]
    trough = closes[0]
    trough_d = dates[0]
    in_dd = False
    for d, c in zip(dates[1:], closes[1:]):
        if c > peak:
            if in_dd and (trough / peak - 1) * 100 <= -threshold:
                eps.append({"peak_date": peak_d, "trough_date": trough_d,
                            "depth_pct": round((trough / peak - 1) * 100, 1),
                            "recovered_date": d})
            in_dd = False
            peak, peak_d = c, d
            trough, trough_d = c, d
        else:
            if c < trough:
                trough, trough_d = c, d
                in_dd = True
    if in_dd and (trough / peak - 1) * 100 <= -threshold:
        eps.append({"peak_date": peak_d, "trough_date": trough_d,
                    "depth_pct": round((trough / peak - 1) * 100, 1),
                    "recovered_date": None})
    return eps


def monthly_returns(dates, closes, months=12):
    """Last N month-end returns."""
    by_month = {}
    for d, c in zip(dates, closes):
        by_month[d[:7]] = c  # last close seen in month
    keys = sorted(by_month)[-months - 1:]
    out = []
    for i in range(1, len(keys)):
        prev, cur = by_month[keys[i - 1]], by_month[keys[i]]
        out.append((keys[i], round((cur / prev - 1) * 100, 1)))
    return out


def fmtpct(x):
    return f"{x:+.1f}%" if x is not None else "--"


def annex(con, ticker, years_note="2y"):
    dates, closes = load_series(con, ticker)
    if len(closes) < 60:
        return None
    rs = ret_stats(closes)
    v20 = realized_vol(closes, 20)
    v60 = realized_vol(closes, 60)
    vol_regime = ("elevated" if (v20 and v60 and v20 > v60 * 1.25)
                  else ("compressing" if (v20 and v60 and v20 < v60 * 0.75)
                        else "stable"))
    eps = drawdown_episodes(dates, closes)
    months = monthly_returns(dates, closes)

    lines = ["---",
             "aliases: []",
             "categories: [sources]",
             "type: reference",
             "status: active",
             f"created: {date.today().isoformat()}",
             f"updated: {date.today().isoformat()}",
             f"tags: []",
             'related: []',
             "---", "",
             f"# Data annex: {ticker.upper()} ({years_note} of daily closes)",
             "",
             f"GENERATED from the point-in-time factor store "
             f"({len(closes)} bars, {dates[0]}..{dates[-1]}). Every number is "
             "recomputable from stored bars; regenerate weekly via "
             "tools/gen-reference-expansion.py.", "",
             "## Return distribution", "",
             f"- trading days: {rs.get('n_days')}",
             f"- percent of days UP: {rs.get('pct_up')}%",
             f"- best day: {fmtpct(rs.get('best_day_pct'))}",
             f"- worst day: {fmtpct(rs.get('worst_day_pct'))}", "",
             "## Volatility term structure", "",
             f"- realized vol 20d: {v20}% | 60d: {v60}% | regime: **{vol_regime}**", "",
             "## Drawdown episodes (>10%)", ""]
    if eps:
        lines += ["| peak | trough | depth | recovered |", "|---|---|---|---|"]
        for e in eps:
            lines.append(f"| {e['peak_date']} | {e['trough_date']} | "
                         f"{e['depth_pct']}% | {e['recovered_date'] or 'ONGOING'} |")
    else:
        lines.append("(no >=10% drawdown episodes in window)")
    lines += ["", "## Monthly returns (last 12)", "",
              "| month | return |", "|---|---|"]
    for m, r in months:
        lines.append(f"| {m} | {r:+.1f}% |")
    lines += ["", "*Additive data layer -- qualitative context lives in "
              "[[ref-sector-benchmarks]] and thesis refs.*"]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "Efforts/osanwe-v2-overhaul/_work/factors.db"))
    ap.add_argument("--ticker")
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    tickers = [r[0] for r in con.execute(
        "SELECT DISTINCT ticker FROM bars WHERE ticker != 'MACRO' ORDER BY ticker")]
    if args.ticker:
        tickers = [t for t in tickers if t.upper() == args.ticker.upper()]

    OUTDIR.mkdir(parents=True, exist_ok=True)
    written = []
    index_rows = []
    for t in tickers:
        text = annex(con, t)
        if not text:
            continue
        p = OUTDIR / f"{t.lower()}-data-annex.md"
        p.write_text(text, encoding="utf-8", newline="\n")
        written.append(p.name)
        # one-line summary for the index
        import re as _re
        vol = _re.search(r"realized vol 20d: (\S+)%", text)
        dd = _re.search(r"\| \d{4}-\d{2}-\d{2} \| (\d{4}-\d{2}-\d{2}) \| (-?\d+(?:\.\d+)?)%", text)
        index_rows.append(f"| [[{p.stem}]] | {t.upper()} | vol20 {vol.group(1)}%"
                          f"{'' if not dd else f' | maxDD {dd.group(2)}%'} |")

    # REFERENCE-INDEX.md
    idx = ["---",
           "aliases: [reference-index]",
           "categories: [sources]",
           "type: index",
           "status: active",
           f"created: {date.today().isoformat()}",
           f"updated: {date.today().isoformat()}",
           "tags: []",
           'related: ["[[ref-sector-benchmarks]]"]',
           "---", "",
           "# Reference data annexes -- index (GENERATED)", "",
           "One data-annex per instrument with bars in the factor store.",
           "Regenerated by tools/gen-reference-expansion.py.", "",
           "| annex | instrument | vol snapshot |", "|---|---|---|"]
    idx += index_rows
    p = OUTDIR / "REFERENCE-INDEX.md"
    p.write_text("\n".join(idx) + "\n", encoding="utf-8", newline="\n")
    print(f"annexes written: {len(written)}; index -> REFERENCE-INDEX.md")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
