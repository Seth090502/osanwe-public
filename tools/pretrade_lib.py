#!/usr/bin/env python3
"""
Osanwe pre-trade action-staircase shared library (TENFOLD T11).

Single source of truth for BOTH the pre-trade gate (tools/pretrade_gate.py) and
the PreToolUse token hook (.claude/hooks/pretrade-token-gate.py). The gate that
ISSUES a signed pass and the hook that VERIFIES it import the same canonical-hash,
HMAC, ceiling, and schema logic here so they can never disagree on what an order
"is" -- a divergence would be a bypass.

FAIL-CLOSED contract: every validator returns (ok: bool, reason: str). Callers
treat any exception, missing input, or unrecognized shape as BLOCK. Nothing in
this module places an order or touches a brokerage endpoint; it only decides
PASS vs BLOCK and signs/verifies a local artifact.

Hardened after the T11 red-team round 1:
  - non-finite floats (NaN/Infinity) are rejected everywhere (round-1 A4);
  - symbol/thesis are type- and format-validated (round-1 A4 low-sev).
Concentration sizing off a TRUSTED book price (never an order-carried number)
and thesis authority live in the gate (round-1 A2).

ASCII-only (Osanwe Pattern 22). No third-party deps (stdlib only).
"""
import hashlib
import hmac
import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path

# --- Locations (all under the gitignored .claude/state/ tree) ---
# STATE_DIR is overridable via OSANWE_PRETRADE_STATE_DIR so tests / the red-team
# run hermetically (isolated key + passes + consumed ledger). Production leaves it
# unset -> the real gitignored path. Resolved at import: gate and hook subprocesses
# inherit the same env, so they always agree on the key and ledger.
VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", r"/path/to/vault"))  # D5 parameterization (2026-08-10)
STATE_DIR = Path(os.environ.get("OSANWE_PRETRADE_STATE_DIR")
                 or (VAULT_ROOT / ".claude" / "state" / "pretrade"))
KEY_PATH = STATE_DIR / "hmac.key"           # 32 random bytes, 0600, gitignored
CONSUMED_DIR = STATE_DIR / "consumed"       # one O_EXCL marker file per consumed order_id
PASS_DIR = STATE_DIR / "passes"             # gate-pass-<order_id>.json artifacts
SLEEP_GATE_SENTINEL = STATE_DIR / "sleep-gate-active"  # presence => defer all BUYs

# --- MCP tool taxonomy (mirrors .claude/settings.json permissions.deny) ---
EQUITY_ORDER_TOOLS = frozenset({
    "mcp__robinhood-trading__place_equity_order",
    "mcp__robinhood-trading__cancel_equity_order",
    "mcp__robinhood-trading__review_equity_order",
})
OPTION_ORDER_TOOLS = frozenset({
    "mcp__robinhood-trading__place_option_order",
    "mcp__robinhood-trading__cancel_option_order",
    "mcp__robinhood-trading__review_option_order",
})
# Registry-mirrored READ allowlist (redteam H3, 2026-08-10): the pretrade hook
# default-BLOCKS any mcp__robinhood-trading__* name not in READ_TOOLS or
# EQUITY_ORDER_TOOLS -- a NEW server-side tool (surface growth) fails closed
# instead of falling through to a permission prompt. Source of truth:
# .agents/mcp/servers.json read_tools. The two no longer agree: the registry
# lists 51 live read tools and this allowlist hardcodes 34, so 17 live READ
# tools fail closed. That is a capability limit, not a safety hole, and
# widening it is an open decision (_audit/FIX-PLAN.md 2.6) -- not a drift to
# silently repair. Verified 2026-09-21.
READ_TOOLS = frozenset("mcp__robinhood-trading__" + n for n in (
    "get_accounts", "get_earnings_calendar", "get_earnings_results",
    "get_equity_fundamentals", "get_equity_historicals", "get_equity_orders",
    "get_equity_positions", "get_equity_price_book", "get_equity_quotes",
    "get_equity_tax_lots", "get_equity_technical_indicators", "get_equity_tradability",
    "get_financials", "get_index_historicals", "get_index_quotes", "get_indexes",
    "get_limited_margin_upgrade_info", "get_option_chains", "get_option_historicals",
    "get_option_instruments", "get_option_level_upgrade_info", "get_option_orders",
    "get_option_positions", "get_option_quotes", "get_option_watchlist",
    "get_pnl_trade_history", "get_popular_watchlists", "get_portfolio",
    "get_realized_pnl", "get_scanner_filter_specs", "get_scans",
    "get_watchlist_items", "get_watchlists", "search",
))

