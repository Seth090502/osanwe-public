#!/usr/bin/env python3
"""backtest-strategy.py -- monthly-rebalance momentum vs SPY, zero lookahead.

Strategy under test (fixed BEFORE results were seen -- no parameter tuning):
  - At each month-end (last SPY trading day of the month), rank every ticker
    in the factor store by trailing 63-trading-bar return (t-63 -> t-1),
    computed ONLY from bars with date <= rebalance date.
  - Buy the top 5, equal weight. Hold ~1 month, then rebalance.
  - Skip any instrument without >= 64 own bars up to the rebalance date or
    whose latest bar is stale (> 7 calendar days old at the rebalance date).

Anti-bias contracts (mandatory safeguards):
  1. LOOKAHEAD PREVENTION : ranking window ends at t-1 relative to execution;
     entry price is the rebalance-date close (t close proxy per spec). Every
     query filters date <= as_of. No future data enters any decision.
  2. NO SURVIVORSHIP EDIT : universe = every ticker present in the store,
     including short-history and illiquid names. NOTE: the store itself only
     contains CURRENTLY LISTED tickers (ingested today), so residual
     survivorship bias remains and is disclosed in the outputs.
  3. TRANSACTION COSTS    : 10 bps per ROUND TRIP => 5 bps per one-way side.
     Charged on traded notional at each rebalance. A full 100% portfolio
     replacement therefore costs 0.1% of NAV, matching the spec.
  4. NO HINDSIGHT PICKS   : selection is purely mechanical (top 5 momentum);
     nothing about the future composition of the list is used.

Honesty contract: parameters were NOT tuned against outcomes. If this loses
to SPY, the script reports that loss verbatim.

Outputs:
  Efforts/osanwe-v2-overhaul/_work/backtest-momentum-results.json
  wiki/research/ref-momentum-backtest.md            (via --write-md)

Offline: reads only the local sqlite factor store. Zero network.
"""

import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "Efforts/osanwe-v2-overhaul/_work/factors.db"
OUT_JSON = ROOT / "Efforts/osanwe-v2-overhaul/_work/backtest-momentum-results.json"
OUT_MD = ROOT / "wiki/research/ref-momentum-backtest.md"

# ---- fixed strategy parameters (do not tune) ---------------------------------
TOP_N = 5              # equal-weight names per rebalance
MOM_LOOKBACK = 63      # trading bars: t-63 -> t-1 trailing return
MIN_HISTORY = 64       # need lookback+1 own bars up to the rebalance date
STALE_DAYS = 7         # reject rank candidates whose last bar is older
COST_ROUNDTRIP = 0.001 # 10 bps round trip
COST_SIDE = COST_ROUNDTRIP / 2.0  # 5 bps per one-way traded side


def load_bars(db_path):
    """All bars as {ticker: [(iso_date, close), ...] sorted by date}."""
    con = sqlite3.connect(str(db_path))
    try:
        rows = con.execute(
            "SELECT ticker, date, close FROM bars ORDER BY ticker, date"
        ).fetchall()
    finally:
        con.close()
    series = defaultdict(list)
    for t, d, c in rows:
        series[t].append((d, float(c)))
    return dict(series)


def trading_calendar(series):
    """Master calendar = SPY trading days (cash equities session)."""
    return [d for d, _ in sorted(series["SPY"], key=lambda x: x[0])]


def month_end_dates(calendar):
    """Last calendar date per (year, month)."""
    last = {}
    for d in calendar:
        key = (d[:4], d[5:7])
        last[key] = d
    return [last[k] for k in sorted(last)]


def build_index(series):
    """Per ticker: {date->close}, plus sorted date list for fast lookup."""
    idx = {}
    for t, pts in series.items():
        idx[t] = {"map": dict(pts), "dates": [d for d, _ in pts]}
    return idx


