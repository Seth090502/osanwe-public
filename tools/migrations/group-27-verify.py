"""Body/fm equivalence vs §3 census."""
import argparse, json, sys
from pathlib import Path
SCRATCH = Path(r"/path/to/local\group-27")
sys.path.insert(0, str(SCRATCH))
from group_27_shared import (
    VAULT_ROOT, parse_frontmatter, split_frontmatter_body, bytes_sha256, fm_sha_excluding,
)


def verify(root):
    census = json.loads((SCRATCH / "group-27-census.json").read_text(encoding="utf-8"))["census"]
    results = []
    for row in census:
        dst, src = root / row["dst"], root / row["src"]
        dst_ok, src_absent = dst.exists(), not src.exists()
        post_body_sha = post_fm_sha = None
        if dst_ok:
            fm, _ = parse_frontmatter(dst)
            _, body = split_frontmatter_body(dst)
            post_body_sha = bytes_sha256(body.encode("utf-8"))
            post_fm_sha = (fm_sha_excluding(fm, ["quarantined-date", "quarantined-reason"])
                           if isinstance(fm, dict) else "NA")
        body_match = (post_body_sha == row["baseline_body_sha256"])
        fm_match = (post_fm_sha == row["baseline_fm_sha_excl_quarantine"]
                    or row["baseline_fm_sha_excl_quarantine"].startswith("PARSE_ERROR"))
        results.append({"src": row["src"], "dst": row["dst"], "src_absent": src_absent,
                        "dst_present": dst_ok, "body_sha_match": body_match, "fm_excl_match": fm_match,
                        "post_body_sha256": post_body_sha, "post_fm_sha_excl": post_fm_sha})
    all_pass = all(r["src_absent"] and r["dst_present"] and r["body_sha_match"] and r["fm_excl_match"] for r in results)
    (SCRATCH / "group-27-verify-results.json").write_text(
        json.dumps({"results": results, "all_pass": all_pass}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    fails = [r for r in results if not (r["src_absent"] and r["dst_present"] and r["body_sha_match"] and r["fm_excl_match"])]
    print(f"verify: total={len(results)} pass={len(results) - len(fails)} fail={len(fails)} all_pass={all_pass}")
    for f in fails[:10]:
        print(f"  FAIL {f['src']} -> {f['dst']}")
    return 0 if not fails else 2


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=str, default=str(VAULT_ROOT))
    args = ap.parse_args()
    sys.exit(verify(Path(args.root)))
