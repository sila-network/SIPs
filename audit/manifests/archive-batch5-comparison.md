# Batch5 archive manifest comparison — 2026-10-23

This is an **SHA-256 path-by-path comparison only**, not a content-parity or rights certification, and it does not import any standards.

## Inputs

- Candidate archive manifest: [`archive-batch5.sha256`](archive-batch5.sha256), 1,377 file paths.
- Candidate archive checksum: [`archive-batch5-archive.sha256`](archive-batch5-archive.sha256), verified as `76f6079f9bbbd40043c0f6224afd645daedf6cda87a34bc7aed0fddef0785ba0`.
- Comparison manifests: [`sila-chain-SIPs-batch1-local.sha256`](../claude-evidence/manifests/sila-chain-SIPs-batch1-local.sha256) (1,352 paths) and [`sila-chain-SIPs-de0fadf0.sha256`](../claude-evidence/manifests/sila-chain-SIPs-de0fadf0.sha256) (1,353 paths), preserved by Claude as historical comparison evidence. Neither is the authority for new Sila work.

## Results

| SHA-256 comparison | Compared to local batch (1,352) | Compared to base (1,353) |
| --- | ---: | ---: |
| Archive paths | 1,377 | 1,377 |
| Identical path and SHA-256 | 209 | 209 |
| Same path, different SHA-256 | 1,087 | 1,087 |
| Present only in candidate archive | 81 | 81 |
| Present only in comparison manifest | 56 | 57 |

Every archive path appears once in the manifest. **SHA equality checks identity only**; SHA inequality does not reveal why content differs. Historical renamed paths, unverified external rights and foreign identity names may explain some path differences, and must be classified without guessing or recreating forbidden aliases.

## Integration requirements

1. Preserve the branch's SIP-1, CI and audit work. Do not overwrite them automatically with either archived or historical files.
2. For the 209 identical paths, byte reuse may be possible, but confirm the independently verified source and licensing before copying.
3. Review the 1,087 changed paths against the archive itself, not just against historical project files.
4. Review the 81 archive-only and 56 comparison-only paths before interpreting any as additions or deletions. **A renamed path is not proof that the new name is authoritative.**
5. Keep the official `sila-network/SIPs` tree strictly Sila-native in operational identities. Unknown or external-only identities remain blockers pending verified Sila counterparts; do not add shims.
6. Independently run the full corpus, website, license, identity, dependency and normative parity checks; nothing here certifies 100/100.

## Status

**MANIFEST TRANSFER COMPLETE. FULL CORPUS IMPORT NOT COMPLETE.**

The owner is not required to download, upload, or relay any files on a phone. The participants can read this report and source manifests on the authorized work branch.
