#!/usr/bin/env python3
"""lane-bench -- the measurement instrument for the local model lane.

GATE-B: wiki/research/gates/gate-b-lane-bench-2026-08-16.md (BUILD-JUSTIFIED, rule 2).

Reports, per model: median-of-N decode tok/s, median-of-N prefill tok/s, MTP draft
acceptance, and the GPU residency + free VRAM observed around every run. Read-only:
it writes NO files and never arms, re-arms, swaps, or restarts anything.

  python tools/lane-bench.py
  python tools/lane-bench.py --model qwen3.8:27b --model qwen3.6:27b
  python tools/lane-bench.py -n 5 --temp 0.6 --top-p 0.95
  python tools/lane-bench.py --json > run.json

WHY THIS EXISTS RATHER THAN A SCRATCHPAD SCRIPT (read before "improving" it):

1. ACCEPTANCE IS RUN-SCOPED BY LOG BYTE OFFSET, not by tailing the log. Every model
   that has ever run against this daemon writes `draft acceptance` lines into ONE
   log, and the `spec common_specu: statistics draft-mtp:` lines are DAEMON-CUMULATIVE
   counters that also reset on model reload. Tailing either one attributes another
   model's speculation to this run. We record the log size before the request and read
   only the bytes appended after it, then match the PER-TASK
   `slot print_timing: ... draft acceptance = R (A accepted / G generated), mean len = L`
   line, which is already scoped to one task. Zero matches reports null with a reason;
   it never falls back to a stale number.

2. EVERY RUN CARRIES ITS VRAM. On 2026-08-16 lane-guard read IMMINENT at 857 MiB free
   with the model still 100% resident, because ~13.6 GB of this card is held by desktop
   processes that WDDM will not attribute per-process. Free headroom here is a function
   of what the operator has open. A run whose model was not fully resident is marked
   SPILLED and excluded from the medians rather than printed as if comparable.

3. PREFILL IS LENGTH-PINNED, AND NONCE-BUSTED AS A PRECAUTION.
   (a) MEASURED, and it is large: prefill tok/s is a strong function of prompt length.
   On this box, temp 0, same model, same day: 1,064 tok/s at 70 prompt tokens, 888 at 91,
   and 2,910 at 2,630. The handoff's ~2,576 tok/s is a large-prompt figure. A prefill
   comparison between two models is therefore only meaningful at MATCHING prompt length,
   so --prefill-tokens pads to a pinned size and the ACTUAL evaluated prompt_tokens is
   printed with every run and every median, and the side-by-side table refuses to let a
   length mismatch pass silently. The pre-registered adoption rule turns on
   "prefill >= +15%", which is unreadable without this pin.
   (b) NOT observed on this path, kept anyway: a repeated identical prompt could in
   principle be served from Ollama's prefix cache, making runs 2..N measure the cache.
   Checked with --no-nonce and it did NOT happen here (prompt_eval stayed at the full 70
   tokens on all three runs). So the per-run nonce is a precaution, not a fix for an
   observed defect, and --min-prefill-tokens is a tripwire that has never fired. Stated
   this way on purpose: the unresolved prefix-reuse failure in the handoff is a DIFFERENT
   path (mode 3 through /v1/messages with cache_control), and conflating the two would
   manufacture a false link between them.

4. NOTHING IS SUMMARISED AWAY. Raw per-run rows are always printed, N is always
   stated, and any quantity that could not be measured is null WITH the reason.
"""

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANE_CONFIG = os.path.join(VAULT, "config", "local-lane.json")

# The scratchpad predecessor's prompt, kept verbatim so decode figures stay comparable
# with the 137.0 tok/s baseline recorded in .agents/migration/HANDOFF.md.
PROMPT = (
    "Write a plain-language explanation of how a GPU streaming multiprocessor schedules "
    "warps during a large matrix multiplication. Cover occupancy, memory coalescing, and "
    "why arithmetic intensity decides whether the kernel is bandwidth-bound or compute-bound. "
    "Use ordinary prose, no bullet points, no headings, and no code."
)

# slot print_timing: id  0 | task 138 | draft acceptance = 0.77273 (  170 accepted /   220 generated), mean len =  4.09
ACC_RE = re.compile(
    r"task\s+(\d+)\s*\|\s*draft acceptance = ([0-9.]+) "
    r"\(\s*(\d+) accepted /\s*(\d+) generated\), mean len =\s*([0-9.]+)")
