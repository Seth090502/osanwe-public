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
  - topic/accounting
  - topic/financial-statements
  - topic/quality-of-earnings
  - topic/fundamental-analysis
related: ["[[edu-quantitative-methods]]", "[[edu-fixed-income]]", "edu-behavioral-finance", "edu-corporate-finance", "investing-moc"]
---

# Accounting Analysis: Reading Financial Statements Like a Skeptic

GENERATED: 2026-08-24. Education-layer reference in this vault's finance
corpus. Financial statements are the raw input to every valuation, and they
are prepared by interested parties under rules with real discretion. This
file covers how the three statements interlock, where modern revenue rules
changed tech accounting, why free cash flow outranks net income as the
honest number, how to smell manipulated statements early, and how machine-
readable filings (XBRL) let analysis scale. The operating stance throughout:
not "companies lie" but "incentives shape presentation," so the analyst's
job is to restate what management shows into economic reality.
Companions: [[edu-fixed-income]], [[edu-quantitative-methods]],
edu-behavioral-finance, edu-corporate-finance.

## Table of contents

1. Why accounting literacy is an edge (and a defense)
2. The three statements and how they link
3. Accrual versus cash accounting: why FCF beats net income
4. Revenue recognition: ASC 606 and its tech-sector effects
5. Quality of earnings red flags
6. Segment reporting and geographic breakdown
7. Off-balance-sheet items
8. XBRL taxonomy and machine-readable filings
9. Common manipulations and detection heuristics
10. A practical statement-analysis workflow

## 1. Why accounting literacy is an edge (and a defense)

Two claims justify this file in an investing corpus:

1. Edge: markets price headline numbers (EPS, revenue growth) efficiently,
   but the QUALITY of those numbers -- accrual composition, cash conversion,
   segment mix, footnote disclosures -- is persistently less efficiently
   processed. Academic work since Sloan (1996) documents that high-accrual
   firms underperform low-accrual firms; the anomaly decayed but never
   fully died because reading footnotes does not scale for most participants.
2. Defense: the catastrophic losses in investing history are dominated by
   accounting failures recognized late (Enron, WorldCom, Wirecard, Luckin).
   Almost all of them showed detectable symptoms years earlier: widening
   gaps between earnings and operating cash flow, receivables outgrowing
   revenue, serial "one-time" charges, opaque segment disclosure.

The vault's calibration culture applies here directly: an analyst who
cannot read the statements should be running near-zero confidence on any
single-name thesis; accounting skill is one of the few inputs that moves
justified confidence up.

## 2. The three statements and how they link

### 2.1 The trio

- Income statement (P&L): performance over a period. Revenue -> COGS ->
  gross profit -> opex -> operating income -> interest/taxes -> net income.
  Accrual-based; contains estimates everywhere (reserves, useful lives,
  recognition timing).
- Balance sheet: stocks at a point in time. Assets = Liabilities + Equity.
  Every P&L event lands somewhere here; the balance sheet is the ledger of
  everything not yet expensed or distributed.
- Cash flow statement: actual cash movements over the period, reconciled
  from accrual earnings. Operating, investing, financing sections. Least
  manipulable at the total level (cash is verifiable), though classification
  BETWEEN sections offers room for games.

### 2.2 The articulation (how they tie)

Trace one dollar through the machine:

1. Sale booked on credit: revenue up on P&L; accounts receivable UP on
   balance sheet. No cash yet.
2. Customer pays: AR converts to CASH; the CF statement's operating section
   reverses the earlier non-cash revenue via the change in working capital.
3. Company buys equipment: no P&L impact today; investing outflow on CF;
   PP&E up on balance sheet.
4. Depreciation: non-cash expense spread over useful life; reduces P&L
   income each period; accumulated depreciation grows on the balance sheet;
   added BACK in the CF operating section.
5. Net income flows into retained earnings (equity section), closing the
   loop: BalanceSheet(t) = BalanceSheet(t-1) + NI - dividends +/- other
   equity moves.

Practical checks that articulation is intact: change in cash on the CF
statement equals the change in the balance-sheet cash lines; retained
earnings roll-forward reconciles; comprehensive income explains the rest.
A filing whose pieces do not tie is a five-alarm data-quality problem.

### 2.3 Where each statement is most informative

- Growth-stage tech: CF statement first (burn, deferred-revenue dynamics),
  then income statement (unit economics trend), balance sheet last
  (runway = cash / burn).
