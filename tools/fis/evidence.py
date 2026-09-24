"""Stateless numeric-claim adapter for the existing FIS ontology/provenance layer.

No database, retrieval, recommendation, or execution. A validated envelope proves
declared semantics are internally consistent, not that a source actually says it.
Use ontology fact IDs and provenance artifact IDs as claim/input IDs when stored.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

KINDS = {"reported", "user_observation", "calculated", "estimate", "assumption", "forecast"}


def timestamp(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp requires a nonempty string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp requires an explicit timezone")
    return parsed.astimezone(timezone.utc)


def finite(value):
    try:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    except OverflowError:
        return False


def nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def unique_object(pairs):
    """A duplicate JSON field is conflicting source shape, not last-writer-wins."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def numeric_token_in_text(token, text):
    """A source token cannot be fabricated by selecting digits inside another number."""
    return (isinstance(token, str) and isinstance(text, str)
            and re.search(r"(?<![\d.,()+-])" + re.escape(token) + r"(?![\d.,()+-])", text) is not None)


def validate_source_review(review, source, claims, snapshot, *, knowledge_cutoff, report_at, original_snapshot=None):
    """Check inspected source support, preserving the packet/1 contract.

    Source labels and reviewer identity remain declarations requiring semantic
    challenge. Exact passages, numeric mappings and version availability are
    mechanically checked; source_checked by itself grants no reviewed status.
    A review selects one available version. Superseded/retracted versions remain
    append-only provenance history and cannot support current accepted analysis.
    """
    import hashlib
    from decimal import Decimal, InvalidOperation
    from urllib.parse import urlsplit

    if not isinstance(review, dict) or not isinstance(source, dict) or not isinstance(snapshot, bytes):
        raise ValueError("source review requires records and immutable snapshot bytes")
    required = {"id", "source_id", "snapshot_artifact", "source_version", "origin_uri",
                "relationship", "revision_status", "supersedes", "inspected_at", "inspected_by", "mappings"}
    if required - review.keys() or review.keys() - required - {"original_snapshot_artifact"}:
        raise ValueError("source review schema is incomplete or contains unsupported fields")
    for key in ("id", "source_id", "snapshot_artifact", "source_version", "origin_uri", "inspected_by"):
        if not nonempty_string(review[key]):
            raise ValueError("source review requires identifiers, version, origin and inspector")
    if review["source_id"] != source["id"]:
        raise ValueError("source review references the wrong source")
    if review["relationship"] not in {"direct", "mirror", "derived"}:
        raise ValueError("source-origin relationship is required")
    origin = urlsplit(review["origin_uri"])
    if origin.scheme not in {"https", "synthetic"} or origin.username or origin.password or (origin.scheme == "https" and not origin.hostname):
        raise ValueError("source origin must be public HTTPS or synthetic")
    if review["relationship"] == "direct" and review["origin_uri"] != source["uri"]:
        raise ValueError("direct source origin must match the inspected source")
    if review["revision_status"] not in {"original", "restated", "retracted"}:
        raise ValueError("source revision status is required")
    predecessors = review["supersedes"]
    if not isinstance(predecessors, list) or len(predecessors) != len(set(predecessors)) or any(not nonempty_string(x) for x in predecessors) or review["id"] in predecessors:
        raise ValueError("source revision predecessors must be unique earlier review IDs")
    if (review["revision_status"] == "original" and predecessors) or (review["revision_status"] != "original" and not predecessors):
        raise ValueError("source revision must preserve its predecessor relationship")
    if review["revision_status"] == "retracted":
        raise ValueError("retracted sources are history, not eligible support")
    inspected = timestamp(review["inspected_at"])
    if not timestamp(source["retrieved_at"]) <= inspected <= timestamp(report_at):
        raise ValueError("source inspection must follow retrieval and precede review")
    if timestamp(source["available_at"]) > timestamp(knowledge_cutoff):
        raise ValueError("source revision was unavailable at the decision cutoff")
    inspected_bytes = original_snapshot if original_snapshot is not None else snapshot
    if not isinstance(inspected_bytes, bytes):
        raise ValueError("original source snapshot bytes are required")
    if source.get("content_sha256") and source["content_sha256"] != hashlib.sha256(inspected_bytes).hexdigest():
        raise ValueError("inspected snapshot is not the source version in the packet")
    try:
        original = snapshot.decode("utf-8")
    except UnicodeError as exc:
        raise ValueError("source inspection requires an exact UTF-8 passage or reviewed table export") from exc
    indexed = {claim["id"]: claim for claim in claims}
    mappings = review["mappings"]
    if not isinstance(mappings, list):
        raise ValueError("source mappings must be a list")
    seen = set()
    for mapping in mappings:
        required_mapping = {"claim_id", "original_label", "normalized_metric", "value_token", "multiplier",
                            "unit", "currency", "basis", "as_of", "support"}
        if not isinstance(mapping, dict) or required_mapping - mapping.keys() or mapping.keys() - required_mapping - {"period_start", "period_end", "original_support"}:
            raise ValueError("source mapping is incomplete or has unsupported fields")
        claim = indexed.get(mapping["claim_id"])
        if claim is None or claim["source"] != source["id"] or claim["id"] in seen:
            raise ValueError("mapping uses the wrong source, claim, or duplicate mapping")
        seen.add(claim["id"])
        if mapping["normalized_metric"] != claim["metric"]:
            raise ValueError("source semantic mapping disagrees with the numeric claim")
        span = mapping["support"]
        if not isinstance(span, dict) or set(span) != {"artifact_id", "start", "end", "text", "locator"}:
            raise ValueError("source support requires exact inspected passage or table-cell span")
        start, end, text = span["start"], span["end"], span["text"]
        if type(start) is not int or type(end) is not int or not isinstance(text, str) or start < 0 or end <= start or end > len(original) or original[start:end] != text or span["artifact_id"] != review["snapshot_artifact"]:
            raise ValueError("source excerpt differs from the source snapshot")
        if not nonempty_string(span["locator"]) or not nonempty_string(mapping["original_label"]) or mapping["original_label"] not in text:
            raise ValueError("original source label and inspected locator are required")
        token = mapping["value_token"]
        if not isinstance(token, str) or not re.fullmatch(r"[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\((?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?\)", token) or not numeric_token_in_text(token, text):
            raise ValueError("source numeric token must occur in the inspected passage")
        if original_snapshot is not None:
            original_span = mapping.get("original_support")
            if not isinstance(original_span, dict) or set(original_span) != {"artifact_id", "start", "end", "text", "locator"}:
                raise ValueError("extracted source mappings require original passage or table-cell support")
            try:
                origin_text = original_snapshot.decode("utf-8")
            except UnicodeError as exc:
                raise ValueError("original source support must be UTF-8") from exc
            start, end, exact = original_span["start"], original_span["end"], original_span["text"]
            if (type(start) is not int or type(end) is not int or not isinstance(exact, str) or start < 0 or end <= start
                    or end > len(origin_text) or origin_text[start:end] != exact
                    or original_span["artifact_id"] != review.get("original_snapshot_artifact")
                    or mapping["original_label"] not in exact or not numeric_token_in_text(token, exact)):
                raise ValueError("extracted source support does not reconcile to the original inspected bytes")
        elif "original_support" in mapping:
            raise ValueError("original support cannot refer to an undeclared original source snapshot")
        multiplier = mapping["multiplier"]
        if not finite(multiplier) or multiplier <= 0:
            raise ValueError("source normalization multiplier must be positive and finite")
        try:
            number = Decimal(token.replace(",", "").replace("(", "-").replace(")", ""))
            if number * Decimal(str(multiplier)) != Decimal(str(claim["value"])):
                raise ValueError("source number and declared normalization do not equal the claim")
        except InvalidOperation as exc:
            raise ValueError("source numeric normalization is invalid") from exc
        for key in ("unit", "currency", "basis", "as_of", "period_start", "period_end"):
            if mapping.get(key) != claim.get(key):
                raise ValueError("source mapping changes unit, currency, basis or period")
    return {"status": "mechanically_supported", "source_id": source["id"],
            "source_version": review["source_version"], "claim_ids": sorted(seen),
            "source_truth": "requires separate semantic reviewer judgment"}


