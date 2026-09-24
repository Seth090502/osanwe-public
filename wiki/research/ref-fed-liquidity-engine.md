---
categories:
  - wiki
type: reference
created: 2026-08-24
updated: 2026-08-24
status: active
trigger: "Definitive Fed liquidity / plumbing reference built from the factor store's 19 FRED series (ticker=MACRO): QT, reserves, reverse repo, SOFR funding stress, yen carry, financial conditions, and the net liquidity verdict."
tags:
  - topic/fed
  - topic/liquidity
  - topic/macro
  - topic/rates
aliases:
  - Fed Liquidity Engine
  - Fed Plumbing Reference
---

# FED LIQUIDITY ENGINE -- QT, RESERVES, REPO, AND THE NET-LIQUIDITY VERDICT

> GENERATED: 2026-08-24 by Hermes agent run. Every number below is pulled directly from
> `Efforts/osanwe-v2-overhaul/_work/factors.db`, table `factors`, `ticker='MACRO'`
> (FRED ingests). Each figure cites its factor series name and as-of date. Do not edit
> values by hand -- regenerate from the store. Units: WALCL/WRESBAL/TREAST/RRPONTSYD are
> billions USD (store stores millions for WALCL-family, converted /1000 here); rates are percent.

## 0. ONE-PARAGRAPH ANSWER

The Fed stopped shrinking in December 2025 and has been quietly re-expanding ever since,
while cutting the policy rate from its 5.33 percent peak (FEDFUNDS, as-of 2023-08-01) to
3.63 percent (FEDFUNDS, as-of 2026-07-01). Net liquidity direction: **EASING IN REAL
TERMS** -- price (rate cuts) and quantity (balance sheet regrowth) both point the same way,
financial conditions sit in the loosest ~4th percentile of the past decade (STLFSI4,
as-of 2026-08-14), and funding markets are quiet. The two live risks are (a) the reverse
repo buffer is fully spent, so any future drain hits bank reserves directly, and (b) the
yen carry trade is stretched to historic extremes and a disorderly unwind transmits into
dollar risk assets fast (it did in August 2024).

## 1. BALANCE SHEET RUNOFF (WALCL)

### 1.1 Headline numbers

| Metric | Value | Source |
|---|---|---|
| QT starting level | 8,965.5 B | WALCL, as-of 2022-04-13 (cycle peak) |
| QT trough | 6,535.8 B | WALCL, as-of 2025-12-03 |
| Current level | 6,745.7 B | WALCL, as-of 2026-08-19 |
| Total reduction, peak to trough | -2,429.7 B (-27.1%) | computed from WALCL rows above |
| Net below cycle peak today | -2,219.8 B | WALCL, as-of 2026-08-19 |
| Re-expansion since trough | +209.9 B over ~37 weeks (+5.7 B/wk, ~+24.6 B/mo) | WALCL 2025-12-03 -> 2026-08-19 |

### 1.2 Monthly path (WALCL, mid-month samples, $B)

| Month | Level | Month | Level |
|---|---|---|---|
| 2022-04 | 8,937.6 | 2024-08 | 7,175.3 |
| 2022-08 | 8,874.6 | 2024-12 | 6,895.8 |
| 2022-12 | 8,582.7 | 2025-04 | 6,723.5 |
| 2023-04 | 8,632.4 | 2025-08 | 6,640.8 |
| 2023-08 | 8,206.8 | 2025-12 | 6,535.8 (monthly trough) |
| 2023-12 | 7,737.4 | 2026-01 | 6,573.6 |
| 2024-04 | 7,439.6 | 2026-04 | 6,675.3 |

(All rows WALCL; dates are first mid-month observation <= the 15th of each month.)

### 1.3 Trend analysis

- Runoff ran roughly 44 months (Apr 2022 -> Dec 2025) at an average ~55 B/month, but the
  pace was heavily back-loaded slow: H2-2025 averaged only ~25 B/month before the trough
  printed on the week of 2025-12-03 (WALCL).
- The trough is unambiguous in the store: weekly prints fell from 6,555.3 (WALCL,
  as-of 2025-11-19) to 6,535.8 (as-of 2025-12-03), then rose every month thereafter --
  6,605.9 (2026-02-04), 6,675.3 (2026-04-01), 6,745.7 (2026-08-19). This is a standing
  balance-sheet expansion of about +25 B/month for eight straight months, i.e. organic
  asset growth (bill issuance roll-off, MBS payoffs slowing, other liabilities management),
  not a new announced QE program -- but mechanically it adds reserves.
