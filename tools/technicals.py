#!/usr/bin/env python3
"""technicals.py -- deterministic technical/risk panel from Robinhood get_equity_historicals JSON.

Usage:
  python technicals.py --file bars.json --ticker AAPL [--benchmark SPY]
  python technicals.py --file bars.json --matrix TICKER1,TICKER2,TICKER3

Input: a file containing the raw get_equity_historicals tool result. Accepts the
full envelope {"data": {"results": [...]}}, {"results": [...]}, or a bare list of
result objects. Bars with "interpolated": true are excluded from all analytics.
Request ~420+ calendar days of daily bars for the full panel (SMA200, 12-1
momentum, 52-week range need ~252 trading sessions); shorter windows degrade
gracefully -- missing indicators come back null with an "insufficient_history" note.

Output: one JSON object on stdout. Numbers only; no advice. stderr carries warnings.

Provenance: script:technicals (Osanwe vault). Ported verbatim from the 2026-07-10
donor skill modulo ASCII transliteration (Pattern 22) + the additive "5_session"
return field (prov source for the GATE-F move_5d_pct marker). Self-tests:
tools/test-technicals.py (authored in-vault; the donor shipped none).
"""
import argparse, json, math, sys
from datetime import datetime

TRADING_DAYS = 252

def load_results(path):
    with open(path) as f:
        raw = json.load(f)
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        if "results" in raw:
            return raw["results"]
        if "data" in raw and isinstance(raw["data"], dict) and "results" in raw["data"]:
            return raw["data"]["results"]
    raise ValueError("Unrecognized JSON shape: expected get_equity_historicals output")

def extract_series(results, symbol):
    for r in results:
        if r.get("symbol", "").upper() == symbol.upper():
            bars = [b for b in r.get("bars", []) if not b.get("interpolated")]
            bars.sort(key=lambda b: b["begins_at"])
            out = []
            for b in bars:
                out.append({
                    "date": b["begins_at"][:10],
                    "close": float(b["close_price"]),
                    "high": float(b.get("high_price", b["close_price"])),
                    "low": float(b.get("low_price", b["close_price"])),
                    "volume": float(b.get("volume", 0) or 0),
                })
            return out
    return None

def sma(closes, n):
    return sum(closes[-n:]) / n if len(closes) >= n else None

def rsi_wilder(closes, n=14):
    if len(closes) < n + 1:
        return None
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]
    avg_g = sum(gains[:n]) / n
    avg_l = sum(losses[:n]) / n
    for i in range(n, len(deltas)):
        avg_g = (avg_g * (n - 1) + gains[i]) / n
        avg_l = (avg_l * (n - 1) + losses[i]) / n
    if avg_l == 0:
        return 100.0
    rs = avg_g / avg_l
    return 100.0 - 100.0 / (1.0 + rs)

def log_returns(closes):
    return [math.log(closes[i] / closes[i-1]) for i in range(1, len(closes))]

def ann_vol(closes, window=None):
    rs = log_returns(closes if window is None else closes[-(window+1):])
    if len(rs) < 20:
        return None
    mean = sum(rs) / len(rs)
    var = sum((r - mean) ** 2 for r in rs) / (len(rs) - 1)
    return math.sqrt(var) * math.sqrt(TRADING_DAYS)

def max_drawdown(series):
    peak, peak_d = series[0]["close"], series[0]["date"]
    mdd, mdd_peak_d, mdd_trough_d = 0.0, series[0]["date"], series[0]["date"]
    for p in series:
        if p["close"] > peak:
            peak, peak_d = p["close"], p["date"]
        dd = p["close"] / peak - 1.0
        if dd < mdd:
            mdd, mdd_peak_d, mdd_trough_d = dd, peak_d, p["date"]
    return {"max_drawdown_pct": round(mdd * 100, 2), "peak_date": mdd_peak_d, "trough_date": mdd_trough_d}

def trailing_return(closes, sessions):
    if len(closes) < sessions + 1:
        return None
    return closes[-1] / closes[-1 - sessions] - 1.0

def align(a, b):
    """Align two series on shared dates; return paired simple daily returns."""
    da = {p["date"]: p["close"] for p in a}
    db = {p["date"]: p["close"] for p in b}
    dates = sorted(set(da) & set(db))
    ra, rb = [], []
    for i in range(1, len(dates)):
        ra.append(da[dates[i]] / da[dates[i-1]] - 1.0)
        rb.append(db[dates[i]] / db[dates[i-1]] - 1.0)
    return ra, rb

def beta_corr(ra, rb):
    n = len(ra)
    if n < 40:
        return None, None
    ma, mb = sum(ra)/n, sum(rb)/n
    cov = sum((ra[i]-ma)*(rb[i]-mb) for i in range(n)) / (n-1)
    va = sum((r-ma)**2 for r in ra) / (n-1)
    vb = sum((r-mb)**2 for r in rb) / (n-1)
    if vb == 0 or va == 0:
        return None, None
    return cov/vb, cov/math.sqrt(va*vb)

def pct(x, nd=2):
    return None if x is None else round(x * 100, nd)

