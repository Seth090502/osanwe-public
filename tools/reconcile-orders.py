#!/usr/bin/env python3
"""reconcile-orders.py -- trade-vs-decision reconciliation (/retro Phase D.5; vNEXT 2026-06-09).

Deterministic, read-only. A fill with no decision record is, by definition, the
FOMO pattern the vault architecture exists to catch -- this catches it mechanically.

Input: a fills-cache JSON written IN-SESSION by /retro via
mcp__robinhood-trading__get_equity_orders (this offline script cannot reach
session-scoped MCP). Canonical cache path (strategist rider R2a -- NOT
.claude/state/, which is path-guarded for skill writes):

    wiki/research/test-tmp/fills-cache-<YYYY-MM-DD>.json

Expected cache schema:
    {
      "fetched_at": "2026-06-09T...",
      "orders": [
        {"ticker": "ORBC-DEMO", "side": "buy", "quantity": 1.0, "price": 38.50,
         "filled_at": "2026-07-15T10:00:00Z", "state": "filled"}
      ]
    }

Matching rule: a filled order is MATCHED if EITHER
  (a) Calendar/decisions/decision-log.md contains a row mentioning the ticker
      dated within +/-WINDOW days of the fill date, OR
  (b) a wiki/investing/analyses/<ticker>-analysis-*.md exists whose filename
      date is within +/-WINDOW days and whose body contains "TRADING DECISION".

Unmatched fills are emitted as flags. No file writes -- pure read + report.

CLI:
  python tools/reconcile-orders.py --fills PATH [--window-days 3] [--json]
"""

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent
DECISION_LOG = VAULT_ROOT / "Calendar" / "decisions" / "decision-log.md"
ANALYSES_DIR = VAULT_ROOT / "wiki" / "investing" / "analyses"
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def load_fills(fills_path):
    data = json.loads(fills_path.read_text(encoding="utf-8"))
    fills = []
    for order in data.get("orders", []):
        if order.get("state") != "filled" or not order.get("filled_at"):
            continue
        try:
            fill_date = datetime.fromisoformat(
                order["filled_at"].replace("Z", "+00:00")).date()
        except ValueError:
            continue
        fills.append({
            "ticker": str(order.get("ticker", "")).upper(),
            "side": order.get("side", "?"),
            "quantity": order.get("quantity"),
            "price": order.get("price"),
            "fill_date": fill_date,
        })
    return fills


def search_decision_log(ticker, fill_date, window):
    """True if any decision-log line mentions the ticker and carries an in-window date."""
    if not DECISION_LOG.exists():
        return False
    pattern = re.compile(rf"\b{re.escape(ticker)}\b")
    for line in DECISION_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        if not pattern.search(line):
            continue
        for ds in DATE_RE.findall(line):
            try:
                d = date.fromisoformat(ds)
            except ValueError:
                continue
            if abs((d - fill_date).days) <= window:
                return True
    return False


def search_analyses(ticker, fill_date, window):
    """True if a <ticker>-analysis-* file dated in-window contains TRADING DECISION."""
    if not ANALYSES_DIR.exists():
        return False
    for path in ANALYSES_DIR.glob(f"{ticker.lower()}-analysis-*.md"):
        m = DATE_RE.search(path.name)
        if not m:
            continue
        try:
            d = date.fromisoformat(m.group(1))
        except ValueError:
            continue
        if abs((d - fill_date).days) <= window:
            try:
                if "TRADING DECISION" in path.read_text(encoding="utf-8", errors="replace"):
                    return True
            except OSError:
                continue
    return False


def reconcile(fills, window):
    unmatched = []
    for fill in fills:
        matched = (search_decision_log(fill["ticker"], fill["fill_date"], window)
                   or search_analyses(fill["ticker"], fill["fill_date"], window))
        if not matched:
            unmatched.append(fill)
    return unmatched


def main():
    ap = argparse.ArgumentParser(description="fill-vs-decision reconciliation")
    ap.add_argument("--fills", type=Path, required=True,
                    help="fills-cache JSON (wiki/research/test-tmp/fills-cache-<date>.json)")
    ap.add_argument("--window-days", type=int, default=3)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not args.fills.exists():
        print(f"ERROR: fills cache not found: {args.fills}", file=sys.stderr)
        return 2
    fills = load_fills(args.fills)
    unmatched = reconcile(fills, args.window_days)

    if args.json:
        print(json.dumps({
            "fills_total": len(fills),
            "unmatched_count": len(unmatched),
            "window_days": args.window_days,
            "unmatched": [
                {**f, "fill_date": f["fill_date"].isoformat()} for f in unmatched
            ],
        }, indent=2))
    else:
        print(f"fills={len(fills)} unmatched={len(unmatched)} window=+/-{args.window_days}d")
        for f in unmatched:
            print(f"UNMATCHED FILL: {f['ticker']} {f['side']} {f['quantity']} @ "
                  f"${f['price']} on {f['fill_date']} -- no decision record within "
                  f"+/-{args.window_days}d (FOMO-pattern flag)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
