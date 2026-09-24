"""Independent accounting examples and adversarial normalized-input tests."""
import copy
from decimal import Decimal
import json
import random
import unittest

from cashflow import MAX_MINOR, analyze_cashflow, cashflow_fixture


def row(identifier, amount, kind, account="acct:checking", **extra):
    return {"id": identifier, "account_ref": account, "amount_minor": amount,
            "kind": kind, "currency": "USD", "currency_scale": 2,
            "date": "2026-01-15", "status": "posted", "source_id": "synthetic:oracle", **extra}


def fixture_with(*rows):
    result = cashflow_fixture()
    result["transactions"] = list(rows)
    return result


class CashflowAccountingTests(unittest.TestCase):
    def test_card_payment_and_purchase_count_spend_once(self):
        result = analyze_cashflow(cashflow_fixture())
        totals = result["totals"]
        self.assertEqual(totals["income_minor"], 100_000)
        self.assertEqual(totals["gross_expense_minor"], 12_345)
        self.assertEqual(totals["refunds_minor"], 345)
        self.assertEqual(totals["net_spending_minor"], 12_000)
        self.assertEqual(totals["observed_cash_movement_minor"], 88_000)
        self.assertEqual(totals["internal_transfer_volume_minor"], 12_000)
        self.assertEqual(totals["paired_transfer_movement_minor"], 0)
        self.assertEqual(totals["unmatched_transfer_movement_minor"], 0)
        self.assertEqual(result["transfers"]["unmatched"], [])
        self.assertEqual(result["saving_ratio"]["value"], .88)
        # Card purchases/refunds are offset by the payment only in the card
        # account bridge; the payment is never a second household expense.
        account_change = {r["account_ref"]: r["observed_cash_movement_minor"] for r in result["accounts"]}
        self.assertEqual(account_change, {"acct:card": 0, "acct:checking": 88_000})

    def test_independent_decimal_cent_oracle(self):
        income = Decimal("100.03")
        expense = sum(map(Decimal, ("0.01", "0.07", "0.13", "15.39")))
        refunds = Decimal("0.03")
        payload = fixture_with(row("i", 10003, "income"), row("e1", -1, "expense"),
            row("e2", -7, "expense"), row("e3", -13, "expense"), row("e4", -1539, "expense"),
            row("r", 3, "refund"))
        result = analyze_cashflow(payload)
        self.assertEqual(result["totals"]["net_spending_minor"], int((expense - refunds) * 100))
        self.assertEqual(result["totals"]["observed_cash_movement_minor"], int((income - expense + refunds) * 100))
        self.assertEqual(result["saving_ratio"]["numerator_minor"], 8446)
        self.assertEqual(result["saving_ratio"]["denominator_minor"], 10003)
        self.assertEqual(result["reconciliation"]["residual_minor"], 0)

    def test_investment_sale_and_unclassified_deposit_are_not_income(self):
        result = analyze_cashflow(fixture_with(row("sale", 12000, "investment"),
            row("purchase", -10000, "investment"), row("deposit", 8000, "unknown")))
        self.assertEqual(result["totals"]["income_minor"], 0)
        self.assertEqual(result["totals"]["net_spending_minor"], 0)
        self.assertEqual(result["totals"]["investment_movement_minor"], 2000)
        self.assertEqual(result["totals"]["unknown_movement_minor"], 8000)
        self.assertEqual(result["totals"]["observed_cash_movement_minor"], 10000)
        self.assertIsNone(result["saving_ratio"]["value"])
        self.assertIn("unknown_transaction_kinds", result["saving_ratio"]["withheld_reasons"])

    def test_unmatched_transfer_stays_in_cash_bridge(self):
        result = analyze_cashflow(fixture_with(row("i", 10000, "income"),
            row("out", -7000, "transfer", transfer_group="external:transfer")))
        self.assertEqual(result["totals"]["net_spending_minor"], 0)
        self.assertEqual(result["totals"]["observed_cash_movement_minor"], 3000)
        self.assertEqual(result["totals"]["unmatched_transfer_movement_minor"], -7000)
        self.assertEqual(result["transfers"]["unmatched"][0]["reason"], "group_requires_exactly_two_supplied_legs")
        self.assertIsNone(result["saving_ratio"]["value"])

    def test_amount_only_pairing_is_never_inferred(self):
        result = analyze_cashflow(fixture_with(row("out", -100, "transfer"),
            row("in", 100, "transfer", account="acct:card")))
        self.assertEqual(result["transfers"]["paired"], [])
        self.assertEqual(len(result["transfers"]["unmatched"]), 2)
        self.assertEqual(result["totals"]["unmatched_transfer_movement_minor"], 0)
        # A zero sum is not sufficient evidence of complete transfers.
        self.assertIn("unmatched_transfers", result["saving_ratio"]["withheld_reasons"])

    def test_cross_boundary_transfer_does_not_cancel_in_period_leg(self):
        for outside_date in ("2025-12-31", "2026-02-01"):
            payload = fixture_with(row("out", -100, "transfer", date="2026-01-01", transfer_group="g"),
                row("in", 100, "transfer", account="acct:card", date=outside_date, transfer_group="g"))
            with self.subTest(date=outside_date):
                result = analyze_cashflow(payload)
                self.assertEqual(result["totals"]["observed_cash_movement_minor"], -100)
                self.assertEqual(result["totals"]["unmatched_transfer_movement_minor"], -100)
                self.assertEqual(result["excluded"]["outside_interval"]["net_movement_minor"], 100)
                self.assertEqual(result["transfers"]["unmatched"][0]["reason"], "counterpart_not_posted_in_interval")

    def test_pending_counterpart_is_excluded_without_cancelling_posted_leg(self):
        result = analyze_cashflow(fixture_with(row("out", -123, "transfer", transfer_group="g"),
            row("in", 123, "transfer", account="acct:card", status="pending", transfer_group="g")))
        self.assertEqual(result["totals"]["observed_cash_movement_minor"], -123)
        self.assertEqual(result["pending"]["net_movement_minor"], 123)
        self.assertEqual(result["transfers"]["paired"], [])
        self.assertEqual(result["counts"]["posted_in_interval"], 1)
        self.assertEqual(result["counts"]["pending_in_interval"], 1)

    def test_pending_income_and_expense_cannot_pollute_totals(self):
        result = analyze_cashflow(fixture_with(row("i", 1000, "income"),
            row("pi", 200, "income", status="pending"), row("pe", -75, "expense", status="pending")))
        self.assertEqual(result["totals"]["income_minor"], 1000)
        self.assertEqual(result["totals"]["gross_expense_minor"], 0)
        self.assertEqual(result["pending"]["net_movement_minor"], 125)
        self.assertEqual(result["pending"]["inflow_minor"], 200)
        self.assertEqual(result["pending"]["outflow_minor"], 75)
        self.assertIsNone(result["saving_ratio"]["value"])

    def test_explicit_group_still_requires_correct_legs(self):
        variants = {
            "same_account": [row("a", -50, "transfer", transfer_group="g"), row("b", 50, "transfer", transfer_group="g")],
            "different_amounts": [row("a", -50, "transfer", transfer_group="g"), row("b", 49, "transfer", account="acct:card", transfer_group="g")],
            "same_sign": [row("a", -50, "transfer", transfer_group="g"), row("b", -50, "transfer", account="acct:card", transfer_group="g")],
            "zero": [row("a", 0, "transfer", transfer_group="g"), row("b", 0, "transfer", account="acct:card", transfer_group="g")],
            "three_legs": [row("a", -50, "transfer", transfer_group="g"), row("b", 50, "transfer", account="acct:card", transfer_group="g"), row("c", 1, "transfer", date="2025-01-01", transfer_group="g")],
        }
        for name, rows in variants.items():
            with self.subTest(name=name):
                result = analyze_cashflow(fixture_with(*rows))
                self.assertEqual(result["transfers"]["paired"], [])
                self.assertEqual(len(result["transfers"]["unmatched"]), 2)
                self.assertEqual(result["totals"]["net_spending_minor"], 0)
                self.assertTrue(result["reconciliation"]["passed"])

    def test_refunds_can_make_net_spending_negative_without_hiding_it(self):
        result = analyze_cashflow(fixture_with(row("i", 1000, "income"), row("e", -25, "expense"), row("r", 100, "refund")))
        self.assertEqual(result["totals"]["net_spending_minor"], -75)
        self.assertEqual(result["totals"]["observed_cash_movement_minor"], 1075)
        self.assertIsNone(result["saving_ratio"]["value"])
        self.assertIn("refunds_exceed_current_period_expense", result["saving_ratio"]["withheld_reasons"])

    def test_unknown_categories_stay_visible(self):
        result = analyze_cashflow(fixture_with(row("a", -5, "expense"),
            row("b", -7, "expense", category="unknown"), row("c", 2, "refund", category=None)))
        categories = {r["category"]: r for r in result["spending_by_category"]}
        self.assertEqual(categories[None]["net_spending_minor"], 3)
        self.assertEqual(categories["unknown"]["net_spending_minor"], 7)
        flag = next(f for f in result["flags"] if f["code"] == "unknown_spending_categories")
        self.assertEqual(flag["transaction_ids"], ["a", "b", "c"])

    def test_no_income_returns_null_ratio_with_reason(self):
        for transactions in ([], [row("e", -7, "expense")], [row("i", 0, "income")]):
            with self.subTest(transactions=transactions):
                result = analyze_cashflow(fixture_with(*transactions))
                self.assertEqual(result["saving_ratio"]["denominator_minor"], 0)
                self.assertIsNone(result["saving_ratio"]["value"])
                self.assertIn("income_not_positive", result["saving_ratio"]["withheld_reasons"])

    def test_overspending_ratio_is_negative_not_clamped(self):
        result = analyze_cashflow(fixture_with(row("i", 100, "income"), row("e", -150, "expense")))
        self.assertEqual(result["saving_ratio"]["value"], -.5)

    def test_partial_unknown_and_subset_coverage_withhold_ratio(self):
        variants = [lambda p: p["coverage"].update(status="incomplete", reason="Synthetic missing records."),
                    lambda p: p["coverage"].update(status="unknown", reason="Synthetic unknown scope."),
                    lambda p: p["coverage"].update(scope="declared_accounts"),
                    lambda p: p["accounts"][0].update(coverage="incomplete", reason="Synthetic missing interval."),
                    lambda p: p["accounts"][1].update(coverage="unknown", reason="Synthetic unverified coverage."),
                    lambda p: p["coverage"]["excluded_scopes"].append({"scope": "cash_wallet", "reason": "Synthetic unobserved spending."})]
        for edit in variants:
            payload = cashflow_fixture()
            edit(payload)
            with self.subTest(payload=payload["coverage"]):
                result = analyze_cashflow(payload)
                self.assertIsNone(result["saving_ratio"]["value"])
                self.assertTrue(result["saving_ratio"]["withheld_reasons"])
                self.assertEqual(result["totals"]["net_spending_minor"], 12000)
                self.assertNotEqual(result["confidence"]["coverage"], "complete_as_declared")

    def test_contradictory_coverage_flag_and_exclusion_reasons_preserved(self):
        payload = cashflow_fixture()
        payload["accounts"][1]["coverage"] = "unknown"
        payload["accounts"][1]["reason"] = "Synthetic coverage not known."
        payload["coverage"]["excluded_scopes"] = [{"scope": "cash_wallet", "reason": "Synthetic unobserved cash."}]
        result = analyze_cashflow(payload)
        self.assertIn("conflicting_coverage_declarations", [f["code"] for f in result["flags"]])
        self.assertEqual(result["coverage"]["noncomplete_account_refs"], ["acct:card"])
        self.assertEqual(result["excluded"]["excluded_scopes"], payload["coverage"]["excluded_scopes"])
        self.assertEqual(result["coverage"]["account_declarations"][0]["reason"], "Synthetic coverage not known.")

    def test_empty_declared_account_is_disclosed_without_guessing_balance(self):
        result = analyze_cashflow(fixture_with(row("i", 123, "income")))
        self.assertEqual(result["coverage"]["accounts_without_posted_activity"], ["acct:card"])
        self.assertIn("does not establish", result["coverage"]["activity_note"])
        self.assertTrue(any("net worth" in value for value in result["limitations"]))

    def test_interval_start_inclusive_end_exclusive(self):
        result = analyze_cashflow(fixture_with(row("before", 1, "income", date="2025-12-31"),
            row("start", 2, "income", date="2026-01-01"), row("last", 4, "income", date="2026-01-31"),
            row("end", 8, "income", date="2026-02-01")))
        self.assertEqual(result["totals"]["income_minor"], 6)
        self.assertEqual(result["lineage"]["income"], ["last", "start"])
        self.assertEqual(result["excluded"]["outside_interval"]["net_movement_minor"], 9)

    def test_order_independence_purity_and_json_roundtrip(self):
        payload = cashflow_fixture()
        before = copy.deepcopy(payload)
        result = analyze_cashflow(payload)
        self.assertEqual(payload, before)
        self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)
        payload["accounts"].reverse()
        payload["transactions"].reverse()
        self.assertEqual(analyze_cashflow(payload), result)
        result["coverage"]["account_declarations"][0]["reason"] = "Output-only change."
        self.assertEqual(payload["accounts"], list(reversed(before["accounts"])))
        self.assertEqual(cashflow_fixture(), before)

    def test_adding_balanced_transfer_leaves_economic_flow_unchanged(self):
        base = fixture_with(row("i", 1001, "income"), row("e", -702, "expense"), row("r", 9, "refund"))
        before = analyze_cashflow(base)
        base["transactions"] += [row("t1", -17, "transfer", transfer_group="g"),
                                  row("t2", 17, "transfer", account="acct:card", transfer_group="g")]
        after = analyze_cashflow(base)
        for key in ("observed_cash_movement_minor", "income_minor", "gross_expense_minor", "refunds_minor", "net_spending_minor"):
            self.assertEqual(before["totals"][key], after["totals"][key])
        self.assertEqual(before["saving_ratio"], after["saving_ratio"])

    def test_generated_signed_rows_reconcile_to_independent_direct_sum(self):
        rng = random.Random(44271)
        for trial in range(40):
            transactions = []
            for i in range(80):
                kind = rng.choice(["income", "expense", "refund", "unknown", "investment", "transfer"])
                amount = rng.randrange(-5000, 5001)
                if kind in {"income", "refund"}:
                    amount = abs(amount)
                elif kind == "expense":
                    amount = -abs(amount)
                transactions.append(row(f"row:{i}", amount, kind, account=rng.choice(["acct:checking", "acct:card"]),
                    date=rng.choice(["2025-12-31", "2026-01-01", "2026-01-31", "2026-02-01"]), status=rng.choice(["posted", "pending"])))
            active = [r for r in transactions if r["status"] == "posted" and "2026-01-01" <= r["date"] < "2026-02-01"]
            result = analyze_cashflow(fixture_with(*transactions))
            with self.subTest(trial=trial):
                direct_sum = sum(r["amount_minor"] for r in active)
                self.assertEqual(result["totals"]["observed_cash_movement_minor"], direct_sum)
                self.assertEqual(result["reconciliation"]["component_sum_minor"], direct_sum)
                self.assertEqual(sum(a["observed_cash_movement_minor"] for a in result["accounts"]), direct_sum)
                self.assertEqual(result["counts"]["supplied"], sum(result["counts"][k] for k in ("posted_in_interval", "pending_in_interval", "outside_interval")))
                for account in result["accounts"]:
                    self.assertEqual(account["observed_cash_movement_minor"], account["income_minor"] - account["net_spending_minor"]
                        + account["paired_transfer_movement_minor"] + account["unmatched_transfer_movement_minor"]
                        + account["investment_movement_minor"] + account["unknown_movement_minor"])

    def test_safe_integer_boundary_and_non_two_decimal_currency(self):
        payload = fixture_with(row("i", MAX_MINOR, "income"))
        for record in [payload, *payload["transactions"]]:
            record["currency"] = "JPY"
            record["currency_scale"] = 0
        result = analyze_cashflow(payload)
        self.assertEqual(result["totals"]["income_minor"], MAX_MINOR)
        self.assertEqual(result["currency_scale"], 0)
        self.assertEqual(json.loads(json.dumps(result))["totals"]["income_minor"], MAX_MINOR)


