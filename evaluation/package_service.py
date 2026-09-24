"""Package explicitly allowlisted public evaluator code, fixtures and procedures.

No runtime state, local native transcripts, credentials, account data, evaluation
logs or original holdouts are discovered. Existing output bytes are not replaced.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parent
FILES=(
    '.gitattributes','REASONING-EVALUATOR.md','challenge_protocol.md','reasoning_protocol.json',
    'request_access.py','reasoning_client.py','native_pilot.py','score_native.mjs',
    'protocol_statistics.py','development_cases.json','build_development_cases.py','calculation_evidence.py',
    'account_scope_development.py','account_scope_development_v1.json','tests/test_account_scope.py',
    'reviewer_controls.py','reviewer_schema.py','run_reviewer_controls.py',
    'prepare_deployment.mjs','benchmark_service.mjs','package_service.py',
    'service/worker.mjs','service/schema.sql','service/witness.sql','service/wrangler.jsonc','service/development.mjs','service/cohort-freeze.mjs',
    'tests/service.test.mjs','tests/cohort.test.mjs','tests/test_protocol.py','tests/test_native_pilot.py','tests/test_deployment.py','tests/test_reviewer_controls.py',
    'reports/native-pilot-runtime-2026-09-13/service/worker.mjs',
    'reports/native-pilot-runtime-2026-09-13/development_cases.json',
    'reports/.gitattributes','tests/fixtures/.gitattributes','tests/fixtures/witness-v1.sql',
    'reports/cohort-controls-2026-09-13.json',
    'reports/reasoning-protocol-2026-09-13-before-coverage-v2.json',
    'reports/account-scope-coverage-controls-2026-09-13.json',
)


def package(destination):
    output=Path(destination).resolve()
    if output.exists():raise ValueError('existing package cannot be overwritten')
    if any(part.lower() in {'.raw','private','finance','credentials','holdout','holdouts','hidden','locked'} for part in output.parts):
        raise ValueError('protected package destination')
    rows={f'evaluation/{name}':(ROOT/name).read_bytes() for name in FILES}
    rows['tools/eval-interface.py']=(ROOT.parent/'tools/eval-interface.py').read_bytes()
    manifest={'schema':'osanwe.evaluator-package/1','evidence_class':'public-development-only',
              'deployed':False,'sealed_admission_included':False,'private_material_included':False,
              'files':{path:hashlib.sha256(data).hexdigest() for path,data in rows.items()}}
    rows['EVALUATOR-PACKAGE-MANIFEST.json']=(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode('ascii')
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for path,data in rows.items():archive.writestr(path,data)
    with zipfile.ZipFile(output) as archive:
        for path,expected in manifest['files'].items():
            if hashlib.sha256(archive.read(path)).hexdigest()!=expected:raise ValueError('package verification failed')
    return {'status':'packaged-and-hash-verified','path':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'files':len(rows)}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output')
    args=p.parse_args();print(json.dumps(package(args.output),sort_keys=True))
