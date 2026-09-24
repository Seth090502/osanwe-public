#!/usr/bin/env python3
"""
Regime-dependent strategy performance analysis (exp-regime-analysis).

QUESTION
    Do momentum, mean-reversion, and low-risk signals perform differently
    across market regimes? Which regime is the market in NOW?

DATA
    factors.db bars table (ticker, date, close), SPY + 107-instrument
    universe, 2021-08-24 .. 2026-08-24. Read with sqlite3 only.
    NOTE: the canonical DB is Efforts/osanwe-v2-overhaul/_work/factors.db;
    the 0-byte /path/to/vault/factors.db stub is ignored unless --db points
    at a populated file.

REGIMES (defined on SPY daily closes)
    BULL:       close > MA200 AND close > MA50
    CORRECTION: close < MA50 but > MA200
    BEAR:       close < MA200

STRATEGIES (computed fresh from bars; no lookahead: signal on day t uses
data through t, position earns the t->t+1 return)
    TSMOM      : time-series momentum, long SPY when SPY 12m-minus-1m
                 return > 0, else flat (cash).
    XS_MOM     : cross-sectional momentum top quintile by trailing
                 126d return among tickers with >= 200d history,
                 equal weight, weekly rebalance (first trading day of ISO week).
    MEANREV    : RSI(14) < 30 entries; equal-weight all oversold names,
                 held until RSI >= 50 or 10 trading days, max 5 names,
                 weekly entry refresh.
    LOWVOL_Q1  : bottom-quintile 60d return volatility, equal weight,
                 monthly rebalance (first trading day of month).

OUTPUTS
    - strategy x regime matrix: mean daily %, ann. %, ann. vol %, Sharpe,
      hit rate, days per regime cell
    - regime transition matrix P(next | current) with Laplace smoothing
    - average regime duration (trading days)
    - current regime as of the last bar date + recommended strategy

ASCII only. No network. stdlib + numpy.

Usage:
    python tools/research/regime-strategies.py [--db PATH] [--json OUT]
"""
import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

import numpy as np

VAULT = Path(r"/path/to/vault")
DEFAULT_DB = VAULT / "Efforts" / "osanwe-v2-overhaul" / "_work" / "factors.db"
ROOT_FALLBACK = VAULT / "factors.db"

REGIMES = ["BULL", "CORRECTION", "BEAR"]

# Exclude index/ETF proxies that would double-count broad-index exposure in
# cross-sectional sorts; keep single names + sector/asset ETFs + crypto.
XS_EXCLUDE = {
    "SPY", "VOO", "QQQ", "SMH", "SOXX",
}


def pick_db(cli_db):
    if cli_db:
        p = Path(cli_db)
        if not p.exists() or p.stat().st_size == 0:
            sys.exit(f"factors db missing or empty: {p}")
        return p
    if DEFAULT_DB.exists() and DEFAULT_DB.stat().st_size > 0:
        return DEFAULT_DB
    if ROOT_FALLBACK.exists() and ROOT_FALLBACK.stat().st_size > 0:
        return ROOT_FALLBACK
    sys.exit(
        "no populated factors.db found; run "
        "`python tools/factor-store.py --init` first"
    )


def load_bars(db_path):
    """Return {ticker: (dates list ascending, closes np.array)} for all tickers."""
    con = sqlite3.connect(str(db_path))
    try:
        rows = con.execute("SELECT ticker, date, close FROM bars ORDER BY ticker, date").fetchall()
    finally:
        con.close()
    series = {}
    cur_t = None
    dates, closes = [], []
    for t, d, c in rows:
        if t != cur_t:
            if cur_t is not None:
                series[cur_t] = (dates, np.asarray(closes, dtype=float))
            cur_t, dates, closes = t, [], []
        dates.append(d)
        closes.append(c)
    if cur_t is not None:
        series[cur_t] = (dates, np.asarray(closes, dtype=float))
    return series


