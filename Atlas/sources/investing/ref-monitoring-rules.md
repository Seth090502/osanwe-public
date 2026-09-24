---
categories:
  - sources
type: reference
created: 2026-04-05
updated: 2026-06-08
status: active
confidence: high
tags:
  - topic/monitoring
  - topic/alerts
  - topic/market-regime
aliases: [monitoring-rules, alert-rules]
related: ["*ref-portfolio-doctrine* (not published)", "[[ref-macro-landscape]]", "*ref-market-calendar* (not published)", "[[ref-theme-alpha]]", "[[ref-evidence-hierarchy]]", "[[ref-briefing-structure]]", "[[ref-regime-taxonomy]]"]
---

# Reference: Monitoring Rules
Last updated: 2026-04-11
Source: Extracted from Project Osanwe SOUL.md and AGENTS.md (April 7-9, 2026 builds) during vault cleanup
Refresh cadence: Quarterly
Purpose: Codifies `<owner>`'s alert classification thresholds, suppression logic, market regime framework, proactive monitoring triggers, and briefing templates. These define what warrants attention and what doesn't.

## Trigger Conditions
Load this document when:
- Any question about whether a price move warrants alert-level attention
- Any market regime question (risk-on, risk-off, rotation, crisis, earnings season, Fed week)
- Any question about pattern detection or recurring market behaviors
- Any "should I be paying attention to this?" classification question
- Any question about what to monitor proactively vs. what to ignore
- When building or reviewing a briefing for `<owner>`
- When deciding whether a market event justifies interrupting `<owner>`'s attention

---

## 1. Intelligence Classification System

Every piece of market intelligence carries an implicit priority level. These determine urgency.

### FLASH -- Immediate, High-Priority
Triggers:
- Single equity position moves exceeding 8% intraday
- Single crypto position moves exceeding 12% in 24 hours (crypto is more volatile -- higher threshold)
- Earnings miss/beat exceeding 15% on a held position
- Regulatory action directly affecting a holding (SEC enforcement, executive order, sanctions)
- Breaking geopolitical event with direct market transmission (conflict escalation, trade policy shock)

### PRIORITY -- Worth Immediate Attention
Triggers:
- Analyst upgrades/downgrades on held positions by major firms
- Sector rotation signals affecting portfolio concentration
- Macro data releases that materially shift the rate/inflation narrative (CPI, jobs, FOMC)
- Crypto regulatory developments (CLARITY Act vote, SEC ruling) even without immediate price impact

### ROUTINE -- Include in Next Scheduled Analysis
- Market summary and index levels
- Portfolio mark-to-market within normal range (under 2% per position)
- Watchlist movements
- Earnings calendar updates
- Knowledge base and ref doc health checks

### BACKGROUND -- Note but Don't Report
- Historical context notes
- Reference document updates
- Non-actionable macro commentary
- Information that confirms existing thesis without adding new data

---

## 2. Suppression Logic

When checking market conditions and ALL of these are true, the correct response is "nothing material to report":
- No held equity position moved more than 2% since last analysis
- No held crypto position moved more than 4% since last analysis
- No earnings were reported or are reporting today for holdings or watchlist
- No FOMC, CPI, jobs, or other Tier 1 macro data was released
- No breaking geopolitical news with portfolio transmission

The goal is zero unnecessary noise. When the system speaks, it should matter.

---

## 3. Market Regime Framework

Track the current market environment and adjust emphasis accordingly.

### Regime Types
| Regime | Characteristics | Emphasis |
|--------|---------------|----------|
| **Risk-on** | VIX <16, breadth expanding, growth outperforming | Opportunity focus, watchlist evaluation |
| **Risk-off** | VIX >25, correlations rising, defensives outperforming | Portfolio defense, thesis stress testing |
| **Rotation** | Sector divergence, some up some down, VIX moderate | Sector analysis, which theses are winning/losing |
| **Crisis** | VIX >35, correlations approaching 1.0, liquidity stress | Lead with total portfolio impact, actionable only |
| **Earnings season** | 2 weeks around major tech earnings | Escalated monitoring, pre-earnings positioning, historical patterns |
| **Fed week** | FOMC decision week | Rate sensitivity analysis, bond yield impact on equity valuations |

### Regime-Adaptive Behavior
- In **crisis mode:** Focus entirely on portfolio impact. Skip non-essential topics.
- In **risk-on calm:** Analysis can be lighter. Other domains get more space.
- In **earnings season** for held positions: Automatically escalate to pre-earnings monitoring (see ref-portfolio-doctrine.md Section 6).

---

## 4. Proactive Monitoring Triggers

### Investment Triggers
- Held position approaches action zone from invest-max report (read valuation.md for zones)
- Earnings within 5 trading days for any holding (enter pre-earnings mode per ref-portfolio-doctrine.md)
- Crypto position moving on regulatory news (even below alert threshold)
- theme-alpha concentration exceeds the tiered cap (60% amber, interim 50% during the phase-in; 70% red) OR any other thesis exceeds 40% OR any single name exceeds 30% (amber; 35% red -> escalate to /decide) (per ref-portfolio-doctrine.md)
- Tax-advantaged account cash undeployed 14+ days after relevant research completes
- Peer company reports earnings before a holding (leading indicator signal per ref-portfolio-doctrine.md)
- 3+ holdings in same thesis move 2%+ same direction (thesis-level event per ref-portfolio-doctrine.md)

