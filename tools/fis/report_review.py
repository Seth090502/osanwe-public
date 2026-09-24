"""Final-artifact review over the existing analysis packet and provenance graph.

This module checks declared coverage and exact bytes, not source truth or reviewer
honesty. Review identities and read-only execution are client-reported. Receipts
are local integrity records, not signed independent or expert certification.
Only reviewed public/synthetic material may enter this persistent interface.
"""
from __future__ import annotations

import copy
import ast
import hashlib
import json
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

import evidence
import workbench as w
from provenance import ProvenanceGraph

REQUEST_SCHEMA = "osanwe.review-request/1"
RECEIPT_SCHEMA = "osanwe.report-review/1"
PRODUCER_CONTRACT_SCHEMA = "osanwe.reviewer-producer-contract/2"
DIMENSIONS = {"economics", "source_support", "method_applicability", "alternatives",
              "costs", "sensitivity", "limitations", "claim_coverage", "rendering"}
SURFACES = {"narrative", "table", "chart_label", "tooltip", "filter", "export"}
ROLES = {"delivered", "original_draft", "source", "library", "render_evidence", "correction", "calculation_evidence", "calculation_code"}
HASH = re.compile(r"[0-9a-f]{64}\Z")
PRIVATE = re.compile(r"(?i)(privacy[_ -]?canary|personal[_ -]?canary|account[_ -]?(?:number|id)"
                     r"\s*[:=]|routing[_ -]?number\s*[:=]|\b\d{3}-\d{2}-\d{4}\b|"
                     r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b)")
HARD_PRIVATE = re.compile(r"(?i)(privacy[_ -]?canary|personal[_ -]?canary|account[_ -]?(?:number|id)"
                          r"\s*[:=]|routing[_ -]?number\s*[:=]|\b\d{3}-\d{2}-\d{4}\b)")


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _fields(value, required, optional=(), label="review record"):
    w.object_fields(value, set(required.split()), set(optional.split()) if isinstance(optional, str) else optional, label)


def _ids(values, label, available=None, nonempty=False):
    w.strings(values, label, nonempty=nonempty)
    for value in values:
        w.string(value, label, identifier=True)
    if available is not None and not set(values) <= set(available):
        raise ValueError(label + ": unknown reference")
    return set(values)


def _indexed(records, label, nonempty=False):
    result = {}
    for record in w.sequence(records, label, nonempty=nonempty):
        if not isinstance(record, dict):
            raise ValueError(label + ": object required")
        key = w.string(record.get("id"), label + ".id", identifier=True)
        if key in result:
            raise ValueError(label + ": duplicate identifier")
        result[key] = record
    return result


def _private(value):
    # Deliberately narrow leak controls, not a claim of automatic de-identification.
    # Do this before hashing, logging, or copying any caller material.
    if isinstance(value, dict):
        for key, item in value.items():
            if key.casefold() in {"account_number", "account_id", "ssn", "personal_amount",
                                  "personal_hash", "access_token", "refresh_token", "password"}:
                raise ValueError("personal or credential material is outside review persistence")
            _private(item)
    elif isinstance(value, list):
        for item in value:
            _private(item)
    elif isinstance(value, str) and PRIVATE.search(value):
        raise ValueError("personal or privacy-canary material is outside review persistence")


def _relative(root, name):
    if not isinstance(name, str) or "\\" in name:
        raise ValueError("artifact requires a relative POSIX path")
    rel = PurePosixPath(name)
    if rel.is_absolute() or any(p in {"", ".", ".."} for p in name.split("/")):
        raise ValueError("artifact path traversal refused")
    lexical = root.joinpath(*rel.parts)
    path = w.safe_path(lexical)
    if not path.is_relative_to(root) or any(p.is_symlink() for p in (lexical, *lexical.parents) if p != root.parent):
        raise ValueError("artifact links or escaped paths refused")
    if path.stat().st_size > w.MAX_BYTES:
        raise ValueError("artifact exceeds byte limit")
    return path


def _span(span, blobs, artifacts, *, role=None):
    _fields(span, "artifact_id start end text locator", label="inspected span")
    artifact = artifacts.get(span["artifact_id"])
    if artifact is None or (role and artifact["role"] != role):
        raise ValueError("inspected span: artifact role mismatch")
    start, end = span["start"], span["end"]
    if not isinstance(start, int) or isinstance(start, bool) or not isinstance(end, int) or isinstance(end, bool):
        raise ValueError("inspected span: integer character offsets required")
    w.string(span["locator"], "span.locator")
    text = span["text"]
    if not isinstance(text, str) or not text or len(text) > 16000:
        raise ValueError("inspected span: bounded exact text required")
    try:
        original = blobs[span["artifact_id"]].decode("utf-8")
    except UnicodeError as exc:
        raise ValueError("inspected spans require UTF-8 evidence or a separately reviewed text export") from exc
    if start < 0 or end <= start or end > len(original) or original[start:end] != text:
        raise ValueError("inspected span differs from the archived artifact")
    return text


def _number(token):
    if not isinstance(token, str) or not re.fullmatch(r"[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\((?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?\)", token):
        raise ValueError("numeric display requires a plain decimal token")
    try:
        return Decimal(token.replace(",", "").replace("(", "-").replace(")", ""))
    except InvalidOperation as exc:
        raise ValueError("invalid numeric token") from exc


def _shown(assertion, node, text):
    _fields(assertion, "token multiplier decimals metric unit currency basis", label="numeric display")
    if not evidence.numeric_token_in_text(assertion["token"], text):
        raise ValueError("display token is absent from its exact span")
    multiplier, decimals = assertion["multiplier"], assertion["decimals"]
    if not evidence.finite(multiplier) or multiplier <= 0 or isinstance(decimals, bool) or not isinstance(decimals, int) or not 0 <= decimals <= 12:
        raise ValueError("display conversion requires positive finite multiplier and bounded precision")
    for key in ("metric", "unit", "currency", "basis"):
        if assertion[key] != node.get(key):
            raise ValueError("numeric display silently changes metric, unit, currency or basis")
    if not evidence.finite(node.get("value")):
        raise ValueError("numeric display must reference a scalar calculation or source claim")
    try:
        expected = (Decimal(str(node["value"])) * Decimal(str(multiplier))).quantize(
            Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_EVEN)
    except InvalidOperation as exc:
        raise ValueError("numeric display exceeds bounded decimal precision") from exc
    if _number(assertion["token"]) != expected:
        raise ValueError("numeric display differs from deterministic calculation and rounding")


