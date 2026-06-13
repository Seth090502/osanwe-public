#!/usr/bin/env python3
r"""
vault-audit.py -- Comprehensive Obsidian vault integrity audit.

Scans all .md files in <VAULT_ROOT>\ and outputs a structured markdown report
covering wikilink integrity, orphan detection, frontmatter validation, staleness,
and MOC completeness.

v2.1 (2026-04-26): false-positive class filtering
 - Index .claude/skills/*/ref-*.md as wikilink-resolution targets (skill-companion refs)
 - Add .base extension support (Obsidian Bases query files)
 - Filter <placeholder>-style template syntax (<TICKER>, ..., X, note-name, Alice, wikilinks, links)
 - Exclude wiki/maintenance/ from broken-wikilink reporting (audit/repair reports quote examples)
 - Strip path prefixes from wikilinks (e.g., [[wiki/X/Y/file]] -> resolve "file")
 - Strip .md extension and trailing backslash artifacts
 - FRONTMATTER_EXEMPT_PATHS for institutional-history and tool docs
 - Extended ORPHAN_EXCLUDES for _quarantine, applications/, prompts/, _templates, daily

v2.1.1 (2026-04-27): prevention architecture Phase 2 false-positive filters
 - Extended PLACEHOLDER_PATTERN with bash/shell construct alternatives (\$, !, ?, *)
 - Code-fence-aware extraction: skip wikilinks inside ``` fenced code blocks
 - Inline-backtick-aware extraction: skip wikilinks inside `inline code` spans
 - Bash double-bracket detection: filter [[$X-Y-Z...]] patterns from shell test constructs
 - MEMORY_PREFIXES exemption: [[memory:...]] and [[feedback_...]] resolve as auto-memory refs
 - FORBIDDEN_FRONTMATTER_FIELDS detector: surface domain: field as classifier-6 finding
 - --scope <path>: restrict scan to one file or subtree (incremental mode for hooks)
 - --changed-only: scan only files modified vs HEAD (for PostToolUse efficiency)
 - --quick: skip orphan + MOC scans (run only 4 cheap CRITICAL classifiers; <500ms target)
 - --json: emit findings as JSON for hook consumption
 - WIKILINK_SCAN_EXEMPT_PATHS: per-file exemptions for prevention-architecture-style docs

Usage:
    python <VAULT_ROOT>/tools/vault-audit.py
    python <VAULT_ROOT>/tools/vault-audit.py --scope wiki/research/foo.md --quick
    python <VAULT_ROOT>/tools/vault-audit.py --changed-only --json
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime, date

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", os.getcwd()))

# Directories to exclude from all scans
GLOBAL_EXCLUDES = {
    "node_modules",
    ".git",
    ".checkpoints",
    ".obsidian",
    ".smart-env",
    ".claude",
    ".agents",   # Mission Four: Codex skills mirror (synced from .claude/skills/; not vault content)
    ".codex",    # Mission Four: Codex agents/config/hooks artifacts (TOML; not vault content)
}

# Additional excludes for orphan detection (files here aren't expected to have backlinks)
ORPHAN_EXCLUDES = {
    "templates",
    ".checkpoints",
    "node_modules",
    "career-ops",
    "_templates",     # canonical pluralized form
    "_quarantine",    # quarantined examples
    "applications",   # career packet sub-files (only parent application file is linked)
    "prompts",        # wiki/research/prompts/ -- Pattern 21 retained-prompt archive
    "daily",          # Calendar/daily/ ephemeral session notes
    "private",        # gitignored personal data; not expected to have public back-links
    "challenges",     # wiki/research/challenges/ -- dated challenge artifacts, often standalone
}

# Additional excludes for frontmatter validation
FRONTMATTER_EXCLUDES = {
    "node_modules",
    "career-ops",
}

# By-design exempt files (specific paths, not directory names)
# These are institutional-history docs and tool documentation that intentionally
# lack vault frontmatter (they're not queryable notes; they're orientation/handoff/tool docs).
FRONTMATTER_EXEMPT_PATHS = {
    "CLAUDE.md",
    "CLAUDE.local.md",
    "AGENTS.md",
    "AGENTS.override.md",
    "AGENTS.override.md.template",
    "docs/PROJECT-OSANWE-PACKET.md",
    "docs/VAULT-HANDOFF-V16.md",
    "docs/CODEX-COMPATIBILITY.md",
    "docs/fs-watcher.md",
    "docs/gpg-recovery-setup.md",
    "tools/CODEX_TOOLS_UNVERIFIED.md",
    "tools/migrations/README.md",
    "tools/migrations/group-30-verification-report.md",
}

# By-design exempt orphans (specific paths). These are root-level config/docs/tool-output
# that are not vault entities and are not expected to have inbound wikilinks.
ORPHAN_EXEMPT_PATHS = {
    "CLAUDE.local.md",
    "AGENTS.md",
    "AGENTS.override.md",
    "AGENTS.override.md.template",
    "docs/PROJECT-OSANWE-PACKET.md",
    "docs/VAULT-HANDOFF-V16.md",
    "docs/CODEX-COMPATIBILITY.md",
    "docs/fs-watcher.md",
    "docs/gpg-recovery-setup.md",
    "tools/CODEX_TOOLS_UNVERIFIED.md",
    "tools/migrations/group-30-verification-report.md",
}

# Files where wikilinks are documentation/quoted-examples, not live references.
# wiki/maintenance/ audit and repair reports quote broken wikilinks for documentation;
# the script cannot distinguish documentation from live usage, so exclude entirely.
WIKILINK_SCAN_EXCLUDES = {
    "maintenance",
}

# Per-file exemptions for prevention-architecture-style docs that legitimately
# discuss broken-wikilink classes in prose. Same principle as WIKILINK_SCAN_EXCLUDES
# but path-specific rather than directory-wide.
WIKILINK_SCAN_EXEMPT_PATHS = {
    "wiki/research/vault-prevention-architecture-2026-04-27.md",
}

# Auto-memory wikilink prefixes (legacy; Claude Code memory files live at
# ~/.claude/projects/<proj>/memory/<stem>.md, outside the vault root).
# Retained as fallback in case the dynamic check fails. Canonical grammar is
# [[memory:<stem>]] which is always exempt; legacy prefixes were observed across
# project_*, reference_*, research_*, feedback_*, user_*, auto_*, MEMORY itself.
MEMORY_PREFIXES = (
    "memory/", "memory:",
    "feedback_", "auto_", "user_",
    "project_", "reference_", "research_",
)


def collect_memory_stems() -> set[str]:
    """Dynamically discover Claude Code auto-memory file stems for wikilink exemption.

    Memory files live at ~/.claude/projects/<proj>/memory/<stem>.md. Returns a
    lowercased set of stems for set-membership exemption check. Robust to new
    memory categories. Silent fail returns empty set; static MEMORY_PREFIXES
    tuple still applies as fallback prefix-match.
    """
    stems: set[str] = set()
    try:
        home = Path.home()
        # Iterate over all project memory dirs (multi-project safety)
        for project_dir in (home / ".claude" / "projects").glob("*"):
            memory_dir = project_dir / "memory"
            if memory_dir.exists():
                for f in memory_dir.glob("*.md"):
                    stems.add(f.stem.lower())
    except (OSError, PermissionError):
        pass
    return stems

# Forbidden frontmatter fields per CLAUDE.md schema (sec "Frontmatter schema").
FORBIDDEN_FRONTMATTER_FIELDS = {"domain"}
FORBIDDEN_TAG_NAMESPACES = ("domain/", "type/")

WIKILINK_PATTERN = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]+)?\]\]")
FRONTMATTER_FENCE = re.compile(r"^---\s*$", re.MULTILINE)
UPDATED_FIELD = re.compile(r"^updated:\s*(.+)$", re.MULTILINE)
DOMAIN_FIELD = re.compile(r"^domain:\s*\S", re.MULTILINE)
# Fence open detection: triple-backtick at column 0 OR with up to 3 leading spaces
# (CommonMark allows up to 3 spaces of indentation before fence open).
FENCE_OPEN = re.compile(r"^ {0,3}```")
# Inline code: balanced backtick pairs only
INLINE_CODE = re.compile(r"`[^`]*`")
# Indented code block (4-space indent at line start); also skips wikilinks inside
INDENTED_CODE = re.compile(r"^    \S")

# Placeholder/example wikilink syntax that should NEVER resolve.
# Matches: <TICKER>, <ticker>-analysis-<date>, <source-stem>, <stem>, ...,
#          X, note-name, Alice, wikilinks, links, plus shell constructs.
PLACEHOLDER_PATTERN = re.compile(
    r"^[<.][\.\w<>-]*[>.]$"      # angle-bracket templates: <X>, <X-Y-Z>, <...>
    r"|^\.\.\.$"                  # bare ellipsis
    r"|^X$"                       # bare X
    r"|^note-name$"               # generic note-name placeholder
    r"|^Alice$"                   # quarantined example
    r"|^wikilinks$|^links$"       # quarantined example syntax
    r"|^\$.*"                     # bash code fragments: [[$- == *i*]] etc.
    r"|^!.*"                      # negation/shell-history: [[!cmd]]
    r"|^[?*].*"                   # shell glob fragments
)

# Bash double-bracket test construct fragments (defense-in-depth for [[$- == *i*]]).
BASH_BRACKETS = re.compile(r"^\$[-_a-zA-Z]")

STALE_THRESHOLD_DAYS = 30

# X2 (audit 2026-04-28): mechanical body-length cap per CLAUDE.md sec 4 guideline.
# Set to 900 (above the largest current skill /brief at 824) so legitimate complex
# skills do not trigger HARD DRIFT. The kepano + Anthropic skill-creator 263-line
# guidance remains aspirational; real institutional-grade skills with multi-phase
# workflows + canonical schemas legitimately exceed it. Cap-as-warning fires only
# when a skill has clearly grown unbounded (>900 lines suggests genuine bloat
# warranting refactor decision; <=900 is operational reality).
SKILL_BODY_LENGTH_CAP = 900

# X8 provenance classifier cutoff (invest vNEXT 2026-06-09). Analyses with
# frontmatter created: BEFORE this date are structurally exempt -- the ~65
# legacy analyses predate the prov: field and must NEVER be retro-flagged
# (by-design-historical content; flooding findings would train alert-blindness).
PROVENANCE_MIGRATION_CUTOFF = date(2026, 6, 10)


def should_exclude(filepath: Path, extra_excludes: set | None = None) -> bool:
    """Check if a file falls under any excluded directory."""
    excludes = GLOBAL_EXCLUDES | (extra_excludes or set())
    parts = filepath.relative_to(VAULT_ROOT).parts
    return any(part in excludes for part in parts)


def collect_md_files() -> list[Path]:
    """Collect all .md files in the vault, respecting global excludes."""
    files = []
    for f in VAULT_ROOT.rglob("*.md"):
        if not should_exclude(f):
            files.append(f)
    return sorted(files)


def collect_skill_companion_refs() -> list[Path]:
    """Collect .claude/skills/*/ref-*.md files for wikilink-resolution-only indexing.

    These are referenceable from vault content (e.g., 'related: ref-application-mechanics')
    but should NOT be audited for frontmatter, orphan status, or staleness.
    """
    refs = []
    skills_dir = VAULT_ROOT / ".claude" / "skills"
    if skills_dir.exists():
        for f in skills_dir.glob("*/ref-*.md"):
            refs.append(f)
    return sorted(refs)


