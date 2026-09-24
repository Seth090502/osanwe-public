---
aliases:
  - ref-alternative-data-signals
categories: [wiki]
type: reference
status: active
created: 2026-08-24
updated: 2026-08-24
confidence: medium
tags:
  - topic/investing
  - topic/filings
  - topic/alternative-data
  - topic/signals
related: ["ref-institutional-flow-analysis", "ref-factor-lens-ingest-2026-06-10", "[[ref-composite-scoring]]", "investing-moc"]
---

# Alternative data signals -- non-price mining reference (GENERATED)

GENERATED: 2026-08-24 by the alternative-data-signals pass. Every number below
is computed offline from existing vault files; no network was used.

## 1. Sources mined

| Source | Path | What it yields |
|---|---|---|
| EDGAR filings JSON | `wiki/investing/filings/*/<T>-filings.json` (95 issuers) + `insider-form4-summary.json` (13 names) | 8-K dates, Form 4 dates, 10-Q/K, 13F-HR/SC 13G/D rows; window 1995-05..2026-08-21 |
| Entity notes | `wiki/entities/tickers/*.md` (108 notes) | backlog $ amounts, guidance moves, contract awards, insider buy/sell language |
| Factor store bars | `Efforts/osanwe-v2-overhaul/_work/factors.db` table `bars(ticker,date,close)` | close-only daily series, 107 tickers, 2021-08-24..2026-08-24 |

## 2. Known data limitations (read before trusting a row)

- **No volume column exists** in factor-store `bars`. The task brief's "unusual
  volume >2x avg" is UNCOMPUTABLE as specified. Substituted a volume-unaware
  proxy: 10-day cumulative return divided by trailing 250-day volatility
  (`VOLADJ-10D-ZSCORE`, threshold |z| >= 1.5). It detects unusual MOVES, not
  unusual turnover. Rebuild when a volume column lands in the store.
- **Form 4 direction is absent** from the filings JSON (dates only, no
  transaction codes). Insider DIRECTION here comes from curated entity-note
  language only ("N sells / 0 buys", "cluster SELL"), tagged
  `INSIDER-NET-SELL (note-sourced)`. Negations ("ZERO insider buys") were
  hand-checked; regex-only classification misfires on them.
- **8-K content is unknown** (form + date rows only). An 8-K spike flags an
  ACTIVE NEWS CLOCK (distress OR catalyst); it does not say which. Pair it
  with the entity-note row before acting.
- **13F-HR coverage is thin**: fresh Q2-26 reports exist for only AMD, AMZN,
  CSCO, GOOGL, INTC, NVDA (these are holders-of-record filings captured by
  the puller, not full institutional positioning). Treat 13F rows as
  "institutional eyes on", not flow.
- Bars end 2026-08-24; filings end 2026-08-21. Staleness grows from those
  anchors; re-run before citing.

## 3. Signal catalog: detection rules

| Signal | Detection rule (as run) | Strength bands | Direction semantics |
|---|---|---|---|
| 8K-FREQ-SPIKE | count of 8-Ks in trailing 92d vs prior-92d baseline (n/2); fire if count >= 3 | HIGH >= 5 (and ratio >= 1.5 when computable); MEDIUM 3-4 | NEUTRAL/CATALYST-CLOCK if last filing <= 21d old else WATCH |
| FORM4-ACTIVITY | count of Form 4s in trailing 92d | HIGH >= 25 with >= 3 in last 14d; MEDIUM 10-24; LOW 5-9 | DIRECTION-UNKNOWN (dates only; see note-sourced rows for direction) |
| 13F-HR-PRESENCE | any 13F-HR row; fresh = dated >= 2026-07-01 | MEDIUM if fresh Q2-26 report exists; STALE otherwise | INSTITUTIONAL-EYES-ON |
| BACKLOG-DISCLOSED | entity-note line matching backlog/book-of-business AND containing a $ amount | HIGH if >= 2 refs; MEDIUM 1 | POSITIVE-VISIBILITY (revenue visibility, not price direction) |
| GUIDANCE-RAISE | note language raising revenue/EPS/outlook guidance (capex-only raises excluded) | HIGH if >= 2 refs; MEDIUM 1 | POSITIVE |
| GUIDANCE-CUT | note language cutting/lowering/missing guidance | HIGH | NEGATIVE |
| CAPEX-RAISE | note language raising capex plan without a revenue-guidance raise | MEDIUM | NEUTRAL/SPEND-COMMITMENT (demand-ambiguous; margin risk if FCF-negative) |
| CREDIT-DOWNGRADE | S&P/Moody/Fitch cut, BBB- / junk-proximity, Altman-Z DISTRESS, credit tripwire fired | HIGH | NEGATIVE |
| CONTRACT-AWARD | contract win/award/MSA/IDIQ/prime-contract language with $ size | MEDIUM | POSITIVE |
| INSIDER-NET-SELL (note-sourced) | curated note language: sells present, buys absent | HIGH if >= 2 refs or $100M+ cluster; MEDIUM/LOW otherwise | NEGATIVE |
| GAP-MOVES>3PCT | daily |close ret| > 3%; counted over last 20 sessions through 2026-08-24 | HIGH >= 6 moves; MEDIUM 3-5; LOW 1-2 | DOWN if majority negative; UP if majority positive |
| DIRECTION-STREAK | >= 5 consecutive same-direction closes ending 2026-08-24 | HIGH >= 7; MEDIUM 5-6 | UP/DOWN by streak sign |
| VOLADJ-10D-ZSCORE | 10d cumulative log-return / (250d daily-vol * sqrt(10)); fire if |z| >= 1.5 | HIGH |z| >= 2.5; MEDIUM 1.5-2.5 | UP/DOWN by z sign |

## 4. Coverage and method notes

- 106 of 107 bar-tickers produced at least one signal; 298 signal rows total.
- 59 tickers carry >= 3 simultaneous signals; 17 of them are multi-signal with
  zero negative rows and net-positive points (Section 5 conviction table).
- Strength points: HIGH=3, MEDIUM=2, LOW=1. Net score = positive points minus negative points.
- Scoring is descriptive triage, not alpha: no look-forward test has been run
  on these rules. Wire into /invest Phase R calibration before weighting.

## 5. Highest-conviction names: MULTIPLE simultaneous signals, no negatives

Rule: >= 3 distinct simultaneous signal types AND zero negative-direction
rows (Form 4 activity and 13F presence count toward confluence even though
they are direction-neutral by design).

| Rank | Ticker | Distinct positive signals | Net score | Signal mix |
|---|---|---|---|---|
| 1 | AMZN | 7 | +7 | BACKLOG-DISCLOSED, CONTRACT-AWARD, GAP-MOVES>3PCT |
| 2 | SOL-USD | 3 | +7 | DIRECTION-STREAK, GAP-MOVES>3PCT, VOLADJ-10D-ZSCORE |
| 3 | GOOGL | 6 | +6 | BACKLOG-DISCLOSED, GUIDANCE-RAISE |
| 4 | ANET | 3 | +6 | GAP-MOVES>3PCT, GUIDANCE-RAISE |
| 5 | COIN | 4 | +5 | GAP-MOVES>3PCT, VOLADJ-10D-ZSCORE |
| 6 | APH | 3 | +4 | CONTRACT-AWARD, GAP-MOVES>3PCT |
| 7 | LMT | 3 | +4 | BACKLOG-DISCLOSED, CONTRACT-AWARD |
| 8 | HPE | 3 | +3 | GAP-MOVES>3PCT |
| 9 | LITE | 3 | +3 | GAP-MOVES>3PCT |
| 10 | MBLY | 3 | +3 | GAP-MOVES>3PCT |
| 11 | SMR | 3 | +3 | GAP-MOVES>3PCT |
| 12 | AAOI | 4 | +2 | BACKLOG-DISCLOSED |
| 13 | AVAV | 4 | +2 | CONTRACT-AWARD |
| 14 | DLR | 3 | +1 | GAP-MOVES>3PCT |
| 15 | EQIX | 3 | +1 | GAP-MOVES>3PCT |
| 16 | WBD | 3 | +1 | GAP-MOVES>3PCT |

Runner-up clusters (2 distinct positive signals, watch-grade):
ANET (+6), GOOGL (+6), BTC-USD (+5), COIN (+5), LINK-USD (+5), XRP-USD (+5), APH (+4), ASML (+4), HBAR-USD (+4), LMT (+4), XLM-USD (+4), BE (+3), AVGO (+2), PLTR (+1), ORCL (+0), NVDA (-1), NBIS (-3)

Most conflicted (strong signals BOTH directions -- do not read as one-way):
- NBIS: pos 5 vs neg 8 -- BACKLOG-DISCLOSED, CAPEX-RAISE, CONTRACT-AWARD, DIRECTION-STREAK, FORM4-ACTIVITY, GAP-MOVES>3PCT, INSIDER-NET-SELL
- AVGO: pos 6 vs neg 4 -- 8K-FREQ-SPIKE, BACKLOG-DISCLOSED, FORM4-ACTIVITY, GAP-MOVES>3PCT, GUIDANCE-RAISE, VOLADJ-10D-ZSCORE
- ORCL: pos 5 vs neg 5 -- CONTRACT-AWARD, CREDIT-DOWNGRADE, FORM4-ACTIVITY, GAP-MOVES>3PCT, INSIDER-NET-SELL
- NVDA: pos 4 vs neg 5 -- 13F-HR-PRESENCE, 8K-FREQ-SPIKE, CAPEX-RAISE, CONTRACT-AWARD, DIRECTION-STREAK, FORM4-ACTIVITY, GAP-MOVES>3PCT, INSIDER-NET-SELL

Strongest NET-NEGATIVE stacks (distribution/distress side):
NBIS (-8), VOLT (-7), AMD (-6), NVDA (-5), RKLB (-5), AMKR (-5), INTC (-5), META (-5), OKLO (-5), ORCL (-5), SNDK (-5), AEIS (-5)

## 6. SIGNAL DASHBOARD (all rows)

Sorted: conviction names first, then by |net score|. Columns: ticker |
signal type | strength | direction | evidence.

