#!/usr/bin/env python3
"""gen-ledger-views.py -- regenerate the four ledger monoliths from nodes.

The text view is HEADER + entry bodies in original order, with newlines
normalized by the parser. Text equality is not a physical-byte cutover proof.
Applying a view either leaves the file untouched or appends a new tail while
preserving every existing byte. Historical changes are refused. Legacy writer
appends can first be INGESTED as new nodes; existing nodes are never overwritten.
"""

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("OSANWE_ATOMIZE_ROOT") or Path(__file__).resolve().parent.parent)

# Reuse the parser single-source-of-truth (file name has a hyphen -> load by path).
# Load from THIS script's directory (not ROOT): the generator may run against a
# sandbox ROOT while the tool code lives in the real repo's tools/.
import importlib.util

_self = Path(__file__).resolve()
_spec = importlib.util.spec_from_file_location("atomize_ledgers", _self.parent / "atomize-ledgers.py")
al = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(al)


def split_file(text):
    """Return (header, entries) where header = everything before entry 1."""
    entries = al.split_headings(text)
    if not entries:
        return text, []
    first = entries[0][1] if entries[0][0] is not None else None
    if first is None:
        # legacy chunk precedes the first heading: it belongs to the header region
        pre_end = len(entries[0][1])
        return text[:pre_end], entries[1:]
    m = entries[0][0]
    return text[: m.start()], entries


def node_body(node_text):
    """Strip the deterministic fm_text scaffold; return just the verbatim body."""
    parts = node_text.split("---\n", 2)
    if len(parts) < 3:
        return node_text
    after = parts[2]
    if after.startswith("\n"):
        after = after[1:]
    if after.startswith("# "):
        nl = after.find("\n")
        after = after[nl + 1:] if nl >= 0 else ""
    if after.startswith("\n"):
        after = after[1:]
    return after


def regenerate(key, spec):
    """Heading ledgers: header + node bodies. Table ledgers (eod/insights):
    the original document is the SKELETON; each parsed row line is replaced by
    a marker; regeneration substitutes node bodies back into the skeleton in
    order. Return newline-normalized text, not physical file bytes."""
    p = ROOT / spec["file"]
    original = p.read_text(encoding="utf-8")

    if key in ("sessions", "decisions"):
        header, _ = split_file(original)
        chunks = [header]
        for idx_file in outdir_nodes(spec):
            chunks.append(node_body(idx_file.read_text(encoding="utf-8")))
        return original, "".join(chunks)

    rows = al.parse_eod_rows(original) if key == "eod" else al.parse_insight_rows(original)
    skeleton = original
    for n, (rid, line) in enumerate(rows):
        fname = f"{n:04d}-{al.slugify(rid, 40)}.md" if key == "eod" else f"{n:04d}-{rid[:10]}.md"
        skeleton = skeleton.replace(line + "\n", f"@@NODE:{fname}@@\n", 1)
    for n, (rid, line) in enumerate(rows):
        fname = f"{n:04d}-{al.slugify(rid, 40)}.md" if key == "eod" else f"{n:04d}-{rid[:10]}.md"
        f = ROOT / spec["node_dir"] / fname
        body = node_body(f.read_text(encoding="utf-8"))
        if not body.endswith("\n"):
            body += "\n"
        marker = f"@@NODE:{fname}@@\n"
        skeleton = skeleton.replace(marker, body, 1)
    return original, skeleton


