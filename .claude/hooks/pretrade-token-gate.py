#!/usr/bin/env python3
"""
PreToolUse token-gate hook for the Osanwe action staircase (TENFOLD T11).

Registered ONLY on the three Robinhood EQUITY-order tools. It is the SECOND
stair: even if the permission-layer deny on those tools is ever lifted, no
equity order executes unless ALL hold:
  1. the LATEST genuine user prompt contains 'EXECUTE ORDER <order_id>'
     (injected tool-result / assistant / file content never counts -- A8),
  2. a fresh HMAC-signed gate pass exists for that order_id (issued by
     tools/pretrade_gate.py only on a clean PASS -- defeats A1 forge, A2
     ceiling-breach, A6 direct-call-without-gate),
  3. the pass is within TTL (A5-stale) and not already consumed (A5-replay;
     atomic O_EXCL claim also defeats the race),
  4. the order the tool is about to place hashes IDENTICALLY to the passed
     order (A7 substitution / TOCTOU).
Option-order and scan/watchlist-mutator tools are BLOCKED outright here as
defense-in-depth (they also remain in permissions.deny -- A3).

Block convention: exit 2 + stderr reason (Claude Code PreToolUse). Any error,
missing input, or unexpected shape -> BLOCK (fail-closed). Exit 0 = allow.

MAIN-LOOP-INSTALLED (never delegated): this file is security-load-bearing and is
guarded by the X26 config-write guard.
"""
import hmac
import json
import sys

sys.path.insert(0, r"/path/to/vault\tools")
import pretrade_lib as L  # noqa: E402


def block(reason):
    sys.stderr.write("pretrade-token-gate: BLOCKED -- %s\n" % reason)
    sys.exit(2)


def allow(note):
    sys.stdout.write("pretrade-token-gate: allow -- %s\n" % note)
    sys.exit(0)


def main():
    raw = sys.stdin.read()
    try:
        d = json.loads(raw)
    except Exception as e:
        block("unparseable hook payload (fail-closed): %s" % e)

    tool = d.get("tool_name", "")

    # Defense-in-depth: this hook NEVER authorizes options or mutators.
    if tool in L.OPTION_ORDER_TOOLS:
        block("option-order tools are denied and not authorizable via the equity staircase (%s)" % tool)
    if tool in L.MUTATOR_TOOLS:
        block("scan/watchlist mutator tools are denied (%s)" % tool)
    if tool not in L.EQUITY_ORDER_TOOLS:
        # Widened matcher (2026-08-10): the hook now sees EVERY robinhood tool.
        # Known read tools flow (exit 0). ANYTHING ELSE is an unknown name --
        # server-side surface growth -- and fails CLOSED (redteam H3: the old
        # fall-through left new mutators one permission-prompt click from live).
        if tool in L.READ_TOOLS:
            sys.exit(0)
        if tool.startswith("mcp__robinhood-trading__"):
            block("unknown robinhood tool %r -- not in the registry read set or any "
                  "order/mutator list (surface grew?); update .agents/mcp/servers.json "
                  "+ pretrade_lib.READ_TOOLS together after review" % tool)
        # Non-robinhood tool name: not our registration surface.
        sys.exit(0)

    tool_input = d.get("tool_input") or {}
    transcript = d.get("transcript_path")

    # (1) order-bound human confirm phrase from the LATEST GENUINE user prompt.
    oid = L.confirm_order_id(transcript)
    if not oid:
        block("no 'EXECUTE ORDER <order_id>' in the latest genuine user prompt "
              "(injected/tool-result/assistant content does not count)")

    # (2) signed gate pass must exist and verify for exactly that order_id.
    pass_path = L.PASS_DIR / ("gate-pass-%s.json" % oid)
    if not pass_path.exists():
        block("no gate pass for order_id %s (run tools/pretrade_gate.py first)" % oid)
    try:
        pass_obj = json.loads(pass_path.read_text(encoding="utf-8"))
    except Exception as e:
        block("gate pass unreadable (fail-closed): %s" % e)
    if pass_obj.get("gate_result") != "PASS":
        block("gate pass for %s is not a PASS" % oid)
    if pass_obj.get("order_id") != oid:
        block("gate pass order_id mismatch")
    if not L.verify_pass_signature(pass_obj):
        block("gate pass HMAC signature invalid (forged or tampered)")

    # (3) freshness (TTL) + anti-replay.
    passed = L.parse_iso(pass_obj.get("passed_utc", ""))
    if passed is None:
        block("gate pass timestamp invalid")
    age = (L.now_utc() - passed).total_seconds()
    ttl = int(pass_obj.get("ttl_sec", 0))
    if age > ttl:
        block("gate pass expired (%.0fs old, ttl %ds) -- re-run the gate" % (age, ttl))
    if age < -300:
        block("gate pass timestamped in the future")
    if L.is_consumed(oid):
        block("gate pass for %s already consumed (replay)" % oid)

    # (4) the order about to EXECUTE must be byte-identical (by canonical hash)
    #     to the order the gate PASSED -- blocks stage-A-execute-B substitution.
    try:
        canon = L.normalize_tool_input(tool_input)
        exec_hash = L.order_hash(canon)
    except Exception as e:
        block("cannot normalize/hash tool_input (fail-closed): %s" % e)
    if not hmac.compare_digest(exec_hash, str(pass_obj.get("order_hash", ""))):
        block("order substitution: tool_input hash != passed order hash")

    # Consume LAST: atomically claim the token, then allow. A lost race blocks.
    if not L.consume_atomic(oid):
        block("token consume race lost for %s (concurrent execution)" % oid)

    allow("order %s authorized (signed PASS + fresh order-bound confirm + hash match; token consumed)" % oid)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # absolute fail-closed backstop
        sys.stderr.write("pretrade-token-gate: BLOCKED -- unexpected error (fail-closed): %s\n" % e)
        sys.exit(2)
