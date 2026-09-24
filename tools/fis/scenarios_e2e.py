#!/usr/bin/env python3
"""W8 -- Cross-Domain End-to-End Scenarios for the Financial Intelligence System.

EXCLUSIVE FILE OWNERSHIP (W8):
    tools/fis/scenarios_e2e.py
    tools/fis/test_scenarios_e2e.py
    _work/fis-data/scenarios/

Eighteen runnable scenarios. Every scenario is driven through the SAME
ordered 18-stage pipeline, and every stage records one of four statuses:

    EXECUTED                 stage ran and produced its artifact
    SKIPPED-NOT-APPLICABLE   stage is structurally meaningless here (with reason)
    BLOCKED                  stage refused to produce a number (safe degraded mode)
    FAILED                   stage raised (fail-closed; harness exits nonzero)

Pipeline stages (fixed order, index 1..18):

     1  EVENT_INGESTION
     2  VALIDATION
     3  PROVENANCE_REGISTRATION
     4  TEMPORAL_STORAGE            (effective_date / known_at / recorded_at)
     5  DEPENDENCY_PROPAGATION
     6  STALE_OUTPUT_INVALIDATION
     7  DIGITAL_TWIN_UPDATE
     8  PORTFOLIO_EFFECT
     9  TAX_EFFECT
    10  LIQUIDITY_EFFECT
    11  RISK_EFFECT
    12  GOAL_EFFECT
    13  ALTERNATIVES_GENERATED
    14  NO_ACTION_PRESENT
    15  SKEPTICAL_REVIEW
    16  DECISION_OBJECT
    17  APPROVAL_ENFORCEMENT
    18  AUDIT_HISTORY

Invariants enforced by the harness (see test_scenarios_e2e.py):
  * NO-ACTION is a generated alternative in every scenario.
  * No scenario ever reaches an EXECUTED financial action. A consequential
    recommendation ends in AWAITING-APPROVAL; a no-action recommendation ends
    in NO-CONSEQUENTIAL-ACTION; a degraded scenario ends in BLOCKED-DEGRADED.
  * A published output whose upstream fact changed is STALE: reading it for
    current use raises StaleOutputError, and the marker read returns
    BLOCKED-STALE. This is real provenance-digest invalidation, not a flag.
  * Every artifact carries data_classification = SYNTHETIC-NOT-USER-DATA.

Determinism: seeded random.Random only, fixed simulation clock, no network,
no wall-clock dependence in any assertion or artifact field.

Other FIS modules are imported READ-ONLY and never modified. Defects found in
them are reported to _work/fis-data/scenarios/BLOCKING-FINDINGS.md.

Usage:
    python tools/fis/scenarios_e2e.py            # run all 18, write artifacts
    python tools/fis/scenarios_e2e.py --only S01

ASCII only. Standard library only. No network.
"""

from __future__ import annotations

import copy
import datetime as _dt
import json
import os
import random
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import calcs_household                                    # noqa: E402
import calcs_ledger                                       # noqa: E402
import obs                                                # noqa: E402
import portfolio_engine                                   # noqa: E402
import provenance                                         # noqa: E402
import risk_engine                                        # noqa: E402
import shadow                                             # noqa: E402
import taxlot_ext                                         # noqa: E402
import twin_identity                                      # noqa: E402
import twin_scenarios                                     # noqa: E402
import twin_schema                                        # noqa: E402


# ===========================================================================
# Constants
# ===========================================================================

DATA_CLASSIFICATION = "SYNTHETIC-NOT-USER-DATA"
HARNESS_ID = "fis-w8-scenarios-e2e"
HARNESS_VERSION = "1.0"

OUT_DIR = os.path.join(REPO_ROOT, "_work", "fis-data", "scenarios")
STATE_DIR = os.path.join(OUT_DIR, "_state")
FIXTURE_DIR = os.path.join(
    REPO_ROOT, "Efforts", "osanwe-v2-overhaul", "_work",
    "fis-data", "synthetic-households")

# Fixed simulation clock. No wall-clock value ever reaches an assertion.
SIM_EFFECTIVE = "2026-08-28"
SIM_KNOWN_PRE = "2026-08-26"
SIM_KNOWN_POST = "2026-08-28"
SIM_CLOCK = "2026-08-28T00:00:00Z"
SIM_EPOCH = "2000-01-01"

STAGES = [
    "EVENT_INGESTION",
    "VALIDATION",
    "PROVENANCE_REGISTRATION",
    "TEMPORAL_STORAGE",
    "DEPENDENCY_PROPAGATION",
    "STALE_OUTPUT_INVALIDATION",
    "DIGITAL_TWIN_UPDATE",
    "PORTFOLIO_EFFECT",
    "TAX_EFFECT",
    "LIQUIDITY_EFFECT",
    "RISK_EFFECT",
    "GOAL_EFFECT",
    "ALTERNATIVES_GENERATED",
    "NO_ACTION_PRESENT",
    "SKEPTICAL_REVIEW",
    "DECISION_OBJECT",
    "APPROVAL_ENFORCEMENT",
    "AUDIT_HISTORY",
]

S_EXECUTED = "EXECUTED"
S_SKIPPED = "SKIPPED-NOT-APPLICABLE"
S_BLOCKED = "BLOCKED"
S_FAILED = "FAILED"

GATE_PENDING = "PENDING"
GATE_AWAITING = "AWAITING-APPROVAL"
GATE_NO_ACTION = "NO-CONSEQUENTIAL-ACTION"
GATE_DEGRADED = "BLOCKED-DEGRADED"

NO_ACTION_ID = "ALT-NO-ACTION"

# Objective-function assumptions. Both are disclosed and challenged in every
# artifact; they are parameters, not evidence.
REBALANCE_PREMIUM = 0.004      # 40 bp of notional moved toward target
LIQUIDITY_PENALTY_RATE = 0.10  # 10c per dollar of cash below the floor

# Synthetic price table. Nominal relative pricing only; absolute levels are
# rescaled per account so the portfolio reconciles with the twin's stated
# balance (see implied_prices).
NOMINAL_PRICES = {
    "ZPHR": 142.50,
    "TOTMKT-SYNTH": 128.40,
    "TGT2035-SYNTH": 54.00,
    "TGT2055-SYNTH": 62.00,
    "TGT2060-SYNTH": 60.00,
    "TGT2065-SYNTH": 58.00,
    "USAGG-SYNTH": 42.00,
    "HSAIDX-SYNTH": 58.00,
    "BONDIDX-SYNTH": 47.50,
    "BNDLAD-SYNTH": 51.20,
    "USBND-LADDER-SYNTH": 49.80,
    "DIVGRO-SYNTH": 96.30,
    "DIVARISTO-SYNTH": 88.10,
    "SMALLCAP-SYNTH": 73.40,
    "EDUAGG-SYNTH": 45.60,
}

BOND_SYMBOLS = frozenset({
    "USAGG-SYNTH", "BONDIDX-SYNTH", "BNDLAD-SYNTH", "USBND-LADDER-SYNTH",
})

TAXABLE_ACCOUNT_TYPES = frozenset({"taxable", "brokerage"})

TARGETS_BY_LEVEL = {
    "conservative": {"equity": 0.35, "bonds": 0.55, "cash": 0.10},
    "moderately_conservative": {"equity": 0.45, "bonds": 0.45, "cash": 0.10},
    "moderate": {"equity": 0.55, "bonds": 0.35, "cash": 0.10},
    "moderately_aggressive": {"equity": 0.70, "bonds": 0.22, "cash": 0.08},
    "aggressive": {"equity": 0.80, "bonds": 0.13, "cash": 0.07},
}

# Findings against OTHER modules, discovered while wiring W8. Reported to
# BLOCKING-FINDINGS.md and referenced by the scenarios they degrade.
KNOWN_FINDINGS = [
    {
        "finding_id": "W8-F1",
        "module": "tools/fis/twin_scenarios.py",
        "location": "twin_scenarios.py:44-54 (_holdings_mv)",
        "severity": "HIGH",
        "title": "Unknown symbols are silently priced at 0.00",
        "detail": (
            "_holdings_mv() resolves a price with "
            "prices.get(h.get('symbol'), 0.0) against a hard-coded 5-symbol "
            "table. Any holding outside that table contributes 0.00 to market "
            "value, so net_worth()['reconciles'] is False for 6 of the 7 "
            "shipped synthetic households even though validate_twin() reports "
            "zero errors. The failure is silent: nothing raises, and the only "
            "signal is a boolean buried in the result."),
        "evidence": (
            "hh-early-career.json holds TGT2065-SYNTH (not in the table); "
            "net_worth() reports reconciles=False with 0 schema errors. "
            "Only hh-tech-accumulator.json reconciles."),
        "recommended_fix": (
            "Replace the literal table with an explicit price parameter "
            "(prices=None) and, when a symbol has no mark, append to "
            "data_gaps ('no price for SYMBOL; contribution excluded') and "
            "set reconciles=False with a per-symbol reason list instead of "
            "silently valuing the position at zero."),
    },
    {
        "finding_id": "W8-F2",
        "module": "tools/fis/twin_scenarios.py",
        "location": "twin_scenarios.py:148-151 (net_worth)",
        "severity": "LOW",
        "title": "holdings_mv is poisoned with NaN but never read",
        "detail": (
            "net_worth() accumulates holdings_mv and adds float('nan') on a "
            "per-account mismatch, then never reads holdings_mv again; the "
            "reconciles flag is recomputed independently at lines 154-158. "
            "The NaN write is dead code that reads like a real signal."),
        "evidence": "Source inspection: holdings_mv appears only in those two spots.",
        "recommended_fix": (
            "Delete the holdings_mv accumulator, or return it as an explicit "
            "holdings_market_value field so callers can see the gap."),
    },
    {
        "finding_id": "W8-F3",
        "module": "tools/fis/twin_scenarios.py",
        "location": "twin_scenarios.py:104-121 (_goal_probability)",
        "severity": "MEDIUM",
        "title": "Broad 'except Exception' silently swaps the model",
        "detail": (
            "If calcs_household.goal_funding_probability raises for any "
            "reason, the function falls back to a crude expected-value ratio "
            "and returns it with no marker distinguishing it from the Monte "
            "Carlo result. A caller cannot tell a 10,000-path probability "
            "from a deterministic ratio."),
        "evidence": (
            "The fallback branch returns a bare float; the result dict has no "
            "model_id or method field."),
        "recommended_fix": (
            "Return {'probability': ..., 'method': 'monte-carlo'|'ev-ratio', "
            "'paths': n} or let the exception propagate. Never downgrade the "
            "model silently."),
    },
    {
        "finding_id": "W8-F4",
        "module": "tools/fis/risk_engine.py",
        "location": "risk_engine.py:53 (_disclosure)",
        "severity": "MEDIUM",
        "title": "Every risk result carries a wall-clock staleness stamp",
        "detail": (
            "_disclosure() sets 'staleness': date.today().isoformat(). Any "
            "result dict is therefore non-reproducible across days, and "
            "golden-file comparison of risk output is impossible without "
            "stripping the field."),
        "evidence": "risk_engine.py:53.",
        "recommended_fix": (
            "Take as_of as a required parameter (as_of=None raising is "
            "acceptable under this module's fail-closed policy) rather than "
            "reading date.today()."),
    },
]


# ===========================================================================
# Exceptions
# ===========================================================================

class SkipStage(Exception):
    """Raised inside a stage: recorded as SKIPPED-NOT-APPLICABLE."""


class BlockStage(Exception):
    """Raised inside a stage: recorded as BLOCKED (safe degraded mode)."""


class StaleOutputError(Exception):
    """Reading a stale output for current use."""


class ApprovalRequiredError(Exception):
    """Attempted to execute a financial action without recorded approval."""


# ===========================================================================
# Small utilities
# ===========================================================================

def ascii_safe(obj):
    """Recursively coerce to JSON-writable, ASCII-only, non-NaN values."""
    if obj is None or isinstance(obj, bool):
        return obj
    if isinstance(obj, int):
        return obj
    if isinstance(obj, float):
        if obj != obj or obj in (float("inf"), float("-inf")):
            return "NON-FINITE"
        return obj
    if isinstance(obj, str):
        return "".join(ch if 32 <= ord(ch) < 127 else "?" for ch in obj)
    if isinstance(obj, dict):
        return {ascii_safe(k): ascii_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [ascii_safe(v) for v in obj]
    return ascii_safe(str(obj))


def money(x):
    return round(float(x) + 0.0, 2)


def day_number(date_str):
    """Days since SIM_EPOCH; deterministic integer calendar index."""
    d = _dt.date.fromisoformat(date_str)
    e = _dt.date.fromisoformat(SIM_EPOCH)
    return (d - e).days


def days_between(a, b):
    return (_dt.date.fromisoformat(b) - _dt.date.fromisoformat(a)).days


def asset_class_of(symbol):
    return "bonds" if symbol in BOND_SYMBOLS else "equity"


def load_household(name):
    path = os.path.join(FIXTURE_DIR, name + ".json")
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def implied_prices(doc):
    """price per (account_id, symbol), rescaled so accounts reconcile.

    A nominal table gives relative pricing; each account's holdings are then
    scaled by (stated balance / nominal market value) so the derived portfolio
    ties to the twin document. Accounts with no stated balance use nominal.
    """
    table = {}
    for acct in doc.get("accounts") or []:
        hs = acct.get("holdings") or []
        if not hs:
            continue
        nominal = sum(
            float(h.get("qty", 0.0)) * NOMINAL_PRICES.get(h.get("symbol"), 0.0)
            for h in hs)
        bal = acct.get("balance", None)
        for h in hs:
            sym = h.get("symbol")
            nominal_px = NOMINAL_PRICES.get(sym, 100.0)
            if nominal > 0 and bal is not None:
                px = nominal_px * (float(bal) / nominal)
            else:
                px = nominal_px
            table["%s|%s" % (acct.get("id", "?"), sym)] = round(px, 6)
    return table


def portfolio_from_twin(doc, prices, effective, taxable_only=False):
    """Build a portfolio_engine-shaped portfolio from a validated twin."""
    cash = 0.0
    holdings = []
    for acct in doc.get("accounts") or []:
        typ = acct.get("type")
        bal = float(acct.get("balance", 0.0) or 0.0)
        if typ == "cash":
            cash += bal
            continue
        if taxable_only and typ not in TAXABLE_ACCOUNT_TYPES:
            continue
        for h in acct.get("holdings") or []:
            sym = h.get("symbol")
            key = "%s|%s" % (acct.get("id", "?"), sym)
            px = prices.get(key) or NOMINAL_PRICES.get(sym, 100.0)
            qty = float(h.get("qty", 0.0))
            if qty <= 0:
                continue
            lots = []
            for i, lot in enumerate(h.get("tax_lots") or []):
                lq = float(lot.get("qty", 0.0))
                if lq <= 0:
                    continue
                cb_total = float(lot.get("cost_basis", 0.0))
                acq = lot.get("acq_date", effective)
                lots.append({
                    "lot_id": "%s|%s|L%03d" % (acct.get("id", "?"), sym, i),
                    "quantity": lq,
                    "cost_basis": round(cb_total / lq, 6),
                    "acquire_date": acq,
                    "term": "long" if days_between(acq, effective) >= 366 else "short",
                })
            if not lots:
                lots = [{
                    "lot_id": "%s|%s|IMPLICIT" % (acct.get("id", "?"), sym),
                    "quantity": qty,
                    "cost_basis": px,
                    "acquire_date": effective,
                    "term": "long",
                }]
            holdings.append({
                "ticker": "%s@%s" % (sym, acct.get("id", "?")),
                "security_symbol": sym,
                "issuer": sym,
                "asset_class": asset_class_of(sym),
                "account": acct.get("id", "?"),
                "quantity": qty,
                "price": px,
                "lots": lots,
            })
    holdings.sort(key=lambda h: h["ticker"])
    return {"cash": round(cash, 2), "holdings": holdings}


def lots_to_taxlot_portfolio(holdings, effective):
    """calcs_household.Portfolio for taxlot_ext, from portfolio holdings."""
    pf = calcs_household.Portfolio()
    for h in holdings:
        for lot in h["lots"]:
            pf.add_lot(calcs_household.Lot(
                lot_id=lot["lot_id"],
                acquire_date=lot["acquire_date"],
                shares=float(lot["quantity"]),
                cost_per_share_cents=int(round(lot["cost_basis"] * 100.0)),
                acquire_day=day_number(lot["acquire_date"]),
            ))
    return pf


def prices_by_lot_id(portfolio):
    """lot_id -> current price per share (dollars)."""
    out = {}
    for h in portfolio["holdings"]:
        for lot in h["lots"]:
            out[lot["lot_id"]] = float(h["price"])
    return out


def policy_for(doc, overrides=None):
    """Deterministic rebalance policy derived from document constraints."""
    cons = doc.get("constraints") or {}
    rt = cons.get("risk_tolerance") or {}
    level = str(rt.get("level", "moderate"))
    targets = dict(TARGETS_BY_LEVEL.get(level, TARGETS_BY_LEVEL["moderate"]))
    bands = {
        "equity": {"low": 0.05, "high": 0.05},
        "bonds": {"low": 0.05, "high": 0.05},
        "cash": {"low": 0.03, "high": 0.05},
    }
    total = sum(float(a.get("balance", 0.0) or 0.0)
                for a in doc.get("accounts") or [])
    floor = float(cons.get("liquidity_floor", 0.0) or 0.0)
    min_cash_pct = 5.0
    if total > 0:
        min_cash_pct = min(5.0, round(floor / total * 100.0, 3))
    issuer_cap = 15.0 if level in ("conservative", "moderately_conservative") else 25.0
    policy = {
        "targets": targets,
        "bands": bands,
        "constraints": {
            "max_single_issuer_pct": issuer_cap,
            "min_cash_pct": min_cash_pct,
            "max_turnover_pct": 20.0,
        },
        "tax_rates": {"long": 0.15, "short": 0.24},
        "level": level,
    }
    if overrides:
        for k, v in overrides.items():
            if isinstance(v, dict) and isinstance(policy.get(k), dict):
                policy[k].update(v)
            else:
                policy[k] = v
    return policy


def class_weights(portfolio):
    total = portfolio_engine._total_value(portfolio)
    acc = {}
    for h in portfolio["holdings"]:
        acc[h["asset_class"]] = (acc.get(h["asset_class"], 0.0)
                                 + portfolio_engine._holding_value(h))
    acc["cash"] = acc.get("cash", 0.0) + float(portfolio.get("cash", 0.0))
    if total <= 0:
        return {}, 0.0
    return {k: v / total for k, v in sorted(acc.items())}, total


def active_share(weights, targets):
    """Sum of |weight - target| across every targeted class."""
    total = 0.0
    for cls, tgt in sorted(targets.items()):
        total += abs(float(weights.get(cls, 0.0)) - float(tgt))
    return round(total, 8)


def mc_terminal_distribution(seed, start, mu, sigma, years, paths=2000):
    """Deterministic seeded terminal-wealth distribution."""
    rng = random.Random(seed)
    finals = []
    for _ in range(paths):
        b = float(start)
        for _y in range(max(int(years), 1)):
            b = b * (1.0 + rng.gauss(mu, sigma))
            if b < 0.0:
                b = 0.0
        finals.append(b)
    finals.sort()

    def q(p):
        i = min(int(p * (len(finals) - 1)), len(finals) - 1)
        return round(finals[i], 2)

    return {"p10": q(0.10), "p50": q(0.50), "p90": q(0.90),
            "paths": paths, "seed": int(seed), "years": int(years)}


# ===========================================================================
# Infrastructure: temporal store, stale registry, approval gate, audit log
# ===========================================================================

class TemporalStore(object):
    """Records keyed by (entity, effective_date, known_at, recorded_at).

    effective_date - when the fact is true in the world
    known_at       - when the system learned it
    recorded_at    - fixed simulation clock write stamp

    A later restatement of the same (entity, effective_date) supersedes the
    earlier row for *future* knowledge queries but never rewrites history:
    querying at an earlier known_at still returns the superseded row.
    """

    def __init__(self, clock):
        self.clock = clock
        self._rows = []
        self._seq = 0

    def put(self, entity, value, effective, known_at, source="twin-doc"):
        self._seq += 1
        for r in self._rows:
            if (r["entity"] == entity and r["effective_date"] == effective
                    and not r["superseded"] and r["known_at"] <= known_at):
                r["superseded"] = True
        row = {
            "seq": self._seq,
            "entity": entity,
            "value": value,
            "effective_date": effective,
            "known_at": known_at,
            "recorded_at": self.clock,
            "source": source,
            "superseded": False,
        }
        self._rows.append(row)
        return row

    def as_of(self, entity, effective, known_at):
        """Row visible for (entity) as known at known_at for effective date."""
        best = None
        for r in self._rows:
            if r["entity"] != entity:
                continue
            if r["effective_date"] > effective:
                continue
            if r["known_at"] > known_at:
                continue
            if best is None or (r["known_at"], r["seq"]) > (best["known_at"], best["seq"]):
                best = r
        return best

    def value_as_of(self, entity, effective, known_at, default=None):
        row = self.as_of(entity, effective, known_at)
        return default if row is None else row["value"]

    def rows(self, entity=None):
        return [r for r in self._rows if entity is None or r["entity"] == entity]

    def entities(self):
        return sorted({r["entity"] for r in self._rows})


class StaleRegistry(object):
    """Published outputs, each bound to a provenance artifact.

    Staleness is decided by the provenance graph, not by a local boolean: an
    output is stale when any node in its transitive input closure was
    re-registered with different content since the output was computed.
    """

    def __init__(self, graph):
        self.graph = graph
        self._pubs = {}

    def publish(self, output_id, artifact_id, value, note=""):
        self._pubs[output_id] = {
            "output_id": output_id,
            "artifact_id": artifact_id,
            "value": value,
            "note": note,
        }
        return self._pubs[output_id]

    def ids(self):
        return sorted(self._pubs)

    def explain(self, output_id):
        pub = self._pubs[output_id]
        return pub, self.graph.explain(pub["artifact_id"])

    def is_stale(self, output_id):
        _pub, exp = self.explain(output_id)
        return (not exp["fresh"]), exp

    def read(self, output_id):
        """Current-use read. Raises StaleOutputError when the output is stale."""
        pub, exp = self.explain(output_id)
        if not exp["fresh"]:
            reasons = "; ".join(
                "%s: %s" % (k, v) for k, v in sorted(exp["reasons"].items()))
            raise StaleOutputError(
                "output %r (artifact %r) is STALE and blocked for current "
                "use: %s" % (output_id, pub["artifact_id"], reasons))
        return pub["value"]

    def marker(self, output_id):
        """Non-raising read returning an explicit blocked marker when stale."""
        pub, exp = self.explain(output_id)
        if not exp["fresh"]:
            return {
                "status": "BLOCKED-STALE",
                "output_id": output_id,
                "artifact_id": pub["artifact_id"],
                "stale_nodes": list(exp["stale"]),
                "reasons": dict(exp["reasons"]),
                "value": None,
            }
        return {"status": "OK", "output_id": output_id,
                "artifact_id": pub["artifact_id"], "value": pub["value"]}


class DegradedMode(object):
    """Safe degraded mode for adversarial scenarios (12-15)."""

    def __init__(self):
        self.active = False
        self.reasons = []
        self.disclosures = []
        self.blocked = set()

    def engage(self, reason, disclosure, blocked=()):
        self.active = True
        self.reasons.append(reason)
        if disclosure:
            self.disclosures.append(disclosure)
        self.blocked.update(blocked)
        return self

    def blocks(self, capability):
        return capability in self.blocked

    def as_dict(self):
        return {
            "active": self.active,
            "reasons": list(self.reasons),
            "disclosures": list(self.disclosures),
            "blocked_capabilities": sorted(self.blocked),
        }


class ApprovalGate(object):
    """Approval enforcement. Nothing executes inside the harness, ever."""

    def __init__(self):
        self.state = GATE_PENDING
        self.decision_id = None
        self.approvals = []
        self.executed_actions = []
        self.refusals = []

    def submit(self, decision):
        self.decision_id = decision["decision_id"]
        sel = decision.get("selected_alternative_id")
        consequential = bool(decision.get("selected_is_consequential"))
        if decision.get("degraded"):
            self.state = GATE_DEGRADED
        elif sel == NO_ACTION_ID or not consequential:
            self.state = GATE_NO_ACTION
        else:
            self.state = GATE_AWAITING
        return self.state

    def execute(self, action):
        """Would place a real order. Refuses unless approval is recorded.

        The harness never records an approval, so this always raises. That is
        the point: the refusal is the assertion.
        """
        refusal = {
            "action": ascii_safe(action),
            "blocked_by": "APPROVAL_REQUIRED",
            "gate_state": self.state,
            "approvals_on_file": len(self.approvals),
        }
        self.refusals.append(refusal)
        raise ApprovalRequiredError(
            "execution refused: no recorded human approval (gate state %s)"
            % self.state)

    def as_dict(self):
        return {
            "state": self.state,
            "decision_id": self.decision_id,
            "approvals_on_file": len(self.approvals),
            "executed_actions": list(self.executed_actions),
            "refusals": list(self.refusals),
        }


class AuditLog(object):
    """Hash-chained audit log verified with shadow.verify_chain."""

    def __init__(self, path, run_id, clock):
        self.path = path
        self.run_id = run_id
        self.clock = clock
        self.records = []
        if os.path.exists(path):
            os.remove(path)

    def _flush(self, rec):
        with open(self.path, "a", encoding="ascii") as fh:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")

    def append(self, event_type, payload=None):
        prev = self.records[-1]["record_hash"] if self.records else "GENESIS"
        rec = {
            "seq": len(self.records) + 1,
            "run_id": self.run_id,
            "clock": self.clock,
            "event_type": ascii_safe(event_type),
            "payload": ascii_safe(payload or {}),
            "prev_record_hash": prev,
        }
        rec["record_hash"] = shadow.record_hash(rec)
        self.records.append(rec)
        self._flush(rec)
        return rec

    def verify(self):
        return shadow.verify_chain(self.records)

    def verify_on_disk(self):
        recs = []
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="ascii") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        recs.append(json.loads(line))
        return shadow.verify_chain(recs), len(recs)


