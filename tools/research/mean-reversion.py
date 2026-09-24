#!/usr/bin/env python
"""Mean-reversion (RSI-based) alpha experiment vs baselines.

Question: does short-term mean reversion (buy oversold, sell overbought)
generate alpha AFTER execution costs?

Universe : factors.db 'bars' table -- liquid instruments only (>1000 daily
           bars), excluding crypto ('-USD') and ADRs.
Signal   : RSI(14) on daily closes.
           LONG when RSI < entry_threshold (default 30; variant 20).
           EXIT when RSI > exit_level (default 50) OR after max_hold days
           (default 10; variant 5).
Execution: signal at close t -> entry at close t+1 (one-bar lag, no
           look-ahead). Exits evaluated at close t' >= t+2 and filled at
           that close. Re-entry requires RSI to re-arm above the entry
           threshold first (no continuous rolling holds through downtrends).
Costs    : round-trip bp from tools/execution-cost-model.py at a fixed
           assumed order size (default $250k), deducted from every trade.
Baselines: 1) buy-and-hold SPY   2) random entry, same exit rules & costs
           3) buy-and-hold the same tickers (equal-weighted average).

Metrics  : CAGR, Sharpe, win rate, avg return/trade (net), t-stat of
           per-trade returns vs zero, max drawdown.
Regimes  : trades split by SPY 20-day realized volatility above/below its
           full-sample median (realized-vol proxy for VIX; no VIX series in
           the vault and no network access allowed).
Segments : ETFs vs individual stocks (per execution-cost-model classes).

Usage: python tools/research/mean-reversion.py [--db PATH] [--order-usd N]
ASCII output only. No network access. sqlite3 used directly.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sqlite3
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# tools/execution-cost-model.py has a hyphenated filename -> load via importlib.
import importlib.util  # noqa: E402

_ecm_path = os.path.join(VAULT, "tools", "execution-cost-model.py")
_spec = importlib.util.spec_from_file_location("execution_cost_model", _ecm_path)
ecm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ecm)


def estimate_trade_cost(tk, size):
    return ecm.estimate_trade_cost(tk, size)

DEFAULT_DB = os.path.join(
    VAULT, "Efforts", "osanwe-v2-overhaul", "_work", "factors.db")

# ADRs to exclude (foreign-domiciled lines; classification source:
# tools/execution-cost-model.py TICKER_CLASS + obvious OTC ADR suffixes).
ADR_TICKERS = {"TSM", "ASML", "ABBNY", "ATEYY", "ASMIY"}

MIN_BARS = 1000
RSI_PERIOD = 14

# ETFs in the universe (sector / broad / thematic funds). Everything else
# that passes the liquidity filter is treated as an individual stock.
ETF_TICKERS = {
    "QQQ", "SPY", "VOO", "VGT", "SMH", "SOXX", "IAU",
    "ITA", "PPA", "XAR", "XLE", "XLF", "XLI", "XLP",
    "XLRE", "XLU", "XLV", "XLY", "VDE", "DTCR",
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_universe(db_path: str):
    """Return {ticker: [close,...]} for liquid non-crypto, non-ADR names."""
    con = sqlite3.connect("file:%s?mode=ro" % db_path.replace("\\", "/"), uri=True)
    rows = con.execute(
        "SELECT ticker, date, close FROM bars ORDER BY ticker, date").fetchall()
    con.close()
    data = {}
    for tk, _date, close in rows:
        if "-USD" in tk.upper():
            continue
        if tk.upper() in ADR_TICKERS:
            continue
        data.setdefault(tk.upper(), []).append(float(close))
    return {tk: c for tk, c in data.items() if len(c) > MIN_BARS}


# ---------------------------------------------------------------------------
# Indicators
# ---------------------------------------------------------------------------

def rsi_series(closes, period=RSI_PERIOD):
    """Wilder-smoothed RSI. Output aligned to input; first `period` slots None."""
    n = len(closes)
    out = [None] * n
    if n <= period:
        return out
    gains, losses = 0.0, 0.0
    for i in range(1, period + 1):
        d = closes[i] - closes[i - 1]
        gains += max(d, 0.0)
        losses += max(-d, 0.0)
    ag, al = gains / period, losses / period
    out[period] = 100.0 if al == 0 else 100.0 - 100.0 / (1.0 + ag / al)
    for i in range(period + 1, n):
        d = closes[i] - closes[i - 1]
        ag = (ag * (period - 1) + max(d, 0.0)) / period
        al = (al * (period - 1) + max(-d, 0.0)) / period
        out[i] = 100.0 if al == 0 else 100.0 - 100.0 / (1.0 + ag / al)
    return out


def realized_vol(closes, window=20):
    """Annualized realized vol series (trailing std of daily log returns)."""
    rets = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
    out = [None] * len(closes)
    for i in range(window, len(rets) + 1):
        chunk = rets[i - window:i]
        mu = sum(chunk) / window
        var = sum((r - mu) ** 2 for r in chunk) / (window - 1)
        out[i] = math.sqrt(var) * math.sqrt(252.0)
    return out


# ---------------------------------------------------------------------------
# Trade simulation
# ---------------------------------------------------------------------------

def simulate_ticker(closes, rsis, entry_thr, exit_lvl, max_hold, cost_rt,
                    rng=None, forced_entry_idx=None):
    """Run one instrument. Returns list of trades:
    (entry_i, exit_i, gross_ret, net_ret, holding_days).

    With rng set, entry days are random (same expected frequency as the
    signal would produce) but exit rules/costs are identical.
    """
    n = len(closes)
    trades = []
    armed = True          # re-entry requires RSI back above entry_thr
    i = 0
    signal_days = None
    if rng is not None:
        # Random entries: sample days where RSI exists, matching the count
        # the deterministic signal produces on this ticker.
        sig_count = sum(1 for t in range(RSI_PERIOD, n - 1) if rsis[t] is not None
                        and rsis[t] < entry_thr)
        pool = list(range(RSI_PERIOD + 1, n - 2))
        rng.shuffle(pool)
        signal_days = sorted(pool[:sig_count])

    while i < n - 1:
        if forced_entry_idx is not None:
            enter_sig = i if i == forced_entry_idx else None
        elif signal_days is not None:
            enter_sig = i if i in signal_days else None
        else:
            ok = (rsis[i] is not None and armed and rsis[i] < entry_thr)
            enter_sig = i if ok else None
        if enter_sig is None:
            if rsis[i] is not None and rsis[i] >= entry_thr:
                armed = True
            i += 1
            continue
        entry = i + 1                      # fill at next close
        if entry >= n:
            break
        exit_i = None
        j = entry + 1                      # earliest managed exit day
        while j < n:
            r = rsis[j]
            if r is not None and r > exit_lvl:
                exit_i = j
                break
            if (j - i) >= max_hold:
                exit_i = j
                break
            j += 1
        if exit_i is None:
            exit_i = n - 1                 # force-close at end of data
        px_in, px_out = closes[entry], closes[exit_i]
        gross = px_out / px_in - 1.0
        net = gross - cost_rt / 10000.0
        trades.append((entry, exit_i, gross, net, exit_i - i))
        i = exit_i                         # resume scanning after exit
        armed = False
    return trades


# ---------------------------------------------------------------------------
# Portfolio aggregation and metrics
# ---------------------------------------------------------------------------

def daily_returns(all_trades, lengths):
    """Equal-weight across concurrently open positions; 0 when all flat.

    all_trades: {ticker: [(entry_i, exit_i, gross, net, hold), ...]}
    lengths:    {ticker: n_bars}
    """
    nmax = max(lengths.values())
    daily = []
    for t in range(nmax):
        act = []
        for tk, trs in all_trades.items():
            if t >= lengths[tk]:
                continue
            for (e, x, g, nt, h) in trs:
                if e < t <= x:
                    seg = None
                    if e < t:
                        # daily return inside the trade, approximated from
                        # closes is not stored here; use linear slice of the
                        # trade's total net return instead (documented).
                        seg = (1.0 + nt) ** (1.0 / max(h, 1)) - 1.0
                    if seg is not None:
                        act.append(seg)
                    break
        daily.append(sum(act) / len(act) if act else 0.0)
    return daily


def perf(daily):
    """CAGR, Sharpe, maxDD from a daily simple-return series."""
    if not daily:
        return dict(cagr=0.0, sharpe=0.0, maxdd=0.0)
    eq, peak, maxdd = 1.0, 1.0, 0.0
    for r in daily:
        eq *= (1.0 + r)
        peak = max(peak, eq)
        maxdd = min(maxdd, eq / peak - 1.0)
    years = len(daily) / 252.0
    cagr = eq ** (1.0 / years) - 1.0 if years > 0 and eq > 0 else -1.0
    mu = sum(daily) / len(daily)
    var = sum((r - mu) ** 2 for r in daily) / max(len(daily) - 1, 1)
    sd = math.sqrt(var)
    sharpe = (mu / sd) * math.sqrt(252.0) if sd > 0 else 0.0
    return dict(cagr=cagr, sharpe=sharpe, maxdd=maxdd)


def trade_stats(trades):
    """win rate, avg net return/trade, t-stat vs zero."""
    if not trades:
        return dict(n=0, win=0.0, avg=0.0, t=0.0)
    nets = [t[3] for t in trades]
    n = len(nets)
    wins = sum(1 for x in nets if x > 0)
    mu = sum(nets) / n
    var = sum((x - mu) ** 2 for x in nets) / max(n - 1, 1)
    sd = math.sqrt(var)
    tstat = mu / (sd / math.sqrt(n)) if sd > 0 and n > 1 else 0.0
    return dict(n=n, win=wins / n, avg=mu, t=tstat)


def bh_daily(closes):
    return [closes[i] / closes[i - 1] - 1.0 for i in range(1, len(closes))]


# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------

def run_variant(data, spy_closes, spy_rv, entry_thr, exit_lvl, max_hold,
                order_usd, seed=42):
    costs = {}
    for tk in data:
        costs[tk] = estimate_trade_cost(tk, order_usd)["round_trip_bp"]

    det, rnd = {}, {}
    rng = random.Random(seed)
    for tk, closes in sorted(data.items()):
        rsis = rsi_series(closes)
        det[tk] = simulate_ticker(closes, rsis, entry_thr, exit_lvl,
                                  max_hold, costs[tk])
        rnd[tk] = simulate_ticker(closes, rsis, entry_thr, exit_lvl,
                                  max_hold, costs[tk],
                                  rng=random.Random(seed + hash(tk) % 10**6))

    lengths = {tk: len(c) for tk, c in data.items()}
    res = {}
    res["signal"] = dict(perf(daily_returns(det, lengths)),
                         **trade_stats(sum(det.values(), [])))
    res["random"] = dict(perf(daily_returns(rnd, lengths)),
                         **trade_stats(sum(rnd.values(), [])))

    # Buy-and-hold the same tickers: equal-weight average of per-name BH.
    bh_matrix = [bh_daily(c) for c in data.values()]
    L = min(len(r) for r in bh_matrix)
    ew = [sum(r[-L:] for r in []) ] if False else None
    ew = []
    for i in range(L):
        ew.append(sum(r[i + (len(bh_daily(c)) - L)] for r, c in
                      zip(bh_matrix, data.values())) / len(bh_matrix))
    res["bh_same"] = perf(ew)

    # Regime split on SIGNAL trades: SPY realized vol above/below median.
    med = sorted(v for v in spy_rv if v is not None)[len(spy_rv) // 2]
    hi, lo = [], []
    spy_dates = list(range(len(spy_closes)))  # bar indices align by position
    for tk, trs in det.items():
        for (e, x, g, nt, h) in trs:
            off = len(data[tk]) - len(spy_closes)
            idx = e + off
            v = spy_rv[idx] if 0 <= idx < len(spy_rv) else None
            if v is None:
                continue
            (hi if v > med else lo).append(nt)
    res["regimes"] = {
        "hi_vol": trade_stats([(0, 0, 0, x, 0) for x in hi]),
        "lo_vol": trade_stats([(0, 0, 0, x, 0) for x in lo]),
    }

    # Segment split: ETFs vs individual stocks.
    etf, stk = [], []
    for tk, trs in det.items():
        (etf if tk in ETF_TICKERS else stk).extend(nt for (_, _, _, nt, _) in trs)
    res["segments"] = {
        "etf": trade_stats([(0, 0, 0, x, 0) for x in etf]),
        "stock": trade_stats([(0, 0, 0, x, 0) for x in stk]),
    }
    res["avg_cost_rt_bp"] = sum(costs.values()) / len(costs)
    res["n_universe"] = len(data)
    return res


def fmt_pct(x):
    return "%+.2f%%" % (100.0 * x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--order-usd", type=float, default=250_000)
    args = ap.parse_args()

    data = load_universe(args.db)
    if "SPY" not in data:
        raise SystemExit("SPY missing from universe")
    spy = data["SPY"]
    spy_rv = realized_vol(spy)

    variants = [
        ("base: RSI<30 enter, >50 exit, 10d max", 30, 50, 10),
        ("deep: RSI<20 enter, >50 exit, 10d max", 20, 50, 10),
        ("fast: RSI<30 enter, >50 exit, 5d max", 30, 50, 5),
        ("deep+fast: RSI<20 enter, >50 exit, 5d max", 20, 50, 5),
    ]
    print("universe: %d liquid names (>1000 bars, no crypto/ADR)" % len(data))
    print("order size: $%.0f | sample: 2021-08-24 .. 2026-08-24 (~1255 bars)"
          % args.order_usd)
    print()

    results = {"order_usd": args.order_usd, "variants": {}}
    for name, thr, xlvl, mh in variants:
        r = run_variant(data, spy, spy_rv, thr, xlvl, mh, args.order_usd)
        results["variants"][name] = r
        bh_spy = perf(bh_daily(spy))
        print("=" * 78)
        print("VARIANT:", name)
        print("  avg round-trip cost: %.1f bp | universe: %d"
              % (r["avg_cost_rt_bp"], r["n_universe"]))
        for label in ("signal", "random"):
            s = r[label]
            print("  %-7s CAGR %8s  Sharpe %5.2f  win %5.1f%%  avg/trade %9s  "
                  "t %5.2f  maxDD %7s  n %d"
                  % (label, fmt_pct(s["cagr"]), s["sharpe"],
                     100 * s["win"], fmt_pct(s["avg"]), s["t"],
                     fmt_pct(s["maxdd"]), s["n"]))
        b = r["bh_same"]
        print("  bh-same CAGR %8s  Sharpe %5.2f  maxDD %7s"
              % (fmt_pct(b["cagr"]), b["sharpe"], fmt_pct(b["maxdd"])))
        print("  bh-SPY  CAGR %8s  Sharpe %5.2f  maxDD %7s"
              % (fmt_pct(bh_spy["cagr"]), bh_spy["sharpe"],
                 fmt_pct(bh_spy["maxdd"])))
        hv, lv = r["regimes"]["hi_vol"], r["regimes"]["lo_vol"]
        print("  regime hi-vol: win %.1f%% avg %s t %.2f n %d | "
              "lo-vol: win %.1f%% avg %s t %.2f n %d"
              % (100 * hv["win"], fmt_pct(hv["avg"]), hv["t"], hv["n"],
                 100 * lv["win"], fmt_pct(lv["avg"]), lv["t"], lv["n"]))
        ef, st = r["segments"]["etf"], r["segments"]["stock"]
        print("  segment ETF: win %.1f%% avg %s t %.2f n %d | "
              "stocks: win %.1f%% avg %s t %.2f n %d"
              % (100 * ef["win"], fmt_pct(ef["avg"]), ef["t"], ef["n"],
                 100 * st["win"], fmt_pct(st["avg"]), st["t"], st["n"]))
        print()
    results["bh_spy"] = perf(bh_daily(spy))

    out = os.path.join(VAULT, "research", "experiments",
                       "exp-mean-reversion-results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=1)
    print("results json ->", out)


if __name__ == "__main__":
    main()
