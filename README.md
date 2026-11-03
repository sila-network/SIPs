# Sila Improvement Proposals (SIPs)

<!-- markdownlint-disable-next-line MD033 -->
<p align="center"><img src="./assets/sila-logo.png" alt="Sila" width="160"></p>

This repository contains proposed Sila-native protocol and governance specifications. A document is not evidence that a Sila discussion, decision, implementation, release, or activation has occurred. [SIP-1](./SIPS/sip-1.md) defines the proposal process and credits Ahmed Ibrahim and Jihad Mustafa as its authors. Sila Network is the publication authority.

The proposed Sila specification categories are listed below. The public canonical site is not yet verified as a publication of this repository:

- **Core SIPs** are improvements to the Sila consensus protocol.
- **Networking SIPs** specify the peer-to-peer networking layer of Sila.
- **Interface SIPs** standardize interfaces to Sila, which determine how users and applications interact with the blockchain.
- **SRCs** specify application layer standards. The institutional Sila SRC corpus and its implementation dependencies must be verified separately; a routing reference does not imply adoption.
- **Meta SIPs** are miscellaneous improvements that nonetheless require some sort of consensus.
- **Informational SIPs** are non-standard improvements that do not require any form of consensus.

New proposals may be discussed at [Sila Magicians](https://sila-magicians.discourse.group/) and must follow [SIP-1](./SIPS/sip-1.md) and the [SIP template](./sip-template.md). A `discussions-to` value is used only for a genuine Sila discussion topic that already exists; no past discussion or consensus is implied.

This repository documents candidate specifications, not implementation support. Technical claims require independent Sila-owned code, tests, security review, and a recorded Sila governance decision before adoption.

## Repository Layout

| Path | Contents |
| --- | --- |
| [`SIPS/`](./SIPS) | SIP documents, one file per proposal, named `sip-N.md` |
| [`assets/`](./assets) | Images, diagrams and auxiliary files, in `assets/sip-N/` |
| [`sip-template.md`](./sip-template.md) | Template for new SIPs |
| [`config/sip-editors.yml`](./config/sip-editors.yml) | SIP editors per category |
| [`config/sipw.toml`](./config/sipw.toml) | `sipw` validation rules |
| [`tests/`](./tests) | Repository checks, run with `tests/run.sh` |
| [`LICENSE.md`](./LICENSE.md) | CC0 1.0 Universal |

## Source and Publication Status

Use a pinned Sila GitHub revision to cite a working document until a Sila-controlled canonical publication is verified. A document in Draft, Review, or Last Call is not an approved network rule. A Living process document likewise does not establish protocol activation. Do not infer Sila history from imported references.

## Validation

SIPs are validated against the rules of SIP-1 with [`sipw`](https://github.com/sila-chain/sipw), the Sila Improvement Proposal linter, using the configuration in [`config/sipw.toml`](./config/sipw.toml). SIP-1 is a process document and is not checked by `sipw`.

To validate an SIP locally, build `sipw` from source and run it from the root of this repository:

```sh
git clone --recurse-submodules https://github.com/sila-chain/sipw
cargo build --release --manifest-path sipw/Cargo.toml
sipw/target/release/sipw --config ./config/sipw.toml SIPS/sip-N.md
```

## License

Sila-authored specification text may be released under [CC0](./LICENSE.md) only to the extent that its authorized rights holders control those rights. Unresolved third-party text, code, and assets are not automatically relicensed by this repository.

**Brand notice:** The Sila logo shown above is supplied and identified by the Sila project owner as the official Sila mark. The logo is a reserved brand asset and is **not** covered by this repository's CC0 waiver for specification text. The Sila logo is reserved for Sila and is not released under the specification-text license.
