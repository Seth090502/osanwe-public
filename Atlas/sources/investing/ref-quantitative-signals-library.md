---
categories: [sources]
type: reference
target_path: Atlas/sources/investing/ref-quantitative-signals-library.md
created: 2026-08-24
updated: 2026-08-24
status: active
confidence: high
tags:
  - topic/quantitative-signals
  - topic/momentum
  - topic/mean-reversion
  - topic/volatility-regime
  - topic/factor-investing
---

# ref-quantitative-signals-library -- cross-instrument quantitative signal rankings

Ranked quantitative signal tables computed for ALL 107 instruments in the factor
store, plus a LONG/NEUTRAL/SHORT composite dashboard. Every number is computed
from `Efforts/osanwe-v2-overhaul/_work/factors.db` table `bars`
(ticker, date, close); no external data, no network.

- As-of date: 2026-08-24 (max date across all series; every instrument is current)
- Universe: 107 instruments, 130,494 bars total
- History depth: 106 instruments have >= 126 bars; SPCX has only 50 bars
  (IPO 2026-06-12), so its 3m/6m/12m, MA200, z-score, vol-ratio and beta cells
  are structurally unavailable and shown as `-`.
- Compute engine: `Efforts/osanwe-v2-overhaul/_work/signals-lib-compute.py`
  (writes `_work/signals-library-data.json`).
- This page: `Efforts/osanwe-v2-overhaul/_work/signals-lib-render.py`.

## REGENERATE

```
python Efforts/osanwe-v2-overhaul/_work/signals-lib-compute.py
python Efforts/osanwe-v2-overhaul/_work/signals-lib-render.py
```

Rerun after each weekly calibration ingest (`osanwe-weekly-calibration`, SUN
07:30) refreshes factors.db. Tables below are a snapshot as of 2026-08-24.

## Conventions and formulas

- Returns are simple price returns over trading-day windows: 1m=21 bars,
  3m=63, 6m=126, 12m=252 (last bar vs bar k back). Percent, signed.
- RS = instrument return minus SPY return over the SAME calendar window,
  matched on dates (SPY close at or before the instrument end date).
- MA50/MA200: simple moving averages of close. State uses the last bar vs
  both MAs; a crossover is flagged only when the MA relationship flipped
  within the last 5 sessions.
- 52w proximity: (px / max(close, last 252 bars) - 1) in percent; negative =
  below the high. Off-low: percent above the same-window minimum.
- RSI(14): Wilder smoothing (standard 14-period). Zones: oversold < 30,
  overbought > 70.
- z200: (px - mean(last 200 closes)) / stdev(last 200 closes).
- Streak: consecutive up (+n) or down (-n) closes through the as-of date.
- Realized vol: annualized stdev of daily log returns (x sqrt(252)); vol20
  uses last 20 returns, vol60 last 60. Ratio = vol20 / vol60;
  expanding > 1.2, contracting < 0.8.
- Vol percentile: current vol20 vs the instrument's OWN entire rolling-20d
  vol history (share of history at or below current).
- Beta60: covariance(instr, SPY) / variance(SPY) over the last 60 daily log
  returns on commonly dated bars; corr60 = Pearson correlation same window.
- Missing cells are `-`; they exist only where history is too short for the
  statistic (thresholds listed per section).

---

## 1. Momentum -- returns and relative strength (all 107, ranked)

Master table ranked by 12m return (descending). RS columns are excess return
vs SPY over the matching window. SPY itself over these windows: 1m +3.5,
3m +2.9, 6m +12.7, 12m +21.7.

| rk | ticker | 1m% | 3m% | 6m% | 12m% | RS1m | RS3m | RS6m | RS12m |
|---:|--------|----:|----:|----:|-----:|-----:|-----:|-----:|------:|
| 1 | SNDK | +3.3 | +0.4 | +122.7 | +3162.4 | -0.2 | -2.5 | +110.0 | +3140.7 |
| 2 | MU | -1.1 | +21.3 | +116.5 | +688.0 | -4.6 | +18.5 | +103.8 | +666.4 |
| 3 | LITE | +7.9 | -13.0 | +22.0 | +601.1 | +4.4 | -15.9 | +9.3 | +579.5 |
| 4 | WDC | -16.7 | -10.6 | +54.5 | +481.4 | -20.2 | -13.4 | +41.8 | +459.7 |
| 5 | AAOI | +9.6 | -39.5 | +103.4 | +363.0 | +6.1 | -42.4 | +90.7 | +341.3 |
| 6 | BE | +10.3 | -32.6 | +27.2 | +354.8 | +6.7 | -35.5 | +14.5 | +333.1 |
| 7 | INTC | -5.4 | -27.1 | +100.2 | +271.8 | -8.9 | -30.0 | +87.6 | +250.1 |
| 8 | DELL | -1.0 | +47.0 | +265.3 | +243.2 | -4.5 | +44.1 | +252.6 | +221.5 |
| 9 | MRVL | +17.1 | +15.9 | +192.7 | +220.2 | +13.6 | +13.1 | +180.0 | +198.5 |
| 10 | COHR | -2.8 | -27.3 | +10.2 | +216.8 | -6.4 | -30.2 | -2.5 | +195.1 |
| 11 | NBIS | +10.9 | -3.0 | +107.0 | +214.7 | +7.4 | -5.9 | +94.3 | +193.0 |
| 12 | LRCX | +0.3 | +0.4 | +26.6 | +212.9 | -3.2 | -2.5 | +14.0 | +191.2 |
| 13 | AMAT | -9.9 | +11.8 | +29.5 | +203.7 | -13.4 | +9.0 | +16.8 | +182.0 |
| 14 | ATEYY | +26.0 | +27.7 | +31.1 | +192.7 | +22.5 | +24.8 | +18.4 | +171.0 |
| 15 | AMD | -12.1 | -1.8 | +133.4 | +180.3 | -15.6 | -4.7 | +120.7 | +158.6 |
| 16 | MKSI | -17.3 | -15.0 | +7.4 | +175.2 | -20.8 | -17.9 | -5.3 | +153.5 |
| 17 | MRAM | +7.8 | -51.7 | +51.3 | +166.7 | +4.3 | -54.5 | +38.7 | +145.0 |
| 18 | ONTO | +2.4 | +6.4 | +30.9 | +164.7 | -1.1 | +3.6 | +18.2 | +143.0 |
| 19 | WBD | +11.5 | +6.3 | -0.6 | +147.9 | +8.0 | +3.5 | -13.3 | +126.2 |
| 20 | HPE | +9.7 | +39.7 | +164.1 | +144.8 | +6.2 | +36.8 | +151.4 | +123.1 |
| 21 | ASML | -0.7 | +6.9 | +17.7 | +138.6 | -4.2 | +4.0 | +5.0 | +116.9 |
| 22 | AMKR | -26.0 | -26.8 | +2.4 | +108.9 | -29.5 | -29.7 | -10.3 | +87.2 |
| 23 | KLAC | -14.2 | -4.4 | +21.5 | +107.8 | -17.8 | -7.2 | +8.8 | +86.1 |
| 24 | ASMIY | -0.7 | -7.7 | +15.0 | +107.0 | -4.2 | -10.6 | +2.3 | +85.3 |
| 25 | VRT | -12.4 | -22.3 | +3.7 | +101.2 | -15.9 | -25.2 | -9.0 | +79.5 |
| 26 | CRDO | +2.5 | +0.1 | +76.2 | +97.1 | -1.0 | -2.8 | +63.5 | +75.4 |
| 27 | SMH | -2.6 | -5.1 | +32.4 | +90.8 | -6.1 | -8.0 | +19.7 | +69.1 |
| 28 | AEIS | -9.8 | -15.6 | -16.7 | +85.5 | -13.3 | -18.4 | -29.4 | +63.8 |
| 29 | TSM | +1.5 | +1.5 | +11.3 | +82.2 | -2.0 | -1.4 | -1.4 | +60.5 |
| 30 | ARM | -8.5 | -22.4 | +92.2 | +78.5 | -12.0 | -25.2 | +79.5 | +56.8 |
| 31 | GOOGL | +9.7 | -8.3 | +12.8 | +76.2 | +6.2 | -11.2 | +0.1 | +54.5 |
| 32 | CSCO | -2.9 | -7.6 | +43.9 | +68.8 | -6.4 | -10.4 | +31.2 | +47.1 |
| 33 | RKLB | +8.5 | -48.9 | -1.2 | +67.0 | +5.0 | -51.8 | -13.9 | +45.3 |
| 34 | FLNC | -17.9 | -48.7 | -31.3 | +61.3 | -21.4 | -51.5 | -44.0 | +39.6 |
| 35 | ALAB | -5.2 | -10.0 | +115.5 | +55.6 | -8.8 | -12.8 | +102.8 | +34.0 |
| 36 | GEV | -7.4 | -9.5 | +13.1 | +55.4 | -10.9 | -12.4 | +0.4 | +33.7 |
| 37 | FN | -11.1 | -39.9 | -26.6 | +52.7 | -14.7 | -42.8 | -39.3 | +31.0 |
| 38 | DTCR | -0.5 | -7.9 | +10.5 | +51.9 | -4.1 | -10.8 | -2.2 | +30.2 |
| 39 | VDE | +5.1 | +5.9 | +15.3 | +50.1 | +1.6 | +3.1 | +2.7 | +28.4 |
| 40 | ABBNY | +1.2 | -8.4 | +10.0 | +49.8 | -2.4 | -11.2 | -2.7 | +28.1 |
| 41 | ANET | +8.8 | +22.9 | +48.6 | +43.4 | +5.3 | +20.1 | +35.9 | +21.7 |
| 42 | APH | +0.7 | +16.6 | +4.4 | +42.3 | -2.8 | +13.8 | -8.3 | +20.6 |
| 43 | GFS | -13.6 | -45.9 | +0.3 | +42.1 | -17.1 | -48.8 | -12.4 | +20.4 |
| 44 | IAU | +15.0 | +3.3 | -11.1 | +39.3 | +11.4 | +0.5 | -23.8 | +17.6 |
| 45 | EQIX | -2.9 | -2.5 | +12.5 | +38.7 | -6.4 | -5.3 | -0.1 | +17.0 |
| 46 | VGT | +3.2 | +1.1 | +28.9 | +37.7 | -0.4 | -1.8 | +16.2 | +16.0 |
| 47 | RTX | -1.3 | +18.7 | +4.5 | +35.9 | -4.8 | +15.8 | -8.2 | +14.3 |
| 48 | VOLT | -5.5 | -9.6 | +1.2 | +32.6 | -9.0 | -12.4 | -11.5 | +10.9 |
| 49 | LMT | -2.9 | +6.8 | -13.3 | +29.9 | -6.4 | +3.9 | -26.0 | +8.2 |
| 50 | QQQ | +3.5 | -1.2 | +18.0 | +26.3 | -0.0 | -4.1 | +5.3 | +4.6 |
| 51 | AVGO | -5.2 | -12.4 | +10.0 | +25.9 | -8.7 | -15.3 | -2.7 | +4.2 |
| 52 | XAR | -0.7 | -1.4 | -4.1 | +25.7 | -4.2 | -4.3 | -16.8 | +4.0 |
| 53 | GD | -0.8 | +12.4 | +10.9 | +23.3 | -4.3 | +9.5 | -1.8 | +1.6 |
| 54 | VOO | +3.5 | +2.9 | +12.7 | +21.8 | +0.0 | +0.0 | +0.0 | +0.1 |
| 55 | SPY | +3.5 | +2.9 | +12.7 | +21.7 | +0.0 | +0.0 | +0.0 | +0.0 |
| 56 | ITA | -2.7 | +3.8 | -3.0 | +20.5 | -6.2 | +0.9 | -15.7 | -1.2 |
| 57 | NVDA | +1.6 | -2.2 | +9.9 | +20.3 | -1.9 | -5.1 | -2.8 | -1.4 |
| 58 | ETN | +1.8 | +5.1 | +14.2 | +20.1 | -1.8 | +2.2 | +1.5 | -1.6 |
| 59 | USAR | +29.2 | -27.7 | -2.7 | +19.8 | +25.7 | -30.6 | -15.4 | -1.9 |
| 60 | AMZN | +13.3 | -1.2 | +28.1 | +18.5 | +9.8 | -4.1 | +15.4 | -3.2 |
| 61 | PPA | -2.4 | +0.6 | -4.3 | +18.1 | -5.9 | -2.2 | -17.0 | -3.6 |
| 62 | DLR | -5.7 | -1.5 | +8.1 | +18.0 | -9.2 | -4.4 | -4.6 | -3.7 |
| 63 | PLTR | +44.3 | +29.6 | +35.8 | +13.6 | +40.8 | +26.7 | +23.1 | -8.1 |
| 64 | NEE | -6.9 | -4.9 | -9.8 | +13.1 | -10.4 | -7.7 | -22.5 | -8.6 |
| 65 | HII | +2.5 | -7.7 | -32.2 | +12.5 | -1.0 | -10.5 | -44.9 | -9.2 |
| 66 | TSLA | +13.8 | -16.4 | -10.9 | +11.3 | +10.3 | -19.3 | -23.6 | -10.4 |
| 67 | HUBB | -3.4 | -0.9 | -8.7 | +11.1 | -7.0 | -3.7 | -21.4 | -10.6 |
| 68 | AEP | -10.1 | -7.4 | -7.1 | +10.2 | -13.6 | -10.3 | -19.8 | -11.5 |
| 69 | AMBA | +4.0 | -19.2 | +5.4 | +7.2 | +0.5 | -22.0 | -7.3 | -14.5 |
| 70 | QCOM | -5.3 | -33.4 | +13.8 | +4.8 | -8.8 | -36.2 | +1.1 | -16.9 |
| 71 | DUK | -6.5 | -2.8 | -3.6 | +0.9 | -10.0 | -5.7 | -16.3 | -20.8 |
| 72 | MSFT | +28.7 | +17.4 | +28.0 | -2.0 | +25.2 | +14.5 | +15.3 | -23.7 |
| 73 | SO | -6.9 | -4.3 | -4.1 | -2.0 | -10.5 | -7.1 | -16.8 | -23.7 |
| 74 | PPL | -4.0 | -3.5 | -5.2 | -2.3 | -7.5 | -6.3 | -17.9 | -24.0 |
| 75 | LHX | -12.2 | -15.2 | -25.3 | -3.0 | -15.8 | -18.1 | -37.9 | -24.7 |
| 76 | CRWV | +19.1 | -18.8 | -5.7 | -5.7 | +15.6 | -21.7 | -18.4 | -27.4 |
| 77 | NOC | +1.5 | -0.5 | -23.8 | -6.4 | -2.1 | -3.4 | -36.5 | -28.1 |
| 78 | BWXT | -12.9 | -25.1 | -23.1 | -7.6 | -16.4 | -27.9 | -35.8 | -29.3 |
| 79 | BTC-USD | +25.0 | +24.0 | +4.5 | -8.2 | +21.4 | +21.1 | -8.2 | -29.9 |
| 80 | ONDO-USD | +2.0 | +15.2 | +48.1 | -9.1 | -1.6 | +12.4 | +35.4 | -30.8 |
| 81 | CDNS | -3.8 | -16.0 | +12.1 | -9.7 | -7.4 | -18.9 | -0.6 | -31.4 |
| 82 | LINK-USD | +41.8 | +47.4 | +24.8 | -9.9 | +38.3 | +44.6 | +12.1 | -31.6 |
| 83 | XLM-USD | +14.8 | -3.0 | +13.2 | -10.9 | +11.3 | -5.9 | +0.5 | -32.6 |
| 84 | CEG | -0.8 | -7.5 | -7.1 | -12.6 | -4.3 | -10.3 | -19.8 | -34.3 |
| 85 | QNT-USD | +8.4 | -8.4 | -12.9 | -14.1 | +4.8 | -11.2 | -25.6 | -35.8 |
| 86 | TLN | -14.8 | -17.6 | -16.6 | -14.3 | -18.3 | -20.5 | -29.3 | -36.0 |
| 87 | MP | +39.7 | -10.5 | +3.6 | -15.5 | +36.2 | -13.3 | -9.1 | -37.2 |
| 88 | SMCI | +17.7 | -0.4 | +15.4 | -16.2 | +14.2 | -3.2 | +2.7 | -37.9 |
| 89 | KTOS | +14.4 | -3.5 | -42.5 | -16.3 | +10.9 | -6.4 | -55.2 | -38.0 |
| 90 | ALGO-USD | +3.2 | +4.1 | -10.0 | -19.4 | -0.3 | +1.3 | -22.7 | -41.1 |
| 91 | XRP-USD | +40.2 | +33.5 | +5.7 | -20.7 | +36.6 | +30.6 | -7.0 | -42.4 |
| 92 | NRG | -20.7 | -18.8 | -36.5 | -22.7 | -24.3 | -21.7 | -49.2 | -44.4 |
| 93 | SOL-USD | +31.9 | +34.8 | +13.6 | -24.1 | +28.4 | +31.9 | +0.9 | -45.8 |
| 94 | META | -6.6 | -8.8 | -12.6 | -24.5 | -10.1 | -11.7 | -25.3 | -46.2 |
| 95 | NOW | +30.8 | +26.5 | +28.1 | -26.4 | +27.2 | +23.6 | +15.4 | -48.1 |
| 96 | BAH | +6.4 | -1.2 | +4.7 | -27.7 | +2.8 | -4.1 | -8.0 | -49.4 |
| 97 | VST | -16.5 | -12.6 | -18.5 | -28.0 | -20.1 | -15.5 | -31.2 | -49.7 |
| 98 | HIMS | +10.4 | +30.6 | +99.9 | -29.5 | +6.9 | +27.7 | +87.2 | -51.2 |
| 99 | HBAR-USD | +13.0 | +1.2 | -11.3 | -30.3 | +9.5 | -1.6 | -24.0 | -52.0 |
| 100 | SNPS | +4.5 | -25.6 | -7.3 | -34.8 | +1.0 | -28.5 | -20.0 | -56.5 |
| 101 | AVAV | +1.9 | -12.6 | -41.7 | -35.2 | -1.6 | -15.4 | -54.4 | -56.9 |
| 102 | ORCL | +25.2 | -24.8 | +2.6 | -37.6 | +21.7 | -27.6 | -10.1 | -59.2 |
| 103 | MBLY | +6.9 | -15.5 | -1.1 | -38.0 | +3.4 | -18.3 | -13.8 | -59.7 |
| 104 | COIN | +17.1 | +0.2 | +15.7 | -38.3 | +13.6 | -2.6 | +3.0 | -60.0 |
| 105 | OKLO | +0.6 | -38.6 | -35.8 | -39.8 | -3.0 | -41.4 | -48.5 | -61.5 |
| 106 | SMR | +14.9 | -18.5 | -26.2 | -72.2 | +11.4 | -21.3 | -38.9 | -93.9 |
| 107 | SPCX | +18.4 | - | - | - | +14.9 | - | - | - |

