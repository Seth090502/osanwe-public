import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_protocol import module

native=module('native_pilot')


class NativePilotControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.document=self.root/'instruction.txt';self.document.write_text('Public synthetic instruction.')
        self.config=self.root/'config.json'
        self.config.write_text(json.dumps({'arms':{a:{'instructions':[str(self.document)],'library':[]} for a in native.ARMS},'timeout_seconds':240,'max_turns':12,'seed':41}))
        self.target=self.root/'pilot'

    def tearDown(self): self.temp.cleanup()

    def test_freeze_randomized_three_arms_and_never_drop_denominator(self):
        native.prepare(self.config,self.target)
        target,m=native.validate_plan(self.target)
        self.assertEqual(len(m['opportunities']),108)
        self.assertEqual(len({(o['case_id'],o['arm']) for o in m['opportunities']}),108)
        self.assertEqual(native.summarize(self.target)['status'],'batch_open_no_score_release')
        out=native.summarize(self.target,close_incomplete=True)
        self.assertEqual(out['denominator'],108)
        self.assertTrue(all(a['missing_or_failed']==36 for a in out['arms'].values()))
        with self.assertRaises(ValueError): native.run(self.target,limit=1)

    def test_editing_source_after_freeze_does_not_change_snapshot(self):
        native.prepare(self.config,self.target)
        self.document.write_text('Changed current instructions.')
        self.assertEqual(native.validate_plan(self.target)[1]['denominator'],108)

    def test_editing_frozen_bytes_is_detected(self):
        native.prepare(self.config,self.target)
        _,m=native.validate_plan(self.target)
        path=next(iter(m['assets']))
        (self.target/path).write_text('tampered')
        with self.assertRaises(ValueError):native.validate_plan(self.target)

    def test_failed_output_overhead_is_counted_and_runtime_remains_replayable(self):
        native.prepare(self.config,self.target);_,m=native.validate_plan(self.target)
        o=next(o for o in m['opportunities'] if o['arm']=='revised_library')
        directory=self.target/'attempts'/o['id'];directory.mkdir()
        (directory/'receipt.json').write_text(json.dumps({'status':'completed','answer':None,'library_reads':['library-00.txt','library-01.txt'],
            'read_files':['task.json','library-00.txt','library-01.txt'],'elapsed_seconds':19.5,'usage':{'claude-opus-5':{'outputTokens':101}}}))
        out=native.summarize(self.target,close_incomplete=True)['arms']['revised_library']
        self.assertEqual(out['missing_or_failed'],36);self.assertEqual(out['library_reads'],2)
        self.assertEqual(out['read_calls'],3);self.assertEqual(out['elapsed_seconds_total'],19.5)
        self.assertEqual(out['usage']['outputTokens'],101);self.assertEqual(out['observed_receipts'],1)
        self.assertEqual((self.target/'runtime/native_pilot.py').read_bytes(),Path(native.__file__).read_bytes())
        result=native.subprocess.run(['python',str(self.target/'runtime/native_pilot.py'),'summarize','--plan',str(self.target)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout);self.assertEqual(json.loads(result.stdout)['arms']['revised_library']['library_reads'],2)

    def test_source_contract_rejects_library_in_no_library_arm(self):
        c=json.loads(self.config.read_text());c['arms']['revised_no_library']['library']=[str(self.document)]
        self.config.write_text(json.dumps(c))
        with self.assertRaises(ValueError):native.prepare(self.config,self.target)

    def test_protected_source_is_never_read(self):
        with self.assertRaises(ValueError):native.safe_path(self.root/'private'/'source.json')

    def test_fresh_native_command_no_bare_and_provider_substitution_guard(self):
        native.prepare(self.config,self.target);_,m=native.validate_plan(self.target)
        with patch.object(native.subprocess,'Popen',side_effect=OSError('synthetic launch failure')) as launch:
            native.run_one(self.target,m,m['opportunities'][0])
        args=launch.call_args.args[0]
        self.assertIn('--restricted',args);self.assertIn('--no-session-persistence',args)
        self.assertNotIn('--bare',args);self.assertEqual(args[args.index('--model')+1],'claude-opus-5')
        self.assertEqual(args[args.index('--effort')+1],'xhigh')
        receipt=json.loads((self.target/'attempts'/m['opportunities'][0]['id']/'receipt.json').read_text())
        self.assertEqual(receipt['status'],'failed');self.assertFalse(receipt['provider_effort_attested'])
        child=self.target/'attempts'/m['opportunities'][0]['id']/'workspace'
        self.assertNotIn('oracle',json.loads((child/'task.json').read_text()))
        with self.assertRaises(FileExistsError):native.run_one(self.target,m,m['opportunities'][0])


if __name__=='__main__':unittest.main()