def add_integration_draft(ontology, claim, *, classification, report_at, knowledge_cutoff=None):
    """Explicit draft bridge into the existing append-only ontology.

    This function does not change the historical add_fact default or promote a
    fact. The caller owns the authorized destination and entity registration.
    Public/synthetic persisted facts require prior privacy review by the caller.
    """
    if classification not in {"public", "synthetic"}:
        raise ValueError("persistent integration facts must be public or synthetic")
    errors = validate_claim(claim, report_at=report_at, knowledge_cutoff=knowledge_cutoff)
    if errors:
        raise ValueError("integration claim failed validation")
    return ontology.add_fact(subject_id=claim["entity"], predicate=claim["metric"], value=claim["value"],
                             source=claim["source"], effective_time=timestamp(claim["as_of"]).date().isoformat(),
                             known_time=timestamp(claim["available_at"]).date().isoformat(),
                             units=claim["unit"], currency=claim["currency"], validation_status="draft")


def validate_claim(claim, *, report_at, knowledge_cutoff=None):
    """Return exact reasons a claim cannot support the requested analysis.

    report_at is when the analysis is produced; knowledge_cutoff is what could
    have been known in a historical decision. Retrieval today does not make a
    publication available yesterday. Caller declares freshness policy by metric.
    """
    errors = []
    now = timestamp(report_at)
    cutoff = timestamp(knowledge_cutoff) if knowledge_cutoff else now
    if cutoff > now:
        raise ValueError("knowledge_cutoff is later than report_at")
    if not isinstance(claim, Mapping):
        return ["claim: object required"]
    for key in ("id", "entity", "metric", "unit", "currency", "basis", "source", "source_locator"):
        if not nonempty_string(claim.get(key)):
            errors.append(f"{key}: required nonempty string")
        elif key not in {"source", "source_locator"} and claim[key] != claim[key].strip():
            errors.append(f"{key}: leading/trailing whitespace is not a canonical identifier")
    kind = claim.get("kind")
    if not isinstance(kind, str) or kind not in KINDS:
        errors.append("kind: reported/user_observation/calculated/estimate/assumption/forecast required")
        kind = None
    if not finite(claim.get("value")):
        errors.append("value: missing or nonfinite; unknown is not zero")
    currency, unit = claim.get("currency"), claim.get("unit")
    if not isinstance(currency, str) or not re.fullmatch(r"(?:[A-Z]{3}|NONE)", currency):
        errors.append("currency: uppercase currency code or NONE required")
    if isinstance(unit, str):
        if unit in {"currency", "currency/share", "thousands", "millions", "billions"} and currency == "NONE":
            errors.append("currency: monetary amounts require an explicit currency")
        if unit in {"shares", "fraction", "percent", "ratio", "count", "basis_points"} and currency != "NONE":
            errors.append("currency: dimensionless/count quantities require NONE")
    times = {}
    for key in ("as_of", "published_at", "available_at", "retrieved_at"):
        try:
            times[key] = timestamp(claim[key])
        except (KeyError, TypeError, ValueError, AttributeError):
            errors.append(f"{key}: valid timezone-aware timestamp required")
    if len(times) == 4:
        if times["published_at"] > times["available_at"] or times["available_at"] > times["retrieved_at"]:
            errors.append("publication <= availability <= retrieval required")
        if times["retrieved_at"] > now:
            errors.append("retrieved_at: future retrieval")
        if times["available_at"] > cutoff:
            errors.append("available_at: future information beyond knowledge cutoff")
        if kind != "forecast" and times["as_of"] > cutoff:
            errors.append("as_of: future observation is not a reported result")
        if kind in {"reported", "user_observation"} and times["as_of"] > times["published_at"]:
            errors.append("as_of: an actual observation cannot postdate its publication")
        # Forecast target dates are not observation timestamps. A target years
        # ahead cannot keep an old forecast indefinitely fresh.
        # A late vendor delivery also cannot refresh an old published forecast.
        freshness_time = times["published_at"] if kind == "forecast" else times["as_of"]
        age = (cutoff - freshness_time).total_seconds() / 86400
        window = claim.get("max_age_days")
        if not finite(window) or window < 0 or not nonempty_string(claim.get("freshness_policy")):
            errors.append("freshness: nonnegative max_age_days and policy rationale required")
        elif age > window:
            errors.append("freshness: stale for the declared use and policy")
    temporal_type = claim.get("temporal_type")
    if not isinstance(temporal_type, str) or temporal_type not in {"point", "flow"}:
        errors.append("temporal_type: point or flow required")
    if temporal_type == "point" and any(key in claim for key in ("period_start", "period_end", "frequency")):
        errors.append("period: point claims cannot carry flow period/frequency fields")
    if temporal_type == "flow":
        try:
            start, end = timestamp(claim["period_start"]), timestamp(claim["period_end"])
            if start >= end:
                errors.append("period: start must precede end")
            if claim.get("kind") != "forecast" and end > cutoff:
                errors.append("period_end: future reported period")
            if "as_of" in times and end != times["as_of"]:
                errors.append("period_end must equal as_of for a flow")
        except (KeyError, TypeError, ValueError, AttributeError):
            errors.append("period: flow requires timezone-aware start/end")
        if not nonempty_string(claim.get("frequency")):
            errors.append("frequency: flow requires fiscal frequency")
    if kind == "calculated":
        inputs = claim.get("inputs")
        if (not isinstance(inputs, list) or not inputs
                or any(not nonempty_string(value) for value in inputs)
                or not nonempty_string(claim.get("transformation"))):
            errors.append("calculation: input IDs and transformation required")
        elif len(inputs) != len(set(inputs)) or claim.get("id") in inputs:
            errors.append("calculation: duplicate or self-referential input IDs")
    return errors


