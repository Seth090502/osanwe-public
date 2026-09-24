---
aliases: [vault-codex, codex]
categories: [meta]
type: reference
status: active
created: 2026-07-06
updated: 2026-09-22
tags: [topic/meta]
related: ["[[COMPATIBILITY]]", "*hot* (not published)"]
---

# Osanwe Vault Codex -- LEAN EDITION (v2, 2026-08-23)

GENERATED-replacement under OSANWE-V2 ADR-09. The exhaustive prose edition (450 KB,
2026-07-06) is FROZEN at `_archive/2026-08-overhaul/docs/Osanwe Vault Codex.md` --
consult it for historical architecture narrative; it is NOT maintained. This file holds
only what AGENTS.md routes here: the glossary, the routing law, the maintenance
protocol, and the append-only changelog. Machine counts live in
`docs/Osanwe Vault Codex.yaml` (generated from disk by `tools/gen-codex-yaml.py`;
hand edits to that file are overwritten).


## Current architecture and authority (2026-09-13)

This map supersedes status claims in the historical glossary and wave reports.

| Layer | Current authority | Evidence boundary |
|---|---|---|
| Contract | root AGENTS.md, single copy | Full bytes; root CLAUDE.md is the one-line stub `@AGENTS.md`, which keeps it loaded beside a CLAUDE.local.md; router-check and the pre-commit cage refuse any other CLAUDE.md content or a .claude/CLAUDE.md |
| State | Efforts/osanwe-v2-overhaul/STATE.md | Current queue and limitations; dated reports are history |
| Knowledge | Atlas/_MOCs/knowledge-moc.md (whole vault); wiki/meta/knowledge-moc.md (finance); wiki/entities/; wiki/investing/ | Select existing primers/methods with applicability and source review; historical research does not establish current account facts |
| Research | docs/financial-analysis-contract.md; .agents/skills/ | Modular source/period/basis/freshness checks; explicit unresolved evidence |
| Method admission | tools/pit/financial_documents.py; existing dataset registry; wiki/research/financial-methods/ | Exact inspected locators, origin/version, applicability, worked examples and reuse review; unreviewed material is discovery history |
| Retrieval | tools/retrieval-core.mjs; external index-vault/qsearch and vault-search server | One immutable admitted generation; full approved spans and current dependency checks; experimental hybrid is not demonstrated financial improvement |
| Truth/data | tools/pit/, tools/fis/ontology.py, existing dataset registry | Point-in-time availability and declared provenance; old data is not current by retrieval |
| Arithmetic | tools/fis/calcs_*, portfolio_engine, risk_engine, taxlot_ext | Isolated deterministic tests; synthetic arithmetic is not advice or performance |
| Control | gate-eval, precommit, checkall, provenance, approval/firewall | Fail-closed diagnostics; strategy/account execution still unavailable by default |
| Evaluation | evaluation/challenge_protocol.md; tools/eval-interface.py | Preregistration and budget gateway; real evaluator unavailable, no invented accuracy |
| Experience | generated hot.md, fis-app/, current reports | A cache/dashboard is a view, never independent authority |
| Finance/Data integration | docs/finance-data-integration.md; .agents/skills/finance-data/; tools/fis/workbench.py | Versioned source/semantic handoff and exact replay; live connector and source-truth verification remain separate |
| History/preservation | Efforts/osanwe-v2-overhaul/PRESERVATION-MATRIX.md | Reconstructed dispositions; no invented original 57-row matrix |

Historical directory names research/code/plans/reports/investing/knowledge/misc
are not a mandate to recreate old trees. Current knowledge entry is the MOC above;
no active knowledge/INDEX.md was found. USER.md retains durable preferences with
historical account figures clearly subordinate to runtime broker evidence.

The two FIS data roots have different runtime roles. Existing tools/pit inputs
and ontology datasets reside under the effort's _work/fis-data; shadow.py writes
current working logs under root _work/fis-data. Historical shipped shadow records
also exist in the effort root and are NOT implicitly the active shadow log.
Do not merge, move, grade or promote them by path guesswork. The STATE/report
records the split and the absence of a current prospective/alpha acceptance.

