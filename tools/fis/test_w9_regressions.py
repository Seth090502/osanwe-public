#!/usr/bin/env python3
"""W9 regression locks: every HIGH/CRITICAL finding, re-tested after repair.

Each block names the finding it locks down and reproduces the ORIGINAL
attack. If a repair is ever reverted, this file fails.

Findings locked here:
  W9A-A6-01 CRITICAL  read path laundered a backfill via two stored fields
  W9A-A5-01 HIGH      non-trading earliest_tradable classified PROSPECTIVE
  W9A-A5-02 HIGH      foreign calendar without offset_session broke policy
  W9B-A6-13 CRITICAL  non-human identities approved (denylist incomplete)
  W9B-A6-06 HIGH      grant consumption was in-memory only

Stdlib only. ASCII only. No network.
"""

from __future__ import annotations

import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import approval  # noqa: E402
import temporal_policy as tp  # noqa: E402

PASSED = []
FAILED = []


def check(cid, ok, detail=""):
    (PASSED if ok else FAILED).append(cid)
    print("[%s] %-52s %s" % ("PASS" if ok else "FAIL", cid, detail))
    return ok


def _safe_rmtree(path):
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                os.unlink(os.path.join(root, name))
            except OSError:
                pass
    try:
        os.rmdir(path)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# W9A-A6-01 (CRITICAL): read path must re-derive, never trust the stamp
# ---------------------------------------------------------------------------

def test_a6_01():
    # Created 2026-08-26 for a 2026-07-02 window: unambiguously
    # retrospective by its own timestamps.
    grade = {
        "record_type": "grade",
        "cohort_id": "TEST",
        "creation_ts": "2026-08-26T04:44:46Z",
        "earliest_tradable": "2026-07-02",
        "provenance_mode": tp.PROSPECTIVE,          # FORGED
        "prospective_evidence": True,               # FORGED
        "excess_vs_benchmark": 0.50,
        "direction_accuracy": 1.0,
    }
    check("A6-01 forged grade stamp overruled",
          tp.is_prospective_evidence(grade) is False,
          "stamp=%s/derived=%s"
          % (grade["provenance_mode"],
             tp.provenance_decision(grade["creation_ts"],
                                    grade["earliest_tradable"])
             ["provenance_mode"]))

    # The stamp must be overruled when only the nested grade block carries
    # the timestamps (the shape grade_matured actually writes).
    nested = {
        "record_type": "grade",
        "provenance_mode": tp.PROSPECTIVE,
        "prospective_evidence": True,
        "grades": {"creation_ts": "2026-08-26T04:44:46Z",
                   "earliest_tradable": "2026-07-02"},
    }
    check("A6-01 nested grade timestamps honoured",
          tp.is_prospective_evidence(nested) is False)

    # A stamp with NO timestamps behind it is unverifiable, not prospective.
    check("A6-01 unverifiable stamp is not prospective",
          tp.is_prospective_evidence(
              {"provenance_mode": tp.PROSPECTIVE,
               "prospective_evidence": True}) is False)

    # A genuinely prospective record still passes.
    good = {"record_type": "prediction",
            "creation_ts": "2026-09-01T12:00:00Z",
            "earliest_tradable": "2026-09-02",
            "provenance_mode": tp.PROSPECTIVE,
            "prospective_evidence": True}
    check("A6-01 genuine record still prospective",
          tp.is_prospective_evidence(good) is True)

    # Non-dict input fails closed.
    check("A6-01 non-dict fails closed",
          tp.is_prospective_evidence(None) is False
          and tp.is_prospective_evidence("x") is False)


# ---------------------------------------------------------------------------
# W9A-A5-01 (HIGH): a non-trading earliest_tradable is not a forecast
# ---------------------------------------------------------------------------

