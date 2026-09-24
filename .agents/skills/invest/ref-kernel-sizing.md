# ref-kernel-sizing -- INVEST KERNEL position-sizing forms (K-bis.7 + D.8)

Read-on-demand companion to /invest SKILL.md (same pattern as ref-dw-topology).
Owns: the KERNEL RUN CARD, the sizing worksheet form + fill rules, the golden
worked example, the override-lane procedure, failure modes, and the
gate/staircase reconciliation map. AUTHORITATIVE numbers live in the two
doctrine machine blocks (`doctrine:` in `Atlas/sources/investing/ref-portfolio-doctrine.md`,
`bands:` in `Atlas/sources/investing/ref-scoring-models.md`) -- this file never
restates a threshold as authority, only as illustration. Built 2026-07-06
(Fable 5 final session); ratified by decision-invest-kernel-doctrine-2026-07-06.
Deployment layer rewritten 2026-07-30 (Pillar 1: 10Y-LEVEL gate retired, VIX
halt converted to a throttle, reserve made releasable) per
decision-invest-rate-gate-retire-2026-07-30.

---

## KERNEL RUN CARD (page 1 -- execute in order; paste the completion table into Phase P)

The executor's contract: fill forms, run commands, transcribe outputs
VERBATIM. Never compute sizing arithmetic by hand; never edit a number the
script produced; if a check fails, fix the INPUTS and re-run `--compute`.

| # | When | Command | Expect |
|---|---|---|---|
| K1 | Phase D.8 (every run) | `python <VAULT_ROOT>/tools/doctrine-lint.py --json` | exit 0. Exit 2 -> HALT the run, clear F11 (zero writes yet), report findings verbatim |
| K2 | Phase D.8 | Record from lint inputs: `doctrine_version` (pd-2/fb-1 style) + `doctrine_fingerprint` (`python <VAULT_ROOT>/tools/doctrine-lint.py --fingerprint`) | both stamped into analysis frontmatter later |
| K3 | Phase J (both tiers) | Build the trusted book snapshot JSON from live MCP positions (same format `tools/pretrade_gate.py` consumes: `total_value`, `positions[{symbol,value,thesis}]` incl. a CASH row, `prices`, `thesis_map`, `as_of_utc`) | saved to the scratchpad; path noted |
| K4 | K-bis.7 | Fill the inputs JSON form (below) -- every field `{value, prov}`, prov non-empty | saved to the scratchpad |
| K5 | K-bis.7 | `python <VAULT_ROOT>/tools/sizing-eval.py --compute --mode add --inputs <inputs.json> --book <book.json> --worksheet-out <ws.md>` (mode `hold-state` for held non-BUY names) | exit 0; paste the emitted worksheet (block + rendered lines) VERBATIM into the analysis after the Decision Sheet |
| K6 | K-bis.7 | Set the TRADING DECISION `**Action**` dollar amount EXACTLY to the worksheet `final_dollars` | equality is script-enforced at K7 |
| K7 | Pre-Output 10b (before Phase O.0 skill-precheck) | `python <VAULT_ROOT>/tools/sizing-eval.py --check <composed-analysis-tmp.md>` | exit 0. Exit 2 -> fix inputs, re-run K5, replace the WHOLE worksheet; hand-editing individual numbers is FORBIDDEN |
| K8 | Phase P | Paste this completion table with actual exit codes + artifact paths | audit trail |

WORKSHEET FIRES: BINDING mode iff rating is BUY/STRONG BUY with an
Initiate/Add action; HOLD-STATE mode for any HELD name at any other rating;
SKIPPED for non-held HOLD/SELL/AVOID (note the skip in Phase P).

On TRIM/EXIT of a held name, the tax-lot pass (ref-analysis-template Section
2.11; Pre-Output 10f) informs WHICH lots to name -- it never changes the
worksheet math. INVARIANT (2026-07-11, source-verified): K.5 conviction
modulation changes the reported Conviction % and nothing else mechanical --
the Kelly win-probability is keyed on rating + R/R bracket (kernel_lib
pick_win_prob), never on conviction; `final_dollars` and the Action amount
never read conviction.

## Deployment layer in one paragraph (what changed 2026-07-30)

