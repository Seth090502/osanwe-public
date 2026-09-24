---
aliases: [fin-behavioral-decision-hygiene]
categories: [wiki]
type: reference
status: active
created: 2026-08-24
updated: 2026-08-24
tags:
  - topic/finance
related: []
---

# Behavioral Decision Hygiene

Status: framework (active)
Scope: all BUY / SELL / TRIM decisions on held and candidate positions
Related: fin-digital-twin-spec.md, wave analyses, /journal

---

## 1. Purpose

Markets punish process errors more reliably than they reward cleverness. This
document binds behavioral finance theory to the vault's operating workflow so
that every trade decision passes through the same hygiene gates. The goal is
not to eliminate bias (impossible) but to make bias *detectable at decision
time* rather than discoverable at reconciliation time.

---

## 2. Pre-Trade Checklist: 7 Questions Before Any BUY / SELL / TRIM

Every order must be answerable in writing (journal entry) before execution.
Any question answered with "gut feel" or "it just seems cheap/expensive" is an
automatic STOP.

1. **THESIS**: What is the current thesis for this position, in one sentence?
   Has anything material changed since the last documented review? If the
   thesis cannot be stated in one sentence, do not trade.

2. **PRE-COMMITMENT CHECK**: Does this action match a pre-committed scenario
   response from the position's wave analysis? If YES, cite the scenario ID.
   If NO, this is a deviation -- see Section 4 before proceeding.

3. **KILL-CRITERIA STATUS**: Are any kill criteria currently triggered or
   within one standard deviation of triggering? If triggered and you are
   NOT selling, name the specific reason you are overriding them (and record
   that reason as a falsifiable claim).

4. **BIAS SWEEP** (see Section 3): Which of the five mapped biases is most
   likely to be distorting this exact decision right now? Name it explicitly.
   "None" is not an acceptable answer; pick the closest risk and say why it
   does not apply.

5. **COUNTERFACTUAL**: If you did not already hold (or had not already
   watched) this position, would you take this exact action today at this
   price? This neutralizes anchoring on cost basis and endowment effects.
   Answer honestly: "no" means the action is driven by history, not value.

6. **SIZING / PORTFOLIO IMPACT**: What does the portfolio look like after
   this trade? Concentration, sector/factor exposure, cash buffer. Does any
   single position cross a documented limit?

7. **REVERSIBILITY & REGRET TEST**: If this trade is wrong, what is the cost,
   how would I know I am wrong (falsification criteria), and by when? A trade
   with no stated falsification criterion has no exit logic and should not be
   placed.

Record: date, ticker, action, checklist answers, scenario ID or deviation
rationale, emotional state tag (calm / urgent / fomo / defensive).

---

## 3. Bias-to-Detection Mapping

| Bias | Definition | How It Shows Up Here | Detection Signal |
|---|---|---|---|
| Overconfidence | Excess certainty in own forecasts; underestimation of variance | Confidence in a call far exceeds the evidence quality; confidence map diverges from realized hit rate | **Confidence-map gap**: compare logged pre-trade confidence vs. outcomes over rolling 20 trades. Persistent gap > 15 points = calibration failure; shrink position sizes until recalibrated |
| Disposition effect | Selling winners too early to lock in gains; riding losers | Trimming/taking profits on positions whose thesis is intact while holding broken theses | Flag any SELL where the stated reason is profit-taking rather than a thesis/valuation trigger. Check whether winners sold early subsequently outperformed the cash they became |
| Loss aversion | Losses loom ~2x larger than equivalent gains | Holding past kill criteria because selling realizes the loss ("it will come back") | Any position past its kill criteria for > 5 trading days without a documented override = loss-aversion flag. The override rationale must be written as if advising someone else |
| Recency bias | Overweighting the most recent regime/data | Extrapolating last month's price action into forecasts; abandoning long-horizon theses after short drawdowns | Compare the decision's implied regime view against the wave analysis's structural view. Divergence between "what happened recently" and "where we are in the wave" requires explicit justification |
| Anchoring | Fixating on arbitrary reference points | Cost basis used as a sell/hold anchor; prior 52-week high treated as "fair value" | Question 5 (counterfactual) directly attacks this. Additionally: any journal entry citing purchase price as a reason is auto-flagged -- cost basis is irrelevant to forward-looking decisions except for tax lots |

Escalation rule: two flags on the same trade = mandatory 24-hour cooling
period before execution (unless kill criteria are triggered, which always
executes immediately).

---

## 4. Pre-Commitment Framework

Principle: decisions made calmly in advance beat decisions made under price
pressure. Every held position carries pre-committed scenario responses
derived from its wave analysis.

Structure per position:

- **Scenario table**: for each analyzed scenario (base / bull / bear / black
  swan), a pre-written response: action, sizing change, and trigger conditions
  (price levels, fundamental markers, macro signals).
- **Trigger specificity**: triggers must be observable and mechanical where
  possible ("close below X for 3 sessions", "guidance cut > Y%", "factor Z
  crosses threshold"). Vague triggers ("if things get worse") are rejected.
- **Deviation protocol**: acting outside the pre-committed responses is
  permitted but MUST be documented in /journal BEFORE execution with:
  1. The pre-committed response being overridden
  2. New information justifying the deviation (must not have been knowable
     when the scenarios were written)
  3. Falsifiable prediction of what the deviation achieves
- **Review cadence**: scenario tables are re-derived after each wave analysis
  refresh; stale tables (> 90 days without refresh) suspend discretionary
  deviations for that position.

Rationale: Thaler/Benartzi-style commitment devices convert willpower
problems into rule-following problems. Deviations remain possible -- rigid
rules break in genuinely novel situations -- but each deviation costs effort
and leaves an audit trail, which suppresses casual overrides.

---

## 5. The Journal Feedback Loop

/journal is the measurement instrument for this entire framework. Without it,
the checklist and pre-commitments degrade into ritual.

Loop mechanics:

1. **Log at decision time** (not after): checklist answers, scenario ID or
   deviation rationale, confidence level (0-100), emotional state tag.
2. **Log outcome later**: at position close or scheduled review, record
   realized result vs. the falsification criteria set at entry.
3. **After 20+ entries**, run pattern analysis:
   - Calibration curve: stated confidence vs. realized accuracy (targets
     overconfidence directly)
   - Action-type breakdown: which flags correlate with losses (e.g., trades
     flagged for disposition effect vs. their P&L)
   - Timing analysis: decisions made during high-volatility days vs. calm
     days; market-hours vs. after-hours impulses
   - Override ledger: pre-committed responses followed vs. overridden, and
     the P&L of each population
4. **Feed back**: recurring weakness patterns become new standing rules or
   tightened triggers. Example: if 70% of deviation-override trades lose
   money, tighten the deviation protocol; if early winner-trims repeatedly
   underperform, add a "trim only on valuation trigger" rule.

Expected finding: every operator has 1-2 dominant personal weaknesses (most
commonly loss aversion + recency in combination). The point of the loop is
to identify YOURS from your own data, then build targeted countermeasures --
not to memorize a generic bias list.

Cadence: formal pattern review at every 20 entries minimum; lightweight
self-check weekly.

---

## 6. Summary Rules

- No trade without the 7-question checklist, in writing, first.
- Name the bias most likely to be active in every decision; "none" is banned.
- Kill criteria triggered = act, unless a written falsifiable override exists.
- Cost basis never appears as a forward-looking reason.
- Pre-committed scenarios govern; deviations cost documentation.
- The journal is the feedback loop; unmeasured process is unmanaged process.
