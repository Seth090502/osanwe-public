# Porting brief: pretrade-gate CLI (execution-time doctrine gate)

COLD BRIEF -- written without sight of the manifest test blocks; the executable `test:` in
`.agents/hooks/manifest.yaml` is the acceptance criterion, not this prose. Criticality: SAFETY-CRITICAL
(money-adjacent). Portable: YES as a CLI -- but read (e) first: off-Claude it is ANALYSIS TOOLING,
never an authorization path.

## (a) What the gate must guarantee

Given a staged order and a snapshot of the LIVE book, return PASS or BLOCK against machine-readable
doctrine, fail-closed. It answers "may this specific order execute right now"; gate-eval's GATE-F
answers "should this trade be proposed at all". Blocking conditions (any one => BLOCK): schema-invalid
staged order, or an untrustworthy / stale book; post-trade thesis concentration >= 50% RED (40% amber
= warning only); post-trade single-name >= 35% RED (30% amber); BUY with reward/risk < 3.0; sleep gate
active, or a BUY without an explicit rested-state attestation; economically implausible size (BUY
notional > total book, SELL > held value); declared notional inconsistent with quantity x trusted price
beyond 5%. On PASS it writes an HMAC-signed pass artifact; on BLOCK it writes NO valid pass, so a
blocked order can never satisfy the downstream Claude-side token hook.

## (b) Reference implementation + load-bearing facts

Reference: `tools/pretrade_gate.py` (344 lines) + `tools/pretrade_lib.py` (shared constants, schema
validation, canonicalization, HMAC). Cross-harness entry point `.agents/scripts/gates/pretrade-gate.py`
resolves the repo root from its own location, sets `VAULT_ROOT` if unset, delegates argv. Stdlib only.

1. THE BOOK COMES FROM `--book`, ALWAYS. An order-embedded `book_snapshot` is attacker-controllable and
   is NEVER consulted -- there is deliberately no code path that sizes concentration off an
   order-carried book. Omitting `--book` is an error, not a fallback to the embedded one. (Red-team
   rounds 4-5, A4: a forged book with an inflated total deflates every concentration ratio.)
2. THE BOOK DECIDES THE THESIS AND THE PRICE, NOT THE ORDER. A held symbol's thesis comes from the
   book's positions/thesis map; a declared thesis that disagrees is a BLOCK (mislabel). Notional is
   `quantity x TRUSTED BOOK PRICE`, never an order-carried number; the order's `estimated_notional` is
   advisory and must agree within 5% or the order is lying about its size -> BLOCK. (Round-1 A2.)
3. RED CEILINGS ARE INCLUSIVE: `>=` on 50% thesis and 35% single-name -- landing exactly ON the red line
   is a breach. Amber (40% / 30%) produces warnings that do NOT block. Off-by-one here is the single
   most likely port defect; test the boundary explicitly.
4. FINITENESS IS CHECKED ON DERIVED VALUES, NOT JUST INPUTS: a finite-but-huge quantity can overflow
   `quantity * price` to infinity, which floors every downstream ratio, so the derived notional must
   itself be finite and > 0 (round-2 A4). SELLs are separately capped against held value, because a
   SELL floors post-trade concentration to zero. FRESHNESS IS A HARD GATE: `as_of_utc` must parse;
   older than 24h -> BLOCK; older than 30 min -> amber warning; >300s in the future -> BLOCK.
5. EXIT CODES: **0 = PASS, 1 = BLOCK, 2 = usage/IO error**. Two is fail-closed and must be TREATED AS
   BLOCK by every caller. This differs from gate-eval (where 2 means FAIL) -- do not unify them.
6. THE PASS ARTIFACT IS THE OUTPUT THAT MATTERS. Default TTL 900s; it binds `order_id`, a canonical
   `order_hash`, `passed_utc`, `ttl_sec`, `gate_result`, and an HMAC signature keyed by
   `.claude/state/pretrade/hmac.key` (32 random bytes, mode 0600, gitignored). `--no-issue` evaluates
   without writing one; `OSANWE_PRETRADE_STATE_DIR` relocates all state for tests.

## (c) Where to bind it

Not a lifecycle hook -- a CLI: `python .agents/scripts/gates/pretrade-gate.py <staged-order.json>
--book <book.json> [--json] [--no-issue]`. Binding on Claude Code is by construction: the PreToolUse
token hook refuses any order lacking a fresh signed pass, so the gate is unskippable. On every other
harness there is no such binding and none should be manufactured (see (e)). If a harness wants a
mechanical checkpoint, bind at `pre-tool-use (blocking)` per `.agents/hooks/README.md` ONLY for
staged-order FILE writes (refuse writing a staged order that does not evaluate PASS) -- never as an
execution authorization.

## (d) Input shape

Two JSON files on argv. Staged order: at minimum `order_id` (6-64 chars of `[A-Za-z0-9._:-]`), `symbol`
(uppercase, <= 12 chars), `side` in {buy, sell}, `quantity` (> 0, finite), `order_type` in {market,
limit}, `account` (one of the book's configured account keys, e.g. taxable or tax-advantaged), `thesis`, `risk_reward` (finite), `estimated_notional` (> 0,
finite), and for BUYs `sleep_gate_ack: true`. Book snapshot: `as_of_utc` (ISO), a portfolio total,
`positions` (each with symbol, value, thesis), and a price map -- in production the main loop populates
it from READ-ONLY broker MCP calls (positions / portfolio / quotes) before invoking. Output: PASS/BLOCK
with reasons, warnings, and a metrics block (total value, trusted price, effective vs declared
notional, current and post-trade symbol and thesis percentages); `--json` for machine consumption.

## (e) Non-goals and known residuals

- THIS SCRIPT NEVER PLACES AN ORDER and never calls a brokerage endpoint: it reads two files and
  writes at most one pass artifact. OFF-CLAUDE IT IS NOT AN AUTHORIZATION PATH. The companion token hook is `portable: NO`
  (`briefs/pretrade-token-gate.md`), and non-Claude harnesses are never given order tools at all -- a
  PASS produced under Codex/OpenCode/Goose/Crush/Cline authorizes nothing. Treat it as dry-run and
  analysis tooling; never build a harness-side executor that consumes these passes.
- It does not evaluate FOMO/behavioral discipline (gate-eval GATE-F) and does not lint doctrine values.
  The ceilings it enforces are constants in `pretrade_lib.py`; doctrine-lint keeps those in agreement
  with the ratified ref-notes. The theme-alpha interim-50 phase-in is folded into the 50% thesis RED
  constant today -- parameterize such constants in a port, never hardcode them in the port's tests.
