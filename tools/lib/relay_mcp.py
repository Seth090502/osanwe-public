"""relay_mcp -- stdlib JSON-RPC 2.0 stdio client for the relay worker's MCP surface.

GATE-B: wiki/research/gates/gate-b-relay-worker-2026-08-16.md.
Protocol prototype proven by experiment E5 (2026-08-16): openinsider cold-spawn
1.0-1.1 s, 3/3, 16 tools enumerated. No SDK, no pip dependency -- the same
newline-delimited JSON-RPC shape /path/to/local/vault-search/server.py hand-rolls.

Containment notes (mechanical, not advisory):
- Server COMMANDS come only from the static SERVER_COMMANDS table below, keyed by
  the allowlist in config/local-lane.json relay.mcp_allowlist. Nothing model-supplied
  ever reaches a process spawn.
- robinhood and claudewatch have NO entry here -- omission, not scanning (D-SEC-1).
- A tool name must be in the roster the server ADVERTISED at tools/list; a
  hallucinated name is a deterministic error, never a request.
"""
import json
import subprocess
import sys
import time

# The ONLY spawnable servers. Adding one is a config + code + gate-sheet event.
SERVER_COMMANDS = {
    "openinsider": ["npx", "-y", "openinsider-mcp@0.3.3"],
    "fred": ["node", "/path/to/home/.local/share/fred-mcp/launch.mjs"],
    # v1.1 candidate, still gated: enable ONLY after the operator-run E5
    # re-probe passes 3/3 cold spawns < 60s (uvx cache primed once manually
    # first) AND EDGAR_IDENTITY is present in the environment:
    #   "edgar-tools": ["uvx", "--from", "edgartools[ai]==5.35.1", "edgartools-mcp"],
}

# Env var NAMES each server requires (.agents/mcp/servers.json:41,:56 -- names
# only, never literals). A missing name is a spawn-time McpError -> the pool
# marks the server DOWN for the leg (never a HALT). Fail-closed even for fred's
# HKCU registry fallback: ONE visible source of truth for where keys come from.
SERVER_ENV = {
    "openinsider": [],
    "fred": ["FRED_API_KEY"],
    "edgar-tools": ["EDGAR_IDENTITY"],
}

# Windows children break without these (winsock needs SystemRoot; npx/uvx/node
# need PATH + profile dirs + temp). The child env is BASE + the named keys and
# NOTHING else -- MCP servers are third-party code and must not inherit session
# tokens or launcher state.
BASE_ENV_VARS = ("SystemRoot", "PATH", "PATHEXT", "COMSPEC", "TEMP", "TMP",
                 "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "APPDATA",
                 "LOCALAPPDATA", "PROGRAMDATA", "NUMBER_OF_PROCESSORS",
                 "PROCESSOR_ARCHITECTURE")

FORBIDDEN_NAMES = ("robinhood", "claudewatch")  # refused by NAME regardless of config


class McpError(Exception):
    pass