# ===========================================================================
# Pipeline runner
# ===========================================================================

class ScenarioRunner(object):
    """Runs one scenario through the fixed 18-stage pipeline."""

    def __init__(self, sid, title, household, seed, objective, out_dir=OUT_DIR):
        self.sid = sid
        self.title = title
        self.household = household
        self.seed = int(seed)
        self.objective = dict(objective)
        self.out_dir = out_dir
        self.clock = SIM_CLOCK
        self.effective = SIM_EFFECTIVE
        self.known_pre = SIM_KNOWN_PRE
        self.known_post = SIM_KNOWN_POST
        self.rng = random.Random(self.seed)
        # Observations recorded mid-stage (e.g. a verified fail-closed
        # refusal) that the artifact should surface, not swallow.
        self.notes = []

        os.makedirs(STATE_DIR, exist_ok=True)
        self.state_prefix = os.path.join(STATE_DIR, sid)
        self.prov_path = self.state_prefix + "-provenance-store.json"
        self.marks_path = self.state_prefix + "-stale-events.jsonl"
        self.obs_path = self.state_prefix + "-obs-events.jsonl"
        self.audit_path = self.state_prefix + "-audit.jsonl"
        for p in (self.prov_path, self.marks_path, self.obs_path):
            if os.path.exists(p):
                os.remove(p)

        self.graph = provenance.ProvenanceGraph(store_path=self.prov_path)
        self.temporal = TemporalStore(self.clock)
        self.outputs = StaleRegistry(self.graph)
        self.audit = AuditLog(self.audit_path, sid, self.clock)
        self.gate = ApprovalGate()
        self.degraded = DegradedMode()

        self.correlation_id = "corr:%s" % sid
        self.dataset_version = "synthetic-households/%s" % household
        self.events = []
        self.obs_events = []
        self.stages = {}
        self.order = []
        self.ctx = {}
        self.findings = []
        self.base_doc = None
        self.post_doc = None
        self.ecm = portfolio_engine._load_ecm()

    # -- observability ----------------------------------------------------

    def emit(self, event_type, payload=None, error_class=None):
        rec = obs.emit_event(
            event_type,
            payload=ascii_safe(payload or {}),
            run_id=self.sid,
            correlation_id=self.correlation_id,
            causation_id=self.events[-1]["event_id"] if self.events else None,
            dataset_version=self.dataset_version,
            error_class=error_class,
            event_log_path=self.obs_path,
        )
        self.obs_events.append(event_type)
        return rec

    # -- stage driver -----------------------------------------------------

    def stage(self, name, fn):
        if name not in STAGES:
            raise ValueError("unknown stage %r" % name)
        if name in self.stages:
            raise RuntimeError("stage %s executed twice" % name)
        try:
            out = fn()
            if out is None:
                detail, summary = {}, "ok"
            elif isinstance(out, dict):
                detail, summary = out, str(out.get("summary", "ok"))
            else:
                detail, summary = {"value": out}, str(out)
            status, reason = S_EXECUTED, ""
        except SkipStage as exc:
            detail, summary, status, reason = {}, str(exc), S_SKIPPED, str(exc)
            out = None
        except BlockStage as exc:
            detail, summary, status, reason = {}, str(exc), S_BLOCKED, str(exc)
            out = None
        except Exception as exc:                       # fail closed
            detail = {
                "exception": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(limit=8),
            }
            summary = "FAILED: %s" % exc
            status, reason = S_FAILED, "%s: %s" % (type(exc).__name__, exc)
            out = None
        rec = {
            "index": STAGES.index(name) + 1,
            "stage": name,
            "status": status,
            "reason": ascii_safe(reason),
            "summary": ascii_safe(summary)[:400],
            "detail": ascii_safe(detail),
        }
        self.stages[name] = rec
        self.order.append(name)
        self.audit.append("stage.%s" % name,
                          {"status": status, "summary": rec["summary"]})
        return out

    def stage_status(self, name):
        return self.stages.get(name, {}).get("status")

    # -- finalisation -----------------------------------------------------

    def finish(self, outcome, extra=None):
        for name in STAGES:
            if name not in self.stages:
                self.stages[name] = {
                    "index": STAGES.index(name) + 1,
                    "stage": name,
                    "status": S_FAILED,
                    "reason": "stage never reached (scenario terminated early)",
                    "summary": "",
                    "detail": {},
                }
        ordered = [self.stages[n] for n in STAGES]
        counts = {}
        for rec in ordered:
            counts[rec["status"]] = counts.get(rec["status"], 0) + 1

        body = {
            "scenario_id": self.sid,
            "title": self.title,
            "harness": {"id": HARNESS_ID, "version": HARNESS_VERSION},
            "data_classification": DATA_CLASSIFICATION,
            "synthetic": True,
            "synthetic_notice": (
                "Every member, employer, custodian, symbol, balance, rate and "
                "date in this artifact is invented for testing. No real "
                "person, account or market data is present."),
            "seed": self.seed,
            "sim_clock": self.clock,
            "sim_effective_date": self.effective,
            "sim_known_at_pre": self.known_pre,
            "sim_known_at_post": self.known_post,
            "household_fixture": self.household,
            "objective": ascii_safe(self.objective),
            "objective_assumptions": {
                "rebalance_premium": REBALANCE_PREMIUM,
                "liquidity_penalty_rate": LIQUIDITY_PENALTY_RATE,
                "note": (
                    "objective_usd = rebalance_premium * notional_moved_toward"
                    "_target - tax_usd - fee_usd - liquidity_penalty_rate * "
                    "cash_below_floor. Both constants are parameters, not "
                    "evidence; the skeptical review challenges them."),
            },
            "event": ascii_safe(self.events[0] if self.events else None),
            "event_count": len(self.events),
            "stages": ordered,
            "stage_counts": counts,
            "terminal_stage": {
                "name": STAGES[-1],
                "status": self.stages[STAGES[-1]]["status"],
            },
            "terminal_state": self.gate.state,
            "degraded_mode": self.degraded.as_dict(),
            "approval_gate": self.gate.as_dict(),
            "executed_financial_action": len(self.gate.executed_actions) > 0,
            "alternatives": ascii_safe(self.ctx.get("alternatives", [])),
            "alternative_ids": [a["alternative_id"]
                                for a in self.ctx.get("alternatives", [])],
            "no_action_present": any(
                a["alternative_id"] == NO_ACTION_ID
                for a in self.ctx.get("alternatives", [])),
            "selected_alternative_id": self.ctx.get("selected_alternative_id"),
            "decision": ascii_safe(self.ctx.get("decision")),
            "skeptical_review": ascii_safe(self.ctx.get("skeptical_review")),
            "effects": ascii_safe({
                "portfolio": self.ctx.get("portfolio_effect"),
                "tax": self.ctx.get("tax_effect"),
                "liquidity": self.ctx.get("liquidity_effect"),
                "risk": self.ctx.get("risk_effect"),
                "goal": self.ctx.get("goal_effect"),
            }),
            "audit": {
                "records": len(self.audit.records),
                "chain_ok": bool(self.audit.verify()[0]),
                "head": self.audit.records[-1]["record_hash"] if self.audit.records else None,
                "path": os.path.relpath(self.audit_path, REPO_ROOT).replace("\\", "/"),
            },
            "observability_events": list(self.obs_events),
            "blocking_finding_ids": [f["finding_id"] for f in self.findings],
            "outcome": ascii_safe(outcome),
        }
        if extra:
            body.update(ascii_safe(extra))
        body["determinism_digest"] = shadow.canonical_sha256(
            json.dumps(body, sort_keys=True))[:32]
        self.artifact = body
        path = os.path.join(self.out_dir, "%s.json" % self.sid)
        with open(path, "w", encoding="ascii") as fh:
            json.dump(body, fh, indent=2, sort_keys=True)
            fh.write("\n")
        self.artifact_path = path
        return body


# ===========================================================================
# Stage helpers (shared by every scenario)
# ===========================================================================

def stage_ingest(rc, event_type, payload, source,
                 effective=SIM_EFFECTIVE, known_at=SIM_KNOWN_POST,
                 severity="normal"):
    def _run():
        raw = {
            "event_type": event_type,
            "source": source,
            "effective_date": effective,
            "known_at": known_at,
            "recorded_at": rc.clock,
            "severity": severity,
            "scenario_id": rc.sid,
            "payload": ascii_safe(payload),
        }
        raw["event_id"] = "evt:%s:%s" % (
            rc.sid, shadow.canonical_sha256(raw)[:12])
        rc.events.append(raw)
        rc.emit("scenario.event.ingested",
                {"event_id": raw["event_id"], "event_type": event_type,
                 "source": source, "severity": severity,
                 "effective_date": effective, "known_at": known_at})
        return {
            "value": raw,
            "summary": "ingested %s from %s (effective %s, known-at %s, "
                       "severity %s)" % (event_type, source, effective,
                                         known_at, severity),
            "event_id": raw["event_id"],
        }
    return rc.stage("EVENT_INGESTION", _run)


def stage_validate(rc, doc, label):
    def _run():
        errors = twin_schema.validate_twin(doc)
        if errors:
            raise BlockStage(
                "twin document %s rejected: %d schema error(s): %s"
                % (label, len(errors), "; ".join(errors[:3])))
        return {"value": doc, "summary": "validate_twin clean on %s" % label,
                "errors": 0}
    return rc.stage("VALIDATION", _run)


def baseline_facts(rc, doc):
    return [
        ("fact:household:%s" % rc.household,
         shadow.canonical_sha256(doc)),
        ("fact:policy:%s" % rc.sid,
         shadow.canonical_sha256(policy_for(doc))),
        ("fact:prices:%s" % rc.sid,
         shadow.canonical_sha256(implied_prices(doc))),
    ]


def stage_provenance(rc, doc):
    """Register base facts and the PRE-event output chain."""
    def _run():
        facts = baseline_facts(rc, doc)
        for fid, content in facts:
            rc.graph.register_fact(fid, content)

        nw_pre = twin_identity.net_worth(doc)
        prices = implied_prices(doc)
        pf_pre = portfolio_from_twin(doc, prices, rc.effective)
        w_pre, v_pre = class_weights(pf_pre)
        risk_pre = risk_engine.household_risk(
            twin_scenarios.liquidity_months(doc)["months_of_cover"],
            twin_scenarios.liquidity_months(doc)["monthly_spend"])

        chain = [
            ("artifact:nw:baseline", ["fact:household:%s" % rc.household],
             "nw=%.2f" % nw_pre, {"code": "twin_identity.net_worth"}),
            ("artifact:weights:baseline",
             ["fact:household:%s" % rc.household, "fact:prices:%s" % rc.sid],
             shadow.canonical_sha256(w_pre), {"code": "scenarios_e2e.class_weights"}),
            ("artifact:risk:baseline",
             ["artifact:nw:baseline", "fact:prices:%s" % rc.sid],
             shadow.canonical_sha256(risk_pre), {"code": "risk_engine.household_risk"}),
            ("artifact:goal:baseline",
             ["artifact:nw:baseline", "artifact:weights:baseline"],
             "goal-baseline-v1", {"code": "calcs_household.goal_funding_probability"}),
        ]
        for aid, inputs, content, params in chain:
            rc.graph.record_artifact(
                aid, inputs,
                script_path="tools/fis/scenarios_e2e.py",
                code_version=HARNESS_VERSION,
                content=content, params=params)

        rc.outputs.publish("OUT:NET_WORTH", "artifact:nw:baseline",
                           nw_pre, "pre-event household net worth")
        rc.outputs.publish("OUT:WEIGHTS", "artifact:weights:baseline",
                           w_pre, "pre-event class weights")
        rc.outputs.publish("OUT:RISK", "artifact:risk:baseline",
                           risk_pre["breach_probability_label"],
                           "pre-event liquidity breach label")
        rc.outputs.publish("OUT:GOAL", "artifact:goal:baseline",
                           "goal-baseline-v1", "pre-event goal funding pack")

        fresh = {oid: rc.outputs.is_stale(oid)[0] for oid in rc.outputs.ids()}
        if any(fresh.values()):
            raise BlockStage("baseline outputs published stale: %s"
                             % [k for k, v in fresh.items() if v])
        return {
            "summary": "registered %d facts and %d artifacts; published %d "
                       "outputs, all fresh" % (len(facts), len(chain),
                                               len(rc.outputs.ids())),
            "facts": [f[0] for f in facts],
            "artifacts": [c[0] for c in chain],
            "outputs": rc.outputs.ids(),
            "edges": [list(e) for e in rc.graph.edges()],
            "pre_net_worth": money(nw_pre),
            "pre_value": money(v_pre),
        }
    return rc.stage("PROVENANCE_REGISTRATION", _run)