| Ticker | Signal type | Strength | Direction | Evidence |
|---|---|---|---|---|
| **AMZN** (net +7) | BACKLOG-DISCLOSED | HIGH | POSITIVE-VISIBILITY | 9 backlog refs; e.g. "backlog $244B +40% YoY" |
|   | 13F-HR-PRESENCE | MEDIUM | INSTITUTIONAL-EYES-ON | 1 Q2-26 13F-HR report(s); history: 2026-05-05, 2026-08-06 |
|   | 8K-FREQ-SPIKE | MEDIUM | WATCH | 4 8-Ks in 92d vs 2/92d baseline; latest 2026-07-30 (25d ago) |
|   | CAPEX-RAISE | MEDIUM | NEUTRAL/SPEND-COMMITMENT | 6 capex-raise refs; e.g. "capex execution; structural per capex sup" |
|   | CONTRACT-AWARD | MEDIUM | POSITIVE | 1 contract refs; e.g. "$100B deal: 5GW Trainium compute commitment over 2026-2029; ~1GW Trainium2+Trainium3 by end-2026; re" |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 12 Form 4s/92d, 2 in last 14d, 4 in last 30d; latest 2026-08-19 (5d ago) |
|   | GAP-MOVES>3PCT | MEDIUM | UP | 3 >3% day-moves in 20 sessions (0 dn/3 up); latest 2026-08-03 +4.58% |
| **SOL-USD** (net +7) | DIRECTION-STREAK | HIGH | UP | 8 consecutive up closes through 2026-08-24 (+30.0% over run) |
|   | GAP-MOVES>3PCT | MEDIUM | UP | 3 >3% day-moves in 20 sessions (0 dn/3 up); latest 2026-08-21 +6.87% |
|   | VOLADJ-10D-ZSCORE | MEDIUM | UP | 10d move z=+2.47 (+28.7% vs 250d vol; volume-unaware proxy) |
| **GOOGL** (net +6) | BACKLOG-DISCLOSED | HIGH | POSITIVE-VISIBILITY | 10 backlog refs; e.g. "backlog $460B doubled QoQ from $240B; Net income $62" |
|   | CAPEX-RAISE | HIGH | NEUTRAL/SPEND-COMMITMENT | FY26 capex RAISED to $195-205B (third raise of 2026); FY27 "significantly increase" |
|   | GUIDANCE-RAISE | HIGH | POSITIVE | 3 raise refs; e.g. "raised $180-190B; FY27" |
|   | 13F-HR-PRESENCE | MEDIUM | INSTITUTIONAL-EYES-ON | 1 Q2-26 13F-HR report(s); history: 2026-08-07 |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 36 Form 4s/92d, 1 in last 14d, 12 in last 30d; latest 2026-08-11 (13d ago) |
|   | GAP-MOVES>3PCT | MEDIUM | MIXED | 4 >3% day-moves in 20 sessions (2 dn/2 up); latest 2026-08-11 -3.84% |
| **ANET** (net +6) | GAP-MOVES>3PCT | HIGH | UP | 10 >3% day-moves in 20 sessions (4 dn/6 up); latest 2026-08-19 -3.48% |
|   | GUIDANCE-RAISE | HIGH | POSITIVE | 2 raise refs; e.g. "guidance rais" |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 35 Form 4s/92d, 2 in last 14d, 7 in last 30d; latest 2026-08-14 (10d ago) |
| **COIN** (net +5) | GAP-MOVES>3PCT | HIGH | UP | 9 >3% day-moves in 20 sessions (4 dn/5 up); latest 2026-08-21 +8.20% |
|   | 8K-FREQ-SPIKE | MEDIUM | WATCH | 4 8-Ks in 92d vs 1.5/92d baseline; latest 2026-07-30 (25d ago) |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 18 Form 4s/92d, 2 in last 14d, 4 in last 30d; latest 2026-08-18 (6d ago) |
|   | VOLADJ-10D-ZSCORE | MEDIUM | UP | 10d move z=+1.63 (+24.7% vs 250d vol; volume-unaware proxy) |
| **APH** (net +4) | CONTRACT-AWARD | MEDIUM | POSITIVE | 2 contract refs; e.g. "$9.4B orders, 1" |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 20 Form 4s/92d, 0 in last 14d, 5 in last 30d; latest 2026-08-06 (18d ago) |
|   | GAP-MOVES>3PCT | MEDIUM | UP | 5 >3% day-moves in 20 sessions (2 dn/3 up); latest 2026-08-18 -6.61% |
| **LMT** (net +4) | BACKLOG-DISCLOSED | MEDIUM | POSITIVE-VISIBILITY | 1 backlog refs; e.g. "Backlog trajectory: $150B pre-2022-invasion -> $176B end-2024 -> $194B end-2025" |
|   | CONTRACT-AWARD | MEDIUM | POSITIVE | 1 contract refs; e.g. "contract awarded by Army Contracting Command-Redstone; ~$15M per missile; range ~1,725 miles; eight-" |
|   | FORM4-ACTIVITY | LOW | DIRECTION-UNKNOWN (dates only) | 6 Form 4s/92d, 2 in last 14d, 3 in last 30d; latest 2026-08-17 (7d ago) |
| **HPE** (net +3) | GAP-MOVES>3PCT | HIGH | UP | 7 >3% day-moves in 20 sessions (3 dn/4 up); latest 2026-08-19 -4.60% |
|   | 8K-FREQ-SPIKE | MEDIUM | NEUTRAL/CATALYST-CLOCK | 3 8-Ks in 92d vs 1/92d baseline; latest 2026-08-04 (20d ago) |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 10 Form 4s/92d, 0 in last 14d, 1 in last 30d; latest 2026-07-28 (27d ago) |
| **LITE** (net +3) | GAP-MOVES>3PCT | HIGH | UP | 15 >3% day-moves in 20 sessions (7 dn/8 up); latest 2026-08-24 -5.00% |
|   | 8K-FREQ-SPIKE | MEDIUM | NEUTRAL/CATALYST-CLOCK | 3 8-Ks in 92d vs 1.5/92d baseline; latest 2026-08-11 (13d ago) |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 19 Form 4s/92d, 10 in last 14d, 10 in last 30d; latest 2026-08-21 (3d ago) |
| **MBLY** (net +3) | GAP-MOVES>3PCT | HIGH | UP | 7 >3% day-moves in 20 sessions (3 dn/4 up); latest 2026-08-24 -4.71% |
|   | 8K-FREQ-SPIKE | MEDIUM | NEUTRAL/CATALYST-CLOCK | 4 8-Ks in 92d vs 0.5/92d baseline; latest 2026-08-12 (12d ago) |
|   | FORM4-ACTIVITY | LOW | DIRECTION-UNKNOWN (dates only) | 7 Form 4s/92d, 1 in last 14d, 2 in last 30d; latest 2026-08-10 (14d ago) |
| **SMR** (net +3) | GAP-MOVES>3PCT | HIGH | UP | 13 >3% day-moves in 20 sessions (6 dn/7 up); latest 2026-08-21 +3.64% |
|   | 8K-FREQ-SPIKE | MEDIUM | NEUTRAL/CATALYST-CLOCK | 3 8-Ks in 92d vs 2/92d baseline; latest 2026-08-11 (13d ago) |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 14 Form 4s/92d, 2 in last 14d, 3 in last 30d; latest 2026-08-20 (4d ago) |
| **AAOI** (net +2) | 8K-FREQ-SPIKE | HIGH | NEUTRAL/CATALYST-CLOCK | 5 8-Ks in 92d vs 0/92d baseline; latest 2026-08-21 (3d ago) |
|   | GAP-MOVES>3PCT | HIGH | MIXED | 16 >3% day-moves in 20 sessions (8 dn/8 up); latest 2026-08-24 -12.08% |
|   | BACKLOG-DISCLOSED | MEDIUM | POSITIVE-VISIBILITY | 1 backlog refs; e.g. "backlog (>$200M 1" |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 29 Form 4s/92d, 2 in last 14d, 4 in last 30d; latest 2026-08-20 (4d ago) |
| **AVAV** (net +2) | 8K-FREQ-SPIKE | HIGH | NEUTRAL/CATALYST-CLOCK | 5 8-Ks in 92d vs 0/92d baseline; latest 2026-08-07 (17d ago) |
|   | GAP-MOVES>3PCT | HIGH | MIXED | 10 >3% day-moves in 20 sessions (5 dn/5 up); latest 2026-08-24 -4.92% |
|   | CONTRACT-AWARD | MEDIUM | POSITIVE | 2 contract refs; e.g. "IDIQ; funded backlog $1" |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 32 Form 4s/92d, 2 in last 14d, 2 in last 30d; latest 2026-08-19 (5d ago) |
| **DLR** (net +1) | 8K-FREQ-SPIKE | HIGH | NEUTRAL/CATALYST-CLOCK | 6 8-Ks in 92d vs 1/92d baseline; latest 2026-08-19 (5d ago) |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 13 Form 4s/92d, 0 in last 14d, 0 in last 30d; latest 2026-07-02 (53d ago) |
|   | GAP-MOVES>3PCT | LOW | UP | 1 >3% day-moves in 20 sessions (0 dn/1 up); latest 2026-08-12 +3.28% |
| **EQIX** (net +1) | 8K-FREQ-SPIKE | MEDIUM | NEUTRAL/CATALYST-CLOCK | 4 8-Ks in 92d vs 2/92d baseline; latest 2026-08-06 (18d ago) |
|   | FORM4-ACTIVITY | LOW | DIRECTION-UNKNOWN (dates only) | 9 Form 4s/92d, 2 in last 14d, 3 in last 30d; latest 2026-08-20 (4d ago) |
|   | GAP-MOVES>3PCT | LOW | UP | 2 >3% day-moves in 20 sessions (0 dn/2 up); latest 2026-08-12 +3.56% |
| **WBD** (net +1) | 8K-FREQ-SPIKE | MEDIUM | NEUTRAL/CATALYST-CLOCK | 4 8-Ks in 92d vs 2/92d baseline; latest 2026-08-06 (18d ago) |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 24 Form 4s/92d, 8 in last 14d, 8 in last 30d; latest 2026-08-18 (6d ago) |
|   | GAP-MOVES>3PCT | LOW | UP | 1 >3% day-moves in 20 sessions (0 dn/1 up); latest 2026-07-31 +3.26% |
| **VOLT** (net -7) | INSIDER-NET-SELL (note-sourced) | HIGH | NEGATIVE | 2 insider-sale refs; e.g. "insider selling (watch)" |
|   | DIRECTION-STREAK | MEDIUM | DOWN | 5 consecutive down closes through 2026-08-24 (-8.9% over run) |
|   | GAP-MOVES>3PCT | MEDIUM | DOWN | 4 >3% day-moves in 20 sessions (3 dn/1 up); latest 2026-08-18 -3.94% |
| **AMD** (net -6) | FORM4-ACTIVITY | HIGH | DIRECTION-UNKNOWN (dates only) | 29 Form 4s/92d, 23 in last 14d, 23 in last 30d; latest 2026-08-21 (3d ago) |
|   | GAP-MOVES>3PCT | HIGH | DOWN | 9 >3% day-moves in 20 sessions (6 dn/3 up); latest 2026-08-24 -3.03% |
|   | INSIDER-NET-SELL (note-sourced) | HIGH | NEGATIVE | OpenInsider 71 sells / 0 buys / $116.1M past 6mo; Papermaster CTO ATH selling $159->$350 |
|   | 13F-HR-PRESENCE | MEDIUM | INSTITUTIONAL-EYES-ON | 1 Q2-26 13F-HR report(s); history: 2026-08-14 |
|   | 8K-FREQ-SPIKE | MEDIUM | NEUTRAL/CATALYST-CLOCK | 4 8-Ks in 92d vs 0/92d baseline; latest 2026-08-19 (5d ago) |
|   | CAPEX-RAISE | MEDIUM | NEUTRAL/SPEND-COMMITMENT | 3 capex-raise refs; e.g. "capex 2026 confirmed (rais" |
| **AMKR** (net -5) | FORM4-ACTIVITY | HIGH | DIRECTION-UNKNOWN (dates only) | 27 Form 4s/92d, 3 in last 14d, 6 in last 30d; latest 2026-08-19 (5d ago) |
|   | GAP-MOVES>3PCT | HIGH | DOWN | 12 >3% day-moves in 20 sessions (7 dn/5 up); latest 2026-08-24 -4.36% |
|   | CAPEX-RAISE | MEDIUM | NEUTRAL/SPEND-COMMITMENT | 1 capex-raise refs; e.g. "capex; new Arizona facility; $407M CHIPS funding (per matrixbcg) (per [[ref-ai-sup" |
|   | DIRECTION-STREAK | MEDIUM | DOWN | 5 consecutive down closes through 2026-08-24 (-21.6% over run) |
| **INTC** (net -5) | GAP-MOVES>3PCT | HIGH | DOWN | 9 >3% day-moves in 20 sessions (5 dn/4 up); latest 2026-08-19 -4.02% |
|   | 13F-HR-PRESENCE | MEDIUM | INSTITUTIONAL-EYES-ON | 1 Q2-26 13F-HR report(s); history: 2026-05-12, 2026-08-14 |
|   | DIRECTION-STREAK | MEDIUM | DOWN | 5 consecutive down closes through 2026-08-24 (-15.6% over run) |
|   | FORM4-ACTIVITY | LOW | DIRECTION-UNKNOWN (dates only) | 7 Form 4s/92d, 1 in last 14d, 3 in last 30d; latest 2026-08-14 (10d ago) |
| **OKLO** (net -5) | GAP-MOVES>3PCT | HIGH | DOWN | 14 >3% day-moves in 20 sessions (8 dn/6 up); latest 2026-08-24 -3.84% |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 21 Form 4s/92d, 3 in last 14d, 7 in last 30d; latest 2026-08-17 (7d ago) |
|   | INSIDER-NET-SELL (note-sourced) | MEDIUM | NEGATIVE | 34 insider sells / 0 buys (~$140M Jan co-founder 10b5-1 + cashless exercises) |
| **SNDK** (net -5) | GAP-MOVES>3PCT | HIGH | DOWN | 16 >3% day-moves in 20 sessions (9 dn/7 up); latest 2026-08-24 -7.00% |
|   | INSIDER-NET-SELL (note-sourced) | MEDIUM | NEGATIVE | zero buys trailing 400d vs 8 sells ($7.87M discretionary cluster May-Jun ~$1,755) |
|   | FORM4-ACTIVITY | LOW | DIRECTION-UNKNOWN (dates only) | 8 Form 4s/92d, 0 in last 14d, 1 in last 30d; latest 2026-08-04 (20d ago) |
| **AEIS** (net -5) | GAP-MOVES>3PCT | HIGH | DOWN | 12 >3% day-moves in 20 sessions (7 dn/5 up); latest 2026-08-24 -4.06% |
|   | DIRECTION-STREAK | MEDIUM | DOWN | 5 consecutive down closes through 2026-08-24 (-21.3% over run) |
| **BTC-USD** (net +5) | VOLADJ-10D-ZSCORE | HIGH | UP | 10d move z=+3.04 (+25.9% vs 250d vol; volume-unaware proxy) |
|   | GAP-MOVES>3PCT | MEDIUM | UP | 3 >3% day-moves in 20 sessions (0 dn/3 up); latest 2026-08-21 +7.26% |
| **LINK-USD** (net +5) | VOLADJ-10D-ZSCORE | HIGH | UP | 10d move z=+2.52 (+29.3% vs 250d vol; volume-unaware proxy) |
|   | GAP-MOVES>3PCT | MEDIUM | UP | 4 >3% day-moves in 20 sessions (0 dn/4 up); latest 2026-08-21 +12.26% |
| **PPA** (net -5) | DIRECTION-STREAK | MEDIUM | DOWN | 6 consecutive down closes through 2026-08-24 (-7.5% over run) |
|   | VOLADJ-10D-ZSCORE | MEDIUM | DOWN | 10d move z=-1.72 (-7.0% vs 250d vol; volume-unaware proxy) |
|   | GAP-MOVES>3PCT | LOW | DOWN | 2 >3% day-moves in 20 sessions (2 dn/0 up); latest 2026-08-20 -3.18% |
| **XRP-USD** (net +5) | VOLADJ-10D-ZSCORE | HIGH | UP | 10d move z=+3.90 (+50.9% vs 250d vol; volume-unaware proxy) |
|   | GAP-MOVES>3PCT | MEDIUM | UP | 4 >3% day-moves in 20 sessions (0 dn/4 up); latest 2026-08-23 +3.99% |
| **CRDO** (net -4) | GAP-MOVES>3PCT | HIGH | MIXED | 14 >3% day-moves in 20 sessions (7 dn/7 up); latest 2026-08-24 -5.22% |
|   | DIRECTION-STREAK | MEDIUM | DOWN | 5 consecutive down closes through 2026-08-24 (-22.7% over run) |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 38 Form 4s/92d, 1 in last 14d, 4 in last 30d; latest 2026-08-21 (3d ago) |
|   | INSIDER-NET-SELL (note-sourced) | MEDIUM | NEGATIVE | 1 insider-sale refs; e.g. "insider selling to normalize" |
| **ASML** (net +4) | GAP-MOVES>3PCT | MEDIUM | UP | 5 >3% day-moves in 20 sessions (2 dn/3 up); latest 2026-08-18 -4.26% |
|   | GUIDANCE-RAISE | MEDIUM | POSITIVE | 1 raise refs; e.g. "guidance rais" |
| **HBAR-USD** (net +4) | GAP-MOVES>3PCT | MEDIUM | UP | 4 >3% day-moves in 20 sessions (0 dn/4 up); latest 2026-08-23 +3.02% |
|   | VOLADJ-10D-ZSCORE | MEDIUM | UP | 10d move z=+2.02 (+21.0% vs 250d vol; volume-unaware proxy) |
| **XLM-USD** (net +4) | GAP-MOVES>3PCT | MEDIUM | UP | 3 >3% day-moves in 20 sessions (0 dn/3 up); latest 2026-08-21 +11.24% |
|   | VOLADJ-10D-ZSCORE | MEDIUM | UP | 10d move z=+1.67 (+24.5% vs 250d vol; volume-unaware proxy) |
| **BE** (net +3) | GAP-MOVES>3PCT | HIGH | MIXED | 8 >3% day-moves in 20 sessions (4 dn/4 up); latest 2026-08-18 -9.97% |
|   | 8K-FREQ-SPIKE | MEDIUM | WATCH | 4 8-Ks in 92d vs 0.5/92d baseline; latest 2026-07-28 (27d ago) |
|   | BACKLOG-DISCLOSED | MEDIUM | POSITIVE-VISIBILITY | 1 backlog refs; e.g. "backlog ~$20B (product $6B 2" |
|   | CONTRACT-AWARD | MEDIUM | POSITIVE | 5 contract refs; e.g. "MSA execution + 1" |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 23 Form 4s/92d, 5 in last 14d, 6 in last 30d; latest 2026-08-18 (6d ago) |
|   | INSIDER-NET-SELL (note-sourced) | LOW | NEGATIVE | ZERO insider buys across the +1,362% run (absence signal, weaker class) |
| **HIMS** (net -3) | FORM4-ACTIVITY | HIGH | DIRECTION-UNKNOWN (dates only) | 36 Form 4s/92d, 24 in last 14d, 24 in last 30d; latest 2026-08-20 (4d ago) |
|   | GAP-MOVES>3PCT | HIGH | DOWN | 13 >3% day-moves in 20 sessions (7 dn/6 up); latest 2026-08-24 -8.20% |
|   | 8K-FREQ-SPIKE | MEDIUM | NEUTRAL/CATALYST-CLOCK | 3 8-Ks in 92d vs 0/92d baseline; latest 2026-08-10 (14d ago) |
| **LHX** (net -3) | 8K-FREQ-SPIKE | MEDIUM | NEUTRAL/CATALYST-CLOCK | 3 8-Ks in 92d vs 2/92d baseline; latest 2026-08-17 (7d ago) |
|   | VOLADJ-10D-ZSCORE | MEDIUM | DOWN | 10d move z=-1.69 (-9.1% vs 250d vol; volume-unaware proxy) |
|   | FORM4-ACTIVITY | LOW | DIRECTION-UNKNOWN (dates only) | 9 Form 4s/92d, 0 in last 14d, 5 in last 30d; latest 2026-08-03 (21d ago) |
|   | GAP-MOVES>3PCT | LOW | DOWN | 2 >3% day-moves in 20 sessions (2 dn/0 up); latest 2026-08-17 -4.61% |
| **QCOM** (net -3) | GAP-MOVES>3PCT | HIGH | DOWN | 6 >3% day-moves in 20 sessions (4 dn/2 up); latest 2026-08-10 -3.39% |
|   | 8K-FREQ-SPIKE | MEDIUM | WATCH | 3 8-Ks in 92d vs 1/92d baseline; latest 2026-07-31 (24d ago) |
|   | FORM4-ACTIVITY | LOW | DIRECTION-UNKNOWN (dates only) | 7 Form 4s/92d, 2 in last 14d, 3 in last 30d; latest 2026-08-21 (3d ago) |
| **RKLB** (net -3) | GAP-MOVES>3PCT | HIGH | DOWN | 11 >3% day-moves in 20 sessions (7 dn/4 up); latest 2026-08-24 -4.44% |
|   | 8K-FREQ-SPIKE | MEDIUM | NEUTRAL/CATALYST-CLOCK | 5 8-Ks in 92d vs 3.5/92d baseline; latest 2026-08-13 (11d ago) |
|   | CONTRACT-AWARD | MEDIUM | POSITIVE | 3 contract refs; e.g. "prime contract anchors institutional thesis" |
|   | DIRECTION-STREAK | MEDIUM | DOWN | 5 consecutive down closes through 2026-08-24 (-15.5% over run) |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 17 Form 4s/92d, 1 in last 14d, 1 in last 30d; latest 2026-08-18 (6d ago) |
| **SMCI** (net -3) | 8K-FREQ-SPIKE | HIGH | NEUTRAL/CATALYST-CLOCK | 6 8-Ks in 92d vs 0/92d baseline; latest 2026-08-11 (13d ago) |
|   | FORM4-ACTIVITY | HIGH | DIRECTION-UNKNOWN (dates only) | 34 Form 4s/92d, 21 in last 14d, 21 in last 30d; latest 2026-08-19 (5d ago) |
|   | GAP-MOVES>3PCT | HIGH | DOWN | 11 >3% day-moves in 20 sessions (6 dn/5 up); latest 2026-08-24 -4.83% |
| **VRT** (net -3) | GAP-MOVES>3PCT | HIGH | DOWN | 7 >3% day-moves in 20 sessions (4 dn/3 up); latest 2026-08-19 -4.23% |
|   | 8K-FREQ-SPIKE | MEDIUM | WATCH | 4 8-Ks in 92d vs 2/92d baseline; latest 2026-07-29 (26d ago) |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 11 Form 4s/92d, 0 in last 14d, 0 in last 30d; latest 2026-06-26 (59d ago) |
| **VST** (net -3) | GAP-MOVES>3PCT | HIGH | DOWN | 6 >3% day-moves in 20 sessions (4 dn/2 up); latest 2026-08-18 -3.83% |
|   | 8K-FREQ-SPIKE | MEDIUM | NEUTRAL/CATALYST-CLOCK | 4 8-Ks in 92d vs 2/92d baseline; latest 2026-08-07 (17d ago) |
|   | FORM4-ACTIVITY | LOW | DIRECTION-UNKNOWN (dates only) | 6 Form 4s/92d, 0 in last 14d, 0 in last 30d; latest 2026-06-23 (62d ago) |
| **WDC** (net -3) | GAP-MOVES>3PCT | HIGH | DOWN | 14 >3% day-moves in 20 sessions (8 dn/6 up); latest 2026-08-24 -5.78% |
|   | 8K-FREQ-SPIKE | MEDIUM | NEUTRAL/CATALYST-CLOCK | 4 8-Ks in 92d vs 0/92d baseline; latest 2026-08-05 (19d ago) |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 31 Form 4s/92d, 1 in last 14d, 3 in last 30d; latest 2026-08-12 (12d ago) |
| **AEP** (net -3) | DIRECTION-STREAK | MEDIUM | DOWN | 5 consecutive down closes through 2026-08-24 (-4.4% over run) |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 11 Form 4s/92d, 0 in last 14d, 2 in last 30d; latest 2026-08-04 (20d ago) |
|   | GAP-MOVES>3PCT | LOW | DOWN | 1 >3% day-moves in 20 sessions (1 dn/0 up); latest 2026-08-21 -3.79% |
| **ALAB** (net -3) | GAP-MOVES>3PCT | HIGH | DOWN | 12 >3% day-moves in 20 sessions (7 dn/5 up); latest 2026-08-24 -3.04% |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 17 Form 4s/92d, 4 in last 14d, 4 in last 30d; latest 2026-08-19 (5d ago) |
| **AMAT** (net -3) | GAP-MOVES>3PCT | HIGH | DOWN | 10 >3% day-moves in 20 sessions (6 dn/4 up); latest 2026-08-19 -3.53% |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 11 Form 4s/92d, 0 in last 14d, 0 in last 30d; latest 2026-07-06 (49d ago) |
| **AMBA** (net -3) | GAP-MOVES>3PCT | HIGH | DOWN | 8 >3% day-moves in 20 sessions (5 dn/3 up); latest 2026-08-24 -4.01% |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 11 Form 4s/92d, 0 in last 14d, 0 in last 30d; latest 2026-07-10 (45d ago) |
| **ARM** (net -3) | GAP-MOVES>3PCT | HIGH | DOWN | 7 >3% day-moves in 20 sessions (4 dn/3 up); latest 2026-08-18 -6.67% |
|   | FORM4-ACTIVITY | LOW | DIRECTION-UNKNOWN (dates only) | 6 Form 4s/92d, 2 in last 14d, 2 in last 30d; latest 2026-08-18 (6d ago) |
| **BWXT** (net -3) | GAP-MOVES>3PCT | HIGH | DOWN | 7 >3% day-moves in 20 sessions (5 dn/2 up); latest 2026-08-24 -3.16% |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 11 Form 4s/92d, 1 in last 14d, 1 in last 30d; latest 2026-08-13 (11d ago) |
| **FLNC** (net -3) | GAP-MOVES>3PCT | HIGH | DOWN | 13 >3% day-moves in 20 sessions (8 dn/5 up); latest 2026-08-20 -5.63% |
|   | FORM4-ACTIVITY | LOW | DIRECTION-UNKNOWN (dates only) | 5 Form 4s/92d, 0 in last 14d, 0 in last 30d; latest 2026-07-21 (34d ago) |
| **GFS** (net -3) | FORM4-ACTIVITY | HIGH | DIRECTION-UNKNOWN (dates only) | 38 Form 4s/92d, 3 in last 14d, 22 in last 30d; latest 2026-08-20 (4d ago) |
|   | GAP-MOVES>3PCT | HIGH | DOWN | 11 >3% day-moves in 20 sessions (6 dn/5 up); latest 2026-08-24 -3.75% |
| **KTOS** (net +3) | GAP-MOVES>3PCT | HIGH | UP | 9 >3% day-moves in 20 sessions (3 dn/6 up); latest 2026-08-24 -5.21% |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 22 Form 4s/92d, 4 in last 14d, 7 in last 30d; latest 2026-08-20 (4d ago) |
| **META** (net -3) | FORM4-ACTIVITY | HIGH | DIRECTION-UNKNOWN (dates only) | 38 Form 4s/92d, 16 in last 14d, 21 in last 30d; latest 2026-08-20 (4d ago) |
|   | GAP-MOVES>3PCT | HIGH | DOWN | 6 >3% day-moves in 20 sessions (4 dn/2 up); latest 2026-08-18 -4.45% |
|   | CAPEX-RAISE | MEDIUM | NEUTRAL/SPEND-COMMITMENT | 15 capex-raise refs; e.g. "capex (rais" |
|   | CAPEX-RAISE | MEDIUM | NEGATIVE-MARGIN-RISK | FY26 capex RAISED to $125-145B; Q2 AMC stock down on capex raise; margin watch |
|   | CONTRACT-AWARD | MEDIUM | POSITIVE | 1 contract refs; e.g. "$3B contract to $27B March 2026; complements Meta's $125-145B FY26 calendar capex (raised from $115-" |
| **MP** (net +3) | GAP-MOVES>3PCT | HIGH | UP | 11 >3% day-moves in 20 sessions (4 dn/7 up); latest 2026-08-24 -3.90% |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 14 Form 4s/92d, 0 in last 14d, 0 in last 30d; latest 2026-06-30 (55d ago) |
| **MU** (net +3) | GAP-MOVES>3PCT | HIGH | UP | 11 >3% day-moves in 20 sessions (5 dn/6 up); latest 2026-08-24 -5.77% |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 14 Form 4s/92d, 1 in last 14d, 4 in last 30d; latest 2026-08-20 (4d ago) |
| **NBIS** (net -3) | BACKLOG-DISCLOSED | HIGH | POSITIVE-VISIBILITY | 2 backlog refs; e.g. "backlog 2027-2031 (Meta $27B Mar 2026 + Microsoft $17" |
|   | GAP-MOVES>3PCT | HIGH | DOWN | 13 >3% day-moves in 20 sessions (7 dn/6 up); latest 2026-08-24 -4.95% |
|   | INSIDER-NET-SELL (note-sourced) | HIGH | NEGATIVE | 18 Form-4 sells / 8 insiders / ~$135M+ zero buys 3/31-6/15; cluster extended to ~$156.8M by 7/15 |
|   | CAPEX-RAISE | MEDIUM | NEUTRAL/SPEND-COMMITMENT | 1 capex-raise refs; e.g. "capex guide $20-25B (rais" |
|   | CONTRACT-AWARD | MEDIUM | POSITIVE | 2 contract refs; e.g. "$27B contracted backlog (see Backlog architecture) means any META infrastructure-spend deferral gate" |
|   | DIRECTION-STREAK | MEDIUM | DOWN | 6 consecutive down closes through 2026-08-24 (-25.0% over run) |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 11 Form 4s/92d, 2 in last 14d, 2 in last 30d; latest 2026-08-18 (6d ago) |
| **NOW** (net +3) | FORM4-ACTIVITY | HIGH | DIRECTION-UNKNOWN (dates only) | 28 Form 4s/92d, 19 in last 14d, 19 in last 30d; latest 2026-08-19 (5d ago) |
|   | GAP-MOVES>3PCT | HIGH | UP | 7 >3% day-moves in 20 sessions (2 dn/5 up); latest 2026-08-19 +6.45% |
| **ASMIY** (net +3) | GAP-MOVES>3PCT | HIGH | UP | 7 >3% day-moves in 20 sessions (3 dn/4 up); latest 2026-08-18 -5.45% |
| **ATEYY** (net +3) | GAP-MOVES>3PCT | HIGH | UP | 10 >3% day-moves in 20 sessions (4 dn/6 up); latest 2026-08-24 -3.90% |
| **ETN** (net +3) | GAP-MOVES>3PCT | HIGH | UP | 7 >3% day-moves in 20 sessions (3 dn/4 up); latest 2026-08-18 -5.29% |
| **ITA** (net -3) | VOLADJ-10D-ZSCORE | MEDIUM | DOWN | 10d move z=-1.58 (-6.9% vs 250d vol; volume-unaware proxy) |
|   | GAP-MOVES>3PCT | LOW | DOWN | 2 >3% day-moves in 20 sessions (2 dn/0 up); latest 2026-08-20 -3.49% |
| **AVGO** (net +2) | BACKLOG-DISCLOSED | HIGH | POSITIVE-VISIBILITY | 3 backlog refs; e.g. "backlog + Tomahawk 6 dominance) but Marvell competitive intensification (NVDA $2B partnership + Goog" |
|   | GUIDANCE-RAISE | HIGH | POSITIVE | 2 raise refs; e.g. "RAISED FY26" |
|   | 8K-FREQ-SPIKE | MEDIUM | WATCH | 4 8-Ks in 92d vs 1.5/92d baseline; latest 2026-07-06 (49d ago) |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 10 Form 4s/92d, 0 in last 14d, 0 in last 30d; latest 2026-07-14 (41d ago) |
|   | GAP-MOVES>3PCT | MEDIUM | DOWN | 5 >3% day-moves in 20 sessions (3 dn/2 up); latest 2026-08-19 -4.61% |
|   | VOLADJ-10D-ZSCORE | MEDIUM | DOWN | 10d move z=-1.62 (-14.3% vs 250d vol; volume-unaware proxy) |
| **BAH** (net -2) | 8K-FREQ-SPIKE | MEDIUM | NEUTRAL/CATALYST-CLOCK | 4 8-Ks in 92d vs 1.5/92d baseline; latest 2026-08-04 (20d ago) |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 21 Form 4s/92d, 1 in last 14d, 12 in last 30d; latest 2026-08-17 (7d ago) |
|   | GAP-MOVES>3PCT | MEDIUM | DOWN | 5 >3% day-moves in 20 sessions (3 dn/2 up); latest 2026-08-20 -3.15% |
| **HUBB** (net -2) | 8K-FREQ-SPIKE | MEDIUM | WATCH | 3 8-Ks in 92d vs 2/92d baseline; latest 2026-07-28 (27d ago) |
|   | GAP-MOVES>3PCT | MEDIUM | DOWN | 3 >3% day-moves in 20 sessions (2 dn/1 up); latest 2026-08-18 -4.05% |
|   | FORM4-ACTIVITY | LOW | DIRECTION-UNKNOWN (dates only) | 6 Form 4s/92d, 4 in last 14d, 4 in last 30d; latest 2026-08-18 (6d ago) |
| **HII** (net -2) | CONTRACT-AWARD | MEDIUM | POSITIVE | 1 contract refs; e.g. "contract awards $11" |
|   | DIRECTION-STREAK | MEDIUM | DOWN | 6 consecutive down closes through 2026-08-24 (-10.1% over run) |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 33 Form 4s/92d, 2 in last 14d, 2 in last 30d; latest 2026-08-11 (13d ago) |
|   | GAP-MOVES>3PCT | MEDIUM | MIXED | 4 >3% day-moves in 20 sessions (2 dn/2 up); latest 2026-08-20 -3.32% |
|   | VOLADJ-10D-ZSCORE | MEDIUM | DOWN | 10d move z=-1.55 (-10.9% vs 250d vol; volume-unaware proxy) |
| **KLAC** (net -2) | FORM4-ACTIVITY | HIGH | DIRECTION-UNKNOWN (dates only) | 37 Form 4s/92d, 12 in last 14d, 32 in last 30d; latest 2026-08-14 (10d ago) |
|   | GAP-MOVES>3PCT | HIGH | MIXED | 8 >3% day-moves in 20 sessions (4 dn/4 up); latest 2026-08-19 -3.86% |
|   | DIRECTION-STREAK | MEDIUM | DOWN | 5 consecutive down closes through 2026-08-24 (-12.4% over run) |
| **MKSI** (net -2) | GAP-MOVES>3PCT | HIGH | MIXED | 12 >3% day-moves in 20 sessions (6 dn/6 up); latest 2026-08-19 -6.21% |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 13 Form 4s/92d, 2 in last 14d, 3 in last 30d; latest 2026-08-18 (6d ago) |
|   | INSIDER-NET-SELL (note-sourced) | MEDIUM | NEGATIVE | 1 insider-sale refs; e.g. "insider selling)" |
| **RTX** (net +2) | BACKLOG-DISCLOSED | HIGH | POSITIVE-VISIBILITY | 2 backlog refs; e.g. "backlog** at end-2024 (superseded 2026-04-29 per voo-analysis-2026-04-29 -- see Claims from voo-" |
|   | FORM4-ACTIVITY | LOW | DIRECTION-UNKNOWN (dates only) | 5 Form 4s/92d, 1 in last 14d, 4 in last 30d; latest 2026-08-19 (5d ago) |
|   | GAP-MOVES>3PCT | LOW | DOWN | 1 >3% day-moves in 20 sessions (1 dn/0 up); latest 2026-08-20 -3.66% |
| **GEV** (net -2) | BACKLOG-DISCLOSED | MEDIUM | POSITIVE-VISIBILITY | 1 backlog refs; e.g. "backlog contribution Q1-26 GEV consolidation $5B (HIGH, per [[ref-ai-power-grid-deep-dive]])" |
|   | DIRECTION-STREAK | MEDIUM | DOWN | 5 consecutive down closes through 2026-08-24 (-12.9% over run) |
|   | GAP-MOVES>3PCT | MEDIUM | DOWN | 4 >3% day-moves in 20 sessions (3 dn/1 up); latest 2026-08-18 -6.90% |
| **ALGO-USD** (net +2) | GAP-MOVES>3PCT | MEDIUM | UP | 5 >3% day-moves in 20 sessions (2 dn/3 up); latest 2026-08-22 -5.14% |
| **QNT-USD** (net +2) | GAP-MOVES>3PCT | MEDIUM | UP | 4 >3% day-moves in 20 sessions (1 dn/3 up); latest 2026-08-22 -5.15% |
| **SMH** (net -2) | GAP-MOVES>3PCT | MEDIUM | DOWN | 5 >3% day-moves in 20 sessions (3 dn/2 up); latest 2026-08-18 -4.09% |
| **TSLA** (net +2) | GAP-MOVES>3PCT | MEDIUM | UP | 5 >3% day-moves in 20 sessions (0 dn/5 up); latest 2026-08-21 +5.14% |
| **GD** (net +1) | 8K-FREQ-SPIKE | MEDIUM | NEUTRAL/CATALYST-CLOCK | 3 8-Ks in 92d vs 1/92d baseline; latest 2026-08-07 (17d ago) |
|   | BACKLOG-DISCLOSED | MEDIUM | POSITIVE-VISIBILITY | 1 backlog refs; e.g. "backlog ~$50B (HIGH, per ref-defense-aerospace-space-economy-deep-dive)" |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 20 Form 4s/92d, 6 in last 14d, 10 in last 30d; latest 2026-08-17 (7d ago) |
|   | GAP-MOVES>3PCT | LOW | DOWN | 1 >3% day-moves in 20 sessions (1 dn/0 up); latest 2026-07-29 -3.11% |
| **NVDA** (net -1) | DIRECTION-STREAK | HIGH | DOWN | 7 consecutive down closes through 2026-08-24 (-6.7% over run) |
|   | 13F-HR-PRESENCE | MEDIUM | INSTITUTIONAL-EYES-ON | 1 Q2-26 13F-HR report(s); history: 2026-05-15, 2026-08-14 |
|   | 8K-FREQ-SPIKE | MEDIUM | NEUTRAL/CATALYST-CLOCK | 4 8-Ks in 92d vs 1.5/92d baseline; latest 2026-08-17 (7d ago) |
|   | CAPEX-RAISE | MEDIUM | NEUTRAL/SPEND-COMMITMENT | 1 capex-raise refs; e.g. "capex $175-185B (2x trigger) BULL extreme CONFIRMED up" |
|   | CONTRACT-AWARD | MEDIUM | POSITIVE | 1 contract refs; e.g. "$100B deal + cumulative $1T 2025-2027 Jensen statement" |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 23 Form 4s/92d, 1 in last 14d, 2 in last 30d; latest 2026-08-12 (12d ago) |
|   | GAP-MOVES>3PCT | MEDIUM | UP | 3 >3% day-moves in 20 sessions (1 dn/2 up); latest 2026-08-12 +3.03% |
|   | INSIDER-NET-SELL (note-sourced) | MEDIUM | NEGATIVE | sells 3x buy count, 4.4x dollar magnitude; sustained absence of insider buying |
| **SNPS** (net -1) | 8K-FREQ-SPIKE | MEDIUM | NEUTRAL/CATALYST-CLOCK | 3 8-Ks in 92d vs 1.5/92d baseline; latest 2026-08-12 (12d ago) |
|   | DIRECTION-STREAK | MEDIUM | DOWN | 6 consecutive down closes through 2026-08-24 (-7.4% over run) |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 10 Form 4s/92d, 1 in last 14d, 1 in last 30d; latest 2026-08-17 (7d ago) |
|   | GAP-MOVES>3PCT | LOW | UP | 2 >3% day-moves in 20 sessions (0 dn/2 up); latest 2026-08-04 +3.01% |
| **CDNS** (net -1) | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 13 Form 4s/92d, 2 in last 14d, 3 in last 30d; latest 2026-08-19 (5d ago) |
|   | GAP-MOVES>3PCT | LOW | DOWN | 1 >3% day-moves in 20 sessions (1 dn/0 up); latest 2026-07-29 -3.47% |
| **CRWV** (net +1) | FORM4-ACTIVITY | HIGH | DIRECTION-UNKNOWN (dates only) | 37 Form 4s/92d, 29 in last 14d, 37 in last 30d; latest 2026-08-21 (3d ago) |
|   | GAP-MOVES>3PCT | HIGH | UP | 9 >3% day-moves in 20 sessions (4 dn/5 up); latest 2026-08-18 -12.10% |
|   | CAPEX-RAISE | MEDIUM | NEUTRAL/SPEND-COMMITMENT | 1 capex-raise refs; e.g. "capex $30-35B (per CRWV Q4 2025 call) (per [[ref-ai-sup" |
|   | DIRECTION-STREAK | MEDIUM | DOWN | 5 consecutive down closes through 2026-08-24 (-19.2% over run) |
| **MSFT** (net -1) | INSIDER-NET-SELL (note-sourced) | HIGH | NEGATIVE | 11 insider-sale refs; e.g. "insiders NET SELLING -- Althoff $7" |
|   | CAPEX-RAISE | MEDIUM | NEUTRAL/SPEND-COMMITMENT | 7 capex-raise refs; e.g. "capex revised UP" |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 34 Form 4s/92d, 1 in last 14d, 3 in last 30d; latest 2026-08-17 (7d ago) |
|   | GAP-MOVES>3PCT | MEDIUM | UP | 4 >3% day-moves in 20 sessions (1 dn/3 up); latest 2026-08-17 -3.04% |
| **PLTR** (net +1) | INSIDER-NET-SELL (note-sourced) | HIGH | NEGATIVE | $571.8M insider sells / 0 buys at the lows; Burry short via puts |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 14 Form 4s/92d, 3 in last 14d, 4 in last 30d; latest 2026-08-19 (5d ago) |
|   | GAP-MOVES>3PCT | MEDIUM | UP | 5 >3% day-moves in 20 sessions (1 dn/4 up); latest 2026-08-21 +3.44% |
|   | GUIDANCE-RAISE | MEDIUM | POSITIVE | 1 raise refs; e.g. "raised FY guide" |
| **TSM** (net +1) | FORM4-ACTIVITY | HIGH | DIRECTION-UNKNOWN (dates only) | 40 Form 4s/92d, 31 in last 14d, 35 in last 30d; latest 2026-08-20 (4d ago) |
|   | GUIDANCE-RAISE | HIGH | POSITIVE | 2 raise refs; e.g. "RAISED FY26" |
|   | GAP-MOVES>3PCT | MEDIUM | DOWN | 3 >3% day-moves in 20 sessions (2 dn/1 up); latest 2026-08-18 -4.07% |
| **DTCR** (net +1) | GAP-MOVES>3PCT | LOW | UP | 2 >3% day-moves in 20 sessions (0 dn/2 up); latest 2026-08-04 +3.20% |
| **FN** (net +1) | GAP-MOVES>3PCT | HIGH | UP | 13 >3% day-moves in 20 sessions (6 dn/7 up); latest 2026-08-24 -3.12% |
|   | DIRECTION-STREAK | MEDIUM | DOWN | 5 consecutive down closes through 2026-08-24 (-29.3% over run) |
| **IAU** (net +1) | GAP-MOVES>3PCT | LOW | UP | 2 >3% day-moves in 20 sessions (0 dn/2 up); latest 2026-08-19 +3.83% |
| **ONTO** (net +1) | GAP-MOVES>3PCT | HIGH | UP | 15 >3% day-moves in 20 sessions (7 dn/8 up); latest 2026-08-24 -4.85% |
|   | DIRECTION-STREAK | MEDIUM | DOWN | 5 consecutive down closes through 2026-08-24 (-20.5% over run) |
| **QQQ** (net +1) | GAP-MOVES>3PCT | LOW | UP | 2 >3% day-moves in 20 sessions (0 dn/2 up); latest 2026-08-04 +3.40% |
| **VDE** (net +1) | GAP-MOVES>3PCT | LOW | UP | 1 >3% day-moves in 20 sessions (0 dn/1 up); latest 2026-08-10 +4.74% |
| **VGT** (net +1) | GAP-MOVES>3PCT | LOW | UP | 2 >3% day-moves in 20 sessions (0 dn/2 up); latest 2026-08-04 +4.35% |
| **CEG** (net +0) | 8K-FREQ-SPIKE | MEDIUM | NEUTRAL/CATALYST-CLOCK | 4 8-Ks in 92d vs 3/92d baseline; latest 2026-08-06 (18d ago) |
|   | GAP-MOVES>3PCT | MEDIUM | MIXED | 4 >3% day-moves in 20 sessions (2 dn/2 up); latest 2026-08-18 -3.94% |
| **DELL** (net +0) | GAP-MOVES>3PCT | HIGH | MIXED | 10 >3% day-moves in 20 sessions (5 dn/5 up); latest 2026-08-19 -6.64% |
|   | 8K-FREQ-SPIKE | MEDIUM | WATCH | 4 8-Ks in 92d vs 0/92d baseline; latest 2026-07-06 (49d ago) |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 36 Form 4s/92d, 0 in last 14d, 0 in last 30d; latest 2026-07-24 (31d ago) |
| **DUK** (net +0) | 8K-FREQ-SPIKE | MEDIUM | NEUTRAL/CATALYST-CLOCK | 5 8-Ks in 92d vs 4/92d baseline; latest 2026-08-13 (11d ago) |
| **MRAM** (net +0) | GAP-MOVES>3PCT | HIGH | MIXED | 16 >3% day-moves in 20 sessions (8 dn/8 up); latest 2026-08-24 -4.91% |
|   | 8K-FREQ-SPIKE | MEDIUM | NEUTRAL/CATALYST-CLOCK | 3 8-Ks in 92d vs 2.5/92d baseline; latest 2026-08-12 (12d ago) |
|   | FORM4-ACTIVITY | LOW | DIRECTION-UNKNOWN (dates only) | 8 Form 4s/92d, 1 in last 14d, 4 in last 30d; latest 2026-08-12 (12d ago) |
| **MRVL** (net +0) | 8K-FREQ-SPIKE | HIGH | NEUTRAL/CATALYST-CLOCK | 5 8-Ks in 92d vs 0/92d baseline; latest 2026-08-19 (5d ago) |
|   | GAP-MOVES>3PCT | HIGH | MIXED | 14 >3% day-moves in 20 sessions (7 dn/7 up); latest 2026-08-24 -4.01% |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 28 Form 4s/92d, 2 in last 14d, 3 in last 30d; latest 2026-08-17 (7d ago) |
|   | GUIDANCE-RAISE | MEDIUM | POSITIVE | 1 raise refs; e.g. "RAISED FY27 revenue outlook" |
|   | INSIDER-NET-SELL (note-sourced) | MEDIUM | NEGATIVE | 1 insider-sale refs; e.g. "insider cluster-SELL: 6 C-suite (CEO Murphy 5 sales, COO, CFO, DC-Pres, GC), 16 Form-4 sales, ZERO b" |
| **NEE** (net +0) | 8K-FREQ-SPIKE | HIGH | NEUTRAL/CATALYST-CLOCK | 8 8-Ks in 92d vs 3.5/92d baseline; latest 2026-08-11 (13d ago) |
|   | FORM4-ACTIVITY | LOW | DIRECTION-UNKNOWN (dates only) | 5 Form 4s/92d, 1 in last 14d, 1 in last 30d; latest 2026-08-18 (6d ago) |
| **PPL** (net +0) | 8K-FREQ-SPIKE | MEDIUM | NEUTRAL/CATALYST-CLOCK | 4 8-Ks in 92d vs 4/92d baseline; latest 2026-08-17 (7d ago) |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 10 Form 4s/92d, 0 in last 14d, 0 in last 30d; latest 2026-07-23 (32d ago) |
| **SO** (net +0) | 8K-FREQ-SPIKE | HIGH | NEUTRAL/CATALYST-CLOCK | 5 8-Ks in 92d vs 1/92d baseline; latest 2026-08-06 (18d ago) |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 17 Form 4s/92d, 0 in last 14d, 2 in last 30d; latest 2026-08-07 (17d ago) |
| **SPCX** (net +0) | 8K-FREQ-SPIKE | HIGH | NEUTRAL/CATALYST-CLOCK | 8 8-Ks in 92d vs 0/92d baseline; latest 2026-08-14 (10d ago) |
| **TLN** (net +0) | GAP-MOVES>3PCT | HIGH | MIXED | 6 >3% day-moves in 20 sessions (3 dn/3 up); latest 2026-08-18 -11.00% |
|   | 8K-FREQ-SPIKE | MEDIUM | NEUTRAL/CATALYST-CLOCK | 3 8-Ks in 92d vs 2/92d baseline; latest 2026-08-05 (19d ago) |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 19 Form 4s/92d, 0 in last 14d, 0 in last 30d; latest 2026-07-15 (40d ago) |
| **USAR** (net +0) | 8K-FREQ-SPIKE | HIGH | NEUTRAL/CATALYST-CLOCK | 11 8-Ks in 92d vs 3/92d baseline; latest 2026-08-10 (14d ago) |
|   | GAP-MOVES>3PCT | HIGH | MIXED | 12 >3% day-moves in 20 sessions (6 dn/6 up); latest 2026-08-24 -5.04% |
|   | FORM4-ACTIVITY | LOW | DIRECTION-UNKNOWN (dates only) | 9 Form 4s/92d, 1 in last 14d, 1 in last 30d; latest 2026-08-21 (3d ago) |
| **CSCO** (net +0) | 13F-HR-PRESENCE | MEDIUM | INSTITUTIONAL-EYES-ON | 1 Q2-26 13F-HR report(s); history: 2026-04-15, 2026-07-13 |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 23 Form 4s/92d, 13 in last 14d, 13 in last 30d; latest 2026-08-20 (4d ago) |
|   | GAP-MOVES>3PCT | LOW | MIXED | 2 >3% day-moves in 20 sessions (1 dn/1 up); latest 2026-08-13 -8.40% |
| **LRCX** (net +0) | GAP-MOVES>3PCT | HIGH | MIXED | 10 >3% day-moves in 20 sessions (5 dn/5 up); latest 2026-08-19 -6.33% |
|   | CAPEX-RAISE | MEDIUM | NEUTRAL/SPEND-COMMITMENT | 2 capex-raise refs; e.g. "capex sup" |
|   | FORM4-ACTIVITY | LOW | DIRECTION-UNKNOWN (dates only) | 7 Form 4s/92d, 0 in last 14d, 2 in last 30d; latest 2026-08-07 (17d ago) |
| **NRG** (net +0) | GAP-MOVES>3PCT | HIGH | MIXED | 10 >3% day-moves in 20 sessions (5 dn/5 up); latest 2026-08-20 -4.33% |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 29 Form 4s/92d, 0 in last 14d, 15 in last 30d; latest 2026-08-05 (19d ago) |
| **ORCL** (net +0) | CREDIT-DOWNGRADE | HIGH | NEGATIVE | 7 credit-stress refs; e.g. "S&P cut to BBB-, one notch above junk, 7/09); do not chase the fres" |
|   | GAP-MOVES>3PCT | HIGH | UP | 6 >3% day-moves in 20 sessions (2 dn/4 up); latest 2026-08-21 +3.10% |
|   | CONTRACT-AWARD | MEDIUM | POSITIVE | 2 contract refs; e.g. "MSA anchor customer and AMD's 50K-GPU MI450 supercluster buyer -- ORCL stress reads through to both " |
|   | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 10 Form 4s/92d, 0 in last 14d, 1 in last 30d; latest 2026-07-28 (27d ago) |
|   | INSIDER-NET-SELL (note-sourced) | MEDIUM | NEGATIVE | 0 buys / $16.3M sells 6mo incl EVP/GC -81% discretionary |
| **QNT** (net +0) | FORM4-ACTIVITY | MEDIUM | DIRECTION-UNKNOWN (dates only) | 13 Form 4s/92d, 0 in last 14d, 0 in last 30d; latest 2026-07-21 (34d ago) |
| **ABBNY** (net +0) | GAP-MOVES>3PCT | LOW | MIXED | 2 >3% day-moves in 20 sessions (1 dn/1 up); latest 2026-08-18 -3.06% |
| **COHR** (net +0) | GAP-MOVES>3PCT | HIGH | MIXED | 14 >3% day-moves in 20 sessions (7 dn/7 up); latest 2026-08-24 -5.23% |
| **NOC** (net +0) | GAP-MOVES>3PCT | LOW | MIXED | 2 >3% day-moves in 20 sessions (1 dn/1 up); latest 2026-08-20 -3.26% |
| **ONDO-USD** (net +0) | GAP-MOVES>3PCT | HIGH | MIXED | 6 >3% day-moves in 20 sessions (3 dn/3 up); latest 2026-08-23 +4.73% |
| **XAR** (net +0) | GAP-MOVES>3PCT | MEDIUM | MIXED | 4 >3% day-moves in 20 sessions (2 dn/2 up); latest 2026-08-20 -4.34% |

