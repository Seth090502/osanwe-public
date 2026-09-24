#!/usr/bin/env python3
"""relay-batch -- sequential mission queue for the relay worker lanes.

GATE-B: wiki/research/gates/gate-b-local-orchestration-program-2026-08-17.md.

Runs N missions SEQUENTIALLY as relay.py subprocesses. NEVER double-locks:
relay.py keeps the lane mutex; a child exit 2 (lane busy) gets a bounded retry
then an honest failed:lane-busy. awaiting-guidance legs PARK without blocking
the queue; --resume-parked resumes only legs whose guidance file EXISTS (no
blind resume). Queue is stable-sorted by leg-family (queue order IS the
KV-prefix cache policy on one Ollama slot -- Fable-review fix 12).

  python tools/relay-batch.py --file <batch.json> [--id B]        # run a spec
  python tools/relay-batch.py --manifest <missions.json> [--if-idle]
        [--stop-by HH:MM]                                          # scheduled
  python tools/relay-batch.py --resume-parked <batch-id>
  python tools/relay-batch.py --status <batch-id>

Batch spec: {"legs": [{"leg": ..., "mission": <path>, "run": <optional>}]}
Manifest (config/scheduled-missions.json): {"missions": [{"id", "leg",
"mission", "enabled", "overrides": {...}}]} -- overrides may LOWER budgets and
force plan_checkpoint off; applied via a temp mission copy (frozen specs stay
frozen).

Trigger attribution (Fable fixes 2 + F-3): if CLAUDE_LANE_TRIGGER is absent in
an INTERACTIVE invocation, the batch sets operator-phrase for its children (it
was invoked by a consented orchestrator); the scheduled wrapper sets
scheduled-idle explicitly and that passes through untouched.

Exit: 0 all completed/partial | 5 any parked | 1 any failed | 3 bad spec |
      4 skipped (--if-idle precheck said no; reason on stdout + runs log).
"""
import argparse
import json
import os
import subprocess
import sys
import time

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, os.path.join(TOOLS_DIR, "lib"))

import relay_schema  # noqa: E402

STATE_DIR = os.path.join(VAULT, ".claude", "state")
BATCH_DIR = os.path.join(STATE_DIR, "relay", "batches")
PENDING = os.path.join(STATE_DIR, "scheduled-worker-pending.json")
LOCK_PATH = os.path.join(os.environ.get("ProgramData", r"/path/to/programdata"), "QwenHost", "lane", "lane.lock")
RELAY = os.path.join(TOOLS_DIR, "relay.py")

FAMILY_ORDER = ("research", "extract", "edit", "compose")


def log(msg):
    print(msg, file=sys.stderr)


def save_batch(state):
    os.makedirs(BATCH_DIR, exist_ok=True)
    p = os.path.join(BATCH_DIR, state["id"] + ".json")
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="ascii") as fh:
        fh.write(relay_schema.dumps_ascii(state))
    os.replace(tmp, p)


def load_batch(batch_id):
    p = os.path.join(BATCH_DIR, batch_id + ".json")
    if not os.path.isfile(p):
        return None
    return json.load(open(p, encoding="ascii"))


def parse_envelope(stdout_text):
    """The envelope is the LAST JSON object on stdout (tolerate noise)."""
    idx = stdout_text.rfind("\n{")
    cand = stdout_text[idx + 1:] if idx >= 0 else stdout_text
    try:
        return json.loads(cand)
    except ValueError:
        try:
            return json.loads(stdout_text[stdout_text.index("{"):])
        except (ValueError, IndexError):
            return None


def run_leg(leg_row, resume=False, timeout_s=3000):
    """Single seam the suite monkeypatches. Returns (exit_code, envelope)."""
    cmd = [sys.executable, RELAY, "--leg", leg_row["leg"],
           "--mission", os.path.join(VAULT, leg_row["mission"])
           if not os.path.isabs(leg_row["mission"]) else leg_row["mission"]]
    if resume:
        cmd += ["--resume", leg_row["run"]]
    else:
        cmd += ["--run", leg_row["run"]]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return 1, {"status": "failed", "error": "batch-level timeout"}
    return r.returncode, parse_envelope(r.stdout or "")


