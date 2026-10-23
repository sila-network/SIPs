# Claude review of commit b420b4b

Reviewed commit `b420b4bc2563d2f4f21216e5240b87b68aa579c9` ("import Sila-native identity and rights
scanners"), 2026-10-23. Note: [`BATCH5_NATIVE_TOOLS_IMPORT.md`](BATCH5_NATIVE_TOOLS_IMPORT.md).

**Verdict: the branch moved from BLOCKED to FAILED.** Not 100/100.

## 1. Byte verification

All four imported files match `manifests/archive-batch5.sha256` exactly:
`tools/check_sila_identity.py`, `tools/check_sila_rights.py`, `tests/test_sila_identity.py`,
`tests/test_sila_rights.py`.

## 2. Imported tests on this tree

Commands requested by the import note, Python 3.13.16:

| Command | Result |
| --- | --- |
| `python3 -m unittest discover -s tests -p test_sila_identity.py` | PASS, 9 tests |
| `python3 -m unittest discover -s tests -p test_sila_rights.py` | PASS, 14 tests |

## 3. Branch suite regression

`tests/run.sh` (same `sipw` commit as CI), locally and on GitHub Actions run 9:

| Check | Before (`fba8c45`) | After (`b420b4b`) |
| --- | --- | --- |
| codespell | PASS | **FAIL** |
| All other 12 checks | PASS | PASS |
| Blockers | 3 | 3 |
| Result | `BLOCKED` | **`FAILED`** (exit 1) |

Cause: `tools/check_sila_identity.py` lines 21 and 24 build its prohibited-word list from string fragments
(for example the first half of a split network name). codespell reads two of those fragments as misspellings:
line 21 with codespell 2.2.6 (CI) and 2.4.1, line 24 with 2.4.1 only.

The fragments exist so the literal names do not appear in project source, because this branch's identity
scan exempts only `tests/` and `audit/`. Splitting strings to keep a word away from a scanner is the same
technique that `sila-chain/SIPs` used to hide an upstream name from text searches, which this project
removed as concealment (see [`CLAUDE_STATUS.md`](CLAUDE_STATUS.md)).

I did not change the imported bytes, the tests or the whitelist. Options, for ChatGPT and the owner:

1. **Literal term list in an exempt location (recommended):** keep the prohibited words as plain words in a
   data file the scanner reads (for example `tests/fixtures/` or a new path), and extend the identity-scan
   exemption to it explicitly in `tests/run.sh` and `audit/AUDIT.md`, with the same reason given for
   `tests/` and `audit/`: scanners must name what they detect. The imported bytes change and must be
   recorded as a documented deviation from the archive.
2. **Move both tools under `tests/`:** no exemption change; the archive paths change.
3. **Add the fragments to `config/.codespell-whitelist`:** not recommended. It hides real misspellings of
   those fragments everywhere in the repository and keeps the concealment pattern.

## 4. What the imported scanners report on this tree

| Scanner | Exit | Result |
| --- | --- | --- |
| `tools/check_sila_identity.py .` | 1 | `BLOCKED`: 25 path or text findings, 2 visuals without clearance |
| `tools/check_sila_rights.py .` | 1 | 2 unresolved issues: `assets/sila-logo.png` and `assets/sip-1/sip-process.svg` lack a positive rights clearance record |

The two identity scanners disagree:

- **`SIPS/sip-1.md` lines 327–342** (the section that permits citing a third-party improvement-proposal
  series, also allowed by `config/sipw.toml`): flagged by the imported scanner, passed by `tests/run.sh`.
  This is a policy question for the owner: are commit-pinned citations of third-party standards allowed in
  Sila documents? It is not a defect in SIP-1.
- **`audit/` files:** flagged by the imported scanner, exempt in `tests/run.sh`. The two tools need one
  shared rule for audit material that must name what it audits.

The rights findings match Blocker 1 in [`AUDIT.md`](AUDIT.md) for the logo. For the process diagram, which
`AUDIT.md` records as drawn for this repository, the archive's mechanism expects an explicit clearance
record (`VISUAL_CLEARANCES.json` in the archive), which this branch does not have.

## 5. Decisions needed

1. Which option in section 3 restores a passing codespell check.
2. Whether commit-pinned third-party standard citations are allowed in SIP-1.
3. One exemption rule for audit material, shared by both scanners.
4. Clearance records for `assets/sila-logo.png` and `assets/sip-1/sip-process.svg`.
5. Still open from [`CLAUDE_BATCH5_REVIEW.md`](CLAUDE_BATCH5_REVIEW.md): where the full archive content is
   committed, which SIP-1 governs, and the 26 foreign-name asset paths.
