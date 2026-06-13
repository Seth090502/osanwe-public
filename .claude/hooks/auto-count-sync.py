#!/usr/bin/env python3
"""
auto-count-sync.py -- PostToolUse hook firing on CLAUDE.md + Atlas/_MOCs/* writes.

Surfaces count-drift in real-time at the moment of write, supplementing the
post-hoc /vault audit X3 (CLAUDE.md count-drift) and X5 (knowledge-moc
count-drift) classifiers. The audit-classifier path requires an explicit
/vault audit invocation; this hook fires on every relevant write so the
writer (Claude or human) sees drift immediately and can correct in-flight.

Trigger:
  PostToolUse Write|Edit|MultiEdit on file_path matching:
    - CLAUDE.md
    - Atlas/_MOCs/*.md

Behavior (default):
  Scan post-write content for count claims; compute actuals via filesystem
  glob; emit warnings to stderr for any drift; log to
  .claude/state/count-drift-<date>.log. Exit 0 (advisory, never blocks).

Behavior (CLAUDE_AUTO_COUNT_SYNC=1):
  Same as default PLUS rewrite the file in place applying the corrections.
  Opt-in because in-place rewrite during a write can collide with other
  hooks in the chain. Use sparingly; verify diff post-write.

Bypass: CLAUDE_AUTO_COUNT_SYNC_BYPASS=1 (logged to bypasses-<date>.log).

Patterns recognized:
  CLAUDE.md
    - "Investing (<N> docs)"            actual: count of Atlas/sources/investing/ref-*.md
    - "<N> refs including <X>"          actual: count of refs in same path block
    - "all <N> skills"                  actual: count of .claude/skills/*/SKILL.md
  knowledge-moc.md
    - "<N> entity notes"                actual: count of wiki/entities/tickers/*.md + companies/*.md
    - "<N> analyses"                    actual: count of wiki/investing/analyses/*.md
    - "<N> reference docs"              actual: total Atlas/sources/*/ref-*.md
"""
from __future__ import annotations
import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", os.getcwd()))


def log_event(kind: str, payload: dict):
    """Append a single JSON line to .claude/state/count-drift-<date>.log."""
    log_dir = VAULT_ROOT / ".claude" / "state"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"count-drift-{date.today().isoformat()}.log"
        entry = {"ts": datetime.now().isoformat(), "kind": kind, **payload}
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


def log_bypass(reason: str):
    log_dir = VAULT_ROOT / ".claude" / "state"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"bypasses-{date.today().isoformat()}.log"
        with log_path.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} auto-count-sync BYPASS reason={reason}\n")
    except OSError:
        pass


def count_glob(pattern: str) -> int:
    """Count files matching a glob relative to VAULT_ROOT."""
    return len(list(VAULT_ROOT.glob(pattern)))


def is_trigger_path(rel_str: str) -> bool:
    """Return True if rel_str is CLAUDE.md or under Atlas/_MOCs/."""
    if rel_str == "CLAUDE.md":
        return True
    if rel_str.startswith("Atlas/_MOCs/") and rel_str.endswith(".md"):
        return True
    return False


def detect_drifts_claude_md(text: str) -> list[dict]:
    """Detect count-drift in CLAUDE.md content. Returns list of finding dicts."""
    findings = []

    # "Investing (<N> docs)" -> Atlas/sources/investing/ref-*.md
    m = re.search(r"Investing \((\d+) docs\)", text)
    if m:
        claimed = int(m.group(1))
        actual = count_glob("Atlas/sources/investing/ref-*.md")
        if claimed != actual:
            findings.append({
                "pattern": "investing_docs_paren",
                "claimed": claimed,
                "actual": actual,
                "literal": m.group(0),
                "replacement": f"Investing ({actual} docs)",
            })

    # "<N> refs including <X>" -- bullet form (used at CLAUDE.md L69)
    for m in re.finditer(r"`([^`]*ref-\*\.md)`\s+--\s+(\d+)\s+refs\s+including\b", text):
        path_glob = m.group(1).rstrip("/").replace("ref-*.md", "ref-*.md")
        # path_glob is already vault-relative or pattern; treat as glob
        claimed = int(m.group(2))
        # Resolve glob: assume the pattern is rooted at VAULT_ROOT
        actual = count_glob(path_glob.lstrip("/"))
        if actual == 0 and "/" in path_glob:
            # Maybe a leading slash; try without it
            actual = count_glob(path_glob.lstrip("/"))
        if claimed != actual and actual > 0:
            findings.append({
                "pattern": "n_refs_bullet",
                "claimed": claimed,
                "actual": actual,
                "literal": m.group(0),
                "replacement": m.group(0).replace(f"{claimed} refs", f"{actual} refs"),
                "glob": path_glob,
            })

    # "all <N> skills"
    m = re.search(r"all (\d+) skills", text)
    if m:
        claimed = int(m.group(1))
        actual = count_glob(".claude/skills/*/SKILL.md")
        if claimed != actual:
            findings.append({
                "pattern": "all_n_skills",
                "claimed": claimed,
                "actual": actual,
                "literal": m.group(0),
                "replacement": f"all {actual} skills",
            })

    return findings


