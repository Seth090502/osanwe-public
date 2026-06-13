#!/usr/bin/env python3
"""
hot-md-check.py -- Schema + lifecycle invariant validator for wiki/hot.md.

Per Atlas/sources/meta/ref-hot-md-schema.md (canonical).
Invoked as PostToolUse hook on Write|Edit|MultiEdit touching wiki/hot.md.
Defense-in-depth alongside /retro Phase J.0 pre-commit gate + /vault audit
10th classifier.

Output: structured JSON to stdout. Exit code 0 on ok==true; 2 on GATE
(PostToolUse blocking semantics require exit 2 to actually block tool dispatch;
exit 1 has unspecified behavior); 2 on infrastructure error.

Bypass: env var CLAUDE_HOT_MD_BYPASS_CHECK=1 (logged to .claude/state/bypasses-<date>.log).

Severities: GATE (block commit); HARD (capped score impact -3); SOFT (-1); WARN (advisory 0); INFO.
"""

from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import os
import re
import sys
from pathlib import Path

CANONICAL_FRONTMATTER_FIELDS = {
    "categories", "type", "created", "updated", "status", "tags", "aliases", "related",
    "last_briefing", "last_audit", "last_audit_score", "last_audit_run", "last_audit_trend",
    "last_audit_milestone", "last_stats", "last_stats_calibration_score_30d",
    "last_refresh", "last_refresh_top_qualitative", "last_refresh_top_formula",
    "last_repair", "last_repair_outcome", "last_spark",
    "last_networth", "schema_version",
    # mission-tracking operational state (vault-hygiene 2026-05-29 whitelist; hot.md last_mission* fields)
    "last_mission", "last_mission_status", "last_mission_velocity_x", "last_mission_arc",
}

REQUIRED_SECTIONS = {"## Last Session", "## Pending Items", "## Active Context"}

ACTIVE_CONTEXT_V2_SUBSECTIONS = {
    "### Vault tooling state",  # legacy + retained
    "### Rebuild status",       # legacy + retained
    "### Portfolio Snapshot",   # NEW -- /networth Phase Q
    "### Active Blockers",      # NEW -- /retro+/career+/invest
    "### Watch Triggers",       # NEW -- /brief+/invest
}

LEGACY_OPERATIONAL_STATE = "### Operational state"

PENDING_ITEMS_GRANDFATHER_MARKER = "MIGRATED-AGE-PENDING"

PENDING_ITEMS_LIVE_CAP = 60
PENDING_ITEMS_COLD_CAP = 30
PENDING_ITEMS_RECENTLY_CAP = 10

STALENESS_RULES_DAYS = {
    "last_audit": (7, 30),
    "last_briefing": (2, 7),
    "last_networth": (7, 30),
}


def sha256_short(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def parse_frontmatter(content: str) -> tuple[dict, str, int]:
    """Return (frontmatter_dict, body, frontmatter_end_line)."""
    if not content.startswith("---\n"):
        return {}, content, 0
    end_match = re.search(r"\n---\n", content[4:])
    if not end_match:
        return {}, content, 0
    fm_text = content[4:4 + end_match.start()]
    body = content[4 + end_match.end():]
    fm_end_line = fm_text.count("\n") + 2
    fm = {}
    current_key = None
    for line in fm_text.split("\n"):
        if not line.strip():
            continue
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)$", line)
        if m:
            current_key = m.group(1)
            val = m.group(2).strip()
            if val == "":
                fm[current_key] = []
            elif val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                fm[current_key] = [v.strip() for v in inner.split(",") if v.strip()] if inner else []
            else:
                fm[current_key] = val
        elif line.startswith("  - ") and current_key:
            if not isinstance(fm.get(current_key), list):
                fm[current_key] = []
            fm[current_key].append(line[4:].strip().strip('"').strip("'"))
    return fm, body, fm_end_line


def get_section_ranges(content: str) -> dict[str, tuple[int, int]]:
    """Return {section_heading: (start_line, end_line_exclusive)} for top-level H2 sections."""
    lines = content.split("\n")
    ranges = {}
    current_section = None
    current_start = None
    for i, line in enumerate(lines):
        if line.startswith("## "):
            if current_section is not None:
                ranges[current_section] = (current_start, i)
            current_section = line.strip()
            current_start = i
    if current_section is not None:
        ranges[current_section] = (current_start, len(lines))
    return ranges


def section_text(content: str, start: int, end: int) -> str:
    lines = content.split("\n")
    return "\n".join(lines[start:end])


def days_since(iso_date: str) -> int | None:
    try:
        dt = datetime.date.fromisoformat(iso_date)
        return (datetime.date.today() - dt).days
    except (ValueError, TypeError):
        return None


