#!/usr/bin/env python
"""FIS M1: INDEPENDENT reproduction + hardening of exp-mean-reversion.

Written fresh by the FIS cold-start audit (2026-08-25). Deliberately differs
from tools/research/mean-reversion.py in accounting and inference while
reproducing the SAME strategy definition (RSI<30 enter / >50 exit / 10d max,
next-close fill, re-arm rule, class-prior round-trip costs):

  1. Date-keyed joins were the INTENT and are not what the code does
     (corrected 2026-09-21): book_true_marks() and _close_at() index each
     ticker's closes by position within that ticker's own history, so a
     ticker with a missing bar is silently offset against the others. Treat
     the cross-ticker alignment as positional until this is repaired.
  2. True close-based mark-to-market book (no linear interpolation of
     intra-trade returns -- the original interpolates, which mechanically
     smooths volatility and inflates Sharpe).
  3. Finite-capital slot models (K=5/10/20) -- signals skipped when no slot
     free -- plus an unbounded true-mark variant isolating the interpolation
     effect alone.
  4. Unsalted, documented RNG for the random-entry control (original salts
     with hash(ticker), which is nondeterministic across PYTHONHASHSEED).
  5. Inference on the DAILY BOOK series: Newey-West t-stat (lag 10) and
     stationary block bootstrap (expected block 20, 2000 draws) for Sharpe /
     CAGR CIs. Per-trade iid t reported for comparison only.
  6. Stress grid: entry delay t+2, doubled costs, 2022-only subperiod,
     last-12m pseudo-OOS tail, listing-cohort splits (survivorship probe),
     and a 30-seed random-control distribution.

Outputs: stdout tables + JSON at
Efforts/osanwe-v2-overhaul/_work/fis-baseline/independent-mr-results.json

ASCII only. No network. sqlite3 read-only.
"""

from __future__ import annotations

import importlib.util
import json
import math
import os
import random
import sqlite3
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_DEFAULT = os.path.join(VAULT, "Efforts", "osanwe-v2-overhaul", "_work", "factors.db")
OUT_JSON = os.path.join(VAULT, "Efforts", "osanwe-v2-overhaul", "_work",
                        "fis-baseline", "independent-mr-results.json")

_ecm_path = os.path.join(VAULT, "tools", "execution-cost-model.py")
_spec = importlib.util.spec_from_file_location("execution_cost_model", _ecm_path)
ecm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ecm)

ADR_TICKERS = {"TSM", "ASML", "ABBNY", "ATEYY", "ASMIY"}
MIN_BARS = 1000
RSI_PERIOD = 14


def load_universe(db_path):
    con = sqlite3.connect("file:%s?mode=ro" % db_path.replace("\\", "/"), uri=True)
    rows = con.execute("SELECT ticker, date, close FROM bars ORDER BY ticker, date").fetchall()
    srcs = [r[0] for r in con.execute("SELECT DISTINCT src FROM bars").fetchall()]
    con.close()
    data = {}
    for tk, d, c in rows:
        tk = tk.upper()
        if "-USD" in tk or tk in ADR_TICKERS:
            continue
        data.setdefault(tk, {"dates": [], "closes": []})
        data[tk]["dates"].append(d)
        data[tk]["closes"].append(float(c))
    data = {tk: v for tk, v in data.items() if len(v["closes"]) > MIN_BARS}
    return data, srcs


def rsi_series(closes, period=RSI_PERIOD):
    n = len(closes)
    out = [None] * n
    if n <= period:
        return out
    g = l = 0.0
    for i in range(1, period + 1):
        d = closes[i] - closes[i - 1]
        g += max(d, 0.0)
        l += max(-d, 0.0)
    ag, al = g / period, l / period
    out[period] = 100.0 if al == 0 else 100.0 - 100.0 / (1.0 + ag / al)
    for i in range(period + 1, n):
        d = closes[i] - closes[i - 1]
        ag = (ag * (period - 1) + max(d, 0.0)) / period
        al = (al * (period - 1) + max(-d, 0.0)) / period
        out[i] = 100.0 if al == 0 else 100.0 - 100.0 / (1.0 + ag / al)
    return out


