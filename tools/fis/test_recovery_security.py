#!/usr/bin/env python3
"""Synthetic W9-C security regressions; only temporary files are written."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import obs
import calcs_household as household
import taxlot_ext as taxlot

spec = importlib.util.spec_from_file_location(
    "recovery_dashboard", HERE.parents[1] / "fis-app" / "build_dashboard.py")
dashboard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dashboard)


class EventSecurity(unittest.TestCase):
    def test_credentials_and_novel_fields_are_suppressed(self):
        keys = ("password", "api_key", "apiKey", "token", "secret",
                "authorization", "Authorization", "x-api-key", "access_token",
                "refresh_token", "client_secret", "private_key", "session_id",
                "cookie", "ssn", "member_name", "household_id", "lot_id",
                "iban", "email", "phone", "dob", "beneficiary", "salary",
                "net_worth_usd", "position_size", "novel_sensitive_field")
        payload = {k: "SYNTHETIC-SECRET-%d" % i for i, k in enumerate(keys)}
        payload["nested"] = {"apiKey": "SYNTHETIC-NESTED-SECRET"}
        payload["count"] = 3
        with tempfile.TemporaryDirectory(prefix="fis-security-") as td:
            path = os.path.join(td, "events.jsonl")
            result = obs.emit_event("test.event", payload, event_log_path=path)
            stored = Path(path).read_text(encoding="ascii")
            self.assertNotIn("SYNTHETIC-SECRET", stored)
            self.assertNotIn("SYNTHETIC-NESTED-SECRET", stored)
            self.assertEqual(result["payload"]["count"], 3)
            self.assertFalse(obs.contains_sensitive_value(result["payload"]))
            self.assertEqual(len(stored.splitlines()), 1)

    def test_metadata_cannot_carry_household_or_credentials(self):
        with tempfile.TemporaryDirectory(prefix="fis-security-") as td:
            path = os.path.join(td, "events.jsonl")
            obs.emit_event("event.ssn:123-45-6789", run_id="household:private-name",
                           dataset_version="synthetic-households/private-name",
                           correlation_id="Bearer SYNTHETIC-SECRET",
                           event_log_path=path)
            stored = Path(path).read_text(encoding="ascii")
            for bad in ("123-45-6789", "private-name", "SYNTHETIC-SECRET"):
                self.assertNotIn(bad, stored)

    def test_operational_metadata_survives(self):
        with tempfile.TemporaryDirectory(prefix="fis-security-") as td:
            event = obs.emit_event("test.event", {"count": 2, "ok": True},
                run_id="run-1", correlation_id="corr-9", causation_id="caus-3",
                dataset_version="abc123", event_log_path=os.path.join(td, "log"))
            self.assertEqual(event["event_type"], "test.event")
            self.assertEqual(event["correlation_id"], "corr-9")
            self.assertEqual(event["payload"], {"count": 2, "ok": True})

    def test_known_field_cannot_smuggle_arbitrary_text(self):
        result = obs.redact({"count": "private-name", "state": "private-name",
                             "effective_date": "private-name"})
        self.assertEqual(set(result.values()), {obs.REDACTED})

    def test_lineage_output_cannot_forge_terminal_lines(self):
        aid = "artifact:safe\x1b[2J\nFORGED"
        store = {"artifacts": {aid: {"current": {
            "kind": "fact", "inputs": [], "digest": "abc\x1b[31m"}}}}
        with tempfile.TemporaryDirectory(prefix="fis-security-") as td:
            path = Path(td) / "provenance.json"
            path.write_text(json.dumps(store), encoding="ascii")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                obs.lineage_trace(aid, store_path=str(path))
            rendered = output.getvalue()
            self.assertEqual(len(rendered.splitlines()), 2)
            self.assertNotIn("\x1b", rendered)


class DashboardSecurity(unittest.TestCase):
    def dated_payload(self):
        return {
            "build_ts_utc": "2026-09-12T12:00:00Z",
            "household": {"as_of": "2026-09-12"},
            "portfolio": {"as_of": "2026-09-12"},
            "risk": {"series_end": "2026-09-12"},
            "decision": {"info_cutoff": {"as_of": "2026-09-12"}},
            "dataquality": {"datasets": [{"coverage_end": "2026-09-12",
                                           "license_status": "verified-open"}]},
        }

    def clock_result(self, payload, now="2026-09-12T13:00:00Z"):
        policy = dashboard.TEMPLATE.split("// FRESHNESS POLICY START", 1)[1].split(
            "// FRESHNESS POLICY END", 1)[0]
        script = policy + "\nprocess.stdout.write(JSON.stringify(reportFreshness(" + \
            json.dumps(payload) + ",Date.parse(" + json.dumps(now) + "))));"
        proc = subprocess.run([shutil.which("node"), "-e", script],
                              capture_output=True, text=True, check=True)
        return json.loads(proc.stdout)

    @unittest.skipUnless(shutil.which("node"), "Node runtime unavailable")
    def test_view_time_ages_the_same_unchanged_report(self):
        payload = self.dated_payload()
        self.assertFalse(self.clock_result(payload)["requires_refresh"])
        later = self.clock_result(payload, "2026-09-19T13:00:00Z")
        self.assertTrue(later["requires_refresh"])
        self.assertEqual(later["status"], "HISTORICAL")
        self.assertEqual(later["oldest_as_of"], "2026-09-12")

    @unittest.skipUnless(shutil.which("node"), "Node runtime unavailable")
    def test_missing_metadata_cannot_look_current(self):
        for missing in ("build_ts_utc", "household", "portfolio", "risk", "decision", "dataquality"):
            with self.subTest(missing=missing):
                payload = self.dated_payload()
                del payload[missing]
                result = self.clock_result(payload)
                self.assertTrue(result["requires_refresh"])
                self.assertEqual(result["status"], "UNVERIFIED")

    @unittest.skipUnless(shutil.which("node"), "Node runtime unavailable")
    def test_new_build_does_not_freshen_old_inputs(self):
        payload = self.dated_payload()
        payload["risk"]["series_end"] = "2024-01-01"
        result = self.clock_result(payload)
        self.assertTrue(result["requires_refresh"])
        self.assertEqual(result["oldest_as_of"], "2024-01-01")

    @unittest.skipUnless(shutil.which("node"), "Node runtime unavailable")
    def test_future_and_invalid_dates_remain_unverified(self):
        for value in ("2030-01-01", "2026-02-31", "not-a-date"):
            with self.subTest(value=value):
                payload = self.dated_payload()
                payload["risk"]["series_end"] = value
                result = self.clock_result(payload)
                self.assertTrue(result["requires_refresh"])
                self.assertEqual(result["status"], "UNVERIFIED")

    @unittest.skipUnless(shutil.which("node"), "Node runtime unavailable")
    def test_current_but_unlicensed_sources_stay_unverified(self):
        payload = self.dated_payload()
        payload["dataquality"]["datasets"][0]["license_status"] = "unverified"
        self.assertEqual(self.clock_result(payload)["status"], "UNVERIFIED")

    def test_fallback_banner_and_view_time_refresh_are_present(self):
        page = dashboard.render_page(self.dated_payload())
        self.assertIn('class="historical-output"', page)
        self.assertIn("HISTORICAL / UNVERIFIED SNAPSHOT. Dates have not been checked.", page)
        self.assertIn("setInterval(updateFreshness,60000)", page)
        self.assertIn('addEventListener("visibilitychange",updateFreshness)', page)
        self.assertNotIn("var stale=d.staleness_days", page)

    @unittest.skipUnless(shutil.which("node"), "Node runtime unavailable")
    def test_complete_generated_script_parses(self):
        page = dashboard.render_page({"note": "synthetic"})
        script = re.search(r"<script>(.*?)</script>", page, re.S).group(1)
        proc = subprocess.run([shutil.which("node"), "--check"], input=script,
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node runtime unavailable")
    def test_real_escape_helper_is_attribute_safe(self):
        fn = re.search(r"function esc\(s\)\{.*?\n  \}", dashboard.TEMPLATE, re.S).group(0)
        payloads = ['x" onmouseover="attack" data-x="', "'`<>&", "</script>",
                    "&#34; onfocus=attack", "safe"]
        script = fn + "\nprocess.stdout.write(JSON.stringify(" + json.dumps(payloads) + ".map(esc)));"
        proc = subprocess.run([shutil.which("node"), "-e", script],
                              capture_output=True, text=True, check=True)
        for original, escaped in zip(payloads, json.loads(proc.stdout)):
            class Tags(HTMLParser):
                def handle_starttag(self, tag, attrs):
                    self.attrs = attrs
            parser = Tags()
            parser.feed('<span title="' + escaped + '">x</span>')
            self.assertEqual(parser.attrs, [("title", original)])

    def test_badge_title_uses_dom_attribute_api(self):
        self.assertIn('setAttribute("title",', dashboard.TEMPLATE)
        self.assertNotIn('title="\'+esc(c.promotion_blocked_reason)', dashboard.TEMPLATE)

    def test_script_data_cannot_close_script_element(self):
        page = dashboard.render_page({"note": "</script><script>attack()</script>"})
        self.assertEqual(page.lower().count("<script>"), 1)
        self.assertEqual(page.lower().count("</script>"), 1)


class ProviderSecurity(unittest.TestCase):
    def trade(self, quote):
        p = household.Portfolio()
        p.add_lot(household.Lot("SYNTH-A", "2025-01-01", 10, 1000, 0))
        return {"portfolio": p, "shares": 2, "price_per_share": quote,
                "day": 500, "date": "2026-09-12"}

    def test_unprovenanced_price_blocks_recommendation_posture(self):
        result = taxlot.rebalancing_tax_cost([self.trade(20)], .24, .15)
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertTrue(result["recommendation_blocked"])
        self.assertEqual(result["trades"][0]["price_source"], "bare-float-unprovenanced")
        self.assertEqual(result["license_status"], "unverified")

    def test_observation_does_not_imply_licensed(self):
        quote = taxlot.PriceQuote(price=20, as_of="2026-09-12", source="synthetic-provider")
        result = taxlot.rebalancing_tax_cost([self.trade(quote)], .24, .15)
        self.assertTrue(result["recommendation_blocked"])
        self.assertEqual(result["license_status"], "unverified")

    def test_explicit_source_license_and_date_are_preserved(self):
        quote = taxlot.PriceQuote(price=20, as_of="2026-09-12",
            source="fixture:licensed-provider", license_status="verified-open")
        result = taxlot.rebalancing_tax_cost([self.trade(quote)], .24, .15)
        self.assertFalse(result["recommendation_blocked"])
        self.assertEqual(result["trades"][0]["price_as_of"], "2026-09-12")
        self.assertEqual(result["price_sources"], ["fixture:licensed-provider"])
        self.assertEqual(result["license_status"], "verified-open")

    def test_future_quote_date_does_not_support_recommendation(self):
        quote = taxlot.PriceQuote(price=20, as_of="2030-01-01",
            source="fixture:licensed-provider", license_status="verified-open")
        result = taxlot.rebalancing_tax_cost([self.trade(quote)], .24, .15)
        self.assertTrue(result["recommendation_blocked"])


if __name__ == "__main__":
    unittest.main()
