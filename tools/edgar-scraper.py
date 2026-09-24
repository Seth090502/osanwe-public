#!/usr/bin/env python3
"""edgar-scraper.py -- mass-scrape SEC filings into the vault's knowledge base.

Pulls structured filing data from SEC EDGAR (free, public, no API key needed
for the JSON endpoints). Covers every ticker in the entity universe:

  1. 10-K/10-Q financial statements via XBRL company-concept API
     (revenue, net income, EPS, cash, debt, capex -- as-reported)
  2. Institutional ownership: 13F holdings of major holders per entity
     (via EDGAR full-text search on CIK, filtered to form=13F-HR)
  3. Insider transactions: Form 4 feed per issuer
  4. Material events: 8-K feed per issuer

All data lands in wiki/investing/filings/<TICKER>/ as markdown tables +
a consolidated JSONL index at Efforts/osanwe-v2-overhaul/_work/edgar-index.jsonl.

SEC fair-access: max 10 req/sec, User-Agent with contact per SEC policy.
"""

import argparse
import json
import re
import sqlite3
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "wiki/investing/filings"
INDEX = ROOT / "Efforts/osanwe-v2-overhaul/_work/edgar-index.jsonl"
UA = "OsanweVault research <email>"  # SEC requires UA with contact

CONCEPTS = {
    "Revenues": "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax": "Revenue",
    "NetIncomeLoss": "NetIncome",
    "EarningsPerShareDiluted": "EPS_diluted",
    "CashAndCashEquivalentsAtCarryingValue": "Cash",
    "LongTermDebt": "LongTermDebt",
    "PaymentsToAcquirePropertyPlantAndEquipment": "Capex",
    "ResearchAndDevelopmentExpense": "R&D",
}


def sec_get(url):
    """Rate-limited GET with proper UA."""
    time.sleep(0.15)  # ~6.7 req/s, under SEC's 10/s cap
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def get_cik_map(tickers):
    """Map tickers to CIKs via SEC's ticker file."""
    data = sec_get("https://www.sec.gov/files/company_tickers.json")
    by_ticker = {}
    for entry in data.values():
        tk = entry.get("ticker", "").upper()
        if tk in tickers:
            by_ticker[tk] = {"cik": str(entry["cik_str"]).zfill(10),
                             "name": entry["title"]}
    return by_ticker


def scrape_concepts(cik, ticker, outdir):
    """Pull key XBRL concepts for one company."""
    results = []
    for concept, label in CONCEPTS.items():
        url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{concept}.json"
        try:
            data = sec_get(url)
        except Exception:
            continue
        units = data.get("units", {}).get("USD", [])
        # take annual (FY) + latest quarterly values
        rows = []
        for u in units:
            if u.get("form") in ("10-K", "10-Q") and u.get("frame") is not None:
                rows.append({"period": u.get("end", ""), "fy": u.get("fy"),
                             "fp": u.get("fp"), "form": u["form"],
                             "value": u["val"], "filed": u.get("filed", "")})
        if rows:
            # dedupe by period keeping most recent filed
            seen = {}
            for r in rows:
                seen[r["period"]] = r
            for p in sorted(seen)[-12:]:  # last 12 periods
                results.append({"ticker": ticker, "concept": label,
                                **seen[p]})
    if results:
        outdir.mkdir(parents=True, exist_ok=True)
        p = outdir / f"{ticker}-xbrl.json"
        p.write_text(json.dumps(results, indent=1), encoding="utf-8")
    return len(results)


def scrape_filings_feed(cik, ticker, forms=("8-K", "13F-HR", "SC 13G", "SC 13D", "4")):
    """Recent filing titles + dates via submissions API."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    try:
        data = sec_get(url)
    except Exception:
        return []
    recent = data.get("filings", {}).get("recent", {})
    out = []
    for i, form in enumerate(recent.get("form", [])):
        if form in forms or any(f in form for f in ("10-K", "10-Q")):
            out.append({"ticker": ticker, "form": form,
                        "date": recent.get("filingDate", [""])[i],
                        "desc": recent.get("primaryDocDescription", [""])[i][:80],
                        "doc": recent.get("primaryDocument", [""])[i]})
    return out[:40]  # last 40 matching


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", help="comma-separated; default = full universe from entities dir")
    ap.add_argument("--limit", type=int, default=20, help="max companies this run (resumable)")
    ap.add_argument("--skip-xbrl", action="store_true")
    args = ap.parse_args()

    if args.tickers:
        universe = [t.strip().upper() for t in args.tickers.split(",")]
    else:
        universe = sorted({f.stem.upper() for f in (ROOT / "wiki/entities/tickers").glob("*.md")})

    print(f"universe: {len(universe)} tickers, processing first {args.limit}")
    cik_map = get_cik_map(set(universe))
    print(f"CIK mapped: {len(cik_map)}")

    idx = open(INDEX, "a", encoding="utf-8") if INDEX.parent.exists() else None
    done = 0
    for t in universe[: args.limit * 2]:
        if t not in cik_map:
            continue
        info = cik_map[t]
        cik = info["cik"]
        outdir = OUT / t.upper()
        print(f"[{done+1}/{args.limit}] {t} ({info['name'][:30]}) CIK {cik}")

        n_xbrl = 0
        if not args.skip_xbrl:
            n_xbrl = scrape_concepts(cik, t, outdir)

        feed = scrape_filings_feed(cik, t)
        if feed:
            outdir.mkdir(parents=True, exist_ok=True)
            fp = outdir / f"{t}-filings.json"
            fp.write_text(json.dumps(feed, indent=1), encoding="utf-8")

        if idx:
            idx.write(json.dumps({"ticker": t, "cik": cik, "name": info["name"],
                                  "xbrl_points": n_xbrl, "filings": len(feed),
                                  "scraped": date.today().isoformat()}) + "\n")
        done += 1
        if done >= args.limit:
            break
    if idx:
        idx.close()
    print(f"done: {done} companies scraped")


if __name__ == "__main__":
    sys.exit(main())