There is no 10Y-LEVEL band any more. Default deployment is 1.0. Two conditions
throttle it and their multipliers combine by MIN, never by product: a DFII10
real-yield SHOCK (rise over a 60-obs lookback, CONFIRMED by a nominal DGS10
rise over the same window, entered on 3 consecutive fire sessions and exited
below the hysteresis floor) at 0.5x, and a VIX THROTTLE at 0.5x. A VIX TAIL
HALT is the only absolute 0.0x. Unreadable VIX is `unknown-treated-halted` at
0.0x and is the ONLY state the override lane can never pierce; unreadable
DFII10 is `rate-unknown-caution` at 0.5x. The script reports a distinct reason
code for every one of these -- three different states used to read "0.5" and
now they never do.

## Inputs form (mode add) -- field by field

Every field is `{"value": ..., "prov": "..."}`. Fill rules:

| Field | Fill rule |
|---|---|
| symbol | uppercased ticker |
| rating | K-bis.5 Step-1 rating VERBATIM (BUY / STRONG BUY only in add mode) |
| entry | regular_market_close used for all threshold math (J.0b); prov `mcp:robinhood:*` or `script:*` |
| stop | a price level; MUST equal a quantified kill-criterion price where one exists; distance 5-25% of entry (script-enforced) |
| stop_basis | enum: `kill-criterion-price` \| `technical-support-200dma` \| `dated-swing-low` |
| target_model | the analysis's own target (valuation method per ref-valuation-methodology) |
| target_basis | enum: `min-analyst-median-vs-model` \| `valuation-fair-value` \| `multiple-reversion` |
| target_analyst_median | analyst consensus median PT with source; `null` value + prov note if genuinely unavailable. The script sizes on MIN(target_model, this) -- anti target-inflation |
| account | the configured account key holding the position (e.g. taxable or tax-advantaged); user-specified for new names |
| account_cash | That account's cash from a successful current-session broker read whose observed schema actually supplies cash; missing fields remain UNVERIFIED |
| cash_reserve | REQUIRED when the account carries a ratified cash reserve: dated earmark from permitted doctrine/session instructions, separate from broker-verified cash. Never read *.local.md; unresolved reserve blocks dependent sizing, not an assumed zero. The script nets it UNLESS a release condition fires (below) |
| is_crypto | Phase E identity |
| scoring_path | from K-bis routing (`negative-eps-bridge` triggers the x0.5 haircut) |
| corr_gt_threshold_flag | true iff Phase J flagged pairwise correlation >0.7 with an existing holding |
| thesis_list | entity frontmatter `thesis:` list (ALL memberships -- the script takes MIN headroom) |
| effective_thesis_pct | per-thesis EFFECTIVE % (ETF look-through, /networth method); script refuses values below the book-strict % |
| **dfii10_series** | **THE GATING SERIES.** Pull ~90 published obs `[{date, value}]` (60-obs lookback + ~30 sessions of hysteresis reconstruction). HARD MINIMUM 61 obs; below that the leg is unresolvable and fails closed to 0.5. Ladder: `mcp:fred:DFII10` -> `script:` keyless curl `https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFII10`. The old briefing-meta.json rung is RETIRED (MIN-2: one cached scalar cannot satisfy a multi-obs rule). Non-mcp/script prov caps the multiplier at 0.5 |
| dgs10_series | DEMOTED to a screen + disclosure + Rf input; it is NOT a gate. Pull the SAME window as dfii10_series (~90 obs) so the nominal-confirm screen can be evaluated at every reconstructed session; also the source of the smoothed 63-session Rf. Same ladder (`DGS10`) |
| vix_series | last 5 obs; same ladder (`VIXCLS`). This is the ONLY series whose absence halts absolutely |
| rate_prov | the prov of dfii10_series (duplicated for the trust check; the loader overwrites it from the series prov either way) |
| dgs10_prov | the prov of dgs10_series (same pattern) |
| **spx_close** | S&P 500 REGULAR close (`mcp:fred:SP500` or `script:fredgraph-csv`) -- reserve-release input |
| **spx_trailing_high** | max regular close over the trailing 252 sessions, same series -- reserve-release input |
| **theme_alpha_eff_pct** | effective theme-alpha concentration % of book (/networth method, same number Phase Q uses) -- reserve-release input |
| override | `{invoked, forensic_clean, gate_f_verdict, user_directive}` -- see the override procedure below |

