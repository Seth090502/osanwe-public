---
aliases: []
categories: [wiki]
type: reference
status: active
created: 2026-08-24
updated: 2026-08-24
confidence: medium
tags:
  - topic/investing
  - topic/filings
  - topic/xbrl
related: ["ref-institutional-insider-tracking", "ref-factor-lens"]
---

# Financial Statements Reference (EDGAR XBRL)

GENERATED: 2026-08-24 from wiki/investing/filings/`<TICKER>`/`<TICKER>`-xbrl.json
(EDGAR companyconcept pulls: Revenues/RevenueFromContractWithCustomerExcludingAssessedTax,
NetIncomeLoss, CashAndCashEquivalentsAtCarryingValue, LongTermDebt,
PaymentsToAcquirePropertyPlantAndEquipment, ResearchAndDevelopmentExpense;
tag map in tools/edgar-scraper.py CONCEPTS). Regenerate by re-running the
aggregation over the xbrl JSONs; do not hand-edit numbers.

Coverage: 82 of 90 indexed tickers have an xbrl JSON; 1189 usable revenue points.
All dollar figures USD. Flow metrics (revenue, net income, capex, R&D) are
quarterly; balance-sheet metrics (cash, long-term debt) are latest snapshots.
Where a fiscal year-end 10-K is the freshest revenue point, Q4 is DERIVED as
FY minus the three reported quarters and marked "(Q4d)". YoY compares the
same fiscal quarter one year earlier (330-400 day window). TTM = trailing
four reported quarters (span 240-400 days).

Market caps for ranking: yfinance fast_info, pulled 2026-08-24, cache outside vault (~/edgar-ref-mcaps.json); 86/90 resolved.

EPS: NOT COMPUTABLE from this corpus. EarningsPerShareDiluted is mapped in
tools/edgar-scraper.py but produced 0 points across all tickers; every EPS
cell below is therefore n/a by construction, not omission.

## 1. Per-ticker financial profile (all tickers with revenue data)

| Ticker | Mkt cap | LQ | Rev/LQ | Rev YoY | NI/LQ | NI YoY | EPS dil | NI marg TTM | Src (file + LQ period) |
|---|---|---|---|---|---|---|---|---|---|
| AAOI | 10.6B | 2026Q2 | 192M | 86.4% | -23M | 150.4% | n/a | -10.8% | wiki/investing/filings/AAOI/AAOI-xbrl.json period=2026-06-30 (10-Q) |
| AEIS | 11.4B | 2026Q2 | 574M | 30.0% | n/a | n/a | n/a | n/a | wiki/investing/filings/AEIS/AEIS-xbrl.json period=2026-06-30 (10-Q) |
| AEP | 65.8B | 2026Q1 | 6.0B | 10.2% | n/a | n/a | n/a | n/a | wiki/investing/filings/AEP/AEP-xbrl.json period=2026-03-31 (10-Q) |
| ALAB | 49.4B | 2026Q2 | 392M | 104.5% | 153M | 198.9% | n/a | 31.3% | wiki/investing/filings/ALAB/ALAB-xbrl.json period=2026-06-30 (10-Q) |
| AMAT | 390.9B | 2026Q3 | 9.1B | 24.8% | 2.5B | 42.7% | n/a | 30.1% | wiki/investing/filings/AMAT/AMAT-xbrl.json period=2026-07-26 (10-Q) |
| AMBA | 3.2B | 2026Q2 | 100M | 16.9% | -18M | -25.6% | n/a | -19.1% | wiki/investing/filings/AMBA/AMBA-xbrl.json period=2026-04-30 (10-Q) |
| AMD | 772.6B | 2026Q2 | 11.5B | 50.1% | 2.3B | 163.4% | n/a | 15.6% | wiki/investing/filings/AMD/AMD-xbrl.json period=2026-06-27 (10-Q) |
| AMKR | 12.5B | 2021Q3 | 1.7B | 24.1% | n/a | n/a | n/a | n/a | wiki/investing/filings/AMKR/AMKR-xbrl.json period=2021-09-30 (10-Q) |
| AMZN | 2.79T | 2026Q2 | 200.6B | 19.6% | 62.6B | 244.9% | n/a | 17.0% | wiki/investing/filings/AMZN/AMZN-xbrl.json period=2026-06-30 (10-Q) |
| ANET | 237.9B | 2026Q2 | 3.0B | 37.7% | 1.2B | 36.5% | n/a | 37.7% | wiki/investing/filings/ANET/ANET-xbrl.json period=2026-06-30 (10-Q) |
| APH | 193.6B | 2026Q2 | 8.8B | 55.0% | 1.8B | 62.1% | n/a | 17.4% | wiki/investing/filings/APH/APH-xbrl.json period=2026-06-30 (10-Q) |
| AVAV | 8.1B | 2025Q4 | 473M | 150.7% | n/a | n/a | n/a | n/a | wiki/investing/filings/AVAV/AVAV-xbrl.json period=2025-11-01 (10-Q) |
| AVGO | 1.75T | 2026Q2 | 22.2B | 47.9% | n/a | n/a | n/a | n/a | wiki/investing/filings/AVGO/AVGO-xbrl.json period=2026-05-03 (10-Q) |
| BAH | 9.3B | 2026Q2 | 2.8B | -4.2% | 198M | -26.9% | n/a | 7.6% | wiki/investing/filings/BAH/BAH-xbrl.json period=2026-06-30 (10-Q) |
| BE | | | | | | | n/a | | no revenue points in xbrl json |
| BTC | | | | | | | n/a | | no revenue points in xbrl json |
| BWXT | 14.4B | 2026Q1 | 860M | 26.1% | 91M | 20.7% | n/a | n/a | wiki/investing/filings/BWXT/BWXT-xbrl.json period=2026-03-31 (10-Q) |
| CEG | 96.7B | 2026Q2 | 7.5B | 23.0% | 513M | -38.9% | n/a | 11.1% | wiki/investing/filings/CEG/CEG-xbrl.json period=2026-06-30 (10-Q) |
| COHR | 56.7B | 2026Q2 | 2.0B | 33.7% | 241M | -351.6% | n/a | 11.3% | wiki/investing/filings/COHR/COHR-xbrl.json period=2026-06-30 (10-K(Q4 derived)) |
| COIN | 49.2B | 2026Q2 | 1.2B | -18.5% | -359M | -125.2% | n/a | 17.6% | wiki/investing/filings/COIN/COIN-xbrl.json period=2026-06-30 (10-Q) |
| CRDO | 43.0B | 2026Q2 | 437M | 157.0% | 169M | 362.2% | n/a | 35.4% | wiki/investing/filings/CRDO/CRDO-xbrl.json period=2026-05-02 (10-K(Q4 derived)) |
| CRWV | 48.5B | 2026Q2 | 2.6B | 112.5% | -626M | 115.9% | n/a | -23.3% | wiki/investing/filings/CRWV/CRWV-xbrl.json period=2026-06-30 (10-Q) |
| CSCO | 437.7B | 2026Q2 | 15.8B | 12.0% | 3.4B | 35.4% | n/a | 19.7% | wiki/investing/filings/CSCO/CSCO-xbrl.json period=2026-04-25 (10-Q) |
| DELL | 285.6B | 2026Q2 | 43.8B | 87.5% | 3.4B | 256.3% | n/a | 5.3% | wiki/investing/filings/DELL/DELL-xbrl.json period=2026-05-01 (10-Q) |
| DLR | 70.5B | 2026Q1 | 1.6B | 16.2% | 179M | 63.0% | n/a | 21.9% | wiki/investing/filings/DLR/DLR-xbrl.json period=2026-03-31 (10-Q) |
| DUK | 93.4B | 2018Q1 | 5.9B | n/a | n/a | n/a | n/a | n/a | wiki/investing/filings/DUK/DUK-xbrl.json period=2018-03-31 (10-Q) |
| EQIX | 105.1B | 2026Q2 | 2.6B | 16.4% | 479M | 30.2% | n/a | 15.6% | wiki/investing/filings/EQIX/EQIX-xbrl.json period=2026-06-30 (10-Q) |
| ETN | 162.8B | 2026Q2 | 8.5B | 21.4% | 821M | -16.4% | n/a | 12.7% | wiki/investing/filings/ETN/ETN-xbrl.json period=2026-06-30 (10-Q) |
| FLNC | 1.6B | 2026Q2 | 650M | 7.9% | -33M | -624.9% | n/a | -3.1% | wiki/investing/filings/FLNC/FLNC-xbrl.json period=2026-06-30 (10-Q) |
| FN | 15.6B | 2026Q2 | 1.3B | 44.6% | 139M | 59.7% | n/a | 10.2% | wiki/investing/filings/FN/FN-xbrl.json period=2026-06-26 (10-K(Q4 derived)) |
| GD | 104.0B | 2018Q3 | 9.2B | n/a | n/a | n/a | n/a | n/a | wiki/investing/filings/GD/GD-xbrl.json period=2018-07-01 (10-Q) |
| GEV | 254.8B | 2026Q2 | 11.1B | 21.9% | 668M | 30.0% | n/a | 23.0% | wiki/investing/filings/GEV/GEV-xbrl.json period=2026-06-30 (10-Q) |
| GOOGL | 4.22T | 2026Q2 | 119.8B | 24.2% | 112.2B | 297.9% | n/a | 53.4% | wiki/investing/filings/GOOGL/GOOGL-xbrl.json period=2026-06-30 (10-Q) |
| HII | 11.8B | 2026Q2 | 3.4B | 10.9% | 208M | 36.8% | n/a | 5.0% | wiki/investing/filings/HII/HII-xbrl.json period=2026-06-30 (10-Q) |
| HIMS | 7.9B | 2026Q2 | 753M | 38.2% | -86M | -303.0% | n/a | -4.7% | wiki/investing/filings/HIMS/HIMS-xbrl.json period=2026-06-30 (10-Q) |
| HPE | 70.8B | 2026Q2 | 10.7B | 40.0% | 624M | -159.4% | n/a | 4.0% | wiki/investing/filings/HPE/HPE-xbrl.json period=2026-04-30 (10-Q) |
| HUBB | | | | | | | n/a | | no revenue points in xbrl json |
| IAU | n/a | 2013Q3 | 772M | 1607.6% | n/a | n/a | n/a | n/a | wiki/investing/filings/IAU/IAU-xbrl.json period=2013-09-30 (10-Q) |
| INTC | 473.3B | 2026Q2 | 16.1B | 25.4% | -11.0B | 278.1% | n/a | -19.8% | wiki/investing/filings/INTC/INTC-xbrl.json period=2026-06-27 (10-Q) |
| KLAC | 240.4B | 2026Q2 | 3.7B | 15.2% | 1.4B | 13.3% | n/a | 35.6% | wiki/investing/filings/KLAC/KLAC-xbrl.json period=2026-06-30 (10-K(Q4 derived)) |
| KTOS | 10.7B | 2026Q2 | 459M | 30.5% | 4M | 51.7% | n/a | 2.0% | wiki/investing/filings/KTOS/KTOS-xbrl.json period=2026-06-28 (10-Q) |
| LHX | 49.7B | 2026Q3 | 5.9B | 8.4% | 600M | 31.0% | n/a | 8.2% | wiki/investing/filings/LHX/LHX-xbrl.json period=2026-07-03 (10-Q) |
| LINK | 80M | 2026Q2 | 4M | 10.4% | 248K | 148.0% | n/a | -7.9% | wiki/investing/filings/LINK/LINK-xbrl.json period=2026-06-30 (10-Q) |
| LITE | 77.7B | 2025Q2 | 481M | n/a | 213M | n/a | n/a | n/a | wiki/investing/filings/LITE/LITE-xbrl.json period=2025-06-28 (10-K(Q4 derived)) |
| LMT | 130.1B | 2026Q2 | 20.1B | 10.5% | 1.8B | 436.8% | n/a | 8.2% | wiki/investing/filings/LMT/LMT-xbrl.json period=2026-06-28 (10-Q) |
| LRCX | 392.9B | 2026Q2 | 6.7B | 30.0% | 2.3B | 32.4% | n/a | 31.3% | wiki/investing/filings/LRCX/LRCX-xbrl.json period=2026-06-28 (10-K(Q4 derived)) |
| MBLY | 7.7B | 2026Q2 | 508M | 0.4% | -21M | -68.7% | n/a | -198.5% | wiki/investing/filings/MBLY/MBLY-xbrl.json period=2026-06-27 (10-Q) |
| META | 1.40T | 2026Q2 | 60.8B | 28.0% | 15.8B | -13.6% | n/a | 27.9% | wiki/investing/filings/META/META-xbrl.json period=2026-06-30 (10-Q) |
| MKSI | 18.9B | 2026Q2 | 1.2B | 28.3% | 175M | 182.3% | n/a | 10.1% | wiki/investing/filings/MKSI/MKSI-xbrl.json period=2026-06-30 (10-Q) |
| MP | 10.7B | 2026Q2 | 108M | 89.0% | -20M | -34.3% | n/a | -33.0% | wiki/investing/filings/MP/MP-xbrl.json period=2026-06-30 (10-Q) |
| MRAM | 417M | 2026Q2 | 19M | 41.9% | -4M | 435.7% | n/a | -7.2% | wiki/investing/filings/MRAM/MRAM-xbrl.json period=2026-06-30 (10-Q) |
| MRVL | 212.8B | 2026Q2 | 2.4B | 27.6% | 34M | -80.6% | n/a | 26.5% | wiki/investing/filings/MRVL/MRVL-xbrl.json period=2026-05-02 (10-Q) |
| MSFT | 3.59T | 2026Q2 | 90.0B | 17.7% | 35.8B | 31.3% | n/a | 40.3% | wiki/investing/filings/MSFT/MSFT-xbrl.json period=2026-06-30 (10-K(Q4 derived)) |
| MU | 1.09T | 2026Q2 | 41.5B | 345.7% | 28.2B | 1398.3% | n/a | 55.9% | wiki/investing/filings/MU/MU-xbrl.json period=2026-05-28 (10-Q) |
| NEE | 174.5B | 2013Q3 | 4.4B | 14.3% | n/a | n/a | n/a | n/a | wiki/investing/filings/NEE/NEE-xbrl.json period=2013-09-30 (10-Q) |
| NOC | 78.3B | 2026Q2 | 10.9B | 5.1% | 1.1B | -6.8% | n/a | 10.5% | wiki/investing/filings/NOC/NOC-xbrl.json period=2026-06-30 (10-Q) |
| NOW | 132.8B | 2026Q2 | 4.0B | 24.0% | 298M | -22.6% | n/a | 11.2% | wiki/investing/filings/NOW/NOW-xbrl.json period=2026-06-30 (10-Q) |
| NRG | 23.8B | 2026Q2 | 7.5B | 11.0% | 506M | -586.5% | n/a | 2.6% | wiki/investing/filings/NRG/NRG-xbrl.json period=2026-06-30 (10-Q) |
| NVDA | 5.20T | 2026Q2 | 81.6B | 85.2% | 58.3B | 210.6% | n/a | 53.4% | wiki/investing/filings/NVDA/NVDA-xbrl.json period=2026-04-26 (10-Q) |
| OKLO | 7.8B | 2026Q2 | 1M | n/a | -49M | 96.6% | n/a | n/a | wiki/investing/filings/OKLO/OKLO-xbrl.json period=2026-06-30 (10-Q) |
| ONTO | 17.9B | 2026Q2 | 343M | 35.3% | 60M | 77.2% | n/a | 13.9% | wiki/investing/filings/ONTO/ONTO-xbrl.json period=2026-06-30 (10-Q) |
| ORCL | 421.9B | 2026Q2 | 19.2B | 20.6% | 4.3B | 25.6% | n/a | 25.4% | wiki/investing/filings/ORCL/ORCL-xbrl.json period=2026-05-31 (10-K(Q4 derived)) |
| PLTR | 432.4B | 2026Q2 | 1.9B | 92.8% | 1.1B | 225.0% | n/a | 44.4% | wiki/investing/filings/PLTR/PLTR-xbrl.json period=2026-06-30 (10-Q) |
| PPL | 25.9B | 2026Q1 | 2.8B | 10.8% | 452M | 9.2% | n/a | 13.1% | wiki/investing/filings/PPL/PPL-xbrl.json period=2026-03-31 (10-Q) |
| QCOM | 168.8B | 2026Q2 | 9.9B | -4.0% | 2.0B | -24.9% | n/a | 21.0% | wiki/investing/filings/QCOM/QCOM-xbrl.json period=2026-06-28 (10-Q) |
| QNT | 2.1B | 2026Q2 | 8M | 279.4% | -65M | n/a | n/a | n/a | wiki/investing/filings/QNT/QNT-xbrl.json period=2026-06-30 (10-Q) |
| RKLB | 46.4B | 2026Q2 | 234M | 62.0% | -49M | -25.8% | n/a | -23.3% | wiki/investing/filings/RKLB/RKLB-xbrl.json period=2026-06-30 (10-Q) |
| RTX | 282.9B | 2026Q2 | 24.7B | 14.5% | 2.1B | 29.1% | n/a | 8.3% | wiki/investing/filings/RTX/RTX-xbrl.json period=2026-06-30 (10-Q) |
| SMCI | 24.1B | 2026Q1 | 10.2B | 122.7% | 483M | 344.4% | n/a | 3.7% | wiki/investing/filings/SMCI/SMCI-xbrl.json period=2026-03-31 (10-Q) |
| SMR | 3.9B | 2026Q2 | 75K | -99.1% | -48M | 169.5% | n/a | -3888.7% | wiki/investing/filings/SMR/SMR-xbrl.json period=2026-06-30 (10-Q) |
| SNDK | 233.7B | 2026Q3 | 9.0B | 371.6% | 6.9B | -30113.0% | n/a | 56.5% | wiki/investing/filings/SNDK/SNDK-xbrl.json period=2026-07-03 (10-K(Q4 derived)) |
| SNPS | 76.2B | 2026Q2 | 2.3B | 41.9% | 17M | -95.0% | n/a | 8.9% | wiki/investing/filings/SNPS/SNPS-xbrl.json period=2026-04-30 (10-Q) |
| SO | 102.3B | 2026Q1 | 8.4B | 8.0% | 1.4B | 1.6% | n/a | 14.5% | wiki/investing/filings/SO/SO-xbrl.json period=2026-03-31 (10-Q) |
| SPCX | 1.81T | 2026Q2 | 7.8B | 91.9% | -541M | -46.3% | n/a | n/a | wiki/investing/filings/SPCX/SPCX-xbrl.json period=2026-06-30 (10-Q) |
| TLN | 15.1B | 2026Q2 | 747M | 18.6% | -92M | -227.8% | n/a | -5.1% | wiki/investing/filings/TLN/TLN-xbrl.json period=2026-06-30 (10-Q) |
| TSLA | 1.43T | 2026Q2 | 28.2B | 25.5% | 1.1B | -4.9% | n/a | 3.7% | wiki/investing/filings/TSLA/TSLA-xbrl.json period=2026-06-30 (10-Q) |
| USAR | 4.7B | 2026Q2 | 6M | n/a | -10M | -92.7% | n/a | n/a | wiki/investing/filings/USAR/USAR-xbrl.json period=2026-06-30 (10-Q) |
| VRT | 100.8B | 2026Q2 | 3.3B | 24.1% | 498M | 53.5% | n/a | 14.0% | wiki/investing/filings/VRT/VRT-xbrl.json period=2026-06-30 (10-Q) |
| VST | 45.7B | 2026Q2 | 4.0B | -5.5% | 305M | -6.7% | n/a | 11.6% | wiki/investing/filings/VST/VST-xbrl.json period=2026-06-30 (10-Q) |
| WBD | 71.6B | 2026Q2 | 8.7B | -11.2% | 149M | -90.6% | n/a | -8.8% | wiki/investing/filings/WBD/WBD-xbrl.json period=2026-06-30 (10-Q) |
| WDC | 165.6B | 2026Q3 | 3.7B | -186.9% | 3.2B | -341.1% | n/a | 72.9% | wiki/investing/filings/WDC/WDC-xbrl.json period=2026-07-03 (10-K(Q4 derived)) |
| XRP | | | | | | | n/a | | no revenue points in xbrl json |

