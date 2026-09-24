"""Deterministic job observation over the existing scheduler's UTC/time primitives.

This module never launches research, queries accounts, or delivers notifications.
Its SQLite journal retains missed opportunities and failed attempts. An OS lock
protects a whole run; a killed process releases that lock, while its durable
running row becomes an interrupted failure on the next observation.
"""
import contextlib
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time
import uuid

from .scheduler import eastern_datetime, eastern_to_utc, iso_z, parse_iso_z

UTC = dt.timezone.utc
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
SAFE_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,80}$")
SCHEDULED_SOURCES = {
    "osanwe-nightly-health": [".agents/scripts/checkall.py"],
    "osanwe-weekly-calibration": ["tools/factor-store.py", "tools/backtest-prediction.py", "tools/backtest-v2.py",
                                  "tools/backtest-offline.py", "tools/calibration-report.py", "tools/confidence-calibrator.py",
                                  "tools/verdict-backtest.py"],
    "osanwe-vault-reindex": ["tools/index-scope.mjs"],
}


def scheduled_sources(job):
    return ["tools/scheduled-job.py", "tools/fis/runtime_health.py", "tools/fis/scheduler.py"] + SCHEDULED_SOURCES[job]


def now_utc():
    return dt.datetime.now(UTC)


def file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_json(path, value):
    """Create dated evidence once; incomplete writes are not valid receipts."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


class OverlapError(RuntimeError):
    pass


def process_exists(pid):
    """Conservative process presence check; never signal Windows processes."""
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return ctypes.get_last_error() != 87
        try:
            code = wintypes.DWORD()
            return not kernel.GetExitCodeProcess(handle, ctypes.byref(code)) or code.value == 259
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


@contextlib.contextmanager
def job_lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    try:
        handle.seek(0, 2)
        if not handle.tell():
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise OverlapError("another observation or job is running") from exc
        yield
    finally:
        # Closing releases the OS lock even after child failure.
        handle.close()


def opportunities(start, end, hour=8, minute=0, weekdays=None):
    """Reuse the financial scheduler's Eastern DST conversions; no backfill run."""
    if end < start:
        raise ValueError("clock moved backwards")
    days = (eastern_datetime(end).date() - eastern_datetime(start).date()).days
    if days > 3660:
        raise ValueError("observation gap exceeds bounded calendar range")
    result = []
    day = eastern_datetime(start).date()
    for _ in range(days + 1):
        candidate, _ = eastern_to_utc(dt.datetime.combine(day, dt.time(hour, minute)))
        if start <= candidate <= end and (weekdays is None or day.weekday() in weekdays):
            result.append(candidate)
        day += dt.timedelta(days=1)
    return result


