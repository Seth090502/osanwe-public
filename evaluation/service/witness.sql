-- Separate D1 database: append-only witness, NEVER restored with the case DB.
-- Triggers prevent ordinary accidental rewrites, not a malicious administrator.
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS custody (
  id TEXT PRIMARY KEY, generation TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS quotas (
  campaign_id TEXT PRIMARY KEY, epoch TEXT NOT NULL,
  max_attempts INTEGER NOT NULL CHECK(max_attempts > 0), plan_digest TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS batch_plans (
  batch_id TEXT PRIMARY KEY, campaign_id TEXT NOT NULL REFERENCES quotas(campaign_id),
  batch_index INTEGER NOT NULL CHECK(batch_index>0), plan_digest TEXT NOT NULL,
  UNIQUE(campaign_id,batch_index)
);
CREATE TABLE IF NOT EXISTS burns (
  id TEXT PRIMARY KEY, campaign_id TEXT NOT NULL REFERENCES quotas(campaign_id),
  epoch TEXT NOT NULL, batch_id TEXT NOT NULL, assignment_id TEXT NOT NULL UNIQUE,
  request_key TEXT NOT NULL, request_digest TEXT NOT NULL, created_at TEXT NOT NULL,
  UNIQUE(campaign_id, request_key)
);
CREATE TABLE IF NOT EXISTS events (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, attempt_id TEXT NOT NULL REFERENCES burns(id),
  kind TEXT NOT NULL CHECK(kind IN ('reserved','issued','submitted','scored','released','failed','abandoned')),
  payload_digest TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(attempt_id, kind)
);
CREATE TABLE IF NOT EXISTS batch_closures (
  batch_id TEXT PRIMARY KEY, plan_digest TEXT NOT NULL, closed_at TEXT NOT NULL,
  closure_digest TEXT NOT NULL, state_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS seals (
  batch_id TEXT NOT NULL REFERENCES batch_closures(batch_id), ordinal INTEGER NOT NULL,
  fragment_json TEXT NOT NULL, PRIMARY KEY(batch_id,ordinal)
);
DROP TRIGGER IF EXISTS event_guard;
CREATE TRIGGER event_guard BEFORE INSERT ON events BEGIN
  SELECT CASE WHEN NEW.kind!='released' AND EXISTS(
    SELECT 1 FROM batch_closures c JOIN burns b ON b.batch_id=c.batch_id WHERE b.id=NEW.attempt_id
  ) THEN RAISE(ABORT, 'batch_closed') END;
  SELECT CASE WHEN NOT COALESCE((
    (NEW.kind='reserved' AND NOT EXISTS(SELECT 1 FROM events WHERE attempt_id=NEW.attempt_id)) OR
    (NEW.kind='issued' AND (SELECT kind FROM events WHERE attempt_id=NEW.attempt_id ORDER BY seq DESC LIMIT 1)='reserved') OR
    (NEW.kind='submitted' AND (SELECT kind FROM events WHERE attempt_id=NEW.attempt_id ORDER BY seq DESC LIMIT 1)='issued') OR
    (NEW.kind='scored' AND (SELECT kind FROM events WHERE attempt_id=NEW.attempt_id ORDER BY seq DESC LIMIT 1)='submitted') OR
    (NEW.kind='released' AND (SELECT kind FROM events WHERE attempt_id=NEW.attempt_id ORDER BY seq DESC LIMIT 1)='scored') OR
    (NEW.kind IN ('failed','abandoned') AND (SELECT kind FROM events WHERE attempt_id=NEW.attempt_id ORDER BY seq DESC LIMIT 1) IN ('reserved','issued','submitted'))
  ),0) THEN RAISE(ABORT, 'invalid_transition') END;
END;
CREATE TRIGGER IF NOT EXISTS burns_no_update BEFORE UPDATE ON burns BEGIN SELECT RAISE(ABORT, 'immutable'); END;
CREATE TRIGGER IF NOT EXISTS burns_no_delete BEFORE DELETE ON burns BEGIN SELECT RAISE(ABORT, 'immutable'); END;
CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT, 'immutable'); END;
CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT, 'immutable'); END;
CREATE TRIGGER IF NOT EXISTS quotas_no_update BEFORE UPDATE ON quotas BEGIN SELECT RAISE(ABORT, 'immutable'); END;
CREATE TRIGGER IF NOT EXISTS quotas_no_delete BEFORE DELETE ON quotas BEGIN SELECT RAISE(ABORT, 'immutable'); END;
CREATE TRIGGER IF NOT EXISTS closures_no_update BEFORE UPDATE ON batch_closures BEGIN SELECT RAISE(ABORT, 'immutable'); END;
CREATE TRIGGER IF NOT EXISTS closures_no_delete BEFORE DELETE ON batch_closures BEGIN SELECT RAISE(ABORT, 'immutable'); END;
CREATE TRIGGER IF NOT EXISTS plans_no_update BEFORE UPDATE ON batch_plans BEGIN SELECT RAISE(ABORT, 'immutable'); END;
CREATE TRIGGER IF NOT EXISTS plans_no_delete BEFORE DELETE ON batch_plans BEGIN SELECT RAISE(ABORT, 'immutable'); END;
CREATE TRIGGER IF NOT EXISTS seals_no_update BEFORE UPDATE ON seals BEGIN SELECT RAISE(ABORT, 'immutable'); END;
CREATE TRIGGER IF NOT EXISTS seals_no_delete BEFORE DELETE ON seals BEGIN SELECT RAISE(ABORT, 'immutable'); END;
CREATE INDEX IF NOT EXISTS event_latest ON events(attempt_id, seq DESC);
CREATE INDEX IF NOT EXISTS campaign_burns ON burns(campaign_id);
CREATE INDEX IF NOT EXISTS batch_burns ON burns(batch_id);

-- Version 2 is additive. Legacy batches retain their original receipts and
-- analysis slots. Chunk indices are transport identities, not new alpha grants.
CREATE TABLE IF NOT EXISTS analysis_slots (
  campaign_id TEXT NOT NULL REFERENCES quotas(campaign_id), analysis_index INTEGER NOT NULL CHECK(analysis_index>0),
  owner_kind TEXT NOT NULL CHECK(owner_kind IN ('batch','cohort')), owner_id TEXT NOT NULL,
  PRIMARY KEY(campaign_id,analysis_index), UNIQUE(owner_kind,owner_id)
);
CREATE TABLE IF NOT EXISTS cohort_plans (
  id TEXT PRIMARY KEY, campaign_id TEXT NOT NULL REFERENCES quotas(campaign_id),
  analysis_index INTEGER NOT NULL CHECK(analysis_index>0), plan_digest TEXT NOT NULL,
  expected_batches INTEGER NOT NULL CHECK(expected_batches BETWEEN 1 AND 32),
  expected_count INTEGER NOT NULL CHECK(expected_count BETWEEN 3 AND 6912),
  required_families INTEGER NOT NULL CHECK(required_families BETWEEN 1 AND 2304),
  arms_json TEXT NOT NULL, resource_digest TEXT NOT NULL, dataset_digest TEXT NOT NULL,
  purpose TEXT NOT NULL CHECK(purpose IN ('development','confirmation')),
  UNIQUE(campaign_id,analysis_index)
);
CREATE TABLE IF NOT EXISTS cohort_members (
  cohort_id TEXT NOT NULL REFERENCES cohort_plans(id), batch_id TEXT NOT NULL UNIQUE REFERENCES batch_plans(batch_id),
  ordinal INTEGER NOT NULL, expected_count INTEGER NOT NULL, family_count INTEGER NOT NULL,
  snapshot_digest TEXT NOT NULL, PRIMARY KEY(cohort_id,ordinal)
);
CREATE TABLE IF NOT EXISTS cohort_freezes (
  cohort_id TEXT PRIMARY KEY REFERENCES cohort_plans(id), manifest_digest TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cohort_fragments (
  cohort_id TEXT NOT NULL REFERENCES cohort_freezes(cohort_id), ordinal INTEGER NOT NULL,
  fragment_json TEXT NOT NULL, PRIMARY KEY(cohort_id,ordinal)
);
CREATE TABLE IF NOT EXISTS cohort_closures (
  cohort_id TEXT PRIMARY KEY REFERENCES cohort_freezes(cohort_id), closure_digest TEXT NOT NULL,
  state_json TEXT NOT NULL, closed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cohort_releases (
  cohort_id TEXT PRIMARY KEY REFERENCES cohort_closures(cohort_id), receipt_json TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS cohort_member_guard BEFORE INSERT ON cohort_members BEGIN
  SELECT CASE WHEN EXISTS(SELECT 1 FROM cohort_freezes WHERE cohort_id=NEW.cohort_id)
    OR EXISTS(SELECT 1 FROM burns WHERE batch_id=NEW.batch_id)
    OR EXISTS(SELECT 1 FROM batch_closures WHERE batch_id=NEW.batch_id)
    THEN RAISE(ABORT,'cohort_membership_locked') END;
END;
CREATE TRIGGER IF NOT EXISTS cohort_freeze_guard BEFORE INSERT ON cohort_freezes BEGIN
  SELECT CASE WHEN (SELECT COUNT(*) FROM cohort_members WHERE cohort_id=NEW.cohort_id) !=
      (SELECT expected_batches FROM cohort_plans WHERE id=NEW.cohort_id)
    OR (SELECT SUM(expected_count) FROM cohort_members WHERE cohort_id=NEW.cohort_id) !=
      (SELECT expected_count FROM cohort_plans WHERE id=NEW.cohort_id)
    OR (SELECT SUM(family_count) FROM cohort_members WHERE cohort_id=NEW.cohort_id) !=
      (SELECT required_families FROM cohort_plans WHERE id=NEW.cohort_id)
    THEN RAISE(ABORT,'cohort_sample_incomplete') END;
END;
CREATE TRIGGER IF NOT EXISTS cohort_close_guard BEFORE INSERT ON cohort_closures BEGIN
  SELECT CASE WHEN (SELECT COUNT(*) FROM cohort_fragments WHERE cohort_id=NEW.cohort_id) !=
      (SELECT expected_batches FROM cohort_plans WHERE id=NEW.cohort_id)
    OR EXISTS(SELECT 1 FROM cohort_members m LEFT JOIN batch_closures c ON m.batch_id=c.batch_id
      WHERE m.cohort_id=NEW.cohort_id AND c.batch_id IS NULL)
    THEN RAISE(ABORT,'cohort_incomplete') END;
END;
CREATE TRIGGER IF NOT EXISTS analysis_slots_no_update BEFORE UPDATE ON analysis_slots BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER IF NOT EXISTS analysis_slots_no_delete BEFORE DELETE ON analysis_slots BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER IF NOT EXISTS cohort_plans_no_update BEFORE UPDATE ON cohort_plans BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER IF NOT EXISTS cohort_plans_no_delete BEFORE DELETE ON cohort_plans BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER IF NOT EXISTS cohort_members_no_update BEFORE UPDATE ON cohort_members BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER IF NOT EXISTS cohort_members_no_delete BEFORE DELETE ON cohort_members BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER IF NOT EXISTS cohort_freezes_no_update BEFORE UPDATE ON cohort_freezes BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER IF NOT EXISTS cohort_freezes_no_delete BEFORE DELETE ON cohort_freezes BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER IF NOT EXISTS cohort_fragments_no_update BEFORE UPDATE ON cohort_fragments BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER IF NOT EXISTS cohort_fragments_no_delete BEFORE DELETE ON cohort_fragments BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER IF NOT EXISTS cohort_closures_no_update BEFORE UPDATE ON cohort_closures BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER IF NOT EXISTS cohort_closures_no_delete BEFORE DELETE ON cohort_closures BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER IF NOT EXISTS cohort_releases_no_update BEFORE UPDATE ON cohort_releases BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER IF NOT EXISTS cohort_releases_no_delete BEFORE DELETE ON cohort_releases BEGIN SELECT RAISE(ABORT,'immutable'); END;
-- A forward migration allocates inherited standalone indices without rewriting
-- history. Reapplying it never turns existing cohort chunks into fresh analyses.
INSERT OR IGNORE INTO analysis_slots(campaign_id,analysis_index,owner_kind,owner_id)
  SELECT p.campaign_id,p.batch_index,'batch',p.batch_id FROM batch_plans p
  WHERE NOT EXISTS(SELECT 1 FROM cohort_members m WHERE m.batch_id=p.batch_id);

-- A projection of append-only burns avoids scanning the full campaign on every
-- reservation. Backfill once under RESTORE_LOCK; never rebuild it downward.
CREATE TABLE IF NOT EXISTS quota_usage (
  campaign_id TEXT PRIMARY KEY REFERENCES quotas(campaign_id), spent INTEGER NOT NULL CHECK(spent>=0)
);
INSERT OR IGNORE INTO quota_usage(campaign_id,spent)
  SELECT q.campaign_id,COUNT(b.id) FROM quotas q LEFT JOIN burns b ON b.campaign_id=q.campaign_id GROUP BY q.campaign_id;
CREATE TRIGGER IF NOT EXISTS quota_usage_initialize AFTER INSERT ON quotas BEGIN
  INSERT INTO quota_usage(campaign_id,spent) VALUES(NEW.campaign_id,0);
END;
CREATE TRIGGER IF NOT EXISTS quota_usage_no_decrease BEFORE UPDATE ON quota_usage BEGIN
  SELECT CASE WHEN NEW.campaign_id!=OLD.campaign_id OR NEW.spent!=OLD.spent+1 THEN RAISE(ABORT,'quota_counter_immutable') END;
END;
CREATE TRIGGER IF NOT EXISTS quota_usage_no_delete BEFORE DELETE ON quota_usage BEGIN SELECT RAISE(ABORT,'immutable'); END;
CREATE TRIGGER IF NOT EXISTS quota_usage_burn AFTER INSERT ON burns BEGIN
  UPDATE quota_usage SET spent=spent+1 WHERE campaign_id=NEW.campaign_id;
  SELECT CASE WHEN changes()!=1 THEN RAISE(ABORT,'quota_counter_unavailable') END;
END;
-- Replacing a trigger changes behavior, not historical rows or credits. The
-- counter update and reservation/event transaction commit or roll back together.
DROP TRIGGER IF EXISTS burn_guard;
CREATE TRIGGER burn_guard BEFORE INSERT ON burns BEGIN
  SELECT CASE WHEN NEW.epoch != (SELECT epoch FROM quotas WHERE campaign_id=NEW.campaign_id)
    THEN RAISE(ABORT,'epoch_mismatch') END;
  SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM quota_usage WHERE campaign_id=NEW.campaign_id)
    THEN RAISE(ABORT,'quota_counter_unavailable') END;
  SELECT CASE WHEN (SELECT spent FROM quota_usage WHERE campaign_id=NEW.campaign_id) >=
    (SELECT max_attempts FROM quotas WHERE campaign_id=NEW.campaign_id)
    THEN RAISE(ABORT,'quota_exhausted') END;
  SELECT CASE WHEN EXISTS(SELECT 1 FROM batch_closures WHERE batch_id=NEW.batch_id)
    THEN RAISE(ABORT,'batch_closed') END;
END;
