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
  - topic/fed
related: ["ref-yen-carry-global-liquidity", "[[ref-inflation-rates-complex]]"]
---

# Fed Policy Reference (Complete)

GENERATED: 2026-08-24 from Efforts/osanwe-v2-overhaul/_work/factors.db
(sqlite; table `factors`, ticker='MACRO', one row per FRED series observation,
plus table `bars` for equity context). Regenerate by re-running the aggregation
queries listed at the bottom of this file against the store AFTER the weekly
calibration chain (cron `osanwe-weekly-calibration`, SUN 07:30, step
`ingest-bars`) refreshes the FRED pulls. Do not hand-edit numbers.

Store coverage of the series used here (obs counts are in-store rows):

| Series    | What it is                          | Obs   | Window              | Last obs   |
|-----------|-------------------------------------|-------|---------------------|------------|
| FEDFUNDS  | Effective fed funds rate, monthly % | 139   | 2015-01 -> 2026-07  | 2026-07-01 |
| WALCL     | Fed total assets, weekly, $M        | 607   | 2015-01-07 ->       | 2026-08-19 |
| WRESBAL   | Bank reserves at the Fed, wk, $M    | 607   | 2015-01-07 ->       | 2026-08-19 |
| RRPONTSYD | Overnight reverse repo volume, $B   | 2901  | 2015-01-02 ->       | 2026-08-21 |
| SOFR      | Secured overnight financing rate, % | 2094  | 2018-04-03 ->       | 2026-08-20 |
| DGS10     | 10y nominal Treasury yield, %       | 2910  | 2015-01-02 ->       | 2026-08-20 |
| T10Y3M    | 10y minus 3m term spread, pp        | 2911  | 2015-01-02 ->       | 2026-08-21 |
| T10Y2Y    | 10y minus 2y term spread, pp        | 2911  | 2015-01-02 ->       | 2026-08-21 |
| DFII10    | 10y TIPS real yield, %              | 2910  | 2015-01-02 ->       | 2026-08-20 |

Percentile rank method (used everywhere below): share of in-store observations
strictly less than or equal to the current value, times 100, over that series'
own full store window. Windows differ per series, so percentiles are comparable
only within a series, never across series.

## 1. Fed funds rate -- last 24 months

Source: factors:FEDFUNDS (monthly average of daily effective rate). A month-row
is the calendar-month average, so it lags intra-month FOMC moves by design.

| Month    | Rate (%) | Chg vs prior mo (pp) |
|----------|----------|----------------------|
| 2024-07  | 5.33     | --                   |
| 2024-08  | 5.33     | 0.00                 |
| 2024-09  | 5.13     | -0.20                |
| 2024-10  | 4.83     | -0.30                |
| 2024-11  | 4.64     | -0.19                |
| 2024-12  | 4.48     | -0.16                |
| 2025-01  | 4.33     | -0.15                |
| 2025-02  | 4.33     | 0.00                 |
| 2025-03  | 4.33     | 0.00                 |
| 2025-04  | 4.33     | 0.00                 |
| 2025-05  | 4.33     | 0.00                 |
| 2025-06  | 4.33     | 0.00                 |
| 2025-07  | 4.33     | 0.00                 |
| 2025-08  | 4.33     | 0.00                 |
| 2025-09  | 4.22     | -0.11                |
| 2025-10  | 4.09     | -0.13                |
| 2025-11  | 3.88     | -0.21                |
| 2025-12  | 3.72     | -0.16                |
| 2026-01  | 3.64     | -0.08                |
| 2026-02  | 3.64     | 0.00                 |
| 2026-03  | 3.64     | 0.00                 |
| 2026-04  | 3.64     | 0.00                 |
| 2026-05  | 3.63     | -0.01                |
| 2026-06  | 3.63     | 0.00                 |
| 2026-07  | 3.63     | 0.00                 |

Cycle structure visible in the store (factors:FEDFUNDS):

- Peak plateau 5.33 held 2023-08 through 2024-08 (store max 5.33).
- Easing leg 1: five consecutive cuts 2024-09..2025-01, -1.00pp total
  (5.33 -> 4.33).
- Hold at 4.33 for eight months (2025-02..2025-09 print).
- Easing leg 2: five more steps 2025-09..2026-01, -0.69pp (4.33 -> 3.64),
  then a drift to 3.63 by 2026-05 and flat through 2026-07.
- Cumulative easing from peak: -1.70pp (5.33 -> 3.63). Current 3.63 sits at
  the 69.8th percentile of the store's 139 monthly prints (2015-01 base).
- Store extremes: min 0.05 (2020-04), max 5.33 (2023-08).

Read: two easing campaigns with a long pause between; policy is now in a
second pause at 3.63, i.e. moderately restrictive-neutral, roughly 170bp off
the cycle top but still well above the 2015-2019 average (yearly means:
2015 0.13 ... 2019 2.16).

## 2. Balance sheet QT trajectory -- WALCL

Source: factors:WALCL, weekly (Wednesday stamp), stored $M, shown $B.
Delta column is week-over-week.

| Week      | Total assets ($B) | WoW ($B) |
|-----------|-------------------|----------|
| 2026-02-18| 6613              | --       |
| 2026-02-25| 6614              | +0       |
| 2026-03-04| 6629              | +15      |
| 2026-03-11| 6646              | +17      |
| 2026-03-18| 6656              | +10      |
| 2026-03-25| 6657              | +1       |
| 2026-04-01| 6675              | +18      |
| 2026-04-08| 6694              | +19      |
| 2026-04-15| 6706              | +12      |
| 2026-04-22| 6707              | +2       |
| 2026-04-29| 6700              | -7       |
| 2026-05-06| 6710              | +10      |
| 2026-05-13| 6729              | +19      |
| 2026-05-20| 6714              | -15      |
| 2026-05-27| 6704              | -9       |
| 2026-06-03| 6711              | +7       |
| 2026-06-10| 6725              | +14      |
| 2026-06-17| 6736              | +11      |
| 2026-06-24| 6736              | -1       |
| 2026-07-01| 6725              | -11      |
| 2026-07-08| 6736              | +11      |
| 2026-07-15| 6743              | +7       |
| 2026-07-22| 6747              | +4       |
| 2026-07-29| 6738              | -9       |
| 2026-08-05| 6749              | +10      |
| 2026-08-12| 6760              | +11      |
| 2026-08-19| 6746              | -14      |

QT scorecard from the store (factors:WALCL):

- All-store peak: 8,965B on 2022-04-13.
- Latest: 6,746B on 2026-08-19.
- Total reduction since peak: -2,220B (-24.76%).
- Last 24 months: 7,178B (wk of 2024-08-19 sample) -> 6,746B = -432B.
- Post-trough behavior: the store's minimum since 2025-01-01 was 6,536B on
  2025-12-03; the balance sheet has since RE-EXPANDED +210B off that trough
  (bill-driven rebuild around year-end plumbing), with the last four months
  netting roughly +90B. Strict roll-off has ended; the recent pattern is
  oscillation with an upward bias, not QT.
- Context: TREAST (Fed securities holdings outright) peaked 5,771B
  (2022-06-08), now 4,542B (2026-08-19), -1,229B (factors:TREAST).

## 3. Bank reserves drain -- WRESBAL

Source: factors:WRESBAL, weekly, stored $M, shown $B. Delta is week-over-week.

| Week      | Reserves ($B) | WoW ($B) |
|-----------|---------------|----------|
| 2026-05-20| 3130          | --       |
| 2026-05-27| 3067          | -63      |
| 2026-06-03| 3014          | -53      |
| 2026-06-10| 3081          | +67      |
| 2026-06-17| 3033          | -47      |
| 2026-06-24| 2951          | -82      |
| 2026-07-01| 2967          | +15      |
| 2026-07-08| 3099          | +132     |
| 2026-07-15| 3143          | +44      |
| 2026-07-22| 3062          | -81      |
| 2026-07-29| 2985          | -78      |
| 2026-08-05| 2993          | +9       |
| 2026-08-12| 2944          | -49      |
| 2026-08-19| 2935          | -9       |

Liquidity implications (all from factors:WRESBAL):

- Peak 4,276B (2021-12-08) -> 2,935B now: a 1,341B drain, -31.35%.
- 2025 range: low 2,848B (2025-10-29), high 3,475B (2025-04-09). Current
  2,935B sits in the bottom quartile of that range and falling again after
  the July tax/refunding rebuild.
- Weekly swings of +/-50-130B are now routine; that amplitude itself signals
  reserves are closer to scarce than ample (banks are actively managing
  intraweek liquidity rather than sitting on buffers).
- The drain is no longer offset by RRP (section 5): through 2022-2024, RRP
  absorbed QT; since 2025 the marginal buyer of Fed liabilities shrinkage is
  bank reserves directly. This is the channel that historically precedes
  repo-market stress events if pushed much further.
- Watch line: sustained breaks below ~2.8T (the 2025-10-29 low) with rising
  SOFR dispersion would be the classic late-QT tell.

## 4. SOFR corridor position vs IORB

Source: factors:SOFR (daily). Note: IORB itself is NOT in the store; the
closest anchors available are FEDFUNDS (effective fed funds, monthly) and
SOFR's own distribution. Treat this section as a corridor-position read via
those proxies only.

Last 20 daily SOFR prints (factors:SOFR):

| Date       | SOFR (%) |
|------------|----------|
| 2026-07-24 | 3.64     |
| 2026-07-27 | 3.64     |
| 2026-07-28 | 3.65     |
| 2026-07-29 | 3.65     |
| 2026-07-30 | 3.65     |
| 2026-07-31 | 3.66     |
| 2026-08-03 | 3.65     |
| 2026-08-04 | 3.66     |
| 2026-08-05 | 3.64     |
| 2026-08-06 | 3.65     |
| 2026-08-07 | 3.62     |
| 2026-08-10 | 3.63     |
| 2026-08-11 | 3.64     |
| 2026-08-12 | 3.62     |
| 2026-08-13 | 3.62     |
| 2026-08-14 | 3.62     |
| 2026-08-17 | 3.66     |
| 2026-08-18 | 3.65     |
| 2026-08-19 | 3.62     |
| 2026-08-20 | 3.63     |