def gen_trades(closes, rsis, entry_thr=30, exit_lvl=50, max_hold=10,
               cost_rt_bp=0.0, rng=None, delay=1):
    """Candidate trades per ticker, identical rules to the original script.

    Returns list of dicts: sig_i, entry_i, exit_i, gross, net, hold_days.
    rng set -> random entries matched to deterministic signal count
    (UNSALTED seed supplied by caller).
    """
    n = len(closes)
    trades = []
    armed = True
    signal_days = None
    if rng is not None:
        sig_count = sum(1 for t in range(RSI_PERIOD, n - 1)
                        if rsis[t] is not None and rsis[t] < entry_thr)
        pool = list(range(RSI_PERIOD + 1, n - 2))
        rng.shuffle(pool)
        signal_days = sorted(pool[:sig_count])
    i = 0
    while i < n - 1:
        if signal_days is not None:
            fire = i in signal_days
        else:
            fire = (rsis[i] is not None and armed and rsis[i] < entry_thr)
        if not fire:
            if rsis[i] is not None and rsis[i] >= entry_thr:
                armed = True
            i += 1
            continue
        entry = i + delay
        if entry >= n:
            break
        exit_i = None
        j = entry + 1
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
            exit_i = n - 1
        gross = closes[exit_i] / closes[entry] - 1.0
        net = gross - cost_rt_bp / 10000.0
        trades.append({"sig": i, "e": entry, "x": exit_i,
                       "gross": gross, "net": net, "hold": exit_i - i})
        i = exit_i
        armed = False
    return trades


# ------------------------------------------------------------------
# Accounting models
# ------------------------------------------------------------------

def book_original_ew(trades_by_tk, lengths):
    """Original accounting: EW of open trades, LINEAR intra-trade slices."""
    nmax = max(lengths.values())
    daily = []
    for t in range(nmax):
        act = []
        for tk, trs in trades_by_tk.items():
            if t >= lengths[tk]:
                continue
            for tr in trs:
                if tr["e"] < t <= tr["x"]:
                    h = max(tr["hold"], 1)
                    seg = (1.0 + tr["net"]) ** (1.0 / h) - 1.0
                    act.append(seg)
                    break
        daily.append(sum(act) / len(act) if act else 0.0)
    return daily


def book_true_marks(data, trades_by_tk):
    """Unbounded concurrency, EQUAL SLICE per open trade, TRUE daily marks."""
    # event stream: per day, entries and exits
    nmax = max(len(v["closes"]) for v in data.values())
    # index closes by position (per ticker lists are aligned to own history)
    pos_of = {tk: {d: k for k, d in enumerate(v["dates"])} for tk, v in data.items()}
    entries, exits = {}, {}
    for tk, trs in trades_by_tk.items():
        for tr in trs:
            entries.setdefault(tr["e"], []).append((tk, tr))
            exits.setdefault(tr["x"], []).append((tk, tr))
    open_pos = {}   # tk -> {"val": dollar value, "last_px": close}
    daily = []
    equity = 1.0
    for t in range(nmax):
        start_eq = equity + sum(p["val"] for p in open_pos.values())
        # process exits at their close
        for (tk, tr) in exits.get(t, []):
            if tk in open_pos:
                px_now = _close_at(data, tk, t)
                if px_now is None:
                    px_now = open_pos[tk]["last_px"]
                open_pos[tk]["val"] *= px_now / open_pos[tk]["last_px"]
                equity += open_pos[tk]["val"]
                del open_pos[tk]
        # process entries at their close
        todays_entries = sorted(entries.get(t, []), key=lambda z: z[0])
        m_remaining = len(todays_entries)
        for (tk, tr) in todays_entries:
            px_now = _close_at(data, tk, t)
            m_remaining -= 1
            if px_now is None or tk in open_pos or equity <= 0:
                continue
            n_open = len(open_pos)
            # equal slice of CASH only; denominator includes remaining
            # entrants today so multi-entry days cannot over-allocate
            alloc = equity / (n_open + 1 + m_remaining)
            # full round-trip cost charged against the position at entry
            rt_cost = tr["gross"] - tr["net"]
            alloc *= (1.0 - rt_cost)
            equity -= alloc
            open_pos[tk] = {"val": alloc, "last_px": px_now}
        # mark to market through the day's close
        for tk, p in open_pos.items():
            px_now = _close_at(data, tk, t)
            if px_now is not None and p["last_px"]:
                p["val"] *= px_now / p["last_px"]
                p["last_px"] = px_now
        end_eq = equity + sum(p["val"] for p in open_pos.values())
        daily.append(end_eq / start_eq - 1.0 if start_eq > 0 else 0.0)
    return daily


def _close_at(data, tk, t):
    v = data[tk]
    k = t  # positions aligned by bar index within ticker history
    return v["closes"][k] if 0 <= k < len(v["closes"]) else None


