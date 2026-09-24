#!/usr/bin/env python3
"""Synthetic, temporary-only controls for physical append-only ledger writes."""

import contextlib
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SPEC = importlib.util.spec_from_file_location(
    "gen_ledger_preservation", Path(__file__).with_name("gen-ledger-views.py"))
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


class LedgerPreservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "ledger.md"
        self.backup = self.path.with_suffix(".md.pre-regen")

    def seed(self, content):
        self.path.write_bytes(content)

    def assert_append(self, original, addition, expected_tail):
        self.seed(original)
        target = GEN.normalized_text(original.decode("utf-8")) + addition
        count = GEN.apply_append_only(self.path, target)
        self.assertEqual(count, len(expected_tail))
        self.assertEqual(self.path.read_bytes(), original + expected_tail)
        self.assertEqual(self.backup.read_bytes(), original)

    def test_equivalent_text_is_no_write_for_all_existing_newlines(self):
        for original in (b"old\nbody\n", b"old\r\nbody\r\n",
                         b"old\nbody\r\n", b"old\r\nbody\n",
                         b"old\rbody\r", b"old without newline"):
            with self.subTest(original=original):
                self.seed(original)
                os.utime(self.path, ns=(2_000_000_000, 2_000_000_000))
                before = self.path.stat().st_mtime_ns
                result = GEN.apply_append_only(
                    self.path, GEN.normalized_text(original.decode("utf-8")))
                self.assertEqual(result, 0)
                self.assertEqual(self.path.read_bytes(), original)
                self.assertEqual(self.path.stat().st_mtime_ns, before)
                self.assertFalse(self.backup.exists())

    def test_lf_append_and_new_backup_preserve_physical_bytes(self):
        self.assert_append(b"old\nbody\n", "new\nend\n", b"new\nend\n")

    def test_crlf_append_uses_recent_newline(self):
        self.assert_append(b"old\r\nbody\r\n", "new\nend\n", b"new\r\nend\r\n")

    def test_mixed_history_ending_crlf_is_never_normalized(self):
        self.assert_append(b"old\nbody\r\n", "new\nend\n", b"new\r\nend\r\n")

    def test_mixed_history_ending_lf_is_never_normalized(self):
        self.assert_append(b"old\r\nbody\n", "new\r\nend\r", b"new\nend\n")

    def test_single_terminal_newline_extension_is_allowed(self):
        self.assert_append(b"old\r\nbody", "\n", b"\r\n")

    def test_no_prior_newline_defaults_to_lf(self):
        self.assert_append(b"old", "\nnew\n", b"\nnew\n")

    def test_old_carriage_return_convention_remains_append_only(self):
        self.assert_append(b"old\nbody\r", "\nnew\n", b"\rnew\r")

    def test_historical_rewrite_or_truncation_is_refused(self):
        original = b"old\nbody\r\n"
        for target in ("changed\nbody\n", "old\nchanged\n", "old\n", ""):
            with self.subTest(target=target):
                self.seed(original)
                with self.assertRaisesRegex(ValueError, "append-only apply refused"):
                    GEN.apply_append_only(self.path, target)
                self.assertEqual(self.path.read_bytes(), original)
                self.assertFalse(self.backup.exists())

    def test_preexisting_backup_is_immutable_on_append(self):
        original = b"old\nbody\r\n"
        self.seed(original)
        checkpoint = b"earlier\rcheckpoint\nbytes\r\n"
        self.backup.write_bytes(checkpoint)
        GEN.apply_append_only(self.path, "old\nbody\nnew\n")
        self.assertEqual(self.path.read_bytes(), original + b"new\r\n")
        self.assertEqual(self.backup.read_bytes(), checkpoint)

    def test_invalid_utf8_is_refused_before_mutation(self):
        original = b"old\xff\n"
        self.seed(original)
        with self.assertRaises(UnicodeDecodeError):
            GEN.apply_append_only(self.path, "old\ufffd\nnew\n")
        self.assertEqual(self.path.read_bytes(), original)
        self.assertFalse(self.backup.exists())

    def test_existing_node_is_never_overwritten(self):
        node = self.root / "0001-existing.md"
        original = b"original\nnode\r\n"
        node.write_bytes(original)
        with self.assertRaises(FileExistsError):
            GEN.write_new_node(node, "replacement\n")
        self.assertEqual(node.read_bytes(), original)

    def test_ingest_preserves_leading_separators_and_appendix_text(self):
        for prefix in ('\n','\n\n','\n\n\n','Append-only annotation\n\n'):
            for eol in ('\n','\r\n'):
                with self.subTest(prefix=prefix,eol=eol),tempfile.TemporaryDirectory() as tmp:
                    self.root=Path(tmp)
                    path,original=self.fixture()
                    addition=(prefix+'### 2026-09-12 -- Added\nnew\n\n\n### 2026-09-13 -- Added again\nsecond\n').replace('\n',eol).encode('ascii')
                    path.write_bytes(original+addition)
                    historical=(self.root/'Calendar/decisions/records/0000-existing.md').read_bytes()
                    rc,out,err=self.run_main('--ingest')
                    self.assertEqual(rc,0,out+err)
                    rc,out,err=self.run_main('--apply')
                    self.assertEqual(rc,0,out+err)
                    self.assertEqual(path.read_bytes(),original+addition)
                    self.assertEqual((self.root/'Calendar/decisions/records/0000-existing.md').read_bytes(),historical)

    def test_ingest_without_a_heading_refuses_before_node_write(self):
        path,original=self.fixture()
        path.write_bytes(original+b'\nUnstructured appendix without a dated heading\n')
        snapshot=self.snapshot()
        with self.assertRaisesRegex(SystemExit,'no nodes written'):
            self.run_main('--ingest')
        self.assertEqual(self.snapshot(),snapshot)

    def fixture(self, *, extra_node=False, changed_node=False):
        spec = GEN.al.LEDGERS["decisions"]
        path = self.root / spec["file"]
        path.parent.mkdir(parents=True)
        original = b"# Ledger\r\n\n### 2026-09-11 -- Existing\r\nold\n"
        path.write_bytes(original)
        nodes = self.root / spec["node_dir"]
        nodes.mkdir(parents=True)
        body = "\n### 2026-09-11 -- Existing\n" + ("changed\n" if changed_node else "old\n")
        (nodes / "0000-existing.md").write_bytes(body.encode("utf-8"))
        if extra_node:
            (nodes / "0001-added.md").write_bytes(b"\n### 2026-09-12 -- Added\nnew\n")
        return path, original

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
                for p in self.root.rglob("*") if p.is_file()}

    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(GEN, "ROOT", self.root):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = GEN.main(["--ledger", "decisions", *args])
        return rc, out.getvalue(), err.getvalue()

    def test_check_is_read_only_and_labels_text_equality_precisely(self):
        self.fixture()
        before = self.snapshot()
        rc, out, err = self.run_main("--check")
        self.assertEqual(rc, 0, err)
        self.assertIn("TEXT-EQUIVALENT (newline-normalized; not a byte-equality proof)", out)
        self.assertNotIn("BYTE-IDENTICAL", out)
        self.assertEqual(self.snapshot(), before)

    def test_check_detects_extension_without_writing(self):
        self.fixture(extra_node=True)
        before = self.snapshot()
        rc, out, err = self.run_main("--check")
        self.assertEqual(rc, 1, err)
        self.assertIn("TEXT-DIFFERS", out)
        self.assertEqual(self.snapshot(), before)

    def test_explicit_check_cannot_ingest_or_apply(self):
        self.fixture(extra_node=True)
        before = self.snapshot()
        for mode in ("--ingest", "--apply"):
            with self.subTest(mode=mode), self.assertRaises(SystemExit) as raised:
                self.run_main("--check", mode)
            self.assertEqual(raised.exception.code, 2)
        self.assertEqual(self.snapshot(), before)

    def test_apply_appends_then_repeated_apply_does_not_touch_files(self):
        path, original = self.fixture(extra_node=True)
        rc, out, err = self.run_main("--apply")
        self.assertEqual(rc, 0, err)
        self.assertIn("existing physical bytes preserved", out)
        self.assertEqual(path.read_bytes(), original + b"\n### 2026-09-12 -- Added\nnew\n")
        self.assertEqual(path.with_suffix(".md.pre-regen").read_bytes(), original)
        before = self.snapshot()
        rc, out, err = self.run_main("--apply")
        self.assertEqual(rc, 0, err)
        self.assertIn("appended 0 bytes", out)
        self.assertEqual(self.snapshot(), before)

    def test_apply_historical_change_returns_failure_without_mutation(self):
        self.fixture(changed_node=True)
        before = self.snapshot()
        rc, out, err = self.run_main("--apply")
        self.assertEqual(rc, 1)
        self.assertIn("REFUSED:", err)
        self.assertIn("changes existing ledger content", err)
        self.assertEqual(self.snapshot(), before)