- TREAST confirms the shape: securities held peaked at 5,771.4 B (TREAST, as-of
  2022-06-08) and stand at 4,542.2 B (TREAST, as-of 2026-08-19), down 1,229.2 B; the gap
  between total assets and Treasuries (other assets incl. loans/spirals) has narrowed.

### 1.4 What level triggers "QT done"?

QT is functionally DONE in this dataset. The operational triggers, ranked:

1. Reserve scarcity floor: bank reserves (WRESBAL) entering the 2,500-3,000 B comfort
   zone -- see section 2. At the 2025-12-03 trough, reserves sampled 2,858.3 B, squarely
   inside the band; the Committee paused there. This is the binding constraint that
   actually stopped QT.
2. Money-market friction: SOFR persistently above the fed funds target midpoint
   (+10 bp rule-of-thumb) and repo trades printing above IORB -- episodes appeared
   repeatedly in Sep-Nov 2025 (section 4) right as reserves dipped toward 2,860 B.
   That friction is the early-warning gauge for the floor.
3. Arithmetic floor: currency in circulation plus the reserve floor plus Treasury
   General Account needs put the practical balance-sheet minimum somewhere near
   6,400-6,600 B given the reserve floor alone is ~2,500-3,000 B. WALCL bottomed at
   6,535.8 B -- consistent with the Fed defending that arithmetic rather than testing it.

Implication for equity risk appetite: the largest mechanical liquidity headwind of
2022-2025 is over and has flipped sign. A flat-to-rising balance sheet removes the
~-50 B/month drag that had to be absorbed by private savings. Mild tailwind.

## 2. RESERVES TRAJECTORY (WRESBAL)

### 2.1 Time series ($B, mid-month samples)

| Date | Reserves | Note |
|---|---|---|
| 2021-12-08 | 4,275.8 | store peak (WRESBAL) |
| 2022-06 | 3,322.0 | early QT |
| 2023-01 | 2,830.1 | first brush with the band (WRESBAL, as-of 2023-01-04: 2,830.1) |
| 2023-06 | 3,349.8 | bank-credit rebound |
| 2024-06 | 3,408.3 | plateau era |
| 2025-03 | 3,312.6 | renewed drain begins |
| 2025-09 | 3,181.7 | |
| 2025-10 | 2,966.1 | enters the band |
| 2025-11 | 2,862.6 | |
| 2025-12 | 2,858.3 | QT-cycle low region |
| 2026-03 | 3,015.5 | re-expansion bounce |
| 2026-06 | 3,013.9 | |
| 2026-07 | 2,966.9 | |
| 2026-08-19 | 2,935.3 | current (WRESBAL) |

### 2.2 Drain-rate math

- From the 2021-12-08 peak (4,275.8 B) to current (2,935.3 B, WRESBAL as-of 2026-08-19):
  -1,340.5 B, about -31.4 percent, over ~56 months ~= -24 B/month average.
- Trailing twelve months: 3,332.5 B (WRESBAL, as-of 2025-08-13 sample) -> 2,993.3 B
  (as-of 2026-08-05) ~= -28 B/month. The drain continues even as total assets grow --
  the wedge between WALCL growth and WRESBAL decline is being absorbed by rising
  currency and TGA-type liabilities.
- Weekly noise is large and calendar-driven: 3,098.9 (2026-07-08) -> 3,142.7
  (2026-07-15) -> 2,984.6 (2026-07-29) is tax/settlement timing, not trend (WRESBAL).
  Judge the level on 4-week averages.

### 2.3 Are we approaching reserves scarcity?

We are INSIDE the commonly cited 2,500-3,000 B scarcity band and holding near its upper
half (2,935.3 B, WRESBAL, as-of 2026-08-19). Read-through:

- The store already recorded the probe of the lower band: 2,858.3 B (mid-Dec 2025) and
  2,830.1 B (Jan 2023) -- each time the system found friction (section 4) and each time
  the trajectory reversed. The floor is real and approximately located: ~2,850 B.
- Distance to the hard-warning zone (2,500 B): about -435 B. At the trailing -28 B/month
  drain rate that is roughly 15 months away IF the Fed holds everything else constant --
  but the observed behavior (QT stop at 2,858 B, balance sheet regrowth) says the
  Committee will defend ~2,850-3,000 B first.