**Top 10 1m:** PLTR +44.3, LINK-USD +41.8, XRP-USD +40.2, MP +39.7, SOL-USD +31.9, NOW +30.8, USAR +29.2, MSFT +28.7, ATEYY +26.0, ORCL +25.2

**Bottom 10 1m:** AMKR -26.0, NRG -20.7, FLNC -17.9, MKSI -17.3, WDC -16.7, VST -16.5, TLN -14.8, KLAC -14.2, GFS -13.6, BWXT -12.9

**Top 10 3m:** LINK-USD +47.4, DELL +47.0, HPE +39.7, SOL-USD +34.8, XRP-USD +33.5, HIMS +30.6, PLTR +29.6, ATEYY +27.7, NOW +26.5, BTC-USD +24.0

**Bottom 10 3m:** MRAM -51.7, RKLB -48.9, FLNC -48.7, GFS -45.9, FN -39.9, AAOI -39.5, OKLO -38.6, QCOM -33.4, BE -32.6, USAR -27.7

**Top 10 6m:** DELL +265.3, MRVL +192.7, HPE +164.1, AMD +133.4, SNDK +122.7, MU +116.5, ALAB +115.5, NBIS +107.0, AAOI +103.4, INTC +100.2

**Bottom 10 6m:** KTOS -42.5, AVAV -41.7, NRG -36.5, OKLO -35.8, HII -32.2, FLNC -31.3, FN -26.6, SMR -26.2, LHX -25.3, NOC -23.8

**Top 10 12m:** SNDK +3162.4, MU +688.0, LITE +601.1, WDC +481.4, AAOI +363.0, BE +354.8, INTC +271.8, DELL +243.2, MRVL +220.2, COHR +216.8

**Bottom 10 12m:** SMR -72.2, OKLO -39.8, COIN -38.3, MBLY -38.0, ORCL -37.6, AVAV -35.2, SNPS -34.8, HBAR-USD -30.3, HIMS -29.5, VST -28.0

### 1b. MA50/MA200 crossover state (all with >= 200 bars)

Spread = (MA50/MA200 - 1) in percent. PxVsMA200 = (px/MA200 - 1) in percent.
Counts: GOLDEN-CROSS 0, DEATH-CROSS 1, ABOVE-BOTH 27, BELOW-BOTH 29,
mixed 49, insufficient-history 1.

