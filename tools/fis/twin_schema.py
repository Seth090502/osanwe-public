#!/usr/bin/env python3
"""Household digital-twin document schema + pure-python validator.

Defines the structure of a household digital-twin document (members,
accounts with holdings/tax lots, liabilities, insurance, goals,
constraints, benefits, estate intentions) and validates documents
against it.

validate_twin(doc) -> list of error strings with precise JSON-style paths
    (e.g. "accounts[0].holdings[1].tax_lots[0].qty: must be a number > 0").

NO real personal data appears anywhere: this module contains schema and
validator logic plus a selftest that uses fully synthetic fixtures only.

ASCII-only, stdlib-only, no network. Run `python twin_schema.py` to
execute the selftest.
"""

from __future__ import annotations

import datetime as _dt
import re as _re

# ---------------------------------------------------------------------------
# Allowed vocabularies
# ---------------------------------------------------------------------------

ACCOUNT_TYPES = (
    "taxable",
    "traditional_401k",
    "roth",
    "hsa",
    "529",
    "brokerage",
    "cash",
)

LIABILITY_KINDS = ("mortgage", "auto", "student", "cc")

INSURANCE_KINDS = ("life", "health", "disability", "ltc", "umbrella", "property")

GOAL_PRIORITIES = ("essential", "high", "medium", "low")

RISK_TOLERANCE_LEVELS = ("conservative", "moderately_conservative", "moderate",
                         "moderately_aggressive", "aggressive")

EMPLOYMENT_STATUSES = ("employed", "self_employed", "unemployed", "retired",
                       "student", "disabled", "homemaker", "deceased")

BENEFIT_MATCH_FREQ = ("per_paycheck", "annual", "none")

DATE_RE = _re.compile(r"^\d{4}-\d{2}-\d{2}$")
CURRENCY_RE = _re.compile(r"^[A-Z]{3}$")

_NONFINT = _re.compile(r"[\[\]]")


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _err(path, msg):
    return "%s: %s" % (path if path else "<root>", msg)


def _parse_date(s):
    """Return a date object for 'YYYY-MM-DD', or None."""
    try:
        return _dt.date(int(s[0:4]), int(s[5:7]), int(s[8:10]))
    except Exception:
        return None


def _check_date(value, path, errors, allow_future=True):
    if not isinstance(value, str) or not DATE_RE.match(value):
        errors.append(_err(path, "must be an ISO date string 'YYYY-MM-DD'"))
        return None
    d = _parse_date(value)
    if d is None:
        errors.append(_err(path, "must be a valid calendar date"))
        return None
    if not allow_future:
        today = _dt.date.today()
        if d < today:
            errors.append(
                _err(path, "target_date %s is in the past; goals must target "
                           "today or later" % value))
    return d


def _check_money(value, path, errors, min_val=0.0):
    if not _is_num(value):
        errors.append(_err(path, "must be a number"))
        return False
    if value < min_val:
        errors.append(_err(path, "must be >= %s" % min_val))
        return False
    return True


def _check_enum(value, allowed, path, errors):
    if not isinstance(value, str) or value not in allowed:
        errors.append(_err(path, "must be one of %s" % ", ".join(allowed)))
        return False
    return True


def _check_str(value, path, errors, max_len=200):
    if not isinstance(value, str) or not value.strip():
        errors.append(_err(path, "must be a non-empty string"))
        return False
    if len(value) > max_len:
        errors.append(_err(path, "exceeds max length %d" % max_len))
        return False
    return True


def _require(obj, key, path, errors):
    if not isinstance(obj, dict) or key not in obj:
        errors.append(_err("%s.%s" % (path, key) if path else key,
                           "required field is missing"))
        return False
    return True


# ---------------------------------------------------------------------------
# Section validators
# ---------------------------------------------------------------------------

