# Porting brief: gate-eval CLI (deterministic judgment-gate verdict engine)

COLD BRIEF -- written without sight of the manifest test blocks; the executable `test:` in
`.agents/hooks/manifest.yaml` is the acceptance criterion, not this prose. Criticality: SAFETY-CRITICAL
(money-adjacent judgment). Portable: YES -- already a harness-neutral CLI, so "porting" means WIRING it.

## (a) What the gate must guarantee

THE MODEL NEVER DECIDES A VERDICT. Three judgment gates are frozen into static decision tables; the
runtime agent only fills markers with provenance and transcribes what the engine returns. GATE-F,
trade-generation discipline (anti-FOMO / anti-panic) before any ADD/TRIM/EXIT -> DISCIPLINED |
FOMO-SUSPECT | BLOCKED. GATE-T, trigger-fired adjudication for manual/evidence thesis triggers ->
FIRED | NOT-FIRED | INSUFFICIENT-EVIDENCE. GATE-B, build-vs-ship before creating any new
skill/script/hook/workflow/index -> BUILD-JUSTIFIED | SHIP-FIRST | DECLINE. Two halves: `--compute`
derives verdict + mandates from the markers; `--check` RE-DERIVES the verdict from the same markers and
FAILS if the verdict recorded in the sheet differs, so a model writing a flattering verdict into the
artifact is caught mechanically. A harness letting a model emit a verdict without a passing `--check`
has not ported the gate.

## (b) Reference implementation + load-bearing facts

Reference: `tools/gate-eval.py` (622 lines) + rules table `tools/gate-rules.json` (schema_version 1).
Cross-harness entry point `.agents/scripts/gates/gate-eval.py` resolves the repo root from its own
location, sets `VAULT_ROOT` in the child env if unset, delegates argv verbatim. Deps: python3 + PyYAML
(lazy). Tests: `tools/test-gate-eval.py`, `.agents/scripts/gates/test-gates.py`.

1. THE RULES TABLE IS AUTHORITATIVE -- not the code comments, not the human mirror.
   `tools/gate-rules.json` holds every marker spec, threshold, ordered rule, mandate set, and
   review-date offset; `ref-gate-tables.md` mirrors it for humans, LOSES on conflict, and is
   version-locked to it by `schema_version`.
2. INVOKE VIA THE WRAPPER, ALWAYS: `--compute <sheet> | --check <sheet> | --calibrate [--since ISO]
   [--json]`. Only coupling: `VAULT_ROOT` plus repo-relative corpus paths (gate sheets, analyses,
   theses, briefings, the execute-or-decline ledger). EXIT CODES ARE THE CONTRACT: `--compute` 0 (2
   only on an unusable sheet); `--check` 0 on PASS and **2 on FAIL**; `--calibrate` always 0.
3. EVERY MARKER CARRIES PROVENANCE, AND PROVENANCE IS VERIFIED. A marker is `{value, prov}`; `prov` must
   match a scheme prefix (`mcp:`/`script:`/`web:`/`test:` -- lowercase, 3+ chars, colon) OR resolve to a
   file EXISTING relative to VAULT_ROOT (dangling = FAIL). Types are strict: a bool is not an int.
4. `--check` VALIDATES MORE THAN THE VERDICT: ASCII (bytes <= 127, Pattern 22); canonical vault
   frontmatter; `gate.schema_version == 1`; `mode` in t|f|b; non-empty `subject`; boolean `golden`;
   uppercase `ticker` (f-mode); every non-optional marker present; recomputed verdict == recorded
   verdict; recomputed mandate SET == recorded mandates; ISO `review_date` whenever mandates exist;
   `outcome` null or VINDICATED/WRONG/OVERRIDDEN/n-a. Findings: `{dimension, expected, actual, status}`.
5. RULE ORDER IS SEMANTIC -- short-circuits run BEFORE scoring. GATE-F rule 1: `trigger_backed AND
   action_side in {TRIM, EXIT} -> DISCIPLINED`; rule 1b: `zone_preregistered AND action_side == ADD ->
   DISCIPLINED`; only then is `fomo_points` counted (7 binary conditions; >= 4 BLOCKED, 2-3
   FOMO-SUSPECT, else DISCIPLINED, plus a combo BLOCK on new-name + no-prior-analysis + catalyst <24h).
   GATE-T applies an evidence FLOOR first (>= 2 items of grade A|B from >= 2 distinct sources, else
   INSUFFICIENT-EVIDENCE), then FIRED iff metric + window + counter all hold. GATE-B rule 1 DECLINEs a
   v2 of an organ unconsumed 30 days BEFORE rule 2's user_directive override; reorder and verdicts move.
6. OPTIONAL MARKERS ARE BACK-COMPAT LOAD-BEARING: a marker flagged `optional` may be absent and takes
   its declared default (e.g. `zone_preregistered` false), so sheets written before the marker existed
   still validate. Do not "tighten" this.

## (c) Where to bind it

Not a lifecycle hook -- a CLI. Binding = making invocation unavoidable at three trigger points
(AGENTS.md "Before you act"): any ADD/TRIM/EXIT -> GATE-F; any thesis-status change on a manual or
evidence trigger -> GATE-T; any new skill/script/hook/workflow/index -> GATE-B. Harness wiring,
strongest first: (1) a `pre-tool-use` blocking hook refusing gate-sheet writes lacking a passing
`--check`; (2) a `post-tool-use` checker running `--check` on written `wiki/research/gates/*.md` (per
`.agents/hooks/README.md` Crush never intercepts PostToolUse -- unavailable there); (3) instructions.

## (d) Input shape

A FILE, not stdin: a gate sheet at `wiki/research/gates/gate-<mode>-<slug>-<YYYY-MM-DD>[-HHMM].md`
whose YAML frontmatter carries a `gate:` mapping with `schema_version`, `mode`, `subject`, `golden`,
`markers`, `verdict`, `mandates`, `review_date`, `outcome`, and (f-mode) `ticker`. Output: human lines;
`--json` gives `{sheet, status, findings, computed}` for `--check`, `{mode, verdict, mandates,
suggested_review_date, detail}` for `--compute`.

## (e) Non-goals and known residuals

- GATE-F checks BEHAVIORAL/TEMPORAL process markers only; it never rechecks doctrine ceilings or R/R
  (those live in the analysis skill and the pretrade gate CLI), GATE-T is out of scope for numeric
  machine triggers, and GATE-B does not duplicate ledger bookkeeping. Adding any of it double-gates.
- `--calibrate` is a ROUTING-AROUND detector (expected-vs-gated events, mandate follow-through) and
  never blocks -- treat its output as a report, never as a gate.
- Fully offline and deterministic: no network, no MCP, no clock sensitivity beyond today's date for
  review-date math. A port that introduces a model call in the verdict path has destroyed the exact
  property the gate exists for.