MUTATOR_TOOLS = frozenset({
    # exercise pair added 2026-08-10 (cross-harness migration S4): live surface
    # exposes them; they were in NO deny/allow list (phase1 MCP audit finding).
    "mcp__robinhood-trading__exercise_option",
    "mcp__robinhood-trading__cancel_option_exercise",
    "mcp__robinhood-trading__add_option_to_watchlist",
    "mcp__robinhood-trading__add_to_watchlist",
    "mcp__robinhood-trading__create_scan",
    "mcp__robinhood-trading__create_watchlist",
    "mcp__robinhood-trading__follow_watchlist",
    "mcp__robinhood-trading__remove_from_watchlist",
    "mcp__robinhood-trading__remove_option_from_watchlist",
    "mcp__robinhood-trading__run_scan",
    "mcp__robinhood-trading__unfollow_watchlist",
    "mcp__robinhood-trading__update_scan_config",
    "mcp__robinhood-trading__update_scan_filters",
    "mcp__robinhood-trading__update_watchlist",
})

# --- Doctrine ceilings (machine-readable; T11 spec) ---
# Concentration is THESIS-level exposure as a share of total portfolio value.
# theme-alpha rides the interim-50 cap (phase-in to 60 on ~2026-09-08, then 70 red);
# the generic 50 red line covers that interim value today. Red is INCLUSIVE (>=):
# landing exactly ON the red line is a breach (fail-closed at the boundary).
THESIS_AMBER_PCT = 40.0
THESIS_RED_PCT = 50.0
SINGLE_NAME_AMBER_PCT = 30.0
SINGLE_NAME_RED_PCT = 35.0
RR_BUY_HURDLE = 3.0            # BUY orders must clear >= 3:1 reward/risk
NOTIONAL_TOLERANCE = 0.05     # declared estimated_notional must be within 5% of qty*price
SNAPSHOT_STALE_AMBER_SEC = 30 * 60      # book snapshot older than 30 min -> amber
SNAPSHOT_STALE_BLOCK_SEC = 24 * 60 * 60  # older than 24h -> BLOCK (untrustworthy book)
DEFAULT_TTL_SEC = 15 * 60      # a gate pass is valid for 15 minutes

REQUIRED_FIELDS = (
    "order_id", "created_utc", "account", "symbol", "side", "asset_class",
    "order_type", "quantity", "estimated_notional", "thesis", "risk_reward",
    "sleep_gate_ack",
)
VALID_ACCOUNTS = {"taxable", "tax_advantaged"}
VALID_SIDES = {"buy", "sell"}
VALID_ORDER_TYPES = {"market", "limit"}

ORDER_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{6,64}$")
SYMBOL_RE = re.compile(r"^[A-Z0-9.\-]{1,12}$")
# Human confirm phrase, order-bound: "EXECUTE ORDER <order_id>"
CONFIRM_RE = re.compile(r"EXECUTE ORDER\s+([A-Za-z0-9._:-]{6,64})")


def now_utc():
    return datetime.now(timezone.utc)


def parse_iso(ts):
    """Parse an ISO-8601 timestamp; return aware UTC datetime or None (fail-closed)."""
    if not isinstance(ts, str):
        return None
    try:
        s = ts.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


