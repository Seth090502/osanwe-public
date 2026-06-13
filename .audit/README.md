---
categories: [meta]
type: reference
status: active
created: 2026-06-11
updated: 2026-06-11
tags:
  - topic/sanitization
aliases: []
related: []
---

# .audit -- public-mirror sanitization toolchain

The pipeline that produced this public repo from a private vault, shipped so
you can run the same discipline on your own fork. Three principles:

1. **Allowlist copying only.** Copy what a layer explicitly approves; never
   copy-all-then-delete (a missed exclusion is a leak; a missed inclusion is
   a harmless gap).
2. **Fail-closed verification.** Any hit -> fix -> FULL re-sweep, never an
   incremental pass over just the fixed file.
3. **The denylist paradox.** Your real denylist embeds your real secrets
   (figures, employer, location). It stays gitignored forever; only the
   structural example ships.

## Toolchain

| File | Role |
|---|---|
| `check-pii.py` | Scan a tree against a denylist (regex categories); exit 1 on any hit; JSON hit log |
| `denylist-example.txt` | Structural template -- copy to `denylist-v1.txt` (gitignored), fill your values |
| `test-fixture-pii-example.md` | Positive control -- must trip every configured category |
| `test-fixture-clean.md` | Negative control -- must produce zero hits |
| `sanitize.py` / `sanitize-batch.py` | Category->marker redaction over a file / tree mirror |
| `wikilink-rewriter.py` | Rewrite wikilinks whose targets were excluded from the mirror |
| `entity-section-strip.py` | Strip position-data sections from entity notes |
| `diff-tree.py` / `diff-baseline.py` | Pre/post tree + capability-count regression checks |
| `assert-exclusions-v2.py` | Prove the TRACKED tree contains no excluded class (run in CI) |
| `pre-push-verify.ps1` | Final 3-layer gate: PII scan + vault-audit + literal sweep |

## Workflow (publishing your own fork)

1. Author your gitignored `denylist-v1.txt` from the example; extend the
   positive-control fixture to match.
2. Smoke test: `python .audit/check-pii.py .audit/test-fixture-pii-example.md
   .audit/denylist-v1.txt` must FAIL (hits in every category);
   `...test-fixture-clean.md...` must PASS.
3. Sanitize content layer by layer (allowlist copying), running
   `check-pii.py` per layer.
4. `python .audit/assert-exclusions-v2.py` -- structural absence proof.
5. `powershell .audit/pre-push-verify.ps1` -- final gate.
6. **Never push working history.** Export the verified tree as a fresh root
   commit (orphan branch); interim commits may contain pre-redaction content.
