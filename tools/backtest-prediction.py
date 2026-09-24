#!/usr/bin/env python3
"""backtest-prediction.py -- retrospective calibration engine (OSANWE-V2 SOTA pass).

The operator loop: the model predicts on PAST dates where outcomes are KNOWN,
then we dissect where the calculation went wrong. Zero-lookahead by construction:

  1. RECONSTRUCT: for each analysis note in wiki/investing/analyses/, take the
     file AS OF its own commit date (git show <commit>:<path>) -- never the
     current edited version.
  2. EXTRACT: rating (BUY/HOLD/SELL family), confidence %, ticker, thesis line,
     and the factor signals the analysis cited (technical/fundamental/sentiment
     buckets from its frontmatter + headings).
  3. OUTCOME: fetch verifiable prices via yfinance for [t0, t0+horizon]; compute
     forward return, max drawdown within window, and whether the verdict's
     direction was right. Prices come ONLY from after t0.
  4. GRADE: emit a JSONL record per prediction compatible with score_ledger.py
     populations: {id, ticker, t0, horizon_days, verdict, confidence, fwd_ret,
     correct, mdd, factors}.

Usage:
  python tools/backtest-prediction.py --list
  python tools/backtest-prediction.py --run --ticker SNDK --horizon 21
  python tools/backtest-prediction.py --run --all --horizon 30 --out _work/calib.jsonl
"""

import argparse
import ast
from functools import lru_cache
import json
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSES = ROOT / "wiki" / "investing" / "analyses"

VERDICT_BULLISH = {"BUY", "ACCUMULATE", "STRONG BUY", "ADD"}
VERDICT_BEARISH = {"SELL", "STRONG SELL", "TRIM", "EXIT", "AVOID", "SHORT"}


def sh(*args):
    r = subprocess.run(list(args), cwd=str(ROOT), capture_output=True)
    return r.stdout.decode(errors="replace")


def analysis_commits():
    """First-commit date + path for every analysis file (its true t0)."""
    log = sh("git", "log", "--diff-filter=A", "--format=%h|%cs|%s",
             "--", "wiki/investing/analyses/")
    out = []
    seen = set()
    for line in log.splitlines():
        parts = line.split("|", 2)
        if len(parts) < 3:
            continue
        sha, d, subj = parts
        # find the path from the commit itself
        name = sh("git", "show", "--diff-filter=A", "--name-only", "--format=", sha,
                  "--", "wiki/investing/analyses/").strip().splitlines()
        for p in name:
            if "/analyses/" in p and p.endswith(".md") and p not in seen:
                seen.add(p)
                out.append({"sha": sha, "t0": d, "path": p, "subject": subj})
    return sorted(out, key=lambda x: x["t0"])