def code_hashes():
    return {**w.code_hashes(), "report_review.py": _hash(Path(__file__).read_bytes()),
            "reviewer_execution.py": _hash(Path(__file__).with_name("reviewer_execution.py").read_bytes())}


def _expression(expression, bindings):
    """Small independent Decimal grader, no eval, imports, calls or attributes.

    Values retain their declared display scale. Addition/subtraction require
    matching dimensions, currencies, scales and accounting bases. Multiplication
    and division propagate dimensions; a quotient of like units is dimensionless.
    """
    w.string(expression, "external.expression")
    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, RecursionError) as exc:
        raise ValueError("external expression is invalid") from exc
    if len(list(ast.walk(tree))) > 100:
        raise ValueError("external expression exceeds operation bound")
    used = set()
    def evaluate(node):
        if isinstance(node, ast.Name) and node.id in bindings:
            used.add(node.id)
            record = bindings[node.id]
            dimensions = {} if record["unit"] in {"fraction", "ratio", "count"} else {
                (record["unit"], record["currency"], record["basis"]): 1}
            return Decimal(str(record["value"])), dimensions
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            value, dimension = evaluate(node.operand)
            return (-value if isinstance(node.op, ast.USub) else value), dimension
        if not isinstance(node, ast.BinOp) or not isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            raise ValueError("external expression permits bound names and arithmetic only")
        left, ld = evaluate(node.left)
        right, rd = evaluate(node.right)
        if isinstance(node.op, (ast.Add, ast.Sub)):
            if ld != rd:
                raise ValueError("external calculation mixes incompatible units, currencies, scales or bases")
            return (left + right if isinstance(node.op, ast.Add) else left - right), ld
        if isinstance(node.op, ast.Div) and right == 0:
            raise ValueError("external calculation has a zero denominator")
        result = left * right if isinstance(node.op, ast.Mult) else left / right
        dimensions = dict(ld)
        for key, power in rd.items():
            dimensions[key] = dimensions.get(key, 0) + (power if isinstance(node.op, ast.Mult) else -power)
            if not dimensions[key]:
                dimensions.pop(key)
        return result, dimensions
    result, dimensions = evaluate(tree.body)
    if used != set(bindings):
        raise ValueError("external expression has unused or undeclared input bindings")
    return result, dimensions


def _pointer(value, pointer):
    if not isinstance(pointer, str) or not pointer.startswith("/") or len(pointer) > 512:
        raise ValueError("external result requires a bounded JSON pointer")
    try:
        for part in pointer[1:].split("/"):
            part = part.replace("~1", "/").replace("~0", "~")
            value = value[int(part)] if isinstance(value, list) else value[part]
    except (IndexError, KeyError, TypeError, ValueError) as exc:
        raise ValueError("external result pointer is unavailable") from exc
    if isinstance(value, bool) or not isinstance(value, (str, float, int)):
        raise ValueError("external result must be a decimal scalar")
    try:
        parsed = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("external result is not a decimal scalar") from exc
    if not parsed.is_finite():
        raise ValueError("external result must be finite")
    return parsed


def _external_calculations(records, nodes, blobs, artifacts):
    computations = _indexed(records, "external_calculations")
    result = {}
    for item in computations.values():
        _fields(item, "id evidence_artifact code_artifact result_pointer expression bindings metric unit currency basis period_policy scope")
        if item["id"] in nodes:
            raise ValueError("external calculation cannot replace an existing fact or workbench result")
        if artifacts.get(item["evidence_artifact"], {}).get("role") != "calculation_evidence" or artifacts.get(item["code_artifact"], {}).get("role") != "calculation_code":
            raise ValueError("external calculation requires separately archived outputs and code")
        w.string(item["scope"], "external.scope")
        if item["period_policy"] not in {"same_period", "explicit_comparison"}:
            raise ValueError("external calculation requires explicit period policy")
        bindings = item["bindings"]
        if not isinstance(bindings, dict) or not bindings or len(bindings) > 100:
            raise ValueError("external bindings must be a bounded nonempty object")
        resolved, refs = {}, []
        for name, binding in bindings.items():
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", name):
                raise ValueError("external binding name must be an identifier")
            if isinstance(binding, dict) and set(binding) == {"ref"}:
                if binding["ref"] not in nodes:
                    raise ValueError("external input reference is unavailable")
                resolved[name] = nodes[binding["ref"]]
                refs.append(binding["ref"])
            else:
                _fields(binding, "assumption unit currency basis rationale")
                w.string(binding["rationale"], "external.assumption.rationale")
                if not evidence.finite(binding["assumption"]):
                    raise ValueError("external assumptions must be finite")
                resolved[name] = {"value": binding["assumption"], **{k: binding[k] for k in ("unit", "currency", "basis")}}
        if not refs:
            raise ValueError("external financial calculation must bind source-bearing input evidence")
        for binding in resolved.values():
            for key in ("unit", "currency", "basis"):
                w.string(binding.get(key), "external.input." + key)
            if not evidence.finite(binding.get("value")):
                raise ValueError("external inputs must be scalar and finite")
        reference_bases = {nodes[x]["basis"] for x in refs}
        if len(reference_bases) != 1 or item["basis"] not in reference_bases:
            raise ValueError("external calculation cannot silently change accounting or nominal/real basis")
        periods = {(nodes[x].get("period_start"), nodes[x].get("period_end"), nodes[x].get("as_of")) for x in refs}
        if item["period_policy"] == "same_period" and len(periods) > 1:
            raise ValueError("external calculation mixes periods without explicit comparison")
        expected, dimensions = _expression(item["expression"], resolved)
        declared = {} if item["unit"] in {"fraction", "ratio", "count", "percent", "percentage_points", "basis_points"} else {(item["unit"], item["currency"], item["basis"]): 1}
        if declared != dimensions or (not declared and item["currency"] != "NONE"):
            raise ValueError("external output unit or currency does not match its expression")
        try:
            document = json.loads(blobs[item["evidence_artifact"]].decode("utf-8"), object_pairs_hook=evidence.unique_object)
        except (UnicodeError, ValueError) as exc:
            raise ValueError("external calculation evidence must be valid JSON") from exc
        _private(document)
        actual = _pointer(document, item["result_pointer"])
        if abs(expected - actual) > Decimal("1e-12") * max(abs(expected), Decimal(1)):
            raise ValueError("external result differs from independent Decimal reproduction")
        scalar = float(expected)
        if not evidence.finite(scalar):
            raise ValueError("external output exceeds finite scalar bound")
        result[item["id"]] = {"id": item["id"], "value": scalar, "metric": item["metric"],
                              "unit": item["unit"], "currency": item["currency"], "basis": item["basis"],
                              "kind": "calculated", "inputs": refs, "transformation": "independent_expression",
                              "scope": item["scope"], "expression": item["expression"], "decimal_result": str(expected)}
        nodes[item["id"]] = result[item["id"]]
    return result