Current required reads are progressive: contract -> relevant authority -> needed
procedure. Generated YAML is an inspectable typed index, not narrative doctrine.
Machine health is obtained by running checks, never by a hardcoded cache sentence.

## Routing law (who writes what)

| writer | destination |
|---|---|
| skills/agents | wiki/, Efforts/`<slug>`/, Calendar/ |
| humans | Atlas/ (agent writes require explicit user authorization, including the September 13 identified financial corrections) |
| generated tools | usage ledgers, hot.md, ledger views, this file's YAML companion |

Full table: AGENTS.md "Writes" + Section 8.3 of the frozen edition.

## Historical glossary (retained vocabulary; current authority map above wins)

## Section 11 -- Glossary

Osanwe-specific terms a cold model trips on. Definitions are 1-2 sentences; paths in backticks, never wikilinks.

- Osanwe -- the project codename for the cross-harness financial research system plus the Obsidian vault at `<VAULT_ROOT>\`.
- ACE -- Milo's "Agentic Context Engineering" pattern (hooks + injected context) the runtime is built on.
- Milo / kepano / Okhlopkov / AgriciDaniel / Evgeny / Piotr1215 -- the named source patterns the vault fuses: ACE runtime, file formats, reader/writer stance, LLM-wiki structure, PR-write discipline, and MCP practice respectively.
- Atlas / wiki (tiers) -- Atlas is human-write-only knowledge; wiki is the agent-maintained LLM-wiki; the routing test decides which.
- hot.md -- `wiki/hot.md`, the session-cache continuity file (schema `hot-md-v2`); generated from session nodes and the resolution-aware action ledger; current authority is STATE.md.
- distillate -- `OSANWE-<private-file>.local.md`, a pointer-mode structural map emitted at SessionStart (gitignored, local-only).
- master-doc -- `<private-file>.local.md`, the ~2.8 MB Parts A-X master context document the distillate points at.
- SENTINEL-1 / SENTINEL-2 -- distillate freshness checks (doc-baseline drift; master-doc sha).
- ARC TENFOLD -- the 14-mission arc (T0..T13) run 2026-07-03..2026-07-05, all closed (tag `tenfold-arc-complete`).
- T0..T13 / tenfold-`<id>`-close -- the individual missions and their git close-tags.
- arc-state.md -- `wiki/research/tenfold/arc-state.md`, the live execution ledger of an arc.
- X## (X12, X37, X56, X59, X67, X70, X70a, X72, X75, X77, X83) -- arc-internal work-item / decision identifiers used across notes.
- X70a / staging pattern -- when the permission classifier denies an autonomous config/persistence edit, stage it to an `apply-*.ps1|py` for `<owner>` to run, and keep a manual-run guarantee.
- X12 -- the subagent-model env-jail root cause; the standing rule NEVER to set `CLAUDE_CODE_SUBAGENT_MODEL` at a persistent scope (it silently outranks every per-call model pin).
- X67 -- the growth/archival threshold doctrine (a growing vault makes a naive staleness metric only rise; archival-by-design paths are excluded from the HARD count).
- MOC -- Map of Content, a domain index note (`<domain>-moc.md`); `knowledge-moc.md` is the index of indexes.
- entity note -- a per-ticker/company knowledge file under `wiki/entities/`; claims append over time.
- thesis essay -- one of 5 investment theses in `Atlas/concepts/investing/theses/`, each carrying a machine `triggers:` frontmatter block.
- triggers: / machine-trigger -- schema-v1 kill/red/amber/manual conditions on a thesis essay, evaluated by `/brief` Phase H (`evaluated_by: brief-phase-h`); `fired:` stamps when tripped.
- Pattern 6 -- deterministic mode routing (a skill picks its mode from explicit args, not inference).
- Pattern 20 -- machine-trigger gating (a status floor derives from a fired trigger, not a judgment call).
- Pattern 22 -- the ASCII-clean byte-scan gate on all agent-written content.
- GATE / HARD DRIFT / SOFT DRIFT -- vault-audit severity tiers; GATE (broken wikilink, missing/forbidden frontmatter, template drift) blocks writes and commits.
- 95/100 floor -- the honest vault-health floor invariant enforced by write-time hooks.
- honesty metric / uncapped HARD -- the real-decay trend (orphans + living-stale + session-gaps + skill-length) surfaced explicitly because the -5 HARD cap conceals it in the score.
- F11 -- atomic-commit suppression bracketing a multi-file skill so it lands as ONE commit (`tools/lib/f11_orchestrator.py`; flag `.claude/state/auto-commit-disabled`).
- F14 -- narrow-stage: stage only the intended paths before an atomic commit.
- F17 -- the Co-Authored-By verification step at commit time.
- F.halt -- the mid-batch failure pattern: stop immediately, leave F11 on, write no partial commit, report succeeded/failed/not-attempted.
- EOD / execute-or-decline -- `Calendar/decisions/execute-or-decline.md`, the escalating action queue (EOD-N rows) surfaced by the open-loops digest.
- open-loops digest -- `tools/open-loops.py`, the SessionStart top-5 stale-loop ranker that enforces EOD escalation dates.
- DW topology / Dynamic Workflow -- a fan-out of read-only worker agents (concurrency <= 6) that a DW-worker skill detects per Phase A.7; the sequential spine is the permanent universal fallback.
- Wave-1/2/3 / invest-verify / brief-research -- the DW waves; Wave-3 is the adversarial skeptic wave in `/invest` (`invest-verify.js`, which the skill calls for every material rating conclusion, fail-closed). DISABLED IN PRACTICE: `invest-verify.js` returns `status: withheld, dispatched_agents: 0` for every valid call, because the Workflow agent API supplies no verified per-call read-only boundary, so the gate resolves to a Phase N withheld acceptance and no skeptic is dispatched (see COMPATIBILITY.md "Validation profiles"). `brief-research.js` is the `/brief` Wave-1 acquirer bundle.
- *_DW_TOKEN_BUDGET -- per-skill env budgets read by the main loop (e.g. BRIEF_DW_TOKEN_BUDGET default 150K); the workflow sandbox has no `process.env`.
- sequential spine -- the deterministic non-DW fallback path every DW-worker skill retains verbatim; no skill conditions behavior on model identity (topology doctrine).
- shadow rating -- a parallel "what the model would say" rating tracked for calibration.
- Brier ledger / calibration-monitor -- `Calendar/decisions/briefings/brier-ledger.json` + `wiki/investing/calibration-monitor.md`, the prediction-scoring substrate.
- INGEST:claims block -- the `<!-- INGEST:claims -->` pipe-row appendix in an analysis that feeds `/ingest`; every row carries `prov:`.
- prov: -- the provenance tag on quantitative claims, precedence `mcp:* > script:* > web:*`.
- evidence grade (A/B/C/D) -- inline source grade `[Grade A|source|date]` with freshness letter-downgrades; drives the confidence caps.
- confidence vs conviction -- confidence is the epistemic probability the analysis is correct (evidence-grade capped); conviction is the strength of the position recommendation; reported separately.
- claim-distributor -- the read-only agent that maps a claim batch to entity sections (Financial signals / Thesis Fit / Risks / Catalysts / Recent) and returns sha256-preserving Edit ops; the parent skill performs the write.
- symmetric back-linking / BACKLINKABLE_CATEGORIES -- reciprocal `related:` wiring shared by both `/ingest` modes (`extract` and `file`, the latter formerly the separate `/enrich` skill, merged 2026-08-23) so every link has a return link.
- body-preservation / sha256 invariant -- the guarantee that content outside intended insertion sites stays byte-exact across an Edit.
- marker signature -- the (entity, metric, value, date) dedup key that makes idempotent re-runs produce zero diff.
- Tier 1/2/3 contradiction resolution -- the `/ingest` contradiction ladder: Tier 1 auto-resolve, Tier 2 flag, Tier 3 reject.
- .vault-substrate / vault-search / server.py -- the out-of-tree semantic-retrieval engine (HNSW index at `~/.vault-substrate/`, server at `<LOCAL_PATH>/vault-search/`), rebuilt every 2 minutes by a scheduled task.
- semantic-context-inject -- the SessionStart/UserPromptSubmit hook that calls `server.py --oneshot` to inject top-5 vault chunks.
- qwen36 / legacy local worktree -- archived whole-session experiment; its obsolete worktree was retired after verified backup on 2026-09-12. History is retained by `archive/local-mode-2026-09-12`; current per-query local routing follows config/local-lane.json and /local.
- D-SEC-1 / D-SEC-2 -- the two security decisions: mechanical the broker order deny; Gmail/playwright session isolation.
- lethal trifecta -- the co-load risk (private data + untrusted content + an external-action tool); the Gmail connector is the external-action leg D-SEC-2 isolates.
- pretrade staircase / three walls / EXECUTE ORDER -- the T11 order-safety stack: permission-deny + `pretrade-token-gate.py` + signed `pretrade_gate.py` PASS, gated on the phrase `EXECUTE ORDER <id>`; no deny was ever lifted (fail-closed). As of 2026-09-22 the phrase condition does not hold -- defects D70, D72, D73 and D74, found by three adversarial rounds run with synthetic transcripts (no order was placed) -- so the controls in force are the permission deny list and the hook's refusal of every robinhood-trading tool except its read tools and three equity-order names; a replacement exists only as a design under adversarial review, outside the repository.
- bypass env vars -- `CLAUDE_VAULT_BYPASS_VALIDATOR`, `CLAUDE_VAULT_LAX_ORPHAN`, `CLAUDE_HOT_MD_BYPASS_CHECK`; each logged to `.claude/state/bypasses-<date>.log`.
- EXEMPT_PATHS -- the `pre-write-validator.py` allow-list (AGENTS.md, `docs/VAULT-HANDOFF-V16.md`, etc.) exempt from path-remap self-blocking.
- net-liquidity composite -- the `/brief` FRED macro reading WALCL - RRP - TGA (4-week trend) plus the DTWEXBGS dollar row.
- price-fetcher Tier 0/1/2 -- the quote-source ladder: Tier 0 the broker MCP (broker-authoritative), Tier 1 `fetch-prices.py` yfinance, Tier 2 single-ticker retry.
- regular_market_close anchor -- the doctrine that concentration and trim-trigger math anchors to the regular-session close even when extended-hours prices are shown.
- archival rule -- the never-overwrite discipline for dated files (new file per run; `-HHMM` on same-day collision).
- Bases / Tasks / .base -- Obsidian plugins; `.base` is a structured-view file used instead of Dataview and carries no frontmatter.
- Codex mirror (.agents / .codex) / AGENTS.md -- REVIVED-INVERTED 2026-07-08 (see 13.4). `AGENTS.md` is now the CANONICAL router (Codex CLI auto-loads it; Claude Code imports it via the `CLAUDE.md` shim); `.agents/skills/` holds thin pointer-adapters (bodies single-source in `.claude/skills/`, never forked) and `.codex/config.toml` holds read-only MCP config. The prior T7-RETIRED Mission-Four mirror (forked bodies + ported hooks) stays archived at `_archive/codex-mirror-2026-07-04/`. SUPERSEDED by the 2026-08-10 cross-harness cutover, per the authority map above: `.agents/skills/` is now the CANON tree and `.claude/skills/` the sync-generated derived copy (`.agents/scripts/sync.py`), not the reverse. `CLAUDE.md` became a byte-identical copy of `AGENTS.md` at that cutover, and on 2026-09-22 went back to a one-line import stub, `@AGENTS.md`, because Claude Code does not read AGENTS.md natively beside a root CLAUDE.local.md.

---



## Section 13 -- Maintenance protocol + changelog (carried; amended for v2)

### 13.1 Append vs regenerate

- **APPEND** (edit this file in place + add a changelog row) for INCREMENTAL change:
  a new/renamed/deprecated skill, hook, agent/role, workflow, MCP server; a corrected fact.
- **REGENERATE** (re-run the producing audit) for STRUCTURAL change: the machine counts
  and organ inventory now regenerate via `python tools/gen-codex-yaml.py`; do not hand-edit
  that file. Folder/skill/agent drift is fixed by fixing DISK, then regenerating.

### 13.2 Changelog row procedure

Append one row per shipped change: date | actor | what | propagation note
(YAML mirrored? distillate affected? skills touched?). Never rewrite prior rows.

### 13.3 v2 amendment (2026-08-23)

The changelog below is carried from the frozen edition. From v2 forward, rows also
accept the form used by OSANWE-V2 commits (`agent(v2/Wn): ...`). The empty-body
2026-08-17 row defect noted at C-pack time was a rendering artifact of the frozen
edition's table width -- the full row text is present there and is not duplicated here.


| Date | Author | Change | Propagation |
|---|---|---|---|
| 2026-09-12 | agent | Recover universal root parity, financial semantics, truthful generated state, evaluator refusal and W9 correctness/security | Regenerate YAML and bootstrap; sync six financial skills; current STATE and preservation matrix supersede old status prose |
| 2026-09-12 | agent | Close recovery with byte-preserving ledger apply and representative workflow/resume acceptance | Nine recovery suites in checkall; historical source/replay evidence recorded, native multi-file timeout and launcher behavioral pin remain explicit limits |
| 2026-09-12 | agent | Establish main as the sole normal branch; recover stranded daily history and retire archived worktree/branches | Update universal roots and hook policy; preserve verified bundle/ZIP and unique archive tags; Git recovery report records every disposition |
| 2026-09-12 | agent | Add public institutional covariance, valuation, Black-Litterman and constrained cost-aware allocation; repair causal simulation and account cash segregation | Institutional-methods organ, three canonical financial skills, eight routine test suites, preregistered synthetic comparison; no proprietary parity or alpha claim |
| 2026-09-12 | agent | Preserve leading appendix text and separators during heading-ledger ingest; verify lossless reconstruction before creating nodes | Add mixed-newline and no-heading refusal controls; repair only this mission's uncommitted nodes while retaining every historical ledger byte |
| 2026-09-12 | agent | Close institutional implementation on main with exact sealed Git artifacts and durable session backlinks | Retire experimental branch; refresh current STATE/YAML/cache, preserve checksum-bound evidence endings, and align retro with physical history preservation plus node text equality |

| 2026-09-12 | agent | Integrate Finances and Data with the existing financial engine | Add a canonical context skill, stateless checked evidence/model handoff, exact cashflow analysis and deterministic portable package; repair sensitive-source and risk-method routes; preserve all account and strategy gates |
| 2026-09-12 | agent | Reject false-green audit scopes and preserve native Data export evidence | Normalize full-scope sentinel, require auditable files, enforce subtree boundaries and expose scan scope/counts; nine regression controls; canonical audit role regenerated, vendor bytes archived without weakening authored-text checks |

| 2026-09-12 | agent | Connect the existing finance education and book-derived references to current financial method selection | Extend the existing finance TOC and shared evidence contract; require method-use provenance, preserve source gaps, repair scoped bear-first challenge reads and version portable context to 1.0.1 without exporting the library |
| 2026-09-12 | agent | Tighten financial reasoning and Data handoffs using native Opus 5 xhigh development cases | Preserve baseline, failed drafts and frozen criteria; require traced arithmetic, causal and population discipline, concrete briefs and final draft review; add named accounting identities and Microsoft v3 in portable context 1.1.0; retain model and bounded-harness limits |
| 2026-09-13 | agent | Begin the approved institutional-quality research release with separate evidence states and final-artifact review | Extend existing workbench/evaluator/runtime owners, preserve frozen baseline and inherited bytes, correct active library consumers and propose protected Atlas corrections; current plan remains open until live, independent and operational evidence exists |
| 2026-09-13 | agent | Release local source-to-artifact review controls, durable development scoring, corrected library consumers and scheduled recovery | Finance/Data 1.2.1 preserves the calculation packet and adds canonical reviewer contracts; native pilot preserves all 108 attempts and establishes no improvement; generated skills, roles and YAML synchronized; independent custody, account-host verification and operational observation remain separate gates |
| 2026-09-13 | agent | Bind reviewer correction references and resolution states in Finance/Data 1.2.2 | Producer v2 passes 139 controls with the semantic acceptance consumer unchanged; isolated package checks pass; public report v4 adds exact tax and cost decompositions, computed revenue reversal thresholds, dynamic financial narrative and one actual browser session; fresh substantive review remains a separate gate |
| 2026-09-13 | agent | Document native turn accounting and extend the public report's decision sensitivity | Fifteen synthetic controls distinguish provider round trips from final tool-result counts; twenty independent JSON Schema controls retain separate structural scope; report v5 compares explicit cost behavior and itemizes actual connector coverage, with final rendered bytes browser-checked; prior failed reviews remain withheld; runtime owner and generated YAML synchronized |
| 2026-09-13 | agent | Correct financial method references and add source admission, exact-passage retrieval and portable public knowledge | Preserve original bytes; extend existing registry, external search, Finance/Data and validation owners; production roles inherit session settings; current release report distinguishes local controls, live public reconciliation and remaining native/account/independent/operational gates |

| 2026-09-13 | agent | Repair table-ledger ingestion exposed by a public AVGO research journey | New EOD/insight suffixes require preserved pre-append bytes and digest; no-op and heading compatibility retained; exact same-day interrupted writes can resume, historical loss and changed bytes refuse; runtime owner and generated YAML synchronized, original failure retained |
| 2026-09-21 | agent | (Branch history, superseded before merge by the 2026-09-22 stub row below.) Move the working system to one agent contract file, AGENTS.md, on branch chore/single-agents-md | Root CLAUDE.md removed after a byte-for-byte match; the .claude/skills/ pair differs and stays; router-check, the pre-commit cage, the session integrity hook, the count-drift classifier and the docs now name AGENTS.md and refuse a reappearing CLAUDE.md; a headless 2.1.278 session in a worktree quoted a random canary from AGENTS.md, and the same session loads nothing when a root CLAUDE.local.md is present, which is recorded as a merge blocker |
| 2026-09-21 | agent | Correct four historical-glossary entries that named components the disk does not hold | Brier-ledger path corrected to Calendar/decisions/briefings/; /enrich described as the /ingest file mode; Wave-3 marked disabled in practice per invest-verify.js; canon/derived skill direction and the CLAUDE.md "shim" wording marked superseded by the 2026-08-10 cutover. Documentation only; no disk or YAML change |
| 2026-09-22 | agent | Record that the order gate's phrase condition does not hold, and what the publication privacy gate missed | Three adversarial rounds drove condition 1 of `pretrade-token-gate` end to end with synthetic transcripts and found shapes it authorised; no broker call was made and no order placed. Four patches retired unmerged; D70, D72, D73 and D74 open; the gate brief no longer calls condition 1 a guarantee, and its matcher and dead-code statements are corrected (the matcher has been the whole broker server since 2026-08-10). A property-based replacement exists only as a design under adversarial review, outside the repository; the deny list and the hook's refusal of unrecognised robinhood-trading tools remain the controls in force. The claude.ai the broker connector, which reached sessions outside the vault with no rule covering it, is denied server-wide at user scope. A PreToolUse guard that refuses heredocs on the Bash tool is registered in both harnesses and has been seen firing only in Claude Code. Publication pipeline, outside the vault: D71 its privacy gate reported failure without stopping a build (fixed to gate); D75 its denylist had no rule for a concentration figure or a roster written in prose (an ownership scan now gates); D76 a replacement public repository inherited private facts through history (a fresh root was chosen). Documentation only. The YAML is NOT regenerated here: `gen-codex-yaml.py` takes its own location as the vault root and counts files on that disk, so run from a worktree it writes the worktree's path and counts into the index; it must be run from the live vault, which is a follow-up rather than part of this merge |
| 2026-09-22 | agent | Resolve the single-contract merge blocker: root CLAUDE.md stays as a one-line stub that imports AGENTS.md | Measured on Claude Code 2.1.280 with synthetic files: AGENTS.md beside a CLAUDE.local.md loads only the local file, and a CLAUDE.md holding only `@AGENTS.md` loads the contract with or without it; a headless worktree session then read a canary through the stub. router-check and the pre-commit cage require exactly the stub and refuse a .claude/CLAUDE.md; the session integrity hook alerts on a wrong stub and drops the version-floor check an import does not need. The YAML is not regenerated here, for the reason in the row above |
