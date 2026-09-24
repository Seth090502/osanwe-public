"""FIS observability + reliability module (OVERNIGHT-W7).

Structured event emission, cheap health probes, dataset freshness,
provenance lineage tracing, and a tested backup/restore cycle for the
critical FIS artifacts.

Design references (adapted, zero dependencies): OpenTelemetry structured
events with correlation/causation ids; OpenLineage-style job lineage.
Standard library only. No network. No git. ASCII only.

Usage:
    python tools/fis/obs.py health
    python tools/fis/obs.py freshness
    python tools/fis/obs.py lineage [decision_id]
    python tools/fis/obs.py backup
    python tools/fis/obs.py restore <backup_dir>
    python tools/fis/obs.py events [N]
"""

import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

THIS_FILE = os.path.abspath(__file__)
TOOLS_FIS = os.path.dirname(THIS_FILE)
REPO_ROOT = os.path.dirname(os.path.dirname(TOOLS_FIS))

EFFORTS_WORK = os.path.join(REPO_ROOT, "Efforts", "osanwe-v2-overhaul",
                            "_work")
FIS_DATA = os.path.join(EFFORTS_WORK, "fis-data")      # canonical live data
OBS_STATE = os.path.join(FIS_DATA, "obs-state")        # W7-owned state
BACKUP_ROOT = os.path.join(OBS_STATE, "backups")

EVENT_LOG_PATH = os.path.join(OBS_STATE, "events.jsonl")
PROV_STORE_PATH = os.path.join(FIS_DATA, "g3-s7-provenance-store.json")
DATASET_REGISTRY_PATH = os.path.join(FIS_DATA, "dataset-registry.jsonl")
FACTORS_DB_PATH = os.path.join(EFFORTS_WORK, "factors.db")
DUAL_PRICES_DB_PATH = os.path.join(FIS_DATA, "dual_prices.db")
EDGAR_PIT_PATH = os.path.join(FIS_DATA, "edgar-pit-full.jsonl")
FREEZE_PATH = os.path.join(FIS_DATA, "shadow-freeze.json")
PREDICTIONS_PATH = os.path.join(FIS_DATA, "shadow-predictions.jsonl")
SCHEDULER_STATE_DIR = os.path.join(FIS_DATA, "scheduler-state")

# Files whose loss would invalidate shadow/tournament/ontology state.
CRITICAL_FILES = {
    "shadow-predictions.jsonl": PREDICTIONS_PATH,
    "shadow-freeze.json": FREEZE_PATH,
    "ontology.db": os.path.join(FIS_DATA, "ontology.db"),
    "dataset-registry.jsonl": DATASET_REGISTRY_PATH,
    "tournament-results.jsonl": os.path.join(FIS_DATA,
                                             "tournament-results.jsonl"),
}

DEFAULT_DECISION_ID = "artifact:s7-execution-request"

MODEL_VERSION_DEFAULT = "fis-shadow-s3-v1"


def utc_now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_ts(text):
    """Parse the timestamp formats found in dataset-registry.jsonl."""
    text = str(text).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        dt = datetime.strptime(text[:10], "%Y-%m-%d")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class Paths(object):
    """Bundle of probed locations, overridable for tests."""

    def __init__(self, **kw):
        self.factors_db = kw.get("factors_db", FACTORS_DB_PATH)
        self.dual_prices_db = kw.get("dual_prices_db", DUAL_PRICES_DB_PATH)
        self.edgar_pit = kw.get("edgar_pit", EDGAR_PIT_PATH)
        self.shadow_predictions = kw.get("shadow_predictions",
                                         PREDICTIONS_PATH)
        self.freeze = kw.get("freeze", FREEZE_PATH)
        self.scheduler_state_dir = kw.get("scheduler_state_dir",
                                          SCHEDULER_STATE_DIR)


# --------------------------------------------------------------------------
# Payload redaction
# --------------------------------------------------------------------------

DENYLIST_SUBSTRINGS = (
    "ticker", "amount", "balance", "account", "password", "secret", "token",
    "apikey", "privatekey", "authorization", "cookie", "session", "credential",
    "ssn", "dob", "email", "phone", "iban", "household", "member", "lotid",
    "beneficiary", "salary", "networth", "position", "liquidity",
)
REDACTED = "[REDACTED]"

