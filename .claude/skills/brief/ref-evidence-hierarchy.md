---
categories: [sources]
type: reference
target_path: .claude/skills/brief/ref-evidence-hierarchy.md
tags: [topic/evidence-grading, topic/analytic-tradecraft, topic/briefing]
aliases: [evidence grading, source hierarchy, analytic tradecraft, confidence calibration]
related:
  - "[[hot]]"
  - "[[ref-research-methodology]]"
  - "[[analysis-depth-standard]]"
  - "[[ref-macro-landscape]]"
  - "[[ref-monitoring-rules]]"
  - "[[doctrine.template]]"
  - "[[ref-geopolitical-framework]]"
  - "[[ref-regime-taxonomy]]"
  - "[[ref-briefing-structure]]"
status: active
created: 2026-04-23
updated: 2026-04-23
word_count: 6525
sources_count: 116
---

## Table of contents

**1.** Introduction and scope
**2.** Evidence grading scale: canonical 5-tier A / B / C / D / F
**3.** Intelligence Community analytic standards
**4.** Sherman Kent's Words of Estimative Probability and calibrated language
**5.** Forecast calibration and Brier scoring
**6.** Primary financial sources: methodology and access paths
**7.** Major wire services and Grade-B financial journalism
**8.** Aggregators and Grade-C services
**9.** Social media as signal: Grade D default, conditions for upgrade
**10.** Analyst ratings and sell-side commentary
**11.** Temporal decay and staleness grading
**12.** Cross-source triangulation
**13.** Confidence cap rules: the Phase N HALT Gate
**14.** Probability language: the briefing output contract
**15.** Paywalled vs open-source trade-offs
**16.** Adversarial information and integrity
**17.** Application to `/brief` Phases
**18.** Coordination with other skills
**19.** Pseudocode: full evidence-grading toolkit
**20.** Limitations and evolution
**21.** References

## 1. Introduction and scope

### 1.1 What this reference covers

