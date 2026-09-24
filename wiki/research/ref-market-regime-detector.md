---
categories: [wiki]
type: reference
status: active
created: 2026-08-24
updated: 2026-08-24
confidence: medium
tags:
  - topic/investing
  - topic/macro
  - topic/scoring
related: ["[[ref-fed-liquidity-engine]]", "ref-scenario-stress-test", "ref-factor-lens-ingest-2026-06-10", "ref-yen-carry-global-liquidity", "[[ref-composite-scoring]]"]
---

# Market Regime Detector -- factor-store derived (GENERATED)

GENERATED: 2026-08-24, computed offline entirely from
`Efforts/osanwe-v2-overhaul/_work/factors.db` (tables: `bars`, `factors`).
No network sources used. REGENERATE by re-running the documented arithmetic;
engine script kept outside the vault at `~/regime_work/regime_final.py`.

## 1. Data basis

- Bars: 107 instruments, 2021-08-24 .. 2026-08-24 (1255 sessions each for
  legacy tickers). Classified window: 2022-06-08 .. 2026-08-24 (1056 sessions;
  first 200 consumed by the SPY MA200 warmup).
- Macro series joined as-of (ffill) onto the SPY calendar: ^VIX, DGS10,
  BAMLH0A0HYM2 (HY OAS), SOFR, STLFSI4, WRESBAL, WALCL, ^SKEW, ^VVIX.
- UNIT NOTES (bit me twice): HY OAS is stored in PERCENT (multiply by 100 for
  bp thresholds); WRESBAL/WALCL are stored in $MILLIONS (divide by 1000 for
  $B). HY OAS begins 2023-08-22 -- before that the BEAR credit gate is waived
  and classification uses price/vol structure only.

## 2. Definitions (as implemented)

Priority order top to bottom; first match wins. Fallback assigns a neutral
state so every session is labeled.

| # | State | Rule |
|---|-------|------|
| 1 | LIQUIDITY-CRISIS | STLFSI4 > 0 AND SOFR stress AND reserves drain |
| 2 | BEAR | SPY < MA200 AND VIX > 28 AND HY OAS > 450bp (credit gate waived pre-2023-08) |
| 3 | RECOVERY | MA50 reclaimed from below within last 10 sessions AND rv21/rv63 < 1.0 AND VIX < 30 |
| 4 | CORRECTION | MA50 < SPY < MA200-equivalent (below MA50, above MA200) AND VIX 20-32 |
| 5 | BULL-EXPANSION | SPY > MA200 AND DGS10 21d change < -5bp AND VIX < 18 AND HY OAS < 300bp |
| 6 | BULL-LATE | SPY > MA200 AND DGS10 21d change > +5bp AND VIX <= 24 |

Derived indicators: SOFR stress = trailing-252d z-score > 1.5 OR 5-day jump
> 15bp; reserves drain = WRESBAL 25-session change < -$50B; rv_ratio =
21d/63d realized vol ratio (vol contracting when < 1).

Spec-gap handling: below-MA200 days that fail the BEAR vol/credit gates
default to CORRECTION (208 such days in window: 146 with VIX 20-28,
12 with VIX < 20, 50 with VIX > 28). Above-MAs days with flat rates
(-5..+5bp) fall back to BULL-LATE (neutral bull).

## 3. REGIME DASHBOARD -- current state (2026-08-24)

```
=====================================================================
 REGIME DASHBOARD              source: factors.db @ 2026-08-24
=====================================================================
 CURRENT STATE: BULL-LATE       run: 7 sessions (62nd pctile of hist)
 persistence: 92.4%/day stays put (historical base rate)
---------------------------------------------------------------------
 SPY 764.96   +1.70% vs MA50 (752.14)   +8.43% vs MA200 (705.46)
 VIX 15.85    RV21/RV63 0.94 (contracting)   SKEW 145.6  VVIX 88.6
 DGS10 4.69%  21d change 0.0bp (flat)        HY OAS 275bp
 SOFR 3.63 (z -0.65, calm)   STLFSI4 -0.83 (risk-off=none)
 RESERVES 2935B  25d change -207B  <-- DRAIN LEG ALREADY LIT
 BALANCE SHEET 6746B
---------------------------------------------------------------------
 CONDITION SCORES (fraction of defining checks met):
   BULL-EXPANSION    75%  <- blocked ONLY by rates leg (need <= -5bp)
   BULL-LATE         67%  <-- ASSIGNED
   RECOVERY          67%     (reclaim trigger stale, vol still contracting)
   LIQUIDITY-CRISIS  33%     (reserves leg live, other two quiet)
   CORRECTION         0%     BEAR             0%
=====================================================================
```

