#!/usr/bin/env python3
"""insight-rank.py -- A5: rank insight candidates for one-pass ratification.

Reads the candidates file produced by insight-candidates.py and scores each by:
  - signal strength (cue phrase weight: 'critical finding' > 'learning')
  - specificity (numbers present = actionable)
  - duplication flag (possible_dup=y sinks)
Emits a ranked promote/merge/reject suggestion list appended to the candidates
file as a RANKING section.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

WEIGHTS = {
    "critical finding": 3,
    "pattern observed": 3,
    "key finding": 2,
    "lesson": 2,
    "insight": 2,
    "learning": 1,
    "realized": 1,
    "again": 1,
}


def score(snippet):
    s = snippet.lower()
    score_val = max((w for cue, w in WEIGHTS.items() if cue in s), default=0)
    if re.search(r"\d", snippet):
        score_val += 1  # numeric specificity
    if len(snippet) > 150:
        score_val += 1  # richer context
    return score_val


def main():
    srcs = sorted((ROOT / "wiki/maintenance").glob("insight-candidates-*.md"))
    if not srcs:
        print("no candidates file")
        return 2
    src = srcs[-1]
    text = src.read_text(encoding="utf-8", errors="replace")
    rows = []
    for line in text.splitlines():
        if not line.startswith("| ") or "---" in line or line.startswith("| date"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 4:
            continue
        d, snip, node, dup = parts[0], parts[1], parts[2], parts[3]
        sc = score(snip) - (2 if dup == "y" else 0)
        rows.append((sc, d, snip, node, dup))
    rows.sort(reverse=True)

    ranking = ["", "## RANKING (generated -- one-pass ratification aid)", "",
               "| rank | verdict-suggestion | candidate | node |", "|---|---|---|---|"]
    for i, (sc, d, snip, node, dup) in enumerate(rows[:20], 1):
        if dup == "y" or sc <= 0:
            sug = "reject"
        elif sc >= 3:
            sug = "PROMOTE"
        else:
            sug = "merge?"
        lines_sug = f"| {i} | {sug} | {snip[:140]} | [[{node.replace('[[','').replace(']]','')}]] |"
        ranking.append(lines_sug)

    with open(src, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(ranking) + "\n")
    print(f"ranking appended to {src.name} ({len(rows)} candidates scored)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
