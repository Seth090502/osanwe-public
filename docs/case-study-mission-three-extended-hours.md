---
categories: [docs, case-study]
type: case-study
status: active
created: 2026-05-11
updated: 2026-05-11
tags:
  - mission/three
  - topic/extended-hours
  - topic/additive-diffusion
  - topic/non-regression
---

# Mission Three -- Extended-Hours Two-Call Merge (Case Study)

> Wall clock: 39 minutes. 127 additive entries shipped. Zero regressions. One architectural pattern codified.

## The problem

Late on a Sunday, an extended-hours position move broke into the next session's pre-market without being visible in any briefing the vault produced. The `/networth` skill fires on `regular_market_close` data from yfinance. The `/brief` skill consumes the same dataset Monday morning. Both report the position as of Friday's 4 PM ET print, which misses anything that happened between 4 PM Friday and 9:30 AM Monday -- a 65.5-hour window where a held position had moved 11% on an after-hours catalyst.

The portfolio surprise wasn't the move itself; it was the reaction time. The thesis on the position was already on a "kill criteria approached" watch from a prior `/invest` run, and a single overnight 11% move was the kind of state-change that should have triggered an immediate re-evaluation cycle. Instead, the agent's frame Monday morning was still Friday's data, and the response was a 45-minute delay rebuilding context that was already known elsewhere.

The blind spot was structural: every consumer of price data in the vault was reading from one yfinance call configured for regular-session pricing. The fix needed to surface extended-hours moves without changing the regular-session math that drove portfolio doctrine (concentration ceilings, position-fit calculations, R/R ratios), all of which anchor to regular-market close.

## The constraint

Zero new external dependencies; everything had to ride on the existing yfinance call infrastructure. The vault budget for the quarter was already spoken for; adding a new data provider was off the table.

Preserve doctrine math byte-equivalent. The 1y/1d query that `/networth`, `/brief`, and `/invest` all depend on for the 50DMA / 200DMA / 1-year return / volatility computations had to stay byte-identical pre and post the change. Concentration ceiling math (the doctrine-template amber/red ceilings) anchors on regular-close; any drift would invalidate doctrine compliance verdicts.

Don't break the existing consumers. `/networth`, `/brief`, `/invest` all called the price-fetcher with a known dict-shape return; the additive change needed to expand the return without altering existing fields.

## The design

Two-call merge inside `fetch-prices.py`. The first call -- 1-year history at 1-day granularity (`period="1y", interval="1d"`) -- runs byte-identical to the prior code path. Same parameters, same return shape, same downstream consumption. This is the call that owns doctrine math.

The second call -- 2-day history at 1-minute granularity with `prepost=True` (`period="2d", interval="1m", prepost=True`) -- runs adjacent. It's the new code path. It returns the most-recent extended-hours print plus a 1-minute volume + price trajectory across the prior session + current session's pre/regular/post windows.

The two calls merge into a single per-ticker dict, with the first call's fields untouched and six new fields added:

| Field | Shape | Source | Purpose |
|---|---|---|---|
| `extended_hours_last` | float | second call | Most-recent print across pre/regular/post |
| `extended_hours_change_pct` | float | derived | % change from prior regular_market_close |
| `extended_hours_volume` | int | second call | Aggregate volume across the active EH window |
| `extended_hours_last_timestamp` | ISO UTC | second call | When the print occurred (ZoneInfo-aware) |
| `market_session` | enum | derived | `pre`, `regular`, `post`, or `closed` |
| `ah_source` | str | second call | yfinance request shape (for debugging stale-data root-causing) |

The `market_session` field is the one that prevents downstream consumers from misreading the data. `/networth` reads `market_session == "regular"` and falls through to the byte-identical 1y/1d call's `regular_market_close` value when true. When `market_session != "regular"`, `/networth` reports both regular-close (anchoring doctrine) and extended-hours-last (anchoring reaction).

The ZoneInfo-aware session detection matters because yfinance returns UTC timestamps; the market clock is in `America/New_York` with DST transitions twice a year. A naive `datetime.utcnow()` comparison would misclassify the session in March + November weeks. The implementation reads `zoneinfo.ZoneInfo("America/New_York")` and computes session boundaries explicitly.

