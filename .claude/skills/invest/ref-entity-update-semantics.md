---
categories: [sources]
type: reference
created: 2026-04-22
updated: 2026-04-22
status: active
confidence: high
tags:
  - topic/knowledge-base-semantics
  - topic/entity-graph
  - topic/claim-extraction
  - topic/body-preservation
  - topic/contradiction-resolution
related:
  - "[[invest]]"
  - "[[ingest]]"
  - "[[enrich]]"
  - "[[ref-research-methodology]]"
word_count: 9716
sources_count: 37
---

# Entity-update semantics for the compounding vault

## Table of contents

1. Introduction and scope
2. Branching logic -- CREATE vs UPDATE
3. CREATE branch
4. UPDATE branch protocol
5. Claim-to-section mapping (shared routing rules)
6. Marker-signature deduplication (LLM-variance-resistant)
7. Contradiction detection and tiering
8. Per-fact provenance format
9. Body-preservation sha256 invariant
10. Zero-new-claims short-circuit (idempotency)
11. Symmetric back-link protocol
12. Coordination with /ingest and /invest
13. Sources and references

## 1. Introduction and scope

This reference defines the canonical entity-update semantics shared between two Claude Code skills that mutate the Obsidian vault entity graph at `<VAULT_ROOT>/wiki/entities/`. Phase L of `/invest` and Phase F of `/ingest` both read this document as the binding specification for how claims are written into ticker notes (`wiki/entities/tickers/<TICKER>.md`) and company notes (`wiki/entities/companies/<Name>.md`). The specification is drop-in compatible across the two skills: a reader of an entity note cannot determine from the text which skill inserted any given claim, because both skills adhere to identical dedup, routing, contradiction-tiering, provenance, and body-preservation rules [1].

The architecture is deliberately **append-only at the body layer**. Bodies of entity notes accumulate claims; they are never rewritten, reformulated, or retroactively edited except through a narrow Tier-1 supersede annotation that is itself an adjacent text addition rather than an in-place replacement. This choice follows the long-established design discipline of log-structured storage, which treats the write-once log as the source of truth and defers consolidation to read time or to explicit compaction passes [2]. The same discipline animates event-sourced application architectures, where the authoritative state is the ordered event stream rather than any current snapshot [3]. In a personal research context, append-only semantics pay off in three concrete ways: audit trails survive intact across months of updates; re-running an ingestion pipeline over the same source yields zero-diff idempotency; and adversarial regressions (a later source downgrading an earlier well-cited fact) are structurally prevented because no prior line can be silently removed.

Scope boundaries matter. This document governs the semantics of one atomic operation -- "accept a batch of candidate claims and reconcile them into one entity note" -- including all preconditions, invariants, and postconditions on that operation. It does **not** cover upstream concerns such as how claims are extracted from source documents, how source grades are assigned, how sources themselves are written, how the vault is indexed, or how commits are staged and pushed. Those are delegated to the respective skill `SKILL.md` and to parallel references such as `ref-research-methodology.md`, `ref-source-grading.md`, and `ref-commit-discipline.md`. Within its narrow scope, this reference is intended to be implementable by a third party from the text alone: every invariant is formalized, every edge case is enumerated, and every normalization rule is specified to the point of executable pseudocode. That level of rigor borrows from the data-integration literature, which has long argued that reproducible semantics in a multi-source knowledge base requires explicit specification of matching, merging, and conflict-resolution rules rather than reliance on ad-hoc heuristics [4].

The vault is modest in scale -- 28+ ticker notes, 5+ company notes, growing monthly -- but the semantics are engineered for institutional-grade correctness at arbitrary scale. The patterns encoded here trace to three lineages: large-scale collaborative knowledge bases such as Wikipedia and Wikidata, where conflict detection and revert discipline were first worked out at global scale [5][6]; semantic-web provenance standards such as PROV-O, which formalize the who-when-where of a fact [7]; and entity-resolution research, which provides the mathematical foundation for deduplication under noisy inputs [8][9].

## 2. Branching logic -- CREATE vs UPDATE

### 2.1 Filesystem existence check protocol

The first decision made by Phase L (`/invest`) and Phase F (`/ingest`) for each candidate entity is a binary branch: does a note already exist at the canonical path, or not? The check is performed with `pathlib.Path.exists()` on the resolved canonical stem, using the filesystem as the single source of truth [10]. For ticker entities the canonical path is `wiki/entities/tickers/<TICKER>.md` with the ticker uppercased; for company entities the canonical path is `wiki/entities/companies/<Name>.md` with the name in title case preserving spaces. Windows NTFS treats filenames as case-insensitive by default, while ext4 and APFS (unless explicitly configured) treat them as case-sensitive; this means a CREATE decision on macOS or Linux could inadvertently collide with an existing file on Windows if casing is inconsistent [11]. The resolver therefore performs a case-insensitive listing of the parent directory and matches against both the canonical stem and its case-folded variant before issuing the binary decision.

### 2.2 Deterministic rule

The rule is strictly deterministic -- no probabilistic scoring, no fuzzy matching, no embedding similarity [12]. If `path.exists()` returns `True`, the branch is UPDATE. Otherwise it is CREATE. Probabilistic entity linking is appropriate during upstream claim extraction (where a source document mentions "Nvidia" and the extractor must map it to `NVDA`), but is explicitly excluded from the CREATE-vs-UPDATE decision because any false positive introduces duplicate entities that must then be reconciled out of band, and any false negative silently overwrites history. The Fellegi-Sunter record-linkage framework establishes that optimal decisions over noisy matches require an explicit cost model over type-1 and type-2 errors [8]; the cost of false merges in an append-only KB is unbounded (data loss), so the decision is made at the one layer where the inputs are not noisy (canonical filesystem path) and is left deterministic there.

### 2.3 Path-collision edge cases

Three edge cases deserve explicit handling. **Ticker disambiguation** arises when an NYSE ticker and a foreign-exchange ticker share a symbol (e.g., `BRK` Berkshire vs a similarly-symboled European issue); the canonical convention is to use the primary-listing exchange's symbol unqualified and to suffix secondary listings with an exchange code (e.g., `BRK-LSE.md`). **Company-alias overlap** occurs when two distinct companies share a name stem (e.g., "Delta" the airline vs "Delta" the faucet maker); the canonical convention is to disambiguate via a parenthetical suffix in the filename (`Delta (airline).md`) with a `company_alias` field in frontmatter enumerating the aliases that resolve to this note. **Unicode normalization** of filenames follows NFC (Canonical Composition), because HFS+ historically normalized to NFD and modern APFS preserves whatever form was written, creating a class of cross-platform filename collisions that the specification resolves by pre-normalizing all candidate stems to NFC before the existence check [13].

## 3. CREATE branch

### 3.1 Grounding in _templates/entity.md

A CREATE operation never composes frontmatter from scratch; it always reads from `_templates/entity.md` and parameterizes. Templates are a correctness mechanism, not a convenience. YAML is a syntactically fragile format whose 1.2.2 revision still permits multiple ambiguous constructs (implicit string vs boolean for the token `yes`; folded-block vs literal-block scalars; flow-style vs block-style collections) [14]. A template that has been round-tripped through `ruamel.yaml` in round-trip mode establishes a reference byte-pattern that downstream parsers are guaranteed to accept; composing frontmatter as raw string concatenation invites subtle parse errors that surface only when Obsidian or a downstream pipeline attempts to read the note [15].

