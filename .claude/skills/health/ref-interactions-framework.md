# Health Interactions & Absorption Framework

Reference content for `/health` interaction severity grading, cumulative dose tracking, hepatotoxicity assessment, and GLP-1 absorption context. SKILL.md imperatively Reads this file before any interaction claim is emitted. Extracted 2026-04-18 (Group 23b) from SKILL.md Quality Rules -- `@import` does not resolve in Claude Code SKILL.md body, so explicit Read directive is used instead.

---

## NatMed interaction severity grading

Every interaction classified: **Major** (contraindicated/dangerous) / **Moderate** (monitor closely) / **Minor** (acceptable, note for awareness). With mechanism + evidence tier.

## Cumulative fat-soluble vitamin tracking

Running dose total for Vitamins D, A, E, K. Auto-flag when combined intake exceeds 2x UL. Vitamin D at [HIGH_DOSE_IU]/day (3.75x UL) **always flagged until 25(OH)D labs confirm <100 ng/mL.**

## Hepatotoxicity stacking

Assessed when 2+ CYP450-metabolized compounds are taken in the same timing window. Example stack compounds NAC + curcumin are both hepatically processed. GLP-1 agonists add additional hepatic load consideration.

## GLP-1 absorption caveat

Every oral supplement timing recommendation must note the GLP-1 class 20-40% gastric emptying delay. This changes bioavailability for all orally-administered compounds.
