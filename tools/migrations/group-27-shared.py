"""Group 27 shared. Source of truth per F7. Imported by every phase."""
import hashlib, io, json, re, subprocess, sys
from datetime import date, datetime, timezone
from pathlib import Path

if sys.version_info < (3, 9):
    sys.exit("Python >= 3.9 required")
try:
    from ruamel.yaml import YAML
    from ruamel.yaml.error import YAMLError
except ImportError:
    sys.exit("pip install ruamel.yaml")

VAULT_ROOT = Path(r"/path/to/vault")
CANONICAL_TOP_LEVEL_DIRS = frozenset({
    "Atlas", "Calendar", "Efforts", "wiki", "private",
    "docs", "_templates", "tools", ".claude",
})
INFRASTRUCTURE_PREFIXES = ("_templates/", "tools/", ".claude/", "_quarantine/")
STRUCTURAL_EXCLUSIONS = frozenset({
    # Obsidian conventions (v12 original)
    "HOME.md", "USER.md",
    # AI agent infrastructure (added after CLAUDE.md scope-error halt 2026-04-21)
    "CLAUDE.md", "AGENTS.md", "GEMINI.md",
    # Project infrastructure
    "README.md", "CONTRIBUTING.md", "CHANGELOG.md", "LICENSE.md",
})
CANONICAL_FM_FIELDS = frozenset({
    "categories", "type", "aliases", "related",
    "status", "tags", "created", "updated",
})
NON_CANONICAL_STATUS_VALUES = frozenset({"planned", "watchlist", "ready-for-execution"})
CANONICAL_STATUS_ENUM = frozenset({
    "active", "paused", "done", "dropped", "stub",
    "deprecated", "draft", "complete", "stale",
})
LONG_DORMANT_DAYS = 180
BODY_SCAN_LINES = 10

KNOWN_DEFERRAL_FILENAME_PREFIXES = {
    "malformed-yaml": ("<private-file>", "<private-file>"),
    "ff13-schema-incomplete": ("<private-file>", "<private-file>"),
}
SUPERSESSION_PATTERNS = [
    (0, re.compile(r"^>\s?SUPERSEDED BY \[\[([^\]]+)\]\]")),
    (1, re.compile(r"^>\s?MOVED TO \[\[([^\]]+)\]\]")),
    (2, re.compile(r"^>\s?REPLACED BY \[\[([^\]]+)\]\]")),
    (3, re.compile(r"^>\s?DEPRECATED\b")),
    (4, re.compile(r"^#\s?SUPERSEDED BY")),
    (5, re.compile(r"<!--\s*redirect-to:\s*(\S+)\s*-->")),
    (6, re.compile(r"<!--\s*deprecated\s*-->")),
]


def yaml_rt():
    y = YAML(); y.preserve_quotes = True; y.indent(mapping=2, sequence=4, offset=2); y.width = 4096
    return y


def normalize_path(p):
    rel = p.relative_to(VAULT_ROOT) if p.is_absolute() else p
    return str(rel).replace("\\", "/")


def enumerate_md_files():
    r = subprocess.run(["git", "-C", str(VAULT_ROOT), "ls-files", "*.md"],
                       check=True, capture_output=True, text=True, encoding="utf-8")
    return sorted(VAULT_ROOT / ln.strip() for ln in r.stdout.splitlines() if ln.strip())


def split_frontmatter_body(path):
    raw = path.read_text(encoding="utf-8-sig")
    lines = raw.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return "", raw
    for i, ln in enumerate(lines[1:], start=1):
        if ln.strip() == "---":
            return "".join(lines[: i + 1]), "".join(lines[i + 1:])
    return "", raw


def parse_frontmatter(path):
    try:
        text = path.read_text(encoding="utf-8-sig")
    except Exception as e:
        return None, f"read: {type(e).__name__}"
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, None
    end = None
    for i, ln in enumerate(lines[1:], start=1):
        if ln.strip() == "---":
            end = i; break
    if end is None:
        return None, "unclosed frontmatter"
    fm_text = "\n".join(lines[1:end])
    if not fm_text.strip():
        return {}, None
    try:
        p = YAML(typ="safe").load(fm_text)
    except YAMLError as e:
        return None, f"yaml: {type(e).__name__}"
    except Exception as e:
        return None, f"parse: {type(e).__name__}"
    if p is None:
        return {}, None
    if not isinstance(p, dict):
        return None, "not a mapping"
    return p, None


def _body_lines(path):
    try:
        t = path.read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return []
    lines = t.splitlines()
    if not lines or lines[0].strip() != "---":
        return lines
    for i, ln in enumerate(lines[1:], start=1):
        if ln.strip() == "---":
            return lines[i + 1:]
    return []


def scan_body_markers(path):
    body = _body_lines(path)
    nonblank = [ln for ln in body if ln.strip()][:BODY_SCAN_LINES]
    out = []
    for line in nonblank:
        for idx, pat in SUPERSESSION_PATTERNS:
            m = pat.search(line)
            if m:
                out.append({"pattern_index": idx, "matched_line": line.strip()[:200],
                            "supersession_target": m.group(1) if m.groups() else None})
    out.sort(key=lambda d: (d["pattern_index"], d["matched_line"]))
    return out


