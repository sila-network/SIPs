"""Regression and negative tests for the original Sila specification checker."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.sila_specs import HEADER_ORDER, ProposalError, validate_repository

ROOT = Path(__file__).resolve().parents[1]
TODAY = date.today().isoformat()
BODY = """## Abstract

An original Sila candidate describing a measurable new rule.

## Specification

A Sila rule with defined inputs and a reproducible result.

## Rationale

This approach can be tested by independent Sila clients.

## Test Cases

Accepted and rejected examples are part of this Sila proposal.

## Security Considerations

Adversarial inputs are checked against stated invariants.

## Copyright

Original Sila Network content; rights reserved.
"""


class NativeSpecTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "config").mkdir()
        (self.root / "SIPS").mkdir()
        shutil.copyfile(ROOT / "config/sila.toml", self.root / "config/sila.toml")
        shutil.copyfile(ROOT / "SIPS/sip-1.md", self.root / "SIPS/sip-1.md")
        shutil.copyfile(ROOT / "LICENSE.md", self.root / "LICENSE.md")
        (self.root / "assets/sip-1").mkdir(parents=True)
        shutil.copyfile(ROOT / "assets/sip-1/process.svg", self.root / "assets/sip-1/process.svg")

    def create(self, num=2, **changes):
        data = {
            "sip": str(num), "title": "Original Sila Rule",
            "description": "A new Sila-native standard for consideration.",
            "author": "Ahmed Ibrahim", "status": "Draft",
            "type": "Standards Track", "category": "Core", "created": TODAY,
        }
        body = changes.pop("body", BODY)
        data.update(changes)
        path = self.root / "SIPS" / f"sip-{num}.md"
        ordered = sorted(data, key=lambda key: HEADER_ORDER.index(key) if key in HEADER_ORDER else len(HEADER_ORDER))
        content = "---\n" + "".join(f"{key}: {data[key]}\n" for key in ordered if data[key] is not None)
        path.write_text(content + "---\n\n" + body, encoding="utf-8")
        return path

    def fails(self, message):
        with self.assertRaisesRegex(ProposalError, message):
            validate_repository(self.root)

    def test_foundation_is_valid(self):
        self.assertEqual(len(validate_repository(self.root)), 1)

    def test_second_draft_is_valid(self):
        self.create()
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_number_matches_path(self):
        self.create(sip="22")
        self.fails("number differs")

    def test_number_must_be_canonical(self):
        p = self.create()
        p.rename(p.with_name("sip-02.md"))
        self.fails("noncanonical")

    def test_duplicate_header(self):
        p = self.create()
        p.write_text(p.read_text().replace("title: Original", "title: Duplicate\n" + "title: Original"))
        self.fails("duplicate metadata")

    def test_unknown_header(self):
        self.create(randomfield="unauthorized")
        self.fails("unknown or duplicate metadata")

    def test_nested_yaml_rejected(self):
        self.create(requires="[1]")
        self.fails("unsupported scalar")

    def test_missing_header_delimiter(self):
        p = self.create()
        p.write_text(p.read_text().replace("---\n", "", 1))
        self.fails("missing opening")

    def test_invalid_date_rejected(self):
        self.create(created="2026-20-45")
        self.fails("invalid created")

    def test_noncanonical_date_rejected(self):
        self.create(created="2026-1-5")
        self.fails("not an ISO date")

    def test_future_date_rejected(self):
        self.create(created=(date.today()+timedelta(days=1)).isoformat())
        self.fails("in the future")

    def test_invalid_status_rejected(self):
        self.create(status="Active")
        self.fails("unrecognized Sila status")

    def test_invalid_category_rejected(self):
        self.create(category="Unknown")
        self.fails("valid category")

    def test_meta_with_category_rejected(self):
        self.create(type="Meta")
        self.fails("category only")

    def test_unauthorized_author_rejected(self):
        self.create(author="Unauthorized Person")
        self.fails("unapproved")

    def test_duplicate_authorship_rejected(self):
        self.create(author="Ahmed Ibrahim, Ahmed Ibrahim")
        self.fails("duplicated Sila author")

    def test_final_without_decision_rejected(self):
        self.create(status="Final")
        self.fails("requires a decision reference")

    def test_final_with_only_a_link_still_blocked(self):
        self.create(status="Final", **{"approval-ref":"https://github.com/sila-network/SIPs"})
        self.fails("not yet independently verifiable")

    def test_living_process_needs_verified_authority(self):
        self.create(type="Meta", category=None, status="Living",
                    **{"approval-ref":"https://github.com/sila-network/SIPs"})
        self.fails("not yet independently verifiable")

    def test_draft_with_false_approval_rejected(self):
        self.create(**{"approval-ref":"https://github.com/sila-network/SIPs"})
        self.fails("unapproved proposal cannot claim")

    def test_last_call_needs_real_topic(self):
        self.create(status="Last Call", **{"last-call-deadline":(date.today()+timedelta(days=15)).isoformat()})
        self.fails("deadline and real discussion")

    def test_last_call_expired_rejected(self):
        self.create(status="Last Call",**{"last-call-deadline":(date.today()-timedelta(days=1)).isoformat(),
            "discussions-to":"https://sila-magicians.discourse.group/t/sample/123"})
        self.fails("deadline is past")

    def test_last_call_valid_syntax(self):
        self.create(status="Last Call",**{"last-call-deadline":(date.today()+timedelta(days=14)).isoformat(),
            "discussions-to":"https://sila-magicians.discourse.group/t/sample/123"})
        self.assertEqual(len(validate_repository(self.root)),2)

    def test_last_call_forum_home_is_not_a_topic(self):
        self.create(status="Last Call",**{"last-call-deadline":(date.today()+timedelta(days=14)).isoformat(),
            "discussions-to":"https://sila-magicians.discourse.group/"})
        self.fails("invalid Sila discussion topic")

    def test_withdrawn_needs_reason(self):
        self.create(status="Withdrawn")
        self.fails("requires a withdrawal reason")

    def test_draft_cannot_carry_withdrawal_reason(self):
        self.create(**{"withdrawal-reason":"No longer applicable"})
        self.fails("non-Withdrawn")

    def test_draft_cannot_carry_last_call_deadline(self):
        self.create(**{"last-call-deadline":(date.today()+timedelta(days=12)).isoformat()})
        self.fails("must not appear")

    def test_missing_required_section(self):
        self.create(body=BODY.replace("## Rationale", "## Other"))
        self.fails("mandatory Sila sections")

    def test_duplicate_required_section(self):
        self.create(body=BODY+"\n## Abstract\n\nA second abstract.\n")
        self.fails("mandatory Sila sections")

    def test_required_sections_out_of_order(self):
        changed=BODY.replace("## Rationale","## TMP").replace("## Specification","## Rationale").replace("## TMP","## Specification")
        self.create(body=changed)
        self.fails("out of order")

    def test_placeholder_section_rejected(self):
        self.create(body=BODY.replace("Adversarial inputs are checked against stated invariants.","TBD"))
        self.fails("placeholder section Security Considerations")

    def test_review_requires_test_cases(self):
        self.create(status="Review",body=BODY.replace("## Test Cases","## Illustrations"))
        self.fails("needs Test Cases")

    def test_unknown_cross_reference(self):
        self.create(body=BODY+"\nSIP-945566 is not issued.\n")
        self.fails("unknown Sila cross-reference")

    def test_known_cross_reference(self):
        self.create(body=BODY+"\nRefer to the existing [SIP-1](sip-1.md#rationale).\n")
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_missing_normative_dependency(self):
        self.create(requires="99")
        self.fails("missing Sila normative dependency")

    def test_duplicate_normative_dependency(self):
        self.create(requires="1, 1")
        self.fails("duplicate normative dependency")

    def test_self_dependency(self):
        self.create(requires="2")
        self.fails("cannot require itself")

    def test_dependency_cycle(self):
        self.create(requires="3")
        self.create(num=3, requires="2")
        self.fails("cyclic Sila proposal dependencies")

    def test_valid_chained_dependency(self):
        self.create(requires="1")
        self.create(num=3,requires="1, 2")
        self.assertEqual(len(validate_repository(self.root)),3)

    def test_local_link_exists(self):
        self.create(body=BODY+"\nSee [rights](../LICENSE.md).\n")
        (self.root/"LICENSE.md").write_text("Sila Network rights reserved")
        self.assertEqual(len(validate_repository(self.root)),2)

    def test_missing_local_link_rejected(self):
        self.create(body=BODY+"\nSee [missing](../missing.md).\n")
        self.fails("unresolved or escaping local link")

    def test_traversal_link_rejected(self):
        self.create(body=BODY+"\nSee [outside](../../other.md).\n")
        self.fails("unresolved or escaping local link")

    def test_encoded_traversal_link_rejected(self):
        self.create(body=BODY+"\nSee [outside](%2e%2e/%2e%2e/other.md).\n")
        self.fails("unresolved or escaping local link")

    def test_absolute_local_link_rejected(self):
        self.create(body=BODY+"\nSee [unsafe](/etc/passwd).\n")
        self.fails("unsafe local link")

    def test_script_link_rejected(self):
        self.create(body=BODY+"\nSee [bad](javascript:malicious).\n")
        self.fails("unsafe or unauthorized")

    def test_unknown_external_host_rejected(self):
        self.create(body=BODY+"\nSee [bad](https://example.com/).\n")
        self.fails("unsafe or unauthorized")

    def test_unrelated_github_repo_rejected(self):
        self.create(body=BODY+"\nSee [bad](https://github.com/unknown/project).\n")
        self.fails("unsafe or unauthorized")

    def test_independent_rfc_link_accepted(self):
        self.create(body=BODY+"\nRead [RFC](https://www.rfc-editor.org/rfc/rfc2119).\n")
        self.assertEqual(len(validate_repository(self.root)),2)

    def test_existing_heading_anchor_accepted(self):
        self.create(body=BODY+"\nSee [details](#rationale).\n")
        self.assertEqual(len(validate_repository(self.root)),2)

    def test_missing_heading_anchor_rejected(self):
        self.create(body=BODY+"\nSee [details](#not-a-heading).\n")
        self.fails("unresolved heading anchor")

    def test_fenced_heading_does_not_duplicate(self):
        self.create(body=BODY+"\n"+chr(96)*3+"\n## Abstract\n"+chr(96)*3+"\n")
        self.assertEqual(len(validate_repository(self.root)),2)

    def test_unclosed_fence_fails(self):
        self.create(body=BODY+"\n"+chr(96)*3+"\nThis fence is unclosed.\n")
        self.fails("unclosed Sila documentation")

    def test_fenced_links_do_not_create_external_dependency(self):
        self.create(body=BODY+"\n"+chr(96)*3+"\n[example](javascript:unsafe)\n"+chr(96)*3+"\n")
        self.assertEqual(len(validate_repository(self.root)),2)

    def test_external_implementation_ignored_as_authority(self):
        self.create(**{"implementation-ref":"https://github.com/outside/unknown"})
        self.fails("invalid Sila implementation reference")

    def test_long_title_rejected(self):
        self.create(title="Long original Sila design name " + "X" * 30)
        self.fails("title or description too long")

    def test_long_description_rejected(self):
        self.create(description="Full Sila specification summary " + "X" * 150)
        self.fails("title or description too long")

    def test_title_cannot_embed_proposal_number(self):
        self.create(title="SIP-2 Another Sila rule")
        self.fails("must not repeat the Sila proposal number")

    def test_out_of_order_metadata_rejected(self):
        candidate = self.create()
        candidate.write_text(candidate.read_text().replace(
            "title: Original Sila Rule\ndescription: A new Sila-native standard for consideration.\n",
            "description: A new Sila-native standard for consideration.\ntitle: Original Sila Rule\n",
        ))
        self.fails("out of canonical order")

    def test_valid_immutable_sila_implementation_reference(self):
        self.create(**{
            "implementation-ref": (
                "https://github.com/sila-network/sila-client/blob/"
                + "a" * 40 + "/src/implementation.py"
            )
        })
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_mutable_sila_implementation_reference_rejected(self):
        self.create(**{
            "implementation-ref": "https://github.com/sila-network/sila-client/blob/main/README.md"
        })
        self.fails("immutable commit")

    def test_sila_implementation_repo_home_is_not_immutable(self):
        self.create(**{
            "implementation-ref": "https://github.com/sila-network/sila-client"
        })
        self.fails("immutable commit")

    def test_anchor_with_repeated_headings(self):
        self.create(body=BODY + "\n### Details\n\nExample A.\n\n"
                    + "### Details\n\nExample B.\n\nSee [second](#details-2).\n")
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_anchor_at_nested_heading_level(self):
        self.create(body=BODY + "\n### Nested Clause\n\nSee [nested](#nested-clause).\n")
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_unicode_anchor_matches_native_site(self):
        self.create(body=BODY + "\n### فحص سيلا\n\nSee [Arabic](#فحص-سيلا).\n")
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_missing_repeated_heading_anchor_rejected(self):
        self.create(body=BODY + "\n### Details\n\nSee [bad](#details-2).\n")
        self.fails("unresolved heading anchor")

    def test_independent_external_standard_commit_link_is_allowed(self):
        self.create(body=BODY + "\nSee [independent format]("
                    + "https://github.com/ChainAgnostic/CAIPs/blob/"
                    + "a" * 40 + "/CAIPs/caip-10.md).\n")
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_independent_public_standard_link_is_allowed(self):
        self.create(body=BODY + "\nSee [independent report]("
                    + "https://www.w3.org/TR/2021/CRD-secure-contexts-20210918/).\n")
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_living_standard_requires_immutable_snapshot(self):
        self.create(body=BODY + "\nSee [HTML standard]("
                    + "https://html.spec.whatwg.org/commit-snapshots/"
                    + "a" * 40 + "/).\n")
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_living_standard_unpinned_link_is_blocked(self):
        self.create(body=BODY + "\nSee [mutable report](https://html.spec.whatwg.org/).\n")
        self.fails("unsafe or unauthorized")

    def test_invalid_external_standard_without_commit_is_blocked(self):
        self.create(body=BODY + "\nSee [unpinned](https://github.com/bitcoin/bips/blob/master/bip-0038.mediawiki).\n")
        self.fails("unsafe or unauthorized")

    def test_external_standard_repo_home_is_not_a_reference(self):
        self.create(body=BODY + "\nSee [unpinned](https://github.com/ChainAgnostic/CAIPs).\n")
        self.fails("unsafe or unauthorized")

    def test_sila_owner_url_must_not_escape_path_components(self):
        self.create(body=BODY + "\nSee [unsafe](https://github.com/sila-network/../someone/secret).\n")
        self.fails("unsafe or unauthorized")

    def test_sila_owner_url_must_not_use_encoded_path_components(self):
        self.create(body=BODY + "\nSee [unsafe](https://github.com/sila-network/%2e%2e/elsewhere).\n")
        self.fails("unsafe or unauthorized")

    def test_public_standard_requires_pinned_unicode_revision(self):
        self.create(body=BODY + "\nSee [Unicode report]("
                    + "https://www.unicode.org/reports/tr46/tr46-35.html).\n")
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_unpinned_unicode_report_is_blocked(self):
        self.create(body=BODY + "\nSee [Unicode](https://www.unicode.org/reports/tr46/).\n")
        self.fails("unsafe or unauthorized")

    def test_rfc_number_is_required_for_external_reference(self):
        self.create(body=BODY + "\nSee [draft](https://www.rfc-editor.org/rfc/).\n")
        self.fails("unsafe or unauthorized")

    # Functional parity contracts: both accepted and denied cases are tested.
    # No synthetic document is published by this fixture suite.
    def test_optional_sections_canonical_order_is_accepted(self):
        body = BODY.replace("## Specification",
            "## Motivation\n\nA real Sila-specific design motivation.\n\n"
            "## Specification")
        body = body.replace("## Test Cases",
            "## Backwards Compatibility\n\nNo incompatible Sila interface changes.\n\n"
            "## Migration\n\nThis is a test-only migration contract.\n\n"
            "## Rollback Plan\n\nThis is a test-only recovery contract.\n\n"
            "## Test Cases")
        body = body.replace("## Security Considerations",
            "## Reference Implementation\n\nA conceptual Sila example with no deployed claim.\n\n"
            "## Security Considerations")
        self.create(body=body)
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_out_of_order_optional_sections_rejected(self):
        changed = BODY.replace(
            "## Test Cases",
            "## Reference Implementation\n\nTest-only example.\n\n"
            "## Backwards Compatibility\n\nA test-only migration issue.\n\n"
            "## Test Cases",
        )
        self.create(body=changed)
        self.fails("out of canonical order")

    def test_unknown_top_level_section_rejected(self):
        self.create(body=BODY.replace(
            "## Test Cases", "## Unsupported Section\n\nAn unexpected document section.\n\n## Test Cases"))
        self.fails("unrecognized Sila top-level section")

    def test_duplicate_optional_section_rejected(self):
        self.create(body=BODY.replace(
            "## Test Cases", "## Motivation\n\nA purpose.\n\n## Motivation\n\nAnother purpose.\n\n## Test Cases"))
        self.fails("duplicate Sila top-level section")

    def test_metadata_title_colon_rejected(self):
        self.create(title="Sila Rule: Native Proposal")
        self.fails("must not contain a colon")

    def test_metadata_description_colon_rejected(self):
        self.create(description="Summary: a Sila rule")
        self.fails("must not contain a colon")

    def test_out_of_order_requires_rejected(self):
        self.create(requires="3, 1")
        self.fails("ascending order")

    def test_valid_ascending_requires(self):
        self.create(requires="1")
        self.create(num=3, requires="1, 2")
        self.assertEqual(len(validate_repository(self.root)), 3)

    def test_review_cannot_depend_on_draft(self):
        self.create(status="Review", requires="1")
        self.fails("insufficient status")

    def test_stagnant_maturity_is_not_stronger_than_review(self):
        self.create(status="Stagnant")
        self.create(num=3, status="Review", requires="2")
        self.fails("insufficient status")

    def test_draft_can_depend_on_draft(self):
        self.create(requires="1")
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_draft_cannot_depend_on_idea(self):
        self.create(status="Idea")
        self.create(num=3, requires="2")
        self.fails("insufficient status")

    def test_specification_mentions_normative_sip_without_requires(self):
        self.create(body=BODY.replace(
            "A Sila rule with defined inputs and a reproducible result.",
            "A Sila rule requiring the previous [SIP-1](sip-1.md#rationale) semantics."
        ))
        self.fails("undeclared normative SIP-1")

    def test_specification_reference_matches_declared_dependency(self):
        self.create(requires="1", body=BODY.replace(
            "A Sila rule with defined inputs and a reproducible result.",
            "This original Sila feature builds on [SIP-1](sip-1.md#rationale)."
        ))
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_informational_reference_does_not_force_requires(self):
        self.create(body=BODY + "\nDiscussion about [SIP-1](sip-1.md#rationale) is informative.\n")
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_inline_example_link_does_not_trigger_security_error(self):
        self.create(body=BODY + "\nExample: `[unsafe](javascript:example)`.\n")
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_inline_example_proposal_id_is_not_a_real_reference(self):
        self.create(body=BODY + "\nExample: `SIP-999999` is illustrative.\n")
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_real_link_still_checked_next_to_inline_example(self):
        self.create(body=BODY + "\n`[example](javascript:example)` "
                    "See [outside](https://example.com/).\n")
        self.fails("unsafe or unauthorized")

    def test_first_sila_reference_must_be_linked(self):
        self.create(body=BODY + "\nThe first SIP-1 citation has no link.\n")
        self.fails("first Sila reference SIP-1")

    def test_first_sila_reference_link_to_other_file_rejected(self):
        self.create(body=BODY + "\nSee [SIP-1](../LICENSE.md) for the rule.\n")
        self.fails("must link to its own document")

    def test_first_sila_reference_correct_link_accepted(self):
        self.create(body=BODY + "\nSee [SIP-1](sip-1.md#rationale) for the rule.\n")
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_second_reference_can_be_plain_after_valid_first_link(self):
        self.create(body=BODY + "\nSee [SIP-1](sip-1.md#rationale). "
                    "The same SIP-1 is cited again here.\n")
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_unrelated_inline_example_does_not_count_as_first_citation(self):
        self.create(body=BODY + "\n`SIP-1` is an example. "
                    "See [SIP-1](sip-1.md#rationale) for the real citation.\n")
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_draft_cannot_link_to_undeclared_future_proposal(self):
        self.create(body=BODY + "\nSee [SIP-9999](sip-9999.md).\n")
        self.fails("unknown Sila cross-reference")

    def test_first_sila_reference_link_fragment_must_resolve(self):
        self.create(body=BODY + "\nSee [SIP-1](sip-1.md#missing-section).\n")
        self.fails("unresolved heading anchor")

    def test_review_cannot_cite_draft_as_stable_authority(self):
        self.create(status="Review", body=BODY +
                    "\nSee [SIP-1](sip-1.md#rationale) for background.\n")
        self.fails("cross-reference SIP-1 has insufficient status")

    def test_draft_can_cite_draft(self):
        self.create()
        self.create(num=3, body=BODY + "\nSee [SIP-2](sip-2.md).\n")
        self.assertEqual(len(validate_repository(self.root)), 3)

    def test_draft_cannot_cite_idea_as_mature(self):
        self.create(status="Idea")
        self.create(num=3, body=BODY + "\nSee [SIP-2](sip-2.md).\n")
        self.fails("cross-reference SIP-2 has insufficient status")

    def test_withdrawn_cross_reference_rejected(self):
        self.create(status="Withdrawn", **{"withdrawal-reason": "Test-only candidate withdrawn."})
        self.create(num=3, body=BODY + "\nSee [SIP-2](sip-2.md).\n")
        self.fails("withdrawn Sila cross-reference SIP-2")

    def test_own_sila_proposal_can_describe_its_number(self):
        self.create(body=BODY + "\nThis SIP-2 is only a test candidate.\n")
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_canonical_sila_prose_reference_accepted(self):
        self.create(body=BODY + "\nRefer to [SIP-1](sip-1.md#rationale).\n")
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_sila_spaced_reference_denied(self):
        self.create(body=BODY + "\nThe notation SIP 1 must be refused.\n")
        self.fails("canonical SIP-N notation")

    def test_sila_joined_reference_denied(self):
        self.create(body=BODY + "\nThe notation SIP1 must be refused.\n")
        self.fails("canonical SIP-N notation")

    def test_sila_spaced_dash_reference_denied(self):
        self.create(body=BODY + "\nThe notation SIP -1 must be refused.\n")
        self.fails("canonical SIP-N notation")

    def test_sila_spaced_dash_on_both_sides_reference_denied(self):
        self.create(body=BODY + "\nThe notation SIP - 1 must be refused.\n")
        self.fails("canonical SIP-N notation")

    def test_sila_space_after_dash_reference_denied(self):
        self.create(body=BODY + "\nThe notation SIP- 1 must be refused.\n")
        self.fails("canonical SIP-N notation")

    def test_sila_leading_zero_reference_denied(self):
        self.create(body=BODY + "\nThe notation SIP-01 must be refused.\n")
        self.fails("canonical SIP-N notation")

    def test_sila_malformed_metadata_reference_denied(self):
        self.create(description="A Sila proposal concerning SIP 1.")
        self.fails("canonical SIP-N notation")

    def test_code_fence_examples_do_not_require_sila_reference_validation(self):
        marker = chr(96) * 3
        self.create(body=BODY + "\n" + marker + "text\nSIP 2\n<!-- code sample -->\n"
                    + marker + "\n")
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_inline_examples_do_not_require_sila_reference_validation(self):
        self.create(body=BODY + "\nExample `SIP1` is not a normative reference.\n")
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_malformed_subheading_without_space_is_denied(self):
        self.create(body=BODY + "\n###Invalid heading marker\n")
        self.fails("headings require a space")

    def test_markdown_subheading_with_space_is_accepted(self):
        self.create(body=BODY + "\n### Proper Subheading\n\nText.\n")
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_html_comment_cannot_hide_specification_content(self):
        self.create(body=BODY + "\n<!-- concealed Sila text -->\n")
        self.fails("raw HTML comments")

    def test_escaped_comment_in_code_is_accepted(self):
        self.create(body=BODY + "\nThe literal `<!-- code -->` is an example.\n")
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_short_title_is_denied(self):
        self.create(title="X")
        self.fails("required minimum")

    def test_short_description_is_denied(self):
        self.create(description="X")
        self.fails("required minimum")

    def citation_body(self, entry: str, *, label: str = "csl-json") -> str:
        fence = chr(96) * 3
        return BODY + "\n" + fence + label + "\n" + entry + "\n" + fence + "\n"

    def test_valid_independent_csl_citation_record(self):
        self.create(body=self.citation_body(
            '{"type":"webpage","id":"sila-test","DOI":"10.1000/sila",'
            '"URL":"https://www.rfc-editor.org/rfc/rfc2119"}'))
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_independent_csl_citation_accepts_numeric_id(self):
        self.create(body=self.citation_body(
            '{"type":"article-journal","id":42,"DOI":"10.1000/example",'
            '"URL":"https://www.rfc-editor.org/rfc/rfc2119"}'))
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_invalid_csl_citation_json_rejected(self):
        self.create(body=self.citation_body('{"type":"webpage", broken}'))
        self.fails("invalid Sila citation JSON")

    def test_duplicate_csl_citation_json_field_rejected(self):
        self.create(body=self.citation_body(
            '{"type":"webpage","type":"book","id":"test","DOI":"10.1000/test",'
            '"URL":"https://www.rfc-editor.org/rfc/rfc2119"}'))
        self.fails("duplicate JSON field")

    def test_missing_csl_citation_doi_rejected(self):
        self.create(body=self.citation_body(
            '{"type":"webpage","id":"test","URL":"https://www.rfc-editor.org/rfc/rfc2119"}'))
        self.fails("must include a DOI")

    def test_missing_csl_citation_url_rejected(self):
        self.create(body=self.citation_body(
            '{"type":"webpage","id":"test","DOI":"10.1000/test"}'))
        self.fails("must include a URL")

    def test_unknown_csl_citation_type_rejected(self):
        self.create(body=self.citation_body(
            '{"type":"made-up","id":"test","DOI":"10.1000/test",'
            '"URL":"https://www.rfc-editor.org/rfc/rfc2119"}'))
        self.fails("valid independent CSL type")

    def test_csl_citation_rejects_non_scalar_id(self):
        self.create(body=self.citation_body(
            '{"type":"webpage","id":[],"DOI":"10.1000/test",'
            '"URL":"https://www.rfc-editor.org/rfc/rfc2119"}'))
        self.fails("valid identifier")

    def test_csl_citation_rejects_insecure_url(self):
        self.create(body=self.citation_body(
            '{"type":"webpage","id":"test","DOI":"10.1000/test",'
            '"URL":"http://www.rfc-editor.org/rfc/rfc2119"}'))
        self.fails("safe HTTPS")

    def test_csl_citation_invalid_author_rejected(self):
        self.create(body=self.citation_body(
            '{"type":"webpage","id":"test","DOI":"10.1000/test",'
            '"URL":"https://www.rfc-editor.org/rfc/rfc2119","author":"not-a-list"}'))
        self.fails("citation author data")

    def test_csl_citation_additional_urls_reject_http(self):
        self.create(body=self.citation_body(
            '{"type":"webpage","id":"test","DOI":"10.1000/test",'
            '"URL":"https://www.rfc-editor.org/rfc/rfc2119",'
            '"custom":{"additional-urls":["http://unsafe.invalid"]}}'))
        self.fails("additional URLs")

    def test_other_json_code_fences_are_not_csl_citations(self):
        self.create(body=self.citation_body(
            '{"arbitrary":true}', label="json"))
        self.assertEqual(len(validate_repository(self.root)), 2)

    def test_current_repository_validates(self):
        self.assertEqual([doc[1]["sip"] for doc in validate_repository(ROOT)], ["1"])


if __name__ == "__main__":
    unittest.main()
