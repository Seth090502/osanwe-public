---
categories:
  - sources
type: reference
created: 2026-04-28
updated: 2026-09-13
status: active
tags:
  - topic/investing
  - topic/frameworks
  - topic/13f
aliases:
  - investor frameworks
  - renowned investor checklists
related:
  - "investing-moc"
  - "[[ref-scoring-models]]"
  - "ref-portfolio-doctrine"
  - "[[ref-monitoring-rules]]"
  - "[[ref-theme-alpha]]"
  - "ref-ai-supply-chain-deep-dive"
  - "ref-theme-beta-institutional-crypto-deep-dive"
  - "ref-defense-aerospace-space-economy-deep-dive"
  - "ref-memory-storage-cycle-deep-dive"
  - "[[ref-ai-power-grid-deep-dive]]"
  - "[[ref-earnings-playbook]]"
  - "[[ref-valuation-methodology]]"
---

# Renowned-Investor Frameworks + Free-Tier Data Sources (2026 SOTA)

Reference document consumed by /invest Phase J-bis (Institutional Positioning) and Phase K-bis (Best-Investor Framework Rotation). Purpose: provide a unified checklist drawing from 11 of history's highest-conviction-at-scale investors so that every /invest analysis triangulates against multiple proven decision frameworks before producing a BUY/SELL/HOLD rating. Data sources documented here are FREE no-auth public-filing-based sources verified live as of 2026-04-28.

This document does not replace fundamental analysis. It SUPPLEMENTS analysis with framework rotation -- the right framework depends on the ticker's category (compounder, cyclical, deep-value, macro-narrative, activist, distressed). Routing rules at section 13.

## Section 1: Warren Buffett (Berkshire Hathaway)

**Edge**: 60-year compounding track record across multiple regimes; "owners earnings" lens (FCF post maintenance-capex) over GAAP earnings; long-hold positioning that survives multiple cycles.

**Quantitative checks**:
1. 10-year average ROE >= 20% with no single year below 15%. Tests durability of return-on-equity not just point-in-time.
2. ROTC (return on tangible capital) >= 12% over 10-year average. Strips out goodwill from acquisition-driven inflation.
3. Debt-to-equity < 0.5 AND long-term debt payable from earnings within 5 years. Stress-tests balance sheet without requiring asset liquidation.

**Qualitative criteria**:
1. Wide and durable moat with the 10-year-durability test ("would this business be intact and dominant in a decade if a competitor with $100B and unlimited talent attacked it?").
2. Honest and rational management with skin-in-game ("does the CEO own meaningful shares purchased on the open market, not just options grants?").

**Distinguishing edge**: Owners earnings calculation (operating cash flow minus maintenance capex, excluding growth capex from the cost base). Long compounder hold periods (often 10+ years) ride out cycle volatility.

**Case studies**: Coca-Cola 1988 (still held 2026; 30+ year compounder), Apple 2016 (turned a $36B cost basis into $170B+ peak), Geico 1976 (private + permanent).

**Application to /invest**: Use for compounder category tickers (NVDA-like quality, MSFT-like dominance). Apply 10-year-durability test in Phase I Competitive context. Reject tickers failing all three quantitative checks unless category exception (e.g., emerging compounder pre-15% ROE).

## Section 2: Charlie Munger (Berkshire / Daily Journal)

**Edge**: Latticework of mental models from psychology, game theory, history, biology. "Lollapalooza convergence" -- multiple independent positive forces compounding simultaneously.

**Quantitative checks**:
1. Incremental ROIC test: does the next $1 of capital deployment earn >= cost of capital? Uses multi-year capital expenditure trends versus operating-income progression.
2. Margin-of-safety price gap >= 25% to conservative intrinsic value estimate. Conservative = use lower-third historical multiples plus haircut for forecast uncertainty.
3. Debt-service stress test under 50% revenue decline scenario. Can the company service interest plus required principal at half-revenue without dilutive financing?

**Qualitative criteria**:
1. Latticework analysis: does the thesis use at least 3 distinct mental models (e.g., network effects + switching costs + commodity-price floor)?
2. Inverted thinking applied: "what would have to be true for this to be the worst investment of my decade?" If no plausible answer, the thesis is overconfident.

**Distinguishing edge**: Lollapalooza convergence -- looking for multiple independent positive forces compounding (e.g., regulatory tailwind + cycle bottom + insider buying + valuation reset). Single-thread theses are weaker than multi-thread.

**Case studies**: BYD 2008 (recognized convergence of Chinese EV policy + cost engineering + battery vertical integration), Costco 1997 (membership model + scale economies + cost discipline).

**Application to /invest**: Use as cross-check for any compounder thesis -- demand at least 3 mental models in Phase I. Apply inversion test before producing BUY rating.

