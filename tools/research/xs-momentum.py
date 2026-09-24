#!/usr/bin/env python
"""Cross-sectional momentum research: does trailing 63d-return momentum
(rank tickers, long winners / short losers) generate alpha after costs?

Universe : factors.db bars, excluding crypto (*-USD), OTC ADRs
           (ABBNY/ASMIY/ATEYY), and tickers with < 750 bars.
Signal   : at each month-end, rank eligible names by trailing 63-trading-day
           return; top quintile = LONG book, bottom quintile = SHORT book.
Costs    : tools/execution-cost-model.py (per-ticker class round-trip bp,
           charged on each side of every rebalance trade).
Baselines: buy-and-hold SPY, equal-weight all eligible, random quintile.
Metrics  : CAGR (long leg), Sharpe, maxDD, t-stat of monthly excess vs SPY,
           IC (Spearman rank IC of signal vs forward month return).
Decay    : holding periods of 21d / 63d / 126d.

Usage:
    python tools/research/xs-momentum.py            # full run + markdown
    python tools/research/xs-momentum.py --test     # unit checks

ASCII only. No network. sqlite3 used directly for all data access.
"""

from __future__ import annotations

import argparse
import math
import os
import random
import sqlite3
import sys
from collections import defaultdict

import numpy as np

# ---------------------------------------------------------------------------
# Locate the vault root and the factors database.
# The repo root factors.db is a placeholder; the populated store lives in
# Efforts/osanwe-v2-overhaul/_work/factors.db. Fall back through candidates.
# ---------------------------------------------------------------------------

VAULT = os.environ.get(
    "OSANWE_VAULT",
    os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "..", "..")),
)

DB_CANDIDATES = [
    os.path.join(VAULT, "Efforts", "osanwe-v2-overhaul", "_work", "factors.db"),
    os.path.join(VAULT, "factors.db"),
]

EXCLUDE_TICKERS = {"ABBNY", "ASMIY", "ATEYY"}   # OTC ADRs per spec
MIN_BARS = 750
QUINTILES = 5

# Cost model import ---------------------------------------------------------
# Cost model import: tools/execution-cost-model.py has hyphens in its
# filename, so it must be loaded by path rather than a plain import.
import importlib.util  # noqa: E402

_COST_MODEL_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..",
    "execution-cost-model.py"))


def _load_cost_model():
    spec = importlib.util.spec_from_file_location(
        "execution_cost_model", _COST_MODEL_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["execution_cost_model"] = mod
    spec.loader.exec_module(mod)
    return mod


_ecm = _load_cost_model()
estimate_trade_cost = _ecm.estimate_trade_cost


def find_db() -> str:
    for path in DB_CANDIDATES:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return path
    raise SystemExit("No populated factors.db found in: %r" % DB_CANDIDATES)


def load_bars(db_path: str):
    """Return {ticker: (dates_list, close_array)} sorted by date."""
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT ticker, date, close FROM bars ORDER BY ticker, date"
        ).fetchall()
    finally:
        con.close()
    data = defaultdict(lambda: ([], []))
    counts = defaultdict(int)
    for tk, dt, cl in rows:
        counts[tk] += 1
        d, c = data[tk]
        d.append(dt)
        c.append(cl)
    return {tk: (np.array(d), np.asarray(c, dtype=float))
            for tk, (d, c) in data.items()}, counts


def eligible_universe(counts) -> list:
    out = []
    for tk, n in sorted(counts.items()):
        if n < MIN_BARS:
            continue
        if tk.endswith("-USD"):
            continue
        if tk.upper() in EXCLUDE_TICKERS:
            continue
        if tk.upper() == "SPY":
            continue  # benchmark, not an asset we cross-sectionally pick
        out.append(tk.upper())
    return out


def month_end_dates(all_dates):
    """Group trading dates by calendar month; return last date of each."""
    seen = {}
    for i, d in enumerate(sorted(set(all_dates))):
        seen.setdefault(d[:7], []).append((d, i))
    return [(month, entries[-1][0], entries[-1][1]) for month, entries in
            sorted(seen.items())]


