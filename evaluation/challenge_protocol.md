---
aliases: []
categories: [decisions]
status: active
created: 2026-08-25
updated: 2026-09-13
tags: [fis]
related: ["[[phase-i-freeze-manifest]]"]
---

# Evaluation Challenge Protocol

Status: ACTIVE; original strategy backend NOT CONNECTED. Separate reasoning
service implemented and development-tested; independent deployment pending.
Created: 2026-08-25

Current reasoning interface: `evaluation/request_access.py reasoning` forwards
to the submission-only Worker client. Its case inputs are deliberately issued
after durable reservation; its hidden grading material is never disclosed.
The current contract and limits are in [[REASONING-EVALUATOR]] and
`evaluation/reasoning_protocol.json`. No reasoning task reuses, opens or weakens
the original strategy holdout below. Local tests and public cases are development
evidence, not independence or strategy-promotion evidence.

Original strategy implementation: the gateway refuses real evaluation with
`backend_unavailable` and exits nonzero. It does not open locked data or
return a synthetic accuracy as a model result. A reviewed isolated model
adapter remains required before any holdout evaluation can occur.
Historical scores produced by the earlier unwired placeholder are not model-quality
evidence. Preserve their logs for audit; do not treat them as a valid baseline or
promotion receipt. Real evaluator results require an identified reviewed backend.

## Original strategy holdout rules (retained)

1. **The holdout dataset is LOCKED.** No agent, process, or human may read,
   copy, move, or modify the holdout data directly.

2. **Research agents cannot access the holdout directly.** Any attempt to
   bypass the interface is a protocol violation and must be logged and
   reported.

3. **Access is via the controlled interface only**
   (`evaluation/request_access.py` -> `tools/eval-interface.py`). All
   evaluation traffic flows through this single gateway.

4. **Max 3 evaluations per unregistered hypothesis.** A hypothesis that has
   not been preregistered in `registry/experiment_ledger.jsonl` gets at
   most 3 queries through the interface.

5. **After 5 total queries on a hypothesis, a new hypothesis must be
   preregistered.** Continued querying of the same hypothesis past 5
   cumulative queries is blocked by the interface.

6. **Every accepted or refused request is logged** to `evaluation_log.jsonl`
   before a response is released. Refused requests carry an outcome and do
   not consume the metric-release budget. Legacy log rows without the new
   `budget_consumed` field still count as evaluations. If audit storage is
   unavailable or another process holds the lock, the interface refuses
   without evaluating and reports `audit_logged: false`; it cannot promise
   an audit write that failed. An existing lock is never stolen automatically.

7. **A nonblank hypothesis ID is required.** Historical empty IDs and
   `(none)` share one counting key; new requests cannot use that reserved
   key. Only the latest ledger status `preregistered` grants the registered
   budget. A later rejection or revocation removes that privilege.

### Log format (one JSON object per line)

```
{"timestamp": "<UTC ISO-8601>", "agent_id": "<agent>", "hypothesis_id": "<id>", "metrics_returned": <count-or-summary>}
```

## What the interface returns

When a reviewed evaluator is connected: only aggregate metrics (e.g.,
accuracy, loss, per-bucket aggregates). Until then: a typed refusal and no
metrics. The caller cannot supply a predictor callback that receives
locked records or labels.
Raw holdout records, labels, and feature values are never exposed.

Control verification: `python tools/test-eval-interface.py`. This suite uses
temporary metadata and mocked aggregate results only; it does not establish
model quality, holdout performance, or evaluator isolation.

## Registration flow

1. Write the hypothesis to `registry/experiment_ledger.jsonl`
   (one JSON line: `hypothesis_id`, `description`, `author`, `date`,
   `status: "preregistered"`).
2. Run evaluations via the controlled interface.
3. Unregistered hypotheses are capped at 3 queries; registered hypotheses
   are capped at 5 before a new hypothesis is required.
