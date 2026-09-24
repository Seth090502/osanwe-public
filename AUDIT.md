# How this public copy was produced

This repository is a mirror of a private working system, published after an audit. This file records how the
copy was made and, more usefully, what each check can and cannot detect. Nothing here says the copy is
"clean": a check is only as good as the class of problem it can see.

## Order of operations

1. **Inventory.** Every file in the working system was classified, with no file left unclassified.
2. **Verification.** Components were run, or exercised by a passing test, or read. `CAPABILITIES.md` keeps
   those three states apart and never merges them.
3. **Publish decision.** Each file was assigned PUBLISH, PUBLISH-SANITIZED or withheld by a first-match rule
   set.
4. **Sanitizing.** Mechanical replacement rules, then ownership-context masking, then curated line edits.
5. **Checks.** Everything in the next section, re-run after every rebuild until each one was stable.

## Execution evidence, and what replaced it here

**Execution evidence was gathered on the originals, not on these files.** The suites, the hook probes and the
formula checks all ran against the working system. Publishing edits text, so the published copies were checked
for *equivalence* to the originals instead:

- **Python**: both sides parsed to syntax trees; every string constant normalised to a single token, so string
  literals, docstrings and comments may differ freely. The remaining trees were compared exactly, and
  identifier sets compared separately. 272 files equivalent; seven differ, all named in the table below.
- **JSON and JSONL**: key structure and container type at every key path compared. Values may differ; shape
  may not. 61 files equivalent; one fixture differs in a value's type, named below.
- **TOML**: key structure compared. 13 files equivalent.
- **PowerShell**: parsed with the PowerShell parser, string and comment tokens dropped, the remaining token
  stream compared in order. 10 files equivalent.
- **Shell and JavaScript**: syntax checked on both sides, since neither has a portable structural form here.
  44 files parse on both sides.
- **Unchecked**: 288 files -- 232 Markdown, 18 `.txt`, 11 without a suffix, and a handful of model files,
  `.cmd`, `.yaml`, `.sha256`, `.sql`, `.base`, `.html` and `.ini`. Prose was reviewed by reading, not by parsing.
- **No original to compare against**: 26 files. 21 are files this audit wrote (this file, the readme, the
  architecture, capabilities, threat-model, withheld and changelog documents, the evals and orchestration
  documents, the formula index, the demo and its readme, the four worked examples, the two licences, the
  continuous-integration workflow, and two short readmes standing in for generated directories). The other 5 are working-system files published under a masked name,
  listed in the next table.

| Difference | File | Explanation |
|---|---|---|
| One identifier renamed | `tools/pit/edgar_pit.py` | The author's local folder name was also a Python variable name. Masking it as a path placeholder produced invalid Python, so the variable is renamed instead. |
| One condition generalised | `tools/kernel_lib.py` | The original keys a cost-basis caveat to a hard-coded value; the published copy keys the same caveat to an input flag, `transferred_basis=True`, so a caller must pass the flag where the original needed none. |
| String values generalised | `tools/kernel_lib.py`, `tools/pretrade_lib.py`, `tools/staged-order.schema.json`, `tools/consolidator.py`, `tools/vault-score-check.py`, `tools/vault-census.py`, `.claude/workflows/brief-research.js`, two test fixtures | Account keys, domain labels, one workflow lane and fixture symbols that named the author's accounts or personal domains carry generic values in this copy. The structure the equivalence check compares is unchanged, but a caller that passes one of the original values gets a different result. |
| Entries removed or added | `.claude/hooks/seed-commitment.py` and its Codex copy, `tools/usage-ledger.py`, `tools/score-outcomes.py` | A dictionary entry and two list entries named the author's personal domains and are removed; a crypto hint set gains common coins. |
| Test identifiers renamed | `tools/test-fetch-prices.py` | A split test uses a synthetic symbol; the test still passes. |
| Fixture value nulled | `tools/test-fixtures/options-ledger-fixture.jsonl` | A tax note is `null`; the suite that reads the fixture still passes. |
| Five files renamed | thesis-labelled paths | Thesis names are replaced by neutral labels everywhere, including in file names, so links still resolve. |

## The checks, and the blind spot in each