def normalized_text(text):
    """Match Python's universal-newline reads without changing other content."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def apply_append_only(path, regenerated):
    """Append only a normalized-text extension; return physical bytes appended.

    No-op equality does not touch the file or its backup. The newest existing
    newline determines the appended tail's convention (LF for an unbroken file).
    An existing .pre-regen backup is immutable, including its line endings.
    """
    original = path.read_bytes()
    current = normalized_text(original.decode("utf-8"))
    target = normalized_text(regenerated)
    if target == current:
        return 0
    if not target.startswith(current):
        raise ValueError("regeneration changes existing ledger content; append-only apply refused")

    endings = list(re.finditer(rb"\r\n|\r|\n", original))
    newline = endings[-1].group() if endings else b"\n"
    tail = target[len(current):].encode("utf-8").replace(b"\n", newline)
    backup = path.with_suffix(".md.pre-regen")

    # O_APPEND enforces the physical write boundary; omit O_CREAT so removal
    # between the read and open fails instead of creating a replacement ledger.
    flags = os.O_WRONLY | os.O_APPEND | getattr(os, "O_BINARY", 0)
    with os.fdopen(os.open(path, flags), "ab") as stream:
        if path.read_bytes() != original:
            raise ValueError("ledger changed during regeneration; append-only apply refused")
        try:
            with backup.open("xb") as saved:
                saved.write(original)
        except FileExistsError:
            pass
        stream.write(tail)
        stream.flush()
        os.fsync(stream.fileno())
    if path.read_bytes() != original + tail:
        raise ValueError("ledger changed during append; inspect concurrent writes before retrying")
    return len(tail)


def write_new_node(path, text):
    """Exclusive creation prevents a sequence/name collision rewriting history."""
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def ingest_table_tail(key, spec, baseline_path, baseline_sha256):
    """Ingest only a table suffix after an independently preserved byte prefix.

    Current node counts and INDEX.md cannot distinguish new rows from deletion
    of the last historical node. The caller supplies the pre-append bytes and
    their expected digest; every corresponding node must still exist unchanged.
    No ledger, baseline, historical node or exact resumed node is rewritten.
    """
    if baseline_path is None and baseline_sha256 is None:
        # Preserve existing all-ledger callers when there is nothing to ingest.
        # Equality grants a no-op only, not a historical-byte boundary. Missing
        # nodes, changed rows and pending tails still need the explicit baseline.
        try:
            original, regen = regenerate(key, spec)
        except (OSError, UnicodeError, ValueError):
            pass
        else:
            if original == regen:
                return 0
    if not baseline_path or not baseline_sha256:
        raise ValueError("table ingestion requires --ingest-baseline and --ingest-baseline-sha256")
    if not re.fullmatch(r"[A-Fa-f0-9]{64}", baseline_sha256):
        raise ValueError("table ingestion baseline SHA256 must contain 64 hexadecimal characters")
    baseline = Path(baseline_path)
    if baseline.is_symlink() or not baseline.is_file():
        raise ValueError("table ingestion baseline must be an existing regular file")
    historical_bytes = baseline.read_bytes()
    if hashlib.sha256(historical_bytes).hexdigest() != baseline_sha256.lower():
        raise ValueError("table ingestion baseline SHA256 mismatch; no nodes written")
    ledger = ROOT / spec["file"]
    original_bytes = ledger.read_bytes()
    if not original_bytes.startswith(historical_bytes):
        raise ValueError("table ledger changed its pre-append physical byte prefix; no nodes written")
    original = normalized_text(original_bytes.decode("utf-8"))
    historical = normalized_text(historical_bytes.decode("utf-8"))
    tail = normalized_text(original_bytes[len(historical_bytes):].decode("utf-8"))
    parse = al.parse_eod_rows if key == "eod" else al.parse_insight_rows
    old_rows, new_rows = parse(historical), parse(tail)
    # A table node represents one exact row. Only whitespace may surround new
    # rows; headers, prose or malformed rows need an explicitly different action.
    if [line for line in tail.splitlines() if line.strip()] != [line for _, line in new_rows]:
        raise ValueError("appended table suffix contains unparsed content; no nodes written")
    if [line for _, line in parse(original)] != [line for _, line in old_rows + new_rows]:
        raise ValueError("table suffix does not preserve row boundaries; no nodes written")

    def filename(seq, rid):
        return (f"{seq:04d}-{al.slugify(rid, 40)}.md" if key == "eod"
                else f"{seq:04d}-{rid[:10]}.md")

    outdir = ROOT / spec["node_dir"]
    if outdir.is_symlink() or (hasattr(outdir, "is_junction") and outdir.is_junction()):
        raise ValueError("table node directory cannot be a link")
    existing = {path.name: path for path in outdir_nodes(spec)}
    expected_old = {filename(seq, rid): line for seq, (rid, line) in enumerate(old_rows)}
    pending = []
    for seq, (rid, line) in enumerate(new_rows, start=len(old_rows)):
        date = "2026-07-04" if key == "eod" else rid[:10]
        text = al.fm_text(spec["categories"], spec["type"], date, str(rid)) + line + "\n"
        pending.append((outdir / filename(seq, rid), text))
    expected_names = set(expected_old) | {path.name for path, _ in pending}
    if set(existing) - expected_names:
        raise ValueError("unknown table node identity or sequence collision; no nodes written")
    if set(expected_old) - set(existing):
        raise ValueError("historical table node missing from the verified baseline; no nodes written")
    observed = {}
    for name, path in existing.items():
        if path.is_symlink() or not path.is_file():
            raise ValueError("table nodes must be regular files; no nodes written")
        observed[name] = path.read_bytes()
    for name, line in expected_old.items():
        body = node_body(normalized_text(observed[name].decode("utf-8")))
        if body != line + "\n":
            raise ValueError("historical table node body differs from the verified baseline; no nodes written")
    missing_seen = False
    new_pending = []
    for path, text in pending:
        if path.name in observed:
            if missing_seen:
                raise ValueError("interrupted table suffix contains a sequence hole; no nodes written")
            if observed[path.name] != text.encode("utf-8"):
                raise ValueError("table suffix node collision or changed bytes; no nodes written")
        else:
            missing_seen = True
            new_pending.append((path, text))
    # Complete all identity/content checks before the first exclusive creation.
    # Recheck snapshots so an observed concurrent writer cannot be overwritten or
    # silently included in this plan. A late write collision still fails via 'x'.
    if (ledger.read_bytes() != original_bytes or baseline.read_bytes() != historical_bytes
            or {path.name for path in outdir_nodes(spec)} != set(existing)
            or any(existing[name].read_bytes() != data for name, data in observed.items())):
        raise ValueError("table ledger, baseline or node inventory changed during preflight; no nodes written")
    written = 0
    for path, text in new_pending:
        write_new_node(path, text)
        written += 1
    print(f"{key}: INGESTED {written} appended entr(ies) as new nodes")
    return written


def ingest_tail(key, spec, *, baseline_path=None, baseline_sha256=None):
    """If the live ledger has appended entries since last generation, parse the
    appended tail into NEW nodes (sequence numbers continue past existing ones)
    so regeneration stays a PURE APPEND and no legacy-writer entry is lost."""
    if key in ("eod", "insights"):
        return ingest_table_tail(key, spec, baseline_path, baseline_sha256)
    p = ROOT / spec["file"]
    original = p.read_text(encoding="utf-8")
    _, regen = regenerate(key, spec)
    if original == regen:
        return 0
    n = min(len(original), len(regen))
    if original[:n] != regen[:n]:
        # divergence is NOT a pure append -> refuse loudly, never guess
        raise SystemExit(
            f"{key}: ledger diverged mid-file (not append-only). "
            "Refusing to ingest; investigate manually.")
    tail = original[len(regen):] if len(original) > len(regen) else ""
    if not tail:
        return 0
    outdir = ROOT / spec["node_dir"]
    existing = [f for f in outdir.glob("*.md") if f.name != "INDEX.md"]
    seq = len(existing)
    written = 0
    if key in ("sessions", "decisions"):
        pending = []
        entries = [m for m in al.split_headings(tail) if m[0] is not None]
        # The legacy parser drops whitespace-only preambles and normalizes
        # nonempty ones. Entry bodies remain exact contiguous suffix slices;
        # derive their omitted prefix from the original tail, never stripped text.
        prefix_length = len(tail) - sum(len(body) for _, body in entries)
        preamble = tail[:prefix_length]
        for m in entries:
            _, d, title = al.node_name(key, m[0], 0)
            fname = f"{seq:04d}-{d}-{al.slugify(title, 50)}.md"
            body = preamble + m[1]
            preamble = ""
            text = al.fm_text(spec["categories"], spec["type"], d, f"{d} -- {title}") + body
            pending.append((outdir / fname, text))
            seq += 1
        if preamble or "".join(node_body(text) for _, text in pending) != tail:
            raise SystemExit(f"{key}: appended text cannot round-trip into heading nodes; no nodes written")
        if any(path.exists() for path, _ in pending):
            raise FileExistsError("new ledger node collision; no nodes written")
        for path, text in pending:
            write_new_node(path, text)
            written += 1
    print(f"{key}: INGESTED {written} appended entr(ies) as new nodes")
    return written


def outdir_nodes(spec):
    d = ROOT / spec["node_dir"]
    return sorted(f for f in d.glob("*.md") if f.name != "INDEX.md")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", choices=sorted(al.LEDGERS))
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true",
                      help="read-only newline-normalized text comparison (also the default)")
    mode.add_argument("--apply", action="store_true",
                      help="append only new view content, preserving all existing ledger bytes")
    ap.add_argument("--ingest", action="store_true",
                    help="before regenerating, parse appended ledger tails into new nodes (pure-append guarantee)")
    ap.add_argument("--ingest-baseline", metavar="PATH",
                    help="table ingestion only: independently preserved pre-append ledger bytes")
    ap.add_argument("--ingest-baseline-sha256", metavar="HEX",
                    help="table ingestion only: expected SHA256 of the entire pre-append baseline")
    args = ap.parse_args(argv)
    if args.check and args.ingest:
        ap.error("--check is read-only and cannot be combined with --ingest")

    ok_all = True
    for key, spec in al.LEDGERS.items():
        if args.ledger and key != args.ledger:
            continue
        if not (ROOT / spec["node_dir"]).is_dir():
            print(f"{key}: no node dir yet -- run atomize-ledgers.py first")
            continue
        try:
            if args.ingest:
                ingest_tail(key, spec, baseline_path=args.ingest_baseline,
                            baseline_sha256=args.ingest_baseline_sha256)
            original, regen = regenerate(key, spec)
            same = original == regen
            verdict = ("TEXT-EQUIVALENT (newline-normalized; not a byte-equality proof)"
                       if same else f"TEXT-DIFFERS ({len(regen)} vs {len(original)} characters)")
            print(f"{key}: {verdict}")
            if args.apply:
                appended = apply_append_only(ROOT / spec["file"], regen)
                print(f"{key}: appended {appended} bytes; existing physical bytes preserved")
                same = True
            ok_all = ok_all and same
        except (OSError, UnicodeError, ValueError) as exc:
            print(f"{key}: REFUSED: {exc}", file=sys.stderr)
            ok_all = False
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