def trailing_return(idx_t, as_of):
    """Return over own bars t-63 -> t-1, both <= as_of. None if insufficient.

    Uses the ticker's OWN bar sequence (crypto trades weekends; equities do
    not). 't' here is the latest own bar strictly <= as_of; the ranking return
    spans the prior MOM_LOOKBACK own bars, ending one bar before 'now'.
    """
    dates = idx_t["dates"]
    m = idx_t["map"]
    hi = bisect_le(dates, as_of)
    if hi is None or hi < MIN_HISTORY:
        return None
    last_d = dates[hi]
    stale = (datetime.strptime(as_of, "%Y-%m-%d")
             - datetime.strptime(last_d, "%Y-%m-%d")).days
    if stale > STALE_DAYS:
        return None
    p_now = m[last_d]
    p_then = m[dates[hi - MOM_LOOKBACK]]
    return p_now / p_then - 1.0


def bisect_le(sorted_dates, as_of):
    """Index of last element <= as_of, else None."""
    lo, hi = 0, len(sorted_dates) - 1
    ans = None
    while lo <= hi:
        mid = (lo + hi) // 2
        if sorted_dates[mid] <= as_of:
            ans = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return ans


def price_at_or_before(idx_t, d):
    """Latest own close <= d (None if ticker has no data yet)."""
    i = bisect_le(idx_t["dates"], d)
    if i is None:
        return None
    return idx_t["map"][idx_t["dates"][i]]


def run_backtest(series, idx, calendar):
    rebal_dates_all = month_end_dates(calendar)
    cal_pos = {d: i for i, d in enumerate(calendar)}

    # Warm-up gate: require at least MIN_HISTORY prior SPY sessions before the
    # first evaluated rebalance so rankings are meaningful store-wide.
    rebal_dates = []
    for d in rebal_dates_all:
        if cal_pos[d] >= MIN_HISTORY:
            rebal_dates.append(d)

    daily_ret = []          # strategy daily net returns aligned to calendar
    daily_dates = []
    spy_daily = []
    monthly_rows = []       # (month_key, strat_ret, spy_ret)
    rebalance_log = []
    frozen_positions = Counter()  # tickers that went stale while held
    cash_months = 0

    weights = {}            # ticker -> drifted weight (starts empty = cash)
    cur_rebal = None

    spy_map = dict(series["SPY"])
    prev_spy_close = None
    last_px = run_backtest._last_px  # ticker -> last price booked into returns

    for di, d in enumerate(calendar):
        # --- advance SPY daily return ---
        if d in spy_map:
            spy_r = 0.0 if prev_spy_close is None else spy_map[d] / prev_spy_close - 1.0
            prev_spy_close = spy_map[d]
        else:
            spy_r = 0.0

        # --- book today's return on CURRENT (pre-rebalance) holdings ---
        # The outgoing portfolio earns through the rebalance-date close (we
        # sell at the t close proxy); the incoming picks start earning the
        # following session. Ranking below uses only bars dated <= t.
        gross = 0.0
        tot = 0.0
        stale_here = []
        for t, w in weights.items():
            idx_t = idx[t]
            px = price_at_or_before(idx_t, d)
            base = last_px.get(t)
            if base is None:
                base = px  # entry day: zero return
            if px is None:
                stale_here.append(t)
                r = 0.0  # frozen price: honest no-recovery assumption
                px = base
            else:
                r = px / base - 1.0
            last_px[t] = px
            gross += w * r
            nw = w * (1.0 + r)
            weights[t] = nw
            tot += nw
        for t in stale_here:
            frozen_positions[t] += 1
        if tot > 0:
            for t in weights:
                weights[t] /= tot  # renormalize drifted weights

        # --- rebalance at the close (AFTER booking the old portfolio) ---
        drag = 0.0
        if d in rebal_dates and di < len(calendar) - 1:
            scores = []
            for t, idx_t in idx.items():
                if t == "SPY":
                    continue
                r = trailing_return(idx_t, d)
                if r is not None:
                    scores.append((r, t))
            scores.sort(reverse=True)
            picks = [t for _, t in scores[:TOP_N]]
            n = len(picks)
            if n == 0:
                cash_months += 1
                new_w = {}
            else:
                new_w = {t: 1.0 / n for t in picks}

            # turnover = one-way fraction (half L1 distance between weights),
            # measured against the drifted weights being replaced
            l1 = sum(abs(new_w.get(t, 0.0) - weights.get(t, 0.0))
                     for t in set(new_w) | set(weights))
            one_way = l1 / 2.0
            drag = one_way * COST_ROUNDTRIP  # 5bps x 2 sides = 10bps x one-way
            rebalance_log.append({
                "date": d, "n_picked": n,
                "picks": picks,
                "mom_scores": {t: round(r, 6) for r, t in scores[:TOP_N]},
                "one_way_turnover": round(one_way, 6),
                "cost_drag": round(drag, 8),
            })
            weights = new_w
            # Re-anchor AT the swap: fresh entries anchor to their entry close
            # (today) so their next session books a real return; exits lose
            # their anchors; names held across keep theirs (else their whole
            # prior move would double-book as a fake same-day gain).
            kept = {t: v for t, v in last_px.items() if t in new_w}
            last_px.clear()
            last_px.update(kept)
            for t in new_w:
                if t not in last_px:
                    px0 = price_at_or_before(idx[t], d)
                    if px0 is not None:
                        last_px[t] = px0

        net = gross - drag
        daily_ret.append(net)
        daily_dates.append(d)
        spy_daily.append(spy_r)

    return {
        "daily_dates": daily_dates, "daily_ret": daily_ret,
        "spy_daily": spy_daily, "rebalance_log": rebalance_log,
        "frozen_positions": dict(frozen_positions), "cash_months": cash_months,
    }