def is_long_dormant(fm, today=None):
    today = today or date.today()
    if not isinstance(fm, dict) or fm.get("status") not in ("dropped", "paused"):
        return False
    upd = fm.get("updated")
    if upd is None:
        return False
    try:
        d = upd if isinstance(upd, date) else date.fromisoformat(str(upd))
    except (ValueError, TypeError):
        return False
    return (today - d).days > LONG_DORMANT_DAYS


def is_canonical_path(rel):
    s = rel.split("/")
    return bool(s) and s[0] in CANONICAL_TOP_LEVEL_DIRS


def under_infrastructure(rel):
    return any(rel.startswith(p) for p in INFRASTRUCTURE_PREFIXES)


def is_structural_exclusion(rel):
    return Path(rel).name in STRUCTURAL_EXCLUSIONS


def file_sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def bytes_sha256(b):
    return hashlib.sha256(b).hexdigest()


def fm_sha_excluding(fm, excluded):
    if not isinstance(fm, dict):
        return "NA"
    filt = {k: v for k, v in fm.items() if k not in set(excluded)}
    return hashlib.sha256(
        json.dumps(filt, sort_keys=True, default=str, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def compute_custom_fields(fm):
    if not isinstance(fm, dict):
        return []
    return sorted(set(fm.keys()) - CANONICAL_FM_FIELDS - {"domain", "quarantined-date", "quarantined-reason"})


def classify(rel, fm, err, markers, deferrals):
    signals = []
    if isinstance(fm, dict) and fm:
        if fm.get("status") == "stale": signals.append("status:stale")
        if fm.get("status") == "deprecated": signals.append("status:deprecated")
        if "deprecated-by" in fm: signals.append("frontmatter:deprecated-by")
    for m in markers:
        signals.append(f"body-marker:p{m['pattern_index']}")
    if is_structural_exclusion(rel):
        signals.append("structural-exclusion")
        return None, "", sorted(set(signals))
    if under_infrastructure(rel):
        return None, "", []
    if err and rel not in deferrals:
        return "broken-fragment", f"yaml parse: {err}", sorted(set(signals))
    if markers:
        f = markers[0]
        tgt = f" -> {f['supersession_target']}" if f["supersession_target"] else ""
        return "superseded", f"body marker: {f['matched_line'][:80]}{tgt}", sorted(set(signals))
    if isinstance(fm, dict):
        if fm.get("status") == "deprecated" or "deprecated-by" in fm:
            return "deprecated", f"status={fm.get('status')}, dep-by={'yes' if 'deprecated-by' in fm else 'no'}", sorted(set(signals))
        if fm.get("status") == "stale":
            return "stale", "status=stale", sorted(set(signals))
        if not fm and is_canonical_path(rel):
            return "broken-fragment", "missing frontmatter in canonical path", sorted(set(signals))
    if not is_canonical_path(rel):
        signals.append("non-canonical-path")
        return "other", "non-canonical top-level path", sorted(set(signals))
    if isinstance(fm, dict) and is_long_dormant(fm):
        signals.append("long-dormant")
        return "other", f"long-dormant (status={fm.get('status')}, >{LONG_DORMANT_DAYS}d)", sorted(set(signals))
    return None, "", sorted(set(signals))


def resolve_deferrals(all_paths, fm_by_path):
    f = {"malformed-yaml": [], "ff13-schema-incomplete": [], "q11-non-canonical-status": []}
    for p in all_paths:
        rel, n = normalize_path(p), p.name
        if any(n.startswith(x) for x in KNOWN_DEFERRAL_FILENAME_PREFIXES["malformed-yaml"]):
            f["malformed-yaml"].append(rel)
        if any(n.startswith(x) for x in KNOWN_DEFERRAL_FILENAME_PREFIXES["ff13-schema-incomplete"]):
            fm = fm_by_path.get(rel)
            if not isinstance(fm, dict) or not {"status", "updated", "created"}.issubset(fm.keys()):
                f["ff13-schema-incomplete"].append(rel)
        fm = fm_by_path.get(rel)
        if isinstance(fm, dict) and fm.get("status") in NON_CANONICAL_STATUS_VALUES:
            f["q11-non-canonical-status"].append(rel)
    audit = {
        "malformed_yaml_found": len(f["malformed-yaml"]), "malformed_yaml_expected": 2,
        "malformed_yaml_paths": sorted(f["malformed-yaml"]),
        "ff13_found": len(f["ff13-schema-incomplete"]), "ff13_expected": 2,
        "ff13_paths": sorted(f["ff13-schema-incomplete"]),
        "q11_found": len(f["q11-non-canonical-status"]), "q11_expected": 4,
        "q11_paths": sorted(f["q11-non-canonical-status"]),
    }
    return frozenset(f["malformed-yaml"] + f["ff13-schema-incomplete"] + f["q11-non-canonical-status"]), audit


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sentinel_present_in_dst(dst_path):
    """F8 extended: idempotency sentinel check on dst."""
    try:
        fm_chunk, _ = split_frontmatter_body(dst_path)
    except Exception:
        return False
    return bool(fm_chunk) and "quarantined-date:" in fm_chunk
