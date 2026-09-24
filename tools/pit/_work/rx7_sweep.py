# RX7 absence-of-future-information sweep. Scanner only; writes nothing else.
import os
import re
import json

ROOTS = [
    "/path/to/vault/tools/pit",
    "/path/to/vault/Efforts/osanwe-v2-overhaul/_work/fis-data",
]

files = []
for r in ROOTS:
    for dp, dn, fn in os.walk(r):
        for f in fn:
            if f.endswith((".pyc", ".txt")):
                continue
            files.append(os.path.join(dp, f))

print("TOTAL FILES:", len(files))
for p in sorted(files):
    print("  ", p)

# ---------- SWEEP 1: future dates ----------
print()
print("=== SWEEP 1: date strings > 2026-08-25 ===")
REF = (2026, 8, 25)
ISO = re.compile(rb"\b(20\d{2})[-/.](0[1-9]|1[0-2])[-/.](0[1-9]|[12]\d|3[01])\b")
US = re.compile(rb"\b(0?[1-9]|1[0-2])/(0?[1-9]|[12]\d|3[01])/(20\d{2})\b")
future = []
for p in files:
    data = open(p, "rb").read()
    if not data or b"\x00" in data[:4096]:
        continue
    for rx in (ISO, US):
        for m in rx.finditer(data):
            if rx is ISO:
                y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            else:
                mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            try:
                import datetime as _dt
                dt = _dt.date(y, mo, d)
            except ValueError:
                continue
            if dt > _dt.date(*REF):
                line = data[: m.start()].count(b"\n") + 1
                ctx = data[max(0, m.start() - 50) : m.end() + 30].decode("ascii", "replace")
                future.append("%s:%d :: %s :: %r" % (p, line, dt.isoformat(), ctx))
print("HITS:", len(future))
for h in future:
    print(h)

# ---------- SWEEP 2: network artifacts ----------
print()
print("=== SWEEP 2: network-use artifacts / pilot cap check ===")
NET_PATS = [
    rb"requests\.(get|post|put|head)",
    rb"urllib\.request",
    rb"httpx",
    rb"aiohttp",
    rb"\bcurl\b",
    rb"\bwget\b",
    rb"sec-api",
    rb"edgar[_-]?(api|client)",
    rb"api[_-]?key",
    rb"\.cache[/\\]",
    rb"yfinance",
]
for p in files:
    data = open(p, "rb").read()
    hits = set()
    for pat in NET_PATS:
        rx = re.compile(pat, re.I)
        for m in rx.finditer(data):
            line = data[: m.start()].count(b"\n") + 1
            hits.add((pat.decode(), line))
    if hits:
        print(p)
        for h in sorted(hits):
            print("   ", h)

print("--- pilot row counts (cap <=10 requests; expect 5 tickers => 5 requests) ---")
base = "/path/to/vault/Efforts/osanwe-v2-overhaul/_work/fis-data/"
for name in ["edgar-pit-pilot.jsonl", "edgar-pit-enriched.jsonl"]:
    fp = base + name
    rows = [json.loads(l) for l in open(fp, encoding="utf-8") if l.strip()]
    print(name, "rows:", len(rows))
    tickers = set()
    ciks = set()
    for r in rows:

        def dig(d):
            for k, v in d.items():
                kl = k.lower()
                if kl == "ticker":
                    tickers.add(str(v).upper())
                if kl == "cik":
                    ciks.add(str(v))
                if isinstance(v, dict):
                    dig(v)

        dig(r)
    print("   distinct tickers:", sorted(tickers))
    print("   distinct ciks:", sorted(ciks))

print("--- cache/fetch remnant filenames ---")
found_remnant = False
for r in ROOTS:
    for dp, dn, fn in os.walk(r):
        for d in dn:
            if "cache" in d.lower():
                print("DIR:", os.path.join(dp, d))
                found_remnant = True
        for f in fn:
            if re.search(r"(cache|fetch|download)", f, re.I):
                print("FILE:", os.path.join(dp, f))
                found_remnant = True
if not found_remnant:
    print("(none)")

# ---------- SWEEP 3: non-ASCII ----------
print()
print("=== SWEEP 3: non-ASCII bytes in delivered py/csv/jsonl/md ===")
DELIVER_EXT = (".py", ".csv", ".jsonl", ".md", ".json")
nonascii = []
for p in files:
    if p.endswith(".pyc"):
        continue
    if not p.endswith(DELIVER_EXT):
        continue
    data = open(p, "rb").read()
    bad = []
    i = 0
    for i, b in enumerate(data):
        if b > 127:
            line = data[:i].count(b"\n") + 1
            col = i - (data.rfind(b"\n", 0, i) + 1)
            bad.append((line, col, b))
    if bad:
        nonascii.append((p, bad[:10], len(bad)))
print("FILES WITH NON-ASCII:", len(nonascii))
for p, bad, n in nonascii:
    print(p, "total_nonascii_bytes:", n)
    for line, col, byte in bad:
        print("   line %d col %d byte 0x%02x" % (line, col, byte))

# ---------- SWEEP 5: secrets ----------
print()
print("=== SWEEP 5: secrets scan (all delivered text) ===")
SECRET_PATS = [
    rb"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}",
    rb"(?i)(secret|token|password|passwd|pwd)\s*[:=]\s*['\"]?[A-Za-z0-9_\-/+=]{12,}",
    rb"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    rb"(?i)bearer\s+[A-Za-z0-9_\-\.=+/]{16,}",
    rb"(?i)gh[pousr]_[A-Za-z0-9]{30,}",
    rb"(?i)xox[baprs]-[A-Za-z0-9\-]{10,}",
    rb"(?i)AKIA[A-Z0-9]{16}",
    rb"(?i)sk-[A-Za-z0-9]{20,}",
    rb"(?i)AIza[0-9A-Za-z_\-]{30,}",
    rb"(?i)ey[J][A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}",  # jwt-ish
]
secrets_found = []
for p in files:
    if p.endswith(".pyc"):
        continue
    data = open(p, "rb").read()
    if b"\x00" in data[:4096]:
        continue
    for pat in SECRET_PATS:
        rx = re.compile(pat)
        for m in rx.finditer(data):
            line = data[: m.start()].count(b"\n") + 1
            frag = m.group(0)[:60].decode("ascii", "replace")
            secrets_found.append("%s:%d :: %s" % (p, line, frag))
print("HITS:", len(secrets_found))
for s in secrets_found:
    print(s)
