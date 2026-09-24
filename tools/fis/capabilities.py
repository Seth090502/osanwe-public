"""Bind financial needs to explicitly observed read tools; never authorize accounts.

This pure adapter accepts the current host's tool inventory. Saved observations
are historical metadata and cannot establish current access or successful reads.
Tool arguments and response semantics must come from the selected live schema.
"""
from __future__ import annotations

import argparse
import json
import re

SCHEMA = "osanwe.financial-capabilities/1"
PREFIXES = ("mcp__codex_apps__robinhood_", "mcp__robinhood-trading__")
READS = {
    "accounts": "get_accounts",
    "account_totals": "get_portfolio",
    "equity_positions": "get_equity_positions",
    "option_positions": "get_option_positions",
    "crypto_positions": "get_crypto_positions",
    "tax_lots": "get_equity_tax_lots",
    "equity_quotes": "get_equity_quotes",
    "equity_history": "get_equity_historicals",
    "crypto_quotes": "get_crypto_quotes",
    "crypto_instruments": "get_currency_pairs",
    "fundamentals": "get_equity_fundamentals",
    "reported_financials": "get_financials",
    "filing_index": "get_sec_filing_index",
    "filing_text": "get_sec_filing",
    "filing_facts": "get_sec_filing_facts",
    "filing_concepts": "get_sec_filing_facts_catalog",
    "news": "get_equity_news",
    "earnings_calendar": "get_earnings_calendar",
    "earnings_results": "get_earnings_results",
    "option_chains": "get_option_chains",
    "option_instruments": "get_option_instruments",
    "option_quotes": "get_option_quotes",
    "option_history": "get_option_historicals",
    "index_quotes": "get_index_quotes",
    "index_history": "get_index_historicals",
    "screening_fields": "get_scanner_filter_specs",
    "screening_data": "get_scanner_datapoints",
    "screening_preview": "preview_scan",
    "realized_pnl": "get_realized_pnl",
    "trade_history": "get_pnl_trade_history",
}
ACCOUNT_NEEDS = {"accounts", "account_totals", "equity_positions", "option_positions",
                 "crypto_positions", "tax_lots", "realized_pnl", "trade_history"}
NAME = re.compile(r"[A-Za-z0-9_:-]{1,180}\Z")


def bind(inventory, *, required=None, selected=None):
    """Return schema bindings only, without account identifiers or tool responses.

    Ambiguous connectors require explicit selection from observed candidates.
    Unknown namespaces cannot acquire authority by copying a familiar suffix.
    """
    if not isinstance(inventory, list) or len(inventory) > 2000:
        raise ValueError("bounded current tool-name list required")
    if any(not isinstance(n, str) or not NAME.fullmatch(n) for n in inventory):
        raise ValueError("inventory accepts tool names only, never responses or account data")
    if len(inventory) != len(set(inventory)):
        raise ValueError("duplicate tool inventory entry")
    required = list(READS) if required is None else required
    if not isinstance(required, list) or any(n not in READS for n in required):
        raise ValueError("unknown financial capability")
    if len(required) != len(set(required)):
        raise ValueError("duplicate required capability")
    selected = {} if selected is None else selected
    if not isinstance(selected, dict) or not set(selected) <= set(required):
        raise ValueError("selection must address required capabilities")
    result = []
    for capability in required:
        names = sorted(p + READS[capability] for p in PREFIXES if p + READS[capability] in inventory)
        chosen = selected.get(capability)
        if chosen is not None and chosen not in names:
            raise ValueError("selected tool is not an observed candidate")
        if chosen is None and len(names) == 1:
            chosen = names[0]
        result.append({"capability": capability, "candidates": names, "tool": chosen,
                       "state": "schema_available" if chosen else "ambiguous" if names else "unavailable",
                       "account_scope_required": capability in ACCOUNT_NEEDS,
                       "live_verified": False, "arguments_from": "current selected tool schema"})
    return {"schema": SCHEMA, "bindings": result, "scope": "tool discovery only",
            "authorizes_account_access": False, "authorizes_execution": False,
            "finances_household_access": "requires separate current host capability",
            "data_rendering": "requires separate current host capability"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", help="JSON array of tool names observed in the current session")
    parser.add_argument("--require", nargs="+", choices=sorted(READS))
    args = parser.parse_args()
    try:
        with open(args.inventory, encoding="utf-8") as source:
            raw = source.read(400001)
        if len(raw) > 400000:
            raise ValueError("inventory exceeds limit")
        print(json.dumps(bind(json.loads(raw), required=args.require), sort_keys=True))
        return 0
    except (ValueError, TypeError, OSError):
        print(json.dumps({"schema": SCHEMA, "state": "refused", "reason": "invalid tool inventory"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
