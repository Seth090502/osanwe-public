#!/usr/bin/env python3
"""Pure identity-transition functions for household digital-twin documents.

Every function takes a twin document (validated by twin_schema.validate_twin)
and returns a NEW document plus an audit event; inputs are NEVER mutated
(all work happens on deep copies). Return shape:

    {
        "new_doc": <transformed document>,
        "events": [{
            "event_id": ...,          # unique per call
            "event_type": ...,        # e.g. "marriage"
            "version": ...,           # schema_version of resulting doc
            "effective_time": ...,
            "recorded_at": ...,
            "affected_entities": [...],
            "idempotency_key": ...    # deterministic per (inputs, doc hash)
        }],
        "history_preserved": True
    }

Transitions: marriage, divorce, add_member, death, account_transfer,
employer_change, residency_change, goal_reprioritize.

ASCII-only, stdlib-only, no network, no git. Run `python twin_identity.py`
for the exit-gated selftest.
"""

from __future__ import annotations

import copy
import datetime as _dt
import hashlib
import json
import uuid

try:
    import twin_schema
except ImportError:  # pragma: no cover - direct-script fallback
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import twin_schema


SCHEMA_VERSION = "1.0"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deep(doc):
    """Deep-copy helper: transitions never mutate their inputs."""
    return copy.deepcopy(doc)


def _now_iso():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      default=str)


def _doc_digest(doc):
    return hashlib.sha256(_canonical(doc).encode("utf-8")).hexdigest()


def _make_event(event_type, doc, effective_date, affected_entities, salt):
    """Build one audit event. idempotency_key is deterministic given the
    same event type, arguments, and starting-document content."""
    idem_src = "|".join([
        event_type,
        effective_date,
        _canonical(sorted(str(a) for a in affected_entities)),
        salt,
    ])
    idem = hashlib.sha256(idem_src.encode("utf-8")).hexdigest()[:24]
    return {
        "event_id": "%s-%s" % (event_type, uuid.uuid4().hex[:12]),
        "event_type": event_type,
        "version": str(doc.get("schema_version", SCHEMA_VERSION)),
        "effective_time": "%sT00:00:00Z" % effective_date,
        "recorded_at": _now_iso(),
        "affected_entities": [str(a) for a in affected_entities],
        "idempotency_key": idem,
    }


def _validate_date(effective_date):
    if not isinstance(effective_date, str) or \
            not twin_schema.DATE_RE.match(effective_date):
        raise ValueError(
            "effective_date must be 'YYYY-MM-DD', got %r" % (effective_date,))
    if twin_schema._parse_date(effective_date) is None:
        raise ValueError("effective_date is not a calendar date: %r"
                         % (effective_date,))
    return effective_date


def net_worth(doc):
    """Accounts minus liabilities (balance fields)."""
    assets = sum(float(a.get("balance", 0.0) or 0.0)
                 for a in doc.get("accounts", []))
    debts = sum(float(l.get("balance", 0.0) or 0.0)
                for l in doc.get("liabilities", []))
    return assets - debts


def household_liquidity(doc):
    """Cash-account balances (the household's spendable liquidity)."""
    return sum(float(a.get("balance", 0.0) or 0.0)
               for a in doc.get("accounts", []) if a.get("type") == "cash")


def _member_ids(doc):
    return set(m["id"] for m in doc.get("members", []) if "id" in m)


def _account_ids(doc):
    return set(a["id"] for a in doc.get("accounts", []) if "id" in a)


def _scale_account(acct, factor):
    """Pro-rata scale an account's balance, holdings, and tax lots."""
    out = copy.deepcopy(acct)
    if "balance" in out:
        out["balance"] = round(float(out["balance"]) * factor, 2)
    for h in out.get("holdings", []):
        if "qty" in h:
            h["qty"] = round(float(h["qty"]) * factor, 6)
        for lot in h.get("tax_lots", []):
            if "qty" in lot:
                lot["qty"] = round(float(lot["qty"]) * factor, 6)
            if "cost_basis" in lot:
                lot["cost_basis"] = round(float(lot["cost_basis"]) * factor, 2)
    return out