def book_slots(data, trades_by_tk, K=10):
    """Finite-capital model: K slots, entry skipped when full, TRUE marks,
    half round-trip cost charged at each leg. Deterministic admission order:
    sorted ticker within a day."""
    nmax = max(len(v["closes"]) for v in data.values())
    events = {}
    for tk, trs in trades_by_tk.items():
        for tr in trs:
            events.setdefault(tr["e"], []).append((tk, tr))
    slots = [None] * K           # each: dict(tk, val, last_px, exit_x, chalf)
    cash = 1.0
    daily = []
    admitted = skipped = 0
    for t in range(nmax):
        start = cash + sum(s["val"] for s in slots if s)
        # 1) exits today: realize at close, pay exit-leg cost
        for si, s in enumerate(slots):
            if s and s["exit_x"] == t:
                px = _close_at(data, s["tk"], t)
                if px is not None:
                    s["val"] *= px / s["last_px"]
                s["val"] *= (1.0 - s["chalf"])      # exit-leg cost
                cash += s["val"]
                slots[si] = None
        # 2) entries today: fill free slots (sorted ticker order)
        n_free_now = sum(1 for s in slots if s is None)
        for (tk, tr) in sorted(events.get(t, []), key=lambda z: z[0]):
            px = _close_at(data, tk, t)
            if (n_free_now <= 0 or px is None or cash <= 0
                    or any(s and s["tk"] == tk for s in slots)):
                skipped += 1
                continue
            alloc = cash / (n_free_now + 1)     # slice of cash; reserve for rest of today's entrants
            n_free_now -= 1
            rt_cost = tr["gross"] - tr["net"]
            slots[next(k for k, s in enumerate(slots) if s is None)] = {
                "tk": tk, "val": alloc * (1.0 - rt_cost / 2.0),
                "last_px": px,
                "exit_x": tr["x"], "chalf": rt_cost / 2.0}
            cash -= alloc
            admitted += 1
        # 3) mark to market at close
        for s in slots:
            if s:
                px = _close_at(data, s["tk"], t)
                if px is not None:
                    s["val"] *= px / s["last_px"]
                    s["last_px"] = px
        end = cash + sum(s["val"] for s in slots if s)
        daily.append(end / start - 1.0 if start > 0 else 0.0)
    return daily, admitted, skipped


# ------------------------------------------------------------------
# Metrics and inference
# ------------------------------------------------------------------

def perf(daily):
    eq, peak, dd = 1.0, 1.0, 0.0
    for r in daily:
        eq *= (1.0 + r)
        peak = max(peak, eq)
        dd = min(dd, eq / peak - 1.0)
    yrs = len(daily) / 252.0
    cagr = eq ** (1.0 / yrs) - 1.0 if eq > 0 else -1.0
    mu = sum(daily) / len(daily)
    var = sum((r - mu) ** 2 for r in daily) / max(len(daily) - 1, 1)
    sd = math.sqrt(var)
    sharpe = mu / sd * math.sqrt(252.0) if sd > 0 else 0.0
    return {"cagr": cagr, "sharpe": sharpe, "maxdd": dd, "days": len(daily)}


def nw_tstat(daily, lag=10):
    n = len(daily)
    mu = sum(daily) / n
    e = [r - mu for r in daily]
    g0 = sum(x * x for x in e) / n
    s = g0
    wsum = 0.0
    for L in range(1, lag + 1):
        gl = sum(e[i] * e[i - L] for i in range(L, n)) / n
        w = 1.0 - L / (lag + 1.0)
        s += 2.0 * w * gl
        wsum += w
    var_mu = s / n
    return mu / math.sqrt(var_mu) if var_mu > 0 else 0.0


def block_bootstrap(daily, n_boot=2000, exp_block=20, seed=7):
    rng = random.Random(seed)
    n = len(daily)
    lam = 1.0 / exp_block
    log1mlam = math.log(1.0 - lam)

    def geo():
        u = rng.random()
        return max(2, int(math.log(1.0 - u) / log1mlam))
    sharpes, cagrs = [], []
    mus = []
    for _ in range(n_boot):
        sample = []
        while len(sample) < n:
            st = rng.randrange(n)
            ln = geo()
            for k in range(ln):
                if len(sample) >= n:
                    break
                sample.append(daily[(st + k) % n])
        p = perf(sample)
        sharpes.append(p["sharpe"])
        cagrs.append(p["cagr"])
        mus.append(sum(sample) / len(sample))
    mus.sort()
    sharpes.sort()
    cagrs.sort()

    def ci(a):
        lo = a[int(0.025 * len(a))]
        hi = a[int(0.975 * len(a)) - 1]
        p_gt0 = sum(1 for x in a if x > 0) / len(a)
        return lo, hi, p_gt0
    slo, shi, sp = ci(sharpes)
    clo, chi, cp = ci(cagrs)
    mlo, mhi, mp = ci(mus)
    return {"sharpe_ci95": [slo, shi], "p_sharpe_gt0": sp,
            "cagr_ci95": [clo, chi], "p_cagr_gt0": cp,
            "daily_mean_ci95": [mlo, mhi], "p_mean_gt0": mp}


