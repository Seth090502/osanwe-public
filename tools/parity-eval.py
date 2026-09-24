#!/usr/bin/env python3
"""parity-eval -- grading harness for the local-worker parity instrument.

GATE-B: wiki/research/gates/gate-b-local-orchestration-program-2026-08-17.md.
RULE (pre-registered, frozen in the SAME commit as this file):
    wiki/research/parity-eval-rule-2026-08-17.md
Manifest (frozen, may NOT be narrowed to pass): tools/parity-cases/cases.json.

This tool GRADES; it never runs arms. Arms run in their own sessions
(worker: relay.py over the frozen missions, trigger=operator-phrase;
frontier: the frozen protocols under tools/parity-cases/frontier/).

  python tools/parity-eval.py --log-run --task T --arm worker|frontier \
         --run LABEL --status complete|abandoned [--note TXT]
  python tools/parity-eval.py --log-share --session LABEL --share-pct F \
         --source claudewatch|jsonl [--note TXT]
  python tools/parity-eval.py --grade --task T --arm worker|frontier \
         (--run RELAY_RUN | --claims FILE) [--slot 1|2]
  python tools/parity-eval.py --blind-pack --task url-harvest-brief
  python tools/parity-eval.py --status
  python tools/parity-eval.py --assemble [--date YYYY-MM-DD]

Grade records + run accounting live under .claude/state/parity/ (untracked
working state); --assemble writes the tracked results doc + JSON to
wiki/research/. Exit 0 ok | 1 grading impossible (missing inputs) | 3 usage.

Matcher (pre-registered; shared numeric core with relay_schema): a reference
claim MATCHES a candidate claim when (a) values agree -- first numeric token
of each side (comma/K/M/B/T/%/unit-word tolerant) equal within the task's
value_tol_rel, else casefold string equality -- AND (b) entity tokens agree
when the reference carries an entity, AND (c) metric token overlap (Jaccard
over lowercased alphanumeric tokens) is the best available >= 0.34. Second
pass (unique-value anchor): a still-missed reference matches a still-unused
candidate when they value-agree and the pairing is UNAMBIGUOUS in both
directions (exactly one such candidate for the ref, exactly one such missed
ref for the candidate) -- synonym phrasing must not sink an exact figure.
Extras (candidate claims matching nothing) NEVER penalize coverage;
extras-precision is a named non-binding number.
"""
import argparse
import base64
import hashlib
import io
import json
import os
import re
import sys
import time

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, os.path.join(TOOLS_DIR, "lib"))
import relay_schema  # noqa: E402

CASES = os.path.join(TOOLS_DIR, "parity-cases", "cases.json")
STATE = os.path.join(VAULT, ".claude", "state", "parity")
RUNS = os.path.join(STATE, "runs.json")
SHARES = os.path.join(STATE, "shares.json")
RELAY_TRACKED = os.path.join(VAULT, ".agents", "relay")


def _load(path, default):
    try:
        with io.open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (IOError, OSError, ValueError):
        return default


def _save(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="ascii", newline="\n") as fh:
        fh.write(relay_schema.dumps_ascii(obj))
    os.replace(tmp, path)


def manifest():
    m = _load(CASES, None)
    if not m:
        print("parity-eval: manifest missing at %s" % CASES, file=sys.stderr)
        sys.exit(1)
    return m


def task_spec(man, task):
    for t in man["tasks"]:
        if t["id"] == task:
            return t
    print("parity-eval: unknown task %r (manifest is FROZEN; no ad-hoc tasks)"
          % task, file=sys.stderr)
    sys.exit(3)


# ---------------------------------------------------------------- matching
_TOK = re.compile(r"[a-z0-9]+")


def _toks(s):
    return set(_TOK.findall((s or "").lower()))


def _first_num(s):
    """First numeric token in a value string; tolerant of unit words
    ('$9,301 million' -> 9301.0)."""
    m = relay_schema._NUM_RE.search(s)
    return relay_schema._parse_num(m.group(0)) if m else None


def _values_agree(ref_val, cand_val, tol):
    a, b = str(ref_val).strip(), str(cand_val).strip()
    if a.casefold() == b.casefold():
        return True
    na, nb = _first_num(a), _first_num(b)
    if na is None or nb is None:
        return False
    if na == nb:
        return True
    return na != 0 and abs(na - nb) <= abs(na) * tol


