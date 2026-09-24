---
aliases: [alternative-data-signals]
categories: [sources]
type: reference
target_path: Atlas/sources/investing/ref-alternative-data-signals.md
created: 2026-08-24
updated: 2026-08-24
status: active
confidence: high
tags:
  - topic/alternative-data
  - topic/edgar-filings
  - topic/insider-signals
  - topic/institutional-positioning
  - topic/signal-dashboard
---

# ref-alternative-data-signals -- non-price signal dashboard, all 107 instruments

Cross-instrument ALTERNATIVE-DATA reference computed from every non-price source in
the vault: EDGAR filing metadata (8-K frequency spikes), entity-note event mining
(backlog / guidance / PPA / management / litigation), wave-analysis conviction +
kill-criteria proximity, and factor-store close-series microstructure (gap days,
direction streaks, vol-regime shifts). Every number is recomputable from the cited
vault file; no network, no external data.

- As-of: 2026-08-24 (factor store max bar 2026-08-24; filings store latest 2026-08-21)
- Universe: 107 instruments (factors.db `bars`); EDGAR flow covers 90 tickers
  (crypto + pure ETF wrappers have no SEC filer); curated evidence covers the
  ~45 names with substantive vault notes.
- Sources mined this build:
  - `_flow_per_ticker.json` (EDGAR metadata, 90 tickers, 3,388 filings)
  - `Efforts/osanwe-v2-overhaul/_work/factors.db` bars table (130,494 rows)
  - `Efforts/osanwe-v2-overhaul/_work/wave*-analysis.md` (51 files, 2026-08-24)
  - `wiki/entities/tickers/*.md` (108 entity notes)
  - `wiki/investing/analyses/*.md` (117 dated analyses)

## REGENERATE

```
python <HOME>/_build_dash.py        # recompute k8 spikes + streaks from stores
```
Curated evidence rows were hand-mined this session; re-mine after any new
/invest cycle. Factor-store rules are close-only (bars carry no volume column),
so the volume-based rule degrades to a gap/streak proxy -- see S4 note.

---

## Signal families and detection rules

### S1. EDGAR 8-K frequency spike (distress/catalyst)
- RULE: count 8-Ks in trailing 60d vs that ticker's own prior-180d monthly rate.
  FIRE if recent >= 4, or recent >= 3 with ratio >= 3x baseline. Strength HIGH at
  >= 5 recent or ratio >= 6; MED otherwise.
- DIRECTION is content-dependent: an earnings/catalyst cluster reads POSITIVE,
  a distress/governance cluster NEGATIVE. Metadata alone cannot score direction;
  flagged names need the filing opened before acting.

### S2. Form 4 insider direction (entity-note evidence)
- RULE: discretionary (non-10b5-1) cluster of >= 3 insiders OR zero-buys-with-
  heavy-sells over 6mo = BEAR distribution. Clean discretionary cluster BUYS into
  weakness = BULL. 10b5-1-cadenced sells are NEUTRAL by vault convention
  (retraction precedent: NVDA 4/30 bear read retracted 6/03).
- Evidence: OpenInsider/Form-4 reads recorded inside wiki/investing/analyses and
  wiki/entities/tickers notes. Direction follows the LATEST analysis verdict per
  Tier-1 newer-supersedes-older.

### S3. 13F institutional interest trend (Dataroma-class reads)
- RULE: magnitude-weighted adds/exits among tracked superinvestors. BULL =
  net conviction ADDs (>= 2 managers or one >= 10% portfolio weight). BEAR =
  conviction exits/reductions. MIXED = breadth-vs-magnitude conflict. Staleness
  cap: Q+45d lag means all Q1-vintage reads are STALE after mid-August.

### S4. Factor-store price microstructure (close-only proxy)
- RULES on factors.db closes (volume column does not exist in this store):
  - gap-proxy day: |close-to-close move| >= 3%
  - direction streak: consecutive same-sign daily closes (current run >= 5)
  - vol regime: RV20 vs RV60 shift > 1.25x = expansion (event-driven tape)
- NOTE: the task's ">2x average volume" rule is NOT computable from the current
  store (no volume column). Gap-day clusters + RV expansion are the volume-spike
  proxies actually available; ingest OHLCV via the weekly calibration job to
  enable the literal rule.

