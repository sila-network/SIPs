# Identity-scanner repair — isolated negative detection fixture

This change addresses the codespell regression reported in `audit/CLAUDE_REVIEW_b420b4b.md`.

## Changes

- `tools/check_sila_identity.py`: imports a validated, explicit negative detection vocabulary instead of constructing prohibited spellings from string fragments
- `tests/fixtures/sila-denied-identities.json`: literal forbidden terms as negative test data only; no runnable identity, package, API, compatibility alias or shim
- `tests/test_sila_identity.py`: adds a regression test confirming only this **one exact** vocabulary file is excluded by the scanner and other test files remain checked
- `tests/run.sh`: excludes only this negative vocabulary fixture from spelling checks, because deliberately disallowed names are intentionally not English words; all other source files remain subject to codespell

The old Batch5 source blobs are unchanged in the archived manifest; this commit records a documented divergence in the active branch.

## Pre-push verification

- Identity scanner Python tests: **10 passed**
- Rights scanner Python tests: **14 passed**
- `python -m compileall -q tools tests`: **passed**
- Full GitHub Actions CI and the final Pure Sila audit: **not yet certified at the time of commit**. External source parity, site build, rights and visual clearances remain blocked.

Scope: `claude/greeting-mgich3` only. No PR, merge, or `main` updates.
