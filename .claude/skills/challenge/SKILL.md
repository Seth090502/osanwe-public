---
name: challenge
risk: safe
description: Thesis stress test. Takes any held position, belief, or assumption and argues against it using vault data and fresh evidence. Surfaces contradictions, invalidation signals, and assumption drift. Use when thesis confidence shifts more than 10 points, before ratifying a major position change, when contradicting evidence emerges, when concentration drifts toward doctrine triggers, or weekly for active investment / career theses on the watchlist.
arguments: [target]
argument-hint: "'orbital-compute thesis', '<TICKER> position', 'career-first-over-investing', 'remote-only requirement'"
allowed-tools: [WebSearch, WebFetch, Read, Write, Edit, Bash, Glob, Grep]
effort: max
user-invocable: true
---

## Quality Standards

- BE GENUINELY ADVERSARIAL. This skill fails if it softballs the bear case.
- Use actual dollar amounts from the portfolio. "$2,400 at risk" hits harder than "significant exposure."
- Calibrated confidence: use percentage scores with justification, not HIGH/MEDIUM/LOW.
- Inline evidence grading: every material claim cites source tier `[Grade A-F | source | date]`.
- Load bear case evidence FIRST. Do NOT read confirming vault data until Phase 2.
- Apply the Ideological Turing Test before output: "Could a genuine bear read this and say 'yes, that's my position accurately represented'?" Score 1-10. If below 7, strengthen the bear case.
- Check [[doctrine.template]] invalidation triggers and report honestly whether any are flashing.
- If the thesis survives the stress test, say so clearly -- "Thesis CONFIRMED under pressure" is a valuable output.
- If the challenge reveals a real weakness, recommend a specific action with dollar impact.

<example type="good_bear_case">
### 1. HBM oversupply risk by Q1 2027
**Evidence:** SK Hynix expanding HBM3E capacity 2.5x by end-2026 [B | Reuters | 2026-04-08]. Samsung restarting HBM3E production after yield fixes [B | Korea Herald | 2026-04-05]. Total HBM supply could exceed demand by 15-20% in Q1 2027 [C | TrendForce estimate | 2026-03-28].
**Impact if true:** Memory-maker margins compress 400-600bps. A held memory-sector position (combined) faces 15-25% drawdown = -$[PORTFOLIO_VALUE] to -$[PORTFOLIO_VALUE]. A GPU peer benefits from cheaper memory but the memory thesis takes a direct hit.
**Challenge strength:** 62% -- supply expansion is confirmed, demand growth is the variable.
</example>

<example type="bad_bear_case">
### 1. Competition could increase
**Evidence:** There are many competitors in the semiconductor space.
**Impact if true:** Could be negative for the stock.
</example>

## /challenge <target>

Genuinely steelman the case against the target position, thesis, or belief. This is not a balanced review -- it's an adversarial stress test.

### Phase 0-pre: Vault context retrieval (NEW; Phase 3.6b -- runs BEFORE Phase 0 Context Loading; read-only; bear-aligned)

Skill-level semantic retrieval over the local HNSW vault index (covers `wiki/` + `Calendar/` + `private/`; `Atlas/` is NOT indexed, so the thesis essays + [[doctrine.template]] are still read directly in Phase 0 -- this block COMPLEMENTS, not replaces). Deeper and path-filtered vs the universal UserPromptSubmit hook. Read-only: a single Bash `node` call; writes nothing. Let `T` = the thesis/position/belief being challenged.

**Bear-alignment:** the 12 queries below are deliberately invalidation/contradiction-oriented, so retrieving them first PRELOADS prior bear thinking + prior challenges + contradictions -- this REINFORCES the "load bear case FIRST" discipline rather than violating it. It pulls NO confirming data; confirming-vault reads still defer to Phase 2.

