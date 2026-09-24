# Example 4 -- a build gate sheet

> As of 2026-09-20. Published as an example of the system's output.
> Not investment advice, not a recommendation, and not a statement of anyone's positions.

How a change to the system itself is authorised before it is built, including the mandates the verdict carries.

**Reading guide.** This is a `/gate b` sheet, the check run before building a new skill, script, hook or
workflow ([`.agents/skills/gate/SKILL.md`](../.agents/skills/gate/SKILL.md)). GATE-B is that gate; the verdict
comes only from `tools/gate-eval.py`. **Mandates** are the conditions the verdict attaches to the build, such
as a review after thirty days of use, which later work must discharge.

---

<details>
<summary>Metadata the system recorded for this run</summary>

```yaml
aliases: []
categories: [wiki]
type: report
tags: [topic/judgment-gates]
status: complete
created: 2026-07-06
updated: 2026-07-06
related:
  - "gates-registry"
  - "execute-or-decline"
gate:
  schema_version: 1
  mode: b
  subject: "Build the judgment-gates kit itself (this session, self-application golden)"
  golden: true
  markers:
    closes_eod_id: {value: null, prov: "Calendar/decisions/execute-or-decline.md"}
    overdue_eod_count: {value: 0, prov: "Calendar/decisions/execute-or-decline.md"}
    user_directive: {value: true, prov: "Calendar/daily/2026-07-06.md"}
    similar_organ: {value: null, prov: "manual:discovery-2026-07-06"}
    similar_organ_consumed_30d: {value: null, prov: "manual:discovery-2026-07-06"}
    size_class: {value: L, prov: "manual:discovery-2026-07-06"}
    deadline_bound: {value: false, prov: "manual:discovery-2026-07-06"}
  verdict: BUILD-JUSTIFIED
  mandates: [consumption-review-30d]
  review_date: 2026-08-05
  outcome: null
```

</details>


# GATE-B: build the judgment-gates kit (2026-07-06, self-application golden)

GOLDEN EXEMPLAR (built by Fable 5, 2026-07-06). The kit gates its own build --
the first GATE-B sheet is about GATE-B. Demonstrates rule ordering, the
user-directive override, and the size-L consumption mandate.

## Evidence

- Proposal: build the judgment-gates kit (3 decision tables + gate-eval.py +
  /gate skill + registry + bindings) -- the Fable 5 final-session artifact.
- closes_eod_id = null: no execute-or-decline.md row is closed by this build
  (the kit FEEDS the ledger; it does not resolve an existing row).
- overdue_eod_count = 0: as of 2026-07-06 no PENDING row is past its
  ESCALATION_DATE (EOD-1 escalates 2026-07-07; EOD-18 2026-07-08; the 7/07
  escalation batch had not landed at build time). Rule 3 therefore cannot fire
  today -- recorded honestly rather than back-fitted.
- user_directive = true: the session prompt (Calendar/daily/2026-07-06.md,
  Log section, 16:12 entry) explicitly commissions this artifact.
- similar_organ = null: the 2026-07-06 discovery pass (Codex read + 3 Explore
  sweeps) found no existing artifact classifying trade-generation discipline,
  manual-trigger adjudication, or build-vs-ship -- the pretrade staircase gates
  EXECUTION, execute-or-decline tracks RATIFIED actions; neither classifies
  proposals. Nearest functions checked and distinguished, so rule 1 (no v2 of
  an unused organ) does not apply.
- size_class = L: well over 200 new lines (gate-eval.py alone ~500).
- deadline_bound = false by the mechanical rule (no Efforts/`<slug>` deadline);
  the real deadline (Fable access ends 2026-07-07) is context, and the marker
  rule is deliberately narrow -- a looming deadline must never be usable to
  justify a build mechanically.

## Verdict + mandates

Rule 1 skipped (no similar organ) -> rule 2 fires: user_directive ->
BUILD-JUSTIFIED. Size L adds consumption-review-30d: review_date 2026-08-05.
Verdict computed by tools/gate-eval.py --compute and transcribed verbatim.

Displaced-work visibility (voluntary; the list-displaced-eod-rows mandate did
not fire at overdue_eod_count = 0): the 2026-07-07/08 escalation batch (EOD-1
offsite go-live, EOD-18) and another pending item are
the nearest shippable actions this build session displaced by a day. Recorded
so the tradeoff is visible, per the decline-as-artifact philosophy.

Consumption review 2026-08-05: if no non-golden gate sheets have accumulated by
then, this kit failed its own bar -- archive candidate, per its own GATE-B rule 1
next time something similar is proposed. The registry Compliance section is the
consumption evidence.
