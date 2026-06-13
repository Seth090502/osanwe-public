#!/usr/bin/env bash
# Prevention Architecture Test Harness (HIGH-5 fix per SOTA gap analysis).
#
# Tests every gate of the vault prevention architecture against synthetic
# adversarial inputs. Uses file-based JSON fixtures to avoid shell-escape issues.
#
# Usage:
#   bash tools/test-prevention-arch.sh           # run all tests
#   bash tools/test-prevention-arch.sh T1        # run only test T1
#   bash tools/test-prevention-arch.sh --list    # list test IDs + descriptions
#
# Exit code: 0 if all selected tests pass; 1 if any fail.
#
# Coverage:
#   T1  pre-write-validator: clean Write -> exit 0
#   T2  pre-write-validator: broken-wikilink Write -> exit 2
#   T3  pre-write-validator: Edit injecting broken wikilink -> exit 2
#   T4  pre-write-validator: MultiEdit injecting broken wikilink -> exit 2
#   T5  pre-write-validator: EXEMPT_PATHS (CLAUDE.md) -> exit 0
#   T6  pre-write-validator: CLAUDE_VAULT_BYPASS_VALIDATOR=1 -> exit 0
#   T7  wikilink-check: PostToolUse on broken file -> exit 2
#   T8  frontmatter-check: forbidden domain field -> exit 2
#   T9  orphan-check: PostToolUse on new orphan file -> exit 2
#   T10 vault-audit.py --json: baseline (GATE clean + score >= 95-floor)
#   T11 vault-audit.py --json: 1 broken wikilink -> score 90 (gate breach)
#   T12 vault-audit.py --json: 5 orphans -> score 95 (hard-drift cap)
#   T13 stop-pr-and-audit.sh: emits continue=true on GATE breach
#   T14 vault-score-check.py: surfaces bypass-log entries
#   T15 skill-precheck.py: broken wikilink batch -> exit 2
#   T16 pre-write-validator: real-target wikilinks NOT blocked (C1 regression)
#   T17 vault-audit.py X1: session-artifact-gaps classifier emits valid schema
#   T18 vault-audit.py X2: skill-body-length classifier emits valid schema
#   T19 vault-audit.py --scope: orphan classifier respects global index (C2 regression)
#   T20 vault-audit.py X3: CLAUDE.md count-drift classifier emits valid schema
#   T21 vault-audit.py X5: knowledge-moc count-drift classifier emits valid schema
#   T22 pre-write-validator: Calendar/decisions/ EXEMPT_PATH_PREFIXES extension (SD-PV1)
#   T23 vault-audit.py X6: investment-analysis-quality classifier emits valid schema
#   T24 vault-audit.py X7: stale-commitments classifier emits valid SOFT-tier schema
#   T25 hot-md-check: 4 ## Last Session blocks (>3 invariant) -> exit 2 (Phase 2 lock)
#   T26 vault-audit X7: synthetic stale-commitment fixture detected as SOFT (zero score)
#   T27 seed-commitment: default mode + BACKFILL_MODE=1 routing (Phase 4.6 lock)
#   T28 fetch-prices.py extended-hours suite: invokes tools/test-fetch-prices.py;
#       T1-T11 (Mission Three Phase 4 lock) cover prepost=True, ah_mover threshold,
#       movers aggregation, contract additivity, crypto/holiday/half-day/multi-ticker
#       partial AH, VGT split preservation, API failure
#   T29 post-compact-reinject: smart-emit surfaces ## Active Context past the 8 KiB
#       head (Phase 7 G1 compaction-bridge) + clean fallback to raw truncation when
#       hot-md-emit-smart.py is unavailable (never throws, never emits nothing)
#   T30 pre-compact.py: archives transcript + hot.md snapshot on PreCompact; exit 0
#       (never throws). Hermetic via PRECOMPACT_ARCHIVE_DIR + PRECOMPACT_HOT_PATH.
#   T31 log-prompt.sh: vault-hygiene F2 floor guard -- bare-CR collapse (single-line
#       daily Log) + Obsidian [[ -> [ [ escape (no live wikilink). The 2026-05-29
#       95->85 GATE breach had no regression test; this is it. Hermetic via OSANWE_TEST_DAILY.
#   T32 auto-commit.sh GATE backstop: vault-audit --scope gate-count refuses a
#       broken-wikilink fixture, commits a clean one (Trap-B: tests the gate-count
#       mechanism the backstop relies on, not the full hook -- the live F11 flag
#       short-circuits the hook top, which would pass for the wrong reason)
#   T33 vault-audit X8 provenance classifier (invest vNEXT): post-cutoff analysis
#       fixture (created 2026-06-10) with one prov-less claim IS flagged; pre-cutoff
#       twin (created 2026-06-09) is NOT (both-directions boundary test); transient
#       fixtures written to wiki/investing/analyses/ and removed in the same test
#   T34 invest-research.js parses in the Workflow-harness dialect (AsyncFunction
#       wrapper with harness globals -- top-level return/await legal; parse-only)
#   T35 invest-verify.js parses in the Workflow-harness dialect (same check)
#   T36 score-outcomes.py fixture Brier lock: pooled new=0.223 (n=5), shadow=0.173125
#       (n=4), sequential stratum new=0.200833, realized_at_3mo=6, armed=false --
#       offline (fixture mode skips backfill); locks RATING_PROB_MAP freeze (R1)
#   T37 spark-sweep.js parses in the Workflow-harness dialect (spark vNEXT; same
#       AsyncFunction parse-only check as T34/T35)
#   T38 spark-verify.js parses in the Workflow-harness dialect (same check)

set -uo pipefail

# Use VAULT_ROOT env var if set; otherwise default to current working directory.
# Git Bash auto-translates C:/ to /c/ for shell ops; Python on Windows needs C:/.
VAULT_ROOT="${VAULT_ROOT:-$(pwd)}"
TEST_DIR="${VAULT_ROOT}/wiki/research/test-tmp/.harness"
JSON_DIR="${TEST_DIR}/json"
RESULTS=()
FAILED=0
PASSED=0
SELECT="${1:-all}"

# Tracking arrays for tests that mutate paths outside TEST_DIR (T26 + T27).
# Each entry is a path to remove on EXIT; backups are tracked separately via
# the .t27bak suffix so the cleanup function can restore-or-delete consistently.
T2X_PATHS_TO_REMOVE=()
T2X_PATHS_TO_RESTORE=()  # entries are "<path>" -- if "<path>.t2xbak" exists, restore from it

cleanup() {
    rm -rf "$TEST_DIR" 2>/dev/null || true
    for p in "${T2X_PATHS_TO_REMOVE[@]:-}"; do
        [ -n "$p" ] && rm -f "$p" 2>/dev/null || true
    done
    for p in "${T2X_PATHS_TO_RESTORE[@]:-}"; do
        if [ -n "$p" ]; then
            if [ -f "$p.t2xbak" ]; then
                mv "$p.t2xbak" "$p" 2>/dev/null || true
            else
                rm -f "$p" 2>/dev/null || true
            fi
        fi
    done
}
trap cleanup EXIT

mkdir -p "$TEST_DIR" "$JSON_DIR"

list_tests() {
    grep -E "^#   T[0-9]+ " "$0" | sed 's/^#   //'
    exit 0
}

[ "$SELECT" = "--list" ] && list_tests

# Helper: write a fixture file with given content
write_fixture() {
    local path="$1"
    shift
    cat > "$path"
}

# Helper: write a hook-input JSON file
write_json() {
    local out_path="$1"
    python -c "
import json, sys
data = json.loads(sys.stdin.read())
with open(r'$out_path', 'w') as f:
    json.dump(data, f)
"
}

