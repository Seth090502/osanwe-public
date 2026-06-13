#!/usr/bin/env python3
"""
PreToolUse pre-write-validator (CAT-1 fix + timeout HALT + content-hash cache).

Per Plan #1 sec 3.2 of wiki/research/vault-prevention-architecture-2026-04-27.md.
Closes the catastrophic race condition where PostToolUse exit-2 could not roll
back the file write and auto-commit (with --no-verify and || true) landed broken
state in git history regardless.

This validator runs at PreToolUse, BEFORE the Write/Edit/MultiEdit tool actually
executes. Exit 2 here means the tool call is BLOCKED -- the file mutation
never happens, auto-commit never fires, broken state never reaches disk.

Validation logic:
- For Write: simulate post-write content from tool_input.content
- For Edit: read current file, apply old_string -> new_string substitution
- For MultiEdit: apply edits sequentially against current file
- Run vault-audit.py --scope on the simulated content via tmp file
- Exit 2 if GATE findings (broken-wikilinks, missing-frontmatter,
  forbidden-frontmatter-fields) introduced by the proposed change

Quality Sweep 1 (2026-05-06) changes:
- Subprocess timeout HALTs (exit 2) instead of silent-pass (exit 0). Closes
  the primary GATE bypass under Windows slow-startup load. Default timeout
  raised 12s -> 20s; tunable via CLAUDE_PRE_WRITE_TIMEOUT_SEC env var.
- Subprocess JSON-parse failure HALTs (exit 2). Was previously silent-pass.
- Content-hash memo cache at .claude/state/pre-write-cache.json:
    * key = sha256 of simulated post-write content
    * value = {ts, gate_count, diagnostics}
    * TTL: 24h (mandatory eviction every invocation BEFORE lookup)
    * Cap: 1000 entries (FIFO eviction by ts on overflow)
  Idempotent re-edits skip the expensive vault-audit subprocess entirely.
  Override: --no-cache flag (for testing/debug).
- Cache statistics surface in --json output: cache_hit, cache_age_seconds,
  cache_size, evicted_count.

Bypass: CLAUDE_VAULT_BYPASS_VALIDATOR=1 (logged to .claude/state/bypasses-DATE.log).
Skipped: non-md/.base files, exempt dirs, files outside vault root.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, date, timedelta
from pathlib import Path

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", os.getcwd()))
EXEMPT_DIRS = {"_archive", "_quarantine", ".claude", ".agents", ".codex", ".git", "node_modules", ".checkpoints"}
EXEMPT_PATHS = {
    "CLAUDE.md", "CLAUDE.local.md",
    "AGENTS.md", "AGENTS.override.md", "AGENTS.override.md.template",
    "docs/PROJECT-OSANWE-PACKET.md", "docs/VAULT-HANDOFF-V16.md",
    "docs/CODEX-COMPATIBILITY.md",
    "docs/fs-watcher.md",  # docs file, no frontmatter required; precheck false-positive
    "tools/CODEX_TOOLS_UNVERIFIED.md",
    "tools/migrations/README.md",
    "tools/migrations/group-30-verification-report.md",
}
EXEMPT_PATH_PREFIXES = (
    "wiki/maintenance/",
    "Calendar/decisions/",
)
PRECHECK_DIR = VAULT_ROOT / "wiki" / "research" / "test-tmp" / ".precheck"

DEFAULT_TIMEOUT_SEC = 20  # raised from 12s to absorb Windows cold-start variance
TIMEOUT_ENV_VAR = "CLAUDE_PRE_WRITE_TIMEOUT_SEC"

CACHE_PATH = VAULT_ROOT / ".claude" / "state" / "pre-write-cache.json"
CACHE_TTL_HOURS = 24
CACHE_MAX_ENTRIES = 1000


def get_timeout_sec() -> int:
    """Resolve subprocess timeout from env var; fall back to DEFAULT_TIMEOUT_SEC."""
    raw = os.environ.get(TIMEOUT_ENV_VAR, "")
    if raw.isdigit():
        return max(1, int(raw))
    return DEFAULT_TIMEOUT_SEC


def log_bypass(rel_path: str, reason: str):
    bypass_log = VAULT_ROOT / ".claude" / "state" / f"bypasses-{date.today().isoformat()}.log"
    bypass_log.parent.mkdir(exist_ok=True, parents=True)
    with bypass_log.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} pre-write-validator {rel_path}: {reason}\n")


def log_silent_exit(reason: str):
    """Log silent-pass cases that previously exited 0 without trail (Reviewer B G-2/G-3 fix).
    NOTE: post-Quality-Sweep-1 the only remaining silent-exit cases are simulation-None
    and skipped-tool-name. Subprocess timeout/parse-fail now HALT (exit 2) per Phase 3."""
    bypass_log = VAULT_ROOT / ".claude" / "state" / f"bypasses-{date.today().isoformat()}.log"
    try:
        bypass_log.parent.mkdir(exist_ok=True, parents=True)
        with bypass_log.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} pre-write-validator silent-exit: {reason}\n")
    except OSError:
        pass


def simulate_post_write_content(tool_name: str, tool_input: dict, fp: Path):
    """Build the post-edit content without actually writing to disk."""
    if tool_name == "Write":
        return tool_input.get("content", "")
    if tool_name == "Edit":
        if not fp.exists():
            return None
        try:
            current = fp.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None
        old_str = tool_input.get("old_string", "")
        new_str = tool_input.get("new_string", "")
        replace_all = tool_input.get("replace_all", False)
        if not old_str:
            return current
        if replace_all:
            return current.replace(old_str, new_str)
        return current.replace(old_str, new_str, 1)
    if tool_name == "MultiEdit":
        if not fp.exists():
            return None
        try:
            current = fp.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None
        for edit in tool_input.get("edits", []):
            old_str = edit.get("old_string", "")
            new_str = edit.get("new_string", "")
            replace_all = edit.get("replace_all", False)
            if not old_str:
                continue
            if replace_all:
                current = current.replace(old_str, new_str)
            else:
                current = current.replace(old_str, new_str, 1)
        return current
    return None


def load_cache() -> dict:
    """Load cache; return empty dict if absent, malformed, or unreadable."""
    if not CACHE_PATH.exists():
        return {}
    try:
        data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def save_cache(cache: dict):
    """Atomic write: tmp then rename. Best-effort; never raises."""
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = CACHE_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(CACHE_PATH)
    except OSError:
        pass


def evict_cache(cache: dict) -> int:
    """Mandatory eviction: drop entries >24h ago + FIFO cap at 1000.
    Returns count of entries removed. Mutates cache in place."""
    evicted = 0
    cutoff = datetime.now() - timedelta(hours=CACHE_TTL_HOURS)
    cutoff_iso = cutoff.isoformat()
    # 24h TTL eviction
    for key in list(cache.keys()):
        entry = cache[key]
        ts = entry.get("ts", "") if isinstance(entry, dict) else ""
        if ts < cutoff_iso:
            del cache[key]
            evicted += 1
    # FIFO cap (oldest by ts dropped if over 1000)
    if len(cache) > CACHE_MAX_ENTRIES:
        sorted_keys = sorted(cache.keys(),
                             key=lambda k: cache[k].get("ts", "") if isinstance(cache[k], dict) else "")
        excess = len(cache) - CACHE_MAX_ENTRIES
        for k in sorted_keys[:excess]:
            del cache[k]
            evicted += 1
    return evicted


def cache_age_seconds(entry: dict) -> int:
    """Compute age in seconds from cached entry's ts. Returns -1 if unparseable."""
    ts = entry.get("ts", "")
    try:
        cached_dt = datetime.fromisoformat(ts)
        return int((datetime.now() - cached_dt).total_seconds())
    except (ValueError, TypeError):
        return -1


