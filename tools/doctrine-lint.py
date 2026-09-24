#!/usr/bin/env python3
"""
Osanwe DOCTRINE-LINT (INVEST KERNEL, 2026-07-06).

Enforces block-vs-prose agreement + tamper evidence on the two doctrine
machine blocks (ref-portfolio-doctrine.md `doctrine:`, ref-scoring-models.md
`bands:`). Run standalone, from tools/sizing-eval.py (fail-closed pre-step),
from tools/test-sizing-eval.py, and at /invest Phase D.8.

Checks per block (any failure -> exit 2):
  A. schema valid (kernel_lib.validate_block_schema);
  B. every lintable scalar leaf has a provenance-table row in the host note
     (`| key | value | verbatim_quote | source |`);
  C. the table value equals the block value (numeric tolerance / string eq);
  D. the verbatim quote exists as a substring of its cited source file
     ('self' = the host note; else Calendar/decisions/<stem>.md);
  E. the block value is evidenced inside the quote (numeric parse / substring);
  F. table rows with keys absent from the block are flagged (table drift);
  G. recomputed fingerprint == the block's registered `fingerprint:` field;
  H. the registered fingerprint appears in at least one
     Calendar/decisions/decision-*.md (ratification linkage -- a re-fingerprinted
     silent edit still fails until a decision record registers it).

Usage:
  doctrine-lint.py [--json] [--doctrine-file PATH] [--bands-file PATH]
                   [--fingerprint]
  --fingerprint: print the recomputed fingerprints and exit 0 (change helper).
Exit: 0 = clean, 2 = findings (fail-closed).
ASCII-only (Pattern 22). Deps: stdlib + PyYAML + tools/kernel_lib.py.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # D5: relocation-proof (2026-08-10)
import kernel_lib as K  # noqa: E402


def _num_or_str(cell):
    """Parse a provenance-table value cell: number if it parses, else string."""
    try:
        return float(cell)
    except ValueError:
        return cell


def _values_equal(block_val, cell):
    if isinstance(block_val, bool):
        return cell.strip().lower() == ("true" if block_val else "false")
    if isinstance(block_val, (int, float)):
        parsed = _num_or_str(cell)
        return isinstance(parsed, float) and abs(parsed - float(block_val)) <= 1e-9
    return str(K._norm(block_val)).strip().lower() == cell.strip().lower()


def lint_block(kind, path_override=None):
    """Return list of finding strings for one block."""
    findings = []
    try:
        block, body, host_path = K.load_block(kind, path_override)
    except K.KernelError as e:
        return ["[%s] %s" % (kind, e)]

    # B-E: provenance table cross-check.
    try:
        table = K.parse_provenance_table(body)
    except K.KernelError as e:
        return ["[%s] %s" % (kind, e)]

    source_cache = {}
    leaves = dict(K.iter_lint_leaves(block))
    for key, val in sorted(leaves.items()):
        row = table.get(key)
        if row is None:
            findings.append("[%s] leaf '%s' has no provenance-table row" % (kind, key))
            continue
        if not _values_equal(val, row["value"]):
            findings.append("[%s] leaf '%s': block value %r != table value %r"
                            % (kind, key, val, row["value"]))
        src = row["source"]
        if src not in source_cache:
            try:
                source_cache[src] = K.resolve_prov_source(src, host_path)
            except K.KernelError as e:
                findings.append("[%s] leaf '%s': %s" % (kind, key, e))
                source_cache[src] = ""
        text = source_cache[src]
        if row["quote"] and row["quote"] not in text:
            findings.append("[%s] leaf '%s': quote %r not found verbatim in source '%s'"
                            % (kind, key, row["quote"], src))
        elif not K.value_matches_quote(val, row["quote"]):
            findings.append("[%s] leaf '%s': value %r not evidenced inside quote %r"
                            % (kind, key, val, row["quote"]))

    # F: table drift (rows for keys the block no longer carries).
    for key in table:
        if key not in leaves:
            findings.append("[%s] provenance-table row '%s' has no matching block leaf"
                            % (kind, key))

    # G: fingerprint integrity.
    registered = str(block.get("fingerprint", ""))
    live = K.compute_fingerprint(block)
    if registered != live:
        findings.append("[%s] fingerprint mismatch: registered '%s' != live '%s' "
                        "(unratified block edit)" % (kind, registered, live))

    # H: ratification linkage -- the registered fingerprint must appear in a
    # decision record (re-fingerprinting a tampered block still fails here).
    ratified = False
    for rec in sorted(K.DECISIONS_DIR.glob("decision-*.md")):
        try:
            if registered and registered in rec.read_text(encoding="utf-8"):
                ratified = True
                break
        except OSError:
            continue
    if not ratified:
        findings.append("[%s] fingerprint '%s' not registered in any "
                        "Calendar/decisions/decision-*.md (ratification missing)"
                        % (kind, registered))
    return findings


def main(argv=None):
    ap = argparse.ArgumentParser(description="Osanwe doctrine-lint (INVEST KERNEL)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--doctrine-file", help="override path to the doctrine note (testing)")
    ap.add_argument("--bands-file", help="override path to the bands note (testing)")
    ap.add_argument("--fingerprint", action="store_true",
                    help="print recomputed fingerprints and exit 0 (change helper)")
    args = ap.parse_args(argv)

    if args.fingerprint:
        out = {}
        for kind, override in (("doctrine", args.doctrine_file), ("bands", args.bands_file)):
            try:
                block, _, _ = K.load_block(kind, override)
                out[kind] = K.compute_fingerprint(block)
            except K.KernelError as e:
                out[kind] = "ERROR: %s" % e
        print(json.dumps(out) if args.json else
              "portfolio-doctrine %s / forensic-bands %s (stamp pd-%s/fb-%s)"
              % (out.get("doctrine"), out.get("bands"), out.get("doctrine"), out.get("bands")))
        return 0

    findings = []
    findings += lint_block("doctrine", args.doctrine_file)
    findings += lint_block("bands", args.bands_file)

    if args.json:
        print(json.dumps({"clean": not findings, "findings": findings,
                          "count": len(findings)}, indent=2))
    else:
        if findings:
            print("DOCTRINE-LINT: %d finding(s)" % len(findings))
            for f in findings:
                print("  " + f)
        else:
            print("DOCTRINE-LINT: clean (both blocks schema-valid, prose-agreed, "
                  "fingerprint-ratified)")
    return 2 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
