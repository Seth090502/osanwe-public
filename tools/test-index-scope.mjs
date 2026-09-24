import assert from 'node:assert/strict';
import { linkSync, mkdtempSync, mkdirSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { basename, dirname, join, resolve } from 'node:path';
import { allowedRelativePath, enumerateApprovedMarkdown, readApprovedMarkdown } from './index-scope.mjs';

const root = mkdtempSync(join(tmpdir(), 'osanwe-index-scope-'));
let cases = 0;
try {
  const protectedPaths = ['private/secret.md', 'finance/secret.md', 'credentials/secret.md', '.raw/secret.md',
    'wiki/private/secret.md', 'wiki/PRIVATE/secret.md', 'wiki/finance/secret.md', 'wiki/credentials/secret.md',
    'wiki/.env-secret/secret.md', 'wiki/auth.json', 'wiki/note.local.md', 'wiki/.env.md'];
  for (const name of [...protectedPaths, 'wiki/safe.md', 'Atlas/safe.md', 'docs/safe.md', '.agents/skills/example/SKILL.md']) {
    const file = join(root, ...name.split('/'));
    mkdirSync(join(file, '..'), { recursive: true });
    writeFileSync(file, protectedPaths.includes(name) ? 'SYNTHETIC_PRIVATE_CANARY_735' : 'approved synthetic public text');
  }
  for (const name of protectedPaths) {
    assert.equal(allowedRelativePath(name), false, name);
    assert.throws(() => readApprovedMarkdown(root, join(root, name)));
    cases++;
  }
  const scan = ['wiki', 'Atlas', 'docs', 'private', 'finance', 'credentials', '.raw', '.agents/skills'].map(p => join(root, p));
  let files = enumerateApprovedMarkdown(root, scan);
  assert.equal(files.length, 4);
  assert.equal(files.map(p => readApprovedMarkdown(root, p)).join('').includes('SYNTHETIC_PRIVATE_CANARY_735'), false);
  cases++;
  linkSync(join(root, 'private/secret.md'), join(root, 'wiki/hardlink.md'));
  assert.equal(enumerateApprovedMarkdown(root, scan).some(p => p.endsWith('hardlink.md')), false);
  assert.throws(() => readApprovedMarkdown(root, join(root, 'wiki/hardlink.md')));
  cases++;
  symlinkSync(join(root, 'private'), join(root, 'wiki/junction'), process.platform === 'win32' ? 'junction' : 'dir');
  assert.equal(enumerateApprovedMarkdown(root, scan).some(p => p.includes('junction')), false);
  assert.throws(() => readApprovedMarkdown(root, join(root, 'wiki/junction/secret.md')));
  cases++;
  assert.equal(allowedRelativePath('../private/secret.md'), false);
  assert.equal(allowedRelativePath('wiki/../private/secret.md'), false);
  assert.equal(allowedRelativePath('.claude/skills/example/SKILL.md'), false);
  assert.equal(allowedRelativePath('wiki/file.md:secret'), false);
  cases++;
  console.log(JSON.stringify({ state: 'passed', cases, scope: 'synthetic traversal/read boundaries', includes_junction_and_hardlink: true }));
} finally {
  // Fixed OS-temp directory returned by mkdtemp; no path is derived from vault data.
  assert.equal(resolve(dirname(root)), resolve(tmpdir()));
  assert.equal(basename(root).startsWith('osanwe-index-scope-'), true);
  rmSync(root, { recursive: true, force: true });
}