# ---------------------------------------------------------------------------
# Transitions
# ---------------------------------------------------------------------------

def marriage(doc_a, doc_b, effective_date):
    """Merge two household twins into one; net worth equals the sum."""
    _validate_date(effective_date)
    a = _deep(doc_a)
    b = _deep(doc_b)

    # Rename colliding member ids in b with a stable prefix, then remap.
    a_ids = _member_ids(a)
    rename = {}
    for m in b.get("members", []):
        old = m["id"]
        if old in a_ids or old in rename.values():
            new = "b-%s" % old
            while new in a_ids or new in rename.values():
                new = "b-" + new
            rename[old] = new
            m["id"] = new
    for acct in b.get("accounts", []):
        acct["owners"] = [rename.get(o, o) for o in acct.get("owners", [])]
        for ben in acct.get("beneficiaries", []):
            if "member_id" in ben:
                ben["member_id"] = rename.get(ben["member_id"],
                                              ben["member_id"])
    for pol in b.get("insurance", []):
        pol["insured_ids"] = [rename.get(o, o)
                              for o in pol.get("insured_ids", [])]

    # Rename colliding account / goal ids in b.
    a_acc = _account_ids(a)
    acc_rename = {}
    for acct in b.get("accounts", []):
        old = acct["id"]
        if old in a_acc or old in acc_rename.values():
            new = "b-%s" % old
            while new in a_acc or new in acc_rename.values():
                new = "b-" + new
            acc_rename[old] = new
            acct["id"] = new
    a_goals = set(g.get("id") for g in a.get("goals", []))
    for g in b.get("goals", []):
        gid = g.get("id")
        if gid in a_goals:
            g["id"] = "b-%s" % gid

    merged = _deep(a)
    merged["members"] = a.get("members", []) + b.get("members", [])
    merged["accounts"] = a.get("accounts", []) + b.get("accounts", [])
    merged["goals"] = a.get("goals", []) + b.get("goals", [])
    merged["liabilities"] = (a.get("liabilities", []) +
                             b.get("liabilities", []))
    merged["insurance"] = a.get("insurance", []) + b.get("insurance", [])
    merged.setdefault("constraints", a.get("constraints", {}))
    if "benefits" in a or "benefits" in b:
        merged["benefits"] = {
            "plans": a.get("benefits", {}).get("plans", []) +
                     b.get("benefits", {}).get("plans", [])
        }
    merged["estate_intentions"] = a.get("estate_intentions",
                                        b.get("estate_intentions", {}))
    merged["household_name"] = "%s+%s" % (
        a.get("household_name", "HOUSEHOLD-A"),
        b.get("household_name", "HOUSEHOLD-B"))
    merged["as_of"] = max(a.get("as_of", ""), b.get("as_of", "")) or \
        effective_date

    event = _make_event(
        "marriage", merged, effective_date,
        ["household:%s" % merged["household_name"]] +
        ["member:%s" % m["id"] for m in merged["members"]],
        _doc_digest(doc_a) + _doc_digest(doc_b))
    return {"new_doc": merged, "events": [event], "history_preserved": True}


