#!/usr/bin/env python3
"""gen-codex-yaml.py -- GENERATE docs/Osanwe Vault Codex.yaml from disk (ADR-09).

Replaces the hand-edited organ map. Idempotent by construction: output is a
pure function of the disk walk + git queries; running twice yields identical
bytes. Prose Codex remains authoritative for semantics; this file is the
machine index of record.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "Osanwe Vault Codex.yaml"


def sh(*args):
    r = subprocess.run(list(args), cwd=str(ROOT), capture_output=True)
    return r.stdout.decode(errors="replace").strip()


def yq(s):
    """Quote a string for YAML single-quote style."""
    return "'" + str(s).replace("'", "''") + "'"


def build():
    c = {"meta": {}, "folders": [], "skills": [], "agents": [], "roles": [],
         "workflows": [], "hooks": {}, "mcp_servers": {}, "scheduled_tasks": [],
         "git": {}, "gaps": []}

    c["entry_points"] = {
        "contract": "AGENTS.md",
        "current_state": "Efforts/osanwe-v2-overhaul/STATE.md",
        "architecture": "docs/Osanwe Vault Codex.md",
        "financial_methodology": "docs/financial-analysis-contract.md",
        "knowledge": "Atlas/_MOCs/knowledge-moc.md",
        "evaluation": "evaluation/challenge_protocol.md",
        "validation": ".agents/scripts/checkall.py",
    }
    c["meta"] = {
        "codex_version": "4.0",
        "generated": date.today().isoformat(),
        "generator": "tools/gen-codex-yaml.py (OSANWE-V2 ADR-09)",
        "vault_root": str(ROOT),
        "note": "GENERATED from disk -- hand edits will be overwritten; "
                "prose Codex is authoritative on conflict",
    }

    VOLATILE = {"_work", "state", "node_modules", "transcripts", ".smart-env",
                ".checkpoints", "cache", ".git", "__pycache__", ".pytest_cache"}
    for name in sorted(os.listdir(ROOT)):
        p = ROOT / name
        if not p.is_dir() or name in VOLATILE:
            continue
        n = 0
        for dp, dns, fns in os.walk(p):
            rel_parts = Path(dp).relative_to(p).parts
            if any(v in rel_parts for v in VOLATILE):
                dns[:] = []
                continue
            n += len(fns)
        if name.startswith(".") and name in (".git", ".smart-env", ".checkpoints"):
            continue
        c["folders"].append({"path": name + "/", "files_on_disk": n})

    skills_dir = ROOT / ".agents" / "skills"
    for d in sorted(skills_dir.iterdir()):
        smd = d / "SKILL.md"
        if d.is_dir() and smd.is_file():
            text = smd.read_text(encoding="utf-8", errors="replace")
            m = re.search(r'^description:\s*"(.+?)"\s*$', text[:2500], re.M)
            last = sh("git", "log", "-1", "--format=%cs", "--",
                      ".agents/skills/" + d.name)
            c["skills"].append({"name": d.name, "desc_chars": len(m.group(1)) if m else 0,
                                "last_commit": last})

    agents_dir = ROOT / ".claude" / "agents"
    if agents_dir.is_dir():
        for f in sorted(agents_dir.glob("*.md")):
            c["agents"].append(f.name[:-3])
    roles_dir = ROOT / ".agents" / "roles"
    if roles_dir.is_dir():
        c["roles"] = [f.name[:-3] for f in sorted(roles_dir.glob("*.md"))]

    wf = ROOT / ".claude" / "workflows"
    c["workflows"] = sorted(f.name for f in wf.glob("*")) if wf.is_dir() else []

    settings = ROOT / ".claude" / "settings.json"
    if settings.is_file():
        txt = settings.read_text(encoding="utf-8", errors="replace")
        c["hooks"]["claude_settings_hook_entries"] = len(re.findall(r'"command"', txt))

    reg = ROOT / ".agents" / "mcp" / "servers.json"
    if reg.is_file():
        data = json.loads(reg.read_text(encoding="utf-8"))
        servers = data.get("servers") or {}
        c["mcp_servers"] = {k: {"write_capable": bool(
            (v or {}).get("write_surface"))} for k, v in servers.items()}

    # This is a portable disk index, not a claim about live Task Scheduler state.
    c["scheduled_tasks"] = []
    c["meta"]["scheduled_tasks_status"] = "not queried; see docs/osanwe-runtime-reference.md"

    c["git"] = {"head_branch": sh("git", "branch", "--show-current"),
                "remotes": sh("git", "remote").splitlines()}

    yaml_skills = c["skills"]
    yaml_names = {s["name"] for s in yaml_skills}
    disk_names = yaml_names
    gaps = []
    if "local" not in disk_names:
        gaps.append("registry drift: 'local' missing")
    c["gaps"] = gaps

    return c


def render():
    data = build()
    text = ("# Osanwe Vault Codex -- machine index (GENERATED; do not hand-edit)\n"
            + yaml.safe_dump(data, sort_keys=False, allow_unicode=False))
    if yaml.safe_load(text) != data:
        raise ValueError("generated index failed typed YAML round trip")
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--check", action="store_true", help="read-only drift check")
    args = parser.parse_args()
    content = render().encode("utf-8")
    if args.check:
        same = args.output.is_file() and args.output.read_bytes() == content
        print("index current" if same else "index drift; regenerate with gen-codex-yaml.py")
        return 0 if same else 1
    args.output.write_bytes(content)
    print(f"wrote {args.output} ({len(content)} bytes); YAML round trip PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