| Check | What it covers | What it cannot detect |
|---|---|---|
| Pattern denylist over every published file | Known shapes: names, addresses, paths, account phrasing, health terms, thesis labels | Anything not shaped like a pattern. It cannot see a holding stated in ordinary prose, a roster in a table, or a figure that merely resembles a real one. It is deliberately switched off for tickers, which are kept for analysis. |
| Path and name scan | Every file path and directory name, plus commit messages and the pull-request title and body before they are created | Content. A clean path says nothing about the file. |
| Ownership-context detector | Lines that state or imply ownership, matched by vocabulary and then read by hand | Ownership stated in vocabulary the detector does not carry. It missed roster disclosures written in ordinary prose, which a later full read found and which were then removed. |
| Private-figure scan | The author's real figures, in every written variant (separators, currency signs, integer part, roundings, k-notation), matched against every published line | Figures below three significant digits, which are not evidence; and any private figure that does not appear in the withheld files it reads. |
| Logic equivalence | Whether sanitizing changed code behaviour | Whether the code was correct to begin with. |
| Publish self-test | Every published Python and JSON file parses; no ownership placeholder is left inside code | Prose damage, and any language it does not parse. |
| Privacy read | Fresh readers, no keyword list, reading every published file in full and reporting anything personal | Human judgement's own limits, and whatever a reader does not recognise as personal. |
| Re-identification test | Whether a reader can name what the placeholders stand for | Inference from outside this repository. |

Two of those checks found what the others could not. The private-figure scan found brokerage account numbers
and a per-name held roster inside a research file that every pattern check had passed. The logic-equivalence
check found five published shell scripts that had stopped parsing, because a bracketed placeholder is a
redirect operator in shell.

A re-identification test was then run against the finished tree: a reader with no access to anything
withheld, asked to name what each placeholder stands for. It recovered all five thesis labels, from a file
title, a wikilink alias, a fund's registered name and a standards URL, and it inverted several ticker
placeholders by finding the same worked example restated in the clear a few lines below its masked version.
Those specific routes are closed. The general one is not: a thesis label is a market theme, and a market
theme is recoverable from the analysis written about it. The labels should be read as a convention of this
copy, not as protection.

What that test did NOT recover, after those repairs, is the contents of any account, any figure belonging to
the author, or anything about their health, location or employment. **It was too generous about positions.**
A later ownership review found the book's shape -- which names were held, which was the concentrated one --
still recoverable, almost always through a placeholder sitting beside an unredacted twin of the same fact.
Those are removed in this copy, and the scanner that missed them now has a rule for exactly that pattern.
The author's name is published deliberately, in the licence copyright line and one line near the top of
the readme; the account handle also appears in this repository's own URLs, because it lives under that
account. The broker is identifiable from the connector's tool names, which the code needs; that is
disclosed deliberately rather than masked in some places and not others. Identity was never the thing being protected here -- what is
protected is everything attached to it.

An earlier report in this audit said the denylist had zero unaccepted hits. That was true of the denylist, and
it was not a statement about privacy: at that moment the tree still contained exact token counts, a cash
balance, a trade plan, a book size, account numbers and a held roster. The correction is recorded here
deliberately, because "zero hits" is the kind of sentence that gets quoted later without its qualifier.

## What was executed, and what was not

Three different statements, which are easy to blur and are kept apart here.

1. **The working system was exercised during the audit.** Test suites, validation scripts and probes were run
   against the author's own copy, and the evidence behind every VERIFIED claim comes from those runs.
2. **The published files were not executed to produce that evidence.** They were checked for equivalence to
   the originals instead: every Python file's syntax tree compared with its original so that only string
   literals, comments and docstrings differ, every JSON file's key structure, and a parser or linter for the
   other languages where one exists. Of 434 files checked, 356 came back equivalent, 44 parsed correctly in
   both copies, eight have an explained difference, 26 had no original to compare against, and none was
   broken by sanitizing in a way the comparison can see. The comparison normalises string literals away, so
   a redaction that broke a literal the code parses is invisible to it; the test run below found one.
