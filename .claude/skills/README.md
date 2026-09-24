# This directory is generated

52 files that normally live here are not published, because a generator in this repository reproduces every
one of them from a source that **is** published.

| | |
|---|---|
| Generator | `.agents/scripts/sync.py` |
| Source | `.agents/skills/` (published in full) |
| To recreate this directory | `python .agents/scripts/sync.py` |
| To check it without writing | `python .agents/scripts/sync.py --check` |

## Why a skill has two copies at all

`.agents/skills/` is the canonical form, written once and portable across harnesses. Claude Code reads its
skills from `.claude/skills/`, Codex from `.codex/`. Rather than maintain the same procedure three times,
the canonical copy is the only one anybody edits and the harness-specific copies are generated from it. Each
generated `SKILL.md` carries a marker naming the generator and its source, and `sync.py --check`
reconstructs the whole directory and fails on any difference, so drift is detected rather than discovered.

Of the 52 withheld files, 36 are byte-identical copies of their canonical source and 16 are `SKILL.md` files
that `sync.py` transforms, chiefly by re-materialising the harness's `allowed-tools` list from canonical
metadata. Nothing is in the generated copies that is not in the source or the generator.

## One file here is not generated, and it is published

`AGENTS.md` in this directory is hand-written and sits on `sync.py`'s never-touch list: the generator neither
writes nor deletes it. It is in the repository.

## If you followed a link here

Some published files reference paths under this directory -- a few by name, such as a configuration pointing
at a reference table, and rather more that simply describe the layout. Those paths resolve after the
generator has been run once. The content behind them is not missing from the repository; it is in
`.agents/skills/` under the same relative path.

This stub is the only file the audit adds here. Nothing was edited to produce it.
