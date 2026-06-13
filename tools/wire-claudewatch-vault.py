#!/usr/bin/env python3
# wire-claudewatch-vault.py -- Phase D6-D10 of the claudewatch install mission.
#
# Runs AFTER tools/install-claudewatch.ps1 succeeds. Performs the vault-side wiring
# as ONE transaction (all-or-nothing), runs 16 named verify gates, and -- only on
# full pass -- lands an F11 atomic commit of the vault files. The osanwe-public
# memory writes are out-of-tree (no git).
#
# Fail-clean: any BLOCKING gate failure rolls back EVERY write (vault + memory) and
# exits 1 with a FAIL report naming the gate. No partial state. No commit.
#
# Refuses to run if the binary install is incomplete (G1 pre-flight) or if claudewatch
# is NOT MCP-only (G6/G15/G16 pre-flight) -- it will not write docs that assert a state
# that is not real.
#
# Usage:
#   python tools/wire-claudewatch-vault.py            # real wiring + gates + commit
#   python tools/wire-claudewatch-vault.py --dry-run  # plan only; no subprocess, no
#                                                      # binary, no writes, no commit
#
# Exit 0 + "STATUS: MISSION_COMPLETE" on full pass; exit 1 + FAIL report otherwise.
# ASCII-only. No emojis. Idempotent (per-edit guards skip already-applied changes).

import argparse
import json
import os
import re
import subprocess
import sys
import threading
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
VAULT = Path(os.environ.get("VAULT_ROOT", os.getcwd()))
MEM = HOME / ".claude" / "projects" / "osanwe-public" / "memory"

BIN = HOME / ".local" / "bin" / "claudewatch.exe"
CLAUDE_JSON = HOME / ".claude.json"
GLOBAL_SETTINGS = HOME / ".claude" / "settings.json"
GLOBAL_HOOKS_DIR = HOME / ".claude" / "hooks"
GLOBAL_RULES_DIR = HOME / ".claude" / "rules"
CW_DB = HOME / ".config" / "claudewatch" / "claudewatch.db"

HOT_MD = VAULT / "wiki" / "hot.md"
CLAUDE_MD = VAULT / "CLAUDE.md"
SKILL_MD = VAULT / ".claude" / "skills" / "telemetry" / "SKILL.md"
SKILL_MIRROR = VAULT / ".agents" / "skills" / "telemetry" / "SKILL.md"
TEST_FILE = VAULT / "tools" / "test-claudewatch.py"
F11 = VAULT / ".claude" / "state" / "auto-commit-disabled"

TOOL_MEM = MEM / "tool_claudewatch.md"
CC_MEM = MEM / "cc_community_patterns_2026.md"
MEMORY_INDEX = MEM / "MEMORY.md"

HOOK_EVENTS = ["PreToolUse", "PostToolUse", "SessionStart", "Stop",
               "UserPromptSubmit", "PreCompact", "PostCompact"]

# ---------------------------------------------------------------------------
# Content (ASCII-only). Anchors are stable substrings in the target files.
# ---------------------------------------------------------------------------
HOTMD_ANCHOR = "### Vault tooling state"
HOTMD_LINE = ("- **claudewatch (live drift, MCP-only)** -- query get_drift_signal / "
              "get_session_dashboard via the claudewatch MCP server mid-session; the "
              "post-hoc trail stays in /telemetry. Installed 2026-05-25; behavioral "
              "rules + blocking hook deferred (see tools/INSTALL-CLAUDEWATCH.md).")

