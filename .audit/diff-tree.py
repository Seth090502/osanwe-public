"""
diff-tree.py -- Compare two tree listings (file paths, one per line).

Usage: python diff-tree.py <pre_tree> <post_tree>

Expected envelope: post may legitimately differ from pre in:
  - Missing: paths under wiki/investing/analyses/ (scaffold-replaced)
  - Missing: paths under Efforts/career-search/<role>/ (populated packets excluded; scaffold-only)
  - Added:   .audit/, README.md, LICENSE, CHANGELOG.md, EXAMPLES.md,
             CONTRIBUTING.md, THREAT-MODEL.md, docs/case-study-*.md

Emits "PASS: structure delta within expected envelope..." or "FAIL: structure delta outside envelope..." line.
"""
import sys
from pathlib import Path


EXPECTED_MISSING_PREFIXES = (
    'private/',
    '.raw/',
    'finance/',
    'credentials/',
    '.claude/state/',
    '.claude/transcripts/',
    '.claude/worktrees/',
    '.claude/command-log.txt',
    '.claude/settings.json.bak',
    '.claude/settings.local.json.bak',
    'CLAUDE.local.md',
    'HOME.md',
    'USER.md',
    'career/',
    'career-ops/',
    'config/',
    'daily/',
    'data/',
    'golf/',
    'health/',
    'personal/',
    'plans/',
    'reviews/',
    'research/',
    'investing/',
    '.checkpoints/',
    '.obsidian/',
    '.smart-env/',
    '_quarantine/',
    'tools/fs-watcher-state.json',
    'tools/__pycache__/',
    # Empty-dir paths that exist in source but didn't propagate
    'Atlas/sources/tech',
    'wiki/research/dumps',
    # Personal Efforts subtrees
    'Efforts/golf-practice',
    'Efforts/health-protocol',
    'Efforts/personal-finance-disputes',
    # vault/ subtrees not propagated (corpus + retrospective)
    'vault/projects/uap-corpus/pipeline-retrospective',
)

EXPECTED_ADDED_PREFIXES = (
    '.audit',
    'README.md',
    'LICENSE',
    'CHANGELOG.md',
    'EXAMPLES.md',
    'CONTRIBUTING.md',
    'THREAT-MODEL.md',
    'docs/case-study',
    '.gitignore',
    # Scaffolds created in mirror that don't exist in source pre-tree
    'vault',  # uap-corpus README.md + scripts/ etc.
    'Calendar',  # daily/.gitkeep + daily/README.md scaffold
    '.claude/skills/_archive',  # stub README
    'wiki/investing/analyses/_EXAMPLE_TICKER',  # worked example
)


def normalize(line):
    s = line.strip().replace('\\', '/')
    if s.startswith('./'):
        s = s[2:]
    return s


def load_tree(path):
    text = Path(path).read_text(encoding='utf-8')
    return set(normalize(line) for line in text.splitlines() if line.strip())


def is_expected_missing(p):
    return any(p == prefix.rstrip('/') or p.startswith(prefix) for prefix in EXPECTED_MISSING_PREFIXES)


def is_expected_added(p):
    return any(p == prefix or p.startswith(prefix if prefix.endswith('/') else prefix + '') for prefix in EXPECTED_ADDED_PREFIXES) \
        or any(p.startswith(prefix.rstrip('/') + '/') for prefix in EXPECTED_ADDED_PREFIXES)


def main():
    if len(sys.argv) != 3:
        print("FAIL: usage: python diff-tree.py <pre_tree> <post_tree>", file=sys.stderr)
        sys.exit(2)
    pre_path, post_path = Path(sys.argv[1]), Path(sys.argv[2])
    if not pre_path.is_file() or not post_path.is_file():
        print(f"FAIL: tree file missing -- pre_exists={pre_path.is_file()} post_exists={post_path.is_file()}",
              file=sys.stderr)
        sys.exit(2)
    pre = load_tree(pre_path)
    post = load_tree(post_path)

    missing_in_post = pre - post
    added_in_post = post - pre

    unexpected_missing = [p for p in missing_in_post if not is_expected_missing(p)]
    unexpected_added = [p for p in added_in_post if not is_expected_added(p)]

    if unexpected_missing or unexpected_added:
        print(f"FAIL: structure delta outside expected envelope")
        if unexpected_missing:
            print(f"  unexpected missing in post ({len(unexpected_missing)}):")
            for p in sorted(unexpected_missing)[:30]:
                print(f"    - {p}")
            if len(unexpected_missing) > 30:
                print(f"    ... and {len(unexpected_missing) - 30} more")
        if unexpected_added:
            print(f"  unexpected added in post ({len(unexpected_added)}):")
            for p in sorted(unexpected_added)[:30]:
                print(f"    + {p}")
            if len(unexpected_added) > 30:
                print(f"    ... and {len(unexpected_added) - 30} more")
        sys.exit(1)

    print(f"PASS: structure delta within expected envelope -- {len(missing_in_post)} expected-missing, {len(added_in_post)} expected-new")
    sys.exit(0)


if __name__ == '__main__':
    main()