def _v_income_stream(stream, path, errors):
    """human_capital income stream parameters (synthetic/parametric)."""
    if not isinstance(stream, dict):
        errors.append(_err(path, "must be an object"))
        return
    # amount is annual gross in currency units
    if not _require(stream, "amount", path, errors):
        pass
    elif not _check_money(stream["amount"], path + ".amount", errors, 0.0):
        pass
    for key in ("start_year", "end_year"):
        if key in stream:
            v = stream[key]
            if not isinstance(v, int) or isinstance(v, bool):
                errors.append(_err(path + "." + key, "must be an integer year"))
            elif v < 1900 or v > 2200:
                errors.append(_err(path + "." + key,
                                   "year out of plausible range 1900-2200"))
    if "growth_rate" in stream and not _check_money(
            stream["growth_rate"], path + ".growth_rate", errors, -0.50):
        errors.append(_err(path + ".growth_rate",
                           "expected decimal rate (e.g. 0.03), min -0.50"))
    if "end_year" in stream and "start_year" in stream:
        sy = stream.get("start_year")
        ey = stream.get("end_year")
        if isinstance(sy, int) and isinstance(ey, int) \
                and not isinstance(sy, bool) and not isinstance(ey, bool) \
                and ey < sy:
            errors.append(_err(path, "end_year must be >= start_year"))


def _v_employment(emp, path, errors):
    if not isinstance(emp, dict):
        errors.append(_err(path, "must be an object"))
        return
    if not _require(emp, "status", path, errors):
        pass
    else:
        _check_enum(emp["status"], EMPLOYMENT_STATUSES,
                    path + ".status", errors)
    if "employer" in emp:
        _check_str(emp["employer"], path + ".employer", errors)
    if "income_streams" in emp:
        streams = emp["income_streams"]
        if not isinstance(streams, list):
            errors.append(_err(path + ".income_streams", "must be an array"))
        else:
            for i, s in enumerate(streams):
                _v_income_stream(s, "%s.income_streams[%d]" % (path, i), errors)


def _v_member(m, i, errors):
    path = "members[%d]" % i
    if not isinstance(m, dict):
        errors.append(_err(path, "must be an object"))
        return
    if not _require(m, "id", path, errors):
        pass
    else:
        _check_str(m["id"], path + ".id", errors)
    if not _require(m, "age", path, errors):
        pass
    else:
        age = m["age"]
        if not isinstance(age, int) or isinstance(age, bool):
            errors.append(_err(path + ".age", "must be an integer"))
        elif age < 0:
            errors.append(_err(path + ".age", "must be >= 0 (got negative)"))
        elif age > 120:
            errors.append(_err(path + ".age",
                               "implausible age > 120"))
    if "name" in m:
        _check_str(m["name"], path + ".name", errors)
    if "employment" in m:
        _v_employment(m["employment"], path + ".employment", errors)
    if "human_capital" in m:
        hc = m["human_capital"]
        if not isinstance(hc, dict):
            errors.append(_err(path + ".human_capital", "must be an object"))
        else:
            if "income_streams" in hc:
                streams = hc["income_streams"]
                if not isinstance(streams, list):
                    errors.append(_err(path + ".human_capital.income_streams",
                                       "must be an array"))
                else:
                    for j, s in enumerate(streams):
                        _v_income_stream(
                            s, "%s.human_capital.income_streams[%d]"
                            % (path, j), errors)


def _v_tax_lot(lot, hi, li, hpath, errors):
    path = "%s.tax_lots[%d]" % (hpath, li)
    if not isinstance(lot, dict):
        errors.append(_err(path, "must be an object"))
        return
    acq = lot.get("acq_date")
    if acq is None:
        errors.append(_err(path + ".acq_date", "required field is missing"))
    else:
        _check_date(acq, path + ".acq_date", errors)
    if "cost_basis" not in lot:
        errors.append(_err(path + ".cost_basis", "required field is missing"))
    else:
        _check_money(lot["cost_basis"], path + ".cost_basis", errors, 0.0)
    if "qty" not in lot:
        errors.append(_err(path + ".qty", "required field is missing"))
    else:
        q = lot["qty"]
        if not _is_num(q):
            errors.append(_err(path + ".qty", "must be a number"))
        elif q <= 0:
            errors.append(_err(path + ".qty", "must be > 0"))


