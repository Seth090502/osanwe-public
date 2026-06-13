#!/usr/bin/env python3
"""seed-commitment.py -- PostToolUse hook firing on Calendar/decisions/decision-*.md writes.

Parses YAML frontmatter for status + decision_date + domain; appends a tier-calibrated
ESCALATION_DATE entry to tomorrow's daily-note Commitments section. Idempotent dedup
via inline-HTML marker comment (re-runs no-op).

Tier mapping (user-spec defaults; calibrated 2026-05-04 per spark-2026-05-04 output --
no domain showed elevated decision-divergence severity warranting tier tightening):
  - investing -> decision_date + 3d
  - career    -> decision_date + 7d
  - skill-infra (default fallback) -> decision_date + 14d

Env vars:
  - CLAUDE_SEED_COMMITMENT_BYPASS=1   bypass the hook entirely (logs to bypasses-<date>.log)
  - BACKFILL_MODE=1                   override target daily-note from `decision_date+1d`
                                      to `today+1d` so stale-decision backfill (Phase 4.6)
                                      lands entries in operationally-visible daily notes,
                                      not past notes (user-flagged load-bearing fix).

Hook contract per existing tools/frontmatter-check.py pattern:
  stdin = JSON {"tool_input": {"file_path": "..."}, ...}
  exit 0 = pass; non-zero = block. This hook is advisory; always exits 0 unless a
  CRITICAL infrastructure error occurs.
"""
from __future__ import annotations
import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", os.getcwd()))
DAILY_DIR = VAULT_ROOT / "Calendar" / "daily"
DECISION_GLOB_RE = re.compile(r"Calendar[\\/]decisions[\\/]decision-")
TIER_DAYS = {
    "investing": 3,
    "career": 7,
    "skill-infra": 14,
    "meta": 14,
    "health": 7,
    "golf": 14,
}
DEFAULT_TIER_DAYS = 14


def log_bypass(reason: str) -> None:
    log_dir = VAULT_ROOT / ".claude" / "state"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"bypasses-{date.today().isoformat()}.log"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} seed-commitment.py BYPASS reason={reason}\n")


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    fences = [m.start() for m in re.finditer(r"^---\s*$", text, re.MULTILINE)]
    if len(fences) < 2:
        return {}
    fm_block = text[fences[0]:fences[1]]
    fm: dict = {}
    in_tags = False
    tags: list[str] = []
    for line in fm_block.splitlines():
        if not line or line.strip() == "---":
            continue
        if in_tags:
            stripped = line.strip()
            if stripped.startswith("- "):
                tags.append(stripped[2:].strip().strip('"\''))
                continue
            else:
                in_tags = False
                fm["tags"] = tags
        if ":" in line:
            k, _, v = line.partition(":")
            k = k.strip()
            v = v.strip()
            if k == "tags" and not v:
                in_tags = True
                tags = []
                continue
            fm[k] = v.strip('"\'')
    if in_tags:
        fm["tags"] = tags
    return fm


def infer_domain(fm: dict) -> str:
    tags = fm.get("tags") or []
    for t in tags:
        if t.startswith("topic/"):
            stem = t.split("/", 1)[1]
            if stem in TIER_DAYS:
                return stem
        if t.startswith("thesis/"):
            return "investing"
    cats = fm.get("categories", "")
    if "investing" in cats or "thesis" in cats:
        return "investing"
    if "career" in cats:
        return "career"
    if "skill" in cats or "meta" in cats:
        return "skill-infra"
    return "skill-infra"


