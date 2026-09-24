#!/usr/bin/env python3
"""validate-prediction.py -- validate a prediction object against
tools/prediction-schema.json (the prediction contract, v1).

Replaces vague BUY/SELL labels: a recorded prediction must be a full
distribution object with explicit horizon, benchmark, uncertainty,
costs, capacity and invalidation terms.

Usage:
  python tools/validate-prediction.py pred.json          # one file
  python tools/validate-prediction.py a.json b.json      # several files
  echo '<json>' | python tools/validate-prediction.py -  # stdin
  python tools/validate-prediction.py --self-test        # run built-in tests

Exit codes: 0 = valid; 1 = invalid; 2 = usage/schema-load error.
Stdout: JSON verdict per file. Stderr: human-readable detail.

Dependencies: jsonschema (already in the vault environment). Falls back to
stdlib-only structural checking if jsonschema is unavailable -- the fallback
covers every contract rule except regex pattern details.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = Path(__file__).resolve().parent / "prediction-schema.json"

TS_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
)
TICKER_RE = re.compile(r"^[A-Z0-9._^-]{1,12}$")
CALIB_BIN_RE = re.compile(r"^\d{2}-\d{2}$")
SIGNAL_KEY_RE = re.compile(r"^[a-z][a-z0-9_-]*$")

REQUIRED = [
    "instrument_id", "prediction_timestamp", "information_cutoff",
    "horizon_days", "target_variable", "benchmark_id", "expected_return",
    "return_distribution", "probability_positive_excess",
    "expected_volatility", "expected_max_drawdown_pct", "var_95_daily",
    "confidence_interval", "calibration_bin", "signal_components",
    "model_version", "dataset_version", "invalidation_conditions",
    "expiration_timestamp", "recommended_action_range", "assumed_cost_bps",
    "capacity_estimate_usd", "liquidity_score",
]


def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _ts(s):
    """Parse an ISO-8601 timestamp with offset into an aware datetime."""
    from datetime import datetime
    txt = s[:-1] + "+00:00" if s.endswith("Z") else s
    return datetime.fromisoformat(txt)


def semantic_checks(obj):
    """Cross-field rules JSON Schema cannot express. Returns error list."""
    errs = []

    def num(o):
        return isinstance(o, (int, float)) and not isinstance(o, bool)

    # Timestamp ordering: cutoff <= issued < expiration.
    try:
        cut, iss, exp = (_ts(obj["information_cutoff"]),
                         _ts(obj["prediction_timestamp"]),
                         _ts(obj["expiration_timestamp"]))
        if cut > iss:
            errs.append("information_cutoff is later than prediction_timestamp "
                        "(lookahead leakage)")
        if exp <= iss:
            errs.append("expiration_timestamp must be strictly after "
                        "prediction_timestamp")
        if (exp.date() == iss.date()):
            pass  # same-day expiry allowed (short-horizon); no opinion here
    except KeyError:
        pass  # missing fields already reported by schema layer
    except ValueError as e:
        errs.append("unparseable timestamp: %s" % e)

    # Percentile ordering p10 <= p25 <= median <= p75 <= p90.
    d = obj.get("return_distribution")
    if isinstance(d, dict) and all(num(d.get(k)) for k in
                                   ("p10", "p25", "median", "p75", "p90")):
        keys = ["p10", "p25", "median", "p75", "p90"]
        for lo, hi in zip(keys, keys[1:]):
            if d[lo] > d[hi]:
                errs.append("return_distribution not monotonic: %s (%s) > %s (%s)"
                            % (lo, d[lo], hi, d[hi]))
        med = d["median"]
        er = obj.get("expected_return")
        if num(er) and abs(med - er) > 0.05:
            errs.append("expected_return (%.4f) diverges from distribution "
                        "median (%.4f) by more than 0.05" % (er, med))

    # Confidence interval sanity.
    ci = obj.get("confidence_interval")
    if isinstance(ci, dict) and all(num(ci.get(k)) for k in
                                    ("lower", "upper", "level")):
        if ci["lower"] > ci["upper"]:
            errs.append("confidence_interval lower > upper")

    # Action range must be a range with room, not a degenerate point.
    ar = obj.get("recommended_action_range")
    if isinstance(ar, dict) and all(num(ar.get(k)) for k in
                                    ("min_action", "max_action")):
        span = ar["max_action"] - ar["min_action"]
        if span <= 0:
            errs.append("recommended_action_range must have max_action > "
                        "min_action (a RANGE, not a point)")
        elif span > 200:
            errs.append("recommended_action_range span %.1f exceeds the "
                        "-100..+100 action scale" % span)

    # Calibration bin bounds should bracket probability_positive_excess*100.
    bin_ = obj.get("calibration_bin")
    pp = obj.get("probability_positive_excess")
    if isinstance(bin_, str) and CALIB_BIN_RE.match(bin_) \
            and num(pp) and 0.0 <= pp <= 1.0:
        lo_s, hi_s = bin_.split("-")
        lo_b, hi_b = int(lo_s), int(hi_s)
        pct = round(pp * 100.0)
        if not (lo_b <= pct <= hi_b or (hi_b >= 99 and pct >= lo_b)):
            errs.append("calibration_bin '%s' does not bracket "
                        "probability_positive_excess (%.0f%%)" % (bin_, pct))

    # Signal component scores bounded like z-scores.
    sc = obj.get("signal_components")
    if isinstance(sc, dict):
        for k, v in sc.items():
            if not num(v) or v < -10.0 or v > 10.0:
                errs.append("signal_components['%s'] must be a number in "
                            "[-10, 10], got %r" % (k, v))

    return errs


def validate(obj, schema=None, use_jsonschema=True):
    """Return list of error strings ([] means valid)."""
    errors = []
    schema = schema if schema is not None else load_schema()

    missing = [k for k in REQUIRED if k not in obj]
    if missing:
        errors.append("missing required field(s): %s" % ", ".join(missing))

    if use_jsonschema:
        try:
            import jsonschema
            validator = jsonschema.Draft7Validator(schema)
            for e in sorted(validator.iter_errors(obj),
                            key=lambda e: list(e.absolute_path)):
                loc = ".".join(str(p) for p in e.absolute_path) or "<root>"
                errors.append("%s: %s" % (loc, e.message))
            if not errors:
                errors.extend(semantic_checks(obj))
            return errors
        except ImportError:
            pass  # fall through to stdlib checks

    # ---- stdlib fallback: mirror the schema's structural rules ----
    def is_num(v):
        return isinstance(v, (int, float)) and not isinstance(v, bool)

    if not isinstance(obj.get("instrument_id"), str) \
            or not TICKER_RE.match(obj.get("instrument_id", "")):
        errors.append("instrument_id: must be an upper-case ticker string")
    if obj.get("target_variable") != "excess_return_vs_benchmark":
        errors.append("target_variable: must be 'excess_return_vs_benchmark'")
    if not isinstance(obj.get("benchmark_id"), str) \
            or not TICKER_RE.match(obj.get("benchmark_id", "")):
        errors.append("benchmark_id: must be an upper-case ticker string")
    for f in ("prediction_timestamp", "information_cutoff",
              "expiration_timestamp"):
        v = obj.get(f)
        if not isinstance(v, str) or not TS_RE.match(v):
            errors.append("%s: must be ISO 8601 WITH timezone offset" % f)
    hd = obj.get("horizon_days")
    if not isinstance(hd, int) or isinstance(hd, bool) \
            or not (1 <= hd <= 1260):
        errors.append("horizon_days: must be integer in [1, 1260]")
    for f in ("probability_positive_excess",):
        v = obj.get(f)
        if not is_num(v) or not (0.0 <= v <= 1.0):
            errors.append("%s: must be number in [0, 1]" % f)
    for f in ("expected_return", "expected_volatility",
              "expected_max_drawdown_pct", "var_95_daily", "assumed_cost_bps",
              "capacity_estimate_usd"):
        if not is_num(obj.get(f)):
            errors.append("%s: must be a number" % f)
    if is_num(obj.get("expected_volatility")) \
            and not (0.0 <= obj["expected_volatility"] <= 5.0):
        errors.append("expected_volatility: must be in [0, 5]")
    ls = obj.get("liquidity_score")
    if not isinstance(ls, int) or isinstance(ls, bool) or not (1 <= ls <= 10):
        errors.append("liquidity_score: must be integer in [1, 10]")
    for f in ("model_version", "dataset_version"):
        v = obj.get(f)
        if not isinstance(v, str) or not (1 <= len(v) <= 64):
            errors.append("%s: must be a non-empty string (<=64 chars)" % f)
    iv = obj.get("invalidation_conditions")
    if not isinstance(iv, list) or len(iv) < 1 \
            or not all(isinstance(x, str) and len(x) >= 8 for x in iv):
        errors.append("invalidation_conditions: non-empty array of strings "
                      "(each >= 8 chars)")
    rd = obj.get("return_distribution")
    if not isinstance(rd, dict) \
            or set(rd) != {"p10", "p25", "median", "p75", "p90",
                           "skew", "kurtosis"} \
            or not all(is_num(v) for v in rd.values()):
        errors.append("return_distribution: needs exactly {p10,p25,median,"
                      "p75,p90,skew,kurtosis}, all numeric")
    ci = obj.get("confidence_interval")
    if not isinstance(ci, dict) or set(ci) != {"lower", "upper", "level"} \
            or not all(is_num(v) for v in ci.values()) \
            or not (0.0 < ci.get("level", 0) < 1.0):
        errors.append("confidence_interval: needs exactly {lower,upper,level}"
                      ", numeric, level in (0,1)")
    ar = obj.get("recommended_action_range")
    if not isinstance(ar, dict) or set(ar) != {"min_action", "max_action"} \
            or not all(is_num(v) for v in ar.values()):
        errors.append("recommended_action_range: needs exactly {min_action,"
                      "max_action}, numeric")
    sc = obj.get("signal_components")
    if not isinstance(sc, dict) or len(sc) < 1 \
            or not all(isinstance(k, str) and SIGNAL_KEY_RE.match(k)
                       and is_num(v) for k, v in sc.items()):
        errors.append("signal_components: map of snake_case name -> numeric "
                      "score, at least one entry")
    b = obj.get("calibration_bin")
    if not isinstance(b, str) or not CALIB_BIN_RE.match(b):
        errors.append("calibration_bin: must match NN-NN (e.g. '70-79')")

    errors.extend(semantic_checks(obj))
    return errors


# ---------------------------------------------------------------- self-test

GOOD_PREDICTION = {
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


def _mutated(mutator):
    import copy
    o = copy.deepcopy(GOOD_PREDICTION)
    mutator(o)
    return o


BAD_CASES = [
    ("missing required field",
     _mutated(lambda o: o.pop("var_95_daily"))),
    ("naive timestamp (no timezone)",
     _mutated(lambda o: o.update(prediction_timestamp="2026-08-25T14:30:00"))),
    ("lookahead: cutoff after issue",
     _mutated(lambda o: o.update(information_cutoff="2026-08-26T00:00:00Z"))),
    ("wrong target_variable",
     _mutated(lambda o: o.update(target_variable="direction"))),
    ("probability out of range",
     _mutated(lambda o: o.update(probability_positive_excess=1.3))),
    ("non-monotonic percentiles",
     _mutated(lambda o: o["return_distribution"].update(p25=0.5))),
    ("point action range",
     _mutated(lambda o: o.update(recommended_action_range={"min_action": 5.0,
                                                           "max_action": 5.0}))),
    ("bad calibration bin",
     _mutated(lambda o: o.update(calibration_bin="high"))),
    ("bin does not bracket probability",
     _mutated(lambda o: o.update(calibration_bin="60-69"))),
    ("liquidity score out of bounds",
     _mutated(lambda o: o.update(liquidity_score=11))),
    ("no invalidation conditions",
     _mutated(lambda o: o.update(invalidation_conditions=[]))),
    ("empty signal components",
     _mutated(lambda o: o.update(signal_components={}))),
]


def self_test():
    failures = []
    good_errors = validate(dict(GOOD_PREDICTION))
    if good_errors:
        failures.append("good prediction rejected: %s" % good_errors)
    for label, case in BAD_CASES:
        errs = validate(case)
        if not errs:
            failures.append("BAD case NOT caught: %s" % label)
    # stdlib fallback path must agree on the good object too
    fb = validate(dict(GOOD_PREDICTION), use_jsonschema=False)
    if fb:
        failures.append("fallback rejected good prediction: %s" % fb)
    print(json.dumps({
        "self_test": "PASS" if not failures else "FAIL",
        "cases": 1 + len(BAD_CASES),
        "failures": failures,
    }, indent=2))
    return 0 if not failures else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="*", help="prediction JSON files, or '-' "
                    "for stdin; omit with --self-test")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(self_test())
    if not args.paths:
        ap.error("give at least one file, '-' for stdin, or --self-test")

    schema = load_schema()
    rc = 0
    for p in args.paths:
        try:
            text = sys.stdin.read() if p == "-" else Path(p).read_text(
                encoding="utf-8")
            obj = json.loads(text)
        except Exception as e:  # noqa: BLE001 - report any read/parse failure
            print(json.dumps({"file": p, "valid": False,
                              "errors": ["unreadable/unparseable: %s" % e]}))
            rc = 1
            continue
        errs = validate(obj, schema=schema)
        print(json.dumps({"file": p, "valid": not errs, "errors": errs}))
        if errs:
            rc = 1
    sys.exit(rc)


if __name__ == "__main__":
    main()
