# Brief Macro Data Sources (FRED) -- Phase E regime classification

Reference content for `/brief` Phase E (Regime Detection). SKILL.md Phase E.0 Reads this file to fetch authoritative macro series from the FRED MCP (`mcp__fred__fred_get_series`) and classify the day + macro regime from structured data instead of a web-search guess. Added 2026-06-05 (overnight MCP-max run, Wave 1; ADD-NOW -- additive, does NOT change any briefing verdict; the regime label is a classification, not a BUY/SELL rating).

This is the authoritative replacement for the prior "Web search ONCE if HY OAS / credit spread data needed" instruction. FRED supplies the WHOLE Phase E input set: yield curve, credit spread, unemployment, inflation, policy rate, and VIX cross-check. Keep the existing Phase E classification TABLES (day-regime 6-class + macro-regime 4-class) intact -- this ref only changes where the inputs come from.

---

## 1. FRED series catalog (the Phase E input set)

Call `mcp__fred__fred_get_series` with `limit: 2-3, sort_order: desc` (latest obs + prior for delta). All series live-confirmed 2026-06-03/04.

| Series ID | What | Phase E use | Units | Freq |
|---|---|---|---|---|
| `DGS10` | 10Y Treasury yield | Markets line + deploy rate-gate (vs USER_SET threshold) | Percent | daily |
| `DGS2` | 2Y Treasury yield | curve, Fed-path read | Percent | daily |
| `T10Y3M` | 10Y-3M spread (recession signal) | **macro-regime curve row** | Percent | daily |
| `T10Y2Y` | 10Y-2Y spread | macro-regime curve cross-check | Percent | daily |
| `BAMLH0A0HYM2` | ICE BofA US HY OAS (credit spread) | **day-regime + macro-regime credit row** | Percent | daily |
| `VIXCLS` | CBOE VIX close | **day-regime VIX row** (cross-check vs Phase D script VIX) | Index | daily |
| `UNRATE` | Unemployment rate | **macro-regime unemployment row** | Percent | monthly |
| `CPILFESL` (units=`pc1`) | Core CPI YoY | CPI scenario priced-in anchor (Phase K) | Percent YoY | monthly |
| `FEDFUNDS` | Fed funds effective | policy-rate context | Percent | monthly |
| `DFII10` | 10Y real yield (TIPS) | gold/crypto/duration context (optional) | Percent | daily |

Convert HY OAS percent to bps for the day-regime table (e.g. 2.75% = 275bps).

## 2. Day-regime mapping (FRED -> the existing 6-class table)

The existing day-regime table thresholds are UNCHANGED. Source the markers from FRED:
- **VIX**: `VIXCLS` (cross-check against the Phase D `tools/fetch-prices.py` VIX; report the FRED close + note any divergence).
- **Credit**: `BAMLH0A0HYM2` in bps. Crisis row >500bps; "OAS widening" = positive delta vs prior obs; "tightening" = negative delta.
- **Term**: keep the Phase D script's VIX term-structure (contango/backwardation) -- FRED does not carry the VIX futures curve.
- VIX > 25 still classifies Risk-off regardless of OAS (existing rule).

## 3. Macro-regime mapping (FRED -> the existing 4-class table)

The existing macro-regime 4-class table is UNCHANGED. Source the three columns from FRED:
- **10Y-3M**: `T10Y3M`. Steep = large positive; Normal = mid-positive; Flat/inverted = near-zero or negative; Re-steepening = rising from a prior inversion (use `T10Y2Y` to corroborate).
- **Unemployment**: `UNRATE` latest + 2-3 prior obs to read the trend (Falling / Stable-low / Rising).
- **Credit**: `BAMLH0A0HYM2` level + delta (Tight/tightening vs Wide/widening).

## 4. Availability-guard pattern (graceful degrade -- mirrors price-fetcher v3)

```
TRY mcp__fred__fred_get_series for each series (read-only).
ON success: classify from FRED; tag provenance "FRED:<series_id> asof <obs_date>"; freshness from obs date.
ON MCP absence/error (Codex engine, headless, server down, pre-tool-registration):
  SKIP FRED silently; fall back to the prior path (Phase D script 10Y/VIX + ONE web search for HY OAS).
  Output contract byte-stable; the regime classification + tables are identical either way.
NEVER HALT on FRED absence.
```

## 5. Caveats (from the capability matrix C1-C9)
- **C6 -- no ISM/PMI on FRED** (proprietary licensing dropped). The macro-regime table does not require ISM; curve + unemployment + credit carry the classification. If ISM is wanted, it stays a web search.
- **C8 -- revision/vintage**: monthly series (UNRATE, CPI, FEDFUNDS) are revisable. For any backtest/Brier use, pass `output_type=4` (initial release) to avoid look-ahead; for the live briefing, the latest revised value is correct.
- **C7 -- BAMLH0A0HYM2 ships only 3yr of history** (FRED note Apr 2026). Fine for current-regime reads.

## 6. Live snapshot example (2026-06-03/04; classification worked end-to-end)

| Series | Value | Read |
|---|---|---|
| DGS10 | 4.49% | above the USER_SET deploy threshold -> HOLD |
| DGS2 | 4.08% | -- |
| T10Y3M | +0.69 | un-inverted, flat-ish positive |
| T10Y2Y | +0.42 | steepening |
| BAMLH0A0HYM2 | 2.75% (275bps) | TIGHT (well below 500bps Crisis) |
| VIXCLS | 16.06 | Risk-on/Rotation boundary |
| UNRATE | 4.3% (4.4->4.3->4.3) | stable-low |
| CPILFESL pc1 | 2.74% YoY | -- |
| FEDFUNDS | 3.63% | cut cycle |

**Day regime** -> Rotation/Risk-on boundary (VIX 16.06, credit tight 275bps, no stress). **Macro regime** -> Late-cycle (flat-ish curve +0.69, stable-low unemployment 4.3%, tight-but-watch credit). Matches the 2026-06-05 briefing's "Late-cycle macro" read -- now sourced authoritatively from FRED instead of a web guess.
