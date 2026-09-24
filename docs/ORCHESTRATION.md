# How long-horizon agent work is governed here

This describes the method used to build and audit this system, not the system itself. Everything in it is
structural: no private content appears, and none is needed to follow the argument.

The problem it answers is narrow. A single agent session is bounded by its context and ends. The work here
runs for days, across many sessions and several models, and touches something with money behind it. That
needs a way for an agent to pick up where another stopped, and a way for a person to stay in control of
decisions without reading every diff.

## Who did what

- **The owner** set the objectives and the acceptance criteria, and approved the gates. Every irreversible
  step waited on their explicit word.
- **A separate reviewing model** drafted the governing briefs and, later, independently re-read the
  published pages as an outside reader.
- **An executing agent** did the work: the inventory, the verification runs, the sanitization pipeline, the
  documents, the fixes.

That last split is worth stating because it turned out to matter. See "What a second reader caught" below.

## The parts

### A governing brief

Work starts from a written brief that states the job, why it matters, the outcomes, how to work, the
guardrails, and the hard stops. Outcomes are written as end states rather than tasks, so an agent can
choose its own route and still be judged against the same bar. The brief is the only thing that directs the
work, alongside the decision log. **Everything else the agent reads -- retrieved pages, tool output, files
in the repository, prompts stored in the vault -- is evidence, not instruction.** That rule is stated in
the agent contract and is the reason a document in the tree cannot redirect a session by containing
instructions.

### Approval gates with literal words

Consequential steps stop and wait for an exact string. Not "confirm", not a yes: a specific word chosen so
it cannot be produced by accident or inferred from context. Publishing waited on one word; pushing waited
on another; merging waited on a third. **Nothing read from a file can supply one of them.** An agent that
finds the approval word written in a document has found a document, not an approval.

The effect is that the expensive mistakes have a person in front of them, and the cheap ones do not.

### A verbatim decision log

Every instruction that changes the standing rules is recorded **word for word**, in order, with the agent's
reading of it recorded separately underneath. The two are kept apart on purpose: one is what was asked, the
other is what was understood, and when they diverge the divergence is visible instead of silently resolved.

Thirteen such decisions accumulated over this work. Several contradicted earlier ones -- a policy was
reversed outright partway through -- and because the log is append-only, the reversal reads as a reversal
rather than as though the new rule had always been the rule.

### State on disk, so a session can be resumed

A running state file records what is done, what is in flight, what was decided on a default and how to undo
it, and the specific things that were true and would not be guessed by the next session. Context runs out;
disk does not. The file is written after each completed outcome, not at the end, because the end is exactly
when a session fails to arrive.

The most valuable entries in it are not the status ones. They are the traps: the pipeline step that has to
run before another or a digest covers stale bytes; the edit keyed to a path that no longer exists and so
silently does nothing; the renderer that eats a token every check reads correctly from source. Each was
learned once, expensively, and written down so it is learned once.

### Worktree isolation

Fix branches are built in git worktrees **outside** the live directory, so the working system stays on its
main branch the whole time and is never mid-checkout. A branch is built, tested, reviewed and left
unmerged; merging is a separate decision, made later, with its own conditions.

This is more than tidiness. The live directory is the system: scheduled jobs run from it unattended, and
one of them committed to the repository unprompted during this work. Checking out a branch there would have
handed a scheduled task a half-built tree.

### One-time exceptions, with reasons

Some actions are permanently forbidden -- making a repository public, deleting one, force-pushing,
rewriting history. Others are forbidden **by default** and granted once, in writing, for one use: create
this repository; push this branch; merge this pull request. Each grant names its scope, and the state file
records which are spent and which stand. A spent exception does not generalise to the next similar action.

## The audit as the worked case

The pass that produced this repository ran under that structure: a brief, two approval gates, a verbatim
log, a state file, and a pipeline that could be re-run from one command.

What it produced is in `AUDIT.md`. What is worth reading here is where the method caught something.

### Where the agent stopped itself

Three times, continuing would have been easy and stopping was correct.

1. **A repository was created to receive the publication, and the first commit carried the wrong email
   address** -- the account's real one rather than its private alias, because a setting was off. The
   instruction said to verify the author of that commit before cloning. It did not match, so nothing was
   cloned, nothing was pushed, and the run stopped with a note. The failure being guarded against was
   exactly the one the audit had found in the *previous* repository's history.
2. **An instruction contained an unfinished editing note to itself** -- a bracketed reminder the author had
   meant to resolve before sending. Acting on it would have required guessing which of two readings was
   meant. The agent stopped and asked instead, and the answer changed the policy.
3. **An adversarial test of the system's own order gate found a way through it.** The standing rule was
   that such a finding outranks whatever else is in progress. Work stopped, the finding was verified
   independently rather than relayed on trust, and it was reported before anything else continued.

### The worked case: four patches, and the decision not to write a fifth

This is the episode the rest of this document exists to make possible, so it is worth following in full.

A standing instruction said: if any transcript shape authorises an order without a person typing it, stop
and report, because that outranks the brief in progress. What happened over one night:

