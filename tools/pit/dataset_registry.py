#!/usr/bin/env python3
"""dataset_registry.py -- D7: full metadata records for FIS datasets (v3).

Extends the dataset-manifest system (Efforts/osanwe-v2-overhaul/_work/
fis-baseline/dataset-manifest-2026-08-25.json[.-v2.json]) with a complete
provenance record per dataset:

  dataset_id, version, sha256, source_url_or_path, retrieval_timestamp,
  license_status in {verified-open, verified-self-produced, unverified},
  schema_summary, units, currency, timezone, coverage_dates,
  missingness_pct, known_defects, transformation_lineage,
  validation_tests, owner

Usage:
  python dataset_registry.py --build          regenerate the registry
  python dataset_registry.py --selftest       validate registry + recompute hashes
  python dataset_registry.py --documents-manifest  inspect current approved document scopes
  python dataset_registry.py --document-admit candidate.json  append a verified public/synthetic version

Stdlib only, no network. Writes ONLY under _work/fis-data/.
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime

try:
    from .financial_documents import (
        DOCUMENT_REGISTRY_OUT, DocumentAdmissionError, admit_document,
        append_document_version, append_document_retraction,
        approved_document_manifest, inventory_financial_documents,
    )
except ImportError:
    from financial_documents import (
        DOCUMENT_REGISTRY_OUT, DocumentAdmissionError, admit_document,
        append_document_version, append_document_retraction,
        approved_document_manifest, inventory_financial_documents,
    )

# --- paths ---------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # repo root (tools/pit/ -> root)
WORK = os.path.join(ROOT, "Efforts", "osanwe-v2-overhaul", "_work")
FACTORS_DB = os.path.join(WORK, "factors.db")
EDGAR_DIR = os.path.join(ROOT, "wiki", "investing", "filings")
FORM4_SUMMARY = os.path.join(EDGAR_DIR, "insider-form4-summary.json")
MANIFEST_V1 = os.path.join(WORK, "fis-baseline", "dataset-manifest-2026-08-25.json")
MANIFEST_V2 = os.path.join(WORK, "fis-baseline", "dataset-manifest-2026-08-25-v2.json")
REGISTRY_OUT = os.path.join(WORK, "fis-data", "dataset-registry.jsonl")

REQUIRED_FIELDS = [
    "dataset_id",
    "version",
    "sha256",
    "source_url_or_path",
    "retrieval_timestamp",
    "license_status",
    "schema_summary",
    "units",
    "currency",
    "timezone",
    "coverage_dates",
    "missingness_pct",
    "known_defects",
    "transformation_lineage",
    "validation_tests",
    "owner",
]
LICENSE_STATUSES = {"verified-open", "verified-self-produced", "unverified"}
REGISTRY_VERSION = "3"
OWNER = "<user>"

# Recorded post-ingest hash of factors.db from manifest v2
# (2026-08-25T15:36:45, R1 verification run). Reused instead of rehashing
# the >25MB database at every build; --selftest DOES rehash to verify.
FACTORS_DB_V2_SHA256 = (
    "ba373202f474903dfa6e320ff21a69a8b4cbdca93c54b53254a28782f4a16aed"
)


# --- hashing -------------------------------------------------------------
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_dir(path):
    """Deterministic aggregate hash over every file in a tree:
    sha256 over 'relpath\\0size\\0file-sha256\\n' lines, sorted by relpath."""
    h = hashlib.sha256()
    members = []
    for dirpath, _dirs, files in os.walk(path):
        for name in files:
            fp = os.path.join(dirpath, name)
            rel = os.path.relpath(fp, path).replace("\\", "/")
            members.append(rel)
    for rel in sorted(members):
        fp = os.path.join(path, rel.replace("/", os.sep))
        h.update(
            ("%s\x00%d\x00%s\n" % (rel, os.path.getsize(fp), sha256_file(fp))).encode("ascii")
        )
    return h.hexdigest()


def compute_sha256(kind, path):
    if kind == "directory":
        return sha256_dir(path)
    return sha256_file(path)


def mtime_iso(path):
    return datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%dT%H:%M:%S")


# --- entry builders ------------------------------------------------------
def entry_factors_db():
    """Physical sqlite store: bars (equity closes) + factors (macro series).
    Hash reused from manifest v2 (post-R1-ingest); cited, not recomputed here."""
    return {
        "dataset_id": "factors.db",
        "version": "3",
        "kind": "file",
        "sha256": FACTORS_DB_V2_SHA256,
        "source_url_or_path": "Efforts/osanwe-v2-overhaul/_work/factors.db",
        "retrieval_timestamp": "2026-08-25T15:36:45",
        "license_status": "unverified",
        "schema_summary": (
            "sqlite: bars(ticker,date,close,src PK ticker+date; 153095 rows, "
            "125 tickers, daily closes) + factors(ticker,date,factor,value,"
            "text_value,src PK ticker+date+factor; 121878 rows)"
        ),
        "units": (
            "bars.close: USD price; factors.value: series-native "
            "(pct/ratio/index/bps depending on factor)"
        ),
        "currency": "USD",
        "timezone": "America/New_York",
        "coverage_dates": {
            "start": "2015-01-02",
            "end": "2026-08-25",
            "note": "bars 2021-08-24..2026-08-25; macro factors 2015-01-02..2026-08-24",
        },
        "missingness_pct": 0.0,
        "known_defects": [],
        "transformation_lineage": {
            "parent_dataset_ids": [],
            "script_paths": ["tools/bulk-data-pull.py", "tools/factor-store.py"],
            "notes": "yfinance-5y bars + fred-csv / yfinance-bulk macro ingested into sqlite",
        },
        "validation_tests": [
            {"name": "row-count-check", "description": "bars=153095 factors=121878 rows present"},
            {"name": "pk-uniqueness", "description": "PRIMARY KEY constraints on both tables"},
            {"name": "manifest-v2-hash", "description": "sha256 matches dataset-manifest-2026-08-25-v2.json"},
        ],
        "owner": OWNER,
        "extra": {
            "bytes": 25198592,
            "manifest_source": "fis-baseline/dataset-manifest-2026-08-25-v2.json",
            "hash_provenance": "recorded post-ingest hash reused; selftest recomputes to verify",
        },
    }


def entry_edgar_corpus():
    n_files = sum(len(f) for _r, _d, f in os.walk(EDGAR_DIR))
    return {
        "dataset_id": "edgar-corpus",
        "version": "1",
        "kind": "directory",
        "sha256": "",  # filled by build (aggregate tree hash)
        "source_url_or_path": "wiki/investing/filings/",
        "retrieval_timestamp": "2026-08-25T15:08:14",
        "license_status": "verified-open",
        "schema_summary": (
            "%d JSON files under wiki/investing/filings/<TICKER>/: "
            "<T>-filings.json (list of {ticker,form,date,desc,doc}), "
            "<T>-xbrl[-extended].json (XBRL concept series), "
            "plus consolidated insider-form4-summary.json" % n_files
        ),
        "units": "n/a (filings metadata and as-reported XBRL values)",
        "currency": "USD",
        "timezone": "America/New_York",
        "coverage_dates": {
            "start": "2021-08-24",
            "end": "2026-08-25",
            "note": "per-ticker filing windows vary; frozen as-of manifest v1",
        },
        "missingness_pct": 0.0,
        "known_defects": [],
        "transformation_lineage": {
            "parent_dataset_ids": [],
            "script_paths": ["tools/edgar-scraper.py"],
            "notes": "SEC EDGAR company-concept XBRL + filings feeds scraped to JSON",
        },
        "validation_tests": [
            {"name": "tree-hash-stable", "description": "aggregate sorted-tree sha256 recomputes exactly"},
            {"name": "member-count", "description": "file count matches schema_summary"},
        ],
        "owner": OWNER,
        "extra": {
            "members": n_files,
            "manifest_source": "fis-baseline/dataset-manifest-2026-08-25.json (group=edgar_corpus)",
            "source_url": "https://www.sec.gov/ (public domain, SEC fair-access <=10 req/s)",
        },
    }


def entry_macro_factors():
    """Logical slice of factors table (ticker='MACRO'); shares the physical
    factors.db file, so its hash equals the factors.db entry's."""
    return {
        "dataset_id": "macro-factors",
        "version": "1",
        "kind": "file",
        "sha256": FACTORS_DB_V2_SHA256,
        "source_url_or_path": "Efforts/osanwe-v2-overhaul/_work/factors.db::factors(ticker='MACRO')",
        "retrieval_timestamp": "2026-08-24",
        "license_status": "unverified",
        "schema_summary": (
            "52 macro/market series (FRED CSV: rates, spreads, FX, energy, "
            "policy plumbing; yfinance-bulk: VIX family, FX pairs, commodities, "
            "regional indexes) keyed (date,factor,value,src); 6078 rows, "
            "no NULL values"
        ),
        "units": "series-native: pct (DGS*, UNRATE), index points (VIX, SP500-family), "
                 "ratio/spread (BAA10Y, T10Y2Y), bps OAS (BAML*), USD (DCOILWTICO, WALCL)",
        "currency": "USD",
        "timezone": "America/New_York",
        "coverage_dates": {"start": "2015-01-01", "end": "2026-08-24", "note": ""},
        "missingness_pct": 0.0,
        "known_defects": [
            "monthly series (CPIAUCSL/FEDFUNDS/UNRATE) forward-fill implicitly on join; "
            "use raw observation dates only",
        ],
        "transformation_lineage": {
            "parent_dataset_ids": ["factors.db"],
            "script_paths": ["tools/bulk-data-pull.py", "tools/macro-expansion.py"],
            "notes": "FRED CSV bulk download (stage 3) + yfinance market macro (stage 3b)",
        },
        "validation_tests": [
            {"name": "series-count", "description": "exactly 52 distinct factors"},
            {"name": "null-value-free", "description": "value IS NOT NULL for all MACRO rows"},
            {"name": "range-check", "description": "dates within 2015-01-01..2026-08-24"},
        ],
        "owner": OWNER,
        "extra": {
            "logical_view_of": "factors.db",
            "manifest_source": "_work/bulk-pull-manifest.json done_macro (28 FRED) + MACRO-X expansion",
        },
    }