```yaml
# _templates/entity.md -- canonical frontmatter skeleton for a ticker
---
categories: [entity, ticker]
type: ticker
ticker: NVDA
sector: semiconductors
thesis: orbital-compute
accounts: []
tags:
  - ticker/NVDA
  - topic/semiconductors
  - thesis/orbital-compute
related:
  - "[[investing-moc]]"
status: active
confidence: medium
created: 2026-04-22
updated: 2026-04-22
---
```

### 3.2 Frontmatter schema for ticker vs company entities

Ticker notes and company notes share most fields but diverge on two axes. Tickers carry a `ticker` scalar and a `sector` scalar; companies carry a `company` scalar and an `industry` scalar (industry being a finer classification than sector). Tickers are tagged under the `ticker/<SYMBOL>` namespace; companies under `company/<name-kebab>`. Both participate in the `thesis/<thesis-slug>` namespace when applicable. The `accounts` field is a list of portfolio account identifiers that hold the entity (empty list by default); this field is meaningful only for tickers, but is kept present-with-empty-list on companies to simplify index-building code. The `categories` field follows the vault's categorical taxonomy, which restricts to a closed vocabulary of about a dozen tokens [`entity`, `ticker`, `company`, `sources`, `moc`, `daily`, `meta`, ...] [16].

### 3.3 5-section body template

The body of every entity note, whether CREATED or UPDATED, adheres to a fixed five-section skeleton plus Overview and Sources wrappers:

```markdown
# NVDA

## Overview
<one-paragraph canonical description>

## Financial signals
<claims about revenue, margin, cash flow, guidance, EPS, ROIC, FCF, backlog>

## Thesis fit
<claims supporting or challenging an active thesis>

## Risks
<customer-concentration, regulatory, supply-chain, competitive, macro-sensitivity claims>

## Catalysts
<earnings dates, product launches, policy events, M&A pipeline>

## Recent
### 2026-04-15
<dated event claims under ISO-date subheaders, newest-first>

## Sources
- [[source-stem-1]]
- [[source-stem-2]]
```

The five-section schema is the interface contract between the extraction layer and the entity layer: any claim accepted by the routing rules of Section 5 of this specification fits into exactly one of these five sections. The Overview paragraph is CREATE-time only and is not mutated by UPDATE operations except under a deliberate manual curation pass that is outside the scope of this specification. The Sources list is maintained as the set union of all sources that have ever contributed a claim, in alphabetical order.

### 3.4 MOC back-link cascade

Every CREATE operation emits a back-link cascade into at least one Map-of-Content (MOC) note. Tickers cascade into `wiki/MOCs/investing-moc.md`; companies cascade into `wiki/MOCs/career-moc.md` by default, with routing to a domain MOC (`aerospace-moc.md`, `semiconductors-moc.md`) when the entity's sector matches a registered domain-MOC entry in the `MOC_STEMS` index. The cascade is symmetric: the entity note's frontmatter `related:` field gains `[[<moc-stem>]]`, and the MOC body gains a bullet line under its appropriate grouping. This mirrors Wikipedia's category-membership discipline where every substantive article belongs to at least one category and every category page lists its members [17]. Symmetric maintenance of both directions is what makes Obsidian's graph-view traversal accurate; Obsidian resolves wikilinks by text match rather than by explicit ID, so the symmetric discipline is the only defense against orphan links [18].

### 3.5 Post-write gates

Immediately after the CREATE Write, Phase L runs four gates before declaring success. First, a `ruamel.yaml` round-trip parse of the frontmatter verifies YAML validity [15]. Second, the tag vocabulary guardrail rejects any tag outside the four registered namespaces (`topic/`, `ticker/`, `company/`, `thesis/`); unknown namespaces halt the pipeline rather than propagate. Third, the path-guard re-confirms the file was written inside `wiki/entities/` and nowhere else (a defense against path-traversal and symlink-following bugs in upstream stem composition) [19]. Fourth, the body bytes are sha256-hashed and the digest recorded to an in-memory cache keyed by entity stem; this seed digest becomes the reference for the future UPDATE path's body-preservation invariant [20].

## 4. UPDATE branch protocol

### 4.1 Pre-edit state capture

The UPDATE branch begins by reading the existing note into memory and computing `before_sha256 = hashlib.sha256(body_bytes).hexdigest()` where `body_bytes` excludes the YAML frontmatter and the trailing newline-delimited sentinel that separates frontmatter from body [21]. The frontmatter is parsed with `ruamel.yaml` in round-trip mode so that key order, quoting style, and comment placement are preserved across the eventual re-serialization [15]. Section offsets are detected by scanning for the six canonical H2 headers (`## Overview`, `## Financial signals`, `## Thesis fit`, `## Risks`, `## Catalysts`, `## Recent`, `## Sources`) and recording byte ranges; under `Recent`, the nested H3 ISO-date subheaders are enumerated so that a new dated event can be inserted at the correct chronological position.

### 4.2 Existing claim extraction

Each of the five content sections is parsed as a list of bullet lines conforming to the provenance-line regex:

```python
CLAIM_RE = re.compile(
    r"^- (?P<text>.+?) \((?P<grade>[A-F])(?:\+|-)?, per \[\[(?P<source>[^\]]+)\]\]\)$"
)
```

Each surviving line yields a `(text, grade, source)` triple from which a marker signature is computed as defined in Section 6. The signatures of all existing claims form a set used during dedup. Lines that do not match the regex are treated as opaque and are preserved verbatim in the body; the specification never modifies a line it does not understand, which is a direct application of Postel's robustness principle to entity notes [22].

### 4.3 Per-new-claim decision loop

For each candidate claim in the incoming batch, the skill executes the following decision loop in strict order:

1. Compute marker signature.
2. If signature is already present in the existing-claims signature set, classify as DEDUP and record a dedup count for the audit report.
3. Else, check for contradiction: scan existing claims for a signature whose `(entity, metric)` prefix matches but whose `(value, date)` tail differs. If found, apply the tiering rules of Section 7.
4. Else, route the claim to its target section using Section 5 rules.
5. Emit an insertion plan consisting of `(section, offset, line)`.

The loop is purely functional -- no file mutations occur yet. At its conclusion the skill holds an in-memory insertion plan, a dedup count, and a contradiction-resolution log [23].

### 4.4 Zero-new-claims short-circuit

If the insertion plan is empty, meaning every incoming claim was either deduped or Tier-3 rejected, the skill takes the short-circuit path: the Edit call is **skipped entirely**, the `updated:` frontmatter field is **not bumped**, and the file is excluded from the Phase O narrow-staging pathspec (F14 discipline). This produces exact zero-diff idempotency: re-running `/invest` or `/ingest` over a fully-reconciled source yields a byte-identical vault, a property shared with well-designed content-addressable systems [24] and event-sourced read models that are deterministic functions of their event stream [3]. The short-circuit preserves the semantic meaning of the `updated:` field -- it records a real content change, not a re-execution timestamp.

### 4.5 Apply batch Edit

If the insertion plan is non-empty, the skill issues a single atomic Edit call that applies all insertions in one pass. Partial-section rewrites are prohibited: an insertion must be a pure byte-range insertion at a specific offset, not a read-modify-write of a whole section. This rule is enforced structurally by the additive-only diff assertion of Section 9.4. The atomicity discipline follows standard database practice -- all-or-nothing commit boundaries -- and prevents the partial-failure class of bugs in which two of three intended insertions land but the third fails, leaving the note in a state that is neither the pre-edit state nor the intended post-edit state [25].

### 4.6 Post-edit gates

