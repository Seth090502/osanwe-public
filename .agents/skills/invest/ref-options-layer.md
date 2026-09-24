---
categories: [sources]
type: reference
created: 2026-07-11
updated: 2026-07-11
status: active
confidence: high
tags:
  - topic/investment-analysis
  - topic/options
  - topic/judgment-gates
related:
  - "invest"
  - "[[ref-analysis-template]]"
  - "[[ref-kernel-sizing]]"
  - "ref-portfolio-doctrine"
---

# ref-options-layer -- Phase K-ter options-structure recommendation layer + prediction ledger

Read-on-demand companion to `.claude/skills/invest/SKILL.md` (same pattern as
ref-kernel-sizing.md at K-bis.7). Loaded at Phase K-ter. Owns: the fires/skip
matrix, the inputs contract, the IV-proxy procedure, the PoP methods + basis
coherence invariant, the screens, the structure mapping table, the per-rec
output block, the tax rules, the standing limits, the ledger record
construction + append procedure, and worked examples. Built 2026-07-11
(invest-enhancement-pass-v1; GATE-B BUILD-JUSTIFIED
gate-b-invest-enhancement-pass-2026-07-11; design twice red-team hardened,
6 Opus adversarial reviews).

**What this layer answers:** after the equity verdict is final, *what is the
correct options expression of this view -- or is there none?* NO TRADE is a
first-class answer ("stock, or nothing, is the trade").

**What this layer never does:** place or stage an order (D-SEC-1 -- the 18
broker mutators are mechanically denied; every output is a PAPER
recommendation); change the rating, the conviction, the sizing worksheet, or
any Pre-Output gate 10a-10e semantics; branch on conviction (see Inputs).

## CONFIG

**FROZEN SCORING KNOBS (R1 discipline -- freeze binds at the FIRST scored
ledger record; changes only via /decide + re-score of all history under both
configs; parity with the RATING_PROB_MAP freeze):**

```yaml
options_scoring:
  iv_rich_threshold: 1.20      # ATM_IV / realized_63s >= 1.20 -> RICH
  iv_cheap_threshold: 1.00     # <= 1.00 -> CHEAP; between -> NEUTRAL
  pop_method_selection: "delta-approx primary when quote carries delta; breakeven-normal-rv fallback"
  pop_basis_rule: "sellers/credit = short strike; longs/debit = breakeven"
```

**Per-situation DEFAULTS (tunable per rec; every deviation stated inline with
its reason -- these are execution parameters, not scoring knobs):**

```yaml
options_defaults:
  dte_income: 30-45            # CSP / covered call
  long_delta: 0.60-0.75        # long ITM calls/puts
  long_dte_rule: ">= 2x horizon-to-catalyst; never short-dated OTM"
  liquidity_bid_ask_max: 0.05  # (ask-bid)/mark per leg
  liquidity_oi_floor: 100      # per leg
  fill_convention: "conservative: credit at bid, debit at ask"
```

## 1. Fires / skip matrix

| Condition | Behavior |
|---|---|
| Full run, equity verdict + K.5 conviction FINAL, Wave-3 gate survived | FIRES (after K.5, before Phase K compose) |
| `--preview` | unreachable (run exits at Phase B) |
| `--refresh <path>` | SKIP (no fresh verdict, no fresh IV -- inputs do not exist) |
| Shadow runs (`--no-entity --no-peripheral`) | K-ter may run for the diff, but the Phase M ledger append is SKIPPED (S7 write isolation -- no A/B artifacts in the scoring population) |
| Asset without listed options (crypto; non-optionable names) | `not-applicable-no-listed-options` -- distinct state, NOT ledger-logged, NOT a NO_TRADE (a NO_TRADE is a decision about an available chain; this is the absence of a chain) |
| Option read tools unreachable this session (Phase 0-style ToolSearch load failure at K-ter) | Layer emits a one-line DISABLED note in the analysis + Phase P; no block, no record; gate items 10g-10i are conditional on `options_layer_enabled` |

## 2. Inputs contract