# --- HMAC key management ---
def load_or_create_key():
    """Return the 32-byte HMAC secret, creating it 0600 on first use.

    Kept out of git (.claude/state/ is gitignored). An attacker who cannot read
    this key cannot forge a valid pass signature (attack A1).
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if KEY_PATH.exists():
        data = KEY_PATH.read_bytes()
        if len(data) >= 32:
            return data
    key = os.urandom(32)
    # Write with restrictive perms where the OS honors them.
    fd = os.open(str(KEY_PATH), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, key)
    finally:
        os.close(fd)
    try:
        os.chmod(str(KEY_PATH), 0o600)
    except Exception:
        pass
    return key


# --- Canonical order identity (binds a pass to an exact order) ---
def _norm_num(x, places):
    """Coerce int/float/str -> rounded FINITE float; raise on anything else.

    Rejects NaN/Infinity: json.loads parses bare NaN/Infinity/-Infinity by
    default and float('nan') accepts the string form, and every fail-closed
    comparison ('> 0', '< hurdle') silently passes on NaN. (T11 red-team A4.)
    """
    if isinstance(x, bool):
        raise ValueError("bool is not a number")
    if isinstance(x, (int, float)):
        v = float(x)
    elif isinstance(x, str):
        v = float(x.strip())
    else:
        raise ValueError("not a number: %r" % (x,))
    if not math.isfinite(v):
        raise ValueError("non-finite number not allowed: %r" % (x,))
    return round(v, places)


def canonical_order(order):
    """Deterministic JSON string over the IMMUTABLE core of an order.

    Any change to account/symbol/side/asset_class/order_type/quantity/limit_price
    changes the hash, so a pass issued for order A cannot authorize order B
    (attack A7, order substitution / TOCTOU). quantity IS bound here, so the gate
    can safely size concentration off quantity (round-1 A2 fix).
    """
    lp = order.get("limit_price", None)
    core = {
        "account": str(order["account"]).strip().lower(),
        "symbol": str(order["symbol"]).strip().upper(),
        "side": str(order["side"]).strip().lower(),
        "asset_class": str(order["asset_class"]).strip().lower(),
        "order_type": str(order["order_type"]).strip().lower(),
        "quantity": _norm_num(order["quantity"], 8),
        "limit_price": (None if lp in (None, "", "null") else _norm_num(lp, 4)),
    }
    return json.dumps(core, sort_keys=True, separators=(",", ":"))


def order_hash(order):
    return hashlib.sha256(canonical_order(order).encode("utf-8")).hexdigest()


# --- Pass signing / verification ---
def _sig_payload(order_id, ohash, passed_utc, ttl_sec):
    return "%s|%s|%s|%d" % (str(order_id), str(ohash), str(passed_utc), int(ttl_sec))


def sign_pass(order_id, ohash, passed_utc, ttl_sec, key=None):
    key = key or load_or_create_key()
    msg = _sig_payload(order_id, ohash, passed_utc, ttl_sec).encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def verify_pass_signature(pass_obj, key=None):
    """Constant-time HMAC check over the pass's own fields. False on any defect."""
    try:
        key = key or load_or_create_key()
        expect = sign_pass(
            pass_obj["order_id"], pass_obj["order_hash"],
            pass_obj["passed_utc"], pass_obj["ttl_sec"], key=key,
        )
        return hmac.compare_digest(expect, str(pass_obj.get("hmac", "")))
    except Exception:
        return False


# --- Tool-input normalization (RH tool_input -> canonical order fields) ---
def _first(d, *keys):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None


