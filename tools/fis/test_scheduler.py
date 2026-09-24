"""Exit-gated tests for tools/fis/scheduler.py (W2 -- scheduler battery).

Plain-assert harness in the FIS house style. Standard library only, ASCII
only, zero network. All time comes from an injected FakeClock; all state
lives in a temp dir. The real production shadow log is never touched.

Run: python tools/fis/test_scheduler.py   (exit 0 = pass, nonzero = fail)
"""

import json
import os
import random
import shutil
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import scheduler  # noqa: E402

FAILURES = []
PASSES = []

UTC = timezone.utc
_ENVS = []


def check(name, cond, detail=""):
    if cond:
        PASSES.append(name)
        print("PASS %s" % name)
    else:
        FAILURES.append((name, detail))
        print("FAIL %s -- %s" % (name, detail))


def iso(dt):
    return scheduler.iso_z(dt)


# --------------------------------------------------------------------------
# Test harness: a fully synthetic, deterministic scheduler environment
# --------------------------------------------------------------------------

class Env(object):
    def __init__(self, start="2026-08-12T21:00:00Z", config=None,
                 drift_extra=None, seed=11):
        self.tmp = tempfile.mkdtemp(prefix="fis-scheduler-test-")
        self.state = scheduler.SchedulerState(
            os.path.join(self.tmp, "scheduler-state"))
        self.clock = scheduler.FakeClock(start)
        self.cal = scheduler.MarketCalendar()
        self.cfg = config or scheduler.SchedulerConfig()
        self.provider = scheduler.SyntheticProvider(self.clock)
        self.engine_stub = drift_extra
        self.sessions = self.cal.trading_days(date(2026, 1, 2),
                                              date(2027, 12, 31))
        self._seed_prices()
        sources = None
        if drift_extra is not None:
            sources = {"scheduler.py": scheduler.MODULE_PATH,
                       "engine_stub.py": drift_extra}
        self.sched = scheduler.Scheduler(
            self.state, self.cfg, self.clock, self.provider, self.cal,
            rng=random.Random(seed), drift_sources=sources)
        _ENVS.append(self)

    def _seed_prices(self):
        for i, cohort in enumerate(self.cfg.cohorts):
            rnd = random.Random(7 + i)
            px = 100.0 + i
            for d in self.sessions:
                px *= (1.0 + 0.0004 + rnd.uniform(-0.002, 0.002))
                self.provider.seed(cohort, d, round(px, 6))

    def ready(self):
        """Install a clean drift freeze so ticks can proceed."""
        return self.sched.drift.freeze(self.clock)

    def tick(self):
        return self.sched.run_tick()

    def tick_until(self, target):
        self.clock.set(target)
        return self.sched.run_tick()

    def close_series(self, cohort):
        out = {}
        for d in self.sessions:
            q = self.sched._safe_quote(cohort, d)
            out[d] = q["close"] if q else None
        return out

    def cleanup(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


def main():
    # ==================================================================
    # A. Clock and timestamp discipline
    # ==================================================================
    t = datetime(2026, 8, 12, 21, 0, 0, tzinfo=UTC)
    check("time.iso_z_format", iso(t) == "2026-08-12T21:00:00Z", iso(t))
    check("time.parse_roundtrip",
          scheduler.parse_iso_z(iso(t)) == t)

    naive = datetime(2026, 8, 12, 21, 0, 0)
    raised = False
    try:
        iso(naive)
    except ValueError:
        raised = True
    check("time.naive_rejected", raised)

    check("time.is_iso_z_rejects_missing_Z",
          not scheduler.is_iso_z("2026-08-12T21:00:00"))
    check("time.is_iso_z_rejects_space_separator",
          not scheduler.is_iso_z("2026-08-12 21:00:00Z"))

    fc = scheduler.FakeClock("2026-08-12T21:00:00Z")
    fc.sleep(3)
    check("clock.fake_sleep_advances",
          iso(fc.now()) == "2026-08-12T21:00:03Z", iso(fc.now()))
    check("clock.fake_sleep_recorded", fc.sleeps == [3], str(fc.sleeps))

    eastern = t.astimezone(timezone(timedelta(hours=-4)))
    check("time.require_utc_normalizes",
          scheduler.require_utc(eastern) == t)

    # ==================================================================
    # B. Market calendar
    # ==================================================================
    cal = scheduler.MarketCalendar()
    check("cal.weekend_not_trading",
          not cal.is_trading_day("2026-08-15")
          and not cal.is_trading_day("2026-08-16"))
    check("cal.weekday_trading", cal.is_trading_day("2026-08-12"))
    check("cal.july3_2026_is_holiday",
          cal.is_holiday("2026-07-03")
          and cal.holiday_name("2026-07-03") == "Independence Day (observed)")
    check("cal.june19_2026_is_holiday", cal.is_holiday("2026-06-19"))
    check("cal.nov27_2026_trades_early",
          cal.is_trading_day("2026-11-27")
          and cal.is_early_close("2026-11-27"))
    check("cal.next_session_skips_holiday_and_weekend",
          cal.next_trading_day("2026-07-02") == date(2026, 7, 6),
          str(cal.next_trading_day("2026-07-02")))

    y2026 = cal.trading_days(date(2026, 1, 1), date(2026, 12, 31))
    y2027 = cal.trading_days(date(2027, 1, 1), date(2027, 12, 31))
    check("cal.2026_session_count", len(y2026) == 251, str(len(y2026)))
    check("cal.2027_session_count", len(y2027) == 251, str(len(y2027)))
    check("cal.no_weekend_or_holiday_sessions",
          not [d for d in y2026 + y2027
               if d.weekday() >= 5 or cal.is_holiday(d)])
    check("cal.nth_trading_day_10",
          cal.nth_trading_day("2026-08-13", 10) == date(2026, 8, 27),
          str(cal.nth_trading_day("2026-08-13", 10)))

    raised = False
    try:
        cal.is_trading_day("2030-06-03")
    except scheduler.CalendarRangeError:
        raised = True
    check("cal.unsupported_year_fails_closed", raised)

    # ==================================================================
    # C. DST
    # ==================================================================
    check("dst.start_2026", iso(scheduler.dst_start_utc(2026))
          == "2026-03-08T07:00:00Z", iso(scheduler.dst_start_utc(2026)))
    check("dst.end_2026", iso(scheduler.dst_end_utc(2026))
          == "2026-11-01T06:00:00Z", iso(scheduler.dst_end_utc(2026)))
    check("dst.start_2027", iso(scheduler.dst_start_utc(2027))
          == "2027-03-14T07:00:00Z", iso(scheduler.dst_start_utc(2027)))
    check("dst.end_2027", iso(scheduler.dst_end_utc(2027))
          == "2027-11-07T06:00:00Z", iso(scheduler.dst_end_utc(2027)))

    jan = scheduler.parse_iso_z("2026-01-15T12:00:00Z")
    jul = scheduler.parse_iso_z("2026-07-15T12:00:00Z")
    check("dst.january_is_est",
          scheduler.eastern_offset(jan) == scheduler.EST)
    check("dst.july_is_edt",
          scheduler.eastern_offset(jul) == scheduler.EDT)

    before = scheduler.parse_iso_z("2026-03-08T06:59:59Z")
    at = scheduler.parse_iso_z("2026-03-08T07:00:00Z")
    check("dst.spring_forward_boundary",
          scheduler.eastern_offset(before) == scheduler.EST
          and scheduler.eastern_offset(at) == scheduler.EDT)

    before_fb = scheduler.parse_iso_z("2026-11-01T05:59:59Z")
    at_fb = scheduler.parse_iso_z("2026-11-01T06:00:00Z")
    check("dst.fall_back_boundary",
          scheduler.eastern_offset(before_fb) == scheduler.EDT
          and scheduler.eastern_offset(at_fb) == scheduler.EST)

    skipped, note = scheduler.eastern_to_utc(
        datetime(2026, 3, 8, 2, 30))
    check("dst.nonexistent_local_time_snapped",
          note == "nonexistent_snapped"
          and iso(skipped) == "2026-03-08T07:00:00Z",
          "%s %s" % (iso(skipped), note))

    amb, amb_note = scheduler.eastern_to_utc(datetime(2026, 11, 1, 1, 30))
    check("dst.ambiguous_local_time_resolved",
          amb_note == "ambiguous_first"
          and iso(amb) == "2026-11-01T05:30:00Z",
          "%s %s" % (iso(amb), amb_note))

    check("dst.close_is_20z_in_edt",
          iso(cal.market_close_utc("2026-08-12")) == "2026-08-12T20:00:00Z",
          iso(cal.market_close_utc("2026-08-12")))
    check("dst.close_is_21z_in_est",
          iso(cal.market_close_utc("2026-01-15")) == "2026-01-15T21:00:00Z",
          iso(cal.market_close_utc("2026-01-15")))
    check("dst.early_close_is_18z_in_est",
          iso(cal.market_close_utc("2026-11-27")) == "2026-11-27T18:00:00Z",
          iso(cal.market_close_utc("2026-11-27")))

    # ==================================================================
    # D. Provenance and backfill restriction -- THE KEY CONTROL
    # ==================================================================
    audit = scheduler.provenance_decision(
        scheduler.parse_iso_z("2026-08-26T04:44:46Z"), "2026-07-02")
    check("prov.audit_case_is_retro",
          audit["provenance_mode"] == scheduler.RETROSPECTIVE_BACKFILL
          and audit["prospective_evidence"] is False,
          json.dumps(audit))
    check("prov.audit_case_cites_rule",
          audit["rule"] == "creation_date_after_earliest_tradable")

    good = scheduler.provenance_decision(
        scheduler.parse_iso_z("2026-08-11T21:00:00Z"), "2026-08-12")
    check("prov.genuine_forecast_is_prospective",
          good["provenance_mode"] == scheduler.PROSPECTIVE
          and good["prospective_evidence"] is True, json.dumps(good))

    after_close = scheduler.provenance_decision(
        scheduler.parse_iso_z("2026-08-12T20:30:00Z"), "2026-08-12")
    check("prov.same_day_after_close_is_retro",
          after_close["provenance_mode"] == scheduler.RETROSPECTIVE_BACKFILL,
          json.dumps(after_close))

    before_close = scheduler.provenance_decision(
        scheduler.parse_iso_z("2026-08-12T13:30:00Z"), "2026-08-12")
    check("prov.same_day_before_close_is_prospective",
          before_close["provenance_mode"] == scheduler.PROSPECTIVE,
          json.dumps(before_close))

    check("prov.unlabeled_record_not_eligible",
          not scheduler.is_prospective_evidence({"provenance_mode": "MAYBE"}))
    check("prov.field_alone_is_not_enough",
          not scheduler.is_prospective_evidence(
              {"provenance_mode": scheduler.PROSPECTIVE,
               "prospective_evidence": False}))

    clean, hits = scheduler.verify_no_backfill_escape_hatch()
    check("prov.no_escape_hatch_in_source", clean, "tokens: %s" % hits)

    mixed = [
        {"record_hash": "p1", "cohort_id": "SPY_BH",
         "provenance_mode": scheduler.PROSPECTIVE,
         "prospective_evidence": True, "excess_vs_benchmark": 0.01,
         "direction_accuracy": 1.0, "earliest_tradable": "2026-08-13",
         "creation_ts": "2026-08-11T21:00:00Z"},
        {"record_hash": "b1", "cohort_id": "SPY_BH",
         "provenance_mode": scheduler.RETROSPECTIVE_BACKFILL,
         "prospective_evidence": False, "excess_vs_benchmark": 0.99,
         "direction_accuracy": 1.0, "earliest_tradable": "2026-07-02",
         "creation_ts": "2026-08-26T04:44:46Z"},
    ]
    agg = scheduler.aggregate_prospective(mixed)
    check("agg.backfill_excluded",
          agg["records_prospective"] == 1
          and agg["records_backfill_excluded"] == 1,
          json.dumps({k: v for k, v in agg.items() if k != "excluded"}))
    check("agg.backfill_does_not_move_mean",
          agg["mean_excess_vs_benchmark"] == 0.01,
          str(agg["mean_excess_vs_benchmark"]))
    check("agg.excluded_marked_permanent",
          agg["excluded"][0]["excluded_permanently"] is True)
    check("agg.summary_refused_below_min_samples",
          agg["claims_allowed"] is False
          and agg["verdict"].startswith("SUMMARY REFUSED"))

    # BEHAVIOUR CHANGE (W9-A6-01, CRITICAL). These 60 records used to carry
    # ONLY the provenance stamp, with no creation_ts and no
    # earliest_tradable, and were counted as prospective on the strength of
    # the stamp alone. That is exactly the laundering path: two stored
    # booleans were sufficient, and no timestamp was ever checked.
    #
    # `is_prospective_evidence` now re-derives from the record's own
    # timestamps, so this fixture -- which has none -- is excluded. The
    # fixture is updated to carry real timestamps, and a NEW check asserts
    # that a record with no timestamps is excluded.
    many = [{"record_hash": "k%d" % i,
             "provenance_mode": scheduler.PROSPECTIVE,
             "prospective_evidence": True,
             "excess_vs_benchmark": 0.001,
             "direction_accuracy": 1.0,
             "creation_ts": "2026-08-11T21:00:00Z",
             "earliest_tradable": "2026-08-13"} for i in range(60)]
    agg60 = scheduler.aggregate_prospective(many)
    check("agg.claims_allowed_at_min_samples",
          agg60["claims_allowed"] is True and agg60["records_prospective"]
          == 60, json.dumps({k: v for k, v in agg60.items()
                             if k != "excluded"}))

    # Fail-closed: a stamp with no timestamps behind it is not evidence.
    untimed = [{"record_hash": "u%d" % i,
                "provenance_mode": scheduler.PROSPECTIVE,
                "prospective_evidence": True,
                "excess_vs_benchmark": 0.001,
                "direction_accuracy": 1.0} for i in range(60)]
    aggu = scheduler.aggregate_prospective(untimed)
    check("agg.unverifiable_stamp_is_excluded",
          aggu["records_prospective"] == 0
          and aggu["records_backfill_excluded"] == 60
          and aggu["claims_allowed"] is False,
          "stamped PROSPECTIVE with no timestamps -> %d prospective"
          % aggu["records_prospective"])

    # A forged stamp on a genuinely retrospective record must be overruled
    # on the READ path, not only at grading time.
    forged = [{"record_hash": "f0",
               "provenance_mode": scheduler.PROSPECTIVE,
               "prospective_evidence": True,
               "creation_ts": "2026-08-26T04:44:46Z",
               "earliest_tradable": "2026-07-02",
               "excess_vs_benchmark": 0.50,
               "direction_accuracy": 1.0}]
    aggf = scheduler.aggregate_prospective(forged)
    check("agg.forged_stamp_overruled_on_read",
          aggf["records_prospective"] == 0
          and aggf["records_backfill_excluded"] == 1,
          "created 2026-08-26 for a 2026-07-02 window, stamped PROSPECTIVE "
          "-> %d prospective" % aggf["records_prospective"])

    raised = False
    try:
        scheduler.aggregate_prospective(mixed, **{"include_backfill": True})
    except TypeError:
        raised = True
    check("agg.no_override_argument_exists", raised)

    # ==================================================================
    # E. Duplicate suppression / idempotency
    # ==================================================================
    env = Env()
    env.ready()
    m1 = env.tick()
    n_pred_1 = len(env.state.predictions())
    check("dup.first_tick_writes_one_per_cohort",
          n_pred_1 == len(env.cfg.cohorts), str(n_pred_1))

    m2 = env.tick()
    n_pred_2 = len(env.state.predictions())
    check("dup.second_identical_tick_writes_nothing",
          n_pred_2 == n_pred_1, "%d vs %d" % (n_pred_2, n_pred_1))
    check("dup.second_tick_reports_skips",
          m2["tasks"][0]["detail"]["skipped_duplicates"] == n_pred_1
          and m2["tasks"][0]["detail"]["written"] == 0,
          json.dumps(m2["tasks"][0]["detail"]))

    env.clock.advance(days=20)
    env.cfg = scheduler.SchedulerConfig(max_missed_runs=99)
    env.sched.cfg = env.cfg
    m3 = env.tick()
    n_grades = len(env.state.grades())
    check("dup.grade_written_once_horizon_expired",
          n_grades == len(env.cfg.cohorts), str(n_grades))

    m4 = env.tick()
    check("dup.repeat_tick_does_not_duplicate_grades",
          len(env.state.grades()) == n_grades,
          "%d vs %d" % (len(env.state.grades()), n_grades))
    check("dup.idempotency_ledger_populated",
          len(env.state.idempotency()) >= n_pred_1 + n_grades,
          str(len(env.state.idempotency())))

    # ==================================================================
    # F. Missing / late / stale data
    # ==================================================================
    now = scheduler.parse_iso_z("2026-08-12T21:00:00Z")
    expected = cal.market_close_utc("2026-08-12")

    check("data.missing_classified",
          scheduler.classify_quote(None, now)["state"] == scheduler.MISSING)

    stale_q = scheduler.Quote("SPY_BH", "2026-08-10", 100.0,
                              now - timedelta(days=3))
    stale = scheduler.classify_quote(stale_q, now, expected_ts=expected)
    check("data.stale_blocked",
          stale["state"] == scheduler.STALE and stale["accepted"] is False,
          json.dumps(stale))

    late_q = scheduler.Quote("SPY_BH", "2026-08-12", 100.0,
                             expected + timedelta(seconds=3600))
    late = scheduler.classify_quote(
        late_q, now, expected_ts=expected,
        sla_seconds=env.cfg.freshness_sla_seconds)
    check("data.late_accepted_but_marked",
          late["state"] == scheduler.LATE and late["accepted"] is True,
          json.dumps(late))

    fresh_q = scheduler.Quote("SPY_BH", "2026-08-12", 100.0, expected)
    fresh = scheduler.classify_quote(fresh_q, now, expected_ts=expected)
    check("data.fresh_classified",
          fresh["state"] == scheduler.FRESH, json.dumps(fresh))

    # Arriving one second past the expected time is LATE, not FRESH: the
    # default late grace is zero.
    edge_q = scheduler.Quote("SPY_BH", "2026-08-12", 100.0,
                             expected + timedelta(seconds=1))
    check("data.one_second_late_is_late",
          scheduler.classify_quote(edge_q, now,
                                   expected_ts=expected)["state"]
          == scheduler.LATE)

    fc2 = scheduler.FakeClock("2026-08-12T21:00:00Z")
    cfg2 = scheduler.SchedulerConfig()
    missing_inputs = dict((c, {"close": None, "state": scheduler.MISSING,
                               "reason": "no observation",
                               "availability_ts": None})
                          for c in cfg2.cohorts)
    rec_missing = scheduler.build_prediction(
        fc2, cal, cfg2, "SPY_BH", "2026-08-12", "2026-08-13",
        missing_inputs, "ds", "dh", "run-missing")
    check("data.missing_input_abstains",
          rec_missing["abstention"] is True
          and rec_missing["confidence"] is None
          and rec_missing["forecast_distribution"] is None,
          json.dumps({k: rec_missing[k] for k in
                      ("abstention", "confidence",
                       "forecast_distribution")}))

    stale_inputs = dict((c, {"close": 100.0, "state": scheduler.STALE,
                             "reason": "too old",
                             "availability_ts": iso(now)})
                        for c in cfg2.cohorts)
    rec_stale = scheduler.build_prediction(
        fc2, cal, cfg2, "SPY_BH", "2026-08-12", "2026-08-13",
        stale_inputs, "ds", "dh", "run-stale")
    check("data.stale_input_abstains",
          rec_stale["abstention"] is True
          and rec_stale["confidence"] is None,
          json.dumps({k: rec_stale[k] for k in ("abstention",
                                                "confidence")}))

    late_inputs = dict((c, {"close": 100.0, "state": scheduler.LATE,
                            "reason": "arrived late",
                            "availability_ts": iso(now)})
                       for c in cfg2.cohorts)
    rec_late = scheduler.build_prediction(
        fc2, cal, cfg2, "SPY_BH", "2026-08-12", "2026-08-13",
        late_inputs, "ds", "dh", "run-late")
    check("data.late_input_accepted_and_marked",
          rec_late["abstention"] is False
          and rec_late["confidence"] is not None
          and rec_late["forecast_distribution"] is not None
          and any("LATE" in n for n in rec_late["notes"]),
          json.dumps(rec_late["notes"]))

    # An abstaining parent must never yield a grade.
    env_a = Env()
    env_a.ready()
    env_a.provider.add_missing("SPY_BH", "2026-08-12")
    for cohort in env_a.cfg.cohorts:
        env_a.provider.add_missing(cohort, "2026-08-12")
    env_a.tick()
    env_a.clock.advance(days=20)
    env_a.cfg = scheduler.SchedulerConfig(max_missed_runs=99)
    env_a.sched.cfg = env_a.cfg
    env_a.tick()
    check("data.abstained_parent_never_graded",
          len(env_a.state.grades()) == 0,
          "%d grades from %d predictions"
          % (len(env_a.state.grades()), len(env_a.state.predictions())))

    # ==================================================================
    # G. Provider outages, retries, dead-letter
    # ==================================================================
    env_o = Env()
    env_o.ready()
    env_o.provider.add_outage(env_o.clock.now(),
                              env_o.clock.now() + timedelta(hours=1))
    raised_cls = None
    try:
        env_o.provider.fetch_close("SPY_BH", "2026-08-12")
    except scheduler.ProviderError as exc:
        raised_cls = exc.error_class
    check("outage.typed_error",
          raised_cls == "PROVIDER_OUTAGE", str(raised_cls))

    # Retry succeeds once the outage clears mid-backoff.
    env_r = Env()
    env_r.ready()
    t0 = env_r.clock.now()
    env_r.provider.add_outage(t0, t0 + timedelta(seconds=5))
    rng = random.Random(5)
    outcome = scheduler.run_with_retry(
        lambda: env_r.provider.fetch_close("SPY_BH", "2026-08-12"),
        scheduler.RetryPolicy(base_seconds=2.0, multiplier=2.0),
        env_r.clock, rng, task="fetch")
    check("retry.recovers_when_outage_clears",
          outcome.ok is True and outcome.attempts == 3
          and len(outcome.delays) == 2,
          json.dumps(outcome.as_dict()))

    # Non-retryable failure: no backoff consumed.
    env_n = Env()
    calls = {"n": 0}

    def boom():
        calls["n"] += 1
        raise scheduler.ProviderDataMissing("field absent")

    raised = False
    try:
        scheduler.run_with_retry(
            boom, scheduler.RetryPolicy(), env_n.clock,
            random.Random(1), task="nonretryable")
    except scheduler.DeadLetterError:
        raised = True
    check("retry.non_retryable_fails_fast",
          raised and calls["n"] == 1 and env_n.clock.sleeps == [],
          "calls=%d sleeps=%s" % (calls["n"], env_n.clock.sleeps))

    # Bounded, increasing, capped backoff.
    pol = scheduler.RetryPolicy(base_seconds=2.0, multiplier=2.0,
                                max_seconds=60.0)
    rng_a = random.Random(99)
    rng_b = random.Random(99)
    d_a = [scheduler.backoff_delay(i, pol, rng_a) for i in range(1, 9)]
    d_b = [scheduler.backoff_delay(i, pol, rng_b) for i in range(1, 9)]
    check("retry.backoff_deterministic_for_seed", d_a == d_b, str(d_a))
    check("retry.backoff_increasing_then_capped",
          d_a[0] < d_a[1] < d_a[2] and max(d_a) <= 60.0 * 1.25,
          str(d_a))
    check("retry.backoff_has_jitter",
          any(d != [2.0, 4.0, 8.0, 16.0, 32.0, 60.0, 60.0, 60.0][i]
              for i, d in enumerate(d_a)), str(d_a))

    # Exhaustion -> dead letter on disk.
    env_d = Env()
    env_d.ready()
    env_d.provider.add_outage(env_d.clock.now() - timedelta(hours=1),
                              env_d.clock.now() + timedelta(hours=48))
    md = env_d.tick()
    check("outage.exhaustion_dead_letters",
          len(env_d.state.dead_letters()) == len(env_d.cfg.cohorts),
          str(env_d.state.dead_letters()))
    check("outage.degraded_mode_reported",
          md["degraded_mode"] is True, json.dumps(md["status"]))
    check("outage.no_grades_from_missing_inputs",
          len(env_d.state.grades()) == 0,
          str(len(env_d.state.grades())))
    check("outage.alert_emitted",
          any(a["alert_code"] == "SCHED.PROVIDER_OUTAGE"
              for a in env_d.state.alerts()))
    check("outage.dead_letter_alert_emitted",
          any(a["alert_code"] == "SCHED.DEAD_LETTER"
              for a in env_d.state.alerts()))

    # ==================================================================
    # H. Code-drift refusal
    # ==================================================================
    stub = os.path.join(tempfile.mkdtemp(prefix="fis-drift-"), "engine.py")
    with open(stub, "w", encoding="ascii") as fh:
        fh.write("ENGINE VERSION 1\n")
    env_f = Env(drift_extra=stub)

    pre = env_f.sched.drift.check()
    check("drift.no_freeze_blocks_grading",
          pre["status"] == scheduler.DRIFT_NO_FREEZE
          and pre["grading_allowed"] is False, json.dumps(pre["status"]))
    m_nf = env_f.tick()
    check("drift.tick_refused_without_freeze",
          m_nf["status"] == scheduler.STATUS_DRIFT_REFUSED
          and len(env_f.state.predictions()) == 0,
          m_nf["status"])

    env_f.ready()
    check("drift.clean_after_freeze",
          env_f.sched.drift.check()["status"] == scheduler.DRIFT_CLEAN)
    m_ok = env_f.tick()
    check("drift.tick_proceeds_when_clean",
          m_ok["status"] == scheduler.STATUS_OK
          and len(env_f.state.predictions()) == len(env_f.cfg.cohorts),
          m_ok["status"])

    with open(stub, "w", encoding="ascii") as fh:
        fh.write("ENGINE VERSION 2\n")
    drifted = env_f.sched.drift.check()
    check("drift.detects_engine_change",
          drifted["status"] == scheduler.DRIFT_CHANGED
          and "engine_stub.py" in drifted["changed_keys"],
          json.dumps(drifted["changed_keys"]))
    check("drift.grading_disallowed_when_drifted",
          drifted["grading_allowed"] is False)

    m_dr = env_f.tick()
    check("drift.tick_refused_when_drifted",
          m_dr["status"] == scheduler.STATUS_DRIFT_REFUSED, m_dr["status"])
    check("drift.alert_emitted",
          any(a["alert_code"] == "SCHED.DRIFT_REFUSED"
              for a in env_f.state.alerts()))

    parent = env_f.state.predictions()[0]
    raised = False
    try:
        scheduler.grade_prediction(
            env_f.clock, env_f.cal, env_f.cfg, parent,
            {parent["record_hash"]: parent}, {}, env_f.sessions, None,
            "run-drift", drifted)
    except scheduler.DriftRefusal:
        raised = True
    check("drift.grade_prediction_refuses", raised)

    # ==================================================================
    # I. Missed-run detection and RESTRICTED recovery
    # ==================================================================
    env_m = Env()
    env_m.ready()
    env_m.tick()
    check("missed.none_when_current",
          scheduler.detect_missed_slots(env_m.state, env_m.cal,
                                        env_m.clock, env_m.cfg) == [])

    env_m.clock.set("2026-08-17T21:00:00Z")
    missed = scheduler.detect_missed_slots(env_m.state, env_m.cal,
                                           env_m.clock, env_m.cfg)
    check("missed.detected_after_gap",
          [d.isoformat() for d in missed] == ["2026-08-13", "2026-08-14"],
          str([d.isoformat() for d in missed]))

    mm = env_m.tick()
    recovery_task = [t for t in mm["tasks"] if t["task"] == "recovery"][0]
    recovered = [p for p in env_m.state.predictions()
                 if p.get("recovery") is True]
    check("missed.recovery_writes_records",
          len(recovered) == len(missed) * len(env_m.cfg.cohorts),
          "%d recovered" % len(recovered))
    check("missed.recovery_all_labeled_retro",
          all(p["provenance_mode"] == scheduler.RETROSPECTIVE_BACKFILL
              for p in recovered),
          str(sorted(set(p["provenance_mode"] for p in recovered))))
    check("missed.recovery_is_prospective_free",
          recovery_task["detail"]["prospective"] == 0,
          json.dumps(recovery_task["detail"]))
    check("missed.recovery_excluded_from_prospective_agg",
          scheduler.aggregate_prospective(env_m.state.predictions())
          ["records_backfill_excluded"] == len(recovered),
          str(scheduler.aggregate_prospective(env_m.state.predictions())
              ["records_backfill_excluded"]))
    check("missed.alert_emitted",
          any(a["alert_code"] == "SCHED.MISSED_RUN"
              for a in env_m.state.alerts()))

    env_l = Env(config=scheduler.SchedulerConfig(max_missed_runs=1))
    env_l.ready()
    env_l.tick()
    env_l.clock.set("2026-08-17T21:00:00Z")
    ml = env_l.tick()
    rt = [t for t in ml["tasks"] if t["task"] == "recovery"][0]
    check("missed.over_limit_refuses_automatic_recovery",
          rt["status"] == "REFUSED"
          and rt["detail"]["error_class"] == "MISSED_RUN_LIMIT",
          json.dumps(rt["detail"]))
    check("missed.limit_alert_emitted",
          any(a["alert_code"] == "SCHED.MISSED_RUN_LIMIT"
              for a in env_l.state.alerts()))

    # ==================================================================
    # J. Run manifests
    # ==================================================================
    m = m_ok
    manifest_dir = os.path.join(env_f.state.root, "manifests")
    check("manifest.file_written",
          any(f.startswith(m["run_id"]) for f in os.listdir(manifest_dir)),
          str(os.listdir(manifest_dir)))
    required = ("run_id", "started_utc", "ended_utc", "tasks_attempted",
                "tasks_succeeded", "tasks_failed", "input_hashes",
                "output_hashes", "drift_state", "status")
    check("manifest.required_fields",
          all(k in m for k in required),
          str([k for k in required if k not in m]))
    check("manifest.task_counts_add_up",
          m["tasks_attempted"] == m["tasks_succeeded"] + m["tasks_failed"]
          and m["tasks_attempted"] == len(m["tasks"]),
          "%d/%d/%d" % (m["tasks_attempted"], m["tasks_succeeded"],
                        m["tasks_failed"]))
    check("manifest.input_hashes_present",
          "drift" in m["input_hashes"] and "config" in m["input_hashes"],
          json.dumps(sorted(m["input_hashes"])))
    check("manifest.output_hashes_match_written",
          m["output_count"] == len(env_f.state.predictions())
          + len(env_f.state.grades()),
          "%d vs %d" % (m["output_count"],
                        len(env_f.state.predictions())))
    check("manifest.run_index_tracks_runs",
          len(env_f.state.read_jsonl(scheduler.RUN_INDEX))
          == len([f for f in os.listdir(manifest_dir)
                  if f.endswith(".json")]),
          "%d index rows vs %d manifests"
          % (len(env_f.state.read_jsonl(scheduler.RUN_INDEX)),
             len([f for f in os.listdir(manifest_dir)
                  if f.endswith(".json")])))
    check("manifest.timestamps_are_iso_z",
          scheduler.is_iso_z(m["started_utc"])
          and scheduler.is_iso_z(m["ended_utc"]))
    check("manifest.declares_no_override",
          m["provenance_policy"]["override_permitted"] is False
          and m["provenance_policy"]["backfill_excluded_from_prospective"]
          is True)

    # ==================================================================
    # K. Structured alerts
    # ==================================================================
    alerts = env_d.state.alerts()
    check("alert.emitted_on_run_start",
          any(a["alert_code"] == "SCHED.RUN_START" for a in alerts))
    schema_ok = all(
        all(k in a for k in ("ts", "alert_id", "alert_code", "severity",
                             "run_id", "component", "detail"))
        for a in alerts)
    check("alert.schema_complete", schema_ok)
    check("alert.severities_are_typed",
          all(a["severity"] in scheduler.ALERT_SEVERITIES for a in alerts))
    check("alert.codes_are_known",
          all(a["alert_code"] in scheduler.ALERT_CODES for a in alerts),
          str(sorted(set(a["alert_code"] for a in alerts))))
    check("alert.timestamps_are_iso_z",
          all(scheduler.is_iso_z(a["ts"]) for a in alerts))

    # ==================================================================
    # L. Safe shutdown: partial work kept, never double-applied
    # ==================================================================
    env_s = Env()
    env_s.ready()
    env_s.sched.shutdown.request("SIGTERM")
    ms1 = env_s.tick()
    check("shutdown.before_effects_writes_nothing",
          ms1["status"] == scheduler.STATUS_SHUTDOWN
          and len(env_s.state.predictions()) == 0,
          ms1["status"])
    check("shutdown.reported_in_manifest",
          ms1["shutdown_requested"] is True
          and ms1["shutdown_reason"] == "SIGTERM")

    env_s.sched.shutdown.clear()
    env_s.tick()
    n_after_first = len(env_s.state.predictions())

    # Stop the run part-way through: trip the shutdown signal from inside
    # the prediction task, after records have been durably appended but
    # before grading begins.
    env_s2 = Env()
    env_s2.ready()
    env_s2.tick()
    preds_before = len(env_s2.state.predictions())
    env_s2.clock.advance(days=20)
    env_s2.cfg = scheduler.SchedulerConfig(max_missed_runs=99)
    env_s2.sched.cfg = env_s2.cfg
    real_append = env_s2.state.append_prediction

    def trip_shutdown(rec):
        out = real_append(rec)
        env_s2.sched.shutdown.request("SIGTERM")
        return out

    env_s2.state.append_prediction = trip_shutdown
    ms2 = env_s2.tick()
    env_s2.state.append_prediction = real_append
    check("shutdown.before_grading_preserves_predictions",
          ms2["status"] == scheduler.STATUS_SHUTDOWN
          and len(env_s2.state.predictions()) > preds_before,
          "%s / %d" % (ms2["status"], len(env_s2.state.predictions())))
    check("shutdown.no_grades_written",
          len(env_s2.state.grades()) == 0,
          str(len(env_s2.state.grades())))

    env_s2.sched.shutdown.clear()
    ms3 = env_s2.tick()
    check("shutdown.resume_completes_grading",
          ms3["status"] in (scheduler.STATUS_OK, scheduler.STATUS_PARTIAL)
          and len(env_s2.state.grades()) == len(env_s2.cfg.cohorts),
          "%s / %d" % (ms3["status"], len(env_s2.state.grades())))
    resumed_preds = len(env_s2.state.predictions())
    env_s2.tick()
    check("shutdown.resume_never_duplicates",
          len(env_s2.state.predictions()) == resumed_preds,
          "%d vs %d" % (len(env_s2.state.predictions()), resumed_preds))
    check("shutdown.partial_work_not_lost", n_after_first ==
          len(env_s.cfg.cohorts), str(n_after_first))

    # ==================================================================
    # M. Financial invariants
    # ==================================================================
    env_i = Env()
    env_i.ready()
    env_i.tick()
    env_i.clock.advance(days=20)
    env_i.cfg = scheduler.SchedulerConfig(max_missed_runs=99)
    env_i.sched.cfg = env_i.cfg
    env_i.tick()

    pred_hashes = set(p["record_hash"] for p in env_i.state.predictions())
    check("invariant.every_grade_has_matching_parent",
          all(g["parent_prediction_hash"] in pred_hashes
              for g in env_i.state.grades())
          and len(env_i.state.grades()) > 0,
          "%d grades" % len(env_i.state.grades()))

    orphan = dict(env_i.state.predictions()[0])
    orphan["record_hash"] = "deadbeef" * 8
    parents_by_hash = dict((p["record_hash"], p)
                           for p in env_i.state.predictions())
    raised = False
    try:
        scheduler.grade_prediction(
            env_i.clock, env_i.cal, env_i.cfg, orphan, parents_by_hash, {},
            env_i.sessions, None, "run-orphan",
            {"status": scheduler.DRIFT_CLEAN})
    except scheduler.GradeWithoutParentError:
        raised = True
    check("invariant.grade_without_parent_refused", raised)

    # A hash-only parent index must also refuse an unknown hash.
    raised_set = False
    try:
        scheduler.grade_prediction(
            env_i.clock, env_i.cal, env_i.cfg, orphan, pred_hashes, {},
            env_i.sessions, None, "run-orphan-set",
            {"status": scheduler.DRIFT_CLEAN})
    except scheduler.GradeWithoutParentError:
        raised_set = True
    check("invariant.grade_without_parent_refused_hash_index", raised_set)

    # A retro parent may be graded, but never as prospective evidence.
    # A long freshness SLA so the recovered (retro) records carry real
    # inputs rather than abstaining -- we want to prove the provenance
    # invariant fires even for a record that is otherwise gradeable.
    env_p = Env(config=scheduler.SchedulerConfig(
        freshness_sla_seconds=30 * 24 * 3600))
    env_p.ready()
    env_p.tick()
    env_p.clock.set("2026-08-17T21:00:00Z")
    env_p.tick()
    retro = [p for p in env_p.state.predictions()
             if p["provenance_mode"] == scheduler.RETROSPECTIVE_BACKFILL]
    check("invariant.retro_records_exist_for_test", len(retro) > 0,
          str(len(retro)))
    check("invariant.retro_records_are_gradeable_shape",
          all(p["abstention"] is False
              and p["forecast_distribution"] is not None for p in retro))

    retro_copy = dict(retro[0])
    retro_copy["provenance_mode"] = scheduler.PROSPECTIVE
    env_p.clock.set("2026-09-01T21:00:00Z")
    sessions = env_p.cal.trading_days_bounded(
        scheduler.eastern_date(env_p.clock.now()), lookback_days=400)
    closes = env_p.close_series(retro_copy["cohort_id"])
    closes["__benchmark__"] = env_p.close_series(scheduler.BENCHMARK)
    latest = env_p.sched._latest_realized(sessions)
    raised = False
    try:
        scheduler.grade_prediction(
            env_p.clock, env_p.cal, env_p.cfg, retro_copy,
            {retro_copy["record_hash"]: retro_copy}, closes, sessions,
            latest, "run-inv", {"status": scheduler.DRIFT_CLEAN})
    except scheduler.BackfillRestrictionError:
        raised = True
    check("invariant.retro_cannot_be_laundered_prospective", raised)

    # Timestamp discipline across every emitted record.
    bad = []
    for rec in (env_i.state.predictions() + env_i.state.grades()
                + env_i.state.alerts()):
        for key, val in rec.items():
            if (key.endswith("_utc") or key.endswith("_ts")) \
                    and val is not None:
                if not scheduler.is_iso_z(val):
                    bad.append("%s=%r" % (key, val))
    check("invariant.all_record_timestamps_are_utc_z", not bad,
          ", ".join(bad[:3]))

    # Duplicate events never duplicate financial effects.
    before_agg = scheduler.aggregate_prospective(env_i.state.grades())
    env_i.tick()
    after_agg = scheduler.aggregate_prospective(env_i.state.grades())
    check("invariant.duplicates_do_not_move_the_books",
          before_agg["records_prospective"]
          == after_agg["records_prospective"]
          and before_agg["mean_excess_vs_benchmark"]
          == after_agg["mean_excess_vs_benchmark"],
          "%s vs %s" % (before_agg["records_prospective"],
                        after_agg["records_prospective"]))

    # ==================================================================
    # N. Hygiene: network-free, ASCII, deterministic
    # ==================================================================
    with open(scheduler.MODULE_PATH, "r", encoding="ascii") as fh:
        source = fh.read()
    net_tokens = ("urllib", "requests", "socket", "urlopen", "ftplib",
                  "http://", "https://", "xmlrpc", "telnet")
    check("hygiene.no_network_tokens",
          not [t for t in net_tokens if t in source],
          str([t for t in net_tokens if t in source]))
    raw = open(scheduler.MODULE_PATH, "rb").read()
    check("hygiene.source_is_ascii", all(b < 128 for b in raw),
          "non-ascii bytes present")
    check("hygiene.module_hash_is_stable",
          len(scheduler.module_code_hash()) == 64)

    env_x = Env(seed=3)
    env_x.ready()
    env_x.tick()
    env_y = Env(seed=3)
    env_y.ready()
    env_y.tick()
    check("hygiene.deterministic_across_identical_envs",
          [p["record_hash"] for p in env_x.state.predictions()]
          == [p["record_hash"] for p in env_y.state.predictions()])

    # ==================================================================
    # O. CLI surface
    # ==================================================================
    status = scheduler.cmd_status(scheduler.SchedulerState(
        os.path.join(tempfile.mkdtemp(prefix="fis-cli-"), "state")))
    check("cli.status_schema",
          all(k in status for k in ("module_version", "predictions",
                                    "grades", "drift_status",
                                    "escape_hatch_clean", "checked_utc")),
          json.dumps(sorted(status)))
    check("cli.reports_no_escape_hatch",
          status["escape_hatch_clean"] is True)

    # ==================================================================
    # Verdict
    # ==================================================================
    for e in _ENVS:
        e.cleanup()

    print("")
    print("=" * 64)
    print("PASSED: %d   FAILED: %d" % (len(PASSES), len(FAILURES)))
    for name, detail in FAILURES:
        print("  FAILED: %s -- %s" % (name, detail))
    print("=" * 64)
    return 0 if not FAILURES else 1


if __name__ == "__main__":
    sys.exit(main())