| rk | ticker | state | spread% | pxVsMA200% |
|---:|--------|-------|--------:|-----------:|
| 1 | DELL | ABOVE-BOTH | 80.2 | 82.2 |
| 2 | HPE | ABOVE-BOTH | 54.7 | 64.8 |
| 3 | LITE | ABOVE-BOTH | 24.0 | 25.6 |
| 4 | ANET | ABOVE-BOTH | 19.3 | 26.9 |
| 5 | ATEYY | ABOVE-BOTH | 19.3 | 31.8 |
| 6 | ONDO-USD | ABOVE-BOTH | 13.0 | 19.2 |
| 7 | EQIX | ABOVE-BOTH | 11.4 | 11.4 |
| 8 | VDE | ABOVE-BOTH | 7.5 | 16.9 |
| 9 | RTX | ABOVE-BOTH | 6.8 | 10.0 |
| 10 | VOO | ABOVE-BOTH | 6.6 | 8.5 |
| 11 | GD | ABOVE-BOTH | 6.6 | 9.3 |
| 12 | SPY | ABOVE-BOTH | 6.6 | 8.4 |
| 13 | NVDA | ABOVE-BOTH | 6.4 | 7.7 |
| 14 | DLR | ABOVE-BOTH | 6.1 | 6.5 |
| 15 | AMZN | ABOVE-BOTH | 4.9 | 10.3 |
| 16 | XLM-USD | ABOVE-BOTH | 1.9 | 13.3 |
| 17 | LMT | ABOVE-BOTH | -0.0 | 3.1 |
| 18 | LINK-USD | ABOVE-BOTH | -0.8 | 31.4 |
| 19 | WBD | ABOVE-BOTH | -0.9 | 6.3 |
| 20 | MSFT | ABOVE-BOTH | -1.9 | 14.2 |
| 21 | SMCI | ABOVE-BOTH | -2.7 | 12.9 |
| 22 | SOL-USD | ABOVE-BOTH | -4.4 | 19.3 |
| 23 | BTC-USD | ABOVE-BOTH | -5.2 | 14.8 |
| 24 | IAU | ABOVE-BOTH | -7.2 | 3.4 |
| 25 | PLTR | ABOVE-BOTH | -7.6 | 17.1 |
| 26 | NOW | ABOVE-BOTH | -8.8 | 7.6 |
| 27 | XRP-USD | ABOVE-BOTH | -13.2 | 18.0 |
| 28 | SNDK | mixed | 74.1 | 57.0 |
| 29 | MU | mixed | 67.6 | 58.6 |
| 30 | MRVL | mixed | 59.7 | 56.2 |
| 31 | ALAB | mixed | 59.2 | 26.0 |
| 32 | AMD | mixed | 54.0 | 38.7 |
| 33 | ARM | mixed | 52.0 | 20.5 |
| 34 | WDC | mixed | 52.0 | 20.4 |
| 35 | INTC | mixed | 49.9 | 21.8 |
| 36 | NBIS | mixed | 48.8 | 39.1 |
| 37 | AMAT | mixed | 41.1 | 21.9 |
| 38 | CRDO | mixed | 39.0 | 26.2 |
| 39 | LRCX | mixed | 32.3 | 20.5 |
| 40 | MKSI | mixed | 31.8 | 5.8 |
| 41 | AAOI | mixed | 30.5 | 12.2 |
| 42 | KLAC | mixed | 29.8 | 7.1 |
| 43 | ONTO | mixed | 29.5 | 18.9 |
| 44 | BE | mixed | 29.1 | 9.1 |
| 45 | SMH | mixed | 25.7 | 16.8 |
| 46 | CSCO | mixed | 25.2 | 19.8 |
| 47 | ASML | mixed | 22.9 | 20.5 |
| 48 | MRAM | mixed | 21.9 | 7.2 |
| 49 | COHR | mixed | 21.2 | 1.4 |
| 50 | ASMIY | mixed | 19.9 | 12.0 |
| 51 | GEV | mixed | 19.1 | 8.1 |
| 52 | TSM | mixed | 16.0 | 12.0 |
| 53 | VRT | mixed | 15.6 | 0.4 |
| 54 | VGT | mixed | 14.1 | 14.0 |
| 55 | ABBNY | mixed | 14.1 | 9.1 |
| 56 | DTCR | mixed | 11.5 | 7.6 |
| 57 | APH | mixed | 11.5 | 6.5 |
| 58 | HIMS | mixed | 11.3 | 7.6 |
| 59 | ETN | mixed | 10.2 | 8.7 |
| 60 | VOLT | mixed | 9.6 | 1.5 |
| 61 | QQQ | mixed | 9.4 | 8.6 |
| 62 | ITA | mixed | 5.7 | 2.4 |
| 63 | GOOGL | mixed | 5.6 | 5.3 |
| 64 | AMBA | mixed | 5.3 | 0.9 |
| 65 | XAR | mixed | 4.3 | 0.8 |
| 66 | PPA | mixed | 3.8 | 0.8 |
| 67 | QNT-USD | mixed | -9.1 | -5.5 |
| 68 | NOC | mixed | -9.8 | -8.5 |
| 69 | MP | mixed | -10.3 | -0.1 |
| 70 | CEG | mixed | -11.8 | -9.0 |
| 71 | BAH | mixed | -12.0 | -2.0 |
| 72 | ALGO-USD | mixed | -12.4 | -3.1 |
| 73 | HBAR-USD | mixed | -17.7 | -5.5 |
| 74 | COIN | mixed | -19.7 | -6.3 |
| 75 | KTOS | mixed | -27.4 | -25.5 |
| 76 | SMR | mixed | -32.8 | -32.8 |
| 77 | NEE | DEATH-CROSS | -0.0 | -4.0 |
| 78 | GFS | BELOW-BOTH | 18.9 | -12.3 |
| 79 | AMKR | BELOW-BOTH | 18.8 | -13.2 |
| 80 | AEIS | BELOW-BOTH | 7.9 | -7.4 |
| 81 | CDNS | BELOW-BOTH | 7.8 | -4.1 |
| 82 | QCOM | BELOW-BOTH | 6.2 | -5.4 |
| 83 | AVGO | BELOW-BOTH | 5.3 | -1.7 |
| 84 | AEP | BELOW-BOTH | 3.9 | -3.3 |
| 85 | RKLB | BELOW-BOTH | 3.0 | -12.0 |
| 86 | SO | BELOW-BOTH | 2.9 | -1.4 |
| 87 | HUBB | BELOW-BOTH | 2.3 | -2.9 |
| 88 | DUK | BELOW-BOTH | 1.9 | -1.0 |
| 89 | TLN | BELOW-BOTH | 1.4 | -15.1 |
| 90 | PPL | BELOW-BOTH | -0.6 | -3.4 |
| 91 | CRWV | BELOW-BOTH | -2.3 | -6.7 |
| 92 | USAR | BELOW-BOTH | -3.5 | -4.5 |
| 93 | VST | BELOW-BOTH | -3.9 | -14.4 |
| 94 | FN | BELOW-BOTH | -4.2 | -21.3 |
| 95 | META | BELOW-BOTH | -4.9 | -10.8 |
| 96 | SNPS | BELOW-BOTH | -6.1 | -12.5 |
| 97 | MBLY | BELOW-BOTH | -6.5 | -8.7 |
| 98 | BWXT | BELOW-BOTH | -7.4 | -21.6 |
| 99 | LHX | BELOW-BOTH | -7.9 | -16.1 |
| 100 | TSLA | BELOW-BOTH | -9.4 | -11.6 |
| 101 | NRG | BELOW-BOTH | -11.5 | -24.8 |
| 102 | FLNC | BELOW-BOTH | -13.3 | -40.2 |
| 103 | HII | BELOW-BOTH | -14.5 | -15.1 |
| 104 | ORCL | BELOW-BOTH | -15.8 | -16.1 |
| 105 | AVAV | BELOW-BOTH | -26.9 | -30.8 |
| 106 | OKLO | BELOW-BOTH | -30.6 | -40.3 |

### 1c. 52-week high proximity (all 107, closest to high first)

DistHi = (px/w52high - 1) percent (0 = at the high). OffLow = percent above
the 52w low. `part` marks windows shorter than 252 bars.

| rk | ticker | px | w52high | DistHi% | OffLow% | note |
|---:|--------|---:|--------:|--------:|--------:|------|
| 1 | VDE | 176.79 | 179.72 | -1.6 | 50.0 |  |
| 2 | VOO | 703.13 | 714.95 | -1.7 | 21.4 |  |
| 3 | SPY | 764.96 | 777.88 | -1.7 | 21.4 |  |
| 4 | GD | 383.61 | 395.97 | -3.1 | 23.3 |  |
| 5 | WBD | 28.74 | 29.98 | -4.2 | 147.3 |  |
| 6 | QQQ | 708.08 | 745.34 | -5.0 | 27.0 |  |
| 7 | EQIX | 1048.31 | 1110.63 | -5.6 | 46.6 |  |
| 8 | VGT | 116.89 | 125.62 | -7.0 | 40.0 |  |
| 9 | RTX | 209.40 | 225.49 | -7.1 | 40.0 |  |
| 10 | DLR | 187.82 | 202.56 | -7.3 | 28.7 |  |
| 11 | AMZN | 263.00 | 284.02 | -7.4 | 32.3 |  |
| 12 | PPA | 171.14 | 185.40 | -7.7 | 17.5 |  |
| 13 | ITA | 233.73 | 253.22 | -7.7 | 20.2 |  |
| 14 | DUK | 121.03 | 131.16 | -7.7 | 8.9 |  |
| 15 | SO | 89.75 | 97.49 | -7.9 | 9.4 |  |
| 16 | MSFT | 490.30 | 537.65 | -8.8 | 39.2 |  |
| 17 | ATEYY | 216.30 | 237.44 | -8.9 | 205.8 |  |
| 18 | XAR | 267.20 | 296.73 | -10.0 | 24.7 |  |
| 19 | ANET | 189.33 | 210.50 | -10.1 | 63.0 |  |
| 20 | NVDA | 210.25 | 235.47 | -10.7 | 27.4 |  |
| 21 | ETN | 410.17 | 459.96 | -10.8 | 31.0 |  |
| 22 | ABBNY | 97.48 | 109.73 | -11.2 | 49.9 |  |
| 23 | PPL | 34.78 | 39.49 | -11.9 | 6.2 |  |
| 24 | AEP | 120.90 | 137.64 | -12.2 | 17.1 |  |
| 25 | ASML | 1743.38 | 1986.87 | -12.3 | 141.8 |  |
| 26 | DELL | 433.21 | 494.51 | -12.4 | 291.9 |  |
| 27 | HPE | 52.33 | 59.82 | -12.5 | 165.5 |  |
| 28 | APH | 153.79 | 176.32 | -12.8 | 42.2 |  |
| 29 | GOOGL | 350.90 | 402.38 | -12.8 | 70.8 |  |
| 30 | DTCR | 27.96 | 32.34 | -13.5 | 54.2 |  |
| 31 | IAU | 87.63 | 101.57 | -13.7 | 38.1 |  |
| 32 | NEE | 83.63 | 97.17 | -13.9 | 22.4 |  |
| 33 | TSM | 409.64 | 477.57 | -14.2 | 81.3 |  |
| 34 | PLTR | 177.40 | 207.18 | -14.4 | 65.4 |  |
| 35 | CSCO | 110.86 | 129.52 | -14.4 | 70.1 |  |
| 36 | VOLT | 35.80 | 42.05 | -14.9 | 33.9 |  |
| 37 | HUBB | 469.35 | 556.18 | -15.6 | 16.3 |  |
| 38 | LMT | 565.78 | 672.30 | -15.8 | 30.3 |  |
| 39 | ONDO-USD | 0.38 | 0.46 | -17.3 | 68.4 |  |
| 40 | LINK-USD | 11.59 | 14.11 | -17.9 | 61.3 |  |
| 41 | BTC-USD | 79297.53 | 96929.33 | -18.2 | 35.4 |  |
| 42 | SMH | 546.78 | 668.91 | -18.3 | 91.5 |  |
| 43 | GEV | 939.50 | 1174.86 | -20.0 | 71.8 |  |
| 44 | AMD | 458.92 | 580.91 | -21.0 | 203.6 |  |
| 45 | LITE | 823.36 | 1053.09 | -21.8 | 589.9 |  |
| 46 | ASMIY | 962.95 | 1243.50 | -22.6 | 105.8 |  |
| 47 | QNT-USD | 64.60 | 84.35 | -23.4 | 15.6 |  |
| 48 | CDNS | 313.69 | 416.39 | -24.7 | 18.1 |  |
| 49 | AVGO | 362.05 | 480.81 | -24.7 | 24.1 |  |
| 50 | XLM-USD | 0.20 | 0.26 | -24.9 | 37.0 |  |
| 51 | MU | 911.02 | 1213.37 | -24.9 | 683.8 |  |
| 52 | AMBA | 70.77 | 95.51 | -25.9 | 45.5 |  |
| 53 | ONTO | 279.10 | 378.45 | -26.3 | 173.8 |  |
| 54 | TSLA | 356.16 | 489.88 | -27.3 | 19.4 |  |
| 55 | NBIS | 208.29 | 286.69 | -27.3 | 225.1 |  |
| 56 | CRDO | 218.54 | 302.52 | -27.8 | 148.9 |  |
| 57 | NOC | 550.21 | 764.65 | -28.0 | 10.9 |  |
| 58 | MRVL | 227.53 | 316.35 | -28.1 | 265.9 |  |
| 59 | META | 555.90 | 777.70 | -28.5 | 5.8 |  |
| 60 | BAH | 76.56 | 107.58 | -28.8 | 29.2 |  |
| 61 | LRCX | 306.25 | 433.33 | -29.3 | 217.4 |  |
| 62 | AEIS | 274.23 | 388.93 | -29.5 | 89.0 |  |
| 63 | LHX | 263.48 | 375.64 | -29.9 | 0.0 |  |
| 64 | TLN | 306.73 | 445.84 | -31.2 | 1.2 |  |
| 65 | CEG | 271.70 | 401.70 | -32.4 | 15.1 |  |
| 66 | VRT | 254.39 | 376.15 | -32.4 | 109.1 |  |
| 67 | NOW | 129.16 | 192.23 | -32.8 | 55.6 |  |
| 68 | AMAT | 482.78 | 722.23 | -33.2 | 210.7 |  |
| 69 | SOL-USD | 96.92 | 146.75 | -34.0 | 55.8 |  |
| 70 | ALGO-USD | 0.09 | 0.14 | -34.6 | 20.5 |  |
| 71 | HII | 294.73 | 451.78 | -34.8 | 11.7 |  |
| 72 | SPCX | 136.26 | 211.39 | -35.5 | 25.9 | part |
| 73 | COHR | 274.37 | 426.89 | -35.7 | 212.5 |  |
| 74 | XRP-USD | 1.51 | 2.35 | -35.9 | 51.8 |  |
| 75 | BWXT | 151.83 | 237.73 | -36.1 | 0.0 |  |
| 76 | SNPS | 390.20 | 612.17 | -36.3 | 4.8 |  |
| 77 | SNDK | 1484.41 | 2335.00 | -36.4 | 3101.2 |  |
| 78 | QCOM | 158.14 | 250.10 | -36.8 | 27.9 |  |
| 79 | VST | 136.35 | 217.02 | -37.2 | 1.4 |  |
| 80 | INTC | 87.37 | 140.94 | -38.0 | 264.0 |  |
| 81 | MKSI | 272.19 | 444.80 | -38.8 | 172.4 |  |
| 82 | NRG | 111.38 | 182.82 | -39.1 | 0.0 |  |
| 83 | HBAR-USD | 0.08 | 0.13 | -39.6 | 23.2 |  |
| 84 | SMCI | 35.44 | 58.68 | -39.6 | 72.6 |  |
| 85 | CRWV | 85.63 | 143.08 | -40.2 | 40.8 |  |
| 86 | KLAC | 180.34 | 301.37 | -40.2 | 114.8 |  |
| 87 | BE | 203.88 | 345.85 | -41.1 | 320.0 |  |
| 88 | MP | 57.71 | 98.65 | -41.5 | 51.5 |  |
| 89 | WDC | 432.87 | 746.23 | -42.0 | 463.9 |  |
| 90 | ALAB | 276.32 | 483.02 | -42.8 | 175.6 |  |
| 91 | FN | 423.02 | 746.47 | -43.3 | 43.7 |  |
| 92 | MBLY | 8.60 | 15.54 | -44.6 | 31.2 |  |
| 93 | ARM | 237.96 | 439.46 | -45.9 | 127.6 |  |
| 94 | GFS | 46.25 | 89.83 | -48.5 | 46.2 |  |
| 95 | AMKR | 48.07 | 93.55 | -48.6 | 103.0 |  |
| 96 | HIMS | 31.01 | 62.76 | -50.6 | 113.6 |  |
| 97 | AAOI | 109.74 | 223.10 | -50.8 | 463.1 |  |
| 98 | COIN | 185.38 | 387.27 | -52.1 | 31.4 |  |
| 99 | USAR | 18.29 | 38.68 | -52.7 | 53.7 |  |
| 100 | RKLB | 69.35 | 150.23 | -53.8 | 75.6 |  |
| 101 | ORCL | 143.96 | 324.63 | -55.7 | 25.2 |  |
| 102 | KTOS | 54.19 | 130.72 | -58.5 | 23.5 |  |
| 103 | AVAV | 152.34 | 409.83 | -62.8 | 11.5 |  |
| 104 | MRAM | 16.27 | 44.01 | -63.0 | 163.7 |  |
| 105 | FLNC | 11.03 | 32.23 | -65.8 | 63.5 |  |
| 106 | OKLO | 40.47 | 174.14 | -76.8 | 9.9 |  |
| 107 | SMR | 9.30 | 53.43 | -82.6 | 22.5 |  |

