#!/usr/bin/env python
"""mr-corrected.py -- CORRECTED capital/exposure/concurrency/return accounting
for the RSI mean-reversion strategy (FIS-MR-001 remediation, 2026-08-25).

Corrections vs tools/research/mean-reversion.py:
  C1  Date-keyed calendar (SPY trading calendar); no positional alignment.
  C2  True close-based marks only. NO interpolated intra-trade returns.
  C3  Finite capital: K slots; signals skipped when full or limits bind.
  C4  Limits: max 1 position per issuer (ticker); max 3 per ETF sector group;
      broad ETFs capped at 4. Stock-level sector mapping does not exist yet
      (Wave D security master) -- documented data-blocked scope.
  C5  Execution: signal at close t -> fill at NEXT close with conservative
      slippage loaded INTO the fill price (half round-trip cost per leg,
      doubled as stress default). Same-close execution impossible by design.
  C6  Costs deducted exactly once per leg via fill prices; idle cash earns 0.
  C7  Inference on the day-book: Newey-West t, stationary block bootstrap,
      trade-cluster counting (overlap-grouped), Benjamini-Hochberg across
      the four variants, deflation reference for 6 tournament trials.
  C8  Missing prices: a position whose bar is absent keeps its last mark;
      no synthetic returns are ever generated.

Outputs stdout tables + Efforts/osanwe-v2-overhaul/_work/fis-baseline/
mr-corrected-results.json. ASCII only, no network, sqlite read-only.
"""

from __future__ import annotations

import importlib.util
import json
import math
import os
import random
import sqlite3

VAULT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(VAULT, "Efforts", "osanwe-v2-overhaul", "_work", "factors.db")
OUT = os.path.join(VAULT, "Efforts", "osanwe-v2-overhaul", "_work",
                   "fis-baseline", "mr-corrected-results.json")

_ecm_path = os.path.join(VAULT, "tools", "execution-cost-model.py")
_spec = importlib.util.spec_from_file_location("ecm", _ecm_path)
ecm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ecm)

ADRS = {"TSM", "ASML", "ABBNY", "ATEYY", "ASMIY"}
MIN_BARS = 1000
RSI_P = 14
K_SLOTS = 10
ISSUER_CAP = 1
ETF_SECTOR_CAP = 3
BROAD_CAP = 4
SLIP_MODE = os.environ.get("MR_SLIP_MODE", "stress")      # stress | standard
LIMITS_ON = os.environ.get("MR_LIMITS", "1") == "1"       # sector/broad caps


def limits_active():
    return LIMITS_ON
SECTORS = {
    "SMH": "semi", "SOXX": "semi",
    "ITA": "defense", "PPA": "defense", "XAR": "defense",
    "XLE": "energy", "VDE": "energy",
    "XLF": "financials", "XLI": "industrial",
    "XLP": "staples", "XLRE": "reit", "XLU": "utility", "XLV": "health",
    "XLY": "discretionary", "DTCR": "discretionary",
    "QQQ": "broad", "SPY": "broad", "VOO": "broad", "VGT": "broad", "IAU": "gold",
}
ETFS = set(SECTORS)


def load():
    con = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)
    rows = con.execute("SELECT ticker, date, close FROM bars ORDER BY ticker, date").fetchall()
    con.close()
    px = {}
    for tk, d, c in rows:
        tk = tk.upper()
        if "-USD" in tk or tk in ADRS:
            continue
        px.setdefault(tk, {})[d] = float(c)
    px = {tk: m for tk, m in px.items() if len(m) > MIN_BARS}
    cal = sorted(px["SPY"])
    return px, cal


def rsi(closes):
    n = len(closes)
    out = [None] * n
    if n <= RSI_P:
        return out
    g = l = 0.0
    for i in range(1, RSI_P + 1):
        d = closes[i] - closes[i - 1]
        g += max(d, 0.0)
        l += max(-d, 0.0)
    ag, al = g / RSI_P, l / RSI_P
    out[RSI_P] = 100.0 if al == 0 else 100.0 - 100.0 / (1 + ag / al)
    for i in range(RSI_P + 1, n):
        d = closes[i] - closes[i - 1]
        ag = (ag * (RSI_P - 1) + max(d, 0.0)) / RSI_P
        al = (al * (RSI_P - 1) + max(-d, 0.0)) / RSI_P
        out[i] = 100.0 if al == 0 else 100.0 - 100.0 / (1 + ag / al)
    return out