### S5. Entity-event signals (backlog / guidance / PPA / contracts / management / litigation)
- RULE: mined $ amounts and events from entity notes; direction POS when the
  event extends revenue visibility or raises guides; NEG on contract loss,
  dilution flags, governance breaks, unresolved litigation; WATCH where the
  event cuts both ways.

### S6. Wave conviction + kill-criteria proximity (analyst-consensus layer)
- RULE: frontmatter `conviction:` across the 51 wave analyses (0-100 scale).
  Kill proximity: explicit WATCH/ARMED/partially-fired kill lines in the Kill
  Criteria section. Conviction >= 40 = elevated analyst-layer agreement.

---

## SIGNAL DASHBOARD (all names with at least one active alternative-data signal)

Strength: H/M/L = HIGH/MED/LOW. Dir: + positive / - negative / o mixed-watch.

### S1 -- 8-K frequency spikes (metadata; open filings before acting)

| ticker | strength | dir | evidence |
|---|---|---|---|
| SPCX | H | ? | 8 x 8-K last 60d vs 0/mo base (IPO-period cluster; latest 8/14) |
| AVAV | H | ? | 5 x 8-K vs 0/mo base (latest 8/19; defense catalyst window) |
| DLR   | H | ? | 5 x 8-K vs 0.8/mo base (latest 8/19) |
| DUK   | H | ? | 5 x 8-K vs 1.3/mo base (latest 8/13) |
| SO    | H | ? | 5 x 8-K vs 0.3/mo base (latest 8/07) |
| USAR  | H | ? | 5 x 8-K vs 2.0/mo base (latest 8/21) |
| AMD   | H | ? | 4 x 8-K vs 0/mo base (latest 8/21) |
| DELL  | H | ? | 4 x 8-K vs 0/mo base (latest 7/24) |
| AVGO  | M | ? | 4 x 8-K vs 0.5/mo base (latest 7/14) |
| BAH   | M | ? | 4 x 8-K vs 0.5/mo base (latest 8/17) |
| EQIX  | M | ? | 4 x 8-K vs 0.7/mo base (latest 8/20) |
| MBLY  | M | ? | 4 x 8-K vs 0.8/mo base (latest 8/12) |
| NEE   | M | ? | 4 x 8-K vs 1.8/mo base (below-baseline; routine cadence) |
| NVDA  | M | ? | 4 x 8-K vs 0.5/mo base (latest 8/17) |
| RKLB  | M | ? | 4 x 8-K vs 1.3/mo base (latest 8/18) |
| VRT   | M | ? | 4 x 8-K vs 0.7/mo base (latest 7/29) |
| VST   | M | ? | 4 x 8-K vs 0.7/mo base (latest 8/10) |
| AAOI  | M | ? | 3 x 8-K vs 0.3/mo base (incl. 8/06 10-Q companion) |

### S2 -- Form 4 insider direction