Confidence reading: BULL-LATE at moderate conviction. The market sits one
5bp move in 10y yields away from upgrading to BULL-EXPANSION, with equity
trend and credit both firmly bullish; the only live stress signal is the
Fed reserves drain, which has not (yet) infected money markets (SOFR z
-0.65, STLFSI4 deeply negative).

## 4. Historical profile per regime (window: 1056 sessions)

Frequency and duration (trading days; runs of consecutive same-label days):

| State | Days | % of time | Episodes | Mean len | Median | Max |
|---|---|---|---|---|---|---|
| BULL-LATE | 622 | 58.9% | 48 | 13.0 | 3 | 180 |
| CORRECTION | 221 | 20.9% | 36 | 6.1 | 3 | 30 |
| BULL-EXPANSION | 81 | 7.7% | 19 | 4.3 | 1 | 19 |
| RECOVERY | 80 | 7.6% | 20 | 4.0 | 2.5 | 10 |
| LIQUIDITY-CRISIS | 41 | 3.9% | 4 | 10.2 | 9.5 | 20 |
| BEAR | 11 | 1.0% | 3 | 3.7 | 3 | 6 |

Median << mean everywhere: labels flicker at thresholds (chatter), while
persistent stretches carry the means/maxes. Read durations as
"durable stretches exist but boundaries are noisy".

Mean indicator posture while in each state:

| State | VIX | HY OAS bp | DGS10 21d bp | dist MA50 % | dist MA200 % | rv_ratio | SOFR z |
|---|---|---|---|---|---|---|---|
| BULL-EXPANSION | 15.7 | 279 | -14.4 | +3.1 | +9.5 | 0.94 | -1.16 |
| BULL-LATE | 16.2 | 315 | +5.7 | +2.9 | +8.8 | 0.93 | -0.24 |
| RECOVERY | 18.3 | 293 | -1.6 | +2.2 | +4.5 | 0.84 | -0.34 |
| CORRECTION | 23.5 | 343 | -0.5 | -1.2 | -0.9 | 1.09 | +0.35 |
| LIQUIDITY-CRISIS | 28.6 | n/a | +30.3 | -5.2 | -11.3 | 1.06 | +2.74 |
| BEAR | 34.4 | 459 | +35.4 | -8.2 | -12.5 | 1.19 | +2.10 |

Exit-day fingerprints (last day of each run -- what the handoff looks like):

- BULL-EXPANSION exits: rates impulse already decayed (-10.2bp avg) and SOFR
  z very negative (-1.38): expansions die when the rates tailwind stops, not
  on a vol shock.
- BULL-LATE exits: VIX drifting up (17.6) and rv_ratio at 0.99: vol pickup,
  not level, ends the neutral bull.
- CORRECTION exits happen right at the MA50 (dist -0.75%) with VIX ~21.7:
  the reclaim IS the exit.
- RECOVERY exits hand off with rates rising again (+7.1bp): recovery matures
  into rising-rate bull, or fails back.
- LIQUIDITY-CRISIS exits while stress is still elevated (SOFR z +2.36,
  VIX 25.5): the label clears on component decay, not on calm.
- BEAR exits at peak stress (VIX 37, SOFR z 1.7): capitulation marks the end.

Next-day transition matrix (row = from, %):

