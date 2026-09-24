#!/usr/bin/env python3
"""canary.py -- live-surface MCP canary (cross-harness migration D9).

For every registry server marked canary=spawnable*: spawn the stdio server,
run the MCP handshake, enumerate tools/list, and compare against the registry:
  - a live tool name NOT in the registry (read_tools + write_tools) => FAIL
    (the surface GREW under a static config -- the Robinhood 45->54 failure
    mode made loud instead of silent)
  - a registry name missing live => FAIL (registry stale in the other direction)
  - roster marked read_tools_unverified: enumeration PRINTS the roster to pin
    into the registry, FAILs until pinned (loud by design)
  - spawn/handshake failure => WARN (recorded, never silently skipped); offline
    work must not be blocked by a network-dependent spawn

Servers marked canary=manual (remote/interactive-auth) are listed with their
last-verified note -- re-verify procedure lives in the registry entry.

Usage: python .agents/mcp/canary.py [--only <server>] [--timeout N]
Exit 0 = no FAIL (WARNs allowed).
"""
import io
import json
import os
import subprocess
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REGISTRY = os.path.join(HERE, "servers.json")
TIMEOUT = 90


def rpc_lines(proc, messages, timeout):
    """Send newline-delimited JSON-RPC messages; collect responses until id 2 answered."""
    out = {}

    def reader():
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except Exception:
                continue
            if "id" in msg:
                out[msg["id"]] = msg
                if msg["id"] == 2:
                    return

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    for m in messages:
        proc.stdin.write(json.dumps(m) + "\n")
        proc.stdin.flush()
    t.join(timeout)
    return out


def enumerate_tools(server, timeout):
    env = dict(os.environ)
    for var in (server.get("env") or {}):
        env.setdefault(var, "canary canary-probe")
    cmd = [server["command"]] + list(server.get("args", []))
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True, env=env,
                            cwd=ROOT, shell=(os.name == "nt" and server["command"] in ("npx", "uvx")))
    try:
        msgs = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                        "clientInfo": {"name": "osanwe-canary", "version": "1.0"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        ]
        out = rpc_lines(proc, msgs, timeout)
        resp = out.get(2)
        if not resp or "result" not in resp:
            return None, "no tools/list response within %ss" % timeout
        return sorted(t["name"] for t in resp["result"].get("tools", [])), None
    finally:
        # Kill the WHOLE tree: shell=True wraps npx/uvx in cmd.exe and a bare
        # proc.kill() orphans the node grandchild, which keeps the canary's
        # inherited stdout pipe open -- `checkall | tail` then hangs on EOF
        # forever (diagnosed 2026-08-17; same fix as relay_mcp.McpServer.kill).
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                               capture_output=True, timeout=15)
            else:
                proc.kill()
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def main():
    args = sys.argv[1:]
    only = args[args.index("--only") + 1] if "--only" in args else None
    timeout = int(args[args.index("--timeout") + 1]) if "--timeout" in args else TIMEOUT
    with io.open(REGISTRY, encoding="utf-8") as f:
        servers = json.load(f)["servers"]
    fails, warns = [], []
    for name, s in sorted(servers.items()):
        if only and name != only:
            continue
        mode = s.get("canary", "manual")
        if not mode.startswith("spawnable"):
            print("[MANUAL] %s: %s" % (name, mode))
            continue
        live, err = enumerate_tools(s, timeout)
        if live is None:
            warns.append("%s: spawn/handshake failed (%s) -- surface NOT verified this run" % (name, err))
            print("[WARN] %s: %s" % (name, err))
            continue
        if s.get("read_tools_unverified"):
            fails.append("%s: roster unpinned; live enumeration = %s -- pin these into "
                         "servers.json read_tools and drop read_tools_unverified" % (name, live))
            print("[FAIL] %s: unpinned roster; live tools: %s" % (name, live))
            continue
        known = set(s.get("read_tools", [])) | set(s.get("write_tools", []))
        unknown = sorted(set(live) - known)
        missing = sorted(known - set(live))
        if unknown:
            fails.append("%s: LIVE tools not in registry: %s (surface grew -- update the "
                         "registry, re-run generators)" % (name, unknown))
        if missing:
            fails.append("%s: registry tools missing live: %s (registry stale)" % (name, missing))
        if not unknown and not missing:
            print("[OK] %s: %d tools match registry exactly" % (name, len(live)))
    for f_ in fails:
        print("[FAIL] " + f_)
    if fails:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
