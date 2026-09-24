#!/usr/bin/env python3
"""kernel-alpha-note.py -- GAP-8: surface the decision-attribution result to the
kernel's Phase L guidance (advisory only).

Reads wiki/maintenance/calibration/decision-attribution.md, extracts the
selection-alpha number, and emits the exact advisory line to paste into
/invest Phase L (or reports it to stdout for --json consumers). This tool does
NOT edit doctrine numbers or the kernel -- advisory text only, refreshed weekly.
"""

import argparse
import json
import math
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "wiki/maintenance/calibration/decision-attribution.md"
MAX_MAP_AGE_DAYS = 45  # /invest R.8 requires a map younger than 45 days.


def parse_alpha(path=None):
    path = path or SRC
    try:
        t = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    m = re.search(r"Doctrine selection alpha:\s*\$([+-][\d,]+\.\d{2})", t)
    d = re.search(r"totaling \$([\d,]+)", t)
    n = re.search(r"Actions WITH capital deployed: (\d+)", t)
    if not m:
        return None
    alpha = float(m.group(1).replace(",", ""))
    deployed = float(d.group(1).replace(",", "")) if d else None
    if not math.isfinite(alpha):
        return None
    try:
        count = int(n.group(1)) if n else None
    except ValueError:
        count = None
    return {"alpha": alpha,
            "deployed": deployed if deployed is not None and math.isfinite(deployed) else None,
            "n": count}


def finite_in_range(value, low, high):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and low <= value <= high and math.isfinite(value))


def confidence_advisory(stated, map_path, context=None, today=None):
    """Validate a historical mapping and its declared applicability, never impute.

    Expected context keys are win_key, horizon (days), cohort, method. Qualified
    maps retain the producer's generated/source/n/bins fields and explicitly add
    cohort, method and nonempty limitations. Existing unqualified maps are not
    rewritten. Metadata matching is not independent validation of calibration.
    """
    result = {"status": "unavailable", "reason": "stated_confidence_unavailable",
              "stated": None, "calibrated": None,
              "scope": "historical target-event mapping; not analysis-correctness probability"}
    if stated is None:
        return result
    if not finite_in_range(stated, 0, 100):
        result["reason"] = "invalid_stated_confidence"
        return result
    result["stated"] = stated
    context = context or {}
    keys = ("win_key", "cohort", "method")
    if (not isinstance(context, dict)
            or any(not isinstance(context.get(key), str) or not context[key].strip() for key in keys)
            or type(context.get("horizon")) is not int or context["horizon"] <= 0):
        result["reason"] = "applicability_context_unavailable"
        return result
    try:
        cm = json.loads(map_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        result["reason"] = "map_absent"
        return result
    except (OSError, UnicodeError, ValueError):
        result["reason"] = "map_unreadable_or_malformed"
        return result
    if not isinstance(cm, dict):
        result["reason"] = "invalid_map_metadata"
        return result
    try:
        generated = date.fromisoformat(cm["generated"])
    except (ValueError, KeyError, TypeError):
        result["reason"] = "map_date_unavailable"
        return result
    age = ((today or date.today()) - generated).days
    result.update({"map_generated": generated.isoformat(), "map_age_days": age})
    if age < 0 or age >= MAX_MAP_AGE_DAYS:
        result["reason"] = "map_future_dated" if age < 0 else "map_stale"
        return result
    if (any(not isinstance(cm.get(key), str) or not cm[key].strip() for key in (*keys, "source"))
            or type(cm.get("horizon")) is not int or cm["horizon"] <= 0
            or type(cm.get("n")) is not int or cm["n"] <= 0
            or not isinstance(cm.get("limitations"), list) or not cm["limitations"]
            or any(not isinstance(item, str) or not item.strip() for item in cm["limitations"])):
        result["reason"] = "map_qualification_unavailable"
        return result
    if any(cm[key] != context[key] for key in (*keys, "horizon")):
        result["reason"] = "map_not_applicable"
        return result
    bins = cm.get("bins")
    if not isinstance(bins, list) or not bins:
        result["reason"] = "invalid_map_bins"
        return result
    for b in bins:
        if (not isinstance(b, dict)
                or not finite_in_range(b.get("lo"), 0, 100)
                or not finite_in_range(b.get("hi"), 0, 100) or b["lo"] > b["hi"]
                or type(b.get("n")) is not int or not 0 < b["n"] <= cm["n"]
                or not finite_in_range(b.get("realized"), 0, 1)
                or not finite_in_range(b.get("calibrated"), 0, 1)):
            result["reason"] = "invalid_map_bins"
            return result
    ordered = sorted(bins, key=lambda b: b["lo"])
    if (sum(b["n"] for b in bins) != cm["n"]
            or any(left["hi"] >= right["lo"] for left, right in zip(ordered, ordered[1:]))):
        result["reason"] = "inconsistent_map_bins"
        return result
    matches = [b for b in bins if b["lo"] <= stated <= b["hi"]]
    if len(matches) != 1:
        result["reason"] = "no_supported_bin"
        return result
    b = matches[0]
    result.update({"status": "available", "reason": None, "calibrated": b["calibrated"],
                   "target_event": cm["win_key"], "horizon_days": cm["horizon"],
                   "cohort": cm["cohort"], "method": cm["method"], "source": cm["source"],
                   "map_n": cm["n"], "bin_n": b["n"], "bin": {"lo": b["lo"], "hi": b["hi"]},
                   "limitations": cm["limitations"],
                   "validation_scope": "metadata and caller context matched; calibration not independently validated"})
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stated", type=float, help="optional stated confidence for calibration join")
    ap.add_argument("--target-event", help="expected map win_key; required for a confidence advisory")
    ap.add_argument("--horizon-days", type=int, help="expected mapping outcome horizon in days")
    ap.add_argument("--cohort", help="expected calibration reference-class identifier")
    ap.add_argument("--calibration-method", help="expected documented calibration method identifier")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    a = parse_alpha()
    out = {"date": date.today().isoformat(), "source": str(SRC.relative_to(ROOT))}
    if a is None:
        out["attribution_status"] = "unavailable"
        out["advisory"] = "Historical decision-attribution source absent, unreadable, or incomplete."
    else:
        sign = "UNDERPERFORMED" if a["alpha"] < 0 else "OUTPERFORMED" if a["alpha"] > 0 else "MATCHED"
        out.update(a)
        missing = [key for key in ("n", "deployed") if a[key] is None]
        out["attribution_status"] = "partial" if missing else "available"
        out["attribution_missing_fields"] = missing
        out["attribution_freshness"] = "unavailable; current date is observation time, not source as-of"
        out["sign"] = sign
        count = f"{a['n']} priced actions" if a["n"] is not None else "priced-action count unavailable"
        deployed = f"${a['deployed']:,.0f} deployed" if a["deployed"] is not None else "deployed amount unavailable"
        out["advisory"] = (
            f"ADVISORY (not binding): historical {count} ({deployed}); ticker "
            f"selection {sign} SPY by ${abs(a['alpha']):,.2f} at 21d. "
            "This does not establish current account quantities. Doctrine, R/R "
            "hurdles, sizing and ratings retain their existing owners.")

    cc = ROOT / "wiki/maintenance/calibration/confidence-map.json"
    out["confidence_advisory"] = confidence_advisory(
        args.stated, cc, {"win_key": args.target_event, "horizon": args.horizon_days,
                          "cohort": args.cohort, "method": args.calibration_method})
    out["calibrated_confidence"] = out["confidence_advisory"]["calibrated"]

    print(json.dumps(out, indent=1, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