def stage_temporal(rc, doc):
    """Store pre-event state with effective / known-at / recorded stamps."""
    def _run():
        rows = []
        for acct in doc.get("accounts") or []:
            rows.append(rc.temporal.put(
                "account:%s:balance" % acct.get("id"),
                float(acct.get("balance", 0.0) or 0.0),
                rc.effective, rc.known_pre, source="twin-doc"))
        for mem in doc.get("members") or []:
            emp = mem.get("employment") or {}
            rows.append(rc.temporal.put(
                "member:%s:employment_status" % mem.get("id"),
                str(emp.get("status", "unknown")),
                rc.effective, rc.known_pre, source="twin-doc"))
        for goal in doc.get("goals") or []:
            rows.append(rc.temporal.put(
                "goal:%s:priority" % goal.get("id"),
                str(goal.get("priority", "unknown")),
                rc.effective, rc.known_pre, source="twin-doc"))
        for liab_i, liab in enumerate(doc.get("liabilities") or []):
            rows.append(rc.temporal.put(
                "liability:%d:rate" % liab_i,
                float(liab.get("rate", 0.0) or 0.0),
                rc.effective, rc.known_pre, source="twin-doc"))

        first = rows[0]["entity"]
        probe_now = rc.temporal.as_of(first, rc.effective, rc.known_pre)
        probe_early = rc.temporal.as_of(first, "2001-01-01", rc.known_pre)
        probe_unknown = rc.temporal.as_of(first, rc.effective, "2001-01-01")
        stamped = all(r["recorded_at"] == rc.clock for r in rows)
        if probe_now is None:
            raise BlockStage("temporal read at known-at %s returned nothing"
                             % rc.known_pre)
        if probe_early is not None:
            raise BlockStage("effective-date filter failed: a row effective "
                             "%s answered a 2001-01-01 query" % rc.effective)
        if probe_unknown is not None:
            raise BlockStage("known-at filter failed: a row known at %s "
                             "answered a 2001-01-01 query" % rc.known_pre)
        if not stamped:
            raise BlockStage("recorded_at not stamped from the fixed sim clock")
        return {
            "summary": "stored %d pre-event rows at known-at %s; effective- and "
                       "known-at filters verified" % (len(rows), rc.known_pre),
            "entities": rc.temporal.entities(),
            "row_count": len(rows),
        }
    return rc.stage("TEMPORAL_STORAGE", _run)


def stage_dependency_propagation(rc, fact_id, new_content):
    def _run():
        affected, marks = provenance.invalidate_and_propagate(
            rc.graph, fact_id, new_content, marks_path=rc.marks_path)
        if not affected:
            raise BlockStage(
                "dependency propagation reached no downstream artifact from "
                "%s -- lineage is not wired" % fact_id)
        rc.emit("provenance.invalidated",
                {"fact": fact_id, "affected": affected, "marks": len(marks)})
        return {
            "summary": "re-registered %s; propagation marked %d downstream "
                       "artifact(s) and emitted %d stale-event(s)"
                       % (fact_id, len(affected), len(marks)),
            "changed_fact": fact_id,
            "affected": affected,
            "marks": len(marks),
        }
    return rc.stage("DEPENDENCY_PROPAGATION", _run)


def stage_stale_invalidation(rc, output_ids):
    def _run():
        results = {}
        for oid in output_ids:
            pub, exp = rc.outputs.explain(oid)
            stale = not exp["fresh"]
            raised = False
            msg = ""
            try:
                rc.outputs.read(oid)
            except StaleOutputError as exc:
                raised = True
                msg = str(exc)
            marker = rc.outputs.marker(oid)
            results[oid] = {
                "artifact_id": pub["artifact_id"],
                "stale": stale,
                "read_raises_stale_output_error": raised,
                "marker_status": marker["status"],
                "stale_nodes": list(exp["stale"]),
                "reason_sample": msg[:200],
            }
        missing = [o for o, r in results.items() if not r["stale"]]
        unraised = [o for o, r in results.items()
                    if r["stale"] and not r["read_raises_stale_output_error"]]
        unmarked = [o for o, r in results.items()
                    if r["stale"] and r["marker_status"] != "BLOCKED-STALE"]
        if unraised:
            raise BlockStage(
                "stale outputs readable without raising: %s" % unraised)
        if unmarked:
            raise BlockStage(
                "stale outputs not returning BLOCKED-STALE marker: %s" % unmarked)
        if len(missing) == len(output_ids):
            raise BlockStage("no published output was invalidated; "
                             "upstream change did not propagate")
        return {
            "summary": "%d/%d published outputs invalidated; stale reads raise "
                       "StaleOutputError and the marker read returns "
                       "BLOCKED-STALE" % (len(output_ids) - len(missing),
                                          len(output_ids)),
            "outputs": results,
            "not_invalidated": missing,
        }
    return rc.stage("STALE_OUTPUT_INVALIDATION", _run)


def stage_twin_update(rc, doc, new_doc, label, transition=None,
                      changed_entities=None):
    def _run():
        errors = twin_schema.validate_twin(new_doc)
        if errors:
            raise BlockStage(
                "post-transition document rejected: %d error(s): %s"
                % (len(errors), "; ".join(errors[:3])))
        nw_before = twin_identity.net_worth(doc)
        nw_after = twin_identity.net_worth(new_doc)
        liq_before = twin_identity.household_liquidity(doc)
        liq_after = twin_identity.household_liquidity(new_doc)

        # Temporal: re-stamp every entity the transition touched, at the new
        # knowledge date. History at the earlier known_at is preserved.
        restamped = []
        for acct in new_doc.get("accounts") or []:
            ent = "account:%s:balance" % acct.get("id")
            if rc.temporal.as_of(ent, rc.effective, rc.known_pre) is None:
                continue
            restamped.append(rc.temporal.put(
                ent, float(acct.get("balance", 0.0) or 0.0),
                rc.effective, rc.known_post, source="twin-transition"))
        for mem in new_doc.get("members") or []:
            ent = "member:%s:employment_status" % mem.get("id")
            if rc.temporal.as_of(ent, rc.effective, rc.known_pre) is None:
                continue
            restamped.append(rc.temporal.put(
                ent, str((mem.get("employment") or {}).get("status", "unknown")),
                rc.effective, rc.known_post, source="twin-transition"))
        for goal in new_doc.get("goals") or []:
            ent = "goal:%s:priority" % goal.get("id")
            if rc.temporal.as_of(ent, rc.effective, rc.known_pre) is None:
                continue
            restamped.append(rc.temporal.put(
                ent, str(goal.get("priority", "unknown")),
                rc.effective, rc.known_post, source="twin-transition"))

        # Bitemporal proof: pre-knowledge read still sees the OLD value.
        diverged = []
        for row in restamped:
            old = rc.temporal.as_of(row["entity"], rc.effective, rc.known_pre)
            new = rc.temporal.as_of(row["entity"], rc.effective, rc.known_post)
            if old is not None and new is not None and old["value"] != new["value"]:
                diverged.append({"entity": row["entity"],
                                 "known_pre": old["value"],
                                 "known_post": new["value"]})

        rc.post_doc = new_doc
        rc.emit("twin.updated",
                {"transition": label, "net_worth_delta": money(nw_after - nw_before),
                 "liquidity_delta": money(liq_after - liq_before)})
        return {
            "value": new_doc,
            "summary": "%s applied; net worth %.2f -> %.2f, liquidity %.2f -> "
                       "%.2f; %d temporal rows restated"
                       % (label, nw_before, nw_after, liq_before, liq_after,
                          len(restamped)),
            "transition": label,
            "audit_event": ascii_safe(transition),
            "net_worth_before": money(nw_before),
            "net_worth_after": money(nw_after),
            "liquidity_before": money(liq_before),
            "liquidity_after": money(liq_after),
            "temporal_rows_restated": len(restamped),
            "bitemporal_divergence": diverged,
            "changed_entities": ascii_safe(changed_entities or []),
        }
    return rc.stage("DIGITAL_TWIN_UPDATE", _run)


def stage_portfolio_effect(rc, doc, policy, portfolio=None):
    def _run():
        if rc.degraded.blocks("PORTFOLIO_EFFECT"):
            raise BlockStage("portfolio effect blocked: " +
                             "; ".join(rc.degraded.reasons))
        prices = implied_prices(doc)
        pf = portfolio if portfolio is not None else \
            portfolio_from_twin(doc, prices, rc.effective)
        w_pre, v_pre = class_weights(pf)
        drift_pre = active_share(w_pre, policy["targets"])

        plan = portfolio_engine.propose_rebalance(
            pf, policy["targets"], policy["bands"], policy["constraints"],
            ecm=rc.ecm, tax_rates=policy["tax_rates"])
        recalc = None
        if plan["action"] is not None:
            portfolio_engine.independent_recalculation(plan, pf, ecm=rc.ecm)
            recalc = "independent_recalculation matched the planner"

        act = plan["action"] or plan["no_action"]
        m_act = act["metrics"]
        w_post = m_act["post_class_weights"]
        drift_post = active_share(w_post, policy["targets"])

        effect = {
            "status": plan["status"],
            "pre_value": money(v_pre),
            "post_value": money(m_act["portfolio_value_usd"]),
            "pre_weights": {k: round(v, 6) for k, v in sorted(w_pre.items())},
            "post_weights": {k: round(v, 6) for k, v in sorted(w_post.items())},
            "drift_before": drift_pre,
            "drift_after": drift_post,
            "trade_count": len(plan["action"]["trades"]) if plan["action"] else 0,
            "turnover_pct": round(m_act["turnover_one_sided_pct"] * 100.0, 4),
            "ecm_cost_usd": money(m_act["ecm_cost_usd"]),
            "realized_tax_usd": money(m_act["realized_gains"]["tax_usd"]),
            "constraint_checks": plan["action"]["constraint_checks"] if plan["action"]
                                 else plan["no_action"]["constraint_checks"],
            "independent_recalculation": recalc,
            "instability": plan["instability"],
            "reasons": plan["reasons"],
        }
        rc.ctx["portfolio_effect"] = effect
        rc.ctx["plan"] = plan
        rc.ctx["portfolio"] = pf
        rc.ctx["policy"] = policy
        rc.ctx["v_pre_usd"] = money(v_pre)
        rc.ctx["prices"] = prices
        rc.ctx["post_cash_usd"] = money(m_act["post_cash_usd"])
        return {
            "value": effect,
            "summary": "rebalance status=%s; %d trade leg(s); drift %.4f -> "
                       "%.4f; tax %.2f; ecm %.2f"
                       % (plan["status"], effect["trade_count"], drift_pre,
                          drift_post, effect["realized_tax_usd"],
                          effect["ecm_cost_usd"]),
            "effect": effect,
        }
    return rc.stage("PORTFOLIO_EFFECT", _run)


def stage_tax_effect(rc, doc, policy, trade_plan=None):
    def _run():
        if rc.degraded.blocks("TAX_EFFECT"):
            raise BlockStage("tax effect blocked: " +
                             "; ".join(rc.degraded.reasons))
        prices = rc.ctx.get("prices") or implied_prices(doc)
        pf = rc.ctx.get("portfolio") or portfolio_from_twin(
            doc, prices, rc.effective)
        taxable = portfolio_from_twin(doc, prices, rc.effective, taxable_only=True)
        taxable_lp = lots_to_taxlot_portfolio(taxable["holdings"], rc.effective)

        harvest = []
        wash_results = []
        wash_report = {"definitive": False, "flag_count": 0}
        rebal_cost = None
        if taxable_lp.lots:
            lot_px = prices_by_lot_id(taxable)
            harvest = taxlot_ext.tax_loss_harvest_candidates(
                taxable_lp, lot_px, min_loss_cents=25000,
                as_of_day=day_number(rc.effective))
            wash_report = taxlot_ext.wash_sale_report(wash_results)

        plan = rc.ctx.get("plan")
        sells = []
        if plan is not None and plan.get("action"):
            for tr in plan["action"]["trades"]:
                if tr["side"] == "SELL":
                    sells.append(tr)
        if sells and taxable_lp.lots:
            per_symbol = {}
            for h in taxable["holdings"]:
                per_symbol[h["ticker"]] = h
            trades = []
            for tr in sells:
                h = per_symbol.get(tr["ticker"])
                if h is None:
                    continue
                sub = lots_to_taxlot_portfolio([h], rc.effective)
                trades.append({
                    "portfolio": sub,
                    "shares": float(tr["notional_usd"]) / float(h["price"]),
                    "price_per_share": float(h["price"]),
                    "day": day_number(rc.effective),
                    "date": rc.effective,
                })
            if trades:
                rebal_cost = taxlot_ext.rebalancing_tax_cost(
                    trades,
                    stcg_rate=policy["tax_rates"]["short"],
                    ltcg_rate=policy["tax_rates"]["long"])

        location = taxlot_ext.asset_location()
        total_harvestable = sum(
            c["unrealized_loss_cents"] for c in harvest) / 100.0

        effect = {
            "tlh_candidate_count": len(harvest),
            "tlh_loss_usd": money(total_harvestable),
            "tlh_flagged_wash_window": sum(
                1 for c in harvest if c["wash_sale_window_flag"]),
            "wash_sale_definitive": wash_report["definitive"],
            "wash_sale_scope": wash_report.get("scope"),
            "wash_sale_flags": wash_report["flag_count"],
            "wash_sale_unresolved_caveats": wash_report.get(
                "unresolved_cross_account_caveats", []),
            "rebalancing_tax_cost_usd": (
                money(rebal_cost["total_tax_cents"] / 100.0)
                if rebal_cost and "total_tax_cents" in rebal_cost else None),
            "rebalancing_tax_rule_version": (
                rebal_cost.get("rule_version") if rebal_cost else None),
            "asset_location_label": location["label"],
            "taxable_holding_count": len(taxable["holdings"]),
            "rates_used": dict(policy["tax_rates"]),
        }
        rc.ctx["tax_effect"] = effect
        return {
            "value": effect,
            "summary": "%d TLH candidate(s) worth %.2f USD loss (%d inside a "
                       "wash window); wash-sale scope %s; asset-location label %s"
                       % (effect["tlh_candidate_count"], effect["tlh_loss_usd"],
                          effect["tlh_flagged_wash_window"],
                          effect["wash_sale_scope"],
                          effect["asset_location_label"]),
            "effect": effect,
        }
    return rc.stage("TAX_EFFECT", _run)


def stage_liquidity_effect(rc, doc, cash_delta=0.0, label="scenario cash move"):
    def _run():
        if rc.degraded.blocks("LIQUIDITY_EFFECT"):
            raise BlockStage("liquidity effect blocked: " +
                             "; ".join(rc.degraded.reasons))
        liq = twin_scenarios.liquidity_months(doc)
        floor = float((doc.get("constraints") or {}).get("liquidity_floor", 0.0) or 0.0)
        months = float(liq["months_of_cover"])
        spend = float(liq["monthly_spend"])
        gap = max(0.0, floor - float(liq["cash_total"]))

        ledger = calcs_ledger.DoubleEntryLedger()
        if abs(cash_delta) > 0.005:
            amt = round(abs(float(cash_delta)), 2)
            if cash_delta < 0:
                ledger.post(rc.effective, label,
                            [("cash:household", -amt), ("expense:scenario", amt)])
            else:
                ledger.post(rc.effective, label,
                            [("cash:household", amt), ("income:scenario", -amt)])
        balanced = ledger.trial_balance_total_cents() == 0

        effect = {
            "months_of_cover": round(months, 4),
            "cash_total": money(liq["cash_total"]),
            "monthly_spend": money(spend),
            "liquidity_floor_usd": money(floor),
            "floor_gap_usd": money(gap),
            "below_floor": bool(float(liq["cash_total"]) < floor),
            "cash_delta_usd": money(cash_delta),
            "ledger_entries": len(ledger.entries),
            "ledger_balanced_cents": ledger.trial_balance_total_cents(),
            "ledger_balanced": balanced,
            "data_gaps": liq["data_gaps"],
        }
        if not balanced:
            raise BlockStage("liquidity ledger does not balance: %d cents"
                             % ledger.trial_balance_total_cents())
        rc.ctx["liquidity_effect"] = effect
        rc.ctx["liquidity_floor_usd"] = money(floor)
        rc.ctx["liquidity_months"] = round(months, 4)
        return {
            "value": effect,
            "summary": "cover %.2f months on %.2f cash vs floor %.2f (gap "
                       "%.2f); %d balanced ledger entry(ies)"
                       % (months, effect["cash_total"], floor, gap,
                          effect["ledger_entries"]),
            "effect": effect,
        }
    return rc.stage("LIQUIDITY_EFFECT", _run)


def stage_risk_effect(rc, doc, shock=None, limits=None, portfolio=None):
    def _run():
        if rc.degraded.blocks("RISK_EFFECT"):
            raise BlockStage("risk effect blocked: " +
                             "; ".join(rc.degraded.reasons))
        liq = twin_scenarios.liquidity_months(doc)
        hh = risk_engine.household_risk(liq["months_of_cover"], liq["monthly_spend"])
        rev = risk_engine.reverse_stress(liq["months_of_cover"])

        pf = portfolio if portfolio is not None else rc.ctx.get("portfolio")
        port = None
        if pf is not None and pf["holdings"]:
            w, _v = class_weights(pf)
            names = sorted(w)
            weights = [w[k] for k in names]
            vols = [0.18 if k == "bonds" else 0.16 if k == "cash" else 0.26
                    for k in names]
            pr = risk_engine.portfolio_risk(weights, vols)
            port = {"port_vol": pr["port_vol"],
                    "hhi_concentration": pr["hhi_concentration"],
                    "top_name_share": pr["top_name_share"]}

        stress = None
        if shock is not None:
            stress = risk_engine.hypothetical_shock(
                equity_pct=shock.get("equity_pct", -0.35),
                duration_shock=shock.get("duration_shock", -0.10))

        metrics = {
            "liquidity_months": hh["months_of_cover"],
            "breach_probability_label": hh["breach_probability_label"],
            "buffer_months": hh["buffer_months"],
            "reverse_stress_decline_pct": rev["breaching_decline_pct"],
            "already_breached": rev["already_breached"],
            "port_vol": (port or {}).get("port_vol"),
            "top_name_share": (port or {}).get("top_name_share"),
            "shock_total_pnl_pct": (stress or {}).get("total_pnl"),
        }
        if "model_hit_rate" in rc.ctx:
            metrics["model_hit_rate"] = rc.ctx["model_hit_rate"]
        lim = limits or {"liquidity_months": {"min": 3.0}}
        tripped = risk_engine.kill_switch(metrics, lim)

        effect = dict(metrics)
        effect.update({
            "kill_switch_tripped": bool(tripped),
            "limits": ascii_safe(lim),
            "risk_disclosure_confidence": hh["disclosure"]["confidence"],
            "included_risks": hh["disclosure"]["included_risks"],
            "excluded_risks": hh["disclosure"]["excluded_risks"],
        })
        rc.ctx["risk_effect"] = effect
        return {
            "value": effect,
            "summary": "liquidity label %s (%.2f mo); reverse-stress breach at "
                       "-%.2f%% cash; kill-switch %s"
                       % (effect["breach_probability_label"],
                          effect["liquidity_months"],
                          effect["reverse_stress_decline_pct"],
                          "TRIPPED" if tripped else "clear"),
            "effect": effect,
        }
    return rc.stage("RISK_EFFECT", _run)


def stage_goal_effect(rc, doc, base_seed=None, investable_override=None):
    def _run():
        if rc.degraded.blocks("GOAL_EFFECT"):
            raise BlockStage("goal effect blocked: " +
                             "; ".join(rc.degraded.reasons))
        goals = sorted(doc.get("goals") or [], key=lambda g: g.get("target_date", ""))
        if not goals:
            raise SkipStage("household declares no goals; goal effect not applicable")
        investable = investable_override
        if investable is None:
            investable = max(0.0, sum(
                float(a.get("balance", 0.0) or 0.0)
                for a in doc.get("accounts") or []
                if a.get("type") != "cash")
                - sum(float(l.get("balance", 0.0) or 0.0)
                      for l in doc.get("liabilities") or []))
        income = twin_scenarios._gross_annual_income(doc)
        contrib = 0.20 * income
        rows = []
        for i, g in enumerate(goals):
            years = max(1, min(int(round(days_between(rc.effective,
                                                      g.get("target_date", rc.effective)) / 365.25)), 40))
            seed = (base_seed if base_seed is not None else rc.seed) + i
            res = calcs_household.goal_funding_probability(
                current_balance=investable,
                annual_contribution=contrib,
                years=years,
                mu=0.06, sigma=0.15,
                goal_amount=float(g.get("target_amount", 0.0) or 0.0),
                seed=seed, simulations=4000)
            rows.append({
                "goal_id": g.get("id"),
                "priority": g.get("priority"),
                "target_date": g.get("target_date"),
                "target_amount": money(g.get("target_amount", 0.0)),
                "years": years,
                "probability": round(float(res["probability"]), 6),
                "p10": money(res["p10_final"]),
                "p50": money(res["median_final"]),
                "p90": money(res["p90_final"]),
                "seed": seed,
                "paths": 4000,
            })
        worst = min(rows, key=lambda r: r["probability"])
        effect = {
            "goals": rows,
            "investable_usd": money(investable),
            "annual_contribution_assumed": money(contrib),
            "worst_goal_id": worst["goal_id"],
            "worst_probability": worst["probability"],
            "model": "calcs_household.goal_funding_probability (lognormal MC, "
                     "4000 paths, seeded)",
        }
        rc.ctx["goal_effect"] = effect
        return {
            "value": effect,
            "summary": "%d goal(s) re-priced; worst is %s at %.3f"
                       % (len(rows), worst["goal_id"], worst["probability"]),
            "effect": effect,
        }
    return rc.stage("GOAL_EFFECT", _run)


