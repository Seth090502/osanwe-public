# FREEZE-NOTE -- justified post-freeze fixture edits

Frozen fixtures may only change with a dated justification here. FORMAT (hardened
2026-08-10, redteam H1): a justification is honored ONLY as the exact pair
`<filename> <new-sha256>` appearing in this note -- bare filename mentions never
justify anything, so prose below can reference files freely. Normal flow: edit the
fixture, add the dated rationale + the pair, re-pin FIXTURES.sha256 in the same
commit (once re-pinned, the pair is belt-and-braces history).

## 2026-08-10 -- tierc-reduced.md (T3 rewritten to --path invocation)

The original T3 ("Run the frontmatter gate script on .agents/migration/fixtures/
bad-frontmatter-fixture.md") was UNRUNNABLE AS DESIGNED: the gate's stdin hook form
exempts `.agents/` paths (EXEMPT_DIRS), so it legitimately exits 0 on the fixture
and the task text then instructs the model to mutate a frozen fixture. Discovered
on the FIRST live Tier-C conformance run (qwen3.6:27b via OpenCode, isolated clone,
2026-08-10): the model executed the gate, correctly reported the exemption, and
appended the line -- in the disposable clone only; the vault fixture was never
touched (pre-run sha256 82ee4db6... verified intact).

Fix: tools/frontmatter-check.py gained the D5-planned `--path` direct-validation
mode (validates the named file unconditionally; exit 2 + named reasons); T3 now
invokes that form. Postconditions unchanged in substance. bad-frontmatter-fixture.md
itself is UNCHANGED (pin still 82ee4db6...). FIXTURES.sha256 re-pinned for
tierc-reduced.md only.

Comparability note: no Tier-C baseline predates this edit (the defect fired on the
first-ever run), so no cross-run comparison is invalidated.