| ticker | strength | dir | evidence source |
|---|---|---|---|
| AAOI | H | - | 5-exec discretionary cluster SELL $30.7M 6/12; 6mo 0 buys/39 sells $109.6M (aaoi-analysis-2026-06-18) |
| AMD  | H | - | 71 sells/0 buys $116.1M 6mo; Papermaster ATH selling; Su $43.7M (amd-analysis-2026-04-30/05-06) |
| AVGO | M | - | non-10b5-1 sell cluster broadened to $33.7M since 6/25, Brazeal 4th tranche 7/10 @ $401 (avgo-analysis-2026-07-16) |
| BE   | H | - | ZERO buys across +1,231% run; $120M+ sold; 4-officer cluster sale 6/16 (be-analysis-2026-06-29) |
| CRWV | H | - | C-suite sales $150.7M, no offsetting buys (waveT-crwv 2026-08-24) |
| MU   | M | - | 11+ C-suite sells vs 1 stale buy; Gomo director sell @$787 record; new Mehrotra plan (the memory-name analysis) |
| NBIS | H | - | 18 sells/8 insiders $135M zero buys 3/31-6/15; >$1M buy invalidation UNFIRED thru -49% DD (nbis-analysis-2026-06-18) |
| NVDA | M | o | 162 sells/$504.9M RECLASSIFIED 10b5-1 routine; bear read RETRACTED 6/03 (nvda-analysis-2026-06-03) |
| MRVL | M | o | earlier 6-C-suite cluster DE-ESCALATED to neutral 7/16 (all post-6/23 sales 10b5-1) (mrvl-analysis-2026-07-16) |
| OKLO | M | - | 34 sells/0 buys; co-founder $140M Jan + $27M/mo (oklo-analysis-2026-06-07) |
| ORCL | H | - | 0 buys/$74.7M sold 180d; Henley $63.7M @$159 pre-drop; EVP/GC -81% discretionary (orcl-analysis-2026-07-13) |
| PLTR | M | - | $571.8M sells/zero buys (stale 6/23 anchor; no refresh in vault) (pltr-analysis-2026-06-23) |
| RKLB | M | - | Director Slusky $25.7M discretionary sells May-Jun; zero buys 180d (rklb-analysis-2026-06-07) |
| SNDK | M | - | zero buys trailing 400d vs 8 discretionary sells $7.87M May-Jun (sndk-analysis-2026-08-17) |
| SMR  | H | - | Fluor FULL EXIT $1.83B; C-suite cashless-exercise sales same week Mar (smr-analysis-2026-06-07) |
| TSLA | M | - | zero discretionary buys 180d; CFO sells re-classified 10b5-1 (tsla-analysis-2026-06-18) |
| TSM  | M | + | FIRST clean discretionary cluster BUY: 3 VPs, 5 buys $895K into weakness 6/22-7/21 (tsm-analysis-2026-07-30) |
| VRT  | M | - | insider cluster 8 sellers ~$157M zero buys (waveE-vrt 2026-08-24) |
| WBD  | M | - | 9-insider cluster ~$250M Mar-2026; Zaslav $113M sale into deal (wbd-analysis-2026-06-07) |
| APH  | M | o | CEO/CFO OE-linked sells $131M BUT Director Livingston BUY $1.29M @$128.51 zone marker (aph-analysis-2026-06-18) |
| HIMS | M | - | all 12mo insider transactions are SALES; zero purchases (hims-analysis entity) |

### S3 -- 13F institutional interest

