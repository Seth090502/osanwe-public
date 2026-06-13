<h1 align="center">osanwe-public</h1>

<p align="center">
  <b>A financial-assistant framework built on compounding knowledge</b><br />
  the public-safe engine of a personal Obsidian + Claude Code vault.
</p>

<p align="center">
  <a href="https://github.com/Seth090502/osanwe-public/actions/workflows/vault-prevention.yml"><img src="https://github.com/Seth090502/osanwe-public/actions/workflows/vault-prevention.yml/badge.svg" alt="CI" /></a>
  <img src="https://img.shields.io/badge/vault--audit-95%2F100-brightgreen" alt="vault-audit 95 of 100" />
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT License" />
  <img src="https://img.shields.io/badge/built%20for-Claude%20Code-8A63D2" alt="Built for Claude Code" />
</p>

---

The architecture is the artifact. The personal layer -- holdings, identity, risk
ceilings, medical context -- lives in gitignored files you create yourself; what
ships here is the engine, the patterns, and the discipline, plus a small
fictional DEMO seed so the repo's own quality gates run green out of the box.

## Five things that distinguish this from a folder of prompts

**1. Dual-topology orchestration.** The heavy skills (`/invest`, `/spark`)
carry two execution spines: a deterministic fan-out layer
(`.claude/workflows/*.js` -- parallel research workers, convergence gates,
structured-output contracts, fan-out capped at 6) and a sequential fallback
that is always valid. Topology is detected at runtime and logged passively on
every rated output; no skill ever conditions behavior on model identity.

**2. Adversarial verification waves.** Analysis is cheap; surviving
refutation is the product. `/spark` routes every qualifying pattern through a
4-lens verifier (evidence / falsifiability / novelty / mundane-alternative),
fail-closed: a verifier that fails to return a valid contract counts as a
refutation. `/invest` runs a skeptic wave (data-integrity, risk/reward,
routing, provenance) before anything is written. Refuted findings are dropped
transparently, never silently.

**3. Prediction scoring + calibration loop.** Every `/invest` verdict appends
a row to `wiki/investing/calibration-monitor.md` (rating, shadow rating,
conviction %, R/R, topology). `tools/score-outcomes.py` backfills realized
1/3/6-month returns and computes rolling Brier scores -- new logic vs shadow
logic, pooled and topology-stratified -- against a pre-committed rollback
trigger. `tools/reconcile-orders.py` cross-checks broker fills against
decision records: a fill with no decision record is, by definition, the FOMO
pattern the architecture exists to catch. `/spark` makes vault-observable
falsifiable predictions and scores its own past predictions on every run.

**4. Semantic retrieval substrate.** A local HNSW vector index
(bge-base-en-v1.5 ONNX, dim 768) over the agent-written layers, living
out-of-tree at `~/.vault-substrate/`. Scripts ship in `substrate/`; wiring is
a UserPromptSubmit hook that injects top-K chunks, a debounced incremental
reindexer with lockfile + atomic swap, and Phase 0 skill-level retrieval in
the five analytical skills. Notes you wrote weeks ago resurface exactly when
a prompt touches them.

**5. A mechanically enforced 95/100 quality floor.** Quality is not a habit
here; it is a hook chain. `pre-write-validator.py` simulates every proposed
write against the audit engine and blocks GATE-class regressions BEFORE they
reach disk; an 11-position PostToolUse chain validates what lands; the
auto-commit gate refuses to commit gate findings. `tools/vault-audit.py`
scores the tree across 12 classifiers (3 GATE, 4 HARD DRIFT, 5 SOFT DRIFT) with
tier-weighted severities (GATE -5/finding with a 90-point hard cap, HARD
DRIFT -1 capped at -5, SOFT advisory). The whole stack is regression-tested
by `tools/test-prevention-arch.sh` -- **38 adversarial tests, T1-T38, all
passing on this public tree** -- and CI enforces the floor on every push.

## What's in the repo

- **22 skills** under `.claude/skills/` -- the analytical core (`/brief`
  morning briefing, `/invest` multi-phase ticker analysis, `/networth`,
  `/challenge`, `/decide`, `/spark`, `/deep`), the vault machinery
  (`/enrich`, `/ingest`, `/retro`, `/vault`, `/consolidate`, `/telemetry`,
  `/tasks`, `/create-skill`), domain advisories (`/career`, `/health`,
  `/golf`), a mass-document pipeline (`/corpus`), and dev utilities
  (`/diagnose`, `/tdd`, `/caveman`). Inventory + write-targets in `CLAUDE.md`.
- **20 subagents** under `.claude/agents/` -- read-only research workers
  (price-fetcher, forensic-scorer, institutional-positioning-scout,
  thesis-critic, claim-distributor, pattern-class-scout, ...) plus coding
  agents. Mandatory-dispatch wiring documented per skill phase.
- **4 dynamic workflows** under `.claude/workflows/` -- `invest-research`,
  `invest-verify`, `spark-sweep`, `spark-verify`.
- **13 hook scripts** under `.claude/hooks/` (plus the `tools/` validators), registered in `.claude/settings.json` across 10 event types,
  paths parameterized via `$CLAUDE_PROJECT_DIR`. Broker order tools are
  mechanically denied in `permissions.deny`.
