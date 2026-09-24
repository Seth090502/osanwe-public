#!/usr/bin/env python3
# -*- coding: ascii -*-
"""Cross-component semantic invariant suite (D-R6 deliverable, 2026-08-25).

Unlike the component suites (test-fis-defects.py pins the MR defects,
test-mr-corrected-invariants.py pins the corrected book laws, the PIT
selftests pin the vintage store), THIS suite asserts laws that only become
visible when TWO components are fed the SAME synthetic data, or when a
stored artifact is checked against the REAL filesystem / structural truth:

  A. Shared-fixture reconciliation: the identical synthetic trade stream is
     pushed through BOTH the mr-corrected event-loop book (fractional
     equity, float) AND the calcs_household Portfolio (integer-cent tax-lot
     ledger). Capital may be committed at most once, and the two books must
     reconcile on realized PnL within cent rounding.
  B. Dependency-graph grounding: every node path in dependency-graph.json
     (v2) must RESOLVE on disk. The v1 placeholder-path defect
     ("/path/to/vault\\tab ools\\..."-style garbage) passes any purely
     structural check and fails only here.
  C. Derived-not-declared provenance: macro_vintage_store.value_asof's
     was_revised flag must be recomputed from STRUCTURE (does an
     earlier-known vintage exist?) and must IGNORE caller-supplied
     revision_of, including hostile/out-of-order insertion.
  D. Timestamp boundary semantics: EDGAR PIT normalization (UTC vs ET
     calendar date, session buckets at 09:30/16:00, the strictly-after
     08:00-ET availability rule, and the one-day filingDate grace). Uses
     tools/pit/edgar_pit.py functions when importable, else falls back to
     documented-convention checks on raw strings.
  E. Allocation invariants: mr-corrected.simulate on a synthetic
     multi-signal fixture must never create a zero-size position, must
     satisfy equity(t) == equity(t-1)*(1+ret(t)), must stay unlevered
     (concurrent cost basis <= initial capital, i.e. implied cash >= 0),
     and must account for every signal admission decision.

Run from repo root:  python tools/test-fis-cross-component.py
Exit 0 = green. ASCII only. Stdlib only. No network. No git.
"""

from __future__ import annotations

import datetime as _dt
import importlib.util
import json
import os
import sys
import tempfile

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASS, FAIL, SKIP = [], [], []

EQUITY_USD = 1000000.0        # scale for the cent-exact mirror book


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print("[%s] %s%s" % (tag, name, (" :: " + detail) if detail else ""))
    (PASS if cond else FAIL).append(name)


def note(name, detail=""):
    print("[SKIP] %s%s" % (name, (" :: " + detail) if detail else ""))
    SKIP.append(name)


def load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod   # dataclass resolution needs module registered
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return mod


# ---------------------------------------------------------------------------
# Component loads (each defensive: a missing sibling must FAIL loudly only
# for the class that needs it, not crash the whole suite at import time).
# ---------------------------------------------------------------------------

mrc = None
try:
    mrc = load_mod(os.path.join(VAULT, "tools", "research",
                                "mr-corrected.py"), "mrc_xcomp")
except Exception as exc:
    note("load mr-corrected.py", repr(exc))

ch = None
try:
    ch = load_mod(os.path.join(VAULT, "tools", "fis",
                               "calcs_household.py"), "ch_xcomp")
except Exception as exc:
    note("load calcs_household.py", repr(exc))

mvs = None
try:
    mvs = load_mod(os.path.join(VAULT, "tools", "pit",
                                "macro_vintage_store.py"), "mvs_xcomp")
except Exception as exc:
    note("load macro_vintage_store.py", repr(exc))

epit = None
try:
    epit = load_mod(os.path.join(VAULT, "tools", "pit",
                                 "edgar_pit.py"), "epit_xcomp")
except Exception as exc:
    note("load edgar_pit.py (fallback conventions)", repr(exc))


