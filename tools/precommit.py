#!/usr/bin/env python3
"""Harness-neutral pre-commit cage for the Osanwe vault (OSANWE-V2-2026-08).

Git-layer carrier for the HB-class invariants that previously lived only in Claude
Code hooks. Wired via `.githooks/pre-commit` + `git config core.hooksPath .githooks`
so EVERY harness that commits in this repo inherits the same rules.

Rules (each has a failing test in tools/test-precommit.py):
  R1 protected-paths   no staged change touches .raw/, private/, finance/,
                       credentials/, .obsidian/
  R2 append-only       the four ledgers (sessions-log, decision-log,
                       execute-or-decline, wiki/insight-stream) may only be changed
                       by APPEND: existing bytes survive as a strict prefix of the
                       new content (same invariant as tools/append-only-check.py,
                       which stays the interactive PreToolUse carrier)
  R3 atlas-content     while .githooks/STRICT exists: Atlas/ changes must be
                       frontmatter-only AND opt-in via env OSANWE_ATLAS_FM_OK=1;
                       every allowance is logged to .claude/state/bypasses-<date>.log.
                       STRICT is removed at mission P5 so post-merge human Atlas
                       writes are not blocked (then this rule is dormant).
  R4 ascii-added-lines ADDED lines in agent-authored trees (wiki/, Calendar/,
                       Efforts/, .agents/, tools/, docs/, root *.md) must be pure
                       ASCII. Legacy untouched lines are NOT rescanned.
  R5 domain-ban        no added line introduces a `domain:` field or a
                       `domain/` / `type/` namespaced tag.
  R6 frontmatter       NEW .md files in wiki/, Calendar/, Efforts/ carry canonical
                       frontmatter (validated with tools/frontmatter-check.py).
  R7 contract-stub     AGENTS.md is the contract and must be staged as a regular,
                       nonempty file; CLAUDE.md must be staged as exactly the
                       one-line stub `@AGENTS.md`, which imports it; and
                       .claude/CLAUDE.md may not exist in the index or the worktree.
                       Without the stub a root CLAUDE.local.md stops Claude Code
                       reading AGENTS.md; anything more in CLAUDE.md is a second
                       set of rules.

Exit codes: 0 clean, 1 blocked (commit refused), 2 internal error.
"""

import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

VAULT_ROOT = Path(os.environ.get("OSANWE_VAULT_ROOT") or (Path(__file__).resolve().parent.parent))

PROTECTED_PREFIXES = (".raw/", "private/", "finance/", "credentials/", ".obsidian/")
LEDGERS = (
    "Calendar/decisions/sessions-log.md",
    "Calendar/decisions/decision-log.md",
    "Calendar/decisions/execute-or-decline.md",
    "wiki/insight-stream.md",
)
ATLAS_PREFIX = "atlas/"
# The whole of root CLAUDE.md: an import of the contract and nothing else (R7).
CONTRACT_STUB = b"@AGENTS.md\n"
# A second project instruction file beside the contract; R7 refuses it.
SECOND_CONTRACTS = (".claude/CLAUDE.md",)
ASCII_SCOPES = ("wiki/", "calendar/", "efforts/", ".agents/", "tools/", "docs/")
NEW_MD_SCOPES = ("wiki/", "calendar/", "efforts/")
DOMAIN_FIELD_RE = re.compile(r"^\s*domain\s*:", re.MULTILINE)
NAMESPACED_TAG_RE = re.compile(r"^\s*-\s*(domain|type)/", re.MULTILINE)
def strict_active():
    return (VAULT_ROOT / ".githooks" / "STRICT").exists()


def _git(*args):
    """Run git in the vault root, return stdout bytes."""
    res = subprocess.run(
        ["git"] + list(args),
        cwd=str(VAULT_ROOT),
        capture_output=True,
    )
    if res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {res.stderr.decode(errors='replace')[:300]}")
    return res.stdout


def _git_ok(*args):
    res = subprocess.run(["git"] + list(args), cwd=str(VAULT_ROOT), capture_output=True)
    return res.returncode == 0


def staged_files():
    """[(status, path)] from the index, NUL-safe."""
    out = _git("diff", "--cached", "--name-status", "-z")
    recs = out.split(b"\0")
    files = []
    i = 0
    while i < len(recs):
        rec = recs[i]
        if not rec:
            i += 1
            continue
        status = rec.decode()
        # rename/copy records carry two paths
        if status.startswith("R") or status.startswith("C"):
            src = recs[i + 1].decode().replace("\\", "/")
            dst = recs[i + 2].decode().replace("\\", "/")
            files.append((status, src))
            files.append((status[0], dst))
            i += 3
        else:
            path = recs[i + 1].decode().replace("\\", "/")
            files.append((status[0] if status else "M", path))
            i += 2
    return files


