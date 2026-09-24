#!/usr/bin/env python
"""Time-series momentum (12-1) vs baselines -- alpha research experiment.

Question: does absolute (time-series) momentum generate alpha AFTER COSTS
in the 125-ticker factor-store universe?

Method
------
* Data:   Efforts/osanwe-v2-overhaul/_work/factors.db, table `bars`
          (ticker, date, close), read with sqlite3 directly.
* Signal: 12-1 momentum per ticker = close[t-21] / close[t-252] - 1.
          LONG if signal > 0, FLAT otherwise.
* Rebalance: weekly (every 5th trading day). Trades execute at the
          decision-date close; position earns returns from next day.
* Costs:  per-side execution costs from tools/execution-cost-model.py
          (half the round-trip bp, charged on both entry AND exit),
          order size = BOOK_USD / number of active positions.
* Baselines (same evaluation window, same cost machinery where traded):
    1. Buy-and-hold SPY (no trading costs)
    2. Buy-and-hold equal-weight all tickers (no trading costs)
    3. MA200 rule per ticker, weekly rebalance, WITH costs
    4. Random-entry strategy matched to TSM average exposure and
       average holding period, WITH costs (multi-seed)

Metrics: CAGR, Sharpe, maxDD, win rate (% positive months),
avg monthly excess vs SPY, t-stat of monthly excess.

Failure criteria: REJECT if Sharpe < SPY buy-and-hold OR t-stat < 1.5.

Regime test: VIXCLS (< 20 = LOW, else HIGH) from the `factors` table.

Constraints honored: ASCII only, no network, sqlite3 direct access,
stdlib-only math.

Usage:
    python tools/research/ts-momentum.py                # run + save JSON
    python tools/research/ts-momentum.py --quick        # fewer random seeds
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import random
import sqlite3
import sys
from collections import defaultdict

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
VAULT = r"/path/to/vault"
DB_PATH = os.path.join(
    VAULT, "Efforts", "osanwe-v2-overhaul", "_work", "factors.db")
COST_MODEL_PATH = os.path.join(VAULT, "tools", "execution-cost-model.py")
RESULTS_DIR = os.path.join(VAULT, "research", "experiments")

BOOK_USD = 1_000_000.0     # notional book used for order-size-dependent costs
REBAL_FREQ = 5             # trading days between rebalances (weekly)
LOOKBACK = 252             # momentum lookback (trading days)
SKIP = 21                  # most-recent days excluded (12-1 momentum)
MA_WINDOW = 200            # moving-average baseline window


def load_cost_model():
    """Import the hyphenated execution-cost-model.py by file path."""
    spec = importlib.util.spec_from_file_location(
        "execution_cost_model", COST_MODEL_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["execution_cost_model"] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Data loading (sqlite3 direct)
# ---------------------------------------------------------------------------

def load_bars(db_path=DB_PATH):
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute("SELECT ticker, date, close FROM bars").fetchall()
        factors = con.execute(
            "SELECT date, value FROM factors "
            "WHERE factor='VIXCLS' AND value IS NOT NULL").fetchall()
    finally:
        con.close()
    px = defaultdict(dict)
    for tk, dt, cl in rows:
        px[tk][dt] = float(cl)
    for tk in px:
        px[tk] = dict(sorted(px[tk].items()))
    vix = dict(sorted(factors))
    return dict(px), vix


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def month_key(date_str):
    return date_str[:7]


def perf_stats(dates, rets, spy_by_date=None):
    """Compute CAGR, Sharpe, maxDD, win rate, monthly excess stats.

    rets: dict date -> daily return (already net of costs).
    """
    ds = [d for d in dates if d in rets]
    rs = [rets[d] for d in ds]
    n = len(rs)
    if n == 0:
        return None

    cum = 1.0
    peak = 1.0
    maxdd = 0.0                 # stored as a negative number (or 0)
    # monthly aggregation
    mret = defaultdict(float)   # log-ish compounding per month
    for d, r in zip(ds, rs):
        cum *= (1.0 + r)
        peak = max(peak, cum)
        drawdown = cum / peak - 1.0     # <= 0
        if drawdown < maxdd:
            maxdd = drawdown
        mret[month_key(d)] += math.log1p(r)

    years = n / 252.0
    cagr = cum ** (1.0 / years) - 1.0 if cum > 0 else -1.0
    mu = sum(rs) / n
    var = sum((r - mu) ** 2 for r in rs) / max(n - 1, 1)
    sd = math.sqrt(var)
    sharpe = (mu / sd) * math.sqrt(252.0) if sd > 0 else 0.0

    months = sorted(mret)
    mrets = [math.expm1(mret[m]) for m in months]
    wins = sum(1 for r in mrets if r > 0)
    win_rate = wins / len(mrets) if mrets else 0.0

    out = {
        "cagr_pct": round(cagr * 100.0, 2),
        "sharpe": round(sharpe, 3),
        "max_dd_pct": round(maxdd * 100.0, 2),
        "win_rate_months_pct": round(win_rate * 100.0, 1),
        "n_days": n,
        "n_months": len(mrets),
        "total_return_pct": round((cum - 1.0) * 100.0, 2),
    }

    if spy_by_date is not None:
        exc = []
        for m in months:
            sm = month_spy_return(m, spy_by_date)
            if sm is not None:
                exc.append(math.expm1(mret[m]) - sm)
        if len(exc) >= 3:
            emu = sum(exc) / len(exc)
            ev = sum((x - emu) ** 2 for x in exc) / max(len(exc) - 1, 1)
            esd = math.sqrt(ev)
            t = emu / esd * math.sqrt(len(exc)) if esd > 0 else 0.0
            out["avg_monthly_excess_vs_spy_pct"] = round(emu * 100.0, 3)
            out["t_stat_monthly_excess_vs_spy"] = round(t, 3)
        else:
            out["avg_monthly_excess_vs_spy_pct"] = None
            out["t_stat_monthly_excess_vs_spy"] = None
    return out


def month_spy_return(month, spy_by_date):
    """Monthly SPY return computed the SAME way as strategy months
    (expm1 of summed log returns) so excess is not an aggregation artifact."""
    rs = [r for d, r in spy_by_date.items() if d[:7] == month]
    if not rs:
        return None
    return math.expm1(sum(math.log1p(r) for r in rs))


# ---------------------------------------------------------------------------
# Backtest engine
# ---------------------------------------------------------------------------

class Universe:
    """Calendar-aligned price panel."""

    def __init__(self, px):
        self.px = px
        self.dates = sorted(set().union(*[set(v) for v in px.values()]))
        self.idx = {d: i for i, d in enumerate(self.dates)}
        # per-ticker aligned close list (None where missing) + daily returns
        self.close = {}
        self.ret = {}
        for tk, ser in px.items():
            cl = [ser.get(d) for d in self.dates]
            self.close[tk] = cl
            r = [None] * len(cl)
            prev = None
            for i, c in enumerate(cl):
                if c is not None and prev is not None and prev > 0:
                    r[i] = c / prev - 1.0
                if c is not None:
                    prev = c
            self.ret[tk] = r

    def ts_mom_signal(self, tk, i):
        """12-1 momentum at decision index i (needs close[i-SKIP]/close[i-LOOKBACK])."""
        cl = self.close[tk]
        j1, j2 = i - SKIP, i - LOOKBACK
        if j2 < 0:
            return None
        c1, c2 = cl[j1], cl[j2]
        if c1 is None or c2 is None or c2 <= 0:
            return None
        return c1 / c2 - 1.0

    def ma_signal(self, tk, i):
        """True if close[i] > 200-day SMA ending at i."""
        cl = self.close[tk]
        lo = i - MA_WINDOW + 1
        if lo < 0 or cl[i] is None:
            return None
        vals = [c for c in cl[lo:i + 1] if c is not None]
        if len(vals) < MA_WINDOW * 0.9:
            return None
        return cl[i] > sum(vals) / len(vals)


def run_rule_backtest(univ, tickers, signal_fn, cost_side_fn, start_i,
                      rebal_freq=REBAL_FREQ):
    """Generic weekly-rebalance long/flat backtest driven by signal_fn.

    Returns (dates, net_returns dict, diagnostics dict).
    """
    dates = univ.dates
    long_set = set()
    pending_entries = set()   # entered this bar -> pay cost now, earn from next
    pending_exit = set()      # held last bar, sold now -> pay cost now
    rets = {}
    n_trades = 0
    total_cost_drag = 0.0
    long_weeks = 0
    weeks = 0

    first_rebal = start_i
    while (first_rebal - start_i) % rebal_freq != 0:
        first_rebal += 1

    for i in range(start_i, len(dates)):
        d = dates[i]
        # 1) realize today's portfolio return from positions set as of yesterday
        day_ret = 0.0
        if long_set:
            vals = [univ.ret[tk][i] for tk in long_set
                    if univ.ret[tk][i] is not None]
            if vals:
                day_ret = sum(vals) / len(vals)
        ret = day_ret

        # 2) weekly decision
        if i >= first_rebal and (i - first_rebal) % rebal_freq == 0:
            weeks += 1
            new_long = set()
            for tk in tickers:
                sig = signal_fn(tk, i)
                if sig:
                    new_long.add(tk)
            entries = new_long - long_set
            exits = long_set - new_long
            n_active = max(len(new_long), 1)
            order_usd = BOOK_USD / n_active
            cost = 0.0
            for tk in entries | exits:
                side_bp = cost_side_fn(tk, order_usd)
                cost += (1.0 / n_active) * side_bp / 10000.0
                n_trades += 1
            ret -= cost
            total_cost_drag += cost
            long_set = new_long
            if new_long:
                long_weeks += 1
        rets[d] = ret

    diag = {
        "n_trades": n_trades,
        "avg_cost_drag_per_rebalance_pct": round(
            100.0 * total_cost_drag / max(weeks, 1), 4),
        "avg_exposure_pct_of_weeks": round(
            100.0 * long_weeks / max(weeks, 1), 1),
    }
    return dates, rets, diag


def measure_holding_stats(univ, tickers, signal_fn, start_i):
    """Average consecutive-long-run length (in weeks) and average exposure."""
    weeks = []
    exposure_sum = 0.0
    runs = []
    cur = {}
    first = start_i
    for i in range(first, len(univ.dates), REBAL_FREQ):
        wl = set()
        for tk in tickers:
            if signal_fn(tk, i):
                wl.add(tk)
        exposure_sum += len(wl)
        weeks.append(wl)
        for tk in tickers:
            if tk in wl:
                cur.setdefault(tk, 0)
                cur[tk] += 1
            elif tk in cur:
                runs.append(cur.pop(tk))
    for tk in cur:
        runs.append(cur[tk])
    n_weeks = len(weeks)
    avg_hold = sum(runs) / len(runs) if runs else 1.0
    exposure = exposure_sum / max(n_weeks * len(tickers), 1)
    return avg_hold, exposure, n_weeks, len(runs)


def run_random_backtest(univ, tickers, cost_side_fn, start_i, avg_hold_weeks,
                        exposure, rng):
    """Random entry matched to TSM exposure and holding period.

    Flat -> enter w.p. p each week; once long -> stay avg_hold_weeks weeks.
    Steady-state exposure = H / (H + 1/p)  =>  p = exposure / (H*(1-exposure)).
    """
    p = exposure / max(avg_hold_weeks * (1.0 - exposure), 1e-9)
    p = min(p, 1.0)
    dates = univ.dates
    holdings = {}   # tk -> weeks remaining
    rets = {}
    n_trades = 0
    weeks = 0
    long_weeks = 0
    first = start_i
    while (first - start_i) % REBAL_FREQ != 0:
        first += 1

    for i in range(start_i, len(dates)):
        d = dates[i]
        day_ret = 0.0
        if holdings:
            vals = [univ.ret[tk][i] for tk in holdings
                    if univ.ret[tk][i] is not None]
            if vals:
                day_ret = sum(vals) / len(vals)
        ret = day_ret

        if i >= first and (i - first) % REBAL_FREQ == 0:
            weeks += 1
            # decrement / exit
            exited = [tk for tk, h in holdings.items() if h <= 1]
            for tk in exited:
                del holdings[tk]
            # entries
            flat = [tk for tk in tickers if tk not in holdings]
            entries = [tk for tk in flat if rng.random() < p]
            n_active = max(len(holdings) + len(entries), 1)
            order_usd = BOOK_USD / n_active
            cost = 0.0
            for tk in exited:
                cost += (1.0 / n_active) * cost_side_fn(tk, order_usd) / 10000.0
                n_trades += 1
            for tk in entries:
                holdings[tk] = avg_hold_weeks
                cost += (1.0 / n_active) * cost_side_fn(tk, order_usd) / 10000.0
                n_trades += 1
            ret -= cost
            if holdings:
                long_weeks += 1
        rets[d] = ret
    diag = {"n_trades": n_trades, "p_entry": round(p, 4)}
    return dates, rets, diag, (long_weeks / max(weeks, 1))


# ---------------------------------------------------------------------------
# Regime analysis (VIX)
# ---------------------------------------------------------------------------

def regime_stats(dates, rets, vix):
    """Forward-fill VIXCLS onto calendar; split daily returns into regimes."""
    vdates = sorted(vix)
    def vix_on(d):
        # latest VIX print on/before d
        import bisect
        k = bisect.bisect_right(vdates, d)
        if k == 0:
            return None
        return vix[vdates[k - 1]]
    low, high = [], []
    for d in dates:
        if d not in rets:
            continue
        v = vix_on(d)
        if v is None:
            continue
        (low if v < 20.0 else high).append(rets[d])

    def ann(rs):
        if len(rs) < 30:
            return None
        mu = sum(rs) / len(rs)
        var = sum((r - mu) ** 2 for r in rs) / max(len(rs) - 1, 1)
        sd = math.sqrt(var)
        cum = 1.0
        for r in rs:
            cum *= (1.0 + r)
        yrs = len(rs) / 252.0
        return {
            "ann_return_pct": round((cum ** (1.0 / yrs) - 1.0) * 100.0, 2)
                              if cum > 0 else -100.0,
            "sharpe": round(mu / sd * math.sqrt(252.0), 3) if sd > 0 else 0.0,
            "n_days": len(rs),
        }
    return {"low_vix_lt20": ann(low), "high_vix_ge20": ann(high),
            "pct_days_low_vix": round(100.0 * len(low) /
                                      max(len(low) + len(high), 1), 1)}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=100)
    args = ap.parse_args()

    cm = load_cost_model()
    px, vix = load_bars()
    univ = Universe(px)
    all_tickers = sorted(univ.px.keys())
    print("tickers=%d dates=%d (%s .. %s)" %
          (len(all_tickers), len(univ.dates), univ.dates[0], univ.dates[-1]))

    # Evaluation window: first index where ANY ticker can produce a 12-1
    # signal, padded so most tickers are eligible; use majority-eligibility.
    def eligible_count(i):
        return sum(1 for tk in all_tickers
                   if i - LOOKBACK >= 0 and univ.close[tk][i - LOOKBACK] is not None
                   and univ.close[tk][i - SKIP] is not None)
    start_i = LOOKBACK
    while start_i < len(univ.dates) and eligible_count(start_i) < len(all_tickers) * 0.8:
        start_i += 1
    eval_dates = univ.dates[start_i:]
    print("eval window: %s .. %s (%d days)" %
          (univ.dates[start_i], univ.dates[-1], len(eval_dates)))

    # cost function: half round trip, cached per (ticker, order bucket)
    cache = {}

    def cost_side_fn(tk, order_usd):
        key = (tk, int(round(order_usd, -3)))
        if key not in cache:
            r = cm.estimate_trade_cost(tk, order_usd)
            cache[key] = r["round_trip_bp"] / 2.0
        return cache[key]

    results = {"meta": {
        "db_path": DB_PATH,
        "n_tickers": len(all_tickers),
        "eval_start": eval_dates[0],
        "eval_end": eval_dates[-1],
        "book_usd": BOOK_USD,
        "rebal_freq_days": REBAL_FREQ,
        "signal": "ts_mom_12_1: close[t-21]/close[t-252]-1 > 0 => LONG",
        "cost_model": "tools/execution-cost-model.py, side = RT/2, entry+exit",
    }, "strategies": {}, "diagnostics": {}, "regimes": {}}

    # --- strategy under test: time-series momentum ------------------------
    mom_sig = lambda tk, i: (lambda s: s is not None and s > 0.0)(
        univ.ts_mom_signal(tk, i))
    _, mom_rets, mom_diag = run_rule_backtest(
        univ, all_tickers, mom_sig, cost_side_fn, start_i)
    results["diagnostics"]["ts_momentum"] = mom_diag
    zero_cost = lambda tk, usd: 0.0
    _, mom_gross_rets, _ = run_rule_backtest(
        univ, all_tickers, mom_sig, zero_cost, start_i)

    # baselines -------------------------------------------------------------
    # 1) SPY buy-and-hold (no costs)
    spy_rets = {d: univ.ret["SPY"][i] for i, d in enumerate(univ.dates)
                if i >= start_i and univ.ret["SPY"][i] is not None}
    # 2) equal-weight buy-and-hold all tickers (no costs)
    ew_rets = {}
    for i in range(start_i, len(univ.dates)):
        vals = [univ.ret[tk][i] for tk in all_tickers
                if univ.ret[tk][i] is not None]
        if vals:
            ew_rets[univ.dates[i]] = sum(vals) / len(vals)
    # 3) MA200 rule with costs
    ma_sig = lambda tk, i: univ.ma_signal(tk, i)
    _, ma_rets, ma_diag = run_rule_backtest(
        univ, all_tickers, ma_sig, cost_side_fn, start_i)
    results["diagnostics"]["ma200"] = ma_diag

    # 4) random entry, matched exposure + holding --------------------------
    avg_hold, exposure, n_weeks, n_runs = measure_holding_stats(
        univ, all_tickers, mom_sig, start_i)
    results["diagnostics"]["ts_momentum"]["avg_hold_weeks"] = round(avg_hold, 2)
    results["diagnostics"]["ts_momentum"]["avg_exposure_fraction"] = round(exposure, 3)
    results["diagnostics"]["ts_momentum"]["n_runs_measured"] = n_runs
    rnd_runs = []
    for s in range(args.seeds):
        rng = random.Random(1234 + s)
        _, rr, _, exp_act = run_random_backtest(
            univ, all_tickers, cost_side_fn, start_i, max(int(round(avg_hold)), 1),
            exposure, rng)
        rnd_runs.append(rr)

    # metrics ---------------------------------------------------------------
    spy_month = {}
    for d, r in spy_rets.items():
        spy_month.setdefault(d[:7], None)

    def add(name, rets):
        st = perf_stats(eval_dates, rets, spy_by_date=spy_rets)
        results["strategies"][name] = st
        return st

    add("ts_momentum_net", mom_rets)
    add("ts_momentum_gross_no_costs", mom_gross_rets)
    add("spy_buy_hold", spy_rets)
    add("ew_buy_hold", ew_rets)
    add("ma200_net", ma_rets)
    rnd_agg = {}
    keys = ["cagr_pct", "sharpe", "max_dd_pct", "win_rate_months_pct",
            "avg_monthly_excess_vs_spy_pct", "t_stat_monthly_excess_vs_spy"]
    for k in keys:
        vals = [r[k] for r in (perf_stats(eval_dates, rr, spy_by_date=spy_rets)
                               for rr in rnd_runs) if r and r.get(k) is not None]
        if vals:
            rnd_agg[k] = round(sum(vals) / len(vals), 3)
    rnd_agg["n_seeds"] = args.seeds
    results["strategies"]["random_matched_net"] = rnd_agg
    # spread of random seeds (context for luck)
    shs = sorted(perf_stats(eval_dates, rr)["sharpe"] for rr in rnd_runs)
    results["strategies"]["random_matched_net"]["sharpe_p05_p95"] = [
        round(shs[int(0.05 * len(shs))], 3), round(shs[int(0.95 * len(shs))], 3)]

    # regime analysis -------------------------------------------------------
    results["regimes"]["ts_momentum_net"] = regime_stats(
        eval_dates, mom_rets, vix)
    results["regimes"]["spy_buy_hold"] = regime_stats(eval_dates, spy_rets, vix)

    # verdict ---------------------------------------------------------------
    mom = results["strategies"]["ts_momentum_net"]
    spy = results["strategies"]["spy_buy_hold"]
    tstat = mom.get("t_stat_monthly_excess_vs_spy")
    fails = []
    if mom["sharpe"] < spy["sharpe"]:
        fails.append("Sharpe %.2f < SPY buy-hold %.2f" %
                     (mom["sharpe"], spy["sharpe"]))
    if tstat is None or tstat < 1.5:
        fails.append("t-stat %s < 1.5" % tstat)
    results["verdict"] = {
        "passes": len(fails) == 0,
        "criteria_failed": fails,
    }

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_json = os.path.join(RESULTS_DIR, "exp-ts-momentum-results.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(json.dumps(results, indent=2))
    print("\nsaved:", out_json)
    return results


if __name__ == "__main__":
    main()