After the Edit, the skill recomputes `after_sha256` and asserts `before_sha256 != after_sha256` (insertions occurred, which is required given the non-empty plan; if equal, a silent no-op has happened and the pipeline halts). It then performs the additive-only diff assertion of Section 9.4. Only after both gates pass is the `updated:` field bumped to today's ISO date and the frontmatter re-serialized. The order matters: body gates first, frontmatter bump last, so that a body-gate failure leaves `updated:` as a truthful record of the last successful update rather than an optimistic one [26].

### 4.7 Related-field extension with back-link wikilink

The last step of a successful UPDATE is to extend the frontmatter `related:` field with any new sources that contributed inserted claims, producing `[[<source-stem>]]` entries inserted in alphabetical order within their group (the group for sources is "analyses and sources", ordered after MOC and thesis groups). This is the outbound half of the symmetric back-link protocol; the inbound half, the source note or analysis note gaining a `[[<TICKER>]]` entry, is performed in the same phase but on the other file. Both halves are individually gated by the two-layer sha256 invariant of Section 11.4.

## 5. Claim-to-section mapping (shared routing rules)

### 5.1 Routing rules table

Routing is performed by a small decision table evaluated top-down, returning the first matching section. The table is identical for `/invest` Phase L and `/ingest` Phase F -- this identity is the core of the drop-in-compatibility guarantee [4].

| Priority | Claim semantic                                                 | Target section      |
|----------|----------------------------------------------------------------|---------------------|
| 1        | Dated event (<= today) with verb of occurrence                 | Recent              |
| 2        | Dated future event (earnings date, launch, policy window)      | Catalysts           |
| 3        | Risk condition (concentration, regulation, supply, competitor) | Risks               |
| 4        | Thesis-relevant support-or-challenge statement                 | Thesis fit          |
| 5        | Quantitative financial metric                                  | Financial signals   |
| 6        | Any other source-attributable fact                             | Claims from [[source]] (date) fallback block within the best-guess section |

The priority ordering reflects specificity: a dated event that also happens to be financial belongs under Recent because its temporal signature is the more distinctive descriptor. Priority is stable across re-runs so that identical claim inputs always route to identical sections.

### 5.2 Financial signals

Claims whose predicate includes revenue, revenue-growth, gross-margin, operating-margin, net-margin, EPS (GAAP or adjusted), free cash flow, operating cash flow, ROIC, ROCE, backlog, bookings, deferred revenue, guidance (any forward quantitative statement), or capital-expenditure route to Financial signals. The metric vocabulary is the closed set enumerated in `ref-metric-ontology.md` (a separate reference), against which every candidate predicate is lowercased-and-kebab-matched before dispatch. For example, "AMD MI300 revenue reached USD 5.5B in FY2025" routes here because `mi300-revenue` resolves to the family `product-line-revenue` which is a registered Financial signals metric [27].

### 5.3 Thesis fit

Thesis-relevant claims are those whose text either explicitly invokes a registered thesis slug (e.g., `orbital-compute`, `defense-modernization`, `memory-cycle-recovery`) or whose predicate has been annotated by the extractor with a `supports:` or `challenges:` relation to an active thesis in the entity's frontmatter. For example, "NVDA Blackwell sampling yields are trending above plan" supports the `orbital-compute` thesis because elevated yields accelerate the revenue ramp that the thesis depends on; the claim routes to Thesis fit. The section is not a duplicate of Financial signals -- it specifically captures the thesis-conditional interpretation, with the thesis slug surfaced in the claim text [28].

### 5.4 Risks

Risk-section routing covers five canonical categories: customer concentration (top-N revenue concentration above a configurable threshold), regulatory exposure (pending agency action, sanctions, antitrust), supply chain (single-source component, geopolitical chokepoint), competitive threat (specific named competitor with disclosed share-shift evidence), and macro sensitivity (rates, FX, commodities, cycle exposure). A claim such as "LMT F-35 program risks concentration with 30%+ of backlog tied to a single customer category" routes to Risks because of the concentration predicate.

### 5.5 Catalysts

Catalysts capture future dated events: earnings dates, product-launch windows, policy events (FOMC, CPI prints, agency rulings), M&A pipeline markers, and scheduled investor-day or analyst-day dates. Each catalyst line includes an ISO date (exact if known, month granularity if not). "MU FY Q3 2026 earnings expected 2026-06-25 post-market" is a canonical catalyst line.

### 5.6 Recent

Recent captures dated events that have already occurred (on or before today). Entries live under ISO-date H3 subheaders sorted newest-first. An acquisition close, a strike action, a partnership announcement, a lawsuit filing, or a material SEC filing are all Recent candidates. "LMT 2026-03-14 awarded USD 4.1B Army IFPC follow-on contract" lives at the top of the Recent section if the date exceeds all existing entries, else at the first position whose subheader is less-than-or-equal to the new date.

### 5.7 Fallback -- Claims from [[source]] (date) section

When no priority-1-through-5 rule matches, the claim is placed under a section-local fallback block with header `### Claims from [[<source-stem>]] (<date>)` created in the best-guess parent section (typically Financial signals for quantitative residue, else Thesis fit). The fallback block preserves source grouping when routing uncertainty is high and is intentionally visually distinct so that periodic manual re-routing passes can promote claims into proper sections.

## 6. Marker-signature deduplication (LLM-variance-resistant)

### 6.1 Signature tuple

Every claim is reduced to a four-tuple signature `(entity_stem, metric_slug, value, date)` before any dedup comparison. The tuple, and nothing else, determines equivalence: two claims with identical tuples are considered the same claim regardless of surface text. (vNEXT 2026-06-09: the INGEST:claims tuple gained an 8th field `prov:` -- machine provenance per ref-dw-topology.md Section 7. `prov` is PASS-THROUGH here: the dedup signature stays this four-tuple; claim-distributor and /ingest carry prov into the inserted line unchanged; legacy 7-field claims remain valid.) This design directly addresses the **LLM variance problem**: an extractor may paraphrase "NVDA Q4 FY2025 revenue was USD 39.3B" as "Nvidia reported fourth-quarter fiscal 2025 revenue of $39.3 billion" or "NVDA FY25Q4 topline printed at 39.3 billion dollars", all of which should collapse to one entry. Text-match dedup would fail; signature dedup succeeds by reducing each form to `(NVDA, revenue-quarterly, 39.3e9, 2025-Q4)` [9][29].

### 6.2 Entity stem normalization

Tickers are uppercased and stripped of exchange suffixes for signature purposes (the exchange qualifier is preserved in the note filename but not in the signature tuple, because cross-exchange identity of the same underlying issuer should collapse). Company names are lowercased, kebab-cased, and resolved against `aliases.yml` in the vault root so that "Nvidia", "NVIDIA Corp", "Nvidia Corporation", and "NVDA Corp" all normalize to `nvidia`. Alias resolution is exact-match only -- fuzzy matching is deferred to upstream extraction, per the deterministic-decision discipline of Section 2.2 [8].

### 6.3 Metric slug normalization

Metric slugs are drawn from `ref-metric-ontology.md`, which enumerates about 80 canonical metrics with their synonym sets. Examples: `revenue-quarterly` absorbs "quarterly revenue", "Q revenue", "topline Q", "net sales Q"; `gross-margin` absorbs "GM", "gross profit margin", "gross margin percent"; `fcf-margin` absorbs "free cash flow margin", "FCF as % of revenue". The dictionary is closed: an extractor proposing a slug not in the dictionary either maps to the nearest registered slug or routes the claim to the fallback Section 5.7 block with a literal-text predicate. This closed-vocabulary approach follows the best practice established by YAGO and DBpedia, which treat their property vocabularies as finite ontologies rather than open sets [30][31].

### 6.4 Value normalization