# The sampler dump the server prints per task, so the record states what sampling ACTUALLY ran
# rather than what we believe we asked for (delegate.py and the mode-3 normalizer disagree).
TEMP_RE = re.compile(r"\btemp = ([0-9.]+)")
TOPP_RE = re.compile(r"\btop_p = ([0-9.]+)")

SPILL_RATIO = 0.999   # lane-guard's threshold, kept identical on purpose
LOW_VRAM_MIB = 1200   # lane-guard's ImminentFreeMiB, kept identical on purpose

# Deterministic filler for --prefill-tokens. Ordinary prose, so the tokenizer behaves as it
# would on real input; no repeated single token, which would prefill unrepresentatively fast.
FILLER = (
    "The scheduler assigns each resident warp to an issue slot and tracks its readiness "
    "against outstanding memory transactions, retiring instructions in order while long "
    "latency loads remain in flight across the register file and shared memory banks. ")


def pad_prompt(prompt, target_tokens):
    """Pad to approximately target_tokens. The server's actual count is what gets reported."""
    if target_tokens <= 0:
        return prompt
    approx_chars = target_tokens * 4          # ~4 chars/token for English prose
    need = approx_chars - len(prompt)
    if need <= 0:
        return prompt
    reps = need // len(FILLER) + 1
    return (FILLER * reps)[:need] + "\n" + prompt


# ----------------------------------------------------------------- plumbing

def http_json(url, body=None, timeout=900):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def gpu_vram():
    """(free_mib, total_mib, error_reason). Never raises."""
    try:
        p = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=20)
    except FileNotFoundError:
        return None, None, "nvidia-smi not on PATH"
    except Exception as exc:                                  # noqa: BLE001
        return None, None, "nvidia-smi failed: %s" % exc
    if p.returncode != 0:
        return None, None, "nvidia-smi exit %d" % p.returncode
    line = (p.stdout or "").strip().splitlines()
    if not line:
        return None, None, "nvidia-smi returned no rows"
    try:
        free, total = [int(x.strip()) for x in line[0].split(",")]
    except ValueError:
        return None, None, "nvidia-smi row unparsed: %r" % line[0]
    return free, total, None


def residency(host, model):
    """size_vram/size for a resident model. None when the model is not loaded."""
    try:
        d = http_json(host + "/api/ps", timeout=30)
    except Exception as exc:                                  # noqa: BLE001
        return None, "/api/ps unreachable: %s" % exc
    for m in d.get("models") or []:
        if model in (m.get("name"), m.get("model")):
            size = m.get("size") or 0
            vram = m.get("size_vram") or 0
            return {
                "size_bytes": size,
                "size_vram_bytes": vram,
                "vram_ratio": round(vram / size, 6) if size else None,
                "resident_mib": int(size / (1024 * 1024)) if size else None,
            }, None
    return None, "model not resident in /api/ps"


def find_server_log(explicit):
    if explicit:
        return (explicit, None) if os.path.isfile(explicit) else (
            None, "log not found at --log %s" % explicit)
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        return None, "LOCALAPPDATA unset; pass --log"
    base = os.path.join(local, "Ollama")
    for name in ("server-launcher.log", "server.log"):
        p = os.path.join(base, name)
        if os.path.isfile(p):
            return p, None
    return None, "no server log under %s (daemon started outside lane-arm?)" % base


def read_window(path, start_off):
    """Bytes appended to the log since start_off. This is the run-scoping mechanism."""
    try:
        end = os.path.getsize(path)
    except OSError as exc:
        return None, "log stat failed: %s" % exc
    if end < start_off:
        return None, "log shrank %d -> %d (rotation or daemon restart mid-run)" % (
            start_off, end)
    if end == start_off:
        return "", None
    try:
        with open(path, "rb") as fh:
            fh.seek(start_off)
            return fh.read(end - start_off).decode("utf-8", "replace"), None
    except OSError as exc:
        return None, "log read failed: %s" % exc