---

## 2. Mean reversion (all 107)

### 2a. RSI(14) Wilder (all with >= 15 bars, most oversold first)

Zones: oversold < 30 (0 instruments), neutral ( 100 ), overbought > 70 ( 7 ).

| rk | ticker | RSI14 | zone |
|---:|--------|------:|------|
| 1 | AEP | 30.7 | neutral |
| 2 | BWXT | 30.7 | neutral |
| 3 | NEE | 31.7 | neutral |
| 4 | LHX | 33.3 | neutral |
| 5 | FLNC | 33.3 | neutral |
| 6 | CDNS | 34.2 | neutral |
| 7 | GFS | 34.9 | neutral |
| 8 | TLN | 35.2 | neutral |
| 9 | SO | 36.5 | neutral |
| 10 | PPA | 36.5 | neutral |
| 11 | AVGO | 36.5 | neutral |
| 12 | ITA | 36.8 | neutral |
| 13 | AMKR | 37.1 | neutral |
| 14 | VOLT | 37.3 | neutral |
| 15 | INTC | 37.3 | neutral |
| 16 | VST | 37.4 | neutral |
| 17 | NRG | 37.4 | neutral |
| 18 | FN | 37.5 | neutral |
| 19 | ARM | 37.6 | neutral |
| 20 | MKSI | 38.0 | neutral |
| 21 | KLAC | 38.2 | neutral |
| 22 | ALAB | 38.8 | neutral |
| 23 | GEV | 38.9 | neutral |
| 24 | XAR | 39.1 | neutral |
| 25 | AEIS | 39.4 | neutral |
| 26 | RKLB | 39.5 | neutral |
| 27 | VRT | 39.5 | neutral |
| 28 | SNPS | 39.6 | neutral |
| 29 | HUBB | 40.1 | neutral |
| 30 | AVAV | 40.3 | neutral |
| 31 | HII | 40.3 | neutral |
| 32 | WDC | 40.5 | neutral |
| 33 | META | 41.1 | neutral |
| 34 | QCOM | 41.2 | neutral |
| 35 | AMBA | 41.6 | neutral |
| 36 | AMAT | 41.6 | neutral |
| 37 | SMH | 41.7 | neutral |
| 38 | DUK | 41.7 | neutral |
| 39 | CSCO | 42.2 | neutral |
| 40 | PPL | 42.3 | neutral |
| 41 | COHR | 42.3 | neutral |
| 42 | ABBNY | 42.4 | neutral |
| 43 | OKLO | 42.5 | neutral |
| 44 | APH | 42.7 | neutral |
| 45 | AMD | 42.9 | neutral |
| 46 | ETN | 43.3 | neutral |
| 47 | AAOI | 43.6 | neutral |
| 48 | BE | 43.6 | neutral |
| 49 | CRDO | 44.5 | neutral |
| 50 | DTCR | 44.8 | neutral |
| 51 | RTX | 44.8 | neutral |
| 52 | ONTO | 45.0 | neutral |
| 53 | TSM | 45.6 | neutral |
| 54 | MRAM | 45.8 | neutral |
| 55 | ASMIY | 45.8 | neutral |
| 56 | DLR | 45.9 | neutral |
| 57 | KTOS | 45.9 | neutral |
| 58 | LRCX | 46.0 | neutral |
| 59 | NOC | 46.2 | neutral |
| 60 | NVDA | 46.3 | neutral |
| 61 | CRWV | 46.3 | neutral |
| 62 | VGT | 46.5 | neutral |
| 63 | LMT | 46.9 | neutral |
| 64 | NBIS | 47.0 | neutral |
| 65 | MBLY | 47.1 | neutral |
| 66 | QQQ | 47.3 | neutral |
| 67 | DELL | 48.1 | neutral |
| 68 | EQIX | 48.3 | neutral |
| 69 | ASML | 48.5 | neutral |
| 70 | MU | 48.6 | neutral |
| 71 | LITE | 49.1 | neutral |
| 72 | SNDK | 49.3 | neutral |
| 73 | GD | 49.4 | neutral |
| 74 | ORCL | 50.4 | neutral |
| 75 | HIMS | 50.7 | neutral |
| 76 | HPE | 50.7 | neutral |
| 77 | SMR | 50.8 | neutral |
| 78 | USAR | 51.2 | neutral |
| 79 | SPCX | 51.3 | neutral |
| 80 | GOOGL | 51.4 | neutral |
| 81 | ANET | 52.2 | neutral |
| 82 | CEG | 52.2 | neutral |
| 83 | MRVL | 52.3 | neutral |
| 84 | AMZN | 53.2 | neutral |
| 85 | SPY | 53.6 | neutral |
| 86 | VOO | 53.6 | neutral |
| 87 | ATEYY | 54.0 | neutral |
| 88 | TSLA | 54.6 | neutral |
| 89 | SMCI | 55.9 | neutral |
| 90 | ONDO-USD | 56.3 | neutral |
| 91 | BAH | 58.3 | neutral |
| 92 | MP | 59.6 | neutral |
| 93 | QNT-USD | 59.9 | neutral |
| 94 | ALGO-USD | 62.0 | neutral |
| 95 | NOW | 63.0 | neutral |
| 96 | VDE | 64.2 | neutral |
| 97 | MSFT | 65.6 | neutral |
| 98 | COIN | 66.1 | neutral |
| 99 | PLTR | 66.6 | neutral |
| 100 | XLM-USD | 66.7 | neutral |
| 101 | WBD | 70.8 | overbought |
| 102 | HBAR-USD | 71.1 | overbought |
| 103 | IAU | 73.0 | overbought |
| 104 | LINK-USD | 78.2 | overbought |
| 105 | BTC-USD | 82.6 | overbought |
| 106 | XRP-USD | 84.3 | overbought |
| 107 | SOL-USD | 85.3 | overbought |

### 2b. Distance from 200d MA in standard deviations (z200, most negative first)

Requires 200 bars; reading beyond +/-2 is stretched vs the trailing year.

| rk | ticker | z200 | band |
|---:|--------|-----:|------|
| 1 | NRG | -2.34 | <= -2sd stretched-down |
| 2 | BWXT | -2.33 | <= -2sd stretched-down |
| 3 | VST | -2.13 | <= -2sd stretched-down |
| 4 | TLN | -2.04 | <= -2sd stretched-down |
| 5 | META | -1.73 | -1..-2sd |
| 6 | LHX | -1.68 | -1..-2sd |
| 7 | FLNC | -1.56 | -1..-2sd |
| 8 | OKLO | -1.41 | -1..-2sd |
| 9 | SNPS | -1.32 | -1..-2sd |
| 10 | FN | -1.30 | -1..-2sd |
| 11 | TSLA | -1.17 | -1..-2sd |
| 12 | AVAV | -1.14 | -1..-2sd |
| 13 | HII | -1.02 | -1..-2sd |
| 14 | KTOS | -0.95 | -1..+1sd |
| 15 | ORCL | -0.91 | -1..+1sd |
| 16 | SMR | -0.91 | -1..+1sd |
| 17 | PPL | -0.86 | -1..+1sd |
| 18 | NEE | -0.76 | -1..+1sd |
| 19 | CEG | -0.74 | -1..+1sd |
| 20 | NOC | -0.72 | -1..+1sd |
| 21 | QNT-USD | -0.68 | -1..+1sd |
| 22 | MBLY | -0.57 | -1..+1sd |
| 23 | AEP | -0.56 | -1..+1sd |
| 24 | AMKR | -0.50 | -1..+1sd |
| 25 | HUBB | -0.45 | -1..+1sd |
| 26 | HBAR-USD | -0.42 | -1..+1sd |
| 27 | RKLB | -0.42 | -1..+1sd |
| 28 | GFS | -0.41 | -1..+1sd |
| 29 | CRWV | -0.40 | -1..+1sd |
| 30 | CDNS | -0.39 | -1..+1sd |
| 31 | AEIS | -0.39 | -1..+1sd |
| 32 | SO | -0.32 | -1..+1sd |
| 33 | QCOM | -0.31 | -1..+1sd |
| 34 | COIN | -0.30 | -1..+1sd |
| 35 | DUK | -0.25 | -1..+1sd |
| 36 | ALGO-USD | -0.21 | -1..+1sd |
| 37 | USAR | -0.21 | -1..+1sd |
| 38 | BAH | -0.19 | -1..+1sd |
| 39 | AVGO | -0.16 | -1..+1sd |
| 40 | MP | -0.01 | -1..+1sd |
| 41 | VRT | 0.01 | -1..+1sd |
| 42 | COHR | 0.05 | -1..+1sd |
| 43 | AMBA | 0.06 | -1..+1sd |
| 44 | XAR | 0.11 | -1..+1sd |
| 45 | VOLT | 0.13 | -1..+1sd |
| 46 | MRAM | 0.14 | -1..+1sd |
| 47 | PPA | 0.14 | -1..+1sd |
| 48 | MKSI | 0.21 | -1..+1sd |
| 49 | AAOI | 0.21 | -1..+1sd |
| 50 | BE | 0.25 | -1..+1sd |
| 51 | LMT | 0.26 | -1..+1sd |
| 52 | KLAC | 0.29 | -1..+1sd |
| 53 | HIMS | 0.32 | -1..+1sd |
| 54 | NOW | 0.36 | -1..+1sd |
| 55 | GEV | 0.39 | -1..+1sd |
| 56 | ITA | 0.40 | -1..+1sd |
| 57 | IAU | 0.42 | -1..+1sd |
| 58 | ARM | 0.45 | -1..+1sd |
| 59 | WDC | 0.47 | -1..+1sd |
| 60 | INTC | 0.47 | -1..+1sd |
| 61 | DTCR | 0.56 | -1..+1sd |
| 62 | GOOGL | 0.57 | -1..+1sd |
| 63 | ALAB | 0.59 | -1..+1sd |
| 64 | ASMIY | 0.59 | -1..+1sd |
| 65 | ABBNY | 0.62 | -1..+1sd |
| 66 | LITE | 0.70 | -1..+1sd |
| 67 | ONTO | 0.72 | -1..+1sd |
| 68 | APH | 0.73 | -1..+1sd |
| 69 | AMAT | 0.74 | -1..+1sd |
| 70 | DLR | 0.74 | -1..+1sd |
| 71 | LRCX | 0.77 | -1..+1sd |
| 72 | SMH | 0.78 | -1..+1sd |
| 73 | SMCI | 0.82 | -1..+1sd |
| 74 | EQIX | 0.82 | -1..+1sd |
| 75 | TSM | 0.83 | -1..+1sd |
| 76 | CRDO | 0.87 | -1..+1sd |
| 77 | ETN | 0.89 | -1..+1sd |
| 78 | SNDK | 0.90 | -1..+1sd |
| 79 | AMD | 0.95 | -1..+1sd |
| 80 | NBIS | 0.95 | -1..+1sd |
| 81 | CSCO | 0.97 | -1..+1sd |
| 82 | NVDA | 0.99 | -1..+1sd |
| 83 | QQQ | 1.06 | +1..+2sd |
| 84 | WBD | 1.08 | +1..+2sd |
| 85 | XLM-USD | 1.09 | +1..+2sd |
| 86 | ONDO-USD | 1.10 | +1..+2sd |
| 87 | ASML | 1.12 | +1..+2sd |
| 88 | MU | 1.15 | +1..+2sd |
| 89 | MRVL | 1.15 | +1..+2sd |
| 90 | AMZN | 1.19 | +1..+2sd |
| 91 | VGT | 1.23 | +1..+2sd |
| 92 | PLTR | 1.24 | +1..+2sd |
| 93 | RTX | 1.29 | +1..+2sd |
| 94 | MSFT | 1.39 | +1..+2sd |
| 95 | XRP-USD | 1.46 | +1..+2sd |
| 96 | DELL | 1.50 | +1..+2sd |
| 97 | VDE | 1.50 | +1..+2sd |
| 98 | SPY | 1.59 | +1..+2sd |
| 99 | VOO | 1.60 | +1..+2sd |
| 100 | HPE | 1.69 | +1..+2sd |
| 101 | BTC-USD | 1.72 | +1..+2sd |
| 102 | GD | 1.82 | +1..+2sd |
| 103 | ANET | 1.83 | +1..+2sd |
| 104 | ATEYY | 1.88 | +1..+2sd |
| 105 | SOL-USD | 2.15 | >= +2sd stretched-up |
| 106 | LINK-USD | 3.32 | >= +2sd stretched-up |