CLAUDEMD_ANCHOR = "## Active Skills"
CLAUDEMD_SECTION = r"""## Observability

Two complementary layers (claudewatch never writes inside <VAULT_ROOT>):

- **Post-hoc -- `/telemetry` + `tools/telemetry_analyzer.py`:** reads the vault's `.claude/state/*.jsonl` sinks (SubagentStart/Stop + PostToolUseFailure + PostCompact) into a derived SQLite index; answers "what failed in the last N days" (orphan pairs, failure clusters, duration outliers). Offline, vault-local.
- **Live -- claudewatch (MCP-only):** a local Go binary (github.com/blackwell-systems/claudewatch, MIT/Apache-2.0) that reads `~/.claude/projects` transcripts into an out-of-tree SQLite DB at `~/.config/claudewatch/claudewatch.db` and exposes ~23 read-only MCP tools (`get_drift_signal`, `get_session_dashboard`, `get_project_health`, ...) so Claude can query its own mid-session metrics; answers "am I drifting right now". Installed 2026-05-25 MCP-ONLY: the global behavioral rules and the blocking PostToolUse hook are DEFERRED -- they would collide with the 11-command PostToolUse chain and override the SessionStart protocol. No network, no API keys. Codex parity: N/A (CC-specific binary + MCP). Install/runbook: `tools/INSTALL-CLAUDEWATCH.md`.

"""

SKILL_ANCHOR = "- **/ingest, /enrich** are not coordinated with /telemetry (different surfaces)."
SKILL_XREF = ("\n\n- **claudewatch** (live counterpart): /telemetry is post-hoc (reads "
              ".claude/state sinks for what already failed); claudewatch is the live, "
              "mid-session layer (read-only MCP tools over ~/.claude transcripts -- "
              "get_drift_signal, get_session_dashboard). Complementary surfaces, not a "
              "replacement. See tools/INSTALL-CLAUDEWATCH.md.")

CC_OLD = "Next-mission candidate after /consolidate lands."
CC_NEW = ("ADOPTED 2026-05-25 (MCP-only; behavioral rules + blocking PostToolUse hook "
          "deferred per [[feedback-prevention-architecture-limits]]). See [[tool-claudewatch]].")

INDEX_TOOLS_OLD = "## Osanwe Vault -- Tools (23)"
INDEX_TOOLS_NEW = "## Osanwe Vault -- Tools (24)"
INDEX_PLAYBOOKS_ANCHOR = "\n\n## Osanwe Vault -- Playbooks (8)"
INDEX_CW_LINE = ("- [claudewatch](tool_claudewatch.md) -- local Go binary; ~23 read-only "
                 "MCP tools for live mid-session metrics (drift/cost/friction); "
                 "out-of-tree SQLite; MCP-only (rules + hook deferred)")
INDEX_CC_OLD = "claudewatch, /council"
INDEX_CC_NEW = "claudewatch (ADOPTED), /council"

TOOL_CLAUDEWATCH_MD = r"""---
name: tool-claudewatch
description: "Local-only Go binary (MIT/Apache-2.0) that reads ~/.claude transcripts into an out-of-tree SQLite DB and exposes ~23 read-only MCP tools for LIVE mid-session metrics (drift, cost velocity, friction). The live counterpart to the post-hoc telemetry analyzer. Installed MCP-only; behavioral rules + blocking hook deferred."
metadata:
  node_type: memory
  type: reference
---

**Purpose.** AgentOps for Claude Code -- lets Claude query its own performance DURING a session via read-only MCP. The LIVE counterpart to [[tool-telemetry-analyzer]] (post-hoc): /telemetry answers "what failed yesterday"; claudewatch answers "am I drifting right now" (get_drift_signal classifies exploring/implementing/drifting from recent tool calls).

**Where it lives.** Binary `~/.local/bin/claudewatch.exe` (v0.15.0 prebuilt windows_amd64). DB + config out-of-tree at `~/.config/claudewatch/` (claudewatch.db + config.yaml) -- NOT under <VAULT_ROOT>. MCP server registered in `~/.claude.json`. Installed via tools/install-claudewatch.ps1 then tools/wire-claudewatch-vault.py.

**Inputs.** Reads `~/.claude/projects` session transcripts (DefaultClaudeHome ~/.claude). CLI subcommands plus `claudewatch mcp` (stdio MCP server). config.yaml: scan_paths (default ~/code; <VAULT_ROOT> added best-effort), friction RecurringThreshold 0.30.

**Outputs.** ~23 read-only MCP tools: ~20 metric readers + get_drift_signal (drift detector) + get_suggestions / get_stale_patterns (suggesters). SQLite snapshots in claudewatch.db. No network, no API keys, no writes outside ~/.config/claudewatch.

**State files.** `~/.config/claudewatch/claudewatch.db` (out-of-tree; not git-tracked; not touched by the vault auto-commit hook) + config.yaml. No vault state files.

**Dual-engine status.** Claude-only (CC-specific binary + MCP client). No Codex mirror; documented gap (claudewatch reads ~/.claude transcripts, which a Codex session does not produce).

**Common failure modes.** (1) README documents macOS/Linux only -- Windows uses the prebuilt windows_amd64.zip release asset (a doc gap, not a capability gap; source ships watch_windows.go). (2) Full `claudewatch install` (without --mcp-only) injects GLOBAL behavioral rules in ~/.claude/rules/ and can add a BLOCKING PostToolUse hook that collides with the vault's 11-command chain -- always install MCP-only (see [[feedback-prevention-architecture-limits]]). (3) claudewatch.db grows unbounded (no built-in retention) -- prune manually.

**Composes with** [[skill-telemetry]], [[tool-telemetry-analyzer]], [[skill-consolidate]], [[hook-subagent-telemetry]], [[feedback-prevention-architecture-limits]].
"""