| Input | Source | Notes |
|---|---|---|
| verdict | K-bis.5 Step 1 (FINAL) | the mapping branches on this |
| conviction | K.5 Step 2 (FINAL, modulated) | **LEDGER LOGGING ONLY. The structure-selection mapping MUST NOT branch on conviction. NO_TRADE is reachable only via verdict + IV context + screens; a conviction threshold anywhere in this mapping is a defect (Pre-Output 10i asserts every NO_TRADE traces to a screen/IV/earnings/scale reason, never a conviction value).** |
| confidence + gate_f verdict | Pre-Output 6/10a state | logged; GATE-F BLOCKED never reaches K-ter (10a HALTs first); FOMO-SUSPECT is logged and stratified by the scorer |
| IV context | Section 3 | atm_iv, realized_63s, regime |
| realized_63s | technicals panel `vol_annualized_pct.trailing_63s` (prov script:technicals) | missing -> IV UNMEASURABLE -> NO TRADE |
| days to next earnings | price-fetcher `next_earnings` / `get_earnings_calendar` | drives earnings-clear placement + `earnings_in_window` |
| thesis horizon | analysis Time Horizon field | drives long-DTE rule + `thesis_horizon_date` |
| shares held (per account) | Phase J.0 live `get_equity_positions` | drives share-backed rows + the scale screen |
| tax-lot state | Section 2.11 pass (trim/exit asks) | drives the SELL/collar row |
| account + option level | Current-session broker read, when exposed by the available schema; missing permission fields stay UNVERIFIED | Section 8 permission review |
| option chain / quotes | main-loop ToolSearch load at K-ter: `select:mcp__robinhood-trading__get_option_chains,get_option_quotes,get_option_instruments` | topology-neutral (main loop in both tiers); load failure -> DISABLED note |

**Historical option-quote field surface (observed 2026-07-11; probe the current schema before use):** quotes carry
`bid_price`/`ask_price` (+sizes), `mark_price`, `break_even_price`,
`implied_volatility`, `delta` (+gamma/rho/theta/vega), `open_interest`,
`volume`, and the broker's own `chance_of_profit_long`/`chance_of_profit_short`.
Delta-approx is therefore the PRIMARY PoP method; record the broker
chance-of-profit per leg as corroboration (never as the scored pop_est -- it
is the broker's model, not this layer's frozen method).

## 3. IV-proxy procedure (free-stack; honest)

1. Identify the candidate expiry PER THE MAPPING ROW (income structures:
   30-45 DTE, earnings-clear unless deliberately structured for the event;
   longs: the DTE rule). IV is measured ON THE EXPIRY THE STRUCTURE WOULD
   TRADE -- never on a generic near expiry.
2. ATM quote = the strike nearest the regular-close underlying price on that
   expiry (`get_option_instruments` by strike, `get_option_quotes` by id).
   The ATM quote must itself pass the bid-ask width test
   (`(ask-bid)/mark <= 0.05`) before its IV is trusted (thin-chain guard).
3. Regime: `RICH` iff `atm_iv / realized_63s >= 1.20`; `CHEAP` iff `<= 1.00`;
   `NEUTRAL` between; `UNMEASURABLE` when the ATM quote is absent/untrusted
   or realized_63s is missing -> NO TRADE.
4. **Earnings confound rule:** if the only expiry showing RICH contains an
   earnings print AND the mapping row demands earnings-clear, that is
   `NO_TRADE (earnings_confounded)` -- the richness IS the event premium, and
   rolling to the earnings-clear expiry loses the very richness that motivated
   the row. Never downgrade to "CSP anyway".
5. Corroboration (optional, additive): the Phase H.2 IV-percentile read
   (ref-analysis-template 6.4) when available. Backward-looking realized vol
   overstates post-crush baselines -- note it when regime flips on a recent
   vol event.

## 4. PoP methods + the basis coherence invariant

**INVARIANT (enforced at score_ledger.py --append AND Pre-Output 10h,
fail-closed):** `pop_method`'s basis == `success_criterion_machine`'s basis.
A PoP computed on one event and a success criterion registered on another
corrupts the Brier by construction -- this invariant kills the class.