def parse_iso(d: str) -> date | None:
    try:
        return datetime.strptime(d.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None


def ensure_daily_note(target_date: date) -> Path:
    """Create canonical 9-section daily note if absent; return path."""
    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    path = DAILY_DIR / f"{target_date.isoformat()}.md"
    if path.exists():
        return path
    template = f"""---
categories:
  - daily
created: {target_date.isoformat()}
updated: {target_date.isoformat()}
status: active
tags: []
related:
  - "[[hot]]"
---

# {target_date.isoformat()}

## Carried Forward

## Market Pulse

## Observations

## Decisions

## Commitments
- [ ]

## Insights

## Sessions Run

## Cross-References

## Tasks
- [ ]

## Log
"""
    path.write_text(template, encoding="utf-8")
    return path


def append_commitment(daily_path: Path, decision_slug: str, decision_date: date,
                      escalation_date: date, decision_text: str, trigger_when: str) -> bool:
    """Append commitment under ## Commitments section. Idempotent via marker.

    Returns True if appended; False if marker already present (no-op).
    """
    text = daily_path.read_text(encoding="utf-8")
    marker = f"<!-- seeded-from: {decision_slug}-{decision_date.isoformat()} -->"
    if marker in text:
        return False
    entry = (
        f"- [ ] {decision_text} {marker} "
        f"(TRIGGER: {trigger_when}; DECISION_DATE: {decision_date.isoformat()}; "
        f"ESCALATION_DATE: {escalation_date.isoformat()})"
    )
    lines = text.splitlines(keepends=False)
    out_lines: list[str] = []
    inserted = False
    in_commit_section = False
    for i, line in enumerate(lines):
        out_lines.append(line)
        if line.strip() == "## Commitments":
            in_commit_section = True
            continue
        if in_commit_section and line.startswith("## ") and line.strip() != "## Commitments":
            # Hit next section without inserting; insert before this line
            out_lines.insert(-1, entry)
            inserted = True
            in_commit_section = False
            continue
        if in_commit_section and (line.strip() == "- [ ]" or line.strip() == ""):
            # Replace empty placeholder OR insert after blank line
            if line.strip() == "- [ ]":
                out_lines[-1] = entry
                inserted = True
                in_commit_section = False
    if not inserted:
        # Fallback append at end of file
        out_lines.append("")
        out_lines.append(entry)
    daily_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return True


def main() -> int:
    if os.environ.get("CLAUDE_SEED_COMMITMENT_BYPASS") == "1":
        log_bypass("env-var")
        return 0

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # No stdin payload; not an error -- some Claude Code dispatch paths
                  # invoke hooks without payload during testing.

    file_path_str = (payload.get("tool_input") or {}).get("file_path", "")
    if not file_path_str:
        return 0
    if not DECISION_GLOB_RE.search(file_path_str):
        return 0
    file_path = Path(file_path_str)
    if not file_path.exists():
        return 0

    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError:
        return 0

    fm = parse_frontmatter(text)
    status = fm.get("status", "")
    if status not in ("active", "pending", "ratified"):
        return 0  # Decisions in non-active state don't escalate

    decision_date_str = fm.get("decision_date") or fm.get("created", "")
    decision_date = parse_iso(decision_date_str)
    if decision_date is None:
        decision_date = date.today()

    domain = infer_domain(fm)
    tier_days = TIER_DAYS.get(domain, DEFAULT_TIER_DAYS)
    escalation_date = decision_date + timedelta(days=tier_days)

    # BACKFILL_MODE env override -- decision_date is by definition old for backfill;
    # `decision_date + 1d` lands entries in past notes (zero operational value).
    # Override to today+1d so backfilled entries land in operationally-visible notes.
    if os.environ.get("BACKFILL_MODE") == "1":
        target_daily = date.today() + timedelta(days=1)
        trigger_when = (
            f"BACKFILL-MODE; original decision_date {decision_date.isoformat()}; "
            f"escalation_date {escalation_date.isoformat()}"
        )
    else:
        target_daily = decision_date + timedelta(days=1)
        trigger_when = "next-day-after-decision"

    decision_slug = file_path.stem
    daily_path = ensure_daily_note(target_daily)

    # Decision text: extract from H1 heading or first non-frontmatter line
    body = text.split("---", 2)[-1] if text.startswith("---") else text
    decision_text = decision_slug.replace("decision-", "").replace("-", " ")
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("# "):
            decision_text = s[2:].strip()
            break

    appended = append_commitment(
        daily_path, decision_slug, decision_date,
        escalation_date, decision_text, trigger_when,
    )
    if appended:
        # Diagnostic stderr-only (PostToolUse hook stdout would pollute Claude context)
        sys.stderr.write(
            f"seed-commitment: appended {decision_slug} -> {daily_path.name} "
            f"(domain={domain}, tier={tier_days}d)\n"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
