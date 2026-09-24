---
aliases: []
categories: [meta]
type: reference
status: active
created: 2026-08-24
updated: 2026-09-12
confidence: high
tags:
  - topic/investing
  - topic/portfolio-construction
  - topic/sizing
related: ["ref-portfolio-doctrine", "ref-portfolio-optimization", "[[ref-correlation-matrix-full]]", "[[ref-composite-scoring]]", "calibration-2026-08-23"]
---

# Allocation Methodology -- position sizing math (normative)

Companion to `.agents/skills/portfolio/SKILL.md` (flow + formats live there;
formulas live here). Every constant is quoted from the doctrine machine block
in `Atlas/sources/investing/ref-portfolio-doctrine.md` (fingerprint
`c5890053`, ratified decision-invest-rate-gate-retire-2026-07-30) or from
the generated research refs cited per section. Arithmetic is local after
current-session broker read acquisition. Quantities, account cash and lots from
saved files do not verify current inputs. No reads of `.raw/`, `private/`,
`finance/`, `credentials/`, `.env*`, `auth.json`, or `*.local.md`. ASCII only.

## Constants (single source: the doctrine block; never restated with new values)

| Symbol | Meaning | Value | Source |
|---|---|---|---|
| b_cap | max payoff ratio b in Kelly | 5.0 | sizing.b_cap |
| p(BUY) | win prob, b <= 4.5 / b <= 5.0 | 0.35 / 0.30 | sizing.win_prob.BUY |
| p(STRONG_BUY) | win prob, b <= 4.5 / b <= 5.0 | 0.40 / 0.35 | sizing.win_prob.STRONG_BUY |
| rr_hurdle | min R/R by rating | BUY 3.0, STRONG_BUY 4.0 | sizing.rr_hurdle |
| stop clamp | stop distance bounds | 5% .. 25% | sizing.stop_rules |
| max tranche | single-tranche cap, % of book | 5.0 | sizing.max_tranche_pct_book |
| min trade | de-minimis floor, % of book | 1.0 | sizing.min_trade_pct_book |
| corr haircut | rho > threshold multiplier | 0.75 at rho > 0.7 | sizing.haircuts.correlation |
| crypto haircut | crypto-sleeve multiplier | 0.5 | sizing.haircuts.crypto |
| name ceilings | single-name amber/red | 30% / 35% | concentration.single_name |
| theme-alpha ceilings | amber/red (interim amber to ~2026-09-08) | 60/70 (interim 50) | concentration.thesis_theme_alpha |
| other-thesis flag | any other thesis flag line | 40% | concentration.other_thesis_flag_pct |

Sizing target rule: `target = MIN(model target, analyst median PT when
available)` [sizing.target_rule]. Win prob DECLINES as b rises (anti
target-inflation): use the row whose b_max first covers the computed b.

## R-A1 -- Deployment state (gate multiplier)

Machine-evaluated from factors.db raw series; never hand-read from prose.

1. RATE-SHOCK leg (DFII10): rise_bp = DFII10[last] - DFII10[last-59 obs].
   Fire requires rise >= 75bp CONFIRMED by nominal DGS10 rising >= 25bp over
   the same window; state entered after 3 consecutive fire sessions; exits
   below 60bp (hysteresis). Fired -> leg multiplier 0.5x; unresolvable series
   -> fails closed to 0.5x [rate_shock block]. DGS10 LEVEL is disclosure-only:
   "the nominal 10Y LEVEL is not a deployment condition (retired 2026-07-30)".
2. VOLATILITY leg (^VIX): all 5 most recent observations > 22 -> 0.5x;
   all 5 > 35 -> 0.0x absolute halt (observable states only).
