"""relay_schema -- mission / claim / distillate validation for the relay worker.

GATE-B: wiki/research/gates/gate-b-relay-worker-2026-08-16.md.
All validation is code; nothing here is advisory. Claims stay byte-compatible with
the /ingest 8-field tuple (entity, metric, value, date, grade, section, text, prov)
so distillates drop into claim-distributor with no adapter. `prov` is the DATA
SOURCE tier; the transcriber is recorded once, leg-level, as `extractor`
(local:<model>@<digest>, the lowest provenance tier).
"""
import json
import re

SCHEMA_VERSION = 1
SLUG_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
LEG_RE = re.compile(r"^[a-z0-9-]+:[A-Za-z0-9._-]+$")
GRADES = ("A", "B", "C", "D")

# Budgets a mission may LOWER, never raise (driver enforces min()).
BUDGET_KEYS = ("max_turns", "max_tool_calls", "max_fetches", "max_mcp_calls",
               "max_segments", "wall_clock_s", "max_output_tokens_total",
               "max_escalations_per_leg", "max_proposals_per_leg",
               "propose_edit_max_chars")

# ---------------------------------------------------------------- grounding
# ONE shared matcher for record-time grounding AND relay-verify (the no-drift
# rule: two matchers would disagree exactly when it matters). GATE-B
# gate-b-local-orchestration-program-2026-08-17, Fable-review F-2.
_NUM_RE = re.compile(r"-?\$?\d[\d,]*(?:\.\d+)?\s*(?:%|[kKmMbBtT]\b)?")
_SCALE = {"k": 1e3, "m": 1e6, "b": 1e9, "t": 1e12}


def _parse_num(s):
    """Parse a number token incl. $, thousands commas, %/K/M/B/T suffix.
    Returns float or None."""
    s = s.strip().lstrip("$").rstrip()
    scale = 1.0
    if s.endswith("%"):
        s = s[:-1].rstrip()
    elif s and s[-1].lower() in _SCALE:
        scale = _SCALE[s[-1].lower()]
        s = s[:-1].rstrip()
    s = s.replace(",", "")
    try:
        return float(s) * scale
    except ValueError:
        return None


def value_occurs(value, text):
    """Does `value` occur in `text`? Returns (found, offset, length).
    Pass 1: literal substring (comma-insensitive on the value side,
    case-insensitive). Pass 2: numeric equality with K/M/B/T scale
    equivalence and %-suffix tolerance (rel 1e-6). Derived/multi-span
    values deliberately do NOT match -- the worker records what is
    printed, or routes to narrative/open-item."""
    if not isinstance(value, str) or not value.strip() or not text:
        return False, -1, 0
    v = value.strip()
    low = text.lower()
    for cand in (v, v.replace(",", "")):
        idx = low.find(cand.lower())
        if idx >= 0:
            return True, idx, len(cand)
    target = _parse_num(v)
    if target is not None:
        for m in _NUM_RE.finditer(text):
            got = _parse_num(m.group(0))
            if got is None:
                continue
            if got == target or (target != 0 and
                                 abs(got - target) <= abs(target) * 1e-6):
                return True, m.start(), len(m.group(0))
    return False, -1, 0


def _err(path, msg):
    return "%s: %s" % (path, msg)


def validate_mission(m):
    """Return list of error strings (empty = valid)."""
    errs = []
    if not isinstance(m, dict):
        return ["mission: not an object"]
    obj = m.get("objective")
    if not isinstance(obj, str) or not obj.strip():
        errs.append(_err("objective", "required non-empty string"))
    for key, typ in (("questions", list), ("seed_urls", list),
                     ("allowed_mcp", list), ("must_not", list)):
        if key in m and not isinstance(m[key], typ):
            errs.append(_err(key, "must be a list"))
    if "budgets" in m:
        b = m["budgets"]
        if not isinstance(b, dict):
            errs.append(_err("budgets", "must be an object"))
        else:
            for k, v in b.items():
                if k not in BUDGET_KEYS:
                    errs.append(_err("budgets.%s" % k, "unknown budget key"))
                elif not isinstance(v, int) or v < 0:
                    # 0 is a legitimate LOWERING (e.g. max_fetches: 0 = no web
                    # egress for this leg); negatives are nonsense.
                    errs.append(_err("budgets.%s" % k, "must be a non-negative int"))
    if "deliverable" in m and m["deliverable"] not in ("claims", "tables", "both"):
        errs.append(_err("deliverable", "must be claims|tables|both"))
    if "plan_checkpoint" in m and not isinstance(m["plan_checkpoint"], bool):
        errs.append(_err("plan_checkpoint", "must be a bool"))
    return errs


def effective_budgets(mission, config_budgets):
    """Mission may only LOWER config budgets."""
    out = dict(config_budgets)
    for k, v in (mission.get("budgets") or {}).items():
        if k in out and isinstance(v, int):
            out[k] = min(out[k], v)
    return out


