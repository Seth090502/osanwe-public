"""Exit-gated tests for tools/fis/obs.py (OVERNIGHT-W7).

Covers: payload redaction; health_check all-ok on the healthy repo;
corrupted-copy probe fails correctly; lineage_trace >= 4 hops on the real
S7 artifact; backup -> restore roundtrip verifies.

Standard library only. ASCII. No network. No git.
Run: python tools/fis/test_obs.py   (exit 0 = pass, nonzero = fail)
"""

import json
import os
import shutil
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import obs  # noqa: E402

FAILURES = []
PASSES = []


def check(name, cond, detail=""):
    if cond:
        PASSES.append(name)
        print("PASS %s" % name)
    else:
        FAILURES.append((name, detail))
        print("FAIL %s -- %s" % (name, detail))


def main():
    # ------------------------------------------------------------------
    # 1. Redaction
    # ------------------------------------------------------------------
    payload = {
        "ticker": "AAPL",
        "order_amount": 12500.50,
        "nested": {
            "account_number": "1234-5678",
            "balance_usd": 98765.43,
            "note": "no sensitive words here",
            "items": [{"ticker_symbol": "TSLA"}],
        },
        "safe_field": "keep me",
    }
    red = obs.redact(payload)
    check("redact.ticker", red["ticker"] == "[REDACTED]")
    check("redact.amount", red["order_amount"] == "[REDACTED]")
    check("redact.nested_account",
          red["nested"]["account_number"] == "[REDACTED]")
    check("redact.nested_balance", red["nested"]["balance_usd"] == "[REDACTED]")
    check("redact.list_item_ticker",
          red["nested"]["items"][0]["ticker_symbol"] == "[REDACTED]")
    check("redact.unknown_fields_suppressed",
          red["safe_field"] == obs.REDACTED
          and red["nested"]["note"] == obs.REDACTED)
    check("redact.no_sensitive_keys_survive",
          not obs.contains_sensitive_value(red))
    check("redact.input_not_mutated", payload["ticker"] == "AAPL")

    tmp_state = tempfile.mkdtemp(prefix="obs-test-state-")
    ev_path = os.path.join(tmp_state, "events.jsonl")
    evt = obs.emit_event("test.event", payload=payload,
                         run_id="run-1", correlation_id="corr-9",
                         causation_id="caus-3", dataset_version="abc123",
                         error_class=None, event_log_path=ev_path)
    stored = json.loads(open(ev_path).read().strip())
    for field in ("ts", "event_type", "run_id", "correlation_id",
                  "causation_id", "dataset_version", "model_version",
                  "error_class"):
        check("emit.field_%s" % field, field in stored)
    check("emit.payload_redacted_in_log",
          not obs.contains_sensitive_value(stored["payload"]))
    check("emit.correlation_ids",
          stored["correlation_id"] == "corr-9"
          and stored["causation_id"] == "caus-3")

    # ------------------------------------------------------------------
    # 2. health_check all-ok on the healthy repo
    # ------------------------------------------------------------------
    results = obs.health_check()
    by_comp = {r["component"]: r for r in results}
    for comp in ("factors.db", "dual_prices.db", "edgar-pit-full.jsonl",
                 "shadow-log-chain", "shadow-freeze.json",
                 "scheduler-state-dir"):
        check("health.component_present_%s" % comp, comp in by_comp)
    schema_ok = all(
        set(("component", "ok", "detail", "checked_at")) <= set(r.keys())
        for r in results)
    check("health.result_schema", schema_ok)
    failed = [r["component"] for r in results if not r["ok"]]
    check("health.all_ok_on_healthy_repo", not failed,
          "failed components: %s" % failed)

    # ------------------------------------------------------------------
    # 3. Corrupted-copy probe fails correctly
    # ------------------------------------------------------------------
    broken_dir = tempfile.mkdtemp(prefix="obs-broken-repo-")
    try:
        # factors.db: a non-sqlite file with content
        bad_db = os.path.join(broken_dir, "factors.db")
        with open(bad_db, "wb") as fh:
            fh.write(b"this is definitely not a sqlite database" * 10)

        # dual_prices.db: valid sqlite but zero rows
        empty_db = os.path.join(broken_dir, "dual_prices.db")
        con = sqlite3.connect(empty_db)
        con.execute("CREATE TABLE t (x)")
        con.commit()
        con.close()

        # edgar-pit: unparseable lines only
        bad_pit = os.path.join(broken_dir, "edgar-pit-full.jsonl")
        with open(bad_pit, "w") as fh:
            fh.write("{not json at all\n")

        # shadow log: tampered record -> chain digest mismatch
        good_log = obs.PREDICTIONS_PATH
        recs = [json.loads(l) for l in open(good_log)]
        recs[0]["confidence"] = 0.99          # tamper without rechain
        bad_log = os.path.join(broken_dir, "shadow-predictions.jsonl")
        with open(bad_log, "w") as fh:
            for r in recs:
                fh.write(json.dumps(r) + "\n")

        # freeze file: invalid JSON
        bad_freeze = os.path.join(broken_dir, "shadow-freeze.json")
        with open(bad_freeze, "w") as fh:
            fh.write("{ truncated json ...")

        p = obs.Paths(factors_db=bad_db, dual_prices_db=empty_db,
                      edgar_pit=bad_pit, shadow_predictions=bad_log,
                      freeze=bad_freeze,
                      scheduler_state_dir=os.path.join(broken_dir,
                                                       "scheduler-state"))
        res = {r["component"]: r for r in obs.health_check(paths=p)}
        check("broken.factors_db_fails", not res["factors.db"]["ok"],
              res["factors.db"]["detail"])
        check("broken.dual_prices_zero_rows_fails",
              not res["dual_prices.db"]["ok"], res["dual_prices.db"]["detail"])
        check("broken.edgar_pit_unparseable_fails",
              not res["edgar-pit-full.jsonl"]["ok"],
              res["edgar-pit-full.jsonl"]["detail"])
        check("broken.shadow_chain_digest_mismatch_detected",
              not res["shadow-log-chain"]["ok"],
              res["shadow-log-chain"]["detail"])
        check("broken.freeze_unparseable_fails",
              not res["shadow-freeze.json"]["ok"],
              res["shadow-freeze.json"]["detail"])
    finally:
        shutil.rmtree(broken_dir, ignore_errors=True)

    # ------------------------------------------------------------------
    # 4. lineage_trace >= 4 hops on the real S7 artifact
    # ------------------------------------------------------------------
    hops = obs.lineage_trace(obs.DEFAULT_DECISION_ID, echo=False)
    kinds = [h["kind"] for h in hops]
    n_hops = len(hops)
    check("lineage.hops_ge_4", n_hops >= 4, "got %d" % n_hops)
    decision = hops[0]
    check("lineage.root_is_decision_artifact",
          decision["id"] == obs.DEFAULT_DECISION_ID)
    has_source = any(k == "fact" for k in kinds)
    check("lineage.reaches_fact_sources", has_source, "kinds=%s" % kinds)
    # every hop's inputs are themselves present in the trace
    ids = set(h["id"] for h in hops)
    dangling = [i for h in hops for i in h["inputs"] if i not in ids]
    check("lineage.no_dangling_inputs", not dangling, str(dangling))
    print(obs.lineage_trace.__module__ + ": lineage demo (%d hops)" % n_hops)
    obs.lineage_trace(obs.DEFAULT_DECISION_ID, echo=True)

    # unknown id raises KeyError
    raised = False
    try:
        obs.lineage_trace("artifact:definitely-not-there", echo=False)
    except KeyError:
        raised = True
    check("lineage.unknown_id_raises", raised)

    # ------------------------------------------------------------------
    # 5. backup -> restore roundtrip
    # ------------------------------------------------------------------
    backup_root = os.path.join(tmp_state, "backups")
    backup_dir, manifest = obs.backup_critical(backup_root=backup_root)
    check("backup.dir_created", os.path.isdir(backup_dir), backup_dir)
    check("backup.manifest_written",
          os.path.exists(os.path.join(backup_dir, "manifest.json")))
    check("backup.covers_all_critical_files",
          set(manifest["files"]) == set(obs.CRITICAL_FILES),
          "%s vs %s" % (sorted(manifest["files"]),
                        sorted(obs.CRITICAL_FILES)))
    # manifest hashes match actual copied bytes
    hash_ok = all(
        obs._sha256_file(os.path.join(backup_dir, name)) == meta["sha256"]
        for name, meta in manifest["files"].items())
    check("backup.manifest_hashes_match_copies", hash_ok)
    # sources untouched (spot-check one sha against live file)
    live_pred_sha = obs._sha256_file(obs.PREDICTIONS_PATH)
    check("backup.source_untouched",
          live_pred_sha ==
          manifest["files"]["shadow-predictions.jsonl"]["sha256"])

    result = obs.restore_verify(backup_dir)
    check("restore.ok", result.get("ok") is True, json.dumps(result)[:300])
    check("restore.hashes_all_ok", result.get("hashes_all_ok") is True)
    check("restore.chain_ok", result.get("chain_ok") is True)
    check("restore.chain_records_match_live",
          result.get("chain_records") ==
          len([l for l in open(obs.PREDICTIONS_PATH) if l.strip()]))
    check("restore.temp_dir_removed",
          result.get("temp_dir_removed") is True)
    # no restore artifacts left in system temp
    leftovers = [d for d in os.listdir(tempfile.gettempdir())
                 if d.startswith("fis-restore-verify-")]
    check("restore.no_temp_leftovers", not leftovers, str(leftovers))

    # corrupted BACKUP copy must fail verification
    corrupt_backup = os.path.join(tmp_state, "backup-corrupt")
    shutil.copytree(backup_dir, corrupt_backup)
    victim = os.path.join(corrupt_backup, "shadow-predictions.jsonl")
    with open(victim, "ab") as fh:
        fh.write(b'tampered line appended\n')
    res_bad = obs.restore_verify(corrupt_backup)
    check("restore.corrupted_backup_fails", res_bad.get("ok") is False,
          json.dumps(res_bad)[:300])

    # missing manifest fails cleanly
    nomani = os.path.join(tmp_state, "backup-nomani")
    os.makedirs(nomani)
    res_no = obs.restore_verify(nomani)
    check("restore.missing_manifest_fails_cleanly", res_no.get("ok") is False)

    # ------------------------------------------------------------------
    # Verdict
    # ------------------------------------------------------------------
    print("")
    print("=" * 60)
    print("PASSED: %d   FAILED: %d" % (len(PASSES), len(FAILURES)))
    for name, detail in FAILURES:
        print("  FAILED: %s -- %s" % (name, detail))
    print("=" * 60)
    return 0 if not FAILURES else 1


if __name__ == "__main__":
    sys.exit(main())
