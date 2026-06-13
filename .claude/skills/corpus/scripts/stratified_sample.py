#!/usr/bin/env python3
"""Pick a stratified MVP sample of N PDFs from a source directory.

Stratification heuristic uses filename pattern matching since extractions
do not yet exist at MVP time.

DOMAIN-SPECIFIC: The PATTERNS dict below is currently configured for UAP-class
corpora (the original corpus this script was built on). For other domains
(legal discovery, regulatory dockets, FDA filings, congressional records),
copy this script to your corpus workspace's scripts/ folder and customize
PATTERNS for your domain. The categorize() function and main() control flow
are domain-agnostic.

Default UAP-class categories and patterns:

    dod-uap     : 'dow.uap', 'uap-mission', 'uscentcom', 'dod'
    fbi-vault   : 'fbi', 'vault', 'hq-65'
    blue-book   : 'blue.book', '\\bbb\\b', 'project-grudge', 'project-sign'
    nasa        : 'nasa', 'apollo', 'jsc-'
    state-cable : 'state-dept', 'cable', 'telegram', 'deptel'
    other       : everything else

Usage:
  python stratified_sample.py --source <absolute-path-to-pdf-dir> --n 5

Output: prints categorization summary, then the N selected PDFs (one per
line, prefixed by category tag) to stdout.

Stdlib only.
"""
from __future__ import annotations

import argparse
import random
import re
import sys
from pathlib import Path

PATTERNS: dict[str, list[str]] = {
    "dod-uap": [r"dow.uap", r"uap-mission", r"uscentcom", r"\bdod\b"],
    "fbi-vault": [r"\bfbi\b", r"\bvault\b", r"hq-65"],
    "blue-book": [r"blue.book", r"\bbb\b", r"project-grudge", r"project-sign"],
    "nasa": [r"\bnasa\b", r"apollo", r"jsc-"],
    "state-cable": [r"state-dept", r"\bcable\b", r"telegram", r"deptel"],
}


def categorize(name: str) -> str:
    nm = name.lower()
    for cat, pats in PATTERNS.items():
        for p in pats:
            if re.search(p, nm):
                return cat
    return "other"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Stratified MVP sampler for document corpora "
        "(PATTERNS dict in this file is domain-specific; UAP-class defaults shipped; "
        "customize per corpus for other domains)"
    )
    ap.add_argument("--source", required=True, help="Directory containing source PDFs")
    ap.add_argument("--n", type=int, default=5, help="Sample size (default 5)")
    ap.add_argument("--seed", type=int, default=42, help="Random seed (default 42)")
    args = ap.parse_args(argv)

    src = Path(args.source)
    if not src.is_dir():
        print(f"ERROR: source {src} is not a directory", file=sys.stderr)
        return 2

    pdfs = sorted(src.glob("*.pdf"))
    if not pdfs:
        print(f"ERROR: no PDFs in {src}", file=sys.stderr)
        return 2

    random.seed(args.seed)
    by_cat: dict[str, list[Path]] = {}
    for p in pdfs:
        c = categorize(p.name)
        by_cat.setdefault(c, []).append(p)

    print(f"Categorized {len(pdfs)} PDFs into {len(by_cat)} category bucket(s):")
    for c, files in sorted(by_cat.items()):
        print(f"  {c}: {len(files)}")

    # One per category up to n; fill remainder from any remaining pool
    sample: list[Path] = []
    cats_with_files = [c for c in by_cat if by_cat[c]]
    random.shuffle(cats_with_files)
    for c in cats_with_files:
        if len(sample) < args.n:
            sample.append(random.choice(by_cat[c]))
    remaining_pool = [p for p in pdfs if p not in sample]
    random.shuffle(remaining_pool)
    while len(sample) < args.n and remaining_pool:
        sample.append(remaining_pool.pop())

    print()
    print(f"Stratified sample of {len(sample)} (seed={args.seed}):")
    for p in sample:
        print(f"  [{categorize(p.name)}] {p.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
