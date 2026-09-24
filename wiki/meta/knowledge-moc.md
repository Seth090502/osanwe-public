---
categories: [wiki]
type: moc
created: 2026-08-24
updated: 2026-09-13
status: active
confidence: high
tags:
  - topic/knowledge-base
  - topic/investing
  - topic/meta
aliases: ["master toc", "finance knowledge graph"]
related: ["*investing-moc* (not published)", "[[financial-analysis-contract]]"]
---

# Knowledge Master TOC (wiki/meta/knowledge-moc)

Routing reviewed: 2026-09-13. This is the existing FINANCE KNOWLEDGE SYSTEM
TOC: education, investment references, analyses, entities and skills. The separate
whole-vault router is `Atlas/_MOCs/knowledge-moc.md`; use that exact path for other
domains. Use this file's exact path, `wiki/meta/knowledge-moc.md`, for finance.

## Current method admission and priority routes

The document registry owned by `tools/pit/dataset_registry.py` distinguishes
inspected, scoped methods from unreviewed inventory. Obtain the current manifest
with `--documents-manifest`; a title, bibliography or confidence label does not
admit a source. Only approved spans and their applicable versions may govern
current conclusions. Older references below remain useful discovery/history
routes and require inspection for the specific claim. Do not assume that their
personal examples, full bibliographies or book originals have been reviewed.

| Supported question | Focused reference | Workflow owner |
|---|---|---|
| Are statement facts comparable across periods and revisions? | [[ref-financial-statement-evidence]] | /invest and Finance/Data evidence intake |
| Does this valuation capitalize cash flows and reconcile to equity? | [[ref-valuation-applicability]] | /invest, valuation.py |
| Which estimation, tail, cost or liquidity assumption changes the allocation? | [[ref-portfolio-risk-sensitivity]] | /portfolio, covariance.py, allocation.py |
| What return and attribution measure fits the cash flows? | [[ref-performance-attribution]] | /portfolio review, calcs_ledger.py |
| Does the result survive selection bias and independent assessment? | [[ref-empirical-research-validation]] | /backtest and evaluation protocol |
| Is an ETF's index exposure implementable on these terms? | [[ref-etf-implementation]] | /invest ETF route |
| Do instrument cash flows match the liability and inflation basis? | [[ref-fixed-income-liabilities]] | /portfolio risk and fixed-income owner |
| What household or tax information is necessary for this decision? | [[ref-household-tax-retirement]] | Finances and authorized host processing |

The examples have reproducible arithmetic and financial counterexamples. That
evidence does not establish expert approval or investment advantage. Admission
records specify the narrower inspected scope. Portable packages include only
explicitly reusable approved passages; supporting original excerpts and the
host-local index remain excluded.

The catalogue below the routing section preserves the 2026-08-25 snapshot.
Counts, positions, measured exposures, forecasts and "current book" descriptions
there are historical. Check each source's own period and current evidence before
using them. The education modules are offline syntheses with named literature;
their bibliographies do not establish verified original readings or full books.

## Select the foundation for the question

Follow `docs/financial-analysis-contract.md`, including its method-use note and
source verification rules. Select relevant sections from these existing files;
the table is a starting point, not a mandatory full-corpus preload. Atlas method
references live in `Atlas/sources/investing/`; education files live in
`wiki/research/`. A source title or agreement among investor frameworks is not
independent evidence, calibration, or permission to alter doctrine.