# Every tool_input key must belong to a known alias group. An UNKNOWN key is an
# execution-affecting parameter the gate never evaluated (stop_price, time_in_force,
# extended_hours, trigger, ...) and is rejected fail-closed -- otherwise it rides an
# approved token unbound (T11 red-team round-2 A7 projection gap). Extending this set
# requires extending the staged-order schema + gate + order_hash to bind the new field.
TOOL_INPUT_ALIAS_GROUPS = {
    "symbol": ("symbol", "ticker", "instrument", "instrument_symbol"),
    "side": ("side", "direction"),
    "quantity": ("quantity", "shares", "qty"),
    "order_type": ("order_type", "type"),
    "account": ("account", "account_number", "account_id", "account_type"),
    "limit_price": ("limit_price", "price", "limit"),
}
KNOWN_TOOL_INPUT_KEYS = frozenset(k for grp in TOOL_INPUT_ALIAS_GROUPS.values() for k in grp)


def normalize_tool_input(tool_input):
    """Map a Robinhood equity-order tool_input into canonical order fields.

    FAIL-CLOSED on anything the gate did not vet:
      - any key outside the known alias groups (an unbound, execution-affecting
        parameter riding an approved token -- round-2 A7 projection gap);
      - conflicting aliases for one field (symbol=AAA + ticker=BBB -- round-2 A7);
      - missing essentials.
    Raises on any of these (caller treats as BLOCK).
    """
    if not isinstance(tool_input, dict):
        raise ValueError("tool_input is not an object")
    unknown = sorted(str(k) for k in tool_input.keys() if k not in KNOWN_TOOL_INPUT_KEYS)
    if unknown:
        raise ValueError("unvetted order parameter(s) not evaluated by the gate: %s" % ",".join(unknown))
    for field, aliases in TOOL_INPUT_ALIAS_GROUPS.items():
        present = [tool_input[k] for k in aliases if k in tool_input and tool_input[k] not in (None, "")]
        if len({str(v).strip().lower() for v in present}) > 1:
            raise ValueError("conflicting aliases for %s: %s" % (field, [str(v) for v in present]))
    symbol = _first(tool_input, *TOOL_INPUT_ALIAS_GROUPS["symbol"])
    side = _first(tool_input, *TOOL_INPUT_ALIAS_GROUPS["side"])
    qty = _first(tool_input, *TOOL_INPUT_ALIAS_GROUPS["quantity"])
    otype = _first(tool_input, *TOOL_INPUT_ALIAS_GROUPS["order_type"])
    account = _first(tool_input, *TOOL_INPUT_ALIAS_GROUPS["account"])
    lp = _first(tool_input, *TOOL_INPUT_ALIAS_GROUPS["limit_price"])
    if symbol is None or side is None or qty is None or otype is None:
        raise ValueError("tool_input missing required order fields")
    return {
        "account": account if account is not None else "taxable",
        "symbol": symbol,
        "side": side,
        "asset_class": "equity",
        "order_type": otype,
        "quantity": qty,
        "limit_price": lp,
    }