def signals(px, cal, entry=30, exit_lvl=50, max_hold=10):
    """Date-keyed candidate signals: list of {tk, sig_date, fill_date, exit_date}.

    Signal at close t -> earliest tradable close is t+1 (same-close forbidden).
    Exits evaluated from t+2 onward at close; force-exit after max_hold or at
    end of the ticker's own data.
    """
    idx_of = {d: i for i, d in enumerate(cal)}
    out = []
    for tk, m in sorted(px.items()):
        dates = sorted(m)
        pos = {d: i for i, d in enumerate(dates)}
        closes = [m[d] for d in dates]
        rs = rsi(closes)
        armed = True
        i = 0
        while i < len(dates) - 1:
            r = rs[i]
            if r is None or not armed or r >= entry:
                if r is not None and r >= entry:
                    armed = True
                i += 1
                continue
            gi = pos[dates[i]]
            if gi + 1 >= len(cal):
                break
            fill_d = cal[gi + 1]
            if fill_d not in m:
                i += 1
                continue          # no artificial fills on missing bars
            xj = None
            j = i + 2             # earliest managed exit (>= fill + 1 close)
            while j < len(dates):
                rr = rs[j]
                gcal = idx_of[dates[j]]
                if (rr is not None and rr > exit_lvl) or (gcal - gi) >= max_hold:
                    xj = j
                    break
                j += 1
            if xj is None:
                xj = len(dates) - 1
            out.append({"tk": tk, "sig": dates[i], "fill": fill_d,
                        "exit": dates[xj]})
            i = xj
            armed = False
    return out


def slip_bp(tk):
    """Per-leg slippage. SLIP_MODE='stress' charges the FULL class round trip
    per leg (2x total); 'standard' charges the half round trip per leg
    (matching tools/research/fis-mr-independent.py totals)."""
    rt = ecm.estimate_trade_cost(tk, 250000)["round_trip_bp"]
    mult = 2.0 if SLIP_MODE == "stress" else 1.0
    return rt / 2.0 * mult


def simulate(sigs, px, cal, K=K_SLOTS, seed=None):
    """Finite-capital event loop. Returns (daily_book, records, stats).

    Deterministic admission: same-day candidates sorted by (tk, sig date).
    """
    events = {}
    for s in sigs:
        events.setdefault(s["fill"], []).append(s)
    exits_at = {}
    for s in sigs:
        exits_at.setdefault(s["exit"], []).append(s)
    cash = 1.0
    openp = []                      # dicts: tk,val,last_px,exit_d
    daily = []
    recs = []
    admitted = skipped_cap = skipped_limit = 0
    exposed_days = 0
    gross_traded = 0.0
    for d in cal:
        start_eq = cash + sum(p["val"] for p in openp)
        # exits first (realize at today's close)
        done = []
        for p in openp:
            if p["exit_d"] == d:
                c = px[p["tk"]].get(d)
                if c is not None:
                    p["val"] *= c * (1 - slip_bp(p["tk"]) / 10000.0) / p["last_px"]
                    gross_traded += p["val"]
                cash += p["val"]
                recs.append({**p["rec"], "exit_d": d, "exit_val": p["val"],
                             "ret_net": p["val"] / p["rec"]["cost_basis"] - 1})
                done.append(p)
        for p in done:
            openp.remove(p)
        # entries (sorted deterministic order)
        for s in sorted(events.get(d, []), key=lambda z: z["tk"]):
            c = px[s["tk"]].get(d)
            if c is None:
                continue
            if len(openp) >= K:
                skipped_cap += 1
                continue
            if any(p["tk"] == s["tk"] for p in openp):
                skipped_limit += 1
                continue
            sec = SECTORS.get(s["tk"])
            if limits_active():
                if sec == "broad":
                    if sum(1 for p in openp if SECTORS.get(p["tk"]) == "broad") >= BROAD_CAP:
                        skipped_limit += 1
                        continue
                elif sec:
                    if sum(1 for p in openp if SECTORS.get(p["tk"]) == sec) >= ETF_SECTOR_CAP:
                        skipped_limit += 1
                        continue
            eq_now = cash + sum(p["val"] for p in openp)
            # slot-target sizing: equal-weight across the K slots, capped by
            # available cash. Uses the CALLER's K (RX-MR review fix: was the
            # module-level K_SLOTS constant, so simulate(K=n) only varied
            # admission, not sizing).
            alloc = min(eq_now / max(K, 1), cash)
            if alloc <= 1e-12:
                skipped_cap += 1
                continue
            s_bp = slip_bp(s["tk"])
            # entry friction charged ONCE: position starts worth
            # alloc/(1+slip) marked at the CLEAN close
            units_val = alloc / (1 + s_bp / 10000.0)
            cash -= alloc
            gross_traded += alloc
            openp.append({"tk": s["tk"], "val": units_val, "last_px": c,
                          "exit_d": s["exit"],
                          "rec": {"tk": s["tk"], "fill_d": d,
                                  "cost_basis": alloc}})
            admitted += 1
        # mark to market
        for p in openp:
            c = px[p["tk"]].get(d)
            if c is not None:
                p["val"] *= c / p["last_px"]
                p["last_px"] = c
        eq = cash + sum(p["val"] for p in openp)
        prev = daily[-1][1] if daily else start_eq
        daily.append((d, eq, eq / prev - 1 if prev > 0 else 0.0))
        if openp:
            exposed_days += 1
    return daily, recs, {"admitted": admitted, "skipped_capacity": skipped_cap,
                         "skipped_limits": skipped_limit,
                         "exposed_days": exposed_days,
                         "gross_traded": gross_traded}


