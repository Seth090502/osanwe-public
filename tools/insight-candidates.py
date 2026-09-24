#!/usr/bin/env python3
"""insight-candidates.py -- GAP-5: revive the insight stream.

Extracts CANDIDATE insights from session nodes (recurring patterns, explicit
"learning"/"realized"/"pattern" language) that were NOT yet captured in
wiki/insight-stream.md. Writes a candidates file for HUMAN ratification --
the insight stream is append-only and human-owned; this tool never writes it
directly. Output: wiki/maintenance/insight-candidates-<date>.md with source
node links so each candidate is traceable.
"""

import argparse
import json
import re
import sqlite3
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CUE = re.compile(
    r"(key finding|critical finding|pattern observed|learning|realized|"
    r"insight|lesson|recurred|again|same (?:mistake|error)|repeat(?:ed)?\b)"
    r"[^\n]{10,240}", re.I)


def existing_insight_texts():
    p = ROOT / "wiki/insight-stream.md"
    if not p.is_file():
        return set()
    return set(re.findall(r"\|\s*[^|]+\s*\|\s*[^|]*\|\s*([^|]{20,})\s*\|", p.read_text(encoding="utf-8", errors="replace")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-08-01")
    ap.add_argument("--out")
    args = ap.parse_args()

    existing = existing_insight_texts()
    nd = ROOT / "Calendar/sessions"
    cands = []
    for f in sorted(nd.glob("*.md")):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", f.name)
        if not m or m.group(1) < args.since:
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        for cue_m in CUE.finditer(text):
            snippet = re.sub(r"\s+", " ", cue_m.group(0)).strip()
            # skip if clearly duplicating an existing insight (crude containment)
            dup = any(snippet[15:60].lower() in e.lower() for e in existing if len(e) > 30)
            cands.append({"date": m.group(1), "node": f.stem,
                          "snippet": snippet[:230], "possible_dup": dup})
    # dedupe within run
    seen = set()
    uniq = []
    for c in cands:
        k = c["snippet"][:70].lower()
        if k not in seen:
            seen.add(k)
            uniq.append(c)

    out = Path(args.out) if args.out else (
        ROOT / "wiki/maintenance" / f"insight-candidates-{date.today().isoformat()}.md")
    lines = ["---",
             "aliases: []",
             "categories: [wiki]",
             "type: report",
             "status: draft",
             f"created: {date.today().isoformat()}",
             f"updated: {date.today().isoformat()}",
             "tags: []",
             'related: ["[[insight-stream]]"]',
             "---", "",
             "# Insight candidates (HUMAN RATIFICATION REQUIRED)", "",
             f"Extracted from session nodes since {args.since}: {len(uniq)} "
             "candidates. The insight stream is append-only + human-owned: promote "
             "a line by appending a dated row to wiki/insight-stream.md, then mark "
             "it promoted here.", "",
             "| date | candidate (cue-context) | node | dup? |", "|---|---|---|---|"]
    for c in uniq[:40]:
        lines.append(f"| {c['date']} | {c['snippet']} | [[{c['node']}]] "
                     f"| {'y' if c['possible_dup'] else 'n'} |")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"-> {out.relative_to(ROOT)} ({len(uniq)} candidates)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
