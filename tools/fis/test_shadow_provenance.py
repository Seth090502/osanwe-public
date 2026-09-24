#!/usr/bin/env python
# -*- coding: ascii -*-
"""Provenance gate regression suite for the shadow research pipeline.

Fixes and locks down F-01 (BLOCKING): the grade gate in shadow.py used to
test only "has the horizon expired relative to realized closes". It never
compared creation_ts to earliest_tradable or to the outcome window, so a
record written AFTER its entire outcome resolved was graded
indistinguishably from a genuine forecast.

That is how six records created 2026-08-26 with earliest_tradable
2026-07-02 were graded 15 seconds later and became "prospective evidence"
for a window that had closed five weeks earlier.

The rule itself is NOT reimplemented here or in shadow.py: both use
scheduler.provenance_decision(). Two copies of a temporal rule drift, and
drift between them is itself a defect.

Run:  python tools/fis/test_shadow_provenance.py
Exit: 0 if all hold, 1 otherwise.
"""

import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import shadow  # noqa: E402
import scheduler  # noqa: E402

RESULTS = []


def check(cid, ok, detail=""):
    RESULTS.append((cid, bool(ok), detail))
    print("%-5s %-48s %s" % ("PASS" if ok else "FAIL", cid, detail))
    return ok


def mk(creation_ts, earliest_tradable, **extra):
    rec = {
        "record_type": "prediction",
        "cohort_id": "TEST",
        "creation_ts": creation_ts,
        "info_cutoff": earliest_tradable,
        "earliest_tradable": earliest_tradable,
        "horizon_days": 10,
    }
    rec.update(extra)
    return rec


