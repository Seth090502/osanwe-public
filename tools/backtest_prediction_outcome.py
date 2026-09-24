"""Child-process outcome helper for backtest-prediction.py (runs under the
interpreter that HAS yfinance). Loads the hyphen-named parent by path and
prints exactly one JSON line with the outcome dict."""
import importlib.util
import json
import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("bp", _here / "backtest-prediction.py")
bp = importlib.util.module_from_spec(_spec)
sys.modules["bp"] = bp
# guard: executing the module runs argparse only under __main__, so this is safe
_spec.loader.exec_module(bp)


def outcome_json(ticker, t0, horizon_days):
    return json.dumps(bp._outcome_direct(ticker, t0, horizon_days))