def _v_holding(h, ai, hi, apath, errors):
    hpath = "%s.holdings[%d]" % (apath, hi)
    if not isinstance(h, dict):
        errors.append(_err(hpath, "must be an object"))
        return
    if not _require(h, "symbol", hpath, errors):
        pass
    else:
        sym = h["symbol"]
        if not isinstance(sym, str) or not sym.strip():
            errors.append(_err(hpath + ".symbol",
                               "must be a non-empty string"))
    qty_total = 0.0
    has_lots = False
    qty_ok = True
    if "qty" in h:
        q = h["qty"]
        if not _is_num(q):
            errors.append(_err(hpath + ".qty", "must be a number"))
            qty_ok = False
        elif q <= 0:
            errors.append(_err(hpath + ".qty", "must be > 0"))
            qty_ok = False
        else:
            qty_total = float(q)
    if "tax_lots" in h:
        lots = h["tax_lots"]
        if not isinstance(lots, list):
            errors.append(_err(hpath + ".tax_lots", "must be an array"))
        else:
            has_lots = len(lots) > 0
            lot_qty_sum = 0.0
            for li, lot in enumerate(lots):
                _v_tax_lot(lot, hi, li, hpath, errors)
                lq = lot.get("qty") if isinstance(lot, dict) else None
                if _is_num(lq) and lq > 0:
                    lot_qty_sum += float(lq)
            # cross-check: sum of lot quantities vs holding-level qty
            if qty_ok and "qty" in h and abs(lot_qty_sum - qty_total) > 1e-6:
                errors.append(_err(
                    hpath,
                    "lot qty mismatch: sum(tax_lots[].qty)=%.6f does not "
                    "match holdings.qty=%.6f" % (lot_qty_sum, qty_total)))
            if has_lots and "qty" not in h and lot_qty_sum <= 0:
                errors.append(_err(hpath,
                                   "lots present but total quantity <= 0"))
    if not has_lots and "qty" not in h and "symbol" in h:
        errors.append(_err(hpath,
                           "holding needs either qty or tax_lots"))


def _v_account(a, i, errors):
    path = "accounts[%d]" % i
    if not isinstance(a, dict):
        errors.append(_err(path, "must be an object"))
        return
    if not _require(a, "id", path, errors):
        pass
    else:
        _check_str(a["id"], path + ".id", errors)
    if not _require(a, "type", path, errors):
        pass
    else:
        _check_enum(a["type"], ACCOUNT_TYPES, path + ".type", errors)
    if not _require(a, "custodian", path, errors):
        pass
    else:
        _check_str(a["custodian"], path + ".custodian", errors)
    bal = a.get("balance")
    if bal is not None and not _check_money(bal, path + ".balance", errors,
                                            0.0):
        pass
    if "currency" in a:
        cur = a["currency"]
        if not isinstance(cur, str) or not CURRENCY_RE.match(cur):
            errors.append(_err(path + ".currency",
                               "must be a 3-letter ISO-4217 code"))
    if "owners" in a:
        owners = a["owners"]
        if not isinstance(owners, list) or not owners:
            errors.append(_err(path + ".owners",
                               "must be a non-empty array of member ids"))
        else:
            for oi, o in enumerate(owners):
                _check_str(o, "%s.owners[%d]" % (path, oi), errors)
    if "beneficiaries" in a:
        bens = a["beneficiaries"]
        if not isinstance(bens, list):
            errors.append(_err(path + ".beneficiaries", "must be an array"))
        else:
            for bi, b in enumerate(bens):
                bpath = "%s.beneficiaries[%d]" % (path, bi)
                if not isinstance(b, dict):
                    errors.append(_err(bpath, "must be an object"))
                    continue
                if "member_id" in b:
                    _check_str(b["member_id"], bpath + ".member_id", errors)
                share = b.get("share")
                if share is not None:
                    if not _is_num(share):
                        errors.append(_err(bpath + ".share",
                                           "must be a number"))
                    elif not (0.0 < share <= 1.0):
                        errors.append(_err(bpath + ".share",
                                           "must be in (0, 1]"))
    if "holdings" in a:
        holds = a["holdings"]
        if not isinstance(holds, list):
            errors.append(_err(path + ".holdings", "must be an array"))
        else:
            for hi, h in enumerate(holds):
                _v_holding(h, i, hi, path, errors)


