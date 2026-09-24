#!/usr/bin/env python3
r"""test-gate-eval.py -- self-contained test harness for tools/gate-eval.py.

House convention: python tools/test-gate-eval.py runs all; --test <name> for one.
Exit 0 all-pass / 1 any-failure. Fixtures are written to a temp dir; the three
golden sheets on disk (wiki/research/gates/, gate.golden: true) run as
integration cases when present and are skipped with a note when absent.
"""

import argparse
import importlib.util
import json
import sys
import tempfile
from datetime import date
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
VAULT_ROOT = TOOLS_DIR.parent
GATES_DIR = VAULT_ROOT / "wiki" / "research" / "gates"

spec = importlib.util.spec_from_file_location("gate_eval", TOOLS_DIR / "gate-eval.py")
ge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ge)

import yaml  # noqa: E402  (gate-eval already requires it)

RULES = ge.load_rules()
TODAY = date.today().isoformat()

RESULTS = []


def record(name, ok, msg=""):
    RESULTS.append((name, ok, msg))
    print("%s %s%s" % ("PASS" if ok else "FAIL", name, (" -- " + msg) if msg else ""))


def mk(value, prov="test:fixture"):
    return {"value": value, "prov": prov}


def f_markers(**over):
    base = {
        "action_side": mk("ADD"),
        "tenure_days": mk(94),
        "held_position": mk(True),
        "catalyst_age_hours": mk(400),
        "prior_analysis_days": mk(12),
        "thesis_member": mk(True),
        "regime_alert": mk(False),
        "move_5d_pct": mk(4),
        "trades_7d": mk(0),
        "after_hours_origination": mk(False),
        "trigger_backed": mk(False),
    }
    for k, v in over.items():
        base[k] = mk(v)
    return base


def t_markers(**over):
    base = {
        "trigger_id": mk("themealpha-amber-capex-guide-down"),
        "thesis": mk("thesis-theme-alpha"),
        "tier": mk("amber"),
        "evidence": mk([
            {"source": "sec.gov", "grade": "A", "date": "2026-06-25", "statement": "s1"},
            {"source": "reuters.com", "grade": "B", "date": "2026-06-28", "statement": "s2"},
        ]),
        "metric_condition_met": mk(True),
        "window_ok": mk(True),
        "consecutive_required": mk(None),
        "consecutive_count": mk(None),
    }
    for k, v in over.items():
        base[k] = mk(v)
    return base


def b_markers(**over):
    base = {
        "closes_eod_id": mk(None),
        "overdue_eod_count": mk(0),
        "user_directive": mk(False),
        "similar_organ": mk(None),
        "similar_organ_consumed_30d": mk(None),
        "size_class": mk("M"),
        "deadline_bound": mk(False),
    }
    for k, v in over.items():
        base[k] = mk(v)
    return base


def write_sheet(tmp, name, mode, markers, verdict, mandates, review_date=None,
                ticker="TEST", subject="fixture subject"):
    fm = {
        "aliases": [],
        "categories": ["wiki"],
        "type": "report",
        "tags": ["topic/judgment-gates"],
        "status": "complete",
        "created": TODAY,
        "updated": TODAY,
        "related": [],
        "gate": {
            "schema_version": 1,
            "mode": mode,
            "subject": subject,
            "golden": False,
            "markers": markers,
            "verdict": verdict,
            "mandates": mandates,
            "review_date": review_date,
            "outcome": None,
        },
    }
    if mode == "f":
        fm["gate"]["ticker"] = ticker
    body = "# GATE fixture\n\nEvidence prose.\n"
    text = "---\n" + yaml.safe_dump(fm, sort_keys=False, allow_unicode=False) + "---\n\n" + body
    p = Path(tmp) / name
    p.write_text(text, encoding="ascii")
    return p


def computed(mode, markers):
    v, m, d = ge.COMPUTE[mode](markers, RULES["gates"][mode])
    rd = ge.expected_review_date(mode, v, markers, RULES["gates"][mode], date.today())
    return v, m, rd, d


# ------------------------------------------------------------------ tests