def head_content(path):
    if not _git_ok("cat-file", "-e", f"HEAD:{path}"):
        return None
    return _git("cat-file", "blob", f"HEAD:{path}")


def staged_content(path):
    if not _git_ok("show", f":{path}"):
        # git show exits nonzero for missing stage-0 entries
        return None
    return _git("show", f":{path}")


def staged_regular_file(path):
    entries = [row for row in _git("ls-files", "--stage", "-z", "--", path).split(b"\0") if row]
    if len(entries) != 1:
        return False
    mode, _object, stage = entries[0].split(b"\t", 1)[0].split()
    return mode in (b"100644", b"100755") and stage == b"0"


def staged_any(path):
    """True when the index holds any entry at path -- a file, a symlink or a conflict stage."""
    return any(row for row in _git("ls-files", "--stage", "-z", "--", path).split(b"\0") if row)


def added_lines(path):
    """['+' lines of the staged diff, UTF-8 decoded]."""
    try:
        out = _git("diff", "--cached", "-U0", "--", path)
    except RuntimeError:
        return []
    text = out.decode("utf-8", errors="replace")
    lines = []
    in_hunk = False
    for ln in text.splitlines():
        if ln.startswith("@@"):
            in_hunk = True
            continue
        if in_hunk and ln.startswith("+") and not ln.startswith("+++"):
            lines.append(ln[1:])
    return lines


