---
name: deep
risk: safe
description: "Use when launching institutional-grade 100+ source research on a market-linked topic, when building canonical reference docs referenced by /brief or /invest, when seeding /enrich onboarding workflow, or when WebFetch alone is insufficient for evidence depth. Generate an optimized Deep Research prompt for claude.ai Research mode that yields output pre-formatted for zero-friction /enrich onboarding + /ingest v2 marker-signature extraction, including a `target_path:` custom frontmatter field so /enrich v9 uses the /deep-intended filename as explicit placement (no slug drift). Composed prompt bakes in MANDATORY OUTPUT FORMAT constraints: canonical YAML frontmatter (with target_path) + numbered H2 TOC + >=100 inline citations + >=6000-word length floor + third-person analytical voice + entity-claim format (for /ingest extraction) + per-entity section block (Financial signals / Thesis Fit / Risks / Catalysts / Recent). Embeds portfolio context (live positions from private/holdings-taxable.md + private/holdings-ira.md), active thesis exposure (from hot.md), existing vault reference material (to avoid duplication and enable symmetric back-linking). Writes composed prompt to wiki/research/prompts/<slug>-<date>.md. Workflow: /deep <target> -> paste prompt into claude.ai Research mode -> wait for 100+ source output -> paste output into Claude Code -> /enrich (reads target_path, validates, symmetric back-links, /ingest YES recommendation) -> paste recommended /ingest command -> entity graph enrichment + audit chain. Four interactions total; zero reformatting friction; zero slug drift. Distinct from /research (shorter-form via WebFetch). Primary use: institutional-grade 100+ source research on a market-linked topic where output becomes canonical reference doc referenced by /brief, /invest, /challenge."
allowed-tools: Read, Write, Bash, Grep, Glob, Agent

---

# /deep -- Research prompt generator with target-path interop (v2 SOTA)

Compose a claude.ai Research mode prompt that yields output pre-formatted for zero-friction downstream skill integration, including explicit target-path signaling to /enrich v9.

## When to use

"I want 100+ source institutional-grade research on a market-linked topic (ticker, sector, thesis, regime) where the output becomes a canonical reference doc at `Atlas/sources/<domain>/ref-<slug>.md` referenced by multiple downstream skills."

Not for:
- Quick multi-source research (use direct WebSearch + WebFetch tool calls)
- Single-ticker institutional analysis (use `/invest` -- uses /deep output as input)
- Thesis stress-test (use `/challenge` -- uses /deep output as evidence)
- Personal / non-market-linked topics

## Invocation

| Syntax | Behavior |
|---|---|
| `/deep <topic-slug>` | Compose prompt on topic; default reference-doc shape |
| `/deep <ticker>` | Compose equity-deep-dive framing with ticker as primary |
| `/deep <thesis-stem>` | Compose thesis-deep-dive with matching active thesis |
| `/deep <topic> --interactive` | Ask clarifying questions before composing |
| `/deep <topic> --preview` | Show composed prompt without writing to vault |

## Execution Rules

- **Subagent dispatch is MANDATORY when specified by phase** (Step 2.5 dispatches `source-aggregator`). Pre-emptive skip based on judgment ("I can find sources inline", "the topic is well-covered already") is FORBIDDEN. The subagent decides source-quality applicability via its own return contract; the parent skill dispatches and validates the return. Legitimate fallback fires ONLY on (a) contract violation -- subagent return missing required fields (table columns, abstracts, blocked-domain summary), OR (b) actual dispatch failure -- timeout, rate limit, tool-denial, hard subagent crash. Pre-emptive skip surfaces in Step 6 audit as **DEVIATION** (not "fallback"). Quality preserved by additive design: existing Step 2 vault-context Glob/Grep stays intact; source-aggregator adds external candidate sources on top.

## Process

### 1. Load portfolio context (parallel Read)

Read: `private/holdings-taxable.md`, `private/holdings-ira.md`, `wiki/hot.md`.

Extract: current positions with cost basis + account split; active thesis exposure percentages (flag doctrine trigger trips); allocation state (deployed/pending/dry powder); kinetic positioning; recent earnings protocol triggers.

### 2. Load vault context relevant to target (Glob + Grep)

Identify:
- `Atlas/sources/<domain>/ref-*.md` matching primary topic tags -> peer refs
- `Atlas/concepts/investing/theses/thesis-*.md` matching thesis tags -> active theses
- `wiki/investing/analyses/*.md` matching ticker -> existing analyses to reconcile
- `wiki/entities/tickers/<T>.md` and `wiki/entities/companies/<N>.md` for substantive entities