No z200 (< 200 bars): SPCX.

### 2c. Consecutive up/down day streak (through 2026-08-24)

+n = n straight up closes, -n = n straight down closes. Sorted longest up first.

| rk | ticker | streak | direction |
|---:|--------|-------:|-----------|
| 1 | SOL-USD | +8 | up |
| 2 | IAU | +4 | up |
| 3 | ANET | +2 | up |
| 4 | BTC-USD | +2 | up |
| 5 | GOOGL | +2 | up |
| 6 | META | +2 | up |
| 7 | MSFT | +2 | up |
| 8 | WBD | +2 | up |
| 9 | AMZN | +1 | up |
| 10 | BE | +1 | up |
| 11 | DUK | +1 | up |
| 12 | LINK-USD | +1 | up |
| 13 | LMT | +1 | up |
| 14 | NOW | +1 | up |
| 15 | PPL | +1 | up |
| 16 | SO | +1 | up |
| 17 | VST | +1 | up |
| 18 | ABBNY | -1 | down |
| 19 | ALGO-USD | -1 | down |
| 20 | AMBA | -1 | down |
| 21 | AMD | -1 | down |
| 22 | APH | -1 | down |
| 23 | ASMIY | -1 | down |
| 24 | ASML | -1 | down |
| 25 | ATEYY | -1 | down |
| 26 | AVAV | -1 | down |
| 27 | AVGO | -1 | down |
| 28 | BAH | -1 | down |
| 29 | BWXT | -1 | down |
| 30 | CDNS | -1 | down |
| 31 | COIN | -1 | down |
| 32 | CSCO | -1 | down |
| 33 | DELL | -1 | down |
| 34 | ETN | -1 | down |
| 35 | GFS | -1 | down |
| 36 | HBAR-USD | -1 | down |
| 37 | HIMS | -1 | down |
| 38 | HPE | -1 | down |
| 39 | HUBB | -1 | down |
| 40 | KTOS | -1 | down |
| 41 | LRCX | -1 | down |
| 42 | MBLY | -1 | down |
| 43 | MP | -1 | down |
| 44 | MRAM | -1 | down |
| 45 | OKLO | -1 | down |
| 46 | ONDO-USD | -1 | down |
| 47 | ORCL | -1 | down |
| 48 | PLTR | -1 | down |
| 49 | QCOM | -1 | down |
| 50 | QNT-USD | -1 | down |
| 51 | QQQ | -1 | down |
| 52 | SMCI | -1 | down |
| 53 | SMR | -1 | down |
| 54 | SPCX | -1 | down |
| 55 | SPY | -1 | down |
| 56 | TSLA | -1 | down |
| 57 | TSM | -1 | down |
| 58 | USAR | -1 | down |
| 59 | VGT | -1 | down |
| 60 | VOO | -1 | down |
| 61 | XAR | -1 | down |
| 62 | XLM-USD | -1 | down |
| 63 | XRP-USD | -1 | down |
| 64 | AAOI | -2 | down |
| 65 | ALAB | -2 | down |
| 66 | AMAT | -2 | down |
| 67 | ARM | -2 | down |
| 68 | COHR | -2 | down |
| 69 | DLR | -2 | down |
| 70 | DTCR | -2 | down |
| 71 | EQIX | -2 | down |
| 72 | LITE | -2 | down |
| 73 | MKSI | -2 | down |
| 74 | MRVL | -2 | down |
| 75 | MU | -2 | down |
| 76 | SMH | -2 | down |
| 77 | SNDK | -2 | down |
| 78 | VDE | -2 | down |
| 79 | VRT | -2 | down |
| 80 | WDC | -2 | down |
| 81 | CEG | -3 | down |
| 82 | FLNC | -3 | down |
| 83 | NRG | -3 | down |
| 84 | TLN | -3 | down |
| 85 | GD | -4 | down |
| 86 | ITA | -4 | down |
| 87 | LHX | -4 | down |
| 88 | NEE | -4 | down |
| 89 | NOC | -4 | down |
| 90 | RTX | -4 | down |
| 91 | AEIS | -5 | down |
| 92 | AEP | -5 | down |
| 93 | AMKR | -5 | down |
| 94 | CRDO | -5 | down |
| 95 | CRWV | -5 | down |
| 96 | FN | -5 | down |
| 97 | GEV | -5 | down |
| 98 | INTC | -5 | down |
| 99 | KLAC | -5 | down |
| 100 | ONTO | -5 | down |
| 101 | RKLB | -5 | down |
| 102 | VOLT | -5 | down |
| 103 | HII | -6 | down |
| 104 | NBIS | -6 | down |
| 105 | PPA | -6 | down |
| 106 | SNPS | -6 | down |
| 107 | NVDA | -7 | down |

---

## 3. Volatility regime (all with >= 61 bars)

### 3a. Realized vol ratio vol20/vol60 (most expanding first)

Regimes: expanding > 1.2 ( 16 ), normal ( 72 ), contracting < 0.8 ( 18 ).

| rk | ticker | vol20%ann | vol60%ann | ratio | regime |
|---:|--------|----------:|----------:|------:|--------|
| 1 | XRP-USD | 77.8 | 51.7 | 1.50 | expanding |
| 2 | HII | 60.4 | 43.0 | 1.41 | expanding |
| 3 | NRG | 82.5 | 58.9 | 1.40 | expanding |
| 4 | AMZN | 59.6 | 43.8 | 1.36 | expanding |
| 5 | PLTR | 104.9 | 78.0 | 1.35 | expanding |
| 6 | QNT-USD | 46.2 | 35.3 | 1.31 | expanding |
| 7 | BTC-USD | 40.0 | 30.9 | 1.29 | expanding |
| 8 | CRWV | 138.4 | 108.3 | 1.28 | expanding |
| 9 | AMKR | 134.4 | 105.4 | 1.28 | expanding |
| 10 | NBIS | 178.6 | 141.7 | 1.26 | expanding |
| 11 | FN | 118.3 | 94.1 | 1.26 | expanding |
| 12 | ALGO-USD | 59.8 | 47.6 | 1.26 | expanding |
| 13 | LINK-USD | 58.9 | 47.0 | 1.25 | expanding |
| 14 | MSFT | 56.8 | 45.5 | 1.25 | expanding |
| 15 | XLM-USD | 60.3 | 48.6 | 1.24 | expanding |
| 16 | COHR | 137.7 | 113.3 | 1.22 | expanding |
| 17 | VRT | 91.6 | 77.0 | 1.19 | normal |
| 18 | LHX | 41.7 | 35.1 | 1.19 | normal |
| 19 | HIMS | 108.0 | 93.0 | 1.16 | normal |
| 20 | LITE | 118.5 | 102.9 | 1.15 | normal |
| 21 | OKLO | 97.1 | 84.7 | 1.15 | normal |
| 22 | ONTO | 115.0 | 101.2 | 1.14 | normal |
| 23 | VST | 50.6 | 45.0 | 1.12 | normal |
| 24 | AEIS | 94.1 | 84.1 | 1.12 | normal |
| 25 | HBAR-USD | 42.4 | 38.0 | 1.11 | normal |
| 26 | MP | 79.1 | 71.2 | 1.11 | normal |
| 27 | BWXT | 45.8 | 41.3 | 1.11 | normal |
| 28 | AAOI | 164.5 | 148.7 | 1.11 | normal |
| 29 | ETN | 55.8 | 50.6 | 1.10 | normal |
| 30 | SOL-USD | 44.5 | 40.5 | 1.10 | normal |
| 31 | COIN | 76.3 | 69.5 | 1.10 | normal |
| 32 | XAR | 34.4 | 31.5 | 1.09 | normal |
| 33 | MKSI | 90.2 | 83.0 | 1.09 | normal |
| 34 | KTOS | 72.9 | 68.0 | 1.07 | normal |
| 35 | APH | 48.8 | 45.7 | 1.07 | normal |
| 36 | CSCO | 42.4 | 39.8 | 1.06 | normal |
| 37 | VDE | 24.7 | 23.2 | 1.06 | normal |
| 38 | CRDO | 110.0 | 103.8 | 1.06 | normal |
| 39 | VOLT | 34.9 | 33.0 | 1.06 | normal |
| 40 | PPA | 25.6 | 24.3 | 1.05 | normal |
| 41 | EQIX | 29.2 | 27.8 | 1.05 | normal |
| 42 | TLN | 60.8 | 57.9 | 1.05 | normal |
| 43 | USAR | 97.7 | 94.0 | 1.04 | normal |
| 44 | SNDK | 144.2 | 139.5 | 1.03 | normal |
| 45 | ANET | 61.6 | 60.1 | 1.02 | normal |
| 46 | AMD | 78.1 | 76.8 | 1.02 | normal |
| 47 | HUBB | 38.7 | 38.1 | 1.02 | normal |
| 48 | GOOGL | 38.7 | 38.3 | 1.01 | normal |
| 49 | ITA | 25.6 | 25.4 | 1.01 | normal |
| 50 | GFS | 70.3 | 69.8 | 1.01 | normal |
| 51 | LRCX | 87.4 | 86.9 | 1.01 | normal |
| 52 | ONDO-USD | 64.9 | 65.3 | 0.99 | normal |
| 53 | META | 47.4 | 48.5 | 0.98 | normal |
| 54 | ASMIY | 62.6 | 64.0 | 0.98 | normal |
| 55 | WDC | 101.7 | 104.5 | 0.97 | normal |
| 56 | DTCR | 28.8 | 29.7 | 0.97 | normal |
| 57 | ALAB | 107.0 | 110.3 | 0.97 | normal |
| 58 | BE | 118.5 | 122.4 | 0.97 | normal |
| 59 | SMR | 87.6 | 91.0 | 0.96 | normal |
| 60 | AMAT | 81.9 | 86.2 | 0.95 | normal |
| 61 | VOO | 13.1 | 13.8 | 0.95 | normal |
| 62 | IAU | 25.1 | 26.6 | 0.95 | normal |
| 63 | SPY | 13.2 | 14.0 | 0.94 | normal |
| 64 | MU | 99.3 | 105.5 | 0.94 | normal |
| 65 | DUK | 18.5 | 19.9 | 0.93 | normal |
| 66 | VGT | 29.6 | 31.9 | 0.93 | normal |
| 67 | AEP | 19.3 | 20.9 | 0.93 | normal |
| 68 | MRAM | 105.2 | 114.8 | 0.92 | normal |
| 69 | ARM | 87.6 | 95.9 | 0.91 | normal |
| 70 | GEV | 53.3 | 58.4 | 0.91 | normal |
| 71 | ABBNY | 34.0 | 37.5 | 0.91 | normal |
| 72 | AVAV | 75.3 | 84.1 | 0.90 | normal |
| 73 | NOC | 27.3 | 30.5 | 0.89 | normal |
| 74 | CEG | 35.1 | 39.3 | 0.89 | normal |
| 75 | PPL | 17.9 | 20.0 | 0.89 | normal |
| 76 | INTC | 74.0 | 84.6 | 0.88 | normal |
| 77 | DELL | 82.5 | 95.4 | 0.86 | normal |
| 78 | QQQ | 22.5 | 26.1 | 0.86 | normal |
| 79 | ATEYY | 78.6 | 91.0 | 0.86 | normal |
| 80 | WBD | 17.9 | 21.0 | 0.85 | normal |
| 81 | BAH | 38.8 | 45.6 | 0.85 | normal |
| 82 | ORCL | 56.5 | 66.7 | 0.85 | normal |
| 83 | NVDA | 34.0 | 40.4 | 0.84 | normal |
| 84 | SMH | 45.1 | 54.4 | 0.83 | normal |
| 85 | RKLB | 78.3 | 94.7 | 0.83 | normal |
| 86 | SNPS | 29.5 | 35.8 | 0.82 | normal |
| 87 | MRVL | 97.2 | 118.8 | 0.82 | normal |
| 88 | SMCI | 97.6 | 121.3 | 0.80 | normal |
| 89 | TSM | 39.4 | 49.5 | 0.79 | contracting |
| 90 | AVGO | 44.9 | 56.5 | 0.79 | contracting |
| 91 | LMT | 28.2 | 35.5 | 0.79 | contracting |
| 92 | SO | 15.2 | 19.2 | 0.79 | contracting |
| 93 | KLAC | 68.2 | 86.5 | 0.79 | contracting |
| 94 | ASML | 43.7 | 56.5 | 0.77 | contracting |
| 95 | HPE | 56.0 | 73.8 | 0.76 | contracting |
| 96 | QCOM | 46.9 | 62.0 | 0.76 | contracting |
| 97 | GD | 17.1 | 22.9 | 0.75 | contracting |
| 98 | NOW | 51.3 | 69.0 | 0.74 | contracting |
| 99 | DLR | 26.5 | 35.8 | 0.74 | contracting |
| 100 | RTX | 21.4 | 30.1 | 0.71 | contracting |
| 101 | NEE | 12.5 | 17.6 | 0.71 | contracting |
| 102 | FLNC | 89.1 | 126.5 | 0.70 | contracting |
| 103 | AMBA | 73.9 | 108.9 | 0.68 | contracting |
| 104 | MBLY | 49.9 | 74.1 | 0.67 | contracting |
| 105 | TSLA | 37.4 | 58.2 | 0.64 | contracting |
| 106 | CDNS | 23.4 | 43.5 | 0.54 | contracting |

