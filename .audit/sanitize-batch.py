"""
sanitize-batch.py -- Walk source tree, mirror to target with sanitization.

Usage: python sanitize-batch.py <source_root> <target_root> <denylist_path>

Mirrors directory structure. For .md/.py/.txt/.yaml/.yml/.json/.sh/.ps1 files,
sanitizes via sanitize.py logic. Other types: byte-identical copy.

Skips exclusion list (private/, .raw/, Calendar/decisions/, finance/, credentials/,
.claude/state/, .claude/transcripts/, .git/, CLAUDE.local.md, .audit/).

Aggregates redaction log to <target>/.audit/sanitize-log.jsonl.
Emits "PASS: sanitize-batch complete..." line.
"""
import sys
import json
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sanitize import load_patterns, sanitize_file


SANITIZE_EXTENSIONS = {'.md', '.py', '.txt', '.yaml', '.yml', '.json', '.sh', '.ps1'}

# Names that must NEVER propagate -- match if any path PART equals one of these.
# Reserved for tokens that are unambiguously private wherever they appear in the tree.
EXCLUDE_DIR_NAMES = {
    'private', '.raw', 'finance', 'credentials',
    '.git', '__pycache__', 'node_modules', '.venv',
    '.audit',
    '.checkpoints', '.obsidian', '.smart-env',
    '_quarantine',
}

# Files that must NEVER propagate (matched on basename anywhere)
EXCLUDE_FILE_NAMES = {
    'CLAUDE.local.md',
    'HOME.md',
    'USER.md',
}

# Path prefixes (relative to source_root) that must not propagate.
# Top-level-only matches go here so we don't accidentally exclude nested dirs
# with the same name (e.g. Atlas/sources/career/ is architectural content
# while top-level career/ is personal job-search ops).
EXCLUDE_PATH_PREFIXES = (
    # Spec exclusions
    'Calendar/decisions',
    'Calendar/daily',  # daily entries excluded; scaffold added post-batch
    '.claude/state',
    '.claude/transcripts',
    '.claude/worktrees',
    '.claude/command-log.txt',
    '.claude/skills/_archive',  # stub README added post-batch
    # Top-level personal-domain dirs (VP-1 extras)
    'career',
    'career-ops',
    'config',
    'data',
    'daily',
    'golf',
    'health',
    'personal',
    'plans',
    'reviews',
    'research',
    'investing',
    # UAP corpus (only README + scripts shape scaffolded post-batch)
    'vault/projects/uap-corpus/20-extractions',
    'vault/projects/uap-corpus/30-canonical',
    'vault/projects/uap-corpus/40-final-report',
    'vault/projects/uap-corpus/50-audit',
    'vault/projects/uap-corpus/60-checkpoints',
    'vault/projects/uap-corpus/80-adversarial',
    'vault/projects/uap-corpus/logs',
    # Test/precheck artifacts that shouldn't ship
    'wiki/research/test-tmp',
    # Personal Efforts subtrees (only career-search/ propagates as scaffold)
    'Efforts/golf-practice',
    'Efforts/health-protocol',
    'Efforts/personal-finance-disputes',
    # Misc personal artifacts that didn't fit other categories
    'vault/projects/uap-corpus/pipeline-retrospective',
    # Runtime state file
    'tools/fs-watcher-state.json',
)

# Substring patterns matched on filename (basename) -- excludes .bak files, settings backups, etc.
EXCLUDE_FILE_PATTERNS = (
    '.bak.',
    '.pyc',
)


def is_excluded(rel_path):
    """Check if a relative path should be excluded from the mirror."""
    parts = rel_path.parts
    if any(p in EXCLUDE_DIR_NAMES for p in parts):
        return True
    if rel_path.name in EXCLUDE_FILE_NAMES:
        return True
    for pat in EXCLUDE_FILE_PATTERNS:
        if pat in rel_path.name:
            return True
    rel_str = str(rel_path).replace('\\', '/')
    for prefix in EXCLUDE_PATH_PREFIXES:
        if rel_str == prefix or rel_str.startswith(prefix + '/') or rel_str == prefix:
            return True
    return False


def main():
    if len(sys.argv) not in (4, 5):
        print("FAIL: usage: python sanitize-batch.py <source_root> <target_root> <denylist> [<log_path>]", file=sys.stderr)
        sys.exit(2)
    source_root = Path(sys.argv[1])
    target_root = Path(sys.argv[2])
    denylist = sys.argv[3]
    if not source_root.is_dir():
        print(f"FAIL: source not a directory: {source_root}", file=sys.stderr)
        sys.exit(2)
    if not Path(denylist).is_file():
        print(f"FAIL: denylist not a file: {denylist}", file=sys.stderr)
        sys.exit(2)
    target_root.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) == 5:
        log_path = Path(sys.argv[4])
        log_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        audit_dir = target_root / '.audit'
        audit_dir.mkdir(exist_ok=True)
        log_path = audit_dir / 'sanitize-log.jsonl'
    pats = load_patterns(denylist)

    processed = 0
    sanitized = 0
    copied = 0
    skipped = 0
    total_redactions = 0
    by_cat = {}

    with log_path.open('a', encoding='utf-8') as log_f:
        for src_fp in source_root.rglob('*'):
            if not src_fp.is_file():
                continue
            rel = src_fp.relative_to(source_root)
            if is_excluded(rel):
                skipped += 1
                continue
            dst_fp = target_root / rel
            if src_fp.suffix in SANITIZE_EXTENSIONS:
                file_log = sanitize_file(src_fp, dst_fp, pats)
                redactions = [e for e in file_log if 'category' in e]
                total_redactions += len(redactions)
                for e in redactions:
                    by_cat[e['category']] = by_cat.get(e['category'], 0) + 1
                if redactions:
                    log_f.write(json.dumps({
                        'file': str(rel),
                        'redaction_count': len(redactions),
                        'entries': redactions,
                    }) + '\n')
                sanitized += 1
            else:
                dst_fp.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(src_fp, dst_fp)
                    copied += 1
                except OSError as e:
                    print(f"WARN: copy failed {src_fp}: {e}", file=sys.stderr)
            processed += 1
            if processed % 50 == 0:
                print(f"  progress: {processed} files ({sanitized} sanitized, {copied} copied, {skipped} skipped, {total_redactions} redactions)")

    print(f"PASS: sanitize-batch complete -- {processed} processed, {sanitized} sanitized, {copied} copied, {skipped} skipped, {total_redactions} total redactions")
    print(f"  by category: {json.dumps(by_cat)}")
    print(f"  log: {log_path}")


if __name__ == '__main__':
    main()
