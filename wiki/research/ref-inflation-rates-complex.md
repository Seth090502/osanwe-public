---
aliases: []
categories: [wiki]
type: reference
status: active
created: 2026-08-24
updated: 2026-08-24
confidence: high
tags:
  - topic/macro
  - topic/rates
  - topic/inflation
related: ["[[ref-fed-policy-complete]]", "ref-yen-carry-global-liquidity"]
---

# Inflation & Rates Complex Reference

GENERATED: 2026-08-24 from Efforts/osanwe-v2-overhaul/_work/factors.db
(sqlite; table `factors`, ticker='MACRO'). Regenerate by re-running the
aggregation queries at the bottom after the weekly calibration chain
(`osanwe-weekly-calibration`, SUN 07:30) refreshes the FRED pulls. Do not
hand-edit numbers.

Store coverage of the series used here:

| Series       | What it is                             | Obs  | Window             | Last obs   |
|--------------|----------------------------------------|------|--------------------|------------|
| DGS10        | 10y Treasury constant maturity, %      | 2910 | 2015-01-02 ->      | 2026-08-20 |
| DGS30        | 30y Treasury constant maturity, %      | 2910 | 2015-01-02 ->      | 2026-08-20 |
| T5YIE        | 5y breakeven inflation rate, pp        | 2911 | 2015-01-02 ->      | 2026-08-21 |
| T10Y3M       | 10y minus 3m term spread, pp           | 2911 | 2015-01-02 ->      | 2026-08-21 |
| T10Y2Y       | 10y minus 2y term spread, pp           | 2911 | 2015-01-02 ->      | 2026-08-21 |
| DFII10       | 10y TIPS real yield, %                 | 2910 | 2015-01-02 ->      | 2026-08-20 |
| CPIAUCSL     | CPI-U index, monthly, NSA (1982-84=100)| 138  | 2015-01 ->         | 2026-07-01 |
| BAMLH0A0HYM2 | ICE BofA US High Yield OAS, pp         | 787  | 2023-08-22 ->      | 2026-08-20 |
| BAMLH0A0HYM2EY | same index effective yield, %        | 787  | 2023-08-22 ->      | 2026-08-20 |

Percentile method: share of in-store observations <= current value over that
series' own full store window, times 100. Comparable within a series only;
the HY window starts 2023-08 so its percentiles are cycle-relative.

## 1. Full term structure -- current + trends

Panel: level, percentile over full store history ("pct-all") and trailing
365d ("pct-1y"), change over 7/30/91 calendar days (pp), 1-year high/low.
Sources: factors:DGS10/DGS30/T5YIE/T10Y3M/T10Y2Y/DFII10.

| Series  | Level | pct-all | pct-1y | d7    | d30   | d90   | 1y lo | 1y hi |
|---------|-------|---------|--------|-------|-------|-------|-------|-------|
| DGS10   | 4.69  | 99.0    | 97.2   | +0.06 | +0.06 | +0.12 | 3.97  | 4.75  |
| DGS30   | 5.23  | 99.8    | 97.2   | +0.02 | +0.10 | +0.13 | 4.54  | 5.31  |
| T5YIE   | 2.34  | 70.7    | 34.7   | +0.10 | +0.04 | -0.20 | 2.16  | 2.72  |
| T10Y3M  | +0.86 | 55.0    | 97.2   | +0.04 | +0.08 | -0.02 | -0.07 | 1.00  |
| T10Y2Y  | +0.50 | 50.1    | 34.3   | -0.01 | +0.14 | +0.07 | 0.27  | 0.74  |
| DFII10  | 2.35  | 98.7    | 91.2   | -0.04 | -0.02 | +0.17 | 1.67  | 2.47  |

Derived spreads (latest stamps): 10y breakeven = DGS10 - DFII10 = 2.34;
5y breakeven (T5YIE direct) = 2.34; 30s10s = +0.54.

Trend narrative (all computed from the store):

- Long end leads everything: DGS10 +0.12pp over 90 days to the 99.0th
  percentile of eleven years; DGS30 +0.13pp over the same span and printing
  within 8bp of its store-era high (5.31 set 2026-08-17 -- the 30y has made
  NEW store highs in 2026 while the 10y remains 29bp under its 2023-10-19
  max of 4.98). Curve shape: 30s10s +0.54 and widening = supply/term-premium
  bear-steepening, not a growth scare.
- Breakevens anchored and cooling: T5YIE 2.34 with 90-day change -0.20pp and
  only the 34.7th percentile of the past year. The 2026 high (2.72,
  2026-05-04) coincided exactly with the CPI spring acceleration (section 2)
  and has since fully round-tripped. Inflation COMPENSATION is near target-
  perimeter; the long-end move is a REAL-yield phenomenon.
