#!/usr/bin/env python3
"""Onboarding session document validator (synthetic-preview flow).

Mirrors twin_schema.validate_twin, but tolerates PARTIAL documents: a
stage-1-only onboarding document (context questions answered, financial
structure not yet collected) validates cleanly AT THE STAGE-1 LEVEL and
returns a section-completion map instead of failing on missing sections.

Document being validated is the ONBOARDING SESSION export produced by
fis-app/onboarding.html:

    {
      "doc_kind": "onboarding_session",
      "schema_version": "1.0",
      "as_of": "YYYY-MM-DD",
      "synthetic_preview": true,
      "consent": true,
      "onboarding": {
        "stage_completed": <int>,
        "context": {
          "adults": <int>, "children": <int>,
          "goals": [<goal>, ...],
          "horizon": <horizon>,
          "jurisdiction": <jurisdiction>,
          "risk_preference": <int 1..5>
        },
        "financial_structure": {
          "accounts": [{"type": <account_type>,
                        "balance_band": <band>}, ...],
          "income_band": <band>, "spending_band": <band>,
          "debt_present": <bool>, "debt_kinds": [<liability_kind>...],
          "insurance_present": <bool>,
          "retirement_accounts_present": <bool>
        }
      },
      ... plus, once stage 3 export completes, the full twin core:
      members / accounts / goals / constraints (+ liabilities, insurance)

NO real personal data appears anywhere. This module contains schema +
validator logic plus a selftest using fully synthetic fixtures only.
ASCII-only, stdlib-only, no network, no git. Run:

    python onboarding_validate.py             -> selftest
    python onboarding_validate.py <file.json> -> CLI PASS/FAIL report
"""

from __future__ import annotations

import datetime as _dt
import json as _json
import os as _os
import re as _re
import sys as _sys

# ---------------------------------------------------------------------------
# Allowed vocabularies (mirror twin_schema where applicable)
# ---------------------------------------------------------------------------

ACCOUNT_TYPES = (
    "taxable", "traditional_401k", "roth", "hsa",
    "529", "brokerage", "cash",
)

LIABILITY_KINDS = ("mortgage", "auto", "student", "cc")

INSURANCE_KINDS = ("life", "health", "disability", "ltc", "umbrella",
                   "property")

RISK_TOLERANCE_LEVELS = ("conservative", "moderately_conservative",
                         "moderate", "moderately_aggressive", "aggressive")

GOAL_TAGS = (
    "emergency_fund", "retirement", "education", "home_purchase",
    "debt_payoff", "travel", "career_transition", "legacy",
)

HORIZONS = ("short_1_3y", "medium_3_10y", "long_10y_plus")

JURISDICTIONS = (
    "US", "US-CA", "US-NY", "US-TX", "US-FL", "US-WA",
    "CA", "GB", "EU", "OTHER",
)

BALANCE_BANDS = ("none", "under_10k", "10k_50k", "50k_150k",
                 "150k_500k", "over_500k")

MONEY_BANDS = ("under_25k", "25k_50k", "50k_100k", "100k_200k", "200k_plus")

DATE_RE = _re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Midpoints used ONLY to synthesize placeholder numbers for the synthetic
# twin core. These are band approximations, never user-entered exact values.
_BALANCE_BAND_MID = {
    "under_10k": 5000.0,
    "10k_50k": 30000.0,
    "50k_150k": 100000.0,
    "150k_500k": 300000.0,
    "over_500k": 750000.0,
}
_MONEY_BAND_MID = {
    "under_25k": 18000.0,
    "25k_50k": 37500.0,
    "50k_100k": 75000.0,
    "100k_200k": 150000.0,
    "200k_plus": 275000.0,
}
_HORIZON_YEARS = {"short_1_3y": 2, "medium_3_10y": 7, "long_10y_plus": 20}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _err(path, msg):
    return "%s: %s" % (path if path else "<root>", msg)


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _check_enum(value, allowed, path, errors):
    if not isinstance(value, str) or value not in allowed:
        errors.append(_err(path, "must be one of %s" % ", ".join(allowed)))
        return False
    return True