def entry_form4_summary():
    return {
        "dataset_id": "insider-form4-summary.json",
        "version": "1",
        "kind": "file",
        "sha256": "",  # filled by build
        "source_url_or_path": "wiki/investing/filings/insider-form4-summary.json",
        "retrieval_timestamp": mtime_iso(FORM4_SUMMARY),
        "license_status": "verified-open",
        "schema_summary": (
            "{ticker: {form4_count: int, recent: [{date, desc}, ...]}} "
            "per-ticker Form 4 insider-transaction rollup (10 most recent each)"
        ),
        "units": "n/a (counts and dates)",
        "currency": "n/a",
        "timezone": "America/New_York",
        "coverage_dates": {
            "start": "2026-05-22",
            "end": "2026-08-20",
            "note": "most-recent-window across covered tickers; per-ticker windows vary",
        },
        "missingness_pct": 0.0,
        "known_defects": [],
        "transformation_lineage": {
            "parent_dataset_ids": ["edgar-corpus"],
            "script_paths": ["tools/edgar-scraper.py"],
            "notes": "consolidated from per-ticker <T>-filings.json form='4' rows",
        },
        "validation_tests": [
            {"name": "json-parse", "description": "loads as dict of dicts"},
            {"name": "hash-match", "description": "sha256 recomputation matches registry"},
        ],
        "owner": OWNER,
        "extra": {"derived_from_group": "edgar_corpus"},
    }