def collect_base_files() -> list[Path]:
    """Collect .base files (Obsidian Bases query files) as valid wikilink targets.

    These live in wiki/meta/ and elsewhere; they're valid Obsidian targets but the
    script's primary glob is .md so they need explicit indexing.
    """
    bases = []
    for f in VAULT_ROOT.rglob("*.base"):
        if not should_exclude(f):
            bases.append(f)
    return sorted(bases)


def read_file(filepath: Path) -> str | None:
    """Read a file with BOM-safe encoding. Returns None on failure."""
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return filepath.read_text(encoding=enc)
        except (UnicodeDecodeError, OSError):
            continue
    return None


def build_filename_index(
    files: list[Path],
    extra_resolution_targets: list[Path] | None = None,
) -> dict[str, Path]:
    """Map lowercase filename (no extension) -> Path for wikilink resolution.

    extra_resolution_targets: additional files to index for resolution but not audit
    (e.g., .claude/skills/*/ref-*.md skill-companion refs and .base files).
    """
    index: dict[str, Path] = {}
    for f in files:
        key = f.stem.lower()
        # First file wins; duplicates are a separate concern
        if key not in index:
            index[key] = f
    if extra_resolution_targets:
        for f in extra_resolution_targets:
            key = f.stem.lower()
            if key not in index:
                index[key] = f
    return index