Corridor diagnostics (computed from factors:SOFR and factors:FEDFUNDS):

- Last 90 days: SOFR mean 3.625, min 3.53, max 3.69.
- SOFR minus FEDFUNDS(3.63): mean -0.005pp over the last 90 days, worst day
  +0.06pp. SOFR is trading ON TOP of the effective funds rate, dead quiet.
- Yearly shape (mean/min/max): 2023 5.01/4.30/5.40; 2024 5.15/4.30/5.40;
  2025 4.24/3.66/4.51; 2026 3.64/3.50/3.75. The 2026 band is the tightest in
  the series' store history -- money markets are pinned to the administered
  rate with essentially no repo pressure.
- Interpretation: despite the reserve drain in section 3, funding markets
  show zero strain. The system is draining toward, not into, scarcity. The
  tripwire is a persistent SOFR pop ABOVE the administered complex (what the
  store can show as multi-day SOFR >= FEDFUNDS + 0.05), which has not
  printed in the current window beyond isolated +0.06 blips.

## 5. Reverse repo facility drawdown -- RRPONTSYD

Source: factors:RRPONTSYD, daily, $B. Sampled below on WALCL Wednesdays for
alignment; delta is vs prior sample.

| Week      | RRP ($B) | Chg ($B) |
|-----------|----------|----------|
| 2026-02-18| 0.9      | --       |
| 2026-02-25| 1.2      | +0.3     |
| 2026-03-04| 0.9      | -0.3     |
| 2026-03-11| 0.6      | -0.3     |
| 2026-03-18| 0.7      | +0.1     |
| 2026-03-25| 0.8      | +0.1     |
| 2026-04-01| 2.1      | +1.3     |
| 2026-04-08| 0.2      | -1.9     |
| 2026-04-15| 0.2      | +0.0     |
| 2026-04-22| 0.5      | +0.3     |
| 2026-04-29| 0.7      | +0.2     |
| 2026-05-06| 1.6      | +0.9     |
| 2026-05-13| 3.7      | +2.1     |
| 2026-05-20| 24.9     | +21.1    |
| 2026-05-27| 1.9      | -23.0    |
| 2026-06-03| 2.1      | +0.2     |
| 2026-06-10| 0.4      | -1.7     |
| 2026-06-17| 6.8      | +6.4     |
| 2026-06-24| 4.5      | -2.3     |
| 2026-07-01| 1.0      | -3.5     |
| 2026-07-08| 3.3      | +2.3     |
| 2026-07-15| 0.2      | -3.2     |
| 2026-07-22| 0.4      | +0.2     |
| 2026-07-29| 2.6      | +2.2     |
| 2026-08-05| 1.6      | -0.9     |
| 2026-08-12| 0.7      | -0.9     |
| 2026-08-19| 0.3      | -0.4     |

Drawdown math (factors:RRPONTSYD):

- Peak 2,553.7B (2022-12-30) -> 0.2B (2026-08-21): drawdown -2,553.5B,
  effectively -100%. The facility is functionally EMPTY.
- 2026 daily stats: 160 obs, max 26.9B (2026-06-30, a quarter-end window-
  dressing artifact), 141 of 160 days under 5B.
- Implication for the QT story: the liquidity buffer that cushioned 2023-2024
  QT is gone. From here, any further Fed liability reduction lands one-for-one
  on bank reserves (section 3). Combined WALCL+RRP drawdown from the joint
  peak: 8,967B (2022-04-13) -> 6,746B (2026-08-19) = -2,222B (-24.8%);
  -432B over the last 24 months (see also ref-yen-carry-global-liquidity
  section 5 for the global-liquidity framing).

## 6. Curve analysis -- DGS10, T10Y3M, T10Y2Y (plus DGS30, DFII10)

Panel: current value, percentile over own full store history ("pct-all") and
over trailing 365 days ("pct-1y"), change over 7/30/91 days (pp), and 1-year
high/low. Sources: factors:DGS10/DGS30/T10Y3M/T10Y2Y/DFII10.

| Series  | Level | pct-all | pct-1y | d7    | d30   | d90   | 1y lo | 1y hi |
|---------|-------|---------|--------|-------|-------|-------|-------|-------|
| DGS10   | 4.69  | 99.0    | 97.2   | +0.06 | +0.06 | +0.12 | 3.97  | 4.75  |
| DGS30   | 5.23  | 99.8    | 97.2   | +0.02 | +0.10 | +0.13 | 4.54  | 5.31  |
| T10Y3M  | +0.86 | 55.0    | 97.2   | +0.04 | +0.08 | -0.02 | -0.07 | 1.00  |
| T10Y2Y  | +0.50 | 50.1    | 34.3   | -0.01 | +0.14 | +0.07 | 0.27  | 0.74  |
| DFII10  | 2.35  | 98.7    | 91.2   | -0.04 | -0.02 | +0.17 | 1.67  | 2.47  |

Derived (levels on 2026-08-20/21 stamps): 10y breakeven = DGS10 - DFII10 =
2.34; 30s10s = +0.54; 10y real = 2.35.

Curve reads:

- Nominal long end: DGS10 at the 99.0th percentile of eleven years of store
  data and 30bp below its store max (4.98, 2023-10-19). DGS30 made a NEW
  store-era high as recently as 2026-08-17 (5.31) and now prints 99.8th
  percentile. This is a term-premium-heavy bear steepening: the long end is
  pricing supply/inflation-risk, not growth.
- Re-inversion watch: T10Y3M went positive again on 2025-10-16 (last negative
  print -0.03) and has climbed to +0.86 (97th pct of the past year) --
  the market has fully priced the easing cycle and then some; the 3m bill
  (implied ~3.8) vs 10y 4.69 says further cuts are NOT the base case.
- T10Y2Y +0.50 with 30-day change +0.14: steepening trend intact but less
  extreme than the 3m measure because 2y carries more cut-pricing.
- Real yields: DFII10 2.35 at the 98.7th percentile -- the highest sustained
  real-rate regime in the store besides late 2023. Ex-ante real financing
  costs are unambiguously tight for duration-sensitive equities.
- Cross-check: 10y breakeven 2.34 vs T5YIE 2.34 -- inflation compensation is
  anchored near target-perimeter, so the nominal move is REAL-yield driven
  (see [[ref-inflation-rates-complex]] sections 2-3).

## 7. Real yields -- DFII10 detail

Source: factors:DFII10 (10y TIPS, daily).

- Level 2.35 (2026-08-20); store min -1.19 (2021-08-03); store max 2.52
  (2023-10-25); current percentile 98.7 all-store, 91.2 trailing-year.
- 2026 path: year high 2.47 (2026-07-31); the 90-day change is +0.17pp, i.e.
  real yields have been climbing THROUGH the Fed's easing pauses -- a
  market-driven tightening impulse that offsets part of the -1.70pp policy
  easing since the 5.33 peak.
- Yearly means: 2020 -0.60, 2021 -0.91 (free-money era), 2022 +0.43,
  2023 +1.68, 2024 +1.94, 2025 +1.96, 2026 +2.06. The three-year plateau just
  under 2% has rolled over into a push above it.

## 8. What it all means for equity deployment bands

Vault deployment doctrine (as applied in wiki/investing snapshots and ticker
analyses and a net-worth session): the DGS10 level
gates the deployment multiplier -- DGS10 above 4.40 puts a book in the 0.0x
hold-cash band; DGS10 at or below 4.40 reopens the band. A separate
regime-halt trips when DGS10 > 4.50 AND VIXCLS > 22 simultaneously.

Current gate state (all from factors, stamps as noted):

| Gate                       | Threshold        | Current                    | State            |
|----------------------------|------------------|----------------------------|------------------|
| DGS10 hold-cash line       | > 4.40 = 0.0x    | 4.69 (2026-08-20)          | BINDING (band per doctrine)   |
| Days above 4.40            | --               | 40 of last 43 obs          | persistent       |
| Current streak > 4.40      | --               | 37 consecutive obs         | since 2026-06-30 |
| Last DGS10 <= 4.40         | --               | 4.38 on 2026-06-29         | --               |
| Regime-halt (DGS10>4.50)   | AND VIXCLS > 22  | 4.69 yes, VIX 16.01 no     | NOT tripped      |
| SPY distance from 52w hi   | context          | -1.6% (765.72, 2026-08-21) | tape strong      |

Translation for deployment:

1. The binding constraint is the LONG END, not the policy rate. Funds rate
   3.63 and falling-flat is compatible with risk appetite; DGS10 at 4.69
   (99th pct) with DFII10 2.35 (98.7th pct) is what keeps the multiplier at
   0.0x. Watch DGS10 <= 4.40 as the band-reopen trigger, not FOMC dates.
2. The halt is inactive (VIX 16.01, 44th pct) but only needs VIX +6pts to
   arm while DGS10 stays over 4.50 -- a single risk-off shock would flip the
   book from "hold-cash by band" to "halted". Size accordingly.
3. QT is no longer the marginal story (RRP empty, WALCL re-expanding since
   2025-12-03), but reserves at 2,935B and falling are the fragility: a
   funding wobble (SOFR popping over administered rates for multiple days)
   is the scenario that converts this from a valuation gate into a
   liquidity event. Monitor WRESBAL < 2.85T as the early-warning line.
4. Upside scenario for reopening the band: breakevens are anchored (2.34), so
   DGS10 falling to 4.40 requires real yields down ~30bp -- i.e. growth
   disappointment or supply relief -- not an inflation event.
5. Historical anchor: DGS10 yearly means 2023 3.96, 2024 4.21, 2025 4.29,
   2026 4.38 -- the entire post-2023 era has averaged inside/near the band's
   danger zone; sub-4.40 windows have been rare and short since mid-2026
   (last one closed 2026-06-29).

## 9. Regeneration