## 7. Refresh procedure

1. Re-pull filings into `wiki/investing/filings/*/-filings.json` and refresh
   factor-store bars (`osanwe-weekly-calibration` ingest step).
2. Re-run the scanner (kept at
   `Efforts/osanwe-v2-overhaul/_work/tmp-altsignals/compute_signals.py` +
   `curate.py`) and regenerate this file; update the GENERATED date.
3. Re-check Section 2 limitations before re-weighting any rule.
---

## 8. Verification pass: strict-threshold rescan + full 107-ticker dashboard (2026-08-24, second writer)

An independent verification subagent re-mined the filings JSONs and bars
with STRICTER thresholds than the primary pass, to see which signals
survive tightening. Primary sections above are untouched; this appendix
adds the stricter cut and a compact per-ticker dashboard covering ALL 107
store instruments (the primary dashboard's long-form rows cover the 106
that fired; here every ticker gets one row, including ETFs and ADRs with
no EDGAR filer).

### 8a. Strict re-run results

- 8-K SPIKES (calendar-month count >= max(3, 2x trailing median incl.
  zero months)): 31 spike-months across 22 issuers since Nov-2024. The
  live ones as of generation: COIN Jul-2026 (3 vs med 1), EQIX Jul-2026
  (3 vs 1), SO Aug-2026 (3 by Aug-06 vs 1). Historical spikes that marked
  real catalysts: SPCX Jun-2026 (6 filings), USAR Jun-2026 (6), DUK
  Mar-2026 (5), AEIS May-2026 (5), INTC Apr-2026 (4). Confirms the
  primary rule fires on both distress and routine deal-flow -- pair with
  entity notes before reading direction.