@lru_cache(maxsize=1)
def crypto_symbol_authority():
    """Read the existing public symbol map without importing its execution code."""
    tree = ast.parse((ROOT / "tools/verdict-backtest.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "CRYPTO_TICKERS" for t in node.targets):
            value = ast.literal_eval(node.value)
            if isinstance(value, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
                return value
    raise ValueError("existing crypto symbol authority unavailable")


def price_identity(ticker, text):
    """Same symbol is not sufficient to choose a crypto or listed-security feed."""
    mapping = crypto_symbol_authority()
    if ticker not in mapping:
        return {"price_symbol": ticker, "instrument_type": "listed-security",
                "symbol_authority": "analysis-ticker"}
    frontmatter = text.split("---", 2)[1] if text.startswith("---") and text.count("---") >= 2 else ""
    if re.search(r"(?:asset_class|asset_type):\s*(?:equity|etf)\b", frontmatter, re.I):
        return {"price_symbol": ticker, "instrument_type": "listed-security",
                "symbol_authority": "explicit-analysis-asset-type"}
    if re.search(r"(?:asset_class|asset_type):\s*crypto\b|store-of-value|ref-crypto-landscape|theme-beta", frontmatter, re.I):
        return {"price_symbol": mapping[ticker], "instrument_type": "crypto",
                "symbol_authority": "tools/verdict-backtest.py:CRYPTO_TICKERS+analysis-frontmatter"}
    return {"price_symbol": None, "instrument_type": "unresolved",
            "symbol_authority": "ambiguous-symbol-no-asset-evidence"}


def _factor_rx(*words):
    """Whole-word keyword matcher for the factor buckets.

    These were bare substring searches, which counted "EPS" inside "steps",
    "hype" inside "hyperscaler", "rates" inside "operates" and "Fed" inside
    "federal" -- a sentence citing no factor at all scored three buckets at
    0.333 each. The boundary is a LETTER boundary, not a regex word boundary:
    in Python regex a digit and `_` are word characters, so a word boundary
    would stop counting the vault's own field names -- `rsi14`, `fcf_yield`,
    `piotroski_f_score`, `dgs10_series` -- which is where many real factor
    mentions live. A plain plural is still allowed so "margins" and
    "buybacks" keep counting as they always did.
    """
    return re.compile(r"(?<![A-Za-z])(?:" + "|".join(words) + r")(?:s|es)?(?![A-Za-z])", re.I)


FACTOR_RX = {
    "technical": _factor_rx("RSI", "moving average", "MACD", "support",
                            "resistance", "200DMA", "VWAP", "drawdown", "vol"),
    "fundamental": _factor_rx("revenue", "earnings", "EPS", "margin", "guidance",
                              "Piotroski", "Altman", "FCF", "PEG", "gross margin"),
    "sentiment": _factor_rx("sentiment", "narrative", "momentum", "crowd",
                            "positioning", "hype"),
    "macro": _factor_rx("regime", "rates", "10Y", "DGS10", "dollar", "macro",
                        "Fed", "inflation", r"geopolit\w*", "tariff"),
    "insider_flow": _factor_rx("insider", "13F", "institutional", "buyback",
                               "short interest", "Tepper", "Polen"),
}


def parse_analysis_text(text, path=""):
    """Extract verdict fields from the AS-OF text (no current-file peeking).

    Two schema eras exist: modern analyses carry `rating:`/`confidence:` in
    frontmatter; April-era ones state confidence as 'Confidence Rating: NN%'
    and embed the verdict in prose. Ticker comes from the filename stem.
    """
    fm_rating = re.search(r"^rating:\s*\"?([A-Za-z /]+)\"?", text, re.M)
    fm_conf = re.search(r"^confidence:\s*\"?(\d{1,3})\s*(?:pct|%)?\"?", text, re.M)
    fm_ticker = re.search(r"^ticker:\s*\"?([A-Z.\-]{1,6})\"?", text, re.M)
    fm_thesis = re.search(r'^thesis_line:\s*"(.+?)"', text, re.S)

    # era-1 fallbacks
    prose_conf = re.search(r"Confidence Rating:\s*(\d{1,3})\s*pct", text)
    stem = Path(path).stem  # e.g. mu-analysis-2026-04-27 / mu-analysis
    m_tick = re.match(r"^([a-z]{2,5})-", stem, re.I)
    ticker = (fm_ticker.group(1).upper() if fm_ticker
              else (m_tick.group(1).upper() if m_tick else None))

    rating = (fm_rating.group(1).strip().upper() if fm_rating else None)
    if not rating:
        # prose verdict: '**Rating**: BUY -- ...' or 'Rating: HOLD'
        pm = re.search(r"\*\*Rating\*\*:?\s*([A-Z][A-Z ]{2,12})", text)
        if not pm:
            pm = re.search(r"^Rating:\s*([A-Z][A-Z ]{2,12})", text, re.M)
        rating = pm.group(1).strip() if pm else None

    conf = None
    for c in (fm_conf, prose_conf):
        if c:
            conf = int(c.group(1))
            break

    factors = {k: len(rx.findall(text)) for k, rx in FACTOR_RX.items()}
    total = sum(factors.values()) or 1

    return {
        "verdict": rating,
        "confidence": conf,
        "ticker": ticker,
        "thesis": (fm_thesis.group(1)[:220] if fm_thesis else None),
        "factors": {k: round(v / total, 3) for k, v in factors.items()},
        **price_identity(ticker, text),
    }


def outcome(ticker, t0, horizon_days, py=None):
    """Verifiable price outcome STRICTLY AFTER t0. Returns dict or None.

    Runs the yfinance fetch in a child interpreter that actually has it
    (repo toolchain /path/to/python/python.exe) when the current one lacks it --
    same pattern as fetch-prices.py consumers.
    """
    try:
        import yfinance as yf  # noqa: F401
        have = True
    except ImportError:
        have = False
    if not have:
        for cand in (r"/path/to/python\python.exe", "python3.14"):
            try:
                subprocess.run([cand, "-c", "import yfinance"], check=True,
                               capture_output=True)
                code = (
                    "import json,sys; sys.path.insert(0,r'%s');"
                    "from backtest_prediction_outcome import outcome_json;"
                    "print(outcome_json(%r,%r,%d))" % (str(ROOT / "tools"), ticker, t0, horizon_days)
                )
                r = subprocess.run([cand, "-c", code], capture_output=True, text=True,
                                   cwd=str(ROOT / "tools"))
                if r.returncode == 0 and r.stdout.strip():
                    return json.loads(r.stdout.strip().splitlines()[-1])
            except (subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError):
                continue
        return None
    return _outcome_direct(ticker, t0, horizon_days)


def _outcome_direct(ticker, t0, horizon_days):
    import yfinance as yf
    start = datetime.strptime(t0, "%Y-%m-%d")
    if not isinstance(horizon_days, int) or isinstance(horizon_days, bool) or horizon_days < 1:
        raise ValueError("horizon must be a positive trading-interval count")
    end = start + timedelta(days=int(horizon_days * 1.5) + 14)
    tk = yf.Ticker(ticker)
    # yfinance 0.2.x strptime-chokes on isoformat's T00:00:00; pass bare dates
    hist = tk.history(start=start.strftime("%Y-%m-%d"),
                      end=end.strftime("%Y-%m-%d"), auto_adjust=True)
    if hist is None or hist.empty or len(hist) < horizon_days + 1:
        return None
    closes = hist["Close"]
    entry = float(closes.iloc[0])
    window = closes.iloc[: horizon_days + 1]
    import math
    if any(not math.isfinite(float(value)) or float(value) <= 0 for value in window):
        raise ValueError("prices must be finite and positive")
    if not window.index.is_monotonic_increasing or window.index.has_duplicates:
        raise ValueError("duplicate or unordered price dates")
    exit_ = float(window.iloc[-1])
    peak = float(window.max())
    trough = float(window.min())
    fwd = (exit_ - entry) / entry
    mdd = (trough - peak) / peak if peak else 0.0
    return {"entry": round(entry, 2), "exit": round(exit_, 2),
            "fwd_ret_pct": round(fwd * 100, 2),
            "max_favorable_pct": round((peak - entry) / entry * 100, 2),
            "mdd_pct": round(mdd * 100, 2),
            "window_days": len(window) - 1,
            "entry_date": str(window.index[0].date()), "exit_date": str(window.index[-1].date()),
            "schema": "osanwe.direction-outcome/2", "evidence_status": "retrospective",
            "source_revision": "current-adjusted-bars", "intraday_analysis_availability": "unverified"}


def grade(verdict, fwd_ret_pct, threshold=2.0):
    v = (verdict or "").upper().strip()
    if any(k in v for k in VERDICT_BULLISH):
        want = "up"
    elif any(k in v for k in VERDICT_BEARISH):
        want = "down"
    else:
        want = "flat"
    if want == "up":
        correct = fwd_ret_pct >= threshold
    elif want == "down":
        correct = fwd_ret_pct <= -threshold
    else:
        correct = abs(fwd_ret_pct) < threshold
    return want, correct


def run(only_ticker, horizon, out_path):
    if out_path and Path(out_path).exists():
        raise ValueError("output exists; preserve historical grades and use a new --out path")
    commits = analysis_commits()
    rows = []
    skipped = 0
    for c in commits:
        if only_ticker and only_ticker.lower() not in c["path"].lower():
            continue
        asof = sh("git", "show", f"{c['sha']}:{c['path']}")
        meta = parse_analysis_text(asof, c["path"])
        if not meta["ticker"] or not meta["verdict"]:
            skipped += 1
            continue
        if meta["instrument_type"] != "listed-security":
            skipped += 1
            continue
        px = outcome(meta["price_symbol"], c["t0"], horizon)
        if not px:
            skipped += 1
            continue
        want, correct = grade(meta["verdict"], px["fwd_ret_pct"])
        rows.append({
            "id": f"{meta['ticker']}-{c['t0']}",
            "ticker": meta["ticker"], "t0": c["t0"],
            "commit": c["sha"], "horizon_days": horizon,
            "verdict": meta["verdict"], "direction_wanted": want,
            "confidence": meta["confidence"], "thesis": meta["thesis"],
            "factors": meta["factors"], **px,
            "correct": correct,
        })
    if out_path:
        with open(out_path, "x", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
    n = len(rows)
    if n:
        acc = sum(1 for r in rows if r["correct"]) / n
        hi = [r for r in rows if (r.get("confidence") or 0) >= 70]
        lo = [r for r in rows if (r.get("confidence") or 0) < 70]
        print(f"predictions graded: {n} (skipped {skipped})")
        print(f"direction accuracy @{horizon}d: {acc:.0%}")
        if hi:
            print(f"  high-conf (>=70): {sum(1 for r in hi if r['correct'])}/{len(hi)} "
                  f"= {sum(1 for r in hi if r['correct'])/len(hi):.0%}")
        if lo:
            print(f"  low-conf  (<70): {sum(1 for r in lo if r['correct'])}/{len(lo)} "
                  f"= {sum(1 for r in lo if r['correct'])/len(lo):.0%}")
        bull = [r for r in rows if r["direction_wanted"] == "up"]
        bear = [r for r in rows if r["direction_wanted"] == "down"]
        if bull:
            print(f"  bullish calls: {sum(1 for r in bull if r['correct'])}/{len(bull)} correct")
        if bear:
            print(f"  bearish calls: {sum(1 for r in bear if r['correct'])}/{len(bear)} correct")
        print(f"records -> {out_path or '(stdout suppressed; use --out)'}")
    else:
        print("no gradable predictions (check tickers/price availability)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--ticker")
    ap.add_argument("--horizon", type=int, default=21)
    ap.add_argument("--out", default="Efforts/osanwe-v2-overhaul/_work/calibration.jsonl")
    args = ap.parse_args()

    if args.list:
        for c in analysis_commits():
            print(f"{c['t0']}  {c['sha']}  {c['path']}")
        return 0
    if args.run:
        if not (args.all or args.ticker):
            print("--run needs --ticker X or --all")
            return 2
        return run(args.ticker, args.horizon, args.out)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