A missing reserve-release input is NOT a failure: the condition evaluates
`unknown` and does NOT release (release is the risk-increasing direction). It
IS a disclosure defect -- the worksheet prints `unknown` and a reader can see
you did not look.

The script computes: the deployment state + every reason code from the RAW
series (never asserted by the model), the reserve-release evaluation with
per-condition inputs and provenance, name/thesis exposure from the book (never
hand-summed), Half-Kelly both algebraic forms, the W1-W8 waterfall, and the
final size.

## Override-lane procedure (D5; never self-invoked) -- TWO-TIER RULE

1. Every BINDING worksheet REPORTS availability: `N/5 conditions met`
   (observable sub-1.0 state; R/R >= the doctrine floor; forensic clean --
   red-band keys in the `bands:` block, N/A counts as NOT clean so crypto is
   ineligible; GATE-F DISCIPLINED; all headrooms positive).
2. **TIER 1 -- PIERCEABLE: any OBSERVABLE sub-1.0 state**, i.e.
   `rate-shock-caution`, `rate-unknown-caution`, `vix-throttle`, `prov-capped`,
   AND `halt-vix-tail`. One tranche size serves all of them: 25% of the
   computed W6 size. There is no separate halt tranche and there never will be
   -- the proposed 10% halt tranche was arithmetically dead (5% tranche cap x
   10% = 0.5% of book, below the 1% de-minimis floor, so every lawful pierce
   would have returned NO-TRADE while recording `override_used: true`).
   `tools/test-sizing-eval.py` T3b asserts a lawful pierce produces a
   TRADEABLE order at live book size; T3c asserts the 10% counterfactual does
   not.
3. **TIER 2 -- NEVER PIERCEABLE: `unknown-treated-halted`.** An unobservable
   state is not a risk judgment, it is an absence of information, and
   conviction cannot pierce an absence. The script refuses (OVERRIDE-UNLAWFUL).
4. INVOKING the lane requires an EXPLICIT USER DIRECTIVE in the current
   session, quoted verbatim in `override.user_directive`. Absent directive ->
   the script refuses. The model NEVER self-invokes.
5. The GATE-F sheet (which produced the DISCIPLINED verdict) + the analysis
   `thesis_line` must state the macro gate is being pierced and why.
6. Same-family caps take MIN, never stack: a GATE-F re-gate tranche-cap-25pct
   and the override 25% resolve to 25%, not 6.25%.
7. Measurability: `deployment_override: true` lands in the analysis
   frontmatter (journal.base column) + the GATE-F registry row; the
   2026-10-06 doctrine review counts uses and abuses. The lane now applies in
   strictly MORE states than before, so that count matters more than it did.

## Golden worked example

Withheld from the public copy: the worked example was regenerated from a real run against the author's own book, and its inputs and outputs are his portfolio figures. The form of the calculation is documented in the sections above.


## Failure modes

| Symptom | Meaning | Recovery |
|---|---|---|
| doctrine-lint exit 2 at D.8 | doctrine blocks corrupted / edited without ratification | HALT the run, CLEAR F11 (zero writes yet -- unlike N.halt), surface findings; a human fixes the note or ratifies via /decide |
| `HURDLE-FAIL` | R/R below the rating's hurdle at the MIN-rule sizing target | the rating should not have been BUY at this bracket -- re-check K-bis.5, do not massage the target |
| `STOP-BAND-FAIL` | stop <5% or >25% from entry | pick a defensible stop basis; do not tune the stop to pass Kelly |
| `OVERRIDE-UNLAWFUL` | an override condition is unmet, the state is unknown-treated-halted, or no verbatim directive | report availability honestly; never re-fill markers to force it |
| state `rate-unknown-caution` | DFII10 short (<61 obs), stale (> obs_max_age_days), or a would-be fire whose DGS10 confirm screen has no data | this is an ACQUISITION bug far more often than a market state. Re-pull ~90 obs of DFII10 AND DGS10 over the same window before accepting the 0.5x |
| state `unknown-treated-halted` | VIX series short or stale | re-pull VIXCLS. Nothing pierces this state; a run that cannot read VIX cannot size |
| state `prov-capped` | the rate series came from neither mcp: nor script: | re-pull from the ladder. A web-sourced yield never earns full deployment |
| verdict NO-TRADE, reason_code `caution-collapsed-de-minimis` | a 0.5x throttle silently became a 0.0x because the halved size fell under the 1% floor (red-team MAJ-6) | transcribe it AS THAT CODE. It is materially different from a plain de-minimis and from a halt, and the 2026-10-06 review counts it |
| `Reserve release: ... spx-drawdown=unknown` | a release input was not filled | fill spx_close / spx_trailing_high / theme_alpha_eff_pct and re-run. The reserve stayed on, so the number is conservative, but the disclosure is incomplete |
| `--check` exit 2 on 10b | worksheet numbers diverge from recompute, Action != final, or kernel frontmatter missing | re-run `--compute`, replace the WHOLE worksheet block, fix frontmatter; hand-editing numbers is the failure mode this kit exists to stop |
| worksheet fingerprint != live | doctrine changed between compute and check | recompute under the current doctrine |

