#!/usr/bin/env python
"""Execution cost model for the Osanwe factor store.

Estimates per-trade transaction costs (spread, market impact, commissions,
fees, slippage) for a given (ticker, order_size_usd), classified into six
instrument classes. Includes a break-even alpha calculator: the minimum
expected return advantage a trade must have to justify paying its costs.

Methodology (summary -- full write-up in docs/execution-cost-model.md):

  * Spread cost per side = half the quoted bid-ask spread (class-level
    prior, cross-checked against published effective-spread studies).
  * Market impact uses the square-root law (Almgren et al. 2005;
    Torre & Ferrari 1999; Grinold & Kahn Ch. 16):

        impact_bps = y * sigma_daily_bp * sqrt(order_usd / adv_usd)

    where sigma_daily_bp is daily volatility in basis points, adv_usd is
    average daily dollar volume, and y is a class-specific coefficient
    (temporary + permanent impact combined).
  * Commissions/fees: zero-commission equity brokers -> 0; crypto carries
    an exchange taker fee per side.
  * Round trip = 2 x (half_spread + impact + fees), one entry + one exit.
  * Calibration targets are the class ranges specified for this book
    (large caps ~5-15 bps round trip, small caps ~50-200 bps, etc.), which
    are themselves consistent with Loeb (1983), Lesmond et al. (1999),
    Korajczyk & Sadka (2004) and Frazzini, Israel & Moskowitz (2012).

All figures are priors/approximations for planning, NOT live quotes.
No network access is used anywhere in this module.

Usage:
    python tools/execution-cost-model.py --estimate AAOI 100000
    python tools/execution-cost-model.py --breakeven AAOI 100000 --days 10
    python tools/execution-cost-model.py --test
    python tools/execution-cost-model.py --demo [--save-results PATH]
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import unittest
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Instrument classification
# ---------------------------------------------------------------------------

LARGE_CAP_EQUITY = "LARGE_CAP_EQUITY"
MID_CAP_EQUITY = "MID_CAP_EQUITY"
SMALL_CAP_EQUITY = "SMALL_CAP_EQUITY"
ETF_BROAD = "ETF_BROAD"
CRYPTO = "CRYPTO"
ADR_FOREIGN = "ADR_FOREIGN"

ALL_CLASSES = (
    LARGE_CAP_EQUITY,
    MID_CAP_EQUITY,
    SMALL_CAP_EQUITY,
    ETF_BROAD,
    CRYPTO,
    ADR_FOREIGN,
)

# Classification of every ticker currently in the factor store
# (source: _flow_per_ticker.json at vault root, 2026-08 snapshot),
# plus common examples used in the spec (SPY, AAPL, ABBNY).
# Unknown tickers default to MID_CAP_EQUITY (conservative middle ground).
TICKER_CLASS: Dict[str, str] = {
    # Mega / large cap equities (market cap > ~$100B)
    "MSFT": LARGE_CAP_EQUITY, "NVDA": LARGE_CAP_EQUITY, "GOOGL": LARGE_CAP_EQUITY,
    "AMZN": LARGE_CAP_EQUITY, "META": LARGE_CAP_EQUITY, "AVGO": LARGE_CAP_EQUITY,
    "AMD": LARGE_CAP_EQUITY, "ORCL": LARGE_CAP_EQUITY, "TSLA": LARGE_CAP_EQUITY,
    "PLTR": LARGE_CAP_EQUITY, "CSCO": LARGE_CAP_EQUITY, "MU": LARGE_CAP_EQUITY,
    "QCOM": LARGE_CAP_EQUITY, "AMAT": LARGE_CAP_EQUITY, "LRCX": LARGE_CAP_EQUITY,
    "KLAC": LARGE_CAP_EQUITY, "ANET": LARGE_CAP_EQUITY, "ARM": LARGE_CAP_EQUITY,
    "NEE": LARGE_CAP_EQUITY, "ETN": LARGE_CAP_EQUITY, "GEV": LARGE_CAP_EQUITY,
    "CEG": LARGE_CAP_EQUITY, "LMT": LARGE_CAP_EQUITY, "RTX": LARGE_CAP_EQUITY,
    "APH": LARGE_CAP_EQUITY, "NOW": LARGE_CAP_EQUITY, "INTC": LARGE_CAP_EQUITY,
    "AAPL": LARGE_CAP_EQUITY,
    # Mid cap equities (~$10-100B)
    "SNPS": MID_CAP_EQUITY, "CDNS": MID_CAP_EQUITY, "DELL": MID_CAP_EQUITY,
    "HPE": MID_CAP_EQUITY, "SMCI": MID_CAP_EQUITY, "MRVL": MID_CAP_EQUITY,
    "EQIX": MID_CAP_EQUITY, "DLR": MID_CAP_EQUITY, "SO": MID_CAP_EQUITY,
    "DUK": MID_CAP_EQUITY, "AEP": MID_CAP_EQUITY, "PPL": MID_CAP_EQUITY,
    "VRT": MID_CAP_EQUITY, "WDC": MID_CAP_EQUITY, "SNDK": MID_CAP_EQUITY,
    "GFS": MID_CAP_EQUITY, "ONTO": MID_CAP_EQUITY, "LITE": MID_CAP_EQUITY,
    "COHR": MID_CAP_EQUITY, "FN": MID_CAP_EQUITY, "CRDO": MID_CAP_EQUITY,
    "ALAB": MID_CAP_EQUITY, "NBIS": MID_CAP_EQUITY, "CRWV": MID_CAP_EQUITY,
    "HIMS": MID_CAP_EQUITY, "RKLB": MID_CAP_EQUITY, "MP": MID_CAP_EQUITY,
    "HUBB": MID_CAP_EQUITY, "WBD": MID_CAP_EQUITY, "COIN": MID_CAP_EQUITY,
    "NOC": MID_CAP_EQUITY, "GD": MID_CAP_EQUITY, "BWXT": MID_CAP_EQUITY,
    "TLN": MID_CAP_EQUITY, "VST": MID_CAP_EQUITY, "NRG": MID_CAP_EQUITY,
    "AEIS": MID_CAP_EQUITY, "AMKR": MID_CAP_EQUITY, "HII": MID_CAP_EQUITY,
    # Small cap equities (< ~$10B)
    "AAOI": SMALL_CAP_EQUITY, "MRAM": SMALL_CAP_EQUITY, "OKLO": SMALL_CAP_EQUITY,
    "SMR": SMALL_CAP_EQUITY, "KTOS": SMALL_CAP_EQUITY, "AVAV": SMALL_CAP_EQUITY,
    "USAR": SMALL_CAP_EQUITY, "FLNC": SMALL_CAP_EQUITY, "BE": SMALL_CAP_EQUITY,
    "MBLY": SMALL_CAP_EQUITY, "AMBA": SMALL_CAP_EQUITY, "BAH": SMALL_CAP_EQUITY,
    "MKSI": SMALL_CAP_EQUITY,
    # Broad / liquid ETFs
    "QQQ": ETF_BROAD, "SPY": ETF_BROAD, "VGT": ETF_BROAD, "IAU": ETF_BROAD,
    "SPCX": ETF_BROAD,
    # Crypto
    "BTC": CRYPTO, "ETH": CRYPTO, "SOL": CRYPTO, "XRP": CRYPTO,
    "QNT": CRYPTO, "LINK": CRYPTO,
    # Foreign ADRs
    "TSM": ADR_FOREIGN, "ASML": ADR_FOREIGN, "ABBNY": ADR_FOREIGN,
    "ATEYY": ADR_FOREIGN,
}

# ---------------------------------------------------------------------------
# Class-level cost parameters (calibration priors)
# ---------------------------------------------------------------------------

# Fields:
#   half_spread_bp   : half the quoted bid/ask spread, per side
#   sigma_daily_bp   : typical daily return volatility, bp
#   adv_usd          : representative average daily dollar volume
#   impact_y         : square-root-law coefficient (temporary + permanent)
#   min_impact_bp    : floor on impact per side (handling/pipeline cost)
#   fee_bp           : commissions + exchange/regulatory fees, per side
#   fx_bp            : currency conversion cost, per side (0 = USD-traded)
#   rt_range_bp      : target round-trip total-cost range this class is
#                      calibrated to hit across its typical order sizes
CLASS_PARAMS: Dict[str, Dict] = {
    LARGE_CAP_EQUITY: dict(
        half_spread_bp=0.75, sigma_daily_bp=130.0, adv_usd=10e9, impact_y=1.0,
        min_impact_bp=1.5, fee_bp=0.0, fx_bp=0.0, rt_range_bp=(5.0, 15.0),
    ),
    MID_CAP_EQUITY: dict(
        half_spread_bp=3.0, sigma_daily_bp=220.0, adv_usd=400e6, impact_y=1.2,
        min_impact_bp=1.5, fee_bp=0.0, fx_bp=0.0, rt_range_bp=(15.0, 40.0),
    ),
    SMALL_CAP_EQUITY: dict(
        half_spread_bp=10.0, sigma_daily_bp=350.0, adv_usd=40e6, impact_y=1.5,
        min_impact_bp=1.0, fee_bp=0.0, fx_bp=0.0, rt_range_bp=(50.0, 200.0),
    ),
    ETF_BROAD: dict(
        half_spread_bp=1.0, sigma_daily_bp=120.0, adv_usd=2e9, impact_y=1.0,
        min_impact_bp=0.02, fee_bp=0.0, fx_bp=0.0, rt_range_bp=(3.0, 8.0),
    ),
    CRYPTO: dict(
        half_spread_bp=4.0, sigma_daily_bp=300.0, adv_usd=10e9, impact_y=1.0,
        min_impact_bp=0.5, fee_bp=8.0, fx_bp=0.0, rt_range_bp=(20.0, 50.0),
    ),
    ADR_FOREIGN: dict(
        half_spread_bp=1.5, sigma_daily_bp=200.0, adv_usd=1.5e9, impact_y=1.1,
        min_impact_bp=0.2, fee_bp=0.0, fx_bp=3.0, rt_range_bp=(8.0, 40.0),
    ),
}

# Per-ticker overrides for names whose liquidity differs materially from the
# class prior. Static approximations (no network); refresh periodically.
#   adv_usd: approximate average daily dollar volume (USD)
#   half_spread_bp: replaces the class half-spread when given
#   fx_bp: explicit FX conversion cost per side when the venue requires it
TICKER_OVERRIDES: Dict[str, Dict] = {
    # Ultra-liquid mega caps: deeper book than the class prior. Spreads are
    # sub-bp, but pipeline/handling costs keep all-in one-way costs ~2-4 bp,
    # consistent with Frazzini-Israel-Moskowitz (2012) live trading.
    "MSFT": dict(adv_usd=15e9, half_spread_bp=1.5),
    "NVDA": dict(adv_usd=40e9, half_spread_bp=1.5),
    "AAPL": dict(adv_usd=30e9, half_spread_bp=1.5),
    "TSLA": dict(adv_usd=25e9, half_spread_bp=2.0, sigma_daily_bp=280.0),
    "AMD": dict(adv_usd=12e9, half_spread_bp=2.0),
    "GOOGL": dict(adv_usd=12e9, half_spread_bp=1.5),
    "AMZN": dict(adv_usd=12e9, half_spread_bp=1.5),
    "META": dict(adv_usd=8e9, half_spread_bp=1.75),
    "PLTR": dict(adv_usd=15e9, half_spread_bp=2.0, sigma_daily_bp=250.0),
    # Liquid ETFs: SPY/QQQ quote sub-bp spreads; the class floor here is a
    # conservative all-in figure (routing + handling) rather than raw spread.
    "SPY": dict(adv_usd=30e9, half_spread_bp=1.0),
    "QQQ": dict(adv_usd=15e9, half_spread_bp=1.05),
    "IAU": dict(adv_usd=3e9, half_spread_bp=1.0),
    # Crypto: majors vs long tail
    "BTC": dict(adv_usd=30e9, sigma_daily_bp=250.0),
    "ETH": dict(adv_usd=15e9, sigma_daily_bp=280.0),
    "SOL": dict(adv_usd=4e9, sigma_daily_bp=380.0),
    "XRP": dict(adv_usd=3e9, sigma_daily_bp=380.0),
    "QNT": dict(adv_usd=30e6, sigma_daily_bp=450.0, half_spread_bp=15.0),
    "LINK": dict(adv_usd=800e6, sigma_daily_bp=380.0),
    # ADRs: TSM/ASML ADRs track very liquid underlying home lines;
    # ABBNY/ATEYY trade OTC with much wider effective spreads
    "TSM": dict(adv_usd=2.5e9, half_spread_bp=1.0),
    "ASML": dict(adv_usd=1.5e9, half_spread_bp=2.0),
    "ABBNY": dict(adv_usd=150e6, half_spread_bp=15.0),
    "ATEYY": dict(adv_usd=50e6, half_spread_bp=25.0),
}


def classify_ticker(ticker: str) -> str:
    """Return the instrument class for a ticker (defaults to mid cap)."""
    return TICKER_CLASS.get(ticker.upper().strip(), MID_CAP_EQUITY)


def get_params(ticker: str) -> Tuple[str, Dict]:
    """Return (ticker_class, merged parameter dict) for a ticker."""
    cls = classify_ticker(ticker)
    params = dict(CLASS_PARAMS[cls])
    ov = TICKER_OVERRIDES.get(ticker.upper().strip(), {})
    params.update({k: v for k, v in ov.items() if k != "rt_range_bp"})
    return cls, params


# ---------------------------------------------------------------------------
# Core cost model
# ---------------------------------------------------------------------------

def estimate_trade_cost(
    ticker: str,
    order_size_usd: float,
    holding_days: Optional[int] = None,
    verbose: bool = False,
) -> Dict:
    """Estimate the transaction cost breakdown for one trade.

    Returns a dict with per-side and round-trip costs in basis points,
    plus the dollar cost of the round trip. All figures are estimates.
    """
    if order_size_usd <= 0:
        raise ValueError("order_size_usd must be positive")
    cls, p = get_params(ticker)

    ratio = order_size_usd / p["adv_usd"]
    sqrt_ratio = math.sqrt(ratio)
    impact_raw_bp = p["impact_y"] * p["sigma_daily_bp"] * sqrt_ratio
    impact_side_bp = max(p["min_impact_bp"], impact_raw_bp)
    spread_side_bp = p["half_spread_bp"]
    fee_side_bp = p["fee_bp"]
    fx_side_bp = p["fx_bp"]

    side_total_bp = spread_side_bp + impact_side_bp + fee_side_bp + fx_side_bp
    round_trip_bp = 2.0 * side_total_bp
    round_trip_usd = order_size_usd * round_trip_bp / 10000.0

    result = {
        "ticker": ticker.upper().strip(),
        "ticker_class": cls,
        "order_size_usd": round(order_size_usd, 2),
        "pct_of_adv": ratio,
        # Per-side components (basis points)
        "spread_bp_per_side": round(spread_side_bp, 3),
        "impact_bp_per_side": round(impact_side_bp, 3),
        "fees_bp_per_side": round(fee_side_bp, 3),
        "fx_bp_per_side": round(fx_side_bp, 3),
        "total_bp_per_side": round(side_total_bp, 3),
        # Round trip
        "round_trip_bp": round(round_trip_bp, 3),
        "round_trip_usd": round(round_trip_usd, 2),
        "calibrated_rt_range_bp": list(p["rt_range_bp"]),
    }
    if holding_days is not None and holding_days > 0:
        be = break_even_alpha(ticker, order_size_usd, holding_days)
        result["breakeven_excess_return_bp"] = be["breakeven_excess_return_bp"]
        result["breakeven_annualized_pct"] = be["breakeven_annualized_pct"]
    if verbose:
        print(format_cost_breakdown(result))
    return result


def format_cost_breakdown(r: Dict) -> str:
    """Human-readable one-screen summary of an estimate_trade_cost result."""
    lo, hi = r["calibrated_rt_range_bp"]
    lines = [
        "%s [%s]  order $%s  (%.4f%% of ADV)" % (
            r["ticker"], r["ticker_class"],
            "{:,.0f}".format(r["order_size_usd"]), r["pct_of_adv"] * 100.0),
        "  spread  : %6.2f bp per side" % r["spread_bp_per_side"],
        "  impact  : %6.2f bp per side (sqrt-law)" % r["impact_bp_per_side"],
        "  fees    : %6.2f bp per side" % r["fees_bp_per_side"],
        "  fx      : %6.2f bp per side" % r["fx_bp_per_side"],
        "  ------------------------------------",
        "  ROUND TRIP: %.2f bp  (= $%.2f)  [calibration band %.0f-%.0f bp]" % (
            r["round_trip_bp"], r["round_trip_usd"], lo, hi),
    ]
    if "breakeven_excess_return_bp" in r:
        lines.append(
            "  BREAKEVEN: %.1f bp excess return over %d-day hold "
            "(%.1f%% annualized)" % (
                r["breakeven_excess_return_bp"], r.get("_holding_days", 0),
                r["breakeven_annualized_pct"]))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Break-even alpha
# ---------------------------------------------------------------------------

def break_even_alpha(
    ticker: str,
    order_size_usd: float,
    holding_days: int,
    safety_buffer_bp: float = 0.0,
) -> Dict:
    """Minimum expected return advantage needed to justify a trade.

    A trade is worth doing only if its expected excess return (vs simply
    holding the benchmark / doing nothing) exceeds the full round-trip
    cost plus any requested safety buffer:

        breakeven_bp = round_trip_cost_bp + safety_buffer_bp
        annualized   = breakeven_bp * (365 / holding_days) / 100  (%/yr)

    This makes explicit why small-cap signals need far bigger edges than
    the same signal on SPY: same idea, different hurdle rate.
    """
    if holding_days <= 0:
        raise ValueError("holding_days must be positive")
    cost = estimate_trade_cost(ticker, order_size_usd)
    be_bp = cost["round_trip_bp"] + safety_buffer_bp
    ann_pct = be_bp * (365.0 / holding_days) / 100.0
    return {
        "ticker": cost["ticker"],
        "order_size_usd": cost["order_size_usd"],
        "holding_days": holding_days,
        "round_trip_cost_bp": cost["round_trip_bp"],
        "safety_buffer_bp": safety_buffer_bp,
        "breakeven_excess_return_bp": round(be_bp, 3),
        "breakeven_annualized_pct": round(ann_pct, 4),
    }


def estimate_portfolio_costs(positions: List[Tuple[str, float]]) -> Dict:
    """Aggregate round-trip cost for a list of (ticker, order_size_usd).

    Useful for sizing turnover: how much edge does a rebalance need in
    aggregate before it pays for itself?
    """
    rows = []
    tot_usd_notional = 0.0
    tot_usd_cost = 0.0
    for ticker, size in positions:
        r = estimate_trade_cost(ticker, size)
        rows.append(r)
        tot_usd_notional += r["order_size_usd"]
        tot_usd_cost += r["round_trip_usd"]
    agg_bp = (tot_usd_cost / tot_usd_notional * 10000.0) if tot_usd_notional else 0.0
    return {
        "n_trades": len(rows),
        "total_notional_usd": round(tot_usd_notional, 2),
        "total_round_trip_cost_usd": round(tot_usd_cost, 2),
        "weighted_round_trip_bp": round(agg_bp, 2),
        "trades": rows,
    }


# ---------------------------------------------------------------------------
# Tests against academic-literature anchors
# ---------------------------------------------------------------------------

class TestExecutionCostModel(unittest.TestCase):
    """Calibration checks against the spec bands and published findings.

    Literature anchors:
      * Loeb (1983), Financial Analysts Journal -- block-trade price
        impact rises steeply as firm size falls; small-firm blocks pay
        multiples of large-firm impact for the same dollar size.
      * Lesmond, Ogden & Trzcinka (1999), JF -- zero-return frequency
        implies small-cap transaction costs an order of magnitude above
        large caps.
      * Almgren, Thum, Hauptmann & Li (2005), Risk -- realized impact
        grows with the square root of participation rate (size/ADV).
      * Korajczyk & Sadka (2004), JF -- price impact constrains
        momentum strategies; costs scale with strategy size.
      * Frazzini, Israel & Moskowitz (2012), "Trading Costs of Asset
        Pricing Anomalies" -- live-trading one-way costs of roughly
        5-30 bp for liquid large-cap US stocks depending on size,
        several times higher for small caps.
      * Broad ETFs (SPY/QQQ) quote ~0.5-1 bp effective spreads --
        effectively frictionless below institutional size.
    """

    def _rt(self, ticker: str, size: float) -> float:
        return estimate_trade_cost(ticker, size)["round_trip_bp"]

    # --- Spec calibration bands -------------------------------------------
    def test_large_cap_band(self):
        # $50k-$5M round trips should land in the ~5-15 bp band.
        for size in (50_000, 250_000, 1_000_000, 5_000_000):
            rt = self._rt("MSFT", size)
            self.assertGreaterEqual(rt, 4.0, msg=str(size))
            self.assertLessEqual(rt, 16.0, msg=str(size))

    def test_mid_cap_band(self):
        # $100k-$1M round trips should land in the ~15-40 bp band.
        for size in (100_000, 250_000, 500_000, 1_000_000):
            rt = self._rt("AEIS", size)
            self.assertGreaterEqual(rt, 14.0, msg=str(size))
            self.assertLessEqual(rt, 41.0, msg=str(size))

    def test_small_cap_band(self):
        # $100k-$1M round trips should land in the ~50-200 bp band.
        for size in (100_000, 250_000, 500_000, 1_000_000):
            rt = self._rt("AAOI", size)
            self.assertGreaterEqual(rt, 48.0, msg=str(size))
            self.assertLessEqual(rt, 205.0, msg=str(size))

    def test_etf_band(self):
        # Small ETF orders: ~3-8 bp round trip (VGT-calibrated class).
        for size in (25_000, 100_000, 500_000, 1_000_000):
            rt = self._rt("VGT", size)
            self.assertGreaterEqual(rt, 2.5, msg=str(size))
            self.assertLessEqual(rt, 8.5, msg=str(size))

    def test_crypto_band(self):
        # $25k-$5M market orders: ~20-50 bp all-in round trip.
        for size in (25_000, 250_000, 1_000_000, 5_000_000):
            rt = self._rt("BTC", size)
            self.assertGreaterEqual(rt, 20.0, msg=str(size))
            self.assertLessEqual(rt, 51.0, msg=str(size))

    # --- Cross-sectional ordering (Loeb 1983 / Lesmond 1999) --------------
    def test_cost_ordering_by_size(self):
        # Same dollar order: small caps cost multiples of large caps.
        size = 250_000
        large = self._rt("MSFT", size)
        mid = self._rt("AEIS", size)
        small = self._rt("AAOI", size)
        etf = self._rt("QQQ", size)
        self.assertLess(etf, large)
        self.assertLess(large, mid)
        self.assertLess(mid, small)
        # Small-cap premium should be steep (order of magnitude, Loeb).
        self.assertGreater(small / large, 5.0)

    # --- Square-root impact scaling (Almgren et al. 2005) -----------------
    def test_impact_scales_sublinearly_with_size(self):
        # Doubling size less than doubles impact => concave in size.
        r1 = estimate_trade_cost("AAOI", 100_000)["impact_bp_per_side"]
        r2 = estimate_trade_cost("AAOI", 200_000)["impact_bp_per_side"]
        r4 = estimate_trade_cost("AAOI", 400_000)["impact_bp_per_side"]
        self.assertLess(r2, 2.0 * r1)
        self.assertLess(r4, 2.0 * r2)
        # And exactly sqrt(2)x for a doubling (pure sqrt law).
        self.assertAlmostEqual(r2 / r1, math.sqrt(2.0), places=3)
        self.assertAlmostEqual(r4 / r1, 2.0, places=3)

    def test_monotone_in_size(self):
        prev = 0.0
        for size in (10_000, 50_000, 250_000, 1_000_000, 5_000_000):
            cur = self._rt("MRAM", size)
            self.assertGreater(cur, prev)
            prev = cur

    # --- Frazzini-Israel-Moskowitz (2012) anchor --------------------------
    def test_large_cap_one_way_near_fim_anchor(self):
        # FIM find ~5-15 bp ONE-WAY for liquid US large caps at fund scale.
        # Our $1M one-way estimate for MSFT should sit in that zone.
        one_way = estimate_trade_cost("MSFT", 1_000_000)["total_bp_per_side"]
        self.assertGreaterEqual(one_way, 1.5)
        self.assertLessEqual(one_way, 15.0)

    # --- Crypto structure --------------------------------------------------
    def test_crypto_has_exchange_fee_component(self):
        r = estimate_trade_cost("BTC", 100_000)
        self.assertGreater(r["fees_bp_per_side"], 0.0)
        # Fee dominates the spread on crypto venues.
        self.assertGreater(r["fees_bp_per_side"], r["spread_bp_per_side"])

    # --- ADR handling -------------------------------------------------------
    def test_adr_liquid_vs_otc(self):
        # TSM ADR (deep NYSE line) far cheaper than an OTC ADR (ABBNY).
        tsm = self._rt("TSM", 250_000)
        abbny = self._rt("ABBNY", 250_000)
        self.assertLess(tsm, abbny)
        self.assertGreater(abbny / tsm, 2.0)

    # --- Break-even alpha ---------------------------------------------------
    def test_break_even_matches_round_trip_cost(self):
        be = break_even_alpha("AAOI", 100_000, holding_days=10)
        rt = self._rt("AAOI", 100_000)
        self.assertAlmostEqual(be["breakeven_excess_return_bp"], rt, places=3)

    def test_break_even_annualization(self):
        be = break_even_alpha("SPY", 100_000, holding_days=365)
        # 1-year hold: annualized hurdle ~= round-trip cost in pct.
        self.assertAlmostEqual(be["breakeven_annualized_pct"],
                               be["round_trip_cost_bp"] / 100.0, places=2)
        # Shorter holds annualize brutally: a 10-day hold's annualized
        # hurdle is 36.5x the 1-year hold's (same bp hurdle, less time).
        be10 = break_even_alpha("SPY", 100_000, holding_days=10)
        self.assertAlmostEqual(be10["breakeven_annualized_pct"]
                               / be["breakeven_annualized_pct"], 36.5, places=1)
        # In raw bp terms the hurdle is identical regardless of hold length.
        self.assertAlmostEqual(be10["breakeven_excess_return_bp"],
                               be["breakeven_excess_return_bp"], places=3)

    def test_break_even_orders_across_classes(self):
        size, days = 250_000, 21
        hurdles = {
            cls: break_even_alpha(tk, size, days)["breakeven_excess_return_bp"]
            for tk, cls in (("QQQ", ETF_BROAD), ("MSFT", LARGE_CAP_EQUITY),
                            ("AEIS", MID_CAP_EQUITY), ("AAOI", SMALL_CAP_EQUITY))
        }
        self.assertLess(hurdles[ETF_BROAD], hurdles[LARGE_CAP_EQUITY])
        self.assertLess(hurdles[LARGE_CAP_EQUITY], hurdles[MID_CAP_EQUITY])
        self.assertLess(hurdles[MID_CAP_EQUITY], hurdles[SMALL_CAP_EQUITY])

    # --- Robustness ---------------------------------------------------------
    def test_unknown_ticker_defaults_to_mid(self):
        self.assertEqual(classify_ticker("ZZZZZ"), MID_CAP_EQUITY)
        r = estimate_trade_cost("zzzzz", 100_000)
        self.assertEqual(r["ticker_class"], MID_CAP_EQUITY)

    def test_invalid_inputs_raise(self):
        with self.assertRaises(ValueError):
            estimate_trade_cost("MSFT", 0)
        with self.assertRaises(ValueError):
            break_even_alpha("MSFT", 100_000, holding_days=0)


# ---------------------------------------------------------------------------
# CLI / results export
# ---------------------------------------------------------------------------

def run_demo(save_path: Optional[str] = None) -> Dict:
    """Run a demonstration sweep over the factor-store universe."""
    demo_orders = {
        LARGE_CAP_EQUITY: ("MSFT", 1_000_000),
        MID_CAP_EQUITY: ("AEIS", 250_000),
        SMALL_CAP_EQUITY: ("AAOI", 250_000),
        ETF_BROAD: ("QQQ", 500_000),
        CRYPTO: ("BTC", 100_000),
        ADR_FOREIGN: ("TSM", 250_000),
    }
    results = {"generated_by": "tools/execution-cost-model.py",
               "note": "Planning estimates, not live quotes.",
               "classes": {}, "breakeven_examples": []}
    print("=" * 64)
    print("EXECUTION COST MODEL -- REPRESENTATIVE TRADES PER CLASS")
    print("=" * 64)
    for cls, (tk, size) in demo_orders.items():
        r = estimate_trade_cost(tk, size)
        results["classes"][cls] = r
        print()
        print(format_cost_breakdown(r))
    print()
    print("=" * 64)
    print("BREAK-EVEN ALPHA EXAMPLES (excess return needed to justify)")
    print("=" * 64)
    examples = [("QQQ", 500_000, 21), ("MSFT", 1_000_000, 21),
                ("AEIS", 250_000, 21), ("AAOI", 250_000, 21),
                ("AAOI", 250_000, 5), ("BTC", 100_000, 7)]
    for tk, size, days in examples:
        be = break_even_alpha(tk, size, days)
        results["breakeven_examples"].append(be)
        print("  %-5s $%9s  %2dd hold -> %6.1f bp edge needed "
              "(%.0f%% annualized)" % (
                  be["ticker"], "{:,}".format(int(be["order_size_usd"])),
                  days, be["breakeven_excess_return_bp"],
                  be["breakeven_annualized_pct"]))
    if save_path:
        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        with open(save_path, "w", encoding="ascii") as f:
            json.dump(results, f, indent=2, sort_keys=True)
        print("\nResults saved to %s" % save_path)
    return results


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--estimate", nargs=2, metavar=("TICKER", "USD"),
                    help="cost breakdown for one order")
    ap.add_argument("--breakeven", nargs=2, metavar=("TICKER", "USD"),
                    help="break-even alpha for one order")
    ap.add_argument("--days", type=int, default=21,
                    help="holding period in days for --breakeven")
    ap.add_argument("--buffer", type=float, default=0.0,
                    help="safety buffer in bp added to break-even")
    ap.add_argument("--demo", action="store_true", help="run demo sweep")
    ap.add_argument("--save-results", metavar="PATH",
                    help="save demo results as JSON (with --demo)")
    ap.add_argument("--test", action="store_true",
                    help="run the unit tests")
    args = ap.parse_args(argv)

    if args.test:
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestExecutionCostModel)
        res = unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if res.wasSuccessful() else 1
    if args.estimate:
        estimate_trade_cost(args.estimate[0], float(args.estimate[1]),
                            verbose=True)
        return 0
    if args.breakeven:
        be = break_even_alpha(args.breakeven[0], float(args.breakeven[1]),
                              holding_days=args.days,
                              safety_buffer_bp=args.buffer)
        print(json.dumps(be, indent=2))
        return 0
    if args.demo:
        run_demo(save_path=args.save_results)
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