def test_f_blocked():
    m = f_markers(tenure_days=3, held_position=False, catalyst_age_hours=6,
                  prior_analysis_days=None, regime_alert=True)
    v, man, rd, d = computed("f", m)
    record("f_blocked", v == "BLOCKED" and d["fomo_points"] == 4,
           "verdict=%s points=%s" % (v, d))


def test_f_disciplined():
    v, man, rd, d = computed("f", f_markers())
    record("f_disciplined", v == "DISCIPLINED" and man == [] and d["fomo_points"] == 0,
           "verdict=%s points=%s" % (v, d))


def test_f_suspect():
    m = f_markers(catalyst_age_hours=20, regime_alert=True)
    v, man, rd, d = computed("f", m)
    ok = (v == "FOMO-SUSPECT" and d["fomo_points"] == 2
          and sorted(man) == sorted(RULES["gates"]["f"]["mandates"]["FOMO-SUSPECT"])
          and rd is not None)
    record("f_suspect", ok, "verdict=%s mandates=%s review=%s" % (v, man, rd))


def test_f_trigger_backed_exit():
    m = f_markers(action_side="EXIT", trigger_backed=True, tenure_days=1,
                  held_position=False, catalyst_age_hours=2,
                  prior_analysis_days=None, regime_alert=True, move_5d_pct=25)
    v, man, rd, d = computed("f", m)
    record("f_trigger_backed_exit", v == "DISCIPLINED" and d["rule"] == 1,
           "verdict=%s rule=%s" % (v, d.get("rule")))


def test_f_zone_preregistered_add():
    # rule 1b: a pre-registered zone firing on an ADD is DISCIPLINED even with
    # fomo_points 3 (catalyst <48h + move_5d >=10 + trades_7d >=3 -- the live
    # a live gate shape that would otherwise return FOMO-SUSPECT).
    m = f_markers(action_side="ADD", zone_preregistered=True, catalyst_age_hours=20,
                  move_5d_pct=14.1, trades_7d=3)
    v, man, rd, d = computed("f", m)
    ok = v == "DISCIPLINED" and d["rule"] == "1b" and d["fomo_points"] == 3 and man == []
    record("f_zone_preregistered_add", ok,
           "verdict=%s rule=%s points=%s" % (v, d.get("rule"), d.get("fomo_points")))


def test_f_zone_preregistered_trim_not_covered():
    # rule 1b covers ADD only; a TRIM with the same markers scores normally.
    m = f_markers(action_side="TRIM", zone_preregistered=True, catalyst_age_hours=20,
                  move_5d_pct=14.1, trades_7d=3)
    v, man, rd, d = computed("f", m)
    ok = v == "FOMO-SUSPECT" and d["rule"] == 3 and d["fomo_points"] == 3
    record("f_zone_preregistered_trim_not_covered", ok,
           "verdict=%s rule=%s points=%s" % (v, d.get("rule"), d.get("fomo_points")))


def test_f_zone_false_or_absent_unchanged():
    # false and absent must both leave pre-1b behavior byte-identical.
    m_false = f_markers(action_side="ADD", zone_preregistered=False,
                        catalyst_age_hours=20, move_5d_pct=14.1, trades_7d=3)
    m_absent = f_markers(action_side="ADD", catalyst_age_hours=20,
                         move_5d_pct=14.1, trades_7d=3)
    v1, _, _, d1 = computed("f", m_false)
    v2, _, _, d2 = computed("f", m_absent)
    ok = (v1 == v2 == "FOMO-SUSPECT" and d1["rule"] == d2["rule"] == 3
          and d1["fomo_points"] == d2["fomo_points"] == 3)
    record("f_zone_false_or_absent_unchanged", ok,
           "false=%s/%s absent=%s/%s" % (v1, d1.get("rule"), v2, d2.get("rule")))


