#!/usr/bin/env python3
"""
F11 orchestrator: cascade-aware management of .claude/state/auto-commit-disabled.

Background. The F11 mechanism (a presence-flag file at .claude/state/auto-commit-disabled
checked by .claude/hooks/auto-commit.sh) suppresses the PostToolUse auto-commit
hook so a multi-phase skill can land an atomic commit at the end without
mid-phase commits leaking out. The convention is: each skill SETs F11 in its
Phase C and CLEARs in its Phase K (single set-point per invocation).

The DEVIATION pattern -- F11-RE-SET-PER-INVOCATION (named 2026-05-06 from the
2026-05-04 sandbox-derived Phase 2 cascade and the 2026-05-05 cohort sweep) --
is what happens when a *cascade* of skills (parent triggering child triggering
grandchild) treats each skill as an isolated F11 atom. Each child sets +
clears its own F11 window, leaving inter-child intervals where PostToolUse
auto-commit can fire on stray edits. Mechanically the vault never corrupts,
but the intended atomicity boundary is lost: 5 ingest commits + 1 retro commit
become 6 commits where the cascade was supposed to be one logical transaction.

Prevention rule. The cascade parent acquires F11 ONCE. Children invoked within
the cascade detect the pre-existing flag and SKIP their own set+clear (cascade
role = 'child'). The parent clears F11 ONCE on cascade exit. The library here
encodes that rule via a context manager.

Usage:
    from tools.lib.f11_orchestrator import f11_session

    # Top-level (most common):
    with f11_session(reason="my-skill-cascade") as f11:
        f11.checkpoint("phase-c-edit-start")
        # ... edits ...
        f11.commit_boundary("phase-j-commit-1")
        # ... more edits within cascade ...
        f11.commit_boundary("phase-j-commit-2")
        # F11 retained across commit boundaries; cleared on context exit

    # Cascade child (rare; only for skills explicitly invoked under a parent):
    with f11_session(reason="child-skill", cascade_role="child") as f11:
        # Detects parent F11; does not set; does not clear; does not collide
        ...

CLI usage:
    python tools/lib/f11_orchestrator.py status        # report current flag state
    python tools/lib/f11_orchestrator.py set --reason X
    python tools/lib/f11_orchestrator.py clear --reason X
    python tools/lib/f11_orchestrator.py detect        # scan today's history for anti-patterns

Anti-pattern detector. Walks .claude/state/f11-history-<date>.jsonl and flags:
  - set_without_clear     more sets than clears (in-flight or orphan)
  - clear_without_set     more clears than sets (manual rm without prior touch)
  - rapid_re_set          3+ set events within a 30-minute window (the DEVIATION pattern)

Telemetry. Every event (set, child_join, checkpoint, commit_boundary, clear,
collision, halt_keep_flag) is appended to .claude/state/f11-history-<date>.jsonl
as a single-line JSON object with ts + event + reason + cascade_role + data.
This lets future skills correlate F11 timing against commit history forensically.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", os.getcwd()))
F11_PATH = VAULT_ROOT / ".claude" / "state" / "auto-commit-disabled"


def _history_path(today: date | None = None) -> Path:
    d = (today or date.today()).isoformat()
    return VAULT_ROOT / ".claude" / "state" / f"f11-history-{d}.jsonl"


def _log_event(event: str, reason: str, cascade_role: str, data: dict | None = None):
    """Append one telemetry line; best-effort (never raises)."""
    try:
        hp = _history_path()
        hp.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now().isoformat(),
            "event": event,
            "reason": reason,
            "cascade_role": cascade_role,
            "data": data or {},
        }
        with hp.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


class F11CollisionError(RuntimeError):
    """Raised when entering an F11 session and the flag is already set by a
    NON-child role. Indicates an in-flight skill or orphan flag."""


class F11Session:
    """Context-managed F11 lifecycle with cascade awareness.

    cascade_role:
        leaf    (default) Independent invocation. Set on enter; clear on exit.
                 Collide-HALT if flag already present.
        parent  Top of a cascade. Set on enter; clear on exit. The parent is
                 expected to invoke child skills inside this context manager.
        child   Within a cascade. Detect parent flag; do NOT set; do NOT
                 clear. If parent flag absent, behave like leaf (set + clear
                 our own); this lets the same skill body work under cascade
                 OR standalone.
    """

    def __init__(self, reason: str, cascade_role: str = "leaf"):
        if cascade_role not in ("leaf", "parent", "child"):
            raise ValueError(f"cascade_role must be leaf|parent|child; got {cascade_role!r}")
        self.reason = reason
        self.cascade_role = cascade_role
        self.set_at: datetime | None = None
        self.we_own_flag: bool = False
        self.checkpoints: list[dict] = []

    def __enter__(self) -> "F11Session":
        existed_pre = F11_PATH.exists()
        if existed_pre and self.cascade_role in ("leaf", "parent"):
            _log_event("collision", self.reason, self.cascade_role,
                       {"flag_already_set": True})
            raise F11CollisionError(
                f"F11 already set ({F11_PATH}); another skill in-flight or "
                f"orphan flag from prior crash. Inspect or rm to recover."
            )
        if existed_pre and self.cascade_role == "child":
            _log_event("child_join", self.reason, self.cascade_role,
                       {"parent_flag_present": True})
            self.we_own_flag = False
            return self
        # We own the flag (leaf, parent, or child-with-no-parent-flag)
        F11_PATH.parent.mkdir(parents=True, exist_ok=True)
        F11_PATH.touch()
        self.set_at = datetime.now()
        self.we_own_flag = True
        effective_role = "leaf" if (self.cascade_role == "child" and not existed_pre) else self.cascade_role
        _log_event("set", self.reason, effective_role,
                   {"path": str(F11_PATH)})
        return self

    def __exit__(self, exc_type, exc, tb):
        if not self.we_own_flag:
            _log_event("child_leave", self.reason, self.cascade_role,
                       {"exc": str(exc) if exc else None})
            return False
        if exc is not None:
            # F.halt: keep flag set; clean recovery is user's responsibility.
            _log_event("halt_keep_flag", self.reason, self.cascade_role,
                       {"exc_type": exc_type.__name__ if exc_type else None,
                        "exc": str(exc) if exc else None})
            return False
        try:
            F11_PATH.unlink()
        except (OSError, FileNotFoundError):
            pass
        duration = (datetime.now() - self.set_at).total_seconds() if self.set_at else 0
        _log_event("clear", self.reason, self.cascade_role,
                   {"checkpoints": len(self.checkpoints),
                    "duration_sec": round(duration, 2)})
        return False

    def checkpoint(self, label: str) -> None:
        """Mark progress within the F11 window. Telemetry only; flag retained."""
        ts = datetime.now().isoformat()
        self.checkpoints.append({"label": label, "ts": ts})
        _log_event("checkpoint", self.reason, self.cascade_role, {"label": label})

    def commit_boundary(self, label: str = "commit") -> None:
        """Mark a git commit boundary. F11 RETAINED across; cascade-correct.
        This is the core abstraction: a cascade can have N commit boundaries
        but a single F11 set-clear pair around the entire cascade."""
        _log_event("commit_boundary", self.reason, self.cascade_role,
                   {"label": label})


@contextmanager
def f11_session(reason: str, cascade_role: str = "leaf"):
    """Convenience context-manager wrapper. See F11Session docstring."""
    s = F11Session(reason, cascade_role)
    s.__enter__()
    try:
        yield s
    except BaseException as e:
        s.__exit__(type(e), e, e.__traceback__)
        raise
    else:
        s.__exit__(None, None, None)


# === Anti-pattern detector ===

def detect_anti_patterns(history_path: Path | None = None,
                         rapid_window_minutes: int = 30,
                         rapid_threshold: int = 3) -> list[dict]:
    """Scan a history file for known F11 anti-patterns.

    Anti-patterns:
      set_without_clear: open sets exceed clears (in-flight or orphan)
      clear_without_set: clears exceed sets (manual rm without prior touch)
      rapid_re_set:      rapid_threshold+ set events in any rapid_window minutes
                         (the F11-RE-SET-PER-INVOCATION cascade pattern)
    """
    findings = []
    hp = history_path or _history_path()
    if not hp.exists():
        return findings
    events = []
    try:
        for line in hp.read_text(encoding="utf-8").splitlines():
            try:
                events.append(json.loads(line))
            except (json.JSONDecodeError, ValueError):
                continue
    except OSError:
        return findings
    if not events:
        return findings

    set_events = [e for e in events if e.get("event") == "set"]
    clear_events = [e for e in events if e.get("event") == "clear"]
    halts = [e for e in events if e.get("event") == "halt_keep_flag"]

    # Pattern 1: imbalance (sets outnumber clears, accounting for halts which keep flag)
    open_sets = len(set_events) - len(clear_events) - len(halts)
    if open_sets > 1:
        findings.append({
            "pattern": "set_without_clear",
            "open_sets": open_sets,
            "set_count": len(set_events),
            "clear_count": len(clear_events),
            "halt_count": len(halts),
            "rule": "Each F11 set must be followed by clear (or halt_keep_flag for crash). open_sets>1 indicates orphan flags.",
        })

    # Pattern 2: clear without prior set (less common; manual rm)
    if len(clear_events) > len(set_events):
        findings.append({
            "pattern": "clear_without_set",
            "set_count": len(set_events),
            "clear_count": len(clear_events),
            "rule": "Clear without prior set indicates manual rm; bypasses telemetry.",
        })

    # Pattern 3: rapid re-set (the DEVIATION cascade pattern)
    set_times = []
    for e in set_events:
        try:
            set_times.append(datetime.fromisoformat(e["ts"]))
        except (ValueError, KeyError):
            continue
    set_times.sort()
    if len(set_times) >= rapid_threshold:
        window = timedelta(minutes=rapid_window_minutes)
        for i, base in enumerate(set_times):
            in_window = sum(1 for t in set_times[i:] if t - base <= window)
            if in_window >= rapid_threshold:
                findings.append({
                    "pattern": "rapid_re_set",
                    "named_pattern": "F11-RE-SET-PER-INVOCATION",
                    "window_start": base.isoformat(),
                    "set_events_in_window": in_window,
                    "window_minutes": rapid_window_minutes,
                    "rule": (f"{in_window} F11 set events within {rapid_window_minutes} minutes; "
                             "symptom of the F11-RE-SET-PER-INVOCATION cascade pattern; "
                             "use cascade_role='parent' on the orchestrator and "
                             "cascade_role='child' on inner skills to hold one F11 across cascade."),
                })
                break

    return findings


# === CLI ===

def cli_main(argv=None):
    parser = argparse.ArgumentParser(description="F11 orchestrator (cascade-aware)")
    parser.add_argument("action", choices=["set", "clear", "status", "detect"])
    parser.add_argument("--reason", default="cli")
    parser.add_argument("--cascade-role", default="leaf",
                        choices=["leaf", "parent", "child"])
    parser.add_argument("--history-date", default=None,
                        help="ISO date to scan for detect (default: today)")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)

    if args.action == "status":
        out = {
            "f11_path": str(F11_PATH),
            "f11_set": F11_PATH.exists(),
            "history_path": str(_history_path()),
            "history_exists": _history_path().exists(),
        }
        if args.json_output:
            print(json.dumps(out, indent=2))
        else:
            print(f"F11 path:    {out['f11_path']}")
            print(f"F11 set:     {out['f11_set']}")
            print(f"History:     {out['history_path']}")
            print(f"History on:  {out['history_exists']}")
        return 0

    if args.action == "set":
        try:
            s = F11Session(args.reason, args.cascade_role)
            s.__enter__()
            if args.json_output:
                print(json.dumps({"set": True, "we_own": s.we_own_flag,
                                  "reason": args.reason, "cascade_role": args.cascade_role}, indent=2))
            else:
                print(f"F11 set: reason={args.reason} cascade_role={args.cascade_role} "
                      f"we_own={s.we_own_flag}")
        except F11CollisionError as e:
            print(f"COLLISION: {e}", file=sys.stderr)
            return 2
        return 0

    if args.action == "clear":
        if F11_PATH.exists():
            F11_PATH.unlink()
            _log_event("clear", args.reason, args.cascade_role, {"via": "cli"})
            print("F11 cleared")
        else:
            print("F11 not set; nothing to clear")
        return 0

    if args.action == "detect":
        target_date = None
        if args.history_date:
            try:
                target_date = date.fromisoformat(args.history_date)
            except ValueError:
                print(f"Invalid --history-date: {args.history_date}", file=sys.stderr)
                return 2
        hp = _history_path(target_date)
        findings = detect_anti_patterns(hp)
        if args.json_output:
            print(json.dumps({"history": str(hp), "findings": findings}, indent=2))
        else:
            if not findings:
                print(f"No anti-patterns detected in {hp.name}")
            else:
                print(f"{len(findings)} anti-pattern(s) in {hp.name}:")
                for f in findings:
                    print(f"  - {f.get('pattern', '?')}: {f.get('rule', '')}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(cli_main())