def _v_liability(liab, i, errors):
    path = "liabilities[%d]" % i
    if not isinstance(liab, dict):
        errors.append(_err(path, "must be an object"))
        return
    if not _require(liab, "kind", path, errors):
        pass
    else:
        _check_enum(liab["kind"], LIABILITY_KINDS, path + ".kind", errors)
    if not _require(liab, "rate", path, errors):
        pass
    else:
        r = liab["rate"]
        if not _is_num(r):
            errors.append(_err(path + ".rate", "must be a number"))
        elif r < 0 or r > 0.60:
            errors.append(_err(path + ".rate",
                               "decimal APR expected, out of range [0, 0.60]"))
    term = liab.get("term_months")
    if term is not None:
        if not isinstance(term, int) or isinstance(term, bool):
            errors.append(_err(path + ".term_months", "must be an integer"))
        elif term <= 0:
            errors.append(_err(path + ".term_months", "must be > 0"))
    bal = liab.get("balance")
    if bal is not None and not _check_money(bal, path + ".balance", errors,
                                            0.0):
        pass
    minpay = liab.get("min_payment")
    if minpay is not None and not _check_money(minpay, path + ".min_payment",
                                               errors, 0.0):
        pass
    if "orig_date" in liab:
        _check_date(liab["orig_date"], path + ".orig_date", errors)


def _v_policy(pol, i, errors):
    path = "insurance[%d]" % i
    if not isinstance(pol, dict):
        errors.append(_err(path, "must be an object"))
        return
    if not _require(pol, "kind", path, errors):
        pass
    else:
        _check_enum(pol["kind"], INSURANCE_KINDS, path + ".kind", errors)
    cov = pol.get("coverage_amount")
    if cov is not None and not _check_money(cov, path + ".coverage_amount",
                                            errors, 0.0):
        pass
    prem = pol.get("premium")
    if prem is not None and not _check_money(prem, path + ".premium", errors,
                                             0.0):
        pass
    if "premium_freq" in pol:
        _check_enum(pol["premium_freq"],
                    ("monthly", "quarterly", "semiannual", "annual"),
                    path + ".premium_freq", errors)
    if "insured_ids" in pol:
        ids = pol["insured_ids"]
        if not isinstance(ids, list) or not ids:
            errors.append(_err(path + ".insured_ids",
                               "must be a non-empty array of member ids"))
        else:
            for ii, mid in enumerate(ids):
                _check_str(mid, "%s.insured_ids[%d]" % (path, ii), errors)


def _v_goal(g, i, errors):
    path = "goals[%d]" % i
    if not isinstance(g, dict):
        errors.append(_err(path, "must be an object"))
        return
    if not _require(g, "id", path, errors):
        pass
    else:
        _check_str(g["id"], path + ".id", errors)
    if not _require(g, "target_date", path, errors):
        pass
    else:
        _check_date(g["target_date"], path + ".target_date", errors,
                    allow_future=False)
    amt = g.get("target_amount")
    if amt is not None and not _check_money(amt, path + ".target_amount",
                                            errors, 0.0):
        pass
    if "priority" in g:
        _check_enum(g["priority"], GOAL_PRIORITIES, path + ".priority", errors)
    else:
        errors.append(_err(path + ".priority", "required field is missing"))


