# Sila Improvement Proposals

Sila Network publishes original technical and governance proposals for the Sila protocol.

This repository begins with a clean Sila specification and tooling foundation. It does not import another network's proposal corpus, history, client implementations, automation code, or protocol identities.

## Components

- [SIP-1](SIPS/sip-1.md): initial Sila governance proposal.
- [Proposal template](sip-template.md): format for new Sila proposals.
- [Sila native specification checker](tools/sila_specs.py): strict metadata, sections, safe links and anchors, and normative dependency graphs.
- [Sila command and site tool](tools/sila.py): runs checks and builds local documentation.
- [Sila verification](.github/workflows/verify.yml): read-only continuous integration.
- [Sila website styling](assets/site.css): original site presentation.

## Commands

Requires Python 3.11 or later. There are no third-party runtime packages. This offline checker does not establish external discussion, governance approval, or network activation.

1. Run unit tests: python3 -m unittest discover -s tests -v
2. Inspect proposal consistency: python3 tools/sila.py check
3. Inspect repository identity: python3 tools/sila.py audit
4. Build a local preview: python3 tools/sila.py build --output _site
5. Verify the generated website: python3 tools/sila.py verify-site --output _site

The site is a preview, not an automatic publication. Merging, network activation, and approval are separate actions that require their own evidence.

## Governance

The publication authority is Sila Network. SIP-1 currently has Draft status. No proposal is considered active merely because its document exists.

The initial named authors of SIP-1 are Ahmed Ibrahim and Jihad Mustafa. Additional document authorship requires actual authorization through Sila's governance process.

## Rights

Sila Network reserves the rights in this newly written Sila-owned repository content. See [LICENSE.md](LICENSE.md). No external protocol source files or third-party application assets are included.

## Original Sila PR review gate

The [Sila review gate](tools/sila_review.py) verifies the changed file list and real
GitHub APPROVED reviews against the explicitly authorized identities in
[the Sila reviewer policy](config/sila-review.toml).

- Sila specifications require editorial and technical role authorization.
  One real reviewer may hold both roles if explicitly appointed to both and
  independent of the pull-request author.
- Code and automation changes require an authorized technical review.
- Other documents and assets require an authorized editorial review.
- Changing the reviewer policy in the same pull request cannot authorize the
  change being reviewed.
- Stale, withdrawn, dismissed, or self-issued reviews are not accepted.
- Jihad Mustafa (`ahmed202225`) is appointed to the editorial and
  technical Sila review roles. Appointing an account never records a
  review or grants final decision authority; GitHub APPROVED reviews
  must still be submitted personally for the exact current revision.
- The gate has GitHub **read-only** permissions. It cannot approve, publish,
  merge, assign reviewers, or change a proposal's governance status.

A passing check does not itself establish an authorized governance decision.
To enforce a mandatory merge block, GitHub's repository rules must require
the corresponding check on the target protected branch; this software cannot
substitute for repository administration settings.

## Sila documentation website

The original Sila static website is generated from verified proposal source;
it does not import third-party themes, remote fonts or client-side libraries.

- [Sila site generator](tools/sila_site.py) builds the home page, an individual
  accessible HTML page for each real SIP, six category pages, eight status
  pages, the searchable JSON index, and the original RSS 2.0 feed.
- [Sila styling](assets/site.css) adapts to phones and respects reduced motion.
- [Sila local search](assets/site.js) filters by text, category, and status;
  all documents remain browsable when JavaScript is disabled.
- The feed links to actual Sila source revisions on the current working branch
  until the official domain is configured and publicly deployed.
- A generated `_site/` preview is local build output, not a public release.
  It MUST NOT be treated as a Final SIP or network activation.

