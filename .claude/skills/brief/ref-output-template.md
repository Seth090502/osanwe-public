# Brief Output Template (v2)

Reference content for `/brief` Phase O output contract. SKILL.md imperatively Reads this file before writing the briefing + meta.json sidecar. Updated 2026-04-23 for v2 final.

Distinct from v1: canonical frontmatter expanded (regime + macro_regime + cross_asset_coherence + thesis_statuses + priced_in_calls + meta + Brier carry-forward); body section order adds Thesis Status Board + Warning Problems + Alternative Analysis + FOLLOWUPS:skills block; meta.json sidecar specified for machine-readable audit + Brier scoring; daily-note linkback pattern replaces v1's full-briefing-in-daily-note.

---

## 1. Output paths

Two artifacts written per /brief invocation in Phase O:

- **Briefing**: `Calendar/decisions/briefings/briefing-<YYYY-MM-DD>[-HHMM].md`
- **Meta sidecar**: `Calendar/decisions/briefings/briefing-<YYYY-MM-DD>[-HHMM]-meta.json`

Same-day collision (no `--replace`): default to `-<HHMM>` timestamped variant; preserves archival rule.

`--replace` overwrites both files (briefing + sidecar) with same date-only filenames.

`--refresh <path>` mutates only Alerts + FOLLOWUPS sections of an existing briefing; appends to existing meta.json `web_searches` + `followup_skills` arrays; bumps `updated:`; body outside Alerts + FOLLOWUPS byte-exact (sha256-verified).

## 2. Canonical frontmatter (briefing file)

```yaml
---
categories: [decisions]
type: briefing
date: YYYY-MM-DD
regime: <Crisis|Risk-off|Earnings|Fed Week|Risk-on|Rotation>
macro_regime: <Early-cycle|Mid-cycle|Late-cycle|Contraction>
macro_regime_transition: <true|false>
cross_asset_coherence: <coherent-on|coherent-off|divergent>
portfolio_health: <A|B|C|D|F>
confidence: <integer 0-100>
confidence_cap_rule: <none|grade-c-30pct|grade-d-any|stale-2plus|script-fallback>
conviction: <low|medium|high>
thesis_statuses:
  <thesis-slug-1>: <HEALTHY|WATCH|STRESSED|INVALIDATED>
  <thesis-slug-2>: <HEALTHY|WATCH|STRESSED|INVALIDATED>
  <thesis-slug-3>: <HEALTHY|WATCH|STRESSED|INVALIDATED>
  <thesis-slug-4>: <HEALTHY|WATCH|STRESSED|INVALIDATED>
  <thesis-slug-5>: <HEALTHY|WATCH|STRESSED|INVALIDATED>
priced_in_calls:
  - event: <name string>
    date: YYYY-MM-DD
    bull_prob: <int 0-100>
    base_prob: <int 0-100>
    bear_prob: <int 0-100>
    trigger_level: <number with unit string>
prior_brier_score_30d: <float or null if <5 scorable calls>
positions_at_action_zones: [<TICKER>@<price>, ...]
followup_skills_count: <int>
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: complete
tags: [topic/market-brief]
related: ["[[hot]]", "[[<entity-stem-1>]]", "[[<entity-stem-2>]]", "[[<thesis-slug-1>]]"]
---
```

Notes:
- `categories: [decisions]` (one element per Group 25 schema)
- `type: briefing` (canonical subtype)
- `tags: [topic/market-brief]` only -- no ticker/company/thesis tags on briefing frontmatter unless briefing is itself thesis-centric (rare; explicit). Briefing emits one tag namespace.
- `related:` field carries 3-7 wikilinks: always [[hot]] + materially-discussed entities (3-5) + thesis-slugs invoked. Symmetric back-linking applies in Phase P Update 4 (only entities in this field, not every ticker mentioned in body).
- `priced_in_calls:` is a structured list (not free-form). Each scenario gets its own entry. Phase C continuity audit consumes this from prior briefings for Brier scoring.
- `prior_brier_score_30d:` carries forward from continuity audit; null if <5 scorable calls in rolling 30 days.
- `confidence_cap_rule:` audits which evidence-grade rule fired (or `none`). Critical for retrospective calibration.

## 3. Body section order

Skip empty sections entirely (no padding). Do NOT emit "nothing to report" placeholders. Order:

1. **H1 + Generated stamp + flags**

   ```
   # Briefing YYYY-MM-DD[-HHMM]

   **Generated: YYYY-MM-DD HH:MM** [Weekend|Holiday|Pre-Market|Intraday] [BROKERAGE WARN: N days stale]
   ```

