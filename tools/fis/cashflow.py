"""Exact, stateless cash-flow analysis over an explicitly normalized envelope.

This is NOT a parser for a proprietary Finances connector schema. The upstream
adapter must establish classification and source linkage, deidentify the data,
and map posting dates into the requested calendar. There is no IO here.

Input (all fields required except transaction category and transfer_group):
    schema: "osanwe.cashflow.input"; version: 1
    dataset_kind: "synthetic" | "public" | "deidentified"
    currency: three uppercase letters; currency_scale: decimal places, 0..9
    interval: {start: "YYYY-MM-DD", end: "YYYY-MM-DD"}, [start, end)
    coverage: {
        status: "complete" | "incomplete" | "unknown",
        scope: "household" | "declared_accounts", reason: nonempty text,
        excluded_scopes: [{scope: normalized token, reason: nonempty text}]
    }
    accounts: [{account_ref: "acct:<pseudonym>", coverage: status, reason: text}]
    transactions: [{
        id: unique token, account_ref: declared account_ref,
        amount_minor: signed JSON-safe integer (positive cash in),
        currency: same as envelope, currency_scale: same as envelope,
        date: "YYYY-MM-DD", status: "posted" | "pending",
        kind: "income" | "expense" | "refund" | "transfer" |
              "investment" | "unknown", source_id: nonempty identifier,
        category: optional normalized token or null (missing stays unknown),
        transfer_group: optional identifier, only for kind "transfer"
    }]

Amounts of income/refunds must be >= 0; expenses must be <= 0. An adapter must
map security sale proceeds to investment, and an unclassified deposit to unknown
or a documented transfer, not infer income from the positive sign. Signed card
purchases are expenses; both card-payment legs are transfers. This function
cannot detect an upstream lie about classification or completeness.

Every account reference uses acct:[a-z][a-z0-9_-]{0,47}. This is a pseudonym
format requirement, not proof of anonymization; do not put real identifiers in
it. All IDs, categories, reasons and declarations must already be safe to share.
No account numbers, merchant descriptions, or arbitrary extra fields are accepted.

Only posted rows dated in [start, end) enter totals. All supplied rows are
validated, including excluded rows. A transfer group is paired only when it has
exactly two supplied rows, both posted in the interval, in different declared
accounts, with equal nonzero opposite amounts. The currency/scale of every row
must agree. We never match by amount alone. Pending, outside-interval, missing,
ambiguous, and otherwise invalid counterparts leave an observable unmatched
transfer; they do not become spending or income.

All returned money is an integer in the declared minor unit. Supplied absolute
amounts must sum to <= 2**53-1, keeping all aggregates exact for JSON/JavaScript.
The saving_ratio value is a dimensionless float for display, accompanied by its
exact integer numerator and denominator; it is not annualized. It is withheld
unless declared household coverage is complete, all account coverage is complete,
there are no exclusions, pending/unknown rows or unmatched transfers, income is
positive, and period refunds do not exceed period gross expense. A deposit-only
account subset cannot establish a household saving ratio. Unknown categories
remain visible even when their expense/income kind is known.

Output schema "osanwe.cashflow.report", version 1:
    dataset_kind, currency, currency_scale, interval: normalized input metadata
    coverage: declarations, account_declarations, noncomplete_account_refs,
              accounts_without_posted_activity, and activity_note
    counts: supplied, posted_in_interval, pending_in_interval, outside_interval
    totals: observed_cash_movement_minor, income_minor, gross_expense_minor,
            refunds_minor, net_spending_minor, paired_transfer_movement_minor,
            unmatched_transfer_movement_minor, internal_transfer_volume_minor,
            investment_movement_minor, unknown_movement_minor
    accounts: per-account posted counts and the same signed component bridge
    spending_by_category: gross expense/refunds/net spending and transaction IDs
    pending: excluded count, signed movement, inflow/outflow, transaction IDs
    excluded: outside_interval (same summary) and excluded_scopes
    transfers: paired groups and unmatched rows with reasons
    reconciliation: equation, component_sum_minor, residual_minor, passed
    saving_ratio: value or null, numerator_minor, denominator_minor,
                  withheld_reasons, definition
    lineage: input transaction IDs for each included component
    source_ids: all supplied source IDs (including excluded rows)
    flags: structured coverage/classification/exclusion/transfer disclosures
    confidence: arithmetic, coverage, source_verification, qualifier
    limitations: semantic limits, including no balance or net-worth inference

Raises ValueError on malformed input. Does not mutate payload. cashflow_fixture()
returns an independent small synthetic example of the complete input contract.
"""
from __future__ import annotations

