---
categories: [wiki]
status: active
created: 2026-08-17
updated: 2026-08-17
---

# Frontier protocol -- doc-extract-earnings (FROZEN 2026-08-17)

Arm: Fable-direct, n=1. Hermetic fixture -- timing free.

1. Read `tools/parity-cases/fixtures/earnings-release.md` ONCE and extract
   every financial figure into `{"claims": [...]}` (8-field shape, prov
   `file:earnings-release.md`), exact values as printed, entity MRSD.
   Do NOT read the answer key (`fixtures/answer-keys/doc-extract-earnings.json`)
   -- grading is vs the key for BOTH arms; parity = score ratio.
2. Save to `.claude/state/parity/doc-extract-earnings/frontier.json`; log run
   + claudewatch cost attribution.
