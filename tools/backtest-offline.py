#!/usr/bin/env python3
"""backtest-offline.py -- P2 verification + offline grading from the factor store.

Two contracts:
  CROSS-CHECK: regrade the same predictions the network path graded and confirm
               IDENTICAL results (store vs live-fetch equivalence).
  OFFLINE: once ingested, this script performs zero network calls.

Grades v1-style (direction) AND P1 hold-bands, per horizon, reading bars from
the sqlite store with as_of windows (zero lookahead by query shape).
"""

import argparse
import json
import math
import sqlite3
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import importlib.util

_spec = importlib.util.spec_from_file_location("bp1", ROOT / "tools" / "backtest-prediction.py")
bp1 = importlib.util.module_from_spec(_spec)
sys.modules["bp1"] = bp1
_spec.loader.exec_module(bp1)

_spec2 = importlib.util.spec_from_file_location("bv2", ROOT / "tools" / "backtest-v2.py")
bv2 = importlib.util.module_from_spec(_spec2)
sys.modules["bv2"] = bv2
_spec2.loader.exec_module(bv2)


def store_window(con, ticker, t0, horizon):
    """Bars for [t0 .. t0+pad] with date>=t0. Pure SQL: no lookahead.

    WINDOW CONTRACT: fetch WIDE (horizon+21 calendar days) and slice by TRADING
    count in stats_from_series -- 22 trading bars can span >31 calendar days
    (holidays), so a tight calendar window silently truncates the horizon.
    Must stay equivalent to backtest-v2.fetch_series + window_stats slicing.
    """
    start = datetime.strptime(t0, "%Y-%m-%d").date()
    end = start + timedelta(days=int(horizon * 1.5) + 14)  # ~1.5x calendar coverage for holidays
    rows = con.execute(
        "SELECT date, close FROM bars WHERE ticker=? AND date>=? AND date<=? ORDER BY date",
        (ticker.upper(), start.isoformat(), end.isoformat())).fetchall()
    return [(r[0], r[1]) for r in rows]