- Scarcity is unevenly distributed: reserves concentrate at large banks; small banks
  feel 2,900 B like big banks feel 2,600 B. Watch the distribution proxies via SOFR
  dispersion rather than the aggregate alone.

Equity risk appetite: reserves at 2.9T are "sufficient but no longer abundant." Neutral
on their own; the option value is that the Fed has demonstrated it stops draining here,
which converts reserve level from a risk into a policy put.

## 3. REVERSE REPO: THE EXHAUSTED SHOCK ABSORBER (RRPONTSYD)

### 3.1 The round trip

| Milestone | Date | Level | Source |
|---|---|---|---|
| Cycle peak | 2022-12-30 | 2,553.7 B | RRPONTSYD |
| Below 2,000 B | 2023-06-15 | | RRPONTSYD |
| Below 1,500 B | 2023-09-12 | | RRPONTSYD |
| Below 1,000 B | 2023-11-09 | | RRPONTSYD |
| Below 500 B | 2024-02-15 | | RRPONTSYD |
| Below 250 B | 2024-09-16 | | RRPONTSYD |
| Below 100 B | 2024-12-20 | | RRPONTSYD |
| Below 50 B | 2025-08-14 | | RRPONTSYD |
| Below 10 B | 2025-10-02 | | RRPONTSYD |
| Effectively zero | 2025-10-07 | <5 B | RRPONTSYD |
| Current | 2026-08-20 | 0.225 B | RRPONTSYD |

### 3.2 What the empty facility means for continued QT

- Mechanism: from Jan 2023 through Oct 2025, nearly all of the 2,550 B that left the RRP
  facility was money-fund cash rotating into T-bills as bill supply exploded. Because
  RRP balances were a parking lot OUTSIDE the banking system, every dollar of QT during
  that window was cushioned: reserves could hold roughly flat while the Fed shrank.
- That shock absorber is now fully consumed (0.225 B, RRPONTSYD, as-of 2026-08-20).
  Any future balance-sheet reduction drains BANK RESERVES one-for-one. There is no
  second cushion between the Fed's ledger and bank liquidity.
- This is precisely why QT terminated when it did: the store shows RRP hitting <10 B
  on 2025-10-02 and reserves then sliding from ~3,180 B (Sep 2025) to 2,858 B (Dec 2025)
  while SOFR frictions flared (section 4). The plumbing told the Fed the buffer was gone;
  the Committee obliged by stopping (WALCL trough 2025-12-03).
- Forward rule of thumb: with RRP at zero, the balance sheet cannot shrink materially
  without breaking something unless reserves are far above the floor. They are not.
  Expect flat-to-growing WALCL for the foreseeable horizon -- which is what the store
  shows since January 2026.

Equity risk appetite: the end of the passive RRP drain removed a hidden +50-100 B/month
liquidity source that quietly fueled risk assets through 2023-2024 (money funds buying
bills released purchasing power). Its exhaustion is why liquidity growth now depends
explicitly on the Fed. Slight negative versus 2024 dynamics, offset by the pivot to
active expansion.

## 4. SOFR DYNAMICS: THE FUNDING STRESS GAUGE (SOFR vs FEDFUNDS)

Spread defined as SOFR minus FEDFUNDS monthly effective rate, daily SOFR observations
matched to their month's FEDFUNDS. Caveat: FEDFUNDS is monthly, so hike-week prints show
artifact spikes until the month averages catch up (e.g., 2022-07-28/29 reads +60/+59 bp,
2022-09-22..27 +42/+43 bp -- those are timing artifacts of the 2022 hiking path, NOT
stress). Structural readings are the ones away from target-change dates.

### 4.1 Stress episodes in the store

| Episode | Dates | Peak spread | Reading | Source |
|---|---|---|---|---|
| Repo crisis | 2019-09-17 | +321 bp | SOFR 5.25 vs FF 2.04 | SOFR, FEDFUNDS |
| Year-end turns | 2018-12-31, 2019-01-02 | +73 to +75 bp | | SOFR, FEDFUNDS |
| COVID dash-for-cash | 2020-03-02/03 | +94 to +99 bp | SOFR 1.64 vs FF 0.65 | SOFR, FEDFUNDS |
| SVB window | 2023-03-27..31 | +16 to +22 bp | | SOFR, FEDFUNDS |
| Pre-cut quarter-end | 2024-09-03..18 | +19 to +25 bp | SOFR up to 5.38 vs FF 5.13 | SOFR, FEDFUNDS |
| Post-cut turn | 2024-11-01..07 | +17 to +22 bp | | SOFR, FEDFUNDS |
| Year-end 2024 | 2024-12-02..17 | +11 to +17 bp | | SOFR, FEDFUNDS |
| Late-QT friction wave | 2025-09..12 | +29 bp (2025-09-15), +25 (2025-11-03), +40 (2025-12-01), +15 (2025-12-31) | cluster of >10 bp days | SOFR, FEDFUNDS |
| 2026 YTD | only 2026-01-02 | +11 bp | then quiet all year | SOFR, FEDFUNDS |

