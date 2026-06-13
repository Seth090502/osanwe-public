---
categories: [meta]
type: threat-model
status: active
created: 2026-05-11
updated: 2026-06-11
tags: []
aliases: []
related: []
---
# Threat model v2: PII boundary for the public variant

Records the explicit in-scope vs out-of-scope decisions for what propagates
from the private vault to this public repo, and the mechanisms that enforce
the boundary. v2 (2026-06-11) supersedes the v1 mirror model: the repo is no
longer a redacted *mirror* of vault content -- it is a *framework variant*
with a fictional DEMO seed, which shrinks the leak surface structurally
instead of relying on redaction reliability.

## In scope (what the boundary protects)

### Personal-financial data
- Brokerage + retirement share counts, cost basis, P&L history
- Portfolio totals, position sizes, concentration percentages
- Ratified doctrine numbers (thesis caps, single-name ceilings, R/R hurdle,
  sleep-gate threshold) -- v2 ships these as `USER_SET` placeholders only
- Real thesis essays and per-position analyses
- Standing per-asset caveats that reveal account history
- Wage rate, employer name, income figures

### Biometric / medical data
- Lab values, anthropometrics, active protocols (doses, schedules, start
  dates), medical history, personal health narrative
- v2 additionally renamed framework write-targets that embedded a drug name

### Identity + location
- Legal name (EXCEPTION: the LICENSE copyright line is deliberate public
  attribution), email/GitHub handles, city/ZIP, age/DOB, household
- Absolute filesystem paths (username + machine layout) -- v2 parameterizes
  every path (`$CLAUDE_PROJECT_DIR`, `VAULT_ROOT`, `~`)

### Operational
- Real daily notes, decision-log, sessions-log, briefings, retrospectives
- Application packets (resume-derived -- wholesale excluded in v2)
- Calibration rows with real tickers/returns (v2 ships `-DEMO` rows only)
- Runtime state: `.claude/state/`, telemetry sinks, bypass logs, fill caches,
  transcripts, memory directories
- The private master-context document and every derivative of it
- **The sanitization secrets-map itself**: the live denylist, the scrub spec,
  remediation manifests, and vault tree snapshots all *embed* the secrets
  they guard (the denylist paradox). v2 untracked all of them; only
  structural examples ship. See `.audit/README.md`.

## Out of scope (what the repo deliberately publishes)

- The full framework: 22 skills, 20 subagents, 13 hooks, 4 dynamic
  workflows, ~36 tools, the substrate scripts, the dual-engine generators
- The prevention architecture and its T1-T38 adversarial harness
- The doctrine TEMPLATE (structure + design principles, zero ratified values)
- The fictional DEMO seed (orbital-compute thesis, `-DEMO` entities,
  synthetic figures that collide with no real vault figure)
- The sanitization toolchain (scanner, sanitizers, assertions, verifier)
  with example denylist + fake-values fixtures
- Methodology references (`Atlas/sources/meta/`) and generic sports
  biomechanics references (`Atlas/sources/golf/`), scrubbed
- Mission case studies written at architecture level

## Enforcement mechanisms (defense in depth)

1. **Allowlist copying.** Nothing enters the tree except what a build layer
   explicitly approves. Never copy-all-then-delete: a missed exclusion is a
   leak; a missed inclusion is a harmless gap.
2. **Scrub spec at copy time.** Every copied file passes through identity /
   medical / figure / doctrine / path transform rules; doubt -> exclude.
3. **Denylist scanning** (`.audit/check-pii.py`): regex categories over
   `.md .py .sh .ps1 .txt .json .yaml .yml .js .mjs .vbs .base .toml`
   (extension set widened in v2 -- v1 never scanned workflows or substrate
   scripts). Zero hits required per layer and at the final gate.
4. **Structural exclusion assertions** (`.audit/assert-exclusions-v2.py`):
   25 absence proofs over the *tracked* tree (personal layers, local files,
   state, logs, secrets-map files) plus DEMO-marking assertions on every
   real-content carrier. Runs in CI.
5. **Real-figure collision sweep.** Demo figures are checked against
   live-sampled private-vault figures; no synthetic value may equal a real
   one.
6. **3-layer pre-push verifier** (`.audit/pre-push-verify.ps1`): denylist
   scan + exclusion assertions + vault-audit floor + literal sweep.
7. **Fresh-root export rule.** Working history contains pre-redaction
   content by construction. Publication is only ever a fresh root commit
   (orphan branch / `git archive`) of the verified tree -- never a push of
   the working branch. This is the single most important rule in this file.

## Known limitations

- Regex sanitization cannot catch every paraphrase of PII; the structural
  shift to a fictional seed (v2) is the mitigation, not better regexes.
- Scrubbed skill bodies still describe *workflow shape* (that the author
  tracks a portfolio, health protocols, golf practice). The framework's
  domain coverage is itself a mild profile signal -- accepted as the cost of
  publishing a real system.
- The LICENSE carries deliberate name attribution; combined with the repo
  topic this links the author to the framework. Accepted by choice.
- Demo figures were checked against a finite live sample of real figures,
  not every number that ever existed in the private vault.

If you spot a residual PII leak, open an issue tagged `[pii-report]`. The
maintainer will fix, run the FULL re-sweep (never incremental), and re-export.
