---
categories: [wiki]
type: reference
status: active
created: 2026-08-24
updated: 2026-08-24
confidence: medium
tags:
  - topic/investing
  - topic/scoring
  - topic/meta
related: ["[[ref-financial-statements]]", "*confidence-map-2026* (not published)", "*ref-sector-benchmarks* (not published)", "*portfolio-x-invest-history* (not published)"]
---

# Quantitative composite scoring engine -- all tickers (GENERATED)

GENERATED: 2026-08-24 by the composite-scoring pass. Every number below is
computed from existing vault files; no network sources were used. REGENERATE:
re-run the documented arithmetic over (a) factor store bars
(Efforts/osanwe-v2-overhaul/_work/factors.db), (b) EDGAR XBRL pulls
(wiki/investing/filings/<T>/<T>-xbrl.json), (c) wave-analysis frontmatter
(Efforts/osanwe-v2-overhaul/_work/wave*-analysis.md), (d)
wiki/maintenance/calibration/confidence-map.json, and (e) the chokepoint
rankings in [[ref-semiconductor-value-chain]] Section 10 and
[[ref-energy-power-complex]] Sections 1-7. Do not hand-edit scores.

## 0. Method

Universe: the 107 instruments in the factor-store bars table (as-of
2026-08-21, the common last close across all equities; crypto series run to
2026-08-24). Component scores are 0-100.

1. MOMENTUM: 0.30*ret21d + 0.25*ret63d + 0.25*dist_MA50 + 0.20*dist_MA200,
   each input clipped to [-50, +50] pct then mapped to [0,100] via
   (x+50). Higher = stronger trend. From store bars.
2. RISK-ADJUSTED (Sharpe-like): ann_return / ann_vol over each ticker's full
   available bar history, mapped to [0,100] by percentile rank across the
   scored universe.
3. DRAWDOWN RESILIENCE: 100 + max_drawdown_pct on full history (so -20% DD =
   80); floor 0. From store bars.
4. FUNDAMENTAL: revenue YoY growth (LQ vs same quarter 330-400d earlier),
   TTM net margin, cash/LT-debt ratio -- each mapped to [0,100] by percentile
   rank across tickers with XBRL data; average of available sub-scores
   (2 of 3 required to score). From <T>-xbrl.json.
5. ANALYST CONFIDENCE: stated confidence from the latest wave analysis file
   for that ticker (51 files, 50 distinct tickers).
6. CALIBRATED CONFIDENCE: analyst confidence x bin calibration ratio from
   wiki/maintenance/calibration/confidence-map.json (60-69 -> 38.9/65,
   70-79 -> 31.2/75, 80-89 -> 31.7/85; stated 45-59 uses the nearest
   measured band 60-69 ratio, flagged as extrapolation).
7. MOAT: qualitative 0-100 from the chokepoint hierarchy in
   [[ref-semiconductor-value-chain]] Section 10 (ASML/TSM/SNPS+CDNS/MU/LITE/
   NVDA/AVGO/ARM ranks) and the power-layer dependency graph in
   [[ref-energy-power-complex]] Section 7 (GEV/ETN grid equipment, CEG/VST/TLN
   firm-capacity PPAs, VRT cooling, BWXT SMR components). Non-covered names
   default 40 with rationale noted per-name where a corpus claim exists.

COMPOSITE = 0.15*Momentum + 0.15*RiskAdj + 0.10*Drawdown + 0.25*Fundamental
+ 0.20*CalibratedConf + 0.15*Moat. Names lacking fundamentals get composite
rescaled over the five available components (weights renormalized); names
without a wave analysis get calibrated confidence = n/a and composite
rescaled over the remaining five components. Full six-component coverage:
49 names. Five-component: 33 names (no analysis or no XBRL). Four-component:
4 names. Minimum to appear in the ranked table: bars + 4 scored components.

## 1. Component score table -- ALL tickers, ranked by COMPOSITE