2. **BLUF / Counter / Alternative**

   ```
   **BLUF:** <one judgment with numbers + dollar impact>
   **Counter:** <one Tenth Man line with cited evidence + date>
   **Alternative:** <third-order mechanism distinct from Counter; one line>
   ```

3. **Regime block + Health + Priced In**

   ```
   **Day Regime:** <class> -- VIX XX.X [cont|bkwd] (date), <markers>
   **Macro Regime:** <phase> -- <yield curve, unemployment, credit signal> [TRANSITION if flagged]
   **Cross-Asset Coherence:** <coherent-on|coherent-off|divergent> -- <one-line justification>
   **Portfolio Health:** <grade> (<one-line justification>)
   **Priced In:** <expectations>. Surprise: <Y>.
   ```

   (Skip Priced In line entirely if nothing material.)

4. **Markets one-liner**

   ```
   **Markets:** S&P $X,XXX (+/-X.X%) | Nasdaq $XX,XXX (+/-X.X%) | 10Y X.XX% [+/-Xbps] | BTC $XX,XXX (+/-X.X%) | DXY XX.X | VIX XX.X [cont|bkwd] | Oil $XX (+/-X.X%) | Gold $X,XXX
   ```

5. **Signal Dashboard** (compact table; 8-12 lines max including header)

   ```
   ### Signal Dashboard
   | Ticker | Price | Chg% | RSI | vs 50MA | vs 52wk H | Beta | Signal |
   |--------|-------|------|-----|---------|-----------|------|--------|
   | <TICK> | $X    | +X%  | XX  | Above   | -X%       | X.X  | NEUTRAL|
   ...
   ```

6. **Thesis Status Board** (NEW v2; one row per configured thesis; binary statuses)

   ```
   ### Thesis Status Board
   | Thesis | Status | Evidence |
   |--------|--------|----------|
   | orbital-compute     | HEALTHY     | <one-line trigger state>     |
   | <thesis-slug-2>     | WATCH       | <one-line>                   |
   | <thesis-slug-3>     | HEALTHY     | <one-line>                   |
   | <thesis-slug-4>     | HEALTHY     | <one-line>                   |
   | <thesis-slug-5>     | HEALTHY     | <one-line>                   |
   ```

7. **Overnight Earnings** (conditional; skip if no held/watchlist reported)

8. **Portfolio Movers** (positions moving >1%; What/SoWhat/NowWhat; copy-paste order blocks if action)

   ```
   ### Portfolio Movers
   | Ticker | What ($ impact) | So What (thesis) | Now What |
   ...
   
   ORDER (confirm at broker):
   SELL [N.NNN] shares <TICKER> @ $[PRICE] LIMIT
   ```

9. **Pre-Earnings Monitor** (conditional; positions with earnings <=10 trading days)

10. **Geopolitical** (conditional; only items passing CFA 3-stage filter)

11. **Alerts** (FLASH/PRIORITY per ref-monitoring-rules.md sec 1; or skip if none)

12. **Calendar (7 days)** (events with conditional framing + historical pattern one-liner)

13. **Scenario Bar** (conditional; ONLY for highest-conviction catalyst within 7d; SINGLE bar)

    ```
    ### Scenario Bar: <Event> (<Date>)
    Bull (XX%): <outcome> | Portfolio +$XX
    Base (XX%): <outcome> | Portfolio +/-$XX
    Bear (XX%): <outcome> | Portfolio -$XX
    Expected Value: +/-$XX
    ```

14. **Intelligence Gaps** (1-3 bullets; skip on quiet days)

    ```
    ### Intelligence Gaps
    - GAP: <unknown>. Impact: <why it matters>. Resolve: <how to fix>
    ```

15. **Warning Problems** (NEW v2; IC convention; distinct from Gaps)

    ```
    ### Warning Problems
    - WARNING: <signal>. Base rate: <historical context>. Trigger: <what would escalate to action>
    ```

16. **Career** (pipeline counts; flags; 2-3 lines max)

17. **Vault** (1-2 lines; "Healthy" or specific flags)

18. **Optionality Map** (concrete deployable optionality)

    ```
    ### Optionality Map
    - Available cash: $X (Roth) + $Y (Brokerage)
    - Positions at action zones: <ticker @ $X vs entry zone $Y-Z>
    - Career actions ready: <X packets, Y min each>
    - Pending decisions from hot.md: <count, oldest age>
    - Yesterday's commitments: X/Y completed (carried: <list>)
    ```

19. **Today's Focus** (1-3 actions with time-to-decision markers; specific, not generic)

    ```
    ### Today's Focus
    1. WITHIN 30 MIN OF OPEN: <action tied to briefing surface>
    2. BEFORE FOMC 2PM: <action>
    3. EOW: <action>
    ```