| Question | Education and method references | Application check |
|---|---|---|
| What expectations justify a company valuation? | *edu-corporate-finance* (not published), [[Atlas/sources/investing/ref-valuation-methodology|ref-valuation-methodology]] | Match FCFF/FCFE, reinvestment, discount basis and business type; expose reverse-DCF expectations and sensitivities. Operating DCF has explicit scope limits in institutional-methods. |
| Are reported earnings and financial quality credible? | [[wiki/research/edu-accounting-analysis|edu-accounting-analysis]], [[Atlas/sources/investing/ref-scoring-models|ref-scoring-models]], *ref-earnings-analysis-framework* (not published) | Inspect accounting definitions, recasts and original filings. Follow /invest's current scoring route; unresolved loss-maker/cyclical wording conflicts are not silently reconciled. |
| Is a portfolio diversified and robust to estimation error? | *edu-portfolio-theory* (not published), *ref-factor-lens* (not published) | Separate thesis labels from factor exposure, estimator error and tail co-movement; current account scope comes from /networth. Use the validated modules in institutional-methods. |
| Does a historical signal survive fair evaluation? | [[wiki/research/edu-quantitative-methods|edu-quantitative-methods]], [[Atlas/sources/investing/ref-quantitative-signals-library|ref-quantitative-signals-library]] | Availability dates, universe coverage, costs, multiple testing and holdout discipline precede performance interpretation; /backtest and the evaluation protocol own acceptance. |
| How do rates, liquidity or credit affect the thesis? | [[wiki/research/edu-macro-analysis|edu-macro-analysis]], [[wiki/research/edu-fixed-income|edu-fixed-income]], [[Atlas/sources/investing/ref-macro-landscape|ref-macro-landscape]] | Refresh dated macro inputs and distinguish causal channels from historical correlations; /brief and /market own current regime claims. |
| How does sector structure transmit demand and margins? | [[wiki/research/edu-semiconductor-industry|edu-semiconductor-industry]], [[wiki/research/edu-energy-power-markets|edu-energy-power-markets]], *ref-ai-supply-chain-deep-dive* (not published) | Trace customers, bottlenecks, capacity, power and substitution through current issuer/industry evidence; old sector snapshots are hypotheses to refresh. |
| What could invalidate the thesis or distort judgment? | *edu-behavioral-finance* (not published), [[Atlas/sources/investing/ref-investor-frameworks-2026|ref-investor-frameworks-2026]] | /challenge loads disconfirming evidence first. Investor lenses generate questions; they do not establish probabilities or voting-based confidence. |
| Could liquidity and implementation costs erase the result? | *edu-market-microstructure* (not published), *ref-technical-analysis-comprehensive* (not published) | Compare spread, impact, turnover and timing assumptions with the actual instrument; analysis does not authorize execution. |

The active executable method map is `docs/institutional-methods.md`. Knowledge
selection informs its assumptions and applicability; a named formula in a primer
does not mean it has a tested implementation. When a portable host lacks these
files, disclose the missing library and use inspected primary sources or an
explicitly selected public excerpt. Never claim that the full corpus was loaded.

## Finance Education Corpus

Ten vault-only theory primers (wiki/research/, `edu-` prefix). Each pairs
canonical theory with this vault's own measured data and doctrine. All carry
a "Related vault data" section mapping theory to the reference layer.

### Valuation and accounting fundamentals

- [[edu-accounting-analysis]] -- the three statements, accrual vs cash,
  revenue recognition (ASC 606), quality-of-earnings red flags, off-balance-
  sheet items, XBRL, manipulation detection heuristics.
- *edu-corporate-finance* (not published) -- DCF theory and tech practice, WACC builds,
  FCFF vs FCFE, capital structure (MM / trade-off / pecking order), working
  capital cycles, M&A accretion math, real options.
- [[edu-fixed-income]] -- present value, bond pricing, duration/convexity,
  curve construction, credit spreads, inflation-linked bonds, Fed toolkit,
  rates-to-equity transmission.
- [[edu-quantitative-methods]] -- stationarity, ARIMA/GARCH, regression,
  hypothesis testing and multiple comparisons, Monte Carlo, bootstrap,
  cointegration, Kalman filters, ML limits.

### Portfolio and market behavior

- *edu-behavioral-finance* (not published) -- prospect theory, cognitive bias catalog,
  disposition effect, overtrading evidence, and the bias-compensating system
  designs (doctrine ladders, gates, calibration) this vault already runs.
- *edu-market-microstructure* (not published) -- order types, spreads and market impact,
  dark pools, maker inventory, circuit breakers, short/squeeze dynamics,
  options market-maker hedging flows.
- *edu-portfolio-theory* (not published) -- Markowitz through factor investing: CAPM,
  Fama-French, APT, Black-Litterman, risk parity, Kelly sizing, correlation
  breakdown, anchored on a covered book's measured effective-bets statistic.

