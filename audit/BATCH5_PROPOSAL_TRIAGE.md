# Sila Batch5 — proposal-by-proposal triage

**Evidence only. This is not a rights clearance, full-source import or 100/100 certificate.**

This report was produced from the owner's verified local Batch5 archive, SHA-256 `76f6079f9bbbd40043c0f6224afd645daedf6cda87a34bc7aed0fddef0785ba0`, without publishing its unresolved source content.

## Corpus classification

| Gate | Finding |
| --- | ---: |
| Proposal files enumerated | 966 |
| Candidate proposal files containing blocked-identity text matches | 451 |
| Candidate proposal files with zero text matches under the current detection pattern | 515 |
| Text matches across candidate proposals | 3,469 |
| Proposal files missing a `status:` front-matter field | 965 |
| Proposal files with a `status:` field | 1 |
| Embedded absolute HTTP(S) URL occurrences | 1,094 |

The **965 missing status fields** require an explicit governance decision. They must not be silently filled with inherited statuses, and the existing proposal validator configuration must not be weakened to ignore them. The individual case counts are recorded in [`archive-batch5-966-proposal-gates.tsv`](archive-batch5-966-proposal-gates.tsv).

The 515 proposals with zero detected identity matches are **not cleared**: exact normative parity, rights, citations, technical interfaces, provenance and site dependencies are still unverified. The historical 4,722 repository-wide identity findings include other paths and use a wider scope than this proposal-only count. Do not conflate them.

## Columns in the TSV

- `path`: path inside the candidate archive
- `sha256`: exact content hash from the extracted archive
- `bytes`, `lines`: proposal size
- `identity_hits`: count from the repository's Batch5 prohibited-identity pattern over text lines
- `external_links`: count of absolute HTTP(S) URL occurrences, not validated URLs
- `status`: literal value of the `status:` front-matter field, or `NOT_SPECIFIED`
- `has_rights_marker`: a **textual search signal only**, not legal clearance
- `restricted_rights_marker`: a narrow text-search signal only; zero never establishes absence of restrictions
- `requires`: literal `requires:` value when present

## Next action for Claude

1. Use the TSV to plan **review batches**, prioritizing docs with zero identity matches, but do not claim they are pure Sila or legally cleared.
2. Review the absent `status:` fields against proposed Sila governance without inventing a Sila vote, status or approval.
3. Share findings via this authorized branch; preserve existing SIP-1, CI and audit changes.
4. The user previously authorized write access to `claude/greeting-mgich3` only. No separate staging branch has been authorized in this conversation. **Do not create another branch or publish the raw 44 MB archive containing unresolved identities/rights issues.**
5. Continue code/content reviews locally and commit only material that passes the relevant gates to the existing authorized branch. Independent full parity and legal publication clearance remain blockers.
6. An hourly GitHub change-watch is already enabled through ChatGPT; a duplicate scheduled watch by Claude is unnecessary.

The owner does not need to download files or relay manifests between agents.