| Structure family | Basis | PoP |
|---|---|---|
| Premium-selling single-leg (CSP, covered call) | short strike (expire OTM) | `1 - abs(short-leg delta)` |
| CREDIT spreads (bear call) | short strike | `1 - abs(short-leg delta)`; `max_loss = (width - net_credit) x 100` |
| Long single-leg (long call / long put) | BREAKEVEN (strike +/- premium) | delta of the breakeven-nearest strike, or `breakeven-normal-rv` |
| DEBIT spreads (call debit vertical) | BREAKEVEN (long strike + net debit) | `breakeven-normal-rv` on the breakeven, or breakeven-nearest-strike delta; `max_loss = net_debit x 100` |
| Two-sided (`inside`/`outside` range payoffs) | no single basis | `resolver: manual` ONLY; the coherence invariant is one-sided-only |

**breakeven-normal-rv (fallback when delta is absent):** lognormal terminal
price; `pop = Phi(d2)` toward the profitable side, with
`d2 = [ln(S/BE) + (mu - 0.5 * sigma_h^2)] / sigma_h`,
`sigma_h = realized_63s * sqrt(DTE_cal / 365)` (the 252/365 conventions cancel
-- verified; do not "fix"), `mu = 0` (real-world drift, conservative).
Unit anchor (tools/test-score-ledger.py): ATM (S == BE), 45 DTE, 40% vol,
mu = 0 -> call-side pop = Phi(-0.5 * sigma_h) ~ 0.472; put-side ~ 0.528
(variance drag puts the lognormal median below spot).

**Named free-stack limits:** delta-as-PoP is the risk-neutral approximation
(N(d1)-adjacent optimism vs true N(d2)); no volatility surface, no skew; both
stated per record via `pop_method`. The scorer reports the model Brier AGAINST
the delta-implied baseline -- skill exists only when the model beats the
market's own probability, so the approximation bias nets out of the skill read.

## 5. Screens (each failure -> NO_TRADE with its reason; ordered)

1. **Chain existence:** no listed options -> `not-applicable-no-listed-options`
   (not logged; Section 1).
2. **Liquidity:** any leg with `(ask-bid)/mark > 0.05` OR `open_interest <
   100` -> `NO_TRADE (liquidity_fail)`.
3. **IV measurability:** regime UNMEASURABLE -> `NO_TRADE (iv_unmeasurable)`;
   earnings confound -> `NO_TRADE (earnings_confounded)`.
4. **Account scale:**
   - CASH-COLLATERAL structures (CSP): collateral = strike x 100. When it
     exceeds deployable account cash, RECOMMEND + `scale_flag:
     not-executable-at-account-scale` (owner-ratified policy 2026-07-11: the
     prediction still logs and scores; it becomes executable once account
     cash covers the collateral).
   - SHARE-BACKED structures (covered call, protective put, collar): require
     shares_held >= 100 in ONE account. Sub-100 holdings ->
     `NO_TRADE (sub_contract_holding)` -- one contract hedges/covers 100
     shares; a "hedge" on a fractional position is a naked position wearing a
     hedge label (category error, not a scale flag; D12).
5. **Ex-div / early assignment:** short-call structures (covered call, collar,
   bear call spread) whose window spans an ex-dividend date: either route the
   record `resolver: manual` (early assignment breaks price-mechanical
   resolution) or NO_TRADE; state which and why per rec.

## 6. Structure mapping (branch on verdict + IV context + screens ONLY)

| Verdict + context | Structure | Parameters (defaults; deviations stated) |
|---|---|---|
| STRONG BUY / BUY, IV rich | Cash-secured put | Strike at the valuation- or support-anchored entry level (Decision Sheet entry / technicals support), 30-45 DTE, expiry clear of earnings unless deliberately structured for it (say so) |
| STRONG BUY / BUY, IV cheap, horizon >= 3mo | Long ITM call | Delta 0.60-0.75, DTE >= 2x horizon-to-catalyst; NEVER short-dated OTM |
| BUY, IV cheap, dated catalyst | Call debit vertical | Defined risk; breakeven-basis PoP; `recommend-only` (multi-leg) |
| HOLD, shares held >= 100, IV rich | Covered call above resistance/target, 30-45 DTE | HARD SKIP on the right-tail test (below); sub-100 shares -> NO_TRADE (sub_contract_holding) |
| HOLD, no IV-rich covered-call setup | NO TRADE (`no_edge`) | The honest default row -- most HOLDs land here; "stock (or nothing) is the trade" |
| SELL, shares held, tax-lot pass says wait | Protective put OR collar bridging to the LT-conversion date | Sized to the ST lots only (Section 2.11 conversion dates); sub-100 -> NO_TRADE (sub_contract_holding); collar `recommend-only` |
| SELL / STRONG SELL, no shares, IV cheap | Long put | Breakeven-basis PoP; same delta/DTE discipline as long calls |
| SELL / STRONG SELL, no shares, IV rich | Bear call credit spread | Defined risk; NEVER naked short calls; short-strike basis; `recommend-only` |
| Any verdict, screen fail / IV unmeasurable / earnings-confounded | NO TRADE | First-class output with `no_trade_reason` |

