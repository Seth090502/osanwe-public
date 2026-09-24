#!/usr/bin/env python3
"""build_dashboard.py -- OVERNIGHT-W5 Experience plane v1 builder.

Reads real FIS system artifacts and emits index.html with all data
embedded as JSON blobs, so the page works fully OFFLINE (no fetch,
no CDN, system fonts only).

Data sources (all read-only):
  Efforts/osanwe-v2-overhaul/_work/fis-data/
    synthetic-households/*.json        (twin documents)
    shadow-status.json                 (cohort prediction/grade counts)
    shadow-freeze.json                 (cohort states, promotion rules)
    shadow-grades.jsonl                (calibration per cohort)
    dataset-registry.jsonl             (freshness per dataset)
    macro-vintage-status.json          (macro vintages)
    edgar-pit-full-checkpoint.json     (edgar-pit status)
    contamination-ledger.jsonl         (research hygiene summary)
    tournament-results.jsonl           (tournament summary)
    g3-s7-decision-object.json         (decision queue)
    g3-s7-provenance-store.json        (lineage chain)
    dual_prices.db                     (SPY closes for risk metrics, READ-ONLY)
  _work/fis-data/
    calcs_ledger_selftest.json, portfolio-engine-selftest.json,
    architecture-fitness-report.json   (selftest matrix)

Usage: python build_dashboard.py
Output: ./index.html next to this script.

ASCII only. Stdlib only. No network. No git.
"""

import json
import math
import os
import re
import sqlite3
import sys
from datetime import date, datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
FIS_DATA = os.path.join(ROOT, "Efforts", "osanwe-v2-overhaul", "_work", "fis-data")
FIS_DATA2 = os.path.join(ROOT, "_work", "fis-data")
TOOLS_DIR = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS_DIR)

BUILD_TS = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# Frozen synthetic price table (same as twin_scenarios.py).
PRICES = {
    "ZPHR": 142.50,
    "TOTMKT-SYNTH": 128.40,
    "TGT2055-SYNTH": 62.00,
    "USAGG-SYNTH": 42.00,
    "HSAIDX-SYNTH": 58.00,
}
CONCENTRATION_CAP_PCT = 30.0