class TableLedgerIngestTests(unittest.TestCase):
    """Frozen controls for verified table tails, using only temporary fixtures."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.serial = 0

    def fixture(self, key, *, addition=None):
        self.serial += 1
        root = self.root / (key + str(self.serial))
        spec = GEN.al.LEDGERS[key]
        path = root / spec["file"]
        path.parent.mkdir(parents=True)
        nodes = root / spec["node_dir"]
        nodes.mkdir(parents=True)
        if key == "eod":
            rows = ["| EOD-1 | First synthetic event |", "| EOD-2 | Second synthetic event |"]
            extra = ["| EOD-39 | New synthetic event |", "| EOD-40 | Another synthetic event |"]
            header = "| ID | Event |\n| --- | --- |\n"
        else:
            rows = ["| 2026-09-11 | systems | First synthetic insight | open |",
                    "| 2026-09-12 | systems | Second synthetic insight | open |"]
            extra = ["| 2026-09-13 | systems | New synthetic insight | open |",
                     "| 2026-09-13 | systems | Another synthetic insight | open |"]
            header = "| Date | Domains | Insight | Status |\n| --- | --- | --- | --- |\n"
        body = "# Synthetic ledger\n\n" + header + "\n".join(rows) + "\n\nHistorical footer.\n"
        original = body.replace("\n", "\r\n").encode("ascii")
        tail = ("\r\n" + "\r\n".join(extra) + "\r\n").encode("ascii") if addition is None else addition
        path.write_bytes(original + tail)
        baseline = root / "pre-append.md"
        baseline.write_bytes(original)
        parse = GEN.al.parse_eod_rows if key == "eod" else GEN.al.parse_insight_rows
        historical = []
        for seq, (rid, line) in enumerate(parse(body)):
            name = self.name(key, seq, rid)
            date = "2026-07-04" if key == "eod" else rid[:10]
            node = nodes / name
            node.write_bytes((GEN.al.fm_text(spec["categories"], spec["type"], date, str(rid)) + line + "\n").encode("utf-8"))
            historical.append(node)
        (nodes / "INDEX.md").write_bytes(b"Synthetic index intentionally not an admission boundary.\n")
        return {"root": root, "key": key, "spec": spec, "path": path, "nodes": nodes,
                "baseline": baseline, "digest": hashlib.sha256(original).hexdigest(),
                "original": original, "tail": tail, "historical": historical}

    def name(self, key, seq, rid):
        return (f"{seq:04d}-{GEN.al.slugify(rid, 40)}.md" if key == "eod"
                else f"{seq:04d}-{rid[:10]}.md")

    def pending(self, case):
        parse = GEN.al.parse_eod_rows if case["key"] == "eod" else GEN.al.parse_insight_rows
        result = []
        for seq, (rid, line) in enumerate(parse(case["tail"].decode("utf-8")), start=2):
            date = "2026-07-04" if case["key"] == "eod" else rid[:10]
            text = GEN.al.fm_text(case["spec"]["categories"], case["spec"]["type"], date, str(rid)) + line + "\n"
            result.append((case["nodes"] / self.name(case["key"], seq, rid), text.encode("utf-8")))
        return result

    def run_case(self, case, *args, baseline=True):
        options = ["--ledger", case["key"], *args]
        if baseline:
            options += ["--ingest-baseline", str(case["baseline"]),
                        "--ingest-baseline-sha256", case["digest"]]
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(GEN, "ROOT", case["root"]), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = GEN.main(options)
        return code, out.getvalue(), err.getvalue()

    def snapshot(self, case):
        return {p.relative_to(case["root"]).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
                for p in case["root"].rglob("*") if p.is_file()}

    def assert_refused_unchanged(self, case, *args, baseline=True):
        before = self.snapshot(case)
        code, out, err = self.run_case(case, *(args or ("--ingest", "--apply")), baseline=baseline)
        self.assertEqual(code, 1, out + err)
        self.assertIn("REFUSED:", err)
        self.assertEqual(self.snapshot(case), before)

    def test_table_append_preserves_crlf_bytes_and_repeated_run_is_noop(self):
        for key in ("eod", "insights"):
            with self.subTest(key=key):
                case = self.fixture(key)
                old = {p: p.read_bytes() for p in case["historical"]}
                code, out, err = self.run_case(case, "--ingest", "--apply")
                self.assertEqual(code, 0, out + err)
                self.assertEqual(case["path"].read_bytes(), case["original"] + case["tail"])
                self.assertEqual({p: p.read_bytes() for p in case["historical"]}, old)
                self.assertFalse(case["path"].with_suffix(".md.pre-regen").exists())
                for path, data in self.pending(case):
                    self.assertEqual(path.read_bytes(), data)
                before = self.snapshot(case)
                code, out, err = self.run_case(case, "--ingest", "--apply")
                self.assertEqual(code, 0, out + err)
                self.assertEqual(self.snapshot(case), before)

    def test_table_changed_prefix_and_truncation_are_refused(self):
        for key in ("eod", "insights"):
            for edit in (lambda b: b.replace(b"Historical footer", b"Rewritten footer", 1),
                         lambda b: b.replace(b"\r\n", b"\n", 1), lambda b: b[:20]):
                with self.subTest(key=key, edit=edit):
                    case = self.fixture(key)
                    case["path"].write_bytes(edit(case["path"].read_bytes()))
                    self.assert_refused_unchanged(case)

    def test_table_deleted_historical_last_or_interior_node_is_not_recreated(self):
        for key in ("eod", "insights"):
            for index in (0, 1):
                with self.subTest(key=key, index=index):
                    case = self.fixture(key)
                    case["historical"][index].unlink()
                    self.assert_refused_unchanged(case)

    def test_table_changed_historical_body_is_refused(self):
        for key in ("eod", "insights"):
            case = self.fixture(key)
            node = case["historical"][0]
            node.write_bytes(node.read_bytes().replace(b"First synthetic", b"Changed synthetic"))
            self.assert_refused_unchanged(case)

    def test_table_baseline_path_and_digest_are_required(self):
        for key in ("eod", "insights"):
            for extra in ([], ["--ingest-baseline"], ["--ingest-baseline-sha256"]):
                with self.subTest(key=key, extra=extra):
                    case = self.fixture(key)
                    values = ([] if not extra else extra + [str(case["baseline"]) if extra[0] == "--ingest-baseline" else case["digest"]])
                    before = self.snapshot(case)
                    code, out, err = self.run_case(case, "--ingest", *values, baseline=False)
                    self.assertEqual(code, 1, out + err)
                    self.assertIn("baseline", err.lower())
                    self.assertEqual(self.snapshot(case), before)

    def test_table_wrong_malformed_or_missing_baseline_fails(self):
        for key in ("eod", "insights"):
            for problem in ("wrong", "malformed", "missing", "changed"):
                with self.subTest(key=key, problem=problem):
                    case = self.fixture(key)
                    if problem in ("wrong", "malformed"):
                        case["digest"] = "0" * 64 if problem == "wrong" else "not-a-digest"
                    elif problem == "missing":
                        case["baseline"].unlink()
                    else:
                        case["baseline"].write_bytes(case["original"] + b"Changed baseline\r\n")
                    self.assert_refused_unchanged(case)

    def test_table_suffix_collision_or_tampering_refuses_before_any_new_node(self):
        for key in ("eod", "insights"):
            for tamper in (lambda b: b + b"tampered\n", lambda b: b.replace(b"\n", b"\r\n")):
                with self.subTest(key=key, tamper=tamper):
                    case = self.fixture(key)
                    path, data = self.pending(case)[1]
                    path.write_bytes(tamper(data))
                    self.assert_refused_unchanged(case)

    def test_table_unknown_identity_or_sequence_hole_is_refused(self):
        for key in ("eod", "insights"):
            for name in ("0002-wrong-identity.md", "0009-unexplained.md", "notes.md"):
                with self.subTest(key=key, name=name):
                    case = self.fixture(key)
                    (case["nodes"] / name).write_bytes(b"Unexplained synthetic node\n")
                    self.assert_refused_unchanged(case)
            case = self.fixture(key)
            path, data = self.pending(case)[1]
            path.write_bytes(data)
            self.assert_refused_unchanged(case)

    def test_table_interrupted_suffix_resumes_exact_nodes_without_duplicates(self):
        for key in ("eod", "insights"):
            with self.subTest(key=key):
                case = self.fixture(key)
                first, data = self.pending(case)[0]
                first.write_bytes(data)
                os.utime(first, ns=(2_000_000_000, 2_000_000_000))
                before_time = first.stat().st_mtime_ns
                code, out, err = self.run_case(case, "--ingest", "--apply")
                self.assertEqual(code, 0, out + err)
                self.assertIn("INGESTED 1", out)
                self.assertEqual(first.read_bytes(), data)
                self.assertEqual(first.stat().st_mtime_ns, before_time)
                self.assertEqual(len(list(case["nodes"].glob("*.md"))), 5)
                self.assertEqual(case["path"].read_bytes(), case["original"] + case["tail"])

    def test_table_nonrow_or_malformed_suffix_is_refused(self):
        for key in ("eod", "insights"):
            for extra in (b"\r\nUnstructured appended text\r\n", b"\r\n| Missing closing pipe\r\n"):
                with self.subTest(key=key, extra=extra):
                    case = self.fixture(key)
                    case["path"].write_bytes(case["path"].read_bytes() + extra)
                    self.assert_refused_unchanged(case)

    def test_table_missing_historical_node_refuses_even_without_new_rows(self):
        for key in ("eod", "insights"):
            case = self.fixture(key, addition=b"")
            case["historical"][-1].unlink()
            self.assert_refused_unchanged(case)

    def test_table_check_stays_read_only_and_baseline_flags_do_not_enable_ingest(self):
        for key in ("eod", "insights"):
            case = self.fixture(key)
            self.assert_refused_unchanged(case, "--check")

    def test_table_ingest_without_baseline_allows_only_verified_noop(self):
        for key in ("eod", "insights"):
            with self.subTest(key=key):
                case = self.fixture(key, addition=b"")
                before = self.snapshot(case)
                for mode in (("--ingest",), ("--ingest", "--apply")):
                    code, out, err = self.run_case(case, *mode, baseline=False)
                    self.assertEqual(code, 0, out + err)
                    self.assertIn("TEXT-EQUIVALENT", out)
                    self.assertEqual(self.snapshot(case), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
