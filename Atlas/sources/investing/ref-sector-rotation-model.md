---
categories:
  - sources
type: reference
status: active
created: 2026-08-24
updated: 2026-08-24
confidence: high
tags:
  - topic/sectors
  - topic/rotation
  - topic/momentum
aliases: [sector-rotation-model, rotation-model]
related: ["*ref-sector-benchmarks* (not published)", "*ref-factor-lens* (not published)", "[[ref-macro-landscape]]", "*ref-etf-evaluation* (not published)"]
---

# Reference: Sector Rotation Model (factor-store derived)

**Built:** 2026-08-24 | **Data:** `Efforts/osanwe-v2-overhaul/_work/factors.db` bars table
(107 instruments, daily closes 2021-08-24 .. 2026-08-24, yfinance)
**Method:** equal-weighted sector return per lookback, each member dated off the SPY
calendar (12-day tolerance); RS-ratio = sector return / SPY return at the same lookback;
acceleration = trailing-window return minus the same window measured one window earlier
(pp delta). ASCII-safe, offline, reproducible from the store.

---

## 1. Sector classification (all 107 store tickers mapped)

Task-specified buckets kept verbatim; remaining 41 instruments assigned by entity
frontmatter (`wiki/entities/tickers/*`) or name knowledge. No ticker left unmapped.

| Sector | Members (n) |
|---|---|
| Semiconductors | NVDA AMD MU TSM AVGO MRVL QCOM INTC SNDK WDC ARM + ALAB AMBA AMKR GFS MRAM (16) |
| Semi Equipment | ASML AMAT LRCX KLAC ONTO + AEIS ATEYY ASMIY MKSI (9) |
| EDA/Software | SNPS CDNS PLTR NOW (4) |
| Networking | ANET COHR LITE CRDO CSCO APH FN + AAOI (8) |
| Power Generation | CEG VST TLN NRG (4) |
| Utilities | NEE AEP DUK PPL SO (5) |
| Grid Equipment | GEV ETN HUBB + ABBNY(ABB adr) VRT (5) |
| Data Center REITs | DLR EQIX + DTCR (3) |
| Server OEM | DELL HPE SMCI (3) |
| Defense/Space | LMT RTX NOC GD HII LHX BAH KTOS AVAV ITA XAR + RKLB SPCX (13) |
| Crypto Majors | BTC-USD XRP-USD SOL-USD (3) |
| Crypto Alts | ALGO-USD HBAR-USD LINK-USD ONDO-USD QNT-USD XLM-USD (6) |
| Crypto Equity | COIN (1) |
| AI/Hyperscale | MSFT GOOGL AMZN META ORCL + NBIS CRWV (7) |
| Nuclear/NextGen Power | OKLO SMR BWXT BE FLNC (5) |
| Critical Materials | MP USAR (2) |
| Mobility/Auto-AI | TSLA MBLY (2) |
| Other Equities | HIMS WBD (2) |
| Theme ETFs | VOLT IAU (2) |
| Index ETFs (benchmarks) | SPY QQQ VGT VOO SMH VDE PPA (7) |

## 2. Equal-weighted sector returns + RS (asof 2026-08-24)

SPY: 1m +3.5% | 3m +2.9% | 6m +12.7% | 1y +21.7%. RS = sector/SPY.

