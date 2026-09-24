# Final financial report review

The `osanwe.analysis/1` calculation packet and seven-file bundle remain unchanged.
`osanwe.review-request/1` and `osanwe.report-review/1` are companion interfaces.
Review public/synthetic material only; personal records and revealing hashes never
enter this persistence path. Keep personal analysis inside its authorized host.

```text
python tools/fis/workbench.py review packet.json calculation request.json --artifacts inputs --prepare
python tools/fis/workbench.py review packet.json calculation request.json --artifacts inputs --prepare --reviewer-id reviewer:separate --reviewer-model claude-opus-5 --reviewer-effort xhigh
python tools/fis/workbench.py review packet.json calculation request.json --artifacts inputs --outdir review-v1
python tools/fis/workbench.py verify-review review-v1
```

Prepare validates deterministic obligations and returns a frozen context digest
and required reviewer coverage. It does not invoke a model or accept the report.
Give a separate read-only reviewer the exact evidence, task, complete rendered
content and context manifest; the reviewer must return its own findings against
that digest. It cannot change evidence, implementation or criteria. Do not copy
synthetic fixture judgments into a live review.

The explicit reviewer options add `producer_contract`: a versioned native JSON
schema, short response key (default `R001`), instructions and digest generated from
the same owning rules as the consumer. Set model and effort explicitly to the
authorized values; these options prepare a contract and do not run or verify a
model. Never hand-copy a different output schema or reinterpret malformed prose
as a passing verdict. Use `consume_reviewer_output(contract, request, prepared,
output)` to check the original response, then place its reviewer record in a new
request and run the ordinary review/archive commands. Those commands recheck the
actual evidence and delivered artifacts; producer schema validity cannot accept a
report on its own.

The current producer schema is `osanwe.reviewer-producer-contract/2`. It binds
`correction_artifact_ids` to the actual `correction` roles in the prepared context.
With no such artifacts, the generated schema permits no resolved finding. With
correction evidence available, a resolved finding must reference one of those
exact IDs and set `resolution_verified` to true. Open and disputed findings must
use null/false resolution metadata. The consumer regenerates this role set from
the actual prepared task; a rehashed contract with forged correction IDs fails.
Structural contract validation alone does not attest that declared roles are true.

Assess current report defects and current unresolved disagreements as findings.
Discuss genuinely corrected historical critiques, scope notes and comparisons in
judgment rationales; do not duplicate them as new resolved or disputed findings.
If an earlier correction is inadequate, report the actual remaining current
financial defect. Preserve every real current disagreement and its evidence.
These producer constraints express the existing semantic rules; they do not
relax financial acceptance. Historical version 1 contracts, model outputs and
receipts remain unchanged and are replayed with their preserved original source.

`disagreements` is a list of IDs of actual findings in that same response. Put the
substance in `finding.reason`, including severity, status and evidence references.
Scope notes, confirmations and history belong in the relevant judgment rationale.
Unknown IDs and prose in the ID list are malformed. A valid unresolved disagreement
withholds acceptance; omitting its ID does not make a `disputed` finding disappear.
Do not downgrade, delete or relabel a real disagreement to obtain acceptance.

The request records author/reviewer identities, question and horizon, supported
obligations, missing information, exact artifact hashes/surfaces, inspected source
passages/cells and original labels, source origins/revisions, method retrieval,
numeric display transformations, render observations, scenarios and alternatives.
Use the actual schema in tools/fis/report_review.py; unsupported fields fail closed.
The full-workspace test_report_review.py fixture is an executable synthetic example,
not evidence that a human or model reviewed a real report.

Material claims require support IDs and actual text spans. Bind final narrative,
tables, charts/labels/tooltips, exports and meaningful filter states, retaining
original drafts and disagreements. Every source claim needs a source review;
`source_checked` alone is insufficient. Original public source bytes can accompany
extracted passages with explicit original-to-extract bindings. A narrowly recorded
public source classification does not waive canary, account or credential controls.

Task obligations prevent blanket refusal on answerable questions. Consequential
reviews require computed reversal conditions and applicable simple alternatives.
External calculation records bind their code and result evidence and independently
reproduce bounded arithmetic expressions; they are distinct from workbench results.
Reviewers assess economic meaning, methods, alternatives, costs, sensitivity,
limitations, complete claim coverage, source support and actual rendering.

Timeouts, malformed verdicts, missing coverage or unresolved critical/major financial
findings withhold acceptance. Changes to evidence, mappings, methods, code, scope
or delivered artifacts require a new review. Archived receipts may remain historically
verifiable for their original versions without establishing current eligibility.
Local model identity/effort and read-only declarations are client-reported; local
receipts are integrity records, not external signatures or expert certification.

## Ordinary native launcher

`tools/fis/native_review.py` extends the owning workbench with an optional host
runner. Keep harness, model and effort explicit in every command. Ordinary native
review does not spend or replenish evaluator credits. The requested evaluation
configuration remains Claude Opus 5 at xhigh; another model requires its own
explicit authorized selection and cannot stand in for that evaluation.

```text
python tools/fis/workbench.py native-review prepare packet.json calculation request.json --artifacts inputs --outdir prepared-v1 --harness claude --model claude-opus-5 --effort xhigh --reviewer-id reviewer:native-1
python tools/fis/workbench.py native-review probe prepared-v1 --harness claude --model claude-opus-5 --effort xhigh --executable PATH_TO_CLAUDE --outdir mechanics-v1
python tools/fis/workbench.py native-review run prepared-v1 --harness claude --model claude-opus-5 --effort xhigh --executable PATH_TO_CLAUDE --qualification mechanics-v1/receipt.json --attempt-id ordinary:review-1 --outdir attempt-v1
python tools/fis/workbench.py verify-review attempt-v1/review
```

