# This directory is generated

15 subagent definitions that normally live here are not published, because a generator in this repository
reproduces every one of them from a source that **is** published.

| | |
|---|---|
| Generator | `.agents/scripts/gen-roles.py` |
| Source | `.agents/roles/` (published in full: 15 role files, a template and a `.gitkeep`) |
| To recreate this directory | `python .agents/scripts/gen-roles.py` |
| To check it without writing | `python .agents/scripts/gen-roles.py --check` |

## What a role file holds, and what the wrapper adds

A role file in `.agents/roles/` is the portable definition of one subagent: its name, a description bounded
to 400 characters, the tools it may use, its model and effort, and a body after a `## Role Body` marker.
`gen-roles.py` turns each into the wrapper format Claude Code expects and writes a marker naming the
generator and the exact source file. All 15 withheld files carry that marker; the mapping to the 15 role
files is one to one, with no role left without a wrapper and no wrapper without a role.

Hand-authored files in this directory that carry no generated marker are never touched by the generator, and
none is withheld here.

## A known defect you can see from the source

Three of these wrappers -- `lane-editor`, `lane-extractor` and `lane-researcher` -- are generated with an
empty frontmatter block and cannot be registered as agents. The fault is in the generator's handling of a
role file with no frontmatter, not in the definitions. It is recorded in `docs/audit.md` and repaired on a branch
that is not part of this repository.

## If you followed a link here

Several published files reference this directory: the generator itself, the checks that count registered
agents, and the compatibility notes. Those references describe how the directory is produced and what
should be in it. Run the generator once and they resolve.

This stub is the only file the audit adds here. Nothing was edited to produce it.
