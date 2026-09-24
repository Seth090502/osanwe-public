"""Portable plugin byte-closure and isolated runtime acceptance tests."""
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
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("package_finance_data",ROOT/"tools/package-finance-data.py")
package=importlib.util.module_from_spec(spec);spec.loader.exec_module(package)


class PackageTests(unittest.TestCase):
    def library_fixture(self):
        sys.path.insert(0, str(ROOT / "tools/pit"))
        import test_financial_documents as fixtures
        import financial_documents as documents
        case = fixtures.DocumentAdmissionTests()
        case.setUp()
        self.addCleanup(case.doCleanups)
        candidate = case.candidate()
        candidate["approved_use"].append("portable-context")
        candidate["chunks"][0]["approved_use"].append("portable-context")
        candidate["reuse"] = {"basis": "original_authorship", "document_sha256": candidate["sha256"],
                             "reviewed_by": "reviewer:fixture", "reviewed_at": fixtures.STAMP,
                             "scope": "approved_chunks_only", "evidence": "Original synthetic test text authored for this regression.",
                             "sources_included": False}
        registry = case.root / "Efforts/osanwe-v2-overhaul/_work/fis-data/financial-document-registry.jsonl"
        registry.parent.mkdir(parents=True)
        documents.append_document_version(registry, candidate, case.root, admitted_at=fixtures.STAMP)
        return case

    def test_library_contains_only_admitted_reusable_spans_and_source_metadata(self):
        case = self.library_fixture()
        files = package.library_bytes(case.root)
        self.assertEqual(set(files), {"knowledge/passages.json", "knowledge/source-records.json"})
        records = json.loads(files["knowledge/source-records.json"])
        self.assertEqual(len(records["documents"]), 1)
        self.assertTrue(records["documents"][0]["reuse"]["sources_included"] is False)
        self.assertNotIn("Operating margin equals operating income", files["knowledge/passages.json"].decode())
        self.assertEqual(files, package.library_bytes(case.root))

    def test_source_change_and_missing_admission_refuse_library_packaging(self):
        case = self.library_fixture()
        (case.root / "docs/margin.md").write_text("Changed method after admission")
        with self.assertRaises(ValueError):
            package.library_bytes(case.root)
        with tempfile.TemporaryDirectory() as empty:
            with self.assertRaises((ValueError, OSError)):
                package.library_bytes(empty)

    def test_deterministic_exact_allowlist(self):
        a=package.package_bytes();b=package.package_bytes()
        self.assertEqual(a,b)
        self.assertTrue(package.verify_bytes(a)["verified"])
        with zipfile.ZipFile(io.BytesIO(a)) as archive:
            self.assertIn(".codex-plugin/plugin.json",archive.namelist())
            self.assertEqual(len(archive.namelist()),len(package.source_map())+1)
            self.assertFalse(any(n.startswith(("wiki/","Calendar/","private/","finance/")) for n in archive.namelist()))

    def test_extra_traversal_duplicate_and_modified_members_refuse(self):
        data=package.package_bytes()
        for mode in ("extra","traversal","duplicate","changed"):
            stream=io.BytesIO()
            with zipfile.ZipFile(io.BytesIO(data)) as original,zipfile.ZipFile(stream,"w") as target:
                for info in original.infolist():
                    b=original.read(info.filename)
                    if mode=="changed" and info.filename=="README.md":b+=b'\nchanged\n'
                    target.writestr(info,b)
                if mode=="extra":target.writestr("unreviewed.txt","extra")
                if mode=="traversal":target.writestr("../escaped.txt","escape")
                if mode=="duplicate":
                    import warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore",UserWarning);target.writestr("README.md","duplicate")
            with self.subTest(mode=mode),self.assertRaises(ValueError):package.verify_bytes(stream.getvalue())

    def test_source_changes_and_linked_source_refuse(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"source";root.mkdir()
            for rel in set(package.source_map().values()):
                p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,p)
            before=package.package_bytes(root)
            p=root/"tools/fis/evidence.py";p.write_bytes(p.read_bytes()+b'\n# changed\n')
            with self.assertRaises(ValueError):package.verify_bytes(before,root)
            # Attempt a real symlink where the host supports it. Byte mutation
            # rejection above always runs, independently of symlink privileges.
            link=root/"tools/fis/valuation.py";data=link.read_bytes();link.unlink()
            outside=Path(td)/"outside.py";outside.write_bytes(data)
            try:link.symlink_to(outside)
            except OSError:
                link.write_bytes(data)
            else:
                with self.assertRaises(ValueError):package.package_bytes(root)

    def test_isolated_portable_runtime_all_examples_and_suites(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            data=package.package_bytes()
            # verify_bytes pins exact regular members before extraction.
            package.verify_bytes(data)
            with zipfile.ZipFile(io.BytesIO(data)) as archive:archive.extractall(root)
            clean_env={k:v for k,v in os.environ.items() if k.upper() in {"PATH","SYSTEMROOT","WINDIR","TEMP","TMP","PATHEXT"}}
            clean_env["PYTHONDONTWRITEBYTECODE"]="1"
            for script in ("test_workbench.py","test_cashflow.py"):
                r=subprocess.run([sys.executable,"-B",str(root/"tools/fis"/script)],cwd=root,env=clean_env,capture_output=True,text=True,timeout=60)
                self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            for name in ("synthetic-company","synthetic-dcf","synthetic-cashflow","msft-historical"):
                source=root/"skills/finance-data/assets"/(name+".json")
                out=root/name
                command=[sys.executable,"-B",str(root/"skills/finance-data/scripts/workbench.py")]
                for args in (["run",str(source),"--outdir",str(out)],["verify",str(source),str(out)]):
                    r=subprocess.run(command+args,cwd=root,env=clean_env,capture_output=True,text=True,timeout=30)
                    self.assertEqual(r.returncode,0,r.stdout+r.stderr)
                    self.assertNotIn("refused",json.loads(r.stdout))
            self.assertFalse((root/"Efforts").exists(),"default persistent provenance store must not be created")

    def test_portable_review_cli_preserves_and_rejects_changed_artifact(self):
        # This test-only fixture generator is not a runtime dependency. The
        # isolated child receives only the packaged runtime and synthetic data.
        sys.path.insert(0, str(ROOT / "tools/fis"))
        from test_report_review import fixture
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            case = root / "case"
            case.mkdir()
            packet, bundle, request, assets = fixture(case)
            runtime = root / "runtime"
            runtime.mkdir()
            data = package.package_bytes()
            package.verify_bytes(data)
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                archive.extractall(runtime)
            packet_path = case / "packet.json"
            request_path = case / "request.json"
            packet_path.write_text(json.dumps(packet), encoding="ascii")
            request_path.write_text(json.dumps(request), encoding="ascii")
            clean_env = {k:v for k,v in os.environ.items() if k.upper() in
                         {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATHEXT"}}
            clean_env["PYTHONDONTWRITEBYTECODE"] = "1"
            command = [sys.executable, "-B", str(runtime / "tools/fis/workbench.py")]
            archive_path = case / "review-archive"
            args = ["review", str(packet_path), str(bundle), str(request_path),
                    "--artifacts", str(assets), "--outdir", str(archive_path)]
            prepared = subprocess.run(command + args + ["--prepare", "--reviewer-id", "reviewer:portable",
                                      "--reviewer-model", "synthetic-model", "--reviewer-effort", "xhigh"],
                                      cwd=runtime, env=clean_env, capture_output=True, text=True, timeout=30)
            self.assertEqual(prepared.returncode, 0, prepared.stdout + prepared.stderr)
            context = json.loads(prepared.stdout)
            contract = context["producer_contract"]
            self.assertEqual(contract["context_sha256"], context["context_sha256"])
            schema = contract["output_schema"]["properties"][contract["response_key"]]["properties"]
            self.assertEqual(schema["coverage"]["const"], context["required_coverage"])
            self.assertIn("pattern", schema["disagreements"]["items"])
            # Import the new execution helper from the extracted package with
            # no workspace Python path or dependency fallback available.
            probe = subprocess.run([sys.executable, "-B", "-c",
                                    "import sys; sys.path.insert(0, 'tools/fis'); import reviewer_execution"],
                                   cwd=runtime, env=clean_env, capture_output=True, text=True, timeout=30)
            self.assertEqual(probe.returncode, 0, probe.stdout + probe.stderr)
            result = subprocess.run(command + args, cwd=runtime, env=clean_env,
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "accepted")
            report = archive_path / "artifacts/report.txt"
            report.write_text("Edited economic conclusion", encoding="ascii")
            result = subprocess.run(command + ["verify-review", str(archive_path)],
                                    cwd=runtime, env=clean_env, capture_output=True,
                                    text=True, timeout=30)
            self.assertNotEqual(result.returncode, 0, "Changed delivered bytes must fail")
            self.assertFalse((runtime / "Efforts").exists())


if __name__=="__main__":unittest.main()
