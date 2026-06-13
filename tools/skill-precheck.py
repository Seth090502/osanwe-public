#!/usr/bin/env python3
"""
Skill-level pre-commit validator with PostToolUse hook mode.

Two modes:

(batch, default -- preserved manual-invocation contract for 7 existing skills):
    python tools/skill-precheck.py <file1> <file2> ... [--skill <name>] [--report {json,markdown}]
    Validates a multi-file batch (composed-and-tmp-written by the skill) before
    its atomic write. Each <fileN> must exist with the proposed content. Exits
    0 if no GATE findings, 2 otherwise.

(hook):
    python tools/skill-precheck.py --mode hook
    Reads PostToolUse tool_input JSON from stdin, extracts file_path, validates
    ONE file. Wired into .claude/settings.json PostToolUse chain after
    orphan-check, before hot-md-check, timeout 10s. Exits 0 on clean / non-md
    / non-vault / exempt; 2 on GATE findings (blocks auto-commit via
    auto-commit.sh gate-count check).

Reports (--report json or markdown, batch mode only):
    json     : structured {files[], aggregate, blocking_files, remediation_hints}
    markdown : human-readable diagnostics block (preserved from prior version)

Remediation hints: when a broken-wikilink finding's target stem fuzzy-matches
an existing vault file (Levenshtein-similarity >=0.7 via difflib), suggest
the closest match. Helps the user identify rename-induced or typo-induced
broken links without re-grep cycles.

Bypass: CLAUDE_VAULT_BYPASS_VALIDATOR=1 (logged to .claude/state/bypasses-<date>.log).

Invocation patterns:
  Skill body (Phase J.0/O.0): unchanged from prior contract; positional args.
  Hook (PostToolUse Write|Edit|MultiEdit): --mode hook, stdin JSON.
"""
import argparse
import difflib
import functools
import json
import os
import subprocess
import sys
from datetime import datetime, date
from pathlib import Path

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", os.getcwd()))
HOOK_TIMEOUT_SEC = 8  # leave headroom under 10s registered hook timeout
BATCH_TIMEOUT_SEC = 20  # preserved
EXEMPT_PATH_PREFIXES_HOOK = (
    "CLAUDE.md",
    "CLAUDE.local.md",
    "AGENTS.md",
    "AGENTS.override.md",
    "AGENTS.override.md.template",
    "docs/PROJECT-OSANWE-PACKET.md",
    "docs/VAULT-HANDOFF-V16.md",
    "docs/CODEX-COMPATIBILITY.md",
    "tools/migrations/README.md",
    "tools/CODEX_TOOLS_UNVERIFIED.md",
    "wiki/research/test-tmp/",
    ".claude/skills/",  # skill bodies validated separately via X2 classifier
    ".agents/skills/",  # Codex-mirror skill bodies (Mission Four)
    ".codex/agents/",   # Codex subagent TOML (Mission Four)
    ".codex/hooks/",    # Codex-specific hook scripts (Mission Four)
    "_archive/",
    "_quarantine/",
)
EXEMPT_EXTENSIONS_HOOK = (".log", ".json", ".jsonl", ".html", ".sh", ".py", ".ps1")


@functools.lru_cache(maxsize=1)
def vault_md_stems():
    """Set of all .md file stems in the vault (for fuzzy-match remediation).
    Cached because vault traversal is expensive. Re-run = re-import = re-scan."""
    stems = set()
    for p in VAULT_ROOT.rglob("*.md"):
        # Skip .git, _archive, _quarantine, .raw paths
        rel = p.relative_to(VAULT_ROOT).as_posix()
        if any(rel.startswith(prefix) for prefix in (".git/", "_archive/", "_quarantine/", ".raw/")):
            continue
        stems.add(p.stem)
    return stems


def fuzzy_suggest(target: str, threshold: float = 0.7):
    """Return up to 3 close-match stems for a broken-wikilink target."""
    if not target:
        return []
    matches = difflib.get_close_matches(target, vault_md_stems(), n=3, cutoff=threshold)
    return matches


def log_bypass(skill: str, files, gate_count: int):
    bypass_log = VAULT_ROOT / ".claude" / "state" / f"bypasses-{date.today().isoformat()}.log"
    bypass_log.parent.mkdir(exist_ok=True, parents=True)
    with bypass_log.open("a", encoding="utf-8") as f:
        f.write(
            f"{datetime.now().isoformat()} skill-precheck skill={skill} "
            f"files={','.join(files)} gate_findings={gate_count}\n"
        )