def _check_bool(value, path, errors):
    if not isinstance(value, bool):
        errors.append(_err(path, "must be a boolean"))
        return False
    return True


def _parse_date(s):
    try:
        return _dt.date(int(s[0:4]), int(s[5:7]), int(s[8:10]))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Section validators
# ---------------------------------------------------------------------------

def _v_context(ctx, errors):
    """Validate onboarding.context. Returns count of fields present+valid."""
    path = "onboarding.context"
    if not isinstance(ctx, dict):
        errors.append(_err(path, "must be an object"))
        return 0
    good = 0

    adults = ctx.get("adults")
    if adults is None:
        errors.append(_err(path + ".adults", "required field is missing"))
    elif not _is_int(adults) or not (1 <= adults <= 8):
        errors.append(_err(path + ".adults", "must be an integer in [1, 8]"))
    else:
        good += 1

    children = ctx.get("children")
    if children is None:
        errors.append(_err(path + ".children", "required field is missing"))
    elif not _is_int(children) or not (0 <= children <= 12):
        errors.append(_err(path + ".children", "must be an integer in [0, 12]"))
    else:
        good += 1

    goals = ctx.get("goals")
    if goals is None:
        errors.append(_err(path + ".goals", "required field is missing"))
    elif not isinstance(goals, list) or not goals:
        errors.append(_err(path + ".goals", "must be a non-empty array"))
    elif not all(isinstance(g, str) and g in GOAL_TAGS for g in goals):
        bad = [g for g in goals
               if not (isinstance(g, str) and g in GOAL_TAGS)]
        errors.append(_err(
            path + ".goals",
            "unknown goal tag(s): %s; allowed: %s"
            % (", ".join(map(str, bad)), ", ".join(GOAL_TAGS))))
    elif len(set(goals)) != len(goals):
        errors.append(_err(path + ".goals", "duplicate goal tags"))
    else:
        good += 1

    if ctx.get("horizon") is None:
        errors.append(_err(path + ".horizon", "required field is missing"))
    elif _check_enum(ctx["horizon"], HORIZONS, path + ".horizon", errors):
        good += 1

    if ctx.get("jurisdiction") is None:
        errors.append(_err(path + ".jurisdiction",
                           "required field is missing"))
    elif _check_enum(ctx["jurisdiction"], JURISDICTIONS,
                     path + ".jurisdiction", errors):
        good += 1

    rp = ctx.get("risk_preference")
    if rp is None:
        errors.append(_err(path + ".risk_preference",
                           "required field is missing"))
    elif not _is_int(rp) or not (1 <= rp <= 5):
        errors.append(_err(path + ".risk_preference",
                           "must be an integer in [1, 5]"))
    else:
        good += 1
    return good