def daily_returns(closes):
    r = np.full(len(closes), np.nan)
    r[1:] = closes[1:] / closes[:-1] - 1.0
    return r


def moving_average(closes, n):
    ma = np.full(len(closes), np.nan)
    if len(closes) >= n:
        csum = np.cumsum(np.insert(closes, 0, 0.0))
        ma[n - 1:] = (csum[n:] - csum[:-n]) / n
    return ma


def rsi14(closes):
    """Wilder RSI(14). NaN until index 14."""
    out = np.full(len(closes), np.nan)
    if len(closes) < 15:
        return out
    delta = np.diff(closes)
    up = np.where(delta > 0, delta, 0.0)
    dn = np.where(delta < 0, -delta, 0.0)
    au = up[:14].mean()
    ad = dn[:14].mean()
    out[14] = 100.0 if ad == 0 else 100.0 - 100.0 / (1.0 + au / ad)
    for i in range(15, len(closes)):
        au = (au * 13.0 + up[i - 1]) / 14.0
        ad = (ad * 13.0 + dn[i - 1]) / 14.0
        out[i] = 100.0 if ad == 0 else 100.0 - 100.0 / (1.0 + au / ad)
    return out


def spy_regimes(spy_dates, spy_closes):
    ma50 = moving_average(spy_closes, 50)
    ma200 = moving_average(spy_closes, 200)
    regimes = [None] * len(spy_closes)
    for i in range(len(spy_closes)):
        px = spy_closes[i]
        m50, m200 = ma50[i], ma200[i]
        if np.isnan(m50) or np.isnan(m200):
            continue
        if px < m200:
            regimes[i] = "BEAR"
        elif px > m50:
            regimes[i] = "BULL"
        else:
            regimes[i] = "CORRECTION"
    return regimes


def align_index(series):
    """Union calendar across tickers -> sorted date list."""
    all_dates = set()
    for dates, _ in series.values():
        all_dates.update(dates)
    return sorted(all_dates)


# ---------------------------------------------------------------- strategies

def strat_tsmom(spy_dates, spy_closes, cal_index):
    """Long SPY when 12m-minus-1m momentum positive; daily returns on cal."""
    r = daily_returns(spy_closes)
    sig = {}
    pos_by_date = {}
    idx_of = {d: i for i, d in enumerate(spy_dates)}
    for j, d in enumerate(cal_index):
        i = idx_of.get(d)
        if i is None or i < 253:
            continue
        mom = spy_closes[i] / spy_closes[i - 253] - 1.0
        mom1 = spy_closes[i] / spy_closes[i - 22] - 1.0
        pos_by_date[d] = 1.0 if (mom - mom1) > 0 else 0.0
    # position established on day t earns t->t+1 return: shift by one calendar slot
    rets = {}
    for k in range(len(cal_index) - 1):
        d_today, d_next = cal_index[k], cal_index[k + 1]
        pos = pos_by_date.get(d_today)
        i_next = {d: i for i, d in enumerate(spy_dates)}.get(d_next)
        if pos is None or i_next is None or i_next < 1 or np.isnan(r[i_next]):
            continue
        rets[d_next] = pos * r[i_next]
    return rets


def strat_xs_mom(series, cal_index, exclude=XS_EXCLUDE, min_hist=200, look=126,
                 q=5, rebal_freq="W"):
    """Top-quintile 126d cross-sectional momentum, equal weight.
    Positions persist daily between rebalance snapshots."""
    snap_picks = {}
    last_key = None
    for d in cal_index:
        key = d[:7] if rebal_freq == "M" else iso_week(d)
        if key != last_key:
            picks = _xs_pick(series, d, exclude, min_hist, look, q)
            if picks:
                snap_picks[d] = picks
            last_key = key
    return _persisted_daily_returns(series, cal_index, snap_picks)