Numeric values are canonicalized to a single representation per kind. Percent-equivalence collapses `37%`, `0.37`, `0.370`, and `37.0 percent` to the float `0.37` (tolerance 1e-6). Currency-scale normalization collapses `$194B`, `USD 194 billion`, `194000M`, and `$194,000,000,000` to the integer `194_000_000_000` with an attached currency code (USD by default; explicit EUR, GBP, JPY prefix when non-USD). SI-prefix handling enforces K = 1e3, M = 1e6, B = 1e9, T = 1e12; non-standard prefixes (mm for thousands in trade-floor notation; bn or bln for billion) are accepted on input but normalized out on signature. The normalization pipeline is specified in executable form:

```python
def normalize_value(raw: str) -> tuple[str, float]:
    """Return (kind, canonical_float) for a raw value string.
    kind in {"percent", "currency-usd", "currency-eur", "ratio", "count"}.
    """
    s = raw.strip().replace(",", "").replace(" ", "")
    if s.endswith("%"):
        return ("percent", float(s[:-1]) / 100.0)
    cur = None
    if s.startswith("$") or s.upper().startswith("USD"):
        cur = "currency-usd"; s = s.lstrip("$").removeprefix("USD")
    elif s.upper().startswith("EUR"):
        cur = "currency-eur"; s = s.removeprefix("EUR")
    mult = 1.0
    if s and s[-1].upper() in "KMBT":
        mult = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}[s[-1].upper()]
        s = s[:-1]
    return (cur or "count", float(s) * mult)
```

### 6.5 Date normalization

Dates are canonicalized to one of three forms: exact ISO (`2025-11-19`), quarter form (`2025-Q4`), or year form (`2025`). Fiscal-year vs calendar-year disambiguation is handled by a per-entity `fiscal_year_end` field in frontmatter (absent means calendar year); a claim stated in fiscal-year terms is tagged with a `FY` prefix in the signature date field (`FY2025-Q4`) so that a fiscal-Q4 and a calendar-Q4 never collide in dedup. Quarter form is treated as equivalent to "end of that quarter" for superseding-newness comparisons in Section 7 but as a distinct signature tail for dedup; "2025-Q4" and "2025-12-31" do **not** dedup against each other because one is a period and the other is an instant [32].

### 6.6 Hash-based signature derivation

The four-tuple is serialized in a canonical form -- `"{entity}|{metric}|{value}|{date}"` with pipes as separators and no whitespace -- and hashed via `hashlib.sha256`:

```python
def signature(entity: str, metric: str, value: float, date: str) -> str:
    raw = f"{entity}|{metric}|{value:.6g}|{date}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]  # 64-bit prefix for speed
```

A 16-hex-character (64-bit) prefix is sufficient for a vault of O(10^5) claims: the birthday-paradox collision probability is negligible below that scale, and the truncation saves index memory [20][21]. The full digest is retained in audit logs for forensic purposes.

### 6.7 Why signature-based dedup beats text-match

Consider the following five paraphrases of one fact, all plausibly emitted by different LLM extraction runs:

1. "NVDA data center revenue reached USD 47.5B in FY2025 Q4."
2. "Nvidia's Q4 FY25 data center segment posted $47.5 billion in revenue."
3. "NVDA reported 47,500M in FY2025-Q4 data-center sales."
4. "Fourth-quarter fiscal 2025 data center revenue at Nvidia was 47.5B USD."
5. "DC revenue: NVDA FY25Q4 = USD 47.5B."

All five reduce to the signature `(NVDA, dc-revenue-quarterly, 4.75e10, FY2025-Q4)`. Text-match dedup would insert five distinct lines; signature dedup inserts one and records four dedup hits in the audit report. The same machinery handles AMD MI300 ("MI300 revenue USD 5.5B FY25" vs "MI300X+MI300A FY2025 revenue = $5.5 billion") and MU HBM ("MU HBM3E shipments reached USD 1B QoQ in FQ2-26" vs "Micron FQ2 2026 HBM revenue at one billion").

## 7. Contradiction detection and tiering

### 7.1 Detection rule

A candidate claim contradicts an existing claim when their signatures share the `(entity, metric)` prefix but differ on `(value, date)` -- that is, the same quantity is asserted with different values, or the same value is asserted with different dates. The detection is computed in O(1) per candidate by maintaining a per-entity index keyed on the `(entity, metric)` prefix and mapping to a list of existing `(value, date, grade, source)` triples [4].

### 7.2 Tier 1 -- auto-resolve (newer supersedes older)

A candidate is Tier 1 when its date is strictly newer than the existing claim's date by more than 30 days **or** when it crosses a reporting-period boundary (e.g., existing claim dated `2025-Q3`, candidate dated `2025-Q4`) **and** its source grade is at least as high as the existing claim's grade. In this case the resolution is: **append the new line** with normal provenance, and **append a supersede-annotation line directly below the old line** (an adjacent text addition, not an in-place edit) of the form:

```markdown
- NVDA Q3 FY2025 revenue USD 35.1B (A, per [[nvda-10q-fy25-q3]])
  - [superseded by [[nvda-10k-fy25]] on 2026-03-27]
- NVDA Q4 FY2025 revenue USD 39.3B (A, per [[nvda-10k-fy25]])
```

The old line is never deleted; the audit trail survives intact. This mirrors the revision-preserving discipline of Wikipedia article histories, where no edit ever erases an earlier revision from the record [5][17].

### 7.3 Tier 2 -- flag (similar authority)

A candidate is Tier 2 when the `(entity, metric)` prefix matches but neither strict-newer-30-days nor period-boundary-crossing holds, and the candidate's source grade is within one letter of the existing grade (A/A-, A/B, B/C, etc.). Resolution: **append the new line with a NOTE suffix** referencing the conflicting prior line, and **increment the Tier-2 contradiction count** in the run's audit report. The analyst reviewing the audit resolves manually in a later curation pass. Worked example: two B-grade analyst reports disagree on AMD MI300 FY25 revenue (one says USD 5.2B, one says USD 5.8B); both lines remain, each with its own provenance, and the audit flags the discrepancy [33].

### 7.4 Tier 3 -- reject (lower authority)

A candidate is Tier 3 when the `(entity, metric)` prefix matches but the candidate's grade is two or more letters below the existing claim's grade. Resolution: **skip insertion**, **log to Tier-3-rejected list**, and **increment the Tier-3 count**. This prevents low-grade sources (e.g., a D-grade social-media post) from introducing noise into an entity note that already has A-grade primary-filing data on the same metric. The rejected candidate is preserved in the run's audit file so that a future promotion of the source's grade can reintroduce it [4][33].

### 7.5 Authority hierarchy (source grades)

Source grades follow the A>B>C>D>F hierarchy defined in `ref-source-grading.md`:

| Grade | Source class                                                               |
|-------|----------------------------------------------------------------------------|
| A     | Primary filings (10-K, 10-Q, 8-K, S-1), first-party transcripts, official agency data |
| B     | Top-tier analyst research (sell-side MDs, reputable independent research), major-paper reporting |
| C     | Second-tier analyst research, trade-press reporting, reputable industry blogs |
| D     | Social-media posts with named accounts, unverified forums, press releases from interested parties |
| F     | Anonymous rumor, chain emails, unsourced speculation                        |

The hierarchy is multiplicatively separated: an A-grade fact is treated as dominating a D-grade contradicting fact regardless of recency. This asymmetry reflects empirical evidence from enterprise RAG deployments that source-stratified retrieval outperforms undifferentiated retrieval on factual accuracy [34][35].

### 7.6 Temporal hierarchy