def trade_stats(trades):
    nets = [tr["net"] for tr in trades]
    n = len(nets)
    if not n:
        return {"n": 0}
    wins = sum(1 for x in nets if x > 0)
    mu = sum(nets) / n
    var = sum((x - mu) ** 2 for x in nets) / max(n - 1, 1)
    sd = math.sqrt(var)
    t = mu / (sd / math.sqrt(n)) if sd > 0 and n > 1 else 0.0
    return {"n": n, "win": wins / n, "avg": mu, "t_iid": t}


# ------------------------------------------------------------------

def main():
    data, srcs = load_universe(DB_DEFAULT)
    spy = data["SPY"]["closes"]
    lengths = {tk: len(v["closes"]) for tk, v in data.items()}
    costs = {tk: ecm.estimate_trade_cost(tk, 250000)["round_trip_bp"] for tk in data}
    print("universe: %d names | bar sources: %s" % (len(data), ",".join(sorted(set(srcs)))))
    print("avg rt cost bp: %.1f" % (sum(costs.values()) / len(costs)))

    results = {"universe_n": len(data), "sources": sorted(set(srcs)),
               "avg_cost_rt_bp": sum(costs.values()) / len(costs)}

    det, rnd = {}, {}
    rng_master = random.Random(42)
    for tk in sorted(data):
        v = data[tk]
        rsis = rsi_series(v["closes"])
        det[tk] = gen_trades(v["closes"], rsis, cost_rt_bp=costs[tk])
        rnd[tk] = gen_trades(v["closes"], rsis, cost_rt_bp=costs[tk],
                             rng=random.Random(rng_master.randrange(10**9)))

    all_det = [tr for tk in sorted(det) for tr in det[tk]]

    # --- A) original-style accounting (interpolated) ------------------
    ew_sig = perf(book_original_ew(det, lengths))
    ew_rnd = perf(book_original_ew(rnd, lengths))
    print("\n[A] ORIGINAL-STYLE accounting (equal-weight, INTERPOLATED slices)")
    print("    signal : CAGR %+.1f%% Sharpe %.2f maxDD %+.1f%%" %
          (100 * ew_sig["cagr"], ew_sig["sharpe"], 100 * ew_sig["maxdd"]))
    print("    random : CAGR %+.1f%% Sharpe %.2f" % (100 * ew_rnd["cagr"], ew_rnd["sharpe"]))
    results["A_original_style"] = {"signal": ew_sig, "random": ew_rnd}

    # --- B) unbounded, true marks (isolates interpolation effect) -----
    tm_sig = perf(book_true_marks(data, det))
    print("[B] UNBOUNDED concurrency, TRUE close marks")
    print("    signal : CAGR %+.1f%% Sharpe %.2f maxDD %+.1f%%" %
          (100 * tm_sig["cagr"], tm_sig["sharpe"], 100 * tm_sig["maxdd"]))
    results["B_true_marks_unbounded"] = tm_sig

    # --- C) finite capital slots --------------------------------------
    print("[C] FINITE-CAPITAL slot models (true marks, skips when full)")
    results["C_slots"] = {}
    for K in (5, 10, 20):
        ds, adm, skp = book_slots(data, det, K=K)
        p = perf(ds)
        bt = block_bootstrap(ds)
        tnw = nw_tstat(ds)
        print("    K=%-2d CAGR %+.1f%% Sharpe %.2f maxDD %+.1f%% | NW-t %.2f | "
              "Sharpe95 [%.2f, %.2f] adm/skip %d/%d" %
              (K, 100 * p["cagr"], p["sharpe"], 100 * p["maxdd"], tnw,
               bt["sharpe_ci95"][0], bt["sharpe_ci95"][1], adm, skp))
        results["C_slots"][str(K)] = {"perf": p, "nw_t": tnw, "boot": bt,
                                      "admitted": adm, "skipped": skp}

    # --- per-trade stats ----------------------------------------------
    ts = trade_stats(all_det)
    print("[D] per-trade (iid assumption, COMPARISON ONLY): n=%d win %.1f%% "
          "avg %+.2f%% t_iid %.2f" %
          (ts["n"], 100 * ts["win"], 100 * ts["avg"], ts["t_iid"]))
    results["D_per_trade_iid"] = ts

    # --- stress grid on K=10 slot model --------------------------------
    base_ds, _, _ = book_slots(data, det, K=10)

    # delayed entry t+2
    det_d2 = {tk: gen_trades(data[tk]["closes"], rsi_series(data[tk]["closes"]),
                             cost_rt_bp=costs[tk], delay=2) for tk in sorted(data)}
    d2, _, _ = book_slots(data, det_d2, K=10)
    # doubled costs
    det_c2 = {tk: gen_trades(data[tk]["closes"], rsi_series(data[tk]["closes"]),
                             cost_rt_bp=2 * costs[tk]) for tk in sorted(data)}
    dc2, _, _ = book_slots(data, det_c2, K=10)
    print("[E] STRESS GRID (K=10): base CAGR %+.1f%% Shp %.2f | delay t+2 "
          "CAGR %+.1f%% Shp %.2f | costs x2 CAGR %+.1f%% Shp %.2f" %
          (100 * perf(base_ds)["cagr"], perf(base_ds)["sharpe"],
           100 * perf(d2)["cagr"], perf(d2)["sharpe"],
           100 * perf(dc2)["cagr"], perf(dc2)["sharpe"]))
    results["E_stress"] = {
        "base_K10": perf(base_ds),
        "delay_t2": perf(d2),
        "costs_x2": perf(dc2),
    }

    # --- subperiods on base K=10 daily book ----------------------------
    spy_dates = data["SPY"]["dates"]
    idx22 = [k for k, d in enumerate(spy_dates) if d.startswith("2022")]
    idx_last = list(range(len(spy_dates) - 252, len(spy_dates)))
    seg = lambda ds, ii: perf([ds[i] for i in ii if i < len(ds)])
    print("[F] SUBPERIODS (K=10): 2022 CAGR %+.1f%% Shp %.2f | last-252d "
          "CAGR %+.1f%% Shp %.2f" %
          (100 * seg(base_ds, idx22)["cagr"], seg(base_ds, idx22)["sharpe"],
           100 * seg(base_ds, idx_last)["cagr"], seg(base_ds, idx_last)["sharpe"]))
    results["F_subperiods"] = {"y2022": seg(base_ds, idx22),
                               "last252": seg(base_ds, idx_last)}

    # --- cohort survivorship probe -------------------------------------
    cohorts = {"pre2022": [], "2022_23": [], "2024plus": []}
    for tk in sorted(data):
        d0 = data[tk]["dates"][0][:4]
        if d0 <= "2021":
            cohorts["pre2022"].append(tk)
        elif d0 <= "2023":
            cohorts["2022_23"].append(tk)
        else:
            cohorts["2024plus"].append(tk)
    results["G_cohorts"] = {}
    for cname, tks in cohorts.items():
        if len(tks) < 5:
            continue
        sub = {tk: det[tk] for tk in tks}
        ds, _, _ = book_slots({tk: data[tk] for tk in tks}, sub, K=10)
        p = perf(ds)
        print("[G] cohort %-8s n=%-3d CAGR %+.1f%% Sharpe %.2f" %
              (cname, len(tks), 100 * p["cagr"], p["sharpe"]))
        results["G_cohorts"][cname] = {"n": len(tks), "perf": p}

    # --- random control: 30 seeds ---------------------------------------
    rs = []
    for s in range(30):
        rg = random.Random(1000 + s)
        rr = {}
        for tk in sorted(data):
            rr[tk] = gen_trades(data[tk]["closes"], rsi_series(data[tk]["closes"]),
                                cost_rt_bp=costs[tk], rng=random.Random(rg.randrange(10**9)))
        ds, _, _ = book_slots(data, rr, K=10)
        rs.append(perf(ds))
    mc = sum(x["cagr"] for x in rs) / len(rs)
    ms = sum(x["sharpe"] for x in rs) / len(rs)
    sds = math.sqrt(sum((x["sharpe"] - ms) ** 2 for x in rs) / (len(rs) - 1))
    print("[H] RANDOM CONTROL (30 seeds, K=10): mean CAGR %+.1f%% mean Sharpe "
          "%.2f (sd %.2f)" % (100 * mc, ms, sds))
    results["H_random_control"] = {"mean_cagr": mc, "mean_sharpe": ms,
                                   "sd_sharpe": sds, "n_seeds": 30}

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=1)
    print("\njson -> %s" % OUT_JSON)


if __name__ == "__main__":
    main()