Notes: NI/LQ is the net-income point closest to the latest revenue quarter
(45-day tolerance; form noted implicitly by same-file provenance). NI margin
TTM uses trailing-four-quarter sums; blank when fewer than 4 contiguous
quarters exist. Negative YoY renders as negative percent.

## 2. Revenue trajectory -- top 30 tickers by market cap, last 8 reported quarters

Values are $B revenue per reported quarter (10-Q/10-K rows only; Q4d =
derived from FY 10-K minus three quarters). Bar length scales with log10
value relative to the row max (min 1 char if value > 0).

| Ticker | Q-7 | Q-6 | Q-5 | Q-4 | Q-3 | Q-2 | Q-1 | Q-0 | Trend |
|---|---|---|---|---|---|---|---|---|---|
| NVDA | 30.0 | 35.1 | 39.3* | 44.1 | 46.7 | 57.0 | 68.1* | 81.6 | ################################################################################ |
| GOOGL | 88.3 | 96.5* | 90.2 | 96.4 | 102.3 | 113.8* | 109.9 | 119.8 | ################################################################################ |
| MSFT | 65.6 | 69.6 | 70.1 | 76.4* | 77.7 | 81.3 | 82.9 | 90.0* | ################################################################################ |
| AMZN | 158.9 | 187.8* | 155.7 | 167.7 | 180.2 | 213.4* | 181.5 | 200.6 | ################################################################################ |
| AVGO | 13.1 | 14.1* | 14.9 | 15.0 | 16.0 | 18.0* | 19.3 | 22.2 | ################################################################################ |
| TSLA | 25.2 | 25.7* | 19.3 | 22.5 | 28.1 | 24.9* | 22.4 | 28.2 | ################################################################################ |
| META | 40.6 | 48.4* | 42.3 | 47.5 | 51.2 | 59.9* | 56.3 | 60.8 | ################################################################################ |
| MU | 7.8* | 8.7 | 8.1 | 9.3 | 11.3* | 13.6 | 23.9 | 41.5 | ########################################################################### |
| AMD | 6.8 | 7.7* | 7.4 | 7.7 | 9.2 | 10.3* | 10.3 | 11.5 | ################################################################################ |
| INTC | 13.3 | 14.3* | 12.7 | 12.9 | 13.7 | 13.7* | 13.6 | 16.1 | ################################################################################ |
| CSCO | 13.6* | 13.8 | 14.0 | 14.1 | 14.7* | 14.9 | 15.3 | 15.8 | ################################################################################ |
| PLTR | 0.7 | 0.8* | 0.9 | 1.0 | 1.2 | 1.4* | 1.6 | 1.9 | ################################################################################ |
| ORCL | 13.3 | 14.1 | 14.1 | 15.9* | 14.9 | 16.1 | 17.2 | 19.2* | ################################################################################ |
| LRCX | 4.2 | 4.4 | 4.7 | 5.2* | 5.3 | 5.3 | 5.8 | 6.7* | ################################################################################ |
| AMAT | 7.0* | 7.2 | 7.1 | 7.3 | 6.8* | 7.0 | 7.9 | 9.1 | ################################################################################ |
| DELL | 25.0 | 24.4 | -47.7* | 23.4 | 29.8 | 27.0 | 33.4* | 43.8 | ####################.################################################## |
| RTX | 20.1 | 21.6* | 20.3 | 21.6 | 22.5 | 24.2* | 22.1 | 24.7 | ################################################################################ |
| GEV | 8.9 | 10.6* | 8.0 | 9.1 | 10.0 | 11.0* | 9.3 | 11.1 | ################################################################################ |
| KLAC | 2.8 | 3.1 | 3.1 | 3.2* | 3.2 | 3.3 | 3.4 | 3.7* | ################################################################################ |
| ANET | 1.8 | 1.9* | 2.0 | 2.2 | 2.3 | 2.5* | 2.7 | 3.0 | ################################################################################ |
| SNDK | 1.9 | 1.9 | 1.7 | 1.9* | 2.3 | 3.0 | 6.0 | 9.0* | ########################################################################### |
| MRVL | 1.3 | 1.5 | 1.8* | 1.9 | 2.0 | 2.1 | 2.2* | 2.4 | ################################################################################ |
| APH | 4.0 | 4.3* | 4.8 | 5.7 | 6.2 | 6.4* | 7.6 | 8.8 | ################################################################################ |
| NEE | . | . | . | . | 3.8 | 3.3 | 3.8 | 4.4 | ....######################################## |
| QCOM | 10.2* | 11.7 | 11.0 | 10.4 | 11.3* | 12.3 | 10.6 | 9.9 | ################################################################################ |
| WDC | 2.2 | 2.4 | 2.3 | -4.3* | 2.8 | 3.0 | 3.3 | 3.7* | ##############################.######################################## |
| ETN | 6.3 | 6.2* | 6.4 | 7.0 | 7.0 | 7.1* | 7.5 | 8.5 | ################################################################################ |
| NOW | 2.8 | 3.0* | 3.1 | 3.2 | 3.4 | 3.6* | 3.8 | 4.0 | ################################################################################ |
| LMT | 17.1 | 18.6* | 18.0 | 18.2 | 18.6 | 20.3* | 18.0 | 20.1 | ################################################################################ |
| EQIX | 2.2 | 2.3* | 2.2 | 2.3 | 2.3 | 2.4* | 2.4 | 2.6 | ################################################################################ |

"Q-N" = N quarters before the latest reported quarter (column alignment is
per-ticker because fiscal calendars differ; read each row left to right as
oldest-to-newest). "*" suffix = Q4 derived from 10-K. "." = no data point.
Negative cells are a derivation artifact (FY minus three 10-Q quarters where
the FY row or quarter set is incomplete -- e.g. DELL, WDC); treat those
quarters as missing, not as real revenue declines.

Per-row source: wiki/investing/filings/`<TICKER>`/`<TICKER>`-xbrl.json, concept
Revenue/Revenues, periods = the up-to-8 dates behind each row (latest matches
the LQ column in Section 1).

## 3. Margin leaders (net margin proxy, TTM)

Gross margin is NOT computable: no cost-of-goods-sold concept was scraped
(see tag map above), so only the net proxy ranks here.

