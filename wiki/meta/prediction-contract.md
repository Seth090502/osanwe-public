---
type: meta
status: active
created: 2026-08-25
updated: 2026-08-25
tags: [topic/meta]
related: ["confidence-map-2026"]
---

# Prediction contract v1

Every quantitative prediction recorded in this vault is a **structured
prediction object**, not a BUY/SELL label. A label compresses an entire belief
into one word and makes calibration, backtesting, sizing, and post-mortems
impossible. The object below keeps the full distribution so that:

- **Backtests** can score realized outcomes against `expected_return`,
  `return_distribution` percentiles, and `probability_positive_excess`
  (`tools/backtest-prediction.py`, `tools/score-outcomes.py`).
- **Calibration** maps stated confidence to realized hit rates via
  `wiki/maintenance/calibration/confidence-map.json`; graders read the
  CALIBRATED value, never the raw one.
- **Sizing** uses `var_95_daily`, `expected_volatility`,
  `capacity_estimate_usd`, and `liquidity_score` -- not vibes.
- **Accountability** is exact: `information_cutoff` proves no lookahead,
  `model_version` / `dataset_version` make every prediction reproducible,
  `invalidation_conditions` + `expiration_timestamp` define when a prediction
  dies before its horizon.

Schema file: `tools/prediction-schema.json` (JSON Schema draft-07,
id `osanwe:prediction-object:v1`).
Validator: `python tools/validate-prediction.py <file.json>|-|--self-test`.

## Required fields

| field | type | meaning |
|---|---|---|
| `instrument_id` | string | Upper-case ticker (e.g. `AAPL`). |
| `prediction_timestamp` | ISO 8601 + TZ | When the prediction was issued. Naive timestamps are invalid. |
| `information_cutoff` | ISO 8601 + TZ | Last timestamp of data used. MUST be <= `prediction_timestamp`. Anything after it is lookahead leakage and invalidates the record. |
| `horizon_days` | int 1..1260 | Trading-day horizon (21 = month, 63 = quarter). |
| `target_variable` | const | Always `excess_return_vs_benchmark`. |
| `benchmark_id` | string | Benchmark ticker excess return is measured against (e.g. `SPY`). |
| `expected_return` | number | Point estimate of ANNUALIZED expected excess return as a decimal (-2.0..+2.0). Must agree with distribution median within 0.05. |
| `return_distribution` | object | `{p10, p25, median, p75, p90, skew, kurtosis}` -- annualized decimals; percentiles must be monotonic. This is the belief; the point estimate is only its center. |
| `probability_positive_excess` | number 0..1 | P(realized excess > 0 over the horizon). |
| `expected_volatility` | number | Annualized volatility of EXCESS returns (decimal). |
| `expected_max_drawdown_pct` | number | Expected max drawdown in PERCENT (positive). |
| `var_95_daily` | dollars > 0 | 95% one-day VaR for the intended position size. |
| `confidence_interval` | object | `{lower, upper, level}` on annualized excess return; lower <= upper, level in (0,1), e.g. level 0.8. |
| `calibration_bin` | `"NN-NN"` | Stated-confidence bin in `confidence-map.json` (e.g. `"70-79"`); must bracket `probability_positive_excess * 100`. Downstream readers substitute the map's calibrated rate. |
| `signal_components` | object | Named factor scores, each numeric in [-10, 10] (e.g. `{"momentum": 1.4, "quality": -0.3}`). >= 1 entry required so attribution is possible later. |
| `model_version` | string | Generating process version. |
| `dataset_version` | string | Reproducible input-data snapshot id. |
| `invalidation_conditions` | string[] | Concrete, checkable events that void the prediction early. >= 1 required. "Something feels wrong" is not checkable. |
| `expiration_timestamp` | ISO 8601 + TZ | Hard death time; must be strictly after issue regardless of horizon. |
| `recommended_action_range` | object | `{min_action, max_action}` in PERCENT of current position to change (-100 exit .. +100 double). MUST be a range (`max > min`) -- uncertainty in the belief forbids a single point action. |
| `assumed_cost_bps` | number | Round-trip transaction cost baked into net expectations. |
| `capacity_estimate_usd` | dollars > 0 | Capital capacity before impact erodes the edge beyond `assumed_cost_bps`. |
| `liquidity_score` | int 1..10 | Instrument liquidity, 10 = deepest. |

## Cross-field rules (checked by the validator, not by JSON Schema alone)

1. `information_cutoff` <= `prediction_timestamp` < `expiration_timestamp`.
2. Percentile ordering: `p10 <= p25 <= median <= p75 <= p90`.
3. `abs(expected_return - median) <= 0.05` -- the point estimate may not
   contradict the stated distribution.
4. `confidence_interval.lower <= upper`.
5. Action range span > 0 and <= 200 (the scale is -100..+100).
6. `calibration_bin` brackets `probability_positive_excess` as a percentage.
7. Every `signal_components` value in [-10, 10].

## Worked example

```json
{
  "instrument_id": "AAPL",
  "prediction_timestamp": "2026-08-25T14:30:00Z",
  "information_cutoff": "2026-08-25T14:00:00Z",
  "horizon_days": 63,
  "target_variable": "excess_return_vs_benchmark",
  "benchmark_id": "SPY",
  "expected_return": 0.08,
  "return_distribution": {
    "p10": -0.15, "p25": -0.02, "median": 0.08,
    "p75": 0.19, "p90": 0.31, "skew": -0.4, "kurtosis": 1.2
  },
  "probability_positive_excess": 0.72,
  "expected_volatility": 0.24,
  "expected_max_drawdown_pct": 18.5,
  "var_95_daily": 1450.0,
  "confidence_interval": {"lower": -0.06, "upper": 0.22, "level": 0.8},
  "calibration_bin": "70-79",
  "signal_components": {"momentum": 1.4, "quality": -0.3},
  "model_version": "invest-v2.3",
  "dataset_version": "prices-2026-08-25",
  "invalidation_conditions": [
    "guidance cut greater than 5 percent",
    "VIX term structure flips to backwardation"
  ],
  "expiration_timestamp": "2026-11-24T21:00:00Z",
  "recommended_action_range": {"min_action": 2.0, "max_action": 6.0},
  "assumed_cost_bps": 12.0,
  "capacity_estimate_usd": 250000.0,
  "liquidity_score": 9
}
```

Read aloud: "Over 63 trading days from 2026-08-25, using data through 14:00Z,
AAPL is expected to beat SPY by 8% annualized; there is a 72% chance of any
positive excess (historically, statements at this confidence have been right
~31% of the time per the calibration map -- treat accordingly); an 80%
interval runs -6% to +22%; if guidance is cut >5% or VIX term structure
inverts, this prediction is dead; act between +2% and +6% of current position."

## Usage

Validate before recording anything:

```
python tools/validate-prediction.py wiki/investing/predictions/<id>.json
python tools/validate-prediction.py --self-test   # 13 built-in cases
```

Exit codes: 0 valid, 1 invalid, 2 usage/schema error. The validator prefers
the installed `jsonschema` package but has a stdlib-only fallback covering all
structural rules.

## Versioning

This is `osanwe:prediction-object:v1`. Any breaking change bumps the `$id`
suffix and requires a migration note here plus an updated validator. Adding
optional fields does not require a bump.