| Sector | 1m% | 3m% | 6m% | 1y% | RS1m | RS3m | RS6m | RS1y |
|---|---|---|---|---|---|---|---|---|
| Server OEM | +8.8 | +28.8 | +148.3 | +123.9 | 2.51 | 10.07 | 11.68 | 5.71 |
| Other Equities | +11.0 | +18.4 | +49.6 | +59.2 | 3.11 | 6.46 | 3.91 | 2.73 |
| Crypto Majors | +31.0 | +11.0 | +19.6 | -41.0 | 8.80 | 3.85 | 1.54 | -1.89 |
| EDA/Software | +18.9 | +3.6 | +17.2 | -14.3 | 5.37 | 1.26 | 1.35 | -0.66 |
| Crypto Alts | +11.9 | +2.8 | +20.1 | -54.9 | 3.38 | 0.97 | 1.58 | -2.53 |
| Semi Equipment | -2.6 | +1.2 | +18.1 | +154.2 | -0.75 | 0.41 | 1.43 | 7.11 |
| Crypto Equity | +17.1 | +0.2 | +15.7 | -38.3 | 4.86 | 0.07 | 1.24 | -1.76 |
| Theme ETFs | +4.7 | -3.1 | -5.0 | +36.0 | 1.34 | -1.09 | -0.39 | 1.66 |
| DC REITs | -3.0 | -4.0 | +10.4 | +36.2 | -0.86 | -1.39 | 0.82 | 1.67 |
| Defense/Space | +2.5 | -4.1 | -13.9 | +10.5 | 0.72 | -1.44 | -1.10 | 0.48 |
| Utilities | -6.9 | -4.6 | -6.0 | +4.0 | -1.95 | -1.60 | -0.47 | 0.18 |
| AI/Hyperscale | +14.3 | -6.8 | +22.9 | +34.2 | 4.07 | -2.39 | 1.80 | 1.58 |
| Grid Equipment | -4.1 | -7.2 | +6.5 | +47.5 | -1.15 | -2.52 | 0.51 | 2.19 |
| Networking | +1.6 | -11.0 | +35.3 | +185.7 | 0.45 | -3.84 | 2.78 | 8.56 |
| Semiconductors | -2.8 | -13.9 | +77.9 | +350.3 | -1.13 | -4.91 | 5.08 | 16.12 |
| Power Generation | -13.2 | -14.1 | -19.7 | -19.4 | -3.75 | -4.95 | -1.55 | -0.89 |
| Mobility/Auto-AI | +10.3 | -15.9 | -6.0 | -13.4 | 2.93 | -5.58 | -0.47 | -0.62 |
| Critical Materials | +34.5 | -19.1 | +0.5 | +2.1 | 9.79 | -6.69 | 0.04 | 0.10 |
| Nuclear/NextGen | -1.0 | -32.7 | -17.9 | +59.3 | -0.28 | -11.44 | -1.41 | 2.73 |

ETF proxy check (same method): SMH 1m -2.6 / 3m -5.1 / 6m +32.4 / 1y +90.8 confirms the
semi stall; VDE 1m +5.1 / 1y +50.1 confirms the energy bid; PPA 6m -4.3 confirms defense
weakness; QQQ/VGT/VOO track their buckets cleanly.

## 3. Acceleration (trailing minus prior window, pp)

| Sector | dAcc 1m | dAcc 3m | Verdict |
|---|---|---|---|
| Critical Materials | +68.1 | -79.6 | fresh 1m thrust off deep drawdown |
| Crypto Equity | +37.9 | +22.5 | accelerating |
| Crypto Majors | +49.5 | +38.6 | accelerating |
| EDA/Software | +26.9 | +0.7 | accelerating |
| AI/Hyperscale | +26.0 | -41.8 | rebounding after 3m air pocket |
| Mobility/Auto-AI | +25.1 | -17.1 | rebounding |
| Nuclear/NextGen | +22.4 | -75.5 | dead-cat off brutal 3m (-33%) |
| Other Equities | +17.4 | +24.0 | accelerating |
| Crypto Alts | +14.9 | +26.9 | accelerating |
| Theme ETFs | +13.8 | -28.3 | stable/bouncing |
| Defense/Space | +4.7 | -26.2 | stable |
| Grid Equipment | +4.2 | -65.0 | stable, trend broken |
| Networking | +9.5 | -204.9 | stable (huge prior-run fade) |
| DC REITs | -1.8 | -45.2 | stable/drifting |
| Utilities | -6.6 | -11.3 | decelerating |
| Power Generation | -6.8 | -4.8 | decelerating |
| Semi Equipment | -7.5 | -87.2 | decelerating |
| Semiconductors | -20.8 | -184.7 | decelerating hard |
| Server OEM | -49.9 | -56.6 | decelerating from extreme |

## 4. Where we are in the classic rotation

Not a clean textbook quadrant -- this is a **late-stage AI-capex digestion inside an
uptrend**:

- **Early-cycle tech-leads signature: gone.** Semis went from RS6m 5.08 to RS3m -4.91;
  SMH confirms (-5.1% 3m). The 1y numbers (semis +350%, networking +186%) mark this as
  the back half of a monster leadership run, not its start.