from datetime import date
import re


SCHEMA = "osanwe.cashflow.input"
REPORT_SCHEMA = "osanwe.cashflow.report"
VERSION = 1
MAX_MINOR = 2**53 - 1
MAX_TRANSACTIONS = 100_000
MAX_ACCOUNTS = 1_000
_COVERAGE = {"complete", "incomplete", "unknown"}
_KINDS = {"income", "expense", "refund", "transfer", "investment", "unknown"}
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z", re.ASCII)
_CATEGORY = re.compile(r"[a-z][a-z0-9_-]{0,63}\Z", re.ASCII)
_ACCOUNT = re.compile(r"acct:[a-z][a-z0-9_-]{0,47}\Z", re.ASCII)


def _object(value, required, optional=(), *, path):
    if type(value) is not dict or not all(type(k) is str for k in value):
        raise ValueError(f"{path}: JSON object required")
    missing = set(required) - value.keys()
    extra = value.keys() - set(required) - set(optional)
    if missing or extra:
        # Do not echo rejected field names: a raw connector payload may contain
        # private data even in keys. Callers can inspect their schema locally.
        raise ValueError(f"{path}: missing required or unexpected fields")


def _choice(value, choices, path):
    if type(value) is not str or value not in choices:
        raise ValueError(f"{path}: invalid declared value")
    return value


def _text(value, path, pattern=None):
    if (type(value) is not str or not 1 <= len(value) <= 300
            or value.strip() != value
            or any(ord(c) < 32 or ord(c) > 126 for c in value)
            or (pattern is not None and pattern.fullmatch(value) is None)):
        raise ValueError(f"{path}: canonical nonempty ASCII text required")
    return value


def _date(value, path):
    if type(value) is not str or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value, re.ASCII) is None:
        raise ValueError(f"{path}: ISO calendar date required")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{path}: impossible calendar date") from None


def _minor(value, path):
    if type(value) is not int or abs(value) > MAX_MINOR:
        raise ValueError(f"{path}: bounded integer minor units required")
    return value


def _row_summary(rows):
    return {
        "count": len(rows),
        "net_movement_minor": sum(r["amount_minor"] for r in rows),
        "inflow_minor": sum(max(0, r["amount_minor"]) for r in rows),
        "outflow_minor": sum(max(0, -r["amount_minor"]) for r in rows),
        "transaction_ids": sorted(r["id"] for r in rows),
    }