| From \ To | BEAR | BULL-EXP | BULL-LATE | CORR | LIQ-CRISIS | RECOV |
|---|---|---|---|---|---|---|
| BEAR | 72.7 | 0 | 0 | 18.2 | 9.1 | 0 |
| BULL-EXPANSION | 0 | 76.5 | 22.2 | 0 | 0 | 1.2 |
| BULL-LATE | 0 | 2.9 | 92.4 | 3.7 | 0 | 1.0 |
| CORRECTION | 0.9 | 0.4 | 8.1 | 83.7 | 1.4 | 5.4 |
| LIQUIDITY-CRISIS | 2.4 | 0 | 0 | 4.9 | 90.2 | 2.4 |
| RECOVERY | 0 | 0 | 15.0 | 10.0 | 0 | 75.0 |

Key asymmetries: corrections resolve UP far more often than down
(8.1+0.4=8.5% to bulls vs 0.9% to BEAR); RECOVERY is a real waystation
(15% converts to BULL-LATE next day); BEAR and LIQUIDITY-CRISIS interconvert
(9.1% and 2.4% cross-links) and never transition directly to BULL states --
the tape must first pass through CORRECTION.

## 5. Typical performance by regime (forward 21d returns, %)

Universe = the 107 instruments in the store (semis, AI infra, power, defense,
crypto rails -- NOT GICS sectors). Overlapping-window averages; small-n rows
are indicative only. breadth = % of ticker-days positive.

### BULL-EXPANSION (n=81 fwd obs | universe +0.47% | breadth 47% | SPY -0.17%)

Paradox row: falling rates coincide with de-risking, not melt-up. Leaders
are memory/storage value names, laggards are the crowded AI complex.

- TOP: SNDK +33.2, BE +15.0, USAR +11.3, WBD +10.9, FLNC +8.9, MRAM +8.7,
  INTC +7.4, WDC +7.3, MU +7.3, LITE +5.8
- BOTTOM: SPCX -21.0, ALGO-USD -8.1, SMR -7.8, ONDO-USD -7.3, SNPS -7.0,
  VST -5.9, XLM-USD -5.1, QNT-USD -4.7, LINK-USD -4.5, BAH -4.4

### BULL-LATE (n=622 | universe +2.66% | breadth 51% | SPY +1.06%)

The workhorse regime. High-beta AI/networking leads; defensives dead money.

- TOP: SNDK +17.7, NBIS +11.9, AAOI +11.8, ONDO-USD +9.2, XLM-USD +7.8,
  PLTR +6.8, CRDO +6.7, SMCI +6.4, HBAR-USD +6.3, ALAB +6.2
- BOTTOM: MBLY -2.6, GFS -0.8, QNT-USD -0.3, BAH -0.1, HII +0.1, CRWV +0.1,
  LHX +0.2, LMT +0.2, NEE +0.3

### CORRECTION (n=221 | universe +3.17% | breadth 50% | SPY +0.97%)

Corrections in this window were BUYABLE dips: forward returns above trend,
led by beaten-down high beta. Utilities/defense lag even here.

- TOP: CRWV +28.7, AAOI +15.4, NBIS +13.4, ALAB +11.8, GEV +11.2,
  HIMS +10.7, CRDO +7.5, ARM +7.1, SNDK +6.3, AMKR +5.7
- BOTTOM: ONDO-USD -1.5, MP -1.0, HBAR-USD -0.6, LMT -0.5, NOC -0.5,
  DUK -0.3, LHX -0.3, KTOS -0.1, NEE -0.1, AEP -0.0

### BEAR (n=11 | universe +7.34% | breadth 59% | SPY +5.36%)

Tiny sample (3 short episodes, all followed by sharp rebounds captured in
the 21d window) -- do NOT read as "bears are bullish". Pattern: power/nuclear
and selected AI absorb flows while crypto and long-duration AI losers bleed.

- TOP: USAR +44.9, HIMS +30.5, ONDO-USD +30.0, GEV +29.5, ARM +28.3,
  ALAB +21.0, PLTR +20.8, TLN +16.9, NBIS +16.7, BE +14.7
- BOTTOM: AAOI -9.9, CRWV -8.8, HBAR-USD -4.8, LITE -2.9, ASMIY -2.1,
  BTC-USD -1.8, VDE -1.8, WBD -1.6, XLM-USD -1.5, META -0.6

### LIQUIDITY-CRISIS (n=41 | universe +5.47% | breadth 61% | SPY +3.57%)