- Real yields are the story: DFII10 2.35, 98.7th pct all-store, +0.17pp over
  90 days, 91st pct of the past year even while the Fed sat on hold/cut
  (see [[ref-fed-policy-complete]] sections 1, 7).
- Spread curve position: T10Y3M +0.86 at the 97th percentile of the year --
  uninverted with force after re-inverting on 2025-10-16 (last negative
  print -0.03). T10Y2Y +0.50, 30d change +0.14. Store extremes worth
  remembering: T10Y3M min -1.89 (2023-05-04), max +2.48 (2015-06-10);
  T10Y2Y min -1.08 (2023-07-03), max +1.77 (2015-06-26).

## 2. Inflation state -- CPIAUCSL YoY from index levels

Computation (this vault derives YoY itself; no precomputed CPI series is in
the store):

```
YoY(m)   = 100 * (idx[m] / idx[m-12] - 1)
MoM(m)   = 100 * (idx[m] / idx[m-1] - 1)
3m ann.  = 100 * ((idx[m] / idx[m-3]) ** 4 - 1)
6m ann.  = 100 * ((idx[m] / idx[m-6]) ** 2 - 1)
```

Last 18 months (factors:CPIAUCSL, NSA index):

| Month    | Index   | YoY    | MoM    |
|----------|---------|--------|--------|
| 2025-01  | 318.961 | +2.99% | +0.43% |
| 2025-02  | 319.679 | +2.80% | +0.23% |
| 2025-03  | 319.785 | +2.38% | +0.03% |
| 2025-04  | 320.302 | +2.33% | +0.16% |
| 2025-05  | 320.620 | +2.38% | +0.10% |
| 2025-06  | 321.435 | +2.68% | +0.25% |
| 2025-07  | 322.169 | +2.74% | +0.23% |
| 2025-08  | 323.291 | +2.94% | +0.35% |
| 2025-09  | 324.245 | +3.02% | +0.30% |
| 2025-10  | MISSING | n/a    | n/a    |
| 2025-11  | 325.063 | +2.70% | +0.25% |
| 2025-12  | 326.031 | +2.65% | +0.30% |
| 2026-01  | 326.588 | +2.39% | +0.17% |
| 2026-02  | 327.460 | +2.43% | +0.27% |
| 2026-03  | 330.293 | +3.29% | +0.87% |
| 2026-04  | 332.407 | +3.78% | +0.64% |
| 2026-05  | 333.979 | +4.17% | +0.47% |
| 2026-06  | 332.568 | +3.46% | -0.42% |
| 2026-07  | 332.813 | +3.30% | +0.07% |

Data-quality flags (visible in the raw store rows):

- 2025-10 is absent from the store (138 obs across a 139-month span). The
  2025-11 YoY above is computed against 2024-11 normally (that month exists),
  but any rolling-window stat spanning Oct-2025 inherits the hole. The
  3m/6m annualizations below use the LAST THREE/LAST SEVEN available rows,
  which straddle the gap.
- Latest readings: YoY +3.30%; 6m ann +3.85%; 3m ann +0.49% -- the 3m figure
  is mechanically crushed by June's -0.42% NSA drop and should not be read
  as disinflation on its own.

Inflation narrative from the index path:

- 2025 was a quiet glide around 2.3-3.0% YoY.
- A sharp spring-2026 acceleration took YoY from +2.43% (Feb) to a local
  peak +4.17% (May) -- index up 6.5 points in three months, the fastest
  climb since the 2022 episode in this store window.
- June-July gave the first genuine cooling: index -0.35% below the May peak,
  YoY off the top by -87bp. One to two prints is a pause, not a trend --
  but it lines up with the breakeven round-trip in section 1 (T5YIE 2.72 ->
  2.34).
- Historical context (calendar-year average YoY, computed from the store):
  2016 +1.27, 2017 +2.13, 2018 +2.44, 2019 +1.81, 2020 +1.25, 2021 +4.68,
  2022 +8.00, 2023 +4.15, 2024 +2.95, 2025 +2.69, 2026 (through Jul) +3.26.
  Current inflation is mid-band between the 2024-25 plateau and the 2022-23
  excess -- NOT consistent with near-term Fed easing below the current
  3.63% funds rate (factors:FEDFUNDS), which matches the market's own
  pricing via the steep positive T10Y3M spread.
- Companion series in the store: UNRATE 4.1 (2026-07), easing steadily off
  its 4.5 (2025-11) local peak; calendar-year means 2024 4.03, 2025 4.26,
  2026 4.27. A labor market this flat keeps wage-push pressure secondary to
  the goods/shock component that drove the spring spike.

