"""
wikilink-rewriter.py -- Rewrite [[wikilinks]] in public mirror based on target existence.

Usage:
  python wikilink-rewriter.py <mirror_root>                  -- heuristic mode
  python wikilink-rewriter.py <mirror_root> <source_root>    -- full classification (preferred)

Two passes per file:
  1. Build set of all .md files (by stem, case-insensitive) in mirror (and source if provided)
  2. For each .md file in mirror, find [[link]] or [[link|alias]] patterns and reclassify:
     - Target exists in mirror: preserve
     - Target was in source but excluded from mirror: classify by source path
         * Calendar/decisions/, private/, .raw/, Efforts/career-search/ populated -> [REMOVED-PRIVATE]
         * wiki/investing/analyses/ (excluding _TEMPLATE_/_EXAMPLE_) -> [SCAFFOLD-EXAMPLE]
         * Otherwise -> [BROKEN-LINK]
     - Target not in source either -> [BROKEN-LINK]

Logs to <mirror>/.audit/broken-links.md
Emits "PASS: wikilink-rewriter complete..." line.
"""
import re
import sys
import json
from pathlib import Path


WIKILINK_RE = re.compile(r'\[\[([^\]|#]+)(#[^\]|]*)?(\|([^\]]+))?\]\]')

EXCLUDED_PATH_PREFIXES = (
    'Calendar/decisions/',
    'private/',
    '.raw/',
    'finance/',
    'credentials/',
)
SCAFFOLD_PATH_PREFIX = 'wiki/investing/analyses/'
SCAFFOLD_KEEP_PREFIXES = ('_template', '_example')


def build_index(root):
    """Return dict: stem.lower() -> relative_path_string."""
    idx = {}
    for fp in root.rglob('*.md'):
        if '.audit' in fp.parts or '.git' in fp.parts:
            continue
        idx[fp.stem.lower()] = str(fp.relative_to(root)).replace('\\', '/')
    return idx


def classify(target_stem, mirror_idx, source_idx):
    """Decide replacement for a wikilink target.
    Returns ('PRESERVE' | 'REMOVED-PRIVATE' | 'SCAFFOLD-EXAMPLE' | 'BROKEN-LINK', source_path_or_None)."""
    key = target_stem.lower().strip()
    if key in mirror_idx:
        return ('PRESERVE', None)
    if source_idx and key in source_idx:
        src_path = source_idx[key]
        if any(src_path.startswith(p) for p in EXCLUDED_PATH_PREFIXES):
            return ('REMOVED-PRIVATE', src_path)
        if src_path.startswith(SCAFFOLD_PATH_PREFIX):
            name_lower = Path(src_path).stem.lower()
            if not any(name_lower.startswith(p) for p in SCAFFOLD_KEEP_PREFIXES):
                return ('SCAFFOLD-EXAMPLE', src_path)
            return ('BROKEN-LINK', src_path)
        return ('BROKEN-LINK', src_path)
    return ('BROKEN-LINK', None)


def rewrite_file(fp, mirror_root, mirror_idx, source_idx, log):
    text = fp.read_text(encoding='utf-8', errors='ignore')
    changes = 0

    def replace(m):
        nonlocal changes
        target = m.group(1).strip()
        action, src_path = classify(target, mirror_idx, source_idx)
        if action == 'PRESERVE':
            return m.group(0)
        changes += 1
        log.append({
            'file': str(fp.relative_to(mirror_root)).replace('\\', '/'),
            'link': target,
            'action': action,
            'source_path': src_path,
        })
        return f'[{action}]'

    new_text = WIKILINK_RE.sub(replace, text)
    if changes:
        fp.write_text(new_text, encoding='utf-8')
    return changes


def main():
    if len(sys.argv) not in (2, 3):
        print("FAIL: usage: python wikilink-rewriter.py <mirror_root> [<source_root>]", file=sys.stderr)
        sys.exit(2)
    mirror_root = Path(sys.argv[1])
    source_root = Path(sys.argv[2]) if len(sys.argv) == 3 else None
    if not mirror_root.is_dir():
        print(f"FAIL: mirror not a directory: {mirror_root}", file=sys.stderr)
        sys.exit(2)
    mirror_idx = build_index(mirror_root)
    source_idx = build_index(source_root) if source_root and source_root.is_dir() else {}
    log = []
    total_changes = 0
    files_modified = 0
    for fp in mirror_root.rglob('*.md'):
        if '.audit' in fp.parts or '.git' in fp.parts:
            continue
        changes = rewrite_file(fp, mirror_root, mirror_idx, source_idx, log)
        if changes:
            files_modified += 1
            total_changes += changes

    audit_dir = mirror_root / '.audit'
    audit_dir.mkdir(exist_ok=True)
    broken_log_path = audit_dir / 'broken-links.md'

    by_action = {}
    for entry in log:
        by_action[entry['action']] = by_action.get(entry['action'], 0) + 1

    lines = ['# Wikilink rewrites -- broken-links audit\n\n']
    lines.append(f'Total rewrites: {total_changes} across {files_modified} files.\n\n')
    lines.append('## By action\n\n')
    for a, c in sorted(by_action.items()):
        lines.append(f'- `{a}`: {c}\n')
    lines.append('\n## Detail (first 200 entries)\n\n')
    for entry in log[:200]:
        src_note = f" (source: `{entry['source_path']}`)" if entry['source_path'] else ''
        lines.append(f"- `{entry['file']}` :: `[[{entry['link']}]]` -> `{entry['action']}`{src_note}\n")
    if len(log) > 200:
        lines.append(f"\n... and {len(log) - 200} more entries.\n")
    broken_log_path.write_text(''.join(lines), encoding='utf-8')

    print(f"PASS: wikilink-rewriter complete -- {total_changes} rewrites across {files_modified} files")
    print(f"  by action: {json.dumps(by_action)}")
    print(f"  source-aware: {bool(source_idx)}")
    print(f"  log: {broken_log_path}")


if __name__ == '__main__':
    main()
