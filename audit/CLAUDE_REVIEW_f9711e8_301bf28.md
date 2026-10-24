# Claude review of commits f9711e8 to 301bf28

Reviewed 2026-10-24. Nine commits after `d06d5fa`, ending at
`301bf28786c95ee9ee3df1e323c439ea02b03475`. Notes reviewed:

- [`OWNER_BRAND_DECISIONS_20261024.md`](OWNER_BRAND_DECISIONS_20261024.md)
- [`SILA_AUTHORSHIP_POLICY_20261024.md`](SILA_AUTHORSHIP_POLICY_20261024.md)
- [`OWNER_CONDITIONAL_RELEASE_APPROVAL_20261024.md`](OWNER_CONDITIONAL_RELEASE_APPROVAL_20261024.md)

**Verdict: FAILED, not 100/100.** The logo blocker is closed. Two new problems appear: the editor list
names an organization, which cannot approve pull requests, and a new test forbids any author other than
Sila Network. The release approval note itself says approval is not yet actionable, and that is correct.

## 1. Results on 301bf28

| Check | Result |
| --- | --- |
| `tests/run.sh`, 14 of 15 checks | PASS |
| identity scan | **FAIL**: `VISUAL_CLEARANCES.json:6` names the AI assistant used in the owner's conversation |
| Unit tests | PASS |
| Jekyll build | exit 0, 28 SIP pages |
| `tools/verify_site.py` | **FAIL**: missing `./sip-4844.md` linked from SIP-8096 |
| CI: Checks run 37, Sila site build run 23 | failure, same causes |
| Blockers | 1 (canonical domain); the logo blocker is gone |
| `tests/run.sh` result | `RESULT: FAILED`, 1 failed check, 1 blocker |

## 2. Logo (f9711e8, 8ac2f05): accepted

- `assets/sila-logo.png` is a real PNG, 512 × 512.
- No C2PA, generator or editing-tool metadata strings remain, so Blocker 1 clears.
- The record gives the source JPEG hash and the derivative hash. Claude cannot see the uploaded source, so
  the source hash rests on the owner's upload.
- The README now says the logo is reserved and not under CC0. That is consistent with
  `VISUAL_CLEARANCES.json`.

## 3. Editors: the listed account cannot approve

`config/sip-editors.yml` now lists only `sila-network` for every category, and `tests/run.sh` requires
exactly that.

The GitHub API reports `sila-network` as type **Organization**. Every commit on this branch is made by the
**User** `sila-chain` (id 214020442). Pull-request reviews come from user accounts; an organization
cannot submit one.

| Review bot | Effect |
| --- | --- |
| Current `sila-chain/sip-review-bot` | Needs one approval from `sila-network`, which can never arrive. Every SIP pull request stays blocked |
| The security patch in [`claude-evidence/sip-review-bot/review-bot-security.patch`](claude-evidence/sip-review-bot/review-bot-security.patch) | Same outcome: it fails closed |

It fails closed, so this is not a security hole, but the editor function no longer works. Options for the
owner:

1. List the user account that acts for the organization (`sila-chain`) as editor.
2. Use a team handle, for example `sila-network/sip-editors`. First confirm the review bot resolves teams
   to their members; its code has not been checked for this.

## 4. Author bylines: two conflicts

All 28 SIPs now have `author: Sila Network (@sila-network)`. The original authors are recorded in
`audit/manifests/sila-authorship-provenance-20261024.tsv`. The policy note says the byline names the
issuer of the adaptation, not the original writer. CC0 allows this. The site does not show the `author`
field on any page.

Two conflicts remain:

1. **SIP-1 still defines `author` as the proposal's authors** (lines 123 and 147), and line 165 requires an
   author with a GitHub username who can approve or reject changes. An organization handle cannot do that.
   Either SIP-1 is amended to define an issuer field, or the bylines contradict the repository's own
   process document.
2. **The new test blocks every future community author.** `tools/verify_sila_publication_identity.py`
   fails any SIP whose `author` is not exactly `Sila Network (@sila-network)`, and `tests/run.sh` runs it on
   every file in `SIPS/`. A new SIP written by anyone else, as SIP-1 invites, can never pass CI. The check
   should apply only to the adapted SIPs listed in the provenance register, not to all of `SIPS/`.

## 5. Identity scan finding

`VISUAL_CLEARANCES.json` line 6 says the owner made the declaration in a conversation with a named AI
assistant. The fact is true, and the scan exists to catch exactly this kind of name in published files.
Options:

- move the conversation detail to the audit record, which the scan already exempts, and keep only the
  owner and date in `VISUAL_CLEARANCES.json`
- or the owner accepts the name as provenance and the scan rule is changed in the open

Not changed here.

## 6. Conditional release approval

The note states the owner's approval in the owner's words and lists seven conditions. Its own conclusion
is that approval is not actionable while checks fail. That matches the facts:

- CI is red
- 28 of 966 SIPs are on the branch
- the domain still serves another repository

Claude takes no merge or deploy action under it.

## 7. Still open

- SIP-8096 needs SIP-4844, which is not on the branch
- sipw fails on all 27 imported SIPs (sections 3 and 4 of
  [`CLAUDE_REVIEW_f3ddc50_5252604.md`](CLAUDE_REVIEW_f3ddc50_5252604.md))
- Text that presents another network's history as Sila's: SIP-3554, 3756, 3855, 4345, 5133, 6873, 8096
- Substitution rules (`SIVM` and others) are still not written down

## 8. Follow-up: commit 51767a1

`51767a188cabd385d3d749d3989b34e245a03bc2` (note:
[`REVIEW_AND_LOGO_CLEARANCE_CORRECTIONS.md`](REVIEW_AND_LOGO_CLEARANCE_CORRECTIONS.md)):

| Change | Assessment |
| --- | --- |
| `config/sip-editors.yml` lists the user account `sila-chain` again; `tests/run.sh` asserts it | Fixes section 3. The file is byte-identical to its version before `8ac2f05` |
| The AI assistant's name removed from `VISUAL_CLEARANCES.json` | Fixes section 5. The fact is still recorded: in [`OWNER_CONDITIONAL_RELEASE_APPROVAL_20261024.md`](OWNER_CONDITIONAL_RELEASE_APPROVAL_20261024.md) and in this file's git history. Not concealment |

Results on `51767a1`:

| Check | Result |
| --- | --- |
| `tests/run.sh` | **0 failed checks**, 15 PASS, 1 blocker (canonical domain): `RESULT: BLOCKED (not 100/100)`, exit 2 |
| Checks run 39 | Same result: 0 failed, BLOCKED, exit 2 |
| Unit tests | PASS |
| `tools/verify_site.py`, Sila site build run 25 | **FAIL**: missing `./sip-4844.md` linked from SIP-8096 |

This is the first commit where no repository check fails. It is still not 100/100:

- the site build fails
- sipw fails on all 27 imported SIPs
- section 4 is still open: the byline test rejects every future author, and the bylines conflict with
  SIP-1
- 28 of 966 SIPs are on the branch
- the domain blocker remains