## 3. Credit complex -- BAMLH0A0HYM2 (OAS) + effective yield

Source: factors:BAMLH0A0HYM2 (option-adjusted spread, pp) and
factors:BAMLH0A0HYM2EY (effective yield, %), both daily from 2023-08-22.

Current state:

- OAS 2.75pp (2026-08-20) = 16.8th percentile of the store window,
  27.5th percentile of the past year. Trend: +0.04pp over 7d, +0.06pp over
  30d, -0.03pp over 90d -- flat-to-marginally-wider inside a tight regime.
- Effective yield 7.09% = 51.6th percentile all-store BUT 90.6th percentile
  of the past year (EY 1y range 6.39-7.48). The decomposition matters:
  credit RISK premium is near cycle lows while the ALL-IN yield is elevated
  purely because Treasuries under it are (DGS10 4.69). Spread investors are
  paid by the rates complex, not by risk compensation.
- Extremes: stress max 4.61pp (2025-04-07, tariff shock); tights min 2.59pp
  (2025-01-22). Current level sits 14bp above the all-time tights.
- Trailing 90 days: mean 2.73, min 2.63, max 2.87 -- a 24bp trading band.
  Compare the April-2025 event: 2.59 -> 4.61 in under six weeks (+202bp).
  Credit vol is dormant; the tail is fat.

Last 14 daily prints:

| Date       | OAS  | Eff yield | Pct-all |
|------------|------|-----------|---------|
| 2026-08-03 | 2.78 | 7.18      | 19.8    |
| 2026-08-04 | 2.73 | 7.07      | 13.7    |
| 2026-08-05 | 2.75 | 7.08      | 16.8    |
| 2026-08-06 | 2.71 | 7.10      | 11.1    |
| 2026-08-07 | 2.70 | 7.05      | 9.1     |
| 2026-08-10 | 2.70 | 7.10      | 9.1     |
| 2026-08-11 | 2.72 | 7.11      | 12.7    |
| 2026-08-12 | 2.71 | 7.08      | 11.1    |
| 2026-08-13 | 2.71 | 7.02      | 11.1    |
| 2026-08-14 | 2.67 | 7.00      | 5.8     |
| 2026-08-17 | 2.70 | 7.05      | 9.1     |
| 2026-08-18 | 2.75 | 7.09      | 16.8    |
| 2026-08-19 | 2.73 | 7.04      | 13.7    |
| 2026-08-20 | 2.75 | 7.09      | 16.8    |

Time-in-band over the store window (787 daily obs, 2023-08-22 -> 2026-08-20):
OAS <= 2.50: 0.0% | 2.50-3.00: 45.7% | 3.00-3.50: 37.1% | 3.50-4.00: 11.1%
| > 4.00: 6.1%.

Calendar-year means: 2023 (partial) 3.95, 2024 3.15, 2025 3.05, 2026 2.85 --
a three-year grind tighter, currently probing the floor of that grind.

