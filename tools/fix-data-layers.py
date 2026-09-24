"""Fix Finding 1: append missing '## Data layers (GENERATED 2026-08-24)'
sections to entity notes in wiki/entities/tickers/.

For each ticker .md lacking a '## Data layers' section, resolve links:
  - wiki/investing/benchmarks/<lower>-benchmark.md and <lower>-data-annex.md
    (crypto tickers try <lower>-usd-*; ADRs try the 5-char yfinance suffix
     when the plain lowercase stem does not resolve)
  - Efforts/osanwe-v2-overhaul/_work/wave*-<ticker>-analysis.md
  - wiki/investing/filings/<TICKER>/<TICKER>-xbrl.json
Only lines whose target resolves on disk are emitted. Idempotent: files that
already carry the section are skipped. ASCII only.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TICKERS = ROOT / "wiki" / "entities" / "tickers"
BENCH = ROOT / "wiki" / "investing" / "benchmarks"
FILINGS = ROOT / "wiki" / "investing" / "filings"
WORK = ROOT / "Efforts" / "osanwe-v2-overhaul" / "_work"

STAMP = "GENERATED 2026-08-24"


def find_bench_pair(ticker):
    lower = ticker.lower()
    direct = BENCH / f"{lower}-benchmark.md"
    if direct.exists():
        annex = BENCH / f"{lower}-data-annex.md"
        return direct, (annex if annex.exists() else None)
    # ADR fallback: scan for benchmarks whose stem starts with the ticker
    hits = sorted(
        p for p in BENCH.glob(f"{lower}*-benchmark.md")
        if not p.name.startswith(lower + "-usd")
    )
    if len(hits) == 1:
        stem = hits[0].name[: -len("-benchmark.md")]
        annex = BENCH / f"{stem}-data-annex.md"
        return hits[0], (annex if annex.exists() else None)
    return None, None


def wave_file(ticker):
    pat = f"-{ticker}-analysis.md"
    hits = sorted(p for p in WORK.glob(f"wave*{pat}"))
    if not hits:
        return None
    return max(hits, key=lambda p: p.stat().st_mtime)


def xbrl_file(ticker):
    d = FILINGS / ticker
    if not d.is_dir():
        return None
    for name in (f"{ticker}-xbrl.json", f"{ticker}-xbrl-extended.json",
                 f"{ticker}-filings.json"):
        p = d / name
        if p.exists():
            return p
    return None


def rel_posix(p):
    return p.resolve().relative_to(ROOT).as_posix()


def build_section(ticker):
    lines = [f"## Data layers ({STAMP})", ""]
    bench, annex = find_bench_pair(ticker)
    if bench:
        slug = bench.name[: -len(".md")]
        lines.append(f"- Benchmark profile: [[{slug}]]")
    if annex:
        slug = annex.name[: -len(".md")]
        lines.append(f"- Data annex: [[{slug}]]")
    wf = wave_file(ticker)
    if wf:
        slug = wf.name[: -len(".md")]
        fm = wf.read_text(encoding="utf-8")[:800]
        m = __import__("re").search(r"^rating:\s*(\S+)", fm, __import__("re").M)
        r = m.group(1) if m else "?"
        m = __import__("re").search(r"^confidence:\s*(\d+)", fm, __import__("re").M)
        c = m.group(1) if m else "?"
        lines.append(
            f"- Latest wave analysis: [[{slug}]] (rating: {r}, confidence: {c})")
    xf = xbrl_file(ticker)
    if xf:
        lines.append(f"- EDGAR XBRL: {rel_posix(xf)}")
    if len(lines) == 2:
        return None
    return "\n".join(lines) + "\n"


def main():
    fixed = []
    skipped = []
    for md in sorted(TICKERS.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        if "## Data layers" in text:
            continue
        sec = build_section(md.stem.upper())
        if sec is None:
            skipped.append(md.name)
            continue
        if not text.endswith("\n"):
            text += "\n"
        md.write_text(text + "\n" + sec, encoding="utf-8", newline="\n")
        fixed.append((md.name, sec.strip().splitlines()[2:]))
    print(f"appended sections: {len(fixed)}")
    for name, body in fixed:
        print(" ", name)
        for ln in body:
            print("   ", ln)
    if skipped:
        print("no resolving layers, left untouched:", ", ".join(skipped))


if __name__ == "__main__":
    main()