def if_idle_precheck():
    """SKIP reasons (fail closed). Every fire logs run OR skip -- the runs log
    is the X70 heartbeat."""
    # 1. lane free (nonblocking acquire-release probe)
    try:
        fh = open(LOCK_PATH, "a+")
        try:
            if os.name == "nt":
                import msvcrt
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            fh.close()
    except OSError:
        return "skip: lane busy"
    # 2. GPU idle: 2 samples 15s apart, util < 20% AND (model resident OR
    #    free >= 20000 MiB). nvidia-smi absent -> fail closed.
    samples = []
    for i in range(2):
        try:
            out = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu,memory.free",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=20).stdout.strip()
            util, free = [int(x.strip()) for x in out.split(",")[:2]]
            samples.append((util, free))
        except Exception:                                     # noqa: BLE001
            return "skip: gpu state unknown (nvidia-smi)"
        if i == 0:
            time.sleep(15)
    if any(u >= 20 for u, _ in samples):
        return "skip: gpu busy (util %s)" % ([u for u, _ in samples],)
    # 3. daemon reachable + model residency
    resident = False
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:11434/api/ps",
                                    timeout=5) as r:
            ps = json.loads(r.read())
        for m in ps.get("models") or []:
            sz = m.get("size") or 0
            if sz and (m.get("size_vram") or 0) / sz >= 0.95:
                resident = True
    except Exception:                                         # noqa: BLE001
        return "skip: daemon unreachable"
    if not resident and all(f < 20000 for _, f in samples):
        return "skip: model not resident and free VRAM %s < 20000 MiB" % (
            [f for _, f in samples],)
    return None


def stop_by_passed(stop_by):
    if not stop_by:
        return False
    try:
        hh, mm = [int(x) for x in stop_by.split(":")]
    except ValueError:
        return False
    now = time.localtime()
    return (now.tm_hour, now.tm_min) >= (hh, mm)


def leg_state_from(code, env):
    status = (env or {}).get("status")
    if code == 0:
        return "completed"
    if code == 5 and status == "awaiting-guidance":
        return "parked"
    if code == 5:
        return "partial"
    return "failed"


def apply_overrides(mission_path, overrides):
    """Frozen specs stay frozen: overrides land on a temp copy. Budgets may
    only LOWER; plan_checkpoint may only be forced OFF."""
    m = json.load(open(os.path.join(VAULT, mission_path)
                       if not os.path.isabs(mission_path) else mission_path,
                       encoding="ascii"))
    b = dict(m.get("budgets") or {})
    for k, v in (overrides or {}).items():
        if k == "plan_checkpoint":
            if v is False:
                m["plan_checkpoint"] = False
        elif isinstance(v, int):
            b[k] = min(v, b.get(k, v))
    if b:
        m["budgets"] = b
    import tempfile
    p = os.path.join(tempfile.mkdtemp(prefix="relay-batch-"), "mission.json")
    with open(p, "w", encoding="ascii") as fh:
        fh.write(relay_schema.dumps_ascii(m))
    return p


def _claim_maps(run):
    """Mechanical fingerprint for the consistency diff: {(entity, sorted
    metric tokens) -> set(values casefold)}. Values keyed per metric so a
    same-key value disagreement is detectable as a CONTRADICTION."""
    import re as _re
    d_path = os.path.join(VAULT, ".agents", "relay", run, "leg-merged.json")
    try:
        d = json.load(open(d_path, encoding="utf-8"))
    except (OSError, ValueError):
        return None
    m = {}
    for c in d.get("claims") or []:
        toks = " ".join(sorted(_re.findall(
            r"[a-z0-9]+", (c.get("metric") or "").lower())))
        k = (str(c.get("entity") or "").casefold(), toks)
        m.setdefault(k, set()).add(
            str(c.get("value") or "").replace(",", "").casefold())
    return m


def consistency_diffs(state, threshold):
    """F-10: a diff computes ONLY when both arms finished ok; anything else is
    consistency-incomplete, never a divergence.

    Verdicts (refined 2026-08-17 after the first live dual-run, BEFORE any
    parity run or promotion): live-data legs legitimately sample different
    ROWS run to run, so coverage variance is reported as COLOR while the
    demotion-relevant verdict keys on CONTRADICTIONS -- the same (entity,
    metric) carrying non-overlapping values in the two arms. A divergence
    alarm that rings on every live-data night protects nothing.
      agree              no contradictions, coverage diff <= threshold
      coverage-variance  no contradictions, coverage diff >  threshold
      divergence         >= 1 contradiction (this is what F-9 demotion reads)
    """
    pairs = {}
    for r in state["legs"]:
        p = r.get("consistency_pair")
        if p:
            pairs.setdefault(p, []).append(r)
    out = []
    for pid, rows in sorted(pairs.items()):
        if len(rows) != 2 or any(r["state"] != "completed" for r in rows):
            out.append({"pair": pid, "result": "consistency-incomplete"})
            continue
        ma, mb = _claim_maps(rows[0]["run"]), _claim_maps(rows[1]["run"])
        if ma is None or mb is None:
            out.append({"pair": pid, "result": "consistency-incomplete"})
            continue
        ka, kb = set(ma), set(mb)
        shared = ka & kb
        contradictions = sorted(
            "%s|%s" % k for k in shared if not (ma[k] & mb[k]))
        denom = max(len(ka), len(kb)) or 1
        cov = len(ka ^ kb) / float(denom)
        if contradictions:
            result = "divergence"
        elif cov > threshold:
            result = "coverage-variance"
        else:
            result = "agree"
        out.append({"pair": pid, "result": result,
                    "contradictions": contradictions[:10],
                    "contradiction_count": len(contradictions),
                    "coverage_diff_fraction": round(cov, 4),
                    "threshold": threshold,
                    "only_a": len(ka - kb), "only_b": len(kb - ka),
                    "common_keys": len(shared)})
    return out