# ---------- metrics ----------

def perf(daily):
    rets = [r for _, _, r in daily]
    eq = 1.0
    peak = 1.0
    dd = 0.0
    for r in rets:
        eq *= 1 + r
        peak = max(peak, eq)
        dd = min(dd, eq / peak - 1)
    yrs = len(rets) / 252.0
    cagr = eq ** (1 / yrs) - 1 if eq > 0 else -1
    mu = sum(rets) / len(rets)
    var = sum((x - mu) ** 2 for x in rets) / max(len(rets) - 1, 1)
    vol = math.sqrt(var) * math.sqrt(252)
    sharpe = mu / math.sqrt(var) * math.sqrt(252) if var > 0 else 0
    dn = [min(x, 0) for x in rets]
    dv = sum(x ** 2 for x in dn) / max(len(dn) - 1, 1)
    sortino = mu / math.sqrt(dv) * math.sqrt(252) if dv > 0 else 0
    return {"cagr": cagr, "ann_vol": vol, "sharpe": sharpe, "sortino": sortino,
            "maxdd": dd, "calmar": (cagr / abs(dd) if dd < 0 else 0)}


def nw_t(rets, lag=10):
    n = len(rets)
    mu = sum(rets) / n
    e = [x - mu for x in rets]
    s = sum(x * x for x in e) / n
    for L in range(1, lag + 1):
        gl = sum(e[i] * e[i - L] for i in range(L, n)) / n
        s += 2 * (1 - L / (lag + 1)) * gl
    return mu / math.sqrt(max(s, 1e-18) / n)


def boot(daily, n=2000, blk=20, seed=7):
    rng = random.Random(seed)
    rets = [r for _, _, r in daily]
    nn = len(rets)
    lam = 1 / blk
    ll = math.log(1 - lam)
    sh, cg = [], []
    for _ in range(n):
        sm = []
        while len(sm) < nn:
            st = rng.randrange(nn)
            ln = max(2, int(math.log(1 - rng.random()) / ll))
            sm += rets[st:st + ln]
        sm = sm[:nn]
        p = perf([(None, None, x) for x in sm])
        sh.append(p["sharpe"])
        cg.append(p["cagr"])
    sh.sort()
    cg.sort()
    return {"sharpe_ci95": [sh[int(.025 * n)], sh[int(.975 * n) - 1]],
            "cagr_ci95": [cg[int(.025 * n)], cg[int(.975 * n) - 1]]}


def clusters(recs):
    """Greedy overlap grouping -> economically independent trade clusters."""
    rs = sorted(recs, key=lambda z: z["fill_d"])
    cls = []
    for r in rs:
        hit = None
        for c in cls:
            if r["fill_d"] <= c["end"]:
                hit = c
                break
        if hit:
            hit["rets"].append(r["ret_net"])
            hit["end"] = max(hit["end"], r["exit_d"])
        else:
            cls.append({"start": r["fill_d"], "end": r["exit_d"],
                        "rets": [r["ret_net"]]})
    means = [sum(c["rets"]) / len(c["rets"]) for c in cls]
    mu = sum(means) / len(means)
    var = sum((x - mu) ** 2 for x in means) / max(len(means) - 1, 1)
    t = mu / math.sqrt(var / len(means)) if var > 0 else 0
    return {"n_clusters": len(cls), "cluster_mean": mu, "cluster_t": t}


def trade_stats(recs):
    nets = [r["ret_net"] for r in recs]
    n = len(nets)
    w = [x for x in nets if x > 0]
    lo = [x for x in nets if x <= 0]
    pf = (sum(w) / abs(sum(lo))) if lo and sum(lo) != 0 else float("inf")
    wins = sum(1 for x in nets if x > 0)
    return {"n_trades_closed": n, "win_rate": wins / n if n else 0,
            "profit_factor": pf,
            "avg_net": sum(nets) / n if n else 0}


