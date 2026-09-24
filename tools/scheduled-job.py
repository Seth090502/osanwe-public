#!/usr/bin/env python3
"""Bounded, artifact-aware wrappers for existing Osanwe scheduled jobs.

The calibration pipeline writes a new version directory and completion receipt
only after fresh network/store equivalence. Legacy grades, the inherited
factor database and prior calibrators remain unchanged. Reindex observes only
external runner/index metadata; it never reads indexed note contents.
"""
import argparse
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import uuid

from fis.runtime_health import (Journal, OverlapError, artifact_state, bounded_process,
    create_json, file_sha, iso_z, job_lock, now_utc, opportunities, parse_iso_z, process_exists, scheduled_sources)

ROOT = Path(__file__).resolve().parent.parent
JOBS = {"nightly-health": {"name": "osanwe-nightly-health", "hour": 3, "minute": 30},
        "weekly-calibration": {"name": "osanwe-weekly-calibration", "hour": 7, "minute": 30, "weekdays": [6]},
        "vault-reindex": {"name": "osanwe-vault-reindex"}}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def step(command, run_dir, label, timeout, outputs=(), maintenance=None):
    started = now_utc()
    result = bounded_process(command, ROOT, timeout, maintenance=maintenance)
    process_observation = dict(result)
    checks = []
    for path, schema in outputs:
        check = artifact_state(path, started, json_schema=schema)
        checks.append({"path": str(path), **check})
    if any(c["state"] != "passed" for c in checks):
        result["state"] = "failed"
        result["reason"] = "output_contract_failed"
    row = {"name": label, **result, "artifacts": checks, "computation": process_observation}
    create_json(run_dir / (label + ".step.json"), row)
    return row


def health_pipeline(run_dir):
    report = run_dir / "validation.json"
    row = step([sys.executable, "-B", str(ROOT / ".agents/scripts/checkall.py"),
                "--quick", "--json", "--json-report", str(report)], run_dir,
               "offline-validation", 300, [(report, "osanwe.validation/1")])
    return {"state": row["state"], "scope": "quick-offline", "steps": [row],
            "limitations": ["Quick checks do not establish native model or connector operation."]}


def staged_report_script(module_path, candidate, arguments):
    # Structured JSON is embedded as a Python literal, never shell-expanded.
    return ("import importlib.util,sys;from pathlib import Path;"
            "spec=importlib.util.spec_from_file_location('staged_report',%r);"
            "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);"
            "m.ROOT=Path(%r);sys.argv=[%r]+%r;sys.exit(m.main())") % (
                str(module_path), str(candidate), str(module_path), arguments)