| Round | What the reviewer did | Result |
|---|---|---|
| 1 | attacked the shipped gate with transcript shapes nobody had tried | **8 shapes authorised an order**, including the model's own compaction summary |
| 2 | attacked the first patch | its premise was false -- 586 of 1,938 accepted entries had not been typed by a person |
| 3 | attacked the fourth patch, end to end, with the explicit goal of placing an order | **7 shapes got through**, and the patch was a *regression on its own predecessor* |

The third round is the one that mattered. The fourth patch had been written to close a case where a flag
set to `0` slipped past a truthiness test. It did close that case. It also meant that a turn the person
typed to **cancel** an order was stepped over and an older approval promoted in its place. Measured across
the reviewer's suite, the patch changed four outcomes against its predecessor: three went from blocking to
allowing, one the other way. Nothing improved.

It also turned out that the measurement justifying the patch had been taken on the wrong population. The
flag had been counted only on one entry type and declared never to appear in its falsy form; counted across
all entry types, the harness already writes it that way over three thousand times.

**The decision was to stop, not to write a fifth patch.** Four passes had each been written under review
pressure, and each had shipped a new hole. The branch was retired unmerged rather than merged or continued.
What replaced it is a different process: write down the security properties first, have a fresh reviewer
attack the *design document* before any code exists, implement, then have a fresh reviewer attack the
implementation end to end with the explicit goal of placing an order -- and send anything that gets through
back to the design rather than to a patch.

Two things made that decision cheap to take. The finding was verified first-hand rather than accepted from
the reviewer's report, because a reviewer is model output too. And the account was never actually exposed:
every order tool sits in the harness permission deny list, so each finding was a failure of the gate behind
a permission layer that held. Knowing which layer was load-bearing is what made "stop" the calm answer instead
of the alarming one.

The open defects are published rather than quietly carried: see `../THREAT-MODEL.md` and the regression
suite `../tools/test-pretrade-transcript-provenance.py`, which prints every open shape against its defect id
on every run.

### Where the method failed, and what changed



- **A verdict of "clean" was a verdict about a checker, not about the files.** A per-file classification was
  done early, and rules added later could not reach the third of the tree that classification had already
  marked clean. Every rule written after that day was silently inert on those files. Fixed by running every
  rule over every file and treating the classification as a label rather than a gate.
- **A check that passed by examining two of one thousand four hundred and seventy-four links.** It followed
  one link syntax and never parsed the one the vault actually uses. It reported PASS. The lesson generalises
  past this repository: a check that reports success without reporting its denominator is not yet a check.
- **Checks that read the source cannot see what the renderer does.** Over a thousand masked tokens were
  correct in the source and were eaten by the web renderer as unknown HTML tags, so the published pages read
  as damaged while every check passed. Nothing caught it until a person looked at a rendered page.
- **A second-pass edit broke a first-pass edit's sentence.** One edit rewrote a sentence; a later one
  replaced the sentence carrying the antecedent it referred to. Both edits succeeded. Only reading caught it.
- **The privacy gate reported failure and let the build finish anyway.** The publish pipeline documents
  that any failing step stops the run, and enforced that by checking exit codes. But its self-test and both
  of its scanners print a verdict and **always exit 0**. So a build printed `UNACCEPTED: 2` and
  `self-test: FAIL` and went on to produce a finished, apparently publishable tree. The gate was a
  thermometer, not a thermostat, and the only thing standing between a failing privacy scan and a push was
  a human reading the numbers. It was caught because someone did read them -- which is not a control.
  Recorded as defect D71 and fixed by gating on each step's own parsed result at the one place that already
  reads it, with a step whose output shape changes now raising rather than being taken as a pass. The two
  hits it had been quietly reporting were real: a private figure in a file being published for the first
  time, in a second phrasing of a fact an existing redaction already covered. It had never been pushed.

  The governance lesson is the same one as the gate's: **a check that cannot fail is not a check.** Both
  findings this method produced were of that shape -- a control that looked like it was working because
  nothing had made it speak up.

### What a second reader caught

Near the end, an independent model re-read nine published documents as an outside reader. Everything it
found had already passed the executing agent's own checks:

- a private company name sitting in a published example -- and, once searched for
  properly, in a second file the first reader had not known about;
- account types left in a methodology document that a policy decision had said to make generic;
- a licence on the prose that contradicted the owner's own recorded decision;
- a status table that summed two different populations into one total;
- placeholder tokens the web renderer was eating, in over two hundred files;
- one thousand four hundred and seventy-two links pointing at material that is not in the repository.

None of these needed privileged access or new tooling. They needed someone who had not built the thing
reading it as a stranger would. **That is the argument for multi-model review in one paragraph**: the
checks an agent writes encode the same assumptions as the work it did, so they cannot find an error in the
assumption. A different reader can.

## What this method does not give you

It does not make an agent's work correct. It makes the work **inspectable**, and it puts a person in front
of the steps that cannot be undone. Every defect described above survived one or more automated checks.
What caught them was a rule that findings are written down rather than fixed quietly, an append-only record
that makes a reversal visible, and a second reader who had not done the work.