def compute_ic_series(panel: PricePanel):
    """Rank IC of 63d trailing return vs next-21d forward return,
    measured at EVERY month-end (independent of holding period)."""
    rets = panel.ret_matrix()
    out = []
    for month, dte, pos in month_end_dates(panel.dates):
        if pos < 63 + 1 or pos + 22 >= panel.n:
            continue
        sig = panel.trailing_return(pos, 63)
        fwd = panel.forward_return(pos, 21)
        valid = np.where(np.isfinite(sig) & np.isfinite(fwd))[0]
        if len(valid) < 10:
            continue
        s = sig[valid]; f = fwd[valid]
        rs = np.argsort(np.argsort(s)).astype(float)
        rf = np.argsort(np.argsort(f)).astype(float)
        if rs.std() == 0 or rf.std() == 0:
            continue
        out.append((dte, float(np.corrcoef(rs, rf)[0, 1])))
    return out


class PricePanel(object):
    """Dense close-price panel indexed by global trading-day position.

    Positions come from the union of all trading dates so that different
    listing histories align on the same integer axis.
    """

    def __init__(self, bars, universe):
        self.dates = sorted({d for tk in universe for d in bars[tk][0]})
        self.pos = {d: i for i, d in enumerate(self.dates)}
        self.n = len(self.dates)
        px = np.full((len(universe), self.n), np.nan)
        self.tickers = list(universe)
        self.idx = {tk: i for i, tk in enumerate(self.tickers)}
        for tk in self.tickers:
            dts, closes = bars[tk]
            row = px[self.idx[tk]]
            for j, dt in enumerate(dts):
                row[self.pos[dt]] = closes[j]
        # Forward-fill within each series (survivorship-free panel keeps NaNs
        # before listing; ffill covers stray market holidays per ticker).
        for i in range(px.shape[0]):
            row = px[i]
            mask = ~np.isnan(row)
            if mask.any():
                idx = np.where(mask)[0]
                row[:idx[0]] = np.nan          # keep pre-listing as NaN
                interp = np.interp(np.arange(self.n), idx, row[idx])
                post_nan = np.isnan(row) & (np.arange(self.n) >= idx[0])
                row[post_nan] = interp[post_nan]
                row[idx] = row[idx]
        self.px = px

    def ret_matrix(self):
        r = np.full_like(self.px, np.nan)
        r[:, 1:] = self.px[:, 1:] / self.px[:, :-1] - 1.0
        return r

    def trailing_return(self, end_pos: int, lookback: int):
        """Per-ticker total return over [end_pos-lookback+1, end_pos]."""
        lo = max(0, end_pos - lookback + 1)
        p0 = self.px[:, lo]
        p1 = self.px[:, end_pos]
        with np.errstate(invalid="ignore", divide="ignore"):
            out = p1 / p0 - 1.0
        out[~np.isfinite(out)] = np.nan
        return out

    def forward_return(self, start_pos: int, horizon_days: int):
        """Per-ticker total return over [start_pos+1, start_pos+horizon]."""
        hi = min(self.n - 1, start_pos + horizon_days)
        p0 = self.px[:, start_pos]
        p1 = self.px[:, hi]
        with np.errstate(invalid="ignore", divide="ignore"):
            out = p1 / p0 - 1.0
        out[~np.isfinite(out)] = np.nan
        return out


# ---------------------------------------------------------------------------
# Cost layer
# ---------------------------------------------------------------------------

COST_ORDER_USD = 100_000.0   # notional per single-name order for cost lookup


def cost_bps(ticker: str) -> float:
    """Round-trip cost in bp from the vault execution-cost model."""
    r = estimate_trade_cost(ticker, COST_ORDER_USD)
    return float(r["round_trip_bp"])


# ---------------------------------------------------------------------------
# Strategy simulation
# ---------------------------------------------------------------------------

