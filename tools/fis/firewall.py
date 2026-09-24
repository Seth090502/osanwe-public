#!/usr/bin/env python3
"""FW1 legacy evaluator: SYNTHETIC SANDBOX ONLY as of 2026-09-12.

Public and filesystem methods refuse until configure_synthetic_sandbox binds a
fresh empty OS-temp directory. Existing persisted challenges cannot be reopened.
The canonical evaluation/request_access.py gateway remains backend-unavailable.
This fixture implementation is NOT an independent evaluator or security boundary.
The following historical design claims describe the superseded candidate:

DESIGN TIER (honest classification): **TIER B-MINUS CANDIDATE** --
"OPERATIONALLY BLINDED WITH DISCLOSED RESIDUAL".

This is NOT Tier C. On a shared single-box there is no true isolation:
anyone who can read files as the operator user -- or as admin -- can read
the evaluator key file and decrypt the challenge set. See
_work/fis-data/firewall-threat-model.md for the exact list of residuals.
Mechanism-level fixes (S9) make this a Tier B-minus CANDIDATE; the box
itself stays Tier C procedural until a separate evaluator credential
exists (see the threat model doc).

What this module enforces *operationally*:
  1. Challenge dataset at rest is an ENCRYPTED SQLite blob (std-lib only:
     hashlib PBKDF2 key derivation + os.urandom salt/nonce; SHA-256
     counter-mode keystream XOR; HMAC-SHA256 encrypt-then-MAC).
     The key lives in an evaluator-only key file; NTFS ACL hardening is
     applied best-effort but admin/user-level readers remain a DISCLOSED
     RESIDUAL, stated plainly.
  2. evaluate_submission() returns ONLY a preregistered metrics dict --
     never raw labels, never per-row equity beyond what preregistration
     specifies.
  3. Evaluation request budget persisted in _work/fis-data/eval-budget.json
     as an HMAC'd ledger (evaluator-key MAC + monotonic counter, S9-1):
     direct writes to eval-budget.json fail verification and are rejected
     and logged as TAMPER. Default 10 submissions per candidate family;
     exhaustion requires an evaluator override carrying a written reason
     (logged). NOTE: on this shared box the same user that can read the
     key can re-seal a forged ledger -- that residual stands; see the
     threat model doc.
  4. Access-event log _work/fis-data/eval-access-log.jsonl records every
     decrypt/open/evaluate attempt (who/when/what/success) as a SHA-256
     hash-chained append-only sequence.
  5. Tamper detection: the challenge DB carries a keyed digest (HMAC over
     the full encrypted blob) verified before EVERY evaluation; mismatch
     aborts and logs TAMPER. The budget ledger carries its own keyed MAC +
     monotonic counter; mismatch aborts and logs TAMPER (S9-1).
  6. Leakage CANARIES: synthetic instruments whose only appearance is the
     holdout window. A submission showing implausible foresight on them
     is flagged CONTAMINATION-SUSPECT in its metrics.
  7. Small-N scoring cutoff (S9-3): hit_rate / rank_ic / canary_accuracy
     are SUPPRESSED below MIN_N_SCORED scored predictions -- only n_scored
     is returned -- because a handful of directional outcomes leaks about
     one bit per query to a probing submitter.
  8. Selftest hygiene (S9-2): selftests run entirely inside a
     tempfile.TemporaryDirectory with guaranteed cleanup; a residue sweep
     asserts nothing matching fw1-selftest-* survives in the OS temp dir.
  9. Key rotation (S9-5): rotate_key() OVERWRITES every keyfile byte
     before unlinking, then logs KEY_ROTATION. (On flash-backed storage
     overwrite-before-delete is best-effort; disclosed residual.)
 10. Error hygiene (S9-4): FirewallError messages are scrubbed through
     _scrub() so no absolute paths, DATA_DIR internals, key-file names,
     or family labels ever appear in exceptions shown to untrusted sides.

Constraints honoured: ASCII only, std-lib only, no network, no git.
"""

from __future__ import annotations

import getpass
import hashlib
import hmac
import json
import math
import os
import sqlite3
import stat
import struct
import tempfile
import time
import threading
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(_REPO_ROOT, "_work", "fis-data")

KEY_FILE = os.path.join(DATA_DIR, ".evaluator-key")
CHALLENGE_ENC = os.path.join(DATA_DIR, "challenge.enc")
MANIFEST_FILE = os.path.join(DATA_DIR, "challenge-manifest.json")
BUDGET_FILE = os.path.join(DATA_DIR, "eval-budget.json")
ACCESS_LOG = os.path.join(DATA_DIR, "eval-access-log.jsonl")
THREAT_MODEL_DOC = os.path.join(DATA_DIR, "firewall-threat-model.md")

DEFAULT_BUDGET_PER_FAMILY = 10
PBKDF2_ITERATIONS = 200_000
LEDGER_SCHEMA_V2 = "fw1-budget-v2"
MIN_N_SCORED = 20          # S9-3: suppress rate metrics below this n_scored
_SELFTEST_PREFIX = "fw1-selftest-"
_SANDBOX_ROOT = None
_REGISTERED_FAMILIES = frozenset()
_BUDGET_HIGH_WATER = 0
_BUDGET_INITIALIZED = False
_OPERATION_MUTEX = threading.RLock()
_OPERATION_LOCAL = threading.local()


class FirewallError(Exception):
    """Base error for the FW1 firewall."""


def configure_synthetic_sandbox(root, registered_families):
    if getattr(_OPERATION_LOCAL, "depth", 0) or not _OPERATION_MUTEX.acquire(blocking=False):
        raise FirewallError("cannot reconfigure an active synthetic evaluator")
    try:
        return _configure_synthetic_sandbox(root, registered_families)
    finally:
        _OPERATION_MUTEX.release()


