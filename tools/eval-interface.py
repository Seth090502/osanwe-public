#!/usr/bin/env python3
"""Controlled holdout gateway. Real evaluation is unavailable until wired.

This interface does not open the locked dataset or manufacture model scores.
Successful metric releases consume the hypothesis budget; refused requests
are audited separately. All budget checks and audit writes share one lock.
"""

import argparse
from contextlib import contextmanager
import json
import os
import sys
from datetime import datetime, timezone

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.join(VAULT, "evaluation", "evaluation_log.jsonl")
LEDGER_PATH = os.path.join(VAULT, "registry", "experiment_ledger.jsonl")
MAX_UNREGISTERED_QUERIES = 3
MAX_TOTAL_QUERIES = 5
UNSPECIFIED_HYPOTHESIS = "(none)"


class EvaluationRefused(Exception):
    """A typed refusal that must not be represented as a model result."""

    def __init__(self, code, detail):
        self.code = code
        self.detail = detail
        super().__init__(detail)


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_hypothesis(value):
    """Map old empty IDs and their logged sentinel to the same budget key."""
    return str(value or "").strip() or UNSPECIFIED_HYPOTHESIS


def read_records(path):
    if not os.path.exists(path):
        return []
    records = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise EvaluationRefused(
                    "audit_state_invalid", "Malformed evaluation control state; evaluation refused."
                ) from exc
            if not isinstance(record, dict):
                raise EvaluationRefused(
                    "audit_state_invalid", "Non-object evaluation control record; evaluation refused."
                )
            records.append(record)
    return records


def count_queries(hypothesis_id):
    key = normalize_hypothesis(hypothesis_id)
    # Legacy entries represented completed evaluations and lacked this flag.
    return sum(
        normalize_hypothesis(record.get("hypothesis_id")) == key
        and record.get("budget_consumed", True) is True
        for record in read_records(LOG_PATH)
    )


def is_registered(hypothesis_id):
    key = normalize_hypothesis(hypothesis_id)
    if key == UNSPECIFIED_HYPOTHESIS:
        return False
    status = None
    for record in read_records(LEDGER_PATH):
        if normalize_hypothesis(record.get("hypothesis_id")) == key:
            status = record.get("status")
    # A later rejection/revocation supersedes an earlier preregistration.
    return status == "preregistered"


def evaluate(model_id, holdout_path, predict_fn=None):
    """Refuse until a reviewed isolated evaluator adapter is implemented.

    A callable supplied by the researcher is not an evaluator boundary: it
    could inspect labels. Retain the old signature only to refuse old callers
    explicitly. Neither holdout bytes nor callback code are accessed here.
    """
    raise EvaluationRefused(
        "backend_unavailable",
        "No reviewed model evaluator is connected. No holdout was opened, "
        "no model was run, and no accuracy or validation result exists.",
    )


@contextmanager
def query_lock():
    """Serialize processes; a stale lock fails closed instead of being stolen."""
    path = LOG_PATH + ".lock"
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise EvaluationRefused(
            "gateway_busy", "Evaluation audit lock exists; no evaluation was attempted."
        ) from exc
    os.close(descriptor)
    try:
        yield
    finally:
        os.unlink(path)


def log_query(agent_id, hypothesis_id, metrics=None, *, outcome="evaluated", model_id=None):
    entry = {
        "timestamp": utc_now(),
        "agent_id": agent_id,
        "model_id": model_id,
        "hypothesis_id": normalize_hypothesis(hypothesis_id),
        "outcome": outcome,
        "budget_consumed": outcome == "evaluated",
        "metrics_returned": list(metrics) if metrics else [],
    }
    with open(LOG_PATH, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return entry


def run_request(args):
    """Return only aggregates or a typed refusal; audit before releasing either."""
    key = normalize_hypothesis(args.hypothesis_id)
    try:
        with query_lock():
            try:
                if key == UNSPECIFIED_HYPOTHESIS:
                    raise EvaluationRefused("hypothesis_required", "Supply a nonblank hypothesis ID.")
                if not args.model_id.strip() or not args.agent_id.strip():
                    raise EvaluationRefused("identity_required", "Supply nonblank model and agent IDs.")
                prior = count_queries(key)
                registered = is_registered(key)
                cap = MAX_TOTAL_QUERIES if registered else MAX_UNREGISTERED_QUERIES
                if prior >= cap:
                    raise EvaluationRefused("query_limit_exceeded", "Hypothesis evaluation budget exhausted.")
                metrics = evaluate(args.model_id, args.holdout)
                if not isinstance(metrics, dict) or not metrics:
                    raise EvaluationRefused("invalid_evaluator_result", "Evaluator returned no aggregate result.")
                entry = log_query(args.agent_id, key, metrics, model_id=args.model_id)
                return {
                    "status": "evaluated", "model_id": args.model_id,
                    "hypothesis_id": key, "hypothesis_registered": registered,
                    "queries_used": prior + 1, "query_cap": cap,
                    "metrics": metrics, "logged_at": entry["timestamp"],
                }, 0
            except EvaluationRefused as exc:
                log_query(args.agent_id, key, outcome=exc.code, model_id=args.model_id)
                return {"status": "refused", "error": exc.code, "detail": exc.detail}, 2
    except EvaluationRefused as exc:
        # With a busy lock it is unsafe to append concurrently; disclose that.
        return {"status": "refused", "error": exc.code, "detail": exc.detail,
                "audit_logged": False}, 2
    except OSError:
        return {"status": "refused", "error": "audit_unavailable",
                "detail": "Evaluation audit could not be committed; no metrics released.",
                "audit_logged": False}, 2


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "reasoning":
        # New reasoning task inputs are explicitly disclosed by the server after
        # reservation. This does not open or reuse the original strategy holdout.
        import runpy
        client = runpy.run_path(os.path.join(VAULT, "evaluation", "reasoning_client.py"))
        return client["main"](argv[1:])
    parser = argparse.ArgumentParser(description="Controlled holdout gateway (evaluator not connected)")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--hypothesis-id", required=True)
    parser.add_argument("--holdout", default=os.path.join(VAULT, "evaluation", "holdout", "holdout.jsonl"))
    result, code = run_request(parser.parse_args(argv))
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