# ===========================================================================
# Objective, alternatives, review, decision, approval, audit
# ===========================================================================

def make_alternative(alt_id, label, kind, *, trades=None, tax_usd=0.0,
                     fee_usd=0.0, drift_before=0.0, drift_after=None,
                     post_cash_usd=None, liquidity_months_after=None,
                     consequential=True, reversible=True, notes=None,
                     objective_suspended_reason=None, evidence=None):
    return {
        "alternative_id": alt_id,
        "label": label,
        "kind": kind,
        "consequential": bool(consequential),
        "reversible": bool(reversible),
        "trades": ascii_safe(trades or []),
        "tax_usd": money(tax_usd),
        "fee_usd": money(fee_usd),
        "drift_before": round(float(drift_before), 8),
        "drift_after": (round(float(drift_after), 8) if drift_after is not None
                        else round(float(drift_before), 8)),
        "post_cash_usd": (money(post_cash_usd) if post_cash_usd is not None else None),
        "liquidity_months_after": (round(float(liquidity_months_after), 4)
                                   if liquidity_months_after is not None else None),
        "objective_suspended_reason": objective_suspended_reason,
        "objective_usd": None,
        "notes": list(notes or []),
        "evidence": ascii_safe(evidence or {}),
    }


def evaluate_objectives(rc, alts):
    v_pre = float(rc.ctx.get("v_pre_usd", 0.0) or 0.0)
    floor = float(rc.ctx.get("liquidity_floor_usd", 0.0) or 0.0)
    for a in alts:
        if a.get("objective_suspended_reason"):
            a["objective_usd"] = None
            continue
        moved = max(0.0, a["drift_before"] - a["drift_after"])
        benefit = moved * v_pre * REBALANCE_PREMIUM
        cash = a.get("post_cash_usd")
        liq_pen = 0.0
        if cash is not None:
            liq_pen = max(0.0, floor - float(cash)) * LIQUIDITY_PENALTY_RATE
        a["objective_usd"] = money(benefit - a["tax_usd"] - a["fee_usd"] - liq_pen)
    return alts


def stage_alternatives(rc, alts):
    def _run():
        if not alts:
            raise BlockStage("no alternatives were generated")
        evaluate_objectives(rc, alts)
        scored = [a for a in alts if a["objective_usd"] is not None]
        if scored:
            ranked = sorted(alts, key=lambda a: (
                -(a["objective_usd"] if a["objective_usd"] is not None
                  else float("-inf")),
                0 if a["alternative_id"] == NO_ACTION_ID else 1,
                a["alternative_id"]))
            selected = ranked[0]["alternative_id"]
        else:
            ranked = list(alts)
            selected = NO_ACTION_ID
        rc.ctx["alternatives"] = ranked
        rc.ctx["selected_alternative_id"] = selected
        rc.emit("alternatives.ranked", {"selected": selected,
                                        "count": len(alts)})
        return {
            "summary": "%d alternatives generated and scored; ranked winner %s"
                       % (len(alts), selected),
            "count": len(alts),
            "selected": selected,
            "scores": {a["alternative_id"]: a["objective_usd"] for a in ranked},
        }
    return rc.stage("ALTERNATIVES_GENERATED", _run)


def stage_no_action(rc):
    def _run():
        alts = rc.ctx.get("alternatives") or []
        na = [a for a in alts if a["alternative_id"] == NO_ACTION_ID]
        if not na:
            raise BlockStage("NO-ACTION alternative is absent from the set")
        na = na[0]
        peers = [a for a in alts if a["alternative_id"] != NO_ACTION_ID]
        peer_keys = set()
        for p in peers:
            peer_keys.update(p.keys())
        missing = sorted(peer_keys - set(na.keys()))
        if missing:
            raise BlockStage(
                "no-action alternative is not a like-for-like peer; missing "
                "keys: %s" % missing)
        if na["consequential"]:
            raise BlockStage("no-action alternative is marked consequential")
        if na["trades"]:
            raise BlockStage("no-action alternative carries trades")
        return {
            "summary": "NO-ACTION present as a full peer alternative with %d "
                       "comparable fields, 0 trades, objective_usd=%s"
                       % (len(peer_keys), na["objective_usd"]),
            "no_action_objective_usd": na["objective_usd"],
            "peer_field_count": len(peer_keys),
            "no_action_wins": rc.ctx.get("selected_alternative_id") == NO_ACTION_ID,
        }
    return rc.stage("NO_ACTION_PRESENT", _run)


def stage_skeptical_review(rc, extra=None):
    def _run():
        challenges = [
            "The objective function charges a %.1f%% rebalancing premium "
            "((%s) bp) that is a modeling assumption, not an evidenced "
            "return; the ranking is only as good as that constant."
            % (REBALANCE_PREMIUM * 100.0, REBALANCE_PREMIUM * 10000.0),
            "Liquidity shortfall is penalised at %.0f cents per dollar below "
            "the floor; that rate is a parameter, not an observed cost."
            % (LIQUIDITY_PENALTY_RATE * 100.0),
            "Goal probabilities assume iid lognormal annual returns with "
            "mu=0.06, sigma=0.15; fat tails, sequence risk and regime change "
            "are excluded, so tail shortfall is understated.",
            "Wash-sale output is FLAGONLY over single-account history: "
            "spouse, IRA and external accounts are UNKNOWN and unexamined.",
            "Tax rates are caller-supplied parameters, not tax law; no "
            "state, NIIT, AMT or bracket interaction is modeled.",
            "Execution cost is a pre-trade ECM estimate, not a fill; realized "
            "slippage can differ materially.",
            "Prices are implied by rescaling a nominal table to each "
            "account's stated balance, so the portfolio reconciles to the "
            "twin by construction and hides any real pricing error.",
        ]
        if rc.ctx.get("risk_effect", {}).get("excluded_risks"):
            challenges.append(
                "Risk disclosure excludes %s; those exposures are unpriced."
                % ", ".join(rc.ctx["risk_effect"]["excluded_risks"]))

        # Model disagreement across independent code paths.
        nw_ti = twin_identity.net_worth(rc.post_doc or rc.base_doc)
        nw_ts = twin_scenarios.net_worth(rc.post_doc or rc.base_doc)
        pf_value = rc.ctx.get("portfolio_effect", {}).get("post_value")
        disagreement = abs(nw_ti - nw_ts["value"])
        notes = []
        if disagreement > 1.0:
            notes.append(
                "twin_identity.net_worth (%.2f) and twin_scenarios.net_worth "
                "(%.2f) disagree by %.2f" % (nw_ti, nw_ts["value"], disagreement))
        if not nw_ts["reconciles"]:
            notes.append(
                "twin_scenarios.net_worth reports reconciles=False: %s "
                "(finding W8-F1 -- unknown symbols are priced at zero)"
                % "; ".join(nw_ts["data_gaps"]))
        if pf_value is not None and abs(pf_value - nw_ti) > 1.0:
            notes.append(
                "portfolio-derived value (%.2f) differs from twin net worth "
                "(%.2f) by %.2f" % (pf_value, nw_ti, abs(pf_value - nw_ti)))

        data_quality = "COMPLETE"
        if rc.degraded.active:
            data_quality = "UNVERIFIABLE"
        elif notes:
            data_quality = "PARTIAL"
        confidence = "MED"
        if rc.degraded.active:
            confidence = "NONE-DEGRADED"
        elif data_quality == "PARTIAL":
            confidence = "LOW"

        review = {
            "challenges": list(challenges) + list(extra or []),
            "challenge_count": len(challenges) + len(extra or []),
            "model_disagreement": notes,
            "net_worth_paths": {
                "twin_identity": money(nw_ti),
                "twin_scenarios": money(nw_ts["value"]),
                "portfolio_derived": money(pf_value) if pf_value is not None else None,
            },
            "data_quality": data_quality,
            "confidence": confidence,
            "dissent": (
                ["A reasonable reviewer could reject every trade alternative "
                 "here: the only benefit term is an assumed rebalancing "
                 "premium, while tax and ECM costs are concrete."]
                if rc.ctx.get("selected_alternative_id") == NO_ACTION_ID
                else ["A reasonable reviewer could prefer holding: the "
                      "benefit term is an assumption and the costs are not."]),
        }
        rc.ctx["skeptical_review"] = review
        return {
            "summary": "skeptical review raised %d challenge(s); data quality "
                       "%s; confidence %s"
                       % (review["challenge_count"], data_quality, confidence),
            "review": review,
        }
    return rc.stage("SKEPTICAL_REVIEW", _run)


def stage_decision(rc):
    def _run():
        alts = rc.ctx.get("alternatives") or []
        if not alts:
            raise BlockStage("no alternatives to decide between")
        sel_id = rc.ctx.get("selected_alternative_id")
        sel = next((a for a in alts if a["alternative_id"] == sel_id), None)
        if sel is None:
            raise BlockStage("selected alternative %r not in the set" % sel_id)
        rev = rc.ctx.get("skeptical_review") or {}
        pf = rc.ctx.get("portfolio_effect") or {}
        tax = rc.ctx.get("tax_effect") or {}
        liq = rc.ctx.get("liquidity_effect") or {}
        risk = rc.ctx.get("risk_effect") or {}
        goal = rc.ctx.get("goal_effect") or {}

        v = float(rc.ctx.get("v_pre_usd", 0.0) or 0.0)
        dist = mc_terminal_distribution(
            rc.seed + 991, v, 0.06, 0.15, 5)

        decision = {
            "decision_id": "decision:%s" % rc.sid,
            "scenario_id": rc.sid,
            "trigger": ascii_safe(rc.events[0]["event_type"] if rc.events else None),
            "info_cutoff": rc.clock,
            "objectives": [rc.objective["statement"]],
            "objective_metric": rc.objective["metric"],
            "horizon_months": rc.objective.get("horizon_months", 12),
            "constraints": ascii_safe((rc.ctx.get("policy") or {}).get("constraints", {})),
            "alternatives_considered": [a["alternative_id"] for a in alts],
            "selected_alternative_id": sel_id,
            "selected_is_consequential": bool(sel["consequential"]),
            "selected_objective_usd": sel["objective_usd"],
            "expected_distribution_5y": dist,
            "tax_effect_usd": money(
                (tax.get("rebalancing_tax_cost_usd") or 0.0)
                + (pf.get("realized_tax_usd") or 0.0)),
            "fee_effect_usd": money(pf.get("ecm_cost_usd") or 0.0),
            "liquidity_effect_usd": money(-1.0 * (liq.get("floor_gap_usd") or 0.0)),
            "opportunity_cost_usd": money(
                max([a["objective_usd"] for a in alts
                     if a["objective_usd"] is not None] or [0.0])
                - (sel["objective_usd"] or 0.0)),
            "risk_effect": ascii_safe({
                "label": risk.get("breach_probability_label"),
                "kill_switch_tripped": risk.get("kill_switch_tripped"),
                "reverse_stress_decline_pct": risk.get("reverse_stress_decline_pct"),
            }),
            "goal_effect": ascii_safe({
                "worst_goal_id": goal.get("worst_goal_id"),
                "worst_probability": goal.get("worst_probability"),
            }),
            "model_disagreement": ascii_safe(rev.get("model_disagreement")),
            "data_quality": rev.get("data_quality"),
            "confidence": rev.get("confidence"),
            "reversibility": "REVERSIBLE" if sel["reversible"] else "IRREVERSIBLE",
            "professional_review_triggers": [
                "tax consequence on a realized gain",
                "liquidity floor breach",
                "insurance coverage change",
                "estate or beneficiary change",
            ],
            "required_approvals": (
                ["human:household", "human:licensed-professional"]
                if sel["consequential"] else []),
            "invalidation_conditions": [
                "any upstream fact in the provenance closure is restated",
                "liquidity floor changes",
                "tax-rate parameters change",
                "new event ingested for this household",
            ],
            "monitoring_plan": {
                "cadence": "on every new event; weekly otherwise",
                "watch": ["liquidity_months", "drift_vs_target",
                          "worst_goal_probability", "kill_switch"],
            },
            "evidence_links": {
                "provenance_store": os.path.relpath(rc.prov_path, REPO_ROOT).replace("\\", "/"),
                "stale_events": os.path.relpath(rc.marks_path, REPO_ROOT).replace("\\", "/"),
                "obs_events": os.path.relpath(rc.obs_path, REPO_ROOT).replace("\\", "/"),
            },
            "degraded": rc.degraded.active,
            "disclosure": (
                "No action described here has been executed. This object is a "
                "recommendation awaiting human approval."
                + (" SAFE DEGRADED MODE: " + " ".join(rc.degraded.disclosures)
                   if rc.degraded.active else "")),
        }
        rc.ctx["decision"] = decision
        rc.emit("decision.assembled",
                {"decision_id": decision["decision_id"],
                 "selected": sel_id,
                 "consequential": sel["consequential"]})
        return {
            "value": decision,
            "summary": "decision %s assembled; selected %s (consequential=%s, "
                       "confidence %s)"
                       % (decision["decision_id"], sel_id,
                          sel["consequential"], decision["confidence"]),
            "decision_id": decision["decision_id"],
        }
    return rc.stage("DECISION_OBJECT", _run)


def stage_approval(rc):
    def _run():
        decision = rc.ctx.get("decision")
        if decision is None:
            raise BlockStage("no decision object to gate")
        state = rc.gate.submit(decision)
        refusals = []
        if decision["selected_is_consequential"]:
            action = {
                "decision_id": decision["decision_id"],
                "alternative_id": decision["selected_alternative_id"],
                "kind": "ORDER_ROUTE",
            }
            try:
                rc.gate.execute(action)
                raise BlockStage(
                    "approval gate FAILED OPEN: execution returned without "
                    "recorded approval")
            except ApprovalRequiredError as exc:
                refusals.append({"action": action, "error": str(exc)})
        # Probe a second, unrelated action to prove the gate is not per-action.
        try:
            rc.gate.execute({"kind": "PROBE_UNAUTHORIZED_TRANSFER",
                             "decision_id": decision["decision_id"]})
            raise BlockStage("approval gate FAILED OPEN on the probe action")
        except ApprovalRequiredError as exc:
            refusals.append({"kind": "PROBE_UNAUTHORIZED_TRANSFER",
                             "error": str(exc)})

        if rc.gate.executed_actions:
            raise BlockStage("approval gate recorded an executed action")
        if decision["selected_is_consequential"] and state != GATE_AWAITING:
            raise BlockStage(
                "consequential decision ended in %s, expected %s"
                % (state, GATE_AWAITING))
        rc.emit("approval.required",
                {"state": state, "refusals": len(refusals)})
        return {
            "summary": "gate state %s; %d execution attempt(s) refused; 0 "
                       "actions executed" % (state, len(refusals)),
            "gate_state": state,
            "refusals": ascii_safe(refusals),
            "executed_actions": rc.gate.executed_actions,
        }
    return rc.stage("APPROVAL_ENFORCEMENT", _run)


def stage_audit(rc):
    def _run():
        rc.audit.append("scenario.completed", {
            "terminal_state": rc.gate.state,
            "executed_actions": len(rc.gate.executed_actions),
            "degraded": rc.degraded.active,
        })
        ok, bad = rc.audit.verify()
        ok_disk, n_disk = rc.audit.verify_on_disk()
        if not ok:
            raise BlockStage("audit chain broken at record %s" % bad)
        if not ok_disk or n_disk != len(rc.audit.records):
            raise BlockStage(
                "on-disk audit chain does not match in-memory records "
                "(disk_ok=%s, disk_records=%d, memory=%d)"
                % (ok_disk, n_disk, len(rc.audit.records)))
        return {
            "summary": "audit log closed with %d records; hash chain verified "
                       "in memory and on disk"
                       % len(rc.audit.records),
            "records": len(rc.audit.records),
            "chain_ok": True,
            "head": rc.audit.records[-1]["record_hash"],
        }
    return rc.stage("AUDIT_HISTORY", _run)


# ===========================================================================
# Standard scenario body
# ===========================================================================

def run_standard(rc, cfg):
    """Drive one scenario through all 18 stages.

    cfg keys:
      event_type, event_source, event_payload, severity
      mutate(doc, rc) -> (new_doc, transition_label, audit_event, changed)
      cash_delta        liquidity ledger movement (USD, signed)
      shock             dict for risk_engine.hypothetical_shock or None
      limits            kill-switch limits or None
      policy_overrides  dict or None
      portfolio_mutate(portfolio, doc, rc) -> portfolio or None
      alternatives(ctx, rc) -> list of alternative dicts
      review_extra      list of extra skeptical challenges
      degraded          (reason, disclosure, blocked_capabilities) or None
      outcome           one-line outcome string
    """
    doc = rc.base_doc

    if cfg.get("degraded"):
        reason, disclosure, blocked = cfg["degraded"]
        rc.degraded.engage(reason, disclosure, blocked)

    stage_ingest(rc, cfg["event_type"], cfg["event_payload"],
                 cfg.get("event_source", "synthetic-feed"),
                 severity=cfg.get("severity", "normal"))
    stage_validate(rc, doc, "pre-event twin (%s)" % rc.household)
    stage_provenance(rc, doc)
    stage_temporal(rc, doc)
    stage_dependency_propagation(
        rc, "fact:household:%s" % rc.household,
        shadow.canonical_sha256(doc) + "|event=" +
        (rc.events[0]["event_id"] if rc.events else "none"))
    stage_stale_invalidation(rc, rc.outputs.ids())

    # --- stage 7: digital-twin update ------------------------------------
    def _twin():
        if cfg.get("freeze_twin"):
            raise BlockStage("twin update refused: " +
                             "; ".join(rc.degraded.reasons))
        new_doc, label, audit_event, changed = cfg["mutate"](copy.deepcopy(doc), rc)
        return _finish_twin(rc, doc, new_doc, label, audit_event, changed)
    rc.stage("DIGITAL_TWIN_UPDATE", _twin)

    policy = policy_for(rc.post_doc or doc, cfg.get("policy_overrides"))

    # --- stage 8: portfolio ----------------------------------------------
    def _pf():
        if rc.degraded.blocks("PORTFOLIO_EFFECT"):
            raise BlockStage("portfolio effect blocked: " +
                             "; ".join(rc.degraded.reasons))
        target_doc = rc.post_doc or doc
        prices = implied_prices(target_doc)
        pf = portfolio_from_twin(target_doc, prices, rc.effective)
        if cfg.get("portfolio_mutate"):
            pf = cfg["portfolio_mutate"](pf, target_doc, rc) or pf
        return _finish_portfolio(rc, target_doc, policy, pf)
    rc.stage("PORTFOLIO_EFFECT", _pf)

    stage_tax_effect(rc, rc.post_doc or doc, policy)
    stage_liquidity_effect(rc, rc.post_doc or doc,
                           cash_delta=cfg.get("cash_delta", 0.0),
                           label=cfg.get("ledger_label", "scenario cash move"))
    stage_risk_effect(rc, rc.post_doc or doc, shock=cfg.get("shock"),
                      limits=cfg.get("limits"),
                      portfolio=rc.ctx.get("portfolio"))
    stage_goal_effect(rc, rc.post_doc or doc)

    alts = cfg["alternatives"](rc.ctx, rc)
    for a in alts:
        if a.get("objective_suspended_reason") is None and rc.degraded.active:
            a["objective_suspended_reason"] = (
                "safe degraded mode: objective not computable on unverified "
                "inputs")
    stage_alternatives(rc, alts)
    stage_no_action(rc)
    stage_skeptical_review(rc, cfg.get("review_extra"))
    stage_decision(rc)
    stage_approval(rc)
    stage_audit(rc)

    return rc.finish(cfg["outcome"], extra=cfg.get("extra"))