def _v_financial(fin, errors):
    """Validate onboarding.financial_structure.
    Returns (items-good count, total)."""
    path = "onboarding.financial_structure"
    if not isinstance(fin, dict):
        errors.append(_err(path, "must be an object"))
        return 0, 8
    good = 0
    total = 6

    accts = fin.get("accounts")
    if accts is None:
        errors.append(_err(path + ".accounts", "required field is missing"))
    elif not isinstance(accts, list) or not accts:
        errors.append(_err(path + ".accounts",
                           "must be a non-empty array of "
                           "{type, balance_band} entries"))
    else:
        acct_ok = True
        seen = set()
        for i, a in enumerate(accts):
            apath = "%s.accounts[%d]" % (path, i)
            if not isinstance(a, dict):
                errors.append(_err(apath, "must be an object"))
                acct_ok = False
                continue
            t = a.get("type")
            if t is None:
                errors.append(_err(apath + ".type",
                                   "required field is missing"))
                acct_ok = False
            elif not _check_enum(t, ACCOUNT_TYPES, apath + ".type", errors):
                acct_ok = False
            elif t in seen:
                errors.append(_err(apath + ".type",
                                   "duplicate account type '%s'" % t))
                acct_ok = False
            else:
                seen.add(t)
            bb = a.get("balance_band")
            if bb is None:
                errors.append(_err(apath + ".balance_band",
                                   "required field is missing "
                                   "(pick 'none' or an approximate range)"))
                acct_ok = False
            elif not _check_enum(bb, BALANCE_BANDS,
                                 apath + ".balance_band", errors):
                acct_ok = False
        if acct_ok:
            good += 1

    for key, allowed in (("income_band", MONEY_BANDS),
                         ("spending_band", MONEY_BANDS)):
        v = fin.get(key)
        if v is None:
            errors.append(_err(path + "." + key,
                               "required field is missing"))
        elif _check_enum(v, allowed, path + "." + key, errors):
            good += 1

    dp = fin.get("debt_present")
    if dp is None:
        errors.append(_err(path + ".debt_present",
                           "required field is missing"))
    elif _check_bool(dp, path + ".debt_present", errors):
        good += 1
        if dp:
            kinds = fin.get("debt_kinds")
            if not isinstance(kinds, list) or not kinds:
                errors.append(_err(path + ".debt_kinds",
                                   "must be a non-empty array when "
                                   "debt_present is true"))
            elif not all(isinstance(k, str) and k in LIABILITY_KINDS
                         for k in kinds):
                errors.append(_err(
                    path + ".debt_kinds",
                    "unknown kind(s); allowed: %s"
                    % ", ".join(LIABILITY_KINDS)))
            else:
                pass
    else:
        pass

    ip = fin.get("insurance_present")
    if ip is None:
        errors.append(_err(path + ".insurance_present",
                           "required field is missing"))
    elif _check_bool(ip, path + ".insurance_present", errors):
        good += 1

    rp = fin.get("retirement_accounts_present")
    if rp is None:
        errors.append(_err(path + ".retirement_accounts_present",
                           "required field is missing"))
    elif _check_bool(rp, path + ".retirement_accounts_present", errors):
        good += 1

    return good, total


# ---------------------------------------------------------------------------
# Twin-core validation (subset of twin_schema rules, mirrored here so the
# module stays dependency-free; the real twin_schema is used too when
# importable and all core sections are present).
# ---------------------------------------------------------------------------

_CORE_SECTIONS = ("schema_version", "as_of", "members", "accounts",
                  "goals", "constraints")


def _v_member(m, i, errors):
    path = "members[%d]" % i
    if not isinstance(m, dict):
        errors.append(_err(path, "must be an object"))
        return
    mid = m.get("id")
    if mid is None:
        errors.append(_err(path + ".id", "required field is missing"))
    elif not isinstance(mid, str) or not mid.strip():
        errors.append(_err(path + ".id", "must be a non-empty string"))
    age = m.get("age")
    if age is None:
        errors.append(_err(path + ".age", "required field is missing"))
    elif not _is_int(age) or age < 0 or age > 120:
        errors.append(_err(path + ".age",
                           "must be an integer in [0, 120]"))


def _v_account(a, i, errors, member_ids):
    path = "accounts[%d]" % i
    if not isinstance(a, dict):
        errors.append(_err(path, "must be an object"))
        return
    for key in ("id", "type", "custodian"):
        v = a.get(key)
        if v is None:
            errors.append(_err(path + "." + key,
                               "required field is missing"))
        elif key == "type":
            _check_enum(v, ACCOUNT_TYPES, path + ".type", errors)
        elif not isinstance(v, str) or not v.strip():
            errors.append(_err(path + "." + key,
                               "must be a non-empty string"))
    bal = a.get("balance")
    if bal is not None:
        if not _is_num(bal) or bal < 0:
            errors.append(_err(path + ".balance", "must be a number >= 0"))
    cur = a.get("currency")
    if cur is not None and (not isinstance(cur, str)
                            or not _re.match(r"^[A-Z]{3}$", cur)):
        errors.append(_err(path + ".currency",
                           "must be a 3-letter ISO-4217 code"))
    owners = a.get("owners")
    if owners is not None:
        if not isinstance(owners, list) or not owners:
            errors.append(_err(path + ".owners",
                               "must be a non-empty array of member ids"))
        else:
            for oi, o in enumerate(owners):
                if not isinstance(o, str) or not o.strip():
                    errors.append(_err("%s.owners[%d]" % (path, oi),
                                       "must be a non-empty string"))
                elif o not in member_ids:
                    errors.append(_err("%s.owners[%d]" % (path, oi),
                                       "references unknown member id '%s'"
                                       % o))
    holds = a.get("holdings")
    if holds is not None:
        if not isinstance(holds, list):
            errors.append(_err(path + ".holdings", "must be an array"))
        else:
            for hi, h in enumerate(holds):
                hpath = "%s.holdings[%d]" % (path, hi)
                if not isinstance(h, dict):
                    errors.append(_err(hpath, "must be an object"))
                    continue
                sym = h.get("symbol")
                if sym is None:
                    errors.append(_err(hpath + ".symbol",
                                       "required field is missing"))
                elif not isinstance(sym, str) or not sym.strip():
                    errors.append(_err(hpath + ".symbol",
                                       "must be a non-empty string"))
                q = h.get("qty")
                if q is None:
                    errors.append(_err(hpath + ".qty",
                                       "required field is missing"))
                elif not _is_num(q) or q <= 0:
                    errors.append(_err(hpath + ".qty", "must be a number > 0"))


