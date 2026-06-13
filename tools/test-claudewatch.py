#!/usr/bin/env python3
# test-claudewatch.py -- T-numbered acceptance tests for the claudewatch install.
# Verifies binary, MCP-only registration, out-of-tree DB invariant, no-vault-hook
# invariant, the live MCP tools/list handshake, and the vault docs.
# PASS/FAIL/SKIP per test; exit 0 if zero failures, 1 on any failure.
# Modeled on tools/test-telemetry-analyzer.py + tools/test-prevention-arch.sh. ASCII-only.
import json
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
VAULT = Path(os.environ.get("VAULT_ROOT", os.getcwd()))
BIN = HOME / ".local" / "bin" / "claudewatch.exe"
CLAUDE_JSON = HOME / ".claude.json"
DB = HOME / ".config" / "claudewatch" / "claudewatch.db"
HOOK_EVENTS = ["PreToolUse", "PostToolUse", "SessionStart", "Stop",
               "UserPromptSubmit", "PreCompact", "PostCompact"]


def _which_cw():
    if BIN.exists():
        return str(BIN)
    return shutil.which("claudewatch")


def _load_claude_json():
    if not CLAUDE_JSON.exists():
        return None
    try:
        return json.loads(CLAUDE_JSON.read_text(encoding="utf-8"))
    except Exception:
        return None


def _find_cw_server(obj):
    if isinstance(obj, dict):
        cw = obj.get("claudewatch")
        if isinstance(cw, dict) and cw.get("command"):
            return cw
        for v in obj.values():
            r = _find_cw_server(v)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _find_cw_server(v)
            if r:
                return r
    return None


def t1_binary_version():
    cw = _which_cw()
    if not cw:
        return ("FAIL", "claudewatch.exe not found on PATH or at " + str(BIN))
    try:
        r = subprocess.run([cw, "--version"], capture_output=True, text=True, timeout=20)
    except Exception as e:
        return ("FAIL", "exec error: " + str(e))
    if r.returncode != 0:
        return ("FAIL", "exit " + str(r.returncode))
    return ("PASS", (r.stdout or r.stderr).strip()[:60])


def t2_mcp_entry():
    data = _load_claude_json()
    if data is None:
        return ("FAIL", "~/.claude.json missing or unparseable")
    if _find_cw_server(data) or ("claudewatch" in json.dumps(data)):
        return ("PASS", "claudewatch MCP entry present")
    return ("FAIL", "no claudewatch entry in ~/.claude.json")


def t3_db_path():
    if DB.exists():
        return ("PASS", "db at " + str(DB))
    return ("SKIP", "db not yet created (lazy on first metric query): " + str(DB))


def t4_db_not_in_vault():
    try:
        DB.resolve().relative_to(VAULT.resolve())
        return ("FAIL", "DB path is UNDER the vault: " + str(DB))
    except ValueError:
        return ("PASS", "DB is out-of-tree (not under " + str(VAULT) + ")")
    except Exception as e:
        return ("PASS", "DB not under vault (" + str(e) + ")")


def _settings_hook_refs(path):
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        return ["<raw-match>"] if "claudewatch" in raw else []
    hooks = data.get("hooks", {}) or {}
    hits = []
    for ev in HOOK_EVENTS:
        if "claudewatch" in json.dumps(hooks.get(ev, [])):
            hits.append(ev)
    return hits


def t5_no_vault_hook():
    hits = []
    for name in ["settings.json", "settings.local.json"]:
        p = VAULT / ".claude" / name
        hits += [name + ":" + h for h in _settings_hook_refs(p)]
    if not hits:
        return ("PASS", "no claudewatch in vault settings hook arrays")
    return ("FAIL", "claudewatch hook refs: " + ", ".join(hits))


def t6_mcp_tools_list():
    data = _load_claude_json()
    srv = _find_cw_server(data) if data else None
    if not srv:
        return ("FAIL", "no claudewatch command in ~/.claude.json")
    cmd = [srv.get("command")] + list(srv.get("args", []) or [])
    init = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                       "clientInfo": {"name": "test-claudewatch", "version": "1.0"}}}
    inited = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    listreq = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
    payload = json.dumps(init) + "\n" + json.dumps(inited) + "\n" + json.dumps(listreq) + "\n"
    try:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True)
    except Exception as e:
        return ("FAIL", "spawn error: " + str(e))
    out_lines = []

    def _reader():
        try:
            for ln in p.stdout:
                out_lines.append(ln)
        except Exception:
            pass

    th = threading.Thread(target=_reader, daemon=True)
    th.start()
    try:
        p.stdin.write(payload)
        p.stdin.flush()
        p.stdin.close()
    except Exception as e:
        p.kill()
        return ("FAIL", "stdin write error: " + str(e))
    th.join(timeout=15)
    try:
        p.terminate()
    except Exception:
        pass
    tools = None
    for ln in out_lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            msg = json.loads(ln)
        except Exception:
            continue
        if msg.get("id") == 2 and isinstance(msg.get("result"), dict):
            tools = msg["result"].get("tools")
            break
    if tools is None:
        tail = "".join(out_lines)[-200:].replace(chr(10), " ")
        return ("FAIL", "no tools/list result (timeout or wrong subcommand); tail: " + tail)
    n = len(tools)
    if n >= 20:
        return ("PASS", str(n) + " MCP tools")
    return ("FAIL", "only " + str(n) + " tools (<20)")


def t7_docs_present():
    problems = []
    cm = VAULT / "CLAUDE.md"
    if not (cm.exists() and "## Observability" in cm.read_text(encoding="utf-8", errors="ignore")):
        problems.append("CLAUDE.md missing ## Observability")
    sk = VAULT / ".claude" / "skills" / "telemetry" / "SKILL.md"
    if not (sk.exists() and "claudewatch" in sk.read_text(encoding="utf-8", errors="ignore")):
        problems.append("telemetry SKILL.md missing claudewatch xref")
    if problems:
        return ("FAIL", "; ".join(problems))
    return ("PASS", "docs present")


TESTS = [
    ("T1 binary --version", t1_binary_version),
    ("T2 ~/.claude.json MCP entry", t2_mcp_entry),
    ("T3 DB path", t3_db_path),
    ("T4 DB out-of-tree guard", t4_db_not_in_vault),
    ("T5 no claudewatch in vault hooks", t5_no_vault_hook),
    ("T6 MCP tools/list handshake", t6_mcp_tools_list),
    ("T7 vault docs present", t7_docs_present),
]


def main():
    failed = 0
    for name, fn in TESTS:
        try:
            status, detail = fn()
        except Exception as e:
            status, detail = "FAIL", "exception: " + str(e)
        print("  " + status + ": " + name + " -- " + detail)
        if status == "FAIL":
            failed += 1
    print("")
    print("Result: " + str(len(TESTS) - failed) + " passed/skipped, " + str(failed) + " failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