def _finish_twin(rc, doc, new_doc, label, audit_event, changed):
    """Body shared by stage 7 (inline so BlockStage is recorded correctly)."""
    errors = twin_schema.validate_twin(new_doc)
    if errors:
        raise BlockStage("post-transition document rejected: %d error(s): %s"
                         % (len(errors), "; ".join(errors[:3])))
    nw_before = twin_identity.net_worth(doc)
    nw_after = twin_identity.net_worth(new_doc)
    liq_before = twin_identity.household_liquidity(doc)
    liq_after = twin_identity.household_liquidity(new_doc)

    restamped = []
    for acct in new_doc.get("accounts") or []:
        ent = "account:%s:balance" % acct.get("id")
        if rc.temporal.as_of(ent, rc.effective, rc.known_pre) is None:
            continue
        restamped.append(rc.temporal.put(
            ent, float(acct.get("balance", 0.0) or 0.0),
            rc.effective, rc.known_post, source="twin-transition"))
    for mem in new_doc.get("members") or []:
        ent = "member:%s:employment_status" % mem.get("id")
        if rc.temporal.as_of(ent, rc.effective, rc.known_pre) is None:
            continue
        restamped.append(rc.temporal.put(
            ent, str((mem.get("employment") or {}).get("status", "unknown")),
            rc.effective, rc.known_post, source="twin-transition"))
    for goal in new_doc.get("goals") or []:
        ent = "goal:%s:priority" % goal.get("id")
        if rc.temporal.as_of(ent, rc.effective, rc.known_pre) is None:
            continue
        restamped.append(rc.temporal.put(
            ent, str(goal.get("priority", "unknown")),
            rc.effective, rc.known_post, source="twin-transition"))

    diverged = []
    for row in restamped:
        old = rc.temporal.as_of(row["entity"], rc.effective, rc.known_pre)
        new = rc.temporal.as_of(row["entity"], rc.effective, rc.known_post)
        if old is not None and new is not None and old["value"] != new["value"]:
            diverged.append({"entity": row["entity"],
                             "known_pre": old["value"],
                             "known_post": new["value"]})

    rc.post_doc = new_doc
    rc.emit("twin.updated",
            {"transition": label,
             "net_worth_delta": money(nw_after - nw_before),
             "liquidity_delta": money(liq_after - liq_before)})
    return {
        "value": new_doc,
        "summary": "%s applied; net worth %.2f -> %.2f, liquidity %.2f -> "
                   "%.2f; %d temporal rows restated (%d diverged)"
                   % (label, nw_before, nw_after, liq_before, liq_after,
                      len(restamped), len(diverged)),
        "transition": label,
        "audit_event": ascii_safe(audit_event),
        "net_worth_before": money(nw_before),
        "net_worth_after": money(nw_after),
        "liquidity_before": money(liq_before),
        "liquidity_after": money(liq_after),
        "temporal_rows_restated": len(restamped),
        "bitemporal_divergence": ascii_safe(diverged),
        "changed_entities": ascii_safe(changed or []),
    }


def _finish_portfolio(rc, doc, policy, pf):
    w_pre, v_pre = class_weights(pf)
    drift_pre = active_share(w_pre, policy["targets"])
    plan = portfolio_engine.propose_rebalance(
        pf, policy["targets"], policy["bands"], policy["constraints"],
        ecm=rc.ecm, tax_rates=policy["tax_rates"])
    recalc = None
    if plan["action"] is not None:
        portfolio_engine.independent_recalculation(plan, pf, ecm=rc.ecm)
        recalc = "independent_recalculation matched the planner"
    act = plan["action"] or plan["no_action"]
    m = act["metrics"]
    drift_post = active_share(m["post_class_weights"], policy["targets"])
    effect = {
        "status": plan["status"],
        "pre_value": money(v_pre),
        "post_value": money(m["portfolio_value_usd"]),
        "pre_weights": {k: round(v, 6) for k, v in sorted(w_pre.items())},
        "post_weights": {k: round(v, 6) for k, v in sorted(m["post_class_weights"].items())},
        "drift_before": drift_pre,
        "drift_after": drift_post,
        "trade_count": len(plan["action"]["trades"]) if plan["action"] else 0,
        "turnover_pct": round(m["turnover_one_sided_pct"] * 100.0, 4),
        "ecm_cost_usd": money(m["ecm_cost_usd"]),
        "realized_tax_usd": money(m["realized_gains"]["tax_usd"]),
        "post_cash_usd": money(m["post_cash_usd"]),
        "constraint_checks": act["constraint_checks"],
        "independent_recalculation": recalc,
        "instability": plan["instability"],
        "reasons": plan["reasons"],
    }
    rc.ctx["portfolio_effect"] = effect
    rc.ctx["plan"] = plan
    rc.ctx["portfolio"] = pf
    rc.ctx["policy"] = policy
    rc.ctx["v_pre_usd"] = money(v_pre)
    rc.ctx["prices"] = implied_prices(doc)
    rc.ctx["post_cash_usd"] = money(m["post_cash_usd"])
    return {
        "value": effect,
        "summary": "rebalance status=%s; %d trade leg(s); drift %.4f -> %.4f; "
                   "tax %.2f; ecm %.2f"
                   % (plan["status"], effect["trade_count"], drift_pre,
                      drift_post, effect["realized_tax_usd"],
                      effect["ecm_cost_usd"]),
        "effect": effect,
    }


# ===========================================================================
# Shared alternative builders
# ===========================================================================

def no_action_alternative(ctx, notes=None):
    pf = ctx.get("portfolio_effect") or {}
    return make_alternative(
        NO_ACTION_ID, "Take no action", "no_action",
        trades=[], tax_usd=0.0, fee_usd=0.0,
        drift_before=pf.get("drift_before", 0.0),
        drift_after=pf.get("drift_before", 0.0),
        post_cash_usd=ctx.get("post_cash_usd"),
        liquidity_months_after=ctx.get("liquidity_months"),
        consequential=False, reversible=True,
        notes=list(notes or ["No trade, no tax event, no execution cost. "
                             "Every other alternative must beat this."]),
        evidence={"baseline": "current twin state"},
    )


def rebalance_alternative(ctx, alt_id="ALT-REBALANCE", label="Rebalance to target"):
    pf = ctx.get("portfolio_effect") or {}
    return make_alternative(
        alt_id, label, "trade",
        trades=(ctx.get("plan") or {}).get("action", {}).get("trades", [])
        if (ctx.get("plan") or {}).get("action") else [],
        tax_usd=pf.get("realized_tax_usd", 0.0),
        fee_usd=pf.get("ecm_cost_usd", 0.0),
        drift_before=pf.get("drift_before", 0.0),
        drift_after=pf.get("drift_after", pf.get("drift_before", 0.0)),
        post_cash_usd=pf.get("post_cash_usd", ctx.get("post_cash_usd")),
        liquidity_months_after=ctx.get("liquidity_months"),
        consequential=True, reversible=True,
        notes=["Band-triggered trades from portfolio_engine.propose_rebalance; "
               "lot selection highest-loss-first; ECM charged round-trip."],
        evidence={"status": pf.get("status"),
                  "turnover_pct": pf.get("turnover_pct")},
    )


# ===========================================================================
# The 18 scenarios
# ===========================================================================

def _unemploy(doc, member_id, months):
    """Mark a member unemployed (twin_identity has no job-loss transition)."""
    for m in doc.get("members") or []:
        if m.get("id") == member_id:
            emp = m.setdefault("employment", {})
            emp["status"] = "unemployed"
            emp["income_streams"] = []
    return doc


def _decline(doc, pct, skip_cash=True):
    for acct in doc.get("accounts") or []:
        if skip_cash and acct.get("type") == "cash":
            continue
        if acct.get("balance") is not None:
            acct["balance"] = round(float(acct["balance"]) * (1.0 + pct), 2)
    return doc


def scenario_01_job_loss_market_crash(rc):
    """Job loss concurrent with a 35% market decline."""
    def mutate(doc, _rc):
        doc = _unemploy(doc, "m1", 6)
        doc = _decline(doc, -0.35)
        tr = twin_identity.goal_reprioritize(
            doc, "g-mg-accessibility-renovation", "low", rc.effective)
        return tr["new_doc"], "job_loss + market_decline(-35%) + goal_reprioritize", \
            tr["events"][0], ["member:m1", "all non-cash accounts"]

    def alts(ctx, _rc):
        out = [no_action_alternative(ctx)]
        pf = ctx.get("portfolio_effect") or {}
        cash_now = float(ctx.get("post_cash_usd") or 0.0)
        floor = float(ctx.get("liquidity_floor_usd") or 0.0)
        top_up = max(0.0, floor * 2.0 - cash_now)
        out.append(make_alternative(
            "ALT-REBUILD-CASH", "Sell bonds to rebuild the cash buffer", "trade",
            trades=[{"side": "SELL", "asset_class": "bonds",
                     "notional_usd": money(top_up)}],
            tax_usd=max(0.0, top_up * 0.02),
            fee_usd=25.44 * 2,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0) + 0.10,
            post_cash_usd=money(cash_now + top_up),
            liquidity_months_after=(ctx.get("liquidity_months") or 0.0) + 1.5,
            consequential=True, reversible=True,
            notes=["Raises cash to 2x the liquidity floor; realizes gain/loss "
                   "in the bond sleeve and pays two ECM legs."]))
        out.append(make_alternative(
            "ALT-CUT-SPEND", "Cut discretionary spend 25% and pause 529", "policy",
            trades=[], tax_usd=0.0, fee_usd=0.0,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0),
            post_cash_usd=money(cash_now),
            liquidity_months_after=(ctx.get("liquidity_months") or 0.0) * 1.33,
            consequential=True, reversible=True,
            notes=["No market action; extends runway by reducing outflow."]))
        return out

    return run_standard(rc, {
        "event_type": "employment.termination+market.decline",
        "event_source": "synthetic-hr-feed+synthetic-market-feed",
        "event_payload": {"member": "m1", "months_unemployed": 6,
                          "market_decline_pct": -0.35,
                          "note": "SYNTHETIC event, no real person or ticker"},
        "severity": "high",
        "mutate": mutate,
        "cash_delta": -45000.0,
        "ledger_label": "6 months synthetic living draw",
        "shock": {"equity_pct": -0.35, "duration_shock": -0.02},
        "limits": {"liquidity_months": {"min": 3.0}},
        "alternatives": alts,
        "review_extra": [
            "Job loss and a 35% decline are modeled as simultaneous; the "
            "correlation between them is assumed, not estimated.",
        ],
        "outcome": ("Liquidity cover collapses below the floor after a "
                    "simultaneous job loss and 35% decline; a cash-buffer "
                    "rebuild is recommended and parked at AWAITING-APPROVAL."),
    })


def scenario_02_employer_equity_vesting(rc):
    """RSU vest: W-2 income, sell-to-cover tax, and concentration growth."""
    VEST_SHARES = 500.0
    VEST_PRICE = 142.50
    VEST_VALUE = VEST_SHARES * VEST_PRICE

    def mutate(doc, _rc):
        for acct in doc.get("accounts") or []:
            if acct.get("id") != "brk-taxable-t":
                continue
            for h in acct.get("holdings") or []:
                if h.get("symbol") == "ZPHR":
                    h["qty"] = round(float(h["qty"]) + VEST_SHARES, 6)
                    h.setdefault("tax_lots", []).append({
                        "acq_date": rc.effective,
                        "cost_basis": money(VEST_VALUE),
                        "qty": VEST_SHARES,
                    })
            acct["balance"] = round(float(acct.get("balance", 0.0)) + VEST_VALUE, 2)
        tr = twin_identity.employer_change(doc, "m1", "SYNTH-EMPLOYER-ZEPHYR",
                                           rc.effective)
        return tr["new_doc"], "rsu_vest + employer_change", tr["events"][0], \
            ["account:brk-taxable-t", "member:m1"]

    def alts(ctx, _rc):
        out = [no_action_alternative(ctx)]
        pf = ctx.get("portfolio_effect") or {}
        out.append(rebalance_alternative(
            ctx, "ALT-TRIM-ZPHR", "Trim ZPHR to the single-issuer cap"))
        sell_cover = VEST_VALUE * 0.37
        out.append(make_alternative(
            "ALT-SELL-TO-COVER", "Sell-to-cover the supplemental withholding",
            "trade",
            trades=[{"side": "SELL", "ticker": "ZPHR@brk-taxable-t",
                     "notional_usd": money(sell_cover)}],
            tax_usd=0.0,
            fee_usd=25.44,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0) + 0.02,
            post_cash_usd=money((ctx.get("post_cash_usd") or 0.0) + sell_cover),
            liquidity_months_after=ctx.get("liquidity_months"),
            consequential=True, reversible=False,
            notes=["Vest-date sale creates a short-term lot; the wash-sale "
                   "window around the vest is unexamined for other accounts."]))
        out.append(make_alternative(
            "ALT-DEFER-SALE", "Hold the full vest and pay tax from cash", "policy",
            trades=[], tax_usd=0.0, fee_usd=0.0,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0),
            post_cash_usd=money((ctx.get("post_cash_usd") or 0.0) - sell_cover),
            liquidity_months_after=ctx.get("liquidity_months"),
            consequential=True, reversible=True,
            notes=["Keeps concentration; draws the tax bill from cash."]))
        return out

    return run_standard(rc, {
        "event_type": "equity.vest",
        "event_source": "synthetic-equity-admin",
        "event_payload": {"symbol": "ZPHR", "shares": VEST_SHARES,
                          "price": VEST_PRICE, "value_usd": money(VEST_VALUE),
                          "award_kind": "RSU",
                          "note": "SYNTHETIC vest, fictional issuer"},
        "mutate": mutate,
        "cash_delta": -VEST_VALUE * 0.37,
        "ledger_label": "supplemental withholding on synthetic RSU vest",
        "alternatives": alts,
        "review_extra": [
            "The 37% supplemental withholding rate is an assumption; actual "
            "withholding depends on jurisdiction and elections not in the twin.",
            "VEST_VALUE uses a frozen synthetic price; the real vest-date "
            "price is unknown at planning time.",
        ],
        "outcome": ("A synthetic RSU vest increases single-issuer "
                    "concentration past the cap; trimming is recommended and "
                    "parked at AWAITING-APPROVAL."),
    })


def scenario_03_rate_shock(rc):
    """+200bp parallel rate shock: bond repricing and variable debt service."""
    DURATION = 6.0
    RATE_SHOCK = 0.02

    def mutate(doc, _rc):
        for acct in doc.get("accounts") or []:
            if acct.get("type") == "cash":
                continue
            for h in acct.get("holdings") or []:
                if asset_class_of(h.get("symbol")) != "bonds":
                    continue
                frac = sum(float(l.get("qty", 0.0)) for l in h.get("tax_lots") or []) \
                    / max(float(h.get("qty", 1.0)), 1e-9)
                if frac <= 0:
                    continue
            if float(acct.get("balance", 0.0) or 0.0) <= 0:
                continue
            bond_mv = 0.0
            prices = implied_prices(doc)
            for h in acct.get("holdings") or []:
                if asset_class_of(h.get("symbol")) == "bonds":
                    px = prices.get("%s|%s" % (acct.get("id"), h.get("symbol")), 0.0)
                    bond_mv += float(h.get("qty", 0.0)) * px
            if bond_mv <= 0:
                continue
            delta = -DURATION * RATE_SHOCK * bond_mv
            acct["balance"] = round(float(acct["balance"]) + delta, 2)
            scale = 1.0 + delta / bond_mv
            for h in acct.get("holdings") or []:
                if asset_class_of(h.get("symbol")) == "bonds":
                    h["qty"] = round(float(h.get("qty", 0.0)) * scale, 6)
        for liab in doc.get("liabilities") or []:
            if liab.get("kind") == "cc":
                liab["rate"] = round(float(liab.get("rate", 0.0)) + RATE_SHOCK, 6)
        return doc, "rate_shock(+200bp) duration repricing", None, \
            ["all bond holdings", "liability:cc"]

    def alts(ctx, _rc):
        out = [no_action_alternative(ctx)]
        pf = ctx.get("portfolio_effect") or {}
        out.append(rebalance_alternative(
            ctx, "ALT-BUY-BONDS", "Buy the bond dip back to target"))
        out.append(make_alternative(
            "ALT-SHORTEN-DURATION", "Shorten duration to reduce rate sensitivity",
            "trade",
            trades=[{"side": "SELL", "asset_class": "bonds", "notional_usd": 60000.0},
                    {"side": "BUY", "asset_class": "bonds-short", "notional_usd": 60000.0}],
            tax_usd=1200.0, fee_usd=25.44 * 2,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=max(0.0, pf.get("drift_before", 0.0) - 0.05),
            post_cash_usd=ctx.get("post_cash_usd"),
            liquidity_months_after=ctx.get("liquidity_months"),
            consequential=True, reversible=True,
            notes=["Duration change is a directional rate view; the passive "
                   "mandate forbids directional bets, so this alternative is "
                   "surfaced but flagged as out-of-mandate."]))
        out.append(make_alternative(
            "ALT-PAY-CC", "Pay down the variable-rate credit line", "policy",
            trades=[], tax_usd=0.0, fee_usd=0.0,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0) + 0.02,
            post_cash_usd=money((ctx.get("post_cash_usd") or 0.0) - 14000.0),
            liquidity_months_after=ctx.get("liquidity_months"),
            consequential=True, reversible=False,
            notes=["Removes the rate-sensitive liability instead of trading "
                   "around it; reduces liquidity."]))
        return out

    return run_standard(rc, {
        "event_type": "rates.shock",
        "event_source": "synthetic-macro-feed",
        "event_payload": {"parallel_shift_bp": 200, "duration_years": DURATION,
                          "note": "SYNTHETIC yield-curve move"},
        "severity": "high",
        "mutate": mutate,
        "cash_delta": -1800.0,
        "ledger_label": "increased variable-rate debt service",
        "shock": {"equity_pct": -0.05, "duration_shock": -0.12},
        "alternatives": alts,
        "review_extra": [
            "A single duration number (%0.1f) stands in for a whole curve; "
            "convexity and credit spread are ignored." % DURATION,
        ],
        "outcome": ("A +200bp shock repriced the bond sleeve and raised "
                    "variable-rate debt service; a policy response is "
                    "recommended and parked at AWAITING-APPROVAL."),
    })