def stats_from_series(series, horizon):
    if not isinstance(horizon, int) or isinstance(horizon, bool) or horizon < 1:
        raise ValueError("horizon must be a positive trading-interval count")
    w = series[: horizon + 1]
    # An immature outcome is not a smaller sample of the requested horizon.
    # Historical rows did not store endpoints, so they cannot prove maturity.
    if len(w) != horizon + 1:
        return None
    if any(w[i][0] >= w[i + 1][0] for i in range(len(w) - 1)):
        raise ValueError("duplicate or unordered price dates")
    if any(not math.isfinite(c) or c <= 0 for _, c in w):
        raise ValueError("prices must be finite and positive")
    entry = w[0][1]
    exit_ = w[-1][1]
    peak = max(c for _, c in w)
    trough = min(c for _, c in w)
    return {"entry": round(entry, 2), "exit": round(exit_, 2),
            "ret_pct": round((exit_ - entry) / entry * 100, 2),
            "mfe_pct": round((peak - entry) / entry * 100, 2),
            "mae_pct": round((trough - entry) / entry * 100, 2),
            "n_days": len(w) - 1, "entry_date": w[0][0], "exit_date": w[-1][0]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "Efforts/osanwe-v2-overhaul/_work/factors.db"))
    ap.add_argument("--horizons", default="5,21,63")
    ap.add_argument("--ticker")
    ap.add_argument("--out", default=str(ROOT / "Efforts/osanwe-v2-overhaul/_work/calibration-offline.jsonl"))
    ap.add_argument("--cross-check", default=str(ROOT / "Efforts/osanwe-v2-overhaul/_work/calibration-v2.jsonl"),
                    help="prior network-graded JSONL to verify identical grades against")
    args = ap.parse_args()
    if Path(args.out).exists():
        ap.error("output exists; preserve historical grades and use a new --out path")

    con = sqlite3.connect(args.db)
    horizons = [int(h) for h in args.horizons.split(",")]
    commits = bp1.analysis_commits()
    rows = []
    unavailable = []
    for c in commits:
        if args.ticker and args.ticker.lower() not in c["path"].lower():
            continue
        asof = bp1.sh("git", "show", f"{c['sha']}:{c['path']}")
        meta = bp1.parse_analysis_text(asof, c["path"])
        if not meta["ticker"] or not meta["verdict"]:
            continue
        if meta["instrument_type"] != "listed-security":
            unavailable.extend({"id": f"{meta['ticker']}-{c['t0']}-h{h}",
                "reason": "crypto-calendar-not-supported" if meta["instrument_type"] == "crypto" else "ambiguous-instrument",
                "price_symbol": meta["price_symbol"], "symbol_authority": meta["symbol_authority"]} for h in horizons)
            continue
        want, _ = bp1.grade(meta["verdict"], 0.0)
        target, stop = bv2.parse_levels(asof)
        band = bv2.parse_hold_band(asof)
        spec = bv2.specificity(asof)
        for h in horizons:
            stk = stats_from_series(store_window(con, meta["ticker"], c["t0"], h), h)
            ben = stats_from_series(store_window(con, "SPY", c["t0"], h), h)
            if not stk or not ben:
                unavailable.append({"id": f"{meta['ticker']}-{c['t0']}-h{h}", "reason": "incomplete-horizon"})
                continue
            if (stk["entry_date"], stk["exit_date"]) != (ben["entry_date"], ben["exit_date"]):
                unavailable.append({"id": f"{meta['ticker']}-{c['t0']}-h{h}", "reason": "benchmark-calendar-mismatch"})
                continue
            excess = round(stk["ret_pct"] - ben["ret_pct"], 2)
            v = meta["verdict"].upper().strip()
            if any(k in v for k in bp1.VERDICT_BULLISH):
                beats = excess > 0
            elif any(k in v for k in bp1.VERDICT_BEARISH):
                beats = excess < 0
            else:
                beats = abs(stk["ret_pct"]) <= abs(ben["ret_pct"]) + 1.0
            band_correct = None
            if band and want == "flat":
                band_correct = stk["ret_pct"] <= band[0] and stk["ret_pct"] >= band[1]
            rows.append({"schema": "osanwe.calibration-outcome/2",
                         "id": f"{meta['ticker']}-{c['t0']}-h{h}",
                         "ticker": meta["ticker"], "t0": c["t0"], "horizon": h,
                         "verdict": meta["verdict"], "confidence": meta["confidence"],
                         "direction": want, "stk_ret": stk["ret_pct"],
                         "spy_ret": ben["ret_pct"], "excess_pct": excess,
                         "beats_spy": beats,
                         "hold_band": list(band) if band else None,
                         "band_correct": band_correct,
                         "specificity": spec, "src": "factor-store",
                         "n_days": stk["n_days"], "entry_date": stk["entry_date"], "exit_date": stk["exit_date"],
                         "benchmark_entry_date": ben["entry_date"], "benchmark_exit_date": ben["exit_date"],
                         "evidence_status": "retrospective", "source_revision": "current-adjusted-bars",
                         "intraday_analysis_availability": "unverified",
                         "instrument_type": meta["instrument_type"], "price_symbol": meta["price_symbol"]})
    with open(args.out, "x", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    with Path(args.out + ".coverage.json").open("x", encoding="utf-8") as handle:
        json.dump({"schema": "osanwe.calibration-coverage/1", "scope": "listed-security-trading-intervals",
                   "produced": len(rows), "unavailable": unavailable,
                   "attempted_obligations": len(rows) + len(unavailable)}, handle, indent=2)

    # cross-check vs network path on matching ids
    cc_problems = []
    checked = 0
    p = Path(args.cross_check)
    if p.is_file():
        net = {}
        with open(p, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                net[r["id"]] = r
        for r in rows:
            n = net.get(r["id"])
            if not n:
                continue
            checked += 1
            if any(n.get(k) != r[k] for k in ("n_days", "entry_date", "exit_date", "benchmark_entry_date", "benchmark_exit_date")):
                cc_problems.append(f"{r['id']}: legacy or incompatible horizon evidence")
            elif abs(n["stk_ret"] - r["stk_ret"]) > 0.01 or n["beats_spy"] != r["beats_spy"] or abs(n["spy_ret"] - r["spy_ret"]) > 0.01:
                cc_problems.append(f"{r['id']}: net {n['stk_ret']} vs store {r['stk_ret']}")
        missing_ids = set(net) ^ {r["id"] for r in rows}
        if missing_ids:
            cc_problems.append(f"cohort differs by {len(missing_ids)} IDs; omitted outputs are not passes")
    else:
        cc_problems.append("cross-check reference unavailable")

    print(f"offline rows: {len(rows)} -> {args.out}")
    print(f"cross-check vs network path: {checked} compared, "
          f"{'ALL MATCH' if not cc_problems else str(len(cc_problems)) + ' MISMATCH'}")
    for pr in cc_problems[:5]:
        print("  ", pr)
    for h in horizons:
        rs = [r for r in rows if r["horizon"] == h]
        banded = [r for r in rs if r.get("band_correct") is not None]
        line = f"h{h}: n={len(rs)} beat-SPY {sum(1 for r in rs if r['beats_spy'])/len(rs):.0%}" if rs else f"h{h}: no data"
        if banded:
            line += f" | banded-HOLDs {sum(1 for r in banded if r['band_correct'])}/{len(banded)} in-band"
        print(line)
    con.close()
    return 1 if cc_problems else 0


if __name__ == "__main__":
    sys.exit(main())
