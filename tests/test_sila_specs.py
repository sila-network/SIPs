"""Regression and negative tests for the original Sila specification checker."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.sila_specs import ProposalError, validate_repository

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
        content = "---\n" + "".join(f"{key}: {value}\n" for key, value in data.items() if value is not None)
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
        self.create(body=BODY+"\nRefer to the existing SIP-1.\n")
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

    def test_current_repository_validates(self):
        self.assertEqual([doc[1]["sip"] for doc in validate_repository(ROOT)], ["1"])


if __name__ == "__main__":
    unittest.main()
