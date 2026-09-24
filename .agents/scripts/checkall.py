#!/usr/bin/env python3
"""One consistency command for the cross-harness surface.

Default: deterministic offline checks, including the root contract and its stub,
skill/config drift, lane configuration, vault structure and generated organs.
--quick: validate, skill sync/drift, fixture pins, router contracts, admitted
financial documents and read-only retrieval-generation freshness.
Neither profile runs live MCP probes or hook-manifest commands. Those potentially
stateful diagnostics require explicit --live and --hooks respectively.
Failures always report WHAT BROKE / WHAT IT MEANS / WHAT TO DO / WHAT TO PASTE BACK.
"""
import argparse
import glob
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FIXTURES = os.path.join(ROOT, ".agents", "migration", "fixtures")
PY = sys.executable
# On Windows, bare "bash" from a Python subprocess can resolve to the WSL launcher
# (System32\bash.exe -> HCS_E_HYPERV_NOT_INSTALLED on machines without WSL). Pin
# Git Bash explicitly; fall back to PATH resolution elsewhere.
_GIT_BASH = r"/path/to/program-files\Git\bin\bash.exe"
BASH = _GIT_BASH if os.path.isfile(_GIT_BASH) else (shutil.which("bash") or "bash")

BLOCKS = []


def block(what, means, todo, paste):
    BLOCKS.append({"WHAT BROKE": what, "WHAT IT MEANS": means,
                   "WHAT TO DO": todo, "WHAT TO PASTE BACK": paste})


def run(cmd, cwd=ROOT, timeout=300):
    r = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=cwd, creationflags=NO_WINDOW, timeout=timeout
    )
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def step_validate():
    rc, out = run([PY, os.path.join(HERE, "validate.py")])
    if rc != 0:
        block("validate.py failed",
              "a canon skill or generated config violates the spec/policy rules "
              "(details in the output below)",
              "read the [FAIL/...] lines; fix the named file; re-run "
              "python .agents/scripts/checkall.py",
              out.strip()[-1500:])
    return rc == 0, out


def step_sync_check():
    rc, out = run([PY, os.path.join(HERE, "sync.py"), "--check"])
    if rc != 0:
        block("sync --check found differences",
              "the Claude-side derived skill copies no longer match what the canon "
              "tree would generate (someone edited a derived file, or canon changed "
              "without re-running sync)",
              "run: python .agents/scripts/sync.py   then commit both trees together",
              out.strip()[-1200:])
    return rc == 0, out


def step_driftcheck():
    rc, out = run([PY, os.path.join(HERE, "driftcheck.py")])
    if rc != 0:
        block("driftcheck found manifest drift",
              "canon and derived skill trees disagree in one of the six tracked ways "
              "(each line names the case)",
              "for case-1/2/3/5: run python .agents/scripts/sync.py and commit; "
              "for case-4: run sync (it removes the orphan); for case-6: never "
              "hand-edit derived files -- restore via sync",
              out.strip()[-1200:])
    return rc == 0, out


def step_skills_ref(quick=False):
    sys.path.insert(0, HERE)
    from sync import migrated_canon_skills, CANON  # noqa: E402
    migrated = migrated_canon_skills()
    if quick or not migrated:
        return True, "skills-ref: skipped (%s)" % ("--quick" if quick else "0 migrated skills")
    exe = shutil.which("agentskills") or shutil.which("skills-ref")
    if exe is None:
        block("skills-ref validator not installed",
              "the PyPI reference validator (Anthropic skills-ref; CLI name "
              "'agentskills') is part of DoD 1 and migrated skills exist",
              "pip install skills-ref   then re-run checkall",
              "output of: pip install skills-ref")
        return False, "skills-ref missing with %d migrated skill(s)" % len(migrated)
    bad = []
    for name in migrated:
        rc, out = run([exe, "validate", os.path.join(CANON, name)])
        if rc != 0:
            bad.append((name, out.strip()[-300:]))
    if bad:
        block("skills-ref validate failed for: %s" % ", ".join(n for n, _ in bad),
              "the reference validator rejects these canon skills' structure/frontmatter",
              "fix each named skill; re-run checkall",
              "\n".join("%s: %s" % b for b in bad)[:1500])
        return False, "skills-ref: %d failure(s)" % len(bad)
    return True, "skills-ref: %d migrated skill(s) valid" % len(migrated)