# --- build / write -------------------------------------------------------
def build_registry():
    entries = [entry_factors_db(), entry_edgar_corpus(), entry_macro_factors(), entry_form4_summary()]
    for e in entries:
        if e["dataset_id"] == "factors.db":
            continue  # reuse recorded manifest-v2 hash (do not rehash big db at build time)
        if e["kind"] == "directory":
            path = EDGAR_DIR
        else:
            path = FORM4_SUMMARY if "form4" in e["dataset_id"] else None
        if path:
            e["sha256"] = compute_sha256(e["kind"], path)
        if e["kind"] == "file" and os.path.exists(
            os.path.join(ROOT, e["source_url_or_path"].split("::")[0])
        ) and "form4" in e["dataset_id"]:
            e["extra"]["bytes"] = os.path.getsize(FORM4_SUMMARY)
    # macro-factors extra bytes reference the shared physical db
    for e in entries:
        if e["dataset_id"] == "macro-factors":
            e["extra"]["physical_bytes"] = os.path.getsize(FACTORS_DB)
        if e["dataset_id"] == "factors.db":
            e["extra"]["bytes"] = os.path.getsize(FACTORS_DB)
    return entries


def validate_entry(e):
    errs = []
    for k in REQUIRED_FIELDS:
        if k not in e:
            errs.append("%s: missing required field %s" % (e.get("dataset_id", "?"), k))
    if "license_status" in e and e["license_status"] not in LICENSE_STATUSES:
        errs.append("%s: bad license_status %r" % (e.get("dataset_id", "?"), e["license_status"]))
    tl = e.get("transformation_lineage", {})
    if isinstance(tl, dict):
        if "parent_dataset_ids" not in tl or "script_paths" not in tl:
            errs.append("%s: lineage needs parent_dataset_ids + script_paths" % e.get("dataset_id", "?"))
    if not isinstance(e.get("known_defects"), list):
        errs.append("%s: known_defects must be a list" % e.get("dataset_id", "?"))
    if not isinstance(e.get("validation_tests"), list):
        errs.append("%s: validation_tests must be a list" % e.get("dataset_id", "?"))
    return errs


