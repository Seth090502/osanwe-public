"""Submission-only client. Never reads strategy holdouts or stores account data.

Endpoint and public key are explicit. Bearer token comes from one environment
variable; no credential/config scans, login automation, or model substitution.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

MAX_BYTES = 8192
OPERATIONS = ('reserve', 'issue', 'submit', 'score', 'finish', 'close', 'seal', 'release', 'acknowledge', 'cohort-seal', 'cohort-close', 'cohort-release')


def canonical(value):
    # Receipt fields are integers and exact JSON floats; verify JS serialization
    # with retained payload bytes if a future schema introduces ambiguous floats.
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def verify_receipt(receipt, spki):
    from cryptography.hazmat.primitives.serialization import load_der_public_key
    if receipt.get('algorithm') != 'Ed25519' or receipt.get('payload', {}).get('schema') not in ('osanwe.reasoning-receipt/1', 'osanwe.reasoning-cohort-receipt/1'):
        raise ValueError('unsupported receipt')
    encoded = base64.b64decode(receipt['signed_payload'], validate=True)
    if canonical(json.loads(encoded)) != canonical(receipt['payload']):
        raise ValueError('receipt object differs from signed bytes')
    if hashlib.sha256(encoded).hexdigest() != receipt.get('payload_sha256'):
        raise ValueError('receipt payload changed')
    if hashlib.sha256(canonical(receipt['artifact_manifest']).encode('utf-8')).hexdigest() != receipt['payload']['artifact_manifest_sha256']:
        raise ValueError('artifact manifest changed')
    load_der_public_key(base64.b64decode(spki, validate=True)).verify(base64.b64decode(receipt['signature'], validate=True), encoded)
    return {'verified': True, 'evidence_class': receipt['payload']['evidence_class'],
            'scope': receipt['payload']['assessment_scope'], 'provider_attestation': False}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        raise ValueError('redirect refused; submission credential must stay on the configured endpoint')


def request(endpoint, operation, payload, *, token, development=False):
    url = urllib.parse.urlsplit(endpoint)
    local = url.hostname in ('127.0.0.1', 'localhost', '::1')
    if operation not in OPERATIONS or url.username or url.password or url.query or url.fragment:
        raise ValueError('invalid endpoint or operation')
    if url.scheme != 'https' and not (development and local and url.scheme == 'http'):
        raise ValueError('HTTPS required; local HTTP requires explicit development mode')
    if not token or len(token) > 256 or '\n' in token or '\r' in token:
        raise ValueError('submission credential unavailable')
    data = canonical(payload).encode('utf-8')
    if len(data) > MAX_BYTES:
        raise ValueError('payload too large')
    req = urllib.request.Request(endpoint.rstrip('/')+'/v1/'+operation, data=data, method='POST',
                                 headers={'Authorization': 'Bearer '+token, 'Content-Type': 'application/json'})
    try:
        response = urllib.request.build_opener(NoRedirect).open(req, timeout=30)
    except urllib.error.HTTPError as error:
        # Server intentionally emits only bounded status codes, never raw inputs.
        response = error
    with response:
        raw = response.read(1_000_001)
        if len(raw) > 1_000_000:
            raise ValueError('response too large')
        result = json.loads(raw)
    if result.get('status') == 'refused':
        return result, 2
    return result, 0


def permitted_payload_path(path, maximum=MAX_BYTES):
    resolved = Path(path).resolve()
    forbidden = {'.raw', 'private', 'finance', 'credentials'}
    if any(part.lower() in forbidden for part in resolved.parts) or resolved.name.lower().startswith('.env') or resolved.name.lower() == 'auth.json' or resolved.name.lower().endswith('.local.md'):
        raise ValueError('protected input path')
    if resolved.stat().st_size > maximum:
        raise ValueError('payload too large')
    return resolved


def main(argv=None):
    parser = argparse.ArgumentParser(description='Reasoning protocol client: submission-only; no strategy holdout access')
    parser.add_argument('operation', choices=(*OPERATIONS, 'verify-receipt'))
    parser.add_argument('--payload', required=True, help='Explicit public/synthetic JSON request path')
    parser.add_argument('--endpoint')
    parser.add_argument('--token-env', default='OSANWE_EVAL_SUBMISSION_TOKEN')
    parser.add_argument('--development', action='store_true')
    parser.add_argument('--public-key', help='Explicit public Ed25519 SPKI base64 path; never a private key')
    args = parser.parse_args(argv)
    try:
        # A receipt may be larger than a request. Public receipts contain no prose or account facts.
        if args.operation == 'verify-receipt':
            if not args.public_key:
                raise ValueError('public key required')
            result = verify_receipt(json.loads(permitted_payload_path(args.payload, 1_000_000).read_text(encoding='utf-8')),
                                    permitted_payload_path(args.public_key).read_text(encoding='ascii').strip())
            code = 0
        else:
            if not args.endpoint or not re.fullmatch(r'[A-Z][A-Z0-9_]{1,63}', args.token_env):
                raise ValueError('explicit endpoint and token variable required')
            payload = json.loads(permitted_payload_path(args.payload).read_text(encoding='utf-8'))
            result, code = request(args.endpoint, args.operation, payload,
                                   token=os.environ.get(args.token_env, ''), development=args.development)
            if code == 0 and args.operation in ('release', 'cohort-release'):
                if not args.public_key:
                    raise ValueError('pinned public key required before score release')
                verify_receipt(result, permitted_payload_path(args.public_key).read_text(encoding='ascii').strip())
        print(canonical(result))
        return code
    except Exception:
        # Do not echo request fragments, secrets, account values, or exception traces.
        print('{"status":"refused","error":"client_validation_or_transport_failed"}')
        return 2


if __name__ == '__main__':
    sys.exit(main())