Build "existing vault context" block with brief scope notes per file.

### 2.5. DELEGATED dispatch to `source-aggregator` subagent (PREFERRED path; Phase C wiring 2026-05-02)

**MANDATORY** (per Execution Rules): dispatch first, no pre-emptive skip. Subagent handles N/A returns gracefully (e.g., topic with sparse external coverage -> empty ranked table + "low candidate corpus" synthesis + confidence: LOW; that is a SUCCESSFUL dispatch).

Use the Agent tool with subagent_type `source-aggregator`. Pass input: `{research_target: "<target slug + framing from Step 1>", primary_topic_tags: [<from Step 3 derivation if available, else inferred>], existing_vault_refs: [<list from Step 2>]}`. The subagent searches preferred-domain whitelist (sec.gov, FRED, dataroma, PubMed, Cochrane, claude.com/docs, etc.) and skips blocked domains (Bloomberg paywalled, WSJ paywalled, Investopedia, Seeking Alpha, etc.) per ref-evidence-hierarchy.md, dedupes against existing Atlas/sources/ refs, and returns a ranked source candidate table + 50-80 word abstracts per candidate + vault-duplicate flags + blocked-domain skip summary.

Validate subagent return:
- Markdown table with columns [Rank | URL | Tier | Freshness | Vault dup? | Relevance]
- Source tier letters (A primary / B Tier-1 wire / C aggregator)
- 50-80 word abstracts per ranked candidate (not 30, not 150)
- Blocked-domain skip summary present (so we know nothing was silently missed)
- Aggregation confidence rating

On contract violation OR dispatch failure: fall through to inline WebSearch + WebFetch source discovery during Step 4 prompt composition. Surface fallback in Step 6 audit.

On dispatch success: inject the ranked source table + abstracts into the composed Research-mode prompt's "EXISTING VAULT CONTEXT" + "MANDATORY OUTPUT FORMAT" sections per the prompt template. Use vault-duplicate flags to recommend continuing existing refs vs onboarding new ones.

### 3. Derive canonical slug + target_path + frontmatter fields

From target:
- `slug` = lowercase-kebab-case of primary target (e.g., `orbital-compute-deep-dive`, `geopolitical-regime-allocation`)
- `domain` = investing | career | supplements | golf | tech | meta
- `target_path` = `Atlas/sources/<domain>/ref-<slug>.md` (this is the value Research mode will emit in the `target_path:` frontmatter field)
- `primary_topic_tag`, `secondary_topic_tags`, `ticker_tags`, `thesis_tag` derived from target framing

### 4. Compose prompt using template

10 mandatory sections. Template markers (`=== BEGIN RESEARCH MODE PROMPT ===`, `=== END RESEARCH MODE PROMPT ===`) MUST be byte-exact for downstream parsing.

### 5. Write to wiki/research/prompts/<slug>-<date>.md

F11 Phase C discipline (set flag before Write). Canonical frontmatter on the prompt file:

    ---
    categories: [wiki]
    type: prompt
    created: <today>
    updated: <today>
    status: active
    tags:
      - topic/<primary-topic>
      - topic/deep-research
    related:
      - "[[<domain-moc-stem>]]"
      - "[[<matching-thesis-stem-if-any>]]"
    ---

    # Deep Research prompt -- <target>

    <full prompt content below, to be pasted into claude.ai Research mode>

### 6. Print workflow reminder (4 steps) + subagent dispatch report

**Subagent dispatch report** (Phase C wiring 2026-05-02): emit one of:
- `Step 2.5 source-aggregator: DISPATCHED` -- subagent ran, sources injected into prompt
- `Step 2.5 source-aggregator: FALLBACK (<reason>)` -- legitimate dispatch failure; inline WebSearch+WebFetch source discovery during Step 4
- `Step 2.5 source-aggregator: DEVIATION (<judgment>)` -- pre-emptive skip; flag as discipline breach + sessions-log entry

Then print:

    /deep prompt written to: wiki/research/prompts/<slug>-<date>.md

    Workflow:
    1. Open file; copy everything between "=== BEGIN RESEARCH MODE PROMPT ===" and "=== END RESEARCH MODE PROMPT ===" markers
    2. Paste into a fresh claude.ai Research mode conversation; wait 20-60 min for 100+ source output
    3. In Claude Code: attach Research output + type /enrich
       - v9 reads target_path in output frontmatter; places at <target_path> directly
       - Symmetric back-links fire on peer refs + theses + entities
       - /ingest recommendation fires YES
    4. Copy recommended /ingest command; paste; done
       - Marker signature extraction into existing entity notes
       - Section-mapped routing (Financial signals / Thesis Fit / Risks / Catalysts / Recent)
       - Body preservation sha256 invariants
       - Audit chain: source -> ingest report -> entities

    4 interactions. Zero reformatting. Zero slug drift.