def _v_goal(g, i, errors):
    path = "goals[%d]" % i
    if not isinstance(g, dict):
        errors.append(_err(path, "must be an object"))
        return
    gid = g.get("id")
    if gid is None:
        errors.append(_err(path + ".id", "required field is missing"))
    elif not isinstance(gid, str) or not gid.strip():
        errors.append(_err(path + ".id", "must be a non-empty string"))
    td = g.get("target_date")
    if td is None:
        errors.append(_err(path + ".target_date",
                           "required field is missing"))
    elif not isinstance(td, str) or not DATE_RE.match(td) \
            or _parse_date(td) is None:
        errors.append(_err(path + ".target_date",
                           "must be an ISO date 'YYYY-MM-DD'"))
    pr = g.get("priority")
    if pr is None:
        errors.append(_err(path + ".priority", "required field is missing"))
    elif pr not in ("essential", "high", "medium", "low"):
        errors.append(_err(path + ".priority",
                           "must be one of essential, high, medium, low"))
    ta = g.get("target_amount")
    if ta is not None and (not _is_num(ta) or ta < 0):
        errors.append(_err(path + ".target_amount",
                           "must be a number >= 0"))


def _v_constraints(c, errors):
    path = "constraints"
    if not isinstance(c, dict):
        errors.append(_err(path, "must be an object"))
        return
    rt = c.get("risk_tolerance")
    if rt is None:
        errors.append(_err(path + ".risk_tolerance",
                           "required field is missing"))
    else:
        if isinstance(rt, dict):
            lvl = rt.get("level")
            if lvl is None:
                errors.append(_err(path + ".risk_tolerance.level",
                                   "required field is missing"))
            else:
                _check_enum(lvl, RISK_TOLERANCE_LEVELS,
                            path + ".risk_tolerance.level", errors)
        else:
            _check_enum(rt, RISK_TOLERANCE_LEVELS,
                        path + ".risk_tolerance", errors)
    rc = c.get("risk_capacity")
    if rc is None:
        errors.append(_err(path + ".risk_capacity",
                           "required field is missing"))
    elif not _is_num(rc) or rc < 0 or rc > 100:
        errors.append(_err(path + ".risk_capacity",
                           "must be a number within [0, 100]"))
    lf = c.get("liquidity_floor")
    if lf is None:
        errors.append(_err(path + ".liquidity_floor",
                           "required field is missing"))
    elif not _is_num(lf) or lf < 0:
        errors.append(_err(path + ".liquidity_floor",
                           "must be a number >= 0"))


def _has_core(doc):
    return all(k in doc for k in _CORE_SECTIONS)