The 30-day and period-boundary thresholds balance two failure modes. Too-tight thresholds (e.g., 1 day) would cause innocent refinements of estimates to trigger supersede semantics inappropriately; too-loose (e.g., 365 days) would allow stale data to remain unchallenged past a full reporting cycle. The 30-day choice aligns with typical monthly analyst-update cadence; the period-boundary override ensures that quarterly reporting cycles always flush prior-quarter estimates [36].

### 7.7 Worked examples

**NVDA Q3 vs Q4 backlog supersede.** Existing: `NVDA data-center backlog USD 23B (A, per [[nvda-10q-fy25-q3]])` dated 2025-Q3. Candidate: `NVDA data-center backlog USD 31B (A, per [[nvda-10k-fy25]])` dated 2025-Q4. Period boundary crossed, grade equal -- Tier 1. Both lines appear; the old is annotated as superseded.

**AMD MI300 revenue update.** Existing: `AMD MI300 FY25 revenue USD 5.0B (B, per [[goldman-amd-2025-10-15]])` dated 2025-10-15. Candidate: `AMD MI300 FY25 revenue USD 5.5B (A, per [[amd-10k-fy25]])` dated 2026-02-04. More than 30 days newer, grade higher -- Tier 1. Both lines appear; old annotated.

**Contradictory analyst estimates.** Existing: `AMD MI300 FY26 revenue estimate USD 8B (B, per [[morgan-stanley-amd-2026-01-10]])` dated 2026-01-10. Candidate: `AMD MI300 FY26 revenue estimate USD 12B (B, per [[jp-morgan-amd-2026-01-12]])` dated 2026-01-12. Both B grade, both within 30 days -- Tier 2 flag. Both lines appear; note suffix added; audit report flags.

## 8. Per-fact provenance format

### 8.1 Inline attribution

Every claim line follows the inline-provenance format:

```
- <claim-text> (<grade>, per [[<source-stem>]])
```

The parenthetical is mandatory. A claim line without attribution is considered malformed and is rejected at post-edit gate. This direct inline binding implements the PROV-O minimum viable provenance: every asserted fact is accompanied by an `wasAttributedTo` relation to a specific identifiable agent (the source) [7]. Obsidian wikilinks in the `[[source-stem]]` form resolve by vault-wide filename match, so clicking any claim's source reference navigates directly to the source note [18].

### 8.2 Audit trail completeness

Because every claim carries its source and its source's grade, any reader can answer four questions from an entity note alone: what was claimed, by whom, under what grade, and (via the source note's own frontmatter) when. This four-field completeness is what distinguishes a compounding research KB from a simple notebook. Record-linkage literature establishes that without explicit per-record provenance, downstream merges become uninvertible and errors become unforensicable [9].

### 8.3 Supersede annotation format

Tier-1 supersede annotations, per Section 7.2, are formatted as nested bullets immediately below the superseded line:

```
- <old-claim> (<old-grade>, per [[<old-source>]])
  - [superseded by [[<new-source>]] on <ISO-date>]
- <new-claim> (<new-grade>, per [[<new-source>]])
```

The nesting is a two-space indent (CommonMark canonical indent for nested list items) [37]. The annotation line is its own line, not embedded in the old claim, because the old claim text itself is not rewritten. This is the structural enforcement of the append-only discipline: the sha256 diff assertion of Section 9.4 confirms that all changes are adjacent insertions.

### 8.4 Cross-source dedup

Two claims from different sources can dedup against each other if their signatures match. The dedup behavior in that case is to **retain the first-inserted line** and **append the second source** to the same line's provenance as a secondary attribution:

```
- NVDA FY25Q4 revenue USD 39.3B (A, per [[nvda-10k-fy25]]; cross-confirmed [[reuters-2026-02-26]])
```

The cross-confirmation tail increases the effective reliability of the fact without multiplying entity-note lines. This mirrors the multi-source provenance pattern used by YAGO and DBpedia for facts that appear in multiple authoritative references [30][31].

## 9. Body-preservation sha256 invariant

### 9.1 Protocol

The body-preservation invariant is the core structural guarantee of the entity-update layer: the body of an entity note is modified **only by insertions at known offsets**, never by rewrites. The invariant is enforced by a sha256 check-pair [20]:

```python
before = hashlib.sha256(body_bytes_before).hexdigest()
<perform edits>
after = hashlib.sha256(body_bytes_after).hexdigest()
assert before != after  # if non-empty plan
assert is_additive(body_bytes_before, body_bytes_after)
```

`body_bytes` is the byte content of the file after the closing `---` of frontmatter, starting at the next byte, through the last byte of the file. The exclusion of frontmatter is deliberate -- frontmatter legitimately mutates (the `updated:` field, the `related:` list) and including it would cause every successful update to violate a naive body-preservation rule (Section 9.5).

### 9.2 Python implementation and Windows subprocess bytes-compare

The implementation uses `hashlib.sha256` from the standard library, which is a CPython binding to OpenSSL's SHA-256 implementation conforming to FIPS 180-4 [21][38]. On Windows, when the verification is performed through a subprocess (the F16 pattern used by `/invest` Phase N), comparing hashes requires careful encoding discipline: `subprocess.run(..., capture_output=True)` returns `bytes`, and a naive comparison to a `str`-typed expected digest silently evaluates to `False` on every run. The F16 pattern mandates `bytes`-to-`bytes` comparison throughout:

```python
result = subprocess.run(
    ["python", "-c", "import hashlib, sys; "
     "sys.stdout.buffer.write(hashlib.sha256(open(sys.argv[1], 'rb').read()).digest())",
     str(body_path)],
    capture_output=True, check=True,
)
actual_digest_bytes = result.stdout  # raw 32 bytes
expected_digest_bytes = bytes.fromhex(expected_hex)
assert actual_digest_bytes == expected_digest_bytes
```

The `sys.stdout.buffer.write(...)` escape from Python's text-mode stdout is essential on Windows because text-mode stdout translates `\n` to `\r\n` and would corrupt raw digest bytes [39].

### 9.3 Nonequality assertion after non-empty plan

If the insertion plan held N > 0 lines but `before_sha256 == after_sha256`, a silent no-op has occurred -- the Edit call returned success but did not actually modify the file, perhaps due to a stale offset or a failed string-match. The pipeline halts immediately. This catches a class of bugs in which Edit-style tools silently degrade to no-ops on exact-match failure [23].

### 9.4 Additive-only diff assertion

Beyond the nonequality check, the post-edit body is verified to be a **superset-by-insertion** of the pre-edit body. Formally, the pre-edit bytes appear as an ordered subsequence of the post-edit bytes, and the post-edit bytes minus the pre-edit bytes (by sequence-diff) consist entirely of insertions, never deletions or replacements:

```python
def is_additive(before: bytes, after: bytes) -> bool:
    # Two-pointer subsequence check
    i = j = 0
    while i < len(before) and j < len(after):
        if before[i] == after[j]:
            i += 1
        j += 1
    return i == len(before)
```

The function returns True iff every byte of `before` appears in order within `after`. Tier-1 supersede annotations pass this test because they are adjacent insertions below the old line rather than in-place rewrites of the old line [2][3]. Failure of this check indicates a body-corruption bug; the pipeline halts and the working tree is left unstaged for manual inspection.

### 9.5 Frontmatter-bytes discipline