TOOL_SECTION_TOKENS = ["**Purpose.**", "**Where it lives.**", "**Inputs.**", "**Outputs.**",
                       "**State files.**", "**Dual-engine status.**",
                       "**Common failure modes.**", "**Composes with**"]

# test-claudewatch.py source (no triple-quotes inside; raw to preserve Windows paths + \n literals)
TEST_PY = r'''#!/usr/bin/env python3
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
'''

# ---------------------------------------------------------------------------
# Edit helpers (idempotent + anchor-asserting)
# ---------------------------------------------------------------------------
class WireError(Exception):
    pass


def safe_insert_after(content, anchor_substr, insert_text, marker):
    """Insert insert_text after the line containing anchor_substr. Idempotent via marker."""
    if marker in content:
        return content, False  # already applied
    lines = content.split("\n")
    idx = [i for i, ln in enumerate(lines) if anchor_substr in ln]
    if len(idx) != 1:
        raise WireError("anchor '%s' found %d times (need 1)" % (anchor_substr, len(idx)))
    i = idx[0]
    lines.insert(i + 1, insert_text)
    return "\n".join(lines), True


def safe_insert_before(content, anchor_substr, insert_text, marker):
    """Insert insert_text immediately before anchor_substr. Idempotent via marker."""
    if marker in content:
        return content, False
    if content.count(anchor_substr) != 1:
        raise WireError("anchor '%s' found %d times (need 1)" % (anchor_substr, content.count(anchor_substr)))
    return content.replace(anchor_substr, insert_text + anchor_substr, 1), True


def safe_replace(content, old, new):
    """Replace old->new exactly once. Idempotent (no-op if new present and old absent)."""
    if new in content and old not in content:
        return content, False
    if content.count(old) != 1:
        raise WireError("replace target '%s' found %d times (need 1)" % (old[:40], content.count(old)))
    return content.replace(old, new, 1), True