## Mandatory prompt template (v2 -- bytes emitted by /deep)

Every /deep-composed prompt contains these sections verbatim (with `<placeholder>` fields filled from context).

=== BEGIN RESEARCH MODE PROMPT ===

## ROLE

You are conducting institutional-grade research for a single-user portfolio management system. Your output will become a canonical reference document at `<target_path>` that primes every subsequent analysis on <topic>. Output: a SINGLE markdown document with canonical YAML frontmatter (including `target_path` as a required field) + numbered-section body. No commentary before or after the markdown. No meta-discussion of the task.

## CONTEXT

<Portfolio context block, auto-composed from step 1>

- Combined portfolio: ~$<amount> (Taxable ~$<N> + IRA ~$<M>)
- Current positions (deployed): <list>
- Pending orders / limits: <list with triggers>
- Dry powder: $<amount>
- Active thesis exposure: <per-thesis % + doctrine status per [[doctrine.template]]>
- Kinetic thesis positioning: <framing + time-conditional triggers>
- Recent earnings protocol triggers: <upcoming catalysts>

## EXISTING VAULT CONTEXT (your output should COMPLEMENT, not duplicate)

<Peer vault files block from step 2 -- list peer refs, thesis essays, analyses, entity notes with scope notes>

Your output is the STRUCTURAL FRAMEWORK for <topic>. Specific enough to be decision-grade; general enough to complement, not overlap, the peer refs listed above.

## TASK

<User-specified research target + framing + scope>

Produce a comprehensive <topic> reference with the structure below. Depth over breadth: each numbered H2 section 500-1,000 words with specific numbers, historical precedents, actionable signals.

## MANDATORY OUTPUT FORMAT (violating any constraint = task failure)

### Frontmatter (MUST be first content; emit verbatim with values filled)

    ---
    categories: [sources]
    type: reference
    target_path: <target_path>
    created: <today-YYYY-MM-DD>
    updated: <today-YYYY-MM-DD>
    status: active
    confidence: high
    tags:
      - topic/<primary-topic>
      - topic/<secondary-topic>
      - topic/<tertiary-topic-if-applicable>
      <for each substantive ticker, UPPERCASE:>
      - ticker/<TICKER>
      <for each matching thesis:>
      - thesis/<thesis-stem>
    aliases:
      - <natural alias 1>
      - <natural alias 2>
    related:
      - "[[<domain-moc-stem>]]"
      - "[[thesis-<matching-if-any>]]"
      - "[[ref-<peer-1>]]"
      - "[[ref-<peer-2>]]"
      <for each substantive entity with existing vault note:>
      - "[[<TICKER>]]"
    ---

The `target_path:` field is CRITICAL -- /enrich v9 reads it to place the file at the exact intended path without autonomous slug derivation. Emit it verbatim with the value specified in ROLE.

### Body (follows frontmatter immediately)

    # <Document Title>

    ## 1. <Section A>
    <600-900 words; fact-dense; inline citations every 2-3 facts>

    ## 2. <Section B>
    ...

    ## N. <Section N>

    ## Footnotes (optional -- only if using numbered footnote citation style)
    [^1]: <Source>, <date>
    ...

### HARD CONSTRAINTS

1. **Minimum length**: 6,000 words (outputs <5,000w are TASK FAILURE; target 6,500-7,500w).
2. **target_path emitted**: `target_path:` line in frontmatter, value exactly `<target_path>` from ROLE.
3. **Numbered H2 TOC**: At least 5 H2 headers formatted `## N. <Title>`. No unnumbered H2.
4. **Citation count**: At least 100 inline citations. Format: `(Source: <authority-or-url>, <date>)` or numbered footnotes `[^N]` collected at document bottom. Consistency within document.
5. **Voice**: Third-person analytical throughout. FORBIDDEN: "I", "my", "we", "our", conviction language. Not a thesis essay.
6. **Entity claim format** (for each substantively-discussed ticker or company):

       - <ENTITY>: <metric-type> <value> <unit-if-applicable> <date> (per <source>)

   Examples:
   - `- NVDA: Q4 2025 revenue $39.3B (per NVDA 10-K filed 2026-02-14)`
   - `- LMT: backlog $194B Q4 2025 (per LMT earnings call 2026-01-28)`

   Enables automated marker-signature claim extraction via /ingest.