Queries behind every table (sqlite3
Efforts/osanwe-v2-overhaul/_work/factors.db):

```
-- any series panel
SELECT date, value FROM factors
 WHERE factor IN ('FEDFUNDS','WALCL','WRESBAL','RRPONTSYD','SOFR',
                  'DGS10','DGS30','T10Y3M','T10Y2Y','DFII10')
 ORDER BY factor, date;
-- percentile rank of current value within a series' own history
SELECT 100.0 * SUM(CASE WHEN value <= (SELECT value FROM factors
                        WHERE factor=:f ORDER BY date DESC LIMIT 1)
                       THEN 1 ELSE 0 END) / COUNT(*)
  FROM factors WHERE factor = :f AND value IS NOT NULL;
-- equity context
SELECT date, close FROM bars WHERE ticker = 'SPY' ORDER BY date;
```

Refresh cadence: rerun after each weekly `osanwe-weekly-calibration` ingest
(SUN 07:30). Monthly series (FEDFUNDS) update monthly; WALCL/WRESBAL weekly;
RRPONTSYD/SOFR/yields daily. If a series' last obs stalls more than two
cycles past its cadence, suspect the ingest step, not this document.

Caveats: FEDFUNDS here is the MONTHLY AVERAGE series (not the daily EFFR);
WALCL/WRESBAL are Wednesday-stamped weeks; RRPONTSYD quarter-end spikes are
genuine but transient; percentiles are store-window-relative (2015-01 base
for yields) and will drift as history accumulates. IORB is not in the store;
corridor reads use FEDFUNDS/SOFR as proxies.

---

# PART 2 APPENDIX -- DEEP HISTORY (appended 2026-08-24)

Sections 10-12 extend the snapshot above with full-cycle history drawn from
the same factor store (Efforts/osanwe-v2-overhaul/_work/factors.db,
ticker=MACRO, src=fred-csv). Nothing in Sections 1-9 is superseded. The
SOFR-FEDFUNDS spread is computed as daily SOFR minus the same-month FEDFUNDS
monthly average, expressed in basis points (2080 matched observations,
2015-01 through 2026-08). All figures were recomputed from the store on the
append date; refresh them alongside the Section 9 cadence.

## 10. Historical rate cycles -- FEDFUNDS inflections 2015-2026

The full monthly path (139 obs, 2015-01 .. 2026-07) spans 0.11 -> 0.05 ->
5.33 -> 3.63: one mid-cycle normalization, one emergency collapse, the
fastest hiking campaign in four decades, and two easing legs.

### 10a. Regime summary

| Regime            | Window           | Funds-rate path        | Cum. move | Shape                                    |
|-------------------|------------------|------------------------|-----------|------------------------------------------|
| Normalization III | 2015-12..2019-01 | 0.12 -> 2.40 (peak mo) | +228bp    | 9 hikes over 37 months, twice paused     |
| Mid-cycle pivot   | 2019-07..2019-10 | 2.40 -> 1.55           | -85bp     | 3 insurance cuts                          |
| COVID emergency   | 2020-03..2020-04 | 1.58 -> 0.05           | -153bp    | 150bp in ~2 weeks, back to ZIRP           |
| ZIRP-2 floor      | 2020-04..2022-02 | <= 0.10 for 23 months  | 0         | Longest floor sit of the sample          |
| Hike cycle IV     | 2022-03..2023-07 | 0.08 -> 5.33           | +525bp    | 11 hikes in 17 months, four 75bp steps   |
| Plateau           | 2023-08..2024-08 | 5.33 held 13 months    | 0         | Higher-for-longer anchor                  |
| Easing leg I      | 2024-09..2025-01 | 5.33 -> 4.33           | -100bp    | Opens 50bp, then 25s                      |
| Hold              | 2025-01..2025-08 | 4.33 held 8 months     | 0         | Tariff/inflation watch pause             |
| Easing leg II     | 2025-09..2025-12 | 4.33 -> 3.72           | -61bp     | Resumes on labor cooling                 |
| 2026 drift        | 2026-01..2026-07 | 3.64 -> 3.63           | -1bp      | No monthly step >= 10bp all year         |

### 10b. Monthly inflection census (steps >= 10bp)

| Year | End lvl | Up-steps | Largest up        | Down-steps | Largest down      |
|------|---------|----------|-------------------|------------|-------------------|
| 2015 | 0.12    | 1        | Dec +0.12         | 0          | --                |
| 2016 | 0.54    | 2        | Dec +0.13         | 0          | --                |
| 2017 | 1.30    | 6        | Dec +0.14         | 0          | --                |
| 2018 | 2.27    | 4        | Oct +0.24         | 0          | --                |
| 2019 | 1.55    | 1        | Jan +0.13         | 3          | Nov -0.28         |
| 2020 | 0.09    | 0        | --                | 2          | Mar -0.93 (record)|
| 2021 | 0.08    | 0        | --                | 0          | --                |
| 2022 | 4.10    | 10       | Nov +0.70         | 0          | --                |
| 2023 | 5.33    | 5        | Feb +0.24         | 0          | --                |
| 2024 | 4.48    | 0        | --                | 4          | Oct -0.30         |
| 2025 | 3.72    | 0        | --                | 5          | Nov -0.21         |
| 2026*| 3.63    | 0        | --                | 0          | --                |

*2026 through July. Largest up-step ever: +0.70 (2022-11); largest down-step
ever: -0.93 (2020-03). Six true turning points: 2015-12 liftoff, 2019-07
pivot, 2020-03 crash, 2022-03 liftoff-II, 2024-09 pivot, 2025-09 resumption.

Read-through for deployment bands: the current 3.63 sits -170bp below the
5.33 plateau and roughly midway between the 2019 cycle peak (2.40) and
plateau; easing legs I and II together already delivered -161bp, more than
the entire 2019 insurance sequence. DGS10 did NOT follow the second leg --
see Section 8 -- so funds-rate relief alone has historically been insufficient
to reopen the long-end band (2019 analog: 3 cuts, DGS10 still rose into 2020).

## 11. Balance sheet deep dive -- WALCL, RRP lifecycle, WRESBAL drain

### 11a. WALCL monthly averages since the 2022 peak (USD trillions)

Peak weekly print 8.965T on 2022-04-13; peak monthly average 8.950T
(2022-04). Trough-to-date monthly averages:

| Month  | Avg | | Month  | Avg | | Month  | Avg |
|--------|-----|-|--------|-----|-|--------|-----|
| 2022-04| 8.950| | 2023-09| 8.057| | 2024-02| 7.604|
| 2022-06| 8.923| | 2023-12| 7.728| | 2024-06| 7.250|
| 2022-09| 8.817| | 2024-01| 7.670| | 2024-09| 7.104|
| 2022-12| 8.570| | 2024-03| 7.520| | 2024-12| 6.892|
| 2023-03| 8.552| | 2024-06| 7.250| | 2025-03| 6.753|
| 2023-04| 8.601| | 2024-09| 7.104| | 2025-06| 6.673|
| 2023-06| 8.370| | 2024-12| 6.892| | 2025-09| 6.606|

Full quarterly-average pace of QT (change vs prior quarter, USD billions):

| Quarter | Avg T | Chg | | Quarter | Avg T | Chg |
|---------|-------|-----|-|---------|-------|-----|
| 2022Q1  | 8.884 | +254| | 2024Q2  | 7.331 | -267|
| 2022Q2  | 8.936 | +52 | | 2024Q3  | 7.155 | -175|
| 2022Q3  | 8.856 | -80 | | 2024Q4  | 6.958 | -197|
| 2022Q4  | 8.651 | -204| | 2025Q1  | 6.795 | -164|
| 2023Q1  | 8.485 | -166| | 2025Q2  | 6.698 | -97 |
| 2023Q2  | 8.476 | -9  | | 2025Q3  | 6.630 | -68 |
| 2023Q3  | 8.166 | -310| | 2025Q4  | 6.575 | -54 |
| 2023Q4  | 7.832 | -335| | 2026Q1  | 6.614 | +39 |
| 2024Q1  | 7.598 | -234| | 2026Q2  | 6.713 | +98 |

QT anatomy: announced 2022-05, effective 2022-06 at 47.5B/mo, capped at
95B/mo from 2022-09. Realized pace lagged cap badly while RRP was full
(2022Q3 only -80B) because runoff was absorbed by money funds leaving RRP,
not reserves. Fastest stretch was 2023Q3-2023Q4 (-310B, -335B per quarter,
~300B/mo annualized pace exceeded cap due to maturity timing). Pace halved
twice -- 2024-06 slowdown, 2025-04 end of Treasury redemption cap --
producing the visible glide: -267B/qtr (2024Q2) -> -97 (2025Q2) -> -54
(2025Q4). Cumulative drawdown peak monthly avg (8.950T, 2022-04) to trough
monthly avg (6.565T, 2025-11): -2.385T, -26.6 percent. The balance sheet
then RE-EXPANDED: +39B (2026Q1), +98B (2026Q2), standing at 6.751T monthly
average for 2026-08, +186B off the trough -- consistent with the Section 2
observation that QT ended 2025-12-03. For scale: the prior-cycle trough was
3.760T (2019-08-28 weekly), so even after -2.4T of QT the footprint remains
~80 percent larger than 2019.

### 11b. RRP lifecycle (RRPONTSYD, daily, USD billions)

| Phase            | Dates           | Marker (avg unless noted)          |
|------------------|-----------------|------------------------------------|
| Background noise | 2015..2020      | tens of Bs; 96B avg 2015-03        |
| Empty at ZIRP    | 2021-01         | 1.0B                               |
| Takeoff          | 2021-06         | first >500B print 2021-06-09       |
| Build            | 2021-09..12     | 1,211 -> 1,600 monthly avg         |
| Peak zone        | 2022-06..2023-04| 2,162 -> peak avg 2,268 (2023-04)  |
| Record print     | 2022-12-30      | 2,553.7B single day                |
| Bleed            | 2023H2          | 2,054 (Jun) -> 808 (Dec avg)       |
| Last 4-figure day| 2023-12-29      | 1,018B                             |
| Residuals        | 2024..2025      | 171 (Dec-24), re-fill ~195 (Jun-25)|
| Final >100B day  | 2025-12-31      | 106.0B                             |
| Emptied          | 2026            | 1.5B avg 2026-07; ~0.2-0.3B Aug-26 |

