#!/usr/bin/env python3
"""Synthetic UTC-ordering regressions; no dataset or evaluator access."""
import datetime as dt
import unittest
from pit_join import join_asof, JoinConfigError


class TimeAxisTests(unittest.TestCase):
    def test_mixed_offset_spellings_do_not_admit_future_instant(self):
        left = [{"t": "2024-01-01T10:00:00+00:00"}]
        future = [{"t": "2024-01-01T08:00:00-05:00",
                   "available_at": "2024-01-01T08:00:00-05:00", "value": 99}]
        self.assertTrue(join_asof(left, future, on="t")[0]["_pit_miss"])

    def test_equal_instants_and_revision_order_are_utc_based(self):
        left = [{"t": "2024-01-01T10:00:00Z"}]
        rows = [{"t": "2024-01-01T04:00:00-05:00", "available_at": "2024-01-01T04:30:00-05:00", "value": 1},
                {"t": "2024-01-01T09:00:00Z", "available_at": "2024-01-01T11:00:00+01:00", "value": 2}]
        snap = [dict(r) for r in rows]
        out = join_asof(left, rows, on="t", max_lookback=dt.timedelta(hours=2))
        self.assertEqual(out[0]["value"], 2)
        self.assertEqual(out[0]["t"], left[0]["t"])
        self.assertEqual(rows, snap)

    def test_naive_or_mixed_grains_refuse(self):
        for key in [dt.datetime(2024, 1, 1), "2024-01-01T00:00:00", True, float("nan"), "not-a-time"]:
            with self.assertRaises(JoinConfigError):
                join_asof([{"t": key}], [], on="t")
        with self.assertRaises(JoinConfigError):
            join_asof([{"t": "2024-01-01"}], [{"t": "2024-01-01T00:00:00Z", "available_at": "2024-01-01T00:00:00Z"}], on="t")

    def test_date_and_numeric_axes_remain_supported(self):
        out = join_asof([{"t": "2024-01-03"}], [{"t": dt.date(2024, 1, 1), "available_at": "2024-01-02", "value": 7}], on="t")
        self.assertEqual(out[0]["value"], 7)

    def test_invalid_lookback_refuses(self):
        for lookback in [-1, float("nan"), True, dt.timedelta(days=-1)]:
            with self.assertRaises(JoinConfigError):
                join_asof([{"t": 3}], [{"t": 1, "available_at": 2}],
                          on="t", max_lookback=lookback)
        out = join_asof([{"t": 3}], [{"t": 1, "available_at": 2, "value": 7}], on="t")
        self.assertEqual(out[0]["value"], 7)


if __name__ == "__main__":
    unittest.main()
