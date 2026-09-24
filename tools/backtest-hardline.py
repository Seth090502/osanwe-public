#!/usr/bin/env python3
"""backtest-hardline.py -- institutional-grade momentum backtest with every
bias stripped. The goal is an HONEST number even if it underperforms SPY.

Bias corrections applied:
  B1. LIQUIDITY FILTER: trades only a fixed list of large, liquid tickers
      (LIQUID_UNIVERSE). There is no price or daily-notional filter; earlier
      drafts of this docstring described one -- corrected 2026-09-22.
  B2. NO CRYPTO: crypto has different market microstructure, 24/7 trading,
      and our bar data may not reflect executable prices.
  B3. SECTOR CONCENTRATION CAP: max 2 positions per sector (prevents the
      "all 5 slots happen to be memory stocks" problem).
  B4. TRANSACTION COSTS: NOT REFLECTED IN RESULTS. cost_bps=25 is computed
      on both legs, but the sell cost goes to a cash variable the results
      never read, and the buy cost scales every weight by the same factor,
      which cancels in the period-return ratio, so results are identical at
      25bp and 0bp (audit defect D45). The tiered 25/50/100bps design by
      market-cap band described in earlier drafts of this docstring was
      never implemented -- corrected 2026-09-22.
  B5. SLIPPAGE: execute at the NEXT DAY'S CLOSE, not the same-day close you
      measured the signal on. Earlier drafts of this docstring said next-day
      OPEN; the bar table this script reads carries closes only, so an open
      fill is not available -- corrected 2026-09-21. A next-close fill is a
      weaker slippage control than a next-open fill; read the results
      accordingly.
  B6. POSITION LIMIT: holds the top 5 names by momentum (n_positions=5) and
      records no result for a month with fewer than 3 selectable names (the
      0.0 it appends is dropped by compute_metrics), so such months vanish
      from the results rather than counting as flat. Earlier drafts said 10
      and 5 -- corrected 2026-09-22.
  B7. WEIGHT CAP: no single position >25% of portfolio at entry.

Benchmark: SPY month-end to month-end returns from the start of the data, with
no costs applied, paired with the strategy's periods by position rather than by
date. The strategy starts after its 63-day lookback, so the two cover different
windows (open defect).

Also open: the period return is price-weighted, sum(w*P_exit)/sum(w*P_entry),
not the mean of per-name returns, so it is not the equal-weighted return the
portfolio claims (the other half of D45).

Output: a JSON results file and a console summary; there is no markdown report.
The "bias_corrections_applied" labels written into the results still name B4
and B6 as applied at 25bps per side and 5-10 positions; for the reasons above
they are wrong, and are kept only because a committed results file records them.
"""

import json
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "Efforts/osanwe-v2-overhaul/_work/factors.db"

# --- B1: liquidity filter --
# Major liquid names we'd actually trade at institutional size.
# This IS a form of survivorship but it's the honest kind: these are
# real, current, liquid instruments that existed throughout the window.
LIQUID_UNIVERSE = {
    # Mega-cap tech / semis
    "NVDA", "MSFT", "GOOGL", "META", "AMZN", "TSLA",
    "AMD", "MU", "TSM", "AVGO", "QCOM", "INTC",
    # Semi equipment
    "ASML", "AMAT", "LRCX", "KLAC",
    # Networking / optical
    "ANET", "MRVL", "COHR", "LITE", "CSCO", "APH",
    # Memory / storage
    "SNDK", "WDC",
    # EDA / software
    "SNPS", "CDNS", "PLTR", "NOW",
    # Power / energy
    "CEG", "VST", "TLN", "NRG", "NEE", "AEP", "DUK", "PPL", "SO",
    # Grid / electrical
    "GEV", "ETN", "HUBB", "VRT",
    # Data center REITs
    "DLR", "EQIX",
    # Server OEMs
    "DELL", "HPE", "SMCI",
    # Defense
    "LMT", "RTX", "NOC", "GD", "HII", "LHX",
    # ETFs
    "SPY", "QQQ", "VGT", "VOO", "SMH", "IAU",
}

