#!/usr/bin/env python3
"""Human-approval state machine for consequential financial decisions.

WHY THIS MODULE EXISTS
----------------------
`portfolio_engine.propose_rebalance()` returns SELL/BUY legs. Before this
module existed nothing in the system distinguished *analysing* a trade
from *authorising* one: the proposal object looked complete, carried a
status of "proposed", and could be handed to an execution surface with no
refusal path anywhere. That is finding GOV-NO-HUMAN-APPROVAL-GATE (W3,
HIGH). The mitigation "a constraint gate can reject it afterwards" is not
an approval control -- it is a post-hoc filter on an object that should
never have been executable in the first place.

This module is the single owner of the answer to "may this be acted on?".

THE CENTRAL RULE
----------------
Under the authority granted by the operator for this program, the
ceiling is `APPROVED_FOR_SIMULATION`. `APPROVED_FOR_EXECUTION`,
`EXECUTED` and `RECONCILED` exist in the state enum because the lifecycle
requires them, but the transition table contains NO inbound edge to
`APPROVED_FOR_EXECUTION`, and therefore none to `EXECUTED` or
`RECONCILED` either. They are declared and unreachable. Raising the
ceiling is an operator decision, not a code decision, and
`test_approval_state_machine.py` asserts the unreachability so a future
edit cannot add the edge quietly.

WHAT AN APPROVAL IS
-------------------
An approval is an HMAC-signed `ApprovalGrant` bound to a content
fingerprint of the exact decision: its legs (instrument, side, quantity,
price or limit, account), the model version, the data version, the policy
version, the code hash, the price as-of date, the expiry, and the
approver's identity. Change any of those and the fingerprint changes, the
grant no longer matches, and the record is INVALIDATED -- not warned
about, invalidated.

Approval is NEVER inferred from:
  * a boolean that defaults to true      -- no such field exists here;
  * the presence of an approval file     -- a file is evidence only after
                                           its signature verifies;
  * an agent's statement                 -- agent identities are in
                                           NON_HUMAN_IDENTITIES and are
                                           refused as approvers;
  * a prior approval                     -- a grant is consumed on use and
                                           cannot be replayed.

Stdlib only. ASCII only. No network access.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import tempfile
import threading
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

APPROVAL_RULE_VERSION = "APPROVAL-STATE-MACHINE-v2"

ADVISORY_LABEL = "NOT-AUTHORIZED-FOR-EXECUTION"

# ---------------------------------------------------------------------------
# States
# ---------------------------------------------------------------------------

STATE_DRAFT_ANALYSIS = "DRAFT_ANALYSIS"
STATE_VALIDATED_ALTERNATIVES = "VALIDATED_ALTERNATIVES"
STATE_RECOMMENDATION_PENDING_REVIEW = "RECOMMENDATION_PENDING_REVIEW"
STATE_HUMAN_APPROVAL_REQUIRED = "HUMAN_APPROVAL_REQUIRED"
STATE_APPROVED_FOR_SIMULATION = "APPROVED_FOR_SIMULATION"
STATE_APPROVED_FOR_EXECUTION = "APPROVED_FOR_EXECUTION"
STATE_REJECTED = "REJECTED"
STATE_EXPIRED = "EXPIRED"
STATE_INVALIDATED = "INVALIDATED"
STATE_EXECUTED = "EXECUTED"
STATE_RECONCILED = "RECONCILED"

ALL_STATES: Tuple[str, ...] = (
    STATE_DRAFT_ANALYSIS,
    STATE_VALIDATED_ALTERNATIVES,
    STATE_RECOMMENDATION_PENDING_REVIEW,
    STATE_HUMAN_APPROVAL_REQUIRED,
    STATE_APPROVED_FOR_SIMULATION,
    STATE_APPROVED_FOR_EXECUTION,
    STATE_REJECTED,
    STATE_EXPIRED,
    STATE_INVALIDATED,
    STATE_EXECUTED,
    STATE_RECONCILED,
)

# Ranking used to compare against the ceiling.
_STATE_RANK: Dict[str, int] = {
    STATE_DRAFT_ANALYSIS: 0,
    STATE_VALIDATED_ALTERNATIVES: 1,
    STATE_RECOMMENDATION_PENDING_REVIEW: 2,
    STATE_HUMAN_APPROVAL_REQUIRED: 3,
    STATE_APPROVED_FOR_SIMULATION: 4,
    STATE_APPROVED_FOR_EXECUTION: 5,
    STATE_EXECUTED: 6,
    STATE_RECONCILED: 7,
    # Terminal non-authorising states rank below every authorising state so
    # that "is this at or under the ceiling" is never true for them by rank.
    STATE_REJECTED: -1,
    STATE_EXPIRED: -1,
    STATE_INVALIDATED: -1,
}

# The authority actually granted. Everything above this is unreachable.
AUTHORITY_CEILING = STATE_APPROVED_FOR_SIMULATION

# ---------------------------------------------------------------------------
# Transition table. NOTE the empty inbound sets: see module docstring.
# ---------------------------------------------------------------------------

ALLOWED_TRANSITIONS: Dict[str, FrozenSet[str]] = {
    STATE_DRAFT_ANALYSIS: frozenset({
        STATE_VALIDATED_ALTERNATIVES, STATE_REJECTED, STATE_INVALIDATED}),
    STATE_VALIDATED_ALTERNATIVES: frozenset({
        STATE_RECOMMENDATION_PENDING_REVIEW, STATE_DRAFT_ANALYSIS,
        STATE_REJECTED, STATE_INVALIDATED}),
    STATE_RECOMMENDATION_PENDING_REVIEW: frozenset({
        STATE_HUMAN_APPROVAL_REQUIRED, STATE_DRAFT_ANALYSIS,
        STATE_REJECTED, STATE_INVALIDATED}),
    STATE_HUMAN_APPROVAL_REQUIRED: frozenset({
        STATE_APPROVED_FOR_SIMULATION, STATE_REJECTED, STATE_EXPIRED,
        STATE_INVALIDATED}),
    STATE_APPROVED_FOR_SIMULATION: frozenset({
        STATE_RECOMMENDATION_PENDING_REVIEW, STATE_EXPIRED,
        STATE_INVALIDATED, STATE_REJECTED}),
    # NO inbound edge. Declared, unreachable by construction.
    STATE_APPROVED_FOR_EXECUTION: frozenset(),
    STATE_REJECTED: frozenset({STATE_INVALIDATED}),
    STATE_EXPIRED: frozenset({STATE_INVALIDATED}),
    STATE_INVALIDATED: frozenset(),
    STATE_EXECUTED: frozenset({STATE_RECONCILED}),
    STATE_RECONCILED: frozenset(),
}

# States in which a leg may be handed to an execution venue. Empty under
# current authority; computed from the transition graph, not hardcoded, so
# it cannot drift from the table above.
def reachable_states() -> FrozenSet[str]:
    """Every state with at least one inbound edge from a reachable state."""
    seen: set = {STATE_DRAFT_ANALYSIS}
    frontier = [STATE_DRAFT_ANALYSIS]
    while frontier:
        cur = frontier.pop()
        for nxt in ALLOWED_TRANSITIONS.get(cur, frozenset()):
            if nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)
    return frozenset(seen)


EXECUTABLE_STATES: FrozenSet[str] = frozenset(
    s for s in (STATE_APPROVED_FOR_EXECUTION, STATE_EXECUTED)
) & reachable_states()

# UI classification. Research / simulation / recommendation / execution are
# four DIFFERENT things and a surface that blurs them is misrepresenting
# the record regardless of what the state machine allows.
UI_CLASSIFICATION: Dict[str, str] = {
    STATE_DRAFT_ANALYSIS: "RESEARCH",
    STATE_VALIDATED_ALTERNATIVES: "RESEARCH",
    STATE_RECOMMENDATION_PENDING_REVIEW: "RECOMMENDATION",
    STATE_HUMAN_APPROVAL_REQUIRED: "RECOMMENDATION",
    STATE_APPROVED_FOR_SIMULATION: "SIMULATION",
    STATE_APPROVED_FOR_EXECUTION: "EXECUTION",
    STATE_REJECTED: "INERT",
    STATE_EXPIRED: "INERT",
    STATE_INVALIDATED: "INERT",
    STATE_EXECUTED: "EXECUTION",
    STATE_RECONCILED: "EXECUTION",
}

NON_HUMAN_IDENTITIES: FrozenSet[str] = frozenset({
    "", "agent", "agents", "assistant", "auto", "automated", "system",
    "scheduler", "pipeline", "model", "llm", "ai", "robot", "bot",
    "default", "unknown", "none", "self", "implicit", "inherited",
    "prior-approval", "file-presence", "default-true",
})

# Substrings that mark an identity as machine-operated. A denylist can
# never be complete (W9-B A6-13: "automation", "claude", "svc-approver-bot"
# and "robot-7" all cleared the exact-match denylist above), so these
# patterns are defence-in-depth BEHIND the registry, not the control
# itself. The control is the positive registry below.
NON_HUMAN_SUBSTRINGS: Tuple[str, ...] = (
    "bot", "svc-", "service", "daemon", "robot", "agent", "assistant",
    "automation", "automated", "script", "pipeline", "scheduler",
    "claude", "gpt", "llm", "model", "system", "-ai", "_ai",
)


@dataclass(frozen=True)
class HumanIdentity:
    """A human who may approve. Registered explicitly, never inferred."""

    identity: str
    display_name: str
    registered_at: str
    registered_by: str
    contact: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "identity": self.identity,
            "display_name": self.display_name,
            "registered_at": self.registered_at,
            "registered_by": self.registered_by,
            "contact": self.contact,
            "kind": "HUMAN",
        }


class HumanApproverRegistry:
    """The ONLY source of approver identities.

    A denylist of non-human names is not a control: it is a guess at the
    set of things to exclude, and red-teaming showed four of nine obvious
    agent identities ("automation", "claude", "svc-approver-bot",
    "robot-7") sailing straight through it. The correct shape is a
    positive registry -- an identity may approve because a human was
    REGISTERED, not because it failed to match a bad-name list.

    The registry starts EMPTY, so an unconfigured deployment approves
    nobody. That is the intended failure direction.
    """

    def __init__(self) -> None:
        self._people: Dict[str, HumanIdentity] = {}

    def register(self, identity: str, display_name: str,
                 registered_by: str, when_utc: Optional[str] = None,
                 contact: str = "") -> HumanIdentity:
        ident = str(identity or "").strip()
        if not ident:
            raise ApprovalViolation("EMPTY_IDENTITY",
                                    "an approver identity must be non-empty")
        if self.looks_non_human(ident):
            raise ApprovalViolation(
                "NON_HUMAN_APPROVER",
                "cannot register %r as a human approver: the identity is "
                "machine-shaped" % (ident,), approver=ident)
        person = HumanIdentity(
            identity=ident, display_name=str(display_name or ident),
            registered_at=when_utc or utc_now_iso(),
            registered_by=str(registered_by or "unspecified"),
            contact=str(contact or ""))
        self._people[ident] = person
        return person

    def revoke(self, identity: str) -> None:
        self._people.pop(str(identity), None)

    def is_registered_human(self, identity: str) -> bool:
        return str(identity or "").strip() in self._people

    def get(self, identity: str) -> Optional[HumanIdentity]:
        return self._people.get(str(identity or "").strip())

    def as_dict(self) -> Dict[str, Any]:
        return {k: v.as_dict() for k, v in sorted(self._people.items())}

    def __len__(self) -> int:
        return len(self._people)

    @classmethod
    def looks_non_human(cls, identity: str) -> bool:
        ident = str(identity or "").strip().lower()
        if not ident or ident in NON_HUMAN_IDENTITIES:
            return True
        return any(s in ident for s in NON_HUMAN_SUBSTRINGS)


class ApprovalViolation(Exception):
    """An attempt to move a decision somewhere it is not allowed to go."""

    def __init__(self, code: str, detail: str, **extra: Any):
        self.code = code
        self.detail = detail
        self.extra = extra
        super().__init__("%s: %s" % (code, detail))

    def as_dict(self) -> Dict[str, Any]:
        out = {"error": "ApprovalViolation", "code": self.code,
               "detail": self.detail, "severity": "HIGH",
               "authorized": False, "advisory": ADVISORY_LABEL}
        out.update(self.extra)
        return out


class ForgedApprovalError(ApprovalViolation):
    """A grant that does not carry a valid signature for its contents."""


# ---------------------------------------------------------------------------
# Canonical hashing
# ---------------------------------------------------------------------------

def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False)


def sha256_hex(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def _f6(v: Optional[float]) -> Optional[str]:
    """Quantise a float so textual formatting cannot change a fingerprint.

    Without this, 100.0 and 100.0000000001 could produce different
    fingerprints for an economically identical leg, and 1e-17 rounding
    noise would invalidate a legitimate approval.
    """
    if v is None:
        return None
    return "%.6f" % (float(v),)


# ---------------------------------------------------------------------------
# Legs and bindings
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Leg:
    """One proposed BUY or SELL. Inert unless the record says otherwise."""

    leg_id: str
    side: str                       # BUY | SELL
    instrument: str
    account: str
    quantity: Optional[float] = None
    limit_price: Optional[float] = None   # None => market / unpriced
    notional_usd: Optional[float] = None

    def __post_init__(self) -> None:
        if self.side not in ("BUY", "SELL"):
            raise ValueError("leg side must be BUY or SELL, got %r"
                             % (self.side,))
        if not self.instrument:
            raise ValueError("leg instrument must be non-empty")
        if not self.account:
            raise ValueError("leg account must be non-empty")
        if not self.leg_id:
            raise ValueError("leg_id must be non-empty")

    def binding_view(self) -> Dict[str, Any]:
        return {
            "leg_id": self.leg_id,
            "side": self.side,
            "instrument": self.instrument,
            "account": self.account,
            "quantity": _f6(self.quantity),
            "limit_price": _f6(self.limit_price),
            "notional_usd": _f6(self.notional_usd),
        }

    def as_dict(self) -> Dict[str, Any]:
        d = self.binding_view()
        d["executable"] = False      # legs are inert by construction
        d["authority"] = "NONE"
        return d


@dataclass(frozen=True)
class DecisionBinding:
    """Everything an approval must be bound to.

    If any field here changes, the fingerprint changes, and any existing
    grant stops matching. That is the mechanism behind "changed inputs
    invalidate approval", "changed model version invalidates approval" and
    "stale prices invalidate approval" -- they are not special-cased rules,
    they are consequences of what is inside the fingerprint.
    """

    decision_id: str
    decision_type: str
    legs: Tuple[Leg, ...]
    account: str
    model_version: str
    data_version: str
    policy_version: str
    code_hash: str
    price_as_of: Optional[str]
    expires_at: str
    requested_by: str

    def fingerprint(self) -> str:
        return sha256_hex({
            "decision_id": self.decision_id,
            "decision_type": self.decision_type,
            "account": self.account,
            "legs": [leg.binding_view() for leg in self.legs],
            "model_version": self.model_version,
            "data_version": self.data_version,
            "policy_version": self.policy_version,
            "code_hash": self.code_hash,
            "price_as_of": self.price_as_of,
            "expires_at": self.expires_at,
            "requested_by": self.requested_by,
        })

    def as_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "decision_type": self.decision_type,
            "account": self.account,
            "legs": [leg.as_dict() for leg in self.legs],
            "leg_ids": [leg.leg_id for leg in self.legs],
            "model_version": self.model_version,
            "data_version": self.data_version,
            "policy_version": self.policy_version,
            "code_hash": self.code_hash,
            "price_as_of": self.price_as_of,
            "expires_at": self.expires_at,
            "requested_by": self.requested_by,
            "fingerprint": self.fingerprint(),
        }


# ---------------------------------------------------------------------------
# Grant
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ApprovalGrant:
    """A signed, scoped, expiring authorisation for ONE exact decision."""

    grant_id: str
    decision_id: str
    fingerprint: str
    state_granted: str
    approver_identity: str
    approved_at: str
    expires_at: str
    leg_scope: Tuple[str, ...]
    signature: str = ""

    def payload(self) -> Dict[str, Any]:
        return {
            "grant_id": self.grant_id,
            "decision_id": self.decision_id,
            "fingerprint": self.fingerprint,
            "state_granted": self.state_granted,
            "approver_identity": self.approver_identity,
            "approved_at": self.approved_at,
            "expires_at": self.expires_at,
            "leg_scope": list(self.leg_scope),
        }

    def signed_payload(self) -> Dict[str, Any]:
        d = self.payload()
        d["signature"] = self.signature
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ApprovalGrant":
        return cls(
            grant_id=str(d["grant_id"]),
            decision_id=str(d["decision_id"]),
            fingerprint=str(d["fingerprint"]),
            state_granted=str(d["state_granted"]),
            approver_identity=str(d["approver_identity"]),
            approved_at=str(d["approved_at"]),
            expires_at=str(d["expires_at"]),
            leg_scope=tuple(str(x) for x in (d.get("leg_scope") or [])),
            signature=str(d.get("signature") or ""),
        )

    def verify_signature(self, key: bytes) -> bool:
        """A grant with no signature, or a wrong one, is not a grant."""
        if not self.signature:
            return False
        want = _sign(key, self.payload())
        return hmac.compare_digest(self.signature, want)


def _sign(key: bytes, payload: Dict[str, Any]) -> str:
    return hmac.new(key, canonical_json(payload).encode("utf-8"),
                    hashlib.sha256).hexdigest()


def _atomic_append_line(path: str, line: str) -> None:
    """Append one line durably: temp file, fsync, atomic rename.

    Used for the grant-consumption ledger. A revocation that only lives in
    memory is not a revocation.
    """
    directory = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(directory, exist_ok=True)
    prior = ""
    if os.path.exists(path):
        with open(path, "r", encoding="ascii") as fh:
            prior = fh.read()
    blob = (prior if prior.endswith("\n") or not prior else prior + "\n") \
        + line + "\n"
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".approval-",
                               suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="ascii") as fh:
            fh.write(blob)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def generate_key() -> bytes:
    return os.urandom(32)


def load_or_create_key(path: str) -> bytes:
    """Load the HMAC key, creating it atomically on first use.

    Persisted so that a grant issued in one process verifies in another --
    an approval that only survives in memory is not an approval.
    """
    try:
        with open(path, "rb") as f:
            data = f.read().strip()
        if data:
            return bytes.fromhex(data.decode("ascii"))
    except (OSError, ValueError):
        pass
    key = generate_key()
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".approval-key-", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(key.hex().encode("ascii"))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return key


# ---------------------------------------------------------------------------
# Clock
# ---------------------------------------------------------------------------

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso_z(s: str) -> datetime:
    if not s or not str(s).endswith("Z"):
        raise ApprovalViolation(
            "BAD_TIMESTAMP",
            "timestamps must be UTC ISO-8601 ending in Z, got %r" % (s,))
    return datetime.strptime(str(s), "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc)


def _add_seconds(s: str, seconds: int) -> str:
    return (_parse_iso_z(s) + timedelta(seconds=int(seconds))).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Decision record
# ---------------------------------------------------------------------------

@dataclass
class DecisionRecord:
    """A proposed decision and its approval lifecycle."""

    binding: DecisionBinding
    state: str = STATE_DRAFT_ANALYSIS
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    history: List[Dict[str, Any]] = field(default_factory=list)
    grant: Optional[ApprovalGrant] = None
    data_gaps: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    # -- identity ---------------------------------------------------------
    @property
    def decision_id(self) -> str:
        return self.binding.decision_id

    def fingerprint(self) -> str:
        return self.binding.fingerprint()

    # -- authority --------------------------------------------------------
    def is_executable(self) -> bool:
        """The one question an execution surface is allowed to ask."""
        return self.state in EXECUTABLE_STATES

    def ui_classification(self) -> str:
        return UI_CLASSIFICATION.get(self.state, "INERT")

    def authority_level(self) -> str:
        """NONE / SIMULATION / EXECUTION -- what this record confers."""
        if self.state == STATE_APPROVED_FOR_SIMULATION:
            return "SIMULATION"
        if self.state in (STATE_APPROVED_FOR_EXECUTION, STATE_EXECUTED,
                          STATE_RECONCILED):
            return "EXECUTION"
        return "NONE"

    # -- transitions ------------------------------------------------------
    def _require(self, target: str, actor: str, reason: str,
                 clock=None) -> None:
        now = (clock or utc_now_iso)()
        if target not in ALL_STATES:
            raise ApprovalViolation("UNKNOWN_STATE",
                                    "%r is not a declared state" % (target,))
        if target not in ALLOWED_TRANSITIONS.get(self.state, frozenset()):
            raise ApprovalViolation(
                "FORBIDDEN_TRANSITION",
                "no transition %s -> %s exists in the table"
                % (self.state, target),
                current_state=self.state, requested_state=target)
        if (_STATE_RANK.get(target, -1) > _STATE_RANK.get(AUTHORITY_CEILING, -1)
                and target != STATE_EXECUTED):
            raise ApprovalViolation(
                "AUTHORITY_CEILING",
                "%s exceeds the granted authority ceiling %s"
                % (target, AUTHORITY_CEILING),
                current_state=self.state, requested_state=target,
                ceiling=AUTHORITY_CEILING)
        if target in (STATE_EXECUTED, STATE_RECONCILED):
            raise ApprovalViolation(
                "AUTHORITY_CEILING",
                "%s is unreachable while the ceiling is %s"
                % (target, AUTHORITY_CEILING),
                current_state=self.state, requested_state=target)
        self.history.append({
            "from": self.state, "to": target, "actor": actor,
            "at": now, "reason": reason,
            "fingerprint": self.fingerprint(),
        })
        self.state = target
        self.updated_at = now

    def advance(self, target: str, actor: str, reason: str = "",
                clock=None) -> "DecisionRecord":
        self._require(target, actor, reason, clock=clock)
        return self

    def invalidate(self, actor: str, reason: str, clock=None) -> "DecisionRecord":
        """Terminal. An invalidated decision cannot be revived."""
        self._require(STATE_INVALIDATED, actor, reason, clock=clock)
        self.grant = None
        return self

    def reject(self, actor: str, reason: str, clock=None) -> "DecisionRecord":
        self._require(STATE_REJECTED, actor, reason, clock=clock)
        self.grant = None
        return self

    # -- serialisation ----------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """The shape every consumer (portfolio, tax, risk, UX) must read.

        `execution` is present and explicitly False unless the state
        machine says otherwise. A consumer that ignores `state` and looks
        only for legs still sees `executable: False` on every leg.
        """
        return {
            "decision_id": self.decision_id,
            "decision_type": self.binding.decision_type,
            "state": self.state,
            "authority_level": self.authority_level(),
            "is_executable": self.is_executable(),
            "ui_classification": self.ui_classification(),
            "binding": self.binding.as_dict(),
            "fingerprint": self.fingerprint(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "history": list(self.history),
            "grant": self.grant.signed_payload() if self.grant else None,
            "approval_present": self.grant is not None,
            "data_gaps": list(self.data_gaps),
            "notes": list(self.notes),
            "execution": {
                "authorized": self.is_executable(),
                "state": self.state,
                "authority_ceiling": AUTHORITY_CEILING,
                "reason": ("no route to APPROVED_FOR_EXECUTION exists under "
                           "the granted authority"
                           if not self.is_executable()
                           else "AUTHORIZED"),
                "advisory": ADVISORY_LABEL,
            },
            "legs": [
                dict(leg.as_dict(),
                     executable=self.is_executable(),
                     authority=self.authority_level())
                for leg in self.binding.legs
            ],
            "approval_rule_version": APPROVAL_RULE_VERSION,
            "advisory": ADVISORY_LABEL,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DecisionRecord":
        """Rehydrate WITHOUT trusting a stored `state`.

        A stored state above HUMAN_APPROVAL_REQUIRED is demoted unless a
        grant is present AND verifies. This is what stops "file presence"
        from being an approval: a JSON file that says
        `"state": "APPROVED_FOR_EXECUTION"` restores as INVALIDATED.
        """
        b = d["binding"]
        legs = tuple(Leg(
            leg_id=str(x["leg_id"]), side=str(x["side"]),
            instrument=str(x["instrument"]), account=str(x["account"]),
            quantity=x.get("quantity"), limit_price=x.get("limit_price"),
            notional_usd=x.get("notional_usd")) for x in b.get("legs", []))
        binding = DecisionBinding(
            decision_id=str(b["decision_id"]),
            decision_type=str(b["decision_type"]),
            legs=legs, account=str(b["account"]),
            model_version=str(b["model_version"]),
            data_version=str(b["data_version"]),
            policy_version=str(b["policy_version"]),
            code_hash=str(b["code_hash"]),
            price_as_of=b.get("price_as_of"),
            expires_at=str(b["expires_at"]),
            requested_by=str(b["requested_by"]))
        rec = cls(
            binding=binding,
            state=str(d.get("state", STATE_DRAFT_ANALYSIS)),
            created_at=str(d.get("created_at", utc_now_iso())),
            updated_at=str(d.get("updated_at", utc_now_iso())),
            history=list(d.get("history", [])),
            data_gaps=list(d.get("data_gaps", [])),
            notes=list(d.get("notes", [])),
        )
        if d.get("grant"):
            rec.grant = ApprovalGrant.from_dict(d["grant"])

        # A stored state is a CLAIM, not an authority. Anything at or above
        # the ceiling, or unreachable in the transition graph, is demoted
        # and recorded. This is what makes "the approval file exists" a
        # non-argument: the file has to survive signature verification
        # first, and there is no signature that can confer execution.
        if (rec.state not in reachable_states()
                or _STATE_RANK.get(rec.state, -1)
                > _STATE_RANK.get(AUTHORITY_CEILING, -1)):
            rec.notes.append(
                "stored state %r is unreachable or above the ceiling %r; "
                "demoted to INVALIDATED on load -- a persisted state is a "
                "claim, not an authority" % (rec.state, AUTHORITY_CEILING))
            rec.history.append({
                "from": rec.state, "to": STATE_INVALIDATED,
                "actor": "approval.from_dict",
                "at": utc_now_iso(),
                "reason": "stored state unreachable or above ceiling",
                "fingerprint": rec.fingerprint(),
            })
            rec.state = STATE_INVALIDATED
            rec.grant = None
        return rec


# ---------------------------------------------------------------------------
# Verification result
# ---------------------------------------------------------------------------

@dataclass
class VerificationResult:
    ok: bool
    effective_state: str
    authority_level: str
    reasons: List[str]
    codes: List[str]
    decision_id: str = ""
    fingerprint: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "authorized_for_simulation": (
                self.ok and self.effective_state == STATE_APPROVED_FOR_SIMULATION),
            "authorized_for_execution": False,
            "effective_state": self.effective_state,
            "authority_level": self.authority_level,
            "reasons": list(self.reasons),
            "codes": list(self.codes),
            "decision_id": self.decision_id,
            "fingerprint": self.fingerprint,
            "advisory": ADVISORY_LABEL,
            "approval_rule_version": APPROVAL_RULE_VERSION,
        }


# ---------------------------------------------------------------------------
# Authority
# ---------------------------------------------------------------------------

class ApprovalAuthority:
    """Issues and verifies grants. The only place a signature is made."""

    def __init__(self, key: bytes, clock=utc_now_iso,
                 max_ttl_seconds: int = 7 * 24 * 3600,
                 require_distinct_approver: bool = True,
                 allow_agent_approver: bool = False,
                 registry: Optional["HumanApproverRegistry"] = None,
                 consumption_path: Optional[str] = None):
        self._key = key
        self.clock = clock
        self.max_ttl_seconds = int(max_ttl_seconds)
        self.require_distinct_approver = bool(require_distinct_approver)
        self.allow_agent_approver = bool(allow_agent_approver)
        self.registry = registry if registry is not None \
            else HumanApproverRegistry()
        # Persistent consumers share an exclusive ledger lock around the
        # entire refresh/check/append transaction. Startup-only snapshots
        # allow two existing authorities to consume the same grant.
        # No path means an explicitly process-local simulation authority.
        self.consumption_path = (os.path.realpath(os.path.abspath(consumption_path))
                                 if consumption_path else None)
        self._consumed: set = set()
        self._consumption_lock = threading.Lock()

    def _read_consumed(self) -> set:
        """Read only while holding the same-ledger lock; malformed is refusal."""
        try:
            with open(self.consumption_path, "r", encoding="ascii") as fh:
                text = fh.read()
        except FileNotFoundError:
            return set()
        except UnicodeError as exc:
            raise ApprovalViolation("CONSUMPTION_LEDGER_CORRUPT",
                                    "consumption ledger is not ASCII") from exc
        if text and not text.endswith("\n"):
            raise ApprovalViolation("CONSUMPTION_LEDGER_CORRUPT",
                                    "consumption ledger has an incomplete final line")
        consumed = set()
        for line_number, line in enumerate(text.splitlines(), 1):
            try:
                row = json.loads(line)
                names = ("grant_id", "decision_id", "fingerprint", "consumed_at")
                if not isinstance(row, dict) or any(
                        not isinstance(row.get(name), str) or not row[name]
                        for name in names):
                    raise ValueError("missing consumption fields")
                _parse_iso_z(row["consumed_at"])
            except (ValueError, ApprovalViolation) as exc:
                raise ApprovalViolation(
                    "CONSUMPTION_LEDGER_CORRUPT",
                    "consumption ledger row %d is invalid" % line_number) from exc
            consumed.add((row["grant_id"], row["decision_id"], row["fingerprint"]))
        return consumed

    def _consume_once(self, token: Tuple[Any, Any, Any]) -> bool:
        """Atomically check and consume. Contention never grants authority."""
        if not self._consumption_lock.acquire(blocking=False):
            raise ApprovalViolation("APPROVAL_LOCKED", "another approval check is in progress")
        try:
            if not self.consumption_path:
                if token in self._consumed:
                    return False
                self._consumed.add(token)
                return True
            os.makedirs(os.path.dirname(self.consumption_path), exist_ok=True)
            lock_path = self.consumption_path + ".lock"
            try:
                lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError as exc:
                raise ApprovalViolation(
                    "APPROVAL_LOCKED", "the consumption ledger is locked; no authority granted") from exc
            try:
                self._consumed.update(self._read_consumed())
                if token in self._consumed:
                    return False
                row = {"grant_id": token[0], "decision_id": token[1],
                       "fingerprint": token[2], "consumed_at": self.clock()}
                _atomic_append_line(self.consumption_path, json.dumps(row, sort_keys=True))
                self._consumed.add(token)
                return True
            finally:
                os.close(lock_fd)
                os.unlink(lock_path)
        finally:
            self._consumption_lock.release()

    # -- issuance ---------------------------------------------------------
    def issue(self, record: DecisionRecord, approver_identity: str,
              leg_scope: Optional[Sequence[str]] = None,
              ttl_seconds: int = 3600, reason: str = "") -> ApprovalGrant:
        now = self.clock()
        ident = str(approver_identity or "").strip()

        if record.state != STATE_HUMAN_APPROVAL_REQUIRED:
            raise ApprovalViolation(
                "NOT_PENDING_APPROVAL",
                "approval may only be issued from %s; record is in %s"
                % (STATE_HUMAN_APPROVAL_REQUIRED, record.state),
                current_state=record.state)

        # The control is a POSITIVE registry, not a denylist. An identity
        # may approve because a human was registered -- not because it
        # failed to match a list of machine-shaped names.
        # The legacy flag remains accepted for caller compatibility, but
        # it cannot disable positive registration of a human approver.
        if not self.registry.is_registered_human(ident):
            if len(self.registry) == 0:
                raise ApprovalViolation(
                    "NO_HUMAN_REGISTERED",
                    "no human approver is registered, so nobody can "
                    "approve; register an identity with "
                    "authority.registry.register(...) before issuing "
                    "an approval", approver=ident)
            raise ApprovalViolation(
                "NON_HUMAN_APPROVER",
                "approver %r is not a registered human identity; an "
                "agent statement, a default, or an unrecognised system "
                "identity cannot approve" % (ident,), approver=ident)

        if self.require_distinct_approver and ident and \
                ident == record.binding.requested_by:
            raise ApprovalViolation(
                "SEPARATION_OF_DUTIES",
                "approver %r is the same identity that requested the "
                "decision; the requester cannot approve its own proposal"
                % (ident,), approver=ident)

        # Expiry must be bounded, and must be in the future.
        if int(ttl_seconds) <= 0:
            raise ApprovalViolation("BAD_TTL",
                                    "ttl_seconds must be positive")
        if int(ttl_seconds) > self.max_ttl_seconds:
            raise ApprovalViolation(
                "TTL_TOO_LONG",
                "ttl %ds exceeds the maximum %ds -- an approval that never "
                "expires is not an approval of a specific decision"
                % (int(ttl_seconds), self.max_ttl_seconds))
        expires_at = _add_seconds(now, int(ttl_seconds))

        if record.binding.expires_at and \
                _parse_iso_z(expires_at) > _parse_iso_z(record.binding.expires_at):
            expires_at = record.binding.expires_at

        all_ids = [leg.leg_id for leg in record.binding.legs]
        if leg_scope is None:
            scope: Tuple[str, ...] = tuple(all_ids)
        else:
            unknown = [x for x in leg_scope if x not in all_ids]
            if unknown:
                raise ApprovalViolation(
                    "UNKNOWN_LEG",
                    "approval scope names legs that are not part of this "
                    "decision: %s" % (unknown,), unknown_legs=unknown)
            scope = tuple(str(x) for x in leg_scope)
        if len(scope) != len(all_ids):
            # Recorded, not refused: a partial grant is legal to ISSUE but
            # can never authorise the whole decision (see verify()).
            record.notes.append(
                "partial approval granted for %d of %d legs at %s"
                % (len(scope), len(all_ids), now))

        payload = {
            "grant_id": sha256_hex({
                "decision_id": record.decision_id,
                "fingerprint": record.fingerprint(),
                "approver": ident, "at": now, "scope": list(scope)})[:32],
            "decision_id": record.decision_id,
            "fingerprint": record.fingerprint(),
            "state_granted": STATE_APPROVED_FOR_SIMULATION,
            "approver_identity": ident,
            "approved_at": now,
            "expires_at": expires_at,
            "leg_scope": list(scope),
        }
        sig = _sign(self._key, payload)
        grant = ApprovalGrant(signature=sig, **payload)

        record.grant = grant
        record._require(STATE_APPROVED_FOR_SIMULATION, ident,
                        reason or "human approval granted", clock=self.clock)
        return grant

    # -- verification -----------------------------------------------------
    def verify(self, record: DecisionRecord,
               grant: Optional[ApprovalGrant] = None,
               now: Optional[str] = None,
               context: Optional[Dict[str, Any]] = None) -> VerificationResult:
        g = grant if grant is not None else record.grant
        now_s = now if now is not None else self.clock()
        ctx = context or {}
        reasons: List[str] = []
        codes: List[str] = []

        def fail(code: str, reason: str, state: str = STATE_INVALIDATED):
            codes.append(code)
            reasons.append(reason)
            return VerificationResult(
                ok=False, effective_state=state, authority_level="NONE",
                reasons=reasons, codes=codes,
                decision_id=record.decision_id,
                fingerprint=record.fingerprint())

        if record.state not in (STATE_HUMAN_APPROVAL_REQUIRED,
                                STATE_APPROVED_FOR_SIMULATION):
            return fail("RECORD_STATE_REFUSED",
                        "record state %s cannot receive approval authority" % record.state)

        # 1. A grant must exist. None of the shortcuts count.
        if g is None:
            return fail("NO_GRANT",
                        "no signed approval grant is attached to this "
                        "decision; a proposal is not an authorisation")

        # 2. The grant must carry a valid signature over its own contents.
        if not g.verify_signature(self._key):
            return fail(
                "FORGED_GRANT",
                "the attached grant does not carry a valid signature for "
                "its contents -- a hand-written or edited approval field is "
                "not an approval")

        # 3. It must belong to THIS decision.
        if g.decision_id != record.decision_id:
            return fail("GRANT_DECISION_MISMATCH",
                        "grant is for decision %s, record is %s"
                        % (g.decision_id, record.decision_id))

        # 4. The decision must be byte-identical to the one approved.
        if g.fingerprint != record.fingerprint():
            return fail(
                "FINGERPRINT_MISMATCH",
                "the decision changed after approval (approved %s, now %s); "
                "changed inputs, quantities, instruments, accounts, model "
                "version, data version, code or expiry all invalidate an "
                "approval" % (g.fingerprint[:12], record.fingerprint()[:12]))

        # 5. Not expired.
        try:
            if _parse_iso_z(now_s) > _parse_iso_z(g.expires_at):
                return fail("EXPIRED_APPROVAL",
                            "approval expired at %s (now %s)"
                            % (g.expires_at, now_s), state=STATE_EXPIRED)
        except ApprovalViolation as exc:
            return fail("BAD_CLOCK", str(exc))

        # 6. Full-basket only. A partial approval authorises nothing.
        all_ids = [leg.leg_id for leg in record.binding.legs]
        missing = [x for x in all_ids if x not in set(g.leg_scope)]
        if missing:
            return fail(
                "PARTIAL_APPROVAL",
                "approval covers %d of %d legs; unapproved legs %s cannot be "
                "carried along by the approved ones -- partial approval "
                "authorises NOTHING"
                % (len(g.leg_scope), len(all_ids), missing))

        # 7. Environment drift. Not inferred from the grant: re-checked
        #    against the live context so a re-run under a new model or a
        #    new dataset cannot reuse an old approval.
        for key_name, ctx_key in (("model_version", "model_version"),
                                  ("data_version", "data_version"),
                                  ("policy_version", "policy_version"),
                                  ("code_hash", "code_hash")):
            want = ctx.get(ctx_key)
            if want is not None and want != getattr(record.binding, key_name):
                return fail(
                    "ENVIRONMENT_DRIFT",
                    "%s changed since approval (approved %s, now %s)"
                    % (ctx_key, getattr(record.binding, key_name), want))
        if ctx.get("price_as_of") is not None and \
                ctx["price_as_of"] != record.binding.price_as_of:
            return fail(
                "STALE_PRICES",
                "price as-of changed since approval (approved %s, now %s); "
                "an approval of stale prices is not an approval of these "
                "prices" % (record.binding.price_as_of, ctx["price_as_of"]))
        if ctx.get("price_stale") is True:
            return fail("STALE_PRICES",
                        "the price feed reports the marks as stale")
        if ctx.get("data_gaps"):
            return fail(
                "DATA_GAP",
                "the decision carries %d unresolved data gap(s); a "
                "recommendation built on a missing price cannot be approved"
                % len(ctx["data_gaps"]))

        # Check the ceiling before consuming an otherwise invalid grant.
        if _STATE_RANK.get(g.state_granted, -1) > _STATE_RANK.get(
                AUTHORITY_CEILING, -1):
            return fail("AUTHORITY_CEILING",
                        "grant confers %s which exceeds the ceiling %s"
                        % (g.state_granted, AUTHORITY_CEILING))

        # 8. Replay: refresh/check/append form one same-ledger transaction.
        token = (g.grant_id, g.decision_id, g.fingerprint)
        try:
            consumed = self._consume_once(token)
        except ApprovalViolation as exc:
            return fail(exc.code, str(exc))
        except OSError:
            return fail("CONSUMPTION_IO_ERROR",
                        "approval consumption could not be persisted; no authority granted")
        if not consumed:
            return fail("REPLAYED_APPROVAL",
                        "grant %s has already been consumed; an approval "
                        "cannot be replayed" % (g.grant_id,))

        return VerificationResult(
            ok=True, effective_state=STATE_APPROVED_FOR_SIMULATION,
            authority_level="SIMULATION", reasons=["valid grant"],
            codes=["OK"], decision_id=record.decision_id,
            fingerprint=record.fingerprint())

    def authorize(self, record: DecisionRecord,
                  grant: Optional[ApprovalGrant] = None,
                  now: Optional[str] = None,
                  context: Optional[Dict[str, Any]] = None,
                  purpose: str = "unspecified") -> VerificationResult:
        """Verify and, on failure, move the record to the terminal state.

        `purpose` is recorded. Asking to authorise for EXECUTION can never
        succeed while the ceiling stands, and saying so explicitly is the
        point.
        """
        res = self.verify(record, grant=grant, now=now, context=context)
        if purpose.upper() == "EXECUTION":
            codes = list(res.codes)
            reasons = list(res.reasons)
            if res.ok:
                res.ok = False
                codes.append("EXECUTION_NOT_AUTHORIZED")
                reasons.append(
                    "authorisation was requested for EXECUTION; the granted "
                    "authority ceiling is %s and no route to %s exists"
                    % (AUTHORITY_CEILING, STATE_APPROVED_FOR_EXECUTION))
            res.codes = codes
            res.reasons = reasons
            res.authority_level = "NONE"
        if not res.ok:
            terminal = (STATE_EXPIRED if "EXPIRED_APPROVAL" in res.codes
                        else STATE_INVALIDATED)
            if record.state in ALLOWED_TRANSITIONS and terminal in \
                    ALLOWED_TRANSITIONS.get(record.state, frozenset()):
                record._require(terminal, "approval-authority",
                                "; ".join(res.codes), clock=lambda: (
                                    now if now is not None else self.clock()))
                record.grant = None
        return res


# ---------------------------------------------------------------------------
# Boundary enforcement -- used by tools and API surfaces, not just the UI
# ---------------------------------------------------------------------------

def enforce_not_executable(obj: Any, where: str = "boundary") -> None:
    """Refuse any object that claims execution authority.

    Called at tool and API boundaries so that enforcement does not live
    only in the interface layer. Raises on:
      * an explicit `is_executable` / `authorized` True;
      * a state above the ceiling;
      * a leg that claims `executable: True`;
      * an `approved: True` boolean, which is not a concept this system
        recognises as an approval.
    """
    pending = [(obj, where)]
    seen = set()
    while pending:
        value, path = pending.pop()
        if not isinstance(value, (DecisionRecord, dict, list, tuple)):
            continue
        if id(value) in seen:
            continue
        seen.add(id(value))
        if isinstance(value, DecisionRecord):
            if value.is_executable() or _STATE_RANK.get(value.state, -1) > \
                    _STATE_RANK.get(AUTHORITY_CEILING, -1):
                raise ApprovalViolation(
                    "AUTHORITY_CEILING", "record exceeds the simulation authority ceiling",
                    where=path)
            pending.append((value.to_dict(), path))
        elif isinstance(value, dict):
            for flag in ("is_executable", "executable", "authorized", "authorized_for_execution"):
                claim = value.get(flag)
                if claim is not None and claim is not False:
                    raise ApprovalViolation(
                        "EXECUTION_NOT_AUTHORIZED",
                        "object at %s claims execution authority through %s" % (path, flag),
                        where=path)
            if value.get("approved") is not None and value.get("approved") is not False:
                raise ApprovalViolation(
                    "BOOLEAN_APPROVAL", "approval cannot be inferred from an approved field",
                    where=path)
            for key in ("state", "state_granted"):
                state = value.get(key)
                if state and _STATE_RANK.get(str(state), -1) > \
                        _STATE_RANK.get(AUTHORITY_CEILING, -1):
                    raise ApprovalViolation(
                        "AUTHORITY_CEILING", "object at %s exceeds the simulation ceiling" % path,
                        where=path)
            pending.extend((child, "%s.%s" % (path, key)) for key, child in value.items())
        else:
            pending.extend((child, "%s[%d]" % (path, index))
                           for index, child in enumerate(value))


def inert_plan_envelope(
    decision_id: str,
    decision_type: str,
    plan: Optional[Dict[str, Any]],
    account: str = "UNSPECIFIED",
    model_version: str = "unspecified",
    data_version: str = "unspecified",
    policy_version: str = "unspecified",
    code_hash: str = "unspecified",
    price_as_of: Optional[str] = None,
    requested_by: str = "agent",
    data_gaps: Optional[List[Dict[str, Any]]] = None,
    ttl_seconds: int = 3600,
) -> Dict[str, Any]:
    """Wrap a computed rebalance plan in an inert decision envelope.

    This is what `portfolio_engine.propose_rebalance` now returns. The
    arithmetic is unchanged; every leg it contains is marked
    `executable: False` and the envelope states, in as many places as a
    careless consumer might look, that nothing here is authorised.
    """
    gaps = list(data_gaps or [])
    legs: List[Leg] = []
    trades = ((plan or {}).get("trades") or [])
    for i, tr in enumerate(trades):
        side = str(tr.get("side", "")).upper()
        tkr = str(tr.get("ticker", ""))
        legs.append(Leg(
            leg_id="L%03d" % i,
            side=side if side in ("BUY", "SELL") else "SELL",
            instrument=tkr or "UNKNOWN",
            account=str(tr.get("account") or account),
            quantity=tr.get("qty"),
            limit_price=None,
            notional_usd=tr.get("notional_usd"),
        ))
    expires_at = _add_seconds(utc_now_iso(), int(ttl_seconds))
    binding = DecisionBinding(
        decision_id=decision_id, decision_type=decision_type,
        legs=tuple(legs), account=account,
        model_version=model_version, data_version=data_version,
        policy_version=policy_version, code_hash=code_hash,
        price_as_of=price_as_of, expires_at=expires_at,
        requested_by=requested_by)
    rec = DecisionRecord(binding=binding, state=STATE_DRAFT_ANALYSIS,
                         data_gaps=gaps)
    if trades:
        # A computed plan is an analysis awaiting review, never a
        # recommendation that has cleared review.
        rec.advance(STATE_VALIDATED_ALTERNATIVES, requested_by,
                    "alternatives computed and constraint-checked")
        rec.advance(STATE_RECOMMENDATION_PENDING_REVIEW, requested_by,
                    "awaiting human review")
        if gaps:
            rec.advance(STATE_HUMAN_APPROVAL_REQUIRED, requested_by,
                        "data gaps present; review must resolve them")
    out = rec.to_dict()
    out["plan"] = _strip_execution_posture(plan)
    out["ui"] = {
        "classification": rec.ui_classification(),
        "badge": "APPROVAL REQUIRED -- NOT AUTHORIZED FOR EXECUTION",
        "distinct_from": {
            "research": "what-if analysis, no commitment implied",
            "simulation": "approved for modelling only, no order may be sent",
            "recommendation": "reviewed output awaiting a human decision",
            "execution": "NOT AVAILABLE -- unreachable under current authority",
        },
        "show_execute_button": False,
        "show_approve_button": rec.state == STATE_HUMAN_APPROVAL_REQUIRED,
    }
    if gaps:
        out["notes"] = list(rec.notes) + [
            "%d data gap(s) present: the recommendation is INCOMPLETE and "
            "any approval of it is void while they remain" % len(gaps)]
    return out


def _strip_execution_posture(plan: Optional[Dict[str, Any]]) -> Any:
    """Copy a plan with every trade explicitly marked non-executable.

    Deep-copies so the caller's own dict is not mutated, and rebuilds the
    trade list so a consumer that reaches past the envelope for
    `plan["trades"]` still cannot find an executable instruction.
    """
    if plan is None:
        return None
    out = json.loads(json.dumps(plan, default=str))
    if isinstance(out, dict):
        for tr in (out.get("trades") or []):
            if isinstance(tr, dict):
                tr["executable"] = False
                tr["authority"] = "NONE"
                tr["order_state"] = "INERT-PROPOSED"
        out["executable"] = False
        out["authorized"] = False
        out["advisory"] = ADVISORY_LABEL
    return out


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def _selftest() -> int:
    failures: List[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        if not cond:
            failures.append("%s %s" % (name, detail))
        print("[%s] %s%s" % ("PASS" if cond else "FAIL", name,
                             (" :: " + detail) if detail else ""))

    check("no-route-to-execution",
          STATE_APPROVED_FOR_EXECUTION not in reachable_states(),
          "reachable=%s" % sorted(reachable_states()))
    check("executable-states-empty", len(EXECUTABLE_STATES) == 0,
          "executable=%s" % sorted(EXECUTABLE_STATES))

    auth = ApprovalAuthority(generate_key(),
                             clock=lambda: "2026-01-01T00:00:00Z")
    base = dict(decision_type="rebalance", account="taxable-001",
                model_version="m1", data_version="d1", policy_version="p1",
                code_hash="c1", price_as_of="2026-01-01",
                requested_by="agent")
    legs = (Leg("L0", "SELL", "ZPHR", "taxable-001", quantity=10.0,
                notional_usd=1000.0),)
    b = DecisionBinding(decision_id="D1", legs=legs,
                        expires_at="2026-01-02T00:00:00Z", **base)
    rec = DecisionRecord(binding=b, state=STATE_HUMAN_APPROVAL_REQUIRED)

    # An EMPTY registry approves nobody -- fail closed before it is
    # configured, rather than approving whoever asks first.
    try:
        auth.issue(rec, "<email>")
        check("empty-registry-approves-nobody", False, "no exception")
    except ApprovalViolation as exc:
        check("empty-registry-approves-nobody",
              exc.code == "NO_HUMAN_REGISTERED", exc.code)

    auth.registry.register("<owner>@household", "<owner>",
                           registered_by="operator-setup",
                           when_utc="2025-12-01T00:00:00Z")

    # W9-B A6-13: identities that cleared the old exact-match denylist.
    for bogus in ("automation", "claude", "svc-approver-bot", "robot-7",
                  "nightly-pipeline", "helper-script", "agent-2"):
        try:
            auth.issue(rec, bogus)
            check("machine-identity-refused[%s]" % bogus, False, "ISSUED")
        except ApprovalViolation as exc:
            check("machine-identity-refused[%s]" % bogus,
                  exc.code == "NON_HUMAN_APPROVER", exc.code)

    # A machine-shaped identity cannot even be registered.
    try:
        auth.registry.register("deploy-bot", "Deploy Bot",
                               registered_by="operator")
        check("machine-identity-unregisterable", False, "registered")
    except ApprovalViolation as exc:
        check("machine-identity-unregisterable",
              exc.code == "NON_HUMAN_APPROVER", exc.code)

    g = auth.issue(rec, "<owner>@household", ttl_seconds=3600)
    check("grant-issued", rec.state == STATE_APPROVED_FOR_SIMULATION,
          rec.state)
    vr = auth.verify(rec, now="2026-01-01T00:10:00Z")
    check("valid-grant-verifies", vr.ok and
          vr.effective_state == STATE_APPROVED_FOR_SIMULATION, str(vr.codes))

    # Replay refused.
    vr2 = auth.authorize(rec, now="2026-01-01T00:11:00Z")
    check("replay-refused", (not vr2.ok) and "REPLAYED_APPROVAL" in vr2.codes,
          str(vr2.codes))

    # Changed quantity invalidates.
    rec2 = DecisionRecord(binding=replace(
        b, legs=(Leg("L0", "SELL", "ZPHR", "taxable-001", quantity=11.0,
                     notional_usd=1000.0),)),
        state=STATE_HUMAN_APPROVAL_REQUIRED)
    vr3 = auth.authorize(rec2, grant=g, now="2026-01-01T00:12:00Z")
    check("changed-quantity-invalidates",
          (not vr3.ok) and "FINGERPRINT_MISMATCH" in vr3.codes, str(vr3.codes))

    # Forged signature refused.
    forged = replace(g, signature="0" * 64)
    rec3 = DecisionRecord(binding=b, state=STATE_HUMAN_APPROVAL_REQUIRED)
    vr4 = auth.authorize(rec3, grant=forged, now="2026-01-01T00:13:00Z")
    check("forged-grant-refused",
          (not vr4.ok) and "FORGED_GRANT" in vr4.codes, str(vr4.codes))

    # Execution purpose can never succeed.
    rec4 = DecisionRecord(binding=b, state=STATE_HUMAN_APPROVAL_REQUIRED)
    auth2 = ApprovalAuthority(generate_key(), clock=lambda: "2026-01-01T00:00:00Z")
    auth2.registry.register("<owner>@household", "<owner>", registered_by="setup",
                            when_utc="2025-12-01T00:00:00Z")
    g4 = auth2.issue(rec4, "<owner>@household", ttl_seconds=3600)
    vr5 = auth2.authorize(rec4, grant=g4, now="2026-01-01T00:14:00Z",
                          purpose="EXECUTION")
    check("execution-never-authorized",
          (not vr5.ok) and "EXECUTION_NOT_AUTHORIZED" in vr5.codes
          and vr5.as_dict()["authorized_for_execution"] is False,
          str(vr5.codes))

    # Partial approval authorises nothing.
    legs2 = (Leg("L0", "SELL", "A", "acct", notional_usd=1.0),
             Leg("L1", "BUY", "B", "acct", notional_usd=1.0))
    b2 = DecisionBinding(decision_id="D2", legs=legs2,
                         expires_at="2026-01-02T00:00:00Z", **base)
    r5 = DecisionRecord(binding=b2, state=STATE_HUMAN_APPROVAL_REQUIRED)
    a3 = ApprovalAuthority(generate_key(), clock=lambda: "2026-01-01T00:00:00Z")
    a3.registry.register("<owner>@household", "<owner>", registered_by="setup",
                         when_utc="2025-12-01T00:00:00Z")
    g5 = a3.issue(r5, "<owner>@household", leg_scope=["L0"], ttl_seconds=3600)
    vr6 = a3.authorize(r5, grant=g5, now="2026-01-01T00:15:00Z")
    check("partial-approval-authorizes-nothing",
          (not vr6.ok) and "PARTIAL_APPROVAL" in vr6.codes, str(vr6.codes))

    # File-presence is not approval.
    stored = {"binding": b.as_dict(), "state": STATE_APPROVED_FOR_EXECUTION,
              "history": [], "data_gaps": [], "notes": []}
    r6 = DecisionRecord.from_dict(stored)
    check("stored-execution-state-demoted",
          r6.is_executable() is False and r6.authority_level() == "NONE",
          "state=%s exec=%s" % (r6.state, r6.is_executable()))
    try:
        enforce_not_executable({"approved": True})
        check("boolean-approval-refused", False, "no exception")
    except ApprovalViolation as exc:
        check("boolean-approval-refused", exc.code == "BOOLEAN_APPROVAL",
              exc.code)

    # --- Consumption must be DURABLE, not in-memory (W9-B A6-06) --------
    # A grant is persisted to disk. If its revocation is not, a restart
    # replays every approval ever issued: durable authorisation with a
    # volatile off-switch.
    tmpd = tempfile.mkdtemp(prefix="approval-consume-")
    try:
        key = generate_key()
        ledger = os.path.join(tmpd, "consumed.jsonl")
        clock = lambda: "2026-01-01T00:00:00Z"  # noqa: E731
        a_first = ApprovalAuthority(key, clock=clock,
                                    consumption_path=ledger)
        a_first.registry.register("<owner>@household", "<owner>",
                                  registered_by="setup",
                                  when_utc="2025-12-01T00:00:00Z")
        r_first = DecisionRecord(binding=b,
                                 state=STATE_HUMAN_APPROVAL_REQUIRED)
        g_first = a_first.issue(r_first, "<owner>@household", ttl_seconds=3600)
        first = a_first.verify(r_first, grant=g_first,
                               now="2026-01-01T00:20:00Z")
        # A FRESH authority sharing the same key and ledger == a restart.
        a_second = ApprovalAuthority(key, clock=clock,
                                     consumption_path=ledger)
        r_second = DecisionRecord(binding=b,
                                  state=STATE_HUMAN_APPROVAL_REQUIRED)
        second = a_second.verify(r_second, grant=g_first,
                                 now="2026-01-01T00:21:00Z")
        check("consumption-is-durable",
              first.ok and (not second.ok)
              and "REPLAYED_APPROVAL" in second.codes,
              "first=%s second=%s" % (first.codes, second.codes))
    finally:
        for root, _dirs, files in os.walk(tmpd):
            for name in files:
                try:
                    os.unlink(os.path.join(root, name))
                except OSError:
                    pass
        try:
            os.rmdir(tmpd)
        except OSError:
            pass

    print("")
    if failures:
        print("FAILURES: %d" % len(failures))
        for f in failures:
            print("  " + f)
        return 1
    print("ALL APPROVAL SELFTESTS PASSED (%s)" % APPROVAL_RULE_VERSION)
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
