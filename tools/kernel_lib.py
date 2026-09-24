#!/usr/bin/env python3
"""
Osanwe invest-kernel shared library (Fable 5 final session, 2026-07-06;
Pillar-1 rate-gate replacement + VIX-halt conversion + reserve-release,
2026-07-30).

Single source of truth for the INVEST KERNEL's deterministic layer:
  - doctrine/bands machine-block parsing from the two Atlas notes
    (ref-portfolio-doctrine.md `doctrine:` block, ref-scoring-models.md
    `bands:` block), schema validation, canonicalization + sha256-8
    fingerprinting (tamper evidence, D21);
  - provenance-quote lint primitives (doctrine-lint.py, D3);
  - deployment state evaluation from RAW series (D24 -- the script computes
    "sustained 5 sessions" and the DFII10 shock/hysteresis walk, never the
    model);
  - book-snapshot exposure computation (D19 -- same trusted book format
    tools/pretrade_gate.py consumes; the model never hand-sums the book);
  - Half-Kelly two-form sizing + the W1-W8 cap waterfall (D8-D10), the
    reserve-release evaluation (P1 2026-07-30), and the hold-state
    compliance panel (D11).

Consumers: tools/doctrine-lint.py, tools/sizing-eval.py, tools/test-sizing-eval.py.
FAIL-CLOSED contract: validators raise KernelError or return explicit error
verdicts; callers treat any exception as exit 2 (refuse to size).
ASCII-only (Osanwe Pattern 22). Deps: stdlib + PyYAML (vault-standard).

P1 (2026-07-30, decision-invest-rate-gate-retire-2026-07-30):
  * dgs10_bands DELETED. The nominal 10Y LEVEL is no longer a deployment
    condition. DGS10 is carried for disclosure, for the rate_shock
    nominal-confirm screen, and for the smoothed Rf input only.
  * NEW rate_shock leg on DFII10 (10Y TIPS real yield): rise >= rise_bp_gte
    over lookback_sessions published obs, CONFIRMED by a DGS10 rise over the
    same calendar window (MAJ-4 breakeven-collapse screen), with hysteresis
    (enter on N consecutive fire sessions, exit below exit_below_bp; MAJ-5).
  * regime_throttle (VIX > 22 sustained) is a 0.5x THROTTLE, not a halt.
  * regime_halt (VIX > 35 sustained) is the only absolute 0.0x stop.
  * Multiplier stacking is MIN across active legs, never a product.
  * Distinct reason codes replace the three indistinguishable 0.5s (MIN-3).
  * Reserve-release: a configured cash reserve is netted from deployable cash
    UNLESS a named doctrine release condition machine-evaluates true.

HYSTERESIS IS A PURE FUNCTION OF THE SUPPLIED SERIES. No state file exists
and none is wanted: persisted deployment state would be an unlinted doctrine
surface that could drift silently (the exact failure mode the fingerprint
seal exists to stop). The entry/exit state machine is instead RECONSTRUCTED
by walking the evaluable sessions of the supplied series oldest-to-newest,
starting from OFF. Reconstruction depth = len(series) - lookback_sessions
sessions. The reconstruction is conservative in the open direction: a caution
state that began BEFORE the supplied window and never exited is not seen. The
inputs form therefore asks for ~90 obs (60 lookback + ~30 sessions of
reconstruction), which covers essentially every historical ON-run (median 2
sessions, 78 pct <= 10 sessions; red-team MAJ-5). Below lookback+1 obs the
leg is UNRESOLVABLE and fails closed to unknown_multiplier.
"""
import copy
import hashlib
import json
import math
import os
import re
from datetime import date, datetime
from pathlib import Path

import yaml

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", r"/path/to/vault"))  # D5 parameterization (2026-08-10)
DOCTRINE_NOTE = VAULT_ROOT / "Atlas" / "sources" / "investing" / "ref-portfolio-doctrine.md"
BANDS_NOTE = VAULT_ROOT / "Atlas" / "sources" / "investing" / "ref-scoring-models.md"
DECISIONS_DIR = VAULT_ROOT / "Calendar" / "decisions"

RATINGS_SIZABLE = ("STRONG BUY", "BUY")

# Reserve-release condition ids this library knows how to evaluate. Schema
# validation REFUSES any doctrine release_conditions id outside this set --
# an unimplemented condition must fail loudly, never evaluate to False in
# silence (that would be a doctrine promise the code does not keep).
RELEASE_IDS = ("spx-drawdown", "theme-alpha-derate", "vix-spike")


class KernelError(Exception):
    """Any doctrine/inputs defect. Callers exit 2 (fail-closed)."""


# ---------------------------------------------------------------- frontmatter
def read_frontmatter_and_body(path):
    """Return (frontmatter_dict, body_text). Raises KernelError on any defect."""
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except Exception as e:
        raise KernelError("cannot read %s: %s" % (p, e))
    if not text.startswith("---"):
        raise KernelError("%s has no frontmatter" % p)
    end = text.find("\n---", 3)
    if end < 0:
        raise KernelError("%s frontmatter is unterminated" % p)
    fm_text = text[3:end]
    body = text[end + 4:]
    try:
        fm = yaml.safe_load(fm_text)
    except Exception as e:
        raise KernelError("%s frontmatter YAML parse failed: %s" % (p, e))
    if not isinstance(fm, dict):
        raise KernelError("%s frontmatter is not a mapping" % p)
    return fm, body


