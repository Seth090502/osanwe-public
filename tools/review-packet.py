#!/usr/bin/env python3
"""review-packet.py -- the reviewer's packet for the OSANWE-V2 branch (ADR-11).

Produces Efforts/osanwe-v2-overhaul/REVIEW-PACKET.md:
  diff --stat vs base, per-wave commit table (SHAs + subjects), metrics delta
  (METRICS.json baseline vs live), file-move table (archive INDEX summary),
  and revert guidance. This repo's PR substitute while remote-less.
"""

import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "abd86c469b60"
EFF = ROOT / "Efforts" / "osanwe-v2-overhaul"


def sh(*args):
    r = subprocess.run(list(args), cwd=str(ROOT), capture_output=True)
    return r.stdout.decode(errors="replace")


def main():
    lines = ["---",
             "aliases: [osanwe-v2-review-packet]",
             "categories: [efforts]",
             "type: report",
             "status: active",
             f"created: {date.today().isoformat()}",
             f"updated: {date.today().isoformat()}",
             "tags: [topic/meta]",
             'related: ["[[MORNING-REPORT]]", "[[INDEX]]"]',
             "---", "",
             "# REVIEW PACKET -- OSANWE-V2-2026-08",
             f"generated {date.today().isoformat()} by tools/review-packet.py", "",
             f"Base: `{BASE}` (cross-harness-migration) -> HEAD:",
             f"`{sh('git','rev-parse','--short','HEAD').strip()}` on "
             f"`{sh('git','branch','--show-current').strip()}`", "",
             "## Merge / discard",
             "",
             "```",
             "# merge (operator only):",
             "git switch cross-harness-migration && git merge --no-ff overhaul/osanwe-v2-2026-08",
             "# discard everything:",
             "git switch cross-harness-migration && git branch -D overhaul/osanwe-v2-2026-08",
             "```", "", "## Per-wave commits (revert any with git revert <sha>)", ""]
    log = sh("git", "log", "--reverse", "--format=%h|%s", f"{BASE}..HEAD")
    for row in log.strip().splitlines():
        sha, subj = row.split("|", 1)
        lines.append(f"- `{sha}` {subj}")
    lines += ["", "## Diff stat vs base (top 40)", "", "```"]
    stat = sh("git", "diff", "--stat", BASE, "HEAD").splitlines()
    lines += stat[-40:]
    lines += ["```", "", "## Metrics delta", "", "| metric | baseline | now |", "|---|---|---|"]

    import json
    m = json.loads((EFF / "METRICS.json").read_text(encoding="utf-8"))
    va_b = m["vault_audit_extract"]["score"]
    out, rc = None, None
    r = subprocess.run([sys.executable, "tools/vault-audit.py", "--json"],
                       cwd=str(ROOT), capture_output=True)
    try:
        va_n = json.loads(r.stdout.decode()).get("score")
    except Exception:
        va_n = "?"
    lines.append(f"| vault-audit score | {va_b} | {va_n} |")
    ss_b = m["resident_surface_baseline"]["components_bytes"].get("session_start_LIVE_MEASURED", 0)
    hot = (ROOT / "wiki" / "hot.md").stat().st_size
    lines.append(f"| session-start surface B | {ss_b or 'n/a'} | {hot} (hot.md component) |")
    led = m["ledgers"] if "ledgers" in m else {}
    sl = m.get("sessions_log_bytes")
    if sl:
        lines.append(f"| sessions-log monolith B | {sl} | {(ROOT/'Calendar/decisions/sessions-log.md').stat().st_size} (now generated view; nodes are truth) |")

    lines += ["", "## File moves", "",
              "Every archive move + reversal command: `_archive/2026-08-overhaul/INDEX.md`.", "",
              "## Deliberately NOT done", "",
              "- W7 full router rewrite: see MORNING-REPORT verdict section.",
              "- vault-search index rebuild: operator command shipped in report (ADR-12).",
              "- .claude-ox physical move: locked by a live process; operator action filed."]
    packet = EFF / "REVIEW-PACKET.md"
    packet.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("packet ->", packet.relative_to(ROOT), f"({packet.stat().st_size} bytes)")


if __name__ == "__main__":
    sys.exit(main())