def _artifacts(request, directory):
    root = w.safe_path(directory, must_exist=False)
    if not root.is_dir():
        raise ValueError("artifact root must exist")
    artifacts = _indexed(request["artifacts"], "artifacts", nonempty=True)
    blobs, paths, public_reviews = {}, set(), {}
    for assessment in w.sequence(request["privacy"].get("public_artifact_reviews", []), "privacy.public_artifact_reviews"):
        _fields(assessment, "artifact_id sha256 public_origin reviewed_by reason")
        aid = assessment["artifact_id"]
        if aid not in artifacts or aid in public_reviews or request["classification"] != "public":
            raise ValueError("public artifact classification review must name one public artifact")
        if assessment["sha256"] != artifacts[aid]["sha256"]:
            raise ValueError("public artifact classification review is stale")
        origin = urlsplit(assessment["public_origin"])
        if origin.scheme != "https" or not origin.hostname or origin.username or origin.password:
            raise ValueError("public artifact classification review requires a public HTTPS origin")
        for key in ("reviewed_by", "reason"):
            w.string(assessment[key], "privacy.public_artifact_review." + key)
        public_reviews[aid] = assessment
    for aid, artifact in artifacts.items():
        _fields(artifact, "id path role media_type classification sha256 surfaces", "rendered_from rendered_from_sha256 render_method", label="artifact")
        if artifact["classification"] != request["classification"] or artifact["role"] not in ROLES:
            raise ValueError("artifact classification or role is outside the review boundary")
        w.string(artifact["media_type"], "artifact.media_type")
        if not HASH.fullmatch(artifact["sha256"]):
            raise ValueError("artifact SHA-256 required")
        w.strings(artifact["surfaces"], "artifact.surfaces")
        if not set(artifact["surfaces"]) <= SURFACES or (artifact["role"] == "delivered" and not artifact["surfaces"]):
            raise ValueError("delivered artifact requires explicit supported surfaces")
        p = _relative(root, artifact["path"])
        if p in paths:
            raise ValueError("artifact paths must be unique")
        paths.add(p)
        data = p.read_bytes()
        text = data.decode("utf-8", errors="ignore")
        if HARD_PRIVATE.search(text) or (PRIVATE.search(text) and aid not in public_reviews):
            raise ValueError("personal or privacy-canary artifact refused before persistence")
        if _hash(data) != artifact["sha256"]:
            raise ValueError("artifact bytes changed since manifest preparation")
        blobs[aid] = data
    for artifact in artifacts.values():
        rendered = {k for k in ("rendered_from", "rendered_from_sha256", "render_method") if k in artifact}
        if rendered:
            if len(rendered) != 3 or artifact["role"] != "render_evidence":
                raise ValueError("render observations require complete source binding and an evidence role")
            original = artifacts.get(artifact["rendered_from"])
            if original is None or original["role"] != "delivered" or original["sha256"] != artifact["rendered_from_sha256"]:
                raise ValueError("render observation belongs to another delivered artifact version")
            w.string(artifact["render_method"], "artifact.render_method")
        elif artifact["role"] == "render_evidence":
            raise ValueError("render observation must bind the exact delivered artifact it observed")
    if sum(map(len, blobs.values())) > 32_000_000:
        raise ValueError("review artifacts exceed total byte limit")
    roles = {a["role"] for a in artifacts.values()}
    if not {"delivered", "original_draft", "source"} <= roles:
        raise ValueError("review must retain the original draft, delivered artifact and source snapshots")
    return artifacts, blobs


