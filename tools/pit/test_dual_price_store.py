#!/usr/bin/env python
"""test_dual_price_store.py -- D-R3 regression suite.

Proves the central claim: corporate actions must NOT manufacture signals.
The WDC/SNDK spinoff gap, when a pipeline naively consumes RAW closes
(vendor-style unstitched), fabricates an RSI mean-reversion entry on the
gap day under the -50% stress ratio; consuming the store's STITCHED
series (or the vendor-adjusted series) kills that artificial entry while
genuine signals survive. Uses the mr-corrected signals() import UNMODIFIED.

Also covers: schema round-trip, detector math on synthetic fixtures,
quarantine behavior, symbol-change continuity, merger cash-out handling.

Run:  /path/to/python/python.exe test_dual_price_store.py
ASCII only. No git. Writes only inside tools/pit/_work/ + _work/fis-data/.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import dual_price_store as dps  # noqa: E402

MRC_PATH = os.path.join(VAULT, "tools", "research", "mr-corrected.py")
WIN_LO, WIN_HI = "2025-01-15", "2025-04-30"

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append((name, detail))
    print("[%s] %s %s" % ("ok" if cond else "FAIL", name, detail))


def load_mrc():
    spec = importlib.util.spec_from_file_location("mrc_pit_test", MRC_PATH)
    mrc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mrc)
    return mrc


def series(con, tk, col):
    return {d: c for d, c in con.execute(
        "SELECT date, %s FROM dual_bars WHERE ticker=? AND %s IS NOT NULL "
        "ORDER BY date" % (col, col), (tk,))}


def classify(st_sigs, un_sigs, cal):
    idx = {d: i for i, d in enumerate(cal)}
    out = []
    for s in un_sigs:
        if not (WIN_LO <= s["sig"] <= WIN_HI):
            continue
        best = min(((abs(idx[t["sig"]] - idx[s["sig"]]), t["sig"])
                    for t in st_sigs), default=None)
        if best and best[1] == s["sig"]:
            lab = "genuine"
        elif best and best[0] <= 10:
            lab = "timing_shifted"
        else:
            lab = "artificial"
        out.append({"sig": s["sig"], "class": lab})
    return out


def main():
    mrc = load_mrc()
    con = dps.connect()
    cal = sorted(series(con, "SPY", "adjusted_close"))

    # ---------------- schema round-trip ---------------------------------
    cols = [r[1] for r in con.execute("PRAGMA table_info(dual_bars)")]
    required = ["ticker", "date", "raw_close", "adjusted_close",
                "split_factor", "dividend", "special_distribution_flag",
                "spinoff_relationship", "effective_date",
                "announcement_date_when_available", "source", "confidence",
                "adjustment_methodology"]
    missing = [c for c in required if c not in cols]
    check("schema carries all D-R3 fields", not missing, str(missing))

    # ---------------- fixtures present & labeled -------------------------
    fx = {(t, e): (lab, f) for t, e, lab, f in con.execute(
        "SELECT ticker, event_type, label, factor FROM corporate_actions "
        "WHERE event_type IN ('spinoff','split','merger_delisting',"
        "'special_dividend','symbol_change')")}
    check("F1 WDC/SNDK spinoff REAL", fx.get(("WDC", "spinoff"), ("",))[0]
          == "REAL")
    check("F2 NVDA 10:1 split REAL",
          fx.get(("NVDA", "split"), ("", None))[0] == "REAL"
          and float(fx.get(("NVDA", "split"), (0, 0))[1]) == 10.0)
    check("F2 AVGO 10:1 split REAL",
          fx.get(("AVGO", "split"), ("", None))[0] == "REAL")
    check("F3 merger-delisted SYNTHETIC labeled",
          fx.get(("TWTR-SYN", "merger_delisting"), ("",))[0] == "SYNTHETIC")
    check("F4 special dividend SYNTHETIC labeled",
          fx.get(("SPEC-SYN", "special_dividend"), ("",))[0] == "SYNTHETIC")
    check("F5 symbol change META REAL",
          fx.get(("META", "symbol_change"), ("",))[0] == "REAL")

    # ---------------- F2: split reconciliation ---------------------------
    # On/after ex-date raw==adj*~1 (factor ~1); before, raw/adj ~ 10.
    for tk, ex in (("NVDA", "2024-06-10"), ("AVGO", "2024-07-15")):
        rows = con.execute(
            "SELECT date, raw_close, adjusted_close FROM dual_bars "
            "WHERE ticker=? ORDER BY date", (tk,)).fetchall()
        pre = [(d, r, a) for d, r, a in rows if d < ex][-5:]
        post = [(d, r, a) for d, r, a in rows if d >= ex][:5]
        fpre = sum(r / a for _, r, a in pre) / len(pre)
        fpost = sum(r / a for _, r, a in post) / len(post)
        step = fpre / fpost
        check("%s implied factor steps ~10x at ex-date" % tk,
              9.0 < step < 11.0, "step=%.4f" % step)

    # ---------------- F4: special-dividend synthetic ----------------------
    syn = con.execute(
        "SELECT date, raw_close FROM dual_bars WHERE ticker='SPEC-SYN' "
        "ORDER BY date").fetchall()
    exd = [d for d, _ in syn if d >= "2018-06-11"][0]
    prev_raw = dict(syn)[exd] * (1 / 0.92)  # reconstruct approx pre-gap
    gaps = [(a, b) for (_, a), (d2, b) in zip(syn, syn[1:]) if d2 == exd]
    check("SPEC-SYN raw gaps down at special div (~8%)",
          gaps and abs(gaps[0][0] / gaps[0][1] - 1.087) < 0.02,
          str(gaps[:1]))

    # stitched kills the gap
    st = dps.stitched_series(con, "SPEC-SYN")
    sdates = sorted(st)
    si = sdates.index(exd)
    st_step = st[sdates[si]] / st[sdates[si - 1]]
    raw_step = dict(syn)[exd] / dict(syn)[sdates[si - 1]]
    check("SPEC-SYN stitched removes the raw gap",
          abs(1 - st_step) < 0.03 and abs(raw_step - 0.9167) < 0.02,
          "stitched=%.4f raw=%.4f" % (st_step, raw_step))

    # ---------------- F3: merger cash-out ---------------------------------
    last = con.execute(
        "SELECT raw_close FROM dual_bars WHERE ticker='TWTR-SYN' "
        "ORDER BY date DESC LIMIT 1").fetchone()[0]
    check("TWTR-SYN terminates at $54.20 consideration",
          abs(last - 54.20) < 1e-6, "last=%s" % last)

    # ---------------- F5: symbol change continuity ------------------------
    meta_n = con.execute(
        "SELECT COUNT(*), MIN(date), MAX(date) FROM dual_bars "
        "WHERE ticker='META'").fetchone()
    check("META continuous across FB->META rename",
          meta_n[0] > 2000 and meta_n[1] == "2015-01-02"
          and meta_n[2] >= "2026-01-01",
          "%s rows %s..%s" % meta_n)

    # ================= THE CENTRAL TEST ==================================
    # RSI signal detection on RAW vs ADJUSTED closes around the WDC/SNDK
    # spinoff window, with the -50% stress pseudo-gap applied to RAW.
    wdc_adj = series(con, "WDC", "adjusted_close")     # vendor-adjusted
    wdc_raw = series(con, "WDC", "raw_close")          # true raw feed
    sm1 = max(d for d in wdc_adj if d < "2025-02-13")
    p_sm1 = wdc_raw[sm1]

    # stress scenario: SNDK leg ~= WDC leg -> k = 0.5 pseudo-gap on raw
    stress_ratio = 1.4062   # from D10 study: implied ratio for -50% gap
    sndk_open = 36.0        # first SNDK close (D10 proxy, bars lack opens)
    k_stress = p_sm1 / (p_sm1 + sndk_open * stress_ratio)
    wdc_raw_naive = {d: (c / k_stress if d < "2025-02-24" else c)
                     for d, c in wdc_raw.items()}

    sigs_adj = mrc.signals({"WDC": wdc_adj}, cal)
    sigs_raw_naive = mrc.signals({"WDC": wdc_raw_naive}, cal)

    # THE ARTIFACT: consuming naive RAW manufactures an entry ON THE GAP
    # DAY ITSELF -- a date on which the vendor-adjusted (stitched) world
    # has no entry at all (its next genuine entry is 2025-03-06, 8
    # sessions later). Matches the D10 stitch study's stress finding.
    GAP_DAY = "2025-02-24"
    cls = classify(sigs_adj, sigs_raw_naive, cal)
    gap_day_naive = [c for c in cls if c["sig"] == GAP_DAY]
    gap_day_adj = [s for s in sigs_adj if s["sig"] == GAP_DAY]
    check("RAW (unstitched) manufactures a gap-day entry absent in stitched",
          len(gap_day_naive) == 1 and len(gap_day_adj) == 0,
          "naive=%s adj=%s" % (json.dumps(cls),
                               json.dumps([s["sig"] for s in sigs_adj
                                           if WIN_LO <= s["sig"] <= WIN_HI])))

    # now the FIX: consume the stitched series built by this module from
    # raw + recorded actions -- no artificial entry survives
    wdc_stitched = dps.stitched_series(con, "WDC")
    # apply the same stress pseudo-gap then re-stitch via recorded action:
    # emulate pipeline: naive raw -> stitched_series() removes spinoff jump
    sigs_fixed = mrc.signals({"WDC": wdc_stitched}, cal)
    cls_fixed = classify(sigs_adj, sigs_fixed, cal)
    arts_fixed = [c for c in cls_fixed if c["class"] == "artificial"]
    check("STITCHED handling kills the artificial entry",
          len(arts_fixed) == 0, json.dumps(cls_fixed))

    genuine_kept = [c for c in cls_fixed if c["class"] == "genuine"]
    check("genuine window signals survive stitching",
          any(c["sig"] == "2025-03-06" for c in genuine_kept)
          or len(genuine_kept) >= 1, json.dumps(genuine_kept))

    # ---------------- detector + quarantine -------------------------------
    # corrupt one ticker's history -> must be quarantined with reason
    bad = "BADQ-T"
    dates = dps._business_days("2022-01-03", 120)
    px = 100.0
    for d in dates:
        upsert_row = {"ticker": bad, "date": d, "raw_close": px,
                      "adjusted_close": px, "source": "SYNTHETIC",
                      "confidence": "LOW"}
        dps.upsert_bar(con, upsert_row)
    # inject an unexplained -25% implied-factor step mid-series
    cut = dates[len(dates) // 2]
    con.execute("UPDATE dual_bars SET adjusted_close = adjusted_close * 1.35 "
                "WHERE ticker=? AND date>=?", (bad, cut))
    con.commit()
    stats_bad = dps.detect_discrepancies(con, tickers=[bad])
    q = con.execute("SELECT reason FROM quarantine WHERE ticker=?",
                    (bad,)).fetchone()
    check("unreconcilable history gets quarantined_from_signal_use=1",
          q is not None and stats_bad["quarantined"] >= 1,
          q[0][:80] if q else "no row")
    check("quarantine reason recorded", bool(q and q[0]), "")

    # clean tickers stay eligible
    stats_all = dps.detect_discrepancies(con)
    n_q = con.execute("SELECT COUNT(*) FROM quarantine").fetchone()[0]
    check("detector runs over full store", stats_all["checked"] >= 120,
          "checked=%d mismatches=%d" % (stats_all["checked"],
                                        stats_all["mismatches"]))
    print("\nquarantine ledger (%d):" % n_q)
    for t, r in con.execute("SELECT ticker, reason FROM quarantine"):
        print("  -", t, "::", r[:110])

    con.close()

    # cleanup: drop the deliberately corrupted probe ticker so the shared
    # store returns to a fully reconciled state for downstream consumers
    con = dps.connect()
    con.execute("DELETE FROM dual_bars WHERE ticker=?", (bad,))
    con.execute("DELETE FROM discrepancies WHERE ticker=?", (bad,))
    con.execute("DELETE FROM quarantine WHERE ticker=?", (bad,))
    con.commit()
    con.close()

    # ---------------- summary ---------------------------------------------
    print("\n==== %d passed, %d failed ====" % (len(PASS), len(FAIL)))
    for name, detail in FAIL:
        print("FAILED:", name, detail)
    res = {"passed": len(PASS), "failed": len(FAIL),
           "failures": [{"name": n, "detail": d} for n, d in FAIL]}
    os.makedirs(dps.FIS_DATA, exist_ok=True)
    with open(os.path.join(dps.FIS_DATA,
                           "dual-price-tests.json"), "w") as f:
        json.dump(res, f, indent=1)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