# ------------------------------------------- canonicalization + fingerprint
def _norm(v):
    """Recursively normalize for canonical JSON: dates -> ISO strings."""
    if isinstance(v, (date, datetime)):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, dict):
        return {str(k): _norm(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_norm(x) for x in v]
    return v


def canonicalize(block):
    """Canonical JSON of a machine block, fingerprint field EXCLUDED."""
    d = copy.deepcopy(block)
    if isinstance(d, dict):
        d.pop("fingerprint", None)
    return json.dumps(_norm(d), sort_keys=True, separators=(",", ":"))


def compute_fingerprint(block):
    """sha256-8 of the canonicalized block (D21 tamper evidence)."""
    return hashlib.sha256(canonicalize(block).encode("utf-8")).hexdigest()[:8]


# ---------------------------------------------------------- schema validation
_DOCTRINE_REQUIRED = [
    ("schema_version",), ("block_id",), ("evaluated_by",), ("fingerprint",),
    ("ratified_by",),
    ("concentration", "thesis_theme_alpha", "amber_pct"),
    ("concentration", "thesis_theme_alpha", "red_pct"),
    ("concentration", "thesis_theme_alpha", "interim_amber_pct"),
    ("concentration", "thesis_theme_alpha", "interim_until"),
    ("concentration", "other_thesis_flag_pct"),
    ("concentration", "single_name", "amber_pct"),
    ("concentration", "single_name", "red_pct"),
    ("deployment", "default_multiplier"),
    ("deployment", "multiplier_stacking"),
    ("deployment", "rate_shock", "series"),
    ("deployment", "rate_shock", "lookback_sessions"),
    ("deployment", "rate_shock", "rise_bp_gte"),
    ("deployment", "rate_shock", "nominal_confirm_bp_gte"),
    ("deployment", "rate_shock", "enter_consecutive_sessions"),
    ("deployment", "rate_shock", "exit_below_bp"),
    ("deployment", "rate_shock", "multiplier"),
    ("deployment", "rate_shock", "unknown_multiplier"),
    ("deployment", "regime_throttle", "vix_gt"),
    ("deployment", "regime_throttle", "sustained_sessions"),
    ("deployment", "regime_throttle", "multiplier"),
    ("deployment", "regime_halt", "vix_gt"),
    ("deployment", "regime_halt", "sustained_sessions"),
    ("deployment", "regime_halt", "multiplier"),
    ("deployment", "regime_halt", "absolute"),
    ("deployment", "provenance_trust", "non_mcp_script_multiplier_cap"),
    ("deployment", "provenance_trust", "obs_max_age_days"),
    ("deployment", "reserve", "release_conditions"),
    ("override_lane", "conditions_all", "rr_ratio_gte"),
    ("override_lane", "tranche_pct_of_computed_size"),
    ("sizing", "b_cap"),
    ("sizing", "win_prob", "STRONG_BUY"),
    ("sizing", "win_prob", "BUY"),
    ("sizing", "rr_hurdle", "BUY"),
    ("sizing", "rr_hurdle", "STRONG_BUY"),
    ("sizing", "stop_rules", "distance_min_pct"),
    ("sizing", "stop_rules", "distance_max_pct"),
    ("sizing", "haircuts", "crypto"),
    ("sizing", "haircuts", "bridge_path"),
    ("sizing", "haircuts", "correlation", "threshold"),
    ("sizing", "haircuts", "correlation", "multiplier"),
    ("sizing", "max_tranche_pct_book"),
    ("sizing", "min_trade_pct_book"),
    ("sizing", "reconciliation", "kelly_form_identity_abs"),
    ("sizing", "reconciliation", "worksheet_dollars_abs"),
    ("sizing", "reconciliation", "shares_derivation_abs_usd"),
]
_BANDS_REQUIRED = [
    ("schema_version",), ("block_id",), ("evaluated_by",), ("fingerprint",),
    ("ratified_by",),
    ("piotroski", "strong_gte"), ("piotroski", "long_gate_gte"),
    ("piotroski", "weak_lte"), ("piotroski", "red_lte"),
    ("altman_z", "safe_gt"), ("altman_z", "distress_lt"), ("altman_z", "red_lt"),
    ("beneish_m", "manipulator_gt"), ("beneish_m", "clean_lt"), ("beneish_m", "red_gt"),
    ("sloan_accruals_pct", "negative_gt"), ("sloan_accruals_pct", "positive_lt"),
    ("sloan_accruals_pct", "red_gt"),
]

# Release-condition id -> the threshold keys the evaluator requires.
_RELEASE_REQUIRED_KEYS = {
    "spx-drawdown": ("drawdown_pct_gte", "lookback_sessions"),
    "theme-alpha-derate": ("eff_pct_lt",),
    "vix-spike": ("vix_gt", "obs_window"),
}


def _dig(d, path):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def validate_block_schema(block, kind):
    """kind in {'doctrine','bands'}. Returns list of error strings (empty = ok)."""
    errors = []
    required = _DOCTRINE_REQUIRED if kind == "doctrine" else _BANDS_REQUIRED
    if not isinstance(block, dict):
        return ["%s block is not a mapping" % kind]
    for path in required:
        if _dig(block, path) is None:
            errors.append("%s block missing required key: %s" % (kind, ".".join(path)))
    if kind != "doctrine":
        return errors

    # P1: the retired level-band gate must be GONE, not merely unused -- a
    # residual dgs10_bands key would be an unlinted second deployment rule.
    if _dig(block, ("deployment", "dgs10_bands")) is not None:
        errors.append("deployment.dgs10_bands is RETIRED (2026-07-30) and must be absent")
    if _dig(block, ("deployment", "regime_halt", "dgs10_gt")) is not None:
        errors.append("deployment.regime_halt.dgs10_gt is RETIRED (2026-07-30) and must be absent")

    rs = _dig(block, ("deployment", "rate_shock"))
    if isinstance(rs, dict):
        try:
            if float(rs["exit_below_bp"]) >= float(rs["rise_bp_gte"]):
                errors.append("rate_shock.exit_below_bp must be BELOW rise_bp_gte (hysteresis)")
            if int(rs["enter_consecutive_sessions"]) < 1:
                errors.append("rate_shock.enter_consecutive_sessions must be >= 1")
            if int(rs["lookback_sessions"]) < 2:
                errors.append("rate_shock.lookback_sessions must be >= 2")
            for k in ("multiplier", "unknown_multiplier"):
                if not (0.0 <= float(rs[k]) <= 1.0):
                    errors.append("rate_shock.%s must be within [0,1]" % k)
            if float(rs["nominal_confirm_bp_gte"]) < 0:
                errors.append("rate_shock.nominal_confirm_bp_gte must be >= 0")
            if not str(rs["series"]).strip():
                errors.append("rate_shock.series must name a FRED series id")
        except (KeyError, TypeError, ValueError) as e:
            errors.append("rate_shock scalars unparsable: %s" % e)

    thr = _dig(block, ("deployment", "regime_throttle"))
    hlt = _dig(block, ("deployment", "regime_halt"))
    if isinstance(thr, dict) and isinstance(hlt, dict):
        try:
            if float(hlt["vix_gt"]) <= float(thr["vix_gt"]):
                errors.append("regime_halt.vix_gt must exceed regime_throttle.vix_gt "
                              "(the halt is the tail of the throttle)")
            if float(hlt["multiplier"]) != 0.0:
                errors.append("regime_halt.multiplier must be 0.0 (the halt is absolute)")
            if not (0.0 < float(thr["multiplier"]) < 1.0):
                errors.append("regime_throttle.multiplier must be strictly within (0,1) "
                              "-- a throttle that reaches 0 is a halt wearing a throttle's name")
            if bool(hlt.get("absolute")) is not True:
                errors.append("regime_halt.absolute must be true")
        except (KeyError, TypeError, ValueError) as e:
            errors.append("regime throttle/halt scalars unparsable: %s" % e)

    rel = _dig(block, ("deployment", "reserve", "release_conditions"))
    if not isinstance(rel, list) or not rel:
        errors.append("deployment.reserve.release_conditions must be a non-empty list")
    else:
        seen = set()
        for i, c in enumerate(rel):
            if not isinstance(c, dict) or "id" not in c or "rule" not in c:
                errors.append("release_conditions[%d] needs id and rule" % i)
                continue
            cid = str(c["id"])
            if cid in seen:
                errors.append("release_conditions duplicate id '%s'" % cid)
            seen.add(cid)
            if cid not in RELEASE_IDS:
                errors.append("release_conditions[%d] id '%s' is not implemented by "
                              "kernel_lib (known: %s)" % (i, cid, ", ".join(RELEASE_IDS)))
                continue
            for k in _RELEASE_REQUIRED_KEYS[cid]:
                if c.get(k) is None:
                    errors.append("release_conditions[%d] (%s) missing %s" % (i, cid, k))

    for rating in ("STRONG_BUY", "BUY"):
        rows = _dig(block, ("sizing", "win_prob", rating))
        if not isinstance(rows, list) or not rows:
            errors.append("sizing.win_prob.%s must be a non-empty list" % rating)
            continue
        last = 0.0
        for i, row in enumerate(rows):
            if not isinstance(row, dict) or "b_max" not in row or "p" not in row:
                errors.append("win_prob.%s[%d] needs b_max and p" % (rating, i))
                continue
            if float(row["b_max"]) <= last:
                errors.append("win_prob.%s b_max must be ascending" % rating)
            last = float(row["b_max"])
            if not (0.0 < float(row["p"]) < 1.0):
                errors.append("win_prob.%s[%d].p out of (0,1)" % (rating, i))
    return errors


def load_block(kind, path=None):
    """Load + schema-validate the doctrine or bands block. Raises KernelError."""
    if kind == "doctrine":
        p = Path(path) if path else DOCTRINE_NOTE
        key = "doctrine"
    elif kind == "bands":
        p = Path(path) if path else BANDS_NOTE
        key = "bands"
    else:
        raise KernelError("unknown block kind: %s" % kind)
    fm, body = read_frontmatter_and_body(p)
    block = fm.get(key)
    if block is None:
        raise KernelError("%s carries no `%s:` machine block" % (p, key))
    errors = validate_block_schema(block, kind)
    if errors:
        raise KernelError("%s schema invalid: %s" % (key, "; ".join(errors)))
    return block, body, p


def doctrine_version(doctrine_block, bands_block):
    return "pd-%s/fb-%s" % (doctrine_block.get("schema_version"),
                            bands_block.get("schema_version"))


def doctrine_fingerprint_pair(doctrine_block, bands_block):
    return "pd-%s/fb-%s" % (compute_fingerprint(doctrine_block),
                            compute_fingerprint(bands_block))


# ------------------------------------------------------- lint leaf iteration
# Leaves exempt from the provenance-quote requirement: block meta + prose
# descriptors. Everything else that is a scalar MUST have a provenance row.
EXEMPT_LEAF_KEYS = {
    "schema_version", "block_id", "evaluated_by", "updated", "ratified_by",
    "fingerprint", "input", "scope", "drift_note", "disclosure", "invocation",
    "applies_when", "never_when", "multi_thesis_rule", "cap_stacking",
    "amount_source", "target_rule", "method", "basis", "rule", "account",
}


def iter_lint_leaves(obj, prefix=""):
    """Yield (dotted_key, scalar_value) for every lintable scalar leaf.
    Lists of scalars (enum lists) are skipped; lists of dicts recurse with
    [i] indexing. Exempt keys (meta/prose) are skipped."""
    if isinstance(obj, dict):
        for k in sorted(obj.keys()):
            key = str(k)
            path = "%s.%s" % (prefix, key) if prefix else key
            v = obj[k]
            if key in EXEMPT_LEAF_KEYS:
                continue
            for item in iter_lint_leaves(v, path):
                yield item
    elif isinstance(obj, list):
        if all(not isinstance(x, (dict, list)) for x in obj):
            return  # enum list: schema-validated, not provenance-linted
        for i, x in enumerate(obj):
            for item in iter_lint_leaves(x, "%s[%d]" % (prefix, i)):
                yield item
    else:
        yield (prefix, obj)


_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")


def value_matches_quote(value, quote):
    """True iff the block value is evidenced inside the verbatim quote.
    Numbers: numeric equality against any number parsed from the quote.
    Dates/strings: case-insensitive substring. Bools: true/false token."""
    if isinstance(value, bool):
        return ("true" if value else "false") in quote.lower()
    if isinstance(value, (int, float)):
        target = float(value)
        for m in _NUM_RE.findall(quote):
            try:
                if math.isclose(float(m), target, rel_tol=1e-9, abs_tol=1e-12):
                    return True
            except ValueError:
                pass
        return False
    return str(_norm(value)).lower() in quote.lower()


def parse_provenance_table(body):
    """Parse the `| key | value | verbatim_quote | source |` table from a note
    body. Returns {key: {value, quote, source}}. Raises KernelError if absent."""
    rows = {}
    in_table = False
    for line in body.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            in_table = False
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) >= 4 and cells[0] == "key" and cells[1] == "value":
            in_table = True
            continue
        if in_table:
            if set(cells[0]) <= set("-: "):
                continue  # separator row
            if len(cells) < 4:
                raise KernelError("provenance table row malformed: %s" % s)
            rows[cells[0]] = {"value": cells[1], "quote": cells[2], "source": cells[3]}
    if not rows:
        raise KernelError("no provenance table (| key | value | verbatim_quote | source |) found")
    return rows