Prepare supplies the complete public/synthetic UTF-8 task, source artifacts,
original draft, current delivered surfaces, calculations, methods, prior reviewer
records and response contract inline. It refuses binary artifacts or excess input
instead of silently truncating or certifying unseen material. Current limits are
1 MB input, 8 MB total process output, 2 MB per event, at most 32 accounted turns,
32,000 requested output tokens and 1,800 seconds. Defaults are 900 seconds, 24
turns and 16,000 requested output tokens. Requested token limits require a matching
observed synthetic-provider request; they are distinct from actual reported usage.
Use an explicit smaller bound when appropriate. Timeouts and process failures
terminate the child process tree and leave a failed attempt.

The prepared directory includes exact evidence and implementation snapshots.
Changes to files, implementation, settings, schema or the selected model require
new preparation and qualification. Supply `--document-registry` when methods use
the admitted financial library. The runner regenerates the existing owner's
manifest and requires exact document hash, source version, and an admitted chunk
containing the inspected method passage. It freezes the manifest and applicable
limitations and rechecks current admission before execution. A changed source or
registry cannot keep the old binding eligible. Without this option the receipt
explicitly says library admission is unverified; `method.approved_scope` does not
approve a document. Admission does not decide whether a method suits this task.

The current `osanwe.native-review-runner/2` policy permits one verdict and no
formatter corrections. Any schema rejection or additional formatter stops the
attempt, even if a replacement would be valid or identical. Failed retry-capable
version 1 probes and native attempts remain failed history; this narrower policy
does not regrade them or establish recovery support.

The probe uses an isolated loopback synthetic provider. It checks exact input
transport, model/effort/output requests, the offered tool set, rejected absolute
and relative reads, a rejected command, a valid verdict, the synthetic native
schema reminder, and stopped schema-rejection/additional-formatter attempts.
Only Claude's native `StructuredOutput` formatter is permitted;
all filesystem and external tools are disabled. The proof binds exact installed
binary bytes, the generated configuration, contract and runner, expires after 24
hours, and is checked again before launch. The native stream must also preserve
the expected offered-tool boundary. These finite controls are development
evidence, not exhaustive OS isolation or native subscription reliability proof.
Native execution separately checks subscription authentication, model events,
fixed budgets and the actual financial consumer. Effort remains client-reported.

Run reserves an immutable attempt before inference. Original safe formatter drafts,
schema rejection metadata and the locked verdict remain in its journal. Raw
provider error prose, thinking, stderr and credential-like output are not written
by the runner. Native session persistence is disabled; this does not certify all
vendor telemetry. Existing reviewer findings remain in the new archived request.
Financial acceptance still requires the unchanged consumer and exact delivered
artifact archive. A successful process with major findings is withheld.

`--harness codex` supports preparation and a distinct development event adapter.
Codex native execution is currently refused because an exhaustive offered-tool
boundary has not been mechanically qualified. Its read-only sandbox restricts
writes and does not establish read containment. The installed CLI and the
[official configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
document individual tool toggles; they do not prove every file-capable tool is
disabled. Codex `item.completed`/`turn.completed` events are never represented as
Claude `Read`/`StructuredOutput` events. Runtime-only portable bundles may omit this
host runner; ordinary run/verify/review commands load no native-only dependency.

## Native execution accounting

`tools/fis/reviewer_execution.py` is the preserved local public/synthetic journal
helper; it performs no inference itself and does not alter historical attempts.
Reserve one new immutable directory with `NativeReviewAttempt` before inference.
Keep the same fixed process deadline, turn limit and campaign attempt through
formatter retries. Feed each complete tool call, typed result and cumulative turn
count into that same attempt; always finish or abandon it. Store the canonical
contract and safe formatter drafts exactly as received. Provider error prose,
thinking blocks, source text and personal data are not journal fields. Results
retain tool IDs, success/error flags and bounded schema diagnostic keywords/paths.

The historical helper permits `Read` and the native `StructuredOutput` formatter.
The ordinary inline launcher narrows this to the formatter alone. The latter
requires the behavior-tested binary SHA-256 pinned in the helper, requested native
JSON schema and strict empty MCP configuration. Any other tool, pending result,
missing final formatter, counter reset or exhausted budget fails the attempt.
The host launcher must enforce the actual process deadline, turn limit and read
scope. These supplied observations and the local journal do not demonstrate
independent execution custody or tamper-proof quota enforcement.

A caller of the historical helper can correct a rejected formatter draft within
that same attempt only after
a recorded provider schema rejection. Preserve every safe draft and typed result,
including failed corrections. Unfinished schema-invalid drafts may undergo normal
reasoning and correction; they are not delivered verdicts. Lock the first locally
schema-valid completed verdict. A later different formatter draft or final output
is rejected and retained. The final output must match the successful formatter and
pass the local canonical schema check even if the provider claims success.
The ordinary version 2 launcher deliberately does not qualify that correction
feature; every rejected draft ends its attempt.

Execution completion still requires the separate financial consumer and final
artifact review. It supplies no new evaluation credit, expert validation or
quality-improvement claim. Reusing an attempt directory is refused, including after
abandonment; local deletion or a different directory cannot be treated as restored
server-controlled credits. Historical attempts and original grading remain fixed.