| Rank | Ticker | NI marg TTM | Rev TTM | NI TTM | LQ | Src |
|---|---|---|---|---|---|---|
| 1 | WDC | 72.9% | 12.9B | 9.4B | 2026Q3 | wiki/investing/filings/WDC/WDC-xbrl.json periods=2026Q3 window |
| 2 | SNDK | 56.5% | 20.2B | 11.4B | 2026Q3 | wiki/investing/filings/SNDK/SNDK-xbrl.json periods=2026Q3 window |
| 3 | MU | 55.9% | 90.3B | 50.5B | 2026Q2 | wiki/investing/filings/MU/MU-xbrl.json periods=2026Q2 window |
| 4 | NVDA | 53.4% | 253.5B | 135.4B | 2026Q2 | wiki/investing/filings/NVDA/NVDA-xbrl.json periods=2026Q2 window |
| 5 | GOOGL | 53.4% | 445.9B | 237.9B | 2026Q2 | wiki/investing/filings/GOOGL/GOOGL-xbrl.json periods=2026Q2 window |
| 6 | PLTR | 44.4% | 6.2B | 2.7B | 2026Q2 | wiki/investing/filings/PLTR/PLTR-xbrl.json periods=2026Q2 window |
| 7 | MSFT | 40.3% | 331.8B | 133.7B | 2026Q2 | wiki/investing/filings/MSFT/MSFT-xbrl.json periods=2026Q2 window |
| 8 | ANET | 37.7% | 10.5B | 4.0B | 2026Q2 | wiki/investing/filings/ANET/ANET-xbrl.json periods=2026Q2 window |
| 9 | KLAC | 35.6% | 13.6B | 4.8B | 2026Q2 | wiki/investing/filings/KLAC/KLAC-xbrl.json periods=2026Q2 window |
| 10 | CRDO | 35.4% | 1.3B | 472M | 2026Q2 | wiki/investing/filings/CRDO/CRDO-xbrl.json periods=2026Q2 window |
| 11 | LRCX | 31.3% | 23.2B | 7.3B | 2026Q2 | wiki/investing/filings/LRCX/LRCX-xbrl.json periods=2026Q2 window |
| 12 | ALAB | 31.3% | 1.2B | 376M | 2026Q2 | wiki/investing/filings/ALAB/ALAB-xbrl.json periods=2026Q2 window |
| 13 | AMAT | 30.1% | 30.8B | 9.3B | 2026Q3 | wiki/investing/filings/AMAT/AMAT-xbrl.json periods=2026Q3 window |
| 14 | META | 27.9% | 228.2B | 63.7B | 2026Q2 | wiki/investing/filings/META/META-xbrl.json periods=2026Q2 window |
| 15 | MRVL | 26.5% | 8.7B | 2.3B | 2026Q2 | wiki/investing/filings/MRVL/MRVL-xbrl.json periods=2026Q2 window |
| 16 | ORCL | 25.4% | 67.4B | 17.1B | 2026Q2 | wiki/investing/filings/ORCL/ORCL-xbrl.json periods=2026Q2 window |
| 17 | GEV | 23.0% | 41.4B | 9.5B | 2026Q2 | wiki/investing/filings/GEV/GEV-xbrl.json periods=2026Q2 window |
| 18 | DLR | 21.9% | 6.3B | 1.4B | 2026Q1 | wiki/investing/filings/DLR/DLR-xbrl.json periods=2026Q1 window |
| 19 | QCOM | 21.0% | 44.1B | 9.3B | 2026Q2 | wiki/investing/filings/QCOM/QCOM-xbrl.json periods=2026Q2 window |
| 20 | CSCO | 19.7% | 60.7B | 12.0B | 2026Q2 | wiki/investing/filings/CSCO/CSCO-xbrl.json periods=2026Q2 window |
| 21 | COIN | 17.6% | 6.3B | 1.1B | 2026Q2 | wiki/investing/filings/COIN/COIN-xbrl.json periods=2026Q2 window |
| 22 | APH | 17.4% | 29.0B | 5.0B | 2026Q2 | wiki/investing/filings/APH/APH-xbrl.json periods=2026Q2 window |
| 23 | AMZN | 17.0% | 775.7B | 132.3B | 2026Q2 | wiki/investing/filings/AMZN/AMZN-xbrl.json periods=2026Q2 window |
| 24 | EQIX | 15.6% | 9.8B | 1.5B | 2026Q2 | wiki/investing/filings/EQIX/EQIX-xbrl.json periods=2026Q2 window |
| 25 | AMD | 15.6% | 41.3B | 6.4B | 2026Q2 | wiki/investing/filings/AMD/AMD-xbrl.json periods=2026Q2 window |

## 4. Capex intensity -- AI-infrastructure names

Method: latest fiscal-year (10-K) Capex and Revenue from the SAME fiscal
period -- a perfectly matched window -- preferred over TTM because the
scraped quarterly capex cadence is ragged (several names have 10-Q capex
gaps). Quarterly fallback only when no FY pair exists.

| Ticker | FY Capex | FY Rev | Capex/Rev | FY period | Src |
|---|---|---|---|---|---|
| NVDA | n/a | n/a | n/a | n/a | wiki/investing/filings/NVDA/NVDA-xbrl.json (no FY capex+revenue pair; quarterly window too thin) |
| TSM | n/a | n/a | n/a | n/a | no xbrl json in corpus (see Section 7) |
| AVGO | 623M | 63.9B | 1.0% | FY end 2025-11-02 (filed 2025-12-18) | wiki/investing/filings/AVGO/AVGO-xbrl.json |
| MRVL | 354M | 8.2B | 4.3% | FY end 2026-01-31 (filed 2026-03-11) | wiki/investing/filings/MRVL/MRVL-xbrl.json |
| MU | 15.9B | 37.4B | 42.4% | FY end 2025-08-28 (filed 2025-10-03) | wiki/investing/filings/MU/MU-xbrl.json |
| SNDK | 177M | 20.2B | 0.9% | FY end 2026-07-03 (filed 2026-08-17) | wiki/investing/filings/SNDK/SNDK-xbrl.json |
| WDC | 418M | 12.9B | 3.2% | FY end 2026-07-03 (filed 2026-08-14) | wiki/investing/filings/WDC/WDC-xbrl.json |

## 5. R&D spend ranking (TTM absolute and % of revenue)

| Rank | Ticker | R&D TTM | R&D % Rev | Rev TTM end | Src |
|---|---|---|---|---|---|
| 1 | META | 71.6B | 31.4% | 2026Q2 | wiki/investing/filings/META/META-xbrl.json R&D+rev TTM ending 2026-06-30 |
| 2 | GOOGL | 69.0B | 15.5% | 2026Q2 | wiki/investing/filings/GOOGL/GOOGL-xbrl.json R&D+rev TTM ending 2026-06-30 |
| 3 | MSFT | 35.6B | 10.7% | 2026Q2 | wiki/investing/filings/MSFT/MSFT-xbrl.json R&D+rev TTM ending 2026-06-30 |
| 4 | NVDA | 20.8B | 8.2% | 2026Q2 | wiki/investing/filings/NVDA/NVDA-xbrl.json R&D+rev TTM ending 2026-04-26 |
| 5 | INTC | 13.2B | 23.1% | 2026Q2 | wiki/investing/filings/INTC/INTC-xbrl.json R&D+rev TTM ending 2026-06-27 |
| 6 | AVGO | 12.0B | 15.9% | 2026Q2 | wiki/investing/filings/AVGO/AVGO-xbrl.json R&D+rev TTM ending 2026-05-03 |
| 7 | ORCL | 10.3B | 15.3% | 2026Q2 | wiki/investing/filings/ORCL/ORCL-xbrl.json R&D+rev TTM ending 2026-05-31 |
| 8 | QCOM | 9.9B | 22.4% | 2026Q2 | wiki/investing/filings/QCOM/QCOM-xbrl.json R&D+rev TTM ending 2026-06-28 |
| 9 | CSCO | 9.5B | 15.7% | 2026Q2 | wiki/investing/filings/CSCO/CSCO-xbrl.json R&D+rev TTM ending 2026-04-25 |
| 10 | AMD | 9.4B | 22.7% | 2026Q2 | wiki/investing/filings/AMD/AMD-xbrl.json R&D+rev TTM ending 2026-06-27 |
| 11 | TSLA | 7.7B | 7.5% | 2026Q2 | wiki/investing/filings/TSLA/TSLA-xbrl.json R&D+rev TTM ending 2026-06-30 |
| 12 | MU | 4.8B | 5.3% | 2026Q2 | wiki/investing/filings/MU/MU-xbrl.json R&D+rev TTM ending 2026-05-28 |
| 13 | AMAT | 4.0B | 12.9% | 2026Q3 | wiki/investing/filings/AMAT/AMAT-xbrl.json R&D+rev TTM ending 2026-07-26 |
| 14 | DELL | 3.3B | 2.5% | 2026Q2 | wiki/investing/filings/DELL/DELL-xbrl.json R&D+rev TTM ending 2026-05-01 |
| 15 | NOW | 3.3B | 22.1% | 2026Q2 | wiki/investing/filings/NOW/NOW-xbrl.json R&D+rev TTM ending 2026-06-30 |
| 16 | HPE | 3.2B | 8.2% | 2026Q2 | wiki/investing/filings/HPE/HPE-xbrl.json R&D+rev TTM ending 2026-04-30 |
| 17 | RTX | 2.8B | 3.0% | 2026Q2 | wiki/investing/filings/RTX/RTX-xbrl.json R&D+rev TTM ending 2026-06-30 |
| 18 | SNPS | 2.8B | 32.1% | 2026Q2 | wiki/investing/filings/SNPS/SNPS-xbrl.json R&D+rev TTM ending 2026-04-30 |
| 19 | LRCX | 2.4B | 10.2% | 2026Q2 | wiki/investing/filings/LRCX/LRCX-xbrl.json R&D+rev TTM ending 2026-06-28 |
| 20 | MRVL | 2.2B | 25.5% | 2026Q2 | wiki/investing/filings/MRVL/MRVL-xbrl.json R&D+rev TTM ending 2026-05-02 |
| 21 | COIN | 1.9B | 30.7% | 2026Q2 | wiki/investing/filings/COIN/COIN-xbrl.json R&D+rev TTM ending 2026-06-30 |
| 22 | KLAC | 1.5B | 11.3% | 2026Q2 | wiki/investing/filings/KLAC/KLAC-xbrl.json R&D+rev TTM ending 2026-06-30 |
| 23 | ANET | 1.4B | 13.0% | 2026Q2 | wiki/investing/filings/ANET/ANET-xbrl.json R&D+rev TTM ending 2026-06-30 |
| 24 | SNDK | 1.3B | 6.6% | 2026Q3 | wiki/investing/filings/SNDK/SNDK-xbrl.json R&D+rev TTM ending 2026-07-03 |
| 25 | GEV | 1.3B | 3.2% | 2026Q2 | wiki/investing/filings/GEV/GEV-xbrl.json R&D+rev TTM ending 2026-06-30 |
| 26 | MBLY | 1.1B | 55.8% | 2026Q2 | wiki/investing/filings/MBLY/MBLY-xbrl.json R&D+rev TTM ending 2026-06-27 |
| 27 | ETN | 845M | 2.8% | 2026Q2 | wiki/investing/filings/ETN/ETN-xbrl.json R&D+rev TTM ending 2026-06-30 |
| 28 | SMCI | 753M | 2.2% | 2026Q1 | wiki/investing/filings/SMCI/SMCI-xbrl.json R&D+rev TTM ending 2026-03-31 |
| 29 | COHR | 723M | 10.2% | 2026Q2 | wiki/investing/filings/COHR/COHR-xbrl.json R&D+rev TTM ending 2026-06-30 |
| 30 | PLTR | 641M | 10.4% | 2026Q2 | wiki/investing/filings/PLTR/PLTR-xbrl.json R&D+rev TTM ending 2026-06-30 |

## 6. Balance-sheet strength (Cash / LongTermDebt, latest snapshots)

Ratio uses latest reported cash and latest reported long-term debt (snapshot
periods cited per side; pairs whose debt snapshot is > 200 days older than
cash are excluded from ranking and listed below).

| Rank | Ticker | Cash | LTD | Cash/LTD | Cash period | LTD period | Src |
|---|---|---|---|---|---|---|---|
| 1 | RKLB | 2.1B | 13M | 162.2x | 2026-06-30 | 2026-06-30 | wiki/investing/filings/RKLB/RKLB-xbrl.json |
| 2 | AAOI | 500M | 34M | 14.7x | 2026-06-30 | 2025-12-31 | wiki/investing/filings/AAOI/AAOI-xbrl.json |
| 3 | MU | 25.0B | 8.8B | 2.8x | 2026-05-28 | 2025-11-27 | wiki/investing/filings/MU/MU-xbrl.json |
| 4 | TSLA | 15.2B | 7.7B | 2.0x | 2026-06-30 | 2026-06-30 | wiki/investing/filings/TSLA/TSLA-xbrl.json |
| 5 | NVDA | 13.2B | 8.5B | 1.6x | 2026-04-26 | 2026-04-26 | wiki/investing/filings/NVDA/NVDA-xbrl.json |
| 6 | WDC | 1.6B | 1.1B | 1.5x | 2026-07-03 | 2026-07-03 | wiki/investing/filings/WDC/WDC-xbrl.json |
| 7 | LRCX | 5.6B | 3.7B | 1.5x | 2026-06-28 | 2026-06-28 | wiki/investing/filings/LRCX/LRCX-xbrl.json |
| 8 | COIN | 8.6B | 5.9B | 1.5x | 2026-06-30 | 2026-06-30 | wiki/investing/filings/COIN/COIN-xbrl.json |
| 9 | GOOGL | 55.9B | 49.1B | 1.1x | 2026-06-30 | 2025-12-31 | wiki/investing/filings/GOOGL/GOOGL-xbrl.json |
| 10 | AEIS | 1.4B | 1.3B | 1.1x | 2026-06-30 | 2026-06-30 | wiki/investing/filings/AEIS/AEIS-xbrl.json |
| 11 | VRT | 2.8B | 2.9B | 1.0x | 2026-06-30 | 2026-06-30 | wiki/investing/filings/VRT/VRT-xbrl.json |
| 12 | MRVL | 3.8B | 5.0B | 0.8x | 2026-05-02 | 2026-05-02 | wiki/investing/filings/MRVL/MRVL-xbrl.json |
| 13 | AMZN | 78.2B | 133.0B | 0.6x | 2026-06-30 | 2026-06-30 | wiki/investing/filings/AMZN/AMZN-xbrl.json |
| 14 | MSFT | 20.9B | 40.3B | 0.5x | 2026-06-30 | 2026-06-30 | wiki/investing/filings/MSFT/MSFT-xbrl.json |
| 15 | AVAV | 377M | 748M | 0.5x | 2026-04-30 | 2026-04-30 | wiki/investing/filings/AVAV/AVAV-xbrl.json |
| 16 | NOW | 2.5B | 5.4B | 0.5x | 2026-06-30 | 2026-06-30 | wiki/investing/filings/NOW/NOW-xbrl.json |
| 17 | MP | 429M | 935M | 0.5x | 2026-06-30 | 2026-06-30 | wiki/investing/filings/MP/MP-xbrl.json |
| 18 | DELL | 11.6B | 31.2B | 0.4x | 2026-05-01 | 2026-05-01 | wiki/investing/filings/DELL/DELL-xbrl.json |
| 19 | COHR | 1.2B | 3.2B | 0.4x | 2026-06-30 | 2026-06-30 | wiki/investing/filings/COHR/COHR-xbrl.json |
| 20 | QCOM | 4.5B | 12.8B | 0.4x | 2026-06-28 | 2026-06-28 | wiki/investing/filings/QCOM/QCOM-xbrl.json |
| 21 | CSCO | 7.1B | 22.9B | 0.3x | 2026-04-25 | 2026-04-25 | wiki/investing/filings/CSCO/CSCO-xbrl.json |
| 22 | AVGO | 19.6B | 64.9B | 0.3x | 2026-05-03 | 2026-05-03 | wiki/investing/filings/AVGO/AVGO-xbrl.json |
| 23 | KLAC | 1.6B | 5.9B | 0.3x | 2026-06-30 | 2026-06-30 | wiki/investing/filings/KLAC/KLAC-xbrl.json |
| 24 | INTC | 12.9B | 46.6B | 0.3x | 2026-06-27 | 2025-12-27 | wiki/investing/filings/INTC/INTC-xbrl.json |
| 25 | HPE | 5.3B | 21.7B | 0.2x | 2026-04-30 | 2025-10-31 | wiki/investing/filings/HPE/HPE-xbrl.json |
| 26 | SNPS | 2.4B | 10.0B | 0.2x | 2026-04-30 | 2026-04-30 | wiki/investing/filings/SNPS/SNPS-xbrl.json |
| 27 | CRWV | 5.5B | 24.9B | 0.2x | 2026-06-30 | 2026-03-31 | wiki/investing/filings/CRWV/CRWV-xbrl.json |
| 28 | META | 15.5B | 83.7B | 0.2x | 2026-06-30 | 2026-06-30 | wiki/investing/filings/META/META-xbrl.json |
| 29 | MKSI | 454M | 2.5B | 0.2x | 2026-06-30 | 2026-06-30 | wiki/investing/filings/MKSI/MKSI-xbrl.json |
| 30 | LMT | 3.8B | 21.7B | 0.2x | 2026-06-28 | 2025-12-31 | wiki/investing/filings/LMT/LMT-xbrl.json |