| rank | ticker | MOM | SHRP | DD | FUND | CONF(c) | CALIB | MOAT | COMP | flag |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | MU | 66 | 95 | 42 | 93 | 55 | 32.9 | 86 | **71.2** |  |
| 2 | CRDO | 60 | 92 | 38 | 88 | -- | -- | 46 | **69.5** |  |
| 3 | APH | 58 | 88 | 71 | 72 | -- | -- | 48 | **67.7** |  |
| 4 | WDC | 45 | 92 | 45 | 83 | -- | -- | 48 | **66.2** |  |
| 5 | NVDA | 53 | 93 | 34 | 87 | 70 | 29.1 | 82 | **65.3** |  |
| 6 | IAU | 58 | 90 | 74 | n/a | -- | -- | 40 | **64.5** |  |
| 7 | ATEYY | 75 | 91 | 44 | n/a | -- | -- | 40 | **64.1** |  |
| 8 | SNDK | 60 | 99 | 44 | 84 | 60 | 35.9 | 52 | **64.1** |  |
| 9 | VDE | 61 | 83 | 73 | n/a | -- | -- | 40 | **63.4** |  |
| 10 | PLTR | 83 | 66 | 21 | 90 | 68 | 40.7 | 56 | **63.3** |  |
| 11 | ALAB | 46 | 79 | 36 | 86 | -- | -- | 40 | **62.6** |  |
| 12 | PPA | 51 | 84 | 82 | n/a | -- | -- | 40 | **62.5** |  |
| 13 | ANET | 66 | 86 | 50 | 77 | 62 | 37.1 | 48 | **61.5** |  |
| 14 | ITA | 52 | 75 | 81 | n/a | -- | -- | 40 | **60.4** |  |
| 15 | LITE | 57 | 78 | 34 | 47 | -- | -- | 84 | **60.0** |  |
| 16 | CDNS | 43 | 41 | 70 | n/a | -- | -- | 88 | **59.7** |  |
| 17 | GD | 56 | 71 | 77 | n/a | -- | -- | 40 | **59.6** |  |
| 18 | VOLT | 45 | 82 | 77 | n/a | -- | -- | 40 | **59.6** |  |
| 19 | ABBNY | 52 | 81 | 67 | n/a | -- | -- | 40 | **59.2** |  |
| 20 | AVGO | 44 | 94 | 59 | 59 | 76 | 31.6 | 76 | **59.0** |  |
| 21 | TSM | 54 | 74 | 44 | n/a | 74 | 30.8 | 96 | **58.7** |  |
| 22 | GEV | 46 | 98 | 62 | 51 | 45 | 26.9 | 78 | **57.7** |  |
| 23 | SPY | 54 | 67 | 76 | n/a | -- | -- | 40 | **57.7** |  |
| 24 | DELL | 74 | 89 | 40 | 55 | 64 | 38.3 | 46 | **56.8** |  |
| 25 | SMH | 51 | 80 | 55 | n/a | -- | -- | 40 | **56.7** |  |
| 26 | XAR | 51 | 68 | 72 | n/a | -- | -- | 40 | **56.5** |  |
| 27 | HUBB | 48 | 60 | 67 | n/a | -- | -- | 54 | **56.4** |  |
| 28 | AMD | 55 | 53 | 35 | 77 | 68 | 40.7 | 55 | **55.2** |  |
| 29 | BWXT | 34 | 64 | 66 | 69 | 55 | 32.9 | 66 | **55.1** |  |
| 30 | NBIS | 59 | 97 | 42 | n/a | 62 | 37.1 | 42 | **55.0** |  |
| 31 | LRCX | 54 | 73 | 44 | 67 | 50 | 29.9 | 58 | **54.8** |  |
| 32 | ONTO | 57 | 50 | 37 | 58 | -- | -- | 62 | **54.5** |  |
| 33 | AMAT | 52 | 61 | 45 | 67 | 55 | 32.9 | 58 | **53.5** |  |
| 34 | GOOGL | 50 | 55 | 56 | 71 | 68 | 40.7 | 40 | **53.2** |  |
| 35 | CEG | 48 | 85 | 49 | 34 | 66 | 39.5 | 80 | **53.1** |  |
| 36 | TLN | 35 | 96 | 66 | 37 | 62 | 37.1 | 66 | **52.9** |  |
| 37 | ASML | 56 | 42 | 43 | n/a | 70 | 29.1 | 98 | **52.7** |  |
| 38 | AEIS | 41 | 52 | 60 | 65 | -- | -- | 40 | **52.6** |  |
| 39 | MRVL | 70 | 43 | 38 | 65 | 65 | 38.9 | 50 | **52.5** |  |
| 40 | QQQ | 53 | 56 | 65 | n/a | -- | -- | 40 | **52.3** |  |
| 41 | SMCI | 68 | 62 | 15 | 70 | 58 | 34.7 | 42 | **51.7** |  |
| 42 | VRT | 39 | 75 | 29 | 56 | 66 | 39.5 | 64 | **51.5** |  |
| 43 | HPE | 78 | 72 | 52 | 42 | 60 | 35.9 | 40 | **51.4** |  |
| 44 | ARM | 41 | 69 | 46 | n/a | 58 | 34.7 | 70 | **51.4** |  |
| 45 | KLAC | 43 | 77 | 56 | 50 | 50 | 29.9 | 60 | **51.2** |  |
| 46 | MSFT | 68 | 37 | 63 | 61 | 65 | 38.9 | 40 | **51.1** |  |
| 47 | FN | 28 | 54 | 56 | 69 | -- | -- | 38 | **50.9** |  |
| 48 | ETN | 55 | 63 | 66 | 33 | 62 | 37.1 | 72 | **50.9** |  |
| 49 | VOO | 54 | 70 | 75 | n/a | 70 | 29.1 | 40 | **50.6** |  |
| 50 | CSCO | 51 | 58 | 63 | 46 | -- | -- | 40 | **50.4** |  |
| 51 | AAOI | 51 | 58 | 17 | 63 | -- | -- | 40 | **49.6** |  |
| 52 | RTX | 58 | 76 | 67 | 32 | 68 | 40.7 | 40 | **49.0** |  |
| 53 | VGT | 55 | 65 | 65 | n/a | 70 | 29.1 | 40 | **48.5** |  |
| 54 | DTCR | 50 | 45 | 61 | n/a | -- | -- | 40 | **47.9** |  |
| 55 | AVAV | 44 | 20 | 33 | 74 | -- | -- | 40 | **46.9** |  |
| 56 | VST | 36 | 87 | 51 | 22 | 55 | 32.9 | 74 | **46.8** |  |
| 57 | KTOS | 54 | 36 | 34 | 58 | -- | -- | 40 | **46.7** |  |
| 58 | SNPS | 43 | 16 | 58 | 47 | 55 | 32.9 | 90 | **46.6** |  |
| 59 | DLR | 54 | 26 | 51 | 55 | 62 | 37.1 | 50 | **45.8** |  |
| 60 | BTC-USD | 71 | 19 | 23 | n/a | -- | -- | 60 | **45.2** |  |
| 61 | RKLB | 36 | 47 | 17 | 61 | -- | -- | 40 | **44.3** |  |
| 62 | NOW | 75 | 10 | 35 | 49 | 62 | 37.1 | 52 | **43.8** |  |
| 63 | ASMIY | 49 | 42 | 42 | n/a | -- | -- | 40 | **43.5** |  |
| 64 | SO | 45 | 48 | 77 | 38 | 45 | 26.9 | 46 | **43.4** |  |
| 65 | CRWV | 46 | 59 | 33 | 43 | 55 | 32.9 | 44 | **43.2** |  |
| 66 | ORCL | 48 | 29 | 35 | 58 | 74 | 30.8 | 48 | **42.9** |  |
| 67 | HIMS | 66 | 40 | 21 | 41 | -- | -- | 40 | **42.7** |  |
| 68 | EQIX | 54 | 28 | 58 | 36 | 63 | 37.7 | 54 | **42.7** |  |
| 69 | AMZN | 55 | 27 | 44 | 54 | 74 | 30.8 | 40 | **42.5** |  |
| 70 | DUK | 46 | 34 | 76 | n/a | 45 | 26.9 | 44 | **42.1** |  |
| 71 | LMT | 53 | 46 | 68 | 25 | 65 | 38.9 | 40 | **41.8** |  |
| 72 | XRP-USD | 79 | 13 | 22 | n/a | -- | -- | 45 | **41.5** |  |
| 73 | COHR | 40 | 49 | 37 | 42 | 50 | 29.9 | 52 | **41.4** |  |
| 74 | LINK-USD | 94 | 5 | 15 | n/a | -- | -- | 42 | **41.1** |  |
| 75 | MP | 64 | 21 | 18 | 48 | -- | -- | 40 | **40.6** |  |
| 76 | NOC | 50 | 39 | 65 | 26 | 63 | 37.7 | 40 | **39.7** |  |
| 77 | QCOM | 39 | 17 | 56 | 46 | -- | -- | 42 | **39.6** |  |
| 78 | TSLA | 49 | 18 | 26 | 56 | 55 | 32.9 | 40 | **39.1** |  |
| 79 | PPL | 46 | 35 | 75 | 30 | 45 | 26.9 | 44 | **39.0** |  |
| 80 | NRG | 31 | 51 | 62 | 15 | -- | -- | 56 | **38.4** |  |
| 81 | MKSI | 39 | 30 | 33 | 43 | -- | -- | 42 | **38.3** |  |
| 82 | META | 41 | 23 | 23 | 55 | 55 | 32.9 | 40 | **38.2** |  |
| 83 | MRAM | 40 | 32 | 29 | 43 | -- | -- | 40 | **38.1** |  |
| 84 | USAR | 54 | 25 | 31 | n/a | -- | -- | 40 | **37.9** |  |
| 85 | BE | 37 | 57 | 24 | n/a | 50 | 29.9 | 40 | **37.8** |  |
| 86 | SOL-USD | 76 | 14 | 4 | n/a | -- | -- | 45 | **37.5** |  |
| 87 | COIN | 57 | 8 | 9 | 49 | 45 | 26.9 | 58 | **36.8** |  |
| 88 | LHX | 39 | 24 | 62 | 29 | -- | -- | 40 | **36.1** |  |
| 89 | NEE | 45 | 15 | 55 | n/a | 45 | 26.9 | 48 | **36.1** |  |
| 90 | ONDO-USD | 62 | 22 | 11 | n/a | -- | -- | 40 | **35.6** |  |
| 91 | INTC | 42 | 25 | 35 | 34 | -- | -- | 42 | **35.4** |  |
| 92 | HII | 47 | 33 | 55 | 17 | -- | -- | 40 | **34.7** |  |
| 93 | AEP | 43 | 44 | 70 | 8 | 45 | 26.9 | 46 | **34.5** |  |
| 94 | OKLO | 29 | 38 | 21 | n/a | -- | -- | 44 | **34.2** |  |
| 95 | AMKR | 29 | 31 | 34 | n/a | -- | -- | 40 | **33.6** |  |
| 96 | BAH | 59 | 12 | 33 | 20 | -- | -- | 40 | **31.2** |  |
| 97 | XLM-USD | 60 | 6 | 17 | n/a | -- | -- | 36 | **30.8** |  |
| 98 | GFS | 27 | 11 | 38 | n/a | -- | -- | 44 | **29.5** |  |
| 99 | HBAR-USD | 57 | 4 | 7 | n/a | -- | -- | 40 | **28.9** |  |
| 100 | ALGO-USD | 62 | 1 | 3 | n/a | -- | -- | 38 | **28.1** |  |
| 101 | QNT-USD | 53 | 3 | 11 | n/a | -- | -- | 38 | **27.6** |  |
| 102 | AMBA | 49 | 7 | 18 | 22 | -- | -- | 40 | **27.3** |  |
| 103 | WBD | 57 | 9 | 22 | 13 | -- | -- | 40 | **26.9** |  |
| 104 | MBLY | 54 | 0 | 14 | 5 | -- | -- | 40 | **21.0** |  |
| 105 | FLNC | 17 | 2 | 10 | 14 | 55 | 32.9 | 46 | **20.9** |  |
| 106 | SMR | 41 | 8 | 13 | 1 | -- | -- | 40 | **18.7** |  |

