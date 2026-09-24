#!/usr/bin/env python3
"""OVERNIGHT-W3b -- Independent TAX+RISK validation of the FIS engines.

Validates (against hand-computed oracles written here, NOT shared with
engine code paths):

  TAX   : calcs_household.py + taxlot_ext.py
    - realized gain for FIFO / LIFO / SPECIFIC_ID recomputed from raw
      lots in integer cents and compared to the engine
    - holding-period classification boundary at exactly 365 / 366 days
    - TLH candidate ranking vs an independent loss sort (incl. ties)
    - wash-sale +/-30d window: replacement buy at -30/-29/0/+29/+30
      flags, +31/-31 does NOT
    - charitable lot = highest basis-per-share LONG-TERM lot
    - asset-location records carry ADVISORY-NOT-TAX-ADVICE
    - FLAGONLY preserved (adjustments_made == 0, caveats verbatim)
    - rule_version present on every record
    - missing price => typed error, not silent zero/skip

  RISK  : risk_engine.py
    - position_risk vs hand-computed ann_vol / maxdd / ES95
    - position->portfolio aggregation matches the weighted covariance
      identity on 100 seeded random cases (+ covariance-matrix branch)
    - singular covariance handled without NaN
    - extreme position (weight 1.0 single name) handled
    - stale-price disclosure when the data window is old
    - missing closes => typed error
    - correlation break (rho -> 1.0) increases port_vol monotonically
    - reverse_stress converges on fixtures
    - kill_switch fires EXACTLY at the configured breach, not before
    - disclosure block complete on every result

  GOVERNANCE
    - human-approval boundary scan: any function proposing an ACTION
      must refuse without an approval flag

ASCII only. NumPy-backed risk validation. No network. No git.

Usage:
    python tools/test_validation_taxrisk.py            # full run
    python tools/test_validation_taxrisk.py --filter WASH
"""

from __future__ import annotations

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIS_DIR = os.path.join(HERE, "fis")
if FIS_DIR not in sys.path:
    sys.path.insert(0, FIS_DIR)

import calcs_household as ch  # noqa: E402
import taxlot_ext as tx  # noqa: E402
import risk_engine as rk  # noqa: E402

REPRO = "python tools/test_validation_taxrisk.py"

# ---------------------------------------------------------------------------
# Result ledger
# ---------------------------------------------------------------------------

RESULTS = []  # (status, cid, severity, detail)


def record(cid, ok, severity_on_fail="LOW", detail=""):
    status = "PASS" if ok else "FAIL"
    RESULTS.append((status, cid, severity_on_fail if not ok else "-", detail))
    print("[%s] %-46s sev=%s %s"
          % (status, cid, "-" if ok else severity_on_fail, detail))
    return ok


def finding(cid, detail, severity="MEDIUM"):
    RESULTS.append(("FINDING", cid, severity, detail))
    print("[FINDING] %-38s sev=%s %s" % (cid, severity, detail))


def summary_exit():
    fails = [r for r in RESULTS if r[0] == "FAIL"]
    finds = [r for r in RESULTS if r[0] == "FINDING"]
    print("")
    print("TOTALS: %d checks | %d PASS | %d FAIL | %d FINDINGS"
          % (len(RESULTS),
             sum(1 for r in RESULTS if r[0] == "PASS"),
             len(fails), len(finds)))
    for st, cid, sev, det in fails:
        print("  FAIL(%s) %s :: %s\n    repro: %s" % (sev, cid, det, REPRO))
    for st, cid, sev, det in finds:
        print("  FINDING(%s) %s :: %s" % (sev, cid, det))
    return 1 if fails else 0


# ---------------------------------------------------------------------------
# Independent tax oracle (written from the documented cent-exact policy,
# NOT imported from engine internals beyond the public cent helpers).
# ---------------------------------------------------------------------------

def oracle_sell(lots, shares, price, sale_day, method,
                specific_ids=None, lt_threshold_days=366):
    """Recompute a lot-matched sale from RAW lots in integer cents.

    lots: list of dicts {lot_id, acquire_date, shares,
                         cost_per_share_cents, acquire_day}
    Returns list of (lot_id, proceeds_cents, basis_cents, gain_cents,
                     long_term_bool) in consumption order.
    """
    if method == ch.FIFO:
        queue = sorted(lots, key=lambda l: (l["acquire_date"],
                                            l["acquire_day"]))
    elif method == ch.LIFO:
        queue = sorted(lots, key=lambda l: (l["acquire_date"],
                                            l["acquire_day"]),
                       reverse=True)
    elif method == ch.SPECIFIC_ID:
        by_id = {l["lot_id"]: l for l in lots}
        queue = [by_id[i] for i in (specific_ids or [])]
    else:
        raise ValueError("bad method %r" % method)

    remaining = float(shares)
    plan = []
    for lot in queue:
        if remaining <= 1e-12:
            break
        take = min(remaining, float(lot["shares"]))
        if take <= 1e-12:
            continue
        plan.append((lot, take))
        remaining -= take
    if remaining > 1e-12:
        raise ValueError("oracle: insufficient shares")

    proceeds_total = ch.to_cents(float(shares) * float(price))
    allocated = 0
    out = []
    n = len(plan)
    for idx, (lot, take) in enumerate(plan):
        if idx == n - 1:
            p = proceeds_total - allocated  # documented last-lot true-up
        else:
            p = ch._round_cents(proceeds_total * (take / shares))
            allocated += p
        basis = ch._round_cents(take * int(lot["cost_per_share_cents"]))
        holding = int(sale_day) - int(lot["acquire_day"])
        out.append((lot["lot_id"], p, basis, p - basis,
                    holding >= lt_threshold_days))
    return out