No ratio (< 61 bars): SPCX.

### 3b. Current vol percentile in own history (highest first)

Percentile of today's 20d realized vol among ALL rolling-20d vols of the same
instrument since its first bar. Low = unusually calm for this name.

| rk | ticker | own-pctile | vol20%ann |
|---:|--------|-----------:|----------:|
| 1 | FN | 100% | 118.3 |
| 2 | AMKR | 100% | 134.4 |
| 3 | COHR | 99% | 137.7 |
| 4 | MSFT | 99% | 56.8 |
| 5 | AEIS | 98% | 94.1 |
| 6 | NRG | 97% | 82.5 |
| 7 | LHX | 97% | 41.7 |
| 8 | ONTO | 97% | 115.0 |
| 9 | LITE | 97% | 118.5 |
| 10 | HII | 96% | 60.4 |
| 11 | AMAT | 96% | 81.9 |
| 12 | LRCX | 96% | 87.4 |
| 13 | WDC | 96% | 101.7 |
| 14 | ETN | 96% | 55.8 |
| 15 | PLTR | 95% | 104.9 |
| 16 | MKSI | 95% | 90.2 |
| 17 | MU | 94% | 99.3 |
| 18 | NBIS | 94% | 178.6 |
| 19 | AMZN | 93% | 59.6 |
| 20 | CSCO | 93% | 42.4 |
| 21 | HPE | 93% | 56.0 |
| 22 | XAR | 92% | 34.4 |
| 23 | MRVL | 92% | 97.2 |
| 24 | VRT | 91% | 91.6 |
| 25 | KLAC | 91% | 68.2 |
| 26 | CRWV | 91% | 138.4 |
| 27 | DELL | 91% | 82.5 |
| 28 | APH | 91% | 48.8 |
| 29 | ATEYY | 90% | 78.6 |
| 30 | MRAM | 89% | 105.2 |
| 31 | CRDO | 89% | 110.0 |
| 32 | PPA | 89% | 25.6 |
| 33 | IAU | 89% | 25.1 |
| 34 | AMD | 89% | 78.1 |
| 35 | AAOI | 88% | 164.5 |
| 36 | KTOS | 88% | 72.9 |
| 37 | DTCR | 87% | 28.8 |
| 38 | SNDK | 87% | 144.2 |
| 39 | GFS | 87% | 70.3 |
| 40 | VOLT | 87% | 34.9 |
| 41 | HUBB | 87% | 38.7 |
| 42 | BE | 86% | 118.5 |
| 43 | AVAV | 85% | 75.3 |
| 44 | HIMS | 85% | 108.0 |
| 45 | ASMIY | 85% | 62.6 |
| 46 | BWXT | 85% | 45.8 |
| 47 | INTC | 84% | 74.0 |
| 48 | ITA | 84% | 25.6 |
| 49 | ORCL | 84% | 56.5 |
| 50 | MP | 83% | 79.1 |
| 51 | ANET | 83% | 61.6 |
| 52 | ABBNY | 82% | 34.0 |
| 53 | SMH | 82% | 45.1 |
| 54 | XRP-USD | 81% | 77.8 |
| 55 | BAH | 79% | 38.8 |
| 56 | TLN | 78% | 60.8 |
| 57 | ARM | 78% | 87.6 |
| 58 | GOOGL | 78% | 38.7 |
| 59 | QCOM | 78% | 46.9 |
| 60 | VGT | 77% | 29.6 |
| 61 | LMT | 77% | 28.2 |
| 62 | ALAB | 76% | 107.0 |
| 63 | SMCI | 74% | 97.6 |
| 64 | SPCX | 73% | 101.2 |
| 65 | AVGO | 72% | 44.9 |
| 66 | AMBA | 72% | 73.9 |
| 67 | NOW | 71% | 51.3 |
| 68 | META | 71% | 47.4 |
| 69 | EQIX | 70% | 29.2 |
| 70 | OKLO | 69% | 97.1 |
| 71 | NOC | 68% | 27.3 |
| 72 | VST | 67% | 50.6 |
| 73 | DUK | 67% | 18.5 |
| 74 | QQQ | 65% | 22.5 |
| 75 | TSM | 63% | 39.4 |
| 76 | USAR | 62% | 97.7 |
| 77 | ASML | 62% | 43.7 |
| 78 | GEV | 62% | 53.3 |
| 79 | VDE | 61% | 24.7 |
| 80 | XLM-USD | 59% | 60.3 |
| 81 | FLNC | 59% | 89.1 |
| 82 | RKLB | 56% | 78.3 |
| 83 | BTC-USD | 56% | 40.0 |
| 84 | PPL | 53% | 17.9 |
| 85 | COIN | 52% | 76.3 |
| 86 | AEP | 51% | 19.3 |
| 87 | DLR | 50% | 26.5 |
| 88 | RTX | 49% | 21.4 |
| 89 | SMR | 47% | 87.6 |
| 90 | SPY | 45% | 13.2 |
| 91 | VOO | 45% | 13.1 |
| 92 | GD | 42% | 17.1 |
| 93 | ALGO-USD | 40% | 59.8 |
| 94 | LINK-USD | 40% | 58.9 |
| 95 | MBLY | 40% | 49.9 |
| 96 | CEG | 35% | 35.1 |
| 97 | SNPS | 34% | 29.5 |
| 98 | QNT-USD | 32% | 46.2 |
| 99 | SO | 31% | 15.2 |
| 100 | ONDO-USD | 29% | 64.9 |
| 101 | NVDA | 22% | 34.0 |
| 102 | HBAR-USD | 18% | 42.4 |
| 103 | CDNS | 15% | 23.4 |
| 104 | TSLA | 12% | 37.4 |
| 105 | SOL-USD | 11% | 44.5 |
| 106 | WBD | 7% | 17.9 |
| 107 | NEE | 1% | 12.5 |

### 3c. Beta to SPY, 60d (highest first; corr60 alongside)

