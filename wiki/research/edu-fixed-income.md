---
categories: [wiki]
type: reference
status: active
created: 2026-08-24
updated: 2026-08-24
confidence: high
generated: 2026-08-24 by finance-education-corpus subagent (vault-only synthesis)
tags:
  - topic/investing
  - topic/fixed-income
  - topic/bonds
  - topic/rates
  - topic/fed-policy
related: ["[[edu-quantitative-methods]]", "[[edu-accounting-analysis]]", "*edu-portfolio-theory* (not published)", "*edu-market-microstructure* (not published)", "*investing-moc* (not published)"]
---

# Fixed Income: Bond Math, Rates, and Policy Transmission

GENERATED: 2026-08-24. Education-layer reference in this vault's finance
corpus. Bonds are the discount-rate engine of every other asset: when bond
yields move, equity valuations, real estate, and private marks reprice with
a lag. This file covers the mechanics (pricing, duration, convexity),
structure (curves, spreads), inflation linkage, the Fed's toolkit, and the
transmission channels into equities -- because a stock-focused investor who
ignores the bond market is navigating with half the map. Companions:
[[edu-quantitative-methods]], [[edu-accounting-analysis]],
*edu-behavioral-finance* (not published), *edu-portfolio-theory* (not published).

## Table of contents

1. Why bond math matters to an equity investor
2. Present value: the one equation underneath everything
3. Bond pricing fundamentals
4. Yield measures: YTM, YTC, realized returns
5. Duration: Macaulay, modified, effective
6. Convexity and large rate moves
7. Yield curve construction and interpretation
8. Credit spreads: drivers and modeling
9. Inflation-linked bonds and breakeven analysis
10. The Federal Reserve's toolkit
11. Transmission: how bond moves hit equity valuations
12. Practical checklist for rates-aware investing

## 1. Why bond math matters to an equity investor

Three reasons this corpus includes a fixed-income file:

1. Discount rates. An equity is a claim on future cash flows; its value is
   the present value of those cash flows at some discount rate. That rate
   anchors off the risk-free Treasury curve. When the 10-year moves 100bp,
   the discount-rate term of every DCF on Earth moved 100bp, whether or not
   the analyst updated his model.
2. Competition for capital. Bonds are stocks' direct competitor in
   portfolios. A 10-year Treasury yielding 5% is a riskless alternative
   that did not exist when yields were 1%; equity risk premiums must be
   re-earned against that higher hurdle.
3. Recession/credit signal. The yield curve slope and credit spread levels
   are among the few macro series with genuine predictive track records.
   Reading them is free information about the probability distribution of
   the next 12 months.

## 2. Present value: the one equation underneath everything

### 2.1 Mechanics

PV = CF / (1 + r)^t

A dollar later is worth less than a dollar now because of time preference,
inflation erosion, and opportunity cost. Compound the logic across many cash
flows and you have all of asset pricing:

- Bond price = PV(coupons) + PV(principal)
- Stock value (DCF) = PV(expected dividends/free cash flows) + terminal value
- Perpetuity: PV = C / r. Growing perpetuity (Gordon): PV = C1 / (r - g).
- Annuity: PV = C * [1 - (1+r)^-n] / r

### 2.2 Sensitivity intuitions worth memorizing

- Longer maturity = bigger PV sensitivity to r. A cash flow 30 years out
  loses ~26% of PV if r rises from 5% to 6% (1.06^30 = 5.74 vs 1.05^30 =
  4.32); a 2-year cash flow barely moves.
- Lower starting r = bigger sensitivity. At r=2%, moving to 3% costs a 30y
  cash flow far more proportionally than at r=8%. Duration explodes as
  yields fall toward zero -- the mathematical heart of the 2020-2021
  long-duration asset bubble and its 2022 unwind.
- Terminal value dominance: in typical growth-stock DCFs, 60-80% of value
  sits beyond year 5. Small discount-rate changes produce violent valuation
  changes. This is why hypergrowth equities trade like very long bonds.

## 3. Bond pricing fundamentals

### 3.1 Anatomy and conventions

A standard coupon bond has: face (par, typically $100 or $1,000), coupon
rate (annual % of face, paid semiannually in USD markets), maturity date,
and price quoted per 100 of par. Key convention: US Treasuries pay
semiannual coupons; yields are quoted as bond-equivalent semiannual yields.
Day counts differ by market (Actual/Actual for Treasuries, 30/360 for many
corporates); the differences are small but real for precise work.