Lifecycle verdict: RRP functioned as a ~2.3T shock absorber that took the
first 14 months of QT almost entirely onto itself (reserves barely moved
before mid-2023), then bled to zero over 30 months. With the facility empty,
the marginal buyer of bill issuance switched from money-fund RRP arb to bank
reserves -- which is precisely when the WRESBAL drain became binding.

### 11c. WRESBAL drain toward the scarcity floor

Weekly series peaks/troughs: cycle high 4.276T (2021-12-08; monthly avg
4.211T in 2021-12); prior-cycle scarcity floor 1.394T (2019-09-18, the repo-
crisis month; monthly avg 1.435T 2019-09).

Yearly averages (T): 2021 3.884 -> 2022 3.396 -> 2023 3.239 -> 2024 3.367
-> 2025 3.195 -> 2026 3.012 (through August). The 2023-2024 flatness is the
RRP-handoff artifact: once RRP exhausted (2024), QT hit reserves directly,
yet TGA behavior and ON RRP residuals masked it until 2025.

Late-drain sequence (monthly avgs, T): 2025-06 3.369 -> 2025-09 3.105 ->
2025-10 2.953 -> 2025-11 2.876 trough -> 2025-12 2.932 -> 2026 oscillation
2.93-3.08 -> 2026-08 2.958. The -493B slide over five months into the
November trough is the fastest reserves drain of the cycle and coincides
with the SOFR stress cluster documented in Section 12 (episode L).

Scarcity-floor arithmetic: the 2019 floor was 1.435T nominal, but the
floor is a FUNCTION of non-reserve liabilities (currency, TGA) and bank
balance-sheet capacity, both far larger in 2026. The operative early-warning
line stays the Section 8 trigger -- weekly prints under 2.85T -- which
November 2025 approached (2.876T monthly avg) before the partial rebound.
Current 2.958T sits only ~110B above that line: the cushion, not the level,
is the story. Watch for a second leg down if bill supply or TGA rebuild
presses reserves again with RRP unavailable as a buffer.

## 12. SOFR and money markets -- spread series and stress spikes

Distribution of the daily SOFR-FEDFUNDS spread, full sample (n=2080):
mean -0.3bp, median -1.0bp, p95 +17bp, p99 +42bp, extremes -73bp
(2022-11-01, SOFR sagging below funds during the steepest hike phase) to
+321bp (2019-09-17). Negative median is structural: SOFR normally prints
at or a hair below EFFR because it is collateral-heavy and bureau-skewed.

Yearly spread profile (bp; med / p95 / p99 / max):

| Year | Obs | Med  | p95  | p99  | Max   | Character                        |
|------|-----|------|------|------|-------|----------------------------------|
| 2018 | 187 | +1.0 | +14  | +30  | +73   | QT-1 friction builds             |
| 2019 | 250 | +1.0 | +17  | +51  | +321  | Repo crisis                      |
| 2020 | 251 | 0.0  | +3   | +58  | +99   | Dash-for-cash, then flood        |
| 2021 | 250 | -4.0 | -1   | +1   | +2    | Ample-reserve calm (only 0 spikes)|
| 2022 | 249 | -3.0 | +29  | +43  | +60   | Liftoff frictions                |
| 2023 | 249 | -2.0 | +6   | +19  | +22   | Post-BTFP normalization          |
| 2024 | 250 | -1.0 | +20  | +22  | +25   | Quarter-end bites return         |
| 2025 | 249 | +1.0 | +20  | +29  | +40   | Reserves squeeze, worst since '19 era|
| 2026 | 145 | 0.0  | +6   | +9   | +11   | Calm restored                    |

Stress episodes (>5bp days, clustered at 7-day gaps; 284 spike days in 59
episodes total). Major windows only:

| Episode               | Window        | Spike days | Worst bp | Worst date   |
|-----------------------|---------------|------------|----------|--------------|
| QT-1 grind            | 2018-04..12   | 42         | +30      | 2018-06-29   |
| YE-2018 squeeze       | 2018-12..2019-01| 12       | +75      | 2019-01-02   |
| Pre-crisis pressure   | 2019-01..2019-09| 32       | +34      | 2019-04-30   |
| REPO CRISIS           | 2019-09-16..18| 12 (Sep)   | +321     | 2019-09-17   |
| Aftershocks           | 2019-09-30..10| 8          | +31      | 2019-09-30   |
| Dash-for-cash         | 2020-03       | 10         | +99      | 2020-03-03   |
| 2021 calm             | 2021          | 0          | --       | --           |
| Liftoff frictions     | 2022          | 41         | +60      | 2022-07-28   |
| 2023 (SVB quarter)    | 2023          | 13         | +22      | 2023-03-31   |
| 2024 quarter-ends     | 2024          | 36         | +25      | 2024-09-16   |
| 2025 early            | 2025-01..09   | 27         | +29      | 2025-09-15   |
| RESERVES SQUEEZE      | 2025-10..12   | 41         | +40      | 2025-12-01   |
| 2026 normalization    | 2026          | 10         | +11      | 2026-01-02   |

Interpretation rules this series supports:

1. Baseline corridor health is median -1 to +1bp. Sustained medians ABOVE
   +5bp for a full quarter have occurred exactly twice: 2018H2 and 2025H2 --
   both times with reserves draining toward scarcity, both times followed
   by central-bank liquidity response (2019 repo ops; the 2025-12 balance
   sheet re-expansion documented in 11a).
2. The 2025Q4 episode is the longest spike run since 2018 (41 days) though
   its amplitude (+40bp max) stayed an order of magnitude under 2019's
   +321bp -- a grinding squeeze, not a blow-up. It validated the Section 8
   warning chain: WRESBAL trough 2.876T -> SOFR pops -> balance sheet
   re-expansion within weeks.
3. 2026 reads clean (p95 +6bp, worst +11bp on 2026-01-02): the funding
   market currently prices reserves as adequate-but-not-lavish. Any return
   of multi-week >15bp runs with WRESBAL under 2.9T should be treated as
   the leading indicator of a 2019-style event, ahead of both VIX and the
   equity band triggers.
4. Quarter-end prints (>20bp on 2022-06-28, 2024-09-16 type dates) are
   genuine but transient balance-sheet-window dressing; they only matter
   when they FAIL to fade in the first days of the new quarter -- the
   2019-09 failure mode.

Cross-links: funds-rate context in Section 10, current corridor snapshot in
Section 4, deployment implications in Section 8. Store query for this
appendix: SELECT date, value FROM factors WHERE ticker='MACRO' AND factor IN
('FEDFUNDS','SOFR','WALCL','WRESBAL','RRPONTSYD') ORDER BY factor, date;
spread derivation joins SOFR to the FEDFUNDS row of the same month.

---

# Deep Sections -- Credit, Yen/FX, Stress Composite

Appended 2026-08-24 from Efforts/osanwe-v2-overhaul/_work/factors.db
(ticker=MACRO factors + bars). All figures computed from the local store;
no network. BAMLH0A0HYM2 values are stored in PERCENT (3.88 = 388 bp);
regime thresholds are applied on bp.

## Credit Market Architecture

High Yield OAS (BAMLH0A0HYM2, ICE BofA US High Yield Index option-adjusted
spread). Store coverage 2023-08-22 through 2026-08-20, 787 daily obs.
This is NOT full FRED history (1996+); the store window begins 2023-08.

### Monthly averages (percent)

| Month | Avg | Min | Max | | Month | Avg | Min | Max |
|---|---|---|---|---|---|---|---|---|
| 2023-08 | 3.88 | 3.80 | 3.93 || 2025-03 | 3.17 | 2.88 | 3.55 |
| 2023-09 | 3.89 | 3.77 | 4.09 || 2025-04 | 4.03 | 3.42 | 4.61 |
| 2023-10 | 4.36 | 4.11 | 4.53 || 2025-05 | 3.35 | 3.09 | 3.78 |
| 2023-11 | 3.99 | 3.80 | 4.47 || 2025-06 | 3.13 | 2.96 | 3.27 |
| 2023-12 | 3.57 | 3.32 | 3.87 || 2025-07 | 2.89 | 2.80 | 3.00 |
| 2024-01 | 3.55 | 3.39 | 3.71 || 2025-08 | 2.90 | 2.75 | 3.13 |
| 2024-02 | 3.36 | 3.22 | 3.56 || 2025-09 | 2.79 | 2.69 | 2.92 |
| 2024-03 | 3.18 | 3.05 | 3.32 || 2025-10 | 2.92 | 2.76 | 3.18 |
| 2024-04 | 3.23 | 3.10 | 3.42 || 2025-11 | 3.08 | 2.92 | 3.20 |
| 2024-05 | 3.12 | 3.03 | 3.21 || 2025-12 | 2.89 | 2.81 | 2.99 |
| 2024-06 | 3.20 | 3.09 | 3.29 || 2026-01 | 2.74 | 2.64 | 2.88 |
| 2024-07 | 3.16 | 3.02 | 3.27 || 2026-02 | 2.92 | 2.81 | 3.12 |
| 2024-08 | 3.37 | 3.13 | 3.93 || 2026-03 | 3.19 | 2.97 | 3.46 |
| 2024-09 | 3.26 | 3.03 | 3.46 || 2026-04 | 2.93 | 2.82 | 3.17 |
| 2024-10 | 2.93 | 2.80 | 3.07 || 2026-05 | 2.77 | 2.71 | 2.86 |
| 2024-11 | 2.70 | 2.60 | 2.87 || 2026-06 | 2.73 | 2.63 | 2.83 |
| 2024-12 | 2.76 | 2.64 | 2.94 || 2026-07 | 2.74 | 2.67 | 2.87 |
| 2025-01 | 2.72 | 2.59 | 2.88 || 2026-08 * | 2.72 | 2.67 | 2.78 |
| 2025-02 | 2.71 | 2.62 | 2.87 ||

