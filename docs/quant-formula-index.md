# Quantitative formula index

Every formula the scoring path uses, and how strongly it has been checked. A formula here is "checked" only
when it was run against an independently computed expected value -- not when it was read and looked right.

## Coverage

| | Count |
|---|---|
| Formulas inventoried across the system | 193 |
| On the `/invest` scoring path | 65 (27 implemented in code, 38 applied by the model from a published definition) |
| Prompt-only across the whole system (no code implementation) | 112 |
| With no consumer at all (defined, nothing calls them) | 3 -- Ohlson O-Score, Graham Number, model-stacking gates |

## Check results

| Scope | Checked | Pass | Mismatch | Not checkable |
|---|---|---|---|---|
| `/invest` path, code | 26, with synthetic inputs | 25 | 1 | 0 |
| `/invest` path, prompt-only | 38 | 34 | 4 | 0 |
| Remainder, first pass (a seeded 20% sample of the other 128) | 26 | 19 | 7 | 0 |
| Second pass (every formula the first pass had not reached, including the 27th `/invest` code formula, checked by a tamper test) | 103 | 88 | 9 | 6 |
| **Not checked** | **0** | -- | -- | -- |

**Every formula in the inventory now has a verdict.** The second pass closed the 103 that had never been
checked: 88 matched their definitions, 9 did not, and 6 could not be checked at all -- each of those six
carries its reason (no definition exists to check against, the inputs are withheld, or the result is not
deterministic). A formula counts as checked only where the expected value was derived from the definition
independently; the implementation's own output was never used as the expected value.

**21 formulas mismatch in total**, and they produce 22 findings, because one formula is wrong in two
independent ways. The tables below carry 13 from the first pass and 9 from the second.

An earlier version of this page reported 0 mismatches on the prompt-only row and listed 12 findings. That
was wrong in a specific and instructive way: the row's own evidence file records 4, and the one finding the
page dropped -- the Composite Quality Score, below -- is the only specification gap sitting directly on the
`/invest` scoring path. A summary row disagreed with the evidence underneath it, and the disagreement
survived because nobody added the row up. It is corrected here rather than quietly.

The textbook formulas on the `/invest` path -- Piotroski F, Altman Z, Beneish M, Sloan accruals, ROIC, free
cash flow, WACC and CAPM, Gordon terminal value, reverse DCF, dilution, runway -- were each run against their
canonical published definition on a worked example, and each matched, coefficient for coefficient.

## The second pass, and what it found

Nine formulas compute something other than what their own definition says. None is on the `/invest` scoring
path. They are listed worst first, by how much a wrong answer would move a decision.

| Finding | Where | What the code or the specification does |
|---|---|---|
| Win probability defined twice | `.agents/skills/portfolio/ref-allocation-methodology.md:72` | One sentence gives two incompatible bounds for the same quantity, and the worked example below it uses the second. The two readings differ enough to turn a position from nothing into a real one. |
| Price-weighted return in an equal-weighted portfolio | `tools/backtest-hardline.py:130` | The portfolio is built equal-weighted and the period return is computed price-weighted. A three-name case whose equal-weighted return is +30.00% reports -8.81%. The transaction cost also cancels out of its own ratio, so 25 basis points and zero give identical results. |
| Ranking window ends on the fill bar | `tools/backtest-strategy.py:94` | Three separate docstrings and an anti-look-ahead contract say the ranking window ends one bar before the fill. The code ranks on the fill bar itself. |
| Window labels that do not match the window | `tools/macro-reference.py:33` | A column labelled "90d avg" averages 180 observations, and "percentile-in-window" is computed over all stored history. One reading published as the 42nd percentile ranks 83rd within its stated window. |
| A threshold used twice | `tools/dissent-tracking.py:78` | A drawdown threshold is also applied, undocumented, as a floor on probability, so cases that should count as realized report zero. |
| A "moving-average cross" against a frozen level | `.agents/skills/market/ref-screening-logic.md:177` | Both sides of the comparison use the same moving-average index, so it tests two closes against one fixed level rather than each close against its own average. |
| Horizon off by one bar in a null | `tools/verdict-backtest.py:822` | The null uses one fewer session than the excursion it is compared against, inflating the ratio by about 9.5% at one week. |
| A ratio with no stated period | `Atlas/sources/investing/ref-valuation-methodology.md:241` | Payback and lifetime-value formulas never pin whether the revenue input is monthly or annual. With an annual input the payback figure is labelled months and is twelve times wrong. |
| A bound that assumes an uncapped input | `.agents/skills/invest/SKILL.md:552` | A "worst case" is computed with a probability of 0.5 that no rule caps. The formula permits 1.0, so the real worst case is double the stated bound. |

