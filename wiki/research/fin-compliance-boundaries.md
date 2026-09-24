---
name: fin-compliance-boundaries
categories: [wiki]
type: reference
status: active
created: 2026-08-24
updated: 2026-08-24
tags:
  - topic/finance
related: []
---

# Financial Compliance Boundaries

Status: ACTIVE
Scope: Personal finance research vault at `<VAULT_ROOT>`
Companion to: fin-governance-framework.md, fin-risk-controls.md

---

## 1. What This System IS

- EDUCATIONAL ANALYSIS: commentary and study material about markets,
  portfolio construction, and risk management techniques.
- PERSONAL RESEARCH: a single-operator research workspace for organizing and
  stress-testing the operator's own investment thinking.
- DECISION SUPPORT TOOL: it surfaces information, runs analyses, and drafts
  proposals -- all final decisions rest with the human operator.

Nothing produced here is a solicitation, offer, or personalized
recommendation to buy or sell any security for anyone other than the sole
operator of this private vault.

---

## 2. What This System Is NOT

The system, the agent, and the operator's use of them do NOT constitute:

- A REGISTERED INVESTMENT ADVISER (RIA): no SEC/state registration exists;
  no advisory services are offered to third parties.
- A BROKER-DEALER: no order execution for others, no custody of client
  assets, no FINRA membership.
- A TAX PREPARER: no tax return preparation, no formal tax advice, no CPA/EA
  representation.
- LEGAL COUNSEL: no attorney-client relationship, no legal advice, no
  representation before any body.

Outputs must not be presented to any third party as professional advice.

---

## 3. When To Consult Licensed Professionals

Escalate OUTSIDE this system to appropriately licensed professionals for:

| Topic | Professional |
|-------|--------------|
| Tax planning beyond education (return positions, elections, audits, multi-state, crypto/disposition specifics) | CPA / Enrolled Agent / tax attorney |
| Estate planning (wills, trusts, beneficiary structures, gifting strategy) | Estate planning attorney |
| Insurance product selection (life, disability, LTC, annuities) | Licensed insurance professional |
| Legal entity formation (LLCs, trusts as vehicles, contracts) | Attorney |

Rule: the agent may explain concepts and tradeoffs educationally, but any
question whose answer would be relied upon for a filing, contract, enrollment,
or irrevocable structure goes to a licensed human first. Drafting such material
is out of scope for this vault.

---

## 4. Data Privacy

Financial data in this vault is HIGHLY SENSITIVE.

- NEVER export vault financial data to external services: no cloud uploads, no
  pasting into third-party websites, no sending content to external APIs or
  endpoints, no email transmission outside the local machine.
- Analysis stays LOCAL. Tools that process vault data must run against local
  files; network access is not part of any approved workflow for this data.
- Credentials live exclusively under .raw/private/finance/credentials/
  (*.local.md). These are read-blocked for the agent under the governance
  authority matrix and must never be copied, moved, quoted, or referenced by
  value anywhere else in the vault.
- Derived artifacts (reports, ledgers) must avoid embedding account numbers,
  balances keyed to identifiable accounts, or credentials; use position-level
  percentages and instrument identifiers.
- If sensitive data is discovered outside its intended location, flag it as a
  governance event rather than moving or copying it unprompted.

---

## 5. Recordkeeping

- ALL recommendations are logged to the DECISION LEDGER (append-only) per the
  governance framework audit trail: timestamp, classification, inputs,
  reasoning, proposal, approval, and reconciliation status.
- Records support after-action review and honest performance measurement --
  including of failed calls. Do not delete or edit historical entries.
- Retention: ledger and supporting reports are retained indefinitely within
  the local vault unless the operator explicitly disposes of them.
- Governance events (boundary attempts, privacy incidents, prohibited-action
  refusals) are recorded in the same ledger.

---

## 6. Related Documents

- fin-governance-framework.md -- decision classes, authority matrix, audit trail
- fin-risk-controls.md -- limits, ladder, leverage, kill switches

Last reviewed: 2026-08-24
