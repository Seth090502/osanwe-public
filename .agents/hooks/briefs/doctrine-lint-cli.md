# Porting brief: doctrine-lint CLI (doctrine tamper-evidence gate)

COLD BRIEF -- written without sight of the manifest test blocks; the executable `test:` in
`.agents/hooks/manifest.yaml` is the acceptance criterion, not this prose. Criticality: SAFETY-CRITICAL
-- the anti-tamper layer under every sizing and concentration number. Portable: YES (harness-neutral
CLI; wire it, do not rewrite it).

## (a) What the gate must guarantee

The machine-readable doctrine blocks that drive position sizing and concentration must AGREE with the
human prose around them, must be EVIDENCED by verbatim quotes from cited sources, and must be RATIFIED
by a decision record. A silent edit to any doctrine number -- even one that also updates the prose and
re-fingerprints -- fails until a decision record registers the new fingerprint. Two blocks are covered:
`doctrine:` in `ref-portfolio-doctrine.md` and `bands:` in `ref-scoring-models.md`. The operational
rule enforced (AGENTS.md): to change a doctrine value you edit the REF NOTE, re-fingerprint, and ratify
via a decision record -- never the consuming skill, because the lint fails closed on tamper.

## (b) Reference implementation + load-bearing facts

Reference: `tools/doctrine-lint.py` (167 lines) + `tools/kernel_lib.py`. Cross-harness entry point
`.agents/scripts/gates/doctrine-lint.py` resolves the repo root from its own location, sets `VAULT_ROOT`
if unset, delegates argv verbatim. Deps: stdlib + PyYAML + kernel_lib.

Eight checks run per block; ANY failure exits 2.
  A. schema valid (`kernel_lib.validate_block_schema`).
  B. every lintable scalar leaf has a provenance-table row in the host note, shaped
     `| key | value | verbatim_quote | source |`.
  C. the table value EQUALS the block value (numeric tolerance 1e-9; booleans compare as literal
     true/false; strings compare normalized and casefolded).
  D. the verbatim quote is a LITERAL SUBSTRING of its cited source file (`self` = the host note,
     otherwise `Calendar/decisions/<stem>.md`).
  E. the block value is EVIDENCED INSIDE that quote (numeric parse or substring).
  F. table rows whose keys are absent from the block are flagged (table drift).
  G. the recomputed fingerprint EQUALS the block's registered `fingerprint:` field.
  H. that registered fingerprint appears in at least one `Calendar/decisions/decision-*.md`.

1. CHECK D IS LITERAL-SUBSTRING, NOT SEMANTIC. Paraphrase fails -- same discipline as the Grade-A
   evidence rule elsewhere in the vault: a quote slot holds quoted bytes or it holds a defect. Check E
   then closes the loophole where a REAL quote is cited that does not contain the number.
2. CHECK H IS WHAT MAKES RE-FINGERPRINTING INSUFFICIENT. Without H, an attacker (or a careless agent)
   edits the value, edits the prose, recomputes the fingerprint, and everything is internally
   consistent. H forces an external, dated, human-ratified artifact into the loop.
3. EXIT CODES: **0 = clean, 2 = findings (fail-closed)**. There is no exit 1; treat any nonzero as a
   block. `--fingerprint` is a CHANGE HELPER that prints recomputed fingerprints, validates nothing,
   and ALWAYS exits 0 -- never wire it as the gate invocation.
4. IT IS A PRE-STEP, NOT A STANDALONE RITUAL: it runs standalone, from `tools/sizing-eval.py` as a
   fail-closed pre-step, from `tools/test-sizing-eval.py`, and at the analysis skill's doctrine-load
   phase. A port must preserve "sizing refuses to compute while doctrine is unlinted".
5. `--doctrine-file PATH` / `--bands-file PATH` are TEST OVERRIDES -- conformance fixtures use them
   instead of mutating live ref-notes. ASCII-only (Pattern 22) binds the output and the linted notes.

## (c) Where to bind it

Not a lifecycle hook -- a CLI: `python .agents/scripts/gates/doctrine-lint.py [--json] [--fingerprint]
[--doctrine-file P] [--bands-file Q]`. Harness binding, strongest first: (1) `pre-tool-use (blocking)`
on file writes -- refuse any write targeting either doctrine ref-note unless the operator has
deliberately armed the edit (the arm-and-consume pattern guard-paths uses for config), then re-lint
after; (2) `post-tool-use` -- lint after any write under the ref-note directory and surface findings as
a blocking report (per `.agents/hooks/README.md`, Crush does NOT intercept PostToolUse: state that loss
rather than silently dropping it); (3) `session-start` -- a tripwire making a tampered block visible
before work begins (weakest: it detects, it does not prevent).

## (d) Input shape

No stdin. Inputs are files resolved under `VAULT_ROOT`: the two ref-notes (markdown, each with a YAML
machine block plus a provenance table in the body) and the `Calendar/decisions/decision-*.md` corpus
for check H. Output: human-readable finding lines by default, structured findings under `--json`;
findings are prefixed with the block kind, e.g. `[doctrine] ...` / `[bands] ...`.

## (e) Non-goals and known residuals

- It lints AGREEMENT and PROVENANCE, not correctness. It cannot tell you that a 50% ceiling is the
  right ceiling; it tells you the block value, table value, quoted value, and ratifying decision match.
- It does not enforce doctrine at execution time -- that is the pretrade gate CLI, which holds its own
  copy of the ceilings as constants. Keeping those constants and the ref-note in sync is a REVIEW
  obligation this lint does NOT check: a known residual worth naming in any conformance record.
- It does not run the sizing math (`tools/sizing-eval.py` does) and writes no decision records. No
  network, no MCP, no model call -- a lint whose verdict depends on a model is not tamper evidence.
