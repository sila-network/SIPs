# Candidate-native audit tools imported from Batch5

This change adds four source files, and preserves the owner's original Batch5 bytes and paths. The files were verified against `audit/manifests/archive-batch5.sha256` locally before import.

## Included

- `tools/check_sila_identity.py`: fail-closed identity and visual review.
- `tools/check_sila_rights.py`: fail-closed rights and license review.
- `tests/test_sila_identity.py`: focused test suite.
- `tests/test_sila_rights.py`: focused test suite.

## Verification and limits

The original archive was CRC-checked and SHA-256 matched to `76f6079f9bbbd40043c0f6224afd645daedf6cda87a34bc7aed0fddef0785ba0`. The full archive's 61 unit tests passed in an isolated local run. This import does **not** claim the four files passed on this exact GitHub tree yet: execute `python -m unittest discover -s tests -p 'test_sila_identity.py' -v` and likewise for `test_sila_rights.py`.

These tools are **not yet an automatic release gate**. The current GitHub tree lacks the whole corpus and rights records, so running audits on it would not certify the candidate corpus. The original archive remains blocked by identity, rights, visual clearance, normative parity, site build and governance checks. No 100/100 claim is authorized.

No third-party operational name was introduced by this code batch according to the source identity scanner. Negative detection patterns inside the audit implementation are not protocol aliases or compatibility interfaces.

The owner authorized changes to `claude/greeting-mgich3` only. Do not change `main` or merge.