# Operational payloads are a closed vocabulary. New fields do not become
# eligible for durable logging merely because no one added them to a denylist.
ALLOWED_PAYLOAD_KEYS = frozenset({
    "count", "marks", "refusals", "consequential", "ok", "severity", "state",
    "status", "event_type", "error_class", "effective_date", "known_at",
    "checked_at", "ts", "nested", "items", "payload",
})
ALLOWED_EVENT_TYPES = frozenset({
    "test.event", "scenario.event.ingested", "provenance.invalidated",
    "twin.updated", "alternatives.ranked", "decision.assembled",
    "approval.required", "backup.created", "restore.verified", "restore.failed",
})
_PAYLOAD_ENUMS = {
    "severity": frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "LOW", "MEDIUM", "HIGH"}),
    "status": frozenset({"OK", "FAILED", "COMPLETE", "INCOMPLETE", "UNKNOWN", "GATED", "REFUSED"}),
    "state": frozenset({"DRAFT_ANALYSIS", "VALIDATED_ALTERNATIVES",
        "RECOMMENDATION_PENDING_REVIEW", "HUMAN_APPROVAL_REQUIRED",
        "APPROVED_FOR_SIMULATION", "REJECTED", "EXPIRED", "INVALIDATED"}),
    "event_type": ALLOWED_EVENT_TYPES,
    "error_class": frozenset({"RESTORE_FAIL"}),
}


def _payload_value(key, value):
    if value is None or value == REDACTED:
        return value
    if key in ("nested", "items", "payload"):
        return redact(value) if isinstance(value, (dict, list, tuple)) else REDACTED
    if key in ("count", "marks", "refusals"):
        return value if type(value) is int and value >= 0 else REDACTED
    if key in ("ok", "consequential"):
        return value if type(value) is bool else REDACTED
    if key in _PAYLOAD_ENUMS:
        return value if isinstance(value, str) and value in _PAYLOAD_ENUMS[key] else REDACTED
    if key in ("effective_date", "known_at", "checked_at", "ts"):
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return value
        except (AttributeError, TypeError, ValueError):
            return REDACTED
    return REDACTED


def _safe_terminal(value):
    """Render untrusted identifiers without controls or additional log lines."""
    return json.dumps(str(value), ensure_ascii=True)[1:-1]


def _opaque_log_id(value):
    """Keep bounded operational identifiers; redact paths and household labels."""
    if value is None:
        return None
    text = str(value)
    if re.fullmatch(r"(?:[a-fA-F0-9]{6,64}|[a-fA-F0-9-]{36}|"
                    r"(?:run|corr|caus)-[A-Za-z0-9]+|(?:corr:)?S[0-9]+)", text):
        return text
    return REDACTED


def _key_is_sensitive(key):
    low = re.sub(r"[^a-z0-9]", "", str(key).lower())
    return any(marker in low for marker in DENYLIST_SUBSTRINGS)


def redact(obj):
    """Keep only known operational fields; unknown values fail closed."""
    if isinstance(obj, dict):
        out = {}
        for key, val in obj.items():
            if _key_is_sensitive(key) or key not in ALLOWED_PAYLOAD_KEYS:
                out[key] = REDACTED
            else:
                out[key] = _payload_value(key, val)
        return out
    if isinstance(obj, (list, tuple)):
        return [redact(item) for item in obj]
    if isinstance(obj, str):
        if obj == REDACTED:
            return obj
        # Payload strings are machine statuses or timestamps, not free text.
        # Notes, provider messages and household descriptions belong outside
        # the durable operational event log.
        if not re.fullmatch(r"[A-Za-z0-9_.:+-]{1,80}", obj) or \
                re.search(r"\d{3}-\d{2}-\d{4}", obj):
            return REDACTED
    return obj


def contains_sensitive_value(obj):
    """True if any denylisted key maps to a value that was NOT redacted.

    Keys whose value is exactly the REDACTED sentinel count as clean --
    they are the product of redaction, not a leak.
    """
    return redact(obj) != obj


# --------------------------------------------------------------------------
# Structured event emitter
# --------------------------------------------------------------------------

