---
sip: 1
title: Sila Proposal Governance
description: Defines how original Sila specifications are proposed, evaluated, and approved.
author: Ahmed Ibrahim, Jihad Mustafa
status: Draft
type: Meta
created: 2026-11-05
---

## Abstract

SIP-1 proposes an independent process for writing, testing, reviewing, and publishing Sila protocol specifications. A document records a proposal, not an activated network rule.

## Motivation

Sila requires a consistent procedure that distinguishes an idea from an implementation and a governance decision. Technical content must be authored for Sila and must be testable without relying on another network's identity or project history.

## Specification

### Ownership and identity

Sila Network is the sole publication authority for its SIP collection. Each normative protocol name, interface, network identifier, and test fixture must belong to Sila. A required but unverified Sila component is a blocker, not a reason to insert a foreign compatibility interface.

### Proposal kinds

The Standards Track type covers Core, Networking, Interface, and SRC categories. Meta covers governance rules, and Informational covers explanatory material that does not set binding protocol behavior.

The SRC category is reserved for application standards. A reference to a proposed SRC does not establish that the related contract or specification exists.

### Workflow states

The permitted states are Idea, Draft, Review, Last Call, Final, Stagnant, Withdrawn, and Living.

Idea records a concept awaiting a complete proposal. Draft is an editable submission. Review means substantive technical review is underway. Last Call identifies a time-bounded final review period. Final requires a recorded Sila approval. Stagnant marks an inactive submission. Withdrawn records an abandoned submission with a reason. Living is reserved for actively maintained process documents after formal approval.

A proposal must not claim Final status without an actual Sila decision reference. A Core protocol proposal additionally needs independent implementation evidence and conformance tests before approval or activation can be claimed.

### Required metadata

A numbered SIP has these mandatory fields: sip, title, description, author, status, type, and created. A Standards Track proposal must provide category. A Last Call proposal must provide last-call-deadline. A Withdrawn proposal must provide withdrawal-reason. A Final proposal must supply approval-ref.

The requires field lists existing Sila SIP numbers only. A discussions-to field may be added only when an actual Sila community discussion exists. No earlier decision, meeting, or activation date may be invented.

### Reviews and release gates

Technical review checks internal consistency, security assumptions, cross-references, ownership, and executable Sila behavior. Automated tests are necessary evidence but are not themselves governance approval.

A Sila-only identity audit is required before release. Changes to network rules additionally require supported Sila implementations, conformance results, and a separately recorded activation decision.

### Source and publication boundaries

Each normative code reference must identify a verified Sila-owned implementation and a stable revision. Independent public standards may be cited for neutral formats or safety rules; such citations do not grant those standards authority over the Sila network.

Publication of a website is separate from acceptance of a specification. A build result cannot be represented as protocol activation.

## Rationale

A small Sila-specific metadata model and a separately testable publication workflow make invalid assumptions easier to identify. Beginning with a single Draft foundation avoids fabricating an inherited history or an unverified proposal collection.

## Test Cases

A complete Draft with accurate metadata should validate. Duplicate identifiers, invented dependencies, unapproved Final status, unrecognized categories, unsafe links, and foreign protocol identifiers must be rejected by the Sila verifier.

## Security Considerations

A document can describe dangerous behavior without implementing it. Approval must therefore include threat analysis and verification that all claimed Sila interfaces actually exist. Website generation must escape document content before producing HTML. No automated check may silently convert an unresolved protocol reference into an approved rule.

## Copyright

Copyright (c) 2026 Sila Network. All rights reserved. See the repository's rights notice.