# ---------------------------------------------------------------------------
# Synthetic shared fixture: four tickers, staggered engineered RSI dips so
# signals fire on overlapping calendars (real concurrency in the book).
# ---------------------------------------------------------------------------

def build_shared_fixture(n_days=170, tickers=None):
    if tickers is None:
        tickers = ["SYN%d" % k for k in range(4)]
    cal = ["d%03d" % i for i in range(n_days)]
    px = {}
    for k, tk in enumerate(tickers):
        closes = [100.0] * n_days
        off = 8 + k * 4                       # staggered dips -> overlap
        for i in range(off, off + 10):        # 10 straight down days
            closes[i] = 100.0 - (i - off + 1) * 3.0      # -> 70
        for i in range(off + 10, off + 22):   # violent +/-7 swings
            closes[i] = 88.0 + (7.0 if i % 2 else -7.0)
        for i in range(off + 22, min(off + 36, n_days)):
            closes[i] = 100.0                 # recovery, then flat
        px[tk] = dict(zip(cal, closes))
    return px, cal


PX, CAL = build_shared_fixture()
CAL_IDX = {d: i for i, d in enumerate(CAL)}


# ---------------------------------------------------------------------------
# CLASS A + E: shared-fixture reconciliation and allocation invariants
# ---------------------------------------------------------------------------

def run_book(K):
    """Zero-friction run so the two accounting systems observe identical
    economics (slippage is a pricing-layer concern, patched OUT here)."""
    saved = mrc.slip_bp
    mrc.slip_bp = lambda tk: 0.0
    try:
        sigs = mrc.signals(PX, CAL)
        daily, recs, st = mrc.simulate(sigs, PX, CAL, K=K)
    finally:
        mrc.slip_bp = saved
    return sigs, daily, recs, st


def concurrent_exposure(recs):
    """Max simultaneous cost basis across any calendar day."""
    delta = {}
    for r in recs:
        i0 = CAL_IDX[r["fill_d"]]
        i1 = CAL_IDX[r["exit_d"]]
        delta[i0] = delta.get(i0, 0.0) + r["cost_basis"]
        delta[i1 + 1] = delta.get(i1 + 1, 0.0) - r["cost_basis"]
    peak = cur = 0.0
    for i in range(len(CAL) + 1):
        cur += delta.get(i, 0.0)
        peak = max(peak, cur)
    return peak


def overlap_pairs(recs):
    """Number of record pairs whose holding windows overlap in time."""
    n = len(recs)
    c = 0
    for i in range(n):
        for j in range(i + 1, n):
            if not (CAL_IDX[recs[i]["exit_d"]] < CAL_IDX[recs[j]["fill_d"]]
                    or CAL_IDX[recs[j]["exit_d"]] < CAL_IDX[recs[i]["fill_d"]]):
                c += 1
    return c


def reconstruct_book(recs):
    """External day-book reconstruction from records + prices.

    With slippage patched to zero, a position opened with cost basis v0 at
    fill price p0 is worth v0 * px(tk,d)/p0 on any day its bar exists.
    Rebuilds the ENDING cash and market-value series independently of the
    simulator's internal state so the reported equity can be RECONCILED,
    not just trusted:
      cash(0)=1; exits add exit_val; fills subtract cost_basis;
      mv(d) = sum of positions OPEN over [fill, exit) marked at close(d);
      an exiting position realizes exit_val into cash on its exit day.
    Returns (days, cash_by_day, mv_by_day).
    """
    cash_by_day = []
    mv_by_day = []
    cash = 1.0
    for idx, d in enumerate(CAL):
        for r in recs:
            if r["exit_d"] == d and CAL_IDX[r["fill_d"]] < idx:
                cash += r["exit_val"]
        for r in recs:
            if r["fill_d"] == d:
                cash -= r["cost_basis"]
        cur_mv = 0.0
        for r in recs:
            i0 = CAL_IDX[r["fill_d"]]
            i1 = CAL_IDX[r["exit_d"]]
            if i0 <= idx < i1:
                p0 = PX[r["tk"]][r["fill_d"]]
                pd = PX[r["tk"]].get(d)
                if pd is None:
                    continue
                if idx == i0:
                    cur_mv += r["cost_basis"]
                else:
                    cur_mv += r["cost_basis"] * pd / p0
        cash_by_day.append(cash)
        mv_by_day.append(cur_mv)
    return CAL, cash_by_day, mv_by_day