- **Mid/late-cycle industrials-and-energy bid: present.** Energy proxy VDE +50% 1y and
  accelerating; critical materials just ripped +34% in a month.
- **Recession signature: absent.** Utilities (-7% 1m, RS 0.18 at 1y) and bonds-style
  defensives are LAGGING, not leading. This is not a risk-off tape.
- **Leadership hand-off in progress:** hardware (semis/equipment/networking) ->
  integrators (server OEM still RS 10 at 3m despite fading), software (EDA +27pp
  acceleration), and speculative crypto complex (majors +31% 1m, everything
  accelerating). Narrowing, risk-seeking, late-cycle-flavored tape.

## 5. Lead-lag relationships (measured, not assumed)

Daily-return cross-correlations, 2y window (lags +/-12d); plus 63d-overlapping-return
cross-correlations, 3y window (lags +/-30d):

| Pair (A vs B) | Best lag | r | Reading |
|---|---|---|---|
| Semis -> Semi Equipment (63d) | Semis LEAD by ~24 td | 0.30 | INVERTED vs classic lore: chipmakers roll first, equipment follows ~5 weeks later. Current equip stall mirrors the semi rollover that began ~Jun 2026. |
| Hyperscale -> Semis (daily) | +4d | 0.25 | Capex-proxy names move first; propagates down-chain within a week. |
| DC REITs -> Power Gen | +7..10d | 0.02-0.14 | NOT supported: no reliable "power follows DC construction" lead at index level over 2-3y. Treat power/DC as coincident. |
| Server OEM <-> Networking | -2d | 0.08 | noise |
| All other pairs | 0d +/- | <0.15 | co-movement, not lead-lag |

Actionable: watch semis (or hyperscaler capex commentary) as the timing signal for
equipment; do not expect DC REITs to front-run CEG/VST/TLN.

## 6. Relative-strength ranking and the rotation trade

**Rotating INTO (RS > 1.1, multi-horizon):**
Server OEM (RS3m 10.1), Crypto Majors (RS1m 8.8), EDA/Software (RS1m 5.4),
AI/Hyperscale (RS1m 4.1), Other Equities, Critical Materials (fresh thrust).

**Rotating OUT OF (RS < 0.9):**
Power Generation (RS1m -3.8), Nuclear/NextGen (RS3m -11.4), Semiconductors,
Mobility/Auto-AI, Networking (3m), Grid Equipment, Utilities, Defense/Space.

**The trade map:**

- Buy as leaders stall: EDA/software strength is real (SNPS CDNS NOW PLTR all positive
  3m while semis bled) -- add pullbacks; server OEM remains the strongest RS pocket but
  its -50pp 1m deceleration says buy dips, not breakouts; crypto majors have the
  cleanest multi-window acceleration if you want beta.
- Sell/fade as laggards bounce: nuclear/next-gen and power-gen rallies are counter-
  trend within a decaying 3-12m structure (CEG VST TLN NRG all negative every horizon);
  grid-equipment bounces lack the 6m+ trend behind them.
- Re-entry trigger for semis/equipment: 3m sector return crossing back above SPY
  (RS3m > 1.0); until then the measured 24-day semi->equip lead says equipment has
  further downside follow-through.
- Hedge posture: with utilities AND power both lagging while crypto accelerates, the
  tape is risk-on but narrow -- respect the concentration risk flagged in
  *ref-sector-benchmarks* (not published) (a concentrated AI-capex portfolio is effectively one long factor).

## 7. Caveats

- Equal weighting lets small high-beta names dominate: SNDK's +3162% 1y is spinoff-
  distorted (SanDisk re-listing) and inflates the semi bucket; MU +688%, WDC +481% are
  genuine memory-cycle moves. Ex-SNDK the semi 1y is still roughly +300%.
- Small buckets (Crypto Equity n=1, Materials/Mobility n=2) are single-stock stories.
- Overlapping windows overlap regime shifts; acceleration deltas on 63d windows swing
  hundreds of pp after parabolic runs (Networking -205pp is arithmetic, not collapse).
- Membership is today's classification applied backward (no point-in-time index).
- Rebuild command pattern: sqlite3 factors.db bars table; method documented above.
