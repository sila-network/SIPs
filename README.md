<p align="center"><img src="./assets/sila-logo.png" alt="Sila" width="160"></p>

# Sila Improvement Proposals (SIPs)

The goal of the SIP project is to standardize and provide high-quality documentation for Sila itself and conventions built upon it. This repository tracks past and ongoing improvements to Sila in the form of Sila Improvement Proposals (SIPs). [SIP-1](./SIPS/sip-1.md) governs how SIPs are published.

The [status page](https://sips.silachain.org/) tracks and lists SIPs, which can be divided into the following categories:

- **Core SIPs** are improvements to the Sila consensus protocol.
- **Networking SIPs** specify the peer-to-peer networking layer of Sila.
- **Interface SIPs** standardize interfaces to Sila, which determine how users and applications interact with the blockchain.
- **SRCs** specify application layer standards, which determine how applications running on Sila can interact with each other. SRCs are maintained in the [SRCs repository](https://github.com/sila-chain/SRCs).
- **Meta SIPs** are miscellaneous improvements that nonetheless require some sort of consensus.
- **Informational SIPs** are non-standard improvements that do not require any form of consensus.

**Before you write an SIP, ideas MUST be thoroughly discussed on [Sila Magicians](https://sila-magicians.discourse.group/) in the [SIPs category](https://sila-magicians.discourse.group/c/sips/5). Once consensus is reached, thoroughly read and review [SIP-1](./SIPS/sip-1.md), which describes the SIP process, and start from the [SIP template](./sip-template.md).**

Please note that this repository is for documenting standards and not for help implementing them. For specific questions and concerns regarding SIPs, it's best to comment on the relevant discussion thread of the SIP denoted by the `discussions-to` tag in the SIP's preamble.

## Repository Layout

| Path | Contents |
| --- | --- |
| [`SIPS/`](./SIPS) | SIP documents, one file per proposal, named `sip-N.md` |
| [`assets/`](./assets) | Images, diagrams and auxiliary files, in `assets/sip-N/` |
| [`sip-template.md`](./sip-template.md) | Template for new SIPs |
| [`config/sip-editors.yml`](./config/sip-editors.yml) | SIP editors per category |
| [`LICENSE.md`](./LICENSE.md) | CC0 1.0 Universal |

## Preferred Citation Format

The canonical URL for an SIP that has achieved draft status at any point is at <https://sips.silachain.org/>. For example, the canonical URL for SIP-1 is <https://sips.silachain.org/SIPS/sip-1>.

Consider any document not published at <https://sips.silachain.org/> as a working paper. Additionally, consider published SIPs with a status of "draft", "review", or "last call" to be incomplete drafts, and note that their specification is likely to be subject to change.

## Validation

SIP-1 rules are enforced using [`sipw`](https://github.com/sila-chain/sipw), the Sila Improvement Proposal linter.

## License

All SIPs are released into the public domain: copyright and related rights waived via [CC0](./LICENSE.md).