def emit_event(event_type, payload=None, run_id=None, correlation_id=None,
               causation_id=None, dataset_version=None,
               model_version=MODEL_VERSION_DEFAULT, error_class=None,
               event_log_path=EVENT_LOG_PATH):
    """Append one structured event as JSONL. Payload is redacted first."""
    event = {
        "ts": utc_now_iso(),
        "event_type": event_type if event_type in ALLOWED_EVENT_TYPES else REDACTED,
        "run_id": _opaque_log_id(run_id),
        "correlation_id": _opaque_log_id(correlation_id),
        "causation_id": _opaque_log_id(causation_id),
        "dataset_version": _opaque_log_id(dataset_version),
        "model_version": model_version if model_version == MODEL_VERSION_DEFAULT else REDACTED,
        "error_class": _payload_value("error_class", error_class),
        "payload": redact(payload if payload is not None else {}),
    }
    blob = json.dumps(event, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)
    directory = os.path.dirname(event_log_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(event_log_path, "a", encoding="ascii") as fh:
        fh.write(blob + "\n")
    return event


# --------------------------------------------------------------------------
# Hash-chain verification (self-contained; matches tools/fis/shadow.py)
# --------------------------------------------------------------------------

def canonical_sha256(obj):
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("ascii")
    return hashlib.sha256(blob).hexdigest()


def shadow_record_hash(rec):
    probe = {k: v for k, v in rec.items() if k != "record_hash"}
    return canonical_sha256(probe)


def verify_shadow_chain(path):
    """Verify prev_record_hash linkage + per-record hashes of a shadow log.

    Returns (ok, head_hash_or_None, n_records, message).
    """
    if not os.path.exists(path):
        return False, None, 0, "missing"
    prev = "GENESIS"
    n = 0
    head = None
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                return False, head, n, ("unparseable line at record %d"
                                        % (n + 1))
            claimed = rec.get("record_hash")
            if rec.get("prev_record_hash") != prev:
                return False, head, n, ("chain break at record %d "
                                        "(prev mismatch)" % (n + 1))
            if shadow_record_hash(rec) != claimed:
                return False, head, n, ("digest mismatch at record %d"
                                        % (n + 1))
            prev = claimed
            head = claimed
            n += 1
    if n == 0:
        return False, None, 0, "empty"
    return True, head, n, "ok (%d records)" % n


# --------------------------------------------------------------------------
# Health check
# --------------------------------------------------------------------------

def _check_file_present(path):
    if not os.path.exists(path):
        return False, "missing"
    size = os.path.getsize(path)
    if size == 0:
        return False, "empty (0 bytes)"
    return True, "%d bytes" % size


def _sqlite_rowcount_ro(path):
    con = sqlite3.connect("file:%s?mode=ro" % path.replace("\\", "/"),
                          uri=True)
    try:
        tables = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")]
        best_table, best = None, -1
        for t in tables:
            try:
                cnt = con.execute(
                    "SELECT COUNT(*) FROM '%s'" % t).fetchone()[0]
            except sqlite3.DatabaseError:
                continue
            if cnt > best:
                best_table, best = t, cnt
        return best, best_table
    finally:
        con.close()


def health_check(paths=None):
    """Cheap existence/parsability/rowcount probes over material subsystems.

    Returns list of {component, ok, detail, checked_at}.
    """
    p = paths or Paths()
    results = []
    checked_at = utc_now_iso()

    def add(component, ok, detail):
        results.append({"component": component, "ok": bool(ok),
                        "detail": str(detail), "checked_at": checked_at})

    # 1. factors.db -- exists, nonempty, opens read-only, rows > 0
    ok, detail = _check_file_present(p.factors_db)
    if ok:
        try:
            rows, table = _sqlite_rowcount_ro(p.factors_db)
            ok = rows > 0
            detail = "max table '%s' rows=%d" % (table, rows)
        except Exception as exc:
            ok, detail = False, "sqlite ro open failed: %s" % exc
    add("factors.db", ok, detail)

    # 2. dual_prices.db
    ok, detail = _check_file_present(p.dual_prices_db)
    if ok:
        try:
            rows, table = _sqlite_rowcount_ro(p.dual_prices_db)
            ok = rows > 0
            detail = "max table '%s' rows=%d" % (table, rows)
        except Exception as exc:
            ok, detail = False, "sqlite ro open failed: %s" % exc
    add("dual_prices.db", ok, detail)

    # 3. edgar-pit-full.jsonl -- lines > 0, every line parses
    ok, detail = _check_file_present(p.edgar_pit)
    if ok:
        lines = bad = 0
        with open(p.edgar_pit, "r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                lines += 1
                try:
                    json.loads(line)
                except ValueError:
                    bad += 1
        ok = lines > 0 and bad == 0
        detail = "lines=%d unparseable=%d" % (lines, bad)
    add("edgar-pit-full.jsonl", ok, detail)

    # 4. shadow prediction log -- chain head verifiable
    ok, head, n, msg = verify_shadow_chain(p.shadow_predictions)
    add("shadow-log-chain", ok,
        "records=%d head=%s %s" % (n, (head or "-")[:12], msg))

    # 5. freeze file parses and carries freeze_hash
    ok, detail = _check_file_present(p.freeze)
    if ok:
        try:
            with open(p.freeze, "r", encoding="utf-8") as fh:
                freeze = json.load(fh)
            ok = bool(freeze.get("freeze_hash"))
            detail = "freeze_id=%s" % freeze.get("freeze_id", "?")
            if not ok:
                detail += " (freeze_hash missing)"
        except Exception as exc:
            ok, detail = False, "unparseable: %s" % exc
    add("shadow-freeze.json", ok, detail)

    # 6. scheduler-state dir (W2 contract surface)
    if os.path.isdir(p.scheduler_state_dir):
        add("scheduler-state-dir", True, "dir present")
    else:
        try:
            os.makedirs(p.scheduler_state_dir, exist_ok=True)
            add("scheduler-state-dir", True,
                "absent; initialized empty by obs")
        except OSError as exc:
            add("scheduler-state-dir", False, "cannot create: %s" % exc)

    return results


# --------------------------------------------------------------------------
# Dataset freshness
# --------------------------------------------------------------------------

def freshness_report(registry_path=None, now=None):
    """days-stale per dataset from dataset-registry.jsonl timestamps."""
    registry_path = registry_path or DATASET_REGISTRY_PATH
    now = now or datetime.now(timezone.utc)
    rows = []
    with open(registry_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            ts_text = rec.get("retrieval_timestamp")
            if ts_text is None:
                rows.append({"dataset_id": rec.get("dataset_id"),
                             "retrieval_timestamp": None,
                             "days_stale": None,
                             "detail": "no retrieval_timestamp"})
                continue
            retrieved = _parse_ts(ts_text)
            days = (now - retrieved).total_seconds() / 86400.0
            rows.append({
                "dataset_id": rec.get("dataset_id"),
                "retrieval_timestamp": ts_text,
                "days_stale": round(days, 2),
            })
    return rows


# --------------------------------------------------------------------------
# Lineage trace
# --------------------------------------------------------------------------

def load_provenance_store(path=None):
    path = path or PROV_STORE_PATH
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def lineage_trace(decision_id, store_path=None, echo=True):
    """Walk provenance store inputs recursively; return decision->source chain.

    Hops are returned decision-first (calc -> ... -> source facts).
    """
    store = load_provenance_store(store_path)
    artifacts = store["artifacts"]
    if decision_id not in artifacts:
        raise KeyError("unknown artifact id: %s (have %d artifacts)"
                       % (decision_id, len(artifacts)))

    hops = []
    seen = set()
    stack = [decision_id]
    while stack:
        aid = stack.pop(0)
        if aid in seen:
            continue
        seen.add(aid)
        cur = artifacts[aid]["current"]
        hops.append({
            "id": aid,
            "kind": cur.get("kind"),
            "inputs": list(cur.get("inputs") or []),
            "digest": cur.get("digest"),
            "computed_at": cur.get("computed_at"),
            "script_path": cur.get("script_path"),
        })
        for inp in cur.get("inputs") or []:
            if inp not in seen:
                stack.append(inp)

    if echo:
        depth_by_id = {}
        order = list(reversed(hops))          # sources first
        for hop in order:
            depth_by_id[hop["id"]] = 0
        for hop in order:
            for inp in hop["inputs"]:
                depth_by_id[inp] = max(depth_by_id.get(inp, 0),
                                       depth_by_id[hop["id"]] + 1)
        print("LINEAGE %s (%d hops)" % (_safe_terminal(decision_id), len(hops)))
        for hop in sorted(order, key=lambda h: depth_by_id[h["id"]]):
            indent = "  " * depth_by_id[hop["id"]]
            role = {"fact": "SOURCE/FACT", "artifact": "CALC",
                    "decision": "DECISION"}.get(hop["kind"],
                                                hop["kind"] or "?")
            print("%s[%s] %s  digest=%s  inputs=%d"
                  % (indent, _safe_terminal(role), _safe_terminal(hop["id"]),
                     _safe_terminal((hop["digest"] or "-")[:16]),
                     len(hop["inputs"])))
    return hops


# --------------------------------------------------------------------------
# Backup / restore
# --------------------------------------------------------------------------

def _sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def backup_critical(backup_root=None, label="critical"):
    """Copy CRITICAL_FILES into a timestamped dir with a SHA256 manifest.

    Never modifies sources. Returns (backup_dir, manifest_dict).
    """
    backup_root = backup_root or BACKUP_ROOT
    stamp = utc_now_iso().replace(":", "").replace("-", "")
    backup_dir = os.path.join(backup_root, "backup-%s-%s" % (stamp, label))
    os.makedirs(backup_dir, exist_ok=True)

    files = {}
    for name, src in sorted(CRITICAL_FILES.items()):
        if not os.path.exists(src):
            raise FileNotFoundError("critical file missing: %s" % src)
        dst = os.path.join(backup_dir, name)
        shutil.copy2(src, dst)
        files[name] = {
            "sha256": _sha256_file(dst),
            "bytes": os.path.getsize(dst),
            "source_relpath": os.path.relpath(src, REPO_ROOT),
        }

    manifest = {
        "created_utc": utc_now_iso(),
        "backup_dir": backup_dir,
        "label": label,
        "files": files,
        "manifest_version": 1,
    }
    with open(os.path.join(backup_dir, "manifest.json"), "w",
              encoding="ascii") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
    return backup_dir, manifest


def restore_verify(backup_dir, keep_temp=False):
    """Restore into a TEMP DIR (never touching live paths), re-verify every
    SHA256 AND the shadow-log chain of the restored copy, then delete temp.

    Returns result dict; raises nothing for expected failures (reported).
    """
    manifest_path = os.path.join(backup_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        return {"ok": False, "error": "manifest.json missing in %s"
                                      % backup_dir}
    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)

    temp_dir = tempfile.mkdtemp(prefix="fis-restore-verify-")
    files = []
    all_hashes_ok = True
    try:
        for name, meta in sorted(manifest["files"].items()):
            src = os.path.join(backup_dir, name)
            dst = os.path.join(temp_dir, name)
            entry = {"name": name}
            if not os.path.exists(src):
                entry.update(hash_ok=False, detail="file missing in backup")
                all_hashes_ok = False
            else:
                shutil.copy2(src, dst)
                got = _sha256_file(dst)
                ok = got == meta["sha256"]
                entry.update(hash_ok=ok,
                             detail="sha256 match" if ok
                             else "sha256 MISMATCH got=%s" % got[:12])
                if not ok:
                    all_hashes_ok = False
            files.append(entry)

        restored_log = os.path.join(temp_dir, "shadow-predictions.jsonl")
        chain_ok, head, n, chain_msg = verify_shadow_chain(restored_log)
    finally:
        if not keep_temp:
            shutil.rmtree(temp_dir, ignore_errors=True)

    ok = all_hashes_ok and chain_ok
    return {
        "ok": ok,
        "backup_dir": backup_dir,
        "restored_to": "<temp dir>",
        "hashes_all_ok": all_hashes_ok,
        "files": files,
        "chain_ok": chain_ok,
        "chain_records": n,
        "chain_head": head,
        "chain_detail": chain_msg,
        "temp_dir_removed": not keep_temp,
    }


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "health"

    if cmd == "health":
        results = health_check()
        all_ok = True
        for r in results:
            all_ok = all_ok and r["ok"]
            print("%-22s %-3s %s" % (r["component"],
                                     "OK" if r["ok"] else "FAIL",
                                     r["detail"]))
        print("HEALTH:", "ALL OK" if all_ok else "DEGRADED")
        return 0 if all_ok else 1

    if cmd == "freshness":
        for row in freshness_report():
            print(json.dumps(row, sort_keys=True))
        return 0

    if cmd == "lineage":
        did = argv[1] if len(argv) > 1 else DEFAULT_DECISION_ID
        hops = lineage_trace(did)
        print("hops=%d" % len(hops))
        return 0

    if cmd == "backup":
        backup_dir, manifest = backup_critical()
        for name, meta in sorted(manifest["files"].items()):
            print("%-28s %8d B  %s" % (name, meta["bytes"],
                                       meta["sha256"][:16]))
        print("BACKUP DIR:", backup_dir)
        emit_event("backup.created", {"backup_dir": backup_dir,
                                      "files": sorted(manifest["files"])})
        return 0

    if cmd == "restore":
        if len(argv) < 2:
            print("usage: obs.py restore <backup_dir>")
            return 2
        result = restore_verify(argv[1])
        print(json.dumps(result, indent=1, sort_keys=True))
        emit_event("restore.verified" if result.get("ok")
                   else "restore.failed",
                   {"backup_dir": result.get("backup_dir"),
                    "ok": result.get("ok")},
                   error_class=None if result.get("ok") else "RESTORE_FAIL")
        return 0 if result.get("ok") else 1

    if cmd == "events":
        n = int(argv[1]) if len(argv) > 1 else 10
        if os.path.exists(EVENT_LOG_PATH):
            with open(EVENT_LOG_PATH, "r", encoding="ascii") as fh:
                lines = fh.read().splitlines()
            for line in lines[-n:]:
                print(line)
        return 0

    print("unknown command: %s" % cmd)
    return 2


if __name__ == "__main__":
    sys.exit(main())