## Section 3: Peter Lynch (Magellan Fund 1977-1990)

**Edge**: 29.2% annualized returns over 13 years; popularized GARP (growth at reasonable price) + 6-bucket categorization framework distinguishing rules per business type.

**Quantitative checks**:
1. PEG ratio <= 1.0 ideal, < 0.5 strong. Price-to-earnings divided by EPS-growth-rate. Lynch's signature metric.
2. EPS growth 15-25% for "fast growers" (small caps with multi-bagger potential), 10-20% for "stalwarts" (mid-large stable compounders). Different rules per bucket.
3. Debt-to-equity low and trending DOWN over 3 years. Rising debt during growth phase = warning sign.

**Qualitative criteria**:
1. Circle of competence applied: "Buy what you know" -- can you explain the business in 2 minutes to a ten-year-old? If no, skip.
2. Inventory-trend health check: rising inventory faster than sales = demand softening signal (especially for retailers, manufacturers, and consumer products).

**Distinguishing edge**: 6-bucket categorization framework with different rules per bucket:
- Slow growers (3-5% EPS growth): own for dividends only; sell on PE expansion
- Stalwarts (10-12% growth): trim at 30-50% gain, redeploy
- Fast growers (20-25% growth): the multi-bagger candidates
- Cyclicals: timing-dependent; buy at trough PE not low PE
- Turnarounds: balance-sheet-first analysis
- Asset plays: hidden value in real estate, patents, or subsidiaries

**Case studies**: Dunkin Brands (recognized franchise model durability), Hanes (asset play in undervalued underwear brand), Chrysler (turnaround under Iacocca).

**Application to /invest**: Use for category determination -- which Lynch bucket does the ticker fit? Different /invest decision logic per bucket. PEG ratio always computed in Phase F Fundamentals.

## Section 4: Joel Greenblatt (Gotham Capital / Magic Formula)

**Edge**: 40% annualized returns at Gotham Capital 1985-1994 (10 years). Open-sourced his approach via "The Little Book That Beats the Market" Magic Formula -- a two-factor mechanical screen with backtested alpha.

**Quantitative checks**:
1. ROIC >= 25% (or top decile of universe). Uses EBIT / (Net Working Capital + Net Fixed Assets) formula -- excludes goodwill, normalizes for capital intensity.
2. EBIT/EV (earnings yield) > 10-year Treasury yield. The higher the better. Captures "cheap on earnings power" without being misled by accounting noise.
3. Combined-rank score: rank universe on both ROIC AND EBIT/EV separately, sum the ranks, top 30 stocks form portfolio. Equal-weight, rebalance annually.

**Qualitative criteria**:
1. Excludes financials (different accounting treatment of leverage) and utilities (regulated returns make ROIC misleading).
2. Market-cap floor of $100M (avoids micro-cap manipulation distortions).

**Distinguishing edge**: Mechanical two-factor screen with documented alpha -- removes analyst judgment from selection. Equal-weight + annual rebalance forces discipline.

**Case studies**: The original 1988-2004 backtest delivered 30.8% annualized vs S&P 12.4%. Subsequent live results 2005-2020 produced 14-16% annualized vs S&P ~10%.

**Application to /invest**: Use as quantitative cross-check on ANY ticker. Compute Magic Formula combined rank in Phase K-bis. Top 5% rank = strong support for BUY rating; bottom 50% = caution flag even if narrative is compelling.

## Section 5: Stanley Druckenmiller (Duquesne / family office)

**Edge**: 30+ years of 30%+ returns at Duquesne with no down years. Macro + narrative + concentrated bets. "The future is the only thing that matters" -- ignores TTM in favor of forward-looking thesis development.

**Quantitative checks**:
1. Position sizing relative to conviction: 1-2 high-conviction bets per year sized to 30-50% of capital ("when you have tremendous conviction in a trade, you have to go for the jugular").
2. Stop-loss on adverse macro thesis-break: pre-defined exit at the price level OR macro signal that would invalidate the thesis (Fed pivot reverses, inflation re-accelerates, etc.).
3. Asymmetric-payoff demand: minimum 5:1 upside-to-downside on concentrated bets (more demanding than the standard 3:1 hurdle).

**Qualitative criteria**:
1. Top-down macro narrative drives stock selection: identify the major capital-rotation theme first (rate cycle, fiscal regime, geopolitical pivot), then pick stocks that ride the theme.
2. "Pig" mentality: when the thesis is right and the trade is working, scale UP not down. Conservative position sizing on conviction trades = leaving alpha on the table.

**Distinguishing edge**: Capital preservation first -- "don't lose much when wrong" through tight stop-losses combined with size-up on conviction. The math: lose 20% on 10 trades sized 5% each = -10% capital; win 50% on 1 trade sized 30% = +15%; net positive.

