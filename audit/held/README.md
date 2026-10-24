# SIP-8096: held outside the publishable SIPS set

**Status: BLOCKED, not discarded or approved.** The exact Sila candidate document from the previous SIPS directory is preserved in [`sip-8096.md.hold`](sip-8096.md.hold), with its original tracked Git blob SHA `9bc9ff8ad38af082ee0a1083603ff60a4d7b9b14`.

Reasons:
- Normative dependency SIP-4844 is not available in this new repository; shipping SIP-8096 would publish a broken link and an orphaned protocol change.
- The current Batch5 candidate for SIP-4844 contains inherited identities and other-network historical claims. This is **not** authority to substitute or invent Sila behavior.
- The prior SIP-8096 candidate asserts that Sila had multiple earlier gas-repricing events without any verified Sila evidence.
- Current policy requires Pure Sila, non-fictitious status and documented normative parity.

To reopen, resolve SIP-4844's proper Sila-native technical identity, dependencies and rights, remove unsupported claims after technical review, import and validate the complete dependency graph, then move SIP-8096 into SIPS in an atomic reviewed change.

**This hold is an explicit unresolved release blocker**, not deletion of a required standard and not permission to claim 100/100.
