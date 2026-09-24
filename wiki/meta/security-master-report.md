---
name: security-master-report
aliases: [security-master-report]
categories: [wiki]
type: reference
status: active
created: 2026-08-25
updated: 2026-08-25
tags:
  - topic/security-master
related: []
---

# Security Master Report

Generated: 2026-08-25 (offline build; no network calls)
Companion artifact: `wiki/meta/security-master.json` (125 records, ASCII-only)
Factor store: `Efforts/osanwe-v2-overhaul/_work/factors.db` (bars table, distinct tickers = 125; window 2021-08-24 .. 2026-08-24)

## 1. What this is

A one-row-per-instrument master for every ticker in the factor store, mapping each
store key to: instrument identity, asset class, sector classification
(GICS-style), listing venue, US-listing status (domestic vs ADR vs fund vs
crypto), identifier data where the vault actually contains it, and ambiguity
flags. Built only from in-vault sources:

1. Entity notes: `wiki/entities/tickers/*.md` (frontmatter + body)
2. EDGAR-derived captures: `wiki/investing/filings/<TICKER>/{TICKER}-filings.json, -xbrl.json`
3. CIK references embedded verbatim in `wiki/investing/analyses/*.md`
4. Store-derived facts: bar coverage, src segments, corporate-action audit at
   `Efforts/osanwe-v2-overhaul/_work/audit-corporate-actions.md`

Per task constraints, `.raw/`, `private/`, `finance/`, and `*.local.md` trees were
not read.

## 2. Composition of the 125

| asset_class | count | notes |
|---|---|---|
| equity | 88 | common stock, US exchange-listed (incl. foreign-incorporated but SEC-domestic filers) |
| adr | 7 | 5 exchange-listed ADS (ARM, ASML, ASX, TSM, NBIS) + 3 OTC/pink ADRs (ABBNY, ASMIY, ATEYY) |
| etf | 20 | broad market, sector SPDRs, defense, semis, thematic |
| crypto | 9 | spot USD pairs (BTC, SOL, XRP, XLM, LINK, HBAR, ALGO, QNT, ONDO) |
| commodity_trust | 1 | IAU gold grantor trust (classified out of "etf" deliberately) |

GICS-style sector distribution: Information Technology 56, Industrials 25,
Utilities 11, Consumer Discretionary 4, Real Estate 4 (2 REITs + XLRE + DTCR),
Communication Services 3, Financials 2 (COIN + XLF), Materials 2 (MP, USAR),
Health Care 2 (HIMS + XLV), Energy 2 (XLE + VDE), Consumer Staples 1 (XLP),
Multi-sector funds 6, crypto n/a 9.

US-listed vs foreign exposure:
- Domestic US-listed equities: 87 (includes foreign-incorporated-but-US-listed
  domestic filers: GFS, CRDO, FN, UCTT - Cayman or Swiss/Irish incorporated,
  NASDAQ/NYSE listed, SEC domestic reporting).
- Exchange-listed ADRs/ADS: ARM (NASDAQ), ASML (NASDAQ NY-registry shares),
  ASX (NYSE), TSM (NYSE), NBIS (NASDAQ; technically a direct listing of Dutch NV
  shares, not an ADS program - classified with the ADR cohort functionally).
- OTC ADRs: ABBNY, ASMIY, ATEYY (pink-sheet level liquidity).
- Foreign private issuers filing 20-F/6-K in this universe: NBIS, TSM, and the
  three OTC ADRs (no EDGAR XBRL layer exists in the vault for any of these;
  their filings dirs hold only Form 4 / SC 13D/G capture).
- Crypto pairs are not securities listings at all.

## 3. Mapping decisions

### 3.1 Asset class boundaries
- **IAU** is a grantor trust holding bullion, not a 1940-Act fund -> recorded as
  `commodity_trust`, separate from ETFs.
