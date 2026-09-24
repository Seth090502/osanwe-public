"""Public/synthetic adapter controls; no account, corpus or embedding access."""
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SERVER = load('retrieval_server_control', Path('/path/to/local/vault-search/server.py'))
HOOK = load('retrieval_hook_control', ROOT / '.claude/hooks/semantic-context-inject.py')
DEBOUNCE = load('retrieval_debounce_control', ROOT / '.claude/hooks/reindex-debounce.py')
CANARY = 'SYNTHETIC_PRIVATE_CANARY_ADAPTER_DO_NOT_OUTPUT'


class AdapterControls(unittest.TestCase):
    def test_import_has_no_persistent_corpus_metadata_cache(self):
        self.assertFalse(hasattr(SERVER, 'CHUNKS'))

    def test_malformed_requests_never_spawn_a_provider(self):
        with patch.object(SERVER.subprocess, 'Popen', side_effect=AssertionError('no spawn')):
            for query, kwargs in [('', {}), ('q', {'top_k': True}), ('q', {'top_k': 99}),
                                  ('q', {'mode': []}), ('q', {'scope': {'x': CANARY}}),
                                  ('q', {'max_characters': 0})]:
                self.assertEqual(SERVER.search(query, **kwargs)['reason'], 'invalid-query-contract')

    def test_failed_query_cannot_smuggle_hit_content(self):
        result = (1, json.dumps({'schema': SERVER.RESULT_SCHEMA,
            'state': 'stale', 'hits': [{'text': CANARY}]}).encode())
        with patch.object(SERVER, '_capture', return_value=result):
            result = SERVER.search('synthetic')
        self.assertEqual(result['reason'], 'failed-query-returned-content')
        self.assertNotIn(CANARY, json.dumps(result))

    def test_successful_json_after_failed_process_is_rejected(self):
        result = (1, json.dumps({'schema': SERVER.RESULT_SCHEMA, 'state': 'no_matches', 'hits': []}).encode())
        with patch.object(SERVER, '_capture', return_value=result):
            self.assertEqual(SERVER.search('synthetic')['reason'], 'query-exit-and-result-disagree')

    def test_timeouts_clean_owned_process_tree_and_expose_no_raw_exception(self):
        with self.assertRaises(SERVER.TransportError) as caught:
            SERVER._capture([sys.executable, '-c', 'import time;time.sleep(30)'], '', timeout_seconds=.1)
        self.assertEqual(caught.exception.reason, 'query-timeout')

    def test_unconfirmed_timeout_cleanup_is_not_reported_as_completed(self):
        with patch.object(SERVER, '_capture', side_effect=SERVER.TransportError('query-timeout-cleanup-unverified')):
            self.assertEqual(SERVER.search('synthetic')['reason'], 'query-timeout-cleanup-unverified')

    def test_nonreading_child_cannot_block_timeout_on_a_full_input_pipe(self):
        with self.assertRaises(SERVER.TransportError) as caught:
            SERVER._capture([sys.executable, '-c', 'import time;time.sleep(30)'],
                            'X' * 96000, timeout_seconds=.1)
        self.assertEqual(caught.exception.reason, 'query-timeout')

    def test_stdout_flood_is_stopped_before_unbounded_capture(self):
        with self.assertRaises(SERVER.TransportError) as caught:
            SERVER._capture([sys.executable, '-c', 'import sys;sys.stdout.buffer.write(b"X"*8000000)'],
                            '', timeout_seconds=5, output_limit=32768)
        self.assertEqual(caught.exception.reason, 'query-response-too-large')

    def test_stderr_flood_is_discarded_and_cannot_enter_response(self):
        code, stdout = SERVER._capture([sys.executable, '-c',
            'import sys;sys.stderr.buffer.write(b"X"*8000000);sys.stdout.write("{}")'], '', timeout_seconds=5)
        self.assertEqual((code, stdout), (0, b'{}'))

    def test_mcp_distinguishes_unavailable_from_no_matches(self):
        for state, error in [('unavailable', True), ('no_matches', False)]:
            result = {'schema': SERVER.RESULT_SCHEMA, 'state': state, 'reason': 'synthetic', 'hits': []}
            with patch.object(SERVER, 'search', return_value=result), patch.object(SERVER.sys, 'stdout', io.StringIO()) as out:
                SERVER.handle({'jsonrpc': '2.0', 'id': 4, 'method': 'tools/call',
                               'params': {'name': 'search', 'arguments': {'query': 'synthetic'}}})
                self.assertEqual(json.loads(out.getvalue())['result']['isError'], error)

    def test_hook_failed_or_malformed_result_supplies_no_source_text(self):
        for result in [[], {'schema': SERVER.RESULT_SCHEMA, 'state': 'stale', 'hits': [{'text': CANARY}]},
                       {'schema': SERVER.RESULT_SCHEMA, 'state': 'passed', 'classification': 'MIXED',
                        'hits': [{'text': CANARY}]}]:
            self.assertNotIn(CANARY, HOOK.context(result))

    def test_hook_requires_generation_classification_and_safe_path(self):
        hit = {'generation_id': 'g-one', 'classification': 'SYNTHETIC', 'source_path': 'wiki/public.md',
               'source_version': '1', 'kind': 'method', 'source_span': {'start_line': 4},
               'context_spans': [{'text': 'Units: USD millions.'}], 'text': 'A synthetic financial passage.'}
        result = {'schema': SERVER.RESULT_SCHEMA, 'state': 'passed', 'classification': 'PUBLIC_OR_SYNTHETIC_ONLY',
                  'generation_id': 'g-one', 'hits': [hit]}
        self.assertIn('Units: USD millions.', HOOK.context(result))
        for change in [{'source_path': 'wiki/private/account.md'}, {'generation_id': 'g-two'}, {'classification': 'UNKNOWN'}]:
            self.assertNotIn(CANARY, HOOK.context({**result, 'hits': [{**hit, **change, 'text': CANARY}]}))

    def test_debounce_uses_canonical_sources_without_generated_duplicate_hints(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / 'marker'
            with patch.object(DEBOUNCE, 'MARKER', marker):
                for path, expected in [('/path/to/vault/.agents/skills/test/SKILL.md', True),
                                       ('/path/to/vault/.claude/skills/test/SKILL.md', False),
                                       ('/path/to/vault/private/secret.md', False)]:
                    if marker.exists(): marker.unlink()
                    with patch.object(DEBOUNCE.sys, 'stdin', io.StringIO(json.dumps({
                            'tool_name': 'Edit', 'tool_input': {'file_path': path}}))):
                        DEBOUNCE.main()
                    self.assertEqual(marker.exists(), expected)


if __name__ == '__main__':
    unittest.main()