def calibration_pipeline(run_dir):
    bp = load_module("scheduled_calibration_bp", ROOT / "tools/backtest-prediction.py")
    symbols = {"SPY"}
    omitted = []
    analysis_meta = {}
    for commit in bp.analysis_commits():
        meta = bp.parse_analysis_text(bp.sh("git", "show", commit["sha"] + ":" + commit["path"]), commit["path"])
        if not meta["ticker"] or not meta["verdict"]:
            continue
        if meta["instrument_type"] == "listed-security":
            symbols.add(meta["price_symbol"])
            key = (meta["ticker"], commit["t0"])
            if key in analysis_meta:
                raise ValueError("analysis identity collision; ticker/date is not unique")
            analysis_meta[key] = meta
        else:
            omitted.append({"ticker": meta["ticker"], "price_symbol": meta["price_symbol"],
                            "instrument_type": meta["instrument_type"], "reason": "requires-compatible-asset-calendar",
                            "symbol_authority": meta["symbol_authority"]})
    db = run_dir / "factors.db"
    network = run_dir / "network-outcomes.jsonl"
    offline = run_dir / "offline-outcomes.jsonl"
    direction = run_dir / "direction-outcomes.jsonl"
    rows = []
    commands = [
        ("public-price-ingest", [sys.executable, str(ROOT / "tools/factor-store.py"),
            "--ingest-bars", ",".join(sorted(symbols)), "--db", str(db)], 300, [(db, None)]),
        ("network-mature-outcomes", [sys.executable, str(ROOT / "tools/backtest-v2.py"),
            "--run", "--all", "--out", str(network)], 600, [(network, None), (Path(str(network) + ".coverage.json"), None)]),
        ("offline-exact-replay", [sys.executable, str(ROOT / "tools/backtest-offline.py"),
            "--db", str(db), "--cross-check", str(network), "--out", str(offline)], 300,
            [(offline, None), (Path(str(offline) + ".coverage.json"), None)]),
    ]
    for label, command, timeout, outputs in commands:
        row = step(command, run_dir, label, timeout, outputs)
        rows.append(row)
        if row["state"] != "passed":
            return {"state": "failed", "scope": "listed-security-retrospective-calibration",
                    "failed_step": label, "steps": rows, "omitted_instruments": omitted,
                    "publication": "withheld; inherited artifacts unchanged"}
    # Reuse the exact verified prices. Calling a third live fetch adds neither
    # independence nor information after network/store equivalence was checked.
    direction_rows = []
    for row in map(json.loads, offline.read_text(encoding="utf-8").splitlines()):
        if row["horizon"] != 21:
            continue
        meta = analysis_meta[(row["ticker"], row["t0"])]
        wanted, correct = bp.grade(meta["verdict"], row["stk_ret"])
        direction_rows.append({**row, "direction_wanted": wanted, "correct": correct,
                               "fwd_ret_pct": row["stk_ret"], "factors": meta["factors"],
                               "thesis": meta["thesis"], "horizon_days": 21})
    with direction.open("x", encoding="utf-8", newline="\n") as handle:
        for row in direction_rows:
            handle.write(json.dumps(row) + "\n")
    rows.append({"name": "direction-mature-outcomes", "state": "passed" if direction_rows else "failed",
                 "method": "existing backtest-prediction.grade over exact verified 21-interval outcomes",
                 "records": len(direction_rows), "source": str(offline), "artifact": str(direction)})
    if not direction_rows:
        return {"state": "failed", "scope": "listed-security-retrospective-calibration",
                "failed_step": "direction-mature-outcomes", "steps": rows, "omitted_instruments": omitted}
    # The scope and independent window checks are explicit, rather than allowing
    # the report's obsolete default JSONL to silently select old data.
    date = dt.date.today().isoformat()
    reports = run_dir / "wiki/maintenance/calibration"
    specs = [
        ("calibration-report", ROOT / "tools/calibration-report.py", ["--jsonl", str(direction)],
         [reports / ("calibration-" + date + ".md"), reports / ("calibration-" + date + ".json")]),
        ("confidence-map", ROOT / "tools/confidence-calibrator.py",
         ["--jsonl", str(offline), "--win-key", "beats_spy", "--horizon", "21"],
         [reports / "confidence-map.json", reports / "confidence-map-2026.md"]),
    ]
    for label, module_path, arguments, outputs in specs:
        command = [sys.executable, "-c", staged_report_script(module_path, run_dir, arguments)]
        row = step(command, run_dir, label, 90, [(p, None) for p in outputs])
        rows.append(row)
        if row["state"] != "passed":
            return {"state": "failed", "scope": "listed-security-retrospective-calibration",
                    "failed_step": label, "steps": rows, "omitted_instruments": omitted,
                    "publication": "withheld; inherited artifacts unchanged"}
    coverage = json.loads(Path(str(offline) + ".coverage.json").read_text())
    return {"state": "passed", "scope": "listed-security-retrospective-calibration",
            "steps": rows, "coverage": coverage, "omitted_instruments": omitted,
            "whole_corpus_state": "unavailable" if coverage["unavailable"] else "passed",
            "source_symbols": sorted(symbols), "evidence_class": "current-source retrospective computation",
            "publication": "versioned candidate; final financial report review still required",
            "limitations": ["Original grades retain their original version and cannot attest to full maturity.",
                            "Crypto and immature horizons remain in coverage as unavailable.",
                            "Current adjusted prices cannot prove historical publication-time availability.",
                            "Generated diagnostic prose is not an accepted independent financial review.",
                            "No inference of alpha, prospective eligibility or native model quality."]}


def refresh_owned_reindex_lock(path, owner_pid):
    """Renew only the running child owner's legacy TTL; never adopt another lock."""
    path = Path(path)
    with path.open("rb") as handle:
        value = handle.read(160)
    if not re.fullmatch(str(owner_pid).encode() + rb" \d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?Z\s*", value):
        raise OverlapError("external lock ownership changed")
    os.utime(path, None)