### 3.2 The price-yield relationship

Price = sum over t of [C/2 / (1 + y/2)^t] + [F / (1 + y/2)^N]

where C is annual coupon, y the semiannual yield-to-maturity, N the number
of half-year periods. Invertible: given price, solve for y (numerically).

The relationship is inverse and NONLINEAR (convex):

- Price falls when yields rise and vice versa.
- The curve is bowed away from the origin (convex): price gains more when
  yields fall than it loses when yields rise by equal amounts.
- Par bond: price = 100 when coupon = yield. Premium: coupon > yield.
  Discount: coupon < yield. Pull-to-par: a premium/discount bond held to
  maturity converges to par regardless of intervening rate moves; total
  return converges to the original YTM (absent default/reinvestment
  surprises).

### 3.3 Zero-coupon bonds and spot rates

A zero-coupon bond makes one payment at maturity; its yield IS the spot
rate for that maturity. Zeros have no reinvestment risk along the way and
maximum duration for their maturity -- a 30-year zero is one of the most
rate-sensitive instruments in existence. Strip yields (principal strips,
coupon strips) give the cleanest read on the pure term structure.

### 3.4 Accrued interest, clean vs dirty price

Between coupon dates, the seller has earned part of the next coupon.
Quoted ("clean") prices exclude accrued interest; invoice ("dirty") price =
clean + accrued. Corporate bonds often quote as spread to benchmark rather
than price; Treasuries quote in 32nds (e.g., 99-16 = 99 + 16/32). These
conventions matter when reading screens.

## 4. Yield measures: YTM, YTC, realized returns

### 4.1 Yield to maturity

YTM is the single discount rate equating price to PV of all promised cash
flows, ASSUMING coupons reinvest at the same YTM and no default. It is a
standardized summary, not a guarantee. Reinvestment assumption understates
realized return when rates fall (coupons get reinvested worse) and
overstates nothing symmetrically -- realized total returns cluster around
initial YTM mainly for HORIZONS EQUAL TO DURATION, a fact worth internalizing
because it converts "yield" into an honest forward-return estimate at the
right horizon.

### 4.2 Callable paper: YTC and YTW

Callable bonds can be redeemed early when convenient for the issuer --
exactly when rates FALL (refinancing wave). So the investor's upside is
capped while downside to rising rates remains full: negative convexity.
Compute yield-to-worst = min over all call/maturity scenarios of the yield.
Premium callable bonds trade to the first call date; the call option's value
is embedded in the OAS (option-adjusted spread) framework of Section 8.

### 4.3 Total return decomposition

Realized holding-period return roughly decomposes into three parts:

Total return ~= yield carry +/- roll-down +/- price impact of yield change
+/- credit migration/default losses

Carry: coupon income accrues daily. Roll-down: on an upward-sloping curve,
a bond "rolls down" toward shorter maturities with lower yields, gaining
price as it ages if the curve shape holds. Price impact: duration times the
yield change (next sections). This decomposition is how professionals think
about expected bond returns; "the yield is the forecast" only works when the
horizon matches duration.

## 5. Duration: Macaulay, modified, effective

### 5.1 Macaulay duration: the weighted-average wait

Macaulay duration = the PV-weighted average time to receive the bond's cash
flows, in years. A 10-year coupon bond might have Macaulay duration ~8
years: most of the PV arrives before maturity. Zeros: duration = maturity
exactly. Intuition: it is the balance point of the cash-flow timeline.

### 5.2 Modified duration: the price ruler

Modified duration converts duration into a price sensitivity:

D_mod = D_mac / (1 + y/k)     (k = compounding periods per year)

Delta P / P ~= -D_mod * Delta y

Examples: D_mod 7 bond, yields +50bp -> price -3.5% approx. A portfolio at
$1M with D_mod 5 loses ~$25k per +50bp. This linearization is excellent for
small moves (few bp) and increasingly wrong for big ones -- hence convexity
(Section 6).

Portfolio duration = market-value-weighted average of holdings' durations;
duration is additive, which is what makes duration matching / immunization
tractable: set portfolio D_mod equal to liability horizon and small parallel
rate shifts leave net wealth approximately unchanged.

### 5.3 Effective duration: when cash flows move