def scenario_04_retirement_before_crash(rc):
    """Retirement begins, then a 30% decline (sequence-of-returns risk)."""

    def mutate(doc, _rc):
        for m in doc.get("members") or []:
            if m.get("id") == "m1":
                emp = m.setdefault("employment", {})
                emp["status"] = "retired"
                emp["income_streams"] = []
        doc = _decline(doc, -0.30)
        return doc, "retirement(m1) + market_decline(-30%)", None, \
            ["member:m1", "all non-cash accounts"]

    def alts(ctx, _rc):
        out = [no_action_alternative(ctx)]
        pf = ctx.get("portfolio_effect") or {}
        out.append(make_alternative(
            "ALT-DELAY-RETIREMENT", "Delay retirement 24 months", "policy",
            trades=[], tax_usd=0.0, fee_usd=0.0,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0),
            post_cash_usd=money((ctx.get("post_cash_usd") or 0.0) + 120000.0),
            liquidity_months_after=(ctx.get("liquidity_months") or 0.0) + 8.0,
            consequential=True, reversible=False,
            notes=["Human-capital decision, not a portfolio trade; the twin "
                   "cannot verify that continued employment is available."]))
        out.append(make_alternative(
            "ALT-REDUCE-WITHDRAWAL", "Cut the draw to 3.0% of the reduced base",
            "policy",
            trades=[], tax_usd=0.0, fee_usd=0.0,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0),
            post_cash_usd=ctx.get("post_cash_usd"),
            liquidity_months_after=(ctx.get("liquidity_months") or 0.0) * 1.20,
            consequential=True, reversible=True,
            notes=["Withdrawal rate is a parameter; no safe-withdrawal "
                   "study is encoded in this harness."]))
        out.append(rebalance_alternative(
            ctx, "ALT-DE-RISK", "De-risk toward the target allocation"))
        return out

    return run_standard(rc, {
        "event_type": "employment.retirement+market.decline",
        "event_source": "synthetic-hr-feed+synthetic-market-feed",
        "event_payload": {"member": "m1", "retirement_date": rc.effective,
                          "market_decline_pct": -0.30,
                          "note": "SYNTHETIC retirement and decline"},
        "severity": "high",
        "mutate": mutate,
        "cash_delta": -96000.0,
        "ledger_label": "first-year retirement draw (synthetic)",
        "shock": {"equity_pct": -0.30, "duration_shock": 0.0},
        "limits": {"liquidity_months": {"min": 6.0}},
        "alternatives": alts,
        "review_extra": [
            "Sequence-of-returns risk is the dominant exposure here and the "
            "Monte Carlo iid model understates it badly.",
            "The 3.0% withdrawal figure is a convention, not an optimized "
            "policy for this household.",
        ],
        "outcome": ("Retirement starting immediately before a 30% decline "
                    "breaches the 6-month liquidity limit; delaying or cutting "
                    "the draw is recommended and parked at AWAITING-APPROVAL."),
    })


def scenario_05_healthcare_shock(rc):
    """Acute health event: out-of-pocket spend and lost income."""
    OOP = 185000.0

    def mutate(doc, _rc):
        for m in doc.get("members") or []:
            if m.get("id") == "m2":
                emp = m.setdefault("employment", {})
                emp["status"] = "disabled"
                emp["income_streams"] = []
        cash = [a for a in doc.get("accounts") or [] if a.get("type") == "cash"]
        remaining = OOP
        for a in cash:
            take = min(float(a.get("balance", 0.0) or 0.0), remaining)
            a["balance"] = round(float(a.get("balance", 0.0)) - take, 2)
            remaining -= take
        doc.setdefault("assumptions", {})["health_shock_uninsured_usd"] = \
            money(max(remaining, 0.0))
        return doc, "disability(m2) + healthcare out-of-pocket", None, \
            ["member:m2", "all cash accounts"]

    def alts(ctx, _rc):
        out = [no_action_alternative(ctx)]
        pf = ctx.get("portfolio_effect") or {}
        cash_now = float(ctx.get("post_cash_usd") or 0.0)
        raise_amt = max(0.0, 240000.0 - cash_now)
        out.append(make_alternative(
            "ALT-LIQUIDATE-FOR-CARE", "Liquidate taxable assets for care costs",
            "trade",
            trades=[{"side": "SELL", "asset_class": "equity",
                     "notional_usd": money(raise_amt)}],
            tax_usd=raise_amt * 0.03,
            fee_usd=25.44,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0) + 0.08,
            post_cash_usd=money(cash_now + raise_amt),
            liquidity_months_after=(ctx.get("liquidity_months") or 0.0) + 6.0,
            consequential=True, reversible=False,
            notes=["Realizes gains in a down-cash state; HSA and 529 are "
                   "sequenced separately by statute not modeled here."]))
        out.append(make_alternative(
            "ALT-HSA-DRAW", "Draw HSA for qualified medical costs", "policy",
            trades=[], tax_usd=0.0, fee_usd=0.0,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0),
            post_cash_usd=money(cash_now + 12180.0),
            liquidity_months_after=ctx.get("liquidity_months"),
            consequential=True, reversible=False,
            notes=["Tax-free for qualified expenses only; eligibility is an "
                   "assumption the twin does not verify."]))
        out.append(make_alternative(
            "ALT-CLAIM-DISABILITY", "Claim the disability policy benefit",
            "policy",
            trades=[], tax_usd=0.0, fee_usd=0.0,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0),
            post_cash_usd=money(cash_now + 9000.0 * 6),
            liquidity_months_after=(ctx.get("liquidity_months") or 0.0) + 3.0,
            consequential=True, reversible=False,
            notes=["Benefit is modeled as 6 months of the stated monthly "
                   "coverage; elimination period and offsets are unmodeled."]))
        return out

    return run_standard(rc, {
        "event_type": "health.shock",
        "event_source": "synthetic-claims-feed",
        "event_payload": {"member": "m2", "out_of_pocket_usd": money(OOP),
                          "status": "disabled",
                          "note": "SYNTHETIC health event, fictional person"},
        "severity": "high",
        "mutate": mutate,
        "cash_delta": -OOP,
        "ledger_label": "synthetic out-of-pocket medical spend",
        "limits": {"liquidity_months": {"min": 3.0}},
        "alternatives": alts,
        "review_extra": [
            "The out-of-pocket figure is a single point estimate; the "
            "distribution of healthcare costs is heavily right-skewed and "
            "unmodeled.",
            "Disability benefit timing (elimination period) can be months and "
            "is not in the twin.",
        ],
        "outcome": ("A disability plus out-of-pocket spend drains cash below "
                    "the floor; a coordinated HSA/claim/liquidate response is "
                    "recommended and parked at AWAITING-APPROVAL."),
    })


def scenario_06_home_purchase(rc):
    """Home purchase: down payment out of cash plus a new mortgage."""
    PRICE = 420000.0
    DOWN = 70000.0

    def mutate(doc, _rc):
        remaining = DOWN
        for a in doc.get("accounts") or []:
            if a.get("type") != "cash" or remaining <= 0:
                continue
            take = min(float(a.get("balance", 0.0) or 0.0), remaining)
            a["balance"] = round(float(a.get("balance", 0.0)) - take, 2)
            remaining -= take
        doc.setdefault("liabilities", []).append({
            "kind": "mortgage", "rate": 0.0675, "term_months": 360,
            "balance": money(PRICE - DOWN), "min_payment": 2275.0,
            "orig_date": rc.effective,
        })
        doc.setdefault("constraints", {})["liquidity_floor"] = 18000.0
        return doc, "home_purchase + new mortgage", None, \
            ["all cash accounts", "liabilities:mortgage"]

    def alts(ctx, _rc):
        out = [no_action_alternative(ctx)]
        pf = ctx.get("portfolio_effect") or {}
        cash_now = float(ctx.get("post_cash_usd") or 0.0)
        out.append(make_alternative(
            "ALT-DELAY-PURCHASE", "Delay the purchase 18 months", "policy",
            trades=[], tax_usd=0.0, fee_usd=0.0,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0),
            post_cash_usd=money(cash_now + 42000.0),
            liquidity_months_after=(ctx.get("liquidity_months") or 0.0) + 5.6,
            consequential=True, reversible=True,
            notes=["Preserves the emergency fund; assumes housing supply and "
                   "price are unchanged, which is not modeled."]))
        out.append(make_alternative(
            "ALT-SMALLER-DOWN", "Buy with a 10% down payment instead", "policy",
            trades=[], tax_usd=0.0, fee_usd=0.0,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0),
            post_cash_usd=money(cash_now + 28000.0),
            liquidity_months_after=(ctx.get("liquidity_months") or 0.0) + 3.7,
            consequential=True, reversible=False,
            notes=["Keeps more cash but adds PMI and a higher payment; PMI "
                   "cost is not modeled."]))
        out.append(make_alternative(
            "ALT-PROCEED", "Proceed with the purchase as planned", "policy",
            trades=[], tax_usd=0.0, fee_usd=0.0,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0),
            post_cash_usd=money(cash_now),
            liquidity_months_after=ctx.get("liquidity_months"),
            consequential=True, reversible=False,
            notes=["Leaves the household below its liquidity floor."]))
        return out

    return run_standard(rc, {
        "event_type": "asset.purchase",
        "event_source": "synthetic-transaction-feed",
        "event_payload": {"kind": "primary_residence", "price_usd": money(PRICE),
                          "down_payment_usd": money(DOWN),
                          "note": "SYNTHETIC purchase, no real property"},
        "mutate": mutate,
        "cash_delta": -DOWN,
        "ledger_label": "synthetic home down payment",
        "limits": {"liquidity_months": {"min": 3.0}},
        "alternatives": alts,
        "review_extra": [
            "The purchase is modeled as a pure cash-out; property taxes, "
            "insurance, maintenance and closing costs are excluded and would "
            "widen the shortfall.",
            "The liquidity floor was raised to 18000 as part of the scenario; "
            "that is a scenario input, not a household preference.",
        ],
        "outcome": ("Funding the down payment from cash leaves the household "
                    "below its floor; delay or a smaller down payment is "
                    "recommended and parked at AWAITING-APPROVAL."),
    })


def scenario_07_debt_refinancing(rc):
    """Refinance student debt at a lower rate; closing cost vs NPV."""
    OLD_RATE = 0.068
    NEW_RATE = 0.042
    CLOSING = 750.0

    def mutate(doc, _rc):
        for liab in doc.get("liabilities") or []:
            if liab.get("kind") == "student":
                liab["rate"] = NEW_RATE
        return doc, "debt_refinance(student)", None, ["liability:student"]

    def alts(ctx, _rc):
        out = [no_action_alternative(ctx)]
        pf = ctx.get("portfolio_effect") or {}
        balance = 31500.0
        years = 10
        old_interest = balance * OLD_RATE * years
        new_interest = balance * NEW_RATE * years
        saving = old_interest - new_interest - CLOSING
        out.append(make_alternative(
            "ALT-REFI", "Refinance student debt at %.1f%%" % (NEW_RATE * 100),
            "policy",
            trades=[], tax_usd=0.0, fee_usd=CLOSING,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0),
            post_cash_usd=money((ctx.get("post_cash_usd") or 0.0) - CLOSING),
            liquidity_months_after=ctx.get("liquidity_months"),
            consequential=True, reversible=False,
            notes=["Straight-line interest comparison over %d years; no "
                   "discounting, no prepayment option value, no federal "
                   "benefit forfeiture modeled." % years],
            evidence={"old_rate": OLD_RATE, "new_rate": NEW_RATE,
                      "est_interest_saving_usd": money(saving)}))
        out.append(make_alternative(
            "ALT-ACCELERATED-PAYOFF", "Accelerate payoff from cash flow",
            "policy",
            trades=[], tax_usd=0.0, fee_usd=0.0,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0) + 0.02,
            post_cash_usd=money((ctx.get("post_cash_usd") or 0.0) - 18000.0),
            liquidity_months_after=(ctx.get("liquidity_months") or 0.0) - 2.0,
            consequential=True, reversible=True,
            notes=["Consumes liquidity to save interest; leaves the household "
                   "closer to its floor."]))
        return out

    return run_standard(rc, {
        "event_type": "debt.refinance_offer",
        "event_source": "synthetic-lender-feed",
        "event_payload": {"kind": "student", "old_rate": OLD_RATE,
                          "new_rate": NEW_RATE, "closing_cost_usd": money(CLOSING),
                          "note": "SYNTHETIC offer, fictional lender"},
        "mutate": mutate,
        "cash_delta": -CLOSING,
        "ledger_label": "synthetic refinance closing cost",
        "alternatives": alts,
        "review_extra": [
            "The interest comparison is undiscounted simple interest; a proper "
            "NPV at the household's opportunity cost would be smaller.",
            "Refinancing federal student loans forfeits income-driven "
            "repayment and forgiveness options that are not in the twin.",
        ],
        "outcome": ("Refinancing dominates on the stated objective; the "
                    "recommendation is parked at AWAITING-APPROVAL with the "
                    "forfeited federal benefits flagged as unmodeled."),
    })


def scenario_08_tax_rule_change(rc):
    """Statutory rate change: LTCG 15%->20%, ordinary 24%->28%."""
    NEW_RATES = {"long": 0.20, "short": 0.28}

    def mutate(doc, _rc):
        doc.setdefault("assumptions", {})["tax_rule_change"] = (
            "SYNTHETIC: LTCG 0.15->0.20 and ordinary 0.24->0.28 effective "
            "2027-01-01; modeled as a scenario parameter, not tax advice.")
        return doc, "tax_rule_change (parameter only)", None, ["assumptions"]

    def alts(ctx, _rc):
        out = [no_action_alternative(ctx)]
        pf = ctx.get("portfolio_effect") or {}
        tlh = ctx.get("tax_effect") or {}
        harvestable = float(tlh.get("tlh_loss_usd") or 0.0)
        out.append(make_alternative(
            "ALT-HARVEST-NOW", "Harvest losses before the rate change", "trade",
            trades=[{"side": "SELL", "asset_class": "equity",
                     "notional_usd": money(min(harvestable * 4.0, 120000.0))}],
            tax_usd=0.0, fee_usd=25.44 * 3,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0) + 0.04,
            post_cash_usd=ctx.get("post_cash_usd"),
            liquidity_months_after=ctx.get("liquidity_months"),
            consequential=True, reversible=False,
            notes=["Losses offset gains at the current rate; the benefit "
                   "depends on there being gains to offset, which the twin "
                   "does not project.",
                   "Wash-sale flags are FLAGONLY and single-account."]))
        out.append(make_alternative(
            "ALT-ACCELERATE-GAINS", "Realize gains at the lower current rate",
            "trade",
            trades=[{"side": "SELL", "asset_class": "equity",
                     "notional_usd": 80000.0}],
            tax_usd=80000.0 * 0.05 * 0.15,
            fee_usd=25.44,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0) + 0.03,
            post_cash_usd=ctx.get("post_cash_usd"),
            liquidity_months_after=ctx.get("liquidity_months"),
            consequential=True, reversible=False,
            notes=["Assumes a realized gain of 5% of notional; the actual "
                   "embedded gain is lot-dependent and only partly known."]))
        out.append(rebalance_alternative(
            ctx, "ALT-REBALANCE", "Rebalance under the new rate schedule"))
        return out

    return run_standard(rc, {
        "event_type": "tax.rule_change",
        "event_source": "synthetic-policy-feed",
        "event_payload": {"jurisdiction": "SYNTH-US-FEDERAL",
                          "effective_date": "2027-01-01",
                          "ltcg": NEW_RATES["long"], "ordinary": NEW_RATES["short"],
                          "note": "SYNTHETIC rule change for testing only"},
        "mutate": mutate,
        "cash_delta": 0.0,
        "policy_overrides": {"tax_rates": NEW_RATES},
        "alternatives": alts,
        "review_extra": [
            "This scenario changes a parameter, not a model: no bracket "
            "interaction, NIIT, state tax, or basis-step-up rule is encoded. "
            "taxlot_ext is explicitly FLAGONLY and carries no tax law.",
            "Accelerating realization is only rational if the future rate is "
            "certain and the asset would otherwise be held; neither is shown.",
        ],
        "outcome": ("A synthetic rate change alters the after-tax ranking; "
                    "loss harvesting is recommended and parked at "
                    "AWAITING-APPROVAL with the tax-law scope disclaimed."),
    })


def scenario_09_insurance_gap(rc):
    """Annual review reveals a life-coverage shortfall."""

    def mutate(doc, _rc):
        doc.setdefault("assumptions", {})["insurance_review_date"] = rc.effective
        return doc, "insurance_review", None, ["assumptions"]

    def alts(ctx, _rc):
        out = [no_action_alternative(ctx)]
        pf = ctx.get("portfolio_effect") or {}
        doc = rc.post_doc or rc.base_doc
        income = twin_scenarios._gross_annual_income(doc)
        debts = sum(float(l.get("balance", 0.0) or 0.0)
                    for l in doc.get("liabilities") or [])
        liquid = sum(float(a.get("balance", 0.0) or 0.0)
                     for a in doc.get("accounts") or [])
        need = calcs_ledger.insurance_needs(
            annual_income=income, income_replacement_pct=0.70,
            replacement_years=15, discount_rate=0.04,
            outstanding_debts=debts, final_expenses=25000.0,
            existing_liquid_assets=liquid)
        cover = sum(float(p.get("coverage_amount", 0.0) or 0.0)
                    for p in doc.get("insurance") or [] if p.get("kind") == "life")
        gap = max(0.0, float(need["total_need"]) - cover)
        out.append(make_alternative(
            "ALT-BUY-TERM", "Add term life cover to close the gap", "policy",
            trades=[], tax_usd=0.0, fee_usd=0.0,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0),
            post_cash_usd=money((ctx.get("post_cash_usd") or 0.0) - 2400.0),
            liquidity_months_after=ctx.get("liquidity_months"),
            consequential=True, reversible=False,
            notes=["Premium is a flat annual assumption; underwriting, age "
                   "and health rating are not modeled."],
            evidence={"total_need_usd": money(need["total_need"]),
                      "coverage_gap_usd": money(need["coverage_gap"]),
                      "existing_cover_usd": money(cover),
                      "gap_vs_stated_cover_usd": money(gap)}))
        out.append(make_alternative(
            "ALT-REDUCE-NEED", "Pay down debt to shrink the coverage need",
            "policy",
            trades=[], tax_usd=0.0, fee_usd=0.0,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0) + 0.03,
            post_cash_usd=money((ctx.get("post_cash_usd") or 0.0) - 60000.0),
            liquidity_months_after=(ctx.get("liquidity_months") or 0.0) - 4.0,
            consequential=True, reversible=False,
            notes=["Trades liquidity for a smaller need; the household sits "
                   "closer to its floor."]))
        return out

    return run_standard(rc, {
        "event_type": "insurance.review",
        "event_source": "synthetic-policy-admin",
        "event_payload": {"review_date": rc.effective, "kind": "life",
                          "note": "SYNTHETIC review, fictional policy"},
        "mutate": mutate,
        "cash_delta": -2400.0,
        "ledger_label": "synthetic annual life premium",
        "alternatives": alts,
        "review_extra": [
            "insurance_needs uses a 70% replacement ratio over 15 years at a "
            "4% discount; all three are conventions, and twin_scenarios "
            "independently uses 10x income -- the two disagree by design and "
            "neither is authoritative.",
            "Existing group cover through an employer is not in the twin and "
            "would reduce the gap.",
        ],
        "outcome": ("A life-coverage gap is quantified by two disagreeing "
                    "models; adding term cover is recommended and parked at "
                    "AWAITING-APPROVAL."),
    })