def _validate_twin_core(doc, errors):
    """Mirror-validate the twin core sections. Never raises."""
    sv = doc.get("schema_version")
    if sv is not None and (not isinstance(sv, str)
                           or not _re.match(r"^\d+\.\d+$", sv)):
        errors.append(_err("schema_version",
                           "must be a semver-like 'MAJOR.MINOR' string"))
    as_of = doc.get("as_of")
    if as_of is not None and (not isinstance(as_of, str)
                              or not DATE_RE.match(as_of)
                              or _parse_date(as_of) is None):
        errors.append(_err("as_of", "must be an ISO date 'YYYY-MM-DD'"))

    member_ids = set()
    members = doc.get("members")
    if isinstance(members, list):
        for i, m in enumerate(members):
            _v_member(m, i, errors)
            if isinstance(m, dict) and isinstance(m.get("id"), str):
                member_ids.add(m["id"])

    accounts = doc.get("accounts")
    if isinstance(accounts, list):
        for i, a in enumerate(accounts):
            _v_account(a, i, errors, member_ids)

    goals = doc.get("goals")
    if isinstance(goals, list):
        for i, g in enumerate(goals):
            _v_goal(g, i, errors)

    if "constraints" in doc:
        _v_constraints(doc["constraints"], errors)


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------

def validate_onboarding_doc(doc):
    """Validate an onboarding session document, tolerating partial docs.

    Returns a dict:
        ok                  bool  - True iff zero errors at the reached level
        level               str   - 'invalid' | 'stage1' | 'stage2' | 'stage3'
        errors              list[str] - precise dotted-path errors
        completion          dict  - section -> percent (0-100)
        overall_completion  float - weighted percent across sections

    A stage-1-only document (only doc_kind/schema_version/as_of/
    onboarding.context filled) yields ok=True, level='stage1'.
    """
    result = {
        "ok": False,
        "level": "invalid",
        "errors": [],
        "completion": {},
        "overall_completion": 0.0,
    }
    errors = result["errors"]

    if not isinstance(doc, dict):
        errors.append(_err("", "document must be an object"))
        result["completion"] = {"context": 0.0, "financial_structure": 0.0,
                                "twin_core": 0.0, "consent": 0.0}
        return result

    # --- envelope -----------------------------------------------------
    if doc.get("doc_kind") != "onboarding_session":
        errors.append(_err("doc_kind",
                           "must be 'onboarding_session' (got %r)"
                           % (doc.get("doc_kind"),)))
    sp = doc.get("synthetic_preview")
    if sp is not True:
        errors.append(_err("synthetic_preview",
                           "must be true: this flow exports a synthetic "
                           "preview document only"))

    ctx_good = 0
    fin_good, fin_total = 0, 8
    has_fin = isinstance(doc.get("onboarding"), dict) \
        and "financial_structure" in doc["onboarding"]

    onb = doc.get("onboarding")
    if onb is None:
        errors.append(_err("onboarding", "required section is missing"))
    elif not isinstance(onb, dict):
        errors.append(_err("onboarding", "must be an object"))
    else:
        if "context" not in onb:
            errors.append(_err("onboarding.context",
                               "required section is missing"))
        else:
            ctx_good = _v_context(onb["context"], errors)
        if "financial_structure" in onb:
            pair = _v_financial(onb["financial_structure"], errors)
            fin_good, fin_total = pair

    # --- twin core (only judged when present; stage tolerance) ---------
    core_errors_before = len(errors)
    if _has_core(doc):
        _validate_twin_core(doc, errors)
        if _importable_twin_schema():
            try:
                from twin_schema import validate_twin
                errors.extend(validate_twin(doc))
            except Exception:
                pass
    core_clean = _has_core(doc) and len(errors) == core_errors_before

    # --- consent -------------------------------------------------------
    consent = doc.get("consent")
    consent_pct = 100.0 if consent is True else 0.0
    if doc.get("consent") is False or (
            "consent" in doc and consent is not True):
        errors.append(_err("consent",
                           "must be true (explicit consent required "
                           "before export)"))

    # --- completion map -------------------------------------------------
    completion = {
        "context": round(100.0 * ctx_good / 6.0, 1),
        "financial_structure":
            round(100.0 * fin_good / float(fin_total), 1),
        "twin_core": round(100.0 * sum(
            1 for k in _CORE_SECTIONS
            if k in doc) / float(len(_CORE_SECTIONS)), 1),
        "consent": consent_pct,
    }
    overall = round(0.25 * completion["context"]
                    + 0.25 * completion["financial_structure"]
                    + 0.40 * completion["twin_core"]
                    + 0.10 * completion["consent"], 1)
    result["completion"] = completion
    result["overall_completion"] = overall

    # --- level ----------------------------------------------------------
    context_ok = completion["context"] >= 100.0 \
        and not any(e.startswith("onboarding.context") for e in errors)
    fin_ok = has_fin and completion["financial_structure"] >= 100.0 \
        and not any(e.startswith("onboarding.financial_structure")
                    for e in errors)

    if core_clean and consent is True and context_ok and fin_ok:
        result["level"] = "stage3"
        result["ok"] = not errors
    elif fin_ok and context_ok:
        result["level"] = "stage2"
        result["ok"] = not errors
    elif context_ok:
        result["level"] = "stage1"
        result["ok"] = not errors
    else:
        result["level"] = "invalid"
        result["ok"] = False
    return result


