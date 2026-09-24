"""Build a deterministic portable plugin from an exact reviewed source allowlist.

No vault scan, arbitrary paths, credentials, account data, app permissions or
installation. Canonical edits stay in .agents/skills and tools/fis. ZIP output
is a local artifact for the user's own import into a supported host.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/fis"))
from workbench import canonical, safe_path

SKILL_FILES = ("SKILL.md", "ref-packet.md", "ref-package.md", "ref-review.md", "ref-capabilities.md", "agents/openai.yaml",
               "scripts/workbench.py", "assets/synthetic-company.json", "assets/synthetic-dcf.json",
               "assets/synthetic-cashflow.json", "assets/msft-historical.json")
RUNTIME_FILES = ("workbench.py", "evidence.py", "valuation.py", "provenance.py", "cashflow.py", "report_review.py", "reviewer_execution.py", "capabilities.py",
                 "test_workbench.py", "test_cashflow.py")


def source_map():
    result = {".codex-plugin/plugin.json": "config/finance-data-plugin.json"}
    result.update({"skills/finance-data/" + n: ".agents/skills/finance-data/" + n for n in SKILL_FILES})
    result.update({"tools/fis/" + n: "tools/fis/" + n for n in RUNTIME_FILES})
    result["README.md"] = ".agents/skills/finance-data/ref-package.md"
    return result


def library_bytes(root=ROOT):
    """Package only currently admitted, explicitly reusable method spans.

    Source snapshots, inventories, unapproved adjacent text and the host index
    are excluded. Revalidate admission and source bytes at every build/verify.
    """
    sys.path.insert(0, str(ROOT / "tools/pit"))
    from financial_documents import approved_document_manifest
    root = Path(root).resolve()
    registry = root / "Efforts/osanwe-v2-overhaul/_work/fis-data/financial-document-registry.jsonl"
    manifest = approved_document_manifest(registry, root, scope="portable-context")
    if not manifest["documents"]:
        raise ValueError("no currently admitted portable method passages")
    passages = []
    for document in manifest["documents"]:
        if document["classification"] not in {"PUBLIC", "SYNTHETIC"} or "reuse" not in document:
            raise ValueError("portable source requires explicit privacy and reuse admission")
        path = safe_path(root / document["source_path"])
        if not path.is_relative_to(root):
            raise ValueError("escaped library source")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != document["sha256"]:
            raise ValueError("library source changed during publication")
        for chunk in document["chunks"]:
            excerpt = raw[chunk["start_byte"]:chunk["end_byte"]].decode("utf-8")
            passages.append({"document_id": document["document_id"],
                             "source_version": document["source_version"],
                             "chunk_id": chunk["chunk_id"], "locator": chunk["locator"],
                             "source_sha256": document["sha256"], "text": excerpt,
                             "excerpt_sha256": hashlib.sha256(excerpt.encode("utf-8")).hexdigest()})
    # The generation clock is a build observation, not part of deterministic
    # knowledge contents. All revision/availability/inspection dates stay bound.
    provenance = {key: value for key, value in manifest.items()
                  if key not in {"generated_at", "exclusions"}}
    result = {"knowledge/passages.json": canonical({"schema": "osanwe.portable-knowledge/1", "passages": passages}) + b"\n",
              "knowledge/source-records.json": canonical(provenance) + b"\n"}
    if any(len(value) > 1_000_000 for value in result.values()):
        raise ValueError("portable knowledge exceeds bounded package size")
    return result


def source_bytes(root=ROOT, *, with_library=False):
    root = Path(root).resolve()
    result, provenance = {}, {}
    for target, rel in source_map().items():
        lexical = root / rel
        path = safe_path(lexical)
        # Every component must stay in the source root; linked files/parents are
        # refused even if they happen to point to another reviewed source today.
        if not path.is_relative_to(root) or path != lexical.absolute():
            raise ValueError("linked or escaped package source")
        for parent in (lexical, *lexical.parents):
            if parent == root:
                break
            if parent.is_symlink() or getattr(parent, "is_junction", lambda: False)():
                raise ValueError("linked package source")
        data = path.read_bytes()
        if len(data) > 1_000_000:
            raise ValueError("unexpectedly large package source")
        # Python/Markdown/JSON/YAML sources are portable text. Normalize only
        # the generated copy, never historical or canonical source bytes.
        data = data.replace(b"\r\n", b"\n")
        data.decode("utf-8")
        result[target] = data
        provenance[target] = {"source": rel, "sha256": hashlib.sha256(data).hexdigest()}
    manifest = json.loads(result[".codex-plugin/plugin.json"])
    if manifest.get("name") != "osanwe-finance-data" or manifest.get("skills") != "./skills/":
        raise ValueError("unexpected plugin identity or skill path")
    if any(k in manifest for k in ("apps", "mcpServers", "hooks")):
        raise ValueError("portable context must not gain app, MCP or hook authority")
    if with_library:
        for target, data in library_bytes(root).items():
            result[target] = data
            provenance[target] = {"source": "current admitted portable-context passages",
                                  "sha256": hashlib.sha256(data).hexdigest()}
    result["SOURCE-MANIFEST.json"] = canonical({"schema": "osanwe.context-package/1",
        "version": manifest["version"], "audience": "existing personal Osanwe workspace and its own portable host",
        "classification": "curated source code and public/synthetic examples; no account records",
        "canonical_editing_sources": ".agents/skills/finance-data and tools/fis in the full workspace",
        "normalization": "generated source copies use LF; canonical source bytes are untouched",
        "files": provenance}) + b"\n"
    return result


def package_bytes(root=ROOT, *, with_library=False):
    files = source_bytes(root, with_library=with_library)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    result = stream.getvalue()
    verify_bytes(result, root, with_library=with_library)
    return result


def verify_bytes(data, root=ROOT, *, with_library=False):
    expected = source_bytes(root, with_library=with_library)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        if len(set(names)) != len(names) or set(names) != set(expected):
            raise ValueError("package member set differs from reviewed sources")
        for info in archive.infolist():
            if info.file_size > 1_000_000 or (info.external_attr >> 16) & 0o170000 != 0o100000:
                raise ValueError("package requires bounded regular files")
            if archive.read(info.filename) != expected[info.filename]:
                raise ValueError("package content differs from current reviewed source")
        if archive.testzip() is not None:
            raise ValueError("package CRC failure")
    return {"verified": True, "files": len(expected), "sha256": hashlib.sha256(data).hexdigest(),
            "scope": "portable package byte integrity; no remote install or live connector verification"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--out")
    group.add_argument("--verify")
    ap.add_argument("--with-library", action="store_true", help="include only admitted portable-context passages with explicit reuse rights")
    args = ap.parse_args()
    try:
        if args.verify:
            result = verify_bytes(safe_path(args.verify).read_bytes(), with_library=args.with_library)
        else:
            target = safe_path(args.out, must_exist=False)
            if target.suffix.casefold() != ".zip" or target.exists():
                raise ValueError("choose a new .zip output path")
            data = package_bytes(with_library=args.with_library)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as f:
                f.write(data)
            result = verify_bytes(data, with_library=args.with_library)
            result["path"] = str(target)
        print(canonical(result).decode())
        return 0
    except (ValueError, OSError, zipfile.BadZipFile) as exc:
        print(canonical({"status": "refused", "reason": str(exc)}).decode())
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
