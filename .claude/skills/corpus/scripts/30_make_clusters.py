"""
Stage 2b: Generate cluster definitions from the indexed corpus.

Produces JSON files in 30-index/clusters/ each defining a synthesis batch.

Cluster rules (run in order, all output to the same dir):
  1. By shared location / installation / facility (3+ docs)
  2. By shared person (3+ docs)
  3. By shared program / project / organization (3+ docs)
  4. By year of event (3+ incident reports)
  5. High-anomaly singletons (score >= 8) -- single-doc deep-dive cluster
  6. Anomaly-score bands (high/mid/low) for any docs not yet captured

  Note: this script is generic and operates on whatever entity/program/location
  fields the per-corpus extraction schema produces. The "shared program" cluster
  works for any domain (UAP: Blue Book/AATIP/UAPTF/AARO; legal: case docket;
  FDA: drug class/trial phase; congressional: committee/bill).

Usage:
  python 30_make_clusters.py --db ../30-index/corpus.db --output ../30-index/clusters
"""
from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("cluster")

MIN_CLUSTER_SIZE = 3
MAX_CLUSTER_SIZE = 40
HIGH_ANOMALY = 8


def safe_id(s: str, max_len: int = 60) -> str:
    out = "".join(c if c.isalnum() or c in "-_" else "_" for c in s.lower())
    return out[:max_len].strip("_")


def write_cluster(out_dir: Path, cluster_id: str, axis: str, rationale: str, doc_ids: list[str]) -> Path:
    if len(doc_ids) > MAX_CLUSTER_SIZE:
        log.warning(f"[truncate] {cluster_id}: {len(doc_ids)} -> {MAX_CLUSTER_SIZE}")
        doc_ids = doc_ids[:MAX_CLUSTER_SIZE]
    payload = {
        "cluster_id": cluster_id,
        "axis": axis,
        "rationale": rationale,
        "size": len(doc_ids),
        "doc_ids": doc_ids,
    }
    path = out_dir / f"{cluster_id}.json"
    path.write_text(json.dumps(payload, indent=2))
    return path


def cluster_by_identifier(conn: sqlite3.Connection, namespace: str, axis: str, out_dir: Path) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id_value, GROUP_CONCAT(doc_id, '|') AS docs, COUNT(*) AS n
        FROM identifiers
        WHERE id_namespace = ?
        GROUP BY id_value
        HAVING n >= ?
        ORDER BY n DESC
        """,
        (namespace, MIN_CLUSTER_SIZE),
    )
    n_clusters = 0
    for id_value, docs_csv, n in cur.fetchall():
        cluster_id = f"{axis}__{safe_id(id_value)}"
        rationale = f"Documents sharing {namespace} identifier '{id_value}' (n={n})"
        write_cluster(out_dir, cluster_id, axis, rationale, docs_csv.split("|"))
        n_clusters += 1
    log.info(f"[{axis}] {n_clusters} clusters")
    return n_clusters


def cluster_high_anomaly_singletons(conn: sqlite3.Connection, out_dir: Path) -> int:
    cur = conn.cursor()
    cur.execute("SELECT doc_id FROM documents WHERE anomaly_score >= ?", (HIGH_ANOMALY,))
    n = 0
    for (doc_id,) in cur.fetchall():
        cluster_id = f"high_anomaly__{safe_id(doc_id)}"
        rationale = f"Single-document deep dive: anomaly_score >= {HIGH_ANOMALY}"
        write_cluster(out_dir, cluster_id, "high_anomaly_singleton", rationale, [doc_id])
        n += 1
    log.info(f"[high_anomaly_singleton] {n} clusters")
    return n


def cluster_by_year(conn: sqlite3.Connection, out_dir: Path) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT substr(date_of_event,1,4) AS yr, GROUP_CONCAT(doc_id, '|'), COUNT(*)
        FROM documents
        WHERE is_incident = 1 AND date_of_event IS NOT NULL
        GROUP BY yr
        HAVING COUNT(*) >= ?
        """,
        (MIN_CLUSTER_SIZE,),
    )
    n = 0
    for yr, docs_csv, count in cur.fetchall():
        if not yr or len(yr) != 4:
            continue
        cluster_id = f"year__{yr}"
        rationale = f"All incident reports with date_of_event in {yr} (n={count})"
        write_cluster(out_dir, cluster_id, "year", rationale, docs_csv.split("|"))
        n += 1
    log.info(f"[year] {n} clusters")
    return n


def cluster_by_anomaly_band(conn: sqlite3.Connection, out_dir: Path) -> int:
    cur = conn.cursor()
    bands = [
        ("anomaly_high", "anomaly_score >= 7", "Anomaly score >= 7"),
        ("anomaly_mid", "anomaly_score BETWEEN 4 AND 6", "Anomaly score 4-6"),
        ("anomaly_low", "anomaly_score <= 3", "Anomaly score <= 3 (mundane / well-explained)"),
    ]
    n = 0
    for cid, where, rationale in bands:
        cur.execute(f"SELECT doc_id FROM documents WHERE {where}")
        docs = [row[0] for row in cur.fetchall()]
        if len(docs) >= MIN_CLUSTER_SIZE:
            for i in range(0, len(docs), MAX_CLUSTER_SIZE):
                batch = docs[i : i + MAX_CLUSTER_SIZE]
                cluster_id = f"{cid}__batch_{i // MAX_CLUSTER_SIZE:03d}"
                write_cluster(out_dir, cluster_id, cid, rationale, batch)
                n += 1
    log.info(f"[anomaly_band] {n} clusters")
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    db_path = Path(args.db)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Cluster definitions are derived; wipe and rebuild
    for f in out_dir.glob("*.json"):
        f.unlink()

    conn = sqlite3.connect(db_path)
    total = 0
    total += cluster_by_identifier(conn, "base", "by_base", out_dir)
    total += cluster_by_identifier(conn, "person", "by_person", out_dir)
    total += cluster_by_identifier(conn, "program", "by_program", out_dir)
    total += cluster_by_year(conn, out_dir)
    total += cluster_high_anomaly_singletons(conn, out_dir)
    total += cluster_by_anomaly_band(conn, out_dir)

    log.info(f"Total clusters: {total}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
