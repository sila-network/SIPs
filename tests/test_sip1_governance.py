"""Binding checks for the original Sila governance specification."""

from __future__ import annotations

import re
import tomllib
import unittest

from tools.sila import ROOT, SilaError, parse_document, read_collection, verify_metadata


class SilaGovernanceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = (ROOT / "SIPS" / "sip-1.md").read_text(encoding="utf-8")
        cls.metadata, cls.body = parse_document(cls.text)
        cls.template = (ROOT / "sip-template.md").read_text(encoding="utf-8")
        cls.settings = tomllib.loads((ROOT / "config" / "sila.toml").read_text(encoding="utf-8"))

    def test_foundation_is_draft_not_approved(self) -> None:
        self.assertEqual(self.metadata["sip"], "1")
        self.assertEqual(self.metadata["status"], "Draft")
        self.assertEqual(self.metadata["type"], "Meta")
        self.assertNotIn("approval-ref", self.metadata)
        self.assertEqual(self.metadata["author"], "Ahmed Ibrahim, Jihad Mustafa")
        self.assertEqual(len(read_collection()), 1)

    def test_every_defined_state_has_an_original_description(self) -> None:
        state_text = self.body.split("### Process states\n", 1)[1].split(
            "### Transition rules and evidence\n", 1
        )[0]
        states_in_document = re.findall(r"^\- \*\*([A-Za-z ]+):\*\*", state_text, flags=re.M)
        self.assertEqual(set(states_in_document), set(self.settings["governance"]["statuses"]))
        self.assertEqual(len(states_in_document), len(set(states_in_document)))

    def test_all_categories_and_types_are_defined(self) -> None:
        for category in self.settings["governance"]["categories"]:
            self.assertIn(f"**{category}:**", self.body)
        for kind in self.settings["governance"]["types"]:
            self.assertIn(f"**{kind}:**", self.body)

    def test_required_metadata_is_documented(self) -> None:
        for field in ("sip", "title", "description", "author", "status", "type", "created",
                      "category", "requires", "discussions-to", "last-call-deadline",
                      "withdrawal-reason", "approval-ref", "implementation-ref"):
            self.assertIn(chr(96) + field + chr(96), self.body)
        for conditional in ("last-call-deadline", "withdrawal-reason", "approval-ref"):
            self.assertIn(conditional, self.template)

    def test_required_governance_evidence_is_distinct(self) -> None:
        for key in ("### Participants and responsibility",
                    "### Proposal numbering and files",
                    "### Transition rules and evidence",
                    "### Technical review and Last Call",
                    "### Adoption and activation are separate",
                    "### Challenges and process changes",
                    "### Publication and external references"):
            self.assertIn(key, self.body)
        self.assertIn("publication", self.body.lower())
        self.assertIn("activation", self.body.lower())
        self.assertIn("Sila-owned", self.body)

    def test_template_does_not_fabricate_governance_events(self) -> None:
        self.assertIn("status: Draft", self.template)
        self.assertIn("created: YYYY-MM-DD", self.template)
        self.assertIn("author: Authorized Sila author", self.template)
        self.assertNotIn("approval-ref: https://", self.template)

    def test_approved_living_requires_reference(self) -> None:
        proposed = {
            "sip": "3", "title": "Sila governance process",
            "description": "An original Sila governance proposal.",
            "author": "Ahmed Ibrahim", "status": "Living",
            "type": "Meta", "created": self.metadata["created"],
        }
        with self.assertRaisesRegex(SilaError, "decision reference"):
            verify_metadata(proposed, "sip-3.md", {1, 3})

    def test_final_requires_decision_reference(self) -> None:
        proposed = {
            "sip": "3", "title": "Sila governance process",
            "description": "An original Sila governance proposal.",
            "author": "Jihad Mustafa", "status": "Final",
            "type": "Meta", "created": self.metadata["created"],
        }
        with self.assertRaisesRegex(SilaError, "decision reference"):
            verify_metadata(proposed, "sip-3.md", {1, 3})

    def test_proposal_includes_original_process_figure(self) -> None:
        self.assertIn("Idea --> Draft --> Review --> Last Call --> Final", self.body)
        self.assertIn("Approved Meta process proposal --> Living", self.body)
        self.assertIn("## Security Considerations", self.body)

    def test_governance_document_is_in_reference_order(self) -> None:
        expected = self.settings["governance"]["required_sections"]
        headings = re.findall(r"^## ([^\n]+)$", self.body, re.M)
        self.assertTrue(set(expected).issubset(headings))
        offsets = [headings.index(section) for section in expected]
        self.assertEqual(offsets, sorted(offsets))


if __name__ == "__main__":
    unittest.main()