20. **FOLLOWUPS:skills block** (NEW v2; Pattern 18 coordination; analog to /invest INGEST:claims)

    ```markdown
    <!-- FOLLOWUPS:skills -->
    - /invest <TICKER> -- export-control signal pressures orbital-compute thesis; [SHARES] combined shares at thesis WATCH threshold (trigger: WITHIN 48H if confirmed by regulator)
    - /challenge orbital-compute -- orbital-compute effective exposure THESIS_CAP_AMBER approaching configured amber threshold (trigger: EOW)
    - /networth -- portfolio value delta >5% since last snapshot; refresh recommended
    - /decide -- <TICKER> trim at $[PRICE] triggered; structured decision record if action taken
    - /retro -- queue at session end if substantive trades/decisions emerge
    <!-- /FOLLOWUPS:skills -->
    ```

    Empty case (no triggers): render `(no followup skills recommended)` between tags. Each emitted skill has concrete one-line rationale tied to briefing body. /retro must be able to parse this block.

21. **Footer: Prior-day calibration** (one line if Brier scoring active; Phase C continuity audit output)

    ```
    ---
    Prior-day calibration: Yesterday: priced-in CPI 3.0-3.3% base 55%; actual 3.1% -> Base HIT
    ```

    Skip if `prior_brier_score_30d` is null (insufficient prior calls).

## 4. Daily note linkback pattern

Phase P Update 1 replaces the entire `## Market Pulse` section body in `Calendar/daily/<today>.md` with a one-line summary + linkback. Body outside `## Market Pulse` is byte-exact (sha256-verified).

Replacement format:

```markdown
## Market Pulse
**BLUF:** <BLUF text>. **Regime:** <day>/<macro>. **Coherence:** <class>. **Health:** <grade>. **Confidence:** <N>%. Full briefing: [[briefing-<date>[-HHMM]]]
```

Distinct from v1 (which wrote the full briefing into the daily note `## Market Pulse` section). v2 keeps the daily note compact and routes the full briefing to the canonical path.

## 5. Meta.json sidecar schema

Written alongside briefing at `Calendar/decisions/briefings/briefing-<YYYY-MM-DD>[-HHMM]-meta.json`. Machine-readable audit trail enabling retrospective Brier scoring + calibration feedback by future /retro and /review runs.

```json
{
  "schema_version": 1,
  "briefing_date": "YYYY-MM-DD",
  "generated_at": "YYYY-MM-DDTHH:MM:SS",
  "mode": "normal",
  "script_output_hash": "<sha256 of fetch-prices.py stdout>",
  "indices_snapshot": {
    "SPX": {"price": 5500.0, "change_pct": 0.4, "date": "YYYY-MM-DD"},
    "NASDAQ": {...},
    "DOW": {...},
    "VIX": {"price": 14.2, "term_structure": "contango", "change_pct": -0.5, "date": "YYYY-MM-DD"},
    "10Y": {...},
    "DXY": {...},
    "GOLD": {...},
    "OIL": {...}
  },
  "equities_snapshot": [
    {"ticker": "<TICKER>", "price": 250.00, "prev_close": 246.50, "change_pct": 1.42, "rsi14": 57.0, "ma50": 240.0, "ma200": 210.0, "beta": 1.60, "short_ratio": 1.5, "pct_from_52wk_high": -4.0, "next_earnings": "YYYY-MM-DD", "date": "YYYY-MM-DD"},
    ...
  ],
  "crypto_snapshot": [
    {"ticker": "XRP", "price": 1.42, "change_pct": 2.1, "date": "YYYY-MM-DD"},
    ...
  ],
  "web_searches": [
    {"query": "HY OAS spread today", "url": "https://...", "grade": "B"}
  ],
  "regime_markers": {
    "vix": 14.2,
    "term": "contango",
    "oas_bps": null,
    "classification": "Risk-on"
  },
  "macro_regime_markers": {
    "yield_curve_10y_3m_bps": 75,
    "unemployment_trend": "stable_low",
    "credit_spreads": "tightening",
    "classification": "Late-cycle"
  },
  "cross_asset_coherence": "coherent-on",
  "portfolio_health": "B",
  "thesis_statuses": {
    "orbital-compute": "HEALTHY",
    "<thesis-slug-2>": "WATCH",
    "<thesis-slug-3>": "HEALTHY",
    "<thesis-slug-4>": "HEALTHY",
    "<thesis-slug-5>": "HEALTHY"
  },
  "priced_in_calls": [
    {
      "event": "CPI Mar 2026",
      "date": "2026-04-15",
      "bull_prob": 25,
      "base_prob": 55,
      "bear_prob": 20,
      "trigger_level": "3.0-3.3% YoY core",
      "scored": false,
      "outcome": null,
      "scored_date": null
    }
  ],
  "prior_brier_score_30d": 0.18,
  "confidence": 75,
  "confidence_cap_rule": "none",
  "conviction": "medium",
  "followup_skills": [
    {"skill": "/networth", "rationale": "portfolio delta >5% since last snapshot", "trigger": "today"}
  ],
  "phases_timing_ms": {
    "A": 12, "B": 3, "C": 145, "D": 3500, "E": 80, "F": 25, "G": 18, "H": 60,
    "I": 220, "J": 95, "K": 110, "L": 40, "M": 55, "N": 30, "O": 180, "P": 420
  },
  "pre_output_gate_results": {
    "item_1_bluf_judgment": "PASS",
    "item_2_counter_present": "PASS",
    "item_3_priced_in_or_skipped": "PASS",
    "item_4_alternative_present": "PASS",
    "item_5_dollar_exact": "PASS",
    "item_6_signal_dashboard_exact": "PASS",
    "item_7_dates_explicit": "PASS",
    "item_8_day_regime_classified": "PASS",
    "item_9_macro_regime_classified": "PASS",
    "item_10_coherence_classified": "PASS",
    "item_11_thesis_board_complete": "PASS",
    "item_12_contradictory_surfaced": "PASS",
    "item_13_evidence_grades": "PASS",
    "item_14_geo_cfa_filter": "PASS",
    "item_15_pct_confidence": "PASS",
    "item_16_empty_skipped": "PASS",
    "item_17_intelligence_gaps_flagged": "PASS",
    "item_18_warning_problems_emitted": "PASS",
    "item_19_pre_earnings_monitor": "PASS",
    "item_20_cross_account_combined": "PASS",
    "item_21_body_word_count": "PASS"
  }
}
```

