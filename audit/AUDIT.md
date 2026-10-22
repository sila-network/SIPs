# Repository Audit

This report records the state of `sila-network/SIPs` on branch `claude/greeting-mgich3`: what the repository contains, what was checked, how, and what remains open. Every check below is reproducible with [`tests/run.sh`](../tests/run.sh), which also runs on GitHub through [`.github/workflows/checks.yml`](../.github/workflows/checks.yml).

**Verdict: not 100/100.** All 13 checks pass, but 3 blockers remain open. They cannot be fixed inside this repository, or they need a decision from the project owner. `tests/run.sh` exits with `RESULT: BLOCKED (not 100/100)` until they are closed.

## Scope

This repository holds the SIP process, not the full set of SIPs.

| | Count |
| --- | --- |
| SIP documents in this repository (`SIPS/sip-N.md`) | 1 (SIP-1) |
| SIP documents in `sila-chain/SIPs` at commit `de0fadf00f0430c4c2829c5ad478a4aae869b36f` | 955 |

None of the 955 documents in `sila-chain/SIPs` were imported, reviewed, or audited. This audit covers only the files listed below.

## Files

| File | Origin | Rights |
| --- | --- | --- |
| `SIPS/sip-1.md` | Adapted from a process document published under CC0 1.0 | CC0 1.0 |
| `sip-template.md` | Adapted from a template published under CC0 1.0 | CC0 1.0 |
| `README.md` | Written for this repository | CC0 1.0 |
| `LICENSE.md` | CC0 1.0 Universal legal code, unmodified (one trailing lint directive added) | Creative Commons legal code |
| `assets/sip-1/sip-process.svg` | Drawn for this repository | CC0 1.0 |
| `assets/sila-logo.png` | Supplied by the project owner | **Open, see Blocker 1** |
| `config/sip-editors.yml` | Written for this repository | CC0 1.0 |
| `config/sipw.toml` | Derived from `sila-chain/SIPs` `config/sipw.toml`, with the corrections listed below | Same as source |
| `config/.markdownlint.yaml` | Copied from `sila-chain/SIPs` `config/.markdownlint.yaml` | Same as source |
| `config/.codespell-whitelist` | Written for this repository | CC0 1.0 |
| `tests/`, `audit/`, `.github/workflows/checks.yml` | Written for this repository | CC0 1.0 |

CC0 waives all copyright and related rights, including attribution, so adapting CC0 text and publishing the result is permitted without crediting the source. Publishing the adaptation does not make SILA Network the original author of the adapted text; SIP-1 separates the steward of the process from the authors of SIPs (see `## SIP Governance`).

## Checks

Last run: all checks pass.

| # | Check | Method | Result |
| --- | --- | --- | --- |
| 1 | Markdown style | `markdownlint-cli2` 0.18.1 with `config/.markdownlint.yaml` | 0 errors |
| 2 | Spelling | `codespell` with `config/.codespell-whitelist` | 0 errors |
| 3 | Config and asset syntax | Parse `sipw.toml` (TOML), `sip-editors.yml` (YAML), `sip-process.svg` (XML) | All parse |
| 4 | SIP rules, positive | `sipw` 0.12.0-dev (commit `94403b5bbe2420fd80176663d5918c357e2a0554`) on `tests/fixtures/sip-9999.md`, a proposal built from the template | Accepted |
| 5 | SIP rules, negative | `sipw` on `tests/fixtures/sip-9998.md`, with three planted errors | Rejected with exactly those three errors |
| 6 | Links | `tests/check_links.py`: 50 links, resolved on disk, at pinned commits, or fetched | 0 broken |
| 7 | Parity with the upstream process document at commit `f1ade090fd315895461fc3e249cb1a675aeb55a9` | Compare sections, statuses, preamble headers, template sections | Identical except the documented changes |
| 8 | Identity | Scan of tracked text files for foreign names, domains and terms | 0 hits |

Checks 1, 2, 4 and 5 use the same tools as the CI of `sila-chain/SIPs`. SIP-1 itself is not run through `sipw`: it is a process document without the sections an SIP requires, and the upstream CI also exempts it.

The identity scan skips `tests/` and `audit/`, because those files must name what they test for (for example, the negative fixture contains a nonexistent forum domain on purpose).