def _importable_twin_schema():
    here = _os.path.dirname(_os.path.abspath(__file__))
    return _os.path.isfile(_os.path.join(here, "twin_schema.py"))


# ---------------------------------------------------------------------------
# Synthetic projection: session doc -> full twin-valid document
# (reference implementation of what onboarding.html assembles)
# ---------------------------------------------------------------------------

def project_full_session_doc(context, financial, as_of=None, consent=True):
    """Build a COMPLETE synthetic onboarding session document whose twin
    core passes twin_schema.validate_twin with zero errors. Inputs are the
    validated onboarding.context / onboarding.financial_structure dicts."""
    as_of = as_of or _dt.date.today().isoformat()
    ctx, fin = context, financial
    adults = ctx["adults"]
    children = ctx.get("children", 0)
    pref = ctx["risk_preference"]
    horizon_years = _HORIZON_YEARS[ctx["horizon"]]
    income_mid = _MONEY_BAND_MID[fin["income_band"]]
    spend_mid = _MONEY_BAND_MID[fin["spending_band"]]
    year = _dt.date.today().year + horizon_years

    letters = "ABCDEFGH"
    members = []
    owner_ids = []
    for ai in range(adults):
        mid = "m%d" % (ai + 1)
        owner_ids.append(mid)
        members.append({"id": mid,
                        "name": "SYNTHETIC-MEMBER-%s" % letters[ai],
                        "age": 45 - 3 * ai})
    for ci in range(children):
        members.append({"id": "mc%d" % (ci + 1),
                        "name": "SYNTHETIC-CHILD-%d" % (ci + 1),
                        "age": 8 + ci})

    accounts = []
    for i, spec in enumerate(fin["accounts"]):
        acct = {"id": "synth-%s-%d" % (spec["type"], i + 1),
                "type": spec["type"],
                "custodian": "SYNTHETIC-CUSTODIAN",
                "currency": "USD",
                "owners": [owner_ids[0]]}
        band_mid = _BALANCE_BAND_MID[spec["balance_band"]]
        if band_mid > 0:
            acct["balance"] = float(band_mid)
            acct["holdings"] = [{"symbol": "CASH-SYNTH-%d" % (i + 1),
                                 "qty": float(band_mid)}]
        else:
            acct["balance"] = 0.0
        accounts.append(acct)

    goal_amounts = {
        "emergency_fund": 3.0 * spend_mid,
        "retirement": 12.0 * income_mid,
        "home_purchase": 4.0 * income_mid,
        "education": 200000.0,
        "debt_payoff": 50000.0,
        "travel": 25000.0,
        "career_transition": 60000.0,
        "legacy": 250000.0,
    }
    priorities = ["essential", "high", "medium", "low"]
    goals = []
    for gi, tag in enumerate(ctx["goals"]):
        goals.append({
            "id": "g-%s" % tag,
            "target_date": "%d-06-30" % year,
            "target_amount": goal_amounts.get(tag, 50000.0),
            "priority": priorities[min(gi, len(priorities) - 1)],
        })

    liabilities = []
    synth_liab = {
        "mortgage": {"rate": 0.0375, "term_months": 360,
                     "balance": 320000.0, "min_payment": 1500.0},
        "auto": {"rate": 0.0549, "term_months": 60,
                 "balance": 18000.0, "min_payment": 420.0},
        "student": {"rate": 0.045, "term_months": 120,
                    "balance": 35000.0, "min_payment": 380.0},
        "cc": {"rate": 0.189, "term_months": 36,
               "balance": 8000.0, "min_payment": 200.0},
    }
    if fin.get("debt_present"):
        for k in fin.get("debt_kinds", []):
            entry = {"kind": k}
            entry.update(synth_liab[k])
            liabilities.append(entry)

    insurance = []
    if fin.get("insurance_present"):
        insurance.append({"kind": "health",
                          "coverage_amount": 5000000.0,
                          "premium": 400.0,
                          "premium_freq": "monthly",
                          "insured_ids": [owner_ids[0]]})

    doc = {
        "doc_kind": "onboarding_session",
        "schema_version": "1.0",
        "as_of": as_of,
        "synthetic_preview": True,
        "consent": bool(consent),
        "onboarding": {
            "stage_completed": 3,
            "context": dict(ctx),
            "financial_structure": dict(fin),
        },
        "household_name": "SYNTHETIC-HOUSEHOLD-ONBOARDING-%d" % year,
        "members": members,
        "accounts": accounts,
        "goals": goals,
        "constraints": {
            "risk_tolerance": {
                "level": RISK_TOLERANCE_LEVELS[pref - 1],
                "score": pref * 20,
            },
            "risk_capacity": pref * 20,
            "liquidity_floor": 3.0 * spend_mid,
        },
    }
    if liabilities:
        doc["liabilities"] = liabilities
    if insurance:
        doc["insurance"] = insurance
    return doc