7. **Substantive entity sections**: Each ticker/company mentioned >=3 times gets a dedicated H3 under the relevant H2 with canonical subsections (aligns with /ingest section-target mapping):

       ### <TICKER> -- <Company Name>
       #### Financial signals
       - <entity-claim format>
       #### Thesis Fit
       <prose + claims>
       #### Risks
       <prose + claims>
       #### Catalysts
       <prose + claims>
       #### Recent
       <dated items>

8. **Numbers + dates**: Every factual claim includes specific numbers with units and dates where applicable.
9. **No meta-commentary before or after**: Start with `---` frontmatter opener; end with last section's last sentence.
10. **No fenced code block around frontmatter**: Output IS a markdown document. Frontmatter is plain `---\n...\n---\n`, not inside fenced code.

## SOURCE HIERARCHY

Strongly preferred (institutional and primary):

<Auto-composed per domain -- see /deep Process step 2 domain mapping>

Explicitly avoid:
bloomberg.com, investopedia.com, macrotrends.net, fintel.io, wsj.com, ft.com, barrons.com, morningstar.com, seekingalpha.com, statista.com, tipranks.com, gurufocus.com, simplywall.st, businessquant.com, spglobal.com, factset.com, pitchbook.com, capitaliq.com, finance.yahoo.com, marketbeat.com, fool.com, zacks.com, tradingview.com

## QUALITY BAR

- Decision-grade: usable by /invest, /brief, /challenge without further research
- Institutional depth: every quantitative claim cited to primary or authoritative secondary source
- Specific not general: "Brent rose $17/bbl in 72 hours on the May 2019 tanker seizure" beats "oil rose on tensions"
- No hedging: "approximately"/"roughly"/"possibly" only where genuinely uncertain; default to specific numbers with attribution
- Framed around ACTIONABILITY for the single-operator portfolio state in CONTEXT; not academic neutrality
- Generalizable beyond the current tactical scenario

Produce the document now, starting with the `---` frontmatter opener.

=== END RESEARCH MODE PROMPT ===

## Interoperability guarantees

When Research output following this prompt is pasted into Claude Code + onboarded via /enrich:

1. **target_path read from frontmatter** -- /enrich v9 detects `target_path`, validates path-guards, uses as explicit placement (bypasses Rule 1-22 autonomous routing, no slug drift)
2. **Placement at `<target_path>`** -- deterministic from /deep's intent
3. **No collision** -- assuming `target_path` is a new file
4. **Frontmatter used verbatim** -- /enrich validates rather than composes
5. **Symmetric back-links fire** on every peer file in `related:`
6. **Substantive entity back-links fire** on existing entity notes
7. **knowledge-moc row added** (type: reference)
8. **/ingest recommendation fires YES** under v8.1 binary logic
9. **Copy-paste /ingest command** surfaces
10. **/ingest v2 extracts cleanly**: marker signatures from entity-claim format, section-mapped routing, per-fact provenance

## Examples

### Example 1: /deep on a sector thesis

`/deep orbital-compute-deep-dive`

Loads positions, active thesis, peer refs, analyses, entity notes. Composes prompt with `target_path = Atlas/sources/investing/ref-orbital-compute-deep-dive.md`. Research mode output emits that `target_path` in frontmatter. /enrich v9 reads it, places at exact path. /ingest distills 80+ claims across entity notes.

### Example 2: /deep on specific ticker

`/deep NVDA` -> `target_path = wiki/investing/analyses/nvda-deep-dive-<date>.md`. Output routes via `target_path` to exact location; richer than standard /invest output.

### Example 3: /deep on geopolitical regime

`/deep iran-kinetic-allocation` -> `target_path = Atlas/sources/investing/ref-iran-kinetic-regime-<date>.md`. Output routes explicitly.

### Example 4: --interactive

Non-obvious target; /deep asks clarifying framing questions before composing.

### Example 5: --preview

Show composed prompt without writing prompt file. Useful for review.

## Coordination with downstream skills

Pipeline: /deep -> Research mode -> /enrich (reads `target_path`) -> /ingest (extracts claims).

Shared invariants: canonical frontmatter schema, tag vocabulary (topic/ticker/company/thesis), path-guards, substantive-mention threshold, symmetric back-linking, ASCII commit bodies, Co-Authored-By suppressed.

## Related skills

- `/invest` -- uses /deep output as input
- `/challenge` -- uses /deep output as evidence
- `/enrich` v9 -- onboards Research output (reads `target_path`)
- `/ingest` v2 final -- distributes Research output's entity claims
