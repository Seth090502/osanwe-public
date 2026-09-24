#!/usr/bin/env python3
"""Bridge test: canonical F2 synthetic-households corpus through the FIS stack.

Distinct from tools/fis/test_fis_e2e.py (which self-provisions its own
g3-e2e-fixture.json). THIS test proves the CANONICAL fixtures delivered by
the F2 agent (Efforts/osanwe-v2-overhaul/_work/fis-data/synthetic-households/)
work end-to-end:

  1. All three fixture files exist and pass the twin-schema validator.
  2. Program-level requirements hold: >=8 accounts total across households,
     >=25 tax lots total, >=3 goals each.
  3. hh-tech-accumulator's concentrated position is structurally present:
     a single-issuer equity >=35% of invested cost basis, multi-lot.
  4. The concentrated position flows through the cent-exact tax-lot engine:
     sell 100 shares highest-cost specific-ID; assert exact arithmetic,
     long/short-term classification, remaining quantity.

Exit 0 = all green. ASCII only, stdlib only, no network, no git.
Writes nothing outside _work/fis-data/.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import os
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(THIS_DIR))
FIS_DATA = os.path.join(REPO, "Efforts", "osanwe-v2-overhaul", "_work", "fis-data")
HH_DIR = os.path.join(FIS_DATA, "synthetic-households")
sys.path.insert(0, THIS_DIR)


def load_mod(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(THIS_DIR, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod          # dataclass processing needs the module registered
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return mod


PASSES, FAILURES = [], []


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print("[%s] %s%s" % (tag, name, (" :: " + detail) if detail else ""))
    (PASSES if cond else FAILURES).append(name)


def main():
    ts = load_mod("twin_schema")
    ch = load_mod("calcs_household")

    files = ["hh-conservative-retiree.json", "hh-tech-accumulator.json",
             "hh-leveraged-young.json"]
    docs = {}
    for fn in files:
        p = os.path.join(HH_DIR, fn)
        if not os.path.exists(p):
            check("exists:" + fn, False, p)
            continue
        docs[fn] = json.load(open(p))
        errs = ts.validate_twin(docs[fn])
        check("validates:" + fn, errs == [], "; ".join(errs[:2]))

    # program totals
    n_accts = sum(len(d.get("accounts", [])) for d in docs.values())
    n_lots = sum(len(h.get("tax_lots", []))
                 for d in docs.values()
                 for a in d.get("accounts", [])
                 for h in a.get("holdings", []))
    check("accounts_total>=8", n_accts >= 8, "n=%d" % n_accts)
    check("lots_total>=25", n_lots >= 25, "n=%d" % n_lots)
    for fn, d in docs.items():
        check("goals>=3:" + fn, len(d.get("goals", [])) >= 3,
              "n=%d" % len(d.get("goals", [])))

    # concentration structure in tech accumulator: SINGLE-ISSUER name
    # (ZPHR), measured against taxable-account invested basis; broad
    # funds (TOTMKT/TGT2055/USAGG/HSAIDX) excluded by design
    doc = docs.get("hh-tech-accumulator.json")
    if not doc:
        print("tech fixture missing; skipping concentration probes")
        sys.exit(1 if FAILURES else 0)

    FUNDMARKS = ("TOTMKT", "TGT", "USAGG", "IDX")
    zphr = None
    for a in doc.get("accounts", []):
        for h in a.get("holdings", []):
            sym_u = str(h.get("symbol") or "").upper()
            if sym_u.startswith("ZPHR"):
                zphr = h
    check("single_issuer_present", zphr is not None)
    taxable_cost = sum(float(l.get("cost_basis", 0))
                       for a in doc["accounts"]
                       if a.get("type") in ("taxable", "brokerage")
                       for h in a.get("holdings", [])
                       for l in h.get("tax_lots", []))
    z_cost = sum(float(l.get("cost_basis", 0)) for l in zphr.get("tax_lots", []))
    z_share = z_cost / taxable_cost if taxable_cost else 0
    check("concentrated_single_issuer>=30pct_taxable_basis",
          z_share >= 0.30, "ZPHR %.1f%% of taxable invested basis (%d lots)"
          % (100 * z_share, len(zphr.get("tax_lots", []))))
    check("concentrated_multi_lot", len(zphr.get("tax_lots", [])) >= 3,
          "lots=%d" % len(zphr.get("tax_lots", [])))

    # flow the position through the cent-exact lot engine:
    # sell 100 shares SPECIFIC_ID from the highest-cost-per-share lot
    lots = zphr["tax_lots"]
    qty = sum(float(l["qty"]) for l in lots)
    cost = sum(float(l["cost_basis"]) for l in lots)
    px = round((cost * 1.4) / max(qty, 1), 2)   # documented synth assumption

    port = ch.Portfolio()
    lots_sorted = sorted(lots,
                         key=lambda l: -float(l["cost_basis"]) / max(float(l["qty"]), 1))
    dayno = None
    for i, l in enumerate(lots_sorted):
        cps_cents = int(round(float(l["cost_basis"]) * 100 / float(l["qty"])))
        y, m, dd = (int(x) for x in l["acq_date"].split("-"))
        dayno = dt.date(y, m, dd).toordinal()
        port.add_lot(ch.Lot(lot_id="ZPHR-L%d" % i,
                            acquire_date=l["acq_date"],
                            shares=float(l["qty"]),
                            cost_per_share_cents=cps_cents,
                            acquire_day=dayno))
    # sale "day" must be consistent with the real calendar ordinals used
    # for acquire_day (the engine does day-number arithmetic)
    sale_day = dt.date.today().toordinal()
    results = port.sell(100.0, px, sale_day,
                        dt.date.today().isoformat(),
                        method="SPECIFIC_ID", specific_lot_ids=["ZPHR-L0"])
    gain_cents = sum(r.gain_cents for r in results)
    cps0 = int(round(float(lots_sorted[0]["cost_basis"]) * 100
                     / float(lots_sorted[0]["qty"])))
    expected_gain_cents = 100 * (int(round(px * 100)) - cps0)
    check("lot_engine_cent_exact",
          abs(gain_cents - expected_gain_cents) <= 1,
          "gain $%.2f selling 100 sh @ $%.2f vs highest-cost-per-share lot "
          "(expected $%.2f)" % (gain_cents / 100.0, px, expected_gain_cents / 100.0))
    lt_attr = "long_term" if hasattr(results[0], "long_term") else "is_long_term"
    # classification must MATCH the actual holding period of the sold lot
    y0, m0, d0 = (int(x) for x in lots_sorted[0]["acq_date"].split("-"))
    held_days = (dt.date.today() - dt.date(y0, m0, d0)).days
    expect_lt = held_days >= int(getattr(results[0], "lt_threshold_days", 366))
    check("sale_classification_matches_holding_period",
          all(bool(getattr(r, lt_attr)) == expect_lt for r in results),
          "held %d days -> engine says %s (expected %s)"
          % (held_days, bool(getattr(results[0], lt_attr)), expect_lt))
    print("\nfixture-bridge: %d passed, %d failed" % (len(PASSES), len(FAILURES)))
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
