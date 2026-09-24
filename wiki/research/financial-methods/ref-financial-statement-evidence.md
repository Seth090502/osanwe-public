---
aliases: [point in time financial statement method]
categories: [wiki]
type: reference
tags: [topic/investing]
status: active
created: 2026-09-13
updated: 2026-09-13
related: ["[[financial-analysis-contract]]", "[[ref-valuation-applicability]]", "[[ref-empirical-research-validation]]"]
---

# Financial statements and information available at the decision time

Public/synthetic method, version 1. This note does not contain company facts or
account data. Its reviewed source scope is SEC API calendar semantics, SEC
non-GAAP presentation guidance and ALFRED vintage semantics. A filing or metric
retrieved through a connector still needs its own inspected evidence.

## E1. Match the economic quantity before calculating

Retain issuer, accession, original table/row label, unit, scale, currency,
accounting basis, consolidation/segment scope, duration versus instant, period
start/end, publication/availability time and retrieval time. Keep the inspected
passage and the normalized mapping together. A label match alone is insufficient.
SEC frame endpoints align observations to calendar periods; fiscal calendars
can differ. Inspect the issuer period instead of assuming every frame is a
comparable quarter. [SEC API documentation, Frames](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)

Do not combine standalone quarters with year-to-date durations. For comparable
duration facts, TTM = latest FY + current YTD - prior comparable YTD. Confirm
fiscal length and restatement basis. For instantaneous balances, that identity
is inapplicable. Keep non-GAAP labels visible, reconcile adjustments individually,
and do not infer comparability from similar names. [SEC non-GAAP guidance,
questions 100.01 and 102.10](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/non-gaap-financial-measures)

## E2. Synthetic duration and revision examples

All amounts in this example are synthetic USD millions. Annual revenue 42,
current nine-month revenue 33 and prior comparable nine-month revenue 27 yield
TTM revenue 48. If annual revenue is later restated to 40 with other inputs
unchanged, current TTM is 46. A replay before that restatement remains 48.
If annual revenue 42 includes nine-month revenue 30, its fourth quarter is 12;
adding 42 and 30 would double-count overlapping activity. Neither operation
applies to cash balances at two different dates.

A second source repeating the same issuer filing is one origin, not independent
corroboration. Conflicting origins require reconciliation; duplicates require
deduplication. A later source revision must invalidate affected current outputs
without silently changing the evidence available to the historical decision.
ALFRED preserves prior data vintages, but its release-date fallbacks and ingestion
lag mean a vintage date alone does not prove an exact intraday trading timestamp.
[ALFRED Help, release dates and verification](https://alfred.stlouisfed.org/help)

## E3. Workflow and limits

Use `tools/fis/evidence.py` and Workbench evidence/review owners; they validate
declared semantics and bindings, not whether a cited source was actually read.
For a historical trade simulation, use the owning point-in-time and fill-time
rules. A later-known fact cannot be made eligible by changing its observation
date. Missing FX, a missing original, an unresolved mapping or unequal fiscal
periods blocks the affected comparison, not unrelated supported answers.

Numerical examples: `tools/fis/test_corpus_examples.py`, E2. Sources inspected
2026-09-13; exact narrow excerpts/locators are recorded in the adjacent source
inspection receipt. Current-source access, full-company reconciliation and
live broker evidence are separate gates.

prov: script:synthetic E2 arithmetic, USD millions, declared FY/YTD durations;
source semantics: web:SEC and ALFRED originals inspected 2026-09-13.
