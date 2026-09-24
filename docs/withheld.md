# What is not in this repository

This copy is a mirror of a working system with the author's own material removed. Rather than leave silent
gaps, this file says what is missing and why, so a reader can tell the difference between "the system does not
do this" and "this part is not published".

Notes in this repository link to each other by name. Where a note names another note in plain text rather than
as a link, that note is one of the files withheld below.

## Whole areas

| Area | What lived there | Why it is withheld |
|---|---|---|
| `Calendar/` | The append-only decision, session and execute-or-decline ledgers, the dated decision records, and the daily notes | Every entry is a record of what the author decided, traded or intended to trade, with dates |
| `private/` | Holdings, account contents and personal material | Personal data, in full |
| `Efforts/` | The working directories of in-flight missions, including data stores and sandboxes | Work-in-progress state over the author's own book |
| `_archive/`, `_quarantine/`, `.backups/` | Superseded copies of the above | Same content, older |
| `wiki/investing/snapshots/`, `wiki/investing/benchmarks/` | Net-worth snapshots and benchmark runs | Balances and positions |
| `wiki/entities/` | Per-company state notes | They carry the author's own rating and holding state per name |
| `.claude-ox/`, caches, vector indexes, runtime state, transcripts | Harness state and derived indexes | Session history and machine state; nothing analytically useful without the rest |

## Individual documents

Fifteen published-eligible documents were pulled after a privacy read, because their subject is the author's
portfolio rather than a method or a public market: reference documents built around their holdings, a
held-position earnings calendar, a correlation and scoring pair that marked which names they own, a review of a
live run containing a broker read, a sizing test whose fixture is their real book, a playbook about their own
execution failures, and the routing fixtures that record their real prompts. `docs/audit.md` explains how they were
found.

A few files were left out because they would only be clutter here: two launcher scripts for a per-machine
harness profile that is itself withheld, a workflow that checks the working vault's own data and so could only
fail in this copy, and a scratch work directory under `tools/pit/`.

## Generated copies

Two directories are absent because a generator in this repository rebuilds them from a source that is
published, so shipping both would put the same content in the tree twice:

| Directory | Files withheld | Generator | Published source |
|---|---|---|---|
| `.claude/skills/` | 52 | `.agents/scripts/sync.py` | `.agents/skills/` |
| `.claude/agents/` | 15 | `.agents/scripts/gen-roles.py` | `.agents/roles/` |

Each directory keeps a stub naming its generator, its source and the command that recreates it. The one
hand-written file inside `.claude/skills/`, its `AGENTS.md`, is on the generator's never-touch list and is
published.
`.codex/` is published as it stands: its agent definitions were produced by a generator that no longer
exists in the tree, so nothing here could reproduce them, and its hook copies are copies rather than
generated output. Generation was confirmed by byte comparison against the source and by each file's own
generator marker, not by running a generator.

## What this means for the code

Tools that read those directories will find them empty. The code paths, schemas and tests are all here; the
state they operated on is not. Where a hash or dataset pin covered withheld data, the pin was removed and a
one-line comment left in its place, so the gap is visible in the source rather than silent.
