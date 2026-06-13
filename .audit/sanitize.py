"""
sanitize.py -- Apply denylist regex replacements to a single file.

Usage: python sanitize.py <source_file> <target_file> <denylist_path>

Reads source, applies category-specific replacement markers, writes target.
Emits "PASS: sanitized..." line with redaction count.

Stdlib only. Importable by sanitize-batch.py.
"""
import re
import sys
from pathlib import Path


REPLACEMENTS = {
    # v1 categories (kept for backward compat)
    'FINANCIAL_PORTFOLIO_VALUE': '[REDACTED-PORTFOLIO]',
    'FINANCIAL_TICKER_PROXIMITY': '[REDACTED-POSITION]',
    'FINANCIAL_WAGE_ACCOUNT': '[REDACTED-ACCOUNT]',
    'BIOMETRIC_NUMERIC': '[REDACTED-HEALTH]',
    'MEDICAL_HISTORY': '[REDACTED-MEDICAL]',
    'LOCATION': '[REDACTED-LOCATION]',
    'EMPLOYER_CURRENT': '[REDACTED-EMPLOYER]',
    'FILES_FORBIDDEN': '[REDACTED-FILE-REF]',
    'DOB_AGE_PRECISION': '[REDACTED-AGE]',
    # v2 additions
    'PERSONAL_PORTFOLIO_HOLDINGS': '[REDACTED-HOLDINGS]',
    'PERSONAL_PORTFOLIO_VALUE_ANCHORED': '[REDACTED-PORTFOLIO]',
    'PERSONAL_LIMIT_ORDER': '[REDACTED-ORDER]',
    'PERSONAL_TICKER_POSITION': '[REDACTED-POSITION]',
    'PERSONAL_CONCENTRATION': '[REDACTED-CONCENTRATION]',
    'USER_IDENTITY': '[REDACTED-USER]',
}
DEFAULT_MARKER = '[REDACTED]'


def load_patterns(denylist_path):
    """Parse denylist file. Returns list of (category, compiled_regex) tuples."""
    pats = []
    current_cat = None
    for raw in Path(denylist_path).read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('CATEGORY:'):
            current_cat = line.split(':', 1)[1].strip()
            continue
        if current_cat is None:
            continue
        try:
            pats.append((current_cat, re.compile(line, re.IGNORECASE | re.MULTILINE)))
        except re.error:
            continue
    return pats


def sanitize_text(text, patterns):
    """Apply all patterns to text. Returns (new_text, list_of_redaction_logs)."""
    log = []
    for cat, pat in patterns:
        marker = REPLACEMENTS.get(cat, DEFAULT_MARKER)

        def replace(m, _cat=cat, _marker=marker):
            log.append({
                'category': _cat,
                'original': m.group(0)[:40],
                'replacement': _marker,
            })
            return _marker

        text = pat.sub(replace, text)
    return text, log


def sanitize_file(src, dst, patterns):
    """Read src, sanitize, write dst. Returns log entries (each a dict with category+original+replacement)."""
    src_path = Path(src)
    dst_path = Path(dst)
    try:
        text = src_path.read_text(encoding='utf-8', errors='ignore')
    except OSError as e:
        return [{'error': str(e)}]
    new_text, log = sanitize_text(text, patterns)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_text(new_text, encoding='utf-8')
    return log


def main():
    if len(sys.argv) != 4:
        print("FAIL: usage: python sanitize.py <src> <dst> <denylist>", file=sys.stderr)
        sys.exit(2)
    src, dst, denylist = sys.argv[1], sys.argv[2], sys.argv[3]
    pats = load_patterns(denylist)
    log = sanitize_file(src, dst, pats)
    redactions = len([e for e in log if 'category' in e])
    print(f"PASS: sanitized {src} -> {dst} with {redactions} redactions across {len(pats)} patterns")
    errors = [e for e in log if 'error' in e]
    if errors:
        print(f"WARN: errors during sanitize: {errors}", file=sys.stderr)


if __name__ == '__main__':
    main()