This document is the canonical reference for evidence grading, source-trust taxonomy, calibrated probability language, confidence cap methodology, and cross-source triangulation as operationalized by the `/brief` v2 skill. It fuses two mature tradecraft traditions: United States Intelligence Community analytic standards as codified in [ODNI Intelligence Community Directive 203](https://www.dni.gov/files/documents/ICD/ICD-203.pdf) and the [CIA Tradecraft Primer on Structured Analytic Techniques](https://www.cia.gov/resources/csi/static/Tradecraft-Primer-apr09.pdf), and institutional investment research discipline as codified by the [CFA Institute Code of Ethics and Standards of Professional Conduct](https://www.cfainstitute.org/standards/professionals/code-ethics-standards) and [FINRA Rule 2241 on Research Analysts and Research Reports](https://www.finra.org/rules-guidance/rulebooks/finra-rules/2241).

The core output contract is decision-grade: every material claim in a briefing body carries an inline `[Grade A-F | source | date]` marker; frontmatter emits an integer `confidence:` on 0-100 and a `conviction:` enum drawn from {low, medium, high}; a sidecar `meta.json` records `priced_in_calls:` for retrospective Brier scoring per [Brier (1950)](https://doi.org/10.1175/1520-0493(1950)078%3C0001:VOFEIT%3E2.0.CO;2) and [Murphy (1973)](https://doi.org/10.1175/1520-0450(1973)012%3C0595:ANVPOT%3E2.0.CO;2).

### 1.2 How `/brief` v2 consumes it

Phase N (the Pre-Output HALT Gate) is the primary consumer: its 22-item checklist draws every threshold, cap rule, and probability-language validation from this document. Phase E (Regime Detection), Phase G (Cross-Asset Coherence), Phase H (Thesis Status Board), Phase K (Scenario Bar), Phase L (Intelligence Gaps vs Warning Problems), and Phase M (`FOLLOWUPS:skills`) are secondary consumers, each drawing from specific sections below.

### 1.3 Two orthogonal dimensions: source-trust scoring vs claim-grading

Source-trust and claim-grading are orthogonal. A Grade-A source can carry a weak claim (an analyst's editorial assertion in a 10-K Management Discussion section does not inherit the filing's evidentiary status); a Grade-D channel can surface a primary artifact (a Reddit user posting a screenshot of an [SEC Form 8-K](https://www.investor.gov/introduction-investing/investing-basics/glossary/form-8-k) is Grade D until the artifact is verified directly against [EDGAR](https://www.sec.gov/edgar)). The `/brief` tradecraft treats these as independent axes and always grades the underlying claim.

### 1.4 What is explicitly out of scope

Security classification, compartmentation, and handling caveats (the IC's TS/SCI stack) are out of scope; all sources consumed by `/brief` are open-source. Model-risk governance for quantitative models (SR 11-7 territory) is out of scope. Legal privilege, MNPI handling, and Reg FD compliance for the user's own communications are out of scope; this document governs inbound claim grading, not outbound disclosure.

## 2. Evidence grading scale: canonical 5-tier A / B / C / D / F

### 2.1 Grade A: primary source

A source is Grade A when it is the issuing authority for the claim. Grade-A artifacts include SEC filings retrieved via [EDGAR full-text search](https://www.sec.gov/edgar/search/) ([10-K](https://www.investor.gov/introduction-investing/investing-basics/glossary/form-10-k), [10-Q](https://www.investor.gov/introduction-investing/investing-basics/glossary/form-10-q), [8-K](https://www.investor.gov/introduction-investing/investing-basics/glossary/form-8-k), [13F](https://www.investor.gov/introduction-investing/investing-basics/glossary/form-13f-reports-filed-institutional-investment), Form 4 insider transactions per the [SEC Insider Transactions Data Sets](https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets), [S-1](https://www.sec.gov/resources-small-businesses/going-public/what-registration-statement) registration statements); [FOMC statements and minutes on federalreserve.gov](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm); the [Federal Reserve Summary of Economic Projections](https://www.federalreserve.gov/monetarypolicy/guide-to-the-summary-of-economic-projections.htm); the [Beige Book](https://www.federalreserve.gov/monetarypolicy/publications/beige-book-default.htm); the [Senior Loan Officer Opinion Survey](https://www.federalreserve.gov/data/sloos.htm); [BLS releases](https://www.bls.gov/news.release/empsit.toc.htm) and [CPI reports](https://www.bls.gov/news.release/cpi.htm); [BEA GDP releases](https://www.bea.gov/data/gdp/gross-domestic-product); [US Treasury daily yield-curve rates](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve); exchange-published methodology such as the [Cboe VIX white paper](https://cdn.cboe.com/api/global/us_indices/governance/Volatility_Index_Methodology_Cboe_Volatility_Index.pdf); [BIS working papers](https://www.bis.org/list/wppdfs/index.htm); [ECB working papers](https://www.ecb.europa.eu/press/research-publications/working-papers/html/index.en.html); and multilateral releases such as the [IMF World Economic Outlook](https://www.imf.org/en/publications/weo) and [Global Financial Stability Report](https://www.imf.org/en/publications/gfsr). Audited financial statements are Grade A; unaudited management KPIs disclosed in the same filing are Grade A but inherit the lower evidentiary status of management assertion.

### 2.2 Grade B: major wire service or authoritative secondary source

A source is Grade B when it is a wire service or newspaper with published editorial standards, attributed sourcing, and a correction process. Grade-B outlets include Reuters (governed by the [Thomson Reuters Trust Principles](https://www.thomsonreuters.com/en/about-us/trust-principles.html) and the [Reuters Handbook of Journalism](https://www.handbookreuters.com/)), the Associated Press (governed by [AP News Values and Principles](https://www.ap.org/about/news-values-and-principles/)), Bloomberg News (operating under standards codified in "The Bloomberg Way" and the [Bloomberg Live Editorial Guidelines](https://assets.bbhub.io/media/sites/9/2020/10/Bloomberg-Live-Editorial-Guidelines_Aug-2020_MASTER-1.pdf)), the Wall Street Journal news desk (governed by the Dow Jones Code of Conduct, see [WSJ News Literacy](https://newsliteracy.wsj.com/)), the [Financial Times Editorial Code of Practice](https://s3.eu-west-1.amazonaws.com/tnw.uploads/uploads/FT-EDITORIAL-CODE-OF-PRACTICE-15-Jan-2024.pdf), [New York Times Standards and Ethics](https://www.nytco.com/company/standards-ethics/), and [Nikkei Asia](https://asia.nikkei.com/about).

### 2.3 Grade C: aggregator or curated secondary service

A source is Grade C when it republishes, summarizes, or scrapes primary and Grade-B content without adding primary reporting. Grade-C services include Yahoo Finance, stockanalysis.com, finviz, Koyfin, the Motley Fool news desk, and the Seeking Alpha news desk. Grade-C channels carry an aggregator-of-aggregators risk: when Grade C cites Grade C, the effective evidentiary grade is lower than either link suggests.

### 2.4 Grade D: social media or unverified

A source is Grade D by default when posted to Twitter/X, Reddit, StockTwits, Telegram, Discord, 4chan /biz/, or equivalent user-generated channels. Grade D is the starting grade even for named practitioners with long track records; upgrade requires triangulation against a Grade-A or Grade-B artifact (Section 12).

### 2.5 Grade F: stale

A source is Grade F when the date of information exceeds the decay threshold for the claim class. For market-linked claims (prices, spreads, implied volatilities, analyst estimates, flow data), the Grade-F threshold is 7 calendar days. For structural and secular claims (industrial policy, technology-adoption curves, regulatory frameworks), the half-life is longer and is set per claim family in Section 11. The staleness mechanism is justified by [Da, Engelberg, and Gao (2011)](https://doi.org/10.1111/j.1540-6261.2011.01679.x) on attention-driven news incorporation, which documented rapid decay of information advantage once news enters widely read channels.

### 2.6 Why 5 tiers rather than 3 or 7

Three tiers (Good/OK/Bad) collapse the critical distinction between primary-source artifacts and wire-service reporting of those artifacts, and obscure the even more consequential distinction between aggregator repackaging and user-generated claims. Seven tiers introduce false precision: calibration literature from [Lichtenstein, Fischhoff, and Phillips (1982)](https://doi.org/10.1017/CBO9780511809477.023) demonstrated that graders achieve reliable inter-rater agreement at roughly five distinguishable levels; finer partitions degrade reliability without improving discrimination. The five-tier scale matches the five-point confidence scale of [ICD 203](https://www.dni.gov/files/documents/ICD/ICD-203.pdf) Analytic Tradecraft and is compatible with the Mastrandrea et al. uncertainty framework (Section 4.6).

| Grade | Rule | Canonical example | Allowed upgrade path |
|-------|------|-------------------|----------------------|
| A | Issuing authority; primary artifact | 10-K filed via EDGAR; FOMC statement PDF | None needed |
| B | Wire service or editorial-standard news desk | Reuters, AP, Bloomberg News, FT, WSJ news desk | Cite underlying Grade-A artifact to upgrade |
| C | Aggregator, summarizer, or curator | Yahoo Finance, finviz, Seeking Alpha news desk | Locate Grade-A or Grade-B upstream; upgrade to that grade |
| D | Social media, user-generated, unverified | Twitter/X, Reddit, StockTwits, Discord | Triangulate vs Grade-A or two independent Grade-B; cap upgrade at C absent primary artifact |
| F | Stale; beyond decay threshold | Quoted spread from 11 days ago for liquid equity | Refresh; not upgradable while stale |

## 3. Intelligence Community analytic standards

### 3.1 ICD 203 Analytic Standards: five analytic standards

The five Analytic Standards, as codified in [ICD 203](https://www.dni.gov/files/documents/ICD/ICD-203.pdf), are objectivity, independence of political consideration, timeliness, basis on all available sources of intelligence, and implementation of analytic tradecraft standards. Objectivity governs the analyst's duty to avoid outcome-conforming reasoning and is mirrored in the [CFA Institute Code of Ethics](https://www.cfainstitute.org/standards/professionals/code-ethics-standards) duty to use reasonable care and exercise independent professional judgment.

### 3.2 Tradecraft standards (nine attributes)

The nine tradecraft attributes are: properly describes quality and credibility of underlying sources; properly expresses and explains uncertainties; properly distinguishes between underlying intelligence and analyst assumptions and judgments; incorporates analysis of alternatives; demonstrates customer relevance and addresses implications; uses clear and logical argumentation; explains change to or consistency of analytic judgments; makes accurate judgments and assessments; and incorporates effective visual information where appropriate. Sourcing discipline is further codified in [ICD 206 on Sourcing Requirements for Disseminated Analytic Products](https://www.dni.gov/files/documents/ICD/ICD-206.pdf), and presentation standards in [ICD 208 on Maximizing the Utility of Analytic Products](https://www.dni.gov/files/documents/ICD/ICD-208-Maximizing-the-Utility-of-Analytic-Products-2017-01-09.pdf).

### 3.3 Psychology of Intelligence Analysis: cognitive biases relevant to financial research

[Heuer's Psychology of Intelligence Analysis](https://www.cia.gov/resources/csi/books-monographs/psychology-of-intelligence-analysis-2/) catalogues biases with direct analogs in portfolio management: anchoring, confirmation bias, evidence-source vividness, availability, absence-of-evidence reasoning, and mirror-imaging. The structural insight -- that analytic errors arise more from cognitive process than from information shortage -- transfers cleanly to the "more data, worse decisions" pattern studied in experimental finance.

### 3.4 Structured Analytic Techniques

The CIA [Tradecraft Primer](https://www.cia.gov/resources/csi/static/Tradecraft-Primer-apr09.pdf) codifies Key Assumptions Check, Analysis of Competing Hypotheses (ACH, developed in [Heuer's Psychology of Intelligence Analysis Chapter 8](https://www.cia.gov/resources/csi/static/Pyschology-of-Intelligence-Analysis.pdf)), Red Cell analysis, Team A / Team B, Pre-Mortem analysis, Devil's Advocacy, What-If analysis, and High-Impact/Low-Probability (HIPL) analysis. [Heuer and Pherson's Structured Analytic Techniques for Intelligence Analysis, 3rd edition](https://collegepublishing.sagepub.com/products/structured-analytic-techniques-for-intelligence-analysis-3-255432) catalogues 66 techniques and is the tradecraft reference.

### 3.5 Mapping to `/brief` v2

Key Assumptions Check is required in Phase H for every thesis-status entry. ACH is the default technique in Phase E when regime-detection candidates are non-overlapping. Red Cell and Pre-Mortem are mandatory companion techniques in Phase K scenario construction; the Pre-Output HALT Gate in Phase N checks that the scenario bar contains at least one genuinely adversarial alternative. HIPL is the required frame for the Phase L Intelligence Gaps / Warning Problems section. The analytic ombudsman role described in [ODNI objectivity materials](https://www.dni.gov/index.php/how-we-work/objectivity) is approximated by the `/challenge` skill (Tier 3 upgrade pending; Section 18.3).

## 4. Sherman Kent's Words of Estimative Probability and calibrated language

### 4.1 Historical origin

Kent's 1964 essay [Words of Estimative Probability](https://www.cia.gov/resources/csi/studies-in-intelligence/archives/vol-8-no-4/words-of-estimative-probability/) drew its urgency from the 1951 controversy over [NIE 29-51 on the Probability of an Invasion of Yugoslavia in 1951](https://www.cia.gov/readingroom/document/cia-rdp98-00979r000100270001-1), in which the estimate asserted a "serious possibility" of Soviet attack; subsequent polling of the drafting officers revealed their private probability assessments ranged from 20 percent to 80 percent. Kent's remedy was explicit verbal-numeric mapping.

### 4.2 The canonical yardstick and mapped percentage ranges

Kent's yardstick, preserved in the [Steury-edited collected essays on Sherman Kent and the Board of National Estimates](https://www.cia.gov/resources/csi/books-monographs/sherman-kent-and-the-board-of-national-estimates-collected-essays-2/), established the following mapping (claim (Kent yardstick -> percentage range), per Kent 1964):

| Kent term | Percentage band |
|-----------|-----------------|
| Certain | 100 |
| Almost certain | 93 (give or take 6) |
| Probable | 75 (give or take 12) |
| Chances about even | 50 (give or take 10) |
| Probably not | 30 (give or take 10) |
| Almost certainly not | 7 (give or take 5) |
| Impossible | 0 |

### 4.3 IC Estimative Probability Yardstick (post-2007 standardization)

Post-2007, the IC adopted a seven-band yardstick codified in [ICD 203](https://www.dni.gov/files/documents/ICD/ICD-203.pdf) Appendix: remote (1-5%), very unlikely (5-20%), unlikely (20-45%), roughly even chance (45-55%), likely (55-80%), very likely (80-95%), almost certain(ly) (95-99%). The post-2007 yardstick is the default used by `/brief` body prose.

### 4.4 Why HIGH / MEDIUM / LOW collapses information

A three-tier confidence scale is information-destroying. [Tetlock's Expert Political Judgment](https://press.princeton.edu/books/hardcover/9780691178288/expert-political-judgment) documented that forecasters who express probabilities on finer grids achieve materially better Brier scores. Mauboussin's research at [Morgan Stanley Counterpoint Global](https://www.morganstanley.com/im/en-us/financial-advisor/insights/series/consilient-observer.html) reaches the same conclusion in an investment-process context: coarse-granularity language collapses distinct epistemic states into operationally identical text.

### 4.5 Mapping to `/brief` frontmatter

`/brief` emits two companion fields. `confidence:` is an integer on 0-100 expressing the analyst's calibrated probability that the briefing's key judgment is correct. `conviction:` is a three-enum action signal (low, medium, high) keyed to position sizing rather than truth probability. Conviction medium with confidence 55 expresses a plausible but poorly sized bet; conviction high with confidence 55 is prohibited by the Pre-Output HALT Gate.

### 4.6 IPCC AR6 uncertainty language as parallel standard

The [Mastrandrea et al. IPCC Guidance Note](https://www.ipcc.ch/site/assets/uploads/2018/05/uncertainty-guidance-note.pdf), operationalized in [IPCC AR6 Working Group I](https://www.ipcc.ch/report/ar6/wg1/chapter/technical-summary/), defines parallel likelihood bands (virtually certain >= 99%, very likely >= 90%, likely >= 66%, more likely than not > 50%, about as likely as not 33-66%, unlikely <= 33%, very unlikely <= 10%, exceptionally unlikely <= 1%) and a confidence scale (very low, low, medium, high, very high). The IPCC companion article is [Mastrandrea et al. (2011)](https://doi.org/10.1007/s10584-011-0178-6). Where a claim has an IPCC analogue (climate-policy, long-horizon macro), the IPCC phrasing is preferred in body prose.

## 5. Forecast calibration and Brier scoring

### 5.1 Brier (1950) quadratic probability score

The Brier score is the mean squared error between a forecast probability vector and a one-hot outcome vector (per [Brier 1950](https://doi.org/10.1175/1520-0493(1950)078%3C0001:VOFEIT%3E2.0.CO;2)). For binary events with forecast p and outcome o in {0,1}, BS = (p - o)^2, bounded on [0,1] with lower scores better. Brier is strictly proper: it is uniquely minimized in expectation by reporting one's true belief.

### 5.2 Alternative scoring rules

The log (ignorance) score from [Roulston and Smith (2002)](https://doi.org/10.1175/1520-0493(2002)130%3C1653:EPFUIT%3E2.0.CO;2) is -log(p_o), penalizing high-confidence errors more aggressively than Brier. The Ranked Probability Score from [Epstein (1969)](https://doi.org/10.1175/1520-0450(1969)008%3C0985:ASSFPF%3E2.0.CO;2) generalizes Brier to ordered categories. [Gneiting and Raftery (2007)](https://doi.org/10.1198/016214506000001437) survey the family of strictly proper scoring rules and the theoretical conditions under which each dominates.

### 5.3 Lichtenstein-Fischhoff-Phillips calibration framework

The foundational calibration literature (see [Lichtenstein, Fischhoff, and Phillips 1982](https://doi.org/10.1017/CBO9780511809477.023) and its [1977 DTIC technical report](https://apps.dtic.mil/sti/tr/pdf/ADA033248.pdf)) established that unaided human probability judgments systematically overestimate confidence, and that feedback-driven training measurably reduces miscalibration. The framework distinguishes reliability (do forecasted 80 percents actually occur 80 percent of the time?), resolution (do forecasts discriminate between events that happen and events that don't?), and sharpness (are forecasts pushed away from the base rate?).

### 5.4 Tetlock's Expert Political Judgment and Good Judgment Project findings

[Tetlock (2005)](https://press.princeton.edu/books/hardcover/9780691178288/expert-political-judgment) documented that subject-matter experts in geopolitics barely outperformed naive extrapolation and often underperformed dart-throwing chimps on multi-year horizons, with hedgehog-style ideological commitment inversely correlated with calibration. The [IARPA Aggregative Contingent Estimation program](https://www.iarpa.gov/research-programs/ace) funded the [Good Judgment Project](https://goodjudgment.com/), which -- per [Mellers et al. (2014) in Psychological Science](https://doi.org/10.1177/0956797614524255) -- identified a ~2% superforecaster tail with Brier scores roughly 30 percent better than the team mean. [Tetlock and Gardner's Superforecasting](https://www.penguinrandomhouse.com/books/227815/superforecasting-by-philip-e-tetlock-and-dan-gardner/) is the practitioner summary.

### 5.5 Superforecaster attributes

Superforecasters share measurable cognitive-style traits: active open-mindedness, granular probability updating, dragonfly-eye perspective-taking, comfort with dissonance, and disciplined record-keeping. The [Forecasting Research Institute](https://forecastingresearch.org/) continues this research program under Tetlock. [IARPA's Hybrid Forecasting Competition](https://www.iarpa.gov/research-programs/hfc) extended the work into human-machine pipelines.

### 5.6 Application to `/brief` meta.json sidecar

Each briefing emits a meta.json sidecar containing `priced_in_calls:`, a list of {claim_id, claim_text, forecast_probability, resolution_criteria, resolution_horizon, grade}. At resolution, `/retro` computes the call-level Brier score, updates a rolling 30-day Brier, and partitions it into Murphy components (Section 5.8). [Metaculus scoring methodology](https://www.metaculus.com/help/scores-faq/) is the external benchmark.

### 5.7 Minimum scorable-call threshold

No aggregate Brier metric is emitted until at least 5 calls have resolved. Below that threshold, sample-size noise dominates signal; [Lichtenstein-Fischhoff-Phillips](https://doi.org/10.1017/CBO9780511809477.023) calibration plots are unstable with fewer than 10 forecasts per probability bin, and [Gneiting and Raftery (2007)](https://doi.org/10.1198/016214506000001437) note that strictly proper scoring rules are consistent only in the limit.

### 5.8 Resolution vs calibration (Murphy decomposition)

[Murphy (1973)](https://doi.org/10.1175/1520-0450(1973)012%3C0595:ANVPOT%3E2.0.CO;2) decomposed the Brier score as BS = reliability - resolution + uncertainty, where uncertainty is a property of the outcome distribution and is fixed once the sample is observed. Reliability measures miscalibration (forecaster reports 80% but events occur 70%); resolution measures discrimination (the forecaster assigns different probabilities to events that happen vs don't). Two forecasters with identical BS can differ sharply in reliability and resolution; `/retro` reports both.

## 6. Primary financial sources: methodology and access paths

### 6.1 SEC EDGAR

The [SEC EDGAR system](https://www.sec.gov/edgar) is the canonical Grade-A distribution channel for corporate disclosures. [10-K annual reports](https://www.investor.gov/introduction-investing/investing-basics/glossary/form-10-k), [10-Q quarterly reports](https://www.investor.gov/introduction-investing/investing-basics/glossary/form-10-q), [8-K current reports](https://www.investor.gov/introduction-investing/investing-basics/glossary/form-8-k), [13F institutional-manager holdings reports](https://www.investor.gov/introduction-investing/investing-basics/glossary/form-13f-reports-filed-institutional-investment), Forms 3/4/5 insider transactions (covered in the [SEC bulletin on forms 3, 4, 5](https://www.sec.gov/files/forms-3-4-5.pdf)), and [Form S-1 registration statements](https://www.sec.gov/resources-small-businesses/going-public/what-registration-statement) are all retrievable via EDGAR full-text search. [Regulation FD](https://www.sec.gov/rules-regulations/2000/08/selective-disclosure-insider-trading) (17 CFR Part 243, text at the [eCFR](https://www.ecfr.gov/current/title-17/chapter-II/part-243)) governs selective-disclosure boundaries.

### 6.2 Federal Reserve

The [FOMC calendar](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm) indexes statements, minutes, press-conference transcripts, and projection materials. The [Summary of Economic Projections](https://www.federalreserve.gov/monetarypolicy/guide-to-the-summary-of-economic-projections.htm), including the dot plot, is the single most-cited central-bank artifact in macro briefings. The [Beige Book](https://www.federalreserve.gov/monetarypolicy/publications/beige-book-default.htm) provides anecdotal district-level texture; the [Senior Loan Officer Opinion Survey](https://www.federalreserve.gov/data/sloos.htm) quantifies bank lending-standard tightening and loan-demand shifts. The [H.15 Selected Interest Rates release](https://www.federalreserve.gov/releases/h15/) is the authoritative overnight record.

### 6.3 Exchanges

Exchange-published methodology is Grade A. The [Cboe Volatility Index methodology PDF](https://cdn.cboe.com/api/global/us_indices/governance/Volatility_Index_Methodology_Cboe_Volatility_Index.pdf) and its [mathematics methodology](https://cdn.cboe.com/resources/indices/Cboe_Volatility_Index_Mathematics_Methodology.pdf) define the VIX. The [NYSE Listed Company Manual](https://nyseguide.srorules.com/listed-company-manual) and the [NASDAQ Listing Rules](https://listingcenter.nasdaq.com/rulebook/nasdaq/rules) govern listing standards.

### 6.4 Company IR

Company-issued press releases, earnings-call transcripts posted to investor-relations pages, and Investor Day decks are Grade A when retrieved from the issuer's own site or filed as 8-K exhibits. Transcripts hosted by aggregators (Seeking Alpha, Yahoo Finance) are Grade C -- the OCR and speaker-attribution quality cannot be audited.

### 6.5 Government statistical releases

The [BLS Employment Situation](https://www.bls.gov/news.release/empsit.toc.htm), [BLS Consumer Price Index](https://www.bls.gov/news.release/cpi.htm), and [BEA Gross Domestic Product release](https://www.bea.gov/data/gdp/gross-domestic-product) are the canonical Grade-A US statistical artifacts. The [US Treasury daily par yield curve](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve) is the benchmark rate source.

### 6.6 Central bank research

[BIS working papers](https://www.bis.org/list/wppdfs/index.htm), the [ECB Working Paper Series](https://www.ecb.europa.eu/press/research-publications/working-papers/html/index.en.html), and equivalent BoJ / BoE series are Grade A for methodology and structural claims but carry the usual caveat that working papers are pre-peer-review; text should note the working-paper status.

### 6.7 Multilateral

The [IMF World Economic Outlook](https://www.imf.org/en/publications/weo) and the [IMF Global Financial Stability Report](https://www.imf.org/en/publications/gfsr), [World Bank Open Data](https://data.worldbank.org/), and [OECD Data](https://data.oecd.org/) are Grade A for cross-country comparisons; the [OECD Data Explorer](https://data-explorer.oecd.org) supports deep-series retrieval.

### 6.8 Grade-A preservation rules

Grade-A status is preserved only when: the retrieval URL is the issuer's own domain or a recognized regulatory portal (sec.gov, federalreserve.gov, bls.gov, bea.gov, treasury.gov, imf.org, bis.org, ecb.europa.eu, oecd.org); the retrieval date is within the claim's decay threshold (Section 11); and the cited text is drawn directly from the artifact, not paraphrased via a secondary channel. Secondary channels downgrade to Grade B at best, even when the underlying claim is Grade-A in origin.

## 7. Major wire services and Grade-B financial journalism

### 7.1 Wire-service editorial standards

The [Thomson Reuters Trust Principles](https://www.thomsonreuters.com/en/about-us/trust-principles.html) enshrine independence, integrity, and freedom from bias, operationalized through the [Reuters Handbook of Journalism](https://www.handbookreuters.com/). The [AP News Values and Principles](https://www.ap.org/about/news-values-and-principles/), codified alongside the [AP Stylebook](https://www.apstylebook.com/), govern attribution, corrections, and anonymous-source discipline. Both services maintain two-source requirements for market-moving claims and published correction trails.

### 7.2 Bloomberg News editorial standards

Bloomberg's standards are codified in "The Bloomberg Way" (Wiley, 14th edition, 2017; [publisher page](https://www.wiley.com/en-us/The+Bloomberg+Way%3A+A+Guide+for+Journalists%2C+14th+Edition-p-9781119272311)) and operationalized in the [Bloomberg Live Editorial Guidelines](https://assets.bbhub.io/media/sites/9/2020/10/Bloomberg-Live-Editorial-Guidelines_Aug-2020_MASTER-1.pdf). Bloomberg's Grade-B status applies to its News desk output; opinion columns (Bloomberg Opinion) are treated as Grade C.

### 7.3 Major newspapers with financial desks

The WSJ news desk operates under the Dow Jones Code of Conduct (see the [WSJ News Literacy standards site](https://newsliteracy.wsj.com/)); the [Financial Times Editorial Code of Practice](https://s3.eu-west-1.amazonaws.com/tnw.uploads/uploads/FT-EDITORIAL-CODE-OF-PRACTICE-15-Jan-2024.pdf) covers FT reporting; the [New York Times Standards and Ethics](https://www.nytco.com/company/standards-ethics/) covers NYT Business; and [Nikkei Asia](https://asia.nikkei.com/about) publishes per parent Nikkei Inc. editorial policy.

### 7.4 Grade-B vs Grade-A distinction

A Reuters bulletin reporting an 8-K filing is Grade B. The 8-K itself, retrieved from EDGAR, is Grade A. The `/brief` rule: when a Grade-B report asserts a claim whose primary source exists and is retrievable, cite the primary source with Grade A; cite the Grade-B report only as corroboration for interpretive gloss.

### 7.5 CNBC real-time vs research

CNBC's breaking-news wire is Grade B when reporting attributed facts. CNBC's on-air commentary and panel discussion are Grade C or below.

### 7.6 When Grade B downgrades to C

A Grade-B report degrades to C when: sourcing is anonymous and the claim is market-moving; the report is a republication of another wire (two-hop attribution); the report is opinion or analysis rather than reporting; or the correction record for the relevant desk shows repeated errors on the topic.

## 8. Aggregators and Grade-C services

### 8.1 Finance aggregators

Yahoo Finance, finviz, Koyfin, and stockanalysis.com republish exchange feeds, company filings, and wire-service text. They are Grade C because they add no primary reporting, their data provenance is opaque downstream, and their refresh cadences are variable. When the underlying datum is available from the primary source, cite the primary.

### 8.2 Aggregator-of-aggregators risk

When Grade C cites Grade C, the effective provenance is unknowable. The `/brief` rule: reject any claim whose traceable provenance is a chain of Grade-C citations without a recoverable Grade-A or Grade-B root.

### 8.3 Seeking Alpha news desk vs individual contributors

The Seeking Alpha news desk (SA News) operates editorial standards comparable to other curated news aggregators and is Grade C. Individual Seeking Alpha contributors are Grade D by default, regardless of follower counts or historical accuracy; an individual contributor's claim upgrades to C only when the contributor cites a Grade-A or Grade-B primary, in which case the primary is the citation.

### 8.4 Motley Fool news vs Fool.com opinion

The Motley Fool news desk is Grade C; Fool.com opinion columns and paid-product marketing are not cited.

### 8.5 CLAUDE.md blocked-domain list methodological rationale

The project's blocked-domain list codifies systematic exclusions. The rationale is the same for each: the domain either (a) republishes without attribution chains, (b) blends promotional and editorial content without disclosure, or (c) has a documented history of pump-and-dump amplification.

| Blocked domain class | Primary failure mode | Replacement preference |
|----------------------|----------------------|------------------------|
| Ad-driven stock-tip aggregators | Promotional blending | Primary IR page; SEC filing |
| Pre-IPO speculation blogs | Rumor republication | Form S-1; registration statement |
| Unattributed Fintwit mirrors | Provenance loss | Original author post (still Grade D) |
| Crypto-only news aggregators | Paid-placement risk | Exchange-published data; on-chain primary |
| SEO-generated "stock forecast" sites | LLM-synthesized text | Analyst note if available; decline otherwise |

## 9. Social media as signal: Grade D default, conditions for upgrade

### 9.1 Fintwit account credibility hierarchy

No Fintwit account -- regardless of follower count, credentials, or prior accuracy -- upgrades above Grade D by virtue of identity alone. Upgrade requires triangulation against a Grade-A or Grade-B artifact per Section 12. The rule is conservative by design: the [Oxford Internet Institute's Computational Propaganda Research Project](https://demtech.oii.ox.ac.uk/research/computational-propaganda/) documented the systematic manipulation of financial-adjacent Twitter conversation by coordinated inauthentic accounts, and its [Global Inventory of Organized Social Media Manipulation](https://demtech.oii.ox.ac.uk/research/posts/industrialized-disinformation/) catalogues the state-actor and commercial-operator landscape.

### 9.2 Reddit

r/wallstreetbets, r/stocks, and r/investing are aggregate-sentiment indicators at best. Individual posts are Grade D. Sentiment aggregation across the forum is treated as a distinct quantitative signal (a flow/positioning proxy), not as evidence of underlying claims.

### 9.3 StockTwits sentiment aggregation

StockTwits message volume and bullish/bearish ratios are retail-sentiment proxies. Used as positioning signals, they are quantitative inputs; used as claim sources, they are Grade D.

### 9.4 Discord and Telegram

Private Discord servers and Telegram channels are Grade D and carry elevated risk of coordinated promotion. The `/brief` rule: do not cite Discord or Telegram as evidence of a claim even when triangulated; use only as leads for Grade-A verification.

### 9.5 Triangulation upgrade rules

A Grade-D claim upgrades to Grade C when at least two independent Grade-B sources confirm the specific factual content (not the narrative framing). A Grade-D claim upgrades to Grade A when a Grade-A artifact confirms the content directly; at that point the claim cites the Grade-A artifact, not the social-media surfacing. No chain of Grade-D claims upgrades any Grade-D claim.

### 9.6 Adversarial information

Narrative laundering, pump-and-dump operations, earnings-leak disinformation, deepfake CEO comments, and computational propaganda are documented and rising. [Chesney and Citron's "Deep Fakes: A Looming Challenge for Privacy, Democracy, and National Security"](https://doi.org/10.15779/Z38RV0D15J) anticipated the deepfake-of-CEO risk now materializing; [Brundage et al.'s "Malicious Use of Artificial Intelligence"](https://arxiv.org/abs/1802.07228) catalogued the broader threat model. [Wardle and Derakhshan's "Information Disorder" for the Council of Europe](https://rm.coe.int/information-disorder-report-version-august-2018/16808c9c77) defines the mis/dis/mal-information taxonomy. [RAND's "Truth Decay"](https://www.rand.org/pubs/research_reports/RR2314.html) frames the macro environment.

### 9.7 SEC influencer enforcement cases

The [SEC v. Kim Kardashian administrative order](https://www.sec.gov/files/litigation/admin/2022/33-11116.pdf) (Release No. 33-11116, October 2022, $1.26M settlement for undisclosed EthereumMax touting; see also the [SEC press release](https://www.sec.gov/newsroom/press-releases/2022-183)) and the [SEC press release on charges against John McAfee](https://www.sec.gov/newsroom/press-releases/2020-246) for undisclosed ICO touting are the canonical modern influencer cases. The [SEC Investor Alert on Celebrity Endorsements](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/investor-22) and the [SEC Investor Alert on Social Media and Investment Fraud](https://www.sec.gov/resources-for-investors/investor-alerts-bulletins/social-media-investment-fraud-investor-alert) are the guidance framework.

## 10. Analyst ratings and sell-side commentary

### 10.1 Sell-side buy/hold/sell rating conventions and known distributional bias

Sell-side ratings are distributionally biased. [Michaely and Womack (1999)](https://doi.org/10.1093/rfs/12.4.653) documented the underwriter-analyst conflict of interest in recommendations for firms with whom the bank has investment-banking relationships; [Barber, Lehavy, McNichols, and Trueman (2001)](https://doi.org/10.1111/0022-1082.00336) quantified the return consequences of acting on sell-side recommendations; [Cowen, Groysberg, and Healy (2006)](https://doi.org/10.1016/j.jacceco.2005.09.001) examined optimism across firm types; [Jegadeesh and Kim (2010)](https://doi.org/10.1093/rfs/hhp093) analyzed herding.

### 10.2 I/B/E/S / Refinitiv consensus methodology

The [LSEG/Refinitiv I/B/E/S Estimates methodology](https://www.refinitiv.com/en/financial-data/company-data/ibes-estimates) aggregates analyst forecasts for earnings, revenue, cash flow, and other metrics. Consensus is Grade B when cited to I/B/E/S directly; individual analyst estimates retain their source-firm grade.

### 10.3 StarMine Analyst Rating methodology

The [LSEG StarMine Analyst Revisions Model](https://www.lseg.com/en/data-analytics/financial-data/analytics/quantitative-analytics/starmine-analyst-revisions-models) weights analysts by historical accuracy; its [Value-Momentum model](https://www.lseg.com/en/data-analytics/financial-data/analytics/quantitative-analytics/starmine-value-momentum-model) combines quantitative factors with analyst signal. StarMine-weighted consensus carries higher Grade-B confidence than equal-weighted consensus.

### 10.4 Institutional Investor All-America Research Team rankings

The [Institutional Investor All-America Research Team](https://www.institutionalinvestor.com/section/all-america-research-team), now branded Extel, ranks sell-side analysts by institutional-client vote; [the 2025 results](https://www.extelinsights.com/results/research-providers/all-america/2025) are the current benchmark. All-America team rankings are a credentialing proxy, not a track-record measure.

### 10.5 FactSet StreetAccount

[FactSet StreetAccount](https://www.factset.com/marketplace/catalog/product/streetaccount) is Grade B for real-time Street-color and attributed fact reporting.

### 10.6 Grade assignment

Sell-side research notes are Grade B when the full note is retrieved (the note's sourcing and methodology are inspectable); a Grade-C wire summary of the same note is Grade C. Consensus estimates are Grade B.

### 10.7 Independent research

Independent research providers (Bernstein, Empirical Research, Trivariate, MoffettNathanson, Melius) are Grade B and carry lower distributional-bias concern given the absence of underwriting relationships. They do not escape cognitive bias and are not Grade A.

### 10.8 Research-objectivity problem: CFA Institute ROS; FINRA Rule 2241

The [CFA Institute Standards of Practice Handbook](https://www.cfainstitute.org/sites/default/files/-/media/documents/code/code-ethics-standards/standards-practice-handbook-12th-edition.pdf) and the [CFA Institute analyst-ethics guidance](https://rpc.cfainstitute.org/policy/positions/analyst-ethics) codify the Research Objectivity Standards. [FINRA Rule 2241](https://www.finra.org/rules-guidance/rulebooks/finra-rules/2241) governs US sell-side research reports; [Regulatory Notice 15-30](https://www.finra.org/sites/default/files/notice_doc_file_ref/Regulatory-Notice-15-30.pdf) is the implementation guidance, and [FINRA Rule 2242](https://www.finra.org/rules-guidance/rulebooks/finra-rules/2242) covers debt research. Analyst compensation disclosure, firewalls between research and banking, and restrictions on pre-publication trading are the operative constraints.

## 11. Temporal decay and staleness grading

### 11.1 Market-linked claims: 7-day Grade-F threshold rationale

For market-linked claims, the Grade-F threshold is 7 calendar days. The rationale follows from attention-driven news incorporation per [Da, Engelberg, and Gao (2011)](https://doi.org/10.1111/j.1540-6261.2011.01679.x): price-relevant information is substantially incorporated within 1-5 trading days of broad attention, and 7 calendar days captures the full incorporation horizon across most asset classes while tolerating weekend boundary conditions.

### 11.2 Intraday decay for liquid equities

For liquid equities during market hours, the effective staleness threshold is tighter: quoted spreads, implied volatilities, and depth-of-book data decay on a minutes-to-hours horizon. The `/brief` rule: any market-microstructure claim older than the current session is downgraded by one grade.

### 11.3 Structural/secular claims: longer half-lives

Industrial-policy claims (CHIPS Act allocations, IRA provisions), technology-adoption curves, demographic trends, and regulatory frameworks have half-lives measured in quarters or years. The `/brief` decay rule for structural claims is 90 days without re-verification triggers a re-grade check, not automatic Grade F.

### 11.4 Academic literature

Peer-reviewed findings decay only when superseded by subsequent peer-reviewed work. Working papers (including BIS, ECB, and NBER) carry an explicit "pre-publication" caveat and are re-graded when the final peer-reviewed version appears.

### 11.5 Earnings-call specific decay

Earnings-call content decays sharply at the next earnings print. Guidance issued on a Q1 call is Grade A through the Q2 print; after the Q2 print it becomes stale for forward-looking claims (though remains Grade A as a historical artifact of management statement).

### 11.6 "Date of information" vs "date of access" distinction

Two dates matter: the date of information (when the claim was true) and the date of access (when the analyst retrieved it). Inline markers format as `[Grade A | source | YYYY-MM-DD]` where the date is the date of information. When date of information is unknown, the grade drops by one and the access date is used with a `(accessed)` suffix.

### 11.7 Stale cap-rule

When two or more material drivers in a briefing are flagged STALE, the Phase N cap rule caps `confidence:` at 65 regardless of source quality (Section 13.3).

## 12. Cross-source triangulation

### 12.1 Independent confirmation vs echo chamber

Triangulation lift requires independent sources. Two wire services both quoting the same anonymous banker are one source, not two. The test is: do the sources have distinct sourcing chains, distinct methodologies, or distinct observational positions? If not, the triangulation multiplier is 1, not 2.

### 12.2 Data-integration literature

[Doan, Halevy, and Ives, Principles of Data Integration](https://doi.org/10.1016/C2011-0-06130-6) is the canonical reference for schema-matching, entity resolution, and conflict resolution across heterogeneous sources. The authors' [companion site](https://research.cs.wisc.edu/dibook/) hosts teaching materials. The techniques translate directly to news-claim integration.

### 12.3 Big data integration and truth fusion

[Dong and Srivastava, Big Data Integration](https://doi.org/10.2200/S00578ED1V01Y201404DTM040) extends the framework to web-scale heterogeneous sources with conflicting values, introducing source-reliability estimation from observed agreement patterns.

### 12.4 Truth-discovery literature

[Yin, Han, and Yu (2008), "Truth Discovery with Multiple Conflicting Information Providers on the Web"](https://doi.org/10.1109/TKDE.2007.190745) introduced the formal truth-discovery problem. [Pasternack and Roth (2010), "Knowing What to Believe"](https://aclanthology.org/C10-1099/) added prior-knowledge integration. [Li et al. (2016), "A Survey on Truth Discovery"](https://doi.org/10.1145/2897350.2897352) (also on [arXiv](https://arxiv.org/abs/1505.02463)) catalogs the method family.

### 12.5 Triangulation lift rules

A claim's effective grade upgrades by one tier when two fully independent sources at the same base grade confirm the specific factual content and the triangulation diversity score exceeds 0.6 (Section 12.6). No triangulation upgrades a claim above Grade A. No triangulation upgrades a Grade-D claim above Grade C without a Grade-A or Grade-B confirmation.

### 12.6 Source-diversity metric

The source-diversity score is 1 - max_pairwise_cosine_similarity across source fingerprints, where fingerprints are computed over (institutional owner, physical location of production, named human author chain, quoted-primary chain). Scores above 0.6 qualify for triangulation lift; scores below indicate echo-chamber risk.

### 12.7 Pseudocode: triangulate_claim

```python
def triangulate_claim(claim, sources):
    # sources: list of {grade, org, authors, quoted_primaries}
    if len(sources) < 2:
        return claim.grade
    diversity = 1 - max_pairwise_fingerprint_similarity(sources)
    if diversity < 0.6:
        return claim.grade  # echo chamber; no lift
    base = min(s.grade for s in sources)  # weakest chain binds
    if base == 'A':
        return 'A'
    if base == 'D' and not any(s.grade in {'A', 'B'} for s in sources):
        return 'D'  # social-only triangulation does not lift past D
    return upgrade_one_tier(base)
```

## 13. Confidence cap rules: the Phase N HALT Gate

### 13.1 Cap rule 1: >30% Grade C -> cap 70

When more than 30% of material claims in the briefing body are Grade C, `confidence:` is capped at 70.

### 13.2 Cap rule 2: any Grade D -> cap 60

When any material claim is Grade D (even if triangulated to inform narrative), `confidence:` is capped at 60.

### 13.3 Cap rule 3: >2 STALE drivers -> cap 65

When more than two material drivers are STALE per Section 11, `confidence:` is capped at 65.

### 13.4 Cap rule 4: script fallback mode -> cap 60

When the briefing runs in script fallback mode (primary data pipelines offline), `confidence:` is capped at 60.

### 13.5 Multiple caps simultaneously: minimum of applicable caps

When multiple cap rules fire, the effective cap is the minimum across all applicable caps. Caps are ceiling constraints, not floors; the analyst's unconstrained `confidence:` may be lower.

### 13.6 Pseudocode: apply_confidence_cap

```python
def apply_confidence_cap(claims, runtime_flags, analyst_confidence):
    caps = []
    grade_c_share = sum(1 for c in claims if c.grade == 'C') / len(claims)
    if grade_c_share > 0.30:
        caps.append(70)
    if any(c.grade == 'D' for c in claims):
        caps.append(60)
    stale_count = sum(1 for c in claims if c.stale)
    if stale_count > 2:
        caps.append(65)
    if runtime_flags.get('script_fallback'):
        caps.append(60)
    effective_cap = min(caps) if caps else 100
    return min(analyst_confidence, effective_cap)
```

### 13.7 What caps do NOT cover

Caps do not cover: cognitive bias in claim selection (addressed by Phase H Key Assumptions Check and Phase K Pre-Mortem); base-rate neglect (addressed by `priced_in_calls` Brier-score feedback); hedgehog-mode ideological commitment per [Tetlock (2005)](https://press.princeton.edu/books/hardcover/9780691178288/expert-political-judgment) (addressed by `/challenge`); correlated errors in sell-side consensus (addressed by triangulation-diversity score).

### 13.8 HALT semantics

A HALT in Phase N is a hard stop. The briefing is not emitted with violating frontmatter; the analyst (the `/brief` invoker) is informed of the violated rule and the required remediation. HALT is not a warning; it is a blocking gate.

| Trigger | Cap | Scope |
|---------|-----|-------|
| Grade-C share > 30% | confidence <= 70 | Material claims only |
| Any Grade-D claim | confidence <= 60 | Regardless of count |
| Stale drivers > 2 | confidence <= 65 | Structural claims excluded |
| Script fallback mode | confidence <= 60 | Runtime flag |
| Conviction high + confidence < 70 | HALT | Inconsistent; reconcile |
| No alternative hypothesis in K | HALT | Tradecraft compliance |
| Priced_in_calls empty | HALT | Brier feedback continuity |

## 14. Probability language: the briefing output contract

### 14.1 Forbidden language in briefing body

Forbidden phrases (case-insensitive, scanned by `validate_probability_language`): "very high confidence" absent explicit mapping, "certainty" absent outcome, "cannot be ruled out" (absence-of-evidence construction per [Heuer](https://www.cia.gov/resources/csi/books-monographs/psychology-of-intelligence-analysis-2/)), "significant probability" (unmapped), "material risk" (unmapped), "may or may not" (non-information).

### 14.2 Required language

Body prose uses the post-2007 IC yardstick (Section 4.3) or Kent's 1964 yardstick (Section 4.2), with the mapped numeric band in parentheses on first use in each major section. Example: "Policy rates are likely (55-80%) to hold through the June meeting."

### 14.3 Kent yardstick canonical table

The Kent mapping is the reproduction of Section 4.2. Any verbal probability expression in body prose must be resolvable to exactly one row of the Kent or IC table.

### 14.4 IC Yardstick (post-2007) alternative mapping

The IC mapping is the reproduction of Section 4.3. The IC yardstick is preferred for present-tense judgments; Kent's is preserved for historical citation where original estimates used Kent's phrasing.

### 14.5 Pseudocode: validate_probability_language

```python
def validate_probability_language(text):
    forbidden = ['cannot be ruled out', 'significant probability',
                 'material risk', 'may or may not', 'possible but unlikely']
    for phrase in forbidden:
        if phrase in text.lower():
            return {'halt': True, 'reason': f'Forbidden phrase: {phrase}'}
    kent_terms = ['almost certain', 'probable', 'about even',
                  'probably not', 'almost certainly not']
    ic_terms = ['remote', 'very unlikely', 'unlikely', 'roughly even',
                'likely', 'very likely', 'almost certain']
    approved = set(kent_terms + ic_terms)
    probability_sentences = extract_probability_sentences(text)
    for s in probability_sentences:
        if not any(term in s.lower() for term in approved):
            return {'halt': True, 'reason': f'Unmapped probability: {s}'}
    return {'halt': False}
```

## 15. Paywalled vs open-source trade-offs

### 15.1 OSINT advantages

Open sources are inspectable, archivable, citable in audit, and reproducible by third parties. The [Mercyhurst Institute for Intelligence Studies](https://www.mercyhurst.edu/academics/intelligence-studies) curriculum and the IC's increasing reliance on OSINT (see the [National Intelligence Council landing](https://www.dni.gov/index.php/features/207-about/organization/national-intelligence-council) and [Global Trends 2040](https://www.dni.gov/files/ODNI/documents/assessments/GlobalTrends_2040.pdf)) reflect the rising OSINT share of tradecraft.

### 15.2 Paywalled advantages

Paywalled sources (Bloomberg Terminal, FactSet, Refinitiv, S&P Capital IQ, FT, WSJ) offer real-time, curated, machine-parseable data and proprietary analytics. The Grade-B status of their news content is preserved behind paywall, as is their editorial standard.

### 15.3 Specific paywalled sources excluded and rationale

Certain paywalled newsletters and trading services are excluded: their business model depends on information asymmetry and their publication incentives conflict with independent verification. The `/brief` rule: paywalled services are permitted when their editorial standards are publicly codified and their content is directly citable; excluded when their business model is signal resale.

### 15.4 When paywalled content is necessary

Paywalled content is necessary when: the primary is only available there (Bloomberg-wire-first events); consensus data is needed at higher refresh than free tiers provide; or machine-parseable feeds are operationally required. In those cases, the paywalled source is cited with its grade per Section 7.

### 15.5 Academic paywall navigation

Academic paywalls (Wiley, Elsevier, SAGE, OUP) are navigated via author preprints (SSRN, arXiv, institutional repositories) where available. The published DOI is always the canonical citation.

## 16. Adversarial information and integrity

### 16.1 Narrative laundering

Narrative laundering is the movement of a claim from a low-credibility origin (anonymous Fintwit, coordinated Reddit campaign) through increasingly credible channels until it appears in a Grade-B report attributed to "market chatter" or "traders said." The detection heuristic: trace the claim's earliest attributable surfacing; if it predates any Grade-A or Grade-B primary, treat as Grade D regardless of final surface.

### 16.2 Pump-and-dump operations

Pump-and-dump operations follow characteristic volume-and-sentiment signatures that are well-documented in [SEC Investor Alerts](https://www.sec.gov/resources-for-investors/investor-alerts-bulletins/social-media-investment-fraud-investor-alert). Detection: unexplained volume spikes in low-float securities coincident with concentrated social-media promotion.

### 16.3 Earnings-leak disinformation

False earnings leaks before prints are a recurring attack pattern. Rule: no pre-print earnings claim enters the briefing without Grade-A confirmation (the print itself, or an 8-K pre-announcement).

### 16.4 Deepfake and AI-generated content

[Chesney and Citron (2019), "Deep Fakes"](https://doi.org/10.15779/Z38RV0D15J) and [Brundage et al. (2018), "The Malicious Use of Artificial Intelligence"](https://arxiv.org/abs/1802.07228) established the threat model. Video/audio of executives is not Grade-A evidence absent issuer-channel distribution and cryptographic provenance where available.

### 16.5 Computational propaganda

The [Oxford Internet Institute DemTech programme](https://demtech.oii.ox.ac.uk/), [Woolley and Howard's "Computational Propaganda"](https://doi.org/10.1093/oso/9780190931407.001.0001), the [DFRLab at the Atlantic Council](https://dfrlab.org/), the [Stanford Internet Observatory](https://cyber.fsi.stanford.edu/io), and the [Harvard Kennedy School Shorenstein Center](https://shorensteincenter.org/) are the canonical research institutions. [Credibility Coalition / Meedan](https://credibilitycoalition.org/) offers operational tooling.

### 16.6 Detection heuristics

Detection heuristics: inconsistent prior posting cadence from the source account; cross-platform posting synchrony inconsistent with human behavior; image or video artifacts inconsistent with claimed provenance; economic-incentive mismatch (free promotion of a security by a non-position-holder).

## 17. Application to `/brief` Phases

### 17.1 Phase N (Pre-Output HALT Gate)

Phase N runs the 22-item checklist immediately before emission. Items include: frontmatter `confidence:` integer valid; `conviction:` enum valid; conviction/confidence coherence; Grade-C share <= 30% or cap applied; no Grade-D uncapped; stale count <= 2 or cap applied; fallback-mode flag checked; Kent/IC probability language validated; alternative hypothesis present in Phase K; priced_in_calls non-empty; meta.json sidecar valid; all citation URLs unique; all grades present on material claims; ICD 203 tradecraft-attribute self-check complete. HALT on any failure.

### 17.2 Phase E (Regime Detection)

Phase E uses ACH per [Heuer Chapter 8](https://www.cia.gov/resources/csi/static/Pyschology-of-Intelligence-Analysis.pdf) when regime-detection candidates are distinct. The chosen regime carries an explicit `regime_confidence:` Kent-mapped probability.

### 17.3 Phase G (Cross-Asset Coherence)

Phase G checks that the signals across rates, credit, equity, FX, and commodities are coherent with the regime identified in Phase E. Divergences are Grade-A primary observations requiring explicit treatment.

### 17.4 Phase H (Thesis Status Board)

Phase H applies Key Assumptions Check to every listed thesis. Assumption-invalidation triggers are documented with Grade-A counterfactual evidence.

### 17.5 Phase I (Geopolitical)

Phase I relies on Grade-A primary statements (government readouts, treaty texts, regulatory notices) and Grade-B wire confirmation; social-media geopolitical signal is Grade D absent primary corroboration.

### 17.6 Phase K (Scenario Bar)

Phase K constructs at least three scenarios (base, upside, downside) and at least one Red Cell / Devil's Advocacy scenario per the [Tradecraft Primer](https://www.cia.gov/resources/csi/static/Tradecraft-Primer-apr09.pdf). Each scenario carries a Kent-mapped probability.

### 17.7 Phase L (Intelligence Gaps vs Warning Problems)

Phase L distinguishes gaps (known unknowns of material importance) from warning problems (high-impact, low-probability events per HIPL). Each gap specifies the Grade-A source that would resolve it; each warning problem specifies the observable that would trigger its elevation.

### 17.8 Phase M (FOLLOWUPS:skills)

Phase M generates machine-actionable follow-up tasks keyed to skills (/invest, /ingest, /challenge, /decide, /retro). Follow-ups carry explicit resolution criteria and expected information sources.

## 18. Coordination with other skills

### 18.1 /invest v2 final

/invest consumes the Thesis Status Board from Phase H as input and produces position-sizing recommendations. `conviction:` flows into sizing; `confidence:` does not size directly but bounds the action space.

### 18.2 /ingest v2 final

/ingest normalizes primary artifacts (10-Ks, FOMC statements, BLS releases) into structured records consumed by /brief. Grade-A preservation depends on /ingest retaining issuer-domain URLs and retrieval timestamps.

### 18.3 /challenge (Tier 3 upgrade pending)

/challenge is the planned Red Cell / Devil's Advocacy skill, approximating the [ODNI analytic ombudsman role](https://www.dni.gov/index.php/how-we-work/objectivity). Tier 3 upgrade will implement automated alternative-hypothesis generation.

### 18.4 /decide (Tier 3 upgrade pending)

/decide is the planned decision-capture skill, recording the analyst's action in response to the brief with resolution criteria that feed `priced_in_calls`.

### 18.5 /retro v2.1

/retro resolves open `priced_in_calls`, computes call-level and rolling Brier scores, and runs the [Murphy (1973)](https://doi.org/10.1175/1520-0450(1973)012%3C0595:ANVPOT%3E2.0.CO;2) decomposition. Monthly output is a calibration plot per [Lichtenstein-Fischhoff-Phillips](https://doi.org/10.1017/CBO9780511809477.023).

## 19. Pseudocode: full evidence-grading toolkit

```python
def grade_source(source):
    """Return {'A','B','C','D','F'} for a retrieved source."""
    if source.domain in PRIMARY_DOMAINS and source.is_issuer_artifact:
        return 'A'
    if source.org in WIRE_SERVICES_WITH_EDITORIAL_STANDARDS:
        return 'B'
    if source.is_aggregator_or_curator:
        return 'C'
    if source.is_social_media_or_unverified:
        return 'D'
    return 'C'  # default conservative

def grade_claim(claim, source_grade, access_date, info_date):
    """Return grade accounting for staleness and claim-source dissonance."""
    g = source_grade
    if apply_temporal_decay(claim, info_date):
        return 'F'
    if claim.is_interpretive and g == 'A':
        g = 'B'  # management gloss inside primary doc
    return g

def apply_temporal_decay(claim, info_date):
    threshold = STALENESS_THRESHOLDS[claim.class_]  # 7d market, 90d structural
    return (TODAY - info_date).days > threshold

def triangulate_claim(claim, sources):
    if len(sources) < 2:
        return claim.grade
    diversity = 1 - max_pairwise_fingerprint_similarity(sources)
    if diversity < 0.6:
        return claim.grade
    base = min(s.grade for s in sources)
    if base in {'A'}:
        return 'A'
    if base == 'D' and not any(s.grade in {'A','B'} for s in sources):
        return 'D'
    return upgrade_one_tier(base)

def apply_confidence_cap(claims, runtime_flags, analyst_confidence):
    caps = []
    grade_c_share = sum(1 for c in claims if c.grade=='C')/len(claims)
    if grade_c_share > 0.30: caps.append(70)
    if any(c.grade=='D' for c in claims): caps.append(60)
    if sum(1 for c in claims if c.stale) > 2: caps.append(65)
    if runtime_flags.get('script_fallback'): caps.append(60)
    return min(analyst_confidence, min(caps) if caps else 100)

def brier_score(forecasts, outcomes):
    return sum((f - o)**2 for f, o in zip(forecasts, outcomes)) / len(forecasts)

def rolling_brier_30d(calls):
    resolved = [c for c in calls if c.resolved
                and (TODAY - c.resolution_date).days <= 30]
    if len(resolved) < 5:
        return None  # below scorable threshold
    return brier_score([c.forecast for c in resolved],
                       [c.outcome for c in resolved])

def validate_probability_language(text):
    forbidden = ['cannot be ruled out','significant probability',
                 'material risk','may or may not','possible but unlikely']
    for phrase in forbidden:
        if phrase in text.lower():
            return {'halt': True, 'reason': phrase}
    approved = KENT_TERMS | IC_TERMS
    for s in extract_probability_sentences(text):
        if not any(term in s.lower() for term in approved):
            return {'halt': True, 'reason': f'unmapped: {s}'}
    return {'halt': False}
```

## 20. Limitations and evolution

### 20.1 Post-2020 information-environment shifts

The post-2020 environment has accelerated narrative laundering, coordinated inauthentic behavior, and LLM-generated content. [RAND's "Truth Decay"](https://www.rand.org/pubs/research_reports/RR2314.html) and the [Oxford OII Industrialized Disinformation report](https://demtech.oii.ox.ac.uk/research/posts/industrialized-disinformation/) document the macro shift; the Grade-D default and cap rules are calibrated accordingly.

### 20.2 Earnings-leak and pre-announcement patterns

[Regulation FD](https://www.sec.gov/rules-regulations/2000/08/selective-disclosure-insider-trading) has narrowed but not eliminated selective disclosure; edge cases include 8-K timing, earnings-call follow-up color, and conference-attendance asymmetries. The `/brief` rule: pre-print earnings claims require Grade-A confirmation or are not cited.

### 20.3 SEC influencer enforcement as moving target

[SEC v. Kim Kardashian](https://www.sec.gov/files/litigation/admin/2022/33-11116.pdf), [SEC v. McAfee](https://www.sec.gov/newsroom/press-releases/2020-246), and subsequent actions define an evolving boundary. The Grade-D default for social-media influencers is conservative and does not rely on any particular enforcement posture.

### 20.4 Known limitations of Brier scoring: Murphy decomposition

[Murphy (1973)](https://doi.org/10.1175/1520-0450(1973)012%3C0595:ANVPOT%3E2.0.CO;2) established that aggregate Brier scores conceal important structure. `/retro` reports the decomposition; the single-number reader should prefer calibration over aggregate Brier for tuning.

### 20.5 Open questions

Open questions include: (a) grading for AI-generated primary-source summaries where the LLM is the producer; (b) handling LLM-synthesized multi-source reports where the underlying sources are not enumerable; (c) coordinated inauthentic behavior detection at the scale required for real-time briefing. The [Brundage et al. 2018 report](https://arxiv.org/abs/1802.07228), [Credibility Coalition](https://credibilitycoalition.org/), and [Stanford Internet Observatory](https://cyber.fsi.stanford.edu/io/publications) track the evolving landscape.

### 20.6 Quarterly review cadence

This reference is reviewed quarterly. Review inputs include: new SEC influencer enforcement actions; revisions to [ICD 203](https://www.dni.gov/files/documents/ICD/ICD-203.pdf); updates to [FINRA Rule 2241](https://www.finra.org/rules-guidance/rulebooks/finra-rules/2241); revisions to the [CFA Institute Standards of Practice Handbook](https://www.cfainstitute.org/sites/default/files/-/media/documents/code/code-ethics-standards/standards-practice-handbook-12th-edition.pdf); new peer-reviewed truth-discovery, calibration, or scoring-rule literature; and accumulated `/retro` Brier decompositions that indicate systematic calibration drift.

## 21. References

1. ODNI ICD 203, Analytic Standards. https://www.dni.gov/files/documents/ICD/ICD-203.pdf
2. ODNI ICD 206, Sourcing Requirements. https://www.dni.gov/files/documents/ICD/ICD-206.pdf
3. ODNI ICD 208, Maximizing Utility of Analytic Products. https://www.dni.gov/files/documents/ICD/ICD-208-Maximizing-the-Utility-of-Analytic-Products-2017-01-09.pdf
4. CIA, A Tradecraft Primer (2009). https://www.cia.gov/resources/csi/static/Tradecraft-Primer-apr09.pdf
5. Heuer, Psychology of Intelligence Analysis (CSI landing). https://www.cia.gov/resources/csi/books-monographs/psychology-of-intelligence-analysis-2/
6. Heuer, Psychology of Intelligence Analysis (PDF). https://www.cia.gov/resources/csi/static/Pyschology-of-Intelligence-Analysis.pdf
7. Kent, Words of Estimative Probability. https://www.cia.gov/resources/csi/studies-in-intelligence/archives/vol-8-no-4/words-of-estimative-probability/
8. NIE 29-51, Probability of Invasion of Yugoslavia. https://www.cia.gov/readingroom/document/cia-rdp98-00979r000100270001-1
9. Steury, Sherman Kent and the Board of National Estimates. https://www.cia.gov/resources/csi/books-monographs/sherman-kent-and-the-board-of-national-estimates-collected-essays-2/
10. Heuer & Pherson, Structured Analytic Techniques, 3rd ed. https://collegepublishing.sagepub.com/products/structured-analytic-techniques-for-intelligence-analysis-3-255432
11. ODNI Objectivity. https://www.dni.gov/index.php/how-we-work/objectivity
12. NIC landing. https://www.dni.gov/index.php/features/207-about/organization/national-intelligence-council
13. Global Trends 2040. https://www.dni.gov/files/ODNI/documents/assessments/GlobalTrends_2040.pdf
14. Mercyhurst IIS. https://www.mercyhurst.edu/academics/intelligence-studies
15. Brier (1950). https://doi.org/10.1175/1520-0493(1950)078%3C0001:VOFEIT%3E2.0.CO;2
16. Murphy (1973). https://doi.org/10.1175/1520-0450(1973)012%3C0595:ANVPOT%3E2.0.CO;2
17. Epstein (1969) RPS. https://doi.org/10.1175/1520-0450(1969)008%3C0985:ASSFPF%3E2.0.CO;2
18. Gneiting & Raftery (2007). https://doi.org/10.1198/016214506000001437
19. Roulston & Smith (2002). https://doi.org/10.1175/1520-0493(2002)130%3C1653:EPFUIT%3E2.0.CO;2
20. Lichtenstein, Fischhoff, Phillips (1982). https://doi.org/10.1017/CBO9780511809477.023
21. Lichtenstein et al. 1977 tech report. https://apps.dtic.mil/sti/tr/pdf/ADA033248.pdf
22. Tetlock, Expert Political Judgment. https://press.princeton.edu/books/hardcover/9780691178288/expert-political-judgment
23. Tetlock & Gardner, Superforecasting. https://www.penguinrandomhouse.com/books/227815/superforecasting-by-philip-e-tetlock-and-dan-gardner/
24. Mellers et al. (2014). https://doi.org/10.1177/0956797614524255
25. Good Judgment Inc. https://goodjudgment.com/
26. IARPA ACE program. https://www.iarpa.gov/research-programs/ace
27. IARPA HFC program. https://www.iarpa.gov/research-programs/hfc
28. Forecasting Research Institute. https://forecastingresearch.org/
29. Metaculus Scores FAQ. https://www.metaculus.com/help/scores-faq/
30. Mastrandrea et al. IPCC Guidance Note. https://www.ipcc.ch/site/assets/uploads/2018/05/uncertainty-guidance-note.pdf
31. Mastrandrea et al. 2011 companion. https://doi.org/10.1007/s10584-011-0178-6
32. IPCC AR6 WGI TS. https://www.ipcc.ch/report/ar6/wg1/chapter/technical-summary/
33. Mauboussin, Consilient Observer. https://www.morganstanley.com/im/en-us/financial-advisor/insights/series/consilient-observer.html
34. SEC EDGAR. https://www.sec.gov/edgar
35. SEC EDGAR search. https://www.sec.gov/edgar/search/
36. SEC Form 10-K glossary. https://www.investor.gov/introduction-investing/investing-basics/glossary/form-10-k
37. SEC Form 10-Q glossary. https://www.investor.gov/introduction-investing/investing-basics/glossary/form-10-q
38. SEC Form 8-K glossary. https://www.investor.gov/introduction-investing/investing-basics/glossary/form-8-k
39. SEC Form 13F glossary. https://www.investor.gov/introduction-investing/investing-basics/glossary/form-13f-reports-filed-institutional-investment
40. SEC Insider Transactions Data Sets. https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets
41. SEC Forms 3/4/5 bulletin PDF. https://www.sec.gov/files/forms-3-4-5.pdf
42. SEC Form S-1 page. https://www.sec.gov/resources-small-businesses/going-public/what-registration-statement
43. SEC Reg FD adopting release. https://www.sec.gov/rules-regulations/2000/08/selective-disclosure-insider-trading
44. 17 CFR Part 243 eCFR. https://www.ecfr.gov/current/title-17/chapter-II/part-243
45. FOMC calendars. https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
46. Federal Reserve SEP. https://www.federalreserve.gov/monetarypolicy/guide-to-the-summary-of-economic-projections.htm
47. Beige Book. https://www.federalreserve.gov/monetarypolicy/publications/beige-book-default.htm
48. SLOOS. https://www.federalreserve.gov/data/sloos.htm
49. H.15 Rates. https://www.federalreserve.gov/releases/h15/
50. BLS Employment Situation. https://www.bls.gov/news.release/empsit.toc.htm
51. BLS CPI. https://www.bls.gov/news.release/cpi.htm
52. BEA GDP. https://www.bea.gov/data/gdp/gross-domestic-product
53. Treasury Yield Curve. https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve
54. Cboe VIX Methodology. https://cdn.cboe.com/api/global/us_indices/governance/Volatility_Index_Methodology_Cboe_Volatility_Index.pdf
55. Cboe VIX Math Methodology. https://cdn.cboe.com/resources/indices/Cboe_Volatility_Index_Mathematics_Methodology.pdf
56. BIS working papers. https://www.bis.org/list/wppdfs/index.htm
57. ECB working papers. https://www.ecb.europa.eu/press/research-publications/working-papers/html/index.en.html
58. IMF WEO. https://www.imf.org/en/publications/weo
59. IMF GFSR. https://www.imf.org/en/publications/gfsr
60. World Bank Open Data. https://data.worldbank.org/
61. OECD Data. https://data.oecd.org/
62. OECD Data Explorer. https://data-explorer.oecd.org
63. NYSE Listed Company Manual. https://nyseguide.srorules.com/listed-company-manual
64. NASDAQ Listing Rules. https://listingcenter.nasdaq.com/rulebook/nasdaq/rules
65. CFA Institute Code and Standards. https://www.cfainstitute.org/standards/professionals/code-ethics-standards
66. CFA Institute Standards of Practice Handbook. https://www.cfainstitute.org/sites/default/files/-/media/documents/code/code-ethics-standards/standards-practice-handbook-12th-edition.pdf
67. CFA Institute analyst ethics. https://rpc.cfainstitute.org/policy/positions/analyst-ethics
68. FINRA Rule 2241. https://www.finra.org/rules-guidance/rulebooks/finra-rules/2241
69. FINRA Regulatory Notice 15-30. https://www.finra.org/sites/default/files/notice_doc_file_ref/Regulatory-Notice-15-30.pdf
70. FINRA Rule 2242. https://www.finra.org/rules-guidance/rulebooks/finra-rules/2242
71. SEC v. Kim Kardashian administrative order. https://www.sec.gov/files/litigation/admin/2022/33-11116.pdf
72. SEC press release on Kardashian/EthereumMax. https://www.sec.gov/newsroom/press-releases/2022-183
73. SEC press release on McAfee. https://www.sec.gov/newsroom/press-releases/2020-246
74. SEC Investor Alert on Celebrity Endorsements. https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/investor-22
75. SEC Social Media Investment Fraud Alert. https://www.sec.gov/resources-for-investors/investor-alerts-bulletins/social-media-investment-fraud-investor-alert
76. Refinitiv I/B/E/S. https://www.refinitiv.com/en/financial-data/company-data/ibes-estimates
77. LSEG StarMine ARM. https://www.lseg.com/en/data-analytics/financial-data/analytics/quantitative-analytics/starmine-analyst-revisions-models
78. LSEG StarMine Value-Momentum. https://www.lseg.com/en/data-analytics/financial-data/analytics/quantitative-analytics/starmine-value-momentum-model
79. Institutional Investor All-America Research Team. https://www.institutionalinvestor.com/section/all-america-research-team
80. Extel 2025 All-America results. https://www.extelinsights.com/results/research-providers/all-america/2025
81. FactSet StreetAccount. https://www.factset.com/marketplace/catalog/product/streetaccount
82. Thomson Reuters Trust Principles. https://www.thomsonreuters.com/en/about-us/trust-principles.html
83. Reuters Handbook of Journalism. https://www.handbookreuters.com/
84. AP News Values and Principles. https://www.ap.org/about/news-values-and-principles/
85. AP Stylebook. https://www.apstylebook.com/
86. Bloomberg Way (Wiley). https://www.wiley.com/en-us/The+Bloomberg+Way%3A+A+Guide+for+Journalists%2C+14th+Edition-p-9781119272311
87. Bloomberg Live Editorial Guidelines PDF. https://assets.bbhub.io/media/sites/9/2020/10/Bloomberg-Live-Editorial-Guidelines_Aug-2020_MASTER-1.pdf
88. WSJ News Literacy. https://newsliteracy.wsj.com/
89. FT Editorial Code 2024. https://s3.eu-west-1.amazonaws.com/tnw.uploads/uploads/FT-EDITORIAL-CODE-OF-PRACTICE-15-Jan-2024.pdf
90. NYT Standards and Ethics. https://www.nytco.com/company/standards-ethics/
91. Nikkei Asia About. https://asia.nikkei.com/about
92. Doan, Halevy, Ives, Principles of Data Integration. https://doi.org/10.1016/C2011-0-06130-6
93. Doan et al. companion site. https://research.cs.wisc.edu/dibook/
94. Dong & Srivastava, Big Data Integration. https://doi.org/10.2200/S00578ED1V01Y201404DTM040
95. Yin, Han, Yu (2008). https://doi.org/10.1109/TKDE.2007.190745
96. Pasternack & Roth (2010). https://aclanthology.org/C10-1099/
97. Li et al. (2016) Survey on Truth Discovery. https://doi.org/10.1145/2897350.2897352
98. Li et al. arXiv preprint. https://arxiv.org/abs/1505.02463
99. Da, Engelberg, Gao (2011) In Search of Attention. https://doi.org/10.1111/j.1540-6261.2011.01679.x
100. Oxford OII DemTech Computational Propaganda. https://demtech.oii.ox.ac.uk/research/computational-propaganda/
101. DemTech Industrialized Disinformation report. https://demtech.oii.ox.ac.uk/research/posts/industrialized-disinformation/
102. Woolley & Howard, Computational Propaganda (OUP DOI). https://doi.org/10.1093/oso/9780190931407.001.0001
103. RAND Truth Decay report. https://www.rand.org/pubs/research_reports/RR2314.html
104. Shorenstein Center. https://shorensteincenter.org/
105. Stanford Internet Observatory. https://cyber.fsi.stanford.edu/io
106. Stanford Internet Observatory publications. https://cyber.fsi.stanford.edu/io/publications
107. DFRLab. https://dfrlab.org/
108. Credibility Coalition. https://credibilitycoalition.org/
109. Wardle & Derakhshan, Information Disorder (CoE). https://rm.coe.int/information-disorder-report-version-august-2018/16808c9c77
110. Chesney & Citron, Deep Fakes. https://doi.org/10.15779/Z38RV0D15J
111. Brundage et al., Malicious Use of AI (arXiv). https://arxiv.org/abs/1802.07228
112. Michaely & Womack (1999) RFS. https://doi.org/10.1093/rfs/12.4.653
113. Barber, Lehavy, McNichols, Trueman (2001) JF. https://doi.org/10.1111/0022-1082.00336
114. Cowen, Groysberg, Healy (2006) JAE. https://doi.org/10.1016/j.jacceco.2005.09.001
115. Jegadeesh & Kim (2010) RFS. https://doi.org/10.1093/rfs/hhp093