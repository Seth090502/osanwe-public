#!/usr/bin/env python3
"""Failing-case-per-rule tests for the OSANWE v2 pre-commit cage.

Runs tools/precommit.py against a THROWAWAY scratch git repo (never plants
fixtures in the live vault). Each rule gets a FAILING case (expect rc=1 with the
rule tag) and a PASSING twin (expect rc=0). A bar that cannot fail is not a bar.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent

CANONICAL_FM = (
    "---\n"
    "aliases: []\n"
    "categories: [wiki]\n"
    "status: active\n"
    "created: 2026-08-23\n"
    "updated: 2026-08-23\n"
    "tags: []\n"
    "related: []\n"
    "---\n\n"
)


def sh(args, cwd, env=None):
    r = subprocess.run(args, cwd=str(cwd), capture_output=True, env=env)
    return r.returncode, r.stdout.decode(errors="replace"), r.stderr.decode(errors="replace")


def mk_scratch():
    """Scratch repo carrying a copy of the cage + the real frontmatter checker."""
    tmp = Path(tempfile.mkdtemp(prefix="osanwe-precommit-test-"))
    sh(["git", "init", "-q"], cwd=tmp)
    sh(["git", "config", "user.email", "test@local"], cwd=tmp)
    sh(["git", "config", "user.name", "test"], cwd=tmp)
    sh(["git", "config", "core.autocrlf", "false"], cwd=tmp)
    shutil.copytree(VAULT / ".githooks", tmp / ".githooks")
    # STRICT is RUNTIME state of the live vault, not cage code -- a scratch repo must
    # start dormant or every non-R3 case inherits an Atlas lock. Cases that exercise
    # R3 plant it explicitly via _r3_setup().
    strict = tmp / ".githooks" / "STRICT"
    if strict.exists():
        strict.unlink()
    (tmp / "tools").mkdir()
    shutil.copy(VAULT / "tools" / "precommit.py", tmp / "tools" / "precommit.py")
    shutil.copy(VAULT / "tools" / "frontmatter-check.py", tmp / "tools" / "frontmatter-check.py")
    (tmp / "AGENTS.md").write_bytes(b"# Complete test contract\n")
    (tmp / "CLAUDE.md").write_bytes(b"@AGENTS.md\n")
    sh(["git", "add", "-A"], cwd=tmp)
    sh(["git", "commit", "-q", "-m", "cage seed"], cwd=tmp)
    return tmp


def run_check(root, extra_env=None, args=()):
    env = dict(os.environ)
    env["OSANWE_VAULT_ROOT"] = str(root)
    env.pop("OSANWE_ATLAS_FM_OK", None)
    if extra_env:
        env.update(extra_env)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return sh([sys.executable, str(root / "tools" / "precommit.py")] + list(args), cwd=root, env=env)


def stage(root, relpath, content, binary=False):
    p = root / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    mode = "wb" if binary else "w"
    kwargs = {} if binary else {"encoding": "utf-8", "newline": ""}
    with open(p, mode, **kwargs) as f:
        f.write(content)
    sh(["git", "add", "--", relpath], cwd=root)
    return p


def commit_seed(root, relpath, content):
    stage(root, relpath, content)
    sh(["git", "commit", "-q", "-m", f"seed {relpath}"], cwd=root)


# ---------------------------------------------------------------- R1 protected paths

def t_r1_blocked(tmp):
    stage(tmp, "private/x.txt", "secret")
    rc, out, _ = run_check(tmp)
    return rc == 1 and "[R1]" in out, f"rc={rc} out={out[:200]}"


def t_r1_passes(tmp):
    stage(tmp, "wiki/r1-ok.md", CANONICAL_FM + "clean\n")
    rc, out, _ = run_check(tmp)
    return rc == 0, f"rc={rc} out={out[:200]}"


# ---------------------------------------------------------------- R2 append-only ledgers

LEDGER = "Calendar/decisions/sessions-log.md"


def t_r2_rewrite_blocked(tmp):
    commit_seed(tmp, LEDGER, "entry-one\n")
    stage(tmp, LEDGER, "tampered\n")  # existing bytes NOT preserved
    rc, out, _ = run_check(tmp)
    return rc == 1 and "[R2]" in out, f"rc={rc} out={out[:200]}"


def t_r2_delete_blocked(tmp):
    commit_seed(tmp, "Calendar/decisions/execute-or-decline.md", "row\n")
    sh(["git", "rm", "-q", "--", "Calendar/decisions/execute-or-decline.md"], cwd=tmp)
    rc, out, _ = run_check(tmp)
    return rc == 1 and "[R2]" in out, f"rc={rc} out={out[:200]}"


def t_r2_append_passes(tmp):
    commit_seed(tmp, "wiki/insight-stream.md", "insight-one\n")
    stage(tmp, "wiki/insight-stream.md", "insight-one\ninsight-two\n")  # strict prefix kept
    rc, out, _ = run_check(tmp)
    return rc == 0, f"rc={rc} out={out[:200]}"


# ---------------------------------------------------------------- R3 Atlas while STRICT

def _r3_setup(tmp):
    (tmp / ".githooks" / "STRICT").write_text("", encoding="utf-8")
    commit_seed(tmp, "Atlas/concepts/note.md", CANONICAL_FM + "human body\n")


def t_r3_body_blocked(tmp):
    _r3_setup(tmp)
    stage(tmp, "Atlas/concepts/note.md", CANONICAL_FM + "agent rewrote body\n")
    rc, out, _ = run_check(tmp)
    return rc == 1 and "[R3]" in out, f"rc={rc} out={out[:200]}"


def t_r3_fm_needs_optin(tmp):
    _r3_setup(tmp)
    stage(tmp, "Atlas/concepts/note.md",
          CANONICAL_FM.replace("updated: 2026-08-23", "updated: 2026-08-24") + "human body\n")
    rc, out, _ = run_check(tmp)
    ok_block = rc == 1 and "[R3]" in out
    rc2, _, _ = run_check(tmp, {"OSANWE_ATLAS_FM_OK": "1"})
    log_ok = (tmp / ".claude" / "state").exists() and any(
        p.name.startswith("bypasses-") for p in (tmp / ".claude" / "state").glob("*.log"))
    return ok_block and rc2 == 0 and log_ok, \
        f"block rc={rc}, optin rc={rc2}, log={log_ok}"


def t_r3_dormant_without_strict(tmp):
    stage(tmp, "Atlas/sources/new-note.md", CANONICAL_FM + "allowed once STRICT is gone\n")
    rc, out, _ = run_check(tmp)
    return rc == 0, f"rc={rc} out={out[:200]}"

# ---------------------------------------------------------------- R4 ascii added lines

def t_r4_nonascii_blocked(tmp):
    # chr(0x2014) keeps the fixture non-ASCII no matter what any editor/transport does
    stage(tmp, "wiki/r4.md", CANONICAL_FM + "em-dash " + chr(0x2014) + " line\n")
    rc, out, _ = run_check(tmp)
    return rc == 1 and "[R4]" in out, f"rc={rc} out={out[:200]}"


def t_r4_legacy_untouched_passes(tmp):
    # legacy non-ASCII already in HEAD must NOT block an unrelated append
    commit_seed(tmp, "wiki/legacy.md", CANONICAL_FM + "legacy em-dash " + chr(0x2014) + "\n")
    stage(tmp, "wiki/legacy.md", CANONICAL_FM + "legacy em-dash " + chr(0x2014) + "\nnew ascii line\n")
    rc, out, _ = run_check(tmp)
    return rc == 0, f"rc={rc} out={out[:200]}"


# ---------------------------------------------------------------- R5 domain bans

def t_r5_domain_field_blocked(tmp):
    stage(tmp, "wiki/r5.md",
          CANONICAL_FM.replace("tags: []", 'domain: investing'))
    rc, out, _ = run_check(tmp)
    blocked_field = rc == 1 and "[R5]" in out
    stage(tmp, "wiki/r5b.md",
          CANONICAL_FM.replace("tags: []", "tags:\n  - domain/investing"))
    rc2, out2, _ = run_check(tmp)
    blocked_tag = rc2 == 1 and "[R5]" in out2
    return blocked_field and blocked_tag, f"field rc={rc}, tag rc={rc2}"


# ---------------------------------------------------------------- R6 frontmatter on new vault md

def t_r6_missing_fm_blocked(tmp):
    stage(tmp, "efforts/no-fm.md", "just a body, no frontmatter\n")
    rc, out, _ = run_check(tmp)
    return rc == 1 and "[R6]" in out, f"rc={rc} out={out[:200]}"


def t_r6_valid_fm_passes(tmp):
    stage(tmp, "calendar/daily-ok.md", CANONICAL_FM + "# ok\n")
    rc, out, _ = run_check(tmp)
    return rc == 0, f"rc={rc} out={out[:200]}"


def t_r6_work_scratch_exempt(tmp):
    stage(tmp, "efforts/some-effort/_work/scratch-note.md", "# raw evidence, no frontmatter\n")
    rc, out, _ = run_check(tmp)
    return rc == 0, f"rc={rc} out={out[:200]}"

# ---------------------------------------------------------------- R7 the contract and its stub


def t_r7_claude_md_mirror_blocked(tmp):
    # A full copy in CLAUDE.md is a second set of rules that can drift from AGENTS.md.
    stage(tmp, "CLAUDE.md", "# Complete test contract\n")
    rc, out, _ = run_check(tmp)
    return rc == 1 and "[R7]" in out, f"rc={rc} out={out[:200]}"


def t_r7_unstaged_stub_edit_blocked(tmp):
    # Not staged, but a live session loads the working copy.
    (tmp / "CLAUDE.md").write_text("@AGENTS.md\nOne more rule.\n", encoding="ascii")
    stage(tmp, "wiki/note.md", "---\ncategories: [x]\n---\n\nbody\n")
    rc, out, _ = run_check(tmp)
    return rc == 1 and "[R7]" in out, f"rc={rc} out={out[:200]}"


def t_r7_stub_with_extra_rule_blocked(tmp):
    stage(tmp, "CLAUDE.md", "@AGENTS.md\nOne more rule.\n")
    rc, out, _ = run_check(tmp)
    return rc == 1 and "[R7]" in out, f"rc={rc} out={out[:200]}"


def t_r7_deleted_stub_blocked(tmp):
    # Without the stub a root CLAUDE.local.md stops Claude Code reading AGENTS.md.
    sh(["git", "rm", "-q", "--", "CLAUDE.md"], cwd=tmp)
    rc, out, _ = run_check(tmp)
    return rc == 1 and "[R7]" in out, f"rc={rc} out={out[:200]}"


def t_r7_nested_claude_md_blocked(tmp):
    stage(tmp, ".claude/CLAUDE.md", "# nested second contract\n")
    rc, out, _ = run_check(tmp)
    return rc == 1 and "[R7]" in out, f"rc={rc} out={out[:200]}"


def t_r7_nested_symlink_entry_blocked(tmp):
    # A symlink-mode index entry is not a regular file, but it is still a second contract.
    stage(tmp, "pointer-target.txt", "AGENTS.md\n")
    _, object_id, _ = sh(["git", "hash-object", "pointer-target.txt"], cwd=tmp)
    sh(["git", "update-index", "--add", "--cacheinfo",
        "120000," + object_id.strip() + ",.claude/CLAUDE.md"], cwd=tmp)
    rc, out, _ = run_check(tmp)
    return rc == 1 and "[R7]" in out, f"rc={rc} out={out[:200]}"


def t_r7_unstaged_contract_deletion_blocked(tmp):
    # The index still holds AGENTS.md, but a live session would load nothing.
    (tmp / "AGENTS.md").unlink()
    stage(tmp, "wiki/note.md", "---\ncategories: [x]\n---\n\nbody\n")
    rc, out, _ = run_check(tmp)
    return rc == 1 and "[R7]" in out, f"rc={rc} out={out[:200]}"


def t_r7_tree_accepts_crlf_stub(tmp):
    # One line-ending rule everywhere: a CRLF working copy of the stub still imports the contract.
    _tree_seed(tmp)
    (tmp / "CLAUDE.md").write_bytes(b"@AGENTS.md\r\n")
    rc, out, _ = run_check(tmp, args=("--tree", "--strict-tree"))
    return rc == 0 and "[R7]" not in out, f"rc={rc} out={out[-250:]}"


def t_r7_contract_with_stub_passes(tmp):
    stage(tmp, "AGENTS.md", "# Updated complete contract\n")
    rc, out, _ = run_check(tmp)
    return rc == 0, f"rc={rc} out={out[:200]}"


def t_r7_deleted_copy_blocked(tmp):
    sh(["git", "rm", "-q", "--", "AGENTS.md"], cwd=tmp)
    rc, out, _ = run_check(tmp)
    return rc == 1 and "[R7]" in out, f"rc={rc} out={out[:200]}"


def t_r7_empty_contracts_blocked(tmp):
    stage(tmp, "AGENTS.md", "")
    rc, out, _ = run_check(tmp)
    return rc == 1 and "[R7]" in out, f"rc={rc} out={out[:200]}"


def t_r7_normalized_index_bytes_pass(tmp):
    stage(tmp, ".gitattributes", "*.md text eol=lf\n")
    stage(tmp, "AGENTS.md", b"# Normalized contract\r\n", binary=True)
    rc, out, _ = run_check(tmp)
    return rc == 0, f"rc={rc} out={out[:200]}"


def t_r7_symlink_index_is_not_a_complete_contract(tmp):
    # No OS symlink privilege is needed: stage matching symlink-mode objects.
    # Worktree documents remain normal and matching, so worktree parity alone
    # would miss this attempted commit.
    stage(tmp, "pointer-target.txt", "other-contract.md\n")
    _, object_id, _ = sh(["git", "hash-object", "pointer-target.txt"], cwd=tmp)
    sh(["git", "update-index", "--add", "--cacheinfo",
        "120000," + object_id.strip() + ",AGENTS.md"], cwd=tmp)
    rc, out, _ = run_check(tmp)
    return rc == 1 and "[R7]" in out, f"rc={rc} out={out[:200]}"


def _tree_seed(tmp):
    for name in (LEDGER, "Calendar/decisions/decision-log.md",
                 "Calendar/decisions/execute-or-decline.md", "wiki/insight-stream.md"):
        p = tmp / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(CANONICAL_FM + "# Seed\n", encoding="ascii")


def t_strict_tree_missing_fm_blocks(tmp):
    _tree_seed(tmp)
    (tmp / "wiki/no-fm.md").write_text("# Missing frontmatter\n", encoding="ascii")
    report_rc, _, _ = run_check(tmp, args=("--tree",))
    rc, out, _ = run_check(tmp, args=("--tree", "--strict-tree"))
    return report_rc == 0 and rc == 1 and "[R6]" in out, f"report rc={report_rc}; strict rc={rc} out={out[-250:]}"


def t_strict_tree_nonascii_blocks(tmp):
    _tree_seed(tmp)
    (tmp / "tools/nonascii.py").write_text("# " + chr(0x2014), encoding="utf-8")
    report_rc, _, _ = run_check(tmp, args=("--tree",))
    rc, out, _ = run_check(tmp, args=("--tree", "--strict-tree"))
    return report_rc == 0 and rc == 1 and "[R4]" in out, f"report rc={report_rc}; strict rc={rc} out={out[-250:]}"


# ---------------------------------------------------------------- harness

CASES = [
    ("R1 protected-path write is blocked", t_r1_blocked),
    ("R1 clean wiki write passes", t_r1_passes),
    ("R2 ledger rewrite (non-append) is blocked", t_r2_rewrite_blocked),
    ("R2 ledger delete is blocked", t_r2_delete_blocked),
    ("R2 pure append passes", t_r2_append_passes),
    ("R3 Atlas body rewrite under STRICT is blocked", t_r3_body_blocked),
    ("R3 Atlas frontmatter repair needs opt-in env and is logged", t_r3_fm_needs_optin),
    ("R3 dormant once STRICT removed", t_r3_dormant_without_strict),
    ("R4 non-ASCII added line is blocked", t_r4_nonascii_blocked),
    ("R4 legacy untouched non-ASCII does not block", t_r4_legacy_untouched_passes),
    ("R5 domain field and namespaced tags are blocked", t_r5_domain_field_blocked),
    ("R6 new vault md without canonical frontmatter is blocked", t_r6_missing_fm_blocked),
    ("R6 new vault md with valid frontmatter passes", t_r6_valid_fm_passes),
    ("R6 _work/ scratch md exempt by name", t_r6_work_scratch_exempt),
    ("R7 a staged CLAUDE.md mirror blocks", t_r7_claude_md_mirror_blocked),
    ("R7 an unstaged edit to the stub blocks", t_r7_unstaged_stub_edit_blocked),
    ("R7 a stub with an extra rule blocks", t_r7_stub_with_extra_rule_blocked),
    ("R7 deleting the stub blocks", t_r7_deleted_stub_blocked),
    ("R7 a staged .claude/CLAUDE.md blocks", t_r7_nested_claude_md_blocked),
    ("R7 a symlink-mode .claude/CLAUDE.md entry blocks", t_r7_nested_symlink_entry_blocked),
    ("R7 an unstaged deletion of AGENTS.md blocks", t_r7_unstaged_contract_deletion_blocked),
    ("R7 --tree accepts a CRLF stub", t_r7_tree_accepts_crlf_stub),
    ("R7 AGENTS.md with the stub passes", t_r7_contract_with_stub_passes),
    ("R7 deleting the root contract blocks", t_r7_deleted_copy_blocked),
    ("R7 an empty root contract blocks", t_r7_empty_contracts_blocked),
    ("R7 LF-normalized index bytes pass", t_r7_normalized_index_bytes_pass),
    ("R7 a symlink-mode index entry is not a contract", t_r7_symlink_index_is_not_a_complete_contract),
    ("strict tree missing frontmatter blocks", t_strict_tree_missing_fm_blocks),
    ("strict tree non-ASCII blocks", t_strict_tree_nonascii_blocks),
]


def main():
    failures = []
    for name, fn in CASES:
        tmp = mk_scratch()
        try:
            ok, detail = fn(tmp)
            print(("PASS  " if ok else "FAIL  ") + name + ("  | " + detail if not ok else ""))
            if not ok:
                failures.append(name)
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL  {name}  | exception: {exc}")
            failures.append(name)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    total, bad = len(CASES), len(failures)
    print(f"\ntest-precommit: {total - bad}/{total} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