def _xs_pick(series, d, exclude, min_hist, look, q):
    scores = []
    for t, (dates, closes) in series.items():
        if t in exclude or len(closes) < min_hist or len(dates) < look + 1:
            continue
        di = bisect_le(dates, d)
        if di is None or di < look:
            continue
        score = closes[di] / closes[di - look] - 1.0
        if np.isfinite(score):
            scores.append((t, score))
    if len(scores) < 20:
        return None
    scores.sort(key=lambda x: x[1], reverse=True)
    nq = max(1, len(scores) // q)
    return [t for t, _ in scores[:nq]]


def strat_meanrev(series, cal_index, max_names=5, hold_max=10, exit_rsi=50.0):
    """Enter names with RSI14 < 30 at the close; exit at RSI >= 50 or after
    hold_max trading days. Daily returns are earned from the day AFTER the
    entry close onward (no lookahead on the entry-day move)."""
    rsi_cache = {t: rsi14(c) for t, (d, c) in series.items()}
    cal_pos = {d: k for k, d in enumerate(cal_index)}
    holdings_by_date = {}
    open_pos = []  # list of [ticker, entry_cal_index]
    for k, d in enumerate(cal_index):
        # exits first (decision at today's close)
        still = []
        for (t, k_entry) in open_pos:
            dates, closes = series[t]
            i = bisect_le(dates, d)
            if i is None:
                continue
            rv = rsi_cache[t][i]
            if (np.isfinite(rv) and rv >= exit_rsi) or (k - k_entry) >= hold_max:
                continue
            still.append([t, k_entry])
        open_pos = still
        # entries at today's close (earn returns starting tomorrow)
        slots = max_names - len(open_pos)
        if slots > 0:
            oversold = []
            for t, (dates, closes) in series.items():
                if any(p[0] == t for p in open_pos) or len(closes) < 30:
                    continue
                i = bisect_le(dates, d)
                if i is None:
                    continue
                rv = rsi_cache[t][i]
                if np.isfinite(rv) and rv < 30.0:
                    oversold.append((rv, t))
            oversold.sort()
            for _, t in oversold[:slots]:
                open_pos.append([t, k])
        if open_pos:
            holdings_by_date[d] = [p[0] for p in open_pos]
    # daily returns: holdings chosen at close of d earn the d -> d_next move
    rets = {}
    for k in range(len(cal_index) - 1):
        d_today, d_next = cal_index[k], cal_index[k + 1]
        picks = holdings_by_date.get(d_today)
        if not picks:
            continue
        day_rets = []
        for t in picks:
            dates, closes = series[t]
            i = bisect_le(dates, d_next)
            j = bisect_le(dates, d_today)
            if i is None or j is None or i <= j:
                continue
            rr = closes[i] / closes[j] - 1.0
            if np.isfinite(rr):
                day_rets.append(rr)
        if day_rets:
            rets[d_next] = float(np.mean(day_rets))
    return rets


def strat_lowvol_q1(series, cal_index, exclude=XS_EXCLUDE, min_hist=80,
                    vol_win=60, q=5, rebal_freq="M"):
    """Bottom-quintile 60d vol, equal weight, monthly rebalance; positions
    persist daily between rebalance snapshots."""
    snap_picks = {}
    last_key = None
    for d in cal_index:
        key = d[:7]
        if key != last_key:
            vols = []
            for t, (dates, closes) in series.items():
                if t in exclude or len(closes) < min_hist + vol_win:
                    continue
                i = bisect_le(dates, d)
                if i is None or i < vol_win:
                    continue
                w = closes[i - vol_win:i + 1]
                r = w[1:] / w[:-1] - 1.0
                sd = float(np.std(r, ddof=1))
                if np.isfinite(sd) and sd > 0:
                    vols.append((t, sd))
            picks = None
            if len(vols) >= 20:
                vols.sort(key=lambda x: x[1])
                nq = max(1, len(vols) // q)
                picks = [t for t, _ in vols[:nq]]
            if picks:
                snap_picks[d] = picks
            last_key = key
    return _persisted_daily_returns(series, cal_index, snap_picks)


def _persisted_daily_returns(series, cal_index, port_by_date):
    """Holdings picked at close of rebalance day persist daily (carry-forward)
    until the next rebalance; each held day earns the d -> d_next move."""
    rets = {}
    current = []
    for k in range(len(cal_index) - 1):
        d_today, d_next = cal_index[k], cal_index[k + 1]
        if d_today in port_by_date:
            current = port_by_date[d_today]
        if not current:
            continue
        day_rets = []
        for t in current:
            dates, closes = series[t]
            i = bisect_le(dates, d_next)
            j = bisect_le(dates, d_today)
            if i is None or j is None or i <= j:
                continue
            rr = closes[i] / closes[j] - 1.0
            if np.isfinite(rr):
                day_rets.append(rr)
        if len(day_rets) >= max(1, int(0.6 * len(current))):
            rets[d_next] = float(np.mean(day_rets))
    return rets


# ------------------------------------------------------------------ helpers

def iso_week(datestr):
    import datetime as _dt
    y, m, dd = map(int, datestr.split("-"))
    return "%04d-W%02d" % (*_dt.date(y, m, dd).isocalendar()[:1],
                           _dt.date(y, m, dd).isocalendar()[1])


def bisect_le(sorted_list, x):
    """Index of largest element <= x, else None."""
    lo, hi = 0, len(sorted_list)
    while lo < hi:
        mid = (lo + hi) // 2
        if sorted_list[mid] <= x:
            lo = mid + 1
        else:
            hi = mid
    return lo - 1 if lo > 0 else None


def trading_day_gap(dates, i_now, i_entry):
    if i_entry is None or i_now < i_entry:
        return 0
    return i_now - i_entry


# ------------------------------------------------------------- stats blocks

def perf_stats(rets_by_date):
    """rets_by_date: {date: decimal daily return}."""
    items = sorted(rets_by_date.items())
    if len(items) < 30:
        return {"days": len(items)}
    arr = np.asarray([r for _, r in items])
    mean_d = float(arr.mean())
    vol_d = float(arr.std(ddof=1))
    ann_ret = mean_d * 252.0
    ann_vol = vol_d * np.sqrt(252.0)
    sharpe = (mean_d / vol_d) * np.sqrt(252.0) if vol_d > 0 else float("nan")
    hit = float((arr > 0).mean())
    cum = float(np.prod(1.0 + arr) - 1.0)
    peak = np.maximum.accumulate(np.cumprod(1.0 + arr))
    dd = float(((np.cumprod(1.0 + arr)) / peak - 1.0).min())
    return {
        "days": int(len(arr)),
        "mean_daily_pct": round(mean_d * 100.0, 4),
        "ann_pct": round(ann_ret * 100.0, 2),
        "ann_vol_pct": round(ann_vol * 100.0, 2),
        "sharpe": round(float(sharpe), 3),
        "hit_rate_pct": round(hit * 100.0, 1),
        "cum_pct": round(cum * 100.0, 1),
        "maxdd_pct": round(dd * 100.0, 1),
    }


def regime_matrix(rets_by_date, regimes_by_date):
    cells = {}
    for d, r in rets_by_date.items():
        g = regimes_by_date.get(d)
        if g is None:
            continue
        cells.setdefault(g, []).append(r)
    out = {}
    for g in REGIMES:
        vals = cells.get(g, [])
        if len(vals) < 20:
            out[g] = {"days": len(vals)}
            continue
        arr = np.asarray(vals)
        mean_d = float(arr.mean())
        vol_d = float(arr.std(ddof=1))
        out[g] = {
            "days": int(len(arr)),
            "mean_daily_pct": round(mean_d * 100.0, 4),
            "ann_pct": round(mean_d * 252.0 * 100.0, 2),
            "ann_vol_pct": round(vol_d * np.sqrt(252.0) * 100.0, 2),
            "sharpe": round(mean_d / vol_d * np.sqrt(252.0), 3) if vol_d > 0 else None,
            "hit_rate_pct": round(float((arr > 0).mean()) * 100.0, 1),
            "t_stat_vs_0": round(mean_d / (vol_d / np.sqrt(len(arr))), 2) if vol_d > 0 else None,
        }
    return out


def transitions(regime_seq):
    counts = {a: {b: 0 for b in REGIMES} for a in REGIMES}
    for a, b in zip(regime_seq[:-1], regime_seq[1:]):
        counts[a][b] += 1
    probs = {}
    for a in REGIMES:
        tot = sum(counts[a].values())
        probs[a] = {
            b: round((counts[a][b] + 1.0) / (tot + len(REGIMES)), 4)  # Laplace
            for b in REGIMES
        }
        probs[a]["_n"] = tot
    return probs, counts


def durations(regime_seq):
    runs = []
    cur, n = regime_seq[0], 1
    for g in regime_seq[1:]:
        if g == cur:
            n += 1
        else:
            runs.append((cur, n))
            cur, n = g, 1
    runs.append((cur, n))
    avg = {}
    for g in REGIMES:
        lens = [n for gg, n in runs if gg == g]
        avg[g] = {
            "episodes": len(lens),
            "avg_trading_days": round(float(np.mean(lens)), 1) if lens else 0,
            "median_trading_days": float(np.median(lens)) if lens else 0,
            "max_trading_days": max(lens) if lens else 0,
        }
    return avg, runs


# --------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    ap.add_argument("--json", default=None, help="optional path to dump results JSON")
    args = ap.parse_args()

    db_path = pick_db(args.db)
    print(f"[db] {db_path}")

    series = load_bars(db_path)
    spy_dates, spy_closes = series["SPY"]
    print(f"[bars] {len(series)} tickers, SPY {spy_dates[0]}..{spy_dates[-1]} ({len(spy_dates)} bars)")

    regimes = spy_regimes(spy_dates, spy_closes)
    regimes_by_date = {d: g for d, g in zip(spy_dates, regimes) if g}

    # Regime shares over the evaluable span
    reg_counter = Counter(g for g in regimes if g)
    total_reg = sum(reg_counter.values())
    print("\n== REGIME DEFINITION ON SPY ==")
    for g in REGIMES:
        pct = 100.0 * reg_counter[g] / total_reg
        print(f"  {g:<11} {reg_counter[g]:>5} days ({pct:.1f}%)")

    cal_index = align_index(series)

    print("\n== COMPUTING STRATEGY DAILY RETURNS ==")
    strat = {}
    strat["TSMOM"] = strat_tsmom(spy_dates, spy_closes, cal_index)
    print(f"  TSMOM      {len(strat['TSMOM'])} days")
    strat["XS_MOM"] = strat_xs_mom(series, cal_index)
    print(f"  XS_MOM     {len(strat['XS_MOM'])} days")
    strat["MEANREV"] = strat_meanrev(series, cal_index)
    print(f"  MEANREV    {len(strat['MEANREV'])} days")
    strat["LOWVOL_Q1"] = strat_lowvol_q1(series, cal_index)
    print(f"  LOWVOL_Q1  {len(strat['LOWVOL_Q1'])} days")

    print("\n== STRATEGY x REGIME MATRIX (daily % / ann % / Sharpe / days) ==")
    header = f"{'strategy':<11}" + "".join(f"{g:>28}" for g in REGIMES) + f"{'ALL':>26}"
    print(header)
    results = {}
    for name in ["TSMOM", "XS_MOM", "MEANREV", "LOWVOL_Q1"]:
        overall = perf_stats(strat[name])
        by_reg = regime_matrix(strat[name], regimes_by_date)
        results[name] = {"overall": overall, "by_regime": by_reg}
        row = f"{name:<11}"
        for g in REGIMES:
            c = by_reg[g]
            if "sharpe" not in c:
                row += f"{'insufficient data':>28}"
            else:
                row += (f"{c['mean_daily_pct']:>+8.3f}/{c['ann_pct']:>+7.1f}/"
                        f"{c['sharpe']:>+6.2f}({c['days']:>4}d)")
        o = overall
        row += (f"{o.get('mean_daily_pct', 0):>+9.3f}/{o.get('ann_pct', 0):>+7.1f}/"
                f"{o.get('sharpe', float('nan')):>+6.2f}")
        print(row)

    print("\n== TRANSITION MATRIX P(next | current) (Laplace-smoothed) ==")
    seq = [g for g in regimes if g]
    probs, counts = transitions(seq)
    hdr = "from\\to"
    print(f"  {hdr:<13}" + "".join(f"{g:>12}" for g in REGIMES))
    for a in REGIMES:
        row = f"  {a:<13}"
        for b in REGIMES:
            row += f"{probs[a][b]:>12.3f}"
        print(row + f"   n={probs[a]['_n']}")

    dur, runs = durations(seq)
    print("\n== REGIME DURATION (trading days) ==")
    for g in REGIMES:
        d = dur[g]
        print(f"  {g:<11} episodes={d['episodes']:>3}  avg={d['avg_trading_days']:>6.1f}"
              f"  median={d['median_trading_days']:>6.1f}  max={d['max_trading_days']:>4}")

    # Current regime
    last_i = len(regimes) - 1
    cur_regime = regimes[last_i]
    cur_date = spy_dates[last_i]
    ma50v = moving_average(spy_closes, 50)[last_i]
    ma200v = moving_average(spy_closes, 200)[last_i]
    px = spy_closes[last_i]
    print("\n== CURRENT STATE ==")
    print(f"  as-of {cur_date}: SPY {px:.2f} | MA50 {ma50v:.2f} | MA200 {ma200v:.2f}"
          f" | vsMA200 {(px / ma200v - 1) * 100:+.1f}% | vsMA50 {(px / ma50v - 1) * 100:+.1f}%")
    print(f"  CURRENT REGIME: {cur_regime}")
    nxt = probs[cur_regime]
    print(f"  next-day transition odds from {cur_regime}: "
          + ", ".join(f"{b} {nxt[b]*100:.1f}%" for b in REGIMES))

    # Recommendation: best strategy by Sharpe within current regime (min 60 obs)
    ranked = []
    for name in results:
        c = results[name]["by_regime"].get(cur_regime, {})
        if c.get("sharpe") is not None and c.get("days", 0) >= 60:
            ranked.append((c["sharpe"], c["ann_pct"], name))
    ranked.sort(reverse=True)
    print("\n== RECOMMENDATION FOR CURRENT REGIME ==")
    if ranked:
        best = ranked[0]
        print(f"  Best in-regime Sharpe: {best[2]} (Sharpe {best[0]:+.2f}, ann {best[1]:+.1f}%)")
        print(f"  Ranking: {' > '.join(n for _, _, n in ranked)}")

    if args.json:
        payload = {
            "asof": cur_date,
            "db": str(db_path),
            "current_regime": cur_regime,
            "spy_px": float(px),
            "spy_ma50": float(ma50v),
            "spy_ma200": float(ma200v),
            "regime_shares": {g: round(100.0 * reg_counter[g] / total_reg, 2) for g in REGIMES},
            "strategies": results,
            "transition_probs": probs,
            "transition_counts": counts,
            "durations": dur,
            "recommendation_ranking": [
                {"strategy": n, "sharpe": s, "ann_pct": a} for s, a, n in ranked
            ],
        }
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(payload, indent=2), encoding="ascii")
        print(f"\n[json] wrote {args.json}")


if __name__ == "__main__":
    main()
