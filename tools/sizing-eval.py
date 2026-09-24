#!/usr/bin/env python3
"""
Osanwe SIZING-EVAL (INVEST KERNEL, 2026-07-06; P1 rate-gate replacement
2026-07-30).

The model NEVER does position-sizing arithmetic: it fills a {value, prov}
input form, this script computes (Half-Kelly two-form + the W1-W8 cap
waterfall + the deployment state from raw series + the reserve-release
evaluation), and the model transcribes the emitted worksheet verbatim into
the analysis (K-bis.7). `--check` re-derives everything from the worksheet's
own machine block before any vault write (Pre-Output gate 10b) -- hand-editing
worksheet numbers is forbidden; recovery is always a fresh `--compute`.

Usage:
  sizing-eval.py --compute --mode add|hold-state --inputs <path|-> --book <path>
                 [--today YYYY-MM-DD] [--worksheet-out <path>] [--json]
  sizing-eval.py --check <analysis-or-worksheet.md> [--today YYYY-MM-DD] [--json]
  (doctrine-lint runs first in both modes; lint failure -> exit 2, no sizing.)

Inputs file: JSON object; every top-level field is {"value": ..., "prov": "..."}
with a NON-EMPTY prov (gate-marker discipline). See
.claude/skills/invest/ref-kernel-sizing.md for the field-by-field form.
Exit: 0 = ok / SIZE-OK / NO-TRADE / HOLD-STATE, 2 = any defect (fail-closed).
ASCII-only (Pattern 22). Deps: stdlib + PyYAML + tools/kernel_lib.py.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, r"/path/to/vault\tools")
import kernel_lib as K  # noqa: E402
import yaml  # noqa: E402

LINT = str(K.VAULT_ROOT / "tools" / "doctrine-lint.py")

REQUIRED_ADD = [
    "symbol", "rating", "entry", "stop", "stop_basis", "target_model",
    "target_basis", "target_analyst_median", "account", "account_cash",
    "is_crypto", "scoring_path", "corr_gt_threshold_flag", "thesis_list",
    "effective_thesis_pct", "dfii10_series", "dgs10_series", "vix_series",
    "rate_prov", "dgs10_prov", "spx_close", "spx_trailing_high",
    "theme_alpha_eff_pct", "override",
]
REQUIRED_HOLD = [
    "symbol", "thesis_list", "effective_thesis_pct", "dfii10_series",
    "dgs10_series", "vix_series", "rate_prov", "dgs10_prov", "is_crypto",
]
# cash_reserve additionally required when account == tax_advantaged (kernel_lib enforces).

# Provenance fields the kernel reads directly off `values`; they are DERIVED
# from the prov of their carrier series/scalar, never fillable independently.
DERIVED_PROV_KEYS = ("rate_prov", "dgs10_prov", "vix_prov", "spx_prov", "theme_alpha_prov")

ANALYSIS_MANDATORY_FM = [
    "rating", "price_at_analysis", "rr_ratio", "position_size_pct",
    "doctrine_version", "doctrine_fingerprint", "deployment_band",
    "deployment_override", "gate_f", "kill_criteria", "thesis_line",
]


def fail(msg, as_json=False):
    if as_json:
        print(json.dumps({"ok": False, "error": msg}))
    else:
        print("SIZING-EVAL: FAIL -- %s" % msg)
    return 2


def run_lint():
    """Fail-closed pre-step: corrupted/tampered doctrine fails at first use."""
    r = subprocess.run([sys.executable, LINT, "--json"], capture_output=True, text=True)
    if r.returncode != 0:
        raise K.KernelError("doctrine-lint failed (exit %d): %s"
                            % (r.returncode, (r.stdout or r.stderr)[:500]))


def attach_derived_provs(values, provs):
    """Single definition of the derived-prov wiring, shared by --compute and
    --check so the two paths can never diverge (the P1 divergence trap)."""
    values["rate_prov"] = provs.get("dfii10_series") or values.get("rate_prov")
    values["dgs10_prov"] = provs.get("dgs10_series") or values.get("dgs10_prov")
    values["vix_prov"] = provs.get("vix_series") or values.get("vix_prov")
    values["spx_prov"] = provs.get("spx_close") or values.get("spx_prov")
    values["theme_alpha_prov"] = provs.get("theme_alpha_eff_pct") or values.get("theme_alpha_prov")
    return values


def load_inputs(spec, mode):
    """Load + validate the {value, prov} form. Returns (values, provs)."""
    raw = sys.stdin.read() if spec == "-" else Path(spec).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise K.KernelError("inputs must be a JSON object")
    required = REQUIRED_ADD if mode == "add" else REQUIRED_HOLD
    values, provs = {}, {}
    for key in required:
        if key not in data:
            raise K.KernelError("inputs missing required field: %s" % key)
    for key, entry in data.items():
        if not (isinstance(entry, dict) and "value" in entry and
                str(entry.get("prov", "")).strip()):
            raise K.KernelError("input '%s' must be {value, prov} with non-empty prov" % key)
        values[key] = entry["value"]
        provs[key] = str(entry["prov"])
    return attach_derived_provs(values, provs), provs


def render_yaml_block(payload):
    return "```kernel:sizing\n" + yaml.safe_dump(
        K._norm(payload), sort_keys=True, default_flow_style=False, width=100
    ).rstrip() + "\n```"


def _fmt_usd(x):
    return "%.2f" % float(x)


def _dep_line(dep):
    """The P1 deployment disclosure: state, multiplier, and BOTH legs' inputs
    (a reader must be able to see WHY without re-running anything)."""
    rate = ("%s %+.1fbp over %s obs (recon %s sessions)"
            % (dep.get("rate_series", "DFII10"), dep["rate_delta_bp"],
               dep.get("rate_lookback_sessions", "?"),
               dep.get("rate_reconstruction_sessions", 0))
            if dep.get("rate_delta_bp") is not None else "rate n/a")
    conf = ("confirm %+.1fbp" % dep["rate_confirm_bp"]
            if dep.get("rate_confirm_bp") is not None else "confirm n/a")
    vix = ("VIX max5 %.2f" % dep["vix_max_recent"]
           if dep.get("vix_max_recent") is not None else "VIX n/a")
    return "state %s mult %s (%s, %s, streak %d; %s)" % (
        dep["state"], dep["multiplier"], rate, conf, dep.get("rate_fire_streak", 0), vix)


def _reserve_line(rr):
    if not rr:
        return "Reserve release: not evaluated"
    if not rr.get("applicable"):
        return "Reserve release: N/A (taxable account; no cash reserve)"
    bits = []
    for cid, c in sorted(rr.get("conditions", {}).items()):
        bits.append("%s=%s" % (cid, c.get("status", "unknown")))
    return ("Reserve release: %s -- reserve $%s, applied $%s [%s]%s"
            % ("RELEASED" if rr.get("released") else "held",
               _fmt_usd(rr.get("reserve_amount", 0)), _fmt_usd(rr.get("reserve_applied", 0)),
               " | ".join(bits),
               (" by " + ", ".join(rr.get("released_by") or [])) if rr.get("released") else ""))


def render_worksheet(mode, payload, result):
    lines = []
    if mode == "add":
        lines.append("### Position Sizing Worksheet (K-bis.7, BINDING)")
    else:
        lines.append("### Position Sizing Worksheet (K-bis.7, HOLD-STATE compliance panel)")
    lines.append("")
    lines.append(render_yaml_block(payload))
    lines.append("")
    lines.append("Rendered arithmetic (emitted by tools/sizing-eval.py --compute; transcribed verbatim -- hand-editing forbidden):")
    if mode == "add":
        r = result
        if r["verdict"] == "SIZE-OK":
            dep = r["deployment"]
            lines += [
                "1. sizing target = %s (MIN rule)" % r["sizing_target"],
                "2. b_raw = %.6f (hurdle PASS); b = %.6f after b_cap" % (r["b_raw"], r["b"]),
                "3. p = %s (win_prob table)" % r["p"],
                "4. F1 = %.6f ; F2 = %.6f ; identity PASS" % (r["f_full_form1"], r["f_full_form2"]),
                "5. f_half = %.6f ; haircuts %s -> f_adj = %.6f"
                % (r["f_half"], (r["haircuts"] or ["none"]), r["f_adjusted"]),
                "6. W3 dollars = %.6f x %s = %s" % (r["f_adjusted"], _fmt_usd(r["book_total"]),
                                                    _fmt_usd(r["w3_raw_dollars"])),
                "7. W4 caps: %s -> W6 = %s (binding: %s)"
                % (" | ".join("%s %s" % (k, _fmt_usd(v)) for k, v in r["caps"].items()),
                   _fmt_usd(r["w6_computed_size"]), r["binding_chain"][0]),
                "8. W7 deployment: %s%s -> final pre-floor"
                % (_dep_line(dep), " OVERRIDE-%gpct" % float(
                    payload["doctrine_override_tranche_pct"]) if r["override_used"] else ""),
                "9. W8 de-minimis floor PASS",
                "10. FINAL = $%s = %.6f shares ; binding chain: %s"
                % (_fmt_usd(r["final_dollars"]), r["final_shares"],
                   " -> ".join(r["binding_chain"])),
                _reserve_line(r.get("reserve_release")),
                "Override availability: %d/%d conditions met; %s"
                % (r["override_availability"]["conditions_met"], r["override_availability"]["of"],
                   "INVOKED (verbatim user directive recorded in block)" if r["override_used"]
                   else "not invoked (model never self-invokes)"),
                "Reconciliation: |shares x entry - dollars| = %.4f <= 0.50 PASS"
                % abs(r["final_shares"] * float(payload["inputs"]["entry"]["value"])
                      - r["final_dollars"]),
            ]
        else:
            lines.append("VERDICT: %s [%s] -- %s"
                         % (r["verdict"], r.get("reason_code", "n/a"), r.get("reason", "")))
            if r.get("deployment"):
                lines.append("8. W7 deployment: %s" % _dep_line(r["deployment"]))
            if r.get("binding_chain"):
                lines.append("Binding chain: %s" % " -> ".join(r["binding_chain"]))
            lines.append(_reserve_line(r.get("reserve_release")))
            if r.get("override_availability"):
                lines.append("Override availability: %d/%d conditions met"
                             % (r["override_availability"]["conditions_met"],
                                r["override_availability"]["of"]))
    else:
        r = result
        lines.append("Single-name: %.2f%% (%s; amber %s / red %s)"
                     % (r["name_pct"], r["single_name_status"],
                        r["single_name_amber_pct"], r["single_name_red_pct"]))
        for t, d in r["theses"].items():
            lines.append("Thesis %s: %.2f%% vs line %s%% (%s; headroom $%s)"
                         % (t, d["pct_used"], d["line_pct"], d["status"],
                            _fmt_usd(d["headroom_usd"])))
        lines.append("Deployment: %s" % _dep_line(r["deployment"]))
        lines.append("Max tranche if adding: $%s (5%% of book)" % _fmt_usd(r["max_tranche_usd_if_add"]))
        for n in r["notes"]:
            lines.append("NOTE: %s" % n)
    return "\n".join(lines)


def do_compute(args):
    run_lint()
    doctrine, _, _ = K.load_block("doctrine")
    bands, _, _ = K.load_block("bands")
    values, provs = load_inputs(args.inputs, args.mode)
    book = json.loads(Path(args.book).read_text(encoding="utf-8"))
    total, name_pct, thesis_pct_book = K.book_exposures(book, values["symbol"])
    exposures = {"book_total": total, "name_pct": name_pct,
                 "thesis_pct_book": thesis_pct_book,
                 "book_as_of": book.get("as_of_utc", "unknown"),
                 "prov": "script:sizing-eval(book=%s)" % args.book}

    if args.mode == "add":
        result = K.size_binding(doctrine, values, None, today=args.today,
                                exposures=exposures)
    else:
        result = K.hold_state_panel(doctrine, values, book, today=args.today)

    payload = {
        "schema_version": 2,
        "mode": args.mode,
        "doctrine_version": K.doctrine_version(doctrine, bands),
        "doctrine_fingerprint": K.doctrine_fingerprint_pair(doctrine, bands),
        "doctrine_override_tranche_pct": float(
            doctrine["override_lane"]["tranche_pct_of_computed_size"]),
        "inputs": {k: {"value": values[k], "prov": provs[k]} for k in values
                   if k not in DERIVED_PROV_KEYS},
        "exposures": exposures,
        "computed": result,
    }
    worksheet = render_worksheet(args.mode, payload, result)
    if args.worksheet_out:
        Path(args.worksheet_out).write_text(worksheet + "\n", encoding="utf-8")
    out = {"ok": True, "verdict": result.get("verdict"), "result": result,
           "worksheet": worksheet}
    print(json.dumps(K._norm(out), indent=2) if args.json else worksheet)
    return 0


def extract_block(text):
    m = re.search(r"```kernel:sizing\n(.*?)\n```", text, re.DOTALL)
    if not m:
        raise K.KernelError("no ```kernel:sizing``` block found")
    return yaml.safe_load(m.group(1)), m.end()


def _diff_computed(expected, actual, prefix=""):
    """Compare recomputed result vs the block's recorded computed dict."""
    findings = []
    if isinstance(expected, dict):
        for k, v in expected.items():
            if k == "notes":
                continue
            if not isinstance(actual, dict) or k not in actual:
                findings.append("computed.%s%s missing from worksheet block" % (prefix, k))
                continue
            findings += _diff_computed(v, actual[k], "%s%s." % (prefix, k))
        return findings
    if isinstance(expected, list):
        if list(expected) != list(actual):
            findings.append("computed.%s: recomputed %r != recorded %r"
                            % (prefix.rstrip("."), expected, actual))
        return findings
    if isinstance(expected, bool) or not isinstance(expected, (int, float)):
        if str(expected) != str(actual):
            findings.append("computed.%s: recomputed %r != recorded %r"
                            % (prefix.rstrip("."), expected, actual))
        return findings
    try:
        if abs(float(expected) - float(actual)) > 1e-6:
            findings.append("computed.%s: recomputed %s != recorded %s"
                            % (prefix.rstrip("."), expected, actual))
    except (TypeError, ValueError):
        findings.append("computed.%s: type mismatch (%r vs %r)"
                        % (prefix.rstrip("."), expected, actual))
    return findings


