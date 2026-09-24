#!/usr/bin/env python3
"""Group 25 frontmatter canonicalization — preserved migration script.

Canonical migration commit: 5e45ff0 (2026-04-19)
Post-migration patch commit: e36d491 (trailing-newline preservation fix)
Rollback anchor: pre-group-25 tag at a75b419

Purpose: migrate pre-canonical frontmatter (type: string form + domain: field +
type/* and domain/* tags) to canonical schema (categories: list + optional
type: subtype + tags with forbidden prefixes stripped + updated: refreshed).

Invocation (from vault root):
    python tools/migrations/group-25-frontmatter-canonicalize.py <file>...

With env-guard for auto-commit hooks (recommended for bulk re-runs):
    touch .claude/state/auto-commit-disabled
    python tools/migrations/group-25-frontmatter-canonicalize.py <files>
    rm .claude/state/auto-commit-disabled

Requires:
    Python 3.10+ (version checked at import)
    ruamel.yaml (install: pip install ruamel.yaml)
    Run from vault root; paths resolve relative to cwd for routing logic.

Idempotency:
    Running twice produces identical output. `updated:` only refreshed if not
    already today's ISO date. Already-canonical files (categories: present,
    no domain:) are detected and skipped entirely. See README.md "Idempotency"
    for verification protocol.

Canonical form emitted:
    - Key order: original preserved; categories: inserted before type: (or
      position 0 if type: absent)
    - Lists: plural keys, block style, 2-space indent
    - Dates: bare ISO YYYY-MM-DD
    - Quote style: ruamel preserve_quotes=True (original quoting retained)
    - Line endings: LF (per .gitattributes)
    - BOM: preserved if present, not introduced
    - Trailing newlines: exact count preserved (count-based — see README
      methodology finding 5)
    - Body: byte-preserved verbatim

Library choice rationale (empirical, Group 25 Section 4):
    ruamel.yaml selected over pyyaml-hand-emit for: quote preservation + key
    order preservation + Templater placeholder survival. Tested on 4 sample
    files including _templates/daily.md with Templater placeholders
    (<% tp.date.now() %>). pyyaml-hand-emit diverged on quote style and key
    order. See README methodology finding 1 context.

Full methodology findings in README.md.
"""
import sys

if sys.version_info < (3, 10):
    sys.stderr.write(
        f"ERROR: Python 3.10+ required, got {sys.version_info.major}.{sys.version_info.minor}\n"
    )
    sys.exit(1)

try:
    from ruamel.yaml import YAML
except ImportError:
    sys.stderr.write(
        "ERROR: ruamel.yaml not installed.\n"
        "Install with: pip install ruamel.yaml\n"
    )
    sys.exit(1)

import datetime
import hashlib
import io
from pathlib import Path

TODAY = datetime.date(2026, 4, 19)
TODAY_STR = '2026-04-19'


def make_yaml():
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096
    y.indent(mapping=2, sequence=4, offset=2)
    return y


def derive_mapping(rel_path: str, old_type):
    """Section 2 routing rules. rel_path uses forward slashes
    (caller responsibility — see README methodology finding 2).
    Returns (categories: list, subtype: str|None) or None for unrecognized."""
    rp = rel_path

    if old_type == 'entity':
        if '/tickers/' in rp: return (['entity'], 'ticker')
        if '/companies/' in rp: return (['entity'], 'company')
        if rp == '_templates/entity.md': return (['entity'], None)
        return (['entity'], None)

    if old_type == 'moc':
        if '/theses/thesis-' in rp: return (['concepts'], 'thesis')  # Q8
        return (['moc'], None)

    if old_type == 'daily':
        if rp == '_templates/weekly-review.md':
            return (['weekly'], 'synthesis')  # Q10
        return (['daily'], None)

    if old_type == 'reference':
        if rp == 'wiki/research/war-timeline-iran-2024-2026.md':
            return (['wiki'], 'research')  # Q6
        return (['sources'], 'reference')

    if old_type == 'research':
        if rp.startswith('Efforts/'):
            return (['efforts'], 'research')  # Q5
        return (['wiki'], 'research')

    if old_type == 'config':
        if rp == 'Atlas/sources/meta/analysis-depth-standard.md':
            return (['sources'], 'reference')  # Q9
        return (['meta'], 'config')

    if old_type == 'profile':
        return (['people'], 'profile')

    if old_type == 'operational':
        if rp == '<private-file>':
            return (['people'], 'profile')  # Q7
        if rp.startswith('Atlas/concepts/'):
            return (['concepts'], None)
        if rp.startswith('Atlas/sources/'):
            return (['sources'], 'reference')  # Q12 — see README methodology finding 3
        if rp.startswith('Efforts/'):
            return (['efforts'], 'operational')  # Q1
        if rp == 'Calendar/decisions/decision-log.md':
            return (['decisions'], 'decision-log')
        if rp == 'Calendar/decisions/sessions-log.md':
            return (['decisions'], 'session-log')
        if rp in ('wiki/hot.md', 'wiki/insight-stream.md'):
            return (['wiki'], 'synthesis')  # Q4
        # Fallback — should not trigger on known scope.
        # See README methodology finding 3: fallback == scope miss, not acceptable default.
        print(f'WARN: operational fallback — unexpected path {rp!r}', file=sys.stderr)
        return (['efforts'], 'operational')

    if old_type == 'output':
        if rp.startswith('wiki/research/prompts/'):
            return (['wiki'], 'prompt')
        if rp.startswith('Calendar/decisions/briefings/'):
            return (['decisions'], 'briefing')
        return (['efforts'], 'output')

    if old_type == 'analysis':
        if rp == '_templates/research.md':
            return (['wiki'], 'research')  # Q10
        if rp.startswith('Efforts/'):
            return (['efforts'], 'analysis')
        return (['wiki'], 'analysis')

    if old_type == 'career': return (['concepts'], None)    # Q2
    if old_type == 'plan':   return (['concepts'], None)    # Q2
    if old_type == 'strategy': return (['concepts'], 'strategy')
    if old_type == 'playbook': return (['concepts'], 'playbook')

    return None  # unrecognized — caller must surface