## Gate / staircase reconciliation map (what the kernel emits -> who consumes)

| Kernel output | Consumer | Contract |
|---|---|---|
| `gate_f:` frontmatter + same-day GATE-F sheet | /gate registry + Pre-Output 10a + calibrate lane | GATE-F runs BETWEEN K-bis.5 (rating known) and K-bis.7 (sizing needs the verdict) whenever the rating is an action verdict OR the override lane is evaluated |
| analysis file dates | GATE-F `prior_analysis_days` marker | an in-flight /invest counts as 0 |
| `kill_criteria:` frontmatter | GATE-T evidence; thesis `triggers:` blocks | kernel NEVER writes thesis files (Pattern 20); the sizing stop SHOULD equal a kill-criterion price |
| `deployment_band:` frontmatter (`<state>:<multiplier>`) | journal.base column + the 2026-10-06 review + /brief | the reason code is the audit unit, not the multiplier -- three states share 0.5 and must stay distinguishable downstream |
| `reserve_release` worksheet stamp | the 2026-10-06 review + /networth reserve narrative | every release is dated, condition-attributed, and input-disclosed |
| rating + Action $ + worksheet final shares | human stages `staged-order.json` -> `tools/pretrade_gate.py` (T11 stair 1) -> `EXECUTE ORDER` token hook (stair 2) | the kernel does NOT emit staged orders; the worksheet is the sizing evidence the human transcribes. SAME trusted book-snapshot format on both sides |
| `deployment_override: true` + verbatim directive | GATE-F sheet body + gates-registry outcome + journal.base column | 2026-10-06 review counts usage/abuse |
| calibration-monitor row (Phase R, unchanged schema) | tools/score-outcomes.py | byte-stable |
| INGEST:claims 8-tuple block (unchanged) | /ingest | untouched by the kernel |

DOCUMENTED DIVERGENCE (not fixed here; needs a /decide): the T11 execution
stair uses thesis amber 40 / red 50 (`tools/pretrade_lib.py` -- deliberately
tighter, riding the interim-50 as its red), while portfolio doctrine is
60/70 with interim amber 50. Generation-side sizing (this kernel) uses the
doctrine block; execution-side blocking keeps its own ratified constants.
A future /decide should either unify them or ratify the two-layer split
explicitly.

SECOND DOCUMENTED DIVERGENCE (2026-07-30): `tools/pretrade_lib.py` has no
knowledge of the reserve-release lane. If a release fires and the human stages
an order that spends released reserve cash, the execution stair evaluates it on
its own constants. That is acceptable (the stair is a blocking layer, not a
sizing layer) but it means a released reserve is NOT double-checked at
execution. Named here so the 2026-10-06 review can decide whether it should be.

## Related

`Atlas/sources/investing/ref-portfolio-doctrine.md` (doctrine block) |
`Atlas/sources/investing/ref-scoring-models.md` (bands block) |
`Calendar/decisions/decision-invest-kernel-doctrine-2026-07-06.md` |
`Calendar/decisions/decision-invest-rate-gate-retire-2026-07-30.md` |
`wiki/research/redteam-invest-overhaul-2026-07-30.md` |
`tools/kernel_lib.py` | `tools/sizing-eval.py` | `tools/doctrine-lint.py` |
`tools/test-sizing-eval.py`