def check_frontmatter_schema(fm: dict) -> list[dict]:
    findings = []
    present = set(fm.keys())
    rogue = present - CANONICAL_FRONTMATTER_FIELDS
    missing_critical = {"schema_version", "categories", "type", "status", "updated"} - present
    if missing_critical:
        findings.append({
            "severity": "GATE",
            "rule": "check_frontmatter_schema",
            "message": f"missing critical frontmatter fields: {sorted(missing_critical)}",
        })
    if rogue:
        findings.append({
            "severity": "HARD",
            "rule": "check_frontmatter_schema",
            "message": f"rogue frontmatter fields not in canonical schema: {sorted(rogue)}",
        })
    sv = fm.get("schema_version", "")
    if sv != "hot-md-v2":
        findings.append({
            "severity": "GATE" if sv == "" else "HARD",
            "rule": "check_frontmatter_schema",
            "message": f"schema_version must be 'hot-md-v2', got '{sv}'",
        })
    return findings


def check_section_count(content: str) -> list[dict]:
    findings = []
    last_session_headings = re.findall(r"^## Last Session.*$", content, re.MULTILINE)
    if len(last_session_headings) > 3:
        findings.append({
            "severity": "GATE",
            "rule": "check_section_count",
            "message": f"hot.md contains {len(last_session_headings)} Last Session blocks; max 3 allowed (current + Previous + Previous-Older)",
        })
    current_count = sum(1 for h in last_session_headings if h.strip() == "## Last Session")
    previous_count = sum(1 for h in last_session_headings if h.strip() == "## Last Session -- Previous")
    older_count = sum(1 for h in last_session_headings if h.strip() == "## Last Session -- Previous-Older")
    if current_count != 1:
        findings.append({
            "severity": "GATE",
            "rule": "check_section_count",
            "message": f"expected exactly 1 '## Last Session' heading, found {current_count}",
        })
    if previous_count > 1:
        findings.append({
            "severity": "GATE",
            "rule": "check_section_count",
            "message": f"expected at most 1 '## Last Session -- Previous' heading, found {previous_count}",
        })
    if older_count > 1:
        findings.append({
            "severity": "HARD",
            "rule": "check_section_count",
            "message": f"expected at most 1 '## Last Session -- Previous-Older' heading, found {older_count}",
        })
    return findings


def check_section_presence(ranges: dict) -> list[dict]:
    findings = []
    present = set(ranges.keys())
    missing = REQUIRED_SECTIONS - present
    if missing:
        findings.append({
            "severity": "GATE",
            "rule": "check_section_presence",
            "message": f"missing required sections: {sorted(missing)}",
        })
    return findings


def check_pending_items_lifecycle(content: str, ranges: dict) -> list[dict]:
    findings = []
    if "## Pending Items" not in ranges:
        return findings
    start, end = ranges["## Pending Items"]
    pending_text = section_text(content, start, end)
    grandfathered = PENDING_ITEMS_GRANDFATHER_MARKER in pending_text
    items = re.findall(r"^- \[[ xX]\] ", pending_text, re.MULTILINE)
    open_items = re.findall(r"^- \[ \] ", pending_text, re.MULTILINE)
    closed_items = re.findall(r"^- \[[xX]\] ", pending_text, re.MULTILINE)
    if len(open_items) > PENDING_ITEMS_LIVE_CAP:
        findings.append({
            "severity": "HARD",
            "rule": "check_pending_items_cap",
            "message": f"live Pending Items count {len(open_items)} exceeds cap {PENDING_ITEMS_LIVE_CAP}",
        })
    if not grandfathered:
        without_age_seed = sum(1 for line in pending_text.split("\n") if line.startswith("- [ ]") and "age_seed:" not in line)
        if without_age_seed > 0:
            findings.append({
                "severity": "HARD",
                "rule": "check_pending_items_age_seed",
                "message": f"{without_age_seed} pending items lack age_seed: marker (and no MIGRATED-AGE-PENDING grandfather banner present)",
            })
    if closed_items:
        recently_section = "## Pending Items -- Recently Completed"
        if recently_section in ranges:
            r_start, r_end = ranges[recently_section]
            recently_text = section_text(content, r_start, r_end)
            for closed in closed_items:
                idx = pending_text.find(closed)
                if idx >= 0 and pending_text[idx:idx + 200] not in recently_text:
                    findings.append({
                        "severity": "SOFT",
                        "rule": "check_pending_items_completed_pruned",
                        "message": f"completed item found in live Pending Items section; should move to Recently Completed",
                    })
                    break
    return findings