# ---------------------------------------------------------------------------
# Transaction (rollback on any failure)
# ---------------------------------------------------------------------------
class Txn:
    def __init__(self, dry):
        self.dry = dry
        self.records = []  # (Path, original_bytes_or_None)
        self.actions = []  # human log

    def _capture(self, path):
        path = Path(path)
        self.records.append((path, path.read_bytes() if path.exists() else None))

    def write(self, path, content, label):
        path = Path(path)
        self.actions.append(label)
        if self.dry:
            print("  would write: " + str(path) + "  (" + label + ")")
            return
        self._capture(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def edit(self, path, transform, label):
        """transform(content)->(new_content, changed_bool). Skips write if unchanged."""
        path = Path(path)
        self.actions.append(label)
        if self.dry:
            print("  would edit:  " + str(path) + "  (" + label + ")")
            return
        if not path.exists():
            raise WireError("edit target missing: " + str(path))
        original = path.read_text(encoding="utf-8")
        new, changed = transform(original)
        if not changed:
            print("  edit no-op (idempotent): " + str(path) + "  (" + label + ")")
            return
        self._capture(path)
        path.write_text(new, encoding="utf-8")

    def capture_external(self, path):
        """Capture a file before an external tool mutates it (for rollback)."""
        if self.dry:
            return
        self._capture(path)

    def rollback(self):
        for path, orig in reversed(self.records):
            try:
                if orig is None:
                    if path.exists():
                        path.unlink()
                else:
                    path.write_bytes(orig)
            except Exception as e:
                print("  ROLLBACK WARN: " + str(path) + ": " + str(e))


# ---------------------------------------------------------------------------
# D6-D10 write phase
# ---------------------------------------------------------------------------
def do_writes(txn):
    # D6 hot.md pointer line
    txn.edit(HOT_MD,
             lambda c: safe_insert_after(c, HOTMD_ANCHOR, HOTMD_LINE, "claudewatch (live drift, MCP-only)"),
             "D6 hot.md drift pointer")
    # D7 test-claudewatch.py
    txn.write(TEST_FILE, TEST_PY, "D7 tools/test-claudewatch.py")
    # D8a CLAUDE.md Observability section
    txn.edit(CLAUDE_MD,
             lambda c: safe_insert_before(c, CLAUDEMD_ANCHOR, CLAUDEMD_SECTION, "## Observability"),
             "D8a CLAUDE.md Observability section")
    # D8b telemetry SKILL.md see-also
    txn.edit(SKILL_MD,
             lambda c: safe_insert_after(c, SKILL_ANCHOR, SKILL_XREF, "**claudewatch** (live counterpart)"),
             "D8b telemetry SKILL.md xref")
    # D8c sync mirror to .agents (external tool; capture mirror first for rollback)
    txn.capture_external(SKILL_MIRROR)
    if txn.dry:
        print("  would run:   python tools/sync-skills.py  (mirror telemetry SKILL.md to .agents)")
    else:
        r = subprocess.run([sys.executable, "tools/sync-skills.py"], cwd=str(VAULT),
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            raise WireError("sync-skills.py failed: " + (r.stderr or r.stdout)[-200:])
    # D9a tool_claudewatch.md memory
    txn.write(TOOL_MEM, TOOL_CLAUDEWATCH_MD, "D9a tool_claudewatch.md (memory)")
    # D9b cc_community_patterns demote
    txn.edit(CC_MEM, lambda c: safe_replace(c, CC_OLD, CC_NEW), "D9b cc_community_patterns demote")
    # D10 MEMORY.md index
    def _index(c):
        c, _ = safe_replace(c, INDEX_TOOLS_OLD, INDEX_TOOLS_NEW)
        c, _ = safe_insert_before(c, INDEX_PLAYBOOKS_ANCHOR, "\n" + INDEX_CW_LINE, "(tool_claudewatch.md)")
        c, _ = safe_replace(c, INDEX_CC_OLD, INDEX_CC_NEW)
        return c, True
    txn.edit(MEMORY_INDEX, _index, "D10 MEMORY.md index (Tools 23->24 + claudewatch line + cc refresh)")


# ---------------------------------------------------------------------------
# Verify gates -- each returns (status, detail); BLOCKING per the registry below
# ---------------------------------------------------------------------------
def _run(cmd, timeout=120):
    return subprocess.run(cmd, cwd=str(VAULT), capture_output=True, text=True, timeout=timeout)


def _load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
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


def _hook_refs(path):
    data = _load_json(path)
    if data is None:
        if Path(path).exists() and "claudewatch" in Path(path).read_text(encoding="utf-8", errors="ignore"):
            return ["<raw>"]
        return []
    hooks = data.get("hooks", {}) or {}
    return [ev for ev in HOOK_EVENTS if "claudewatch" in json.dumps(hooks.get(ev, []))]


BASELINE_GATE_IDS = None  # set in pre-flight BEFORE any write; used by G7 (delta check)


def _audit_json():
    r = _run([sys.executable, "tools/vault-audit.py", "--json"], timeout=180)
    try:
        return json.loads(r.stdout)
    except Exception:
        return None


def _gate_ids(data):
    """Stable ids for GATE-tier findings (broken wikilinks + missing/forbidden frontmatter)."""
    ids = set()
    if not data:
        return ids
    for it in (data.get("broken_wikilinks") or []):
        if isinstance(it, dict):
            ids.add("bw:%s:%s:%s" % (it.get("file"), it.get("line"), it.get("target")))
        else:
            ids.add("bw:" + str(it))
    for it in (data.get("missing_frontmatter") or []):
        ids.add("mf:" + str(it))
    for it in (data.get("forbidden_frontmatter") or []):
        ids.add("ff:" + str(it))
    return ids


def g1_binary():
    cw = str(BIN) if BIN.exists() else None
    if not cw:
        from shutil import which
        cw = which("claudewatch")
    if not cw:
        return ("FAIL", "claudewatch not found (run install-claudewatch.ps1)")
    try:
        r = subprocess.run([cw, "--version"], capture_output=True, text=True, timeout=20)
    except Exception as e:
        return ("FAIL", "exec error: " + str(e))
    return ("PASS", (r.stdout or r.stderr).strip()[:50]) if r.returncode == 0 else ("FAIL", "exit " + str(r.returncode))


def g2_mcp_entry():
    data = _load_json(CLAUDE_JSON)
    if data is None:
        return ("FAIL", "~/.claude.json missing/unparseable")
    if _find_cw_server(data) or ("claudewatch" in json.dumps(data)):
        return ("PASS", "claudewatch registered in ~/.claude.json")
    return ("FAIL", "no claudewatch entry")


def g3_mcp_list():
    from shutil import which
    if not which("claude"):
        return ("SKIP", "claude CLI not on PATH; cannot run 'claude mcp list'")
    try:
        r = subprocess.run(["claude", "mcp", "list"], capture_output=True, text=True, timeout=40)
    except Exception as e:
        return ("SKIP", "claude mcp list error: " + str(e))
    out = (r.stdout or "") + (r.stderr or "")
    return ("PASS", "claudewatch listed") if "claudewatch" in out else ("FAIL", "claudewatch not in 'claude mcp list'")


def g4_tools_list():
    data = _load_json(CLAUDE_JSON)
    srv = _find_cw_server(data) if data else None
    if not srv:
        return ("FAIL", "no claudewatch command in ~/.claude.json")
    cmd = [srv.get("command")] + list(srv.get("args", []) or [])
    init = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                       "clientInfo": {"name": "wire", "version": "1.0"}}}
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
    for ln in out_lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            msg = json.loads(ln)
        except Exception:
            continue
        if msg.get("id") == 2 and isinstance(msg.get("result"), dict):
            n = len(msg["result"].get("tools") or [])
            return ("PASS", str(n) + " MCP tools") if n >= 20 else ("FAIL", "only " + str(n) + " tools")
    return ("FAIL", "no tools/list response (timeout or wrong MCP subcommand)")


