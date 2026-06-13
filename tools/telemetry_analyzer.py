#!/usr/bin/env python3
"""
telemetry_analyzer.py -- Read-side consumer for the SubagentStart/Stop + PostToolUseFailure
telemetry sinks at .claude/state/{subagent-telemetry,failures}-YYYY-MM-DD.jsonl.

Closes the open feedback loop: hooks ship telemetry, this module reads it.

Architecture:
  - JSONL (existing, unchanged): append-only truth from the hooks.
  - SQLite (this module): derived index at .claude/state/telemetry.db.
    Rebuilt incrementally via cursor; full rebuild on --rebuild.
  - Versioned envelope: records without schema_version treated as "0.9" (legacy).
    Future records with "1.0" carry additive fields (agent_id, duration_ms,
    background_tasks). raw_json preserved per row for forensic replay.

Signals computed:
  1. Subagent pair status: paired | orphan_stop | hanging_start
  2. Duration percentiles per agent_type (p50, p95)
  3. Tool failure rate per tool_name
  4. Tool failure clustering by (tool_name, error_class)
  5. Session failure topology: sessions with >=N failures and no clean SubagentStop

Test-fixture detection (default-ON; R11 mitigation):
  Records where tool_use_id matches synthetic markers, OR cwd empty/single-char
  are excluded from signal computations. Provenance line surfaces filtered count.
  Opt-in to include via --include-test-fixtures.

CLI:
  python tools/telemetry_analyzer.py                       # default 7-day window, human output
  python tools/telemetry_analyzer.py --json                # machine-readable JSON output
  python tools/telemetry_analyzer.py --rebuild --json      # full rebuild + JSON
  python tools/telemetry_analyzer.py --window 30           # 30-day window
  python tools/telemetry_analyzer.py --include-test-fixtures   # raw view, no filter
  python tools/telemetry_analyzer.py --include-agents-view     # poll `claude agents --json`
  python tools/telemetry_analyzer.py --markdown <path>     # write markdown report to path
  python tools/telemetry_analyzer.py --followups-block     # compact /retro form to stdout

Module surface:
  from tools.telemetry_analyzer import TelemetryAnalyzer
  a = TelemetryAnalyzer()
  stats = a.ingest_new()
  report = a.analyze(window_days=7)
  a.render_markdown(report, Path("wiki/maintenance/telemetry-2026-05-23.md"))
  block = a.render_followups_block(report)
"""
import argparse
import json
import os
import re
import sqlite3
import statistics
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", os.getcwd()))
STATE_DIR = VAULT_ROOT / ".claude" / "state"
DEFAULT_DB_PATH = STATE_DIR / "telemetry.db"

# Test-fixture detection (R11; default-ON via --exclude-test-fixtures default True)
TEST_FIXTURE_TOOL_USE_IDS = {
    "unknown", "epsilon", "theta", "alpha_test",
    "toolu_test_alpha", "toolu_real", "toolu_sweep",
}
TEST_FIXTURE_TOOL_USE_ID_RE = re.compile(r"^toolu_(test|sweep|real)")


def is_test_fixture(record: dict) -> bool:
    """Multi-rule synthetic detection (refinement-cycle-2; session_id rule dropped).

    Returns True if the record matches ANY of:
      1. tool_use_id in fixed set
      2. tool_use_id matches regex ^toolu_(test|sweep|real)
      3. cwd empty or single-character placeholder
    """
    tuid = record.get("tool_use_id", "") or ""
    cwd = record.get("cwd", "") or ""
    if tuid in TEST_FIXTURE_TOOL_USE_IDS:
        return True
    if TEST_FIXTURE_TOOL_USE_ID_RE.match(tuid):
        return True
    if len(cwd) <= 1:
        return True
    return False


def is_session_stop(row) -> bool:
    """D-T1 (2026-06-10): main-session Stop-hook events written into the
    subagent sink carry tool_use_id == session_id AND an empty agent_type;
    no SubagentStart can ever match them, so counting them as orphan_stop
    overstated real start-drops ~10x (orphan-investigation-2026-06-10).
    BOTH conditions are required: legacy subagent records exist with
    tool_use_id == session_id but a real agent_type (those must keep
    pairing eligibility)."""
    return bool(row["tool_use_id"]) and row["tool_use_id"] == row["session_id"] \
        and not row["agent_type"]


