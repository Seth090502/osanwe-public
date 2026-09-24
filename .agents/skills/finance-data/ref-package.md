# Osanwe Finance and Data -- portable context

Version 1.3.1. Maintainer: Osanwe workspace maintainers. Intended audience:
the existing personal Osanwe workspace and the user's own supported Codex or
ChatGPT host. No account records or organization-wide distribution are included.

This package contains one context skill, finance-data, its public/synthetic
examples, and a Python standard-library runtime for evidence admission, scalar
financial metrics, operating DCF and cashflow analysis. Source and byte manifests
make the exact contents reviewable. Version 1.3.1 documents the host's narrower
single-verdict native review policy: schema rejection fails an attempt; automatic
repair is not a qualified feature. The optional native runner stays in the full
workspace, while portable run/verify/review load no native-only dependency.
Version 1.3.0 adds current semantic capability
bindings and an optional admitted public-method library. Only reviewed authored
passages with explicit reuse permission enter that library. Source originals,
personal or mixed material, and the full host index remain outside the package.
Version 1.2.2 binds allowable correction
references and resolution states into the producer schema and clarifies current
findings versus corrected historical critiques. Original failed reviews and
earlier packages remain unchanged. Version 1.2.1 added a canonical reviewer-producer
contract and bounded formatter-retry accounting for future runs. Earlier failed
native reviews remain failed; software controls do not retroactively accept them.
Version 1.2.0 added final-artifact review and
verification receipts with source passages, obligations and explicit reviewer
coverage, while preserving the existing calculation packet. Version 1.1.0 retained foundation selection
and adds causal-claim discipline, concrete Data briefs and traced incremental
margin. The 1.1.0 runtime adds named same-period accounting identities with
ordered metric roles; arbitrary cross-metric subtraction remains refused.
Native Opus 5 development QA informed these changes; it does not
establish investment performance or full live integration. The default package
contains method routing without library passages. The optional library is an
explicitly admitted subset; it is not the vault's entire research collection.
Missing library access must be disclosed. No broker connectors or account access
are added.

The canonical editable sources remain `.agents/skills/finance-data/`,
`tools/fis/`, and `config/finance-data-plugin.json` in the original workspace.
Regenerate with `python tools/package-finance-data.py --out <new-version.zip>`.
Do not edit generated ZIP members as a competing authority. Keep the old ZIP
for reproducibility, increment the manifest version for changed distributions,
and import/reinstall the new package through the host's supported plugin flow.
Updating the original workspace does not update already imported copies.

To include currently admitted, reusable public method passages, add
`--with-library` when building AND verifying the package. The existing financial
document registry validates each source version, exact passage, applicability,
worked calculation and reuse review before packaging. The package includes
`knowledge/passages.json` and `knowledge/source-records.json`, not source snapshots.
An empty admission set, changed source, invalid reuse review or excluded document
cannot be converted into an approved portable reference. A runtime-only package
continues to work without this option and discloses the missing library.

## Use in Codex and ChatGPT

In the Osanwe workspace, the canonical `.agents/skills/finance-data/SKILL.md`
is natively discoverable. A new task may be needed to refresh skill discovery.
No global installation is needed to use it in that workspace.

For a supported separate host, import the ZIP through its available plugin
import/upload flow. Workspace administrators may control that capability.
The ZIP has `.codex-plugin/plugin.json` at its root and includes no enclosing
directory. OpenAI's [plugin guidance](https://help.openai.com/en/articles/20001256/)
describes availability and account/app access separately. Import is not automatic
cross-product synchronization; this artifact does not claim it was imported into
ChatGPT, nor that Finances is callable there.

Finances and Data are separate plugins. Use them in the target host only when
their actual capabilities are available. A Python-capable host can run the
included runtime; a host without one can read the context and evidence, but
must label runtime execution UNVERIFIED. Do not send the vault or private
account data to compensate for a missing connector. The full investing,
portfolio, surveillance, backtest and decision workflows require the full vault.

Try: "Compare these company statements and prepare a source-backed Data report."
For a host with available authorized Finances data: "Explain my spending and
transfers, and show which accounts and transactions were included."
These are starter prompts, not claims that a live connector test has passed.

## Test the portable runtime

After extracting to a new directory, use that directory as the working folder:

```text
python tools/fis/test_workbench.py
python tools/fis/test_cashflow.py
python skills/finance-data/scripts/workbench.py run skills/finance-data/assets/synthetic-company.json --outdir company-demo
python skills/finance-data/scripts/workbench.py verify skills/finance-data/assets/synthetic-company.json company-demo
```

The same path supports synthetic-dcf.json and synthetic-cashflow.json. The
msft-historical.json example uses Microsoft's FY2024/FY2025 annual statement
figures and explicit historical limits; it is not a current valuation or advice.
No example requires credentials, paid data, network access or real accounts.

Runtime outputs include evidence and receipt JSON, safe tabular CSV, semantic
definitions, a report handoff and file hashes. Data can use these to produce
and validate a report or dashboard, with source IDs and coverage retained.
Personal records are not accepted for persistent cashflow interchange. Use
Finances in the authorized host; pure cashflow analysis requires that host to
keep data in the authorized session. No account actions are authorized.