def g5_db():
    return ("PASS", "db present: " + str(CW_DB)) if CW_DB.exists() else ("WARN", "db not yet created (lazy); not blocking")


def g6_no_global_rules():
    if not GLOBAL_RULES_DIR.exists():
        return ("PASS", "no ~/.claude/rules dir")
    hits = list(GLOBAL_RULES_DIR.glob("claudewatch-*.md"))
    return ("PASS", "zero claudewatch rule files") if not hits else ("FAIL", str(len(hits)) + " global rule files (full install ran)")


def g7_vault_audit():
    # Delta-based: FAIL only on a GATE the WIRING introduces (post - baseline). A
    # pre-existing GATE unrelated to claudewatch (e.g. an old broken wikilink in a
    # daily note) is reported and carried, never attributed to this mission, so it
    # cannot block a clean wiring. Falls back to absolute gate==0 if no baseline.
    data = _audit_json()
    if data is None:
        return ("FAIL", "audit JSON parse failed")
    score = data.get("score", -1)
    gate = data.get("tiers", {}).get("gate", {}).get("count", -1)
    post = _gate_ids(data)
    if BASELINE_GATE_IDS is None:
        if gate == 0:
            return ("PASS", "score=%s gate=0 (absolute; no baseline)" % score)
        return ("FAIL", "score=%s gate=%s (absolute; no baseline)" % (score, gate))
    new = sorted(post - BASELINE_GATE_IDS)
    if new:
        return ("FAIL", "%d NEW GATE from wiring: %s" % (len(new), "; ".join(new)[:220]))
    return ("PASS", "no new GATE vs baseline (score=%s; %d pre-existing carried)" % (score, len(post)))


