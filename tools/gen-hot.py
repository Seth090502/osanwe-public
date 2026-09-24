#!/usr/bin/env python3
"""gen-hot.py -- generate wiki/hot.md as a lean working-set cache (ADR-02/SOTA-6).

Sources of truth consumed: latest Calendar/sessions/*.md node (by sequence
prefix), Calendar/decisions/loops/*.md open-loop nodes, git status.
Output: wiki/hot.md <= 8,000 bytes emitting every section tools/hot-md-check.py
REQUIRES ('## Last Session', '## Pending Items', '## Active Context').
The previous hand-curated hot.md is preserved at
_archive/2026-08-overhaul/hot-md-hand-curated-pre-gen.md before first write.
"""

import argparse
import importlib.util
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(os.environ.get("OSANWE_ATOMIZE_ROOT")
            or Path(__file__).resolve().parent.parent)

REQUIRED = ("## Last Session", "## Pending Items", "## Active Context")
BUDGET = 8000


def latest_session_node():
    d = ROOT / "Calendar" / "sessions"
    files = sorted(f for f in d.glob("*.md") if f.name != "INDEX.md") if d.is_dir() else []
    return files[-1] if files else None


def body_after_fm(p):
    parts = p.read_text(encoding="utf-8", errors="replace").split("---\n", 2)
    return parts[2] if len(parts) == 3 else ""


def field(body, label):
    m = re.search(r"^(?:\*\*)?" + re.escape(label) + r":(?:\*\*)?[ \t]*(.+)$", body, re.M)
    return m.group(1).strip() if m else None


def section(body, name):
    m = re.search(r"^" + re.escape(name) + r"\s*$(.*?)(?=^### |^## |\Z)", body, re.M | re.S)
    return m.group(1).strip() if m else ""


def open_loops(limit=10):
    """Reuse the resolution-aware authority instead of reopening closed nodes."""
    path = Path(__file__).resolve().with_name("open-loops.py")
    spec = importlib.util.spec_from_file_location("hot_open_loops", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.EXEC_LEDGER = ROOT / "Calendar/decisions/execute-or-decline.md"
    return sorted(module.scan_exec_or_decline(date.today()), reverse=True)[:limit]


def git_status_lines(n=8):
    try:
        result = subprocess.run(["git", "status", "--short"], cwd=str(ROOT),
                                capture_output=True, text=True, timeout=15)
        if result.returncode:
            return [], "UNVERIFIED"
        lines = [l for l in result.stdout.splitlines() if l.strip()]
        return lines[:n], len(lines)
    except Exception:
        return [], "UNVERIFIED"


def build():
    ls_node = latest_session_node()
    last_session = "(no session node found)"
    active_context = []
    body = ""
    if ls_node:
        body = body_after_fm(ls_node)
        title = field(body, "Domain")
        bluf = field(body, "BLUF") or field(body, "Focus") or ""
        artifact = field(body, "Artifact") or ""
        conf = field(body, "Confidence") or ""
        stamp = re.search(r"\d{4}-\d{2}-\d{2}", ls_node.name)
        when = stamp.group() if stamp else "unknown"
        last_session = (
            f"- **Date:** {when} -- see [[{ls_node.stem}]]\n"
            f"- **BLUF:** {bluf[:600]}\n"
            f"- **Confidence:** {conf}\n"
            f"- **Artifact:** {artifact}\n"
        ).strip()
        for kw in ("Notable:", "Thesis shifts:", "Followup skills:"):
            v = field(body, kw.rstrip(":"))
            if v:
                active_context.append(f"- {kw} {v[:220]}")

    loops = open_loops()
    pending = ["- " + summary.rstrip() for _, _, summary in loops]
    total_open = len(loops)

    blockers = [f"- {w.rstrip()}" for _, _, w in loops[:3]]
    watch = []
    for w in [x for x in re.split(r";\s*", field(body, "Thesis shifts") or "") if x]:
        watch.append(f"- {w[:180]}")

    glines, gcount = git_status_lines()

    out = ["---",
           "aliases: [session cache, hot]",
           "categories: [wiki]",
           "type: synthesis",
           "status: active",
           "schema_version: hot-md-v2",
           f"created: {date.today().isoformat()}",
           f"updated: {date.today().isoformat()}",
           "tags: []",
           'related: ["[[sessions-log]]", "[[execute-or-decline]]"]',
           "---", "",
           "# Session Cache",
           "",
           "GENERATED cache; session nodes + resolution-aware action ledger. Verify current state before acting.",
           "",
           "## Last Session",
           last_session, "",
           f"## Pending Items",
           "(top {n} overdue actions; full digest: tools/open-loops.py)".format(n=len(pending))]
    out += (pending or ["- (none parsed)"])
    out += ["", "## Active Context",
            "### Vault tooling state",
            "- UNVERIFIED in this cache; run python .agents/scripts/checkall.py and tools/vault-score-check.py",
            "### Rebuild status",
            "- Current authority: [[STATE]] at Efforts/osanwe-v2-overhaul/STATE.md; old wave reports are historical",
            "### Portfolio Snapshot",
            "- (networth runs write snapshots to wiki/investing/snapshots/; not generated here)",
            "### Active Blockers"]
    out += blockers or ["- (none parsed)"]
    out += ["### Watch Triggers"]
    out += watch or ["- (none surfaced by latest session node)"]
    out += ["", "## Working Tree",
            f"- git status: {gcount} entr(ies)" + (":" if glines else "")]
    out += [f"  {l}" for l in glines]
    text = "\n".join(out) + "\n"
    if len(text.encode()) > BUDGET:
        # trim Pending Items hardest -- the full set lives in loop nodes anyway
        keep = max(3, len(pending) // 2)
        out2 = []
        skipped = False
        for line in out:
            if line.startswith("- EXEC-OR-DECLINE"):
                if not skipped and keep <= 0:
                    out2.append("- (... older loops live in Calendar/decisions/loops/)")
                    skipped = True
                if keep > 0:
                    out2.append(line)
                    keep -= 1
            else:
                out2.append(line)
        text = "\n".join(out2) + "\n"
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write wiki/hot.md (backs up hand-curated original on first run)")
    args = ap.parse_args()
    text = build()
    print(f"generated hot.md: {len(text.encode())} bytes (budget {BUDGET})")
    missing = [s for s in REQUIRED if s not in text]
    if missing:
        print("MISSING REQUIRED SECTIONS:", missing)
        return 2
    if args.apply:
        hot = ROOT / "wiki" / "hot.md"
        backup = ROOT / "_archive" / "2026-08-overhaul" / "hot-md-hand-curated-pre-gen.md"
        if hot.exists() and not backup.exists():
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_text(hot.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
            print("hand-curated original preserved ->", backup.relative_to(ROOT))
        hot.write_text(text, encoding="utf-8", newline="\n")
        print("written ->", hot.relative_to(ROOT))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