* 2026-08 partial (14 obs through 2026-08-20).

Full-window stats: mean 3.15 pct (315 bp); min 2.59 pct (2025-01-22);
max 4.61 pct (2025-04-07). Yearly means: 2023 3.95, 2024 3.15, 2025 3.05,
2026 2.85. Latest print 2.75 (2026-08-20).

### Regime classification (thresholds on bp)

| Regime | Band | Daily obs | Share of window | Months (avg-based) |
|---|---|---|---|---|
| Tight   | < 300 bp    | 356 | 45.2% | 17 of 37 |
| Normal  | 300-400 bp  | 382 | 48.5% | 18 of 37 |
| Stressed| 400-550 bp  | 49  | 6.2%  | 2 of 37  |
| Crisis  | > 550 bp    | 0   | 0.0%  | 0 of 37  |

Duration detail -- contiguous non-tight runs:

| Window | Regime | Calendar days spanned | Obs |
|---|---|---|---|
| 2023-08-22 -> 2023-09-25 | Normal (Aug avg 3.88, Sep 3.89) | 34 | 25 |
| 2023-09-26 -> 2023-11-13 | Stressed (Oct avg 4.36, peak 4.53) | 48 | 36 |
| 2023-11-16              | Stressed one-day blip            | 1  | 1  |
| 2023-11-17 -> 2025-04-02 | Normal                          | 502 | 359 |
| 2025-04-03 -> 2025-04-21 | Stressed (tariff shock, max 4.61) | 18 | 12 |
| 2025-04-22 -> 2026-08-20 | Normal, tight since Jul-2026     | 320 | 352 |

Reading: the whole store window is tight-or-normal except two short stressed
bursts (Oct-Nov 2023 duration scare; Apr 2025 tariff shock). No crisis-regime
observation exists in-window. From Jun 2025 through Aug 2026 the monthly
average has printed under 300 bp for 15 straight months -- historically a
late-cycle compression extreme. Spread cushion is thin by pre-2024 standards:
the 2023 stressed episode ignited from an average near 3.88 (one ~100 bp
leg from normal into stressed). Today sits 25 bp above the tight line, but
cushion is illusory at these speeds: Apr-2025 went 3.42 (Apr-02 close) to
4.61 (Apr-07) in three trading days -- a 119 bp shock in one week.

## Yen and Global FX

DEXJPUS (USD/JPY noon buying rate). Store coverage 2015-01-02 through
2026-08-14, 2904 obs. RISING = yen WEAKENING (more yen per dollar).

### Monthly average levels, 2015-2026

| Month | Avg | Min | Max || Month | Avg | Min | Max |
|---|---|---|---|---|---|---|---|---|
| 2015-01 | 118.25 | 116.78 | 120.20 || 2020-11 | 104.41 | 103.32 | 105.58 |
| 2015-02 | 118.76 | 117.33 | 120.38 || 2020-12 | 103.80 | 103.13 | 104.52 |
| 2015-03 | 120.39 | 119.01 | 121.50 || 2021-01 | 103.79 | 102.70 | 104.64 |
| 2015-04 | 119.51 | 118.80 | 120.36 || 2021-02 | 105.38 | 104.62 | 106.64 |
| 2015-05 | 120.80 | 119.09 | 124.18 || 2021-03 | 108.70 | 106.68 | 110.61 |
| 2015-06 | 123.72 | 122.10 | 125.58 || 2021-04 | 109.04 | 107.94 | 110.67 |
| 2015-07 | 123.31 | 120.54 | 124.38 || 2021-05 | 109.11 | 108.52 | 109.83 |
| 2015-08 | 123.00 | 118.56 | 124.90 || 2021-06 | 110.11 | 109.25 | 111.05 |
| 2015-09 | 120.15 | 119.05 | 120.94 || 2021-07 | 110.21 | 109.45 | 111.56 |
| 2015-10 | 120.05 | 118.26 | 121.20 || 2021-08 | 109.85 | 109.09 | 110.54 |
| 2015-11 | 122.64 | 120.70 | 123.51 || 2021-09 | 110.16 | 109.33 | 111.83 |
| 2015-12 | 121.63 | 120.27 | 123.52 || 2021-10 | 113.12 | 110.94 | 114.31 |
| 2016-01 | 118.23 | 116.38 | 121.05 || 2021-11 | 113.97 | 112.87 | 115.34 |
| 2016-02 | 114.62 | 111.36 | 121.06 || 2021-12 | 113.83 | 112.82 | 115.17 |
| 2016-03 | 112.93 | 111.30 | 113.94 || 2022-01 | 114.83 | 113.72 | 116.12 |
| 2016-04 | 109.55 | 106.90 | 112.06 || 2022-02 | 115.28 | 114.36 | 115.91 |
| 2016-05 | 108.85 | 106.34 | 110.75 || 2022-03 | 118.58 | 114.65 | 123.25 |
| 2016-06 | 105.35 | 101.66 | 109.55 || 2022-04 | 126.37 | 122.60 | 130.94 |
| 2016-07 | 104.19 | 100.65 | 106.65 || 2022-05 | 128.85 | 126.56 | 130.41 |
| 2016-08 | 101.24 | 100.07 | 103.38 || 2022-06 | 133.96 | 129.83 | 136.50 |
| 2016-09 | 101.78 | 100.34 | 104.18 || 2022-07 | 136.71 | 133.25 | 138.94 |
| 2016-10 | 103.91 | 101.54 | 105.40 || 2022-08 | 135.28 | 131.80 | 138.74 |
| 2016-11 | 108.44 | 103.02 | 114.34 || 2022-09 | 143.28 | 139.93 | 144.71 |
| 2016-12 | 116.00 | 113.50 | 118.32 || 2022-10 | 147.05 | 144.32 | 149.82 |
| 2017-01 | 114.87 | 112.72 | 117.68 || 2022-11 | 142.44 | 138.28 | 148.18 |
| 2017-02 | 112.91 | 111.74 | 114.34 || 2022-12 | 134.91 | 131.08 | 137.92 |
| 2017-03 | 112.92 | 110.48 | 115.02 || 2023-01 | 130.45 | 127.85 | 133.57 |
| 2017-04 | 110.09 | 108.40 | 111.52 || 2023-02 | 133.05 | 128.45 | 136.36 |
| 2017-05 | 112.24 | 110.68 | 114.19 || 2023-03 | 133.66 | 130.64 | 137.18 |
| 2017-06 | 110.91 | 109.16 | 112.42 || 2023-04 | 133.47 | 131.11 | 135.99 |
| 2017-07 | 112.42 | 110.38 | 114.20 || 2023-05 | 137.05 | 133.76 | 140.53 |
| 2017-08 | 109.83 | 108.89 | 110.80 || 2023-06 | 141.36 | 138.74 | 144.72 |
| 2017-09 | 110.78 | 107.72 | 112.76 || 2023-07 | 140.94 | 138.14 | 144.56 |
| 2017-10 | 112.91 | 111.72 | 113.92 || 2023-08 | 144.78 | 141.79 | 146.40 |
| 2017-11 | 112.82 | 111.00 | 114.25 || 2023-09 | 147.84 | 146.20 | 149.48 |
| 2017-12 | 112.94 | 111.88 | 113.62 || 2023-10 | 149.59 | 148.49 | 151.46 |
| 2018-01 | 110.87 | 108.38 | 113.18 || 2023-11 | 149.68 | 147.39 | 151.56 |
| 2018-02 | 107.97 | 106.10 | 110.40 || 2023-12 | 143.98 | 140.92 | 147.26 |
| 2018-03 | 106.05 | 104.83 | 106.91 || 2024-01 | 146.29 | 141.89 | 148.55 |
| 2018-04 | 107.66 | 105.99 | 109.33 || 2024-02 | 149.62 | 146.18 | 150.79 |
| 2018-05 | 109.69 | 108.62 | 111.08 || 2024-03 | 149.82 | 146.86 | 151.66 |
| 2018-06 | 110.06 | 109.45 | 110.71 || 2024-04 | 153.89 | 151.55 | 157.62 |
| 2018-07 | 111.52 | 110.48 | 112.98 || 2024-05 | 155.87 | 152.85 | 157.65 |
| 2018-08 | 111.00 | 110.38 | 111.80 || 2024-06 | 157.86 | 154.87 | 160.88 |
| 2018-09 | 112.10 | 110.87 | 113.48 || 2024-07 | 157.52 | 150.38 | 161.73 |
| 2018-10 | 112.72 | 111.65 | 114.19 || 2024-08 | 146.26 | 143.95 | 150.06 |
| 2018-11 | 113.34 | 112.54 | 113.97 || 2024-09 | 142.95 | 140.66 | 145.82 |
| 2018-12 | 112.20 | 109.70 | 113.66 || 2024-10 | 149.89 | 143.66 | 153.47 |
| 2019-01 | 108.96 | 108.07 | 109.79 || 2024-11 | 153.71 | 150.41 | 155.96 |
| 2019-02 | 110.44 | 109.55 | 111.38 || 2024-12 | 153.81 | 149.12 | 158.01 |
| 2019-03 | 111.14 | 109.76 | 111.98 || 2025-01 | 156.48 | 154.22 | 158.31 |
| 2019-04 | 111.64 | 110.92 | 112.00 || 2025-02 | 151.57 | 149.09 | 154.68 |
| 2019-05 | 109.97 | 108.66 | 111.39 || 2025-03 | 149.06 | 147.13 | 150.97 |
| 2019-06 | 108.07 | 106.92 | 108.56 || 2025-04 | 144.13 | 140.81 | 149.98 |
| 2019-07 | 108.29 | 107.74 | 108.86 || 2025-05 | 144.88 | 142.61 | 148.09 |
| 2019-08 | 106.19 | 105.30 | 108.28 || 2025-06 | 144.48 | 142.76 | 146.47 |
| 2019-09 | 107.54 | 105.88 | 108.17 || 2025-07 | 147.20 | 143.58 | 150.60 |
| 2019-10 | 108.14 | 106.76 | 109.02 || 2025-08 | 147.48 | 146.82 | 148.35 |
| 2019-11 | 108.86 | 108.16 | 109.47 || 2025-09 | 147.86 | 146.36 | 149.78 |
| 2019-12 | 109.10 | 108.53 | 109.67 || 2025-10 | 151.35 | 147.16 | 154.17 |
| 2020-01 | 109.27 | 107.94 | 110.16 || 2025-11 | 155.14 | 152.97 | 157.41 |
| 2020-02 | 110.03 | 108.12 | 111.86 || 2025-12 | 155.91 | 154.80 | 157.43 |
| 2020-03 | 107.67 | 102.52 | 111.44 || 2026-01 | 156.65 | 152.88 | 159.06 |
| 2020-04 | 107.74 | 106.67 | 109.11 || 2026-02 | 155.10 | 152.64 | 157.10 |
| 2020-05 | 107.20 | 106.07 | 107.89 || 2026-03 | 158.68 | 156.93 | 160.16 |
| 2020-06 | 107.58 | 106.44 | 109.68 || 2026-04 | 159.12 | 156.66 | 160.23 |
| 2020-07 | 106.68 | 105.03 | 107.55 || 2026-05 | 158.15 | 156.44 | 159.47 |
| 2020-08 | 106.01 | 105.30 | 106.89 || 2026-06 | 160.77 | 159.66 | 162.61 |
| 2020-09 | 105.59 | 104.44 | 106.34 || 2026-07 | 162.33 | 159.16 | 163.86 |
| 2020-10 | 105.21 | 104.33 | 105.98 || 2026-08 * | 158.40 | 156.96 | 159.35 |