0-pre.1 -- Build 12 bear-oriented queries:
`"<T>"`, `"<T> invalidation signals"`, `"<T> adversarial bear case"`, `"<T> contradicting evidence"`, `"<T> base rates"`, `"<T> historical precedents"`, `"<T> falsification triggers"`, `"<T> counter-positioning"`, `"<T> regulatory risks"`, `"<T> technical risks"`, `"<T> market structure risks"`, `"<T> narrative shifts"`.

0-pre.2 -- Fire `query-skill.mjs` TWICE via Bash, piping the JSON payload to stdin (heredoc; no temp file). Model loads once per call (~1-1.5s each):
- BROAD (cross-vault, no filter): stdin `{"queries":[<the 12>],"top_k":100,"threshold":0.60}` piped to `node ~/.vault-substrate/query-skill.mjs`
- FOCUSED (prior challenges; the bear-record subtree): stdin `{"queries":[<the 12>],"top_k":25,"threshold":0.60,"filter_path_prefix":"wiki/research/challenges/"}` piped to the same script.

Each returns a JSON array `[{path,line,score,text}]`. The script always exits 0 (emits `[]` on any error), so Phase 0-pre never crashes the run.

0-pre.3 -- Merge BROAD + FOCUSED; dedup by `path:line` (keep higher score); sort by score desc; cap to top 100. Store as VAULT_CONTEXT.

0-pre.4 -- EMIT a visible summary (MANDATORY):

    Phase 0-pre -- retrieved vault context (N hits; M from wiki/research/challenges/)
    Top results:
      [score] path:line -- first ~80 chars of text
      ... (show up to 15)

If both calls fail or return `[]`: emit `Phase 0-pre -- no vault context retrieved (query-skill.mjs unavailable or index empty)` and continue. NEVER HALT on Phase 0-pre.

0-pre.5 -- Downstream consumers (these phases stay UNCHANGED; consult VAULT_CONTEXT as prior bear-thinking instead of re-deriving from scratch):
- Phase 2 (Vault Contradiction Analysis): seed assumption-drift + blind-spot + prior-position detection from VAULT_CONTEXT -- this phase benefits MOST (it is contradiction-retrieval-shaped).
- Phase 0 (Context Loading): add any prior-challenge / entity / decision-log paths surfaced in VAULT_CONTEXT to the load set.
- Phase 1 (Bear Case research): extend the prior bear cases surfaced in VAULT_CONTEXT rather than rediscovering them.

Cite any used chunk inline as `(vault: path:line)` -- plain text, NO wikilink syntax (Phase 0-pre context is raw, not vault-resolved).

### Phase 0: Context Loading

**CRITICAL ORDER: Load bear case evidence BEFORE confirming vault data.**

Determine what's being challenged and load relevant context:

**Investment thesis challenge:** Read [[doctrine.template]], the thesis MOC, all entity notes in that thesis, `private/holdings-taxable.md`, `private/holdings-ira.md`, `watchlist.md`, `ref-research-insights.md`, and any prior analyses for positions in that thesis.

**Individual position challenge:** Read the entity note, any prior analysis, `private/holdings-taxable.md`/`private/holdings-ira.md` for position size, and the thesis MOC it belongs to.

**Career/life challenge:** Read USER.md, profile.md, tracker.md, opportunities.md, ref-remote-data-careers.md, decision-log.md.

**Any challenge:** Read insight-stream.md and decision-log.md for prior positions on this topic.

### Phase 1: Research the Bear Case (3-5 searches)

Search specifically for:
1. Negative analyst reports, downgrades, bear arguments
2. Competitive threats and disruption risks
3. Macro headwinds specific to this position/thesis
4. Recent negative developments the vault may have underweighted
5. Contrarian voices with credible track records

Do NOT search for confirming evidence. The /invest skill already does that. This skill searches for what's wrong.

### Phase 2: Vault Contradiction Analysis

