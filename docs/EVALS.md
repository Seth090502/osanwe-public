# What is evaluated, and how

Four things are evaluated here, and they are not equally strong. They are listed strongest first, with what
each can and cannot support. Where the numbers are unflattering or too small to carry a claim, they say so.

## 1. Adversarial tests against the system's own controls

This is the strongest evidence in the repository, and not because it succeeded. It is the only evaluation
that found something serious, kept finding it, and changed what was built as a result.

The order gate's first stair asks the session transcript whether a person authorised this specific order.
It answered that by rejecting three known-bad transcript shapes and accepting everything else. A denylist
of shapes has a failure built in: every new kind of entry the harness invents is accepted by omission,
silently, from the day it ships.

It was attacked in three independent rounds, each driving the real hook as a subprocess:

| Round | Target | Result |
|---|---|---|
| 1 | the shipped gate | **8 transcript shapes authorised an order**, among them the model's own compaction summary |
| 2 | the first patch | its premise was false: 586 of 1,938 accepted entries had not been typed by a person |
| 3 | the fourth patch | **7 shapes placed an order**, and the patch was a regression on its predecessor |

The compaction case is the one that closes a loop: the summary is written by the model about a conversation
that contains fetched pages and tool output, so text that arrived as *content the model read* could re-enter
the session inside a turn the filter called human. That is precisely the attack the stair exists to stop.

Four patches were written. The fourth turned a turn the person typed to *cancel* an order into one that was
stepped over, promoting an older approval in its place. **None of the four shipped.** The work stopped
rather than producing a fifth patch under review pressure, and the gate in this tree is still the original
denylist. Its open design flaws are D70, D72, D73 and D74, described in `../THREAT-MODEL.md`.

**The test:** `tools/test-pretrade-transcript-provenance.py`, 28 cases, run in CI on every push. Ten pass;
**eighteen are known-open and print their defect id on every run** -- never skipped. It exits non-zero only
on a regression, so a known defect does not turn CI red daily; it is attributed instead. Its fixtures take
their key layout from real Claude Code 2.1.278 transcript entries with all content replaced, because a
fixture shaped only to the filter's own assumptions cannot detect the harness writing something the filter
misreads.

**What it supports:** that the stair is broken in these specific, named ways, and that a future change which
breaks one of the ten passing cases will be caught. **What it cannot support:** anything about a shape
nobody has tried, which is the argument for a design that fails closed rather than one more patch.

What is protecting the account meanwhile is not this code: every order, cancel and alert tool the connector
exposes is in the harness permission deny list.

## 2. The runnable demonstration

`demo/run_staircase_demo.py` walks every stair of the gate in eleven cases, from a clean clone, with no
network and no secrets, using only the standard library. It prints the hook's own reason each time and exits
non-zero on any mismatch.

The tenth case is the one that makes the other ten mean something: it satisfies all four conditions and is
**allowed**. A demonstration in which everything blocks cannot distinguish a working defence from a gate
that blocks everything.

## 3. The reasoning-evaluation harness

`evaluation/` holds a harness for scoring reasoning rather than output format: the protocol, its case set,
the scoring path, reviewer controls, and the tests that cover them. 35 files are published, including seven
test files.

**What it cannot support:** any claim about model quality. It has been exercised on development cases; it
has not been run as a graded evaluation whose result is reported here. `CAPABILITIES.md` marks what was
executed and what was only read, and this is in the second group for its end-to-end path.

## 4. The prior-calls record, which is too small to calibrate

Every `/invest` run records its rating, the confidence it stated, and the reasoning behind both. Later runs
on the same company grade the earlier ones and list, row by row, where new evidence changed a prior claim.
You can read one in `examples/01-equity-analysis-end-to-end.md`, which grades the two runs published beside
it as examples 5 and 6.

That per-analysis discipline is real and it is visible. **What it does not yet support is a calibration
claim**, and this section exists to say so with the numbers rather than to imply otherwise.

Aggregating the whole call log, and counting only calls with a realized three-month return:

| Calls | n | Result |
|---|---|---|
| Rated BUY | 5 | 4 of 5 rose; mean three-month return +15.1%, at a mean stated conviction of 37% |
| Rated HOLD, i.e. declined to act | 24 | 17 of 24 did not rise; mean three-month return -7.5% |

**Five scored BUY calls is not a track record.** A hit rate computed on five observations has a confidence
interval wide enough to contain almost any true value, and reporting a four-in-five hit rate would be an
inflated claim on this evidence. It is stated here only so the denominator is visible.

The larger and more meaningful group is the second one: across 24 calls where the system's answer was to do
nothing, 17 of those names did not rise over the following three months. That is weak evidence that the
system's refusals were not simply timidity, and it is the more interesting result, because a research system
that is willing to reach "no" and be measured on it is rarer than one that is willing to reach "buy".

**These are outcomes of rating calls on public companies, not account returns.** The log records what the
system said about a name, not what was held, and nothing here is a statement of investment performance.

**What would make this evaluable:** more scored calls, a pre-registered definition of "worked" fixed before
the outcomes were known, and a horizon chosen in advance rather than read off whichever column is populated.
None of those is true of the present record, and the sizing method already applies the conservative
correction that matters in the meantime -- half-Kelly on a capped payoff ratio, with a reward-to-risk hurdle
that must be cleared before any position is opened at all.

## What none of this evaluates

No claim here bears on returns, alpha, or whether the analysis is any good as analysis. What is evaluated is
whether the machinery does what it says: whether a gate blocks what it claims to block, whether a formula
computes what its definition says, whether a component runs. `docs/quant-formula-index.md` records 21
formulas that do not, and they are published rather than quietly corrected.
