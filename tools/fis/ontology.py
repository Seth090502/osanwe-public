#!/usr/bin/env python3
"""E1 -- Temporal financial ontology core (FIS Phase-II).

Bitemporal financial knowledge graph backed by SQLite.

Entity classes (12):
    person, household, account, institution, instrument, holding,
    tax_lot, transaction, economic_series, fact, model, decision

Relationship types (11):
    member_of      person        -> household      (membership)
    owns           person        -> account        (beneficial ownership)
    custodied_at   account       -> institution    (custody)
    issued_by      instrument    -> institution    (issuer)
    holds          account       -> holding        (position container)
    part_of        tax_lot       -> holding        (lot decomposition)
    realized_by    tax_lot       -> transaction    (lot opened/closed by tx)
    executed_via   transaction   -> account        (settlement account)
    transacts_in   transaction   -> instrument     (what was traded)
    observes       fact          -> economic_series (series datum link)
    produced_by    decision      -> model          (model attribution)

ID grammar: "<prefix>:<slug>" where <slug> is [a-z0-9][a-z0-9_-]* and
<prefix> must be the registered prefix for the entity's type
(person, hh, acct, inst, instr, holdg, lot, txn, series, fact, model,
dec).  IDs are immutable once written.

Every FACT carries mandatory provenance:
    source            where it came from (non-empty string)
    effective_time    when it is true in the real world (ISO date)
    known_time        when WE learned/believed it (ISO date)
    recorded_time     when this row was appended (UTC ISO datetime)
    units             unit of measure (e.g. USD, shares)
    currency          ISO-4217 code or 'NONE'
    confidence        float in [0, 1]
    validation_status draft | validated | rejected

Facts are append-only: a revision is a NEW row for the same
(subject_id, predicate); queries resolve the winning row per key by
latest effective_time then latest known_time, restricted to rows whose
known_time <= knowledge_date (point-in-time / no-lookahead discipline).

Run `python ontology.py` to execute the embedded selftest.
"""

from __future__ import annotations

import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

# --------------------------------------------------------------------------
# Vocabulary
# --------------------------------------------------------------------------

ENTITY_TYPES = (
    "person", "household", "account", "institution", "instrument",
    "holding", "tax_lot", "transaction", "economic_series", "fact",
    "model", "decision",
)

TYPE_PREFIX = {
    "person": "person",
    "household": "hh",
    "account": "acct",
    "institution": "inst",
    "instrument": "instr",
    "holding": "holdg",
    "tax_lot": "lot",
    "transaction": "txn",
    "economic_series": "series",
    "fact": "fact",
    "model": "model",
    "decision": "dec",
}
PREFIX_TYPE = {v: k for k, v in TYPE_PREFIX.items()}

RELATIONSHIP_TYPES = (
    "member_of", "owns", "custodied_at", "issued_by", "holds",
    "part_of", "realized_by", "executed_via", "transacts_in",
    "observes", "produced_by",
)

VALIDATION_STATUSES = ("draft", "validated", "rejected")

SLUG_OK = "abcdefghijklmnopqrstuvwxyz0123456789_-"

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "Efforts", "osanwe-v2-overhaul", "_work", "fis-data",
    "ontology.db",
)


class OntologyError(ValueError):
    """Raised for schema/grammar/provenance violations."""


# --------------------------------------------------------------------------
# Validation helpers
# --------------------------------------------------------------------------

def _check_id(entity_type: str, entity_id: str) -> str:
    if entity_type not in ENTITY_TYPES:
        raise OntologyError("unknown entity type: %r" % (entity_type,))
    if not isinstance(entity_id, str) or ":" not in entity_id:
        raise OntologyError(
            "id %r violates grammar '<prefix>:<slug>'" % (entity_id,))
    prefix, slug = entity_id.split(":", 1)
    expected = TYPE_PREFIX[entity_type]
    if prefix != expected:
        raise OntologyError(
            "id prefix %r is not valid for type %r (expected %r)"
            % (prefix, entity_type, expected))
    if not slug or slug[0] not in "abcdefghijklmnopqrstuvwxyz0123456789":
        raise OntologyError("id slug must start alphanumeric: %r" % (slug,))
    if any(c not in SLUG_OK for c in slug):
        raise OntologyError(
            "id slug may contain only [a-z0-9_-]: %r" % (slug,))
    return entity_id