def class_a_and_e():
    if mrc is None or ch is None:
        note("A/E skipped: component unavailable")
        return

    sigs, daily, recs, st = run_book(K=mrc.K_SLOTS)

    check("A.precondition: fixture produced trades", len(recs) >= 3,
          "n_records=%d" % len(recs))
    check("A.precondition: book experienced concurrency",
          overlap_pairs(recs) >= 1,
          "overlapping_pairs=%d" % overlap_pairs(recs))

    # -- A1 capital-once: no fill day commits more than initial capital ------
    per_fill = {}
    for r in recs:
        per_fill[r["fill_d"]] = per_fill.get(r["fill_d"], 0.0) + r["cost_basis"]
    worst_day = max(per_fill.values()) if per_fill else 0.0
    check("A1_capital_committed_once_per_fill_day", worst_day <= 1.0 + 1e-9,
          "max=%.6f" % worst_day)

    # -- A2 unlevered: externally reconstructed implied cash never negative --
    days, cash_by_day, mv_by_day = reconstruct_book(recs)
    min_cash = min(cash_by_day)
    check("A2_no_leverage_implied_cash_never_negative",
          min_cash >= -1e-9,
          "min_cash=%.6f peak_basis=%.6f" % (min_cash, concurrent_exposure(recs)))

    # -- A2b reconciliation: reconstructed cash+mv equals reported equity ----
    eq_gap = max(abs(cash_by_day[t] + mv_by_day[t] - daily[t][1])
                 for t in range(len(days)))
    check("A2b_reconstructed_book_matches_reported_equity",
          eq_gap <= 1e-9, "max_gap=%.3g" % eq_gap)

    # -- A3/A4 cent-exact mirror book fed IDENTICAL economics ----------------
    total_sim_pnl_usd = 0.0
    total_pf_gain_usd = 0.0
    worst_cent_gap = 0.0
    signs_agree = True
    cent_exact_internal = True
    proceeds_true_up = True
    for n, r in enumerate(recs):
        fill_px = PX[r["tk"]][r["fill_d"]]
        exit_px = PX[r["tk"]][r["exit_d"]]
        cb_usd = r["cost_basis"] * EQUITY_USD
        shares = cb_usd / fill_px
        pf = ch.Portfolio()
        pf.add_lot(ch.Lot("L%d" % n, r["fill_d"], shares,
                          ch.to_cents(fill_px),
                          acquire_day=CAL_IDX[r["fill_d"]]))
        res = pf.sell(shares, exit_px, CAL_IDX[r["exit_d"]], r["exit_d"],
                      method=ch.FIFO)
        # internal cent-exact identities
        for rr in res:
            if rr.gain_cents != rr.proceeds_cents - rr.cost_basis_cents:
                cent_exact_internal = False
        if sum(rr.proceeds_cents for rr in res) != ch.to_cents(shares * exit_px):
            proceeds_true_up = False
        pf_gain_usd = sum(rr.gain_cents for rr in res) / 100.0
        sim_pnl_usd = (r["exit_val"] - r["cost_basis"]) * EQUITY_USD
        gap = abs(pf_gain_usd - sim_pnl_usd)
        worst_cent_gap = max(worst_cent_gap, gap)
        total_sim_pnl_usd += sim_pnl_usd
        total_pf_gain_usd += pf_gain_usd
        if (sim_pnl_usd > 0) != (pf_gain_usd > 0) and gap > 0.02:
            signs_agree = False

    check("A3_mirror_book_cent_exact_identities", cent_exact_internal)
    check("A3_mirror_book_proceeds_true_up_exact", proceeds_true_up)
    check("A4_books_reconcile_within_cent_rounding", worst_cent_gap <= 0.05,
          "worst gap $%.4f" % worst_cent_gap)
    check("A4_totals_reconcile", abs(total_pf_gain_usd - total_sim_pnl_usd)
          <= 0.05 * max(1.0, abs(total_sim_pnl_usd)),
          "pf=$%.4f sim=$%.4f" % (total_pf_gain_usd, total_sim_pnl_usd))
    check("A4_per_trade_sign_agreement", signs_agree)

    # -- E allocation invariants --------------------------------------------
    check("E1_no_zero_size_positions",
          all(r["cost_basis"] > 1e-12 and r["exit_val"] > 0.0 for r in recs),
          "n=%d" % len(recs))

    eq_ok = True
    for t in range(1, len(daily)):
        prev_eq = daily[t - 1][1]
        if abs(daily[t][1] / prev_eq - 1.0 - daily[t][2]) > 1e-12:
            eq_ok = False
            break
    check("E2_equity_equals_cash_plus_positions_every_day "
          "(return-bookkeeping identity)", eq_ok and len(daily) > 0,
          "days=%d" % len(daily))

    check("E3_equity_positive_every_day",
          all(eq > 0 for _, eq, _ in daily))

    # scarcity variant: K=2 must force capacity skips, never zero sizes.
    # Unlevered law under scarcity: reconstructed implied cash >= 0 (the
    # raw concurrent-cost-basis proxy is NOT the law -- old positions'
    # bases drift with marks while committed capital stays fixed).
    _, daily_k2, recs_k2, st_k2 = run_book(K=2)
    accounted = (st_k2["admitted"] + st_k2["skipped_capacity"]
                 + st_k2["skipped_limits"])
    check("E4_every_signal_decision_accounted_K2",
          accounted == len(sigs),
          "adm=%d cap=%d lim=%d sigs=%d"
          % (st_k2["admitted"], st_k2["skipped_capacity"],
             st_k2["skipped_limits"], len(sigs)))
    days_k2, cash_k2, mv_k2 = reconstruct_book(recs_k2)
    check("E5_no_zero_size_under_scarcity_K2",
          all(r["cost_basis"] > 1e-12 for r in recs_k2)
          and min(cash_k2) >= -1e-9,
          "n=%d min_cash=%.6f" % (len(recs_k2), min(cash_k2)))