def do_check(args):
    run_lint()
    doctrine, _, _ = K.load_block("doctrine")
    bands, _, _ = K.load_block("bands")
    text = Path(args.check).read_text(encoding="utf-8")
    payload, block_end = extract_block(text)
    findings = []

    # Doctrine currency: a worksheet computed under a superseded doctrine
    # must be recomputed, not trusted.
    live_fp = K.doctrine_fingerprint_pair(doctrine, bands)
    if payload.get("doctrine_fingerprint") != live_fp:
        findings.append("worksheet doctrine_fingerprint %s != live %s (recompute required)"
                        % (payload.get("doctrine_fingerprint"), live_fp))

    mode = payload.get("mode")
    raw_inputs = payload.get("inputs") or {}
    values = {k: v.get("value") for k, v in raw_inputs.items()}
    provs = {k: str(v.get("prov", "")) for k, v in raw_inputs.items()}
    for k, v in raw_inputs.items():
        if not str(v.get("prov", "")).strip():
            findings.append("input '%s' carries no prov" % k)
    values = attach_derived_provs(values, provs)
    exposures = payload.get("exposures")
    recorded = payload.get("computed") or {}
    today = args.today or str(payload.get("generated_date") or "") or None

    try:
        if mode == "add":
            recomputed = K.size_binding(doctrine, values, None, today=today,
                                        exposures=exposures)
        elif mode == "hold-state":
            # Rebuild a minimal book from the recorded exposures for the panel.
            recomputed = K.hold_state_panel(
                doctrine, values,
                {"total_value": exposures["book_total"],
                 "positions": [{"symbol": values["symbol"],
                                "value": exposures["book_total"] * exposures["name_pct"] / 100.0,
                                "thesis": ""},
                               {"symbol": "_REST_",
                                "value": exposures["book_total"] * (1 - exposures["name_pct"] / 100.0),
                                "thesis": ""}],
                 "as_of_utc": exposures.get("book_as_of")},
                today=today)
            # thesis panel recheck from recorded strict pcts:
            for t, d in (recorded.get("theses") or {}).items():
                line = K.thesis_line_pct(doctrine, t, today)
                if abs(line - float(d.get("line_pct", -1))) > 1e-9:
                    findings.append("thesis %s line_pct recorded %s != doctrine %s"
                                    % (t, d.get("line_pct"), line))
            recomputed = {k: v for k, v in recomputed.items() if k not in ("theses",)}
            recorded = {k: v for k, v in recorded.items() if k not in ("theses",)}
        else:
            raise K.KernelError("unknown worksheet mode: %r" % mode)
    except K.KernelError as e:
        return fail("recompute failed: %s" % e, args.json)

    findings += _diff_computed(K._norm(recomputed), K._norm(recorded))

    # Rendered-lines spot check: the transcribed FINAL numbers must appear.
    tail = text[block_end:block_end + 4000]
    if mode == "add" and recomputed.get("verdict") == "SIZE-OK":
        for token in (_fmt_usd(recomputed["final_dollars"]),
                      "%.6f" % recomputed["final_shares"]):
            if token not in tail:
                findings.append("rendered lines missing FINAL token '%s'" % token)

    # Full-analysis obligations (frontmatter + Action-line equality).
    fm = None
    if text.startswith("---"):
        try:
            fm, _ = K.read_frontmatter_and_body(args.check)
        except K.KernelError:
            fm = None
    if fm and fm.get("type") == "analysis":
        for field in ANALYSIS_MANDATORY_FM:
            if field not in fm:
                findings.append("analysis frontmatter missing kernel field '%s'" % field)
        if str(fm.get("doctrine_fingerprint", "")) != live_fp:
            findings.append("frontmatter doctrine_fingerprint != live doctrine")
        if mode == "add" and recomputed.get("verdict") == "SIZE-OK":
            m = re.search(r"\*\*Action\*\*:[^\n$]*\$\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)", text)
            if not m:
                findings.append("TRADING DECISION Action line with a $ amount not found")
            else:
                action_usd = float(m.group(1).replace(",", ""))
                tol = float(doctrine["sizing"]["reconciliation"]["worksheet_dollars_abs"])
                if abs(action_usd - float(recomputed["final_dollars"])) > tol:
                    findings.append("Action $%.2f != worksheet final $%.2f (tol %.2f)"
                                    % (action_usd, recomputed["final_dollars"], tol))
            if bool(fm.get("deployment_override")) != bool(recomputed.get("override_used")):
                findings.append("frontmatter deployment_override != worksheet override_used")

    if args.json:
        print(json.dumps({"ok": not findings, "findings": findings,
                          "verdict": recomputed.get("verdict")}, indent=2))
    else:
        if findings:
            print("SIZING-CHECK: %d finding(s)" % len(findings))
            for f in findings:
                print("  " + f)
        else:
            print("SIZING-CHECK: clean (%s, verdict %s)" % (mode, recomputed.get("verdict")))
    return 2 if findings else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Osanwe sizing-eval (INVEST KERNEL)")
    ap.add_argument("--compute", action="store_true")
    ap.add_argument("--check", help="analysis or worksheet file to re-derive")
    ap.add_argument("--mode", choices=["add", "hold-state"], default="add")
    ap.add_argument("--inputs", help="path to {value, prov} inputs JSON, or - for stdin")
    ap.add_argument("--book", help="path to TRUSTED book snapshot (pretrade_gate format)")
    ap.add_argument("--today", help="override today YYYY-MM-DD (tests)")
    ap.add_argument("--worksheet-out", help="also write the worksheet markdown here")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        if args.compute:
            if not args.inputs or not args.book:
                return fail("--compute requires --inputs and --book", args.json)
            return do_compute(args)
        if args.check:
            return do_check(args)
        return fail("one of --compute / --check required", args.json)
    except K.KernelError as e:
        return fail(str(e), args.json)
    except Exception as e:  # fail-closed on anything unexpected
        return fail("unexpected error (fail-closed): %s: %s" % (type(e).__name__, e),
                    args.json)


if __name__ == "__main__":
    sys.exit(main())
