#!/usr/bin/env python3
"""Batch market data fetcher for /brief skill.

Fetches live prices, technical indicators (RSI, MAs), metadata (beta, short
ratio, earnings date, 52-week range), and market status via yfinance.
Outputs structured JSON to stdout.

Usage:
    python fetch-prices.py --equities "NVDA,TSLA,VOO" --crypto "XRP,BTC"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import warnings
from datetime import datetime, date, time
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*auto_adjust.*")

# -- Configuration env vars ------------------------------------------------
#   AH_MOVER_THRESHOLD_PCT (default 3.0): emit ah_mover signal when an AH change_pct
#                                          magnitude meets/exceeds this percent
#   FETCH_PRICES_NO_EXTENDED (default unset): if "1", equivalent to --no-extended
#   ALPACA_API_KEY / ALPACA_API_SECRET (Session 4): not used; reserved for future
#                                                    second-source fallback path
ET = ZoneInfo("America/New_York")
AH_MOVER_THRESHOLD_PCT = float(os.environ.get("AH_MOVER_THRESHOLD_PCT", "3.0"))

# -- Index / Macro Tickers -------------------------------------------------
INDEX_MAP = {
    "^GSPC": "SPX",
    "^IXIC": "NASDAQ",
    "^DJI": "DOW",
    "^VIX": "VIX",
    "^VIX3M": "VIX3M",
    "^TNX": "10Y",
    "DX-Y.NYB": "DXY",
    "GC=F": "GOLD",
    "CL=F": "OIL",
}

# -- Helpers ---------------------------------------------------------------

def compute_rsi(series: pd.Series, period: int = 14) -> float | None:
    """Wilder-smoothed RSI."""
    if series is None or len(series) < period + 1:
        return None
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    val = rsi.iloc[-1]
    return round(float(val), 1) if pd.notna(val) else None


def compute_ma(series: pd.Series, window: int) -> float | None:
    """Simple moving average (last value)."""
    if series is None or len(series) < window:
        return None
    val = series.rolling(window).mean().iloc[-1]
    return round(float(val), 2) if pd.notna(val) else None


def safe_round(val, digits=2):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    return round(float(val), digits)


def detect_market_status(
    last_data_date: date | None,
    intraday_market_sessions: dict | None = None,
) -> str:
    """Determine market status. Preferred: reduce per-ticker market_session
    (from intraday-bar verification) to a global market_status enum.
    Fallback: ET clock comparison against last_data_date."""
    # Preferred path: per-ticker intraday session reduction
    if intraday_market_sessions:
        sessions = set(s for s in intraday_market_sessions.values() if s)
        if "regular" in sessions:
            return "open"
        if "after-hours" in sessions:
            return "post_market"
        if "pre-market" in sessions:
            return "pre_market"
        return "closed"

    # Fallback: ET-aware clock comparison
    if last_data_date is None:
        return "unknown"
    et_now = datetime.now(ET)
    today = et_now.date()
    weekday = today.weekday()  # 0=Mon, 6=Sun

    if last_data_date == today:
        et_time = et_now.time()
        if et_time < time(9, 30):
            return "pre_market"
        elif et_time >= time(16, 0):
            return "post_market"
        return "open"

    if weekday in (5, 6):
        return "closed"
    if (today - last_data_date).days <= 3:
        return "closed"  # likely holiday or just after weekend
    return "closed"


# -- Main Fetch ------------------------------------------------------------

def fetch_all(
    equity_tickers: list[str],
    crypto_tickers: list[str],
    no_extended: bool = False,
) -> dict:
    result = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "market_status": "unknown",
        "last_trading_day": None,
        "indices": {},
        "equities": {},
        "crypto": {},
        "extended_hours_movers": [],
        "signals": {
            "oversold": [],
            "overbought": [],
            "below_ma50": [],
            "below_ma200": [],
            "earnings_within_10d": [],
            "high_short_ratio": [],
            "ah_movers": [],
        },
        "errors": [],
    }

    # Build combined ticker list for batch download
    crypto_yf = [f"{t}-USD" for t in crypto_tickers]
    index_tickers = list(INDEX_MAP.keys())
    all_tickers = equity_tickers + index_tickers + crypto_yf

    if not all_tickers:
        return result

    # -- Batch download (single HTTP call) ---------------------------------
    try:
        raw = yf.download(
            all_tickers,
            period="1y",
            group_by="ticker",
            progress=False,
            threads=True,
        )
    except Exception as e:
        result["errors"].append(f"yf.download failed: {e}")
        return result

    # -- Intraday + extended-hours bars (second call; period=2d/interval=1m/prepost=True) -
    # Daily-bar call above is preserved for RSI/MA stability; this call adds
    # 1-minute bars covering pre-market (04:00-09:30 ET) + after-hours
    # (16:00-20:00 ET). Failure here is non-fatal -- result["errors"] populates
    # and per-ticker AH fields fall back to None.
    intraday_raw = None
    if not no_extended:
        try:
            intraday_raw = yf.download(
                all_tickers,
                period="2d",
                interval="1m",
                prepost=True,
                group_by="ticker",
                progress=False,
                threads=True,
            )
        except Exception as e:
            result["errors"].append(f"yf.download intraday failed: {e}")
            intraday_raw = None

    multi = len(all_tickers) > 1
    last_date = None
    intraday_market_sessions: dict[str, str] = {}

    # -- Process each ticker -----------------------------------------------
    for ticker in all_tickers:
        try:
            if multi:
                if ticker not in raw.columns.get_level_values(0):
                    result["errors"].append(f"{ticker}: not in download")
                    continue
                df = raw[ticker].dropna(how="all")
            else:
                df = raw.dropna(how="all")

            if df.empty or "Close" not in df.columns:
                result["errors"].append(f"{ticker}: no data")
                continue

            closes = df["Close"].dropna()
            if closes.empty:
                result["errors"].append(f"{ticker}: no closes")
                continue

            price = safe_round(closes.iloc[-1])
            prev_close = safe_round(closes.iloc[-2]) if len(closes) > 1 else price
            change_pct = safe_round(
                (closes.iloc[-1] - closes.iloc[-2]) / closes.iloc[-2] * 100
            ) if len(closes) > 1 and closes.iloc[-2] != 0 else 0.0

            data_date = closes.index[-1]
            if hasattr(data_date, "date"):
                data_date = data_date.date()
            date_str = str(data_date)

            if last_date is None or data_date > last_date:
                last_date = data_date

            entry = {
                "price": price,
                "prev_close": prev_close,
                "change_pct": change_pct,
                "date": date_str,
            }

            # -- Extended-hours extraction (from intraday_raw 1m/2d/prepost) -
            # Crypto: 24/7 markets; market_session=regular; AH fields null.
            # No intraday data: market_session=closed; AH fields null.
            # Active AH window today: extract last AH bar; ah_source="yfinance".
            extended_hours_last = None
            extended_hours_change_pct = None
            extended_hours_volume = None
            extended_hours_last_timestamp = None
            market_session = "closed"
            ah_source = None  # reserved for Session 4 Alpaca fallback

            if ticker.endswith("-USD"):
                market_session = "regular"
            elif intraday_raw is not None:
                intra_df = None
                if multi:
                    if ticker in intraday_raw.columns.get_level_values(0):
                        intra_df = intraday_raw[ticker].dropna(how="all")
                else:
                    intra_df = intraday_raw.dropna(how="all")

                if intra_df is None or intra_df.empty:
                    market_session = "closed"
                else:
                    # yfinance 1.3.0 returns tz-aware UTC; convert to ET
                    if intra_df.index.tz is None:
                        bars_et = intra_df.tz_localize("UTC").tz_convert(ET)
                    else:
                        bars_et = intra_df.tz_convert(ET)

                    et_now = datetime.now(ET)
                    today_et = et_now.date()
                    today_bars = bars_et[bars_et.index.date == today_et]

                    if today_bars.empty:
                        market_session = "closed"
                    else:
                        last_bar_time = today_bars.index[-1].time()
                        if time(4, 0) <= last_bar_time < time(9, 30):
                            market_session = "pre-market"
                        elif time(9, 30) <= last_bar_time < time(16, 0):
                            market_session = "regular"
                        elif time(16, 0) <= last_bar_time < time(20, 0):
                            market_session = "after-hours"
                        else:
                            market_session = "closed"

                        if market_session in ("pre-market", "after-hours"):
                            ah_bars = today_bars[
                                (today_bars.index.time < time(9, 30))
                                | (today_bars.index.time >= time(16, 0))
                            ]
                            if not ah_bars.empty:
                                extended_hours_last = float(ah_bars["Close"].iloc[-1])
                                if price and price != 0:
                                    extended_hours_change_pct = round(
                                        ((extended_hours_last - price) / price) * 100, 2
                                    )
                                # 0 = AH session active but ticker untraded; null = no AH session
                                extended_hours_volume = int(ah_bars["Volume"].sum())
                                extended_hours_last_timestamp = ah_bars.index[-1].isoformat()
                                ah_source = "yfinance"

            intraday_market_sessions[ticker] = market_session

            entry.update({
                "extended_hours_last": extended_hours_last,
                "extended_hours_change_pct": extended_hours_change_pct,
                "extended_hours_volume": extended_hours_volume,
                "extended_hours_last_timestamp": extended_hours_last_timestamp,
                "market_session": market_session,
                "ah_source": ah_source,
            })

            # ah_mover signal: emit when AH change_pct magnitude exceeds threshold
            if extended_hours_change_pct is not None and abs(extended_hours_change_pct) >= AH_MOVER_THRESHOLD_PCT:
                result["signals"]["ah_movers"].append(ticker)

            # -- Route to correct bucket -----------------------------------
            if ticker in INDEX_MAP:
                name = INDEX_MAP[ticker]
                result["indices"][name] = entry
            elif ticker.endswith("-USD"):
                crypto_name = ticker.replace("-USD", "")
                result["crypto"][crypto_name] = entry
            else:
                # Compute technicals for equities
                rsi = compute_rsi(closes)
                ma50 = compute_ma(closes, 50)
                ma200 = compute_ma(closes, 200)
                entry.update({
                    "rsi14": rsi,
                    "ma50": ma50,
                    "ma200": ma200,
                    "above_ma50": price > ma50 if ma50 else None,
                    "above_ma200": price > ma200 if ma200 else None,
                })
                result["equities"][ticker] = entry

                # Signal detection
                if rsi is not None and rsi < 30:
                    result["signals"]["oversold"].append(ticker)
                if rsi is not None and rsi > 70:
                    result["signals"]["overbought"].append(ticker)
                if ma50 and price < ma50:
                    result["signals"]["below_ma50"].append(ticker)
                if ma200 and price < ma200:
                    result["signals"]["below_ma200"].append(ticker)

        except Exception as e:
            result["errors"].append(f"{ticker}: {e}")

    # -- Extended-hours movers aggregation (top-level; sorted desc by |magnitude|) -
    # Always a list (never null) so consuming skills can iterate without null-check.
    movers_list = []
    for bucket_name in ("equities", "crypto", "indices"):
        for t, e in result.get(bucket_name, {}).items():
            mag = e.get("extended_hours_change_pct")
            if mag is not None and abs(mag) >= AH_MOVER_THRESHOLD_PCT:
                movers_list.append({
                    "ticker": t,
                    "magnitude_pct": mag,
                    "session": e.get("market_session"),
                    "last_price": e.get("extended_hours_last"),
                    "last_timestamp": e.get("extended_hours_last_timestamp"),
                })
    movers_list.sort(key=lambda x: abs(x["magnitude_pct"]), reverse=True)
    result["extended_hours_movers"] = movers_list

    # -- VIX term structure ------------------------------------------------
    vix_spot = result["indices"].get("VIX", {}).get("price")
    vix3m = result["indices"].get("VIX3M", {}).get("price")
    if vix_spot and vix3m:
        result["indices"]["VIX"]["term_structure"] = (
            "backwardation" if vix_spot > vix3m else "contango"
        )
    # Remove VIX3M from output (internal use only)
    result["indices"].pop("VIX3M", None)

    # -- Per-ticker metadata (beta, short ratio, 52wk, earnings) ----------
    for ticker in equity_tickers:
        if ticker not in result["equities"]:
            continue
        try:
            info = yf.Ticker(ticker).info
            e = result["equities"][ticker]
            e["beta"] = safe_round(info.get("beta"))
            e["short_ratio"] = safe_round(info.get("shortRatio"))
            e["pct_from_52wk_high"] = safe_round(
                (e["price"] - info.get("fiftyTwoWeekHigh", e["price"]))
                / info.get("fiftyTwoWeekHigh", e["price"])
                * 100
            ) if info.get("fiftyTwoWeekHigh") else None
            e["pct_from_52wk_low"] = safe_round(
                (e["price"] - info.get("fiftyTwoWeekLow", e["price"]))
                / info.get("fiftyTwoWeekLow", e["price"])
                * 100
            ) if info.get("fiftyTwoWeekLow") else None

            # Next earnings date
            earn_dates = info.get("earningsTimestamps") or []
            if not earn_dates:
                # Try the calendar approach
                try:
                    cal = yf.Ticker(ticker).calendar
                    if cal is not None and not cal.empty:
                        earn_date = cal.index[0] if hasattr(cal, "index") else None
                        if earn_date:
                            earn_dates = [earn_date]
                except Exception:
                    pass

            # Try earningsDate from info
            if not earn_dates:
                ed = info.get("earningsDate")
                if ed:
                    earn_dates = ed if isinstance(ed, list) else [ed]

            next_earn = None
            today_dt = date.today()
            for ed in earn_dates:
                try:
                    if isinstance(ed, (int, float)):
                        from datetime import timezone
                        ed_date = datetime.fromtimestamp(ed, tz=timezone.utc).date()
                    elif isinstance(ed, str):
                        ed_date = datetime.fromisoformat(ed).date()
                    elif hasattr(ed, "date"):
                        ed_date = ed.date()
                    else:
                        ed_date = ed
                    if ed_date >= today_dt:
                        if next_earn is None or ed_date < next_earn:
                            next_earn = ed_date
                except Exception:
                    continue

            if next_earn:
                e["next_earnings"] = str(next_earn)
                days_to_earn = (next_earn - today_dt).days
                if days_to_earn <= 14:  # ~10 trading days
                    result["signals"]["earnings_within_10d"].append(ticker)

            if e.get("short_ratio") and e["short_ratio"] > 5:
                result["signals"]["high_short_ratio"].append(ticker)

        except Exception as ex:
            result["errors"].append(f"{ticker} info: {ex}")

    # -- Market status -----------------------------------------------------
    # Preferred: per-ticker intraday market_session reduction. Falls back to
    # ET-aware clock + last_data_date when intraday data unavailable.
    result["market_status"] = detect_market_status(last_date, intraday_market_sessions)
    result["last_trading_day"] = str(last_date) if last_date else None

    return result


# -- CLI -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Fetch market data for /brief")
    parser.add_argument(
        "--equities", type=str, default="",
        help="Comma-separated equity/ETF tickers",
    )
    parser.add_argument(
        "--crypto", type=str, default="",
        help="Comma-separated crypto tickers (without -USD suffix)",
    )
    parser.add_argument(
        "--no-extended", action="store_true", dest="no_extended",
        help="Skip extended-hours bar fetching (preserves pre-Mission-3 daily-bar-only behavior)",
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Force JSON output (current default; reserved for clarity)",
    )
    args = parser.parse_args()

    eq = [t.strip() for t in args.equities.split(",") if t.strip()]
    cr = [t.strip() for t in args.crypto.split(",") if t.strip()]

    # Honor FETCH_PRICES_NO_EXTENDED=1 env var as opt-out equivalent
    no_extended = args.no_extended or os.environ.get("FETCH_PRICES_NO_EXTENDED") == "1"

    data = fetch_all(eq, cr, no_extended=no_extended)
    print(json.dumps(data, indent=2, default=str))


if __name__ == "__main__":
    main()
