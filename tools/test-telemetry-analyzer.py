#!/usr/bin/env python3
"""
test-telemetry-analyzer.py -- 11 named test cases for tools/telemetry_analyzer.py.

Test #1 (test_classifies_session_stop_for_main_session_stop_event) covers the
D-T1 classifier (2026-06-10): main-session Stop-hook events written into the
subagent sink (tool_use_id == session_id AND empty agent_type) classify as
session_stop, NOT orphan_stop -- the orphan-investigation-2026-06-10 root
cause (~97 of 106 'orphans' were this artifact). Test #1b asserts a TRUE
subagent orphan still classifies orphan_stop. The remaining cases cover
pairing, fixture filtering, error clustering, schema versioning, idempotency,
and a regression baseline against the real archive.

Usage:
  python tools/test-telemetry-analyzer.py             # run all tests
  python tools/test-telemetry-analyzer.py --test <name>   # focused single test

Exit code: 0 on all-pass, 1 on any failure.
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", os.getcwd()))
TOOLS_DIR = VAULT_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

# Use a hyphenated import workaround (telemetry_analyzer.py is hyphen-free; fine)
import telemetry_analyzer as ta  # noqa: E402


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _make_workspace():
    """Create a tmp dir with a state subdir + empty db path. Returns (tmp, state_dir, db_path)."""
    tmp = Path(tempfile.mkdtemp(prefix="telemetry-test-"))
    state_dir = tmp / "state"
    state_dir.mkdir()
    db_path = state_dir / "telemetry.db"
    return tmp, state_dir, db_path


def _write_jsonl(path: Path, records):
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# ----------------------------------------------------------------------
# Test 1: main-session Stop classification (D-T1; PRIMARY)
# ----------------------------------------------------------------------
def test_classifies_session_stop_for_main_session_stop_event():
    """Fixture: a single Stop record with the main-session signature
    (tool_use_id == session_id, empty agent_type) and no preceding Start.
    Assertion (D-T1 2026-06-10): pair.status == 'session_stop', NOT
    orphan_stop; events.is_orphan stays 0. Pre-D-T1 this exact fixture
    (modeled on the real 5/22 16:57:38 record) classified orphan_stop --
    the root-caused ~10x orphan-count overstatement."""
    tmp, state_dir, db_path = _make_workspace()
    try:
        session_stop = {
            "ts": "2026-05-22T16:57:38.530",
            "event": "stop",
            "tool_use_id": "387d8e91-6fe9-4c8a-a42c-963cb70ffc83",
            "agent_type": "",
            "session_id": "387d8e91-6fe9-4c8a-a42c-963cb70ffc83",
            "cwd": "/vault-root",
            "duration_seconds": None,
        }
        _write_jsonl(state_dir / "subagent-telemetry-2026-05-22.jsonl", [session_stop])

        with ta.TelemetryAnalyzer(state_dir=state_dir, db_path=db_path,
                                  exclude_test_fixtures=False) as a:
            a.rebuild()
            report = a.analyze(window_days=3650)

            # Verify D-T1 pair classification
            assert report.pair_summary.get("session_stop") == 1, (
                f"expected 1 session_stop, got {report.pair_summary}")
            assert report.pair_summary.get("orphan_stop") == 0, (
                f"main-session stop must NOT count as orphan; got {report.pair_summary}")
            assert report.pair_summary.get("paired") == 0
            assert report.pair_summary.get("hanging_start") == 0

            # Verify event row does NOT carry is_orphan
            c = a._conn.cursor()
            c.execute("SELECT is_orphan, raw_json FROM events WHERE event_kind='subagent_stop'")
            row = c.fetchone()
            assert row is not None
            assert row["is_orphan"] == 0, "session stop must not flip is_orphan"

            # Verify raw_json preserves tool_use_id == session_id coalescence
            raw = json.loads(row["raw_json"])
            assert raw["tool_use_id"] == raw["session_id"], (
                "the main-session signature is preserved in raw_json")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------
# Test 1b: TRUE subagent orphan still classifies orphan_stop (D-T1 guard)
# ----------------------------------------------------------------------
def test_classifies_orphan_stop_for_true_subagent_orphan():
    """Fixture: a Stop with a distinct tool_use_id + real agent_type and no
    preceding Start (a genuine start-record drop under heavy dispatch).
    Assertion: still classifies orphan_stop with is_orphan == 1 -- D-T1
    narrows the orphan definition, it does not blind the detector."""
    tmp, state_dir, db_path = _make_workspace()
    try:
        true_orphan = {
            "ts": "2026-06-09T03:14:00.000",
            "event": "stop",
            "tool_use_id": "real-dropped-start-uuid-001",
            "agent_type": "workflow-subagent",
            "session_id": "real-session-uuid-xyz",
            "cwd": "/vault-root",
            "duration_seconds": 41.2,
        }
        _write_jsonl(state_dir / "subagent-telemetry-2026-06-09.jsonl", [true_orphan])

        with ta.TelemetryAnalyzer(state_dir=state_dir, db_path=db_path,
                                  exclude_test_fixtures=False) as a:
            a.rebuild()
            report = a.analyze(window_days=3650)
            assert report.pair_summary.get("orphan_stop") == 1, (
                f"true subagent orphan must classify orphan_stop; got {report.pair_summary}")
            assert report.pair_summary.get("session_stop") == 0
            c = a._conn.cursor()
            c.execute("SELECT is_orphan FROM events WHERE event_kind='subagent_stop'")
            assert c.fetchone()["is_orphan"] == 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------
# Test 2: clean pair within session
# ----------------------------------------------------------------------
def test_pairs_clean_start_stop_within_session():
    """Fixture: a Start record then a Stop 6.44s later with matching tool_use_id.
    Assertion: pair.status == 'paired', duration_seconds == 6.44."""
    tmp, state_dir, db_path = _make_workspace()
    try:
        records = [
            {
                "ts": "2026-05-22T16:32:06.038",
                "event": "start",
                "tool_use_id": "toolu_real_explore",
                "agent_type": "Explore",
                "session_id": "387d8e91-6fe9-4c8a-a42c-963cb70ffc83",
                "cwd": "/vault-root",
            },
            {
                "ts": "2026-05-22T16:32:12.477",
                "event": "stop",
                "tool_use_id": "toolu_real_explore",
                "agent_type": "Explore",
                "session_id": "387d8e91-6fe9-4c8a-a42c-963cb70ffc83",
                "cwd": "/vault-root",
                "duration_seconds": 6.44,
            },
        ]
        _write_jsonl(state_dir / "subagent-telemetry-2026-05-22.jsonl", records)
        with ta.TelemetryAnalyzer(state_dir=state_dir, db_path=db_path,
                                  exclude_test_fixtures=False) as a:
            a.rebuild()
            report = a.analyze(window_days=3650)
            assert report.pair_summary["paired"] == 1
            assert report.pair_summary["orphan_stop"] == 0
            assert report.pair_summary["hanging_start"] == 0
            # Check duration in duration_by_agent_type
            dat = report.duration_by_agent_type.get("Explore", {})
            assert dat.get("count") == 1
            assert abs(dat.get("p50", 0) - 6.44) < 0.01
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------
# Test 3: hanging Start (no Stop) detection
# ----------------------------------------------------------------------
def test_classifies_hanging_start_when_no_stop():
    """Fixture: a Start record with no following Stop.
    Assertion: pair.status == 'hanging_start', stop_event_id is None."""
    tmp, state_dir, db_path = _make_workspace()
    try:
        hanging = {
            "ts": "2026-05-21T22:06:35.851",
            "event": "start",
            "tool_use_id": "toolu_hanging_explore",
            "agent_type": "Explore",
            "session_id": "real-session-uuid-abc",
            "cwd": "/vault-root",
        }
        _write_jsonl(state_dir / "subagent-telemetry-2026-05-21.jsonl", [hanging])
        with ta.TelemetryAnalyzer(state_dir=state_dir, db_path=db_path,
                                  exclude_test_fixtures=False) as a:
            a.rebuild()
            report = a.analyze(window_days=3650)
            assert report.pair_summary["hanging_start"] == 1
            assert report.pair_summary["paired"] == 0
            assert report.pair_summary["orphan_stop"] == 0
            c = a._conn.cursor()
            c.execute("SELECT start_event_id, stop_event_id FROM pairs WHERE status='hanging_start'")
            r = c.fetchone()
            assert r["start_event_id"] is not None
            assert r["stop_event_id"] is None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------
# Test 4: default fixture filter excludes synthetics
# ----------------------------------------------------------------------
def test_excludes_test_fixtures_by_default():
    """Fixture: 7 synthetic records matching R11 detection markers.
    Assertion: real_count == 0, filtered_count == 7, signals exclude them."""
    tmp, state_dir, db_path = _make_workspace()
    try:
        records = [
            # Rule 1: fixed tool_use_id set
            {"ts": "2026-05-21T22:00:00.000", "event": "start",
             "tool_use_id": "epsilon", "agent_type": "Explore",
             "session_id": "s", "cwd": ""},
            {"ts": "2026-05-21T22:00:01.000", "event": "start",
             "tool_use_id": "theta", "agent_type": "Plan",
             "session_id": "sess-t", "cwd": ""},
            {"ts": "2026-05-21T22:00:02.000", "event": "stop",
             "tool_use_id": "alpha_test", "agent_type": "",
             "session_id": "x", "cwd": "x"},
            {"ts": "2026-05-21T22:00:03.000", "event": "start",
             "tool_use_id": "unknown", "agent_type": "",
             "session_id": "", "cwd": ""},
            # Rule 2: regex on tool_use_id
            {"ts": "2026-05-21T22:00:04.000", "event": "start",
             "tool_use_id": "toolu_test_foo", "agent_type": "Plan",
             "session_id": "any", "cwd": "/some/path"},
            {"ts": "2026-05-21T22:00:05.000", "event": "stop",
             "tool_use_id": "toolu_sweep_x", "agent_type": "",
             "session_id": "any2", "cwd": "/some/path"},
            # Rule 3: cwd empty/single-char
            {"ts": "2026-05-21T22:00:06.000", "event": "start",
             "tool_use_id": "real_uuid_abc", "agent_type": "Explore",
             "session_id": "real-session", "cwd": ""},
        ]
        _write_jsonl(state_dir / "subagent-telemetry-2026-05-21.jsonl", records)
        with ta.TelemetryAnalyzer(state_dir=state_dir, db_path=db_path,
                                  exclude_test_fixtures=True) as a:
            a.rebuild()
            report = a.analyze(window_days=3650)
            assert report.total_count == 7
            assert report.real_count == 0
            assert report.filtered_count == 7
            assert report.pair_summary.get("paired", 0) == 0
            assert report.pair_summary.get("orphan_stop", 0) == 0
            assert report.pair_summary.get("hanging_start", 0) == 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------
# Test 5: opt-in includes fixtures
# ----------------------------------------------------------------------
def test_includes_test_fixtures_when_opt_in_flag_set():
    """Fixture: same 7 records as test 4 but with exclude_test_fixtures=False.
    Assertion: real_count == 7, filtered_count == 0."""
    tmp, state_dir, db_path = _make_workspace()
    try:
        records = [
            {"ts": "2026-05-21T22:00:00.000", "event": "start",
             "tool_use_id": "epsilon", "agent_type": "Explore",
             "session_id": "s", "cwd": ""},
            {"ts": "2026-05-21T22:00:01.000", "event": "stop",
             "tool_use_id": "epsilon", "agent_type": "Explore",
             "session_id": "s", "cwd": "", "duration_seconds": 1.0},
        ]
        _write_jsonl(state_dir / "subagent-telemetry-2026-05-21.jsonl", records)
        with ta.TelemetryAnalyzer(state_dir=state_dir, db_path=db_path,
                                  exclude_test_fixtures=False) as a:
            a.rebuild()
            report = a.analyze(window_days=3650)
            assert report.real_count == 2
            assert report.filtered_count == 0
            assert report.pair_summary["paired"] == 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------
# Test 6: failure clustering by (tool_name, error_class)
# ----------------------------------------------------------------------
def test_failure_clusters_by_tool_and_error_class():
    """Fixture: 4 Bash failures with different error texts.
    Assertion: clusters resolve to expected error_class buckets."""
    tmp, state_dir, db_path = _make_workspace()
    try:
        records = [
            {"ts": "2026-05-23T01:00:00.000", "tool": "Bash",
             "error": "Exit code 1\nsomething 404 not found",
             "session_id": "real-uuid-1", "cwd": "/vault-root",
             "mode": "auto", "tool_input_keys": ["command"]},
            {"ts": "2026-05-23T01:00:01.000", "tool": "Bash",
             "error": "Exit code 1\nupstream 500 server error",
             "session_id": "real-uuid-1", "cwd": "/vault-root",
             "mode": "auto", "tool_input_keys": ["command"]},
            {"ts": "2026-05-23T01:00:02.000", "tool": "Bash",
             "error": "Exit code 2\nvalidator block",
             "session_id": "real-uuid-1", "cwd": "/vault-root",
             "mode": "auto", "tool_input_keys": ["command"]},
            {"ts": "2026-05-23T01:00:03.000", "tool": "Bash",
             "error": "Exit code 1\nanother 404 not found",
             "session_id": "real-uuid-1", "cwd": "/vault-root",
             "mode": "auto", "tool_input_keys": ["command"]},
        ]
        _write_jsonl(state_dir / "failures-2026-05-23.jsonl", records)
        with ta.TelemetryAnalyzer(state_dir=state_dir, db_path=db_path,
                                  exclude_test_fixtures=False) as a:
            a.rebuild()
            report = a.analyze(window_days=3650)
            # Convert clusters to {(tool, error_class): count}
            cluster_map = {(c["tool_name"], c["error_class"]): c["count"]
                           for c in report.failure_clusters}
            assert cluster_map.get(("Bash", "Exit_code_1_HTTP_404")) == 2
            assert cluster_map.get(("Bash", "Exit_code_1_HTTP_500")) == 1
            assert cluster_map.get(("Bash", "Exit_code_2")) == 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------
# Test 7: legacy records without schema_version
# ----------------------------------------------------------------------
def test_handles_legacy_records_without_schema_version():
    """Fixture: a record missing schema_version (the current hook emit shape).
    Assertion: ingested as schema_version='0.9', raw_json preserved."""
    tmp, state_dir, db_path = _make_workspace()
    try:
        legacy = {
            "ts": "2026-05-21T22:00:00.000",
            "event": "stop",
            "tool_use_id": "real-uuid-xyz",
            "agent_type": "Explore",
            "session_id": "real-uuid-xyz",
            "cwd": "/vault-root",
            "duration_seconds": 3.5,
        }
        _write_jsonl(state_dir / "subagent-telemetry-2026-05-21.jsonl", [legacy])
        with ta.TelemetryAnalyzer(state_dir=state_dir, db_path=db_path,
                                  exclude_test_fixtures=False) as a:
            a.rebuild()
            c = a._conn.cursor()
            c.execute("SELECT schema_version, raw_json FROM events")
            row = c.fetchone()
            assert row["schema_version"] == "0.9"
            assert "duration_seconds" in row["raw_json"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------
# Test 8: v2.1.147 records with agent_id distinct from tool_use_id
# ----------------------------------------------------------------------
def test_handles_v2147_records_with_agent_id_separate_from_tool_use_id():
    """Fixture: a Stop record with schema_version='1.0' + distinct agent_id + duration_ms.
    Assertion: agent_id captured separately, duration_seconds derived from duration_ms/1000."""
    tmp, state_dir, db_path = _make_workspace()
    try:
        v147 = {
            "schema_version": "1.0",
            "ts": "2026-05-23T10:00:00.000",
            "event": "stop",
            "tool_use_id": "toolu_abc_xyz",
            "agent_id": "agent_uuid_distinct_from_tool_use_id",
            "agent_type": "Plan",
            "session_id": "real-session-uuid",
            "cwd": "/vault-root",
            "duration_ms": 4500,
            "background_tasks": False,
        }
        _write_jsonl(state_dir / "subagent-telemetry-2026-05-23.jsonl", [v147])
        with ta.TelemetryAnalyzer(state_dir=state_dir, db_path=db_path,
                                  exclude_test_fixtures=False) as a:
            a.rebuild()
            c = a._conn.cursor()
            c.execute("SELECT schema_version, agent_id, duration_seconds FROM events")
            row = c.fetchone()
            assert row["schema_version"] == "1.0"
            assert row["agent_id"] == "agent_uuid_distinct_from_tool_use_id"
            assert abs(row["duration_seconds"] - 4.5) < 0.01
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------
# Test 9: cursor advances idempotently
# ----------------------------------------------------------------------
def test_cursor_advances_idempotently():
    """Fixture: ingest the same JSONL file twice.
    Assertion: second invocation inserts zero new rows."""
    tmp, state_dir, db_path = _make_workspace()
    try:
        records = [
            {"ts": "2026-05-23T01:00:00.000", "event": "start",
             "tool_use_id": "real-uuid-1", "agent_type": "Explore",
             "session_id": "real-uuid-1", "cwd": "/vault-root"},
            {"ts": "2026-05-23T01:00:01.000", "event": "stop",
             "tool_use_id": "real-uuid-1", "agent_type": "Explore",
             "session_id": "real-uuid-1", "cwd": "/vault-root",
             "duration_seconds": 1.0},
        ]
        _write_jsonl(state_dir / "subagent-telemetry-2026-05-23.jsonl", records)
        with ta.TelemetryAnalyzer(state_dir=state_dir, db_path=db_path,
                                  exclude_test_fixtures=False) as a:
            stats1 = a.ingest_new()
            stats2 = a.ingest_new()
            assert stats1.events_ingested == 2
            assert stats2.events_ingested == 0
            # cursor table should have one row for the source file
            c = a._conn.cursor()
            c.execute("SELECT COUNT(*) AS n FROM cursors")
            assert c.fetchone()["n"] == 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------
# Test 10: regression baseline against the real archive
# ----------------------------------------------------------------------
def test_real_archive_orphan_count_matches_phase0_finding():
    """Read the actual .claude/state/{subagent-telemetry,failures}-*.jsonl files.

    Recalibrated for D-T1 (2026-06-10): pre-fix the full archive showed 189
    'orphans' (dominated by main-session Stop-hook events); post-fix the same
    archive decomposes into 176 session_stops + 15 TRUE orphans (all
    workflow-subagent start-drops under heavy parallel dispatch; rate ~0.01).
    Band [2, 60] absorbs future accretion at the observed ~0.5-2% drop rate
    on max-concurrency days without re-breaking this baseline. Also locks the
    D-T1 classifier on real data: session_stop must be substantial (>= 50)."""
    state_dir = VAULT_ROOT / ".claude" / "state"
    db_path = state_dir / "telemetry-test-real.db"
    # Clean any prior test db
    if db_path.exists():
        db_path.unlink()
    try:
        with ta.TelemetryAnalyzer(state_dir=state_dir, db_path=db_path,
                                  exclude_test_fixtures=True) as a:
            a.rebuild()
            report = a.analyze(window_days=3650)
            orphan_count = report.pair_summary.get("orphan_stop", 0)
            assert 2 <= orphan_count <= 60, (
                f"expected TRUE orphan_count in [2,60] (D-T1 baseline 15); got {orphan_count}.\n"
                f"pair_summary={report.pair_summary}"
            )
            session_stops = report.pair_summary.get("session_stop", 0)
            assert session_stops >= 50, (
                f"D-T1 classifier should find substantial session_stops on the real "
                f"archive (baseline 176); got {session_stops}"
            )
            # Also sanity check: real_count > 0
            assert report.real_count > 0
    finally:
        if db_path.exists():
            db_path.unlink()


# ----------------------------------------------------------------------
# Runner
# ----------------------------------------------------------------------
TEST_REGISTRY = {
    "test_classifies_session_stop_for_main_session_stop_event": test_classifies_session_stop_for_main_session_stop_event,
    "test_classifies_orphan_stop_for_true_subagent_orphan": test_classifies_orphan_stop_for_true_subagent_orphan,
    "test_pairs_clean_start_stop_within_session": test_pairs_clean_start_stop_within_session,
    "test_classifies_hanging_start_when_no_stop": test_classifies_hanging_start_when_no_stop,
    "test_excludes_test_fixtures_by_default": test_excludes_test_fixtures_by_default,
    "test_includes_test_fixtures_when_opt_in_flag_set": test_includes_test_fixtures_when_opt_in_flag_set,
    "test_failure_clusters_by_tool_and_error_class": test_failure_clusters_by_tool_and_error_class,
    "test_handles_legacy_records_without_schema_version": test_handles_legacy_records_without_schema_version,
    "test_handles_v2147_records_with_agent_id_separate_from_tool_use_id": test_handles_v2147_records_with_agent_id_separate_from_tool_use_id,
    "test_cursor_advances_idempotently": test_cursor_advances_idempotently,
    "test_real_archive_orphan_count_matches_phase0_finding": test_real_archive_orphan_count_matches_phase0_finding,
}


def run_tests(test_filter: str = "") -> int:
    failed = []
    passed = 0
    for name, fn in TEST_REGISTRY.items():
        if test_filter and test_filter != name:
            continue
        try:
            fn()
            print(f"  PASS: {name}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {name}\n    {e}")
            failed.append(name)
        except Exception as e:
            print(f"  ERROR: {name}\n    {type(e).__name__}: {e}")
            failed.append(name)
    print()
    print(f"Result: {passed} passed, {len(failed)} failed")
    return 1 if failed else 0


def main():
    p = argparse.ArgumentParser(description="Unit tests for tools/telemetry_analyzer.py")
    p.add_argument("--test", default="", help="Run only the named test")
    args = p.parse_args()
    return run_tests(test_filter=args.test)


if __name__ == "__main__":
    sys.exit(main())