Field semantics:
- `script_output_hash`: sha256 of fetch-prices.py stdout. Enables idempotency check and audit of source data integrity.
- `priced_in_calls[].scored`, `outcome`, `scored_date`: filled by future /brief runs during Phase C continuity audit when actual outcomes resolve. Initialize as `false`/`null`/`null` at write time.
- `prior_brier_score_30d`: float between 0.0 (perfect) and 1.0 (worst). Computed via `mean((forecast_prob - outcome)^2)` across rolling 30-day scorable calls. Null if <5 scorable calls.
- `confidence_cap_rule`: which Pre-Output gate cap rule fired (`none`, `grade-c-30pct`, `grade-d-any`, `stale-2plus`, `script-fallback`).
- `phases_timing_ms`: per-phase elapsed milliseconds; surfaces performance regressions across versions.
- `pre_output_gate_results`: PASS/FAIL per gate item; if any FAIL, no briefing was written and sidecar may not exist.

## 6. ASCII discipline

All NEW content (briefing body + sidecar JSON) must be ASCII-only. Apply Pattern 22 replacement table pre-write (em-dash -> `--`, curly quotes -> `"`/`'`, arrows -> `->` / `<-`, `<=` / `>=`, ellipsis -> `...`, euro -> `EUR`, NBSP -> space, middle dot -> `-`). Byte-scan; HALT on any byte > 127.

Pre-existing legacy non-ASCII in unmodified body sections is tolerated (body-preservation invariant covers it byte-exact); applies to NEW insertions only.

## 7. Validation gates (Phase O)

After composing briefing + sidecar:

1. Frontmatter parses via ruamel.yaml without error
2. JSON sidecar parses via stdlib json without error
3. ASCII byte-scan on briefing body (modulo body-preservation legacy): zero bytes > 127
4. ASCII byte-scan on sidecar JSON: zero bytes > 127
5. Body word count <= 650 (3-minute rule); --quick mode <=200
6. Tag vocabulary: only `topic/market-brief` (HALT on drift)
7. `related:` field has 3-7 wikilinks (Pattern 8 fan-out bound)

Any failure -> HALT before Phase P Write; do not write briefing or sidecar; F11 stays on; report which gate failed.

## 8. Daily note creation (if missing)

If today's daily note does not exist (SessionStart hook should have created it; rare edge case if running mid-session before hook fires), create it with the canonical 9-section schema BEFORE Phase P Update 1:

```markdown
# YYYY-MM-DD

## Market Pulse

## Observations

## Decisions

## Commitments

## Insights

## Sessions Run

## Cross-References

## Tasks

## Log
```

Then Phase P Update 1 replaces the empty `## Market Pulse` body with the linkback pattern from sec 4.
