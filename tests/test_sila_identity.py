"""Safeguards against non-Sila labels and unreviewed visual sources."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.check_sila_identity import audit


class SilaIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "SIPS").mkdir()
        (self.root / "SIPS/sip-1.md").write_text("Sila-native process\n")

    def test_plain_sila_text_has_no_hits(self):
        result = audit(self.root)
        self.assertEqual(result["counts"]["path_or_text_findings"], 0)
        self.assertEqual(result["counts"]["visuals_missing_clearance"], 0)

    def test_foreign_protocol_name_is_rejected(self):
        (self.root / "SIPS/sip-2.md").write_text("et" + "hereum")
        self.assertGreater(audit(self.root)["counts"]["path_or_text_findings"], 0)

    def test_runtime_namespace_is_rejected(self):
        (self.root / "SIPS/sip-2.md").write_text("ev" + "m_debugTrace")
        self.assertGreater(audit(self.root)["counts"]["path_or_text_findings"], 0)

    def test_camel_case_protocol_identity_is_rejected(self):
        (self.root / "SIPS/sip-2.md").write_text("gas" + "EV" + "MPlusEmulate")
        self.assertGreater(audit(self.root)["counts"]["path_or_text_findings"], 0)

    def test_legal_plain_english_is_not_mistaken_for_protocol_identity(self):
        (self.root / "SIPS/sip-2.md").write_text(
            "A commercial exercise needs merchantability and legal review."
        )
        result = audit(self.root)
        self.assertEqual(result["counts"]["path_or_text_findings"], 0)

    def test_foreign_filename_is_rejected(self):
        (self.root / ("er" + "c-20.md")).write_text("neutral")
        self.assertTrue(any(hit["kind"] == "path" for hit in audit(self.root)["term_hits"]))

    def test_only_exact_negative_vocabulary_fixture_is_exempt(self):
        fixture = self.root / "tests/fixtures/sila-denied-identities.json"
        fixture.parent.mkdir(parents=True)
        fixture.write_text("et" + "hereum")
        self.assertEqual(audit(self.root)["counts"]["path_or_text_findings"], 0)
        (self.root / "tests/fixtures/another-file.json").write_text(
            "et" + "hereum"
        )
        self.assertGreater(audit(self.root)["counts"]["path_or_text_findings"], 0)

    def test_media_requires_positive_clearance(self):
        folder = self.root / "assets"
        folder.mkdir()
        (folder / "figure.png").write_bytes(b"sample")
        self.assertEqual(audit(self.root)["counts"]["visuals_missing_clearance"], 1)

    def test_known_foreign_visual_content_cannot_be_approved(self):
        from unittest.mock import patch
        import tools.check_sila_identity as source

        visual = self.root / "assets/example.png"
        visual.parent.mkdir(parents=True)
        visual.write_bytes(b"foreign-logo-fixture")
        digest = hashlib.sha256(visual.read_bytes()).hexdigest()
        evidence = {
            "sha256": digest,
            "identity_review": "cleared",
            "license_basis": "permission asserted",
            "reviewed_by": "authorized human",
            "evidence_reference": "record",
        }
        (self.root / "VISUAL_CLEARANCES.json").write_text(
            json.dumps({"assets/example.png": evidence})
        )
        with patch.object(source, "KNOWN_FOREIGN_VISUAL_SHA256", {digest}):
            result = audit(self.root)
        self.assertEqual(result["counts"]["visuals_missing_clearance"], 0)
        self.assertEqual(result["forbidden_visuals"], ["assets/example.png"])
        self.assertEqual(result["status"], "BLOCKED")

    def test_positive_media_clearance_must_match_bytes(self):
        folder = self.root / "assets"
        folder.mkdir()
        png = folder / "figure.png"
        png.write_bytes(b"sample")
        entry = {
            "sha256": hashlib.sha256(b"sample").hexdigest(),
            "identity_review": "cleared",
            "license_basis": "original illustration",
            "reviewed_by": "authorized human",
            "evidence_reference": "manual evidence record",
        }
        (self.root / "VISUAL_CLEARANCES.json").write_text(json.dumps({"assets/figure.png": entry}))
        self.assertEqual(audit(self.root)["counts"]["visuals_missing_clearance"], 0)
        png.write_bytes(b"changed bytes")
        self.assertEqual(audit(self.root)["counts"]["visuals_missing_clearance"], 1)


if __name__ == "__main__":
    unittest.main()