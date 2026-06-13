"""tools/lib/hook_payload.py -- Mission Four (2026-05-15)

Defensive stdin payload parser for hook scripts. Tries the Claude schema first
(tool_input.file_path), falls back to candidate Codex field names if those fail.
Logs schema-miss events to .claude/state/codex-schema-probe-<date>.jsonl so Phase 0.5+
empirical probing populates the true Codex field-name registry from real traffic.

Per Phase 0 V3 re-verify (developers.openai.com/codex/hooks):
  Codex PostToolUse stdin documents fields: turn_id, tool_name, tool_use_id,
  tool_input, tool_response. The tool_response field replaces Claude's
  tool_input.file_path semantic for "what got affected" -- but tool_input may
  still carry the call args including paths. Parser tries both.

Bypass-env-var helper bypass_active(claude_var, osanwe_var=None) implements the
dual-read pattern documented in AGENTS.md: returns True if either env var == "1".

Usage in a Python hook script:
    from tools.lib.hook_payload import parse_hook_payload, bypass_active
    payload = parse_hook_payload(sys.stdin.read())
    if not payload.file_path:
        sys.exit(0)
    if bypass_active("CLAUDE_VAULT_BYPASS_VALIDATOR", "OSANWE_VAULT_BYPASS_VALIDATOR"):
        sys.exit(0)
    # ... validate payload.file_path ...
"""
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", os.getcwd()))
SCHEMA_PROBE_LOG = VAULT_ROOT / ".claude" / "state" / f"codex-schema-probe-{date.today().isoformat()}.jsonl"


@dataclass
class HookPayload:
    """Normalized hook payload. All str fields default to empty string (not None) so
    downstream `if not field` guards work uniformly."""
    tool_name: str = ""
    file_path: str = ""
    content: str = ""
    old_string: str = ""
    new_string: str = ""
    edits: list = field(default_factory=list)
    raw: dict = field(default_factory=dict)
    schema_origin: str = "unknown"  # 'claude' | 'codex' | 'unknown'


def _log_schema_probe(raw: dict, origin: str, fields_present: list[str]):
    """Append schema observation to probe log. Best-effort; never raises."""
    try:
        SCHEMA_PROBE_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now().isoformat(),
            "origin": origin,
            "engine": os.environ.get("OSANWE_ENGINE", "unknown"),
            "fields_present": fields_present,
            "tool_name": raw.get("tool_name") or raw.get("tool") or "",
        }
        with SCHEMA_PROBE_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def parse_hook_payload(raw_text: str) -> HookPayload:
    """Parse a hook stdin JSON payload defensively.

    Tries Claude schema first: tool_name + tool_input.{file_path, content,
    old_string, new_string, edits}. Falls back to candidate Codex schemas:
      Codex try 1: tool_name + tool_input.{file_path, ...} (same as Claude)
      Codex try 2: name + input.{path, content, ...}
      Codex try 3: tool + parameters.{path, ...}

    Returns HookPayload(...) with empty strings for missing fields.
    """
    try:
        data = json.loads(raw_text)
    except (json.JSONDecodeError, ValueError):
        return HookPayload()

    if not isinstance(data, dict):
        return HookPayload()

    # Claude (and Codex if it adopts the same schema): tool_name + tool_input
    if "tool_name" in data and "tool_input" in data:
        ti = data.get("tool_input") or {}
        fields = list(ti.keys()) if isinstance(ti, dict) else []
        # Probe-log only if engine is Codex and field set diverges (worth knowing)
        if os.environ.get("OSANWE_ENGINE") == "codex":
            _log_schema_probe(data, "claude-schema-under-codex", fields)
        return HookPayload(
            tool_name=data.get("tool_name", ""),
            file_path=ti.get("file_path", "") if isinstance(ti, dict) else "",
            content=ti.get("content", "") if isinstance(ti, dict) else "",
            old_string=ti.get("old_string", "") if isinstance(ti, dict) else "",
            new_string=ti.get("new_string", "") if isinstance(ti, dict) else "",
            edits=ti.get("edits", []) if isinstance(ti, dict) else [],
            raw=data,
            schema_origin="claude",
        )

    # Codex try 2: 'name' + 'input'
    if "name" in data and "input" in data:
        inp = data.get("input") or {}
        fields = list(inp.keys()) if isinstance(inp, dict) else []
        _log_schema_probe(data, "codex-name-input", fields)
        if isinstance(inp, dict):
            return HookPayload(
                tool_name=data.get("name", ""),
                file_path=inp.get("path", "") or inp.get("file_path", ""),
                content=inp.get("content", ""),
                old_string=inp.get("old_string", ""),
                new_string=inp.get("new_string", ""),
                edits=inp.get("edits", []),
                raw=data,
                schema_origin="codex",
            )

    # Codex try 3: 'tool' + 'parameters'
    if "tool" in data and "parameters" in data:
        params = data.get("parameters") or {}
        fields = list(params.keys()) if isinstance(params, dict) else []
        _log_schema_probe(data, "codex-tool-parameters", fields)
        if isinstance(params, dict):
            return HookPayload(
                tool_name=data.get("tool", ""),
                file_path=params.get("path", "") or params.get("file_path", ""),
                content=params.get("content", ""),
                old_string=params.get("old_string", ""),
                new_string=params.get("new_string", ""),
                edits=params.get("edits", []),
                raw=data,
                schema_origin="codex",
            )

    # Total miss: log keys for debugging
    _log_schema_probe(data, "no-known-schema", list(data.keys()))
    return HookPayload(raw=data)


def bypass_active(claude_var: str, osanwe_var: str = None) -> bool:
    """Dual-read bypass env-var check. Returns True if either var is set to "1".
    The OSANWE_* equivalent of any CLAUDE_* bypass is the migration path for
    engine-neutral bypass control without breaking Claude-side workflows.

    Usage:
        if bypass_active("CLAUDE_VAULT_BYPASS_VALIDATOR", "OSANWE_VAULT_BYPASS_VALIDATOR"):
            sys.exit(0)
    """
    if os.environ.get(claude_var) == "1":
        return True
    if osanwe_var and os.environ.get(osanwe_var) == "1":
        return True
    return False
