#!/usr/bin/env python3
"""driftcheck.py -- reconstruct-and-compare directory manifests, canon vs derived.

Cross-harness migration D3 Branch G (plan of record, operator-approved 2026-08-10).
Shares the transform with sync.py (single source -- prose can't diverge from code).

Covers the six enumerated drift cases:
  1 derived-edited            derived bytes != expected-from-canon
  2 canon-edited-unsynced     same detection surface as 1 (direction stated in message)
  3 canon-added               migrated canon skill with no derived dir/file
  4 canon-deleted-orphan      generated derived dir whose canon source is gone
  5 ref drift                 manifest compare covers every allowlisted file, not just SKILL.md
  6 marker/frontmatter-pos    derived byte 0 must be '-' ('---'); GENERATED marker must sit
                              IMMEDIATELY after the closing frontmatter fence

Unmigrated skills (canon SKILL.md still a legacy adapter stub) are skipped and counted.
Exit 0 = no drift.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sync import (CANON, DERIVED, migrated_canon_skills, canon_file_set,   # noqa: E402
                  expected_derived_bytes, actual_derived_bytes,
                  derived_orphan_dirs, generated_marker, read_lf)


def main():
    problems = []
    migrated = migrated_canon_skills()
    for name in migrated:
        rels = canon_file_set(name)
        ddir = os.path.join(DERIVED, name)
        if not os.path.isdir(ddir):
            problems.append("case-3 canon-added: %s/ has no derived dir (run sync)" % name)
            continue
        for rel in rels:
            want = expected_derived_bytes(name, rel)
            have = actual_derived_bytes(name, rel)
            if have is None:
                problems.append("case-3 canon-added: %s/%s missing in derived (run sync)" % (name, rel))
            elif have != want:
                case = "case-5 ref-drift" if rel != "SKILL.md" else "case-1/2 edited-or-unsynced"
                problems.append("%s: %s/%s bytes differ (derived hand-edited OR canon edited "
                                "without sync)" % (case, name, rel))
        # file-level extras
        want_set = set(rels)
        for root, _dirs, files in os.walk(ddir):
            for fn in files:
                rel = os.path.relpath(os.path.join(root, fn), ddir).replace("\\", "/")
                if rel not in want_set:
                    problems.append("case-1 derived-edited: %s/%s exists with no canon source" % (name, rel))
        # marker + frontmatter position
        smd = os.path.join(ddir, "SKILL.md")
        if os.path.isfile(smd):
            text = read_lf(smd)
            if not text.startswith("---"):
                problems.append("case-6 marker/frontmatter: %s derived byte 0 is not '---'" % name)
            else:
                end = text.find("\n---\n", 3)
                if end < 0:
                    problems.append("case-6 marker/frontmatter: %s derived has no closing fence" % name)
                else:
                    after = text[end + 5:]
                    if not after.startswith(generated_marker(name)):
                        problems.append("case-6 marker/frontmatter: %s GENERATED marker not "
                                        "immediately after the closing fence" % name)
    for name in derived_orphan_dirs():
        problems.append("case-4 canon-deleted-orphan: derived %s/ is generated but canon is gone "
                        "(run sync to remove)" % name)
    n_un = len([1 for d in (sorted(os.listdir(CANON)) if os.path.isdir(CANON) else [])
                if os.path.isfile(os.path.join(CANON, d, "SKILL.md"))]) - len(migrated)
    if problems:
        print("driftcheck FAIL -- %d problem(s) (%d migrated checked, %d unmigrated skipped):"
              % (len(problems), len(migrated), n_un))
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    print("driftcheck OK: %d migrated skill(s) manifest-clean (%d unmigrated skipped)"
          % (len(migrated), n_un))
    sys.exit(0)


if __name__ == "__main__":
    main()
