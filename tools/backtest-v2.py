#!/usr/bin/env python3
"""backtest-v2 additions -- benchmark-relative grading + target/stop tracking.

Methodology upgrade over backtest-prediction.py v1 (kept separate for A/B):
  - BENCHMARK RELATIVE: a call only "wins" if it beats SPY over the SAME window.
    Reason: in a +8% tape, HOLD->+4% was a good call, not a miss; in a -10% tape,
    HOLD->+4% was excellent. Absolute grading conflated market beta with skill.
  - TARGET/STOP TRACKING: modern analyses state explicit target + stop prices;
    we record which hit first within the window (the analysis's OWN falsifiers,
    not our threshold).
  - MULTI-HORIZON: 5/21/63 trading-day windows in one sweep; calibration claims
    must be horizon-scoped.
  - SPECIFICITY: whether the analysis committed to numbers (falsifiable) or
    prose (unfalsifiable) -- itself a quality metric per the mission bar.

Usage:
  python tools/backtest-v2.py --run --all --horizons 5,21,63 \
      --out Efforts/osanwe-v2-overhaul/_work/calibration-v2.jsonl
"""

import argparse
import json
import math
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(ROOT / "tools"))
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "bp1", ROOT / "tools" / "backtest-prediction.py")
bp1 = importlib.util.module_from_spec(_spec)
sys.modules["bp1"] = bp1
_spec.loader.exec_module(bp1)


def fetch_series(ticker, t0, days, py_ok):
    """Close series for [t0, t0+days calendar]. Returns list[(date, close)]."""
    start = datetime.strptime(t0, "%Y-%m-%d")
    # end must be INCLUSIVE-safe: yfinance end is exclusive; +14 covers holidays
    end = start + timedelta(days=int(days * 1.5) + 14)
    code = (
        "import json;"
        "import yfinance as yf;"
        f"h=yf.Ticker({ticker!r}).history(start={start.strftime('%Y-%m-%d')!r},"
        f"end={end.strftime('%Y-%m-%d')!r},auto_adjust=True);"
        "print(json.dumps([[str(i.date()),float(c)] for i,c in h['Close'].items()]))"
    )
    r = subprocess.run([py_ok, "-c", code], capture_output=True, text=True, timeout=90)
    if r.returncode != 0:
        return []
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return []


def window_stats(series, horizon_days):
    """Stats over the first `horizon_days` TRADING days of the series."""
    w = series[: horizon_days + 1]
    if not isinstance(horizon_days, int) or isinstance(horizon_days, bool) or horizon_days < 1:
        raise ValueError("horizon must be a positive trading-interval count")
    if len(w) != horizon_days + 1:
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


def parse_hold_band(text):
    """Extract hold_band frontmatter: "[12.5, -8.0] pct ..." -> (12.5, -8.0).
    OSANWE-V2 SOTA P1: makes HOLD calls falsifiable (in-band = correct)."""
    m = re.search(r'^hold_band:\s*"\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)', text, re.M)
    return (float(m.group(1)), float(m.group(2))) if m else None


