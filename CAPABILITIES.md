# Capabilities

What this system does, separated by how strongly each claim is supported. The separation matters more than the
totals: a component that was read is not a component that works.

## How the states are defined

| State | Meaning |
|---|---|
| **EXECUTED** | The component was run directly during the audit, or a test that names it passed |
| **OBSERVED** | The component was seen running by the harness during the audit session, with side effects recorded |
| **PRESENT-UNTESTED** | The component exists and was read, and nothing exercised it |
| **ATTEMPTED** | A second pass tried to run it in a sandbox; see the next section |
| **STALE** | Registered and reachable, but enforcing a rule the system has retired |
| **BROKEN** | Exercised and failed, or a dependency it needs does not start |
| **UNREFERENCED / ORPHANED** | Present, with nothing pointing at it |

## The headline

**352 of the 467 executable components have been run and worked.** That is the number to hold on to: the
component was executed, and what it did was what it is supposed to do. **391 ran at all** -- the difference is
the 39 that ran and then either failed or were stopped by something other than themselves.

Two populations, kept apart. The 467 are the components that can be executed or exercised. Separately, 142
reference documents carry a state describing whether anything reads them -- 105 UNREFERENCED and 37 LOADED --
and they are not executable, so they are not in the 467 and never were. An earlier version of this page
listed all seven states in one tally that summed to 609; that was two populations added together, and it is
corrected here.

| Across the 467 | Count |
|---|---|
| Ran, and worked | **352** |
| Ran, and failed | 9 |
| Ran, but the environment decided the outcome, not the component | 30 |
| Found broken by inspection, never executed | 11 |
| Parsed by a check that ran, but never executed | 5 |
| Never ran | 60 |

The first three rows are the components that were actually executed, and they sum to the 391 above. The
fourth row is separate on purpose: those 11 were judged broken by reading their wiring -- an entry point
that cannot resolve, a dependency that is not there -- and were never run, so counting them as "ran, and
failed" inflated the executed total. An earlier version of this page did exactly that, which is why its
"ran" rows summed to 402 while the headline said 391. The headline was right.

The 352 comes from two passes. The first, during the inventory, executed 174: 96 run directly, 72 exercised by
a passing test that names them, and 6 observed running in the harness with their side effects recorded. The
second went back for all 261 components the inventory had only read, and tried to run every one in a throwaway
copy of the tree under a containment shim that refused any write outside the sandbox, any read of the live
system, all network access, and any `git commit`, package install or scheduled-task registration. 217 of the
261 ran with their output captured; 44 still have not been run, each for a written reason.

Running is not passing, and a non-zero exit is not automatically a fault. Of the 217, 172 exited 0. The other
45 were classified one at a time by reading each run, not by pattern:

| Why a run exited non-zero | Count |
|---|---|
| Withheld data the sandbox does not carry | 12 |
| A real component defect | 9 |
| A missing optional YAML package | 7 |
| The containment shim stopping a component that reached for the live system | 6 |
| The component refusing, or rejecting bad arguments, correctly | 6 |
| A gate control whose fixture was deliberately excluded | 3 |
| Needs a git repository | 1 |
| Unexplained -- exit 3, no output | 1 |

The 6 correct refusals count as working, which is why 352 is 174 + 178 rather than 174 + 172. The 9 defects
are in the defect record, over 8 distinct components.

## Observed running during the audit session (6)

These were not run by the auditor; the harness ran them, and the effect was recorded.

| Component | What was seen |
|---|---|
| `log-prompt` | Appended a line to the day's note on each prompt |
| `semantic-context-inject` | Injected retrieved passages into the session |
| `session-integrity-check` | Emitted its contract-integrity warning at session start |
| `post-compact-reinject` | Re-injected the startup surface after a context compaction |
| `subagent-telemetry` | Wrote telemetry state files, visible in before/after snapshots |
| `post-tool-use-failure` | Wrote failure-capture state after a failing tool call |