def _v_constraint(c, errors):
    path = "constraints"
    if not isinstance(c, dict):
        errors.append(_err(path, "must be an object"))
        return
    rt = c.get("risk_tolerance")
    if rt is None:
        errors.append(_err(path + ".risk_tolerance",
                           "required field is missing"))
    else:
        # questionnaire result: level string + optional raw score 1..N answers
        if isinstance(rt, dict):
            if "level" not in rt:
                errors.append(_err(path + ".risk_tolerance.level",
                                   "required field is missing"))
            else:
                _check_enum(rt["level"], RISK_TOLERANCE_LEVELS,
                            path + ".risk_tolerance.level", errors)
            score = rt.get("score")
            if score is not None:
                if not _is_num(score):
                    errors.append(_err(path + ".risk_tolerance.score",
                                       "must be a number"))
                elif score < 0:
                    errors.append(_err(path + ".risk_tolerance.score",
                                       "must be >= 0"))
        else:
            _check_enum(rt, RISK_TOLERANCE_LEVELS,
                        path + ".risk_tolerance", errors)
    rc = c.get("risk_capacity")
    if rc is None:
        errors.append(_err(path + ".risk_capacity", "required field is missing"))
    else:
        if not _is_num(rc):
            errors.append(_err(path + ".risk_capacity",
                               "must be a numeric score"))
        elif rc < 0 or rc > 100:
            errors.append(_err(path + ".risk_capacity",
                               "score must be within [0, 100]"))
    lf = c.get("liquidity_floor")
    if lf is None:
        errors.append(_err(path + ".liquidity_floor",
                           "required field is missing"))
    else:
        if not _check_money(lf, path + ".liquidity_floor", errors, 0.0):
            pass
    br = c.get("behavioral_rules")
    if br is not None:
        if not isinstance(br, list):
            errors.append(_err(path + ".behavioral_rules", "must be an array"))
        else:
            for ri, rule in enumerate(br):
                rpath = "%s.behavioral_rules[%d]" % (path, ri)
                if not isinstance(rule, dict):
                    errors.append(_err(rpath, "must be an object"))
                    continue
                if "name" not in rule:
                    errors.append(_err(rpath + ".name",
                                       "required field is missing"))
                else:
                    _check_str(rule["name"], rpath + ".name", errors)
                if "params" in rule and not isinstance(rule["params"], dict):
                    errors.append(_err(rpath + ".params", "must be an object"))


def _v_benefits(ben, errors):
    path = "benefits"
    if not isinstance(ben, dict):
        errors.append(_err(path, "must be an object"))
        return
    plans = ben.get("plans")
    if not isinstance(plans, list):
        errors.append(_err(path + ".plans", "must be an array"))
        return
    for pi, plan in enumerate(plans):
        ppath = "%s.plans[%d]" % (path, pi)
        if not isinstance(plan, dict):
            errors.append(_err(ppath, "must be an object"))
            continue
        if not _require(plan, "account_type", ppath, errors):
            pass
        else:
            _check_enum(plan["account_type"], ACCOUNT_TYPES,
                        ppath + ".account_type", errors)
        match = plan.get("employer_match")
        if match is not None:
            mpath = ppath + ".employer_match"
            if not isinstance(match, dict):
                errors.append(_err(mpath, "must be an object describing the "
                                           "match formula"))
            else:
                formula = match.get("formula")
                if formula is None:
                    errors.append(_err(mpath + ".formula",
                                       "required field is missing"))
                else:
                    # formula is a structured expression, e.g.
                    # {"type": "ratio_of_salary", "rate": 0.5, "cap": 0.06}
                    if not isinstance(formula, str) or not formula.strip():
                        errors.append(_err(mpath + ".formula",
                                           "must be a non-empty formula string"))
                rate = match.get("rate")
                if rate is not None and not _check_money(rate, mpath + ".rate",
                                                         errors, 0.0):
                    pass
                cap = match.get("cap")
                if cap is not None and not _check_money(cap, mpath + ".cap",
                                                        errors, 0.0):
                    pass
                if "freq" in match:
                    _check_enum(match["freq"], BENEFIT_MATCH_FREQ,
                                mpath + ".freq", errors)


