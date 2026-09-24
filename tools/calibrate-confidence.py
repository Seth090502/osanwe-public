#!/usr/bin/env python3
"""calibrate-confidence.py -- read a stated confidence %, return the calibrated
probability from wiki/maintenance/calibration/confidence-map.json.

The consumption half of confidence-calibrator.py: /invest Phase L (or any grader)
pipes its raw confidence through this before recording pop_est/Brier inputs.

Usage:
  python tools/calibrate-confidence.py 76            # -> {"stated":76,...}
  python tools/calibrate-confidence.py 76 --quiet    # value only (for scripts)

Exit codes: 0 ok; 3 no map / map too old (>45d) -- caller should fall back to the
raw value and note "uncalibrated". Never fails silently into a wrong number.
"""

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAP = ROOT / "wiki" / "maintenance" / "calibration" / "confidence-map.json"
MAX_AGE_DAYS = 45


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("value", type=float, help="stated confidence 0-100")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not MAP.is_file():
        if not args.quiet:
            print(json.dumps({"error": "no confidence map", "calibrated": None}))
        print("uncalibrated (no map)", file=sys.stderr)
        return 3

    d = json.loads(MAP.read_text(encoding="utf-8"))
    gen = datetime.strptime(d.get("generated", "2000-01-01"), "%Y-%m-%d").date()
    if (date.today() - gen).days > MAX_AGE_DAYS:
        if not args.quiet:
            print(json.dumps({"error": "map stale", "generated": d["generated"],
                              "calibrated": None}))
        return 3

    v = max(0.0, min(100.0, args.value))
    bin_ = None
    for b in d.get("bins", []):
        # bins are integer decades (confidence-calibrator: lo = c//10*10, hi = lo+9),
        # so "60-69" means [60, 70): a fractional 69.5 belongs to it, not to nothing.
        if b["lo"] <= v < b["hi"] + 1:
            bin_ = b
            break
    if bin_ is None:
        # 100 lands outside the last hi (e.g. bins 60-69,70-79,...,90-99): clamp to last
        bins_sorted = d.get("bins", [])
        if bins_sorted and v >= bins_sorted[-1]["lo"]:
            bin_ = bins_sorted[-1]

    out = {
        "stated": round(v, 1),
        "calibrated": bin_["calibrated"] if bin_ else None,
        "bin": f"{bin_['lo']}-{bin_['hi']}" if bin_ else None,
        "bin_n": bin_["n"] if bin_ else 0,
        "base_rate": d.get("base_rate"),
        "map_generated": d.get("generated"),
    }
    if args.quiet:
        print(out["calibrated"] if out["calibrated"] is not None else v)
    else:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