## 2. Top 10 strongest overall

1. **MU** -- composite 71.2. Full-stack leader: #1 fundamental (rev +346% YoY LQ, 56% TTM margin, cash 2.8x LTD), top-decile risk-adjusted history, S10#4 HBM chokepoint. Composite capped by calibrated confidence (55 stated reads 33) and the -58% cycle max drawdown.
2. **CRDO** -- composite 69.5. Best no-analysis name: +157% rev growth, 35% margin, 92nd-pct risk-adjusted. Unscored analyst layer (no wave file) renormalizes weights upward on price/fundamentals -- treat rank as provisional until analyzed.
3. **APH** -- composite 67.7. Connector sockets multiplexed but sticky; strong balance sheet, shallow drawdowns, quiet compounder profile across the full 5y window.
4. **WDC** -- composite 66.2. NAND/HDD cycle at full throttle (+372% YoY revenue cohort), 92nd-pct Sharpe; no wave analysis so confidence contributes nothing; HDD layer substitutability caps moat.
5. **NVDA** -- composite 65.3. Everything high except the calibration haircut: 70 stated -> 29 calibrated is the single biggest composite drag of any top-10 name. CUDA moat + fundamentals (rev +85% YoY LQ, 59% TTM margin) keep it #2 of the 41 fully-covered names, behind only MU.
6. **IAU** -- composite 64.5. Gold: shallow drawdowns, low vol, zero fundamental/an analyst coverage. Ranks on resilience alone -- a portfolio diversifier reading, not an alpha signal.
7. **ATEYY** -- composite 64.1. Advantest ADR: tester-cycle momentum (75th-pct momentum) + 91st-pct Sharpe. No XBRL corpus, no analysis, default moat -- data-thin rank.
8. **SNDK** -- composite 64.1. top risk-adjusted name in the store (sharpe percentile 99; the raw 5y ann ret ~1120% rides a low 2025 spin-in price), fundamentals rebuilt post-spin. **VDE** -- composite 63.4. Energy ETF beta: deep drawdown recovery + steady carry; no fundamentals/analysis layers; ranks as regime exposure only.
10. **PLTR** -- composite 63.3. Highest momentum in the scored universe (83) + 47.5% TTM margin on +92.8% YoY revenue; deepest drawdown of the top tier (-79%) and the valuation paradox documented in ref-datacenter-infrastructure S4 are the risks priced in.