### Sector frameworks

- [[edu-semiconductor-industry]] -- industry structure, value chain, foundry
  economics, memory cycles, equipment intensity, fabless vs IDM, advanced
  node economics, export-control impact map, per-segment metrics.
- [[edu-energy-power-markets]] -- electricity markets, nuclear, renewables
  intermittency and storage, grid infrastructure, datacenter power demand,
  PPAs, IPPs vs regulated utilities, commodity exposure.
- [[edu-macro-analysis]] -- GDP reading, CPI/PCE/PPI measurement, monetary
  transmission, fiscal policy and issuance, currencies, business-cycle dating,
  geopolitical risk scoring, the weekly investor macro routine.

## Investment Reference Layer

Generated/measured references in wiki/research/ (`ref-` prefix), organized by
type. Ingest reports (`*-ingest-*`) sit under Data as source archives.

### Macro

- [[ref-fed-policy-complete]] -- complete Fed policy picture from the factor
  store: funds rate path, balance sheet, reaction function.
- [[ref-fed-liquidity-engine]] -- QT, reserves, repo, RRP; the net-liquidity
  verdict model behind the brief's liquidity overlay.
- *ref-yen-carry-global-liquidity* (not published) -- yen carry unwind anatomy, DEXJPUS
  episode census, global liquidity transmission into semis.
- [[ref-inflation-rates-complex]] -- inflation and rates complex: breakevens,
  real rates, the DGS10 gate lineage now carried by DFII10.
- [[ref-market-regime-detector]] -- regime classification over 1,056 sessions;
  transition matrix; feeds brief, signals, and doctrine bands.

### Sector

- [[ref-semiconductor-value-chain]] -- semi value chain reference: segments,
  demand engines, cycle position, per-name exposure map.
- *ref-supply-chain-dependency* (not published) -- AI value chain dependency map: who earns
  which system-level margin, single-source chokepoints.
- [[ref-energy-power-complex]] -- energy / AI-power complex: generators,
  IPPs, utilities, fuel and turbine supply, PPA economics.
- [[ref-datacenter-infrastructure]] -- datacenter infrastructure: capacity
  pipeline, power density, REIT vs developer models.
- *ref-crypto-deep-dive* (not published) -- crypto majors plus the theme-beta institutional
  coverage.
- [[ref-ai-supply-chain-complete]] -- Tier 0-7 dependency graph across the
  full AI stack; edge-level supplier relationships, single-source flags.
- *ref-ai-outcome-scenarios* (not published) -- AI buildout outcome scenarios mapped to
  portfolio exposure; complements *ref-cross-analysis-synthesis* (not published).
- [[ref-theme-alpha|theme-alpha thesis layer (Atlas)]] and its ingest archives:
  [[ref-theme-alpha-ingest-2026-04-22]], [[ref-theme-alpha-ingest-2026-07-16]],
  [[ref-ai-supply-chain-deep-dive-ingest-2026-05-06]],
  [[ref-ai-power-grid-deep-dive-ingest-2026-05-06]],
  [[ref-memory-storage-cycle-deep-dive-ingest-2026-05-06]],
  *ref-defense-aerospace-space-economy-deep-dive-ingest-2026-05-06* (not published),
  [[ref-theme-beta-institutional-crypto-deep-dive-ingest-2026-05-06]].

### Quantitative

- [[ref-correlation-matrix-full]] -- full 90-day pairwise correlation matrix
  across the covered universe; N_eff inputs; crisis-co movement notes.
- [[ref-composite-scoring]] -- composite scoring engine: quality/momentum/
  valuation sleeves for every ticker.
- *Factor lens (Atlas)* (not published) -- factor decomposition of the
  book; concentration risk view.
- *ref-theme-detection* (not published) -- theme detection engine over the /invest corpus.
- *ref-synthetic-benchmarks* (not published) and *ref-synthetic-benchmarks-extended* (not published) --
  true-benchmark alpha vs the opportunity set a book actually competes with.
- *ref-options-derivatives-layer* (not published) -- options overlay: IV context, skew,
  earnings-event structures per name.

### Portfolio