### 4.2 Current state

Last 40 observations (Jun-Jul 2026) oscillate between -10 bp and +6 bp; latest print
+3 bp (SOFR 3.66 vs FEDFUNDS 3.63, as-of 2026-07-31). No sustained >+10 bp day in 2026
outside New Year's Day. The 2025 Q4 friction wave -- the exact period reserves touched
2,858 B and RRP hit zero -- fully resolved after the QT stop and balance-sheet regrowth.

### 4.3 Read-through

- The +10 bp tripwire fired as a CLUSTER in Sep-Dec 2025, correctly signaling late-QT
  strain, and went quiet once WALCL turned up. Gauge validated and currently green.
- Recurring pattern: stress appears at quarter/year-end turns first (Sep 2024, Nov-Dec
  2024, Dec 2025). With the RRP buffer at zero, expect these seasonal bumps to be the
  first place renewed scarcity shows. Next scheduled test: year-end 2026.
- Equity implication: quiet SOFR = dealers can finance inventories cheaply = risk-asset
  bid intact. A fresh cluster of >+10 bp days would be an early de-risking signal that
  historically leads equity vol by weeks, not months.

## 5. YEN CARRY MECHANISM (DEXJPUS)

### 5.1 Where we are

| Metric | Value | Source |
|---|---|---|
| Current USDJPY | 159.21 | DEXJPUS, as-of 2026-08-14 |
| Store high | 163.86 | DEXJPUS, as-of 2026-07-29 |
| Percentile vs 2015+ history | beyond 95th (p95 = 157.58) | DEXJPUS distribution |
| Days >= 158 | 124, spanning 2024-06-20 to 2026-08-14 | DEXJPUS |
| First >= 160 / >= 162 | 2024-06-26 / 2026-06-30 | DEXJPUS |
| Single-day plunge on record recently | 163.86 -> 159.47 on 2026-07-29 -> 07-30 (-4.39) | DEXJPUS |

159 is deep into historically weak-yen territory: the store's median since 2015 is
114.76 (DEXJPUS), so the current level is roughly 39 percent weaker than the decade norm.

### 5.2 Carry mechanics

- Borrow yen at Japan's policy rate (~0.25-0.5 percent), convert to dollars, buy USD
  assets yielding the fed funds 3.63 percent (FEDFUNDS, as-of 2026-07-01) up to 10-year
  Treasuries at 4.69 percent (DGS10, as-of 2026-08-20). Gross carry: ~330-440 bp before
  hedge costs, plus any FX gain if yen keeps sliding. Un-hedged, this is one of the
  widest carry differentials of the modern era.
- The trade is short volatility by construction: profits accrue slowly, losses arrive
  suddenly. Leverage accumulates while the yen grinds weaker (which it did: 155 first
  crossed 2024-04-24, 160 on 2024-06-26, 162 on 2026-06-30 -- DEXJPUS).
- Unwind sequence (documented live in the store, Aug 2024): BOJ hawkish surprise or MoF
  intervention flips the FX move; leveraged books get margin-called simultaneously.
  JPY ripped from 161.73 (2024-07-10) to 156.56 (2024-07-17); three weeks later VIX
  printed 38.57 (VIXCLS, as-of 2024-08-05) from 18.59 (as-of 2024-08-01). Forced selling
  of USD equities/carry assets, dollar funding squeeze, cross-asset deleveraging.
- The July 2026 one-day 4.39-yen drop (163.86 -> 159.47, DEXJPUS) is intervention-class
  price action and a warning that authorities are again uncomfortable at these levels.
  The higher the yen goes from here, the more compressed the carry and the larger the
  unwound base.

### 5.3 What happens on a full unwind

