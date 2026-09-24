#!/usr/bin/env python3
"""Check complete cross-harness contracts, bootstrap and canon skill adapters.

Default and --quick are read-only and fail on drift. AGENTS.md is the contract and
the only instruction file: a CLAUDE.md at the root, in .claude/ or in .claude/skills/
is a FINDING. Claude Code reads AGENTS.md natively only when
the project root carries none of CLAUDE.md, .claude/CLAUDE.md or CLAUDE.local.md, so
a per-machine CLAUDE.local.md must begin with the line `@AGENTS.md`; one that does not
is a FINDING. There is no --sync mode: nothing is mirrored, so nothing is copied.
This checker never calls checkall, so checkall may invoke it without recursion.
"""
import argparse
import importlib.util
import os
from pathlib import Path
import re
import sys

ROOT = Path(os.environ.get("OSANWE_VAULT_ROOT") or Path(__file__).resolve().parents[1])
sys.dont_write_bytecode = True

# Instruction files a live session would load beside the contract. The pre-commit
# cage also refuses a CLAUDE.md at any depth in the index; this checker spawns no
# processes, so it checks the paths Claude Code reads.
SECOND_CONTRACTS = ("CLAUDE.md", ".claude/CLAUDE.md", ".claude/skills/CLAUDE.md")
# A per-machine CLAUDE.local.md suppresses Claude Code's native AGENTS.md read
# (measured 2026-09-22 on 2.1.280: AGENTS.md beside CLAUDE.local.md loaded only the
# local file), so its first line must import the contract. CRLF is accepted, the
# same line-ending rule as the pre-commit cage.
LOCAL_FILE = "CLAUDE.local.md"
LOCAL_IMPORT = b"@AGENTS.md"


def local_imports_contract(path):
    """True when the file's first line is exactly '@AGENTS.md'. Reads that line only;
    the rest of the per-machine file is private and never read."""
    with path.open("rb") as f:
        return f.readline(256).rstrip(b"\r\n") == LOCAL_IMPORT


def contract_findings(root=ROOT):
    findings = []
    canon = root / "AGENTS.md"
    if not canon.is_file():
        return ["AGENTS.md missing"]
    if canon.is_symlink():
        return ["AGENTS.md must be a regular file, not a symbolic link"]
    raw = canon.read_bytes()
    if not raw.strip():
        findings.append("AGENTS.md empty")
    for extra in SECOND_CONTRACTS:
        path = root / extra
        if path.is_file() or path.is_symlink():
            findings.append("%s exists: a second project instruction file beside the contract; delete it" % extra)
    local = root / LOCAL_FILE
    if local.is_file() and not local_imports_contract(local):
        findings.append("%s does not begin with the line '@AGENTS.md': a root CLAUDE.local.md stops "
                        "Claude Code reading AGENTS.md natively, so it must import the contract" % LOCAL_FILE)
    if any(b > 127 for b in raw):
        findings.append("AGENTS.md contains non-ASCII bytes")
    return findings


def bootstrap_findings(root=ROOT):
    path = root / ".agents/scripts/gen-bootstrap.py"
    if not path.is_file():
        return [".agents/scripts/gen-bootstrap.py missing"]
    spec = importlib.util.spec_from_file_location("contract_bootstrap", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    expected = mod.render(root)
    target = root / "BOOTSTRAP.md"
    if not target.is_file() or target.read_bytes() != expected:
        return ["BOOTSTRAP.md stale or incomplete; run python .agents/scripts/gen-bootstrap.py"]
    return []


def skill_findings(root=ROOT):
    def names(base):
        return {p.name for p in base.iterdir() if not p.name.startswith("_")
                and p.is_dir() and (p / "SKILL.md").is_file()} if base.is_dir() else set()
    canon = names(root / ".agents/skills")
    derived = names(root / ".claude/skills")
    if canon != derived:
        return ["skill-tree set mismatch: canon-only=%s derived-only=%s" %
                (sorted(canon - derived), sorted(derived - canon))]
    return []


def link_findings(root=ROOT):
    """Retain router pointer checks without loading protected file contents."""
    findings = []
    routers = [root / "AGENTS.md", root / ".agents/skills/AGENTS.md",
               root / ".claude/skills/AGENTS.md"]
    skip = {".git", ".raw", "private", "finance", "credentials", ".obsidian",
            "node_modules", "_archive", "_quarantine", "_work", ".checkpoints"}
    stems = set()
    for scope in ("wiki", "Atlas", "Calendar", "Efforts", "docs", ".agents", ".claude/skills"):
        base = root / scope
        if not base.is_dir():
            continue
        for current, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in skip and not (Path(current) / d).is_symlink()]
            stems.update(Path(name).stem for name in files if name.endswith(".md") and not name.endswith(".local.md"))
    file_pattern = re.compile(r"(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\.(?:md|py|sh|yaml|json|toml|js)\b")
    for router in routers:
        if not router.is_file():
            continue
        text = re.sub(r"```.*?```", "", router.read_text(encoding="utf-8"), flags=re.S)
        for link in re.findall(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]", text):
            if not link.startswith("memory:") and link.strip() not in stems:
                findings.append("%s: wikilink [[%s]] does not resolve" % (router.relative_to(root), link))
        for token in re.findall(r"`([^`]+)`", text):
            if any(c in token for c in "<>*{}") or "://" in token:
                continue
            for match in file_pattern.finditer(token):
                name = match.group(0)
                if match.start() and token[match.start() - 1] in "/:\\":
                    continue
                if not (root / name).is_file():
                    findings.append("%s: file pointer %s does not resolve" % (router.relative_to(root), name))
    return findings


def size_findings(root=ROOT):
    budget = 32768
    config = root / ".codex/config.toml"
    if config.is_file():
        match = re.search(r"^\s*project_doc_max_bytes\s*=\s*(\d+)",
                          config.read_text(encoding="utf-8"), re.M)
        if match:
            budget = int(match.group(1))
    nested = [root / ".agents/skills/AGENTS.md", root / ".claude/skills/AGENTS.md"]
    chain = (root / "AGENTS.md").stat().st_size + max(
        (p.stat().st_size for p in nested if p.is_file()), default=0)
    return ["contract chain %d bytes exceeds configured budget %d" % (chain, budget)] if chain > budget else []


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quick", action="store_true", help="compact output; nonzero on failure")
    args = ap.parse_args(argv)
    try:
        findings = contract_findings()
        if (ROOT / "AGENTS.md").is_file() and not (ROOT / "AGENTS.md").is_symlink():
            findings += bootstrap_findings() + size_findings()
        findings += skill_findings() + link_findings()
    except Exception as exc:
        print("router-check FAIL: %s" % exc)
        return 1
    if not args.quick:
        for finding in findings:
            print("[FAIL/router] " + finding)
    print("router-check: %d FAIL (single root contract, complete bootstrap, skill sets, pointers, size)" % len(findings))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