Cross-market confirmation (trailing 365d, daily diffs): SPY return vs
delta-OAS r = -0.628; delta-VIX vs delta-OAS r = +0.528. Equity drawdowns
and credit widening remain one trade. An OAS break above ~3.50 (the
store's 83rd-percentile-plus zone) would be an early systemic tell long
before VIX confirms; see ref-yen-carry-global-liquidity sections 4-5
for the stress-index side.

## 4. Historical context tables

Calendar-year means computed from the store (partial years marked *):

| Year | DGS10 | DGS30 | T5YIE | DFII10 | FEDFUNDS | HY OAS* | VIX  | CPI YoY | UNRATE |
|------|-------|-------|-------|--------|----------|---------|------|---------|--------|
| 2015 | 2.14  | 2.84  | 1.38  | 0.45   | 0.13     | n/a     | 16.67| n/a     | 5.28   |
| 2016 | 1.84  | 2.59  | 1.43  | 0.27   | 0.40     | n/a     | 15.83| 1.27    | 4.88   |
| 2017 | 2.33  | 2.89  | 1.74  | 0.46   | 1.00     | n/a     | 11.09| 2.13    | 4.36   |
| 2018 | 2.91  | 3.11  | 1.97  | 0.83   | 1.83     | n/a     | 16.64| 2.44    | 3.89   |
| 2019 | 2.14  | 2.58  | 1.60  | 0.40   | 2.16     | n/a     | 15.39| 1.81    | 3.68   |
| 2020 | 0.89  | 1.56  | 1.32  | -0.60  | 0.38     | n/a     | 29.25| 1.25    | 8.10   |
| 2021 | 1.45  | 2.06  | 2.55  | -0.91  | 0.08     | n/a     | 19.66| 4.68    | 5.35   |
| 2022 | 2.95  | 3.11  | 2.78  | 0.43   | 1.68     | n/a     | 25.64| 8.00    | 3.65   |
| 2023 | 3.96  | 4.09  | 2.25  | 1.68   | 5.02     | 3.95*   | 16.85| 4.15    | 3.62   |
| 2024 | 4.21  | 4.41  | 2.25  | 1.94   | 5.14     | 3.15    | 15.55| 2.95    | 4.03   |
| 2025 | 4.29  | 4.78  | 2.41  | 1.96   | 4.21     | 3.05    | 18.93| 2.69    | 4.26   |
| 2026*| 4.38  | 4.95  | 2.44  | 2.06   | 3.64     | 2.85    | 18.70| 3.26*   | 4.27   |

(* = partial-year through each series' last store observation; CPI YoY 2026
averages Jan-Jul; HY OAS begins 2023-08; CPI YoY 2015 not computable because
2014 index months are outside the store window.)

Derived from the yearly means (nominal minus real, same-year averages --
approximate breakeven proxy):

| Year | 10y nominal | 10y real | Implied BE proxy |
|------|-------------|----------|------------------|
| 2020 | 0.89        | -0.60    | 1.49             |
| 2021 | 1.45        | -0.91    | 2.36             |
| 2022 | 2.95        | 0.43     | 2.52             |
| 2023 | 3.96        | 1.68     | 2.28             |
| 2024 | 4.21        | 1.94     | 2.27             |
| 2025 | 4.29        | 1.96     | 2.33             |
| 2026 | 4.38        | 2.06     | 2.32             |

Read of the decade shape: nominal yields have ratcheted up every year since
2020 while implied breakevens have been STABLE at 2.3 +/- 0.1 since 2023 --
the entire bear market in bonds is a real-yield repricing, and 2026 is the
first year the real component pushed decisively above 2%.

## 5. Synthesis -- what the complex says right now

1. Inflation re-accelerated to +4.17% YoY in May 2026, cooled two prints,
   and breakevens believe the cooling (T5YIE back to 2.34, 35th pct of the
   year). Market-implied path: no re-acceleration priced, no collapse either.
2. The long end refuses to rally anyway. With breakevens flat, the DGS10/
   DGS30 grind higher is term premium + real yield -- the least Fed-friendly
   configuration for equity duration, and the direct driver of the vault's
   0.0x deployment band at that threshold
   ([[ref-fed-policy-complete]] section 8).
3. Credit is the calmest major complex in the store (OAS 16.8th pct, 24bp
   90-day range) -- historically a late-cycle signature: tight spreads fund
   the risk appetite that high real yields are trying to cool. Watch order:
   OAS > 3.50 first, STLFSI4 crossing 0 second, VIX > 22 third.
4. The single most useful internal consistency check: 10y breakeven (2.34)
   == T5YIE (2.34) == CPI-market gap. If CPI prints re-accelerate toward the
   spring path while these stay pinned, the move belongs to term premium --
   historically the stickiest and most equity-hostile kind.

## 6. Regeneration

Queries behind every number (sqlite3
Efforts/osanwe-v2-overhaul/_work/factors.db):

```
-- yield panel
SELECT date, value FROM factors
 WHERE factor IN ('DGS10','DGS30','T5YIE','T10Y3M','T10Y2Y','DFII10')
 ORDER BY factor, date;
-- CPI levels (YoY/MoM derived per formulas in section 2)
SELECT date, value FROM factors WHERE factor='CPIAUCSL' ORDER BY date;
-- credit complex
SELECT date, value FROM factors
 WHERE factor IN ('BAMLH0A0HYM2','BAMLH0A0HYM2EY') ORDER BY date;
-- percentile rank of latest value in a series' own window
SELECT 100.0 * SUM(CASE WHEN value <= :cur THEN 1 ELSE 0 END) / COUNT(*)
  FROM factors WHERE factor = :f AND value IS NOT NULL;
```

Refresh cadence: rerun after each weekly `osanwe-weekly-calibration` ingest
(SUN 07:30). Yields/OAS daily; CPIAUCSL monthly (watch for the occasional
missing month -- verify the prior-year month exists before trusting a YoY);
yearly tables roll forward each January.

Caveats: CPIAUCSL is NSA (headline MoM swings like 2026-06's -0.42% include
seasonal effects; do not annualize one NSA month into a trend); HY OAS
percentiles cover only the 2023-08+ cycle; T10Y3M/T10Y2Y are FRED-computed
spreads, not locally derived; DFII10 suspends on some TIPS auction days
(gaps bridged in correlations only, never interpolated into level tables).