def parse_levels(text):
    """Extract stated target/stop prices from AS-OF text.

    v2 (SOTA pass): handles BOTH frontmatter keys AND the prose patterns the
    corpus actually uses: '$350 kill-stop', '$350 stop is...', 'conservative
    $480 model FV', '$537 consensus avg -> 6.60' (target context), 'price_target:'
    keys. Verified against tsm-analysis-2026-07-30 ($480 FV / $350 stop).
    """
    tgt = re.search(r"(?:price_target|target_price|target)\s*:\s*\$?(\d{2,4}(?:\.\d+)?)", text)
    stop = re.search(r"(?:kill_stop|stop_loss|stop)\s*:\s*\$?(\d{2,4}(?:\.\d+)?)", text)

    # kernel-era indented rr_inputs block (illustrative values):
    #   rr_inputs:\n    entry: 100.00\n    stop: 80.00\n    target: 140.00
    if tgt is None:
        m = re.search(r"^\s+target:\s*\"?(\d{2,5}(?:\.\d+)?)\"?\s*$", text, re.M)
        if m:
            class _M:
                def __init__(self, v):
                    self.v = v

                def group(self, i):
                    return str(self.v)
            tgt = _M(m.group(1))
    if stop is None:
        m = re.search(r"^\s+(?:kill_)?stop:\s*\"?(\d{2,5}(?:\.\d+)?)\"?\s*$", text, re.M)
        if m:
            class _M:
                def __init__(self, v):
                    self.v = v

                def group(self, i):
                    return str(self.v)
            stop = _M(m.group(1))

    if tgt is None:
        # PRIORITY 1: kernel-era structured worksheet rows
        #   "target_model 480" / "target: ... $520 consensus-avg | target $480 model FV"
        m = re.search(r"target_model[:\s]+(\d{2,4}(?:\.\d+)?)", text)
        if m:
            class _M:
                def __init__(self, v):
                    self.v = v

                def group(self, i):
                    return str(self.v)
            tgt = _M(float(m.group(1)))
    if tgt is None:
        # PRIORITY 2 (legacy prose): the MIN-rule line
        #   "$520 consensus-avg | target $480 model FV" -> take the model FV
        m = re.search(r"target\s+\$(\d{2,4}(?:\.\d+)?)\s+model FV", text)
        if not m:
            m = re.search(r"\$\d{2,4}(?:\.\d+)?[^\n]{0,20}?target\s+\$(\d{2,4}(?:\.\d+)?)\s+model FV", text)
        if not m:
            # plain 'conservative $480 model FV' / '$480 model FV'
            m = re.search(r"\$(\d{2,4}(?:\.\d+)?)\s+(?:model FV|fair value)", text)
        if m:
            class _M:
                def __init__(self, v):
                    self.v = v

                def group(self, i):
                    return str(self.v)
            tgt = _M(float(m.group(1)))
    if stop is None:
        m = re.search(r"\$(\d{2,4}(?:\.\d+)?)\s+(?:kill-stop|kill stop|stop\b|no-averaging-down floor)", text, re.I)
        if not m:
            m = re.search(r"\b(?:kill-stop|stop)\b[^\n]{0,25}?\$?(\d{3}(?:\.\d+)?)", text, re.I)
        stop = m

    # sanity: stop must be below any target (a mixup inverts grading)
    if tgt and stop and float(stop.group(1)) >= float(tgt.group(1)):
        stop, tgt = tgt, stop
    return (float(tgt.group(1)) if tgt else None,
            float(stop.group(1)) if stop else None)


def which_hit_first(series, entry, target, stop):
    """Walk the window; return 'target'|'stop'|None (chronological first touch)."""
    for d, c in series[1:]:
        if target is not None and c >= target:
            return "target", d
        if stop is not None and c <= stop:
            return "stop", d
    return None, None


