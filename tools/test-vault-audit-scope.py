"""Isolated controls against false-green or accidentally widened audit scopes."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location("audit_scope_test", Path(__file__).with_name("vault-audit.py"))
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class ScopeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        patch = mock.patch.object(AUDIT, "VAULT_ROOT", self.root)
        patch.start()
        self.addCleanup(patch.stop)
        for name, body in (("wiki/team/peer.md", "[[root]]"),
                           ("wiki/root.md", "[[peer]]"),
                           ("wiki/team-extra/broken.md", "[[missing-target]]")):
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("---\naliases: []\ncategories: [wiki]\ntags: []\nstatus: active\ncreated: 2026-09-12\nupdated: 2026-09-12\nrelated: []\n---\n# Fixture\n" + body + "\n", encoding="ascii")

    def audit(self, scope=None, **kwargs):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            AUDIT.run_audit(scope=scope, json_output=True, **kwargs)
        return json.loads(output.getvalue())

    def test_all_and_default_cover_the_same_real_defect(self):
        default = self.audit()
        for value in ("all", "ALL"):
            self.assertEqual(self.audit(value), default)
        self.assertEqual(default["files_scanned"], 3)
        self.assertEqual(len(default["broken_wikilinks"]), 1)
        self.assertTrue(default["gate_breach"])

    def test_subtree_excludes_a_sibling_with_same_prefix(self):
        scoped = self.audit("wiki/team")
        self.assertEqual(scoped["files_scanned"], 1)
        self.assertEqual(scoped["broken_wikilinks"], [])
        self.assertEqual(scoped["orphans"], [])

    def test_single_file_still_reports_its_defect(self):
        scoped = self.audit("wiki/team-extra/broken.md")
        self.assertEqual(scoped["files_scanned"], 1)
        self.assertEqual(scoped["broken_wikilinks"][0]["target"], "missing-target")

    def test_nonexistent_scope_refuses_before_collecting(self):
        with mock.patch.object(AUDIT, "collect_md_files", side_effect=AssertionError("must not scan")):
            with self.assertRaisesRegex(ValueError, "does not exist"):
                self.audit("missing-directory")

    def test_empty_or_unauditable_scope_cannot_claim_a_score(self):
        for scope in ("", "  "):
            with self.assertRaises(ValueError):
                self.audit(scope)
        empty = self.root / "wiki/empty"
        empty.mkdir()
        with self.assertRaisesRegex(ValueError, "no auditable Markdown"):
            self.audit("wiki/empty")

    def test_empty_changed_set_remains_an_explicit_incremental_result(self):
        with mock.patch.object(AUDIT, "get_changed_files", return_value=[]):
            result = self.audit(changed_only=True)
        self.assertEqual(result["files_scanned"], 0)
        self.assertTrue(result["changed_only"])

    def test_empty_full_vault_refuses_both_default_and_all(self):
        with tempfile.TemporaryDirectory() as empty, mock.patch.object(AUDIT, "VAULT_ROOT", Path(empty)):
            for scope in (None, "all", "ALL"):
                with self.subTest(scope=scope), self.assertRaisesRegex(ValueError, "no auditable Markdown"):
                    self.audit(scope)

    def test_markdown_named_directory_is_not_an_audited_file(self):
        with tempfile.TemporaryDirectory() as empty, mock.patch.object(AUDIT, "VAULT_ROOT", Path(empty)):
            (Path(empty) / "wiki/folder.md").mkdir(parents=True)
            self.assertEqual(AUDIT.collect_md_files(), [])
            for scope in (None, "all", "wiki/folder.md"):
                with self.subTest(scope=scope), self.assertRaisesRegex(ValueError, "no auditable Markdown"):
                    self.audit(scope)

    def test_cli_missing_scope_exits_nonzero_without_a_score(self):
        missing = self.root / "does-not-exist"
        p = subprocess.run([sys.executable, str(Path(AUDIT.__file__)), "--scope", str(missing), "--json"],
                           capture_output=True, text=True, timeout=10)
        self.assertEqual(p.returncode, 2)
        data = json.loads(p.stdout)
        self.assertEqual(data["status"], "refused")
        self.assertIsNone(data["score"])


if __name__ == "__main__":
    unittest.main()
