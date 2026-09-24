#!/usr/bin/env python
# -*- coding: ascii -*-
"""Regression suite for realized-gain / holding-period tax semantics.

These tests exist because of three defects found by INDEPENDENT
recalculation while running the W8 S02 employer-equity scenario. Each is
stated below with the transaction that exposed it, so nobody "fixes" the
test by reintroducing the bug.

  fis-tax-d1  Holding-period misattribution.
              A sale spanning several lots booked the WHOLE gain under one
              holding period, chosen by SHARE COUNT rather than by which
              lots produced the gain. In S02, a ZPHR sale consumed a 500-sh
              short lot whose gain was exactly 0.00 and a 346.34-sh long lot
              whose gain was +3,948.31. Because the short lot had more
              shares, 3,948.31 USD of LONG-TERM gain was booked as
              SHORT-TERM: 24% tax on what should be 15%.

  fis-tax-d2  Destroyed carryforward loss.
              Cross-term netting wrote `st = max(0, st+lt); lt = 0.0`,
              discarding the residual. With gross LT -23,964.89 and gross
              ST +3,948.31 the correct answer is a net LT loss of
              -20,016.58 that carries forward. The old code reported 0.0/0.0
              and silently destroyed 20,016.58 USD of capital loss -- an
              asset that offsets future gains and (for an individual filer)
              up to 3,000 USD/yr of ordinary income.

  fis-tax-d3  Apples-to-oranges independent check.
              independent_recalculation compared a TERM-AGNOSTIC gross
              realized gain against (lt_net + st_net), a CROSS-NETTED
              quantity. The two differ whenever offsetting occurs, so the
              check fired even when both sides were correct.

Run:  python tools/fis/test_realized_gain_tax.py
Exit: 0 if all hold, 1 otherwise.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import portfolio_engine as pe  # noqa: E402

RESULTS = []


def check(cid, ok, detail=""):
    RESULTS.append((cid, bool(ok), detail))
    print("%-5s %-46s %s" % ("PASS" if ok else "FAIL", cid, detail))
    return ok


def close(a, b, tol=1e-6):
    return abs(float(a) - float(b)) <= tol


# ---------------------------------------------------------------------------
# The S02 transaction set, reconstructed exactly as the scenario produced it.
# px / qty / basis / term taken from the captured portfolio at the failure
# point. Ground truth was computed independently with Decimal arithmetic.
# ---------------------------------------------------------------------------
S02_LOTS = {
    "HSAIDX-SYNTH@hsa-m1-t": (
        58.0, [("L000", 110.0, 114.545455, "long"),
               ("L001", 100.0, 115.2, "long")]),
    "TGT2055-SYNTH@401k-zephyr-t": (
        62.0, [("L000", 700.0, 90.0, "long"),
               ("L001", 700.0, 96.0, "long"),
               ("L002", 700.0, 126.0, "long")]),
    "TOTMKT-SYNTH@brk-taxable-t": (
        128.4, [("L000", 1100.0, 86.0, "long"),
                ("L001", 1000.0, 112.5, "long"),
                ("L002", 1000.0, 118.0, "long")]),
    "ZPHR@brk-taxable-t": (
        142.5, [("L000", 400.0, 48.2, "long"),
                ("L001", 400.0, 71.85, "long"),
                ("L002", 400.0, 96.4, "long"),
                ("L003", 400.0, 118.75, "long"),
                ("L004", 400.0, 131.1, "long"),
                ("L005", 500.0, 142.5, "short")]),
}

# Ground truth computed independently (Decimal, outside this engine).
TRUTH = {
    "gross_lt": -20016.580587291028,
    "gross_st": 0.0,
    "net_lt": -20016.580587291028,
    "net_st": 0.0,
    "carryforward": 20016.580587291028,
    "tax": 0.0,
}


def build_events():
    """Rebuild the sale set and return realized_events as the planner does."""
    sells = [
        ("HSAIDX-SYNTH@hsa-m1-t", 55.327612165010535),
        ("TGT2055-SYNTH@401k-zephyr-t", 553.2761216501053),
        ("TOTMKT-SYNTH@brk-taxable-t", 1264.7497560046729),
        ("ZPHR@brk-taxable-t", 846.342938),
    ]
    events = []
    for ticker, qty in sells:
        px, lots_raw = S02_LOTS[ticker]
        lots = [{"lot_id": lid, "quantity": q, "cost_basis": b,
                 "term": t, "_px": px} for lid, q, b, t in lots_raw]
        fills, gain, term_gains = pe.select_lots_highest_loss_first(lots, qty)
        for term in ("long", "short"):
            g = term_gains[term]
            if abs(g) > 1e-12:
                events.append((ticker, g, term))
    return events


def main():
    rates = {"long": 0.15, "short": 0.24}

    # ---- fis-tax-d1: gain follows the lot, not the share count ----------
    ev = build_events()
    zphr = [(g, t) for sym, g, t in ev if sym == "ZPHR@brk-taxable-t"]
    check("d1.zphr_gain_is_long_term",
          zphr and all(t == "long" for _, t in zphr),
          "ZPHR gain characterised as %s (was 'short' before the fix)"
          % [t for _, t in zphr])
    check("d1.zphr_gain_amount",
          zphr and close(sum(g for g, _ in zphr), 3948.3095, 1e-3),
          "ZPHR long-term gain %r" % (sum(g for g, _ in zphr) if zphr else 0))

    # ---- fis-tax-d2: the residual loss survives --------------------------
    out = pe._split_term_tax(ev, rates)
    check("d2.net_lt_preserved",
          close(out["lt_net_gain"], TRUTH["net_lt"]),
          "net LT %r (expected %r; old code gave 0.0)"
          % (out["lt_net_gain"], TRUTH["net_lt"]))
    check("d2.no_tax_on_net_loss",
          close(out["tax_usd"], TRUTH["tax"]),
          "tax %r" % out["tax_usd"])
    check("d2.carryforward_reported",
          close(out.get("carryforward_loss_usd", 0.0), TRUTH["carryforward"]),
          "carryforward %r (old code reported none)" %
          out.get("carryforward_loss_usd"))
    check("d2.gross_fields_present",
          "gross_lt_gain" in out and "gross_st_gain" in out,
          "gross (pre-netting) figures exposed for independent comparison")

    # ---- conservation: netting may redistribute, never create/destroy ----
    check("d2.netting_is_conservative",
          close(out["lt_net_gain"] + out["st_net_gain"],
                out["gross_lt_gain"] + out["gross_st_gain"]),
          "net %r == gross %r"
          % (out["lt_net_gain"] + out["st_net_gain"],
             out["gross_lt_gain"] + out["gross_st_gain"]))

    # ---- the opposite direction: short loss offsets long gain ------------
    ev2 = [("X", 1000.0, "long"), ("X", -300.0, "short")]
    o2 = pe._split_term_tax(ev2, rates)
    check("d2.st_loss_offsets_lt_gain",
          close(o2["lt_net_gain"], 700.0) and close(o2["st_net_gain"], 0.0),
          "LT 1000 / ST -300 -> net LT %r, net ST %r"
          % (o2["lt_net_gain"], o2["st_net_gain"]))
    check("d2.offset_gain_taxed_at_long_rate",
          close(o2["tax_usd"], 105.0),
          "tax %r == 700 * 0.15" % o2["tax_usd"])

    # ---- a standalone loss carries through untouched ---------------------
    ev3 = [("Y", -500.0, "long")]
    o3 = pe._split_term_tax(ev3, rates)
    check("d2.standalone_loss_survives",
          close(o3["lt_net_gain"], -500.0) and close(o3["tax_usd"], 0.0),
          "net LT %r, carryforward %r"
          % (o3["lt_net_gain"], o3["carryforward_loss_usd"]))

    # ---- mixed gains are taxed at their own rates ------------------------
    ev4 = [("Z", 1000.0, "long"), ("Z", 500.0, "short")]
    o4 = pe._split_term_tax(ev4, rates)
    check("d1.mixed_gains_taxed_separately",
          close(o4["tax_usd"], 1000.0 * 0.15 + 500.0 * 0.24),
          "tax %r" % o4["tax_usd"])

    # ---- unknown holding periods must fail closed ------------------------
    try:
        pe.select_lots_highest_loss_first(
            [{"lot_id": "L0", "quantity": 1.0, "cost_basis": 1.0,
              "term": "medium", "_px": 2.0}], 1.0)
        check("d1.unknown_term_rejected", False, "no error raised")
    except ValueError:
        check("d1.unknown_term_rejected", True,
              "ValueError on term='medium' (fails closed)")

    n_fail = sum(1 for _, ok, _ in RESULTS if not ok)
    print("")
    print("=" * 62)
    print("PASSED: %d   FAILED: %d" % (len(RESULTS) - n_fail, n_fail))
    print("=" * 62)
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