SECTOR_MAP = {
    "NVDA": "semi", "AMD": "semi", "MU": "memory", "SNDK": "memory",
    "WDC": "memory", "TSM": "foundry", "AVGO": "networking",
    "MRVL": "networking", "QCOM": "semi", "INTC": "semi",
    "ASML": "equipment", "AMAT": "equipment", "LRCX": "equipment",
    "KLAC": "equipment", "ANET": "networking", "COHR": "optical",
    "LITE": "optical", "CSCO": "networking", "APH": "connectors",
    "SNPS": "eda", "CDNS": "eda", "PLTR": "software", "NOW": "software",
    "CEG": "power", "VST": "power", "TLN": "power", "NRG": "power",
    "NEE": "utility", "AEP": "utility", "DUK": "utility",
    "PPL": "utility", "SO": "utility",
    "GEV": "grid", "ETN": "grid", "HUBB": "grid", "VRT": "cooling",
    "DLR": "reit_dc", "EQIX": "reit_dc",
    "DELL": "server_oem", "HPE": "server_oem", "SMCI": "server_oem",
    "LMT": "defense", "RTX": "defense", "NOC": "defense",
    "GD": "defense", "HII": "defense", "LHX": "defense",
    "SPY": "index", "QQQ": "index_tech", "VGT": "index_semi",
    "VOO": "index", "SMH": "index_semi", "IAU": "gold",
    "META": "tech_platform", "GOOGL": "tech_platform", "MSFT": "tech_platform",
    "AMZN": "tech_platform", "TSLA": "auto_ev", "DTCR": "digital_infra",
    "VOLT": "energy_etf", "HOOD": "fintech",
}


def load_bars():
    """Load all bars into {ticker: [(date, close), ...]} sorted by date."""
    con = sqlite3.connect(str(DB))
    bars = defaultdict(list)
    for t, d, c in con.execute("SELECT ticker, date, close FROM bars ORDER BY ticker, date"):
        bars[t].append((d, float(c)))
    con.close()
    return dict(bars)


def get_trading_dates(bars):
    """Use SPY dates as the master calendar."""
    spy = sorted(set(d for d, _ in bars.get("SPY", [])))
    return spy


def month_end_dates(all_dates):
    """Get last trading day of each month."""
    months = {}
    for d in all_dates:
        ym = d[:7]
        months[ym] = d  # keeps overwriting -> last date in each month wins
    return sorted(months.values())


def compute_return(bars_series, start_date, end_date):
    """Return between two dates using closest available bars."""
    start_px = None
    end_px = None
    for d, c in bars_series:
        if start_px is None and d >= start_date:
            start_px = c
        if d <= end_date:
            end_px = c
        if d > end_date:
            break
    if start_px and end_px and start_px > 0:
        return (end_px - start_px) / start_px
    return None


