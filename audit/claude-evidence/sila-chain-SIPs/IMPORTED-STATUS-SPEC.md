# PROPOSED: Sila-native `Imported` status (specification and test matrix)

Status of this document: proposal only. Nothing is implemented. Every **[APPROVE]** item needs
the owner's explicit decision on its exact wording before any file changes.

## 1. Semantics

**[APPROVE] Definition text** (proposed wording for SIP-1, "SIP Process"):

> **Imported** - A technical specification published in this repository without any Sila
> governance decision. An `Imported` SIP records no Sila discussion, review, acceptance,
> rejection, withdrawal or finalization. It becomes subject to Sila governance only when the
> maintainer records a decision moving it to another status.

Properties:

| Property | Value |
|---|---|
| Who may set it | Only the import of existing specifications; never assigned to a new submission |
| Transitions out | `Imported` → `Draft` or `Living` by a recorded maintainer decision (policy §1.5) **[APPROVE]**: is `Imported` → `Withdrawn` allowed, to record a decision not to adopt? |
| Transitions in | None after the initial import (no SIP returns to `Imported`) |
| Applies to | 590 non-stub SIPs (today: Final 138, Stagnant 237, Withdrawn 35, Review 35, Draft 137, Last Call 5, Living 3) |
| Never applies to | The 365 `Moved` routing stubs (unchanged) |
| Technical content | Unchanged. `requires` is unchanged. Consensus-critical definitions are unchanged |

## 2. Preamble rules for `Imported` SIPs

| Field | Rule | Reason |
|---|---|---|
| `status` | `Imported` | §1 |
| `discussions-to` | absent | No genuine Sila discussion exists |
| `last-call-deadline` | absent | Inherited event |
| `withdrawal-reason` | absent | Inherited event |
| `created` | **[APPROVE]** date first published in `sila-chain/SIPs` (954 files: `2026-09-07`, commit `9f232c19`; 1 file: `2026-09-13`, commit `07a8087e`), or omitted | Truthful, verifiable |
| `author` | unchanged (genuine attribution) | Legal and attribution; fabricated addresses removed per B10 |
| `requires`, `type`, `category`, `title`, `description` | unchanged | Technical metadata |

## 3. Change matrix (all files that must change together)

| Component | File(s) | Change |
|---|---|---|
| Process document | `SIPS/sip-1.md` **and** `SRCs/SRCS/sip-1.md` (byte-identical) | Add the definition; rules for `discussions-to` and `created` |
| Validator, both repos | `config/sipw.toml` | `preamble-enum-status` + `Imported`; `preamble-req` without `discussions-to`; 7 × `preamble-required-if-eq` for `discussions-to` (one per Sila-governed status); `Imported` in the first tier of `preamble-requires-status` and `markdown-link-status`; `preamble-re-discussions-to` pattern only after the forum URL is verified |
| Validator engine | `sila-chain/sipw` | New lint kind to **forbid** `discussions-to`, `last-call-deadline`, `withdrawal-reason` when `status` is `Imported` (not expressible today) |
| Site | `_data/statuses.yaml`, `all.html`, `core.html`, `networking.html`, `interface.html`, `meta.html`, `informational.html`, `src.html`, `_includes/siptable.html`, `_layouts/sip.html` (status badge), `rss/*.xml` | Show `Imported` as its own group; no "Final/Last Call" presentation for imported specs |
| Review bot | `sila-chain/sip-review-bot` `rules/statuschange.ts` | `Imported` → other status requires governance approval (today an unknown status falls back to editor approval; must be explicit) |
| Review guidance | `.github/instructions/review.instructions.md`, `sip-template.md` | New submissions never use `Imported` |
| Corpus | 590 `SIPS/sip-*.md` preambles | Mechanical preamble change only; bodies untouched |

## 4. Test matrix

| # | Test | Pass criterion |
|---|---|---|
| T1 | Body invariance | For all 590 files, everything after the closing `---` of the preamble is byte-identical before/after |
| T2 | Preamble delta | Only `status`, `discussions-to`, `last-call-deadline`, `withdrawal-reason` and (if approved) `created` differ; every other preamble line byte-identical |
| T3 | Stub invariance | 365 `Moved` files byte-identical |
| T4 | Dependency graph | The `requires` graph (309 files) is identical; status-ordering lints pass corpus-wide with `Imported` in tier 1 |
| T5 | Validator, positive | `Imported` without `discussions-to` passes; `Draft` with a verified-forum topic passes |
| T6 | Validator, negative | `Draft`/`Review`/`Last Call`/`Final`/`Living`/`Stagnant`/`Withdrawn` without `discussions-to` fail; a wrong forum host fails; an unknown status fails; an adopted `Final` SIP that `requires` an `Imported` SIP fails |
| T7 | Validator, forbid (after the `sipw` lint exists) | `Imported` **with** `discussions-to` / `last-call-deadline` / `withdrawal-reason` fails |
| T8 | Mutation | Removing any new lint makes at least one T5–T7 fixture fail |
| T9 | SIP-1 sync | SIPs and SRCs copies byte-identical; the check fails on a one-byte change |
| T10 | Merge behaviour | `merge-repos` reproduced; SRCs content replaces the stubs exactly as before |
| T11 | Site | Full build + HTMLProofer (UTF-8); full-site comparison: only status groupings/badges and removed governance fields differ |
| T12 | Bot | Fixture PRs: `Imported`→`Draft` by a non-governance account never satisfies; by the owner on their own PR never self-satisfies |
| T13 | Consensus cross-check | Meta-SIP activation tables still equal `go-sila` `params/config.go` |
| T14 | Audits | Pure Sila Audit (no allowlists) and licence/copyright-line comparison against the approved legal baseline |