* 2026-08 partial (10 obs through 2026-08-14).

Era anchors (monthly avgs): 2015 ~118-124 (Abenomics weak-yen plateau);
2016 flight-to-safety squeeze 105-116; 2019-2021 range 103-113; 2022
policy-divergence collapse 115 -> 147 (Oct avg peak); 2023-24 grind to
157.86 (Jun-2024 avg, intramonth 160.88); Jul-Aug 2024 carry unwind snap
(avg 157.52 -> 146.26); re-weakening to 156.65 (Jan-2026 avg); fresh
cycle high 162.33 avg in Jul-2026 before a sharp Aug reversal to 158.40.
Full-range extremes: weakest 163.86 (Jul-2026), strongest 100.07
(Aug-2016).

### Carry-unwind episodes (>3 pct USD/JPY move within <=5 calendar days)

32 deduplicated episodes over 2015-2026. Sign convention: negative = yen
STRENGTHENING (classic unwind trigger). Forward equity columns measure
the 10 trading days after episode END: worst drawdown from any new high,
then net return. Bars coverage starts 2021-08-24 (-- = pre-bars).

| Start | End | Move | SMH DD/Ret | NVDA DD/Ret | SPY DD/Ret | Trigger context |
|---|---|---|---|---|---|---|
| 2015-08-19 | 2015-08-24 | -4.5% | -- | -- | -- | China devaluation risk-off |
| 2016-02-01 | 2016-02-04 | -3.6% | -- | -- | -- | BoJ negative-rate shock |
| 2016-02-08 | 2016-02-11 | -3.4% | -- | -- | -- | Global growth scare follow-through |
| 2016-04-27 | 2016-05-02 | -4.3% | -- | -- | -- | BoJ hold disappointment |
| 2016-05-31 | 2016-06-03 | -3.5% | -- | -- | -- | Pre-Brexit flight to safety |
| 2016-06-23 | 2016-06-27 | -4.0% | -- | -- | -- | Brexit vote |
| 2016-07-08 | 2016-07-12 | +4.0% | -- | -- | -- | Post-Brexit rebound |
| 2016-07-25 | 2016-07-29 | -3.5% | -- | -- | -- | BoJ stimulus underwhelms |
| 2016-07-28 | 2016-08-02 | -3.9% | -- | -- | -- | Follow-through selling |
| 2016-11-09 | 2016-11-14 | +3.3% | -- | -- | -- | Trump-election reflation |
| 2020-03-04 | 2020-03-09 | -4.5% | -- | -- | -- | COVID oil-crash day |
| 2020-03-09 | 2020-03-13 | +4.5% | -- | -- | -- | Emergency rebound |
| 2020-03-16 | 2020-03-20 | +5.4% | -- | -- | -- | Dollar-squeeze whipsaw |
| 2020-03-25 | 2020-03-30 | -3.0% | -- | -- | -- | Fed unlimited-QE calm-down |
| 2022-06-16 | 2022-06-21 | +3.5% | -9.3% / -6.2% | -15.2% / -8.7% | -3.3% / +2.2% | BoJ yield-curve-control defense |
| 2022-07-27 | 2022-08-01 | -4.0% | -6.5% / +3.7% | -11.1% / +3.2% | -0.7% / +4.4% | Recession scare reversal |
| 2022-09-02 | 2022-09-07 | +3.1% | -7.7% / -3.9% | -10.9% / -3.3% | -7.8% / -4.7% | Hawkish-Fed dollar surge |
| 2022-11-07 | 2022-11-10 | -3.3% | -4.4% / +3.5% | -8.1% / +3.3% | -1.1% / +1.9% | CPI-miss relief rally |
| 2022-11-09 | 2022-11-14 | -3.9% | -4.5% / -1.5% | -8.1% / -4.0% | -1.8% / +0.0% | Post-CPI giveback |
| 2022-11-30 | 2022-12-02 | -3.2% | -6.2% / -4.6% | -8.3% / -1.8% | -5.4% / -5.4% | Powell Brookings speech |
| 2022-12-15 | 2022-12-20 | -5.0% | -7.1% / -2.3% | -14.9% / -11.3% | -2.5% / -0.3% | BoY tweak / year-end unwind |
| 2023-01-11 | 2023-01-13 | -3.6% | -3.1% / +3.4% | -5.9% / +13.4% | -2.5% / +0.5% | Yen rebound on BoJ review chatter |
| 2023-02-02 | 2023-02-06 | +3.4% | -7.0% / -3.8% | -10.1% / -2.1% | -3.9% / -2.6% | Hot US jobs report |
| 2023-12-11 | 2023-12-14 | -3.3% | -2.8% / +1.5% | -3.9% / +2.4% | -1.4% / +1.1% | Dovish FOMC |
| 2024-05-01 | 2024-05-03 | -3.0% | -1.6% / +5.8% | -3.7% / +4.2% | -0.2% / +3.6% | Intervention suspicion |
| 2024-07-29 | 2024-08-02 | -4.5% | -3.2% / +12.9% | -7.8% / +16.1% | -2.9% / +4.0% | Jul-2024 carry UNWIND begins |
| 2024-08-01 | 2024-08-06 | -3.3% | -2.8% / +14.1% | -5.1% / +22.1% | -0.7% / +7.0% | Unwind climax (Aug 5 crash) |
| 2024-09-30 | 2024-10-04 | +3.8% | -5.4% / +1.5% | -4.7% / +10.5% | -0.9% / +2.0% | US data surge |
| 2025-05-07 | 2025-05-12 | +3.2% | -4.3% / +3.2% | -3.2% / +10.2% | -2.6% / +1.4% | US-China tariff truce |
| 2025-10-03 | 2025-10-08 | +3.7% | -6.0% / -2.2% | -6.6% / -4.7% | -3.0% / -0.8% | Risk-on melt-up |
| 2026-01-22 | 2026-01-27 | -3.4% | -8.7% / -0.6% | -10.7% / +0.0% | -2.6% / -0.5% | DeepSeek-style AI capex scare |
| 2026-07-29 | 2026-08-03 | -4.2% | -2.3% / +8.9% | -2.9% / +8.9% | -0.7% / +2.0% | Jul-2026 unwind (BOJ hike fear) |

Aggregates (forward 10-day window after episode end):

| Cohort | N | SMH avgDD | NVDA avgDD | SPY avgDD | SMH ret | NVDA ret | SPY ret | SMH worst | NVDA worst | SPY worst |
|---|---|---|---|---|---|---|---|---|---|---|
| All episodes (bars era) | 18 | -5.2 | -7.8 | -2.4 | +1.9 | +3.2 | +0.9 | -9.3 | -15.2 | -7.8 |
| Yen strength >3 pct (unwind-type) | 12 | -4.4 | -7.5 | -1.9 | +3.7 | +4.7 | +1.5 | -8.7 | -14.9 | -5.4 |
| Yen weakness >3 pct | 6 | -6.6 | -8.5 | -3.6 | -1.9 | +0.3 | -0.4 | -9.3 | -15.2 | -7.8 |

Correlation read (daily moves, 2021-08-25 -> 2026-08-14 overlap, n=1236):

- DEXJPUS daily change vs same-day returns: SMH -0.004, NVDA 0.011, SPY 0.000.
- On the 57 days the yen firmed more than 1 pct: SMH averaged +0.69 pct (all-days +0.14), NVDA +0.78 (all +0.24), SPY +0.29 (all +0.05).

Interpretation: contemporaneous correlation is ~zero because yen strength
is usually SYMPTOM (risk-off bid) rather than CAUSE. The damage shows up
in the event tails, not the mean: unwind cohorts carry -15 to -16 pct
worst-case NVDA drawdowns within ten sessions (Dec-2022, Jan-2026) versus
a -2 to -8 pct typical path, and the two canonical unwinds (Aug-2024,
Aug-2026) each produced SMH forward drawdowns around -3 pct followed by
double-digit recoveries once the squeeze passed -- i.e. unwind shocks buy
the dip in semis when credit stays tight-regime, but the Jan-2026 episode
(yen -3.4 pct WITH an AI-capex narrative shock) was the one that stuck,
leaving NVDA flat over the following month.

## Financial Stress Composite