Modified duration assumes cash flows are FIXED. But callable bonds'
expected life shortens as yields fall; MBS prepayments accelerate; puts
extend. Effective (option-adjusted) duration answers with a finite
difference around the actual model:

D_eff = [P(y - dy) - P(y + dy)] / [2 * P0 * dy]

using prices recomputed WITH the option behavior modeled. For option-free
bonds D_eff equals D_mod closely; for callables/MBS they diverge badly --
callables can show D_eff near 2 even at 8-year stated maturity, and MBS can
flip sign characteristics in extreme rate states.

### 5.4 Key-rate durations

Parallel-shift-only analysis hides curve reshaping. Key-rate durations
measure sensitivity to shifts AT SPECIFIC MATURITIES (e.g., 2y/5y/10y/30y).
A steepener position is long 30y key-rate duration, short 2y; its overall
duration may be near zero while its curve risk is large. Any portfolio that
expresses a curve view must be evaluated key-rate by key-rate.

### 5.5 Worked micro-examples

Example A: 2-year note, 4% coupon semiannual, par 100, yield 4%. Macaulay
duration computes near 1.92y; D_mod near 1.88. +100bp -> roughly -1.9%.

Example B: 30-year zero, yield 5%. D_mac = 30, D_mod ~ 28.6. +50bp ->
roughly -14.3%. Same 50bp on a 2-year costs under 2%. THIS is why "rates
went up 1%" means completely different P/L for different instruments.

## 6. Convexity and large rate moves

### 6.1 Definition and intuition

Convexity is the second derivative of price with respect to yield -- the
curvature of the price/yield relation. Taylor expansion:

Delta P / P ~= -D_mod*dy + 0.5*C*dx^2 (with dx the yield change)

Because the true relation is convex for option-free bonds, the linear
duration estimate ALWAYS understates price for any move size: gains on
rallies exceed losses on sellouts of equal bp. Positive convexity is a
free lunch paid for through lower current yield (you give up carry for the
curve).

### 6.2 Magnitudes and drivers

- Convexity scales with the square of maturity: long zeros carry enormous
  convexity. A 30-year zero benefits hugely from the curvature term once
  moves exceed ~100bp.
- Lower yields = higher convexity (curve bends harder near zero).
- Scattered cash flows (barbell: short + long zeros) have MORE convexity
  than a bullet of equal duration. Barbell-for-bullet trades are the classic
  expression of a view that vol will be realized either direction.

### 6.3 Negative convexity

Callables and MBS embed SHORT options for the investor: issuer calls when
rates fall (your rally is truncated), MBS prepays when rates fall
(reinvestment at lower rates), extension risk when rates rise (duration
lengthens exactly when prices fall). Result: price gains capped on rallies,
losses amplified on declines. Holding negative-convexity paper demands
compensation -- which is precisely why it offers wider spreads than
option-free corporates. Match the instrument's convexity profile to your
rate outlook and stomach; do not collect extra yield blindly.

### 6.4 Duration-convexity in practice

For moves above ~100-200bp, use duration PLUS convexity correction, or
better: full repricing/scenario grid (e.g., +/-25/50/100/200/300bp table).
Professional risk reports show the scenario grid, not just a single
duration number, because rate SHOCKS are never parallel anyway.

## 7. Yield curve construction and interpretation

### 7.1 From instruments to curve

The curve maps maturity to yield for a single credit quality (usually
Treasuries). Construction choices:

- On-the-run Treasuries: liquid but occasionally distorted (auction
  squeezes, flight-to-liquidity premiums).
- Off-the-run inclusion / fitted curves (e.g., cubic spline, Nelson-Siegel/
  Svensson parametric fits): smoother, uses the whole bill/note/bond complex.
- Swap curve: LIBOR-replacement (SOFR) swap rates; reflects bank credit and
  hedging flows, the pricing backbone for floating-rate corporate debt.
- Bootstrapping: strip par yields into zero (spot) curves sequentially --
  each par bond's cash flows priced with previously derived spots. Forward
  rates follow: f(t1,t2) implied by spot ratios. Forward curves embed both
  expectations AND term/hedging premia; treat forwards as breakevens, not
  forecasts (empirically poor predictors, rich information content).

### 7.2 Shapes and their standard readings

