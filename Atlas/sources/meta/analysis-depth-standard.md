---
categories:
  - sources
type: reference
created: 2026-04-05
updated: 2026-04-23
status: active
tags:
  - topic/analysis-standard
  - topic/methodology
aliases: ["depth standard", "analytical spine"]
related: ["[[ref-research-methodology]]"]
---

# Analysis Depth Standard
Last updated: 2026-04-09
Applies to: all market, portfolio, company, ETF, crypto, sector, macro, and thesis-linked analysis in Project Osanwe
Primary readers: `SOUL.md`, `TOOLS.md`, `AGENTS.md`, OpenClaw investing skills

## Purpose
This is the authoritative depth contract for all investing and market analysis. It keeps responses current-data-first, portfolio-specific, thesis-aware, macro-aware, and decision-oriented without bloating the bootstrap files.

Portfolio-level responses such as `/performance` use the same spine with portfolio wording: current mark/freshness, recent drivers or catalysts, macro impact, exact holdings or period impact, portfolio thesis posture, and action.

## A. Core Analytical Spine
When the task is market-linked, every analytical response must include these six elements in this order. Short forms may compress wording, but they may not skip the spine.

1. Live price or latest quoted value
   - Include the freshest confirmed quote, mark, or valuation available.
   - State freshness directly: "as of 2026-04-09 3:42 PM ET" or "latest confirmed close: 2026-04-08".

2. Recent news or catalysts
   - Include the most relevant fresh developments with exact dates.
   - If nothing material is fresh, say that directly.

3. Macro or regime connection
   - Explain what the current market regime, rates, inflation, regulation, liquidity, or sector rotation means here.
   - If macro is weakly relevant, say "Macro link: limited."

4. Exact portfolio impact
   - If held, read `<VAULT_ROOT>/private/holdings-taxable.md` and `<VAULT_ROOT>/private/holdings-ira.md`.
   - Report exact share count or token amount across accounts.
   - Report current position value, dollar impact of the move, and overlap or concentration note when practical.
   - If not held, say "Not currently held."

5. Thesis status
   - Use exactly one: `CONFIRM`, `CHALLENGE`, `NEUTRAL`.
   - Tie the label to evidence, not tone.

6. Action recommendation with conviction
   - End with a base-case action view.
   - Use exactly one conviction label: `HIGH`, `MEDIUM`, `LOW`.
   - Action should be concrete: add, hold, trim, exit, wait, watchlist, starter zone, or avoid.

### Confidence Level Definitions
- **HIGH CONFIDENCE:** Multiple independent, high-quality sources confirm. Data is concrete, recent, and verifiable.
- **MEDIUM CONFIDENCE:** Evidence supports but has gaps. Single-source, or data is 1-4 weeks old. Reasonable inference from strong priors but not directly confirmed.
- **LOW CONFIDENCE:** Analytically grounded speculation. Early signals, unconfirmed reports, extrapolation from limited data, or novel situation without historical precedent. Flag explicitly as speculative.

Always state the basis for the confidence level: "MEDIUM CONFIDENCE based on Reuters reporting and prior FOMC communication patterns" -- not just "MEDIUM CONFIDENCE."

Calibration test: if asked to defend the confidence level, you should be able to name the specific sources or evidence in one sentence. If you can't, the level is too high.

## B. Decision-Grade Workflow
For analytical work, use this workflow after gathering evidence:
1. Lead with what is new and decision-relevant.
2. Map the new evidence against Osanwe's prior view if one exists.
3. Separate base case from upside and downside instead of blurring them together.
4. State what the market may be missing only when there is credible evidence for a variant view.
5. Translate the result into a portfolio decision, not just an opinion.

## C. Mandatory Depth Modules
These modules are required whenever the task is analytical. In short form they can be compressed to one line each.

### Change Detection
- State what changed since prior Osanwe understanding, prior report, prior briefing, or last relevant research.
- If there is no prior internal view, say that explicitly.

### Variant View
- State what the market may be underweighting, overpricing, or missing.
- If no credible variant view exists, say so directly instead of inventing one.

### Three-Case Frame
- Base case
- Bull case
- Bear case or failure mode
- Use probabilities or confidence bands only when they are supportable by evidence. No fake precision.

### Catalyst Map
- Next decision window
- Next hard catalyst
- What would upgrade conviction
- What would downgrade conviction
- What would fully invalidate the view

### Evidence Quality
- Best confirming evidence
- Strongest contradictory evidence
- Known unknowns that materially matter
- Freshness quality note when the data picture is thin or partially stale

### Key Numbers
- Include a short "numbers that matter" block using asset-appropriate numbers only.
- Do not dump random metrics. Every number should sharpen the decision.

Equities:
- price
- market cap
- revenue growth
- margin or profitability marker
- EPS, guidance, or next earnings date when available
- one valuation proxy that matters

ETFs:
- price
- expense ratio
- top-holdings concentration
- sector exposure
- overlap relevance
- benchmark comparison

Crypto:
- price
- market cap
- supply, unlock, regulatory, network, or liquidity catalyst as applicable

Portfolio-level:
- current value or mark
- biggest driver
- concentration note
- available performance math
- history sufficiency

### Portfolio Decision Layer
If held:
- exact current exposure
- dollar impact of the move or event
- concentration or overlap note when relevant
- whether to add, hold, trim, exit, or wait

If not held:
- explicitly say "Not currently held"
- state whether it belongs on the watchlist, in a starter-position zone, or on the avoid list

### Time-Horizon Split
Where relevant, separate:
- immediate / 24h
- next catalyst window
- medium term / 3-6 months
- longer term / 12 months

