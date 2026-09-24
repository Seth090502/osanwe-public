// Shared, testable traversal boundary for the existing local indexer.
import { closeSync, constants, fstatSync, lstatSync, openSync, readFileSync, readdirSync, realpathSync } from 'node:fs';
import { isAbsolute, join, relative, resolve, sep } from 'node:path';

const deniedDirectories = new Set(['.raw', 'private', 'finance', 'credentials',
  'test-tmp', '.precheck', '_archive', '.obsidian', 'node_modules', '.git']);
const approvedRoots = new Set(['wiki', 'calendar', 'atlas', 'efforts', 'docs']);

export function allowedRelativePath(name) {
  const parts = name.replace(/\\/g, '/').toLowerCase().split('/');
  if (!parts.length || parts.some(p => !p || p === '.' || p === '..' ||
      /[\x00-\x1f:]/.test(p) || p.endsWith('.') || p.endsWith(' ') ||
      deniedDirectories.has(p) || p.startsWith('.env') || p === 'auth.json' || p.endsWith('.local.md'))) return false;
  // Canonical instructions get one vote. Generated .claude mirrors are aliases,
  // never separately admitted search documents.
  return approvedRoots.has(parts[0]) || (parts[0] === '.agents' && ['skills', 'roles'].includes(parts[1]));
}

function inside(root, candidate) {
  const rel = relative(root, candidate);
  return rel !== '' && !isAbsolute(rel) && rel !== '..' && !rel.startsWith('..' + sep) && allowedRelativePath(rel);
}

export function approvedPath(root, candidate) {
  root = realpathSync(root);
  candidate = resolve(candidate);
  if (!inside(root, candidate)) return false;
  // Refuse symbolic links/junctions at every segment, before traversal/read.
  let current = root;
  for (const part of relative(root, candidate).split(sep)) {
    current = join(current, part);
    const stat = lstatSync(current);
    if (stat.isSymbolicLink()) return false;
  }
  return inside(root, realpathSync(candidate));
}

export function enumerateApprovedMarkdown(root, scan) {
  root = realpathSync(root);
  const result = [];
  function walk(path) {
    if (!approvedPath(root, path)) return;
    for (const entry of readdirSync(path, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      const next = join(path, entry.name);
      if (!allowedRelativePath(relative(root, next)) || entry.isSymbolicLink()) continue;
      if (entry.isDirectory()) walk(next);
      else if (entry.isFile() && entry.name.toLowerCase().endsWith('.md') && approvedPath(root, next)) {
        if (lstatSync(next).nlink === 1) result.push(next);
      }
    }
  }
  for (const path of scan) walk(path);
  return [...new Set(result)];
}

export function readApprovedMarkdown(root, path) {
  return readApprovedMarkdownBytes(root, path).toString('utf8');
}

export function readApprovedMarkdownBytes(root, path, maximumBytes = 8 * 1024 * 1024) {
  if (!approvedPath(root, path) || !path.toLowerCase().endsWith('.md')) throw new Error('index source outside approved boundary');
  const before = lstatSync(path);
  if (!before.isFile() || before.nlink !== 1) throw new Error('index source must be an unlinked regular file');
  if (!Number.isSafeInteger(maximumBytes) || maximumBytes <= 0 || before.size > maximumBytes) throw new Error('index source exceeds approved read budget');
  const descriptor = openSync(path, constants.O_RDONLY | (constants.O_NOFOLLOW || 0));
  try {
    const opened = fstatSync(descriptor);
    if (opened.dev !== before.dev || opened.ino !== before.ino || opened.nlink !== 1) throw new Error('index source changed before read');
    return readFileSync(descriptor);
  } finally {
    closeSync(descriptor);
  }
}