def extract_wikilinks(text: str) -> list[tuple[int, str]]:
    """Return list of (line_number, link_target) for all wikilinks in text.

    v2.1.1: Code-fence-aware (skips inside ``` fenced blocks); inline-backtick-aware
    (skips wikilinks inside `inline code` spans); MEMORY_PREFIXES exempt; bash
    double-bracket detection.

    Filters out template-placeholder syntax that should never resolve.
    Strips path prefixes and trailing .md / backslash artifacts.
    """
    results = []
    in_fence = False
    memory_stems = collect_memory_stems()  # dynamic exemption set
    for i, line in enumerate(text.splitlines(), start=1):
        # Code-fence-aware: toggle on ``` lines (allow up to 3 spaces of indent)
        if FENCE_OPEN.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        # Indented code block (4-space indent): skip wikilinks inside
        if INDENTED_CODE.match(line):
            continue
        # Inline-backtick-aware: strip `inline code` spans before scanning for wikilinks
        scan_line = INLINE_CODE.sub("", line)
        for match in WIKILINK_PATTERN.finditer(scan_line):
            target = match.group(1).strip()
            if not target:
                continue
            # Skip placeholder/example syntax (extended in v2.1.1 with shell constructs)
            if PLACEHOLDER_PATTERN.match(target):
                continue
            # Bash double-bracket detection (defense-in-depth for [[$- == *i*]])
            if BASH_BRACKETS.match(target):
                continue
            # Auto-memory exemption: dynamic stem set first (covers any memory category)
            target_lower = target.lower()
            if target_lower in memory_stems:
                continue
            # Static prefix fallback (legacy compatibility + when home dir unreadable)
            if any(target_lower.startswith(p) for p in MEMORY_PREFIXES):
                continue
            # Strip trailing backslash artifacts (e.g., [[file\]] from sloppy escapes)
            target = target.rstrip("\\")
            # Strip path prefix: [[wiki/X/Y/file]] -> match against basename "file"
            if "/" in target:
                target = target.rsplit("/", 1)[-1]
            # Strip trailing .md or .base extension if present
            # (e.g., [[CLAUDE.md]] -> "CLAUDE"; [[dashboard.base]] -> "dashboard")
            if target.lower().endswith(".md"):
                target = target[:-3]
            elif target.lower().endswith(".base"):
                target = target[:-5]
            if not target:
                continue
            results.append((i, target))
    return results


def detect_forbidden_frontmatter(text: str) -> list[str]:
    """Return list of forbidden field names found in frontmatter (v2.1.1 classifier 6).

    Detects:
    - `domain:` field (forbidden per CLAUDE.md schema)
    - `tags:` entries with `domain/*` or `type/*` namespaces
    """
    if not text.startswith("---"):
        return []
    fences = list(FRONTMATTER_FENCE.finditer(text))
    if len(fences) < 2:
        return []
    fm_block = text[fences[0].end():fences[1].start()]
    findings = []
    if DOMAIN_FIELD.search(fm_block):
        findings.append("domain")
    # Tag namespace check: scan tag list entries
    in_tags = False
    for line in fm_block.splitlines():
        stripped = line.strip()
        if stripped.startswith("tags:"):
            in_tags = True
            continue
        if in_tags:
            if stripped.startswith("- "):
                tag_val = stripped[2:].strip().strip("'\"")
                if any(tag_val.startswith(ns) for ns in FORBIDDEN_TAG_NAMESPACES):
                    findings.append(f"tag-namespace:{tag_val}")
            elif stripped and not stripped.startswith("-"):
                in_tags = False
    return findings


def parse_frontmatter(text: str) -> tuple[bool, str | None]:
    """
    Check for YAML frontmatter. Returns (has_frontmatter, updated_value).
    updated_value is the raw string from the 'updated' field, or None.
    """
    if not text.startswith("---"):
        return False, None

    fences = list(FRONTMATTER_FENCE.finditer(text))
    if len(fences) < 2:
        return False, None

    # Frontmatter is between first and second fence
    fm_block = text[fences[0].end():fences[1].start()]
    updated_match = UPDATED_FIELD.search(fm_block)
    updated_val = updated_match.group(1).strip().strip("'\"") if updated_match else None
    return True, updated_val


