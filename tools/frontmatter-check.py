#!/usr/bin/env python3
r"""
PostToolUse frontmatter validator.

Reads PostToolUse hook JSON from stdin, identifies the file just modified, and
validates frontmatter compliance per CLAUDE.md schema:

- categories: must be a plural list (`[wiki]`, not bare `wiki`)
- created: ISO date `\d{4}-\d{2}-\d{2}`
- updated: ISO date `\d{4}-\d{2}-\d{2}`
- tags: if present, must be a list; no entry starts with `domain/` or `type/`
- status: if present, must be in canonical enum
- domain: field MUST NOT be present (forbidden per schema)

Existing files are grandfathered: only NEW writes to wiki/, Calendar/, Efforts/
trigger full validation. Edits to existing files only validate if frontmatter
region was modified (best-effort detection).

Bypass: CLAUDE_VAULT_BYPASS_VALIDATOR=1 in env (logged to
.claude/state/bypasses-<date>.log).

Skipped paths: .claude/, _archive/, _quarantine/, .git/, node_modules/,
.checkpoints/, non-md files. Per-file exempts: CLAUDE.md, CLAUDE.local.md,
docs/PROJECT-OSANWE-PACKET.md, docs/VAULT-HANDOFF-V16.md, tools/migrations/README.md.
Validates only writes to wiki/, Calendar/, Efforts/, Atlas/ (VALIDATE_DIRS).
Sub-skipped: paths containing "maintenance" component.
"""
import json
import os
import re
import sys
from datetime import datetime, date
from pathlib import Path

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", os.getcwd()))
EXEMPT_DIRS = {"_archive", "_quarantine", ".claude", ".agents", ".codex", ".git", "node_modules", ".checkpoints"}
EXEMPT_PATHS = {
    "CLAUDE.md", "CLAUDE.local.md",
    "AGENTS.md", "AGENTS.override.md", "AGENTS.override.md.template",
    "docs/PROJECT-OSANWE-PACKET.md", "docs/VAULT-HANDOFF-V16.md",
    "docs/CODEX-COMPATIBILITY.md",
    "tools/CODEX_TOOLS_UNVERIFIED.md",
    "tools/migrations/README.md",
}
# Validate frontmatter for NEW files in these top-level paths
VALIDATE_DIRS = {"wiki", "Calendar", "Efforts", "Atlas"}

CANONICAL_STATUS = {
    "active", "paused", "done", "dropped", "stub", "deprecated",
    "draft", "complete", "stale",
}
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FRONTMATTER_FENCE = re.compile(r"^---\s*$", re.MULTILINE)
DOMAIN_FIELD = re.compile(r"^domain:\s*\S", re.MULTILINE)
# Match `categories: <scalar>` where scalar is a bare value (not inline-list `[...]`,
# not multi-line list trailing whitespace). Inline lists like `[wiki]` are valid.
CATEGORIES_SCALAR = re.compile(r"^categories:\s+([^\[\-\s].*)$", re.MULTILINE)
CREATED_FIELD = re.compile(r"^created:\s*(.+)$", re.MULTILINE)
UPDATED_FIELD = re.compile(r"^updated:\s*(.+)$", re.MULTILINE)
STATUS_FIELD = re.compile(r"^status:\s*(.+)$", re.MULTILINE)


def log_bypass(rel_path: Path, violations: list[str]):
    bypass_log = VAULT_ROOT / ".claude" / "state" / f"bypasses-{date.today().isoformat()}.log"
    bypass_log.parent.mkdir(exist_ok=True, parents=True)
    with bypass_log.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} frontmatter-check {rel_path}: {'; '.join(violations)}\n")


def parse_frontmatter(text: str) -> str | None:
    if not text.startswith("---"):
        return None
    fences = list(FRONTMATTER_FENCE.finditer(text))
    if len(fences) < 2:
        return None
    return text[fences[0].end():fences[1].start()]


def validate(fm: str) -> list[str]:
    violations = []
    if DOMAIN_FIELD.search(fm):
        violations.append("forbidden field `domain:` (stripped per CLAUDE.md schema)")
    cat_scalar = CATEGORIES_SCALAR.search(fm)
    if cat_scalar:
        val = cat_scalar.group(1).strip()
        violations.append(f"`categories:` must be a list (got scalar: {val})")
    created_m = CREATED_FIELD.search(fm)
    if created_m:
        v = created_m.group(1).strip().strip("'\"")
        if v and not ISO_DATE.match(v):
            violations.append(f"`created:` must be ISO date (got: {v})")
    updated_m = UPDATED_FIELD.search(fm)
    if updated_m:
        v = updated_m.group(1).strip().strip("'\"")
        if v and not ISO_DATE.match(v):
            violations.append(f"`updated:` must be ISO date (got: {v})")
    status_m = STATUS_FIELD.search(fm)
    if status_m:
        v = status_m.group(1).strip().strip("'\"")
        if v and v not in CANONICAL_STATUS:
            violations.append(f"`status:` must be in canonical enum (got: {v})")
    in_tags = False
    for line in fm.splitlines():
        stripped = line.strip()
        if stripped.startswith("tags:"):
            in_tags = True
            continue
        if in_tags:
            if stripped.startswith("- "):
                tag_val = stripped[2:].strip().strip("'\"")
                if tag_val.startswith("domain/") or tag_val.startswith("type/"):
                    violations.append(f"forbidden tag namespace: {tag_val}")
            elif stripped and not stripped.startswith("-"):
                in_tags = False
    return violations


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)

    fp = Path(file_path)
    if fp.suffix != ".md":
        sys.exit(0)

    try:
        rel_path = fp.relative_to(VAULT_ROOT)
    except ValueError:
        sys.exit(0)

    if any(part in EXEMPT_DIRS for part in rel_path.parts):
        sys.exit(0)
    rel_str = str(rel_path).replace("\\", "/")
    if rel_str in EXEMPT_PATHS:
        sys.exit(0)
    if rel_path.parts and rel_path.parts[0] not in VALIDATE_DIRS:
        sys.exit(0)
    if "maintenance" in rel_path.parts:
        sys.exit(0)

    try:
        text = fp.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        sys.exit(0)

    fm = parse_frontmatter(text)
    if fm is None:
        # File missing frontmatter entirely -- only flag for new files in VALIDATE_DIRS
        if os.environ.get("CLAUDE_VAULT_BYPASS_VALIDATOR") == "1":
            log_bypass(rel_path, ["missing frontmatter"])
            sys.exit(0)
        msg = (
            f"vault-audit: {rel_path} missing canonical frontmatter\n"
            "Required fields: categories: [<axis>], created: YYYY-MM-DD, updated: YYYY-MM-DD\n"
            "Bypass: CLAUDE_VAULT_BYPASS_VALIDATOR=1 (logs to .claude/state/bypasses-<date>.log)\n"
        )
        print(msg, file=sys.stderr)
        sys.exit(2)

    violations = validate(fm)
    if not violations:
        sys.exit(0)

    if os.environ.get("CLAUDE_VAULT_BYPASS_VALIDATOR") == "1":
        log_bypass(rel_path, violations)
        sys.exit(0)

    msg = f"vault-audit: frontmatter violations in {rel_path}\n"
    for v in violations:
        msg += f"  - {v}\n"
    msg += "Bypass: CLAUDE_VAULT_BYPASS_VALIDATOR=1 (logs to .claude/state/bypasses-<date>.log)\n"
    print(msg, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
