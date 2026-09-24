#!/usr/bin/env python3
"""run-share.py -- frontier cost attribution for a Claude Code session.

GATE-B: gate-b-orchestration-economics-2026-08-17.

WHY THIS EXISTS. Nothing in the vault could answer "what did THIS run cost the
frontier". The pieces that looked like they could all lie:

  - claudewatch get_cost_attribution misses the subagent fleet entirely
    (it reported $<amount> for a session whose own recent-sessions row said $<amount>).
  - `isSidechain` is ALWAYS false in these transcripts -- subagent turns are not in
    the session file at all, they live in <session>/subagents/agent-*.jsonl.
  - Summing message.usage naively overstates by 12-50x, because streaming writes
    one row per content block and every row repeats the SAME usage object.
  - delegate.py's orchestrator-share line reads kind:"local-share" rows that no
    producer ever wrote -- its only input was a suite fixture (share_pct 3.4).

THE COST LAW (the thing the old plan got wrong):

    cost = cache_read + 12.5*cache_creation + 50*output
    and   cache_read = SUM over turns of (resident context)

So the bill is turn-count x residency. Bytes admitted to context are charged ONCE
as cache_creation (~7% of the bill) and then re-charged on every later turn. The
four classes differ ~50x in price and are therefore NEVER summed into one number
here; `weighted` is the only blended figure and it prints its own formula.

WEIGHTS are relative price ratios, not dollars (input:cache_read = 10:1,
output:cache_read = 50:1, cache_creation:cache_read = 12.5:1). Absolute dollars are
deliberately not computed: claudewatch prices every session at Sonnet rates
regardless of the model actually used, so any dollar figure derived from it is ~5x
low for an Opus session. Ratios hold; dollars do not.

NO SHARE METRIC BY DEFAULT. frontier/(frontier+worker) mixes currencies -- it
excluded prompt re-read on the frontier side while including qwen's re-evaluated
prompt on the worker side -- and it is MAXIMISED BY WASTE: adding useless worker
legs lowers it while making the run more expensive. Worker tokens are reported
standalone, with their convention printed. --share prints it anyway, labelled.

Usage:
  python tools/run-share.py                      # latest session, per-skill table
  python tools/run-share.py --session <8-char>   # a specific session
  python tools/run-share.py --skill invest       # one skill's window
  python tools/run-share.py --all-sessions       # system-wide per-skill rollup
  python tools/run-share.py --json
  python tools/run-share.py --emit-ledger        # write the real local-share row
"""
import argparse
import glob
import json
import os
import sys

PROJECT_DIR = os.path.expanduser(
    r"~\.claude\projects\C--VaultRoot")
STATE_DIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), ".claude", "state")

# Relative price ratios vs cache_read. See module docstring: ratios, never dollars.
W_CACHE_READ = 1.0
W_CACHE_CREATE = 12.5
W_OUTPUT = 50.0
W_INPUT = 10.0


def _blank():
    return {"turns": 0, "input": 0, "cc": 0, "cr": 0, "out": 0, "think": 0}


def _add(acc, u):
    acc["turns"] += 1
    acc["input"] += u.get("input_tokens", 0) or 0
    acc["cc"] += u.get("cache_creation_input_tokens", 0) or 0
    acc["cr"] += u.get("cache_read_input_tokens", 0) or 0
    acc["out"] += u.get("output_tokens", 0) or 0
    det = u.get("output_tokens_details") or {}
    acc["think"] += det.get("thinking_tokens", 0) or 0


def weighted(acc):
    return (acc["cr"] * W_CACHE_READ + acc["cc"] * W_CACHE_CREATE
            + acc["out"] * W_OUTPUT + acc["input"] * W_INPUT)


def _iter_assistant(path):
    """Yield (dedup_key, record) for assistant rows carrying usage.

    Dedup key is message.id when present (one logical API response), else
    requestId. Without this the same usage object is counted once per streamed
    content block -- measured 60% duplicate rows, 50x main-loop inflation.
    """
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return
    with fh:
        for line in fh:
            if '"assistant"' not in line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("type") != "assistant":
                continue
            msg = r.get("message") or {}
            u = msg.get("usage") or {}
            if not u:
                continue
            key = msg.get("id") or r.get("requestId")
            if not key:
                continue
            yield key, r, u