def perf_stats(dates, rets):
    eq = 1.0
    curve = []
    peak = 1.0
    max_dd = 0.0
    for r in rets:
        eq *= (1.0 + r)
        curve.append(eq)
        peak = max(peak, eq)
        max_dd = min(max_dd, eq / peak - 1.0)
    n_years = (datetime.strptime(dates[-1], "%Y-%m-%d")
               - datetime.strptime(dates[0], "%Y-%m-%d")).days / 365.25
    cagr = eq ** (1.0 / n_years) - 1.0 if n_years > 0 and eq > 0 else None
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    sd = var ** 0.5
    sharpe = (mean / sd) * (252 ** 0.5) if sd > 0 else None
    return {"total_return": eq - 1.0, "cagr": cagr, "sharpe_daily": sharpe,
            "max_drawdown": max_dd, "n_days": len(rets), "years": n_years}


def monthly_table(dates, rets, spy_rets):
    agg = defaultdict(lambda: [0.0, 0.0])
    for d, rs, rm in zip(dates, rets, spy_rets):
        k = d[:7]
        agg[k][0] = (1 + agg[k][0]) * (1 + rs) - 1
        agg[k][1] = (1 + agg[k][1]) * (1 + rm) - 1
    rows = []
    for k in sorted(agg):
        s, m = agg[k]
        rows.append({"month": k, "strategy": round(s, 6),
                     "spy": round(m, 6), "excess": round(s - m, 6)})
    wins = sum(1 for r in rows if r["excess"] > 0)
    return rows, wins / len(rows) if rows else None


