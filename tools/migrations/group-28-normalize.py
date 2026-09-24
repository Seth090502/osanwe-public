#!/usr/bin/env python3
"""Group 28 normalizer v3: records per-edit byte offsets (in src) for validation.

Output per-file report now includes `edit_spans_src` -- list of (start, end) byte
offsets of every occurrence of every before_string in the source file, in order.
The validator uses these to construct a regions-outside-edit byte-equality proof.
"""
import json, sys, os, hashlib
from pathlib import Path

def should_skip_source(source_rel):
    return source_rel.startswith("_quarantine/")

def find_all_spans(content_bytes, before_b):
    """Return list of (start, end) byte offsets where before_b appears in content_bytes."""
    spans = []
    start = 0
    while True:
        i = content_bytes.find(before_b, start)
        if i == -1:
            break
        spans.append((i, i + len(before_b)))
        start = i + len(before_b)  # no overlap assumption
    return spans

def normalize_file(vault_root, source_rel, edits, dst_root=None):
    src = Path(vault_root) / source_rel
    dst = Path(dst_root) / source_rel if dst_root else src
    dst.parent.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        return False, {"source": source_rel, "error": "source missing"}

    src_bytes = src.read_bytes()
    pre_hash = hashlib.sha256(src_bytes).hexdigest()

    # Record all edit spans in src (before any modifications)
    all_spans = []  # list of (start, end, before_string, after_string)
    for e in edits:
        before_b = e["before_string"].encode("utf-8")
        after_s = e["after_string"]
        expected = e.get("occurrence_count")
        spans = find_all_spans(src_bytes, before_b)
        actual = len(spans)
        if expected is not None and actual != expected:
            return False, {
                "source": source_rel,
                "error": "occurrence_count mismatch",
                "before": e["before_string"],
                "expected": expected,
                "actual": actual,
            }
        for s, ep in spans:
            all_spans.append((s, ep, e["before_string"], after_s))

    # Sort spans by start offset. Assert no overlaps (would indicate a bug in
    # mapping composition, since two before_strings shouldn't overlap a single region).
    all_spans.sort()
    for i in range(1, len(all_spans)):
        prev_end = all_spans[i-1][1]
        cur_start = all_spans[i][0]
        if cur_start < prev_end:
            return False, {
                "source": source_rel,
                "error": "overlapping edit spans",
                "prev": all_spans[i-1],
                "cur": all_spans[i],
            }

    # Apply edits in span order by splicing
    out_parts = []
    cursor = 0
    for s, ep, before_s, after_s in all_spans:
        out_parts.append(src_bytes[cursor:s])
        out_parts.append(after_s.encode("utf-8"))
        cursor = ep
    out_parts.append(src_bytes[cursor:])
    dst_bytes = b"".join(out_parts)

    # Idempotency gate: no before_string should remain
    for e in edits:
        before_b = e["before_string"].encode("utf-8")
        if before_b in dst_bytes:
            return False, {
                "source": source_rel,
                "error": "residual_before_string_after_replace",
                "before": e["before_string"],
                "residual": dst_bytes.count(before_b),
            }

    post_hash = hashlib.sha256(dst_bytes).hexdigest()
    dst.write_bytes(dst_bytes)

    return True, {
        "source": source_rel,
        "pre_sha256": pre_hash,
        "post_sha256": post_hash,
        "bytes_pre": len(src_bytes),
        "bytes_post": len(dst_bytes),
        "edit_spans_src": [[s, ep, bs, as_] for s, ep, bs, as_ in all_spans],
        "edits_applied": len(all_spans),
    }

def apply_all(mapping_data, vault_root, dst_root=None, source_filter=None):
    per_source = mapping_data["per_source_edits"]
    reports = []
    all_ok = True
    edit_count = 0
    file_count = 0
    for src_rel, edits in per_source.items():
        if should_skip_source(src_rel):
            continue
        if source_filter and src_rel not in source_filter:
            continue
        edits = [e for e in edits if e["action"] not in ("KEEP_AS_IS", "FLAG_FOR_OWNER")]
        if not edits:
            continue
        ok, report = normalize_file(vault_root, src_rel, edits, dst_root=dst_root)
        if not ok:
            all_ok = False
        reports.append(report)
        if ok:
            edit_count += report["edits_applied"]
            file_count += 1
    return all_ok, reports, edit_count, file_count

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--mapping", required=True)
    ap.add_argument("--vault", default="/path/to/vault")
    ap.add_argument("--dst", default=None)
    ap.add_argument("--sources", default=None)
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    mapping_data = json.loads(Path(args.mapping).read_text(encoding="utf-8"))
    source_filter = set(args.sources.split(",")) if args.sources else None

    ok, reports, edit_count, file_count = apply_all(mapping_data, args.vault, dst_root=args.dst, source_filter=source_filter)
    out = {
        "ok": ok,
        "edits_applied": edit_count,
        "files_touched": file_count,
        "reports": reports,
        "dst_root": args.dst,
    }
    Path(args.report).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("normalizer_ok:", ok)
    print("edits_applied:", edit_count)
    print("files_touched:", file_count)
    sys.exit(0 if ok else 2)