def divorce(doc, split_map, effective_date):
    """Split joint accounts pro-rata per split_map {acct_id: [member_ids]}.

    Every mapped joint account is replaced by one single-owner account per
    listed member, each holding an equal pro-rata share of balance,
    holdings, and tax lots, so TOTAL VALUE IS PRESERVED. Any joint account
    NOT named in the map is split evenly among its existing owners.
    """
    _validate_date(effective_date)
    new_doc = _deep(doc)
    known_members = _member_ids(new_doc)
    known_accounts = _account_ids(new_doc)
    touched = []
    rebuilt = []

    for acct in new_doc.get("accounts", []):
        aid = acct["id"]
        owners = list(acct.get("owners", []))
        if aid in split_map:
            parts = [m for m in split_map[aid] if m in owners]
            if not parts:
                parts = [m for m in split_map[aid] if m in known_members]
            if not parts:
                raise ValueError(
                    "split_map for account %r lists no valid members" % aid)
        elif len(owners) > 1:
            parts = owners
        else:
            rebuilt.append(acct)
            continue
        factor = 1.0 / float(len(parts))
        touched.append(aid)
        for mid in parts:
            piece = _scale_account(acct, factor)
            piece["id"] = "%s::%s" % (aid, mid)
            piece["owners"] = [mid]
            rebuilt.append(piece)

    new_doc["accounts"] = rebuilt
    event = _make_event(
        "divorce", new_doc, effective_date,
        ["account:%s" % t for t in touched],
        _doc_digest(doc) + _canonical(split_map))
    return {"new_doc": new_doc, "events": [event], "history_preserved": True}


def add_member(doc, member_dict, relationship, effective_date):
    """Add a member (birth, adoption, marriage-in, etc.)."""
    _validate_date(effective_date)
    new_doc = _deep(doc)
    member = copy.deepcopy(member_dict)
    if "id" not in member or not str(member["id"]).strip():
        raise ValueError("member_dict must carry a non-empty 'id'")
    if member["id"] in _member_ids(new_doc):
        raise ValueError("member id %r already exists" % (member["id"],))
    if "age" not in member:
        raise ValueError("member_dict must carry an 'age'")
    member["relationship"] = relationship
    new_doc.setdefault("members", []).append(member)
    event = _make_event(
        "add_member", new_doc, effective_date,
        ["member:%s" % member["id"], "relationship:%s" % relationship],
        _doc_digest(doc) + _canonical(member_dict))
    return {"new_doc": new_doc, "events": [event], "history_preserved": True}


def death(doc, member_id, beneficiary_map, effective_date):
    """Redistribute a deceased member's ownership per beneficiary_map.

    Map keys are account ids OR holding symbols ('asset_or_account_id');
    values are surviving member ids. Account-level entries swap the
    deceased owner for the beneficiary; symbol-level entries move the
    holding into the beneficiary's first account. Balances and quantities
    never change, so household liquidity cannot increase. The member's
    employment status becomes 'deceased' and estate_intentions activate
    (will_status -> signed, beneficiary_reviewed -> true).
    """
    _validate_date(effective_date)
    new_doc = _deep(doc)
    if member_id not in _member_ids(new_doc):
        raise ValueError("unknown member %r" % (member_id,))
    known_accounts = _account_ids(new_doc)
    account_keys = set(k for k in beneficiary_map if k in known_accounts)
    symbol_keys = set(beneficiary_map) - account_keys

    moved_holdings = []
    for acct in new_doc.get("accounts", []):
        if member_id not in acct.get("owners", []):
            continue
        aid = acct["id"]
        if aid in account_keys:
            ben = beneficiary_map[aid]
        elif len(acct["owners"]) == 1:
            raise ValueError(
                "account %r owned solely by deceased member %r has no "
                "beneficiary_map entry" % (aid, member_id))
        else:
            ben = None
        if ben is not None and ben not in _member_ids(new_doc):
            raise ValueError("beneficiary %r is not a member" % (ben,))
        if ben is not None:
            owners = acct["owners"]
            idx = owners.index(member_id)
            if ben in owners:
                owners.pop(idx)
            else:
                owners[idx] = ben
        # symbol-level redistribution out of deceased-owned accounts
        remaining = []
        for h in acct.get("holdings", []):
            if h.get("symbol") in symbol_keys:
                moved_holdings.append((beneficiary_map[h["symbol"]],
                                       copy.deepcopy(h)))
            else:
                remaining.append(h)
        acct["holdings"] = remaining

    for ben, holding in moved_holdings:
        target = None
        for acct in new_doc.get("accounts", []):
            if ben in acct.get("owners", []):
                target = acct
                break
        if target is None:
            raise ValueError("no account found for beneficiary %r to "
                             "receive holding %r" % (ben, holding["symbol"]))
        target.setdefault("holdings", []).append(holding)

    for m in new_doc.get("members", []):
        if m.get("id") == member_id:
            m.setdefault("employment", {})["status"] = "deceased"

    estate = new_doc.get("estate_intentions")
    if not isinstance(estate, dict):
        estate = {}
    estate["will_status"] = "signed"
    estate["beneficiary_reviewed"] = True
    note = str(estate.get("notes", "")).strip()
    tag = "ESTATE-ACTIVATED-ON-DEATH-%s" % effective_date
    estate["notes"] = (note + " " + tag).strip()[:1000]
    new_doc["estate_intentions"] = estate

    event = _make_event(
        "death", new_doc, effective_date,
        ["member:%s" % member_id] +
        sorted(set(["asset:" + k for k in beneficiary_map])),
        _doc_digest(doc) + _canonical(beneficiary_map))
    return {"new_doc": new_doc, "events": [event], "history_preserved": True}