def resolve_prov_source(source, host_path):
    """Map a provenance-table source cell to file text. 'self' -> the host
    note; else a Calendar/decisions/<stem>.md decision record."""
    if source == "self":
        return Path(host_path).read_text(encoding="utf-8")
    p = DECISIONS_DIR / (source + ".md")
    if not p.exists():
        raise KernelError("provenance source not found: %s" % p)
    return p.read_text(encoding="utf-8")


# ------------------------------------------------- deployment evaluation (P1)
def _clean_series(series):
    """Normalize [{date, value}] -> sorted newest-first, nulls dropped."""
    out = []
    for row in series or []:
        if not isinstance(row, dict):
            continue
        v = row.get("value")
        d = row.get("date")
        if v is None or d is None:
            continue
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(fv):
            continue
        out.append({"date": str(_norm(d)), "value": fv})
    out.sort(key=lambda r: r["date"], reverse=True)
    return out


def _age_days(today, obs_date):
    try:
        return (datetime.strptime(today, "%Y-%m-%d").date()
                - datetime.strptime(obs_date, "%Y-%m-%d").date()).days
    except ValueError:
        return 10 ** 6


def _asof(series_desc, target_date):
    """Newest obs dated on-or-before target_date (series sorted newest-first)."""
    for r in series_desc:
        if r["date"] <= target_date:
            return r
    return None


