#!/usr/bin/env python3
"""
hot-md-emit-smart.py -- Smart-emit helper for SessionStart hook.

When wiki/hot.md exceeds the SessionStart context budget (default 8KB),
emit a priority-ordered subset that preserves the highest-leverage continuity
content while skipping bulk archive content (Last Session -- Previous /
Previous-Older blocks live in Calendar/decisions/sessions-log.md anyway).

Priority order (per ref-hot-md-schema sec 6):
  1. Always full: frontmatter (24 fields).
  2. Always full: ## Last Session block.
  3. Always full: ## Active Context (all subsections).
  4. Pending Items: 1-line stats banner + first N=15 active items + full
     Recently Completed buffer.
  5. Skip: ## Last Session -- Previous and Previous-Older blocks.
  6. Always: Related: footer.

Output to stdout. Exit code 0 on success; 1 on parse failure (caller falls
back to cat).
"""

from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

DEFAULT_MAX_BYTES = 8192
PENDING_ITEMS_TOP_N = 15


def get_section_ranges(content: str) -> dict[str, tuple[int, int]]:
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


def emit_pending_items_summary(pending_text: str) -> str:
    open_items = re.findall(r"^- \[ \] .*$", pending_text, re.MULTILINE)
    closed_items = re.findall(r"^- \[[xX]\] .*$", pending_text, re.MULTILINE)
    grandfathered = "MIGRATED-AGE-PENDING" in pending_text
    age_marker = "MIGRATED-AGE" if grandfathered else "v2-age-seed"
    summary = (
        f"## Pending Items\n"
        f"> [smart-emit] live={len(open_items)} closed={len(closed_items)} mode={age_marker}; full list in wiki/hot.md\n"
    )
    summary += "\n".join(open_items[:PENDING_ITEMS_TOP_N])
    if len(open_items) > PENDING_ITEMS_TOP_N:
        summary += f"\n> ... ({len(open_items) - PENDING_ITEMS_TOP_N} more pending items omitted; see wiki/hot.md)"
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="hot.md smart-emit helper")
    parser.add_argument("--input", required=True, help="path to hot.md")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES, help="target output byte budget")
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"hot-md-emit-smart: file not found: {path}", file=sys.stderr)
        return 1

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"hot-md-emit-smart: read failed: {e}", file=sys.stderr)
        return 1

    # Frontmatter (always full)
    fm_match = re.match(r"^(---\n.*?\n---\n)", content, re.DOTALL)
    frontmatter = fm_match.group(1) if fm_match else ""

    ranges = get_section_ranges(content)

    parts = [frontmatter.rstrip()]
    parts.append("\n# Session Cache\n")

    if "## Last Session" in ranges:
        s, e = ranges["## Last Session"]
        parts.append(section_text(content, s, e).rstrip())

    if "## Last Session -- Previous" in ranges:
        s_p, e_p = ranges["## Last Session -- Previous"]
        date_match = re.search(r"^\- \*\*Date:\*\* (.+)$", section_text(content, s_p, e_p), re.MULTILINE)
        date_hint = date_match.group(1)[:80] if date_match else "see sessions-log"
        parts.append(f"## Last Session -- Previous (skipped; see Calendar/decisions/sessions-log.md)\n> {date_hint}")

    if "## Last Session -- Previous-Older" in ranges:
        parts.append("## Last Session -- Previous-Older (skipped; see Calendar/decisions/sessions-log.md)")

    if "## Pending Items" in ranges:
        s, e = ranges["## Pending Items"]
        parts.append(emit_pending_items_summary(section_text(content, s, e)))

    if "## Pending Items -- Recently Completed" in ranges:
        s, e = ranges["## Pending Items -- Recently Completed"]
        parts.append(section_text(content, s, e).rstrip())

    if "## Active Context" in ranges:
        s, e = ranges["## Active Context"]
        parts.append(section_text(content, s, e).rstrip())

    related_match = re.search(r"\n(Related:.*)$", content, re.DOTALL)
    if related_match:
        parts.append(related_match.group(1).rstrip())

    output = "\n\n".join(parts) + "\n"
    output_bytes = len(output.encode("utf-8"))
    if output_bytes > args.max_bytes:
        print(f"# hot-md-emit-smart: output {output_bytes} bytes still exceeds budget {args.max_bytes}; emitting anyway", file=sys.stderr)

    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