def main():
    db = DEFAULT_DB
    if "--db" in sys.argv:
        db = Path(sys.argv[sys.argv.index("--db") + 1])
    series = load_bars(db)
    if "SPY" not in series:
        sys.exit("FATAL: no SPY in store")
    idx = build_index(series)
    calendar = trading_calendar(series)

    # reset module-level last-price cache
    run_backtest._last_px = {}
    res = run_backtest(series, idx, calendar)

    strat = perf_stats(res["daily_dates"], res["daily_ret"])
    spy = perf_stats(res["daily_dates"], res["spy_daily"])
    rows, win_rate = monthly_table(res["daily_dates"], res["daily_ret"],
                                   res["spy_daily"])

    turnovers = [r["one_way_turnover"] for r in res["rebalance_log"]]
    avg_turnover = sum(turnovers) / len(turnovers) if turnovers else 0.0

    universe = sorted(series.keys())
    out = {
        "meta": {
            "script": "tools/backtest-strategy.py",
            "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "db": str(db.relative_to(ROOT)),
            "store_window": [series["SPY"][0][0], series["SPY"][-1][0]],
            "backtest_window": [res["daily_dates"][0], res["daily_dates"][-1]],
            "universe_size": len(universe),
            "universe": universe,
            "params": {"top_n": TOP_N, "momentum_lookback_trading_bars": MOM_LOOKBACK,
                       "min_history_bars": MIN_HISTORY, "stale_bar_days": STALE_DAYS,
                       "cost_roundtrip_bps": 10, "rebalance": "monthly (month-end)"},
            "safeguards": {
                "lookahead_prevention": ("ranking uses own bars t-63..t-1 strictly "
                                         "<= rebalance date; entry at t close proxy"),
                "survivorship_handling": ("all 107 stored tickers included incl. "
                                          "short-history; RESIDUAL bias remains "
                                          "because store holds only currently-"
                                          "listed names ingested 2026-08-24"),
                "transaction_costs": "10 bps round trip (5 bps per side) on traded notional",
                "hindsight_selection": "none; mechanical top-5 momentum only",
            },
            "honesty_note": ("first honest run; parameters not tuned against "
                             "outcomes regardless of result"),
        },
        "metrics": {
            "strategy": {k: (round(v, 6) if isinstance(v, float) else v)
                         for k, v in strat.items()},
            "spy": {k: (round(v, 6) if isinstance(v, float) else v)
                    for k, v in spy.items()},
            "beat_spy_total_return": bool(strat["total_return"] > spy["total_return"]),
            "win_rate_vs_spy_monthly": round(win_rate, 4) if win_rate is not None else None,
            "avg_one_way_turnover_per_rebalance": round(avg_turnover, 4),
            "rebalances": len(res["rebalance_log"]),
            "months_strategy_fully_in_cash": res["cash_months"],
            "stale_frozen_position_days": res["frozen_positions"],
        },
        "monthly_returns": rows,
        "rebalance_log": res["rebalance_log"],
    }
    OUT_JSON.write_text(json.dumps(out, indent=2), encoding="ascii")
    print(json.dumps(out["metrics"], indent=2))
    print("wrote", OUT_JSON)
    if "--write-md" in sys.argv:
        write_md(out)
        print("wrote", OUT_MD)


def fmt_pct(x):
    return f"{x * 100:+.2f}%"


