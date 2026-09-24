# Reference: journal entry format, vocabularies, and computation logic

Companion to `SKILL.md`. Defines the canonical entry template, every
controlled vocabulary, the lot-matching algorithm, and the exact formulas
behind `/journal review`. Nothing here overrides the Cage rules in SKILL.md.

## 1. Canonical entry file

Path: `Calendar/journal/<YYYY-MM-DD>-<TICKER>.md`
(`<YYYY-MM-DD>` = trade_date of the FIRST entry in the file).

```markdown
---
aliases: []
categories: [journal]
type: journal
status: active
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
tags: [ticker/<TICKER>]
related: []
---
# Journal -- <TICKER>

## Entry 1 -- <ACTION> <HH:MM>

- ticker: <TICKER>
- action: <BUY|SELL|TRIM|HOLD>
- trade_date: <YYYY-MM-DD>
- price: <number|NULL>
- size: <positive number|NULL>
- size_unit: <share|usd|contract|unit|NULL>
- horizon: <intraday|swing|position|long-term>
- stated_confidence: <0-100>
- calibrated_confidence: <0-100|NULL>   # from tools/calibrate-confidence.py; NULL = uncalibrated
- emotional_state: <vocabulary below>
- doctrine_compliant: <pass|fail|partial>
- data_quality: <complete|incomplete>

### Context
<1-3 sentences: what prompted this, market/thesis backdrop.>

### Rationale
<Operator's own words, compressed, <=3 sentences. Written BEFORE outcome.>

### Doctrine compliance
| Gate | Result | Evidence |
|---|---|---|
| Trend filter | <PASS|FAIL|N-A> | <basename or none> |
| R/R >= 3:1 | <PASS|FAIL|N-A> | <basename or none> |
| Sizing kernel | <PASS|FAIL|N-A> | <basename or none> |
| Kill criteria | <PASS|FAIL|N-A> | <basename or none> |
| Thesis challenge | <PASS|FAIL|N-A> | <basename or none> |

override: <REQUIRED iff any FAIL -- why the trade proceeded anyway>

### Plan
- entry: <...> ; stop: <...> ; target: <...> ; invalidation: <kill criteria>

### Outcome            <!-- filled later; never at creation -->
- status: <OPEN|CLOSED-WIN|CLOSED-LOSS|CLOSED-FLAT|PARTIAL>
- realized_pct: <signed number|NULL>
- resolved_by: [[<YYYY-MM-DD>-<TICKER>]]   <!-- closing entry file -->
- process_grade: <A|B|C|D>                 <!-- grades PROCESS, not P&L -->

### Related
- [[<TICKER>]]
```

Later same-day entries append as `## Entry 2 -- <ACTION> <HH:MM>` blocks with
identical internal structure. Required-field checklist (every block): ticker,
action, trade_date, stated_confidence, emotional_state, doctrine_compliant,
data_quality, Rationale, Outcome.status. Any missing -> `data_quality:
incomplete` and the block is excluded from review math.

## 2. Controlled vocabularies

- **action**: BUY | SELL | TRIM | HOLD. Direction lives in the action; size
  is always positive. TRIM = partial close of an existing long. HOLD =
  deliberate no-action decision (price/size NULL; enters compliance and
  emotion stats, never P&L stats).
- **emotional_state** (pick ONE tag; free-text nuance goes in Context):
  `calm`, `disciplined`, `fearful`, `bored`, `urgent`, `fomo`, `greedy`,
  `revenge`. Buckets: hot = {fomo, revenge, greedy, urgent, bored};
  cool = {calm, disciplined, fearful}.
- **process_grade**: A = followed plan exactly; B = minor deviation, no P&L
  impact; C = meaningful deviation; D = abandoned plan / no plan.
- **doctrine gates**: the five gates in the template. N-A is legitimate only
  when the gate structurally cannot apply (e.g., Thesis challenge on a
  mechanical index ETF add). A gate that WOULD apply but lacks evidence is
  scored FAIL, not N-A.

