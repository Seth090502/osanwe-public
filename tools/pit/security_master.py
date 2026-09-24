#!/usr/bin/env python3
"""Canonical instrument identity (point-in-time security master).

Maps each ticker to a canonical identity record:

    ticker -> {name, asset_class, exchange, first_bar_date,
               last_bar_date, status}

Sources (read-only):
  * SQLite bars/factors database (default: Efforts/osanwe-v2-overhaul/
    _work/factors.db). Table ``bars`` supplies first/last bar dates.
  * Entity notes at wiki/entities/tickers/<TICKER>.md. YAML frontmatter
    ``aliases`` / H1 title supply name hints; frontmatter ``status`` and
    body text (e.g. "NASDAQ: AAOI") supply exchange/status hints.
    Notes are optional -- absence degrades gracefully, never fails.

Output CSV columns:
    ticker,name,asset_class,exchange,first_bar_date,last_bar_date,status

Usage:
    python tools/pit/security_master.py                 # build CSV
    python tools/pit/security_master.py --selftest      # run self-tests

Constraints honored: ASCII only, stdlib only, no network, sqlite opened
read-only via URI mode.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sqlite3
import sys
import tempfile
import unittest.mock  # noqa: F401  (kept for parity with test harness)
from typing import Dict, Iterable, List, Optional

VAULT_ROOT = os.environ.get("OSANWE_VAULT", "/path/to/vault")
DEFAULT_DB = os.path.join(
    VAULT_ROOT, "Efforts/osanwe-v2-overhaul/_work/factors.db"
)
DEFAULT_NOTES_DIR = os.path.join(VAULT_ROOT, "wiki/entities/tickers")
DEFAULT_OUT = os.path.join(
    VAULT_ROOT, "Efforts/osanwe-v2-overhaul/_work/fis-data/security-master.csv"
)

CSV_COLUMNS = [
    "ticker",
    "name",
    "asset_class",
    "exchange",
    "first_bar_date",
    "last_bar_date",
    "status",
]

STALE_DAYS = 45  # gap vs newest bar in universe before status -> 'stale'

# Conservative ETF allow-list used only for asset_class classification;
# anything not listed and lacking a crypto suffix is treated as equity.
ETF_TICKERS = frozenset(
    {
        "SPY", "QQQ", "SMH", "SOXX", "IAU", "ITA", "PPA", "VDE", "VGT",
        "VOO", "VOX", "XAR", "XLE", "XLF", "XLI", "XLP", "XLRE", "XLU",
        "XLV", "XLY",
    }
)

EXCHANGE_PATTERNS = [
    (re.compile(r"\bNASDAQ[:\s\-]", re.I), "NASDAQ"),
    (re.compile(r"\bNYSE\s*[:\-\s]\s*[A-Z]{2,}", re.I), "NYSE"),
    (re.compile(r"\bNYSEAMERICAN\b|\bNYSE\s+AMERICAN\b", re.I), "NYSEAMERICAN"),
    (re.compile(r"\bAMEX\b", re.I), "AMEX"),
    (re.compile(r"\bOTC\s*(?:MKTS|QX|QB)?\b|\bOTC\s+ADR\b", re.I), "OTC"),
]


class SecurityMasterError(Exception):
    """Base class for security-master errors."""


class UnknownTickerError(SecurityMasterError):
    """Raised when a ticker cannot be resolved to any known instrument."""


class DuplicateSymbolError(SecurityMasterError):
    """Raised when two raw symbols collide case-insensitively."""


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def open_db_readonly(db_path: str) -> sqlite3.Connection:
    """Open the factors database strictly read-only."""
    path = os.path.abspath(db_path).replace("\\", "/")
    uri = "file:///" + path.lstrip("/") + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def load_bar_ranges(conn: sqlite3.Connection) -> Dict[str, Dict[str, object]]:
    """Aggregate bars into per-ticker first/last dates and row counts.

    Keys are canonical (upper-cased) tickers.
    """
    cur = conn.execute(
        "SELECT UPPER(ticker), MIN(date), MAX(date), COUNT(*) "
        "FROM bars GROUP BY UPPER(ticker)"
    )
    ranges: Dict[str, Dict[str, object]] = {}
    for canon, first, last, n in cur.fetchall():
        ranges[canon] = {
            "first_bar_date": first,
            "last_bar_date": last,
            "bar_count": int(n),
        }
    return ranges


def _parse_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value.strip()


def _parse_inline_list(value: str) -> List[str]:
    inner = value.strip()
    if inner.startswith("[") and inner.endswith("]"):
        inner = inner[1:-1]
        items = []
        for part in inner.split(","):
            part = part.strip()
            if not part:
                continue
            items.append(_parse_scalar(part))
        return items
    return [_parse_scalar(inner)] if inner else []


def parse_frontmatter(text: str) -> Optional[Dict[str, object]]:
    """Minimal YAML-frontmatter parser (flat scalars + block/inline lists).

    Returns None when the document has no frontmatter block.
    """
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    if len(lines) < 2 or lines[0].strip() != "---":
        return None
    fm: Dict[str, object] = {}
    current_list_key: Optional[str] = None
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if not stripped:
            continue
        if stripped.startswith("- ") and current_list_key is not None:
            fm[current_list_key].append(_parse_scalar(stripped[2:]))
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):(.*)$", stripped)
        if not m:
            current_list_key = None
            continue
        key, rest = m.group(1), m.group(2).strip()
        if rest == "":
            fm[key] = []
            current_list_key = key
        elif rest.startswith("["):
            fm[key] = _parse_inline_list(rest)
            current_list_key = None
        else:
            fm[key] = _parse_scalar(rest)
            current_list_key = None
    return fm


def _is_symbol_alias(alias: str) -> bool:
    """True when the alias looks like a bare symbol rather than prose/slug."""
    if alias.isupper() and alias.replace("-", "").replace(".", "").isalnum():
        return True
    return "-" in alias or (alias == alias.lower() and alias.isalnum())


def extract_name_hint(text: str, fm: Optional[Dict[str, object]]) -> str:
    """Best-effort company name from frontmatter aliases or H1 title."""
    if fm:
        aliases = fm.get("aliases")
        if isinstance(aliases, list):
            for alias in aliases:
                alias = str(alias).strip()
                if alias and not _is_symbol_alias(alias):
                    return alias
    m = re.search(r"^#\s+[A-Z0-9.\-]+\s+--\s+(.+?)\s*$", text, re.M)
    if m:
        return m.group(1).strip()
    m = re.search(r"^#\s+(.+?)\s*$", text, re.M)
    if m:
        return m.group(1).strip()
    return ""


def extract_exchange_hint(text: str) -> str:
    """Scan note body for an exchange mention ('NASDAQ: AAOI', OTC, ...)."""
    for pattern, label in EXCHANGE_PATTERNS:
        if pattern.search(text):
            return label
    return ""


def load_entity_notes(
    notes_dir: str, tickers: Iterable[str]
) -> Dict[str, Optional[Dict[str, object]]]:
    """Load optional per-ticker entity notes.

    Returns a mapping keyed by canonical ticker. Values are None when no
    note exists (missing notes are expected and handled downstream).
    """
    out: Dict[str, Optional[Dict[str, object]]] = {}
    for canon in tickers:
        path = os.path.join(notes_dir, canon + ".md")
        if not os.path.isfile(path):
            out[canon] = None
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            out[canon] = None
            continue
        fm = parse_frontmatter(text)
        note_status = ""
        if fm:
            raw_status = fm.get("status")
            if isinstance(raw_status, str) and raw_status.strip():
                note_status = raw_status.strip().lower()
        out[canon] = {
            "name": extract_name_hint(text, fm),
            "exchange": extract_exchange_hint(text),
            "note_status": note_status,
        }
    return out


# ---------------------------------------------------------------------------
# Building the master
# ---------------------------------------------------------------------------

def classify_asset_class(canon_ticker: str) -> str:
    if canon_ticker.endswith("-USD"):
        return "crypto"
    if canon_ticker in ETF_TICKERS:
        return "etf"
    return "equity"


def derive_status(
    note_status: str, last_bar_date: str, universe_last_date: str
) -> str:
    """Status precedence: entity-note status, then recency heuristic."""
    if note_status:
        return note_status
    try:
        y1, m1, d1 = (int(p) for p in last_bar_date.split("-"))
        y2, m2, d2 = (int(p) for p in universe_last_date.split("-"))
    except ValueError:
        return "unknown"
    # Approximate day difference (good enough at monthly granularity).
    days1 = y1 * 372 + m1 * 31 + d1
    days2 = y2 * 372 + m2 * 31 + d2
    if days2 - days1 > STALE_DAYS:
        return "stale"
    return "active"


def build_master(
    bar_ranges: Dict[str, Dict[str, object]],
    notes: Dict[str, Optional[Dict[str, object]]],
) -> List[Dict[str, str]]:
    """Assemble master rows keyed by canonical (upper-case) ticker.

    Raises DuplicateSymbolError when two distinct raw symbols collapse to
    the same case-insensitive key with conflicting identities.
    """
    seen_raw: Dict[str, str] = {}
    universe_last = max(
        (str(r["last_bar_date"]) for r in bar_ranges.values()), default=""
    )
    rows: List[Dict[str, str]] = []
    for canon in sorted(bar_ranges):
        rng = bar_ranges[canon]
        raw = str(rng.get("raw_ticker", canon))
        prev = seen_raw.setdefault(canon, raw)
        if prev != raw:
            raise DuplicateSymbolError(
                "case-insensitive symbol collision: %r vs %r" % (prev, raw)
            )
        note = notes.get(canon)
        name = str(note["name"]) if note and note["name"] else canon
        exchange = str(note["exchange"]) if note and note["exchange"] else ""
        note_status = (
            str(note["note_status"]) if note and note["note_status"] else ""
        )
        rows.append(
            {
                "ticker": canon,
                "name": name,
                "asset_class": classify_asset_class(canon),
                "exchange": exchange,
                "first_bar_date": str(rng["first_bar_date"]),
                "last_bar_date": str(rng["last_bar_date"]),
                "status": derive_status(
                    note_status, str(rng["last_bar_date"]), universe_last
                ),
            }
        )
    return rows


class SecurityMaster:
    """Case-insensitive lookup index over master rows."""

    def __init__(self, rows: Iterable[Dict[str, str]]):
        self._by_canon: Dict[str, Dict[str, str]] = {}
        for row in rows:
            canon = row["ticker"].upper()
            if canon in self._by_canon:
                raise DuplicateSymbolError(
                    "duplicate case-insensitive symbol: %s" % canon
                )
            self._by_canon[canon] = row

    def __len__(self) -> int:
        return len(self._by_canon)

    def get(self, ticker: str) -> Dict[str, str]:
        """Resolve a ticker (any casing) to its canonical identity record."""
        canon = ticker.upper()
        if canon not in self._by_canon:
            raise UnknownTickerError("unknown ticker: %r" % ticker)
        return dict(self._by_canon[canon])

    def rows(self) -> List[Dict[str, str]]:
        return [dict(self._by_canon[c]) for c in sorted(self._by_canon)]


def write_csv(rows: List[Dict[str, str]], out_path: str) -> int:
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="ascii", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            clean = {
                k: v.encode("ascii", "replace").decode("ascii")
                for k, v in row.items()
            }
            writer.writerow(clean)
    return len(rows)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def build_from_sources(
    db_path: str = DEFAULT_DB,
    notes_dir: str = DEFAULT_NOTES_DIR,
) -> SecurityMaster:
    conn = open_db_readonly(db_path)
    try:
        bar_ranges = load_bar_ranges(conn)
    finally:
        conn.close()
    notes = load_entity_notes(notes_dir, bar_ranges.keys())
    rows = build_master(bar_ranges, notes)
    return SecurityMaster(rows)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the point-in-time security master CSV."
    )
    parser.add_argument("--db", default=DEFAULT_DB, help="factors.db path")
    parser.add_argument("--notes-dir", default=DEFAULT_NOTES_DIR,
                        help="entity ticker-notes directory")
    parser.add_argument("--out", default=DEFAULT_OUT, help="output CSV path")
    parser.add_argument("--selftest", action="store_true",
                        help="run built-in self-tests and exit")
    args = parser.parse_args(argv)

    if args.selftest:
        return run_selftests()

    master = build_from_sources(args.db, args.notes_dir)
    n = write_csv(master.rows(), args.out)
    print("security master rows written: %d -> %s" % (n, args.out))
    return 0


# ---------------------------------------------------------------------------
# Self-tests (pytest-style functions + unittest-free runner)
# ---------------------------------------------------------------------------

def _sample_rows():
    return [
        {
            "ticker": "AAOI",
            "name": "Applied Optoelectronics",
            "asset_class": "equity",
            "exchange": "NASDAQ",
            "first_bar_date": "2021-08-24",
            "last_bar_date": "2026-08-21",
            "status": "active",
        },
        {
            "ticker": "BTC-USD",
            "name": "BTC-USD",
            "asset_class": "crypto",
            "exchange": "",
            "first_bar_date": "2021-01-01",
            "last_bar_date": "2026-08-21",
            "status": "active",
        },
    ]


def test_unknown_ticker():
    master = SecurityMaster(_sample_rows())
    try:
        master.get("ZZZZZ")
    except UnknownTickerError as exc:
        assert "ZZZZZ" in str(exc)
    else:
        raise AssertionError("expected UnknownTickerError for ZZZZZ")
    # Lookups are case-insensitive for KNOWN tickers.
    assert master.get("aaoi")["ticker"] == "AAOI"


def test_duplicate_case_insensitive_symbols():
    rows = _sample_rows()
    dupe = dict(rows[0])
    dupe["ticker"] = "aaoi"  # same identity, different casing
    try:
        SecurityMaster(rows + [dupe])
    except DuplicateSymbolError:
        pass
    else:
        raise AssertionError("expected DuplicateSymbolError for aaoi/AAOI")


def test_missing_entity_note():
    bar_ranges = {
        "XYZ": {"first_bar_date": "2024-01-02",
                "last_bar_date": "2024-03-01", "bar_count": 5},
        # A second, fresh listing sets the universe reference date so the
        # recency heuristic can flag XYZ as stale.
        "NEW": {"first_bar_date": "2026-08-03",
                "last_bar_date": "2026-08-21", "bar_count": 10},
    }
    notes = {"XYZ": None, "NEW": None}  # no markdown notes on disk
    rows = build_master(bar_ranges, notes)
    assert len(rows) == 2
    by_ticker = {r["ticker"]: r for r in rows}
    row = by_ticker["XYZ"]
    # No note: falls back to the symbol itself, no exchange hint, and a
    # recency-based status (old last-bar vs fresh universe -> stale).
    assert row["name"] == "XYZ"
    assert row["exchange"] == ""
    assert row["status"] == "stale"
    # The missing note must not break the fresh listing either.
    assert by_ticker["NEW"]["name"] == "NEW"
    assert by_ticker["NEW"]["status"] == "active"


def run_selftests() -> int:
    tests = [test_unknown_ticker,
             test_duplicate_case_insensitive_symbols,
             test_missing_entity_note]
    failures = 0
    for fn in tests:
        try:
            fn()
        except AssertionError as exc:
            failures += 1
            print("FAIL %s: %s" % (fn.__name__, exc))
        except Exception as exc:  # noqa: BLE001 - report and continue
            failures += 1
            print("ERROR %s: %r" % (fn.__name__, exc))
        else:
            print("PASS %s" % fn.__name__)
    total = len(tests) - failures
    print("%d/%d self-tests passed" % (total, len(tests)))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