- Upward sloping (normal): growth/expansion baseline; positive term premium.
- Flat: transition; market pricing slowdown without conviction.
- Inverted (short > long): historically the strongest single recession
  signal (2s10s inversion preceded most US recessions with multi-month
  leads). Mechanism: Fed holds shorts high; market prices cuts plus weak
  long-run growth. Caveats: timing is loose (months to years), inversion
  depth/duration vary, and structural demand for long duration (pensions,
  QE) can flatten the signal. Treat as prior-updater, not oracle.
- Steepening/flattening dynamics: bear steepener (long end sells off:
  inflation/term-premium fears), bull steepener (Fed cuts shorts: easing
  cycle), bull flattener (flight to quality long bid: recession fear),
  bear flattener (Fed hiking hard). Naming the regime sharpens macro reads.

### 7.3 What drives the long end

Long yields decompose approximately into: average expected short rates over
the horizon + term premium + liquidity/technical effects. Expected-path
component follows inflation expectations and growth; term premium is the
compensation for bearing duration risk (driven by supply/demand: issuance
calendar, pension immunization flows, central bank QE/QT, foreign reserve
management). Two eras with identical Fed policy can have wildly different
10y yields purely via term premium -- so attributing every long-end move to
"the market changing its Fed view" is naive.

## 8. Credit spreads: drivers and modeling

### 8.1 Definitions

Credit spread = yield on risky bond minus matched-maturity benchmark
(Treasury or swap). Investment grade (IG): roughly BBB-/Baa3 and above;
high yield (HY): below. Spreads compensate for expected loss = PD (default
probability) x LGD (loss given default) PLUS risk premium for bearing
systematic credit-cycle risk PLUS illiquidity premium PLUS technicals.

### 8.2 Spread arithmetic reality check

Historical HY default rates run mid-single digits annually on average
(worse in recessions), recoveries ~40 cents on dollar for senior unsecured.
Expected loss might be 2-3%/yr, yet average HY spreads over time run
~3-5%. The excess over expected loss is the risk premium -- and it VARIES
enormously: 15%+ spreads in panics (March 2020) versus sub-300bp in complacent
late-cycle stretches. Spread LEVEL therefore encodes both fundamentals and
sentiment; tight spreads predict LOW forward excess returns (starting yield
is the honest forward-return anchor, and it is lowest exactly when spreads
are tightest).

### 8.3 Drivers and regime behavior

- Macro cycle: spreads compress in expansions, blow out in recessions.
  Correlation with equities is strongly NEGATIVE (spreads widen as stocks
  fall) -- credit is implicitly short volatility.
- Rates interaction: IG duration is meaningful (7-9y typical index level);
  IG total return mixes rate and spread effects. HY duration runs short
  (3-5y) and behaves partly like equity-with-coupon.
- Technicals: fund flows, issuance calendars, dealer inventory shrinkage
  post-regulation, ETF-driven trading amplify moves both directions.
- Ratings migration: downgrades at cycle turns create forced selling
  (fallen angels crossing IG/HY boundary), a recurring dislocation source.

### 8.4 Modeling sketch

Institutional practice models credit via structural models (Merton: equity
as call on assets; distance-to-default) and reduced-form intensity models
(hazard rates calibrated to spreads). Practical retail-grade heuristics:

- Compare current spread to its own history (percentile) and to realized
  loss experience for that rating bucket.
- Watch IG-HY spread ratio and HY spread vs equity volatility (implied
  correlation between the two markets).
- Breakeven thinking: a 300bp spread earns back ~1.5% of price per year of
  widening protection at 5y duration... i.e., ask "how much widening can I
  absorb before my carry year is wiped out?" before reaching for yield.

## 9. Inflation-linked bonds and breakeven analysis

### 9.1 TIPS mechanics

US Treasury Inflation-Protected Securities adjust PRINCIPAL by CPI-U
(with a ~3-month indexation lag). Coupon rate is fixed but paid on the
ADJUSTED principal, so payments scale with realized inflation; maturity
repays adjusted principal (floored at original par at maturity for US
TIPS). Nominal Treasuries promise dollars; TIPS promise purchasing power.

### 9.2 Breakeven inflation

Breakeven = nominal yield minus real (TIPS) yield at matched maturity. It
is the CPI path at which the two bonds return equally. Interpretation:

Breakeven = expected inflation + inflation risk premium - liquidity
premium (TIPS historically less liquid)