def compatible(left, right, *, allow_period_change=False):
    """Disallow silent currency, unit, GAAP/adjusted, nominal/real, split or type mixing.

    basis is an explicit semantic identifier, e.g. 'GAAP:nominal:split-adjusted'.
    Cross-period growth must opt in; fiscal frequency remains required to agree.
    """
    if not isinstance(left, Mapping) or not isinstance(right, Mapping):
        raise ValueError("comparison requires claim objects")
    if not isinstance(allow_period_change, bool):
        raise ValueError("allow_period_change must be an explicit boolean")
    keys = ["metric", "unit", "currency", "basis", "kind", "temporal_type"]
    if left.get("temporal_type") == "flow" or right.get("temporal_type") == "flow":
        keys += ["frequency"]
        if not allow_period_change:
            keys += ["period_start", "period_end"]
    elif not allow_period_change:
        keys += ["as_of"]
    conflicts = []
    for key in keys:
        a, b = left.get(key), right.get(key)
        if not nonempty_string(a) or not nonempty_string(b):
            conflicts.append(key)
        elif key in {"as_of", "period_start", "period_end"}:
            try:
                if timestamp(a) != timestamp(b):
                    conflicts.append(key)
            except ValueError:
                conflicts.append(key)
        elif a != b:
            conflicts.append(key)
    for record in (left, right):
        if not isinstance(record.get("kind"), str) or record["kind"] not in KINDS:
            conflicts.append("kind")
        if record.get("temporal_type") == "flow":
            try:
                start, end = timestamp(record.get("period_start")), timestamp(record.get("period_end"))
                if start >= end or end != timestamp(record.get("as_of")):
                    conflicts.append("period")
            except ValueError:
                conflicts.append("period")
        elif record.get("temporal_type") != "point":
            conflicts.append("temporal_type")
        elif any(key in record for key in ("period_start", "period_end", "frequency")):
            conflicts.append("period")
    return list(dict.fromkeys(conflicts))


