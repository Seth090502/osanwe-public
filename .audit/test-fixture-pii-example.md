---
categories: [meta]
type: test-fixture
tags: []
status: active
created: 2026-06-11
updated: 2026-06-11
aliases: []
related: []
---

# Test fixture: known-PII strings (positive control) -- EXAMPLE

Seeds one OBVIOUSLY-FAKE string per denylist category so
`python .audit/check-pii.py .audit/test-fixture-pii-example.md <your-denylist>`
reports hits in every category you have configured. After authoring your real
(gitignored) denylist, extend this fixture with one fake-but-matching string
per category. Never put REAL values here -- a fixture with real values is
itself a leak (this replaces a v1 fixture that made exactly that mistake).

## PERSONAL_PORTFOLIO_VALUE_ANCHORED

Portfolio total: $99,999 currently. Position size = $9,999. Account balance = $9,999.

## PERSONAL_PORTFOLIO_HOLDINGS

Holding 12.3456 shares combined. Portfolio impact +$999.

## BIOMETRIC_NUMERIC

Latest labs: testosterone = 999 ng/dL. HbA1c 9.9. Weight 999 lb. BMI 99.9.

## MEDICAL_HISTORY

Bloodwork 2099-01-01 fictional entry.

## DOB_AGE_PRECISION

Born 2099. DOB = 2099-01-01.

## FILES_FORBIDDEN

@CLAUDE.local import line example.