# --- Staged-order schema validation ---
def validate_schema(order):
    """Return (ok, reason). Fail-closed: any missing/mistyped field -> not ok."""
    if not isinstance(order, dict):
        return False, "staged order is not a JSON object"
    for f in REQUIRED_FIELDS:
        if f not in order:
            return False, "missing required field: %s" % f
    oid = order["order_id"]
    if not (isinstance(oid, str) and ORDER_ID_RE.match(oid)):
        return False, "order_id must match %s" % ORDER_ID_RE.pattern
    if parse_iso(order["created_utc"]) is None:
        return False, "created_utc is not a valid ISO-8601 timestamp"
    if str(order["account"]).strip().lower() not in VALID_ACCOUNTS:
        return False, "account must be one of %s" % sorted(VALID_ACCOUNTS)
    # symbol: must be a clean ticker string (rejects object/array/huge -- round-1 A4).
    if not isinstance(order["symbol"], str):
        return False, "symbol must be a string"
    if not SYMBOL_RE.match(order["symbol"].strip().upper()):
        return False, "symbol must match %s" % SYMBOL_RE.pattern
    if str(order["side"]).strip().lower() not in VALID_SIDES:
        return False, "side must be one of %s" % sorted(VALID_SIDES)
    # asset_class MUST be equity: options are not eligible via this staircase (A3).
    if str(order["asset_class"]).strip().lower() != "equity":
        return False, "asset_class must be 'equity' (options remain denied)"
    if str(order["order_type"]).strip().lower() not in VALID_ORDER_TYPES:
        return False, "order_type must be one of %s" % sorted(VALID_ORDER_TYPES)
    # thesis: a bounded string (rejects array/object -- round-1 A4).
    if not isinstance(order["thesis"], str) or not (1 <= len(order["thesis"].strip()) <= 40):
        return False, "thesis must be a 1-40 char string"
    try:
        q = _norm_num(order["quantity"], 8)
        if q <= 0:
            return False, "quantity must be > 0"
    except Exception:
        return False, "quantity is not a positive finite number"
    try:
        notional = _norm_num(order["estimated_notional"], 2)
        if notional <= 0:
            return False, "estimated_notional must be > 0"
    except Exception:
        return False, "estimated_notional is not a positive finite number"
    if str(order["order_type"]).strip().lower() == "limit":
        lp = order.get("limit_price", None)
        try:
            if lp is None or _norm_num(lp, 4) <= 0:
                return False, "limit order requires a positive limit_price"
        except Exception:
            return False, "limit_price is not a positive finite number"
    try:
        rr = _norm_num(order["risk_reward"], 4)
        if rr < 0:
            return False, "risk_reward must be >= 0"
    except Exception:
        return False, "risk_reward is not a finite number"
    if not isinstance(order["sleep_gate_ack"], bool):
        return False, "sleep_gate_ack must be a boolean"
    return True, "schema ok"


# --- Consumed-token ledger (anti-replay, atomic) ---
def is_consumed(order_id):
    return (CONSUMED_DIR / order_id).exists()


def consume_atomic(order_id):
    """Atomically claim a token. Returns True on first claim, False if already
    consumed or racing (O_EXCL). This is the anti-replay / anti-race primitive (A5).
    """
    CONSUMED_DIR.mkdir(parents=True, exist_ok=True)
    marker = CONSUMED_DIR / order_id
    try:
        fd = os.open(str(marker), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return False
    except OSError:
        return False
    try:
        os.write(fd, now_utc().isoformat().encode("utf-8"))
    finally:
        os.close(fd)
    return True


# --- Transcript parsing (A8: only a genuine user text turn authorizes) ---
def latest_user_text(transcript_path):
    """Return the text of the MOST RECENT genuine user prompt, or None.

    A genuine user turn is type=='user', role=='user', and content that is a
    string OR a list containing a 'text' block and NO 'tool_result' block.
    Tool results (web fetches, file reads, MCP output) arrive as user-role
    'tool_result' lists and are injected content -- they NEVER authorize.
    Assistant turns and meta turns are ignored. Fail-closed: any error -> None.
    """
    try:
        p = Path(transcript_path)
        if not p.exists():
            return None
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return None
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("type") != "user":
            continue
        if d.get("isMeta") is True:
            continue
        # tool-result carriers expose a toolUseResult sibling key in CC transcripts
        if "toolUseResult" in d:
            continue
        msg = d.get("message")
        if not isinstance(msg, dict) or msg.get("role") != "user":
            continue
        content = msg.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            block_types = {b.get("type") for b in content if isinstance(b, dict)}
            if "tool_result" in block_types:
                continue  # injected content, not a genuine prompt
            texts = [b.get("text", "") for b in content
                     if isinstance(b, dict) and b.get("type") == "text"]
            if texts:
                return "\n".join(texts)
        # unknown shape -> skip (fail-closed)
    return None


def confirm_order_id(transcript_path):
    """Extract the order_id the human authorized in their latest prompt, or None."""
    text = latest_user_text(transcript_path)
    if not text:
        return None
    m = CONFIRM_RE.search(text)
    return m.group(1) if m else None