So breakevens OVERSTATE pure expectation slightly in calm times and can
wrench far from fundamentals in crises (March 2020: breakevens collapsed on
TIPS liquidity panic even as inflation was about to surge). 5y5y forward
breakeven (market-implied CPI over years 5-10) is the cleanest read on
medium-term inflation expectations -- the number the Fed watches publicly.

### 9.3 Using the pair

- If you believe realized CPI will exceed breakeven: hold TIPS over nominals.
- Real yield LEVEL matters independently: deeply negative real yields
  (2021) punished cash and nominals alike; strongly positive real yields
  (2023+) made risk-free purchasing power genuinely competitive again --
  a first-order input to equity valuation pressure (Section 11).
- Series-I savings bonds: retail-grade inflation protection with tax
  deferral and purchase limits; a legitimate allocation line for the
  household balance sheet.
- Caveat: TIPS protect against CPI as MEASURED; housing/healthcare weight
  debates and definitional changes mean personal inflation may differ from
  the index.

## 10. The Federal Reserve's toolkit

### 10.1 The mandate and the FOMC

Dual mandate: maximum employment and stable prices (2% PCE inflation
target de facto). The FOMC (12 voting members: 7 governors + NY Fed
president + 4 rotating regional presidents) sets the target range for the
federal funds rate eight scheduled meetings a year, guided by the Summary
of Economic Projections (dot plot) and press conferences. Communication IS
a policy tool (forward guidance): the committee moves markets by shaping
expected paths before moving the actual rate.

### 10.2 Standing facilities and corridor mechanics

- Interest on Reserve Balances (IORB): the floor-setting administered rate;
  banks will not lend reserves below what the Fed pays idly.
- Overnight Reverse Repo Facility (ON RRP): nonbank counterparties (money
  funds) park cash overnight at an administered rate, absorbing the floor
  leakages; ON RRP usage levels are a live gauge of system liquidity
  abundance vs scarcity (trillions in 2021 -> drained through 2023-2025).
- Discount window: lender-of-last-resort backstop for DEPOSITARY
  institutions, collateralized loans at the primary credit rate; stigma
  historically suppressed use until the 2023 regional-bank stress introduced
  the standing BTFP facility alongside. Watch discount-window usage as a
  funding-stress tell.
- Standing repo operations: post-2019 repo-spike reforms added standing
  facilities to cap money-market rates from above.

### 10.3 Balance sheet tools: QE and QT

- Quantitative Easing (QE): outright purchases of Treasuries/MBS credited
  with new reserves. Channels: portfolio rebalancing (sellers reach for
  risk), signaling (commitment device for low future rates), scarcity/
  duration extraction (removing interest-rate risk supply from the market).
  Empirically lowered term premia and supported risk assets; magnitude
  estimates vary widely -- communication surprises around QE rounds moved
  markets as much as the flow itself.
- Quantitative Tightening (QT): letting maturing securities roll off (or
  caps on reinvestment). Drains reserves; raises term premia gradually;
  interacts with Treasury issuance supply. QT is deliberately slower and
  quieter than QE; its end-stage shows up in money-market plumbing (RRP
  drain complete, reserves approaching "ample-to-scarce").
- Distinction that matters: rate policy steers the FRONT end directly;
  QE/QT mostly works on the LONG end via term premia and supply absorption.

### 10.4 Transmission lags

Monetary policy hits the economy with long and variable lags (commonly
quoted: 12-18 months for peak effect). Channels: borrowing costs (mortgage
refi freeze at high rates), wealth effects (equity/house prices), exchange
rate, credit availability (bank lending standards), and expectations. This
is why the Fed hikes into strength and stops before obvious weakness --
it is steering a ship with a mile of tiller rope.

## 11. Transmission: how bond moves hit equity valuations

### 11.1 Channel 1: discount rates on long-duration cash flows

From Section 2: equity value = PV of cash flows. Rate rises compress PVs
most where cash flows sit FAR in the future: unprofitable tech, biotech
pre-revenue, SPAC-era growth, long-lease REITs. The 2022 episode is the
canonical case: 10y yield from ~1.5% to ~4% produced 60-80% drawdowns in
the longest-duration equity cohorts while value/cash-generative names fell
far less. Rule of thumb for sensitivity: compare a company's weighted
cash-flow duration to the bond's; similar-duration assets move similarly.

### 11.2 Channel 2: equity risk premium competition