# Helper: invoke a validator and return its exit code
invoke_validator() {
    local validator_path="$1"
    local json_path="$2"
    local extra_env="${3:-}"
    if [ -n "$extra_env" ]; then
        env $extra_env python "$validator_path" < "$json_path"
    else
        python "$validator_path" < "$json_path"
    fi
}

run_test() {
    local id="$1"
    local desc="$2"
    local actual_exit="$3"
    local expected_exit="$4"

    if [ "$SELECT" != "all" ] && [ "$SELECT" != "$id" ]; then
        return 0
    fi

    if [ "$actual_exit" = "$expected_exit" ]; then
        RESULTS+=("PASS  $id  exit=$actual_exit  $desc")
        PASSED=$((PASSED + 1))
    else
        RESULTS+=("FAIL  $id  expected=$expected_exit got=$actual_exit  $desc")
        FAILED=$((FAILED + 1))
    fi
}

# ---------- Synthetic content fixtures ----------

write_fixture "$TEST_DIR/clean.md" << 'EOF'
---
categories: [wiki]
created: 2026-04-28
updated: 2026-04-28
status: active
---

# Clean test
Just plain prose here.
EOF

write_fixture "$TEST_DIR/broken.md" << 'EOF'
---
categories: [wiki]
created: 2026-04-28
updated: 2026-04-28
status: active
---

# Broken
[[nonexistent-target-test-harness-XYZ]]
EOF

write_fixture "$TEST_DIR/forbidden-domain.md" << 'EOF'
---
categories: [wiki]
domain: career
created: 2026-04-28
updated: 2026-04-28
status: active
---

# Has forbidden domain
EOF

# Existing file for Edit tests
write_fixture "$TEST_DIR/existing.md" << 'EOF'
---
categories: [wiki]
created: 2026-04-28
updated: 2026-04-28
status: active
---

# Existing
Original content here.
EOF

# ---------- T1: pre-write-validator clean Write -> exit 0 ----------
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T1" ]; then
    python -c "
import json
data = {
    'tool_name': 'Write',
    'tool_input': {
        'file_path': '${VAULT_ROOT}/wiki/research/test-tmp/.harness/t1-new.md',
        'content': open(r'$TEST_DIR/clean.md').read()
    }
}
with open(r'$JSON_DIR/t1.json', 'w') as f:
    json.dump(data, f)
"
    set +e
    python "$VAULT_ROOT/tools/pre-write-validator.py" < "$JSON_DIR/t1.json" > /dev/null 2>&1
    actual=$?
    set -e
    run_test T1 "pre-write-validator: clean Write" "$actual" 0
fi

# ---------- T2: pre-write-validator broken Write -> exit 2 ----------
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T2" ]; then
    python -c "
import json
data = {
    'tool_name': 'Write',
    'tool_input': {
        'file_path': '${VAULT_ROOT}/wiki/research/test-tmp/.harness/t2-new.md',
        'content': open(r'$TEST_DIR/broken.md').read()
    }
}
with open(r'$JSON_DIR/t2.json', 'w') as f:
    json.dump(data, f)
"
    set +e
    python "$VAULT_ROOT/tools/pre-write-validator.py" < "$JSON_DIR/t2.json" > /dev/null 2>&1
    actual=$?
    set -e
    run_test T2 "pre-write-validator: broken-wikilink Write" "$actual" 2
fi

# ---------- T3: pre-write-validator Edit -> exit 2 ----------
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T3" ]; then
    python -c "
import json
data = {
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': '${VAULT_ROOT}/wiki/research/test-tmp/.harness/existing.md',
        'old_string': 'Original content here.',
        'new_string': 'Now with [[nonexistent-target-T3]] reference.'
    }
}
with open(r'$JSON_DIR/t3.json', 'w') as f:
    json.dump(data, f)
"
    set +e
    python "$VAULT_ROOT/tools/pre-write-validator.py" < "$JSON_DIR/t3.json" > /dev/null 2>&1
    actual=$?
    set -e
    run_test T3 "pre-write-validator: Edit injecting broken wikilink" "$actual" 2
fi

# ---------- T4: pre-write-validator MultiEdit -> exit 2 ----------
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T4" ]; then
    python -c "
import json
data = {
    'tool_name': 'MultiEdit',
    'tool_input': {
        'file_path': '${VAULT_ROOT}/wiki/research/test-tmp/.harness/existing.md',
        'edits': [
            {'old_string': 'Original content here.', 'new_string': 'Step 1.'},
            {'old_string': 'Step 1.', 'new_string': 'Step 1 with [[nonexistent-multi-target-T4]].'}
        ]
    }
}
with open(r'$JSON_DIR/t4.json', 'w') as f:
    json.dump(data, f)
"
    set +e
    python "$VAULT_ROOT/tools/pre-write-validator.py" < "$JSON_DIR/t4.json" > /dev/null 2>&1
    actual=$?
    set -e
    run_test T4 "pre-write-validator: MultiEdit injecting broken wikilink" "$actual" 2
fi

# ---------- T5: pre-write-validator EXEMPT_PATHS (CLAUDE.md) -> exit 0 ----------
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T5" ]; then
    python -c "
import json
data = {
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': '${VAULT_ROOT}/CLAUDE.md',
        'old_string': 'foo',
        'new_string': 'bar [[broken-but-exempt]]'
    }
}
with open(r'$JSON_DIR/t5.json', 'w') as f:
    json.dump(data, f)
"
    set +e
    python "$VAULT_ROOT/tools/pre-write-validator.py" < "$JSON_DIR/t5.json" > /dev/null 2>&1
    actual=$?
    set -e
    run_test T5 "pre-write-validator: EXEMPT_PATHS CLAUDE.md (broken edit allowed)" "$actual" 0
fi

# ---------- T6: pre-write-validator CLAUDE_VAULT_BYPASS_VALIDATOR=1 -> exit 0 ----------
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T6" ]; then
    set +e
    CLAUDE_VAULT_BYPASS_VALIDATOR=1 python "$VAULT_ROOT/tools/pre-write-validator.py" < "$JSON_DIR/t2.json" > /dev/null 2>&1
    actual=$?
    set -e
    run_test T6 "pre-write-validator: CLAUDE_VAULT_BYPASS_VALIDATOR=1 bypass" "$actual" 0
fi

# ---------- T7: wikilink-check on broken file -> exit 2 ----------
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T7" ]; then
    python -c "
import json
data = {
    'tool_name': 'Write',
    'tool_input': {
        'file_path': r'$TEST_DIR/broken.md'
    }
}
with open(r'$JSON_DIR/t7.json', 'w') as f:
    json.dump(data, f)
"
    set +e
    python "$VAULT_ROOT/tools/wikilink-check.py" < "$JSON_DIR/t7.json" > /dev/null 2>&1
    actual=$?
    set -e
    run_test T7 "wikilink-check: PostToolUse on broken file" "$actual" 2
fi

# ---------- T8: frontmatter-check forbidden domain -> exit 2 ----------
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T8" ]; then
    python -c "
import json
data = {
    'tool_name': 'Write',
    'tool_input': {
        'file_path': r'$TEST_DIR/forbidden-domain.md'
    }
}
with open(r'$JSON_DIR/t8.json', 'w') as f:
    json.dump(data, f)
"
    set +e
    python "$VAULT_ROOT/tools/frontmatter-check.py" < "$JSON_DIR/t8.json" > /dev/null 2>&1
    actual=$?
    set -e
    run_test T8 "frontmatter-check: forbidden domain field" "$actual" 2
fi