**Case studies**: Soros's 1992 Pound short (Druckenmiller co-architected; 5x leverage on conviction macro trade), 1999 tech short and buyback (caught the bubble peak), 2020 tech long (recognized COVID-stimulus = digital-acceleration combo).

**Application to /invest**: Use for macro-narrative-fit category tickers (semiconductor cycle plays, rate-sensitive REITs, FX-exposed multinationals). Demand explicit macro thesis statement in Phase I. If no clear macro tailwind, downgrade conviction even if fundamentals are strong.

## Section 6: Howard Marks (Oaktree Capital)

**Edge**: 15+ year compounder in distressed credit. Author of "The Most Important Thing" -- the canonical text on second-level thinking and risk-first investing.

**Quantitative checks**:
1. Cycle position assessment (1-7 scale): where are we in the credit/sentiment cycle? 1 = panic bottom, 7 = euphoria peak. Buy aggressively at 1-2; trim at 6-7; do nothing at 3-5.
2. Margin-of-safety price gap: minimum 20-30% gap between purchase price and conservative intrinsic-value estimate. The gap is the cushion against being wrong.
3. Risk-asymmetry payoff: explicit asymmetric upside (e.g., distressed bonds with 3x recovery potential vs 50% loss probability = +1.5x EV).

**Qualitative criteria**:
1. Second-level thinking: "what's already priced in versus my view?" -- alpha comes from non-consensus correctness, not consensus correctness. If everyone agrees with you, the price already reflects it.
2. Range-of-outcomes probabilistic, not point estimates: model 5-7 plausible scenarios with probability weights, not a single base case.

**Distinguishing edge**: Risk = "permanent loss probability", not standard deviation. Volatility without permanent loss is opportunity. This redefines the entire risk-management lens.

**Case studies**: 2008-2009 distressed credit plays (Oaktree raised $11B fund within weeks of Lehman; deployed into 30-cents-on-the-dollar paper that recovered to par over 2-3 years), 2020 BBB credit (recognized cycle position 2 = aggressive deployment).

**Application to /invest**: Use for cyclical and distressed category tickers. Apply cycle-position assessment in Phase I. Demand 5-7 scenario range-of-outcomes in Phase H Risk Assessment, not just base/bull/bear.

## Section 7: Klarman (Baupost Group)

**Edge**: 20%+ compounded since 1982 with absolute-not-relative-return target. Author of "Margin of Safety" (out-of-print classic; copies trade for $1500+).

**Quantitative checks**:
1. Margin of safety >= 30-50% gap to intrinsic value. More demanding than Marks's 20-30% because Klarman targets absolute returns.
2. Cash >= 30-50% of portfolio when no opportunities meet the margin-of-safety hurdle. Patience is a strategic asset; do not deploy capital just to be "in".
3. Event-driven catalyst within 2-3 years: bankruptcy emergence, spin-off, recapitalization, asset sale -- specific event that unlocks value.

**Qualitative criteria**:
1. "Rule #1: Don't lose money. Rule #2: Don't forget rule #1." Capital preservation dominates return maximization in priority order.
2. Cross-asset opportunism: not bound to equities; will deploy in distressed debt, real estate, currencies, special situations -- whatever offers margin of safety.

**Distinguishing edge**: Absolute-return mandate frees the manager from benchmark-hugging. If the entire equity universe is overpriced, hold cash. If a single distressed bond offers 40% IRR, concentrate.

**Case studies**: 2008 distressed real estate (deployed cash position aggressively into 30-50% discount-to-NAV REITs), Lehman bankruptcy claims (bought at 8 cents, recovered to 40+ cents over 5 years), early Cohen Companies oil & gas distressed (12-bagger).

**Application to /invest**: Use for special-situation and event-driven theses. Apply margin-of-safety threshold in Phase J Portfolio Fit. If portfolio cash is < 10% AND no current ticker meets 30%+ margin-of-safety, raise the deployment hurdle on this analysis.

## Section 8: Stevie Cohen (SAC Capital / Point72)

**Edge**: 30%+ annualized at SAC Capital 1992-2013 (most successful hedge fund of that era by absolute dollars). Catalyst-driven + sector specialization + multi-PM structure.

**Quantitative checks**:
1. Earnings-revision delta: track 4-week analyst-estimate trend. Acceleration in upward revisions = momentum signal; reversal in downward revisions = inflection signal.
2. Short-term catalyst within 1-2 quarters: earnings beat, product launch, regulatory approval, contract win. Specific event that re-rates the multiple.
3. Sector position-sizing limits: max 15% portfolio weight per sector to enforce diversification across PM specializations.

**Qualitative criteria**:
1. Sector specialization: deep PM expertise per sector (semis specialist, biotech specialist, energy specialist). Generalists underperform specialists in alpha generation.
2. Inflection-point identification: distinguish between linear trend continuation (low alpha, market priced) versus second-derivative inflection (high alpha, often mispriced).

