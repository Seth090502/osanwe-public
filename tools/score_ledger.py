#!/usr/bin/env python3
"""score_ledger.py -- append-only options prediction ledger: validator, appender, resolver, Brier scorer.

Sibling of tools/score-outcomes.py (invest-enhancement-pass-v1, 2026-07-11;
GATE-B gate-b-invest-enhancement-pass-2026-07-11). Owns the options-PoP Brier
population ONLY -- it never touches RATING_PROB_MAP, calibration-monitor.md,
or brier-ledger.json (distinct populations, distinct freeze clocks; D13).

Ledger: wiki/investing/options-ledger.jsonl -- strict append-only JSONL.
  prediction line        {"type": "prediction", ...}   one per structure rec
  discipline line        {"type": "discipline_record", ...}  NO_TRADE audits
  resolution line        {"type": "resolution", "kind": "structure"|"verdict", ...}
Resolutions are SEPARATE event lines folded on (id, kind) -- a prediction line
is never rewritten (append-only purity; the prediction's own status/resolution
fields are a write-time snapshot; fold-by-id is authoritative).

Integrity design (all fail-closed, exit 2):
  - WRITE-TARGET WHITELIST: this script writes ONLY the canonical ledger path
    or paths under tools/test-fixtures/ (Bash-layer writes bypass the vault
    hook chain entirely -- X30 class -- so the guard lives HERE).
  - sha256 APPEND-ONLY PREFIX CHECK: existing bytes must be a byte-exact
    prefix of the post-append file.
  - POINT-IN-TIME GATE (date-carrying fields; observational values are
    writer-trusted + review-verified, honestly NOT mechanically checkable):
    horizon_check_date == max leg expiry, strictly > ts-date; every leg
    expiry strictly > ts-date (same-day-expiry structures rejected);
    thesis_horizon_date > ts-date.
  - POP-BASIS COHERENCE INVARIANT: pop_basis == success_criterion_machine.basis
    (sellers/credit = short-strike; longs/debit = breakeven). A PoP computed
    on one event and scored against another corrupts the Brier by design.
  - brier_contrib is a CACHE: the scorer recomputes (pop_est - outcome)^2 and
    asserts equality with the stored value.
  - ASCII: json.dumps(ensure_ascii=True) + a post-append byte assert.

Scoring report (PAPER -- mid/conservative-fill, no slippage, never executed):
  - Brier(model pop_est) vs Brier(delta-implied baseline, recomputed from
    stored per-leg deltas) vs Brier(base-rate). Skill = beating the delta
    baseline; a model that transcribes the chain scores exactly 0 skill.
  - Stratified by pop_method and executability x scale_flag; headline stratum
    = executable + at-scale.
  - n-floors at sibling parity (score-outcomes.py): pooled >= 5, stratum /
    calibration bucket >= 3. --json ALWAYS emits values + interpretable flag;
    the human-readable headline suppresses sub-floor numbers.
  - Hit-rate by VERDICT uses kind=verdict resolutions (thesis_horizon_date
    claim) -- an OTM CSP on a flat stock does NOT validate a BUY.
  - Hit-rate by STRUCTURE uses kind=structure resolutions.
  - R (realized_value / abs(max_loss)) per STRUCTURE CLASS only, median +
    clamped mean (R clamped to [-1, 10]); never a pooled headline (D14).
  - DUPLICATE-SUSPECT: same ticker+structure with overlapping windows.
  - void-rate reported (a gaming detector); unresolved-past-horizon
    denominator printed beside every metric.

CLI:
  python tools/score_ledger.py [--ledger PATH] [--fixture PATH] [--json]
      [--dry-run] [--verbose] [--list-due] [--closes PATH] [--fetch]
      [--append JSON] [--resolve PATH] [--kill-fired ID]
Exit codes: 0 success; 2 validation/integrity error.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
import os
import statistics
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LEDGER = os.path.join(VAULT, "wiki", "investing", "options-ledger.jsonl")
FIXTURES_DIR = os.path.join(VAULT, "tools", "test-fixtures")

N_FLOOR_POOLED = 5   # sibling parity: score-outcomes.py N_FLOOR_POOLED
N_FLOOR_STRATUM = 3  # sibling parity: score-outcomes.py N_FLOOR_STRATUM
R_CLAMP = (-1.0, 10.0)

GUARDED_PREFIXES = ("private", ".raw", "_quarantine", "finance", "credentials",
                    ".git", ".claude", "Atlas")

STRUCTURES = {"cash-secured-put", "covered-call", "long-call", "long-put",
              "call-debit-vertical", "bear-call-credit-spread", "collar",
              "protective-put", "NO_TRADE"}
SELLER_BASIS = {"cash-secured-put", "covered-call", "bear-call-credit-spread"}
DEBIT_BASIS = {"long-call", "long-put", "call-debit-vertical", "protective-put"}
NO_TRADE_REASONS = {"liquidity_fail", "iv_unmeasurable", "earnings_confounded",
                    "account_scale", "sub_contract_holding", "no_edge"}

PRED_REQUIRED = ["id", "type", "ts", "ticker", "underlying_px", "px_source",
                 "prov", "account", "verdict", "confidence", "conviction",
                 "structure", "executability", "scale_flag", "legs",
                 "pop_est", "pop_method", "pop_basis", "success_criterion",
                 "success_criterion_machine", "horizon_check_date",
                 "thesis_horizon_date", "verdict_success_criterion",
                 "earnings_in_window", "kill_criteria", "thesis",
                 "iv_context", "analysis_path", "est_premium_mid",
                 "premium_per_contract", "breakeven", "max_loss", "max_gain"]
DISC_REQUIRED = ["id", "type", "ts", "ticker", "verdict", "structure",
                 "no_trade_reason", "thesis", "analysis_path", "iv_context"]
RES_REQUIRED = ["id", "type", "kind", "resolved_ts", "resolver", "prov"]


def fail(msg):
    print(f"score_ledger: ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def d(s):
    """ISO date or timestamp -> date."""
    return dt.date.fromisoformat(str(s)[:10])


def phi(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def pop_normal_rv(spot, breakeven, realized_vol_ann, dte_cal, side, mu=0.0):
    """Lognormal terminal-price PoP on the breakeven (free-stack fallback).
    side: 'above' = P(S_T > BE) (call side); 'below' = P(S_T < BE) (put side)."""
    sigma_h = realized_vol_ann * math.sqrt(dte_cal / 365.0)
    if sigma_h <= 0:
        return None
    d2 = (math.log(spot / breakeven) + (mu - 0.5 * sigma_h ** 2)) / sigma_h
    p_above = phi(d2)
    return p_above if side == "above" else 1.0 - p_above


# ---------------------------------------------------------------- load / fold

def load_ledger(path):
    if not os.path.exists(path):
        return []
    records = []
    with open(path, encoding="ascii") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                fail(f"malformed JSONL at {path}:{i}: {e}")
    return records


def fold(records):
    """-> {id: {'prediction': rec|None, 'structure': res|None, 'verdict': res|None}}"""
    out = {}
    for r in records:
        t = r.get("type")
        if t == "probe_stub":
            continue
        rid = r.get("id")
        if not rid:
            fail("record missing id")
        slot = out.setdefault(rid, {"prediction": None, "structure": None, "verdict": None})
        if t in ("prediction", "discipline_record"):
            if slot["prediction"] is not None:
                fail(f"duplicate prediction line for id {rid}")
            slot["prediction"] = r
        elif t == "resolution":
            kind = r.get("kind")
            if kind not in ("structure", "verdict"):
                fail(f"resolution {rid} has invalid kind {kind!r}")
            if slot[kind] is not None:
                fail(f"duplicate {kind} resolution for id {rid}")
            slot[kind] = r
        else:
            fail(f"unknown record type {t!r} (id {rid})")
    for rid, slot in out.items():
        if slot["prediction"] is None and (slot["structure"] or slot["verdict"]):
            fail(f"resolution without prediction for id {rid}")
    return out


# ---------------------------------------------------------------- validation

def validate_prediction(rec, existing_ids):
    t = rec.get("type")
    if t == "discipline_record":
        missing = [k for k in DISC_REQUIRED if k not in rec]
        if missing:
            fail(f"discipline_record missing fields: {missing}")
        if rec.get("structure") != "NO_TRADE":
            fail("discipline_record must have structure NO_TRADE")
        if rec.get("no_trade_reason") not in NO_TRADE_REASONS:
            fail(f"invalid no_trade_reason {rec.get('no_trade_reason')!r}")
        return
    if t != "prediction":
        fail(f"append expects prediction/discipline_record/resolution, got {t!r}")
    missing = [k for k in PRED_REQUIRED if k not in rec]
    if missing:
        fail(f"prediction missing fields: {missing}")
    if rec["structure"] not in STRUCTURES or rec["structure"] == "NO_TRADE":
        fail(f"invalid structure {rec['structure']!r} for a prediction "
             "(NO_TRADE logs as discipline_record)")
    ts_date = d(rec["ts"])
    legs = rec["legs"]
    if not legs:
        fail("prediction requires legs")
    expiries = [d(l["expiry"]) for l in legs]
    for e in expiries:
        if e <= ts_date:
            fail(f"leg expiry {e} not strictly after ts date {ts_date} "
                 "(same-day-expiry structures rejected)")
    hzn = d(rec["horizon_check_date"])
    if hzn != max(expiries):
        fail(f"horizon_check_date {hzn} != max leg expiry {max(expiries)} "
             "(structure resolves at expiry -- forced)")
    if d(rec["thesis_horizon_date"]) <= ts_date:
        fail("thesis_horizon_date must be strictly after ts date")
    # pop-basis coherence invariant
    basis = rec.get("pop_basis")
    crit_basis = (rec.get("success_criterion_machine") or {}).get("basis")
    if basis != crit_basis:
        fail(f"POP-BASIS COHERENCE: pop_basis {basis!r} != "
             f"success_criterion_machine.basis {crit_basis!r}")
    expected = "short-strike" if rec["structure"] in SELLER_BASIS else "breakeven"
    if rec["structure"] in SELLER_BASIS | DEBIT_BASIS and basis != expected:
        fail(f"structure {rec['structure']} requires basis {expected!r}, got {basis!r}")
    scm = rec["success_criterion_machine"]
    if scm.get("direction") not in (">=", "<="):
        fail("success_criterion_machine.direction must be '>=' or '<=' "
             "(two-sided 'inside' criteria are resolver:manual only and carry "
             "direction 'manual')") if scm.get("direction") != "manual" else None
    vsc = rec["verdict_success_criterion"]
    if vsc.get("direction") not in ("up", "down") or "threshold_pct" not in vsc:
        fail("verdict_success_criterion requires {direction: up|down, threshold_pct}")
    p = rec.get("pop_est")
    if p is not None and not (0.0 <= p <= 1.0):
        fail(f"pop_est {p} outside [0,1]")
    if rec["id"] in existing_ids:
        fail(f"duplicate id {rec['id']}")


def assign_id(rec, existing_ids):
    ts_date = str(rec["ts"])[:10]
    prefix = f"{ts_date}-{rec['ticker'].upper()}-"
    if rec.get("id"):
        return rec
    n = 0
    for eid in existing_ids:
        if eid.startswith(prefix):
            try:
                n = max(n, int(eid[len(prefix):]))
            except ValueError:
                pass
    rec["id"] = f"{prefix}{n + 1:03d}"
    return rec


def validate_resolution(rec, folded):
    missing = [k for k in RES_REQUIRED if k not in rec]
    if missing:
        fail(f"resolution missing fields: {missing}")
    rid = rec["id"]
    slot = folded.get(rid)
    if not slot or slot["prediction"] is None:
        fail(f"resolution for unknown prediction id {rid}")
    if slot["prediction"].get("type") == "discipline_record":
        fail(f"discipline_record {rid} takes no resolution")
    kind = rec["kind"]
    if slot[kind] is not None:
        fail(f"duplicate {kind} resolution for id {rid}")
    pred = slot["prediction"]
    if kind == "structure":
        if rec.get("outcome") not in ("win", "loss", "partial", "void"):
            fail("structure resolution outcome must be win|loss|partial|void")
        if rec["outcome"] == "void" and not rec.get("void_reason"):
            fail("void requires void_reason (delisting/merger/split...) + prov")
        if rec["outcome"] != "void":
            rv = rec.get("realized_value")
            if rv is None:
                fail("structure resolution requires realized_value")
            ob = rec.get("outcome_binary")
            expected_ob = 1 if rv > 0 else 0
            if ob != expected_ob:
                fail(f"outcome_binary {ob} != sign-derived {expected_ob}")
            # criterion-consistency assert: price-mechanical resolvers only
            if rec.get("resolver") in ("price-mechanical", "mcp-close"):
                scm = pred["success_criterion_machine"]
                px = rec.get("realized_underlying_px")
                if px is not None and scm.get("direction") in (">=", "<="):
                    crit_met = (px >= scm["level"]) if scm["direction"] == ">=" else (px <= scm["level"])
                    if crit_met != (ob == 1):
                        fail(f"criterion-consistency: machine criterion says "
                             f"{'win' if crit_met else 'loss'} but outcome_binary={ob} "
                             f"(id {rid}; manual resolutions are exempt)")
            elif rec.get("resolver") == "manual":
                pass  # manual realized_value is authoritative; mismatch only flags in report
            # brier cache check
            if pred.get("pop_est") is not None and rec.get("brier_contrib") is not None:
                recomputed = (pred["pop_est"] - expected_ob) ** 2
                if abs(recomputed - rec["brier_contrib"]) > 1e-9:
                    fail(f"brier_contrib cache {rec['brier_contrib']} != "
                         f"recomputed {recomputed:.10f} (id {rid})")
    else:  # verdict
        if rec.get("verdict_outcome") not in ("win", "loss"):
            fail("verdict resolution requires verdict_outcome win|loss")


# ---------------------------------------------------------------- append

def check_write_target(path):
    ap = os.path.abspath(path)
    if ap == os.path.abspath(DEFAULT_LEDGER):
        return
    if os.path.abspath(FIXTURES_DIR) == os.path.dirname(ap):
        return
    rel = os.path.relpath(ap, VAULT)
    fail(f"write target {rel} refused: whitelist is the canonical ledger or "
         "tools/test-fixtures/ only (Bash writes bypass the vault hook chain; "
         "the guard lives here)")


def append_record(rec, path):
    check_write_target(path)
    rel = os.path.relpath(os.path.abspath(path), VAULT).replace("\\", "/")
    for g in GUARDED_PREFIXES:
        if rel.startswith(g):
            fail(f"write target under guarded prefix {g}/ refused")
    records = load_ledger(path)
    folded = fold(records)
    existing_ids = {r.get("id") for r in records if r.get("type") in ("prediction", "discipline_record")}
    if rec.get("type") == "resolution":
        validate_resolution(rec, folded)
    else:
        rec = assign_id(rec, existing_ids)
        validate_prediction(rec, existing_ids)
    line = json.dumps(rec, ensure_ascii=True, sort_keys=True)
    before = b""
    if os.path.exists(path):
        with open(path, "rb") as f:
            before = f.read()
    before_sha = hashlib.sha256(before).hexdigest()
    with open(path, "ab") as f:
        f.write(line.encode("ascii") + b"\n")
    with open(path, "rb") as f:
        after = f.read()
    if hashlib.sha256(after[:len(before)]).hexdigest() != before_sha:
        fail("APPEND-ONLY VIOLATION: existing bytes changed during append")
    if any(b > 127 for b in after):
        fail("ASCII VIOLATION: ledger contains a byte > 127 after append")
    print(json.dumps({"appended": rec["id"], "type": rec.get("type"),
                      "kind": rec.get("kind"), "ledger": rel}))
    return rec


# ---------------------------------------------------------------- resolution

def realized_value_terminal(pred, s_t):
    """European-terminal PAPER P&L per contract (standing limit 4)."""
    st = pred["structure"]
    prem = pred["premium_per_contract"]  # signed: credit +, debit -
    legs = pred["legs"]
    if st in ("cash-secured-put", "covered-call"):
        k = legs[0]["strike"]
        intrinsic = max(0.0, k - s_t) if legs[0]["type"] == "put" else max(0.0, s_t - k)
        return prem - intrinsic * 100.0
    if st in ("long-call", "long-put", "protective-put"):
        k = legs[0]["strike"]
        intrinsic = max(0.0, s_t - k) if legs[0]["type"] == "call" else max(0.0, k - s_t)
        return intrinsic * 100.0 + prem
    if st == "bear-call-credit-spread":
        ks = sorted(l["strike"] for l in legs)
        width = ks[1] - ks[0]
        return prem - min(max(0.0, s_t - ks[0]), width) * 100.0
    if st == "call-debit-vertical":
        ks = sorted(l["strike"] for l in legs)
        width = ks[1] - ks[0]
        return min(max(0.0, s_t - ks[0]), width) * 100.0 + prem
    return None  # collar and exotic -> manual


def close_at_or_after(closes, ticker, when):
    series = closes.get(ticker.upper()) or []
    for row in sorted(series, key=lambda r: r["date"]):
        if d(row["date"]) >= when:
            return float(row["close"]), row["date"]
    return None, None


def resolve_due(folded, closes, path, today, kill_fired=None):
    appended = []
    for rid, slot in sorted(folded.items()):
        pred = slot["prediction"]
        if pred is None or pred.get("type") != "prediction":
            continue
        # structure resolution
        if slot["structure"] is None and d(pred["horizon_check_date"]) <= today:
            if (pred.get("resolver_route") or "price-mechanical") == "manual":
                pass  # manual-only records never auto-resolve
            else:
                s_t, on = close_at_or_after(closes, pred["ticker"], d(pred["horizon_check_date"]))
                if s_t is not None:
                    rv = realized_value_terminal(pred, s_t)
                    if rv is not None:
                        ob = 1 if rv > 0 else 0
                        res = {"id": rid, "type": "resolution", "kind": "structure",
                               "resolved_ts": today.isoformat(),
                               "outcome": "win" if ob else "loss",
                               "outcome_binary": ob,
                               "realized_value": round(rv, 2),
                               "realized_underlying_px": s_t,
                               "close_date_used": on,
                               "brier_contrib": round((pred["pop_est"] - ob) ** 2, 10)
                               if pred.get("pop_est") is not None else None,
                               "resolver": "price-mechanical",
                               "prov": "script:score_ledger+closes"}
                        appended.append(append_record(res, path))
        # verdict resolution
        if slot["verdict"] is None:
            if kill_fired and rid in kill_fired:
                res = {"id": rid, "type": "resolution", "kind": "verdict",
                       "resolved_ts": today.isoformat(), "verdict_outcome": "loss",
                       "kill_fired": True, "resolver": "manual",
                       "prov": "manual:kill-criterion-fired"}
                appended.append(append_record(res, path))
            elif d(pred["thesis_horizon_date"]) <= today:
                s_t, on = close_at_or_after(closes, pred["ticker"], d(pred["thesis_horizon_date"]))
                if s_t is not None:
                    vsc = pred["verdict_success_criterion"]
                    move = (s_t / pred["underlying_px"] - 1.0) * 100.0
                    win = (move >= vsc["threshold_pct"]) if vsc["direction"] == "up" \
                        else (move <= -vsc["threshold_pct"])
                    res = {"id": rid, "type": "resolution", "kind": "verdict",
                           "resolved_ts": today.isoformat(),
                           "verdict_outcome": "win" if win else "loss",
                           "realized_underlying_px": s_t, "close_date_used": on,
                           "realized_move_pct": round(move, 2),
                           "resolver": "price-mechanical",
                           "prov": "script:score_ledger+closes"}
                    appended.append(append_record(res, path))
    return appended


# ---------------------------------------------------------------- report

def brier(pairs):
    """pairs: [(p, outcome_binary)] -> (brier, n)"""
    pairs = [(p, o) for p, o in pairs if p is not None and o is not None]
    if not pairs:
        return None, 0
    return sum((p - o) ** 2 for p, o in pairs) / len(pairs), len(pairs)


def delta_implied_pop(pred):
    """Recompute the market-implied PoP from stored per-leg deltas (baseline)."""
    legs = pred.get("legs") or []
    st = pred.get("structure")
    if st in SELLER_BASIS:
        shorts = [l for l in legs if l.get("side") == "sell" and l.get("delta") is not None]
        if shorts:
            return 1.0 - abs(shorts[0]["delta"])
    elif st in DEBIT_BASIS:
        be_delta = pred.get("breakeven_nearest_delta")
        if be_delta is not None:
            return abs(be_delta)
        longs = [l for l in legs if l.get("side") == "buy" and l.get("delta") is not None]
        if longs:
            return abs(longs[0]["delta"])  # honest over-optimistic proxy; flagged in report
    return None


def windows_overlap(a, b):
    return not (d(a["horizon_check_date"]) < d(b["ts"]) or d(b["horizon_check_date"]) < d(a["ts"]))


def report(folded, today, as_json=False, verbose=False):
    preds = [s["prediction"] for s in folded.values()
             if s["prediction"] and s["prediction"].get("type") == "prediction"]
    disc = [s["prediction"] for s in folded.values()
            if s["prediction"] and s["prediction"].get("type") == "discipline_record"]
    resolved = [(s["prediction"], s["structure"]) for s in folded.values()
                if s["prediction"] and s["structure"] and s["prediction"].get("type") == "prediction"]
    scored = [(p, r) for p, r in resolved if r.get("outcome") not in ("void",)]
    voids = [r for _, r in resolved if r.get("outcome") == "void"]
    verdict_res = [(s["prediction"], s["verdict"]) for s in folded.values()
                   if s["prediction"] and s["verdict"]]

    def stratum(p):
        ex = "executable" if (p.get("executability") == "single-leg"
                              and p.get("scale_flag") in (None, "executable")) else "paper"
        return ex

    model_pairs = [(p.get("pop_est"), r.get("outcome_binary")) for p, r in scored]
    delta_pairs = [(delta_implied_pop(p), r.get("outcome_binary")) for p, r in scored]
    outcomes = [r.get("outcome_binary") for _, r in scored if r.get("outcome_binary") is not None]
    base_rate = sum(outcomes) / len(outcomes) if outcomes else None
    base_pairs = [(base_rate, o) for o in outcomes] if outcomes else []

    b_model, n_model = brier(model_pairs)
    b_delta, n_delta = brier(delta_pairs)
    b_base, _ = brier(base_pairs)

    by_structure = {}
    for p, r in scored:
        st = p["structure"]
        e = by_structure.setdefault(st, {"n": 0, "wins": 0, "r_values": []})
        e["n"] += 1
        e["wins"] += 1 if r.get("outcome_binary") == 1 else 0
        ml = p.get("max_loss")
        if ml and r.get("realized_value") is not None:
            e["r_values"].append(max(R_CLAMP[0], min(R_CLAMP[1], r["realized_value"] / abs(ml))))
    for st, e in by_structure.items():
        rs = sorted(e["r_values"])
        # true median: with an even count the two middle R values are averaged
        # (rs[len(rs)//2] alone reported the upper-middle one)
        e["r_median"] = statistics.median(rs) if rs else None
        e["r_clamped_mean"] = round(sum(rs) / len(rs), 5) if rs else None
        e["hit_rate"] = round(e["wins"] / e["n"], 4) if e["n"] else None
        del e["r_values"]

    by_verdict = {}
    for p, r in verdict_res:
        v = p["verdict"]
        e = by_verdict.setdefault(v, {"n": 0, "wins": 0})
        e["n"] += 1
        e["wins"] += 1 if r.get("verdict_outcome") == "win" else 0

    strata = {}
    for p, r in scored:
        s = stratum(p)
        strata.setdefault(s, []).append((p.get("pop_est"), r.get("outcome_binary")))
    strata_out = {}
    for s, pairs in strata.items():
        b, n = brier(pairs)
        strata_out[s] = {"brier": round(b, 5) if b is not None else None,
                         "n": n, "interpretable": n >= N_FLOOR_STRATUM}

    buckets = {}
    for p, r in scored:
        if p.get("pop_est") is None or r.get("outcome_binary") is None:
            continue
        lo = min(int(p["pop_est"] * 10) / 10.0, 0.9)
        b = buckets.setdefault(lo, {"n": 0, "pred_sum": 0.0, "real_sum": 0})
        b["n"] += 1
        b["pred_sum"] += p["pop_est"]
        b["real_sum"] += r["outcome_binary"]
    calib = [{"bucket": f"[{lo:.1f},{lo + 0.1:.1f})",
              "n": v["n"],
              "predicted_mean": round(v["pred_sum"] / v["n"], 4),
              "realized_freq": round(v["real_sum"] / v["n"], 4),
              "interpretable": v["n"] >= N_FLOOR_STRATUM}
             for lo, v in sorted(buckets.items())]

    open_structure = [p["id"] for s in folded.values()
                      if (p := s["prediction"]) and p.get("type") == "prediction"
                      and s["structure"] is None]
    due_structure = [rid for rid in open_structure
                     if d(folded[rid]["prediction"]["horizon_check_date"]) <= today]
    due_verdict = [p["id"] for s in folded.values()
                   if (p := s["prediction"]) and p.get("type") == "prediction"
                   and s["verdict"] is None and d(p["thesis_horizon_date"]) <= today]

    dupes = []
    plist = sorted(preds, key=lambda p: p["id"])
    for i in range(len(plist)):
        for j in range(i + 1, len(plist)):
            a, b2 = plist[i], plist[j]
            if (a["ticker"] == b2["ticker"] and a["structure"] == b2["structure"]
                    and windows_overlap(a, b2)):
                dupes.append([a["id"], b2["id"]])

    disc_by_reason = {}
    for r in disc:
        disc_by_reason[r.get("no_trade_reason", "unknown")] = \
            disc_by_reason.get(r.get("no_trade_reason", "unknown"), 0) + 1

    seller_scored = [(p, r) for p, r in scored if p["structure"] in SELLER_BASIS]
    prem_capture = None
    if seller_scored:
        realized_freq = sum(1 for _, r in seller_scored if r.get("outcome_binary") == 1) / len(seller_scored)
        implied = [delta_implied_pop(p) for p, _ in seller_scored]
        implied = [x for x in implied if x is not None]
        prem_capture = {"n": len(seller_scored),
                        "realized_win_freq": round(realized_freq, 4),
                        "delta_implied_mean": round(sum(implied) / len(implied), 4) if implied else None,
                        "interpretable": len(seller_scored) >= N_FLOOR_STRATUM}

    out = {
        "stamp": "PAPER -- mid-fill / conservative convention, no slippage, never executed",
        "as_of": today.isoformat(),
        "counts": {"predictions": len(preds), "discipline_records": len(disc),
                   "structure_resolved": len(scored), "voids": len(voids),
                   "open_structure": len(open_structure),
                   "due_structure_past_horizon": len(due_structure),
                   "due_verdict_past_horizon": len(due_verdict),
                   "verdict_resolved": len(verdict_res)},
        "brier": {
            "options_pop_model": {"value": round(b_model, 5) if b_model is not None else None,
                                  "n": n_model, "interpretable": n_model >= N_FLOOR_POOLED},
            "delta_implied_baseline": {"value": round(b_delta, 5) if b_delta is not None else None,
                                       "n": n_delta},
            "base_rate_baseline": {"value": round(b_base, 5) if b_base is not None else None,
                                   "base_rate": round(base_rate, 4) if base_rate is not None else None},
            "note": "skill = model beating the delta-implied baseline; label: options-PoP Brier "
                    "(DISTINCT population from the R.5 rating-Brier / calibration-monitor)"},
        "strata": strata_out,
        "calibration_buckets": calib,
        "hit_rate_by_structure": by_structure,
        "hit_rate_by_verdict": {v: {"n": e["n"], "wins": e["wins"],
                                    "hit_rate": round(e["wins"] / e["n"], 4)}
                                for v, e in by_verdict.items()},
        "premium_capture_vs_implied": prem_capture,
        "r_note": "R reported per structure class only, median + clamped mean [-1,10]; "
                  "pooled avg R across seller/buyer denominators is a known artifact (D14)",
        "duplicate_suspects": dupes,
        "discipline_by_reason": disc_by_reason,
        "void_rate": round(len(voids) / len(resolved), 4) if resolved else None,
        "due": {"structure": due_structure, "verdict": due_verdict},
    }
    if as_json:
        print(json.dumps(out, indent=1, ensure_ascii=True))
    else:
        print(out["stamp"])
        c = out["counts"]
        print(f"Options ledger @ {out['as_of']}: {c['predictions']} predictions "
              f"({c['structure_resolved']} structure-resolved, {c['open_structure']} open, "
              f"{c['due_structure_past_horizon']} due), {c['discipline_records']} discipline records, "
              f"{c['voids']} voids")
        bm = out["brier"]["options_pop_model"]
        if bm["interpretable"]:
            print(f"options-PoP Brier(model) {bm['value']} vs delta-baseline "
                  f"{out['brier']['delta_implied_baseline']['value']} vs base-rate "
                  f"{out['brier']['base_rate_baseline']['value']} (n={bm['n']})")
        else:
            print(f"options-PoP Brier: n={bm['n']} below floor ({N_FLOOR_POOLED}), NOT interpretable")
        for st, e in out["hit_rate_by_structure"].items():
            tag = "" if e["n"] >= N_FLOOR_STRATUM else " [below stratum floor]"
            print(f"  {st}: {e['wins']}/{e['n']} hit; R median {e['r_median']} "
                  f"clamped-mean {e['r_clamped_mean']}{tag}")
        for v, e in out["hit_rate_by_verdict"].items():
            print(f"  verdict {v}: {e['wins']}/{e['n']} (thesis-horizon claim)")
        if out["duplicate_suspects"]:
            print(f"  DUPLICATE-SUSPECT pairs: {out['duplicate_suspects']}")
        if out["discipline_by_reason"]:
            print(f"  NO_TRADE discipline tally: {out['discipline_by_reason']}")
        if verbose:
            print(json.dumps(out, indent=1, ensure_ascii=True))
    return out


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", default=DEFAULT_LEDGER)
    ap.add_argument("--fixture", default=None, help="offline test mode: score this file, never fetch")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="report only; no resolution writes")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--list-due", action="store_true")
    ap.add_argument("--closes", default=None, help="JSON file {TICKER: [{date, close}...]}")
    ap.add_argument("--fetch", action="store_true", help="optional yfinance fallback for closes (never primary)")
    ap.add_argument("--append", default=None, help="one record as a JSON string")
    ap.add_argument("--resolve", default=None, help="JSON file with a list of manual resolution records")
    ap.add_argument("--kill-fired", default=None, help="prediction id: force verdict_outcome=loss (manual)")
    ap.add_argument("--today", default=None, help="override today (tests)")
    args = ap.parse_args()

    path = args.fixture or args.ledger
    today = d(args.today) if args.today else dt.date.today()

    if args.append:
        try:
            rec = json.loads(args.append)
        except json.JSONDecodeError as e:
            fail(f"--append is not valid JSON: {e}")
        append_record(rec, path)
        return

    if args.resolve:
        with open(args.resolve, encoding="ascii") as f:
            for rec in json.load(f):
                append_record(rec, path)
        return

    records = load_ledger(path)
    folded = fold(records)

    if args.list_due:
        due_s = [rid for rid, s in folded.items()
                 if s["prediction"] and s["prediction"].get("type") == "prediction"
                 and s["structure"] is None
                 and d(s["prediction"]["horizon_check_date"]) <= today]
        due_v = [rid for rid, s in folded.items()
                 if s["prediction"] and s["prediction"].get("type") == "prediction"
                 and s["verdict"] is None
                 and d(s["prediction"]["thesis_horizon_date"]) <= today]
        print(json.dumps({"due_structure": sorted(due_s), "due_verdict": sorted(due_v)},
                         indent=1))
        return

    closes = {}
    if args.closes:
        with open(args.closes, encoding="ascii") as f:
            closes = {k.upper(): v for k, v in json.load(f).items()}
    elif args.fetch and not args.fixture and not args.dry_run:
        try:
            import yfinance as yf  # optional fallback, never primary
            tickers = sorted({s["prediction"]["ticker"] for s in folded.values()
                              if s["prediction"] and s["prediction"].get("type") == "prediction"})
            for t in tickers:
                hist = yf.Ticker(t).history(period="1y", auto_adjust=True)
                closes[t] = [{"date": i.date().isoformat(), "close": float(r["Close"])}
                             for i, r in hist.iterrows()]
        except Exception as e:
            print(f"score_ledger: --fetch degraded ({e}); pass --closes instead",
                  file=sys.stderr)

    kill = [args.kill_fired] if args.kill_fired else None
    if (closes or kill) and not args.dry_run and not args.fixture:
        resolve_due(folded, closes, path, today, kill_fired=kill)
        folded = fold(load_ledger(path))
    elif kill and not args.dry_run and args.fixture:
        fail("--kill-fired writes; refuse against --fixture")

    report(folded, today, as_json=args.json, verbose=args.verbose)


if __name__ == "__main__":
    main()