Frontmatter is governed by a **separate** invariant layer. The body-preservation gate deliberately excludes frontmatter because two fields legitimately mutate per update: `updated:` is bumped to today's ISO date, and `related:` gains new wikilink entries under the back-link cascade. A frontmatter-diff assertion verifies that **only these two fields change** and **all other keys remain byte-identical** to the pre-edit state. The assertion is executed via `ruamel.yaml` round-trip comparison: parse both versions, diff the resulting mapping, assert the diff's key set is a subset of `{"updated", "related"}` [15]. This two-layer formulation -- body strict-append-only, frontmatter structured-mutation -- is the right factoring because conflating them would force a choice between disallowing legitimate `updated:` bumps (too strict) or allowing silent body edits (too loose). Separation preserves both invariants at their appropriate granularity.

### 9.6 Failure handling

Any gate failure halts the pipeline immediately: no further files are processed, no commits are staged, the F11 auto-commit-disabled flag at `.claude/state/auto-commit-disabled` remains asserted, and the failure is written to `.claude/logs/<run-id>/gate-failure.log` with the full before/after hashes and the offending diff. Recovery is manual. This halt-and-report discipline mirrors the fail-closed posture used in financial-trading preflight gates and in CRDT-inconsistency detectors, which both prefer halt over silent corruption when invariants break [40].

## 10. Zero-new-claims short-circuit (idempotency)

### 10.1 Detection

After the decision loop of Section 4.3 completes, the skill inspects the insertion plan. If it contains zero `(section, offset, line)` entries -- every candidate was either deduped (signature match) or Tier-3 rejected -- the short-circuit condition is met [12]. The Tier-1 supersede path does **not** empty the plan (it contributes at least the new line plus the annotation); Tier-2 similarly contributes at least one line. Only pure dedup + Tier-3 combine to produce an empty plan.

### 10.2 Short-circuit behavior

The short-circuit disables three actions that would otherwise occur: the Edit call is skipped; the `updated:` field is not bumped; and the file is excluded from the Phase O `git add -- <pathspecs>` narrow-staging list. No byte of the file changes, no staging entry is created, no commit touches the file. The short-circuit is the correctness companion to the narrow-staging (F14) discipline: staging is narrow by default, and the short-circuit ensures that the staging list for a given entity is empty when no change occurred [41].

### 10.3 Phase P audit report

The run's Phase P audit report logs short-circuited entities with the message `entity <TICKER> unchanged (N claims all deduped; M Tier-3 rejected)`. This tells the analyst how much work the run did even when the working tree diff is empty -- a crucial signal because a high dedup rate on a fresh source indicates either genuine redundancy or upstream extraction drift, and the distinction matters for monitoring pipeline health.

### 10.4 Why this matters

True idempotency means `apply(apply(x, batch), batch) == apply(x, batch)`. The short-circuit makes this literally true at the byte level: re-running `/invest` or `/ingest` over the same source yields a byte-identical vault, confirmed by `git status` reporting zero changes. This property is what makes the pipeline safe to retry on network failures, safe to run in CI, and safe to compose with other pipelines. Idempotent write semantics are a design criterion in the CRDT literature and in content-addressable storage specifications, and are empirically rare in ad-hoc scripting contexts [40][24].