def test_check_legacy_sheet_no_zone_marker(tmp):
    # backward compat: a sheet with no zone_preregistered key still validates
    # (the marker is optional-with-default-false under schema_version 1).
    m = f_markers()
    assert "zone_preregistered" not in m
    v, man, rd, d = computed("f", m)
    p = write_sheet(tmp, "gate-f-legacy.md", "f", m, v, man, rd)
    findings, comp = ge.check_sheet(p, RULES)
    record("check_legacy_sheet_no_zone_marker", findings == [],
           json.dumps(findings) if findings else "no findings")


def test_t_fired():
    v, man, rd, d = computed("t", t_markers())
    ok = v == "FIRED" and sorted(man) == sorted(
        ["status-floor-amber", "eod-row-trigger-action"]) and rd is not None
    record("t_fired", ok, "verdict=%s mandates=%s" % (v, man))


def test_t_notfired():
    v, man, rd, d = computed("t", t_markers(metric_condition_met=False))
    record("t_notfired", v == "NOT-FIRED" and man == [] and rd is None,
           "verdict=%s mandates=%s" % (v, man))


def test_t_insufficient():
    ev = [{"source": "sec.gov", "grade": "A", "date": "2026-06-25", "statement": "s1"}]
    v, man, rd, d = computed("t", t_markers(evidence=ev))
    record("t_insufficient", v == "INSUFFICIENT-EVIDENCE"
           and man == ["eod-row-evidence-collection"],
           "verdict=%s mandates=%s" % (v, man))


def test_t_counter():
    m = t_markers(consecutive_required=2, consecutive_count=1)
    v, man, rd, d = computed("t", m)
    record("t_counter_unsatisfied", v == "NOT-FIRED", "verdict=%s" % v)


def test_b_shipfirst():
    v, man, rd, d = computed("b", b_markers(overdue_eod_count=2))
    ok = v == "SHIP-FIRST" and sorted(man) == sorted(
        ["resolve-top-overdue-eod-first", "regate-after"])
    record("b_shipfirst", ok, "verdict=%s mandates=%s" % (v, man))


def test_b_justified_directive():
    m = b_markers(user_directive=True, size_class="L", overdue_eod_count=1)
    v, man, rd, d = computed("b", m)
    ok = (v == "BUILD-JUSTIFIED"
          and sorted(man) == sorted(["consumption-review-30d", "list-displaced-eod-rows"])
          and rd is not None)
    record("b_justified_directive", ok, "verdict=%s mandates=%s review=%s" % (v, man, rd))


def test_b_decline():
    m = b_markers(similar_organ="tools/consolidator.py", similar_organ_consumed_30d=False,
                  user_directive=True)
    v, man, rd, d = computed("b", m)
    record("b_decline_precedes_directive", v == "DECLINE" and d["rule"] == 1,
           "verdict=%s rule=%s" % (v, d.get("rule")))


def test_check_pass(tmp):
    m = f_markers()
    v, man, rd, d = computed("f", m)
    p = write_sheet(tmp, "gate-f-pass.md", "f", m, v, man, rd)
    findings, comp = ge.check_sheet(p, RULES)
    record("check_pass", findings == [], json.dumps(findings) if findings else "")


def test_check_verdict_mismatch(tmp):
    m = f_markers(tenure_days=3, held_position=False, catalyst_age_hours=6,
                  prior_analysis_days=None, regime_alert=True)
    p = write_sheet(tmp, "gate-f-mismatch.md", "f", m, "DISCIPLINED", [])
    findings, comp = ge.check_sheet(p, RULES)
    hit = any(f["dimension"] == "verdict" for f in findings)
    record("check_verdict_mismatch", hit, "findings=%d" % len(findings))


def test_check_missing_prov(tmp):
    m = f_markers()
    m["tenure_days"] = {"value": 94}  # no prov
    v = "DISCIPLINED"
    p = write_sheet(tmp, "gate-f-noprov.md", "f", m, v, [])
    findings, comp = ge.check_sheet(p, RULES)
    hit = any("tenure_days" in f["dimension"] for f in findings)
    record("check_missing_prov", hit, "findings=%d" % len(findings))