def validate_claim(c, known_source_refs):
    """Return list of error strings. `known_source_refs` = refs registered THIS
    SEGMENT -- a claim citing anything else is rejected at call time (the
    anti-fabrication gate; it is code, not instruction)."""
    errs = []
    if not isinstance(c, dict):
        return ["claim: not an object"]
    for req in ("entity", "metric", "value", "prov", "source_ref"):
        v = c.get(req)
        if not isinstance(v, str) or not v.strip():
            errs.append(_err(req, "required non-empty string"))
    if errs:
        return errs
    if c["source_ref"] not in known_source_refs:
        errs.append(_err("source_ref", "%r does not name a tool result from this "
                         "segment (known: %s)" % (
                             c["source_ref"], sorted(known_source_refs)[:12])))
    if "date" in c and c["date"] and not re.match(r"^\d{4}-\d{2}-\d{2}$", str(c["date"])):
        errs.append(_err("date", "ISO YYYY-MM-DD or omit"))
    if "grade" in c and c["grade"] and c["grade"] not in GRADES:
        errs.append(_err("grade", "one of %s or omit" % (GRADES,)))
    for k in c:
        # "extractor" is PER-CLAIM on purpose (2026-08-17). The leg-level
        # extractor in the distillate envelope is dropped the moment a claim is
        # copied into an analysis (the INGEST tuple carries prov and no
        # transcriber field), after which nothing downstream can tell a locally
        # transcribed figure from a frontier-fetched one -- and claim-distributor
        # adjudicates on grade alone. That is how a local-tier claim launders
        # into a vault-native prior and, one run later, into a rating input.
        if k not in ("entity", "metric", "value", "date", "grade", "section",
                     "text", "prov", "source_ref", "verify", "witness",
                     "injection_suspect", "conflict", "extractor"):
            errs.append(_err(k, "unknown claim field"))
    # ASCII gate on every string field (Pattern 22)
    for k, v in c.items():
        if isinstance(v, str) and any(ord(ch) > 127 for ch in v):
            errs.append(_err(k, "non-ASCII characters (Pattern 22): use -- for "
                             "dashes, straight quotes, -> for arrows"))
    return errs


def claim_key(c):
    """De-dup key across segments."""
    return (c.get("entity"), c.get("metric"), c.get("value"), c.get("date"))


def merge_claims(existing, new):
    """Append with de-dup; a conflicting VALUE for the same (entity, metric, date)
    is kept AND flagged -- the local model never adjudicates conflicts."""
    seen = {claim_key(c) for c in existing}
    by3 = {}
    for c in existing:
        by3.setdefault((c.get("entity"), c.get("metric"), c.get("date")), []).append(c)
    conflicts = []
    out = list(existing)
    for c in new:
        if claim_key(c) in seen:
            continue
        k3 = (c.get("entity"), c.get("metric"), c.get("date"))
        if k3 in by3:
            c = dict(c)
            c["conflict"] = True
            for prior in by3[k3]:
                prior["conflict"] = True
            conflicts.append(k3)
        out.append(c)
        seen.add(claim_key(c))
        by3.setdefault(k3, []).append(c)
    return out, conflicts


def assemble_distillate(run, leg, segment, extractor, mission_digest, claims,
                        sources, open_items, done_items, not_found, narrative,
                        accounting, flags, proposed_edits=None):
    """MACHINE-ASSEMBLED. The model only ever authors `narrative`.
    proposed_edits is OPTIONAL under schema v1 (absent for non-edit roles;
    additive, so on-disk distillates and pinned expectations are untouched)."""
    d = {
        "schema_version": SCHEMA_VERSION,
        "run": run, "leg": leg, "segment": segment,
        "extractor": extractor, "mission_digest": mission_digest,
        "claims": claims,
        "sources": sources,
        "open_items": open_items,
        "done_items": done_items,
        "not_found": not_found,
        "narrative": (narrative or "")[:1200],
        "accounting": accounting,
        "flags": flags,
    }
    if proposed_edits is not None:
        d["proposed_edits"] = proposed_edits
    return d


def validate_distillate(d):
    errs = []
    if not isinstance(d, dict):
        return ["distillate: not an object"]
    if d.get("schema_version") != SCHEMA_VERSION:
        errs.append("schema_version: expected %d" % SCHEMA_VERSION)
    for req in ("run", "leg", "segment", "extractor", "claims", "sources",
                "open_items", "done_items", "not_found", "accounting", "flags"):
        if req not in d:
            errs.append("%s: missing" % req)
    if errs:
        return errs
    refs = {s.get("ref") for s in d["sources"]}
    for i, c in enumerate(d["claims"]):
        for e in validate_claim(c, refs):
            errs.append("claims[%d].%s" % (i, e))
    for i, pe in enumerate(d.get("proposed_edits") or []):
        for req in ("id", "path", "before_sha256", "old", "new", "why"):
            v = pe.get(req)
            if not isinstance(v, str) or not v:
                errs.append("proposed_edits[%d].%s: required non-empty string"
                            % (i, req))
        sha = pe.get("before_sha256", "")
        if isinstance(sha, str) and not re.match(r"^[0-9a-f]{64}$", sha):
            errs.append("proposed_edits[%d].before_sha256: not 64-hex" % i)
        for k, v in pe.items():
            if isinstance(v, str) and any(ord(ch) > 127 for ch in v):
                errs.append("proposed_edits[%d].%s: non-ASCII" % (i, k))
    return errs


def dumps_ascii(obj):
    """ASCII-safe JSON (Pattern 22 for on-disk artifacts)."""
    return json.dumps(obj, indent=2, ensure_ascii=True, sort_keys=False)