- FORM-4 CLUSTERS (>= 3 same-day Form 4s): present in 82 of 90 filers --
  same-day clusters are the NORM (scheduled 10b5-1 batches), confirming
  the primary pass's decision to treat them as compensation-grade noise.
  Leaderboard: CSCO/DELL/DLR/LHX 6 clusters each, RTX/NOW/NEE/MRAM/LITE/
  KLAC 5 each. Live comp-batch windows at generation: CRWV (4 on Aug-19,
  8 on Aug-21), LITE (5+5 on Aug-18/21), CSCO (7 on Aug-12, 5 on Aug-17),
  KLAC (6 on Aug-10).
- ISOLATED PAIRS (exactly 2 same-day): the discretionary-signal tier.
  Live examples: MU (2 on 2026-08-20 after the -5.8% tape day), NBIS,
  AMZN, INTC. Weak evidence class: dates only, no transaction codes in
  store -- treat as "look closer", never as buy/sell.
- FILING-GAP ANALYSIS: genuine anomalies are QQQ (last row 2014 -- puller
  artifact, exclude), ASML and ATEYY (ADR 20-F cadence, silence is
  structural), then AMBA (45d), AVGO (41d), GEV (33d), TSLA (32d), DELL
  (31d) as of 2026-08-24 -- all inside normal quarterly-report spacing,
  so NO true unusual-silence alerts fire today. Freshest filers: AMD/
  AAOI/CRDO/CRWV/LITE all 2026-08-21.
