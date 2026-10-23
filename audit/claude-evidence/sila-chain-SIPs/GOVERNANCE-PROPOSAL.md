# Sila SIP governance: proposal for owner approval

> **Corrections, 2026-10-23.** Two findings below were wrong because I checked the wrong names:
>
> - The forum exists at `https://sila-magicians.discourse.group` (HTTP 200, 9 categories,
>   1 topic). Only `sila-magicians.org` has no DNS.
> - `sila-chain/sila-devp2p`, `sila-chain/sila-portal-network-specs`, `sila-chain/sila-yellowpaper`
>   and `sila-chain/sila-pm` exist. The unprefixed names (`devp2p`, `pm`, ...) do not.
>   `sys-asm` and `execution-spec-tests` exist under neither name.

Status: PROPOSAL. Nothing here is in the repository. Every item marked **[APPROVE]** needs an
explicit owner decision before implementation. Facts are cited to the evidence they rest on.

Repositories: `sila-chain/SIPs` (active), `sila-chain/SRCs` (coordinated changes only, as patches).

---

## 1. Proposed governance policy

### 1.1 Two classes of specification

| Class | Definition | How a document enters it |
|---|---|---|
| **Imported specification** | Technical text published in `sila-chain/SIPs` by the import of 2026-09-07 (commit `9f232c19`, 954 files) or the sync of 2026-09-13 (commit `07a8087e`, 1 file). No Sila governance decision has been made about it. | Already the case for all 590 non-stub SIPs. |
| **Adopted specification** | A specification for which the maintainer has recorded a Sila decision under section 1.5. | Only by a recorded decision. Nothing is adopted automatically. |
| **Routing stub** | The 365 `status: Moved` files that route SIP numbers to `sila-chain/SRCs`. | Unchanged. Not governance; must be preserved byte-for-byte. |

### 1.2 Meaning of `status`

- For **adopted** specifications, `status` is the Sila governance state, with the existing definitions
  (`Draft`, `Review`, `Last Call`, `Final`, `Stagnant`, `Withdrawn`, `Living`) applied only to events
  that happened in Sila.
- For **imported** specifications, `status` must not assert any Sila decision. Inherited values
  (Final 138, Stagnant 237, Withdrawn 35, Review 35, Draft 137, Last Call 5, Living 3) are not Sila decisions.
- **[APPROVE] Mechanism.** No new value is implemented without approval. Options:
  - **A1 (recommended):** one new status value for imported specifications, proposed name `Imported`.
    It is the only option that keeps a single, checkable `status` field truthful.
  - **A2:** a separate adoption registry file listing adopted SIPs; `status` on imported specs is then
    still visibly an inherited value, so this does not satisfy "do not present inherited decisions
    as Sila governance" unless the site labels it, which needs template work.
  - **A3:** set every imported spec to `Draft`. Not recommended: `Draft` asserts active authorship
    in Sila, which is untrue.
- `last-call-deadline` (5 files) and `withdrawal-reason` (18 files) record inherited events. Under A1
  they are removed together with the status change, because they are only required for
  `Last Call`/`Withdrawn`.

### 1.3 Meaning of `created`

- **Proposed rule:** `created` is the date the document was first published in `sila-chain/SIPs`,
  verifiable from git history.
- Applying it today: 954 files → `2026-09-07` (commit `9f232c19`), 1 file → `2026-09-13`
  (commit `07a8087e`). For new SIPs: the date of the pull request that first adds the file.
- **[APPROVE]** whether imported specs carry this date, or whether `created` is optional for
  imported specs. The validator only checks the date format, so either is expressible.

### 1.4 When `discussions-to` is required

- **Required** for every adopted status (`Draft`, `Review`, `Last Call`, `Final`, `Stagnant`,
  `Withdrawn`, `Living`) and must be a topic URL on the verified Sila Magicians forum.
- **Absent** for imported specifications. No historical topics exist, so no value is truthful.
- The 468 current `sila-magicians.org/t/...` values and 34 GitHub values are removed from imported specs.
- Blocked on the **verified forum URL** (section 4, A3). No forum link is added before then.

### 1.5 How a solo maintainer records genuine decisions

A decision is valid only if all of the following exist, and nothing else counts:

1. A pull request to `sila-chain/SIPs` that makes the change (for example `Imported` → `Draft`),
   merged by the maintainer's verified GitHub account.
