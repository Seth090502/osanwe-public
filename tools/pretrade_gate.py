#!/usr/bin/env python3
"""
Osanwe pre-trade gate (TENFOLD T11) -- the first stair of the action staircase.

Reads a staged-order artifact (+ a book snapshot representing the LIVE book) and
returns PASS or BLOCK(reason) against machine-readable doctrine ceilings:
  - thesis concentration     40 amber / 50 red   (incl. the theme-alpha interim-50)
  - single-name              30 amber / 35 red
  - reward/risk              >= 3:1 hurdle on BUY
  - sleep-gate               defer BUYs when degraded / not rested
On PASS the gate writes an HMAC-signed pass artifact that the PreToolUse token
hook (.claude/hooks/pretrade-token-gate.py) later verifies. On BLOCK it writes
NO valid pass, so a blocked order can never satisfy the hook.

Concentration is sized off quantity x a TRUSTED book price (never an order-carried
number) and a held symbol's thesis is taken from the book, not the order's self-
label -- both hardened after T11 red-team round 1 (A2). Non-finite numbers are
rejected (round-1 A4). Red ceilings are inclusive (>=): landing ON the red line
is a breach.

This script NEVER places an order or calls a brokerage endpoint. In production the
main loop populates the book snapshot from the read-only Robinhood MCP tools
(get_equity_positions / get_portfolio / get_equity_quotes) before invoking the gate.

Usage:
  pretrade_gate.py <staged-order.json> [--book <book-snapshot.json>] [--json]
Exit: 0 = PASS, 1 = BLOCK, 2 = usage/IO error (fail-closed -> treated as BLOCK).

ASCII-only (Osanwe Pattern 22). Stdlib only.
"""
import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # D5: relocation-proof (2026-08-10)
import pretrade_lib as L  # noqa: E402


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _book_from(order, book_arg):
    """The book ALWAYS comes from a TRUSTED --book file (production: the read-only
    Robinhood MCP loop populates it). An order-embedded book_snapshot is attacker-
    controllable and is NEVER consulted -- there is no code path that sizes concentration
    off an order-carried book, so no forged embedded book (inflated total, fabricated cash
    line) can deflate a concentration ratio (round-4 + round-5 A4). This eliminates the
    untrusted-book surface entirely rather than trying to sanitize a hostile book.
    """
    if not book_arg:
        raise ValueError("no trusted book: pass --book from the read-only broker MCP "
                         "(an order-embedded book_snapshot is never trusted)")
    return _load_json(book_arg)


def _num(x):
    """Finite float or None (never raises)."""
    try:
        return float(L._norm_num(x, 8))
    except Exception:
        return None


def _sum_by(positions, key, match, value_key="value"):
    total = 0.0
    for p in positions:
        if str(p.get(key, "")).strip().lower() == str(match).strip().lower():
            total += float(p.get(value_key, 0) or 0)
    return total


def _validate_book(book):
    """Return (ok, reason, total, positions, prices, thesis_map). Fail-closed.

    Rejects non-finite numbers and an internally inconsistent (forged) book where
    the positions sum exceeds the declared total.
    """
    if not isinstance(book, dict):
        return False, "book snapshot is not an object", None, None, None, None
    total = book.get("total_value")
    if isinstance(total, bool) or not isinstance(total, (int, float)):
        return False, "book total_value must be a number", None, None, None, None
    total = float(total)
    if not math.isfinite(total) or total <= 0:
        return False, "book total_value must be finite and > 0", None, None, None, None
    positions = book.get("positions")
    if not isinstance(positions, list):
        return False, "book positions must be a list", None, None, None, None
    pos_sum = 0.0
    for p in positions:
        if not isinstance(p, dict):
            return False, "book position is not an object", None, None, None, None
        v = p.get("value", 0)
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)):
            return False, "book position value must be a finite number", None, None, None, None
        pos_sum += float(v)
    if pos_sum > total * 1.02:
        return False, "book inconsistent: positions sum %.2f > total_value %.2f" % (pos_sum, total), None, None, None, None
    # Symmetric lower bound: a coherent book accounts for ~all value as positions
    # (cash included). Positions covering < 90% of total means an INFLATED denominator
    # (a forged book that deflates concentration) -- round-4 A4 defense-in-depth.
    if pos_sum < total * 0.90:
        return False, "book inconsistent: positions sum %.2f accounts for < 90%% of total_value %.2f (inflated denominator?)" % (pos_sum, total), None, None, None, None
    prices = book.get("prices") or {}
    if not isinstance(prices, dict):
        return False, "book prices must be an object", None, None, None, None
    thesis_map = book.get("thesis_map") or {}
    if not isinstance(thesis_map, dict):
        return False, "book thesis_map must be an object", None, None, None, None
    return True, "ok", total, positions, prices, thesis_map