`AH_MOVER_THRESHOLD_PCT` is a module-level constant defaulting to 3.0. When `abs(extended_hours_change_pct) >= AH_MOVER_THRESHOLD_PCT`, the ticker is added to an `ExtendedHoursMovers[]` aggregation that downstream consumers (`/brief`, `/invest --refresh`) read as a "trigger flag" signal. The threshold is configurable so consumers with different signal-to-noise tolerances can adjust without rewriting the fetcher.

## The diffusion

This is a two-layer additive change. The data layer is `fetch-prices.py`; the contract layer is the per-skill consumer of price data.

`/networth` Phase 2 (portfolio snapshot composition) adds a conditional read: when `market_session != "regular"`, the snapshot row gets an extra column "EH" populated with the change_pct + last_timestamp. The existing portfolio-math column stays anchored to regular-close. Doctrine compliance verdict (doctrine-template ceilings) reads from regular-close, unchanged.

`/brief` Phase D (portfolio movers section) gains an `ExtendedHoursMovers` subsection rendered only when the aggregation is non-empty. The render is conditional, so the morning brief on a quiet weekend (no AH moves crossing 3.0%) looks byte-identical to the prior version. When the aggregation has entries, the section appears with movers listed by absolute change_pct descending.

`/invest --refresh <analysis-path>` Phase J.5 (prior-research drift detection) gains a 4th drift type: "AH-supersede" -- triggered when extended_hours_change_pct since the analysis was last refreshed exceeds 5.0% (a higher threshold than `/brief`'s 3.0% because `/invest` runs less frequently and warrants a more decisive signal). This populates the analysis's Inconsistency Log with a dated entry.

In all three consumers, the change is additive: an optional read of the new fields gated on a new condition, with the existing read path unchanged when the gate is closed. No signature changes. No breaking changes to downstream callers of `/networth`, `/brief`, `/invest`.

## The non-regression discipline

Three layers of non-regression invariant ran in parallel during the mission.

**Layer 1: capability baseline JSON diff with semver classification.** Before the mission started, a snapshot of the vault's capability surface was captured to `capability-baseline-pre.json`: `skills_count`, `agents_count`, `hooks_count`, `ref_docs_count`, audit-classifier count, prevention-dimension count, and the per-skill phase-count for `/networth` + `/brief` + `/invest`. After the mission, `capability-baseline-post.json` was generated by re-running the same enumerators. The `diff-baseline.py` script compared the two and emitted `PASS:` only if the diff was additive-only (existing dimensions unchanged; new dimensions optional). The Mission Three diff added six new dimensions (the new price-fetcher fields) and modified zero existing -- additive-only by construction.

**Layer 2: structure smoke test.** Before-state and after-state trees of the source vault were captured via `Get-ChildItem -Recurse -Depth 4`. The `diff-tree.py` script compared them, with an EXPECTED_MISSING + EXPECTED_ADDED envelope encoding the legitimate-change frontier (added: tools/lib/extended_hours.py if extracted, modified: tools/fetch-prices.py; removed: nothing). Any path outside the envelope failed the layer.

**Layer 3: regression check against Mission Two hook surface.** Mission Two had codified the F11-RE-SET-PER-INVOCATION anti-pattern detector inside `lib/f11_orchestrator.py`. The Mission Three change touched `fetch-prices.py` (not orchestrator-shaped), but the regression check ran the prior test suite (`test-prevention-arch.sh` 750-line bash suite) end-to-end to confirm F11 invariant held across `/networth` + `/brief` + `/invest` post-change. All 50+ assertions held.

Final tally: 127 additive entries across data, contract, and consumer-skill layers. Zero removals. Zero regressions. Wall clock 39 minutes from start to atomic commit.

## What broke and what didn't

`/invest` had a doc-code drift surface during the diffusion. The skill body documented "Phase J price-fetcher dispatch -- uses fetch-prices.py for current price + 52-week range" but the actual implementation went directly to WebSearch + parsing the Yahoo Finance HTML. The doc said dispatch; the body did fetch. This was a latent bug -- Phase J was running stale data 7+ days when the WebSearch fell through to cached HTML -- not introduced by Mission Three but surfaced because the Mission Three diffusion would have wired the new fields through Phase J only if the existing dispatch were already in place.

The decision: do not retrofit Phase J during Mission Three. The non-regression discipline says "additive-only"; fixing a latent bug is not additive. The drift surfaced was logged to a Mission Four-bis queue (separate mission, separate scope) and Phase J was explicitly excluded from the diffusion. The Inconsistency Log for `/invest` got a new dated entry: "Phase J price-fetcher dispatch documented but not wired; defer to Mission Four-bis."

This is the discipline: surface what breaks, exclude it from the active mission, queue it for the next mission. Don't try to fix everything at once when the constraint is additive-only. The cost of expanding scope mid-mission is non-linear -- you start introducing regressions because the additional changes lack the non-regression coverage that drove the original three-layer invariant.

## The pattern

`TWO-CALL-MERGE-FOR-PRESERVE-COMPUTE-STABILITY` is the codified pattern. The shape: when an architectural change needs to add a new compute path that cannot disturb an existing compute path that downstream consumers depend on byte-equivalently, split the calls. The first call preserves existing behavior verbatim. The second call adds new fields. Merge into a single return. Consumers opt-in to the new fields conditionally; existing consumers see no signature change.

This is generalizable beyond price-fetching. Any time a data layer needs to be extended without disturbing the existing contract, the pattern applies. Examples that came up in the months since Mission Three:

- Adding a second `/invest` source-aggregator pass (Phase E.2) that runs in parallel with the existing Phase E, merging into a single sources_count field without changing Phase E's behavior.
- Extending the entity-note schema with an `Inconsistency Log` section in Phase L UPDATE without disturbing the existing five-section claim-to-section mapping.
- Adding a hot.md "X-Y day delta" overlay without changing hot.md's existing single-line-per-thesis schema.

The pattern's tension is the same in every case: the existing compute path is correct, valued, and consumed by N downstream callers. The new compute path is needed but distinct. Either you fork the call sites (expensive, signature drift, brittle), or you preserve the existing path verbatim and add a parallel one (additive, signature-stable, idempotent). The two-call-merge says: do the second thing.

## The why-not

The natural alternative is to push the new fields into the same yfinance call by changing the period + interval parameters. This produces a single call with a richer dataset, which is theoretically more efficient. It also breaks the byte-equivalence of the 1y/1d call. The 1y/1d call's return shape encodes the regular_market_close field at a specific index, and the alternative parameters return a different shape -- which means every downstream consumer would need to be re-tested for byte-equivalence in their compute paths. The two-call merge sidesteps this by keeping the byte-equivalent call as-is. The cost is one additional network round-trip per ticker. The savings is no regression testing on the unchanged compute paths.

The single-call alternative also has worse failure modes. If yfinance returns a partial response for the combined parameters (a common failure mode under rate limiting), the consumer can't tell whether the regular-session subset is intact. The two-call merge separates these concerns: the first call's success/failure is independent of the second's, and downstream consumers can degrade gracefully -- showing regular-session data with a "EH unavailable" note instead of a hard error.

## Velocity

Mission Three's 7.7x manual-velocity equivalent (39 min vs. estimated 5 hours of manual change-implementation-test-verification cycle) came from three factors. First, the additive-only constraint made the change scope-bounded; there was no "while we're in there" temptation. Second, the three-layer non-regression discipline ran in parallel with the implementation, not after it -- the capability baseline, structure diff, and Mission Two regression check were all `PASS:`-line outputs the agent emitted as it progressed, so the closure verdict was already accumulating before the atomic commit. Third, the surfaced doc-code drift on `/invest` Phase J was handled by deferral rather than expansion -- the mission did not try to fix the latent bug because doing so would have violated additive-only.

The leverage was in the discipline, not the cleverness. A two-call merge is not a clever architecture; it's a boring one. The win is in the velocity at which the boring architecture ships without regression.