2. A decision note in the pull request description: what was decided, by whom, on what date.
3. Once the forum URL is verified: a forum topic linked from `discussions-to`.
4. No review, vote or approval by anyone else is claimed. While there is one maintainer, records say
   "maintainer decision", never "editors approved" or "consensus reached".

**[APPROVE]** whether decisions must use signed commits, and whether a decision log file is kept in the
repository in addition to pull request history.

### 1.6 Technical dependencies stay valid regardless of governance

- `requires` (309 files) is technical and kept unchanged for imported and adopted specs alike.
- Consensus-critical definitions (opcodes, gas schedules, transaction formats, RPC and wire
  definitions, test vectors, fork activation tables) are kept 1:1. Example: SIP-7569's activation
  table matches `go-sila` `params/config.go` exactly (`SilaCancunTime = 1710338135`).
- Rule for the status-ordering lints: **[APPROVE]** where `Imported` sits in the ordering used by
  `preamble-requires-status` and `markdown-link-status`.
  - Recommended: same tier as `Draft`. Then an adopted `Final` spec cannot depend on an imported
    one, so adoption proceeds bottom-up through the dependency graph. That is strict but truthful.
  - Alternative: a separate tier exempt from ordering. That is weaker and not recommended.

---

## 2. Editor and approval-authority audit

Evidence: `sila-chain/sip-review-bot@e9399a60`, pinned in `.github/workflows/auto-review-bot.yml`.

| Finding | Evidence | Risk |
|---|---|---|
| `config/sip-editors.yml` names 5 upstream accounts (lightclient, SamWilsn, xinbenlv, g11tech, jochem-brouwer) as editors in every category | file contents; same list in `sila-chain/SRCs` | Their approvals count toward bot merges |
| Bot enables **auto-merge (squash)** when its rules are satisfied | `src/merge.ts` `performMergeAction` | Merge without owner action, if `secrets.TOKEN` exists and auto-merge is allowed |
| `rule.min = Math.min(rule.min, rule.reviewers.length)` | `src/action.ts:386` | **Empty editor list = every rule needs 0 approvals = everything auto-merges** |
| `unknown` and `terminal` rules use `floor(len(governance)/2)` | `src/rules/unknown.ts`, `terminal.ts` | **Single-editor list = 0 approvals** for workflows, config, layouts, README and Final/Withdrawn SIPs |
| PR author counts as an approver when listed in the rule | `src/action.ts` (PR Author Approval) | Combined with the above, self-merge |
| `authors` rule: GitHub handles in a SIP's `author` line can approve changes to that SIP | `src/rules/authors.ts` | Upstream authors hold approval power over imported specs |
| `CODEOWNERS`: `* @sil-bot` | `.github/CODEOWNERS` | Account not verified; owner should confirm who controls it |
| SIP-1 "SIP Editors" lists the same 5 people as current Sila editors, plus 10 emeritus | `SIPS/sip-1.md:522-543` | Inherited governance claim |

**Conclusion:** neither emptying the list nor replacing it with one account is safe with the current
bot. Proposed order, nothing granted to an unverified account:

1. **Owner, in repository settings (only the owner can verify):** confirm whether `secrets.TOKEN`
   exists, whether "Allow auto-merge" is enabled, and what branch protection is on `main`.
   Recommended: disable auto-merge and require the owner's review on `main` before step 2.
2. **[APPROVE]** confirm the owner's GitHub account. Evidence suggests `sila-chain`: source commits use
   `sila-chain@users.noreply.github.com`, a user-account noreply address. Not assumed.
3. Then, in **both** repos: replace the editor lists with the verified owner account only, replace
   `CODEOWNERS` with the same account, and keep the bot unable to auto-merge until
   `sila-chain/sip-review-bot` enforces a minimum of 1 owner approval (a fix in that repository).
4. SIP-1 and SIP-5069 editor sections rewritten to state the solo-maintainer model (section 3).

---

## 3. SIP-1 correction and validator change matrix

### 3.1 Merge behaviour that must be preserved

`.github/actions/merge-repos` copies `sila-chain/SRCs/SRCS/*` over `SIPS/` before both the site build
and `sipw`. `SRCS/sip-1.md` therefore **replaces** `SIPS/sip-1.md` on the published site. Upstream works
the same way and keeps two separately maintained copies, which differ by 46 lines at upstream HEAD.

