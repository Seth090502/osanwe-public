#!/usr/bin/env python3
"""Isolated negative controls for contract, bootstrap and checker profiles."""
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Contracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="osanwe-contract-test-")
        self.root = Path(self.tmp.name)
        self.contract = b"# Complete contract\n\nEvery binding rule.\n"
        (self.root / "AGENTS.md").write_bytes(self.contract)
        (self.root / "CLAUDE.md").write_bytes(b"@AGENTS.md\n")
        target = self.root / ".agents/scripts/gen-bootstrap.py"
        target.parent.mkdir(parents=True)
        shutil.copy2(ROOT / ".agents/scripts/gen-bootstrap.py", target)
        self.router = load("router_test", ROOT / "tools/router-check.py")
        self.bootstrap = load("bootstrap_test", target)
        (self.root / "BOOTSTRAP.md").write_bytes(self.bootstrap.render(self.root))

    def tearDown(self):
        self.tmp.cleanup()

    def invoke(self, path, *args):
        env = dict(os.environ, OSANWE_VAULT_ROOT=str(self.root), PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run([sys.executable, "-B", str(path), *args], env=env,
                              capture_output=True, text=True, timeout=15)

    def test_contract_with_stub_passes(self):
        self.assertEqual([], self.router.contract_findings(self.root))
        self.assertEqual([], self.router.bootstrap_findings(self.root))
        r = self.invoke(ROOT / "tools/router-check.py")
        self.assertEqual(0, r.returncode, r.stdout + r.stderr)

    def test_claude_md_mirror_is_rejected(self):
        # A full copy in CLAUDE.md is a second set of rules that can drift.
        (self.root / "CLAUDE.md").write_bytes(self.contract)
        self.assertTrue(self.router.contract_findings(self.root))
        r = self.invoke(ROOT / "tools/router-check.py", "--quick")
        self.assertEqual(1, r.returncode, r.stdout + r.stderr)

    def test_missing_stub_is_rejected(self):
        # Without the stub a root CLAUDE.local.md stops Claude Code reading AGENTS.md.
        (self.root / "CLAUDE.md").unlink()
        self.assertTrue(self.router.contract_findings(self.root))
        r = self.invoke(ROOT / "tools/router-check.py", "--quick")
        self.assertEqual(1, r.returncode, r.stdout + r.stderr)

    def test_stub_with_extra_rule_is_rejected(self):
        (self.root / "CLAUDE.md").write_bytes(b"@AGENTS.md\nOne more rule.\n")
        self.assertTrue(self.router.contract_findings(self.root))

    def test_crlf_stub_passes(self):
        # Same line-ending rule as the pre-commit cage.
        (self.root / "CLAUDE.md").write_bytes(b"@AGENTS.md\r\n")
        self.assertEqual([], self.router.contract_findings(self.root))

    def test_nested_claude_md_is_rejected(self):
        nested = self.root / ".claude"
        nested.mkdir(exist_ok=True)
        (nested / "CLAUDE.md").write_bytes(self.contract)
        self.assertTrue(self.router.contract_findings(self.root))

    def test_no_sync_mode_remains(self):
        # Nothing is mirrored any more, so nothing may copy the contract.
        r = self.invoke(ROOT / "tools/router-check.py", "--sync")
        self.assertNotEqual(0, r.returncode, r.stdout + r.stderr)
        source = (ROOT / "tools/router-check.py").read_text(encoding="utf-8")
        self.assertNotIn("write_bytes", source)

    def test_missing_and_empty_contracts_fail(self):
        (self.root / "AGENTS.md").write_bytes(b"")
        self.assertTrue(self.router.contract_findings(self.root))
        (self.root / "AGENTS.md").unlink()
        self.assertTrue(self.router.contract_findings(self.root))

    def test_bootstrap_preserves_complete_source_bytes(self):
        rendered = self.bootstrap.render(self.root)
        self.assertTrue(rendered.endswith(self.contract))
        self.assertEqual(1, rendered.count(self.contract))
        (self.root / "AGENTS.md").write_bytes(self.contract + b"Additional mandatory rule.\n")
        self.assertTrue(self.router.bootstrap_findings(self.root))

    def test_bootstrap_check_never_repairs_drift(self):
        path = self.root / "BOOTSTRAP.md"
        path.write_bytes(b"stale bootstrap")
        r = self.invoke(self.root / ".agents/scripts/gen-bootstrap.py", "--check")
        self.assertEqual(1, r.returncode, r.stdout + r.stderr)
        self.assertEqual(b"stale bootstrap", path.read_bytes())

    def test_non_ascii_contract_is_reported(self):
        (self.root / "AGENTS.md").write_bytes(self.contract + "curly \u2019 quote\n".encode("utf-8"))
        self.assertTrue(self.router.contract_findings(self.root))

    def test_missing_router_file_pointer_is_not_silently_accepted(self):
        (self.root / "AGENTS.md").write_bytes(self.contract + b"Run `python tools/missing-check.py`.\n")
        self.assertTrue(self.router.link_findings(self.root))
        (self.root / "tools").mkdir()
        (self.root / "tools/missing-check.py").write_bytes(b"# fixture\n")
        self.assertEqual([], self.router.link_findings(self.root))

    def test_router_never_spawns_checkall(self):
        with patch.object(self.router, "ROOT", self.root):
            # The CLI integration also completes in 15s; source-level absence of
            # subprocess is deliberate: no indirect recursion or generators.
            self.assertFalse(hasattr(self.router, "subprocess"))


class BranchPolicy(unittest.TestCase):
    """Run copied hooks only in disposable repositories with isolated Git config."""

    @classmethod
    def setUpClass(cls):
        git_bash = Path(r"/path/to/program-files\Git\bin\bash.exe")
        cls.bash = str(git_bash) if git_bash.is_file() else shutil.which("bash")
        cls.git_binary = shutil.which("git")
        if not cls.bash or not cls.git_binary:
            raise RuntimeError("BranchPolicy requires Git and Bash for isolated hook tests")
        cls.hooks = {}
        for name in ("session-branch.sh", "auto-commit.sh"):
            body = (ROOT / ".claude/hooks" / name).read_text(encoding="utf-8")
            # A copied historical hook could still cd into the production vault.
            # Refuse to execute that unsafe fixture rather than touching live state.
            if any(value in body for value in ("/path/to/vault", "/path/to/vault", r"/path/to/vault")):
                raise AssertionError(f"{name}: hardcoded production path is not fixture-safe")
            cls.hooks[name] = body

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="osanwe branch policy ")
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.root = self.base / "vault copy"
        self.cwd = self.base / "unrelated cwd"
        self.empty_hooks = self.base / "empty git hooks"
        for path in (self.root, self.cwd, self.empty_hooks):
            path.mkdir()
        config = self.base / "empty git config"
        config.write_text("", encoding="ascii")
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith("GIT_") and k not in
                    {"BASH_ENV", "ENV", "CLAUDE_DISABLE_AUTO_COMMIT"}}
        self.env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=str(config),
                        GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
        self.git("init", "--initial-branch=main", "--template=" + str(self.empty_hooks))
        for key, value in (("user.name", "Branch Policy Fixture"),
                           ("user.email", "fixture@example.invalid"),
                           ("core.hooksPath", str(self.empty_hooks)),
                           ("core.autocrlf", "false"), ("commit.gpgsign", "false"),
                           ("gc.auto", "0")):
            self.git("config", key, value)
        (self.root / "tracked.txt").write_text("baseline\n", encoding="ascii")
        self.git("add", "tracked.txt")
        self.git("commit", "-m", "fixture: baseline")
        self.copy_hooks(self.root)
        (self.root / "tracked.txt").write_text("uncommitted edit\n", encoding="ascii")
        (self.root / "staged.txt").write_text("already staged\n", encoding="ascii")
        self.git("add", "staged.txt")
        (self.root / "new.txt").write_text("untracked write\n", encoding="ascii")

    def git(self, *args):
        return subprocess.run([self.git_binary, "--no-optional-locks", *args],
                              cwd=self.root, env=self.env, capture_output=True,
                              text=True, check=True, timeout=15).stdout

    def copy_hooks(self, root):
        path = root / ".claude/hooks"
        path.mkdir(parents=True)
        for name, body in self.hooks.items():
            (path / name).write_bytes(body.encode("utf-8"))

    def state(self):
        return ((self.root / ".git/HEAD").read_bytes(),
                self.git("for-each-ref", "--format=%(refname) %(objectname)"),
                (self.root / ".git/index").read_bytes(),
                self.git("status", "--porcelain=v1", "--untracked-files=all"),
                self.git("diff", "--binary"), self.git("diff", "--cached", "--binary"))

    def invoke(self, name, *, root=None, payload=None, syntax=False):
        args = [self.bash, "--noprofile", "--norc"]
        if syntax:
            args.append("-n")
        args.append((Path(root or self.root) / ".claude/hooks" / name).as_posix())
        if payload is None:
            payload = json.dumps({"tool_input": {"file_path": str(self.root / "tracked.txt")}})
        return subprocess.run(args, cwd=self.cwd, env=self.env, input=payload,
                              capture_output=True, text=True, timeout=15)

    def assert_allowed_unchanged(self, hook="session-branch.sh", **kwargs):
        before = self.state()
        result = self.invoke(hook, **kwargs)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("", result.stdout + result.stderr)
        self.assertEqual(before, self.state())

    def test_shell_syntax(self):
        for name in self.hooks:
            result = self.invoke(name, syntax=True)
            self.assertEqual(0, result.returncode, result.stderr)

    def test_main_allows_without_moving_head_refs_or_index(self):
        self.assert_allowed_unchanged()

    def test_named_feature_branches_allow_without_switching(self):
        for branch in ("feature/meaningful-change", "codex/cleanup", "master"):
            with self.subTest(branch=branch):
                self.git("switch", "-c", branch)
                self.assert_allowed_unchanged()

    def test_detached_refuses_with_recovery_and_preserves_state(self):
        self.git("switch", "--detach")
        before = self.state()
        result = self.invoke("session-branch.sh")
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn("detached", result.stderr)
        self.assertIn("git switch -c codex/", result.stderr)
        self.assertIn("git switch main", result.stderr)
        self.assertEqual(before, self.state())

    def test_auto_commit_never_stages_or_commits_on_main_feature_or_detached(self):
        for branch in ("main", "feature/milestone", None):
            with self.subTest(branch=branch):
                if branch is None:
                    self.git("switch", "--detach")
                elif branch != "main":
                    self.git("switch", "-c", branch)
                for key, name in (("file_path", "tracked.txt"), ("path", "new.txt")):
                    self.assert_allowed_unchanged("auto-commit.sh", payload=json.dumps(
                        {"tool_input": {key: str(self.root / name)}}))

    def test_auto_commit_ignores_empty_and_malformed_payloads(self):
        for payload in ("", "not JSON", '{"tool_input": null}'):
            self.assert_allowed_unchanged("auto-commit.sh", payload=payload)

    def test_hooks_outside_repository_are_noops(self):
        outside = self.base / "plain directory"
        self.copy_hooks(outside)
        for name in self.hooks:
            self.assert_allowed_unchanged(name, root=outside)