To preview locally (using only Python's standard library):

```sh
python3 tools/sila.py check
python3 tools/sila.py build --output _site
python3 tools/sila.py verify-site --output _site
python3 -m http.server 8000 --directory _site
```

Open `http://localhost:8000` on the computer running that server.
No public deployment or domain change is performed by these commands.

## Integrated lifecycle verification

The original [Sila end-to-end test suite](tests/test_sila_flow.py)
executes the actual offline Sila CLI within an isolated temporary project:

1. Draft a **test-only** SIP with a genuine dependency on SIP-1.
2. Run the same native specification check and identity checks used by CI.
3. Generate and verify the searchable site, category and status pages, RSS,
   proposal metadata, and converted cross-document links and heading anchors.
4. Exercise the actual review-gate decision logic using **synthetic GitHub
   event and review fixtures**, including positive and rejection scenarios.
5. Remove the test-only SIP and confirm that rebuilt site files and search
   indexes no longer expose it.

A synthetic review is NEVER a real human approval or governance decision.
No test SIP or simulated reviewer is committed to this repository.

Run the lifecycle tests explicitly with:

```sh
python3 -m unittest discover -s tests -p test_sila_flow.py -v
```

The production PR review step still requires actual authorized reviewers
and real GitHub review records. Administrative branch-protection settings
remain a separate, mandatory requirement for final publication readiness.

## Final Sila closure gate (read-only)

The [Sila closure checker](tools/sila_closure.py) inspects current GitHub
protection rules and the explicitly configured Sila reviewer roster. It does
not invent reviewers, authorize a proposal, post a new record, publish a site,
or merge a branch.

Run the local Pure Sila and lifecycle verification, then run the remote
administrative preflight:

```sh
python3 -m unittest discover -s tests -v
python3 tools/sila.py audit
python3 tools/sila.py check
python3 tools/sila.py build --output _site
python3 tools/sila.py verify-site --output _site
python3 tools/sila_closure.py check
```

The final command returns a nonzero status until all of these are true:

- A real GitHub account **other than the change author** has been explicitly
  appointed to each required reviewer role.
- Active GitHub rules cover `main` and require the successful
  `native-checks` status, at least one real independent approval, stale
  review dismissal, resolution of review threads, and linear history.
- No unknown actor bypasses those controls.

A passing administrative preflight is necessary but NOT sufficient for final
closure. The team must still independently verify a real PR review run and
decision, confirm the exact latest HEAD, inspect all residual technical and
rights blockers, and deliberately approve any merge or publication. Without
this evidence, the result is **BLOCKED**, not 100/100.

This checker prints results to the console only; it does not create archives,
approval records, or retrospective Sila governance history.

## Sila final decision and review responsibility

Ahmed Ibrahim is the exclusive final decision owner for approving or rejecting
changes in Sila-owned repositories. His designated GitHub account for this
repository is `sila-chain`. Jihad Mustafa remains a founding author, not a
second final decision owner.

Final owner authorization is different from independent technical review:
a qualified, explicitly appointed reviewer other than the change author
must approve changes requiring that review. No fake reviewer accounts,
automatic approvals, delegated final authority, or self-reviews are permitted.

SIP-1 remains a Draft. The owner designation is not a decision to approve
SIP-1, merge PR #1, publish the website, or activate protocol changes.
The repository's technical gates do not yet prove a final owner sign-off,
and this rule must be implemented and verified separately wherever other
Sila repositories exist. The GitHub permissions of those repositories are
not changed by editing this repository.

## Final approval of Sila changes

Ahmed Ibrahim is the **exclusive final decision authority**. His designated
GitHub identity is `sila-chain`. The independent technical reviewer
must be a real, explicitly authorized GitHub account other than the change
author. A technical recommendation alone never grants final authorization.

After the independent approval of the exact current commit, Ahmed may
personally add one of these exact comments to the **same GitHub pull request**:

```text
SILA FINAL APPROVE <40-character-head-commit-sha>
SILA FINAL REJECT <40-character-head-commit-sha>
SILA FINAL REVOKE <40-character-head-commit-sha>
```

Only a new, unedited comment authenticated as `sila-chain` and
created **after** the independent review qualifies as owner approval.
The check rejects outdated revisions, an altered decision comment, missing
reviewer approvals, revocations, and a newer rejection. Do not ask any
automation to write the final decision on Ahmed's behalf.

This adds a **technical PR gate for this SIP repository**. It does not
grant an approval for SIP-1, bypass GitHub branch protection, or authorize
a merge or release. The appointed reviewer must submit an actual, independent review
of the current revision. This repository gate is not automatically installed in
other Sila repositories; each repository must be assessed separately.

## Reference safety and Sila metadata contracts

Sila's native checker uses a strict metadata order, short proposal titles
(up to 44 characters), short descriptions (up to 140 characters), and
pinned implementation source revisions. It resolves document-local anchors
with the same Unicode heading identifiers that the Sila site generator uses.

Independent technical standards may retain their own actual identities.
Their configured links are restricted to stable revisions where supported;
only the genuinely independent standard repositories explicitly listed in
`config/sila.toml` may use pinned external GitHub source links.
These checks validate **reference syntax**. They cannot by themselves attest
that an external revision exists or that any external code is part of Sila.
Any unverified Sila counterpart remains a blocker, not an invented artifact.

SIP-1 remains a **Draft** and no approved or activated protocol status is
created by these metadata checks.