def prepare_context(packet, bundle, request, artifacts_directory):
    """Validate deterministic obligations and return the immutable reviewer input.

    Calling this does not invoke a reviewer or accept a report. The returned digest
    must be carried by an independent review of these exact inputs and artifacts.
    """
    _fields(request, "schema id classification privacy author_id reviewed_at task artifacts source_reviews methods assertions render_checks scenarios comparisons revisions reviewers", "external_calculations")
    _private(request)
    _private(packet)
    if request["schema"] != REQUEST_SCHEMA or request["classification"] not in {"public", "synthetic"} or request["classification"] != packet.get("classification"):
        raise ValueError("review accepts matching public/synthetic classifications only")
    w.string(request["id"], "review.id", identifier=True)
    w.string(request["author_id"], "author_id", identifier=True)
    reviewed = evidence.timestamp(request["reviewed_at"])
    if reviewed < evidence.timestamp(packet["report_at"]):
        raise ValueError("review cannot predate the report")
    _fields(request["privacy"], "classification reviewed_by contains_personal_data", "public_artifact_reviews")
    if request["privacy"]["classification"] != request["classification"] or request["privacy"]["contains_personal_data"] is not False:
        raise ValueError("explicit public/synthetic privacy review required")
    w.string(request["privacy"]["reviewed_by"], "privacy.reviewed_by", identifier=True)
    w.verify_bundle(packet, bundle)
    calculation = w.analyze(packet)
    artifacts, blobs = _artifacts(request, artifacts_directory)
    nodes = {n["id"]: n for n in calculation["claims"] + calculation["results"]}
    external = _external_calculations(request.get("external_calculations", []), nodes, blobs, artifacts)
    sources = {s["id"]: s for s in packet["sources"]}
    source_reviews = _indexed(request["source_reviews"], "source_reviews", nonempty=True)
    mapped, source_ids, origins = set(), set(), {}
    for item in source_reviews.values():
        _fields(item, "id source_id snapshot_artifact source_version origin_uri relationship revision_status supersedes inspected_at inspected_by mappings", "original_snapshot_artifact")
        source = sources.get(item["source_id"])
        snapshot = artifacts.get(item["snapshot_artifact"])
        if source is None or snapshot is None or snapshot["role"] != "source":
            raise ValueError("source review references an unknown source or snapshot")
        original_snapshot = None
        if "original_snapshot_artifact" in item:
            original_id = item["original_snapshot_artifact"]
            if original_id == item["snapshot_artifact"] or artifacts.get(original_id, {}).get("role") != "source":
                raise ValueError("extracted source support must preserve a distinct original source snapshot")
            original_snapshot = blobs[original_id]
        evidence.validate_source_review(item, source, packet["claims"], blobs[item["snapshot_artifact"]],
                                        knowledge_cutoff=packet["knowledge_cutoff"], report_at=request["reviewed_at"],
                                        original_snapshot=original_snapshot)
        for mapping in item["mappings"]:
            cid = mapping["claim_id"]
            if cid in mapped:
                raise ValueError("source claim has duplicate competing review mappings")
            mapped.add(cid)
            _span(mapping["support"], blobs, artifacts, role="source")
            if mapping["support"]["artifact_id"] != item["snapshot_artifact"]:
                raise ValueError("source mapping excerpt comes from the wrong snapshot")
            if original_snapshot is not None:
                _span(mapping["original_support"], blobs, artifacts, role="source")
        source_ids.add(item["source_id"])
        uri = source["uri"]
        if uri in origins and origins[uri] != item["origin_uri"]:
            raise ValueError("the same source cannot manufacture independent origins")
        origins[uri] = item["origin_uri"]
    if source_ids != set(sources) or mapped != {n["id"] for n in packet["claims"]}:
        raise ValueError("every packet source and source claim requires inspected evidence")
    assertions = _indexed(request["assertions"], "assertions", nonempty=True)
    delivered = {k for k, a in artifacts.items() if a["role"] == "delivered"}
    seen_surfaces, supported_nodes, limitations = set(), set(), set()
    for a in assertions.values():
        _fields(a, "id kind support_refs span surface limitations", "display delivered_artifact_id")
        if a["kind"] not in {"numeric", "interpretation", "limitation", "withholding"} or a["surface"] not in SURFACES:
            raise ValueError("assertion requires a financial kind and artifact surface")
        if "delivered_artifact_id" in a:
            text = _span(a["span"], blobs, artifacts, role="render_evidence")
            aid = a["delivered_artifact_id"]
            observation = artifacts[a["span"]["artifact_id"]]
            if observation.get("rendered_from") != aid or aid not in delivered:
                raise ValueError("rendered assertion is not bound to its delivered artifact")
        else:
            text = _span(a["span"], blobs, artifacts, role="delivered")
            aid = a["span"]["artifact_id"]
        if a["surface"] not in artifacts[aid]["surfaces"]:
            raise ValueError("assertion surface absent from delivered artifact manifest")
        refs = _ids(a["support_refs"], "assertion.support_refs", nodes)
        w.strings(a["limitations"], "assertion.limitations")
        limitations.update(a["limitations"])
        supported_nodes |= refs
        seen_surfaces.add((aid, a["surface"]))
        if a["kind"] == "numeric":
            if len(refs) != 1 or "display" not in a:
                raise ValueError("numeric assertion requires one exact input/result and display conversion")
            _shown(a["display"], nodes[next(iter(refs))], text)
        elif "display" in a:
            raise ValueError("only numeric assertions may declare display conversion")
    expected_surfaces = {(k, s) for k in delivered for s in artifacts[k]["surfaces"]}
    if seen_surfaces != expected_surfaces:
        raise ValueError("declared delivered surfaces have unreviewed content")
    required_limits = set(packet["gaps"] + packet["scope"]["limitations"])
    if not required_limits <= limitations:
        raise ValueError("packet gaps or scope limitations were omitted from report review")
    # Limitations must actually occur in the delivered bytes, not just metadata.
    visible = delivered | {k for k, a in artifacts.items() if a.get("rendered_from") in delivered}
    delivered_text = "\n".join(blobs[k].decode("utf-8", errors="ignore") for k in visible)
    if any(text not in delivered_text for text in required_limits):
        raise ValueError("a required limitation is absent from the delivered artifact")
    task = request["task"]
    _fields(task, "question horizon consequential coupled_required material_assumptions obligations")
    for key in ("question", "horizon"):
        w.string(task[key], "task." + key)
    if type(task["consequential"]) is not bool or type(task["coupled_required"]) is not bool:
        raise ValueError("task consequential/coupled flags require booleans")
    assumptions = _ids(task["material_assumptions"], "material_assumptions", nodes)
    obligations = _indexed(task["obligations"], "obligations", nonempty=True)
    calculation_ids = {n["id"] for n in calculation["results"]} | set(external)
    for o in obligations.values():
        _fields(o, "id question support answer_assertions required_calculations missing_information withholding_reason")
        w.string(o["question"], "obligation.question")
        answers = _ids(o["answer_assertions"], "obligation.answer_assertions", assertions)
        required = _ids(o["required_calculations"], "obligation.required_calculations", calculation_ids)
        w.strings(o["missing_information"], "obligation.missing_information")
        if o["support"] not in {"supported", "partial", "unsupported"}:
            raise ValueError("obligation answerability is required")
        if o["support"] in {"supported", "partial"} and (not answers or not required <= supported_nodes or all(assertions[x]["kind"] == "withholding" for x in answers)):
            raise ValueError("supported obligations cannot be replaced by blanket withholding")
        if o["support"] in {"partial", "unsupported"}:
            if not o["missing_information"]:
                raise ValueError("withholding requires genuinely missing information")
            w.string(o["withholding_reason"], "obligation.withholding_reason")
        elif o["withholding_reason"] is not None:
            raise ValueError("supported obligation cannot claim a withholding reason")
    methods = _indexed(request["methods"], "methods")
    for method in methods.values():
        _fields(method, "id name version approved_scope applies_because retrieved_at support calculation_ids contrary_guidance missing_inputs alternatives")
        for key in ("name", "version", "approved_scope", "applies_because"):
            w.string(method[key], "method." + key)
        if evidence.timestamp(method["retrieved_at"]) > reviewed:
            raise ValueError("method retrieval postdates review")
        _span(method["support"], blobs, artifacts, role="library")
        _ids(method["calculation_ids"], "method.calculation_ids", calculation_ids, nonempty=True)
        for key in ("contrary_guidance", "missing_inputs", "alternatives"):
            w.strings(method[key], "method." + key)
    scenarios = _indexed(request["scenarios"], "scenarios")
    scenario_results = []
    for scenario in scenarios.values():
        _fields(scenario, "id changes result_id threshold direction conclusion reverses")
        changes = scenario["changes"]
        if not isinstance(changes, dict) or not changes or not set(changes) <= assumptions:
            raise ValueError("scenario changes require declared material assumption IDs")
        modified = copy.deepcopy(packet)
        for cid, value in changes.items():
            if not evidence.finite(value):
                raise ValueError("scenario values must be finite")
            claim = next((c for c in modified["claims"] if c["id"] == cid), None)
            if claim is None or claim["kind"] not in {"assumption", "forecast", "estimate"}:
                raise ValueError("scenario must vary an assumption, estimate or forecast, not a reported fact")
            claim["value"] = value
        sid = scenario["result_id"]
        baseline = nodes.get(sid, {}).get("value")
        replay = {n["id"]: n for n in w.analyze(modified)["results"]}
        value = replay.get(sid, {}).get("value")
        if not evidence.finite(baseline) or not evidence.finite(value) or not evidence.finite(scenario["threshold"]) or scenario["direction"] not in {"above", "below"} or type(scenario["reverses"]) is not bool:
            raise ValueError("scenario requires a scalar computed decision boundary")
        threshold = scenario["threshold"]
        holds = lambda x: x > threshold if scenario["direction"] == "above" else x < threshold
        reverses = holds(baseline) != holds(value)
        if scenario["reverses"] != reverses:
            raise ValueError("claimed decision reversal disagrees with computed scenario")
        w.string(scenario["conclusion"], "scenario.conclusion")
        scenario_results.append({"id": scenario["id"], "baseline": baseline, "result": value, "reverses": reverses})
    if task["consequential"] and (not scenarios or not any(s["reverses"] for s in scenario_results)):
        raise ValueError("consequential review requires a computed condition that reverses its conclusion")
    if task["coupled_required"] and not any(len(s["changes"]) >= 2 for s in scenarios.values()):
        raise ValueError("coupled sensitivity requires jointly changed material inputs")
    comparisons = _indexed(request["comparisons"], "comparisons")
    for comparison in comparisons.values():
        _fields(comparison, "id candidate alternative inputs input_sha256 costs constraints result_ids worse_conditions")
        for key in ("candidate", "alternative"):
            w.string(comparison[key], "comparison." + key)
        ids = _ids(comparison["inputs"], "comparison.inputs", nodes, nonempty=True)
        if comparison["input_sha256"] != {k: w.sha(nodes[k]) for k in sorted(ids)}:
            raise ValueError("method comparison does not bind consistent input evidence")
        _ids(comparison["result_ids"], "comparison.result_ids", calculation_ids, nonempty=True)
        for key in ("costs", "constraints", "worse_conditions"):
            w.strings(comparison[key], "comparison." + key, nonempty=True)
    if task["consequential"] and not comparisons:
        raise ValueError("consequential review requires an applicable simple alternative comparison")
    for revision in w.sequence(request["revisions"], "revisions"):
        _fields(revision, "prior_request_sha256 draft_artifact correction_artifact reason")
        if not HASH.fullmatch(revision["prior_request_sha256"]):
            raise ValueError("revision requires the original review request digest")
        for key, role in (("draft_artifact", "original_draft"), ("correction_artifact", "correction")):
            if artifacts.get(revision[key], {}).get("role") != role:
                raise ValueError("revision must preserve both the original draft and correction")
        w.string(revision["reason"], "revision.reason")
    render_checks = _indexed(request["render_checks"], "render_checks")
    states = {}
    for check in render_checks.values():
        _fields(check, "id artifact_id surface state outcome evidence_artifact assertion_ids", "applicability")
        aid = check["artifact_id"]
        if aid not in delivered or check["surface"] not in artifacts[aid]["surfaces"]:
            raise ValueError("render check references an absent delivered surface")
        if check["state"] not in {"default", "empty", "partial", "missing", "zero_denominator", "currency_boundary", "time_boundary", "negative"} or check["outcome"] not in {"pass", "fail", "unavailable", "not_applicable"}:
            raise ValueError("render check requires explicit boundary state and outcome")
        if check["outcome"] == "not_applicable":
            applicability = check.get("applicability")
            _fields(applicability, "interface exposed reason")
            for key in ("interface", "reason"):
                w.string(applicability[key], "render_check.applicability." + key)
            if check["state"] in {"default", "partial"} or applicability["exposed"] is not False:
                raise ValueError("default, partial and exposed financial input states cannot be declared not applicable")
        elif "applicability" in check:
            raise ValueError("applicability exception is only valid for an explicitly unexposed state")
        if artifacts.get(check["evidence_artifact"], {}).get("role") != "render_evidence":
            raise ValueError("render checks require actual saved observation evidence")
        if artifacts[check["evidence_artifact"]].get("rendered_from") != aid:
            raise ValueError("render check evidence observed another delivered artifact")
        _ids(check["assertion_ids"], "render_check.assertion_ids", assertions, nonempty=True)
        states.setdefault((aid, check["surface"]), set()).add(check["state"])
    for aid, surface in expected_surfaces:
        required = {"default"}
        if surface == "filter":
            required |= {"empty", "partial", "missing", "zero_denominator", "currency_boundary", "time_boundary", "negative"}
        if not required <= states.get((aid, surface), set()):
            raise ValueError("delivered artifact lacks a required render or filter-boundary observation")
    frozen = {k: v for k, v in request.items() if k != "reviewers"}
    coverage = {"assertions": sorted(assertions), "obligations": sorted(obligations), "artifacts": sorted(artifacts),
                "sources": sorted(source_reviews), "methods": sorted(methods), "render_checks": sorted(render_checks)}
    manifest = w.load_packet(Path(bundle) / "manifest.json")
    context = {"request": frozen, "packet_sha256": w.sha(packet), "calculation_manifest_sha256": w.sha(manifest),
               "code_sha256": code_hashes(), "required_coverage": coverage, "scenario_results": scenario_results}
    return {"context_sha256": w.sha(context), "required_coverage": coverage, "context": context,
            "artifacts": artifacts, "blobs": blobs, "source_origins": sorted(set(origins.values())),
            "not_applicable_checks": sorted(c["id"] for c in render_checks.values() if c["outcome"] == "not_applicable")}