def _eval_rate_shock(cfg, dfii, dgs):
    """Reconstruct the rate_shock entry/exit state machine from raw series.

    Returns a dict:
      delta_bp        current session's DFII10 rise over lookback published obs
      confirm_bp      DGS10 rise over the SAME calendar window (screen input)
      state_on        True iff the reconstructed hysteresis state is ON now
      fire_streak     consecutive fire sessions ending at the current session
      resolvable      False when a would-be fire cannot be adjudicated
      reconstruction_sessions   how many sessions the walk covered
    Pure function: no persisted state (see module docstring).
    """
    lookback = int(cfg["lookback_sessions"])
    rise = float(cfg["rise_bp_gte"])
    confirm_gte = float(cfg["nominal_confirm_bp_gte"])
    enter_n = int(cfg["enter_consecutive_sessions"])
    exit_below = float(cfg["exit_below_bp"])

    out = {"delta_bp": None, "confirm_bp": None, "state_on": False,
           "fire_streak": 0, "resolvable": False, "reconstruction_sessions": 0,
           "screen_blocked": False, "notes": []}
    if len(dfii) < lookback + 1:
        out["notes"].append("DFII10 series has %d obs, need >= %d (lookback %d + 1) "
                            "-- rate leg unresolvable" % (len(dfii), lookback + 1, lookback))
        return out

    n_eval = len(dfii) - lookback
    out["reconstruction_sessions"] = n_eval
    deltas, confirms = [], []
    for i in range(n_eval):
        deltas.append((dfii[i]["value"] - dfii[i + lookback]["value"]) * 100.0)
        a = _asof(dgs, dfii[i]["date"])
        b = _asof(dgs, dfii[i + lookback]["date"])
        confirms.append(None if (a is None or b is None)
                        else (a["value"] - b["value"]) * 100.0)

    state_on, streak = False, 0
    for i in reversed(range(n_eval)):
        d, c = deltas[i], confirms[i]
        fire = bool(d >= rise and c is not None and c >= confirm_gte)
        if state_on and d < exit_below:
            state_on, streak = False, 0
        if not state_on:
            streak = streak + 1 if fire else 0
            if streak >= enter_n:
                state_on = True

    out["delta_bp"] = round(deltas[0], 4)
    out["confirm_bp"] = None if confirms[0] is None else round(confirms[0], 4)
    out["state_on"] = state_on
    out["fire_streak"] = streak
    out["resolvable"] = True

    # Fail-closed carve-outs: a would-be fire we cannot adjudicate is NOT a
    # silent pass. (a) the DGS10 confirm screen has no data for the window;
    # (b) the reconstruction is shorter than the entry requirement while the
    # current session fires.
    if deltas[0] >= rise:
        if confirms[0] is None:
            out["resolvable"] = False
            out["screen_blocked"] = True
            out["notes"].append("DFII10 delta %+.1fbp >= %.0fbp but the DGS10 confirm "
                                "screen has no data for the window -- unresolvable"
                                % (deltas[0], rise))
        elif n_eval < enter_n and confirms[0] >= confirm_gte:
            out["resolvable"] = False
            out["notes"].append("current session fires but only %d session(s) are "
                                "reconstructible (need %d) -- streak unconfirmable"
                                % (n_eval, enter_n))
    if out["resolvable"] and n_eval < enter_n:
        out["notes"].append("reconstruction depth %d < enter_consecutive_sessions %d "
                            "(non-firing tape, state OFF is determinate)" % (n_eval, enter_n))
    return out