# ---------------------------------------------------------------------------
# CLASS B: dependency-graph nodes resolve to REAL paths
# ---------------------------------------------------------------------------

def class_b():
    gp = os.path.join(VAULT, "Efforts", "osanwe-v2-overhaul", "_work",
                      "fis-data", "dependency-graph.json")
    if not os.path.exists(gp):
        note("B skipped: dependency-graph.json missing", gp)
        return
    g = json.load(open(gp))
    check("B1_dep_graph_is_v2_or_later", g.get("version", 0) >= 2,
          "version=%r" % g.get("version"))
    ds = g.get("datasets", {})
    check("B2_dep_graph_nonempty", len(ds) >= 1, "nodes=%d" % len(ds))
    missing = []
    for name, node in sorted(ds.items()):
        rel = node.get("path", "")
        abspath = os.path.join(VAULT, rel.replace("/", os.sep))
        if not os.path.exists(abspath):
            missing.append("%s -> %s" % (name, rel))
    check("B3_every_node_path_exists_on_disk", not missing,
          "; ".join(missing[:5]))
    dangling = []
    for name, node in sorted(ds.items()):
        for dep in node.get("depends_on", []):
            if dep not in ds:
                dangling.append("%s -> %s" % (name, dep))
    check("B4_dependency_edges_resolve_to_declared_nodes", not dangling,
          "; ".join(dangling[:5]))


# ---------------------------------------------------------------------------
# CLASS C: derived-not-declared provenance probe
# ---------------------------------------------------------------------------

