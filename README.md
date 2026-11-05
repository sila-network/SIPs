# Sila Improvement Proposals

Sila Network publishes original technical and governance proposals for the Sila protocol.

This repository begins with a clean Sila specification and tooling foundation. It does not import another network's proposal corpus, history, client implementations, automation code, or protocol identities.

## Components

- [SIP-1](SIPS/sip-1.md): initial Sila governance proposal.
- [Proposal template](sip-template.md): format for new Sila proposals.
- [Native Sila tool](tools/sila.py): format validation, dependency checks, identity audit, and website generation.
- [Sila verification](.github/workflows/verify.yml): read-only continuous integration.
- [Sila website styling](assets/site.css): original site presentation.

## Commands

Requires Python 3.11 or later. There are no third-party runtime packages.

1. Run unit tests: python3 -m unittest discover -s tests -v
2. Inspect proposal consistency: python3 tools/sila.py check
3. Inspect repository identity: python3 tools/sila.py audit
4. Build a local preview: python3 tools/sila.py build --output _site
5. Verify the generated website: python3 tools/sila.py verify-site --output _site

The site is a preview, not an automatic publication. Merging, network activation, and approval are separate actions that require their own evidence.

## Governance

The publication authority is Sila Network. SIP-1 currently has Draft status. No proposal is considered active merely because its document exists.

The initial named authors of SIP-1 are Ahmed Ibrahim and Jihad Mustafa. Additional document authorship requires actual authorization through Sila's governance process.

## Rights

Sila Network reserves the rights in this newly written Sila-owned repository content. See [LICENSE.md](LICENSE.md). No external protocol source files or third-party application assets are included.