# Error-class regex prefix patterns (compiled once)
ERROR_CLASS_PATTERNS = [
    (re.compile(r"^Exit code (\d+).*?\b(\d{3})\b", re.DOTALL),
     lambda m: f"Exit_code_{m.group(1)}_HTTP_{m.group(2)}"),
    (re.compile(r"^Exit code (\d+)", re.DOTALL),
     lambda m: f"Exit_code_{m.group(1)}"),
    (re.compile(r"^old_string not found"),
     lambda m: "Edit_old_string_not_found"),
    (re.compile(r"^HTTP (\d+)"),
     lambda m: f"HTTP_{m.group(1)}"),
    (re.compile(r"^err\d+", re.IGNORECASE),
     lambda m: "test_err_marker"),
]


def derive_error_class(error_text: str) -> str:
    """Map raw error text to a stable error_class via prefix-regex match.
    Falls back to 'unclassified' if no pattern matches."""
    if not error_text:
        return "empty_error"
    for pat, fmt in ERROR_CLASS_PATTERNS:
        m = pat.match(error_text)
        if m:
            return fmt(m)
    return "unclassified"


@dataclass
class IngestStats:
    events_ingested: int = 0
    skipped_existing: int = 0
    files_scanned: int = 0
    new_orphans: int = 0


@dataclass
class AnalyzerReport:
    generated_at: str = ""
    window_days: int = 7
    window_start: str = ""
    real_count: int = 0
    filtered_count: int = 0
    total_count: int = 0
    pair_summary: dict = field(default_factory=dict)
    duration_by_agent_type: dict = field(default_factory=dict)
    failure_rate_by_tool: dict = field(default_factory=dict)
    failure_clusters: list = field(default_factory=list)
    session_failures: list = field(default_factory=list)
    agents_view_snapshot: dict = field(default_factory=dict)
    mid_task_crashes: list = field(default_factory=list)