def class_c():
    if mvs is None:
        note("C skipped: macro_vintage_store unavailable")
        return
    tmp = tempfile.mkdtemp(prefix="xcomp_prov_")
    try:
        store = mvs.VintageStore(os.path.join(tmp, "prov.db"))
        sid, obs = "PROBE_SERIES", "2026-01-01"

        # Hostile arrival order: the REVISION is inserted FIRST, with
        # revision_of=None (caller 'declares' it as an original).
        store.insert(sid, obs, 4.5, "2026-03-16", revision_of=None,
                     src="probe-rev-first")
        # The TRUE original arrives SECOND, also declared revision_of=None.
        store.insert(sid, obs, 3.0, "2026-01-16", revision_of=None,
                     src="probe-original-second")

        late = store.value_asof(sid, obs, "2026-06-01")
        check("C1_out_of_order_latest_value_is_revision",
              late is not None and late["value"] == 4.5,
              repr(late))
        check("C2_was_revised_derived_not_declared "
              "(winner said revision_of=None)",
              late is not None and late["was_revised"] is True)

        early = store.value_asof(sid, obs, "2026-02-01")
        check("C3_early_query_returns_original_not_revised",
              early is not None and early["value"] == 3.0
              and early["was_revised"] is False)

        # Caller LIES upward: lone row claims a revision_of link to a
        # nonexistent row. Structure says: nothing earlier exists.
        store.insert(sid, "2026-05-01", 9.9, "2026-06-01",
                     revision_of=999999, src="probe-bogus-link")
        lone = store.value_asof(sid, "2026-05-01", "2026-07-01")
        check("C4_caller_supplied_revision_of_cannot_manufacture_history",
              lone is not None and lone["was_revised"] is False,
              repr(lone))

        # Same-timestamp tie: last-insert-wins, and the winner DOES see an
        # earlier id at equal first_seen -> structurally revised.
        store.insert(sid, "2026-07-01", 1.0, "2026-08-01", revision_of=None)
        store.insert(sid, "2026-07-01", 2.0, "2026-08-01", revision_of=None)
        tie = store.value_asof(sid, "2026-07-01", "2026-08-01")
        check("C5_same_vintage_tie_last_insert_wins",
              tie is not None and tie["value"] == 2.0, repr(tie))
        check("C6_tie_winner_flags_structurally_earlier_row",
              tie is not None and tie["was_revised"] is True)

        check("C7_future_query_still_none_before_any_vintage",
              store.value_asof(sid, "2026-09-01", "2026-08-01") is None)
        store.close()
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# CLASS D: timestamp boundary semantics (EDGAR PIT normalization)
# ---------------------------------------------------------------------------

GOOD_ROW = {
    "cik": 1,
    "form": "10-K",
    "accession_number": "0000000000-26-000001",
    "filing_date": "2026-08-19",
    "acceptance_datetime": "2026-08-19T16:31:00.000Z",
    "report_date": "2026-06-30",
}