class CashflowRefusalTests(unittest.TestCase):
    def test_duplicate_ids_across_pending_and_outside_rows_are_refused(self):
        for change in ({}, {"status": "pending"}, {"date": "2025-01-01"}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "duplicate transaction"):
                analyze_cashflow(fixture_with(row("same", 1, "income"), row("same", 2, "income", **change)))

    def test_money_rejects_bool_fraction_float_string_and_excessive_range(self):
        for amount in (True, False, 1.0, .01, "100", None, float("nan"), float("inf"), MAX_MINOR + 1, -MAX_MINOR - 1):
            with self.subTest(amount=amount), self.assertRaisesRegex(ValueError, "minor units"):
                analyze_cashflow(fixture_with(row("bad", amount, "unknown")))
        # Even offsetting or excluded rows cannot conceal aggregate overflow.
        for change in ({}, {"date": "2025-01-01"}, {"status": "pending"}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "aggregate absolute"):
                analyze_cashflow(fixture_with(row("a", MAX_MINOR, "unknown"), row("b", -1, "unknown", **change)))

    def test_kind_sign_conflicts_including_negative_refund_refused(self):
        for kind, amount in (("income", -1), ("expense", 1), ("refund", -1)):
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, "kind conflicts"):
                analyze_cashflow(fixture_with(row("bad", amount, kind)))

    def test_incompatible_currency_or_scale_is_never_converted(self):
        for change in ({"currency": "EUR"}, {"currency": "usd"}, {"currency": None},
                       {"currency_scale": 3}, {"currency_scale": True}, {"currency_scale": 2.0}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                analyze_cashflow(fixture_with(row("bad", 1, "income", **change)))
        for key in ("currency", "currency_scale"):
            bad = row("bad", 1, "income")
            del bad[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                analyze_cashflow(fixture_with(bad))
        for scale in (True, -1, 10, 2.0, None):
            payload = cashflow_fixture()
            payload["currency_scale"] = scale
            with self.subTest(scale=scale), self.assertRaises(ValueError):
                analyze_cashflow(payload)

    def test_impossible_and_noncanonical_dates_are_refused_everywhere(self):
        for value in ("2026-02-29", "2024-02-30", "2026-13-01", "0000-01-01", "2026-1-01", "20260101", "2026-01-01T00:00:00Z", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                analyze_cashflow(fixture_with(row("bad", 1, "income", date=value)))
        for start, end in (("2026-02-01", "2026-02-01"), ("2026-02-02", "2026-02-01"), ("2026-02-30", "2026-03-01")):
            payload = cashflow_fixture()
            payload["interval"] = {"start": start, "end": end}
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                analyze_cashflow(payload)
        # A valid leap day is accepted and simply disclosed as outside interval.
        result = analyze_cashflow(fixture_with(row("leap", 1, "income", date="2024-02-29")))
        self.assertEqual(result["counts"]["outside_interval"], 1)

    def test_missing_or_undeclared_or_nonpseudonymous_accounts_refused(self):
        for value in ("acct:absent", "123456789012", "acct:123456", "person@example.invalid", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                analyze_cashflow(fixture_with(row("bad", 1, "income", account=value)))
        payload = cashflow_fixture()
        del payload["transactions"][0]["account_ref"]
        with self.assertRaises(ValueError):
            analyze_cashflow(payload)
        payload = cashflow_fixture()
        payload["accounts"].append(copy.deepcopy(payload["accounts"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate pseudonymous"):
            analyze_cashflow(payload)

    def test_transfer_group_cannot_be_attached_to_nontransfer(self):
        for kind in ("income", "expense", "refund", "unknown", "investment"):
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, "transfer_group"):
                analyze_cashflow(fixture_with(row("bad", 0, kind, transfer_group="g")))
        for group in (None, "", [], {}, True, "raw group with spaces"):
            with self.subTest(group=group), self.assertRaises(ValueError):
                analyze_cashflow(fixture_with(row("bad", 0, "transfer", transfer_group=group)))

    def test_source_id_required_and_not_implicitly_invented(self):
        for source in (None, "", " source", "source\nline", [], {}):
            with self.subTest(source=source), self.assertRaises(ValueError):
                analyze_cashflow(fixture_with(row("bad", 1, "income", source_id=source)))
        bad = row("bad", 1, "income")
        del bad["source_id"]
        with self.assertRaises(ValueError):
            analyze_cashflow(fixture_with(bad))

    def test_all_required_shapes_and_fields_validated(self):
        for field in cashflow_fixture():
            payload = cashflow_fixture()
            del payload[field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                analyze_cashflow(payload)
        edits = [lambda p: p.update(version=True), lambda p: p.update(version=2), lambda p: p.update(schema="raw-provider-schema"),
                 lambda p: p.update(dataset_kind="private"), lambda p: p.update(transactions={}), lambda p: p.update(accounts=[]),
                 lambda p: p.update(coverage=None), lambda p: p["coverage"].update(status=[]),
                 lambda p: p["coverage"].update(reason=""), lambda p: p["coverage"].update(excluded_scopes="all"),
                 lambda p: p["accounts"][0].update(coverage=None), lambda p: p["transactions"][0].update(status="cleared"),
                 lambda p: p["transactions"][0].update(kind="deposit"), lambda p: p["transactions"][0].update(category={})]
        for index, edit in enumerate(edits):
            payload = cashflow_fixture()
            edit(payload)
            with self.subTest(edit=index), self.assertRaises(ValueError):
                analyze_cashflow(payload)
        for payload in (None, [], "payload", True):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                analyze_cashflow(payload)

    def test_unexpected_raw_fields_refused_without_echoing_private_input(self):
        payload = cashflow_fixture()
        payload["transactions"][0]["synthetic_sensitive_key"] = "synthetic_sensitive_value"
        with self.assertRaises(ValueError) as caught:
            analyze_cashflow(payload)
        self.assertNotIn("synthetic_sensitive_key", str(caught.exception))
        self.assertNotIn("synthetic_sensitive_value", str(caught.exception))

    def test_malformed_excluded_rows_and_duplicate_exclusion_scopes_refused(self):
        for change in ({"status": "pending"}, {"date": "2025-01-01"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                analyze_cashflow(fixture_with(row("bad", True, "unknown", **change)))
        payload = cashflow_fixture()
        payload["coverage"]["excluded_scopes"] = [{"scope": "cash_wallet", "reason": "Synthetic gap."}] * 2
        with self.assertRaisesRegex(ValueError, "duplicate scope"):
            analyze_cashflow(payload)


if __name__ == "__main__":
    unittest.main()