def simulate(panel: PricePanel, hold_days: int, seed: int = 42,
             mode: str = "ls", n_random: int = 1):
    """Simulate monthly-rebalanced momentum portfolios.

    mode='ls'   : long top quintile + short bottom quintile (returns of the
                  combined book = 0.5*L + 0.5*S, S sign-flipped)
    mode='long' : long top quintile only (the reported 'long leg')
    mode='ew'   : equal-weight ALL eligible names
    mode='random': random-quintile baseline (n_random draws averaged)

    Returns dict with daily return arrays and turnover stats.
    """
    rng = random.Random(seed)
    rets = panel.ret_matrix()
    med = month_end_dates(panel.dates)
    cost_table = {tk: cost_bps(tk) for tk in panel.tickers}

    rebal_points = []      # (pos, month)
    for month, dte, pos in med:
        if pos < 63 + 1 or pos + 1 >= panel.n:
            continue
        rebal_points.append((pos, month))
    # Holding-period logic: with hold_days > ~21d we do NOT trade every
    # month-end; we only rebalance when the current holding window expires.
    if hold_days <= 21:
        active = list(rebal_points)
    else:
        step = max(1, round(hold_days / 21.0))   # months per holding period
        active = rebal_points[::step]
    rebal_points = active

    daily = np.full(panel.n, np.nan)       # strategy daily return
    ic_series = []                          # (date_str, ic)
    turnover_events = []
    prev_long, prev_short = set(), set()

    for k in range(len(rebal_points)):
        pos, month = rebal_points[k]
        nxt = rebal_points[k + 1][0] if k + 1 < len(rebal_points) \
            else panel.n - 1
        sig = panel.trailing_return(pos, 63)
        fwd = panel.forward_return(pos, 21)   # IC measured vs next-month-ish
        valid = np.where(np.isfinite(sig) & np.isfinite(fwd))[0]

        # Rank IC (Spearman): corr of signal ranks vs fwd ranks
        if len(valid) >= 10:
            s = sig[valid]; f = fwd[valid]
            rs = np.argsort(np.argsort(s)).astype(float)
            rf = np.argsort(np.argsort(f)).astype(float)
            if rs.std() > 0 and rf.std() > 0:
                ic = float(np.corrcoef(rs, rf)[0, 1])
                ic_series.append((panel.dates[pos], ic))

        qsize = max(1, len(valid) // QUINTILES)
        order = valid[np.argsort(-sig[valid])]      # descending signal
        top = set(order[:qsize].tolist())
        bot = set(order[-qsize:].tolist())

        if mode == "random":
            pool = valid.tolist()
            top = set(rng.sample(pool, qsize))
            bot = set()

        if mode == "ew":
            top = set(valid.tolist())
            bot = set()

        # ---- daily returns until next rebalance --------------------------
        days = range(pos + 1, nxt + 1)
        # Per-day equal-weight book return: average across members (axis 0
        # of rets is tickers), yielding one value per trading day.
        L = (np.nanmean(rets[sorted(top)], axis=0)
             if top else np.full(panel.n, np.nan))
        leg_vals = [("long", top, L)]
        if mode == "ls":
            B = (np.nanmean(rets[sorted(bot)], axis=0)
                 if bot else np.full(panel.n, np.nan))
            leg_vals.append(("short", bot, B))

        # Turnover costs: each traded name pays the cost model's round trip
        # (entry charged now, exit charged when it later leaves). The charge
        # is a fraction of the LEG's capital: traded_names / leg_size.
        seg_cost_frac = 0.0
        for legname, members, _arr in leg_vals:
            new_set = set(members)
            old_set = prev_long if legname == "long" else prev_short
            entered = new_set - old_set
            exited = old_set - new_set
            traded = entered | exited
            if new_set:
                avg_rt_bp = (sum(cost_table.get(t, 20.0) for t in traded)
                             / len(traded)) if traded else 0.0
                seg_cost_frac += (len(traded) / len(new_set)) \
                    * avg_rt_bp / 10000.0
            if legname == "long":
                prev_long = new_set
            else:
                prev_short = new_set

        n_legs = len(leg_vals)
        for d in days:
            parts = []
            for _legname, _mem, arr in leg_vals:
                v = arr[d]
                if np.isfinite(v):
                    parts.append(v if _legname != "short" else -v)
            if not parts:
                continue
            r = sum(parts) / len(parts)
            # amortize one-off rebalance cost evenly over the holding window
            ndays = max(1, nxt - pos)
            r -= seg_cost_frac / ndays
            daily[d] = r
        turnover_events.append(seg_cost_frac * 10000.0)

    return {
        "daily": daily,
        "ic": ic_series,
        "turnover_bp_per_rebal": turnover_events,
        "cost_table": cost_table,
    }


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def perf_stats(daily: np.ndarray, ann_factor=252.0):
    r = daily[np.isfinite(daily)]
    if len(r) < 30:
        return None
    eq = np.cumprod(1.0 + r)
    years = len(r) / ann_factor
    cagr = eq[-1] ** (1.0 / years) - 1.0
    mu, sd = r.mean(), r.std(ddof=1)
    sharpe = (mu / sd) * math.sqrt(ann_factor) if sd > 0 else float("nan")
    peak = np.maximum.accumulate(eq)
    mdd = float(((eq - peak) / peak).min())
    return {"cagr": cagr, "sharpe": sharpe, "maxdd": mdd, "ndays": len(r),
            "total_ret": eq[-1] - 1.0}


def monthly_series(daily: np.ndarray, dates):
    """Compound daily returns into calendar-month returns."""
    agg = defaultdict(float)
    for d, r in zip(dates, daily):
        if np.isfinite(r):
            agg[d[:7]] *= (1.0 + r)
            agg[d[:7]] += r  # log-ish approx replaced below
    # redo properly (compounding)
    agg = defaultdict(lambda: 1.0)
    for d, r in zip(dates, daily):
        if np.isfinite(r):
            agg[d[:7]] *= (1.0 + r)
    return {m: v - 1.0 for m, v in agg.items()}


def tstat_excess(strat_daily: np.ndarray, bench_daily: np.ndarray,
                 dates, freq="monthly"):
    """t-stat of mean periodic excess return of strategy vs benchmark."""
    ms = monthly_series(strat_daily, dates)
    mb = monthly_series(bench_daily, dates)
    common = sorted(set(ms) & set(mb))
    ex = np.array([ms[m] - mb[m] for m in common])
    if len(ex) < 5 or ex.std(ddof=1) == 0:
        return float("nan"), len(ex), float("nan")
    t = ex.mean() / (ex.std(ddof=1) / math.sqrt(len(ex)))
    return float(t), len(ex), float(ex.mean())


def spearman_ic_stats(ic_pairs):
    ics = np.array([v for _, v in ic_pairs])
    if len(ics) < 5:
        return float("nan"), float("nan"), len(ics)
    t = ics.mean() / (ics.std(ddof=1) / math.sqrt(len(ics)))
    return float(ics.mean()), float(t), len(ics)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(holds=(21, 63, 126), verbose=True):
    db = find_db()
    bars, counts = load_bars(db)
    universe = eligible_universe(counts)
    panel = PricePanel(bars, universe)
    spy = bars.get("SPY")
    assert spy is not None, "SPY required as benchmark"

    # SPY aligned onto the panel's date axis
    spy_daily = np.full(panel.n, np.nan)
    spy_px_by_date = dict(zip(spy[0].tolist(), spy[1].tolist()))
    dts = panel.dates
    px_prev = None
    for i, d in enumerate(dts):
        p = spy_px_by_date.get(d)
        if p is None:
            continue
        if px_prev is not None:
            spy_daily[i] = p / px_prev - 1.0
        px_prev = p

    results = {"universe_n": len(universe),
               "panel_days": panel.n,
               "start": dts[0], "end": dts[-1],
               "cost_order_usd": COST_ORDER_USD}
    results["spy_stats"] = perf_stats(spy_daily)

    ew = simulate(panel, 21, mode="ew")
    results["ew_stats"] = perf_stats(ew["daily"])

    rnd_runs = [simulate(panel, h, seed=s, mode="random")
                for h in (21,) for s in (7, 8, 9)]
    rnd_avg = np.full(panel.n, np.nan)
    stack = np.vstack([r["daily"] for r in rnd_runs])
    with np.errstate(invalid="ignore"):
        rnd_avg = np.nanmean(stack, axis=0)
    results["random_stats"] = perf_stats(rnd_avg)

    base = simulate(panel, 63, mode="ls")     # also yields IC series
    ic_full = compute_ic_series(panel)
    results["ic_mean"], results["ic_t"], results["ic_n"] = \
        spearman_ic_stats(ic_full)
    # IC at the (quarterly) rebalance dates only, for comparison
    ic_rebal = [(d, v) for d, v in base["ic"]]
    results["ic_mean_rebal"], results["ic_t_rebal"], _ = \
        spearman_ic_stats(ic_rebal)
    results["avg_turnover_bp"] = float(np.mean(base["turnover_bp_per_rebal"]))

    long_sim = simulate(panel, 21, mode="long")
    results["long_stats"] = perf_stats(long_sim["daily"])
    ls_sim = base
    results["ls_stats"] = perf_stats(ls_sim["daily"])

    results["t_monthly_vs_spy"] = {}
    for label, sim in (("long", long_sim), ("ls", ls_sim),
                       ("ew", ew), ("random", {"daily": rnd_avg})):
        t, n, mu = tstat_excess(sim["daily"], spy_daily, dts)
        results["t_monthly_vs_spy"][label] = (t, n, mu)

    # Decay study: hold 21 / 63 / 126 days, report long-leg stats + IC
    decay = {}
    for h in holds:
        sim_l = simulate(panel, h, mode="long")
        st = perf_stats(sim_l["daily"])
        t, n, mu = tstat_excess(sim_l["daily"], spy_daily, dts)
        decay[h] = {"stats": st, "t_vs_spy": t}
    results["decay"] = decay

    if verbose:
        print_report(results)
    return results


def fmt(x, pct=False):
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "n/a"
    return ("%+.2f%%" % (100 * x)) if pct else "%.2f" % x


def print_report(res):
    print("=" * 72)
    print("CROSS-SECTIONAL MOMENTUM vs BASELINES")
    print("=" * 72)
    print("DB bars: %s .. %s (%d trading days), %d eligible tickers"
          % (res["start"], res["end"], res["panel_days"],
             res["universe_n"]))
    print("Avg turnover cost per rebalance: %.1f bp (both legs)"
          % res["avg_turnover_bp"])
    print("")
    hdr = "%-22s %10s %8s %9s %12s" % (
        "portfolio", "CAGR", "Sharpe", "maxDD", "t-mo vs SPY")
    print(hdr)
    print("-" * 72)
    rows = [
        ("Momentum LONG leg", res["long_stats"]),
        ("Momentum L+S", res["ls_stats"]),
        ("Equal-weight all", res["ew_stats"]),
        ("Random quintile", res["random_stats"]),
        ("SPY buy&hold", res["spy_stats"]),
    ]
    tmap = res["t_monthly_vs_spy"]
    labels = ["long", "ls", "ew", "random"]
    for (name, st), lab in zip(rows, labels + [None]):
        tcell = "n/a"
        if lab and lab in tmap:
            tcell = fmt(tmap[lab][0])
        if st is None:
            print("%-22s %10s %8s %9s %12s" % (name, "-", "-", "-", tcell))
        else:
            print("%-22s %10s %8s %9s %12s" % (
                name, fmt(st["cagr"], pct=True), fmt(st["sharpe"]),
                fmt(st["maxdd"], pct=True), tcell))
    print("")
    print("Rank IC (63d signal vs fwd 21d, all %d month-ends): mean=%s t=%s"
          % (res["ic_n"], fmt(res["ic_mean"]), fmt(res["ic_t"])))
    print("Rank IC at quarterly rebalance dates only: mean=%s t=%s"
          % (fmt(res["ic_mean_rebal"]), fmt(res["ic_t_rebal"])))
    print("")
    print("Signal decay (LONG leg, after costs):")
    print("  %-6s %10s %8s %9s %12s" % ("hold", "CAGR", "Sharpe", "maxDD",
                                          "t vs SPY"))
    for h in sorted(res["decay"]):
        d = res["decay"][h]
        st = d["stats"]
        if st is None:
            print("  %-6d %10s %8s %9s %12s" % (h, "-", "-", "-", "-"))
        else:
            print("  %-6d %10s %8s %9s %12s" % (
                h, fmt(st["cagr"], pct=True), fmt(st["sharpe"]),
                fmt(st["maxdd"], pct=True), fmt(d["t_vs_spy"])))
    print("")


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

def run_tests():
    # 1. month-end grouping
    me = month_end_dates(["2024-01-31", "2024-01-15", "2024-02-29",
                          "2024-02-05"])
    assert me[0][0] == "2024-01" and me[0][1] == "2024-01-31"
    assert me[1][1] == "2024-02-29"
    # 2. trailing / forward returns
    class P: pass
    p = P(); p.px = np.array([[10., 11., 12., 13., 14.]])
    pp = PricePanel.__new__(PricePanel)
    pp.px = p.px; pp.n = 5
    tr = pp.trailing_return(3, 3)
    assert abs(tr[0] - (13.0 / 11.0 - 1)) < 1e-9
    fr = pp.forward_return(1, 3)
    assert abs(fr[0] - (14.0 / 11.0 - 1)) < 1e-9
    # 3. cost function sane
    c = cost_bps("MSFT")
    assert 3.0 <= c <= 60.0, c
    c2 = cost_bps("AAOI")
    assert c2 > c
    # 4. monthly compounding
    ms = monthly_series(np.array([0.10, -0.05, np.nan]),
                        ["2024-01-02", "2024-01-03", "2024-02-01"])
    assert abs(ms["2024-01"] - (1.10 * 0.95 - 1)) < 1e-12
    assert "2024-02" not in ms
    print("All tests passed.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    args = ap.parse_args()
    if args.test:
        run_tests()
    else:
        run()