- Cyclical industrials: balance sheet leverage through cycle + P&L margin
  trajectory.
- Financials: balance sheet IS the business; income statement is mostly
  derived from it. Requires its own toolkit (this file stays general).

## 3. Accrual versus cash accounting: why FCF beats net income

### 3.1 Accrual logic and its necessity

Accrual accounting matches revenues to the periods they are EARNED and
expenses to the periods INCURRED, regardless of cash timing. Without it, a
company billing multi-year contracts would show lumpy meaningless income.
Accruals are necessary -- and they are also where judgment enters:
estimates of bad debts, warranty costs, returns, asset lives, impairments.
Every estimate is a lever someone can pull.

### 3.2 The accrual gap as a signal

Net income minus operating cash flow = accruals (broadly). Persistent
positive earnings with lagging cash conversion is the classic warning:
revenues recognized ahead of cash, capitalizing costs aggressively,
channel stuffing inflating AR. One year can be noise (working-capital
growth in fast expansion); three consecutive years of divergence is a
thesis-level finding.

Sloan's accrual anomaly formalized it: investors fixate on earnings levels
and systematically misprice accrual COMPONENTS; low-accrual portfolios beat
high-accrual ones historically. Tradeable alpha faded post-publication;
the defensive use (avoiding junk-quality earners) remains robust.

### 3.3 Free cash flow definitions and their uses

- FCF (simple): CFO - capex. The workhorse. Use for mature businesses.
- Owner earnings (Buffett): NI + D&A +/- other non-cash - maintenance
  capex - SBC treated as cost. Honest for owner-operator thinking.
- Levered vs unlevered: FCFE (after interest) belongs to equity holders;
  FCFF (before interest) services all capital. Match the discount rate to
  the flow when you value.