def session_paths(session_arg):
    files = sorted(glob.glob(os.path.join(PROJECT_DIR, "*.jsonl")),
                   key=os.path.getmtime)
    if not files:
        return []
    if session_arg in (None, "latest"):
        return [files[-1]]
    hits = [f for f in files
            if os.path.basename(f).startswith(session_arg)]
    return hits


def scan_main(path):
    """Per-skill main-loop totals + per-turn timeline for subagent attribution."""
    per_skill = {}
    timeline = []  # (ts, skill) at each attributed turn
    seen = set()
    for key, r, u in _iter_assistant(path):
        if key in seen:
            continue
        seen.add(key)
        skill = r.get("attributionSkill") or "(unattributed)"
        per_skill.setdefault(skill, _blank())
        _add(per_skill[skill], u)
        ts = r.get("timestamp")
        if ts:
            timeline.append((ts, skill))
    timeline.sort()
    return per_skill, timeline


def scan_subagents(session_path, timeline):
    """Walk <session>/subagents/*.jsonl -- the arm isSidechain and claudewatch miss.

    Each agent is attributed to the skill that was active in the main loop at the
    agent's first timestamp. Attribution is best-effort by design: if the main
    loop was unattributed then, so is the agent.
    """
    base = session_path[:-len(".jsonl")]
    sub_dir = os.path.join(base, "subagents")
    fleet = {}      # agentType -> acc + dispatch count
    by_skill = {}   # skill -> acc
    if not os.path.isdir(sub_dir):
        return fleet, by_skill, 0
    n = 0
    for meta_path in sorted(glob.glob(os.path.join(sub_dir, "*.meta.json"))):
        jl = meta_path[:-len(".meta.json")] + ".jsonl"
        if not os.path.exists(jl):
            continue
        try:
            meta = json.load(open(meta_path, encoding="utf-8"))
        except (OSError, ValueError):
            meta = {}
        atype = meta.get("agentType") or "(unknown)"
        acc = _blank()
        first_ts = None
        seen = set()
        for key, r, u in _iter_assistant(jl):
            if key in seen:
                continue
            seen.add(key)
            _add(acc, u)
            if first_ts is None:
                first_ts = r.get("timestamp")
        if not acc["turns"]:
            continue
        n += 1
        f = fleet.setdefault(atype, dict(_blank(), dispatches=0))
        f["dispatches"] += 1
        for k in ("turns", "input", "cc", "cr", "out", "think"):
            f[k] += acc[k]
        skill = "(unattributed)"
        if first_ts and timeline:
            prior = [s for ts, s in timeline if ts <= first_ts]
            if prior:
                skill = prior[-1]
        s = by_skill.setdefault(skill, _blank())
        for k in ("turns", "input", "cc", "cr", "out", "think"):
            s[k] += acc[k]
    return fleet, by_skill, n


def worker_totals(run_prefix=None):
    """Worker (local model) tokens, STANDALONE -- never a denominator with frontier.

    Convention printed alongside: relay rows carry prompt_tokens as a CUMULATIVE
    re-evaluated prompt across turns (the local analogue of cache_read), so it is
    not commensurable with a frontier figure that excludes cache_read.
    """
    tot = {"prompt_reeval": 0, "out": 0, "legs": 0}
    for p in sorted(glob.glob(os.path.join(STATE_DIR, "delegate-runs-*.jsonl"))):
        try:
            fh = open(p, encoding="utf-8", errors="replace")
        except OSError:
            continue
        with fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("kind") != "relay":
                    continue
                if run_prefix and not str(r.get("run", "")).startswith(run_prefix):
                    continue
                tot["legs"] += 1
                tot["prompt_reeval"] += r.get("prompt_tokens") or 0
                tot["out"] += r.get("out_tokens") or 0
    return tot


def fmt_row(name, acc, width=26):
    w = weighted(acc) / 1e6
    resid = acc["cr"] // acc["turns"] if acc["turns"] else 0
    thinkpct = (100.0 * acc["think"] / acc["out"]) if acc["out"] else 0.0
    return ("%-*s %6d %10d %6.1f%% %11d %13d %9.1f %10d"
            % (width, name[:width], acc["turns"], acc["out"], thinkpct,
               acc["cc"], acc["cr"], w, resid))


HEAD = ("%-26s %6s %10s %7s %11s %13s %9s %10s"
        % ("attribution", "turns", "output", "think", "cache_cr", "cache_read",
           "wtd(M)", "resid/turn"))


