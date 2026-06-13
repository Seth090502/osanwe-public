#!/usr/bin/env python3
"""
gen-codex-agents.py -- Mission Four (2026-05-15)

Generates Codex subagent TOML files at .codex/agents/<name>.toml from the
Claude-native source at .claude/agents/<name>.md.

Per developers.openai.com/codex/subagents (V2 verified Phase 0):
  - Path: .codex/agents/<name>.toml (project-scoped) OR ~/.codex/agents/ (personal)
  - Format: TOML
  - Required fields: name, description, developer_instructions
  - Optional: model, model_reasoning_effort, sandbox_mode, tools, max_turns

Field translation (Claude .md frontmatter -> Codex .toml):
  name        -> name (verbatim)
  description -> description (verbatim; preserved for description-trigger dispatch)
  tools       -> tools (verbatim TOML array; Codex tool-name equivalence unverified --
                 see tools/CODEX_TOOLS_UNVERIFIED.md)
  model       -> model with mapping:
                   opus    -> gpt-5.5  (V6: NO documented Claude->Codex mapping;
                   sonnet  -> gpt-5.4   conservative empirical choice; honest_degradation)
                   haiku   -> gpt-5.4-mini  (no haiku agents currently)
  effort      -> model_reasoning_effort with EFFORT_MAP translation:
                   low    -> "low"
                   medium -> "medium"
                   high   -> "high"
                   max    -> "xhigh"   (Codex docs only document low/medium/high/xhigh;
                                        "max" is Claude-native and would error under Codex.
                                        Mission Four-FIX M1 correction 2026-05-16.)
  body        -> developer_instructions (V2: NOT system_prompt; verbatim multi-line string)
  disallowedTools -> dropped silently (no documented Codex equivalent)
  color       -> dropped silently (no Codex equivalent)
  maxTurns    -> max_turns (3 agents affected; semantics unverified pending Phase 5)

Idempotent: re-runs produce zero diff on unchanged source.
CLI:
  python tools/gen-codex-agents.py            # full generation (14 agents)
  python tools/gen-codex-agents.py --check    # idempotency assert
  python tools/gen-codex-agents.py --verbose  # per-agent run log
"""
import argparse
import os
import re
import sys
from pathlib import Path

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", os.getcwd()))
SOURCE_ROOT = VAULT_ROOT / ".claude" / "agents"
TARGET_ROOT = VAULT_ROOT / ".codex" / "agents"

MODEL_MAP = {
    "opus": "gpt-5.5",
    "sonnet": "gpt-5.4",
    "haiku": "gpt-5.4-mini",
}

# Codex documents model_reasoning_effort as one of: low | medium | high | xhigh
# Claude-native "max" maps to Codex "xhigh" (Mission Four-FIX M1 correction 2026-05-16).
EFFORT_MAP = {
    "low": "low",
    "medium": "medium",
    "high": "high",
    "xhigh": "xhigh",
    "max": "xhigh",
}

# YAML extraction helpers (single-line scalar values; brackets-array for tools/disallowedTools)
SCALAR_RE = re.compile(r"^([\w-]+)\s*:\s*(.+)$")
ARRAY_BRACKET_RE = re.compile(r"^\[(.*)\]$")


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from a Claude agent .md file.
    Returns (fields_dict, body_str). fields_dict preserves field order via insertion.
    """
    fields = {}
    if not text.startswith("---\n"):
        return ({}, text)
    end_idx = text.find("\n---\n", 4)
    if end_idx == -1:
        return ({}, text)
    fm_block = text[4:end_idx]  # skip opening --- and closing ---
    body = text[end_idx + 5:]   # skip closing ---\n

    for line in fm_block.split("\n"):
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        m = SCALAR_RE.match(line)
        if not m:
            continue
        key, raw_val = m.group(1), m.group(2).strip()
        # Strip surrounding quotes from string values
        if (raw_val.startswith('"') and raw_val.endswith('"')) or \
           (raw_val.startswith("'") and raw_val.endswith("'")):
            raw_val = raw_val[1:-1]
        # Detect bracket-array
        ab = ARRAY_BRACKET_RE.match(raw_val)
        if ab:
            items = [s.strip().strip('"').strip("'") for s in ab.group(1).split(",") if s.strip()]
            fields[key] = items
        else:
            # Comma-list scalar (e.g., "tools: Read, Grep, Glob"): split on comma
            if "," in raw_val and key in ("tools", "disallowedTools"):
                items = [s.strip().strip('"').strip("'") for s in raw_val.split(",")]
                fields[key] = items
            else:
                fields[key] = raw_val
    return (fields, body)


def toml_escape_multiline(text: str) -> str:
    # Escape text for TOML multi-line basic string (triple-quoted form).
    # Backslashes and triple-quote sequences need escaping.
    text = text.replace("\\", "\\\\")
    text = text.replace('"""', '\\"\\"\\"')
    return text


def toml_escape_string(text: str) -> str:
    """Escape text for TOML basic string ("...")."""
    text = text.replace("\\", "\\\\")
    text = text.replace('"', '\\"')
    text = text.replace("\n", "\\n")
    text = text.replace("\r", "\\r")
    text = text.replace("\t", "\\t")
    return text


def render_toml_array(items: list[str]) -> str:
    """Render a list of strings as a TOML inline array."""
    return "[" + ", ".join(f'"{toml_escape_string(s)}"' for s in items) + "]"