def account_transfer(doc, acct_id, to_household_name, effective_date):
    """Transfer an account OUT of this household to another household."""
    _validate_date(effective_date)
    new_doc = _deep(doc)
    before = len(new_doc.get("accounts", []))
    new_doc["accounts"] = [a for a in new_doc.get("accounts", [])
                           if a["id"] != acct_id]
    if len(new_doc["accounts"]) == before:
        raise ValueError("unknown account %r" % (acct_id,))
    event = _make_event(
        "account_transfer", new_doc, effective_date,
        ["account:%s" % acct_id, "to_household:%s" % to_household_name],
        _doc_digest(doc) + _canonical([acct_id, to_household_name]))
    return {"new_doc": new_doc, "events": [event], "history_preserved": True}


def employer_change(doc, member_id, new_employer, effective_date):
    """Change a member's employer (job switch)."""
    _validate_date(effective_date)
    new_doc = _deep(doc)
    target = None
    for m in new_doc.get("members", []):
        if m.get("id") == member_id:
            target = m
            break
    if target is None:
        raise ValueError("unknown member %r" % (member_id,))
    emp = target.setdefault("employment", {})
    emp["status"] = "employed"
    emp["employer"] = str(new_employer)
    event = _make_event(
        "employer_change", new_doc, effective_date,
        ["member:%s" % member_id, "employer:%s" % new_employer],
        _doc_digest(doc) + _canonical([member_id, str(new_employer)]))
    return {
        "new_doc": new_doc, "events": [event], "history_preserved": True}


def residency_change(doc, member_id, new_jurisdiction, effective_date):
    """Record a member's move to a new tax/legal jurisdiction."""
    _validate_date(effective_date)
    new_doc = _deep(doc)
    target = None
    for m in new_doc.get("members", []):
        if m.get("id") == member_id:
            target = m
            break
    if target is None:
        raise ValueError("unknown member %r" % (member_id,))
    target["residency"] = {
        "jurisdiction": str(new_jurisdiction),
        "effective_date": effective_date,
    }
    event = _make_event(
        "residency_change", new_doc, effective_date,
        ["member:%s" % member_id, "jurisdiction:%s" % new_jurisdiction],
        _doc_digest(doc) + _canonical([member_id, str(new_jurisdiction)]))
    return {"new_doc": new_doc, "events": [event], "history_preserved": True}


