# Session capabilities and complete financial briefs

The current user request and root contract govern authorization. A tool binding
is a routing observation; it is not an account read, authorization or successful
workflow. Production roles inherit authorized session settings. Fixed evaluation
model and effort settings remain fixed in their separate evaluation protocol.

## Resolve capabilities before acquiring data

Use the actual session tool inventory. `tools/fis/capabilities.py` maps exact
trusted names to financial read capabilities across Codex app and direct MCP
namespaces. It accepts only a bounded list of names, never tool responses or
account identifiers. Persist only this public metadata if a receipt is useful:

`python tools/fis/capabilities.py <tool-names.json> --require equity_quotes`

An ambiguous capability requires selection of the intended connector; a missing
capability stays unavailable. Inspect each selected schema for arguments, response
shape, units, delays and pagination. Direct MCP registration and Codex app
registration are separate. Do not transfer permissions or cached authorization
between them. Workers without connector access return a scoped request to the
parent; they do not substitute old account files or widen their tool grants.

For portfolio reads, establish the intended accounts using the session request
and connector rules. `account_number` and numeric `rhs_account_number` are distinct
identifiers in current the broker schemas; crypto needs the latter. Do not choose
an arbitrary first account. Reconcile equity, option and crypto positions, cash,
liabilities and totals within the selected population. Buying power can include
margin and must not be called cash. A closed option position must not enter open
risk; use the schema's open-position filter and complete pagination.

Use supported public fundamentals, financial statements, filing indexes/facts,
quotes, histories and screening fields when useful. Filing facts still need
filing-specific label, unit, period and amendment checks. Financial statement
coverage, custom taxonomy coverage and market history depth are separate claims.
For equity quotes requiring dated official closes, current Codex the broker batches
must contain <=20 symbols. Preserve dated close objects and per-symbol errors.

Finances owns its available household account reads, Data owns supported rendering
and analysis tools. Observe availability separately in each host. Never invent
missing account tools, silently export personal data to another host, or infer
live verification from installed plugin metadata or a portable package.

## Portfolio brief completion order

1. Establish the question, horizon, objectives, liquidity needs and relevant
   account constraints from authorized current preferences. Mark consequential
   missing constraints and ask only for information needed for the affected
   decision. Never invent taxes, return targets or risk tolerance.
2. Acquire and reconcile current authorized evidence. Separate supported
   subquestions from missing account or instrument coverage. Household and
   brokerage feeds can overlap; reconcile transfers and avoid double counting.
3. Retrieve passages needed for methods, prior decisions and disconfirmation.
   Use admitted public spans and their exact versions; original inspection and
   current applicability are separate from synthesis confidence. Missing originals,
   stale guidance or unavailable libraries are recorded limitations. Use the
   knowledge map when that suffices; retrieval volume is not a quality target.
4. Run the existing deterministic evidence, valuation, risk, allocation and
   reconciliation owners applicable to the question. Show a consistent simple
   alternative, including holding, with costs and constraints. Do not treat
   covariance, narrative probabilities or stop orders as calibrated loss protection.
5. Compute material reversal conditions and coupled scenarios, separating
   assumptions from calibrated forecasts. Apply existing action and doctrine gates.
   Review material BUY, HOLD and SELL conclusions equally.
6. Render useful tables/visuals with Data where supported. Review the actual final
   narrative, table labels, tooltips, meaningful filters and exports. Public and
   synthetic reports use the workbench's frozen review contract and financial
   consumer; schema validity alone cannot accept them. Keep failed reviews and
   disagreements. A changed delivered artifact needs a new review.

Complete relevant analysis and review before delivering the portfolio brief.
Answer supported portions even when other decisions must remain withheld. State
whether review was independently executed, manually performed or unavailable;
never describe an unexecuted review adapter as successful.

Personal financial inputs and review remain inside the authorized host. The
public/synthetic native-review runner rejects personal classifications. No raw
responses, amounts, identifiers, transaction descriptions or revealing hashes go
into the vault, public review archive, portable package or hosted evaluator.
Persist only a non-sensitive process record when the workflow calls for a vault
note; the actual personal brief stays in its authorized session. Account-scope
metadata that could identify the user is personal too.
