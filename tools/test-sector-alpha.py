#!/usr/bin/env python3
"""Self-test for corr() in tools/sector-alpha.py (audit defect D35).

corr() took the last n bars of each ticker and zipped them by POSITION. Any
calendar difference between the two histories -- a halted session, a crypto
series that trades weekends, a bar that simply has not loaded yet -- silently
shifted one return series against the other by a day. Two identical price
paths, one of them missing a single interior day, came out at 0.683 in the
audit's example (0.4311 on this file's test data) instead of 1.0, and two series sharing only a handful of dates still produced a confident
number because the >= 30 bar guard counted each ticker's own rows.

The oracle here is construction, not arithmetic: if the two closes on every
shared date are the same path (or a constant multiple of it), the correlation
of their returns on those dates is exactly 1.0, whatever days are missing.

Framework: unittest stdlib (pytest not installed; per tools/ convention).
Run: py tools/test-sector-alpha.py
"""
import importlib.util
import os
import random
import sqlite3
import sys
import unittest
from datetime import date, timedelta

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)

_spec = importlib.util.spec_from_file_location(
    "sector_alpha", os.path.join(TOOLS, "sector-alpha.py"))
sa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sa)

SCHEMA = """CREATE TABLE bars (
  ticker TEXT NOT NULL,
  date   TEXT NOT NULL,
  close  REAL NOT NULL,
  src    TEXT NOT NULL DEFAULT 'test',
  PRIMARY KEY (ticker, date)
)"""


def sessions(count, start="2026-01-05"):
    """`count` weekday dates as ISO strings."""
    d = date.fromisoformat(start)
    out = []
    while len(out) < count:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def walk(count, seed=20260921, start=100.0):
    """Deterministic price path; moves are large enough that a one-day shift
    is unmistakable."""
    rng = random.Random(seed)
    px, out = start, []
    for _ in range(count):
        px *= 1.0 + rng.uniform(-0.04, 0.04)
        out.append(round(px, 4))
    return out


def store(rows):
    con = sqlite3.connect(":memory:")
    con.execute(SCHEMA)
    con.executemany("INSERT INTO bars (ticker, date, close) VALUES (?,?,?)", rows)
    return con


class TestCorrDateAlignment(unittest.TestCase):
    def test_identical_series_same_calendar(self):
        days, px = sessions(60), walk(60)
        rows = [("AAA", d, p) for d, p in zip(days, px)]
        rows += [("BBB", d, p) for d, p in zip(days, px)]
        self.assertAlmostEqual(sa.corr(store(rows), "AAA", "BBB"), 1.0, places=9)

    def test_identical_series_one_missing_interior_day(self):
        # D35: BBB is the same path with session 30 absent. Positionally zipped
        # this scored 0.4311 on this data; aligned on date it is the same path,
        # so 1.0.
        days, px = sessions(60), walk(60)
        rows = [("AAA", d, p) for d, p in zip(days, px)]
        rows += [("BBB", d, p) for i, (d, p) in enumerate(zip(days, px)) if i != 30]
        self.assertAlmostEqual(sa.corr(store(rows), "AAA", "BBB"), 1.0, places=9)

    def test_scaled_series_with_several_gaps(self):
        # A constant multiple has identical returns; holes on either side must
        # not change that.
        days, px = sessions(70), walk(70)
        skip_a, skip_b = {11, 40}, {12, 41, 55}
        rows = [("AAA", d, p) for i, (d, p) in enumerate(zip(days, px)) if i not in skip_a]
        rows += [("BBB", d, p * 3.0) for i, (d, p) in enumerate(zip(days, px)) if i not in skip_b]
        self.assertAlmostEqual(sa.corr(store(rows), "AAA", "BBB"), 1.0, places=9)

    def test_too_few_shared_dates_returns_none(self):
        # 60 bars each but only 20 dates in common: there is no 30-bar sample
        # to correlate, and inventing one is exactly the bug.
        days, px = sessions(100), walk(100)
        rows = [("AAA", d, p) for i, (d, p) in enumerate(zip(days, px)) if i < 60]
        rows += [("BBB", d, p) for i, (d, p) in enumerate(zip(days, px)) if i >= 40]
        self.assertIsNone(sa.corr(store(rows), "AAA", "BBB"))

    def test_short_history_still_returns_none(self):
        days, px = sessions(20), walk(20)
        rows = [("AAA", d, p) for d, p in zip(days, px)]
        rows += [("BBB", d, p) for d, p in zip(days, px)]
        self.assertIsNone(sa.corr(store(rows), "AAA", "BBB"))

    def test_window_is_the_last_n_shared_dates(self):
        # Before the window: BBB moves opposite to AAA. Inside it: identical.
        # A correct n=40 window sees only the identical tail.
        days, px = sessions(90), walk(90)
        rows = [("AAA", d, p) for d, p in zip(days, px)]
        b = []
        for i, (d, p) in enumerate(zip(days, px)):
            b.append(("BBB", d, p if i >= 45 else 200.0 - p))
        self.assertAlmostEqual(sa.corr(store(rows + b), "AAA", "BBB", n=40), 1.0, places=9)

    def test_window_on_mixed_calendars(self):
        # AAA trades every calendar day (a crypto calendar); BBB trades weekdays.
        # The last 40 SHARED dates are identical paths; everything earlier moves
        # opposite. Taking each ticker's own last 40 rows before intersecting
        # leaves ~28 shared dates and returns None; the right window is 1.0.
        start = date(2026, 1, 1)
        cal = [(start + timedelta(days=i)).isoformat() for i in range(150)]
        px = walk(150)
        rows = [("AAA", d, p) for d, p in zip(cal, px)]
        weekdays = [(d, p) for d, p in zip(cal, px) if date.fromisoformat(d).weekday() < 5]
        tail = set(d for d, _ in weekdays[-40:])
        rows += [("BBB", d, p if d in tail else 200.0 - p) for d, p in weekdays]
        self.assertAlmostEqual(sa.corr(store(rows), "AAA", "BBB", n=40), 1.0, places=9)

    def test_one_history_ending_early(self):
        # BBB's history stops 70 sessions before AAA's. They still share 130
        # dates, and the last 90 of those are identical: the answer is 1.0,
        # not None.
        days, px = sessions(200), walk(200)
        rows = [("AAA", d, p) for d, p in zip(days, px)]
        rows += [("BBB", d, p) for d, p in zip(days[:130], px[:130])]
        self.assertAlmostEqual(sa.corr(store(rows), "AAA", "BBB", n=90), 1.0, places=9)


if __name__ == "__main__":
    unittest.main(verbosity=2)