- **NBIS**: Dutch N.V. shares listed directly on NASDAQ (ex-Yandex restructuring,
  renamed Aug 2024). Vault note cites ISIN NL0009805522 verbatim. Classified
  `equity` with subclass `foreign_issuer_shares_us_listed`, grouped with the
  ADR-exchange cohort for exposure purposes.
- **COIN** is an operating company (crypto exchange), NOT crypto asset class.
- **SPCX** is SpaceX itself since the 2026-06-12 IPO. The old Tuttle "SPAC and
  New Issue ETF" that previously used SPCX moved to SPCK on 2026-04-07
  (documented in the entity note). The store's SPCX bars start 2026-06-12 =
  exactly the IPO date = consistent with the SpaceX identity. Flagged anyway.
- **SMR** is NuScale Power - the ticker collides with the generic technology term
  used throughout the vault ("small modular reactor"). Disambiguated by CIK.

### 3.2 Sector scheme
Vault entity notes carry free-text `sector:` fields that do not map cleanly to
GICS. The master assigns a GICS-sector-consistent label per record and keeps the
vault's own language in `industry_hint`. ETF sectors reflect underlying index
sector (e.g., DTCR -> Real Estate despite ~13% semis weight documented in the
6/07 analysis).

### 3.3 Identifier policy (the big caveat)
CUSIP/ISIN values were filled ONLY when verbatim in vault text. Result:
- ISIN documented: 1 (NBIS NL0009805522)
- CUSIP documented: 0
- CIK documented: 15 records (AMD 2488, AMZN 1018724, AVGO 1730168, GEV/META/
  MSFT/NBIS/OKLO/RKLB/SMR/TSM/WBD/VOO/SMH/NVDA-family references; see JSON
  `identifier_provenance` per record)
- Everything else: null, deliberately. Fabricating identifiers offline would be
  worse than leaving them empty. This is the single largest gap; see section 5.

Note on META CIK: two different references exist in vault analyses (1045810 and
1326801). One belongs to Meta Platforms; the other appears in an analysis
context that may conflate entities. The JSON carries the conflict flag rather
than silently choosing. Similarly, GOOGL analyses cite CIK 1652044 (Alphabet)
consistently.

### 3.4 Bar-key vs note-key mismatches (resolved)
The factor store keys differ from entity-note keys for these instruments; the
JSON links them via flags:
- `ABBNY` (bars) <-> `ABB.md` (entity note) - same instrument, ABB Ltd ADR
- `BTC-USD` <-> `BTC.md`, `SOL-USD` <-> `SOL.md`, `XRP-USD` <-> `XRP.md`,
  `ALGO-USD` <-> `ALGO.md`, `HBAR-USD` <-> `HBAR.md`, `LINK-USD` <-> `LINK.md`,
  `ONDO-USD` <-> `ONDO.md`, `QNT-USD` <-> `QNT.md`, `XLM-USD` <-> `XLM.md`
- `SPY` has no entity note (benchmark-only role in the store)
Entity-note keys without bars (ABB, PSTG, XDC and the un-suffixed crypto keys):
present in the knowledge base but not in this factor store; not master rows.

## 4. Identifier ambiguities flagged

1. **ABBNY vs ABB**: store uses ABBNY (OTC ADR); knowledge base keys the note
   ABB. Same issuer, two symbol conventions across systems. Also: ABB Ltd has
   multiple ADR programs historically; ratio changes would silently embed in
   yfinance-adjusted bars (corporate-action audit rates this LOW risk).
2. **ASX vs ASMIY - genuine collision risk**: ASX here is ASE Technology Holding
   (Taiwan OSAT, NYSE ADS) - NOT the Australian Securities Exchange ticker
   namespace and NOT ASM International. ASMIY separately maps to ASM
   International N.V. (Netherlands, OTC ADR). Three-way confusion surface:
   ASX (ASE Taiwan) / ASMIY (ASM Intl NL) / ASX.AX (ASX Ltd Australia, not in
   store). Both entity notes exist separately and both instruments have
   independent rows in the master.
