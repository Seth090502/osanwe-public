# Changelog

This repository is a periodically published mirror, not a continuously developed project. Its history is the
history of the publications, not of the working system.

## 2026-09-23 -- v1.0.0, published from a fresh root

The copy published on 2026-09-20 was retired and made private, because its history still reached earlier
versions of files that described the author's own holdings. This repository starts from a new root: nothing
in its history predates the sanitized tree.

**Changed**
- Every placeholder that stood for a held name is gone. A fresh ownership review found that masks could be
  decoded from their context -- a peer that reports first, a price on a date, a chart title -- so each is
  now a generic slot or, where a line is plain company analysis, the symbol itself.
- Account types are generic throughout ("tax-advantaged account"), and worked examples built on real
  runs carry invented values.
- The build now recomputes every hash pin over the published bytes, including pins in sha256sum-format
  files, and the clean-room check verifies each one.
- `evaluation/tests/test_protocol.py`: a redaction rule had broken a synthetic URL literal; restored.

**Added**
- The heredoc guard the published settings already registered, its test, the copy helper the hook suite
  uses, and four regression suites for published tools. CI now runs 49 suites.
- In `AUDIT.md`, the 22 published test files that do not pass from a clean copy, each with its reason.

## 2026-09-20 -- Republished after a full audit

The previous public repository was retired and made private. This copy replaces it and was produced by an
audit that inventoried the working system, classified every file, sanitized what could be published, and
checked the result several different ways.

**Added**
- `README.md`, `ARCHITECTURE.md`, `CAPABILITIES.md`, `AUDIT.md`, `WITHHELD.md`, and
  `docs/quant-formula-index.md`, all written from the audit's evidence.
- `examples/`: four complete worked outputs, each with an as-of date, a not-advice line, and any defect that
  affects how it should be read stated at the top rather than in a footnote.

**Changed**
- Thesis names are replaced by neutral labels throughout, including in file names and in code identifiers.
- Local paths, the machine name, the author's identity, private file names and personal
  vocabulary are replaced by placeholders.
- Statements of what the author owns, owned or traded are removed or genericized. Analysis of public
  companies, funds and markets is kept as written, with real tickers and real published figures.
- Some documents describe portfolio mechanics against a clearly labelled synthetic illustrative book.

**Removed**
- Every private, state, cache, checkpoint and working directory, listed by area in `WITHHELD.md`.
- Fifteen individual documents whose subject is the author's portfolio rather than a method or a market.
- Hash pins covering withheld data, each replaced by a one-line comment saying why it is gone.

**Known at publication**
- The published copy was never executed end to end; equivalence to the originals was checked instead.
- Defects found during the audit were recorded, not repaired, so the code matches what was actually running.
- Some formulas do not match their published definition; `docs/quant-formula-index.md` names each one.

## Earlier

The prior public repository (2026-06) was a manual orphan export of an older state. It is not continuous with
this one, and its history is not carried forward here.