def _fm_module():
    """Load tools/frontmatter-check.py as a module (single source of truth for
    canonical-frontmatter parsing/validation across R6 and --tree mode)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "frontmatter_check", VAULT_ROOT / "tools" / "frontmatter-check.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def strip_frontmatter(raw_bytes):
    text = raw_bytes.decode("utf-8", errors="replace")
    if not text.startswith("---"):
        return text
    m = re.search(r"\n---\s*\n", text[3:])
    if not m:
        return text
    return text[3 + m.end():]


def log_bypass(tag, path):
    day = datetime.date.today().isoformat()
    log = VAULT_ROOT / ".claude" / "state" / f"bypasses-{day}.log"
    log.parent.mkdir(exist_ok=True, parents=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now().isoformat()} {tag} {path}\n")


def check(violations):
    files = staged_files()

    # Check the index, not the working tree, so a repaired worktree cannot conceal a
    # commit that deletes or replaces the contract. This also catches deletion/rename.
    canon = staged_content("AGENTS.md") if staged_regular_file("AGENTS.md") else None
    if canon is None or not canon.strip():
        violations.append(("R7", "AGENTS.md",
                           "the root contract must be staged as a regular, nonempty file; "
                           "stage AGENTS.md"))
    stub = staged_content("CLAUDE.md") if staged_regular_file("CLAUDE.md") else None
    if stub != CONTRACT_STUB:
        violations.append(("R7", "CLAUDE.md",
                           "must be staged as exactly the one-line stub '@AGENTS.md'; without it a "
                           "root CLAUDE.local.md stops Claude Code reading AGENTS.md, and anything "
                           "more is a second set of rules"))
    # The working copies are what a live session loads, staged or not.
    live_canon = VAULT_ROOT / "AGENTS.md"
    if live_canon.is_symlink() or not live_canon.is_file() or not live_canon.read_bytes().strip():
        violations.append(("R7", "AGENTS.md (worktree)",
                           "the working copy of the contract is missing, empty or a symbolic link; a "
                           "live session loads it whether or not it is staged"))
    live_stub = VAULT_ROOT / "CLAUDE.md"
    if (live_stub.is_symlink() or not live_stub.is_file()
            or live_stub.read_bytes().replace(b"\r\n", b"\n") != CONTRACT_STUB):
        violations.append(("R7", "CLAUDE.md (worktree)",
                           "the working copy is not exactly the one-line stub '@AGENTS.md'; a live "
                           "session loads it whether or not it is staged"))
    for extra in SECOND_CONTRACTS:
        path = VAULT_ROOT / extra
        if staged_any(extra) or path.is_file() or path.is_symlink():
            violations.append(("R7", extra,
                               "a second project instruction file beside the contract; delete it"))

    # R1 protected paths
    for status, path in files:
        norm = path.lower()
        if any(norm.startswith(p) for p in PROTECTED_PREFIXES):
            violations.append(("R1", path, "protected path (.raw/private/finance/credentials/.obsidian)"))

    # R2 append-only ledgers
    for status, path in files:
        if path not in LEDGERS:
            continue
        if status in ("D",):
            violations.append(("R2", path, "ledger deletion is never append-only"))
            continue
        if status in ("A",):
            continue  # brand-new ledger file: nothing to preserve
        old = head_content(path)
        new = staged_content(path)
        if old is None:
            continue
        if not new.startswith(old):
            violations.append(("R2", path, "ledger modified outside strict-append (existing bytes not preserved as prefix)"))

    # R3 Atlas content while STRICT exists
    if strict_active():
        fm_opt_in = os.environ.get("OSANWE_ATLAS_FM_OK") == "1"
        for status, path in files:
            if not path.lower().startswith(ATLAS_PREFIX):
                continue
            if status == "D":
                violations.append(("R3", path, "Atlas deletion while STRICT active"))
                continue
            if status == "A":
                violations.append(("R3", path, "new Atlas file while STRICT active (Atlas is human-write-only)"))
                continue
            if not path.lower().endswith(".md"):
                violations.append(("R3", path, "non-markdown Atlas change while STRICT active"))
                continue
            old = head_content(path)
            new = staged_content(path)
            if old is None or new is None:
                violations.append(("R3", path, "unreadable Atlas pair while STRICT active"))
                continue
            if strip_frontmatter(old) != strip_frontmatter(new):
                violations.append(("R3", path, "Atlas BODY changed while STRICT active (frontmatter-only repairs only)"))
                continue
            if not fm_opt_in:
                violations.append(("R3", path, "frontmatter-only Atlas repair requires env OSANWE_ATLAS_FM_OK=1"))
                continue
            log_bypass("precommit-atlas-fm-ok", path)

    # R4/R5 added-line scans in agent-authored scopes
    VERBATIM_COPY_SCOPES = (
        # generated node dirs: bodies are BYTE-COPIES of ledger entries by
        # construction (ADR-02 strangler); provenance = the ledger file, which
        # stays the R4 enforcement surface for NEW appends. Legacy entries
        # legally contain non-ASCII (pre-dates Pattern-22 discipline).
        "calendar/sessions/",
        "calendar/decisions/records/",
        "calendar/decisions/loops/",
        "wiki/insights/",
        # mission sandbox: regenerable evidence copy of the ledgers
        "/_work/sandbox/",
    )
    for status, path in files:
        if status == "D":
            continue
        lowered = path.lower()
        if any(lowered.startswith(p) or p in lowered for p in VERBATIM_COPY_SCOPES):
            continue
        in_scope = any(lowered.startswith(p) for p in ASCII_SCOPES) or (
            "/" not in path and path.lower().endswith(".md")
        )
        if not in_scope:
            continue
        for ln in added_lines(path):
            if any(b > 127 for b in ln.encode("utf-8")):
                snippet = ln.strip()[:80]
                violations.append(("R4", path, f"non-ASCII byte in ADDED line: {snippet!r}"))
            if DOMAIN_FIELD_RE.search(ln + "\n"):
                violations.append(("R5", path, f"`domain:` field introduced: {ln.strip()[:60]!r}"))
            elif NAMESPACED_TAG_RE.match(ln + "\n"):
                violations.append(("R5", path, f"namespaced tag domain/ or type/ introduced: {ln.strip()[:60]!r}"))

    # R6 canonical frontmatter on NEW md files in vault dirs
    fm_mod = _fm_module()
    for status, path in files:
        if status != "A":
            continue
        lowered = path.lower()
        if not lowered.endswith(".md"):
            continue
        if not any(lowered.startswith(p) for p in NEW_MD_SCOPES):
            continue
        # by-name exemption: Efforts/*/_work/ holds intermediate evidence files
        # (mission A4.3: JSON/MD scratch under _work), not vault organs -- frontmatter
        # there is overhead, not signal. Narrow: only an explicit /_work/ segment.
        if "/_work/" in lowered:
            continue
        raw = staged_content(path)
        if raw is None:
            continue
        text = raw.decode("utf-8", errors="replace")
        fm = fm_mod.parse_frontmatter(text)
        if fm is None:
            violations.append(("R6", path, "new vault .md missing canonical frontmatter"))
            continue
        errs = fm_mod.validate(fm)
        for e in errs:
            violations.append(("R6", path, f"frontmatter invalid: {e}"))


def check_tree(strict_tree=False):
    """Whole-tree mode for the checkall consistency command.

    BLOCKS on: any tracked file under protected prefixes; a missing ledger.
    REPORTS by default (BLOCKS with --strict-tree): missing-frontmatter files in
    wiki/Calendar/Efforts (non-_work), files containing bytes>127 in agent
    trees. Always blocks a missing, empty, or divergent root contract pair.
    """
    problems = []
    # tracked files must never include protected paths
    out = _git("ls-files")
    for p in out.decode(errors="replace").splitlines():
        norm = p.replace("\\", "/").lower()
        if any(norm.startswith(x) for x in PROTECTED_PREFIXES):
            problems.append(("R1", p, "PROTECTED path is TRACKED in git"))
    for lp in LEDGERS:
        if not (VAULT_ROOT / lp).is_file():
            problems.append(("R2", lp, "append-only ledger MISSING from tree"))
    canon = VAULT_ROOT / "AGENTS.md"
    if not canon.is_file() or canon.is_symlink() or not canon.read_bytes().strip():
        problems.append(("R7", "AGENTS.md", "root contract missing, empty, or a symbolic link"))
    stub = VAULT_ROOT / "CLAUDE.md"
    if (stub.is_symlink() or not stub.is_file()
            or stub.read_bytes().replace(b"\r\n", b"\n") != CONTRACT_STUB):
        problems.append(("R7", "CLAUDE.md", "not exactly the one-line stub '@AGENTS.md'"))
    for extra in SECOND_CONTRACTS:
        if (VAULT_ROOT / extra).is_file() or (VAULT_ROOT / extra).is_symlink():
            problems.append(("R7", extra, "a second project instruction file beside the contract"))
    counts = {"missing_frontmatter": [], "non_ascii_files": []}
    fm_mod = _fm_module()
    for scope in ("wiki", "Calendar", "Efforts"):
        base = VAULT_ROOT / scope
        if not base.is_dir():
            continue
        for p in base.rglob("*.md"):
            rel = str(p.relative_to(VAULT_ROOT)).replace("\\", "/")
            if "/_work/" in rel.lower() or "/_archive/" in rel.lower():
                continue
            try:
                raw = p.read_bytes()
            except OSError:
                continue
            text = raw.decode("utf-8", errors="replace")
            if fm_mod.parse_frontmatter(text) is None:
                counts["missing_frontmatter"].append(rel)
    for scope in ("wiki", "Calendar", "Efforts", ".agents", "tools", "docs"):
        base = VAULT_ROOT / scope
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in (".md", ".py", ".sh", ".json", ".yaml", ".yml"):
                continue
            rel = str(p.relative_to(VAULT_ROOT)).replace("\\", "/")
            if "/_archive/" in rel.lower() or "/_work/" in rel.lower() or "/node_modules/" in rel:
                continue
            try:
                if any(b > 127 for b in p.read_bytes()):
                    counts["non_ascii_files"].append(rel)
            except OSError:
                pass
    print(f"[tree] tracked-files scanned: {len(out.decode(errors='replace').splitlines())}")
    level = "BLOCK" if strict_tree else "report"
    print(f"[tree] missing_frontmatter ({level}): {len(counts['missing_frontmatter'])}")
    print(f"[tree] non_ascii_files   ({level}): {len(counts['non_ascii_files'])}")
    if strict_tree:
        if counts["missing_frontmatter"]:
            problems.append(("R6", "tree", "missing canonical frontmatter in strict tree scan"))
        if counts["non_ascii_files"]:
            problems.append(("R4", "tree", "non-ASCII files in strict tree scan"))
    for rel in counts["missing_frontmatter"][:5]:
        print(f"[tree]   fm-missing e.g. {rel}")
    for rel in counts["non_ascii_files"][:5]:
        print(f"[tree]   non-ascii e.g. {rel}")
    for rule, path, why in problems:
        print(f"BLOCKED [{rule}] {path}: {why}")
    return 1 if problems else 0


def main():
    if "--tree" in sys.argv:
        try:
            rc = check_tree(strict_tree="--strict-tree" in sys.argv)
        except Exception as exc:  # noqa: BLE001
            print(f"precommit --tree: INTERNAL ERROR (exit 2): {exc}")
            rc = 2
        return rc
    try:
        violations = []
        check(violations)
    except Exception as exc:  # noqa: BLE001
        print(f"precommit: INTERNAL ERROR (exit 2): {exc}")
        return 2
    if violations:
        seen = set()
        for rule, path, why in violations:
            key = (rule, path, why)
            if key in seen:
                continue
            seen.add(key)
            print(f"BLOCKED [{rule}] {path}: {why}")
        print(
            f"precommit: {len(seen)} violation(s). "
            "Fix the content; never bypass the checker (AGENTS.md Before-you-act)."
        )
        return 1
    n = len(staged_files())
    print(f"precommit: ok ({n} staged file(s) checked against R1-R7)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
