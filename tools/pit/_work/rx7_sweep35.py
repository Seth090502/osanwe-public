# RX7 sweeps 3+5: non-ASCII check and secrets scan
import os
import re

ROOTS = [
    "/path/to/vault/tools/pit",
    "/path/to/vault/Efforts/osanwe-v2-overhaul/_work/fis-data",
]
files = []
for r0 in ROOTS:
    for dp, dn, fn in os.walk(r0):
        for f in fn:
            if f.endswith((".pyc", ".txt")):
                continue
            files.append(os.path.join(dp, f))
print("FILES:", len(files), flush=True)

# ---------- SWEEP 3 ----------
print("=== SWEEP 3: non-ASCII in delivered py/csv/jsonl/md/json ===", flush=True)
DELIVER_EXT = (".py", ".csv", ".jsonl", ".md", ".json")
nonascii = []
for p in files:
    if not p.endswith(DELIVER_EXT):
        continue
    data = open(p, "rb").read()
    bad = []
    pos = -1
    while True:
        idx = data.find(b"", pos + 1) if False else None
        break
    i = 0
    n = len(data)
    # fast path: ascii decode test
    try:
        data.decode("ascii")
        ok = True
    except UnicodeDecodeError as e:
        ok = False
        bad.append((e.start,))
    if not ok:
        e_start = bad[0][0]
        # enumerate up to 10 occurrences
        cnt = 0
        j = 0
        total = 0
        while j < n:
            b = data[j]
            if b > 127:
                total += 1
                if cnt < 10:
                    line = data[:j].count(b"\n") + 1
                    col = j - (data.rfind(b"\n", 0, j) + 1)
                    bad.append((line, col, b))
                    cnt += 1
            j += 1
        nonascii.append((p, bad[:10], total))
print("FILES WITH NON-ASCII:", len(nonascii), flush=True)
for p, bad, tot in nonascii:
    print(p, "total_nonascii_bytes:", tot, flush=True)
    for item in bad:
        if len(item) == 3:
            print("   line %d col %d byte 0x%02x" % item, flush=True)
print("SWEEP3 DONE", flush=True)

# ---------- SWEEP 5 ----------
print("=== SWEEP 5: secrets patterns in delivered text ===", flush=True)
SECRET_PATS = [
    rb"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}",
    rb"(?i)(secret|token|password|passwd|pwd)\s*[:=]\s*['\"]?[A-Za-z0-9_\-/+=]{12,}",
    rb"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    rb"(?i)bearer\s+[A-Za-z0-9_\-.=+/]{16,}",
    rb"(?i)gh[pousr]_[A-Za-z0-9]{30,}",
    rb"(?i)xox[baprs]-[A-Za-z0-9\-]{10,}",
    rb"(?i)AKIA[A-Z0-9]{16}",
    rb"(?i)sk-[A-Za-z0-9]{20,}",
    rb"(?i)AIza[0-9A-Za-z_\-]{30,}",
]
secrets_found = []
for p in files:
    if p.endswith(".db"):
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
print("HITS:", len(secrets_found), flush=True)
for s in secrets_found:
    print(s, flush=True)
print("SWEEP5 DONE", flush=True)
