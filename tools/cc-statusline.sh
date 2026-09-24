#!/usr/bin/env bash
# Claude Code status line (Osanwe). Reads session JSON on stdin.
#
# THIS FILE IS AUTHORITATIVE. ~/.claude/cc-statusline.sh is a 2-line exec pointer at it.
# Do not restore a second copy there -- two files, one live and one reviewed, diverge by
# construction (the generator-rot pattern this vault has already paid for once).
#
# The context-bar glyphs below are pre-existing operator content, preserved byte-exact
# rather than ASCII-fied, because silently changing the operator's display is worse than
# a Pattern-22 nit in a file he authored. Everything ADDED by an agent here is ASCII.
# BOUNDED READ, corrected 2026-09-06. `input=$(cat)` blocks forever whenever Claude Code
# spawns the statusline without closing stdin, and with refreshInterval 5 that leaked one
# permanently-blocked bash per session every 5 seconds -- 194 orphans holding 1.5 GB after
# two days, at ~0% CPU, so nothing looked wrong except the RAM. The orphans also held this
# script open, which is why the file could not be rewritten until they were killed.
# `read -t` bounds the wait and STILL assigns whatever already arrived, so the normal path
# (JSON then EOF) is byte-identical and only the hang case changes. `|| true` because read
# returns non-zero on both timeout and EOF-without-delimiter, which is the success path
# here; JSON contains no NUL, so -d '' means "read until EOF".
IFS= read -r -d '' -t 3 input || true

# Degrade gracefully if jq is missing: minimal line, never error.
if ! command -v jq >/dev/null 2>&1; then
  m=$(printf '%s' "$input" | grep -o '"display_name":"[^"]*"' | head -1 | cut -d'"' -f4)
  echo "[${m:-Claude}]"; exit 0
fi