def _trusted_price(symbol, prices, positions):
    """Current price for `symbol` from the TRUSTED book (prices map, then a
    per-position price field). Never from the order. None if unavailable."""
    for k, v in prices.items():
        if str(k).strip().upper() == symbol:
            pv = _num(v)
            if pv is not None and pv > 0:
                return pv
    for p in positions:
        if str(p.get("symbol", "")).strip().upper() == symbol:
            pv = _num(p.get("price"))
            if pv is not None and pv > 0:
                return pv
    return None


def _canonical_thesis(symbol, positions, thesis_map):
    """The book's authoritative thesis for `symbol` (thesis_map, then position
    label). None if the symbol is unknown to the book."""
    for k, v in thesis_map.items():
        if str(k).strip().upper() == symbol and str(v).strip():
            return str(v).strip()
    for p in positions:
        if str(p.get("symbol", "")).strip().upper() == symbol:
            t = str(p.get("thesis", "")).strip()
            if t:
                return t
    return None


def evaluate(order, book):
    """Return (decision, reasons, warnings, metrics). decision in {PASS, BLOCK}."""
    reasons = []       # any entry => BLOCK
    warnings = []      # amber notes; do not block
    metrics = {}

    ok, why = L.validate_schema(order)
    if not ok:
        return "BLOCK", ["schema: " + why], warnings, metrics

    okb, whyb, total, positions, prices, thesis_map = _validate_book(book)
    if not okb:
        return "BLOCK", [whyb], warnings, metrics

    # Book freshness.
    as_of = L.parse_iso(book.get("as_of_utc", ""))
    if as_of is None:
        return "BLOCK", ["book snapshot as_of_utc missing/invalid (untrustworthy book)"], warnings, metrics
    age = (L.now_utc() - as_of).total_seconds()
    if age < -300:
        return "BLOCK", ["book snapshot is timestamped in the future"], warnings, metrics
    if age > L.SNAPSHOT_STALE_BLOCK_SEC:
        return "BLOCK", ["book snapshot older than 24h (%.1fh) -- refresh the live book" % (age / 3600)], warnings, metrics
    if age > L.SNAPSHOT_STALE_AMBER_SEC:
        warnings.append("book snapshot is %.0f min old (amber)" % (age / 60))

    symbol = str(order["symbol"]).strip().upper()
    side = str(order["side"]).strip().lower()
    qty = _num(order["quantity"])
    if qty is None or qty <= 0:
        return "BLOCK", ["quantity is not a positive finite number"], warnings, metrics
    rr = _num(order["risk_reward"])
    if rr is None:
        return "BLOCK", ["risk_reward is not a finite number"], warnings, metrics

    # --- Effective notional off quantity x TRUSTED book price (never order-carried) ---
    price = _trusted_price(symbol, prices, positions)
    if price is None:
        return "BLOCK", ["no trusted price for %s in book snapshot (refresh the book with a live quote)" % symbol], warnings, metrics
    effective_notional = round(qty * price, 2)
    # The DERIVED notional must itself be finite: a finite-but-huge quantity can
    # overflow quantity*price to inf, which then floors every downstream check
    # (round-2 A4). Raw-input finiteness alone is not enough.
    if not math.isfinite(effective_notional) or effective_notional <= 0:
        return "BLOCK", ["effective notional (quantity x price) is not a positive finite number (overflow?)"], warnings, metrics
    declared = _num(order.get("estimated_notional"))
    if declared is None or declared <= 0:
        return "BLOCK", ["estimated_notional is not a positive finite number"], warnings, metrics
    # The declared notional is advisory; a wide divergence from qty*price means the
    # order is lying about its size -> BLOCK (round-1 A2 notional/quantity decoupling).
    if abs(effective_notional - declared) > max(1.0, L.NOTIONAL_TOLERANCE * effective_notional):
        return "BLOCK", ["declared estimated_notional %.2f inconsistent with quantity*book-price %.2f (> %d%%)"
                         % (declared, effective_notional, int(L.NOTIONAL_TOLERANCE * 100))], warnings, metrics

    # --- Thesis authority: the BOOK decides a known symbol's thesis (round-1 A2) ---
    declared_thesis = str(order["thesis"]).strip()
    canonical_thesis = _canonical_thesis(symbol, positions, thesis_map)
    if canonical_thesis is not None and canonical_thesis.lower() != declared_thesis.lower():
        return "BLOCK", ["declared thesis '%s' != known thesis '%s' for %s (mislabel)"
                         % (declared_thesis, canonical_thesis, symbol)], warnings, metrics
    thesis = canonical_thesis or declared_thesis

    delta = effective_notional if side == "buy" else -effective_notional
    cur_symbol = _sum_by(positions, "symbol", symbol)
    cur_thesis = _sum_by(positions, "thesis", thesis)
    post_symbol = max(0.0, cur_symbol + delta)
    post_thesis = max(0.0, cur_thesis + delta)
    # Buys are funded from cash -> total portfolio value is invariant to the swap.
    post_symbol_pct = post_symbol / total * 100.0
    post_thesis_pct = post_thesis / total * 100.0
    metrics.update({
        "total_value": round(total, 2),
        "symbol": symbol, "thesis": thesis, "side": side,
        "trusted_price": round(price, 4), "quantity": qty,
        "effective_notional": effective_notional, "declared_notional": declared,
        "risk_reward": rr,
        "cur_symbol_pct": round(cur_symbol / total * 100.0, 2),
        "post_symbol_pct": round(post_symbol_pct, 2),
        "cur_thesis_pct": round(cur_thesis / total * 100.0, 2),
        "post_thesis_pct": round(post_thesis_pct, 2),
    })

    # Economic sanity: a BUY cannot exceed the whole book (funded from cash <= total);
    # a SELL cannot exceed the held position value (round-2 A4 overflow/oversell -- a
    # SELL floors post-concentration to 0, so absurd sizes otherwise slip through).
    if side == "buy" and effective_notional > total:
        reasons.append("BUY notional %.2f exceeds total portfolio value %.2f (implausible)" % (effective_notional, total))
    if side == "sell" and effective_notional > cur_symbol * 1.02 + 1.0:
        reasons.append("oversell: %s notional %.2f exceeds held position value %.2f" % (symbol, effective_notional, cur_symbol))

    # --- Sleep-gate (defer irreversible deployment when degraded / not rested) ---
    if L.SLEEP_GATE_SENTINEL.exists():
        reasons.append("sleep-gate ACTIVE (%s): irreversible orders deferred" % L.SLEEP_GATE_SENTINEL.name)
    if side == "buy" and not order.get("sleep_gate_ack", False):
        reasons.append("sleep-gate: BUY requires sleep_gate_ack=true (rested-state attestation)")

    # --- R/R hurdle (BUY only) ---
    if side == "buy" and rr < L.RR_BUY_HURDLE:
        reasons.append("reward/risk %.2f < %.1f:1 BUY hurdle" % (rr, L.RR_BUY_HURDLE))

    # --- Concentration ceilings (post-trade; red is inclusive) ---
    if post_thesis_pct >= L.THESIS_RED_PCT:
        reasons.append("thesis '%s' post-trade %.2f%% >= %.0f%% RED (concentration ceiling)"
                       % (thesis, post_thesis_pct, L.THESIS_RED_PCT))
    elif post_thesis_pct >= L.THESIS_AMBER_PCT:
        warnings.append("thesis '%s' post-trade %.2f%% in amber (%.0f-%.0f%%)"
                        % (thesis, post_thesis_pct, L.THESIS_AMBER_PCT, L.THESIS_RED_PCT))

    if post_symbol_pct >= L.SINGLE_NAME_RED_PCT:
        reasons.append("single-name %s post-trade %.2f%% >= %.0f%% RED"
                       % (symbol, post_symbol_pct, L.SINGLE_NAME_RED_PCT))
    elif post_symbol_pct >= L.SINGLE_NAME_AMBER_PCT:
        warnings.append("single-name %s post-trade %.2f%% in amber (%.0f-%.0f%%)"
                        % (symbol, post_symbol_pct, L.SINGLE_NAME_AMBER_PCT, L.SINGLE_NAME_RED_PCT))

    return ("BLOCK" if reasons else "PASS"), reasons, warnings, metrics