# ---------- T9: orphan-check on new file with 0 inbound wikilinks -> exit 2 ----------
# Audit 2026-04-28 fourth-pass H4: T9 had been deleted from the test harness without
# rationale, leaving the orphan-check.py PostToolUse hook with zero regression coverage.
# Symmetric pattern: T7 covers wikilink-check, T8 covers frontmatter-check, T9 covers
# orphan-check -- all three PostToolUse hooks that exit 2 to block the tool call.
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T9" ]; then
    write_fixture "$TEST_DIR/t9-orphan.md" << 'EOFT9'
---
categories: [wiki]
created: 2026-04-28
updated: 2026-04-28
status: active
---

# T9 orphan -- no inbound wikilinks
EOFT9
    python -c "
import json
data = {
    'tool_name': 'Write',
    'tool_input': {
        'file_path': r'$TEST_DIR/t9-orphan.md'
    }
}
with open(r'$JSON_DIR/t9.json', 'w') as f:
    json.dump(data, f)
"
    set +e
    python "$VAULT_ROOT/tools/orphan-check.py" < "$JSON_DIR/t9.json" > /dev/null 2>&1
    actual=$?
    set -e
    rm "$TEST_DIR/t9-orphan.md" 2>/dev/null || true
    run_test T9 "orphan-check: PostToolUse on new orphan file" "$actual" 2
fi