RESET=$'\033[0m'; BOLD=$'\033[1m'; DIM=$'\033[90m'
CYAN=$'\033[36m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; RED=$'\033[31m'; MAUVE=$'\033[35m'; BLUE=$'\033[34m'

MODEL=$(printf '%s' "$input" | jq -r '.model.display_name // "Claude"')
DIR=$(printf '%s'   "$input" | jq -r '.workspace.current_dir // .cwd // ""')
DNAME="${DIR##*[/\\]}"; [ -z "$DNAME" ] && DNAME="$DIR"
PCT=$(printf '%s'   "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1); PCT=${PCT:-0}
COST=$(printf '%s'  "$input" | jq -r '.cost.total_cost_usd // 0')
CTXWIN=$(printf '%s' "$input" | jq -r '.context_window.context_window_size // 0')
SID=$(printf '%s'   "$input" | jq -r '.session_id // "default"')
FIVE_H=$(printf '%s' "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
WEEK=$(printf '%s'   "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')

# git info cached 5s per session (avoids lag in large repos)
CACHE="${TMPDIR:-/tmp}/cc-statusline-git-$SID"; stale=1
if [ -f "$CACHE" ]; then
  mt=$(stat -c %Y "$CACHE" 2>/dev/null || stat -f %m "$CACHE" 2>/dev/null || echo 0)
  [ $(( $(date +%s) - mt )) -le 5 ] && stale=0
fi
if [ "$stale" -eq 1 ]; then
  if git rev-parse --git-dir >/dev/null 2>&1; then
    b=$(git branch --show-current 2>/dev/null)
    s=$(git diff --cached --numstat 2>/dev/null | wc -l | tr -d ' ')
    m=$(git diff --numstat 2>/dev/null | wc -l | tr -d ' ')
    printf '%s|%s|%s' "$b" "$s" "$m" > "$CACHE"
  else printf '||' > "$CACHE"; fi
fi
IFS='|' read -r BRANCH STAGED MODIFIED < "$CACHE"
STAGED=${STAGED:-0}; MODIFIED=${MODIFIED:-0}

# context bar
# CORRECTED 2026-09-02. Claude Code's own docs: "The status line's used_percentage always
# measures against the model's FULL context window, so once CLAUDE_CODE_AUTO_COMPACT_WINDOW
# is set, that percentage no longer indicates when compaction will run." Every lane here
# now sets that variable, so the raw percentage was quietly answering the wrong question --
# it would read ~75% at the exact moment compaction had already fired.
# CORRECTED AGAIN 2026-09-02, after the first correction caused a WORSE failure.
# Making the headline number "progress toward compaction" was arithmetically right and
# operationally wrong: it runs ~1.33x the window figure, so it read 94% while 29% of a
# 1M window was still free. The operator reasonably read that as nearly-full and
# hand-compacted every session at ~710k -- 40k short of the 750k trigger -- so
# auto-compact never got to fire and looked broken. A gauge that provokes the very
# intervention it exists to predict is a bad gauge.
# So: the headline number and the bar are the SHARE OF THE WINDOW USED, which is what
# "context %" means everywhere else. The compaction point is shown as a fixed marker on
# that same scale, and only the COLOUR tracks proximity to it.
CPCT="$PCT"; FIREPCT=""
if [ -n "$CLAUDE_CODE_AUTO_COMPACT_WINDOW" ] && [ "$CTXWIN" -gt 0 ] 2>/dev/null; then
  # Claude Code reserves a fixed, non-configurable buffer inside the declared window
  # (observed 33k on every lane), so compaction fires that much before the window itself.
  _used=$(( PCT * CTXWIN / 100 ))
  _fire=$(( CLAUDE_CODE_AUTO_COMPACT_WINDOW - 33000 ))
  [ "$_fire" -lt 1000 ] && _fire=$CLAUDE_CODE_AUTO_COMPACT_WINDOW
  CPCT=$(( _used * 100 / _fire ))          # proximity to the trigger -- COLOUR ONLY
  [ "$CPCT" -gt 999 ] && CPCT=999
  # Rounded, not truncated: qwen's trigger is 59.997% of its window and truncation
  # printed "compact 59%" for a lane the operator deliberately set to 60%.
  FIREPCT=$(( (_fire * 200 / CTXWIN + 1) / 2 ))   # the trigger, as a share of the window
fi
# RED is reserved for OVERDUE -- past the trigger without having fired. That is the only
# state that genuinely needs a human. Approaching the trigger is routine and is amber.
if   [ "$CPCT" -gt 102 ]; then BARC="$RED"
elif [ "$CPCT" -ge 90 ];  then BARC="$YELLOW"
else BARC="$GREEN"; fi
PCT_BAR="$PCT"
FILLED=$((PCT_BAR/10)); [ "$FILLED" -gt 10 ] && FILLED=10; EMPTY=$((10-FILLED))
printf -v F "%${FILLED}s" ""; printf -v E "%${EMPTY}s" ""
BAR="${F// /█}${E// /░}"

# --- lane chip (launcher modes only) -------------------------------------------------
# Renders ONLY when the launcher set CLAUDE_LANE_MODE, so ordinary sessions and non-vault
# projects are untouched. The model name is read from the SSOT at render time, never from
# an env var: a mid-session `delegate.py --use <tag>` swap must not leave the chip lying.
CHIP=""
if [ -n "$CLAUDE_LANE_MODE" ] && [ "$CLAUDE_LANE_MODE" != "sub" ]; then
  if [ "$CLAUDE_LANE_MODE" = "muse" ] || [ "$CLAUDE_LANE_MODE" = "opencode" ]; then
    # The Muse lane is NOT the Ollama lane. Reading local-lane.json here would print the
    # LOCAL model's name during an OpenCode Go session -- a statusline that lies. That is
    # exactly why mode 2 previously set no CLAUDE_LANE_MODE at all and rendered no chip.
    # Take the id the launcher actually pinned, and skip lane-state entirely: ARMED/WARMING
    # describe the Ollama lane's readiness and mean nothing here.
    LMODEL="${CLAUDE_LANE_MODEL:-muse}"
    TAG="MUSE"; CC="$GREEN"
    if [ "$CLAUDE_LANE_MODE" = "opencode" ]; then
      case "$CLAUDE_LANE_POOL" in
        go) TAG="GO" ;;
        free) TAG="ZEN FREE" ;;
        *) TAG="ZEN PAID" ;;
      esac
    fi
  else
    LANE_JSON="/path/to/vault/config/local-lane.json"
    LANE_STATE_FILE="/path/to/vault/.claude/state/lane-state"
    LMODEL=""
    [ -r "$LANE_JSON" ] && LMODEL=$(jq -r '.model // empty' "$LANE_JSON" 2>/dev/null)
    [ -z "$LMODEL" ] && LMODEL="lane"
    LSTATE=""
    [ -r "$LANE_STATE_FILE" ] && LSTATE=$(cut -d'|' -f1 < "$LANE_STATE_FILE" 2>/dev/null)
    case "$CLAUDE_LANE_MODE" in
      hybrid) TAG="HYB" ;;
      local)  TAG="LOCAL" ;;
      *)      TAG="LANE" ;;
    esac
    case "$LSTATE" in
      ARMED)    CC="$GREEN" ;;
      WARMING)  CC="$YELLOW"; TAG="${TAG}*" ;;
      DISARMED) CC="$RED";    TAG="${TAG}!" ;;
      *)        CC="$DIM" ;;
    esac
  fi
  CHIP=" ${DIM}|${RESET} ${CC}${TAG} ${LMODEL}${RESET}"