def specificity(text):
    """0-3: how falsifiable is the as-of reasoning?"""
    s = 0
    if re.search(r"\$\d{2,4}(?:\.\d+)?\s*(?:target|FV|fair value)", text, re.I):
        s += 1
    if re.search(r"(?:kill-stop|stop loss|invalidation).*?\$\d{2,4}", text, re.I | re.S):
        s += 1
    if re.search(r"\d{2,4}(?:\.\d+)?\s*(?:pct|%)", text):
        s += 1
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--ticker")
    ap.add_argument("--horizons", default="5,21,63")
    ap.add_argument("--out", default="Efforts/osanwe-v2-overhaul/_work/calibration-v2.jsonl")
    args = ap.parse_args()
    if not args.run:
        ap.print_help()
        return 0
    if Path(args.out).exists():
        ap.error("output exists; preserve historical grades and use a new --out path")

    # pick an interpreter that has yfinance
    py_ok = None
    for cand in (sys.executable, r"/path/to/python\python.exe"):
        try:
            subprocess.run([cand, "-c", "import yfinance"], check=True,
                           capture_output=True)
            py_ok = cand
            break
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
    if not py_ok:
        print("no interpreter with yfinance found")
        return 2

    horizons = [int(h) for h in args.horizons.split(",")]
    commits = bp1.analysis_commits()
    out_rows = []
    unavailable = []
    series_cache = {}

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
        want, _ = bp1.grade(meta["verdict"], 0.0)  # direction class only
        target, stop = parse_levels(asof)
        hold_band = parse_hold_band(asof)
        spec = specificity(asof)

        key = (meta["ticker"], c["t0"])
        if key not in series_cache:
            series_cache[key] = fetch_series(meta["ticker"], c["t0"],
                                             max(horizons), py_ok)
        bench_key = ("SPY", c["t0"])
        if bench_key not in series_cache:
            series_cache[bench_key] = fetch_series("SPY", c["t0"], max(horizons), py_ok)
        stk = series_cache[key]
        ben = series_cache[bench_key]

        for h in horizons:
            ws = window_stats(stk, h)
            wb = window_stats(ben, h)
            if not ws or not wb:
                unavailable.append({"id": f"{meta['ticker']}-{c['t0']}-h{h}", "reason": "incomplete-horizon"})
                continue
            if (ws["entry_date"], ws["exit_date"]) != (wb["entry_date"], wb["exit_date"]):
                unavailable.append({"id": f"{meta['ticker']}-{c['t0']}-h{h}", "reason": "benchmark-calendar-mismatch"})
                continue
            excess = round(ws["ret_pct"] - wb["ret_pct"], 2)
            v = meta["verdict"].upper().strip()
            if any(k in v for k in bp1.VERDICT_BULLISH):
                beats = excess > 0
                tstat = ("target" if target and ws["exit"] >= target else
                         ("stop" if stop and ws["exit"] <= stop else None))
            elif any(k in v for k in bp1.VERDICT_BEARISH):
                beats = excess < 0
                tstat = None
            else:
                beats = abs(ws["ret_pct"]) <= abs(wb["ret_pct"]) + 1.0
                tstat = None
            hit, hit_date = (which_hit_first(stk[:h + 1], ws["entry"], target, stop)
                             if (target or stop) else (None, None))
            # P1 falsifiable-HOLD grading: in-band through horizon = correct
            band_correct = None
            if hold_band and want == "flat":
                up, dn = hold_band
                band_correct = (ws["ret_pct"] <= up) and (ws["ret_pct"] >= dn)
            out_rows.append({
                "schema": "osanwe.calibration-outcome/2",
                "id": f"{meta['ticker']}-{c['t0']}-h{h}",
                "ticker": meta["ticker"], "t0": c["t0"], "horizon": h,
                "verdict": meta["verdict"], "confidence": meta["confidence"],
                "direction": want, "stk_ret": ws["ret_pct"], "spy_ret": wb["ret_pct"],
                "excess_pct": excess, "beats_spy": beats,
                "hold_band": list(hold_band) if hold_band else None,
                "band_correct": band_correct,
                "mfe_pct": ws["mfe_pct"], "mae_pct": ws["mae_pct"],
                "target": target, "stop": stop,
                "level_hit_first": hit, "level_hit_date": hit_date,
                "specificity": spec,
                "n_days": ws["n_days"], "entry_date": ws["entry_date"], "exit_date": ws["exit_date"],
                "benchmark_entry_date": wb["entry_date"], "benchmark_exit_date": wb["exit_date"],
                "evidence_status": "retrospective", "source_revision": "current-adjusted-bars",
                "intraday_analysis_availability": "unverified",
                "instrument_type": meta["instrument_type"], "price_symbol": meta["price_symbol"],
            })

    with open(args.out, "x", encoding="utf-8", newline="\n") as f:
        for r in out_rows:
            f.write(json.dumps(r) + "\n")
    with Path(args.out + ".coverage.json").open("x", encoding="utf-8") as handle:
        json.dump({"schema": "osanwe.calibration-coverage/1", "scope": "listed-security-trading-intervals",
                   "produced": len(out_rows), "unavailable": unavailable,
                   "attempted_obligations": len(out_rows) + len(unavailable)}, handle, indent=2)
    if args.ticker:
        # partial run: never clobber the corpus evidence file
        print(f"NOTE: --ticker run; consider --out with a distinct name "
              f"(wrote {len(out_rows)} rows to {args.out})")

    print(f"v2 rows: {len(out_rows)} -> {args.out}")
    for h in horizons:
        rs = [r for r in out_rows if r["horizon"] == h]
        if not rs:
            continue
        acc_abs = sum(1 for r in rs if r["beats_spy"])
        hi = [r for r in rs if (r.get("confidence") or 0) >= 70]
        print(f"h{h}: n={len(rs)} beat-SPY rate={acc_abs/len(rs):.0%} "
              f"(high-conf {sum(1 for r in hi if r['beats_spy'])}/{len(hi)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