class McpServer:
    """One stdio child. Spawn, initialize, enumerate, call, kill."""

    def __init__(self, name, spawn_timeout_s=60):
        if any(f in name for f in FORBIDDEN_NAMES):
            raise McpError("server %r is refused by name (D-SEC-1)" % name)
        if name not in SERVER_COMMANDS:
            raise McpError("server %r has no code path" % name)
        self.name = name
        self.tools = {}          # name -> inputSchema
        self.calls_made = 0
        self._id = 0
        import os
        child_env = {k: os.environ[k] for k in BASE_ENV_VARS
                     if k in os.environ}
        for var in SERVER_ENV.get(name, []):
            if var not in os.environ:
                raise McpError("server %r requires env var %s, not set in "
                               "this process -- fail-closed" % (name, var))
            child_env[var] = os.environ[var]
        t0 = time.time()
        self.proc = subprocess.Popen(
            SERVER_COMMANDS[name], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, shell=(sys.platform == "win32"),
            env=child_env)
        try:
            self._rpc("initialize", {
                "protocolVersion": "2025-06-18", "capabilities": {},
                "clientInfo": {"name": "relay", "version": "1"}},
                deadline=t0 + spawn_timeout_s)
            self._notify("notifications/initialized")
            res = self._rpc("tools/list", None, deadline=t0 + spawn_timeout_s)
            for t in res.get("result", {}).get("tools", []):
                self.tools[t["name"]] = t.get("inputSchema") or {}
        except Exception:
            self.kill()
            raise
        if not self.tools:
            self.kill()
            raise McpError("server %r advertised zero tools" % name)
        self.spawn_s = round(time.time() - t0, 2)

    # -- wire ------------------------------------------------------------
    def _send(self, obj):
        self.proc.stdin.write((json.dumps(obj) + "\n").encode())
        self.proc.stdin.flush()

    def _notify(self, method):
        self._send({"jsonrpc": "2.0", "method": method})

    def _rpc(self, method, params, deadline=None, timeout_s=120):
        self._id += 1
        want = self._id
        msg = {"jsonrpc": "2.0", "id": want, "method": method}
        if params is not None:
            msg["params"] = params
        self._send(msg)
        deadline = deadline or (time.time() + timeout_s)
        buf = b""
        while time.time() < deadline:
            ch = self.proc.stdout.read(1)
            if not ch:
                if self.proc.poll() is not None:
                    raise McpError("server %r died mid-call" % self.name)
                time.sleep(0.01)
                continue
            buf += ch
            if ch == b"\n":
                line = buf.decode("utf-8", "replace").strip()
                buf = b""
                if not line:
                    continue
                try:
                    parsed = json.loads(line)
                except ValueError:
                    continue
                if parsed.get("id") == want:
                    return parsed
        raise McpError("timeout on %s to %r" % (method, self.name))

    # -- surface ---------------------------------------------------------
    def validate_args(self, tool, args):
        """Minimal schema check: required keys present, no unknown keys when the
        schema enumerates properties. Returns error string or None."""
        schema = self.tools.get(tool)
        if schema is None:
            return "tool %r not in %r's advertised roster %s" % (
                tool, self.name, sorted(self.tools))
        if not isinstance(args, dict):
            return "arguments must be an object"
        props = schema.get("properties")
        if isinstance(props, dict) and props:
            unknown = [k for k in args if k not in props]
            if unknown:
                return "unknown argument keys %s (allowed: %s)" % (
                    unknown, sorted(props))
        for req in schema.get("required") or []:
            if req not in args:
                return "missing required argument %r" % req
        return None

    def call(self, tool, args, max_chars=200000):
        err = self.validate_args(tool, args)
        if err:
            raise McpError(err)
        self.calls_made += 1
        res = self._rpc("tools/call", {"name": tool, "arguments": args})
        if "error" in res:
            raise McpError("server error: %s" % json.dumps(res["error"])[:400])
        out = res.get("result", {})
        parts = [c.get("text", "") for c in out.get("content", [])
                 if c.get("type") == "text"]
        text = "\n".join(parts) if parts else json.dumps(out)
        return text[:max_chars]

    def kill(self):
        """Kill the WHOLE process tree. shell=True wraps the server in cmd.exe
        on Windows; proc.kill() alone orphans the node/uvx grandchild, which
        keeps inherited pipes open (diagnosed 2026-08-17: `checkall | tail`
        hung on EOF because an orphaned node held stdout)."""
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/PID", str(self.proc.pid),
                                "/T", "/F"], capture_output=True, timeout=15)
            else:
                self.proc.kill()
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass


class McpPool:
    """Lazy pool over the ALLOWLISTED servers. A server that misses its spawn
    timeout is marked DOWN for this pool's lifetime -- never a HALT."""

    def __init__(self, allowlist, spawn_timeout_s=60, per_server_call_cap=40):
        self.allowlist = list(allowlist)
        self.spawn_timeout_s = spawn_timeout_s
        self.per_server_call_cap = per_server_call_cap
        self.servers = {}
        self.down = {}           # name -> reason

    def get(self, name):
        if name not in self.allowlist:
            raise McpError("server %r not in this leg's allowlist %s" % (
                name, self.allowlist))
        if name in self.down:
            raise McpError("server %r is DOWN for this leg: %s" % (
                name, self.down[name]))
        if name not in self.servers:
            try:
                self.servers[name] = McpServer(name, self.spawn_timeout_s)
            except Exception as exc:                          # noqa: BLE001
                self.down[name] = str(exc)
                raise McpError("server %r failed to spawn: %s" % (name, exc))
        return self.servers[name]

    def call(self, name, tool, args):
        srv = self.get(name)
        if srv.calls_made >= self.per_server_call_cap:
            raise McpError("per-server call cap (%d) reached for %r" % (
                self.per_server_call_cap, name))
        try:
            return srv.call(tool, args)
        except McpError:
            raise
        except Exception as exc:                              # noqa: BLE001
            # one respawn, then DOWN
            srv.kill()
            del self.servers[name]
            try:
                srv2 = McpServer(name, self.spawn_timeout_s)
                self.servers[name] = srv2
                return srv2.call(tool, args)
            except Exception as exc2:                         # noqa: BLE001
                self.down[name] = "crashed twice: %s / %s" % (exc, exc2)
                raise McpError(self.down[name])

    def rosters(self):
        return {n: sorted(s.tools) for n, s in self.servers.items()}

    def close(self):
        for s in self.servers.values():
            s.kill()
        self.servers.clear()
