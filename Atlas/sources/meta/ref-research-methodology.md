---
categories:
  - sources
type: reference
created: 2026-04-05
updated: 2026-06-11
status: active
confidence: high
tags:
  - topic/methodology
  - topic/source-evaluation
aliases: [research-methodology, methodology]
related: ["[[ref-claude-code-mastery]]"]
---

# Reference: Research Methodology Standards
Last updated: 2026-04-06
Sources: Internal methodology (no external sources needed)
Refresh cadence: As-needed (methodology is stable)
Built by: Claude Code (direct authorship)

## Purpose
Source evaluation criteria, credibility hierarchy, cross-referencing methodology, confidence assessment framework, bias detection, statistical literacy, and citation standards. Loaded by ALL skills that perform web research to ensure consistent, rigorous output quality.

## Key Takeaways
- Every major claim must be supported by 2+ independent sources (triangulation)
- Source credibility follows a 7-tier hierarchy: academic > government > industry > news > trade > corporate > user-generated
- Confidence ratings (HIGH/MEDIUM/LOW/SPECULATIVE) are mandatory on all major claims
- Recency weighting varies by domain: financial data stales in months, biomechanics in decades
- Always prefer primary sources over secondary reporting
- Check for funding bias, survivorship bias, and confirmation bias before accepting conclusions
- Correlation does not imply causation -- look for controlled studies and mechanisms
- Cite every source with enough detail that a reader could find and verify it

---

## Source Credibility Hierarchy

Use this hierarchy to prioritize sources. Higher-tier sources carry more weight in analysis. Lower-tier sources are acceptable when triangulated with others.

### Tier 1: Academic and Peer-Reviewed (Highest Credibility)
Published research in peer-reviewed journals, systematic reviews, and meta-analyses. These undergo rigorous review by domain experts before publication.
- Examples: Nature, Science, The Lancet, Journal of Finance, PNAS, JAMA
- When to use: As the gold standard for any factual claim, especially in health, science, and economics
- Limitations: Publication lag means results may be 6-12 months old. May be narrow in scope.

### Tier 2: Government and Regulatory Sources
Official data from government agencies, central banks, regulatory filings, and international organizations. These are authoritative for economic data, legal status, and policy.
- Examples: SEC filings (10-K, 10-Q, 8-K), Federal Reserve publications, BLS data, CDC, WHO, USDA, Congressional Research Service
- When to use: For economic indicators, legal/regulatory status, population-level health data, corporate financial disclosures
- Limitations: May lag real-time conditions. Government data revisions can change figures retroactively.

### Tier 3: Industry Research Reports
Professional analysis from established research firms, rating agencies, and financial data providers.
- Examples: McKinsey, Deloitte, Gartner, Bloomberg, Morningstar, S&P Global, Moody's
- When to use: For market sizing, industry trends, competitive landscapes, credit analysis
- Limitations: Often behind paywalls (summaries available). May reflect firm's consulting interests.

### Tier 4: Established News Organizations
Outlets with editorial standards, fact-checking processes, and journalistic accountability.
- Examples: Reuters, Associated Press, Wall Street Journal, Financial Times, New York Times, The Economist
- When to use: For current events, breaking developments, expert quotes, investigative reporting
- Limitations: May have political or editorial leanings. Breaking news can be revised. Headlines may not match article content.

### Tier 5: Trade Publications and Domain-Specific Outlets
Specialized media covering specific industries or domains. Credible within their domain but narrower in scope.
- Examples: TechCrunch (tech), Insurance Journal (insurance), Golf Digest (golf), Barron's (investing), Ars Technica (tech)
- When to use: For industry-specific trends, product reviews, domain expert opinions
- Limitations: May have advertising relationships. Review objectivity varies.

### Tier 6: Corporate Communications
Earnings calls, press releases, investor presentations, corporate blogs, and company-authored white papers. Useful but inherently self-serving.
- Examples: Company IR pages, quarterly earnings transcripts, product announcements
- When to use: For company-specific financials (cross-reference with SEC filings), product roadmaps, management commentary
- Limitations: Always positively biased. Forward-looking statements are aspirational. Cherry-picked metrics are common.

### Tier 7: User-Generated Content (Lowest Credibility)
Blogs, forums, social media, Reddit, YouTube, podcasts, and other unvetted content. Useful for sentiment and anecdotal data only.
- Examples: Reddit r/investing, Twitter/X financial accounts, personal blogs, YouTube channels
- When to use: For retail sentiment, emerging narratives, anecdotal data points that may be followed up with primary sources
- Limitations: No fact-checking. Survivorship bias rampant. Financial influencers may have undisclosed positions. Misinformation risk is highest here.

---

## Cross-Referencing Methodology

### Triangulation Rule
Every major claim in a research output should be supported by at least 2 independent sources. For high-stakes claims (investment theses, health recommendations), aim for 3+ sources.

### Claim Verification Workflow
1. Find claim in Source A
2. Search specifically for confirmation or contradiction in Sources B and C
3. If confirmed by 2+ independent sources: report as supported
4. If contradicted: report both positions, identify which source is more authoritative and more recent
5. If only found in a single source: flag as "single-source claim" and note the source tier

### Handling Contradictions
When sources disagree:
- Check source tiers -- higher-tier source gets more weight
- Check recency -- more recent data wins for time-sensitive claims
- Check methodology -- study with larger sample size or more rigorous design wins
- Report BOTH positions in the output with sources cited
- State which position the evidence favors and why

### Primary vs Secondary Sources
Always prefer the original source over someone reporting on it. If a news article cites a study, find and read the original study. The reporter may have misinterpreted the results, omitted caveats, or sensationalized findings.

