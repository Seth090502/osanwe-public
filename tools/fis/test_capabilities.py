"""Synthetic namespace/scope controls; these do not call any connector."""
import unittest
from capabilities import bind, READS, PREFIXES


class CapabilityTests(unittest.TestCase):
    def test_both_harness_names_have_equivalent_semantics(self):
        results = [bind([p + op for op in READS.values()]) for p in PREFIXES]
        for result in results:
            self.assertTrue(all(b["state"] == "schema_available" for b in result["bindings"]))
            self.assertFalse(result["authorizes_account_access"])
            self.assertFalse(result["authorizes_execution"])
            self.assertTrue(all(not b["live_verified"] for b in result["bindings"]))
        self.assertEqual([b["capability"] for b in results[0]["bindings"]],
                         [b["capability"] for b in results[1]["bindings"]])

    def test_unsupported_namespace_and_order_tools_never_bind(self):
        names = ["mcp__untrusted__get_equity_quotes", PREFIXES[0] + "place_equity_order"]
        self.assertTrue(all(b["state"] == "unavailable" for b in bind(names)["bindings"]))

    def test_ambiguity_requires_explicit_selection(self):
        names = [p + "get_equity_quotes" for p in PREFIXES]
        self.assertEqual(bind(names, required=["equity_quotes"])["bindings"][0]["state"], "ambiguous")
        self.assertEqual(bind(names, required=["equity_quotes"], selected={"equity_quotes": names[1]})["bindings"][0]["tool"], names[1])
        with self.assertRaises(ValueError):
            bind(names, required=["equity_quotes"], selected={"equity_quotes": "other"})

    def test_crypto_and_account_scope_do_not_disappear(self):
        names = [PREFIXES[0] + READS[c] for c in ("crypto_positions", "crypto_quotes")]
        rows = {b["capability"]: b for b in bind(names)["bindings"]}
        self.assertTrue(rows["crypto_positions"]["account_scope_required"])
        self.assertFalse(rows["crypto_quotes"]["account_scope_required"])
        self.assertEqual(rows["crypto_positions"]["state"], "schema_available")

    def test_reject_data_and_malformed_inventories(self):
        for value in ({"account_id": "synthetic"}, [{"name": "tool", "data": 0}], ["bad\nname"], ["duplicate", "duplicate"]):
            with self.subTest(value=value), self.assertRaises(ValueError):
                bind(value)
        with self.assertRaises(ValueError):
            bind([], required=["place_order"])


if __name__ == "__main__":
    unittest.main()