def eval_deployment(doctrine, dfii10_series, dgs10_series, vix_series, rate_prov,
                    today=None, binding=True):
    """Compute the deployment STATE + multiplier from RAW series (D24).

    Leg order: VIX tail halt (absolute 0.0) -> VIX throttle (0.5) -> rate
    shock / rate unknown (0.5) -> provenance cap. Multipliers combine by MIN,
    never by product (doctrine deployment.multiplier_stacking).

    Reason codes (result["state"], highest precedence first):
      unknown-treated-halted  VIX unresolvable/stale -- 0.0, never pierceable
      halt-vix-tail           VIX > halt threshold all N obs -- 0.0 absolute
      vix-throttle            VIX > throttle threshold all N obs -- 0.5
      rate-shock-caution      DFII10 shock ON (screened + hysteresis) -- 0.5
      rate-unknown-caution    DFII10 short/stale/unadjudicable -- 0.5
      prov-capped             non mcp:/script: provenance cap binds -- 0.5
      normal                  no active condition -- 1.0
    (caution-collapsed-de-minimis is a W8 verdict code, emitted by
    size_binding, not a deployment state.)

    Never raises for missing data -- fail-closed multipliers instead.
    `binding` is accepted for call-site symmetry; the evaluation is identical
    in HOLD-STATE mode (the panel is informational either way).
    """
    dep = doctrine["deployment"]
    rate_cfg = dep["rate_shock"]
    thr_cfg = dep["regime_throttle"]
    halt_cfg = dep["regime_halt"]
    trust = dep["provenance_trust"]
    today = today or date.today().strftime("%Y-%m-%d")
    max_age = int(trust["obs_max_age_days"])
    notes = []

    dfii = _clean_series(dfii10_series)
    dgs = _clean_series(dgs10_series)
    vix = _clean_series(vix_series)

    result = {
        "state": "normal",
        "reasons": [],
        "band": "normal:1.0",
        "multiplier": float(dep["default_multiplier"]),
        "halt_active": False,
        "halt_status": "ok",
        "rate_series": str(rate_cfg["series"]),
        "rate_lookback_sessions": int(rate_cfg["lookback_sessions"]),
        "rate_delta_bp": None,
        "rate_confirm_bp": None,
        "rate_fire_streak": 0,
        "rate_reconstruction_sessions": 0,
        "dfii10_newest": dfii[0]["value"] if dfii else None,
        "dgs10_newest": dgs[0]["value"] if dgs else None,
        "vix_max_recent": None,
        "notes": notes,
    }

    legs = {"default": float(dep["default_multiplier"])}

    # ---- VIX legs first (the only absolute stop lives here).
    n_halt = int(halt_cfg["sustained_sessions"])
    n_thr = int(thr_cfg["sustained_sessions"])
    n_vix_need = max(n_halt, n_thr)
    vix_unknown = False
    if len(vix) < n_vix_need:
        vix_unknown = True
        notes.append("VIX series has %d obs, need %d -> fail-closed "
                     "(unknown-treated-halted)" % (len(vix), n_vix_need))
    else:
        vix_age = _age_days(today, vix[0]["date"])
        if vix_age > max_age:
            vix_unknown = True
            notes.append("VIX newest obs %s is %dd old (> %dd) -> fail-closed "
                         "(unknown-treated-halted)" % (vix[0]["date"], vix_age, max_age))

    if vix_unknown:
        result["state"] = "unknown-treated-halted"
        result["reasons"] = ["unknown-treated-halted"]
        result["band"] = "unknown-treated-halted:0.0"
        result["multiplier"] = 0.0
        result["halt_active"] = True
        result["halt_status"] = "unknown-treated-halted"
        return result

    result["vix_max_recent"] = max(r["value"] for r in vix[:n_vix_need])
    vix_tail = all(r["value"] > float(halt_cfg["vix_gt"]) for r in vix[:n_halt])
    vix_thr = all(r["value"] > float(thr_cfg["vix_gt"]) for r in vix[:n_thr])
    if vix_tail:
        legs["halt-vix-tail"] = float(halt_cfg["multiplier"])
        result["reasons"].append("halt-vix-tail")
        result["halt_active"] = True
        result["halt_status"] = "halt-vix-tail"
        notes.append("TAIL HALT: all %d recent VIX obs > %s -- absolute 0.0x "
                     "(COVID-class stress only)" % (n_halt, halt_cfg["vix_gt"]))
    elif vix_thr:
        legs["vix-throttle"] = float(thr_cfg["multiplier"])
        result["reasons"].append("vix-throttle")
        notes.append("VIX throttle: all %d recent VIX obs > %s -> %sx "
                     "(converted from an absolute halt 2026-07-30)"
                     % (n_thr, thr_cfg["vix_gt"], thr_cfg["multiplier"]))

    # ---- rate leg (DFII10 shock, DGS10-confirmed, hysteretic).
    rate = _eval_rate_shock(rate_cfg, dfii, dgs)
    notes.extend(rate["notes"])
    result["rate_delta_bp"] = rate["delta_bp"]
    result["rate_confirm_bp"] = rate["confirm_bp"]
    result["rate_fire_streak"] = rate["fire_streak"]
    result["rate_reconstruction_sessions"] = rate["reconstruction_sessions"]

    rate_stale = False
    if dfii:
        age = _age_days(today, dfii[0]["date"])
        if age > max_age:
            rate_stale = True
            notes.append("DFII10 newest obs %s is %dd old (> %dd) -> rate leg unknown"
                         % (dfii[0]["date"], age, max_age))

    if (not rate["resolvable"]) or rate_stale:
        legs["rate-unknown-caution"] = float(rate_cfg["unknown_multiplier"])
        result["reasons"].append("rate-unknown-caution")
    elif rate["state_on"]:
        legs["rate-shock-caution"] = float(rate_cfg["multiplier"])
        result["reasons"].append("rate-shock-caution")
        notes.append("RATE SHOCK ON: %s +%.1fbp over %s obs (DGS10 confirm %+.1fbp >= %s), "
                     "hysteresis entered (streak %d >= %s); exits below %sbp"
                     % (rate_cfg["series"], rate["delta_bp"], rate_cfg["lookback_sessions"],
                        rate["confirm_bp"] if rate["confirm_bp"] is not None else float("nan"),
                        rate_cfg["nominal_confirm_bp_gte"], rate["fire_streak"],
                        rate_cfg["enter_consecutive_sessions"], rate_cfg["exit_below_bp"]))

    # ---- provenance trust: non-mcp/script yield never earns full deployment.
    prov = str(rate_prov or "")
    if not (prov.startswith("mcp:") or prov.startswith("script:")):
        cap = float(trust["non_mcp_script_multiplier_cap"])
        legs["prov-capped"] = cap
        result["reasons"].append("prov-capped")
        notes.append("rate-series prov '%s' not mcp:/script: -> multiplier capped at %s"
                     % (prov, cap))

    # ---- MIN stacking (never a product).
    mult = min(legs.values())
    result["multiplier"] = mult

    order = ["halt-vix-tail", "vix-throttle", "rate-shock-caution",
             "rate-unknown-caution", "prov-capped"]
    state = "normal"
    for code in order:
        if code in result["reasons"]:
            state = code
            break
    result["state"] = state
    result["band"] = "%s:%s" % (state, mult)
    return result


def eval_reserve_release(doctrine, inputs, account):
    """Evaluate the doctrine reserve RELEASE conditions (P1 2026-07-30).

    A configured cash reserve is netted from deployable cash UNLESS at least
    one named condition machine-evaluates TRUE. A condition whose inputs are
    missing evaluates UNKNOWN and does NOT release (releasing cash is the
    risk-increasing direction; unknown fails toward the reserve staying on).
    Returns a stamp dict; never raises.
    """
    cfg = doctrine["deployment"]["reserve"]
    conds = {}
    released_by = []
    vix = _clean_series(inputs.get("vix_series"))

    for c in cfg["release_conditions"]:
        cid = str(c["id"])
        row = {"met": False, "status": "unknown", "rule": str(c.get("rule", "")),
               "inputs": {}, "prov": ""}
        if cid == "spx-drawdown":
            close = inputs.get("spx_close")
            high = inputs.get("spx_trailing_high")
            row["prov"] = str(inputs.get("spx_prov") or "")
            row["inputs"] = {
                "spx_close": None if close is None else float(close),
                "spx_trailing_high": None if high is None else float(high),
                "drawdown_pct_gte": float(c["drawdown_pct_gte"]),
                "lookback_sessions": int(c["lookback_sessions"]),
            }
            if close is not None and high is not None and float(high) > 0:
                trigger = (1.0 - float(c["drawdown_pct_gte"]) / 100.0) * float(high)
                row["inputs"]["trigger_level"] = round(trigger, 4)
                row["inputs"]["drawdown_pct"] = round(
                    (1.0 - float(close) / float(high)) * 100.0, 4)
                row["met"] = float(close) <= trigger
                row["status"] = "true" if row["met"] else "false"
        elif cid == "theme-alpha-derate":
            eff = inputs.get("theme_alpha_eff_pct")
            row["prov"] = str(inputs.get("theme_alpha_prov") or "")
            row["inputs"] = {"theme_alpha_eff_pct": None if eff is None else float(eff),
                             "eff_pct_lt": float(c["eff_pct_lt"])}
            if eff is not None:
                row["met"] = float(eff) < float(c["eff_pct_lt"])
                row["status"] = "true" if row["met"] else "false"
        elif cid == "vix-spike":
            window = int(c["obs_window"])
            row["prov"] = str(inputs.get("vix_prov") or "")
            recent = [r["value"] for r in vix[:window]]
            row["inputs"] = {"vix_recent": recent, "obs_window": window,
                             "vix_gt": float(c["vix_gt"]),
                             "vix_max_recent": max(recent) if recent else None}
            if len(recent) >= window:
                row["met"] = any(v > float(c["vix_gt"]) for v in recent)
                row["status"] = "true" if row["met"] else "false"
        conds[cid] = row
        if row["met"]:
            released_by.append(cid)

    reserve_amount = 0.0
    if account == "tax_advantaged":
        reserve_amount = float(inputs.get("cash_reserve", 0.0) or 0.0)
    released = bool(released_by)
    return {
        "applicable": account == "tax_advantaged",
        "released": released,
        "released_by": sorted(released_by),
        "reserve_amount": round(reserve_amount, 2),
        "reserve_applied": 0.0 if released else round(reserve_amount, 2),
        "conditions": conds,
    }


