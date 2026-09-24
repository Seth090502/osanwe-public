"""Native source-admission -> generation -> MCP check, synthetic OS-temp data only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/pit'))
import test_financial_documents as fixture


def main():
    case = fixture.DocumentAdmissionTests()
    case.setUp()
    started = time.monotonic()
    try:
        case.approve()
        base = case.root / 'candidate'
        base.mkdir()
        environment = {**os.environ, 'OSANWE_RETRIEVAL_ROOT': str(case.root),
                       'OSANWE_RETRIEVAL_BASE': str(base), 'OSANWE_DOCUMENT_REGISTRY': str(case.path)}
        runtime = Path('/path/to/home/.vault-substrate')
        def command(args, input=None, expected=0):
            result = subprocess.run(args, input=input, text=True, capture_output=True,
                                    cwd=ROOT, env=environment, timeout=90,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            if result.returncode != expected:
                raise AssertionError('synthetic child failed: ' + result.stdout[:1000])
            return json.loads(result.stdout)
        before = command(['node', str(runtime / 'reindex-runner.mjs'), '--inspect'], expected=3)
        assert before['reason'] == 'no-admitted-generation'
        assert not (base / 'index/current.json').exists()
        built = command(['node', str(runtime / 'index-vault.mjs'), '--publish'])
        assert built['state'] == 'passed' and built['published'] is True
        inspected = command(['node', str(runtime / 'reindex-runner.mjs'), '--inspect'])
        assert inspected['state'] == 'passed' and inspected['admitted_document_count'] == 1
        request = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'search',
                   'arguments': {'query': 'accounting margin', 'scope': 'accounting', 'mode': 'hybrid'}}}
        result = command([sys.executable, '/path/to/local/vault-search/server.py'], json.dumps(request) + '\n')
        content = result['result']['structuredContent']
        assert result['result']['isError'] is False and content['state'] == 'passed'
        assert content['generation_id'] == inspected['generation_id']
        assert any('25 percent' in hit['text'] for hit in content['hits'])
        assert all(hit['supporting_origin_ids'] == ['origin:fixture-source'] for hit in content['hits'])
        loader = case.root / 'deny-embedding-imports.mjs'
        loader.write_text("export async function resolve(specifier, context, next) {\n"
                          " if (specifier.includes('@xenova') || specifier.includes('hnswlib'))\n"
                          "  throw new Error('synthetic-provider-import-blocked');\n"
                          " return next(specifier, context);\n}\n", encoding='utf-8')
        lexical = command(['node', '--experimental-loader', loader.as_uri(), str(runtime / 'qsearch.mjs'), '--stdin'],
                          json.dumps({'query': 'margin', 'mode': 'lexical', 'scope': 'accounting'}))
        assert lexical['state'] == 'passed' and lexical['generation_id'] == inspected['generation_id']
        assert lexical['embedding_use'] == 'not-used-generation-identity-only'
        assert lexical['evidence_coverage'] == 'retrieved-subset-not-complete-answer-evidence'
        blocked_hybrid = command(['node', '--experimental-loader', loader.as_uri(), str(runtime / 'qsearch.mjs'), '--stdin'],
                                 json.dumps({'query': 'margin', 'mode': 'hybrid'}), expected=1)
        assert blocked_hybrid['state'] == 'unavailable' and blocked_hybrid['hits'] == []
        # An editor write has no Claude debounce marker, but admission must expire.
        (case.root / 'docs/margin.md').write_text(fixture.TEXT + 'Changed fixture source.\n', encoding='utf-8')
        after = command(['node', str(runtime / 'reindex-runner.mjs'), '--inspect'], expected=3)
        assert after['state'] == 'unavailable' and after['reason'] == 'no-admitted-documents'
        rejected = command([sys.executable, '/path/to/local/vault-search/server.py'], json.dumps(request) + '\n')
        assert rejected['result']['isError'] is True
        assert rejected['result']['structuredContent']['hits'] == []
        print(json.dumps({'schema': 'osanwe.retrieval-admission-e2e/1', 'state': 'passed',
              'classification': 'SYNTHETIC', 'admitted_documents': 1, 'native_provider': 'cached BGE/HNSW',
              'mcp_verified': True, 'cross_harness_source_change_refused': True, 'live_index_modified': False,
              'lexical_works_with_embedding_imports_blocked': True,
              'elapsed_seconds': round(time.monotonic() - started, 6),
              'scope': 'synthetic source admission and native CLI/MCP integration; no real corpus or financial quality claim'}))
    finally:
        case.doCleanups()


if __name__ == '__main__':
    main()