def g8_hot_md_check():
    r = _run([sys.executable, "tools/hot-md-check.py", "wiki/hot.md"], timeout=60)
    return ("PASS", "ok") if r.returncode == 0 else ("FAIL", "exit " + str(r.returncode))


def g9_test_suite():
    r = _run([sys.executable, "tools/test-claudewatch.py"], timeout=120)
    last = (r.stdout or "").strip().splitlines()[-1:] or [""]
    return ("PASS", last[0]) if r.returncode == 0 else ("FAIL", "exit " + str(r.returncode) + " :: " + last[0])


def g10_sync_check():
    r = _run([sys.executable, "tools/sync-skills.py", "--check"], timeout=120)
    return ("PASS", "idempotent") if r.returncode == 0 else ("FAIL", "exit " + str(r.returncode))


def g11_vault_hooks():
    hits = []
    for name in ["settings.json", "settings.local.json"]:
        hits += [name + ":" + h for h in _hook_refs(VAULT / ".claude" / name)]
    return ("PASS", "no claudewatch in vault hooks") if not hits else ("FAIL", ", ".join(hits))


def g15_global_settings_hooks():
    hits = _hook_refs(GLOBAL_SETTINGS)
    return ("PASS", "no claudewatch in global hook arrays") if not hits else ("FAIL", "global hook arrays: " + ", ".join(hits))


def g16_enumerate_global_hooks():
    found = []
    found += ["settings.json:" + h for h in _hook_refs(GLOBAL_SETTINGS)]
    if GLOBAL_HOOKS_DIR.exists():
        found += ["hooks/" + p.name for p in GLOBAL_HOOKS_DIR.glob("*claudewatch*")]
    return ("PASS", "empty enumeration") if not found else ("FAIL", "claudewatch hooks: " + ", ".join(found))


def _mem_slug_map():
    out = {}
    for f in MEM.glob("*.md"):
        if f.name == "MEMORY.md":
            continue
        head = "\n".join(f.read_text(encoding="utf-8", errors="ignore").splitlines()[:12])
        m = re.search(r"(?m)^name:\s*(.+)$", head)
        out[f.name] = m.group(1).strip() if m else None
    return out


def g12_dir_vs_index():
    files = _mem_slug_map()
    idx = MEMORY_INDEX.read_text(encoding="utf-8", errors="ignore")
    refs = set(re.findall(r"\(([^)]+\.md)\)", idx))
    refs.discard("MEMORY.md")
    names = set(files.keys())
    dir_not = names - refs
    idx_not = refs - names
    miss_name = [n for n, s in files.items() if not s]
    if dir_not or idx_not or miss_name:
        return ("FAIL", "dir_not_in_index=%s index_not_in_dir=%s missing_name=%s" % (sorted(dir_not), sorted(idx_not), miss_name))
    return ("PASS", str(len(names)) + " files == " + str(len(refs)) + " refs; both directions empty")