## The findings, tagged

Each finding is either a **specification gap** (the published definition itself is incomplete or ambiguous, so
no implementation can be correct) or a **computational defect** (the code computes something other than what
its own definition says).

### Computational defects (5)

| Finding | Where | What the code does |
|---|---|---|
| 12-1 momentum window | `tools/technicals.py:186` | Uses a 230-session window (t-21 vs t-251) where the standard is t-21 vs t-252. On a linear test series: 25.56 against 28.88. |
| Correlation alignment | `tools/sector-alpha.py:48-66` | Aligns two series by position (last N bars each) rather than by date. Two identical series, one missing a single day, correlate at 0.683 instead of 1.0. Any calendar difference -- a crypto asset against an equity, a holiday -- silently corrupts the result. |
| Factor-bucket keywords | `tools/backtest-prediction.py:131-137` | Counts factor keywords with substring regexes and no word boundaries, so "EPS" matches "steps", "hype" matches "hyperscaler", "rates" matches "operates". |
| Upper-middle median | `tools/score_ledger.py:494` | Takes the upper-middle element as the median, and an integer bin boundary leaves a gap. |
| Calibration lookup | `tools/calibrate-confidence.py:47-57` | The lookup does not resolve to the bin the specification names. |

### Specification gaps (8)

| Finding | Where | What is missing |
|---|---|---|
| Composite Quality Score normalization | `.agents/skills/invest/SKILL.md:442` | The score gives component weights summing to 100 but never says how Piotroski F, Altman Z and Beneish M become 0-100. The same company scores 81.3 under a linear mapping and 70.0 under a band mapping -- STRONG BUY against BUY. This is the only gap on the `/invest` scoring path, and the model supplies the missing conversion silently, so two runs can disagree. |
| Rating tiers | `.agents/skills/invest/SKILL.md:480-484` | A mechanical enumeration of the input space leaves data states with no assigned rating. |
| Net debt / EBITDA bands | `ref-scoring-models.md:657` | Bands are <2, 2-3, >=4, >=6: the 3-4x range is unclassified. |
| Bridge revenue-growth bands | `ref-scoring-models.md:771` | Integer bands 10-19 / 20-39 / 40-59 leave 19-20% and the equivalent boundaries unassigned. |
| ROIC-minus-WACC bands | `ref-scoring-models.md` | Adjacent bands do not meet, so a spread can fall between them. |
| Net buyback yield units | `ref-scoring-models.md` | The unit is ambiguous, so two faithful readings give different numbers. |
| Volatility-parity sizing | `ref-allocation-methodology.md:108` | P = V x sigma_target / sigma_i has no 1/N term, so P lands at roughly 50-200% of the book and the soft cap below it can never bind. The rule is inert as written. |
| Haircut stacking | `/portfolio` against `/invest` | The two skills stack their haircuts in different orders, so the same inputs can size differently depending on which one asks. |

## How to read this

A specification gap is a documentation fault and shows up as an unassigned or ambiguous case. A computational
defect will produce a plausible-looking number that is wrong, which is the more dangerous kind: nothing in the
output signals it. Each affected formula carries a one-line note beside it in the published source.

These verdicts record what the check found at the time. The audit recorded defects rather than fixing them, but
the working system has fixed some since, and the code published here carries those fixes: all five computational
defects in the first table are fixed (the line numbers above are from the check and may have moved). The second-pass
findings and the specification gaps have not been re-checked; read the code for their current state.