## What the system can do

**Research and analysis.** Pull filings and market data point-in-time, score a company on a published formula
set, grade every piece of evidence by source quality, argue the bear case before writing a verdict, and record
the falsifiers that would overturn it.

**Portfolio mechanics.** Position sizing with explicit caps and bands, concentration accounting on two
attribution bases, correlation clustering, tax-lot-aware trim analysis, and a doctrine layer whose version is
fingerprinted into every analysis it scored.

**Knowledge management.** Typed notes with enforced frontmatter, entity notes per company, generated views
rebuilt from their sources, append-only decision and session ledgers, and a validation suite that refuses to
let a broken link or a schema violation reach a commit.

**Delegation.** A relay that hands bounded work to a local model with an approval checkpoint before the first
tool batch executes, and subagent definitions for research, scoring, criticism and scanning.

**Safety.** A pre-trade gate that blocks any brokerage tool name it does not recognise as a read; gates that
must return a verdict before a build, a financial action or a thesis change is ratified; and a pre-write
validator that refuses malformed vault Markdown.

## What is present but unproven

44 components have still not been run, down from 261. They are not a residue of effort; each one has a reason
that another hour would not remove:

| Why it stayed unrun | Count |
|---|---|
| Not an executable component -- a document, template or placeholder | 12 |
| Declarative agent definitions for another harness, consumed as configuration rather than executed, and whose in-tree generator was retired | 14 |
| Would spend money or touch credentials | 7 |
| A live per-machine profile, deliberately outside the audit's safety scope | 5 |
| Hardcodes the live system's root path with no override, so it cannot run against a copy | 3 |
| Registers operating-system scheduled tasks | 2 |
| Needs a continuous-integration runner | 1 |

The third and fifth rows are the interesting ones. "No consumer available" and "hardcodes the root path" are
not facts about the audit; they are defects in the system, and they are recorded as such. `AUDIT.md` explains
separately why the published copy could not be executed end to end.

## Known weak points

- **11 BROKEN components**, including one MCP configuration whose server fails to start.
- **6 STALE components**, including a retired commit hook that is still registered.
- **The brokerage deny list had drifted, and nothing detected it.** It named 20 tool names the connector no
  longer offers and none of the 8 live ones, so for a period the pre-trade gate's default-deny was the only
  layer standing between the agent and an order. It held. The list has since been completed and the whole
  61-tool surface re-checked without calling anything; `THREAT-MODEL.md` tells that story properly, because the
  detection failure matters more than the configuration error.
- **One documented multi-agent verification wave never runs**: its entry point fail-closes on every call.
- **Retrieval is lexical, not vector**, despite an embedding index being present: only a small admitted subset
  of documents is searchable, and ranking is lexical.
- **Some formulas do not match their published definition.** Every formula in the index now carries a verdict
  -- none is left unchecked -- and `docs/quant-formula-index.md` names each mismatch and says whether the fault
  is a specification gap or a computational defect.
- **A validation gate measures the wrong tree.** The vault audit resolves the author's own absolute path rather
  than the tree it is invoked from, so the continuous-integration step that asserts a minimum score scores a
  directory that does not exist on the runner. 132 of 500 tracked code files carry that absolute path, counting
  all three ways it gets written -- the two Windows spellings and the Git-Bash one; 108 use a Windows
  spelling. An earlier version of this page gave 108 without saying it had counted only those.
- **A destructive test suite can only run against the live system**, for the same reason, which is why six
  hook-manifest checks stayed unverified.
- **Two tools rewrite configuration on an unrecognised flag**, because they test for one flag by name and let
  everything else fall through to the write path.

69 defects were recorded during the audit rather than repaired, so this list is a starting point, not a warning
label on an otherwise clean system. 16 of the 69 came from the second execution pass -- that is what running a
component buys you over reading it -- and one more came from reading this repository after it was published,
which is the argument for reading a thing in the form its readers will see.