def parse_acceptance(path, start_off, wait_s):
    """Match the per-task acceptance line inside this run's log window.

    The server flushes print_timing at task completion, which can trail the HTTP
    response slightly, so poll up to wait_s before concluding there is nothing.
    """
    deadline = time.time() + wait_s
    window, err = "", None
    while True:
        window, err = read_window(path, start_off)
        if err:
            return None, err
        if ACC_RE.search(window) or time.time() >= deadline:
            break
        time.sleep(0.1)

    hits = ACC_RE.findall(window)
    if not hits:
        return None, ("no draft acceptance line in this run's log window "
                      "(model may not ship draft_num_predict, or MTP is inactive)")
    task, rate, accepted, generated, mean_len = hits[-1]
    out = {
        "task": int(task),
        "rate": float(rate),
        "accepted": int(accepted),
        "generated": int(generated),
        "mean_len": float(mean_len),
        "lines_matched": len(hits),
    }
    if len(hits) > 1:
        out["note"] = ("%d acceptance lines in window; reporting the last. "
                       "Another caller shared the daemon during this run." % len(hits))
    t, p = TEMP_RE.findall(window), TOPP_RE.findall(window)
    out["server_temp"] = float(t[-1]) if t else None
    out["server_top_p"] = float(p[-1]) if p else None
    return out, None


# ----------------------------------------------------------------- one run

def one_run(host, model, prompt, num_predict, temp, top_p, seed,
            log_path, acc_wait, min_prefill):
    run = {"valid": True, "invalid_reason": None}

    free_before, total_mib, vram_err = gpu_vram()
    log_off = os.path.getsize(log_path) if log_path else None

    # SAMPLING IS NOT IMPOSED BY DEFAULT. temp/top_p are omitted from the request unless the
    # caller passed them, so the server applies the model's OWN shipped parameters
    # (qwen3.8:27b modelfile: temperature 1, top_p 0.95, top_k 20). Three different values are
    # live on this box -- delegate.py hardcodes 0, the mode-3 normalizer injects 0.6, the model
    # ships 1 -- and picking one here would silently privilege it. The actual value the server
    # used is parsed back out of the log and reported with every run.
    opts = {"num_predict": num_predict, "seed": seed}
    if temp is not None:
        opts["temperature"] = temp
    if top_p is not None:
        opts["top_p"] = top_p
    body = {"model": model, "prompt": prompt, "stream": False, "options": opts}
    t0 = time.time()
    try:
        d = http_json(host + "/api/generate", body)
    except Exception as exc:                                  # noqa: BLE001
        run.update(valid=False, invalid_reason="/api/generate failed: %s" % exc,
                   wall_s=round(time.time() - t0, 3))
        return run
    run["wall_s"] = round(time.time() - t0, 3)

    ec, ed = d.get("eval_count") or 0, d.get("eval_duration") or 0
    pc, pd = d.get("prompt_eval_count") or 0, d.get("prompt_eval_duration") or 0
    run["eval_tokens"] = ec
    run["prompt_tokens"] = pc
    run["decode_tok_s"] = round(ec / (ed / 1e9), 1) if ed and ec else None
    run["load_s"] = round((d.get("load_duration") or 0) / 1e9, 2)
    run["total_s"] = round((d.get("total_duration") or 0) / 1e9, 2)

    if not pd or not pc:
        run["prefill_tok_s"] = None
        run["prefill_reason"] = "server reported no prompt_eval work"
    elif pc < min_prefill:
        run["prefill_tok_s"] = None
        run["prefill_reason"] = (
            "only %d prompt tokens evaluated (< --min-prefill-tokens %d): prefix cache "
            "hit, so any rate here measures the cache" % (pc, min_prefill))
    else:
        run["prefill_tok_s"] = round(pc / (pd / 1e9), 1)
        run["prefill_reason"] = None

    if run["decode_tok_s"] is None:
        run.update(valid=False, invalid_reason="server reported no eval work")

    res, res_err = residency(host, model)
    run["residency"] = res
    run["residency_reason"] = res_err
    if res and res["vram_ratio"] is not None and res["vram_ratio"] < SPILL_RATIO:
        run.update(valid=False, invalid_reason=(
            "SPILLED: %.4f of the model on GPU (< %.3f). Numbers from a partly-CPU "
            "model are not comparable." % (res["vram_ratio"], SPILL_RATIO)))

    free_after, _, _ = gpu_vram()
    run["vram_free_before_mib"] = free_before
    run["vram_free_after_mib"] = free_after
    run["vram_total_mib"] = total_mib
    run["vram_reason"] = vram_err

    if log_path:
        acc, acc_err = parse_acceptance(log_path, log_off, acc_wait)
    else:
        acc, acc_err = None, "no server log located"
    run["acceptance"] = acc
    run["acceptance_reason"] = acc_err
    return run