3. **The published test files WERE executed, from a fresh copy of this repository, and they do not all pass.**
   50 of 72 exit 0; 22 do not. 49 of the 50 are also run by continuous integration on a clean Linux runner --
   `.github/workflows/tests.yml`, read-only token, no secrets, four packages installed -- so the figure can
   be checked by anyone rather than believed. The 50th, `tools/test-delegate.py`, grades a local language
   model and passed here only because one was running; CI has none. The 22 that fail are named in the table
   below with the reason each gave. They were recorded, not repaired, with two exceptions that were the
   publication's own doing. Three hash pins had been made stale by sanitizing: a pin that no longer matches
   the bytes it covers is a false integrity claim, so the build now recomputes every pin over the published
   bytes (and drops the one whose file is withheld), and the clean-room check verifies each pin
   independently. And a redaction rule had matched the credential part of a synthetic URL in
   `evaluation/tests/test_protocol.py`, breaking the test that such URLs are refused; that literal is
   restored with a reserved example domain, and the file passes.

| Test file | Why it does not pass from a clean copy |
|---|---|
| `evaluation/tests/test_account_scope.py`, `test_deployment.py` | Read a pilot report under `evaluation/reports/`, which is withheld |
| `tools/fis/test_fis_e2e.py`, `test_fixture_bridge.py`, `test_institutional_benchmark.py`, `test_obs.py`, `test_research_evidence.py`, `test_shadow_mutation.py`, `test_shadow_provenance.py`, `test_twin_identity.py` | Read the working data under `Efforts/`: synthetic household fixtures, the factor and price stores, the shadow-prediction log, the planning documents |
| `tools/pit/test_dual_price_store.py` | Reads the point-in-time price store |
| `tools/fis/test_architecture_fitness.py` | One check reads withheld working data; three order-gate checks run the published hook, which imports its library from a hard-coded vault root that publishing replaced with a placeholder |
| `tools/test-gate-eval.py`, `tools/test-retrieval-adapters.py` | Hard-coded paths to the author's machine, replaced by placeholders (`fix/parameterize-paths`, unmerged, removes them) |
| `.agents/scripts/gates/test-gates.py` | Its two allow-controls run against the live vault: one through a hard-coded path, one over the sizing doctrine, which is withheld |
| `tools/test-append-only.py` | Copies the session and decision ledgers, which are withheld |
| `tools/test-retrieval-admission-e2e.py` | Runs the retrieval runtime, which lives outside the repository at a path publishing replaced with a placeholder |
| `tools/test-generators.py`, `tools/test-consolidator.py`, `tools/test-telemetry-analyzer.py` | Checks that read the live vault, its planning documents or its session archive, all withheld |
| `tools/test-claudewatch.py` | One check expects two cross-references (a section of the root contract, a link in a skill) that the current documents do not carry |
| `tools/test-relay.py` | Grades a local language model; also misses one containment check in this copy |

4. **A second pass went back for everything the first pass had only read.** 261 components carried the status
   PRESENT-UNTESTED -- present, read, never exercised. All 261 were attempted in a throwaway copy of the
   working tree, under a shim that refused any write outside the sandbox, any read of the live system, all
   network access, and any commit, package install or scheduled-task registration. 217 ran with their output
   captured; 44 did not, each for a recorded reason, and the two largest reasons are themselves defects rather
   than limits of the audit. Of the 217 runs, 172 exited 0. Of the 45 that did not, most were correct
   behaviour -- a guard refusing, a suite reaching for withheld data -- and 9 exposed 8 real component
   defects. A parallel pass did the same for the formula index: every formula in it now carries a verdict.

None of that amounts to running the system end to end from a clean clone. That has not been done, and no
claim anywhere in this repository should be read as saying it has.

One thing the second pass changed about this document's own reliability is worth stating. Running the
components found faults that reading them had not, including a validation gate that measures the wrong
directory and a destructive test suite that can only run against the live system. Both had been read during
the first pass and passed. "Read and looks right" is a weaker claim than it feels like, and this audit made
that mistake at its own scale before finding it: the build applied its redaction rules only to files a first
pass had flagged, so rules added later never reached a third of the tree.

## What is withheld

Withheld material is not in this repository in any form. Where a withheld directory is part of the
architecture, a stub marks the place and says what lived there. Withheld: portfolio and account contents,
balances, share and token counts, cost basis, trade and decision records, session ledgers, personal
records, transcripts, caches, checkpoints, vector indexes, runtime
state and every working directory.

## Reproducing the checks

The audit tooling is not published: it necessarily contains the private values on the left-hand side of every
replacement rule. What is published is the result, and this description of the method, so a reader can judge
the method rather than take the result on trust.