def scenario_10_corporate_spinoff(rc):
    """Parent spins off a subsidiary: basis allocation and price discovery."""
    RATIO = 0.25          # 1 spinCo share per 4 parent shares
    BASIS_TO_SPIN = 0.30  # 30% of parent basis moves to spinCo

    def mutate(doc, _rc):
        for acct in doc.get("accounts") or []:
            for h in acct.get("holdings") or []:
                if h.get("symbol") != "ZPHR":
                    continue
                spin_qty = round(float(h.get("qty", 0.0)) * RATIO, 6)
                spin_lots = []
                keep_lots = []
                for i, lot in enumerate(h.get("tax_lots") or []):
                    lq = float(lot.get("qty", 0.0))
                    cb = float(lot.get("cost_basis", 0.0))
                    spin_lots.append({
                        "acq_date": lot.get("acq_date", rc.effective),
                        "cost_basis": money(cb * BASIS_TO_SPIN),
                        "qty": round(lq * RATIO, 6),
                    })
                    keep_lots.append({
                        "acq_date": lot.get("acq_date", rc.effective),
                        "cost_basis": money(cb * (1.0 - BASIS_TO_SPIN)),
                        "qty": round(lq, 6),
                    })
                h["tax_lots"] = keep_lots
                acct.setdefault("holdings", []).append({
                    "symbol": "ZPHR-SPIN-SYNTH",
                    "qty": spin_qty,
                    "tax_lots": spin_lots,
                })
        doc.setdefault("assumptions", {})["spinoff"] = (
            "SYNTHETIC spinoff: ZPHR distributed 1 ZPHR-SPIN-SYNTH per 4 ZPHR "
            "with %.0f%% of basis allocated to the spinCo. SpinCo has no "
            "reliable mark for the first 3 trading days." % (BASIS_TO_SPIN * 100))
        return doc, "corporate_spinoff(ZPHR -> ZPHR-SPIN-SYNTH)", None, \
            ["holding:ZPHR", "holding:ZPHR-SPIN-SYNTH"]

    def alts(ctx, _rc):
        out = [no_action_alternative(ctx)]
        pf = ctx.get("portfolio_effect") or {}
        out.append(rebalance_alternative(
            ctx, "ALT-TRIM-PARENT", "Trim the parent back under the issuer cap"))
        out.append(make_alternative(
            "ALT-SELL-SPIN", "Sell the spinCo stub", "trade",
            trades=[{"side": "SELL", "ticker": "ZPHR-SPIN-SYNTH@brk-taxable-t",
                     "notional_usd": 45000.0}],
            tax_usd=45000.0 * 0.10 * 0.15,
            fee_usd=25.44,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0) + 0.02,
            post_cash_usd=money((ctx.get("post_cash_usd") or 0.0) + 45000.0),
            liquidity_months_after=ctx.get("liquidity_months"),
            consequential=True, reversible=False,
            notes=["The spinCo mark is a when-issued estimate; the realized "
                   "proceeds are unknown until the stub trades."]))
        out.append(make_alternative(
            "ALT-HOLD-BOTH", "Hold both entities through price discovery",
            "policy",
            trades=[], tax_usd=0.0, fee_usd=0.0,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0),
            post_cash_usd=ctx.get("post_cash_usd"),
            liquidity_months_after=ctx.get("liquidity_months"),
            consequential=False, reversible=True,
            notes=["Defers the decision 3-5 trading days until the stub has "
                   "a reliable mark."]))
        return out

    return run_standard(rc, {
        "event_type": "corporate_action.spinoff",
        "event_source": "synthetic-corporate-actions-feed",
        "event_payload": {"parent": "ZPHR", "spinco": "ZPHR-SPIN-SYNTH",
                          "ratio": RATIO, "basis_to_spinco": BASIS_TO_SPIN,
                          "note": "SYNTHETIC action, fictional issuer"},
        "mutate": mutate,
        "cash_delta": 0.0,
        "alternatives": alts,
        "review_extra": [
            "portfolio_engine keys issuer concentration by the 'issuer' field; "
            "here parent and spinCo carry different issuers, so combined "
            "single-entity exposure after a spinoff can exceed the cap while "
            "each leg passes. That aggregation gap is a real limitation.",
            "The 30% basis split is an assumption; the actual allocation is an "
            "issuer tax election the twin does not carry.",
        ],
        "outcome": ("A synthetic spinoff splits one concentrated issuer into "
                    "two, exposing an issuer-aggregation gap; holding both "
                    "through price discovery is recommended and parked at "
                    "AWAITING-APPROVAL."),
    })


def scenario_11_delisting(rc):
    """A holding is acquired for cash: forced realization and a cash spike."""
    CASH_PER_SHARE = 97.50

    def mutate(doc, _rc):
        realized = 0.0
        proceeds = 0.0
        removed = []
        for acct in doc.get("accounts") or []:
            keep = []
            for h in acct.get("holdings") or []:
                if h.get("symbol") != "DIVARISTO-SYNTH":
                    keep.append(h)
                    continue
                qty = float(h.get("qty", 0.0))
                proceeds += qty * CASH_PER_SHARE
                realized += qty * CASH_PER_SHARE - sum(
                    float(l.get("cost_basis", 0.0)) for l in h.get("tax_lots") or [])
                removed.append(acct.get("id"))
            acct["holdings"] = keep
            if removed and acct.get("id") in removed:
                acct["balance"] = round(
                    float(acct.get("balance", 0.0) or 0.0) + proceeds, 2)
        doc.setdefault("assumptions", {})["delisting"] = (
            "SYNTHETIC cash acquisition of DIVARISTO-SYNTH at %.2f per share; "
            "forced realization of %.2f USD gain." % (CASH_PER_SHARE, realized))
        rc.ctx["forced_realized_gain_usd"] = money(realized)
        rc.ctx["forced_proceeds_usd"] = money(proceeds)
        return doc, "delisting(DIVARISTO-SYNTH) cash merger", None, \
            ["holding:DIVARISTO-SYNTH"]

    def alts(ctx, _rc):
        out = [no_action_alternative(ctx)]
        pf = ctx.get("portfolio_effect") or {}
        proceeds = float(ctx.get("forced_proceeds_usd") or 0.0)
        gain = float(ctx.get("forced_realized_gain_usd") or 0.0)
        out.append(make_alternative(
            "ALT-REINVEST", "Reinvest proceeds back to target weights", "trade",
            trades=[{"side": "BUY", "asset_class": "equity",
                     "notional_usd": money(proceeds)}],
            tax_usd=max(0.0, gain * 0.15),
            fee_usd=25.44 * 2,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=max(0.0, pf.get("drift_before", 0.0) - 0.08),
            post_cash_usd=money(max(0.0, (ctx.get("post_cash_usd") or 0.0))),
            liquidity_months_after=ctx.get("liquidity_months"),
            consequential=True, reversible=True,
            notes=["Restores market exposure; the tax on the forced gain is "
                   "due regardless of what happens next."]))
        out.append(make_alternative(
            "ALT-HOLD-CASH", "Hold the proceeds in cash pending review", "policy",
            trades=[], tax_usd=max(0.0, gain * 0.15), fee_usd=0.0,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0) + 0.06,
            post_cash_usd=ctx.get("post_cash_usd"),
            liquidity_months_after=ctx.get("liquidity_months"),
            consequential=False, reversible=True,
            notes=["Accepts tracking error against target while the household "
                   "decides; the tax bill is identical."]))
        return out

    return run_standard(rc, {
        "event_type": "security.delisted",
        "event_source": "synthetic-corporate-actions-feed",
        "event_payload": {"symbol": "DIVARISTO-SYNTH",
                          "cash_per_share": CASH_PER_SHARE,
                          "reason": "cash_merger",
                          "note": "SYNTHETIC delisting, fictional issuer"},
        "severity": "high",
        "mutate": mutate,
        "cash_delta": 0.0,
        "alternatives": alts,
        "review_extra": [
            "The gain is computed from total lot basis in the twin; the twin "
            "carries no adjustment for return-of-capital or prior wash sales, "
            "so the taxable gain is an estimate.",
        ],
        "outcome": ("A synthetic cash merger forces realization and spikes "
                    "cash; reinvestment is recommended and parked at "
                    "AWAITING-APPROVAL."),
    })


# ---------------------------------------------------------------------------
# 12-15: deliberately adversarial. The correct outcome is SAFE DEGRADED MODE.
# ---------------------------------------------------------------------------

def scenario_12_bad_market_data(rc):
    """Price feed delivers negative, NaN and stale quotes."""
    BAD_TICKS = [
        {"symbol": "TOTMKT-SYNTH", "price": -128.40, "as_of": rc.effective},
        {"symbol": "USAGG-SYNTH", "price": None, "as_of": rc.effective},
        {"symbol": "DIVARISTO-SYNTH", "price": 88.10, "as_of": "2026-05-02"},
        {"symbol": "TOTMKT-SYNTH", "price": float("nan"), "as_of": rc.effective},
        {"symbol": "USAGG-SYNTH", "price": 42.00, "as_of": rc.effective},
    ]

    def mutate(doc, _rc):
        accepted, rejected = [], []
        for t in BAD_TICKS:
            px = t["price"]
            why = None
            if px is None:
                why = "missing price"
            elif isinstance(px, float) and (px != px or px in
                                            (float("inf"), float("-inf"))):
                why = "non-finite price"
            elif float(px) <= 0:
                why = "non-positive price"
            elif t["as_of"] != rc.effective:
                why = "stale as_of %s (expected %s)" % (t["as_of"], rc.effective)
            if why:
                rejected.append({"symbol": t["symbol"], "reason": why})
            else:
                accepted.append(t)
        rc.ctx["tick_validation"] = {
            "total": len(BAD_TICKS),
            "accepted": len(accepted),
            "rejected": len(rejected),
            "rejections": rejected,
        }
        doc.setdefault("assumptions", {})["market_data_quarantine"] = (
            "SYNTHETIC: %d of %d price ticks quarantined on %s; no mark is "
            "trusted for valuation." % (len(rejected), len(BAD_TICKS),
                                        rc.effective))
        return doc, "market_data_quarantine (no valuation applied)", None, \
            ["assumptions"]

    def alts(ctx, _rc):
        return [
            no_action_alternative(
                ctx, notes=["Safe default while marks are unverified: no "
                            "valuation, no trade, no advice."]),
            make_alternative(
                "ALT-QUARANTINE-FEED", "Quarantine the feed and re-request marks",
                "freeze", consequential=False, reversible=True,
                notes=["Operational action only; no financial consequence."],
                objective_suspended_reason="no verified marks",
                evidence=ctx.get("tick_validation")),
            make_alternative(
                "ALT-PUBLISH-PARTIAL-NAV", "Publish a partial NAV with gaps",
                "freeze", consequential=False, reversible=True,
                notes=["Rejected by the skeptical review: a partial NAV reads "
                       "as a confident number."],
                objective_suspended_reason="partial NAV would be misleading"),
        ]

    cfg = {
        "event_type": "market_data.quality_failure",
        "event_source": "synthetic-price-feed",
        "event_payload": {"ticks": len(BAD_TICKS),
                          "defects": ["negative", "null", "stale", "nan"],
                          "note": "SYNTHETIC bad-data injection"},
        "severity": "critical",
        "mutate": mutate,
        "cash_delta": 0.0,
        "alternatives": alts,
        "review_extra": [
            "No valuation is published in this scenario. Any number produced "
            "from these ticks would be a guess presented as a measurement.",
            "The quarantine itself is unverified: the harness assumes the "
            "defect list is complete, which no feed guarantees.",
        ],
        "outcome": ("Bad ticks are quarantined, every valuation stage is "
                    "BLOCKED, and the system reports SAFE DEGRADED MODE with "
                    "no net-worth or risk number."),
    }
    rc_pre = rc
    return _run_degraded(rc_pre, cfg,
                         reason="market data unverified: 4 of 5 ticks rejected",
                         disclosure=("SAFE DEGRADED MODE -- valuation, tax and "
                                     "risk outputs are withheld because the "
                                     "price feed failed validation. No figure "
                                     "in this artifact should be used as a "
                                     "net-worth or risk measurement."),
                         blocked=("PORTFOLIO_EFFECT", "TAX_EFFECT",
                                  "RISK_EFFECT", "GOAL_EFFECT"))


def scenario_13_provider_outage(rc):
    """Custodian API outage: 3 of 5 accounts unreachable."""

    def alts(ctx, _rc):
        return [
            no_action_alternative(
                ctx, notes=["No order can be placed against an account whose "
                            "balance is unknown."]),
            make_alternative(
                "ALT-RETRY-LATER", "Retry the custodian after the outage window",
                "freeze", consequential=False, reversible=True,
                notes=["Operational retry only."],
                objective_suspended_reason="custody data unavailable"),
            make_alternative(
                "ALT-USE-LAST-KNOWN", "Trade on last-known-good balances",
                "freeze", consequential=False, reversible=True,
                notes=["Rejected: stale balances would silently mis-size every "
                       "order."],
                objective_suspended_reason="stale balances must not size orders"),
        ]

    cfg = {
        "event_type": "provider.outage",
        "event_source": "synthetic-custodian-gateway",
        "event_payload": {"provider": "SYNTH-CUSTODIAN-WEST",
                          "status": 503,
                          "accounts_total": 5, "accounts_unreachable": 3,
                          "note": "SYNTHETIC outage"},
        "severity": "critical",
        "mutate": lambda doc, _rc: (doc, "provider outage (twin frozen)", None,
                                    ["provider:SYNTH-CUSTODIAN-WEST"]),
        "freeze_twin": True,
        "cash_delta": 0.0,
        "alternatives": alts,
        "review_extra": [
            "Coverage is 2 of 5 accounts. Any household-level figure computed "
            "from that subset is a partial measurement, not a total.",
            "The outage duration is unknown; the harness cannot say when "
            "coverage returns.",
        ],
        "outcome": ("A custodian outage leaves 2 of 5 accounts visible; the "
                    "twin freeze and every value-dependent stage is BLOCKED "
                    "and the system reports SAFE DEGRADED MODE."),
    }
    return _run_degraded(rc, cfg,
                         reason="custodian outage: 3 of 5 accounts unreachable",
                         disclosure=("SAFE DEGRADED MODE -- the twin is frozen "
                                     "and no household-level total, liquidity "
                                     "figure or trade is produced on partial "
                                     "custody coverage."),
                         blocked=("PORTFOLIO_EFFECT", "TAX_EFFECT",
                                  "LIQUIDITY_EFFECT", "RISK_EFFECT"))


def scenario_14_model_degradation(rc):
    """Forecasting model's out-of-sample hit rate collapses."""
    FLOOR = 0.45

    def mutate(doc, _rc):
        rng = random.Random(rc.seed + 14)
        window = [1 if rng.random() < 0.62 else 0 for _ in range(40)]
        recent = [1 if rng.random() < 0.28 else 0 for _ in range(20)]
        hit = (sum(window) + sum(recent)) / float(len(window) + len(recent))
        rc.ctx["model_hit_rate"] = round(hit, 4)
        rc.ctx["model_hit_rate_baseline"] = round(sum(window) / float(len(window)), 4)

        rec = {
            "cohort_id": "W8-S14",
            "as_of": rc.effective,
            "model_version": obs.MODEL_VERSION_DEFAULT,
            "dataset_version": rc.dataset_version,
            "hit_rate_recent": round(sum(recent) / float(len(recent)), 4),
            "hit_rate_baseline": round(sum(window) / float(len(window)), 4),
            "confidence": round(hit, 4),
            "note": "SYNTHETIC out-of-sample diagnostic, no live prediction",
        }
        rec["prev_record_hash"] = "GENESIS"
        rec["record_hash"] = shadow.record_hash(rec)
        ok, bad = shadow.verify_chain([rec])
        rc.ctx["shadow_record"] = {
            "record": ascii_safe(rec),
            "chain_ok": bool(ok),
            "first_bad_index": bad,
            "chain_verified_with": "shadow.verify_chain",
        }
        doc.setdefault("assumptions", {})["model_health"] = (
            "SYNTHETIC: hit rate %.3f over 60 observations against a %.2f "
            "floor; new model-driven actions are suppressed." % (hit, FLOOR))
        return doc, "model_health_diagnostic (no twin value change)", None, \
            ["assumptions"]

    def alts(ctx, _rc):
        out = [no_action_alternative(
            ctx, notes=["Default when the model is outside its validated "
                        "envelope: do nothing that depends on it."])]
        out.append(make_alternative(
            "ALT-REVALIDATE-MODEL", "Re-validate the model before reuse",
            "freeze", consequential=False, reversible=True,
            notes=["Operational: re-run the walk-forward suite on a fresh "
                   "window before any prediction is published."],
            objective_suspended_reason="model outside validated envelope",
            evidence=ctx.get("shadow_record")))
        out.append(make_alternative(
            "ALT-REDUCE-SIZE", "Continue with reduced position sizing",
            "freeze", consequential=False, reversible=True,
            notes=["Rejected: a degraded model does not become safe at a "
                   "smaller size; the error is in the estimate, not the scale."],
            objective_suspended_reason="model outside validated envelope"))
        return out

    cfg = {
        "event_type": "model.degradation",
        "event_source": "synthetic-model-monitor",
        "event_payload": {"model": obs.MODEL_VERSION_DEFAULT,
                          "hit_rate_floor": FLOOR,
                          "observations": 60,
                          "note": "SYNTHETIC degradation signal"},
        "severity": "critical",
        "mutate": mutate,
        "cash_delta": 0.0,
        "alternatives": alts,
        "review_extra": [
            "The 40/20 observation split is synthetic; a real degradation test "
            "needs a pre-registered window and an out-of-sample cut the "
            "harness does not own.",
            "Suppressing a model does not make the household's position safe; "
            "it only stops adding model-driven error.",
        ],
        "outcome": ("Out-of-sample hit rate falls below the floor; the kill "
                    "switch trips, new model-driven actions are suppressed, "
                    "and all 18 stages still execute in SAFE DEGRADED MODE."),
    }
    return _run_degraded(
        rc, cfg,
        reason="model hit rate below floor; model-driven actions suppressed",
        disclosure=("SAFE DEGRADED MODE -- the forecasting model is outside "
                    "its validated envelope. Numeric stages below are computed "
                    "from custody data and remain valid, but no model-driven "
                    "recommendation is produced."),
        blocked=("MODEL_DRIVEN_ACTION",),
        limits={"liquidity_months": {"min": 3.0},
                "model_hit_rate": {"min": FLOOR}})


def scenario_15_security_incident(rc):
    """Suspected credential compromise on a custodian connection."""

    def alts(ctx, _rc):
        return [
            no_action_alternative(
                ctx, notes=["No financial movement during an open incident: "
                            "that is the controlled response."]),
            make_alternative(
                "ALT-REVOKE-CREDENTIALS", "Revoke tokens and force re-auth",
                "freeze", consequential=False, reversible=False,
                notes=["Operational containment; no financial consequence."],
                objective_suspended_reason="security incident open"),
            make_alternative(
                "ALT-FREEZE-ORDERS", "Freeze all outbound order routing",
                "freeze", consequential=False, reversible=True,
                notes=["Containment until the incident is closed."],
                objective_suspended_reason="security incident open"),
        ]

    cfg = {
        "event_type": "security.incident",
        "event_source": "synthetic-soc",
        "event_payload": {"incident_id": "SYNTH-INC-2026-0828",
                          "kind": "suspected_credential_compromise",
                          "scope": ["SYNTH-CUSTODIAN-WEST"],
                          "containment": "order_routing_frozen",
                          "note": "SYNTHETIC incident, no real system"},
        "severity": "critical",
        "mutate": lambda doc, _rc: (doc, "security incident (twin frozen)",
                                    None, ["security:order_routing"]),
        "freeze_twin": True,
        "cash_delta": 0.0,
        "alternatives": alts,
        "review_extra": [
            "The harness cannot verify the scope of a compromise; assuming the "
            "blast radius is one custodian is itself an unverified claim.",
            "Read-only computation continues, but every read may be against "
            "data an attacker could have altered.",
        ],
        "outcome": ("A suspected credential compromise freezes order routing "
                    "and the twin; value-dependent stages are BLOCKED and the "
                    "system reports SAFE DEGRADED MODE with containment only."),
    }
    return _run_degraded(
        rc, cfg,
        reason="security incident open: order routing frozen",
        disclosure=("SAFE DEGRADED MODE -- no order can be routed and the twin "
                    "is frozen while incident SYNTH-INC-2026-0828 is open. "
                    "Reads below are last-known-good and may be untrustworthy."),
        blocked=("PORTFOLIO_EFFECT", "TAX_EFFECT"))


def _run_degraded(rc, cfg, reason, disclosure, blocked=(), limits=None):
    """Wrapper for adversarial scenarios: engage degraded mode, then run."""
    rc.degraded.engage(reason, disclosure, blocked)
    rc.findings.extend(
        [f for f in KNOWN_FINDINGS if f["finding_id"] == "W8-F4"])
    if limits:
        cfg["limits"] = limits
    return run_standard(rc, cfg)


# ---------------------------------------------------------------------------
# 16-18
# ---------------------------------------------------------------------------