def external_utc(value):
    # Node's ISO timestamps include milliseconds; the financial scheduler's
    # intentionally second-resolution parser remains unchanged.
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?Z", value):
        raise ValueError("external timestamp must be explicit UTC")
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def reindex_pipeline(run_dir, base=None, node=None):
    base = Path(base) if base else Path.home() / ".vault-substrate"
    # Shared by every state directory; changing a diagnostic output path must
    # not create another permission to build the same external index.
    try:
        with job_lock(base / ".osanwe-reindex-observer.lock"):
            return observed_reindex_pipeline(run_dir, base, node)
    except OverlapError:
        return {"state": "unavailable", "reason": "external-reindex-already-running", "index_rebuilt": False}


def observed_reindex_pipeline(run_dir, base=None, node=None):
    """Observe admitted generation integrity without reading corpus text here.

    Scope/code approval remains a refusal gate. The Node --inspect path detects
    registry and approved source changes independently of Claude write hooks.
    """
    base = Path(base) if base else Path.home() / ".vault-substrate"
    node = Path(node) if node else Path(r"/path/to/program-files\nodejs\node.exe")
    runner = base / "reindex-runner.mjs"
    reviewed = {
        "indexer_sha256": base / "index-vault.mjs",
        "scope_module_sha256": ROOT / "tools/index-scope.mjs",
        "retrieval_core_sha256": ROOT / "tools/retrieval-core.mjs",
        "provider_sha256": base / "retrieval-provider.mjs",
        "runner_sha256": runner,
    }
    if not node.is_file() or any(not path.is_file() for path in reviewed.values()):
        return {"state": "unavailable", "reason": "external-retrieval-runtime-unavailable", "index_rebuilt": False}
    manifest = json.loads((ROOT / "config/scheduled-jobs.json").read_text(encoding="utf-8"))
    approval = next((j.get("indexer_scope_approval", {}) for j in manifest["jobs"]
                     if j["name"] == "osanwe-vault-reindex"), {})
    if any(approval.get(key) != file_sha(path) for key, path in reviewed.items()):
        return {"state": "unavailable", "reason": "external-indexer-scope-review-stale", "index_rebuilt": False}
    old_lock = base / ".reindex.lock"
    if old_lock.exists():
        with old_lock.open("rb") as stream:
            data = stream.read(160)
        owner = re.fullmatch(rb"([1-9][0-9]{0,9}) \d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?Z\s*", data)
        if not owner or process_exists(int(owner[1])) or now_utc().timestamp() - old_lock.stat().st_mtime < 1200:
            return {"state": "unavailable", "reason": "external-reindex-already-running", "index_rebuilt": False}
    run_dir.mkdir(parents=True, exist_ok=True)
    steps = []

    def observe(label, build=False):
        path = run_dir / (label + ".json")
        command = [str(node), str(runner)]
        if not build:
            command.append("--inspect")
        command += ["--receipt", str(path)]
        started = now_utc()
        result = step(command, run_dir, label, 3600 if build else 60,
                      [(path, "osanwe.retrieval-health/1")])
        steps.append(result)
        if result.get("reason") == "timeout" or artifact_state(path, started)["state"] != "passed":
            return {"state": "failed", "reason": "fresh-retrieval-receipt-missing", "needs_rebuild": False}
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            state = value.get("state")
            if (value.get("schema") != "osanwe.retrieval-health/1"
                    or state not in {"passed", "stale", "unavailable"}
                    or type(value.get("needs_rebuild")) is not bool
                    or not isinstance(value.get("reason"), str)
                    or not re.fullmatch(r"[a-z0-9-]{1,100}", value["reason"])
                    or result.get("exit_code") != {"passed": 0, "stale": 2, "unavailable": 3}[state]):
                raise ValueError("invalid retrieval receipt")
            stamp = external_utc(value["observed_at"])
            if not started - dt.timedelta(seconds=2) <= stamp <= now_utc() + dt.timedelta(seconds=2):
                raise ValueError("stale retrieval observation")
            if state == "passed":
                identifier = value.get("generation_id")
                if not isinstance(identifier, str) or not re.fullmatch(r"g-[a-zA-Z0-9_-]{1,100}", identifier):
                    raise ValueError("invalid generation id")
                expected = base / "index/generations" / identifier / "manifest.json"
                if value.get("receipt_path") is None or Path(value["receipt_path"]).resolve() != expected.resolve() or not expected.is_file():
                    raise ValueError("missing generation receipt")
                for name in ("document_count", "passage_count"):
                    if type(value.get(name)) is not int or value[name] <= 0:
                        raise ValueError("invalid scope counts")
            # Copy only safe metadata. No child-returned text/extra fields reaches
            # the scheduled receipt or downstream notification.
            return {key: value[key] for key in ("state", "reason", "needs_rebuild", "generation_id",
                    "observed_at", "receipt_path", "document_count", "passage_count") if key in value}
        except (OSError, ValueError, KeyError, TypeError):
            return {"state": "failed", "reason": "retrieval-receipt-invalid", "needs_rebuild": False}

    before = observe("retrieval-inspect")
    if not before.get("needs_rebuild"):
        return {**before, "steps": steps, "index_rebuilt": False,
                "scope": "admitted-public-synthetic-generation"}
    marker = base / ".debounce-marker"
    if marker.exists() and now_utc().timestamp() - marker.stat().st_mtime < 300:
        return {"state": "stale", "reason": "admission-pending-write-debounce", "steps": steps, "index_rebuilt": False}
    built = observe("admitted-reindex", build=True)
    if built["state"] != "passed":
        return {**built, "steps": steps, "index_rebuilt": False}
    after = observe("retrieval-post-build")
    changed = after.get("generation_id") != before.get("generation_id")
    verified = after["state"] == "passed" and after.get("generation_id") == built.get("generation_id") and changed
    return {**after, "state": "passed" if verified else "failed",
            "reason": "new-admitted-generation-verified" if verified else "fresh-generation-not-verified",
            "steps": steps, "index_rebuilt": verified, "scope": "admitted-public-synthetic-generation",
            "external_runner_sha256": file_sha(runner), "node_sha256": file_sha(node)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("job", choices=JOBS)
    ap.add_argument("--manual", action="store_true", help="diagnostic outside the scheduled opportunity denominator")
    ap.add_argument("--state-dir", type=Path, default=ROOT / ".agents/state/scheduled-jobs")
    args = ap.parse_args(argv)
    args.state_dir = args.state_dir.resolve()
    config = JOBS[args.job]
    journal = Journal(args.state_dir)
    try:
        with job_lock(args.state_dir / (args.job + ".lock")):
            at = now_utc()
            if args.job == "vault-reindex":
                slot = journal.reconcile_interval(config["name"], at)
            else:
                slot = journal.reconcile(config["name"], at, config["hour"], config["minute"], config.get("weekdays"))
                if slot is None:
                    previous = opportunities(at - dt.timedelta(days=8), at, config["hour"], config["minute"], config.get("weekdays"))
                    slot = iso_z(previous[-1]) if previous else None
            attempt = journal.begin(config["name"], slot, at, "manual" if args.manual else "scheduled")
            if attempt is None:
                print(json.dumps({"state": "unavailable", "reason": "current_slot_already_spent"}))
                return 2
            run_dir = args.state_dir / args.job / attempt["run_id"]
            run_dir.mkdir(parents=True, exist_ok=False)
            sources = scheduled_sources(config["name"])
            code_identity = {name: file_sha(ROOT / name) for name in sources}
            interpreter_identity = file_sha(sys.executable)
            try:
                result = {"nightly-health": health_pipeline, "weekly-calibration": calibration_pipeline,
                          "vault-reindex": reindex_pipeline}[args.job](run_dir)
            except Exception as exc:
                # Never persist raw exceptions/child streams, which may expose
                # a path or source payload. The exception type is sufficient.
                result = {"state": "failed", "reason": "pipeline-exception", "exception_type": type(exc).__name__}
            code_stable = code_identity == {name: file_sha(ROOT / name) for name in sources} and interpreter_identity == file_sha(sys.executable)
            if not code_stable:
                result["state"], result["reason"] = "stale", "executed-code-changed-during-run"
            receipt = {"schema": "osanwe.scheduled-job/1", "attempt": attempt,
                       "verified_at": iso_z(now_utc()), "python": sys.version.split()[0],
                       "executable_sha256": interpreter_identity, "code_identity": code_identity,
                       "code_unchanged_during_run": code_stable, **result}
            path = run_dir / "receipt.json"
            create_json(path, receipt)
            journal.finish(attempt, now_utc(), receipt["state"], path)
            print(json.dumps({"state": receipt["state"], "evidence": str(path),
                              "scope": receipt.get("scope"), "whole_corpus_state": receipt.get("whole_corpus_state"),
                              "reason": receipt.get("reason"), "failed_step": receipt.get("failed_step")}))
            return 0 if receipt["state"] == "passed" else 1
    except OverlapError:
        print(json.dumps({"state": "unavailable", "reason": "overlap_refused"}))
        return 2
    finally:
        journal.close()


if __name__ == "__main__":
    raise SystemExit(main())