**Covered-call right-tail HARD SKIP (thesis-SHAPE test; explicitly NOT
conviction-keyed):** skip the covered call entirely iff EITHER (a) a named
asymmetric-upside catalyst falls inside the call's expiry window (product
launch, an earnings print whose implied move exceeds the strike distance,
live M&A optionality), OR (b) the bull-case target exceeds the candidate
strike by more than the base-case upside to that strike (the call would cap
more than half the modeled upside). Capping a 10x candidate for premium
crumbs is thesis-inconsistent -- when the skip fires, SAY SO in the block.
A floored-conviction HOLD on a right-tail name still skips; a high-conviction
HOLD on a flat-distribution name remains covered-call-eligible.

## 7. Required per-rec output block (renders under body section 21 via the
`<!-- OPTIONS-BLOCK insertion point -->`; ref-analysis-template 6.4)

Every recommendation states ALL of (10g; no placeholders):

```markdown
### Options expression (Phase K-ter) -- PAPER (mid-based, conservative fill: credit at bid / debit at ask; never executed)

**Structure**: <name> (<single-leg | recommend-only-multi-leg>) <scale_flag if not executable>
**Legs**: <side> <qty> <TICKER> <expiry> <strike><C|P> (delta <d>, IV <iv>, OI <oi>)
**Est premium (fill convention)**: $<X.XX>/share (credit + / debit -) = $<XXX>/contract
**Breakeven**: $<X.XX>   **Max loss**: $<X> ($risk basis)   **Max gain**: $<X | unbounded>
**PoP**: <0.XX> (<delta-approx | breakeven-normal-rv>; basis <short-strike | breakeven>; broker chance-of-profit <0.XX> corroboration)
**Earnings exposure**: <next earnings YYYY-MM-DD is inside|outside the structure window; treatment>
**Tax note**: <options P&L is ST ordinary income; stated when it changes the trade -- always on covered calls (converts LTCG-eligible appreciation to ST premium) and collar rows>
**Success criterion (pre-registered)**: <prose> | machine: {basis, level(s), direction}
**Horizon**: structure resolves at max leg expiry <date>; verdict claim resolves at thesis horizon <date> (<direction> <threshold_pct>)
**Executability**: <account + option level read; single-leg placeable at level 2 | spreads recommend-only (level 3 + MCP single-leg limit)> -- recommendation only, never an order
**Ledger**: <id> appended (wiki/investing/options-ledger.jsonl)
```

NO_TRADE blocks state: the verdict, the reason (`no_trade_reason` enum:
`liquidity_fail | iv_unmeasurable | earnings_confounded | account_scale |
sub_contract_holding | no_edge`), the screen values that failed, and the line
"stock (or nothing) is the trade."

## 8. Current account option permissions

Derive account permissions from current-session broker read evidence using the
actual callable tool schema. Never reuse account identifiers, option levels or
single-leg/multileg capabilities from a historical run or this reference.

| Account alias | Observed permission | Research implication |
|---|---|---|
| <non-identifying alias> | <current broker read + time, or UNVERIFIED> | <supported structure constraints, or permission gap> |

A current permitted structure is still an inert recommendation. Missing account
permissions or product/contract coverage prevents any claim of executability.
Describe the gap without changing permissions, enabling options, staging orders
or inferring that a connector installation authorizes execution. Keep the PAPER
label and every screen, collateral, tax and GATE-F requirement unchanged.

## 9. Ledger record construction + append (Phase M; script-owned)

Records are constructed IN MEMORY at K-ter, appended at Phase M via
`python tools/score_ledger.py --append '<record-json>'`
(the script owns id-assignment, the point-in-time gate, the basis-coherence
invariant, the horizon = max-leg-expiry assert, ASCII sanitization, the
write-target whitelist, and the sha256 append-only prefix check -- validation
lives in ONE tested place). The ledger path rides the D.5 sha256 baseline set,
the O.1 additive-prefix check, and the O.2 F14 pathspec (atomic with the
analysis commit). Full schema: tools/score_ledger.py docstring + the fixture.
Key semantics:

- One `type: "prediction"` line per structure rec; NO_TRADE logs as
  `type: "discipline_record"` (logged + tallied by reason; excluded from
  Brier and verdict hit-rate -- truth-in-labeling: a criterion-less record is
  a discipline audit, not a prediction).
- `horizon_check_date` == max leg expiry (strictly > ts; same-day-expiry
  structures rejected). The verdict-level claim lives on
  `thesis_horizon_date` + `verdict_success_criterion {direction, threshold_pct}`
  (price-mechanical at that date).
- Resolutions are SEPARATE event lines (append-only purity): `kind:
  "structure"` at expiry, `kind: "verdict"` at thesis horizon; fold on
  (id, kind). A fired kill criterion forces verdict loss via the MANUAL
  `--resolve --kill-fired <id>` input (no daemon watches kills between
  sessions -- stated, not implied).
- Point-in-time: date-carrying fields are mechanically gated; observational
  VALUES (underlying_px, atm_iv, realized_63s) are writer-trusted +
  review-verified + cross-checked against `--closes[ts]` when available.
- `conviction` is logged, never consumed by the scorer's structure metrics.

## 10. Standing limits (state them; never imply otherwise)

1. **IV context is a realized-vol PROXY, not an IV-rank/percentile history.**
   RICH/CHEAP are directional reads off one ATM quote vs 63-session realized
   vol -- not a percentile against the name's own 52-week IV distribution.
2. **A session-based agent cannot monitor or manage short-dated options
   between sessions.** The DTE floors and the never-short-dated-OTM rule
   exist for that reason, not for edge.
3. **Desk-grade PROCESS on a free/retail DATA stack.** Live consensus, a full
   vol surface, and execution algos are NOT on this stack; the layer never
   implies otherwise.
4. **European-terminal resolution.** The scorer resolves on the terminal
   underlying vs the registered level; early assignment, ex-div exercise, and
   path-dependent management are NOT modeled (ex-div short-call records route
   `resolver: manual`; intra-window short-strike crosses stamp
   `resolver_confidence: LOW`).
5. **PAPER, always.** Mid-based with the conservative fill convention; no
   slippage model; nothing was executed. Every record and every scorer report
   header carries the PAPER stamp.
6. **Recommend-only, always** (D-SEC-1 + Section 8).

## 11. Worked examples (illustrative numbers; ASCII)

- **Row 1 (BUY + rich):** `<ticker>` BUY at 190 close, entry level 175 (Decision
  Sheet support), 41-DTE expiry earnings-clear, ATM IV 0.50 vs realized_63s
  0.38 -> ratio 1.32 RICH. Rec: sell 175P 41 DTE; premium (bid) 3.80 ->
  breakeven 171.20; max_loss (175-3.80)x100 = 17,120; PoP = 1-|delta 0.22| =
  0.78 (basis short-strike); collateral 17,500 vs a modelled cash balance -> scale_flag
  not-executable-at-account-scale; still logged + scored.
- **Row 4 SKIP (HOLD + rich, right-tail):** `<ticker>` HOLD, modelled share count < 100 ->
  NO_TRADE (sub_contract_holding) before the right-tail test is even reached;
  on a >=100-share right-tail name the HARD SKIP would fire instead and the
  block says the cap-the-upside sentence.
- **Row 5 default (HOLD + neutral IV):** most HOLDs -> NO_TRADE (no_edge);
  the discipline record logs verdict + regime + screens passed.
- **Row 7 (SELL, no shares, cheap):** long put, strike-nearest-breakeven
  delta or normal-rv PoP on breakeven basis; DTE >= 2x horizon-to-catalyst.

## Related

`.claude/skills/invest/SKILL.md` (Phase K-ter dispatcher) |
`ref-analysis-template.md` Sections 2.9/2.11/6.4 |
`tools/score_ledger.py` + `tools/test-score-ledger.py` |
`wiki/investing/options-ledger.jsonl` |
gate-b-invest-enhancement-pass-2026-07-11
