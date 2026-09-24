---
categories: [wiki]
status: active
created: 2026-08-17
updated: 2026-08-17
---

# Frontier protocol -- insider-sweep-screen (FROZEN 2026-08-17)

Arm: Fable-direct, n=1, SAME EVENING as the worker arms (live data).

1. Using the openinsider MCP directly (<= 16 calls), answer the mission
   questions: top insider buys (30d), top sells (30d), cluster buys (30d);
   cap at the 15 largest rows per screen.
2. Emit `{"claims": [...]}` in the relay 8-field shape, prov
   `mcp:openinsider:<tool>`, one claim per row (insider, ticker, role, value,
   date encoded in metric/value/text).
3. Save to `.claude/state/parity/insider-sweep-screen/frontier.json`; log the
   run via parity-eval.py --log-run; record claudewatch cost attribution.