def jload(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def jlines(path):
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def staleness_days(end_date_str):
    if not end_date_str:
        return None
    m = re.search(r"(\d{4}-\d{2}-\d{2})", str(end_date_str))
    if not m:
        return None
    try:
        d = datetime.strptime(m.group(1), "%Y-%m-%d").date()
        return (date.today() - d).days
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 1. Twin household (synthetic)
# ---------------------------------------------------------------------------

def load_twin():
    sys.path.insert(0, TOOLS_DIR)
    import fis.twin_scenarios as ts  # noqa: E402

    path = os.path.join(FIS_DATA, "synthetic-households",
                        "hh-tech-accumulator.json")
    doc = jload(path)
    nw = ts.net_worth(doc)
    liq = ts.liquidity_months(doc)
    cf = ts.annual_cash_flow(doc)

    # Job-loss sensitivity ladder
    sensitivity = []
    for m in (0, 3, 6, 9, 12):
        sd = ts.apply_job_loss(doc, m)
        nw2 = ts.net_worth(sd)
        liq2 = ts.liquidity_months(sd)
        sc = sd.get("scenario", {})
        sensitivity.append({
            "months": m,
            "net_worth_usd": nw2["value"],
            "delta_usd": round(nw2["value"] - nw["value"], 2),
            "liquidity_months": liq2["months_of_cover"],
            "shortfall_usd": sc.get("shortfall_if_any", 0.0),
        })

    members = len(doc.get("members") or [])
    accounts = len(doc.get("accounts") or [])

    # Portfolio holdings across all accounts (frozen price table)
    rows = {}
    for acct in doc.get("accounts") or []:
        for h in acct.get("holdings") or []:
            sym = h.get("symbol", "?")
            qty = float(h.get("qty", 0.0))
            px = PRICES.get(sym, 0.0)
            r = rows.setdefault(sym, {"symbol": sym, "qty": 0.0,
                                      "price": px, "value": 0.0,
                                      "accounts": []})
            r["qty"] += qty
            r["value"] += qty * px
            if acct.get("id", "?") not in r["accounts"]:
                r["accounts"].append(acct.get("id", "?"))
    total_mv = sum(r["value"] for r in rows.values())
    holdings = []
    for r in rows.values():
        w_pct = round(100.0 * r["value"] / total_mv, 2) if total_mv else 0.0
        holdings.append({
            "symbol": r["symbol"],
            "qty": round(r["qty"], 2),
            "price_usd": r["price"],
            "value_usd": round(r["value"], 2),
            "weight_pct": w_pct,
            "accounts": sorted(r["accounts"]),
            "concentration_flag": bool(w_pct > CONCENTRATION_CAP_PCT),
        })
    holdings.sort(key=lambda x: -x["value_usd"])

    zphr = next((h for h in holdings if h["symbol"] == "ZPHR"), None)
    zphr_weight_pct = zphr["weight_pct"] if zphr else 0.0

    # Scenario params embedded for client-side recompute
    cash_total = liq["cash_total"]
    monthly_spend = liq["monthly_spend"]
    liabilities = nw["total_liabilities"]
    non_cash_assets = round(nw["total_assets"] - cash_total, 2)

    twin = {
        "household_name": doc.get("household_name"),
        "as_of": doc.get("as_of"),
        "members": members,
        "member_names": [m.get("name") for m in doc.get("members") or []],
        "accounts": accounts,
        "account_types": [a.get("type") for a in doc.get("accounts") or []],
        "net_worth": nw,
        "liquidity": liq,
        "cash_flow": cf,
        "job_loss_sensitivity": sensitivity,
        "scenario_params": {
            "cash_total_usd": cash_total,
            "monthly_spend_usd": monthly_spend,
            "non_cash_assets_usd": non_cash_assets,
            "liabilities_usd": liabilities,
            "baseline_net_worth_usd": nw["value"],
            "baseline_liquidity_months": liq["months_of_cover"],
        },
        "assumptions": nw.get("assumptions", []),
        "data_gaps": nw.get("data_gaps", []),
    }
    portfolio = {
        "as_of": doc.get("as_of"),
        "price_table": PRICES,
        "total_market_value_usd": round(total_mv, 2),
        "holdings": holdings,
        "concentration_cap_pct": CONCENTRATION_CAP_PCT,
        "zphr_weight_pct": zphr_weight_pct,
        "zphr_concentration_breach": bool(zphr_weight_pct > CONCENTRATION_CAP_PCT),
    }
    return twin, portfolio


# ---------------------------------------------------------------------------
# 2. Risk block (risk_engine math on real dual_prices.db SPY closes)
# ---------------------------------------------------------------------------

def load_risk():
    sys.path.insert(0, TOOLS_DIR)
    import fis.risk_engine as re_eng  # noqa: E402

    db = os.path.join(FIS_DATA, "dual_prices.db")
    con = sqlite3.connect("file:%s?mode=ro" % db.replace("\\", "/"), uri=True)
    try:
        rows = con.execute(
            "select date, adjusted_close from dual_bars where ticker='SPY' "
            "order by date desc limit 121").fetchall()[::-1]
    finally:
        con.close()
    closes = [float(r[1]) for r in rows]
    pr = re_eng.position_risk(closes, as_of=rows[-1][0], report_date=date.today().isoformat(),
                              price_basis="adjusted close")

    kill_metrics = {
        "ann_vol": pr["ann_vol"],
        "maxdd": pr["maxdd"],
        "top_name_conc_pct": None,  # filled by caller
    }
    limits = {"ann_vol": {"max": 0.60}, "maxdd": {"max": 0.50}}
    risk = {
        "model_id": pr["disclosure"]["model_id"],
        "horizon": pr["disclosure"]["horizon"],
        "data_window": pr["disclosure"]["data_window"],
        "benchmark_series": "dual_prices.db SPY adjusted_close",
        "series_start": rows[0][0],
        "series_end": rows[-1][0],
        "n_obs": pr["n_obs"],
        "ann_vol": pr["ann_vol"],
        "max_drawdown": pr["maxdd"],
        "es95": pr["es95"],
        "confidence": pr["disclosure"]["confidence"],
        "kill_switch_limits": limits,
    }

    def finalize(top_name_pct):
        km = dict(kill_metrics)
        km["top_name_conc_pct"] = top_name_pct
        lims = dict(limits)
        lims["top_name_conc_pct"] = {"max": CONCENTRATION_CAP_PCT}
        breached = [k for k, v in lims.items() if re_eng.kill_switch(
            {k2: v2 for k2, v2 in km.items()}, {k: v})]
        return {
            "status": "TRIGGERED" if breached else "CLEAR",
            "breached_metrics": breached,
            "metrics": km,
            "limits": lims,
        }, breached

    disclosure = {
        "horizon": pr["disclosure"]["horizon"],
        "data_window": pr["disclosure"]["data_window"],
        "model_id": pr["disclosure"]["model_id"],
        "assumptions": pr["disclosure"]["assumptions"],
        "confidence": pr["disclosure"]["confidence"],
        "included_risks": list(re_eng.INCLUDED_RISKS),
        "excluded_risks": list(re_eng.EXCLUDED_RISKS),
        "staleness": pr["disclosure"]["staleness"],
        "sensitivity": pr["disclosure"]["sensitivity"],
        "applicable_limits": pr["disclosure"]["applicable_limits"],
    }
    return risk, disclosure, finalize


# ---------------------------------------------------------------------------
# 3. Decision queue (S7)
# ---------------------------------------------------------------------------

def load_decision():
    d = jload(os.path.join(FIS_DATA, "g3-s7-decision-object.json"))
    approval_required = ("human" in (d.get("required_approvals") or [])) \
        or not bool(d.get("human_approval"))
    return {
        "decision_id": d.get("decision_id"),
        "schema_version": d.get("schema_version"),
        "trigger": d.get("trigger"),
        "objectives": d.get("objectives"),
        "alternatives": d.get("alternatives"),
        "expected_outcomes": d.get("expected_outcomes"),
        "effects": d.get("effects"),
        "constraints": d.get("constraints"),
        "required_approvals": d.get("required_approvals"),
        "approval_required": approval_required,
        "human_approval_given": bool(d.get("human_approval")),
        "reversibility": d.get("reversibility"),
        "info_cutoff": d.get("info_cutoff"),
        "monitoring_plan": d.get("monitoring_plan"),
        "invalidation_conditions": d.get("invalidation_conditions"),
        "professional_review_triggers": d.get("professional_review_triggers"),
        "data_quality": d.get("data_quality"),
        "evidence_links": d.get("evidence_links"),
        "confidence": d.get("confidence"),
        "model_disagreement": d.get("model_disagreement"),
    }


# ---------------------------------------------------------------------------
# 4. Shadow research
# ---------------------------------------------------------------------------

def load_shadow():
    freeze = jload(os.path.join(FIS_DATA, "shadow-freeze.json"))
    status = jload(os.path.join(FIS_DATA, "shadow-status.json"))
    grades = jlines(os.path.join(FIS_DATA, "shadow-grades.jsonl"))
    grade_by_cohort = {g["cohort_id"]: g["grades"] for g in grades}

    preds = []
    ppath = os.path.join(FIS_DATA, "shadow-predictions.jsonl")
    if os.path.exists(ppath):
        preds = jlines(ppath)

    cohorts = []
    for cid, c in (freeze.get("cohorts") or {}).items():
        st = (status.get("cohorts") or {}).get(cid, {})
        gr = grade_by_cohort.get(cid, {})
        cohorts.append({
            "cohort_id": cid,
            "label": c.get("label"),
            "instrument": c.get("instrument"),
            "model_state": c.get("status"),
            "promotion_eligible": c.get("promotion_eligible"),
            "promotion_blocked_reason": c.get("promotion_blocked_reason"),
            "predictions": st.get("predictions", 0),
            "graded": st.get("graded", 0),
            "calibration_inside_p10_p90": gr.get("inside_p10_p90"),
            "calibration_bucket": gr.get("calibration_bucket"),
            "excess_net_of_costs": gr.get("excess_net_of_costs"),
            "direction_accuracy": gr.get("direction_accuracy"),
        })
    cohorts.sort(key=lambda x: x["cohort_id"])

    horizon_days = (freeze.get("horizons") or {}).get(
        "forecast_horizon_trading_days")

    return {
        "freeze_id": freeze.get("freeze_id"),
        "model_version": freeze.get("model_version"),
        "freeze_hash": freeze.get("freeze_hash"),
        "launched_utc": status.get("launched_utc"),
        "last_tick_date": status.get("last_tick_date"),
        "last_grade_date": status.get("last_grade_date"),
        "horizon_trading_days": horizon_days,
        "benchmark": (freeze.get("horizons") or {}).get("benchmark"),
        "prediction_count": len(preds),
        "promotion_path": (freeze.get("promotion_and_rejection_criteria") or {})
            .get("promotion_path"),
        "rejection_rule": (freeze.get("promotion_and_rejection_criteria") or {})
            .get("rejection_rule"),
        "cohorts": cohorts,
    }


# ---------------------------------------------------------------------------
# 5. Data quality (registry freshness)
# ---------------------------------------------------------------------------

def load_data_quality():
    reg = {}
    for entry in jlines(os.path.join(FIS_DATA, "dataset-registry.jsonl")):
        reg[entry.get("dataset_id")] = entry

    def fmt_entry(ds_id, label, source_note):
        e = reg.get(ds_id) or {}
        cov = e.get("coverage_dates") or {}
        end = cov.get("end") if isinstance(cov, dict) else cov
        start = cov.get("start") if isinstance(cov, dict) else None
        return {
            "dataset_id": ds_id,
            "label": label,
            "coverage_start": start,
            "coverage_end": end,
            "staleness_days": staleness_days(end) if end else None,
            "retrieval_timestamp": e.get("retrieval_timestamp"),
            "license_status": e.get("license_status"),
            "missingness_pct": e.get("missingness_pct"),
            "known_defects": e.get("known_defects") or [],
            "source_note": source_note,
            "sha256_prefix": (e.get("sha256") or "")[:16] or None,
            "version": e.get("version"),
        }

    macro_status = jload(os.path.join(FIS_DATA, "macro-vintage-status.json"))
    edgar_ckpt = jload(os.path.join(FIS_DATA, "edgar-pit-full-checkpoint.json"))

    edgar_note = "; ".join(str(v) for k, v in list(edgar_ckpt.items())
                           if k in ("rows_ingested", "tickers_done", "status")
                           ) or str(list(edgar_ckpt.keys()))

    datasets = [
        fmt_entry("factors.db", "factors.db",
                  "sqlite bars + macro factors (bulk pull manifest)"),
        fmt_entry("dual-prices", "dual_prices",
                  "dual_prices.db raw/adjusted dual bars + corporate actions"),
        fmt_entry("edgar-corpus", "edgar-pit",
                  "EDGAR point-in-time corpus; checkpoint: " + edgar_note[:160]),
        fmt_entry("macro-factors", "macro-vintages",
                  macro_status.get("coverage", "")),
    ]
    return {
        "generated_from": "dataset-registry.jsonl",
        "datasets": datasets,
        "macro_counts": macro_status.get("counts"),
        "macro_generated_utc": macro_status.get("generated_utc"),
    }


# ---------------------------------------------------------------------------
# 6. Contamination + tournament summaries
# ---------------------------------------------------------------------------

def load_research_hygiene():
    contam_path = os.path.join(FIS_DATA, "contamination-ledger.jsonl")
    n_contam = 0
    datasets = set()
    if os.path.exists(contam_path):
        for rec in jlines(contam_path):
            n_contam += 1
            if rec.get("dataset"):
                datasets.add(rec["dataset"])
    tourn = jlines(os.path.join(FIS_DATA, "tournament-results.jsonl"))
    summary = {}
    states = []
    for t in tourn:
        rt = t.get("record_type")
        if rt == "tournament_summary":
            summary = t
        elif rt == "state_transition":
            states.append(t)
    return {
        "contamination_records": n_contam,
        "contamination_datasets": sorted(datasets)[:12],
        "tournament_summary": summary,
        "state_transitions": [
            {"id": s.get("id"), "from": s.get("from"), "to": s.get("to")}
            for s in states[-10:]
        ],
    }


# ---------------------------------------------------------------------------
# 7. Provenance chain (g3-s7 store)
# ---------------------------------------------------------------------------

def load_provenance():
    store = jload(os.path.join(FIS_DATA, "g3-s7-provenance-store.json"))
    arts = store.get("artifacts") or {}

    def node(nid):
        cur = (arts.get(nid) or {}).get("current") or {}
        return {
            "id": nid,
            "kind": cur.get("kind"),
            "digest": cur.get("digest"),
            "computed_at": cur.get("computed_at"),
            "script_path": cur.get("script_path"),
            "code_version": cur.get("code_version"),
            "version": cur.get("version"),
            "inputs": cur.get("inputs") or [],
        }

    chain_ids = [
        "ca:WDC:spinoff:2025-02-24",       # source fact (corporate action)
        "fx:ee0c3bc3646f4ff091f0",          # source fact (position/exposure)
        "artifact:s7-networth-pre-event",   # calc
        "artifact:s7-alternatives",         # calc
        "artifact:s7-risk-effects",         # calc
        "artifact:s7-execution-request",    # calc
        "artifact:s7-decision-audit",       # decision record (fact)
    ]
    chain = [node(n) for n in chain_ids if n in arts]
    return {
        "store": "g3-s7-provenance-store.json",
        "artifact_count": len(arts),
        "chain": chain,
        "chain_legend": "source -> fact -> calc -> decision "
                        "(kind field marks each node)",
    }


# ---------------------------------------------------------------------------
# 8. System health (selftest matrix)
# ---------------------------------------------------------------------------

def load_system_health(risk_ok, twin_ok):
    checks = []

    cl = jload(os.path.join(FIS_DATA2, "calcs_ledger_selftest.json"))
    checks.append({
        "component": "calcs_ledger (fis-calcs-ledger-1.0.0)",
        "source": "_work/fis-data/calcs_ledger_selftest.json",
        "passed": cl.get("passed", 0), "failed": cl.get("failed", 0),
        "ok": bool(cl.get("ok")),
        "detail": "%s property tests" % sum(
            (cl.get("property_tests") or {}).values()),
    })

    pe = jload(os.path.join(FIS_DATA2, "portfolio-engine-selftest.json"))
    cases = pe.get("cases") or []
    checks.append({
        "component": "portfolio_engine",
        "source": "_work/fis-data/portfolio-engine-selftest.json",
        "passed": sum(1 for c in cases if c.get("pass")),
        "failed": sum(1 for c in cases if not c.get("pass")),
        "ok": bool(pe.get("all_pass")),
        "detail": "%d cases" % len(cases),
    })

    af = jload(os.path.join(FIS_DATA2, "architecture-fitness-report.json"))
    results = af.get("results") or []
    checks.append({
        "component": "architecture-fitness",
        "source": "_work/fis-data/architecture-fitness-report.json",
        "passed": sum(1 for c in results if c.get("passed")),
        "failed": sum(1 for c in results if not c.get("passed")),
        "ok": not (af.get("failed") or []),
        "detail": "%d checks run" % af.get("checks_run", len(results)),
    })

    checks.append({
        "component": "twin_scenarios (live at build time)",
        "source": "tools/fis/twin_scenarios.py",
        "passed": 1 if twin_ok else 0, "failed": 0 if twin_ok else 1,
        "ok": twin_ok, "detail": "net_worth/liquidity/job_loss executed",
    })
    checks.append({
        "component": "risk_engine (live at build time)",
        "source": "tools/fis/risk_engine.py + dual_prices.db (read-only)",
        "passed": 1 if risk_ok else 0, "failed": 0 if risk_ok else 1,
        "ok": risk_ok, "detail": "position_risk over %s closes" % "SPY",
    })

    return {
        "built_at_utc": BUILD_TS,
        "checks": checks,
        "all_ok": all(c["ok"] for c in checks),
    }


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

TEMPLATE = """<!DOCTYPE html>
<html lang="en" class="historical-output">
<head>
<meta charset="ascii">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FIS Experience Plane v1 - Local Dashboard</title>
<style>
:root{
  --foreground:#e6e6e6;
  --muted-foreground:#9a9aa5;
  --accent:#4da3ff;
  --border:#33333d;
  --card:#1b1b22;
  --bg:#121218;
  --ok:#3fbf6f;
  --warn:#e0b03f;
  --bad:#e06c5f;
}
@media (prefers-color-scheme: light){
  :root{
    /* tokens stay dark-themed per spec; light scheme keeps same values */
  }
}
*{box-sizing:border-box}
html{font-size:100%}
body{
  margin:0;background:var(--bg);color:var(--foreground);
  font-family:"Segoe UI",system-ui,-apple-system,Arial,sans-serif;
  line-height:1.55;font-size:1rem;
}
a{color:var(--accent)}
code,kbd,pre{font-family:Consolas,"Courier New",monospace;font-size:0.95em}
.skip{
  position:absolute;left:-999px;top:0;background:var(--accent);
  color:#101014;padding:.5rem 1rem;z-index:10;
}
.skip:focus{left:.5rem;top:.5rem}
header.app, nav[aria-label="Sections"], main, footer{
  max-width:70rem;margin:0 auto;padding:0 1rem;
}
header.app{padding-top:1.25rem;padding-bottom:.5rem}
h1{font-size:1.5rem;margin:.2rem 0}
.subtitle{color:var(--muted-foreground);font-size:.95rem;margin:.2rem 0}
nav[aria-label="Sections"] ul{
  list-style:none;display:flex;flex-wrap:wrap;gap:.25rem;
  padding:0;margin:.75rem 0;border-bottom:1px solid var(--border);
}
nav[aria-label="Sections"] a{
  display:inline-block;padding:.35rem .65rem;text-decoration:none;
  color:var(--foreground);border:1px solid transparent;border-radius:4px;
}
nav[aria-label="Sections"] a:hover{border-color:var(--border)}
nav[aria-label="Sections"] a:focus-visible,a:focus-visible,
button:focus-visible,input:focus-visible,[tabindex]:focus-visible{
  outline:3px solid var(--accent);outline-offset:2px;
}
main{padding-top:1rem}
section{
  background:var(--card);border:1px solid var(--border);
  border-radius:8px;padding:1rem;margin:0 0 1.25rem 0;
  overflow-wrap:break-word;
}
section > h2{font-size:1.15rem;margin:.1rem 0 .75rem 0;
  border-bottom:1px solid var(--border);padding-bottom:.4rem}
section.research-band{border-left:6px solid var(--warn)}
.research-header{
  color:var(--warn);font-weight:bold;letter-spacing:.05em;
  font-family:Consolas,"Courier New",monospace;
}
.banner{
  border:1px dashed var(--warn);color:var(--warn);
  padding:.6rem .8rem;border-radius:6px;margin:.5rem 0;
  font-weight:bold;
}
.historical-output section{border-left:4px solid var(--warn)}
.historical-output .badge.ok{color:var(--warn);border-color:var(--warn)}
#freshness-banner{font-weight:normal}
.sim-banner{
  border:1px solid var(--accent);color:var(--accent);
  padding:.6rem .8rem;border-radius:6px;margin:.5rem 0;
  font-weight:bold;letter-spacing:.04em;
}
.cards{display:flex;flex-wrap:wrap;gap:.75rem;margin:.5rem 0}
.card{
  flex:1 1 14rem;border:1px solid var(--border);border-radius:6px;
  padding:.75rem;background:var(--bg);min-width:12rem;
}
.card .k{color:var(--muted-foreground);font-size:.85rem;display:block}
.card .v{font-size:1.35rem;font-weight:bold}
table{border-collapse:collapse;width:100%;margin:.5rem 0;font-size:.95rem}
th,td{text-align:left;padding:.4rem .55rem;border-bottom:1px solid var(--border);vertical-align:top}
th{color:var(--muted-foreground);font-weight:600}
tr:hover td{background:rgba(255,255,255,.03)}
.tablewrap{overflow-x:auto}
.badge{
  display:inline-block;padding:.05rem .45rem;border-radius:4px;
  border:1px solid var(--border);font-size:.82rem;
  font-family:Consolas,"Courier New",monospace;
}
.badge.ok{color:var(--ok);border-color:var(--ok)}
.badge.warn{color:var(--warn);border-color:var(--warn)}
.badge.bad{color:var(--bad);border-color:var(--bad)}
.badge.accent{color:var(--accent);border-color:var(--accent)}
.muted{color:var(--muted-foreground);font-size:.9rem}
.disclosure{
  border-left:4px solid var(--border);padding:.5rem .8rem;margin:.5rem 0;
  color:var(--muted-foreground);font-size:.92rem;
}
.slider-row{margin:.9rem 0}
.slider-row label{display:block;font-weight:600;margin-bottom:.25rem}
input[type="range"]{width:min(100%,28rem);height:2rem;accent-color:var(--accent)}
output{font-weight:bold;color:var(--accent)}
.kv{display:flex;gap:.5rem;flex-wrap:wrap;margin:.25rem 0}
.kv div{min-width:10rem}
.chain{list-style:none;padding:0;margin:.5rem 0}
.chain li{
  border-left:3px solid var(--accent);padding:.3rem 0 .3rem .8rem;
  margin-left:.5rem;
}
.chain li::before{
  content:"";
}
footer{color:var(--muted-foreground);font-size:.85rem;padding:1rem 1rem 2rem 1rem}
@media (max-width:48rem){
  .cards{flex-direction:column}
}
</style>
</head>
<body>
<a class="skip" href="#main">Skip to main content</a>
<header class="app" role="banner">
  <h1>FIS EXPERIENCE PLANE v1</h1>
  <p class="subtitle">Local financial intelligence system dashboard.
     Built __BUILD_TS__ from local artifacts. Offline: no network requests.</p>
  <div id="freshness-banner" class="banner" role="status" aria-live="polite">
    HISTORICAL / UNVERIFIED SNAPSHOT. Dates have not been checked.
    Refresh this report before relying on its figures.
  </div>
</header>

<nav aria-label="Sections">
  <ul>
    <li><a href="#home">Home</a></li>
    <li><a href="#household">Household</a></li>
    <li><a href="#portfolio">Portfolio</a></li>
    <li><a href="#risk">Risk</a></li>
    <li><a href="#decisions">Decisions</a></li>
    <li><a href="#scenarios">Scenarios</a></li>
    <li><a href="#shadow">Shadow Research</a></li>
    <li><a href="#dataquality">Data Quality</a></li>
    <li><a href="#provenance">Provenance</a></li>
    <li><a href="#health">System Health</a></li>
  </ul>
</nav>

<main id="main">

<section id="home" aria-labelledby="h-home">
  <h2 id="h-home">HOME</h2>
  <div class="banner" role="note">SYNTHETIC DATA NOTICE: every figure on this
  dashboard derives from SYNTHETIC-HOUSEHOLD fixtures and research datastores.
  Nothing here represents a real person's finances. NOT FINANCIAL ADVICE.</div>
  <div class="cards">
    <div class="card">
      <span class="k">Net worth (synthetic twin)</span>
      <span class="v" id="nw-value">$0</span>
      <span class="k">As of <span id="nw-asof"></span></span>
    </div>
    <div class="card">
      <span class="k">Liquidity</span>
      <span class="v" id="nw-liq"></span>
      <span class="k">months of core spend</span>
    </div>
    <div class="card">
      <span class="k">Reconciles</span>
      <span class="v" id="nw-recon"></span>
      <span class="k">holdings vs stated balances</span>
    </div>
  </div>
  <p class="muted" id="nw-assumptions"></p>
</section>

<section id="household" aria-labelledby="h-household">
  <h2 id="h-household">HOUSEHOLD (SYNTHETIC TWIN SUMMARY)</h2>
  <div class="cards">
    <div class="card"><span class="k">Members</span><span class="v" id="hh-members"></span></div>
    <div class="card"><span class="k">Accounts</span><span class="v" id="hh-accounts"></span></div>
    <div class="card"><span class="k">Liquidity</span><span class="v" id="hh-liq"></span></div>
    <div class="card"><span class="k">Gross income / yr</span><span class="v" id="hh-income"></span></div>
  </div>
  <h3>Job-loss sensitivity (from twin_scenarios at build time)</h3>
  <div class="tablewrap"><table>
    <caption class="muted">Net worth impact of employment stopping for N months</caption>
    <thead><tr>
      <th scope="col">Months unemployed</th>
      <th scope="col">Net worth (USD)</th>
      <th scope="col">Delta vs baseline</th>
      <th scope="col">Liquidity after draw (months)</th>
      <th scope="col">Shortfall</th>
    </tr></thead>
    <tbody id="jl-body"></tbody>
  </table></div>
  <details><summary class="muted">Assumptions and data gaps</summary>
    <ul id="hh-gaps" class="muted"></ul>
  </details>
</section>

<section id="portfolio" aria-labelledby="h-portfolio">
  <h2 id="h-portfolio">PORTFOLIO (SYNTHETIC HOLDINGS)</h2>
  <p>Total market value: <strong id="pf-total"></strong>
     at frozen synthetic price table, as of <span id="pf-asof"></span>.
  <span id="pf-breach-badge"></span></p>
  <div class="tablewrap"><table>
    <thead><tr>
      <th scope="col">Symbol</th>
      <th scope="col">Quantity</th>
      <th scope="col">Price (USD)</th>
      <th scope="col">Value (USD)</th>
      <th scope="col">Weight %</th>
      <th scope="col">Accounts</th>
      <th scope="col">Concentration</th>
    </tr></thead>
    <tbody id="pf-body"></tbody>
  </table></div>
  <p class="muted">Concentration rule: flag any single name above
  <span id="pf-cap"></span>% weight.</p>
</section>

<section id="risk" aria-labelledby="h-risk">
  <h2 id="h-risk">RISK</h2>
  <div class="cards">
    <div class="card"><span class="k">Annualized vol (SPY proxy)</span><span class="v" id="rk-vol"></span></div>
    <div class="card"><span class="k">Max drawdown</span><span class="v" id="rk-mdd"></span></div>
    <div class="card"><span class="k">Top-name concentration</span><span class="v" id="rk-conc"></span></div>
    <div class="card"><span class="k">Kill-switch</span><span class="v" id="rk-kill"></span></div>
  </div>
  <p class="muted" id="rk-detail"></p>
  <h3>Model disclosure (verbatim)</h3>
  <div class="disclosure" id="rk-disclosure"></div>
</section>

<section id="decisions" aria-labelledby="h-decisions">
  <h2 id="h-decisions">DECISIONS QUEUE</h2>
  <p><span id="dc-id" class="badge accent"></span>
     <span id="dc-appr"></span>
     confidence <output id="dc-conf" aria-label="Decision confidence"></output>,
     reversibility: <span id="dc-rev" class="muted"></span></p>
  <h3>Alternatives considered</h3>
  <div class="tablewrap"><table>
    <thead><tr>
      <th scope="col">Alternative</th>
      <th scope="col">Engine</th>
      <th scope="col">Key figures</th>
    </tr></thead>
    <tbody id="dc-body"></tbody>
  </table></div>
  <h3>Constraints, cutoff, monitoring</h3>
  <div id="dc-meta" class="muted"></div>
  <h3>Invalidate this decision when</h3>
  <ul id="dc-inval" class="muted"></ul>
</section>

<section id="scenarios" aria-labelledby="h-scenarios">
  <h2 id="h-scenarios">SCENARIOS</h2>
  <div class="sim-banner" role="note">SIMULATION NOT PREDICTION. These sliders
  replay deterministic what-if arithmetic on the synthetic twin's frozen
  balance sheet. They do not forecast markets or outcomes.</div>
  <div class="slider-row">
    <label for="sl-job">Simulated job loss duration: <output id="sl-job-out"
      for="sl-job">0</output> months</label>
    <input type="range" id="sl-job" min="0" max="12" step="1" value="0"
      aria-label="Job loss duration in months, 0 to 12"
      aria-describedby="sim-result">
  </div>
  <div class="slider-row">
    <label for="sl-mkt">Simulated market decline: <output id="sl-mkt-out"
      for="sl-mkt">0</output> percent on all non-cash assets</label>
    <input type="range" id="sl-mkt" min="-60" max="0" step="1" value="0"
      aria-label="Market decline percent, negative 60 to 0"
      aria-describedby="sim-result">
  </div>
  <div class="cards" id="sim-result" role="status" aria-live="polite">
    <div class="card"><span class="k">Simulated net worth</span><span class="v" id="sim-nw"></span>
      <span class="k" id="sim-nw-delta"></span></div>
    <div class="card"><span class="k">Simulated liquidity</span><span class="v" id="sim-liq"></span>
      <span class="k">months of cover remaining</span></div>
    <div class="card"><span class="k">Cash remaining</span><span class="v" id="sim-cash"></span>
      <span class="k" id="sim-shortfall"></span></div>
  </div>
  <p class="muted">Method: job loss draws N x monthly core spend from cash
  accounts only; market decline scales all non-cash assets proportionally.
  Identical arithmetic to tools/fis/twin_scenarios.py apply_job_loss /
  apply_market_decline.</p>
</section>

<section id="shadow" class="research-band" aria-labelledby="h-shadow">
  <p class="research-header" id="h-shadow">RESEARCH-DIAGNOSTIC</p>
  <h2>SHADOW RESEARCH (NOT PERSONAL DATA - MODEL DIAGNOSTICS ONLY)</h2>
  <p class="muted">Freeze <span id="sh-freeze"></span>, model
  <span id="sh-model"></span>, launched <span id="sh-launch"></span>,
  horizon <span id="sh-horizon"></span> trading days,
  predictions logged: <span id="sh-count"></span>.</p>
  <p class="muted">Promotion path: <span id="sh-path"></span></p>
  <div class="tablewrap"><table>
    <thead><tr>
      <th scope="col">Cohort</th>
      <th scope="col">Model state</th>
      <th scope="col">Predictions</th>
      <th scope="col">Graded</th>
      <th scope="col">Calibration</th>
      <th scope="col">Excess net of costs</th>
      <th scope="col">Promotion</th>
    </tr></thead>
    <tbody id="sh-body"></tbody>
  </table></div>
  <p class="muted">Research hygiene: <span id="sh-hygiene"></span></p>
</section>

<section id="dataquality" aria-labelledby="h-dq">
  <h2 id="h-dq">DATA QUALITY (REGISTRY FRESHNESS)</h2>
  <div class="tablewrap"><table>
    <thead><tr>
      <th scope="col">Dataset</th>
      <th scope="col">Coverage</th>
      <th scope="col">Stale by (days)</th>
      <th scope="col">License</th>
      <th scope="col">Notes</th>
    </tr></thead>
    <tbody id="dq-body"></tbody>
  </table></div>
  <p class="muted" id="dq-macro"></p>
</section>

<section id="provenance" aria-labelledby="h-prov">
  <h2 id="h-prov">PROVENANCE (SAMPLE LINEAGE CHAIN)</h2>
  <p class="muted" id="pv-legend"></p>
  <ol class="chain" id="pv-chain" reversed></ol>
  <p class="muted">Store holds <span id="pv-count"></span> artifacts. Digests
  shown are content hashes recorded at computation time.</p>
</section>

<section id="health" aria-labelledby="h-health">
  <h2 id="h-health">SYSTEM HEALTH (SELFTEST MATRIX)</h2>
  <div class="tablewrap"><table>
    <thead><tr>
      <th scope="col">Component</th>
      <th scope="col">Passed</th>
      <th scope="col">Failed</th>
      <th scope="col">Status</th>
      <th scope="col">Detail</th>
    </tr></thead>
    <tbody id="hl-body"></tbody>
  </table></div>
  <p class="muted">Built <span id="hl-ts"></span>. Overall:
  <span id="hl-all"></span></p>
</section>

</main>

<footer>
  FIS Experience Plane v1 | offline build, zero network calls |
  all personal-section figures synthetic |
  research sections are model diagnostics, not advice
</footer>

<script>
"use strict";
window.FIS_DATA = __DATA_JSON__;
(function(){
  function $(id){return document.getElementById(id);}
  function usd(x){
    var neg=x<0; var v=Math.abs(Math.round(x));
    var s="$"+v.toString().replace(/\\B(?=(\\d{3})+(?!\\d))/g,",");
    return neg?"-"+s:s;
  }
  function esc(s){
    return String(s==null?"":s).replace(/&/g,"&amp;")
      .replace(/</g,"&lt;").replace(/>/g,"&gt;")
      .replace(/"/g,"&quot;").replace(/'/g,"&#39;").replace(/`/g,"&#96;");
  }
  // FRESHNESS POLICY START
  var FRESHNESS_SLA_DAYS=5;
  function viewDataAge(value,nowMs){
    var text=typeof value==="string"?value:"";
    var dayOnly=/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(text);
    var utcStamp=/^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:[.][0-9]{3})?Z$/.test(text);
    var ms=Date.parse(dayOnly?text+"T00:00:00Z":text);
    if((!dayOnly&&!utcStamp)||!Number.isFinite(ms)||!Number.isFinite(nowMs)){
      return {status:"UNVERIFIED",as_of:null,age_days:null};
    }
    var roundtrip=new Date(ms).toISOString();
    if((dayOnly&&roundtrip.slice(0,10)!==text)||
       (!dayOnly&&roundtrip.replace(".000Z","Z")!==text.replace(".000Z","Z"))){
      return {status:"UNVERIFIED",as_of:null,age_days:null};
    }
    var age=(nowMs-ms)/86400000;
    return {status:age<0?"FUTURE":age>FRESHNESS_SLA_DAYS?"HISTORICAL":"DATED",
      as_of:text,age_days:Math.floor(age)};
  }
  function reportFreshness(data,nowMs){
    data=data||{};
    var household=data.household||{},portfolio=data.portfolio||{},risk=data.risk||{};
    var decision=data.decision||{},cutoff=decision.info_cutoff||{};
    var inputs=[household.as_of,portfolio.as_of,risk.series_end||
      (risk.disclosure||{}).data_as_of,cutoff.as_of];
    var datasets=(data.dataquality||{}).datasets||[];
    if(!Array.isArray(datasets)||!datasets.length){datasets=[];inputs.push(null);}
    var unlicensed=false;
    datasets.forEach(function(d){
      inputs.push(d.coverage_end);
      if(d.license_status!=="verified-open"&&d.license_status!=="licensed"){unlicensed=true;}
    });
    var states=[viewDataAge(data.build_ts_utc,nowMs)].concat(inputs.map(function(v){
      return viewDataAge(v,nowMs);
    }));
    var unknown=states.some(function(s){return s.status==="UNVERIFIED"||s.status==="FUTURE";});
    var historical=states.some(function(s){return s.status==="HISTORICAL";});
    var dates=states.slice(1).filter(function(s){return s.as_of&&s.status!=="FUTURE";})
      .map(function(s){return s.as_of.slice(0,10);}).sort();
    return {status:unknown||unlicensed?"UNVERIFIED":historical?"HISTORICAL":"DATED",
      historical:historical,requires_refresh:unknown||historical||unlicensed,
      oldest_as_of:dates.length?dates[0]:null,sla_days:FRESHNESS_SLA_DAYS};
  }
  // FRESHNESS POLICY END
  var D=window.FIS_DATA;
  function updateFreshness(){
    var now=Date.now(),state=reportFreshness(D,now);
    var label=state.requires_refresh?"HISTORICAL / UNVERIFIED SNAPSHOT":"DATED SNAPSHOT";
    $("freshness-banner").textContent=label+". Oldest input date: "+
      (state.oldest_as_of||"unknown")+". Viewed "+new Date(now).toISOString().slice(0,10)+". "+
      (state.requires_refresh?"Refresh and verify the data before relying on these figures. ":
        "Dates are within the reporting window. ")+"Reporting window: "+state.sla_days+" days.";
    document.documentElement.classList.toggle("historical-output",state.requires_refresh);
    document.querySelectorAll("[data-freshness-asof]").forEach(function(cell){
      var age=viewDataAge(cell.getAttribute("data-freshness-asof"),now);
      cell.textContent=age.status==="UNVERIFIED"?"unknown date":age.status==="FUTURE"?
        "future date - unverified":age.age_days+" days"+(age.status==="HISTORICAL"?" - historical":"");
    });
  }
  updateFreshness();
  setInterval(updateFreshness,60000);
  document.addEventListener("visibilitychange",updateFreshness);

  // HOME
  var nw=D.household.net_worth;
  $("nw-value").textContent=usd(nw.value);
  $("nw-asof").textContent=D.household.as_of;
  $("nw-liq").textContent=D.household.liquidity.months_of_cover.toFixed(1);
  $("nw-recon").innerHTML=nw.reconciles
    ?'<span class="badge ok">YES</span>'
    :'<span class="badge bad">NO</span>';
  $("nw-assumptions").textContent=
    "Assumptions: "+D.household.assumptions.join("; ")+".";

  // HOUSEHOLD
  $("hh-members").textContent=D.household.members;
  $("hh-accounts").textContent=D.household.accounts;
  $("hh-liq").textContent=D.household.liquidity.months_of_cover.toFixed(1);
  $("hh-income").textContent=usd(D.household.cash_flow.gross_income);
  var jb=$("jl-body");
  D.household.job_loss_sensitivity.forEach(function(r){
    var tr=document.createElement("tr");
    tr.innerHTML="<td>"+r.months+"</td>"
      +"<td>"+usd(r.net_worth_usd)+"</td>"
      +"<td>"+(r.delta_usd===0?"baseline":"-"+usd(-r.delta_usd).slice(0))+"</td>"
      +"<td>"+r.liquidity_months.toFixed(2)+"</td>"
      +"<td>"+(r.shortfall_usd>0?'<span class="badge bad">'+usd(r.shortfall_usd)+" shortfall</span>":'<span class="badge ok">covered</span>')+"</td>";
    jb.appendChild(tr);
  });
  var gapsUl=$("hh-gaps");
  D.household.data_gaps.concat(D.household.cash_flow.data_gaps||[])
    .forEach(function(g){
      var li=document.createElement("li");li.textContent=g;gapsUl.appendChild(li);
    });

  // PORTFOLIO
  var pf=D.portfolio;
  $("pf-total").textContent=usd(pf.total_market_value_usd);
  $("pf-asof").textContent=pf.as_of;
  $("pf-cap").textContent=pf.concentration_cap_pct.toFixed(0);
  var pb=$("pf-body");
  pf.holdings.forEach(function(h){
    var tr=document.createElement("tr");
    tr.innerHTML="<td>"+esc(h.symbol)+"</td>"
      +"<td>"+h.qty.toLocaleString("en-US")+"</td>"
      +"<td>"+usd(h.price_usd)+"</td>"
      +"<td>"+usd(h.value_usd)+"</td>"
      +"<td>"+h.weight_pct.toFixed(2)+"</td>"
      +"<td>"+h.accounts.map(esc).join(", ")+"</td>"
      +"<td>"+(h.concentration_flag
        ?'<span class="badge bad">CONCENTRATION '+h.weight_pct.toFixed(2)+'% &gt; '+pf.concentration_cap_pct+'%</span>'
        :'<span class="badge ok">within cap</span>')+"</td>";
    pb.appendChild(tr);
  });
  $("pf-breach-badge").innerHTML=pf.zphr_concentration_breach
    ?'<span class="badge bad">ZPHR CONCENTRATION BREACH: '+pf.zphr_weight_pct.toFixed(2)+'%</span>'
    :'<span class="badge ok">ZPHR within cap ('+pf.zphr_weight_pct.toFixed(2)+'%)</span>';

  // RISK
  var rk=D.risk;
  $("rk-vol").textContent=(100*rk.ann_vol).toFixed(1)+"%";
  $("rk-mdd").textContent=(100*rk.max_drawdown).toFixed(1)+"%";
  $("rk-conc").textContent=pf.zphr_weight_pct.toFixed(2)+"%";
  var killEl=$("rk-kill");
  killEl.innerHTML=rk.kill_switch.status==="TRIGGERED"
    ?'<span class="badge bad">TRIGGERED</span>'
    :'<span class="badge ok">CLEAR</span>';
  var det="Benchmark series "+rk.benchmark_series+", "+rk.series_start
    +" to "+rk.series_end+" ("+rk.n_obs+" daily returns). 1-day ES95="
    +(100*rk.es95).toFixed(1)+"%. Kill-switch limits: "
    +Object.keys(rk.kill_switch.limits).map(function(k){
      return k+" <= "+rk.kill_switch.limits[k].max;
    }).join(", ")
    +". Breached: "+(rk.kill_switch.breached_metrics.length
      ?rk.kill_switch.breached_metrics.join(", "):"none")+".";
  $("rk-detail").textContent=det;
  var dl=document.createElement("dl");
  Object.keys(rk.disclosure).forEach(function(k){
    var dt=document.createElement("dt");
    dt.style.fontWeight="bold";dt.textContent=k.toUpperCase();
    dl.appendChild(dt);
    var dd=document.createElement("dd");
    dd.style.marginLeft="1rem";
    var v=rk.disclosure[k];
    if(v instanceof Array){dd.textContent=v.join(" | ");}
    else if(v instanceof Object){dd.textContent=JSON.stringify(v);}
    else{dd.textContent=String(v);}
    dl.appendChild(dd);
  });
  $("rk-disclosure").appendChild(dl);

  // DECISIONS
  var dc=D.decision;
  $("dc-id").textContent=dc.decision_id;
  $("dc-conf").value=(100*dc.confidence).toFixed(0)+"%";
  $("dc-rev").textContent=dc.reversibility;
  $("dc-appr").innerHTML=dc.approval_required
    ?'<span class="badge warn">APPROVAL REQUIRED: human sign-off before any execution</span>'
    :'<span class="badge ok">no human approval pending</span>';
  var db=$("dc-body");
  dc.alternatives.forEach(function(a){
    var figs=[];
    ["proceeds_usd","after_tax_proceeds_usd","tax_usd","var95_pre",
     "review_date","top_lot"].forEach(function(k){
      if(a[k]!==undefined){
        var val=a[k];
        figs.push(k+": "+(typeof val==="number"&&(k.indexOf("_usd")>=0)
          ?usd(val):val));
      }
    });
    var tr=document.createElement("tr");
    tr.innerHTML='<td>'+esc(a.id)
      +(a.id==="hold_no_action"?' <span class="badge accent">no-action option</span>':'')
      +'</td><td>'+esc(a.engine)+'</td><td>'
      +(figs.length?esc(figs.join("; ")):'<span class="muted">-</span>')
      +"</td>";
    db.appendChild(tr);
  });
  var meta=[];
  meta.push("Objectives: "+dc.objectives.primary+" (secondary: "
    +dc.objectives.secondary+")");
  meta.push("Constraints: max single name "+dc.constraints.max_single_name_pct
    +"%; liquidity floor "+usd(dc.constraints.liquidity_floor_usd)
    +"; risk tolerance "+dc.constraints.risk_tolerance);
  meta.push("Info cutoff: as-of "+dc.info_cutoff.as_of+", knowledge date "
    +dc.info_cutoff.knowledge_date+"; prices known through "
    +dc.info_cutoff.prices_known_through);
  meta.push("Expected outcomes ("+dc.expected_outcomes.note+"): median "
    +usd(dc.expected_outcomes.scenario_median_usd)+", p5 "
    +usd(dc.expected_outcomes.scenario_p5_usd));
  meta.push("Monitoring: every "+dc.monitoring_plan.cadence_days
    +" days - "+dc.monitoring_plan.checks.join("; ")
    +". Next review "+dc.monitoring_plan.next_review);
  meta.push("Data quality caveats: "+dc.data_quality.caveats.join("; "));
  var metaEl=$("dc-meta");
  meta.forEach(function(m){
    var p=document.createElement("p");p.textContent="- "+m;metaEl.appendChild(p);
  });
  var inv=$("dc-inval");
  (dc.invalidation_conditions||[]).forEach(function(c){
    var li=document.createElement("li");li.textContent=c;inv.appendChild(li);
  });

  // SCENARIOS (client-side recompute)
  var sp=D.household.scenario_params;
  var slJob=$("sl-job"), slMkt=$("sl-mkt");
  function recompute(){
    var months=parseInt(slJob.value,10);
    var declinePct=parseInt(slMkt.value,10)/100;
    $("sl-job-out").value=String(months);
    $("sl-mkt-out").value=String(parseInt(slMkt.value,10));
    var spend=sp.monthly_spend_usd;
    var draw=months*spend;
    var cashAfter=Math.max(sp.cash_total_usd-draw,0);
    var unspent=Math.max(draw-sp.cash_total_usd,0);
    var noncash=sp.non_cash_assets_usd*(1+declinePct);
    var simNW=cashAfter+noncash-sp.liabilities_usd;
    var liqMonths=spend>0?cashAfter/spend:0;
    $("sim-nw").textContent=usd(simNW);
    var d=simNW-sp.baseline_net_worth_usd;
    $("sim-nw-delta").textContent=(d>=0?"+":"")+usd(d)+" vs baseline";
    $("sim-liq").textContent=liqMonths.toFixed(2);
    $("sim-cash").textContent=usd(cashAfter);
    $("sim-shortfall").textContent=unspent>0
      ?"SHORTFALL: draw exceeds cash by "+usd(unspent):"no shortfall";
  }
  slJob.addEventListener("input",recompute);
  slMkt.addEventListener("input",recompute);
  recompute();

  // SHADOW RESEARCH
  var sh=D.shadow, hy=D.hygiene;
  $("sh-freeze").textContent=sh.freeze_id;
  $("sh-model").textContent=sh.model_version;
  $("sh-launch").textContent=sh.launched_utc;
  $("sh-horizon").textContent=sh.horizon_trading_days;
  $("sh-count").textContent=sh.prediction_count;
  $("sh-path").textContent=sh.promotion_path;
  var sb=$("sh-body");
  sh.cohorts.forEach(function(c){
    var promo;
    if(c.promotion_eligible===false&&c.promotion_blocked_reason){
      var badge=document.createElement("span");
      badge.className="badge bad";
      badge.setAttribute("title", String(c.promotion_blocked_reason));
      badge.textContent="PROMOTION-BLOCKED";
      promo=badge.outerHTML;
    }else if(c.promotion_eligible){
      promo='<span class="badge ok">eligible (shadow-only)</span>';
    }else{promo='<span class="badge">n/a</span>';}
    var calib=c.calibration_inside_p10_p90===null||c.calibration_inside_p10_p90===undefined
      ?'<span class="muted">not graded yet</span>'
      :(c.calibration_inside_p10_p90
        ?'<span class="badge ok">inside p10-p90 ('+esc(c.calibration_bucket)+')</span>'
        :'<span class="badge bad">OUTSIDE p10-p90</span>');
    var excess=c.excess_net_of_costs===undefined||c.excess_net_of_costs===null
      ?'-'
      :(100*c.excess_net_of_costs).toFixed(2)+"%";
    var stateBadge=c.model_state==="dev-rejected"
      ?'<span class="badge warn">'+esc(c.model_state)+'</span>'
      :'<span class="badge">'+esc(c.model_state)+'</span>';
    var tr=document.createElement("tr");
    tr.innerHTML="<td><strong>"+esc(c.cohort_id)+'</strong><br><span class="muted">'
      +esc(c.label)+"</span></td>"
      +"<td>"+stateBadge+"</td>"
      +"<td>"+c.predictions+"</td>"
      +"<td>"+c.graded+"</td>"
      +"<td>"+calib+"</td>"
      +"<td>"+excess+"</td>"
      +"<td>"+promo+"</td>";
    sb.appendChild(tr);
  });
  $("sh-hygiene").textContent=hy.contamination_records
    +" contamination-ledger records spanning "
    +hy.contamination_datasets.length+" datasets; tournament: "
    +hy.tournament_summary.candidates+" candidates, controls_clean="
    +hy.tournament_summary.controls_clean+", dev_passed="
    +(hy.tournament_summary.dev_passed||[]).length;

  // DATA QUALITY
  var qb=$("dq-body");
  D.dataquality.datasets.forEach(function(d){
    var age=viewDataAge(d.coverage_end,Date.now());
    var stale=age.age_days;
    var staleHtml=age.status==="UNVERIFIED"?'unknown date':age.status==="FUTURE"?
      'future date - unverified':stale+" days"+(age.status==="HISTORICAL"?" - historical":"");
    var notes=[d.source_note].concat(d.known_defects).filter(Boolean)
      .join(" | ");
    var tr=document.createElement("tr");
    tr.innerHTML="<td><strong>"+esc(d.dataset_id)+"</strong>"
      +(d.version?'<br><span class="muted">'+esc(d.version)+"</span>":"")
      +"</td>"
      +"<td>"+esc(String(d.coverage_start||"?"))+" .. "
        +esc(String(d.coverage_end||"?"))+"</td>"
      +"<td>"+staleHtml+"</td>"
      +"<td>"+(d.license_status
        ?'<span class="badge '+(d.license_status==="unverified"?"warn":"ok")
          +'">'+esc(d.license_status)+"</span>"
        :'<span class="muted">-</span>')+"</td>"
      +'<td class="muted">'+esc(notes)+"</td>";
    qb.appendChild(tr);
    tr.children[2].setAttribute("data-freshness-asof",String(d.coverage_end||""));
  });
  var mc=D.dataquality.macro_counts;
  if(mc){
    $("dq-macro").textContent="Macro vintages ("+D.dataquality.macro_generated_utc
      +"): actual-vintage-history="+mc["actual-vintage-history"]
      +", reconstruction="+mc["release-calendar-reconstruction"]
      +", assumed-lag="+mc["assumed-lag"]
      +", no-safe-use="+mc["no-safe-use"]+".";
  }

  // PROVENANCE
  var pv=D.provenance;
  $("pv-legend").textContent=pv.chain_legend;
  $("pv-count").textContent=pv.artifact_count;
  var pc=$("pv-chain");
  pv.chain.slice().reverse().forEach(function(n){
    var kindLabel={fact:"FACT/SOURCE",artifact:"CALC"}[n.kind]||String(n.kind);
    var li=document.createElement("li");
    li.innerHTML='<code>'+esc(n.id)+'</code> '
      +'<span class="badge '+(n.kind==="fact"?"accent":"")+'">'
      +esc(kindLabel)+"</span>"
      +'<br><span class="muted">digest='+esc(n.digest||"-")
      +" version="+esc(n.version==null?"-":n.version)
      +" computed_at="+esc(n.computed_at||"-")
      +(n.script_path?" via "+esc(n.script_path):"")
      +(n.inputs&&n.inputs.length?"<br>inputs: "+n.inputs.map(esc).join(", "):"")
      +"</span>";
    pc.appendChild(li);
  });

  // SYSTEM HEALTH
  var hl=D.health;
  var hb=$("hl-body");
  hl.checks.forEach(function(c){
    var tr=document.createElement("tr");
    tr.innerHTML="<td>"+esc(c.component)+"</td>"
      +"<td>"+c.passed+"</td>"
      +"<td>"+c.failed+"</td>"
      +"<td>"+(c.ok?'<span class="badge ok">PASS</span>'
               :'<span class="badge bad">FAIL</span>')+"</td>"
      +'<td class="muted">'+esc(c.detail)+"</td>";
    hb.appendChild(tr);
  });
  $("hl-ts").textContent=hl.built_at_utc;
  $("hl-all").innerHTML=hl.all_ok
    ?'<span class="badge ok">ALL GREEN</span>'
    :'<span class="badge bad">FAILURES PRESENT</span>';
})();
</script>
</body>
</html>
"""


def render_page(payload, build_ts=None):
    """Pure rendering boundary, usable with synthetic payloads in regression tests."""
    data_json = json.dumps(payload, ensure_ascii=True, sort_keys=True,
                           default=str, allow_nan=False).replace("<", "\\u003c")
    html = TEMPLATE.replace("__DATA_JSON__", data_json)
    return html.replace("__BUILD_TS__", build_ts or BUILD_TS)


def main():
    twin, portfolio = load_twin()

    risk_ok = True
    try:
        risk, disclosure, finalize = load_risk()
        ks, breached = finalize(portfolio["zphr_weight_pct"])
        risk["kill_switch"] = ks
    except Exception as exc:  # pragma: no cover
        risk_ok = False
        risk = {"error": str(exc), "kill_switch": {"status": "UNKNOWN",
                "breached_metrics": [], "limits": {}, "metrics": {}}}
        disclosure = {"error": str(exc)}

    twin_ok = twin["net_worth"]["value"] > 0

    payload = {
        "build_ts_utc": BUILD_TS,
        "household": twin,
        "portfolio": portfolio,
        "risk": dict(risk, kill_switch=None) if risk_ok else risk,
        "decision": load_decision(),
        "shadow": load_shadow(),
        "hygiene": load_research_hygiene(),
        "dataquality": load_data_quality(),
        "provenance": load_provenance(),
    }
    if risk_ok:
        rk = dict(risk)
        rk["kill_switch"] = ks
        rk["disclosure"] = disclosure
        payload["risk"] = rk
    else:
        payload["risk"]["disclosure"] = disclosure
    payload["health"] = load_system_health(risk_ok, twin_ok)

    html = render_page(payload)

    out = os.path.join(HERE, "index.html")
    with open(out, "w", encoding="ascii") as fh:
        fh.write(html)
    size = os.path.getsize(out)
    print("WROTE %s (%d bytes)" % (out, size))
    print("sections:", ",".join([
        "home", "household", "portfolio", "risk", "decisions",
        "scenarios", "shadow", "dataquality", "provenance", "health"]))
    print("risk_ok=%s twin_ok=%s kill=%s zphr=%.2f%%" % (
        risk_ok, twin_ok,
        risk.get("kill_switch", {}).get("status"),
        portfolio["zphr_weight_pct"]))


if __name__ == "__main__":
    main()