- **~36 tool files** under `tools/` (32 Python/shell + reference docs) -- the audit engine, the
  prevention harness, the calibration loop, dual-engine Codex generators
  (`sync-skills.py`, `gen-codex-agents.py`, `gen-codex-config.py`; see
  `docs/CODEX-COMPATIBILITY.md`), price fetching with extended-hours support,
  telemetry analysis, and the F11 atomic-commit orchestrator library.
- **The sanitization pipeline** under `.audit/` -- the toolchain that
  produced this repo from the private vault (denylist scanner, batch
  sanitizer, structural exclusion assertions, 3-layer pre-push verifier),
  shipped so you can run the same discipline on a fork. See
  `.audit/README.md`, including the denylist paradox and the
  fresh-root-export rule.
- **A fictional DEMO seed** -- an `orbital-compute` demo thesis (orbital data
  centers; deliberately fictional), three `-DEMO` ticker entities, one demo
  analysis, a calibration-monitor schema seed, a 9-section daily note, and a
  schema-valid `wiki/hot.md`. Every demo figure is synthetic. The seed exists
  so the repo's own `vault-audit.py` scores >= 95 with zero broken links and
  the schemas have living examples.

## Architecture in four layers

**Atlas** is human-write-only: timeless concepts, reference docs, Maps of
Content. The doctrine lives here as a template --
`Atlas/concepts/investing/doctrine.template.md` -- with every personal risk
number (`THESIS_CAP_AMBER/RED`, `SINGLE_NAME_AMBER/RED`, `RR_HURDLE`,
`SLEEP_GATE_THRESHOLD`, exit-ladder triggers) as a `USER_SET` placeholder you
ratify yourself. Skills read the placeholders by name.

**wiki** is the agent-synthesis layer: entity notes with per-fact provenance
and claim-to-section mappings, dated analyses (new-file-per-run, never
overwritten), the calibration monitor, and `wiki/hot.md` -- the
session-continuity cache validated by its own schema checker.

**Calendar** is the operational log: 9-section daily notes, append-only
decision-log and sessions-log, dated briefings.

**Efforts** is deadline-bound work (career search, health protocol, practice
logs) -- created by the skills on first use; intentionally absent here.

The separation dictates write discipline: skills write wiki/Calendar/Efforts;
Atlas writes require human confirmation; `private/` and `.raw/` are blocked
by a PreToolUse path guard. Atomic multi-file skill commits run under the F11
suppression flag with narrow staging (never `git add -A`) and a pre-commit
audit gate.

## Getting started

1. Clone; open in Obsidian (optional) and Claude Code.
2. Read `CLAUDE.md` -- it is the operating constitution.
3. Create your personal layer: `CLAUDE.local.md` + `private/` files (see
   CLAUDE.md "Personal Context"; all gitignored).
4. Copy `Atlas/concepts/investing/doctrine.template.md` values into ratified
   numbers; author your first thesis from `_templates/thesis.md`.
5. Optional: set up semantic retrieval per `substrate/` (out-of-tree index).
6. Run the gates yourself: `bash tools/test-prevention-arch.sh` (expect
   38/38), `python tools/vault-audit.py --json` (expect >= 95, gate 0),
   `python .audit/assert-exclusions-v2.py` (expect PASS).
7. Replace the DEMO seed with real work; the hooks take it from there.

## How to read this codebase

Start with `CLAUDE.md`, then
`Atlas/sources/meta/ref-execution-discipline.md` (F11 atomic-commit
discipline) and `ref-claude-code-mastery.md`. Then one dense skill body --
`.claude/skills/invest/SKILL.md` -- cross-referenced with the three agents it
dispatches (`forensic-scorer`, `institutional-positioning-scout`,
`thesis-critic`) and the two workflows that parallelize it. Then
`tools/vault-audit.py` for the tier semantics, and
`tools/test-prevention-arch.sh` for how every guarantee above is
adversarially tested. `wiki/investing/analyses/ORBC-DEMO-analysis-2026-06-11.md`
shows the output shape end-to-end.

## What's NOT here

Personal portfolio values, share counts, cost basis, concentration
percentages; biometric and lab data; location, age, wage, employer; real
thesis essays and the ratified doctrine numbers; real daily notes, decision
logs, sessions logs, briefings; application packets and resumes; research
dumps; the private master-context document and its derivatives; the live PII
denylist (the denylist paradox: a real denylist is a list of your secrets --
see `.audit/README.md`). Structural absence is mechanically asserted by
`.audit/assert-exclusions-v2.py`, which runs in CI.

## Author + License

Attribution in `LICENSE`. MIT.

## See also

- `THREAT-MODEL.md` -- the explicit PII boundary + redaction model
- `EXAMPLES.md` -- worked `/goal` autonomous-loop examples
- `docs/case-study-mission-three-extended-hours.md` -- a 39-minute
  autonomous mission case study
- `docs/CODEX-COMPATIBILITY.md` -- dual-engine (Codex CLI) layer
- `CONTRIBUTING.md` -- forking + reporting policy
