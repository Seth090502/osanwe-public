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
CREATE TRIGGER IF NOT EXISTS burn_guard BEFORE INSERT ON burns BEGIN
  SELECT CASE WHEN NEW.epoch != (SELECT epoch FROM quotas WHERE campaign_id=NEW.campaign_id)
    THEN RAISE(ABORT, 'epoch_mismatch') END;
  SELECT CASE WHEN (SELECT COUNT(*) FROM burns WHERE campaign_id=NEW.campaign_id) >=
    (SELECT max_attempts FROM quotas WHERE campaign_id=NEW.campaign_id)
    THEN RAISE(ABORT, 'quota_exhausted') END;
  SELECT CASE WHEN EXISTS(SELECT 1 FROM batch_closures WHERE batch_id=NEW.batch_id)
    THEN RAISE(ABORT, 'batch_closed') END;
END;
CREATE TRIGGER IF NOT EXISTS event_guard BEFORE INSERT ON events BEGIN
  SELECT CASE WHEN NEW.kind!='released' AND EXISTS(
    SELECT 1 FROM batch_closures c JOIN burns b ON b.batch_id=c.batch_id WHERE b.id=NEW.attempt_id
  ) THEN RAISE(ABORT, 'batch_closed') END;
  SELECT CASE WHEN NOT (
    (NEW.kind='reserved' AND NOT EXISTS(SELECT 1 FROM events WHERE attempt_id=NEW.attempt_id)) OR
    (NEW.kind='issued' AND (SELECT kind FROM events WHERE attempt_id=NEW.attempt_id ORDER BY seq DESC LIMIT 1)='reserved') OR
    (NEW.kind='submitted' AND (SELECT kind FROM events WHERE attempt_id=NEW.attempt_id ORDER BY seq DESC LIMIT 1)='issued') OR
    (NEW.kind='scored' AND (SELECT kind FROM events WHERE attempt_id=NEW.attempt_id ORDER BY seq DESC LIMIT 1)='submitted') OR
    (NEW.kind='released' AND (SELECT kind FROM events WHERE attempt_id=NEW.attempt_id ORDER BY seq DESC LIMIT 1)='scored') OR
    (NEW.kind IN ('failed','abandoned') AND (SELECT kind FROM events WHERE attempt_id=NEW.attempt_id ORDER BY seq DESC LIMIT 1) IN ('reserved','issued','submitted'))
  ) THEN RAISE(ABORT, 'invalid_transition') END;
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
