#!/usr/bin/env python3
r"""gate-eval.py -- deterministic verdict engine + validator for the judgment gates.

The three gates (GATE-F trade-generation discipline, GATE-T trigger-fired
adjudication, GATE-B build-vs-ship) freeze judgment calls into static decision
tables (tools/gate-rules.json). A runtime model NEVER decides a verdict: it
fills markers with provenance, runs --compute to obtain the verdict + mandates,
transcribes them into the gate sheet, then runs --check to confirm.

Modes:
  --compute <sheet>            parse markers, apply rules, print verdict + mandates. Exit 0.
  --check <sheet>              full validation (schema, markers, provenance paths,
                               recomputed verdict == recorded, mandates, review_date,
                               ASCII). Exit 0 pass / 2 fail (gate semantics).
  --calibrate [--since DATE]   routing-around detector: expected-vs-gated events per
                               gate + mandate follow-through. Exit 0 always (report).
  --json                       machine output for any mode.

Findings use the X6 shape {dimension, expected, actual, status: "FAIL"}.
Deterministic, offline, ASCII-only (Pattern 22). No session-scoped MCP.
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import os as _os
VAULT_ROOT = Path(_os.environ.get("VAULT_ROOT", r"/path/to/vault"))  # D5 parameterization (2026-08-10)
RULES_PATH = VAULT_ROOT / "tools" / "gate-rules.json"
GATES_DIR = VAULT_ROOT / "wiki" / "research" / "gates"
ANALYSES_DIR = VAULT_ROOT / "wiki" / "investing" / "analyses"
THESES_DIR = VAULT_ROOT / "Atlas" / "concepts" / "investing" / "theses"
BRIEFINGS_DIR = VAULT_ROOT / "Calendar" / "decisions" / "briefings"
EOD_LEDGER = VAULT_ROOT / "Calendar" / "decisions" / "execute-or-decline.md"

VERDICTS = {
    "f": ["DISCIPLINED", "FOMO-SUSPECT", "BLOCKED"],
    "t": ["FIRED", "NOT-FIRED", "INSUFFICIENT-EVIDENCE"],
    "b": ["BUILD-JUSTIFIED", "SHIP-FIRST", "DECLINE"],
}
OUTCOMES = ["VINDICATED", "WRONG", "OVERRIDDEN", "n/a"]
STATUS_ENUM = ["active", "paused", "done", "dropped", "stub", "deprecated",
               "draft", "complete", "stale"]
SCHEME_RE = re.compile(r"^[a-z][a-z0-9_+-]{2,}:")
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def read_text(path):
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return Path(path).read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return Path(path).read_text(errors="replace")


def load_rules():
    return json.loads(read_text(RULES_PATH))


def parse_frontmatter(text):
    """Return (frontmatter_dict_or_None, error_or_None)."""
    if not text.startswith("---"):
        return None, "no frontmatter delimiter at byte 0"
    m = re.match(r"^---\s*\n(.*?)\n---\s*(\n|$)", text, re.DOTALL)
    if not m:
        return None, "unterminated frontmatter block"
    try:
        import yaml
    except ImportError:
        return None, "PyYAML not importable"
    try:
        fm = yaml.safe_load(m.group(1))
    except Exception as exc:  # yaml parse error
        return None, "frontmatter YAML parse error: %s" % exc
    if not isinstance(fm, dict):
        return None, "frontmatter is not a mapping"
    return fm, None


def marker_value(markers, name):
    entry = markers.get(name)
    if isinstance(entry, dict) and "value" in entry:
        return entry["value"]
    return entry


# ---------------------------------------------------------------- verdicts

def compute_f(markers, gate_rules):
    th = gate_rules["thresholds"]
    v = lambda n: marker_value(markers, n)
    points = []
    if v("catalyst_age_hours") is not None and v("catalyst_age_hours") < th["catalyst_age_hours_lt"]:
        points.append("catalyst_lt_%dh" % th["catalyst_age_hours_lt"])
    tenure_fires = (not v("held_position")) and (v("tenure_days") is not None
                                                 and v("tenure_days") < th["tenure_days_lt"])
    if tenure_fires:
        points.append("tenure_lt_%dd" % th["tenure_days_lt"])
    pad = v("prior_analysis_days")
    if pad is None or pad > th["prior_analysis_days_gt"]:
        points.append("no_recent_analysis")
    if v("regime_alert"):
        points.append("regime_alert")
    if v("move_5d_pct") is not None and abs(v("move_5d_pct")) >= th["move_5d_pct_gte"]:
        points.append("move_5d_gte_%dpct" % th["move_5d_pct_gte"])
    if v("after_hours_origination"):
        points.append("after_hours")
    if v("trades_7d") is not None and v("trades_7d") >= th["trades_7d_gte"]:
        points.append("trades_7d_gte_%d" % th["trades_7d_gte"])

    if v("trigger_backed") and v("action_side") in ("TRIM", "EXIT"):
        verdict = "DISCIPLINED"
        detail = {"rule": 1, "fomo_points": len(points), "points": points}
    elif v("zone_preregistered") and v("action_side") == "ADD":
        # rule 1b -- a pre-registered zone firing is the plan working, not FOMO.
        # Short-circuits BEFORE fomo_points scoring, exactly like rule 1 does for
        # TRIM/EXIT. Absent marker (legacy sheet) is falsy -> rule never fires.
        verdict = "DISCIPLINED"
        detail = {"rule": "1b", "fomo_points": len(points), "points": points}
    else:
        combo = (tenure_fires and pad is None
                 and v("catalyst_age_hours") is not None
                 and v("catalyst_age_hours") < th["blocked_combo_catalyst_lt"])
        n = len(points)
        if n >= th["blocked_points_gte"] or combo:
            verdict = "BLOCKED"
            detail = {"rule": 2, "fomo_points": n, "points": points, "combo": combo}
        elif n >= th["suspect_points_min"]:
            verdict = "FOMO-SUSPECT"
            detail = {"rule": 3, "fomo_points": n, "points": points}
        else:
            verdict = "DISCIPLINED"
            detail = {"rule": 4, "fomo_points": n, "points": points}
    mandates = list(gate_rules["mandates"][verdict])
    return verdict, mandates, detail


def compute_t(markers, gate_rules):
    th = gate_rules["thresholds"]
    v = lambda n: marker_value(markers, n)
    evidence = v("evidence") or []
    qualified = [e for e in evidence
                 if isinstance(e, dict) and str(e.get("grade", "")).upper() in ("A", "B")]
    distinct = len(set(str(e.get("source", "")).lower() for e in qualified))
    if len(qualified) < th["min_evidence_items"] or distinct < th["min_distinct_sources"]:
        verdict = "INSUFFICIENT-EVIDENCE"
        detail = {"rule": 1, "qualified_items": len(qualified), "distinct_sources": distinct}
    else:
        counter_ok = True
        if v("consecutive_required") is not None:
            counter_ok = (v("consecutive_count") is not None
                          and v("consecutive_count") >= v("consecutive_required"))
        if v("metric_condition_met") and v("window_ok") and counter_ok:
            verdict = "FIRED"
            detail = {"rule": 2, "qualified_items": len(qualified),
                      "distinct_sources": distinct, "counter_ok": counter_ok}
        else:
            verdict = "NOT-FIRED"
            detail = {"rule": 3, "qualified_items": len(qualified),
                      "distinct_sources": distinct, "counter_ok": counter_ok}
    mandates = [m.replace("<tier>", str(v("tier"))) for m in gate_rules["mandates"][verdict]]
    return verdict, mandates, detail


def compute_b(markers, gate_rules):
    v = lambda n: marker_value(markers, n)
    if v("similar_organ") is not None and v("similar_organ_consumed_30d") is False:
        verdict, rule = "DECLINE", 1
    elif v("user_directive"):
        verdict, rule = "BUILD-JUSTIFIED", 2
    elif v("closes_eod_id") is None and (v("overdue_eod_count") or 0) >= 1:
        verdict, rule = "SHIP-FIRST", 3
    else:
        verdict, rule = "BUILD-JUSTIFIED", 4
    mandates = list(gate_rules["mandates"][verdict])
    if verdict == "BUILD-JUSTIFIED":
        if v("size_class") == "L":
            mandates.append("consumption-review-30d")
        if (v("overdue_eod_count") or 0) >= 1:
            mandates.append("list-displaced-eod-rows")
    return verdict, mandates, {"rule": rule}


COMPUTE = {"f": compute_f, "t": compute_t, "b": compute_b}


def expected_review_date(mode, verdict, markers, gate_rules, sheet_date):
    days_map = gate_rules.get("review_date_days", {})
    days = days_map.get(verdict)
    if mode == "b" and verdict == "BUILD-JUSTIFIED" and marker_value(markers, "size_class") == "L":
        days = days_map.get("BUILD-JUSTIFIED_L", days)
    if days is None:
        return None
    return (sheet_date + timedelta(days=days)).isoformat()


# ---------------------------------------------------------------- check

def finding(dimension, expected, actual):
    return {"dimension": dimension, "expected": expected, "actual": actual, "status": "FAIL"}


def check_sheet(path, rules):
    findings = []
    p = Path(path)
    if not p.exists():
        return [finding("file", "exists", "missing: %s" % path)], None
    raw = p.read_bytes()
    non_ascii = [i for i, b in enumerate(raw) if b > 127]
    if non_ascii:
        findings.append(finding("ascii (Pattern 22)", "all bytes <= 127",
                                "%d bytes > 127 (first at offset %d)" % (len(non_ascii), non_ascii[0])))
    text = read_text(p)
    fm, err = parse_frontmatter(text)
    if fm is None:
        findings.append(finding("frontmatter", "parseable YAML frontmatter", err))
        return findings, None

    cats = fm.get("categories")
    if not (isinstance(cats, list) and "wiki" in cats):
        findings.append(finding("frontmatter.categories", "list containing 'wiki'", repr(cats)))
    if fm.get("status") not in STATUS_ENUM:
        findings.append(finding("frontmatter.status", "one of %s" % STATUS_ENUM, repr(fm.get("status"))))
    for df in ("created", "updated"):
        val = str(fm.get(df, ""))
        if not ISO_RE.match(val):
            findings.append(finding("frontmatter.%s" % df, "ISO YYYY-MM-DD", repr(fm.get(df))))

    gate = fm.get("gate")
    if not isinstance(gate, dict):
        findings.append(finding("gate block", "gate: mapping in frontmatter", repr(type(gate).__name__)))
        return findings, None
    if gate.get("schema_version") != 1:
        findings.append(finding("gate.schema_version", 1, repr(gate.get("schema_version"))))
    mode = gate.get("mode")
    if mode not in VERDICTS:
        findings.append(finding("gate.mode", "one of t|f|b", repr(mode)))
        return findings, None
    if not str(gate.get("subject", "")).strip():
        findings.append(finding("gate.subject", "non-empty string", repr(gate.get("subject"))))
    if not isinstance(gate.get("golden", False), bool):
        findings.append(finding("gate.golden", "bool", repr(gate.get("golden"))))
    if mode == "f":
        ticker = gate.get("ticker")
        if not (isinstance(ticker, str) and ticker.isupper() and ticker):
            findings.append(finding("gate.ticker", "UPPERCASE ticker string (f-mode)", repr(ticker)))

    gate_rules = rules["gates"][mode]
    markers = gate.get("markers") or {}
    spec = gate_rules["markers"]
    for name, mspec in spec.items():
        if name not in markers:
            if mspec.get("optional"):
                continue  # optional marker: absent == its declared default (back-compat)
            findings.append(finding("marker.%s" % name, "present", "missing"))
            continue
        entry = markers[name]
        if not (isinstance(entry, dict) and "value" in entry and "prov" in entry):
            findings.append(finding("marker.%s" % name, "{value, prov} mapping", repr(entry)))
            continue
        val, prov = entry["value"], entry["prov"]
        if not (isinstance(prov, str) and prov.strip()):
            findings.append(finding("marker.%s.prov" % name, "non-empty string", repr(prov)))
        elif not SCHEME_RE.match(prov):
            target = (VAULT_ROOT / prov.split("#")[0]).resolve()
            if not target.exists():
                findings.append(finding("marker.%s.prov" % name,
                                        "vault path exists (or scheme prov like mcp:/script:/web:/test:)",
                                        "missing on disk: %s" % prov))
        ty = mspec["type"]
        ok = True
        if ty == "int":
            ok = isinstance(val, int) and not isinstance(val, bool)
        elif ty == "int_or_null":
            ok = val is None or (isinstance(val, int) and not isinstance(val, bool))
        elif ty == "number":
            ok = isinstance(val, (int, float)) and not isinstance(val, bool)
        elif ty == "bool":
            ok = isinstance(val, bool)
        elif ty == "bool_or_null":
            ok = val is None or isinstance(val, bool)
        elif ty == "str":
            ok = isinstance(val, str) and bool(val.strip())
        elif ty == "str_or_null":
            ok = val is None or (isinstance(val, str) and bool(val.strip()))
        elif ty == "enum":
            ok = val in mspec.get("values", [])
        elif ty == "list":
            ok = isinstance(val, list) and len(val) > 0
            if ok and "item_fields" in mspec:
                for i, item in enumerate(val):
                    missing = [f for f in mspec["item_fields"]
                               if not (isinstance(item, dict) and item.get(f) not in (None, ""))]
                    if missing:
                        findings.append(finding("marker.%s[%d]" % (name, i),
                                                "fields %s" % mspec["item_fields"],
                                                "missing %s" % missing))
        if not ok:
            findings.append(finding("marker.%s.value" % name, "type %s" % ty, repr(val)))

    if any(f["dimension"].startswith("marker.") and ".prov" not in f["dimension"]
           and f["actual"] == "missing" for f in findings):
        return findings, None

    try:
        verdict, mandates, detail = COMPUTE[mode](markers, gate_rules)
    except Exception as exc:
        findings.append(finding("recompute", "verdict computable from markers", "error: %s" % exc))
        return findings, None

    recorded_verdict = gate.get("verdict")
    if recorded_verdict != verdict:
        findings.append(finding("verdict", verdict, repr(recorded_verdict)))
    recorded_mandates = gate.get("mandates")
    if not isinstance(recorded_mandates, list) or sorted(recorded_mandates) != sorted(mandates):
        findings.append(finding("mandates", sorted(mandates),
                                sorted(recorded_mandates) if isinstance(recorded_mandates, list)
                                else repr(recorded_mandates)))

    created = str(fm.get("created", ""))
    if ISO_RE.match(created):
        sheet_date = date.fromisoformat(created)
        exp_review = expected_review_date(mode, verdict, markers, gate_rules, sheet_date)
        rec_review = gate.get("review_date")
        if exp_review is None:
            if rec_review not in (None, "null"):
                pass  # extra review dates are allowed (stricter than required)
        else:
            if not (isinstance(rec_review, (str, date)) and ISO_RE.match(str(rec_review))):
                findings.append(finding("gate.review_date",
                                        "ISO date (mandates present; suggested %s)" % exp_review,
                                        repr(rec_review)))

    outcome = gate.get("outcome")
    if outcome is not None and outcome not in OUTCOMES:
        findings.append(finding("gate.outcome", "null or one of %s" % OUTCOMES, repr(outcome)))

    computed = {"mode": mode, "verdict": verdict, "mandates": mandates, "detail": detail}
    return findings, computed


# ---------------------------------------------------------------- calibrate

def sheet_records():
    recs = []
    if not GATES_DIR.exists():
        return recs
    for p in sorted(GATES_DIR.glob("gate-*-*.md")):
        text = read_text(p)
        fm, err = parse_frontmatter(text)
        if fm is None or not isinstance(fm.get("gate"), dict):
            continue
        g = fm["gate"]
        created = str(fm.get("created", ""))
        if not ISO_RE.match(created):
            continue
        recs.append({"path": str(p.relative_to(VAULT_ROOT)).replace("\\", "/"),
                     "mode": g.get("mode"), "subject": str(g.get("subject", "")),
                     "ticker": g.get("ticker"), "verdict": g.get("verdict"),
                     "trigger_id": marker_value(g.get("markers") or {}, "trigger_id"),
                     "date": date.fromisoformat(created)})
    return recs


def within(d1, d2, tol_days):
    return abs((d1 - d2).days) <= tol_days


def calibrate(since, rules):
    cal = rules["calibration"]
    tol = cal["match_tolerance_days"]
    sheets = sheet_records()
    report = {"since": since.isoformat(), "gates": {}, "mandate_followthrough": [],
              "routing_around_flags": [], "notes": []}

    # --- GATE-F expected: action-rated analyses
    expected_f, misses_f, gated_f = 0, [], 0
    if ANALYSES_DIR.exists():
        for p in sorted(ANALYSES_DIR.glob("*-analysis-*.md")):
            fm, err = parse_frontmatter(read_text(p))
            if fm is None:
                continue
            created = str(fm.get("created", fm.get("updated", "")))
            if not ISO_RE.match(created):
                continue
            d = date.fromisoformat(created)
            if d < since:
                continue
            rating = str(fm.get("rating", "")).upper()
            if rating not in cal["action_ratings"]:
                continue
            expected_f += 1
            ticker = p.name.split("-analysis-")[0].upper()
            hit = any(s["mode"] == "f" and s.get("ticker") == ticker
                      and within(s["date"], d, tol) for s in sheets)
            if hit:
                gated_f += 1
            else:
                misses_f.append({"event": "analysis %s rating %s" % (p.name, rating), "date": created})
    report["gates"]["f"] = _gate_block(expected_f, gated_f, misses_f)

    # --- GATE-T expected: fired manual/evidence triggers + briefing status changes
    expected_t, misses_t, gated_t = 0, [], 0
    if THESES_DIR.exists():
        for p in sorted(THESES_DIR.glob("thesis-*.md")):
            fm, err = parse_frontmatter(read_text(p))
            if fm is None or not isinstance(fm.get("triggers"), dict):
                continue
            trig = fm["triggers"]
            for tier in ("kill", "red", "amber"):
                for t in trig.get(tier) or []:
                    if not isinstance(t, dict):
                        continue
                    manualish = (t.get("source") == "manual"
                                 or t.get("window") == "earnings_window")
                    fired = t.get("fired")
                    if not (manualish and fired):
                        continue
                    fired_s = str(fired)
                    if not ISO_RE.match(fired_s):
                        continue
                    d = date.fromisoformat(fired_s)
                    if d < since:
                        continue
                    expected_t += 1
                    hit = any(s["mode"] == "t" and s.get("trigger_id") == t.get("id")
                              and within(s["date"], d, tol) for s in sheets)
                    if hit:
                        gated_t += 1
                    else:
                        misses_t.append({"event": "trigger %s fired" % t.get("id"), "date": fired_s})
    briefing_diff_checked = False
    try:
        metas = []
        if BRIEFINGS_DIR.exists():
            for mp in sorted(BRIEFINGS_DIR.glob("*meta.json")):
                try:
                    md = json.loads(read_text(mp))
                except Exception:
                    continue
                ds = None
                m = re.search(r"(\d{4}-\d{2}-\d{2})", mp.name)
                if m:
                    ds = m.group(1)
                statuses = md.get("thesis_statuses") or md.get("thesis_status_board")
                if ds and isinstance(statuses, dict):
                    metas.append((date.fromisoformat(ds), statuses))
        metas.sort(key=lambda x: x[0])
        for (d1, s1), (d2, s2) in zip(metas, metas[1:]):
            if d2 < since:
                continue
            for thesis, status in s2.items():
                if thesis in s1 and s1[thesis] != status:
                    expected_t += 1
                    hit = any(s["mode"] == "t" and thesis.lower() in s["subject"].lower()
                              and within(s["date"], d2, tol) for s in sheets)
                    if hit:
                        gated_t += 1
                    else:
                        misses_t.append({"event": "briefing %s: %s %s -> %s"
                                         % (d2.isoformat(), thesis, s1[thesis], status),
                                         "date": d2.isoformat()})
        briefing_diff_checked = True
    except Exception as exc:
        report["notes"].append("briefing sidecar diff skipped: %s" % exc)
    report["notes"].append("briefing_diff_checked: %s" % briefing_diff_checked)
    report["gates"]["t"] = _gate_block(expected_t, gated_t, misses_t)

    # --- GATE-B expected: days with new files under .claude/skills or tools (git)
    expected_b, misses_b, gated_b = 0, [], 0
    try:
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--name-only",
             "--since=%s" % since.isoformat(), "--pretty=format:@%ad", "--date=short",
             "--", ".claude/skills", "tools"],
            cwd=str(VAULT_ROOT), capture_output=True, text=True, timeout=60)
        days = {}
        cur = None
        for line in out.stdout.splitlines():
            line = line.strip()
            if line.startswith("@"):
                cur = line[1:]
            elif line and cur and "_archive/" not in line and "/.precheck/" not in line:
                days.setdefault(cur, []).append(line)
        for ds, files in sorted(days.items()):
            if not ISO_RE.match(ds):
                continue
            d = date.fromisoformat(ds)
            if d < since:
                continue
            expected_b += 1
            hit = any(s["mode"] == "b" and within(s["date"], d, tol) for s in sheets)
            if hit:
                gated_b += 1
            else:
                misses_b.append({"event": "%d new runtime file(s), e.g. %s" % (len(files), files[0]),
                                 "date": ds})
    except Exception as exc:
        report["notes"].append("git lane skipped: %s" % exc)
    report["gates"]["b"] = _gate_block(expected_b, gated_b, misses_b)

    # --- mandate follow-through (F10)
    eod_text = read_text(EOD_LEDGER).lower() if EOD_LEDGER.exists() else ""
    for s in sheets:
        if s["date"] < since:
            continue
        if s["mode"] == "f" and s["verdict"] == "FOMO-SUSPECT":
            key = (s.get("ticker") or s["subject"]).lower()
            eod_ok = key in eod_text
            regate = any(x["mode"] == "f" and x.get("ticker") == s.get("ticker")
                         and s["date"] < x["date"] <= s["date"] + timedelta(days=7)
                         for x in sheets)
            if not (eod_ok and regate):
                report["mandate_followthrough"].append(
                    {"sheet": s["path"], "missing": [m for m, ok in
                     [("eod-row", eod_ok), ("re-gate", regate)] if not ok]})
        if s["mode"] == "t" and s["verdict"] == "INSUFFICIENT-EVIDENCE":
            key = str(s.get("trigger_id") or "").lower()
            if key and key not in eod_text:
                report["mandate_followthrough"].append(
                    {"sheet": s["path"], "missing": ["eod-row-evidence-collection"]})

    for mode_key, block in report["gates"].items():
        if (block["expected"] >= cal["min_events_for_flag"]
                and block["compliance_pct"] is not None
                and block["compliance_pct"] < cal["compliance_floor_pct"]):
            report["routing_around_flags"].append(
                "GATE-%s compliance %s%% < %d%% over %d expected events"
                % (mode_key.upper(), block["compliance_pct"],
                   cal["compliance_floor_pct"], block["expected"]))
    return report


def _gate_block(expected, gated, misses):
    pct = round(100.0 * gated / expected, 1) if expected else None
    return {"expected": expected, "gated": gated, "compliance_pct": pct, "misses": misses}


# ---------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(description="Judgment-gate verdict engine + validator")
    ap.add_argument("--compute", metavar="SHEET")
    ap.add_argument("--check", metavar="SHEET")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--since", default=None, help="ISO date for --calibrate (default: 30d ago)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    rules = load_rules()

    if args.compute:
        text = read_text(args.compute)
        fm, err = parse_frontmatter(text)
        if fm is None or not isinstance(fm.get("gate"), dict):
            print("ERROR: %s" % (err or "no gate block"))
            return 2
        gate = fm["gate"]
        mode = gate.get("mode")
        if mode not in COMPUTE:
            print("ERROR: gate.mode must be t|f|b, got %r" % mode)
            return 2
        verdict, mandates, detail = COMPUTE[mode](gate.get("markers") or {}, rules["gates"][mode])
        created = str(fm.get("created", date.today().isoformat()))
        sheet_date = date.fromisoformat(created) if ISO_RE.match(created) else date.today()
        review = expected_review_date(mode, verdict, gate.get("markers") or {},
                                      rules["gates"][mode], sheet_date)
        result = {"mode": mode, "verdict": verdict, "mandates": mandates,
                  "suggested_review_date": review, "detail": detail}
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("verdict: %s" % verdict)
            print("mandates: %s" % (", ".join(mandates) if mandates else "(none)"))
            print("suggested review_date: %s" % review)
            print("detail: %s" % json.dumps(detail))
        return 0

    if args.check:
        findings, computed = check_sheet(args.check, rules)
        result = {"sheet": args.check, "status": "PASS" if not findings else "FAIL",
                  "findings": findings, "computed": computed}
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("%s: %s" % (result["status"], args.check))
            for f in findings:
                print("  FAIL %s: expected %s, actual %s"
                      % (f["dimension"], f["expected"], f["actual"]))
        return 0 if not findings else 2

    if args.calibrate:
        since = (date.fromisoformat(args.since) if args.since
                 else date.today() - timedelta(days=30))
        report = calibrate(since, rules)
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print("Calibration since %s" % report["since"])
            for mode_key in ("f", "t", "b"):
                b = report["gates"][mode_key]
                print("  GATE-%s: expected %d, gated %d, compliance %s%%, misses %d"
                      % (mode_key.upper(), b["expected"], b["gated"],
                         b["compliance_pct"], len(b["misses"])))
            for flag in report["routing_around_flags"]:
                print("  ROUTING-AROUND: %s" % flag)
            for ft in report["mandate_followthrough"]:
                print("  FOLLOW-THROUGH MISS: %s missing %s" % (ft["sheet"], ft["missing"]))
            for note in report["notes"]:
                print("  note: %s" % note)
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
