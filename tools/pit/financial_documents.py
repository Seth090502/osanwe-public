"""Public/synthetic document records owned by the existing FIS dataset registry.

Admission proves bounded source inspection, calculation and byte/scope contracts.
It does not prove source authenticity, semantic entailment or expert certification.
Privacy classification is explicit and bound to inspected bytes; a path is never
classification evidence. Unreviewed inventory never opens or hashes document bodies.
"""
from __future__ import annotations

import copy
import ast
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
from hashlib import sha256
from fractions import Fraction
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[2]
DOCUMENT_REGISTRY_OUT = ROOT / "Efforts/osanwe-v2-overhaul/_work/fis-data/financial-document-registry.jsonl"
DOCUMENT_SCHEMA = "osanwe.financial-document-version/1"
RETRACTION_SCHEMA = "osanwe.financial-document-retraction/1"
MANIFEST_SCHEMA = "osanwe.financial-document-manifest/1"
POLICY_VERSION = "1"
SAFE_CLASSES = {"PUBLIC", "SYNTHETIC"}
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,159}\Z")
VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
PRIVATE_MARKER = re.compile(r"PERSONAL[_ -]FINANCE[_ -]CANARY|(?:account[_ -]?(?:id|number)|access[_ -]?token|secret[_ -]?key)\s*[:=]\s*[\"']?[A-Za-z0-9_-]{6,}", re.I)
DENIED_PARTS = {".raw", "private", "finance", "credentials", ".git"}
MAX_BYTES = 4 * 1024 * 1024
DOCUMENT_FIELDS = set("schema document_id source_version source_origin_id source_uri source_path sha256 classification source_kind kind status approved_use applicability published_at available_at reviewed_at supersedes privacy_review sources claims chunks source_review worked_examples revision_status admission reuse validation_evidence".split())
SOURCE_FIELDS = set("source_id origin_id source_version uri snapshot_path sha256 classification source_kind retrieved_at available_at privacy_review published_at original_locator transformations reviewed_scope availability_basis source_version_label".split())
PRIVACY_FIELDS = set("classification sha256 reviewed_by reviewed_at scope".split())
RETRACTION_FIELDS = set("schema document_id source_version source_origin_id source_uri classification status revision_status supersedes available_at reviewed_at reviewed_by reason_code admission".split())


