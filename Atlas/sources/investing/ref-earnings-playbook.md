---
categories: [sources]
type: reference
target_path: Atlas/sources/investing/ref-earnings-playbook.md
created: 2026-06-10
updated: 2026-06-10
status: active
confidence: high
tags:
  - topic/earnings-mechanics
  - topic/pead
  - topic/estimate-revisions
  - topic/guidance-analysis
  - ticker/MU
  - ticker/AVGO
  - ticker/SNDK
  - ticker/NVDA
aliases:
  - earnings playbook
related:
  - "investing-moc"
  - "ref-portfolio-doctrine"
  - "[[ref-investor-frameworks-2026]]"
  - "[[ref-scoring-models]]"
  - "ref-market-calendar"
  - "MU"
  - "AVGO"
  - "SNDK"
  - "NVDA"
  - "SK-Hynix"
  - "[[ref-earnings-playbook-ingest-2026-06-10]]"
---

# Earnings Playbook

## Table of Contents
1. [Consensus Formation Mechanics](#1-consensus-formation-mechanics)
2. [Estimate-Revision Momentum](#2-estimate-revision-momentum)
3. [Pre-Print Checklist (T-10 -> T-0)](#3-pre-print-checklist-t-10---t-0)
4. [Implied Move Interpretation](#4-implied-move-interpretation)
5. [Print-Night Decomposition Protocol](#5-print-night-decomposition-protocol)
6. [Guidance Weighting](#6-guidance-weighting)
7. [PEAD -- The Academic Core](#7-pead----the-academic-core)
8. [Beat-and-Drop Anatomy](#8-beat-and-drop-anatomy)
9. [Peer-Constellation Signal Mechanics](#9-peer-constellation-signal-mechanics)
10. [Cyclical-Name Earnings Specifics](#10-cyclical-name-earnings-specifics)
11. [Post-Print Protocol](#11-post-print-protocol)
12. [Thresholds-as-Data Master Table](#12-thresholds-as-data-master-table)

---

## 1. Consensus Formation Mechanics

Published consensus is a manufactured number, not a market truth. The "Zacks Consensus Estimate" and the I/B/E/S/LSEG mean are simple or weighted averages of individual sell-side analyst forecasts collected over a trailing window -- the Livnat-Mendenhall convention uses all forecasts in the 90-day period before the print, with a minimum of two forecasts [Livnat & Mendenhall, Journal of Accounting Research 2006]. The mechanics of how that average forms determine how reliable it is as the bar a stock must clear.

**Clustering and herding.** Analysts do not forecast independently. Scharfstein & Stein (1990) modeled herd behavior in which agents rationally mimic prior forecasts to protect reputation [Scharfstein & Stein, American Economic Review 1990]. The empirical fingerprint is forecast clustering: estimates bunch tightly around a focal value, understating true dispersion. The practical consequence for the operator is that a tight consensus band masks real uncertainty, and the published mean lags reality when news breaks mid-window.

**Stale-estimate detection.** Because consensus is a trailing average, individual estimates that have not been updated since before a material event drag the mean toward outdated information. Stickel (1990) documented that analyst forecast accuracy and timing vary widely [Stickel, Journal of Accounting Research 1990]. Detection method for the retail operator: on Yahoo Finance, Zacks, or Nasdaq.com estimate pages, compare the "number of analysts" and the high/low range; a wide high-low spread with a stale low estimate signals an un-updated laggard. The "Most Accurate Estimate" that Zacks isolates is precisely the most-recently-revised forecast, and the gap between it and the consensus is the Zacks Earnings ESP [Zacks.com, ESP methodology].

**Whisper numbers vs published consensus.** The whisper number is the buy-side's unofficial expectation -- typically above published consensus into a hot print. The relevant evidence is from the options market: a CBOE-referenced study found the actual post-earnings move was smaller than the straddle-implied move in 72% of cases across ten years of S&P 500 events [CBOE study via Volatility Box, 2023], which means options price the whisper, not the published number. For a momentum name like MU into FQ3-2026, the published consensus is the floor; the whisper (embedded in the implied move and the run-up) is the real bar.

**Buy-side bogeys.** Institutional desks maintain internal "bogeys" -- the number a stock must hit to avoid selling. These are unobservable directly but inferable from (a) the pre-print run-up, (b) the implied move, and (c) analyst price-target revisions. When a stock has rallied hard into the print (MU rallied 720% in 2025 [stockanalysis.com, 2026]), the buy-side bogey sits well above published EPS consensus, and a headline beat that misses the bogey produces a beat-and-drop.

**MU-specific consensus mechanics.** Micron's FQ2-2026 (reported March 18, 2026) saw actual non-GAAP EPS of $12.20 against an LSEG consensus of $9.31 on revenue of $23.86 billion versus $20.07 billion expected [CNBC, March 18, 2026] -- roughly a +31% EPS surprise -- yet the stock fell more than 4% the next session [Yahoo Finance/Reuters, March 19, 2026]. This is the clearest possible demonstration that published consensus is not the operative bar for a crowded cyclical: the buy-side bogey and the options-implied move were far above the sell-side mean.

Operator takeaways for the daily briefing: (1) always show consensus alongside the number of contributing analysts and the high-low range; (2) flag estimates not revised in 30 days as stale; (3) treat the implied move as the proxy for the buy-side bogey; (4) for run-up names, expect the operative bar to exceed published consensus by the magnitude of the pre-print rally.

## 2. Estimate-Revision Momentum

Estimate-revision momentum is one of the most durable documented anomalies in equities, and unlike PEAD it remains exploitable by retail because the signal is free and the decay horizon is months, not days.

**Foundational literature and effect sizes.** Givoly & Lakonishok (1979) first documented that revisions in analysts' earnings forecasts carry information and that the market underreacts -- a semi-strong inefficiency -- using a sample of 67 firms over 1967-1974 from the Standard & Poor's Earnings Forecaster [Givoly & Lakonishok, Journal of Accounting and Economics 1979]. Stickel (1991) sharpened this: firms whose consensus forecast was recently revised upward earned higher abnormal returns over the next 3 to 12 months than firms revised downward [Stickel, The Accounting Review 1991]. Chan, Jegadeesh & Lakonishok (1996) is the canonical effect-size source: using I/B/E/S data over 1977-1993, up-revision portfolios earned about 7.7% higher returns than down-revision portfolios over the six months following portfolio formation [Chan, Jegadeesh & Lakonishok, Journal of Finance 1996]. The same paper reports a 7.5% spread across extreme SUE (earnings-surprise) portfolios over six months for 1973-1993, with the 12-month spread only marginally higher -- confirming the signal is concentrated in the first six months and is "relatively short-lived" [Chan, Jegadeesh & Lakonishok, Journal of Finance 1996].

**Decay horizon.** The Chan et al. evidence is the key calibration: the bulk of the revision-momentum return accrues within 6 months and is largely exhausted by 12 months. Gleason & Lee (2003) documented that the post-forecast-revision drift is larger for high-innovation revisions (those that exceed both the analyst's own prior and the prior consensus) and for low-coverage firms [Gleason & Lee, The Accounting Review 2003]. Importantly, the post-forecast-revision-drift magnitude decreased after 2002, paralleling the broader attenuation of accounting anomalies.

**Zacks Rank as the productized version.** The Zacks Rank is a quantitative model built on revision agreement, magnitude, upside, and surprise [Zacks.com]. Zacks reports that since 1988 its #1 Rank stocks generated an annualized return of about 25.67% (a hypothetical equal-weighted monthly-rebalanced portfolio) versus roughly 11% for the S&P 500 over a comparable window -- the firm describes these as hypothetical-portfolio returns, not a backtest [Zacks performance disclosure]. The Earnings ESP combined with a Zacks Rank #1-3 produced a positive surprise 70% of the time and 28.3% average annual returns in a 10-year backtest [Zacks.com]. The operator should treat the headline annualized figures as marketing-adjacent (hypothetical, gross of costs) but the directional signal -- up-revisions precede outperformance -- as well-supported by independent academic work.

**Computing revision breadth/magnitude from free sources.** This is the actionable core for the daily briefing:
- **Yahoo Finance** (Analysis tab -> "EPS Trend" and "EPS Revisions"): shows current-quarter and current-year consensus at 7/30/60/90-day lookbacks, plus counts of "Up Last 30 Days" and "Down Last 30 Days." Breadth = up count / (up + down); magnitude = % change in consensus over 30/90 days.
- **Zacks.com** (free Estimates page): "Magnitude -- Consensus Estimate Trend" gives % change over 7/30/60 days; "Agreement" shows the up/down revision split.
- **Nasdaq.com** (/market-activity/stocks/`<ticker>`/earnings): consensus and revision history.
- **Finviz**: "EPS next Y" and analyst revision summary fields.
- **TipRanks / Seeking Alpha**: revision counts and the "EPS Revisions" grade.

For MU specifically, revisions turned decisively positive in summer 2025; over a trailing 60-day window into mid-2025, current-year EPS expectations climbed 22.38% and next-year estimates rose 32.42%, earning MU a Zacks Rank #1 (Strong Buy) [Zacks/Nasdaq, 2025]. That is textbook up-revision momentum and the quantitative case against fading a cyclical into the catalyst.

**Operator rule.** Compute 30-day revision breadth and 30-day/90-day consensus magnitude each briefing. Breadth >70% up with positive magnitude is a confirming signal; breadth deteriorating below 50% while price holds is an early CHALLENGE flag.

## 3. Pre-Print Checklist (T-10 -> T-0)

The checklist below is designed to be copied directly into the per-ticker analysis skill and executed on a countdown. It separates positioning checks (what the market has already priced) from fundamental checks (what the read-through evidence says).

**Positioning checks.**

| # | Check | Data source | Threshold / flag |
|---|-------|-------------|------------------|
| P1 | Implied move (front-week ATM straddle / spot) | Market Chameleon, broker option chain | Compare to trailing 8-quarter realized move; flag if implied >> realized |
| P2 | Realized move history (last 8 prints) | Market Chameleon "Earnings Charts" | Median absolute next-day move |
| P3 | Implied vs realized premium | P1 vs P2 | Implied exceeds realized in ~72% of S&P events [CBOE/Volatility Box 2023] |
| P4 | IV percentile / IV rank | optionalpha, broker | IV rank >70 = elevated crowding into print |
| P5 | Option skew (25-delta put vs call IV) | broker chain | Steep put skew = downside hedging demand |
| P6 | Short interest % float | Nasdaq, Finviz | Rising SI into print = squeeze/gap risk |
| P7 | Pre-print run-up (price vs 50/200 DMA) | any charting | Large run-up raises the buy-side bogey |
| P8 | Institutional flow / retail concentration | 13F lag, broker flow notes | High retail concentration = fragile (MU was the most-bought retail stock pre-6/5/2026 selloff per BNP Paribas) [Yahoo Finance, June 2026] |

**Fundamental checks.**

| # | Check | Data source | Threshold / flag |
|---|-------|-------------|------------------|
| F1 | Peer prints already out | company IR, this doc sec. 9 | SK Hynix Q1 leads MU FQ3 by ~6-8 weeks |
| F2 | Channel / pricing data | TrendForce, DRAMeXchange | DRAM/NAND contract price direction |
| F3 | 30-day revision breadth & magnitude | Yahoo/Zacks (see sec. 2) | Breadth >70% up = confirming |
| F4 | Guidance cadence / sandbag history | this doc sec. 6, transcripts | Does management habitually guide low? |
| F5 | Hyperscaler capex guides | AMZN/GOOGL/MSFT/META calls | Demand-side signal for semis |
| F6 | Prior-quarter guidance vs current consensus | 8-K outlook table | Is consensus above or below last guide midpoint? |
| F7 | Inventory / margin trajectory | 10-Q, press release | Gross-margin inflection is the cyclical tell |
| F8 | Whisper vs published consensus | options implied move (P1) | Implied move proxies the whisper |

**Countdown protocol.**
- **T-10 to T-7:** Run F1-F5. Establish whether peer prints and channel data confirm or challenge the thesis.
- **T-6 to T-3:** Run P1-P8 and F6-F8. IV builds gradually; recompute implied move daily.
- **T-2 to T-1:** IV typically peaks the day before earnings; lock the final implied move and realized-history comparison. Note that a Thursday-after-close print reads higher IV than a Monday print because there are fewer days to weekly expiration [projectoption].
- **T-0 (print day):** Confirm exact report time (after-market-close for MU), consensus EPS/revenue, guidance-midpoint expectation, and the decomposition plan from sec. 5.

The checklist's output is a single line for the daily briefing: countdown, consensus, 30-day revision trend, historical-pattern label, implied move, and PEAD peer signal.

## 4. Implied Move Interpretation

**The worked formula.** The options market's expected one-standard-deviation move through earnings is approximated from the at-the-money (ATM) straddle of the nearest expiration after the print:

- **Quick method:** Expected move % = ATM straddle price / stock price. If a $100 stock has a combined ATM call + put priced at $5, the implied move is 5% [Option Alpha].
- **Precise (1-SD) method:** Multiply the straddle by ~0.85 to approximate the 1-SD move, because the straddle slightly overstates the 1-SD range. Example: AAPL straddle $9.00 x 0.85 = $7.65 expected 1-SD move [Volatility Box; Options Hawk]. Some desks use a 1.25 multiplier on the straddle to get a weekly band, or add the two nearest OTM strangles for a refined estimate [MenthorQ; moomoo].

The 1-SD interpretation: the stock is expected to stay within the implied-move band roughly 68-70% of the time on a normal-distribution assumption [Options Hawk].

**IV crush.** Implied volatility inflates into the print (often to 80-150%+ in the earnings-week expiration) and collapses 30-60% in the first session after the release as uncertainty resolves [FlashAlpha; projectoption]. The mechanical consequence: a long straddle can lose value even when the stock moves in the holder's direction, if the realized move is inside the implied band. A worked example: a $100 stock's 2-DTE straddle at 80% IV costs $4.72; the stock opens at $102 (inside the move), IV collapses to 30%, and the straddle buyer loses 54% overnight despite a $2 move [projectoption].

**When implied >> realized history means crowding vs information.** The diagnostic:
- If the current implied move sits well **above** the stock's trailing realized-move history, the options market is pricing either (a) genuine new information/binary risk, or (b) crowding -- hedging demand from a concentrated long base bidding up puts. Distinguish via skew (P5): steep put skew + high retail ownership = crowding; symmetric IV rise = information.
- If the implied move sits **below** realized history, options are cheap relative to the stock's typical reaction and IV may rise further into the event [MenthorQ].

The CBOE-referenced statistic anchors the base rate: across ten years of S&P 500 earnings events, the actual move was smaller than the straddle-implied move in 72% of cases [CBOE via Volatility Box, 2023]. This is the volatility risk premium -- options are systematically overpriced into earnings as compensation to market makers bearing gap risk [Volatility Box]. The operator should therefore treat the implied move as an upper bound on the typical reaction, while recognizing that the ~28% of events that exceed the band include the violent gaps (a 10-20% move) that dominate P&L for a concentrated book.

For MU FQ3-2026, the relevant interpretation is that an elevated implied move combined with steep put skew and the highest-retail-ownership flag indicates crowding, not just information -- consistent with the beat-and-drop hypothesis.

## 5. Print-Night Decomposition Protocol

When the release crosses, decompose the reaction into its drivers in a fixed order, because the dominant driver differs by sector and determines whether the move is durable.

**The decomposition stack.**
1. **EPS surprise** -- actual vs consensus (use non-GAAP for semis).
2. **Revenue surprise** -- actual vs consensus. Livnat and Jegadeesh & Livnat (2006) show revenue surprises carry incremental drift information beyond EPS [Jegadeesh & Livnat, Financial Analysts Journal 2006].
3. **Guidance** -- next-quarter revenue/EPS/margin midpoint vs current consensus (see sec. 6 -- this is usually the dominant driver for growth/cyclical names).
4. **Mix/margin quality** -- gross-margin trajectory, segment mix, one-time items.

**Which driver dominates by sector (base-rate guidance).** Academic decomposition (Brandt, Kishore, Santa-Clara & Venkatachalam, "Earnings Announcements are Full of Surprises") shows the earnings-announcement return (EAR) captures information beyond the SUE, and the EAR-sorted spread (18.7%) exceeds the SUE-sorted spread -- i.e., the market reacts to far more than the headline EPS number [Brandt et al., Duke working paper]. The practical sector mapping:

| Sector | Dominant reaction driver | Notes |
|--------|--------------------------|-------|
| Semis / memory (MU, SK Hynix) | Guidance + gross-margin trajectory | Headline EPS frequently a beat; forward revenue guide and margin inflection dominate |
| AI accelerators (NVDA, AVGO) | Forward guidance vs the whisper/highest hopes | AVGO 6/2026: beat + raise, but Q3 AI guide ($16.0B) below the ~$17.2B whisper -> stock fell [Yahoo Finance, June 2026] |
| Software (PLTR) | Revenue growth + net revenue retention + raise | Multiple-compression risk on any deceleration |
| Hyperscalers (AMZN/GOOGL/MSFT/META) | Capex guide vs cloud growth | Rising capex with decelerating cloud = punished (META fell 9.25% on a capex raise) [Yahoo, 2026] |
| Consumer/retail | Same-store sales + margin + guide | Sandbag culture more common |

**First-reaction fade statistics.** The overnight-vs-intraday literature is directly relevant. Lou, Polk & Skouras (2017/2019) document that overnight and intraday returns exhibit distinct continuation/reversal patterns -- overnight returns positively predict subsequent overnight returns but negatively predict subsequent intraday returns [Lou, Polk & Skouras; NY Fed Staff Report 917]. The "Tug of War" evidence (overnight winners earn negative intraday returns) implies that an after-hours pop driven by retail/attention can partially reverse during the next regular session [AEA "A Tug of War"]. MU FQ3-2025 is a clean specimen: the stock "initially popped in extended trading before paring most of its gains" [CNBC, June 25, 2025]. Operator rule: do not treat the after-hours print reaction as the settled verdict; the regular-session close (and the +1/+2-day drift) is the durable signal.

For the per-ticker skill, the decomposition output should be four labeled lines (EPS surprise %, revenue surprise %, guidance vs consensus %, margin delta) plus a one-line dominant-driver verdict.

## 6. Guidance Weighting

For growth and cyclical names, **guidance -- not the reported quarter -- is the dominant price driver.** The reported EPS is backward-looking; guidance resets the forward consensus that valuation hangs on.

**The raise/maintain/lower matrix vs consensus positioning.** The actual signal is not the guidance action in isolation but the **guidance-vs-consensus spread** -- where management's guide midpoint sits relative to the current Street consensus:

| Guidance action | Guide vs consensus | Typical reaction | Interpretation |
|-----------------|--------------------|--------------------|----------------|
| Raise | Above consensus | Strongly positive | Clean beat-and-raise |
| Raise | In line / below whisper | Negative ("raise but light") | AVGO 6/2026 -- raised FY AI to $56B but Q3 AI guide $16.0B below whisper -> fell ~14% [Yahoo/StockTitan, 2026] |
| Maintain | Below consensus | Negative | De facto cut |
| Maintain | Above consensus | Positive | Conservative reiteration with cushion |
| Lower | Below consensus | Strongly negative | Confirmed deceleration |
| Lower | Above prior-quarter actual | Mixed | Cyclical reset, may be priced |

**Sandbagging cultures.** Some management teams habitually guide below internal expectations to engineer beats. Sandbagging means deliberately understating forecasts so the inevitable "beat" lifts the stock [Wall Street Oasis]. The market learns: once a sandbag culture is recognized, "continuous sandbagging becomes embedded in analyst valuations" and the muted reaction reflects an already-elevated bogey [SuperMoney; heygotrade]. The operator's rule is to track each held name's guide-midpoint-vs-actual history over 8 quarters; a company that beats its own guide by a consistent margin is sandbagging, and its published guide should be mentally marked up.

**MU's guidance pattern.** Micron's guidance has repeatedly been the swing factor. FQ1-2025 (reported Dec 18, 2024) was a slight EPS beat ($1.79 vs $1.75) but the stock plunged ~13% in extended trading on **weak second-quarter guidance despite the beat** [CNBC, Dec 18, 2024]. Conversely, FQ1-2026 (Dec 17, 2025) beat hugely ($4.78 vs ~$3.94) AND guided FQ2-2026 revenue to $18.70B +/- $400M, well above Street, and the stock rose 5%+ [Micron 8-K; Alpha Spread, Dec 17, 2025]. The guidance-vs-consensus spread, not the EPS beat, explained both reactions. The FQ2-2026 print (March 18, 2026) crystallized this: management guided FQ3 to ~$33.5B revenue and ~$19.15 adjusted EPS -- a large sequential raise -- yet the stock still fell ~4% because the run-up had lifted the bogey above even that guide [CNBC, March 18, 2026; Yahoo/Reuters, March 19, 2026].

**Guidance withdrawal effects.** When a company withdraws or refuses to provide guidance (common in macro shocks), the information vacuum is treated as bad news and volatility rises -- the operator should treat a guidance withdrawal as a CHALLENGE flag pending clarification.

**Thresholds as data.**

| Guide-vs-consensus spread | Tier | Action signal |
|---------------------------|------|---------------|
| > +5% | Tier 1 (strong raise) | Thesis CONFIRM |
| +1% to +5% | Tier 2 (modest beat) | Confirm if breadth positive |
| -1% to +1% | Tier 3 (in line) | Reaction driven by positioning/whisper |
| -5% to -1% | Tier 4 (soft) | CHALLENGE flag |
| < -5% | Tier 5 (cut) | Strong CHALLENGE |

## 7. PEAD -- The Academic Core

Post-earnings-announcement drift (PEAD) is the tendency for cumulative abnormal returns to continue drifting in the direction of an earnings surprise for weeks after the announcement. Every claim below is cited to paper, year, and sample period.

**Origins.** Ball & Brown (1968) first documented that prices kept drifting in the direction of the earnings surprise after the announcement -- up for good news, down for bad -- using annual earnings; the original drift was "negligible" because they split firms only above/below expectations [Ball & Brown, Journal of Accounting Research 1968, vol. 6, 159-178].

**Quarterly refinement and effect sizes.** Foster, Olsen & Shevlin (1984) replicated using quarterly data over 1974-1981, estimating that a long-top-decile/short-bottom-decile SUE strategy yielded about a 25% annualized abnormal return before transaction costs; they found the drift was persistent across the period with no concentration in a subperiod, and that sign/magnitude of forecast error plus firm size explained 81% and 61% of the drift variation respectively [Foster, Olsen & Shevlin, The Accounting Review 1984, vol. 59, 574-603].

**Bernard & Thomas -- the landmark.** Bernard & Thomas (1989, 1990) sharpened PEAD using 1974-1986 data. The top-minus-bottom SUE-decile spread was positive in 41 of 48 quarters [Bernard & Thomas, Journal of Accounting Research 1989]. They documented an abnormal-return spread on the order of ~4% over 60 trading days for the hedge portfolio (often annualized into the high-teens), with various summaries citing an ~2% one-sided drift over 60 days for each leg [Bernard & Thomas 1989; ScienceDirect review 2021]. Bernard & Thomas (1990) documented that quarterly seasonal-difference earnings exhibit positive autocorrelation at the first three lags (~0.34, 0.19, 0.06), the mechanism by which a beat this quarter predicts beats in the next three [Bernard & Thomas, Journal of Accounting and Economics 1990, vol. 13, 305-340].

**Surprise definition matters.** Livnat & Mendenhall (2006) showed the drift is significantly larger when the surprise is defined using analyst forecasts and I/B/E/S actuals (about 1-1.5% per quarter larger) than using a time-series seasonal-random-walk model; they report a drift magnitude near 6.9% (and a comparison strategy near 7.7%) for extreme deciles [Livnat & Mendenhall, Journal of Accounting Research 2006, vol. 44, 177-205].

**The momentum connection.** Chan, Jegadeesh & Lakonishok (1996) tied earnings momentum to price momentum: SUE-based and revision-based strategies each generated drifts not subsumed by the other, with the ~7.5% six-month SUE spread (1973-1993) [Chan, Jegadeesh & Lakonishok, Journal of Finance 1996]. Chordia & Shivakumar (2006) framed PEAD as earnings momentum and linked it to investor learning [Chordia & Shivakumar, Journal of Financial Economics 2006, vol. 80, 627-656].

**Post-2010 attenuation -- critical for a large-cap book.** This is the most important modern caveat. Charles Martineau's "Rest in Peace Post-Earnings Announcement Drift" (2021/2022) showed PEAD began disappearing from non-microcap stocks around 2001 and was essentially zero for large-cap stocks by 2006, because prices now fully reflect surprises on the announcement date [Martineau, SSRN 2021/2022]. The high-minus-low SUE spread fell from ~5% in the 1980s-1990s to ~3% or lower by the late 2010s [Martineau summary; ScienceDirect review 2021]. Causes: decimalization, Reg NMS (2005) accelerating HFT, and more arbitrage [Chordia et al. 2014; McLean & Pontiff, Journal of Finance 2016]. McLean & Pontiff (2016) found anomaly returns decay ~58% out-of-sample after publication [McLean & Pontiff, Journal of Finance 2016].

**When PEAD reverses / persists.** A 2025 working-paper debate (Subrahmanyam, UCLA) reconciles the contradiction: whether PEAD "exists" hinges on research design, especially whether illiquid microcaps (about 3% of market value) are included [UCLA Anderson Review 2025]. The disaggregation literature (Caltech "An Anomalous Anomaly") finds the monotonic SUE-return relationship fades at the firm level -- in the good-news portfolio only 51.8% of 13-week returns were positive [Caltech PEAD working paper].

**Operator conclusion.** For MU, NVDA, AVGO and other large/mega-caps, classic numerical PEAD is weak-to-nonexistent -- do not expect a reliable multi-week drift purely from the SUE. The durable signals are (a) estimate-revision momentum (sec. 2, still alive), and (b) guidance-driven repricing (sec. 6). PEAD as a tradable edge survives mainly in small/illiquid names, which is outside the universe considered here.

## 8. Beat-and-Drop Anatomy

A beat-and-drop occurs when a company exceeds EPS (and often revenue) consensus yet the stock falls. It is not paradoxical once positioning is understood: the headline beat clears the published consensus but misses the buy-side bogey / implied move / whisper.

**Causes.**
1. **Priced-in positioning / run-up.** A large pre-print rally raises the operative bar far above published consensus. MU FQ2-2026 beat EPS ($12.20 vs $9.31) and revenue ($23.86B vs $20.07B) handily and still fell ~4% [CNBC, March 18, 2026; Yahoo/Reuters, March 2026].
2. **Guidance quality.** A beat with soft forward guidance (negative guide-vs-consensus spread) -- MU FQ1-2025 beat but fell ~13% on weak FQ2 guidance [CNBC, Dec 18, 2024].
3. **Cycle position.** Late-cycle, peak-margin prints invite "as good as it gets" selling even on a beat.
4. **Whisper/highest-hope miss.** AVGO June 2026 raised guidance but the Q3 AI revenue guide of $16.0B fell below the ~$17.2B whisper [Yahoo Finance, June 2026].
5. **IV crush + crowding.** A concentrated long base unwinds into the resolved-uncertainty vacuum.

**Detection BEFORE the print.** The pre-print checklist (sec. 3) is the detector: large run-up (P7) + implied move >> realized (P3) + steep put skew (P5) + high retail concentration (P8) + a recent peer beat-and-drop (F1) is the beat-and-drop fingerprint. When >=3 of these fire, the per-ticker skill should flag elevated beat-and-drop risk regardless of the expected EPS beat.

**Worked specimen -- AVGO, fiscal Q2 2026 (reported June 3, 2026).** Broadcom posted record revenue of $22.2B (+48% YoY), adjusted EPS of $2.44 (above the ~$2.40 Street figure), and record AI semiconductor revenue of $10.8B (+143%), with a reported backlog in excess of $30B [Broadcom 8-K; Motley Fool, June 3, 2026]. CFO Kirsten Spears guided Q3 revenue to $29.4B (+84% YoY) at a stable 67% non-GAAP operating margin, with full-year AI raised to $56B and FY27 reiterated at >$100B [Broadcom 8-K, June 3, 2026]. Yet the stock declined sharply -- roughly 14.44% in the post-report reaction, with some recaps citing cumulative drops as large as 16% over following sessions [StockTitan; Yahoo Finance; Motley Fool, June 2026]. Cause: CEO Hock Tan's Q3 AI guide of $16.0B came in below the ~$17.2B analyst whisper [Broadcom 8-K; Yahoo Finance, June 2026], and the stock had closed at a record high the prior day [Motley Fool]. Classic beat-and-drop: clean beat + raise, but the raise missed the highest hopes while positioning was extended.

**Worked specimen -- MU, the actual base rate (CY2024-March 2026).** Every one of Micron's nine quarters in this window was an EPS beat. Of those, the stock fell the next session in at least 5 of 9 (~56%), making "beat-and-drop" MU's modal -- not anomalous -- reaction:
- **FQ3-2024 (Jun 26, 2024):** beat, stock ~-7% next day on a light revenue forecast [Reuters, June 2024].
- **FQ1-2025 (Dec 18, 2024):** EPS $1.79 vs $1.75 beat, stock ~-13% on weak FQ2 guidance [CNBC, Dec 18, 2024].
- **FQ2-2025 (Mar 20, 2025):** EPS $1.56 vs $1.43 beat, stock ~-8% next day [Motley Fool/Nasdaq; TIKR].
- **FQ4-2025 (Sep 23, 2025):** EPS $3.03 vs ~$2.86 beat + strong guidance, stock -2.8% [Motley Fool, Sep 24, 2025].
- **FQ2-2026 (Mar 18, 2026):** EPS $12.20 vs $9.31 beat, revenue $23.86B vs $20.07B, stock ~-4% [CNBC; Yahoo/Reuters, March 2026].
- Beat-and-RISE quarters: FQ2-2024 (+14%), FQ4-2024 (+14-15%), FQ1-2026 (+5%+). FQ3-2025 (Jun 25, 2025) was mixed -- popped after-hours then pared most gains [CNBC, June 25, 2025].

The "MU beat-and-drop" pattern is therefore empirically supported: a beat is the base case, but a next-day drop is the modal reaction, driven by guidance-vs-bogey and run-up dynamics. The mechanism is positioning, not a fundamental break -- which is why the beat-and-drops repeatedly preceded continued fundamental strength.

## 9. Peer-Constellation Signal Mechanics

Earnings information leaks across a supply chain in a predictable lead-lag order. For the memory/semis/hyperscaler constellation, the formalization is below.

**The lead-lag map.**
- **SK Hynix Q1 -> MU FQ3** (lead ~6-8 weeks). SK Hynix reports on a calendar-quarter basis ~6-8 weeks before Micron's offset fiscal quarter. SK Hynix Q1 2026 (reported April 23, 2026) printed record revenue of KRW 52.5763T (+198% YoY, +60% QoQ), operating profit of KRW 37.6103T at a 72% operating margin, with DRAM ASP up ~mid-60% sequentially and NAND ASP up ~mid-70% sequentially [SK Hynix Q1 2026 release; CNBC, April 23, 2026; StorageNewsletter]. This is a direct positive read-through for MU's pricing and HBM demand into FQ3-2026.
- **Samsung memory segment** -> corroborates DRAM/NAND pricing; Samsung reclaimed the DRAM revenue lead in Q4 2025 while SK Hynix kept a 57% HBM share [Counterpoint via CNBC, 2026].
- **TSMC monthlies** -> leading demand-side read for the whole AI-semis complex (monthly revenue released ~10th of each month).
- **Hyperscaler capex guides** -> demand-side signal for memory/accelerators. The four hyperscalers (Google, Amazon, Microsoft, Meta) collectively plan to spend ~$725B on capex in 2026, up 77% from 2025's record $410B, per Financial Times data [Tom's Hardware/FT, 2026]; Microsoft set CY2026 capex at $190B (well above the $152B average analyst estimate, with CFO Amy Hood attributing $25B to rising memory-chip and component costs), Alphabet $175-185B (raised to ~$190B), Amazon ~$200B, Meta $115-145B [Tom's Hardware/FT; CreditSights, 2026]. Rising capex = structural memory demand, but the market now scrutinizes capex-vs-cloud-growth (META fell 9.25% on a capex raise) [Yahoo, 2026].

**Formalizing "SK Hynix beat -> MU positive read."** The mechanism: SK Hynix and MU sell into the same DRAM/HBM/NAND end markets at correlated contract prices, so SK Hynix's realized ASPs and demand commentary are a same-cycle proxy for MU's coming quarter. Hit-rate computation method (for the operator to maintain): tabulate, over the last 8 cycles, whether SK Hynix's quarter-over-quarter ASP direction matched MU's reported ASP direction one quarter later. In the current upcycle the correlation is near 1.0 (both reporting record sequential price gains 2025-2026). SK Hynix's Q1 2026 call stated that customer demand for HBM for the next three years "far exceeds SK Hynix's current supply capacity," with HBM4E sampling targeted for H2 2026 and mass production in 2027 [SK Hynix earnings call transcript, April 23, 2026] -- a structural-demand claim that reads directly through to MU.

**Caveat -- read-through != reaction.** A positive peer read predicts the fundamental result, NOT the stock reaction. SK Hynix's blowout was a fundamental positive for MU, yet MU's own print can still beat-and-drop on positioning. The June 5, 2026 episode is the warning: AVGO's Q3 AI guide landing below the whisper triggered a sector-wide reassessment of AI capex, and MU fell ~13% in sympathy (its worst single-day decline since April 2025) even though the news was AVGO-specific [Yahoo Finance, June 2026]. Peer signals therefore feed the fundamental thesis (CONFIRM/CHALLENGE) and the demand-side narrative, but positioning (sec. 3) governs the reaction.

**Operator rule for the briefing's PEAD-peer signal line:** show (1) the most recent peer print + surprise direction, (2) the read-through label (confirms/challenges thesis), and (3) an explicit note that read-through governs fundamentals, not the next-day move.

## 10. Cyclical-Name Earnings Specifics

Memory is the archetypal cyclical, and cyclical earnings mechanics invert the usual valuation intuitions. This section covers how to read memory cyclicals such as MU, SK Hynix, and SNDK.

**Normalized vs reported EPS at cycle turns.** Reported EPS at a cyclical trough is depressed or negative (MU reported a GAAP loss of $(5,833)M for FY2023 and a $(1,234)M loss in FQ1-2024) [Micron 8-K, FY2024]; at the peak it is inflated by maximum pricing and operating leverage (MU's FQ1-2026 GAAP gross margin reached 56.0% versus 38.4% a year earlier) [Micron 8-K, FY2026]. Valuation on trailing or even forward reported EPS is therefore misleading at both turns. The normalized-EPS approach uses mid-cycle margins applied to through-cycle revenue.

**Why cycle-trough P/E looks expensive and cycle-peak cheap.** This is the central cyclical trap. At the trough, the "E" collapses faster than the "P" (the market looks ahead to recovery), so the P/E spikes to a huge or meaningless number -- the stock looks "expensive" precisely when it is cheapest on normalized earnings. At the peak, "E" is maxed out, so the P/E compresses to a low single-digit multiple -- the stock looks "cheap" precisely when it is most dangerous. MU traded at a forward non-GAAP P/E of ~6.3x in late 2025 even as the stock made new highs [TheStreet, 2025] -- a classic low-P/E-at-cyclical-strength signature. This dovetails with the investor-frameworks doc's cycle-peak signatures: a trough-to-peak run with a compressing P/E and decelerating revision magnitude is the late-cycle tell.

**Estimate-revision behavior around memory inflections.** Revisions lag the cycle and then over-extrapolate. Into the 2025-2026 upcycle, MU's revisions turned "decisively higher" in summer 2025 as HBM visibility improved, with current-year EPS up 22.38% over 60 days [Zacks/Nasdaq, 2025]. The danger is that at the inflection the revision train reverses violently: when DRAM/NAND contract prices roll over, analysts cut estimates in clusters and the P/E (low at peak) provides no support because the "E" is about to fall. The operator should weight **the second derivative of revisions** -- decelerating up-revision magnitude even while price rises -- as the earliest cycle-peak warning.

**Cyclical guidance reading.** For a cyclical, a guide that is below consensus but above the prior-quarter actual can still be a positive (the cycle is still climbing). Conversely, the first guide that is merely "in line" after a string of raises often marks the inflection. SK Hynix's claim that HBM requests exceed planned capacity for the next three years is a structural-demand statement that, if it holds, extends the cycle [SK Hynix call, April 2026] -- but the operator should treat multi-year demand claims made at peak margins (72% operating margin) with cycle-aware skepticism.

**Operator rule:** for cyclical names, the per-ticker skill should display normalized-EPS context, the P/E-vs-cycle-position caveat, and the revision second-derivative -- never a bare trailing P/E.

## 11. Post-Print Protocol

After the print, discipline is about updating the thesis on evidence, not on the price reaction alone -- especially given large-cap PEAD attenuation (sec. 7), which means the day-1 move usually IS most of the information.

**CONFIRM vs CHALLENGE -- what evidence justifies each.**

| Evidence | CONFIRM thesis | CHALLENGE thesis |
|----------|----------------|------------------|
| EPS surprise | Beat in line with revision momentum | Miss, or beat far below whisper |
| Revenue surprise | Beat with accelerating YoY | Decelerating or miss |
| Guidance spread (sec. 6) | Tier 1-2 (>= +1% vs consensus) | Tier 4-5 (< -1%) |
| Gross-margin trajectory | Expanding / inflecting up | Peaking or compressing |
| Revision response | Analysts raising post-print | Cuts within 48h |
| Peer corroboration (sec. 9) | Aligned with peer reads | Diverging from peers |

A thesis is CONFIRMED when the fundamental drivers (revenue, guidance, margin) move in the thesis direction, **regardless of a beat-and-drop price reaction**. A thesis is CHALLENGED when guidance turns soft, margins peak, or revisions reverse -- even if the stock rose. The price reaction is positioning; the thesis update is fundamentals.

**Drift-window monitoring schedule.** Given attenuated large-cap PEAD, the monitoring is about confirming the day-1 verdict and watching the revision response, not harvesting a mechanical drift:
- **Day +1:** Record the regular-session close (not just after-hours) -- the durable first verdict. Watch for first-reaction fade (sec. 5): an after-hours pop that reverses intraday is a weak-hands signal.
- **Day +2 to +5:** Track the analyst revision response. A cluster of upgrades/target hikes = revision-momentum CONFIRM (sec. 2). The bulk of any large-cap drift is realized in this window if at all.
- **Day +6 to +20:** Watch for the revision second derivative and peer prints in the constellation.
- **Day +21 to +60:** Classic PEAD window -- relevant only for smaller names; for mega-caps, expect little incremental drift [Martineau 2022].

**When to act day-1 vs wait for the drift.**
- **Act day-1** when the thesis is CHALLENGED on fundamentals (soft guidance, margin peak, revision reversal). Large-cap information is incorporated fast; waiting forfeits the exit.
- **Wait** when the reaction is a beat-and-drop driven purely by positioning/IV crush while fundamentals CONFIRM -- the drop is often a positioning unwind, not a thesis break, and the revision response over days +2 to +5 clarifies it. MU's repeated beat-and-drops that preceded continued fundamental strength illustrate why a positioning-driven dip is not an automatic sell.
- **Never** act on the after-hours move alone; the sec. 5 fade statistics show after-hours pops can reverse.

For a memory name at its print: a beat-and-drop with CONFIRMED guidance (Tier 1-2) and continued positive revisions argues the thesis stands through the drift; a beat-and-drop with soft guidance (Tier 4-5) or a margin peak argues a day-1 CHALLENGE.

## 12. Thresholds-as-Data Master Table

This consolidated table is machine-readable; the consuming skills can cite it by row ID.

**A. Surprise-decile drift base rates (large-cap context).**

| Row | SUE decile | 60-day drift (1974-1986, B&T) | Modern large-cap (post-2006) | Source |
|-----|-----------|-------------------------------|------------------------------|--------|
| A1 | Top decile (good news) | ~+2% one-sided / hedge ~+4% | ~0 (attenuated) | Bernard & Thomas 1989; Martineau 2022 |
| A2 | Bottom decile (bad news) | ~-2% one-sided | ~0 (attenuated) | Bernard & Thomas 1989; Martineau 2022 |
| A3 | Hedge (top-bottom), 60d | ~8-9%/qtr (1980s-90s) | ~3% or lower late-2010s | Bernard & Thomas 1990; ScienceDirect review 2021 |
| A4 | FOS annualized hedge | ~25%/yr (1974-1981) | n/a | Foster, Olsen & Shevlin 1984 |
| A5 | Livnat-Mendenhall analyst-SUE | ~6.9-7.7% extreme deciles | larger w/ analyst def | Livnat & Mendenhall 2006 |

**B. Revision-breadth cutoffs (30-day window).**

| Row | Breadth (up / total) | 90d magnitude | Signal |
|-----|---------------------|---------------|--------|
| B1 | > 70% up | positive | CONFIRM (revision momentum) |
| B2 | 50-70% up | flat-positive | Neutral-positive |
| B3 | < 50% up | negative | CHALLENGE flag |
| B4 | MU mid-2025 reference | CY-EPS +22.38% / NY +32.42% (60d) | Strong CONFIRM [Zacks/Nasdaq 2025] |

**C. Implied-move percentile actions.**

| Row | Condition | Action |
|-----|-----------|--------|
| C1 | Implied move >> trailing realized (P3) + steep put skew + high retail | Beat-and-drop risk HIGH; size down expectation |
| C2 | Implied ~= realized | Normal; reaction likely within band (~70%) |
| C3 | Implied < realized | Options cheap; gap risk underpriced |
| C4 | Base rate | Actual move < implied in 72% of S&P events [CBOE/Volatility Box 2023] |
| C5 | IV crush expected | 30-60% IV collapse day +1 [FlashAlpha; projectoption] |

**D. Guidance-spread tiers (guide midpoint vs consensus).**

| Row | Spread | Tier | Signal |
|-----|--------|------|--------|
| D1 | > +5% | 1 | Thesis CONFIRM |
| D2 | +1% to +5% | 2 | Confirm if breadth positive |
| D3 | -1% to +1% | 3 | Positioning/whisper governs |
| D4 | -5% to -1% | 4 | CHALLENGE flag |
| D5 | < -5% | 5 | Strong CHALLENGE |

**E. Entity-specific extractable facts.**

- MU: FQ2-2026 non-GAAP EPS $12.20 vs $9.31 LSEG consensus, revenue $23.86B vs $20.07B, stock ~-4% next day, FQ3 guide ~$33.5B rev / ~$19.15 EPS (2026-03-18) [CNBC; Yahoo/Reuters]
- MU: FQ1-2026 non-GAAP EPS $4.78 vs ~$3.94, revenue $13.64B vs $12.95B, stock +5%+, FQ2 guide $18.70B (2025-12-17) [Micron 8-K; Alpha Spread]
- MU: FQ4-2025 EPS $3.03 vs ~$2.86, revenue $11.32B, stock -2.8% (2025-09-23) [Motley Fool]
- MU: FQ3-2025 EPS $1.91 vs $1.60, revenue $9.30B, popped then pared (2025-06-25) [CNBC]
- MU: FQ2-2025 EPS $1.56 vs $1.43, stock ~-8% (2025-03-20) [Motley Fool/Nasdaq]
- MU: FQ1-2025 EPS $1.79 vs $1.75, stock ~-13% on weak guidance (2024-12-18) [CNBC]
- MU: FQ3-2024 beat, stock ~-7% on light revenue forecast (2024-06-26) [Reuters]
- MU: beat-and-drop base rate ~5 of 9 quarters CY2024-Mar2026 (~56%) [compiled]
- AVGO: FQ2-2026 revenue $22.2B (+48%), EPS $2.44 vs ~$2.40, AI rev $10.8B (+143%), backlog >$30B, stock -14.44%, Q3 rev guide $29.4B (+84%), Q3 AI guide $16.0B vs ~$17.2B whisper, FY26 AI $56B (2026-06-03) [Broadcom 8-K; Yahoo; StockTitan]
- SNDK: FQ3-2026 EPS $23.41 vs ~$14.36-14.66 consensus (+63%), revenue $5.95B (+251% YoY), gross margin 78.4%, stock +14.5% (2026-04-30) [Public.com; 24/7 Wall St; Sandisk IR]
- SK Hynix: Q1 2026 revenue KRW 52.5763T (+198% YoY, +60% QoQ), operating profit KRW 37.6103T (72% margin), DRAM ASP +mid-60% QoQ, NAND ASP +mid-70% QoQ (2026-04-23) [SK Hynix; CNBC; StorageNewsletter]
- Hyperscaler 2026 capex: ~$725B combined, +77% from 2025's $410B; MSFT $190B, GOOGL ~$185-190B, AMZN ~$200B, META $115-145B [Tom's Hardware/FT; CreditSights]

**F. PEAD regime flag.**

| Row | Market-cap bucket | PEAD status | Source |
|-----|-------------------|-------------|--------|
| F1 | Large/mega-cap (MU, NVDA, AVGO) | ~zero since 2006 | Martineau 2022 |
| F2 | Microcap | persists (recently) | Martineau 2022; Subrahmanyam 2025 |
| F3 | Anomaly decay post-publication | ~58% out-of-sample | McLean & Pontiff 2016 |

## Sources

1. Ball, R. & Brown, P. (1968). An Empirical Evaluation of Accounting Income Numbers. Journal of Accounting Research 6, 159-178.
2. Foster, G., Olsen, C. & Shevlin, T. (1984). Earnings Releases, Anomalies, and the Behavior of Security Returns. The Accounting Review 59, 574-603.
3. Bernard, V. & Thomas, J. (1989). Post-Earnings-Announcement Drift: Delayed Price Response or Risk Premium? Journal of Accounting Research 27, 1-48.
4. Bernard, V. & Thomas, J. (1990). Evidence that Stock Prices Do Not Fully Reflect the Implications of Current Earnings for Future Earnings. Journal of Accounting and Economics 13, 305-340.
5. Chan, L.K.C., Jegadeesh, N. & Lakonishok, J. (1996). Momentum Strategies. Journal of Finance 51(5), 1681-1713.
6. Livnat, J. & Mendenhall, R.R. (2006). Comparing the Post-Earnings Announcement Drift for Surprises Calculated from Analyst and Time Series Forecasts. Journal of Accounting Research 44, 177-205.
7. Chordia, T. & Shivakumar, L. (2006). Earnings and Price Momentum. Journal of Financial Economics 80, 627-656.
8. Martineau, C. (2021/2022). Rest in Peace Post-Earnings Announcement Drift. SSRN.
9. McLean, R.D. & Pontiff, J. (2016). Does Academic Research Destroy Stock Return Predictability? Journal of Finance.
10. Givoly, D. & Lakonishok, J. (1979). The Information Content of Financial Analysts' Forecasts of Earnings. Journal of Accounting and Economics 1, 165-185.
11. Stickel, S.E. (1991). Common Stock Returns Surrounding Earnings Forecast Revisions. The Accounting Review 66(2).
12. Stickel, S.E. (1990). Predicting Individual Analyst Earnings Forecasts. Journal of Accounting Research 28(2).
13. Gleason, C. & Lee, C. (2003). Analyst Forecast Revisions and Market Price Discovery. The Accounting Review.
14. Scharfstein, D. & Stein, J. (1990). Herd Behavior and Investment. American Economic Review 80(3).
15. Brandt, M., Kishore, R., Santa-Clara, P. & Venkatachalam, M. Earnings Announcements are Full of Surprises. Duke working paper.
16. Jegadeesh, N. & Livnat, J. (2006). Post-Earnings-Announcement Drift: The Role of Revenue Surprises. Financial Analysts Journal 62(2).
17. Lou, D., Polk, C. & Skouras, S. A Tug of War: Overnight vs Intraday Expected Returns.
18. Boyarchenko, N., Larsen, L. & Whelan, P. The Overnight Drift. NY Fed Staff Report 917.
19. ScienceDirect (2021). A Review of the Post-Earnings-Announcement Drift.
20. UCLA Anderson Review (2025). Is Post-Earnings Announcement Drift a Thing? Again?
21. Zacks Investment Research. Zacks Rank methodology, Earnings ESP, performance disclosure. zacks.com.
22. CBOE study via Volatility Box (2023). Earnings IV crush statistics.
23. Option Alpha. IV Crush explainer. optionalpha.com.
24. projectoption. Implied Volatility / IV crush. projectoption.com.
25. MenthorQ. From Straddle Price to Expected Move.
26. Options Hawk. Calculating Expected Moves Using Options.
27. FlashAlpha Research. IV Crush Explained.
28. Micron Technology 8-K earnings releases FY2024-FY2026. SEC EDGAR.
29. CNBC (Dec 18, 2024; June 25, 2025; March 18, 2026; April 23, 2026). Micron and SK Hynix earnings coverage.
30. Motley Fool (June 3, 2026; Sep 24, 2025; May 27, 2026). AVGO, MU, SNDK coverage.
31. Yahoo Finance / Reuters (March 19, 2026; June 2026). MU and AVGO earnings.
32. TIKR (2026). Micron stock slips 4.3% after earnings.
33. Broadcom 8-K FY2026. SEC EDGAR.
34. StockTitan / Tech Insider (2026). Broadcom Q2 2026 earnings.
35. Public.com (2026). SNDK earnings report.
36. 24/7 Wall St. (May 15, 2026). Sandisk price prediction.
37. Sandisk Corporation IR (April 30, 2026). Fiscal Q3 2026 results.
38. SK Hynix Q1 2026 results; StorageNewsletter; Blocks & Files; NineScrolls; AlphaSense transcript (April 2026).
39. Tom's Hardware / Financial Times (2026). Hyperscaler capex $725B.
40. CreditSights (2026). Hyperscaler capex estimates.
41. TradingKey (2026). SK Hynix and SanDisk earnings previews.
42. Wall Street Oasis; SuperMoney; heygotrade. Sandbagging explainers.
43. Caltech. The Post-Earnings Announcement Drift: An Anomalous Anomaly.
44. TheStreet (2025). Micron forward P/E.
45. Simply Wall St (2026); stockanalysis.com (2026). Micron forecast, FQ2-2026 guidance, 2025 return.
