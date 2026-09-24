#!/usr/bin/env python3
"""resident-surface.py -- pre-turn instruction-surface accounting.

Computes what a session loads BEFORE the first user turn, per harness:
  Claude Code: AGENTS.md (imported by the CLAUDE.md stub) + CLAUDE.local.md size-only
               + memory MEMORY.md size + subagent descriptions + skill
               descriptions + SessionStart injection estimate.
  Hermes:      merged AGENTS.md chain + skill index estimate.
Token figure = bytes / 3.6 (mission C1 convention). Prints a table + top-5
levers; --json for machine consumption.
"""

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def size_or_none(p):
    p = ROOT / p if not Path(p).is_absolute() else Path(p)
    try:
        return os.path.getsize(p)
    except OSError:
        return None


def desc_sum(dirpath, flat=False):
    tot = n = 0
    base = ROOT / dirpath
    if not base.is_dir():
        return 0, 0
    entries = [base / f for f in os.listdir(base)
               if f.endswith(".md")] if flat else \
              [d / "SKILL.md" for d in sorted(base.iterdir()) if (d / "SKILL.md").is_file()]
    for p in entries:
        text = p.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'^description:\s*(.+(?:\n\s+.+)*)$', text[:6000], re.M)
        n += 1
        if m:
            tot += len(m.group(1).strip().encode())
    return tot, n


def hot_md_smart_emit_estimate():
    """Session-start smart emit ~ Last Session block + pending head; measured proxy."""
    p = ROOT / "wiki" / "hot.md"
    if not p.is_file():
        return 0
    text = p.read_text(encoding="utf-8", errors="replace")
    ls = re.findall(r"^## Last Session.*?(?=^## )", text, re.M | re.S)
    pend = re.search(r"^## Pending Items.*?(?=^## )", text, re.M | re.S)
    est = sum(len(b.encode()) for b in ls) + (len(pend.group(0).encode()) * 0.15 if pend else 0)
    return int(est)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = []
    def add(component, b):
        rows.append((component, b, round(b / 3.6)))

    add("AGENTS.md (root contract)", size_or_none("AGENTS.md") or 0)
    stub = size_or_none("CLAUDE.md")
    if stub:
        is_stub = (ROOT / "CLAUDE.md").read_bytes().replace(b"\r\n", b"\n") == b"@AGENTS.md\n"
        add("CLAUDE.md (stub importing AGENTS.md)" if is_stub
            else "CLAUDE.md (NOT the stub -- a second set of rules)", stub)
    cl_local = size_or_none("CLAUDE.local.md")
    if cl_local:
        add("CLAUDE.local.md (size only; contents NOT read)", cl_local)

    mem = os.environ.get("CLAUDE_MEMORY_MD")
    mem_size = size_or_none(mem) if mem else None
    if mem_size is None:
        cand = Path.home() / ".claude" / "MEMORY.md"
        mem_size = cand.stat().st_size if cand.is_file() else None
    if mem_size:
        add("Claude memory MEMORY.md (size only)", mem_size)

    sd, sn = desc_sum(".claude/agents", flat=True)
    add(f"subagent descriptions ({sn})", sd)
    kd, kn = desc_sum(".agents/skills")
    add(f"skill descriptions ({kn})", kd)
    add("hot.md smart-emit estimate (Last Session x2 + 15% Pending)", hot_md_smart_emit_estimate())
    add("BOOTSTRAP.md (Tier-C boot surface)", size_or_none("BOOTSTRAP.md") or 0)
    add(".agents/skills/AGENTS.md (nested router)", size_or_none(".agents/skills/AGENTS.md") or 0)

    total_b = sum(b for _, b, _ in rows)
    total_t = round(total_b / 3.6)
    levers = sorted(rows, key=lambda r: -r[1])[:5]

    out = {
        "generated": date.today().isoformat(),
        "rows": [{"component": c, "bytes": b, "tokens_est": t} for c, b, t in rows],
        "total_bytes": total_b,
        "total_tokens_est": total_t,
        "top_levers": [{"component": c, "bytes": b} for c, b, _ in levers],
        "notes": [
            "token figure = bytes/3.6 per mission C1",
            "*.local.md and MEMORY.md counted by SIZE ONLY (HB-04)",
            "session-start hook injections beyond hot.md estimated separately in METRICS.json",
        ],
    }
    if args.json:
        print(json.dumps(out, indent=1))
    else:
        w = max(len(c) for c, _, _ in rows)
        for c, b, t in rows:
            print(f"{c:<{w}}  {b:>8} B  ~{t:>6} tok")
        print("-" * (w + 24))
        print(f"{'TOTAL':<{w}}  {total_b:>8} B  ~{total_t:>6} tok")
        print("\ntop levers:")
        for c, b, _ in levers:
            print(f"  {b:>8} B  {c}")


if __name__ == "__main__":
    sys.exit(main())