**Distinguishing edge**: High-turnover catalyst-driven approach combined with multi-PM autonomy -- 100+ portfolio managers each running 50-200 positions with strict risk limits. Aggregates to a quasi-quantitative ensemble.

**Case studies**: NVDA accumulation 2018-2020 (recognized AI-training-demand inflection 18 months before consensus), TLRY post-cannabis IPO short (recognized regulatory mismatch and supply glut), AMD 2017 EPYC launch positioning.

**Application to /invest**: Use for catalyst-driven theses and sector-specialist plays (semiconductors, biotech, energy). Demand explicit catalyst calendar in Phase E Identity with Cohen-style 1-2 quarter window.

## Section 9: Bill Ackman (Pershing Square Capital)

**Edge**: Activist + concentrated + high-conviction. Tends to hold 8-12 positions only. 2020 hedging trade made $2.6B on $27M cost (a 96x return) on tail-risk credit derivatives.

**Quantitative checks**:
1. FCF generation + predictability >= 10-year history. Demands proven track record of cash-flow stability before considering any position.
2. Revenue growth track record: 5-year average growth + low quarter-to-quarter volatility (volatility-of-growth, not just absolute growth).
3. Margin-improvement runway via operational levers: identify 3-5 specific cost-reduction or revenue-enhancement initiatives the company can execute. Activist mindset.

**Qualitative criteria**:
1. "Simple, predictable, dominant business with moat": passes a 30-second test of "I understand exactly what they do, how they make money, and why competitors can't easily disrupt."
2. Low leverage + modest economic sensitivity: avoids commodity-cyclicals, deep cyclicals, and high-leverage financials. Wants stability.

**Distinguishing edge**: Concentrated 8-12 positions with multi-year hold periods; activist engagement to unlock value when management is underdelivering. Avoids leveraged tech and high-multiple SaaS as "outside circle of competence."

**Case studies**: Chipotle 2016 (activist stake in turnaround), Lowe's 2018 (activist push on operational improvements), 2020 hedging trade (recognized COVID tail risk before consensus).

**Application to /invest**: Use for high-quality dominant-business theses. Demand the 30-second-test in Phase A pre-flight. If thesis cannot be summarized in 2-3 sentences understandable to a non-expert, complexity flag in Decision Sheet.

## Section 10: Michael Burry (Scion Capital)

**Edge**: First public investor to short subprime mortgages 2005-2007 (Big Short fame; ~$725M profit on $1B fund). Contrarian + deep-value + macro-thesis driven. Reads every SEC filing including footnotes.

**Quantitative checks**:
1. Low EV/EBITDA vs sector (bottom decile preferred). Burry's preferred valuation metric -- he distrusts P/E and ROE as "deceptive."
2. Low P/B (asset-adjusted): focuses on asset-light businesses where book value still has predictive power, OR asset-heavy businesses where assets are demonstrably understated.
3. Strong FCF + minimal debt: balance-sheet survivability is non-negotiable for deep-value plays where the catalyst may take 2-5 years to materialize.

**Qualitative criteria**:
1. Read every SEC filing including footnotes: 10-K + 10-Q + 8-K + proxy statements + every footnote. Burry famously found credit-default-swap exposure buried in mortgage-bond footnotes.
2. Contrarian -- look where others won't: scan for tickers the analyst community has abandoned (zero coverage, declining ratings, persistent under-performance versus peers).

**Distinguishing edge**: Ignores P/E and ROE as "deceptive" -- focuses on EV/EBITDA, FCF yield, and balance-sheet quality. Special category: "rare birds" = asset plays + arbitrage + sub-2/3-of-net-current-asset-value names. Will short macro themes when deep-value long ideas are scarce.

**Case studies**: 2005-2007 subprime CDO short (the Big Short), 2020 GameStop long (recognized retail-trading-platform tailwind + asset-light model + insider buying), 2008 stress-test bank shorts.

**Application to /invest**: Use for deep-value and contrarian theses. Apply EV/EBITDA bottom-decile screen in Phase F Fundamentals. Mandate full-filing-read for any thesis requiring footnote-level detail (e.g., complex capital structure, off-balance-sheet exposure).

## Section 11: David Tepper (Appaloosa Management)

**Edge**: Distressed-debt origin transitioned to equity rotation. 30%+ annualized over 30 years. Famously said "money is made on the bold pivot" in 2009 buying bank stocks at the bottom.

