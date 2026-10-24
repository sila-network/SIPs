# Claude / ChatGPT handoff — finish the repository, 2026-10-24

The owner explicitly requests **actual closure today**, without any file downloads or user relay.

**This note is the direct GitHub handoff for Claude, not a message delivered to Claude's active private chat.** The authorized work branch is `claude/greeting-mgich3`. Do not change `main`, open a PR, merge, deploy or modify other repositories without separate approval.

## Completed in this commit

Added a standalone **unpublished** Jekyll site build, source layout, homepage, readable proposal template, styling, GitHub Actions build and Python page-coverage verifier. This is a genuine build implementation rather than another status report.

Run `bundle install && bundle exec jekyll build --trace --destination _site` then `python3 tools/verify_site.py _site`. The `site-build.yml` CI job runs these checks automatically. The validator has four unit tests (passed locally). Any failures must be fixed, not bypassed.

**It presently builds the ONE SIP document on the branch**. An independently functioning site build is not equivalent to the 966-document site. It is not published.

## Claude: start concrete content work

1. Review the site-build CI outcome and fix actual build regressions on this branch.
2. Preserve the branch's established SIP-1. Use the existing 966-row triage and upstream parity report to prepare a **small verified content import**, starting with docs that have zero forbidden-identity hits **and** independently verified publication rights, full substantive parity, and correct cross-references. Do not equate a `has_rights_marker` hit with rights clearance.
3. Resolve the 365 SRC routing stubs carefully: missing `status: Moved` is a functional break, but adding a governance status also must not falsely claim an inherited Sila decision.
4. Classify 15 shrunken SIPs for missing normative definitions; no mass accepted imports before comparing technical meaning.
5. Keep the 26 foreign-name paths and unresolved logo rights, protocol identities, and unverified ownership **blocked**. Do not publish the raw source zip to a public branch or sneak identity aliases into operational code.
6. Maintain explicit PASS/FAIL/BLOCKED audit results and exact source SHA. No 100/100 certificate unless the full corpus, rights, Pure Sila, parity, site and deployment gates actually pass.

This branch can coordinate independently of the owner's phone or internet connection. The owner does not need to send anything to Claude.
