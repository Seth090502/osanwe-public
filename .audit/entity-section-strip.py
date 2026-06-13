"""
entity-section-strip.py -- Remove personal-context sections from entity notes.

Usage: python entity-section-strip.py <mirror_root>

Targets: <mirror>/wiki/entities/tickers/*.md, <mirror>/wiki/entities/companies/*.md

Removes H2/H3 sections whose header (lowercased+stripped) matches:
  Position, Position Sizing, Why I Hold, Personal Context, Cost Basis, P&L, PnL,
  Trade History, Personal Notes, Conviction, Holding Size, My Position, Entry, Entries

Preserves frontmatter and all other sections.
Appends a one-line footer note to modified files.
Logs to <mirror>/.audit/entity-strip-log.jsonl.
Emits "PASS: entity-section-strip complete..." line.
"""
import re
import sys
import json
from pathlib import Path


SKIP_HEADERS = {
    'position', 'position sizing', 'why i hold', 'personal context',
    'cost basis', 'p&l', 'pnl', 'trade history', 'personal notes',
    'conviction', 'holding size', 'my position', 'entry', 'entries',
    'cost', 'pl', 'p and l',
}

HEADER_RE = re.compile(r'^(#{2,3})\s+(.+?)\s*$', re.MULTILINE)
FRONTMATTER_RE = re.compile(r'^---\n(.*?)\n---\n', re.DOTALL)
FOOTER_NOTE = '\n\n---\n\n> Personal context sections (position sizing, cost basis, trade history, conviction) removed in public mirror. The entity-note schema is documented in the architecture docs.\n'


def strip_sections(text):
    """Drop H2/H3 sections whose name is in SKIP_HEADERS. Returns (new_text, removed_header_names)."""
    fm_match = FRONTMATTER_RE.match(text)
    if fm_match:
        frontmatter = text[:fm_match.end()]
        body = text[fm_match.end():]
    else:
        frontmatter = ''
        body = text

    headers = [(m.start(), m.end(), m.group(1), m.group(2)) for m in HEADER_RE.finditer(body)]
    if not headers:
        return text, []

    removed = []
    keep_ranges = []

    if headers[0][0] > 0:
        keep_ranges.append((0, headers[0][0]))

    for i, (start, _end, _hashes, name) in enumerate(headers):
        section_end = headers[i + 1][0] if i + 1 < len(headers) else len(body)
        if name.lower().strip() in SKIP_HEADERS:
            removed.append(name.strip())
            continue
        keep_ranges.append((start, section_end))

    new_body = ''.join(body[a:b] for a, b in keep_ranges)
    if removed:
        new_body = new_body.rstrip() + FOOTER_NOTE
    return frontmatter + new_body, removed


def main():
    if len(sys.argv) != 2:
        print("FAIL: usage: python entity-section-strip.py <mirror_root>", file=sys.stderr)
        sys.exit(2)
    mirror_root = Path(sys.argv[1])
    if not mirror_root.is_dir():
        print(f"FAIL: mirror not a directory: {mirror_root}", file=sys.stderr)
        sys.exit(2)
    audit_dir = mirror_root / '.audit'
    audit_dir.mkdir(exist_ok=True)
    log_path = audit_dir / 'entity-strip-log.jsonl'

    targets = []
    for sub in ['tickers', 'companies']:
        d = mirror_root / 'wiki' / 'entities' / sub
        if d.is_dir():
            targets.extend(sorted(d.glob('*.md')))

    total_files = 0
    total_sections = 0
    with log_path.open('w', encoding='utf-8') as log_f:
        for fp in targets:
            text = fp.read_text(encoding='utf-8', errors='ignore')
            new_text, removed = strip_sections(text)
            if removed:
                fp.write_text(new_text, encoding='utf-8')
                log_f.write(json.dumps({
                    'file': str(fp.relative_to(mirror_root)).replace('\\', '/'),
                    'removed_sections': removed,
                }) + '\n')
                total_files += 1
                total_sections += len(removed)

    print(f"PASS: entity-section-strip complete -- {total_files} files modified, {total_sections} sections removed across {len(targets)} entity notes scanned")
    print(f"  log: {log_path}")


if __name__ == '__main__':
    main()