# ------------------------------------------------------ book exposure (D19)
def book_exposures(book, symbol):
    """Validate a trusted --book snapshot (same format tools/pretrade_gate.py
    consumes) and return (total, name_pct, thesis_pct_map). Raises KernelError."""
    if not isinstance(book, dict):
        raise KernelError("book snapshot is not an object")
    total = book.get("total_value")
    if isinstance(total, bool) or not isinstance(total, (int, float)):
        raise KernelError("book total_value must be a number")
    total = float(total)
    if not math.isfinite(total) or total <= 0:
        raise KernelError("book total_value must be finite and > 0")
    positions = book.get("positions")
    if not isinstance(positions, list):
        raise KernelError("book positions must be a list")
    pos_sum = 0.0
    for p in positions:
        if not isinstance(p, dict):
            raise KernelError("book position is not an object")
        v = p.get("value", 0)
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)):
            raise KernelError("book position value must be a finite number")
        pos_sum += float(v)
    if pos_sum > total * 1.02:
        raise KernelError("book inconsistent: positions sum %.2f > total %.2f" % (pos_sum, total))
    if pos_sum < total * 0.90:
        raise KernelError("book inconsistent: positions sum %.2f < 90%% of total %.2f "
                          "(inflated denominator?)" % (pos_sum, total))
    sym = str(symbol).strip().upper()
    name_val = sum(float(p.get("value", 0)) for p in positions
                   if str(p.get("symbol", "")).strip().upper() == sym)
    thesis_pct = {}
    for p in positions:
        t = str(p.get("thesis", "")).strip()
        if t:
            thesis_pct[t] = thesis_pct.get(t, 0.0) + float(p.get("value", 0))
    thesis_pct = {t: round(v / total * 100.0, 4) for t, v in thesis_pct.items()}
    return total, round(name_val / total * 100.0, 4), thesis_pct


# --------------------------------------------------------------- Kelly (D8/D9)
def kelly_two_form(p, b):
    """Two algebraically-identical Kelly forms computed via different paths.
    F1 win-prob form; F2 expectation form. Caller asserts |F1-F2| tolerance."""
    f1 = (p * (b + 1.0) - 1.0) / b
    f2 = p - (1.0 - p) / b
    return f1, f2


def pick_win_prob(doctrine, rating, b_capped):
    key = str(rating).strip().upper().replace(" ", "_")
    rows = doctrine["sizing"]["win_prob"].get(key)
    if not rows:
        raise KernelError("no win_prob table for rating '%s' (sizable: %s)"
                          % (rating, ", ".join(RATINGS_SIZABLE)))
    for row in rows:
        if b_capped <= float(row["b_max"]):
            return float(row["p"])
    return float(rows[-1]["p"])


def thesis_line_pct(doctrine, thesis, today=None):
    """The amber/flag line (in pct) applicable to a thesis today."""
    conc = doctrine["concentration"]
    today = today or date.today().strftime("%Y-%m-%d")
    if thesis == "theme-alpha":
        t = conc["thesis_theme_alpha"]
        interim_until = str(_norm(t["interim_until"]))
        if today <= interim_until:
            return float(t["interim_amber_pct"])
        return float(t["amber_pct"])
    return float(conc["other_thesis_flag_pct"])


def _exposures(book, symbol, exposures=None):
    """Book-derived exposures, or the recorded snapshot a worksheet embeds
    (--check path: arithmetic integrity is re-derived from the same numbers)."""
    if exposures is not None:
        return (float(exposures["book_total"]), float(exposures["name_pct"]),
                {str(k): float(v) for k, v in (exposures.get("thesis_pct_book") or {}).items()})
    return book_exposures(book, symbol)


def _deployment_from_inputs(doctrine, inputs, today, binding):
    return eval_deployment(doctrine,
                           inputs.get("dfii10_series"),
                           inputs.get("dgs10_series"),
                           inputs.get("vix_series"),
                           inputs.get("rate_prov") or inputs.get("dgs10_prov"),
                           today=today, binding=binding)