---

## Recency Weighting

How aggressively to weight newer sources depends on the domain:

| Domain | Data Staleness Threshold | Concept Stability |
|--------|------------------------|-------------------|
| Financial markets (prices, valuations) | 1-3 months | Low -- changes constantly |
| Financial fundamentals (revenue, margins) | 3-12 months | Medium -- quarterly updates |
| Technology products and services | 6-12 months | Low -- rapid change |
| Technology architecture and concepts | 2-3 years | Medium -- evolves |
| Science and health (established) | 2-5 years | High -- stable foundations |
| Science and health (emerging) | 6-12 months | Low -- active research frontier |
| Legal and regulatory | Check effective dates | Medium -- changes with legislation |
| Career and labor market (salary data) | 6-12 months | Medium |
| Career and labor market (job demand) | 3-6 months | Low -- responsive to economy |
| Golf technique fundamentals | 5-10 years | High -- biomechanics are stable |
| Golf equipment reviews | 12-18 months | Medium -- new models annually |
| Supplement science | 1-3 years | Medium -- steady research output |

**Rule:** Always note the date of the source data, not just the publication date. A 2026 article may cite 2023 data.

---

## Confidence Assessment Framework

Every major claim in a research output should carry a confidence rating. Use these criteria:

### HIGH Confidence
- 3+ agreeing primary or secondary sources from Tier 1-4
- No credible contradictions found
- Data is recent relative to domain staleness threshold
- Well-established domain with mature evidence base
- Use when: Reporting well-supported factual claims

### MEDIUM Confidence
- 2 sources agreeing, or 1 strong primary source (Tier 1-2)
- Minor contradictions exist but the weight of evidence favors the claim
- Some recency concerns but not critical
- Emerging domain or evolving consensus
- Use when: The claim is likely correct but not ironclad

### LOW Confidence
- Single non-primary source
- Significant contradictions across sources
- Stale data beyond domain threshold
- Emerging or contested domain with active debate
- Use when: The information is the best available but uncertain

### SPECULATIVE
- Insufficient sources to assess
- Based on extrapolation, analogy, or expert opinion without data backing
- Included for completeness but flagged as unverified
- Use when: Noting possibilities or forecasts that cannot be substantiated

---

## Bias Detection Checklist

Before accepting conclusions from any source, check for these common biases:

| Bias | Question to Ask | Red Flag |
|------|----------------|----------|
| Funding bias | Who paid for this research or report? | Company-funded study finds company's product is superior |
| Selection bias | Is the sample representative? | Study only includes successful cases |
| Survivorship bias | Are we only seeing winners? | "These 10 stocks returned 500%" ignores the 100 that went to zero |
| Confirmation bias | Am I only finding sources that agree with my thesis? | All 5 sources support the bull case but you did not search for bear arguments |
| Recency bias | Am I overweighting the latest data point? | One bad quarter does not invalidate a 10-year trend |
| Authority bias | Am I accepting this because of who said it? | Famous investor says X, but the data shows Y |
| Anchoring | Am I fixated on the first number I found? | The first price target I saw was $150, so all others seem high or low relative to that |

**Mitigation:** For investment research, explicitly search for the opposing thesis. For health research, look for contradictory studies. For career research, check multiple salary data sources.

---

## Statistical Literacy Reminders

Quick-reference rules for evaluating quantitative claims:

- **Correlation is not causation:** Two trends moving together does not mean one causes the other. Look for randomized controlled trials, natural experiments, or plausible causal mechanisms.
- **Check sample sizes:** Results from n < 30 are suspect for most generalizations. Larger samples produce more reliable estimates.
- **Base rates matter:** A "200% increase" from 1 to 3 is meaningless. Always check the absolute numbers behind percentages.
- **Averages hide distributions:** A market with average P/E of 20 might have half of stocks at 10 and half at 30. Look for medians and distributions when available.
- **Beware false precision:** A forecast of "4.37% GDP growth" implies a level of certainty that does not exist. Round appropriately.
- **P-values are thresholds, not truth:** p < 0.05 is the conventional significance threshold, but check for p-hacking (running many tests until one passes) and multiple comparisons.
- **Compounding matters:** A 50% loss requires a 100% gain to recover. A 20% annual return doubles in 3.6 years. Think in compound terms for any multi-year projection.

---

## Citation Standards

How to cite sources in knowledge base documents and research outputs:

### Source List Format
At the end of every research document, include a numbered sources section:
```
## Sources
[1] Organization, "Article Title," Publication, Date. URL
[2] Author Name, "Paper Title," Journal, Volume, Date. DOI or URL
```

### In-Text References
- Direct attribution: "According to [3], revenue grew 15% year-over-year"
- Supporting citation: "Revenue grew 15% YoY (Source: [3])"
- Multiple sources: "Multiple analyses agree on the 15-20% growth range ([3], [7], [12])"

### Rules
- Every specific data point must cite its source -- never write "research shows" without a reference
- When paraphrasing, cite the source but do not use quotation marks
- Distinguish between data from the original source and analysis or interpretation
- For financial data: specify the time period (TTM, FY2025, Q1 2026) and whether adjusted or GAAP
- For scientific claims: note whether the finding is from a single study or a meta-analysis

---

## Update Triggers
This methodology document is stable. Refresh only when:
- New source types emerge that need to be classified in the hierarchy
- New bias patterns are identified
- Citation standards need updating for new output formats
- Experience reveals gaps in the current framework

## Related
[[knowledge-moc]] | [[analysis-depth-standard]]