## 3. Lot matching (FIFO per ticker)

Maintain per ticker an ordered queue of open lots from BUY entries
(size * price = cost basis). Apply subsequent entries in date order:

- TRIM q units: pop from oldest lots until q exhausted; each consumed slice
  realizes `pct = (trim_price - lot_price) / lot_price * 100` on that slice;
  lot-level `realized_pct` = size-weighted mean of consumed slices. Remaining
  lot stays OPEN with status PARTIAL.
- SELL q units: identical mechanics; if total sold exceeds total open size,
  excess is flagged UNMATCHED (review surfaces it; never silently nets).
- Closing a lot sets the opening block's `Outcome` (status CLOSED-WIN /
  CLOSED-LOSS / CLOSED-FLAT at +/-0.1% boundary, realized_pct, resolved_by ->
  closing entry file) and bumps the closing entry as resolver.
- HOLD: no queue effect.

## 4. Review formulas (over CLOSED trades unless stated)

Let T = closed trades in period, p_i = realized_pct.

- win_rate = |{i : p_i > 0}| / |T|
- avg_gain = mean(p_i for winners); avg_loss = mean(|p_i| for losers)
- expectancy = win_rate * avg_gain - (1 - win_rate) * avg_loss
- profit_factor = sum(winner p_i) / sum(|loser p_i|)
- best/worst = argmax/argmin p_i, reported with ticker, date,
  emotional_state, doctrine_compliant, process_grade
- doctrine_compliance_rate = passes / (passes + fails); partials counted as
  non-compliant in the headline, reported separately with their count
- emotion table: group T by emotional_state -> n, win rate, mean p_i; FLAG a
  state when n >= 3 and |win rate - overall| > 15 percentage points; also
  emit hot-vs-cool rollup (Section 2 buckets)
- confidence cross-tab: band stated_confidence into 50-59 / 60-69 / 70-79 /
  80-89 / 90-100; realized win rate per band; title the table `ADVISORY
  input for confidence-map rebuild`. Bands with n < 3 print
  `n<3 -- anecdotal`.
- OPEN positions: listed separately (ticker, unrealized mark only if fetched
  under the Cage rule), never inside win-rate math.

## 5. Lessons file

Path: `wiki/maintenance/calibration/journal-lessons.md`. Canonical frontmatter
(categories: [wiki], type: report), then three standing H2 sections:
`## Active lessons`, `## Superseded`, `## Calibration deltas`. Each lesson:
one-line imperative statement, supporting entry dates (>= 3 entries across
>= 2 tickers; doctrine-gap + loss pairs promote at 2), trigger condition
(matched by Step L.5), routing target. Ends with
`Related: [[decision-attribution]]` (existing basename; never add unresolved
wikilinks). Strictly additive between runs except the `updated:` bump and
Active -> Superseded moves.

Calibration-loop wiring (who eats what):

1. log captures stated vs calibrated confidence at decision time.
2. review computes realized win rate per stated band (ADVISORY table).
3. lessons parks band misrankings in `## Calibration deltas`.
4. The weekly calibration lane (`ingest-bars -> backtest-offline ->
   calibration-report -> confidence-calibrator`) and /invest R.8/R.9 consume
   the lane BY LOCATION; journal artifacts are advisory inputs and never
   rewrite generator-owned organs (`confidence-map.json` et al.).
5. Next `/journal log` re-surfaces ACTIVE lessons (Step L.5) -- the only
   step where mined history changes entry-time behavior. Loop closed.

## 6. Idempotency and integrity

- Marker signature per entry: `(trade_date, ticker, action, first 40
  normalized chars of Rationale)`. Present in the file already -> SKIP.
- Body preservation: appending a block or filling an `Outcome` section may
  touch only that region; everything else byte-exact.
- Corrections after outcomes are known: new block citing the old entry and
  what changed; never rewrite historical rationale.
