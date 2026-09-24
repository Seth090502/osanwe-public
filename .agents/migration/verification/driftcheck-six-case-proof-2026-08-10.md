# driftcheck six-case proof -- 2026-08-10 06:48Z

Subject skill: gate (migrated). Each case deliberately induced, driftcheck run, then restored (clean run asserted after every restore).

| Case | Induction | Verdict | exit | Detection line |
|---|---|---|---|---|
| 1 | derived-edited (byte appended to derived SKILL.md) | LOUD | 1 | - case-1/2 edited-or-unsynced: gate/SKILL.md bytes differ (derived hand-edited OR canon edited without sync) |
| 2 | canon-edited-unsynced (byte appended to canon SKILL.md) | LOUD | 1 | - case-1/2 edited-or-unsynced: gate/SKILL.md bytes differ (derived hand-edited OR canon edited without sync) |
| 3 | canon-added (new canon ref with no derived counterpart) | LOUD | 1 | - case-3 canon-added: gate/ref-driftproof.md missing in derived (run sync) |
| 4 | canon-deleted-orphan (canon dir removed; generated derived remains) | LOUD | 1 | - case-4 canon-deleted-orphan: derived gate/ is generated but canon is gone (run sync to remove) |
| 5 | ref drift (derived ref-gate-tables.md mutated) | LOUD | 1 | - case-5 ref-drift: gate/ref-gate-tables.md bytes differ (derived hand-edited OR canon edited without sync) |
| 6 | marker violation (GENERATED marker altered after fence) | LOUD | 1 | - case-6 marker/frontmatter: gate GENERATED marker not immediately after the closing fence |

RESULT: ALL 6 CASES LOUD
