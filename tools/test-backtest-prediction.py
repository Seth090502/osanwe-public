#!/usr/bin/env python3
"""Self-test for the factor-bucket keyword counts in tools/backtest-prediction.py
(audit defect D36).

parse_analysis_text() tallies how often an analysis leans on technical,
fundamental, sentiment, macro and insider evidence, and those shares feed the
calibration factor reports. The tallies were plain substring searches, so
"steps" counted as EPS, "hyperscaler" as hype, "operates" as rates and
"federal" as Fed. A sentence citing none of the factor words came back as
fundamental/sentiment/macro 0.333 each -- an attribution invented out of
ordinary English.

The oracle is the sentence: text with no factor word must score zero
everywhere, text with one must score only that bucket, and the words the tool
always did count (plurals such as "margins", prefixes such as "geopolitical")
must keep counting.

Framework: unittest stdlib (pytest not installed; per tools/ convention).
Run: py tools/test-backtest-prediction.py
"""
import importlib.util
import os
import sys
import unittest

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)

_spec = importlib.util.spec_from_file_location(
    "backtest_prediction", os.path.join(TOOLS, "backtest-prediction.py"))
bp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bp)

HEADER = '---\nticker: "TEST"\nrating: "BUY"\nconfidence: 70\n---\n\n'


def factors(body):
    return bp.parse_analysis_text(HEADER + body, "test-analysis-2026-01-01.md")["factors"]


class TestFactorKeywordBoundaries(unittest.TestCase):
    def test_sentence_with_no_factor_word_scores_nothing(self):
        # D36: "steps" -> EPS, "hyperscaler" -> hype, "operates" -> rates,
        # "federal" -> Fed. Before the fix this read 0.2/0.2/0.2/0.4 -- the old
        # RSI pattern also matched inside "oversight".
        f = factors("The hyperscaler steps through the build as the company "
                    "operates under federal oversight.")
        self.assertEqual(set(f.values()), {0.0})

    def test_each_false_positive_individually(self):
        for body, bucket in (("Management steps back.", "fundamental"),
                             ("A hyperscaler customer.", "sentiment"),
                             ("The plant operates at capacity.", "macro"),
                             ("A federal review is pending.", "macro")):
            with self.subTest(body=body):
                self.assertEqual(factors(body)[bucket], 0.0)

    def test_field_names_still_count(self):
        # The vault writes factors as field names, and a regex word boundary
        # treats digits and `_` as part of the word: `\b` would have stopped
        # counting every one of these.
        self.assertEqual(factors("RSI14 at 62; rsi_14 rising.")["technical"], 1.0)
        self.assertEqual(factors("fcf_yield 4.1%; piotroski_f_score 7.")["fundamental"], 1.0)

    def test_real_keywords_still_count(self):
        f = factors("Revenue and EPS beat; gross margin expanded.")
        self.assertEqual(f["fundamental"], 1.0)
        self.assertEqual(f["sentiment"], 0.0)
        self.assertEqual(f["macro"], 0.0)

    def test_plurals_still_count(self):
        # These matched before the fix (substring) and must keep matching.
        for body, bucket in (("Margins expanded.", "fundamental"),
                             ("Buybacks resumed.", "insider_flow"),
                             ("Insiders bought.", "insider_flow"),
                             ("Narratives shifted.", "sentiment"),
                             ("Tariffs bite.", "macro"),
                             ("Drawdowns were shallow.", "technical")):
            with self.subTest(body=body):
                self.assertEqual(factors(body)[bucket], 1.0)

    def test_prefix_and_symbol_terms_still_count(self):
        for body, bucket in (("Geopolitical risk is elevated.", "macro"),
                             ("The 10Y yield fell.", "macro"),
                             ("13F filings show adds.", "insider_flow"),
                             ("RSI is 62 and MACD turned.", "technical"),
                             ("A 200DMA reclaim.", "technical")):
            with self.subTest(body=body):
                self.assertGreater(factors(body)[bucket], 0.0)

    def test_buckets_still_share_out_to_one(self):
        f = factors("Revenue grew; the regime is risk-on; insiders bought.")
        self.assertAlmostEqual(sum(f.values()), 1.0, places=2)  # 3x round(1/3, 3)
        self.assertEqual(f["technical"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