# ---------------------------------------------------------------------------
# Selftest
# ---------------------------------------------------------------------------

def _minimal_stage1_doc():
    return {
        "doc_kind": "onboarding_session",
        "schema_version": "1.0",
        "as_of": "2026-08-26",
        "synthetic_preview": True,
        "onboarding": {
            "stage_completed": 1,
            "context": {
                "adults": 2,
                "children": 1,
                "goals": ["retirement", "education"],
                "horizon": "long_10y_plus",
                "jurisdiction": "US-CA",
                "risk_preference": 3,
            },
        },
    }


def _stage2_financial():
    return {
        "accounts": [
            {"type": "taxable", "balance_band": "50k_150k"},
            {"type": "traditional_401k", "balance_band": "150k_500k"},
        ],
        "income_band": "100k_200k",
        "spending_band": "50k_100k",
        "debt_present": True,
        "debt_kinds": ["mortgage"],
        "insurance_present": True,
        "retirement_accounts_present": True,
    }


def _run_selftest():
    failures = []

    # 1. minimal stage-1-only doc validates cleanly at the stage-1 level
    r = validate_onboarding_doc(_minimal_stage1_doc())
    if not r["ok"]:
        failures.append("minimal stage-1 doc not ok: %r" % (r["errors"],))
    if r["level"] != "stage1":
        failures.append("expected level stage1, got %r" % r["level"])
    if r["completion"]["context"] != 100.0:
        failures.append("stage-1 context completion != 100: %r"
                        % (r["completion"],))
    if r["completion"]["twin_core"] >= 100.0:
        failures.append("stage-1 doc should not claim full twin core")

    # 2. full projected doc passes BOTH validate_onboarding_doc (stage3)
    #    and the real twin_schema.validate_twin completely
    full = project_full_session_doc(
        _minimal_stage1_doc()["onboarding"]["context"],
        _stage2_financial())
    r = validate_onboarding_doc(full)
    if not r["ok"] or r["level"] != "stage3":
        failures.append("full doc failed onboarding validation "
                        "(level=%s): %r" % (r["level"], r["errors"]))
    try:
        from twin_schema import validate_twin
    except ImportError:
        failures.append("could not import twin_schema for cross-check")
    else:
        twin_errs = validate_twin(full)
        if twin_errs:
            failures.append("full doc rejected by validate_twin: %r"
                            % (twin_errs,))

    # 3. garbage rejected WITH paths, never raising
    for junk in (None, [], "string", 42, {"foo": 1},
                 {"doc_kind": 7, "onboarding": "nope",
                  "members": [42], "accounts": [{"holdings": ["x"]}]}):
        try:
            r = validate_onboarding_doc(junk)
        except Exception as exc:
            failures.append("raised on garbage %r: %r" % (junk, exc))
            continue
        if r["ok"]:
            failures.append("garbage accepted: %r" % (junk,))
        if junk is not None and not r["errors"]:
            failures.append("garbage produced no paths: %r" % (junk,))

    # 4. targeted malformations must be caught with their own paths
    def mutate_and_check(label, mutate, expected_path_fragment):
        base = project_full_session_doc(
            _minimal_stage1_doc()["onboarding"]["context"],
            _stage2_financial())
        mutate(base)
        r = validate_onboarding_doc(base)
        hit = [e for e in r["errors"]
               if expected_path_fragment in e]
        if not hit:
            failures.append("malformation not caught at %s: %s -> %r"
                            % (expected_path_fragment, label, r["errors"]))
        if r["ok"]:
            failures.append("malformed doc reported ok: %s" % label)

    mutate_and_check("bad account type", lambda d:
                     d["onboarding"]["financial_structure"]["accounts"][0]
                     .__setitem__("type", "offshore_gold_vault"),
                     "financial_structure.accounts[0].type")
    mutate_and_check("bad risk preference", lambda d:
                     d["onboarding"]["context"].__setitem__(
                         "risk_preference", 9),
                     "onboarding.context.risk_preference")
    mutate_and_check("bad balance band", lambda d:
                     d["onboarding"]["financial_structure"]["accounts"][0]
                     .__setitem__("balance_band", "exactly_12345"),
                     "financial_structure.accounts[0].balance_band")
    mutate_and_check("debt kinds missing", lambda d:
                     d["onboarding"]["financial_structure"]
                     .__setitem__("debt_kinds", []),
                     "financial_structure.debt_kinds")
    mutate_and_check("constraint capacity out of range", lambda d:
                     d["constraints"].__setitem__("risk_capacity", 145),
                     "constraints.risk_capacity")
    mutate_and_check("negative holding qty", lambda d:
                     d["accounts"][0]["holdings"][0].__setitem__("qty", -5),
                     "accounts[0].holdings[0].qty")
    mutate_and_check("owner references unknown member", lambda d:
                     d["accounts"][0]["owners"].append("ghost"),
                     "accounts[0].owners[1]")
    mutate_and_check("consent false", lambda d:
                     d.__setitem__("consent", False), "consent")
    mutate_and_check("bad goal priority", lambda d:
                     d["goals"][0].__setitem__("priority", "whenever"),
                     "goals[0].priority")
    mutate_and_check("bad horizon", lambda d:
                     d["onboarding"]["context"].__setitem__(
                         "horizon", "whenever_later"),
                     "onboarding.context.horizon")

    n = 10
    print("selftest: %d scenario groups exercised (%d malformations)" %
          (4, n))
    if failures:
        print("selftest FAILED (%d):" % len(failures))
        for f in failures:
            print("  - " + f)
        return 1
    print("selftest PASSED")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main(argv):
    if "--selftest" in argv or len(argv) < 2:
        return _run_selftest()
    path = argv[-1]
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = _json.load(fh)
    except Exception as exc:
        print("FAIL cannot read %s: %s" % (path, exc))
        return 2
    r = validate_onboarding_doc(doc)
    print("document : %s" % path)
    print("verdict  : %s (level=%s)" % ("PASS" if r["ok"] else "FAIL",
                                        r["level"]))
    print("overall completion: %.1f%%" % r["overall_completion"])
    for section in sorted(r["completion"]):
        print("  %-22s %5.1f%%" % (section, r["completion"][section]))
    if r["errors"]:
        print("errors (%d):" % len(r["errors"]))
        for e in r["errors"]:
            print("  - " + e)
    else:
        print("errors: none")
    if r["level"] == "stage3" and r["ok"]:
        print("note: synthetic-preview document is export-complete.")
    elif not r["ok"]:
        print("note: fix errors above; partial docs validate at their "
              "reached stage level.")
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(_main(_sys.argv))
