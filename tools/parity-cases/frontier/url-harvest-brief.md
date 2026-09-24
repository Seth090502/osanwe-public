---
categories: [wiki]
status: active
created: 2026-08-17
updated: 2026-08-17
---

# Frontier protocol -- url-harvest-brief (FROZEN 2026-08-17)

Arm: Fable-direct, n=1, SAME EVENING as the worker arms (live web data).

1. WebFetch the two frozen seeds (stockanalysis.com nvda + mu; same fallback
   rules as the worker: curl -sk on SSL failure, one retry) and answer the
   mission questions: market cap, P/E, revenue TTM, EPS TTM, 52-week range,
   next earnings date per ticker.
2. Emit `{"claims": [...]}` (8-field shape, prov `web:<url>`) AND a 5-8
   sentence narrative brief in a sibling `frontier-narrative.txt`.
3. Claims = reference for the mechanical 80% of this task. The narrative
   feeds the judged 20%: `python tools/parity-eval.py --blind-pack --task
   url-harvest-brief` packs worker + frontier narratives under sealed labels
   for blind grading (mapping written sealed; prose-fingerprint caveat is
   named in the rule doc).
4. Save to `.claude/state/parity/url-harvest-brief/frontier.json`; log run +
   claudewatch cost attribution.
