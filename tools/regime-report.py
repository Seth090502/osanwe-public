#!/usr/bin/env python3
"""regime-report.py -- P3: stratify calibration by market regime.

Regime features per call date, computed FROM THE STORE (no network):
  trend:  SPY close vs its 50-bar moving average (above/below)
  vol:    21-bar realized vol of SPY (high >= 20% annualized / low)
  drawdown: SPY drawdown from 60-bar peak (>5% = correction)

Joins the offline calibration JSONL and prints/stores per-regime beat-SPY rates.
The kernel's DGS10 halt is rate-regime; this is the EQUITY-regime complement
(VIX join lands when fred snapshots are imported into the store).
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def spy_series(con):
    rows = con.execute("SELECT date, close FROM bars WHERE ticker='SPY' ORDER BY date").fetchall()
    return [(r[0], r[1]) for r in rows]


def regime_at(spy, as_of, con=None):
    """Classify regime using only bars <= as_of (zero lookahead).

    VIX (FRED VIXCLS, ingested in factors table) takes precedence when
    available as-of; realized-vol proxy is the fallback.
    """
    past = [(d, c) for d, c in spy if d <= as_of]
    if len(past) < 60:
        return {"trend": "unknown", "vol": "unknown", "drawdown": "unknown"}
    closes = [c for _, c in past]
    last = closes[-1]
    ma50 = sum(closes[-50:]) / 50
    rets = [closes[i] / closes[i - 1] - 1 for i in range(len(closes) - 20, len(closes))]
    mean = sum(rets) / len(rets)
    var = sum((x - mean) ** 2 for x in rets) / len(rets)
    vol_ann = (var ** 0.5) * (252 ** 0.5) * 100
    peak60 = max(closes[-60:])
    dd = (last - peak60) / peak60 * 100

    vix = None
    vix_src = "proxy"
    if con is not None:
        r = con.execute(
            "SELECT date, value FROM factors WHERE factor='VIXCLS' AND date<=? "
            "ORDER BY date DESC LIMIT 1", (as_of,)).fetchone()
        # stale guard: VIX older than 7 calendar days falls back to proxy
        if r and (datetime.strptime(as_of, "%Y-%m-%d").date() -
                  datetime.strptime(r[0], "%Y-%m-%d").date()).days <= 7:
            vix = float(r[1])
            vix_src = "VIXCLS"
    vol_class = ("high" if (vix if vix is not None else vol_ann) >= 20 else "low")

    return {
        "trend": "up" if last > ma50 else "down",
        "vol": vol_class,
        "vol_pct": round(vix, 1) if vix is not None else round(vol_ann, 1),
        "vol_source": vix_src,
        "drawdown": "correction" if dd <= -5 else "normal",
        "dd_pct": round(dd, 1),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", default=str(ROOT / "Efforts/osanwe-v2-overhaul/_work/calibration-offline.jsonl"))
    ap.add_argument("--db", default=str(ROOT / "Efforts/osanwe-v2-overhaul/_work/factors.db"))
    ap.add_argument("--horizon", type=int, default=21)
    ap.add_argument("--out", default=str(ROOT / "wiki/maintenance/calibration/regime-stratification.md"))
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    spy = spy_series(con)
    rows = [json.loads(l) for l in open(args.jsonl, encoding="utf-8")
            if l.strip() and json.loads(l).get("horizon") == args.horizon]
    if not rows:
        print("no rows at that horizon")
        return 2

    strata = {}
    for r in rows:
        reg = regime_at(spy, r["t0"], con)
        key = f"trend={reg['trend']} | vol={reg['vol']}"
        r["regime"] = reg
        strata.setdefault(key, []).append(r)

    lines = ["---",
             "aliases: []",
             "categories: [wiki]",
             "type: report",
             "status: active",
             "created: 2026-08-23",
             "updated: 2026-08-23",
             "tags: [topic/meta]",
             'related: ["[[calibration-2026-08-23]]"]',
             "---", "",
             f"# Regime-stratified calibration ({args.horizon}d horizon)", "",
             f"n={len(rows)} calls; regimes computed from stored SPY bars, "
             "strictly as-of each call date (no lookahead).", "",
             "| regime | n | beat-SPY | median excess |", "|---|---|---|---|"]
    for key in sorted(strata):
        rs = strata[key]
        n = len(rs)
        win = sum(1 for r in rs if r["beats_spy"])
        med = sorted(r["excess_pct"] for r in rs)[n // 2] if n else 0
        lines.append(f"| {key} | {n} | {win/n:.0%} | {med:+.1f}% |")

    # directional split within regime (the interesting cell: BUYs in down-trend)
    lines += ["", "## Direction x trend (the cell that matters)", "",
              "| direction | trend | n | beat-SPY |", "|---|---|---|---|"]
    cross = {}
    for r in rows:
        k = (r["direction"], r.get("regime", {}).get("trend", "?"))
        cross.setdefault(k, []).append(r)
    for k in sorted(cross):
        rs = cross[k]
        lines.append(f"| {k[0]} | {k[1]} | {len(rs)} | "
                     f"{sum(1 for r in rs if r['beats_spy'])/len(rs):.0%} |")

    out = Path(args.out)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"-> {out.relative_to(ROOT)}")
    for line in lines[lines.index("| regime | n | beat-SPY | median excess |")+2:]:
        if line.startswith("|"):
            print(line)
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