def report(session_paths_list, skill_filter, want_json, all_sessions):
    per_skill = {}
    fleet = {}
    fleet_by_skill = {}
    n_sub = 0
    for sp in session_paths_list:
        ps, timeline = scan_main(sp)
        for k, v in ps.items():
            acc = per_skill.setdefault(k, _blank())
            for f in ("turns", "input", "cc", "cr", "out", "think"):
                acc[f] += v[f]
        fl, fbs, n = scan_subagents(sp, timeline)
        n_sub += n
        for k, v in fl.items():
            f = fleet.setdefault(k, dict(_blank(), dispatches=0))
            f["dispatches"] += v["dispatches"]
            for x in ("turns", "input", "cc", "cr", "out", "think"):
                f[x] += v[x]
        for k, v in fbs.items():
            acc = fleet_by_skill.setdefault(k, _blank())
            for x in ("turns", "input", "cc", "cr", "out", "think"):
                acc[x] += v[x]

    if skill_filter:
        per_skill = {k: v for k, v in per_skill.items() if k == skill_filter}
        fleet_by_skill = {k: v for k, v in fleet_by_skill.items()
                          if k == skill_filter}

    wk = worker_totals()

    if want_json:
        out = {
            "sessions": [os.path.basename(p)[:8] for p in session_paths_list],
            "weights": {"cache_read": W_CACHE_READ,
                        "cache_creation": W_CACHE_CREATE,
                        "output": W_OUTPUT, "input": W_INPUT,
                        "note": "relative price ratios, not dollars"},
            "main_loop": {k: dict(v, weighted=weighted(v)) for k, v in per_skill.items()},
            "fleet_by_agent": {k: dict(v, weighted=weighted(v)) for k, v in fleet.items()},
            "fleet_by_skill": {k: dict(v, weighted=weighted(v)) for k, v in fleet_by_skill.items()},
            "subagent_dispatches": n_sub,
            "worker": dict(wk, convention="prompt_reeval is cumulative "
                           "re-evaluated prompt (local analogue of cache_read); "
                           "NOT commensurable with a frontier figure that "
                           "excludes cache_read. Reported standalone."),
        }
        print(json.dumps(out, indent=1, sort_keys=True))
        return 0

    scope = ("ALL %d sessions" % len(session_paths_list)) if all_sessions \
        else ", ".join(os.path.basename(p)[:8] for p in session_paths_list)
    print("run-share -- frontier attribution (%s)" % scope)
    print("cost law: weighted = cache_read + 12.5*cache_creation + 50*output"
          " + 10*input   [ratios, not dollars]")
    print()
    print("MAIN LOOP")
    print(HEAD)
    tot = _blank()
    for k, v in sorted(per_skill.items(), key=lambda kv: -weighted(kv[1])):
        print(fmt_row(k, v))
        for f in ("turns", "input", "cc", "cr", "out", "think"):
            tot[f] += v[f]
    print(fmt_row("-- main-loop total", tot))

    if fleet:
        print()
        print("SUBAGENT FLEET  (%d dispatches; the arm isSidechain and claudewatch"
              " both miss)" % n_sub)
        print("%-26s %6s %10s %7s %11s %13s %9s %10s"
              % ("agentType", "disp", "output", "think", "cache_cr",
                 "cache_read", "wtd(M)", "per-disp(M)"))
        ftot = _blank()
        for k, v in sorted(fleet.items(), key=lambda kv: -weighted(kv[1])):
            w = weighted(v) / 1e6
            per = w / v["dispatches"] if v["dispatches"] else 0.0
            tp = (100.0 * v["think"] / v["out"]) if v["out"] else 0.0
            print("%-26s %6d %10d %6.1f%% %11d %13d %9.1f %10.2f"
                  % (k[:26], v["dispatches"], v["out"], tp, v["cc"], v["cr"],
                     w, per))
            for f in ("turns", "input", "cc", "cr", "out", "think"):
                ftot[f] += v[f]
        print("%-26s %6d %10d %6s %11d %13d %9.1f"
              % ("-- fleet total", n_sub, ftot["out"], "", ftot["cc"],
                 ftot["cr"], weighted(ftot) / 1e6))

    print()
    unattr = per_skill.get("(unattributed)")
    if unattr:
        pct = 100.0 * weighted(unattr) / weighted(tot) if weighted(tot) else 0.0
        print("UNATTRIBUTED main-loop work: %.1f%% of frontier weighted cost "
              "(%d turns)." % (pct, unattr["turns"]))
        print("  Session work outside any skill. No per-skill change touches it;"
              " residency + turn discipline is the only lever here.")
    print("WORKER (local, standalone -- never a denominator with the above):"
          " %d leg(s), %d output, %d prompt-re-eval"
          % (wk["legs"], wk["out"], wk["prompt_reeval"]))
    print("  prompt-re-eval is the local analogue of cache_read; it is NOT"
          " commensurable with a frontier number that excludes cache_read.")
    return 0