def issue_pass(order, ttl_sec=None):
    """Write an HMAC-signed pass artifact for a PASSED order. Returns the pass dict."""
    ttl_sec = int(ttl_sec or L.DEFAULT_TTL_SEC)
    ohash = L.order_hash(order)
    passed_utc = L.now_utc().isoformat()
    pass_obj = {
        "order_id": order["order_id"],
        "order_hash": ohash,
        "gate_result": "PASS",
        "passed_utc": passed_utc,
        "ttl_sec": ttl_sec,
        "symbol": str(order["symbol"]).strip().upper(),
        "side": str(order["side"]).strip().lower(),
    }
    pass_obj["hmac"] = L.sign_pass(order["order_id"], ohash, passed_utc, ttl_sec)
    L.PASS_DIR.mkdir(parents=True, exist_ok=True)
    out = L.PASS_DIR / ("gate-pass-%s.json" % order["order_id"])
    out.write_text(json.dumps(pass_obj, indent=2), encoding="utf-8")
    return pass_obj


def main(argv=None):
    ap = argparse.ArgumentParser(description="Osanwe pre-trade gate (T11)")
    ap.add_argument("staged_order", help="path to staged-order JSON")
    ap.add_argument("--book", help="path to TRUSTED book-snapshot JSON (production: from the read-only broker MCP)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--no-issue", action="store_true", help="evaluate only; do not write a pass")
    args = ap.parse_args(argv)

    try:
        order = _load_json(args.staged_order)
    except Exception as e:
        _emit("BLOCK", ["cannot read/parse staged order: %s" % e], [], {}, None, args.json)
        return 2
    try:
        book = _book_from(order, args.book)
    except Exception as e:
        _emit("BLOCK", ["cannot load book snapshot: %s" % e], [], {}, None, args.json)
        return 1

    try:
        decision, reasons, warnings, metrics = evaluate(order, book)
    except Exception as e:  # fail-closed on any unexpected error
        _emit("BLOCK", ["evaluation error (fail-closed): %s" % e], [], {}, None, args.json)
        return 1

    pass_obj = None
    if decision == "PASS" and not args.no_issue:
        try:
            pass_obj = issue_pass(order)
        except Exception as e:
            _emit("BLOCK", ["could not issue signed pass (fail-closed): %s" % e], warnings, metrics, None, args.json)
            return 1

    _emit(decision, reasons, warnings, metrics, pass_obj, args.json)
    return 0 if decision == "PASS" else 1


def _emit(decision, reasons, warnings, metrics, pass_obj, as_json):
    if as_json:
        print(json.dumps({
            "decision": decision, "reasons": reasons, "warnings": warnings,
            "metrics": metrics, "pass": pass_obj,
        }, indent=2))
        return
    print("PRETRADE GATE: %s" % decision)
    for w in warnings:
        print("  [amber] %s" % w)
    if decision == "BLOCK":
        for r in reasons:
            print("  [BLOCK] %s" % r)
    if metrics:
        print("  metrics: eff_notional=%.2f post_thesis=%.2f%% post_single=%.2f%% rr=%.2f"
              % (metrics.get("effective_notional", 0), metrics.get("post_thesis_pct", 0),
                 metrics.get("post_symbol_pct", 0), metrics.get("risk_reward", 0)))
    if pass_obj:
        print("  pass issued: %s (ttl %ds)" % (pass_obj["order_id"], pass_obj["ttl_sec"]))


if __name__ == "__main__":
    sys.exit(main())