- Caveat: simple FCF flatters companies that pay employees in stock (SBC
  is non-cash until it isn't -- buybacks offsetting dilution ARE cash).
  For SBC-heavy tech, compute FCF after treating SBC as an expense.
  Section 4.4 quantifies why.

### 3.4 When net income IS the better lens

Balance the skepticism: financials/insurers (accruals are the business),
REITs (depreciation overstates economic cost decline -- hence FFO/AFFO),
and hypergrowth phases funded deliberately by deferred-revenue float all
need adjusted lenses rather than naive FCF worship. The rule is not "FCF
always"; it is "understand WHY the accrual/cash gap exists before trusting
either number."

## 4. Revenue recognition: ASC 606 and its tech-sector effects

### 4.1 What ASC 606 did

ASC 606 (Revenue from Contracts with Customers; IFRS 15 internationally),
effective ~2018, replaced industry-specific patchworks with a single
five-step model:

1. Identify the contract.
2. Identify performance obligations (distinct promises).
3. Determine transaction price (including variable consideration).
4. ALLOCATE price to obligations on relative standalone selling prices.
5. Recognize revenue when each obligation is SATISFIED (control transfers).

The philosophy shift: from "risks and rewards" toward transfer-of-control,
with forced unbundling of bundled deals and explicit treatment of variable
consideration, significant financing components, and contract cost
capitalization.

### 4.2 Tech-sector consequences that matter to analysts

- Bundled hardware+services+support deals must be split; more revenue gets
  DEFERRED (contract liabilities) and recognized ratably or on delivery of
  each element. Deferred revenue ballooned on balance sheets of SaaS and
  device-plus-services firms; it became a leading indicator (billings).
- Licenses with right-to-use vs right-to-access distinctions change timing:
  on-premise perpetual licenses can still recognize upfront; SaaS
  subscriptions ratable. Business-model shifts therefore MOVE REPORTED
  GROWTH even when cash economics barely changed -- analysts must separate
  model migration from demand acceleration.
- Sales commissions and certain fulfillment costs got CAPITALIZED
  (amortized) rather than expensed immediately -- flattering near-term EBIT
  modestly; watch amortization creep in later years.
- Variable consideration (usage fees, rebates, penalties) constrained
  estimates: revenue smoothing options narrowed but estimate ranges remain.

### 4.3 Metrics that pair with 606-era statements

For subscription businesses, reported GAAP growth must be read alongside:

- Billings = revenue + change in deferred revenue (+ change in unbilled
  AR). Nearer to cash reality than revenue alone.
- RPO/cRPO (remaining performance obligations): contracted backlog not yet
  recognized; the forward-looking book.
- Net revenue retention and cohort gross retention: quality of the base.
- Cash collection efficiency: DSO trend and free-cash conversion against
  billings, not just revenue.

### 4.4 Stock-based compensation: the recurring controversy

SBC is a real economic cost (dilution) paid in equity. Companies tout
non-GAAP EPS excluding SBC; the honest treatment adds SBC back into the
denominator of ownership math: if SBC runs 10% of revenue annually and
buybacks merely neutralize dilution, the company spends real cash to stand
still. Vault practice: treat SBC as expense for valuation; separately track
buyback-adjusted share count trend as the tell for whether dilution is
being managed or papered over.

## 5. Quality of earnings red flags

### 5.1 The core ratios (compute these every time)

1. CFO / Net Income: sustained < 1.0 warrants explanation; healthy
   businesses typically run above 1.0 once depreciation add-backs dominate.
2. Receivables growth vs revenue growth: AR growing materially faster =
   revenue pulled forward or fictitious. Same test for inventory (COGS
   stuffing) in product businesses.
3. Gross PP&E vs depreciation: slowing capex with rising D&A hints at past
   overinvestment; sudden useful-life EXTENSIONS flatter earnings (airline
   and media examples recur).
4. Days metrics: DSO, DIO, DPO trajectories. Deteriorating cash-conversion
   cycle during claimed strength is contradiction in terms.
5. Accruals ratio: (NI - CFO) / average total assets; rank against sector.

### 5.2 Presentation-level tells

- Serial restructuring charges: recurring "non-recurring" costs are
  operating costs wearing a costume; add them back into normalized
  earnings.
- Frequent one-time gains propping EPS (asset sales, pension assumption
  tweaks, legal settlements received): strip them.
- Non-GAAP metric proliferation: each added adjusted metric is a place to
  hide a cost. Compare the company's own non-GAAP definition changes
  year-over-year; quiet redefinitions are deliberate.
- Round-trip revenue: simultaneous buy/sell with counterparties (capacity
  swaps, vendor-financed purchases). Vendor financing is channel stuffing
  with extra steps: watch financing receivables and related-party notes.
- Auditor changes mid-stream, audit fees falling below peer norms, CFO
  churn (multiple CFO exits inside two years), delayed filings, material
  weaknesses disclosed -- governance correlates with numbers.

### 5.3 Sector-specific quick screens

- Software: deferred revenue + RPO trend vs bookings narrative; SBC share
  of revenue; capitalized commission balances growing faster than salesforce.
- Retail/product: inventory days vs sales growth; vendor rebate reserves;
  lease-liability restatements under ASC 842.
- Biotech/pharma: milestone revenue recognition, rebate/chargeback reserve
  swings (gross-to-net), collaboration accounting.
- Lenders: allowance build/release direction vs charge-offs; day-one
  losses on origination; gain-on-sale reliance.

## 6. Segment reporting and geographic breakdown

### 6.1 What ASC 280 requires

Public companies disclose reportable segments (management approach --
segments as management organizes internally), with segment revenue,
profitability measure, assets, and reconciliation to consolidated totals.
ASU 2023-07 (effective FY2024 filings) expanded this significantly: public
disclosure now requires significant segment EXPENSES regularly provided to
the CODM (chief operating decision maker), the CODM's title, and other
segment items -- the biggest transparency upgrade in segment reporting in
decades. New filers and older analyses need care comparing pre/post
disclosure regimes.

### 6.2 Why segments carry the thesis

Consolidated numbers hide mix shifts that dominate value:

- Declining legacy segment masking growth segment economics (or vice versa
  -- glamour segment subsidization by cash-cow segment).
- Geographic concentration risk (single-country revenue exposure, FX
  translation vs transaction exposure distinction).
- Intersegment sales: eliminate or they inflate both revenue and apparent
  diversification.
- Margin divergence across segments means blended margins move with MIX
  even with zero operational improvement -- a common way headline margin
  expansion misleads.

### 6.3 Practical decomposition habits

- Build a small segment matrix per year: revenue x growth x margin per
  segment; compute each segment's contribution to total profit CHANGE.
- Read geographic notes for customer-vs-property basis (where revenue is
  billed vs where assets sit); sanctions/tariff sensitivity lives here.
- Watch for segment recasts: when management redefines segments, prior
  comparatives get restated -- sometimes to obscure a deteriorating line.
  Recompute growth only on like-for-like recast data.
- Unallocated corporate expense trends reveal where HQ bloat hides.

## 7. Off-balance-sheet items

### 7.1 The taxonomy of what sits outside

Post-Enron reforms (FIN 46R on VIEs, ASC 842 leases on-balance) moved many
items onto the balance sheet, but economically meaningful exposures remain
outside or disguised:

- Operating leases pre-2019 (now capitalized, but check discount-rate
  assumptions used -- aggressive rates shrink the liability).
- Unconsolidated affiliates/VIEs and JVs: proportional debt and guarantees
  not in consolidated leverage. Airlines' regional-capacity deals and
  retailers' supplier-financing arrangements historically lived here.
- Guarantees and indemnifications: parent guarantees of JV/sub debt,
  tax indemnities, litigation contingencies (loss contingencies accrue only
  when PROBABLE and estimable -- the definition leaves room for hope).
- Pension underfunding: projected deficits beyond the recognized net
  liability, sensitive to discount-rate assumptions (each 25bp drop in
  assumed rate materially raises PBO).
- Purchase obligations and take-or-pay contracts: committed future spend
  disclosed in contractual-obligations tables, absent from leverage ratios.
  Data-center/cloud commitments at AI-era tech are the modern case study:
  multi-year tens-of-billions commitments that ratio screens miss entirely.
- Factoring/securitization: receivables sold WITH recourse or via revolving
  structures return as contingent exposure and distort DSO improvements.

### 7.2 Detection approach

Read these specific places every time: commitments-and-contingencies note,
subsequent events, related-party transactions, VIE note, contractual
obligations table, MD&A liquidity section, and the equity-method
investments note. Compute an ADJUSTED net-debt figure including lease
liabilities, pension deficit, and material purchase obligations before
comparing leverage across companies; unadjusted comparisons systematically
favor the most aggressive reporters.

## 8. XBRL taxonomy and machine-readable filings

### 8.1 What XBRL is

XBRL (eXtensible Business Reporting Language) tags every fact in SEC
filings to a taxonomy concept (us-gaap namespace, e.g., us-gaap:Revenues,
us-gaap:NetIncomeLoss, dei:EntityCommonStockSharesOutstanding) with period,
unit, and dimensional context (segment members). EDGAR serves structured
data (Financial Statements datasets, Frames API, companyconcept/
companyfacts endpoints) alongside the human HTML. Filings are therefore
queryable databases, not just PDFs -- the difference between reading one
10-K and screening ten thousand.

### 8.2 Practical mechanics worth knowing

- Taxonomy versioning: us-gaap concepts evolve (e.g., RevenueFromContract-
  WithCustomerExcludingAssessedTax arriving post-606); historical series
  break at transitions. Robust pipelines map multiple concepts to one
  analytic series and record which tag fed which point.
- Dimensions: segment facts live as axis/member contexts
  (StatementBusinessSegmentsAxis); naive scrapers that take untagged
  consolidations miss segment detail; dimension-aware extraction gets it.
- Custom extension tags: companies define their OWN concepts when standard
  ones do not fit ("custom:" namespace). Heavy custom-tag use in key lines
  complicates cross-company comparison -- itself a mild comparability flag.
- Sign conventions and scales trip naive consumers (negative revenue
  adjustments, shares in raw counts). Validate sums against known totals.
- R-files (financial-statement renderings) plus the FilingSummary.xml give
  clean table structure; the frames API aligns facts across calendar
  windows for point-in-time studies.

### 8.3 What this enables in vault-style workflows

- Point-in-time fundamentals joins (availability date = filing date) kill
  look-ahead bias in backtests -- the discipline Section 6 of
  [[edu-quantitative-methods]] demands.
- Automated red-flag screens at scale: CFO/NI, accruals ratio, DSO deltas,
  custom-tag density, disclosure-length anomalies across whole universes.
- Consistency monitoring: same-company tag usage drift signals policy
  changes worth reading about.

Caveats: XBRL carries what was filed, errors included; amended filings
(10-K/A) require supersession logic; and structured data cannot replace
reading the notes for context -- it routes ATTENTION, not judgment.

## 9. Common manipulations and detection heuristics

### 9.1 The classic playbook (know the moves to see the counters)

1. Channel stuffing / pull-forward: ship early, loosen credit terms.
   Detect: AR and DSO spike, quarter-end revenue concentration, returns
   reserve jumps, next-quarter softness.
2. Big-bath restructuring: cram future costs into one terrible quarter to
   flatter all subsequent quarters. Detect: restructuring recurring across
   cycles, "adjusted" EPS walking up while GAAP stagnates.
3. Cookie-jar reserves: over-reserve in good times, release in bad.
   Detect: reserve balances inversely tracking results; releases timed to
   guidance shortfalls.
4. Capitalize-and-hide: push opex onto the balance sheet (WorldCom line
   costs; capitalized software/commissions/fulfillment today). Detect:
   unusual capex/intangibles growth vs peers, capitalized-cost amortization
   swelling later, declining current-year expense despite flat volumes.
5. Revenue fabrication (the endgame fraud): fake customers, round-trips.
   Detect: receivables and cash diverge badly, auditor resignation,
   undisclosed related parties, impossible unit economics vs physical
   capacity checks.
6. Timing games within GAAP: useful-life extensions, discount-rate moves
   on pensions, percentage-of-completion aggressiveness, software
   development phase judgments.
7. Classification shuffles: moving expenses between operating and
   "special" lines; parking losses in discontinued operations; presenting
   pro-forma metrics excluding real costs.
8. Debt disguise: securitizations, supply-chain financing (watch for its
   separate disclosure requirement adopted recently), repo games at banks,
   operating-commitment substitutes for debt (Section 7).

### 9.2 Composite detection framework

Layer the screens rather than trusting any single one:

- Layer 1 (mechanical): the Section 5.1 ratios, ranked cross-sectionally.
- Layer 2 (narrative): MD&A tone/explanation vs numbers; footnote length
  growth around contested items; litigation/regulatory mentions.
- Layer 3 (governance): auditor tenure/change, audit-committee financial
  expertise, insider selling patterns around optically strong quarters,
  compensation metrics tied to the exact non-GAAP measures being flattered.
- Layer 4 (external): short-seller reports deserve engagement, not
  dismissal; supplier/customer channel checks; hiring-site posting volume
  as activity proxy; customs/logistics data where available.

Base rates matter: outright fabrication is rare, aggressive-but-legal
presentation is common, and the analytical error most investors make is
neither detecting fraud nor missing it -- it is paying growth multiples for
low-quality growth that quietly mean-reverts.

### 9.3 The honest-analyst corollary

Detection cuts both ways: the same tools exonerate. Many scary-looking
screens fire on legitimately different business models (fast growers
legitimately run negative CFO/NI ratios while investing; heavy capex
utilities legitimately show weak FCF). The output of red-flag work is a
QUESTION LIST and a position-size constraint, rarely an instant conviction.

## 10. A practical statement-analysis workflow

Ten steps, roughly an evening per company:

1. Pull the last 3-5 annual filings plus latest quarterly; XBRL companyfacts
   if available for the series.
2. Normalize: strip one-timers per Section 5.2 list; rebuild revenue into
   segment/geography matrix (Section 6.3).
3. Reconcile the three statements' articulation; confirm cash ties.
4. Compute the quality battery: CFO/NI, accruals ratio, DSO/DIO/DPO,
   capex/D&A, SBC/revenue, buybacks vs dilution.
5. Restate leverage: net debt including leases/pensions/material
   commitments; coverage ratios at normalized EBITDA.
6. Read the notes in this order: revenue recognition, segment note,
   commitments/contingencies, related parties, critical accounting
   estimates (MD&A), subsequent events.
7. Write down the three estimates management makes that most move reported
   earnings (e.g., expected credit loss, useful lives, discount rates);
   stress each qualitatively.
8. Convert to owner earnings / normalized FCF; sanity-check against
   billings/backlog dynamics for subscription models (Section 4.3).
9. List open questions for the next call/report; assign confidence per the
   vault's calibration standards -- unresolved red flags cap confidence
   mechanically, whatever the story quality.
10. Date-stamp the analysis; schedule the recheck on the next filing.
   Statements age; conclusions without timestamps become false anchors.

## Closing summary

Accounting is the language in which management speaks to capital markets,
and fluency is asymmetric: most market participants read headlines, fewer
read the statements, almost nobody reads the notes -- the edge concentrates
exactly there. The three statements form one articulated system; cash flow
truth-tests accrual income; ASC 606 reshaped tech reporting around
obligations and deferrals; quality-of-earnings ratios expose the gap
between reported and earned; segments and off-balance-sheet commitments
carry risks the consolidated lines hide; XBRL turns vigilance into a
scalable screen; and the manipulation playbook has stable signatures for
those who look. Pair this file with [[edu-fixed-income]] for the leverage
consequences and [[edu-quantitative-methods]] for testing whether detected
patterns are statistically real or noise.

## Appendix A: Glossary of core terms

- Accruals: difference between net income and operating cash flow; measures
  how much reported earnings depends on estimates rather than cash.
- ASC 606: the revenue recognition standard built on the five-step
  transfer-of-control model; forced unbundling and deferral of bundled deals.
- ASC 842: lease accounting standard bringing operating leases on-balance.
- Billings: revenue plus change in deferred revenue; nearer-term cash proxy
  for subscription businesses.
- cRPO / RPO: current / total remaining performance obligations --
  contracted revenue not yet recognized.
- Cookie-jar reserves: excess allowances built in good periods and released
  to smooth later earnings.
- CFO / NI ratio: operating cash flow divided by net income; sustained
  readings below 1.0 flag accrual-heavy earnings.
- DSO / DIO / DPO: days sales outstanding, days inventory outstanding,
  days payables outstanding; the cash-conversion-cycle trio.
- Deferred revenue: cash collected before performance obligations are met;
  a contract liability, and for SaaS a leading indicator.
- FCF: operating cash flow minus capital expenditures; the workhorse
  valuation flow.
- FCFF / FCFE: free cash flow to the firm (before interest) versus to
  equity (after interest); match discount rate accordingly.
- Owner earnings: net income plus non-cash charges minus maintenance capex
  with SBC treated as a true cost.
- Quality of earnings: the discipline of testing whether reported profits
  reflect durable economics or presentation choices.
- SBC: stock-based compensation; non-cash but dilutive, hence a real cost.
- Segment reporting (ASC 280): disclosure by management-defined business
  units; ASU 2023-07 added significant segment expenses and CODM identity.
- Sloan accrual anomaly: finding that high-accrual firms underperform
  low-accrual firms; the defensive screen survives its alpha decay.
- VIE: variable interest entity; consolidation-dependent structure where
  exposures can hide off-balance-sheet.
- XBRL: XML-based tagging standard behind machine-readable SEC filings;
  enables point-in-time, dimension-aware fundamental data pipelines.

## Appendix B: Red-flag quick screen (one page)

Score one point each; two or more warrants a full Section 10 workflow:

1. CFO / Net Income below 0.8 in each of the last three fiscal years.
2. Accounts receivable growth exceeding revenue growth by 10+ points for
   two consecutive years.
3. Inventory growth materially outrunning COGS growth (product firms).
4. Any restructuring charge in three of the last five years.
5. Non-GAAP EPS positive while GAAP EPS negative for two straight years.
6. SBC above 15% of revenue with buybacks roughly equal to dilution.
7. Auditor or CFO change without clean explanation in the last 24 months.
8. Material weakness disclosed, or filing deadline missed, recently.
9. Purchase commitments or guarantees adding 25%+ to stated net debt if
   capitalized.
10. Custom XBRL tags used for headline revenue or margin lines.

The screen exists to ROUTE attention. It does not convict; it schedules
skepticism. Companies fail screens for honest reasons -- hypergrowth working
capital, real restructuring after real strategy shifts -- which is why step
two is always reading the actual notes, never acting on the score alone.


---

## Related vault data

Where the theory above plugs into this vault's measured layer:

- [[ref-financial-statements]] -- EDGAR XBRL statement data; the raw feed for
  the statement-linkage and red-flag screens in Sections 2 through 9.
- ref-earnings-analysis-framework -- earnings framework over the covered
  names; applies Section 10's workflow name by name each print.
- [[ref-composite-scoring]] -- quality sleeves consume the accrual and FCF
  conversion checks defined here; scoring inputs trace to statement items.
- ref-institutional-insider-tracking -- ownership and insider context;
  the behavioral cross-check when statement signals and smart money diverge.
- [[ref-alternative-data-signals]] -- non-price signals mined from filings;
  extends Section 9's manipulation heuristics with disclosed-data tells.
- Companion theory: edu-corporate-finance (what the statements should
  imply for value), [[edu-fixed-income]] (leverage channel),
  [[edu-quantitative-methods]] (statistical testing of screen hit rates).