- PRICE SIGNALS from bars (no volume column exists in the store -- the
  tasking's ">2x avg volume" is uncomputable as specified; substituted
  move-magnitude screens, consistent with primary Section 2):
  strict >= 5% single-day moves, trailing 90d: AAOI 39, SNDK 38, LITE 32,
  MRAM 32, COHR 31, CRDO/MRVL/ONTO 30, ALAB/FLNC 28 -- versus SPY 0 and
  VOO 0. The semis/memory complex IS the high-tape cohort; >3% gap days
  cluster there too (MU 26 >=5% moves in 90d).

### 8b. SIGNAL DASHBOARD -- one row per store instrument (107 rows)

Columns: ticker | total 8-K / Form-4 rows in filings JSON | days since
last filing of any form | >= 3% single-day moves in last 90d | latest big
move | flags. Flags: CAT8K = 8-K spike month current or prior calendar
month; COMP4 = >= 6 insider filings in same-day clusters within 30d;
ISO4 = isolated Form-4 pairs or small clusters <= 30d; QUIET = no filing
in 30+d (domestic filer); STALE = known-stale source (ADRs/QQQ); TAPE =
>= 3 big moves in 90d or a big move within 3 sessions; CALM = none.

| AAOI | 5 | 34 | 3 | 20 | -12.1% 2026-08-24 | ISO4,TAPE |
| ABBNY | - | - | - | 7 | -3.1% 2026-08-18 | TAPE |
| AEIS | 7 | 31 | 4 | 29 | -6.4% 2026-08-19 | TAPE |
| AEP | 5 | 33 | 20 | 1 | -3.8% 2026-08-21 | ISO4,TAPE |
| ALAB | 3 | 35 | 5 | 15 | -12.0% 2026-08-05 | ISO4,TAPE |
| ALGO-USD | - | - | - | 5 | 10.7% 2026-08-21 | TAPE |
| AMAT | 5 | 32 | 4 | 22 | 5.5% 2026-08-17 | TAPE |
| AMBA | 5 | 32 | 45 | 17 | 16.1% 2026-07-31 | QUIET,TAPE |
| AMD | 4 | 34 | 3 | 19 | 6.5% 2026-08-14 | COMP4,TAPE |
| AMKR | 3 | 36 | 5 | 22 | -7.2% 2026-08-19 | ISO4,TAPE |
| AMZN | 8 | 28 | 5 | 7 | 4.6% 2026-08-03 | ISO4,TAPE |
| ANET | 2 | 37 | 10 | 13 | 6.4% 2026-08-12 | ISO4,TAPE |
| APH | 9 | 28 | 18 | 18 | -6.6% 2026-08-18 | ISO4,TAPE |
| ARM | 0 | 30 | 6 | 19 | -6.7% 2026-08-18 | TAPE |
| ASMIY | - | - | - | 13 | -5.4% 2026-08-18 | TAPE |
| ASML | 0 | 0 | 1658 | 16 | -4.3% 2026-08-18 | STALE,TAPE |
| ATEYY | 0 | 0 | 2209 | 23 | -5.2% 2026-08-20 | STALE,TAPE |
| AVAV | 5 | 33 | 5 | 22 | -4.9% 2026-08-24 | TAPE |
| AVGO | 7 | 31 | 41 | 16 | -4.6% 2026-08-19 | QUIET,TAPE |
| BAH | 7 | 31 | 7 | 17 | -3.1% 2026-08-20 | COMP4,TAPE |
| BE | 5 | 32 | 6 | 17 | -10.0% 2026-08-18 | ISO4,TAPE |
| BTC-USD | 17 | 0 | 20 | 8 | 7.3% 2026-08-21 | TAPE |
| BWXT | 3 | 34 | 11 | 17 | -3.2% 2026-08-24 | TAPE |
| CDNS | 3 | 35 | 5 | 7 | -3.5% 2026-07-29 | ISO4,TAPE |
| CEG | 11 | 26 | 11 | 6 | 4.2% 2026-08-03 | TAPE |
| COHR | 6 | 31 | 4 | 28 | -6.2% 2026-08-19 | TAPE |
| COIN | 7 | 31 | 6 | 5 | 8.2% 2026-08-21 | CAT8K,TAPE |
| CRDO | 1 | 38 | 3 | 20 | -13.0% 2026-08-18 | ISO4,TAPE |
| CRWV | 2 | 37 | 3 | 7 | -12.1% 2026-08-18 | COMP4,TAPE |
| CSCO | 3 | 34 | 4 | 10 | -8.4% 2026-08-13 | COMP4,TAPE |
| DELL | 4 | 36 | 31 | 22 | -6.6% 2026-08-19 | QUIET,TAPE |
| DLR | 10 | 27 | 5 | 5 | 3.3% 2026-08-12 | TAPE |
| DTCR | - | - | - | 6 | 3.2% 2026-08-04 | TAPE |
| DUK | 13 | 25 | 11 | 1 | 3.0% 2026-07-02 | CALM |
| EQIX | 8 | 30 | 4 | 5 | 3.6% 2026-08-12 | CAT8K,TAPE |
| ETN | 7 | 31 | 10 | 24 | -5.3% 2026-08-18 | TAPE |
| FLNC | 7 | 30 | 19 | 11 | -9.2% 2026-08-05 | TAPE |
| FN | 7 | 29 | 6 | 23 | -5.8% 2026-08-19 | ISO4,TAPE |
| GD | 5 | 33 | 7 | 4 | -3.1% 2026-07-29 | ISO4,TAPE |
| GEV | 6 | 31 | 33 | 11 | -6.9% 2026-08-18 | QUIET,TAPE |
| GFS | 0 | 40 | 4 | 20 | -6.6% 2026-08-18 | COMP4,TAPE |
| GOOGL | 2 | 36 | 13 | 11 | -3.8% 2026-08-11 | COMP4,TAPE |
| HBAR-USD | - | - | - | 2 | 8.6% 2026-08-21 | TAPE |
| HII | 3 | 35 | 13 | 11 | -3.3% 2026-08-20 | ISO4,TAPE |
| HIMS | 3 | 36 | 4 | 11 | -8.2% 2026-08-24 | COMP4,TAPE |
| HPE | 5 | 34 | 20 | 20 | -4.6% 2026-08-19 | TAPE |
| HUBB | 7 | 31 | 6 | 10 | -4.1% 2026-08-18 | ISO4,TAPE |
| IAU | 8 | 0 | 18 | 6 | 3.8% 2026-08-19 | TAPE |
| INTC | 7 | 29 | 10 | 23 | -6.6% 2026-08-18 | ISO4,TAPE |
| ITA | - | - | - | 4 | -3.5% 2026-08-20 | TAPE |
| KLAC | 2 | 37 | 10 | 21 | -5.3% 2026-08-18 | COMP4,TAPE |
| KTOS | 3 | 35 | 4 | 21 | -5.2% 2026-08-24 | ISO4,TAPE |
| LHX | 7 | 31 | 7 | 7 | -4.6% 2026-08-17 | ISO4,TAPE |
| LINK-USD | 19 | 11 | 11 | 5 | 12.3% 2026-08-21 | ISO4,TAPE |
| LITE | 6 | 32 | 3 | 27 | 6.2% 2026-08-20 | COMP4,TAPE |
| LMT | 3 | 35 | 7 | 5 | 10.5% 2026-07-23 | TAPE |
| LRCX | 4 | 33 | 17 | 28 | -6.3% 2026-08-19 | TAPE |
| MBLY | 14 | 21 | 12 | 8 | 6.9% 2026-08-04 | TAPE |
| META | 1 | 38 | 4 | 13 | -4.4% 2026-08-18 | COMP4,TAPE |
| MKSI | 4 | 33 | 6 | 21 | -6.2% 2026-08-19 | TAPE |
| MP | 4 | 33 | 17 | 12 | 9.1% 2026-08-21 | TAPE |
| MRAM | 9 | 28 | 12 | 24 | -7.1% 2026-08-18 | ISO4,TAPE |
| MRVL | 5 | 34 | 5 | 27 | 5.8% 2026-08-20 | ISO4,TAPE |
| MSFT | 3 | 35 | 7 | 13 | -3.0% 2026-08-17 | TAPE |
| MU | 6 | 32 | 4 | 27 | -5.8% 2026-08-24 | ISO4,TAPE |
| NBIS | 0 | 24 | 6 | 13 | 34.1% 2026-08-12 | ISO4,TAPE |
| NEE | 15 | 23 | 6 | 1 | -3.9% 2026-06-01 | CALM |
| NOC | 5 | 33 | 3 | 6 | -3.3% 2026-08-20 | TAPE |
| NOW | 2 | 37 | 5 | 21 | 6.5% 2026-08-19 | COMP4,TAPE |
| NRG | 4 | 34 | 19 | 12 | -4.3% 2026-08-20 | COMP4,TAPE |
| NVDA | 7 | 30 | 7 | 3 | -5.0% 2026-07-27 | TAPE |
| OKLO | 4 | 33 | 7 | 18 | -5.7% 2026-08-18 | ISO4,TAPE |
| ONDO-USD | - | - | - | 6 | 11.6% 2026-08-21 | TAPE |
| ONTO | 13 | 23 | 14 | 29 | -10.2% 2026-08-18 | TAPE |
| ORCL | 9 | 28 | 27 | 23 | -3.6% 2026-08-14 | TAPE |
| PLTR | 3 | 34 | 5 | 10 | 10.3% 2026-08-07 | TAPE |
| PPA | - | - | - | 3 | -3.2% 2026-08-20 | TAPE |
| PPL | 12 | 26 | 7 | 1 | 3.6% 2026-07-02 | CALM |
| QCOM | 5 | 33 | 3 | 22 | 4.7% 2026-08-07 | TAPE |
| QNT-USD | 1 | 13 | 11 | 1 | 7.2% 2026-08-21 | TAPE |
| QQQ | 2 | 0 | 4368 | 6 | 3.4% 2026-08-04 | STALE,TAPE |
| RKLB | 12 | 26 | 6 | 13 | 9.5% 2026-08-07 | TAPE |
| RTX | 4 | 34 | 5 | 7 | -3.7% 2026-08-20 | ISO4,TAPE |
| SMCI | 6 | 34 | 5 | 15 | 19.0% 2026-08-12 | COMP4,TAPE |
| SMH | - | - | - | 22 | -4.1% 2026-08-18 | TAPE |
| SMR | 7 | 30 | 4 | 5 | 13.3% 2026-07-30 | TAPE |
| SNDK | 6 | 31 | 7 | 18 | 13.7% 2026-08-13 | TAPE |
| SNPS | 7 | 31 | 7 | 7 | 4.4% 2026-07-31 | TAPE |
| SO | 7 | 31 | 17 | 2 | 3.0% 2026-07-02 | CAT8K |
| SOL-USD | - | - | - | 3 | 10.8% 2026-08-19 | TAPE |
| SPCX | 8 | 1 | 10 | 6 | 9.6% 2026-08-12 | TAPE |
| SPY | - | - | - | 0 | 3.3% 2025-05-12 | CALM |
| TLN | 7 | 31 | 19 | 15 | -11.0% 2026-08-18 | TAPE |
| TSLA | 12 | 22 | 32 | 6 | -14.5% 2026-07-23 | QUIET,TAPE |
| TSM | 0 | 40 | 4 | 15 | -4.1% 2026-08-18 | COMP4,TAPE |
| USAR | 17 | 21 | 3 | 15 | 12.6% 2026-08-21 | TAPE |
| VDE | - | - | - | 2 | 4.7% 2026-08-10 | CALM |
| VGT | - | - | - | 6 | 4.4% 2026-08-04 | TAPE |
| VOLT | - | - | - | 10 | -3.9% 2026-08-18 | TAPE |
| VOO | - | - | - | 0 | 3.3% 2025-05-12 | CALM |
| VRT | 8 | 30 | 26 | 14 | -6.8% 2026-08-18 | TAPE |
| VST | 8 | 29 | 14 | 7 | -8.2% 2026-08-04 | TAPE |
| WBD | 8 | 30 | 6 | 0 | 6.3% 2025-12-05 | COMP4 |
| WDC | 4 | 35 | 10 | 30 | -5.8% 2026-08-24 | ISO4,TAPE |
| XAR | - | - | - | 7 | -4.3% 2026-08-20 | TAPE |
| XLM-USD | - | - | - | 15 | 11.2% 2026-08-21 | TAPE |
| XRP-USD | - | - | - | 6 | 14.6% 2026-08-21 | TAPE |

### 8c. Reading notes

- 50 tickers carry TAPE alone; 25 add ISO4; 14 add COMP4; only 3 fire
  CAT8K (COIN, EQIX, SO) and only DUK/PPL/SO-class utilities sit fully
  CALM -- consistent with a late-cycle tape where volatility concentrates
  in the AI complex while the funding leg stays quiet.
- The three CAT8K names deserve first reads: SO's Aug-2026 burst (3 8-Ks
  in four sessions) alongside its 17 Form 4s; EQIX around its Jul-2026
  cluster; COIN riding crypto-beta TAPE plus a Jul-2026 8-K trio.
- Rows with "-" in filing columns are ETFs/crypto/ADRs with no EDGAR
  filer mapping in the vault (SMH, SPY, VOO, VGT, ITA, PPA, XAR, VDE,
  ABBNY, ASMIY, DTCR, VOLT, USAR has filings but thin history, all
  *-USD except BTC/LINK/QNT which map to BTC/LINK/QNT dirs).
- Regeneration: re-run the scanner per Section 7, then this appendix's
  strict rules (thresholds stated inline above); anchors are bars through
  2026-08-24 and filings through 2026-08-21.