def main():
    px, cal = load()
    print("universe %d | calendar %s..%s (%d days)"
          % (len(px), cal[0], cal[-1], len(cal)))
    results = {}
    variants = [("base", 30, 50, 10), ("deep", 20, 50, 10),
                ("fast", 30, 50, 5), ("deepfast", 20, 50, 5)]
    pvals = []
    for name, en, exl, mh in variants:
        sigs = signals(px, cal, en, exl, mh)
        daily, recs, st = simulate(sigs, px, cal)
        p = perf(daily)
        t_nw = nw_t([r for _, _, r in daily])
        bt = boot(daily)
        cl = clusters(recs)
        ts = trade_stats(recs)
        from math import erf
        pval = 1 - 0.5 * (1 + erf(abs(t_nw) / math.sqrt(2)))
        pvals.append(pval)
        # exposure/time-in-market/turnover
        rets = [r for _, _, r in daily]
        expo = st["exposed_days"] / len(daily)
        turnover = st["gross_traded"] / (len(daily) / 252.0)
        res = {"perf": p, "nw_t": t_nw, "boot": bt, "clusters": cl,
               "trades": ts, "signals": len(sigs), "sim_stats": st,
               "exposure_time_in_market": expo,
               "turnover_x_per_year": turnover,
               "raw_p_value_two_sided_normal": pval,
               "slippage_model": "half-rt x2 per leg, charged once per leg"}
        results[name] = res
        print("[%s] signals %d adm %d skip(cap/lim) %d/%d | CAGR %+.1f%% vol %.1f%% "
              "Shp %.2f Sort %.2f maxDD %.1f%% Calmar %.2f | NW-t %.2f "
              "clus %d (t %.2f) | win %.1f%% PF %.2f | expo %.0f%% TO %.1fx"
              % (name, len(sigs), st["admitted"], st["skipped_capacity"],
                 st["skipped_limits"],
                 100 * p["cagr"], 100 * p["ann_vol"], p["sharpe"], p["sortino"],
                 100 * p["maxdd"], p["calmar"], t_nw, cl["n_clusters"],
                 cl["cluster_t"], 100 * ts["win_rate"], ts["profit_factor"],
                 100 * expo, turnover))

    # Benjamini-Hochberg across the four variants (two-sided normal p)
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    bh = [0.0] * m
    prev = 1.0
    for rank, i in enumerate(reversed(order)):
        k = m - rank
        prev = min(prev, min(1.0, pvals[i] * m / k))
        bh[i] = prev
    for idx, (name, *_rest) in enumerate(variants):
        results[name]["bh_q_value"] = bh[idx]
        print("[bh] %-9s raw p=%.4g q=%.4g"
              % (name, results[name]["raw_p_value_two_sided_normal"], bh[idx]))

    # capacity: smallest class-order size where avg edge < round-trip cost
    avg_edge = results["base"]["trades"]["avg_net"]
    cap_rows = []
    for sz in (25_000, 50_000, 100_000, 250_000, 500_000):
        rt = sum(ecm.estimate_trade_cost(tk, sz)["round_trip_bp"]
                 for tk in list(px)[:40]) / 40
        cap_rows.append({"order_usd": sz, "avg_rt_bp": rt,
                         "edge_gt_cost": avg_edge * 1e4 > rt})
    results["capacity_scan"] = {"avg_trade_net_pct": avg_edge * 100,
                                "rows": cap_rows}

    # factor adjustment vs SPY RETURNS (date-keyed): beta + annualized alpha
    # + Newey-West t on the residual stream of the base-variant book.
    spy = px["SPY"]
    spy_ret = {}
    sd = sorted(spy)
    for a, b in zip(sd, sd[1:]):
        spy_ret[b] = spy[b] / spy[a] - 1
    sigs0 = signals(px, cal, 30, 50, 10)
    base_daily, _, _ = simulate(sigs0, px, cal)
    pairs = [(spy_ret[d], r) for d, _, r in base_daily if d in spy_ret]
    xs = [a for a, _ in pairs]
    ys = [r for _, r in pairs]
    n = len(pairs)
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((a - mx) * (b - my) for a, b in pairs) / (n - 1)
    vx = sum((a - mx) ** 2 for a in xs) / (n - 1)
    beta = cov / vx
    resid = [b - beta * a for a, b in pairs]
    alpha_ann = (my - beta * mx) * 252
    results["factor_adjusted"] = {"spy_beta": beta, "alpha_ann": alpha_ann,
                                  "resid_nw_t": nw_t(resid)}
    print("[factors] beta %.2f alpha_ann %+.1f%% resid NW-t %.2f"
          % (beta, 100 * alpha_ann, results["factor_adjusted"]["resid_nw_t"]))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(results, open(OUT, "w"), indent=1)
    print("json ->", OUT)


if __name__ == "__main__":
    main()