def analyze_cashflow(payload):
    """Validate normalized rows and return the exact report documented above."""
    _object(payload, ("schema", "version", "dataset_kind", "currency", "currency_scale",
                      "interval", "coverage", "accounts", "transactions"), path="payload")
    if payload["schema"] != SCHEMA or type(payload["version"]) is not int or payload["version"] != VERSION:
        raise ValueError("payload: unsupported schema/version")
    dataset_kind = _choice(payload["dataset_kind"], {"synthetic", "public", "deidentified"}, "dataset_kind")
    currency = _text(payload["currency"], "currency", re.compile(r"[A-Z]{3}\Z", re.ASCII))
    scale = payload["currency_scale"]
    if type(scale) is not int or not 0 <= scale <= 9:
        raise ValueError("currency_scale: integer decimal places 0..9 required")
    interval = payload["interval"]
    _object(interval, ("start", "end"), path="interval")
    start, end = _date(interval["start"], "interval.start"), _date(interval["end"], "interval.end")
    if start >= end:
        raise ValueError("interval: start must precede exclusive end")

    coverage = payload["coverage"]
    _object(coverage, ("status", "scope", "reason", "excluded_scopes"), path="coverage")
    _choice(coverage["status"], _COVERAGE, "coverage.status")
    _choice(coverage["scope"], {"household", "declared_accounts"}, "coverage.scope")
    _text(coverage["reason"], "coverage.reason")
    exclusions = coverage["excluded_scopes"]
    if type(exclusions) is not list or len(exclusions) > MAX_ACCOUNTS:
        raise ValueError("coverage.excluded_scopes: bounded array required")
    seen_scopes = set()
    for i, item in enumerate(exclusions):
        path = f"coverage.excluded_scopes[{i}]"
        _object(item, ("scope", "reason"), path=path)
        _text(item["scope"], path + ".scope", _CATEGORY)
        _text(item["reason"], path + ".reason")
        if item["scope"] in seen_scopes:
            raise ValueError("coverage.excluded_scopes: duplicate scope")
        seen_scopes.add(item["scope"])

    accounts = payload["accounts"]
    if type(accounts) is not list or not 1 <= len(accounts) <= MAX_ACCOUNTS:
        raise ValueError("accounts: nonempty bounded array required")
    refs = set()
    for i, item in enumerate(accounts):
        path = f"accounts[{i}]"
        _object(item, ("account_ref", "coverage", "reason"), path=path)
        ref = _text(item["account_ref"], path + ".account_ref", _ACCOUNT)
        _choice(item["coverage"], _COVERAGE, path + ".coverage")
        _text(item["reason"], path + ".reason")
        if ref in refs:
            raise ValueError("accounts: duplicate pseudonymous reference")
        refs.add(ref)

    transactions = payload["transactions"]
    if type(transactions) is not list or len(transactions) > MAX_TRANSACTIONS:
        raise ValueError("transactions: bounded array required")
    rows, seen_ids, groups = [], set(), {}
    absolute_total = 0
    for i, item in enumerate(transactions):
        path = f"transactions[{i}]"
        _object(item, ("id", "account_ref", "amount_minor", "currency", "currency_scale",
                       "date", "status", "kind", "source_id"),
                ("category", "transfer_group"), path=path)
        identifier = _text(item["id"], path + ".id", _TOKEN)
        if identifier in seen_ids:
            raise ValueError("transactions: duplicate transaction ID")
        seen_ids.add(identifier)
        ref = _text(item["account_ref"], path + ".account_ref", _ACCOUNT)
        if ref not in refs:
            raise ValueError(f"{path}.account_ref: account was not declared")
        amount = _minor(item["amount_minor"], path + ".amount_minor")
        absolute_total += abs(amount)
        if absolute_total > MAX_MINOR:
            raise ValueError("transactions: aggregate absolute minor units exceed safe range")
        if (item["currency"] != currency or type(item["currency"]) is not str
                or type(item["currency_scale"]) is not int or item["currency_scale"] != scale):
            raise ValueError(f"{path}: incompatible or missing currency/scale")
        observed = _date(item["date"], path + ".date")
        _choice(item["status"], {"posted", "pending"}, path + ".status")
        kind = _choice(item["kind"], _KINDS, path + ".kind")
        _text(item["source_id"], path + ".source_id", _TOKEN)
        if (kind in {"income", "refund"} and amount < 0) or (kind == "expense" and amount > 0):
            raise ValueError(f"{path}: kind conflicts with signed amount")
        category = item.get("category")
        if category is not None:
            _text(category, path + ".category", _CATEGORY)
        group = item.get("transfer_group")
        if "transfer_group" in item:
            if kind != "transfer":
                raise ValueError(f"{path}: transfer_group requires transfer kind")
            _text(group, path + ".transfer_group", _TOKEN)
        row = dict(item, category=category, in_interval=start <= observed < end)
        rows.append(row)
        if group is not None:
            groups.setdefault(group, []).append(row)

    posted = sorted((r for r in rows if r["in_interval"] and r["status"] == "posted"), key=lambda r: r["id"])
    pending = [r for r in rows if r["in_interval"] and r["status"] == "pending"]
    outside = [r for r in rows if not r["in_interval"]]
    paired, unmatched, paired_ids = [], [], set()
    for row in posted:
        if row["kind"] != "transfer" or row["id"] in paired_ids:
            continue
        group = row.get("transfer_group")
        legs = groups.get(group, [])
        if group is None:
            reason = "no_explicit_transfer_group"
        elif len(legs) != 2:
            reason = "group_requires_exactly_two_supplied_legs"
        elif not all(r["in_interval"] and r["status"] == "posted" for r in legs):
            reason = "counterpart_not_posted_in_interval"
        elif legs[0]["account_ref"] == legs[1]["account_ref"]:
            reason = "counterpart_is_same_account"
        elif legs[0]["amount_minor"] == 0 or legs[0]["amount_minor"] != -legs[1]["amount_minor"]:
            reason = "amounts_are_not_nonzero_exact_opposites"
        else:
            debit = next(r for r in legs if r["amount_minor"] < 0)
            credit = next(r for r in legs if r["amount_minor"] > 0)
            ids = sorted(r["id"] for r in legs)
            paired_ids.update(ids)
            paired.append({"transfer_group": group, "amount_minor": credit["amount_minor"],
                           "debit_account_ref": debit["account_ref"], "credit_account_ref": credit["account_ref"],
                           "transaction_ids": ids})
            continue
        unmatched.append({"id": row["id"], "transfer_group": group,
                          "amount_minor": row["amount_minor"], "reason": reason})

    lineage = {k: [] for k in ("income", "expense", "refund", "paired_transfer", "unmatched_transfer", "investment", "unknown")}
    account_totals = {}
    for ref in sorted(refs):
        account_totals[ref] = {"account_ref": ref, "posted_count": 0, "pending_count": 0,
            "observed_cash_movement_minor": 0, "income_minor": 0, "gross_expense_minor": 0,
            "refunds_minor": 0, "net_spending_minor": 0, "paired_transfer_movement_minor": 0,
            "unmatched_transfer_movement_minor": 0, "investment_movement_minor": 0, "unknown_movement_minor": 0}
    categories = {}
    for row in pending:
        account_totals[row["account_ref"]]["pending_count"] += 1
    for row in posted:
        account = account_totals[row["account_ref"]]
        amount, kind = row["amount_minor"], row["kind"]
        component = ("paired_transfer" if row["id"] in paired_ids else "unmatched_transfer") if kind == "transfer" else kind
        lineage[component].append(row["id"])
        account["posted_count"] += 1
        account["observed_cash_movement_minor"] += amount
        if kind == "income":
            account["income_minor"] += amount
        elif kind in {"expense", "refund"}:
            key = "gross_expense_minor" if kind == "expense" else "refunds_minor"
            contribution = -amount if kind == "expense" else amount
            account[key] += contribution
            category = categories.setdefault(row["category"], {"category": row["category"],
                "gross_expense_minor": 0, "refunds_minor": 0, "net_spending_minor": 0, "transaction_ids": []})
            category[key] += contribution
            category["transaction_ids"].append(row["id"])
        else:
            account[component + "_movement_minor"] += amount
    for result in [*account_totals.values(), *categories.values()]:
        result["net_spending_minor"] = result["gross_expense_minor"] - result["refunds_minor"]
    money_keys = [k for k in next(iter(account_totals.values())) if k.endswith("_minor")]
    totals = {k: sum(a[k] for a in account_totals.values()) for k in money_keys}
    totals["internal_transfer_volume_minor"] = sum(p["amount_minor"] for p in paired)
    component_sum = (totals["income_minor"] - totals["gross_expense_minor"] + totals["refunds_minor"]
                     + totals["paired_transfer_movement_minor"] + totals["unmatched_transfer_movement_minor"]
                     + totals["investment_movement_minor"] + totals["unknown_movement_minor"])
    residual = totals["observed_cash_movement_minor"] - component_sum
    if residual or totals["paired_transfer_movement_minor"]:
        raise RuntimeError("cashflow internal reconciliation invariant failed")

    reasons, flags = [], []
    if coverage["scope"] != "household":
        reasons.append("scope_is_declared_accounts_only")
    if coverage["status"] != "complete":
        reasons.append("coverage_" + coverage["status"])
    noncomplete = sorted(a["account_ref"] for a in accounts if a["coverage"] != "complete")
    for status in ("incomplete", "unknown"):
        if any(a["coverage"] == status for a in accounts):
            reasons.append("account_coverage_" + status)
    if exclusions:
        reasons.append("excluded_scopes_present")
    if coverage["status"] == "complete" and (noncomplete or (exclusions and coverage["scope"] == "household")):
        flags.append({"code": "conflicting_coverage_declarations", "account_refs": noncomplete})
    if pending:
        reasons.append("pending_transactions_excluded")
        flags.append({"code": "pending_transactions_excluded", "transaction_ids": sorted(r["id"] for r in pending)})
    if outside:
        flags.append({"code": "outside_interval_excluded", "transaction_ids": sorted(r["id"] for r in outside)})
    if lineage["unknown"]:
        reasons.append("unknown_transaction_kinds")
        flags.append({"code": "unknown_transaction_kinds", "transaction_ids": lineage["unknown"][:]})
    unknown_categories = [r["id"] for r in posted if r["kind"] in {"expense", "refund"} and r["category"] in {None, "unknown"}]
    if unknown_categories:
        flags.append({"code": "unknown_spending_categories", "transaction_ids": unknown_categories})
    if unmatched:
        reasons.append("unmatched_transfers")
        flags.append({"code": "unmatched_transfers", "transaction_ids": [r["id"] for r in unmatched]})
    if totals["net_spending_minor"] < 0:
        reasons.append("refunds_exceed_current_period_expense")
        flags.append({"code": "refunds_exceed_current_period_expense", "transaction_ids": lineage["refund"][:]})
    coverage_reasons = [r for r in reasons if "coverage" in r or r.startswith("scope_") or r == "excluded_scopes_present"]
    if coverage_reasons:
        flags.append({"code": "limited_declared_coverage", "reasons": coverage_reasons})
    if totals["income_minor"] <= 0:
        reasons.append("income_not_positive")
    numerator = totals["income_minor"] - totals["net_spending_minor"]
    uncertain_coverage = coverage["status"] == "unknown" or any(a["coverage"] == "unknown" for a in accounts)
    coverage_summary = "unknown" if uncertain_coverage else "limited" if coverage_reasons else "complete_as_declared"
    coverage_out = dict(coverage, excluded_scopes=[dict(x) for x in exclusions],
        account_declarations=[dict(a) for a in sorted(accounts, key=lambda a: a["account_ref"])],
        noncomplete_account_refs=noncomplete,
        accounts_without_posted_activity=[ref for ref, a in account_totals.items() if a["posted_count"] == 0],
        activity_note="No observed transactions does not establish missing data or a zero account balance.")
    return {
        "schema": REPORT_SCHEMA, "version": VERSION, "dataset_kind": dataset_kind,
        "currency": currency, "currency_scale": scale, "interval": dict(interval), "coverage": coverage_out,
        "counts": {"supplied": len(rows), "posted_in_interval": len(posted), "pending_in_interval": len(pending), "outside_interval": len(outside)},
        "totals": totals, "accounts": list(account_totals.values()),
        "spending_by_category": sorted(categories.values(), key=lambda c: (c["category"] is not None, c["category"] or "")),
        "pending": _row_summary(pending),
        "excluded": {"outside_interval": dict(_row_summary(outside), posted_count=sum(r["status"] == "posted" for r in outside),
                     pending_count=sum(r["status"] == "pending" for r in outside)), "excluded_scopes": [dict(x) for x in exclusions]},
        "transfers": {"paired": sorted(paired, key=lambda p: p["transfer_group"]), "unmatched": unmatched},
        "reconciliation": {"equation": "income - gross_expense + refunds + paired_transfer + unmatched_transfer + investment + unknown",
            "component_sum_minor": component_sum, "residual_minor": residual, "passed": residual == 0},
        "saving_ratio": {"value": None if reasons else numerator / totals["income_minor"],
            "numerator_minor": numerator, "denominator_minor": totals["income_minor"], "withheld_reasons": reasons,
            "definition": "(declared posted income - net spending) / declared posted income for this interval; not a net-worth change"},
        "lineage": lineage, "source_ids": sorted({r["source_id"] for r in rows}), "flags": flags,
        "confidence": {"arithmetic": "exact_integer_reconciliation", "coverage": coverage_summary,
            "source_verification": "not_performed",
            "qualifier": "Exact arithmetic over supplied normalized rows; coverage and classification are caller declarations. Source truth is not verified here."},
        "limitations": ["Observed cash movement is the sum of included normalized transaction amounts, not a bank/broker balance reconciliation or change in net worth.",
            "Investment cash movements are neither income nor consumption spending; asset sales, deposits, borrowing and transfers must be classified upstream.",
            "Refunds reduce this interval's expense without proving the original purchase occurred in this interval.",
            "Sources, posting-calendar mapping and deidentification require upstream validation. Pseudonym syntax does not prove privacy.",
            "No annualization, tax characterization, transaction categorization inference, recurrence inference, or financial execution is performed."],
    }


