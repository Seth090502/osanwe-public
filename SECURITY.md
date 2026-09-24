# Security

## Scope

This repository is a sanitized copy of a personal research system whose agents can hold a live brokerage
connection, and its threat model covers two things: what stops an agent from placing an order nobody asked
for, and what stops this publication from exposing its owner's private data. Orders are blocked today by a
permission deny list over every broker order, cancel and alert tool; the order gate behind that list has four
open defects in its first stair, which are documented rather than hidden, and the copy published here holds
no credentials and no account data.

The full model, including the attacks that were tried and what got through, is in
[docs/threat-model.md](docs/threat-model.md).

## Reporting a problem

Report a vulnerability privately through GitHub's private vulnerability reporting: open this repository's
**Security** tab and choose **Report a vulnerability**.
Please do not open a public issue for a security problem. Only the `main` branch is maintained.

The open defects already listed in the threat model (D70, D72, D73 and D74) do not need to be reported again.
A report of private data in this repository is treated as a security problem too.