def check_active_context(content: str, ranges: dict) -> list[dict]:
    findings = []
    if "## Active Context" not in ranges:
        return findings
    start, end = ranges["## Active Context"]
    ac_text = section_text(content, start, end)
    if LEGACY_OPERATIONAL_STATE in ac_text:
        findings.append({
            "severity": "HARD",
            "rule": "check_no_operational_state",
            "message": "legacy 'Operational state' subsection found in Active Context; v2 retired this subsection",
        })
    h3_present = set(re.findall(r"^### .*$", ac_text, re.MULTILINE))
    h3_normalized = {h.split("(")[0].strip() for h in h3_present}
    expected_v2 = {h.split("(")[0].strip() for h in ACTIVE_CONTEXT_V2_SUBSECTIONS}
    missing_v2 = expected_v2 - h3_normalized
    if missing_v2 and "### Portfolio Snapshot" in missing_v2:
        findings.append({
            "severity": "SOFT",
            "rule": "check_active_context_subsections",
            "message": f"v2 Active Context missing subsection(s): {sorted(missing_v2)}",
        })
    return findings


def check_staleness(fm: dict) -> list[dict]:
    findings = []
    for field, (warn_threshold, fail_threshold) in STALENESS_RULES_DAYS.items():
        val = fm.get(field)
        if val in (None, "null", ""):
            continue
        days = days_since(str(val).strip())
        if days is None:
            continue
        if days > fail_threshold:
            findings.append({
                "severity": "SOFT",
                "rule": f"check_{field}_age",
                "message": f"{field} {val} is {days}d old (>{fail_threshold}d threshold)",
            })
        elif days > warn_threshold:
            findings.append({
                "severity": "WARN",
                "rule": f"check_{field}_age",
                "message": f"{field} {val} is {days}d old (>{warn_threshold}d threshold)",
            })
    return findings


def compute_section_sha256(content: str, ranges: dict) -> dict[str, str]:
    sha_map = {}
    for heading, (start, end) in ranges.items():
        txt = section_text(content, start, end)
        sha_map[heading.replace("## ", "").replace(" ", "_").lower()] = sha256_short(txt)
    return sha_map


def main() -> int:
    parser = argparse.ArgumentParser(description="hot.md schema + lifecycle validator")
    parser.add_argument("file", nargs="?", default="wiki/hot.md", help="path to hot.md")
    parser.add_argument("--json", action="store_true", default=True, help="JSON output (default)")
    parser.add_argument("--quiet", action="store_true", help="suppress findings unless GATE")
    args = parser.parse_args()

    if os.environ.get("CLAUDE_HOT_MD_BYPASS_CHECK") == "1":
        bypass_log = Path(".claude/state") / f"bypasses-{datetime.date.today().isoformat()}.log"
        bypass_log.parent.mkdir(parents=True, exist_ok=True)
        with bypass_log.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now().isoformat()} hot-md-check.py bypassed via CLAUDE_HOT_MD_BYPASS_CHECK=1 on {args.file}\n")
        print(json.dumps({"ok": True, "bypassed": True, "file": args.file}))
        return 0

    path = Path(args.file)
    if not path.exists():
        print(json.dumps({"ok": False, "error": f"file not found: {path}", "exit_code": 2}))
        return 2

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"read failed: {e}", "exit_code": 2}))
        return 2

    fm, body, _ = parse_frontmatter(content)
    ranges = get_section_ranges(content)

    findings = []
    findings.extend(check_frontmatter_schema(fm))
    findings.extend(check_section_count(content))
    findings.extend(check_section_presence(ranges))
    findings.extend(check_pending_items_lifecycle(content, ranges))
    findings.extend(check_active_context(content, ranges))
    findings.extend(check_staleness(fm))

    gate_count = sum(1 for f in findings if f["severity"] == "GATE")
    hard_count = sum(1 for f in findings if f["severity"] == "HARD")
    soft_count = sum(1 for f in findings if f["severity"] == "SOFT")
    warn_count = sum(1 for f in findings if f["severity"] == "WARN")
    ok = gate_count == 0

    last_session_blocks = len(re.findall(r"^## Last Session.*$", content, re.MULTILINE))
    pending_live = len(re.findall(r"^- \[ \] ", section_text(content, *ranges.get("## Pending Items", (0, 0))), re.MULTILINE)) if "## Pending Items" in ranges else 0

    output = {
        "ok": ok,
        "file": str(path),
        "section_sha256": compute_section_sha256(content, ranges),
        "findings": findings,
        "stats": {
            "last_session_blocks": last_session_blocks,
            "pending_items_live": pending_live,
            "schema_version": fm.get("schema_version", "absent"),
            "frontmatter_field_count": len(fm),
            "total_lines": content.count("\n"),
            "total_bytes": len(content.encode("utf-8")),
            "gate_count": gate_count,
            "hard_count": hard_count,
            "soft_count": soft_count,
            "warn_count": warn_count,
        },
    }
    if not args.quiet or not ok:
        print(json.dumps(output, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
