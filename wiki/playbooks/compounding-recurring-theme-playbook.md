---
categories: [wiki]
type: synthesis
status: active
created: 2026-05-24
updated: 2026-07-10
tags: [topic/consolidation, topic/playbook]
related:
  - "hot"
---

# Compounding (recurring theme) Playbook

## Pattern
Invariant: A vault artifact compounds -- gets re-read and built upon in a later session -- if and only if some skill's read-path names it as an input; theme-recurrence and inbound-link count do not make an artifact compound, and an artifact outside every read-path is written once and decays.

The only compounding mechanism demonstrated on disk is a skill phase that mechanically reads a prior artifact by path: /invest Phase J.5 reads the prior dated analysis plus the entity note and accretes drift into an additive-only Inconsistency Log (sessions-log.md:1124), and the proof is later sessions citing the earlier file by name -- the 4/13 analyses re-read 15-17 days later as the J.5 baseline (4/29 "6 Material drift entries vs prior amzn-analysis-2026-04-13", sessions-log.md:30; 4/30 "22 dated drift entries vs prior amd-analysis 4/13", :28). The 4/22 thin-stubs-over-missing-entities rule holds for the same reason: a stub compounds only as a back-link accretion target a future /enrich+/ingest run reads (sessions-log.md:552) -- exactly the 4/13 aspiration "Compounding vault needs active skills to generate linked, tagged output" (Calendar/daily/2026-04-13.md:101). Disk-verifiable: the 14 ticker entities inside the J.5 read-path all carry dated Inconsistency Logs, while the 49 wiki/entities/companies/ notes outside it carry none. The falsifier confirms the boundary -- thesis-theme-alpha held the vault's heaviest inbound load (112 links) yet rotted into "correctness-poison," the explicitly-named inverse of compounding, because no skill refreshed its hardcoded numbers (sessions-log.md:3302). This is the knowledge-side twin of execution-gap-playbook: as a ratified action closes only through a machine-interceptable channel, an artifact compounds only through a skill read-path.

Confidence: 80% -- mechanism disk-verified (14 ticker entities carry the J.5 read-path, 0 of 49 company entities do; the thesis-theme-alpha 112-inbound decay is the named falsifier) and owner-stated (daily/2026-04-13.md:101); haircut for folding three read-path mechanisms (J.5, enrich/ingest accretion, brief recency) into one iff without an exhaustive orphan-vs-reread audit of every artifact.

## Evidence
- 2026-04-21: theme 'compounding'
- 2026-04-13: theme 'compounding'
- 2026-04-15: theme 'compounding'
- 2026-04-22: theme 'compounding'
- 2026-04-28: theme 'compounding'
- Threshold cleared: >= 3 distinct sessions share theme (observed 11).

## Counter-cases

- 2026-06-03 -- thesis-theme-alpha at 112 inbound links = "the inverse of compounding"; the durable fix was linking the essay to the entity layer (a read-path), not refreshing hardcoded numbers (Calendar/decisions/sessions-log.md:3302). Refutes the stub's premise that recurrence or centrality equals compounding; confirms the narrowed read-path rule
- 2026-04-15 -- the miner tags this session theme 'compounding' but it is a homonym: "compounds volatility" (Calendar/daily/2026-04-15.md:59) and tax-loss "compounding capital" (:117) are the portfolio/risk sense, not artifact re-use -- the raw 13-session count conflates senses and overstates the theme
- 2026-05-01 -- "Pattern-codification != thesis-validation" and cross-source provenance compounding mistaken for confirmation (sessions-log.md:1553,:1494): the read-path is value-neutral -- it re-propagates whatever is wired in, including stale errors (the 4/13 NVDA "mass production confirmed" false claim rode the J.5 path until a fresh pass superseded it, sessions-log.md:1455). Compounding is not automatically beneficial

## Recommendation

Execute the open-since-2026-04-28 follow-up at sessions-log.md:1147 -- port the /invest Phase J.5 prior-research-comparison read-path (.claude/skills/invest/SKILL.md) into the other research skills so their subjects accrue an additive Inconsistency Log the way the 14 ticker entities do; today the 49 wiki/entities/companies/ notes have none, so company research does not compound. Ratify the write-side rule via /decide compounding-read-path-gate: before /retro or /consolidate writes any standalone synthesis (playbook, spark, ref-doc, thesis essay), it must name the skill phase that will read the file back on a later run, or mark it write-once reference rather than a compounding asset; and any thesis essay's live numbers must be entity-layer links, not hardcoded values (the 2026-06-03 fix). Do NOT satisfy this by adding inbound links or another consolidation-digest mention -- neither is a read-path.

## Apply-when

Before writing or promoting any standalone synthesis: grep the .claude/skills tree for the target file's path or type. If no skill phase reads it back (zero hits in under 30s, as wiki/entities/companies/ returns against the J.5 phase), it will not compound -- wire it into a read-path (entity Inconsistency Log, /brief entity-recency pull, /enrich+/ingest back-link accretion) or record it as write-once, not a compounding asset.

## Related
- hot -- session cache; this playbook is surfaced in the consolidation digest
- [[meta-skill-infrastructure-decisions-playbook]]
- investing-decisions-playbook
- a private file