# ------------------------------------------------------ sizing waterfall (D10)
def size_binding(doctrine, inputs, book, today=None, exposures=None):
    """BINDING-mode sizing. inputs is a plain dict (values already extracted
    from the {value, prov} worksheet fields). Raises KernelError on any
    fill-rule violation (caller -> exit 2). Returns the full computed dict."""
    s = doctrine["sizing"]
    today = today or date.today().strftime("%Y-%m-%d")
    rating = str(inputs["rating"]).strip().upper()
    if rating not in RATINGS_SIZABLE:
        raise KernelError("BINDING sizing only for %s (got '%s')"
                          % ("/".join(RATINGS_SIZABLE), rating))

    entry = float(inputs["entry"])
    stop = float(inputs["stop"])
    target_model = float(inputs["target_model"])
    analyst = inputs.get("target_analyst_median")
    if entry <= 0 or stop <= 0 or target_model <= 0:
        raise KernelError("entry/stop/target must be positive")
    if not (stop < entry < target_model):
        raise KernelError("require stop < entry < target for a long ADD bracket")

    # D9: sizing target = MIN(model target, analyst median PT when available).
    sizing_target = target_model
    if analyst is not None:
        sizing_target = min(target_model, float(analyst))

    # D20: stop sanity band.
    stop_dist_pct = (entry - stop) / entry * 100.0
    if not (float(s["stop_rules"]["distance_min_pct"]) <= stop_dist_pct
            <= float(s["stop_rules"]["distance_max_pct"])):
        raise KernelError("STOP-BAND-FAIL: stop distance %.2f%% outside [%s, %s]"
                          % (stop_dist_pct, s["stop_rules"]["distance_min_pct"],
                             s["stop_rules"]["distance_max_pct"]))
    if str(inputs.get("stop_basis", "")).strip() not in set(s["stop_rules"]["basis_enum"]):
        raise KernelError("stop_basis '%s' not in enum %s"
                          % (inputs.get("stop_basis"), s["stop_rules"]["basis_enum"]))
    if str(inputs.get("target_basis", "")).strip() not in set(s["target_basis_enum"]):
        raise KernelError("target_basis '%s' not in enum %s"
                          % (inputs.get("target_basis"), s["target_basis_enum"]))

    b_raw = (sizing_target - entry) / (entry - stop)
    hurdle = float(s["rr_hurdle"][rating.replace(" ", "_")])
    if b_raw < hurdle:
        raise KernelError("HURDLE-FAIL: R/R %.2f:1 < %.1f:1 %s hurdle (sizing target %.2f)"
                          % (b_raw, hurdle, rating, sizing_target))
    b = min(b_raw, float(s["b_cap"]))

    # W1: Half-Kelly at capped b, two forms.
    p = pick_win_prob(doctrine, rating, b)
    f1, f2 = kelly_two_form(p, b)
    if abs(f1 - f2) > float(s["reconciliation"]["kelly_form_identity_abs"]):
        raise KernelError("KELLY-FORM-DIVERGENCE: |%.12f - %.12f| > tolerance (script bug)"
                          % (f1, f2))
    f_half = f1 / 2.0
    if f_half <= 0:
        return {"verdict": "NO-SIZE", "reason": "non-positive Kelly edge",
                "reason_code": "non-positive-kelly",
                "p": p, "b_raw": round(b_raw, 6), "b": b,
                "f_full": round(f1, 6), "f_half": round(f_half, 6)}

    # W2: multiplicative haircuts.
    haircuts = []
    f_adj = f_half
    if bool(inputs.get("is_crypto", False)):
        f_adj *= float(s["haircuts"]["crypto"])
        haircuts.append("crypto x%s" % s["haircuts"]["crypto"])
    if str(inputs.get("scoring_path", "")) == "negative-eps-bridge":
        f_adj *= float(s["haircuts"]["bridge_path"])
        haircuts.append("bridge-path x%s" % s["haircuts"]["bridge_path"])
    if bool(inputs.get("corr_gt_threshold_flag", False)):
        f_adj *= float(s["haircuts"]["correlation"]["multiplier"])
        haircuts.append("correlation x%s" % s["haircuts"]["correlation"]["multiplier"])

    # W3: dollars.
    total, name_pct, thesis_pct_book = _exposures(book, inputs["symbol"], exposures)
    w3 = f_adj * total

    # W4: caps (min of tranche / name headroom / thesis headroom / cash).
    caps = {}
    caps["max_tranche_pct_book"] = float(s["max_tranche_pct_book"]) / 100.0 * total

    single_amber = float(doctrine["concentration"]["single_name"]["amber_pct"])
    caps["single-name-headroom"] = max(0.0, (single_amber - name_pct) / 100.0 * total)

    # Thesis headroom: MIN over ALL memberships, effective basis when supplied.
    thesis_list = list(inputs.get("thesis_list") or [])
    eff = dict(inputs.get("effective_thesis_pct") or {})
    thesis_details = {}
    if thesis_list:
        head = None
        for t in thesis_list:
            strict = float(thesis_pct_book.get(t, 0.0))
            e = float(eff.get(t, 0.0))
            if e and e < strict - 0.25:
                raise KernelError("effective_thesis_pct[%s]=%.2f below book strict %.2f "
                                  "(cannot claim effective under strict)" % (t, e, strict))
            used = max(strict, e)
            line = thesis_line_pct(doctrine, t, today)
            h = max(0.0, (line - used) / 100.0 * total)
            thesis_details[t] = {"pct_used": round(used, 4), "line_pct": line,
                                 "headroom_usd": round(h, 2)}
            head = h if head is None else min(head, h)
        caps["thesis-headroom"] = head
    else:
        caps["thesis-headroom"] = caps["max_tranche_pct_book"]  # no thesis: not binding

    # Account-scoped cash (D25): a configured account cash reserve is netted UNLESS a doctrine
    # release condition machine-evaluates true (P1 2026-07-30).
    account = str(inputs.get("account", "")).strip().lower()
    if account not in ("taxable", "tax_advantaged"):
        raise KernelError("account must be taxable|tax_advantaged (got '%s')" % account)
    cash = float(inputs["account_cash"])
    if account == "tax_advantaged" and "cash_reserve" not in inputs:
        raise KernelError("tax-advantaged sizing requires a cash_reserve input")
    reserve_release = eval_reserve_release(doctrine, inputs, account)
    caps["deployable-cash"] = max(0.0, cash - reserve_release["reserve_applied"])

    w6 = min(w3, *caps.values())
    binding = "kelly" if w6 == w3 else min(caps, key=lambda k: caps[k])
    if w6 <= 0:
        return {"verdict": "NO-TRADE", "reason": "zero headroom (%s)" % binding,
                "reason_code": "zero-headroom",
                "binding_chain": [binding], "p": p, "b_raw": round(b_raw, 6), "b": b,
                "f_half": round(f_half, 6), "caps": {k: round(v, 2) for k, v in caps.items()},
                "reserve_release": reserve_release,
                "book_total": round(total, 2), "name_pct": name_pct,
                "thesis_details": thesis_details}

    # W7: deployment multiplier or lawful override.
    dep = _deployment_from_inputs(doctrine, inputs, today, True)
    binding_chain = [binding]
    override_used = False
    ov = inputs.get("override") or {}

    # Override AVAILABILITY is always reported (N/5); INVOCATION is separate
    # and requires a verbatim user directive (the model never self-invokes).
    # P1: an OBSERVABLE sub-1.0 state -- including the VIX tail halt -- is
    # pierceable at the single 25pct tranche. unknown-treated-halted is NOT.
    lane_cfg = doctrine["override_lane"]
    observable_sub1 = (dep["halt_status"] != "unknown-treated-halted"
                       and dep["multiplier"] < 1.0)
    avail_conditions = {
        "multiplier_below_1_observable": observable_sub1,
        "rr_gte_floor": b_raw >= float(lane_cfg["conditions_all"]["rr_ratio_gte"]),
        "forensic_clean": ov.get("forensic_clean") is True,
        "gate_f_disciplined": str(ov.get("gate_f_verdict", "")).strip().upper() == "DISCIPLINED",
        "headrooms_positive": (caps["single-name-headroom"] > 0
                               and caps["thesis-headroom"] > 0
                               and caps["deployable-cash"] > 0),
    }
    override_availability = {
        "conditions_met": sum(1 for v in avail_conditions.values() if v),
        "of": len(avail_conditions),
        "detail": avail_conditions,
        "halt_blocks_lane": dep["halt_status"] == "unknown-treated-halted",
    }
    if bool(ov.get("invoked", False)):
        problems = []
        if dep["halt_status"] == "unknown-treated-halted":
            problems.append("deployment state is unknown-treated-halted "
                            "(never pierceable -- the lane needs an OBSERVABLE state)")
        if dep["multiplier"] >= 1.0:
            problems.append("multiplier is 1.0 -- override lane does not apply")
        if b_raw < float(lane_cfg["conditions_all"]["rr_ratio_gte"]):
            problems.append("rr %.2f < override floor %s"
                            % (b_raw, lane_cfg["conditions_all"]["rr_ratio_gte"]))
        if ov.get("forensic_clean") is not True:
            problems.append("forensic_clean is not True (N/A counts as NOT clean)")
        if str(ov.get("gate_f_verdict", "")).strip().upper() != "DISCIPLINED":
            problems.append("GATE-F verdict is not DISCIPLINED")
        if not (caps["single-name-headroom"] > 0 and caps["thesis-headroom"] > 0
                and caps["deployable-cash"] > 0):
            problems.append("a concentration/cash headroom is non-positive")
        if not str(ov.get("user_directive", "")).strip():
            problems.append("no verbatim user directive (model never self-invokes)")
        if problems:
            raise KernelError("OVERRIDE-UNLAWFUL: " + "; ".join(problems))
        tranche = float(lane_cfg["tranche_pct_of_computed_size"])
        w7 = w6 * tranche / 100.0
        override_used = True
        binding_chain.append("override-%gpct-of-computed" % tranche)
    else:
        w7 = w6 * dep["multiplier"]
        if dep["multiplier"] < 1.0:
            binding_chain.append("deploy-%s-%s" % (dep["state"], dep["multiplier"]))

    # W8: de-minimis floor. MAJ-6: a 0.5x "caution" is a SILENT 0.0x whenever
    # it drags a would-have-passed size under the floor -- that state gets its
    # own reason code so the three 0.5s never again read alike.
    floor = float(s["min_trade_pct_book"]) / 100.0 * total
    if w7 < floor:
        collapsed = (w6 >= floor and dep["multiplier"] > 0.0
                     and (dep["multiplier"] < 1.0 or override_used))
        reason_code = "caution-collapsed-de-minimis" if collapsed else "de-minimis"
        return {"verdict": "NO-TRADE",
                "reason": "final %.2f below de-minimis floor %.2f (%.1f%% of book)"
                          % (w7, floor, float(s["min_trade_pct_book"])),
                "reason_code": reason_code,
                "binding_chain": binding_chain, "p": p, "b_raw": round(b_raw, 6), "b": b,
                "f_half": round(f_half, 6), "caps": {k: round(v, 2) for k, v in caps.items()},
                "w6_computed_size": round(w6, 2),
                "deployment": dep, "override_used": override_used,
                "override_availability": override_availability,
                "reserve_release": reserve_release,
                "book_total": round(total, 2), "name_pct": name_pct,
                "thesis_details": thesis_details}

    final_dollars = round(w7, 2)
    shares = round(final_dollars / entry, 6)
    return {
        "verdict": "SIZE-OK",
        "reason_code": "ok",
        "sizing_target": round(sizing_target, 4),
        "stop_dist_pct": round(stop_dist_pct, 4),
        "b_raw": round(b_raw, 6), "b": b, "p": p,
        "f_full_form1": round(f1, 6), "f_full_form2": round(f2, 6),
        "f_half": round(f_half, 6), "haircuts": haircuts,
        "f_adjusted": round(f_adj, 6),
        "w3_raw_dollars": round(w3, 2),
        "caps": {k: round(v, 2) for k, v in caps.items()},
        "w6_computed_size": round(w6, 2),
        "deployment": dep,
        "override_used": override_used,
        "override_availability": override_availability,
        "reserve_release": reserve_release,
        "final_dollars": final_dollars,
        "final_shares": shares,
        "position_size_pct": round(final_dollars / total * 100.0, 4),
        "binding_chain": binding_chain,
        "book_total": round(total, 2), "name_pct": name_pct,
        "thesis_details": thesis_details,
    }


