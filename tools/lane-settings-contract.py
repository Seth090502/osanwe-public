#!/usr/bin/env python3
"""
Lane settings contract verifier -- offline verification; --accept probes loopback.

WHY THIS EXISTS
---------------
The three lanes are configured entirely through env keys in --settings overlays.
Claude Code auto-updates (autoUpdatesChannel: latest), and an update can:

  1. rename or remove an env key, so the overlay still parses, still loads, and
     silently stops doing anything -- the lane reverts to defaults with NO error
     printed anywhere;
  2. change a measured invariant (the max_tokens hard cap, or the fixed reserve
     buffer subtracted from the declared window) so the firing point drifts away
     from the percentage the operator chose;
  3. reject an overlay outright -- Claude Code SILENTLY IGNORES a settings file
     that is not strict JSON, restoring user-scope beliefs with no diagnostic.

All three failures are quiet. This check makes them loud, and it is the reason a
binary update does not require re-deriving the lane policy by hand.

WHAT IT DOES NOT DO
-------------------
The default check contacts no provider and starts no daemon. --accept runs an
isolated synthetic loopback provider with a non-secret synthetic key. Key names
in the binary and the historical formulas below do not prove current semantics.
Acceptance requires fresh behavioral controls and a matching SHA256 receipt.
Native subscription and resume evidence remain separate.

Exit 0 = scoped static/mechanics checks hold. Exit 1 = failed/stale. Exit 2 = unavailable.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAUDE_EXE = os.path.expandvars(r"%USERPROFILE%\.local\bin\claude.exe")
PIN_PATH = os.path.join(ROOT, "config", "lane-settings-contract.pin")

# ---------------------------------------------------------------------------
# Historical nominal invariants. Current acceptance requires fresh observations.
# ---------------------------------------------------------------------------
# Claude Code clamps the outbound max_tokens. Measured against 2.1.258 by probe:
#   requested 100000 -> 100000 | 150000 -> 128000 | 262144 -> 128000
OUTPUT_HARD_CAP = 128000

# Claude Code subtracts a fixed, non-configurable reserve from the DECLARED
# window to get the actual compaction trigger. Corroborated across 50 recorded
# auto-compactions clustered at 716,845-721,395 against a 750,000 window.
COMPACT_RESERVE = 33000

# Lane 1 runs a first-party model whose native window is not declared in any
# file; it is the ceiling the overlay must stay under.
LANE1_NATIVE = 1000000

# ---------------------------------------------------------------------------
# THE CONTRACT. overlay -> what the lane promises.
# ---------------------------------------------------------------------------
LANES = [
    {
        "name": "1 subscription",
        "overlay": "config/mode-sub.settings.json",
        "native": LANE1_NATIVE,
        "want_pct": 75.0,
        # Deliberately omits CLAUDE_CODE_MAX_CONTEXT_TOKENS: documented no-op for
        # any id resolving to a Claude model unless DISABLE_COMPACT=1, which would
        # disable compaction entirely. Declaring it would be dead config.
        "forbid": ["CLAUDE_CODE_MAX_CONTEXT_TOKENS"],
    },
    {
        "name": "2 muse/go ",
        "overlay": "config/mode-muse.settings.json",
        "native": None,          # taken from the overlay's own ctx declaration
        "want_pct": 75.0,
        "forbid": [],
    },
    {
        "name": "3 local",
        "overlay": "config/mode-local.settings.json",
        "native": None,
        "want_pct": 60.0,
        "forbid": [],
    },
]

# Every env key any lane relies on. If a build stops shipping one of these
# names, the lane that sets it goes quietly back to defaults.
REQUIRED_KEYS = [
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW",
    "CLAUDE_CODE_MAX_CONTEXT_TOKENS",
    "CLAUDE_CODE_MAX_OUTPUT_TOKENS",
    "CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY",
    "CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS",
    "CLAUDE_CODE_ATTRIBUTION_HEADER",
    "CLAUDE_CODE_DISABLE_AUTO_MEMORY",
    "BASH_MAX_OUTPUT_LENGTH",
    "MAX_MCP_OUTPUT_TOKENS",
]

# Keys that must NOT be set by any lane, because each one would defeat the
# zero-fallback rule or silently re-route a lane to a different model.
FORBIDDEN_ANYWHERE = [
    "FALLBACK_FOR_ALL_PRIMARY_MODELS",
    "CLAUDE_CODE_SUBAGENT_MODEL",
    "CLAUDE_CODE_SUBAGENT_MODEL_FORCE",
    "ANTHROPIC_MODEL",
    "CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT",
    "DISABLE_COMPACT",
    "DISABLE_AUTO_COMPACT",
]


def binary_identity(path):
    """Content identity; size/mtime do not establish installed binary identity."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan_binary(path, needles):
    """Single chunked pass; returns the set of needles found. Overlap avoids
    missing a name that straddles a chunk boundary."""
    found = set()
    encoded = {n: n.encode("ascii") for n in needles}
    overlap = max(len(v) for v in encoded.values()) + 1
    tail = b""
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(8 << 20)
            if not chunk:
                break
            buf = tail + chunk
            for name, enc in encoded.items():
                if name not in found and enc in buf:
                    found.add(name)
            if len(found) == len(encoded):
                break
            tail = buf[-overlap:]
    return found