def match_claims(reference, candidates, tol):
    """Greedy best-match: each reference claim consumes at most one candidate.
    Returns (matched_pairs, missed_refs, extra_candidates)."""
    used = set()
    matched, missed = [], []
    for ref in reference:
        rtok = _toks(ref.get("metric"))
        rent = _toks(ref.get("entity"))
        best, best_j = None, 0.0
        for i, c in enumerate(candidates):
            if i in used:
                continue
            if not _values_agree(ref.get("value"), c.get("value"), tol):
                continue
            if rent and _toks(c.get("entity")) and not (rent & _toks(c.get("entity"))):
                continue
            ctok = _toks(c.get("metric")) | _toks(c.get("text"))
            j = (len(rtok & ctok) / float(len(rtok | ctok))) if (rtok or ctok) else 1.0
            if rtok and rtok <= ctok:
                j = max(j, 0.5)
            if j > best_j:
                best, best_j = i, j
        if best is not None and best_j >= 0.34:
            used.add(best)
            matched.append({"ref": ref, "cand_index": best})
        else:
            missed.append(ref)
    # Second pass: unique-value anchor (pre-registered; see module docstring).
    still_missed = []
    for ref in missed:
        rent = _toks(ref.get("entity"))
        agree = [i for i, c in enumerate(candidates)
                 if i not in used
                 and _values_agree(ref.get("value"), c.get("value"), tol)
                 and not (rent and _toks(c.get("entity"))
                          and not (rent & _toks(c.get("entity"))))]
        if len(agree) == 1:
            rivals = [r for r in missed if r is not ref and _values_agree(
                r.get("value"), candidates[agree[0]].get("value"), tol)]
            if not rivals:
                used.add(agree[0])
                matched.append({"ref": ref, "cand_index": agree[0],
                                "via": "unique-value"})
                continue
        still_missed.append(ref)
    missed = still_missed
    extras = [c for i, c in enumerate(candidates) if i not in used]
    return matched, missed, extras


# ---------------------------------------------------------------- arm loading
def load_arm_claims(args, spec):
    """Returns (claims, proposed_edits, meta) for the graded arm."""
    if args.claims:
        obj = _load(args.claims, None)
        if obj is None:
            print("parity-eval: cannot read --claims %s" % args.claims,
                  file=sys.stderr)
            sys.exit(1)
        return (obj.get("claims") or [], obj.get("proposed_edits") or [],
                {"source": args.claims})
    if args.run:
        dpath = os.path.join(RELAY_TRACKED, args.run, "leg-merged.json")
        d = _load(dpath, None)
        if d is None:
            print("parity-eval: no distillate at %s" % dpath, file=sys.stderr)
            sys.exit(1)
        rec = d.get("receipt") or {}
        vpath = os.path.join(RELAY_TRACKED, args.run, "verify.json")
        v = _load(vpath, None)
        meta = {"source": dpath, "run": args.run,
                "trigger": rec.get("trigger"), "role": rec.get("role"),
                "prompt_tokens": rec.get("prompt_tokens"),
                "escalations": len(rec.get("escalations") or []),
                "verify": ({"verified": v.get("verified"),
                            "fabrication_grade": v.get("fabrication_grade"),
                            "drift_possible": (v.get("mismatch", 0) or 0) -
                                              (v.get("fabrication_grade", 0) or 0),
                            "unverifiable": v.get("unverifiable")} if v else None)}
        return d.get("claims") or [], d.get("proposed_edits") or [], meta
    print("parity-eval: --grade needs --run or --claims", file=sys.stderr)
    sys.exit(3)


def load_reference(grading, task):
    if grading.get("reference") == "answer-key":
        key = _load(os.path.join(VAULT, grading["answer_key"]), None)
        if key is None:
            print("parity-eval: answer key unreadable: %s" % grading["answer_key"],
                  file=sys.stderr)
            sys.exit(1)
        return key
    fpath = os.path.join(STATE, task, "frontier.json")
    ref = _load(fpath, None)
    if ref is None:
        print("parity-eval: frontier reference missing at %s -- run the "
              "frontier protocol first (this task's reference IS the frontier "
              "claim set)" % fpath, file=sys.stderr)
        sys.exit(1)
    return ref


