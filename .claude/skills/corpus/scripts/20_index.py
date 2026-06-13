"""
Stage 2: Build SQLite index from per-document extractions.

No LLM involved. Pure deterministic indexing for cross-document queries.

Usage:
  python 20_index.py --input ../20-extractions --db ../30-index/corpus.db
  python 20_index.py --db ../30-index/corpus.db --list-clusters
"""
from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("index")


SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY,
    doc_type TEXT,
    date_originated TEXT,
    date_of_event TEXT,
    location_named TEXT,
    location_country TEXT,
    is_incident INTEGER,
    anomaly_score INTEGER,
    redaction_density TEXT,
    summary TEXT,
    analyst_notes TEXT,
    json_path TEXT
);
CREATE INDEX IF NOT EXISTS idx_doc_anomaly ON documents(anomaly_score);
CREATE INDEX IF NOT EXISTS idx_doc_date ON documents(date_of_event);
CREATE INDEX IF NOT EXISTS idx_doc_location ON documents(location_named);

CREATE TABLE IF NOT EXISTS entities (
    doc_id TEXT,
    entity_type TEXT,
    entity_value TEXT,
    PRIMARY KEY (doc_id, entity_type, entity_value)
);
CREATE INDEX IF NOT EXISTS idx_ent_value ON entities(entity_value);
CREATE INDEX IF NOT EXISTS idx_ent_type_value ON entities(entity_type, entity_value);

CREATE TABLE IF NOT EXISTS identifiers (
    doc_id TEXT,
    identifier TEXT,
    id_namespace TEXT,
    id_value TEXT,
    PRIMARY KEY (doc_id, identifier)
);
CREATE INDEX IF NOT EXISTS idx_ident_value ON identifiers(id_namespace, id_value);

CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    doc_id UNINDEXED,
    summary,
    analyst_notes,
    content=''
);
"""


def upsert_document(conn: sqlite3.Connection, ext: dict, json_path: str) -> None:
    incident = ext.get("incident") or {}
    location = incident.get("location") or {}
    anomaly = ext.get("anomaly_score") or {}
    redactions = ext.get("redactions") or {}

    score = anomaly.get("score")
    try:
        score = int(score) if score is not None else None
    except (TypeError, ValueError):
        score = None

    # date_of_event can live at top level or nested in incident
    date_of_event = ext.get("date_of_event") or incident.get("date_of_event")

    conn.execute(
        """
        INSERT INTO documents
            (doc_id, doc_type, date_originated, date_of_event, location_named, location_country,
             is_incident, anomaly_score, redaction_density, summary, analyst_notes, json_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(doc_id) DO UPDATE SET
            doc_type=excluded.doc_type,
            date_originated=excluded.date_originated,
            date_of_event=excluded.date_of_event,
            location_named=excluded.location_named,
            location_country=excluded.location_country,
            is_incident=excluded.is_incident,
            anomaly_score=excluded.anomaly_score,
            redaction_density=excluded.redaction_density,
            summary=excluded.summary,
            analyst_notes=excluded.analyst_notes,
            json_path=excluded.json_path
        """,
        (
            ext.get("doc_id"),
            ext.get("doc_type"),
            ext.get("date_originated"),
            date_of_event,
            location.get("named"),
            location.get("country"),
            int(bool(incident.get("is_incident_report"))),
            score,
            redactions.get("redaction_density"),
            ext.get("summary"),
            ext.get("analyst_notes"),
            json_path,
        ),
    )

    # Replace entities and identifiers for this doc
    conn.execute("DELETE FROM entities WHERE doc_id = ?", (ext.get("doc_id"),))
    entities = ext.get("entities") or {}
    for etype, values in entities.items():
        if not isinstance(values, list):
            continue
        for v in values:
            if not v:
                continue
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO entities(doc_id, entity_type, entity_value) VALUES (?, ?, ?)",
                    (ext.get("doc_id"), etype, str(v).strip()),
                )
            except sqlite3.IntegrityError:
                pass

    conn.execute("DELETE FROM identifiers WHERE doc_id = ?", (ext.get("doc_id"),))
    hooks = ext.get("synthesis_hooks") or {}
    for ident in hooks.get("shared_identifiers_for_crosslink") or []:
        if not isinstance(ident, str) or ":" not in ident:
            continue
        ns, val = ident.split(":", 1)
        try:
            conn.execute(
                "INSERT OR IGNORE INTO identifiers(doc_id, identifier, id_namespace, id_value) VALUES (?, ?, ?, ?)",
                (ext.get("doc_id"), ident.strip(), ns.strip(), val.strip()),
            )
        except sqlite3.IntegrityError:
            pass

    conn.execute("DELETE FROM documents_fts WHERE doc_id = ?", (ext.get("doc_id"),))
    conn.execute(
        "INSERT INTO documents_fts(doc_id, summary, analyst_notes) VALUES (?, ?, ?)",
        (ext.get("doc_id"), ext.get("summary") or "", ext.get("analyst_notes") or ""),
    )


def build_index(input_dir: Path, db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)

    files = sorted(input_dir.glob("*.json"))
    if not files:
        log.warning(f"No extractions found in {input_dir}")
        return
    log.info(f"Indexing {len(files)} extractions into {db_path}")
    n_ok = 0
    for f in files:
        try:
            ext = json.loads(f.read_text(encoding="utf-8"))
            upsert_document(conn, ext, str(f))
            n_ok += 1
        except Exception as e:
            log.error(f"[fail] {f.name}: {e}")
    conn.commit()

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM documents")
    total = cur.fetchone()[0]
    cur.execute(
        "SELECT anomaly_score, COUNT(*) FROM documents WHERE anomaly_score IS NOT NULL "
        "GROUP BY anomaly_score ORDER BY anomaly_score"
    )
    dist = cur.fetchall()
    cur.execute("SELECT COUNT(DISTINCT id_value) FROM identifiers WHERE id_namespace='base'")
    n_bases = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT id_value) FROM identifiers WHERE id_namespace='person'")
    n_people = cur.fetchone()[0]

    log.info(f"Indexed {n_ok}/{len(files)} extractions.")
    log.info(f"Total documents in index: {total}")
    log.info(f"Anomaly score distribution: {dist}")
    log.info(f"Distinct bases: {n_bases}, distinct people: {n_people}")
    conn.close()


def list_clusters(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    print("\n=== High-population identifiers (potential cluster anchors) ===")
    cur.execute(
        """
        SELECT id_namespace, id_value, COUNT(*) AS n
        FROM identifiers
        GROUP BY id_namespace, id_value
        HAVING n >= 3
        ORDER BY n DESC
        LIMIT 50
        """
    )
    for ns, val, n in cur.fetchall():
        print(f"  [{ns:10s}] {val:50s}  ({n} docs)")

    print("\n=== Documents by year ===")
    cur.execute(
        """
        SELECT substr(date_of_event,1,4) AS yr, COUNT(*)
        FROM documents
        WHERE date_of_event IS NOT NULL
        GROUP BY yr
        ORDER BY yr
        """
    )
    for yr, n in cur.fetchall():
        print(f"  {yr}: {n}")

    print("\n=== Top anomaly cases (score >= 7) ===")
    cur.execute(
        """
        SELECT doc_id, anomaly_score, location_named, date_of_event, substr(summary,1,120)
        FROM documents
        WHERE anomaly_score >= 7
        ORDER BY anomaly_score DESC
        LIMIT 30
        """
    )
    for doc_id, score, loc, dt, summ in cur.fetchall():
        print(f"  [{score}] {doc_id} | {loc or '-'} | {dt or '-'} | {summ}...")

    conn.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="Directory of extraction JSONs")
    ap.add_argument("--db", required=True)
    ap.add_argument("--list-clusters", action="store_true")
    args = ap.parse_args()

    db_path = Path(args.db)

    if args.list_clusters:
        if not db_path.exists():
            log.error(f"DB not found: {db_path}")
            return 1
        list_clusters(db_path)
        return 0

    if not args.input:
        log.error("--input required when not using --list-clusters")
        return 1
    build_index(Path(args.input), db_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
