# Health /labs mode

Phase-by-phase execution contract for `/health labs`. SKILL.md imperatively Reads this before executing labs mode. Extracted 2026-04-18 (Group 23b).

---

Ingest bloodwork and correlate to stack.

## Phase 1: Data Ingestion
Accept lab values in any format:
- Key=value: `/health labs vitD=62 ALT=24 AST=28`
- Narrative: "Vitamin D came back at 62, liver enzymes ALT 24 AST 28"
- Bulk paste from lab report

## Phase 2: Three-Tier Range Assessment (1-2 searches)
For each marker, compare against:
1. **Standard range** (lab default)
2. **Optimal functional range** (concierge medicine)
3. **the user's optimized zone** (personalized to goals/interventions)

| Marker | Value | Standard | Optimal | the user's Zone | Status |
Status: **OPTIMAL** / **ADEQUATE** / **SUBOPTIMAL** / **FLAGGED** / **CRITICAL**

## Phase 3: Supplement-Biomarker Correlation
For each value, cross-reference the supplement(s) that should affect it:
- Is 25(OH)D in range given [HIGH_DOSE_IU]? If <60, absorption issue. If >100, TOXICITY.
- Are liver enzymes safe despite NAC + curcumin + GLP-1 agonist?
- Do triglycerides reflect omega-3 effectiveness?
- Does testosterone correlate with zinc supplementation?

## Phase 4: Action Items
- **CRITICAL:** values requiring immediate action
- **ADJUST:** supplements needing dose change based on labs
- **RETEST:** markers needing follow-up (with timeline -- 90 days)
- **CONFIRM:** supplements validated by lab results

## Phase 5: Output + Data Update
Write analysis to `<VAULT_ROOT>/Efforts/health-protocol/analyses/labs-analysis-YYYY-MM-DD.md` with canonical frontmatter (`categories: [efforts]`, `type: analysis`, standard fields).
**UPDATE** `<VAULT_ROOT>/Efforts/health-protocol/bloodwork.md` with new values, date, and flags. This is the source of truth for lab history.