3. **ATEYY**: Advantest OTC ADR; TER (Teradyne) is the US peer, not the same
   company. Note also warns TEL (TE Connectivity, NYSE) must not be confused
   with Tokyo Electron (8035.T) - the latter is not in the store.
4. **SPCX ticker reuse**: former Tuttle ETF until 2026-04-07; SpaceX from
   2026-06-12. Bars start on the IPO date so the series is clean, but any
   external tool resolving historical "SPCX" may return the dead ETF series.
5. **MRAM**: Everspin Technologies - ticker equals the technology acronym
   (magnetoresistive RAM); search-tooling hazard.
6. **WDC/SNDK split**: SanDisk spun off from Western Digital 2025-02-24; SNDK
   bars start 2025-02-13 (spin-related listing mechanics). Corporate-action
   audit rates WDC pre-spin bars HIGH risk for event backtests (distribution
   unadjusted).
7. **CEG**: Constellation spun off from Exelon Jan 2022 - first bar 2022-01-19;
   pre-spin history does not exist in-store.
8. **GEV**: GE Vernova spinoff Apr 2024; short history is structural.
9. **Dual-src seam**: ACLS, ASX, COHU, ENTG, GLW, MPWR, TEL, TER, UCTT carry two
   ingest segments ('yfinance' from 2025-01-21, 'yfinance-5y' before); audited
   seam discontinuities plausible (-4.4%..+4.2%) but no systematic break.
10. **De-SPAC early-bar artifacts**: SMR (-33%/-35% moves flagged MEDIUM), OKLO
    (mid-price opening series, MEDIUM), USAR (2025 de-SPAC).
11. **ADJ basis drift**: all bars are yfinance auto-adjusted closes ingested at
    different times; cross-ticker LEVEL comparisons mix adjustment bases
    (documented in audit-corporate-actions.md finding 3). Within-ticker returns
    unaffected.

## 5. Gaps (honest list)

1. **No CUSIPs, near-no ISINs.** The constraint set forbade network lookups and
   the vault simply never recorded them. To complete: run a permitted-network
   pass against SEC company_tickers.json (maps ticker->CIK->cusip via filings
   header data) plus an ISIN vendor/OpenFIGI lookup. Estimated effort: trivial
   once network is allowed; the schema already has the fields.
2. **ETF holdings metadata** (index, issuer) is captured from vault analyses
   where present (VOLT, DTCR, SMH, VOO) and otherwise best-known values marked
   in flags; no prospectus documents are stored locally.
3. **Venue values for most equities** (NASDAQ vs NYSE) are best-known primary
   venues, not vault-verbatim. They were stable for years for these large caps,
   but a handful could have moved (e.g., voluntary transfer listings). Treat
   venue as high-confidence-not-certain except where a flag cites a source.
4. **ADR program type** (sponsored vs unsponsored) unverifiable offline for
   ABBNY/ASMIY/ATEYY; flagged generically.
5. **Crypto pair provenance**: bars come from yfinance aggregate feeds; venue is
   therefore "aggregate", not a specific exchange. No CUSIP/ISIN applies; if
   needed later, ISO-style crypto asset identifiers (e.g., DTI) are out of scope.
6. **HOOD appears in the EDGAR filings tree** but has NO bars in factors.db ->
   correctly excluded from the master (it is not a factor-store instrument).
7. **PSTG, XDC** have entity notes but no bars -> excluded, noted here so the
   next person doesn't think they were dropped by accident.

## 6. Files

- `wiki/meta/security-master.json` - the machine-readable master (schema_version 1.0)
- `wiki/meta/security-master-report.md` - this document
- Build script (reproducible): `~\build-security-master.py`
  (kept outside the vault because it was authored in session workspace; copy it
  under Efforts/osanwe-v2-overhaul/_work/ to regenerate after re-ingests)

## 7. Regeneration contract

Re-run the build script after any bulk re-ingest. It hard-fails if the bar
ticker set changes (asserts exactly 125 and full mapping coverage), so a new
instrument cannot enter the store silently unmapped.
