"""Group 26 Tag Normalization — production migration script.

Transforms vault frontmatter tags and skill layer-2 template tags per §2 mapping.
Applies REPLACE-LINE + STRIP-LINE primitives via ruamel.yaml round-trip. Preserves
non-tag frontmatter fields byte-exact (SHA-256 verified). Preserves trailing-newline
count (Group 25 Finding 5 pattern). Idempotent under exact-string match.

Usage:
  python group-26-tag-normalization.py --manifest <path> --transforms <path> [--dry-run-dir <path>]

Exits non-zero on any abort. Emits JSON summary to stdout.
"""
import argparse
import hashlib
import io
import json
import re
import shutil
import sys
from pathlib import Path

if sys.version_info < (3, 10):
    print(
        f"ERROR: Python 3.10+ required (found {sys.version_info.major}.{sys.version_info.minor}).",
        file=sys.stderr,
    )
    sys.exit(2)

try:
    from ruamel.yaml import YAML
except ImportError:
    print("ERROR: ruamel.yaml required. Install with: pip install ruamel.yaml", file=sys.stderr)
    sys.exit(2)

VAULT_ROOT = Path("/path/to/vault")
CENSUS_PATH = Path("/path/to/local/section-3-census.json")


def norm(p):
    """§4.D Windows path-separator preemption."""
    return str(p).replace("\\", "/")


def make_yaml():
    """§4.A — inherited from Group 25 make_yaml() verbatim."""
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096
    y.indent(mapping=2, sequence=4, offset=2)
    return y