def _reviewers(request, prepared):
    blockers = []
    try:
        reviewers = _indexed(request["reviewers"], "reviewers", nonempty=True)
    except (TypeError, ValueError):
        return ["reviewer_missing_or_malformed"]
    for reviewer in reviewers.values():
        try:
            _fields(reviewer, "id kind status context_sha256 read_only full_artifact_reviewed coverage judgments findings disagreements", "model effort not_applicable_checks")
            if reviewer["id"] == request["author_id"] or reviewer["kind"] not in {"model", "human"}:
                raise ValueError("separate reviewer required")
            if reviewer["status"] != "completed" or reviewer["read_only"] is not True or reviewer["full_artifact_reviewed"] is not True:
                raise ValueError("review incomplete or not read-only")
            if reviewer["context_sha256"] != prepared["context_sha256"]:
                raise ValueError("review context changed")
            if reviewer["kind"] == "model":
                for key in ("model", "effort"):
                    w.string(reviewer.get(key), "reviewer." + key)
            if reviewer["coverage"] != prepared["required_coverage"]:
                raise ValueError("reviewer omitted coverage")
            if reviewer.get("not_applicable_checks", []) != prepared["not_applicable_checks"]:
                raise ValueError("reviewer did not explicitly confirm each unexposed-state applicability decision")
            if not isinstance(reviewer["judgments"], dict) or set(reviewer["judgments"]) != DIMENSIONS:
                raise ValueError("reviewer omitted interpretation dimensions")
            for dimension, judgment in reviewer["judgments"].items():
                _fields(judgment, "status rationale")
                w.string(judgment["rationale"], "reviewer.rationale")
                applicable = dimension not in {"costs", "alternatives", "sensitivity"} or request["task"]["consequential"]
                if judgment["status"] not in {"pass", "not_applicable"} or (applicable and judgment["status"] != "pass"):
                    blockers.append("reviewer_financial_dimension_failed")
            findings = _indexed(reviewer["findings"], "reviewer.findings")
            for finding in findings.values():
                _fields(finding, "id severity status reason assertion_ids artifact_ids resolution_artifact resolution_verified")
                if finding["severity"] not in {"critical", "major", "minor"} or finding["status"] not in {"open", "resolved", "disputed"}:
                    raise ValueError("malformed finding")
                w.string(finding["reason"], "finding.reason")
                _ids(finding["assertion_ids"], "finding.assertion_ids", prepared["required_coverage"]["assertions"])
                _ids(finding["artifact_ids"], "finding.artifact_ids", prepared["artifacts"])
                if finding["status"] == "resolved":
                    if finding["resolution_verified"] is not True or prepared["artifacts"].get(finding["resolution_artifact"], {}).get("role") != "correction":
                        raise ValueError("finding resolution lacks preserved independently reviewed correction")
                elif finding["resolution_artifact"] is not None or finding["resolution_verified"] is not False:
                    raise ValueError("unresolved finding cannot declare a resolution")
                if finding["severity"] in {"major", "critical"} and finding["status"] != "resolved":
                    blockers.append("unresolved_material_financial_finding")
            disagreements = _ids(reviewer["disagreements"], "reviewer.disagreements", findings)
            if any(findings[key]["status"] == "resolved" for key in disagreements):
                raise ValueError("resolved finding cannot be an unresolved disagreement")
            if disagreements or any(f["status"] == "disputed" for f in findings.values()):
                blockers.append("unresolved_reviewer_disagreement")
        except (KeyError, TypeError, ValueError):
            blockers.append("reviewer_missing_malformed_stale_or_incomplete")
    if any(c["outcome"] not in {"pass", "not_applicable"} for c in request["render_checks"]):
        blockers.append("render_check_failed_or_unavailable")
    return sorted(set(blockers))