def corr_matrix(results, symbols):
    """Pairwise daily-return correlations among symbols present in the file."""
    series = {}
    for sym in symbols:
        s = extract_series(results, sym)
        if s and len(s) >= 41:
            series[sym.upper()] = s
    syms = sorted(series)
    out = {"symbols": syms, "pairs": [], "missing": [s.upper() for s in symbols if s.upper() not in series]}
    for i in range(len(syms)):
        for j in range(i + 1, len(syms)):
            ra, rb = align(series[syms[i]], series[syms[j]])
            _, corr = beta_corr(ra, rb)
            out["pairs"].append({"a": syms[i], "b": syms[j],
                                 "corr": round(corr, 2) if corr is not None else None,
                                 "flag_gt_0.7": bool(corr is not None and corr > 0.7)})
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--ticker", default=None)
    ap.add_argument("--benchmark", default=None)
    ap.add_argument("--matrix", default=None, help="comma-separated symbols for pairwise correlation matrix")
    args = ap.parse_args()

    results = load_results(args.file)
    if args.matrix:
        print(json.dumps(corr_matrix(results, args.matrix.split(",")), indent=1)); return
    if not args.ticker:
        print(json.dumps({"error": "provide --ticker or --matrix"})); sys.exit(1)
    s = extract_series(results, args.ticker)
    if not s:
        print(json.dumps({"error": f"ticker {args.ticker} not found in file"})); sys.exit(1)
    closes = [p["close"] for p in s]
    notes = []
    # 12-1 momentum reads closes[-253], so it needs 253 sessions, not 252: at
    # exactly 252 the field is null, and the note has to say why.
    if len(closes) < TRADING_DAYS + 1:
        notes.append(f"insufficient_history: {len(closes)} sessions (<253) -- SMA200/12-1 momentum/52wk fields may be null")

    sma50, sma200 = sma(closes, 50), sma(closes, 200)
    cross = None
    if sma50 is not None and sma200 is not None:
        cross = {"state": "golden (50>200)" if sma50 > sma200 else "death (50<200)", "crossed_within_30_sessions": False}
        for k in range(1, min(31, len(closes) - 199)):
            c = closes[:-k]
            s5, s2 = sma(c, 50), sma(c, 200)
            if s5 is None or s2 is None:
                break
            if (s5 > s2) != (sma50 > sma200):
                cross["crossed_within_30_sessions"] = True
                break

    lb252 = s[-TRADING_DAYS:] if len(s) >= TRADING_DAYS else s
    hi52 = max(p["high"] for p in lb252)
    lo52 = min(p["low"] for p in lb252)

    mom_12_1 = None
    if len(closes) >= TRADING_DAYS + 1:
        # 12-1 momentum spans t-252 -> t-21 (231 sessions): the close 252 sessions
        # back is closes[-253], not closes[-252] (which is t-251).
        mom_12_1 = closes[-22] / closes[-(TRADING_DAYS + 1)] - 1.0

    out = {
        "ticker": args.ticker.upper(),
        "as_of": s[-1]["date"],
        "sessions": len(closes),
        "last_close": round(closes[-1], 2),
        "sma50": round(sma50, 2) if sma50 else None,
        "sma200": round(sma200, 2) if sma200 else None,
        "price_vs_sma50_pct": pct(closes[-1]/sma50 - 1) if sma50 else None,
        "price_vs_sma200_pct": pct(closes[-1]/sma200 - 1) if sma200 else None,
        "cross": cross,
        "rsi14": round(rsi_wilder(closes), 1) if rsi_wilder(closes) is not None else None,
        "returns_pct": {
            "5_session": pct(trailing_return(closes, 5)),  # GATE-F move_5d_pct prov source (vault addition)
            "10_session": pct(trailing_return(closes, 10)),   # GATE-F chase input (donor)
            "1_month_21s": pct(trailing_return(closes, 21)),
            "3_month_63s": pct(trailing_return(closes, 63)),
            "6_month_126s": pct(trailing_return(closes, 126)),
            "12_month_252s": pct(trailing_return(closes, 252)),
            "momentum_12_1": pct(mom_12_1),
        },
        "vol_annualized_pct": {"trailing_63s": pct(ann_vol(closes, 63)), "full_window": pct(ann_vol(closes))},
        "drawdown": max_drawdown(s),
        "52wk": {"high": round(hi52, 2), "low": round(lo52, 2),
                 "off_high_pct": pct(closes[-1]/hi52 - 1), "off_low_pct": pct(closes[-1]/lo52 - 1)},
        "volume_ratio_20d_vs_90d": None,
        "benchmark": None,
        "notes": notes,
    }
    vols = [p["volume"] for p in s if p["volume"] > 0]
    if len(vols) >= 90:
        out["volume_ratio_20d_vs_90d"] = round((sum(vols[-20:])/20) / (sum(vols[-90:])/90), 2)

    if args.benchmark:
        b = extract_series(results, args.benchmark)
        if not b:
            notes.append(f"benchmark {args.benchmark} not found in file -- beta/correlation/RS skipped")
        else:
            ra, rb = align(s, b)
            beta, corr = beta_corr(ra, rb)
            bcloses = [p["close"] for p in b]
            rs6 = None
            tr, br = trailing_return(closes, 126), trailing_return(bcloses, 126)
            if tr is not None and br is not None:
                rs6 = tr - br
            out["benchmark"] = {
                "symbol": args.benchmark.upper(),
                "beta": round(beta, 2) if beta is not None else None,
                "daily_return_correlation": round(corr, 2) if corr is not None else None,
                "overlap_sessions": len(ra) + 1,
                "relative_strength_6mo_pct": pct(rs6),
            }

    print(json.dumps(out, indent=1))

if __name__ == "__main__":
    main()