# ---------------------------------------------------------------- graders
def grade_coverage(grading, task, claims, meta):
    tol = float(grading.get("value_tol_rel", 0.005))
    ref = load_reference(grading, task)
    ref_claims = ref.get("reference_claims") or ref.get("claims") or []
    if not ref_claims:
        print("parity-eval: reference for %s has zero claims" % task,
              file=sys.stderr)
        sys.exit(1)
    matched, missed, extras = match_claims(ref_claims, claims, tol)
    cov = len(matched) / float(len(ref_claims))
    k = int(grading.get("extras_audit_k", 5))
    sample = sorted(extras, key=lambda c: hashlib.sha256(
        relay_schema.dumps_ascii(c).encode()).hexdigest())[:k]
    return {"score": round(cov, 4), "matched": len(matched),
            "reference_total": len(ref_claims),
            "missed": [{"metric": m.get("metric"), "value": m.get("value")}
                       for m in missed],
            "extras_count": len(extras),
            "extras_audit_sample": sample,
            "judged_narrative_weight": grading.get("judged_narrative_weight", 0),
            "meta": meta}


def _prop_applyable(p):
    """Uniqueness-in-current-file proxy for apply-clean (relay-apply.py is the
    live checker; this mechanical proxy is pre-registered for grading)."""
    path = os.path.join(VAULT, p.get("path", ""))
    try:
        body = io.open(path, encoding="utf-8").read()
    except (IOError, OSError):
        return False
    old = p.get("old") or ""
    try:
        old = old.encode("ascii").decode("unicode_escape")
    except (UnicodeDecodeError, ValueError):
        pass
    return old != "" and body.count(old) == 1


def grade_edits(grading, task, proposals, claims, meta):
    key = _load(os.path.join(VAULT, grading["answer_key"]), None)
    if key is None:
        print("parity-eval: answer key unreadable", file=sys.stderr)
        sys.exit(1)
    planted = key.get("planted") or []
    clean = key.get("clean_files") or []
    covered, fp = 0, 0
    used = set()
    for d in planted:
        need = d.get("match_old_contains") or d.get("escaped_char") or ""
        want_n = int(d.get("occurrences", 1))
        hits = 0
        for i, p in enumerate(proposals):
            if i in used:
                continue
            if os.path.normpath(p.get("path", "")) == os.path.normpath(
                    os.path.relpath(d["file"], "") if os.path.isabs(d["file"])
                    else d["file"]) and need and (
                    need in (p.get("old") or "")):
                used.add(i)
                hits += 1
                if hits >= want_n:
                    break
        covered += min(hits, want_n)
    total_planted = sum(int(d.get("occurrences", 1)) for d in planted)
    for i, p in enumerate(proposals):
        if i in used:
            continue
        if any(os.path.normpath(p.get("path", "")) == os.path.normpath(c)
               for c in clean):
            fp += 1
    neg_credit = 0
    neg_text = relay_schema.dumps_ascii(claims).lower()
    for c in clean:
        base = os.path.basename(c).lower()
        touched = any(os.path.normpath(p.get("path", "")) ==
                      os.path.normpath(c) for p in proposals)
        if (not touched) or (base in neg_text and "clean" in neg_text):
            neg_credit += 1
    neg_frac = neg_credit / float(len(clean)) if clean else 1.0
    apply_frac = (sum(1 for i, p in enumerate(proposals)
                      if i in used and _prop_applyable(p)) /
                  float(covered)) if covered else 0.0
    recall = max(0.0, (covered - fp) / float(total_planted)) if total_planted else 0.0
    score = 0.8 * recall + 0.1 * neg_frac + 0.1 * apply_frac
    return {"score": round(score, 4), "recall": round(recall, 4),
            "covered": covered, "planted_total": total_planted,
            "false_positives": fp, "clean_file_credit": round(neg_frac, 4),
            "applyable_fraction": round(apply_frac, 4),
            "proposals_count": len(proposals), "meta": meta}