def bench_model(args, model, log_path, log_reason):
    print("\n=== %s ===" % model)
    free, total, verr = gpu_vram()
    if verr:
        print("vram: UNMEASURED (%s)" % verr)
    else:
        print("vram: %d MiB free of %d MiB%s" % (
            free, total,
            "   WARNING: below %d MiB, a spill during this bench is possible"
            % LOW_VRAM_MIB if free < LOW_VRAM_MIB else ""))
    if log_reason:
        print("acceptance: UNMEASURABLE (%s)" % log_reason)

    result = {"model": model, "runs": [], "warmup": None,
              "config": {"n": args.n, "num_predict": args.num_predict,
                         "temp": args.temp, "top_p": args.top_p, "seed": args.seed,
                         "nonce": not args.no_nonce, "host": args.host,
                         "server_log": log_path, "server_log_reason": log_reason,
                         "prefill_tokens_target": args.prefill_tokens,
                         "min_prefill_tokens": args.min_prefill_tokens}}

    warm = one_run(args.host, model, PROMPT, 32, args.temp, args.top_p, args.seed,
                   log_path, args.acceptance_wait, args.min_prefill_tokens)
    result["warmup"] = warm
    print("warmup: load_s=%s decode=%s tok/s%s" % (
        warm.get("load_s"), warm.get("decode_tok_s"),
        "" if warm["valid"] else "   INVALID: %s" % warm["invalid_reason"]))
    if not warm["valid"] and warm.get("decode_tok_s") is None:
        print("HALT: warmup produced no usable generation. Nothing measured.")
        result["halted"] = warm["invalid_reason"]
        return result

    base = pad_prompt(PROMPT, args.prefill_tokens)
    for i in range(1, args.n + 1):
        # The nonce goes at the very FRONT so no prefix of the request can be served from
        # cache. A nonce anywhere else leaves everything before it reusable.
        prompt = base if args.no_nonce else (
            "Request id %d-%d, ignore this line.\n%s" % (int(time.time()), i, base))
        r = one_run(args.host, model, prompt, args.num_predict, args.temp, args.top_p,
                    args.seed, log_path, args.acceptance_wait, args.min_prefill_tokens)
        r["run"] = i
        result["runs"].append(r)
        acc = r.get("acceptance")
        print("run%d: decode=%-6s prefill=%-8s eval_tok=%-5s prompt_tok=%-6s "
              "acc=%-7s vram_free=%s MiB%s" % (
                  i,
                  r.get("decode_tok_s"),
                  r.get("prefill_tok_s") if r.get("prefill_tok_s") is not None else "null",
                  r.get("eval_tokens"), r.get("prompt_tokens"),
                  acc["rate"] if acc else "null",
                  r.get("vram_free_after_mib"),
                  "" if r["valid"] else "   INVALID: %s" % r["invalid_reason"]))
        if r.get("prefill_tok_s") is None and r.get("prefill_reason"):
            print("        prefill null: %s" % r["prefill_reason"])
        if acc is None and r.get("acceptance_reason"):
            print("        acceptance null: %s" % r["acceptance_reason"])
        elif acc and acc.get("note"):
            print("        %s" % acc["note"])

    valid = [r for r in result["runs"] if r["valid"]]
    dec = [r["decode_tok_s"] for r in valid if r.get("decode_tok_s") is not None]
    pre = [r["prefill_tok_s"] for r in valid if r.get("prefill_tok_s") is not None]
    accs = [r["acceptance"]["rate"] for r in valid if r.get("acceptance")]
    mlen = [r["acceptance"]["mean_len"] for r in valid if r.get("acceptance")]
    ptoks = [r["prompt_tokens"] for r in valid if r.get("prompt_tokens")]

    summary = {
        "runs_total": len(result["runs"]),
        "runs_valid": len(valid),
        "runs_invalid": len(result["runs"]) - len(valid),
        "decode_tok_s_median": round(statistics.median(dec), 1) if dec else None,
        "decode_tok_s_runs": dec,
        "decode_n": len(dec),
        "prefill_tok_s_median": round(statistics.median(pre), 1) if pre else None,
        "prefill_tok_s_runs": pre,
        "prefill_n": len(pre),
        "acceptance_median": round(statistics.median(accs), 5) if accs else None,
        "acceptance_runs": accs,
        "acceptance_n": len(accs),
        "mean_len_median": round(statistics.median(mlen), 3) if mlen else None,
        # Carried into the summary because a prefill figure is only comparable against
        # another prefill figure measured at the same evaluated prompt length.
        "prompt_tokens_median": round(statistics.median(ptoks)) if ptoks else None,
    }
    result["summary"] = summary

    nn = lambda x: "null" if x is None else x     # noqa: E731 -- match the per-run rows
    print("-- medians over %d/%d valid run(s) --" % (len(valid), len(result["runs"])))
    print("decode  : %s tok/s   n=%d  runs=%s" % (
        nn(summary["decode_tok_s_median"]), summary["decode_n"], dec or "[]"))
    print("prefill : %s tok/s   n=%d  runs=%s  at %s prompt tokens" % (
        nn(summary["prefill_tok_s_median"]), summary["prefill_n"], pre or "[]",
        nn(summary["prompt_tokens_median"])))
    print("accept  : %s         n=%d  runs=%s  mean_len=%s" % (
        nn(summary["acceptance_median"]), summary["acceptance_n"], accs or "[]",
        nn(summary["mean_len_median"])))

    # Benching itself consumes VRAM: llama.cpp allocates context checkpoints (~150-160 MiB
    # each, up to 32) and recreates them whenever the prefix changes, which the per-run nonce
    # guarantees. Measured 2026-08-16: free headroom fell 921 -> 390 MiB across four
    # invocations. Print the drain so a long bake-off does not quietly walk into a spill.
    # What the SERVER actually sampled with, read back out of its own log rather than assumed
    # from what we sent. This is the check that catches a modelfile default changing under us.
    stemps = [r["acceptance"]["server_temp"] for r in valid
              if r.get("acceptance") and r["acceptance"].get("server_temp") is not None]
    stopps = [r["acceptance"]["server_top_p"] for r in valid
              if r.get("acceptance") and r["acceptance"].get("server_top_p") is not None]
    summary["server_temp"] = stemps[-1] if stemps else None
    summary["server_top_p"] = stopps[-1] if stopps else None
    if stemps or stopps:
        print("sampling: server used temp=%s top_p=%s (as logged, not as assumed)" % (
            nn(summary["server_temp"]), nn(summary["server_top_p"])))
    else:
        print("sampling: NOT CONFIRMED (no sampler dump in this run's log window)")

    v_end, _, _ = gpu_vram()
    if free is not None and v_end is not None:
        summary["vram_free_start_mib"], summary["vram_free_end_mib"] = free, v_end
        print("vram    : %d -> %d MiB free (delta %+d) over this model's runs%s" % (
            free, v_end, v_end - free,
            "   WARNING: under %d MiB, stop and free VRAM before benching further"
            % LOW_VRAM_MIB if v_end < LOW_VRAM_MIB else ""))
    if summary["runs_invalid"]:
        print("EXCLUDED %d invalid run(s):" % summary["runs_invalid"])
        for r in result["runs"]:
            if not r["valid"]:
                print("  run%s: %s" % (r.get("run"), r["invalid_reason"]))
    for label, key in (("decode", "decode_n"), ("prefill", "prefill_n"),
                       ("acceptance", "acceptance_n")):
        if summary[key] == 0:
            print("%s: NOT MEASURED in any run (see the per-run reasons above)" % label)
    return result