**Proposal:** one canonical SIP-1 text, byte-identical in both repositories, changed only by
coordinated pull requests (SIPs first, the SRCs mirror second). Add a check to `sila-ci` in each repo
that fails when the two copies differ. That is a new, stricter check, not an exception.

### 3.2 SIP-1 changes

| SIP-1 section (SIPs line / SRCs) | Change | Depends on |
|---|---|---|
| `author:` preamble | Names only (fabricated addresses already removed in SIPs; SRCs copy still has them) | none (SRCs patch) |
| Status definitions (`SIP Process`) | Add the imported/adopted distinction (1.1–1.2) | A1 approval |
| `discussions-to` header (§171–175) | Required only for adopted statuses; forum URL | forum URL |
| `created` header (§185) | Meaning per 1.3 | 1.3 approval |
| `requires` header (§189) | Unchanged; state that dependency validity is independent of governance | none |
| Shepherding / Core SIPs (§48–66): AllCoreDevs calls, "Sila Core Developers" → `sila-chain/pm` (repo does not exist) | Replace with the actual Sila process: maintainer decision + forum | 1.5 approval, forum URL |
| Linking to External Resources (§195–507) | Keep only exceptions that point to repositories that exist; must match each repo's `sipw.toml` `markdown-rel-links` | B5: `devp2p`, `yellowpaper`, `sys-asm`, `portal-network-specs`, `execution-spec-tests` are missing |
| SIP Editors (§522–545) | Solo-maintainer statement; remove inherited current and emeritus lists | editor audit steps 1–2 |
| History (§597) | **Keep.** Genuine attribution of the document's derivation (BIP-0001, PEP-0001) | — |
| Copyright (§601) | **Keep.** CC0 waiver | — |

### 3.3 Validator changes (`config/sipw.toml`, both repos)

| Lint | Today | Proposed | Weakening? |
|---|---|---|---|
| `preamble-req` | requires `discussions-to` unconditionally | remove `discussions-to` from the unconditional list | No, only together with the next row |
| new `preamble-req-discussions-to-<status>` ×7 (`preamble-required-if-eq`) | — | `discussions-to` required when status is each adopted value | Same strictness for every Sila-governed SIP |
| `preamble-re-discussions-to` | pattern `^https://sila-magicians.org/t/...` | pattern for the **verified** forum URL | — |
| `preamble-enum-status` | 7 values | + `Imported` | A1 approval |
| `preamble-requires-status`, `markdown-link-status` flows | 4 tiers | `Imported` in the `Draft` tier | Stricter |
| `preamble-req-last-call-deadline`, `-withdrawal-reason` | unchanged | unchanged | — |
| `preamble-date-created` | format check | unchanged | — |
| `sipw-action` `unchecked: 1, 5069, 5757` | 3 SIPs unchecked | **[APPROVE]** remove once SIP-1/5069 pass; currently SIP-1 has 38 errors | Removal is stricter |
| **Gap** | `sipw` cannot *forbid* a field | "no `discussions-to` on Imported" needs a new lint kind in `sila-chain/sipw` | Tracked, not faked |

Other consumers of `status` that must change with A1: `_data/statuses.yaml`, index pages
(`all`, `core`, ... `.html`), `rss/*.xml`, the review bot's `statuschange.ts` (unknown statuses fall back
to editor approval), `.github/instructions/review.instructions.md`.

---

## 4. Files safely fixable now (no approval needed)

| Files | Fix | Why safe |
|---|---|---|
| `SIPS/sip-1015.md` (3 links: issues 960, 156, PR 867), `SIPS/sip-2566.md` (issue 1138), `SIPS/sip-2938.md` (PRs 2937, 2975) | Unlink references to `sila-chain/SIPs` PR/issue numbers that do not exist (the repository has PRs 1–6 only), keeping the sentence text | The files pass CI today; only the false "a Sila discussion exists here" link is removed; rationale text is unchanged |

Checked and excluded from this list:

- `sip-2786.md`: its only reference is the `discussions-to` value, which needs the policy.
- `sip-3403.md:105`: the link identifies which refund variant the comparison table models, so it is technical context and needs case-by-case wording.

Everything else is blocked:

- The other 46 files with such references fail CI on `preamble-req` (21 files) and related rules that the policy resolves.
- The 15 B10-deferred files: same cause.
- Editor files: section 2.
- Licence files: section 5.

---