def test_a5_01():
    for label, day in (("Saturday", "2026-03-07"),
                       ("Sunday", "2026-03-08"),
                       ("Christmas", "2026-12-25"),
                       ("New Year", "2026-01-01"),
                       ("Thanksgiving", "2026-11-26")):
        v = tp.provenance_decision("2026-01-05T12:00:00Z", day)
        check("A5-01 %s is not a trading session" % label,
              v["provenance_mode"] == tp.RETROSPECTIVE_BACKFILL
              and v["prospective_evidence"] is False,
              "%s -> %s" % (day, v["rule"]))

    v = tp.prediction_eligibility_verdict({
        "record_type": "prediction", "cohort_id": "T",
        "creation_ts": "2026-01-05T12:00:00Z",
        "info_cutoff": "2026-01-02",
        "earliest_tradable": "2026-03-07", "horizon_days": 5,
        "missing_data_state": {"state": "complete"}})
    check("A5-01 verdict refuses non-trading session",
          v.prediction_eligible is False,
          "%s" % v.reason_code)

    # A real session is unaffected.
    v2 = tp.provenance_decision("2026-09-01T12:00:00Z", "2026-09-02")
    check("A5-01 real session still prospective",
          v2["provenance_mode"] == tp.PROSPECTIVE, v2["rule"])


# ---------------------------------------------------------------------------
# W9A-A5-02 (HIGH): a partial foreign calendar must not break the policy
# ---------------------------------------------------------------------------

class PartialCalendar(object):
    """Deliberately incomplete: no offset_session, no session_index."""

    def __init__(self):
        self.inner = tp.SimpleUSMarketCalendar()

    def is_trading_day(self, day):
        return self.inner.is_trading_day(day)

    def trading_days(self, start, end):
        return self.inner.trading_days(start, end)

    def market_close_utc(self, day):
        return self.inner.market_close_utc(day)


def test_a5_02():
    saved = tp.get_default_calendar()
    try:
        tp.set_default_calendar(PartialCalendar())
        rec = {
            "record_type": "prediction", "cohort_id": "T",
            "creation_ts": "2026-08-03T12:00:00Z",
            "info_cutoff": "2026-08-02",
            "earliest_tradable": "2026-08-03", "horizon_days": 5,
            "missing_data_state": {"state": "complete"},
        }
        try:
            avail = tp.outcome_availability(rec)
            check("A5-02 partial calendar derives offset_session",
                  avail["maturity_date"] is not None,
                  "maturity=%s" % avail["maturity_date"])
            v = tp.grade_eligibility_verdict(rec, now_utc="2026-09-01T21:00:00Z")
            check("A5-02 partial calendar supports grading verdict",
                  v.grade_eligible is True, v.reason_code)
        except AttributeError as exc:
            check("A5-02 partial calendar derives offset_session", False,
                  "AttributeError: %s" % exc)
    finally:
        tp.set_default_calendar(saved)

    # The scheduler's real calendar must also survive registration.
    if "tools" in HERE or True:
        try:
            import scheduler  # noqa: F401
            rec = {
                "record_type": "prediction", "cohort_id": "T",
                "creation_ts": "2026-08-03T12:00:00Z",
                "info_cutoff": "2026-08-02",
                "earliest_tradable": "2026-08-03", "horizon_days": 5,
                "missing_data_state": {"state": "complete"},
            }
            avail = tp.outcome_availability(rec)
            check("A5-02 scheduler calendar works through adapter",
                  avail["maturity_date"] is not None,
                  "maturity=%s" % avail["maturity_date"])
        except Exception as exc:                # noqa: BLE001
            check("A5-02 scheduler calendar works through adapter", False,
                  "%s: %s" % (type(exc).__name__, exc))


# ---------------------------------------------------------------------------
# W9B-A6-13 (CRITICAL): a denylist is not an approver control
# ---------------------------------------------------------------------------

