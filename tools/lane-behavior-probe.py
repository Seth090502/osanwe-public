#!/usr/bin/env python3
"""Local fake-provider behavioral probes bound to exact installed Claude bytes.

No native subscription inference occurs. No credentials are read. Requests are
sent to a loopback HTTP server using a synthetic key in an isolated config dir.
The receipt attests to observed client mechanics, not native model reliability.
"""
import argparse
import datetime as dt
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import uuid

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = "osanwe.lane-behavior/1"
MODEL = "claude-opus-5"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class Provider(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, usage):
        super().__init__(("127.0.0.1", 0), Handler)
        self.usage = usage
        self.requests = []
        self.tool_path = None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        if self.path.endswith("count_tokens"):
            payload = json.dumps({"input_tokens": 100}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(payload)
            return
        messages = body.get("messages", [])
        encoded = json.dumps(messages).lower()
        compact = "summar" in encoded or "context window" in encoded
        row = {"model": body.get("model"), "max_tokens": body.get("max_tokens"),
               "effort": (body.get("output_config") or {}).get("effort"),
               "compact_request": compact, "message_count": len(messages),
               "path": self.path}
        self.server.requests.append(row)
        use_tool = bool(self.server.tool_path and len(self.server.requests) == 1 and not compact)
        usage = 100 if compact else self.server.usage
        message = {"id": "msg_synthetic_" + uuid.uuid4().hex, "type": "message", "role": "assistant",
                   "model": body.get("model"), "content": [], "stop_reason": None,
                   "stop_sequence": None, "usage": {"input_tokens": usage,
                       "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 1}}
        answer = "Synthetic compacted context." if compact else "PROBE_OK"
        content = {"type": "tool_use", "id": "synthetic_read", "name": "Read", "input": {}} if use_tool else {"type": "text", "text": ""}
        delta = {"type": "input_json_delta", "partial_json": json.dumps({"file_path": self.server.tool_path})} if use_tool else {"type": "text_delta", "text": answer}
        self.send_response(200)
        if body.get("stream"):
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            events = [("message_start", {"type": "message_start", "message": message}),
                      ("content_block_start", {"type": "content_block_start", "index": 0,
                                              "content_block": content}),
                      ("content_block_delta", {"type": "content_block_delta", "index": 0,
                                              "delta": delta}),
                      ("content_block_stop", {"type": "content_block_stop", "index": 0}),
                      ("message_delta", {"type": "message_delta", "delta": {"stop_reason": "tool_use" if use_tool else "end_turn", "stop_sequence": None},
                                         "usage": {"input_tokens": usage, "cache_creation_input_tokens": 0,
                                                   "cache_read_input_tokens": 0, "output_tokens": 5}}),
                      ("message_stop", {"type": "message_stop"})]
            for name, value in events:
                self.wfile.write(("event: " + name + "\ndata: " + json.dumps(value) + "\n\n").encode())
                self.wfile.flush()
        else:
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            message.update(content=[{"type": "text", "text": answer}], stop_reason="end_turn")
            message["usage"]["output_tokens"] = 5
            self.wfile.write(json.dumps(message).encode())


def run_case(exe, output_tokens, usage=100, compact_window=100000, two_turns=False, timeout=40, trigger_tool=False):
    provider = Provider(usage)
    thread = threading.Thread(target=provider.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix="osanwe-lane-probe-") as temp:
            work = Path(temp)
            settings = {"disableAllHooks": True, "autoMemoryEnabled": False, "autoCompactEnabled": True, "env": {
                "CLAUDE_CODE_MAX_OUTPUT_TOKENS": str(output_tokens),
                "CLAUDE_CODE_AUTO_COMPACT_WINDOW": str(compact_window),
                "CLAUDE_CODE_EFFORT_LEVEL": "xhigh"}}
            (work / "settings.json").write_text(json.dumps(settings))
            (work / "mcp.json").write_text('{"mcpServers": {}}')
            config = work / "config"
            config.mkdir()
            (config / ".claude.json").write_text(json.dumps({"autoCompactEnabled": True,
                "hasCompletedOnboarding": True, "bypassPermissionsModeAccepted": False}))
            (work / ".claude.json").write_text(json.dumps({"autoCompactEnabled": True,
                "hasCompletedOnboarding": True}))
            if trigger_tool:
                (work / "synthetic.txt").write_text("Synthetic probe fixture.\n")
                provider.tool_path = str(work / "synthetic.txt")
            env = {key: value for key, value in os.environ.items()
                   if not key.upper().startswith(("ANTHROPIC", "CLAUDE", "OPENAI", "CODEX"))}
            env.update(ANTHROPIC_BASE_URL="http://127.0.0.1:%s" % provider.server_port,
                       ANTHROPIC_API_KEY="synthetic-local-probe-only",
                       CLAUDE_CONFIG_DIR=str(config), CLAUDE_CODE_EFFORT_LEVEL="xhigh",
                       HOME=str(work), USERPROFILE=str(work),
                       CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1",
                       CLAUDE_CODE_DISABLE_AUTO_MEMORY="1", DISABLE_AUTOUPDATER="1")
            command = [str(exe), "-p", "--model", MODEL, "--effort", "xhigh",
                       "--restricted", "--permission-mode", "dontAsk", "--tools", "Read" if trigger_tool else "",
                       "--disable-slash-commands", "--strict-mcp-config", "--mcp-config", str(work / "mcp.json"),
                       "--settings", str(work / "settings.json"), "--no-session-persistence",
                       "--output-format", "stream-json", "--verbose", "--system-prompt", "Synthetic client mechanics probe."]
            if trigger_tool:
                command.extend(["--allowedTools", "Read"])
            if two_turns:
                command.extend(["--input-format", "stream-json"])
                prompt = "\n".join(json.dumps({"type": "user", "message": {"role": "user", "content": text}})
                                   for text in ("Reply PROBE_OK.", "Reply PROBE_OK again.")) + "\n"
            else:
                prompt = "Reply PROBE_OK."
            try:
                proc = subprocess.run(command, cwd=work, env=env, input=prompt,
                                      capture_output=True, text=True, encoding="utf-8", errors="replace",
                                      timeout=timeout, creationflags=NO_WINDOW)
                code = proc.returncode
                compact_boundary = any('"compact_boundary"' in line for line in proc.stdout.splitlines())
                # This is synthetic output only, but save only typed mechanics.
                result_seen = any('"type":"result"' in line.replace(" ", "") for line in proc.stdout.splitlines())
                reason = "completed" if code == 0 and result_seen else "client_failed"
            except subprocess.TimeoutExpired:
                code, result_seen, reason, compact_boundary = None, False, "timeout", False
            return {"requested_output_tokens": output_tokens, "reported_input_usage": usage,
                    "compact_window": compact_window, "two_turns": two_turns, "trigger_tool": trigger_tool,
                    "exit_code": code, "result_seen": result_seen, "reason": reason,
                    "requests": provider.requests,
                    "compacted": compact_boundary or any(r["compact_request"] for r in provider.requests)}
    finally:
        provider.shutdown()
        provider.server_close()


def probe(exe, include_compaction=True):
    exe = Path(exe).resolve()
    before = sha(exe)
    version = subprocess.run([str(exe), "--version"], capture_output=True, text=True,
                             timeout=15, creationflags=NO_WINDOW).stdout.strip()
    cases = []
    for request in (100000, 150000, 262144):
        cases.append(run_case(exe, request))
    if include_compaction:
        # A bracket is measured, not an exact 33,000-token claim. Repeated
        # deterministic probes detect a semantically changed trigger.
        for usage in (65976, 68024):
            cases.append(run_case(exe, 32000, usage=usage, trigger_tool=True))
    caps = []
    for case in cases[:3]:
        primary = [r["max_tokens"] for r in case["requests"] if r["model"] == MODEL and not r["compact_request"]]
        caps.append(primary[0] if primary else None)
    controls = {
        "output_cap": {"state": "passed" if caps == [100000, 128000, 128000] else "failed",
                       "expected": [100000, 128000, 128000], "observed": caps},
        "request_identity": {"state": "passed" if all(c["exit_code"] == 0 and c["result_seen"] and
                                  any(r["model"] == MODEL and r["effort"] == "xhigh" for r in c["requests"])
                                  for c in cases) else "failed"},
        "compaction_bracket": {"state": "passed" if include_compaction and not cases[3]["compacted"] and
                                  cases[4]["compacted"] else "failed" if include_compaction else "unavailable",
                               "declared_window": 100000,
                               "reported_usage_no_compact": 65976, "reported_usage_compact": 68024,
                               "exact_reserve": "not_established"}}
    after = sha(exe)
    controls["binary_unchanged"] = {"state": "passed" if before == after else "failed"}
    return {"schema": SCHEMA, "classification": "synthetic", "scope": "fake-provider-client-mechanics",
            "verified_at": dt.datetime.now(dt.timezone.utc).isoformat(), "binary_sha256": before,
            "binary_version": version, "probe_code_sha256": sha(__file__),
            "state": "passed" if all(c["state"] == "passed" for c in controls.values()) else "failed",
            "controls": controls, "cases": cases, "native_subscription": "not_run", "native_resume": "not_run",
            "limits": ["Synthetic provider usage is controlled, not native subscription evidence.",
                       "The compaction boundary is bracketed; other tool/config semantics are not certified.",
                       "The receipt is local development evidence, not an independent attestation."]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exe", type=Path, default=Path.home() / ".local/bin/claude.exe")
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--output-only", action="store_true", help="diagnostic; cannot authorize lane acceptance")
    args = ap.parse_args(argv)
    if args.output.exists():
        ap.error("receipt exists; choose a new path")
    result = probe(args.exe, not args.output_only)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"state": result["state"], "controls": result["controls"], "evidence": str(args.output)}))
    return 0 if result["state"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