STLFSI4 (St Louis Fed Financial Stress Index, weekly). Store coverage
2015-01-02 through 2026-08-14, 607 obs.

### Current reading

| Metric | Value |
|---|---|
| Latest (2026-08-14) | -0.8285 |
| Historical percentile (store window) | 4.0 pct |
| Window mean | -0.266 |
| Window min | -0.9666 (2025-01-24) |
| Window max | 5.6565 (2020-03-20) |

Interpretation: at -0.83 the system is deeply DE-STRESSED -- the reading
sits in the bottom 96 pct of the eleven-year window and roughly one
full point of index units below zero. Stress this compressed has
coincided with HY spreads in the tight regime (see Credit section) and
with the semis tape making highs; the asymmetry risk is that zero is
~0.83 units away, and every historical stress burst crossed that
distance in under four weeks once it started.

### Episodes above zero (stress readings), >=3 consecutive-ish obs

| Episode start | End | Peak | Cal days | Obs | Event family |
|---|---|---|---|---|---|
| 2015-08-21 | 2015-10-30 | 0.7083 | 70 | 11 | China devaluation / commodity bust |
| 2015-11-13 | 2016-04-15 | 1.2687 | 154 | 23 | China devaluation / commodity bust |
| 2016-04-29 | 2016-07-08 | 0.5978 | 70 | 11 | China FX + Brexit + election sequence |
| 2016-07-22 | 2016-11-04 | 0.5061 | 105 | 16 | China FX + Brexit + election sequence |
| 2018-03-23 | 2018-04-13 | 0.3426 | 21 | 4 | Volmageddon, Q4 rate-hike panic |
| 2018-12-07 | 2019-01-04 | 0.6761 | 28 | 5 | Volmageddon, Q4 rate-hike panic |
| 2019-09-27 | 2019-10-11 | 0.3730 | 14 | 3 | Repo squeeze, trade-war flare-ups |
| 2020-02-28 | 2020-05-29 | 5.6565 | 91 | 14 | COVID crisis (all-time 5.66 peak) |
| 2020-06-12 | 2020-07-17 | 0.5171 | 35 | 6 | COVID crisis (all-time 5.66 peak) |
| 2022-02-25 | 2022-03-11 | 0.3051 | 14 | 3 | Hiking cycle + Ukraine + UK gilt |
| 2022-04-29 | 2022-05-27 | 0.5701 | 28 | 5 | Hiking cycle + Ukraine + UK gilt |
| 2022-06-17 | 2022-07-15 | 0.6222 | 28 | 5 | Hiking cycle + Ukraine + UK gilt |
| 2022-09-23 | 2022-10-14 | 0.5218 | 21 | 4 | Hiking cycle + Ukraine + UK gilt |
| 2022-12-09 | 2022-12-23 | 0.1341 | 14 | 3 | Hiking cycle + Ukraine + UK gilt |

Excluded micro-blips (short/low runs under the >=3 obs / >=14 day bar):
14 occurrences, mostly single Friday prints in 2015-2020; the only
post-2020 ones are the Mar-2023 SVB week (peak 1.12) and the Apr-2025
tariff blip (peak 0.59, two prints).

Episode census: 132 total obs above zero out of 607 (22 pct of window).
The index has NOT closed above zero since the Apr-2025 tariff blip
(peak 0.587, two prints) -- 70 consecutive weeks of de-stress as of
the latest print. Combined with tight HY spreads and an empty RRP, the
composite says maximum-complacency plumbing; the watch item is the
same one flagged in section 8 -- reserves draining toward the
funding-critical zone while every stress gauge idles at floor levels.

### Regeneration notes (Part 2 sections)

```
-- HY OAS monthly panel + regime cuts (values stored in percent)
SELECT substr(date,1,7) ym, AVG(value)*100 bp_avg FROM factors
 WHERE factor='BAMLH0A0HYM2' GROUP BY ym ORDER BY ym;
-- carry-unwind scan (>3 pct within 5 calendar days)
-- self-join DEXJPUS on julianday(date) diff <= 5, abs(pct change) > 3;
-- then join bars ON date >= episode_end ORDER BY ticker, date LIMIT 11
-- STLFSI4 percentile
SELECT 100.0*SUM(CASE WHEN value<=:last THEN 1 ELSE 0 END)/COUNT(*)
  FROM factors WHERE factor='STLFSI4';
```


# Deep Sections -- Rate Cycles, Balance Sheet, Money Markets

## Historical Rate Cycles

Inflection points of FEDFUNDS (effective federal funds rate, MONTHLY AVERAGE
series) 2015-2026. An inflection here is a sustained turn of at least 25 bps;
smaller month-to-month wiggles are averaging noise. Dates are the first month
whose average reflects the turn, so each leg registers 2-6 weeks after the
underlying FOMC action.

| Turn (first month avg reflects it) | Rate at turn | Move since prior turn | Regime note |
|------------------------------------|--------------|-----------------------|-------------|
| 2015-01 | 0.11 | --            | ZIRP base entering the store window |
| 2015-12 | 0.24 | +13 bps       | Liftoff (Dec 2015 hike) |
| 2016-12 | 0.54 | +30 bps       | Slow grind; only +30 bps across all of 2016 |
| 2018-12 | 2.27 | +173 bps      | Last hike of the cycle; monthly avg crests at 2.42 by 2019-04 |
| 2019-08 | 2.13 | -14 bps       | Pivot: "insurance" cuts begin |
| 2019-11 | 1.55 | -58 bps       | Three cuts done; cycle rolls over into 2020 |
| 2020-03 | 0.65 | -93 bps m/m   | COVID emergency; -153 bps vs the Feb 2020 avg of 1.58 |
| 2020-04 | 0.05 | -60 bps       | ZIRP restored; cycle trough |
| 2022-03 | 0.20 | +15 bps       | Liftoff II |
| 2023-08 | 5.33 | +513 bps      | Terminal rate; +528 bps measured from the 2020-04 trough |
| 2024-09 | 5.13 | -20 bps       | First cut after a 13-month plateau at 5.33 (2023-08 to 2024-08) |
| 2025-01 | 4.33 | -80 bps       | Pause; -100 bps delivered in four months |
| 2025-09 | 4.22 | -11 bps       | Cuts resume after an 8-month hold |
| 2026-05 | 3.63 | -59 bps       | Plateau; -58 bps through the 2026-01 avg, flat 3.63 since |

Cycle context (same store):

- Hiking speed: 2015-12 to 2018-12 added +203 bps over 24 months (~8 bps/mo);
  2022-03 to 2023-08 added +513 bps over 17 months (~30 bps/mo), roughly 3.5x
  faster. Cutting shows the same asymmetry: -100 bps in 4 months (2024-09 to
  2025-01) versus -58 bps in 4 months (2025-09 to 2026-01).
- Longest hold: 5.33 for 13 consecutive monthly averages (2023-08 to
  2024-08); the current 3.63 plateau has run seven prints (2026-01 through
  2026-07, store end).
- Yield backdrop at the turns: DGS10 went 2.12 (2015-01-02) -> 4.05 at the
  2023-08 peak -> 4.39 at the 2026-05 turn; T10Y3M bottomed at -1.89 pp on
  2023-05-04 (deepest inversion in store) and was +0.71 pp by 2026-05, i.e.
  the curve dis-inverted as the Fed cut from 5.33 toward 3.63.

## Balance Sheet Deep Dive

WALCL (Fed total assets) peaked the week of 2022-04-13 at USD 8,965,487MM
(about 8.97T). Monthly averages since that peak (USD M, raw store units;
MoM = change in monthly average):

| Month   | Avg ($M) | MoM ($M) |
|---------|----------|----------|
| 2022-04 | 8,953,512 | -- |
| 2022-05 | 8,935,540 | -17973 |
| 2022-06 | 8,922,725 | -12815 |
| 2022-07 | 8,894,234 | -28491 |
| 2022-08 | 8,856,210 | -38024 |
| 2022-09 | 8,816,882 | -39328 |
| 2022-10 | 8,746,258 | -70624 |
| 2022-11 | 8,637,468 | -108790 |
| 2022-12 | 8,570,432 | -67036 |
| 2023-01 | 8,493,903 | -76529 |
| 2023-02 | 8,408,984 | -84919 |
| 2023-03 | 8,552,199 | +143215 |
| 2023-04 | 8,600,803 | +48604 |
| 2023-05 | 8,457,176 | -143627 |
| 2023-06 | 8,370,156 | -87020 |
| 2023-07 | 8,278,283 | -91873 |
| 2023-08 | 8,164,223 | -114060 |
| 2023-09 | 8,056,563 | -107660 |
| 2023-10 | 7,937,207 | -119356 |
| 2023-11 | 7,829,861 | -107346 |
| 2023-12 | 7,728,449 | -101412 |
| 2024-01 | 7,669,766 | -58683 |
| 2024-02 | 7,603,666 | -66100 |
| 2024-03 | 7,519,978 | -83688 |
| 2024-04 | 7,421,418 | -98560 |
| 2024-05 | 7,320,808 | -100611 |
| 2024-06 | 7,249,592 | -71216 |
| 2024-07 | 7,207,538 | -42053 |
| 2024-08 | 7,154,034 | -53505 |
| 2024-09 | 7,104,191 | -49842 |
| 2024-10 | 7,035,189 | -69002 |
| 2024-11 | 6,947,570 | -87620 |
| 2024-12 | 6,892,152 | -55418 |
| 2025-01 | 6,838,012 | -54140 |
| 2025-02 | 6,793,220 | -44792 |
| 2025-03 | 6,753,142 | -40078 |
| 2025-04 | 6,722,838 | -30305 |
| 2025-05 | 6,696,532 | -26305 |
| 2025-06 | 6,673,324 | -23208 |
| 2025-07 | 6,656,215 | -17109 |
| 2025-08 | 6,626,564 | -29651 |
| 2025-09 | 6,606,256 | -20308 |
| 2025-10 | 6,590,191 | -16065 |
| 2025-11 | 6,565,224 | -24967 |
| 2025-12 | 6,570,759 | +5535 |
| 2026-01 | 6,581,862 | +11104 |
| 2026-02 | 6,613,871 | +32008 |
| 2026-03 | 6,647,084 | +33214 |
| 2026-04 | 6,696,456 | +49372 |
| 2026-05 | 6,714,008 | +17552 |
| 2026-06 | 6,727,240 | +13232 |
| 2026-07 | 6,737,754 | +10514 |
| 2026-08 | 6,751,407 | +13653 |