def is_hook_exempt(rel_path: str) -> bool:
    """Hook-mode path exemptions: skip non-vault-content writes (script files,
    fenced docs that intentionally hold illustrative wikilinks, raw notes).
    Batch mode does NOT use this list (skill explicitly opted in)."""
    if not rel_path:
        return True
    rp = rel_path.replace("\\", "/")
    if any(rp.startswith(p) for p in EXEMPT_PATH_PREFIXES_HOOK):
        return True
    if rp.endswith(EXEMPT_EXTENSIONS_HOOK):
        return True
    return False


def run_audit_scope(rel_path, timeout_sec):
    """Run vault-audit.py --scope <rel_path> --json. Returns parsed JSON or None."""
    try:
        result = subprocess.run(
            ["python", str(VAULT_ROOT / "tools" / "vault-audit.py"),
             "--scope", str(rel_path), "--json"],
            cwd=str(VAULT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None
    try:
        return json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return None


def extract_file_findings(data):
    """Pull per-file GATE/HARD findings from vault-audit JSON. Returns dict."""
    if not data:
        return {"gate": 0, "hard": 0, "broken_wikilinks": [],
                "missing_frontmatter": [], "forbidden_frontmatter": [],
                "orphans": []}
    return {
        "gate": data.get("tiers", {}).get("gate", {}).get("count", 0),
        "hard": data.get("tiers", {}).get("hard_drift", {}).get("count", 0),
        "broken_wikilinks": data.get("broken_wikilinks", []),
        "missing_frontmatter": data.get("missing_frontmatter", []),
        "forbidden_frontmatter": data.get("forbidden_frontmatter", []),
        "orphans": data.get("orphans", []),
    }


def build_diagnostics(file_arg, findings, with_hints=True):
    """Compose human-readable diagnostic lines for a file's GATE findings.
    Returns list of strings. Includes fuzzy-match hints when with_hints=True."""
    diags = []
    for b in findings["broken_wikilinks"]:
        line = f"  [GATE/broken-wikilink] {b.get('file', file_arg)}:{b.get('line', '?')} -> [[{b.get('target', '')}]]"
        if with_hints:
            suggestions = fuzzy_suggest(b.get("target", ""))
            if suggestions:
                line += f"  (suggested: {', '.join(f'[[{s}]]' for s in suggestions)})"
        diags.append(line)
    for fm in findings["missing_frontmatter"]:
        diags.append(f"  [GATE/missing-frontmatter] {fm}")
    for ff in findings["forbidden_frontmatter"]:
        fields = ", ".join(ff.get("fields", [])) if isinstance(ff, dict) else ""
        path = ff.get("file", "") if isinstance(ff, dict) else str(ff)
        diags.append(f"  [GATE/forbidden-frontmatter] {path} -> {fields}")
    return diags


def build_remediation_hints(per_file):
    """Aggregate fuzzy-match suggestions across all broken-wikilink findings."""
    hints = []
    for entry in per_file:
        for b in entry["findings"]["broken_wikilinks"]:
            suggestions = fuzzy_suggest(b.get("target", ""))
            if suggestions:
                hints.append({
                    "file": entry["path"],
                    "line": b.get("line"),
                    "broken_target": b.get("target"),
                    "suggested_targets": suggestions,
                })
    return hints


def render_markdown_report(per_file, aggregate, skill):
    """Human-readable batch report (used when --report markdown or default)."""
    lines = [f"skill-precheck ({skill}): {aggregate['total_gate']} GATE finding(s) "
             f"across {aggregate['total_files']} file(s)"]
    if aggregate["blocking_files"]:
        lines.append(f"  Blocking files: {', '.join(aggregate['blocking_files'])}")
    for entry in per_file:
        if entry["findings"]["gate"] > 0:
            lines.append(f"\nFile: {entry['path']}  (gate={entry['findings']['gate']}, "
                         f"hard={entry['findings']['hard']})")
            lines.extend(build_diagnostics(entry["path"], entry["findings"]))
    lines.append(
        "\nFix options: (1) correct target name; (2) de-link to plain text; "
        "(3) wrap illustrative wikilinks in `inline code` or fenced ``` blocks; "
        "(4) for auto-memory targets use [[memory:<stem>]] grammar; "
        "(5) prepend canonical frontmatter for new wiki/Calendar/Efforts/Atlas files."
    )
    lines.append("Bypass: CLAUDE_VAULT_BYPASS_VALIDATOR=1 (logs to .claude/state/bypasses-<date>.log)")
    return "\n".join(lines)


def render_json_report(per_file, aggregate, hints, skill):
    return {
        "mode": "batch",
        "skill": skill,
        "files": [
            {
                "path": entry["path"],
                "gate_findings": entry["findings"]["gate"],
                "hard_findings": entry["findings"]["hard"],
                "would_breach_floor": entry["findings"]["gate"] > 0,
                "diagnostics": build_diagnostics(entry["path"], entry["findings"], with_hints=False),
            }
            for entry in per_file
        ],
        "aggregate": aggregate,
        "remediation_hints": hints,
    }


def run_batch(args):
    """Default mode: positional file args; aggregated multi-file report."""
    per_file = []
    total_gate = 0
    total_hard = 0
    blocking = []

    for file_arg in args.files:
        fp = Path(file_arg)
        if not fp.exists():
            print(f"skill-precheck: file not found: {file_arg}", file=sys.stderr)
            sys.exit(2)
        try:
            rel_path = fp.relative_to(VAULT_ROOT)
        except ValueError:
            rel_path = fp.resolve()

        data = run_audit_scope(rel_path, BATCH_TIMEOUT_SEC)
        findings = extract_file_findings(data)
        per_file.append({"path": str(rel_path), "findings": findings})
        total_gate += findings["gate"]
        total_hard += findings["hard"]
        if findings["gate"] > 0:
            blocking.append(str(rel_path))

    # Estimate post-batch score using same v2.2 formula vault-audit applies
    gate_pen = max(total_gate * -5, -10)
    hard_pen = max(total_hard * -1, -5)
    post_score = max(0, min(100, 100 + gate_pen + hard_pen))
    if total_gate > 0 and post_score > 90:
        post_score = 90

    aggregate = {
        "total_gate": total_gate,
        "total_hard": total_hard,
        "total_files": len(per_file),
        "blocking_files": blocking,
        "post_batch_score_estimate": post_score,
    }

    if total_gate == 0:
        if args.report == "json":
            hints = build_remediation_hints(per_file)
            print(json.dumps(render_json_report(per_file, aggregate, hints, args.skill), indent=2))
        sys.exit(0)

    if os.environ.get("CLAUDE_VAULT_BYPASS_VALIDATOR") == "1":
        log_bypass(args.skill, args.files, total_gate)
        if args.report == "json":
            hints = build_remediation_hints(per_file)
            print(json.dumps(render_json_report(per_file, aggregate, hints, args.skill), indent=2))
        sys.exit(0)

    if args.report == "json":
        hints = build_remediation_hints(per_file)
        out = render_json_report(per_file, aggregate, hints, args.skill)
        print(json.dumps(out, indent=2), file=sys.stderr)
    else:
        print(render_markdown_report(per_file, aggregate, args.skill), file=sys.stderr)
    sys.exit(2)


def run_hook():
    """PostToolUse hook mode: read tool_input JSON from stdin; validate one file."""
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)  # malformed input -> silent skip (do not block tool chain)

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)

    fp = Path(file_path)
    if not fp.exists():
        sys.exit(0)  # file gone (hook fires post-write but file may have been temp)

    try:
        rel_path = fp.relative_to(VAULT_ROOT)
    except ValueError:
        sys.exit(0)  # outside vault root

    rel_str = str(rel_path).replace("\\", "/")
    if is_hook_exempt(rel_str):
        sys.exit(0)

    audit_data = run_audit_scope(rel_path, HOOK_TIMEOUT_SEC)
    findings = extract_file_findings(audit_data)

    if findings["gate"] == 0:
        sys.exit(0)

    if os.environ.get("CLAUDE_VAULT_BYPASS_VALIDATOR") == "1":
        log_bypass("hook", [rel_str], findings["gate"])
        sys.exit(0)

    diags = build_diagnostics(rel_str, findings)
    print(f"skill-precheck (hook): {findings['gate']} GATE finding(s) on {rel_str}", file=sys.stderr)
    for line in diags:
        print(line, file=sys.stderr)
    print("Bypass: CLAUDE_VAULT_BYPASS_VALIDATOR=1 (logs to .claude/state/bypasses-<date>.log)", file=sys.stderr)
    sys.exit(2)


def main():
    parser = argparse.ArgumentParser(description="Skill-level pre-commit validator (batch + hook modes)")
    parser.add_argument("files", nargs="*", help="Files to validate (batch mode positional args)")
    parser.add_argument("--skill", default="unknown", help="Invoking skill name (batch mode)")
    parser.add_argument("--mode", choices=["batch", "hook"], default="batch",
                        help="batch (default; positional files) or hook (stdin JSON)")
    parser.add_argument("--report", choices=["json", "markdown"], default="markdown",
                        help="Report format (batch mode only; default markdown)")
    args = parser.parse_args()

    if args.mode == "hook":
        run_hook()
    else:
        if not args.files:
            parser.error("batch mode requires at least one file path")
        run_batch(args)


if __name__ == "__main__":
    main()
