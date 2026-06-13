# Health Evidence Framework

Reference content for `/health` evidence-tier grading and confidence gating. SKILL.md imperatively Reads this file before any claim is emitted. Extracted 2026-04-18 (Group 23b) from SKILL.md Quality Rules -- `@import` does not resolve in Claude Code SKILL.md body, so explicit Read directive is used instead.

---

## GRADE-mapped evidence inline with every claim

Format: `[T1 | Cochrane SR | 2024 | n=3,412 | GRADE: High]`

- **T1:** Systematic reviews, meta-analyses (Cochrane, AHRQ) -- GRADE: High
- **T2:** RCTs n>100 -- GRADE: Moderate
- **T3:** Smaller RCTs, well-designed cohort -- GRADE: Low
- **T4:** Observational, case series -- GRADE: Very Low
- **T5:** Animal, in vitro, mechanism-based -- below GRADE, label **SPECULATIVE**
- **T6:** Expert opinion, traditional use -- below GRADE, label **SPECULATIVE**

**No claim without an evidence citation. No exceptions.**

## Confidence gating (Viome model)

- >=60% confidence -> included in **Immediate Actions**
- 40-59% -> labeled **EVALUATE** (monitor, do not act yet)
- <40% -> labeled **SPECULATIVE** (excluded from all action items)

This prevents the #1 failure mode of health AI: confident-sounding advice backed by rat studies.
