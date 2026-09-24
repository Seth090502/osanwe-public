# ref-local-protocol -- relay lane mechanics cheat sheet (code is AUTHORITATIVE)

Consumed by /local. On any conflict, the code wins: tools/relay.py,
tools/lib/relay_{exec,mcp,schema}.py, tools/relay-{mission,batch,verify,apply}.py,
config/local-lane.json. Doctrine home: docs/osanwe-runtime-reference.md
"model lane". This sheet exists so the skill body stays lean.

## Exit contract (relay.py and relay-batch.py children)

| Exit | Meaning | Orchestrator action |
|---|---|---|
| 0 | leg complete, distillate valid | verify -> consume |
| 2 | lane unavailable (lane.lock held / daemon down) | bounded retry, then report lane-busy |
| 3 | refused: bad mission, never_local leg, budget raise, role/sha drift on resume | fix the cause; NEVER bypass |
| 4 | output unusable (schema-invalid after retries) | inspect state, re-dispatch or keep frontier-side |
| 5 | partial OR awaiting-guidance -- distillate VALID both ways | status; if pending_escalation: guidance + resume; else consume the partial |

Batch exits: 0 all done | 5 parked legs remain | 1 failures | 3 bad manifest |
4 skipped (if-idle precheck said no; reason logged).

## Paths

| What | Where | Tracked |
|---|---|---|
| Mission specs | .claude/state/relay/missions/`<slug>`.json | no |
| Run state (resume/status source) | .claude/state/relay/`<run>`/state.json | no |
| Distillate | .agents/relay/`<run>`/leg-merged.json | YES |
| Verify report | .agents/relay/`<run>`/verify.json | YES |
| Batch state | .claude/state/relay/batches/`<id>`.json | no |
| Scheduled surfacing | .claude/state/scheduled-worker-pending.json | no |
| Share JSONL | .claude/state/local-orchestration-`<date>`.jsonl | no |
| Lane mutex | .claude/state/lane.lock | no |

Prune: `python tools/relay.py --prune [--keep-days 30]` (runs, missions, batches).

## Role families (config relay.roles; frozen into state at leg creation)

| Family | Role file (.agents/roles/) | Tool surface | Notes |
|---|---|---|---|
| research | lane-researcher.md | 11 tools incl. url_fetch + mcp_call | egress allowed |
| extract | lane-extractor.md | no-egress subset | local docs only |
| edit | lane-editor.md | propose_edit + raw reads + sha headers | proposals ONLY; never writes |

Role + trigger are FROZEN at creation; resume refuses (exit 3) on role-file
sha drift; a resume under a different env records resumed_triggers but the
frozen trigger governs all counters.

## Escalations

- Worker tool `ask_frontier`: budget 3/leg, executor-validated (refs must
  resolve leg-wide, tried-floor). Pause = exit 5 + pending_escalation.
- P-01 (kind plan): synthetic, budget-free, only when mission
  plan_checkpoint=true; carries the worker's plan + its HELD first tool
  batch (name+args). APPROVE dispatches the held batch unchanged; anything
  else drops it and injects the reply as steering.
- Guidance file: plain ASCII text; registered worker-side as source kind
  frontier (R-nn); claims derived from it carry prov frontier. Guidance is
  the ONE trusted non-sentinel-wrapped channel -- keep it decisive, <= 200
  words; the citation rule: the worker cites the guidance ref only when the
  VALUE appears in the guidance text.

## Verify classes (tools/relay-verify.py)

| Class | Cause | Consumption |
|---|---|---|
| VERIFIED | witness seek or re-fetch matched | normal |
| MISMATCH fabrication-grade | witness invalid OR fresh payload sha == recorded (source unchanged, claim wrong) | QUARANTINE distillate; auto-demotion trigger; counts against promotion |
| MISMATCH drift-possible | fresh payload sha differs (source moved) | consume with drift flagged; does NOT count against promotion |
| UNVERIFIABLE | locator truncated / server down / frontier recorded-only | consume with grade degraded one tier, reason named |

Every claim carries a byte-offset witness `file:offset:len` into the
normalized spill (or "spill-failed" -> verify falls back to re-fetch).
Verify writes a ledger row kind=relay-verify -- excluded from ALL promotion
counters (AUX_KINDS in delegate.py).

## Receipt fields that matter (distillate.receipt)

trigger (frozen; operator-phrase | launcher-mode-2 | scheduled-idle |
unattributed) | role | escalations[] | grounding_refusals | prompt_tokens
(cumulative prompt_eval_count) | resumed_triggers[] | fill/wall accounting.
Promotion counters (delegate.py --report) count only exit 0, trigger in
{operator-phrase, launcher-mode-2}, run not dbg/t5s/t8d/suite-prefixed.

## Canonical command sequences

Single research leg, background:

    python tools/relay-mission.py --leg research:insider-sweep --print
    python tools/relay-mission.py --leg research:insider-sweep
    CLAUDE_LANE_TRIGGER=operator-phrase python tools/relay.py \
      --leg research:insider-sweep --mission .claude/state/relay/missions/`<slug>`.json
    python tools/relay.py --status `<run>`
    # exit 5 + pending: write guidance.txt, then
    CLAUDE_LANE_TRIGGER=operator-phrase python tools/relay.py --resume `<run>` --guidance guidance.txt
    python tools/relay-verify.py --run `<run>`
    python tools/delegate.py --report --run `<run>`

Edit-family proposals:

    python tools/relay-apply.py --run `<run>`          # read-only re-check, prints Edit params
    # apply APPLYABLE proposals via the orchestrator's own Edit tool

Batch:

    python tools/relay-batch.py --file `<batch.json>`
    python tools/relay-batch.py --status `<batch>`
    # answer every parked leg's guidance file, then:
    python tools/relay-batch.py --resume-parked `<batch>`

Scheduled lane (context, not /local's to run): run-local-worker.cmd sets
CLAUDE_LANE_TRIGGER=scheduled-idle and calls relay-batch --if-idle; results
surface via scheduled-worker-pending.json + the open-loops digest.