Tickers with cash but no long-term-debt point (ratio undefined): ALAB, AMBA, ANET, CRDO, FLNC, HIMS, MBLY, MRAM, NEE, OKLO, PLTR, SMR, SNDK, SO, USAR.
Excluded from ranking -- latest LongTermDebt snapshot > 200 days older
than latest cash (stale debt side; listed with their LTD period):
  AMAT (2020-10-25); AMD (2021-12-25); APH (2018-03-31); BWXT (2015-12-31); DLR (2012-03-31); FN (2014-03-28); HII (2022-12-31); KTOS (2021-12-26); LHX (2019-09-27); LITE (2023-04-01); ONTO (2013-12-28); ORCL (2022-05-31); RTX (2024-12-31); SMCI (2023-06-30).

## 7. Data gaps and caveats

- Missing xbrl JSON entirely (8): ARM, ASML, ATEYY, CDNS, GFS, NBIS, QQQ, TSM.
- Sparse corpora (< 45 raw points): XRP (3); QNT (7); BTC (8); SPCX (10); BE (12); HUBB (12); AMKR (24); GD (29); IAU (30); GEV (36); HIMS (36); NEE (36); OKLO (41); DLR (42); USAR (42).
- No LongTermDebt points: ALAB, AMBA, ANET, BE, BTC, CRDO, FLNC, GEV, HIMS, IAU, LINK, MBLY, MRAM, NEE, OKLO, PLTR, QNT, SMR, SO, USAR, XRP.
- No R&D points: AEP, AMKR, AMZN, BAH, BE, BTC, CEG, DLR, DUK, EQIX, FN, HIMS, HUBB, IAU, LHX, MP, NEE, PPL, SO, VST, WBD, WDC, XRP.
- No Capex points: AMKR, BE, BTC, DLR, GD, GEV, HIMS, HPE, HUBB, IAU, KTOS, LRCX, NEE, QCOM, QNT, SPCX, XRP.
- EPS: zero points corpus-wide (scraper maps EarningsPerShareDiluted but EDGAR
  pulls returned none); all EPS fields are n/a by construction.
- Gross margin: not computable (no COGS concept scraped).
- Fiscal-calendar skew: rows align by period date, so "LQ" mixes calendar
  quarters across retailers/fund-like tickers with non-December year-ends.
- Stale/ragged windows: some tickers (e.g. AMKR, DUK, GD, NEE, IAU) have
  their freshest revenue point years old -- the corpus holds only what the
  last scrape returned; "latest" means latest in-file, not current.
- Suspect values (verify against the cited filing before use):
  netmargin_latest = NI within 45d of LQ exceeds 55% of LQ revenue (often a
  YTD row mislabeled as quarterly or an off-by-one-year period label);
  rev_yoy_extreme = YoY above +200% or below -100% (frequently rides on a
  derived/artifact quarter -- see Section 2 note).
    - GOOGL: netmargin_latest=0.937 at 2026Q2 (verify against cited filing)
    - IAU: rev_yoy_extreme=16.08 at 2013Q3 (verify against cited filing)
    - MU: netmargin_latest=0.681 at 2026Q2 (verify against cited filing)
    - MU: rev_yoy_extreme=3.46 at 2026Q2 (verify against cited filing)
    - NVDA: netmargin_latest=0.715 at 2026Q2 (verify against cited filing)
    - QNT: rev_yoy_extreme=2.79 at 2026Q2 (verify against cited filing)
    - SNDK: netmargin_latest=0.77 at 2026Q3 (verify against cited filing)
    - SNDK: rev_yoy_extreme=3.72 at 2026Q3 (verify against cited filing)
    - WDC: netmargin_latest=0.853 at 2026Q3 (verify against cited filing)
    - WDC: rev_yoy_extreme=-1.87 at 2026Q3 (verify against cited filing)

---

# Expansion: extended profiles, comparative rankings, AI-infrastructure footprint

GENERATED: 2026-08-24 (expansion pass). Sections 8-12 below were computed
from BOTH wiki/investing/filings/<T>/<T>-xbrl.json AND
<T>-xbrl-extended.json where the extended file exists (30 extended files
in corpus; LRCX and KLAC have NO extended file, so their operating-margin,
equity, share-count and computed-FCF fields are n/a by construction).
Price inputs come from the offline store Efforts/osanwe-v2-overhaul/_work/
factors.db table bars (yfinance closes, through 2026-08-24); market caps
from the cache noted in the header. No network was used.

Conventions carried over from Sections 1-7: flow metrics are quarterly,
"d" suffix marks a fiscal-Q4 value DERIVED as FY 10-K minus the three
reported 10-Q quarters, "n/a" means zero supporting XBRL points in the
corpus, and "latest" always means latest-in-file, not necessarily current.
New conventions: quarter columns are labeled by their period END date;
alignment tolerance between a metric point and its revenue quarter is
45 days; TTM here = sum over the last four reported revenue quarters
(requires >= 3 aligned points); margin trajectory compares the mean of
the newer half of the margin series against the mean of the older half
(band +/-0.75 pt = flat).

## 8. Method addendum for Sections 9-12

- Concept map, per side:
  - base file: Revenue OR Revenues; NetIncome; Cash (cash-and-equivalents
    carrying value); LongTermDebt; Capex; R&D.
  - extended file (concepts block): GrossProfit; OperatingIncomeLoss;
    StockholdersEquity; NetCashProvidedByUsedInOperatingActivities (OCF);
    PaymentsToAcquirePropertyPlantAndEquipment (capex, merged with base
    Capex, latest filing wins per period); ShareIssued; FreeCashFlow_
    computed (= OCF - capex, precomputed upstream; patch notes flag
    ShareIssued <= CommonStockSharesOutstanding substitution).
- Duplicate control: identical (period, form) rows appearing twice because
  of restatement re-filings collapse to the latest FILED row.
- Fiscal-quarter reconstruction: 10-Q rows stand alone; a FY (10-K/20-F)
  row contributes a derived Q4 = FY - sum(10-Qs whose period falls in the
  trailing 365-day window ending at the FY date), requiring >= 3 such
  10-Qs. Matches the Q4d values already used in Section 2.
- Money format: T = trillion, B = billion, M = million, K = thousand.
- EPS remains not computable corpus-wide (see header note).
- Rounding: displayed values are rounded; ratios are computed on unrounded
  values, so re-derived numbers may differ in the last decimal.

## 9. Extended financial profiles -- top 30 by market cap

Order follows the Section 2 market-cap ranking. Each block reconstructs
the statement stack for the LAST FOUR reported revenue quarters (oldest
to newest, left to right; period-end dates are the column heads). A cell
can be blank/n/a even mid-table when the extended pull missed that quarter.
Balance-sheet snapshots cite their own as-of dates, which need not match
the income-statement window.

### 9.1 NVDA -- NVIDIA CORP (mkt cap 5.20T)
| Metric ($M) | 2025-07-27 | 2025-10-26 | 2026-01-25d | 2026-04-26 |
|---|---|---|---|---|
| Revenue | 46743 | 57006 | 68127 | 81615 |
| Gross profit | 33853 | 41849 | 51093 | 61157 |
| Operating income | 28440 | 36010 | 44299 | 53536 |
| Net income | 26422 | 31910 | n/a | 58321 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-07-27 | 2025-10-26 | 2026-01-25d | 2026-04-26 |
|---|---|---|---|---|
| Gross margin | +72.4 | +73.4 | +75.0 | +74.9 |
| Operating margin | +60.8 | +63.2 | +65.0 | +65.6 |
| Net margin | +56.5 | +56.0 | n/a | +71.5 |

Balance-sheet snapshot: Cash 13.2B (2026-04-26); LTD 8.5B (2026-04-26); Equity 195.5B (2026-04-26).
  Ratios: LTD/Equity 0.04x; net debt (LTD-Cash) -4.8B; Cash/Equity 0.07x; implied EV-ish (Eq+LTD-Cash) 200.2B.

Cash flow (per quarter: OCF | capex | FCF):
  - 2025-07-27: OCF 42.8B / capex 3.1B / FCF 39.7B
  - 2025-10-26: OCF 66.5B / capex 4.8B / FCF 61.8B
  - 2026-01-25d: OCF n/a / capex n/a / FCF 96.7B
  - 2026-04-26: OCF 50.3B / capex 1.8B / FCF 48.6B
Dilution: shares issued 24477M (2025-01-26) -> 24304M (2026-01-25), -0.71% over 364 days.
R&D intensity: 2025-07-27 4291M (9.2%); 2025-10-26 4705M (8.3%); 2026-01-25 5512M (8.1%); 2026-04-26 6321M (7.7%).
Src: wiki/investing/filings/NVDA/NVDA-xbrl.json + NVDA-xbrl-extended.json

### 9.2 GOOGL -- ALPHABET INC (mkt cap 4.22T)
| Metric ($M) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Revenue | 102346 | 113828 | 109896 | 119796 |
| Gross profit | n/a | n/a | n/a | n/a |
| Operating income | 31228 | 35934 | 39696 | 40770 |
| Net income | 34979 | n/a | 62578 | 112193 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Gross margin | n/a | n/a | n/a | n/a |
| Operating margin | +30.5 | +31.6 | +36.1 | +34.0 |
| Net margin | +34.2 | n/a | +56.9 | +93.7 |

Balance-sheet snapshot: Cash 55.9B (2026-06-30); LTD 49.1B (2025-12-31); Equity 640.5B (2026-06-30).
  Ratios: LTD/Equity 0.08x; net debt (LTD-Cash) -6.8B; Cash/Equity 0.09x; implied EV-ish (Eq+LTD-Cash) 647.3B.

Cash flow (per quarter: OCF | capex | FCF):
  - 2025-09-30: OCF 112.3B / capex 63.6B / FCF 48.7B
  - 2025-12-31d: OCF n/a / capex n/a / FCF 73.3B
  - 2026-03-31: OCF 45.8B / capex 35.7B / FCF 10.1B
  - 2026-06-30: OCF 84.9B / capex 80.6B / FCF 4.3B
Dilution: shares issued 12116M (2026-03-31) -> 12230M (2026-06-30), +0.94% over 91 days.
R&D intensity: 2025-09-30 15151M (14.8%); 2025-12-31 18572M (16.3%); 2026-03-31 17032M (15.5%); 2026-06-30 18219M (15.2%).
Src: wiki/investing/filings/GOOGL/GOOGL-xbrl.json + GOOGL-xbrl-extended.json

### 9.3 MSFT -- MICROSOFT CORP (mkt cap 3.59T)
| Metric ($M) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30d |
|---|---|---|---|---|
| Revenue | 77673 | 81273 | 82886 | 90007 |
| Gross profit | 53630 | 55295 | 56058 | 60482 |
| Operating income | 37961 | 38275 | 38398 | 40603 |
| Net income | 27747 | 38458 | 31778 | 35766 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30d |
|---|---|---|---|---|
| Gross margin | +69.0 | +68.0 | +67.6 | +67.2 |
| Operating margin | +48.9 | +47.1 | +46.3 | +45.1 |
| Net margin | +35.7 | +47.3 | +38.3 | +39.7 |

Balance-sheet snapshot: Cash 20.9B (2026-06-30); LTD 40.3B (2026-06-30); Equity 442.4B (2026-06-30).
  Ratios: LTD/Equity 0.09x; net debt (LTD-Cash) 19.4B; Cash/Equity 0.05x; implied EV-ish (Eq+LTD-Cash) 423.0B.

Cash flow (per quarter: OCF | capex | FCF):
  - 2025-09-30: OCF 45.1B / capex 19.4B / FCF 25.7B
  - 2025-12-31: OCF 35.8B / capex 29.9B / FCF 5.9B
  - 2026-03-31: OCF 46.7B / capex 30.9B / FCF 15.8B
  - 2026-06-30d: OCF 55.4B / capex 35.8B / FCF 67.0B
Dilution: shares issued 7429M (2026-03-31) -> 7427M (2026-06-30), -0.03% over 91 days.
R&D intensity: 2025-09-30 8146M (10.5%); 2025-12-31 8504M (10.5%); 2026-03-31 8915M (10.8%); 2026-06-30 9997M (11.1%).
Src: wiki/investing/filings/MSFT/MSFT-xbrl.json + MSFT-xbrl-extended.json

### 9.4 AMZN -- AMAZON.COM INC (mkt cap 2.79T)
| Metric ($M) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Revenue | 180169 | 213386 | 181519 | 200606 |
| Gross profit | n/a | n/a | n/a | n/a |
| Operating income | 17422 | 24977 | 23852 | 27461 |
| Net income | 21187 | n/a | 30255 | 62647 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Gross margin | n/a | n/a | n/a | n/a |
| Operating margin | +9.7 | +11.7 | +13.1 | +13.7 |
| Net margin | +11.8 | n/a | +16.7 | +31.2 |