| rk | ticker | beta60 | corr60 |
|---:|--------|-------:|-------:|
| 1 | AAOI | 5.35 | 0.50 |
| 2 | FLNC | 5.24 | 0.58 |
| 3 | SNDK | 5.19 | 0.52 |
| 4 | MRAM | 5.07 | 0.62 |
| 5 | ALAB | 4.99 | 0.63 |
| 6 | MRVL | 4.87 | 0.57 |
| 7 | BE | 4.86 | 0.55 |
| 8 | NBIS | 4.74 | 0.47 |
| 9 | USAR | 4.39 | 0.65 |
| 10 | SMCI | 4.35 | 0.50 |
| 11 | ONTO | 4.29 | 0.59 |
| 12 | ARM | 4.26 | 0.62 |
| 13 | MU | 4.25 | 0.56 |
| 14 | COHR | 4.15 | 0.51 |
| 15 | SMR | 3.97 | 0.61 |
| 16 | LRCX | 3.90 | 0.63 |
| 17 | AMKR | 3.89 | 0.51 |
| 18 | ATEYY | 3.87 | 0.59 |
| 19 | WDC | 3.86 | 0.52 |
| 20 | CRWV | 3.84 | 0.50 |
| 21 | CRDO | 3.77 | 0.51 |
| 22 | OKLO | 3.76 | 0.62 |
| 23 | MKSI | 3.73 | 0.63 |
| 24 | KLAC | 3.67 | 0.59 |
| 25 | AMD | 3.64 | 0.66 |
| 26 | AMBA | 3.59 | 0.46 |
| 27 | AMAT | 3.58 | 0.58 |
| 28 | INTC | 3.58 | 0.59 |
| 29 | LITE | 3.44 | 0.47 |
| 30 | AEIS | 3.43 | 0.57 |
| 31 | RKLB | 3.38 | 0.50 |
| 32 | FN | 3.20 | 0.47 |
| 33 | MBLY | 3.11 | 0.59 |
| 34 | VRT | 3.08 | 0.56 |
| 35 | HIMS | 3.00 | 0.45 |
| 36 | SMH | 2.90 | 0.74 |
| 37 | GFS | 2.89 | 0.58 |
| 38 | TSLA | 2.84 | 0.68 |
| 39 | ASMIY | 2.80 | 0.61 |
| 40 | MP | 2.72 | 0.53 |
| 41 | QCOM | 2.69 | 0.61 |
| 42 | DELL | 2.61 | 0.38 |
| 43 | ORCL | 2.61 | 0.54 |
| 44 | TSM | 2.56 | 0.72 |
| 45 | ANET | 2.48 | 0.58 |
| 46 | AVAV | 2.43 | 0.40 |
| 47 | HPE | 2.43 | 0.46 |
| 48 | ASML | 2.43 | 0.60 |
| 49 | ETN | 2.37 | 0.65 |
| 50 | AVGO | 2.19 | 0.54 |
| 51 | KTOS | 2.18 | 0.45 |
| 52 | GEV | 2.14 | 0.51 |
| 53 | PLTR | 2.12 | 0.38 |
| 54 | NVDA | 1.99 | 0.69 |
| 55 | VGT | 1.95 | 0.86 |
| 56 | COIN | 1.88 | 0.38 |
| 57 | TLN | 1.84 | 0.44 |
| 58 | ABBNY | 1.81 | 0.67 |
| 59 | ONDO-USD | 1.80 | 0.31 |
| 60 | QQQ | 1.72 | 0.92 |
| 61 | ALGO-USD | 1.68 | 0.34 |
| 62 | XLM-USD | 1.62 | 0.25 |
| 63 | SOL-USD | 1.62 | 0.39 |
| 64 | APH | 1.61 | 0.49 |
| 65 | DTCR | 1.54 | 0.73 |
| 66 | CDNS | 1.52 | 0.49 |
| 67 | VOLT | 1.51 | 0.64 |
| 68 | LINK-USD | 1.46 | 0.35 |
| 69 | AMZN | 1.41 | 0.45 |
| 70 | XRP-USD | 1.33 | 0.29 |
| 71 | BWXT | 1.33 | 0.45 |
| 72 | GOOGL | 1.32 | 0.48 |
| 73 | XAR | 1.31 | 0.58 |
| 74 | CSCO | 1.28 | 0.45 |
| 75 | META | 1.24 | 0.36 |
| 76 | HBAR-USD | 1.20 | 0.34 |
| 77 | VST | 1.20 | 0.37 |
| 78 | HUBB | 1.19 | 0.43 |
| 79 | MSFT | 1.15 | 0.35 |
| 80 | SNPS | 1.07 | 0.42 |
| 81 | SPY | 1.00 | 1.00 |
| 82 | VOO | 0.99 | 1.00 |
| 83 | BTC-USD | 0.96 | 0.33 |
| 84 | PPA | 0.93 | 0.53 |
| 85 | CEG | 0.93 | 0.33 |
| 86 | IAU | 0.92 | 0.48 |
| 87 | HII | 0.85 | 0.28 |
| 88 | ITA | 0.77 | 0.42 |
| 89 | QNT-USD | 0.76 | 0.24 |
| 90 | NRG | 0.76 | 0.18 |
| 91 | NOW | 0.66 | 0.13 |
| 92 | DLR | 0.46 | 0.18 |
| 93 | EQIX | 0.39 | 0.20 |
| 94 | WBD | 0.35 | 0.23 |
| 95 | BAH | 0.17 | 0.05 |
| 96 | GD | 0.14 | 0.08 |
| 97 | NOC | -0.03 | -0.02 |
| 98 | NEE | -0.06 | -0.05 |
| 99 | PPL | -0.14 | -0.10 |
| 100 | RTX | -0.15 | -0.07 |
| 101 | LMT | -0.24 | -0.09 |
| 102 | AEP | -0.27 | -0.18 |
| 103 | LHX | -0.32 | -0.13 |
| 104 | SO | -0.42 | -0.31 |
| 105 | VDE | -0.47 | -0.28 |
| 106 | DUK | -0.48 | -0.34 |

No beta (< 61 common bars): SPCX.

---

## 4. Composite signal dashboard (all 107, strongest signal first)

Rules (verbatim from the mandate):

- LONG if ALL hold: positive 3m momentum AND RSI not overbought (< 70) AND
  vol contracting (ratio < 0.8) AND price above MA50.
- SHORT if ALL hold: negative 3m momentum AND RSI oversold (< 30) AND vol
  expanding (ratio > 1.2) AND price below MA50.
- Everything else NEUTRAL. Confidence = share of that side's four conditions
  met (100 only for clean LONG/SHORT); lean flags which side dominates a
  NEUTRAL row. Gate codes: M=momentum, R=RSI, V=vol-regime, A=MA50; `.` = gate
  failed. Positive-momentum side gates shown for context on every row.

Result: **5 LONG, 0 SHORT, 102 NEUTRAL** of 107.

