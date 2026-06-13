"""
check-pii.py -- Scan a directory tree for PII matches against a denylist.

Usage: python check-pii.py <root_dir> <denylist_path>

Exit 0 with "PASS: check-pii zero hits..." line on success.
Exit 1 with "FAIL: check-pii found N hits..." + per-category breakdown on any hit.
Hits logged to <root>/.audit/pii-check-<unix_ts>.log as JSON array.

Stdlib only.
"""
import re
import sys
import json
import time
from pathlib import Path


SCAN_EXTENSIONS = {'.md', '.py', '.sh', '.ps1', '.txt', '.json', '.yaml', '.yml',
                   '.js', '.mjs', '.vbs', '.base', '.toml'}
EXCLUDE_DIRS = {'.git', '.audit', '__pycache__', 'node_modules', '.venv'}


def load_patterns(denylist_path):
    """Parse denylist file. Returns list of (category, compiled_regex) tuples."""
    pats = []
    current_cat = None
    text = Path(denylist_path).read_text(encoding='utf-8')
    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('CATEGORY:'):
            current_cat = line.split(':', 1)[1].strip()
            continue
        if current_cat is None:
            sys.stderr.write(f"WARN: pattern before any CATEGORY at line {line_no}: {line}\n")
            continue
        try:
            pats.append((current_cat, re.compile(line, re.IGNORECASE | re.MULTILINE)))
        except re.error as e:
            sys.stderr.write(f"WARN: invalid regex at line {line_no}: {line} ({e})\n")
    return pats


def _scan_one_file(fp, root_for_relpath, patterns, hits):
    """Scan a single file, append hits to the list."""
    if fp.suffix not in SCAN_EXTENSIONS:
        return
    try:
        text = fp.read_text(encoding='utf-8', errors='ignore')
    except (OSError, UnicodeDecodeError):
        return
    for cat, pat in patterns:
        for m in pat.finditer(text):
            line_no = text[:m.start()].count('\n') + 1
            start = max(0, m.start() - 20)
            end = min(len(text), m.end() + 20)
            snippet = text[start:end].replace('\n', ' ').strip()
            try:
                rel = str(fp.relative_to(root_for_relpath))
            except ValueError:
                rel = fp.name
            hits.append({
                'file': rel,
                'line': line_no,
                'category': cat,
                'snippet': snippet,
                'match': m.group(0),
            })


def scan(target, patterns):
    """Walk target (file or directory), return list of hit dicts and file-scanned count."""
    hits = []
    target_path = Path(target)
    files_scanned = 0
    if target_path.is_file():
        _scan_one_file(target_path, target_path.parent, patterns, hits)
        if target_path.suffix in SCAN_EXTENSIONS:
            files_scanned = 1
    elif target_path.is_dir():
        for fp in target_path.rglob('*'):
            if not fp.is_file():
                continue
            if any(part in EXCLUDE_DIRS for part in fp.parts):
                continue
            if fp.suffix not in SCAN_EXTENSIONS:
                continue
            _scan_one_file(fp, target_path, patterns, hits)
            files_scanned += 1
    return hits, files_scanned


def main():
    if len(sys.argv) != 3:
        print("FAIL: usage: python check-pii.py <root_file_or_dir> <denylist_path>", file=sys.stderr)
        sys.exit(2)
    target, denylist = sys.argv[1], sys.argv[2]
    target_path = Path(target)
    if not (target_path.is_dir() or target_path.is_file()):
        print(f"FAIL: target not a file or directory: {target}", file=sys.stderr)
        sys.exit(2)
    if not Path(denylist).is_file():
        print(f"FAIL: denylist not a file: {denylist}", file=sys.stderr)
        sys.exit(2)
    pats = load_patterns(denylist)
    hits, files_scanned = scan(target_path, pats)
    # Log location: <target>/.audit/ if target is dir, else <target.parent> (or .audit ancestor if present).
    if target_path.is_dir():
        audit_dir = target_path / '.audit'
    else:
        parent = target_path.resolve().parent
        audit_dir = parent if parent.name == '.audit' else parent / '.audit'
    audit_dir.mkdir(exist_ok=True)
    log_path = audit_dir / f'pii-check-{int(time.time())}.log'
    log_path.write_text(json.dumps(hits, indent=2), encoding='utf-8')
    by_cat = {}
    for h in hits:
        by_cat[h['category']] = by_cat.get(h['category'], 0) + 1
    if hits:
        print(f"FAIL: check-pii found {len(hits)} hits across {len(by_cat)} categories")
        print(f"  by category: {json.dumps(by_cat)}")
        print(f"  log: {log_path}")
        sys.exit(1)
    print(f"PASS: check-pii zero hits across {len(pats)} patterns scanning {files_scanned} files")
    print(f"  log: {log_path}")
    sys.exit(0)


if __name__ == '__main__':
    main()
