#!/usr/bin/env python3
"""Self-test for the bin lookup in tools/calibrate-confidence.py (audit D37c).

The confidence map's bins are integer decades built by confidence-calibrator.py
(`lo = c // 10 * 10`, `hi = lo + 9`), so the bin labelled "60-69" stands for the
decade [60, 70). The lookup matched `lo <= v <= hi`, which is right for integer
stated confidences but drops every fractional value in the gap between two bins:
69.5 matched neither 60-69 nor 70-79, so the tool returned calibrated null (and
--quiet echoed the raw, uncalibrated number as if it were the answer).

These cases pin the decade semantics: every value from lo up to but excluding
lo+10 lands in that bin, integer lookups and the >= last-bin clamp are
unchanged, and a value below the lowest bin stays unmapped (the map genuinely
has no data there).

Framework: unittest stdlib (pytest not installed; per tools/ convention).
Run: py tools/test-calibrate-confidence.py
"""
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

TOOLS = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(TOOLS, "calibrate-confidence.py")

_spec = importlib.util.spec_from_file_location("calibrate_confidence", SCRIPT)
cc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cc)

# Same shape as the live map (three decade bins), dated today so the 45-day
# staleness guard never fires and the suite stays deterministic.
MAP_FIXTURE = {
    "generated": date.today().isoformat(),
    "base_rate": 0.34,
    "bins": [
        {"lo": 60, "hi": 69, "n": 10, "stated_mid": 65, "realized": 0.5, "calibrated": 0.393},
        {"lo": 70, "hi": 79, "n": 42, "stated_mid": 75, "realized": 0.31, "calibrated": 0.319},
        {"lo": 80, "hi": 89, "n": 1, "stated_mid": 85, "realized": 0.0, "calibrated": 0.323},
    ],
}

_TMPDIR = None


def setUpModule():
    global _TMPDIR
    _TMPDIR = tempfile.TemporaryDirectory()
    p = Path(_TMPDIR.name) / "confidence-map.json"
    p.write_text(json.dumps(MAP_FIXTURE), encoding="utf-8")
    cc.MAP = p


def tearDownModule():
    _TMPDIR.cleanup()


def lookup(value, quiet=False):
    """Run main() against the synthetic map; return (rc, stdout payload)."""
    buf = io.StringIO()
    old_argv = sys.argv
    sys.argv = [SCRIPT, str(value)] + (["--quiet"] if quiet else [])
    try:
        with contextlib.redirect_stdout(buf):
            rc = cc.main()
    finally:
        sys.argv = old_argv
    text = buf.getvalue().strip()
    return rc, (text if quiet else json.loads(text))


class TestBinLookup(unittest.TestCase):
    def test_fractional_between_bins_is_mapped(self):
        # D37c: 69.5 sits in the 60-69 decade; it used to fall through to null.
        rc, out = lookup(69.5)
        self.assertEqual(rc, 0)
        self.assertEqual(out["bin"], "60-69")
        self.assertEqual(out["calibrated"], 0.393)
        self.assertEqual(out["bin_n"], 10)

    def test_fractional_just_under_next_bin(self):
        rc, out = lookup(79.999)
        self.assertEqual(rc, 0)
        self.assertEqual(out["bin"], "70-79")
        self.assertEqual(out["calibrated"], 0.319)

    def test_fractional_inside_a_bin(self):
        _, out = lookup(75.5)
        self.assertEqual(out["bin"], "70-79")
        self.assertEqual(out["calibrated"], 0.319)

    def test_integer_lookups_unchanged(self):
        for v, want in ((60, "60-69"), (69, "60-69"), (70, "70-79"),
                        (79, "70-79"), (80, "80-89"), (89, "80-89")):
            with self.subTest(v=v):
                _, out = lookup(v)
                self.assertEqual(out["bin"], want)

    def test_above_last_bin_still_clamps(self):
        for v in (95, 99.5, 100):
            with self.subTest(v=v):
                _, out = lookup(v)
                self.assertEqual(out["bin"], "80-89")
                self.assertEqual(out["calibrated"], 0.323)

    def test_below_lowest_bin_stays_unmapped(self):
        # The map has no evidence under 60: null is the honest answer, not a guess.
        for v in (59.5, 12):
            with self.subTest(v=v):
                rc, out = lookup(v)
                self.assertEqual(rc, 0)
                self.assertIsNone(out["calibrated"])
                self.assertIsNone(out["bin"])

    def test_quiet_prints_the_calibrated_value_for_a_fractional_input(self):
        # Before the fix this echoed "69.5" -- the raw stated number, which a
        # caller would have recorded as if it had been calibrated.
        _, text = lookup(69.5, quiet=True)
        self.assertEqual(text, "0.393")


if __name__ == "__main__":
    unittest.main(verbosity=2)