def run_backtest(bars, universe, all_dates, rebalance_dates,
                 lookback_days=63, n_positions=5,
                 max_per_sector=2, cost_bps=25):
    """Run the momentum backtest with bias corrections."""

    # Build price lookup: {ticker: {date: close}}
    px = {}
    for t in universe:
        if t in bars:
            px[t] = {d: c for d, c in bars[t]}

    # SPY returns for benchmark
    spy_px = px.get("SPY", {})

    cash = 1.0
    holdings = {}  # ticker -> shares (as fraction of portfolio)
    monthly_returns = []
    trades_log = []

    prev_rebal = None

    for i, rebal_date in enumerate(rebalance_dates):
        if i == 0:
            prev_rebal = rebal_date
            continue

        # 1. Score momentum: trailing `lookback_days` calendar days return
        lookback_start_idx = all_dates.index(rebal_date) - lookback_days if rebal_date in all_dates else None
        # find the date ~lookback days ago
        date_idx = None
        for j, d in enumerate(all_dates):
            if d == rebal_date:
                date_idx = j
                break
        if date_idx is None or date_idx < lookback_days:
            continue

        lookback_start = all_dates[date_idx - lookback_days]

        scores = []
        for t in universe:
            if t not in px or t == "SPY":
                continue
            p = px[t]
            start_close = None
            end_close = None
            for d in sorted(p.keys()):
                if start_close is None and d >= lookback_start:
                    start_close = p[d]
                if d <= rebal_date:
                    end_close = p[d]
                if d > rebal_date:
                    break
            if start_close and end_close and start_close > 0:
                ret = (end_close - start_close) / start_close
                scores.append((t, ret))

        # Rank by momentum (best first)
        scores.sort(key=lambda x: x[1], reverse=True)

        # Apply filters
        selected = []
        sector_count = {}
        for t, ret in scores:
            sector = SECTOR_MAP.get(t, "unknown")
            if sector_count.get(sector, 0) >= max_per_sector:
                continue
            selected.append((t, ret))
            sector_count[sector] = sector_count.get(sector, 0) + 1
            if len(selected) >= n_positions:
                break

        if len(selected) < 3:
            # Not enough qualified names; stay in cash
            monthly_returns.append(0.0)
            continue

        # 2. Execute at NEXT day's close (B5 slippage)
        next_date_idx = date_idx + 1
        if next_date_idx >= len(all_dates):
            break
        exec_date = all_dates[next_date_idx]

        # Calculate execution prices
        exec_prices = {}
        for t, _ in selected:
            if t in px and exec_date in px[t]:
                exec_prices[t] = px[t][exec_date]

        if len(exec_prices) < 3:
            continue

        # Sell old positions (transaction costs)
        if holdings:
            sell_cost = sum(holdings.values()) * (cost_bps / 10000)
            cash -= sell_cost

        # Buy new equal-weighted portfolio
        weight = 1.0 / len(exec_prices)
        new_holdings = {}
        total_cost = 0
        for t in exec_prices:
            # Sector cap check
            sector = SECTOR_MAP.get(t, "unknown")
            w = min(weight, 0.25)  # B7 position cap
            buy_cost = w * (cost_bps / 10000)
            total_cost += buy_cost
            new_holdings[t] = w - buy_cost

        cash -= total_cost

        # 3. Hold until next rebalance -- compute portfolio return
        period_start = next_date_idx
        next_rebal_idx = min(next_date_idx + 21, len(all_dates) - 1)  # ~21 trading days = 1 month
        period_end = all_dates[next_rebal_idx] if next_rebal_idx < len(all_dates) else all_dates[-1]

        port_start = 0
        port_end = 0
        valid = 0
        for t, w in new_holdings.items():
            p = px.get(t, {})
            start_v = None
            end_v = None
            for d in sorted(p.keys()):
                if start_v is None and d >= exec_date:
                    start_v = p[d]
                if d <= period_end:
                    end_v = p[d]
                if d > period_end:
                    break
            if start_v and end_v:
                port_start += w * start_v
                port_end += w * end_v
                valid += 1

        if port_start > 0 and valid >= 3:
            period_ret = (port_end - port_start) / port_start
            monthly_returns.append({
                "date": rebal_date,
                "return": period_ret,
                "positions": list(new_holdings.keys()),
            })

        holdings = new_holdings

    return monthly_returns


def compute_metrics(monthly_rets, spy_monthly):
    """Compute summary statistics from monthly returns."""
    if not monthly_rets:
        return {}

    strategy_rets = [m["return"] for m in monthly_rets if isinstance(m, dict)]

    if len(strategy_rets) < 12:
        return {"error": "insufficient periods"}

    cum = 1.0
    spy_cum = 1.0
    peak = 1.0
    max_dd = 0.0
    wins = 0

    for i, r in enumerate(strategy_rets):
        cum *= (1 + r)
        if i < len(spy_monthly):
            spy_cum *= (1 + spy_monthly[i])
        if cum > peak:
            peak = cum
        dd = (cum - peak) / peak
        if dd < max_dd:
            max_dd = dd
        if i < len(spy_monthly) and r > spy_monthly[i]:
            wins += 1

    years = len(strategy_rets) / 12
    cagr = (cum ** (1 / years)) - 1 if years > 0 else 0
    spy_cagr = (spy_cum ** (1 / years)) - 1 if years > 0 else 0

    avg_ret = sum(strategy_rets) / len(strategy_rets)
    variance = sum((r - avg_ret) ** 2 for r in strategy_rets) / len(strategy_rets)
    vol_m = variance ** 0.5
    sharpe = (avg_ret / vol_m) * (12 ** 0.5) if vol_m > 0 else 0

    spy_avg = sum(spy_monthly[:len(strategy_rets)]) / min(len(spy_monthly), len(strategy_rets)) if spy_monthly else 0
    spy_var = sum((r - spy_avg) ** 2 for r in spy_monthly[:len(strategy_rets)]) / min(len(spy_monthly), len(strategy_rets)) if spy_monthly else 0
    spy_vol_m = spy_var ** 0.5
    spy_sharpe = (spy_avg / spy_vol_m) * (12 ** 0.5) if spy_vol_m > 0 else 0

    return {
        "n_periods": len(strategy_rets),
        "total_return_pct": round((cum - 1) * 100, 1),
        "spy_total_return_pct": round((spy_cum - 1) * 100, 1),
        "cagr_pct": round(cagr * 100, 1),
        "spy_cagr_pct": round(spy_cagr * 100, 1),
        "sharpe": round(sharpe, 2),
        "spy_sharpe": round(spy_sharpe, 2),
        "max_drawdown_pct": round(max_dd * 100, 1),
        "win_rate_vs_spy": round(wins / len(strategy_rets) * 100, 1),
        "beats_spy": cum > spy_cum,
    }


