#!/usr/bin/env python3
"""Audit Phase B dispatch verifiability (v5 wave-aware) for the /corpus pipeline.

Reconciles four sources of evidence per wave:
  1. dispatch-<wave>-<ts>.json   -- orchestrator promise (per wave)
  2. batch-<batch_id>-started.txt -- sub-agent start sentinels
  3. batch-<batch_id>-<ts>.json   -- sub-agent return manifests
  4. _meta blocks in each extraction JSON

Reports PASS/FAIL per wave and overall.

Workspace resolution (in order of precedence):
  1. --workspace <path>
  2. CORPUS_WORKSPACE environment variable
  3. Current working directory if it contains .corpus.json

Usage:
  python audit_run.py --wave N [--workspace <path>]
  python audit_run.py --all
  python audit_run.py --phase-b-complete

Exit codes:
  0 = PASS (all checks consistent)
  1 = FAIL (inconsistencies found)
  2 = infrastructure failure or invalid args

This is the v5 wave-aware audit. The legacy non-wave audit-run.py (with
hyphen) coexists for backwards compatibility with v3/v4 single-dispatch runs.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# Assigned in main() after workspace resolution.
WORKSPACE: Path | None = None
LOGS: Path | None = None
EXTRACTIONS: Path | None = None


def resolve_workspace(arg_workspace: str | None) -> Path:
    """Resolve workspace via --workspace arg, CORPUS_WORKSPACE env, or cwd-with-.corpus.json."""
    if arg_workspace:
        ws = Path(arg_workspace)
    elif env_ws := os.environ.get("CORPUS_WORKSPACE"):
        ws = Path(env_ws)
    elif (Path.cwd() / ".corpus.json").exists():
        ws = Path.cwd()
    else:
        print(
            "ERROR: workspace not resolved. Provide --workspace <path>, "
            "set CORPUS_WORKSPACE env var, or run from a directory containing .corpus.json.",
            file=sys.stderr,
        )
        sys.exit(2)
    if not ws.is_dir():
        print(f"ERROR: workspace {ws} is not a directory", file=sys.stderr)
        sys.exit(2)
    return ws.resolve()


def is_acceptable_model(model_id: str) -> bool:
    """Accept Sonnet 4.6+ or Opus 4.6+. Reject Haiku and pre-4.6 Sonnet/Opus."""
    if not model_id:
        return False
    m = re.match(r"claude-(sonnet|opus|haiku)-(\d+)-(\d+)", model_id)
    if not m:
        return False
    family = m.group(1)
    major = int(m.group(2))
    minor = int(m.group(3))
    if family == "haiku":
        return False
    if family == "sonnet" and (major, minor) < (4, 6):
        return False
    if family == "opus" and (major, minor) < (4, 6):
        return False
    return True


def load_dispatch_logs(wave: int) -> list[dict]:
    """Load all dispatch-<wave>-*.json logs for a given wave."""
    out: list[dict] = []
    for f in sorted(LOGS.glob(f"dispatch-{wave}-*.json")):
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return out


def load_started_sentinels(wave: int) -> list[dict]:
    """Load all batch-<id>-started.txt sentinels whose batch_id starts with wave_<N>_."""
    out: list[dict] = []
    for f in LOGS.glob(f"batch-wave_{wave}_*-started.txt"):
        d: dict[str, Any] = {}
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            if ":" not in line:
                continue
            k, _, v = line.partition(":")
            k = k.strip()
            v = v.strip()
            if k == "assigned_doc_ids":
                try:
                    d[k] = json.loads(v)
                except json.JSONDecodeError:
                    d[k] = []
            else:
                d[k] = v
        d["__filename__"] = f.name
        out.append(d)
    return out


def load_manifests(wave: int) -> list[dict]:
    """Load all batch manifests for the given wave (excluding started sentinels)."""
    out: list[dict] = []
    for f in LOGS.glob(f"batch-wave_{wave}_*-*.json"):
        if f.name.endswith("-started.txt"):
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        data["__filename__"] = f.name
        out.append(data)
    return out


def load_extraction_metas(wave: int) -> dict[str, dict]:
    """Return doc_id -> _meta block, filtered to extractions for this wave."""
    out: dict[str, dict] = {}
    if not EXTRACTIONS.exists():
        return out
    for f in EXTRACTIONS.glob("*.json"):
        try:
            ext = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(ext, dict):
            continue
        meta = ext.get("_meta", {})
        if not isinstance(meta, dict):
            continue
        if meta.get("wave") == wave:
            out[ext.get("doc_id", f.stem)] = meta
    return out


def audit_wave(wave: int) -> tuple[bool, list[str]]:
    """Run all four-source cross-checks for one wave. Returns (ok, issue_lines)."""
    issues: list[str] = []
    dispatches = load_dispatch_logs(wave)
    starts = load_started_sentinels(wave)
    manifests = load_manifests(wave)
    metas = load_extraction_metas(wave)

    if not dispatches:
        issues.append(f"  - No dispatch log found for wave {wave}")
    if not starts:
        issues.append(f"  - No batch-started sentinels found for wave {wave}")
    if not manifests:
        issues.append(f"  - No batch manifests found for wave {wave}")

    # Check models in started sentinels
    for s in starts:
        m = s.get("model_self_id", "")
        if not is_acceptable_model(m):
            issues.append(
                f"  - UNACCEPTABLE MODEL in started sentinel "
                f"{s.get('__filename__', '?')}: {m!r}"
            )

    # Check models in manifests
    for mf in manifests:
        m = mf.get("model_self_id", "")
        if not is_acceptable_model(m):
            issues.append(
                f"  - UNACCEPTABLE MODEL in manifest "
                f"{mf.get('__filename__', '?')} (batch={mf.get('batch_id')}): {m!r}"
            )

    # Check models in extraction _meta blocks
    for doc_id, meta in metas.items():
        m = meta.get("model_self_id", "")
        if not is_acceptable_model(m):
            issues.append(
                f"  - UNACCEPTABLE MODEL in extraction {doc_id}: {m!r}"
            )

    # Check expected vs actual doc_ids (against dispatch logs)
    if dispatches:
        expected: set[str] = set()
        for d in dispatches:
            assignments = d.get("batch_assignments", {}) or {}
            for batch, ids in assignments.items():
                if isinstance(ids, list):
                    expected.update(ids)
        actual = set(metas.keys())
        # fail_doc_ids legitimately have no extraction
        legit_fail: set[str] = set()
        for mf in manifests:
            for d in mf.get("fail_doc_ids", []) or []:
                legit_fail.add(d)
        missing = (expected - actual) - legit_fail
        extra = actual - expected
        if missing:
            issues.append(
                f"  - Wave {wave}: expected but missing extractions: {sorted(missing)}"
            )
        if extra:
            issues.append(
                f"  - Wave {wave}: extracted but not in any dispatch: {sorted(extra)}"
            )

    # Check sub_agent_run_id consistency between started and manifests
    starts_by_batch = {s.get("batch_id"): s.get("sub_agent_run_id") for s in starts}
    for mf in manifests:
        bid = mf.get("batch_id")
        if bid and starts_by_batch.get(bid) != mf.get("sub_agent_run_id"):
            issues.append(
                f"  - sub_agent_run_id mismatch for batch {bid}: "
                f"started={starts_by_batch.get(bid)} != "
                f"manifest={mf.get('sub_agent_run_id')}"
            )

    # Check _meta sub_agent_run_id matches some manifest
    manifests_run_ids = {m.get("sub_agent_run_id") for m in manifests if m.get("sub_agent_run_id")}
    for doc_id, meta in metas.items():
        runid = meta.get("sub_agent_run_id")
        if runid and runid not in manifests_run_ids:
            issues.append(
                f"  - Extraction {doc_id} has run_id {runid} not in any manifest"
            )

    # Wave-completion sentinel
    wave_complete = LOGS / f"wave-{wave}-complete.json"
    if not wave_complete.exists():
        issues.append(
            f"  - wave-{wave}-complete.json sentinel missing "
            f"(orchestrator did not formally close the wave)"
        )

    return (len(issues) == 0, issues)


def discover_completed_waves() -> list[int]:
    """Return wave numbers with wave-N-complete.json present, sorted ascending."""
    out: list[int] = []
    for f in LOGS.glob("wave-*-complete.json"):
        m = re.match(r"wave-(\d+)-complete\.json", f.name)
        if m:
            try:
                out.append(int(m.group(1)))
            except ValueError:
                continue
    return sorted(set(out))


def discover_dispatched_waves() -> list[int]:
    """Return wave numbers that have any dispatch-N-*.json log, sorted ascending."""
    out: list[int] = []
    for f in LOGS.glob("dispatch-*-*.json"):
        m = re.match(r"dispatch-(\d+)-.*\.json", f.name)
        if m:
            try:
                out.append(int(m.group(1)))
            except ValueError:
                continue
    return sorted(set(out))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Audit /corpus v5 wave-based sub-agent dispatch verifiability."
    )
    ap.add_argument("--wave", type=int, help="Audit a specific wave number")
    ap.add_argument("--all", action="store_true", help="Audit every wave found in logs")
    ap.add_argument(
        "--phase-b-complete",
        action="store_true",
        help="Audit every wave AND require phase-b-complete.json sentinel",
    )
    ap.add_argument(
        "--workspace",
        help="Corpus workspace path (overrides CORPUS_WORKSPACE env and cwd-with-.corpus.json autodetect)",
    )
    args = ap.parse_args(argv)

    global WORKSPACE, LOGS, EXTRACTIONS
    WORKSPACE = resolve_workspace(args.workspace)
    LOGS = WORKSPACE / "logs" / "runs"
    EXTRACTIONS = WORKSPACE / "20-extractions"

    if not LOGS.exists():
        print(f"ERROR: logs/runs/ not found at {LOGS}", file=sys.stderr)
        return 2
    if not EXTRACTIONS.exists():
        print(f"ERROR: 20-extractions/ not found at {EXTRACTIONS}", file=sys.stderr)
        return 2

    if args.wave is not None:
        ok, issues = audit_wave(args.wave)
        status = "PASS" if ok else "FAIL"
        print(f"Wave {args.wave}: {status}")
        for line in issues:
            print(line)
        return 0 if ok else 1

    if args.all or args.phase_b_complete:
        # Discover from any wave we have evidence of (dispatched or completed)
        waves = sorted(set(discover_completed_waves() + discover_dispatched_waves()))
        if not waves:
            print(
                "ERROR: no wave-*-complete.json or dispatch-*-*.json files found. "
                "Either no /corpus extract has been run under v5, or evidence is missing.",
                file=sys.stderr,
            )
            return 2
        all_ok = True
        for w in waves:
            ok, issues = audit_wave(w)
            status = "PASS" if ok else "FAIL"
            print(f"Wave {w}: {status}")
            for line in issues:
                print(line)
            all_ok = all_ok and ok

        if args.phase_b_complete:
            pbc = LOGS / "phase-b-complete.json"
            if not pbc.exists():
                print()
                print("phase-b-complete.json MISSING -- orchestrator did not formally close Phase B")
                all_ok = False

        print()
        print(f"OVERALL: {'PASS' if all_ok else 'FAIL'} across {len(waves)} wave(s)")
        return 0 if all_ok else 1

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