ERP = earnings yield minus risk-free proxy (often trailing/forward E/P
minus 10y). When the 10y jumps 250bp and earnings yields do not follow,
ERP compresses -- either equities must cheapen or investors accept thinner
compensation. Rising-rate environments force this renegotiation continuously.
Note asymmetries: the ERP framework works best for broad indices; for
individual names, WACC shifts feed through levered FCF models with brutal
nonlinearity (terminal-value multiple compression).

### 11.3 Channel 3: leverage, refinancing walls, and credit conditions

Corporate debt floats (SOFR-linked) or refis on schedules. Higher-for-longer
rates: raise interest expense at each refinancing (interest coverage
deteriorates, especially for levered small caps and CRE), tighten bank
lending standards (SLOOS surveys), and raise hurdle rates for buybacks/LBOs
-- removing marginal bid. Private equity marks and private credit books
lag public markets but obey the same math; public equities reprice first.

### 11.4 Channel 4: sector rotation and relative bets

- Banks: steeper curves + higher short rates help NIM; inverted curves +
  deposit flight hurt. Regional banks are also collateral-mark sensitive.
- Utilities/telecom/staples: bond proxies; underperform when yields spike,
  outperform when duration gets bid.
- Energy/financials/value: historically better in rising-rate regimes
  tied to nominal growth; long-duration growth suffers.
- Housing chain: mortgage rates are THE transmission valve (existing-home
  turnover collapses at 7%+ mortgage rates; builders then discount via
  buydowns).

### 11.5 Reading the tape jointly

Practical synthesis for vault use: track (a) 2y (policy path), (b) 10y /
term premium (valuation anchor), (c) 2s10s (recession odds), (d) HY IG/HY
spreads (credit stress), (e) 5y5y breakeven (inflation expectations),
(f) MOVE/VIX cross (vol regimes). Equity decisions made WITHOUT these six
readings are half-blind; the vault's regime detector and scenario stress
tests should ingest them mechanically.

## 12. Practical checklist for rates-aware investing

Before sizing any equity or fund position, answer:

1. What is the position's effective cash-flow duration? (growth profile,
   terminal value share)
2. Which direction does the current rate REGIME push this asset? (not the
   absolute level -- the second derivative of policy)
3. Is the entity a net borrower or net creditor, floating or fixed?
4. What does the curve say about the next 12 months (slope, recent shift)?
5. Are credit spreads confirming or diverging from equity optimism?
6. Where are breakevens relative to consensus inflation narrative?
7. What is the carry-vs-risk asymmetry here (bond math applied to equity:
   dividend/FCF yield vs duration risk)?
8. Does my thesis survive a +150bp shock? A -150bp shock? Write both down.

## Closing summary

Fixed income supplies the gravitational field of finance: present value is
the law, duration measures how far an asset sits from the center, convexity
describes how the field bends, and the yield curve plus credit spreads are
the seismographs. The Fed administers the field's strength through the
front end and reshapes it through the balance sheet. Every equity decision
is secretly a rates decision; the investor who can price a bond can feel
the pull on his stocks before the drawdown arrives. Pair this file with
[[edu-quantitative-methods]] for the statistical machinery behind spread
and curve modeling, and [[edu-accounting-analysis]] for the cash-flow
statement side of the leverage channel.


---

## Related vault data

Where bond math meets this vault's measured rates stack:

- [[ref-fed-policy-complete]] -- funds-rate path, balance sheet, and
  reaction-function evidence behind Sections 10 and 11.
- [[ref-inflation-rates-complex]] -- breakevens, real rates, and the curve
  series feeding Sections 7 and 9; the DGS10 gate lineage lives here.
- [[ref-fed-liquidity-engine]] -- QT, reserves, and repo plumbing; the
  balance-sheet channel of Section 10 in operational detail.
- *ref-yen-carry-global-liquidity* (not published) -- global carry mechanics where
  duration, FX, and risk appetite collide; unwind episode census.
- *ref-portfolio-risk-decomposition* (not published) -- how rates exposure shows up in
  current factor contributions and duration-like sensitivities.
- *ref-scenario-stress-test* (not published) -- the rate-shock scenarios that turn
  duration intuition into portfolio P&L numbers.
- [[ref-datacenter-infrastructure]] -- bond-proxy REIT exposure (DLR-class)
  where equity duration makes Section 11's transmission direct.
- Companion theory: [[edu-quantitative-methods]] (spread and curve
  modeling statistics) and [[edu-accounting-analysis]] (cash-flow side of
  the leverage channel).
