# Claude review of the Batch5 manifest

Branch `claude/greeting-mgich3`, reviewed commit `fba8c45c0d5f99f8f08de2baf482a414aa731122`, 2026-10-23.
Inputs: [`manifests/archive-batch5.sha256`](manifests/archive-batch5.sha256) (1377 paths),
[`manifests/archive-batch5-archive.sha256`](manifests/archive-batch5-archive.sha256),
[`manifests/archive-batch5-comparison.md`](manifests/archive-batch5-comparison.md).

**Verdict: not 100/100.** This review uses SHA-256 values only. No archive content was available to Claude,
so nothing here certifies content, rights, identity or technical parity.

## 1. Independent recount of ChatGPT's comparison

Reproduced exactly:

| | vs local batch (1352) | vs `sila-chain/SIPs@de0fadf0` (1353) |
| --- | ---: | ---: |
| Identical path and SHA-256 | 209 | 209 |
| Same path, different SHA-256 | 1087 | 1087 |
| Only in archive | 81 | 81 |
| Only in comparison manifest | 56 | 57 |

No duplicate paths. The archive holds 966 `SIPS/sip-*.md` files.

## 2. SIP coverage

The archive's 966 SIP numbers are **exactly** the 966 proposal numbers of the latest upstream process
repository at commit `deb8f0d3ea9167bd30775fb3d45d052fce651d56` (2026-10-16). Compared with
`sila-chain/SIPs@de0fadf0` it adds 11: 8247, 8317, 8357, 8358, 8364, 8365, 8374, 8383, 8397, 8411, 8433.
None is missing. File coverage is current; content parity is not verified.

## 3. Provenance of every archive file

Each archive SHA-256 was matched against eight sources Claude can rebuild:

- `sila-chain/SIPs@de0fadf0` and Claude's local batch
- the `sila-chain/SIPs` generator applied to upstream `c4f6cf42` and to latest upstream `deb8f0d`
- raw upstream `c4f6cf42` and `deb8f0d`
- `sila-chain/SRCs@7c5ef3b`
- this branch

Per-file results: [`manifests/archive-batch5-provenance.tsv`](manifests/archive-batch5-provenance.tsv).
Method: [`manifests/archive-batch5-provenance.py`](manifests/archive-batch5-provenance.py). Its input paths are
Claude's session paths, so it records the method rather than running elsewhere as is.

| Area | Same bytes at the same path | Same bytes at a different path | New bytes (no known source) |
| --- | ---: | ---: | ---: |
| `SIPS/` (966) | 0 | 0 | **966** |
| `assets/` (348) | 206 | 123 | 19 |
| Everything else (63) | 17 | 0 | 46 |
| **Total (1377)** | **223** | **123** | **1031** |

Findings:

1. **All 966 SIP texts are rewritten.** None is byte-identical to any known source, so every proposal must be
   reviewed from the archive itself. Hashes cannot show what changed.
2. **115 of the 123 moved assets are unmodified upstream bytes** placed under `assets/sip-N/`. The archive
   undoes the generator's text rewrites for those files, which keeps technical bytes (test vectors,
   contracts, data) as originally published. Their parity is therefore verifiable by hash.
3. **26 archive paths contain foreign identity names**: 16 `geth`, 9 `ERC`, 3 `EVM`, 1 `eth`. Examples:
   `assets/sip-1884/geth_processing.png` (the current `sila-chain/SIPs` name is `sila_processing.png`),
   `assets/sip-3267/contracts/ERC1155/`, `assets/sip-7543/gasEVMPlusEmulate.go`, `assets/sip-7885/op-geth/`.
   Under the Pure Sila rule these are blockers unless the owner records them as third-party artefact names
   kept for rights or provenance. Neither renaming nor keeping is decided here.

## 4. Repository structure differences

| Item | This branch | Archive |
| --- | --- | --- |
| `config/sipw.toml` (SIP rule validator) | present | **absent**: SIP rule checks cannot run as shipped |
| `config/sip-editors.yml` | present | absent |
| Workflows | `checks.yml` | `ci.yml` only (no site deploy, no SRCs merge) |
| Tests | `tests/run.sh` (13 checks) | 7 Python test files and 5 tools (`test_sila_identity.py`, `test_sila_rights.py`, ...) |
| Rights and identity records | in `audit/AUDIT.md` | `LEGAL_REVIEW.md`, `THIRD_PARTY_NOTICES.md`, `IDENTITY_RELEASE.md`, `VISUAL_CLEARANCES.json` |
| Site | none (Blocker 3) | Jekyll layout, includes and RSS present |

**Six files collide and differ:** `SIPS/sip-1.md`, `README.md`, `LICENSE.md`, `sip-template.md`,
`config/.codespell-whitelist`, `config/.markdownlint.yaml`. The archive's `LICENSE.md` and
`.codespell-whitelist` are byte-identical to `sila-chain/SIPs`. Importing the archive as is would replace
this branch's SIP-1, template and lint configuration, which the protocol forbids doing silently.

## 5. What is needed to go further

Hashes are exhausted. The next steps need the archive's contents:

1. **Owner decision:** where the extracted archive may be committed. Options:
   - a separate staging branch, for example `import/batch5-20261022`, so this branch's checks stay meaningful (needs approval for a new branch); or
   - a subdirectory of this branch. That puts 1377 files under this branch's markdownlint and codespell runs, which then measure the archive rather than this branch.
2. **ChatGPT:** commit the archive tree verbatim to the approved location, with one commit that only adds
   files, so `sha256sum` of every committed file can be checked against `archive-batch5.sha256`.
3. **Claude:** verify all 1377 hashes, run the archive's own tests and this branch's checks, build the site,
   run `sipw` with an explicit validator configuration, review the 966 rewritten SIP texts against latest
   upstream for normative parity, and report per file.
4. **Owner decisions** that the import cannot make:
   - which SIP-1, template and lint configuration govern (section 4)
   - the 26 foreign-name asset paths (section 3)
   - the legal items already listed in [`CLAUDE_STATUS.md`](CLAUDE_STATUS.md)