3. Stack: `m = MIN(active multipliers)`, never multiply ("MIN across active
   states, never multiply"); no active state -> m = 1.0.
4. Reserve: any ratified opportunity reserve stays NETTED from deployable cash unless a
   release condition evaluates TRUE: SPX close <= 0.85 x trailing-252-session
   regular-close high; OR effective theme-alpha < 35% of book; OR any of the 5
   latest VIX obs > 30. Unknown inputs evaluate UNKNOWN -> reserve stays on.
   Stamp every condition's input + provenance into the worksheet.

Provenance trust: non-MCP-script macro reads cap deployment at 0.5x; macro
observations older than 5 days are stale for gate purposes
[provenance_trust].

## R-A2 -- Calibrated win probability

1. Take stated confidence c (0-100) from the ticker's latest analysis
   frontmatter.
2. Map to bin in `wiki/maintenance/calibration/confidence-map.json`
   (`lo <= c < hi`). Stated 45-59 uses nearest measured band (flagged
   extrapolation); outside all bins -> nearest band + extrapolation flag.
3. Calibrated p_c = stated_mid_ratio applied to the doctrine win-prob row:
   p = p(rating, b) x (bin_calibrated / bin_stated_mid), floored at the base
   rate 0.333 x p(rating,b)/0.40 normalization is NOT used -- keep p within
   [base_rate x p_row, p_row] and print both stated and calibrated values.
4. If confidence-map.json is missing/stale (>45d), degrade: p = p(rating, b)
   x 0.75 and print `[UNCALIBRATED]`.

## R-A3 -- Half-Kelly two-form core size

Inputs: book V ($), price px (regular close), target T, stop S, rating,
p from R-A2, m from R-A1.

1. b = (T - px) / (px - S), capped at b_cap = 5.0.
2. Form 1: f* = p - (1-p)/b. Form 2: f* = (p*b - (1-p))/b.
   Assert |Form1 - Form2| <= 1e-9 [reconciliation.kelly_form_identity_abs].
3. Half-Kelly fraction f = f*/2. Core dollars D_kelly = f x V x m
   (deployment multiplier applied HERE, once).
4. Hurdle check: R/R = b must clear rr_hurdle for the rating; failure ->
   report NO-GO (sizing math still shown) unless an armed standing limit sits
   at a zone where it passes (state the zone).

## R-A4 -- Volatility parity cross-check (risk-parity bound)

Risk parity says one position should not dominate book variance:

1. Build one complete common-date return matrix for the scored sleeve and
   candidate (last min(90, n) shared observations). Estimate validated daily C
   through `tools/fis/covariance.py` with explicit method and annualization=1;
   sigma_i = sqrt(C_ii), sigma_p,d = sqrt(w'Cw), using normalized scored
   weights. Report data dates, return basis and missing/unknown coverage.
2. Parity dollars P = V x (sigma_target / sigma_i) where
   sigma_target = median daily sigma across held SCORED names. A candidate
   contributing > 25% of post-entry portfolio variance prints a
   `[VOL-PARITY EXCESS]` note; P is reported alongside, not substituted.
3. Beta context: beta_i vs SPY over the same window; beta > 1.5 tightens the
   recommended tranche count by one (see R-A7). UNSCORED tickers skip this
   recipe entirely and carry `[UNSCORED]` -- never zero-risk.

## R-A5 -- Waterfall caps (order fixed; each takes MIN with prior stage)

```
C1 = D_kelly                                   (R-A3)
C2 = MIN(C1, correlation-haircut stage)        rho(new, any held) > 0.7 -> C1 x 0.75
                                               crypto sleeve -> C1 x 0.5 (stacks by MIN)
C3 = MIN(C2, vol-parity soft cap P)            soft: breach prints, does not bind
C4 = MIN(C3, 5% x V)                           max_tranche_pct_book
C5 = MIN(C4, headroom)                         headroom = MIN over ALL thesis
                                               memberships: (ceiling - current thesis
                                               weight) x V, each vs its own amber line
C6 = MIN(C5, deployable cash)                  account-scoped; reserve netted per R-A1
CANDIDATE = MAX(C6, 0); if C6 < 1% x V -> below min_trade floor:
           report NO-GO or round UP only if operator explicitly waives the floor
```

Correlation inputs must identify asset set, window and generation date. A
separately reported pair may use its own shared-date sample; disclose it and
never assemble differing pairwise estimates into the portfolio covariance.

## R-A6 -- Stop construction

Basis enum (doctrine): kill-criterion-price | technical-support-200dma |
dated-swing-low. Procedure:

1. Prefer the kill-criterion price from the analysis (thesis-falsifying level).
2. Distance d = (px - S)/px must satisfy 5% <= d <= 25%; clamp outward bound
   to 25%, inward bound to 5% and note the clamp.
3. Recompute R/R at the final (possibly clamped) stop; the hurdle check in
   R-A3.4 uses THIS number, so clamping can flip a pass to a fail.

## R-A7 -- Entry strategy: lump vs tranche

TRANCHE when ANY of: (a) CANDIDATE would exceed one 5%-of-book tranche before
capping; (b) beta > 1.5 or sigma_i > 1.5 x median held sigma; (c) entry price
sits > 1 ATR(14) above the analysis action-zone low (chase risk); (d) earnings
within 10 trading days [doctrine Section 6 protocol]; (e) sleep-gate active
(any add while theme-alpha >= 50% of book pauses overnight before execution).
Otherwise LUMP.

Tranche plan: N = CEIL(CANDIDATE / (5% x V)), each tranche <= 5% of book;
tranche 1 fires at marketable limit in the analysis zone; later tranches need
named confirmations (zone retest, thesis confirmation print, or calendar).
First-tranche convention from precedent (optimization ref Sec 4 step 8): 25%
of computed size when entering against headroom pressure.

## R-A8 -- Post-entry weights

w_after = (mv_i + delta_i)/V_after for every affected name and thesis;
report: name weight now -> after, thesis aggregate now -> after vs its amber
line, deployable cash after. Breach of any amber line at AFTER weights means
the trade list must be re-cut, not warned about.

## R-B -- Rebalance recipes

1. Targets: read sleeve/name targets from ref-portfolio-optimization.md
   Section 3 (cite generation date; regenerate-before-acting caveat applies).
   Missing target for a name -> HOLD (no invented target).
2. Gap_i = w_target,i - w_now,i; work in dollars: gap$ = gap_i x V.
3. Trade construction rules:
   - |gap$| < 1% x V -> skip (min-trade floor; round-down, never up into a buy).
   - Buys funded ONLY from same-pass sells (cash neutrality first); residual
     buys sized down to proceeds + deployable cash.
   - Account routing: sells/buys route through the tax-advantaged account first
     where the rotation is tax-free (per the doctrine exit ladder).
   - Tax lots: sells from a taxable account take highest-cost lots first for trims
     into strength (optimization ref REC-7 pattern); deep-ITM names prefer
     lowest-gain lots or wait-for-print (REC-2 pattern); respect wash-sale
     windows on any repurchase inside 30 days.
   - Tranches: any single order > 5% of book splits; execution sequence =
     sells before buys, ratified actions before new decisions, tax-advantaged
     actions before taxable [optimization ref Sec 4 sequencing rationale].
   - Every line cites its REC-n or doctrine source; no line without one.
4. Output the ordered list in SKILL.md rebalance format with the cash check.

## R-C -- Review recipes

1. Single-name ledger: each holding vs amber 30% / red 35% (combined-book,
   regular-close basis). Red requires escalation via /decide -- quote, do not
   paraphrase.
2. Thesis ledger: theme-alpha effective weight vs interim amber 50% (through
   ~2026-09-08, promotion conditional per doctrine) then 60%; red 70%;
   every other thesis vs 40%. Headroom = MIN over ALL memberships.
3. Sleeve ledger: each sleeve against its construction target
   [optimization ref] -- labeled guidance, not ceiling.
4. Correlation ledger: count held pairs rho > 0.75 [corr matrix sec 4];
   N_eff of the held book; duplication chains named.
5. Cash buffer: deployable cash >= one max tranche (5% of book) + netted
   reserve intact unless a release condition stamps TRUE.
6. Coverage: UNSCORED holdings, never-analyzed holdings, stale analyses
   (>45d), unexecuted ratified actions.
7. Verdict scale: CLEAN (no rows above FLAG), N FLAGS (conscious-monitor
   items), BREACHES (amber/red crossings -> mandatory /decide path).

## Worked micro-example (shape only; numbers illustrative, marked as such)

ILLUSTRATIVE (synthetic book, round numbers so the arithmetic can be checked):
V=$100,000, BUY rating, b=3.10, stated conf 68 -> bin 60-69
(calibrated ratio 38.9/65 = 0.598) -> p = 0.35 x 0.598 = 0.209 -> floored to
base-band floor 0.333 x 0.35/0.40 = 0.291... the floor mechanics matter more
than the example: PRINT p_stated, p_raw, p_calibrated, and which bound bit.
Kelly form 1: f* = 0.291 - 0.709/3.10 = 0.0623; half -> 0.0311 -> $3,110 at
1.0x (0.0311 x $100,000); rho-to-book 0.10 (< 0.7, no haircut); 5% cap $5,000
not binding; cash OK; candidate ~$3,110 = TRANCHE x1 (beta 0.6, no chase) ->
lump. This is the
worksheet SHAPE, not a recommendation.

## Reconciliation tolerances (hard asserts, from the doctrine block)

- Kelly two-form identity: abs diff <= 1e-9.
- Worksheet dollars: recomputed vs printed <= $0.50.
- Shares derivation: shares x px vs dollars <= $0.50.
- Any tolerance trip -> HALT and recompute; never hand-edit a worksheet line.

## Caveats

- All correlations/vols are 90d regime-specific; rerun after any >5% SPY
  weekly drawdown [corr matrix caveats].
- Half-Kelly assumes the stated probabilities; calibration says stated
  confidence overrates realized win rates -- that is WHY R-A2 exists.
- Not investment advice; the operator executes (D-SEC-1).

Related: .agents/skills/allocate/SKILL.md | ref-portfolio-doctrine |
ref-portfolio-optimization | tools/sizing-eval.py