# Phase boundary: T10-T12 are vault-state scenario tests. They require .harness/
# to be empty (other tests' fixtures introduce their own GATE findings).
# Clear .harness/ and re-create json/ for any subsequent tests that need it.
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T10" ] || [ "$SELECT" = "T11" ] || [ "$SELECT" = "T12" ]; then
    rm -rf "$TEST_DIR"/*.md "$TEST_DIR"/orphans 2>/dev/null || true
fi

# ---------- T10: vault-audit.py --json baseline (GATE clean + above-floor) ----------
# Audit 2026-04-28: refactored from fixed-score-100 assertion to architectural
# invariant assertion. After X2 (skill-body-length classifier) added, the real
# vault may have legitimate HARD DRIFT findings (e.g., 10 known H2 violators)
# until the body-length refactor batch lands. The architecture invariant is
# "GATE clean (count == 0) AND score >= 95-floor", which holds regardless of
# in-flight HARD DRIFT remediation work.
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T10" ]; then
    set +e
    cd "$VAULT_ROOT" && python tools/vault-audit.py --json 2>/dev/null | python -c "
import sys, json
d = json.load(sys.stdin)
score = d['score']
gate = d.get('tiers', {}).get('gate', {}).get('count', 0)
assert gate == 0, f'GATE breach: count={gate}'
assert score >= 95, f'Score below 95-floor: {score}'
sys.exit(0)
" > /dev/null 2>&1
    actual=$?
    set -e
    run_test T10 "vault-audit.py --json: baseline (GATE clean + score >= 95)" "$actual" 0
fi

# ---------- T11: vault-audit.py --json 1 broken -> 90 ----------
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T11" ]; then
    write_fixture "$TEST_DIR/t11-gate-breach.md" << 'EOF3'
---
categories: [wiki]
created: 2026-04-28
updated: 2026-04-28
status: active
---

# T11 gate breach
[[t11-nonexistent-target-XYZ]]
EOF3
    set +e
    score=$(cd "$VAULT_ROOT" && python tools/vault-audit.py --json 2>/dev/null | python -c "import json, sys; d = json.load(sys.stdin); print(d['score'])")
    set -e
    rm "$TEST_DIR/t11-gate-breach.md"
    if [ "$score" = "90" ]; then
        run_test T11 "vault-audit.py --json: 1 broken wikilink -> 90 (gate breach)" 0 0
    else
        run_test T11 "vault-audit.py --json: 1 broken wikilink -> 90 (got $score)" 1 0
    fi
fi

# ---------- T12: vault-audit.py --json 5 orphans -> 95 ----------
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T12" ]; then
    mkdir -p "$TEST_DIR/orphans"
    for i in 1 2 3 4 5; do
        write_fixture "$TEST_DIR/orphans/orphan-t12-$i.md" << EOF2
---
categories: [wiki]
created: 2026-04-28
updated: 2026-04-28
status: active
---

# Orphan $i
EOF2
    done
    set +e
    score=$(cd "$VAULT_ROOT" && python tools/vault-audit.py --json 2>/dev/null | python -c "import json, sys; d = json.load(sys.stdin); print(d['score'])")
    set -e
    rm -rf "$TEST_DIR/orphans"
    if [ "$score" = "95" ]; then
        run_test T12 "vault-audit.py --json: 5 orphans -> 95 (hard-drift cap)" 0 0
    else
        run_test T12 "vault-audit.py --json: 5 orphans -> 95 (got $score)" 1 0
    fi
fi

# ---------- T13: stop-pr-and-audit.sh continue=true on broken state ----------
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T13" ]; then
    write_fixture "$TEST_DIR/t13-gate-breach.md" << 'EOFT13'
---
categories: [wiki]
created: 2026-04-28
updated: 2026-04-28
status: active
---

# T13 gate breach
[[t13-nonexistent-XYZ]]
EOFT13
    set +e
    output=$(echo '{}' | bash "$VAULT_ROOT/.claude/hooks/stop-pr-and-audit.sh" 2>/dev/null)
    set -e
    rm "$TEST_DIR/t13-gate-breach.md"
    if echo "$output" | grep -q '"continue": true'; then
        run_test T13 "stop-pr-and-audit.sh: emits continue=true on GATE breach" 0 0
    else
        run_test T13 "stop-pr-and-audit.sh: emits continue=true on GATE breach (no match)" 1 0
    fi
fi

# ---------- T14: vault-score-check.py bypass-log surfacing ----------
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T14" ]; then
    LOG_FILE="$VAULT_ROOT/.claude/state/bypasses-$(date +%Y-%m-%d).log"
    TEST_ENTRY="$(date -Iseconds 2>/dev/null || date +%Y-%m-%dT%H:%M:%S) test-prevention-arch T14: synthetic test entry"
    echo "$TEST_ENTRY" >> "$LOG_FILE"
    set +e
    python "$VAULT_ROOT/tools/vault-score-check.py" 2>&1 | grep -q "Validator bypasses (today)"
    actual=$?
    set -e
    run_test T14 "vault-score-check.py: surfaces bypass-log entries (regex-counted)" "$actual" 0
fi

# ---------- T15: skill-precheck.py broken batch -> exit 2 ----------
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T15" ]; then
    write_fixture "$TEST_DIR/t15-broken.md" << 'EOFT15'
---
categories: [wiki]
created: 2026-04-28
updated: 2026-04-28
status: active
---

# T15
[[t15-nonexistent-target-XYZ]]
EOFT15
    set +e
    python "$VAULT_ROOT/tools/skill-precheck.py" "$TEST_DIR/t15-broken.md" --skill /test > /dev/null 2>&1
    actual=$?
    set -e
    rm "$TEST_DIR/t15-broken.md"
    run_test T15 "skill-precheck.py: broken wikilink batch -> exit 2" "$actual" 2
fi

# ---------- T16: pre-write-validator NOT block on real-target wikilinks (C1 regression test) ----------
# Audit 2026-04-28 finding C1: vault-audit.py --scope was producing false-positive
# broken-wikilink reports because the global file index was not built when scope was
# restricted. The pre-write-validator runs --scope on a tmp file, so EVERY new file
# with wikilinks to real vault targets was falsely blocked. This test fixture asserts
# the post-fix behavior: a Write with [[hot]], [[CLAUDE]], [[knowledge-moc]],
# [[sessions-log]], [[decision-log]] in frontmatter related: list is NOT blocked.
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T16" ]; then
    write_fixture "$TEST_DIR/t16-real-targets.md" << 'EOFT16'
---
categories: [wiki]
created: 2026-04-28
updated: 2026-04-28
status: active
related:
  - "[[hot]]"
  - "[[CLAUDE]]"
  - "[[knowledge-moc]]"
  - "[[sessions-log]]"
  - "[[decision-log]]"
---

# T16 -- real-target wikilinks resolve under --scope

This file references known-real vault targets that exist on disk. Pre-fix
behavior reported these as broken because --scope mode did not build the
global file index. Post-fix should resolve cleanly.
EOFT16
    python -c "
import json
data = {
    'tool_name': 'Write',
    'tool_input': {
        'file_path': '${VAULT_ROOT}/wiki/research/test-tmp/.harness/t16-new.md',
        'content': open(r'$TEST_DIR/t16-real-targets.md').read()
    }
}
with open(r'$JSON_DIR/t16.json', 'w') as f:
    json.dump(data, f)
"
    set +e
    python "$VAULT_ROOT/tools/pre-write-validator.py" < "$JSON_DIR/t16.json" > /dev/null 2>&1
    actual=$?
    set -e
    run_test T16 "pre-write-validator: real-target wikilinks NOT blocked (C1 regression)" "$actual" 0
fi

# ---------- T17: vault-audit.py X1 classifier (session-artifact continuity) ----------
# Audit 2026-04-28 X1: Classifier 10 reports retro commits without paired
# sessions-log + decision-log entries. Smoke-test: assert the classifier ran
# and emitted a list-typed result key in JSON output (regardless of content).
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T17" ]; then
    set +e
    python "$VAULT_ROOT/tools/vault-audit.py" --json 2>/dev/null | python -c "
import sys, json
d = json.load(sys.stdin)
gaps = d.get('session_artifact_gaps', None)
assert gaps is not None, 'session_artifact_gaps key missing from JSON output'
assert isinstance(gaps, list), 'session_artifact_gaps must be a list'
# Schema check on first entry if any
for g in gaps:
    assert 'commit' in g and 'date' in g and 'missing' in g, 'malformed gap entry'
sys.exit(0)
" > /dev/null 2>&1
    actual=$?
    set -e
    run_test T17 "vault-audit.py X1: session-artifact-gaps classifier emits valid schema" "$actual" 0
fi

# ---------- T18: vault-audit.py X2 classifier (skill-body-length cap) ----------
# Audit 2026-04-28 X2: Classifier 11 reports SKILL.md files exceeding the
# SKILL_BODY_LENGTH_CAP (raised 263 -> 900 in commit 332516f per H2 revert
# quality-preservation policy). Smoke-test: assert the classifier ran and
# emitted a list-typed result key. Schema check uses 900 to match current cap.
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T18" ]; then
    set +e
    python "$VAULT_ROOT/tools/vault-audit.py" --json 2>/dev/null | python -c "
import sys, json
d = json.load(sys.stdin)
viol = d.get('skill_body_length_violations', None)
assert viol is not None, 'skill_body_length_violations key missing from JSON output'
assert isinstance(viol, list), 'skill_body_length_violations must be a list'
# Schema check on entries (when present); cap raised 263 -> 900 per H2 revert
for v in viol:
    assert 'skill' in v and 'lines' in v and 'over_by' in v, 'malformed violation entry'
    assert v['lines'] > 900, 'reported violation does not exceed cap'
    assert v['over_by'] == v['lines'] - 900, 'over_by computation incorrect'
sys.exit(0)
" > /dev/null 2>&1
    actual=$?
    set -e
    run_test T18 "vault-audit.py X2: skill-body-length classifier emits valid schema" "$actual" 0
fi

# ---------- T20: vault-audit.py X3 classifier (CLAUDE.md count-drift) ----------
# Audit 2026-04-28 5th-pass X3: Classifier 12 reports CLAUDE.md count claims
# (Active Skills table, "all N skills" narrative, "Investing (N docs)") that
# disagree with actuals on disk. Smoke-test: assert classifier ran and emitted
# a list-typed result key with valid schema entries (when present).
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T20" ]; then
    set +e
    python "$VAULT_ROOT/tools/vault-audit.py" --json 2>/dev/null | python -c "
import sys, json
d = json.load(sys.stdin)
drifts = d.get('claude_md_count_drift', None)
assert drifts is not None, 'claude_md_count_drift key missing from JSON output'
assert isinstance(drifts, list), 'claude_md_count_drift must be a list'
for entry in drifts:
    assert 'location' in entry and 'claimed' in entry and 'actual' in entry, 'malformed drift entry'
sys.exit(0)
" > /dev/null 2>&1
    actual=$?
    set -e
    run_test T20 "vault-audit.py X3: CLAUDE.md count-drift classifier emits valid schema" "$actual" 0
fi

# ---------- T21: vault-audit.py X5 classifier (knowledge-moc count-drift) ----------
# Audit 2026-04-28 5th-pass X5: Classifier 13 reports knowledge-moc count claims
# (investing-moc entity-note + analysis counts; career-moc company-entity count)
# that disagree with actuals on disk. Smoke-test: assert valid schema.
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T21" ]; then
    set +e
    python "$VAULT_ROOT/tools/vault-audit.py" --json 2>/dev/null | python -c "
import sys, json
d = json.load(sys.stdin)
drifts = d.get('knowledge_moc_count_drift', None)
assert drifts is not None, 'knowledge_moc_count_drift key missing from JSON output'
assert isinstance(drifts, list), 'knowledge_moc_count_drift must be a list'
for entry in drifts:
    assert 'location' in entry and 'claimed' in entry and 'actual' in entry, 'malformed drift entry'
sys.exit(0)
" > /dev/null 2>&1
    actual=$?
    set -e
    run_test T21 "vault-audit.py X5: knowledge-moc count-drift classifier emits valid schema" "$actual" 0
fi

# ---------- T22: pre-write-validator Calendar/decisions/ EXEMPT_PATH_PREFIXES (SD-PV1) ----------
# Audit 2026-04-28 5th-pass SD-PV1: Calendar/decisions/{sessions,decision}-log.md
# are append-only operational logs that frequently introduce wikilinks to files
# created in the same atomic commit. Pre-write-validator must NOT block such
# cross-temporal wikilinks. Test fixture: simulate a sessions-log Edit that
# introduces a [[not-yet-existent]] wikilink; expect exit 0 (allowed).
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T22" ]; then
    write_fixture "$TEST_DIR/t22-cross-temporal.md" << 'EOFT22'
---
categories: [decisions]
type: session-log
created: 2026-04-28
updated: 2026-04-28
status: active
---

# Sessions Log

### 2026-04-28 -- T22 cross-temporal entry
Domain: meta
Skills: /retro
Modified: [[t22-not-yet-existent-target-XYZ]]
Decisions: T22 forward-reference test
EOFT22
    python -c "
import json
data = {
    'tool_name': 'Edit',
    'tool_input': {
        'file_path': '${VAULT_ROOT}/Calendar/decisions/sessions-log.md',
        'old_string': 'placeholder-old',
        'new_string': open(r'$TEST_DIR/t22-cross-temporal.md').read()
    }
}
with open(r'$JSON_DIR/t22.json', 'w') as f:
    json.dump(data, f)
"
    set +e
    python "$VAULT_ROOT/tools/pre-write-validator.py" < "$JSON_DIR/t22.json" > /dev/null 2>&1
    actual=$?
    set -e
    rm "$TEST_DIR/t22-cross-temporal.md" 2>/dev/null || true
    run_test T22 "pre-write-validator: Calendar/decisions/ EXEMPT_PATH_PREFIXES extension (SD-PV1)" "$actual" 0
fi

# ---------- T19: vault-audit.py --scope orphan classifier symmetry (C2 regression) ----------
# Audit 2026-04-28 fourth-pass C2: orphan classifier was using scope-bounded
# `all_link_targets`, so a file with inbound links from OUTSIDE the scope was
# falsely reported as orphan when scoped to itself. Post-fix: the global pass
# (run before scope filter) populates `global_all_link_targets` from the FULL
# vault, and the orphan check uses the global set under --scope mode.
# Test: wiki/hot.md has inbound links from many vault files (HOME.md, daily
# notes, etc.). Under --scope wiki/hot.md, orphan count must be 0.
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T19" ]; then
    set +e
    python "$VAULT_ROOT/tools/vault-audit.py" --scope wiki/hot.md --json 2>/dev/null | python -c "
import sys, json
d = json.load(sys.stdin)
orphans = d.get('orphans', [])
# wiki/hot.md is referenced by HOME.md, sessions-log.md, daily notes, etc.
# Pre-fix: hot.md reported as orphan (false positive under --scope).
# Post-fix: hot.md NOT in orphans list because global inbound index sees the links.
assert len(orphans) == 0, f'C2 regression: hot.md reported orphan under --scope: orphans={orphans}'
sys.exit(0)
" > /dev/null 2>&1
    actual=$?
    set -e
    run_test T19 "vault-audit --scope: orphan classifier respects global index (C2 regression)" "$actual" 0
fi

# ---------- T23: vault-audit.py X6 classifier (investment-analysis-quality) ----------
# /invest extreme-overhaul X6: Classifier 14 scores wiki/investing/analyses/*.md
# on 7 dimensions (source count + diversity + forensic metrics + Dataroma + CapitolTrades
# + OpenInsider + TRADING DECISION header). Smoke-test: assert valid schema.
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T23" ]; then
    set +e
    python "$VAULT_ROOT/tools/vault-audit.py" --json 2>/dev/null | python -c "
import sys, json
d = json.load(sys.stdin)
drifts = d.get('investment_analysis_quality_drift', None)
assert drifts is not None, 'investment_analysis_quality_drift key missing from JSON output'
assert isinstance(drifts, list), 'investment_analysis_quality_drift must be a list'
for entry in drifts:
    assert 'file' in entry and 'dimension' in entry and 'expected' in entry and 'actual' in entry and 'status' in entry, 'malformed drift entry'
sys.exit(0)
" > /dev/null 2>&1
    actual=$?
    set -e
    run_test T23 "vault-audit.py X6: investment-analysis-quality classifier emits valid schema" "$actual" 0
fi

# ---------- T24: vault-audit.py X7 classifier (stale-commitments) ----------
# Phase 4.5 commitment-tracking auto-escalation: SOFT DRIFT classifier scans
# Calendar/daily/last-30-days for unchecked Commitments past ESCALATION_DATE.
# Smoke-test: assert key present + list type + entry schema (when populated).
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T24" ]; then
    set +e
    python "$VAULT_ROOT/tools/vault-audit.py" --json 2>/dev/null | python -c "
import sys, json
d = json.load(sys.stdin)
findings = d.get('x7_stale_commitments', None)
assert findings is not None, 'x7_stale_commitments key missing from JSON output'
assert isinstance(findings, list), 'x7_stale_commitments must be a list'
for entry in findings:
    assert 'file' in entry and 'line' in entry and 'type' in entry, 'malformed x7 entry'
    assert entry['severity'] == 'SOFT', 'x7 must be SOFT tier (0 score impact)'
    assert 'days_overdue' in entry, 'days_overdue must be present'
sys.exit(0)
" > /dev/null 2>&1
    actual=$?
    set -e
    run_test T24 "vault-audit.py X7: stale-commitments classifier emits valid SOFT-tier schema" "$actual" 0
fi

# ---------- T25: hot-md-check 4 ## Last Session blocks -> exit 2 ----------
# Locks Quality Sweep 1 Phase 2 (skill-precheck hook) defense-in-depth: hot-md-check
# is the post-PostToolUse final gate on wiki/hot.md schema invariants. The "<=3
# Last Session blocks" rule is the canonical demote-on-write guard. Fixture
# isolated to TEST_DIR with UUID suffix; no real wiki/hot.md mutation.
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T25" ]; then
    T25_UUID=$(python -c 'import uuid; print(uuid.uuid4().hex[:8])')
    T25_FIXTURE="$TEST_DIR/t25-hot-md-${T25_UUID}.md"
    write_fixture "$T25_FIXTURE" << 'EOFT25'
---
categories: [wiki]
type: synthesis
schema_version: hot-md-v2
status: active
created: 2026-05-06
updated: 2026-05-06
tags: []
aliases: []
related: []
---

# Hot

## Last Session
Block A.

## Last Session
Block B.

## Last Session
Block C.

## Last Session
Block D (4th block; violates <=3 invariant)

## Pending Items

## Active Context
EOFT25
    set +e
    python "$VAULT_ROOT/tools/hot-md-check.py" "$T25_FIXTURE" --quiet > /dev/null 2>&1
    actual=$?
    set -e
    rm -f "$T25_FIXTURE" 2>/dev/null || true
    run_test T25 "hot-md-check: 4 ## Last Session blocks (>3 invariant)" "$actual" 2
fi

# ---------- T26: vault-audit X7 synthetic stale-commitment fixture (SOFT zero-score) ----------
# Locks Phase 4.5 commitment-tracking auto-escalation classifier. Creates a
# UUID-marked stale-commitment fixture in Calendar/daily/<unused-date>.md (date
# stem REQUIRED for x7 scan; date selected to be in 30d window AND have no
# existing daily file). Asserts the classifier detects our marker AND that
# severity == SOFT (zero score impact per v2.2). Cleanup deletes the fixture
# unconditionally via the trap registry.
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T26" ]; then
    T26_UUID=$(python -c 'import uuid; print(uuid.uuid4().hex[:8])')
    # Find an unused date in the last 30 days (x7 scan window)
    T26_DATE=$(python -c "
from pathlib import Path
from datetime import date, timedelta
existing = {p.stem for p in Path('Calendar/daily').glob('*.md')}
today = date.today()
for d in range(2, 30):
    target = today - timedelta(days=d)
    if target.isoformat() not in existing:
        print(target.isoformat())
        break
")
    T26_FIXTURE="$VAULT_ROOT/Calendar/daily/${T26_DATE}.md"
    T2X_PATHS_TO_REMOVE+=("$T26_FIXTURE")
    # Build fixture: stale ESCALATION_DATE in the past + UUID marker for detection
    T26_PAST_DATE=$(python -c "
from datetime import date, timedelta
print((date.today() - timedelta(days=3)).isoformat())
")
    cat > "$T26_FIXTURE" << EOFT26
---
categories: [daily]
created: $T26_DATE
updated: $T26_DATE
status: active
tags: []
related: []
---

# $T26_DATE

## Commitments
- [ ] T26 ${T26_UUID} stale fixture <!-- seeded-from: t26-${T26_UUID}-${T26_DATE} --> (TRIGGER: t26; DECISION_DATE: ${T26_DATE}; ESCALATION_DATE: ${T26_PAST_DATE})
EOFT26
    set +e
    python "$VAULT_ROOT/tools/vault-audit.py" --json 2>/dev/null | python -c "
import sys, json
d = json.load(sys.stdin)
findings = d.get('x7_stale_commitments', [])
# Locate our UUID-marked fixture entry
hits = [e for e in findings if 't26-${T26_UUID}' in str(e.get('decision_slug', ''))]
assert hits, 'T26 UUID-marked fixture not detected by x7 classifier'
e = hits[0]
assert e.get('severity') == 'SOFT', f\"x7 must be SOFT tier, got {e.get('severity')}\"
assert 'days_overdue' in e and e['days_overdue'] >= 1, 'days_overdue missing or invalid'
sys.exit(0)
" > /dev/null 2>&1
    actual=$?
    set -e
    run_test T26 "vault-audit X7: synthetic stale-commitment fixture detected SOFT zero-score" "$actual" 0
fi

# ---------- T27: seed-commitment default + BACKFILL_MODE=1 routing ----------
# Locks Phase 4.6 stale-decision backfill load-bearing fix. The hook routes a
# decision-* file's commitment to either decision_date+1d (default) or today+1d
# (BACKFILL_MODE=1). Test verifies BOTH paths.
#
# Safety: fixture decision lives in real Calendar/decisions/ (regex-matched by
# the hook). UUID suffix prevents collision. Daily-note targets backed up via
# .t2xbak before mutation; cleanup restores or deletes per the trap registry.
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T27" ]; then
    T27_UUID=$(python -c 'import uuid; print(uuid.uuid4().hex[:8])')
    # Pick a decision_date in the deep past where decision_date+1d has no daily
    T27_DECISION_DATE=$(python -c "
from pathlib import Path
from datetime import date, timedelta
existing = {p.stem for p in Path('Calendar/daily').glob('*.md')}
today = date.today()
# Find an old date whose +1d also has no daily, AND decision_date itself has no daily
for d in range(60, 200):
    target = today - timedelta(days=d)
    nxt = target + timedelta(days=1)
    if target.isoformat() not in existing and nxt.isoformat() not in existing:
        print(target.isoformat())
        break
")
    T27_DEFAULT_DAILY_DATE=$(python -c "
from datetime import date, timedelta
print((date.fromisoformat('${T27_DECISION_DATE}') + timedelta(days=1)).isoformat())
")
    T27_BACKFILL_DAILY_DATE=$(python -c "
from datetime import date, timedelta
print((date.today() + timedelta(days=1)).isoformat())
")
    T27_FIXTURE_DEC="$VAULT_ROOT/Calendar/decisions/decision-test-${T27_UUID}-${T27_DECISION_DATE}-test.md"
    T27_DEFAULT_DAILY="$VAULT_ROOT/Calendar/daily/${T27_DEFAULT_DAILY_DATE}.md"
    T27_BACKFILL_DAILY="$VAULT_ROOT/Calendar/daily/${T27_BACKFILL_DAILY_DATE}.md"

    # Track for cleanup. Fixture decision: always remove. Daily targets: backup-restore.
    T2X_PATHS_TO_REMOVE+=("$T27_FIXTURE_DEC")
    T2X_PATHS_TO_RESTORE+=("$T27_DEFAULT_DAILY" "$T27_BACKFILL_DAILY")
    # Backup any pre-existing daily targets so restore is faithful
    [ -f "$T27_DEFAULT_DAILY" ] && cp "$T27_DEFAULT_DAILY" "$T27_DEFAULT_DAILY.t2xbak"
    [ -f "$T27_BACKFILL_DAILY" ] && cp "$T27_BACKFILL_DAILY" "$T27_BACKFILL_DAILY.t2xbak"

    # Build fixture decision file
    cat > "$T27_FIXTURE_DEC" << EOFT27DEC
---
categories: [decisions]
type: decision
status: active
decision_date: $T27_DECISION_DATE
created: $T27_DECISION_DATE
updated: $T27_DECISION_DATE
tags:
  - topic/skill-infra
related: []
---

# T27 fixture decision ${T27_UUID}

Test decision text body.
EOFT27DEC

    # Build hook input JSON
    python -c "
import json
data = {'tool_name': 'Write', 'tool_input': {'file_path': r'$T27_FIXTURE_DEC'}}
with open(r'$JSON_DIR/t27.json', 'w') as f:
    json.dump(data, f)
"
    set +e
    # Test 1: default mode -> decision_date+1d daily
    python "$VAULT_ROOT/.claude/hooks/seed-commitment.py" < "$JSON_DIR/t27.json" 2>/dev/null
    test1=0
    if [ -f "$T27_DEFAULT_DAILY" ]; then
        if grep -q "${T27_UUID}" "$T27_DEFAULT_DAILY" 2>/dev/null; then
            test1=1
        fi
    fi

    # Test 2: BACKFILL_MODE=1 -> today+1d daily
    BACKFILL_MODE=1 python "$VAULT_ROOT/.claude/hooks/seed-commitment.py" < "$JSON_DIR/t27.json" 2>/dev/null
    test2=0
    if [ -f "$T27_BACKFILL_DAILY" ]; then
        if grep -q "${T27_UUID}" "$T27_BACKFILL_DAILY" 2>/dev/null; then
            test2=1
        fi
    fi
    set -e

    if [ "$test1" = "1" ] && [ "$test2" = "1" ]; then
        actual=0
    else
        actual=1
    fi
    run_test T27 "seed-commitment: default decision_date+1d AND BACKFILL_MODE today+1d routing" "$actual" 0
fi

# ---------- T28: fetch-prices.py extended-hours suite (Mission Three Phase 4) ----------
# Wraps tools/test-fetch-prices.py (unittest stdlib, T1-T11). Asserts exit 0 = all
# 11 tests pass. Invokes via python; output captured + suppressed
# unless failure. Selected by orchestration parity with T1-T27 vault-schema tests;
# domain-separated test files are intentional (vault-schema vs yfinance-script).
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T28" ]; then
    actual=0
    python "$VAULT_ROOT/tools/test-fetch-prices.py" >"$TEST_DIR/t28-output.log" 2>&1 || actual=1
    run_test T28 "fetch-prices.py T1-T11 (extended-hours diffusion suite)" "$actual" 0
fi

# ---------- T29: post-compact-reinject smart-emit + clean fallback (Phase 7 G1) ----------
# G1 compaction-bridge: post-compact-reinject.py must emit the smart priority-ordered
# subset (so ## Active Context survives compaction even though it sits past the 8 KiB
# raw-truncation head), AND degrade cleanly to raw truncation -- never throw, never emit
# nothing -- when hot-md-emit-smart.py is unavailable. Hermetic via env overrides
# (POSTCOMPACT_HOT_PATH + POSTCOMPACT_SMART_EMIT); no real wiki/hot.md mutation.
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T29" ]; then
    T29_UUID=$(python -c 'import uuid; print(uuid.uuid4().hex[:8])')
    T29_FIX="$TEST_DIR/t29-hot-${T29_UUID}.md"
    T29_MARK="T29-MARKER-${T29_UUID}"
    python -c "
fm = '---\ncategories: [wiki]\ntype: synthesis\nschema_version: hot-md-v2\nstatus: active\ncreated: 2026-05-30\nupdated: 2026-05-30\ntags: []\naliases: []\nrelated: []\n---\n\n# Session Cache\n\n'
last = '## Last Session\n' + ('Filler to push Active Context past the 8 KiB raw-truncation head. ' * 8 + '\n') * 30 + '\n'
active = '## Active Context\n${T29_MARK} -- current arc + tooling state that MUST survive compaction.\n\n'
pending = '## Pending Items\n- [ ] sample pending item\n'
open(r'$T29_FIX', 'w', encoding='utf-8').write(fm + last + active + pending)
"
    set +e
    # (a) NORMAL: smart-emit wired -> Active Context body (marker) survives the 8 KiB head
    out_a=$(POSTCOMPACT_HOT_PATH="$T29_FIX" python "$VAULT_ROOT/.claude/hooks/post-compact-reinject.py" < /dev/null 2>/dev/null)
    rc_a=$?
    # (b) FALLBACK: smart-emit helper missing -> still emits non-empty, exit 0, never throws
    out_b=$(POSTCOMPACT_HOT_PATH="$T29_FIX" POSTCOMPACT_SMART_EMIT="$TEST_DIR/nope-${T29_UUID}.py" python "$VAULT_ROOT/.claude/hooks/post-compact-reinject.py" < /dev/null 2>/dev/null)
    rc_b=$?
    set -e
    rm -f "$T29_FIX" 2>/dev/null || true
    actual=1
    if [ "$rc_a" = "0" ] && echo "$out_a" | grep -q "$T29_MARK" \
       && [ "$rc_b" = "0" ] && [ -n "$out_b" ]; then
        actual=0
    fi
    run_test T29 "post-compact-reinject: smart-emit surfaces Active Context + clean fallback" "$actual" 0
fi

# ---------- T30: pre-compact.py archive (PreCompact transcript + hot snapshot) ----------
# Locks the PreCompact archive hook: must write transcript-<stamp>.json + hot-snapshot-<stamp>.md
# and exit 0 (never throw). Hermetic via env overrides (PRECOMPACT_ARCHIVE_DIR +
# PRECOMPACT_HOT_PATH); no real .claude/transcripts or wiki/hot.md mutation.
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T30" ]; then
    T30_UUID=$(python -c 'import uuid; print(uuid.uuid4().hex[:8])')
    T30_ARCH="$TEST_DIR/t30-arch-${T30_UUID}"
    T30_HOT="$TEST_DIR/t30-hot-${T30_UUID}.md"
    T30_MARK="T30-MARKER-${T30_UUID}"
    mkdir -p "$T30_ARCH"
    printf '# hot fixture\n%s -- active context that must be snapshotted.\n' "$T30_MARK" > "$T30_HOT"
    set +e
    printf '{"transcript":"hermetic %s payload"}' "$T30_MARK" | \
        PRECOMPACT_ARCHIVE_DIR="$T30_ARCH" PRECOMPACT_HOT_PATH="$T30_HOT" \
        python "$VAULT_ROOT/.claude/hooks/pre-compact.py" >/dev/null 2>&1
    rc=$?
    set -e
    actual=1
    if [ "$rc" = "0" ] \
       && ls "$T30_ARCH"/transcript-*.json >/dev/null 2>&1 \
       && ls "$T30_ARCH"/hot-snapshot-*.md >/dev/null 2>&1 \
       && grep -q "$T30_MARK" "$T30_ARCH"/hot-snapshot-*.md 2>/dev/null; then
        actual=0
    fi
    rm -rf "$T30_ARCH" "$T30_HOT" 2>/dev/null || true
    run_test T30 "pre-compact.py: archives transcript + hot snapshot, exit 0 (never throws)" "$actual" 0
fi

# ---------- T31: log-prompt.sh CR-collapse + wikilink-escape (vault-hygiene F2 floor guard) ----------
# Locks BOTH halves of the 2026-05-29 fix that the broken-wikilink GATE breach (95->85)
# exposed: (Fix-A) bare CR + newlines collapse to a single space, and (Fix-B) the Obsidian
# wikilink marker [[ is escaped to [ [ so no live wikilink can form in the daily ## Log.
# Feed a prompt containing BOTH a bare CR and a literal [[marker]]; assert the appended Log
# line is single (no CR fracture) AND the [[ was escaped. Hermetic via OSANWE_TEST_DAILY.
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T31" ]; then
    T31_UUID=$(python -c 'import uuid; print(uuid.uuid4().hex[:8])')
    T31_DAILY="$TEST_DIR/t31-daily-${T31_UUID}.md"
    T31_MARK="T31-MARKER-${T31_UUID}"
    T31_JSON="$JSON_DIR/t31-${T31_UUID}.json"
    # Pre-seed a daily fixture with a ## Log section so the hook appends (skips template).
    printf -- '---\ncategories: [daily]\nstatus: active\ncreated: 2026-05-31\nupdated: 2026-05-31\ntags: []\nrelated: []\n---\n\n# fixture\n\n## Log\n\n' > "$T31_DAILY"
    # Build hook input: prompt with a BARE CR and a literal Obsidian wikilink marker.
    python -c "
import json
prompt = 'before\r${T31_MARK} [[wikilink-target-${T31_UUID}]] after'
open(r'$T31_JSON','w').write(json.dumps({'prompt': prompt}))
"
    set +e
    OSANWE_TEST_DAILY="$T31_DAILY" bash "$VAULT_ROOT/.claude/hooks/log-prompt.sh" < "$T31_JSON" >/dev/null 2>&1
    set -e
    actual=$(python -c "
content = open(r'$T31_DAILY', encoding='utf-8').read()
lines = content.split('\n')
hits = [l for l in lines if '${T31_MARK}' in l]
ok = bool(hits) and len(hits) == 1 and ('\r' not in hits[0]) and ('[[' not in hits[0])
print(0 if ok else 1)
")
    rm -f "$T31_DAILY" "$T31_JSON" 2>/dev/null || true
    run_test T31 "log-prompt.sh: CR collapsed (single line) + [[ escaped in daily Log (F2 floor guard)" "$actual" 0
fi

# ---------- T32: auto-commit.sh GATE backstop (gate-count refuse mechanism) ----------
# Locks the CAT-1 defense-in-depth backstop: auto-commit.sh refuses to commit a markdown
# file when vault-audit.py --scope --json reports tiers.gate.count > 0 (and commits when 0).
# Per Trap B, this drives the exact gate-count check the hook relies on (NOT the full hook --
# the live F11 flag short-circuits the hook at its top, which would pass for the wrong reason).
# Falsifiable: broken-wikilink fixture MUST yield refuse (gate>0), clean MUST yield commit
# (gate==0) -- the discrimination is the test. A structural assert binds the hook's REFUSED
# block so removing it from auto-commit.sh also fails T32.
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T32" ]; then
    T32_UUID=$(python -c 'import uuid; print(uuid.uuid4().hex[:8])')
    T32_BROKEN="$TEST_DIR/t32-broken-${T32_UUID}.md"
    T32_CLEAN="$TEST_DIR/t32-clean-${T32_UUID}.md"
    printf -- '---\ncategories: [wiki]\nstatus: active\ncreated: 2026-05-31\nupdated: 2026-05-31\ntags: []\nrelated: []\n---\n\n# t32 broken\n[[nonexistent-target-t32-%s]]\n' "$T32_UUID" > "$T32_BROKEN"
    printf -- '---\ncategories: [wiki]\nstatus: active\ncreated: 2026-05-31\nupdated: 2026-05-31\ntags: []\nrelated: []\n---\n\n# t32 clean\nPlain prose only.\n' > "$T32_CLEAN"
    # The exact gate-count extraction auto-commit.sh performs (CAT-1 backstop).
    gate_of() {
        python "$VAULT_ROOT/tools/vault-audit.py" --scope "$1" --json 2>/dev/null | python -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('tiers', {}).get('gate', {}).get('count', 0))
except Exception:
    print(0)
" 2>/dev/null || echo 0
    }
    set +e
    rel_broken=$(echo "$T32_BROKEN" | sed "s|^${VAULT_ROOT}/||;s|^${VAULT_ROOT}\\\\||")
    rel_clean=$(echo "$T32_CLEAN" | sed "s|^${VAULT_ROOT}/||;s|^${VAULT_ROOT}\\\\||")
    gc_broken=$(gate_of "$rel_broken")
    gc_clean=$(gate_of "$rel_clean")
    grep -q "auto-commit: REFUSED" "$VAULT_ROOT/.claude/hooks/auto-commit.sh"
    has_block=$?
    set -e
    rm -f "$T32_BROKEN" "$T32_CLEAN" 2>/dev/null || true
    actual=1
    if [ "${gc_broken:-0}" -gt 0 ] && [ "${gc_clean:-0}" -eq 0 ] && [ "$has_block" = "0" ]; then
        actual=0
    fi
    run_test T32 "auto-commit.sh GATE backstop: refuse gate>0 fixture, commit clean (Trap-B gate-count)" "$actual" 0
fi

# ---------- T33: vault-audit X8 provenance classifier (both-directions boundary) ----------
# Post-cutoff fixture (created: 2026-06-10, ON the boundary) with one prov-less claim
# must be flagged exactly once (its prov-carrying claim must NOT be flagged); the
# pre-cutoff twin (created: 2026-06-09) must produce zero findings. Falsifiable in
# both directions: a classifier that flags everything fails on the twin; one that
# flags nothing fails on the fixture. Transient fixtures in the REAL analyses dir
# (X8 scans only wiki/investing/analyses/), removed in-test.
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T33" ]; then
    T33_UUID=$(python -c 'import uuid; print(uuid.uuid4().hex[:8])')
    T33_POST="$VAULT_ROOT/wiki/investing/analyses/t33-post-${T33_UUID}-analysis-2026-06-10.md"
    T33_PRE="$VAULT_ROOT/wiki/investing/analyses/t33-pre-${T33_UUID}-analysis-2026-06-09.md"
    t33_body() {
        printf -- '---\ncategories: [wiki]\ntype: analysis\nstatus: active\ncreated: %s\nupdated: %s\ntags: []\nrelated: []\n---\n\n# t33 fixture\n\n<!-- INGEST:claims -->\n```yaml\n:::ingest:claims\n- entity: T33X\n  metric: with-prov\n  value: 1.0\n  date: 2026-06-09\n  grade: A\n  section: financial-signals\n  text: "has provenance"\n  prov: script:yfinance\n- entity: T33X\n  metric: missing-prov\n  value: 2.0\n  date: 2026-06-09\n  grade: A\n  section: financial-signals\n  text: "no provenance"\n:::\n```\n' "$1" "$1"
    }
    t33_body "2026-06-10" > "$T33_POST"
    t33_body "2026-06-09" > "$T33_PRE"
    set +e
    T33_OUT=$(python "$VAULT_ROOT/tools/vault-audit.py" --json 2>/dev/null | python -c "
import json, sys
d = json.load(sys.stdin)
f = d.get('x8_provenance_coverage', [])
post = [x for x in f if 't33-post-' in x.get('file','')]
pre  = [x for x in f if 't33-pre-'  in x.get('file','')]
ok = (len(post) == 1 and post[0].get('metric') == 'missing-prov' and len(pre) == 0)
print('OK' if ok else f'BAD post={len(post)} pre={len(pre)}')
" 2>/dev/null)
    set -e
    rm -f "$T33_POST" "$T33_PRE" 2>/dev/null || true
    actual=1
    [ "$T33_OUT" = "OK" ] && actual=0
    run_test T33 "vault-audit X8 provenance: post-cutoff prov-less claim flagged once; pre-cutoff twin clean" "$actual" 0
fi

# ---------- T34/T35: invest workflow scripts parse in the HARNESS dialect ----------
# Workflow scripts run inside an async-function wrapper (top-level return + await
# are legal there but NOT in plain ESM, so raw `node --check` is the wrong parser).
# This parses the body via the AsyncFunction constructor with the harness globals
# declared -- the same dialect the Workflow tool uses. Parse-only; never executes.
check_workflow_esm() {
    local src="$1"
    if [ ! -f "$src" ]; then
        return 3  # script missing
    fi
    node -e '
const fs = require("fs");
let src = fs.readFileSync(process.argv[1], "utf8");
src = src.replace(/^export const meta/m, "const meta");
const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
new AsyncFunction("args","agent","parallel","pipeline","phase","log","budget","workflow", src);
' "$src" >/dev/null 2>&1
    return $?
}
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T34" ]; then
    set +e
    check_workflow_esm "$VAULT_ROOT/.claude/workflows/invest-research.js"
    actual=$?
    set -e
    run_test T34 "invest-research.js parses in Workflow-harness dialect (AsyncFunction, parse-only)" "$actual" 0
fi
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T35" ]; then
    set +e
    check_workflow_esm "$VAULT_ROOT/.claude/workflows/invest-verify.js"
    actual=$?
    set -e
    run_test T35 "invest-verify.js parses in Workflow-harness dialect (AsyncFunction, parse-only)" "$actual" 0
fi

# ---------- T36: score-outcomes.py fixture Brier lock (RATING_PROB_MAP freeze, R1) ----------
# Locks the pre-registered probability map by asserting exact Brier values on the
# synthetic fixture. Any drift in RATING_PROB_MAP, the exclusion rules (HOLD/NR),
# the legacy-stratum mapping, or the short-row parser changes these numbers.
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T36" ]; then
    set +e
    T36_OUT=$(python "$VAULT_ROOT/tools/score-outcomes.py" \
        --fixture "$VAULT_ROOT/tools/test-fixtures/calibration-fixture.md" \
        --dry-run --json 2>/dev/null | python -c "
import json, sys
r = json.load(sys.stdin)
p = r['pooled']; s = r['stratified']; rb = r['rollback']
ok = (p['new']['brier'] == 0.223 and p['new']['n'] == 5
      and p['shadow']['brier'] == 0.173125 and p['shadow']['n'] == 4
      and s['sequential']['new']['brier'] == 0.200833
      and s['dw']['sufficient'] is False
      and s['sequential-legacy']['new']['n'] == 1
      and rb['realized_at_3mo'] == 6 and rb['armed'] is False
      and len(r['backfilled']) == 0)
print('OK' if ok else 'BAD ' + json.dumps([p, rb['realized_at_3mo']]))
" 2>/dev/null)
    set -e
    actual=1
    [ "$T36_OUT" = "OK" ] && actual=0
    run_test T36 "score-outcomes fixture Brier lock: pooled 0.223/0.173125, stratified, realized=6, no backfill" "$actual" 0
fi

# ---------- T37/T38: spark vNEXT workflow scripts parse in the HARNESS dialect ----------
# Same check_workflow_esm() helper as T34/T35 (AsyncFunction wrapper with harness
# globals declared; parse-only, never executes).
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T37" ]; then
    set +e
    check_workflow_esm "$VAULT_ROOT/.claude/workflows/spark-sweep.js"
    actual=$?
    set -e
    run_test T37 "spark-sweep.js parses in Workflow-harness dialect (AsyncFunction, parse-only)" "$actual" 0
fi
if [ "$SELECT" = "all" ] || [ "$SELECT" = "T38" ]; then
    set +e
    check_workflow_esm "$VAULT_ROOT/.claude/workflows/spark-verify.js"
    actual=$?
    set -e
    run_test T38 "spark-verify.js parses in Workflow-harness dialect (AsyncFunction, parse-only)" "$actual" 0
fi

# ---------- Summary ----------

echo ""
echo "==================== RESULTS ===================="
for r in "${RESULTS[@]}"; do
    echo "$r"
done
echo "================================================="
echo "PASSED: $PASSED   FAILED: $FAILED"
echo "================================================="

[ "$FAILED" -eq 0 ] && exit 0 || exit 1