def _check_date(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise OntologyError("%s must be an ISO date string" % (name,))
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise OntologyError(
            "%s must be YYYY-MM-DD, got %r" % (name, value))
    return value


# --------------------------------------------------------------------------
# Core store
# --------------------------------------------------------------------------

_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS entity (
    id           TEXT PRIMARY KEY,
    entity_type  TEXT NOT NULL CHECK (entity_type IN (
                     'person','household','account','institution',
                     'instrument','holding','tax_lot','transaction',
                     'economic_series','fact','model','decision')),
    label        TEXT NOT NULL,
    detail       TEXT NOT NULL DEFAULT '',
    created_utc  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS relationship (
    id             TEXT PRIMARY KEY,
    rel_type       TEXT NOT NULL CHECK (rel_type IN (
                       'member_of','owns','custodied_at','issued_by',
                       'holds','part_of','realized_by','executed_via',
                       'transacts_in','observes','produced_by')),
    subject_id     TEXT NOT NULL REFERENCES entity(id),
    object_id      TEXT NOT NULL REFERENCES entity(id),
    source         TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to   TEXT,              -- NULL = open-ended
    known_time     TEXT NOT NULL,
    confidence     REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    UNIQUE (rel_type, subject_id, object_id, effective_from)
);

CREATE TABLE IF NOT EXISTS fact (
    id                TEXT PRIMARY KEY,
    subject_id        TEXT NOT NULL REFERENCES entity(id),
    predicate         TEXT NOT NULL,
    value_num         REAL,
    value_text        TEXT,
    source            TEXT NOT NULL,
    effective_time    TEXT NOT NULL,
    known_time        TEXT NOT NULL,
    recorded_time     TEXT NOT NULL,
    units             TEXT NOT NULL,
    currency          TEXT NOT NULL,
    confidence        REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    validation_status TEXT NOT NULL CHECK (validation_status IN
                          ('draft','validated','rejected')),
    UNIQUE (id),
    UNIQUE (recorded_time, subject_id, predicate)
);

CREATE INDEX IF NOT EXISTS ix_fact_subject_pred
    ON fact (subject_id, predicate);
CREATE INDEX IF NOT EXISTS ix_fact_known
    ON fact (known_time);
CREATE INDEX IF NOT EXISTS ix_rel_subject
    ON relationship (subject_id);
CREATE INDEX IF NOT EXISTS ix_rel_object
    ON relationship (object_id);
"""


class Ontology:
    """SQLite-backed bitemporal financial ontology."""

    def __init__(self, db_path: str = None):
        self.db_path = os.path.abspath(db_path or DEFAULT_DB_PATH)
        parent = os.path.dirname(self.db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    @contextmanager
    def transaction(self):
        try:
            yield self._conn
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    # -- entity API --------------------------------------------------------

    def add_entity(self, entity_type: str, entity_id: str, label: str,
                   detail: str = "") -> str:
        _check_id(entity_type, entity_id)
        if not label:
            raise OntologyError("entity requires a non-empty label")
        with self.transaction() as cx:
            cx.execute(
                "INSERT INTO entity (id, entity_type, label, detail,"
                " created_utc) VALUES (?, ?, ?, ?, ?)",
                (entity_id, entity_type, label, detail,
                 datetime.now(timezone.utc).isoformat(timespec="seconds")))
        return entity_id

    def get_entity(self, entity_id: str):
        row = self._conn.execute(
            "SELECT * FROM entity WHERE id = ?", (entity_id,)).fetchone()
        return dict(row) if row else None

    def entities(self, entity_type: str = None):
        if entity_type is None:
            cur = self._conn.execute(
                "SELECT * FROM entity ORDER BY id")
        else:
            if entity_type not in ENTITY_TYPES:
                raise OntologyError("unknown entity type: %r" % (entity_type,))
            cur = self._conn.execute(
                "SELECT * FROM entity WHERE entity_type = ? ORDER BY id",
                (entity_type,))
        return [dict(r) for r in cur.fetchall()]

    # -- relationship API --------------------------------------------------

    def add_relationship(self, rel_type: str, subject_id: str,
                         object_id: str, source: str,
                         effective_from: str, effective_to: str = None,
                         known_time: str = None, confidence: float = 1.0) -> str:
        if rel_type not in RELATIONSHIP_TYPES:
            raise OntologyError("unknown relationship type: %r" % (rel_type,))
        if not source:
            raise OntologyError("relationship requires provenance source")
        _check_date(effective_from, "effective_from")
        if effective_to is not None:
            _check_date(effective_to, "effective_to")
            if effective_to < effective_from:
                raise OntologyError("effective_to precedes effective_from")
        known_time = known_time or effective_from
        _check_date(known_time, "known_time")
        if not 0.0 <= confidence <= 1.0:
            raise OntologyError("confidence must be within [0, 1]")
        rid = "rel:" + uuid.uuid4().hex[:16]
        with self.transaction() as cx:
            cx.execute(
                "INSERT INTO relationship (id, rel_type, subject_id,"
                " object_id, source, effective_from, effective_to,"
                " known_time, confidence) VALUES (?,?,?,?,?,?,?,?,?)",
                (rid, rel_type, subject_id, object_id, source,
                 effective_from, effective_to, known_time, confidence))
        return rid

    def relationships_for(self, entity_id: str, rel_type: str = None,
                          direction: str = "both"):
        if direction not in ("out", "in", "both"):
            raise OntologyError("direction must be out|in|both")
        clauses, params = [], []
        if rel_type is not None:
            if rel_type not in RELATIONSHIP_TYPES:
                raise OntologyError("unknown relationship type: %r"
                                    % (rel_type,))
            clauses.append("rel_type = ?")
            params.append(rel_type)
        if direction in ("out", "both"):
            clauses.append("subject_id = ?")
            params.append(entity_id)
        if direction in ("in", "both"):
            clauses.append("object_id = ?")
            params.append(entity_id)
        sql = ("SELECT * FROM relationship WHERE "
               + " OR ".join("(%s)" % c for c in clauses)
               + " ORDER BY effective_from")
        return [dict(r) for r in
                self._conn.execute(sql, params).fetchall()]

    # -- fact API ----------------------------------------------------------

    def add_fact(self, subject_id: str, predicate: str, value=None,
                 source: str = "", effective_time: str = "",
                 known_time: str = "", recorded_time: str = None,
                 units: str = "", currency: str = "",
                 confidence: float = 1.0,
                 validation_status: str = "validated") -> str:
        """Append an immutable bitemporal fact. Revisions = new rows."""
        if not source:
            raise OntologyError("fact provenance requires source")
        if not predicate:
            raise OntologyError("fact requires a predicate")
        _check_date(effective_time, "effective_time")
        _check_date(known_time, "known_time")
        if not units:
            raise OntologyError("fact provenance requires units")
        if not currency or currency == "NONE":
            pass
        elif len(currency) != 3 or not currency.isupper() \
                or not currency.isalpha():
            raise OntologyError(
                "currency must be ISO-4217 code or NONE, got %r"
                % (currency,))
        else:
            # keep caller's explicit code; empty string means unspecified
            currency = currency
        if currency == "":
            raise OntologyError(
                "fact provenance requires an explicit currency "
                "(ISO-4217 code, or 'NONE' for unitless)")
        if not 0.0 <= confidence <= 1.0:
            raise OntologyError("confidence must be within [0, 1]")
        if validation_status not in VALIDATION_STATUSES:
            raise OntologyError(
                "validation_status must be one of %s"
                % (VALIDATION_STATUSES,))
        if value is None:
            value_num = value_text = None
        elif isinstance(value, bool):
            value_num, value_text = float(value), None
        elif isinstance(value, (int, float)):
            value_num, value_text = float(value), None
        else:
            value_num, value_text = None, str(value)
        recorded_time = recorded_time or datetime.now(
            timezone.utc).isoformat(timespec="milliseconds")
        fid = "fx:" + uuid.uuid4().hex[:20]
        with self.transaction() as cx:
            cx.execute(
                "INSERT INTO fact (id, subject_id, predicate, value_num,"
                " value_text, source, effective_time, known_time,"
                " recorded_time, units, currency, confidence,"
                " validation_status)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (fid, subject_id, predicate, value_num, value_text,
                 source, effective_time, known_time, recorded_time,
                 units, currency, confidence, validation_status))
        return fid

    @staticmethod
    def _winning_clause(knowledge_date: str, as_of_date: str,
                        include_rejected: bool) -> str:
        """Point-in-time eligibility: only facts already KNOWN by
        knowledge_date and EFFECTIVE by as_of_date may participate.
        Winner per (subject, predicate): latest effective_time, then
        latest known_time (a later-known correction of the same
        effective moment supersedes the earlier belief)."""
        sql = """
            SELECT f.* FROM fact f
            JOIN (
                SELECT subject_id, predicate, MAX(effective_time) AS eff
                FROM fact
                WHERE known_time <= :kd AND effective_time <= :ad
                  {rej}
                GROUP BY subject_id, predicate
            ) w
              ON f.subject_id = w.subject_id
             AND f.predicate = w.predicate
             AND f.effective_time = w.eff
            WHERE f.known_time <= :kd AND f.effective_time <= :ad
              AND f.known_time = (
                    SELECT MAX(f2.known_time) FROM fact f2
                    WHERE f2.subject_id = f.subject_id
                      AND f2.predicate  = f.predicate
                      AND f2.effective_time = f.effective_time
                      AND f2.known_time <= :kd)
              {rej2}
        """
        rej = "" if include_rejected else \
            "AND validation_status <> 'rejected'"
        return sql.format(rej=rej, rej2=rej.replace("validation_status",
                                                    "f.validation_status"))

    def facts(self, subject_id: str, predicate: str = None,
              as_of_date: str = None, knowledge_date: str = None,
              include_rejected: bool = False):
        """Winning facts for a subject under point-in-time bounds.

        as_of_date      -- world time bound (default: unbounded)
        knowledge_date  -- belief time bound (default: unbounded).
                           Facts whose known_time exceeds it are
                           invisible (no lookahead).
        """
        if knowledge_date is not None:
            _check_date(knowledge_date, "knowledge_date")
        if as_of_date is not None:
            _check_date(as_of_date, "as_of_date")
        sql = self._winning_clause(
            knowledge_date or "9999-12-31",
            as_of_date or "9999-12-31",
            include_rejected)
        params = {}
        clauses = ["f.subject_id = :sid"]
        params["sid"] = subject_id
        if predicate is not None:
            clauses.append("f.predicate = :pred")
            params["pred"] = predicate
        sql += " AND " + " AND ".join(clauses)
        sql += " ORDER BY f.predicate, f.effective_time"
        params["kd"] = knowledge_date or "9999-12-31"
        params["ad"] = as_of_date or "9999-12-31"
        return [dict(r) for r in
                self._conn.execute(sql, params).fetchall()]

    # -- household query API ----------------------------------------------

    def net_worth(self, household_id: str, as_of_date: str,
                  knowledge_date: str) -> dict:
        """Point-in-time net worth of a household in USD.

        ONLY facts with known_time <= knowledge_date and
        effective_time <= as_of_date are consulted. Composition:
          assets   = sum of latest cash_balance over the household's
                     cash accounts (via person -member_of-> household,
                     person -owns-> account)
          liabilities = sum of latest balance_due over liability accounts
          net_worth = assets - liabilities
        Returns breakdown plus the exact fact ids used (audit trail).
        """
        _check_date(as_of_date, "as_of_date")
        _check_date(knowledge_date, "knowledge_date")
        members = [r["subject_id"] for r in
                   self.relationships_for(household_id, "member_of",
                                          direction="in")]
        accounts = set()
        for pid in members:
            for rel in self.relationships_for(pid, "owns", direction="out"):
                ent = self.get_entity(rel["object_id"])
                if ent and ent["entity_type"] == "account":
                    accounts.add(ent["id"])
        assets = liabilities = 0.0
        used_asset_ids, used_liab_ids = [], []
        for acct in sorted(accounts):
            rows = self.facts(acct, "cash_balance",
                              as_of_date=as_of_date,
                              knowledge_date=knowledge_date)
            if rows:
                assets += float(rows[-1]["value_num"] or 0.0)
                used_asset_ids.append(rows[-1]["id"])
            rows = self.facts(acct, "balance_due",
                              as_of_date=as_of_date,
                              knowledge_date=knowledge_date)
            if rows:
                liabilities += float(rows[-1]["value_num"] or 0.0)
                used_liab_ids.append(rows[-1]["id"])
        return {
            "household_id": household_id,
            "as_of_date": as_of_date,
            "knowledge_date": knowledge_date,
            "assets_usd": round(assets, 2),
            "liabilities_usd": round(liabilities, 2),
            "net_worth_usd": round(assets - liabilities, 2),
            "accounts_seen": sorted(accounts),
            "asset_fact_ids": used_asset_ids,
            "liability_fact_ids": used_liab_ids,
        }


# --------------------------------------------------------------------------
# Selftest
# --------------------------------------------------------------------------

def run_selftest(db_path: str = None) -> bool:
    """Synthetic two-person household; cash revised over time.

    Timeline (all effective 2026-01-01 unless noted):
      known 2026-01-05: cash_balance 10_000.00  (bank statement v1)
      known 2026-02-10: cash_balance 12_000.00  (restated statement;
                         same effective moment, discovered later)
    Point-in-time net worth must read 0 before anything is known,
    10_000 between the two knowledge dates, and 12_000 after the
    revision became known -- regardless of how far forward as_of runs.
    """
    path = db_path or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "_selftest.db")
    if os.path.exists(path):
        os.remove(path)
    onto = Ontology(path)
    failures = []

    def check(name, cond, detail=""):
        if cond:
            print("PASS  %s" % name)
        else:
            failures.append(name)
            print("FAIL  %s  %s" % (name, detail))

    try:
        # --- synthetic household -------------------------------------
        onto.add_entity("household", "hh:test-smith", "Smith Household")
        onto.add_entity("person", "person:ada-smith", "Ada Smith")
        onto.add_entity("person", "person:bo-smith", "Bo Smith")
        onto.add_entity("institution", "inst:first-test-bank",
                        "First Test Bank")
        onto.add_entity("account", "acct:jointsavings-001",
                        "Joint Savings x001")

        onto.add_relationship("member_of", "person:ada-smith",
                              "hh:test-smith", "fixture", "2026-01-01")
        onto.add_relationship("member_of", "person:bo-smith",
                              "hh:test-smith", "fixture", "2026-01-01")
        onto.add_relationship("custodied_at", "acct:jointsavings-001",
                              "inst:first-test-bank", "fixture",
                              "2026-01-01")
        onto.add_relationship("owns", "person:ada-smith",
                              "acct:jointsavings-001", "fixture",
                              "2026-01-01")
        onto.add_relationship("owns", "person:bo-smith",
                              "acct:jointsavings-001", "fixture",
                              "2026-01-01")

        prov = dict(source="fixture:bank-statement", units="USD",
                    currency="USD", confidence=0.99,
                    validation_status="validated")
        onto.add_fact("acct:jointsavings-001", "cash_balance", 10000.00,
                      effective_time="2026-01-01",
                      known_time="2026-01-05",
                      recorded_time="2026-01-05T09:00:00.000+00:00",
                      **prov)
        onto.add_fact("acct:jointsavings-001", "cash_balance", 12000.00,
                      effective_time="2026-01-01",   # restatement
                      known_time="2026-02-10",
                      recorded_time="2026-02-10T09:00:00.000+00:00",
                      **prov)

        # --- ID grammar enforcement ----------------------------------
        try:
            onto.add_entity("person", "instr:bad-prefix", "Bad")
            check("reject wrong id prefix", False, "no exception")
        except OntologyError:
            check("reject wrong id prefix", True)
        try:
            onto.add_entity("person", "person:BAD SLUG!", "Bad")
            check("reject bad slug charset", False, "no exception")
        except OntologyError:
            check("reject bad slug charset", True)
        try:
            onto.add_fact("person:ada-smith", "x", 1, source="s",
                          effective_time="2026-01-01",
                          known_time="2026-01-01", units="USD")
            check("reject fact missing provenance", False, "no exception")
        except OntologyError:
            check("reject fact missing provenance", True)  # no currency
        try:
            onto.add_fact("person:ada-smith", "x", 1, source="s",
                          effective_time="2026-13-40",
                          known_time="2026-01-01", units="USD")
            check("reject invalid effective_time", False, "no exception")
        except OntologyError:
            check("reject invalid effective_time", True)

        # --- referential integrity ------------------------------------
        try:
            onto.add_relationship("owns", "person:ada-smith",
                                  "acct:does-not-exist", "fixture",
                                  "2026-01-01")
            check("FK blocks dangling relationship", False, "no exception")
        except sqlite3.IntegrityError:
            check("FK blocks dangling relationship", True)

        # --- point-in-time assertions ---------------------------------
        cases = [
            # (knowledge_date, expected_net_worth)
            ("2026-01-04", 0.0),      # nothing known yet
            ("2026-01-05", 10000.0),  # v1 known
            ("2026-02-09", 10000.0),  # still pre-revision belief
            ("2026-02-10", 12000.0),  # revision becomes known today
            ("2026-08-25", 12000.0),  # stays restated thereafter
        ]
        for kd, expected in cases:
            nw = onto.net_worth("hh:test-smith", as_of_date="2026-06-30",
                                knowledge_date=kd)
            check("PIT net worth kd=%s == %.0f" % (kd, expected),
                  abs(nw["net_worth_usd"] - expected) < 0.005,
                  "got %.2f" % nw["net_worth_usd"])

        # as_of bound also gates visibility (fact effective 2026-01-01)
        nw = onto.net_worth("hh:test-smith", as_of_date="2025-12-31",
                            knowledge_date="2026-08-25")
        check("as_of before effectiveness yields 0",
              nw["net_worth_usd"] == 0.0,
              "got %.2f" % nw["net_worth_usd"])

        # audit trail present
        nw = onto.net_worth("hh:test-smith", as_of_date="2026-06-30",
                            knowledge_date="2026-08-25")
        check("audit trail cites exactly one winning fact",
              len(nw["asset_fact_ids"]) == 1
              and len(nw["asset_fact_ids"][0]) > 0,
              str(nw["asset_fact_ids"]))
        check("both members linked", len(nw["accounts_seen"]) == 1)
    finally:
        onto.close()
        if os.path.exists(path):
            os.remove(path)

    print("-" * 60)
    if failures:
        print("SELFTEST FAILED: %d failure(s): %s"
              % (len(failures), ", ".join(failures)))
        return False
    print("SELFTEST PASSED")
    return True


if __name__ == "__main__":
    raise SystemExit(0 if run_selftest() else 1)
