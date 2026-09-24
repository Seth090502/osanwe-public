---
categories: [wiki]
status: active
created: 2026-08-17
updated: 2026-08-17
---

# Frontier protocol -- insider-sweep-held (FROZEN 2026-08-17)

Arm: Fable-direct, n=1, run the SAME EVENING as the worker arms (live data).

1. Using the openinsider MCP directly (same allowlist, <= 24 calls), answer the
   three mission questions for the configured ticker list: latest Form 4 trades,
   cluster buys (90d), short interest + days-to-cover.
2. Emit a claims JSON file: `{"claims": [...]}` in the relay 8-field shape
   (entity, metric, value, date, grade, section, text, prov) -- prov `mcp:openinsider:<tool>`.
   One claim per figure, exact values as returned, date every dated figure.
3. This claim set IS the reference for the worker arms (grading.reference =
   frontier). Save to `.claude/state/parity/insider-sweep-held/frontier.json`
   and log the run: `python tools/parity-eval.py --log-run --task
   insider-sweep-held --arm frontier --run <label> --status complete`.
4. Record the session's token cost via claudewatch get_cost_attribution into
   the run log (F-8 session-level share source).
