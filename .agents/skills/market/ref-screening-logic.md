# ref-screening-logic -- /screen formulas and worked examples

Normative companion to `/screen` SKILL.md. Every formula here matches an
existing corpus engine so screen output stays comparable with the docs the
vault already publishes:

- RSI/MA/returns math == `tools/technicals.py` (Wilder RSI, simple MAs,
  trading-day offsets)
- Composite components == `wiki/research/ref-composite-scoring.md` Method
  section (GENERATED doc)
- Signal definitions == `Atlas/sources/investing/ref-quantitative-signals-library.md`
  Conventions section
- XBRL aggregation rules == `wiki/research/ref-financial-statements.md` header

If one of those sources changes its math, change this file in the same commit.

## 1. Data access

```bash
# READ-ONLY open; never write to factors.db from a screen run
python - <<'EOF'
import sqlite3
con = sqlite3.connect("file:Efforts/osanwe-v2-overhaul/_work/factors.db?mode=ro", uri=True)
rows = con.execute("SELECT ticker, date, close FROM bars WHERE ticker=? ORDER BY date", ("MU",)).fetchall()
EOF
```

- `bars(ticker TEXT, date TEXT, close REAL, src TEXT)` -- daily closes,
  ~130k rows, 107 tickers, 2021-08..2026-08. As-of = MAX(date) actually used.
- Macro series live in `factors(ticker='MACRO', factor='<FRED-ID>')`; not used
  by any current mode but available for future regime gates.
- Signals convenience snapshot: `Efforts/osanwe-v2-overhaul/_work/signals-library-data.json`
  (`signals[ticker]`: r1m/r3m/r6m/r12m, ma50/ma200, ma_state, rsi14, vol20,
  vol60, vol_ratio, vol_pctile_own, beta60, corr60, z200, streak). When its
  `meta.asof` lags the db, recompute from bars instead.
- Fundamentals: `wiki/investing/filings/<T>/<T>-xbrl.json` (list of records:
  concept, period, fy, fp, form, value, filed) and `-xbrl-extended.json`
  (dict: concepts{OperatingIncomeLoss, GrossProfit, StockholdersEquity,
  NetCashProvidedByUsedInOperatingActivities, PaymentsToAcquirePropertyPlantAndEquipment,
  ShareIssued}, FreeCashFlow_computed list).
- Market caps for P/S and P/E: `wiki/research/ref-financial-statements.md`
  table column "Mkt cap" (cache: ~/edgar-ref-mcaps.json, outside
  the vault). No network pulls from a screen run.
- Ratings + zones: frontmatter of `Efforts/osanwe-v2-overhaul/_work/wave*-analysis.md`;
  fallback glob `wiki/investing/analyses/<ticker>-analysis*.md`.
- HELD set: current-session broker read evidence when available; otherwise
  UNVERIFIED. No quantities or current membership inferred from saved history.

## 2. Indicator primitives (identical to tools/technicals.py)

Let `c[0..n-1]` be a ticker's ascending close series at as-of.

```
SMA_k        = mean(c[n-k .. n-1])                       (None if n < k)
ret_kd       = c[-1] / c[-(k+1)] - 1                     (simple return, k bars)
dist_MA      = c[-1] / SMA_k - 1
RSI14        = Wilder smoothing:
               d[i] = c[i] - c[i-1]; g = max(d,0); l = max(-d,0)
               avgG = mean(g[1..14]); avgL = mean(l[1..14])
               avgG = (avgG*13 + g[i]) / 14   (iterate i = 15..n-1, same avgL)
               RSI = 100 - 100/(1 + avgG/avgL)             (100 if avgL == 0)
vol_w        = stdev(log returns over last w returns) * sqrt(252)
vol_ratio    = vol_20 / vol_60          expanding > 1.2 | contracting < 0.8
vol_pctile_own = share of the instrument's rolling-20d vol history <= current
max_drawdown = min over t of (c[t] / max(c[0..t]) - 1)
```

Zones (signal-library convention): oversold RSI < 30, overbought RSI > 70.
History gate: MA50 needs >=50 bars, MA200 >=200, RSI >=15, vol_ratio >=61.
Short-history tickers (e.g. SPCX-class recent IPOs) are SKIPPED with a reason,
never zero-filled.

## 3. Momentum mode

MOM component (composite-scoring Method 1), inputs clipped to [-50,+50] then
mapped to [0,100] by adding 50:

```
clipmap(x)   = clamp(x, -50, +50) + 50                  -> [0, 100]
MOM          = 0.30*clipmap(ret_21d%)
             + 0.25*clipmap(ret_63d%)
             + 0.25*clipmap(dist_MA50%)
             + 0.20*clipmap(dist_MA200%)
```

Filters (ALL must hold): `RSI14 <= 70`, `c[-1] > SMA_50`, `n >= 200`.
Rank: MOM descending; default top 10. Report COMP (full composite from
ref-composite-scoring.md when the name is covered there) as context only --
the momentum rank keys on MOM, not COMP.