**Quantitative checks**:
1. Distressed-debt discount to recovery value: in distressed plays, demand >= 50% gap between current price and conservative recovery scenario.
2. Macro-pivot signal triggers: pre-defined macro indicators that signal regime change (rate cuts, liquidity injections, fiscal pivots, currency stabilization).
3. Position concentration on conviction: when the macro signal fires, deploy aggressively (similar to Druckenmiller's "pig" mentality).

**Qualitative criteria**:
1. Opportunistic + flexible (no rigid value/growth label): will rotate from distressed debt to equity to commodity to currency depending on where the asymmetric opportunity lies.
2. Follow capital flows + sector rotation: identify which sectors are receiving institutional inflows and which are being dumped. Position with the flow at inflection points, against it at extremes.

**Distinguishing edge**: Distressed-debt origin gives Tepper a unique perspective on capital structure and recovery dynamics. Bold pivots on Fed-policy signals -- often early and often correct.

**Case studies**: 2009 financial sector long (Citigroup, Bank of America at $1-3 prices; 5-10x returns over 18 months), 2014 European distressed (Greek bank recapitalization plays), 2020 reopening trade (recognized airline + cruise recovery before vaccines).

**Application to /invest**: Use for cyclical-bottom and distressed-debt theses. Apply Fed-policy + liquidity signal check in Phase I Macro. If macro indicators are at pivot points (rate cuts beginning, QE expanding), upgrade conviction on cyclicals.

## Section 12: Universal Cross-Investor Convergence (where 8+ agree)

The following are research syntheses requiring original-source and applicability checks, not verified investor votes or universal calibrated rules. Use them as questions, with the current workflow owning any operative threshold.

1. **Free cash flow conversion + quality > GAAP earnings**: Buffett, Munger, Lynch, Greenblatt, Klarman, Burry, Ackman, Tepper, Druckenmiller all favor cash-flow analysis over reported earnings. GAAP earnings can be manipulated through accruals, working-capital timing, or one-time items. Cash is less malleable. Compute FCF / EBITDA conversion ratio: >= 80% strong, 100% ideal, < 50% weak.

2. **Margin of safety >= 20-30% gap to intrinsic value**: Buffett, Munger, Marks, Klarman, Burry explicitly demand a price gap; Lynch and Greenblatt embed it in PEG and earnings yield; Ackman demands quality-at-reasonable-price; Tepper requires distressed-recovery-discount. The proposed 25% threshold is unverified synthesis, not established universal agreement. A margin-of-safety choice depends on valuation uncertainty, downside, horizon and costs; retain any separately ratified local policy and disclose its basis.

3. **Capital allocation history audit**: Buffett, Munger, Lynch, Ackman, Klarman, Burry, Druckenmiller all explicitly track buyback timing (good = buy at low P/E; bad = buy at peaks), dividend coverage, debt-paydown, M&A premium history, and SBC dilution. The single best signal of management quality is their capital-allocation track record over 5-10 years.

4. **Moat durability with multi-year stress test**: Buffett, Munger, Lynch, Ackman, Klarman, Cohen, Burry, Druckenmiller all apply some form of moat analysis (network effects, scale economies, brand, switching costs, cost advantage, regulatory protection, proprietary technology). The 10-year-durability test asks: would the moat survive a $100B-and-unlimited-talent attack from a competitor?

5. **Management integrity + skin-in-game**: Buffett, Munger, Lynch, Ackman, Klarman, Burry, Druckenmiller all weigh management quality. Skin-in-game = significant open-market share purchases by C-suite (not just options grants), modest compensation relative to free cash flow, transparent communication in shareholder letters and earnings calls, history of capital-returns-to-shareholders rather than empire-building acquisitions.

## Section 13: Ticker-Category Routing Table

The right framework depends on the ticker's category. Apply primary + secondary frameworks per /invest Phase K-bis Best-Investor Framework Rotation:

| Category | Primary Framework | Secondary Framework | Tertiary Framework |
|---|---|---|---|
| Compounder (durable moat, ROIC >=20%, predictable FCF) | Buffett | Munger | Lynch (stalwart) |
| Fast Grower (revenue 20-40%, GARP price) | Lynch (fast grower) | Greenblatt | Cohen |
| Pre-Profit Grower (structural op-income <0, revenue >20%, runway >=18mo; routes via the forward-earnings bridge, ref-scoring-models Section 10) | Druckenmiller | Cohen | Marks |
| Cyclical (semis, energy, materials, autos) | Lynch (cyclical) | Marks | Tepper |
| Deep Value (EV/EBITDA bottom decile, asset plays) | Burry | Greenblatt | Klarman |
| Macro Narrative (rate-sensitive, FX, geopolitical) | Druckenmiller | Tepper | Marks |
| Activist (operational levers, governance change) | Ackman | Burry | Greenblatt |
| Distressed (bankruptcy, restructuring, recapitalization) | Marks | Klarman | Tepper |
| Special Situation (spin-off, M&A target, recap) | Klarman | Greenblatt | Ackman |
| ETF (diversified passive or factor-tilted) | Custom (see ref-etf-evaluation) | -- | -- |
| Crypto / Token (e.g., BTC, ETH) | Custom (see ref-crypto-landscape) | -- | -- |

**Routing logic**: Phase K-bis applies all three frameworks (primary, secondary, tertiary) to the ticker. Each produces 5 checks (3 quantitative + 2 qualitative). Total 15 framework-checks per analysis. The composite quality score weights primary 50%, secondary 30%, tertiary 20%.

**Category determination**: First-pass uses sector + market cap + revenue growth rate + ROIC. Edge cases (e.g., a turnaround that is also a deep-value asset play) apply BOTH frameworks and reconcile in Decision Sheet.

## Section 14: Free-Tier Data Sources (verified live 2026-04-28)

### 14.1 Dataroma (renowned-investor 13F aggregation)

URL pattern: `https://www.dataroma.com/m/stock.php?sym={TICKER}` for stock-by-ticker view; `https://www.dataroma.com/m/holdings.php?m={CODE}` for manager portfolio (codes: BRK Berkshire, AM Appaloosa, psc Pershing Square, SAM Scion, OAK Oaktree, LP Lone Pine, TG Tiger Global, etc.); `https://www.dataroma.com/m/m_activity.php?m={CODE}&typ=a` for manager activity (a=all, b=buys, s=sells); `https://www.dataroma.com/m/managers.php` for full manager index.

**Coverage**: 65 managers including Buffett (Berkshire), Burry (Scion), Klarman (Baupost), Tepper (Appaloosa), Loeb (Third Point), Ackman (Pershing Square), Marks (Oaktree), Mandel (Lone Pine), Cooperman (Omega), Pabrai, Coleman (Tiger Global), Watsa (Fairfax), Einhorn (Greenlight), Icahn, Peltz (Trian), Hohn (TCI), Li Lu (Himalaya), Spier, Pzena, Berkowitz, Akre, Rolfe (Wedgewood), Nygren (Oakmark), Chou, Smith (Fundsmith).

**Coverage gaps**: Druckenmiller (family office, no 13F filings), Cohen / Point72 (broader hedge fund not curated by Dataroma's "superinvestor" filter), Singer / Elliott Management.

**Update frequency**: Quarterly Q+45 days regulatory deadline; populated within ~24h of SEC release.

**Authentication**: None required. Works via WebFetch directly.

**Data fields**: Manager name + portfolio code, share count, percent of manager AUM, recent activity (Buy / Add / Reduce / Closed / New), reporting date.

### 14.2 SEC EDGAR direct (audit-grade fallback for long-tail managers)

URL patterns: Filer list by form `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={CIK}&type=13F-HR&dateb=&owner=include&count=10`; filing JSON index `https://data.sec.gov/submissions/CIK{10-digit}.json`; 13F infotable XML `https://www.sec.gov/Archives/edgar/data/{CIK}/{accession-no-dashes}/infotable.xml`.

**CIK reference for top managers**: Berkshire `0001067983`, Scion `0001649339`, Baupost `0001061165`, Appaloosa `0001656456`, Pershing Square `0001336528`, Third Point `0001040273`, Point72 `0001603466`, Tiger Global `0001167483`, Lone Pine `0001061768`.

**Coverage**: Every 13F-filer ($100M+ AUM threshold) -- includes Singer / Elliott, Cohen / Point72, Druckenmiller-related vehicles, plus all 65 Dataroma managers.

**Update frequency**: Real-time on filing (Q+45 days).

**Authentication**: Anti-bot blocks WebFetch on `efts.sec.gov` full-text search. Use Bash + curl with User-Agent header per SEC fair-access policy: `curl -A "OsanweResearch contact@email" "https://www.sec.gov/cgi-bin/browse-edgar?..."`. Do NOT use WebFetch for SEC.

**Best use**: Cross-reference Dataroma quarterly grouping against actual filing dates + accession numbers for audit-grade citations. Fallback for managers not in Dataroma's 65-manager set.

### 14.3 CapitolTrades (congressional STOCK Act trades)

URL patterns: Ticker filter `https://www.capitoltrades.com/trades?txDate=last-90-days&asset={TICKER}`; issuer page `https://www.capitoltrades.com/issuers/{numeric-id}` (e.g., NVIDIA `433770`, Microsoft `433382`, Apple `429789`); per-politician trades `https://www.capitoltrades.com/politicians/{slug}`; politicians index `https://www.capitoltrades.com/politicians`.

**Coverage**: 3-year history limit (stated explicitly). Includes both House and Senate disclosures plus their immediate family members. Top traders by frequency: Josh Gottheimer (D-NJ) 1,400+ trades $185M+; Gil Cisneros (D-CA) 1,200+ trades; Kevin Hern (R-OK); April McClain Delaney (D-MD); David Taylor (R-OH). High-profile traders: Pelosi, Crenshaw, Tuberville, Greene -- all present in dataset.

**Update frequency**: 45-day STOCK Act disclosure window; CapitolTrades scrapes within ~1-2 days of filing.

**Authentication**: None. Works via WebFetch.

**Caveat**: Issuer numeric ID required (not ticker symbol). /invest needs a CIK-or-ticker-to-CapitolTrades-issuer-id resolver step; embed a top-50 lookup table in /invest body or fetch dynamically via search.

### 14.4 OpenInsider (Form 4 corporate-insider transactions)

URL pattern: `http://openinsider.com/screener?s={TICKER}&xp=1&xs=1&cnt=100` (xp=1 includes purchases, xs=1 includes sales, cnt=100 returns top 100 transactions).

**Coverage**: Form 4 filings (officers, directors, 10% holders) including 10b5-1 plan flag versus discretionary open-market trades.

**Critical predictive signal**: Cluster open-market buys (3+ C-suite open-market purchases within 30 days, NOT 10b5-1 scheduled trades) generate ~8-11 percentage points of 12-month excess returns over benchmark per Columbia Law / SEC research. 10b5-1 sales are generally noise (pre-scheduled liquidity).

**Update frequency**: Real-time on filing (Form 4 must be filed within 2 business days of transaction).

**Authentication**: WebFetch fails on http:// URL (no TLS upgrade). Use Bash + curl: `curl -sk -A "Mozilla/5.0" "http://openinsider.com/screener?s={TICKER}&xp=1&xs=1&cnt=100"`.

**Decision threshold**: 3+ open-market C-suite purchases / 30 days = positive signal Grade-A. 10b5-1 selling = neutral noise. Mixed pattern = read individual transactions for context (e.g., CEO selling for divorce settlement vs CFO selling at all-time highs is qualitatively different).

### 14.5 stockanalysis.com (universal fundamentals; already in CLAUDE.md preferred sources)

URL patterns: `https://stockanalysis.com/stocks/{ticker}/financials/` for income statement, balance sheet, cash flow; `https://stockanalysis.com/stocks/{ticker}/statistics/` for ratios, valuations, returns; `https://stockanalysis.com/stocks/{ticker}/financials/balance-sheet/` for direct balance sheet.

**Coverage**: All US-listed equities + most ADRs. Free tier provides 5-year historical financials, current ratios, peer comparisons.

**Top-12 universal metrics live**: ROIC, FCF conversion, FCF yield, Net Debt / EBITDA, interest coverage, EV/EBITDA, PEG, SBC / Revenue, buyback yield, capex / D&A, short interest %, days-to-cover. All extractable from a single page load on `/stocks/{ticker}/statistics/`.

**Update frequency**: Within 1-3 hours of earnings release.

**Authentication**: None. Works via WebFetch.

## Section 15: Cluster-Buy Detection Methodology

OpenInsider data includes both 10b5-1 scheduled trades and discretionary open-market trades. The predictive signal is in the discretionary cluster-buy pattern, not the aggregate insider activity.

**Detection criteria**:
1. Time window: rolling 30-day period
2. Insider count: minimum 3 distinct C-suite or board-level individuals (not 3 trades by 1 person)
3. Trade type: open-market purchase ONLY (filter out 10b5-1 plan trades, which are pre-scheduled)
4. Direction: net BUY (total dollar-purchases exceed total dollar-sales for the cluster window)
5. Size threshold: cluster total >= $250K aggregate purchase value (filters trivial signals)

**Empirical evidence**: Multiple academic studies (Cohen, Malloy, Pomorski 2012; Jeng, Metrick, Zeckhauser 2003; SEC research 2025) consistently show 8-11 percentage points of 12-month excess returns on tickers triggering cluster-buy criteria. The signal degrades after 12 months but is robust within the first year.

**False positives**: Beware ESG-funded or mandate-funded purchases (CEO purchases shares using a structured-loan-from-employer arrangement). Read 10-Q footnotes for these. Also: secondary-offering participation by insiders is technically open-market but not a conviction signal.

**Application in /invest Phase J-bis**: When OpenInsider returns a cluster-buy match, score Grade-A confirmation. When it returns 10b5-1-only or net selling, score neutral noise. When it returns single-insider-multi-purchase (one person buying repeatedly), score Grade-B as moderate signal.

## Section 16: 13F Lag Awareness + Superinvestor-Concentration Signals

13F filings have inherent quarterly lag (Q+45 days regulatory deadline). The data is therefore stale by 45 to 135 days when /invest reads it. Despite this lag, the signal value remains high for two reasons:

1. **Superinvestors hold positions for years**: Buffett's Apple position at Berkshire has been held for ~10 years. A 90-day-old 13F filing is still informative about a 10-year position.

2. **Concentration signal beats single-quarter timing**: When 3+ aligned superinvestors ADD to a position in the same quarter, that pattern persists across quarters. Even with 90-day lag, the multi-investor convergence signal is durable.

**Decision thresholds**:
- 3+ superinvestors hold position with stable / increasing weights: Grade-B confirmation signal (not Grade-A because of the lag)
- 5+ superinvestors actively ADDING (not just holding) in most-recent quarter: Grade-A confirmation
- 3+ superinvestors REDUCING in most-recent quarter: Grade-B caution flag (not Grade-A because lag means the reduction may be priced in)
- 5+ superinvestors REDUCING: Grade-A caution flag, potentially overrides bullish thesis

**Anti-pattern**: Single high-profile manager position (e.g., "Buffett bought it") without confirmation from other investors = weak signal. Buffett's individual selections have been wrong (IBM 2011-2017, Kraft Heinz 2015-present). Multi-investor convergence is the alpha, not single-investor identity.

**Cross-check with insider data**: Strongest combined signal = superinvestor concentration + insider cluster-buy. When both fire on the same ticker, treat as Grade-A multi-vector confirmation; thesis confidence may exceed standard caps.

## Section 17: Best-Investor Framework Rotation Algorithm

/invest Phase K-bis applies framework rotation as follows:

1. **Phase 1: Determine ticker category** (Section 13 routing table). Inputs: sector classification, market cap tier, 5-yr revenue CAGR, ROIC, debt/EBITDA, valuation tier (cheap / fair / expensive on EV/EBITDA percentile).

2. **Phase 2: Apply primary framework** (5 checks). Score each check pass/fail/partial. If all 5 pass: framework recommends BUY. If 3-4 pass: framework recommends HOLD. If 0-2 pass: framework recommends SELL or AVOID.

3. **Phase 3: Apply secondary framework** (5 checks). Same scoring. If primary and secondary disagree (one BUY, one SELL), apply tertiary as tiebreaker.

4. **Phase 4: Compute composite quality score** (0-100 scale): 50% weight to primary, 30% to secondary, 20% to tertiary. Each framework's contribution = (passing checks / 5) * weight * 100.

5. **Phase 5: Reconcile with quantitative scoring stack** from ref-scoring-models (Piotroski + Altman + Beneish + Top-12 metrics). The two scores (framework-rotation-composite and forensic-scoring-stack) should agree directionally. Material disagreement = surface in Decision Sheet for explicit reconciliation.

6. **Phase 6: Generate BUY/SELL/HOLD rating** as composite of framework-rotation + forensic-scoring + portfolio-fit + risk-reward. Five-tier scale: STRONG BUY (composite >= 80, R/R >= 4:1, multi-vector signal), BUY (composite 60-79, R/R >= 3:1), HOLD (composite 40-59 OR thesis-intact-but-no-edge), SELL (composite 20-39 OR kill-criteria approached), STRONG SELL (composite < 20 OR kill-criteria triggered OR multi-vector negative signal).

**Calibration**: The framework rotation is a CHECKLIST not a scoring algorithm. A ticker that fails Buffett's quantitative checks is not automatically a SELL -- it may be a Lynch fast-grower that intentionally violates Buffett's stability tests. Match the framework to the category, then apply with judgment.

## Section 18: Application Audit Trail

Every /invest analysis must cite which frameworks were applied, why those frameworks were selected (category match), how the framework checks scored, and how disagreements between frameworks were reconciled. The audit trail goes in Phase K-bis output.

Sample audit trail format:
```
### Framework Rotation Audit (Phase K-bis)

**Category**: Compounder (semis, mega-cap, ROIC > 20%, predictable FCF)
**Primary**: Buffett (5/5 checks pass)
**Secondary**: Munger (4/5 checks pass; lattice-of-3-mental-models partial)
**Tertiary**: Lynch stalwart (4/5 checks pass; PEG 0.67 strong)
**Composite quality score**: 86/100
**Forensic-scoring agreement**: Piotroski 7/9 (strong); Altman Z 5.2 (safe); Beneish M -2.3 (low manipulation risk) -- agreement with framework-rotation directional BUY
**Reconciliation**: No material disagreements; composite signal is Grade-A multi-vector BUY
```

This audit trail makes /invest decisions transparent, reproducible, and reviewable by future /retro continuity audits.

## Maintenance Triggers

- Update Section 13 routing table when new ticker categories emerge (e.g., AI-native software, climate-tech infrastructure)
- Update Section 14 data sources when free-tier policies change (Dataroma adding paywall; CapitolTrades extending history; OpenInsider TLS upgrade)
- Update Section 12 universal-convergence checks when academic research surfaces new signals
- Re-validate cluster-buy 8-11ppt excess return claim every 24 months as research evolves