def resolve_path(e):
    dsid = e["dataset_id"]
    if dsid == "factors.db" or dsid == "macro-factors":
        return FACTORS_DB
    if dsid == "edgar-corpus":
        return EDGAR_DIR
    if dsid == "insider-form4-summary.json":
        return FORM4_SUMMARY
    raise ValueError("unknown dataset_id %s" % dsid)


def selftest(registry_path):
    failures = []
    n = 0
    with open(registry_path, "r", encoding="ascii") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            n += 1
            e = json.loads(line)
            failures.extend("line %d: %s" % (lineno, x) for x in validate_entry(e))
            # hash recomputation must match recorded value
            try:
                actual = compute_sha256(e["kind"], resolve_path(e))
                if actual != e["sha256"]:
                    failures.append(
                        "line %d (%s): sha mismatch recorded=%s actual=%s"
                        % (lineno, e["dataset_id"], e["sha256"], actual)
                    )
            except Exception as exc:  # noqa: BLE001
                failures.append("line %d: hash recompute failed: %s" % (lineno, exc))
    print("selftest: %d entries checked" % n)
    if failures:
        for msg in failures:
            print("FAIL:", msg)
        return 1
    print("PASS: all required fields present; all sha256 recomputations match")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="FIS dataset registry v3 (D7)")
    ap.add_argument("--build", action="store_true", help="regenerate the registry jsonl")
    ap.add_argument("--selftest", action="store_true", help="validate fields + recompute hashes")
    ap.add_argument("--out", default=REGISTRY_OUT)
    ap.add_argument("--documents-manifest", action="store_true", help="read approved document scopes; never rebuild datasets")
    ap.add_argument("--document-admit", metavar="CANDIDATE_JSON", help="mechanically verify and append one public/synthetic document version")
    ap.add_argument("--documents-inventory", metavar="PATH_LIST_JSON", help="metadata-only inventory of explicit reference paths")
    ap.add_argument("--documents-registry", default=str(DOCUMENT_REGISTRY_OUT))
    ap.add_argument("--root", default=ROOT, help="workspace root for document path confinement")
    ap.add_argument("--as-of", help="timezone-aware document eligibility cutoff")
    ap.add_argument("--scope", help="approved document-use scope token")
    args = ap.parse_args(argv)

    if args.documents_manifest or args.document_admit or args.documents_inventory:
        if sum(bool(x) for x in (args.documents_manifest, args.document_admit, args.documents_inventory, args.build, args.selftest)) != 1:
            ap.error("select exactly one document or legacy dataset operation")
        def unique_document_pairs(pairs):
            result = {}
            for key, value in pairs:
                if key in result: raise ValueError("duplicate document metadata key")
                result[key] = value
            return result
        def reject_nonfinite(value):
            raise ValueError("nonfinite document metadata")
        try:
            if args.documents_manifest:
                result = approved_document_manifest(args.documents_registry, args.root, as_of=args.as_of, scope=args.scope)
            elif args.document_admit:
                with open(args.document_admit, "r", encoding="utf-8") as handle:
                    candidate = json.load(handle, object_pairs_hook=unique_document_pairs, parse_constant=reject_nonfinite)
                record = append_document_version(args.documents_registry, candidate, args.root)
                result = {"document_id": record["document_id"], "source_version": record["source_version"],
                          "status": record["status"], "admission": record["admission"]}
            else:
                with open(args.documents_inventory, "r", encoding="utf-8") as handle:
                    paths = json.load(handle, object_pairs_hook=unique_document_pairs, parse_constant=reject_nonfinite)
                result = inventory_financial_documents(paths, args.root)
        except DocumentAdmissionError as error:
            print(json.dumps({"state": "failed", "reason": error.code}, sort_keys=True))
            return 2
        except (OSError, ValueError, TypeError):
            print(json.dumps({"state": "failed", "reason": "document_input_unavailable_or_invalid"}, sort_keys=True))
            return 2
        print(json.dumps(result, sort_keys=True, ensure_ascii=True))
        return 0

    if args.build:
        entries = build_registry()
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w", encoding="ascii", newline="\n") as f:
            for e in entries:
                errs = validate_entry(e)
                if errs:
                    for x in errs:
                        print("BUILD FAIL:", x, file=sys.stderr)
                    return 2
                f.write(json.dumps(e, sort_keys=True, ensure_ascii=True) + "\n")
        print("wrote %d entries -> %s" % (len(entries), args.out))
        return 0

    if args.selftest:
        return selftest(args.out)

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
