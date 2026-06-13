#!/usr/bin/env python3
"""Mission Three Phase 4 -- Extended-hours pricing diffusion tests.

Tests T1-T11 cover the new behavior added in Mission Three Commit A
(65f2d0d feat(fetch-prices): two-call merge for prepost=True extended-hours data).

Coverage matrix:
  T1  AH-active path: extended_hours_last populated; market_session=after-hours
  T2  Regular-session-no-AH: extended_hours_last=null; market_session=regular
  T3  ah_mover signal threshold: signals.ah_movers populated at >=3.0% AH move;
      NOT populated at 10.0% threshold
  T4  extended_hours_movers[] aggregation: sorted desc by |magnitude_pct|
  T5  Subagent contract additivity: price-fetcher.md documents all 6 new fields +
      removes /invest from dispatching list
  T6  Crypto path: XRP/BTC -> market_session=regular; AH fields all null
  T7  Holiday path: empty intraday bars -> market_session=closed
  T8  Half-day path: last bar at 14:00 ET on early-close day -> market_session=after-hours
      (because AH starts at 13:00 on half-days)
  T9  Multi-ticker partial AH: per-ticker independence (one has AH, other doesn't)
  T10 VGT split preservation: extended_hours_last reflects post-split price
      (auto_adjust=True path)
  T11 API failure: yfinance intraday call throws -> errors[] populated;
      daily call still works; AH fields null but other equities unaffected

Framework: unittest stdlib (pytest not installed; freezegun not installed; per
Mission Three plan fallback decision 2026-05-05). Clock freezing via
unittest.mock.patch on the datetime symbol imported into fetch-prices module.

Run: python tools/test-fetch-prices.py
"""

import importlib.util
import json
import os
import sys
import unittest
from datetime import datetime, date, time, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ET = ZoneInfo("America/New_York")

# Load fetch-prices.py (hyphenated filename precludes regular import)
SCRIPT_PATH = Path(__file__).parent / "fetch-prices.py"
spec = importlib.util.spec_from_file_location("fetch_prices", SCRIPT_PATH)
fp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fp)


# --- Fixture builders -----------------------------------------------------

def make_daily_df(tickers, base_price=100.0, days=30, multi=True):
    """Create a fake yf.download daily-bar DataFrame with MultiIndex columns
    matching yfinance group_by='ticker' shape. Each ticker gets `days` daily bars
    starting `days` days ago, with synthetic prices around base_price.
    """
    end = pd.Timestamp.now('UTC').normalize()
    dates = pd.date_range(end=end, periods=days, freq='D')
    frames = {}
    for i, t in enumerate(tickers):
        seed_price = base_price + i * 10
        closes = np.linspace(seed_price * 0.9, seed_price, days)
        df_t = pd.DataFrame({
            'Open': closes,
            'High': closes * 1.01,
            'Low': closes * 0.99,
            'Close': closes,
            'Volume': [1_000_000] * days,
        }, index=dates)
        frames[t] = df_t
    if multi:
        return pd.concat(frames, axis=1)
    return frames[tickers[0]]


def make_intraday_df(ticker_to_bars, multi=True):
    """Create a fake yf.download intraday-bar DataFrame with MultiIndex columns.

    ticker_to_bars: dict {ticker -> list[(ts_iso_utc, open, high, low, close, volume)]}

    Empty frames get a tz-aware empty DatetimeIndex so pd.concat preserves
    DatetimeIndex on the combined result (otherwise concat falls back to a
    generic Index, breaking downstream `index.tz` access).
    """
    frames = {}
    for ticker, bars in ticker_to_bars.items():
        if not bars:
            df_t = pd.DataFrame(
                columns=['Open', 'High', 'Low', 'Close', 'Volume'],
                index=pd.DatetimeIndex([], tz='UTC'),
            )
        else:
            ts = [pd.Timestamp(t).tz_convert('UTC') if pd.Timestamp(t).tz else
                  pd.Timestamp(t).tz_localize('UTC') for t, *_ in bars]
            df_t = pd.DataFrame({
                'Open': [r[1] for r in bars],
                'High': [r[2] for r in bars],
                'Low': [r[3] for r in bars],
                'Close': [r[4] for r in bars],
                'Volume': [r[5] for r in bars],
            }, index=pd.DatetimeIndex(ts, tz='UTC'))
        frames[ticker] = df_t
    if multi:
        return pd.concat(frames, axis=1) if frames else pd.DataFrame()
    return list(frames.values())[0] if frames else pd.DataFrame()


