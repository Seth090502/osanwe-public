#!/usr/bin/env python3
"""Observe deterministic runtime health; no model research or account queries.

The daily Codex heartbeat calls `python tools/runtime-health.py run --scheduled`.
Sunday selects the full offline profile; other days use --quick. Manual runs do
not count toward the seven actual scheduled-cycle pilot. Notification delivery
is recorded separately using `notice`; this command cannot certify delivery.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
import re
import sys

from fis.runtime_health import (Journal, OverlapError, artifact_state, bounded_process,
    create_json, eastern_datetime, inventory, iso_z, job_lock, now_utc,
    readiness, reconcile_inventory, completion_marker, file_sha)
from fis.runtime_health import validation_outcome

ROOT = Path(__file__).resolve().parent.parent
JOB = "osanwe-daily-monitor"
MONITOR_SOURCES = ["tools/runtime-health.py", "tools/fis/runtime_health.py", "tools/fis/scheduler.py",
                   ".agents/scripts/checkall.py", "config/scheduled-jobs.json"]


def monitor_identity(root=ROOT):
    return {name: file_sha(root / name) for name in MONITOR_SOURCES}


def monitor_readiness(receipt, at, root=ROOT):
    state = readiness(receipt, at)
    if state == "host-unobserved":
        return state
    claimed = receipt.get("code_identity")
    if not isinstance(claimed, dict) or set(claimed) != set(MONITOR_SOURCES):
        return "unavailable"
    try:
        return state if claimed == monitor_identity(root) else "stale"
    except OSError:
        return "unavailable"


def scorer_producer_findings(root=ROOT):
    """Legacy completion alone cannot attest to a changed scoring producer."""
    log = root / ".claude/state/score-outcomes-runs.log"
    if completion_marker(log, "score-outcomes-summary/1")["state"] != "passed":
        return []  # The existing completion contract reports this failure.
    try:
        with log.open("rb") as handle:
            handle.seek(max(0, log.stat().st_size - 4096))
            lines = handle.read(4096).decode("ascii", errors="replace").strip().splitlines()
        marker = re.fullmatch(r"Runtime: producer_sha256=([0-9a-f]{64})", lines[-2].strip()) if len(lines) >= 2 else None
        if not marker:
            state, code = "unavailable", "producer-code-identity-unavailable"
        elif marker[1] != file_sha(root / "tools/score-outcomes.py"):
            state, code = "stale", "producer-code-identity-stale"
        else:
            return []
    except OSError:
        state, code = "unavailable", "producer-code-identity-unavailable"
    return [{"job": "osanwe-sunday-scorer", "state": state, "code": code}]


def retain_unchecked_validation(findings, open_incidents, profile):
    """A quick pass cannot recover an incident established by the full audit."""
    prefix = "validation-" + profile + "-"
    for row in open_incidents:
        code = row["code"]
        if row["job"] == JOB and code.startswith("validation-") and not code.startswith(prefix):
            prior_state = code.rsplit("-", 1)[-1]
            findings.append({"job": JOB, "state": prior_state if prior_state in ("failed", "stale", "unavailable") else "unavailable",
                             "code": code, "reason": "prior-validation-scope-not-rechecked"})


def run(args):
    at = now_utc()
    journal = Journal(args.state_dir)
    try:
        with job_lock(args.state_dir / "monitor.lock"):
            code_identity = monitor_identity()
            slot = journal.reconcile(JOB, at)
            # On its first scheduled invocation after 08:00, explicitly admit
            # today's opportunity; earlier opportunities remain unobserved.
            if args.scheduled and slot is None:
                from fis.runtime_health import opportunities
                slots = opportunities(at - dt.timedelta(hours=24), at)
                if slots and eastern_datetime(slots[-1]).date() == eastern_datetime(at).date():
                    slot = iso_z(slots[-1])
            if args.scheduled and slot is None:
                return {"schema": "osanwe.runtime-health/1", "state": "unavailable",
                        "reason": "current_slot_not_due", "verified_at": iso_z(at)}, 2
            attempt = journal.begin(JOB, slot, at, "scheduled" if args.scheduled else "manual")
            if attempt is None:
                return {"schema": "osanwe.runtime-health/1", "state": "unavailable",
                        "reason": "current_slot_already_spent", "verified_at": iso_z(at)}, 2
            run_dir = args.state_dir / "runs" / attempt["run_id"]
            run_dir.mkdir(parents=True, exist_ok=False)
            check_report = run_dir / "checkall.json"
            deep = eastern_datetime(at).weekday() == 6 if not args.quick else False
            command = [sys.executable, "-B", str(ROOT / ".agents/scripts/checkall.py"),
                       "--json", "--json-report", str(check_report)]
            if not deep:
                command.append("--quick")
            computation = bounded_process(command, ROOT, 1800 if deep else 300)
            artifact = validation_outcome(computation, check_report, at)
            observed = inventory(ROOT)
            manifest = json.loads((ROOT / "config/scheduled-jobs.json").read_text(encoding="utf-8"))
            findings = reconcile_inventory(manifest, observed, ROOT)
            findings.extend(scorer_producer_findings())
            validation_profile = "full" if deep else "quick"
            if artifact["state"] != "passed":
                findings.append({"job": JOB, "state": artifact["state"], "code": "validation-" + validation_profile + "-" + artifact["state"],
                                 "reason": artifact["reason"]})
            open_incidents = journal.db.execute("SELECT job,code FROM incidents WHERE state='open'").fetchall()
            retain_unchecked_validation(findings, open_incidents, validation_profile)
            code_stable = code_identity == monitor_identity()
            if not code_stable:
                findings.append({"job": JOB, "state": "stale", "code": "monitor-code-changed-during-run"})
            state = ("failed" if any(f["state"] == "failed" for f in findings) else
                     "stale" if any(f["state"] == "stale" for f in findings) else
                     "unavailable" if any(f["state"] == "unavailable" for f in findings) else "passed")
            transitions = []
            current = {(f["job"], f["code"]) for f in findings}
            for name, code in current:
                change = journal.incident(name, code, True, now_utc())
                if change:
                    transitions.append(change)
            for open_row in journal.db.execute("SELECT job,code FROM incidents WHERE state='open'").fetchall():
                if (open_row["job"], open_row["code"]) not in current:
                    # An unavailable inventory cannot demonstrate task recovery.
                    if observed["state"] != "passed" and open_row["job"] != JOB:
                        continue
                    change = journal.incident(open_row["job"], open_row["code"], False, now_utc())
                    if change:
                        transitions.append(change)
            report = {"schema": "osanwe.runtime-health/1", "state": state,
                      "verified_at": iso_z(now_utc()), "expires_at": iso_z(now_utc() + dt.timedelta(hours=25)),
                      "attempt": attempt, "profile": "sunday-offline" if deep else "quick-offline",
                      "code_identity": code_identity, "code_unchanged_during_run": code_stable,
                      "computation": computation, "artifact": artifact,
                      "validation_evidence": str(check_report), "scheduler": observed,
                      "findings": findings, "incident_transitions": transitions,
                      "notification_needed": bool(transitions), "notification_delivery": "not_attempted",
                      "external_missing_heartbeat_observer": "unavailable",
                      "limits": ["Manual invocation cannot establish an actual scheduled opportunity.",
                                 "A local machine cannot observe its own offline state.",
                                 "No model research, evaluation attempts, or account reads occur."]}
            path = run_dir / "receipt.json"
            create_json(path, report)
            journal.finish(attempt, now_utc(), state, path)
            # This returned view is computed from the journal after completion;
            # the immutable receipt above is the evidence for this one run.
            report["rolling_30_days"] = journal.summary(JOB, now_utc())
            return report, 0 if state == "passed" else 1
    except OverlapError:
        return {"schema": "osanwe.runtime-health/1", "state": "unavailable",
                "reason": "overlap_refused", "verified_at": iso_z(at)}, 2
    finally:
        journal.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state-dir", type=Path, default=ROOT / ".agents/state/runtime-health")
    sub = ap.add_subparsers(dest="action", required=True)
    runp = sub.add_parser("run")
    runp.add_argument("--scheduled", action="store_true")
    runp.add_argument("--quick", action="store_true", help="manual diagnostic only; never weaken a Sunday scheduled run")
    sub.add_parser("status")
    notice = sub.add_parser("notice")
    notice.add_argument("--incident", required=True)
    notice.add_argument("--outcome", choices=("attempted", "failed", "confirmed"), required=True)
    notice.add_argument("--delivery-receipt")
    args = ap.parse_args(argv)
    args.state_dir = args.state_dir.resolve()
    if args.action == "run":
        if args.scheduled and args.quick:
            ap.error("scheduled Sunday scope cannot be overridden")
        report, code = run(args)
        print(json.dumps(report, indent=2))
        return code
    journal = Journal(args.state_dir)
    try:
        if args.action == "notice":
            journal.notice(args.incident, args.outcome, now_utc(), args.delivery_receipt)
            print(json.dumps({"state": "recorded", "outcome": args.outcome,
                              "attestation": "caller-reported delivery evidence"}))
            return 0
        latest_row = journal.db.execute("SELECT evidence FROM opportunities WHERE job=? AND status IN "
                                       "('passed','failed','stale','unavailable') AND evidence IS NOT NULL "
                                       "ORDER BY ended DESC LIMIT 1", (JOB,)).fetchone()
        latest = Path(latest_row[0]) if latest_row else None
        try:
            receipt = json.loads(latest.read_text()) if latest else None
            current_state = monitor_readiness(receipt, now_utc()) if receipt else "host-unobserved"
        except (OSError, ValueError):
            receipt, current_state = None, "unavailable"
        print(json.dumps({"schema": "osanwe.runtime-health-status/1",
                          "state": current_state,
                          "latest_evidence": str(latest) if latest else None,
                          "rolling_30_days": journal.summary(JOB, now_utc())}, indent=2))
        return 0
    finally:
        journal.close()


if __name__ == "__main__":
    raise SystemExit(main())