def cashflow_fixture():
    """Return a fresh, fully synthetic normalized example (never account data)."""
    def row(identifier, account, amount, kind, **extra):
        return {"id": identifier, "account_ref": account, "amount_minor": amount, "kind": kind,
                "currency": "USD", "currency_scale": 2, "date": "2026-01-15", "status": "posted",
                "source_id": "synthetic:cashflow", **extra}
    return {"schema": SCHEMA, "version": VERSION, "dataset_kind": "synthetic", "currency": "USD", "currency_scale": 2,
        "interval": {"start": "2026-01-01", "end": "2026-02-01"},
        "coverage": {"status": "complete", "scope": "household", "reason": "All accounts in the synthetic household are declared.", "excluded_scopes": []},
        "accounts": [{"account_ref": "acct:checking", "coverage": "complete", "reason": "Complete synthetic posted rows for the interval."},
                     {"account_ref": "acct:card", "coverage": "complete", "reason": "Complete synthetic posted rows for the interval."}],
        "transactions": [row("txn:income", "acct:checking", 100_000, "income"),
            row("txn:purchase", "acct:card", -12_345, "expense", category="groceries"),
            row("txn:refund", "acct:card", 345, "refund", category="groceries"),
            row("txn:payment-out", "acct:checking", -12_000, "transfer", transfer_group="transfer:card-payment"),
            row("txn:payment-in", "acct:card", 12_000, "transfer", transfer_group="transfer:card-payment")]}