def emit_ledger(session_paths_list):
    """Write the REAL kind:'local-share' row. Until now the only such rows in the
    ledger were suite fixtures (test-relay.py, run 't5s-cnt', share_pct 3.4), which
    delegate.py then read back and printed as if measured."""
    per_skill = {}
    for sp in session_paths_list:
        ps, _ = scan_main(sp)
        for k, v in ps.items():
            acc = per_skill.setdefault(k, _blank())
            for f in ("turns", "input", "cc", "cr", "out", "think"):
                acc[f] += v[f]
    tot = _blank()
    for v in per_skill.values():
        for f in ("turns", "input", "cc", "cr", "out", "think"):
            tot[f] += v[f]
    wk = worker_totals()
    sid = os.path.basename(session_paths_list[-1])[:8]
    row = {
        "ts": "run-share",
        "kind": "local-share",
        "run": "rs-" + sid,
        "frontier_weighted": int(weighted(tot)),
        "frontier_turns": tot["turns"],
        "mean_resident_context": (tot["cr"] // tot["turns"]) if tot["turns"] else 0,
        "frontier_output": tot["out"],
        "worker_output": wk["out"],
        "worker_legs": wk["legs"],
        "source": "run-share.py",
    }
    # Ledger filenames follow the repo's LOCAL-date convention (delegate.py:235)
    # so rows land in the file the readers glob. Transcript WINDOWING is UTC --
    # the two conventions are deliberate and must not be conflated.
    import datetime
    day = datetime.datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(STATE_DIR, "delegate-runs-%s.jsonl" % day)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
    print("appended local-share row to %s" % path)
    return 0


def current_context(path):
    """Resident context on the most recent turn of the live session.

    This is the number U1 gates on. A skill cannot read its own context size --
    the harness exposes it to the statusline, not to the model -- but the
    transcript is written live, so the last turn's cache_read IS the resident
    prefix that every subsequent turn will re-pay.
    """
    last = 0
    for _key, _r, u in _iter_assistant(path):
        cr = u.get("cache_read_input_tokens", 0) or 0
        if cr:
            last = cr
    return last


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default=None,
                    help="session id prefix, or 'latest' (default)")
    ap.add_argument("--skill", default=None,
                    help="filter to one attributionSkill")
    ap.add_argument("--all-sessions", action="store_true",
                    help="system-wide rollup across every session")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--emit-ledger", action="store_true",
                    help="append the real kind:'local-share' row")
    ap.add_argument("--current-context", action="store_true",
                    help="print resident context of the live session's last turn "
                         "(the U1 gate input) and exit 1 if over --budget")
    ap.add_argument("--budget", type=int, default=150000,
                    help="U1 residency budget for --current-context (default 150000)")
    args = ap.parse_args(argv)

    if args.all_sessions:
        paths = sorted(glob.glob(os.path.join(PROJECT_DIR, "*.jsonl")))
    else:
        paths = session_paths(args.session)
    if not paths:
        sys.stderr.write("run-share: no transcript found under %s\n" % PROJECT_DIR)
        return 2

    if args.current_context:
        cur = current_context(paths[-1])
        over = cur > args.budget
        print("resident context: %d tokens (budget %d) -- %s"
              % (cur, args.budget, "OVER" if over else "ok"))
        if over:
            print("Every turn from here re-pays this prefix. A heavy skill run "
                  "started at this residency costs roughly %.1fx the same run "
                  "started fresh. Recommend /clear and re-invoke."
                  % (max(1.0, cur / 55875.0)))
        return 1 if over else 0

    if args.emit_ledger:
        return emit_ledger(paths)
    return report(paths, args.skill, args.json, args.all_sessions)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