class TelemetryAnalyzer:
    """Read-only analyzer over JSONL telemetry sinks; SQLite-indexed derived state."""

    def __init__(self, state_dir: Path = STATE_DIR, db_path: Path = DEFAULT_DB_PATH,
                 exclude_test_fixtures: bool = True):
        self.state_dir = Path(state_dir)
        self.db_path = Path(db_path)
        self.exclude_test_fixtures = exclude_test_fixtures
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _init_schema(self):
        c = self._conn.cursor()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            schema_version TEXT NOT NULL,
            event_kind TEXT NOT NULL,
            ts_iso TEXT NOT NULL,
            session_id TEXT,
            tool_use_id TEXT,
            agent_id TEXT,
            agent_type TEXT,
            tool_name TEXT,
            error_text TEXT,
            error_class TEXT,
            duration_seconds REAL,
            is_orphan INTEGER,
            cwd TEXT,
            raw_json TEXT NOT NULL,
            source_file TEXT NOT NULL,
            source_line INTEGER NOT NULL,
            UNIQUE(source_file, source_line)
        );
        CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
        CREATE INDEX IF NOT EXISTS idx_events_kind_ts ON events(event_kind, ts_iso);

        CREATE TABLE IF NOT EXISTS cursors (
            source_file TEXT PRIMARY KEY,
            last_processed_ts TEXT NOT NULL,
            last_processed_line INTEGER NOT NULL,
            last_run_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pairs (
            pair_id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_event_id INTEGER,
            stop_event_id INTEGER,
            session_id TEXT,
            tool_use_id TEXT,
            agent_type TEXT,
            duration_seconds REAL,
            status TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_pairs_status ON pairs(status);
        """)
        self._conn.commit()

    # ------------------------------------------------------------------
    # Ingest layer (cursor-based incremental + full rebuild)
    # ------------------------------------------------------------------
    def rebuild(self) -> IngestStats:
        """Drop and rebuild the events + pairs tables. Cursors reset."""
        c = self._conn.cursor()
        c.executescript("""
        DELETE FROM events;
        DELETE FROM pairs;
        DELETE FROM cursors;
        """)
        self._conn.commit()
        return self.ingest_new()

    def ingest_new(self) -> IngestStats:
        """Cursor-advance ingest across all JSONL sources. Idempotent (UNIQUE constraint)."""
        stats = IngestStats()
        for source_path in sorted(self.state_dir.glob("subagent-telemetry-*.jsonl")):
            stats.events_ingested += self._ingest_file(source_path, "subagent", stats)
            stats.files_scanned += 1
        for source_path in sorted(self.state_dir.glob("failures-*.jsonl")):
            stats.events_ingested += self._ingest_file(source_path, "failure", stats)
            stats.files_scanned += 1
        self._rebuild_pairs()
        # Count orphans surfaced this run
        c = self._conn.cursor()
        c.execute("SELECT COUNT(*) FROM pairs WHERE status='orphan_stop'")
        stats.new_orphans = c.fetchone()[0]
        return stats

    def _ingest_file(self, source_path: Path, kind_family: str, stats: IngestStats) -> int:
        """Ingest one JSONL file from current cursor position. Returns rows inserted."""
        cursor_row = self._conn.execute(
            "SELECT last_processed_line FROM cursors WHERE source_file=?",
            (str(source_path),),
        ).fetchone()
        last_line = cursor_row["last_processed_line"] if cursor_row else 0
        rows_inserted = 0
        last_ts = ""
        current_line = 0
        try:
            with source_path.open("r", encoding="utf-8") as f:
                for line_no, raw in enumerate(f, start=1):
                    current_line = line_no
                    if line_no <= last_line:
                        stats.skipped_existing += 1
                        continue
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        rec = json.loads(raw)
                    except (json.JSONDecodeError, ValueError):
                        # malformed line; record at advisory level then skip
                        continue
                    self._insert_event(rec, kind_family, source_path, line_no)
                    rows_inserted += 1
                    last_ts = rec.get("ts", last_ts)
        except OSError:
            return rows_inserted

        # Update cursor (best-effort; idempotent on re-run)
        self._conn.execute(
            """INSERT INTO cursors(source_file, last_processed_ts, last_processed_line, last_run_at)
               VALUES(?,?,?,?)
               ON CONFLICT(source_file) DO UPDATE SET
                   last_processed_ts=excluded.last_processed_ts,
                   last_processed_line=excluded.last_processed_line,
                   last_run_at=excluded.last_run_at""",
            (str(source_path), last_ts, current_line, datetime.now().isoformat()),
        )
        self._conn.commit()
        return rows_inserted

    def _insert_event(self, rec: dict, kind_family: str, source_path: Path, line_no: int):
        """Single-record insert into events table. UNIQUE(source_file, source_line) gates idempotency."""
        schema_version = rec.get("schema_version", "0.9")
        ts = rec.get("ts", "")
        session_id = rec.get("session_id", "") or ""
        tool_use_id = rec.get("tool_use_id", "") or ""
        agent_id = rec.get("agent_id", "") or ""  # v2.1.147 forward
        agent_type = rec.get("agent_type", "") or ""
        cwd = rec.get("cwd", "") or ""

        if kind_family == "subagent":
            event_kind = f"subagent_{rec.get('event', 'unknown')}"  # subagent_start | subagent_stop
            # duration_seconds: prefer raw duration_ms (v2.1.147) -> /1000; else use legacy field
            duration_ms = rec.get("duration_ms")
            if duration_ms is not None:
                duration_seconds = float(duration_ms) / 1000.0
            else:
                duration_seconds = rec.get("duration_seconds")
            tool_name = None
            error_text = None
            error_class = None
        else:
            event_kind = "tool_failure"
            duration_seconds = None
            tool_name = rec.get("tool", "") or ""
            error_text = rec.get("error", "") or ""
            error_class = derive_error_class(error_text)

        try:
            self._conn.execute(
                """INSERT OR IGNORE INTO events(
                    schema_version, event_kind, ts_iso, session_id, tool_use_id,
                    agent_id, agent_type, tool_name, error_text, error_class,
                    duration_seconds, is_orphan, cwd, raw_json, source_file, source_line)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    schema_version, event_kind, ts, session_id, tool_use_id,
                    agent_id, agent_type, tool_name, error_text, error_class,
                    duration_seconds, 0, cwd, json.dumps(rec, ensure_ascii=False),
                    str(source_path), line_no,
                ),
            )
        except sqlite3.IntegrityError:
            pass

    def _rebuild_pairs(self):
        """Reconstruct subagent Start/Stop pairing.

        Algorithm:
          For each subagent_start event S, find the nearest-following subagent_stop
          with same tool_use_id (or same session_id when tool_use_id is empty/duplicates session_id).
          Main-session Stop-hook events (is_session_stop signature) -> session_stop,
          excluded from match candidacy AND from the orphan count (D-T1 2026-06-10).
          Other unmatched Stops -> orphan_stop. Unmatched Starts -> hanging_start.
        """
        c = self._conn.cursor()
        c.execute("DELETE FROM pairs")

        # Load all subagent events ordered by ts
        c.execute("""
            SELECT event_id, event_kind, ts_iso, session_id, tool_use_id, agent_type, duration_seconds
            FROM events
            WHERE event_kind IN ('subagent_start', 'subagent_stop')
            ORDER BY ts_iso, event_id
        """)
        rows = [dict(r) for r in c.fetchall()]

        consumed_stops = set()
        for s in rows:
            if s["event_kind"] != "subagent_start":
                continue
            # Look for the next stop with matching tool_use_id strictly after this start
            matched = None
            for t in rows:
                if t["event_id"] in consumed_stops:
                    continue
                if t["event_kind"] != "subagent_stop":
                    continue
                if is_session_stop(t):
                    continue  # D-T1: main-session stops never pair
                if t["ts_iso"] <= s["ts_iso"]:
                    continue
                # Match: same tool_use_id when present, OR same session_id when tool_use_id is coalesced
                if s["tool_use_id"] and s["tool_use_id"] == t["tool_use_id"]:
                    matched = t
                    break
                if not s["tool_use_id"] and s["session_id"] and s["session_id"] == t["session_id"]:
                    matched = t
                    break
            if matched:
                consumed_stops.add(matched["event_id"])
                duration = matched["duration_seconds"]
                if duration is None and s["ts_iso"] and matched["ts_iso"]:
                    try:
                        d0 = datetime.fromisoformat(s["ts_iso"])
                        d1 = datetime.fromisoformat(matched["ts_iso"])
                        duration = round((d1 - d0).total_seconds(), 3)
                    except ValueError:
                        duration = None
                self._conn.execute(
                    """INSERT INTO pairs(start_event_id, stop_event_id, session_id, tool_use_id,
                                         agent_type, duration_seconds, status)
                       VALUES(?,?,?,?,?,?,?)""",
                    (s["event_id"], matched["event_id"], s["session_id"], s["tool_use_id"],
                     s["agent_type"] or matched["agent_type"], duration, "paired"),
                )
            else:
                self._conn.execute(
                    """INSERT INTO pairs(start_event_id, stop_event_id, session_id, tool_use_id,
                                         agent_type, duration_seconds, status)
                       VALUES(?,?,?,?,?,?,?)""",
                    (s["event_id"], None, s["session_id"], s["tool_use_id"],
                     s["agent_type"], None, "hanging_start"),
                )

        # Remaining unconsumed stops -> session_stop (main-session Stop-hook
        # events, D-T1) or orphan_stop (true subagent start-drops)
        for t in rows:
            if t["event_kind"] == "subagent_stop" and t["event_id"] not in consumed_stops:
                status = "session_stop" if is_session_stop(t) else "orphan_stop"
                self._conn.execute(
                    """INSERT INTO pairs(start_event_id, stop_event_id, session_id, tool_use_id,
                                         agent_type, duration_seconds, status)
                       VALUES(?,?,?,?,?,?,?)""",
                    (None, t["event_id"], t["session_id"], t["tool_use_id"],
                     t["agent_type"], t["duration_seconds"], status),
                )
                if status == "orphan_stop":
                    # only TRUE orphans flip is_orphan on the event row
                    self._conn.execute("UPDATE events SET is_orphan=1 WHERE event_id=?", (t["event_id"],))

        self._conn.commit()

    # ------------------------------------------------------------------
    # Analysis layer
    # ------------------------------------------------------------------
    def analyze(self, window_days: int = 7) -> AnalyzerReport:
        """Compute signals over the requested window. Returns an AnalyzerReport."""
        now = datetime.now()
        window_start = (now - timedelta(days=window_days)).isoformat()
        report = AnalyzerReport(
            generated_at=now.isoformat(timespec="seconds"),
            window_days=window_days,
            window_start=window_start,
        )

        # Filter logic embedded in the helper
        real_event_ids = self._select_real_event_ids(window_start)
        all_event_ids = self._select_all_event_ids(window_start)
        report.real_count = len(real_event_ids)
        report.total_count = len(all_event_ids)
        report.filtered_count = report.total_count - report.real_count

        report.pair_summary = self._compute_pair_summary(real_event_ids)
        report.duration_by_agent_type = self._compute_duration_outliers(real_event_ids)
        report.failure_rate_by_tool = self._compute_failure_rate(real_event_ids, window_days)
        report.failure_clusters = self._compute_failure_clusters(real_event_ids)
        report.session_failures = self._compute_session_failures(real_event_ids)
        return report

    def _select_all_event_ids(self, window_start_iso: str) -> set:
        c = self._conn.cursor()
        c.execute("SELECT event_id FROM events WHERE ts_iso >= ?", (window_start_iso,))
        return {r["event_id"] for r in c.fetchall()}

    def _select_real_event_ids(self, window_start_iso: str) -> set:
        """Apply --exclude-test-fixtures filter (if enabled) at the event-row level."""
        c = self._conn.cursor()
        c.execute("SELECT event_id, raw_json FROM events WHERE ts_iso >= ?", (window_start_iso,))
        out = set()
        for r in c.fetchall():
            if not self.exclude_test_fixtures:
                out.add(r["event_id"])
                continue
            try:
                raw = json.loads(r["raw_json"])
            except (json.JSONDecodeError, ValueError):
                continue
            if not is_test_fixture(raw):
                out.add(r["event_id"])
        return out

    def _compute_pair_summary(self, real_event_ids: set) -> dict:
        """Pair counts by status, restricted to pairs whose anchor event is in the real set."""
        c = self._conn.cursor()
        c.execute("""
            SELECT pair_id, start_event_id, stop_event_id, status, agent_type, duration_seconds
            FROM pairs
        """)
        out = {"paired": 0, "orphan_stop": 0, "hanging_start": 0,
               "session_stop": 0,  # D-T1: main-session stops, reported separately
               "orphan_examples": [], "hanging_examples": []}
        for r in c.fetchall():
            anchor = r["start_event_id"] or r["stop_event_id"]
            if anchor not in real_event_ids:
                continue
            out[r["status"]] = out.get(r["status"], 0) + 1
            if r["status"] == "orphan_stop" and len(out["orphan_examples"]) < 5:
                out["orphan_examples"].append({
                    "pair_id": r["pair_id"],
                    "agent_type": r["agent_type"] or "(empty)",
                    "duration_seconds": r["duration_seconds"],
                })
            elif r["status"] == "hanging_start" and len(out["hanging_examples"]) < 5:
                out["hanging_examples"].append({
                    "pair_id": r["pair_id"],
                    "agent_type": r["agent_type"] or "(empty)",
                })
        # D-T1: session_stop rows are NOT subagent lifecycle events -- excluded
        # from the pair total and the orphan rate (reported as their own count).
        total = out["paired"] + out["orphan_stop"] + out["hanging_start"]
        out["total"] = total
        out["orphan_rate"] = round(out["orphan_stop"] / total, 3) if total else 0.0
        return out

    def _compute_duration_outliers(self, real_event_ids: set) -> dict:
        """For each agent_type, p50 + p95 of duration_seconds across paired pairs."""
        c = self._conn.cursor()
        c.execute("""
            SELECT agent_type, duration_seconds, start_event_id
            FROM pairs
            WHERE status='paired' AND duration_seconds IS NOT NULL
        """)
        buckets: dict = {}
        for r in c.fetchall():
            if r["start_event_id"] not in real_event_ids:
                continue
            agent_type = r["agent_type"] or "(empty)"
            buckets.setdefault(agent_type, []).append(float(r["duration_seconds"]))
        out = {}
        for agent_type, ds in buckets.items():
            ds_sorted = sorted(ds)
            n = len(ds_sorted)
            p50 = statistics.median(ds_sorted)
            # p95 via simple index (sufficient for small n; fall through for n<=1)
            if n >= 2:
                p95_idx = max(0, min(n - 1, int(round(0.95 * (n - 1)))))
                p95 = ds_sorted[p95_idx]
            else:
                p95 = ds_sorted[-1]
            out[agent_type] = {
                "count": n,
                "p50": round(p50, 3),
                "p95": round(p95, 3),
                "max": round(ds_sorted[-1], 3),
                "outlier": p95 > p50 * 3 if p50 > 0 else False,
            }
        return out

    def _compute_failure_rate(self, real_event_ids: set, window_days: int) -> dict:
        """Per tool_name: failure count + per-day rate (purely informational since
        we have failures but not total tool-invocation count)."""
        c = self._conn.cursor()
        c.execute("""
            SELECT event_id, tool_name FROM events
            WHERE event_kind='tool_failure'
        """)
        counts: dict = {}
        for r in c.fetchall():
            if r["event_id"] not in real_event_ids:
                continue
            tn = r["tool_name"] or "(empty)"
            counts[tn] = counts.get(tn, 0) + 1
        return {
            tn: {"count": cnt, "per_day": round(cnt / max(1, window_days), 3)}
            for tn, cnt in counts.items()
        }

    def _compute_failure_clusters(self, real_event_ids: set) -> list:
        """Cluster failures by (tool_name, error_class). Top-N (default 10) returned."""
        c = self._conn.cursor()
        c.execute("""
            SELECT event_id, tool_name, error_class FROM events
            WHERE event_kind='tool_failure'
        """)
        counts: dict = {}
        for r in c.fetchall():
            if r["event_id"] not in real_event_ids:
                continue
            key = (r["tool_name"] or "(empty)", r["error_class"] or "(empty)")
            counts[key] = counts.get(key, 0) + 1
        sorted_items = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
        return [
            {"tool_name": k[0], "error_class": k[1], "count": v}
            for k, v in sorted_items[:10]
        ]

    def compute_mid_task_crashes(self, agents_view: dict) -> list:
        """B3 mid-task crash detector: sessions in failed/stopped status with no clean SubagentStop pair.

        agents_view: {session_id: {status, name, kind, ...}} from poll_agents_view().
        Returns list of {session_id, status, name, has_clean_pair: bool, failures_in_session}.
        """
        if not agents_view:
            return []
        TERMINAL_ERROR_STATES = {"failed", "stopped"}
        out = []
        c = self._conn.cursor()
        for sid, info in agents_view.items():
            status = (info.get("status") or "").lower()
            if status not in TERMINAL_ERROR_STATES:
                continue
            c.execute("SELECT COUNT(*) AS n FROM pairs WHERE session_id=? AND status='paired'", (sid,))
            clean_count = c.fetchone()["n"]
            c.execute("SELECT COUNT(*) AS n FROM events WHERE session_id=? AND event_kind='tool_failure'", (sid,))
            fail_count = c.fetchone()["n"]
            if clean_count == 0:
                out.append({
                    "session_id": sid,
                    "status": info.get("status", ""),
                    "name": info.get("name", "") or "(unnamed)",
                    "kind": info.get("kind", ""),
                    "cwd": info.get("cwd", ""),
                    "has_clean_pair": False,
                    "failures_in_session": fail_count,
                })
        return out

    def _compute_session_failures(self, real_event_ids: set, threshold: int = 3) -> list:
        """Sessions with >=threshold tool_failure events AND zero paired SubagentStop."""
        c = self._conn.cursor()
        c.execute("""
            SELECT session_id, COUNT(*) AS fail_count
            FROM events
            WHERE event_kind='tool_failure'
            GROUP BY session_id
            HAVING fail_count >= ?
        """, (threshold,))
        candidates = [(r["session_id"], r["fail_count"]) for r in c.fetchall() if r["session_id"]]

        out = []
        for session_id, fail_count in candidates:
            c2 = self._conn.cursor()
            c2.execute("""
                SELECT COUNT(*) AS clean_count FROM pairs
                WHERE session_id=? AND status='paired'
            """, (session_id,))
            clean_count = c2.fetchone()["clean_count"]
            if clean_count == 0:
                out.append({
                    "session_id": session_id,
                    "fail_count": fail_count,
                    "clean_pairs": clean_count,
                })
        return out

    # ------------------------------------------------------------------
    # Agent View JSON ingest (B3; optional)
    # ------------------------------------------------------------------
    def poll_agents_view(self) -> dict:
        """Run `claude agents --json`; return {session_id: {status, name, ...}}.
        Best-effort: returns empty dict on any failure."""
        try:
            result = subprocess.run(
                ["claude", "agents", "--json"],
                capture_output=True, text=True, timeout=10,
            )
            data = json.loads(result.stdout)
        except (FileNotFoundError, subprocess.TimeoutExpired,
                json.JSONDecodeError, ValueError, OSError):
            return {}
        out = {}
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                sid = item.get("sessionId") or item.get("session_id")
                if sid:
                    out[sid] = item
        return out

    # ------------------------------------------------------------------
    # Render layer (markdown + followups block)
    # ------------------------------------------------------------------
    def render_markdown(self, report: AnalyzerReport, out_path: Path) -> None:
        """Write canonical telemetry report markdown. ASCII-clean."""
        lines = []
        today = datetime.now().date().isoformat()
        lines.append("---")
        lines.append("categories: [wiki]")
        lines.append("type: report")
        lines.append("status: complete")
        lines.append(f"created: {today}")
        lines.append(f"updated: {today}")
        lines.append("tags: [topic/telemetry, topic/observability]")
        lines.append("related: [[hot]] [[knowledge-moc]]")
        lines.append("---")
        lines.append("")
        lines.append(f"# Telemetry Report -- {today}")
        lines.append("")
        lines.append(f"- Generated at: {report.generated_at}")
        lines.append(f"- Window: {report.window_days} days (since {report.window_start})")
        lines.append(
            f"- Test fixtures filtered: {report.filtered_count} records / "
            f"Real records: {report.real_count} / "
            f"Total: {report.total_count} (use --include-test-fixtures for raw view)"
        )
        lines.append("")
        lines.append("## Subagent Pair Health")
        ps = report.pair_summary
        lines.append(f"- Paired: {ps.get('paired', 0)}")
        lines.append(f"- Orphan stops (Stop with no paired Start): {ps.get('orphan_stop', 0)}")
        lines.append(f"- Hanging starts (Start with no paired Stop): {ps.get('hanging_start', 0)}")
        lines.append(f"- Session stops (main-session Stop-hook events; excluded from orphan pairing per D-T1): {ps.get('session_stop', 0)}")
        lines.append(f"- Total pairs: {ps.get('total', 0)}")
        lines.append(f"- Orphan rate: {ps.get('orphan_rate', 0.0)}")
        if ps.get("orphan_examples"):
            lines.append("")
            lines.append("Orphan examples:")
            for ex in ps["orphan_examples"]:
                lines.append(
                    f"  - pair_id={ex['pair_id']} agent_type={ex['agent_type']} "
                    f"duration_seconds={ex['duration_seconds']}"
                )
        lines.append("")
        lines.append("## Agent Duration Outliers")
        if not report.duration_by_agent_type:
            lines.append("(no paired durations in window)")
        else:
            lines.append("| agent_type | count | p50 | p95 | max | outlier |")
            lines.append("|---|---|---|---|---|---|")
            for at, d in sorted(report.duration_by_agent_type.items()):
                outlier = "YES" if d["outlier"] else "no"
                lines.append(
                    f"| {at} | {d['count']} | {d['p50']} | {d['p95']} | {d['max']} | {outlier} |"
                )
        lines.append("")
        lines.append("## Tool Failure Surface")
        if not report.failure_rate_by_tool:
            lines.append("(no tool failures in window)")
        else:
            lines.append("| tool_name | count | per_day |")
            lines.append("|---|---|---|")
            for tn, d in sorted(report.failure_rate_by_tool.items(),
                                key=lambda kv: kv[1]["count"], reverse=True):
                lines.append(f"| {tn} | {d['count']} | {d['per_day']} |")
        lines.append("")
        lines.append("## Failure Clusters (top 10)")
        if not report.failure_clusters:
            lines.append("(no failure clusters in window)")
        else:
            lines.append("| tool_name | error_class | count |")
            lines.append("|---|---|---|")
            for c in report.failure_clusters:
                lines.append(f"| {c['tool_name']} | {c['error_class']} | {c['count']} |")
        lines.append("")
        lines.append("## Session Failure Topology")
        if not report.session_failures:
            lines.append("(no high-failure sessions without clean pairs)")
        else:
            lines.append("| session_id | fail_count | clean_pairs |")
            lines.append("|---|---|---|")
            for s in report.session_failures:
                lines.append(f"| {s['session_id'][:8]}... | {s['fail_count']} | {s['clean_pairs']} |")
        lines.append("")
        # B3 -- Agent View mid-task crash detection (only present when --include-agents-view supplied)
        if report.agents_view_snapshot or report.mid_task_crashes:
            lines.append("## Mid-Task Crash Detection (Agent View)")
            if not report.mid_task_crashes:
                lines.append(f"(agents_view snapshot present: {len(report.agents_view_snapshot)} live sessions; no failed/stopped sessions without clean pair)")
            else:
                lines.append("| session_id | status | name | failures | cwd |")
                lines.append("|---|---|---|---|---|")
                for c in report.mid_task_crashes:
                    sid_short = c["session_id"][:8] + "..."
                    lines.append(
                        f"| {sid_short} | {c['status']} | {c['name']} | "
                        f"{c['failures_in_session']} | {c['cwd']} |"
                    )
            lines.append("")
        lines.append("## FOLLOWUPS:skills")
        lines.append(self.render_followups_block(report))
        lines.append("")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(lines), encoding="utf-8")

    def render_followups_block(self, report: AnalyzerReport) -> str:
        """Compact 1-5 line block for /retro FOLLOWUPS:skills consumption.

        Threshold rules (any trigger surfaces output):
          - orphan_count >= 1
          - any tool failure_rate count >= 3 in window
          - any agent_type with p95 > p50 * 3
        """
        triggers = []
        orphan = report.pair_summary.get("orphan_stop", 0)
        if orphan >= 1:
            triggers.append(f"orphan_count={orphan}")
        top_failure = None
        if report.failure_clusters:
            tf = report.failure_clusters[0]
            if tf["count"] >= 3:
                top_failure = f"{tf['tool_name']}::{tf['error_class']} x{tf['count']}"
            triggers.append(f"top_cluster: {tf['tool_name']}::{tf['error_class']} x{tf['count']}")
        outlier_agents = [
            f"{at}(p95={d['p95']}s)"
            for at, d in report.duration_by_agent_type.items()
            if d.get("outlier")
        ]
        if outlier_agents:
            triggers.append("outliers: " + ", ".join(outlier_agents))
        # B3 -- mid-task crash signal (only when agents_view ran)
        if report.mid_task_crashes:
            crashes = ", ".join(
                f"{c['session_id'][:8]}({c['status']})" for c in report.mid_task_crashes
            )
            triggers.append(f"mid_task_crashes: {crashes}")
        if not triggers:
            return "[telemetry] no signals above threshold in window"
        return "[telemetry] " + "; ".join(triggers)


