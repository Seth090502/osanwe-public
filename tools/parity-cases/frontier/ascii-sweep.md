---
categories: [wiki]
status: active
created: 2026-08-17
updated: 2026-08-17
---

# Frontier protocol -- ascii-sweep (FROZEN 2026-08-17)

Arm: Fable-direct, n=1. Hermetic fixture tree -- timing free.

1. Read the three files in `tools/parity-cases/fixtures/editor-tree/` and
   emit proposals in the propose_edit shape as JSON:
   `{"proposed_edits": [{"path", "old", "new", "why"}...]}` -- one per
   non-ASCII body defect (em-dash -> --, curly quote -> straight); an empty
   list entry per clean file is recorded as a negative claim. Do NOT touch
   frontmatter fields; do NOT read the answer key.
2. Save to `.claude/state/parity/ascii-sweep/frontier.json`; log run +
   claudewatch cost attribution. Grading: recall of planted defects x
   apply-clean x clean-file negatives, vs the key, both arms.