# ---------------------------------------------------------------- commands
def cmd_grade(args):
    man = manifest()
    spec = task_spec(man, args.task)
    grading = _load(os.path.join(VAULT, spec["grading"]), None)
    if grading is None:
        print("parity-eval: grading spec unreadable", file=sys.stderr)
        sys.exit(1)
    claims, proposals, meta = load_arm_claims(args, spec)
    if grading["type"] == "edit_correctness":
        rec = grade_edits(grading, args.task, proposals, claims, meta)
    else:
        rec = grade_coverage(grading, args.task, claims, meta)
    rec.update({"task": args.task, "arm": args.arm, "slot": args.slot,
                "graded_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "grading_type": grading["type"]})
    name = "%s%s.json" % (args.arm, "-2" if args.slot == 2 else "")
    _save(os.path.join(STATE, args.task, "grade-" + name), rec)
    print(relay_schema.dumps_ascii(
        {"task": args.task, "arm": args.arm, "slot": args.slot,
         "score": rec["score"],
         "detail": {k: rec[k] for k in rec
                    if k in ("matched", "reference_total", "extras_count",
                             "recall", "false_positives", "covered")}}))
    return 0


def cmd_log_run(args):
    runs = _load(RUNS, {"runs": []})
    runs["runs"].append({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                         "task": args.task, "arm": args.arm, "run": args.run,
                         "status": args.status, "note": args.note or ""})
    _save(RUNS, runs)
    print("logged: %s %s %s %s" % (args.task, args.arm, args.run, args.status))
    return 0


def cmd_log_share(args):
    sh = _load(SHARES, {"sessions": []})
    sh["sessions"].append({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                           "session": args.session,
                           "share_pct": args.share_pct,
                           "source": args.source, "note": args.note or ""})
    _save(SHARES, sh)
    print("logged share: %s %.3f%% (%s)" % (args.session, args.share_pct,
                                            args.source))
    return 0


def cmd_blind_pack(args):
    man = manifest()
    spec = task_spec(man, args.task)
    tdir = os.path.join(STATE, args.task)
    entries = []
    for label, path in (("frontier", os.path.join(tdir, "frontier-narrative.txt")),
                        ("worker-1", os.path.join(tdir, "worker-narrative-1.txt")),
                        ("worker-2", os.path.join(tdir, "worker-narrative-2.txt"))):
        try:
            entries.append((label, io.open(path, encoding="utf-8").read()))
        except (IOError, OSError):
            pass
    if len(entries) < 2:
        print("parity-eval: need >=2 narratives under %s (frontier-narrative"
              ".txt, worker-narrative-N.txt)" % tdir, file=sys.stderr)
        return 1
    entries.sort(key=lambda e: hashlib.sha256(e[1].encode()).hexdigest())
    pack, mapping = [], {}
    for i, (label, text) in enumerate(entries):
        blind = "SAMPLE-%s" % chr(ord("A") + i)
        mapping[blind] = label
        pack.append("== %s ==\n%s\n" % (blind, text.strip()))
    with io.open(os.path.join(tdir, "blind-pack.txt"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(pack))
    sealed = base64.b64encode(
        relay_schema.dumps_ascii(mapping).encode()).decode()
    with io.open(os.path.join(tdir, "blind-mapping.sealed"), "w",
                 encoding="ascii", newline="\n") as fh:
        fh.write(sealed + "\n")
    print("blind pack: %d samples -> %s (mapping SEALED; decode only after "
          "scores are recorded)" % (len(pack), os.path.join(tdir, "blind-pack.txt")))
    return 0


def _task_parity(task_dir):
    fr = _load(os.path.join(task_dir, "grade-frontier.json"), None)
    w1 = _load(os.path.join(task_dir, "grade-worker.json"), None)
    w2 = _load(os.path.join(task_dir, "grade-worker-2.json"), None)
    if not w1:
        return None
    workers = [w for w in (w1, w2) if w]
    wscores = [w["score"] for w in workers]
    spread = (max(wscores) - min(wscores)) * 100 if len(wscores) > 1 else 0.0
    high_var = spread > 10.0
    wscore = min(wscores) if high_var else sum(wscores) / len(wscores)
    if fr:
        fscore = fr["score"]
        parity = (wscore / fscore * 100.0) if fscore > 0 else 0.0
    else:
        parity = wscore * 100.0  # frontier-referenced coverage: frontier == 1
    return {"parity_pct": round(min(parity, 100.0), 2),
            "parity_uncapped": round(parity, 2),
            "worker_scores": wscores, "worker_arms": len(wscores),
            "spread_pts": round(spread, 2), "high_variance": high_var,
            "frontier_score": fr["score"] if fr else None,
            "fabrications": sum((w.get("meta") or {}).get("verify", {} )
                                .get("fabrication_grade", 0) or 0
                                for w in workers if (w.get("meta") or {}).get("verify"))}


def cmd_assemble(args):
    man = manifest()
    date = args.date or time.strftime("%Y-%m-%d")
    per_task, incomplete = {}, []
    for t in man["tasks"]:
        r = _task_parity(os.path.join(STATE, t["id"]))
        if r is None:
            incomplete.append(t["id"])
        else:
            per_task[t["id"]] = r
    runs = _load(RUNS, {"runs": []})["runs"]
    shares = _load(SHARES, {"sessions": []})["sessions"]
    binding = [s for s in shares if s["source"] == "claudewatch"]
    result = {
        "date": date, "rule_doc": man["rule_doc"], "manifest_frozen": man["frozen"],
        "tasks_graded": len(per_task), "tasks_total": len(man["tasks"]),
        "incomplete": incomplete, "per_task": per_task,
        "run_accounting": runs, "share_sessions": shares,
        "bars": None, "note": "bars computed only when all tasks graded"}
    if not incomplete:
        vals = sorted(v["parity_pct"] for v in per_task.values())
        n = len(vals)
        median = (vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2.0)
        fabs = sum(v["fabrications"] or 0 for v in per_task.values())
        result["bars"] = {
            "median_parity_pct": round(median, 2),
            "min_task_pct": min(vals),
            "median_ge_97": median >= 97.0,
            "no_task_lt_90": min(vals) >= 90.0,
            "every_share_session_le_5": (bool(binding) and
                                         all(s["share_pct"] <= 5.0 for s in binding)),
            "share_sessions_binding": len(binding),
            "fabrication_grade_events": fabs,
            "zero_fabrication": fabs == 0}
        result["promotion_recommendation"] = (
            "PASS -- take to /decide with the rule doc" if (
                result["bars"]["median_ge_97"] and result["bars"]["no_task_lt_90"]
                and result["bars"]["every_share_session_le_5"]
                and result["bars"]["zero_fabrication"])
            else "FAIL -- results doc must name the failing bar + per-task fixes")
    out_json = os.path.join(VAULT, "wiki", "research",
                            "parity-eval-%s.json" % date)
    _save(out_json, result)
    lines = ["---", "categories: [wiki]", "status: active",
             "created: %s" % date, "updated: %s" % date, "---", "",
             "# Parity evaluation results -- %s" % date, "",
             "Rule (pre-registered, binding): %s. Manifest frozen %s; %d/%d "
             "tasks graded." % (man["rule_doc"], man["frozen"],
                                len(per_task), len(man["tasks"])), ""]
    if result.get("bars"):
        b = result["bars"]
        lines += ["| Bar | Value | Pass |", "|---|---|---|",
                  "| median parity | %.2f%% | %s |" % (b["median_parity_pct"], b["median_ge_97"]),
                  "| min task | %.2f%% | %s |" % (b["min_task_pct"], b["no_task_lt_90"]),
                  "| every session share <= 5%% | %d binding session(s) | %s |" % (
                      b["share_sessions_binding"], b["every_share_session_le_5"]),
                  "| fabrication-grade events | %d | %s |" % (
                      b["fabrication_grade_events"], b["zero_fabrication"]),
                  "", "Recommendation: %s" % result["promotion_recommendation"], ""]
    else:
        lines += ["INCOMPLETE -- ungraded tasks: %s" % ", ".join(incomplete), ""]
    lines += ["## Per-task", "",
              "| Task | Parity | Arms | Spread | High-var | Frontier score |",
              "|---|---|---|---|---|---|"]
    for tid in sorted(per_task):
        v = per_task[tid]
        lines.append("| %s | %.2f%% | %d | %.1fpt | %s | %s |" % (
            tid, v["parity_pct"], v["worker_arms"], v["spread_pts"],
            v["high_variance"], v["frontier_score"]))
    lines += ["", "## Honest limitations", "",
              "- Self-judging ceiling: the frontier arm authored the reference "
              "sets for live tasks; the matcher is mechanical but the "
              "reference choice is not adversarial.",
              "- Task-selection bias: 8 frozen tasks cannot span every "
              "workload; the manifest may not be narrowed, but it also "
              "cannot be exhaustive.",
              "- Live-data drift: tasks 1/2/3/6 pair same-evening; residual "
              "drift shows up as MISMATCH drift-possible, which does NOT "
              "count against the zero-verification-failures bar "
              "(fabrication-grade does).",
              "- n=2 worker arms: variance detection is coarse; >10pt spread "
              "scores at min of arms (pre-registered).",
              "- Orchestrator share is an estimate: claudewatch "
              "get_cost_attribution is binding at SESSION granularity; the "
              "per-step chars/4 JSONL is color.",
              "- Judged residue: url-harvest-brief narrative (20% of that "
              "task, ~2% of instrument) is blind-packed but "
              "prose-fingerprinting of the frontier arm is possible.",
              "", "Confidence Rating: MEDIUM (mechanical weight >= 95%; the "
              "limitations above are structural, stated, and pre-registered)."]
    out_md = os.path.join(VAULT, "wiki", "research", "parity-eval-%s.md" % date)
    with io.open(out_md, "w", encoding="ascii", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("assembled -> %s + .json (%d/%d tasks)" % (
        os.path.relpath(out_md, VAULT), len(per_task), len(man["tasks"])))
    return 0 if not incomplete else 1


def cmd_status(args):
    man = manifest()
    for t in man["tasks"]:
        tdir = os.path.join(STATE, t["id"])
        have = [n for n in ("grade-frontier.json", "grade-worker.json",
                            "grade-worker-2.json")
                if os.path.exists(os.path.join(tdir, n))]
        print("%-22s %s" % (t["id"], ", ".join(have) or "-"))
    runs = _load(RUNS, {"runs": []})["runs"]
    print("runs logged: %d (%d complete)" % (
        len(runs), sum(1 for r in runs if r["status"] == "complete")))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grade", action="store_true")
    ap.add_argument("--log-run", action="store_true", dest="log_run")
    ap.add_argument("--log-share", action="store_true", dest="log_share")
    ap.add_argument("--blind-pack", action="store_true", dest="blind_pack")
    ap.add_argument("--assemble", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--task")
    ap.add_argument("--arm", choices=["worker", "frontier"])
    ap.add_argument("--run")
    ap.add_argument("--claims")
    ap.add_argument("--slot", type=int, default=1, choices=[1, 2])
    ap.add_argument("--status-val", dest="run_status")
    ap.add_argument("--session")
    ap.add_argument("--share-pct", type=float, dest="share_pct")
    ap.add_argument("--source", choices=["claudewatch", "jsonl"])
    ap.add_argument("--note")
    ap.add_argument("--date")
    args, extra = ap.parse_known_args()
    # --status conflicts with --log-run's status value; accept "--status
    # complete|abandoned" positionally for log-run ergonomics:
    if args.log_run and not args.run_status:
        for e in extra:
            if e in ("complete", "abandoned"):
                args.run_status = e
    if args.grade:
        if not (args.task and args.arm):
            print("--grade needs --task + --arm", file=sys.stderr)
            return 3
        return cmd_grade(args)
    if args.log_run:
        if not (args.task and args.arm and args.run and args.run_status):
            print("--log-run needs --task --arm --run --status-val "
                  "complete|abandoned", file=sys.stderr)
            return 3
        args.status = args.run_status
        return cmd_log_run(args)
    if args.log_share:
        if not (args.session and args.share_pct is not None and args.source):
            print("--log-share needs --session --share-pct --source",
                  file=sys.stderr)
            return 3
        return cmd_log_share(args)
    if args.blind_pack:
        if not args.task:
            print("--blind-pack needs --task", file=sys.stderr)
            return 3
        return cmd_blind_pack(args)
    if args.assemble:
        return cmd_assemble(args)
    if args.status:
        return cmd_status(args)
    print(__doc__.strip().split("\n\n")[1])
    return 3


if __name__ == "__main__":
    sys.exit(main())