class DocumentAdmissionError(ValueError):
    """Public-safe reason codes only; never interpolate document data into errors."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _fail(code): raise DocumentAdmissionError(code)


def _fields(value, allowed):
    if not isinstance(value, dict) or not set(value) <= allowed: _fail("unexpected_metadata_fields")


def _safe_metadata(value):
    try: encoded = _canonical(value)
    except (ValueError, TypeError, OverflowError): _fail("invalid_public_metadata")
    if len(encoded) > MAX_BYTES: _fail("metadata_too_large")
    if PRIVATE_MARKER.search(encoded.decode("ascii")): _fail("privacy_marker")


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def _digest(value): return sha256(_canonical(value)).hexdigest()


def _identifier(value, version=False):
    if not isinstance(value, str) or not (VERSION if version else ID).fullmatch(value): _fail("invalid_identifier")
    return value


def _strings(value, *, nonempty=False, identifiers=False):
    if not isinstance(value, list) or (nonempty and not value) or any(not isinstance(x, str) or not x.strip() or len(x) > 4000 for x in value):
        _fail("invalid_string_list")
    if len(set(value)) != len(value): _fail("duplicate_identifier")
    if identifiers:
        for item in value: _identifier(item)
    return value


def _stamp(value):
    if not isinstance(value, str): _fail("invalid_timestamp")
    try: result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError: _fail("invalid_timestamp")
    if result.tzinfo is None or result.utcoffset() is None: _fail("invalid_timestamp")
    return result.astimezone(timezone.utc)


def _now(): return datetime.now(timezone.utc).isoformat()


def _uri(value):
    if not isinstance(value, str) or len(value) > 2048: _fail("invalid_source_uri")
    if value.startswith(("synthetic:", "urn:osanwe:")):
        if not re.fullmatch(r"[A-Za-z0-9:/_.-]+", value): _fail("invalid_source_uri")
        return value
    try: parsed = urlsplit(value)
    except ValueError: _fail("invalid_source_uri")
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        _fail("invalid_source_uri")
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/", parsed.query, ""))


def _path(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative or any(ord(char) < 32 for char in relative):
        _fail("unsafe_path")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or any(x in ("..", ".") for x in pure.parts): _fail("unsafe_path")
    if any(x.lower() in DENIED_PARTS or x.lower().startswith(".env") or x.lower() == "auth.json" or x.lower().endswith(".local.md") for x in pure.parts):
        _fail("unsafe_path")
    root = Path(root).resolve()
    if any(part.lower() in DENIED_PARTS for part in root.parts): _fail("unsafe_path")
    current = root
    for part in pure.parts:
        current = current / part
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()): _fail("unsafe_path")
    if not current.resolve().is_relative_to(root): _fail("unsafe_path")
    return current


def _privacy(record, *, path_key):
    # This complete metadata preflight runs for ALL document and supporting
    # sources before any source file is opened, hashed or excerpted.
    if not isinstance(record, dict) or record.get("classification") not in SAFE_CLASSES: _fail("classification_not_approved")
    digest = record.get("sha256")
    if not isinstance(digest, str) or not SHA.fullmatch(digest): _fail("invalid_public_hash")
    privacy = record.get("privacy_review")
    _fields(privacy, PRIVACY_FIELDS)
    if not isinstance(privacy, dict) or privacy.get("classification") != record["classification"] or privacy.get("sha256") != digest or privacy.get("scope") != "whole_document":
        _fail("privacy_review_incomplete")
    _identifier(privacy.get("reviewed_by"))
    _stamp(privacy.get("reviewed_at"))
    if not isinstance(record.get(path_key), str): _fail("unsafe_path")


def _read(root, record, *, path_key):
    path = _path(root, record[path_key])
    if not path.is_file(): _fail("source_unavailable")
    try:
        if path.stat().st_size > MAX_BYTES: _fail("source_too_large")
        raw = path.read_bytes()
    except OSError: _fail("source_unavailable")
    if len(raw) > MAX_BYTES: _fail("source_too_large")
    if sha256(raw).hexdigest() != record["sha256"]: _fail("source_hash_mismatch")
    try: text = raw.decode("utf-8")
    except UnicodeError: _fail("source_encoding_unsupported")
    if PRIVATE_MARKER.search(text): _fail("privacy_marker")
    return raw, text


def _locator(text, locator, *, inspected=False):
    if not isinstance(locator, dict): _fail("invalid_locator")
    start, end = locator.get("start_line"), locator.get("end_line")
    lines = text.splitlines(keepends=True)
    if type(start) is not int or type(end) is not int or not (1 <= start <= end <= len(lines)):
        _fail("invalid_locator")
    excerpt = "".join(lines[start - 1:end])
    if inspected and locator.get("text") != excerpt: _fail("locator_text_mismatch")
    heading = locator.get("heading")
    if heading is not None:
        preceding = [re.sub(r"^#{1,6}\s+", "", line.strip()).strip() for line in lines[:start] if re.match(r"^#{1,6}\s+", line)]
        if not isinstance(heading, str) or not preceding or preceding[-1] != heading: _fail("locator_heading_mismatch")
    start_char = len("".join(lines[:start - 1]))
    end_char = start_char + len(excerpt)
    return {"start_line": start, "end_line": end, "heading": heading,
            "start_char": start_char, "end_char": end_char,
            "start_byte": len(text[:start_char].encode("utf-8")), "end_byte": len(text[:end_char].encode("utf-8"))}


def _literal_fraction(expression):
    try: tree = ast.parse(expression, mode="eval")
    except (SyntaxError, ValueError, TypeError): _fail("worked_example_invalid")
    if len(list(ast.walk(tree))) > 256: _fail("worked_example_invalid")
    def visit(node, depth=0):
        if depth > 32: _fail("worked_example_invalid")
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            try: value = Fraction(str(node.value))
            except (ValueError, OverflowError): _fail("worked_example_invalid")
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            value = visit(node.operand, depth + 1) * (-1 if isinstance(node.op, ast.USub) else 1)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
            left, right = visit(node.left, depth + 1), visit(node.right, depth + 1)
            if isinstance(node.op, ast.Add): value = left + right
            elif isinstance(node.op, ast.Sub): value = left - right
            elif isinstance(node.op, ast.Mult): value = left * right
            elif isinstance(node.op, ast.Div):
                if right == 0: _fail("worked_example_invalid")
                value = left / right
            else:
                if right.denominator != 1 or abs(right.numerator) > 60 or (left == 0 and right < 0): _fail("worked_example_invalid")
                value = left ** right.numerator
        else: _fail("worked_example_invalid")
        if value.numerator.bit_length() > 8192 or value.denominator.bit_length() > 8192: _fail("worked_example_invalid")
        return value
    return visit(tree.body)


def _pointer(document, pointer):
    if not isinstance(pointer, str) or not pointer.startswith("/"): _fail("worked_example_evidence_missing")
    value = document
    try:
        for key in pointer[1:].split("/"):
            if isinstance(value, list):
                if not re.fullmatch(r"0|[1-9][0-9]*", key): _fail("worked_example_evidence_missing")
                value = value[int(key)]
            else: value = value[key]
    except (KeyError, TypeError, IndexError, ValueError): _fail("worked_example_evidence_missing")
    return value


def _example(example, evidence_blobs=None):
    if not isinstance(example, dict): _fail("worked_example_invalid")
    _identifier(example.get("example_id"))
    independent = example.get("independent_result", {})
    _fields(example, set("example_id inputs expression result unit currency independent_result mode basis evidence_ref".split()))
    _fields(independent, set("numerator denominator checked_by method".split()))
    _identifier(independent.get("checked_by"))
    if independent.get("method") != "exact_fraction" or type(independent.get("numerator")) is not int or type(independent.get("denominator")) is not int or independent["denominator"] <= 0:
        _fail("worked_example_invalid")
    if independent["numerator"].bit_length() > 4096 or independent["denominator"].bit_length() > 4096: _fail("worked_example_invalid")
    if not isinstance(example.get("expression"), str) or len(example["expression"]) > 4096: _fail("worked_example_invalid")
    if example.get("mode") == "literal_fixture":
        reference = example.get("evidence_ref", {})
        _fields(reference, {"evidence_id", "pointer", "code_evidence_id"})
        blobs = evidence_blobs or {}
        if reference.get("evidence_id") not in blobs or reference.get("code_evidence_id") not in blobs: _fail("worked_example_evidence_missing")
        try: receipt = json.loads(blobs[reference["evidence_id"]])
        except (ValueError, TypeError): _fail("worked_example_evidence_missing")
        if not isinstance(receipt, dict) or receipt.get("classification") != "SYNTHETIC" or receipt.get("passed") is not True or receipt.get("failures") != 0 or receipt.get("errors") != 0 or type(receipt.get("tests_run")) is not int or receipt["tests_run"] <= 0:
            _fail("worked_example_evidence_missing")
        if receipt.get("test_file_sha256") != sha256(blobs[reference["code_evidence_id"]]).hexdigest(): _fail("worked_example_evidence_missing")
        original = _pointer(receipt, reference.get("pointer"))
        if not isinstance(original, dict) or original.get("classification") != "SYNTHETIC" or any(original.get(key) != example.get(key) for key in ("example_id", "expression", "unit", "currency", "basis", "result")):
            _fail("worked_example_evidence_mismatch")
        expected_fraction = {key: independent[key] for key in ("numerator", "denominator")}
        if original.get("expected_fraction") != expected_fraction or example.get("inputs") != {}: _fail("worked_example_evidence_mismatch")
        actual = _literal_fraction(example["expression"])
        expected = Fraction(independent["numerator"], independent["denominator"])
        try:
            output = Decimal(str(example["result"]))
            if not output.is_finite(): _fail("worked_example_invalid")
            if actual != expected or abs(output - Decimal(expected.numerator) / Decimal(expected.denominator)) > Decimal("1e-12") * max(Decimal(1), abs(output)):
                _fail("worked_example_mismatch")
        except DocumentAdmissionError: raise
        except (InvalidOperation, ValueError, TypeError, OverflowError): _fail("worked_example_invalid")
        return {"example_id": example["example_id"], "result": str(example["result"]), "independent_method": "exact_fraction", "outcome": "pass",
                "unit_scope": "Labels agree with the bound synthetic test receipt; literal arithmetic does not independently establish financial unit semantics."}
    inputs = example.get("inputs")
    if not isinstance(inputs, dict) or not inputs or len(inputs) > 32: _fail("worked_example_invalid")
    for name, binding in inputs.items():
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", name) or not isinstance(binding, dict): _fail("worked_example_invalid")
        _fields(binding, {"value", "unit", "currency", "basis"})
        if type(binding.get("value")) not in (int, float) or any(not isinstance(binding.get(key), str) or not binding[key] for key in ("unit", "currency", "basis")):
            _fail("worked_example_invalid")
        if type(binding["value"]) is int and binding["value"].bit_length() > 4096: _fail("worked_example_invalid")
        if not Decimal(str(binding["value"])).is_finite(): _fail("worked_example_invalid")
    # Reuse the existing bounded financial expression/units implementation.
    # It supports only arithmetic over declared inputs, never function calls.
    fis = str(ROOT / "tools/fis")
    if fis not in sys.path: sys.path.insert(0, fis)
    import report_review
    try:
        with localcontext() as context:
            context.prec = 50
            value, dimensions = report_review._expression(example.get("expression"), inputs)
            output = Decimal(str(example.get("result")))
            reference = Decimal(independent["numerator"]) / Decimal(independent["denominator"])
            if not output.is_finite() or not value.is_finite(): _fail("worked_example_invalid")
            tolerance = Decimal("1e-12") * max(Decimal(1), abs(reference))
            if abs(value - reference) > tolerance or abs(output - reference) > tolerance: _fail("worked_example_mismatch")
    except DocumentAdmissionError: raise
    except (ValueError, TypeError, InvalidOperation, OverflowError, ZeroDivisionError): _fail("worked_example_invalid")
    unit, currency = example.get("unit"), example.get("currency")
    bases = {binding["basis"] for binding in inputs.values()}
    if len(bases) != 1: _fail("worked_example_units")
    expected = {} if unit in {"fraction", "ratio", "count", "percent", "percentage_points", "basis_points"} else {(unit, currency, next(iter(bases))): 1}
    if dimensions != expected or (not expected and currency != "NONE"): _fail("worked_example_units")
    return {"example_id": example["example_id"], "result": str(output), "independent_method": "exact_fraction", "outcome": "pass"}


def _indexed(values, key, *, nonempty=True):
    if not isinstance(values, list) or (nonempty and not values): _fail("required_evidence_missing")
    result = {}
    for value in values:
        if not isinstance(value, dict): _fail("required_evidence_missing")
        identifier = _identifier(value.get(key))
        if identifier in result: _fail("duplicate_identifier")
        result[identifier] = value
    return result


def _candidate_payload(record):
    if not isinstance(record, dict): _fail("classification_not_approved")
    result = copy.deepcopy(record)
    result.pop("admission", None)
    if result.get("status") == "approved": result["status"] = "candidate"
    return result


def _identity(): return sha256(Path(__file__).read_bytes()).hexdigest()


def _dependencies():
    # The typed example mode delegates unit-aware arithmetic to this owner.
    # Its changes also invalidate current admission; old records remain intact.
    return {"tools/fis/report_review.py": sha256((ROOT / "tools/fis/report_review.py").read_bytes()).hexdigest()}


def _validate_candidate(record, root, admitted_at):
    if not isinstance(record, dict) or record.get("classification") not in SAFE_CLASSES: _fail("classification_not_approved")
    sources = _indexed(record.get("sources"), "source_id")
    _privacy(record, path_key="source_path")
    for source in sources.values(): _privacy(source, path_key="snapshot_path")
    evidence = _indexed(record.get("validation_evidence", []), "evidence_id", nonempty=False)
    for item in evidence.values():
        _privacy(item, path_key="source_path")
        _fields(item, {"evidence_id", "source_path", "sha256", "classification", "privacy_review", "kind"})
    _fields(record, DOCUMENT_FIELDS)
    for source in sources.values(): _fields(source, SOURCE_FIELDS)
    _safe_metadata(record)
    _path(root, record["source_path"])
    for source in sources.values(): _path(root, source["snapshot_path"])
    for item in evidence.values(): _path(root, item["source_path"])
    if record.get("schema") != DOCUMENT_SCHEMA or record.get("status") not in ("candidate", "approved"): _fail("invalid_document_schema")
    for key in ("document_id", "source_origin_id", "kind", "source_kind"): _identifier(record.get(key))
    _identifier(record.get("source_version"), version=True)
    _uri(record.get("source_uri"))
    approved_use = _strings(record.get("approved_use"), nonempty=True, identifiers=True)
    applicability = record.get("applicability")
    if not isinstance(applicability, dict): _fail("applicability_missing")
    _fields(applicability, set("applies_when not_applicable_when required_inputs limitations alternatives".split()))
    for key in ("applies_when", "not_applicable_when", "required_inputs", "limitations", "alternatives"):
        _strings(applicability.get(key), nonempty=key in ("applies_when", "limitations"))
    available, reviewed, admitted = _stamp(record.get("available_at")), _stamp(record.get("reviewed_at")), _stamp(admitted_at)
    if not available <= reviewed <= admitted or _stamp(record["privacy_review"]["reviewed_at"]) > admitted: _fail("availability_violation")
    reuse = record.get("reuse")
    if "portable-context" in approved_use:
        if not isinstance(reuse, dict): _fail("portable_reuse_unapproved")
        _fields(reuse, {"basis", "document_sha256", "reviewed_by", "reviewed_at", "scope", "evidence", "sources_included", "license_uri"})
        if reuse.get("basis") not in ("original_authorship", "public_domain", "licensed_open", "permission_granted") or reuse.get("document_sha256") != record["sha256"] or reuse.get("scope") != "approved_chunks_only" or reuse.get("sources_included") is not False:
            _fail("portable_reuse_unapproved")
        _identifier(reuse.get("reviewed_by"))
        if _stamp(reuse.get("reviewed_at")) > admitted or not isinstance(reuse.get("evidence"), str) or not reuse["evidence"].strip(): _fail("portable_reuse_unapproved")
        if reuse["basis"] in ("licensed_open", "permission_granted"): _uri(reuse.get("license_uri"))
    published = record.get("published_at")
    if published is not None:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", published): published = published + "T00:00:00+00:00"
        if _stamp(published) > available: _fail("availability_violation")
    supersedes = record.get("supersedes")
    if not isinstance(supersedes, list) or len(set(supersedes)) != len(supersedes): _fail("invalid_supersession")
    source_texts, origin_uris = {}, {}
    for source_id, source in sources.items():
        _identifier(source.get("origin_id"))
        _identifier(source.get("source_version"), version=True)
        _identifier(source.get("source_kind"))
        uri = _uri(source.get("uri"))
        if uri in origin_uris and origin_uris[uri] != source["origin_id"]: _fail("source_origin_conflict")
        origin_uris[uri] = source["origin_id"]
        if not _stamp(source.get("available_at")) <= _stamp(source.get("retrieved_at")) <= reviewed or _stamp(source["privacy_review"]["reviewed_at"]) > admitted:
            _fail("availability_violation")
    raw, text = _read(root, record, path_key="source_path")
    for source_id, source in sources.items(): source_texts[source_id] = _read(root, source, path_key="snapshot_path")[1]
    evidence_blobs = {key: _read(root, item, path_key="source_path")[0] for key, item in evidence.items()}
    examples = _indexed(record.get("worked_examples"), "example_id", nonempty=False)
    example_checks = [_example(example, evidence_blobs) for example in examples.values()]
    claims = _indexed(record.get("claims"), "claim_id")
    review = record.get("source_review")
    if not isinstance(review, dict): _fail("review_coverage_incomplete")
    _fields(review, {"reviewed_by", "reviewed_at", "claim_ids", "findings"})
    _identifier(review.get("reviewed_by"))
    if _stamp(review.get("reviewed_at")) > admitted: _fail("availability_violation")
    if set(_strings(review.get("claim_ids"), identifiers=True)) != set(claims): _fail("review_coverage_incomplete")
    if not isinstance(review.get("findings"), list): _fail("review_coverage_incomplete")
    for finding in review["findings"]:
        if not isinstance(finding, dict) or finding.get("severity") not in ("critical", "major", "minor"): _fail("review_coverage_incomplete")
        _fields(finding, {"severity", "status", "claim_id", "resolution_verified"})
        # A past material finding needs a fresh source review for the corrected
        # version. A resolution_verified declaration is not resolution evidence.
        if finding["severity"] in ("critical", "major"):
            _fail("unresolved_material_finding")
    claim_bounds, used_sources, used_examples = {}, set(), set()
    for claim_id, claim in claims.items():
        _fields(claim, {"claim_id", "kind", "document_locator", "supports", "example_ids", "independent_origin_count"})
        if claim.get("kind") not in ("reported_fact", "method", "limitation", "worked_example"): _fail("invalid_claim_kind")
        claim_bounds[claim_id] = _locator(text, claim.get("document_locator"), inspected=True)
        if not isinstance(claim.get("supports"), list) or not claim["supports"]: _fail("required_evidence_missing")
        origins, support_classes = set(), set()
        for support in claim["supports"]:
            _fields(support, {"source_id", "locator"})
            source_id = support.get("source_id")
            if source_id not in sources: _fail("unknown_source_reference")
            _locator(source_texts[source_id], support.get("locator"), inspected=True)
            origins.add(sources[source_id]["origin_id"])
            support_classes.add(sources[source_id]["classification"])
            used_sources.add(source_id)
        if claim.get("independent_origin_count", len(origins)) != len(origins): _fail("origin_count_mismatch")
        if claim["kind"] == "reported_fact" and "PUBLIC" not in support_classes: _fail("synthetic_source_cannot_establish_reported_fact")
        ids = _strings(claim.get("example_ids"), identifiers=True)
        if any(x not in examples for x in ids) or (claim["kind"] == "worked_example" and not ids): _fail("worked_example_missing")
        used_examples.update(ids)
    if used_sources != set(sources) or used_examples != set(examples): _fail("unused_admission_evidence")
    if record["kind"] == "method_reference" and not examples: _fail("worked_example_missing")
    chunks = _indexed(record.get("chunks"), "chunk_id")
    chunk_bounds, covered_claims, intervals = [], set(), []
    lines = text.splitlines(keepends=True)
    for chunk_id, chunk in chunks.items():
        _fields(chunk, {"chunk_id", "locator", "approved_use", "claim_ids"})
        bounds = _locator(text, chunk.get("locator"))
        uses = _strings(chunk.get("approved_use"), nonempty=True, identifiers=True)
        if not set(uses) <= set(approved_use): _fail("scope_not_approved")
        ids = _strings(chunk.get("claim_ids"), nonempty=True, identifiers=True)
        if any(cid not in claims for cid in ids): _fail("review_coverage_incomplete")
        covered = set()
        for cid in ids:
            loc = claim_bounds[cid]
            if not bounds["start_line"] <= loc["start_line"] <= loc["end_line"] <= bounds["end_line"]: _fail("claim_outside_chunk")
            covered.update(range(loc["start_line"], loc["end_line"] + 1))
        if any(lines[index - 1].strip() and index not in covered for index in range(bounds["start_line"], bounds["end_line"] + 1)):
            _fail("unreviewed_chunk_content")
        if any(bounds["start_line"] <= end and start <= bounds["end_line"] for start, end in intervals): _fail("overlapping_chunks")
        intervals.append((bounds["start_line"], bounds["end_line"]))
        covered_claims.update(ids)
        chunk_bounds.append({"chunk_id": chunk_id, "locator": {key: bounds[key] for key in ("start_line", "end_line", "heading")},
                             **{key: bounds[key] for key in ("start_byte", "end_byte", "start_char", "end_char")},
                             "approved_use": uses, "claim_ids": ids})
    if covered_claims != set(claims): _fail("review_coverage_incomplete")
    return {"source_records": len(sources), "claim_records": len(claims), "worked_examples": example_checks,
            "supporting_origin_ids": sorted({sources[s]["origin_id"] for s in used_sources}), "chunk_bounds": chunk_bounds}


def admit_document(record, root=ROOT, *, admitted_at=None):
    timestamp = admitted_at or _now()
    candidate = _candidate_payload(record)
    validation = _validate_candidate(candidate, root, timestamp)
    result = copy.deepcopy(candidate)
    result["status"] = "approved"
    result["revision_status"] = "superseding" if candidate.get("supersedes") else "original"
    result["admission"] = {"policy_version": POLICY_VERSION, "validator_sha256": _identity(), "dependency_sha256": _dependencies(), "admitted_at": timestamp,
                           "candidate_sha256": _digest(_candidate_payload(result)), "validation": validation,
                           "evidence_state": "mechanically_admitted", "expert_certification": False}
    result["admission"]["record_sha256"] = _digest(result)
    return result


def _record_key(record): return _identifier(record.get("document_id")) + "@" + _identifier(record.get("source_version"), version=True)


def _verify_seal(record):
    if not isinstance(record, dict) or record.get("classification") not in SAFE_CLASSES: _fail("classification_not_approved")
    if record.get("schema") not in (DOCUMENT_SCHEMA, RETRACTION_SCHEMA): _fail("invalid_document_schema")
    for key in ("document_id", "source_origin_id"): _identifier(record.get(key))
    _identifier(record.get("source_version"), version=True)
    if record["schema"] == DOCUMENT_SCHEMA:
        _fields(record, DOCUMENT_FIELDS)
        _privacy(record, path_key="source_path")
        for source in _indexed(record.get("sources"), "source_id").values():
            _privacy(source, path_key="snapshot_path")
            _fields(source, SOURCE_FIELDS)
        for item in _indexed(record.get("validation_evidence", []), "evidence_id", nonempty=False).values(): _privacy(item, path_key="source_path")
    else:
        _fields(record, RETRACTION_FIELDS)
        if record.get("status") != "retracted" or record.get("reason_code") not in ("source_retracted", "source_revised", "applicability_withdrawn", "privacy_withdrawn"):
            _fail("invalid_retraction_reason")
    _safe_metadata(record)
    admission = record.get("admission")
    if not isinstance(admission, dict) or admission.get("policy_version") != POLICY_VERSION: _fail("admission_missing")
    unsigned = copy.deepcopy(record)
    recorded = unsigned["admission"].pop("record_sha256", None)
    if recorded != _digest(unsigned): _fail("registry_record_tampered")
    if record["schema"] == DOCUMENT_SCHEMA and admission.get("candidate_sha256") != _digest(_candidate_payload(record)):
        _fail("registry_record_tampered")
    _stamp(admission.get("admitted_at"))


def _load_registry(path):
    path = Path(path)
    if not path.exists(): return [], b""
    try: raw = path.read_bytes()
    except OSError: _fail("registry_unavailable")
    if len(raw) > 32 * MAX_BYTES: _fail("registry_too_large")
    if raw and not raw.endswith(b"\n"): _fail("registry_incomplete_write")
    records, seen, uri_origins = [], {}, {}
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result: _fail("registry_duplicate_key")
            result[key] = value
        return result
    try:
        for line in raw.splitlines():
            if not line: _fail("registry_invalid_json")
            record = json.loads(line, object_pairs_hook=unique_pairs, parse_constant=lambda value: _fail("registry_invalid_json"))
            _verify_seal(record)
            key = _record_key(record)
            if key in seen: _fail("duplicate_document_version")
            for prior in record.get("supersedes", []):
                if prior not in seen or seen[prior]["document_id"] != record["document_id"]: _fail("invalid_supersession")
                if _stamp(seen[prior]["available_at"]) > _stamp(record["available_at"]): _fail("invalid_supersession")
            for source in record.get("sources", []):
                uri = _uri(source["uri"])
                if uri in uri_origins and uri_origins[uri] != source["origin_id"]: _fail("source_origin_conflict")
                uri_origins[uri] = source["origin_id"]
            seen[key] = record
            records.append(record)
    except (UnicodeError, json.JSONDecodeError, KeyError, TypeError): _fail("registry_invalid_json")
    return records, raw


def _append_locked(path, candidate, root, timestamp, *, retraction=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = Path(str(path) + ".lock")
    try: descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError: _fail("registry_busy")
    try:
        os.close(descriptor)
        records, raw = _load_registry(path)
        key = _record_key(candidate)
        existing = next((record for record in records if _record_key(record) == key), None)
        if existing:
            compared = _candidate_payload(candidate)
            if not retraction: compared["revision_status"] = "superseding" if compared.get("supersedes") else "original"
            if _candidate_payload(existing) != compared: _fail("document_version_immutable")
            if not retraction: _validate_candidate(_candidate_payload(existing), root, existing["admission"]["admitted_at"])
            return existing
        prior = [record for record in records if record["document_id"] == candidate["document_id"]]
        if prior and _record_key(prior[-1]) not in candidate.get("supersedes", []): _fail("supersession_required")
        if any(ref not in {_record_key(record) for record in prior} for ref in candidate.get("supersedes", [])): _fail("invalid_supersession")
        if retraction:
            result = copy.deepcopy(candidate)
            result["admission"] = {"policy_version": POLICY_VERSION, "validator_sha256": _identity(), "admitted_at": timestamp,
                                   "evidence_state": "document_retracted", "expert_certification": False}
            result["admission"]["record_sha256"] = _digest(result)
        else: result = admit_document(candidate, root, admitted_at=timestamp)
        for old in records:
            if old.get("schema") == DOCUMENT_SCHEMA and old["document_id"] != result["document_id"] and (_uri(old["source_uri"]), old["source_origin_id"], old["source_version"]) == (_uri(result["source_uri"]), result["source_origin_id"], result["source_version"]):
                _fail("duplicate_document_origin_version")
            origins = {_uri(source["uri"]): source["origin_id"] for source in old.get("sources", [])}
            if any(_uri(source["uri"]) in origins and origins[_uri(source["uri"])] != source["origin_id"] for source in result.get("sources", [])):
                _fail("source_origin_conflict")
        encoded = _canonical(result) + b"\n"
        with path.open("ab") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        return result
    finally:
        lock.unlink(missing_ok=True)


def append_document_version(registry_path, record, root=ROOT, *, admitted_at=None):
    # Privacy preflight also precedes reading/hash-binding the public registry.
    if not isinstance(record, dict) or record.get("classification") not in SAFE_CLASSES: _fail("classification_not_approved")
    _privacy(record, path_key="source_path")
    for source in _indexed(record.get("sources"), "source_id").values(): _privacy(source, path_key="snapshot_path")
    for item in _indexed(record.get("validation_evidence", []), "evidence_id", nonempty=False).values(): _privacy(item, path_key="source_path")
    _fields(record, DOCUMENT_FIELDS)
    _safe_metadata(record)
    _record_key(record)
    return _append_locked(registry_path, _candidate_payload(record), root, admitted_at or _now())


def append_document_retraction(registry_path, document_id, source_version, root=ROOT, *, available_at, reviewed_by, reason_code):
    _identifier(document_id)
    _identifier(source_version, version=True)
    _identifier(reviewed_by)
    timestamp = _stamp(available_at)
    if reason_code not in ("source_retracted", "source_revised", "applicability_withdrawn", "privacy_withdrawn"):
        _fail("invalid_retraction_reason")
    records, _ = _load_registry(registry_path)
    prior = [record for record in records if record["document_id"] == document_id]
    if not prior: _fail("unknown_document")
    old = prior[-1]
    if timestamp < _stamp(old["available_at"]): _fail("availability_violation")
    record = {"schema": RETRACTION_SCHEMA, "document_id": document_id, "source_version": source_version,
              "source_origin_id": old["source_origin_id"], "source_uri": old["source_uri"], "classification": old["classification"],
              "status": "retracted", "revision_status": "retracted", "supersedes": [_record_key(old)],
              "available_at": available_at, "reviewed_at": available_at, "reviewed_by": reviewed_by, "reason_code": reason_code}
    return _append_locked(registry_path, record, root, available_at, retraction=True)


def approved_document_manifest(registry_path=DOCUMENT_REGISTRY_OUT, root=ROOT, *, as_of=None, scope=None):
    cutoff = _stamp(as_of or _now())
    if scope is not None: _identifier(scope)
    records, raw = _load_registry(registry_path)
    visible = [record for record in records if _stamp(record["available_at"]) <= cutoff and _stamp(record["admission"]["admitted_at"]) <= cutoff]
    superseded = {key for record in visible for key in record.get("supersedes", [])}
    documents, exclusions, seen_origins = [], [], set()
    current = [record for record in visible if _record_key(record) not in superseded]
    counts = {record["document_id"]: sum(x["document_id"] == record["document_id"] for x in current) for record in current}
    for record in visible:
        reason = None
        key = _record_key(record)
        if key in superseded: reason = "superseded"
        elif record["status"] == "retracted": reason = "retracted"
        elif counts[record["document_id"]] != 1: reason = "ambiguous_current_version"
        elif record["admission"]["validator_sha256"] != _identity(): reason = "validation_policy_changed"
        elif record["admission"].get("dependency_sha256") != _dependencies(): reason = "validation_dependency_changed"
        elif scope and scope not in record["approved_use"]: reason = "scope_not_approved"
        if reason is None:
            try: validation = _validate_candidate(_candidate_payload(record), root, record["admission"]["admitted_at"])
            except DocumentAdmissionError as error: reason = error.code
        if reason is None:
            identity = (_uri(record["source_uri"]), record["source_origin_id"], record["source_version"])
            if identity in seen_origins: reason = "duplicate_document_origin_version"
            else: seen_origins.add(identity)
        if reason:
            exclusions.append({"document_id": record["document_id"], "source_version": record["source_version"], "reason": reason})
            continue
        chunks = [chunk for chunk in validation["chunk_bounds"] if scope is None or scope in chunk["approved_use"]]
        if not chunks:
            exclusions.append({"document_id": record["document_id"], "source_version": record["source_version"], "reason": "scope_not_approved"})
            continue
        documents.append({**{key: record[key] for key in ("document_id", "source_version", "source_origin_id", "source_uri", "source_path", "sha256", "classification", "source_kind", "kind", "status", "approved_use", "applicability", "published_at", "available_at", "reviewed_at", "supersedes", "revision_status")},
                          "eligible": True, "supporting_origin_ids": validation["supporting_origin_ids"],
                          "supporting_sources": [{key: source[key] for key in ("source_id", "origin_id", "source_version", "uri", "classification", "source_kind", "sha256", "snapshot_path", "available_at", "retrieved_at", "original_locator", "transformations", "reviewed_scope", "availability_basis", "source_version_label") if key in source} for source in record["sources"]],
                          "chunks": chunks, "admission_record_sha256": record["admission"]["record_sha256"],
                          "reuse": record.get("reuse"), "evidence_state": "mechanically_admitted", "expert_certification": False})
    result = {"schema": MANIFEST_SCHEMA, "policy_version": POLICY_VERSION, "generated_at": _now(), "as_of": as_of,
              "scope": scope, "registry_sha256": sha256(raw).hexdigest(), "validator_sha256": _identity(), "dependency_sha256": _dependencies(),
              "documents": sorted(documents, key=lambda item: (item["document_id"], item["source_version"])),
              "exclusions": exclusions, "inventory_included": False,
              "limits": ["Only declared, inspected PUBLIC/SYNTHETIC versions and approved locators are eligible.",
                         "Mechanical source/byte/arithmetic controls do not establish authenticity, semantic entailment, expert certification or financial performance."]}
    result["manifest_sha256"] = _digest({key: value for key, value in result.items() if key != "generated_at"})
    return result


def inventory_financial_documents(paths, root=ROOT):
    """Explicit path inventory only; no content, excerpts, sizes or body hashes."""
    _strings(paths)
    rows = []
    for index, relative in enumerate(sorted(set(paths)), 1):
        path = _path(root, relative)
        rows.append({"inventory_id": f"inventory:{index:05d}", "source_path": relative,
                     "classification": "UNKNOWN", "status": "unreviewed", "content_inspected": False,
                     "present": path.is_file(), "eligible": False})
    return {"schema": "osanwe.financial-document-inventory/1", "generated_at": _now(), "documents": rows,
            "scope": "Metadata-only inventory of explicitly supplied financial reference paths; directory names confer no admission or privacy approval."}