def _configure_synthetic_sandbox(root, registered_families):
    """Bind this process to a fresh temporary synthetic fixture directory.

    Never reopens persisted evaluators. This is test containment, not a security
    boundary against the operator or a connection to the canonical holdout.
    """
    global DATA_DIR, KEY_FILE, CHALLENGE_ENC, MANIFEST_FILE, BUDGET_FILE
    global ACCESS_LOG, THREAT_MODEL_DOC, _SANDBOX_ROOT, _REGISTERED_FAMILIES
    global _BUDGET_HIGH_WATER, _BUDGET_INITIALIZED
    target = Path(root)
    if target.is_symlink():
        raise FirewallError("sandbox root cannot be a link")
    target = target.resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    if target == temp_root or temp_root not in target.parents:
        raise FirewallError("synthetic sandbox must be a fresh OS temporary subdirectory")
    if not isinstance(registered_families, (list, tuple, set, frozenset)) or not registered_families:
        raise FirewallError("explicit synthetic family registration required")
    families = list(registered_families)
    if any(not isinstance(f, str) or not f.strip() or f != f.strip() for f in families) or len(set(families)) != len(families):
        raise FirewallError("unique nonblank synthetic family IDs required")
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise FirewallError("synthetic sandbox must be empty; persisted data cannot be reopened")
    target.mkdir(parents=False, exist_ok=True)
    DATA_DIR = str(target)
    KEY_FILE = str(target / ".evaluator-key")
    CHALLENGE_ENC = str(target / "challenge.enc")
    MANIFEST_FILE = str(target / "challenge-manifest.json")
    BUDGET_FILE = str(target / "eval-budget.json")
    ACCESS_LOG = str(target / "eval-access-log.jsonl")
    THREAT_MODEL_DOC = str(target / "firewall-threat-model.md")
    _SANDBOX_ROOT = str(target)
    _REGISTERED_FAMILIES = frozenset(families)
    _BUDGET_HIGH_WATER, _BUDGET_INITIALIZED = 0, False
    (target / "SYNTHETIC_ONLY.json").write_text(json.dumps({
        "scope": "SYNTHETIC_TEST_ONLY_NO_HOLDOUT_ACCESS",
        "families": sorted(families)}), encoding="ascii")


def _sandbox_path(path):
    if _SANDBOX_ROOT is None:
        raise FirewallError("legacy evaluator unavailable; explicit synthetic sandbox required")
    candidate = Path(path)
    root = Path(_SANDBOX_ROOT)
    if candidate.is_symlink() or root not in candidate.resolve().parents:
        raise FirewallError("path is outside the configured synthetic sandbox")
    return candidate


def _require_sandbox():
    if _SANDBOX_ROOT is None or Path(DATA_DIR).resolve() != Path(_SANDBOX_ROOT):
        raise FirewallError("legacy evaluator unavailable; explicit synthetic sandbox required")
    for path in [KEY_FILE, CHALLENGE_ENC, MANIFEST_FILE, BUDGET_FILE, ACCESS_LOG, THREAT_MODEL_DOC]:
        _sandbox_path(path)


@contextmanager
def _serialized_operation():
    _require_sandbox()
    if not _OPERATION_MUTEX.acquire(blocking=False):
        raise FirewallError("synthetic evaluator busy; no evaluation attempted")
    outer = getattr(_OPERATION_LOCAL, "depth", 0) == 0
    acquired = False
    lock_path = str(Path(_SANDBOX_ROOT) / ".gateway.lock")
    try:
        if outer:
            try:
                fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.close(fd)
                acquired = True
            except FileExistsError:
                raise FirewallError("synthetic evaluator busy; no evaluation attempted") from None
        _OPERATION_LOCAL.depth = getattr(_OPERATION_LOCAL, "depth", 0) + 1
        try:
            yield
        finally:
            _OPERATION_LOCAL.depth -= 1
    finally:
        try:
            if acquired:
                os.unlink(lock_path)
        finally:
            _OPERATION_MUTEX.release()


def _sandbox_operation(fn):
    @wraps(fn)
    def guarded(*args, **kwargs):
        with _serialized_operation():
            try:
                return fn(*args, **kwargs)
            except (FirewallError, ValueError, OSError):
                if fn.__name__ == "evaluate_submission":
                    # Never log submission rows, scores, labels or caller text.
                    log_event("evaluate_refused", {"scope": "synthetic_only"}, False)
                raise
    return guarded


def _require_family(family):
    if not isinstance(family, str) or family not in _REGISTERED_FAMILIES:
        raise FirewallError("unregistered synthetic candidate family")


class TamperDetected(FirewallError):
    """Keyed digest did not verify (challenge blob or budget ledger)."""


class BudgetExhausted(FirewallError):
    """Candidate family has consumed its evaluation budget."""

    def __init__(self, used: int, limit: int):
        # S9-4: family label intentionally NOT included in message.
        super().__init__(
            "budget exhausted (%d/%d used); "
            "no public override; register a fresh synthetic experiment"
            % (used, limit)
        )
        self.used = used
        self.limit = limit


def _scrub(message: str) -> str:
    """S9-4: scrub error text of internal labels/paths before raising.

    Removes absolute filesystem paths, the data directory, key/blob/log
    filenames, and any 'family=...' style internals from messages."""
    out = str(message)
    for path in (DATA_DIR, KEY_FILE, CHALLENGE_ENC, MANIFEST_FILE,
                 BUDGET_FILE, ACCESS_LOG, THREAT_MODEL_DOC, _REPO_ROOT):
        if path and path in out:
            out = out.replace(path, "<internal>")
    out = out.replace(os.path.basename(KEY_FILE), "<keyfile>")
    while "<repo-root>\\" in out or "<repo-root>/" in out:
        pass  # defensive no-op; replacements above already collapsed paths
    # generic absolute-path scrubber: drive-letter or posix-looking paths
    import re as _re
    out = _re.sub(r"(?:[A-Za-z]:)?[\\/](?:[\w.\-]+[\\/])+[\w.\-]+", "<path>", out)
    return out


class _ScrubbedError(FirewallError):
    """FirewallError whose rendered message is scrubbed at raise-time."""

    def __init__(self, message: str):
        super().__init__(_scrub(message))


# --------------------------------------------------------------------------
# Logging: hash-chained append-only JSONL
# --------------------------------------------------------------------------