Worked example (bars thru 2026-08-24): MU ret21d -1.1%, ret63d +21.3%,
dist_MA50 -5.4%, dist_MA200 +58.6% ->
MOM = 30*(48.9) + 25*(71.3) + 25*(44.6) + 20*(100) all divided by 100... i.e.
0.30*48.9 + 0.25*71.3 + 0.25*44.6 + 0.20*100 = 63.7. RSI14 48.6 passes;
px < MA50 FAILS the px>MA50 filter -> MU correctly excluded from top momentum
despite a high MOM.

## 4. Value mode (XBRL)

From `<T>-xbrl.json` (concept aliases per tools/edgar-scraper.py CONCEPTS):

```
LQ           = latest reported revenue period
TTM_rev      = sum of trailing four REPORTED revenue quarters; when a fiscal-Q4
               is missing because only the 10-K FY total exists,
               Q4_derived = FY - Q1 - Q2 - Q3            (mark "(Q4d)")
rev_YoY      = LQ.value / value(same fiscal quarter, period 330-400 days before LQ) - 1
TTM_NI       = trailing four NetIncome quarters         (P/E only when TTM_NI > 0)
TTM_FCF      = trailing four FreeCashFlow_computed values from
               -xbrl-extended.json; fallback = trailing four
               NetCashProvidedByUsedInOperatingActivities minus
               PaymentsToAcquirePropertyPlantAndEquipment
P_S          = mktcap / TTM_rev                         (primary rank, ascending)
P_E          = mktcap / TTM_NI                          (tiebreak display only)
NI_marg_TTM  = TTM_NI / TTM_rev
```

Filters: `TTM_FCF > 0`, `rev_YoY > 0`, XBRL present, LQ no older than
3 quarters vs as-of (`[STALE-FUND]` otherwise). EPS-based P/E is impossible
corpus-wide (zero EPS points in the EDGAR pull) -- P/E here always means
mktcap/TTM_NI or is shown as `--`.

Tag-migration guards (verified 2026-08-24): some tickers carry BOTH
`Revenues` (legacy years) and `Revenue` (current years, e.g. AVGO/VST) --
group points PER CONCEPT, pick the concept with the freshest max period, then
dedupe periods before summing TTM. Skip individual revenue points with
value <= 0 (legacy zero fills exist, e.g. ETN/VRT pre-2019 rows); they are
artifacts, not revenue.

Worked example (AMD, caps per ref-financial-statements.md 2026-08-24):
LQ 2026-06-27 rev $11.536B; TTM rev $65.7B; TTM NI $9.3B; TTM FCF $17.8B;
P/S = 772.6/65.7 = **11.8**; P/E = 772.6/9.3 = **83.5**; rev YoY = +50.1%;
passes FCF>0 and YoY>0.

## 5. Quality mode

FUND component (composite-scoring Method 4): percentile-rank across tickers
with XBRL, each input to [0,100]:

```
sub-scores   = { rev_YoY_growth, NI_margin_TTM, cash_to_LT_debt }
FUND         = mean(available sub-scores); require >= 2 of 3
cash_to_LT_debt = latest Cash snapshot / latest LongTermDebt snapshot
margin_stdev = population stdev of the last four quarterly net margins (pp)
margin_trend = NI_marg_TTM_now - NI_marg_TTM_four_quarters_ago
dilution_4q  = ShareIssued_latest / ShareIssued_(4 quarters prior) - 1
```

Filters: `margin_stdev <= 5.0 pp`, `margin_trend >= -5.0 pp`,
`dilution_4q <= +3.0%`. Names lacking ShareIssued data cannot pass the
dilution gate -> excluded from the ranked top-10 and listed under BLIND SPOTS
(ShareIssued exists only in extended pulls, ~30 tickers). Rank: FUND desc.

## 6. Oversold mode

```
fund_pos     = count of positive members of {rev_YoY, NI_marg_TTM, TTM_FCF}
               (XBRL required; no XBRL -> excluded, listed unscored)
```

Filters: `RSI14 < 30`, `c[-1] < SMA_200`, `fund_pos >= 2`.
Rank: RSI14 ascending (most oversold first). Also report dist below MA200
and days-since-RSI-was-last-above-30 for context. Classification label:
"mean-reversion watch", never "buy".

EMPTY IS A RESULT: a strict gate can legitimately return zero names (it did
on 2026-08-24 -- tightest RSI14 was 30.7). When the strict screen is empty,
print "0 names pass strict gates" and, clearly labeled as a NEAR-MISS VIEW,
list the closest failures (e.g. RSI < 40 AND below MA200: AEP 30.7, BWXT 30.7
...). Never silently relax the gate into the ranked table.

## 7. Breakdown mode

Fresh break (either condition, within the last 5 sessions B):