def test_a6_13():
    auth = approval.ApprovalAuthority(approval.generate_key(),
                                      clock=lambda: "2026-01-01T00:00:00Z")
    b = approval.DecisionBinding(
        decision_id="D-NH", decision_type="rebalance_proposal",
        legs=(approval.Leg("L0", "SELL", "ZPHR", "acct", quantity=1.0),),
        account="acct", model_version="m", data_version="d",
        policy_version="p", code_hash="c", price_as_of="2026-01-01",
        expires_at="2026-01-02T00:00:00Z", requested_by="agent")
    rec = approval.DecisionRecord(
        binding=b, state=approval.STATE_HUMAN_APPROVAL_REQUIRED)

    # Before any human is registered, nobody may approve.
    try:
        auth.issue(rec, "<email>")
        check("A6-13 empty registry approves nobody", False, "ISSUED")
    except approval.ApprovalViolation as exc:
        check("A6-13 empty registry approves nobody",
              exc.code == "NO_HUMAN_REGISTERED", exc.code)

    auth.registry.register("owner@household", "owner",
                           registered_by="operator-setup",
                           when_utc="2025-12-01T00:00:00Z")

    # The exact identities that cleared the old denylist.
    for bogus in ("automation", "claude", "svc-approver-bot", "robot-7",
                  "nightly-pipeline", "helper-script", "agent-2",
                  "deploy-bot", "svc-account", "ai-helper"):
        r = approval.DecisionRecord(
            binding=b, state=approval.STATE_HUMAN_APPROVAL_REQUIRED)
        try:
            auth.issue(r, bogus)
            check("A6-13 refuses[%s]" % bogus, False, "ISSUED")
        except approval.ApprovalViolation as exc:
            check("A6-13 refuses[%s]" % bogus,
                  exc.code == "NON_HUMAN_APPROVER", exc.code)

    # The registered human can still approve.
    r = approval.DecisionRecord(
        binding=b, state=approval.STATE_HUMAN_APPROVAL_REQUIRED)
    g = auth.issue(r, "owner@household", ttl_seconds=3600)
    check("A6-13 registered human can approve",
          g.approver_identity == "owner@household"
          and r.state == approval.STATE_APPROVED_FOR_SIMULATION)

    # A machine-shaped identity cannot be registered either.
    try:
        auth.registry.register("ci-bot", "CI", registered_by="operator")
        check("A6-13 machine identity unregisterable", False, "registered")
    except approval.ApprovalViolation as exc:
        check("A6-13 machine identity unregisterable",
              exc.code == "NON_HUMAN_APPROVER", exc.code)


# ---------------------------------------------------------------------------
# W9B-A6-06 (HIGH): revocation must be as durable as the grant
# ---------------------------------------------------------------------------

def test_a6_06():
    tmpd = tempfile.mkdtemp(prefix="w9-consume-")
    try:
        key = approval.generate_key()
        ledger = os.path.join(tmpd, "consumed.jsonl")
        clock = lambda: "2026-01-01T00:00:00Z"  # noqa: E731
        b = approval.DecisionBinding(
            decision_id="D-DUP", decision_type="rebalance_proposal",
            legs=(approval.Leg("L0", "SELL", "ZPHR", "acct", quantity=1.0),),
            account="acct", model_version="m", data_version="d",
            policy_version="p", code_hash="c", price_as_of="2026-01-01",
            expires_at="2026-01-02T00:00:00Z", requested_by="agent")

        a1 = approval.ApprovalAuthority(key, clock=clock,
                                        consumption_path=ledger)
        a1.registry.register("owner@household", "owner", registered_by="setup",
                             when_utc="2025-12-01T00:00:00Z")
        r1 = approval.DecisionRecord(
            binding=b, state=approval.STATE_HUMAN_APPROVAL_REQUIRED)
        g1 = a1.issue(r1, "owner@household", ttl_seconds=3600)
        first = a1.verify(r1, grant=g1, now="2026-01-01T00:20:00Z")
        check("A6-06 first presentation accepted", first.ok, str(first.codes))

        # A restart: same key, same ledger, fresh object.
        a2 = approval.ApprovalAuthority(key, clock=clock,
                                        consumption_path=ledger)
        r2 = approval.DecisionRecord(
            binding=b, state=approval.STATE_HUMAN_APPROVAL_REQUIRED)
        second = a2.verify(r2, grant=g1, now="2026-01-01T00:21:00Z")
        check("A6-06 replay refused after restart",
              (not second.ok) and "REPLAYED_APPROVAL" in second.codes,
              str(second.codes))

        # In-process replay is refused too.
        r3 = approval.DecisionRecord(
            binding=b, state=approval.STATE_HUMAN_APPROVAL_REQUIRED)
        third = a1.verify(r3, grant=g1, now="2026-01-01T00:22:00Z")
        check("A6-06 replay refused in process",
              (not third.ok) and "REPLAYED_APPROVAL" in third.codes,
              str(third.codes))

        check("A6-06 consumption ledger persisted",
              os.path.exists(ledger)
              and os.path.getsize(ledger) > 0)
    finally:
        _safe_rmtree(tmpd)


# ---------------------------------------------------------------------------

def main():
    print("=" * 66)
    print("W9 REGRESSION LOCKS")
    print("=" * 66)
    for fn in (test_a6_01, test_a5_01, test_a5_02, test_a6_13, test_a6_06):
        fn()
    print("=" * 66)
    print("PASSED: %d   FAILED: %d" % (len(PASSED), len(FAILED)))
    print("=" * 66)
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