Four episodes (2022-06, 2022-09, 2022-12, 2023-03 SVB). Positive forwards
reflect post-panic rebounds inside the 21d window, plus 2022's
rates-shock-not-credit-collapse character. Intra-crisis leaders: compute
hardware and crypto-beta; losers: mega-cap tech and duration proxies.

- TOP: QNT-USD +32.7, SMCI +21.3, VRT +21.2, CRDO +15.5, AMKR +15.4,
  RKLB +13.7, FLNC +12.2, GFS +11.3, ASML +11.2, SMR +10.7
- BOTTOM: META -7.2, MBLY -2.8, GOOGL -1.8, NOW -0.9, COHR -0.8,
  XLM-USD -0.6, TSM -0.6, IAU -0.3, SO +0.3, DUK +0.3

### RECOVERY (n=80 | universe +4.20% | breadth 54% | SPY +1.30%)

Best risk-adjusted window in the store: the highest-quality leaders emerge
here. Memory and AI infra re-rate hardest; crypto rails lag.

- TOP: SNDK +28.7, CRWV +27.1, SPCX +20.0, AAOI +11.5, OKLO +10.5,
  NBIS +10.4, SMCI +10.1, BE +9.7, LITE +9.5, KTOS +9.1
- BOTTOM: ONDO-USD -6.8, XLM-USD -2.7, ALGO-USD -2.0, FLNC -1.6,
  SOL-USD -1.5, QCOM -1.2, XRP-USD -1.1, NOW -0.4, LINK-USD -0.0, BAH -0.0

Cross-regime constants: SNDK (memory) ranks top-3 in four of six regimes;
NBIS/AAOI/ALAB/GEV-type AI-power beta leads every risk-on or bounce state;
defense (LMT/NOC/LHX/GD/BAH) and utilities (NEE/DUK/SO/AEP) anchor the
bottom in ALL six regimes -- this universe offers no internal defensive
rotation, so de-risking must leave the universe (cash/bonds) rather than
rotate within it. META shows up at the bottom in exactly the two stress
regimes (BEAR, LIQ-CRISIS).

## 6. Transition watch table (live margins, 2026-08-24)

```
+------------------------------------------------------------------+
| WATCH                          TRIGGER               NOW   DIST  |
+------------------------------------------------------------------+
| BULL-LATE -> BULL-EXPANSION    DGS10 21d <= -5bp    +0.0bp  5bp  |
|   (VIX<18 ok: 15.9 | HY<300 ok: 275 -- rates is the only gate)   |
| BULL-LATE -> CORRECTION        SPY<MA50 AND VIX>=20  +1.7%  1.7% |
|                                       second leg   15.9  4.2pts|
| ANY -> LIQUIDITY-CRISIS        STLFSI4>0 + SOFR z>   -0.83  0.83 |
|   1.5/jump>15bp + drain<-50B/25d   drain leg LIVE: -207B/25d     |
| BULL -> BEAR                   SPY<MA200 + VIX>28 +  +8.4%  8.4% |
|   HY OAS>450bp                 three-leg AND:      15.9 12.2pts  |
|                                                    275bp  175bp  |
| CORRECTION -> RECOVERY         MA50 reclaim w/        n/a  watch |
|                                rv_ratio<1.0 (5.4%/day base rate)   |
| CORRECTION -> BEAR             rare: 0.9%/day; corr max life 30d  |
+------------------------------------------------------------------+
```

What to monitor, in order of information value:

1. DGS10 21-day momentum crossing +/-5bp -- the single switch between the
   two bull states (currently dead flat at 0.0bp).
2. Distance to MA50 (+1.7% cushion) jointly with VIX >= 20 -- the correction
   gate needs BOTH; VIX at 15.9 gives 4.2 points of slack.
3. Reserves drain (ACTIVE: -$207B/25d) meeting ANY uptick in STLFSI4 toward
   0 (now -0.83) or a SOFR spike (z -0.65 now; stress line z>+1.5 or +15bp
   in 5 sessions). Historical note: all four prior LIQ-CRISIS episodes
   started from STLFSI4 crossings, and 90.2% of LC days persist -- it does
   not clear in a day once lit.