1. Yen rallies sharply (short squeeze) -> carry goes negative for holders.
2. Margin calls force sales of the highest-momentum USD assets (equities, credit,
   crypto-adjacent) -- not because they are impaired but because they are liquid.
3. Dollar funding tightens (foreign borrowers scramble for USD), visible in SOFR basis
   and, in extremis, in the SOFR-FEDFUNDS spread of section 4 spiking.
4. Vol rises, dealers widen, liquidity multipliers amplify -- a plumbing event becomes
   an equity event. Scale reference: the Aug 2024 mini-unwind took VIX from ~14 to ~39
   (VIXCLS, Aug 2024) in four sessions and fully mean-reverted within weeks because the
   Fed had ample liquidity to absorb it. With RRP at zero today the absorption capacity
   is thinner, so the same trigger would likely bite harder.

Equity risk appetite: latent tail risk, not a current headwind. Size positions knowing
that the carry-unwind scenario correlates ALL risk assets at once, precisely when
correlations go to 1.

## 6. FINANCIAL CONDITIONS (STLFSI4)

### 6.1 Level and thresholds

| Metric | Value | Source |
|---|---|---|
| Current | -0.8285 | STLFSI4, as-of 2026-08-14 |
| Store mean (2015+) | -0.266 | STLFSI4 |
| Std dev | 0.596 | STLFSI4 |
| Mean + 1 sd threshold | +0.33 | computed |
| Mean + 2 sd threshold | +0.93 | computed |
| Percentile of current reading | 3.8th | STLFSI4 rank |
| Stress records | +5.6565 (COVID, as-of 2020-03-20); +1.1197 (SVB, as-of 2023-03-17) | STLFSI4 |

### 6.2 Path

