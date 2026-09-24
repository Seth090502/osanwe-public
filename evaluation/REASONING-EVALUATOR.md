---
aliases: []
categories: [reference]
tags: [fis]
status: active
created: 2026-09-13
updated: 2026-09-13
related: ["[[challenge_protocol]]"]
---

# Reasoning evaluator implementation and custody

The reasoning service is implemented and development-tested. It has not been
deployed, placed in independent custody, or used to establish financial quality.
The original strategy holdout gateway remains unavailable and never opens its
locked data. This is a second protocol behind the existing gateway, not a new
route to that holdout.

| Component | Implemented | Development tested | Independent assessment | Live verified |
| --- | --- | --- | --- | --- |
| Worker admission, accounting, grader, signing | yes | local SQLite D1 adapter | unavailable | no |
| Native Opus 5 / xhigh pilot runner | yes | failure, freeze and all-attempt telemetry controls | no | original frozen version ran 108 native sessions; later changes development-tested |
| Original public development tasks | 36 synthetic tasks, nine families | arithmetic/control checks | no | structured completion 36/36/33; no whole-prose assessment |
| Account-scope development supplement | four additional synthetic tasks, one distinct family | rational/decimal arithmetic and planted-error controls | no | not native-tested |
| Cohort release across bounded chunks | yes | 3,423-slot synthetic load and failure controls | no | no hosted capacity claim |
| Admission tasks | prospective 72 across ten families | shape checks/procedure only | curator unavailable | no |
| Statistical planning | exact intervals, paired power, Holm | deterministic checks | methodological review pending | not an inference service |

## Existing entry point and API

`python evaluation/request_access.py reasoning --help` routes through
`tools/eval-interface.py`. Legacy arguments keep the strategy backend refusal.
The new client receives a submission token only. The CLI reads one explicit
public/synthetic JSON request, obtains its token from an explicit environment
variable, follows no redirects, and requires HTTPS except explicit loopback
development mode. It never scans credential files or selects a brokerage account.

Every HTTP operation is POST with JSON and a Bearer submission token:

| Route | Required payload | Released information |
| --- | --- | --- |
| `/v1/reserve` | assignment_id, candidate_digest, protocol_digest, idempotency_key UUID | attempt ID and state only |
| `/v1/issue` | attempt_id | assigned public/synthetic task after durable reservation/issuance |
| `/v1/submit` | attempt_id, submission | locked state only |
| `/v1/score` | attempt_id | scored state only, never correctness |
| `/v1/finish` | attempt_id, outcome failed/abandoned | terminal state; credit stays spent |
| `/v1/close` | batch_id | closure after all attempts terminal, or frozen deadline |
| `/v1/seal` | batch_id | progress for four internally selected fragments; no grade |
| `/v1/release` | batch_id | signed aggregate once sealed and its whole cohort, if any, is closed |
| `/v1/acknowledge` | attempt_id | durable scored -> released transition |
| `/v1/cohort-seal` | batch_id | commits one chunk aggregate; status only |
| `/v1/cohort-close` | cohort_id | closure only after every frozen member closed and sealed |
| `/v1/cohort-release` | cohort_id | signed whole-cohort aggregate and chunk commitments |

No public endpoint admits a new campaign, candidate, source, grader, assignment,
batch, quota or model configuration. A renamed hypothesis or local-log deletion
cannot create an authorized assignment. One continuing campaign retains all
candidate batches and replacement datasets. Append-only witness batch indices
cannot be reset to claim a fresh familywise error allowance.

Submissions contain only privacy (`public` or `synthetic`), a bounded answer list,
and client-reported execution metadata. Each answer uses a known obligation ID,
answered/withheld status, a finite number/boolean/null or approved vocabulary
item, and known source IDs. Arbitrary narrative, account fields, personal files,
local arbitrary artifact hashes, unknown sources and extra metadata are rejected.
The maximum body is 8192 bytes and there are at most 16 obligations per case.

This schema limits accidental exfiltration but cannot prove a submitted number
was never derived from a personal account. Only assigned public/synthetic cases
may be submitted. Personal workflows and their narratives never enter this
service, its logs, bundles, native case fixtures or receipts.

## Durability and release boundary