| ticker | strength | dir | evidence source |
|---|---|---|---|
| AMZN  | H | + | Tepper +98%/Klarman +47%/Ackman +19% (#1 holder) vs Berkshire exit; net accumulation (amzn-analysis-2026-06-23) |
| META  | H | + | Ackman 11.37% AUM concentrated BUY + Tepper +62% + ValueAct +36%; Viking/Polen/Third Point initiations (meta-analysis-2026-04-30) |
| MSFT  | H | + | Pershing NEW $2.1B SEC-confirmed + Dodge&Cox +61% $4.43B; value-cohort rotation IN; 40/65 hold rank #1 (msft-analysis-2026-07-25) |
| GOOGL | M | + | Berkshire +204% + $10B placement (~$41B combined); Li Lu 22.85%; PRE-PRINT vintage stale (googl-analysis-2026-07-23) |
| AVGO  | M | o | 6/29 net-bullish 3-manager adds -> downgraded MIXED 7/16 on insider cluster (avgo-analysis-2026-07-16) |
| TSM   | M | o | breadth distribution 16 reducers/-30.2% group stake BUT Tiger +49% ($1.88B) + Tepper +17% (tsm-analysis-2026-07-30) |
| MU    | M | o | a large manager raising it to its #1 holding vs single-bull fragility (the memory-name analysis) |
| NOW   | M | o | Polen +28% to 5.26% book + Akre/Vulcan adds vs 5-insider sell cluster; de-crowded (now-analysis-2026-06-12) |
| AMD   | M | - | Tepper -65.79%/Viking -10.5%/Mairs -22.5% reductions; ARK sell (amd-analysis-2026-04-30) |
| ORCL  | M | - | net REDUCE top holders; Polen -30%; 0 new positions (orcl-analysis-2026-07-13) |
| SNDK  | M | - | Tepper/Appaloosa SOLD 100% in Q2-CY26 13F while KEEPING MU (sndk-analysis-2026-08-17) |
| NVDA  | M | o | Loeb -93.6% exit vs Duan +91%/Egerton NEW/Tiger +9% (nvda-analysis-2026-06-23) |
| APH   | M | - | Egerton -22.6% top holder; Lone Pine -92% near-exit (aph-analysis-2026-06-18) |
| WBD   | M | - | Oakmark (largest/longest holder) -58% conviction cut (wbd-analysis-2026-06-07) |

### S4 -- factor-store microstructure (close-only proxy; as-of 2026-08-24)

Active streaks >= 5 sessions:

| ticker | strength | dir | streak | evidence |
|---|---|---|---|---|
| SOL-USD | M | + | 8 UP | consecutive up closes thru 8/24 (factors.db) |
| NVDA    | M | - | 7 DOWN | longest equity slide in the sample; pre-print bleed (factors.db) |
| NBIS    | M | - | 6 DOWN | post-unlock supply tape (factors.db) |
| HII     | M | - | 6 DOWN | defense-prime fade (factors.db) |
| PPA     | M | - | 6 DOWN | defense-ETF sleeve rotation (factors.db) |
| SNPS    | M | - | 6 DOWN | basing attempt failing (waveS-snps) |
| GEV     | M | - | 5 DOWN | power-layer pullback (factors.db) |
| AEIS    | L | - | 5 DOWN | semi-services fade (factors.db) |
| AEP     | L | - | 5 DOWN | utility drift (factors.db) |
| AMKR    | L | - | 5 DOWN | OSAT fade incl. -10.54% 8/18 (factors.db) |
| CRDO    | L | - | 5 DOWN | -13.03% 8/18 event day (factors.db) |
| CRWV    | L | - | 5 DOWN | -12.1% 8/18 after +19.28% 8/12 whipsaw (factors.db) |
| FN       | L | - | 5 DOWN | -19.38% 8/18 print reaction (factors.db) |
| INTC    | L | - | 5 DOWN | foundry fade (factors.db) |
| KLAC    | L | - | 5 DOWN | tools-cycle pullback (factors.db) |

Vol-regime expansions (RV20/RV60 > 1.25x, event-driven tapes): AAOI, NBIS,
CRWV, FN, COHR, CRDO, AMKR, FLNC, SNDK, MU, MP, USAR, KTOS, AVAV, RKLB, BE.
Highest-frequency 3%+ movers full-history (beta class): SOL/ALGO/LINK/HBAR-USD,
AAOI (706), FLNC, COIN, BE, HIMS, RKLB, SMR.

### S5 -- entity-event signals

| ticker | type | strength | dir | evidence source |
|---|---|---|---|---|
| AAOI  | backlog+guide | M | + | >$324M 800G/1.6T backlog; FY26 guide raised >$1.1B rev/>$140M op inc; 100K->650K u/mo YE26 (AAOI.md) |
| AAOI  | dilution/litigation-flag | H | - | ~$838M raised/12mo + $600M ATM; auditor change post material weakness (AAOI.md) |
| AMZN  | backlog | H | + | AWS backlog $364B +49% YoY ex-Anthropic; effective ~$464B w/ $100B forward = 3.6x cover (amzn-analysis-2026-04-29) |
| ANET  | guidance | M | + | 2026 guide raised to $11.25B (+25%); AI networking $3.25B 2.17x YoY (ref-theme-alpha) |
| ASML  | backlog+guide | M | + | EUR 38.8B backlog; guide raised EUR 36-40B (ref-theme-alpha) |
| AVAV  | backlog | M | + | funded backlog $1.1B record; $186M Switchblade order under $990M IDIQ (defense ref) |
| AVGO  | backlog | H | + | $73B AI backlog via 8-K 2026-03-04; FY27 $100B AI reaffirmed (AVGO.md/ref-theme-alpha) |
| BE    | backlog | M | + | $7.65B contracted in 90 days (Oracle/Brookfield/Nebius); ~$20B total (be-analysis-2026-06-29) |
| BE    | mgmt | M | o | NEW CEO PSU retention grant = board-vs-officer governance divergence (be-analysis-2026-06-29) |
| BE    | contract-loss | H | - | Chevron+MSFT chose gas turbines (2.67GW GEV PPA); pricing-power challenge FM1 65% (be-analysis-2026-06-29) |
| CEG   | PPA | H | + | MSFT Crane 837MW 20yr PPA ~$16B life-of-contract; AWS $18B peer read-through (waveE-ceg 2026-08-24) |
| CRWV  | backlog | M | + | contracted backlog $66.8B end-Q4 2025 (supply-chain ref) |
| DELL  | backlog | H | + | $43B AI-server backlog entering FY27 + $50B AI-revenue target (~4 qtrs cover) (waveI-dell) |
| ETN   | backlog+guide | M | + | backlog $22.8B (68% deliverable 12mo); growth guide RAISED 8->10% (grid ref) |
| FLNC  | backlog | L | + | $3B+ multi-year BESS backlog vs SELL-rated tape (waveU-FLNC) |
| GD    | backlog | M | + | $93.7B total backlog; Marine ~$50B (defense ref) |
| GEV   | backlog | H | + | $163.3B total (+32% YoY); gas backlog+slots 83->100GW -> 110GW YE-26 (waveE-gev) |
| GOOGL | backlog | H | + | Cloud backlog $240B->$460B->$514B two quarters; Cloud +82% @ 35.6% margin (googl-analysis-2026-07-23) |
| GOOGL | litigation | M | + | DOJ breakup REJECTED Apr 8; DC Circuit residual tail only (googl-analysis-2026-04-30) |
| HII   | backlog | M | + | record $56.9B Q2-25 (+17.1% YoY) (defense ref) |
| LMT   | backlog | M | + | $194B end-2025 ($150B pre-2022); book-to-bill 1.6x (waveT-lmt) |
| MU    | guidance | M | + | FQ3 guide $33.5B/+40% QoQ, 81% GM; capex raised to $25B (the memory-name analysis) |
| MSFT  | litigation | M | - | two securities class actions 6/13 + 6/24 (D&O insured, low fundamental) (msft-analysis-2026-06-29) |
| MSFT  | guidance-open | M | o | FY27 capex legs >=$230B kill / <=$210B bull UNRESOLVED; lease-adj FCF margin 15.5% through 20% line report 1-of-2 (wave1-msft) |
| NBIS  | backlog | H | + | $46-50B contracted 2027-31 (Meta $27B + MSFT $17.4-19.4B); deferred rev confirms (NBIS.md) |
| NBIS  | customer-conc | M | - | Meta ~50% of backlog insourcing threat 7/01; 2 customers = 88% (nbis-analysis-2026-07-12) |
| NOC   | backlog | M | + | record $95.7B end-2025; $46B+ awards 2025; SHIELD $151B pull (waveT-noc) |
| NVDA  | backlog | M | + | $500B backlog cited; Blackwell sold out; Rubin ahead of schedule (NVDA.md) |
| ORCL  | backlog | H | + | RPO $638B (+$85B seq); OCI +93% (ORCL.md) |
| ORCL  | financing | H | - | FY26 FCF -$23.7B; $43B+$40B debt plans + $20B ATM; negative outlooks (ORCL.md/orcl-analysis-2026-07-13) |
| RKLB  | backlog | M | + | $1.85B +73% YoY end-2025 (RKLB.md) |
| RTX   | backlog | H | + | record $268B Q1-26 (+$50B/6mo); international 44% (RTX.md/waveT-rtx) |
| TLN   | PPA | M | + | AWS ~$18B life-of-contract on 1.92GW Susquehanna FOM thru 2042 (waveE-tln) |
| VST   | PPA | M | + | AWS Comanche Peak 1.2GW + Meta 2,609MW PJM nuclear PPAs ~3,800MW total (VST.md/grid ref) |
| VRT   | backlog | H | + | $15B backlog +109% YoY; book-to-bill 2.9x = compute-to-power rotation tell (VRT.md/ref-theme-alpha) |
| USAR  | M&A/contract | M | + | LCM close $200M = sole Western mine-to-magnet integrator; $125M injection (USAR.md) |
| WBD   | M&A/litigation | M | o | $31 Paramount spread M&A-arb; antitrust block FM 28%; Netflix fee -$2.8B one-time (wbd-analysis-2026-06-07) |

### S6 -- wave-analyst conviction + kill proximity (51 analyses, 2026-08-24)

Conviction ranking (top decile):

| ticker | rating | conv | kill proximity | source |
|---|---|---|---|---|
| FLNC | SELL | 60 | n/a (avoid stance) | waveU-FLNC |
| RTX  | BUY  | 55 | none armed | waveT-rtx |
| XRP  | HOLD | 50 | none armed | waveU-XRP |
| LMT  | HOLD | 45 | none armed | waveT-lmt |
| BE   | HOLD | 45 | WATCH: <$163 capitulation floor | waveU-BE |
| NOC  | HOLD | 44 | award-cadence conditional | waveT-noc |
| NBIS | HOLD | 42 | supply-overhang re-cut watch $100-120 | waveT-nbis |
| META | HOLD | 40 | none armed | wave2-meta |
| CEG  | HOLD | 40 | none armed | waveE-ceg |
| VST  | HOLD | 40 | none armed | waveE-vst |
| ASML | HOLD | 40 | watchlist lane pending re-derivation | waveS-asml |
| LRCX | HOLD | 40 | WATCH <$285 shelf break | waveS-lrcx |

Kill-proximity flags (WATCH/ARMED lines live): GOOGL (core-EPS counter AT 2
consecutive + SMA200-warning band), MSFT (FCF kill report 1-of-2 route OPEN),
NVDA (Q2 print 8/26 guide <$95B trigger), SNDK (kill #4 ARMED; Consumer
-32% seq; resolves 11/06), SMCI (cash <$1.0B solvency trigger),
NOW (<$95 zone-floor), SNPS (<$285 shelf), COHR (<$240/<$222 extension lines),
DLR (BUY but <$175 x2 = exit line), MRVL (<$208 cancel line).

---

## MULTI-SIGNAL CONVICTION BOARD (>= 2 simultaneous POSITIVE signals)

Ranked by count and quality of simultaneous positive signals:

| ticker | positive signals | count | board note |
|---|---|---|---|
| AMZN | S3 institutional accumulation (H) + S5 backlog $364B/$464B effective (H) | 2 | highest-quality pairing: Tier-A adds + demand visibility |
| MSFT | S3 value-cohort inflow Pershing/Dodge&Cox (H) + S6 conviction stable, kills clear | 2 | litigation tail D&O-insured; capex-transcript leg open |
| RTX  | S5 record $268B backlog (H) + S6 top-BUY conviction 55, no kills armed | 2 | cleanest defense compounder setup |
| CEG  | S5 MSFT Crane PPA $16B life-of-contract (H) + S6 conviction 40 | 2 | contracted-nuclear scarcity story |
| GEV  | S5 backlog +32% to $163.3B, 110GW path (H) + S6 conviction 40 | 2 | offset by active 5-session down-streak (S4-) |
| AVGO | S5 $73B AI backlog 8-K (H) + S3 formerly net-bullish | 2 | degraded by S2 discretionary insider cluster (-) |
| GOOGL| S5 Cloud backlog $514B (H) + S3 Berkshire cohort (+, stale) + DOJ resolved | 3 | third signal stale-vintage; SMA200 warning + EPS counter temper |
| VST  | S5 dual hyperscaler PPAs 3,800MW (M) + S6 conviction 40 | 2 | PPA revenue starts back-loaded |
| DELL | S5 $43B AI backlog (H) + S1 8-K cluster | 2 | working-capital FM 40% caps conviction |
| TSM  | S2 first clean insider cluster-buy (M+) + Tiger/Tepper 13F adds | 2 | against 13F breadth distribution (o) |
| META | S3 magnitude-positive adds (H) + S6 conviction 40 | 2 | zero open-market insider buys blocks STRONG tier |
| NOC  | S5 record backlog + SHIELD pull (M) + S6 conviction 44 | 2 | award cadence conditional |

BEAR-SIDE multi-signal cluster (mirror screen): AAOI (insider H- + dilution H-
+ 3%-day churn), NBIS (insider H- + customer concentration - + 6-session down
streak), ORCL (insider H- + 13F net reduce - + financing stress -), BE
(insider H- + contract-loss H- vs bull backlog + = conflicted), SNDK (Tepper
full exit + insider distribution + kill #4 ARMED), CRWV (C-suite $150.7M -
+ whipsaw tape + <$208 cancel line nearby), PLTR (dated but unrefreshed
distribution signal), RKLB (discretionary director sells + down-streak).

## Coverage gaps (honesty ledger)

1. Volume-based signals not computable: factors.db bars lack a volume column;
   S4 uses gap-days/streaks/vol-regime as proxies. Ingest OHLCV to enable the
   literal >2x-average-volume rule.
2. Form 4 direction requires filing CONTENT; the EDGAR store holds metadata
   only (form/date/doc). Insider direction above comes from analysis-time
   OpenInsider reads recorded in vault prose, not from parsed XML.
3. 13F reads are Q1-CY26 vintage for most names (Q+45d lag); Q2 filings due
   8/14 are only partially reflected (SNDK, TSM refreshed). Re-run after the
   next Dataroma sweep.
4. Crypto tickers and pure ETF wrappers have no SEC filer; their rows come
   solely from S4/S6 (spot tokens: N/A across 13F/Form-4 universe).
5. SPCX 8-K spike is IPO-mechanics-shaped (warrants/units), not distress --
   do not read S1 direction without opening the documents.

*Additive data layer. Qualitative context lives in [[ref-scoring-models]],
[[ref-monitoring-rules]], *ref-factor-lens* (not published), and per-ticker entity notes.*