| rk | signal | conf% | ticker | long-gates | short-gates | RSI14 | volRatio | MAstate | 3m% | 12m% |
|---:|--------|------:|--------|------------|-------------|------:|---------:|---------|----:|----:|
| 1 | LONG | 100 | HPE | MRVA | ... | 50.7 | 0.76 | ABOVE-BOTH | +39.7 | +144.8 |
| 2 | LONG | 100 | NOW | MRVA | ... | 63.0 | 0.74 | ABOVE-BOTH | +26.5 | -26.4 |
| 3 | LONG | 100 | RTX | MRVA | ... | 44.8 | 0.71 | ABOVE-BOTH | +18.7 | +35.9 |
| 4 | LONG | 100 | GD | MRVA | ... | 49.4 | 0.75 | ABOVE-BOTH | +12.4 | +23.3 |
| 5 | LONG | 100 | LMT | MRVA | ... | 46.9 | 0.79 | ABOVE-BOTH | +6.8 | +29.9 |
| 6 | NEUTRAL-lean-L | 75 | ALGO-USD | MR.A | ..V | 62.0 | 1.26 | mixed | +4.1 | -19.4 |
| 7 | NEUTRAL-lean-S | 75 | AMKR | .R. | M.VA | 37.1 | 1.28 | BELOW-BOTH | -26.8 | +108.9 |
| 8 | NEUTRAL-lean-L | 75 | ANET | MR.A | ... | 52.2 | 1.02 | ABOVE-BOTH | +22.9 | +43.4 |
| 9 | NEUTRAL-lean-L | 75 | ASML | MRV | ...A | 48.5 | 0.77 | mixed | +6.9 | +138.6 |
| 10 | NEUTRAL-lean-L | 75 | ATEYY | MR.A | ... | 54.0 | 0.86 | ABOVE-BOTH | +27.7 | +192.7 |
| 11 | NEUTRAL-lean-S | 75 | COHR | .R. | M.VA | 42.3 | 1.22 | mixed | -27.3 | +216.8 |
| 12 | NEUTRAL-lean-L | 75 | COIN | MR.A | ... | 66.1 | 1.10 | mixed | +0.2 | -38.3 |
| 13 | NEUTRAL-lean-S | 75 | CRWV | .R. | M.VA | 46.3 | 1.28 | BELOW-BOTH | -18.8 | -5.7 |
| 14 | NEUTRAL-lean-L | 75 | DELL | MR.A | ... | 48.1 | 0.86 | ABOVE-BOTH | +47.0 | +243.2 |
| 15 | NEUTRAL-lean-L | 75 | DLR | .RVA | M.. | 45.9 | 0.74 | ABOVE-BOTH | -1.5 | +18.0 |
| 16 | NEUTRAL-lean-S | 75 | FN | .R. | M.VA | 37.5 | 1.26 | BELOW-BOTH | -39.9 | +52.7 |
| 17 | NEUTRAL-lean-S | 75 | HII | .R. | M.VA | 40.3 | 1.41 | BELOW-BOTH | -7.7 | +12.5 |
| 18 | NEUTRAL-lean-L | 75 | MSFT | MR.A | ..V | 65.6 | 1.25 | ABOVE-BOTH | +17.4 | -2.0 |
| 19 | NEUTRAL-lean-S | 75 | NBIS | .R. | M.VA | 47.0 | 1.26 | mixed | -3.0 | +214.7 |
| 20 | NEUTRAL-lean-S | 75 | NRG | .R. | M.VA | 37.4 | 1.40 | BELOW-BOTH | -18.8 | -22.7 |
| 21 | NEUTRAL-lean-L | 75 | ONDO-USD | MR.A | ... | 56.3 | 0.99 | ABOVE-BOTH | +15.2 | -9.1 |
| 22 | NEUTRAL-lean-L | 75 | PLTR | MR.A | ..V | 66.6 | 1.35 | ABOVE-BOTH | +29.6 | +13.6 |
| 23 | NEUTRAL-lean-L | 75 | SPY | MR.A | ... | 53.6 | 0.94 | ABOVE-BOTH | +2.9 | +21.7 |
| 24 | NEUTRAL-lean-L | 75 | TSM | MRV | ...A | 45.6 | 0.79 | mixed | +1.5 | +82.2 |
| 25 | NEUTRAL-lean-L | 75 | VDE | MR.A | ... | 64.2 | 1.06 | ABOVE-BOTH | +5.9 | +50.1 |
| 26 | NEUTRAL-lean-L | 75 | VOO | MR.A | ... | 53.6 | 0.95 | ABOVE-BOTH | +2.9 | +21.8 |
| 27 | NEUTRAL-lean-S | 50 | AAOI | .R. | M..A | 43.6 | 1.11 | mixed | -39.5 | +363.0 |
| 28 | NEUTRAL-lean-S | 50 | ABBNY | .R. | M..A | 42.4 | 0.91 | mixed | -8.4 | +49.8 |
| 29 | NEUTRAL-lean-S | 50 | AEIS | .R. | M..A | 39.4 | 1.12 | BELOW-BOTH | -15.6 | +85.5 |
| 30 | NEUTRAL-lean-S | 50 | AEP | .R. | M..A | 30.7 | 0.93 | BELOW-BOTH | -7.4 | +10.2 |
| 31 | NEUTRAL-lean-S | 50 | ALAB | .R. | M..A | 38.8 | 0.97 | mixed | -10.0 | +55.6 |
| 32 | NEUTRAL-lean-L | 50 | AMAT | MR. | ...A | 41.6 | 0.95 | mixed | +11.8 | +203.7 |
| 33 | NEUTRAL | 50 | AMBA | .RV | M..A | 41.6 | 0.68 | mixed | -19.2 | +7.2 |
| 34 | NEUTRAL-lean-S | 50 | AMD | .R. | M..A | 42.9 | 1.02 | mixed | -1.8 | +180.3 |
| 35 | NEUTRAL | 50 | AMZN | .R.A | M.V | 53.2 | 1.36 | ABOVE-BOTH | -1.2 | +18.5 |
| 36 | NEUTRAL-lean-L | 50 | APH | MR. | ...A | 42.7 | 1.07 | mixed | +16.6 | +42.3 |
| 37 | NEUTRAL-lean-S | 50 | ARM | .R. | M..A | 37.6 | 0.91 | mixed | -22.4 | +78.5 |
| 38 | NEUTRAL-lean-S | 50 | ASMIY | .R. | M..A | 45.8 | 0.98 | mixed | -7.7 | +107.0 |
| 39 | NEUTRAL-lean-S | 50 | AVAV | .R. | M..A | 40.3 | 0.90 | BELOW-BOTH | -12.6 | -35.2 |
| 40 | NEUTRAL | 50 | AVGO | .RV | M..A | 36.5 | 0.79 | BELOW-BOTH | -12.4 | +25.9 |
| 41 | NEUTRAL-lean-L | 50 | BAH | .R.A | M.. | 58.3 | 0.85 | mixed | -1.2 | -27.7 |
| 42 | NEUTRAL-lean-S | 50 | BE | .R. | M..A | 43.6 | 0.97 | mixed | -32.6 | +354.8 |
| 43 | NEUTRAL-lean-L | 50 | BTC-USD | M..A | ..V | 82.6 | 1.29 | ABOVE-BOTH | +24.0 | -8.2 |
| 44 | NEUTRAL-lean-S | 50 | BWXT | .R. | M..A | 30.7 | 1.11 | BELOW-BOTH | -25.1 | -7.6 |
| 45 | NEUTRAL | 50 | CDNS | .RV | M..A | 34.2 | 0.54 | BELOW-BOTH | -16.0 | -9.7 |
| 46 | NEUTRAL-lean-L | 50 | CEG | .R.A | M.. | 52.2 | 0.89 | mixed | -7.5 | -12.6 |
| 47 | NEUTRAL-lean-L | 50 | CRDO | MR. | ...A | 44.5 | 1.06 | mixed | +0.1 | +97.1 |
| 48 | NEUTRAL-lean-S | 50 | CSCO | .R. | M..A | 42.2 | 1.06 | mixed | -7.6 | +68.8 |
| 49 | NEUTRAL-lean-S | 50 | DTCR | .R. | M..A | 44.8 | 0.97 | mixed | -7.9 | +51.9 |
| 50 | NEUTRAL-lean-S | 50 | DUK | .R. | M..A | 41.7 | 0.93 | BELOW-BOTH | -2.8 | +0.9 |
| 51 | NEUTRAL-lean-L | 50 | EQIX | .R.A | M.. | 48.3 | 1.05 | ABOVE-BOTH | -2.5 | +38.7 |
| 52 | NEUTRAL-lean-L | 50 | ETN | MR. | ...A | 43.3 | 1.10 | mixed | +5.1 | +20.1 |
| 53 | NEUTRAL | 50 | FLNC | .RV | M..A | 33.3 | 0.70 | BELOW-BOTH | -48.7 | +61.3 |
| 54 | NEUTRAL-lean-S | 50 | GEV | .R. | M..A | 38.9 | 0.91 | mixed | -9.5 | +55.4 |
| 55 | NEUTRAL-lean-S | 50 | GFS | .R. | M..A | 34.9 | 1.01 | BELOW-BOTH | -45.9 | +42.1 |
| 56 | NEUTRAL-lean-S | 50 | GOOGL | .R. | M..A | 51.4 | 1.01 | mixed | -8.3 | +76.2 |
| 57 | NEUTRAL-lean-L | 50 | HBAR-USD | M..A | ... | 71.1 | 1.11 | mixed | +1.2 | -30.3 |
| 58 | NEUTRAL-lean-L | 50 | HIMS | MR. | ...A | 50.7 | 1.16 | mixed | +30.6 | -29.5 |
| 59 | NEUTRAL-lean-S | 50 | HUBB | .R. | M..A | 40.1 | 1.02 | BELOW-BOTH | -0.9 | +11.1 |
| 60 | NEUTRAL-lean-L | 50 | IAU | M..A | ... | 73.0 | 0.95 | ABOVE-BOTH | +3.3 | +39.3 |
| 61 | NEUTRAL-lean-S | 50 | INTC | .R. | M..A | 37.3 | 0.88 | mixed | -27.1 | +271.8 |
| 62 | NEUTRAL-lean-L | 50 | ITA | MR. | ...A | 36.8 | 1.01 | mixed | +3.8 | +20.5 |
| 63 | NEUTRAL | 50 | KLAC | .RV | M..A | 38.2 | 0.79 | mixed | -4.4 | +107.8 |
| 64 | NEUTRAL-lean-L | 50 | KTOS | .R.A | M.. | 45.9 | 1.07 | mixed | -3.5 | -16.3 |
| 65 | NEUTRAL-lean-S | 50 | LHX | .R. | M..A | 33.3 | 1.19 | BELOW-BOTH | -15.2 | -3.0 |
| 66 | NEUTRAL-lean-L | 50 | LINK-USD | M..A | ..V | 78.2 | 1.25 | ABOVE-BOTH | +47.4 | -9.9 |
| 67 | NEUTRAL-lean-L | 50 | LITE | .R.A | M.. | 49.1 | 1.15 | ABOVE-BOTH | -13.0 | +601.1 |
| 68 | NEUTRAL-lean-L | 50 | LRCX | MR. | ...A | 46.0 | 1.01 | mixed | +0.4 | +212.9 |
| 69 | NEUTRAL | 50 | MBLY | .RV | M..A | 47.1 | 0.67 | BELOW-BOTH | -15.5 | -38.0 |
| 70 | NEUTRAL-lean-S | 50 | META | .R. | M..A | 41.1 | 0.98 | BELOW-BOTH | -8.8 | -24.5 |
| 71 | NEUTRAL-lean-S | 50 | MKSI | .R. | M..A | 38.0 | 1.09 | mixed | -15.0 | +175.2 |
| 72 | NEUTRAL-lean-L | 50 | MP | .R.A | M.. | 59.6 | 1.11 | mixed | -10.5 | -15.5 |
| 73 | NEUTRAL-lean-S | 50 | MRAM | .R. | M..A | 45.8 | 0.92 | mixed | -51.7 | +166.7 |
| 74 | NEUTRAL-lean-L | 50 | MRVL | MR. | ...A | 52.3 | 0.82 | mixed | +15.9 | +220.2 |
| 75 | NEUTRAL-lean-L | 50 | MU | MR. | ...A | 48.6 | 0.94 | mixed | +21.3 | +688.0 |
| 76 | NEUTRAL | 50 | NEE | .RV | M..A | 31.7 | 0.71 | DEATH-CROSS | -4.9 | +13.1 |
| 77 | NEUTRAL-lean-L | 50 | NOC | .R.A | M.. | 46.2 | 0.89 | mixed | -0.5 | -6.4 |
| 78 | NEUTRAL-lean-L | 50 | NVDA | .R.A | M.. | 46.3 | 0.84 | ABOVE-BOTH | -2.2 | +20.3 |
| 79 | NEUTRAL-lean-S | 50 | OKLO | .R. | M..A | 42.5 | 1.15 | BELOW-BOTH | -38.6 | -39.8 |
| 80 | NEUTRAL-lean-L | 50 | ONTO | MR. | ...A | 45.0 | 1.14 | mixed | +6.4 | +164.7 |
| 81 | NEUTRAL-lean-S | 50 | ORCL | .R. | M..A | 50.4 | 0.85 | BELOW-BOTH | -24.8 | -37.6 |
| 82 | NEUTRAL-lean-L | 50 | PPA | MR. | ...A | 36.5 | 1.05 | mixed | +0.6 | +18.1 |
| 83 | NEUTRAL-lean-S | 50 | PPL | .R. | M..A | 42.3 | 0.89 | BELOW-BOTH | -3.5 | -2.3 |
| 84 | NEUTRAL | 50 | QCOM | .RV | M..A | 41.2 | 0.76 | BELOW-BOTH | -33.4 | +4.8 |
| 85 | NEUTRAL | 50 | QNT-USD | .R.A | M.V | 59.9 | 1.31 | mixed | -8.4 | -14.1 |
| 86 | NEUTRAL-lean-S | 50 | QQQ | .R. | M..A | 47.3 | 0.86 | mixed | -1.2 | +26.3 |
| 87 | NEUTRAL-lean-S | 50 | RKLB | .R. | M..A | 39.5 | 0.83 | BELOW-BOTH | -48.9 | +67.0 |
| 88 | NEUTRAL-lean-L | 50 | SMCI | .R.A | M.. | 55.9 | 0.80 | ABOVE-BOTH | -0.4 | -16.2 |
| 89 | NEUTRAL-lean-S | 50 | SMH | .R. | M..A | 41.7 | 0.83 | mixed | -5.1 | +90.8 |
| 90 | NEUTRAL-lean-L | 50 | SMR | .R.A | M.. | 50.8 | 0.96 | mixed | -18.5 | -72.2 |
| 91 | NEUTRAL-lean-L | 50 | SNDK | MR. | ...A | 49.3 | 1.03 | mixed | +0.4 | +3162.4 |
| 92 | NEUTRAL-lean-S | 50 | SNPS | .R. | M..A | 39.6 | 0.82 | BELOW-BOTH | -25.6 | -34.8 |
| 93 | NEUTRAL | 50 | SO | .RV | M..A | 36.5 | 0.79 | BELOW-BOTH | -4.3 | -2.0 |
| 94 | NEUTRAL-lean-L | 50 | SOL-USD | M..A | ... | 85.3 | 1.10 | ABOVE-BOTH | +34.8 | -24.1 |
| 95 | NEUTRAL-lean-S | 50 | TLN | .R. | M..A | 35.2 | 1.05 | BELOW-BOTH | -17.6 | -14.3 |
| 96 | NEUTRAL | 50 | TSLA | .RV | M..A | 54.6 | 0.64 | BELOW-BOTH | -16.4 | +11.3 |
| 97 | NEUTRAL-lean-S | 50 | USAR | .R. | M..A | 51.2 | 1.04 | BELOW-BOTH | -27.7 | +19.8 |
| 98 | NEUTRAL-lean-L | 50 | VGT | MR. | ...A | 46.5 | 0.93 | mixed | +1.1 | +37.7 |
| 99 | NEUTRAL-lean-S | 50 | VOLT | .R. | M..A | 37.3 | 1.06 | mixed | -9.6 | +32.6 |
| 100 | NEUTRAL-lean-S | 50 | VRT | .R. | M..A | 39.5 | 1.19 | mixed | -22.3 | +101.2 |
| 101 | NEUTRAL-lean-S | 50 | VST | .R. | M..A | 37.4 | 1.12 | BELOW-BOTH | -12.6 | -28.0 |
| 102 | NEUTRAL-lean-L | 50 | WBD | M..A | ... | 70.8 | 0.85 | ABOVE-BOTH | +6.3 | +147.9 |
| 103 | NEUTRAL-lean-S | 50 | WDC | .R. | M..A | 40.5 | 0.97 | mixed | -10.6 | +481.4 |
| 104 | NEUTRAL-lean-S | 50 | XAR | .R. | M..A | 39.1 | 1.09 | mixed | -1.4 | +25.7 |
| 105 | NEUTRAL | 50 | XLM-USD | .R.A | M.V | 66.7 | 1.24 | ABOVE-BOTH | -3.0 | -10.9 |
| 106 | NEUTRAL-lean-L | 50 | XRP-USD | M..A | ..V | 84.3 | 1.50 | ABOVE-BOTH | +33.5 | -20.7 |
| 107 | NEUTRAL-no-data | 0 | SPCX | .R. | ...A | 51.3 | - | - | - | - |

### 4a. Top LONG signals

| rk | ticker | conf% | RSI14 | volRatio | MAstate | 3m% | 6m% | 12m% | RS3m |
|---:|--------|------:|------:|---------:|---------|----:|----:|-----:|-----:|
| 1 | HPE | 100 | 50.7 | 0.76 | ABOVE-BOTH | +39.7 | +164.1 | +144.8 | +36.8 |
| 2 | NOW | 100 | 63.0 | 0.74 | ABOVE-BOTH | +26.5 | +28.1 | -26.4 | +23.6 |
| 3 | RTX | 100 | 44.8 | 0.71 | ABOVE-BOTH | +18.7 | +4.5 | +35.9 | +15.8 |
| 4 | GD | 100 | 49.4 | 0.75 | ABOVE-BOTH | +12.4 | +10.9 | +23.3 | +9.5 |
| 5 | LMT | 100 | 46.9 | 0.79 | ABOVE-BOTH | +6.8 | -13.3 | +29.9 | +3.9 |

### 4b. Top SHORT signals

No instrument satisfies all four SHORT gates as of 2026-08-24. Closest
candidates (3 of 4 short gates met), by gates then RSI ascending:

| rk | ticker | short-gates | RSI14 | volRatio | MAstate | 3m% |
|---:|--------|-------------|------:|---------:|---------|----:|
| 1 | AMKR | M.VA | 37.1 | 1.28 | BELOW-BOTH | -26.8 |
| 2 | NRG | M.VA | 37.4 | 1.40 | BELOW-BOTH | -18.8 |
| 3 | FN | M.VA | 37.5 | 1.26 | BELOW-BOTH | -39.9 |
| 4 | HII | M.VA | 40.3 | 1.41 | BELOW-BOTH | -7.7 |
| 5 | COHR | M.VA | 42.3 | 1.22 | mixed | -27.3 |
| 6 | CRWV | M.VA | 46.3 | 1.28 | BELOW-BOTH | -18.8 |
| 7 | NBIS | M.VA | 47.0 | 1.26 | mixed | -3.0 |

### 4c. Interpretation cautions

- The composite is a mechanical screen, not a trade recommendation; the vault
  invest doctrine (ref-portfolio-doctrine) gates any real order on sizing,
  thesis and risk layers far beyond this table.
- SHORT gates require simultaneous oversold RSI and expanding vol inside a
  downtrend; that full stack is rare on one as-of date (0 hits here). Use the
  3-of-4 candidate list and section 2/3 tables for staged entries.
- Crypto pairs (-USD) trade 7d weeks; their 21-bar 'month' spans fewer
  calendar days than equity months. Beta/corr vs SPY still computed on
  commonly dated bars only.
- SPCX has 50 bars: treat every `-` cell as unknown, never as neutral.

---

Snapshot provenance: factors.db bars 130,494 rows x 107 tickers, as-of 2026-08-24;
computed offline, zero network. Downstream consumers: weekly calibration
digest, /invest Phase R screening.