The primary D1 database contains frozen cases, oracles, assignments, submitted
artifacts and receipt cache. A separate witness D1 database holds campaign quota,
batch admission, immutable reservations, transitions, closures and sealed result
fragments. D1 `batch()` commits the reservation and its initial event together;
failure rolls the transaction back. Subsequent submission bytes are committed to
the witness before primary artifact persistence. A crash there refuses recovery
of the missing artifact and preserves the spent attempt; it never accepts a
replacement answer. [D1 batch API](https://developers.cloudflare.com/d1/worker-api/d1-database/#batch)

`reserved -> issued -> submitted -> scored -> released` is enforced by SQL
triggers. Failed and abandoned outcomes are terminal. All changes are append-only.
Retries return the original attempt or state when bytes agree; changed bytes
under the same key are rejected. Server closure freezes every assigned slot,
including missing outputs and timeouts. Later completion cannot improve the
closed denominator. No metric is returned before closure and full sealing.

Ed25519 signatures bind canonical aggregate payload bytes and a hash of the
public artifact manifest. The manifest binds server-received structured answer
bytes and scored artifacts. Receipts identify protocol, dataset, batch plan,
epoch, witness, deployment code and declared evidence class. Verify against an
out-of-band pinned public key, never a key supplied by the same response. Historic
receipts remain verifiable with their old key and schema; they do not certify
new code, new datasets, financial prose, expertise or future reliability.

## Restores and rollback

Restoring the primary database cannot restore reservations in the separate
witness. Missing artifacts or mismatched epochs/plans refuse further scoring.
Before any database restore or code rollback the custodian enables RESTORE_LOCK.
Preserve both current stores and independently retained receipts first. Keep the
witness intact, restore only necessary primary data, compare exact committed
submission/score hashes, and leave unrecoverable attempts failed or abandoned.
Never rewrite old events or refund credits. A compatible code rollback retains
the witness and old signing public keys; it does not delete a failed campaign.

**An administrator rolling back both databases and the deployment anchor to a
mutually consistent old state is not detectable by this software alone.** This
is an explicit trust boundary. Independent custody must protect the witness and
retain its generation, admissions, closures and released receipts outside any
common restore set. If that cannot be demonstrated, use development scoring.
An assertion or a generation string alone is not independent custody evidence.

## Deployment preparation and final setup

The code ships with RESTORE_LOCK enabled, custody unverified, no public route,
placeholder database IDs, and no signing or submission secrets. There is no
automatic paid upgrade, login, account creation or deployment.

1. Run `node --test evaluation/tests/service.test.mjs evaluation/tests/cohort.test.mjs` and
   `python -m pytest evaluation/tests -q`; run the retained legacy gateway tests.
2. Build a new development load with
   `node evaluation/prepare_deployment.mjs <new-output-directory>`. It generates
   two SQL loads and an explicit public 108-slot plan. Its candidate digests are
   labeled placeholders and it is never an admission or model-quality result.
3. The independent custodian reviews source and negative-test evidence, pins a
   Wrangler version and hashes the Worker. They create two D1 databases in their
   account, set database IDs, apply the two reviewed schemas/loads, and keep
   deployment/database credentials and the administrative browser session out
   of research access. SQL loads are review artifacts; migration tooling must
   respect D1 transaction behavior rather than blindly nesting BEGIN statements.
4. The custodian generates an Ed25519 key outside the research host, stores the
   PKCS8 private key in the Worker secret SIGNING_KEY_PKCS8, and supplies only the
   public SPKI key to the client. A high-entropy submission token is installed as
   SUBMISSION_TOKEN_SHA256 on the server and provided to the submitter only.
   Keys and tokens are never committed or included in the deployment bundle.
5. In a development-only remote probe, exercise maximum payloads, concurrent
   quota exhaustion, interrupted persistence, full 216-slot load, sealing,
   signature verification, redaction and restore recovery. Measure actual Worker
   CPU, D1 operations and failures before any admission release. Keep request
   content/header logging disabled. Record only aggregate resource telemetry.
6. Only after the custody and capacity evidence is reviewed may the custodian
   admit independently curated 72-case material after candidate/source freeze:
   seven cases in each of valuation, earnings, portfolio, historical, macro,
   cycles, judgment and liquidity; eight household and eight account-scope cases.
   Inspect answerable, conflicting-evidence, applicability and misleading-framing
   coverage in every family. The Worker enforces counts and arms; labels alone
   cannot establish substantive coverage or independence. Only then may they
   set the matching custody receipt/code digests and unfreeze the service. An
   independent operator must reproduce calculations and inspect actual original
   passages, answerability, alternatives and financial materiality. Self-reported
   flags or agreement between language models do not provide expert validation.

Cloudflare currently lists a 10 ms free CPU budget, 100000 requests/day and
128 MB memory. Network/database wait is distinct from CPU. The local adapter
proves bounded code paths, not those hosted limits. It caps a batch at 216 slots
and seals four results per call; the final signature request aggregates already
sealed fragments. Windows process CPU has coarse ticks and is not a substitute
for hosted telemetry. No free-tier fit claim is made until the remote probe.
[Workers limits](https://developers.cloudflare.com/workers/platform/limits/)

## Confirmation cohorts and controlled rollback

A 216-slot admission batch is too small for many confirmatory sample sizes.
The existing service now supports one immutable cohort across at most 32 chunks,
each containing at most 216 assignments. This is a bounded extension of the
same databases, scoring code and submission client. It adds no inference host.

The custodian-only `service/cohort-freeze.mjs` helper freezes an explicit cohort
ID, campaign, analysis index, required family sample, three paired candidates,
equal resources and the complete member list before any reservation. It hashes
batch metadata, assignments, candidate/source/oracle identities, and resources.
Shared scenario or source metadata cannot become extra sampling units. The
helper deliberately refuses multiple cases from one such family; the selected
design uses one paired case per sampling unit. Human source-family labels still
require independent justification; renaming load fixtures does not create real
independence. No submitter route can create a cohort or alter its membership.

The witness owns one `analysis_slots` row for the whole cohort. Its statistical
index determines 0.05/2^j once. Transport chunk numbers confer no additional
alpha. Candidate renaming, new chunks, primary restoration, and SQL migration
cannot reclaim an occupied index or change the fixed family sample. Future
candidates and replacement datasets remain in the same campaign.

After ordinary `close` and `seal` calls for a member batch, call `cohort-seal`
with `{ "batch_id": "<member>" }`. It aggregates one bounded chunk into an
immutable witness fragment and returns status only. `cohort-close` takes
`{ "cohort_id": "<frozen-id>" }` and succeeds only after every fixed member
has closed and sealed. `cohort-release` returns a signed aggregate; ordinary
member `release`, including cached receipt replay, is blocked until that same
whole-cohort closure. Missing and abandoned opportunities remain in the fixed
denominator. Apply prespecified paired tests and Holm once to the complete
cohort, never separately to each released chunk. Receipts bind per-chunk artifact
manifest commitments; the submitter can then fetch member manifests to reconcile
every submitted artifact.

The additive witness migration preserves legacy batches, events, credits and
receipts. It backfills their existing analysis slots and never assigns new slots
to cohort members. Keep the new `EVAL_WITNESS_V2` database binding, with no legacy
`WITNESS` binding, during a code rollback. The archived pre-cohort Worker then
refuses service as unconfigured rather than bypassing cohort release. Apply
RESTORE_LOCK before any code/configuration/database recovery. An incompatible
old code version remains locked; rollback is not permission to reinstate an old
binding or erase cohort state. Malicious joint rollback of code, bindings,
databases and external custody history remains outside the software trust boundary.

The local 3,423-assignment load test uses 1,141 renamed synthetic load fixtures,
16 chunks and all-missing outcomes. It proves only bounded accounting/release
behavior: the full denominator survives, signatures verify, and the measured
maximum was 20 local D1 method calls per request. It does not establish genuine
independent cases, statistical power, model quality, or actual Cloudflare CPU.
Remote capacity testing must include this cohort path and the maximum admitted
cohort, alongside the original full-submission path, before deployment.

Quota checks use an atomic witness projection of spent burns, incremented in
the reservation transaction. It cannot decrease or be deleted through ordinary
SQL, and a failed transaction rolls the increment back with its reservation.
The migration backfills existing burns once without replacing their history.
This removes the prior repeated full-campaign count from the request path.
Query-call counts alone do not prove hosting fit: D1 meters scanned and written
rows, including index writes. Its free allowance currently includes 5 million
rows read and 100,000 rows written per day. The remote resource gate must retain
actual `rows_read` and `rows_written` metadata across the entire cohort and its
daily schedule; do not substitute local method-call counts for those metrics.
[D1 pricing and row accounting](https://developers.cloudflare.com/d1/platform/pricing/)

The remaining final setup is a custodian-controlled Cloudflare account/session,
the two database bindings, separately held secrets/public-key pin, and a reviewed
remote resource/custody probe. Until these exist, the delivered service is a
tested development implementation.

## Public native comparison and statistical interpretation

`native_pilot.py prepare` freezes all 108 opportunities, exact instruction and
library bytes, task/calculation evidence, binary/runner/grader hashes, resource
limits and randomized interleaving. It accepts three explicitly configured arms:
baseline, revised_no_library and revised_library. `run` uses fresh native
`claude-opus-5` sessions at xhigh and first-party subscription authentication;
it refuses a changed binary or model substitution. No `--bare` flag is used.
Only Read is allowed in copied public workspaces. The case oracle remains in
parent storage, outside the child's allowed working directory.

Identical rational calculation evidence is supplied to every arm. This native
pilot evaluates interpretation and reconciliation; it does not show that a
Read-only model executed the production calculation engine. Final prose and
actual library reads are preserved for separate review. The primary mechanical
score comes from the same bounded grader as the Worker and does not grade prose.
The run never prints interim scores. Missing/interrupted attempts cannot rerun;
closing an incomplete batch fixes their failures in the 108-slot denominator.

Future preparations archive their exact runner and grader under the plan's
`runtime/` directory. Run that archived `native_pilot.py summarize --plan <plan>`
to verify historical source versions after subsequent implementation changes.
The completed September 13 pilot predates automatic runtime archiving; its
hash-matched copy and original summary are preserved in
`reports/native-pilot-runtime-2026-09-13/`. Current summary version 2 counts
latency, usage and retrieval from every observed receipt before evaluating
output validity. Missing receipts are unobserved overhead, not free work.
The historical summary remains unchanged; its 66 reads covered only valid
outputs, while the all-attempt pilot report correctly records 72 library reads.

The 36 cases are synthetic, publicly exposed and author-curated. Numeric oracle
checks use independent rational expressions; applicability controls cover source
origins, restatements, costs, partial accounts, uncalibrated probability, irrelevant
primers, conflicting/stale guidance and unavailable originals/library. Their
successes do not establish unseen financial performance. Public benchmark
examples such as [FinanceBench](https://arxiv.org/abs/2311.11944) also belong in
development, not a confidently unseen holdout.

The closed pilot covered nine families, omitting the separately required
account-scope family. Its partial-account questions within other families do
not fulfill that missing coverage obligation. The original 36 cases, all 108
opportunities, scores, runtime archive and earlier packages remain unchanged.
Protocol revision 2 corrects prospective admission coverage to ten families
while retaining 72 cases and the same continuing campaign.

`account_scope_development_v1.json` is a separate four-task public supplement:
account-view deduplication, revoked scope versus cached permission, beneficial
ownership versus household gross assets, and cross-host/action authorization.
`account_scope_development.py --check` verifies its reproducible contents;
independent decimal test expressions check the rational arithmetic. Correct
controls and planted scope errors exercise the existing grader. This is local
development evidence, not independent curation or a new native-model result.
There are now 40 public development tasks across the retained release and its
supplement; no revised 36-task release or retroactive full-coverage pilot is
claimed. The native runner still targets the original 36-task release.
The public source/custody bundle for this revision is
`reports/evaluator-service-2026-09-13-coverage-v3.zip`; its manifest binds every
included file. `reports/account-scope-coverage-controls-2026-09-13.json` records
the local controls and historical preservation checks. Earlier bundles and
`reports/reasoning-protocol-2026-09-13-before-coverage-v2.json` remain history;
their successful checks do not certify subsequently changed source files.

`reviewer_controls.py prepare --output <new-directory>` writes a blinded
reviewer-input directory and a separate parent oracle. Six financial scenarios
produce 24 presentation pairs and 48 judgments, with 24 correct reports and
24 planted material defects. Each truth class has equal plain, confident,
verbose and combined-style reports, and report order varies. Some pairs are
both correct or both defective, preventing success by always criticizing one.
The scorer requires actual defect identification and correct-control acceptance;
missing, duplicate or malformed judgments fail. Strata are reported by style,
position and truth class. These are calibration controls, not independent
reliability samples. Native reviewer calibration remains a separate required run.
`run_reviewer_controls.py --controls <prepared-directory> --output <new-directory>`
performs that one bounded native subscription session and loads the parent oracle
only after the model finishes. It retains the first attempt, exact delivered
text, model IDs, input/binary hashes and any timeout. The native evidence remains
client-reported. Model effort configuration is recorded but is not provider
attestation, and a calibration pass is not expert certification.
The first native attempt failed 47/48 because one report ID was mistyped.
A separately versioned development correction used short blinded handles and
native required-key JSON Schema; it passed 48/48 on reordered exposed controls.
Both attempts and their distinct denominators are preserved in
*native-reviewer-controls-2026-09-13* (not published). The reusable `reviewer_schema.py` helper
rejects missing or unknown coverage; it never repairs an identifier by guessing.

`protocol_statistics.py` groups shared scenario OR source families before binary outcomes,
keeps missing outcomes as failures, provides exact paired tests and Clopper-Pearson
intervals, and sizes a fixed confirmation for 90% power at a five-point completion
improvement using public pilot discordance uncertainty. Batch j receives
0.05/2^j across one campaign, with Holm correction for the two prespecified
comparisons. No confirmatory outcomes enter sample-size planning. Insufficient
power or insufficient independent cases remains inconclusive. A perfect small
admission sample is not a rare-error guarantee.
The observed pilot was ceiling-limited at 36/36 for both non-library arms.
Conditional planning estimates are not a guarantee of 90% power: a literal
five-point increase over a truly perfect baseline is impossible. Before freezing
a confirmatory sample, justify its intended-use distribution, feasible effect,
independent families and transfer assumptions. Do not pick harder cases after
the fact and erase the original campaign or its adaptation history.
[Exact limits](https://itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm),
[adaptive reuse](https://arxiv.org/abs/1506.02629)