Balance-sheet snapshot: Cash 78.2B (2026-06-30); LTD 133.0B (2026-06-30); Equity 551.6B (2026-06-30).
  Ratios: LTD/Equity 0.24x; net debt (LTD-Cash) 54.8B; Cash/Equity 0.14x; implied EV-ish (Eq+LTD-Cash) 496.8B.

Cash flow (per quarter: OCF | capex | FCF):
  - 2025-09-30: OCF 35.5B / capex 35.1B / FCF 430M
  - 2025-12-31d: OCF 54.5B / capex 39.5B / FCF 7.7B
  - 2026-03-31: OCF 26.0B / capex 44.2B / FCF -18.2B
  - 2026-06-30: OCF 45.4B / capex 54.2B / FCF -8.8B
Dilution: shares issued 10754M (2026-03-31) -> 10783M (2026-06-30), +0.27% over 91 days.
R&D intensity: n/a (no R&D points in window).
Src: wiki/investing/filings/AMZN/AMZN-xbrl.json + AMZN-xbrl-extended.json

### 9.5 AVGO -- BROADCOM INC (mkt cap 1.75T)
| Metric ($M) | 2025-08-03 | 2025-11-02d | 2026-02-01 | 2026-05-03 |
|---|---|---|---|---|
| Revenue | 15952 | 18015 | 19311 | 22187 |
| Gross profit | 10703 | 12249 | 13157 | 15415 |
| Operating income | 5887 | 7508 | 8563 | 10788 |
| Net income | n/a | n/a | n/a | n/a |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-08-03 | 2025-11-02d | 2026-02-01 | 2026-05-03 |
|---|---|---|---|---|
| Gross margin | +67.1 | +68.0 | +68.1 | +69.5 |
| Operating margin | +36.9 | +41.7 | +44.3 | +48.6 |
| Net margin | n/a | n/a | n/a | n/a |

Balance-sheet snapshot: Cash 19.6B (2026-05-03); LTD 64.9B (2026-05-03); Equity 24.9B (2019-11-03 STALE).
  Ratios: net debt (LTD-Cash) 45.3B.

Cash flow (per quarter: OCF | capex | FCF):
  - 2025-08-03: OCF 19.8B / capex 386M / FCF 19.4B
  - 2025-11-02d: OCF n/a / capex n/a / FCF 26.9B
  - 2026-02-01: OCF 8.3B / capex 250M / FCF 8.0B
  - 2026-05-03: OCF 18.8B / capex 481M / FCF 18.3B
Dilution: shares issued 4736M (2026-02-01) -> 4758M (2026-05-03), +0.46% over 91 days.
R&D intensity: 2025-08-03 3050M (19.1%); 2025-11-02 2981M (16.5%); 2026-02-01 2965M (15.4%); 2026-05-03 2995M (13.5%).
Src: wiki/investing/filings/AVGO/AVGO-xbrl.json + AVGO-xbrl-extended.json

### 9.6 TSLA -- TESLA INC (mkt cap 1.43T)
| Metric ($M) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Revenue | 28095 | 24901 | 22387 | 28236 |
| Gross profit | 5054 | 5009 | 4720 | 4751 |
| Operating income | 1624 | 1409 | 941 | 398 |
| Net income | 1373 | 840 | 477 | 1114 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Gross margin | +18.0 | +20.1 | +21.1 | +16.8 |
| Operating margin | +5.8 | +5.7 | +4.2 | +1.4 |
| Net margin | +4.9 | +3.4 | +2.1 | +3.9 |

Balance-sheet snapshot: Cash 15.2B (2026-06-30); LTD 7.7B (2026-06-30); Equity 86.9B (2026-06-30).
  Ratios: LTD/Equity 0.09x; net debt (LTD-Cash) -7.5B; Cash/Equity 0.18x; implied EV-ish (Eq+LTD-Cash) 94.4B.

Cash flow (per quarter: OCF | capex | FCF):
  - 2025-09-30: OCF 10.9B / capex 6.1B / FCF 4.8B
  - 2025-12-31d: OCF n/a / capex n/a / FCF 6.2B
  - 2026-03-31: OCF 3.9B / capex 2.5B / FCF 1.4B
  - 2026-06-30: OCF 8.6B / capex 8.3B / FCF 352M
Dilution: shares issued 3755M (2026-03-31) -> 3949M (2026-06-30), +5.17% over 91 days.
R&D intensity: 2025-09-30 1630M (5.8%); 2025-12-31 1783M (7.2%); 2026-03-31 1946M (8.7%); 2026-06-30 2371M (8.4%).
Src: wiki/investing/filings/TSLA/TSLA-xbrl.json + TSLA-xbrl-extended.json

### 9.7 META -- META PLATFORMS INC (mkt cap 1.40T)
| Metric ($M) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Revenue | 51242 | 59894 | 56311 | 60801 |
| Gross profit | 42036 | 48988 | 46093 | 49471 |
| Operating income | 20535 | 24745 | 22872 | 18775 |
| Net income | 2709 | n/a | 26773 | 15848 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Gross margin | +82.0 | +81.8 | +81.9 | +81.4 |
| Operating margin | +40.1 | +41.3 | +40.6 | +30.9 |
| Net margin | +5.3 | n/a | +47.5 | +26.1 |

Balance-sheet snapshot: Cash 15.5B (2026-06-30); LTD 83.7B (2026-06-30); Equity 261.2B (2026-06-30).
  Ratios: LTD/Equity 0.32x; net debt (LTD-Cash) 68.2B; Cash/Equity 0.06x; implied EV-ish (Eq+LTD-Cash) 193.0B.

Cash flow (per quarter: OCF | capex | FCF):
  - 2025-09-30: OCF 79.6B / capex 48.3B / FCF 31.3B
  - 2025-12-31d: OCF n/a / capex n/a / FCF 46.1B
  - 2026-03-31: OCF 32.2B / capex 19.0B / FCF 13.2B
  - 2026-06-30: OCF 64.1B / capex 49.1B / FCF 15.0B
Dilution: shares issued 2564M (2026-03-31) -> 2566M (2026-06-30), +0.08% over 91 days.
R&D intensity: 2025-09-30 15144M (29.6%); 2025-12-31 17136M (28.6%); 2026-03-31 17699M (31.4%); 2026-06-30 21656M (35.6%).
Src: wiki/investing/filings/META/META-xbrl.json + META-xbrl-extended.json

### 9.8 MU -- MICRON TECHNOLOGY (mkt cap 1.09T)
| Metric ($M) | 2025-08-28d | 2025-11-27 | 2026-02-26 | 2026-05-28 |
|---|---|---|---|---|
| Revenue | 11315 | 13643 | 23860 | 41456 |
| Gross profit | 5054 | 7646 | 17755 | 35056 |
| Operating income | 3654 | 6136 | 16135 | 33318 |
| Net income | 3201 | 5240 | 13785 | 28243 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-08-28d | 2025-11-27 | 2026-02-26 | 2026-05-28 |
|---|---|---|---|---|
| Gross margin | +44.7 | +56.0 | +74.4 | +84.6 |
| Operating margin | +32.3 | +45.0 | +67.6 | +80.4 |
| Net margin | +28.3 | +38.4 | +57.8 | +68.1 |

Balance-sheet snapshot: Cash 25.0B (2026-05-28); LTD 8.8B (2025-11-27); Equity 100.7B (2026-05-28).
  Ratios: LTD/Equity 0.09x; net debt (LTD-Cash) -16.2B; Cash/Equity 0.25x; implied EV-ish (Eq+LTD-Cash) 116.9B.

Cash flow (per quarter: OCF | capex | FCF):
  - 2025-08-28d: OCF n/a / capex n/a / FCF 1.7B
  - 2025-11-27: OCF 8.4B / capex 5.4B / FCF 3.0B
  - 2026-02-26: OCF 20.3B / capex 11.8B / FCF 8.5B
  - 2026-05-28: OCF 45.7B / capex 19.6B / FCF 26.1B
Dilution: shares issued 1128M (2026-02-26) -> 1129M (2026-05-28), +0.09% over 91 days.
R&D intensity: 2025-08-28 1047M (9.3%); 2025-11-27 1171M (8.6%); 2026-02-26 1250M (5.2%); 2026-05-28 1316M (3.2%).
Src: wiki/investing/filings/MU/MU-xbrl.json + MU-xbrl-extended.json

### 9.9 AMD -- ADVANCED MICRO DEVICES (mkt cap 772.6B)
| Metric ($M) | 2025-09-27 | 2025-12-27d | 2026-03-28 | 2026-06-27 |
|---|---|---|---|---|
| Revenue | 9246 | 10270 | 10253 | 11536 |
| Gross profit | 4780 | 5577 | 5416 | 6203 |
| Operating income | 1270 | 1752 | 1476 | 1990 |
| Net income | 1243 | 1511 | 1383 | 2297 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-09-27 | 2025-12-27d | 2026-03-28 | 2026-06-27 |
|---|---|---|---|---|
| Gross margin | +51.7 | +54.3 | +52.8 | +53.8 |
| Operating margin | +13.7 | +17.1 | +14.4 | +17.3 |
| Net margin | +13.4 | +14.7 | +13.5 | +19.9 |

Balance-sheet snapshot: Cash 5.1B (2026-06-27); LTD 1M (2021-12-25); Equity 67.2B (2026-06-27).
  Ratios: LTD/Equity 0.00x; net debt (LTD-Cash) -5.1B; Cash/Equity 0.08x; implied EV-ish (Eq+LTD-Cash) 72.3B.

Cash flow (per quarter: OCF | capex | FCF):
  - 2025-09-27: OCF 5.1B / capex 752M / FCF 4.4B
  - 2025-12-27d: OCF n/a / capex n/a / FCF 6.7B
  - 2026-03-28: OCF 3.0B / capex 389M / FCF 2.6B
  - 2026-06-27: OCF 5.3B / capex 1.2B / FCF 4.1B
Dilution: shares issued 1630M (2026-03-28) -> 1632M (2026-06-27), +0.12% over 91 days.
R&D intensity: 2025-09-27 2139M (23.1%); 2025-12-27 2330M (22.7%); 2026-03-28 2397M (23.4%); 2026-06-27 2528M (21.9%).
Src: wiki/investing/filings/AMD/AMD-xbrl.json + AMD-xbrl-extended.json

### 9.10 INTC -- INTEL CORP (mkt cap 473.3B)
| Metric ($M) | 2025-09-27 | 2025-12-27d | 2026-03-28 | 2026-06-27 |
|---|---|---|---|---|
| Revenue | 13653 | 13674 | 13577 | 16128 |
| Gross profit | n/a | n/a | n/a | n/a |
| Operating income | n/a | n/a | n/a | n/a |
| Net income | 4063 | n/a | -3728 | -11033 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-09-27 | 2025-12-27d | 2026-03-28 | 2026-06-27 |
|---|---|---|---|---|
| Gross margin | n/a | n/a | n/a | n/a |
| Operating margin | n/a | n/a | n/a | n/a |
| Net margin | +29.8 | n/a | -27.5 | -68.4 |

Balance-sheet snapshot: Cash 12.9B (2026-06-27); LTD 46.6B (2025-12-27); StockholdersEquity n/a.
  Ratios: net debt (LTD-Cash) 33.7B.

Cash flow (per quarter: OCF | capex | FCF):
  - 2026-03-28: OCF n/a / capex 3.6B / FCF n/a
Dilution: fewer than two ShareIssued points (n/a).
R&D intensity: 2025-09-27 3231M (23.7%); 2025-12-27 3219M (23.5%); 2026-03-28 3375M (24.9%); 2026-06-27 3368M (20.9%).
Src: wiki/investing/filings/INTC/INTC-xbrl.json

### 9.11 CSCO -- CISCO SYSTEMS (mkt cap 437.7B)
| Metric ($M) | 2025-07-26d | 2025-10-25 | 2026-01-24 | 2026-04-25 |
|---|---|---|---|---|
| Revenue | 14673 | 14883 | 15349 | 15841 |
| Gross profit | n/a | n/a | n/a | n/a |
| Operating income | n/a | n/a | n/a | n/a |
| Net income | 2550 | 2860 | 3175 | 3373 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-07-26d | 2025-10-25 | 2026-01-24 | 2026-04-25 |
|---|---|---|---|---|
| Gross margin | n/a | n/a | n/a | n/a |
| Operating margin | n/a | n/a | n/a | n/a |
| Net margin | +17.4 | +19.2 | +20.7 | +21.3 |

Balance-sheet snapshot: Cash 7.1B (2026-04-25); LTD 22.9B (2026-04-25); StockholdersEquity n/a.
  Ratios: net debt (LTD-Cash) 15.8B.

Cash flow (per quarter: OCF | capex | FCF):
  - 2025-10-25: OCF n/a / capex 323M / FCF n/a
Dilution: fewer than two ShareIssued points (n/a).
R&D intensity: 2025-07-26 2380M (16.2%); 2025-10-25 2400M (16.1%); 2026-01-24 2355M (15.3%); 2026-04-25 2377M (15.0%).
Src: wiki/investing/filings/CSCO/CSCO-xbrl.json

### 9.12 PLTR -- PALANTIR TECHNOLOGIES (mkt cap 432.4B)
| Metric ($M) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Revenue | 1181 | 1407 | 1633 | 1935 |
| Gross profit | 974 | 1191 | 1417 | 1639 |
| Operating income | 393 | 575 | 754 | 912 |
| Net income | 476 | n/a | 871 | 1062 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Gross margin | +82.4 | +84.6 | +86.8 | +84.7 |
| Operating margin | +33.3 | +40.9 | +46.2 | +47.1 |
| Net margin | +40.3 | n/a | +53.3 | +54.9 |

Balance-sheet snapshot: Cash 2.0B (2026-06-30); LongTermDebt n/a; Equity 9.8B (2026-06-30).
  Ratios: Cash/Equity 0.21x.