def audit_simulated_content(content: str, original_rel_path: Path,
                            use_cache: bool, timeout_sec: int):
    """Validate simulated content. Returns (status, gate_count, diagnostics, meta).
       status:
         'ok'              - subprocess succeeded; gate_count and diagnostics valid
         'timeout'         - subprocess exceeded timeout_sec; HALT signal
         'parse_fail'      - subprocess returned but JSON parse failed; HALT signal
         'subprocess_fail' - other subprocess exception; HALT signal
       meta: {'cache_hit', 'cache_age_seconds', 'cache_size', 'evicted_count'}
    """
    # Compute content sha256 for cache key
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

    cache = {}
    evicted_count = 0
    if use_cache:
        cache = load_cache()
        evicted_count = evict_cache(cache)
        if sha in cache:
            entry = cache[sha]
            return ("ok",
                    int(entry.get("gate_count", 0)),
                    list(entry.get("diagnostics", [])),
                    {"cache_hit": True,
                     "cache_age_seconds": cache_age_seconds(entry),
                     "cache_size": len(cache),
                     "evicted_count": evicted_count})

    # Cache miss (or --no-cache): run subprocess
    PRECHECK_DIR.mkdir(parents=True, exist_ok=True)
    precheck_filename = f"precheck-{uuid.uuid4().hex[:12]}-{original_rel_path.stem}.md"
    precheck_path = PRECHECK_DIR / precheck_filename

    meta = {"cache_hit": False, "cache_age_seconds": -1,
            "cache_size": len(cache), "evicted_count": evicted_count}

    try:
        precheck_path.write_text(content, encoding="utf-8")
        try:
            rel_for_audit = precheck_path.relative_to(VAULT_ROOT)
        except ValueError:
            return ("subprocess_fail", 0, ["precheck path resolution failed"], meta)

        try:
            result = subprocess.run(
                ["python", str(VAULT_ROOT / "tools" / "vault-audit.py"),
                 "--scope", str(rel_for_audit), "--json"],
                cwd=str(VAULT_ROOT),
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
        except subprocess.TimeoutExpired:
            return ("timeout", 0,
                    [f"vault-audit subprocess exceeded {timeout_sec}s"], meta)
        except (FileNotFoundError, OSError) as e:
            return ("subprocess_fail", 0,
                    [f"vault-audit subprocess error: {type(e).__name__}: {e}"], meta)

        try:
            data = json.loads(result.stdout)
        except (json.JSONDecodeError, ValueError):
            return ("parse_fail", 0,
                    ["vault-audit returned non-JSON output (subprocess crashed?)"], meta)

        gate_count = data.get("tiers", {}).get("gate", {}).get("count", 0)
        diagnostics = []
        for b in data.get("broken_wikilinks", []):
            diagnostics.append(f"  [GATE/broken-wikilink] line {b['line']} -> [[{b['target']}]]")
        for f in data.get("missing_frontmatter", []):
            diagnostics.append(f"  [GATE/missing-frontmatter] {f}")

        if use_cache:
            cache[sha] = {
                "ts": datetime.now().isoformat(),
                "gate_count": gate_count,
                "diagnostics": diagnostics,
            }
            save_cache(cache)
            meta["cache_size"] = len(cache)

        return ("ok", gate_count, diagnostics, meta)
    finally:
        try:
            precheck_path.unlink()
        except (OSError, FileNotFoundError):
            pass


def emit_json_output(rel_path, status, gate_count, diagnostics, meta, blocked: bool):
    """Emit machine-readable JSON for testing/debug consumers."""
    out = {
        "tool": "pre-write-validator",
        "rel_path": str(rel_path),
        "status": status,
        "gate_count": gate_count,
        "diagnostics": diagnostics,
        "blocked": blocked,
        "cache_hit": meta.get("cache_hit", False),
        "cache_age_seconds": meta.get("cache_age_seconds", -1),
        "cache_size": meta.get("cache_size", 0),
        "evicted_count": meta.get("evicted_count", 0),
    }
    print(json.dumps(out, indent=2))


def main():
    parser = argparse.ArgumentParser(description="PreToolUse vault-content validator with content-hash cache")
    parser.add_argument("--no-cache", action="store_true",
                        help="Disable content-hash cache (force subprocess on every invocation)")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Emit machine-readable JSON to stdout (default: human stderr only)")
    args = parser.parse_args()
    use_cache = not args.no_cache
    timeout_sec = get_timeout_sec()

    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        log_silent_exit("malformed JSON stdin")
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path or tool_name not in ("Write", "Edit", "MultiEdit"):
        sys.exit(0)

    fp = Path(file_path)
    if fp.suffix not in (".md", ".base"):
        sys.exit(0)

    try:
        rel_path = fp.relative_to(VAULT_ROOT)
    except ValueError:
        sys.exit(0)

    if any(part in EXEMPT_DIRS for part in rel_path.parts):
        sys.exit(0)

    rel_str = str(rel_path).replace("\\", "/")
    if rel_str in EXEMPT_PATHS:
        sys.exit(0)

    if any(rel_str.startswith(p) for p in EXEMPT_PATH_PREFIXES):
        sys.exit(0)

    proposed_content = simulate_post_write_content(tool_name, tool_input, fp)
    if proposed_content is None:
        log_silent_exit(f"simulation returned None for {tool_name} on {rel_path}")
        sys.exit(0)

    status, gate_count, diagnostics, meta = audit_simulated_content(
        proposed_content, rel_path, use_cache=use_cache, timeout_sec=timeout_sec
    )

    # Track 1 fix: subprocess timeout / parse-fail now HALT instead of silent-pass.
    # Closes the primary GATE bypass under slow-startup load. Bypass via env var.
    if status in ("timeout", "parse_fail", "subprocess_fail"):
        if os.environ.get("CLAUDE_VAULT_BYPASS_VALIDATOR") == "1":
            log_bypass(str(rel_path),
                       f"{status} bypassed via env (timeout={timeout_sec}s)")
            if args.json_output:
                emit_json_output(rel_path, status, gate_count, diagnostics, meta, blocked=False)
            sys.exit(0)

        msg = (
            f"pre-write-validator: TIMEOUT/PARSE-FAIL on vault-audit subprocess for {rel_path}\n"
            f"  status: {status} (timeout={timeout_sec}s; tunable via {TIMEOUT_ENV_VAR})\n"
            + "\n".join(diagnostics) + "\n"
            f"\nThe write is BLOCKED conservatively because GATE state cannot be verified.\n"
            f"Bypass: CLAUDE_VAULT_BYPASS_VALIDATOR=1 (logs to .claude/state/bypasses-<date>.log)\n"
            f"Tune: {TIMEOUT_ENV_VAR}=<seconds> (default {DEFAULT_TIMEOUT_SEC})\n"
        )
        print(msg, file=sys.stderr)
        if args.json_output:
            emit_json_output(rel_path, status, gate_count, diagnostics, meta, blocked=True)
        sys.exit(2)

    # Status == 'ok' from here; standard GATE check
    if gate_count == 0:
        if args.json_output:
            emit_json_output(rel_path, status, gate_count, diagnostics, meta, blocked=False)
        sys.exit(0)

    if os.environ.get("CLAUDE_VAULT_BYPASS_VALIDATOR") == "1":
        log_bypass(str(rel_path), f"{gate_count} GATE finding(s) bypassed")
        if args.json_output:
            emit_json_output(rel_path, status, gate_count, diagnostics, meta, blocked=False)
        sys.exit(0)

    msg = (
        f"pre-write-validator: {gate_count} GATE finding(s) detected in proposed {tool_name} on {rel_path}\n"
        + "\n".join(diagnostics) + "\n"
        + "\nThe write is BLOCKED before disk mutation. Fix options:\n"
        + "  (1) correct target name to match an existing vault file basename\n"
        + "  (2) de-link to plain text (remove brackets) for non-navigable references\n"
        + "  (3) wrap illustrative wikilinks in `inline code` or fenced ``` blocks\n"
        + "  (4) for auto-memory targets use [[memory:<stem>]] grammar\n"
        + "  (5) prepend canonical frontmatter for new wiki/Calendar/Efforts/Atlas files\n"
        + "Bypass: CLAUDE_VAULT_BYPASS_VALIDATOR=1 (logs to .claude/state/bypasses-<date>.log)\n"
    )
    print(msg, file=sys.stderr)
    if args.json_output:
        emit_json_output(rel_path, status, gate_count, diagnostics, meta, blocked=True)
    sys.exit(2)


if __name__ == "__main__":
    main()