def extract_vault_fm(text):
    """Extract vault frontmatter content + fence indices. §3.C extraction logic."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].rstrip("\r\n") == "---":
            return "".join(lines[1:i]), 0, i
    return None


def extract_skill_template(text, sentinel):
    """§4.C.7 — extract skill layer-2 template.

    Idempotency-safe sentinel: match block containing a `tags:` key at line
    start AND `type: <sentinel>` at line start. The `type:` value is stable
    across migration (tags change; type subtype does not), so Run 2 of the
    script still identifies the correct block post-STRIP or post-REPLACE.
    """
    lines = text.splitlines(keepends=True)
    fences = [i for i, ln in enumerate(lines) if ln.rstrip("\r\n") == "---"]
    matches = []
    for k in range(len(fences) - 1):
        a, b = fences[k], fences[k + 1]
        block = "".join(lines[a + 1:b])
        has_tags_key = re.search(r"^tags:", block, re.MULTILINE) is not None
        has_type_sentinel = re.search(
            rf"^type:\s+{re.escape(sentinel)}\s*$", block, re.MULTILINE
        ) is not None
        if has_tags_key and has_type_sentinel:
            matches.append((block, a, b))
    if len(matches) == 0:
        return None, "no_match"
    if len(matches) >= 2:
        return None, "ambiguous_match"
    return matches[0], "unique"


def excise_tags_region(fm):
    """§3.C excision — remove tags: field + its value region."""
    lines = fm.split("\n")
    out = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if re.match(r"^tags:", ln):
            if re.match(r"^tags:\s*\[.*\]\s*$", ln):
                i += 1; continue
            if re.match(r"^tags:\s*$", ln):
                i += 1
                while i < len(lines) and re.match(r"^\s+-\s+", lines[i]):
                    i += 1
                continue
            i += 1; continue
        out.append(ln); i += 1
    return "\n".join(out).encode("utf-8")


def non_tag_sha(fm):
    return hashlib.sha256(excise_tags_region(fm)).hexdigest()


def apply_transforms_to_fm(fm_text, operations):
    """§4.B.1 REPLACE + §4.B.2 STRIP + §4.B.4 compound atomicity.

    Returns (new_fm_text, ops_applied_list, ops_skipped_idempotent_list).
    """
    # §4.C.6 trailing-newline preservation
    trailing = len(fm_text) - len(fm_text.rstrip("\n"))
    stripped = fm_text.rstrip("\n")
    y = make_yaml()
    d = y.load(io.StringIO(stripped + "\n"))
    if d is None or "tags" not in d:
        raise ValueError("missing_tags_key")
    tags = d["tags"]
    if not hasattr(tags, "__iter__") or isinstance(tags, str):
        raise ValueError("non_sequence_tags")

    ops_applied = []
    ops_skipped = []

    for op in operations:
        if op["op"] == "REPLACE":
            src, tgt = op["source"], op["target"]
            # Idempotent check: source absent AND target present
            src_idx = next((i for i, v in enumerate(tags) if v == src), -1)
            if src_idx >= 0:
                tags[src_idx] = tgt
                ops_applied.append({"op": "REPLACE", "source": src, "target": tgt, "at_index": src_idx})
            elif tgt in tags:
                ops_skipped.append({"op": "REPLACE", "source": src, "target": tgt, "reason": "idempotent_already_migrated"})
            else:
                print(f"  WARN: REPLACE source '{src}' not found and target '{tgt}' not present; skipping", file=sys.stderr)
                ops_skipped.append({"op": "REPLACE", "source": src, "target": tgt, "reason": "neither_present"})
        elif op["op"] == "STRIP":
            src = op["source"]
            # §4.E idempotent: source absent → skip
            indices = [i for i, v in enumerate(tags) if v == src]
            if not indices:
                ops_skipped.append({"op": "STRIP", "source": src, "reason": "idempotent_already_stripped"})
                continue
            # Contract: strip first occurrence only (documented behavior for synthetic case 12)
            # Duplicate source tags not expected in scope; single-strip behavior is defined.
            del tags[indices[0]]
            ops_applied.append({"op": "STRIP", "source": src, "at_index": indices[0]})
            # If there are more duplicates (shouldn't happen in scope), warn
            if len(indices) > 1:
                print(f"  WARN: STRIP source '{src}' has {len(indices)} occurrences; stripped first only", file=sys.stderr)
        else:
            raise ValueError(f"unknown_op: {op.get('op')}")

    buf = io.StringIO()
    y.dump(d, buf)
    new_fm = buf.getvalue().rstrip("\n")
    # §4.C.6 restore trailing-newline count
    if trailing > 0:
        new_fm += ("\n" * trailing)

    return new_fm, ops_applied, ops_skipped


def compute_vault_file(src_path, operations):
    """Compute transformed vault file content IN MEMORY. Returns (new_text_or_None,
    result_dict). new_text is None for idempotent-skip."""
    text = src_path.read_text(encoding="utf-8")
    ext = extract_vault_fm(text)
    if ext is None:
        raise ValueError(f"no_frontmatter: {norm(src_path)}")
    fm, start_idx, end_idx = ext
    lines = text.splitlines(keepends=True)
    pre_sha = non_tag_sha(fm)
    new_fm, applied, skipped = apply_transforms_to_fm(fm, operations)
    post_sha = non_tag_sha(new_fm)
    if pre_sha != post_sha:
        raise RuntimeError(f"non_tag_sha changed: {norm(src_path)} pre={pre_sha} post={post_sha}")
    if not applied and skipped:
        return None, {"status": "skipped_idempotent", "applied": [], "skipped": skipped,
                      "pre_sha": pre_sha, "post_sha": post_sha}
    if not new_fm.endswith("\n"):
        new_fm += "\n"
    opener = lines[start_idx]
    closer = lines[end_idx]
    body = "".join(lines[end_idx + 1:])
    new_text = opener + new_fm + closer + body
    return new_text, {"status": "transformed", "applied": applied, "skipped": skipped,
                      "pre_sha": pre_sha, "post_sha": post_sha}


def compute_skill_file(src_path, operations, sentinel):
    """Compute transformed skill SKILL.md content IN MEMORY. Returns (new_text_or_None,
    result_dict)."""
    text = src_path.read_text(encoding="utf-8")
    result, status = extract_skill_template(text, sentinel)
    if status != "unique":
        raise RuntimeError(f"skill template extraction: {norm(src_path)} status={status}")
    fm, a, b = result
    lines = text.splitlines(keepends=True)
    pre_sha = non_tag_sha(fm)
    new_fm, applied, skipped = apply_transforms_to_fm(fm, operations)
    post_sha = non_tag_sha(new_fm)
    if pre_sha != post_sha:
        raise RuntimeError(f"non_tag_sha changed (layer-2): {norm(src_path)} pre={pre_sha} post={post_sha}")
    if not applied and skipped:
        return None, {"status": "skipped_idempotent", "applied": [], "skipped": skipped,
                      "pre_sha": pre_sha, "post_sha": post_sha}
    if not new_fm.endswith("\n"):
        new_fm += "\n"
    prefix = "".join(lines[:a + 1])
    suffix = "".join(lines[b:])
    new_text = prefix + new_fm + suffix
    return new_text, {"status": "transformed", "applied": applied, "skipped": skipped,
                      "pre_sha": pre_sha, "post_sha": post_sha}


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--transforms", required=True)
    ap.add_argument("--dry-run-dir", default=None)
    args = ap.parse_args()

    manifest_lines = Path(args.manifest).read_text(encoding="utf-8").strip().splitlines()
    manifest_entries = []
    for ln in manifest_lines:
        parts = ln.split("|")
        if len(parts) != 2:
            print(f"ERROR: malformed manifest line: {ln}", file=sys.stderr)
            sys.exit(2)
        manifest_entries.append({"path": norm(parts[0]), "file_class": parts[1]})

    transforms = json.loads(Path(args.transforms).read_text(encoding="utf-8"))

    # Pre-flight: manifest vs transforms coverage
    manifest_paths = {e["path"] for e in manifest_entries}
    transforms_paths = set(transforms.keys())
    if manifest_paths != transforms_paths:
        missing_in_transforms = manifest_paths - transforms_paths
        missing_in_manifest = transforms_paths - manifest_paths
        print(f"ERROR: manifest/transforms mismatch", file=sys.stderr)
        if missing_in_transforms:
            print(f"  in manifest, not in transforms: {missing_in_transforms}", file=sys.stderr)
        if missing_in_manifest:
            print(f"  in transforms, not in manifest: {missing_in_manifest}", file=sys.stderr)
        sys.exit(2)

    root = Path(args.dry_run_dir) if args.dry_run_dir else VAULT_ROOT

    # Pre-flight: §3.C baseline verification
    census = json.loads(CENSUS_PATH.read_text(encoding="utf-8"))
    census_by_path = {}
    for r in census:
        raw_path = r["path"]
        # For skill_layer2 records, strip "#L..-L.." suffix for path lookup
        if "#" in raw_path:
            key = raw_path.split("#", 1)[0]
        else:
            key = raw_path
        census_by_path[norm(key)] = r

    pre_flight_errors = []
    for entry in manifest_entries:
        path = root / entry["path"]
        if not path.exists():
            pre_flight_errors.append(f"missing: {entry['path']}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if entry["file_class"] == "vault":
            ext = extract_vault_fm(text)
            if ext is None:
                pre_flight_errors.append(f"no_frontmatter: {entry['path']}")
                continue
            fm = ext[0]
        else:
            sentinel = transforms[entry["path"]]["skill_sentinel"]
            result, status = extract_skill_template(text, sentinel)
            if status != "unique":
                pre_flight_errors.append(f"skill_template_{status}: {entry['path']} sentinel={sentinel}")
                continue
            fm = result[0]
        current_sha = non_tag_sha(fm)
        baseline = census_by_path.get(entry["path"])
        if baseline is None:
            pre_flight_errors.append(f"no_baseline_record: {entry['path']}")
            continue
        if current_sha != baseline["non_tag_fields_sha256"]:
            # In dry-run, may be running on already-transformed file after Run 1;
            # skip the baseline check when --dry-run-dir is set AND sha differs
            # (caller is responsible for Run-1 vs Run-2 semantics via idempotency)
            if args.dry_run_dir is None:
                pre_flight_errors.append(f"non_tag_sha_drift: {entry['path']}")

    if pre_flight_errors:
        print("PRE-FLIGHT FAILED:", file=sys.stderr)
        for e in pre_flight_errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(2)

    # ======================================================================
    # Batch-atomic transform: Phase 1 = compute all 40 in memory. Phase 2 =
    # write all 40 (or none, if any Phase 1 error). No intermediate state on
    # disk if an abort occurs in Phase 1.
    # ======================================================================
    pending_writes = []  # list of (dst_path, new_text, result_dict, rel)
    per_file_results = []
    transformed_count = 0
    skipped_count = 0

    # Phase 1: compute
    for entry in manifest_entries:
        rel = entry["path"]
        spec = transforms[rel]
        src = root / rel
        dst = root / rel
        try:
            if spec["file_class"] == "vault":
                new_text, result = compute_vault_file(src, spec["operations"])
            else:
                new_text, result = compute_skill_file(src, spec["operations"], spec["skill_sentinel"])
        except Exception as e:
            print(f"PHASE-1 ERROR: {rel}: {e}", file=sys.stderr)
            print(f"  No files written. Batch aborted with zero on-disk changes.", file=sys.stderr)
            sys.exit(2)

        if result["status"] == "transformed":
            pending_writes.append((dst, new_text, result, rel, spec["file_class"]))
            transformed_count += 1
        else:
            skipped_count += 1
            per_file_results.append({
                "path": rel,
                "file_class": spec["file_class"],
                "status": result["status"],
                "operations_applied": result["applied"],
                "operations_skipped": result["skipped"],
                "non_tag_sha256_pre": result["pre_sha"],
                "non_tag_sha256_post": result["post_sha"],
                "file_sha256_post": None,  # no write, no post-sha
            })

    # Phase 2: write all pending. If any write fails, abort — at this point
    # some files may already be written (file system I/O is not fully atomic
    # across N independent files), but Phase 1's validation + SHA checks
    # ensure the content is valid before Phase 2 begins.
    written = []
    write_error = None
    for dst, new_text, result, rel, file_class in pending_writes:
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            tmp = dst.with_suffix(dst.suffix + ".group-26-tmp")
            tmp.write_text(new_text, encoding="utf-8", newline="")
            tmp.replace(dst)
            written.append(dst)
            post_sha256 = sha256_file(dst)
            per_file_results.append({
                "path": rel,
                "file_class": file_class,
                "status": result["status"],
                "operations_applied": result["applied"],
                "operations_skipped": result["skipped"],
                "non_tag_sha256_pre": result["pre_sha"],
                "non_tag_sha256_post": result["post_sha"],
                "file_sha256_post": post_sha256,
            })
        except Exception as e:
            write_error = (rel, e)
            break

    if write_error:
        rel, e = write_error
        print(f"PHASE-2 WRITE ERROR: {rel}: {e}", file=sys.stderr)
        print(f"  {len(written)} files written before abort.", file=sys.stderr)
        print(f"  Manual rollback via `git checkout -- <paths>` required.", file=sys.stderr)
        sys.exit(2)

    summary = {
        "files_processed": len(manifest_entries),
        "files_transformed": transformed_count,
        "files_skipped_idempotent": skipped_count,
        "files_aborted": 0,
        "atomicity_model": "in-memory-compute-then-write",
        "per_file": per_file_results,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
