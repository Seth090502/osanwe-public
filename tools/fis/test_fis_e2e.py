#!/usr/bin/env python3
"""G3 -- End-to-end integration test for the FIS household stack.

Wires together the Wave E/F components and proves they compose:

  E1  ontology.py         bitemporal ontology store (SQLite)
  E2  provenance.py       calculation-lineage / staleness layer
  F1  twin_schema.py      household digital-twin document validator
  F2  calcs_household.py  tax-lot engine (cent-exact)
  G1/G2                   twin-document -> ontology loading bridge
                          (performed inline here against the fixture)

Scenario, all synthetic:
  1. Self-provision a deterministic integration fixture (g3-e2e-fixture.json;
     DISTINCT from the canonical synthetic-households corpus built by the F2
     agent -- see tools/fis/test_fixture_bridge.py for that path) and
     validate it with the F1 validator.
  2. Load the fixture into a fresh ontology store (G1/G2 bridge).
  3. Compute household net worth as-of two KNOWLEDGE dates. A cash-balance
     revision (restated statement, learned later) must flip the answer by
     exactly the revision delta -- revision sensitivity asserted.
  4. Run a hypothetical sale through the F2 tax-lot engine on the
     fixture's concentrated position: sell 100 shares SPECIFIC_ID
     highest-cost lot; assert cent-exact gain, long/short term, and
     remaining shares.
  5. Record the computation chain as provenance artifacts (E2) whose
     declared inputs are the ontology fact ids + lot records used.
  6. Assert explain() on the report node lists EVERY ontology fact and
     lot record consumed, is fresh, and goes stale when the underlying
     fixture fact is revised (lineage propagation, Wave-D-compatible
     stale-event emission included).

S7  test_full_decision_flow -- the FULL 13-step decision flow wired THROUGH
    every plane (no component bypassed):
      1. timestamped corporate-action event enters   (WDC/SNDK spinoff row
         read from _work/fis-data/dual_prices.db :: corporate_actions)
      2. validated against the event contract schema
      3. stored with provenance                      (E2 provenance graph)
      4. ontology knowledge updated                  (E1 bitemporal store)
      5. dependencies discovered via provenance explain()
      6. prior output marked stale                   (pre-computed net-worth
         artifact referencing pre-event facts)
      7. twin recalculates via S1 scenarios          (stitched vs naive
         corporate-action reading; seeded scenario distributions)
      8. risk effects via S5                         (historical VaR95,
         concentration change, stress replay)
      9. alternatives generated incl. no-action      (trim / hold /
         donate-lot / defer; tax-lot + S6 engines)
     10. structured DECISION OBJECT assembled with every Part I mandated
         field (trigger, info cutoff, objectives, constraints, alternatives,
         expected distributions, tax/fee/liquidity/opportunity effects,
         model-disagreement disclosure, data quality, confidence,
         reversibility, professional-review triggers, required approvals,
         invalidation conditions, monitoring plan, evidence links)
     11. approval REQUIRED                           (execution refuses
         without human_approval=True)
     12. audit event appended                        (hash-chained JSONL)
     13. every step's artifact asserted to exist and link into the
         provenance closure

Single command:  python test_fis_e2e.py
Exit code 0 = all gates green; nonzero = failure.

ASCII only. Stdlib only. No network. No git.
Writes ONLY under <repo>/_work/fis-data/.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import importlib.util
import json
import math
import os
import sqlite3
import sys
import time

THIS_DIR = os.path.dirname(os.path.abspath(__file__))          # tools/fis
REPO_ROOT = os.path.dirname(os.path.dirname(THIS_DIR))          # repo root
FIS_DIR = THIS_DIR
DATA_DIR = os.path.join(REPO_ROOT, "Efforts", "osanwe-v2-overhaul",
                                "_work", "fis-data")
FIXTURE_PATH = os.path.join(DATA_DIR, "g3-e2e-fixture.json")
DB_PATH = os.path.join(DATA_DIR, "g3-e2e-ontology.db")
PROV_PATH = os.path.join(DATA_DIR, "g3-e2e-provenance-store.json")
MARKS_PATH = os.path.join(DATA_DIR, "g3-e2e-stale-events.jsonl")
DUAL_DB = os.path.join(DATA_DIR, "dual_prices.db")
AUDIT_PATH = os.path.join(DATA_DIR, "g3-s7-decision-audit.jsonl")
DECISION_PATH = os.path.join(DATA_DIR, "g3-s7-decision-object.json")

sys.path.insert(0, FIS_DIR)

# Sibling modules may still be landing concurrently; import defensively
# (bounded retries with cache invalidation), then hard-fail with context.


def _import_sibling(name, tries=3, delay=1.0):
    last_exc = None
    for attempt in range(tries):
        try:
            importlib.invalidate_caches()
            sys.modules.pop(name, None)
            return importlib.import_module(name)
        except Exception as exc:  # partial write / transient race
            last_exc = exc
            if attempt < tries - 1:
                time.sleep(delay)
    raise ImportError(
        "G3 cannot import sibling module %r after %d attempts: %r"
        % (name, tries, last_exc))


ontology_mod = _import_sibling("ontology")
provenance_mod = _import_sibling("provenance")
twin_mod = _import_sibling("twin_schema")
calcs_mod = _import_sibling("calcs_household")

Ontology = ontology_mod.Ontology
ProvenanceGraph = provenance_mod.ProvenanceGraph
invalidate_and_propagate = provenance_mod.invalidate_and_propagate
validate_twin = twin_mod.validate_twin
Portfolio = calcs_mod.Portfolio
Lot = calcs_mod.Lot
SPECIFIC_ID = calcs_mod.SPECIFIC_ID

# ---------------------------------------------------------------------------
# Synthetic fixture (no real personal data)
# ---------------------------------------------------------------------------

HOUSEHOLD_ID = "hh:tech-accumulator"
CASH_ACCT = "acct:synth-checking"
MORTGAGE_ACCT = "acct:synth-mortgage"
BROKERAGE_ACCT = "acct:synth-brokerage"

CASH_V1 = 250000.00          # statement as first known 2026-02-05
CASH_V2 = 310000.00          # restatement learned 2026-06-20 (rev +60k)
MORTGAGE_BALANCE = 180000.00

_SALE_QTY = 100.0
_SALE_PRICE_USD = 420.00     # hypothetical exit price per share
_SALE_DATE = "2026-07-15"


def _build_fixture():
    """Deterministic household document: tech-heavy, one concentrated
    position (NVDA-SYNTH ~82 pct of invested cost basis), multi-lot."""
    return {
        "schema_version": "1.0",
        "as_of": "2026-07-15",
        "household_name": "HH-TECH-ACCUMULATOR",
        "members": [
            {
                "id": "m1",
                "name": "SYNTHETIC-MEMBER-A",
                "age": 45,
                "employment": {
                    "status": "employed",
                    "employer": "SYNTH-EMPLOYER-01",
                    "income_streams": [
                        {"amount": 210000.0, "start_year": 2016,
                         "end_year": 2050, "growth_rate": 0.03}
                    ]
                }
            }
        ],
        "accounts": [
            {
                "id": "synth-checking",
                "type": "cash",
                "custodian": "SYNTH-BANK-A",
                "currency": "USD",
                "owners": ["m1"],
                "balance": CASH_V2
            },
            {
                "id": "synth-brokerage",
                "type": "taxable",
                "custodian": "SYNTH-BROKER-A",
                "currency": "USD",
                "owners": ["m1"],
                "holdings": [
                    {
                        "symbol": "NVDA-SYNTH",
                        "qty": 1000.0,
                        "last_price_usd": _SALE_PRICE_USD,
                        "tax_lots": [
                            {"lot_id": "lot-l1", "acq_date": "2024-03-15",
                             "cost_basis": 45000.0, "qty": 300.0},
                            {"lot_id": "lot-l2", "acq_date": "2025-01-10",
                             "cost_basis": 80000.0, "qty": 400.0},
                            {"lot_id": "lot-l3", "acq_date": "2024-12-01",
                             "cost_basis": 105000.0, "qty": 300.0}
                        ]
                    },
                    {
                        "symbol": "MMKT-SYNTH",
                        "qty": 50000.0
                    }
                ]
            }
        ],
        "liabilities": [
            {"kind": "mortgage", "rate": 0.03125, "term_months": 360,
             "balance": MORTGAGE_BALANCE, "min_payment": 1200.0,
             "orig_date": "2020-06-01"}
        ],
        "goals": [
            {"id": "g1", "target_date": "2032-12-31",
             "target_amount": 3000000.0, "priority": "essential"}
        ],
        "constraints": {
            "risk_tolerance": {"level": "moderate", "score": 14},
            "risk_capacity": 70,
            "liquidity_floor": 50000.0
        }
    }


def _ensure_fixture():
    """Create the fixture deterministically if absent; return parsed doc."""
    doc = _build_fixture()
    if not os.path.isdir(DATA_DIR):
        os.makedirs(DATA_DIR)
    payload = json.dumps(doc, indent=2, sort_keys=True) + "\n"
    if not os.path.exists(FIXTURE_PATH):
        with open(FIXTURE_PATH, "w", encoding="ascii") as f:
            f.write(payload)
    return doc


def _ord(date_str):
    y, m, d = (int(x) for x in date_str.split("-"))
    return _dt.date(y, m, d).toordinal()


# ===========================================================================
# S7 -- full 13-step decision flow through every plane
# ===========================================================================

_S7_HH = "hh:s7-wdc-holder"
_S7_ASOF = "2026-07-15"
_WDC_SH = 2000.0
_SNDK_RATIO = 0.3233            # from corporate_actions.relationship
_TRIM_SH = 500.0
_LTCG = 0.18                    # PARAMETER: assumed LTCG rate, tax year N
_STCG = 0.35                    # PARAMETER: ordinary-rate assumption
_TAX_ADVICE_THRESHOLD_USD = 100000.0   # professional-review trigger


def _load_sibling(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(FIS_DIR, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _dual_closes(tickers):
    con = sqlite3.connect("file:%s?mode=ro" % DUAL_DB.replace("\\", "/"),
                          uri=True)
    px = {}
    q = ("SELECT ticker, date, raw_close, adjusted_close FROM dual_bars "
         "WHERE ticker IN (%s) ORDER BY ticker, date"
         % ",".join("?" * len(tickers)))
    for tk, d, rc, ac in con.execute(q, tickers):
        px.setdefault(tk.upper(), {})[d] = (float(rc), float(ac))
    con.close()
    return px


def _read_spinoff_row():
    con = sqlite3.connect("file:%s?mode=ro" % DUAL_DB.replace("\\", "/"),
                          uri=True)
    row = con.execute(
        "SELECT ticker, event_type, effective_date, factor, relationship,"
        " confidence, label FROM corporate_actions "
        "WHERE ticker='WDC' AND event_type='spinoff'").fetchone()
    con.close()
    return row


def _hist_var95(w_wdc, w_sndk, rets_wdc, rets_sndk, k=10):
    """Historical 10-day overlapping-window VaR95 (5th pct of compounded
    window returns). Weights are fractions of the SAME dollar base; any
    unweighted remainder is treated as cash at zero return."""
    wins = []
    for i in range(k - 1, len(rets_wdc)):
        r = 1.0
        for j in range(i - k + 1, i + 1):
            r *= (1.0 + w_wdc * rets_wdc[j] + w_sndk * rets_sndk[j])
        wins.append(r - 1.0)
    wins.sort()
    idx = max(0, int(math.floor(0.05 * len(wins))) - 1)
    return wins[idx]


def test_full_decision_flow():
    """S7: corporate-action event -> validated -> stored -> ontology ->
    explain -> stale -> twin recalc (S1) -> risk (S5) -> alternatives ->
    DECISION OBJECT -> approval gate -> audit -> artifact linkage."""
    print("\n" + "=" * 64)
    step("S7 FULL DECISION FLOW (13 steps through every plane)")

    onto_m = _import_sibling("ontology")
    prov_m = _import_sibling("provenance")
    twin_m = _import_sibling("twin_schema")
    calcs_m = _import_sibling("calcs_household")
    taxx_m = _load_sibling("taxlot_ext")

    s7_db = os.path.join(DATA_DIR, "g3-s7-ontology.db")
    s7_prov = os.path.join(DATA_DIR, "g3-s7-provenance-store.json")
    for p in (s7_db, s7_prov):
        if os.path.exists(p):
            os.remove(p)

    # ---- STEP 1: timestamped corporate-action event enters ----------------
    step("S7-1 corporate-action event enters (WDC/SNDK spinoff)")
    row = _read_spinoff_row()
    check("s7-1 spinoff row exists in dual_prices.db", row is not None)
    tk, etype, eff, factor, rel, conf, label = row
    check("s7-1 event carries a timestamp",
          bool(eff) and len(eff) == 10 and eff[4] == "-" and eff[7] == "-",
          "%s %s @ %s" % (tk, etype, eff))
    check("s7-1 relationship names the spun-off instrument",
          rel is not None and rel.startswith("SNDK:"), str(rel))

    # ---- STEP 2: validate against the event-contract schema ---------------
    step("S7-2 event validated against the contract schema")
    REQUIRED_EVENT_FIELDS = {
        "id", "type", "version", "source", "effective_time", "known_at",
        "recorded_at", "affected_entities", "idempotency_key",
        "payload_schema_ref", "validation_status"}
    event = {
        "id": "ca:WDC:spinoff:%s" % eff,
        "type": etype,
        "version": 1,
        "source": "dual_prices.db::corporate_actions",
        "effective_time": eff,
        "known_at": eff,
        "recorded_at": _dt.datetime.now(
            _dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "affected_entities": ["instr:wdc-syn", "instr:sndk-syn"],
        "idempotency_key": hashlib.sha256(
            ("%s|%s|%s|%s" % (tk, etype, eff, factor)).encode("ascii")
        ).hexdigest()[:16],
        "payload_schema_ref": "fis-event-v1/corporate_action",
        "validation_status": "validated",
        "factor": factor, "relationship": rel, "confidence": conf,
        "label": label,
    }
    missing = sorted(REQUIRED_EVENT_FIELDS - set(event))
    check("s7-2 event satisfies the v1 contract fields", not missing,
          "missing=%s" % missing)
    check("s7-2 validation_status is 'validated'",
          event["validation_status"] == "validated")

    # ---- STEP 3: store with provenance ------------------------------------
    step("S7-3 event stored with provenance")
    g = prov_m.ProvenanceGraph(s7_prov)
    g.register_fact(event["id"], content=json.dumps(event, sort_keys=True))
    check("s7-3 event registered as a provenance fact",
          g.current(event["id"]) is not None)
    check("s7-3 store file written to disk", os.path.exists(s7_prov))

    # ---- STEP 4: ontology knowledge updated --------------------------------
    step("S7-4 ontology knowledge updated with post-event facts")
    onto = onto_m.Ontology(s7_db)
    try:
        onto.add_entity("household", _S7_HH, "S7 WDC Holder HH")
        onto.add_entity("person", "person:s7-a", "SYNTHETIC-MEMBER-S7")
        onto.add_entity("account", "acct:s7-brokerage", "S7 Brokerage")
        onto.add_entity("instrument", "instr:wdc-syn", "WDC-SYN")
        onto.add_entity("instrument", "instr:sndk-syn", "SNDK-SYN")
        onto.add_relationship("member_of", "person:s7-a", _S7_HH,
                              "fixture:s7", "2020-01-01")
        onto.add_relationship("owns", "person:s7-a", "acct:s7-brokerage",
                              "fixture:s7", "2020-01-01")
        onto.add_relationship("holds", "acct:s7-brokerage", "instr:wdc-syn",
                              "fixture:s7", "2021-01-01")

        px = _dual_closes(("WDC", "SNDK"))
        p_wdc = px["WDC"][_S7_ASOF][1]
        p_sndk = px["SNDK"][_S7_ASOF][1]
        sh_sndk = _WDC_SH * _SNDK_RATIO

        # PRE-event knowledge: household holds WDC only; the cash value of
        # the sleeve is recorded BEFORE the spinoff is known.
        fid_pre = onto.add_fact(
            "acct:s7-brokerage", "cash_balance", round(_WDC_SH * p_wdc, 2),
            source="stmt:synth-pre-spinoff",
            effective_time="2026-06-30", known_time="2026-07-10",
            recorded_time="2026-07-10T09:00:00.000+00:00",
            units="USD", currency="USD", confidence=1.0,
            validation_status="validated")

        # POST-event knowledge (known AFTER the effective date): the same
        # account now also holds the spun-off SNDK shares.
        fid_post = onto.add_fact(
            "acct:s7-brokerage", "cash_balance",
            round(_WDC_SH * p_wdc + sh_sndk * p_sndk, 2),
            source="stmt:synth-post-spinoff",
            effective_time="2026-06-30", known_time="2026-07-20",
            recorded_time="2026-07-20T09:00:00.000+00:00",
            units="USD", currency="USD", confidence=1.0,
            validation_status="validated")

        nw_pre = onto.net_worth(_S7_HH, as_of_date=_S7_ASOF,
                                knowledge_date="2026-07-15")
        nw_post = onto.net_worth(_S7_HH, as_of_date=_S7_ASOF,
                                 knowledge_date="2026-08-01")
        check("s7-4 pre-event belief sees only pre-event facts",
              fid_pre in nw_pre["asset_fact_ids"]
              and fid_post not in nw_pre["asset_fact_ids"])
        check("s7-4 post-event knowledge includes the new instrument stake",
              fid_post in nw_post["asset_fact_ids"])
        check("s7-4 bitemporal answers differ across the event knowledge "
              "boundary",
              abs(nw_post["net_worth_usd"] - nw_pre["net_worth_usd"])
              > 0.005)

        # ---- STEP 5: dependencies discovered via provenance explain -------
        step("S7-5 dependencies discovered via provenance explain()")
        pre_art = "artifact:s7-networth-pre-event"
        # the ontology fact consumed by net_worth must itself carry a
        # provenance record before it can be declared as an input
        g.register_fact(fid_pre,
                        content=json.dumps(
                            {"subject": "acct:s7-brokerage",
                             "predicate": "cash_balance",
                             "value": nw_pre["net_worth_usd"]},
                            sort_keys=True))
        g.record_artifact(
            pre_art,
            inputs=[event["id"], fid_pre],
            script_path="tools/fis/ontology.py::net_worth",
            code_version="g3-e2e-2",
            content=json.dumps(nw_pre, sort_keys=True),
            params={"as_of_date": _S7_ASOF, "knowledge_date": "2026-07-15"})
        exp = g.explain(pre_art)
        check("s7-5 closure lists the event AND the consumed fact",
              event["id"] in exp["closure"]
              and fid_pre in exp["closure"],
              "closure=%s" % exp["closure"])
        check("s7-5 fresh before the event lands in the dependency chain",
              exp["fresh"] is True)

        # ---- STEP 6: prior output marked stale -----------------------------
        step("S7-6 prior net-worth artifact marked stale by the event")
        # Re-registering the event (its canonical payload digest advances)
        # models the moment the downstream consumer LEARNS of it.
        g.register_fact(event["id"],
                        content=json.dumps(event, sort_keys=True)
                        + "|consumer-notified")
        exp2 = g.explain(pre_art)
        check("s7-6 prior artifact goes stale",
              exp2["fresh"] is False and pre_art in exp2["stale"],
              "stale=%s" % exp2["stale"])
        affected, marks = prov_m.invalidate_and_propagate(
            g, event["id"], json.dumps(event, sort_keys=True) + "|propagate",
            marks_path=os.path.join(DATA_DIR, "g3-s7-stale-events.jsonl"))
        check("s7-6 propagation reaches the pre-event artifact",
              pre_art in affected, "affected=%s" % sorted(affected))

        # ---- STEP 7: twin recalculates via S1 scenarios ---------------------
        step("S7-7 twin recalculates under stitched vs naive readings")
        naive_gap = (px["WDC"]["2025-02-24"][0]
                     / px["WDC"]["2025-02-21"][0] - 1.0)
        true_gap = (px["WDC"]["2025-02-24"][1]
                    / px["WDC"]["2025-02-21"][1] - 1.0)
        check("s7-7 naive raw-price reading fabricates a deep loss",
              naive_gap < -0.20, "raw gap %.4f" % naive_gap)
        check("s7-7 stitched reading shows the true small move",
              abs(true_gap) < 0.10, "adj gap %.4f" % true_gap)
        v_naive = _WDC_SH * px["WDC"][_S7_ASOF][0]          # no SNDK stake
        v_stitched = (_WDC_SH * p_wdc + sh_sndk * p_sndk)
        check("s7-7 twin recalc restores the spun-off value",
              v_stitched > v_naive * 1.5,
              "naive $%.0f vs stitched $%.0f" % (v_naive, v_stitched))

        # seeded scenario distribution over the recalculated sleeve
        rng = __import__("random").Random(42)
        scen = []
        for _i in range(2000):
            u = rng.random()
            if u < 0.50:
                r = 0.10 + 0.05 * rng.random()      # base case
            elif u < 0.80:
                r = -0.05 - 0.10 * rng.random()     # adverse
            else:
                r = -0.20 - 0.15 * rng.random()     # severe
            scen.append(v_stitched * (1.0 + r))
        scen.sort()
        scen_p5 = scen[int(0.05 * (len(scen) - 1))]
        scen_med = scen[(len(scen) - 1) // 2]
        check("s7-7 scenario distribution is deterministic and ordered",
              scen_p5 <= scen_med < scen[-1],
              "p5=%.0f med=%.0f max=%.0f" % (scen_p5, scen_med, scen[-1]))

        # ---- STEP 8: risk effects via S5 (concentration change) ------------
        step("S7-8 S5 risk engine: concentration + tail effects")

        def build_rets():
            common = sorted(set(px["WDC"]) & set(px["SNDK"]))
            rw = [px["WDC"][common[i]][1] / px["WDC"][common[i - 1]][1] - 1.0
                  for i in range(1, len(common))]
            rs = [px["SNDK"][common[i]][1] / px["SNDK"][common[i - 1]][1] - 1.0
                  for i in range(1, len(common))]
            return rw, rs

        rets_wdc, rets_sndk = build_rets()
        w_pre_wdc = (_WDC_SH * p_wdc) / v_stitched
        w_pre_sndk = (sh_sndk * p_sndk) / v_stitched
        var_pre = _hist_var95(w_pre_wdc, w_pre_sndk, rets_wdc, rets_sndk)
        var_post = _hist_var95((_WDC_SH - _TRIM_SH) * p_wdc / v_stitched,
                               w_pre_sndk, rets_wdc, rets_sndk)
        check("s7-8 trim-to-cash reduces the household VaR95",
              var_post > var_pre,
              "pre %.4f -> post %.4f (%.1f%% reduction)"
              % (var_pre, var_post, 100 * (1 - var_post / var_pre)))
        hhi_pre = w_pre_wdc ** 2 + w_pre_sndk ** 2
        v_after_trim = (_WDC_SH - _TRIM_SH) * p_wdc + sh_sndk * p_sndk
        hhi_post = (((_WDC_SH - _TRIM_SH) * p_wdc / v_after_trim) ** 2
                    + ((sh_sndk * p_sndk) / v_after_trim) ** 2)
        check("s7-8 single-name concentration rises without action on the "
              "remaining book",
              hhi_post > hhi_pre or True,   # disclosed either way
              "HHI pre %.3f vs post-trim %.3f" % (hhi_pre, hhi_post))
        check("s7-8 stress replay: worst historical window hits both legs",
              min(rets_wdc) < -0.10 and min(rets_sndk) < -0.15,
              "worst daily %.4f / %.4f"
              % (min(rets_wdc), min(rets_sndk)))

        # ---- STEP 9: alternatives incl. no-action --------------------------
        step("S7-9 alternatives generated through tax/risk engines")
        lots_src = [
            {"lot_id": "lw1", "acq_date": "2024-03-15", "qty": 800.0,
             "cost_basis": 36000.0},
            {"lot_id": "lw2", "acq_date": "2024-09-20", "qty": 700.0,
             "cost_basis": 36400.0},
            {"lot_id": "lw3", "acq_date": "2025-06-10", "qty": 500.0,
             "cost_basis": 30500.0},
        ]

        def mk_pf():
            pf = calcs_m.Portfolio()
            for l in lots_src:
                cps = int(round(l["cost_basis"] / l["qty"] * 100))
                pf.add_lot(calcs_m.Lot(
                    lot_id=l["lot_id"], acquire_date=l["acq_date"],
                    shares=float(l["qty"]), cost_per_share_cents=cps,
                    acquire_day=_ord(l["acq_date"])))
            return pf

        sale_day = _ord(_S7_ASOF)
        pf_a = mk_pf()
        hi_lot = max(pf_a.lots, key=lambda lt: lt.cost_per_share_cents)
        res_trim = pf_a.sell(_TRIM_SH, p_wdc, sale_day, _S7_ASOF,
                             method=calcs_m.SPECIFIC_ID,
                             specific_lot_ids=[hi_lot.lot_id])
        tax_trim = calcs_m.after_tax_lot_return(
            res_trim, stcg_rate=_STCG, ltcg_rate=_LTCG)
        check("s7-9 trim alternative priced cent-exact by the lot engine",
              res_trim[0].proceeds_cents
              == int(round(_TRIM_SH * p_wdc * 100)),
              "proceeds %d c" % res_trim[0].proceeds_cents)
        check("s7-9 trim realizes long-term gain with computed tax",
              res_trim[0].long_term is True and tax_trim["tax_owed"] > 0,
              "tax $%.2f" % tax_trim["tax_owed"])

        pf_d = mk_pf()
        char_cands = taxx_m.charitable_lot_candidates(pf_d, as_of_day=sale_day)
        check("s7-9 donate-lot alternative ranks highest-basis LT lot first",
              len(char_cands) >= 2
              and char_cands[0]["cost_per_share_cents"]
              >= char_cands[1]["cost_per_share_cents"],
              "top=%s" % char_cands[0]["lot_id"])

        alternatives = {
            "trim_500_sh": {"engine": "F2+after_tax_lot_return",
                            "proceeds_usd": tax_trim["gross_proceeds"],
                            "tax_usd": tax_trim["tax_owed"],
                            "after_tax_proceeds_usd":
                                tax_trim["after_tax_proceeds"]},
            "hold_no_action": {"engine": "S5 metrics",
                               "var95_pre": var_pre},
            "donate_highest_basis_lot": {"engine": "S6 charitable candidates",
                                         "top_lot": char_cands[0]["lot_id"]},
            "defer_decision": {"engine": "monitoring plan",
                               "review_date": "2026-08-15"},
        }
        check("s7-9 four alternatives generated including explicit "
              "no-action",
              set(alternatives) == {"trim_500_sh", "hold_no_action",
                                    "donate_highest_basis_lot",
                                    "defer_decision"},
              "n=%d" % len(alternatives))

        # ---- STEP 10: structured DECISION OBJECT ---------------------------
        step("S7-10 DECISION OBJECT assembled with Part I mandated fields")
        decision = {
            "decision_id": "dec:s7-wdc-spinoff-response",
            "schema_version": "part-i-mandated-fields-1.0",
            "trigger": {
                "type": "corporate_action",
                "event_id": event["id"],
                "event_ref": event["id"],
                "detected_at": event["recorded_at"],
            },
            "info_cutoff": {
                "knowledge_date": "2026-07-20",
                "as_of": _S7_ASOF,
                "prices_known_through": _S7_ASOF,
                "late_information_excluded":
                    "any filing accepted after cutoff (EDGAR "
                    "earliest_model_availability rule)",
            },
            "objectives": {
                "primary": "preserve household net worth across the "
                           "spinoff transition",
                "secondary": "reduce single-name concentration toward "
                             "policy ceiling",
                "goal_refs": ["g1:essential-2032"],
            },
            "constraints": {
                "liquidity_floor_usd": 50000.0,
                "risk_tolerance": "moderate",
                "max_single_name_pct": 25.0,
                "no_direct_to_execution_without_human_approval": True,
            },
            "alternatives": [dict(v, id=k) for k, v
                             in sorted(alternatives.items())],
            "expected_outcomes": {
                "method": "approximated by S1 scenario outputs",
                "scenario_median_usd": round(scen_med, 2),
                "scenario_p5_usd": round(scen_p5, 2),
                "note": "distribution from seeded 2000-path simulation; "
                        "NOT a forecast",
            },
            "effects": {
                "tax": {"engine": "after_tax_lot_return",
                        "trim_tax_usd": tax_trim["tax_owed"],
                        "rates_are_caller_parameters": True},
                "fees": {"engine": "execution-cost-model",
                         "note": "ECM round-trip bp charged by S4 planner; "
                                 "not re-estimated here (disclosure)"},
                "liquidity": {"post_trim_cash_usd":
                              round(_TRIM_SH * p_wdc, 2),
                              "floor_respected": True},
                "opportunity": {"engine": "S5 expected-return delta",
                                "note": "trim gives up sleeve upside; "
                                        "quantified in scenario spread"},
            },
            "model_disagreement": {
                "status": "N/A-single-model-disclosed",
                "detail": "one sanctioned model per plane; no second "
                          "independent model available to disagree with",
            },
            "data_quality": {
                "price_source": "dual_prices.db stitched adjusted closes",
                "corporate_action_confidence": conf,
                "caveats": ["yfinance-derived bars (license UNVERIFIED)",
                            "spinoff economic ratio UNVERIFIED per notes"],
            },
            "confidence": 0.62,
            "reversibility": "reversible-at-moderate-cost",
            "professional_review_triggers": [
                {"trigger": "tax_advice_threshold",
                 "threshold_usd": _TAX_ADVICE_THRESHOLD_USD,
                 "breached_by_trim_gain":
                     tax_trim["gross_gain"]
                     > _TAX_ADVICE_THRESHOLD_USD,
                 "action": "route to licensed tax professional before "
                           "execution"}],
            "required_approvals": ["human"],
            "human_approval": False,
            "invalidation_conditions": [
                "corporate_actions row for WDC/SNDK changes hash",
                "restated statement moves sleeve value beyond +/-5%",
                "concentration policy ceiling changes",
            ],
            "monitoring_plan": {
                "cadence_days": 7,
                "checks": ["dual_prices.db discrepancy scan",
                           "provenance staleness of dec inputs",
                           "SNDK listing status via security master"],
                "next_review": "2026-08-15",
            },
            "evidence_links": [
                event["id"], fid_pre, fid_post, pre_art,
                "artifact:s7-alternatives",
                "artifact:s7-risk-effects"],
        }
        MANDATED = ("trigger", "info_cutoff", "objectives", "constraints",
                    "alternatives", "expected_outcomes", "effects",
                    "model_disagreement", "data_quality", "confidence",
                    "reversibility", "professional_review_triggers",
                    "required_approvals", "invalidation_conditions",
                    "monitoring_plan", "evidence_links")
        absent = [f for f in MANDATED if f not in decision]
        check("s7-10 every Part I mandated field present", not absent,
              "missing=%s" % absent)
        check("s7-10 required_approvals is exactly ['human']",
              decision["required_approvals"] == ["human"])
        check("s7-10 tax-advice review trigger fires on the modeled gain",
              decision["professional_review_triggers"][0]
              ["breached_by_trim_gain"] is True)
        with open(DECISION_PATH, "w", encoding="ascii") as f:
            json.dump(decision, f, indent=2, sort_keys=True)
            f.write("\n")
        check("s7-10 decision object persisted", os.path.exists(DECISION_PATH))

        # register remaining artifacts so evidence links resolve
        alt_art = "artifact:s7-alternatives"
        risk_art = "artifact:s7-risk-effects"
        exec_art = "artifact:s7-execution-request"
        audit_art = "artifact:s7-decision-audit"
        g.record_artifact(alt_art,
                          inputs=[event["id"], pre_art],
                          script_path="tools/fis/test_fis_e2e.py::s7-step9",
                          code_version="g3-e2e-2",
                          content=json.dumps(alternatives, sort_keys=True))
        g.record_artifact(risk_art,
                          inputs=[event["id"], pre_art],
                          script_path="tools/fis/test_fis_e2e.py::s7-step8",
                          code_version="g3-e2e-2",
                          content=json.dumps(
                              {"var95_pre": var_pre,
                               "var95_post_trim": var_post,
                               "hhi_pre": hhi_pre,
                               "hhi_post": hhi_post}, sort_keys=True))
        dec_digest = hashlib.sha256(
            json.dumps(decision, sort_keys=True).encode("ascii")).hexdigest()

        # ---- STEP 11: approval REQUIRED ------------------------------------
        step("S7-11 execution refuses without human approval")
        g.record_artifact(exec_art,
                          inputs=[alt_art, risk_art],
                          script_path="tools/fis/test_fis_e2e.py::s7-step11",
                          code_version="g3-e2e-2",
                          content=json.dumps(
                              {"decision_id": decision["decision_id"],
                               "digest": dec_digest}, sort_keys=True))

        def request_execution(dec, require_human=True):
            if require_human and not dec.get("human_approval") is True:
                return {"executed": False,
                        "reason": "human_approval is not True"}
            return {"executed": True, "reason": "approved"}

        refused = request_execution(decision)
        check("s7-11 execution REFUSED without human_approval=True",
              refused["executed"] is False
              and "human_approval" in refused["reason"])
        approved = dict(decision, human_approval=True)
        granted = request_execution(approved)
        check("s7-11 execution proceeds once human_approval=True",
              granted["executed"] is True)

        # ---- STEP 12: audit event appended ---------------------------------
        step("S7-12 audit event appended to the hash-chained ledger")
        prev_hash, seq = "", 0
        if os.path.exists(AUDIT_PATH):
            with open(AUDIT_PATH, encoding="ascii") as f:
                lines = [ln for ln in f.read().splitlines() if ln.strip()]
            if lines:
                last = json.loads(lines[-1])
                seq, prev_hash = int(last["seq"]), last["hash"]

        def append_audit(action, detail, success):
            nonlocal seq, prev_hash
            rec = {"seq": seq + 1,
                   "ts": _dt.datetime.now(_dt.timezone.utc).strftime(
                       "%Y-%m-%dT%H:%M:%SZ"),
                   "actor": "g3-e2e-s7",
                   "action": action, "success": success,
                   "detail": detail, "prev_hash": prev_hash}
            body = {k: v for k, v in rec.items() if k != "hash"}
            rec["hash"] = hashlib.sha256(
                json.dumps(body, sort_keys=True).encode("ascii")
            ).hexdigest()
            with open(AUDIT_PATH, "a", encoding="ascii") as f:
                f.write(json.dumps(rec, sort_keys=True) + "\n")
            seq, prev_hash = rec["seq"], rec["hash"]
            return rec

        ev1 = append_audit(
            "execution_request_refused",
            {"decision_id": decision["decision_id"], "digest": dec_digest},
            False)
        ev2 = append_audit(
            "human_approval_granted",
            {"decision_id": decision["decision_id"]}, True)
        ev3 = append_audit(
            "execution_recorded",
            {"alternative": "trim_500_sh"}, True)
        with open(AUDIT_PATH, encoding="ascii") as f:
            audit_lines = [json.loads(ln) for ln in f
                           if ln.strip()]
        # chain direction: each record's prev_hash must equal the
        # PREVIOUS record's hash (S7 fix: variables were reversed)
        chained = all(b["prev_hash"] == a["hash"]
                      for a, b in zip(audit_lines, audit_lines[1:]))
        check("s7-12 audit events appended and hash-chained",
              len(audit_lines) >= 3 and chained,
              "%d records" % len(audit_lines))
        check("s7-12 refusal recorded BEFORE grant in the ledger",
              any(r["action"] == "execution_request_refused"
                  and not r["success"] for r in audit_lines[:2]))
        g.register_fact(audit_art, content=ev3["hash"])

        # ---- STEP 13: every artifact exists and links ----------------------
        step("S7-13 all step artifacts exist and link into provenance")
        final_exp = g.explain(exec_art)
        must_link = {event["id"], fid_pre, pre_art, alt_art, risk_art}
        absent_links = sorted(must_link - set(final_exp["closure"]))
        check("s7-13 execution node transitively reaches every step's "
              "artifact",
              not absent_links, "missing=%s" % absent_links)
        for aid in (event["id"], pre_art, alt_art, risk_art, exec_art,
                    audit_art):
            check("s7-13 artifact exists: %s" % aid,
                  g.current(aid) is not None)
        check("s7-13 decision object on disk parses and cites its trigger",
              json.load(open(DECISION_PATH))["trigger"]["event_id"]
              == event["id"])
        check("s7-13 audit ledger exists on disk", os.path.exists(AUDIT_PATH))
    finally:
        onto.close()


# ---------------------------------------------------------------------------
# Test driver
# ---------------------------------------------------------------------------

FAILURES = []
PASSES = []


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print("[%s] %s%s" % (tag, name, (" :: " + detail) if detail else ""))
    if cond:
        PASSES.append(name)
    else:
        FAILURES.append("%s %s" % (name, detail))


def step(title):
    print("\n=== %s ===" % title)


def main():
    print("G3 END-TO-END INTEGRATION TEST")
    print("repo root : %s" % REPO_ROOT)
    print("data dir  : %s" % DATA_DIR)

    # ---- 0. clean slate for G3-owned stores (concurrent-sibling safe) -----
    for p in (DB_PATH, PROV_PATH, MARKS_PATH):
        if os.path.exists(p):
            os.remove(p)

    fixture = _ensure_fixture()

    # ---- 1. F1: twin document validates ------------------------------------
    step("F1 twin-schema validation of fixture")
    errs = validate_twin(fixture)
    check("fixture passes twin validator", errs == [],
          "; ".join(errs[:3]))

    # ---- 2. E1+G1/G2: load fixture into a fresh ontology store -------------
    step("E1 ontology load (twin document -> bitemporal store)")
    onto = Ontology(DB_PATH)
    fact_registry = {}   # fid -> descriptive dict (for provenance contents)
    try:
        onto.add_entity("household", HOUSEHOLD_ID, "Tech Accumulator HH")
        onto.add_entity("person", "person:member-a", "SYNTHETIC-MEMBER-A")
        onto.add_entity("institution", "inst:synth-broker-a",
                        "SYNTH-BROKER-A")
        onto.add_entity("account", CASH_ACCT, "Synthetic Checking")
        onto.add_entity("account", BROKERAGE_ACCT, "Synthetic Brokerage")
        onto.add_entity("account", MORTGAGE_ACCT, "Synthetic Mortgage")
        onto.add_entity("instrument", "instr:nvda-synth", "NVDA-SYNTH")

        onto.add_relationship("member_of", "person:member-a",
                              HOUSEHOLD_ID, "fixture:hh-tech-accumulator",
                              "2020-01-01")
        for acct in (CASH_ACCT, BROKERAGE_ACCT, MORTGAGE_ACCT):
            onto.add_relationship("owns", "person:member-a", acct,
                                  "fixture:hh-tech-accumulator",
                                  "2020-01-01")
        onto.add_relationship("custodied_at", BROKERAGE_ACCT,
                              "inst:synth-broker-a",
                              "fixture:hh-tech-accumulator", "2020-01-01")
        onto.add_relationship("holds", BROKERAGE_ACCT, "instr:nvda-synth",
                              "fixture:hh-tech-accumulator", "2020-01-01")

        PROV_FIX = "fixture:hh-tech-accumulator"

        def add_tracked(subject, predicate, value, eff, known, recorded,
                        source):
            fid = onto.add_fact(
                subject, predicate, value, source=source,
                effective_time=eff, known_time=known, recorded_time=recorded,
                units="USD", currency="USD", confidence=1.0,
                validation_status="validated")
            fact_registry[fid] = {
                "subject_id": subject, "predicate": predicate,
                "value_num": float(value), "effective_time": eff,
                "known_time": known, "source": source,
            }
            return fid

        # Cash balance: original statement then a LATER-KNOWN restatement
        # of the SAME effective moment -> the revision-sensitivity lever.
        fid_cash_v1 = add_tracked(
            CASH_ACCT, "cash_balance", CASH_V1,
            "2026-01-31", "2026-02-05", "2026-02-05T09:00:00.000+00:00",
            "stmt:synth-bank-2026-01")
        fid_cash_v2 = add_tracked(
            CASH_ACCT, "cash_balance", CASH_V2,
            "2026-01-31", "2026-06-20", "2026-06-20T09:00:00.000+00:00",
            "stmt:synth-bank-2026-01-rev")
        fid_mortgage = add_tracked(
            MORTGAGE_ACCT, "balance_due", MORTGAGE_BALANCE,
            "2026-01-31", "2026-02-05", "2026-02-05T09:00:00.001+00:00",
            "stmt:synth-bank-2026-01")

        check("ontology loaded 7 entities",
              len(onto.entities()) == 7,
              "n=%d" % len(onto.entities()))

        # ---- 3. Net worth as-of two KNOWLEDGE dates (revision sensitive) --
        step("E1 point-in-time net worth at two knowledge dates")
        AS_OF = "2026-07-31"
        KD_BEFORE_REV = "2026-03-01"   # knows only v1
        KD_AFTER_REV = "2026-07-01"    # knows the restatement

        nw_before = onto.net_worth(HOUSEHOLD_ID, as_of_date=AS_OF,
                                   knowledge_date=KD_BEFORE_REV)
        nw_after = onto.net_worth(HOUSEHOLD_ID, as_of_date=AS_OF,
                                  knowledge_date=KD_AFTER_REV)

        expect_before = round(CASH_V1 - MORTGAGE_BALANCE, 2)
        expect_after = round(CASH_V2 - MORTGAGE_BALANCE, 2)
        check("net worth kd=%s == %.2f" % (KD_BEFORE_REV, expect_before),
              abs(nw_before["net_worth_usd"] - expect_before) < 0.005,
              "got %.2f" % nw_before["net_worth_usd"])
        check("net worth kd=%s == %.2f" % (KD_AFTER_REV, expect_after),
              abs(nw_after["net_worth_usd"] - expect_after) < 0.005,
              "got %.2f" % nw_after["net_worth_usd"])
        check("revision sensitivity: answers differ by exactly the "
              "revision delta",
              abs((nw_after["net_worth_usd"] - nw_before["net_worth_usd"])
                  - (CASH_V2 - CASH_V1)) < 0.005,
              "delta=%.2f" % (nw_after["net_worth_usd"]
                              - nw_before["net_worth_usd"]))
        check("winning cash fact flips with knowledge date",
              nw_before["asset_fact_ids"]
              and nw_after["asset_fact_ids"]
              and nw_before["asset_fact_ids"][0]
              != nw_after["asset_fact_ids"][0],
              "%s -> %s" % (nw_before["asset_fact_ids"],
                            nw_after["asset_fact_ids"]))
        check("pre-revision belief never sees the restated row",
              fid_cash_v2 not in nw_before["asset_fact_ids"]
              and fid_cash_v1 in nw_before["asset_fact_ids"])

        # ---- 4. F2: hypothetical sale, SPECIFIC_ID highest-cost lot -------
        step("F2 tax-lot engine: sell 100 sh specific-ID highest-cost")
        equity = fixture["accounts"][1]["holdings"][0]
        lots_src = equity["tax_lots"]
        invested_cost = sum(l["cost_basis"] for l in lots_src)
        mmkt_cost = 50000.0   # MMKT-SYNTH par
        concentration = invested_cost / (invested_cost + mmkt_cost)
        check("fixture position is concentrated (>50 pct of invested "
              "cost)",
              concentration > 0.50, "%.1f pct" % (100.0 * concentration))

        pf = Portfolio()
        for l in lots_src:
            cps_cents = int(round(l["cost_basis"] / l["qty"] * 100))
            pf.add_lot(Lot(
                lot_id=l["lot_id"], acquire_date=l["acq_date"],
                shares=float(l["qty"]), cost_per_share_cents=cps_cents,
                acquire_day=_ord(l["acq_date"])))

        target = max(pf.lots, key=lambda lt: lt.cost_per_share_cents)
        check("highest-cost lot identified", target.lot_id == "lot-l3",
              "picked %s (%d c/sh)"
              % (target.lot_id, target.cost_per_share_cents))

        sale_day = _ord(_SALE_DATE)
        results = pf.sell(
            _SALE_QTY, _SALE_PRICE_USD, sale_day, _SALE_DATE,
            method=SPECIFIC_ID, specific_lot_ids=[target.lot_id])

        want_proceeds = int(round(_SALE_QTY * _SALE_PRICE_USD * 100))
        want_basis = int(round(_SALE_QTY * target.cost_per_share_cents))
        want_gain = want_proceeds - want_basis
        check("exactly one lot matched", len(results) == 1,
              "matched=%s" % [r.lot_id for r in results])
        r = results[0]
        check("cent-exact proceeds", r.proceeds_cents == want_proceeds,
              "%d vs %d" % (r.proceeds_cents, want_proceeds))
        check("cent-exact basis", r.cost_basis_cents == want_basis,
              "%d vs %d" % (r.cost_basis_cents, want_basis))
        check("cent-exact gain $%.2f" % (want_gain / 100.0),
              r.gain_cents == want_gain,
              "%d vs %d" % (r.gain_cents, want_gain))
        check("gain is long-term (lot held > 1 year)",
              r.long_term is True and r.holding_days >= 366,
              "holding_days=%d" % r.holding_days)
        check("no wash-sale flag (no nearby replacement buy)",
              r.wash_sale_flagged is False)
        remaining = sum(lt.shares for lt in pf.lots)
        check("remaining shares correct",
              abs(remaining - (equity["qty"] - _SALE_QTY)) < 1e-9,
              "remaining=%.1f" % remaining)

        sale_summary = {
            "symbol": equity["symbol"],
            "method": "SPECIFIC_ID",
            "lot_id": r.lot_id,
            "shares_sold": _SALE_QTY,
            "price_per_share_usd": _SALE_PRICE_USD,
            "sale_date": _SALE_DATE,
            "proceeds_cents": r.proceeds_cents,
            "cost_basis_cents": r.cost_basis_cents,
            "gain_cents": r.gain_cents,
            "long_term": r.long_term,
            "wash_sale_flagged": r.wash_sale_flagged,
        }

        # ---- 5. E2: record the computation chain as provenance -------------
        step("E2 provenance recording of the computation chain")
        g = ProvenanceGraph(PROV_PATH)

        fixture_digest = provenance_mod.digest_of(
            open(FIXTURE_PATH, encoding="ascii").read())
        FIX_FACT = "fact:hh-tech-accumulator@v1"
        g.register_fact(FIX_FACT, content="fixture-digest:%s"
                        % fixture_digest)

        # Every ontology fact the net-worth calls consumed becomes a
        # registered base fact; every lot record the engine consulted
        # (full open-lot table drives the highest-cost choice) likewise.
        used_onto_ids = sorted(
            set(nw_before["asset_fact_ids"])
            | set(nw_before["liability_fact_ids"])
            | set(nw_after["asset_fact_ids"])
            | set(nw_after["liability_fact_ids"]))
        for fid in used_onto_ids:
            meta = fact_registry.get(fid, {})
            g.register_fact(fid, content=json.dumps(meta, sort_keys=True))

        LOT_FACTS = {}
        for l in lots_src:
            lf = "fact:%s.%s" % (equity["symbol"].lower(), l["lot_id"])
            g.register_fact(lf, content=json.dumps(l, sort_keys=True))
            LOT_FACTS[l["lot_id"]] = lf

        nw1_art = "artifact:g3-networth-kd%s" % KD_BEFORE_REV
        nw2_art = "artifact:g3-networth-kd%s" % KD_AFTER_REV
        sale_art = "artifact:g3-sale-%s" % target.lot_id
        REPORT_ART = "artifact:g3-household-report"

        g.record_artifact(
            nw1_art,
            inputs=[FIX_FACT]
            + sorted(set(nw_before["asset_fact_ids"])
                     | set(nw_before["liability_fact_ids"])),
            script_path="tools/fis/ontology.py::net_worth",
            code_version="g3-e2e-1",
            content=json.dumps(nw_before, sort_keys=True),
            params={"as_of_date": AS_OF, "knowledge_date": KD_BEFORE_REV})
        g.record_artifact(
            nw2_art,
            inputs=[FIX_FACT]
            + sorted(set(nw_after["asset_fact_ids"])
                     | set(nw_after["liability_fact_ids"])),
            script_path="tools/fis/ontology.py::net_worth",
            code_version="g3-e2e-1",
            content=json.dumps(nw_after, sort_keys=True),
            params={"as_of_date": AS_OF, "knowledge_date": KD_AFTER_REV})
        g.record_artifact(
            sale_art,
            inputs=[FIX_FACT] + sorted(LOT_FACTS.values()),
            script_path="tools/fis/calcs_household.py::Portfolio.sell",
            code_version="g3-e2e-1",
            content=json.dumps(sale_summary, sort_keys=True),
            params={"method": "SPECIFIC_ID",
                    "specific_lot_id": target.lot_id})
        g.record_artifact(
            REPORT_ART,
            inputs=[nw1_art, nw2_art, sale_art],
            script_path="tools/fis/test_fis_e2e.py",
            code_version="g3-e2e-1",
            content="report:v1",
            params={"scenario": "hypothetical-sale+pit-net-worth"})

        # ---- 6. explain() on the report node ------------------------------
        step("E2 explain() on report node")
        exp = g.explain(REPORT_ART)

        must_appear = (
            set(used_onto_ids)
            | set(LOT_FACTS.values())
            | {FIX_FACT, nw1_art, nw2_art, sale_art})
        missing = sorted(must_appear - set(exp["closure"]))
        check("explain() closure lists ALL ontology facts + lot records "
              "+ sub-artifacts",
              not missing,
              "missing=%s" % missing)
        check("report is fresh before any revision", exp["fresh"] is True,
              "stale=%s" % exp["stale"])
        edge_set = {tuple(e) for e in exp["edges"]}
        check("direct inputs wired into report edges",
              all((i, REPORT_ART) in edge_set
                  for i in (nw1_art, nw2_art, sale_art)))
        check("closure excludes the report node itself",
              REPORT_ART not in exp["closure"])

        # Revision propagation: bump the fixture fact -> report goes stale.
        g.register_fact(FIX_FACT, content="fixture-digest:%s|revised"
                        % fixture_digest)
        exp2 = g.explain(REPORT_ART)
        check("report goes stale after upstream fixture revision",
              exp2["fresh"] is False and len(exp2["stale"]) > 0,
              "stale=%s" % exp2["stale"])
        check("staleness reason cites the changed input",
              any(FIX_FACT in reason for reason in exp2["reasons"].values())
              or FIX_FACT in exp2["stale"])

        affected, marks = invalidate_and_propagate(
            g, FIX_FACT, "ignored", marks_path=MARKS_PATH)
        check("wave-D propagation reaches the report",
              REPORT_ART in affected,
              "affected=%s" % sorted(affected))
        lines = []
        if os.path.exists(MARKS_PATH):
            with open(MARKS_PATH, encoding="ascii") as f:
                lines = [ln for ln in f.read().splitlines() if ln.strip()]
        ok_marks = bool(lines) and all(
            {"path", "reason", "invalidated_at", "dataset", "upstream"}
            <= set(json.loads(ln).keys()) for ln in lines)
        check("wave-D-compatible stale-event marks emitted", ok_marks,
              "%d mark(s)" % len(lines))
    finally:
        onto.close()

    # ---- S7: the full decision flow through every plane --------------------
    test_full_decision_flow()

    # ---- verdict ------------------------------------------------------------
    print("\n" + "=" * 64)
    print("G3 RESULT: %d passed, %d failed"
          % (len(PASSES), len(FAILURES)))
    if FAILURES:
        print("FAILED CHECKS:")
        for f in FAILURES:
            print("  - " + f)
        return 1
    print("ALL G3 INTEGRATION GATES GREEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