Cash flow (per quarter: OCF | capex | FCF):
  - 2025-09-30: OCF 1.4B / capex 21M / FCF 1.3B
  - 2025-12-31d: OCF n/a / capex n/a / FCF 2.1B
  - 2026-03-31: OCF 899M / capex 7M / FCF 892M
  - 2026-06-30: OCF 2.1B / capex 22M / FCF 2.1B
Dilution: shares issued 2397M (2026-03-31) -> 2403M (2026-06-30), +0.24% over 91 days.
R&D intensity: 2025-09-30 144M (12.2%); 2025-12-31 144M (10.2%); 2026-03-31 161M (9.9%); 2026-06-30 193M (9.9%).
Src: wiki/investing/filings/PLTR/PLTR-xbrl.json + PLTR-xbrl-extended.json

### 9.13 ORCL -- ORACLE CORP (mkt cap 421.9B)
| Metric ($M) | 2025-08-31 | 2025-11-30 | 2026-02-28 | 2026-05-31d |
|---|---|---|---|---|
| Revenue | 14926 | 16058 | 17190 | 19183 |
| Gross profit | n/a | n/a | n/a | n/a |
| Operating income | n/a | n/a | n/a | n/a |
| Net income | 2927 | 6135 | 3721 | 4304 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-08-31 | 2025-11-30 | 2026-02-28 | 2026-05-31d |
|---|---|---|---|---|
| Gross margin | n/a | n/a | n/a | n/a |
| Operating margin | n/a | n/a | n/a | n/a |
| Net margin | +19.6 | +38.2 | +21.6 | +22.4 |

Balance-sheet snapshot: Cash 31.3B (2026-05-31); LTD 0 (2022-05-31); StockholdersEquity n/a.
  Ratios: net debt (LTD-Cash) -31.3B.

Cash flow (per quarter: OCF | capex | FCF):
  - 2025-08-31: OCF n/a / capex 8.5B / FCF n/a
Dilution: fewer than two ShareIssued points (n/a).
R&D intensity: 2025-08-31 2491M (16.7%); 2025-11-30 2561M (15.9%); 2026-02-28 2607M (15.2%); 2026-05-31 2613M (13.6%).
Src: wiki/investing/filings/ORCL/ORCL-xbrl.json

### 9.14 LRCX -- LAM RESEARCH (mkt cap 392.9B)
| Metric ($M) | 2025-09-28 | 2025-12-28 | 2026-03-29 | 2026-06-28d |
|---|---|---|---|---|
| Revenue | 5324 | 5345 | 5841 | 6722 |
| Gross profit | n/a | n/a | n/a | n/a |
| Operating income | n/a | n/a | n/a | n/a |
| Net income | 1569 | 1594 | 1825 | 2277 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-09-28 | 2025-12-28 | 2026-03-29 | 2026-06-28d |
|---|---|---|---|---|
| Gross margin | n/a | n/a | n/a | n/a |
| Operating margin | n/a | n/a | n/a | n/a |
| Net margin | +29.5 | +29.8 | +31.2 | +33.9 |

Balance-sheet snapshot: Cash 5.6B (2026-06-28); LTD 3.7B (2026-06-28); StockholdersEquity n/a.
  Ratios: net debt (LTD-Cash) -1.9B.

Cash flow: n/a (no OCF/capex/FCF points aligned to the window).
Dilution: fewer than two ShareIssued points (n/a).
R&D intensity: 2025-09-28 576M (10.8%); 2025-12-28 573M (10.7%); 2026-03-29 583M (10.0%); 2026-06-28 643M (9.6%).
Src: wiki/investing/filings/LRCX/LRCX-xbrl.json

### 9.15 AMAT -- APPLIED MATERIALS (mkt cap 390.9B)
| Metric ($M) | 2025-10-26d | 2026-01-25 | 2026-04-26 | 2026-07-26 |
|---|---|---|---|---|
| Revenue | 6800 | 7012 | 7910 | 9115 |
| Gross profit | n/a | n/a | n/a | n/a |
| Operating income | n/a | n/a | n/a | n/a |
| Net income | 1897 | 2026 | 2806 | 2538 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-10-26d | 2026-01-25 | 2026-04-26 | 2026-07-26 |
|---|---|---|---|---|
| Gross margin | n/a | n/a | n/a | n/a |
| Operating margin | n/a | n/a | n/a | n/a |
| Net margin | +27.9 | +28.9 | +35.5 | +27.8 |

Balance-sheet snapshot: Cash 7.0B (2026-07-26); LTD 5.4B (2020-10-25); StockholdersEquity n/a.
  Ratios: net debt (LTD-Cash) -1.6B.

Cash flow (per quarter: OCF | capex | FCF):
  - 2026-01-25: OCF n/a / capex 646M / FCF n/a
Dilution: fewer than two ShareIssued points (n/a).
R&D intensity: 2025-10-26 917M (13.5%); 2026-01-25 928M (13.2%); 2026-04-26 1027M (13.0%); 2026-07-26 1100M (12.1%).
Src: wiki/investing/filings/AMAT/AMAT-xbrl.json

### 9.16 DELL -- DELL TECHNOLOGIES (mkt cap 285.6B)
| Metric ($M) | 2025-08-01 | 2025-10-31 | 2026-01-30d | 2026-05-01 |
|---|---|---|---|---|
| Revenue | 29776 | 27005 | 33379 | 43842 |
| Gross profit | n/a | n/a | n/a | n/a |
| Operating income | n/a | n/a | n/a | n/a |
| Net income | 1164 | 1548 | n/a | 3438 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-08-01 | 2025-10-31 | 2026-01-30d | 2026-05-01 |
|---|---|---|---|---|
| Gross margin | n/a | n/a | n/a | n/a |
| Operating margin | n/a | n/a | n/a | n/a |
| Net margin | +3.9 | +5.7 | n/a | +7.8 |

Balance-sheet snapshot: Cash 11.6B (2026-05-01); LTD 31.2B (2026-05-01); StockholdersEquity n/a.
  Ratios: net debt (LTD-Cash) 19.6B.

Cash flow (per quarter: OCF | capex | FCF):
  - 2026-05-01: OCF n/a / capex 963M / FCF n/a
Dilution: fewer than two ShareIssued points (n/a).
R&D intensity: 2025-08-01 785M (2.6%); 2025-10-31 752M (2.8%); 2026-01-30 797M (2.4%); 2026-05-01 983M (2.2%).
Src: wiki/investing/filings/DELL/DELL-xbrl.json

### 9.17 RTX -- RTX CORP (mkt cap 282.9B)
| Metric ($M) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Revenue | 22478 | 24238 | 22076 | 24708 |
| Gross profit | n/a | n/a | n/a | n/a |
| Operating income | n/a | n/a | n/a | n/a |
| Net income | 1918 | 1622 | 2059 | 2139 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Gross margin | n/a | n/a | n/a | n/a |
| Operating margin | n/a | n/a | n/a | n/a |
| Net margin | +8.5 | +6.7 | +9.3 | +8.7 |

Balance-sheet snapshot: Cash 8.3B (2026-06-30); LTD 41.1B (2024-12-31); StockholdersEquity n/a.
  Ratios: net debt (LTD-Cash) 32.8B.

Cash flow (per quarter: OCF | capex | FCF):
  - 2026-03-31: OCF n/a / capex 546M / FCF n/a
Dilution: fewer than two ShareIssued points (n/a).
R&D intensity: 2025-09-30 684M (3.0%); 2025-12-31 789M (3.3%); 2026-03-31 627M (2.8%); 2026-06-30 726M (2.9%).
Src: wiki/investing/filings/RTX/RTX-xbrl.json

### 9.18 GEV -- GE VERNOVA (mkt cap 254.8B)
| Metric ($M) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Revenue | 9969 | 10956 | 9339 | 11104 |
| Gross profit | 1897 | 2322 | 1781 | 2360 |
| Operating income | 366 | 601 | 179 | 653 |
| Net income | 452 | 3664 | 4745 | 668 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Gross margin | +19.0 | +21.2 | +19.1 | +21.3 |
| Operating margin | +3.7 | +5.5 | +1.9 | +5.9 |
| Net margin | +4.5 | +33.4 | +50.8 | +6.0 |

Balance-sheet snapshot: Cash n/a; LongTermDebt n/a; Equity 12.0B (2026-06-30).

Cash flow (per quarter: OCF | capex | FCF):
  - 2025-09-30: OCF 2.5B / capex 606M / FCF 1.9B
  - 2025-12-31d: OCF n/a / capex 126M / FCF 3.7B
  - 2026-03-31: OCF 5.2B / capex 397M / FCF 4.8B
  - 2026-06-30: OCF 10.7B / capex 783M / FCF 9.9B
Dilution: shares issued 269M (2026-03-31) -> 266M (2026-06-30), -0.89% over 91 days.
R&D intensity: 2025-09-30 310M (3.1%); 2025-12-31 366M (3.3%); 2026-03-31 304M (3.3%); 2026-06-30 334M (3.0%).
Src: wiki/investing/filings/GEV/GEV-xbrl.json + GEV-xbrl-extended.json

### 9.19 KLAC -- KLA CORP (mkt cap 240.4B)
| Metric ($M) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30d |
|---|---|---|---|---|
| Revenue | 3210 | 3297 | 3415 | 3658 |
| Gross profit | n/a | n/a | n/a | n/a |
| Operating income | n/a | n/a | n/a | n/a |
| Net income | 1121 | 1146 | 1201 | 1363 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-09-30 | 2025-12-31 | 2026-03-31 | 2026-06-30d |
|---|---|---|---|---|
| Gross margin | n/a | n/a | n/a | n/a |
| Operating margin | n/a | n/a | n/a | n/a |
| Net margin | +34.9 | +34.7 | +35.2 | +37.3 |

Balance-sheet snapshot: Cash 1.6B (2026-06-30); LTD 5.9B (2026-06-30); StockholdersEquity n/a.
  Ratios: net debt (LTD-Cash) 4.2B.

Cash flow (per quarter: OCF | capex | FCF):
  - 2025-09-30: OCF n/a / capex 96M / FCF n/a
Dilution: fewer than two ShareIssued points (n/a).
R&D intensity: 2025-09-30 360M (11.2%); 2025-12-31 384M (11.6%); 2026-03-31 389M (11.4%); 2026-06-30 399M (10.9%).
Src: wiki/investing/filings/KLAC/KLAC-xbrl.json

### 9.20 ANET -- ARISTA NETWORKS (mkt cap 237.9B)
| Metric ($M) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Revenue | 2308 | 2488 | 2709 | 3036 |
| Gross profit | 1490 | 1564 | 1677 | 1910 |
| Operating income | 978 | 1033 | 1158 | 1378 |
| Net income | 853 | n/a | 1023 | 1213 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Gross margin | +64.6 | +62.9 | +61.9 | +62.9 |
| Operating margin | +42.4 | +41.5 | +42.7 | +45.4 |
| Net margin | +37.0 | n/a | +37.8 | +40.0 |

Balance-sheet snapshot: Cash 2.3B (2026-06-30); LongTermDebt n/a; Equity 14.8B (2026-06-30).
  Ratios: Cash/Equity 0.15x.

Cash flow (per quarter: OCF | capex | FCF):
  - 2025-09-30: OCF 3.1B / capex 82M / FCF 3.0B
  - 2026-03-31: OCF 1.7B / capex 54M / FCF 1.6B
  - 2026-06-30: OCF 2.8B / capex 84M / FCF 2.7B
Dilution: shares issued 1259M (2026-03-31) -> 1261M (2026-06-30), +0.16% over 91 days.
R&D intensity: 2025-09-30 326M (14.1%); 2025-12-31 348M (14.0%); 2026-03-31 344M (12.7%); 2026-06-30 348M (11.5%).
Src: wiki/investing/filings/ANET/ANET-xbrl.json + ANET-xbrl-extended.json

### 9.21 SNDK -- SANDISK CORP (mkt cap 233.7B)
| Metric ($M) | 2025-10-03 | 2026-01-02 | 2026-04-03 | 2026-07-03d |
|---|---|---|---|---|
| Revenue | 2308 | 3025 | 5950 | 8965 |
| Gross profit | 687 | 1541 | 4662 | 7582 |
| Operating income | 176 | 1065 | 4111 | 7037 |
| Net income | 112 | 803 | 3615 | 6903 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-10-03 | 2026-01-02 | 2026-04-03 | 2026-07-03d |
|---|---|---|---|---|
| Gross margin | +29.8 | +50.9 | +78.4 | +84.6 |
| Operating margin | +7.6 | +35.2 | +69.1 | +78.5 |
| Net margin | +4.9 | +26.5 | +60.8 | +77.0 |

Balance-sheet snapshot: Cash 4.8B (2026-07-03); LTD 0 (2026-07-03); Equity 15.7B (2026-07-03).
  Ratios: LTD/Equity 0.00x; net debt (LTD-Cash) -4.8B; Cash/Equity 0.30x; implied EV-ish (Eq+LTD-Cash) 20.5B.

Cash flow (per quarter: OCF | capex | FCF):
  - 2025-10-03: OCF 488M / capex 50M / FCF 438M
  - 2026-01-02: OCF 1.5B / capex 89M / FCF 1.4B
  - 2026-04-03: OCF 4.5B / capex 134M / FCF 4.4B
  - 2026-07-03d: OCF 5.1B / capex n/a / FCF 11.5B
Dilution: shares issued 148M (2026-04-03) -> 146M (2026-07-03), -1.35% over 91 days.
R&D intensity: 2025-10-03 316M (13.7%); 2026-01-02 327M (10.8%); 2026-04-03 337M (5.7%); 2026-07-03 348M (3.9%).
Src: wiki/investing/filings/SNDK/SNDK-xbrl.json + SNDK-xbrl-extended.json

### 9.22 MRVL -- MARVELL TECHNOLOGY (mkt cap 212.8B)
| Metric ($M) | 2025-08-02 | 2025-11-01 | 2026-01-31d | 2026-05-02 |
|---|---|---|---|---|
| Revenue | 2006 | 2074 | 2219 | 2418 |
| Gross profit | 1011 | 1070 | 1148 | 1261 |
| Operating income | 290 | 358 | 404 | 339 |
| Net income | 195 | 1901 | n/a | 34 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-08-02 | 2025-11-01 | 2026-01-31d | 2026-05-02 |
|---|---|---|---|---|
| Gross margin | +50.4 | +51.6 | +51.7 | +52.1 |
| Operating margin | +14.5 | +17.2 | +18.2 | +14.0 |
| Net margin | +9.7 | +91.7 | n/a | +1.4 |

