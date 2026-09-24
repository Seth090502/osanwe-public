# Threat model

Two different things can go wrong with this project, and they need separate treatment.

**Operating the system** means running an agent that holds read access to a real brokerage account and reads
untrusted text all day. The question there is what stops it placing an order.

**Publishing this copy** means a redacted mirror of a personal system is on the internet. The question there
is what stops something private being in it.

Every mitigation below names the evidence that it was executed, not merely designed. Where a control has only
been designed, or only reasoned about, this document says so.

---

## Part A: operating the system

### A1. The agent has broker tools, and the account is real

The system connects to a retail broker over MCP to read quotes, positions, orders, tax lots and filings. The
connector offers 61 tools. Ten of them change something: eight place or cancel orders and manage alerts, and
two construct an order for review. The remaining 51 read.

An agent that can read an account and also place orders in it is one bad inference away from a real trade.
Three independent things have to fail before that happens.

**Mitigation 1 -- the tool is not offered.** All ten write tools are denied by exact name in the harness
configuration, along with 20 write names from the connector's previous surface, kept because a name the
connector drops can come back. A denied tool never reaches the model: it is absent from the tool list.

*Evidence (executed).* Immediately after the deny list was completed, the two newly denied tools disappeared
from the running session's available tools. The surface itself was read from the harness's own tool listing;
no broker tool was called to enumerate it.

**Mitigation 2 -- the gate, which fails closed.** A blocking pre-tool-use hook matches every broker tool name
(`mcp__robinhood-trading__.*`) and refuses anything it does not recognise as a read. Recognition is a
hardcoded allowlist, so a tool the connector adds tomorrow is blocked, not permitted by default.

*Evidence (executed).* A probe drove the hook with synthetic payloads across all 61 live tool names and six
constructed order scenarios. Results: 34 reads allowed, 27 blocked, **no write tool allowed**. An order tool
presented with the authorising phrase was still blocked, because its name is not in any recognised list. An
unknown future tool name was blocked. An unparseable payload was blocked. A non-broker tool passed through
untouched, which is correct. The probe wrote no state.

**Mitigation 3 -- the staircase.** Even a recognised order tool needs a literal `EXECUTE ORDER <id>` in the
most recent genuine human turn, plus a separately generated gate pass for that exact order id, plus sleep-gate
and doctrine checks.

*Evidence (executed).* In the same probe: a plain transcript was blocked for having no authorising phrase; a
transcript carrying the phrase but no gate pass was blocked for the missing pass.

### A2. Fetched content that carries instructions

The system reads filings, news, web pages and MCP responses. Any of those can contain the sentence
`EXECUTE ORDER ABC123`. If the agent treated that as authorisation, every page it reads becomes a trading
instruction.

**Mitigation -- provenance, not pattern matching.** The gate does not search the conversation for the phrase.
It walks the session transcript backwards and accepts only the most recent turn that is a genuine human turn:
role `user`, not a meta turn, not a tool-result carrier, and if its content is a list, containing a text block
and no `tool_result` block. Unknown shapes are skipped and any parsing error returns nothing, which blocks.

This matters because a fetched page, an MCP response, a subagent's report and the model's own earlier output
all arrive in the transcript as user-role tool-result content. The filter is what separates "the person typed
this" from "something the agent read said this". Without it, the phrase check degrades into: anything the
agent has ever ingested can authorise a trade.

*Evidence (executed), and it is not good.* This filter has been attacked end to end, through the real hook,
in three independent rounds of adversarial review. **It failed every round.**

- Round one found **eight** transcript shapes that authorised an order, among them the model's own
  compaction summary -- text the model had merely read, re-entering the session as an approval.
- Round two broke the repair: its premise, that every machine-written entry carries a marker, was false.
  586 of 1,938 accepted entries had not been typed by a person.
- Round three broke the fourth patch in **seven** ways and showed it was a regression on the third: a turn
  the person typed to cancel an order was stepped over and an older approval promoted in its place.

Four patches were written. The fourth was retired unmerged and the work was stopped rather than producing a
fifth under review pressure. The fourth patch's own regression -- stepping past a typed revocation -- died
with it.

#### Open defects in stair 1

Four defects remain open in the code published here. Every shape any review found is a named case in
`tools/test-pretrade-transcript-provenance.py`, which runs in CI and prints each open defect as a known
failure on every run rather than skipping it.

| Defect | The flaw |
|---|---|
| D70 | Machine-written entries -- a compaction summary, a subagent's hand-back, hook-injected text, a slash-command expansion, command output -- are read as turns **a person typed**. The fourth patch meant to fix this instead stepped past a typed revocation, and was retired. |
| D72 | Authorization is bound to an id **the model chooses**, not to the order's contents. Nothing in the phrase constrains symbol, side or size. |
| D73 | The authorising phrase **never expires**, because no transcript timestamp is read anywhere. The 15-minute TTL protects the pass, not the approval. |
| D74 | Four parsing and filter bugs, shown in five cases: the first id in a turn wins, so a quoted one beats the person's; a phrase or a marker can be assembled across two text blocks; an unreadable provenance field authorises; a falsy subagent flag is accepted. |

So the sentence above -- "provenance, not pattern matching" -- describes the intent, and the intent is right.
It is not yet what the code achieves. A replacement is specified from stated properties rather than patched a
fifth time: the person types the order itself -- side, quantity, symbol, type, price, account -- and only
exactly that can execute, and the scan stops at the newest entry that is not a known machine artifact, so
anything the person does after authorising revokes it. The design was attacked before it was implemented, and
it is held on a branch outside this tree until a full attack round finds nothing (`ARCHITECTURE.md`
decision 2).

