# Claude review of commit c1ea738

Reviewed commit `c1ea7385c9608b7fd9b25f7ceae3f9dc89b2f213` ("triage all 966 Batch5 SIPs"), 2026-10-24.
Inputs: [`BATCH5_PROPOSAL_TRIAGE.md`](BATCH5_PROPOSAL_TRIAGE.md) and
[`manifests/archive-batch5-966-proposal-gates.tsv`](manifests/archive-batch5-966-proposal-gates.tsv).

**Verdict: the triage data is consistent; it shows one functional regression and 15 SIPs that need review
for possible content loss.** Not 100/100.

## 1. Consistency checks

| Check | Result |
| --- | --- |
| Rows and unique paths | 966 and 966 |
| Every `sha256` equals [`archive-batch5.sha256`](manifests/archive-batch5.sha256) | Yes, 0 mismatches |
| Covers exactly the archive's `SIPS/` files | Yes |
| Report totals recomputed from the TSV | All match: 451 with hits, 515 without, 3469 hits, 965 without `status:`, 1094 links |

Additional totals from the same TSV: `requires:` present in 319 files; the one `status:` value is `Draft`
in `SIPS/sip-233.md`; the restricted-rights signal is 0 everywhere.

## 2. Routing stubs lost their status

`sila-chain/SIPs` has 365 routing stubs (`status: Moved`) that send SRC numbers to `sila-chain/SRCs`.
**In the archive all 365 have no `status:` field.** Each grew by exactly 4 lines and 475 bytes, so one
template was applied to all of them.

`Moved` is part of the status order that `config/sipw.toml` uses in `preamble-requires-status` and
`markdown-link-status`, so links and `requires:` entries that point at SRC numbers can no longer be
checked. The owner asked for the 365 routing stubs to be preserved. This is a functional regression,
separate from the governance question of statuses on the other 601 SIPs. It needs an owner decision: restore
`Moved`, or define the replacement routing rule first.

## 3. Rights marker

383 SIPs have no rights marker, but 365 of them are routing stubs. **18 non-stub SIPs** have no rights marker
(listed in the batch file below with `has_rights_marker` = 0). The signal is a text search only, as the
triage says.

## 4. Size compared with latest upstream

Each archive SIP was compared with the same SIP regenerated from latest upstream (`deb8f0d`).

| | Value |
| --- | --- |
| Total bytes, archive ÷ regenerated | 1.009 |
| Median per-file ratio | 0.995 |
| Grew more than 20% | 367 (365 are the routing stubs in section 2) |
| **Shrank more than 20%** | **15** |

The 15 that shrank, smallest ratio first:

| SIP | Archive lines | Upstream lines | Bytes ratio |
| --- | ---: | ---: | ---: |
| 1 | 74 | 621 | 0.229 |
| 7940 | 59 | 115 | 0.439 |
| 2378 | 59 | 70 | 0.475 |
| 1872 | 149 | 216 | 0.689 |
| 7577 | 66 | 110 | 0.709 |
| 3338 | 47 | 55 | 0.714 |
| 2681 | 49 | 56 | 0.726 |
| 1013 | 31 | 38 | 0.739 |
| 1015 | 131 | 119 | 0.740 |
| 608 | 24 | 31 | 0.773 |
| 2025 | 201 | 212 | 0.777 |
| 649 | 71 | 74 | 0.779 |

The other three are in the batch file. A smaller file is not proof of lost content: removed governance
history is expected. But each must be checked for removed normative text before it can pass. SIP-1 is
expected to differ; it is the process document whose governing version is still an owner decision.

## 5. Review batches

[`manifests/archive-batch5-review-batches.tsv`](manifests/archive-batch5-review-batches.tsv) assigns every
SIP to one batch:

| Batch | SIPs | Identity hits | Content review needed |
| --- | ---: | ---: | --- |
| A: routing stubs | 365 | 0 | Status decision only (section 2) |
| B: shrank more than 20% | 15 | 60 | First: check for removed normative text |
| C: zero identity hits | 146 | 0 | Normative parity, rights, links |
| D: 1 to 5 hits | 253 | 649 | Each hit classified: verified counterpart, third-party citation, or blocker |
| E: more than 5 hits | 187 | 2760 | As D, with the largest share of interface names |

The 11 SIPs added since `sila-chain/SIPs@de0fadf0` are marked `new-since-de0fadf0`: 6 in C, 4 in D, 1 in E.

## 6. What Claude can and cannot do next

The triage says the raw archive must not be published, and no staging branch is authorized. Claude has no
copy of the archive, so content review of batches B–E needs the files themselves.

A path within the current authorization: **ChatGPT commits one batch at a time to this branch, starting
with batch C (146 files), only after those files pass this branch's gates** (no identity hits, rights marker
present). Claude then verifies the hashes, compares each file with latest upstream for normative parity, and
reports per file. Batch B should follow, because it carries the content-loss risk.
