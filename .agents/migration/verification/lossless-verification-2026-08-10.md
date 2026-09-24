# Independent lossless-migration verification -- all 15 skills (2026-08-10)

Operator-mandated ("dispatch some opus workers to make sure the skills are updated
1 to 1 and lossless"). Five INDEPENDENT opus verifiers (none did the migration),
3 skills each. Method per skill: frontmatter field-by-field ledger vs the pinned
legacy baseline (`227c857` for 14 skills; `0a708fc` for create-skill, whose disarm
edits were separately sanctioned); description-substance survival tables (exhaustive
for invest's 4,848->457 compression); body unified diff with EVERY hunk classified
into the four sanctioned edit classes ([A] harness-conditional dispatch, [B] eval
heading surgery, [C] retired-generator/path updates, [D] ASCII/whitespace) or
flagged; sha256 on every companion ref.

## Verdict: 15/15 LOSSLESS. Zero HIGH findings. Zero content loss.

| Batch | Skills | Verdict | Refs |
|---|---|---|---|
| 1 | gate, networth, one withheld skill | LOSSLESS x3 | 9/9 sha256-identical |
| 2 | challenge, deep, decide | LOSSLESS x2 + deep LOSSLESS-with-findings | 0 companions either side |
| 3 | consolidate, create-skill, retro | LOSSLESS x3 | 0 companions either side |
| 4 | spark, enrich, ingest | LOSSLESS x3 | 3/3 sha256-identical |
| 5 | vault, brief, invest | LOSSLESS x3 (exhaustive; invest per-capability table 30+ rows) | 14/14 sha256-identical |

Key systemic results:
- All 23 companion ref files byte-identical legacy vs canon (incl. the 93KB
  analysis template and 77KB evidence hierarchy).
- Every body hunk in all 15 skills classified A-D; "every deleted line is one half
  of a modification pair" -- the only pure deletion anywhere is a single blank line.
- All 6 D7 disambiguation directions literal + reciprocal.
- The 5 apparent invest gaps (Klarman/Ackman/Tepper, "metric degradation" wording,
  "5-phase research spine" phrase, CSP/covered-call, LTCG) were each verified absent
  from the LEGACY body too -- pre-existing description-vs-body drift, resolved in
  byte-identical companion/Atlas refs. Not migration loss.
- invest 898 lines (2 under the X2 cap); derived mirrors differ from canon by
  exactly the GENERATED banner + re-materialized allowed-tools (no privilege change).

## Findings -> dispositions (all LOW)

| Finding | Disposition |
|---|---|
| F-DEEP-1: imported counts-from-MCP Quality Rule contradicted retained Phase 1 private/-reads | **FIXED**: Phase 1 aligned to the AGENTS.md live-positions invariant (MCP counts where available, [STALE-COUNT] otherwise, private/ = interpretation layer) |
| F-B1: brief dangling "Quality Standards" cross-reference after heading rename | **FIXED**: reference now names Quality Rules (formerly Quality Standards) |
| create-skill Finding D: >= 100-char description floor dropped from prose (still done-bar enforced) | **FIXED**: floor restored to the Quality Rules bullet |
| withheld skill osanwe-created "2026-04-13" != git first-add 2026-04-18 | **FIXED**: corrected to 2026-04-18 |
| F-I2: 3 invest CLAUDE.md references vs vault's AGENTS.md convention | **FIXED**: all 3 -> AGENTS.md |
| deep osanwe-arguments bracket inconsistency "[target]" | **FIXED**: normalized to "target" |
| osanwe-updated bumped to 2026-08-10 on 8 skills where legacy field was present | ACCEPTED + RATIFIED here as the convention: migration IS a modification; created: preserved everywhere |
| F-DEEP-2/-3, F-S2, F-E1, F-V2/-V3, spark sessions-log obligation, ingest F.5 tally line (dead "re-dispatched" token), new negative-trigger description clauses | ACCEPTED: global-doctrine imports and codifications, none contradict legacy behavior; enumerated here for the record |
| F-V1 (vault D.1 --json flag), F-I1 (invest E.0 formally mandatory), F-I2-ingest --json | ACCEPTED as bug-fix-class tightenings (each matches the dispatched agent's own documented contract) |
| Description-only trigger phrases dropped (gate mandatory-invocation conditions; networth >2%-delta + dividend events; challenge weekly cadence + 2 triggers; deep archived-/research pointer; consolidate/create-skill mode keywords) | ACCEPTED: routing-recall tradeoff inherent to the 500-char cap; gate's conditions remain mechanically encoded in tools/gate-rules.json; candidates for future description tuning if live routing misses them |

Post-fix re-verification: sync clean, driftcheck manifest-clean 15/15, validate
0 FAIL / 0 WARN (budget 6,779 fits), skills-ref 15/15, checkall ALL GREEN.
Ops note: one checkall invocation appeared to hang ~20 min; the work had completed --
an orphaned edgar-tools uvx grandchild held the stdout pipe open (same spawn
pathology as the canary WARN). Cosmetic; the S5 edgar defect row already covers it.
