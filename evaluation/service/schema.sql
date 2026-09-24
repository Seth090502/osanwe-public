-- Cases and frozen plans. No public HTTP endpoint can populate these tables.
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS campaigns (
  id TEXT PRIMARY KEY, protocol_digest TEXT NOT NULL, dataset_digest TEXT NOT NULL,
  epoch TEXT NOT NULL, witness_id TEXT NOT NULL,
  evidence_class TEXT NOT NULL CHECK(evidence_class IN ('development','independent-admission')),
  custody_receipt_digest TEXT, status TEXT NOT NULL CHECK(status IN ('frozen','retired'))
);
CREATE TABLE IF NOT EXISTS batches (
  id TEXT PRIMARY KEY, campaign_id TEXT NOT NULL REFERENCES campaigns(id),
  plan_digest TEXT NOT NULL, expected_count INTEGER NOT NULL CHECK(expected_count BETWEEN 1 AND 216),
  batch_index INTEGER NOT NULL CHECK(batch_index > 0), closes_at TEXT NOT NULL,
  arms_json TEXT NOT NULL, resource_digest TEXT NOT NULL, dataset_digest TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cases (
  id TEXT PRIMARY KEY, family TEXT NOT NULL, scenario_family TEXT NOT NULL,
  source_family TEXT NOT NULL, version TEXT NOT NULL, case_digest TEXT NOT NULL,
  oracle_digest TEXT NOT NULL,
  privacy TEXT NOT NULL CHECK(privacy IN ('public','synthetic')),
  input_json TEXT NOT NULL, oracle_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS assignments (
  id TEXT PRIMARY KEY, batch_id TEXT NOT NULL REFERENCES batches(id),
  case_id TEXT NOT NULL REFERENCES cases(id), arm TEXT NOT NULL,
  candidate_digest TEXT NOT NULL, ordinal INTEGER NOT NULL,
  oracle_digest TEXT NOT NULL,
  UNIQUE(batch_id, case_id, arm), UNIQUE(batch_id, ordinal)
);
CREATE TABLE IF NOT EXISTS artifacts (
  attempt_id TEXT PRIMARY KEY, batch_id TEXT NOT NULL, submission_digest TEXT NOT NULL,
  submission_json TEXT NOT NULL, score_json TEXT, score_digest TEXT
);
CREATE INDEX IF NOT EXISTS artifact_batch ON artifacts(batch_id);
CREATE TABLE IF NOT EXISTS releases (
  batch_id TEXT PRIMARY KEY, receipt_json TEXT NOT NULL
);