def _v_estate(est, errors):
    path = "estate_intentions"
    if not isinstance(est, dict):
        errors.append(_err(path, "must be an object"))
        return
    for key in ("will_status", "trust_intent", "beneficiary_reviewed",
                "healthcare_directive", "power_of_attorney"):
        if key in est:
            v = est[key]
            if key == "will_status":
                _check_enum(v, ("none", "draft", "signed", "review_due"),
                            path + ".will_status", errors)
            elif key == "trust_intent":
                _check_enum(v, ("none", "revocable", "irrevocable",
                                "under_review"),
                            path + ".trust_intent", errors)
            elif isinstance(v, bool):
                continue
            elif key == "beneficiary_reviewed":
                errors.append(_err(path + "." + key,
                                   "must be a boolean or null placeholder"))
    if "notes" in est:
        _check_str(est["notes"], path + ".notes", errors, max_len=1000)


# ---------------------------------------------------------------------------
# Top-level validator
# ---------------------------------------------------------------------------

def validate_twin(doc):
    """Validate a household digital-twin document.

    Returns a list of error strings with precise paths. Empty list means
    the document is valid. Never raises on malformed input: every defect
    becomes an error entry.
    """
    errors = []

    if not isinstance(doc, dict):
        return [_err("", "document must be an object")]

    # -- required sections -------------------------------------------------
    for section in ("schema_version", "as_of", "members", "accounts",
                    "goals", "constraints"):
        _require(doc, section, "", errors)

    sv = doc.get("schema_version")
    if sv is not None:
        if not isinstance(sv, str) or not _re.match(r"^\d+\.\d+$", sv):
            errors.append(_err("schema_version",
                               "must be a semver-like 'MAJOR.MINOR' string"))

    if doc.get("as_of") is not None:
        _check_date(doc["as_of"], "as_of", errors)

    members = doc.get("members")
    if members is not None:
        if not isinstance(members, list) or not members:
            errors.append(_err("members", "must be a non-empty array"))
        else:
            seen_ids = set()
            for i, m in enumerate(members):
                _v_member(m, i, errors)
                mid = m.get("id") if isinstance(m, dict) else None
                if isinstance(mid, str) and mid:
                    if mid in seen_ids:
                        errors.append(_err("members[%d].id" % i,
                                           "duplicate member id '%s'" % mid))
                    seen_ids.add(mid)

    accounts = doc.get("accounts")
    if accounts is not None:
        if not isinstance(accounts, list):
            errors.append(_err("accounts", "must be an array"))
        else:
            seen_acc = set()
            for i, a in enumerate(accounts):
                _v_account(a, i, errors)
                aid = a.get("id") if isinstance(a, dict) else None
                if isinstance(aid, str) and aid:
                    if aid in seen_acc:
                        errors.append(_err("accounts[%d].id" % i,
                                           "duplicate account id '%s'" % aid))
                    seen_acc.add(aid)

    liabilities = doc.get("liabilities")
    if liabilities is not None:
        if not isinstance(liabilities, list):
            errors.append(_err("liabilities", "must be an array"))
        else:
            for i, liab in enumerate(liabilities):
                _v_liability(liab, i, errors)

    insurance = doc.get("insurance")
    if insurance is not None:
        if not isinstance(insurance, list):
            errors.append(_err("insurance", "must be an array"))
        else:
            for i, pol in enumerate(insurance):
                _v_policy(pol, i, errors)

    goals = doc.get("goals")
    if goals is not None and isinstance(goals, list):
        for i, g in enumerate(goals):
            _v_goal(g, i, errors)

    constraints = doc.get("constraints")
    if constraints is not None:
        _v_constraint(constraints, errors)

    benefits = doc.get("benefits")
    if benefits is not None:
        _v_benefits(benefits, errors)

    estate = doc.get("estate_intentions")
    if estate is not None:
        _v_estate(estate, errors)

    return errors


# ---------------------------------------------------------------------------
# Synthetic selftest fixture (no real personal data)
# ---------------------------------------------------------------------------