Monthly samples: -0.80 (2025-06), -0.42/-0.49 (Oct-Nov 2025 -- the late-QT friction),
then steady easing through 2026: -0.56 (2026-01), -0.23 (2026-04), -0.83 (2026-06),
-0.77 (2026-08) -- all STLFSI4. Corroborating tape: VIX 16.01 (VIXCLS, as-of
2026-08-20; 2026 range 14.25-31.05), HY OAS 2.75 percent (BAMLH0A0HYM2, as-of
2026-08-20; near the store's tights, 2026 range 2.63-3.46), HY expected default 7.09
percent (BAMLH0A0HYM2EY, as-of 2026-08-20).

### 6.3 Interpretation

Conditions sit in the loosest ~4 percent of weekly readings since 2015 -- easier than
at ANY point of the 2022-2025 tightening cycle and approaching the easy-regime floors
of 2017/2021. Distance to the mean+1sd stress threshold (+0.33) is ~1.16 points: there
is enormous room for conditions to deteriorate before they would even read "average."
For allocation purposes this is a contrarian caution as much as a green light: the
cushion is thin precisely because everyone is comfortable. Complacency-priced markets
gap on the yen-carry and year-end-repo scenarios above.

## 7. SYNTHESIS: THE ACTUAL LIQUIDITY DIRECTION

Scoreboard across the five plumbing dimensions:

| Dimension | Direction | Evidence |
|---|---|---|
| Price (policy rate) | EASING | FEDFUNDS 5.33 (2023-08-01) -> 3.63 (2026-07-01): -170 bp of cuts |
| Quantity (balance sheet) | EASING (since Dec 2025) | WALCL trough 6,535.8 (2025-12-03) -> 6,745.7 (2026-08-19): +209.9 B |
| Reserves | NEUTRAL-EASING | WRESBAL stabilized 2,858-3,143 B band since Oct 2025; 2,935.3 current (2026-08-19) |
| Funding plumbing | EASING | SOFR-FF +40 bp peak friction (2025-12-01) resolved to +3 bp (2026-07-31); zero 2026 clusters |
| Financial conditions | EASY | STLFSI4 -0.8285, 3.8th percentile (2026-08-14); VIX 16, HY 2.75 |
| Tail risks | PRESENT | RRP exhausted (0.225 B, 2026-08-20); yen at 95th+ percentile extreme (159.21, 2026-08-14) |

VERDICT: **THE FED IS EASING IN REAL TERMS.** The tightening cycle is fully over on both
axes -- rates cut 170 bp from peak, QT terminated at the December 2025 trough, and the
balance sheet has re-expanded ~25 B/month for eight consecutive months. Net liquidity
(quantity adjusted for the RRP drain, which is now complete) flipped from contraction
to expansion around October-December 2025: before that date, falling RRP masked QT;
after it, flat-to-rising WALCL flows straight into reserves and bill holders. Real
(short-rate minus inflation-proxy) restraint is also fading: 10y breakevens at 2.34
percent (T5YIE, as-of 2026-08-21) against a 3.63 percent funds rate leaves a modestly
restrictive but rapidly shrinking real stance, and the 10y real yield of 2.35 percent
(DFII10, as-of 2026-08-20) is the one price signal still arguably tight.

EQUITY RISK APPETITE IMPLICATION: the macro liquidity backdrop is supportive -- a
policy regime biased toward adding reserves, quiet funding markets, and record-easy
financial conditions argues for pro-risk positioning NOW. The honest caveats are (1)
much ease is already priced (HY at 2.75 percent OAS leaves little compensation for
default risk), (2) the shock absorbers that muted the last two shocks (RRP buffer,
abundant reserves) are spent, and (3) the yen carry complex is the most stretched it
has been in the store's memory -- the plausible origin of the next liquidity air pocket.

## 8. MONITORING PLAYBOOK (TRIPWIRES AND RESPONSES)

| Tripwire | Threshold | Meaning if tripped | Action bias |
|---|---|---|---|
| WRESBAL | < 2,800 B sustained (4-wk avg) | reserves leaving the defended band | reduce leverage, expect Fed tool talk (SRP/standing repo usage) |
| SOFR-FEDFUNDS | > +10 bp for 3+ consecutive sessions off quarter-end | structural, not seasonal, scarcity | de-risk into strength |
| RRPONTSYD | re-inflating > 100 B | bill supply/demand dislocation, not bullish | investigate before assuming liquidity add |
| DEXJPUS | fast rally > 3 yen in <= 5 sessions from > 158 | carry unwind in motion | cut correlated risk FAST; vol hedges over delta hedges |
| STLFSI4 | crossing 0 then +0.33 | conditions normalizing then stressing | raise cash buffer systematically |
| WALCL | renewed weekly declines > 30 B for 3+ weeks | resumption of drain | fade risk appetite until reversed |

## 9. SERIES INVENTORY AND METHOD NOTES

Factor store: `Efforts/osanwe-v2-overhaul/_work/factors.db`, table `factors`,
`ticker='MACRO'` -- 32,736 rows across 19 FRED series. Coverage used here:

| Series | Rows | Range | Role in this note |
|---|---|---|---|
| WALCL | 607 | 2015-01-07 .. 2026-08-19 | balance sheet |
| WRESBAL | 607 | 2015-01-07 .. 2026-08-19 | reserves |
| RRPONTSYD | 2,901 | 2015-01-02 .. 2026-08-21 | reverse repo |
| SOFR | 2,094 | 2018-04-03 .. 2026-08-20 | funding rate |
| FEDFUNDS | 139 | 2015-01-01 .. 2026-07-01 | policy rate (monthly) |
| DEXJPUS | 2,904 | 2015-01-02 .. 2026-08-14 | yen carry leg |
| STLFSI4 | 607 | 2015-01-02 .. 2026-08-14 | financial conditions |
| TREAST | 607 | 2015-01-07 .. 2026-08-19 | securities held |
| DGS10 / DGS30 | 2,910 ea | .. 2026-08-20 | yield anchors (4.69 / 5.23) |
| DFII10 | 2,910 | .. 2026-08-20 | 10y real yield (2.35) |
| T5YIE | 2,911 | .. 2026-08-21 | breakeven inflation (2.34) |
| T10Y2Y / T10Y3M | 2,911 ea | .. 2026-08-21 | curve (+0.50 / +0.86) |
| VIXCLS | 2,957 | .. 2026-08-20 | vol (16.01) |
| BAMLH0A0HYM2(EY) | 787 ea | .. 2026-08-20 | credit spreads (2.75 / 7.09) |
| UNRATE / CPIAUCSL | 138 ea | .. 2026-07-01 | macro backdrop (4.1 / 332.813) |

Method notes: (1) monthly tables sample the first weekly/daily observation on or before
the 15th; (2) SOFR-FEDFUNDS spreads pair daily SOFR to the contemporaneous monthly
FEDFUNDS, which smears hike dates -- flagged where relevant; (3) billions conversion
divides stored millions by 1,000; (4) percentile ranks are against the full in-store
history of each series, not official FRED full-history percentiles; (5) "GENERATED"
means regenerate from the store rather than hand-editing values.

*End of generated reference.*