def cli():
    p = argparse.ArgumentParser(description="Telemetry analyzer over .claude/state/ JSONL sinks")
    p.add_argument("--window", type=int, default=7,
                   help="Window in days (default 7)")
    p.add_argument("--rebuild", action="store_true",
                   help="Drop SQLite tables + full re-ingest from JSONL")
    p.add_argument("--json", action="store_true",
                   help="Emit JSON to stdout instead of human text")
    p.add_argument("--markdown", type=str, default="",
                   help="Write markdown report to this path")
    p.add_argument("--followups-block", action="store_true",
                   help="Emit just the compact /retro FOLLOWUPS line to stdout")
    p.add_argument("--include-agents-view", action="store_true",
                   help="Poll `claude agents --json` and include snapshot in report")
    p.add_argument("--include-test-fixtures", action="store_true",
                   help="Include synthetic test events in signals (default: excluded)")
    args = p.parse_args()

    with TelemetryAnalyzer(exclude_test_fixtures=not args.include_test_fixtures) as a:
        if args.rebuild:
            stats = a.rebuild()
        else:
            stats = a.ingest_new()
        report = a.analyze(window_days=args.window)
        if args.include_agents_view:
            report.agents_view_snapshot = a.poll_agents_view()
            report.mid_task_crashes = a.compute_mid_task_crashes(report.agents_view_snapshot)

        if args.markdown:
            a.render_markdown(report, Path(args.markdown))

        if args.followups_block:
            print(a.render_followups_block(report))
            return 0

        if args.json:
            payload = {
                "events_ingested": stats.events_ingested,
                "skipped_existing": stats.skipped_existing,
                "files_scanned": stats.files_scanned,
                "orphan_count": report.pair_summary.get("orphan_stop", 0),
                "real_count": report.real_count,
                "filtered_count": report.filtered_count,
                "total_count": report.total_count,
                "pair_summary": report.pair_summary,
                "duration_by_agent_type": report.duration_by_agent_type,
                "failure_rate_by_tool": report.failure_rate_by_tool,
                "failure_clusters": report.failure_clusters,
                "session_failures": report.session_failures,
                "agents_view": report.agents_view_snapshot,
                "mid_task_crashes": report.mid_task_crashes,
                "followups_block": a.render_followups_block(report),
            }
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(f"Telemetry analyzer report ({args.window}-day window)")
            print(f"  Events ingested this run: {stats.events_ingested}")
            print(f"  Files scanned: {stats.files_scanned}")
            print(f"  Real records: {report.real_count} / Test-fixtures filtered: {report.filtered_count} / Total: {report.total_count}")
            print(f"  Pair summary: paired={report.pair_summary.get('paired',0)} "
                  f"orphan_stop={report.pair_summary.get('orphan_stop',0)} "
                  f"hanging_start={report.pair_summary.get('hanging_start',0)}")
            print(f"  FOLLOWUPS: {a.render_followups_block(report)}")
    return 0


if __name__ == "__main__":
    sys.exit(cli())