fi

# line 1
L1="${CYAN}${BOLD}${MODEL}${RESET} ${DIM}|${RESET} ${BLUE}${DNAME}${RESET}${CHIP}"
if [ -n "$BRANCH" ]; then
  L1="${L1} ${DIM}|${RESET} ${MAUVE}${BRANCH}${RESET}"
  [ "$STAGED"  -gt 0 ] 2>/dev/null && L1="${L1} ${GREEN}+${STAGED}${RESET}"
  [ "$MODIFIED" -gt 0 ] 2>/dev/null && L1="${L1} ${YELLOW}~${MODIFIED}${RESET}"
fi

# line 2
# Cost comes from Claude Code's internal ANTHROPIC price table. On the Muse lane (an
# OpenCode Go contributor route) and the fully-local lane it is not merely imprecise -- it
# is a confident dollar figure for tokens Anthropic never billed. Show the DECLARED CONTEXT
# WINDOW instead, which is the number that actually governs those sessions: if it does not
# read 1049k on lane 2 or 262k on lane 3, the --settings overlay did not take effect, and
# that is the fastest signal available that compaction is about to misbehave.
# The bar and its leading number are the share of the WINDOW used; "(compact N%)" marks
# the trigger on that same scale, and the colour is what tracks proximity to it.
L2="${BARC}${BAR}${RESET} ${PCT}%"
if [ -n "$FIREPCT" ]; then
  if [ "$CPCT" -gt 102 ]; then
    # Past the trigger and still running: auto-compact did NOT fire. Say so outright
    # rather than showing a number the operator has to do arithmetic on.
    L2="${L2} ${RED}compact OVERDUE (${FIREPCT}%)${RESET}"
  else
    L2="${L2} ${DIM}(compact ${FIREPCT}%)${RESET}"
  fi
fi
case "$CLAUDE_LANE_MODE" in
  muse|opencode|local)
    # Cost comes from Claude Code's internal ANTHROPIC price table, so on an OpenCode Go
    # contributor route and a local model it is a confident dollar figure for tokens
    # Anthropic never billed. Show the declared window instead: if it does not read the expected
    # value, the --settings overlay did not apply, which is the fastest available warning
    # that compaction is about to misbehave.
    if [ -n "$CTXWIN" ] && [ "$CTXWIN" != "null" ] && [ "$CTXWIN" -gt 0 ] 2>/dev/null; then
      L2="${L2} ${DIM}|${RESET} ${DIM}win $((CTXWIN / 1000))k${RESET}"
    fi
    ;;
  *)
    COSTF=$(printf '$%.2f' "$COST" 2>/dev/null || echo '$0.00')
    L2="${L2} ${DIM}|${RESET} ${YELLOW}${COSTF}${RESET}"
    ;;
esac
rl=""
if [ -n "$FIVE_H" ]; then f=$(printf '%.0f' "$FIVE_H" 2>/dev/null || echo 0)
  if [ "$f" -ge 90 ]; then c="$RED"; elif [ "$f" -ge 70 ]; then c="$YELLOW"; else c="$GREEN"; fi
  rl="${c}5h ${f}%${RESET}"; fi
if [ -n "$WEEK" ]; then w=$(printf '%.0f' "$WEEK" 2>/dev/null || echo 0)
  if [ "$w" -ge 90 ]; then c="$RED"; elif [ "$w" -ge 70 ]; then c="$YELLOW"; else c="$GREEN"; fi
  rl="${rl:+$rl ${DIM}|${RESET} }${c}7d ${w}%${RESET}"; fi
[ -n "$rl" ] && L2="${L2} ${DIM}|${RESET} ${rl}"

printf '%b\n' "$L1"
printf '%b\n' "$L2"