- *ref-portfolio-risk-decomposition* (not published) -- factor exposures, risk
  contributions, concentration ladder on a modelled book.
- *ref-portfolio-optimization* (not published) -- a modelled book vs optimal weights;
  rebalance paths under doctrine ceilings.
- *ref-hedge-construction* (not published) -- systemic risks mapped to measured
  instruments; sleeve sizing logic.
- *ref-scenario-stress-test* (not published) -- six macro shocks applied to a modelled
  book; trigger-to-P&L playbook.
- *ref-cross-analysis-synthesis* (not published) -- synthesis across all 51 wave analyses:
  consensus leaders, contrarian file, contradiction log, scenario playbook.
- *ref-earnings-analysis-framework* (not published) -- earnings framework across the covered
  names; post-print rerun checklist.
- *ref-earnings-calendar* (not published) -- dated earnings calendar for covered names.
- *ref-technical-analysis-comprehensive* (not published) -- technical read on every covered
  ticker: trend, levels, zones wired to doctrine triggers.
- [[ref-momentum-backtest]] and [[ref-strategy-backtest-results]] --
  momentum baseline vs SPY and the V1/V2/V3 variant results (honest costs).

### Data

- [[ref-financial-statements]] -- EDGAR XBRL statement reference feeding
  quality checks and reverse-DCF inputs.
- *ref-institutional-flow-analysis* (not published) -- filings-based institutional money
  flow analysis.
- *ref-institutional-insider-tracking* (not published) -- institutional ownership and
  insider transaction tracking from EDGAR feeds.
- [[ref-alternative-data-signals]] -- non-price alternative signals mined
  from filings and disclosures.
- Ingest archives: [[ref-earnings-playbook-ingest-2026-06-10]]
  (earnings mechanics + PEAD), *ref-factor-lens-ingest-2026-06-10* (not published),
  *ref-claude-leveraged-income-2026-ingest-2026-04-29* (not published).

## Analysis Corpus