def is_templater(v):
    return isinstance(v, str) and '<%' in v


def transform_fm(data, rel_path):
    old_type = data.get('type')
    mapping = derive_mapping(rel_path, old_type)
    if mapping is None:
        raise ValueError(f"No mapping for type={old_type!r} at {rel_path}")
    new_cats, new_subtype = mapping

    if 'domain' in data:
        del data['domain']

    if new_subtype is None:
        if 'type' in data:
            del data['type']
    else:
        data['type'] = new_subtype

    if 'categories' in data:
        data['categories'] = new_cats
    else:
        if 'type' in data:
            keys = list(data.keys())
            data.insert(keys.index('type'), 'categories', new_cats)
        else:
            data.insert(0, 'categories', new_cats)

    if 'tags' in data and data['tags']:
        tags = data['tags']
        data['tags'] = [t for t in tags if not (str(t).startswith('domain/') or str(t).startswith('type/'))]

    u = data.get('updated')
    if is_templater(u):
        pass
    elif u == TODAY or u == TODAY_STR:
        pass
    elif 'updated' in data:
        data['updated'] = TODAY

    return data


def split_fm(text):
    if not text.startswith('---'):
        return None, text
    end = text.find('\n---', 3)
    if end < 0:
        return None, text
    fm = text[3:end+1].strip('\n')
    body_start = end + 4
    if body_start < len(text) and text[body_start] == '\n':
        body_start += 1
    body = text[body_start:] if body_start < len(text) else ''
    return fm, body


def compute_rel_path(file_path):
    """Return vault-relative path with forward slashes.
    Windows path normalization is mandatory — see README methodology finding 2."""
    p = Path(file_path).resolve()
    cwd = Path.cwd()
    try:
        rel = str(p.relative_to(cwd)).replace('\\', '/')
    except ValueError:
        rel = str(p).replace('\\', '/')
    return rel


def migrate_file(path):
    """Migrate a single file. Returns report dict.
    Already-canonical files (categories: + no domain:) are skipped."""
    p = Path(path)
    rel_path = compute_rel_path(path)
    raw = p.read_bytes()
    has_bom = raw[:3] == b'\xef\xbb\xbf'
    text = raw[3:].decode('utf-8') if has_bom else raw.decode('utf-8')
    text = text.replace('\r\n', '\n')
    # Count-based trailing-newline preservation — see README methodology finding 5.
    trailing_count = len(text) - len(text.rstrip('\n'))
    text_stripped = text.rstrip('\n')

    fm_str, body = split_fm(text_stripped)
    if fm_str is None:
        return {'path': rel_path, 'status': 'no_frontmatter'}

    y = make_yaml()
    data = y.load(fm_str)
    if not isinstance(data, dict):
        return {'path': rel_path, 'status': 'non_dict_frontmatter'}

    # Already-canonical detection: categories present AND no domain field → skip
    if 'categories' in data and 'domain' not in data:
        return {'path': rel_path, 'status': 'skipped_already_canonical'}

    try:
        data = transform_fm(data, rel_path)
    except ValueError as e:
        return {'path': rel_path, 'status': 'error', 'error': str(e)}

    buf = io.StringIO()
    y.dump(data, buf)
    new_fm = buf.getvalue().rstrip('\n')

    new_text = f'---\n{new_fm}\n---\n{body}'
    # Preserve exact trailing-newline count — see README methodology finding 5.
    new_text = new_text.rstrip('\n') + ('\n' * trailing_count)

    new_bytes = new_text.encode('utf-8')
    if has_bom:
        new_bytes = b'\xef\xbb\xbf' + new_bytes

    p.write_bytes(new_bytes)
    return {'path': rel_path, 'status': 'migrated'}


def main():
    if len(sys.argv) < 2:
        sys.stderr.write(
            "Usage: python group-25-frontmatter-canonicalize.py <file>...\n\n"
            "Run from vault root. Paths resolve relative to cwd for routing.\n"
            "See README.md for full documentation including methodology findings.\n"
        )
        sys.exit(1)

    files = sys.argv[1:]
    counts = {'migrated': 0, 'skipped_already_canonical': 0,
              'no_frontmatter': 0, 'non_dict_frontmatter': 0, 'error': 0}
    for f in files:
        report = migrate_file(f)
        status = report.get('status', 'unknown')
        counts[status] = counts.get(status, 0) + 1
        if status == 'migrated':
            print(f"  MIGRATED: {report['path']}")
        elif status == 'skipped_already_canonical':
            print(f"  SKIPPED (already canonical): {report['path']}")
        elif status == 'error':
            print(f"  ERROR: {report['path']}: {report.get('error')}", file=sys.stderr)

    print(f"\nSummary: {counts}")
    return 0 if counts['error'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