def main():
    # ------------------------------------------------------------------
    # 1. The discriminator: created before vs after its own tradable open
    # ------------------------------------------------------------------
    genuine = mk("2026-09-01T12:00:00Z", "2026-09-02")
    backfill = mk("2026-08-26T04:44:46Z", "2026-07-02")

    pg = shadow.classify_provenance(genuine)
    pb = shadow.classify_provenance(backfill)

    check("genuine_forecast_is_prospective",
          pg["prospective_evidence"] is True
          and pg["provenance_mode"] == scheduler.PROSPECTIVE,
          "%s / %s" % (pg["provenance_mode"], pg["rule"]))
    check("backfill_is_not_prospective",
          pb["prospective_evidence"] is False
          and pb["provenance_mode"] == scheduler.RETROSPECTIVE_BACKFILL,
          "%s / %s" % (pb["provenance_mode"], pb["rule"]))

    # ------------------------------------------------------------------
    # 2. The six real contaminated records must all classify as backfill
    # ------------------------------------------------------------------
    real = os.path.join(REPO, "Efforts", "osanwe-v2-overhaul", "_work",
                        "fis-data", "shadow-predictions.jsonl")
    if os.path.exists(real):
        recs = [json.loads(l) for l in open(real, encoding="ascii")
                if l.strip()]
        verdicts = [shadow.classify_provenance(r) for r in recs]
        n_retro = sum(1 for v in verdicts
                      if v["provenance_mode"] == scheduler.RETROSPECTIVE_BACKFILL)
        check("all_existing_records_classify_as_backfill",
              n_retro == len(recs),
              "%d/%d RETROSPECTIVE_BACKFILL (0 prospective records exist)"
              % (n_retro, len(recs)))
        check("no_record_is_prospective_evidence",
              not any(shadow.is_prospective_evidence(r) for r in recs),
              "0 of %d records carry prospective_evidence=True" % len(recs))
    else:
        check("all_existing_records_classify_as_backfill", False,
              "shadow-predictions.jsonl not found at %s" % real)

    # ------------------------------------------------------------------
    # 3. Fail-closed: missing / malformed temporal fields
    # ------------------------------------------------------------------
    for label, rec in (("no_creation_ts", mk(None, "2026-09-02")),
                       ("no_earliest_tradable", mk("2026-09-01T12:00:00Z", None))):
        v = shadow.classify_provenance(rec)
        check("fail_closed_%s" % label,
              v["prospective_evidence"] is False
              and v["rule"] == "missing_temporal_fields",
              v["rule"])

    # Unknown is NOT prospective: a record predating the control has no
    # provenance_mode and must not inherit prospective status.
    check("unstamped_record_is_not_prospective",
          shadow.is_prospective_evidence(mk("2026-09-01T12:00:00Z", "2026-09-02"))
          is False,
          "record with no provenance_mode is treated as non-prospective")
    check("non_dict_is_not_prospective",
          shadow.is_prospective_evidence("not-a-record") is False
          and shadow.is_prospective_evidence(None) is False,
          "fails closed on non-dict input")

    # ------------------------------------------------------------------
    # 4. Tamper detection: stored mode must match re-derived mode
    # ------------------------------------------------------------------
    forged = mk("2026-08-26T04:44:46Z", "2026-07-02")
    forged["provenance_mode"] = scheduler.PROSPECTIVE
    forged["prospective_evidence"] = True
    v = shadow.classify_provenance(forged)
    check("forged_prospective_stamp_is_overruled",
          v["prospective_evidence"] is False,
          "re-derivation overrules a forged PROSPECTIVE stamp")
    check("stored_vs_derived_mismatch_detected",
          forged["provenance_mode"] != v["provenance_mode"],
          "stored=%s vs derived=%s -> grading refuses"
          % (forged["provenance_mode"], v["provenance_mode"]))

    # ------------------------------------------------------------------
    # 5. The filter has no override and the module refuses to grow one
    # ------------------------------------------------------------------
    code = shadow.prospective_grades.__code__
    args = code.co_varnames[:code.co_argcount]
    check("filter_has_no_override_parameter",
          args == ("grades",) and not any(
              t in a.lower() for a in args
              for t in ("include", "allow", "force", "override")),
          "prospective_grades%s" % (args,))

    clean, hits = shadow.shadow_no_backfill_escape_hatch()
    check("no_escape_hatch_in_module", clean, "hits: %s" % (hits or "none"))

    # ------------------------------------------------------------------
    # 6. Aggregate excludes backfill permanently
    # ------------------------------------------------------------------
    mixed = [dict(genuine, **shadow.classify_provenance(genuine)),
             dict(backfill, **shadow.classify_provenance(backfill))]
    agg = shadow.aggregate_prospective(mixed, min_samples=1)
    check("aggregate_excludes_backfill",
          agg["records_prospective"] == 1
          and agg["records_backfill_excluded"] == 1,
          "prospective=%d excluded=%d total=%d"
          % (agg["records_prospective"], agg["records_backfill_excluded"],
             agg["records_total"]))
    check("aggregate_declares_no_override_policy",
          agg.get("backfill_policy") == "EXCLUDED_PERMANENTLY_NO_OVERRIDE",
          str(agg.get("backfill_policy")))

    # ------------------------------------------------------------------
    # 7. Clock injection (F-04)
    # ------------------------------------------------------------------
    from datetime import datetime, timezone, timedelta

    fixed = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)
    check("clock_is_injectable",
          shadow.utc_now_iso(lambda: fixed) == "2026-09-01T12:00:00Z",
          shadow.utc_now_iso(lambda: fixed))
    try:
        shadow.require_utc_z("2026-09-01T12:00:00")
        check("naive_timestamp_rejected", False, "no error raised")
    except ValueError:
        check("naive_timestamp_rejected", True,
              "rejects timestamp without trailing Z")
    try:
        shadow.require_utc_z(datetime(2026, 9, 1, 12, 0, 0))
        check("non_string_timestamp_rejected", False, "no error raised")
    except ValueError:
        check("non_string_timestamp_rejected", True, "rejects datetime object")

    # ------------------------------------------------------------------
    # 8. Monotonicity: the rule may only get stricter, never looser
    # ------------------------------------------------------------------
    stricter = []
    for day in range(1, 10):
        r = mk("2026-09-1%dT12:00:00Z" % day, "2026-09-05")
        stricter.append(shadow.classify_provenance(r)["prospective_evidence"])
    check("rule_is_monotone_in_creation_time",
          stricter == sorted(stricter, reverse=True),
          "once retrospective, never prospective again: %s"
          % "".join("P" if s else "R" for s in stricter))

    n_fail = sum(1 for _, ok, _ in RESULTS if not ok)
    print("")
    print("=" * 66)
    print("PASSED: %d   FAILED: %d" % (len(RESULTS) - n_fail, n_fail))
    print("=" * 66)
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
