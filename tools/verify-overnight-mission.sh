#!/usr/bin/env bash
# verify-overnight-mission.sh -- emits one PASS/FAIL line per overnight-mission HALT gate.
# Run from repo root:  bash tools/verify-overnight-mission.sh
# Gates: ENCYCLOPEDIA_FILES MEMORY_INDEX CONSOLIDATE_SKILL CONSOLIDATE_MIRROR
#        CONSOLIDATOR_MODULE CONSOLIDATOR_TESTS_FILE CONSOLIDATOR_TESTS PLAYBOOKS
#        HOT_MD_UPDATED VAULT_AUDIT GIT_CLEAN  + final STATUS_MD line.
# Worker prose is INSUFFICIENT for the HALT gate; only this script's literal
# paired Bash tool_result output counts.

ROOT="/path/to/vault"
MEM="${HOME}/.claude/projects/C--vault-rebuild/memory"
STATUS="${ROOT}/.claude/state/overnight-status.md"
cd "$ROOT" 2>/dev/null || { echo "FATAL: cannot cd $ROOT"; exit 1; }

allpass=1
check() {  # $1=name  $2=0(pass)/1(fail)  $3=detail
  if [ "$2" = "0" ]; then
    echo "$1: PASS ($3)"
  else
    echo "$1: FAIL ($3)"
    allpass=0
  fi
}

# 1. ENCYCLOPEDIA_FILES -- >=50 new reference memory files in the vault-rebuild memory dir
enc=$(ls "$MEM"/hook_*.md "$MEM"/tool_*.md "$MEM"/agent_*.md "$MEM"/skill_*.md 2>/dev/null | wc -l | tr -d ' ')
if [ "${enc:-0}" -ge 50 ]; then check ENCYCLOPEDIA_FILES 0 "${enc} files (floor 50)"; else check ENCYCLOPEDIA_FILES 1 "${enc} files (<50)"; fi

# 2. MEMORY_INDEX -- 4 new sections appended to MEMORY.md
midx=$(grep -c "VaultRoot Vault --" "$MEM/MEMORY.md" 2>/dev/null | tr -d ' ')
if [ "${midx:-0}" -ge 4 ]; then check MEMORY_INDEX 0 "${midx} new sections"; else check MEMORY_INDEX 1 "${midx} sections (<4)"; fi

# 3. CONSOLIDATE_SKILL
if [ -s ".claude/skills/consolidate/SKILL.md" ]; then check CONSOLIDATE_SKILL 0 "present"; else check CONSOLIDATE_SKILL 1 "missing/empty"; fi

# 4. CONSOLIDATE_CANON (.agents/skills is the canonical tree; .claude copy is sync-generated)
if [ -s ".agents/skills/consolidate/SKILL.md" ]; then check CONSOLIDATE_MIRROR 0 "present"; else check CONSOLIDATE_MIRROR 1 "missing/empty"; fi

# 5. CONSOLIDATOR_MODULE -- class Consolidator present
if grep -q "class Consolidator" tools/consolidator.py 2>/dev/null; then check CONSOLIDATOR_MODULE 0 "class Consolidator"; else check CONSOLIDATOR_MODULE 1 "no class Consolidator"; fi

# 6. CONSOLIDATOR_TESTS_FILE
if [ -s "tools/test-consolidator.py" ]; then check CONSOLIDATOR_TESTS_FILE 0 "present"; else check CONSOLIDATOR_TESTS_FILE 1 "missing/empty"; fi

# 7. CONSOLIDATOR_TESTS -- run the suite; PASS only on exit 0
tout=$(python tools/test-consolidator.py 2>&1)
trc=$?
tsum=$(printf "%s\n" "$tout" | grep -E "^Result:" | head -1)
if [ "$trc" -eq 0 ]; then check CONSOLIDATOR_TESTS 0 "${tsum:-no-summary}"; else check CONSOLIDATOR_TESTS 1 "exit=${trc} ${tsum}"; fi

# 8. PLAYBOOKS -- 3..8 playbook files
pb=$(ls wiki/playbooks/*-playbook.md 2>/dev/null | wc -l | tr -d ' ')
if [ "${pb:-0}" -ge 3 ] && [ "${pb:-0}" -le 8 ]; then check PLAYBOOKS 0 "${pb} playbooks (3-8)"; else check PLAYBOOKS 1 "${pb} playbooks (need 3-8)"; fi

# 9. HOT_MD_UPDATED -- digest inserted
if grep -q "Consolidation Digest" wiki/hot.md 2>/dev/null; then check HOT_MD_UPDATED 0 "digest present"; else check HOT_MD_UPDATED 1 "no digest"; fi

# 10. VAULT_AUDIT -- score>=95 AND gate.count==0
audit=$(python tools/vault-audit.py --json 2>/dev/null)
score=$(printf "%s" "$audit" | python -c "import sys,json;\
d=json.load(sys.stdin);print(d.get('score',-1))" 2>/dev/null)
gate=$(printf "%s" "$audit" | python -c "import sys,json;\
d=json.load(sys.stdin);print(d.get('tiers',{}).get('gate',{}).get('count',-1))" 2>/dev/null)
if [ "${score:-0}" -ge 95 ] && [ "${gate:--1}" -eq 0 ]; then check VAULT_AUDIT 0 "score=${score} gate=${gate}"; else check VAULT_AUDIT 1 "score=${score} gate=${gate}"; fi

# 11. GIT_CLEAN -- mission-owned paths fully committed (pre-existing untracked cruft is out of scope)
dirty=$(git status --porcelain -- \
  wiki/playbooks tools/consolidator.py tools/test-consolidator.py \
  tools/verify-overnight-mission.sh .claude/skills/consolidate \
  .agents/skills/consolidate wiki/hot.md 2>/dev/null | wc -l | tr -d ' ')
if [ "${dirty:-1}" -eq 0 ]; then check GIT_CLEAN 0 "mission paths committed"; else check GIT_CLEAN 1 "${dirty} uncommitted mission path(s)"; fi

# Final STATUS_MD line (HALT gate also requires the literal "STATUS_MD: MISSION_COMPLETE")
echo "---"
if grep -q "MISSION_COMPLETE" "$STATUS" 2>/dev/null; then
  echo "STATUS_MD: MISSION_COMPLETE"
else
  echo "STATUS_MD: MISSION_INCOMPLETE"
  allpass=0
fi

if [ "$allpass" -eq 1 ]; then
  echo "ALL_GATES: PASS"
  exit 0
else
  echo "ALL_GATES: FAIL"
  exit 1
fi
