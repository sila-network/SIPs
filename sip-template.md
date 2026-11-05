# Sila proposal authoring template

This original Sila template implements the document contract proposed in [SIP-1](SIPS/sip-1.md). It is an authoring aid, not an approved specification or a historical record.

An authorized Sila editor must assign a real positive proposal number before a numbered SIP is published. Only actual Sila authors, dates, dependencies, and decisions may be entered. A new document normally begins as Draft.

## Front matter example

The lines below are placeholders, not an issued proposal:

```yaml
---
sip: N
title: Concise original Sila feature
description: One sentence describing the proposed Sila behavior.
author: Authorized Sila author
status: Draft
type: Standards Track
category: Core
created: YYYY-MM-DD
---
```

For a Meta or Informational SIP, omit category. For Standards Track use exactly one of Core, Networking, Interface, or SRC.

Additional fields are conditional:

- `requires` — existing, verified Sila SIP numbers only.
- `discussions-to` — link to an actual Sila discussion topic; omit if none exists.
- `last-call-deadline` — required only when a genuine Last Call begins.
- `withdrawal-reason` — required if the proposal is actually withdrawn.
- `approval-ref` — required for Final or approved Living; a real, immutable Sila decision reference.
- `implementation-ref` — optional pinned Sila code or conformance reference, never a fabricated implementation.

Do not add arbitrary extra preamble fields or claim status transitions that did not occur.

## Abstract

Describe the proposal and its limits without claiming activation.

## Motivation

Explain the Sila-specific problem, users affected, and why action is needed.

## Specification

Precisely define the behavior or governance rule, inputs, outputs, error conditions, dependencies, and testable acceptance criteria. Explain all Sila-specific numeric constants and network interfaces used by the proposal. Identify missing Sila components as blockers.

## Rationale

Explain the chosen solution and meaningful trade-offs.

## Test Cases

Provide Sila-native accepted and rejected examples, including adversarial and boundary cases where relevant. Test cases do not override the Specification.

## Security Considerations

Document realistic risks, attacker capabilities, invariants, mitigation, upgrade impact, and any assumptions that still need validation.

## Copyright

State the rights applicable to the original Sila content and any permitted assets. See the repository [rights notice](LICENSE.md).