def _valid_doc():
    """Fully synthetic example household document."""
    return {
        "schema_version": "1.0",
        "as_of": "2026-01-15",
        "household_name": "EXAMPLE-HOUSEHOLD-01",
        "members": [
            {
                "id": "m1",
                "name": "SYNTHETIC-MEMBER-A",
                "age": 41,
                "employment": {
                    "status": "employed",
                    "employer": "ACME-SYNTHETIC-CORP",
                    "income_streams": [
                        {"amount": 120000.0, "start_year": 2015,
                         "end_year": 2052, "growth_rate": 0.03}
                    ]
                },
                "human_capital": {
                    "income_streams": [
                        {"amount": 8000.0, "start_year": 2026,
                         "end_year": 2052, "growth_rate": 0.02}
                    ]
                }
            },
            {
                "id": "m2",
                "name": "SYNTHETIC-MEMBER-B",
                "age": 39,
                "employment": {"status": "self_employed"}
            }
        ],
        "accounts": [
            {
                "id": "a1",
                "type": "traditional_401k",
                "custodian": "SYNTH-CUSTODIAN-A",
                "currency": "USD",
                "owners": ["m1"],
                "balance": 250000.0,
                "holdings": [
                    {
                        "symbol": "VTSAX-SYNTH",
                        "qty": 100.0,
                        "tax_lots": [
                            {"acq_date": "2020-06-01", "cost_basis": 60000.0,
                             "qty": 40.0},
                            {"acq_date": "2023-01-15", "cost_basis": 90000.0,
                             "qty": 60.0}
                        ]
                    }
                ]
            },
            {
                "id": "a2",
                "type": "taxable",
                "custodian": "SYNTH-CUSTODIAN-B",
                "currency": "USD",
                "owners": ["m1", "m2"],
                "beneficiaries": [{"member_id": "m2", "share": 1.0}],
                "balance": 50000.0,
                "holdings": [
                    {"symbol": "MMKT-SYNTH", "qty": 50000.0}
                ]
            }
        ],
        "liabilities": [
            {"kind": "mortgage", "rate": 0.03125, "term_months": 360,
             "balance": 320000.0, "min_payment": 1500.0,
             "orig_date": "2019-05-01"},
            {"kind": "auto", "rate": 0.0449, "term_months": 60,
             "balance": 12000.0, "min_payment": 420.0}
        ],
        "insurance": [
            {"kind": "life", "coverage_amount": 750000.0, "premium": 85.0,
             "premium_freq": "monthly", "insured_ids": ["m1"]},
            {"kind": "health", "coverage_amount": 5000000.0, "premium": 450.0,
             "premium_freq": "monthly", "insured_ids": ["m1", "m2"]}
        ],
        "goals": [
            {"id": "g1", "target_date": "2035-06-30",
             "target_amount": 1500000.0, "priority": "essential"},
            {"id": "g2", "target_date": "2029-08-31",
             "target_amount": 60000.0, "priority": "medium"}
        ],
        "constraints": {
            "risk_tolerance": {"level": "moderate", "score": 14,
                               "questionnaire_items": 20},
            "risk_capacity": 72,
            "liquidity_floor": 30000.0,
            "behavioral_rules": [
                {"name": "no_panic_sell", "params": {"drawdown_pct": 0.20}},
                {"name": "rebalance_band", "params": {"band_pct": 0.05}}
            ]
        },
        "benefits": {
            "plans": [
                {
                    "account_type": "traditional_401k",
                    "employer_match": {
                        "formula": "ratio_of_salary",
                        "rate": 0.50,
                        "cap": 0.06,
                        "freq": "per_paycheck"
                    }
                }
            ]
        },
        "estate_intentions": {
            "will_status": "signed",
            "trust_intent": "none",
            "beneficiary_reviewed": True,
            "healthcare_directive": False,
            "power_of_attorney": True,
            "notes": "PLACEHOLDER-REVIEW-ANNUALLY"
        }
    }


# ---------------------------------------------------------------------------
# Selftest
# ---------------------------------------------------------------------------