def load_overlay(rel):
    """Strict-JSON load. Claude Code silently ignores an invalid settings file,
    so a parse error here is a lane-down condition, not a style nit."""
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        return None, "overlay missing: %s" % rel
    try:
        with open(path, encoding="utf-8") as fh:
            return (json.load(fh).get("env") or {}), None
    except ValueError as exc:
        return None, ("%s is not strict JSON (%s) -- Claude Code would ignore it "
                      "SILENTLY and the lane would inherit user scope" % (rel, exc))


def check_lanes(problems):
    rows = []
    for lane in LANES:
        env, err = load_overlay(lane["overlay"])
        if err:
            problems.append(err)
            continue

        for key in lane["forbid"]:
            if key in env:
                problems.append("%s: declares %s, which this lane deliberately omits"
                                % (lane["name"], key))

        window = int(env.get("CLAUDE_CODE_AUTO_COMPACT_WINDOW", 0))
        output = int(env.get("CLAUDE_CODE_MAX_OUTPUT_TOKENS", 0))
        native = lane["native"] or int(env.get("CLAUDE_CODE_MAX_CONTEXT_TOKENS", 0))

        if not window:
            problems.append("%s: no CLAUDE_CODE_AUTO_COMPACT_WINDOW -- compaction "
                            "would follow user scope, not this lane" % lane["name"])
            continue
        if not native:
            problems.append("%s: no context window declared or known" % lane["name"])
            continue
        if not output:
            problems.append("%s: no CLAUDE_CODE_MAX_OUTPUT_TOKENS -- unrecognized "
                            "model ids silently default to 32000" % lane["name"])
            continue

        if output > OUTPUT_HARD_CAP:
            problems.append("%s: MAX_OUTPUT_TOKENS %d exceeds the measured client "
                            "hard cap %d and would be silently clamped"
                            % (lane["name"], output, OUTPUT_HARD_CAP))
        if not 0 < window <= native:
            problems.append("%s: AUTO_COMPACT_WINDOW %d is not inside the %d window"
                            % (lane["name"], window, native))
            continue

        fires_at = window - COMPACT_RESERVE
        if fires_at <= 0:
            problems.append("%s: window %d is below the %d reserve; compaction would "
                            "never fire sanely" % (lane["name"], window, COMPACT_RESERVE))
            continue
        if fires_at <= output:
            problems.append("%s: fires at %d but a single output may reach %d -- a "
                            "full-length answer cannot fit before compaction"
                            % (lane["name"], fires_at, output))

        pct = 100.0 * fires_at / native
        if abs(pct - lane["want_pct"]) > 0.5:
            problems.append("%s: fires at %.1f%% of the window, but this lane is "
                            "specified at %.1f%% (window %d, reserve %d)"
                            % (lane["name"], pct, lane["want_pct"], window, COMPACT_RESERVE))
        rows.append((lane["name"], native, window, fires_at, pct, output))
    return rows


def check_forbidden(problems):
    """No lane may set a key that re-routes the model or enables a fallback."""
    for lane in LANES:
        env, err = load_overlay(lane["overlay"])
        if err or env is None:
            continue
        for key in FORBIDDEN_ANYWHERE:
            if key in env:
                problems.append("%s: sets %s -- this defeats the zero-fallback rule "
                                "or re-routes the lane" % (lane["name"], key))