Balance-sheet snapshot: Cash 3.8B (2026-05-02); LTD 5.0B (2026-05-02); Equity 18.2B (2026-05-02).
  Ratios: LTD/Equity 0.27x; net debt (LTD-Cash) 1.1B; Cash/Equity 0.21x; implied EV-ish (Eq+LTD-Cash) 17.1B.

Cash flow (per quarter: OCF | capex | FCF):
  - 2025-08-02: OCF 794M / capex 166M / FCF 628M
  - 2025-11-01: OCF 1.4B / capex 240M / FCF 1.1B
  - 2026-01-31d: OCF n/a / capex n/a / FCF 1.4B
  - 2026-05-02: OCF 639M / capex 156M / FCF 483M
Dilution: shares issued 866M (2025-02-01) -> 847M (2026-01-31), -2.16% over 364 days.
R&D intensity: 2025-08-02 519M (25.9%); 2025-11-01 512M (24.7%); 2026-01-31 536M (24.2%); 2026-05-02 652M (27.0%).
Src: wiki/investing/filings/MRVL/MRVL-xbrl.json + MRVL-xbrl-extended.json

### 9.23 APH -- AMPHENOL (mkt cap 193.6B)
| Metric ($M) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Revenue | 6194 | 6439 | 7620 | 8758 |
| Gross profit | n/a | n/a | n/a | n/a |
| Operating income | n/a | n/a | n/a | n/a |
| Net income | 1246 | n/a | 933 | 1769 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Gross margin | n/a | n/a | n/a | n/a |
| Operating margin | n/a | n/a | n/a | n/a |
| Net margin | +20.1 | n/a | +12.2 | +20.2 |

Balance-sheet snapshot: Cash 4.7B (2026-06-30); LTD 3.2B (2018-03-31); StockholdersEquity n/a.
  Ratios: net debt (LTD-Cash) -1.5B.

Cash flow (per quarter: OCF | capex | FCF):
  - 2026-03-31: OCF n/a / capex 292M / FCF n/a
Dilution: fewer than two ShareIssued points (n/a).
R&D intensity: n/a (no R&D points in window).
Src: wiki/investing/filings/APH/APH-xbrl.json

### 9.24 NEE -- NEXTERA ENERGY (mkt cap 174.5B)
| Metric ($M) | 2012-09-30 | 2013-03-31 | 2013-06-30 | 2013-09-30 |
|---|---|---|---|---|
| Revenue | 3843 | 3279 | 3833 | 4394 |
| Gross profit | n/a | n/a | n/a | n/a |
| Operating income | n/a | n/a | n/a | n/a |
| Net income | n/a | n/a | n/a | n/a |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2012-09-30 | 2013-03-31 | 2013-06-30 | 2013-09-30 |
|---|---|---|---|---|
| Gross margin | n/a | n/a | n/a | n/a |
| Operating margin | n/a | n/a | n/a | n/a |
| Net margin | n/a | n/a | n/a | n/a |

Balance-sheet snapshot: Cash 2.0B (2026-03-31); LongTermDebt n/a; Equity 55.2B (2026-03-31).
  Ratios: Cash/Equity 0.04x.

Cash flow: n/a (no OCF/capex/FCF points aligned to the window).
Dilution: shares issued 2083M (2025-12-31) -> 2085M (2026-03-31), +0.10% over 90 days.
R&D intensity: n/a (no R&D points in window).
Src: wiki/investing/filings/NEE/NEE-xbrl.json + NEE-xbrl-extended.json

### 9.25 QCOM -- QUALCOMM (mkt cap 168.8B)
| Metric ($M) | 2025-09-28d | 2025-12-28 | 2026-03-29 | 2026-06-28 |
|---|---|---|---|---|
| Revenue | 11271 | 12252 | 10599 | 9947 |
| Gross profit | n/a | n/a | n/a | n/a |
| Operating income | n/a | n/a | n/a | n/a |
| Net income | n/a | 3004 | 7370 | 2002 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-09-28d | 2025-12-28 | 2026-03-29 | 2026-06-28 |
|---|---|---|---|---|
| Gross margin | n/a | n/a | n/a | n/a |
| Operating margin | n/a | n/a | n/a | n/a |
| Net margin | n/a | +24.5 | +69.5 | +20.1 |

Balance-sheet snapshot: Cash 4.5B (2026-06-28); LTD 12.8B (2026-06-28); StockholdersEquity n/a.
  Ratios: net debt (LTD-Cash) 8.2B.

Cash flow: n/a (no OCF/capex/FCF points aligned to the window).
Dilution: fewer than two ShareIssued points (n/a).
R&D intensity: 2025-09-28 2370M (21.0%); 2025-12-28 2453M (20.0%); 2026-03-29 2463M (23.2%); 2026-06-28 2607M (26.2%).
Src: wiki/investing/filings/QCOM/QCOM-xbrl.json

### 9.26 WDC -- WESTERN DIGITAL (mkt cap 165.6B)
| Metric ($M) | 2025-10-03 | 2026-01-02 | 2026-04-03 | 2026-07-03d |
|---|---|---|---|---|
| Revenue | 2818 | 3017 | 3337 | 3747 |
| Gross profit | n/a | n/a | n/a | n/a |
| Operating income | n/a | n/a | n/a | n/a |
| Net income | 1182 | 1842 | 3205 | 3195 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-10-03 | 2026-01-02 | 2026-04-03 | 2026-07-03d |
|---|---|---|---|---|
| Gross margin | n/a | n/a | n/a | n/a |
| Operating margin | n/a | n/a | n/a | n/a |
| Net margin | +41.9 | +61.1 | +96.0 | +85.3 |

Balance-sheet snapshot: Cash 1.6B (2026-07-03); LTD 1.1B (2026-07-03); StockholdersEquity n/a.
  Ratios: net debt (LTD-Cash) -527M.

Cash flow (per quarter: OCF | capex | FCF):
  - 2025-10-03: OCF n/a / capex 73M / FCF n/a
Dilution: fewer than two ShareIssued points (n/a).
R&D intensity: n/a (no R&D points in window).
Src: wiki/investing/filings/WDC/WDC-xbrl.json

### 9.27 ETN -- EATON CORP (mkt cap 162.8B)
| Metric ($M) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Revenue | 6988 | 7055 | 7451 | 8531 |
| Gross profit | 2675 | 2598 | 2652 | 2855 |
| Operating income | n/a | n/a | n/a | n/a |
| Net income | 1010 | 1131 | 866 | 821 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Gross margin | +38.3 | +36.8 | +35.6 | +33.5 |
| Operating margin | n/a | n/a | n/a | n/a |
| Net margin | +14.5 | +16.0 | +11.6 | +9.6 |

Balance-sheet snapshot: Cash 483M (2026-06-30); LTD 18.5B (2026-06-30); Equity 20.3B (2026-06-30).
  Ratios: LTD/Equity 0.91x; net debt (LTD-Cash) 18.0B; Cash/Equity 0.02x; implied EV-ish (Eq+LTD-Cash) 2.2B.

Cash flow (per quarter: OCF | capex | FCF):
  - 2025-09-30: OCF 2.5B / capex 527M / FCF 2.0B
  - 2025-12-31d: OCF 571M / capex n/a / FCF 3.6B
  - 2026-03-31: OCF 507M / capex 193M / FCF 314M
  - 2026-06-30: OCF 1.6B / capex 446M / FCF 1.2B
Dilution: shares issued 388M (2026-03-31) -> 388M (2026-06-30), +0.03% over 91 days.
R&D intensity: 2025-09-30 203M (2.9%); 2025-12-31 204M (2.9%); 2026-03-31 211M (2.8%); 2026-06-30 227M (2.7%).
Src: wiki/investing/filings/ETN/ETN-xbrl.json + ETN-xbrl-extended.json

### 9.28 NOW -- SERVICENOW (mkt cap 132.8B)
| Metric ($M) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Revenue | 3407 | 3568 | 3770 | 3987 |
| Gross profit | n/a | n/a | n/a | n/a |
| Operating income | n/a | n/a | n/a | n/a |
| Net income | 502 | n/a | 469 | 298 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Gross margin | n/a | n/a | n/a | n/a |
| Operating margin | n/a | n/a | n/a | n/a |
| Net margin | +14.7 | n/a | +12.4 | +7.5 |

Balance-sheet snapshot: Cash 2.5B (2026-06-30); LTD 5.4B (2026-06-30); StockholdersEquity n/a.
  Ratios: net debt (LTD-Cash) 2.9B.

Cash flow (per quarter: OCF | capex | FCF):
  - 2026-03-31: OCF n/a / capex 141M / FCF n/a
Dilution: fewer than two ShareIssued points (n/a).
R&D intensity: 2025-09-30 750M (22.0%); 2025-12-31 773M (21.7%); 2026-03-31 823M (21.8%); 2026-06-30 915M (22.9%).
Src: wiki/investing/filings/NOW/NOW-xbrl.json

### 9.29 LMT -- LOCKHEED MARTIN (mkt cap 130.1B)
| Metric ($M) | 2025-09-28 | 2025-12-31d | 2026-03-29 | 2026-06-28 |
|---|---|---|---|---|
| Revenue | 18609 | 20321 | 18021 | 20063 |
| Gross profit | 2240 | 2322 | 2078 | 2446 |
| Operating income | 2280 | 2331 | 2063 | 2479 |
| Net income | 1619 | 1344 | 1488 | 1836 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-09-28 | 2025-12-31d | 2026-03-29 | 2026-06-28 |
|---|---|---|---|---|
| Gross margin | +12.0 | +11.4 | +11.5 | +12.2 |
| Operating margin | +12.3 | +11.5 | +11.4 | +12.4 |
| Net margin | +8.7 | +6.6 | +8.3 | +9.2 |

Balance-sheet snapshot: Cash 3.8B (2026-06-28); LTD 21.7B (2025-12-31); Equity 8.8B (2026-06-28).
  Ratios: LTD/Equity 2.47x; net debt (LTD-Cash) 17.9B; Cash/Equity 0.43x; implied EV-ish (Eq+LTD-Cash) -9.1B.

Cash flow (per quarter: OCF | capex | FCF):
  - 2025-09-28: OCF 5.3B / capex 1.2B / FCF 4.2B
  - 2025-12-31d: OCF 200M / capex n/a / FCF 6.9B
  - 2026-03-29: OCF 220M / capex 511M / FCF -291M
  - 2026-06-28: OCF 3.5B / capex 829M / FCF 2.6B
Dilution: shares issued 234M (2024-12-31) -> 229M (2025-12-31), -2.14% over 365 days.
R&D intensity: n/a (no R&D points in window).
Src: wiki/investing/filings/LMT/LMT-xbrl.json + LMT-xbrl-extended.json

### 9.30 EQIX -- EQUIINIX (mkt cap 105.1B)
| Metric ($M) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Revenue | 2316 | 2420 | 2444 | 2625 |
| Gross profit | n/a | n/a | n/a | n/a |
| Operating income | n/a | n/a | n/a | n/a |
| Net income | 374 | 265 | 415 | 479 |

Margin stack (% of revenue, same quarters):
| Metric (%) | 2025-09-30 | 2025-12-31d | 2026-03-31 | 2026-06-30 |
|---|---|---|---|---|
| Gross margin | n/a | n/a | n/a | n/a |
| Operating margin | n/a | n/a | n/a | n/a |
| Net margin | +16.1 | +11.0 | +17.0 | +18.2 |

Balance-sheet snapshot: Cash 979M (2026-06-30); LTD 19.9B (2026-06-30); StockholdersEquity n/a.
  Ratios: net debt (LTD-Cash) 18.9B.

Cash flow: n/a (no OCF/capex/FCF points aligned to the window).
Dilution: fewer than two ShareIssued points (n/a).
R&D intensity: n/a (no R&D points in window).
Src: wiki/investing/filings/EQIX/EQIX-xbrl.json

## 10. Comparative rankings expanded

All ranks cover the Section 2 top 30 only, and only names with enough
aligned points; excluded names are listed under each table with the reason.

### 10.1 Operating-margin leaders (TTM operating income / TTM revenue)

| Rank | Ticker | Op marg TTM | Trajectory | n qtr obs |
|---|---|---|---|---|
| 1 | MU | 65.6% | improving | 7 |
| 2 | NVDA | 64.0% | improving | 8 |
| 3 | SNDK | 61.2% | improving | 7 |
| 4 | MSFT | 46.8% | improving | 8 |
| 5 | AVGO | 43.4% | improving | 8 |
| 6 | ANET | 43.1% | flat | 8 |
| 7 | PLTR | 42.8% | improving | 8 |
| 8 | META | 38.1% | declining | 8 |
| 9 | GOOGL | 33.1% | flat | 8 |
| 10 | MRVL | 16.0% | improving | 7 |
| 11 | AMD | 15.7% | improving | 8 |
| 12 | AMZN | 12.1% | flat | 8 |
| 13 | LMT | 11.9% | improving | 8 |
| 14 | GEV | 4.3% | improving | 7 |
| 15 | TSLA | 4.2% | declining | 8 |

Excluded (no OperatingIncomeLoss coverage or <3 aligned points): INTC, CSCO, ORCL, LRCX, AMAT, DELL, RTX, KLAC, APH, NEE, QCOM, WDC, ETN, NOW, EQIX.

Reading: trajectory = newer-half mean minus older-half mean of the
per-quarter operating-margin series (+/-0.75 pt band = flat). LRCX and
KLAC cannot appear: no extended file, hence no OperatingIncomeLoss points.

### 10.2 Gross-margin stability (coefficient of variation, lower = steadier)