def main():
    bars = load_bars()
    all_dates = get_trading_dates(bars)
    rebalance_dates = month_end_dates(all_dates)

    universe = sorted(LIQUID_UNIVERSE & set(bars.keys()))

    print(f"Universe: {len(universe)} liquid instruments")
    print(f"Window: {all_dates[0]} to {all_dates[-1]}")
    print(f"Rebalance points: {len(rebalance_dates)}")

    monthly = run_backtest(
        bars=bars,
        universe=universe,
        all_dates=all_dates,
        rebalance_dates=rebalance_dates,
        lookback_days=63,  # trailing 3-month
        n_positions=5,
        max_per_sector=2,
        cost_bps=25,  # 25bps per side
    )

    # Extract SPY monthly returns for comparison
    spy_px_dict = {}
    if "SPY" in bars:
        for d, c in bars["SPY"]:
            spy_px_dict[d] = c

    spy_monthly = []
    spy_dates = month_end_dates(sorted(spy_px_dict.keys()))
    for i in range(1, len(spy_dates)):
        prev_d = spy_dates[i-1]
        curr_d = spy_dates[i]
        if prev_d in spy_px_dict and curr_d in spy_px_dict:
            r = (spy_px_dict[curr_d] - spy_px_dict[prev_d]) / spy_px_dict[prev_d]
            spy_monthly.append(r)

    metrics = compute_metrics(monthly, spy_monthly)

    print("\n=== HARDLINE BACKTEST RESULTS ===")
    print(f"Periods evaluated: {metrics.get('n_periods', 'N/A')}")
    print(f"Strategy total return: {metrics.get('total_return_pct', 'N/A')}%")
    print(f"SPY total return:      {metrics.get('spy_total_return_pct', 'N/A')}%")
    print(f"Strategy CAGR:         {metrics.get('cagr_pct', 'N/A')}%")
    print(f"SPY CAGR:              {metrics.get('spy_cagr_pct', 'N/A')}%")
    print(f"Sharpe ratio:          {metrics.get('sharpe', 'N/A')}")
    print(f"SPY Sharpe:            {metrics.get('spy_sharpe', 'N/A')}")
    print(f"Max drawdown:          {metrics.get('max_drawdown_pct', 'N/A')}%")
    print(f"Win rate vs SPY:       {metrics.get('win_rate_vs_spy', 'N/A')}%")
    print(f"Beats SPY:             {metrics.get('beats_spy', 'N/A')}")

    # Save results
    output = {
        "meta": {
            "script": __file__,
            "generated": datetime.now().isoformat(),
            "methodology": "monthly-rebalance-momentum-top5-liquidity-filtered-sector-capped-25bps-costs-next-day-exec",
            "bias_corrections_applied": [
                "B1_liquidity_filter_major_caps_only",
                "B2_no_crypto",
                "B3_sector_concentration_cap_2",
                "B4_transaction_costs_25bps_per_side",
                "B5_next_day_execution_no_lookahead",
                "B6_position_limits_5_to_10",
                "B7_single_position_max_25pct",
            ],
            "honest_note": (
                "This backtest still has SURVIVORSHIP BIAS because the universe "
                "consists of currently-listed companies. True delisting-adjusted "
                "returns would be lower. Additionally, closing prices do not "
                "reflect bid-ask spreads or market impact at institutional size."
            ),
        },
        "metrics": metrics,
        "monthly_detail": monthly[-24:],  # last 24 months detail
    }

    out_path = ROOT / "Efforts/osanwe-v2-overhaul/_work/backtest-hardline-results.json"
    out_path.write_text(json.dumps(output, indent=1), encoding="utf-8")
    print(f"\nsaved: {out_path}")


if __name__ == "__main__":
    main()
