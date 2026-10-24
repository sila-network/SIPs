# Review authority and identity-record corrections

Date: 2026-10-24. Authorized branch: `claude/greeting-mgich3` only.

- The brand clearance register now names the **Sila project owner** as the attesting party without including a platform identity in the Sila-owned operational configuration. Its original owner declaration and exact logo SHA remain documented in `audit/OWNER_BRAND_DECISIONS_20261024.md`. No asset bytes or claimed clearance fields changed.
- `config/sip-editors.yml` now names the existing Sila user account `sila-chain` as the responsible GitHub reviewer in all seven sections. A GitHub organization cannot submit pull-request reviews; `sila-network` remains the official owning organization and the sole Sila adaptation issuer in the published SIP bylines.
- `tests/run.sh` asserts this concrete reviewer account rather than a non-reviewable organization. This does not enable any external review bot and does not introduce a foreign-network identity or compatibility interface.
- All permissions and substantive rights/consensus concerns remain independently gated. This correction does **not** address unresolved cross-SIP links, missing preamble governance, historic network assertions, site deployment or the remaining corpus.
- Do not merge into `main` or publish until the owner’s conditional PURE SILA release criteria pass.
