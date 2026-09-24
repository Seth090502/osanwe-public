---
name: gate
description: "Run a judgment gate before acting: /gate f trade discipline (anti-FOMO / anti-panic) before any ADD / TRIM / EXIT, /gate b build-vs-ship before building a new skill, script, hook, workflow or index, /gate t before changing a thesis status on a manual trigger (did it FIRE?), /gate calibrate for the routing-around compliance report. The model never judges -- verdicts come ONLY from tools/gate-eval.py. Not for sizing or doctrine-band questions."
metadata:
  categories: decisions
  osanwe-risk: "safe"
  osanwe-effort: "max"
  osanwe-arguments: "mode_and_subject"
  osanwe-argument-hint: "/gate f `<TICKER>` add | /gate t thesis-theme-alpha themealpha-amber-capex-guide-down | /gate b 'new backup daemon' | /gate calibrate | append --preview for dry-run"
  osanwe-allowed-tools: "Read Write Edit Bash Grep Glob"
  osanwe-categories: "meta"
  osanwe-type: "skill"
  osanwe-status: "active"
  osanwe-created: "2026-07-06"
  osanwe-updated: "2026-08-10"
---

## /gate <f|t|b|calibrate> `<subject>` [--preview]

One artifact set encodes the judgment; this skill only fills forms. AUTHORITATIVE
rules: `tools/gate-rules.json`. Human mirror + fill-rules + worked examples:
`ref-gate-tables.md` (sibling of this file) -- READ IT BEFORE FILLING ANY MARKER.
Golden exemplars (imitate them): the `golden: true` sheets in `wiki/research/gates/`.

### Mode routing (Pattern 6 -- deterministic, from args only)
- `f <ticker + action>` -> GATE-F trade-generation discipline sheet
- `t <thesis> <trigger-id>` -> GATE-T trigger-fired adjudication sheet
- `b <proposal>` -> GATE-B build-vs-ship sheet
- `calibrate` -> compliance report only (no sheet)
- `--preview` on any mode: run Phases 0-B, print the would-be sheet, write nothing.

### Phase 0: Load context (read-only)
1. `tools/gate-rules.json` + `ref-gate-tables.md`.
2. `wiki/research/gates/gates-registry.md` (prior sheets on this subject; a BLOCKED
   verdict on the same instrument within 5 trading days forbids a re-gate -- HALT).
3. Mode inputs: F -> entity note `wiki/entities/tickers/<T>.md`, latest analysis in
   `wiki/investing/analyses/`, latest briefing meta.json in
   `Calendar/decisions/briefings/` (VIX fields), `Calendar/decisions/execute-or-decline.md`;
   T -> the thesis file's `triggers:` block + the evidence sources themselves;
   B -> `execute-or-decline.md` + open-loops digest + the nearest similar artifact.

### Phase A: Fill markers
Every marker = `{value, prov}` per the fill-rules in ref-gate-tables.md. Provenance:
vault-relative path, or a scheme prov (`mcp:*`, `script:*`, `web:*`, `manual:*`).
NEVER estimate a marker you can read; NEVER omit one. Sheets carry NO dollar
amounts, share counts, or position sizes -- fractions and percentages only.

### Phase B: Compute (never judge)
`python tools/gate-eval.py --compute <draft-sheet> --json`
Transcribe verdict, mandates, suggested review_date VERBATIM into the sheet.
If the verdict surprises you, the markers are wrong or the table is wrong -- say so
to the user; do not adjust markers to steer the verdict (that is the failure mode
this kit exists to stop).

### Phase C: Write the sheet
`wiki/research/gates/gate-<mode>-<slug>-<YYYY-MM-DD>[-HHMM].md` (archival rule;
never overwrite). Frontmatter: canonical + `gate:` block exactly as in the goldens;
`related:` includes `[[gates-registry]]` + the entity/thesis touched. Body: two
sections -- `## Evidence` (prose behind each marker, cited) and
`## Verdict + mandates` (restated; user overrides are recorded HERE with the
override reason -- markers are never edited to flip a verdict).

### Phase D: Check (HALT gate)
`python tools/gate-eval.py --check <sheet> --json`
Exit 2 -> HALT: report findings, fix the sheet, re-check. Never proceed unchecked.

### Phase E: Registry row
Append one row to the index table in `wiki/research/gates/gates-registry.md`:
`| date | mode | subject | verdict | mandates | review_date | outcome |`
(outcome starts empty; a later session fills VINDICATED / WRONG / OVERRIDDEN).

### Phase F: Execute mandates
- `eod-row-*` mandates -> append the row to `Calendar/decisions/execute-or-decline.md`
  per its row protocol (ID = next EOD-N, ESCALATION_DATE from the mandate).
- `status-floor-*` -> the existing /brief Pattern-20 path does the `fired:` stamp;
  this sheet is its evidence record -- reference the sheet in the briefing, do not
  edit thesis files from here.
- Report every mandate executed / deferred in the final output.

### Phase G: Daily note
One line to today's `Calendar/daily/` note under the session's actions:
`- [HH:MM] /gate <mode> <subject> -> <verdict>` plus a Cross-References wikilink
to the sheet.

### Mode: calibrate
`python tools/gate-eval.py --calibrate --since <date> --json`
(default 30d). Append a dated `## Compliance <date>` block to gates-registry.md
with the per-gate expected/gated/compliance table, misses, ROUTING-AROUND flags,
and mandate follow-through gaps. Surface flags to the user bluntly -- low
compliance means the gates are being routed around, which is the primary threat
model. Also fill any `outcome:` fields whose review_date has passed (judge from
what the vault records show happened; OVERRIDDEN when the user acted against a
verdict).

### Quality Rules
- Verdicts come from gate-eval.py output only; transcription must be verbatim.
- Every marker carries provenance; vault-path provs must exist on disk.
- ASCII only (Pattern 22). No dollar values / share counts on any sheet.
- Registry row per sheet, no exceptions -- unindexed sheets defeat calibration.
- Empty-input safeguard: if the subject cannot be resolved to a concrete
  instrument / trigger-id / proposal, HALT and ask -- do not gate a vague subject.