| Rank | Ticker | GM CV % | GM mean % | GM stdev (pts) | n qtr obs |
|---|---|---|---|---|---|
| 1 | META | 0.3 | 81.9 | 0.2 | 8 |
| 2 | MSFT | 1.0 | 68.4 | 0.7 | 8 |
| 3 | ANET | 1.6 | 63.6 | 1.0 | 8 |
| 4 | AVGO | 2.8 | 67.1 | 1.9 | 8 |
| 5 | PLTR | 3.2 | 82.3 | 2.6 | 8 |
| 6 | ETN | 4.7 | 37.1 | 1.7 | 8 |
| 7 | NVDA | 6.3 | 72.4 | 4.6 | 8 |
| 8 | AMD | 8.5 | 50.4 | 4.3 | 8 |
| 9 | TSLA | 9.7 | 18.2 | 1.8 | 8 |
| 10 | GEV | 14.0 | 19.0 | 2.7 | 8 |
| 11 | MRVL | 19.6 | 47.0 | 9.2 | 8 |
| 12 | MU | 34.8 | 51.0 | 17.8 | 8 |
| 13 | LMT | 35.7 | 10.0 | 3.6 | 8 |
| 14 | SNDK | 49.3 | 45.4 | 22.4 | 8 |

Excluded (<4 aligned GrossProfit quarters; includes all names without an
extended file and cyclical names with thin GP coverage): GOOGL, AMZN, INTC, CSCO, ORCL, LRCX, AMAT, DELL, RTX, KLAC, APH, NEE, QCOM, WDC, NOW, EQIX.

### 10.3 FCF yield (TTM computed FCF per share / last store-bar close)

| Rank | Ticker | FCF TTM | Shares | FCF/sh | Price 2026-08-24 | Yield |
|---|---|---|---|---|---|---|
| 1 | LMT | 13.4B | 229M | 58.49 | 565.78 | 10.34% |
| 2 | SNDK | 17.8B | 146M | 121.65 | 1484.41 | 8.20% |
| 3 | GEV | 20.3B | 266M | 76.22 | 939.50 | 8.11% |
| 4 | META | 105.6B | 2566M | 41.15 | 555.90 | 7.40% |
| 5 | NVDA | 246.7B | 24304M | 10.15 | 210.25 | 4.83% |
| 6 | ETN | 7.0B | 388M | 18.11 | 410.17 | 4.42% |
| 7 | AVGO | 72.6B | 4758M | 15.27 | 362.05 | 4.22% |
| 8 | MU | 39.3B | 1129M | 34.83 | 911.02 | 3.82% |
| 9 | GOOGL | 136.4B | 12230M | 11.15 | 350.90 | 3.18% |
| 10 | MSFT | 114.3B | 7427M | 15.39 | 490.30 | 3.14% |
| 11 | ANET | 7.4B | 1261M | 5.83 | 189.33 | 3.08% |
| 12 | AMD | 17.8B | 1632M | 10.90 | 458.92 | 2.37% |
| 13 | MRVL | 3.6B | 847M | 4.30 | 227.53 | 1.89% |
| 14 | PLTR | 6.4B | 2403M | 2.67 | 177.40 | 1.51% |
| 15 | TSLA | 12.8B | 3949M | 3.25 | 356.16 | 0.91% |
| 16 | AMZN | -18.9B | 10783M | -1.75 | 263.00 | -0.67% |

Excluded (needs extended-file FCF, a ShareIssued point, and store bars;
LRCX/KLAC fail on the extended file): INTC, CSCO, ORCL, LRCX, AMAT, DELL, RTX, KLAC, APH, NEE, QCOM, WDC, NOW, EQIX.

### 10.4 Share-count change, oldest-vs-newest ShareIssued inside the window

Window = points within 420 days of the latest revenue quarter (falls back
to the last two points otherwise). More negative = more buyback/accretive.

| Rank | Ticker | First shares (date) | Last shares (date) | Change % | Days |
|---|---|---|---|---|---|
| 1 | GEV | 272M (2025-06-30) | 266M (2026-06-30) | -2.16% | 365 |
| 2 | MRVL | 866M (2025-02-01) | 847M (2026-01-31) | -2.16% | 364 |
| 3 | LMT | 234M (2024-12-31) | 229M (2025-12-31) | -2.14% | 365 |
| 4 | NVDA | 24477M (2025-01-26) | 24304M (2026-01-25) | -0.71% | 364 |
| 5 | ETN | 389M (2025-06-30) | 388M (2026-06-30) | -0.23% | 365 |
| 6 | META | 2570M (2025-06-30) | 2566M (2026-06-30) | -0.16% | 365 |
| 7 | MSFT | 7434M (2025-06-30) | 7427M (2026-06-30) | -0.09% | 365 |
| 8 | SNDK | 146M (2025-06-27) | 146M (2026-07-03) | +0.00% | 371 |
| 9 | ANET | 1257M (2025-06-30) | 1261M (2026-06-30) | +0.35% | 365 |
| 10 | AMD | 1622M (2025-06-28) | 1632M (2026-06-27) | +0.62% | 364 |
| 11 | MU | 1119M (2025-05-29) | 1129M (2026-05-28) | +0.89% | 364 |
| 12 | GOOGL | 12104M (2025-06-30) | 12230M (2026-06-30) | +1.04% | 365 |
| 13 | AMZN | 10660M (2025-06-30) | 10783M (2026-06-30) | +1.15% | 365 |
| 14 | AVGO | 4703M (2025-05-04) | 4758M (2026-05-03) | +1.17% | 364 |
| 15 | PLTR | 2372M (2025-06-30) | 2403M (2026-06-30) | +1.31% | 365 |
| 16 | TSLA | 3224M (2025-06-30) | 3949M (2026-06-30) | +22.49% | 365 | <-- OUTLIER: verify against filing (possible split/award)

Excluded (<2 ShareIssued points near the window): INTC, CSCO, ORCL, LRCX, AMAT, DELL, RTX, KLAC, APH, NEE, QCOM, WDC, NOW, EQIX.

Caution: ShareIssued changes mix issuance, buybacks AND split events; a
jump of ~10x is a split artifact, not dilution. Cross-check any outlier
against the cited filing before trading on it.

### 10.5 Book-value / price ratio (StockholdersEquity / shares / price)

| Rank | Ticker | Equity | Shares (latest) | BVPS | Price | BV/P |
|---|---|---|---|---|---|---|
| 1 | NEE | 55.2B | 2085M | 26.49 | 83.63 | 31.7% |
| 2 | AMZN | 551.6B | 10783M | 51.16 | 263.00 | 19.5% |
| 3 | META | 261.2B | 2566M | 101.80 | 555.90 | 18.3% |
| 4 | GOOGL | 640.5B | 12230M | 52.37 | 350.90 | 14.9% |
| 5 | ETN | 20.3B | 388M | 52.15 | 410.17 | 12.7% |
| 6 | MSFT | 442.4B | 7427M | 59.56 | 490.30 | 12.1% |
| 7 | MU | 100.7B | 1129M | 89.22 | 911.02 | 9.8% |
| 8 | MRVL | 18.2B | 847M | 21.50 | 227.53 | 9.4% |
| 9 | AMD | 67.2B | 1632M | 41.19 | 458.92 | 9.0% |
| 10 | SNDK | 15.7B | 146M | 107.78 | 1484.41 | 7.3% |
| 11 | LMT | 8.8B | 229M | 38.29 | 565.78 | 6.8% |
| 12 | ANET | 14.8B | 1261M | 11.73 | 189.33 | 6.2% |
| 13 | TSLA | 86.9B | 3949M | 21.99 | 356.16 | 6.2% |
| 14 | GEV | 12.0B | 266M | 44.89 | 939.50 | 4.8% |
| 15 | NVDA | 195.5B | 24304M | 8.04 | 210.25 | 3.8% |
| 16 | PLTR | 9.8B | 2403M | 4.07 | 177.40 | 2.3% |
| 17 | AVGO | 24.9B | 4758M | 5.24 | 362.05 | 1.4% |

Excluded (needs extended-file StockholdersEquity + ShareIssued + price): INTC, CSCO, ORCL, LRCX, AMAT, DELL, RTX, KLAC, APH, QCOM, WDC, NOW, EQIX.

Low BV/P is normal for asset-light software/services; this screen favors
balance-sheet-heavy names (banks-like, capital-intensive semis, utilities).

## 11. The AI-infrastructure financial footprint

Question: how much real capex sits behind the AI build, and what revenue
does each capex dollar support? Two cohorts, per the delegation:
semis/equipment/storage (NVDA, TSM, AVGO, MRVL, SNDK, WDC, AMAT, LRCX,
KLAC) versus hyperscalers (MSFT, GOOGL, META, AMZN).

Capex basis, chosen per company for maximal SAME-WINDOW integrity, in
priority order: (1) FY pair = fiscal-year 10-K/20-F capex and revenue for
the identical FY period; (2) TTM = sum of the last four aligned quarterly
points; (3) LQ = latest single quarter (flagged). The multiplier column
is revenue divided by capex on the SAME basis -- dollars of revenue per
dollar of capex.

### 11.1 Semiconductor cohort -- capex footprint

| Company | Basis | Window end | Capex | Revenue | Capex/Rev | Rev per $1 capex |
|---|---|---|---|---|---|---|
| NVDA | FY | 2026-01-25 | 6.0B | 215.9B | 2.8% | 35.7 |
| TSM | n/a | n/a | n/a | n/a | n/a | n/a |
| AVGO | FY | 2025-11-02 | 623M | 63.9B | 1.0% | 102.5 |
| MRVL | FY | 2026-01-31 | 354M | 8.2B | 4.3% | 23.1 |
| SNDK | FY | 2026-07-03 | 177M | 20.2B | 0.9% | 114.4 |
| WDC | FY | 2026-07-03 | 418M | 12.9B | 3.2% | 30.9 |
| AMAT | FY | 2025-10-26 | 2.3B | 28.4B | 8.0% | 12.6 |
| LRCX | n/a | n/a | n/a | n/a | n/a | n/a |
| KLAC | FY | 2026-06-30 | 376M | 13.6B | 2.8% | 36.1 |
| **TOTAL (7 names)** | mixed | mixed | **10.3B** | **363.1B** | 2.8% | **35.43** |

### 11.2 Hyperscaler cohort -- capex footprint

| Company | Basis | Window end | Capex | Revenue | Capex/Rev | Rev per $1 capex |
|---|---|---|---|---|---|---|
| MSFT | FY | 2026-06-30 | 115.9B | 331.8B | 34.9% | 2.9 |
| GOOGL | FY | 2025-12-31 | 91.4B | 402.8B | 22.7% | 4.4 |
| META | FY | 2025-12-31 | 69.7B | 201.0B | 34.7% | 2.9 |
| AMZN | FY | 2025-12-31 | 131.8B | 716.9B | 18.4% | 5.4 |
| **TOTAL (4 names)** | mixed | mixed | **408.9B** | **1.65T** | 24.7% | **4.04** |

### 11.3 Cohort comparison

| Cohort | Total capex | Total revenue | Blended capex/revenue | Blended multiplier |
|---|---|---|---|---|
| Semis/AI infra (measured names) | 10.3B | 363.1B | 2.8% | 35.43 |
| Hyperscalers | 408.9B | 1.65T | 24.7% | 4.04 |

Ratio of cohorts: semi capex is 0.03x hyperscaler capex; hyperscaler
revenue is 4.55x measured-semi revenue. Every $1 the hyperscaler cohort
spends on capex meets roughly $0.03 of semi-cohort capex on the other
side of the trade.

### 11.4 Data-quality notes specific to this section

- TSM: no base xbrl JSON in the corpus (Section 7 gap) and the extended
  file holds only 20-F annual rows through FY2017 with NO revenue concept,
  so its row shows n/a. The semi-cohort TOTAL is therefore UNDERSTATED by
  however much of TSM's current tens-of-billions annual capex is missing;
  do not quote the total as industry-wide.
- NVDA: fab-lite, so its own capex line dramatically understates its pull
  on the supply chain; foundry capex lands on TSM's books, which this
  corpus cannot currently quantify (see TSM note).
- LRCX: base-file Capex points exist only as scattered pre-2020 Q1 rows,
  and there is no extended file, so no same-window pair forms -- n/a.
- Mixed bases inside one cohort total (FY vs TTM windows) are labeled per
  row; the blended multiplier mixes slightly different windows and is
  directional, not audited.
- Reading the asymmetry: hyperscaler capex (409B) is ~40x the measured
  semi-cohort capex because the two cohorts sit at different points of
  the value chain. Semis monetize capex through manufacturing THROUGHPUT
  sold as chips (high revenue per capex dollar), hyperscalers deploy capex
  into owned datacenters that monetize gradually through services (low
  revenue per capex dollar today). The ratio of cohort capex is a supply-
  chain flow statement: hyperscaler dollars are what fund the ecosystem,
  including the missing TSM line.
- SNDK price bars start 2025-02-13 (spin-off listing), which only affects
  per-share screens, not this section.

## 12. Expansion caveats (read before quoting any number above)

- Everything inherits the Section 7 caveats: stale corpora (NEE's freshest
  revenue point is 2013Q3; AMKR/DUK/GD similar), suspect extreme YoY and
  net-margin flags, non-computable EPS, and fiscal-calendar skew across
  the cohort.
- Derived Q4 cells inherit the Section 2 derivation-artifact risk: where
  an FY row or the quarter set underneath it is incomplete, the derived
  value can be wrong (negative revenue cells elsewhere in this corpus are
  exactly this artifact). Cells are marked "d"; treat suspicious ones as
  missing rather than as real declines.
- Margin stacks mix bases when GrossProfit excludes items that
  OperatingIncomeLoss includes (stock-based comp placement differs by
  filer); cross-company margin LEVELS are less comparable than each
  company's own TRAJECTORY.
- FCF is the upstream computed field (OCF minus capex patch); companies
  with heavy finance-segment flows or capitalized-software nuance will
  diverge from vendor-reported FCF.
- ShareIssued is shares issued at balance dates and, per the upstream
  patch note, falls back to CommonStockSharesOutstanding; splits make
  level jumps that are NOT dilution (Section 10.4 caution applies).
- Prices are daily closes from the offline factors.db store (through
  2026-08-24). Yields/BV-P move with the market daily while the XBRL side
  moves quarterly; re-run before acting.
- ASCII-only and hand-edit-discouraged: regenerate this expansion from the
  same aggregation logic rather than editing individual cells.