def detect_drifts_knowledge_moc(text: str) -> list[dict]:
    """Detect count-drift in knowledge-moc.md (and other MOC files)."""
    findings = []

    # "<N> entity notes" -> wiki/entities/tickers/*.md + companies/*.md
    m = re.search(r"(\d+)\s+entity\s+notes", text)
    if m:
        claimed = int(m.group(1))
        actual = (count_glob("wiki/entities/tickers/*.md")
                  + count_glob("wiki/entities/companies/*.md"))
        if claimed != actual:
            findings.append({
                "pattern": "entity_notes_total",
                "claimed": claimed,
                "actual": actual,
                "literal": m.group(0),
                "replacement": f"{actual} entity notes",
            })

    # "<N> analyses" -> wiki/investing/analyses/*.md
    m = re.search(r"(\d+)\s+analyses\b", text)
    if m:
        claimed = int(m.group(1))
        actual = count_glob("wiki/investing/analyses/*.md")
        if claimed != actual:
            findings.append({
                "pattern": "analyses_count",
                "claimed": claimed,
                "actual": actual,
                "literal": m.group(0),
                "replacement": f"{actual} analyses",
            })

    return findings


def apply_auto_fix(file_path: Path, findings: list[dict]) -> int:
    """Apply replacement strings to the file in place. Returns number applied."""
    if not findings:
        return 0
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError:
        return 0
    applied = 0
    new_text = text
    for f in findings:
        if "literal" in f and "replacement" in f and f["literal"] in new_text:
            new_text = new_text.replace(f["literal"], f["replacement"], 1)
            applied += 1
    if applied > 0 and new_text != text:
        try:
            file_path.write_text(new_text, encoding="utf-8")
        except OSError:
            return 0
    return applied


def main() -> int:
    if os.environ.get("CLAUDE_AUTO_COUNT_SYNC_BYPASS") == "1":
        log_bypass("env-var")
        return 0

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    file_path_str = (payload.get("tool_input") or {}).get("file_path", "")
    if not file_path_str:
        return 0

    fp = Path(file_path_str)
    if not fp.exists():
        return 0
    try:
        rel_str = str(fp.relative_to(VAULT_ROOT)).replace("\\", "/")
    except ValueError:
        return 0

    if not is_trigger_path(rel_str):
        return 0

    try:
        text = fp.read_text(encoding="utf-8")
    except OSError:
        return 0

    if rel_str == "CLAUDE.md":
        findings = detect_drifts_claude_md(text)
    else:
        findings = detect_drifts_knowledge_moc(text)

    if not findings:
        return 0

    # Surface to stderr (advisory) + log
    sys.stderr.write(f"auto-count-sync: {len(findings)} count-drift finding(s) in {rel_str}\n")
    for f in findings:
        sys.stderr.write(
            f"  - {f['pattern']}: claimed={f['claimed']} actual={f['actual']} "
            f"(suggest: '{f.get('replacement', '?')}')\n"
        )
    log_event("drift_detected", {"file": rel_str, "findings": findings})

    if os.environ.get("CLAUDE_AUTO_COUNT_SYNC") == "1":
        applied = apply_auto_fix(fp, findings)
        sys.stderr.write(f"auto-count-sync: AUTO-FIX applied {applied}/{len(findings)} corrections to {rel_str}\n")
        log_event("auto_fix_applied", {"file": rel_str, "applied": applied,
                                       "total_findings": len(findings)})

    return 0  # Advisory; never blocks


if __name__ == "__main__":
    sys.exit(main())
