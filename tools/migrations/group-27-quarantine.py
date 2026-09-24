"""§4 migration: F8 sentinel; F9 atomicity; F12 write-before-rename; idempotent Run-2."""
import argparse, io, json, shutil, subprocess, sys
from datetime import date
from pathlib import Path
SCRATCH = Path(r"/path/to/local\group-27")
sys.path.insert(0, str(SCRATCH))
from group_27_shared import (
    VAULT_ROOT, yaml_rt, split_frontmatter_body, file_sha256, sentinel_present_in_dst,
)

QDATE = date.today().isoformat()


def transform(src_path, classification):
    """Compute new bytes for src. Returns (new_bytes, modified, error)."""
    try:
        raw = src_path.read_text(encoding="utf-8-sig")
    except Exception as e:
        return None, False, f"read: {e}"
    fm_chunk, body = split_frontmatter_body(src_path)
    if fm_chunk and "quarantined-date:" in fm_chunk:
        return raw.encode("utf-8"), False, None
    if not fm_chunk:
        return (f"---\nquarantined-date: {QDATE}\nquarantined-reason: {classification}\n---\n" + body).encode("utf-8"), True, None
    inner = "\n".join(fm_chunk.splitlines()[1:-1]) + "\n"
    y = yaml_rt()
    try:
        data = y.load(inner)
        if data is None:
            data = {}
    except Exception as e:
        return None, False, f"yaml rt: {e}"
    if not isinstance(data, dict):
        return None, False, "fm not a mapping"
    data["quarantined-date"] = QDATE
    data["quarantined-reason"] = classification
    buf = io.StringIO()
    y.dump(data, buf)
    new_fm = "---\n" + buf.getvalue()
    if not new_fm.endswith("\n"):
        new_fm += "\n"
    new_fm += "---\n"
    return (new_fm + body).encode("utf-8"), True, None


def run(production, workspace_root=None):
    root = VAULT_ROOT if production else Path(workspace_root)
    mapping = json.loads((SCRATCH / "group-27-mapping.json").read_text(encoding="utf-8"))
    transforms, backup, errors, already_migrated = [], {}, [], []
    # Phase 1: compute all transforms in memory (F9)
    for m in mapping["mapping"]:
        src = root / m["src"]
        dst = root / m["dst"]
        if not src.exists():
            # F8 extended: if src absent but dst has sentinel, no-op
            if dst.exists() and sentinel_present_in_dst(dst):
                already_migrated.append({"src": m["src"], "dst": m["dst"]})
                continue
            errors.append(f"missing src: {m['src']} (dst_exists={dst.exists()}, sentinel={sentinel_present_in_dst(dst) if dst.exists() else False})")
            continue
        backup[m["src"]] = file_sha256(src)
        new_bytes, modified, err = transform(src, m["classification"])
        if err:
            errors.append(f"{m['src']}: {err}")
            continue
        transforms.append((m["src"], m["dst"], new_bytes, modified))

    if errors:
        sys.stderr.write("HALT: Phase 1 errors:\n" + "\n".join(f"  {e}" for e in errors) + "\n")
        return 2

    # Phase-2 backup manifest (F9) before any writes
    if transforms:
        manifest = "phase2-backup-manifest-production.json" if production else "phase2-backup-manifest-dryrun.json"
        (SCRATCH / manifest).write_text(json.dumps({
            "baseline_git_head": mapping["baseline_git_head"], "production": production,
            "quarantine_date": QDATE, "files": backup,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Phase 2: writes. F12 CORRECTED pattern (empirically validated 2026-04-20).
    # v12 §2.8 halt-5 diagnosis proposed "write src then git mv"; that does NOT
    # work because git mv moves the index entry (original blob hash) to the new
    # path without re-hashing worktree content. Correct ordering:
    #   (1) git mv src dst  (stages rename of original blob to new path)
    #   (2) dst.write_bytes(new_bytes)  (modifies worktree at dst)
    #   (3) git add dst  (re-hashes dst's worktree content, stages new blob)
    results = []
    for src_rel, dst_rel, new_bytes, modified in transforms:
        src, dst = root / src_rel, root / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if production:
            subprocess.run(["git", "-C", str(root), "mv", src_rel, dst_rel],
                           check=True, capture_output=True, text=True)
        else:
            shutil.move(str(src), str(dst))
        if modified:
            dst.write_bytes(new_bytes)
            if production:
                subprocess.run(["git", "-C", str(root), "add", "--", dst_rel],
                               check=True, capture_output=True, text=True)
        results.append({"src": src_rel, "dst": dst_rel,
                        "post_sha256": file_sha256(dst), "modified": modified})

    name = "group-27-migration-results-production.json" if production else "group-27-migration-results-dryrun.json"
    (SCRATCH / name).write_text(json.dumps({
        "results": results, "already_migrated": already_migrated,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    n_mod = sum(1 for r in results if r["modified"])
    print(f"quarantine mode={'prod' if production else 'dry'} transformed={len(results)} modified={n_mod} already_migrated={len(already_migrated)}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--production", action="store_true")
    ap.add_argument("--workspace", type=str, default=None)
    args = ap.parse_args()
    if not args.production and not args.workspace:
        sys.exit("specify --production or --workspace PATH")
    sys.exit(run(args.production, args.workspace))
