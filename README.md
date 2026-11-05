# Sila Improvement Proposals

Sila Network publishes original technical and governance proposals for the Sila protocol.

This repository begins with a clean Sila specification and tooling foundation. It does not import another network's proposal corpus, history, client implementations, automation code, or protocol identities.

## Components

- [SIP-1](SIPS/sip-1.md): initial Sila governance proposal.
- [Proposal template](sip-template.md): format for new Sila proposals.
- [Sila native specification checker](tools/sila_specs.py): strict metadata, sections, safe links and anchors, and normative dependency graphs.
- [Sila command and site tool](tools/sila.py): runs checks and builds local documentation.
- [Sila verification](.github/workflows/verify.yml): read-only continuous integration.
- [Sila website styling](assets/site.css): original site presentation.

## Commands

Requires Python 3.11 or later. There are no third-party runtime packages. This offline checker does not establish external discussion, governance approval, or network activation.

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

## Original Sila PR review gate

The [Sila review gate](tools/sila_review.py) verifies the changed file list and real
GitHub APPROVED reviews against the explicitly authorized identities in
[the Sila reviewer policy](config/sila-review.toml).

- Sila specifications require editorial and technical role authorization.
  One real reviewer may hold both roles if explicitly appointed to both and
  independent of the pull-request author.
- Code and automation changes require an authorized technical review.
- Other documents and assets require an authorized editorial review.
- Changing the reviewer policy in the same pull request cannot authorize the
  change being reviewed.
- Stale, withdrawn, dismissed, or self-issued reviews are not accepted.
- No reviewers are appointed by this code. The initial roster is empty, so
  applicable pull requests remain blocked until real reviewer accounts are
  separately authorized by Sila Network.
- The gate has GitHub **read-only** permissions. It cannot approve, publish,
  merge, assign reviewers, or change a proposal's governance status.

A passing check does not itself establish an authorized governance decision.
To enforce a mandatory merge block, GitHub's repository rules must require
the corresponding check on the target protected branch; this software cannot
substitute for repository administration settings.

## Sila documentation website

The original Sila static website is generated from verified proposal source;
it does not import third-party themes, remote fonts or client-side libraries.

- [Sila site generator](tools/sila_site.py) builds the home page, an individual
  accessible HTML page for each real SIP, six category pages, eight status
  pages, the searchable JSON index, and the original RSS 2.0 feed.
- [Sila styling](assets/site.css) adapts to phones and respects reduced motion.
- [Sila local search](assets/site.js) filters by text, category, and status;
  all documents remain browsable when JavaScript is disabled.
- The feed links to actual Sila source revisions on the current working branch
  until the official domain is configured and publicly deployed.
- A generated `_site/` preview is local build output, not a public release.
  It MUST NOT be treated as a Final SIP or network activation.

To preview locally (using only Python's standard library):

```sh
python3 tools/sila.py check
python3 tools/sila.py build --output _site
python3 tools/sila.py verify-site --output _site
python3 -m http.server 8000 --directory _site
```

Open `http://localhost:8000` on the computer running that server.
No public deployment or domain change is performed by these commands.