def write_pending(state, extra=None):
    """Scheduled-mode surfacing (X70): counts + parked questions + per-server
    health; NEVER payload content (worker-authored text stays out of the
    session-start surface)."""
    parked = [{"run": r["run"], "leg": r["leg"],
               "guidance_path": r.get("guidance_path")}
              for r in state["legs"] if r["state"] == "parked"]
    servers = {}
    for r in state["legs"]:
        for srv, why in (r.get("degraded_servers") or {}).items():
            servers[srv] = "DOWN"
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "batch": state["id"],
           "new_distillates": sum(1 for r in state["legs"]
                                  if r["state"] in ("completed", "partial")),
           "parked": parked, "servers_down": sorted(servers),
           "last_result": extra or state.get("summary")}
    if state.get("consistency"):
        out["consistency"] = state["consistency"]
    tmp = PENDING + ".tmp"
    with open(tmp, "w", encoding="ascii") as fh:
        fh.write(relay_schema.dumps_ascii(out))
    os.replace(tmp, PENDING)


def run_queue(state, stop_by=None, lane_retries=3, lane_wait=60,
              scheduled=False):
    for row in state["legs"]:
        if row["state"] not in ("queued", "retry"):
            continue
        if stop_by_passed(stop_by):
            row["state"] = "skipped"
            row["reason"] = "stop-by"
            save_batch(state)
            continue
        attempts = 0
        while True:
            attempts += 1
            row["state"] = "running"
            save_batch(state)
            code, env = run_leg(row)
            if code == 2 and attempts <= lane_retries:
                log("lane busy; retry %d/%d in %ds" % (attempts, lane_retries,
                                                       lane_wait))
                time.sleep(lane_wait)
                continue
            break
        row["exit"] = code
        row["status"] = (env or {}).get("status")
        row["state"] = leg_state_from(code, env)
        if code == 2:
            row["state"] = "failed"
            row["reason"] = "lane-busy"
        if row["state"] == "parked":
            row["escalation"] = (env or {}).get("escalation")
            row["guidance_path"] = (env or {}).get("guidance_path")
        flags = (env or {}).get("flags") or {}
        if flags.get("degraded_servers"):
            row["degraded_servers"] = flags["degraded_servers"]
        row["attempts"] = attempts
        save_batch(state)
    state["summary"] = {
        "completed": sum(1 for r in state["legs"] if r["state"] == "completed"),
        "partial": sum(1 for r in state["legs"] if r["state"] == "partial"),
        "parked": sum(1 for r in state["legs"] if r["state"] == "parked"),
        "failed": sum(1 for r in state["legs"] if r["state"] == "failed"),
        "skipped": sum(1 for r in state["legs"] if r["state"] == "skipped")}
    save_batch(state)
    if scheduled:
        write_pending(state)
    print(relay_schema.dumps_ascii({"id": state["id"], **state["summary"]}))
    s = state["summary"]
    return 5 if s["parked"] else (1 if s["failed"] else 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file")
    ap.add_argument("--manifest")
    ap.add_argument("--id")
    ap.add_argument("--resume-parked", metavar="BATCH")
    ap.add_argument("--status", metavar="BATCH")
    ap.add_argument("--if-idle", action="store_true")
    ap.add_argument("--stop-by", default=None, metavar="HH:MM")
    ap.add_argument("--lane-retries", type=int, default=3)
    ap.add_argument("--lane-wait", type=int, default=60)
    args = ap.parse_args()

    if args.status:
        st = load_batch(args.status)
        print(relay_schema.dumps_ascii(st or {"error": "no such batch"}))
        return 0 if st else 3

    if args.resume_parked:
        st = load_batch(args.resume_parked)
        if not st:
            print(relay_schema.dumps_ascii({"error": "no such batch"}))
            return 3
        resumed = 0
        for row in st["legs"]:
            if row["state"] != "parked":
                continue
            gp = row.get("guidance_path")
            gp_abs = os.path.join(VAULT, gp) if gp and not os.path.isabs(gp) \
                else gp
            if not gp_abs or not os.path.isfile(gp_abs):
                row["reason"] = "guidance not written yet"
                continue
            code, env = run_leg(row, resume=True)
            row["exit"] = code
            row["status"] = (env or {}).get("status")
            row["state"] = leg_state_from(code, env)
            if row["state"] == "parked":     # escalated again (budget holds)
                row["escalation"] = (env or {}).get("escalation")
                row["guidance_path"] = (env or {}).get("guidance_path")
            resumed += 1
            save_batch(st)
        st["summary"] = {
            "completed": sum(1 for r in st["legs"] if r["state"] == "completed"),
            "partial": sum(1 for r in st["legs"] if r["state"] == "partial"),
            "parked": sum(1 for r in st["legs"] if r["state"] == "parked"),
            "failed": sum(1 for r in st["legs"] if r["state"] == "failed"),
            "skipped": sum(1 for r in st["legs"] if r["state"] == "skipped")}
        save_batch(st)
        print(relay_schema.dumps_ascii(
            {"id": st["id"], "resumed": resumed, **st["summary"]}))
        return 5 if st["summary"]["parked"] else 0

    scheduled = bool(args.manifest)
    # trigger attribution (F-3): interactive batch = consented orchestrator
    if not os.environ.get("CLAUDE_LANE_TRIGGER") and not scheduled:
        os.environ["CLAUDE_LANE_TRIGGER"] = "operator-phrase"

    if args.if_idle:
        why = if_idle_precheck()
        if why:
            print(why)
            return 4
        # scheduled mode: resume parked legs whose guidance now exists, before
        # new missions
        if scheduled and os.path.isdir(BATCH_DIR):
            for fn in sorted(os.listdir(BATCH_DIR)):
                st = load_batch(fn[:-5])
                if st and any(r["state"] == "parked" for r in st["legs"]):
                    for row in st["legs"]:
                        if row["state"] != "parked":
                            continue
                        gp = row.get("guidance_path")
                        gp_abs = os.path.join(VAULT, gp) if gp and \
                            not os.path.isabs(gp) else gp
                        if gp_abs and os.path.isfile(gp_abs):
                            code, env = run_leg(row, resume=True)
                            row["exit"] = code
                            row["state"] = leg_state_from(code, env)
                            save_batch(st)
                    # surface the resumed batch's fresh state now; the new
                    # batch's own write_pending (if it runs) overwrites later
                    write_pending(st)

    legs = []
    consistency_threshold = 0.25
    if args.file:
        try:
            spec = json.load(open(args.file, encoding="ascii"))
            legs = list(spec.get("legs") or [])
        except (OSError, ValueError) as exc:
            print(relay_schema.dumps_ascii({"error": "bad spec: %s" % exc}))
            return 3
    elif args.manifest:
        try:
            man = json.load(open(os.path.join(VAULT, args.manifest)
                                 if not os.path.isabs(args.manifest)
                                 else args.manifest, encoding="ascii"))
        except (OSError, ValueError) as exc:
            print(relay_schema.dumps_ascii({"error": "bad manifest: %s" % exc}))
            return 3
        consistency_threshold = float(man.get("consistency_diff_threshold",
                                              0.25))
        for m in man.get("missions") or []:
            if not m.get("enabled"):
                continue
            mp = apply_overrides(m["mission"], m.get("overrides"))
            if m.get("consistency"):
                # SOTA-DELTA: run the leg TWICE, diff claim sets mechanically
                # after the queue (zero-frontier-cost divergence telemetry).
                for arm in ("a", "b"):
                    legs.append({"leg": m["leg"], "mission": mp,
                                 "consistency_pair": m.get("id") or m["leg"],
                                 "consistency_arm": arm})
            else:
                legs.append({"leg": m["leg"], "mission": mp})
    else:
        print("relay-batch: --file, --manifest, --resume-parked or --status "
              "required", file=sys.stderr)
        return 3
    if not legs:
        print(relay_schema.dumps_ascii({"error": "no legs"}))
        return 3

    # stable sort by role family (KV-prefix cache policy, fix 12)
    def fam_key(row):
        fam = (row.get("leg") or "").split(":", 1)[0]
        return FAMILY_ORDER.index(fam) if fam in FAMILY_ORDER else 99

    legs = sorted(legs, key=fam_key)
    batch_id = args.id or "b-" + time.strftime("%Y%m%d-%H%M%S")
    for i, row in enumerate(legs, 1):
        row.setdefault("run", "%s-L%d" % (batch_id, i))
        row["state"] = "queued"
    state = {"schema_version": 1, "id": batch_id,
             "created": time.strftime("%Y-%m-%dT%H:%M:%S"), "legs": legs}
    save_batch(state)
    rc = run_queue(state, stop_by=args.stop_by,
                   lane_retries=args.lane_retries, lane_wait=args.lane_wait,
                   scheduled=scheduled)
    if scheduled and any(r.get("consistency_pair") for r in state["legs"]):
        state["consistency"] = consistency_diffs(state, consistency_threshold)
        save_batch(state)
        write_pending(state)
    return rc


if __name__ == "__main__":
    sys.exit(main())