def verify_probe_receipt(receipt, exe, probe_path):
    problems = []
    if receipt.get("schema") != "osanwe.lane-behavior/1" or receipt.get("scope") != "fake-provider-client-mechanics":
        problems.append("behavioral receipt schema/scope invalid")
    if receipt.get("binary_sha256") != binary_identity(exe):
        problems.append("behavioral receipt belongs to different installed bytes")
    if receipt.get("probe_code_sha256") != binary_identity(probe_path):
        problems.append("behavioral probe code changed after observation")
    expected = {"output_cap", "request_identity", "compaction_bracket", "binary_unchanged"}
    controls = receipt.get("controls", {})
    if receipt.get("state") != "passed" or set(controls) != expected or any(
            not isinstance(controls.get(key), dict) or controls[key].get("state") != "passed" for key in expected):
        problems.append("required behavioral controls did not all pass")
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify static lane configuration and hash-bound observed client mechanics.")
    parser.add_argument("--accept", action="store_true", help="run fresh isolated behavioral probes before any pin change")
    parser.add_argument("--exe", default=CLAUDE_EXE)
    parser.add_argument("--pin", default=PIN_PATH)
    parser.add_argument("--evidence-dir", default=os.path.join(ROOT, ".agents", "state", "lane-probes"))
    args = parser.parse_args(argv)
    exe, pin_path = args.exe, args.pin
    problems = []

    if not os.path.isfile(exe):
        print("[lane-contract] UNAVAILABLE: configured claude.exe does not exist")
        return 2

    ident = binary_identity(exe)
    pinned = None
    if os.path.isfile(pin_path):
        try:
            with open(pin_path, encoding="utf-8") as fh:
                pinned = json.load(fh)
        except (ValueError, OSError):
            pinned = None

    missing = sorted(set(REQUIRED_KEYS) - scan_binary(exe, REQUIRED_KEYS))
    for key in missing:
        problems.append("BUILD DROPPED KEY: %s was not found; behavior is unverified." % key)

    try:
        rows = check_lanes(problems)
    except (TypeError, ValueError) as exc:
        problems.append("overlay has malformed numeric settings: " + type(exc).__name__)
        rows = []
    check_forbidden(problems)

    print("[lane-contract] binary SHA256 %s" % ident)
    print("  Nominal lane formulas below use the historical reserve; they are not current behavioral evidence.")
    if rows:
        for name, native, window, fires, pct, out in rows:
            print("  %-16s native=%-9s window=%-8s fires=%-8s %5.1f%%  out=%s"
                  % (name, "{:,}".format(native), "{:,}".format(window),
                     "{:,}".format(fires), pct, "{:,}".format(out)))

    if problems:
        print("\n[lane-contract] CONTRACT BROKEN")
        for p in problems:
            print("  - %s" % p)
        return 1

    probe_path = Path(ROOT) / "tools/lane-behavior-probe.py"
    if args.accept:
        spec = importlib.util.spec_from_file_location("lane_behavior", probe_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        receipt = module.probe(exe)
        evidence_dir = Path(args.evidence_dir)
        evidence_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        path = evidence_dir / ("behavior-" + stamp + ".json")
        with path.open("x", encoding="utf-8") as handle:
            json.dump(receipt, handle, indent=2)
        failures = verify_probe_receipt(receipt, exe, probe_path)
        if failures:
            print("[lane-contract] FAILED: fresh behavioral controls did not establish the contract; previous pin preserved")
            for failure in failures:
                print("  - " + failure)
            print("  evidence: " + str(path))
            return 1
        pin = {"schema": "osanwe.lane-pin/2", "binary_sha256": ident,
               "evidence": str(path.resolve()), "evidence_sha256": binary_identity(path),
               "accepted_at": receipt["verified_at"], "scope": receipt["scope"]}
        target = Path(pin_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".tmp")
        with temporary.open("x", encoding="utf-8") as handle:
            json.dump(pin, handle, indent=2)
        os.replace(temporary, target)
        pinned = pin
    if not isinstance(pinned, dict) or pinned.get("schema") != "osanwe.lane-pin/2" or pinned.get("binary_sha256") != ident:
        print("[lane-contract] STALE: installed binary lacks a matching behavioral pin; static key presence is insufficient")
        print("  run --accept to measure, preserve the receipt, and pin only if all required controls pass")
        return 1
    try:
        evidence = Path(pinned["evidence"])
        receipt = json.loads(evidence.read_text(encoding="utf-8"))
        failures = verify_probe_receipt(receipt, exe, probe_path)
        if binary_identity(evidence) != pinned["evidence_sha256"]:
            failures.append("behavioral evidence edited after acceptance")
    except (KeyError, OSError, ValueError):
        failures = ["behavioral evidence unavailable or malformed"]
    if failures:
        print("[lane-contract] FAILED: " + "; ".join(failures))
        return 1
    print("[lane-contract] OK -- static overlays and hash-bound fake-provider mechanics verified; native subscription/resume NOT VERIFIED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