Preserving `updated:` as a meaningful signal is the second win. If `updated:` were bumped on every re-run regardless of content change, it would record pipeline re-execution rather than content freshness. Downstream consumers that use `updated:` for sort-by-freshness (the vault's Dataview queries, the MOC regeneration script, the research-staleness dashboard) would become meaningless. The short-circuit preserves the field's semantic contract.

### 10.5 Edge case -- novel metric signatures

One edge case sits on the boundary. If an incoming claim batch reformulates an existing fact under a novel metric decomposition -- for example, an existing `NVDA data-center revenue USD 47.5B FY25Q4` is accompanied by a decomposition batch that adds `NVDA HGX revenue USD 30B FY25Q4` and `NVDA networking revenue USD 17.5B FY25Q4` -- the novel metric signatures (`hgx-revenue-quarterly`, `networking-revenue-quarterly`) are not in the existing-signature set. The short-circuit does not fire; both decomposition lines are inserted; the aggregate line is not flagged as contradicted because the `(entity, metric)` prefixes differ. This is the intended behavior: finer decompositions are net-new information, and preserving both the aggregate and the decomposition captures maximum signal.

## 11. Symmetric back-link protocol

### 11.1 Analysis or source side

Upstream of Phase L, analysis notes (produced by `/invest`) and source notes (produced by `/ingest` for external documents) compose their frontmatter with a `related:` field already containing `[[<TICKER>]]` and/or `[[<Company>]]` entries for each entity they discuss. This upstream composition is the responsibility of the respective skill's earlier phases and is out of scope for this reference, but it is the precondition that makes symmetric back-linking work [18].

### 11.2 Entity side

The entity-side half of the back-link gains a reciprocal `[[<source-stem>]]` or `[[<ticker>-analysis-<date>]]` in its own `related:` field. The insertion is idempotent: if the entry already exists, no change is made; if absent, it is inserted. The idempotency is enforced by a set-membership check before the YAML mutation.

### 11.3 Alphabetical-within-group insertion

The `related:` field is organized into four ordered groups, separated by YAML comments where the format permits:

```yaml
related:
  # MOCs
  - "[[investing-moc]]"
  - "[[semiconductors-moc]]"
  # theses
  - "[[thesis-orbital-compute]]"
  - "[[thesis-memory-cycle-recovery]]"
  # refs
  - "[[ref-metric-ontology]]"
  # analyses and sources
  - "[[nvda-analysis-2026-04-22]]"
  - "[[nvda-10k-fy25]]"
```

Within each group, entries are sorted alphabetically by stem. Insertion of a new entry places it at its sorted position within the correct group; group membership is inferred by stem prefix (`*-moc` -> MOC group; `thesis-*` -> thesis group; `ref-*` -> refs group; else analyses-and-sources group) [17].

### 11.4 Per-file sha256 gate on related-field edit -- two-layer invariant

A back-link cascade frequently touches two files per cascade (entity + source), and occasionally more (entity + multiple sources, or entity + MOC). Each file edit is individually gated by a two-layer invariant:

**Layer A -- body-sha256 gate.** The body bytes of the file (content after the closing `---` of frontmatter) must be byte-identical before and after the related-field edit. This is a strict equality, unlike the Section 9 body gate which asserts non-equality for content-edit passes. A related-field-only edit touches only the YAML frontmatter; if the body-sha256 differs pre-to-post, an unintended body mutation has occurred and the pipeline halts.

```python
body_before = hashlib.sha256(body_bytes_before).hexdigest()
<related-field edit>
body_after = hashlib.sha256(body_bytes_after).hexdigest()
assert body_before == body_after, "body must be byte-identical during related-only edit"
```

**Layer B -- frontmatter-diff assertion.** The frontmatter, parsed as a mapping, must differ only in that `related:` has gained one or more entries (with in-group alphabetical order preserved) and `updated:` has advanced to today's ISO date. Every other key is byte-identical to its pre-edit serialization. This assertion is performed post-edit by re-parsing both versions and diffing:

```python
fm_before = ruamel.yaml.YAML(typ="rt").load(fm_bytes_before)
fm_after  = ruamel.yaml.YAML(typ="rt").load(fm_bytes_after)
changed_keys = {k for k in set(fm_before) | set(fm_after)
                if fm_before.get(k) != fm_after.get(k)}
assert changed_keys <= {"updated", "related"}
# further assert related gained entries, didn't lose any:
assert set(fm_before.get("related", [])) <= set(fm_after["related"])
```

The justification for the two-layer formulation is structural. The body is a strict append-only log with one special case (Tier-1 supersede as adjacent insertion), and its invariant is a strict-subset-plus-insertions relation best expressed over raw bytes. The frontmatter is a structured metadata record whose keys have semantic meaning and whose values legitimately mutate under well-specified operations (`updated:` bump, `related:` extension). Conflating them into a single "nothing changes" invariant would force false positives (the legitimate `updated:` bump would fail); conflating them into a single "anything can change" invariant would force false negatives (a bug silently overwriting a frontmatter field would pass). Separating them and applying the correct discipline to each layer preserves both strictness and legitimacy [26][40]. This factoring mirrors the HTTP resource-vs-representation distinction, where entity-body and header-metadata have different cache-validation semantics for the same structural reason [42].

### 11.5 BACKLINKABLE_CATEGORIES filter

Not every related entry is inserted. The `BACKLINKABLE_CATEGORIES` index filters out back-link cascades to `[daily]` and `[meta]` category notes. Daily notes are ephemeral captures that would pollute entity graph-view traversals; meta notes are the vault's self-reference documentation (the tag vocabulary itself, the skill indexes) and should not appear as related in every entity they happen to mention [17][18]. The filter is applied at the cascade-planning step, before any file is opened; a source note tagged `[daily]` contributes nothing to the entity-side back-link even if it contains entity mentions.

## 12. Coordination with /ingest and /invest

### 12.1 Shared infrastructure enumeration

Both skills rely on a shared set of vault indexes loaded at Phase A (and refreshed between phases when stale): `TICKERS` (list of ticker stems), `COMPANIES` (list of company stems), `MOC_STEMS` (list of MOC-note stems for back-link routing), `THESIS_STEMS` (list of registered thesis slugs), `ALL_BASENAMES` (global basename index for wikilink-resolution checks), and `BACKLINKABLE_CATEGORIES` (the filter of Section 11.5). The indexes are constructed by a shared build step that scans the vault filesystem and emits JSON files under `.claude/state/indexes/`; both skills read the same JSON, guaranteeing that a decision made in one skill's Phase L matches the decision the other skill would have made in its Phase F [43].

Operational patterns are shared across skills: the F11 auto-commit-disabled flag at `.claude/state/auto-commit-disabled` (asserted on pipeline entry, cleared only on successful completion, ensuring that a mid-run crash does not leave a half-reconciled vault committed automatically); the F14 narrow-staging discipline (`git add -- <explicit pathspec list>` rather than `git add -A`, so that only files the skill intends to modify enter the index); the F16 subprocess bytes-compare pattern documented in Section 9.2; and the F17 Co-Authored-By suppression verification, which ensures that Claude Code's default `Co-Authored-By` commit trailer does not leak into a personal vault's git history when suppression is requested [44].

### 12.2 Complementary roles

`/invest` and `/ingest` play complementary roles in the fact-flow. `/invest` originates facts via its 5-phase research process (Phase A-E context gathering, Phase F-I research and synthesis, Phase J drafting, Phase K claim emission, Phase L entity distribution, Phase M-P verification and commit); it is the entry point when the analyst asks "produce an institutional-grade analysis of NVDA". `/ingest` distributes facts from external sources (arrived as PDFs, URLs, or pasted text) or from vault-internal sources into the entity graph; it is the entry point when the analyst asks "here is a 10-K, add its facts to the relevant entity notes". Despite the different upstream paths, both converge on the identical entity-update semantics of this specification at Phase L / Phase F [4].

### 12.3 INGEST:claims coordination hint (Pattern 18)

A bridge pattern links the two skills. `/invest` Phase K emits, as a side-effect of analysis-note composition, a fenced block in the analysis note labeled `INGEST:claims` containing the full set of marker signatures and normalized claims that the analysis asserts. Downstream, the analyst or an automation can run `/ingest <analysis-path>` to re-distribute those claims through `/ingest` Phase F, which consumes the `INGEST:claims` block via marker-signature extraction. Because both skills use identical signatures and identical routing, the re-distribution is deterministic and idempotent: every claim already placed by `/invest` Phase L dedups during `/ingest` Phase F, producing a zero-diff re-run. This is the mechanism by which `/invest`'s in-skill distribution and `/ingest`'s general-purpose distribution stay byte-compatible [12].

### 12.4 Drop-in-compatibility guarantee

The drop-in-compatibility guarantee is the normative claim that ties this specification together: a reader opening `wiki/entities/tickers/NVDA.md` cannot tell, from the text alone, which skill inserted any given claim. The guarantee holds because both skills share the same routing rules (Section 5), the same signature derivation (Section 6), the same tiering (Section 7), the same provenance format (Section 8), the same body-preservation invariant (Section 9), the same short-circuit (Section 10), and the same back-link protocol (Section 11). A third-party re-implementation of either skill that adhered to this specification could be swapped into either slot without any observable change to the entity graph. The guarantee is verifiable mechanically: running `/invest` and `/ingest` over the same (analysis, source) pair produces the same entity-note diff modulo the `INGEST:claims` hint block itself [45].

## 13. Sources and references

[1] Halevy, A., Rajaraman, A., Ordille, J. "Data Integration: The Teenage Years." VLDB 2006. https://www.vldb.org/conf/2006/p9-halevy.pdf

[2] O'Neil, P., Cheng, E., Gawlick, D., O'Neil, E. "The log-structured merge-tree (LSM-tree)." Acta Informatica 33(4): 351-385, June 1996. DOI: 10.1007/s002360050048

[3] Fowler, M. "Event Sourcing." martinfowler.com, 12 December 2005. https://martinfowler.com/eaaDev/EventSourcing.html

[4] Doan, A., Halevy, A., Ives, Z. Principles of Data Integration. Morgan Kaufmann, 2012. ISBN 978-0-12-416044-6. DOI: 10.1016/C2011-0-06130-6

[5] Wikipedia contributors. "Wikipedia:Edit warring (including the three-revert rule, WP:3RR)." https://en.wikipedia.org/wiki/Wikipedia:Edit_warring

[6] Vrandecic, D., Krotzsch, M. "Wikidata: A Free Collaborative Knowledgebase." Communications of the ACM 57(10): 78-85, October 2014. DOI: 10.1145/2629489

[7] Lebo, T., Sahoo, S., McGuinness, D. (eds.) "PROV-O: The PROV Ontology." W3C Recommendation 30 April 2013. https://www.w3.org/TR/prov-o/

[8] Fellegi, I.P., Sunter, A.B. "A Theory for Record Linkage." Journal of the American Statistical Association 64(328): 1183-1210, December 1969. DOI: 10.1080/01621459.1969.10501049

[9] Christen, P. Data Matching: Concepts and Techniques for Record Linkage, Entity Resolution, and Duplicate Detection. Springer, 2012. ISBN 978-3-642-31163-5. DOI: 10.1007/978-3-642-31164-2

[10] Python Software Foundation. "pathlib -- Object-oriented filesystem paths." Python Standard Library documentation. https://docs.python.org/3/library/pathlib.html

[11] Microsoft. "Naming Files, Paths, and Namespaces -- case sensitivity on Windows filesystems." Win32 File System documentation. https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file

[12] Helland, P. "Idempotence Is Not a Medical Condition." ACM Queue 10(4): 30-46, 2012. https://queue.acm.org/detail.cfm?id=2187821

[13] Davis, M., Whistler, K. (eds.) "Unicode Standard Annex #15: Unicode Normalization Forms (UAX #15)." Unicode Consortium. https://www.unicode.org/reports/tr15/

[14] Ben-Kiki, O., Evans, C., Ingy dot Net. "YAML Ain't Markup Language (YAML) revision 1.2.2." YAML Language Development Team, 1 October 2021. https://yaml.org/spec/1.2.2/

[15] van der Neut, A. "ruamel.yaml documentation." https://yaml.readthedocs.io/

[16] W3C. "SKOS Simple Knowledge Organization System Reference." W3C Recommendation 18 August 2009. https://www.w3.org/TR/skos-reference/

[17] Wikipedia contributors. "Wikipedia:Categorization -- guidance on category membership, navigation, and inclusion." https://en.wikipedia.org/wiki/Wikipedia:Categorization

[18] Obsidian. "Internal links." Obsidian Help. https://help.obsidian.md/links

[19] OWASP. "Path Traversal." OWASP Web Security Testing Guide. https://owasp.org/www-community/attacks/Path_Traversal

[20] National Institute of Standards and Technology. "FIPS 180-4: Secure Hash Standard (SHS)." NIST, August 2015. DOI: 10.6028/NIST.FIPS.180-4. https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf

[21] Python Software Foundation. "hashlib -- Secure hashes and message digests." Python Standard Library documentation. https://docs.python.org/3/library/hashlib.html

[22] Postel, J. "RFC 761 (Transmission Control Protocol)" and "RFC 793," Section 2.10 Robustness Principle. IETF 1980/1981. https://www.rfc-editor.org/rfc/rfc793

[23] Weikum, G., Vossen, G. Transactional Information Systems. Morgan Kaufmann, 2002. ISBN 978-1-55860-508-4.

[24] Benet, J. "IPFS -- Content Addressed, Versioned, P2P File System." arXiv:1407.3561, July 2014. https://arxiv.org/abs/1407.3561

[25] Gray, J., Reuter, A. Transaction Processing: Concepts and Techniques. Morgan Kaufmann, 1993. ISBN 978-1-55860-190-1.

[26] Lampson, B. "Hints for Computer System Design." ACM Operating Systems Review 17(5): 33-48, 1983.

[27] Auer, S., Bizer, C., Kobilarov, G., Lehmann, J., Cyganiak, R., Ives, Z. "DBpedia: A Nucleus for a Web of Open Data." ISWC 2007, LNCS 4825, pp. 722-735. Springer. DOI: 10.1007/978-3-540-76298-0_52

[28] Graham, B., Dodd, D. Security Analysis. 6th ed., McGraw-Hill, 2008. (For thesis-conditional interpretation of financial claims.) ISBN 978-0-07-159253-6.

[29] Broder, A. "On the resemblance and containment of documents." Compression and Complexity of Sequences 1997. DOI: 10.1109/SEQUEN.1997.666900

[30] Suchanek, F.M., Kasneci, G., Weikum, G. "YAGO: A Core of Semantic Knowledge (Unifying WordNet and Wikipedia)." WWW 2007, pp. 697-706. DOI: 10.1145/1242572.1242667

[31] Bizer, C., Heath, T., Berners-Lee, T. "Linked Data -- The Story So Far." International Journal on Semantic Web and Information Systems 5(3), 2009. DOI: 10.4018/jswis.2009081901

[32] International Organization for Standardization. "ISO 8601-1:2019 Date and time -- Representations for information interchange." https://www.iso.org/standard/70907.html

[33] Wikidata. "Help:Property constraints portal / list of constraints." https://www.wikidata.org/wiki/Help:Property_constraints_portal

[34] Lewis, P., et al. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." NeurIPS 2020. arXiv:2005.11401. https://arxiv.org/abs/2005.11401

[35] Gao, Y., et al. "Retrieval-Augmented Generation for Large Language Models: A Survey." arXiv:2312.10997, December 2023. https://arxiv.org/abs/2312.10997

[36] Financial Accounting Standards Board. "Accounting Standards Codification Topic 270 -- Interim Reporting." FASB. https://asc.fasb.org/270

[37] MacFarlane, J. "CommonMark Spec, Version 0.31.2." 28 January 2024. https://spec.commonmark.org/0.31.2/

[38] OpenSSL Project. "OpenSSL Cryptographic Library: SHA implementation documentation." https://www.openssl.org/docs/

[39] Python Software Foundation. "subprocess -- Subprocess management." Python Standard Library documentation. https://docs.python.org/3/library/subprocess.html

[40] Shapiro, M., Preguica, N., Baquero, C., Zawirski, M. "Conflict-free Replicated Data Types." INRIA Research Report RR-7687, July 2011. https://hal.inria.fr/inria-00609399

[41] Chacon, S., Straub, B. Pro Git. 2nd ed., Apress, 2014. ISBN 978-1-4842-0077-3. Chapter 10 "Git Internals," Section 10.2 "Git Objects." https://git-scm.com/book/en/v2

[42] Fielding, R., et al. "RFC 7232: Hypertext Transfer Protocol (HTTP/1.1): Conditional Requests." IETF, June 2014. https://www.rfc-editor.org/rfc/rfc7232

[43] Garcia-Molina, H., Ullman, J., Widom, J. Database Systems: The Complete Book. 2nd ed., Pearson, 2008. ISBN 978-0-13-187325-4.

[44] Git project. "git-diff(1) reference." https://git-scm.com/docs/git-diff

[45] Hayes, P.J., Patel-Schneider, P.F. (eds.) "RDF 1.1 Semantics." W3C Recommendation 25 February 2014. https://www.w3.org/TR/rdf11-mt/

[46] Kellogg, G., Champin, P.-A., Longley, D. (eds.) "JSON-LD 1.1." W3C Recommendation 16 July 2020. https://www.w3.org/TR/json-ld11/

[47] Berners-Lee, T., Fielding, R.T., Masinter, L. "RFC 3986: Uniform Resource Identifier (URI): Generic Syntax." IETF STD 66, January 2005. DOI: 10.17487/RFC3986

[48] Schema.org Community Group. "Schema.org vocabulary, version 30.0." https://schema.org/

[49] Git project. "git hash-function-transition (SHA-256 object format)." https://git-scm.com/docs/hash-function-transition

[50] Preston-Werner, T. "Semantic Versioning 2.0.0." https://semver.org/spec/v2.0.0.html (cited for `updated:` field semantics analogy to version monotonicity)

[51] Merkle, R.C. "A Digital Signature Based on a Conventional Encryption Function." CRYPTO '87, LNCS 293. Springer, 1988. DOI: 10.1007/3-540-48184-2_32

[52] Lamport, L. "Time, Clocks, and the Ordering of Events in a Distributed System." Communications of the ACM 21(7): 558-565, 1978. DOI: 10.1145/359545.359563 (cited for temporal-hierarchy ordering discipline)

[53] Moreau, L., Missier, P. (eds.) "PROV-DM: The PROV Data Model." W3C Recommendation 30 April 2013. https://www.w3.org/TR/prov-dm/

[54] Cyganiak, R., Wood, D., Lanthaler, M. (eds.) "RDF 1.1 Concepts and Abstract Syntax." W3C Recommendation 25 February 2014. https://www.w3.org/TR/rdf11-concepts/

[55] Dean, J., Ghemawat, S. "MapReduce: Simplified Data Processing on Large Clusters." OSDI 2004. (cited for batch-processing idempotency principles)

[56] Helland, P. "Immutability Changes Everything." Communications of the ACM 59(1): 64-70, 2016. DOI: 10.1145/2844112

[57] Silberschatz, A., Korth, H.F., Sudarshan, S. Database System Concepts. 7th ed., McGraw-Hill, 2019. ISBN 978-0-07-802215-9.

[58] Codd, E.F. "A Relational Model of Data for Large Shared Data Banks." Communications of the ACM 13(6): 377-387, 1970. DOI: 10.1145/362384.362685