def mk_lot_dict(lot):
    return {"lot_id": lot.lot_id, "acquire_date": lot.acquire_date,
            "shares": lot.shares,
            "cost_per_share_cents": lot.cost_per_share_cents,
            "acquire_day": lot.acquire_day}


def engine_sell_results_match(engine_results, oracle_rows, cid):
    """Per-lot multiset comparison of engine SaleResults vs oracle rows."""
    eng = sorted((r.lot_id, r.proceeds_cents, r.cost_basis_cents,
                  r.gain_cents, r.long_term) for r in engine_results)
    orc = sorted(oracle_rows)
    return record(cid, eng == orc,
                  "HIGH",
                  "engine=%s oracle=%s" % (eng, orc) if eng != orc else "")


# ---------------------------------------------------------------------------
# TAX validations
# ---------------------------------------------------------------------------

def validate_tax():
    # --- T1: FIFO / LIFO / SPECIFIC_ID vs oracle --------------------------
    def build_pf():
        pf = ch.Portfolio()
        pf.add_lot(ch.Lot("A", "2024-01-02", 10.0, 10000, acquire_day=1))
        pf.add_lot(ch.Lot("B", "2024-03-01", 10.0, 12000, acquire_day=60))
        pf.add_lot(ch.Lot("C", "2024-06-01", 10.0, 8000, acquire_day=150))
        return pf

    raw = [mk_lot_dict(l) for l in build_pf().lots]

    pf_fifo = build_pf()
    res = pf_fifo.sell(15.0, 130.0, 400, "2025-02-04", method=ch.FIFO)
    engine_sell_results_match(
        res, oracle_sell(raw, 15.0, 130.0, 400, ch.FIFO), "TAX-FIFO-GAIN")

    pf_lifo = build_pf()
    res = pf_lifo.sell(15.0, 130.0, 400, "2025-02-04", method=ch.LIFO)
    engine_sell_results_match(
        res, oracle_sell(raw, 15.0, 130.0, 400, ch.LIFO), "TAX-LIFO-GAIN")

    pf_sid = build_pf()
    res = pf_sid.sell(15.0, 130.0, 400, "2025-02-04", method=ch.SPECIFIC_ID,
                      specific_lot_ids=["C", "A"])
    engine_sell_results_match(
        res, oracle_sell(raw, 15.0, 130.0, 400, ch.SPECIFIC_ID,
                         specific_ids=["C", "A"]), "TAX-SPECID-GAIN")

    # Odd-cent adversarial case: proceeds split must still be cent-exact
    # and sum exactly to the cent total (documented true-up policy).
    pf_odd = build_pf()
    res = pf_odd.sell(17.0, 91.13, 400, "2025-02-04", method=ch.FIFO)
    rows = oracle_sell(raw, 17.0, 91.13, 400, ch.FIFO)
    ok_sum = (sum(r[1] for r in rows) == ch.to_cents(17.0 * 91.13))
    ok_match = [(r.lot_id, r.proceeds_cents, r.cost_basis_cents,
                 r.gain_cents, r.long_term) for r in res]
    record("TAX-FIFO-ODDCENTS-EXACT",
           sorted(ok_match) == sorted(rows) and ok_sum,
           "HIGH",
           "allocated=%d total=%d"
           % (sum(r[1] for r in rows), ch.to_cents(17.0 * 91.13)))

    # Fractional shares.
    pf_fr = build_pf()
    res = pf_fr.sell(12.5, 104.44, 400, "2025-02-04", method=ch.FIFO)
    engine_sell_results_match(
        res, oracle_sell(raw, 12.5, 104.44, 400, ch.FIFO),
        "TAX-FIFO-FRACTIONAL")

    # --- T2: holding-period boundary at exactly 365 / 366 days ------------
    for days, want_lt, cid in ((365, False, "TAX-HOLD-365-IS-SHORT"),
                               (366, True, "TAX-HOLD-366-IS-LONG")):
        pf = ch.Portfolio()
        pf.add_lot(ch.Lot("H", "2024-01-02", 5.0, 10000, acquire_day=0))
        r = pf.sell(5.0, 120.0, days, "x")[0]
        record(cid, r.long_term is want_lt and r.holding_days == days,
               "MEDIUM",
               "holding=%d long_term=%s" % (r.holding_days, r.long_term))

    # --- T3: TLH ranking vs independent loss sort, incl. ties -------------
    pf = ch.Portfolio()
    pf.add_lot(ch.Lot("T_LOSS_BIG", "2024-01-02", 10.0, 20000,
                      acquire_day=1))     # loss vs px 150: 50000c
    pf.add_lot(ch.Lot("T_TIE_A", "2024-02-01", 10.0, 20000,
                      acquire_day=32))    # identical loss 50000c
    pf.add_lot(ch.Lot("T_TIE_B", "2024-03-01", 10.0, 20000,
                      acquire_day=61))    # identical loss 50000c
    pf.add_lot(ch.Lot("T_SMALL", "2024-04-01", 10.0, 15500,
                      acquire_day=92))    # loss 500c
    prices = {"T_LOSS_BIG": 150.0, "T_TIE_A": 150.0, "T_TIE_B": 150.0,
              "T_SMALL": 150.0}
    cands = tx.tax_loss_harvest_candidates(pf, prices, min_loss_cents=1,
                                           as_of_day=400)
    my_sort = sorted(
        cands, key=lambda c: -c["unrealized_loss_cents"])  # stable sort
    my_losses = {
        "T_LOSS_BIG": 10 * (20000 - 15000),
        "T_TIE_A": 10 * (20000 - 15000),
        "T_TIE_B": 10 * (20000 - 15000),
        "T_SMALL": 10 * (15500 - 15000),
    }
    ok_vals = all(c["unrealized_loss_cents"] == my_losses[c["lot_id"]]
                  for c in cands)
    record("TAX-TLH-RANKING-INCL-TIES",
           [c["lot_id"] for c in cands] == [c["lot_id"] for c in my_sort]
           and ok_vals,
           "MEDIUM",
           "order=%s" % [c["lot_id"] for c in cands])

    # --- T4: wash-sale window boundaries ----------------------------------
    # Sale on day 0; replacement buy placed at each offset. Original lot
    # acquired far in the past so it never sits in the window itself.
    flagged_expect = {-30: True, -29: True, 0: True, 29: True, 30: True,
                      31: False, -31: False}
    all_ok = True
    detail = []
    for off, want in sorted(flagged_expect.items()):
        pf = ch.Portfolio()
        pf.add_lot(ch.Lot("WS", "2020-01-02", 10.0, 20000, acquire_day=-1000))
        pf.history.append(("buy", off, 1.0))
        r = pf.sell(10.0, 150.0, 0, "sale-date", method=ch.FIFO)[0]
        got = r.wash_sale_flagged
        all_ok &= (got == want)
        detail.append("%+d:%s" % (off, "F" if got else "-"))
    record("TAX-WASH-WINDOW-BOUNDARIES", all_ok, "HIGH",
           "offset->flag %s (expect F at -30/-29/0/+29/+30, '-' at +/-31)"
           % ",".join(detail))

    # --- T5: charitable lot = highest basis-per-share LONG-TERM -----------
    pf = ch.Portfolio()
    pf.add_lot(ch.Lot("LT_MID", "2023-01-02", 10.0, 3000, acquire_day=10))
    pf.add_lot(ch.Lot("LT_HI", "2023-03-01", 10.0, 9000, acquire_day=70))
    pf.add_lot(ch.Lot("ST_HI", "2025-07-01", 10.0, 99000, acquire_day=900))
    char = tx.charitable_lot_candidates(pf, as_of_day=1000)
    record("TAX-CHARITABLE-HIGHEST-BASIS-LT",
           len(char) == 2 and char[0]["lot_id"] == "LT_HI"
           and char[0]["cost_per_share_cents"] == 9000
           and all(r["long_term"] for r in char),
           "MEDIUM",
           "order=%s" % [r["lot_id"] for r in char])
    # Tie on basis/share -> older acquire_date first.
    pf2 = ch.Portfolio()
    pf2.add_lot(ch.Lot("YOUNG", "2024-01-02", 10.0, 7000, acquire_day=700))
    pf2.add_lot(ch.Lot("OLD", "2023-01-02", 10.0, 7000, acquire_day=10))
    char2 = tx.charitable_lot_candidates(pf2, as_of_day=1200)
    record("TAX-CHARITABLE-TIE-BREAK-OLDEST",
           [r["lot_id"] for r in char2] == ["OLD", "YOUNG"],
           "LOW",
           "order=%s" % [r["lot_id"] for r in char2])

    # --- T6: asset-location ADVISORY label on EVERY record ----------------
    loc = tx.asset_location()
    ok = (loc.get("label") == tx.ADVISORY_LABEL
          and all(rec.get("label") == tx.ADVISORY_LABEL
                  for rec in loc["records"]))
    record("TAX-ASSETLOCATION-LABEL-EVERYWHERE", ok, "MEDIUM",
           "%d records" % len(loc["records"]))

    # --- T7: FLAGONLY preserved -------------------------------------------
    pf = ch.Portfolio()
    pf.add_lot(ch.Lot("FO", "2024-01-02", 10.0, 20000, acquire_day=1))
    pf.history.append(("buy", 25, 1.0))  # replacement inside window
    res = pf.sell(10.0, 180.0, 40, "2024-02-10")
    raw_gain = 10 * 18000 - 10 * 20000  # -20000c, UNADJUSTED
    rep = tx.wash_sale_report(res)
    ok = (rep["adjustments_made"] == 0
          and res[0].wash_sale_flagged is True
          and res[0].gain_cents == raw_gain
          and rep["flags"][0]["adjusted"] is False
          and rep["definitive"] is False)
    record("TAX-FLAGONLY-NO-ADJUSTMENT", ok, "HIGH",
           "gain=%d (raw %d), adjustments_made=%d"
           % (res[0].gain_cents, raw_gain, rep["adjustments_made"]))
    caveats_ok = all(c in rep["unresolved_cross_account_caveats"]
                     for c in tx.UNRESOLVED_CROSS_ACCOUNT_CAVEATS)
    record("TAX-FLAGONLY-CAVEATS-VERBATIM", caveats_ok, "HIGH",
           "caveats=%d verbatim=%s"
           % (rep["caveat_count"], caveats_ok))

    # --- T8: rule_version on every record ---------------------------------
    versions_ok = True
    for c in cands:
        versions_ok &= c.get("rule_version") == tx.RULE_VERSION
    for r in char + char2:
        versions_ok &= r.get("rule_version") == tx.RULE_VERSION
    versions_ok &= rep.get("rule_version") == tx.RULE_VERSION
    for f in rep["flags"]:
        versions_ok &= f.get("rule_version") == tx.RULE_VERSION
    versions_ok &= loc.get("rule_version") == tx.RULE_VERSION
    for rec_ in loc["records"]:
        versions_ok &= rec_.get("rule_version") == tx.RULE_VERSION
    rb = tx.rebalancing_tax_cost(
        [{"portfolio": build_pf(), "shares": 5.0, "price_per_share": 130.0,
          "day": 1100, "date": "2026-08-25"}],
        stcg_rate=0.32, ltcg_rate=0.15)  # PARAMETER rates, caller-supplied
    versions_ok &= rb.get("rule_version") == tx.RULE_VERSION
    for t in rb["trades"]:
        versions_ok &= t.get("rule_version") == tx.RULE_VERSION
    record("TAX-RULEVERSION-EVERY-RECORD", bool(versions_ok), "MEDIUM",
           "rule_version=%s" % tx.RULE_VERSION)

    # --- T9: missing price => typed error, not silent skip ----------------
    pf = ch.Portfolio()
    pf.add_lot(ch.Lot("P1", "2024-01-02", 10.0, 20000, acquire_day=1))
    pf.add_lot(ch.Lot("P2", "2024-01-02", 10.0, 20000, acquire_day=1))
    partial_prices = {"P1": 150.0}  # P2 has NO price
    raised = None
    try:
        out = tx.tax_loss_harvest_candidates(pf, partial_prices,
                                             min_loss_cents=1,
                                             as_of_day=400)
    except (KeyError, ValueError, LookupError) as exc:
        raised = type(exc).__name__
    if raised is not None:
        record("TAX-MISSING-PRICE-TYPED-ERROR", True, "-",
               "raised %s" % raised)
    else:
        record("TAX-MISSING-PRICE-TYPED-ERROR", False, "HIGH",
               "NO error; P2 silently dropped from candidates "
               "(taxlot_ext.py line ~160 'silently skip')")