class Journal:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "runtime.sqlite", timeout=15)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS opportunities(
          job TEXT,slot TEXT,kind TEXT,status TEXT,run_id TEXT,started TEXT,ended TEXT,
          evidence TEXT,PRIMARY KEY(job,slot));
        CREATE TABLE IF NOT EXISTS events(
          seq INTEGER PRIMARY KEY AUTOINCREMENT,at TEXT,event TEXT,job TEXT,slot TEXT,
          detail TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS incidents(
          id TEXT PRIMARY KEY,job TEXT,code TEXT,state TEXT,opened TEXT,recovered TEXT);
        CREATE TABLE IF NOT EXISTS notices(
          seq INTEGER PRIMARY KEY AUTOINCREMENT,incident TEXT,at TEXT,outcome TEXT,
          evidence TEXT);
        """)

    def close(self):
        self.db.close()

    def event(self, at, event, job, slot=None, detail=None):
        self.db.execute("INSERT INTO events(at,event,job,slot,detail) VALUES(?,?,?,?,?)",
                        (iso_z(at), event, job, slot, json.dumps(detail or {}, sort_keys=True)))

    def reconcile(self, job, at, hour=8, minute=0, weekdays=None):
        key = "first_observed:" + job
        with self.db:
            row = self.db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
            if row is None:
                self.db.execute("INSERT INTO meta VALUES(?,?)", (key, iso_z(at)))
                start = at
                self.event(at, "observation_started", job,
                           detail={"earlier_history": "unobserved"})
            else:
                start = parse_iso_z(row[0])
            slots = opportunities(start, at, hour, minute, weekdays)
            latest = iso_z(slots[-1]) if slots else None
            for slot in slots:
                stamp = iso_z(slot)
                self.db.execute("INSERT OR IGNORE INTO opportunities(job,slot,kind,status) VALUES(?,?,?,?)",
                                (job, stamp, "scheduled", "due" if stamp == latest else "missed"))
            prior = self.db.execute("SELECT slot,status FROM opportunities WHERE job=? AND status IN ('due','running')",
                                    (job,)).fetchall()
            for item in prior:
                # This is called with the OS lock. A running row has no live owner.
                if item["status"] == "running":
                    self.db.execute("UPDATE opportunities SET status='failed',ended=? WHERE job=? AND slot=?",
                                    (iso_z(at), job, item["slot"]))
                    self.event(at, "interrupted", job, item["slot"], {"reason": "previous_owner_terminated"})
                elif item["slot"] != latest:
                    self.db.execute("UPDATE opportunities SET status='missed' WHERE job=? AND slot=?",
                                    (job, item["slot"]))
                    self.event(at, "missed", job, item["slot"], {"retrospective": True})
            return latest

    def begin(self, job, slot, at, kind="scheduled"):
        if not SAFE_NAME.fullmatch(job):
            raise ValueError("invalid job name")
        with self.db:
            if kind == "manual":
                slot = "manual:" + str(uuid.uuid4())
            self.db.execute("INSERT OR IGNORE INTO opportunities(job,slot,kind,status) VALUES(?,?,?,?)",
                            (job, slot, kind, "due"))
            run_id = uuid.uuid4().hex
            changed = self.db.execute("UPDATE opportunities SET status='running',run_id=?,started=? "
                                      "WHERE job=? AND slot=? AND status='due'",
                                      (run_id, iso_z(at), job, slot)).rowcount
            if not changed:
                self.event(at, "duplicate_refused", job, slot)
                return None
            self.event(at, "started", job, slot, {"run_id": run_id, "kind": kind})
            return {"job": job, "slot": slot, "run_id": run_id, "kind": kind}

    def reconcile_interval(self, job, at, seconds=120):
        """Record missed polling opportunities, admitting only the current one."""
        if seconds < 60:
            raise ValueError("polling interval below bounded scheduler scope")
        current = int(at.timestamp()) // seconds * seconds
        key = "last_interval_observed:" + job
        with self.db:
            previous = self.db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
            first = int(previous[0]) if previous else current
            if current < first:
                raise ValueError("clock moved backwards")
            # Keep older missed history as explicit counted ranges. Only the
            # rolling 30-day opportunities need individual rows for monitoring.
            cutoff = current - (30 * 86400 // seconds) * seconds
            if previous and first < cutoff:
                gap_start, gap_end = first + seconds, cutoff - seconds
                if gap_start <= gap_end:
                    self.event(at, "missed_interval_range", job, detail={
                        "first_slot": iso_z(dt.datetime.fromtimestamp(gap_start, UTC)),
                        "last_slot": iso_z(dt.datetime.fromtimestamp(gap_end, UTC)),
                        "count": (gap_end - gap_start) // seconds + 1,
                        "interval_seconds": seconds, "classification": "retrospective missed; not discarded"})
                first = cutoff
            latest = iso_z(dt.datetime.fromtimestamp(current, UTC))
            for stamp in range(first, current + 1, seconds):
                slot = iso_z(dt.datetime.fromtimestamp(stamp, UTC))
                self.db.execute("INSERT OR IGNORE INTO opportunities(job,slot,kind,status) VALUES(?,?,?,?)",
                                (job, slot, "scheduled", "due" if stamp == current else "missed"))
            self.db.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (key, str(current)))
            for row in self.db.execute("SELECT slot,status FROM opportunities WHERE job=? AND status IN ('due','running')", (job,)).fetchall():
                if row["status"] == "running":
                    self.db.execute("UPDATE opportunities SET status='failed',ended=? WHERE job=? AND slot=?", (iso_z(at), job, row["slot"]))
                    self.event(at, "interrupted", job, row["slot"], {"reason": "previous_owner_terminated"})
                elif row["slot"] != latest:
                    self.db.execute("UPDATE opportunities SET status='missed' WHERE job=? AND slot=?", (job, row["slot"]))
                    self.event(at, "missed", job, row["slot"], {"retrospective": True})
            return latest

    def finish(self, run, at, state, evidence):
        if state not in ("passed", "failed", "stale", "unavailable"):
            raise ValueError("invalid completion state")
        with self.db:
            changed = self.db.execute("UPDATE opportunities SET status=?,ended=?,evidence=? "
                                      "WHERE job=? AND slot=? AND run_id=? AND status='running'",
                                      (state, iso_z(at), str(evidence), run["job"], run["slot"], run["run_id"])).rowcount
            if changed != 1:
                raise ValueError("completion has no matching running attempt")
            self.event(at, state, run["job"], run["slot"], {"run_id": run["run_id"], "evidence": str(evidence)})

    def classify_manual_trigger(self, run_id, at):
        """Append a correction when a registered task was explicitly test-started."""
        row = self.db.execute("SELECT job,slot FROM opportunities WHERE run_id=?", (run_id,)).fetchone()
        if not row:
            raise ValueError("unknown registered task probe")
        existing = [json.loads(r[0]).get("run_id") for r in self.db.execute("SELECT detail FROM events WHERE event='manual_trigger_classified'")]
        if run_id not in existing:
            with self.db:
                self.event(at, "manual_trigger_classified", row["job"], row["slot"],
                           {"run_id": run_id, "classification": "manually started registration probe; not a scheduled opportunity",
                            "original_receipt": "preserved; this appended event corrects interpretation"})

    def incident(self, job, code, unhealthy, at):
        if not SAFE_NAME.fullmatch(job) or not SAFE_NAME.fullmatch(code):
            raise ValueError("incident identifiers must be nonpersonal machine codes")
        open_row = self.db.execute("SELECT id FROM incidents WHERE job=? AND code=? AND state='open'",
                                   (job, code)).fetchone()
        with self.db:
            if unhealthy and not open_row:
                ident = uuid.uuid4().hex
                self.db.execute("INSERT INTO incidents VALUES(?,?,?,?,?,NULL)",
                                (ident, job, code, "open", iso_z(at)))
                self.event(at, "incident_opened", job, detail={"incident": ident, "code": code})
                return {"incident": ident, "transition": "opened", "code": code,
                        "notification": "not_attempted"}
            if not unhealthy and open_row:
                self.db.execute("UPDATE incidents SET state='recovered',recovered=? WHERE id=?",
                                (iso_z(at), open_row[0]))
                self.event(at, "incident_recovered", job, detail={"incident": open_row[0], "code": code})
                return {"incident": open_row[0], "transition": "recovered", "code": code,
                        "notification": "not_attempted"}
        return None

    def notice(self, incident, outcome, at, evidence=None):
        if outcome not in ("attempted", "failed", "confirmed"):
            raise ValueError("invalid notification outcome")
        if not self.db.execute("SELECT 1 FROM incidents WHERE id=?", (incident,)).fetchone():
            raise ValueError("unknown incident")
        if outcome == "confirmed" and not evidence:
            raise ValueError("confirmation requires a provider delivery receipt reference")
        if evidence and not re.fullmatch(r"[A-Za-z0-9._:/-]{1,200}", evidence):
            raise ValueError("receipt reference must not contain message text or personal data")
        with self.db:
            self.db.execute("INSERT INTO notices(incident,at,outcome,evidence) VALUES(?,?,?,?)",
                            (incident, iso_z(at), outcome, evidence))

    def summary(self, job, at, grace_seconds=3600):
        cutoff = iso_z(at - dt.timedelta(days=30))
        rows = [dict(r) for r in self.db.execute(
            "SELECT * FROM opportunities WHERE job=? AND kind='scheduled' AND slot>=? ORDER BY slot",
            (job, cutoff))]
        corrections = {json.loads(r[0])["run_id"] for r in self.db.execute(
            "SELECT detail FROM events WHERE event='manual_trigger_classified' AND job=?", (job,))}
        corrected = sum(r["run_id"] in corrections for r in rows)
        rows = [r for r in rows if r["run_id"] not in corrections]
        counts = {s: sum(r["status"] == s for r in rows)
                  for s in ("due", "running", "passed", "failed", "stale", "unavailable", "missed")}
        timely = sum(r["status"] == "passed" and r["ended"] and
                     (parse_iso_z(r["ended"]) - parse_iso_z(r["slot"])).total_seconds() <= grace_seconds
                     for r in rows)
        sunday = any(r["status"] == "passed" and eastern_datetime(parse_iso_z(r["slot"])).weekday() == 6 for r in rows)
        completed = sum(r["status"] in ("passed", "failed", "stale", "unavailable") for r in rows)
        return {"window_days": 30, "scheduled_opportunities": len(rows), "counts": counts,
                "timely_completions": timely, "observed_completions": completed,
                "seven_cycle_pilot": "observed" if completed >= 7 and sunday else "pending",
                "successful_sunday_observed": sunday, "scope": "local observations only",
                "manual_trigger_corrections": corrected,
                "limits": "No offline-host observation or notification delivery is inferred."}


def artifact_state(path, started_at, max_age_seconds=None, json_schema=None):
    path = Path(path)
    if not path.is_file():
        return {"state": "failed", "reason": "required_artifact_missing"}
    stat = path.stat()
    if stat.st_size == 0:
        return {"state": "failed", "reason": "required_artifact_empty"}
    modified = dt.datetime.fromtimestamp(stat.st_mtime, UTC)
    if modified < started_at - dt.timedelta(seconds=2):
        return {"state": "stale", "reason": "artifact_predates_run"}
    if max_age_seconds is not None and (now_utc() - modified).total_seconds() > max_age_seconds:
        return {"state": "stale", "reason": "artifact_expired"}
    if json_schema:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if value.get("schema") != json_schema or value.get("state") != "passed":
                return {"state": "failed", "reason": "artifact_contract_failed"}
        except (ValueError, AttributeError):
            return {"state": "failed", "reason": "artifact_malformed"}
    return {"state": "passed", "reason": "fresh_artifact_present"}


def bounded_process(command, cwd, timeout, env=None, maintenance=None, maintenance_interval=30):
    """Capture no child output in persistent receipts; errors are typed codes."""
    if timeout <= 0 or maintenance_interval <= 0:
        raise ValueError("process bounds must be positive")
    started = now_utc()
    deadline = time.monotonic() + timeout
    with subprocess.Popen(command, cwd=str(cwd), env=env, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, creationflags=NO_WINDOW,
                          start_new_session=os.name != "nt") as process:
        failure = None
        try:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(command, timeout)
                try:
                    code = process.wait(timeout=min(remaining, maintenance_interval) if maintenance else remaining)
                    break
                except subprocess.TimeoutExpired:
                    if time.monotonic() >= deadline:
                        raise
                    if maintenance and process.poll() is None:
                        try:
                            maintenance(process.pid)
                        except Exception:
                            failure = "process-maintenance-failed"
                            raise subprocess.TimeoutExpired(command, timeout)
            return {"state": "passed" if code == 0 else "failed", "exit_code": code,
                    "reason": "process_completed" if code == 0 else "process_nonzero",
                    "started_at": iso_z(started), "ended_at": iso_z(now_utc())}
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               creationflags=NO_WINDOW, timeout=15)
            else:
                import signal
                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=15)
            return {"state": "failed", "exit_code": process.returncode, "reason": failure or "timeout",
                    "started_at": iso_z(started), "ended_at": iso_z(now_utc())}


def readiness(receipt, at, ttl_seconds=90000):
    """Readiness expires even if the previous check passed."""
    try:
        age = (at - parse_iso_z(receipt["verified_at"])).total_seconds()
    except (KeyError, TypeError, ValueError):
        return "unavailable"
    if age < 0:
        return "unavailable"
    return "host-unobserved" if age > ttl_seconds else receipt["state"]


def validation_outcome(process, report_path, started_at):
    """A completed validation may report stale/unavailable without crashing."""
    if process.get("reason") == "timeout":
        return {"state": "failed", "reason": "validation-computation-timeout"}
    fresh = artifact_state(report_path, started_at)
    if fresh["state"] != "passed":
        return {"state": fresh["state"], "reason": "validation-" + fresh["reason"].replace("_", "-")}
    try:
        report = json.loads(Path(report_path).read_text(encoding="utf-8"))
        state = report.get("state")
        if report.get("schema") != "osanwe.validation/1" or state not in ("passed", "failed", "stale", "unavailable"):
            raise ValueError("invalid validation receipt")
        expected_exit = {"passed": 0, "failed": 1, "stale": 1, "unavailable": 2}[state]
        if process.get("exit_code") != expected_exit:
            raise ValueError("validation exit and receipt disagree")
        return {"state": state, "reason": "validation-" + state}
    except (OSError, ValueError, AttributeError):
        return {"state": "failed", "reason": "validation-receipt-invalid"}


def completion_marker(path, contract):
    """Read only a bounded tail; return no financial values or log text."""
    if contract != "score-outcomes-summary/1":
        return {"state": "unavailable", "reason": "unknown-completion-contract"}
    try:
        with Path(path).open("rb") as handle:
            handle.seek(max(0, Path(path).stat().st_size - 4096))
            lines = handle.read(4096).decode("ascii", errors="replace").strip().splitlines()
        number = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
        pattern = r"Rollback: realized_at_3mo=(?:0|[1-9]\d*) armed=(?:True|False) gap=(?:None|" + number + r") fired=(?:True|False)"
        valid = bool(lines and re.fullmatch(pattern, lines[-1].strip()))
        return {"state": "passed" if valid else "failed", "reason": "typed-completion-present" if valid else "typed-completion-missing-or-malformed"}
    except OSError:
        return {"state": "unavailable", "reason": "completion-artifact-unreadable"}


def inventory(root):
    """Read only explicit scheduler metadata. No principals, usernames or task XML."""
    if os.name != "nt":
        return {"state": "unavailable", "reason": "windows_scheduler_unavailable", "tasks": []}
    script = r"""
    $ErrorActionPreference = 'Stop'
    $calendarService = New-Object -ComObject Schedule.Service
    $calendarService.Connect()
    $rows = @(Get-ScheduledTask | Where-Object TaskName -like 'osanwe-*' | ForEach-Object {
      $i = $_ | Get-ScheduledTaskInfo
      $monthly = @()
      if ($_.TaskName -eq 'osanwe-monthly-usage-ledger') {
        $nativeTriggers = $calendarService.GetFolder($_.TaskPath).GetTask($_.TaskName).Definition.Triggers
        $monthly = @($nativeTriggers | Where-Object Type -eq 4 | ForEach-Object {
          [pscustomobject]@{type=$_.Type;days_of_month=$_.DaysOfMonth;months_of_year=$_.MonthsOfYear;last_day=$_.RunOnLastDayOfMonth}
        })
      }
      [pscustomobject]@{name=$_.TaskName; state=$_.State.ToString();
        monthly_calendar=$monthly;
        actions=@($_.Actions | ForEach-Object {[pscustomobject]@{execute=$_.Execute;arguments=$_.Arguments;cwd=$_.WorkingDirectory}});
        last_run=$i.LastRunTime.ToUniversalTime().ToString('o'); last_result=$i.LastTaskResult;
        missed=$i.NumberOfMissedRuns; next_run=$i.NextRunTime.ToUniversalTime().ToString('o');
        triggers=@($_.Triggers | ForEach-Object {[pscustomobject]@{type=$_.CimClass.CimClassName;
          start=$_.StartBoundary;enabled=$_.Enabled;days_of_week=$_.DaysOfWeek;days_interval=$_.DaysInterval;
          weeks_interval=$_.WeeksInterval;repetition=$_.Repetition.Interval;repetition_duration=$_.Repetition.Duration}});
        settings=[pscustomobject]@{start_when_available=$_.Settings.StartWhenAvailable;wake_to_run=$_.Settings.WakeToRun;
          multiple_instances=$_.Settings.MultipleInstances;timeout=$_.Settings.ExecutionTimeLimit;
          run_only_if_idle=$_.Settings.RunOnlyIfIdle}}
    })
    ConvertTo-Json -InputObject $rows -Depth 5 -Compress
    """
    try:
        proc = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                              capture_output=True, text=True, timeout=30, creationflags=NO_WINDOW)
        if proc.returncode:
            return {"state": "unavailable", "reason": "scheduler_query_failed", "tasks": []}
        rows = json.loads(proc.stdout)
        if not isinstance(rows, list):
            raise ValueError("expected scheduler list")
        # Identity is only read for reviewed executables/scripts in the manifest;
        # arbitrary new task actions are not a new filesystem read authority.
        import shutil
        manifest = json.loads((Path(root) / "config/scheduled-jobs.json").read_text(encoding="utf-8"))
        approved = {j["name"]: j.get("registered_action") for j in manifest["jobs"]}
        for row in rows:
            expected = approved.get(row["name"])
            if expected and row["actions"] == [expected]:
                candidate = shutil.which(expected["execute"])
                if candidate and Path(candidate).is_file():
                    row["executable_identity"] = {"resolved_path": candidate, "sha256": file_sha(candidate)}
        return {"state": "passed", "verified_at": iso_z(now_utc()), "tasks": rows}
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return {"state": "unavailable", "reason": "scheduler_query_unavailable", "tasks": []}


def reconcile_inventory(manifest, observed, root):
    findings = []
    if observed["state"] != "passed":
        return [{"job": "scheduler", "state": "unavailable", "code": "inventory-unavailable"}]
    jobs = manifest["jobs"]
    names = [job["name"] for job in jobs]
    if len(names) != len(set(names)):
        findings.append({"job": "scheduler", "state": "failed", "code": "duplicate-manifest-jobs"})
    actual = {task["name"]: task for task in observed["tasks"]}
    for task in observed["tasks"]:
        if task["name"] not in names:
            findings.append({"job": task["name"], "state": "failed", "code": "unmanifested-task"})
    for job in jobs:
        name = job["name"]
        if job.get("registration") != "registered":
            continue
        task = actual.get(name)
        if not task:
            findings.append({"job": name, "state": "unavailable", "code": "registered-task-missing"})
            continue
        expected = job.get("registered_action")
        if expected and task["actions"] != [expected]:
            findings.append({"job": name, "state": "failed", "code": "registered-action-drift"})
        if job.get("schedule_contract") is not None and task.get("triggers") != job["schedule_contract"]:
            findings.append({"job": name, "state": "failed", "code": "registered-trigger-drift"})
        if job.get("monthly_contract") is not None and task.get("monthly_calendar") != job["monthly_contract"]:
            findings.append({"job": name, "state": "failed", "code": "registered-monthly-drift"})
        if job.get("executable_identity") is not None and task.get("executable_identity") != job["executable_identity"]:
            findings.append({"job": name, "state": "stale", "code": "registered-executable-changed"})
        for key, value in job.get("desired_settings", {}).items():
            if task.get("settings", {}).get(key) != value:
                findings.append({"job": name, "state": "failed", "code": "registered-settings-drift"})
                break
        if task.get("state") == "Running":
            findings.append({"job": name, "state": "unavailable", "code": "current-job-running"})
        elif task["last_result"] != 0:
            findings.append({"job": name, "state": "failed", "code": "last-process-failed"})
        # Windows reports a cumulative counter, including intentional idle-gated
        # polls. Preserve it in inventory; a fresh valid output can recover.
        output = job.get("output_contract")
        if output and output.get("glob"):
            paths = list(Path(root).glob(output["glob"]))
            latest = max(paths, key=lambda p: p.stat().st_mtime) if paths else None
            if latest is None or not latest.is_file() or latest.stat().st_size < output.get("min_bytes", 1):
                findings.append({"job": name, "state": "failed", "code": "required-artifact-missing"})
            elif now_utc().timestamp() - latest.stat().st_mtime > output["max_age_seconds"]:
                findings.append({"job": name, "state": "stale", "code": "required-artifact-stale"})
            elif output.get("schema"):
                try:
                    receipt = json.loads(latest.read_text(encoding="utf-8"))
                    if receipt.get("schema") != output["schema"] or receipt.get("state") != "passed":
                        findings.append({"job": name, "state": "failed", "code": "artifact-result-not-passed"})
                    elif output["schema"] == "osanwe.scheduled-job/1":
                        # The current owner supplies paths, never the receipt.
                        # Historical success cannot certify subsequently edited
                        # runtime code, a different job or a changed interpreter.
                        expected_sources = scheduled_sources(name) if name in SCHEDULED_SOURCES else []
                        claimed = receipt.get("code_identity")
                        if (not expected_sources or not isinstance(claimed, dict) or set(claimed) != set(expected_sources) or
                            receipt.get("attempt", {}).get("job") != name or receipt.get("code_unchanged_during_run") is not True):
                            findings.append({"job": name, "state": "failed", "code": "artifact-code-identity-invalid"})
                        elif (any(claimed[path] != file_sha(Path(root) / path) for path in expected_sources) or
                              receipt.get("executable_sha256") != task.get("executable_identity", {}).get("sha256")):
                            findings.append({"job": name, "state": "stale", "code": "artifact-code-identity-stale"})
                except (ValueError, AttributeError):
                    findings.append({"job": name, "state": "failed", "code": "artifact-result-malformed"})
                except OSError:
                    findings.append({"job": name, "state": "unavailable", "code": "artifact-code-identity-unavailable"})
            if latest is not None and output.get("completion_contract"):
                marker = completion_marker(latest, output["completion_contract"])
                if marker["state"] != "passed":
                    findings.append({"job": name, "state": marker["state"], "code": marker["reason"]})
        else:
            findings.append({"job": name, "state": "unavailable", "code": "output-contract-unverified"})
    return findings