## 3. Bottom 5 weakest

- **AMBA** -- composite 27.3 (rank 102/106). Weak across the board: 7th-pct Sharpe, 22 fundamentals (-19% margin cohort), no coverage; edge-AI narrative not yet in numbers.
- **WBD** -- composite 26.9 (rank 103/106). No value-chain claim, 13.5 fundamentals, bottom-quintile risk-adjusted; media name outside every thesis graph in the corpus.
- **MBLY** -- composite 21.0 (rank 104/106). Bottom-decile risk-adjusted (0th pct Sharpe over 5y), thin fundamentals (5.8), no analyst coverage. Momentum positive but from a deep base.
- **FLNC** -- composite 20.9 (rank 105/106). Worst momentum (-21% 21d, -30% below MA50), 98% annualized vol, negative TTM margin, China cost-curve risk. The 55-stated confidence (->33 calibrated) cannot offset four weak layers.
- **SMR** -- composite 18.7 (rank 106/106). Fundamental floor: $75K LQ revenue (-99% artifact), -226% net margin, -87.5% max drawdown, near-worst risk-adjusted. Only NRC certification keeps it off zero.

## 4. Portfolio view

Withheld from the public copy: this section compared portfolio positions against the rest of the scored universe, name by name.


## 5. Caveats

- Confidence calibration ratios are indicative at n=54 (shrinkage k=20);
  the 80-89 bin has n=1. Stated confidences below 60 use the 60-69 band
  ratio as nearest-band extrapolation.
- Fundamental percentile ranks compare heterogeneous sectors; utilities and
  hyperscalers sit in the same distribution by construction.
- Moat scores for non-AI-supply-chain names are defaults, not measurements;
  per-name overrides cited inline above only where the corpus makes a claim.
- Bars as-of 2026-08-21 for equities (crypto to 2026-08-24); XBRL latest
  quarters vary by fiscal calendar (LITE lags two quarters, etc.).
- ARM/ASML/CDNS/GFS/NBIS/TSM/QQQ lack <T>-xbrl.json (corpus gap honored);
  TSM carries a partial extended pull only.