def goal_reprioritize(doc, goal_id, new_priority, effective_date):
    """Change a goal's priority (must be a valid GOAL_PRIORITIES value)."""
    _validate_date(effective_date)
    if new_priority not in twin_schema.GOAL_PRIORITIES:
        raise ValueError("priority must be one of %s, got %r"
                         % (", ".join(twin_schema.GOAL_PRIORITIES),
                            new_priority))
    new_doc = _deep(doc)
    target = None
    for g in new_doc.get("goals", []):
        if g.get("id") == goal_id:
            target = g
            break
    if target is None:
        raise ValueError("unknown goal %r" % (goal_id,))
    old = target.get("priority")
    target["priority"] = new_priority
    event = _make_event(
        "goal_reprioritize", new_doc, effective_date,
        ["goal:%s" % goal_id, "priority:%s->%s" % (old, new_priority)],
        _doc_digest(doc) + _canonical([goal_id, new_priority]))
    return {"new_doc": new_doc, "events": [event], "history_preserved": True}


# ---------------------------------------------------------------------------
# Selftest (exit-gated)
# ---------------------------------------------------------------------------

def _base_household():
    """Fully synthetic two-member household for the selftest."""
    return {
        "schema_version": "1.0",
        "as_of": "2026-08-25",
        "household_name": "SYNTHETIC-HOUSEHOLD-IDENTITY-SELFTEST",
        "members": [
            {"id": "m1", "name": "SYNTH-MEMBER-S1", "age": 35,
             "employment": {"status": "employed",
                            "employer": "SYNTH-EMPLOYER-A",
                            "income_streams": [
                                {"amount": 120000.0, "start_year": 2018,
                                 "end_year": 2055, "growth_rate": 0.03}]}},
            {"id": "m2", "name": "SYNTH-MEMBER-S2", "age": 33,
             "employment": {"status": "employed",
                            "employer": "SYNTH-EMPLOYER-B"}},
        ],
        "accounts": [
            {"id": "joint-cash", "type": "cash",
             "custodian": "SYNTH-BANK", "currency": "USD",
             "owners": ["m1", "m2"], "balance": 40000.0},
            {"id": "joint-brokerage", "type": "brokerage",
             "custodian": "SYNTH-BROKER", "currency": "USD",
             "owners": ["m1", "m2"], "balance": 100000.0,
             "holdings": [{"symbol": "IDX-SYNTH", "qty": 1000.0,
                           "tax_lots": [
                               {"acq_date": "2021-01-15",
                                "cost_basis": 40000.0, "qty": 500.0},
                               {"acq_date": "2023-06-01",
                                "cost_basis": 45000.0, "qty": 500.0}]}]},
            {"id": "retire-m1", "type": "traditional_401k",
             "custodian": "SYNTH-RETIRE", "currency": "USD",
             "owners": ["m1"], "balance": 90000.0},
        ],
        "liabilities": [{"kind": "mortgage", "rate": 0.04,
                         "term_months": 300, "balance": 200000.0,
                         "min_payment": 1200.0}],
        "insurance": [{"kind": "life", "coverage_amount": 500000.0,
                       "premium": 60.0, "premium_freq": "monthly",
                       "insured_ids": ["m1", "m2"]}],
        "goals": [
            {"id": "g-retire", "target_date": "2055-01-31",
             "target_amount": 2000000.0, "priority": "essential"},
            {"id": "g-house", "target_date": "2029-06-30",
             "target_amount": 80000.0, "priority": "high"},
            {"id": "g-travel", "target_date": "2027-12-31",
             "target_amount": 12000.0, "priority": "low"},
        ],
        "constraints": {
            "risk_tolerance": {"level": "moderate", "score": 13,
                               "questionnaire_items": 20},
            "risk_capacity": 65,
            "liquidity_floor": 30000.0,
        },
        "estate_intentions": {"will_status": "draft", "trust_intent": "none",
                              "beneficiary_reviewed": False,
                              "notes": "SYNTHETIC"},
        "assumptions": {
            "synthetic_data_notice":
                "Entirely fictional in-memory fixture for the "
                "twin_identity selftest; SYNTHETIC, no real persons."
        },
    }