def scenario_16_conflicting_goals(rc):
    """Two essential/high goals compete for the same marginal dollar."""

    def mutate(doc, _rc):
        for g in doc.get("goals") or []:
            if g.get("id") == "g-mg-college-m3":
                g["target_amount"] = 240000.0
        doc.setdefault("assumptions", {})["goal_conflict"] = (
            "SYNTHETIC: college funding requirement raised to 240000, in "
            "direct conflict with the retirement and caregiving goals.")
        return doc, "goal_conflict(college vs retirement vs caregiving)", None, \
            ["goal:g-mg-college-m3"]

    def alts(ctx, _rc):
        out = [no_action_alternative(ctx)]
        pf = ctx.get("portfolio_effect") or {}
        cash_now = float(ctx.get("post_cash_usd") or 0.0)
        spend = float((ctx.get("liquidity_effect") or {}).get("monthly_spend") or 7500.0)
        base = dict(drift_before=pf.get("drift_before", 0.0),
                    liquidity_months_after=ctx.get("liquidity_months"))
        out.append(make_alternative(
            "ALT-FUND-COLLEGE", "Prioritise the 529 for the student", "policy",
            trades=[], tax_usd=0.0, fee_usd=0.0,
            drift_after=pf.get("drift_before", 0.0) + 0.04,
            post_cash_usd=money(cash_now - spend * 12 * 0.25),
            consequential=True, reversible=True,
            notes=["Directly conflicts with g-mg-retire-together (essential)."],
            **base))
        out.append(make_alternative(
            "ALT-FUND-RETIREMENT", "Prioritise retirement contributions",
            "policy",
            trades=[], tax_usd=0.0, fee_usd=0.0,
            drift_after=pf.get("drift_before", 0.0) + 0.01,
            post_cash_usd=money(cash_now - spend * 12 * 0.25),
            consequential=True, reversible=True,
            notes=["Directly conflicts with g-mg-college-m3 (high)."],
            **base))
        out.append(make_alternative(
            "ALT-FUND-CAREGIVING", "Prioritise the caregiving reserve", "policy",
            trades=[], tax_usd=0.0, fee_usd=0.0,
            drift_after=pf.get("drift_before", 0.0) + 0.03,
            post_cash_usd=money(cash_now - spend * 12 * 0.25),
            consequential=True, reversible=True,
            notes=["Caregiving timing is uncertain; the reserve may be needed "
                   "before either other goal."],
            **base))
        out.append(make_alternative(
            "ALT-SPLIT", "Split the marginal dollar three ways", "policy",
            trades=[], tax_usd=0.0, fee_usd=0.0,
            drift_after=pf.get("drift_before", 0.0) + 0.02,
            post_cash_usd=money(cash_now - spend * 12 * 0.25),
            consequential=True, reversible=True,
            notes=["Underfunds all three; the conflict is deferred, not "
                   "resolved."],
            **base))
        return out

    return run_standard(rc, {
        "event_type": "goal.conflict",
        "event_source": "synthetic-planning-review",
        "event_payload": {"goals": ["g-mg-retire-together", "g-mg-college-m3",
                                    "g-mg-care-for-parents"],
                          "note": "SYNTHETIC conflict, fictional goals"},
        "mutate": mutate,
        "cash_delta": -22500.0,
        "ledger_label": "synthetic incremental college funding",
        "alternatives": alts,
        "review_extra": [
            "This is a genuine value conflict, not a calculation error: the "
            "alternatives are mutually exclusive and no objective function "
            "here can rank them without a household preference the twin does "
            "not contain.",
            "The objective function ranks these only on liquidity and drift, "
            "which is the wrong axis for a goal-priority decision; the ranking "
            "should be read as inconclusive.",
        ],
        "outcome": ("Three competing goals are surfaced with an explicit "
                    "irresolution disclosure; a recommendation is made on the "
                    "weak liquidity axis only and parked at AWAITING-APPROVAL."),
    })


def scenario_17_estate_transition(rc):
    """Death of a member: beneficiary redistribution and estate goals."""

    def mutate(doc, _rc):
        # SAFETY PROPERTY FIRST. An account solely owned by the decedent with
        # NO beneficiary designation must be REFUSED outright -- the system
        # must never infer who inherits. mg-529-m3-t is solely owned by m1 and
        # is deliberately omitted from this first map. The scenario ASSERTS
        # the refusal rather than quietly completing the transition, so the
        # fail-closed property is exercised on every run instead of assumed.
        partial = {"mg-401k-m1-t": "m2", "mg-joint-cash-t": "m2"}
        try:
            twin_identity.death(doc, "m1", partial, rc.effective)
        except ValueError as exc:
            if "beneficiary_map" not in str(exc):
                raise
            _rc.notes.append(
                "fail-closed verified: death() REFUSED an incomplete "
                "beneficiary designation for solely-owned account "
                "mg-529-m3-t (%s)" % exc)
        else:
            raise AssertionError(
                "death() completed with an INCOMPLETE beneficiary_map: "
                "solely-owned account mg-529-m3-t had no designation and the "
                "engine did not refuse. Beneficiary designation must never "
                "be inferred; this is a fail-closed violation.")
        # The executor now supplies a COMPLETE designation, and only then may
        # the estate transition proceed.
        bmap = {"mg-401k-m1-t": "m2", "mg-joint-cash-t": "m2",
                "mg-529-m3-t": "m2"}
        tr = twin_identity.death(doc, "m1", bmap, rc.effective)
        new_doc = tr["new_doc"]
        est = new_doc.setdefault("estate_intentions", {})
        est["will_status"] = "signed"
        est["beneficiary_reviewed"] = True
        return (
            new_doc,
            "death(m1) + beneficiary redistribution (fail-closed refusal "
            "on incomplete designation verified first)",
            tr["events"][0],
            ["member:m1", "account:mg-401k-m1-t", "account:mg-joint-cash-t",
             "account:mg-529-m3-t"],
        )

    def alts(ctx, _rc):
        out = [no_action_alternative(ctx)]
        pf = ctx.get("portfolio_effect") or {}
        out.append(rebalance_alternative(
            ctx, "ALT-REBALANCE-SURVIVOR",
            "Rebalance the survivor portfolio to target"))
        out.append(make_alternative(
            "ALT-UPDATE-BENEFICIARIES", "Update contingent beneficiaries",
            "policy",
            trades=[], tax_usd=0.0, fee_usd=0.0,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0),
            post_cash_usd=ctx.get("post_cash_usd"),
            liquidity_months_after=ctx.get("liquidity_months"),
            consequential=True, reversible=False,
            notes=["Estate documents are outside this system; this is a "
                   "trigger for professional review, not an instruction."]))
        out.append(make_alternative(
            "ALT-CLAIM-LIFE", "Claim the life policy benefit into cash", "policy",
            trades=[], tax_usd=0.0, fee_usd=0.0,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0) + 0.05,
            post_cash_usd=money((ctx.get("post_cash_usd") or 0.0) + 900000.0),
            liquidity_months_after=(ctx.get("liquidity_months") or 0.0) + 40.0,
            consequential=True, reversible=False,
            notes=["Proceeds modeled at the stated coverage amount; claim "
                   "adjudication timing is not modeled."],
            evidence={"life_coverage_usd": 900000.0}))
        return out

    return run_standard(rc, {
        "event_type": "identity.death",
        "event_source": "synthetic-vital-records",
        "event_payload": {"member": "m1", "effective_date": rc.effective,
                          "beneficiary_map": {"mg-401k-m1-t": "m2"},
                          "note": "SYNTHETIC event, fictional person"},
        "severity": "high",
        "mutate": mutate,
        "cash_delta": 900000.0,
        "ledger_label": "synthetic life policy proceeds",
        "alternatives": alts,
        "review_extra": [
            "twin_identity.death redistributes ownership only: balances and "
            "quantities never change, so household liquidity cannot increase "
            "from the transition itself. Any liquidity change here comes from "
            "the (modeled, unadjudicated) life claim.",
            "Estate tax, probate and spousal election rights are entirely "
            "outside this harness; the professional-review trigger is the only "
            "honest output on those points.",
        ],
        "outcome": ("A death transition redistributes ownership with zero "
                    "value change; the life-claim alternative dominates on "
                    "liquidity and is parked at AWAITING-APPROVAL with estate "
                    "questions explicitly deferred to professionals."),
    })


def scenario_18_no_action_best(rc):
    """Periodic review where every correction costs more than it is worth."""

    def mutate(doc, _rc):
        doc.setdefault("assumptions", {})["periodic_review"] = (
            "SYNTHETIC periodic review on %s; no external event." % rc.effective)
        return doc, "periodic_review (no external event)", None, ["assumptions"]

    def alts(ctx, _rc):
        out = [no_action_alternative(
            ctx, notes=["No external event: the only case for acting is the "
                        "assumed rebalancing premium."])]
        pf = ctx.get("portfolio_effect") or {}
        out.append(rebalance_alternative(ctx))
        tax = ctx.get("tax_effect") or {}
        harvestable = float(tax.get("tlh_loss_usd") or 0.0)
        out.append(make_alternative(
            "ALT-TLH", "Harvest the largest available loss", "trade",
            trades=[{"side": "SELL", "asset_class": "equity",
                     "notional_usd": money(min(harvestable * 3.0, 60000.0))}],
            tax_usd=0.0, fee_usd=25.44,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=pf.get("drift_before", 0.0) + 0.05,
            post_cash_usd=ctx.get("post_cash_usd"),
            liquidity_months_after=ctx.get("liquidity_months"),
            consequential=True, reversible=False,
            notes=["A harvested loss is only worth the tax it offsets; the "
                   "twin carries no realized-gain forecast to offset against.",
                   "Wash-sale status is FLAGONLY and single-account."]))
        out.append(make_alternative(
            "ALT-SHIFT-TO-BONDS", "Move 5% from equity to bonds", "trade",
            trades=[{"side": "SELL", "asset_class": "equity", "notional_usd": 43611.0},
                    {"side": "BUY", "asset_class": "bonds", "notional_usd": 43611.0}],
            tax_usd=43611.0 * 0.52 * 0.15,
            fee_usd=25.44 * 2,
            drift_before=pf.get("drift_before", 0.0),
            drift_after=max(0.0, pf.get("drift_before", 0.0) - 0.10),
            post_cash_usd=ctx.get("post_cash_usd"),
            liquidity_months_after=ctx.get("liquidity_months"),
            consequential=True, reversible=True,
            notes=["Assumes 52% embedded gain on the equity sold; the real "
                   "figure is lot-dependent.",
                   "This is a directional allocation change, outside a purely "
                   "band-triggered mandate."]))
        return out

    return run_standard(rc, {
        "event_type": "review.periodic",
        "event_source": "synthetic-scheduler",
        "event_payload": {"review_date": rc.effective,
                          "note": "SYNTHETIC scheduled review, no external shock"},
        "mutate": mutate,
        "cash_delta": 0.0,
        "alternatives": alts,
        "review_extra": [
            "The whole case for acting rests on a 40bp rebalancing premium. "
            "If that constant is wrong, every trade alternative here is value "
            "destroying, and the harness cannot estimate it from this data.",
            "No external trigger exists for this scenario; the review is "
            "scheduler-driven, which is the weakest possible reason to trade.",
        ],
        "outcome": ("On the stated objective NO-ACTION WINS: every correction "
                    "costs more in concrete tax and execution cost than the "
                    "assumed rebalancing premium returns, so nothing is "
                    "recommended and no approval is required."),
    })


# ===========================================================================
# Registry
# ===========================================================================

OBJECTIVE = {
    "id": "obj.after-tax-risk-adjusted-12m",
    "statement": ("Maximise the 12-month after-tax, after-cost risk-adjusted "
                  "outcome subject to the household liquidity floor."),
    "metric": "objective_usd",
    "horizon_months": 12,
}

SCENARIOS = [
    ("S01", "Job loss + market crash", "hh-multigenerational", 101,
     scenario_01_job_loss_market_crash),
    ("S02", "Employer equity + vesting and taxes", "hh-tech-accumulator", 102,
     scenario_02_employer_equity_vesting),
    ("S03", "Rate shock", "hh-business-owner", 103, scenario_03_rate_shock),
    ("S04", "Retirement before a crash", "hh-multigenerational", 104,
     scenario_04_retirement_before_crash),
    ("S05", "Healthcare shock", "hh-multigenerational", 105,
     scenario_05_healthcare_shock),
    ("S06", "Home purchase", "hh-early-career", 106, scenario_06_home_purchase),
    ("S07", "Debt refinancing", "hh-leveraged-young", 107,
     scenario_07_debt_refinancing),
    ("S08", "Tax-rule change", "hh-business-owner", 108,
     scenario_08_tax_rule_change),
    ("S09", "Insurance gap", "hh-multigenerational", 109,
     scenario_09_insurance_gap),
    ("S10", "Corporate spinoff", "hh-tech-accumulator", 110,
     scenario_10_corporate_spinoff),
    ("S11", "Delisting", "hh-estate-transition", 111, scenario_11_delisting),
    ("S12", "Bad market data", "hh-estate-transition", 112,
     scenario_12_bad_market_data),
    ("S13", "Provider outage", "hh-business-owner", 113,
     scenario_13_provider_outage),
    ("S14", "Model degradation", "hh-conservative-retiree", 114,
     scenario_14_model_degradation),
    ("S15", "Security incident", "hh-early-career", 115,
     scenario_15_security_incident),
    ("S16", "Conflicting goals", "hh-multigenerational", 116,
     scenario_16_conflicting_goals),
    ("S17", "Estate transition", "hh-multigenerational", 117,
     scenario_17_estate_transition),
    ("S18", "No action as the best option", "hh-tech-accumulator", 118,
     scenario_18_no_action_best),
]


def run_scenario(sid, out_dir=OUT_DIR):
    """Run one scenario by id; returns the artifact dict."""
    entry = next((s for s in SCENARIOS if s[0] == sid), None)
    if entry is None:
        raise KeyError("unknown scenario %r" % sid)
    sid, title, household, seed, fn = entry
    rc = ScenarioRunner(sid, title, household, seed, OBJECTIVE, out_dir=out_dir)
    rc.base_doc = load_household(household)
    fn(rc)
    if not hasattr(rc, "artifact"):
        rc.finish("scenario returned without finalising")
    return rc


def run_all(out_dir=OUT_DIR, verbose=True):
    """Run every scenario; returns {sid: ScenarioRunner}."""
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(STATE_DIR, exist_ok=True)
    runners = {}
    for sid, title, household, seed, fn in SCENARIOS:
        rc = ScenarioRunner(sid, title, household, seed, OBJECTIVE,
                            out_dir=out_dir)
        rc.base_doc = load_household(household)
        try:
            fn(rc)
        except Exception as exc:
            sys.stderr.write("%s aborted: %s: %s\n"
                             % (sid, type(exc).__name__, exc))
        if not hasattr(rc, "artifact"):
            rc.finish("scenario returned without finalising")
        runners[sid] = rc
        if verbose:
            art = rc.artifact
            print("%s  %-38s terminal=%-24s stages=%s"
                  % (sid, title[:38], art["terminal_state"],
                     ",".join("%s:%s" % (k, art["stage_counts"][k])
                              for k in sorted(art["stage_counts"]))))
    _write_index(runners, out_dir)
    _write_blocking_findings(out_dir)
    return runners


def _write_index(runners, out_dir):
    rows = []
    for sid, _t, household, seed, _fn in SCENARIOS:
        rc = runners.get(sid)
        if rc is None:
            continue
        art = rc.artifact
        rows.append({
            "scenario_id": sid,
            "title": art["title"],
            "household": household,
            "seed": seed,
            "terminal_stage_status": art["terminal_stage"]["status"],
            "terminal_state": art["terminal_state"],
            "stage_counts": art["stage_counts"],
            "no_action_present": art["no_action_present"],
            "selected_alternative_id": art["selected_alternative_id"],
            "executed_financial_action": art["executed_financial_action"],
            "degraded": art["degraded_mode"]["active"],
            "confidence": (art.get("skeptical_review") or {}).get("confidence"),
            "determinism_digest": art["determinism_digest"],
            "outcome": art["outcome"],
        })
    body = {
        "harness": {"id": HARNESS_ID, "version": HARNESS_VERSION},
        "data_classification": DATA_CLASSIFICATION,
        "synthetic": True,
        "sim_clock": SIM_CLOCK,
        "scenario_count": len(rows),
        "scenarios": rows,
    }
    with open(os.path.join(out_dir, "INDEX.json"), "w", encoding="ascii") as fh:
        json.dump(body, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return body


def _write_blocking_findings(out_dir):
    lines = [
        "# BLOCKING FINDINGS -- W8 Cross-Domain End-to-End Scenarios",
        "",
        "Discovered while wiring tools/fis/scenarios_e2e.py. The W8 agent owns",
        "only scenarios_e2e.py, test_scenarios_e2e.py and _work/fis-data/scenarios/;",
        "none of the modules below were modified. Each finding is recorded here",
        "with file:line, evidence, and a recommended fix, and the affected",
        "scenario artifacts record the degradation rather than papering over it.",
        "",
        "Data classification: SYNTHETIC-NOT-USER-DATA. Every fixture referenced",
        "is a synthetic household; no real person, account or market data is",
        "involved.",
        "",
        "---",
        "",
    ]
    for f in KNOWN_FINDINGS:
        lines.extend([
            "## %s -- %s" % (f["finding_id"], f["title"]),
            "",
            "- Severity: %s" % f["severity"],
            "- Module: %s" % f["module"],
            "- Location: %s" % f["location"],
            "",
            "%s" % f["detail"],
            "",
            "Evidence: %s" % f["evidence"],
            "",
            "Recommended fix: %s" % f["recommended_fix"],
            "",
        ])
    lines.extend([
        "---",
        "",
        "## How W8 compensated",
        "",
        "- scenarios_e2e.py does NOT use twin_scenarios._holdings_mv or",
        "  net_worth()['reconciles'] for any valuation. It builds its own price",
        "  table (NOMINAL_PRICES) and rescales per account so the derived",
        "  portfolio ties to the twin's stated balance.",
        "- Every artifact records twin_scenarios.net_worth()['reconciles'] as a",
        "  model-disagreement note in the skeptical review (stage 15) when it",
        "  is False, so the degradation is visible rather than hidden.",
        "- risk_engine results are consumed but their wall-clock 'staleness'",
        "  field is never asserted on; the harness uses its own fixed sim clock.",
        "",
        "## Stages that are scaffolded rather than deep",
        "",
        "- Stages 8-12 call real engines, but the scenario 'physics' (job loss",
        "  draws, rate-shock duration repricing, out-of-pocket medical draws)",
        "  are hand-written transforms in this file, not calibrated models.",
        "- The objective function is a single scalar with two hard-coded",
        "  constants (REBALANCE_PREMIUM, LIQUIDITY_PENALTY_RATE). It is a",
        "  decision-rank demonstrator, not an optimizer.",
        "- Alternatives are constructed per scenario from the engines' outputs;",
        "  their trade lists for policy alternatives (insurance, refinancing,",
        "  goal funding) are declarative descriptions, not executable orders.",
        "",
    ])
    path = os.path.join(out_dir, "BLOCKING-FINDINGS.md")
    with open(path, "w", encoding="ascii") as fh:
        fh.write("\n".join(lines))
    return path


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    only = None
    if "--only" in argv:
        only = argv[argv.index("--only") + 1]
    if only:
        rc = run_scenario(only)
        art = rc.artifact
        print("scenario=%s terminal_state=%s terminal_stage=%s"
              % (only, art["terminal_state"], art["terminal_stage"]["status"]))
        for rec in art["stages"]:
            print("  %2d %-26s %-22s %s"
                  % (rec["index"], rec["stage"], rec["status"], rec["summary"][:90]))
        return 0
    runners = run_all()
    bad = [sid for sid, rc in runners.items()
           if rc.artifact["stage_counts"].get(S_FAILED)]
    print("")
    print("scenarios=%d failed=%d" % (len(runners), len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