def market_cap(price, shares, *, report_at, max_alignment_days, knowledge_cutoff=None):
    """Price * outstanding shares with explicit freshness/alignment and split basis.

    The permitted shares-price lag is supplied and disclosed by the caller; this
    function never silently treats an old filing count as today's actual count.
    """
    errors = (validate_claim(price, report_at=report_at, knowledge_cutoff=knowledge_cutoff)
              + validate_claim(shares, report_at=report_at, knowledge_cutoff=knowledge_cutoff))
    if not finite(max_alignment_days) or max_alignment_days < 0:
        raise ValueError("max_alignment_days must be nonnegative and finite")
    if errors:
        raise ValueError("; ".join(errors))
    if (price["entity"] != shares["entity"] or price["basis"] != shares["basis"]
            or price["id"] == shares["id"]
            or price["metric"] not in {"price", "share_price"}
            or shares["metric"] not in {"shares", "shares_outstanding"}
            or price["unit"] != "currency/share" or shares["unit"] != "shares"
            or shares["currency"] != "NONE" or price["currency"] == "NONE"
            or price["kind"] != "reported" or shares["kind"] != "reported"
            or price["temporal_type"] != "point" or shares["temporal_type"] != "point"):
        raise ValueError("price/shares entity, split basis, actual status or units incompatible")
    lag = abs((timestamp(price["as_of"]) - timestamp(shares["as_of"])).total_seconds()) / 86400
    if lag > max_alignment_days:
        raise ValueError("shares count and price are temporally misaligned")
    if price["value"] < 0 or shares["value"] <= 0:
        raise ValueError("price must be nonnegative and shares positive")
    result = price["value"] * shares["value"]
    if not math.isfinite(result):
        raise ValueError("market cap overflow")
    return {"value": result, "currency": price["currency"], "kind": "calculated",
            "inputs": [price["id"], shares["id"]], "transformation": "price * shares",
            "alignment_days": lag, "max_alignment_days": max_alignment_days}