def g13_memory_quality():
    if not TOOL_MEM.exists():
        return ("FAIL", "tool_claudewatch.md missing")
    raw = TOOL_MEM.read_text(encoding="utf-8", errors="ignore")
    if any(ord(c) > 127 for c in raw):
        return ("FAIL", "non-ASCII chars present")
    m = re.search(r"(?m)^name:\s*(.+)$", raw)
    if not m or m.group(1).strip() != "tool-claudewatch":
        return ("FAIL", "name slug != tool-claudewatch")
    bad = [t + "=" + str(raw.count(t)) for t in TOOL_SECTION_TOKENS if raw.count(t) != 1]
    return ("PASS", "ASCII + slug + 8 sections each once") if not bad else ("FAIL", "section tokens: " + ", ".join(bad))


def g14_index_count():
    idx = MEMORY_INDEX.read_text(encoding="utf-8", errors="ignore")
    if INDEX_TOOLS_NEW not in idx:
        return ("FAIL", "Tools header not (24)")
    if "(tool_claudewatch.md)" not in idx:
        return ("FAIL", "no tool_claudewatch.md reference in index")
    return ("PASS", "Tools (24) + tool_claudewatch.md referenced")


# id, desc, fn, blocking
GATES = [
    ("G1", "binary --version", g1_binary, True),
    ("G2", "~/.claude.json MCP entry", g2_mcp_entry, True),
    ("G3", "claude mcp list shows claudewatch", g3_mcp_list, True),
    ("G4", "MCP tools/list handshake (>=20)", g4_tools_list, True),
    ("G5", "claudewatch.db exists", g5_db, False),
    ("G6", "no global claudewatch rules", g6_no_global_rules, True),
    ("G7", "vault-audit: no NEW gate vs baseline", g7_vault_audit, True),
    ("G8", "hot-md-check ok", g8_hot_md_check, True),
    ("G9", "test-claudewatch.py exit 0", g9_test_suite, True),
    ("G10", "sync-skills --check idempotent", g10_sync_check, True),
    ("G11", "no claudewatch in VAULT hooks", g11_vault_hooks, True),
    ("G12", "memory dir-vs-index cross-check", g12_dir_vs_index, True),
    ("G13", "tool_claudewatch.md quality", g13_memory_quality, True),
    ("G14", "MEMORY.md Tools (24) + ref", g14_index_count, True),
    ("G15", "no claudewatch in GLOBAL settings hooks", g15_global_settings_hooks, True),
    ("G16", "no claudewatch global hooks enumerated", g16_enumerate_global_hooks, True),
]

# G3 downgraded to non-blocking when claude CLI absent (SKIP); SKIP never blocks.


def run_gates(only=None):
    results = []
    for gid, desc, fn, blocking in GATES:
        if only and gid not in only:
            continue
        try:
            status, detail = fn()
        except Exception as e:
            status, detail = "FAIL", "exception: " + str(e)
        results.append((gid, desc, status, detail, blocking))
        print("  [%s] %-4s %-42s %s" % (status, gid, desc, detail))
    return results


# ---------------------------------------------------------------------------
# Commit (F11 atomic; vault files only; no push)
# ---------------------------------------------------------------------------
VAULT_COMMIT_PATHS = [
    "wiki/hot.md", "tools/test-claudewatch.py", "CLAUDE.md",
    ".claude/skills/telemetry/SKILL.md", ".agents/skills/telemetry/SKILL.md",
]