class CheckerProfiles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load("checkall_test", ROOT / ".agents/scripts/checkall.py")

    def test_quick_exact_readonly_profile(self):
        labels = [name for name, _ in self.mod.selected_steps(quick=True)]
        # The approved daily monitor now includes source admission and read-only
        # generation freshness. It still must not execute research or reindex.
        self.assertEqual(["validate", "sync-check", "driftcheck", "fixture-pins", "router-check",
                          "financial-document-admission", "retrieval-integrity"], labels)

    def test_default_excludes_live_and_hook_execution(self):
        labels = [name for name, _ in self.mod.selected_steps()]
        self.assertNotIn("mcp-canary", labels)
        self.assertNotIn("hook-manifest", labels)
        self.assertIn("router-check", labels)

    def test_router_step_invokes_actual_checker(self):
        with patch.object(self.mod, "run", return_value=(1, "contract drift")) as run:
            good, out = self.mod.step_router_check()
        self.assertFalse(good)
        self.assertIn("router-check.py", run.call_args.args[0][-1])
        self.assertEqual("contract drift", out)

    def test_vault_audit_error_exit_cannot_be_green(self):
        completed = SimpleNamespace(returncode=1, stderr="", stdout=json.dumps({
            "score": 100, "tiers": {"gate": {"count": 0}}, "broken_wikilinks": []}))
        with patch.object(self.mod.subprocess, "run", return_value=completed):
            good, _ = self.mod.step_vault_audit_gate()
        self.assertFalse(good)

    def test_absent_local_lane_adapter_is_unverified_without_running_it(self):
        with tempfile.TemporaryDirectory(prefix="osanwe-clone-without-local-adapter-") as tmp:
            script = Path(tmp) / ".agents/scripts/checkall.py"
            script.parent.mkdir(parents=True)
            shutil.copy2(ROOT / ".agents/scripts/checkall.py", script)
            relocated = load("relocated_checkall", script)
            self.assertEqual(Path(tmp), Path(relocated.ROOT))
            with patch.object(relocated.subprocess, "run") as run:
                good, out = relocated.step_lane_contract()
        self.assertTrue(good)
        self.assertTrue(out.startswith("UNVERIFIED:"))
        run.assert_not_called()

    def test_local_adapter_missing_binary_is_unverified(self):
        completed = SimpleNamespace(returncode=0, stderr="", stdout="[lane-contract] SKIP: claude.exe not found\n")
        with patch("pathlib.Path.is_file", return_value=True), patch.object(self.mod.subprocess, "run", return_value=completed):
            good, out = self.mod.step_lane_contract()
        self.assertTrue(good)
        self.assertTrue(out.startswith("UNVERIFIED:"))

    def test_checker_exception_is_reported_and_does_not_skip_remaining_checks(self):
        second = unittest.mock.Mock(return_value=(True, "remaining invariant checked"))
        def broken():
            raise ValueError("synthetic invalid configuration")
        out = io.StringIO()
        with patch.object(self.mod, "selected_steps", return_value=[("broken", broken), ("second", second)]), redirect_stdout(out):
            result = self.mod.main(["--quick"])
        self.assertEqual(1, result)
        second.assert_called_once()
        for heading in ("WHAT BROKE", "WHAT IT MEANS", "WHAT TO DO", "WHAT TO PASTE BACK"):
            self.assertIn(heading, out.getvalue())
        self.assertIn("synthetic invalid configuration", out.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
