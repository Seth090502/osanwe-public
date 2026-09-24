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
  3. ## Active Context: all subsections when they fit; under budget pressure the
     NEWEST subsection is kept full and older ones are elided to their heading +
     a pointer (shrink rung 3, added 2026-08-13 -- Active Context was 77.5% of
     the emit with no shrink path, making the budget unreachable by construction).
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

    def _msys_to_win(p):
        # Git-Bash callers pass /path/to/vault/... which Windows Python cannot
        # resolve; translate the drive-letter form so smart-emit never silently
        # falls back to raw injection (root-caused 2026-08-23, OSANWE-V2).
        if len(p) >= 3 and p[0] == "/" and p[2] == "/":
            return p[1].upper() + ":" + p[2:]
        return p

    args = parser.parse_args()
    path = Path(_msys_to_win(args.input))
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

    # Honest-emit fix (TENFOLD T2, X22p): if the priority subset still exceeds
    # the budget, actually shrink it (drop Recently Completed, then halve the
    # pending top-N) instead of silently emitting an oversized payload. The
    # emitted banner always reports REAL byte counts so the SessionStart log
    # can never claim a compression that did not happen.
    if output_bytes > args.max_bytes:
        parts = [p for p in parts if not p.startswith("## Pending Items -- Recently Completed")]
        output = "\n\n".join(parts) + "\n"
        output_bytes = len(output.encode("utf-8"))
    while output_bytes > args.max_bytes:      # halve toward the 3-item floor (2026-08-13:
        changed = False                       # single-shot halving left 7 oversized items)
        for i, p in enumerate(parts):
            if p.startswith("## Pending Items"):
                kept = p.split("\n")
                head = kept[:2]  # heading + stats banner
                items = [l for l in kept[2:] if l.startswith("- [ ]")]
                n = max(len(items) // 2, 3)
                if n < len(items):
                    parts[i] = "\n".join(head + items[:n] + [f"> ... ({len(items) - n} more omitted for budget; see wiki/hot.md)"])
                    changed = True
                break
        if not changed:
            break
        output = "\n\n".join(parts) + "\n"
        output_bytes = len(output.encode("utf-8"))
    # Rung 3 (2026-08-13): elide Active Context. Keep the newest subsection full
    # (it describes the immediately-previous session); older subsections collapse
    # to their heading + a pointer. Their full text survives in wiki/hot.md and
    # the narrative also lives in sessions-log -- the emit is a cache view, not
    # the record. Without this rung the budget was unreachable by construction
    # (Active Context alone was ~30KB against an 8KB budget) and every compaction
    # re-injected the overage.
    if output_bytes > args.max_bytes:
        for i, p in enumerate(parts):
            if p.startswith("## Active Context"):
                blocks = re.split(r"\n(?=### )", p)
                if len(blocks) > 2:
                    kept = blocks[:2]  # section header + newest subsection
                    elided = [b.split("\n", 1)[0] + " (elided for budget; full text in wiki/hot.md)"
                              for b in blocks[2:]]
                    parts[i] = "\n".join(kept + elided)
                break
        output = "\n\n".join(parts) + "\n"
        output_bytes = len(output.encode("utf-8"))

    raw_bytes = len(content.encode("utf-8"))
    over = "; OVER BUDGET (shrink exhausted)" if output_bytes > args.max_bytes else ""
    banner = f"> [smart-emit] emitted {output_bytes} bytes (raw {raw_bytes}, budget {args.max_bytes}){over}\n"
    sys.stdout.write(banner + output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