### Decision Density Rule
- Longer is not inherently better.
- Every required section must change a decision, sharpen uncertainty, or reduce a blind spot.
- Remove repetitive, decorative, or generic sections even in deep form.

## D. Freshness Rules
- No market or company analytical answer without current data unless current data is unavailable after a real attempt.
- Price freshness target: within the last 2 hours when possible.
- If intraday confirmation is not available, use the latest close and explicitly label it as close or after-hours.
- Recent news target: last 24 hours for ticker or company analysis unless nothing material happened.
- Use exact dates, not vague relative phrasing like "today" or "recently" without a date.
- If freshness is uncertain, search again before concluding.
- If the answer depends on a stale number, label it as stale.

## E. Search And Source Rules
- Minimum 3 fresh web searches (via your configured search tool) for any analytical response.
- `/invest`, `/invest-max`, `/thesis`, `/briefing` on major movers, and thesis-critical market-linked `/research` should usually use 5 to 8 targeted searches.
- Read relevant reference docs before web search so search effort focuses on what changed.
- Prefer short, specific query strings.
- Use multiple query angles, not duplicate searches.
- Prefer the existing preferred-source pattern and respect blocked-domain rules.
- If snippets are enough to answer confidently, do not over-fetch.
- If freshness is uncertain, search again before concluding.
- If your search tool is down or materially degraded, label the output `LIMITED DATA` and avoid pretending current coverage is complete.

### Source Quality Hierarchy
When synthesizing information from multiple sources, weight them in this order:
1. **Primary:** SEC filings (EDGAR), company investor relations, Federal Reserve (FRED, FOMC statements), official government releases
2. **Tier 1 data:** Earnings transcripts, sell-side research from top-10 firms, exchange data
3. **Tier 1 journalism:** Reuters, AP, CNBC official reporting (not opinion)
4. **Industry-specific:** SIA (semiconductors), CoinDesk/The Block (crypto regulation), EIA (energy)
5. **Analytical:** Reputable independent analysts, research aggregators
6. **Sentiment only:** Reddit, Twitter/X, Discord -- use exclusively for sentiment reads, never for facts

Note: this hierarchy ranks source *trust*. Some Tier 1 sources (Bloomberg, WSJ, FT, Barron's) are listed in CLAUDE.md's blocked domains because they paywall content and the snippets aren't useful -- the trust ranking still applies if you encounter them via another route, but don't waste fetches on them directly.

Recommended query pattern:
1. Price, mark, or quote query
2. Recent catalyst or news query
3. Macro, sector, peer, or regulatory query
4. Variant-view or contradictory-evidence query
5. Portfolio alternative or benchmark query when useful

## F. Portfolio Math Rules
- Holdings source of truth:
  - `<VAULT_ROOT>/private/holdings-taxable.md`
  - `<VAULT_ROOT>/private/holdings-ira.md`
- If held, calculate portfolio impact from actual share counts or token amounts.
- If not held, say "Not currently held."
- Do not fabricate cost basis or P&L numbers.
- Respect these known caveats:
  - Some ETFs have pending corporate actions (e.g., a stock split) that mechanically change share count and price while total value does not -- record these in your CLAUDE.local.md caveats.
  - Some positions have a documented behavioral pattern around catalysts (e.g., a recurring post-earnings drift); document these as known caveats so analyses frame them consistently.

## G. Internal Comparison Rules
Where relevant, compare against:
- prior Osanwe view or prior analysis file
- benchmark, peer, or sector alternative
- current portfolio alternative use of capital

Examples:
- better than adding to a core index position right now?
- worse risk/reward than an existing held position?
- incremental improvement versus the last view on this name?

Do not force a comparison when it is artificial. Use it when it sharpens the decision.

## H. Output Contracts
Use one of these three response forms.

### 1. Short Analytical Form
Use for Telegram-compact answers such as `/price`, quick thesis checks, compact `/performance`, and portfolio mover notes.

Required shape:
- six-part spine
- one compressed line for what changed
- one compressed line for the variant view or "no credible variant view"
- one compressed line covering bull, bear, and next trigger
- one compressed line for change-my-mind or invalidation and the most important unknown

Target length:
- 6 to 12 short lines

### 2. Standard Analytical Form
Use for most direct answers, `/thesis`, market-linked `/research`, and key sections inside briefings.

Required shape:
- six-part spine
- what changed
- variant view
- key numbers
- base, bull, bear
- catalyst map
- evidence quality
- action implication

Target length:
- 10 to 20 lines or 2 to 5 short paragraphs

### 3. Deep Analytical Form
Use for `/invest`, `/invest-max` decision summaries, and market-linked deep research.

Required shape:
- six-part spine up front as a decision sheet
- what changed
- variant view
- key numbers
- base, bull, bear
- catalyst map with upgrade, downgrade, and invalidation triggers
- portfolio decision layer
- supporting valuation, quality, risk, macro, peers, and benchmark comparisons only when they change the decision

Target length:
- as needed, but the decision sheet must be the highest-density section and appear before deeper support

## I. Failure Behavior
- If a required input is missing, say exactly what is missing.
- If a live quote cannot be confirmed, do not fake one.
- If news is thin, say that directly and move to thesis implications.
- If a portfolio impact cannot be computed, say why.
- If prior Osanwe context does not exist, say that directly in the change-detection line.
- Never end with vague "it depends" language.
- Always provide:
  - base case
  - conviction
  - trigger that would change the view

## J. Decision Discipline
- Conclusions must be decisive enough to guide the user's next step.
- Uncertainty must narrow action, not erase it.
- "Need more data" is acceptable only when paired with the exact missing datapoint and the decision that datapoint would change.
- Good analytical depth means more decision value per line, not more lines.

## Related
[[investing-moc]] | [[ref-research-methodology]]