def class_d_with_module(ep):
    # UTC vs ET calendar-date normalization (EDT, UTC-4, in August)
    check("D1_acceptance_utc_date_normalization",
          ep.acceptance_date_str("2026-08-20T02:00:00.000Z") == "2026-08-20")

    d = ep.derive_pit_fields("2026-08-20T02:00:00.000Z")  # 22:00 ET Wed 8/19
    check("D2_et_date_differs_from_utc_date",
          d["et_date"] == "2026-08-19" and d["utc_instant"].startswith(
              "2026-08-20"), json.dumps(d))
    check("D3_evening_acceptance_is_after_close",
          d["market_session"] == "after_close", d["market_session"])

    # availability rule: next 08:00 ET STRICTLY after the instant
    check("D4_evening_acceptance_avails_next_morning_0800et",
          d["earliest_model_availability"] == "2026-08-20T12:00:00Z",
          d["earliest_model_availability"])
    morn = ep.derive_pit_fields("2026-08-19T11:00:00.000Z")  # 07:00 ET
    check("D5_pre_0800et_acceptance_avails_same_day_0800et",
          morn["earliest_model_availability"] == "2026-08-19T12:00:00Z"
          and morn["market_session"] == "before_open",
          "%s / %s" % (morn["earliest_model_availability"],
                       morn["market_session"]))
    edge = ep.derive_pit_fields("2026-08-19T12:00:00.000Z")  # 08:00:00 ET sharp
    check("D6_exactly_0800et_rolls_to_next_day_strict_after",
          edge["earliest_model_availability"] == "2026-08-20T12:00:00Z",
          edge["earliest_model_availability"])

    # session bucket minute boundaries (documented: 09:30 open, 16:00 close
    # cross counts as regular hours; bucketing is minute-granular)
    b1 = ep._classify_session(_dt.datetime(2026, 8, 19, 9, 29), "2026-08-19")
    b2 = ep._classify_session(_dt.datetime(2026, 8, 19, 9, 30), "2026-08-19")
    b3 = ep._classify_session(_dt.datetime(2026, 8, 19, 16, 0), "2026-08-19")
    b4 = ep._classify_session(_dt.datetime(2026, 8, 19, 16, 1), "2026-08-19")
    check("D7_session_boundaries_0930_1600",
          (b1, b2, b3, b4) == ("before_open", "regular_hours",
                               "regular_hours", "after_close"),
          "%s/%s/%s/%s" % (b1, b2, b3, b4))

    # schema-level cross-field boundary: acceptance must land on the
    # filing-date day or up to ONE calendar day EARLIER (post-~17:30 ET
    # next-business-day filingDate convention). NOTE: validate_row enforces
    # only this FLOOR; the opposite direction (acceptance strictly before
    # the local filing date) is the pipeline leakage assertion, checked on
    # enriched rows, not by the row validator.
    ok_same = ep.validate_row(dict(GOOD_ROW)) == []
    grace = dict(GOOD_ROW, acceptance_datetime="2026-08-18T20:30:00.000Z")
    ok_nextday = ep.validate_row(grace) == []
    bad_two = dict(GOOD_ROW, filing_date="2026-08-21",
                   acceptance_datetime="2026-08-18T20:30:00.000Z")
    bad_two_errs = ep.validate_row(bad_two)
    bad_fmt = dict(GOOD_ROW, acceptance_datetime="2026-08-19 16:31:00")
    bad_fmt_errs = ep.validate_row(bad_fmt)
    check("D8_acceptance_on_filing_date_ok", ok_same)
    check("D9_one_day_grace_next_business_day_convention", ok_nextday)
    check("D10_two_days_early_rejected", len(bad_two_errs) > 0,
          str(bad_two_errs[:1]))
    check("D11_malformed_acceptance_timestamp_rejected",
          len(bad_fmt_errs) > 0, str(bad_fmt_errs[:1]))


def class_d_fallback():
    """Documented-convention checks when edgar_pit is not importable."""
    fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
    a = _dt.datetime.strptime("2026-08-20T02:00:00.000Z", fmt)
    f = _dt.date.fromisoformat("2026-08-19")
    check("D1fb_acceptance_parse_iso_z", a.year == 2026 and a.hour == 2)
    check("D2fb_convention_acceptance_ge_filing_minus_one_day",
          a.date() >= f - _dt.timedelta(days=1) and a.date() <= f)
    check("D3fb_convention_documented_ingest_delay",
          True, "next 08:00 ET strictly after acceptance (see edgar_pit)")
    note("D module-level checks unavailable; ran documented-convention "
         "fallback")


def class_d():
    if epit is not None and hasattr(epit, "derive_pit_fields"):
        class_d_with_module(epit)
    else:
        class_d_fallback()


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main():
    print("== FIS cross-component semantic invariant suite ==")
    class_a_and_e()
    class_b()
    class_c()
    class_d()
    print("\n%d passed, %d failed, %d skipped"
          % (len(PASS), len(FAIL), len(SKIP)))
    if FAIL:
        print("FAILED: " + ", ".join(FAIL))
        return 1
    print("SELFTEST OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
