#!/usr/bin/env python3
"""Offline negative controls for the canonical source-policy parser and the
relay worker read jail."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
import relay_exec

START = "<!-- blocked-domains:start -->"
END = "<!-- blocked-domains:end -->"
DOMAINS = ["site%d.example" % i for i in range(16)]


class SourcePolicy(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="osanwe-source-policy-")
        self.path = Path(self.tmp.name) / "source-policy.md"
        self.target = patch.object(relay_exec, "SOURCE_POLICY_MD", str(self.path))
        self.target.start()

    def tearDown(self):
        self.target.stop()
        self.tmp.cleanup()

    def parse(self, body):
        self.path.write_text(body, encoding="ascii")
        return relay_exec.load_blocked_domains()

    def block(self, domains=DOMAINS):
        return START + "\n" + "\n".join(domains) + "\n" + END

    def test_complete_block_and_only_the_block_are_read(self):
        value = self.parse("Other source: unblocked.example\n" + self.block())
        self.assertEqual(sorted(DOMAINS), value)

    def test_missing_source_fails_closed(self):
        self.assertIsNone(relay_exec.load_blocked_domains())

    def test_invalid_text_encoding_fails_closed(self):
        self.path.write_bytes(b"\xff")
        self.assertIsNone(relay_exec.load_blocked_domains())

    def test_missing_or_duplicate_markers_fail_closed(self):
        for content in ("\n".join(DOMAINS), self.block() + START, self.block() + END,
                        END + "\n" + START + "\n".join(DOMAINS)):
            with self.subTest(content=content):
                self.assertIsNone(self.parse(content))

    def test_short_or_duplicate_domain_list_fails_closed(self):
        self.assertIsNone(self.parse(self.block(DOMAINS[:14])))
        self.assertIsNone(self.parse(self.block([DOMAINS[0]] * 16)))

    def test_invalid_tokens_cannot_be_ignored(self):
        self.assertIsNone(self.parse(self.block(DOMAINS + ["https://bad.example/path"])))

    def test_comma_separated_policy_is_valid(self):
        self.assertEqual(sorted(DOMAINS), self.parse(START + ", ".join(DOMAINS) + END))

    def test_sentence_period_or_single_dns_root_dot_is_normalized(self):
        self.assertEqual(sorted(DOMAINS), self.parse(START + ", ".join(DOMAINS) + "." + END))
        self.assertIsNone(self.parse(START + ", ".join(DOMAINS) + ".." + END))


class ReadJail(unittest.TestCase):
    """audit D17d -- the read jail excluded private/finance/credentials/.raw and
    *.local.md, but not .env* or auth.json, the two secret-bearing names the
    contract calls out by name. The relay worker holds web egress, so anything
    it can read it can also send.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="osanwe-read-jail-")
        self.target = patch.object(relay_exec, "VAULT", self.tmp.name)
        self.target.start()

    def tearDown(self):
        self.target.stop()
        self.tmp.cleanup()

    def jail(self, rel):
        return relay_exec.Executor._jail(None, rel)

    def test_secret_bearing_names_are_refused(self):
        for rel in (".env", ".env.local", ".env.production", "auth.json",
                    os.path.join("tools", ".env"),
                    os.path.join("wiki", "auth.json")):
            with self.subTest(rel=rel):
                with self.assertRaises(relay_exec.Refusal):
                    self.jail(rel)

    def test_renamed_and_backup_copies_of_secrets_are_refused(self):
        # A review found these readable under the exact-name rule. A backup or
        # a renamed copy of a secret is the same secret.
        for rel in ("auth.json.bak", "auth.json~", "auth.jsonc", "old-auth.json", ".auth.json",
                    "app.env", os.path.join("wiki", "prod.env"), ".credentials.json",
                    "signing.key", "tls.pem", "AUTH.JSON.BAK"):
            with self.subTest(rel=rel):
                with self.assertRaises(relay_exec.Refusal):
                    self.jail(rel)

    def test_names_that_only_look_similar_still_resolve(self):
        for rel in (os.path.join("wiki", "keynote.md"), os.path.join("tools", "key_points.md"),
                    os.path.join("wiki", "author-notes.md"), os.path.join("wiki", "envelope.md")):
            with self.subTest(rel=rel):
                self.assertTrue(self.jail(rel).lower().startswith(
                    os.path.realpath(self.tmp.name).lower()))

    def test_existing_exclusions_still_hold(self):
        for rel in (os.path.join("private", "<private-file>"),
                    os.path.join("finance", "x.md"),
                    os.path.join("credentials", "x.md"),
                    "notes.local.md"):
            with self.subTest(rel=rel):
                with self.assertRaises(relay_exec.Refusal):
                    self.jail(rel)

    def test_ordinary_vault_paths_still_resolve(self):
        for rel in (os.path.join("wiki", "note.md"),
                    os.path.join("wiki", "environment.md"),
                    os.path.join("tools", "authors.md")):
            with self.subTest(rel=rel):
                self.assertTrue(self.jail(rel).lower().startswith(
                    os.path.realpath(self.tmp.name).lower()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