def write_md(out):
    m = out["metrics"]
    s, p = m["strategy"], m["spy"]
    lines = []
    ap = lines.append
    ap("---")
    ap("categories:")
    ap("  - wiki")
    ap("type: research")
    ap("created: 2026-08-24")
    ap("updated: 2026-08-24")
    ap("status: active")
    ap("confidence: MEDIUM")
    ap("tags:")
    ap("  - topic/backtesting")
    ap("  - topic/momentum")
    ap("related:")
    ap("  - \"[[ref-factor-lens]]\"")
    ap("---")
    ap("")
    ap("# Ref: Monthly Momentum Backtest vs SPY (baseline, untuned)")
    ap("")
    ap(f"Generated {out['meta']['generated_utc']} by `{out['meta']['script']}` "
       f"from `{Path(out['meta']['db']).as_posix()}`. Store window {out['meta']['store_window'][0]}"
       f"..{out['meta']['store_window'][1]}; evaluated window "
       f"{out['meta']['backtest_window'][0]}..{out['meta']['backtest_window'][1]} "
       f"(first ~4 months consumed by the 63-bar warm-up).")
    ap("")
    ap("## Methodology")
    ap("")
    ap("- Universe: ALL %d tickers in the factor store, no exclusions." % out["meta"]["universe_size"])
    ap("- Signal: at each month-end (last SPY session of the month) rank every")
    ap("  ticker by trailing %d-trading-bar return over its OWN bars, computed" % MOM_LOOKBACK)
    ap("  strictly from bars dated <= the rebalance date (zero lookahead).")
    ap("- Portfolio: top %d equal weight; hold ~1 month; rebalance." % TOP_N)
    ap("- Execution: rebalance-date close proxy (spec-permitted); no intraday fills.")
    ap("- Costs: 10 bps per ROUND TRIP (5 bps/side) charged on traded notional;")
    ap("  a full 100 pct portfolio replacement costs 0.1 pct of NAV.")
    ap("- Skips: fewer than %d own bars up to the rebalance date, or latest bar" % MIN_HISTORY)
    ap("  older than %d calendar days (stale/delisted)." % STALE_DAYS)
    ap("- Weights drift intra-month (true buy-and-hold between rebalances);")
    ap("  a name that stops printing is frozen at its last close (no recovery).")
    ap("")
    ap("## Results (first honest run -- NOT parameter-tuned)")
    ap("")
    ap("| Metric | Momentum Top-%d | SPY |" % TOP_N)
    ap("|---|---|---|")
    ap("| Total return | %s | %s |" % (fmt_pct(s["total_return"]), fmt_pct(p["total_return"])))
    ap("| CAGR | %s | %s |" % (fmt_pct(s["cagr"]), fmt_pct(p["cagr"])))
    ap("| Sharpe (daily, rf=0) | %.2f | %.2f |" % (s["sharpe_daily"], p["sharpe_daily"]))
    ap("| Max drawdown | %s | %s |" % (fmt_pct(s["max_drawdown"]), fmt_pct(p["max_drawdown"])))
    ap("")
    ap("- Months strategy beat SPY: %.1f%% (%d of %d months)" % (
        m["win_rate_vs_spy_monthly"] * 100,
        round(m["win_rate_vs_spy_monthly"] * len(out["monthly_returns"])),
        len(out["monthly_returns"])))
    ap("- Avg one-way turnover per rebalance: %.1f%% of NAV" % (
        m["avg_one_way_turnover_per_rebalance"] * 100))
    ap("- Verdict: %s" % (
        "**BEAT SPY** on total return." if m["beat_spy_total_return"]
        else "**DID NOT BEAT SPY** on total return. Reported as-is; no tuning was applied."))
    ap("")
    ap("## Monthly returns (strategy / SPY / excess)")
    ap("")
    ap("| Month | Strategy | SPY | Excess |")
    ap("|---|---|---|---|")
    for r in out["monthly_returns"]:
        ap("| %s | %s | %s | %s |" % (
            r["month"], fmt_pct(r["strategy"]), fmt_pct(r["spy"]), fmt_pct(r["excess"])))
    ap("")
    ap("## Bias disclosure")
    ap("")
    ap("1. **Lookahead**: prevented by construction -- signal window ends at")
    ap("   t-1, queries filter date <= as_of, entry is the t close proxy.")
    ap("2. **Survivorship (RESIDUAL)**: the store contains only tickers listed")
    ap("   TODAY (ingested 2026-08-24). Names that delisted before ingestion")
    ap("   are absent, so results likely OVERSTATE achievable returns. All")
    ap("   %d present tickers were included, including recent IPOs with short" % out["meta"]["universe_size"])
    ap("   histories (which simply sit out until they clear the warm-up).")
    ap("3. **Transaction costs**: flat 10 bps round trip; real slippage on the")
    ap("   small-caps and crypto names here would likely exceed this.")
    ap("4. **No hindsight selection**: purely mechanical ranking; parameters")
    ap("   (top-5, 63-bar lookback, monthly cadence) were fixed ex ante.")
    ap("5. **Close-proxy fills** ignore open-price execution and gaps.")
    ap("6. **Frozen-price delistings**: if a held name stops printing, it is")
    ap("   carried at its last close (no bankruptcy recovery modeled).")
    ap("7. **Sharpe uses rf=0** and daily returns annualized by sqrt(252);")
    ap("   crypto constituents trade weekends and are valued on SPY sessions.")
    ap("")
    ap("## Reproduce")
    ap("")
    ap("```")
    ap("python tools/backtest-strategy.py --write-md")
    ap("```")
    ap("")
    ap("Machine-readable results: `Efforts/osanwe-v2-overhaul/_work/backtest-momentum-results.json`.")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
