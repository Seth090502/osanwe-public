#!/usr/bin/env python3
"""vault-census.py -- reproducible tree + organ census for Project Osanwe.

Read-only. Emits JSON (default: Efforts/osanwe-v2-overhaul/_work/census.json)
plus a compact stdout summary. Becomes the generator behind the Vault Codex
YAML organ map in W7 (--codex flag lands then).
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDE_TOP = {"nested-tooling"}          # nested separate repo: shallow-count only
EXCLUDE_DIR_NAMES = {".git", "node_modules", ".smart-env", "transcripts",
                     "_archive", "_quarantine", ".checkpoints"}
LEDGERS = ["Calendar/decisions/sessions-log.md", "Calendar/decisions/decision-log.md",
           "Calendar/decisions/execute-or-decline.md", "wiki/insight-stream.md"]


def sh(*args):
    r = subprocess.run(list(args), cwd=str(ROOT), capture_output=True)
    return r.stdout.decode(errors="replace"), r.returncode


def dir_stats(path):
    files = md_files = 0
    md_bytes = all_bytes = 0
    newest = 0.0
    for dp, dns, fns in os.walk(path):
        rel_top = Path(dp).relative_to(path).parts
        if any(part in EXCLUDE_DIR_NAMES for part in rel_top):
            dns[:] = []
            continue
        for fn in fns:
            p = Path(dp) / fn
            try:
                st = p.stat()
            except OSError:
                continue
            files += 1
            all_bytes += st.st_size
            newest = max(newest, st.st_mtime)
            if fn.lower().endswith(".md"):
                md_files += 1
                md_bytes += st.st_size
    return {"files": files, "bytes": all_bytes, "md_files": md_files,
            "md_bytes": md_bytes}


def frontmatter_desc_len(text):
    m = re.search(r'^description:\s*(.+(?:\n\s+.+)*)$', text[:6000], re.M)
    return len(m.group(1).strip().encode()) if m else 0


def census_skills():
    out = {}
    base = ROOT / ".agents" / "skills"
    if not base.is_dir():
        return out
    for d in sorted(base.iterdir()):
        sk = d / "SKILL.md"
        if not sk.is_file():
            continue
        text = sk.read_text(encoding="utf-8", errors="replace")
        refs = sorted(d.glob("ref-*.md"))
        ref_bytes = sum(p.stat().st_size for p in refs)
        last = sh("git", "log", "-1", "--format=%cs", "--", str(d.relative_to(ROOT)))[0].strip()
        out[d.name] = {
            "skill_md_bytes": sk.stat().st_size,
            "skill_md_lines": text.count("\n") + 1,
            "desc_bytes": frontmatter_desc_len(text),
            "refs": len(refs),
            "ref_bytes": ref_bytes,
            "last_commit": last,
        }
    return out


def census_agents():
    out = {}
    base = ROOT / ".claude" / "agents"
    if not base.is_dir():
        return out
    for p in sorted(base.glob("*.md")):
        text = p.read_text(encoding="utf-8", errors="replace")
        model = re.search(r"^model:\s*(\S+)", text, re.M)
        out[p.stem] = {
            "bytes": p.stat().st_size,
            "desc_bytes": frontmatter_desc_len(text),
            "model": model.group(1) if model else None,
        }
    return out


def census_tools():
    ext = {}
    largest = []
    tdir = ROOT / "tools"
    for p in tdir.rglob("*"):
        if not p.is_file():
            continue
        e = p.suffix.lower() or "(none)"
        ext[e] = ext.get(e, 0) + 1
        try:
            largest.append((p.stat().st_size, str(p.relative_to(tdir))))
        except OSError:
            pass
    largest.sort(reverse=True)
    return {"by_ext": dict(sorted(ext.items(), key=lambda kv: -kv[1])),
            "file_count": sum(ext.values()),
            "largest_10": [[n, nm] for n, nm in largest[:10]]}


def census_mcp():
    reg = ROOT / ".agents" / "mcp" / "servers.json"
    servers = {}
    if reg.is_file():
        try:
            data = json.loads(reg.read_text(encoding="utf-8"))
            for name, spec in (data.get("servers") or data.get("mcpServers") or {}).items():
                ws = None
                if isinstance(spec, dict):
                    ws = (spec.get("write_surface") is not None) or bool(spec.get("write_tools"))
                    if isinstance(spec.get("tools"), dict):
                        ws = ws or any(
                            ("write" in str(k).lower() or "order" in str(k).lower())
                            for k in spec["tools"])
                servers[name] = {"write_capable_hint": bool(ws)}
        except Exception as exc:
            servers["_parse_error"] = {"err": str(exc)[:120]}
    gen = {}
    for cfg in [".mcp.json", "opencode.json"]:
        p = ROOT / cfg
        if p.is_file():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                gen[cfg] = list((data.get("mcpServers") or {}).keys())
            except Exception:
                gen[cfg] = ["_parse_error"]
    return {"registry": servers, "generated": gen}


def census_state():
    st = ROOT / ".claude" / "state"
    n = b = 0
    if st.is_dir():
        for p in st.rglob("*"):
            if p.is_file():
                n += 1
                try:
                    b += p.stat().st_size
                except OSError:
                    pass
    relay = ROOT / ".claude" / "state" / "relay"
    rn = rb = 0
    if relay.is_dir():
        for p in relay.rglob("*"):
            if p.is_file():
                rn += 1
                rb += p.stat().st_size
    return {"state_files": n, "state_bytes": b, "relay_files": rn, "relay_bytes": rb}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "Efforts/osanwe-v2-overhaul/_work/census.json"))
    args = ap.parse_args()

    c = {"generated": date.today().isoformat(), "root": str(ROOT)}

    c["top_dirs"] = {}
    for entry in sorted(os.listdir(ROOT)):
        p = ROOT / entry
        if not p.is_dir():
            continue
        if entry in EXCLUDE_TOP or entry.startswith("."):
            if entry == ".claude":
                c["top_dirs"][".claude"] = dir_stats(p)
            elif entry == ".agents":
                c["top_dirs"][".agents"] = dir_stats(p)
            continue
        c["top_dirs"][entry] = dir_stats(p)

    c["nested_repo_shallow"] = {
        "note": "nested separate repo, LOCAL-BRANCH-ONLY; not walked",
        "router_agents_md_bytes": (ROOT / "nested-tooling" / "AGENTS.md").stat().st_size
        if (ROOT / "nested-tooling" / "AGENTS.md").is_file() else None,
    }

    c["skills_canon"] = census_skills()
    derived = ROOT / ".claude" / "skills"
    c["skills_derived_count"] = len([d for d in derived.iterdir() if d.is_dir()]
                                    ) if derived.is_dir() else 0
    c["agents_claude"] = census_agents()
    roles = ROOT / ".agents" / "roles"
    c["roles_portable"] = sorted(p.name for p in roles.glob("*.md")) if roles.is_dir() else []

    settings = ROOT / ".claude" / "settings.json"
    c["hooks_claude_entries"] = None
    if settings.is_file():
        txt = settings.read_text(encoding="utf-8", errors="replace")
        c["hooks_claude_entries"] = len(re.findall(r'"matcher"|"command"', txt))
    manifest = ROOT / ".agents" / "hooks" / "manifest.yaml"
    c["hooks_manifest_bytes"] = manifest.stat().st_size if manifest.is_file() else 0

    wf = ROOT / ".claude" / "workflows"
    c["workflows"] = sorted(p.name for p in wf.glob("*")) if wf.is_dir() else []

    c["tools"] = census_tools()
    c["mcp"] = census_mcp()

    cfg = ROOT / "config"
    c["config_files"] = {p.name: p.stat().st_size
                         for p in sorted(cfg.iterdir()) if p.is_file()} if cfg.is_dir() else {}

    c["ledgers"] = {}
    for lp in LEDGERS + ["wiki/hot.md", "docs/backlog.md"]:
        fp = ROOT / lp
        if fp.is_file():
            raw = fp.read_bytes()
            c["ledgers"][lp] = {"bytes": len(raw), "lines": raw.count(b"\n") + 1}

    for key, pattern, rootp in [
        ("daily_notes", "*.md", "Calendar/daily"),
        ("briefings", "*.md", "Calendar/decisions/briefings"),
        ("entities_tickers", "*.md", "wiki/entities/tickers"),
        ("entities_companies", "*.md", "wiki/entities/companies"),
        ("research_notes", "*.md", "wiki/research"),
        ("theses", "*.md", "Atlas/concepts/investing/theses"),
    ]:
        d = ROOT / rootp
        c[key] = len(list(d.rglob(pattern))) if d.is_dir() else 0

    git_out, _ = sh("git", "rev-list", "--count", "HEAD")
    branch_out, _ = sh("git", "branch")
    head_out, _ = sh("git", "branch", "--show-current")
    status_out, _ = sh("git", "status", "--porcelain")
    c["git"] = {
        "total_commits": int(git_out.strip() or 0),
        "branches": len([l for l in branch_out.splitlines() if l.strip()]),
        "head_branch": head_out.strip(),
        "dirty_entries": len([l for l in status_out.splitlines() if l.strip()]),
    }

    c["state_telemetry"] = census_state()

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(c, f, indent=1)

    s = c["skills_canon"]
    print("census ->", args.out)
    print(f"skills canon: {len(s)} | derived: {c['skills_derived_count']} | "
          f"agents: {len(c['agents_claude'])} | roles: {len(c['roles_portable'])}")
    print(f"top_dirs: {len(c['top_dirs'])} | tools files: {c['tools']['file_count']}")
    print(f"sessions-log: {c['ledgers'].get('Calendar/decisions/sessions-log.md')}")
    print(f"hot.md: {c['ledgers'].get('wiki/hot.md')}")
    print(f"git: {c['git']}")


if __name__ == "__main__":
    sys.exit(main())