# ---------------------------------------------------------------------------
# RISK validations
# ---------------------------------------------------------------------------

REQUIRED_DISCLOSURE_KEYS = [
    "horizon", "data_window", "model_id", "confidence",
    "included_risks", "excluded_risks", "staleness", "sensitivity",
]


def hand_position_risk(closes):
    """Independent reimplementation for cross-checking (float math)."""
    rets = [closes[i] / closes[i - 1] - 1.0
            for i in range(1, len(closes))]
    n = len(rets)
    mu = sum(rets) / n
    var = sum((r - mu) ** 2 for r in rets) / (n - 1)
    ann_vol = math.sqrt(var) * math.sqrt(252)
    peak, mdd = closes[0], 0.0
    for c in closes:
        peak = max(peak, c)
        mdd = min(mdd, (c - peak) / peak)
    # Rockafellar-Uryasev variational oracle: independent from the engine's
    # sorted fractional-tail integral, including discrete boundary mass.
    losses = [-r for r in rets]
    es95 = min(t + math.fsum(max(loss - t, 0.0) for loss in losses) / (0.05 * n)
               for t in losses)
    return ann_vol, abs(mdd), es95


def validate_risk():
    # --- R1: position_risk vs hand computation ----------------------------
    closes = [100.0, 108.0, 97.0, 112.0, 90.0, 95.0, 121.0, 88.0, 102.0,
              140.0, 133.0]
    pos = rk.position_risk(closes)
    a_vol, a_mdd, a_es = hand_position_risk(closes)
    ok = (abs(pos["ann_vol"] - round(a_vol, 6)) <= 1e-6
          and abs(pos["maxdd"] - round(a_mdd, 6)) <= 1e-6
          and abs(pos["es95"] - round(a_es, 6)) <= 1e-6)
    record("RISK-POSITION-HANDCOMPUTED", ok, "HIGH",
           "engine(vol=%.6f mdd=%.6f es95=%.6f) vs hand(%.6f %.6f %.6f)"
           % (pos["ann_vol"], pos["maxdd"], pos["es95"], a_vol, a_mdd, a_es))

    rng_syn = random.Random(7)
    ser = [100.0]
    for _ in range(250):
        ser.append(max(ser[-1] * (1.0 + rng_syn.gauss(0.0004, 0.011)), 0.01))
    pos2 = rk.position_risk(ser)
    b_vol, b_mdd, b_es = hand_position_risk(ser)
    ok2 = (abs(pos2["ann_vol"] - round(b_vol, 6)) <= 1e-6
           and abs(pos2["maxdd"] - round(b_mdd, 6)) <= 1e-6
           and abs(pos2["es95"] - round(b_es, 6)) <= 1e-6)
    record("RISK-POSITION-SYNTHETIC-250", ok2, "HIGH",
           "vol %.6f/%.6f mdd %.6f/%.6f es95 %.6f/%.6f"
           % (pos2["ann_vol"], b_vol, pos2["maxdd"], b_mdd,
              pos2["es95"], b_es))

    # --- R2: aggregation identity, 100 random cases ------------------------
    rng = random.Random(20260826)
    mismatches = []
    for case_i in range(100):
        n = rng.randint(1, 6)
        vols = [rng.uniform(0.05, 0.60) for _ in range(n)]
        rho = rng.uniform(-0.15, 0.95)
        # Public contract: relative allocations, not leveraged notionals.
        raw = [rng.uniform(0.05, 1.0) for _ in range(n)]
        total = sum(raw)
        w = [x / total for x in raw]
        corr = (lambda i, j, r=rho: 1.0 if i == j else r)
        got = rk.portfolio_risk(w, vols, corr_func=corr)["port_vol"]
        want = math.sqrt(sum(
            w[i] * w[j] * vols[i] * vols[j] * corr(i, j)
            for i in range(n) for j in range(n)))
        if abs(got - round(want, 6)) > 1e-6:
            mismatches.append((case_i, got, want))
        # covariance-matrix branch must agree with the corr_func branch
        cov = [[vols[i] * vols[j] * corr(i, j) for j in range(n)]
               for i in range(n)]
        # Percentage allocations must give the same independent covariance oracle.
        got_cov = rk.portfolio_risk([100.0 * x for x in w], cov)["port_vol"]
        if abs(got_cov - round(want, 6)) > 1e-6:
            mismatches.append((case_i, got_cov, want))
    record("RISK-AGG-IDENTITY-X100", not mismatches, "HIGH",
           "%d mismatches%s" % (len(mismatches),
                                " e.g. %s" % mismatches[:2]
                                if mismatches else ""))

    # --- R3: singular covariance -> explicit degradation, never NaN -------
    sing_cov = [[0.04, 0.04], [0.04, 0.04]]   # rank-1 singular PSD
    r_sing = rk.portfolio_risk([0.5, 0.5], sing_cov)
    zero_cov = [[0.0, 0.0], [0.0, 0.0]]       # fully degenerate
    r_zero = rk.portfolio_risk([0.5, 0.5], zero_cov)
    ok_nan = all(math.isfinite(r[k]) for r in (r_sing, r_zero)
                 for k in ("port_vol", "hhi_concentration"))
    closed_form = math.sqrt(0.04) * 1.0       # (w1+w2)^2 * a
    record("RISK-SINGULAR-COV-NO-NAN",
           ok_nan and abs(r_sing["port_vol"] - closed_form) <= 1e-6
           and r_zero["port_vol"] == 0.0, "MEDIUM",
           "singular vol=%.6f (closed form %.6f), zero vol=%.6f "
           "-- valid PSD singular/zero covariance, never NaN"
           % (r_sing["port_vol"], closed_form, r_zero["port_vol"]))
    # Corrupt covariance is refused, never repaired into a zero-risk report.
    refused = False
    try:
        rk.portfolio_risk([0.5, 0.5], [[0.04, -0.08], [-0.08, 0.04]])
    except ValueError:
        refused = True
    record("RISK-NEGATIVE-VARIANCE-REFUSED",
           refused and r_sing["variance_clamped"] is False
           and r_zero["variance_clamped"] is False,
           "MEDIUM", "non-PSD refused; valid singular/zero PSD accepted")

    # --- R4: extreme positions (weight 1.0 single name) -------------------
    r_one = rk.portfolio_risk([1.0], [0.37])
    r_one_two = rk.portfolio_risk([1.0, 0.0], [0.37, 0.20])
    ok = (abs(r_one["port_vol"] - 0.37) <= 1e-6
          and r_one["top_name_share"] == 1.0
          and r_one["hhi_concentration"] == 1.0
          and abs(r_one_two["port_vol"] - 0.37) <= 1e-6
          and r_one_two["top_name_share"] == 1.0)
    record("RISK-EXTREME-WEIGHT-ONE", ok, "MEDIUM",
           "vol=%s top=%s hhi=%s"
           % (r_one["port_vol"], r_one["top_name_share"],
              r_one["hhi_concentration"]))

    # --- R5: actual observation time must reach the disclosure ------------
    unknown = rk.position_risk([100.0, 101.0, 102.0])["disclosure"]
    old = rk.position_risk([100.0, 101.0, 102.0], as_of="1999-01-01",
                           report_date="2026-09-12")["disclosure"]
    record("RISK-STALE-DISCLOSURE-PRESENT",
           "UNKNOWN" in unknown["staleness"]
           and old["is_stale"] is True
           and old["data_as_of"] == "1999-01-01", "HIGH",
           "unknown=%s; old=%s; as_of=%s" % (
               unknown["staleness"], old["staleness"], old["data_as_of"]))

    # --- R6: missing closes => typed error --------------------------------
    errs = []
    for bad_series in ([], [100.0], [100.0, 101.0]):
        try:
            rk.position_risk(bad_series)
            errs.append("%r accepted" % (bad_series,))
        except ValueError:
            pass
    try:
        rk.position_risk([100.0, None, 102.0])
        errs.append("[..., None, ...] accepted")
    except TypeError:
        pass  # typed error (TypeError), acceptable
    record("RISK-MISSING-CLOSES-TYPED-ERROR", not errs, "MEDIUM",
           "; ".join(errs) if errs else
           "short series -> ValueError, None element -> TypeError")

    # The inherited untyped crash must now be a deliberate input refusal.
    refused = False
    try:
        rk.position_risk([0.0, 0.0, 0.0])
    except ValueError:
        refused = True
    record("RISK-ZERO-SERIES-TYPED-REFUSAL", refused, "LOW",
           "all-zero observations must raise ValueError")

    # --- R7: correlation break rho -> 1.0 raises port_vol monotonically ---
    vols = [0.20, 0.35]
    w = [0.5, 0.5]
    rhos = [round(x * 0.05, 2) for x in range(0, 21)]  # 0.00 .. 1.00
    vols_out = [rk.portfolio_risk(
        w, vols, corr_func=lambda i, j, r=rho: 1.0 if i == j else r
    )["port_vol"] for rho in rhos]
    mono = all(vols_out[i] <= vols_out[i + 1] + 1e-12
               for i in range(len(vols_out) - 1))
    strict_over_range = vols_out[-1] > vols_out[0]
    record("RISK-CORR-BREAK-MONOTONIC", mono and strict_over_range, "HIGH",
           "rho0=%.4f rho1=%.4f monotone=%s (last must equal mean vol "
           "%.4f)" % (vols_out[0], vols_out[-1], mono,
                      sum(vols) / 2))

    # --- R8: reverse_stress converges on fixtures --------------------------
    conv_ok = True
    detail = []
    for cur, fl in ((8.0, 3.0), (12.0, 4.0), (30.0, 3.0)):
        rev = rk.reverse_stress(cur, fl)
        liq_at = cur * (1.0 - rev["breaching_decline_pct"] / 100.0)
        analytic = (1.0 - fl / cur) * 100.0
        ok = (abs(liq_at - fl) <= 0.01
              and abs(rev["breaching_decline_pct"] - analytic) <= 0.01)
        conv_ok &= ok
        detail.append("cur=%.0f->decline=%.4f%% (analytic %.4f%%)"
                      % (cur, rev["breaching_decline_pct"], analytic))
    breached = rk.reverse_stress(2.0, 3.0)
    conv_ok &= (breached["already_breached"] is True
                and breached["breaching_decline_pct"] == 0.0)
    record("RISK-REVERSE-STRESS-CONVERGES", conv_ok, "MEDIUM",
           "; ".join(detail) + "; breached-case handled")

    # --- R9: kill_switch fires EXACTLY at breach, not before --------------
    ks_ok = True
    cases = [
        ({"v": 19.999}, {"v": 20.0}, False),   # just below -> no fire
        ({"v": 20.0}, {"v": 20.0}, False),     # AT the limit -> no fire
        ({"v": 20.0001}, {"v": 20.0}, True),   # past -> fire
        ({"v": 5.0}, {"v": {"min": 5.0}}, False),   # at min -> no fire
        ({"v": 4.999}, {"v": {"min": 5.0}}, True),  # below min -> fire
        ({"v": 5.001}, {"v": {"min": 5.0}}, False),
    ]
    for metrics, limits, want in cases:
        got = rk.kill_switch(metrics, limits)
        ks_ok &= (got is want)
    # Required limits cannot disappear because a feed omitted its metric.
    ks_ok &= rk.kill_switch({"other": 999.0}, {"v": 1.0}) is True
    # An unrelated extra metric is harmless when every required metric exists.
    ks_ok &= rk.kill_switch({"v": 0.5, "other": 999.0}, {"v": 1.0}) is False
    record("RISK-KILL-SWITCH-EXACT-BREACH", ks_ok, "HIGH",
           "strict '>' semantics verified at/below/above scalar and "
           "min/max dict limits; missing required metrics refuse, extras ignored")

    # --- R10: disclosure block complete on EVERY result --------------------
    def disc_complete(d):
        return (isinstance(d, dict)
                and all(k in d and d[k] not in (None, "") for k in
                        REQUIRED_DISCLOSURE_KEYS))

    results_with_disclosure = [
        ("position_risk", rk.position_risk(ser)),
        ("portfolio_risk", rk.portfolio_risk([0.6, 0.4], [0.2, 0.3])),
        ("household_risk", rk.household_risk(5.0, 7000.0)),
        ("reverse_stress", rk.reverse_stress(8.0, 3.0)),
        ("historical_stress_2022q1", rk.historical_stress_2022q1(
            {"X": 1000.0}, lambda t: None)),
        ("hypothetical_shock", rk.hypothetical_shock()),
    ]
    missing = [name for name, res in results_with_disclosure
               if not disc_complete(res.get("disclosure"))]
    record("RISK-DISCLOSURE-COMPLETE", not missing, "MEDIUM",
           "required=%s missing_on=%s"
           % (",".join(REQUIRED_DISCLOSURE_KEYS),
              ",".join(missing) if missing else "none"))

    # --- R11: household label bands sanity (supporting) --------------------
    hh = rk.household_risk(4.0, 7500.0)
    record("RISK-HOUSEHOLD-BAND-VALID",
           hh["breach_probability_label"] in ("LOW", "MED", "HIGH"),
           "LOW", "label=%s" % hh["breach_probability_label"])