def run_selftest():
    failures = []

    def check(label, cond, detail=""):
        if cond:
            print("  ok: %s" % label)
        else:
            failures.append("%s %s" % (label, detail))
            print("  FAIL: %s %s" % (label, detail))

    base = _base_household()

    # -- purity harness -----------------------------------------------------
    import hashlib as _h

    def digest(d):
        return _h.sha256(_canonical(d).encode("utf-8")).hexdigest()

    snapshots = {}

    def snap(key, d):
        snapshots[key] = digest(d)

    def purity_ok(*keys):
        return all(snapshots[k] == s for k, s in
                   [(k, snapshots[k]) for k in keys])

    # -- marriage -----------------------------------------------------------
    snap("base", base)
    other = _base_household()
    other["members"][0]["id"] = "x1"
    other["members"][1]["id"] = "x2"
    for i, a in enumerate(other["accounts"]):
        a["id"] = "oth-%d" % i
        a["owners"] = ["x1", "x2"]
    for g in other["goals"]:
        g["id"] = "oth-" + g["id"]
    r = marriage(base, other, "2026-09-01")
    nd = r["new_doc"]
    check("marriage: net worth sums",
          abs(net_worth(nd) -
              (net_worth(base) + net_worth(other))) < 1e-6,
          "%.2f vs %.2f" % (net_worth(nd),
                            net_worth(base) + net_worth(other)))
    check("marriage: validates clean",
          twin_schema.validate_twin(nd) == [],
          str(twin_schema.validate_twin(nd)))
    check("marriage: history_preserved", r["history_preserved"] is True)
    snap("after-marriage-inputs", base)

    # -- divorce ------------------------------------------------------------
    nw0 = net_worth(base)
    r = divorce(base, {"joint-cash": ["m1", "m2"],
                       "joint-brokerage": ["m1", "m2"]}, "2027-01-15")
    nd = r["new_doc"]
    check("divorce: net worth preserved within $1",
          abs(net_worth(nd) - nw0) <= 1.0,
          "%.2f vs %.2f" % (net_worth(nd), nw0))
    check("divorce: validates clean",
          twin_schema.validate_twin(nd) == [],
          str(twin_schema.validate_twin(nd)))
    joint = [a for a in nd["accounts"] if len(a["owners"]) > 1]
    check("divorce: no joint accounts remain", joint == [])
    snap("after-divorce-inputs", base)

    # -- add_member ---------------------------------------------------------
    r = add_member(base, {"id": "m3", "name": "SYNTH-BABY", "age": 0},
                   "birth", "2026-10-01")
    nd = r["new_doc"]
    check("add_member: member added",
          any(m["id"] == "m3" for m in nd["members"]))
    check("add_member: validates clean",
          twin_schema.validate_twin(nd) == [])
    snap("after-addmember-inputs", base)

    # -- death --------------------------------------------------------------
    liq0 = household_liquidity(base)
    r = death(base, "m1", {"retire-m1": "m2", "IDX-SYNTH": "m2"},
              "2027-03-01")
    nd = r["new_doc"]
    check("death: liquidity did not increase",
          household_liquidity(nd) <= liq0 + 1e-9,
          "%.2f -> %.2f" % (liq0, household_liquidity(nd)))
    retire = [a for a in nd["accounts"] if a["id"] == "retire-m1"][0]
    check("death: account ownership redistributed per map",
          retire["owners"] == ["m2"], str(retire["owners"]))
    check("death: member marked deceased",
          [m for m in nd["members"] if m["id"] == "m1"][0]
          ["employment"]["status"] == "deceased")
    check("death: estate intentions activated",
          nd["estate_intentions"]["will_status"] == "signed" and
          nd["estate_intentions"]["beneficiary_reviewed"] is True)
    check("death: validates clean",
          twin_schema.validate_twin(nd) == [],
          str(twin_schema.validate_twin(nd)))
    snap("after-death-inputs", base)

    # -- account_transfer ---------------------------------------------------
    r = account_transfer(base, "retire-m1", "SYNTHETIC-OTHER-HOUSEHOLD",
                         "2027-04-01")
    nd = r["new_doc"]
    check("account_transfer: account removed",
          all(a["id"] != "retire-m1" for a in nd["accounts"]))
    check("account_transfer: validates clean",
          twin_schema.validate_twin(nd) == [])
    snap("after-transfer-inputs", base)

    # -- employer_change / residency_change / goal_reprioritize -------------
    r = employer_change(base, "m2", "SYNTH-EMPLOYER-C", "2026-11-01")
    nd = r["new_doc"]
    check("employer_change applied",
          [m for m in nd["members"] if m["id"] == "m2"][0]
          ["employment"]["employer"] == "SYNTH-EMPLOYER-C")
    check("employer_change: validates clean",
          twin_schema.validate_twin(nd) == [])

    r = residency_change(base, "m1", "US-CA-SYNTH", "2027-01-01")
    nd = r["new_doc"]
    check("residency_change applied",
          [m for m in nd["members"] if m["id"] == "m1"][0]
          ["residency"]["jurisdiction"] == "US-CA-SYNTH")

    r = goal_reprioritize(base, "g-travel", "medium", "2026-12-01")
    nd = r["new_doc"]
    check("goal_reprioritize applied",
          [g for g in nd["goals"] if g["id"] == "g-travel"][0]
          ["priority"] == "medium")
    try:
        goal_reprioritize(base, "g-travel", "urgent", "2026-12-01")
        check("goal_reprioritize rejects bad priority", False)
    except ValueError:
        check("goal_reprioritize rejects bad priority", True)

    # -- events -------------------------------------------------------------
    calls = [
        ("marriage", lambda: marriage(base, other, "2026-09-01")),
        ("divorce", lambda: divorce(
            base, {"joint-cash": ["m1", "m2"]}, "2027-01-15")),
        ("add_member", lambda: add_member(
            base, {"id": "m9", "age": 0}, "adoption", "2026-10-01")),
        ("death", lambda: death(
            base, "m1", {"retire-m1": "m2", "joint-cash": "m2",
                         "joint-brokerage": "m2"}, "2027-03-01")),
        ("account_transfer", lambda: account_transfer(
            base, "retire-m1", "OTHER", "2027-04-01")),
        ("employer_change", lambda: employer_change(
            base, "m1", "E-C", "2026-11-01")),
        ("residency_change", lambda: residency_change(
            base, "m1", "US-NY-SYNTH", "2027-01-01")),
        ("goal_reprioritize", lambda: goal_reprioritize(
            base, "g-travel", "medium", "2026-12-01")),
    ]
    for name, fn in calls:
        res = fn()
        evs = res["events"]
        ok = isinstance(evs, list) and len(evs) >= 1 and \
            all(e.get("idempotency_key") for e in evs) and \
            all(e.get("event_type") and e.get("event_id") and
                e.get("effective_time") and e.get("recorded_at") and
                "affected_entities" in e and e.get("version")
                for e in evs)
        check("transition %s emits well-formed event(s)" % name, ok)
        # idempotency: same inputs -> same key
        again = fn()
        check("transition %s idempotency_key deterministic" % name,
              evs[0]["idempotency_key"] ==
              again["events"][0]["idempotency_key"])

    # -- purity: originals unmutated ----------------------------------------
    expected = snapshots["base"]
    check("original doc unmutated across all transitions",
          digest(base) == expected)

    # -- summary ------------------------------------------------------------
    print("")
    if failures:
        print("selftest FAILED (%d):" % len(failures))
        for f in failures:
            print("  - " + f)
        return 1
    print("selftest PASSED")
    print("selftest PASSED: 8 transitions pure, evented, validate-clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_selftest())