## 5. Legal blocker inventory (nothing here is changed without legal direction)

| ID | Files | Issue |
|---|---|---|
| L1 | `SIPS/sip-1355.md`, `SIPS/sip-1485.md` | Licensed **CC BY-NC-SA 4.0**. The generator rewrote both without the required indication of changes; NC restricts commercial use |
| L2 | 21 SIPs with no copyright/waiver statement: 2, 3, 4, 5, 6, 7, 86, 100, 101, 150, 155, 158, 160, 161, 170, 210, 616, 1014, 5022, 7783, 7790 | Licence status not established by the repository |
| L3 | `assets/sip-7543/decimal_float_test.go`, `assets/sip-7885/op-sila/cgo/contracts.go`, `.../cgo/contracts_test.go`, `.../nocgo/core/vm/contracts.go`, `.../nocgo/core/vm/contracts_test.go` | **LGPL-3.0 copyright notices were rewritten** (`Copyright 2014 The go-ethereum Authors` → `... go-sila Authors`; "This file is part of the go-ethereum library" likewise). LGPL requires notices kept intact; the current text misattributes copyright. Restoring them conflicts with the naming policy; needs a legal decision |
| L4 | `assets/sip-7885/solidity/src/ZKNOX_NTT.sol` and 2 tests | MIT licence; notices intact; keep |
| L5 | 27 PDFs (third-party papers, 26 contain foreign identities in text) | Redistribution rights per paper not established |
| L6 | 16 assets with `SPDX-License-Identifier: CC0-1.0` | Intact; keep |

---

## 6. Remaining authority, dependency and legal blockers

- **Authority:**
  - A1/A2/A3 choice and the status name.
  - Meaning of `created`.
  - Decision-record format.
  - The owner's verified GitHub account.
  - Repository settings (`TOKEN`, auto-merge, branch protection).
  - The verified forum URL.
  - SRCs-side approval for the mirrored changes.
- **Dependency:**
  - `go-sila` activation parameters for a new network (SIPs follow the implementation).
  - Missing `sila-chain` repositories referenced as spec sources (B5).
  - `sila-chain/sipw` lint gap (forbid-field).
  - `sila-chain/sip-review-bot` minimum-approval fix.
  - The 139-commit upstream sync (B8).
- **Legal:** L1–L5.
- **Carried over:** B4 (SVM/EVM naming), B7 (interfaces without counterparts), B11 (PDF text),
  B12/B10 deferred files, B14 (stagnant bot).

---

## 7. Tests required to establish genuine parity

1. **Technical-content invariance:** for every SIP touched by governance changes, the body below the
   preamble is byte-identical except for listed substitutions; specification sections are compared
   after rendering, as done for batch 1.
2. **Full-site comparison:** all pages; the only allowed differences are listed governance fields and
   the substitutions. Batch 1 reached 0 unexplained differences across 1313 pages; the same bar applies.
3. **Upstream technical parity:** off-repo regeneration from the target upstream commit; per-file
   classification as identical, documented substitution, or governance-field change. No unexplained deltas.
4. **Dependency graph:** the `requires` graph is identical before and after; `preamble-requires-status`
   and `markdown-link-status` pass across the whole corpus under the new status rules.
5. **Validator:** whole-repository `sipw` with the new config. Every remaining error listed and owned;
   positive and negative fixtures for each new rule (Imported without `discussions-to` passes; Draft
   without it fails; wrong forum host fails).
6. **SIP-1 sync check:** SIPs and SRCs copies byte-identical; the check fails on a deliberate one-byte change.
7. **Merge-behaviour test:** the `merge-repos` step reproduced locally; the 365 stubs are replaced by SRC
   content exactly as before; stub files are unchanged.
8. **Bot authority test:** the review bot's rule evaluation run against fixture PRs (outsider PR to a
   workflow file, imported-SIP author PR, owner PR) with the proposed editor config. No path
   reaches `min <= 0` for a non-owner.
9. **Consensus cross-check:** fork activation tables and parameters in meta SIPs match `go-sila`
   `params/config.go`.
10. **Pure Sila Audit and licence check:** the audit is re-run (no allowlists); licence/copyright lines
    are compared to the legal-approved baseline, and any change fails.
11. **CI-scoped checks at CI versions:** markdownlint 0.6.0, codespell, link check, HTMLProofer (UTF-8),
    Jekyll on Ruby 3.1 with the frozen lockfile.
