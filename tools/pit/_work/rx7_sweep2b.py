# RX7 sweep 2b: pilot row counts vs network cap + cache/remnant check
import os
import re
import json

print("=== SWEEP 2b: pilot rows vs cap ===", flush=True)
base = "/path/to/vault/Efforts/osanwe-v2-overhaul/_work/fis-data/"
for name in ["edgar-pit-pilot.jsonl", "edgar-pit-enriched.jsonl"]:
    fp = base + name
    data = open(fp, "rb").read()
    print(name, "bytes:", len(data), flush=True)
    lines = [l for l in data.split(b"\n") if l.strip()]
    print("  rows:", len(lines), flush=True)
    tickers = set()
    ciks = set()
    for l in lines:
        r = json.loads(l)

        def dig(d):
            for k, v in d.items():
                kl = k.lower()
                if kl == "ticker":
                    tickers.add(str(v).upper())
                if kl == "cik":
                    ciks.add(str(v))
                if isinstance(v, dict):
                    dig(v)
                if isinstance(v, list):
                    for x in v:
                        if isinstance(x, dict):
                            dig(x)

        dig(r)
    print("  distinct tickers:", sorted(tickers), flush=True)
    print("  distinct ciks:", sorted(ciks), flush=True)

print("--- cache/remnant filenames under scope ---", flush=True)
found = False
for r0 in ["/path/to/vault/tools/pit", base.rstrip("/")]:
    for dp, dn, fn in os.walk(r0):
        for d in dn:
            if "cache" in d.lower():
                print("DIR:", os.path.join(dp, d), flush=True)
                found = True
        for f in fn:
            if re.search(r"(cache|fetch|download|\.tmp$|\.part$)", f, re.I):
                print("FILE:", os.path.join(dp, f), flush=True)
                found = True
if not found:
    print("(none)", flush=True)
print("SWEEP2B DONE", flush=True)