def reviewer_contract(prepared, *, reviewer_id, model, effort, response_key="R001"):
    """Generate native JSON schema and instructions from the owning review rules.

    JSON schema cannot prove dynamic references to findings in the same output.
    Consumers must still call consume_reviewer_output and the existing review gate.
    This function performs no inference and adds no report acceptance evidence.
    """
    for name, value in (("reviewer_id", reviewer_id), ("response_key", response_key)):
        w.string(value, name, identifier=True)
    for name, value in (("model", model), ("effort", effort)):
        w.string(value, name)
    _private([reviewer_id, model, effort, response_key])
    if not HASH.fullmatch(prepared.get("context_sha256", "")):
        raise ValueError("producer contract requires a prepared review context")
    coverage = prepared["required_coverage"]
    _fields(coverage, "assertions obligations artifacts sources methods render_checks", label="reviewer coverage")
    for values in coverage.values():
        _ids(values, "reviewer coverage")
    _ids(prepared["not_applicable_checks"], "not_applicable_checks", coverage["render_checks"])
    artifacts = prepared.get("artifacts")
    if (not isinstance(artifacts, dict) or set(artifacts) != set(coverage["artifacts"])
            or any(not isinstance(value, dict) or value.get("role") not in ROLES for value in artifacts.values())):
        raise ValueError("producer contract requires prepared artifact roles")
    correction_ids = sorted(key for key, value in artifacts.items() if value["role"] == "correction")
    identifier = {"type": "string", "pattern": "^" + w.ID.pattern.removesuffix(r"\Z") + r"$(?![\s\S])"}
    plain = {"type": "string", "minLength": 1, "maxLength": 4096,
             "pattern": r"^[^\s\x00-\x1f](?:[^\x00-\x1f]*[^\s\x00-\x1f])?$(?![\s\S])"}

    def obj(properties):
        return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}

    def refs(values):
        return {"type": "array", "maxItems": w.MAX_ITEMS if values else 0, "uniqueItems": True,
                "items": {"type": "string", "enum": list(values)} if values else copy.deepcopy(identifier)}

    common_finding = {"id": identifier, "severity": {"enum": ["critical", "major", "minor"]}, "reason": plain,
                      "assertion_ids": refs(coverage["assertions"]), "artifact_ids": refs(coverage["artifacts"])}
    unresolved_finding = obj({**common_finding, "status": {"enum": ["open", "disputed"]},
                             "resolution_artifact": {"type": "null"}, "resolution_verified": {"const": False}})
    # Native-supported object branches encode the existing cross-field rules.
    # There is no resolved branch when the prepared evidence has no correction.
    finding = unresolved_finding
    if correction_ids:
        resolved_finding = obj({**common_finding, "status": {"const": "resolved"},
                               "resolution_artifact": {"type": "string", "enum": correction_ids},
                               "resolution_verified": {"const": True}})
        finding = {"anyOf": [unresolved_finding, resolved_finding]}
    judgment = obj({"status": {"enum": ["pass", "fail", "not_applicable"]}, "rationale": plain})
    record = obj({"id": {"const": reviewer_id}, "kind": {"const": "model"},
                  "model": {"const": model}, "effort": {"const": effort},
                  "status": {"enum": ["completed", "failed", "timeout"]},
                  "context_sha256": {"const": prepared["context_sha256"]}, "read_only": {"type": "boolean"},
                  "full_artifact_reviewed": {"type": "boolean"}, "coverage": {"const": copy.deepcopy(coverage)},
                  "not_applicable_checks": {"const": copy.deepcopy(prepared["not_applicable_checks"])},
                  "judgments": obj({d: copy.deepcopy(judgment) for d in sorted(DIMENSIONS)}),
                  "findings": {"type": "array", "maxItems": w.MAX_ITEMS, "items": finding},
                  "disagreements": {"type": "array", "maxItems": w.MAX_ITEMS, "uniqueItems": True,
                                    "items": identifier, "description": "Existing finding IDs only; never prose, scope notes or history."}})
    contract = {"schema": PRODUCER_CONTRACT_SCHEMA, "context_sha256": prepared["context_sha256"],
                "reviewer_id": reviewer_id, "model": model, "effort": effort, "response_key": response_key,
                "correction_artifact_ids": correction_ids,
                "output_schema": obj({response_key: record}),
                "instructions": (
                    "Return the exact keyed object required by output_schema. Schema constants do not establish substantive coverage. "
                    "If incomplete, report status failed and full_artifact_reviewed false. Findings require unique canonical IDs. "
                    "disagreements contains only IDs of findings in this same output; use [] if there is no current unresolved disagreement. "
                    "Put the substance of a disagreement in its finding.reason, with its severity, status and evidence references. "
                    "Assess current report defects and current unresolved disagreements as findings. Discuss genuinely corrected historical critiques, "
                    "scope notes and comparisons in judgment rationales, without duplicating them as new resolved or disputed findings. "
                    "If an earlier correction is inadequate, report the actual remaining current financial defect. Do not suppress a real current disagreement. "
                    "A resolved finding requires an actually inspected correction-role artifact from correction_artifact_ids and resolution_verified true. "
                    "If that list is empty, resolved findings are impossible. Open or disputed findings require resolution_artifact null and resolution_verified false. "
                    "A scope statement, historical comparison or confirmation is not itself a current disagreement. "
                    "Do not erase real unresolved disagreements or change their severity to pass. "
                    "Assess all financial dimensions and challenge suspect arithmetic; deterministic replay is separate assurance. "
                    "The existing consumer checks dynamic references, finding resolutions, full coverage and unresolved findings. "
                    "A schema-valid output is not report acceptance. No evidence, code, grading or delivered artifact may be edited.")}
    contract["contract_sha256"] = w.sha(contract)
    return contract