4. SKEW 145.6 with VVIX 88.6: tail-hedging demand elevated while realized
   vol contracts -- consistent with late-cycle complacency on the surface,
   hedged underneath.
5. If a correction starts, expect resolution up (historically 8.5%/day to
   bull states vs 0.9% to BEAR) and watch for the MA50-reclaim +
   rv_ratio<1.0 pair that defines RECOVERY entries.

## 7. Caveats

- Overlapping 21d forward windows; observations are not independent.
- BEAR/LIQ-CRISIS samples are tiny (11 / 41 labeled days); their sector
  tables are anecdote, not statistic.
- Regime labels flicker at thresholds (median run 3d vs mean 13d); smooth
  with a k-of-n majority filter before using for execution.
- HY OAS coverage starts 2023-08; earlier stress classifications lean on
  price/vol only.
- Universe bias: 107 instruments skewed to semis/AI/power/crypto; "sector"
  conclusions do not generalize to broad markets.
- All values recomputable from factors.db; re-run after each weekly
  ingest-bars pass to refresh.
---

## APPENDIX A -- Independent verification pass (2026-08-24, second writer)

This appendix was produced by an independent verification subagent that
re-ran the regime arithmetic from factors.db with a DIFFERENT rule
parameterization (MA50/MA200 trend structure + VIX level + HY-OAS credit
gate + drawdown depth; 200-session warmup; <5-session runs merged into the
predecessor state to kill threshold chatter). Its purpose is triangulation:
where both parameterizations agree, treat the label as robust; where they
disagree, treat the boundary as genuinely ambiguous. The primary engine
remains sections 1-7 above; nothing in those sections was altered.

### A1. Alternative parameterization results (1055 classified sessions)

| State | Days | % of window | Episodes | Mean len | Max len |
|---|---|---|---|---|---|
| BULL-EXPANSION | 644 | 61.0% | 13 | 50 | 100 |
| CORRECTION | 157 | 14.9% | 12 | 13 | 38 |
| BEAR | 131 | 12.4% | 4 | 33 | 103 |
| LIQUIDITY-CRISIS | 51 | 4.8% | 2 | 26 | 38 |
| RECOVERY | 61 | 5.8% | 2 | 30 | 39 |
| BULL-LATE | 12 | 1.1% | 2 | 6 | 7 |