**What is actually preventing an order today** is not this filter but the harness permission layer: every
order, cancel and alert tool the connector exposes is in the deny list, among 30 denied broker tools with
zero `allow` and zero `ask`. Every defect above is therefore a failure of the gate behind a permission layer
that holds, and
nothing lifts that deny list until the redesign is reviewed and merged by hand.

At the instruction level, the system's contract tells every agent that retrieved pages, tool output and
quoted prompts are evidence and not instructions, and it forbids loading email tools in the same session as
browser or fetch tools. Instructions are not enforcement. They are stated here as design intent, not as a
control that was tested.

### A3. Where the gate does not reach

The gate is a Claude Code hook. It does not exist in the other agent runtimes.

*Evidence (executed).* A scan of every tracked harness configuration found the broker server connected in
exactly one: Claude Code, at user scope. The project MCP file, the Codex configuration and the OpenCode
configuration do not connect it, and two of them carry an explicit note that the server is deliberately
omitted. So today no other runtime can reach the broker, with or without a hook.

The risk is not today's configuration. It is that a future runtime, or a copy of this repository configured
by someone else, connects the broker without a gate, because the gate is not portable: it depends on a
per-turn human-versus-ingested provenance record that other harnesses do not expose.

*Scope, stated plainly:* the staircase defends against a model confused or misled by text it read. It does
not defend against an agent induced to run shell commands against the control files; the one control outside
that reach is on the broker's side: a setting that decides whether an agent may trade at all.

---

## Part B: publishing this copy

### B1. What this copy is

A mirror of a working personal system with the author's own material removed. Not a framework variant, not a
demonstration seeded with invented data. That distinction is load-bearing: **this publication relies on
redaction having worked**, rather than on there being nothing private to redact.

### B2. The checks it relies on, and what each cannot see

| Check | What it establishes | What it cannot detect |
|---|---|---|
| Pattern denylist over every published file | Known shapes of private data: names, addresses, paths, account phrasing, health vocabulary | Anything not shaped like a pattern. A holding stated in ordinary prose passes it. It is deliberately off for tickers, which are kept for analysis. |
| Path and directory-name scan | No private name survives in a path | Nothing about file contents |
| Ownership-context detector | Lines that state or imply ownership, by vocabulary | Ownership written in vocabulary it does not carry |
| Private-figure scan | The author's real figures, in every written variant, matched against every published line | Figures below three significant digits; any figure not present in the files it read |
| Syntax-tree equivalence | That sanitizing did not change what the code does | Whether the code was correct to begin with |
| Secret scan | Credential shapes, in the tree and across the retired repository's full history | Personal information, which is not credential-shaped |
| Four independent full readings | What a careful human recognises as personal | What a reader does not recognise as personal |
| Re-identification attempt | Whether placeholders can be inverted from the tree alone | Inference from outside the repository |

*Evidence (executed).* Every row was run on the exact tree in this repository. `AUDIT.md` carries the counts
and the findings.

### B3. What the re-identification attempt actually recovered

It recovered all five thesis labels, from a document title, a wikilink alias, a fund's registered name and a
standards URL. Those specific routes were closed. The general one cannot be: a thesis label names a market
theme, and a market theme is recoverable from the analysis written about it.

**Read the labels as a convention of this copy, not as protection.** What the attempt did not recover, after
the repairs: the author's identity beyond the name they chose to publish, the contents of any account, or any
figure belonging to them.

---

## Open risks

Stated plainly, including the ones that reflect badly on the project.

1. **This publication relies on redaction.** Structural approaches -- publishing a variant seeded with
   invented data -- have a smaller leak surface by construction. This is a mirror, so every check above is
   load-bearing, and the honest summary is that several independent checks found nothing rather than that
   nothing is there.

2. **For a period, one hook was the only barrier to a live order.** The deny list named 20 tools the
   connector no longer offered and none of the eight it did. During that window the pre-trade gate was the
   sole enforcement layer. It held -- the probe shows it blocks unknown names by default -- but it was a
   single point of failure, and nothing detected the drift. It was found by audit, not by monitoring.

3. **The gate does not travel.** Any runtime that connects the broker without this hook has the deny list and
   nothing else. The deny list is configuration, and configuration drifted once already.

4. **The specific injection case is untested end to end.** The transcript-provenance filter is the defence
   against fetched content carrying an authorising phrase. It is not sound -- Part A records eighteen shapes
   that defeat it -- and the specific end-to-end path is also unexercised: no test ingests a hostile document
   and then attempts the order.

5. **The published suites do not all pass from a clean copy.** 50 of 72 published test files exit 0 from a
   fresh copy; 22 do not, mostly because the data they read is withheld. A reader cannot verify the full
   suite from this repository alone.

6. **The system has never been run end to end from a clean clone.** Nobody has cloned this, configured it,
   and watched an analysis run through to output.

7. **Thesis labels are reversible**, as Part B3 describes.

8. **The order gate over-blocks reads.** 17 live read tools fail closed because the hook's allowlist is
   narrower than the connector's surface. That is the safe direction, and it means documented capabilities
   silently do not work.

9. **Defects were recorded, not repaired.** The code here matches what was actually running, including its
   faults. `docs/quant-formula-index.md` names the formulas that do not match their own definitions.

---

## What would change this document

New broker tools on the connector, a second runtime connecting the broker, a test that drives the injection
case end to end, or a decision to publish a variant instead of a mirror. Any of those makes part of this
document wrong, and it should be revised rather than quietly kept.