def test_check_bad_prov_path(tmp):
    m = f_markers()
    m["tenure_days"] = mk(94, prov="wiki/entities/tickers/NO-SUCH-TICKER-XYZQ.md")
    p = write_sheet(tmp, "gate-f-badprov.md", "f", m, "DISCIPLINED", [])
    findings, comp = ge.check_sheet(p, RULES)
    hit = any(f["dimension"] == "marker.tenure_days.prov" for f in findings)
    record("check_bad_prov_path", hit, "findings=%d" % len(findings))


def test_check_non_ascii(tmp):
    m = f_markers()
    v, man, rd, d = computed("f", m)
    p = write_sheet(tmp, "gate-f-ascii.md", "f", m, v, man, rd)
    raw = p.read_bytes() + "em\xe2\x80\x94dash\n".encode("latin-1")
    p.write_bytes(raw)
    findings, comp = ge.check_sheet(p, RULES)
    hit = any("ascii" in f["dimension"] for f in findings)
    record("check_non_ascii", hit, "findings=%d" % len(findings))


def test_goldens():
    goldens = []
    if GATES_DIR.exists():
        for p in sorted(GATES_DIR.glob("gate-*-*.md")):
            fm, err = ge.parse_frontmatter(ge.read_text(p))
            if fm and isinstance(fm.get("gate"), dict) and fm["gate"].get("golden") is True:
                goldens.append(p)
    if not goldens:
        record("goldens_integration", True, "SKIPPED: no golden sheets on disk yet")
        return
    bad = []
    for p in goldens:
        findings, comp = ge.check_sheet(p, RULES)
        if findings:
            bad.append("%s: %s" % (p.name, json.dumps(findings)))
    record("goldens_integration", not bad,
           ("%d golden(s) clean" % len(goldens)) if not bad else "; ".join(bad))


def test_calibrate_runs():
    try:
        report = ge.calibrate(date(2026, 6, 1), RULES)
        ok = all(k in report["gates"] for k in ("f", "t", "b"))
        record("calibrate_runs", ok,
               "f=%s t=%s b=%s" % tuple(report["gates"][k]["expected"] for k in ("f", "t", "b")))
    except Exception as exc:
        record("calibrate_runs", False, "exception: %s" % exc)


TESTS = {
    "f_blocked": test_f_blocked,
    "f_disciplined": test_f_disciplined,
    "f_suspect": test_f_suspect,
    "f_trigger_backed_exit": test_f_trigger_backed_exit,
    "f_zone_preregistered_add": test_f_zone_preregistered_add,
    "f_zone_preregistered_trim_not_covered": test_f_zone_preregistered_trim_not_covered,
    "f_zone_false_or_absent_unchanged": test_f_zone_false_or_absent_unchanged,
    "check_legacy_sheet_no_zone_marker": test_check_legacy_sheet_no_zone_marker,
    "t_fired": test_t_fired,
    "t_notfired": test_t_notfired,
    "t_insufficient": test_t_insufficient,
    "t_counter": test_t_counter,
    "b_shipfirst": test_b_shipfirst,
    "b_justified_directive": test_b_justified_directive,
    "b_decline": test_b_decline,
    "check_pass": test_check_pass,
    "check_verdict_mismatch": test_check_verdict_mismatch,
    "check_missing_prov": test_check_missing_prov,
    "check_bad_prov_path": test_check_bad_prov_path,
    "check_non_ascii": test_check_non_ascii,
    "goldens_integration": test_goldens,
    "calibrate_runs": test_calibrate_runs,
}
NEEDS_TMP = {"check_pass", "check_verdict_mismatch", "check_missing_prov",
             "check_bad_prov_path", "check_non_ascii",
             "check_legacy_sheet_no_zone_marker"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", default=None)
    args = ap.parse_args()
    names = [args.test] if args.test else list(TESTS)
    with tempfile.TemporaryDirectory() as tmp:
        for name in names:
            fn = TESTS.get(name)
            if fn is None:
                print("unknown test: %s" % name)
                return 1
            if name in NEEDS_TMP:
                fn(tmp)
            else:
                fn()
    failed = [n for n, ok, _ in RESULTS if not ok]
    print("\n%d/%d passed" % (len(RESULTS) - len(failed), len(RESULTS)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
