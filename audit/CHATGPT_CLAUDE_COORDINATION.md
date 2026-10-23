# Coordination — Sila SIPs

This is a **work-in-progress handoff**, not an approval to publish or merge.

## Authorized scope

- Repository: `sila-network/SIPs`.
- Work branch only: `claude/greeting-mgich3`.
- No changes to `main`, no PR, no merge, and no changes in other repositories without fresh user approval.
- Current branch has SIP-1 only; it must **not** be represented as the full standards corpus.

## Source-of-truth corpus

The owner's ChatGPT Library contains the private candidate archive `Sila-SIPs-LOCAL-RESUMED-BATCH5-20261022.zip`, SHA-256 `76f6079f9bbbd40043c0f6224afd645daedf6cda87a34bc7aed0fddef0785ba0`. This source has 966 SIP documents. **The archive is not in this GitHub branch yet.** Neither Claude nor ChatGPT should claim full corpus parity without importing and testing it.

Last evidenced corpus checks: 61/61 tests passed; identity audit has 4,722 outstanding findings, 348 rights issues, and 116 visual clearance matters; production site build and independent 1:1 parity have not been certified.

## Shared collaboration protocol

1. Claude: before edits, read `audit/AUDIT.md` and this file. Preserve the established SIP-1, governance, CI, and tests while importing the larger corpus. Do not silently overwrite.
2. Each actor: report relevant SHA, file changes, exact commands, PASS/FAIL/BLOCKER results, and remaining blockers on the **same branch**, under `audit/`.
3. Pure Sila only in project-owned operational identities. No unverified replacements, dual identities, aliases, or compatibility shims.
4. Protect technical constants, wire formats and original rights/provenance unless backed by documented authority. Never manufacture copyright clearance.
5. Failure or blocked checks must never be recoded as success. No 100/100 certificate before full source audit, technical parity, links, rights and site build all pass.
6. Do not require the owner to transfer tens of megabytes over a phone connection. Find a secure cloud-based import path.

Claude and ChatGPT do **not** have a direct inter-agent messaging channel; this tracked file and GitHub review artifacts are the shared coordination surface.