def _producer_json(value, depth=0):
    """Bound public/synthetic JSON before hashing or journal persistence."""
    if depth > 32:
        raise ValueError("reviewer output exceeds nesting limit")
    if isinstance(value, dict):
        if len(value) > w.MAX_ITEMS or any(not isinstance(key, str) for key in value):
            raise ValueError("reviewer JSON requires bounded string-keyed objects")
        for item in value.values():
            _producer_json(item, depth + 1)
    elif isinstance(value, list):
        if len(value) > w.MAX_ITEMS:
            raise ValueError("reviewer JSON exceeds item limit")
        for item in value:
            _producer_json(item, depth + 1)
    elif value is not None and type(value) not in (str, bool, int, float):
        raise ValueError("reviewer output must contain only JSON values")
    if depth == 0:
        _private(value)
        if len(w.canonical(value)) > w.MAX_BYTES:
            raise ValueError("reviewer JSON exceeds byte limit")


def validate_reviewer_contract(contract):
    """Reject edited schemas, even if a caller recomputes their local digest.

    This checks the canonical producer structure. The prepared-context comparison
    in consume_reviewer_output still binds it to the actual source/artifact task.
    """
    _producer_json(contract)
    try:
        record = contract["output_schema"]["properties"][contract["response_key"]]["properties"]
        prepared = {"context_sha256": contract["context_sha256"],
                    "required_coverage": record["coverage"]["const"],
                    "not_applicable_checks": record["not_applicable_checks"]["const"]}
        correction_ids = _ids(contract["correction_artifact_ids"], "contract correction IDs", prepared["required_coverage"]["artifacts"])
        # Structural replay uses the declared set. The consumer independently
        # regenerates it from actual prepared roles, rejecting forged role sets.
        prepared["artifacts"] = {key: {"role": "correction" if key in correction_ids else "source"}
                                 for key in prepared["required_coverage"]["artifacts"]}
        expected = reviewer_contract(prepared, reviewer_id=contract["reviewer_id"], model=contract["model"],
                                     effort=contract["effort"], response_key=contract["response_key"])
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError("malformed reviewer producer contract") from exc
    if contract != expected:
        raise ValueError("reviewer producer contract changed")
    return True


def _matches_producer_schema(schema, value):
    """Validate only the small JSON-schema subset generated above; no plugins."""
    if "const" in schema and w.canonical(value) != w.canonical(schema["const"]):
        return False
    if "enum" in schema and all(w.canonical(value) != w.canonical(item) for item in schema["enum"]):
        return False
    if "anyOf" in schema and not any(_matches_producer_schema(branch, value) for branch in schema["anyOf"]):
        return False
    expected_type = schema.get("type")
    if expected_type == "object":
        if not isinstance(value, dict) or set(value) != set(schema["required"]):
            return False
        return all(_matches_producer_schema(subschema, value[key]) for key, subschema in schema["properties"].items())
    if expected_type == "array":
        if not isinstance(value, list) or len(value) > schema.get("maxItems", w.MAX_ITEMS):
            return False
        if schema.get("uniqueItems") and len({w.canonical(item) for item in value}) != len(value):
            return False
        return all(_matches_producer_schema(schema["items"], item) for item in value)
    if expected_type == "string":
        return (isinstance(value, str) and schema.get("minLength", 0) <= len(value) <= schema.get("maxLength", w.MAX_BYTES)
                and ("pattern" not in schema or re.search(schema["pattern"], value) is not None))
    if expected_type == "boolean":
        return type(value) is bool
    if expected_type == "null":
        return value is None
    return expected_type is None


def reviewer_output_schema_valid(contract, output):
    """Schema validity is distinct from source truth and financial acceptance."""
    validate_reviewer_contract(contract)
    _producer_json(output)
    return _matches_producer_schema(contract["output_schema"], output)


def consume_reviewer_output(contract, request, prepared, output):
    """Consume a generated producer contract without repairing the model's output."""
    if not isinstance(contract, dict):
        raise ValueError("reviewer producer contract must be an object")
    expected = reviewer_contract(prepared, reviewer_id=contract.get("reviewer_id"), model=contract.get("model"),
                                 effort=contract.get("effort"), response_key=contract.get("response_key"))
    if contract != expected:
        raise ValueError("reviewer producer contract changed")
    key = contract["response_key"]
    _fields(output, key, label="native reviewer output")
    _private(output)
    reviewer = output[key]
    if not isinstance(reviewer, dict) or any(reviewer.get(name) != expected_value for name, expected_value in (
            ("id", contract["reviewer_id"]), ("kind", "model"), ("model", contract["model"]),
            ("effort", contract["effort"]), ("context_sha256", prepared["context_sha256"]))):
        raise ValueError("reviewer identity or context differs from producer contract")
    submitted = {**request, "reviewers": [copy.deepcopy(reviewer)]}
    blockers = (_reviewers(submitted, prepared) if reviewer_output_schema_valid(contract, output)
                else ["reviewer_missing_malformed_stale_or_incomplete"])
    return {"status": "withheld" if blockers else "accepted", "blockers": blockers,
            "reviewer": copy.deepcopy(reviewer), "contract_sha256": contract["contract_sha256"]}