### Intelligence Gaps
When something is noticed but cannot be fully researched, note it:
```
INTELLIGENCE GAP: [Topic]. Noted [date].
Suggested: [Queue /invest, /research, or manual investigation]
```

### Weekend Research Queue
Friday analysis should include:
```
WEEKEND RESEARCH QUEUE:
  - [TICKER/topic] -- [reason this would benefit from deep research]
  - [TICKER/topic] -- [reason]
```

---

## 4.5 Extended-hours signal thresholds (Mission Three; 2026-05-05)

Operational thresholds for after-hours (16:00-20:00 ET) and pre-market (04:00-09:30 ET) signal classification surfaced via fetch-prices.py prepost=True intraday call. Surfaced in /brief Signal Dashboard AH/PM column + Phase J Extended-Hours Movers subsection; /networth Phase 2 live-valuation source decision.

- **ah_mover threshold:** 3.0% (configurable via `AH_MOVER_THRESHOLD_PCT` env var). When `abs(extended_hours_change_pct) >= threshold`, ticker is added to `signals.ah_movers[]` and `extended_hours_movers[]` aggregation.
- **Material AH gap:** 5.0% (used by /invest Phase J.5 drift class once Mission Four-bis adds dispatch). Triggers Material/High severity drift escalation to /retro for ratification.
- **Quiet-day suppression interaction:** AH movers >= 5.0% suppress regular quiet-day BLUF redirect in /brief (AH-quiet != regular-quiet; the regular-session 7-condition quiet rule does not apply when AH session has material movers).
- **0-volume edge:** `extended_hours_volume = 0` is valid (AH session active but ticker untraded that minute). Distinguishable from `null` (no AH session). Consuming code renders "$X (after-hours, untraded)" for the 0-volume case; not a signal-suppression case.
- **Doctrine boundary:** concentration math + trim trigger evaluation REMAIN regular_market_close anchored (NOT AH-priced) per ref-portfolio-doctrine. AH valuation is reported in /networth snapshots (`valuation_session` frontmatter) but does NOT trigger doctrine threshold evaluations -- AH prices are volatile + transient.

---

## 5. Briefing Architecture

### Daily Morning Briefing
Modeled after a Presidential Daily Brief crossed with a hedge fund morning note.

**1. SITUATION OVERVIEW** (3-4 sentences max)
The single most important thing `<owner>` needs to know today. What changed overnight. If nothing material changed, say so in one sentence.

**2. MARKET INTELLIGENCE**
Pre-market snapshot. Only include what's relevant:
```
Futures: S&P [+/-]X% | NQ [+/-]X% | R2K [+/-]X%
VIX: XX.X ([+/-]X.X)
Rates: 10Y X.XX% | 2Y X.XX% | Curve [inverted/steepening/flat]
DXY: XXX.X ([+/-]X.X%)
Crypto: BTC $XXk ([+/-]X%) | ETH $X,XXX ([+/-]X%)
Oil: $XX.XX ([+/-]X%) | Gold: $X,XXX ([+/-]X%)
```
Skip lines if moves are under 1.5%.

**3. PORTFOLIO WATCH**
Only positions with moves exceeding 2% OR specific catalysts:
```
[TICKER] [+/-]X.X% to $XXX.XX | [Catalyst]
  Exposure: X.XX shares across all held accounts = X.XX total
```
If no positions meet the threshold: "Portfolio: No material moves." One line.

**4. CATALYST CALENDAR**
What is happening TODAY and THIS WEEK that could move held positions or watchlist.

**5. GEOPOLITICAL RADAR**
Only include if there is actual geopolitical news with portfolio relevance. If nothing, skip entirely. When included, use transmission mapping from ref-geopolitical-framework.md.

**6. STRATEGIC ASSESSMENT**
One to three sentences. The highest-conviction current view. If unchanged: "No thesis changes warranted."

**7. OPERATIONS STATUS**
Research completion status, cash deployment status, ref doc health.

### Weekend Briefing
No market data. Reflective and forward-looking.

1. **WEEK IN REVIEW** -- Portfolio P&L, biggest movers, thesis confirmations/challenges
2. **WEEK AHEAD PREVIEW** -- Monday events, earnings calendar, macro calendar, geopolitical events
3. **STRATEGIC NOTES** -- Positions approaching action zones, concentration check, thesis health
4. **SYSTEM HEALTH** -- Recent analysis outputs, ref doc freshness, knowledge base updates

### Weekly Strategic Review (Sunday)
Deeper than the weekend briefing. The "zoom out" moment.

- **Sector rotation analysis:** Where is money flowing? How does this affect portfolio positioning?
- **Thesis scoreboard:** Rate each core thesis 1-10 with one sentence justification
- **Concentration risk:** Current portfolio weights by thesis/sector + single-name. Flag if theme-alpha >60% (interim 50% during the phase-in) or any other thesis >40% or any single name >30% (amber; >35% red -> escalate to /decide) (per ref-portfolio-doctrine.md)
- **Forward calendar:** The 3-5 most important events in the coming 2 weeks
- **Pending decisions:** What is `<owner>` waiting on?
- **Recommendation queue:** If any invest-max report has been complete for 7+ days without action, flag it

## Related
*investing-moc* (not published) | *ref-portfolio-doctrine* (not published) | *ref-geopolitical-framework* (not published) | *watchlist* (not published)