def hold_state_panel(doctrine, inputs, book, today=None):
    """HOLD-STATE compliance panel (D11): no Kelly; headrooms + deployment
    state + current size vs caps. Positions flagged transferred_basis get the no-P&L caveat."""
    today = today or date.today().strftime("%Y-%m-%d")
    symbol = str(inputs["symbol"]).strip().upper()
    total, name_pct, thesis_pct_book = book_exposures(book, symbol)
    conc = doctrine["concentration"]
    single_amber = float(conc["single_name"]["amber_pct"])
    single_red = float(conc["single_name"]["red_pct"])
    thesis_list = list(inputs.get("thesis_list") or [])
    eff = dict(inputs.get("effective_thesis_pct") or {})
    theses = {}
    for t in thesis_list:
        strict = float(thesis_pct_book.get(t, 0.0))
        used = max(strict, float(eff.get(t, 0.0)))
        line = thesis_line_pct(doctrine, t, today)
        theses[t] = {"pct_used": round(used, 4), "line_pct": line,
                     "status": "over-line" if used >= line else "under-line",
                     "headroom_usd": round(max(0.0, (line - used) / 100.0 * total), 2)}
    dep = _deployment_from_inputs(doctrine, inputs, today, False)
    notes = []
    if bool(inputs.get("is_crypto", False)) and bool(inputs.get("transferred_basis", False)):
        notes.append("Transferred-basis caveat: cost basis is unreliable at the broker for externally "
                     "transferred positions; "
                     "report current value only, never P&L")
    return {
        "verdict": "HOLD-STATE",
        "book_total": round(total, 2),
        "name_pct": name_pct,
        "single_name_status": ("red" if name_pct >= single_red
                               else "amber" if name_pct >= single_amber else "ok"),
        "single_name_amber_pct": single_amber, "single_name_red_pct": single_red,
        "theses": theses,
        "deployment": dep,
        "max_tranche_usd_if_add": round(float(doctrine["sizing"]["max_tranche_pct_book"])
                                        / 100.0 * total, 2),
        "notes": notes,
    }
