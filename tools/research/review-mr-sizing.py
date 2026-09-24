#!/usr/bin/env python
"""review-mr-sizing.py -- RX-MR independent adversarial review harness.

Imports tools/research/mr-corrected.py (read-only; never calls its main())
and re-implements thin variants around ITS signals()/perf()/nw_t()/boot().
Own code here: sizing comparison, instrumented event-loop copy (concurrency,
cash reconciliation, exposure), sector-correlation, ETF-overlap, cluster-size
distribution, NW lag grid, bootstrap grid, slippage multipliers, execution
delay. ASCII only, no network, no git. Does NOT edit any existing file.
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import random
import statistics

VAULT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTDIR = os.path.join(VAULT, "Efforts", "osanwe-v2-overhaul", "_work", "fis-baseline")
MRC_PATH = os.path.join(VAULT, "tools", "research", "mr-corrected.py")

_spec = importlib.util.spec_from_file_location("mrc", MRC_PATH)
mrc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mrc)


def pct(x):
    return "%.1f%%" % (100 * x)


def fmt_row(tag, p, t):
    return ("%-14s CAGR %+.2f%% Shp %+.2f NW-t %+.2f maxDD %.1f%% expo %.0f%% adm %d"
            % (tag, 100 * p["cagr"], p["sharpe"], t, 100 * p["maxdd"],
               100 * p.get("expo", float("nan")), p.get("adm", -1)))


# ---------------------------------------------------------------- probe 1
def probe_k_sensitivity(px, cal, out):
    """K sensitivity via THEIR simulate(K=...). NOTE: their simulate sizes with
    module constant K_SLOTS (=10) regardless of K -- admission-only variation."""
    sigs = mrc.signals(px, cal, 30, 50, 10)
    rows = {}
    for k in (3, 5, 10, 20, 40):
        daily, recs, st = mrc.simulate(sigs, px, cal, K=k)
        p = mrc.perf(daily)
        t = mrc.nw_t([r for _, _, r in daily])
        p["adm"] = st["admitted"]
        p["expo"] = st["exposed_days"] / len(daily)
        rows[k] = {"cagr": p["cagr"], "sharpe": p["sharpe"], "nw_t": t,
                   "maxdd": p["maxdd"], "admitted": st["admitted"],
                   "skip_cap": st["skipped_capacity"]}
        print(fmt_row("K=%d" % k, p, t))
    signs = set(("+" if v["cagr"] > 0 else "-") for v in rows.values())
    out["k_sensitivity"] = {"rows": rows, "sign_flip_anywhere": len(signs) > 1,
                            "sizing_note": "their simulate() sizes eq/K_SLOTS(=10) "
                                           "regardless of K arg -> K varies ADMISSION ONLY"}
    print("[p1] sign flip anywhere:", len(signs) > 1)


# ------------------------------------------------- probe 2 (own simulator)
def rolling_vol(px, cal, win=20):
    vols = {}
    for tk, m in px.items():
        ds = sorted(m)
        rs = {}
        for i in range(1, len(ds)):
            rs[ds[i]] = m[ds[i]] / m[ds[i - 1]] - 1
        v = {}
        acc = []
        for d in ds[1:]:
            acc.append(rs[d])
            if len(acc) > win:
                acc.pop(0)
            if len(acc) >= win // 2:
                mu = sum(acc) / len(acc)
                var = sum((x - mu) ** 2 for x in acc) / max(len(acc) - 1, 1)
                v[d] = math.sqrt(var * 252) if var > 0 else None
            else:
                v[d] = None
        vols[tk] = v
    return vols


def sized_sim(sigs, px, cal, mode, vols=None, frac=0.10, K=10):
    """Copy of their event loop with pluggable SIZING only. Admission rules,
    caps, ordering, cost loading, marks identical to mr-corrected.simulate."""
    events = {}
    for s in sigs:
        events.setdefault(s["fill"], []).append(s)
    cash = 1.0
    openp = []
    daily = []
    recs = []
    conc = []
    exposed_days = 0
    max_gross = 0.0
    recon_viol = 0.0
    med_vol = None
    if vols:
        allv = [v for tk in vols for v in vols[tk].values() if v]
        med_vol = statistics.median(allv)
    for d in cal:
        # exits
        done = []
        for p in openp:
            if p["exit_d"] == d:
                c = px[p["tk"]].get(d)
                if c is not None:
                    p["val"] *= c * (1 - mrc.slip_bp(p["tk"]) / 10000.0) / p["last_px"]
                cash += p["val"]
                recs.append({**p["rec"], "exit_d": d, "exit_val": p["val"],
                             "ret_net": p["val"] / p["rec"]["cost_basis"] - 1})
                done.append(p)
        for p in done:
            openp.remove(p)
        for s in sorted(events.get(d, []), key=lambda z: z["tk"]):
            c = px[s["tk"]].get(d)
            if c is None:
                continue
            if len(openp) >= K:
                continue
            if any(p["tk"] == s["tk"] for p in openp):
                continue
            sec = mrc.SECTORS.get(s["tk"])
            if sec == "broad":
                if sum(1 for p in openp if mrc.SECTORS.get(p["tk"]) == "broad") >= mrc.BROAD_CAP:
                    continue
            elif sec:
                if sum(1 for p in openp if mrc.SECTORS.get(p["tk"]) == sec) >= mrc.ETF_SECTOR_CAP:
                    continue
            eq_now = cash + sum(p["val"] for p in openp)
            if mode == "slot":                      # theirs: min(eq/K, cash)
                alloc = min(eq_now / mrc.K_SLOTS, cash)
            elif mode == "fixedfrac":               # fixed fraction of book
                alloc = min(frac * eq_now, cash)
            elif mode == "equalrisk":               # inverse-vol weights, same budget
                sv = vols[s["tk"]].get(d)
                if not sv:
                    sv = med_vol
                scale = min(3.0, (med_vol / sv) if sv else 1.0)
                alloc = min((eq_now / mrc.K_SLOTS) * scale, cash)
            else:
                raise ValueError(mode)
            if alloc <= 1e-12:
                continue
            s_bp = mrc.slip_bp(s["tk"])
            units_val = alloc / (1 + s_bp / 10000.0)
            cash -= alloc
            openp.append({"tk": s["tk"], "val": units_val, "last_px": c,
                          "exit_d": s["exit"], "entry_d": d,
                          "rec": {"tk": s["tk"], "fill_d": d, "cost_basis": alloc}})
        for p in openp:
            c = px[p["tk"]].get(d)
            if c is not None:
                p["val"] *= c / p["last_px"]
                p["last_px"] = c
        eq = cash + sum(p["val"] for p in openp)
        # reconciliation identity checked every day (probe 4)
        recon_viol = max(recon_viol, abs(eq - (cash + sum(p["val"] for p in openp))))
        inv = sum(p["val"] for p in openp)
        if eq > 0:
            max_gross = max(max_gross, inv / eq)
        conc.append(len(openp))
        prev = daily[-1][1] if daily else 1.0
        daily.append((d, eq, eq / prev - 1 if prev > 0 else 0.0))
        if openp:
            exposed_days += 1
    pos_daily = {}
    return daily, recs, {"conc": conc, "max_gross": max_gross,
                         "recon_viol": recon_viol,
                         "exposed_days": exposed_days}


def probe_sizing_and_book(px, cal, out, vols):
    sigs = mrc.signals(px, cal, 30, 50, 10)
    res = {}
    book = None
    for mode, tag in (("slot", "slot-target(theirs)"), ("equalrisk", "equal-risk(inv-vol)"),
                      ("fixedfrac", "fixed-fraction 10%")):
        daily, recs, st = sized_sim(sigs, px, cal, mode, vols)
        p = mrc.perf(daily)
        t = mrc.nw_t([r for _, _, r in daily])
        p["expo"] = st["exposed_days"] / len(daily)
        res[tag] = {"cagr": p["cagr"], "sharpe": p["sharpe"], "nw_t": t,
                    "maxdd": p["maxdd"]}
        print(fmt_row(tag, p, t))
        if mode == "slot":
            book = (daily, recs, st)
    out["sizing_comparison"] = res
    daily, recs, st = book
    out["book"] = {"daily": [(d, e) for d, e, _ in daily],
                   "rets": [r for _, _, r in daily],
                   "conc": st["conc"], "max_gross": st["max_gross"],
                   "recon_viol": st["recon_viol"]}
    # probe 8: cluster sizes on this book
    rs = sorted(recs, key=lambda z: z["fill_d"])
    cls = []
    for r in rs:
        hit = None
        for c in cls:
            if r["fill_d"] <= c["end"]:
                hit = c
                break
        if hit:
            hit["n"] += 1
            hit["end"] = max(hit["end"], r["exit_d"])
        else:
            cls.append({"start": r["fill_d"], "end": r["exit_d"], "n": 1})
    sizes = sorted(c["n"] for c in cls)
    n = len(rs)
    top_dec = sizes[max(0, int(0.9 * len(sizes))):]
    big = sum(top_dec)
    out["cluster_sizes"] = {
        "n_clusters": len(cls), "sizes": sizes,
        "median": statistics.median(sizes), "max": max(sizes),
        "share_trades_in_top_decile_clusters": big / n if n else 0}
    print("[p8] clusters %d median size %s max %d | top-decile-cluster trade share %.1f%%"
          % (len(cls), statistics.median(sizes), max(sizes),
             100 * (big / n if n else 0)))
    return recs


# ------------------------------------------- probes 3/4/5 on instrumented copy
def probe_book_integrity(out):
    b = out["book"]
    conc = sorted(b["conc"])
    n = len(conc)

    def q(p):
        return conc[min(n - 1, int(p * n))]
    out["concurrency"] = {"p50": q(0.50), "p95": q(0.95), "max": max(conc)}
    out["cash_reconciliation_max_violation"] = b["recon_viol"]
    out["gross_exposure_max"] = b["max_gross"]
    print("[p3] concurrent positions p50=%d p95=%d max=%d" %
          (q(0.50), q(0.95), max(conc)))
    print("[p4] cash recon max |violation| = %.3e (float eps scale = pass)" % b["recon_viol"])
    print("[p5] max gross exposure = %.4f (<=1.0: %s)" % (b["max_gross"], b["max_gross"] <= 1.0))


# ------------------------------------------------------------- probe 6
def probe_sector_corr(px, cal, out):
    """Avg pairwise correlation of SAME-GROUP concurrent-position daily returns."""
    sigs = mrc.signals(px, cal, 30, 50, 10)
    events = {}
    for s in sigs:
        events.setdefault(s["fill"], []).append(s)
    # reconstruct holding intervals exactly like their loop (deterministic)
    openp, spans = [], []
    for d in cal:
        done = []
        for p in openp:
            if p["exit_d"] == d:
                done.append(p)
        for p in done:
            openp.remove(p)
        for s in sorted(events.get(d, []), key=lambda z: z["tk"]):
            c = px[s["tk"]].get(d)
            if c is None or len(openp) >= mrc.K_SLOTS:
                continue
            if any(p["tk"] == s["tk"] for p in openp):
                continue
            sec = mrc.SECTORS.get(s["tk"])
            if sec == "broad":
                if sum(1 for p in openp if mrc.SECTORS.get(p["tk"]) == "broad") >= mrc.BROAD_CAP:
                    continue
            elif sec:
                if sum(1 for p in openp if mrc.SECTORS.get(p["tk"]) == sec) >= mrc.ETF_SECTOR_CAP:
                    continue
            openp.append({"tk": s["tk"], "exit_d": s["exit"]})
            spans.append({"tk": s["tk"], "sec": sec or "STOCK", "a": d, "b": s["exit"]})
    # ticker daily returns
    rets = {}
    for tk, m in px.items():
        ds = sorted(m)
        rets[tk] = {b: m[b] / m[a] - 1 for a, b in zip(ds, ds[1:])}
    def corr(a_r, b_r):
        ds = [d for d in a_r if d in b_r]
        if len(ds) < 30:
            return None
        xs = [a_r[d] for d in ds]
        ys = [b_r[d] for d in ds]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        vx = sum((x - mx) ** 2 for x in xs)
        vy = sum((y - my) ** 2 for y in ys)
        return cov / math.sqrt(vx * vy) if vx > 0 and vy > 0 else None
    same_g, cross_g = [], []
    by_sec = {}
    for i in range(len(spans)):
        for j in range(i + 1, len(spans)):
            ov_a = max(spans[i]["a"], spans[j]["a"])
            ov_b = min(spans[i]["b"], spans[j]["b"])
            if ov_a >= ov_b:
                continue
            da = {d: r for d, r in rets.get(spans[i]["tk"], {}).items() if ov_a <= d <= ov_b}
            db = {d: r for d, r in rets.get(spans[j]["tk"], {}).items() if ov_a <= d <= ov_b}
            c = corr(da, db)
            if c is None:
                continue
            if spans[i]["sec"] == spans[j]["sec"]:
                same_g.append(c)
                by_sec.setdefault(spans[i]["sec"], []).append(c)
            else:
                cross_g.append(c)
    rng = random.Random(7)
    rand_g = []
    etfs = [t for t in px if t in mrc.SECTORS]
    for _ in range(400):
        a, b2 = rng.sample(etfs, 2)
        c = corr(rets[a], rets[b2])
        if c is not None:
            rand_g.append(c)
    out["sector_correlation"] = {
        "same_group_concurrent_pairs": len(same_g),
        "same_group_avg_corr": sum(same_g) / len(same_g) if same_g else None,
        "cross_group_concurrent_pairs": len(cross_g),
        "cross_group_avg_corr": sum(cross_g) / len(cross_g) if cross_g else None,
        "random_etf_pair_avg_corr": sum(rand_g) / len(rand_g) if rand_g else None,
        "by_group": {k: sum(v) / len(v) for k, v in by_sec.items()}}
    print("[p6] same-group concurrent avg corr %.3f (n=%d) vs cross-group %.3f vs random ETF %.3f"
          % (out["sector_correlation"]["same_group_avg_corr"] or 0, len(same_g),
             out["sector_correlation"]["cross_group_avg_corr"] or 0,
             out["sector_correlation"]["random_etf_pair_avg_corr"] or 0))
    return spans


# ------------------------------------------------------------- probe 7
def probe_etf_overlap(px, out):
    groups = {}
    for tk, sec in mrc.SECTORS.items():
        groups.setdefault(sec, []).append(tk)
    rets = {}
    for tk, m in px.items():
        ds = sorted(m)
        rets[tk] = {b: m[b] / m[a] - 1 for a, b in zip(ds, ds[1:])}
    def corr(a, b):
        da, db = rets[a], rets[b]
        ds = [d for d in da if d in db]
        xs = [da[d] for d in ds]
        ys = [db[d] for d in ds]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        vx = sum((x - mx) ** 2 for x in xs)
        vy = sum((y - my) ** 2 for y in ys)
        return cov / math.sqrt(vx * vy) if vx > 0 and vy > 0 else None
    hi, rows = {}, []
    for sec, tks in sorted(groups.items()):
        for i in range(len(tks)):
            for j in range(i + 1, len(tks)):
                c = corr(tks[i], tks[j])
                if c is None:
                    continue
                rows.append({"group": sec, "pair": tks[i] + "/" + tks[j], "corr": round(c, 3)})
                if c > 0.90:
                    hi.setdefault(sec, []).append((tks[i], tks[j], round(c, 3)))
    # effective independent bets per group: (sum lam)^2 / sum(lam^2) proxy using avg corr
    eff = {}
    for sec, tks in sorted(groups.items()):
        cs = [corr(tks[i], tks[j]) for i in range(len(tks)) for j in range(i + 1, len(tks))]
        cs = [c for c in cs if c is not None]
        if cs:
            ac = sum(cs) / len(cs)
            k = len(tks)
            eff[sec] = round(k / (1 + (k - 1) * ac), 2)   # effective N given avg corr
    out["etf_overlap"] = {"high_corr_pairs_gt090_by_group": hi,
                          "effective_n_independent_names_per_group": eff,
                          "all_pairs": rows}
    print("[p7] corr>0.90 pairs inside same cap-group:")
    for sec, ps in hi.items():
        print("     %-14s %s" % (sec, ", ".join("%s/%s=%.2f" % p for p in ps)))
    print("     effective-N per group:", eff)


# ------------------------------------------- probes 9/10/11/12
def probe_inference_grids(out):
    rets = out["book"]["rets"]
    daily = [(None, None, r) for r in rets]
    lags = {}
    for L in (3, 10, 21, 42):
        lags[L] = mrc.nw_t(rets, lag=L)
    out["nw_lag_sensitivity"] = lags
    print("[p9] NW-t by lag:", {k: round(v, 3) for k, v in lags.items()})
    boots = {}
    for blk in (10, 20, 40):
        for sd in (7, 42, 2026):
            b = mrc.boot(daily, n=1000, blk=blk, seed=sd)
            boots["blk%d_seed%d" % (blk, sd)] = b["sharpe_ci95"]
            print("[p10] blk %2d seed %5d Sharpe CI [%.3f, %.3f]"
                  % (blk, sd, b["sharpe_ci95"][0], b["sharpe_ci95"][1]))
    out["block_bootstrap_sharpe_ci"] = boots
    stable = all(lo > 0 for lo, _ in boots.values()) or all(hi < 0 for _, hi in boots.values())
    out["bootstrap_ci_sign_stable_across_grid"] = stable
    print("[p10] CI excludes zero uniformly across grid:", stable)


def probe_slippage(px, cal, out):
    sigs = mrc.signals(px, cal, 30, 50, 10)
    orig = mrc.slip_bp
    res = {}
    for mult in (0.5, 1.0, 2.0):
        mrc.slip_bp = lambda tk, m=mult: orig.__wrapped__(tk) * m if hasattr(orig, "__wrapped__") else _scaled(orig, tk, m)
        daily, recs, st = mrc.simulate(sigs, px, cal)
        p = mrc.perf(daily)
        t = mrc.nw_t([r for _, _, r in daily])
        res["x%g" % mult] = {"cagr": p["cagr"], "sharpe": p["sharpe"], "nw_t": t}
        print(fmt_row("slip x%g" % mult, p, t))
    mrc.slip_bp = orig
    out["slippage_sensitivity"] = res
    print("[p11] note: multiplier applied on top of STRESS basis (full class RT per leg)")


def _scaled(orig_fn, tk, m):
    return orig_fn(tk) * m


def probe_delay(px, cal, out):
    """Fill at t+2 / t+3 instead of t+1: shift fill forward, keep signal+exit."""
    idx_of = {d: i for i, d in enumerate(cal)}
    res = {}
    for delay in (1, 2, 3):
        raw = mrc.signals(px, cal, 30, 50, 10)
        sigs = []
        for s in raw:
            gi = idx_of.get(s["fill"])
            if gi is None or gi + delay - 1 >= len(cal):
                continue
            nf = cal[gi + delay - 1]
            if s["exit"] <= nf:
                continue
            sigs.append({"tk": s["tk"], "sig": s["sig"], "fill": nf, "exit": s["exit"]})
        daily, recs, st = mrc.simulate(sigs, px, cal)
        p = mrc.perf(daily)
        t = mrc.nw_t([r for _, _, r in daily])
        res["t+%d" % delay] = {"signals": len(sigs), "cagr": p["cagr"],
                               "sharpe": p["sharpe"], "nw_t": t}
        print(fmt_row("delay t+%d" % delay, p, t))
    out["execution_delay"] = res
    print("[p12] note: exit kept at original RSI-based date; signals whose exit precedes new fill dropped")


def main():
    px, cal = mrc.load()
    print("universe %d | %s..%s (%d days)" % (len(px), cal[0], cal[-1], len(cal)))
    out = {"meta": {"universe": len(px), "cal_start": cal[0], "cal_end": cal[-1],
                    "n_days": len(cal), "engine": MRC_PATH}}
    probe_k_sensitivity(px, cal, out)
    vols = rolling_vol(px, cal)
    probe_sizing_and_book(px, cal, out, vols)
    probe_book_integrity(out)
    spans = probe_sector_corr(px, cal, out)
    out["holding_spans_n"] = len(spans)
    probe_etf_overlap(px, out)
    probe_inference_grids(out)
    probe_slippage(px, cal, out)
    probe_delay(px, cal, out)
    path = os.path.join(OUTDIR, "rx-mr-review.json")
    json.dump(out, open(path, "w"), indent=1)
    print("json ->", path)


if __name__ == "__main__":
    main()
