#!/usr/bin/env python3
"""Explicit native subscription/resume probe; never part of scheduled monitoring.

Uses only synthetic nonces and a single read-only control file, with the requested
Claude Opus 5/xhigh route. Session persistence is necessary for this test. Receipts
retain only allowlisted mechanics and synthetic outputs, never raw auth/provider
streams or account identifiers. They are client-reported observations.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import uuid

from fis.runtime_health import create_json, file_sha, iso_z, now_utc, NO_WINDOW

MODEL = "claude-opus-5"


def child_environment():
    env = dict(os.environ)
    for key in list(env):
        if key.upper().startswith(("ANTHROPIC_", "CLAUDE_CODE_USE_")) or key.upper() in {
            "CLAUDE_CONFIG_DIR", "CLAUDE_CODE_SIMPLE", "CLAUDE_CODE_SUBAGENT_MODEL",
            "CLAUDE_CODE_SUBAGENT_MODEL_FORCE", "FALLBACK_FOR_ALL_PRIMARY_MODELS"}:
            env.pop(key)
    env.update(CLAUDE_CODE_EFFORT_LEVEL="xhigh", CLAUDE_CODE_DISABLE_AUTO_MEMORY="1",
               CLAUDE_CODE_DISABLE_BACKGROUND_TASKS="1", CLAUDE_CODE_DISABLE_CRON="1",
               CLAUDE_CODE_DISABLE_CLAUDE_MDS="1", DISABLE_AUTOUPDATER="1")
    return env


def invocation(exe, stage, settings, mcp, session, resume=False):
    return [str(exe), "--restricted", "-p", "--model", MODEL, "--effort", "xhigh",
            "--tools", "Read", "--allowedTools", "Read", "--permission-mode", "dontAsk",
            "--disable-slash-commands", "--strict-mcp-config", "--mcp-config", str(mcp),
            "--settings", str(settings), "--max-turns", "6", "--output-format", "stream-json", "--verbose",
            "--resume" if resume else "--session-id", session]


def is_control_read(call, stage):
    if call.get("name") != "Read" or not call.get("path"):
        return False
    candidate = Path(call["path"])
    if not candidate.is_absolute():
        candidate = stage / candidate
    return candidate.resolve() == (stage / "control.txt").resolve()


def execute(command, prompt, stage, env, timeout):
    start = now_utc()
    try:
        process = subprocess.run(command, input=prompt, cwd=stage, env=env,
                                 text=True, capture_output=True, encoding="utf-8", errors="replace",
                                 timeout=timeout, creationflags=NO_WINDOW)
    except subprocess.TimeoutExpired:
        return {"state": "failed", "reason": "timeout", "started_at": iso_z(start), "verified_at": iso_z(now_utc())}
    events, texts, reads, models = [], [], [], []
    result_seen = False
    successful_result = False
    for line in process.stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("subtype") == "init":
            events.append({"type": "init", "model": event.get("model"),
                           "tools": event.get("tools"), "mcp_count": len(event.get("mcp_servers") or []),
                           "permission_mode": event.get("permissionMode")})
        if event.get("type") == "assistant":
            message = event.get("message", {})
            models.append(message.get("model"))
            for block in message.get("content", []):
                if block.get("type") == "text":
                    texts.append(block.get("text", ""))
                elif block.get("type") == "tool_use":
                    reads.append({"name": block.get("name"), "path": (block.get("input") or {}).get("file_path")})
        if event.get("type") == "result":
            result_seen = True
            successful_result = event.get("is_error") is False
            events.append({"type": "result", "subtype": event.get("subtype"), "is_error": event.get("is_error"),
                           "num_turns": event.get("num_turns"), "duration_ms": event.get("duration_ms"),
                           "model_usage_keys": sorted((event.get("modelUsage") or {}).keys()),
                           "permission_denial_count": len(event.get("permission_denials") or [])})
    return {"state": "passed" if process.returncode == 0 and result_seen and successful_result else "failed",
            "exit_code": process.returncode, "started_at": iso_z(start), "verified_at": iso_z(now_utc()),
            "events": events, "assistant_models": models, "text": "\n".join(texts), "tool_calls": reads,
            "stderr_present": bool(process.stderr), "raw_streams_persisted": False}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exe", type=Path, default=Path.home() / ".local/bin/claude.exe")
    ap.add_argument("--output-dir", required=True, type=Path)
    ap.add_argument("--timeout", type=int, default=180)
    args = ap.parse_args(argv)
    root = args.output_dir.resolve()
    root.mkdir(parents=True, exist_ok=False)
    stage = root / "workspace"
    stage.mkdir()
    env = child_environment()
    digest = file_sha(args.exe)
    version = subprocess.run([str(args.exe), "--version"], env=env, capture_output=True,
                             text=True, timeout=20, creationflags=NO_WINDOW).stdout.strip()
    # Parse only safe authentication state; no raw status is retained or printed.
    auth_process = subprocess.run([str(args.exe), "auth", "status", "--json"], cwd=stage, env=env,
                                  capture_output=True, text=True, timeout=30, creationflags=NO_WINDOW)
    try:
        auth = json.loads(auth_process.stdout)
    except ValueError:
        auth = {}
    auth_state = {k: auth.get(k) for k in ("loggedIn", "authMethod", "apiProvider", "subscriptionType")}
    expected_auth = (auth_state.get("loggedIn") is True and auth_state.get("apiProvider") == "firstParty"
                     and auth_state.get("authMethod") in ("claude.ai", "oauth", "claudeAi"))
    if not expected_auth:
        receipt = {"schema": "osanwe.native-resume/1", "state": "unavailable", "reason": "native-subscription-auth-not-established",
                   "authentication": auth_state, "binary_sha256": digest, "binary_version": version}
        create_json(root / "receipt.json", receipt)
        print(json.dumps(receipt))
        return 2
    settings = root / "settings.json"
    create_json(settings, {"disableAllHooks": True, "autoMemoryEnabled": False, "effortLevel": "xhigh",
                          "permissions": {"defaultMode": "dontAsk", "blockReadsOutsideWorkingDirectories": True}})
    mcp = root / "empty-mcp.json"
    create_json(mcp, {"mcpServers": {}})
    nonce = "SYNTHETIC_" + uuid.uuid4().hex
    control = "CONTROL_" + uuid.uuid4().hex
    (stage / "control.txt").write_text(control, encoding="ascii")
    session = str(uuid.uuid4())
    first_prompt = "This is a synthetic session-persistence test. Remember this exact synthetic nonce: " + nonce + ". Reply only ACK. Do not read any files."
    first = execute(invocation(args.exe, stage, settings, mcp, session), first_prompt, stage, env, args.timeout)
    create_json(root / "first.json", first)
    second = {"state": "not_run", "reason": "first_attempt_failed"}
    if first["state"] == "passed":
        second_prompt = "This is the same synthetic session-persistence test after the prior process exited. Read only control.txt. Reply exactly with the synthetic nonce remembered from the previous turn, a vertical bar, then the control file contents. No other text."
        second = execute(invocation(args.exe, stage, settings, mcp, session, True), second_prompt, stage, env, args.timeout)
    create_json(root / "resume.json", second)
    controls = {
        "native_authentication": expected_auth,
        "first_process_completed": first["state"] == "passed",
        "resumed_process_completed": second["state"] == "passed",
        "nonce_recovered_from_session": second.get("text", "").strip() == nonce + "|" + control,
        "read_only_control_observed": any(is_control_read(c, stage) for c in second.get("tool_calls", [])),
        "no_unexpected_tools": not first.get("tool_calls") and all(is_control_read(c, stage) for c in second.get("tool_calls", [])),
        "primary_model_exact": bool(first.get("assistant_models")) and bool(second.get("assistant_models")) and
             all(model == MODEL for model in first.get("assistant_models", []) + second.get("assistant_models", [])),
        "binary_unchanged": file_sha(args.exe) == digest,
    }
    receipt = {"schema": "osanwe.native-resume/1", "state": "passed" if all(controls.values()) else "failed",
               "classification": "synthetic", "scope": "native-subscription-and-process-resume",
               "verified_at": iso_z(now_utc()), "binary_sha256": digest, "binary_version": version,
               "probe_code_sha256": file_sha(__file__), "authentication": auth_state, "controls": controls,
               "requested_model": MODEL, "requested_effort": "xhigh", "effort_attestation": "client configuration; no independent server effort attestation",
               "session_persistence": "enabled for this synthetic test", "session_id": session,
               "limits": ["This does not validate compaction semantics, financial answer quality or live connectors.",
                          "Auxiliary model usage is retained in per-attempt model_usage_keys.",
                          "Local observations are client-reported, not independent custody."]}
    create_json(root / "receipt.json", receipt)
    print(json.dumps({"state": receipt["state"], "controls": controls, "evidence": str(root / "receipt.json")}, indent=2))
    return 0 if receipt["state"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