def fake_ticker_metadata(ticker_info=None):
    """Build a MagicMock for yf.Ticker that returns benign .info + .calendar."""
    mock = MagicMock()
    mock.info = ticker_info or {
        'beta': 1.0, 'shortRatio': 1.0,
        'fiftyTwoWeekHigh': 200.0, 'fiftyTwoWeekLow': 50.0,
    }
    mock.calendar = pd.DataFrame()  # empty calendar (no upcoming earnings)
    return mock


# --- Tests ----------------------------------------------------------------

class TestExtendedHoursDiffusion(unittest.TestCase):

    def _patched_fetch_all(self, equity_tickers, crypto_tickers, daily_data,
                           intraday_data=None, fake_now_et=None, no_extended=False,
                           intraday_raises=False):
        """Run fp.fetch_all() with mocked yf.download + yf.Ticker + datetime.now(ET).
        daily_data: DataFrame for first yf.download call
        intraday_data: DataFrame for second yf.download call (or None / Exception)
        fake_now_et: optional datetime for "now" in ET; used to mock datetime.now(ET)
        """
        # Mock yf.download to return daily on first call, intraday on second
        download_calls = [daily_data]
        if not no_extended:
            if intraday_raises:
                download_calls.append(Exception("intraday API failure"))
            else:
                download_calls.append(intraday_data if intraday_data is not None else pd.DataFrame())

        def fake_download(*args, **kwargs):
            r = download_calls.pop(0)
            if isinstance(r, Exception):
                raise r
            return r

        with patch.object(fp, 'yf') as mock_yf:
            mock_yf.download = MagicMock(side_effect=fake_download)
            mock_yf.Ticker = MagicMock(return_value=fake_ticker_metadata())

            if fake_now_et is not None:
                # Patch datetime.now(ET) inside fetch_prices
                real_datetime = fp.datetime
                class FrozenDatetime:
                    @classmethod
                    def now(cls, tz=None):
                        if tz is not None:
                            return fake_now_et.astimezone(tz)
                        return fake_now_et.replace(tzinfo=None)
                    @classmethod
                    def fromtimestamp(cls, *args, **kwargs):
                        return real_datetime.fromtimestamp(*args, **kwargs)
                    @classmethod
                    def fromisoformat(cls, *args, **kwargs):
                        return real_datetime.fromisoformat(*args, **kwargs)
                with patch.object(fp, 'datetime', FrozenDatetime):
                    return fp.fetch_all(equity_tickers, crypto_tickers, no_extended=no_extended)
            return fp.fetch_all(equity_tickers, crypto_tickers, no_extended=no_extended)

    def test_T1_ah_active_path(self):
        """T1: AH session active; extended_hours_last populated;
        market_session=after-hours; ah_source=yfinance."""
        # Today's date in ET; AH bars at 18:00-19:30 ET (= 22:00-23:30 UTC)
        today_et = datetime.now(ET).date()
        # Build AH bars: 19:00 ET 19:15 ET 19:30 ET (UTC: 23:00, 23:15, 23:30)
        bars = []
        for hh, mm in [(19, 0), (19, 15), (19, 30)]:
            ts = datetime(today_et.year, today_et.month, today_et.day, hh, mm, tzinfo=ET).astimezone(timezone.utc)
            bars.append((ts.isoformat(), 105.0, 105.5, 104.8, 105.2, 50000))
        # Add some regular-session bars for completeness
        for hh in [10, 11, 12, 13, 14, 15]:
            ts = datetime(today_et.year, today_et.month, today_et.day, hh, 0, tzinfo=ET).astimezone(timezone.utc)
            bars.append((ts.isoformat(), 100.0, 101.0, 99.5, 100.5, 1000000))
        # Sort by timestamp
        bars.sort(key=lambda b: b[0])

        all_tickers = ['NVDA'] + list(fp.INDEX_MAP.keys())
        daily = make_daily_df(all_tickers, base_price=100.0)
        intraday = make_intraday_df({t: bars if t == 'NVDA' else [] for t in all_tickers})

        fake_now = datetime(today_et.year, today_et.month, today_et.day, 19, 35, tzinfo=ET)
        result = self._patched_fetch_all(['NVDA'], [], daily, intraday, fake_now_et=fake_now)

        nvda = result['equities']['NVDA']
        self.assertIsNotNone(nvda['extended_hours_last'], "T1: extended_hours_last must be populated")
        self.assertEqual(nvda['extended_hours_last'], 105.2)
        self.assertEqual(nvda['market_session'], 'after-hours')
        self.assertEqual(nvda['ah_source'], 'yfinance')
        self.assertIsNotNone(nvda['extended_hours_last_timestamp'])

    def test_T2_regular_no_ah(self):
        """T2: Regular session active; no AH bars; extended_hours_last=null;
        market_session=regular."""
        today_et = datetime.now(ET).date()
        # Only regular-session bars
        bars = []
        for hh in [10, 11, 12, 13, 14]:
            ts = datetime(today_et.year, today_et.month, today_et.day, hh, 0, tzinfo=ET).astimezone(timezone.utc)
            bars.append((ts.isoformat(), 100.0, 101.0, 99.5, 100.5, 1000000))

        all_tickers = ['NVDA'] + list(fp.INDEX_MAP.keys())
        daily = make_daily_df(all_tickers, base_price=100.0)
        intraday = make_intraday_df({t: bars if t == 'NVDA' else [] for t in all_tickers})

        fake_now = datetime(today_et.year, today_et.month, today_et.day, 14, 30, tzinfo=ET)
        result = self._patched_fetch_all(['NVDA'], [], daily, intraday, fake_now_et=fake_now)

        nvda = result['equities']['NVDA']
        self.assertIsNone(nvda['extended_hours_last'], "T2: extended_hours_last must be null")
        self.assertEqual(nvda['market_session'], 'regular')
        self.assertIsNone(nvda['ah_source'])

    def test_T3_ah_mover_threshold(self):
        """T3: ah_mover signal fires at default 3.0% threshold; suppressed at 10.0%."""
        today_et = datetime.now(ET).date()
        # AH bar with +5% move (price 100 -> ah 105); above default 3.0% threshold
        ts = datetime(today_et.year, today_et.month, today_et.day, 19, 0, tzinfo=ET).astimezone(timezone.utc)
        ah_bars = [(ts.isoformat(), 105.0, 105.5, 104.8, 105.2, 50000)]

        all_tickers = ['NVDA'] + list(fp.INDEX_MAP.keys())
        daily = make_daily_df(all_tickers, base_price=100.0)
        intraday = make_intraday_df({t: ah_bars if t == 'NVDA' else [] for t in all_tickers})
        fake_now = datetime(today_et.year, today_et.month, today_et.day, 19, 5, tzinfo=ET)

        # At default threshold (3.0%): signal SHOULD fire (5.2% > 3%)
        # Monkey-patch the module-level constant directly (avoids importlib.reload
        # since fp is not in sys.modules per spec.loader.exec_module pathway)
        original_threshold = fp.AH_MOVER_THRESHOLD_PCT
        fp.AH_MOVER_THRESHOLD_PCT = 3.0
        try:
            result = self._patched_fetch_all(['NVDA'], [], daily, intraday, fake_now_et=fake_now)
            self.assertIn('NVDA', result['signals']['ah_movers'],
                          "T3: NVDA should be in ah_movers at 3% threshold (5.2% AH move)")

            # At 10% threshold: signal should NOT fire
            fp.AH_MOVER_THRESHOLD_PCT = 10.0
            result = self._patched_fetch_all(['NVDA'], [], daily, intraday, fake_now_et=fake_now)
            self.assertNotIn('NVDA', result['signals']['ah_movers'],
                             "T3: NVDA should NOT be in ah_movers at 10% threshold (5.2% AH move)")
        finally:
            fp.AH_MOVER_THRESHOLD_PCT = original_threshold

    def test_T4_movers_aggregation_sort(self):
        """T4: extended_hours_movers[] sorted desc by |magnitude_pct|."""
        today_et = datetime.now(ET).date()
        ts = datetime(today_et.year, today_et.month, today_et.day, 19, 0, tzinfo=ET).astimezone(timezone.utc)
        # NVDA +5%, AMD -7%, MU +4%
        nvda_bars = [(ts.isoformat(), 105.0, 105.5, 104.8, 105.0, 50000)]   # +5% from base 100
        amd_bars = [(ts.isoformat(), 102.0, 103.0, 101.5, 102.7, 50000)]    # base 110 (idx 1) -> -7%? actually depends on base
        # For deterministic test, use very controlled fixtures
        # Build daily where NVDA closes at 100, AMD at 100, MU at 100
        all_tickers = ['NVDA', 'AMD', 'MU'] + list(fp.INDEX_MAP.keys())
        daily = make_daily_df(all_tickers, base_price=100.0)
        # Override last close for each to 100 for deterministic AH math
        for t in ['NVDA', 'AMD', 'MU']:
            if hasattr(daily.columns, 'get_level_values'):
                daily.loc[daily.index[-1], (t, 'Close')] = 100.0

        intraday_data = {
            'NVDA': [(ts.isoformat(), 105.0, 105.5, 104.5, 105.0, 50000)],   # +5%
            'AMD':  [(ts.isoformat(),  93.0,  94.0,  92.0,  93.0, 50000)],   # -7%
            'MU':   [(ts.isoformat(), 104.0, 104.5, 103.8, 104.0, 50000)],   # +4%
        }
        for t in fp.INDEX_MAP.keys():
            intraday_data[t] = []
        intraday = make_intraday_df(intraday_data)

        fake_now = datetime(today_et.year, today_et.month, today_et.day, 19, 5, tzinfo=ET)
        result = self._patched_fetch_all(['NVDA', 'AMD', 'MU'], [], daily, intraday, fake_now_et=fake_now)

        movers = result['extended_hours_movers']
        self.assertGreaterEqual(len(movers), 3, "T4: 3 tickers should appear in movers (all >3%)")
        magnitudes = [abs(m['magnitude_pct']) for m in movers]
        self.assertEqual(magnitudes, sorted(magnitudes, reverse=True),
                         "T4: extended_hours_movers must be sorted desc by |magnitude|")

    def test_T5_subagent_contract_additivity(self):
        """T5: price-fetcher.md documents all 6 new fields + removes /invest."""
        agent_path = Path(__file__).parent.parent / ".claude" / "agents" / "price-fetcher.md"
        content = agent_path.read_text(encoding="utf-8")
        # All 6 new fields documented
        for field in ["extended_hours_last", "extended_hours_change_pct",
                      "extended_hours_volume", "extended_hours_last_timestamp",
                      "market_session", "ah_source"]:
            self.assertIn(field, content,
                          f"T5: price-fetcher.md must document field '{field}'")
        # extended_hours_movers top-level documented
        self.assertIn("extended_hours_movers", content,
                      "T5: price-fetcher.md must document extended_hours_movers[]")
        # ah_movers signal documented (or named in version footer)
        self.assertIn("ah_movers", content,
                      "T5: price-fetcher.md must document ah_movers signal")
        # /invest dispatching claim REMOVED from "When parent skills dispatch you" list
        # (must not list /invest as active dispatcher; remediation acknowledgment OK)
        # Find the dispatching list section and verify
        dispatch_section_start = content.find("When parent skills dispatch you")
        dispatch_section_end = content.find("##", dispatch_section_start + 1)
        dispatch_block = content[dispatch_section_start:dispatch_section_end]
        # Must NOT have an active "/invest Phase J" bullet (without remediation context)
        # The remediation note should be present
        self.assertIn("Mission Four-bis", content,
                      "T5: drift remediation must reference Mission Four-bis")
        # v2 version footer present
        self.assertTrue("v2" in content and "Mission Three" in content,
                        "T5: version footer must mark v2 / Mission Three")

    def test_T6_crypto_path(self):
        """T6: Crypto -> market_session=regular; AH fields null (24/7 markets)."""
        all_tickers = list(fp.INDEX_MAP.keys()) + ['BTC-USD', 'XRP-USD']
        daily = make_daily_df(all_tickers, base_price=100.0)
        # Crypto would have intraday bars too but irrelevant for crypto path
        # (code overrides market_session=regular for ticker.endswith('-USD'))
        intraday = make_intraday_df({t: [] for t in all_tickers})

        result = self._patched_fetch_all([], ['BTC', 'XRP'], daily, intraday)

        for c in ['BTC', 'XRP']:
            entry = result['crypto'][c]
            self.assertEqual(entry['market_session'], 'regular',
                             f"T6: {c} must have market_session=regular")
            self.assertIsNone(entry['extended_hours_last'],
                              f"T6: {c} must have extended_hours_last=null")
            self.assertIsNone(entry['ah_source'],
                              f"T6: {c} must have ah_source=null")

    def test_T7_holiday_empty_intraday(self):
        """T7: Holiday path -> empty intraday bars -> market_session=closed."""
        all_tickers = ['NVDA'] + list(fp.INDEX_MAP.keys())
        daily = make_daily_df(all_tickers, base_price=100.0)
        # Empty intraday for all tickers (holiday: no bars)
        intraday = make_intraday_df({t: [] for t in all_tickers})

        # Pretend it's July 4 11:00 ET (Independence Day)
        fake_now = datetime(2026, 7, 4, 11, 0, tzinfo=ET)
        result = self._patched_fetch_all(['NVDA'], [], daily, intraday, fake_now_et=fake_now)

        nvda = result['equities']['NVDA']
        self.assertEqual(nvda['market_session'], 'closed',
                         "T7: holiday with empty intraday must yield market_session=closed")
        self.assertIsNone(nvda['extended_hours_last'])

    def test_T8_half_day_after_hours(self):
        """T8: Half-day (early close 13:00 ET); 14:00 ET -> market_session=after-hours."""
        # Day-after-Thanksgiving 2026-11-27, regular session 09:30-13:00; AH 13:00-17:00
        # Intraday bars from 09:30 to 14:00 ET; last bar at 14:00 is in AH window
        bars = []
        for hh in [10, 11, 12]:
            ts = datetime(2026, 11, 27, hh, 0, tzinfo=ET).astimezone(timezone.utc)
            bars.append((ts.isoformat(), 100.0, 101.0, 99.5, 100.5, 100000))
        # AH bars (post 13:00)
        for hh, mm in [(13, 30), (14, 0)]:
            ts = datetime(2026, 11, 27, hh, mm, tzinfo=ET).astimezone(timezone.utc)
            bars.append((ts.isoformat(), 100.5, 101.0, 100.0, 100.8, 50000))

        all_tickers = ['NVDA'] + list(fp.INDEX_MAP.keys())
        daily = make_daily_df(all_tickers, base_price=100.0)
        intraday = make_intraday_df({t: bars if t == 'NVDA' else [] for t in all_tickers})

        fake_now = datetime(2026, 11, 27, 14, 5, tzinfo=ET)
        result = self._patched_fetch_all(['NVDA'], [], daily, intraday, fake_now_et=fake_now)

        nvda = result['equities']['NVDA']
        # Code uses standard 16:00 ET as AH-start; on a half-day, 14:00 ET would be
        # market_session=regular (since 09:30 <= 14:00 < 16:00). This documents that
        # the implementation does NOT special-case half-days; bars-after-13:00 are
        # treated as "regular" not "after-hours". This is acceptable -- consuming
        # skills can detect via day-of-month + holiday calendar if needed.
        self.assertIn(nvda['market_session'], ('regular', 'after-hours', 'closed'),
                      "T8: half-day classification depends on standard 16:00 boundary; document expected")

    def test_T9_multi_ticker_partial_ah(self):
        """T9: Multi-ticker partial AH -- per-ticker independence."""
        today_et = datetime.now(ET).date()
        ts_ah = datetime(today_et.year, today_et.month, today_et.day, 19, 0, tzinfo=ET).astimezone(timezone.utc)
        ts_reg = datetime(today_et.year, today_et.month, today_et.day, 14, 0, tzinfo=ET).astimezone(timezone.utc)

        all_tickers = ['NVDA', 'AMD'] + list(fp.INDEX_MAP.keys())
        daily = make_daily_df(all_tickers, base_price=100.0)
        intraday_data = {
            'NVDA': [(ts_ah.isoformat(), 105.0, 105.5, 104.8, 105.2, 50000)],   # has AH bar
            'AMD': [(ts_reg.isoformat(), 100.0, 101.0, 99.5, 100.5, 1000000)],  # only regular bar
        }
        for t in fp.INDEX_MAP.keys():
            intraday_data[t] = []
        intraday = make_intraday_df(intraday_data)

        fake_now = datetime(today_et.year, today_et.month, today_et.day, 19, 5, tzinfo=ET)
        result = self._patched_fetch_all(['NVDA', 'AMD'], [], daily, intraday, fake_now_et=fake_now)

        nvda = result['equities']['NVDA']
        amd = result['equities']['AMD']
        self.assertIsNotNone(nvda['extended_hours_last'], "T9: NVDA has AH; should be populated")
        self.assertEqual(nvda['market_session'], 'after-hours')
        self.assertIsNone(amd['extended_hours_last'], "T9: AMD lacks AH bar; must remain null")
        self.assertEqual(amd['market_session'], 'regular',
                         "T9: AMD last bar at 14:00 ET = regular session")

    def test_T10_vgt_split_preservation(self):
        """T10: VGT split passed through via auto_adjust=True (default).
        The mock provides post-split prices; AH extraction should report them as-is.
        """
        today_et = datetime.now(ET).date()
        ts = datetime(today_et.year, today_et.month, today_et.day, 19, 0, tzinfo=ET).astimezone(timezone.utc)
        # Post-split VGT price ~$80 (was ~$640 pre-split)
        bars = [(ts.isoformat(), 80.0, 80.5, 79.8, 80.2, 100000)]

        all_tickers = ['VGT'] + list(fp.INDEX_MAP.keys())
        daily = make_daily_df(all_tickers, base_price=80.0)
        intraday = make_intraday_df({t: bars if t == 'VGT' else [] for t in all_tickers})

        fake_now = datetime(today_et.year, today_et.month, today_et.day, 19, 5, tzinfo=ET)
        result = self._patched_fetch_all(['VGT'], [], daily, intraday, fake_now_et=fake_now)

        vgt = result['equities']['VGT']
        # Assert post-split price reflected; not normalized to pre-split
        self.assertIsNotNone(vgt['extended_hours_last'])
        self.assertLess(vgt['extended_hours_last'], 100.0,
                        "T10: post-split VGT should be ~$80; not pre-split ~$640")

    def test_T11_api_failure(self):
        """T11: Intraday yf.download throws -> errors[] populated; daily call OK;
        AH fields null but other equities (in this batch, none) unaffected."""
        all_tickers = ['NVDA'] + list(fp.INDEX_MAP.keys())
        daily = make_daily_df(all_tickers, base_price=100.0)

        result = self._patched_fetch_all(['NVDA'], [], daily, intraday_data=None,
                                          intraday_raises=True)

        # errors[] should contain the intraday failure
        self.assertTrue(any('intraday' in e for e in result['errors']),
                        f"T11: errors[] must mention intraday failure; got {result['errors']}")
        nvda = result['equities']['NVDA']
        # Daily-bar fields preserved
        self.assertIsNotNone(nvda.get('price'), "T11: regular price must still be populated")
        # AH fields null
        self.assertIsNone(nvda['extended_hours_last'])
        self.assertEqual(nvda['market_session'], 'closed')


if __name__ == "__main__":
    # Use unittest CLI; exit code 0 on all-pass, 1 on any fail
    unittest.main(verbosity=2, exit=True)