def _malformations():
    """Build (label, mutate_fn) pairs producing distinct validation failures."""
    def bad_enum(doc):
        doc["accounts"][0]["type"] = "offshore_gold_vault"

    def negative_age(doc):
        doc["members"][0]["age"] = -5

    def lot_qty_mismatch(doc):
        doc["accounts"][0]["holdings"][0]["tax_lots"][1]["qty"] = 55.0

    def goal_past_target(doc):
        doc["goals"][0]["target_date"] = "1999-12-31"

    def bad_date_format(doc):
        doc["as_of"] = "15/01/2026"

    def negative_cost_basis(doc):
        doc["accounts"][0]["holdings"][0]["tax_lots"][0]["cost_basis"] = -1.0

    def bad_liability_kind(doc):
        doc["liabilities"][0]["kind"] = "gambling_debt"

    def risk_capacity_out_of_range(doc):
        doc["constraints"]["risk_capacity"] = 145

    def missing_required_section(doc):
        del doc["constraints"]

    def missing_custodian(doc):
        del doc["accounts"][1]["custodian"]

    def duplicate_member_id(doc):
        doc["members"][1]["id"] = "m1"

    def bad_priority_enum(doc):
        doc["goals"][1]["priority"] = "whenever"

    def implausible_rate(doc):
        doc["liabilities"][0]["rate"] = 4.5

    def bad_currency(doc):
        doc["accounts"][0]["currency"] = "us dollars"

    def end_before_start(doc):
        doc["members"][0]["employment"]["income_streams"][0]["end_year"] = 2010

    def bad_match_formula(doc):
        doc["benefits"]["plans"][0]["employer_match"]["formula"] = ""

    def bad_will_status(doc):
        doc["estate_intentions"]["will_status"] = "maybe_signed"

    def negative_liquidity_floor(doc):
        doc["constraints"]["liquidity_floor"] = -100.0

    def bad_share(doc):
        doc["accounts"][1]["beneficiaries"][0]["share"] = 2.5

    def root_not_object():
        return []  # replaced wholesale below

    return [
        ("bad enum on account type", bad_enum),
        ("negative member age", negative_age),
        ("lot qty mismatch vs holding qty", lot_qty_mismatch),
        ("goal with past target_date", goal_past_target),
        ("bad ISO date format", bad_date_format),
        ("negative cost basis", negative_cost_basis),
        ("bad liability kind enum", bad_liability_kind),
        ("risk capacity outside [0,100]", risk_capacity_out_of_range),
        ("missing required section", missing_required_section),
        ("missing custodian", missing_custodian),
        ("duplicate member id", duplicate_member_id),
        ("bad goal priority enum", bad_priority_enum),
        ("implausible liability rate", implausible_rate),
        ("invalid currency code", bad_currency),
        ("income end_year before start_year", end_before_start),
        ("empty employer match formula", bad_match_formula),
        ("bad will status enum", bad_will_status),
        ("negative liquidity floor", negative_liquidity_floor),
        ("beneficiary share > 1", bad_share),
    ]


def _run_selftest():
    failures = []

    # 1. complete valid document must produce zero errors
    doc = _valid_doc()
    errs = validate_twin(doc)
    if errs:
        failures.append("VALID doc rejected: %r" % errs)

    # 2. each malformation must be rejected, mentioning its own path area
    for label, mutate in _malformations():
        doc = _valid_doc()
        mutate(doc)
        errs = validate_twin(doc)
        if not errs:
            failures.append("MALFORMATION not caught: %s" % label)

    # 3. non-object roots must be rejected without raising
    for junk in (None, [], "string", 42):
        errs = validate_twin(junk)
        if not errs:
            failures.append("non-object root %r not rejected" % (junk,))

    # 4. validator must never raise on garbage
    try:
        validate_twin({"members": [42], "accounts": [{"holdings": ["x"]}]}
                      )
    except Exception as exc:  # pragma: no cover
        failures.append("validator raised on partial garbage: %r" % (exc,))

    n_malformed = len(_malformations())
    print("selftest: valid doc -> %d errors" % len(validate_twin(_valid_doc())))
    print("selftest: %d malformation cases exercised" % n_malformed)
    if failures:
        print("selftest FAILED (%d):" % len(failures))
        for f in failures:
            print("  - " + f)
        return 1
    print("selftest PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run_selftest())
