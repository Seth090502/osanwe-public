#!/usr/bin/env python
"""test_shadow_mutation.py -- tamper-evidence proof suite for the S3 shadow log.

OVERNIGHT-W1 deliverable. Operates on a COPY of the real append-only,
hash-chained shadow logs; the originals are opened READ-ONLY and are never
modified. ASCII only. Stdlib only. No network. No git commands.

Proven properties (each is a selftest case; any failure => nonzero exit):

  T1  reversed parent pointer detected
      (a record's prev_record_hash points at the wrong predecessor)
  T2  single-character prediction edit detected
      (one char of forecast content changed -> record_hash recompute mismatch)
  T3  grade edit detected
      (grade references prediction_hash; editing grade payload makes its
       recorded file digest diverge from the trusted anchor)
  T4  record deletion detected (chain break)
  T5  reordering detected (prev pointers no longer line up)
  T6  duplication detected (same seq/hash appears twice)
  T7  chain-head replacement detectable against a trusted anchor file
      (shadow-audit/chain-head-anchor.json stores genesis..head hashes)

Chain hash convention (identical to tools/fis/shadow.py):
    record_hash = sha256(canonical_json(record minus 'record_hash'))
where canonical_json = json.dumps(sort_keys=True, separators=(",", ":"),
ensure_ascii=True), and prev_record_hash IS included in the hashed payload so
tamper-and-rechain attacks propagate forward to the head.

Usage:
    python tools/fis/test_shadow_mutation.py            # run all cases
    python tools/fis/test_shadow_mutation.py --selftest # exit-code gated

Exit code: 0 iff every case detects its mutation AND the pristine copy
verifies clean.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile

# --------------------------------------------------------------------------
# Paths -- real inputs are read-only; all mutations happen on copies.
# --------------------------------------------------------------------------

VAULT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EFFORTS = os.path.join(VAULT, "Efforts", "osanwe-v2-overhaul")
FIS_DATA = os.path.join(EFFORTS, "_work", "fis-data")
REAL_PREDICTIONS = os.path.join(FIS_DATA, "shadow-predictions.jsonl")
REAL_GRADES = os.path.join(FIS_DATA, "shadow-grades.jsonl")
ANCHOR_PATH = os.path.join(FIS_DATA, "shadow-audit", "chain-head-anchor.json")

REVIEWER = "fis-w1-audit-v1"


# --------------------------------------------------------------------------
# Hash / chain primitives (byte-identical semantics to tools/fis/shadow.py)
# --------------------------------------------------------------------------

def canonical_sha256(obj):
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("ascii")
    return hashlib.sha256(blob).hexdigest()


def record_hash(rec):
    probe = {k: v for k, v in rec.items() if k != "record_hash"}
    return canonical_sha256(probe)


# --------------------------------------------------------------------------
# Verification functions
# --------------------------------------------------------------------------

def load_jsonl(path):
    with open(path, "r", encoding="ascii") as f:
        return [json.loads(line) for line in f.read().splitlines() if line.strip()]


def verify_chain(records):
    """Full chain verification. Returns list of error strings (empty = clean)."""
    errors = []
    expected_prev = "GENESIS"
    seen_hashes = []
    for i, rec in enumerate(records):
        tag = "record %d" % i
        if rec.get("prev_record_hash") != expected_prev:
            errors.append("%s: prev_record_hash mismatch (expected %s..., got %s...)"
                          % (tag, expected_prev[:16], rec.get("prev_record_hash", "")[:16]))
        if record_hash(rec) != rec.get("record_hash"):
            errors.append("%s: record_hash recompute mismatch" % tag)
        if rec.get("record_hash") in seen_hashes:
            errors.append("%s: duplicate record_hash in sequence" % tag)
        seen_hashes.append(rec.get("record_hash"))
        expected_prev = rec.get("record_hash")
    return errors


def verify_anchor(records, grades_path, anchor_path):
    """Verify a predictions log against the trusted chain-head anchor file.

    Checks genesis..head hashes, count, and the raw-bytes sha256 of the grades
    file. Returns list of error strings (empty = clean).
    """
    errors = []
    with open(anchor_path, "r", encoding="ascii") as f:
        anchor = json.load(f)
    got = [r.get("record_hash") for r in records]
    want = anchor["record_hashes"]
    if len(got) != anchor["num_predictions"]:
        errors.append("prediction count %d != anchored %d" % (len(got), anchor["num_predictions"]))
    n = min(len(got), len(want))
    for i in range(n):
        if got[i] != want[i]:
            errors.append("hash at position %d diverges from anchor (%s... != %s...)"
                          % (i, got[i][:16], want[i][:16]))
            break
    if len(got) >= len(want) and got[:len(want)] == want and len(got) > len(want):
        errors.append("log extended beyond anchored head (head replacement / unanchored append)")
    h = hashlib.sha256()
    with open(grades_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    if h.hexdigest() != anchor["grades_file_sha256"]:
        errors.append("grades file sha256 diverges from anchor (grade payload edited)")
    return errors


# --------------------------------------------------------------------------
# Mutation helpers (operate on a temp COPY)
# --------------------------------------------------------------------------

class CopyFixture(object):
    """Copy the real logs into a temp dir once per suite run."""

    def __init__(self):
        self.tmpdir = tempfile.mkdtemp(prefix="shadow-mutation-")
        self.preds = os.path.join(self.tmpdir, "shadow-predictions.jsonl")
        self.grades = os.path.join(self.tmpdir, "shadow-grades.jsonl")
        self.anchor = os.path.join(self.tmpdir, "chain-head-anchor.json")
        shutil.copyfile(REAL_PREDICTIONS, self.preds)
        shutil.copyfile(REAL_GRADES, self.grades)
        shutil.copyfile(ANCHOR_PATH, self.anchor)

    def cleanup(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)


def write_jsonl(path, records):
    with open(path, "w", encoding="ascii") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True, ensure_ascii=True) + "\n")


# --------------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------------

CASES = []


def case(fn):
    CASES.append(fn)
    return fn


@case
def t0_pristine_copy_verifies_clean(fx):
    """Control: an untouched copy must verify with zero errors."""
    errs = verify_chain(load_jsonl(fx.preds))
    assert not errs, errs
    errs = verify_anchor(load_jsonl(fx.preds), fx.grades, fx.anchor)
    assert not errs, errs
    return "pristine copy verifies clean"


@case
def t1_reversed_parent_pointer_detected(fx):
    recs = load_jsonl(fx.preds)
    # Swap record 5's parent pointer from preds[4] back to preds[3].
    recs[5]["prev_record_hash"] = recs[3]["record_hash"]
    write_jsonl(fx.preds, recs)
    errs = verify_chain(load_jsonl(fx.preds))
    assert errs, "reversed parent pointer NOT detected"
    return "reversed parent pointer detected: " + errs[0]


@case
def t2_single_character_prediction_edit_detected(fx):
    recs = load_jsonl(fx.preds)
    # Flip one character inside the p50 forecast of record 9.
    old = repr(recs[9]["forecast_distribution"]["p50"])
    flipped = None
    for c in "0123456789":
        if c != old[0]:
            flipped = float(old.replace(old[0], c, 1))
            break
    recs[9]["forecast_distribution"]["p50"] = flipped
    write_jsonl(fx.preds, recs)
    errs = verify_chain(load_jsonl(fx.preds))
    assert errs, "single-character edit NOT detected"
    return "single-character edit detected: " + errs[0]


@case
def t3_grade_edit_detected(fx):
    grades = load_jsonl(fx.grades)
    # Tamper one digit of the realized return; grade rows carry no chain hash
    # of their own, but their aggregate file digest is pinned in the anchor.
    grades[0]["grades"]["realized_horizon_return"] = -0.999999
    write_jsonl(fx.grades, grades)
    errs = verify_anchor(load_jsonl(fx.preds), fx.grades, fx.anchor)
    assert errs, "grade edit NOT detected"
    assert any("grades file" in e for e in errs), errs
    return "grade edit detected via anchor digest: " + errs[0]


@case
def t4_record_deletion_chain_break(fx):
    recs = load_jsonl(fx.preds)
    del recs[7]
    write_jsonl(fx.preds, recs)
    got = load_jsonl(fx.preds)
    errs = verify_chain(got)
    assert errs, "deletion NOT detected"
    assert any("prev_record_hash mismatch" in e for e in errs), errs
    return "deletion chain break detected: " + errs[0]


@case
def t5_reordering_detected(fx):
    recs = load_jsonl(fx.preds)
    recs[10], recs[11] = recs[11], recs[10]
    write_jsonl(fx.preds, recs)
    errs = verify_chain(load_jsonl(fx.preds))
    assert errs, "reordering NOT detected"
    assert any("prev_record_hash mismatch" in e for e in errs), errs
    return "reordering detected: " + errs[0]


@case
def t6_duplication_detected(fx):
    recs = load_jsonl(fx.preds)
    recs.insert(13, json.loads(json.dumps(recs[13])))  # exact duplicate row
    write_jsonl(fx.preds, recs)
    errs = verify_chain(load_jsonl(fx.preds))
    assert errs, "duplication NOT detected"
    assert any("duplicate record_hash" in e or "prev_record_hash mismatch" in e for e in errs), errs
    return "duplication detected: " + errs[0]


@case
def t7_head_replacement_vs_anchor(fx):
    recs = load_jsonl(fx.preds)
    # Attacker replaces the tail with a re-chained forged record.
    forged = dict(recs[-1])
    forged["forecast_distribution"] = {"p10": -0.01, "p50": 0.99, "p90": 1.99}
    forged["prev_record_hash"] = recs[-2]["record_hash"]
    forged["record_hash"] = record_hash(forged)   # perfectly re-chained forgery
    recs[-1] = forged
    write_jsonl(fx.preds, recs)
    # Internal chain check passes (forgery is self-consistent)...
    internal = verify_chain(load_jsonl(fx.preds))
    assert not internal, "fixture broken: forged tail should be internally consistent, got %s" % internal
    # ...but the trusted anchor catches it. This is exactly why the anchor exists.
    errs = verify_anchor(load_jsonl(fx.preds), fx.grades, fx.anchor)
    assert errs, "head replacement NOT detected vs anchor"
    return "re-chained head forgery caught by anchor: " + errs[0]


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true",
                    help="run the full suite; exit 0 iff every mutation is detected")
    args = ap.parse_args(argv)

    missing = [p for p in (REAL_PREDICTIONS, REAL_GRADES, ANCHOR_PATH) if not os.path.exists(p)]
    if missing:
        print("FATAL: required input(s) missing: %s" % ", ".join(missing))
        return 2

    fx = CopyFixture()
    passed = failed = 0
    try:
        print("suite root: %s" % fx.tmpdir)
        print("originals untouched (read-only); mutations applied to copies\n")
        for fn in CASES:
            # Fresh copies per case so mutations never leak between cases.
            sub = tempfile.mkdtemp(prefix=os.path.basename(fn.__name__) + "-", dir=fx.tmpdir)
            case_fx = CopyFixture.__new__(CopyFixture)
            case_fx.tmpdir = sub
            case_fx.preds = os.path.join(sub, "shadow-predictions.jsonl")
            case_fx.grades = os.path.join(sub, "shadow-grades.jsonl")
            case_fx.anchor = os.path.join(sub, "chain-head-anchor.json")
            shutil.copyfile(REAL_PREDICTIONS, case_fx.preds)
            shutil.copyfile(REAL_GRADES, case_fx.grades)
            shutil.copyfile(ANCHOR_PATH, case_fx.anchor)
            try:
                detail = fn(case_fx)
                print("[PASS] %-38s %s" % (fn.__name__, detail))
                passed += 1
            except AssertionError as e:
                print("[FAIL] %-38s %s" % (fn.__name__, e))
                failed += 1
    finally:
        fx.cleanup()

    print("\n%d/%d cases passed" % (passed, len(CASES)))
    ok = (failed == 0 and passed == len(CASES))
    print("SELFTEST %s" % ("OK" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