Weekly-delta QT pace since the peak (USD B; delta = week-over-week change):

| Period              | Weeks | Mean/wk | Median/wk | Worst wk | Best wk |
|---------------------|-------|---------|-----------|----------|---------|
| 2022 (Apr-)         | 38    | -10.2   | -6.7      | -53.3    | +27.9   |
| 2023                | 52    | -16.1   | -20.3     | -74.7    | +297.0  |
| 2024                | 52    | -15.9   | -11.8     | -52.2    | +5.7    |
| 2025                | 53    | -4.6    | -2.3      | -33.5    | +59.4   |
| 2026 (thru Aug 19)  | 33    | +3.2    | +7.4      | -67.0    | +19.0   |
| Total               | 227   | -9.8    |           |          | cum -2220 |

Readings:

- Cumulative shrink peak-to-trough: -2.43T (-27 pct), weekly trough
  6,535,781MM on 2025-12-03; last obs 6,745,699MM (2026-08-19) and rising.
  Compare the prior cycle: 4.52T peak (2015-01-14) to 3.76T trough
  (2019-08-28), only -0.76T (-17 pct). This QT ran more than three times
  deeper.
- Largest single weeks: -75B (2023-09-20) and -74B (2023-04-05) on the run-
  off side; +297B (2023-03-15) and +94B (2023-03-22) during the SVB stress
  week (discount window/BTFP lending plus mark-ups), which is why 2023 shows
  the widest dispersion.
- QT is over: 2026 YTD the weekly delta averages POSITIVE +3.2B/wk. The
  sequence matches liquidity plumbing: through 2023-2024 RRP runoff absorbed
  QT, so reserves barely fell; once RRP hit zero in late 2025 every QT dollar
  came out of reserves, and the Fed stopped shrinking within weeks (WALCL
  trough 2025-12-03).

RRP lifecycle (RRPONTSYD, overnight reverse repo volume, USD B):

| Year       | Daily mean ($B) | Milestones                                   |
|------------|-----------------|----------------------------------------------|
| 2015       | 112             | modest legacy usage                          |
| 2016       | 104             |                                              |
| 2017       | 145             |                                              |
| 2018       | 12              | drained to near zero                         |
| 2019       | 5               |                                              |
| 2020       | 9               | QE flood                                     |
| 2021       | 722             | first day above 1,000: 2021-07-30            |
| 2022       | 1,996           | first day above 2,000: 2022-05-23            |
| 2023       | 1,747           | ALL-TIME PEAK 2,553.7 on 2022-12-30 (quarter-end print); last day >= 1,000: 2023-11-09 |
| 2024       | 390             | below 500 from 2024-02-15; below 100 from 2024-12-20 |
| 2025       | 103             | below 50 from 2025-08-14                     |
| 2026 (YTD) | 2               | below 10 from 2025-10-02; near zero since (last: 0.2 on 2026-08-21) |

The facility rose from ~0 to 2.55T in about 18 months (bill supply plus the
IORB/on-RRP wedge), then collapsed to zero over the following ~24 months.
Quarter-end spikes along the way (e.g. +77B on 2018-06-29) are genuine but
transient, matching the store caveat. With RRP empty it can no longer buffer
balance-sheet policy: the drain now lands directly on reserves.

WRESBAL drain toward the 2.5-3.0T scarcity floor:

| Year       | Reserves mean ($T) | Notes                                        |
|------------|--------------------|----------------------------------------------|
| 2015       | 2.61               |                                              |
| 2016       | 2.31               |                                              |
| 2017       | 2.25               |                                              |
| 2018       | 1.98               | QT1 runoff                                   |
| 2019       | 1.56               | min 1.39T on 2019-09-18, the repo-crisis level |
| 2020       | 2.65               | QE re-flood                                  |
| 2021       | 3.88               | weekly peak 4.28T on 2021-12-08              |
| 2022       | 3.40               |                                              |
| 2023       | 3.24               | dip to 2.83T on 2023-01-04                   |
| 2024       | 3.37               | reserves ROSE as RRP runoff recycled inward  |
| 2025       | 3.20               | mean drain -2.7B/wk, total -138.6B           |
| 2026 (YTD) | 3.01               | mean -1.9B/wk, total -61.1B thru 2026-08-19  |

Current state: local low 2.85T on 2025-10-29, rebound to ~3.06T in July 2026,
latest 2,935,287MM (2026-08-19). That sits just above the upper bound of the
2.5-3.0T scarcity zone proposed for this cycle - plausible given the balance
sheet and non-reserve liabilities are far larger than 2019, when trouble began
at 1.39T. Corroborating tell: SOFR-FEDFUNDS ran persistently rich in Sep-Dec
2025 (see SOFR & Money Markets below) exactly as reserves crossed ~2.9-3.0T,
and WALCL stopped shrinking in Dec 2025.

## SOFR & Money Markets

Spread = daily SOFR minus the same-month FEDFUNDS monthly average, in bps;
2,080 observations 2018-04-03 through 2026-07-31. Store-wide: mean -0.3,
median -1, stdev 13.4 bps; roughly 73 pct of days sit inside +/-5 bps.
Caveat: pairing a daily rate against a monthly average mechanically inflates
the spread in any month where the Fed moved, so flag clusters around FOMC
months and quarter/year-end turns before calling them stress.

Annual profile:

| Year | Obs | Mean | Median | Min | Max  | Days gt +5bps | Days lt -5bps |
|------|-----|------|--------|-----|------|---------------|---------------|
| 2018 | 187 | +2.4 | +1.0   | -15 | +73  | 26 pct        | 6 pct         |
| 2019 | 250 | +4.3 | +1.0   | -22 | +321 | 22 pct        | 3 pct         |
| 2020 | 251 | -0.8 | 0.0    | -64 | +99  | 4 pct         | 5 pct         |
| 2021 | 250 | -4.1 | -4.0   | -7  | +2   | 0 pct         | 22 pct        |
| 2022 | 249 | -5.1 | -3.0   | -73 | +60  | 16 pct        | 38 pct        |
| 2023 | 249 | -2.2 | -2.0   | -26 | +22  | 5 pct         | 15 pct        |
| 2024 | 250 | +0.2 | -1.0   | -31 | +25  | 14 pct        | 9 pct         |
| 2025 | 249 | +3.0 | +1.0   | -10 | +40  | 27 pct        | 8 pct         |
| 2026 | 145 | -0.0 | 0.0    | -13 | +11  | 7 pct         | 8 pct         |

Flagged spikes beyond +/-5 bps, by episode (dates = store dates):

- 2018-2019 corridor friction, recurring month/quarter-end pops of +5 to
  +34 bps: 2018-04-03..11 (+14 max), 2018-06-05..07-05 (+30), 2018-09-27/28
  (+30), 2018-11-30 (+8), 2019-03-29 (+24), 2019-04-29..05-02 (+34),
  2019-06-28 (+12), 2019-07-31..08-02 (+15). Year-end turn printed +73
  (2018-12-31) and +75 (2019-01-02).
- REPO CRISIS, 2019-09: SOFR 5.25 pct on 2019-09-17 against a 2.04 pct FF
  month-average = +321 bps, the store maximum; still +51 on 09-18 and +39 on
  09-16; the whole 2019-09-03..09-30 window averaged +23. Reserves had
  drained to their cycle low (1.39T, 2019-09-18) - the canonical scarcity
  episode.
- 2020-03 dash-for-cash: +99 (2020-03-03), +94 (2020-03-02), +58 (03-04);
  then the sign flipped, -64 on every day 2020-03-24..03-31 (SOFR pinned at
  0.01 vs the still-high March FF average) once QE flooded bills.
- 2022 QT ramp, persistently NEGATIVE: monthly means -5.4 (May), -11.3
  (Jun), -7.3 (Jul); extreme prints -47 (2022-05-02), -52 (mid-June), -73
  (2022-11-01/02, the store minimum) as FF averages lagged collapsing bill
  yields - then +60/+59 on 2022-07-28/29 at the month/hike turn.
- 2023: mild. March (SVB) topped at +22 within the month; May printed -25
  (05-01..03); July ran +19 max at month-end. Stress stayed inside the
  corridor because the standing facilities held and the FF average lagged.
- 2024 cutting-ramp noise: -31 min in September, +22 (Oct 31) and +25
  (Nov 7) pops, December averaging +5.2 with an -18 intramonth low.
- 2025 H2 - the signal event: four consecutive months averaging +8.0 (Sep),
  +11.1 (Oct), +9.8 (Nov), +8.0 (Dec), max print +40 inside the
  2025-11-21..12-12 episode; since Sep 2025, 28 pct of days ran above +5 -
  the richest sustained run since 2019, coinciding with reserves near
  2.9-3.0T and RRP at zero (see Balance Sheet Deep Dive above).
- 2026 normalization: Jan-Aug averages ~0 with only scattered +6..+9 days
  (2026-02-17/18, 2026-03-02/03, 2026-04-15, 2026-06-15) and shallow
  -10..-13 dips (mid-May, 2026-07-09/10). Latest print: SOFR 3.63
  (2026-08-20) vs the 3.63 FF July average = 0 bps - plumbing calm even as
  reserves hover just above the proposed scarcity floor.

Monitoring rule from this history: single-day prints beyond +20 bps or
multi-week averages beyond +5 bps OUTSIDE FOMC-move months have marked
genuine reserve scarcity (2019-09, 2025 Q4) and preceded balance-sheet
policy responses (bill injection in 2019, QT stop in Dec 2025).

---
