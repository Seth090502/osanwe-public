import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest
import zipfile
from test_protocol import ROOT,module

packager=module('package_service')


class DeploymentControls(unittest.TestCase):
    def test_actual_v1_witness_migrates_without_rewriting_or_refunding_history(self):
        witness=sqlite3.connect(':memory:')
        witness.executescript((ROOT/'tests/fixtures/witness-v1.sql').read_text())
        witness.execute("INSERT INTO quotas VALUES('campaign','epoch',2,'protocol')")
        witness.execute("INSERT INTO batch_plans VALUES('batch','campaign',1,'plan')")
        witness.execute("INSERT INTO burns VALUES('previous','campaign','epoch','batch','assignment','request','hash','then')")
        witness.execute("INSERT INTO events(attempt_id,kind,payload_digest,created_at) VALUES('previous','reserved','hash','then')")
        original=witness.execute('SELECT * FROM burns').fetchall();events=witness.execute('SELECT * FROM events').fetchall()
        witness.executescript((ROOT/'service/witness.sql').read_text())
        self.assertEqual(witness.execute('SELECT * FROM burns').fetchall(),original)
        self.assertEqual(witness.execute('SELECT * FROM events').fetchall(),events)
        self.assertEqual(witness.execute('SELECT spent FROM quota_usage').fetchone()[0],1)
        self.assertEqual(witness.execute('SELECT owner_kind,owner_id FROM analysis_slots').fetchone(),('batch','batch'))
        with self.assertRaises(sqlite3.DatabaseError):witness.execute('UPDATE quota_usage SET spent=0')
        witness.rollback()
        with self.assertRaises(sqlite3.DatabaseError):
            with witness:
                witness.execute("INSERT INTO burns VALUES('new','campaign','epoch','batch','new-assignment','new-request','hash','now')")
                witness.execute("INSERT INTO events(attempt_id,kind,payload_digest,created_at) VALUES('new','scored','hash','now')")
        self.assertEqual(witness.execute('SELECT spent FROM quota_usage').fetchone()[0],1)
        self.assertEqual(witness.execute('SELECT * FROM burns').fetchall(),original)
        witness.close()

    def test_generated_load_and_forward_schema_keep_existing_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'load'
            r=subprocess.run(['node',str(ROOT/'prepare_deployment.mjs'),str(output)],capture_output=True,text=True,check=True)
            self.assertFalse(json.loads(r.stdout)['production_eligible'])
            db=sqlite3.connect(':memory:');witness=sqlite3.connect(':memory:')
            db.executescript((output/'case-database.sql').read_text())
            witness.executescript((output/'witness-database.sql').read_text())
            self.assertEqual(db.execute('SELECT COUNT(*) FROM assignments').fetchone()[0],108)
            witness.execute("INSERT INTO burns VALUES('attempt','osanwe-reasoning-development-v1',(SELECT epoch FROM quotas),'development-batch-1','assigned','request','hash','now')")
            witness.execute("INSERT INTO events(attempt_id,kind,payload_digest,created_at) VALUES('attempt','reserved','hash','now')")
            # Forward CREATE IF NOT EXISTS migration retains credits/events.
            witness.executescript((ROOT/'service/witness.sql').read_text())
            self.assertEqual(witness.execute('SELECT COUNT(*) FROM burns').fetchone()[0],1)
            with self.assertRaises(sqlite3.DatabaseError):witness.execute('DELETE FROM events')
            db.close();witness.close()

    def test_package_excludes_runtime_private_and_hidden_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'service.zip';result=packager.package(output)
            self.assertEqual(result['status'],'packaged-and-hash-verified')
            with zipfile.ZipFile(output) as z:
                self.assertNotIn('evaluation/evaluation_log.jsonl',z.namelist())
                self.assertFalse(any('/holdout/' in name or 'receipt.json' in name or '.env' in name for name in z.namelist()))
                self.assertIn('evaluation/service/worker.mjs',z.namelist())
            with self.assertRaises(ValueError):packager.package(output)


if __name__=='__main__':unittest.main()