```
low20[t]     = min(closes over the window ending at t, 20 sessions)
BREAK_LOWHIGH= exists s in [n-B, n-1]: c[s] < low20[s-1]
BREAK_MA     = exists s in [n-B, n-1]: (c[s] < SMA50[s]) != (c[s+1] < SMA50[s])
               (same construction against SMA200 counts as a major break)
EXPANSION    = vol_ratio > 1.2
```

Filters: fresh break AND expansion. Rank: vol_ratio desc. Report off-low
(percent above the pre-break 20-session low), break type, days since break,
and vol_pctile_own. Classification: "avoid / risk-off candidates". This mode
NEVER emits trade language; it feeds de-risking review via /advise and
re-analysis via /invest.

## 8. Setup mode (wave analyses)

Parse each wave file (`Efforts/osanwe-v2-overhaul/_work/wave*-analysis.md`):

1. Frontmatter: `ticker`, `date`, `rating`, `rr_ratio`.
2. Body: entry zone lines (`entry:` block or prose ranges like "400-415"),
   stop level, target(s), and stated ratio lines matching
   `rr_at_zone_mid:` / `rr_at_zone_low_*` / `rr_at_spot` patterns.
3. Effective R/R = best STATED zone R/R; else compute
   `(target - zone_mid) / (zone_mid - stop)`. Spot R/R alone NEVER qualifies
   (spot fails while zone passes is common: ETN spot 0.94:1, zone-mid 1.67:1,
   zone-low 3.33:1).
4. Keep only effective R/R >= 3.0 AND rating not SELL-side-only.
5. VOID CHECK against live bars: scan bar dates AFTER the analysis date for a
   close beyond the zone's cancel/stop level (STOP-BREACHED law: a breached
   bracket is void, never recomputed). Voided names move to a VOIDED list with
   the breach date; they are not candidates.
6. Carry rejection reasons verbatim where the analysis states them
   (BWXT: "3.16:1 raw at spot REJECTED: stop inside noise band").

Report distance-to-zone from the live close so staleness of the fill is
visible.

## 9. Cross-mode conventions

- HELD flag: current-session broker-verified membership only. Without it,
  report UNVERIFIED; do not silently exclude candidates as already held or
  claim completeness of a holdings-only result.
- Rating: freshest wave file for the ticker; else latest
  `wiki/investing/analyses/<ticker>-analysis*.md`. Cite file + date. Never
  read ratings out of Atlas watchlist rows (documented stale-prior incident).
- Rounding: percentages 0.1pp, ratios 2 decimals, dollars to 2 significant
  decimals; scores 1 decimal.
- Denominators are printed per run (e.g. "value universe: 41 of 107 with
  usable XBRL"); they shrink/grow with filings coverage.
- Determinism: same db + same files -> byte-identical tables (sort ties broken
  by ticker ascending).

## 10. Worked examples (verified 2026-08-24 against live data)

- momentum: MU ret21d -1.1%, ret63d +21.3%, dist_MA50 -5.4%, dist_MA200
  +58.6% -> MOM = 0.30*48.9 + 0.25*71.3 + 0.25*44.6 + 0.20*100 = 63.7,
  RSI14 48.6 passes, but px < MA50 FAILS -> MU excluded despite high MOM.
  PLTR passes all gates: MOM 80.8, RSI14 66.6.
- value: AMD TTM rev $65.7B, TTM NI $9.3B, TTM FCF $17.8B (extended pull),
  cap $772.6B -> P/S 11.8, P/E 83.5, rev YoY +50.1% -- passes FCF/YoY gates.
- quality gates on extended pulls (30 tickers): MSFT margin stdev 4.3pp <= 5,
  dilution -0.09% <= 3% -> passes; LMT dilution -15.5% (buyback) also passes;
  names without ShareIssued cannot clear the dilution gate and go to BLIND
  SPOTS.
- oversold: strict gate EMPTY on 2026-08-24 (lowest RSI14 = AEP/BWXT 30.7) --
  print the empty result plus a labeled near-miss view.
- breakdown: NRG broke its 20-session low 5 sessions before as-of with
  vol20/vol60 = 1.40 > 1.2 -> the single qualifying avoid/risk-off candidate.
- setup: ETN spot R/R 0.94:1 fails but zone-low vs 480 extension is 3.33:1 ->
  qualifies on ZONE basis; DLR zone-mid blended 5.2:1; BWXT raw 3.16:1 stays
  rejected ("stop inside noise band" reason travels with the name).

## 11. Known limits

- Bars are CLOSES ONLY (no OHLCV) -> volume-based stats come from the signals
  snapshot's stored fields; if absent for a name, breakdown falls back to
  price-range expansion (10d realized range vs prior 50d) and says which path
  was used.
- Point-in-time fundamentals: xbrl records carry `filed` dates; screens do NOT
  back-adjust history to filing dates (a today-scan, not event-safe research).
  For historical studies use /backtest with zero-lookahead queries.
- Survivorship: the universe is today's ingested 107; delisted names since
  2021 are absent from every mode equally.