def weighted_overlap(left, right):
    """Long-only constituent weights, keyed by stable instrument ID (not ticker).

    Partial holdings are not renormalized. This is weight arithmetic only:
    complete describes the supplied weights, not source freshness/coverage.
    Use holdings_overlap for source-enveloped, temporally aligned comparisons.
    """
    for holdings in (left, right):
        if not isinstance(holdings, dict) or not holdings:
            raise ValueError("holdings must be a nonempty instrument->weight mapping")
        if any(not isinstance(k, str) or not k.strip() or k != k.strip() or not finite(v) or v < 0
               for k, v in holdings.items()):
            raise ValueError("invalid instrument or weight")
        if sum(holdings.values()) > 1 + 1e-9:
            raise ValueError("holdings exceed 100%; duplicates/leverage require explicit modeling")
    a, b = sum(left.values()), sum(right.values())
    return {"overlap": sum(min(v, right.get(k, 0)) for k, v in left.items()),
            "coverage_left": a, "coverage_right": b,
            "complete": abs(a - 1) <= 1e-9 and abs(b - 1) <= 1e-9,
            "scope": "supplied_weights_only", "freshness_validated": False}


def holdings_overlap(left, right, *, report_at, max_alignment_days, knowledge_cutoff=None):
    """Validate disclosed holdings snapshots before comparing their weights.

    Each side contains a `claim` with metric holdings_coverage, value equal to
    the disclosed weight sum, unit fraction, and a `holdings` ID->weight map.
    Declared source semantics are checked; independent source review is still
    needed to establish that the provider actually disclosed those holdings.
    """
    if not finite(max_alignment_days) or max_alignment_days < 0:
        raise ValueError("max_alignment_days must be nonnegative and finite")
    for snapshot in (left, right):
        if not isinstance(snapshot, Mapping):
            raise ValueError("holdings snapshot must be an object")
        source = snapshot.get("claim")
        errors = validate_claim(source, report_at=report_at, knowledge_cutoff=knowledge_cutoff)
        if errors:
            raise ValueError("; ".join(errors))
        if (source["metric"] != "holdings_coverage" or source["unit"] != "fraction"
                or source["currency"] != "NONE" or source["temporal_type"] != "point"
                or source["kind"] not in {"reported", "user_observation"}):
            raise ValueError("holdings require an actual point-in-time coverage fraction")
    result = weighted_overlap(left.get("holdings"), right.get("holdings"))
    for snapshot, coverage in ((left, result["coverage_left"]), (right, result["coverage_right"])):
        if abs(snapshot["claim"]["value"] - coverage) > 1e-9:
            raise ValueError("declared coverage does not equal the disclosed holdings weight sum")
    a, b = left["claim"], right["claim"]
    if a["id"] == b["id"] and (a != b or left["holdings"] != right["holdings"]):
        raise ValueError("same source claim ID carries conflicting holdings snapshots")
    if a["basis"] != b["basis"]:
        raise ValueError("holdings weight bases conflict")
    lag = abs((timestamp(a["as_of"]) - timestamp(b["as_of"])).total_seconds()) / 86400
    if lag > max_alignment_days:
        raise ValueError("holdings snapshots are temporally misaligned")
    result.update(scope="declared_snapshot_semantics", freshness_validated=True,
                  alignment_days=lag, max_alignment_days=max_alignment_days,
                  inputs=[a["id"], b["id"]])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("envelope", type=Path, help="JSON with report_at, claims, optional knowledge_cutoff")
    args = parser.parse_args()
    try:
        data = json.loads(args.envelope.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        if not isinstance(data, dict):
            raise ValueError("envelope must be an object")
        if not isinstance(data.get("claims"), list) or not data["claims"]:
            raise ValueError("claims must be a nonempty list")
        results = []
        seen = set()
        for claim in data["claims"]:
            errors = validate_claim(claim, report_at=data["report_at"], knowledge_cutoff=data.get("knowledge_cutoff"))
            claim_id = claim.get("id") if isinstance(claim, Mapping) else None
            if isinstance(claim_id, str) and claim_id in seen:
                errors.append("id: duplicate claim")
            if isinstance(claim_id, str):
                seen.add(claim_id)
            results.append({"id": claim_id if isinstance(claim_id, str) else None, "errors": errors})
        print(json.dumps({"scope": "declared semantics only; source support requires review", "results": results}, indent=2))
        return int(any(r["errors"] for r in results))
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
