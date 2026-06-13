"""
diff-baseline.py -- Compare two capability-baseline JSON files.

Usage: python diff-baseline.py <pre_json> <post_json>

Allowed-divergent dimensions: entity_scaffold_count (decrease OK).
All others must match exactly.

Emits "PASS: capability parity additive-only..." or "FAIL: capability regression..." line.
"""
import sys
import json
from pathlib import Path


ALLOWED_DIVERGENT = {'entity_scaffold_count', '_meta'}


def compare(pre, post, prefix=''):
    """Recursively compare two dicts. Returns list of regression strings."""
    regressions = []
    for key, pre_v in pre.items():
        full_key = f"{prefix}{key}"
        if key in ALLOWED_DIVERGENT:
            continue
        post_v = post.get(key)
        if isinstance(pre_v, dict) and isinstance(post_v, dict):
            regressions.extend(compare(pre_v, post_v, prefix=f"{full_key}."))
        elif pre_v != post_v:
            regressions.append(f"{full_key}: pre={pre_v} post={post_v}")
    return regressions


def main():
    if len(sys.argv) != 3:
        print("FAIL: usage: python diff-baseline.py <pre_json> <post_json>", file=sys.stderr)
        sys.exit(2)
    pre_path, post_path = Path(sys.argv[1]), Path(sys.argv[2])
    if not pre_path.is_file() or not post_path.is_file():
        print(f"FAIL: baseline file missing -- pre_exists={pre_path.is_file()} post_exists={post_path.is_file()}",
              file=sys.stderr)
        sys.exit(2)
    pre = json.loads(pre_path.read_text(encoding='utf-8'))
    post = json.loads(post_path.read_text(encoding='utf-8'))

    regressions = compare(pre, post)
    if regressions:
        print(f"FAIL: capability regression in {len(regressions)} dimension(s):")
        for r in regressions:
            print(f"  - {r}")
        sys.exit(1)

    counted = [k for k in pre if k not in ALLOWED_DIVERGENT]
    print(f"PASS: capability parity additive-only across {len(counted)} dimensions (entity_scaffold_count drop allowed)")
    sys.exit(0)


if __name__ == '__main__':
    main()