All 51 wave analyses live in Efforts/osanwe-v2-overhaul/_work/ (mission
scratch space; wikilinks resolve via the audit's extra-targets wiring).
Cross-file synthesis: *ref-cross-analysis-synthesis* (not published). Entity notes carry
the symmetric "latest wave analysis" links back.

### Large-cap names

*wave2-amd-analysis* (not published), *wave2-amzn-analysis* (not published), *wave2-googl-analysis* (not published), *wave2-meta-analysis* (not published),
*wave1-msft-analysis* (not published), *wave1-mu-analysis* (not published), *wave1-nvda-analysis* (not published), *wave1-sndk-analysis* (not published),
*wave2-tsla-analysis* (not published), *wave1-tsm-analysis* (not published), *wave2-vgt-analysis* (not published), *wave1-voo-analysis* (not published)

### Wave E -- energy and compute-cooling complex

*waveE-bwxt-analysis* (not published), *waveE-ceg-analysis* (not published), *waveE-etn-analysis* (not published),
*waveE-gev-analysis* (not published), *waveE-nee-analysis* (not published), *waveE-tln-analysis* (not published),
*waveE-vrt-analysis* (not published), *waveE-vst-analysis* (not published)

### Wave I -- AI server OEMs and datacenter REITs

*waveI-dell-analysis* (not published), *waveI-dlr-analysis* (not published), *waveI-eqix-analysis* (not published),
*waveI-hpe-analysis* (not published), *waveI-smci-analysis* (not published)

### Wave N -- AI networking and interconnect

*waveN-anet-analysis* (not published), *waveN-avgo-analysis* (not published), *waveN-cohr-analysis* (not published),
*waveN-mrvl-analysis* (not published)

### Wave S -- semiconductor equipment, EDA, IP

*waveS-amat-analysis* (not published), *waveS-arm-analysis* (not published), *waveS-asml-analysis* (not published),
*waveS-klac-analysis* (not published), *waveS-lrcx-analysis* (not published), *waveS-snps-analysis* (not published)

### Wave T -- software, cloud, defense primes, neocloud

*waveT-crwv-analysis* (not published), *waveT-lmt-analysis* (not published), *waveT-nbis-analysis* (not published),
*waveT-noc-analysis* (not published), *waveT-now-analysis* (not published), *waveT-orcl-analysis* (not published),
*waveT-pltr-analysis* (not published), *waveT-rtx-analysis* (not published)

### Wave U -- utilities, power names, crypto kernels

*waveU-AEP-analysis* (not published), *waveU-BE-analysis* (not published), *waveU-COIN-analysis* (not published),
*waveU-DUK-analysis* (not published), *waveU-FLNC-analysis* (not published), *waveU-PPL-analysis* (not published),
*waveU-SO-analysis* (not published), *waveU-XRP-analysis* (not published)


### Semiconductor supply chain -- 2026-08-24 ingest batch

Newly wired entities (bars since 2021-08-24 in the factor store; entity
notes + benchmark profiles + data annexes generated 2026-08-24):

- Equities: *ASX* (not published), *ACLS* (not published), *TER* (not published), *ENTG* (not published), *MPWR* (not published), *GLW* (not published),
  *TEL* (not published), *UCTT* (not published), *COHU* (not published)
- Sector ETFs: *SOXX* (not published), *XLE* (not published), *XLF* (not published), *XLI* (not published), *XLP* (not published), *XLRE* (not published),
  *XLU* (not published), *XLV* (not published), *XLY* (not published)
- Existing semi supply-chain entities refreshed with generated data layers:
  *CDNS* (not published), *GFS* (not published), *AMKR* (not published), *ONTO* (not published), *AEIS* (not published), *APH* (not published), *SMH* (not published)

Data sources: per-ticker benchmark profiles under
*reference-index* (not published); XBRL statement data via [[ref-financial-statements]];
value-chain placement in [[ref-semiconductor-value-chain]] and
*ref-supply-chain-dependency* (not published). Landed wave analyses (2026-08-24 supply-chain wave):

- *waveSC-aph-analysis* (not published) -- APH: connectors, backplanes, high-speed interconnect.
- *waveSC-cohu-analysis* (not published) -- COHU: test handling and metrology instrumentation.
- *waveSC-acls-analysis* (not published) -- ACLS: plasma abatement and thermal subsystems.
- *waveSC-aeis-analysis* (not published) -- AEIS: semiconductor thermal/ESD solutions.
- *waveSC-amkr-analysis* (not published) -- AMKR: OSAT assembly and test services.
- *waveSC-asx-analysis* (not published) -- ASX: advanced packaging and test equipment.
- *waveSC-cdns-analysis* (not published) -- CDNS: EDA and digital design implementation.
- *waveSC-entg-analysis* (not published) -- ENTG: specialty materials and wafer reclaim.
- *waveSC-gfs-analysis* (not published) -- GFS: global foundries, differentiated nodes.
- *waveSC-glw-analysis* (not published) -- GLW: optical fiber and connectivity.
- *waveSC-mram-analysis* (not published) -- MRAM-class memory and embedded NVM exposure.
- *waveSC-mpwr-analysis* (not published) -- MPWR: analog/power management ICs.
- *waveSC-onto-analysis* (not published) -- ONTO: process control and inspection.
- *waveSC-tel-analysis* (not published) -- TEL: connectivity and sensor solutions.
- *waveSC-ter-analysis* (not published) -- TER: automated test equipment.
- *waveSC-uctt-analysis* (not published) -- UCTT: semiconductor consumables and components.


### Wave X -- 2026-08-25 ad-hoc batch

Equities: *waveX-aaoi-analysis* (not published) (optical modules),
*waveX-abbny-analysis* (not published) (ABB ADR),
*waveX-alab-analysis* (not published) (Arista), *waveX-amba-analysis* (not published) (Ambarella),
*waveX-gd-analysis* (not published) (General Dynamics, AUKUS submarine prime),
*waveX-lhx-analysis* (not published) (L3Harris, defense electronics).

Crypto: *waveX-link-usd-analysis* (not published) (Chainlink).

Late additions (2026-08-24/25): *waveX-AVAV-analysis* (not published) (AeroVironment),
*waveX-BAH-analysis* (not published) (Booz Allen), *waveX-hii-analysis* (not published) (HII, naval
shipbuilding), *waveX-mbly-analysis* (not published) (Mobileye),
*waveX-mksi-analysis* (not published) (MKS Instruments), *waveX-soxx-analysis* (not published)
(SOXX ETF benchmark read), *waveX-ateyy-analysis* (not published) (Advantest ADR),
*waveX-spcx-analysis* (not published) (SpaceX private-markets read),
*waveX-hims-analysis* (not published) (HIMS, telehealth post-squeeze),
*waveX-CRDO-analysis* (not published) (Credo, connectivity silicon),
*waveX-usar-analysis* (not published) (USA Rare Earth), *waveX-hubb-analysis* (not published)
(Hubbell), *waveX-mpwr-analysis* (not published) (Monolithic Power),
*waveX-nrg-analysis* (not published) (NRG Energy).

### Wave 7 -- memory and defense hardware kernels

*wave7-WDC-analysis* (not published) -- Western Digital storage cycle read.
*wave7-XAR-analysis* (not published) -- SPDR S&P Aerospace & Defense ETF kernel.

### Wave 8 -- sector ETF kernels

*wave8-xlp-analysis* (not published) -- Consumer Staples sector SPDR.
*wave8-xlre-analysis* (not published) -- Real Estate sector SPDR.

Wave 7 ETF kernel: *wave7-XLE-analysis* (not published) -- Energy sector SPDR.

## Entity Universe

Entity navigation lives in the Atlas MOC layer:

- *investing-moc* (not published) -- portfolio, watchlist, research log; routes into
  wiki/entities/tickers/ (108 ticker notes) and wiki/entities/companies/
  (51 company notes).
- Whole-vault domain router: [[knowledge-moc]] (Atlas/_MOCs).
- Concept nodes: Atlas/concepts/investing and sources indexes under
  Atlas/sources/investing (26 canonical reference docs).

## Skills Index

Canon skills in .agents/skills/ (synced to .claude/skills/). Use the skill
when its trigger matches; each SKILL.md carries full modes and quality rules.

| Skill | Purpose | When to use |
|---|---|---|
| invest | Full institutional analysis of ONE ticker | Pre-entry, post-earnings rerun, conviction refresh |
| portfolio | Advisory, risk, sizing, review, journal mega-skill | Strategic memo, risk dashboard, sizing worksheet, periodic review |
| market | Watch, screen, signals, regime, earnings dispatcher | Daily surveillance, screener runs, regime check, event calendar |
| brief | Morning briefing, PDB-style | Start of trading day, before FOMC/CPI/earnings |
| backtest | Strategy simulation on the factor store | Testing hypothetical rules, zero-lookahead queries |
| challenge | Red-team an EXISTING thesis (no record written) | Bear case requested, confidence shifted >10 pts, STRESSED status |
| decide | Commit a NEW consequential choice (writes record) | Offers, deploy/exit calls, build commitments |
| gate | Judgment gates f/b/t/calibrate via gate-eval.py | Before ADD/TRIM/EXIT, before new builds, before manual status flips |
| deep | Compose Deep Research prompts (never runs them) | Commissioning 100+ source external research |
| ingest | extract claims / file whole documents | After material news or onboarding dumps |
| networth | Live whole-portfolio snapshot | "What is it worth right now," concentration checks |
| retro | Atomic session close-out | Ending substantive work; captures decisions |
| synthesis | spark (cross-domain patterns) / consolidate lessons | Weekly scheduler runs; playbook mining |
| local | Route work through the local qwen worker | Bulk extraction at 2-5% token cost |
| vault | Integrity audit and maintenance | Broken-link/frontmatter audits; health score |

Method companions referenced above live inside skill dirs (e.g.
market/ref-screening-logic.md, portfolio/ref-risk-methodology.md); they are
indexed for resolution but audited only in their canon home.

## Maintenance Rules

- Update the "Last updated" line when editing this index.
- New edu/ref docs get one line here in the right section, same day they land.
- Wave analyses are indexed by wave prefix; keep ratings OUT of this file
  (they age fast) -- ratings live in the files themselves and in
  *ref-cross-analysis-synthesis* (not published).
- ASCII only; no numbers invented here -- this file routes, it does not assert.