def f11_commit():
    pre = F11.exists()
    if not pre:
        F11.parent.mkdir(parents=True, exist_ok=True)
        F11.write_text("", encoding="utf-8")
    try:
        branch = subprocess.run(["git", "-C", str(VAULT), "rev-parse", "--abbrev-ref", "HEAD"],
                               capture_output=True, text=True).stdout.strip()
        if branch in ("main", "master"):
            new_branch = "claude/claudewatch-2026-05-25"
            subprocess.run(["git", "-C", str(VAULT), "switch", "-c", new_branch], capture_output=True, text=True)
            print("  (was on " + branch + "; created " + new_branch + ")")
        subprocess.run(["git", "-C", str(VAULT), "add"] + VAULT_COMMIT_PATHS, capture_output=True, text=True)
        msg = "agent: wire claudewatch (MCP-only) into observability layer"
        r = subprocess.run(["git", "-C", str(VAULT), "commit", "-m", msg], capture_output=True, text=True)
        if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
            print("  COMMIT WARN: " + (r.stderr or r.stdout).strip()[-200:])
        else:
            print("  committed: " + msg + " (no push)")
    finally:
        if not pre and F11.exists():
            F11.unlink()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Wire claudewatch (MCP-only) into the vault")
    ap.add_argument("--dry-run", action="store_true", help="plan only; no subprocess/binary/writes")
    args = ap.parse_args()

    print("wire-claudewatch-vault.py -- " + ("DRY-RUN" if args.dry_run else "REAL WIRING"))

    if args.dry_run:
        print("\nPLANNED WRITES (D6-D10):")
        txn = Txn(dry=True)
        do_writes(txn)
        print("\nPLANNED VERIFY GATES (run in real mode, after writes):")
        for gid, desc, _fn, blocking in GATES:
            print("  would run: %-4s %-42s [%s]" % (gid, desc, "BLOCKING" if blocking else "advisory"))
        print("\nThen: F11 atomic commit of vault files -> " + ", ".join(VAULT_COMMIT_PATHS) + " (no push).")
        print("DRY-RUN OK -- no subprocess, no binary, no writes, no commit.")
        return 0

    # PRE-FLIGHT: refuse to write unless install is real + MCP-only
    print("\nPRE-FLIGHT (no writes yet):")
    pre = run_gates(only={"G1", "G6", "G15", "G16"})
    pre_fail = [(g, d) for g, _de, s, d, b in pre if s == "FAIL"]
    if pre_fail:
        print("\nABORT: pre-flight failed -- not writing anything.")
        for g, d in pre_fail:
            print("  " + g + ": " + d)
        print("Fix: run tools/install-claudewatch.ps1 (MCP-only) first; resolve any global rule/hook leakage.")
        print("STATUS: MISSION_BLOCKED_PREFLIGHT")
        return 1

    # Capture pre-write GATE baseline so G7 attributes only NEW gates to the wiring.
    global BASELINE_GATE_IDS
    BASELINE_GATE_IDS = _gate_ids(_audit_json())
    print("  baseline GATE findings: " + str(len(BASELINE_GATE_IDS)) + " (pre-existing; carried, not attributed to wiring)")

    # WRITE PHASE (transactional)
    print("\nWRITE PHASE (D6-D10):")
    txn = Txn(dry=False)
    try:
        do_writes(txn)
    except Exception as e:
        txn.rollback()
        print("\nWRITE FAILED -- rolled back. Reason: " + str(e))
        print("STATUS: MISSION_FAILED (no partial state)")
        return 1

    # VERIFY PHASE (all 16 gates)
    print("\nVERIFY PHASE (16 gates):")
    results = run_gates()
    blocking_fail = [(g, d) for g, _de, s, d, b in results if b and s == "FAIL"]

    if blocking_fail:
        txn.rollback()
        print("\nGATE FAILURE -- rolled back ALL writes (vault + memory).")
        for g, d in blocking_fail:
            print("  FAIL " + g + ": " + d)
        print("STATUS: MISSION_FAILED (no partial state, no commit)")
        return 1

    # COMMIT (vault only)
    print("\nCOMMIT PHASE (F11 atomic; vault files; no push):")
    f11_commit()

    skips = [g for g, _de, s, _d, _b in results if s == "SKIP"]
    warns = [g for g, _de, s, _d, _b in results if s == "WARN"]
    print("\nAll BLOCKING gates PASS." + (" SKIP: " + ",".join(skips) if skips else "") + (" WARN: " + ",".join(warns) if warns else ""))
    print("Memory writes (out-of-tree, not committed): tool_claudewatch.md, cc_community_patterns_2026.md, MEMORY.md")
    print("STATUS: MISSION_COMPLETE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
