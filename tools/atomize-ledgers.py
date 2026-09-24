#!/usr/bin/env python3
"""atomize-ledgers.py -- split the four append-only monoliths into typed nodes.

Strangler design (mission ADR-02): every node body holds the VERBATIM original
entry text; tools/gen-ledger-views.py regenerates each ledger as header +
entries in original order, and the cutover proof is an EMPTY diff against the
original file. This tool is idempotent: running twice produces zero changes.

Modes:
  --dry-run   parse + reconcile counts only (default prints plan)
  --write     create node files + INDEX.md per ledger family
  --ledger X  restrict to one of: sessions | decisions | eod | insights
"""

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(os.environ.get("OSANWE_ATOMIZE_ROOT") or Path(__file__).resolve().parent.parent)

LEDGERS = {
    "sessions": {
        "file": "Calendar/decisions/sessions-log.md",
        "node_dir": "Calendar/sessions",
        "type": "session",
        "categories": "[decisions]",
    },
    "decisions": {
        "file": "Calendar/decisions/decision-log.md",
        "node_dir": "Calendar/decisions/records",
        "type": "decision",
        "categories": "[decisions]",
    },
    "eod": {
        "file": "Calendar/decisions/execute-or-decline.md",
        "node_dir": "Calendar/decisions/loops",
        "type": "loop",
        "categories": "[decisions]",
    },
    "insights": {
        "file": "wiki/insight-stream.md",
        "node_dir": "wiki/insights",
        "type": "insight",
        "categories": "[wiki]",
    },
}

HEADING_RE = re.compile(r"^### (\d{4}-\d{2}-\d{2}) -- (.+?)\s*$", re.M)


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


def slugify(text, maxlen=60):
    s = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return s[:maxlen].rstrip("-") or "entry"


def fm_text(categories, type_, slug_date, title, status="complete"):
    return (
        "---\n"
        "aliases: []\n"
        f"categories: {categories}\n"
        f"type: {type_}\n"
        f"status: {status}\n"
        f"created: {slug_date}\n"
        f"updated: {date.today().isoformat()}\n"
        "tags: []\n"
        "related: []\n"
        "---\n\n"
        f"# {title}\n\n"
    )


def split_headings(text):
    """Return [(mobj, entry_text)] where entry_text runs to the next ### or EOF.

    An entry BEGINS at the blank line preceding its '### ' heading when present
    (the separator byte belongs to the entry -- this keeps regeneration
    byte-identical). Legacy pipe-row regions before the first heading are
    returned as one synthetic None chunk so nothing is lost.
    """
    matches = list(HEADING_RE.finditer(text))
    if not matches:
        return []
    starts = []
    for m in matches:
        s = m.start()
        if s > 0 and text[s - 1] == "\n" and (s < 2 or text[s - 2] == "\n"):
            s -= 1  # include the blank separator line in the entry body
        starts.append(s)
    entries = []
    pre = text[: starts[0]]
    if pre.strip():
        entries.append((None, pre.rstrip() + "\n"))
    for i, m in enumerate(matches):
        end = starts[i + 1] if i + 1 < len(matches) else len(text)
        entries.append((m, text[starts[i]:end]))
    return entries


def parse_eod_rows(text):
    """EOD ledger: pipe-table rows across sections. Returns [(row_id, row_line)]."""
    rows = []
    for line in text.splitlines():
        s = line.strip()
        if not (s.startswith("|") and s.endswith("|") and "---" not in s):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells or cells[0] in ("ID", "id", "") or cells[0].startswith("**"):
            continue
        rows.append((cells[0], line))
    return rows


def parse_insight_rows(text):
    """insight-stream: one md table |Date|Domains|Insight|Status|."""
    rows = []
    for i, line in enumerate(text.splitlines()):
        s = line.strip()
        if not (s.startswith("|") and s.endswith("|") and "---" not in s):
            continue
        m = re.match(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|", s)
        if not m:
            continue
        rows.append((f"{m.group(1)}-{i:04d}", line))
    return rows


def node_name(key, m, idx):
    if key == "sessions":
        d, title = m.group(1), m.group(2)
        return f"{d}-{slugify(title, 50)}.md", d, title
    if key == "decisions":
        d, title = m.group(1), m.group(2)
        return f"{d}-{slugify(title, 50)}.md", d, title
    return None


def build_nodes(key, spec):
    text = read(spec["file"])
    nodes = []  # (filename, frontmatter_date, title, verbatim_body)
    if key in ("sessions", "decisions"):
        entries = split_headings(text)
        for n, (m, body) in enumerate(entries):
            if m is None:
                # legacy chunk stays embedded as a view-only region; the
                # generator keeps it inline so the round-trip stays byte-exact.
                continue
            _, d, title = node_name(key, m, n)
            # sequence prefix preserves DOCUMENT order under filename sort
            # (ledgers are not strictly chronological; also kills collisions)
            fname = f"{n:04d}-{d}-{slugify(title, 50)}.md"
            nodes.append((fname, d, f"{d} -- {title}", body))
    elif key == "eod":
        for n, (rid, line) in enumerate(parse_eod_rows(text)):
            fname = f"{n:04d}-{slugify(rid, 40)}.md"
            nodes.append((fname, "2026-07-04", str(rid), line + "\n"))
    elif key == "insights":
        for n, (rid, line) in enumerate(parse_insight_rows(text)):
            fname = f"{n:04d}-{rid[:10]}.md"
            nodes.append((fname, rid[:10], rid[:10], line + "\n"))
    return nodes


def write_nodes(key, spec, nodes):
    outdir = ROOT / spec["node_dir"]
    outdir.mkdir(parents=True, exist_ok=True)
    for fname, d, title, body in nodes:
        text = fm_text(spec["categories"], spec["type"], d, title) + body
        (outdir / fname).write_text(text, encoding="utf-8", newline="\n")
    index = ["---",
             "aliases: []",
             f"categories: {spec['categories']}",
             f"type: index",
             "status: active",
             f"created: {date.today().isoformat()}",
             f"updated: {date.today().isoformat()}",
             "tags: []",
             'related: []',
             "---", "",
             f"# {key} node index",
             "",
             "GENERATED by tools/atomize-ledgers.py -- one node per entry;",
             "bodies are verbatim; the ledger file remains the generated view.", ""]
    for fname, d, title, _ in nodes:
        index.append(f"- [[{fname[:-3]}]] -- {title}")
    (outdir / "INDEX.md").write_text("\n".join(index) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--ledger", choices=sorted(LEDGERS))
    args = ap.parse_args()

    report = {}
    for key, spec in LEDGERS.items():
        if args.ledger and key != args.ledger:
            continue
        nodes = build_nodes(key, spec)
        report[key] = {"entries": len(nodes), "node_dir": spec["node_dir"]}
        print(f"{key}: {len(nodes)} entries -> {spec['node_dir']}/")
        if args.write:
            write_nodes(key, spec, nodes)
    if not any(report.values()):
        print("nothing matched -- check --ledger value")

    if args.dry_run or not args.write:
        plan = ROOT / "Efforts/osanwe-v2-overhaul/_work/atomize-plan.json"
        plan.parent.mkdir(parents=True, exist_ok=True)
        plan.write_text(json.dumps(report, indent=1), encoding="utf-8")
        print("(dry-run; plan -> _work/atomize-plan.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