def review(packet, bundle, request, artifacts_directory):
    prepared = prepare_context(packet, bundle, request, artifacts_directory)
    blockers = _reviewers(request, prepared)
    receipt = {"schema": RECEIPT_SCHEMA, "id": request["id"], "classification": request["classification"],
               "status": "withheld" if blockers else "accepted", "blockers": blockers,
               "request_sha256": w.sha(request), "context_sha256": prepared["context_sha256"],
               "packet_sha256": w.sha(packet), "code_sha256": code_hashes(),
               "calculation_manifest_sha256": prepared["context"]["calculation_manifest_sha256"],
               "reviewed_at": request["reviewed_at"], "required_coverage": prepared["required_coverage"],
               "artifact_sha256": {k: a["sha256"] for k, a in prepared["artifacts"].items()},
               "source_origins": prepared["source_origins"], "source_origin_count": len(prepared["source_origins"]),
               "scenario_results": prepared["context"]["scenario_results"],
               "render_state_outcomes": [{"id": c["id"], "surface": c["surface"], "state": c["state"],
                                           "outcome": c["outcome"], "applicability": c.get("applicability")}
                                          for c in request["render_checks"]],
               "render_check_counts": {status: sum(c["outcome"] == status for c in request["render_checks"])
                                       for status in ("pass", "fail", "unavailable", "not_applicable")},
               "assurance": {"mechanical": "calculation replay, exact inspected spans, declared coverage and artifact integrity",
                             "semantic": "separate client-reported reviewer judgment; completeness and source truth require challenge",
                             "identity": "client-reported; no reviewer execution or expert qualification attestation",
                             "privacy": "reviewed public/synthetic only; canary checks are not automatic de-identification",
                             "authenticity": "unsigned local integrity record; edits plus recomputed hashes are not forgery-resistant"},
               "production_eligible": False, "financial_execution_authorized": False}
    receipt["receipt_sha256"] = w.sha(receipt)
    return receipt


def write_review(packet, bundle, request, artifacts_directory, directory):
    receipt = review(packet, bundle, request, artifacts_directory)
    artifacts, blobs = _artifacts(request, artifacts_directory)
    target = w.safe_path(directory, must_exist=False)
    if target.exists():
        raise ValueError("review output exists; original drafts and decisions are never overwritten")
    target.mkdir(parents=True, exist_ok=False)
    # These snapshots include only the explicitly validated public/synthetic set.
    for name, value in (("review-request.json", request), ("review-receipt.json", receipt), ("evidence.json", packet)):
        with (target / name).open("xb") as stream:
            stream.write(w.canonical(value) + b"\n")
    archive = target / "artifacts"
    archive.mkdir()
    for aid, artifact in artifacts.items():
        path = archive.joinpath(*PurePosixPath(artifact["path"]).parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(blobs[aid])
    calculation = target / "calculation"
    calculation.mkdir()
    for name in w.bundle_bytes(packet):
        with (calculation / name).open("xb") as stream:
            stream.write((Path(bundle) / name).read_bytes())
    graph = ProvenanceGraph(str(target / "provenance.json"))
    dependencies = {"review:packet": packet, "review:scope": packet["scope"],
                    "review:sources": request["source_reviews"], "review:methods": request["methods"],
                    "review:code": receipt["code_sha256"], "review:task": request["task"],
                    "review:external-calculations": request.get("external_calculations", []),
                    "review:delivered": receipt["artifact_sha256"], "review:judgment": request["reviewers"]}
    for key, value in dependencies.items():
        graph.register_fact(key, w.canonical(value))
    graph.record_artifact("review:accepted-report", sorted(dependencies), "tools/fis/report_review.py",
                          receipt["code_sha256"]["report_review.py"], w.canonical(receipt),
                          {"status": receipt["status"], "classification": receipt["classification"]})
    files = {p.relative_to(target).as_posix(): _hash(p.read_bytes()) for p in target.rglob("*") if p.is_file()}
    with (target / "archive-manifest.json").open("xb") as stream:
        stream.write(w.canonical({"schema": "osanwe.review-archive/1", "files": files}) + b"\n")
    return {"status": receipt["status"], "directory": str(target), "receipt_sha256": receipt["receipt_sha256"],
            "blockers": receipt["blockers"]}


def verify_review(directory, *, historical=False, current_packet=None, current_request=None):
    target = w.safe_path(directory, must_exist=False)
    manifest = w.load_packet(target / "archive-manifest.json")
    _fields(manifest, "schema files")
    if manifest["schema"] != "osanwe.review-archive/1" or not isinstance(manifest["files"], dict):
        raise ValueError("unsupported review archive")
    actual = {p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file()}
    if actual != set(manifest["files"]) | {"archive-manifest.json"}:
        raise ValueError("review archive file set changed")
    for name, digest in manifest["files"].items():
        data = _relative(target, name).read_bytes()
        if _hash(data) != digest:
            raise ValueError("review archive was edited")
    request = w.load_packet(target / "review-request.json")
    receipt = w.load_packet(target / "review-receipt.json")
    packet = w.load_packet(target / "evidence.json")
    _private(request)
    _private(packet)
    body = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    if receipt.get("schema") != RECEIPT_SCHEMA or w.sha(body) != receipt.get("receipt_sha256") or w.sha(request) != receipt.get("request_sha256") or w.sha(packet) != receipt.get("packet_sha256"):
        raise ValueError("review receipt integrity failed")
    changed = receipt["code_sha256"] != code_hashes()
    input_changed = ((current_packet is not None and w.sha(current_packet) != receipt["packet_sha256"])
                     or (current_request is not None and w.sha(current_request) != receipt["request_sha256"]))
    current = False
    if not historical and not changed and not input_changed:
        regenerated = review(packet, target / "calculation", request, target / "artifacts")
        if regenerated != receipt:
            raise ValueError("review no longer agrees with current validation")
        current = receipt["status"] == "accepted"
    return {"historical_integrity": True, "current_eligible": current,
            "status": "historical_only" if historical else "stale" if changed or input_changed else receipt["status"],
            "code_changed": changed, "input_changed": input_changed,
            "source_currency": "not_live_checked", "verified_at": datetime.now(timezone.utc).isoformat(),
            "scope": "eligibility for this archived task only; pass current packet/request to compare changed inputs; not live source freshness or authenticity"}