def generate_toml(fields: dict, body: str, source_name: str) -> str:
    """Generate the .codex/agents/<name>.toml content from parsed Claude agent fields."""
    lines = [
        f"# Generated by tools/gen-codex-agents.py (Mission Four, 2026-05-15)",
        f"# Source: .claude/agents/{source_name}",
        f"# DO NOT EDIT this file directly. Edit the source and re-run the generator.",
        f"# Tools field translated verbatim; Codex tool-name equivalence unverified --",
        f"#   see tools/CODEX_TOOLS_UNVERIFIED.md for Phase 0.5 empirical probe checklist.",
        f"",
    ]

    name = fields.get("name", source_name.replace(".md", ""))
    description = fields.get("description", "")
    tools = fields.get("tools", [])
    model = fields.get("model", "")
    effort = fields.get("effort", "")
    max_turns = fields.get("maxTurns", "")

    lines.append(f'name = "{toml_escape_string(name)}"')

    # description as basic string (Codex parses single-line for description-trigger)
    lines.append(f'description = "{toml_escape_string(description)}"')

    if tools and isinstance(tools, list):
        # Strip MCP tools (mcp__*): they are Claude-session-only; Codex cannot resolve
        # the tool name and would error on agent load. The Claude-side availability-guard
        # already degrades gracefully when the MCP is absent (always the case on Codex).
        codex_tools = [t for t in tools if not t.startswith("mcp__")]
        if codex_tools:
            lines.append(f"tools = {render_toml_array(codex_tools)}")

    # Model mapping (opus->gpt-5.5, sonnet->gpt-5.4)
    if model:
        mapped_model = MODEL_MAP.get(model.lower(), model)
        lines.append(f'model = "{mapped_model}"  # mapped from Claude model: {model}')

    if effort:
        # M1: translate Claude-native "max" -> Codex-spec "xhigh"; pass others through.
        mapped_effort = EFFORT_MAP.get(effort.lower(), effort)
        comment = f"  # mapped from Claude effort: {effort}" if mapped_effort != effort else ""
        lines.append(f'model_reasoning_effort = "{mapped_effort}"{comment}')

    if max_turns:
        lines.append(f"max_turns = {max_turns}  # semantics unverified pending Phase 5")

    # developer_instructions: V2-corrected field name (NOT system_prompt)
    # Multi-line string with triple-quote delimiter
    lines.append("")
    lines.append('developer_instructions = """')
    lines.append(toml_escape_multiline(body.rstrip("\n")))
    lines.append('"""')
    lines.append("")

    return "\n".join(lines)


def gen_agent(source_path: Path, target_path: Path, verbose: bool = False) -> dict:
    """Generate one TOML file. Returns stats dict."""
    stats = {"written": False, "skipped": False, "name": source_path.stem,
             "model_mapped_from": "", "dropped_fields": []}
    text = source_path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(text)
    if not fields:
        if verbose:
            print(f"  SKIPPED {source_path.name} (no frontmatter)")
        stats["skipped"] = True
        return stats

    # Track dropped fields for run-log
    for f in ("disallowedTools", "color"):
        if f in fields:
            stats["dropped_fields"].append(f)

    stats["model_mapped_from"] = fields.get("model", "")
    toml_content = generate_toml(fields, body, source_path.name)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists() and target_path.read_text(encoding="utf-8") == toml_content:
        if verbose:
            print(f"  SKIPPED-IDENTICAL {source_path.stem}")
        stats["skipped"] = True
    else:
        target_path.write_text(toml_content, encoding="utf-8")
        stats["written"] = True
        if verbose:
            mapped = MODEL_MAP.get(stats["model_mapped_from"].lower(), stats["model_mapped_from"])
            dropped = ", ".join(stats["dropped_fields"]) if stats["dropped_fields"] else "none"
            print(f"  GENERATED {source_path.stem}.toml (model {stats['model_mapped_from']} -> {mapped}; dropped: {dropped})")
    return stats


def gen_all(check_only: bool = False, verbose: bool = False) -> int:
    if not SOURCE_ROOT.exists():
        print(f"ERROR: source not found: {SOURCE_ROOT}", file=sys.stderr)
        return 2
    TARGET_ROOT.mkdir(parents=True, exist_ok=True)

    total = 0
    written = 0
    skipped = 0
    model_distribution = {}

    for source_path in sorted(SOURCE_ROOT.glob("*.md")):
        target_path = TARGET_ROOT / (source_path.stem + ".toml")
        stats = gen_agent(source_path, target_path, verbose=verbose)
        total += 1
        if stats["written"]:
            written += 1
        if stats["skipped"]:
            skipped += 1
        if stats["model_mapped_from"]:
            mapped = MODEL_MAP.get(stats["model_mapped_from"].lower(), stats["model_mapped_from"])
            model_distribution[mapped] = model_distribution.get(mapped, 0) + 1

    print(f"gen-codex-agents: {total} agents processed", file=sys.stderr)
    print(f"  TOML: {written} generated, {skipped} skipped-identical", file=sys.stderr)
    if model_distribution:
        for m, c in sorted(model_distribution.items()):
            print(f"  model {m}: {c} agent(s)", file=sys.stderr)

    if check_only and written > 0:
        print(f"CHECK FAILED: {written} TOML files diverged", file=sys.stderr)
        return 1
    if check_only:
        print("CHECK OK: zero diff (idempotent)", file=sys.stderr)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Generate .codex/agents/*.toml from .claude/agents/*.md")
    parser.add_argument("--check", action="store_true", help="Idempotency check: exit 1 if any divergence")
    parser.add_argument("--verbose", action="store_true", help="Per-agent run log")
    args = parser.parse_args()
    return gen_all(check_only=args.check, verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main())
