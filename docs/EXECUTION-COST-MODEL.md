---
aliases: []
categories: [decisions]
status: complete
created: 2026-08-25
updated: 2026-08-25
tags: [fis]
related: ["[[phase-i-freeze-manifest]]"]
---

# Execution Cost Model -- Methodology

Tool: `tools/execution-cost-model.py`
Results snapshot: `data/execution-cost-results.json`
Status: planning-grade priors, ASCII-only, zero network dependencies.

## What it answers

Given `(ticker, order_size_usd)`, the model returns a per-trade cost
breakdown (spread, market impact, fees, FX) in basis points per side plus
the round-trip total in bp and dollars, and the break-even alpha: the
minimum expected excess return that justifies taking the trade.

## Universe

All 90 tickers from `_flow_per_ticker.json` (vault root, 2026-08 snapshot)
are classified into six instrument classes, with static per-ticker
overrides for names whose liquidity differs materially from their class
prior. Unknown tickers default to `MID_CAP_EQUITY` (conservative).

## Model

### 1. Spread cost

Per side we pay half the quoted bid-ask spread. Class priors are set from
the calibration bands below and cross-checked against published effective
spread studies; per-ticker overrides replace the prior where liquidity is
known to differ (e.g. SPY ~1 bp vs QNT ~15 bp half-spread).

### 2. Market impact -- square-root law

    impact_bp_per_side = y * sigma_daily_bp * sqrt(order_usd / adv_usd)

* `sigma_daily_bp`: typical daily volatility of the name (bp).
* `adv_usd`: representative average daily dollar volume.
* `y` (~1.0-1.5): class-specific coefficient combining temporary and
  permanent impact.
* `min_impact_bp`: floor representing pipeline/handling costs even at tiny
  participation.

The square-root form is the standard empirical result: Almgren, Thum,
Hauptmann & Li (2005, Risk) show realized impact grows with the square root
of participation rate; Torre & Ferrari (1999, Morgan Stanley) and Grinold &
Kahn (Active Portfolio Management, ch. 16) use the same functional form.
Consequence: impact is concave in order size -- doubling size raises impact
only ~1.41x, which the test suite verifies exactly.

### 3. Commissions and fees

Zero-commission equity brokers -> $0 for equities/ETFs. Crypto carries an
exchange taker fee (~8 bp/side), which dominates its spread component --
consistent with observed major-venue fee schedules.

### 4. Currency conversion (ADRs)

Liquid ADRs (TSM, ASML) trade in USD on NYSE/Nasdaq against deeply liquid
home lines: no explicit FX charge beyond a small friction allowance.
OTC ADRs (ABBNY, ATEYY) carry wide effective spreads instead; where a venue
does require conversion, `fx_bp` is charged per side.

### 5. Round trip

    round_trip_bp = 2 * (half_spread + impact + fees + fx)

One entry + one exit, each paying half-spread + impact + fees.

## Calibration bands (spec)

| Class              | Round-trip band | Representative check          |
|--------------------|-----------------|-------------------------------|
| LARGE_CAP_EQUITY   | 5-15 bp         | MSFT $50k-$5M -> 6.0-8.6 bp   |
| MID_CAP_EQUITY     | 15-40 bp        | AEIS $100k-$1M -> 16.4-27 bp  |
| SMALL_CAP_EQUITY   | 50-200 bp       | AAOI $100k-$1M -> 74-146 bp   |
| ETF_BROAD          | 3-8 bp          | VGT $25k-$1M -> 3.3-3.9 bp    |
| CRYPTO             | 20-50 bp        | BTC $25k-$5M -> 24-30 bp      |
| ADR_FOREIGN        | 8-40 bp         | TSM/ABBNY span the band       |

## Literature anchors used in tests

* **Loeb (1983), FAJ** -- block-trade impact rises steeply as firm size
  falls. Test: at equal dollar size, small-cap RT > mid > large > broad
  ETF, with small/large ratio > 5x.
* **Lesmond, Ogden & Trzcinka (1999), JF** -- small-cap trading costs an
  order of magnitude above large caps. Same ordering tests.
* **Almgren et al. (2005)** -- sqrt scaling. Tests verify exact
  sqrt(2)-per-doubling growth and sublinearity/concavity.
* **Frazzini, Israel & Moskowitz (2012), "Trading Costs of Asset Pricing
  Anomalies"** -- live one-way costs ~5-30 bp for liquid US large caps.
  Test: MSFT $1M one-way lands within that zone.
* **Korajczyk & Sadka (2004), JF** -- impact constrains strategy scale;
  motivates the ADV-participation output (`pct_of_adv`) on every estimate.
* Broad ETFs (SPY/QQQ) quote sub-bp spreads; our all-in figures include a
  conservative routing/handling floor rather than raw quote spread.

## Break-even alpha

A trade is worth doing only if expected excess return exceeds:

    breakeven_bp = round_trip_cost_bp + safety_buffer_bp
    annualized % = breakeven_bp * 365 / holding_days / 100

Examples (21-day hold unless noted):

| Trade            | Hurdle (bp) | Annualized |
|------------------|-------------|------------|
| QQQ $500k        | 3.5         | ~1%        |
| MSFT $1M         | 6.0         | ~1%        |
| AEIS $250k       | 19.2        | ~3%        |
| AAOI $250k       | 103.0       | ~18%       |
| AAOI $250k (5d)  | 103.0       | ~75%       |
| BTC $100k (7d)   | 25.0        | ~13%       |

Implication: identical signals clear easily in large caps/broad ETFs but
need triple-digit edges in small caps at short horizons -- position sizing
and turnover decisions should be hurdle-aware.

## Usage

    python tools/execution-cost-model.py --estimate AAOI 250000
    python tools/execution-cost-model.py --breakeven AEIS 250000 --days 10 --buffer 5
    python tools/execution-cost-model.py --demo --save-results data/execution-cost-results.json
    python tools/execution-cost-model.py --test

Programmatic API: `estimate_trade_cost(ticker, usd)`,
`break_even_alpha(ticker, usd, days, buffer)`,
`estimate_portfolio_costs([(ticker, usd), ...])`.

## Limitations

* Static priors: no live quotes or volumes; refresh overrides periodically.
* Class-level sigmas hide idiosyncratic vol (e.g. high-beta SMR-type
  names will impact more than modeled).
* Ignores borrow costs (shorting), financing, taxes, and timing-of-day
  liquidity effects (VWAP execution would realize less than these caps).
* Impact model is calibrated for orders < ~1% of ADV; larger clips should
  be scheduled across days, not lumped.