def main():
    ap = argparse.ArgumentParser(
        description="Median-of-N decode/prefill/MTP-acceptance for the local lane. "
                    "Read-only: writes no files, changes no lane state.")
    ap.add_argument("--model", action="append", default=None,
                    help="model tag; repeatable for side-by-side. "
                         "Default: the lane model in config/local-lane.json")
    ap.add_argument("-n", type=int, default=3, help="measured runs per model (default 3)")
    ap.add_argument("--num-predict", type=int, default=300)
    ap.add_argument("--temp", type=float, default=None,
                    help="default: OMITTED, so the model's shipped temperature applies "
                         "(qwen3.8:27b ships 1). Pass 0.6 to measure what the mode-3 "
                         "normalizer injects, or 0 for determinism work -- but note that "
                         "temp 0 is greedy decoding on a thinking+MTP model, which risks "
                         "repetition degeneration AND measurably lowers draft acceptance, "
                         "so a temp-0 throughput number is not representative either.")
    ap.add_argument("--top-p", type=float, default=None,
                    help="default: OMITTED, so the model's shipped top_p applies (0.95)")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--host", default=None)
    ap.add_argument("--log", default=None, help="server log path override")
    ap.add_argument("--acceptance-wait", type=float, default=2.0,
                    help="seconds to wait for the server to flush print_timing")
    ap.add_argument("--prefill-tokens", type=int, default=0,
                    help="pad the prompt to approximately this many tokens before measuring. "
                         "0 (default) uses the bare 91-token prompt, whose prefill rate is "
                         "mostly fixed overhead and is NOT comparable to a large-prompt "
                         "figure. Pin the same value across any model comparison.")
    ap.add_argument("--min-prefill-tokens", type=int, default=32,
                    help="below this many evaluated prompt tokens, prefill is reported "
                         "null as a prefix-cache hit rather than as a rate")
    ap.add_argument("--no-nonce", action="store_true",
                    help="reuse one fixed prompt (reproduces the scratchpad predecessor; "
                         "prefill after run 1 will be a cache hit)")
    ap.add_argument("--json", action="store_true", help="emit the full record to stdout")
    args = ap.parse_args()

    lane = {}
    if os.path.isfile(LANE_CONFIG):
        with open(LANE_CONFIG, encoding="utf-8") as fh:
            lane = json.load(fh)
    args.host = args.host or lane.get("host") or "http://127.0.0.1:11434"
    models = args.model or ([lane["model"]] if lane.get("model") else [])
    if not models:
        print("no model: pass --model or populate config/local-lane.json", file=sys.stderr)
        return 2

    try:
        version = http_json(args.host + "/api/version", timeout=15).get("version")
    except Exception as exc:                                  # noqa: BLE001
        print("daemon unreachable at %s: %s" % (args.host, exc), file=sys.stderr)
        print("arm the lane with: pwsh -NoProfile -File tools/lane-arm.ps1",
              file=sys.stderr)
        return 2

    log_path, log_reason = find_server_log(args.log)
    lane_model = lane.get("model")

    print("lane-bench: ollama %s at %s" % (version, args.host))
    shown = lambda x: "model-default" if x is None else x   # noqa: E731
    print("config: n=%d num_predict=%d temp=%s top_p=%s seed=%d nonce=%s" % (
        args.n, args.num_predict, shown(args.temp), shown(args.top_p),
        args.seed, not args.no_nonce))
    if args.temp == 0:
        print("WARNING: --temp 0 is greedy decoding. On a thinking+MTP model this risks "
              "repetition degeneration, and it measurably LOWERS draft acceptance "
              "(0.563 vs 0.625 at temp 0.6, measured 2026-08-16), so the throughput "
              "number it produces is not representative of any production path except "
              "delegate.py. Valid for determinism work; do not quote it as the lane's speed.")
    print("server log: %s" % (log_path or "NOT FOUND (%s)" % log_reason))
    off_lane = [m for m in models if lane_model and m != lane_model]
    if off_lane:
        print("NOTE: benching %s evicts the lane model %s (OLLAMA_MAX_LOADED_MODELS=1). "
              "The next mode-3 or delegate call reloads it, costing one load." % (
                  ", ".join(off_lane), lane_model))

    record = {"ollama_version": version, "host": args.host, "lane_model": lane_model,
              "models": []}
    for m in models:
        record["models"].append(bench_model(args, m, log_path, log_reason))

    if len(models) > 1:
        print("\n=== side by side ===")
        print("%-42s %10s %10s %10s %12s" % (
            "model", "decode", "prefill", "accept", "prompt_tok"))
        for r in record["models"]:
            s = r.get("summary") or {}
            print("%-42s %10s %10s %10s %12s" % (
                r["model"], s.get("decode_tok_s_median"),
                s.get("prefill_tok_s_median"), s.get("acceptance_median"),
                s.get("prompt_tokens_median")))
        lens = {(r.get("summary") or {}).get("prompt_tokens_median")
                for r in record["models"]}
        lens.discard(None)
        if len(lens) > 1:
            print("WARNING: prompt lengths differ across models (%s). The prefill column "
                  "is NOT comparable. Re-run with --prefill-tokens pinned." % sorted(lens))
        print("Adoption rule (HANDOFF, pre-registered): ADOPT iff no regression on the "
              "discriminating suite AND prefill >= +15% AND decode >= -5%.")
        print("This tool reports numbers only. It does not apply the rule.")

    if args.json:
        print("\n" + json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