# ---------------------------------------------------------------------------
# Governance: human-approval boundary
# ---------------------------------------------------------------------------

ACTION_PROPOSERS = [
    ("tools/fis/portfolio_engine.py", "propose_rebalance"),
    ("tools/fis/taxlot_ext.py", "rebalancing_tax_cost"),
]


def validate_governance():
    """BEHAVIOURAL approval-gate probe.

    The previous version searched each source file for the substring
    "approve" and passed if it appeared anywhere. That is a string-marker
    scan, not a control: one comment, docstring, or unrelated error
    message satisfies it, and it cannot distinguish an enforcement point
    from a mention.

    This version EXERCISES the gate. It builds a real proposal and asserts
    that nothing in the emitted object can be mistaken for authorisation,
    and that the state machine has no reachable execution state. It fails
    closed if the modules cannot be imported.
    """
    try:
        import approval
        import portfolio_engine as pe
    except Exception as exc:                       # noqa: BLE001
        finding("GOV-APPROVAL-MODULE-UNIMPORTABLE",
                "cannot exercise the approval gate: %s: %s"
                % (type(exc).__name__, exc), "HIGH")
        return

    # --- 1. No route to execution exists in the state machine ------------
    reachable = approval.reachable_states()
    record("GOV-NO-ROUTE-TO-EXECUTION",
           approval.STATE_APPROVED_FOR_EXECUTION not in reachable
           and len(approval.EXECUTABLE_STATES) == 0, "HIGH",
           "reachable=%s executable=%s"
           % (sorted(reachable), sorted(approval.EXECUTABLE_STATES)))

    # --- 2. A real proposal is inert everywhere a consumer might look ----
    pf = {
        "cash": 40000.0,
        "holdings": [
            {"ticker": "ZPHR", "issuer": "ZPHR", "asset_class": "equity",
             "account": "taxable-001", "quantity": 900.0, "price": 260.0,
             "lots": [{"lot_id": "Z1", "quantity": 900.0,
                       "cost_basis": 100.0, "acquire_date": "2020-01-02",
                       "term": "long"}]},
            {"ticker": "BND", "issuer": "BND", "asset_class": "bond",
             "account": "taxable-001", "quantity": 100.0, "price": 100.0,
             "lots": [{"lot_id": "B1", "quantity": 100.0,
                       "cost_basis": 100.0, "acquire_date": "2020-01-02",
                       "term": "long"}]},
        ],
    }
    # Targets and bands are FRACTIONS (0.60 == 60%), matching the engine's
    # own selftest constants. This book is 82.4% equity against a 60% +/-
    # 5pp band, so it breaches and produces real legs.
    out = pe.propose_rebalance(
        pf, {"equity": 0.60, "bond": 0.30, "cash": 0.10},
        {"equity": {"low": 0.05, "high": 0.05},
         "bond": {"low": 0.05, "high": 0.05},
         "cash": {"low": 0.05, "high": 0.05}},
        {"max_single_issuer_pct": 25.0, "min_cash_pct": 2.0,
         "max_turnover_pct": 50.0})

    trades = ((out.get("action") or {}).get("trades") or [])
    legs_inert = all(
        tr.get("executable") is False and tr.get("authority") == "NONE"
        for tr in trades)
    record("GOV-EVERY-TRADE-LEG-INERT", bool(trades) and legs_inert, "HIGH",
           "%d legs, all executable=False" % len(trades))

    exec_block = out.get("execution") or {}
    record("GOV-EXECUTION-BLOCK-PRESENT",
           exec_block.get("authorized") is False
           and out.get("decision", {}).get("is_executable") is False
           and out.get("decision", {}).get("authority_level") == "NONE",
           "HIGH", "authorized=%s state=%s"
           % (exec_block.get("authorized"),
              out.get("decision", {}).get("state")))

    # --- 3. The boundary enforcer agrees --------------------------------
    try:
        approval.enforce_not_executable(out, where="validation_probe")
        enf_ok, detail = True, "accepted"
    except approval.ApprovalViolation as exc:
        enf_ok, detail = False, exc.code
    record("GOV-BOUNDARY-ENFORCER-ACCEPTS", enf_ok, "HIGH", detail)

    refused = False
    try:
        approval.enforce_not_executable(
            {"approved": True, "is_executable": True}, where="forged")
    except approval.ApprovalViolation:
        refused = True
    record("GOV-FORGED-AUTHORIZATION-REFUSED", refused, "HIGH",
           "approved=True + is_executable=True rejected")

    # --- 4. A VALID signed grant still cannot authorise EXECUTION --------
    binding = approval.DecisionBinding(
        decision_id="GOV-PROBE-1", decision_type="rebalance_proposal",
        legs=(approval.Leg("L0", "SELL", "ZPHR", "taxable-001",
                           quantity=1.0, notional_usd=260.0),),
        account="taxable-001", model_version="m", data_version="d",
        policy_version="p", code_hash="c", price_as_of="2026-08-28",
        expires_at="2026-09-30T00:00:00Z", requested_by="agent")
    rec = approval.DecisionRecord(
        binding=binding, state=approval.STATE_HUMAN_APPROVAL_REQUIRED)
    auth = approval.ApprovalAuthority(
        approval.generate_key(), clock=lambda: "2026-08-28T12:00:00Z")
    # Approval requires a REGISTERED human. A denylist of machine names is
    # not a control (W9-B A6-13), so an unregistered identity is refused
    # and a machine-shaped one cannot even be registered.
    auth.registry.register("operator@household", "Operator",
                           registered_by="validation-probe",
                           when_utc="2026-08-01T00:00:00Z")
    grant = auth.issue(rec, "operator@household", ttl_seconds=3600)
    vr = auth.authorize(rec, grant=grant, now="2026-08-28T12:30:00Z",
                        purpose="EXECUTION")
    record("GOV-GRANT-CANNOT-AUTHORIZE-EXECUTION",
           (not vr.ok) and vr.as_dict()["authorized_for_execution"] is False
           and "EXECUTION_NOT_AUTHORIZED" in vr.codes, "HIGH",
           "codes=%s" % vr.codes)

    # --- 5. The tax proposer refuses an unpriceable input ----------------
    pf_t = ch.Portfolio()
    pf_t.add_lot(ch.Lot("G1", "2024-01-02", 10.0, 20000, acquire_day=1))
    blocked, why = False, "no refusal"
    try:
        tx.rebalancing_tax_cost(
            [{"portfolio": pf_t, "shares": 5.0, "price_per_share": 0.0,
              "day": 1100, "date": "2026-08-28"}],
            stcg_rate=0.32, ltcg_rate=0.15)
    except tx.MissingPriceError as exc:
        blocked, why = True, exc.gaps[0].code
    record("GOV-TAX-PROPOSER-REFUSES-UNPRICEABLE", blocked, "HIGH", why)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv):
    flt = None
    if "--filter" in argv:
        flt = argv[argv.index("--filter") + 1].upper()

    def run(fn):
        # --filter matches check-ID prefixes (e.g. WASH, STALE, KILL),
        # not the section function name.
        if flt is None:
            fn()
            return
        captured = []
        orig_record = globals()["record"]
        globals()["record"] = (
            lambda cid, ok, sev="LOW", det="": (
                captured.append(cid) or orig_record(cid, ok, sev, det)
                if flt in cid.upper() else None))
        orig_finding = globals()["finding"]
        globals()["finding"] = (
            lambda cid, det, sev="MEDIUM": (
                captured.append(cid) or orig_finding(cid, det, sev)
                if flt in cid.upper() else None))
        try:
            fn()
        finally:
            globals()["record"] = orig_record
            globals()["finding"] = orig_finding
        if not captured:
            print("no checks matched filter %r in %s" % (flt, fn.__name__))

    run(validate_tax)
    run(validate_risk)
    run(validate_governance)
    return summary_exit()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
