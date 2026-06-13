#!/usr/bin/env python3
"""assert-exclusions-v2.py -- L4 exclusion assertions for OsanwePublic v2.

Proves the TRACKED tree (git ls-files) contains none of the excluded classes:
  private layers, raw notes, *.local.md, runtime state, telemetry/fills/bypass
  logs, real calibration rows, real decision/sessions logs, real daily notes,
  transcripts, memory dirs, distillates, the master doc, the secrets-map
  files (live denylists / scrub spec / v1 run artifacts), and real-figure
  carriers. Synthetic DEMO seeds are asserted to be DEMO-marked.

Usage: python .audit/assert-exclusions-v2.py   (run from repo root)
Exit 0 = all assertions PASS; exit 1 = any FAIL (fail-closed).
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def tracked():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                         text=True, check=True).stdout
    return [l for l in out.splitlines() if l.strip()]


FAILS = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}: {name}" + (f" ({detail})" if detail else ""))
    if not ok:
        FAILS.append(name)


def main():
    files = tracked()

    # 1. Forbidden path prefixes (personal layers + runtime state)
    forbidden_prefixes = [
        "private/", ".raw/", "finance/", "credentials/",
        ".claude/state/", ".claude/transcripts/", ".claude/logs/",
        ".claude/worktrees/", "memory/", "Efforts/",
    ]
    for p in forbidden_prefixes:
        hits = [f for f in files if f.startswith(p)]
        check(f"no tracked files under {p}", not hits, "; ".join(hits[:3]))

    # 2. Forbidden filename patterns
    forbidden_patterns = {
        "*.local.md": re.compile(r"\.local\.md$", re.I),
        "telemetry/fills/bypass logs": re.compile(
            r"(telemetry.*\.jsonl|fills-cache|bypasses-\d{4}|\.jsonl$|command-log)", re.I),
        "transcripts": re.compile(r"transcript", re.I),
        "master doc / distillate": re.compile(r"(MASTER-CONTEXT|distillate)", re.I),
        "settings.local.json": re.compile(r"settings\.local\.json$", re.I),
    }
    for name, pat in forbidden_patterns.items():
        hits = [f for f in files if pat.search(f)]
        check(f"no tracked {name}", not hits, "; ".join(hits[:3]))

    # 3. Secrets-map files (live denylists, scrub spec, v1 run artifacts)
    secrets_map = [
        ".audit/denylist-v1.txt", ".audit/denylist-v2.txt", ".audit/denylist-v3.txt",
        ".audit/SCRUB-SPEC-v2.md", ".audit/STATUS-v2.md",
        ".audit/remediation-2026-05-11.md", ".audit/broken-links.md",
        ".audit/path-rewrites.md", ".audit/denylist-tuning.md",
        ".audit/pre-tree.txt", ".audit/post-tree.txt",
        ".audit/source-vault-head.txt", ".audit/source-vault-branch.txt",
        ".audit/source-vault-status.txt",
        ".audit/capability-baseline-pre.json", ".audit/capability-baseline-post.json",
        ".audit/test-fixture-pii.md", ".audit/transform_invest_skill.py",
        ".audit/PUBLISH-CHECKLIST.md", ".audit/MISSION-PROMPT.md",
        ".audit/PRESTAGE-MANIFEST.md",
    ]
    hits = [f for f in files if f in secrets_map]
    check("no tracked secrets-map / mission-internal .audit files", not hits,
          "; ".join(hits[:6]))

    # 4. Real-content carriers replaced by DEMO seeds
    demo_required = {
        "wiki/hot.md": "DEMO",
        "wiki/insight-stream.md": "DEMO CONTENT",
        "wiki/investing/calibration-monitor.md": "DEMO CONTENT",
        "Calendar/decisions/decision-log.md": "DEMO CONTENT",
        "Calendar/decisions/sessions-log.md": "DEMO CONTENT",
    }
    for rel, marker in demo_required.items():
        p = ROOT / rel
        if rel not in files:
            check(f"{rel} present (DEMO seed)", False, "missing from tracked tree")
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        check(f"{rel} is DEMO-marked", marker in text)

    # 5. Calibration monitor: every data row uses a -DEMO ticker
    cal = ROOT / "wiki/investing/calibration-monitor.md"
    if cal.exists():
        bad_rows = []
        for line in cal.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\|\s*\d{4}-\d{2}-\d{2}\s*\|\s*([A-Z0-9.-]+)\s*\|", line)
            if m and not m.group(1).endswith("-DEMO"):
                bad_rows.append(m.group(1))
        check("calibration-monitor rows are all -DEMO tickers", not bad_rows,
              "; ".join(bad_rows[:5]))

    # 6. Daily notes: only DEMO-marked seeds
    daily = [f for f in files if f.startswith("Calendar/daily/")]
    non_demo = [f for f in daily
                if "DEMO" not in (ROOT / f).read_text(encoding="utf-8", errors="ignore")]
    check("all tracked daily notes are DEMO-marked", not non_demo,
          "; ".join(non_demo[:3]))

    # 7. Thesis essays: only the fictional demo
    theses = [f for f in files if f.startswith("Atlas/concepts/investing/theses/")]
    check("thesis essays == [thesis-orbital-compute.md]",
          theses == ["Atlas/concepts/investing/theses/thesis-orbital-compute.md"],
          "; ".join(theses))

    # 8. No real-entity scaffold (entities limited to -DEMO stems)
    entities = [f for f in files if f.startswith("wiki/entities/")]
    bad_entities = [f for f in entities if "-DEMO.md" not in f]
    check("all tracked entities are -DEMO stems", not bad_entities,
          "; ".join(bad_entities[:5]))

    print()
    if FAILS:
        print(f"RESULT: FAIL ({len(FAILS)} assertion(s) failed)")
        return 1
    print(f"RESULT: PASS (all assertions hold across {len(files)} tracked files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