def step_fixture_pins():
    pin_file = os.path.join(FIXTURES, "FIXTURES.sha256")
    if not os.path.isfile(pin_file):
        return True, "UNVERIFIED: fixture pins: no FIXTURES.sha256 (nothing to enforce)"
    freeze_note = ""
    fn_path = os.path.join(FIXTURES, "FREEZE-NOTE.md")
    if os.path.isfile(fn_path):
        with io.open(fn_path, encoding="utf-8") as f:
            freeze_note = f.read()
    mismatches, justified = [], []
    with io.open(pin_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            want_hash, fname = line.split(None, 1)
            fname = fname.lstrip("*").strip()
            p = os.path.join(FIXTURES, fname)
            if not os.path.isfile(p):
                mismatches.append("%s: MISSING" % fname)
                continue
            with open(p, "rb") as fh:
                got = hashlib.sha256(fh.read()).hexdigest()
            if got != want_hash:
                # Redteam H1: a bare filename mention in FREEZE-NOTE is NOT a
                # justification -- it would fail-open forever for any file ever
                # named. A mismatch is justified ONLY when the note carries the
                # exact "<filename> <new-sha256>" pair for THIS content.
                if ("%s %s" % (fname, got)) in freeze_note:
                    justified.append(fname)
                else:
                    mismatches.append("%s: hash changed; FREEZE-NOTE.md lacks the "
                                      "'%s %s' justification pair (H1: bare filename "
                                      "mentions never justify)" % (fname, fname, got))
    if mismatches:
        block("frozen fixture pin mismatch",
              "the conformance/routing fixtures were frozen at S1 so post-migration "
              "runs compare like-for-like; an unjustified edit invalidates every "
              "comparison made against them",
              "either restore the fixture from git, or (if the edit is deliberate) "
              "add a dated justification naming the file to "
              ".agents/migration/fixtures/FREEZE-NOTE.md, then re-pin FIXTURES.sha256",
              "\n".join(mismatches))
        return False, "fixture pins: %d mismatch(es)" % len(mismatches)
    note = " (%d justified edit(s): %s)" % (len(justified), justified) if justified else ""
    return True, "fixture pins: all pinned fixtures verified%s" % note


def step_local_lane():
    """Local delegation lane config consistency -- OFFLINE ONLY.

    Deliberately never contacts the Ollama daemon: coupling the one consistency command
    to a live GPU would turn checkall red whenever the daemon sleeps, inverting the
    lane's own "lane absence is NEVER a HALT" rule. Liveness is `delegate.py --check`.
    """
    cfg_path = os.path.join(ROOT, "config", "local-lane.json")
    if not os.path.isfile(cfg_path):
        return True, "UNVERIFIED: local-lane: no lane config (lane not installed)"
    try:
        with open(cfg_path, encoding="utf-8") as f:
            cfg = json.load(f)
    except ValueError as e:
        return False, "local-lane: config is not valid JSON: %s" % e
    problems = []
    for key in ("model", "host", "legs"):
        if not cfg.get(key):
            problems.append("missing required key '%s'" % key)
    tool = os.path.join(ROOT, "tools", "delegate.py")
    if not os.path.isfile(tool):
        problems.append("config exists but tools/delegate.py does not")
    for skill, legs in (cfg.get("legs") or {}).items():
        d = {x["id"] for x in legs.get("delegable", [])}
        n = set(legs.get("never_local", []))
        both = d & n
        if both:
            problems.append("%s: leg id(s) in BOTH delegable and never_local: %s"
                            % (skill, ", ".join(sorted(both))))
    # ctx coherence (2026-08-13, staged via apply-sota-config): the launcher and
    # lane-arm pin OLLAMA_CONTEXT_LENGTH from cfg["ctx"] at daemon start, and the
    # mode-3 overlay declares the same window to claude.exe. A model swap does not
    # re-derive the pin (delegate.py --use only WARNS), so this offline cross-lint
    # is the mechanical guard against a stale pin silently truncating the window.
    overlay_path = os.path.join(ROOT, "config", "mode-local.settings.json")
    if cfg.get("ctx") and os.path.isfile(overlay_path):
        try:
            with open(overlay_path, encoding="utf-8") as f:
                oenv = (json.load(f).get("env") or {})
            o_ctx = int(oenv.get("CLAUDE_CODE_MAX_CONTEXT_TOKENS", 0))
            o_cw = int(oenv.get("CLAUDE_CODE_AUTO_COMPACT_WINDOW", 0))
            # FAIL CLOSED (2026-09-02). Both guards used to be gated on `if o_ctx` / `if
            # o_cw`, so an ABSENT OR MISSPELLED key read back as 0, which is falsy, which
            # skipped the check entirely and reported GREEN -- while mode 3 silently
            # inherited the user-scope 1,000,000-token belief against a 262k daemon. That
            # is the exact failure this lint exists to catch, so absence is now the
            # LOUDEST outcome rather than the quietest.
            if not o_ctx:
                problems.append("mode-local overlay declares no CLAUDE_CODE_MAX_CONTEXT_TOKENS "
                                "(mode 3 would inherit the user-scope 1M window)")
            elif o_ctx != int(cfg["ctx"]):
                problems.append("ctx pin %s != mode-local MAX_CONTEXT_TOKENS %s "
                                "(re-derive after the model swap)" % (cfg["ctx"], o_ctx))
            if not o_cw:
                problems.append("mode-local overlay declares no CLAUDE_CODE_AUTO_COMPACT_WINDOW "
                                "(compaction would follow the user-scope 750k setting)")
            elif o_ctx and not (0 < o_cw < o_ctx):
                problems.append("mode-local AUTO_COMPACT_WINDOW %s not inside the %s window"
                                % (o_cw, o_ctx))
        except (ValueError, OSError) as e:
            problems.append("mode-local.settings.json unreadable/invalid: %s "
                            "(mode 3 silently ignores a failing settings file)" % e)
    # A model name anywhere else is drift: the config is the single source of truth.
    if problems:
        return False, "local-lane: " + "; ".join(problems)
    return True, "local-lane: config coherent (model=%s, %d skill map(s))" % (
        cfg.get("model"), len(cfg.get("legs") or {}))


def step_relay():
    """Relay-worker lane lints -- OFFLINE ONLY (BACKLOG 2026-08-16 integration
    batch; GATE-B gate-b-relay-worker-2026-08-16 / gate-b-ask-frontier-2026-08-16).
    (a) relay-cases fixture pins: FIXTURES.sha256 covers cases.json AND fixtures/,
        so a quiet case edit cannot manufacture a suite win;
        (b) blocked-domains agreement: the REAL relay_exec parser run against the
        canonical source-policy organ must clear its fail-closed >=15 floor (a silent fail-closed
        strands every fetch_url leg -- make it loud here instead);
    (c) threshold arithmetic anchored to W_eff (the livelock/overrun invariant,
        Fable-review fix 1)."""
    relay_tool = os.path.join(ROOT, "tools", "relay.py")
    if not os.path.isfile(relay_tool):
        return True, "relay: not installed"
    problems = []
    domains = None
    # (a) pins
    cases_dir = os.path.join(ROOT, "tools", "relay-cases")
    pin_file = os.path.join(cases_dir, "FIXTURES.sha256")
    if os.path.isfile(pin_file):
        with io.open(pin_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                want, rel = line.split(None, 1)
                rel = rel.strip()
                p = os.path.join(cases_dir, rel)
                if not os.path.isfile(p):
                    problems.append("relay pin: %s MISSING" % rel)
                    continue
                with open(p, "rb") as fh:
                    got = hashlib.sha256(fh.read()).hexdigest()
                if got != want:
                    problems.append("relay pin mismatch: %s (a deliberate edit "
                                    "needs python tools/test-relay.py --repin)" % rel)
    else:
        problems.append("tools/relay-cases/FIXTURES.sha256 missing")
    # (b) blocked-domains agreement
    lib = os.path.join(ROOT, "tools", "lib")
    if lib not in sys.path:
        sys.path.insert(0, lib)
    try:
        import relay_exec
        domains = relay_exec.load_blocked_domains()
        if domains is None:
            problems.append("canonical source-policy blocked-domain parse fails its >=15 floor "
                            "(fetch_url would run fail-closed DISABLED)")
        elif "bloomberg.com" not in domains:
            problems.append("blocked-domain parse lost a canonical entry "
                            "(bloomberg.com) -- parser vs source-policy drift")
    except Exception as exc:                                   # noqa: BLE001
        problems.append("relay_exec import failed: %r" % exc)
    # (c) threshold arithmetic anchored to W_eff + (d) roles-block coherence
    cfg_path = os.path.join(ROOT, "config", "local-lane.json")
    try:
        with open(cfg_path, encoding="utf-8") as f:
            rcfg = (json.load(f).get("relay") or {})
        for rkey, rspec in (rcfg.get("roles") or {}).items():
            if rkey.startswith("_"):
                continue
            rf = rspec.get("role_file") or ""
            if not os.path.isfile(os.path.join(ROOT, rf)):
                problems.append("role %r: role_file missing: %s" % (rkey, rf))
            try:
                import relay_exec as _rx
                bad_tools = [t for t in (rspec.get("tools") or [])
                             if t not in _rx.Executor.TABLE]
                if not rspec.get("tools") or bad_tools:
                    problems.append("role %r: tools empty or unknown: %s"
                                    % (rkey, bad_tools))
            except Exception as exc:                           # noqa: BLE001
                problems.append("role lint import failed: %r" % exc)
        w = int(rcfg["w_eff_tokens"])
        thr = int(rcfg["relay_threshold_tokens"])
        res = int(rcfg["relay_reserve_tokens"])
        mr = int(rcfg["max_result_tokens"])
        if thr + res + mr > w:
            problems.append("relay invariant broken: threshold+reserve+max_result "
                            "= %d > w_eff %d" % (thr + res + mr, w))
        want_mr = min(32768, int(0.15 * w))
        if mr != want_mr:
            problems.append("max_result_tokens %d != min(32768, 0.15*w_eff) = %d"
                            % (mr, want_mr))
    except (KeyError, TypeError, ValueError, OSError) as exc:
        problems.append("relay block unreadable in config/local-lane.json: %r" % exc)
    if problems:
        block("relay lane lints failed",
              "the relay worker's pinned suite, its canonical source-policy domain "
              "blocklist, or its context-window arithmetic no longer hold -- "
              "each named problem points at the drifted piece",
              "for a pin mismatch: restore from git or run "
              "python tools/test-relay.py --repin after a DELIBERATE edit; for "
              "the blocklist: fix the blocked-domains block in docs/osanwe-runtime-reference.md or the "
              "parser; for arithmetic: fix config/local-lane.json relay block",
              "\n".join(problems)[:1500])
        return False, "relay: %d problem(s)" % len(problems)
    return True, ("relay: pins verified, blocked-domains parse healthy (%d), "
                  "threshold arithmetic holds" % (len(domains) if domains else 0))


def step_gen_configs():
    gen = os.path.join(HERE, "gen-mcp-configs.py")
    if not os.path.isfile(gen):
        return True, "gen-configs: generator not present"
    rc, out = run([PY, gen, "--check"])
    if rc != 0:
        block("generated MCP configs drifted",
              "someone hand-edited .mcp.json / opencode.json / .codex/config.toml, "
              "or the registry changed without regenerating them",
              "run: python .agents/scripts/gen-mcp-configs.py   and commit registry + "
              "configs together (or revert the hand-edit)",
              out.strip()[-800:])
    return rc == 0, out


def step_workflow_pins():
    """Enforce the current user-authorized session-inheritance policy.

    Production wrappers/workflows inherit session settings. Evaluation runners
    are outside these trees and keep their explicitly frozen configurations.
    Unknown named roles still fail; this check cannot prove native execution.
    """
    wf_dir = Path(ROOT) / ".claude/workflows"
    roles = Path(ROOT) / ".agents/roles"
    known = {p.stem for p in (Path(ROOT) / ".claude/agents").glob("*.md")}
    known |= {"Explore", "Plan", "general-purpose", "claude", "fork"}
    bad = []
    for path in roles.glob("*.md"):
        src = path.read_text(encoding="utf-8")
        if src.startswith("---\n"):
            frontmatter = src.split("---", 2)[1]
            if re.search(r"^(model|effort):", frontmatter, re.M):
                bad.append(str(path.relative_to(ROOT)) + ": production role pins session settings")
    for path in wf_dir.glob("*.js"):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("//"):
                continue
            if re.search(r"\b(?:model|effort)\s*:\s*['\"]", line):
                bad.append(f"{path.relative_to(ROOT)}:{number}: literal production model/effort")
            for role in re.findall(r"\bagentType\s*:\s*'([^']+)'", line):
                if role not in known:
                    bad.append(f"{path.relative_to(ROOT)}:{number}: unknown named role")
    if bad:
        block("production model inheritance or role binding drift",
              "a production workflow overrides authorized session settings or names an unavailable role",
              "remove obsolete literal defaults, retain explicit caller options, or repair the named role; never change frozen evaluation settings",
              "\n".join(bad[:20]))
    return not bad, "production workflow inheritance: " + ("; ".join(bad) if bad else "passed (static only)")


def step_hook_manifest():
    hooks_dir = os.path.join(ROOT, ".agents", "hooks")
    manifest = os.path.join(hooks_dir, "manifest.yaml")
    if not os.path.isfile(manifest):
        return True, "hook manifest: not present yet (pre-S4)"
    try:
        import yaml
        with io.open(manifest, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as exc:
        block("hook manifest unparseable", "manifest.yaml is not valid YAML",
              "fix the YAML syntax", repr(exc))
        return False, "hook manifest: unparseable"
    problems = []
    for entry in (data.get("hooks") or []):
        logic = entry.get("logic")
        if logic and not os.path.isfile(os.path.join(ROOT, logic)):
            problems.append("%s: logic path %s does not resolve" % (entry.get("id"), logic))
        test = entry.get("test")
        if test:
            rc, out = run([BASH, "-c", test])
            if rc != 0:
                problems.append("%s: test block FAILED: %s" % (entry.get("id"), out.strip()[-200:]))
    if problems:
        block("hook manifest checks failed",
              "a Tier-1 manifest entry points at a missing script or its executable "
              "test: block no longer passes",
              "fix the named entry or the underlying hook script",
              "\n".join(problems)[:1500])
        return False, "hook manifest: %d problem(s)" % len(problems)
    return True, "hook manifest: all logic paths resolve, all test blocks green"


def step_mcp_canary(quick=False):
    canary = os.path.join(ROOT, ".agents", "mcp", "canary.py")
    if quick or not os.path.isfile(canary):
        return True, "UNVERIFIED: mcp canary: %s" % ("skipped (--quick)" if quick else "not present yet (pre-S2.5)")
    rc, out = run([PY, canary])
    if rc != 0:
        block("MCP live-surface canary failed",
              "a live MCP server exposes a tool name the registry does not record -- "
              "the server surface GREW (or shrank) under a static config; this is the "
              "45->54 Robinhood failure mode made loud",
              "update .agents/mcp/servers.json to the true surface, re-run the "
              "generators, re-run checkall",
              out.strip()[-1200:])
    if rc == 0 and re.search(r"^\[(?:WARN|MANUAL|UNVERIFIED|UNAVAILABLE|SKIP)\]", out, re.M):
        return True, "UNVERIFIED: live MCP diagnostic did not verify all requested servers\n" + out
    return rc == 0, out


def step_precommit_tree():
    """OSANWE-V2 ADR-04: whole-tree structural cage over the tracked tree."""
    import subprocess
    from pathlib import Path as _P
    root_p = _P(ROOT)
    r = subprocess.run([sys.executable, str(root_p / "tools" / "precommit.py"), "--tree"],
                       cwd=str(ROOT), capture_output=True, text=True, timeout=240,
                       creationflags=NO_WINDOW)
    good = r.returncode == 0
    tail = r.stdout.strip().splitlines()
    summary = next((l for l in tail if l.startswith("[tree] missing_frontmatter")),
                   tail[-1] if tail else "no output")
    return good, summary + ("\n" + "\n".join(tail[-4:]) if not good else "")


def step_router_check():
    """Real, nonrecursive contract + standalone-bootstrap + skill-set check."""
    returncode, out = run([PY, os.path.join(ROOT, "tools", "router-check.py")])
    return returncode == 0, out



def step_vault_audit_gate():
    """Vault score floor 95 + GATE findings must be zero."""
    from pathlib import Path as _P
    r = subprocess.run([sys.executable, "tools/vault-audit.py", "--json"],
                       cwd=str(_P(ROOT)), capture_output=True, text=True, timeout=300,
                       creationflags=NO_WINDOW)
    try:
        d = json.loads(r.stdout or "{}")
        score = d.get("score")
        gate = d.get("tiers", {}).get("gate", {}).get("count", -1)
        broken = len(d.get("broken_wikilinks") or [])
        good = (r.returncode == 0 and isinstance(score, (int, float))
                and score >= 95 and gate == 0 and broken == 0)
        return good, f"rc={r.returncode} score={score} gate={gate} broken={broken}"
    except Exception as exc:
        return False, f"audit parse failed: {exc}"


def step_check_paths():
    """MSYS/interpreter path hygiene (SOTA pass): the defect class that killed
    the Stop-hook, smart-emit, and 25 Claude hook registrations."""
    from pathlib import Path as _P
    r = subprocess.run([sys.executable, "tools/check-paths.py"],
                       cwd=str(_P(ROOT)), capture_output=True, text=True, timeout=60,
                       creationflags=NO_WINDOW)
    out = ((r.stdout or "") + (r.stderr or "")).strip().splitlines()
    return r.returncode == 0, out[-1] if out else f"rc={r.returncode}"


def step_lane_contract():
    """Lane settings contract -- OFFLINE. Guards the three --settings overlays
    against a claude.exe update that renames or drops an env key, which would
    leave the overlay parsing fine while doing nothing. Goes red on a binary
    change until the contract is re-verified and re-pinned with --accept."""
    from pathlib import Path as _P
    contract = _P(ROOT) / "tools" / "lane-settings-contract.py"
    if not contract.is_file():
        return True, "UNVERIFIED: local Claude lane adapter is not installed; no lane contract claim"
    r = subprocess.run([sys.executable, "tools/lane-settings-contract.py"],
                       cwd=str(_P(ROOT)), capture_output=True, text=True, timeout=120,
                       creationflags=NO_WINDOW)
    out = ((r.stdout or "") + (r.stderr or "")).strip().splitlines()
    if any(line.startswith("[lane-contract] STALE:") for line in out):
        return True, "STALE: installed Claude binary lacks passing behavioral evidence"
    if any(line.startswith("[lane-contract] UNAVAILABLE:") for line in out):
        return True, "UNVERIFIED: configured Claude runtime is unavailable"
    if r.returncode != 0:
        return False, "lane-contract: " + "\n".join(out[-20:])
    if any(line.startswith("[lane-contract] SKIP:") for line in out):
        return True, "UNVERIFIED: " + out[-1]
    return True, out[-1] if out else "ok"


def step_gen_regression():
    """Generated-organ regression suite (views==nodes, hot checker-green,
    YAML idempotency, node counts)."""
    from pathlib import Path as _P
    r = subprocess.run([sys.executable, "tools/test-generators.py"],
                       cwd=str(_P(ROOT)), capture_output=True, text=True, timeout=300,
                       creationflags=NO_WINDOW)
    out = ((r.stdout or "") + (r.stderr or "")).strip().splitlines()
    return r.returncode == 0, out[-1] if out else f"rc={r.returncode}"


def step_recovery_tests():
    """Isolated negative controls for the repaired contract and financial gates."""
    names = ("tools/test-router-contract.py", "tools/test-precommit.py",
             "tools/test-relay-policy.py",
             "tools/test-eval-interface.py", "tools/fis/test_recovery_financial_invariants.py",
             "tools/fis/test_research_evidence.py", "tools/fis/test_recovery_security.py",
             "tools/fis/test_recovery_approval.py", "tools/test-ledger-preservation.py",
             "tools/test-vault-audit-scope.py")
    failures = []
    for name in names:
        path = os.path.join(ROOT, name)
        if not os.path.isfile(path):
            failures.append(name + ": required recovery suite missing")
            continue
        rc, out = run([PY, "-B", path])
        if rc != 0:
            failures.append(name + ": " + out.strip()[-1600:])
    return not failures, ("\n".join(failures) if failures else "%d recovery suites passed" % len(names))


def step_institutional_tests():
    """Independent numerical and causal controls; no scored run or live data."""
    names = ("tools/fis/test_institutional_risk.py", "tools/fis/test_institutional_portfolio.py",
             "tools/fis/test_institutional_analytics.py", "tools/fis/test_institutional_benchmark.py",
             "tools/fis/test_tournament_causality.py", "tools/pit/test_pit_time_axis.py",
             "tools/fis/test_firewall_sandbox.py", "tools/fis/test_architecture_fitness.py")
    failures = []
    for name in names:
        path = os.path.join(ROOT, name)
        if not os.path.isfile(path):
            failures.append(name + ": required institutional suite missing")
            continue
        rc, out = run([PY, "-B", path])
        if rc != 0:
            failures.append(name + ": " + out.strip()[-1600:])
    return not failures, ("\n".join(failures) if failures else "%d institutional suites passed" % len(names))


def step_finance_data_tests():
    """Financial interchange, portable review and bounded reviewer execution."""
    names = ("tools/fis/test_workbench.py", "tools/fis/test_cashflow.py",
             "tools/test-finance-data-package.py", "tools/fis/test_report_review.py",
             "tools/fis/test_source_review_evidence.py",
             "tools/fis/test_reviewer_execution.py", "tools/fis/test_capabilities.py",
             "tools/fis/test_corpus_examples.py", "tools/pit/test_financial_documents.py",
             "tools/test-financial-integration-controls.py", "tools/pit/test_macro_status.py",
             "tools/fis/test_native_review.py")
    failures = []
    unavailable = []
    for name in names:
        rc, out = run([PY, "-B", name])
        if rc != 0:
            failures.append(name + ": " + out.strip()[-1600:])
        elif re.search(r"\bskipped=[1-9]\d*", out):
            unavailable.append(name + ": required controls skipped")
    if not failures and unavailable:
        return True, "UNVERIFIED: " + "; ".join(unavailable)
    return not failures, ("\n".join(failures) if failures else "%d Finance/Data suites passed" % len(names))


def step_financial_document_admission():
    """Current source/scope validation, not a corpus quality certification."""
    rc, out = run([PY, "-B", "tools/pit/dataset_registry.py", "--documents-manifest"], timeout=60)
    try:
        result = json.loads(out)
        if rc or result.get("schema") != "osanwe.financial-document-manifest/1":
            return False, "document admission: invalid registry or manifest"
        documents, exclusions = result["documents"], result["exclusions"]
        if (not isinstance(documents, list) or not isinstance(exclusions, list)
                or any(not isinstance(row, dict) for row in documents + exclusions)):
            raise ValueError("invalid document observation shape")
        intentional = {"superseded", "retracted", "scope_not_approved"}
        invalid_current = [row for row in exclusions if row.get("reason") not in intentional]
        if invalid_current:
            return True, "STALE: document admission excludes %d changed/unsupported current versions" % len(invalid_current)
        if not documents:
            return True, "UNVERIFIED: no currently admitted financial method passages"
        return True, "document admission: %d current documents, %d exact approved spans; semantic review scope remains separate" % (
            len(documents), sum(len(row["chunks"]) for row in documents))
    except (ValueError, KeyError, TypeError):
        return False, "document admission: malformed result (input contents not echoed)"


def step_retrieval_integrity():
    """Read-only generation/source inspection; no reindex or model inference."""
    node = shutil.which("node")
    runner = Path.home() / ".vault-substrate/reindex-runner.mjs"
    if not node or not runner.is_file():
        return True, "UNVERIFIED: active retrieval owner unavailable on this host"
    rc, out = run([node, str(runner), "--inspect"], timeout=60)
    try:
        result = json.loads(out)
        if result.get("schema") != "osanwe.retrieval-health/1":
            return False, "retrieval integrity: unsupported observation schema"
        state = result.get("state")
        if state == "passed" and rc == 0 and result.get("generation_id") and result.get("needs_rebuild") is False:
            return True, "retrieval integrity: current immutable generation; result quality is assessed separately"
        if state == "stale" and rc == 2:
            return True, "STALE: retrieval generation requires recovery"
        if state == "unavailable" and rc == 3:
            return True, "UNVERIFIED: retrieval generation unavailable"
        return False, "retrieval integrity: inconsistent state or failed observation"
    except (ValueError, TypeError):
        return False, "retrieval integrity: malformed result (raw output not echoed)"


def step_retrieval_controls():
    node = shutil.which("node")
    if not node:
        return True, "UNVERIFIED: Node unavailable for retrieval controls"
    commands = ([node, "tools/test-retrieval-runtime.mjs"],
                [node, "tools/test-index-scope.mjs"],
                [PY, "-B", "tools/test-retrieval-adapters.py"])
    failed = []
    for command in commands:
        rc, out = run(command, timeout=120)
        if rc:
            failed.append(command[-1] + ": " + out.strip()[-1400:])
    return not failed, "\n".join(failed) if failed else "synthetic retrieval generation, privacy scope and transport controls passed; no answer-quality or live-index claim"


def step_evaluator_controls():
    """Local deterministic grader/accounting controls; never invoke inference."""
    node = shutil.which("node")
    if not node:
        return True, "UNVERIFIED: Node.js unavailable for evaluator deterministic controls"
    commands = ([PY, "-B", "-m", "unittest", "discover", "-s", "evaluation/tests", "-p", "test_*.py"],
                [node, "--test", "evaluation/tests/service.test.mjs", "evaluation/tests/cohort.test.mjs"])
    failures, unavailable = [], []
    for command in commands:
        rc, out = run(command, timeout=60)
        if rc != 0:
            failures.append(command[-1] + ": " + out.strip()[-1600:])
        elif re.search(r"\bskipped=[1-9]\d*|\bskipped [1-9]\d*", out):
            unavailable.append(command[-1] + ": required controls skipped")
    if failures:
        return False, "\n".join(failures)
    if unavailable:
        return True, "UNVERIFIED: " + "; ".join(unavailable)
    return True, "Python unittest discovery and Node service/cohort controls passed; no model inference or held-out evaluation attempts"


def step_runtime_controls():
    """Synthetic scheduler, horizon, source-boundary and probe controls only."""
    node = shutil.which("node")
    if not node:
        return True, "UNVERIFIED: Node.js unavailable for source-boundary controls"
    commands = ([PY, "-B", "tools/test-runtime-health.py"],
                [PY, "-B", "tools/test-calibration-horizons.py"],
                [PY, "-B", "tools/test-outcome-confidence.py"],
                [node, "tools/test-index-scope.mjs"])
    failures = []
    for command in commands:
        rc, out = run(command)
        if rc != 0:
            failures.append(command[-1] + ": " + out.strip()[-1600:])
    return not failures, ("\n".join(failures) if failures else "4 runtime control suites passed; no native inference or scheduled cycles consumed")


def selected_steps(quick=False, hooks=False, live=False):
    # This compact profile is safe for frequent local checks. The router does
    # not call checkall; no step here executes tests, generators or live tools.
    steps = [("validate", step_validate),
             ("sync-check", step_sync_check),
             ("driftcheck", step_driftcheck),
             ("fixture-pins", step_fixture_pins),
             ("router-check", step_router_check),
             ("financial-document-admission", step_financial_document_admission),
             ("retrieval-integrity", step_retrieval_integrity)]
    if not quick:
        steps += [("skills-ref", step_skills_ref),
                  ("claude-workflow-adapter", step_workflow_pins),
                  ("relay", step_relay),
                  ("gen-configs", step_gen_configs),
                  ("local-lane", step_local_lane),
                  ("lane-contract", step_lane_contract),
                  ("precommit-tree", step_precommit_tree),
                  ("vault-audit-gate", step_vault_audit_gate),
                  ("check-paths", step_check_paths),
                  ("gen-regression", step_gen_regression),
                  ("recovery-tests", step_recovery_tests),
                  ("institutional-tests", step_institutional_tests),
                  ("finance-data-tests", step_finance_data_tests),
                  ("retrieval-controls", step_retrieval_controls),
                  ("runtime-controls", step_runtime_controls),
                  ("evaluator-controls", step_evaluator_controls)]
    if hooks:
        steps.append(("hook-manifest", step_hook_manifest))
    if live:
        steps.append(("mcp-canary", step_mcp_canary))
    return steps


def result_state(good, out):
    """A zero exit status cannot promote skipped or unavailable evidence."""
    text = str(out).strip()
    if not good:
        return "failed"
    if text.startswith("STALE:"):
        return "stale"
    if text.startswith("UNVERIFIED:") or re.match(r"^[^:\n]+:\s*(?:skipped|SKIP:)", text):
        return "unavailable"
    return "passed"


def execute_profile(quick=False, hooks=False, live=False, steps=None, emit=True):
    BLOCKS.clear()
    started = datetime.now(timezone.utc).isoformat()
    rows = []
    selected = selected_steps(quick, hooks, live) if steps is None else steps
    for label, fn in selected:
        before = len(BLOCKS)
        tick = time.monotonic()
        try:
            good, out = fn()
            exception_type = None
        except Exception as exc:
            good, out = False, "%s: %s" % (type(exc).__name__, exc)
            exception_type = type(exc).__name__
        state = result_state(good, out)
        if state == "failed" and len(BLOCKS) == before:
            block(label + " failed", "this consistency check did not establish its invariant",
                  "fix the reported cause and rerun this check; do not bypass it", str(out).strip()[-2000:])
        row = {"check": label, "state": state,
               "scope": "live-tool-surface" if label == "mcp-canary" else
                        "hook-behavior" if label == "hook-manifest" else "local-offline",
               "verified_at": datetime.now(timezone.utc).isoformat(),
               "duration_seconds": round(time.monotonic() - tick, 3),
               "evidence_location": None,
               "reason": exception_type or ("invariant_checked" if state == "passed" else
                         "required_evidence_missing" if state == "unavailable" else "check_not_satisfied")}
        warning_counts = re.findall(r"\b(\d+) WARN\b", str(out))
        row["warning_count"] = max(map(int, warning_counts)) if warning_counts else len(re.findall(r"^\[WARN\]", str(out), re.M))
        rows.append(row)
        if emit:
            tail = str(out).strip().splitlines()[-1] if str(out).strip() else ""
            print("[%s] %s %s" % (state.upper(), label, tail[:150]), flush=True)
    selected_names = {name for name, _ in selected}
    for label, _ in selected_steps(False, True, True):
        if label not in selected_names:
            rows.append({"check": label, "state": "not_run", "scope":
                         "live-tool-surface" if label == "mcp-canary" else
                         "hook-behavior" if label == "hook-manifest" else "local-offline",
                         "verified_at": None, "duration_seconds": 0,
                         "evidence_location": None, "reason": "outside_requested_profile"})
    required = [row for row in rows if row["state"] != "not_run"]
    state = ("failed" if any(row["state"] == "failed" for row in required) else
             "stale" if any(row["state"] == "stale" for row in required) else
             "unavailable" if any(row["state"] == "unavailable" for row in required) else "passed")
    return {"schema": "osanwe.validation/1", "state": state,
            "scope": "quick-offline" if quick else "offline-plus-opt-in" if hooks or live else "offline",
            "started_at": started, "verified_at": datetime.now(timezone.utc).isoformat(),
            "runtime": {"python": sys.version.split()[0], "executable": sys.executable},
            "checks": rows, "counts": {s: sum(r["state"] == s for r in rows)
                                        for s in ("passed", "failed", "stale", "unavailable", "not_run")},
            "limitations": ["Offline checks do not establish live connector or native subscription operation.",
                            "Excluded checks remain not_run and are never counted as passed."]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quick", action="store_true", help="compact, read-only offline subset")
    ap.add_argument("--hooks", action="store_true", help="also execute potentially stateful hook test commands")
    ap.add_argument("--live", action="store_true", help="also contact live MCP servers")
    ap.add_argument("--json", action="store_true", help="emit only structured results; no raw diagnostic output")
    ap.add_argument("--json-report", type=Path, help="create a new structured evidence file; refuses overwrite")
    args = ap.parse_args(argv)
    if args.quick and (args.hooks or args.live):
        ap.error("--quick cannot be combined with --hooks or --live")
    if args.json_report and args.json_report.exists():
        ap.error("evidence file already exists; use a new time-suffixed path")
    report = execute_profile(args.quick, args.hooks, args.live, emit=not args.json)
    if args.json_report:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        for row in report["checks"]:
            if row["state"] != "not_run":
                row["evidence_location"] = str(args.json_report.resolve()) + "#" + row["check"]
        with args.json_report.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(report, handle, indent=2)
            handle.write("\n")
    if args.json:
        print(json.dumps(report, indent=2))
    elif report["state"] == "failed":
        for failure in BLOCKS:
            for key in ("WHAT BROKE", "WHAT IT MEANS", "WHAT TO DO", "WHAT TO PASTE BACK"):
                print("%s:\n  %s" % (key, str(failure[key]).replace("\n", "\n  ")))
    if not args.json:
        print("checkall: %s (%s; %s)" % (report["state"].upper(), report["scope"], report["counts"]))
    return 0 if report["state"] == "passed" else 1 if report["state"] in ("failed", "stale") else 2


if __name__ == "__main__":
    raise SystemExit(main())
