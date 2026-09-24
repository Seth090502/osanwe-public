# The action staircase, run against the real hook

```bash
python demo/run_staircase_demo.py
```

No arguments, no network, no credentials, no configuration. Standard library only. It finishes in about a
second and exits non-zero if any step does not behave as documented.

## What it is

This drives **the same PreToolUse hook the live system uses**, as a subprocess, against synthetic tool
payloads and synthetic session transcripts inside a temporary directory. Nothing touches a broker. The
`OSANWE_PRETRADE_STATE_DIR` environment variable points the gate's signing key and pass directory at that
temporary directory, which is removed when the run exits. The figures in the gate evaluation at the end are
invented; the book it sizes against is synthetic and labelled as such.

Eleven steps, each printed with the hook's own refusal reason:

| # | Step | Expected |
|---|---|---|
| 1 | a read tool | allow |
| 2 | an unknown, newly added broker tool | block |
| 3 | an option-order tool with every other condition satisfied | block |
| 4 | an equity order with no authorising phrase in the turn | block |
| 5 | the phrase arriving inside a tool result | block |
| 6 | a genuine phrase, but no gate pass | block |
| 7 | a forged pass signature | block |
| 8 | a valid pass with the order altered underneath it | block |
| 9 | a validly signed pass, back-dated past its TTL | block |
| 10 | all four conditions satisfied | allow |
| 11 | the same order replayed | block |

Step 9 uses a genuinely signed pass carrying an old timestamp rather than making you wait fifteen minutes.
Step 10 is a real PASS from `tools/pretrade_gate.py` against a synthetic book, not a simulated one, so the
allowed case is as real as the blocked ones.

## What it shows, and what it does not

**It shows behaviour. It does not show soundness.**

Every step here is a case someone chose. A passing run means the gate behaves as documented on eleven
inputs; it does not mean no twelfth input gets through. That distinction is not academic in this repository:
**stair 1 of this staircase has four open defects found by adversarial review** (D70, D72, D73 and D74),
and this demo passes anyway, because none of the eleven steps is the shape that breaks it. A green
demo over a flawed control is exactly the failure mode worth seeing once.

Steps 7 to 11 exercise stairs 2, 3 and 4, which held in every case tested. Steps 4 and 5 exercise stair 1,
which has the open defects above.

Read [`../docs/threat-model.md`](../docs/threat-model.md) before drawing any conclusion about what this system
prevents. It records what was attacked, what got through, and what is protecting the account meanwhile --
which is the harness permission deny list, not this code.

## If a step fails

The step prints `<-- MISMATCH`, the tally drops below eleven, and the process exits 1. That path is itself
tested: an expectation is flipped in a throwaway copy and the non-zero exit confirmed, because a demo that
goes green over a broken gate would be worse than having none.