def _canonical(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


@_sandbox_operation
def log_event(action: str, detail: Dict[str, Any], success: bool,
              actor: Optional[str] = None) -> Dict[str, Any]:
    """Append one access event to the hash-chained access log."""
    os.makedirs(DATA_DIR, exist_ok=True)
    prev_hash = ""
    seq = 0
    if os.path.exists(ACCESS_LOG):
        with open(ACCESS_LOG, "rb") as fh:
            last = b""
            for line in fh:            # find last non-empty line
                if line.strip():
                    last = line
            if last:
                rec = json.loads(last.decode("ascii"))
                seq = int(rec["seq"])
                prev_hash = rec["hash"]
    event = {
        "seq": seq + 1,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "actor": actor or getpass.getuser(),
        "action": action,
        "success": bool(success),
        "detail": detail,
        "prev_hash": prev_hash,
    }
    event["hash"] = hashlib.sha256(_canonical(event).encode("ascii")).hexdigest()
    with open(ACCESS_LOG, "a", encoding="ascii") as fh:
        fh.write(_canonical(event) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    return event


@_sandbox_operation
def verify_log_integrity() -> Tuple[bool, str]:
    """Verify the hash chain of the access log. Returns (ok, message)."""
    if not os.path.exists(ACCESS_LOG):
        return True, "empty log"
    prev = ""
    n = 0
    with open(ACCESS_LOG, "r", encoding="ascii") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            n += 1
            rec = json.loads(line)
            claimed = rec.pop("hash")
            if rec["prev_hash"] != prev:
                return False, "chain break at seq %d" % rec["seq"]
            if hashlib.sha256(_canonical(rec).encode("ascii")).hexdigest() != claimed:
                return False, "digest mismatch at seq %d" % rec["seq"]
            prev = claimed
    return True, "ok (%d events)" % n


# --------------------------------------------------------------------------
# Key management
# --------------------------------------------------------------------------

def _derive_key(salt: bytes) -> bytes:
    """Derive the 32-byte data key from the secret in KEY_FILE via PBKDF2."""
    secret = _load_secret()
    return hashlib.pbkdf2_hmac("sha256", secret, salt, PBKDF2_ITERATIONS)


@_sandbox_operation
def _load_secret() -> bytes:
    if not os.path.exists(KEY_FILE):
        raise _ScrubbedError(
            "evaluator key material unavailable; call init_keyfile() "
            "as evaluator")
    with open(KEY_FILE, "rb") as fh:
        secret = fh.read().strip()
    if len(secret) < 32:
        raise _ScrubbedError("evaluator key material unusable")
    return secret


@_sandbox_operation
def _harden_keyfile(path: str) -> None:
    """Private permissions for a synthetic fixture key; no isolation claim."""
    _sandbox_path(path)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


@_sandbox_operation
def init_keyfile(force: bool = False) -> None:
    """Create the evaluator-only key file (32 random bytes, hex-encoded)."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(KEY_FILE) and not force:
        return
    secret = os.urandom(32).hex().encode("ascii")
    tmp = KEY_FILE + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(secret)
    os.replace(tmp, KEY_FILE)
    _harden_keyfile(KEY_FILE)
    log_event("keyfile_init", {}, success=True)


@_sandbox_operation
def _overwrite_bytes(path: str) -> None:
    """Overwrite a file's contents in place, byte-for-byte, three passes."""
    _sandbox_path(path)
    try:
        size = os.path.getsize(path)
    except OSError:
        return
    if size == 0:
        return
    try:
        with open(path, "r+b") as fh:
            for _ in range(3):
                fh.seek(0)
                remaining = size
                while remaining > 0:
                    chunk = os.urandom(min(65536, remaining))
                    fh.write(chunk)
                    remaining -= len(chunk)
                fh.flush()
                os.fsync(fh.fileno())
                fh.seek(0)
    except OSError:
        pass  # best-effort; disclosed residual on flash/CoW filesystems


@_sandbox_operation
def rotate_key() -> bool:
    """S9-5: destroy the current evaluator key file safely.

    Overwrites EVERY byte of the keyfile (3 passes of random data,
    flushed + fsync'd) BEFORE unlinking, then logs KEY_ROTATION.
    Returns True if a key was rotated, False if none existed."""
    if not os.path.exists(KEY_FILE):
        log_event("KEY_ROTATION", {"rotated": False}, True)
        return False
    _overwrite_bytes(KEY_FILE)
    try:
        os.unlink(KEY_FILE)
    except OSError:
        # could not remove; leave overwritten (zeroed-with-random) file
        log_event("KEY_ROTATION", {"rotated": False, "unlinked": False},
                  False)
        return False
    log_event("KEY_ROTATION", {"rotated": True}, True)
    return True


# --------------------------------------------------------------------------
# Encryption primitives (std-lib only): SHA-256 CTR keystream + HMAC
# --------------------------------------------------------------------------

def _keystream_xor(key: bytes, nonce: bytes, data: bytes) -> bytes:
    out = bytearray(len(data))
    block = 0
    pos = 0
    while pos < len(data):
        ctr = struct.pack(">Q", block)
        ks = hashlib.sha256(key + nonce + ctr).digest()
        chunk = data[pos:pos + 32]
        for i, b in enumerate(chunk):
            out[pos + i] = b ^ ks[i]
        pos += 32
        block += 1
    return bytes(out)


def _mac(key: bytes, nonce: bytes, ciphertext: bytes) -> str:
    return hmac.new(key, nonce + ciphertext, hashlib.sha256).hexdigest()


def _seal(key: bytes, plaintext: bytes) -> Tuple[bytes, bytes]:
    nonce = os.urandom(16)
    ct = _keystream_xor(key, nonce, plaintext)
    return nonce, ct


# --------------------------------------------------------------------------
# Challenge DB build / open
# --------------------------------------------------------------------------

@_sandbox_operation
def build_challenge_db(rows: Sequence[Tuple[str, str, float]],
                       canaries: Sequence[str]) -> None:
    """Build + seal the challenge database.

    rows: (instrument, date_iso, realized_return) tuples. Canary instruments
    MUST have their only appearances inside the holdout window -- the caller
    asserts this by passing the explicit canary instrument names.
    """
    init_keyfile()
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE labels (instrument TEXT, date TEXT, ret REAL)")
    con.execute("CREATE TABLE meta (k TEXT PRIMARY KEY, v TEXT)")
    con.executemany("INSERT INTO labels VALUES (?,?,?)",
                    [(i, d, float(r)) for i, d, r in rows])
    con.executemany("INSERT INTO meta VALUES (?,?)", [
        ("schema", "fw1-challenge-v1"),
        ("canaries", ",".join(sorted(set(canaries)))),
        ("n_rows", str(len(rows))),
    ])
    con.commit()
    plaintext = con.serialize()
    con.close()

    salt = os.urandom(16)
    key = _derive_key(salt)
    nonce, ct = _seal(key, plaintext)

    with open(CHALLENGE_ENC + ".tmp", "wb") as fh:
        fh.write(ct)
    os.replace(CHALLENGE_ENC + ".tmp", CHALLENGE_ENC)

    manifest = {
        "schema": "fw1-manifest-v1",
        "pbkdf2_iterations": PBKDF2_ITERATIONS,
        "salt_hex": salt.hex(),
        "nonce_hex": nonce.hex(),
        "keyed_digest": _mac(key, nonce, ct),
        "plaintext_sha256": hashlib.sha256(plaintext).hexdigest(),
        "n_canaries": len(set(canaries)),
    }
    with open(MANIFEST_FILE + ".tmp", "w", encoding="ascii") as fh:
        json.dump(manifest, fh, indent=1)
    os.replace(MANIFEST_FILE + ".tmp", MANIFEST_FILE)
    log_event("challenge_build", {"n_rows": len(rows),
                                  "n_canaries": len(set(canaries))},
              success=True)


@_sandbox_operation
def _open_challenge(actor_note: str = "") -> sqlite3.Connection:
    """Verify keyed digest, decrypt IN MEMORY, return live sqlite connection.

    The plaintext never touches disk (sqlite3 deserialize). Any tamper
    aborts before decryption and is logged as TAMPER."""
    ev_detail: Dict[str, Any] = {"note": actor_note}
    try:
        if not (os.path.exists(CHALLENGE_ENC) and os.path.exists(MANIFEST_FILE)):
            log_event("decrypt_open", ev_detail, False)
            raise _ScrubbedError("challenge blob or manifest missing")
        with open(MANIFEST_FILE, "r", encoding="ascii") as fh:
            manifest = json.load(fh)
        with open(CHALLENGE_ENC, "rb") as fh:
            ct = fh.read()
        salt = bytes.fromhex(manifest["salt_hex"])
        nonce = bytes.fromhex(manifest["nonce_hex"])
        key = _derive_key(salt)
        digest = _mac(key, nonce, ct)
        if not hmac.compare_digest(digest, manifest["keyed_digest"]):
            log_event("TAMPER", dict(ev_detail,
                      expected_prefix=digest[:12],
                      got_prefix=manifest["keyed_digest"][:12]), False)
            raise TamperDetected(
                "keyed digest mismatch on challenge blob -- TAMPER logged")
        pt = _keystream_xor(key, nonce, ct)
        if hashlib.sha256(pt).hexdigest() != manifest["plaintext_sha256"]:
            log_event("TAMPER", dict(ev_detail, stage="post-decrypt"), False)
            raise TamperDetected("plaintext digest mismatch -- TAMPER logged")
        con = sqlite3.connect(":memory:")
        con.deserialize(pt)
        log_event("decrypt_open", ev_detail, True)
        return con
    except TamperDetected:
        raise
    except Exception as exc:  # noqa: BLE001 - log and re-raise scrubbed
        if isinstance(exc, FirewallError):
            raise
        log_event("decrypt_open", dict(ev_detail,
                  error=_scrub(str(exc))[:120]), False)
        raise _ScrubbedError(str(exc))


# --------------------------------------------------------------------------
# Budget ledger: HMAC'd with evaluator key + monotonic counter (S9-1)
# --------------------------------------------------------------------------

def _ledger_mac(counter: int, payload: Dict[str, Any]) -> str:
    mac_key = hashlib.sha256(b"FW1-BUDGET-LEDGER-V2:" + _load_secret()).digest()
    body = _canonical({"counter": counter, "payload": payload})
    return hmac.new(mac_key, body.encode("ascii"), hashlib.sha256).hexdigest()


@_sandbox_operation
def _read_budget() -> Dict[str, Any]:
    """Read + verify the budget ledger.

    Ledger format v2:
      {"schema": "fw1-budget-v2", "counter": N, "payload": {...},
       "mac": <hmac over canonical {counter,payload}>}

    The MAC is keyed by the evaluator secret; the monotonic counter must
    never go backwards vs. our cached high-water mark (kept inside the
    payload itself AND checked against the access log's last recorded
    counter via the ledger's own history entry). A missing MAC, a MAC
    mismatch, or a rolled-back counter is rejected as TAMPER and logged.
    """
    if not os.path.exists(BUDGET_FILE):
        if _BUDGET_INITIALIZED:
            raise TamperDetected("budget state disappeared after initialization")
        return {"default_limit": DEFAULT_BUDGET_PER_FAMILY,
                "families": {}, "last_counter": 0}
    try:
        with open(BUDGET_FILE, "r", encoding="ascii") as fh:
            raw = json.load(fh)
    except (OSError, ValueError):
        log_event("TAMPER", {"target": "budget_ledger",
                             "reason": "unreadable"}, False)
        raise TamperDetected("budget ledger unreadable -- TAMPER logged")
    if not isinstance(raw, dict) \
            or raw.get("schema") != LEDGER_SCHEMA_V2 \
            or "counter" not in raw or "payload" not in raw \
            or "mac" not in raw:
        log_event("TAMPER", {"target": "budget_ledger",
                             "reason": "legacy_or_missing_mac"}, False)
        raise TamperDetected(
            "budget ledger failed integrity check -- TAMPER logged")
    counter = raw["counter"]
    payload = raw["payload"]
    if not isinstance(counter, int) or counter < 0 or not isinstance(payload, dict):
        log_event("TAMPER", {"target": "budget_ledger",
                             "reason": "malformed"}, False)
        raise TamperDetected("budget ledger malformed -- TAMPER logged")
    expect = _ledger_mac(counter, payload)
    if not hmac.compare_digest(expect, raw["mac"]):
        log_event("TAMPER", {"target": "budget_ledger",
                             "reason": "mac_mismatch"}, False)
        raise TamperDetected(
            "budget ledger failed integrity check -- TAMPER logged")
    # Monotonicity: payload records the counter it was sealed under; also
    # refuse counters below the highest previously seen value which we
    # persist in the payload itself (high_water).
    hw = max(int(payload.get("_high_water", counter)), _BUDGET_HIGH_WATER)
    ok, _ = verify_log_integrity()
    if not ok or not os.path.exists(ACCESS_LOG):
        raise TamperDetected("budget audit evidence is missing or corrupt")
    with open(ACCESS_LOG, encoding="ascii") as history:
        logged = max((json.loads(line).get("detail", {}).get("counter", 0)
                      for line in history if line.strip()), default=0)
    if counter != logged or counter < hw:
        log_event("TAMPER", {"target": "budget_ledger",
                             "reason": "counter_regression"}, False)
        raise TamperDetected(
            "budget ledger counter regression -- TAMPER logged")
    return payload


@_sandbox_operation
def _write_budget(payload: Dict[str, Any]) -> None:
    """Seal + write the budget ledger with a fresh monotonic counter."""
    global _BUDGET_HIGH_WATER, _BUDGET_INITIALIZED
    prev_hw = _BUDGET_HIGH_WATER
    if os.path.exists(BUDGET_FILE):
        try:
            with open(BUDGET_FILE, "r", encoding="ascii") as fh:
                old = json.load(fh)
            if isinstance(old, dict) and isinstance(old.get("payload"), dict):
                prev_hw = max(prev_hw, int(old["payload"].get("_high_water", 0)))
                prev_counter = old.get("counter")
                if isinstance(prev_counter, int):
                    prev_hw = max(prev_hw, prev_counter)
        except (OSError, ValueError):
            pass
    counter = prev_hw + 1
    payload = dict(payload)
    payload["_high_water"] = counter
    mac = _ledger_mac(counter, payload)
    envelope = {
        "schema": LEDGER_SCHEMA_V2,
        "counter": counter,
        "payload": payload,
        "mac": mac,
    }
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = BUDGET_FILE + ".tmp"
    with open(tmp, "w", encoding="ascii") as fh:
        json.dump(envelope, fh, indent=1)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, BUDGET_FILE)
    _BUDGET_HIGH_WATER, _BUDGET_INITIALIZED = counter, True
    log_event("budget_commit", {"counter": counter}, True)


@_sandbox_operation
def budget_status(family: str) -> Dict[str, int]:
    _require_family(family)
    b = _read_budget()   # raises TamperDetected on forged/direct-written ledger
    limit = int(b.get("default_limit", DEFAULT_BUDGET_PER_FAMILY))
    fam = b.get("families", {}).get(family, {})
    return {"used": int(fam.get("used", 0)),
            "limit": int(fam.get("limit", limit))}


@_sandbox_operation
def evaluator_override(family: str, reason: str) -> None:
    """No public budget override exists, including in a synthetic sandbox."""
    _require_family(family)
    raise FirewallError("budget overrides are unavailable; register a fresh synthetic experiment")


# --------------------------------------------------------------------------
# Submission handling + metrics
# --------------------------------------------------------------------------

_PREREGISTERED_METRIC_KEYS = (
    "n_scored", "rank_ic", "hit_rate", "canary_n", "canary_accuracy",
    "contamination_suspect", "flags",
)


@_sandbox_operation
def parse_submission(submission_file: str) -> List[Dict[str, Any]]:
    """Parse a submission CSV: columns instrument,date,score. ASCII CSV only."""
    import csv
    _sandbox_path(submission_file)
    if not os.path.exists(submission_file):
        raise _ScrubbedError("submission file not found")
    out: List[Dict[str, Any]] = []
    seen = set()
    with open(submission_file, "r", encoding="ascii", newline="") as fh:
        rdr = csv.DictReader(fh)
        need = {"instrument", "date", "score"}
        if rdr.fieldnames is None or not need.issubset(
                {c.strip().lower() for c in rdr.fieldnames}):
            raise _ScrubbedError(
                "submission must be CSV with columns instrument,date,score")
        for row in rdr:
            low = {(k or "").strip().lower(): v for k, v in row.items()}
            try:
                score = float(low["score"])
            except (TypeError, ValueError):
                raise _ScrubbedError("submission score must be finite numeric") from None
            out.append({
                "instrument": (low["instrument"] or "").strip(),
                "date": (low["date"] or "").strip(),
                "score": score,
            })
    for row in out:
        key = (row["instrument"], row["date"])
        if not all(key) or key in seen or not math.isfinite(row["score"]):
            raise _ScrubbedError("submission requires unique nonblank row keys and finite scores")
        seen.add(key)
    if not out:
        raise _ScrubbedError("submission has no rows")
    return out


def _rank(vals: List[float]) -> List[float]:
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(xs: List[float], ys: List[float]) -> float:
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    if sxx <= 0 or syy <= 0:
        return 0.0
    return sxy / ((sxx ** 0.5) * (syy ** 0.5))


@_sandbox_operation
def evaluate_submission(submission_file: str, family: str,
                        allow_over_budget: bool = False
                        ) -> Dict[str, Any]:
    """Evaluate a submission against the sealed challenge set.

    Returns ONLY the preregistered metrics dict (keys in
    _PREREGISTERED_METRIC_KEYS). Never labels, never per-row equity curves.
    Rate metrics (rank_ic / hit_rate / canary_accuracy) are suppressed when
    n_scored < MIN_N_SCORED (S9-3 small-N leakage cutoff). Consumes one unit
    of the registered synthetic family budget. Over-budget access is refused."""
    _require_family(family)
    if allow_over_budget is not False:
        raise FirewallError("public over-budget evaluation is unavailable")
    status = budget_status(family)
    if status["used"] >= status["limit"]:
        log_event("evaluate_reject", {"family": family,
                                      "reason": "budget_exhausted"}, False)
        raise BudgetExhausted(status["used"], status["limit"])

    sub = parse_submission(submission_file)
    con = _open_challenge(actor_note="evaluate")
    try:
        labels = {}
        canaries: set = set()
        for inst, date, ret in con.execute(
                "SELECT instrument, date, ret FROM labels"):
            labels[(inst, date)] = ret
        for (v,) in con.execute(
                "SELECT v FROM meta WHERE k='canaries'"):
            canaries = set(v.split(",")) if v else set()
    finally:
        con.close()

    scored: List[Tuple[float, float]] = []
    can_hits = 0
    can_total = 0
    missing = 0
    for row in sub:
        ret = labels.get((row["instrument"], row["date"]))
        if ret is None:
            missing += 1
            continue
        scored.append((row["score"], ret))
        if row["instrument"] in canaries:
            can_total += 1
            if (row["score"] >= 0) == (ret >= 0):
                can_hits += 1

    flags: List[str] = []
    canary_acc = (can_hits / can_total) if can_total else 0.0
    if can_total >= 5 and canary_acc >= 0.90:
        flags.append("CONTAMINATION-SUSPECT")
    if missing:
        flags.append("UNSCORED_ROWS=%d" % missing)

    n_scored = len(scored)
    metrics: Dict[str, Any] = {"n_scored": n_scored}
    # --- S9-3 small-N cutoff --------------------------------------------
    # Below MIN_N_SCORED scored predictions, hit_rate/rank_ic leak roughly
    # one bit of holdout information per query to a probing submitter.
    # Suppress them; return n_scored only (plus flags/canary bookkeeping).
    small_n = n_scored < MIN_N_SCORED
    if small_n:
        flags.append("SMALL_N_SUPPRESSED=min_n=%d" % MIN_N_SCORED)
        metrics["rank_ic"] = None
        metrics["hit_rate"] = None
        metrics["canary_accuracy"] = None
        metrics["contamination_suspect"] = None
    else:
        metrics["rank_ic"] = round(_pearson(_rank([s for s, _ in scored]),
                                            _rank([r for _, r in scored])), 6)
        metrics["hit_rate"] = round(
            sum(1 for s, r in scored if (s >= 0) == (r >= 0)) / n_scored, 6)
        metrics["canary_accuracy"] = round(canary_acc, 6)
        metrics["contamination_suspect"] = "CONTAMINATION-SUSPECT" in flags
    metrics["canary_n"] = can_total
    metrics["flags"] = flags
    assert set(metrics) == set(_PREREGISTERED_METRIC_KEYS)

    b = _read_budget()
    fam = b.setdefault("families", {}).setdefault(family, {})
    fam["limit"] = int(fam.get("limit", b.get("default_limit",
                                              DEFAULT_BUDGET_PER_FAMILY)))
    fam["used"] = int(fam.get("used", 0)) + 1
    _write_budget(b)
    log_event("evaluate", {"family": family,
                           "n_scored": metrics["n_scored"],
                           "flags": flags}, True)
    return metrics


# --------------------------------------------------------------------------
# Selftest (S9-2: tempfile.TemporaryDirectory + residue sweep)
# --------------------------------------------------------------------------

def _residue_sweep() -> List[str]:
    """Return any fw1-selftest-* leftovers in the OS temp dir (should be [])."""
    tmp_root = tempfile.gettempdir()
    hits: List[str] = []
    try:
        for name in os.listdir(tmp_root):
            if name.startswith(_SELFTEST_PREFIX):
                hits.append(name)
    except OSError:
        pass
    return hits


def _selftest() -> List[str]:
    results: List[str] = []

    def check(name: str, ok: bool, extra: str = "") -> None:
        results.append(("PASS %s%s" % (name, (" :: " + extra) if extra else ""))
                       if ok else
                       "FAIL %s%s" % (name, (" :: " + extra) if extra else ""))

    import csv
    old_globals = {k: globals()[k] for k in
                   ("DATA_DIR", "KEY_FILE", "CHALLENGE_ENC", "MANIFEST_FILE",
                    "BUDGET_FILE", "ACCESS_LOG")}
    try:
        # --- S9-2: everything happens inside a TemporaryDirectory -------
        with tempfile.TemporaryDirectory(prefix=_SELFTEST_PREFIX) as tdir:
            configure_synthetic_sandbox(tdir, ["selftest-budget", "selftest-family-a",
                                                "selftest-small-n", "selftest-canary", "selftest-noise"])

            # --- fixture: 40 real instruments x 2 dates + 8 canaries ----
            rows: List[Tuple[str, str, float]] = []
            rng_state = 12345

            def prng() -> float:
                nonlocal rng_state
                rng_state = (1103515245 * rng_state + 12345) % (2 ** 31)
                return rng_state / (2 ** 31)

            dates = ["2026-06-30", "2026-07-31"]
            for i in range(40):
                inst = "SYM%03d" % i
                for d in dates:
                    rows.append((inst, d, (prng() - 0.5) * 0.08))
            canaries = ["CANARY-%02d" % i for i in range(8)]
            holdout = "2026-07-31"
            for c in canaries:
                rows.append((c, holdout, (prng() - 0.5) * 0.08))

            def write_sub(path: str,
                          entries: List[Tuple[str, str, float]]) -> None:
                with open(path, "w", encoding="ascii", newline="") as fh:
                    w = csv.writer(fh)
                    w.writerow(["instrument", "date", "score"])
                    for e in entries:
                        w.writerow(e)

            # ================= challenge blob roundtrip ==================
            build_challenge_db(rows, canaries)
            check("build_sealed_blob", os.path.exists(globals()["CHALLENGE_ENC"])
                  and os.path.getsize(globals()["CHALLENGE_ENC"]) > 0)

            # ================= S9-1 budget ledger =======================
            init_keyfile()
            st0 = budget_status("selftest-budget")
            check("ledger_fresh_defaults",
                  st0 == {"used": 0, "limit": DEFAULT_BUDGET_PER_FAMILY},
                  str(st0))
            sub_small = os.path.join(tdir, "sub_small.csv")
            write_sub(sub_small, [("SYM000", "2026-06-30", 0.01)])
            evaluate_submission(sub_small, "selftest-budget")
            st1 = budget_status("selftest-budget")
            check("budget_decrements", st1["used"] == st0["used"] + 1,
                  "%s -> %s" % (st0, st1))

            # direct write to eval-budget.json must be rejected as TAMPER
            with open(globals()["BUDGET_FILE"], "w", encoding="ascii") as fh:
                json.dump({"default_limit": 999999,
                           "families": {"selftest-budget":
                                        {"used": 0, "limit": 999999}}}, fh)
            raised = False
            try:
                budget_status("selftest-budget")
            except TamperDetected:
                raised = True
            check("direct_budget_write_rejected_tamper", raised)

            # well-formed envelope, forged payload (recompute nothing):
            # load the CURRENT sealed envelope, flip used back to 0, write
            # WITHOUT recomputing the MAC -> MAC mismatch -> TAMPER
            _write_budget({"default_limit": DEFAULT_BUDGET_PER_FAMILY,
                           "families": {"selftest-budget": {"used": 1}},
                           "last_counter": 0})
            with open(globals()["BUDGET_FILE"], "r",
                      encoding="ascii") as fh:
                env = json.load(fh)
            if "payload" not in env or "mac" not in env:
                raise RuntimeError("selftest: ledger not in v2 envelope form")
            env["payload"]["families"]["selftest-budget"]["used"] = 0
            with open(globals()["BUDGET_FILE"], "w",
                      encoding="ascii") as fh:
                json.dump(env, fh)
            raised = False
            try:
                budget_status("selftest-budget")
            except TamperDetected:
                raised = True
            check("forged_payload_rejected_tamper", raised)

            # counter rollback: attacker replays a VALIDLY SEALED envelope
            # with a lower counter (e.g. an old copy of the ledger). The
            # payload's _high_water must exceed the replayed counter for
            # this to be caught -> seal the forged payload at its own
            # current counter, then roll the envelope counter back.
            _write_budget({"default_limit": DEFAULT_BUDGET_PER_FAMILY,
                           "families": {"selftest-budget": {"used": 1}},
                           "last_counter": 0})
            with open(globals()["BUDGET_FILE"], "r",
                      encoding="ascii") as fh:
                env2 = json.load(fh)
            cur = int(env2["counter"])
            rolled_payload = json.loads(json.dumps(env2["payload"]))
            rollback_env = {
                "schema": LEDGER_SCHEMA_V2,
                "counter": max(0, cur - 3),
                "payload": rolled_payload,
                "mac": _ledger_mac(max(0, cur - 3), rolled_payload),
            }
            with open(globals()["BUDGET_FILE"], "w",
                      encoding="ascii") as fh:
                json.dump(rollback_env, fh)
            raised = False
            try:
                budget_status("selftest-budget")
            except TamperDetected:
                raised = True
            check("counter_rollback_rejected_tamper", raised)

            tamper_logged = False
            with open(globals()["ACCESS_LOG"], encoding="ascii") as fh:
                for ln in fh:
                    if '"TAMPER"' in ln and '"budget_ledger"' in ln:
                        tamper_logged = True
                        break
            check("budget_tamper_logged", tamper_logged)

            # restore a clean sealed ledger and continue
            clean = {"default_limit": DEFAULT_BUDGET_PER_FAMILY,
                     "families": {"selftest-budget": {"used": 1}},
                     "last_counter": 0}
            _write_budget(clean)

            # ================= challenge blob roundtrip ==================
            with open(globals()["CHALLENGE_ENC"], "rb") as fh:
                head = fh.read(64)
            check("blob_not_plaintext_sqlite",
                  not head.startswith(b"SQLite format 3"))

            sub1 = os.path.join(tdir, "sub1.csv")
            write_sub(sub1, [(r[0], r[1], r[2]) for r in rows])  # oracle
            m1 = evaluate_submission(sub1, "selftest-family-a")
            check("roundtrip_metrics_only",
                  set(m1) == set(_PREREGISTERED_METRIC_KEYS))
            check("perfect_sub_high_ic_and_hitrate",
                  m1["rank_ic"] > 0.95 and m1["hit_rate"] > 0.99,
                  "ic=%.4f hr=%.4f" % (m1["rank_ic"], m1["hit_rate"]))
            check("no_labels_leaked",
                  "ret" not in _canonical(m1) and "label" not in _canonical(m1))

            # ============ S9-3 small-N scoring cutoff ====================
            msmall = evaluate_submission(sub_small, "selftest-small-n")
            check("small_n_suppresses_rates",
                  msmall["n_scored"] == 1
                  and msmall["hit_rate"] is None
                  and msmall["canary_accuracy"] is None,
                  _canonical(msmall)[:120])
            check("small_n_flag_present",
                  any(str(f).startswith("SMALL_N_SUPPRESSED")
                      for f in msmall["flags"]))
            check("large_n_returns_rates",
                  "hit_rate" in m1 and m1["n_scored"] >= MIN_N_SCORED)

            # ============ budget exhaustion / override ===================
            b = _read_budget()
            used_now = b["families"]["selftest-budget"]["used"]
            b["families"]["selftest-budget"]["limit"] = used_now
            _write_budget(b)
            raised = False
            try:
                evaluate_submission(sub_small, "selftest-budget")
            except BudgetExhausted:
                raised = True
            check("budget_exhaustion_raises", raised)
            err_text = ""
            try:
                evaluate_submission(sub_small, "selftest-budget")
            except BudgetExhausted as exc:
                err_text = str(exc)
            check("budget_error_scrubbed",
                  "family" not in err_text.lower()
                  and "selftest-budget" not in err_text
                  and tdir not in err_text,
                  err_text[:80])
            raised = False
            try:
                evaluator_override("selftest-budget", "previously public override attempt")
            except FirewallError:
                raised = True
            check("public_override_refused", raised)
            check("override_does_not_change_budget",
                  budget_status("selftest-budget")["used"] == used_now)

            # ============ tamper abort (challenge blob) ==================
            with open(globals()["CHALLENGE_ENC"], "r+b") as fh:
                fh.seek(10)
                orig = fh.read(1)
                fh.seek(10)
                fh.write(bytes([orig[0] ^ 0xFF]))
            raised = False
            try:
                _open_challenge(actor_note="tamper-test")
            except TamperDetected:
                raised = True
            check("tamper_aborts", raised)
            build_challenge_db(list(rows), canaries)  # restore
            check("tamper_logged",
                  os.path.exists(globals()["ACCESS_LOG"])
                  and "TAMPER" in open(globals()["ACCESS_LOG"],
                                       encoding="ascii").read())

            # ============ canary detection logic =========================
            # NOTE (S9-3): a canary-only submission is n=8 -> below MIN_N
            # -> rates suppressed. Build LARGE-N submissions instead:
            # all 88 holdout-window rows, with sign foresight on the 8
            # canaries only.
            sub_canary = os.path.join(tdir, "sub_canary.csv")
            can_set = set(canaries)
            can_entries: List[Tuple[str, str, float]] = [
                (r[0], r[1],
                 (0.01 if r[2] >= 0 else -0.01) if r[0] in can_set
                 else ((prng() - 0.5) * 0.08))
                for r in rows if r[1] == holdout]
            write_sub(sub_canary, can_entries)
            mc = evaluate_submission(sub_canary, "selftest-canary")
            check("canary_contamination_flagged",
                  mc["contamination_suspect"]
                  and mc["canary_n"] == 8 and mc["canary_accuracy"] >= 0.90,
                  "acc=%.2f" % mc["canary_accuracy"])
            sub_noise = os.path.join(tdir, "sub_noise.csv")
            noise_entries: List[Tuple[str, str, float]] = []
            ci = 0
            for r in rows:
                if r[1] != holdout:
                    noise_entries.append(
                        (r[0], r[1], (prng() - 0.5) * 0.08))
                    continue
                if r[0] in can_set:
                    noise_entries.append((r[0], r[1],
                                          0.01 if ci % 2 == 0 else -0.01))
                    ci += 1
                else:
                    noise_entries.append((r[0], r[1], (prng() - 0.5) * 0.08))
            write_sub(sub_noise, noise_entries)
            mn = evaluate_submission(sub_noise, "selftest-noise")
            check("clean_sub_not_flagged", not mn["contamination_suspect"],
                  "acc=%.2f" % mn["canary_accuracy"])

            # ============ S9-4 error scrubbing ===========================
            err = ""
            saved_kf = globals()["KEY_FILE"]
            try:
                globals()["KEY_FILE"] = os.path.join(
                    tdir, ".does-not-exist-key")
                try:
                    _load_secret()
                except FirewallError as exc:
                    err = str(exc)
            finally:
                globals()["KEY_FILE"] = saved_kf
            check("missing_key_error_scrubbed",
                  err != "" and tdir not in err
                  and ".does-not-exist-key" not in err
                  and DATA_DIR not in err,
                  err[:80])

            # ============ S9-5 rotate_key ================================
            check("rotate_key_key_exists_pre", os.path.exists(saved_kf))
            with open(saved_kf, "rb") as fh:
                pre_bytes = fh.read()
            rotated = rotate_key()
            check("rotate_key_rotates", rotated is True)
            check("rotate_key_unlinks", not os.path.exists(saved_kf))
            # prove the bytes were overwritten before deletion by rotating
            # a fresh key and watching the intermediate state
            init_keyfile(force=True)
            seen_overwritten = {"flag": False}

            orig_unlink = os.unlink

            def spy_unlink(path, *a, **kw):  # type: ignore
                if os.path.abspath(str(path)) == os.path.abspath(saved_kf):
                    with open(path, "rb") as fh:
                        cur = fh.read()
                    if cur != pre_bytes and len(cur) == len(pre_bytes):
                        seen_overwritten["flag"] = True
                return orig_unlink(path, *a, **kw)

            os.unlink = spy_unlink  # type: ignore
            try:
                rotate_key()
            finally:
                os.unlink = orig_unlink  # type: ignore
            check("rotate_key_overwrites_before_unlink",
                  seen_overwritten["flag"])
            kr_logged = False
            with open(globals()["ACCESS_LOG"], encoding="ascii") as fh:
                for ln in fh:
                    if '"KEY_ROTATION"' in ln:
                        kr_logged = True
                        break
            check("key_rotation_logged", kr_logged)
            init_keyfile(force=True)   # restore usable key for log checks

            # ============ log append integrity ============================
            ok, msg = verify_log_integrity()
            check("log_chain_verifies", ok, msg)
            with open(globals()["ACCESS_LOG"], "r", encoding="ascii") as fh:
                lines = [ln for ln in fh if ln.strip()]
            recs = [json.loads(ln) for ln in lines]
            check("log_records_all_actions",
                  any(r["action"] == "TAMPER" for r in recs)
                  and any(r["action"] == "evaluate" for r in recs)
                  and any(r["action"] == "KEY_ROTATION" for r in recs)
                  and all({"actor", "ts", "action", "success"} <= set(r)
                          for r in recs),
                  "%d events" % len(recs))
            mid = len(lines) // 2
            mutated = lines[:]
            victim = json.loads(mutated[mid])
            victim["success"] = not victim["success"]
            mutated[mid] = _canonical(victim) + "\n"
            with open(globals()["ACCESS_LOG"], "w", encoding="ascii") as fh:
                fh.writelines(mutated)
            ok2, _ = verify_log_integrity()
            check("log_detects_midchain_edit", not ok2)
        # TemporaryDirectory context exits here: guaranteed cleanup (S9-2)

        # ============ S9-2 residue sweep =================================
        residue = _residue_sweep()
        check("no_fw1_selftest_residue", residue == [], ",".join(residue))
    finally:
        # restore module-level path globals even on failure
        for k, v in old_globals.items():
            globals()[k] = v
        # TemporaryDirectory owns cleanup. Never delete other test runs' paths.
    return results


def run_selftest() -> int:
    res = _selftest()
    fails = [r for r in res if r.startswith("FAIL")]
    print("\n".join(res))
    print("SELFTEST: %d checks, %d failures" % (len(res), len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(run_selftest())