### Documented differences from the upstream process document

| Change | Reason |
| --- | --- |
| Removed "System Contract Implementations" | Sila has no repository for it |
| Removed "Yellow Paper" | `sila-chain/sila-yellowpaper` attributes Sila to a founder of another network |
| Removed "History" | Sila has no history before this repository; the owner asked for none |
| Added "SIP Governance" | Names SILA Network as steward, separate from authorship |
| Replaced calls and core developer references | Sila has no core developer calls; inclusion decisions rest with the steward |
| Replaced automated status changes with editor action | This repository has no status bot |
| Replaced client product names with "Sila client implementations" | The client repositories carry third-party product names |

### Corrections in `config/sipw.toml`

The configuration in `sila-chain/SIPs` rejects valid SIPs. Running its own `sipw` on `tests/fixtures/sip-9999.md` fails with two errors. This repository's copy fixes:

| Setting | `sila-chain/SIPs` | This repository |
| --- | --- | --- |
| `discussions-to` pattern | `sila-magicians.org` (does not exist) | `sila-magicians.discourse.group` |
| Allowed links | `sila-chain/yellowpaper`, `devp2p`, `portal-network-specs`, `sys-asm` (do not exist) | `sila-chain/sila-devp2p`, `sila-portal-network-specs`, `execution-apis` (exist) |
| Citation schema `$id` | `sips.sila.org` (does not resolve) | `sips.silachain.org` |

## Open blockers

### Blocker 1: logo provenance

`assets/sila-logo.png` carries a C2PA content credential signed by a third-party image generator (`gpt-image`, 2026-07-25, `digitalSourceType: trainedAlgorithmicMedia`). This is a foreign operational identity embedded in the file. Removing a content credential falsifies the image's provenance, so it was left in place.

Copyright protection for machine-generated images is not settled in every jurisdiction. The owner should choose one:

- Keep the file as is;
- Re-export the logo from the original design file;
- Replace it with an original design.

In any case, state in `README.md` that the logo is not covered by the CC0 waiver.

### Blocker 2: the canonical domain serves another repository

`https://sips.silachain.org/SIPS/sip-1` currently serves the SIP-1 of `sila-chain/SIPs`, which names authors and editors of another network and a forum that does not exist. The README of this repository cites that domain as canonical. Fixing this means changing the site source or the deployment, outside this repository.

### Blocker 3: no site build

This repository has no static site configuration, so the status page cannot be built or checked (HTML, internal links, images) from here.

## Owner decisions

These need the owner's confirmation; none of them has been applied:

1. **Logo:** choose an option from Blocker 1.
2. **Steward powers:** confirm the two steward powers in `## SIP Governance`: appointing and removing editors through a Meta SIP, and deciding which Core SIPs enter a network upgrade.
3. **Provenance:** optionally add a neutral sentence to SIP-1 saying it was adapted from public-domain (CC0) process documents.

## Issues outside this repository

Reported only; nothing outside this repository was changed.

| Repository | Issue |
| --- | --- |
| `sila-chain/SIPs` | `config/sipw.toml` errors listed above |
| `sila-chain/sipw` | Help links point to `https://sila.github.io/sipw/...`, which returns 404 |
| `sila-chain/execution-specs` | `README.md` at the commit linked from SIP-1 uses the name of another network's virtual machine twice |
| `sila-chain/sila-yellowpaper` | Attributes Sila to a founder of another network |
| `sila-chain/sila-pm` | Links to `sila-chain/pm`, which does not exist, and to a forum domain that does not exist |

## Reproducing

```sh
git clone --recurse-submodules https://github.com/sila-chain/sipw
git -C sipw checkout 94403b5bbe2420fd80176663d5918c357e2a0554
git -C sipw submodule update --init
cargo build --release --manifest-path sipw/Cargo.toml
SIPW=sipw/target/release/sipw tests/run.sh
```

Requirements: Node.js (for `npx`), Python 3.11 or later with PyYAML, `codespell`, `curl`, `git`, and Rust.

Commit authorship: commits on this branch are authored as `SILA Network`. They are not signed, so GitHub shows them as "Unverified". Signing requires a key registered on the `sila-chain` account.