def parse_date(date_str: str) -> date | None:
    """Try common date formats."""
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def relative_path(filepath: Path) -> str:
    """Return a vault-relative path string."""
    try:
        return str(filepath.relative_to(VAULT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(filepath)


def get_changed_files() -> list[Path] | None:
    """Return list of files modified vs HEAD (for --changed-only mode).

    Returns None if git is unavailable or fails.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=str(VAULT_ROOT),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None
        paths = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            p = VAULT_ROOT / line
            if p.exists() and (p.suffix == ".md" or p.suffix == ".base"):
                paths.append(p)
        return paths
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def collect_session_artifact_gaps() -> list[dict]:
    """X1 Classifier 10 (audit 2026-04-28): session-artifact continuity.

    For each git commit matching `^retro:` (a /retro session-end commit),
    verify that sessions-log.md AND decision-log.md have a body entry whose
    date matches the commit's date. Reports HARD DRIFT for retro commits
    without paired log entries.

    The match looks for heading-style entries (`### YYYY-MM-DD`) or table-row
    entries (`| YYYY-MM-DD |`); arbitrary substring matches do not count
    (avoids false negatives where the date appears only in cross-references
    or follow-up triggers within other entries).

    Returns list of {commit, date, subject, missing} dicts. `missing` is a
    list naming which log file(s) lack the matching date entry.
    """
    gaps = []
    try:
        result = subprocess.run(
            ["git", "log", "--grep=^retro:", "--pretty=format:%H|%ci|%s"],
            cwd=str(VAULT_ROOT),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return []
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return []

    sessions_log_path = VAULT_ROOT / "Calendar" / "decisions" / "sessions-log.md"
    decision_log_path = VAULT_ROOT / "Calendar" / "decisions" / "decision-log.md"

    sessions_text = read_file(sessions_log_path) or ""
    decision_text = read_file(decision_log_path) or ""

    def has_dated_entry(text: str, date_str: str) -> bool:
        """True if text contains a heading-style or table-row entry for date_str."""
        heading_pattern = re.compile(rf"^###\s+{re.escape(date_str)}\b", re.MULTILINE)
        table_pattern = re.compile(rf"^\|\s*{re.escape(date_str)}\s*\|", re.MULTILINE)
        return bool(heading_pattern.search(text) or table_pattern.search(text))

    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) < 3:
            continue
        commit_sha, commit_iso, subject = parts
        commit_date = commit_iso.split(" ")[0]  # "YYYY-MM-DD"

        missing = []
        if not has_dated_entry(sessions_text, commit_date):
            missing.append("sessions-log.md")
        if not has_dated_entry(decision_text, commit_date):
            missing.append("decision-log.md")

        if missing:
            gaps.append({
                "commit": commit_sha[:7],
                "date": commit_date,
                "subject": subject,
                "missing": missing,
            })

    return gaps


def collect_skill_body_length_violations() -> list[dict]:
    """X2 Classifier 11 (audit 2026-04-28): skill-body-length cap.

    Walk .claude/skills/*/SKILL.md (excluding _archive/) and report files
    exceeding SKILL_BODY_LENGTH_CAP (263 lines per CLAUDE.md sec 4).

    Returns list of {skill, lines, over_by} dicts.
    """
    violations = []
    skills_dir = VAULT_ROOT / ".claude" / "skills"
    if not skills_dir.exists():
        return []

    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        # Skip _archive/ subdirectories
        if "_archive" in skill_md.parts:
            continue
        try:
            line_count = sum(1 for _ in skill_md.open(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        if line_count > SKILL_BODY_LENGTH_CAP:
            violations.append({
                "skill": skill_md.parent.name,
                "lines": line_count,
                "over_by": line_count - SKILL_BODY_LENGTH_CAP,
            })

    return violations


def collect_claude_md_count_drift() -> list[dict]:
    """X3 Classifier 12 (audit 2026-04-28 5th-pass): CLAUDE.md count-drift detection.

    Parses three count claims in CLAUDE.md and reconciles against actuals:
      - "all <N> skills" (sec preamble narrative)
      - "Active Skills" table row count
      - "Investing (<N> docs)" (sec Reference Documents)

    Returns list of {location, claimed, actual} dicts. Tier: SOFT DRIFT (advisory).
    """
    drifts = []
    claude_md_path = VAULT_ROOT / "CLAUDE.md"
    text = read_file(claude_md_path)
    if text is None:
        return []

    skills_dir = VAULT_ROOT / ".claude" / "skills"
    investing_refs_dir = VAULT_ROOT / "Atlas" / "sources" / "investing"

    actual_skill_count = len(list(skills_dir.glob("*/SKILL.md"))) if skills_dir.exists() else 0
    actual_investing_refs = len(list(investing_refs_dir.glob("ref-*.md"))) if investing_refs_dir.exists() else 0

    # Parse "all <N> skills"
    m = re.search(r"all (\d+) skills", text)
    if m:
        claimed = int(m.group(1))
        if claimed != actual_skill_count:
            drifts.append({
                "location": "CLAUDE.md preamble 'all N skills'",
                "claimed": claimed,
                "actual": actual_skill_count,
            })

    # Parse "Active Skills" table row count
    table_match = re.search(r"## Active Skills.*?(?=\n## |\Z)", text, re.DOTALL)
    if table_match:
        rows = re.findall(r"^\| `/[a-z-]+`", table_match.group(0), re.MULTILINE)
        if len(rows) != actual_skill_count:
            drifts.append({
                "location": "CLAUDE.md Active Skills table",
                "claimed": len(rows),
                "actual": actual_skill_count,
            })

    # Parse "Investing (<N> docs)"
    m = re.search(r"Investing \((\d+) docs\)", text)
    if m:
        claimed = int(m.group(1))
        if claimed != actual_investing_refs:
            drifts.append({
                "location": "CLAUDE.md Investing ref-doc count",
                "claimed": claimed,
                "actual": actual_investing_refs,
            })

    return drifts


def collect_knowledge_moc_count_drift() -> list[dict]:
    """X5 Classifier 13 (audit 2026-04-28 5th-pass): knowledge-moc count-drift detection.

    Parses three count claims in Atlas/_MOCs/knowledge-moc.md and reconciles
    against actuals:
      - investing-moc "<N> entity notes, <M> analyses"
      - career-moc "<K> company entities" (only fires drift when claimed > actual)

    Returns list of {location, claimed, actual} dicts. Tier: SOFT DRIFT (advisory).
    """
    drifts = []
    moc_path = VAULT_ROOT / "Atlas" / "_MOCs" / "knowledge-moc.md"
    text = read_file(moc_path)
    if text is None:
        return []

    tickers_dir = VAULT_ROOT / "wiki" / "entities" / "tickers"
    companies_dir = VAULT_ROOT / "wiki" / "entities" / "companies"
    analyses_dir = VAULT_ROOT / "wiki" / "investing" / "analyses"

    actual_tickers = len(list(tickers_dir.glob("*.md"))) if tickers_dir.exists() else 0
    actual_companies = len(list(companies_dir.glob("*.md"))) if companies_dir.exists() else 0
    actual_entities = actual_tickers + actual_companies
    actual_analyses = len(list(analyses_dir.glob("*.md"))) if analyses_dir.exists() else 0

    # Parse investing-moc claims
    m = re.search(r"investing-moc.*?(\d+) entity notes,\s*(\d+) analyses", text)
    if m:
        claimed_e = int(m.group(1))
        claimed_a = int(m.group(2))
        if claimed_e != actual_entities:
            drifts.append({
                "location": "knowledge-moc investing-moc entity-note count",
                "claimed": claimed_e,
                "actual": actual_entities,
            })
        if claimed_a != actual_analyses:
            drifts.append({
                "location": "knowledge-moc investing-moc analyses count",
                "claimed": claimed_a,
                "actual": actual_analyses,
            })

    # Parse career-moc claim (company entities)
    m = re.search(r"career-moc.*?(\d+) company entities", text)
    if m:
        claimed_c = int(m.group(1))
        # Tolerance: company entities span career + investing namespaces; only
        # fire drift if claimed > actual (over-claim is hard drift; under-claim
        # is acceptable since some companies may belong to other domains).
        if claimed_c > actual_companies:
            drifts.append({
                "location": "knowledge-moc career-moc company-entity count",
                "claimed": claimed_c,
                "actual": actual_companies,
            })

    return drifts


def collect_investment_analysis_quality_drift() -> list[dict]:
    """X6 Classifier 14 (audit 2026-04-28 5th-pass): investment-analysis-quality scoring.

    For each wiki/investing/analyses/*.md, score on 7 dimensions per /invest
    extreme-overhaul mandates:
      1. Source count >= 25 (citation density)
      2. Source diversity >= 8 distinct domains
      3. Forensic metrics present (Piotroski + Altman + Beneish all numeric)
      4. Renowned-investor reference (Dataroma / 13F overlay present)
      5. Politician overlay (CapitolTrades / STOCK Act reference present)
      6. Insider cluster-buy check (OpenInsider reference present)
      7. TRADING DECISION header present (BUY/SELL/HOLD rating + summary)

    Returns list of {file, dimension, expected, actual, status} dicts for any
    failing dimensions. Tier: SOFT DRIFT (advisory; 0 score impact). Surfaces
    as recommendation in /vault audit output for analysts to address in next
    /invest invocation on the ticker.
    """
    drifts = []
    analyses_dir = VAULT_ROOT / "wiki" / "investing" / "analyses"
    if not analyses_dir.exists():
        return []

    domain_pattern = re.compile(r"https?://([^/\s\)]+)")
    grade_pattern = re.compile(r"\[Grade [A-F]")
    piotroski_pattern = re.compile(r"Piotroski.*?\b\d+\s*/\s*9\b", re.IGNORECASE)
    altman_pattern = re.compile(r"Altman.*?Z[- ]?Score.*?\d+\.\d+", re.IGNORECASE)
    beneish_pattern = re.compile(r"Beneish.*?M[- ]?Score.*?-?\d+\.\d+", re.IGNORECASE)
    dataroma_pattern = re.compile(r"dataroma|13F|13f-hr|superinvestor", re.IGNORECASE)
    capitol_pattern = re.compile(r"capitoltrades|STOCK Act|congressional|politician", re.IGNORECASE)
    openinsider_pattern = re.compile(r"openinsider|cluster.?buy|10b5-1|Form 4", re.IGNORECASE)
    rating_pattern = re.compile(r"TRADING DECISION|STRONG BUY|^\*\*Rating\*\*", re.MULTILINE)

    for analysis_md in sorted(analyses_dir.glob("*.md")):
        try:
            text = analysis_md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        rel = relative_path(analysis_md)

        # Dim 1: Source count (Grade markers + URLs)
        grade_count = len(grade_pattern.findall(text))
        url_count = len(domain_pattern.findall(text))
        source_count = max(grade_count, url_count)
        if source_count < 25:
            drifts.append({
                "file": rel, "dimension": "source_count",
                "expected": ">=25", "actual": source_count, "status": "FAIL"
            })

        # Dim 2: Source diversity (distinct domains)
        domains = set(domain_pattern.findall(text))
        if len(domains) < 8:
            drifts.append({
                "file": rel, "dimension": "source_diversity",
                "expected": ">=8 distinct domains", "actual": len(domains), "status": "FAIL"
            })

        # Dim 3: Forensic metrics (Piotroski + Altman + Beneish all numeric)
        has_piotroski = bool(piotroski_pattern.search(text))
        has_altman = bool(altman_pattern.search(text))
        has_beneish = bool(beneish_pattern.search(text))
        forensic_present = has_piotroski and has_altman and has_beneish
        if not forensic_present:
            missing = []
            if not has_piotroski: missing.append("Piotroski")
            if not has_altman: missing.append("Altman")
            if not has_beneish: missing.append("Beneish")
            drifts.append({
                "file": rel, "dimension": "forensic_metrics",
                "expected": "Piotroski+Altman+Beneish all numeric", "actual": f"missing {','.join(missing)}",
                "status": "FAIL"
            })

        # Dim 4: Renowned-investor reference (Dataroma / 13F)
        if not dataroma_pattern.search(text):
            drifts.append({
                "file": rel, "dimension": "renowned_investor_overlay",
                "expected": "Dataroma/13F reference", "actual": "absent", "status": "FAIL"
            })

        # Dim 5: Politician overlay (CapitolTrades / STOCK Act)
        if not capitol_pattern.search(text):
            drifts.append({
                "file": rel, "dimension": "politician_overlay",
                "expected": "CapitolTrades/STOCK-Act reference", "actual": "absent", "status": "FAIL"
            })

        # Dim 6: Insider cluster-buy check (OpenInsider)
        if not openinsider_pattern.search(text):
            drifts.append({
                "file": rel, "dimension": "insider_cluster_buy",
                "expected": "OpenInsider/cluster-buy/10b5-1 reference", "actual": "absent", "status": "FAIL"
            })

        # Dim 7: TRADING DECISION header (BUY/SELL/HOLD rating)
        if not rating_pattern.search(text):
            drifts.append({
                "file": rel, "dimension": "trading_decision_header",
                "expected": "TRADING DECISION header with BUY/SELL/HOLD rating", "actual": "absent",
                "status": "FAIL"
            })

    return drifts


def collect_stale_commitments(today: date) -> list[dict]:
    """X7 classifier (SOFT DRIFT; 0 score impact) -- 2026-05-04.

    Scans Calendar/daily/*.md for last 30 days for unchecked Commitments entries
    with ESCALATION_DATE in the past. Surfaces in audit output as advisory; the
    SessionStart STALE COMMITMENTS context block is the action-driver, not score.

    SOFT DRIFT tier (per user-flagged correction): backfilling 5+ stale entries
    on activation would breach 95-floor if HARD; visual surfacing handles action.
    """
    from datetime import timedelta as _td
    findings: list[dict] = []
    daily_dir = VAULT_ROOT / "Calendar" / "daily"
    if not daily_dir.exists():
        return findings
    cutoff = today - _td(days=30)
    pat_esc = re.compile(r"ESCALATION_DATE:\s*(\d{4}-\d{2}-\d{2})")
    pat_seed = re.compile(r"<!--\s*seeded-from:\s*(\S+?)\s*-->")
    for p in sorted(daily_dir.glob("*.md")):
        try:
            stem_date = datetime.strptime(p.stem, "%Y-%m-%d").date()
        except (ValueError, AttributeError):
            continue
        if stem_date < cutoff:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        in_commit = False
        for line_no, line in enumerate(text.splitlines(), start=1):
            s = line.strip()
            if s == "## Commitments":
                in_commit = True
                continue
            if in_commit and s.startswith("## "):
                in_commit = False
                continue
            if in_commit and s.startswith("- [ ]"):
                m = pat_esc.search(line)
                if m:
                    try:
                        esc = datetime.strptime(m.group(1), "%Y-%m-%d").date()
                    except ValueError:
                        continue
                    if esc < today:
                        days_overdue = (today - esc).days
                        seed_m = pat_seed.search(line)
                        slug = seed_m.group(1) if seed_m else "unknown"
                        findings.append({
                            "file": str(p.relative_to(VAULT_ROOT)).replace("\\", "/"),
                            "line": line_no,
                            "type": "stale-commitment",
                            "severity": "SOFT",
                            "decision_slug": slug,
                            "escalation_date": m.group(1),
                            "days_overdue": days_overdue,
                        })
    return findings


def collect_provenance_coverage() -> list[dict]:
    """X8 classifier (SOFT DRIFT; 0 score impact; cutoff-scoped) -- invest vNEXT 2026-06-09.

    Scans wiki/investing/analyses/*.md whose frontmatter created: date is on or
    after PROVENANCE_MIGRATION_CUTOFF for INGEST:claims entries missing the
    prov: field (the vNEXT 8th tuple field: mcp:* | script:* | web:*+grade).
    Detection is INGEST-block-scoped (between ':::ingest:claims' and the closing
    ':::') -- body-wide quantitative-claim regexes are too noisy by design.

    Fail-safe bias: files without parseable frontmatter or created: are SKIPPED
    (never flagged); pre-cutoff files are structurally exempt. SOFT tier means
    false negatives are acceptable; false positives on legacy content are not.
    """
    findings: list[dict] = []
    analyses_dir = VAULT_ROOT / "wiki" / "investing" / "analyses"
    if not analyses_dir.exists():
        return findings
    created_re = re.compile(r"^created:\s*(\S+)", re.MULTILINE)
    for p in sorted(analyses_dir.glob("*.md")):
        text = read_file(p)
        if text is None or not text.startswith("---"):
            continue
        # Extract the frontmatter block (between the first two --- fences);
        # parse_frontmatter() returns only the updated: value, not the block.
        fm_end = text.find("\n---", 3)
        if fm_end == -1:
            continue
        m = created_re.search(text[:fm_end])
        if not m:
            continue
        created = parse_date(m.group(1).strip().strip("'\""))
        if created is None or created < PROVENANCE_MIGRATION_CUTOFF:
            continue
        # Extract the INGEST claims block (':::ingest:claims' ... '\n:::')
        block_m = re.search(r":::ingest:claims\n(.*?)\n:::", text, re.DOTALL)
        if not block_m:
            continue
        block = block_m.group(1)
        # Split into claim entries on '- entity:' list-item starts
        entries = re.split(r"(?m)^- (?=entity:)", block)
        claim_no = 0
        for entry in entries:
            if not entry.strip().startswith("entity:"):
                continue
            claim_no += 1
            if not re.search(r"(?m)^\s+prov:", entry):
                metric_m = re.search(r"(?m)^\s*metric:\s*(\S+)", entry)
                findings.append({
                    "file": relative_path(p),
                    "type": "missing-provenance",
                    "severity": "SOFT",
                    "claim_index": claim_no,
                    "metric": metric_m.group(1) if metric_m else "unknown",
                    "created": created.isoformat(),
                })
    return findings


def run_audit(scope: str | None = None, changed_only: bool = False,
              quick: bool = False, json_output: bool = False):
    today = date.today()
    files = collect_md_files()
    # v2.2.1 C1 fix: build filename_index from FULL vault BEFORE applying
    # scope/changed_only filters. The scan scope restricts WHICH files are
    # scanned for content checks, but wikilink resolution must use the full
    # vault index to avoid false-positive broken-wikilink reports for targets
    # that exist in the vault but happen to be outside the current scope.
    # Pre-fix behavior caused pre-write-validator to falsely block every
    # Write/Edit on .md content with wikilinks (audit 2026-04-28 finding C1).
    skill_refs = collect_skill_companion_refs()
    base_files = collect_base_files()
    extra_targets = skill_refs + base_files
    filename_index = build_filename_index(files, extra_resolution_targets=extra_targets)
    # v2.2.2 C2 fix (audit 2026-04-28 fourth-pass): orphan classifier symmetry
    # counterpart to the C1 broken-wikilink fix. The orphan check needs the
    # GLOBAL set of wikilink targets (any file in the full vault that references
    # any other file). Pre-fix: orphan check used `all_link_targets` which is
    # populated only inside the scoped-files iteration, so under --scope mode
    # any inbound link from outside the scope was invisible -> false-positive
    # orphan reports. Build a global set BEFORE applying scope/changed_only
    # filters so the orphan classifier can resolve inbound links correctly
    # regardless of the scan-scope restriction.
    needs_global_pass = bool(scope) or changed_only
    global_all_link_targets: set[str] = set()
    if needs_global_pass:
        for f in files:  # `files` is the full vault list at this point
            text = read_file(f)
            if text is None:
                continue
            for _, target in extract_wikilinks(text):
                global_all_link_targets.add(target.lower())
    # v2.1.1 incremental modes (apply AFTER index build per C1 fix)
    if scope:
        scope_path = (VAULT_ROOT / scope).resolve()
        if scope_path.is_file():
            files = [f for f in files if f.resolve() == scope_path]
        else:
            files = [f for f in files if str(f.resolve()).startswith(str(scope_path))]
    if changed_only:
        changed = get_changed_files()
        if changed is not None:
            changed_resolved = {f.resolve() for f in changed}
            files = [f for f in files if f.resolve() in changed_resolved]

    # --- Data collection ---
    file_links: dict[Path, list[tuple[int, str]]] = {}      # outgoing wikilinks
    file_has_fm: dict[Path, bool] = {}                       # has frontmatter
    file_updated: dict[Path, str | None] = {}                # raw updated value

    # Aggregates
    broken_links: list[tuple[Path, int, str]] = []           # (file, line, target)
    all_link_targets: set[str] = set()                       # all referenced stems (lowered)
    files_missing_fm: list[Path] = []
    stale_files: list[tuple[Path, str, int]] = []            # (file, updated_str, days)
    forbidden_findings: list[tuple[Path, list[str]]] = []    # (file, list of forbidden field names) -- v2.2.x classifier 6 plumb 2026-05-04

    for f in files:
        text = read_file(f)
        if text is None:
            continue

        # Wikilinks -- always extract for orphan-detection inbound credit; but only
        # report-as-broken if the file is NOT in WIKILINK_SCAN_EXCLUDES nor in
        # WIKILINK_SCAN_EXEMPT_PATHS (per-file exemption for prevention-architecture-
        # style docs that legitimately discuss broken-wikilink classes in prose).
        links = extract_wikilinks(text)
        file_links[f] = links
        in_scan_exclude = should_exclude(f, WIKILINK_SCAN_EXCLUDES)
        rel_for_scan = relative_path(f)
        in_scan_exempt = rel_for_scan in WIKILINK_SCAN_EXEMPT_PATHS
        for line_no, target in links:
            target_lower = target.lower()
            all_link_targets.add(target_lower)
            if not in_scan_exclude and not in_scan_exempt and target_lower not in filename_index:
                broken_links.append((f, line_no, target))

        # Frontmatter
        has_fm, updated_val = parse_frontmatter(text)
        file_has_fm[f] = has_fm
        file_updated[f] = updated_val

        # Missing frontmatter (with extra excludes + by-design exempt paths)
        rel_path = relative_path(f)
        if (
            not has_fm
            and not should_exclude(f, FRONTMATTER_EXCLUDES)
            and rel_path not in FRONTMATTER_EXEMPT_PATHS
        ):
            files_missing_fm.append(f)

        # Stale detection
        if updated_val:
            d = parse_date(updated_val)
            if d:
                delta = (today - d).days
                if delta > STALE_THRESHOLD_DAYS:
                    stale_files.append((f, updated_val, delta))

        # Forbidden frontmatter detection (v2.1.1 classifier 6 -- plumbed 2026-05-04)
        # Detects forbidden `domain:` field + `domain/*` or `type/*` tag namespaces
        # per CLAUDE.md schema. GATE-class because schema violations are mechanically
        # forbidden, not advisory. FRONTMATTER_EXCLUDES applied for consistency with
        # missing-frontmatter classifier scope.
        if has_fm and not should_exclude(f, FRONTMATTER_EXCLUDES):
            forbidden = detect_forbidden_frontmatter(text)
            if forbidden:
                forbidden_findings.append((f, forbidden))

    # Orphan detection
    # C2 fix (audit 2026-04-28 fourth-pass): under --scope or --changed-only,
    # `all_link_targets` only sees outbound wikilinks from the scoped subset.
    # The orphan check requires inbound-link resolution against the FULL vault,
    # so use `global_all_link_targets` (built pre-filter) when scope is active.
    inbound_targets = global_all_link_targets if needs_global_pass else all_link_targets
    orphans: list[Path] = []
    for f in files:
        if should_exclude(f, ORPHAN_EXCLUDES):
            continue
        if relative_path(f) in ORPHAN_EXEMPT_PATHS:
            continue
        stem_lower = f.stem.lower()
        if stem_lower not in inbound_targets:
            orphans.append(f)

    # MOC completeness
    moc_stats: list[tuple[Path, int]] = []
    for f in files:
        if f.stem.endswith("-moc"):
            count = len(file_links.get(f, []))
            moc_stats.append((f, count))
    moc_stats.sort(key=lambda x: x[1], reverse=True)

    # --- Statistics ---
    total_files = len(files)
    with_fm = sum(1 for v in file_has_fm.values() if v)
    without_fm = total_files - with_fm
    total_links = sum(len(v) for v in file_links.values())
    avg_links = total_links / total_files if total_files else 0

    # --- Report ---
    out = []

    def w(line=""):
        out.append(line)

    w(f"# Vault Integrity Audit")
    w(f"**Generated:** {today.isoformat()}")
    w(f"**Vault root:** `{VAULT_ROOT}`")
    w(f"**Script version:** v2.1 (2026-04-26 false-positive filtering)")
    w()

    # Summary
    w("## Summary Statistics")
    w()
    w("| Metric | Count |")
    w("|--------|------:|")
    w(f"| Total .md files scanned | {total_files} |")
    w(f"| Skill-companion refs indexed | {len(skill_refs)} |")
    w(f"| .base files indexed | {len(base_files)} |")
    w(f"| Files with frontmatter | {with_fm} |")
    w(f"| Files without frontmatter | {without_fm} |")
    w(f"| Total wikilinks found | {total_links} |")
    w(f"| Avg links per file | {avg_links:.1f} |")
    w(f"| Broken wikilinks | {len(broken_links)} |")
    w(f"| Orphan files | {len(orphans)} |")
    w(f"| Stale files (>{STALE_THRESHOLD_DAYS}d) | {len(stale_files)} |")
    w()

    # Broken wikilinks
    w("## Broken Wikilinks")
    w()
    if broken_links:
        w(f"Found **{len(broken_links)}** broken links.")
        w()
        w("| Source File | Line | Broken Link |")
        w("|------------|-----:|-------------|")
        for f, line_no, target in sorted(broken_links, key=lambda x: (relative_path(x[0]), x[1])):
            w(f"| `{relative_path(f)}` | {line_no} | `[[{target}]]` |")
    else:
        w("No broken wikilinks found.")
    w()

    # Orphan files
    w("## Orphan Files (Zero Incoming Links)")
    w()
    if orphans:
        w(f"Found **{len(orphans)}** files with no incoming wikilinks.")
        w()
        w("| File | Has Frontmatter |")
        w("|------|:---------------:|")
        for f in sorted(orphans, key=lambda x: relative_path(x)):
            fm = "Yes" if file_has_fm.get(f, False) else "No"
            w(f"| `{relative_path(f)}` | {fm} |")
    else:
        w("No orphan files detected.")
    w()

    # Missing frontmatter
    w("## Files Missing Frontmatter")
    w()
    if files_missing_fm:
        w(f"Found **{len(files_missing_fm)}** files without YAML frontmatter.")
        w()
        w("| File |")
        w("|------|")
        for f in sorted(files_missing_fm, key=lambda x: relative_path(x)):
            w(f"| `{relative_path(f)}` |")
    else:
        w("All scanned files have frontmatter.")
    w()

    # Forbidden frontmatter (v2.1.1 classifier 6 -- plumbed 2026-05-04; GATE tier)
    w("## Forbidden Frontmatter Fields")
    w()
    if forbidden_findings:
        w(f"Found **{len(forbidden_findings)}** files with forbidden frontmatter fields.")
        w()
        w("| File | Forbidden Fields |")
        w("|------|------------------|")
        for f, fields in sorted(forbidden_findings, key=lambda x: relative_path(x[0])):
            w(f"| `{relative_path(f)}` | {', '.join(fields)} |")
    else:
        w("No forbidden frontmatter fields detected.")
    w()

    # Stale files
    w("## Stale Files")
    w()
    if stale_files:
        w(f"Found **{len(stale_files)}** files with `updated` date older than {STALE_THRESHOLD_DAYS} days.")
        w()
        w("| File | Updated | Days Stale |")
        w("|------|---------|----------:|")
        for f, updated_str, days in sorted(stale_files, key=lambda x: x[2], reverse=True):
            w(f"| `{relative_path(f)}` | {updated_str} | {days} |")
    else:
        w("No stale files detected.")
    w()

    # MOC completeness
    w("## MOC Completeness")
    w()
    if moc_stats:
        w("| MOC File | Outgoing Links |")
        w("|----------|---------------:|")
        for f, count in moc_stats:
            w(f"| `{relative_path(f)}` | {count} |")
    else:
        w("No MOC files found.")
    w()

    # === Vault Health Score (v2.2.2 -- 95-floor tier-weighted) ===
    # GATE classifiers: broken-wikilinks + missing-frontmatter (script-side)
    # HARD DRIFT: orphan-detection + stale-refs + session-artifact-gaps (X1) + skill-body-length (X2)
    # SOFT DRIFT (advisory; 0 score impact): handled by inline classifiers in /vault SKILL.md

    # X1 + X2 audit-2026-04-28 classifier extensions
    session_artifact_gaps = collect_session_artifact_gaps()
    skill_body_length_violations = collect_skill_body_length_violations()
    # X3 + X5 audit-2026-04-28 5th-pass classifier extensions (SOFT DRIFT)
    claude_md_count_drift = collect_claude_md_count_drift()
    knowledge_moc_count_drift = collect_knowledge_moc_count_drift()
    # X6 audit-2026-04-28 /invest extreme-overhaul classifier (SOFT DRIFT)
    investment_analysis_quality_drift = collect_investment_analysis_quality_drift()
    # X7 audit-2026-05-04 commitment-tracking: stale-commitment classifier (SOFT)
    stale_commitments_findings = collect_stale_commitments(today)
    # X8 invest-vnext-2026-06-09: provenance-coverage classifier (SOFT; cutoff-scoped)
    provenance_coverage_findings = collect_provenance_coverage()

    GATE_FINDINGS = len(broken_links) + len(files_missing_fm) + len(forbidden_findings)
    HARD_DRIFT_FINDINGS = (len(orphans) + len(stale_files)
                           + len(session_artifact_gaps)
                           + len(skill_body_length_violations))
    SOFT_DRIFT_FINDINGS = 0  # populated by inline classifiers; placeholder here

    GATE_PER, GATE_CAP = -5, -10
    HARD_PER, HARD_CAP = -1, -5

    gate_penalty = max(GATE_FINDINGS * GATE_PER, GATE_CAP)
    hard_penalty = max(HARD_DRIFT_FINDINGS * HARD_PER, HARD_CAP)
    soft_penalty = 0

    raw_pre_trend = 100 + gate_penalty + hard_penalty + soft_penalty
    # Trend adjustment is intentionally 0 here. The /vault SKILL.md Phase J reads
    # prior 3 audit reports and applies +/-2 with the suppression rule:
    #   if raw_pre_trend >= 97 AND GATE_FINDINGS == 0: trend_adjustment = +/-2
    # The script's --json output reflects the un-trend-adjusted score; consumers
    # that need the trend-adjusted score must invoke the SKILL or re-derive.
    trend_adjustment = 0
    raw_score = raw_pre_trend + trend_adjustment
    score = max(0, min(100, raw_score))
    if GATE_FINDINGS > 0 and score > 90:
        score = 90  # gate-breach hard-cap surfaces hook-bypass

    w("## Vault Health Score (v2.2)")
    w()
    w(f"**Score: {score}/100** (floor invariant: 95)")
    w()
    w("| Tier | Findings | Per | Cap | Penalty |")
    w("|------|---------:|----:|----:|--------:|")
    w(f"| GATE (must-be-zero) | {GATE_FINDINGS} | {GATE_PER} | {GATE_CAP} | {gate_penalty} |")
    w(f"| HARD DRIFT (capped) | {HARD_DRIFT_FINDINGS} | {HARD_PER} | {HARD_CAP} | {hard_penalty} |")
    w(f"| SOFT DRIFT (advisory) | {SOFT_DRIFT_FINDINGS} | 0 | 0 | 0 |")
    w()
    if GATE_FINDINGS > 0:
        w(f"**GATE breach: score hard-capped at 90** (must-be-zero violation present; investigate hook configuration).")
    else:
        w("GATE clean. Steady-state floor 95/100 holds.")
    w()
    w("Trend adjustment (+/-2) applied by /vault SKILL.md Phase J after reading prior 3 audits.")
    w()

    if json_output:
        findings = {
            "score": score,
            "gate_breach": GATE_FINDINGS > 0,
            "tiers": {
                "gate": {"count": GATE_FINDINGS, "penalty": gate_penalty},
                "hard_drift": {"count": HARD_DRIFT_FINDINGS, "penalty": hard_penalty},
                "soft_drift": {"count": SOFT_DRIFT_FINDINGS, "penalty": 0},
            },
            "broken_wikilinks": [
                {"file": relative_path(f), "line": ln, "target": t}
                for (f, ln, t) in broken_links
            ],
            "missing_frontmatter": [relative_path(f) for f in files_missing_fm],
            "forbidden_frontmatter": [
                {"file": relative_path(f), "fields": fields}
                for (f, fields) in forbidden_findings
            ],
            "orphans": [relative_path(f) for f in orphans],
            "stale_files": [
                {"file": relative_path(f), "updated": u, "days": d}
                for (f, u, d) in stale_files
            ],
            # X1 audit-2026-04-28: session-artifact continuity classifier
            "session_artifact_gaps": session_artifact_gaps,
            # X2 audit-2026-04-28: skill-body-length cap classifier
            "skill_body_length_violations": skill_body_length_violations,
            # X3 audit-2026-04-28 5th-pass: CLAUDE.md count-drift classifier (SOFT)
            "claude_md_count_drift": claude_md_count_drift,
            # X5 audit-2026-04-28 5th-pass: knowledge-moc count-drift classifier (SOFT)
            "knowledge_moc_count_drift": knowledge_moc_count_drift,
            # X6 audit-2026-04-28 /invest extreme-overhaul: investment-analysis quality (SOFT)
            "investment_analysis_quality_drift": investment_analysis_quality_drift,
            # X7 audit-2026-05-04 commitment-tracking: stale-commitment (SOFT; advisory only)
            "x7_stale_commitments": stale_commitments_findings,
            # X8 invest-vnext-2026-06-09: provenance-coverage (SOFT; cutoff-scoped 2026-06-10+)
            "x8_provenance_coverage": provenance_coverage_findings,
        }
        print(json.dumps(findings, indent=2))
        return

    report = "\n".join(out)
    print(report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vault integrity audit (v2.1.1)")
    parser.add_argument("--scope", default=None,
                        help="Restrict scan to one file or subtree (relative to vault root)")
    parser.add_argument("--changed-only", action="store_true",
                        help="Compare against HEAD; scan only modified files")
    parser.add_argument("--quick", action="store_true",
                        help="Skip orphan + MOC scans; run only 4 cheap CRITICAL classifiers")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Emit findings as JSON for hook consumption")
    args = parser.parse_args()
    run_audit(scope=args.scope, changed_only=args.changed_only,
              quick=args.quick, json_output=args.json_output)