Read through the loaded vault context and identify:
- **Assumption drift:** What was assumed when the position was entered vs what's true now?
- **Confirmation bias signals:** Has the vault only captured positive catalysts? Are negative developments missing from watchlist.md or entity notes?
- **Concentration risk:** How much capital is exposed to this thesis failing?
- **Correlated risk:** If this thesis fails, what else in the portfolio gets hit? (Use risk cascade data from [[doctrine.template]])
- **Thesis fatigue:** Has this thesis been CONFIRM for so long that invalidation signals are being ignored?

### Phase 3: Steelman Output

Write to `wiki/research/challenges/challenge-{slug}-YYYY-MM-DD.md`:

```yaml
---
categories: [wiki]
type: challenge
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
confidence: medium
tags: []
related:
  - "[[decision-log]]"
  - "[[doctrine.template]]"
---
```

```markdown
# Challenge: [Target]
**Date:** YYYY-MM-DD | **Challenging:** [thesis/position/belief]

## The Current Position
[What the vault currently believes, with evidence and conviction level]

## The Bear Case (steelmanned)

### 1. [Strongest counterargument]
**Evidence:** [specific data, sources]
**Impact if true:** [dollar/career/life impact]

### 2. [Second counterargument]
...

### 3. [Third counterargument]
...

## Vault Blind Spots
[What the vault has been ignoring or underweighting]

## Assumption Audit
| Assumption | Source File | Date Established | Current Reality | Acknowledged in Vault? | Gap |
|------------|-------------|-----------------|-----------------|----------------------|-----|

## Concentration Exposure
[How much is at risk if this thesis fails -- dollar amounts from actual positions]

## Risk Cascade
[If this fails, what else gets hit -- from [[doctrine.template]]]

## Verdict

### Metacognitive Assessment
Before writing the verdict, run this internal loop:
1. **Understand:** What exactly am I challenging and what evidence did I find?
2. **Preliminary judgment:** What does the bear evidence honestly suggest?
3. **Critical evaluation:** Am I being genuinely adversarial or performing adversarialism? Would a real bear accept this as their position?
4. **Decision:** What is the honest assessment after this self-check?
5. **Confidence calibration:** How confident am I, expressed as a percentage with evidence basis?

**Challenge strength:** [X]% -- [evidence basis]. Would drop to [Y]% if [condition].
**Thesis status after stress test:** CONFIRMED UNDER PRESSURE | CHALLENGED | INVALIDATED
**Recommended action:** [specific action with dollar impact: "trim 30% of position ($[PORTFOLIO_VALUE]) to reduce concentration" not "consider reducing"]
**What would change this verdict:** [specific measurable trigger]
**Ideological Turing Test score:** [1-10] -- would a genuine bear accept this as their position?
```

### Phase 3.5: Self-Verification

Before writing output, verify:
1. Bear case loaded BEFORE confirming evidence?
2. Each counterargument has specific evidence with source grades?
3. Dollar impacts calculated from actual share counts?
4. Assumption audit references specific vault files and dates?
5. Ideological Turing Test score >= 7? If not, strengthen bear case.
6. At least one counterargument has challenge strength > 50%?

### Phase 4: Knowledge Base Updates
1. If thesis status changed, update the relevant thesis MOC
2. Append to decision-log.md if an action is recommended
3. Append to today's daily note under Insights
4. Append to `Calendar/decisions/sessions-log.md`
5. If new invalidation signals found, note in the entity note(s)

### Quality Rules
- BE GENUINELY ADVERSARIAL. This skill fails if it softballs the bear case.
- Use actual dollar amounts from the portfolio. "$2,400 at risk" hits harder than "significant exposure."
- Check [[doctrine.template]] invalidation triggers and report honestly whether any are flashing.
- If the thesis survives the stress test, say so clearly -- "Thesis CONFIRMED under pressure" is a valuable output.
- If the challenge reveals a real weakness, recommend a specific action (trim, hedge, set a stop, increase monitoring).
