#!/usr/bin/env python3
"""
test-consolidator.py -- named test cases for tools/consolidator.py.

Covers: canonical ingest (sessions + decisions), decision-tag threshold
above/below, telemetry cluster pattern, retro theme threshold, skill
failure-rate threshold, playbook section rendering, hot.md digest <4KB,
dry-run no-write, run writes playbooks, idempotent re-run, and a real-vault
integration smoke test.

Usage:
  python tools/test-consolidator.py                 # run all
  python tools/test-consolidator.py --test <name>   # focused single test

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

import consolidator as cz  # noqa: E402


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _make_vault():
    """Create a tmp vault skeleton. Returns (tmp, decisions_dir, daily_dir, state_dir)."""
    tmp = Path(tempfile.mkdtemp(prefix="consolidate-test-"))
    dec_dir = tmp / "Calendar" / "decisions"
    daily_dir = tmp / "Calendar" / "daily"
    state_dir = tmp / "state"
    for d in (dec_dir, daily_dir, state_dir):
        d.mkdir(parents=True, exist_ok=True)
    return tmp, dec_dir, daily_dir, state_dir


def _new(tmp, state_dir, since=None):
    return cz.Consolidator(vault_root=tmp, since=since, state_dir=state_dir)


def _write(path: Path, text: str):
    path.write_text(text, encoding="utf-8")


def _write_jsonl(path: Path, records):
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


SESSIONS_HEADER = (
    "---\ncategories: [decisions]\n---\n\n# Session Log\n\n"
    "| Date | Topic | Outcome | Files Created/Updated |\n"
    "|------|-------|---------|----------------------|\n")
DECISION_HEADER = (
    "---\ncategories: [decisions]\n---\n\n# Decision Log\n\n"
    "| Date | Domain | Decision | Rationale | Status |\n"
    "|------|--------|----------|-----------|--------|\n")


# ----------------------------------------------------------------------
# 1. ingest sessions canonical
# ----------------------------------------------------------------------
def test_ingest_sessions_canonical():
    tmp, dec, daily, state = _make_vault()
    try:
        rows = (
            "| 2026-05-01 | Topic A | Domain: investing. Did stuff. | files |\n"
            "| 2026-05-02 | Topic B | Domain: meta/skill-infrastructure. More. | files |\n")
        _write(dec / "sessions-log.md", SESSIONS_HEADER + rows)
        c = _new(tmp, state)
        sessions = c.ingest_sessions()
        assert len(sessions) == 2, f"expected 2 sessions, got {len(sessions)}"
        assert sessions[0]["date"] == "2026-05-01"
        assert sessions[0]["domain"] == "investing", sessions[0]["domain"]
        assert "meta" in sessions[1]["domain"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------
# 2. ingest decisions canonical
# ----------------------------------------------------------------------
def test_ingest_decisions_canonical():
    tmp, dec, daily, state = _make_vault()
    try:
        rows = (
            "| 2026-05-01 | investing | Buy X | reason | active |\n"
            "| 2026-05-02 | career | Apply Y | reason | ratified |\n"
            "| 2026-05-03 | investing | Trim Z | reason | active |\n")
        _write(dec / "decision-log.md", DECISION_HEADER + rows)
        c = _new(tmp, state)
        decisions = c.ingest_decisions()
        assert len(decisions) == 3, f"expected 3 decisions, got {len(decisions)}"
        assert decisions[0]["domain"] == "investing"
        assert decisions[1]["domain"] == "career"
        assert decisions[0]["status"] == "active"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------
# 3. decision-tag threshold ABOVE (>=3 same domain -> pattern)
# ----------------------------------------------------------------------
def test_decision_tag_threshold_above():
    tmp, dec, daily, state = _make_vault()
    try:
        rows = (
            "| 2026-05-01 | investing | Buy X | r | active |\n"
            "| 2026-05-02 | investing | Trim Y | r | active |\n"
            "| 2026-05-03 | investing | Hold Z | r | active |\n")
        _write(dec / "decision-log.md", DECISION_HEADER + rows)
        c = _new(tmp, state)
        pats = [p for p in c.identify_patterns() if p.pattern_type == "decision_tag"]
        keys = [p.key for p in pats]
        assert any("investing" in k for k in keys), f"expected investing decision_tag, got {keys}"
        inv = [p for p in pats if "investing" in p.key][0]
        assert inv.count == 3
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------
# 4. decision-tag threshold BELOW (<3 -> no pattern)
# ----------------------------------------------------------------------
def test_decision_tag_threshold_below():
    tmp, dec, daily, state = _make_vault()
    try:
        rows = (
            "| 2026-05-01 | investing | Buy X | r | active |\n"
            "| 2026-05-02 | investing | Trim Y | r | active |\n")
        _write(dec / "decision-log.md", DECISION_HEADER + rows)
        c = _new(tmp, state)
        pats = [p for p in c.identify_patterns()
                if p.pattern_type == "decision_tag" and "investing" in p.key]
        assert pats == [], f"expected no investing decision_tag (only 2), got {pats}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------
# 5. telemetry cluster pattern (>=5 -> pattern; 4 -> none)
# ----------------------------------------------------------------------
def test_telemetry_cluster_pattern():
    tmp, dec, daily, state = _make_vault()
    try:
        cwd = os.environ.get("VAULT_ROOT", os.getcwd())
        recs = [{"ts": "2026-05-20T01:00:0%d.000" % i, "tool": "Bash",
                 "error": "Exit code 2\nvalidator block",
                 "session_id": "real-1", "cwd": cwd} for i in range(5)]
        _write_jsonl(state / "failures-2026-05-20.jsonl", recs)
        c = _new(tmp, state, since="2026-04-01")
        pats = [p for p in c.identify_patterns() if p.pattern_type == "telemetry_cluster"]
        assert len(pats) == 1, f"expected 1 cluster pattern, got {len(pats)}"
        assert pats[0].count == 5
        assert "Bash" in pats[0].key and "Exit_code_2" in pats[0].key

        # Below threshold: 4 failures -> no cluster pattern
        tmp2, dec2, daily2, state2 = _make_vault()
        try:
            recs4 = recs[:4]
            _write_jsonl(state2 / "failures-2026-05-20.jsonl", recs4)
            c2 = _new(tmp2, state2, since="2026-04-01")
            pats2 = [p for p in c2.identify_patterns() if p.pattern_type == "telemetry_cluster"]
            assert pats2 == [], f"expected no cluster (4<5), got {pats2}"
        finally:
            shutil.rmtree(tmp2, ignore_errors=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------
# 6. retro theme threshold (token in >=3 distinct sessions -> pattern)
# ----------------------------------------------------------------------
def test_retro_theme_threshold():
    tmp, dec, daily, state = _make_vault()
    try:
        rows = (
            "| 2026-05-01 | A | Domain: investing. Methodology learnings: frobnication discipline observed. Follow-ups: none | f |\n"
            "| 2026-05-02 | B | Domain: investing. Methodology learnings: frobnication recurs again. Follow-ups: none | f |\n"
            "| 2026-05-03 | C | Domain: investing. Methodology learnings: frobnication third time. Follow-ups: none | f |\n")
        _write(dec / "sessions-log.md", SESSIONS_HEADER + rows)
        c = _new(tmp, state)
        pats = [p for p in c.identify_patterns() if p.pattern_type == "retro_theme"]
        keys = [p.key for p in pats]
        assert any("frobnication" in k for k in keys), f"expected frobnication theme, got {keys}"
        fro = [p for p in pats if "frobnication" in p.key][0]
        assert fro.count == 3
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------
# 7. skill failure-rate threshold (>=30% with min events -> pattern)
# ----------------------------------------------------------------------
def test_skill_failure_rate_threshold():
    tmp, dec, daily, state = _make_vault()
    try:
        cwd = os.environ.get("VAULT_ROOT", os.getcwd())
        recs = [
            # Explore: 3 dispatches, 2 unpaired (failed), 1 paired -> 66.7% fail
            {"ts": "2026-05-20T01:00:00.000", "event": "start", "tool_use_id": "ex-1", "agent_type": "Explore", "session_id": "s", "cwd": cwd},
            {"ts": "2026-05-20T01:00:01.000", "event": "stop", "tool_use_id": "ex-1", "agent_type": "Explore", "session_id": "s", "cwd": cwd},
            {"ts": "2026-05-20T01:00:02.000", "event": "start", "tool_use_id": "ex-2", "agent_type": "Explore", "session_id": "s", "cwd": cwd},
            {"ts": "2026-05-20T01:00:03.000", "event": "start", "tool_use_id": "ex-3", "agent_type": "Explore", "session_id": "s", "cwd": cwd},
            # Plan: 4 dispatches, 1 unpaired -> 25% fail (below threshold)
            {"ts": "2026-05-20T01:00:04.000", "event": "start", "tool_use_id": "pl-1", "agent_type": "Plan", "session_id": "s", "cwd": cwd},
            {"ts": "2026-05-20T01:00:05.000", "event": "stop", "tool_use_id": "pl-1", "agent_type": "Plan", "session_id": "s", "cwd": cwd},
            {"ts": "2026-05-20T01:00:06.000", "event": "start", "tool_use_id": "pl-2", "agent_type": "Plan", "session_id": "s", "cwd": cwd},
            {"ts": "2026-05-20T01:00:07.000", "event": "stop", "tool_use_id": "pl-2", "agent_type": "Plan", "session_id": "s", "cwd": cwd},
            {"ts": "2026-05-20T01:00:08.000", "event": "start", "tool_use_id": "pl-3", "agent_type": "Plan", "session_id": "s", "cwd": cwd},
            {"ts": "2026-05-20T01:00:09.000", "event": "stop", "tool_use_id": "pl-3", "agent_type": "Plan", "session_id": "s", "cwd": cwd},
            {"ts": "2026-05-20T01:00:10.000", "event": "start", "tool_use_id": "pl-4", "agent_type": "Plan", "session_id": "s", "cwd": cwd},
        ]
        _write_jsonl(state / "subagent-telemetry-2026-05-20.jsonl", recs)
        c = _new(tmp, state, since="2026-04-01")
        pats = [p for p in c.identify_patterns() if p.pattern_type == "skill_failure_rate"]
        keys = [p.key for p in pats]
        assert any("Explore" in k for k in keys), f"expected Explore failure-rate pattern, got {keys}"
        assert not any("Plan" in k for k in keys), f"Plan (25%) should be below threshold, got {keys}"
        ex = [p for p in pats if "Explore" in p.key][0]
        assert ex.metric >= 0.30
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------
# 8. render_playbook has required sections + frontmatter
# ----------------------------------------------------------------------
def test_render_playbook_has_required_sections():
    tmp, dec, daily, state = _make_vault()
    try:
        c = _new(tmp, state)
        p = cz.Pattern(pattern_type="decision_tag", key="investing decisions",
                       count=5, metric=5.0, evidence=["2026-05-01: Buy X"],
                       threshold_desc=">= 3 decisions")
        md = c.render_playbook(p, sibling_slugs=["other-thing"], today="2026-05-24")
        for section in ("## Pattern", "## Evidence", "## Recommendation", "## Related"):
            assert section in md, f"missing {section}"
        assert md.startswith("---"), "missing frontmatter open"
        assert "categories: [wiki]" in md
        assert "created: 2026-05-24" in md
        assert "[[hot]]" in md
        assert all(ord(ch) < 128 for ch in md), "playbook must be ASCII-clean"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------
# 9. hot.md digest under 4KB + dated + links
# ----------------------------------------------------------------------
def test_hot_md_digest_under_4kb():
    tmp, dec, daily, state = _make_vault()
    try:
        c = _new(tmp, state, since="2026-04-01")
        pats = [cz.Pattern("decision_tag", f"domain-{i} decisions", 4, 4.0,
                           ["ev"], ">=3") for i in range(20)]
        slugs = c._unique_slugs(pats)
        digest = c.render_hot_md_digest(pats, slugs, today="2026-05-24")
        assert len(digest.encode("utf-8")) <= cz.DIGEST_MAX_BYTES, \
            f"digest {len(digest.encode('utf-8'))} bytes exceeds {cz.DIGEST_MAX_BYTES}"
        assert "Consolidation Digest -- 2026-05-24" in digest
        assert "[[" in digest
        assert all(ord(ch) < 128 for ch in digest), "digest must be ASCII-clean"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------
# 10. dry-run writes nothing
# ----------------------------------------------------------------------
def test_dry_run_writes_nothing():
    tmp, dec, daily, state = _make_vault()
    try:
        rows = (
            "| 2026-05-01 | investing | Buy X | r | active |\n"
            "| 2026-05-02 | investing | Trim Y | r | active |\n"
            "| 2026-05-03 | investing | Hold Z | r | active |\n")
        _write(dec / "decision-log.md", DECISION_HEADER + rows)
        c = _new(tmp, state)
        report = c.run(max_playbooks=8, dry_run=True)
        assert report.written == [], "dry-run must write nothing"
        pb = tmp / "wiki" / "playbooks"
        files = list(pb.glob("*.md")) if pb.exists() else []
        assert files == [], f"dry-run left files: {files}"
        assert len(report.patterns) >= 1, "should still identify patterns in dry-run"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------
# 11. run writes playbooks (one per pattern)
# ----------------------------------------------------------------------
def test_run_writes_playbooks():
    tmp, dec, daily, state = _make_vault()
    try:
        rows = (
            "| 2026-05-01 | investing | Buy X | r | active |\n"
            "| 2026-05-02 | investing | Trim Y | r | active |\n"
            "| 2026-05-03 | investing | Hold Z | r | active |\n"
            "| 2026-05-04 | career | Apply A | r | active |\n"
            "| 2026-05-05 | career | Apply B | r | active |\n"
            "| 2026-05-06 | career | Apply C | r | active |\n")
        _write(dec / "decision-log.md", DECISION_HEADER + rows)
        c = _new(tmp, state)
        report = c.run(max_playbooks=8, dry_run=False)
        assert len(report.written) == len(report.patterns), \
            f"{len(report.written)} files != {len(report.patterns)} patterns"
        assert len(report.written) >= 2, "expected investing + career playbooks"
        for w in report.written:
            assert Path(w).exists()
            body = Path(w).read_text(encoding="utf-8")
            assert "## Pattern" in body and "## Related" in body
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------
# 12. idempotent re-run (deterministic render + identical files)
# ----------------------------------------------------------------------
def test_idempotent_rerun():
    tmp, dec, daily, state = _make_vault()
    try:
        rows = (
            "| 2026-05-01 | investing | Buy X | r | active |\n"
            "| 2026-05-02 | investing | Trim Y | r | active |\n"
            "| 2026-05-03 | investing | Hold Z | r | active |\n")
        _write(dec / "decision-log.md", DECISION_HEADER + rows)
        c = _new(tmp, state)
        p = c.identify_patterns()[0]
        md1 = c.render_playbook(p, today="2026-05-24")
        md2 = c.render_playbook(p, today="2026-05-24")
        assert md1 == md2, "render_playbook must be deterministic"
        r1 = c.run(max_playbooks=8, dry_run=False)
        contents1 = {Path(w).name: Path(w).read_text(encoding="utf-8") for w in r1.written}
        r2 = c.run(max_playbooks=8, dry_run=False)
        contents2 = {Path(w).name: Path(w).read_text(encoding="utf-8") for w in r2.written}
        assert contents1.keys() == contents2.keys(), "re-run changed file set"
        # body identical except possibly the date line (same-day -> identical)
        for name in contents1:
            assert contents1[name] == contents2[name], f"re-run changed {name}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------
# 13. real-vault integration smoke (no crash, sane structures)
# ----------------------------------------------------------------------
def test_real_vault_integration_smoke():
    c = cz.Consolidator(since="2026-04-01")
    report = c.run(max_playbooks=8, dry_run=True)
    assert isinstance(report.patterns, list)
    assert report.n_decisions > 0, "real decision-log should have rows"
    assert report.n_sessions > 0, "real sessions-log should have rows"
    assert len(report.digest.encode("utf-8")) <= cz.DIGEST_MAX_BYTES
    # dry-run must not have created the real playbooks dir contents
    assert report.written == []


TEST_REGISTRY = {
    "test_ingest_sessions_canonical": test_ingest_sessions_canonical,
    "test_ingest_decisions_canonical": test_ingest_decisions_canonical,
    "test_decision_tag_threshold_above": test_decision_tag_threshold_above,
    "test_decision_tag_threshold_below": test_decision_tag_threshold_below,
    "test_telemetry_cluster_pattern": test_telemetry_cluster_pattern,
    "test_retro_theme_threshold": test_retro_theme_threshold,
    "test_skill_failure_rate_threshold": test_skill_failure_rate_threshold,
    "test_render_playbook_has_required_sections": test_render_playbook_has_required_sections,
    "test_hot_md_digest_under_4kb": test_hot_md_digest_under_4kb,
    "test_dry_run_writes_nothing": test_dry_run_writes_nothing,
    "test_run_writes_playbooks": test_run_writes_playbooks,
    "test_idempotent_rerun": test_idempotent_rerun,
    "test_real_vault_integration_smoke": test_real_vault_integration_smoke,
}


def run_tests(test_filter: str = "") -> int:
    failed, passed = [], 0
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
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR: {name}\n    {type(e).__name__}: {e}")
            failed.append(name)
    print()
    print(f"Result: {passed} passed, {len(failed)} failed")
    return 1 if failed else 0


def main():
    ap = argparse.ArgumentParser(description="Unit tests for tools/consolidator.py")
    ap.add_argument("--test", default="", help="Run only the named test")
    args = ap.parse_args()
    return run_tests(test_filter=args.test)


if __name__ == "__main__":
    sys.exit(main())