Reconciliation with section 4: both engines agree the window is bull-
dominated and that CORRECTION is the second-largest state. They disagree on
the BULL-LATE / BULL-EXPANSION split (the alt rule keys bull subtype off the
50/200 golden-cross + VIX 20 line rather than DGS10 21d momentum, which
relabels most of the primary engine's BULL-LATE as BULL-EXPANSION) and on
BEAR mass (the alt rule holds the bear label through the full 2022-H2 grind,
103 consecutive days ending 2023-01-25, where the primary engine's credit/
vol gates chop it into shorter segments). Both agree LIQUIDITY-CRISIS is a
small, violent minority state.

### A2. Episode spine (alt engine, runs >= 8 sessions)

```
CORRECTION         2022-06-08 .. 2022-07-07   (20d)
BEAR               2022-07-08 .. 2022-07-27   (14d)
RECOVERY           2022-07-28 .. 2022-08-26   (22d)
BEAR               2022-08-29 .. 2023-01-25   (103d)  <- the 2022 grind
BULL-EXPANSION     2023-01-26 .. 2023-02-23   (20d)
LIQUIDITY-CRISIS   2023-09-26 .. 2023-11-16   (38d)
BULL-EXPANSION     2023-11-17 .. 2024-04-12   (100d)
CORRECTION         2024-04-15 .. 2024-05-02   (14d)
BULL-EXPANSION     2024-05-03 .. 2024-08-05   (64d)   ends at yen crash #26
LIQUIDITY-CRISIS   2025-04-03 .. 2025-04-22   (13d)   tariff shock
RECOVERY           2025-05-01* .. 2025-06-26  (39d)
BULL-EXPANSION     2025-06-27 .. 2025-11-14   (99d)
CORRECTION         2026-02-12 .. 2026-04-08   (38d)
BULL-EXPANSION     2026-04-09 .. 2026-07-22   (72d)
BULL-EXPANSION     2026-07-31 .. open         current run
(*overlap of one session at the LC/RECOVERY handoff -- label boundary.)
```

Cross-checks that strengthen confidence:

- Both engines date the ONLY true 2022-era BEAR identically (Jul-2022 ->
  Jan-2023 complex) and both put the 2023 SVB stress and 2025-04 tariff
  shock in LIQUIDITY-CRISIS.
- Both engines have the tape in a BULL state continuously since late April
  2026, interrupted only by the Feb-2026 correction, with the current run
  opening 17+ sessions ago.
- Regime-boundary dates land within days of the section 4/6 transition
  table for every episode longer than two weeks.

### A3. Segment-level performance cross-check (episode start->end returns)

Where section 5 measures forward-21d overlapping windows per labeled day,
this pass measured each segment start-to-end directly (first-to-last close
of the run). Directional agreement is high; magnitudes differ by design:

| Regime | Alt-engine leaders (segment returns) | vs section 5 |
|---|---|---|
| BULL-EXPANSION | AAOI +71.6%, BE +44.7%, SMCI +39.8%, MU +26.8% avg/run | SNDK/MU family also top-decile there |
| RECOVERY | AAOI +69.3%, SMR +63.1%, OKLO +56.2%, FLNC +50.8% | same high-beta recovery cohort |
| LIQUIDITY-CRISIS | SOL-USD +115.6%, LINK-USD +49.2%, PLTR +27.0%, BTC-USD +25.2% | crypto-beta leads confirmed; note these are the two 2025-26 episodes only |
| CORRECTION | AAOI +7.2%, LITE +5.3%, FN +4.6% | corrections were buyable dips in both readings |
| BEAR | QNT-USD +18.2%, AMKR +15.7%, ASML +14.3% | small-n caveat applies doubly here |
| BULL-LATE | PLTR +13.1%, HIMS +12.8% (only 2 short runs) | n too small to rank |

Structural finding reproduced independently: defense/utilities anchor the
bottom across risk-on states while crypto/AI beta tops them -- the
universe offers no internal defensive rotation (section 5 "cross-regime
constants"), so de-risking still must leave the universe.

### A4. Verification dashboard delta (as-of 2026-08-24 close inputs)

Inputs recomputed this pass: SPY 764.96 (+1.7% vs MA50 752.14, +8.4% vs
MA200 705.46); 200dma slope over 20 bars +9.65 points (rising); drawdown
from 252d high -1.7%; DGS10 4.69 (99th pctl all-store); VIXCLS 16.01 (44th
pctl; trailing-year range 13.47-31.05); HY OAS 2.75 (17th pctl;
trailing-year range 2.63-3.46). Under THIS parameterization the label is
BULL-EXPANSION (above both MAs, golden cross intact, vol mid-band, credit
calm); under the primary rates-momentum rule it is BULL-LATE (rates flat
at 0.0bp/21d blocks the upgrade). Either way: no stress gate is within
firing distance except the reserves-drain leg already flagged in the
section 3 dashboard.

Verdict: the section 3 REGIME DASHBOARD's condition scores survive
triangulation; the single live ambiguity is the bull-subtype boundary,
which is a definitional choice (rates-momentum vs trend-structure), not a
data question. Monitor the section 6 watch table for the tiebreakers.

### A5. Regeneration

Alt-engine recipe (kept out-of-vault like the primary): SPY closes from
bars; MA50/MA200; 200dma falling = slope negative over 20 sessions; dd =
close / running 252d max - 1; macro joined as-of with 10-calendar-day
staleness guard. Priority: LIQUIDITY-CRISIS if HY OAS >= 4.0 or (VIX >= 30
and HY >= 3.0); BEAR if 200dma falling and dd <= -15%; CORRECTION if below
MA50 and dd <= -10% (or below MA50 with dd > -10% as fallback); RECOVERY
if above MA50 without golden cross; else bull (subtype by VIX 20 line).
Merge any run < 5 sessions into its predecessor, iterate to stability.
