#!/usr/bin/env python3
"""
open-loops.py -- READ-ONLY ranked top-5 open-loop digest at SessionStart.

TENFOLD T2 (X52 rev-7). The vault's keystone break: artifacts carry trigger
fields (FOLLOWUPS blocks, ESCALATION_DATEs, review dates, proposal TTLs,
prediction horizons) that nothing reads. This digest is the first organ that
reads them. It is deliberately minimal:

  - READ-ONLY: never writes, never pushes, never mutates state.
  - BUILD-gated (roadmap doctrine a): promotion to any push/alert lane only
    after 30 days of observed consumption (promotion review ~2026-08-03;
    consumption proxy = digest items acted on / mentioned in sessions-log).
  - NON-FATAL (X77): every scanner class is individually try/except-wrapped;
    the whole main is wrapped; ALWAYS exits 0. Registered as its OWN
    SessionStart hook entry so it can never abort session-start.sh's chain.
  - Windows python: C:/ paths only (invoked as `python C:/...` from
    settings.json; /c/ msys paths are unreadable here).

Scanned loop classes (weight -- higher = more decision-urgent):
  EXEC-OR-DECLINE  3.0  Calendar/decisions/execute-or-decline.md PENDING rows
                        past ESCALATION_DATE (the X01/X04 forcing function).
  PREDICTION       2.5  spark *.meta.json prediction_scoring.unresolved > 0;
                        plus scorer-run staleness (>8d since last
                        score-outcomes run in .claude/state/score-outcomes-runs.log).
  COMMITMENT       2.0  daily-note ## Commitments unchecked items past
                        ESCALATION_DATE (same source the session-start stale
                        scan reads; here they compete in one ranked view).
  REVIEW-DATE      1.5  decision-log 'review date YYYY-MM-DD' lines past due.
  FOLLOWUPS        1.2  FOLLOWUPS:skills items in the LATEST briefing when
                        that briefing is >48h old (unconsumed coordination).
  PROPOSAL-TTL     1.0  wiki/maintenance/proposals/*.md older than 14d with
                        non-terminal status (staged-but-never-ratified decay).

Always-emitted line (not ranked -- this IS the T4 silent-failure detector,
sequencing M6): BRIEFING FRESHNESS -- latest briefing date vs the last
weekday. Market holidays are not modeled; a 1-weekday gap on a holiday is an
accepted false positive, the detector's job is catching multi-day silence
(T4 doctrine: Task Scheduler fallback after 2 silent failures counted here).

X75 written-vs-delivered distinction: if a machine-trigger fire is recorded
(briefing meta.json "alerts_fired" field, wired at T9) without a matching
receipt line in .claude/state/alerts-delivered.log (appended by the T4 push
lane), the freshness line reports "alert fired but delivery UNCONFIRMED".
A briefing that published while its push died silently must not read green.
Both records are absent today; the check stays dormant until T9/T4 wire it.

Score = class_weight * min(days_overdue, 60). Top 5 emitted.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

VAULT = Path("/path/to/vault")
DAILY_DIR = VAULT / "Calendar" / "daily"
BRIEFINGS_DIR = VAULT / "Calendar" / "decisions" / "briefings"
DECISION_LOG = VAULT / "Calendar" / "decisions" / "decision-log.md"
EXEC_LEDGER = VAULT / "Calendar" / "decisions" / "execute-or-decline.md"
PROPOSALS_DIR = VAULT / "wiki" / "maintenance" / "proposals"
SPARKS_DIR = VAULT / "wiki" / "research" / "sparks"
SCORER_LOG = VAULT / ".claude" / "state" / "score-outcomes-runs.log"
ALERTS_LOG = VAULT / ".claude" / "state" / "alerts-delivered.log"

DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
ESC_RE = re.compile(r"ESCALATION_DATE:\s*(\d{4}-\d{2}-\d{2})")
PROPOSAL_TTL_DAYS = 14
SCORER_STALE_DAYS = 8
TOP_N = 5
CAP_DAYS = 60


def parse_date(s: str) -> date | None:
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None


def scan_exec_or_decline(today: date) -> list[tuple[float, int, str]]:
    """PENDING rows past ESCALATION_DATE in the execute-or-decline ledger.

    Row protocol amended 2026-08-13 (ledger is append-only end to end): a row is
    closed by APPENDING a RESOLUTION row that carries the same ID and a terminal
    Status (EXECUTED/DECLINED/SUPERSEDED); the original PENDING row is never
    edited. A PENDING row therefore counts as open only while no row anywhere in
    the file shares its ID with a terminal Status."""
    out = []
    if not EXEC_LEDGER.exists():
        return out
    lines = EXEC_LEDGER.read_text(encoding="utf-8", errors="ignore").splitlines()
    resolved: set[str] = set()
    for line in lines:
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        # Status is matched as a bare uppercase token; tolerate bold/punctuation
        # (this ledger already uses **bold** inside Resolution cells).
        if len(cells) >= 5 and cells[4].strip("*").rstrip(".").upper() in (
                "EXECUTED", "DECLINED", "SUPERSEDED"):
            resolved.add(cells[0])
    seen_pending: set[str] = set()
    for line in lines:
        if not line.strip().startswith("|") or "PENDING" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        # MALFORMED ROWS ARE SURFACED, NEVER DROPPED (red team 2026-08-14).
        # The ledger's own ORDER-string convention mandates pipes INSIDE the
        # Action cell ("ORDER: BUY X | LIMIT $y | ..."), which splits a 6-cell
        # row into 11+, moves the escalation date off cells[3], and previously
        # made the row vanish from the highest-urgency loop class entirely --
        # silently, and precisely on the money-adjacent rows
        # that are queued to receive ORDER strings. Escape literal pipes as
        # &#124; in ledger cells; until then a wrong-shaped row still escalates.
        if len(cells) != 6:
            ident = cells[0] if cells else "?"
            if ident not in resolved:
                out.append((3.0 * CAP_DAYS, CAP_DAYS,
                            f"EXEC-OR-DECLINE (MALFORMED ROW, unparseable date -- "
                            f"escape literal pipes as &#124;): {ident} "
                            f"{' '.join(cells[1:3])[:80]}"))
            continue
        if cells[0] in resolved:
            continue
        # ID uniqueness became load-bearing when closure moved to appended
        # RESOLUTION rows: one terminal row closes EVERY PENDING row sharing
        # its ID. A duplicate is therefore a silent-close hazard, not cosmetic.
        if cells[0] in seen_pending:
            out.append((3.0 * CAP_DAYS, CAP_DAYS,
                        f"EXEC-OR-DECLINE (DUPLICATE ID {cells[0]} -- a single "
                        f"RESOLUTION row would close both): {cells[1][:70]}"))
        seen_pending.add(cells[0])
        # ledger convention: column 4 (0-indexed 3) is ESCALATION_DATE
        m = DATE_RE.search(cells[3]) if len(cells) > 3 else None
        esc = parse_date(m.group(1)) if m else None
        if esc is None or esc > today:
            continue
        days = (today - esc).days
        action = cells[1][:110] if len(cells) > 1 else line[:110]
        out.append((3.0 * min(days if days > 0 else 1, CAP_DAYS), days,
                    f"EXEC-OR-DECLINE ({days}d past escalation): {action}"))
    return out


def scan_commitments(today: date) -> list[tuple[float, int, str]]:
    out = []
    if not DAILY_DIR.exists():
        return out
    cutoff = today - timedelta(days=365)
    for p in sorted(DAILY_DIR.glob("*.md")):
        stem = parse_date(p.stem)
        if stem is None or stem < cutoff:
            continue
        in_commit = False
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            s = line.strip()
            if s == "## Commitments":
                in_commit = True
                continue
            if in_commit and s.startswith("## "):
                in_commit = False
                continue
            if in_commit and s.startswith("- [ ]"):
                m = ESC_RE.search(line)
                if not m:
                    continue
                esc = parse_date(m.group(1))
                if esc is None or esc >= today:
                    continue
                days = (today - esc).days
                body = re.sub(r"<!--.*?-->", "", s.split("(TRIGGER:")[0])
                body = body.lstrip("- [ ]").strip()[:110]
                out.append((2.0 * min(days, CAP_DAYS), days,
                            f"COMMITMENT ({days}d overdue): {body}"))
    return out


def scan_review_dates(today: date) -> list[tuple[float, int, str]]:
    out = []
    if not DECISION_LOG.exists():
        return out
    heading = ""
    for line in DECISION_LOG.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("### "):
            heading = line[4:].strip()[:80]
            continue
        m = re.search(r"[Rr]eview date:?\s*(\d{4}-\d{2}-\d{2})", line)
        if not m:
            continue
        rd = parse_date(m.group(1))
        if rd is None or rd >= today:
            continue
        days = (today - rd).days
        out.append((1.5 * min(days, CAP_DAYS), days,
                    f"REVIEW-DATE ({days}d past): {heading}"))
    return out


def latest_briefing() -> tuple[date | None, Path | None]:
    latest, latest_p = None, None
    if BRIEFINGS_DIR.exists():
        for p in BRIEFINGS_DIR.glob("briefing-*.md"):
            m = DATE_RE.search(p.name)
            d = parse_date(m.group(1)) if m else None
            if d and (latest is None or d > latest):
                latest, latest_p = d, p
    return latest, latest_p


def scan_followups(today: date) -> list[tuple[float, int, str]]:
    out = []
    bdate, bpath = latest_briefing()
    if bpath is None or bdate is None or (today - bdate).days < 2:
        return out
    days = (today - bdate).days
    text = bpath.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"<!-- FOLLOWUPS:skills -->\n(.*?)<!-- /FOLLOWUPS:skills -->",
                  text, re.DOTALL)
    if not m:
        return out
    for line in m.group(1).splitlines():
        s = line.strip()
        if s.startswith("- "):
            out.append((1.2 * min(days, CAP_DAYS), days,
                        f"FOLLOWUPS ({bdate}, {days}d unconsumed): {s[2:][:110]}"))
    return out


def scan_proposals(today: date) -> list[tuple[float, int, str]]:
    out = []
    if not PROPOSALS_DIR.exists():
        return out
    terminal = {"done", "complete", "deprecated", "dropped", "superseded"}
    for p in PROPOSALS_DIR.glob("*.md"):
        text = p.read_text(encoding="utf-8", errors="ignore")[:2000]
        sm = re.search(r"^status:\s*(\S+)", text, re.MULTILINE)
        if sm and sm.group(1).lower() in terminal:
            continue
        dm = re.search(r"^created:\s*(\d{4}-\d{2}-\d{2})", text, re.MULTILINE)
        created = parse_date(dm.group(1)) if dm else None
        if created is None:
            m = DATE_RE.search(p.name)
            created = parse_date(m.group(1)) if m else None
        if created is None:
            continue
        age = (today - created).days
        if age <= PROPOSAL_TTL_DAYS:
            continue
        out.append((1.0 * min(age, CAP_DAYS), age,
                    f"PROPOSAL-TTL ({age}d staged, TTL {PROPOSAL_TTL_DAYS}d): {p.stem}"))
    return out


def scan_predictions(today: date) -> list[tuple[float, int, str]]:
    out = []
    if SPARKS_DIR.exists():
        for p in SPARKS_DIR.glob("*.meta.json"):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            ps = d.get("prediction_scoring") or {}
            unresolved = ps.get("unresolved", 0)
            if unresolved:
                out.append((2.5 * 10, 10,
                            f"PREDICTION: {p.stem} has {unresolved} unresolved matured prediction(s)"))
    try:
        if SCORER_LOG.exists():
            mtime = date.fromtimestamp(SCORER_LOG.stat().st_mtime)
            age = (today - mtime).days
            if age > SCORER_STALE_DAYS:
                out.append((2.5 * min(age, CAP_DAYS), age,
                            f"PREDICTION: score-outcomes last ran {age}d ago (>{SCORER_STALE_DAYS}d; Sunday scorer may be dead)"))
    except OSError:
        pass
    return out


def scan_scheduled_worker(today: date) -> list[tuple[float, int, str]]:
    """W11 (GATE-B 2026-08-17): surface overnight relay-worker output waiting
    for consumption + parked escalations + degraded MCP servers + the LANE
    SILENT heartbeat. Reads pending.json (written by relay-batch scheduled
    mode) and the run log's mtime. Log ABSENT = task not yet registered
    (staged state) -> quiet by design; the Vault Codex row says Staged."""
    out: list[tuple[float, int, str]] = []
    state_dir = VAULT / ".claude" / "state"
    pending = state_dir / "scheduled-worker-pending.json"
    if pending.is_file():
        try:
            p = json.loads(pending.read_text(encoding="utf-8"))
            ts = parse_date(str(p.get("ts", ""))[:10])
            days = max((today - ts).days, 1) if ts else 1
            n_d = int(p.get("new_distillates") or 0)
            n_p = len(p.get("parked") or [])
            down = p.get("servers_down") or []
            div = [c for c in (p.get("consistency") or [])
                   if c.get("result") == "divergence"]
            if n_d or n_p:
                msg = (f"SCHEDULED-WORKER: {n_d} distillate(s) await "
                       f"consumption, {n_p} parked (batch {p.get('batch')})")
                if down:
                    msg += f"; servers DOWN: {', '.join(down)}"
                if div:
                    msg += f"; {len(div)} consistency divergence(s)"
                out.append((2.0 * min(days, CAP_DAYS), days, msg))
            elif down:
                out.append((1.0 * min(days, CAP_DAYS), days,
                            f"SCHEDULED-WORKER: servers DOWN overnight: "
                            f"{', '.join(down)} (keys missing at machine "
                            f"scope? see register-local-worker-task.ps1)"))
        except Exception:
            pass
    run_log = state_dir / "local-worker-runs.log"
    if run_log.is_file():
        import time as _t
        silent_days = int((_t.time() - run_log.stat().st_mtime) // 86400)
        if silent_days >= 2:
            out.append((2.5 * min(silent_days, CAP_DAYS), silent_days,
                        f"SCHEDULED-WORKER: LANE SILENT -- "
                        f"local-worker-runs.log last write {silent_days}d ago "
                        f"(task dead, unregistered, or machine asleep at "
                        f"03:30?)"))
    return out


def briefing_freshness_line(today: date) -> str:
    """Always emitted. The T4 silent-failure detector + X75 delivery check."""
    bdate, bpath = latest_briefing()
    if bdate is None:
        return "BRIEFING FRESHNESS: no briefings found"
    # last weekday strictly before or equal to today
    d = today
    while d.weekday() >= 5:  # Sat=5 Sun=6
        d -= timedelta(days=1)
    missed = 0
    cur = d
    while cur > bdate:
        if cur.weekday() < 5:
            missed += 1
        cur -= timedelta(days=1)
    status = "OK" if missed == 0 else f"STALE -- {missed} weekday(s) unbriefed (holidays not modeled)"
    line = f"BRIEFING FRESHNESS: latest {bdate}; {status}"
    # X75: briefing-WRITTEN vs alert-DELIVERED (dormant until T9 wires alerts_fired)
    try:
        meta = bpath.with_name(bpath.stem + "-meta.json") if bpath else None
        if meta and meta.exists():
            md = json.loads(meta.read_text(encoding="utf-8"))
            fired = md.get("alerts_fired") or []
            if fired:
                delivered = ALERTS_LOG.read_text(encoding="utf-8", errors="ignore") if ALERTS_LOG.exists() else ""
                unconfirmed = [a for a in fired if str(a.get("id", a)) not in delivered]
                if unconfirmed:
                    line += f"; ALERT FIRED but delivery UNCONFIRMED ({len(unconfirmed)})"
                else:
                    line += "; alerts delivered"
    except Exception:
        pass
    return line


def main() -> int:
    today = date.today()
    findings: list[tuple[float, int, str]] = []
    for scanner in (scan_exec_or_decline, scan_commitments, scan_review_dates,
                    scan_followups, scan_proposals, scan_predictions):
        try:
            findings.extend(scanner(today))
        except Exception:
            continue  # X77: a broken class never kills the digest
    findings.sort(key=lambda t: t[0], reverse=True)
    lines = [f"[open-loops digest (read-only, top {TOP_N} of {len(findings)}; X52 BUILD-gated, no push)]"]
    for _, _, text in findings[:TOP_N]:
        lines.append(f"- {text}")
    if not findings:
        lines.append("- no open loops past escalation (clean)")
    try:
        lines.append(briefing_freshness_line(today))
    except Exception:
        pass
    # W11: scheduled-worker lines are ALWAYS-ON footers (like briefing
    # freshness), not ranked findings -- a fresh overnight distillate must
    # surface every morning without displacing (or being displaced by) the
    # escalation-ranked EOD rows.
    try:
        for _, _, text in scan_scheduled_worker(today):
            lines.append(f"- {text}")
    except Exception:
        pass
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # non-fatal by contract (X77)
