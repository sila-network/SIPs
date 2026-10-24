"""Ensure owner identity policy rejects regressions rather than normalizing them."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.verify_sila_publication_identity import SILA_ISSUER, check


class SilaOwnerIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "SIPS").mkdir()
        (self.root / "assets").mkdir()
        (self.root / "SIPS/sip-12.md").write_text(
            f"---\nsip: 12\nauthor: {SILA_ISSUER}\n---\n\n## Abstract\n\nSila.\n",
            encoding="utf-8",
        )
        data = b"\x89PNG\r\n\x1a\n" + b"fixture"
        (self.root / "assets/sila-logo.png").write_bytes(data)
        (self.root / "VISUAL_CLEARANCES.json").write_text(json.dumps({
            "assets/sila-logo.png": {
                "sha256": hashlib.sha256(data).hexdigest(),
                "identity_review": "cleared",
                "evidence_reference": "owner declaration",
            }
        }), encoding="utf-8")

    def issues(self):
        # The fixture cannot masquerade as the real owner's approved logo.
        return check(self.root)

    def test_approved_sila_identity_passes(self):
        logo = (self.root / "assets/sila-logo.png").read_bytes()
        with patch("tools.verify_sila_publication_identity.LOGO_SHA256", hashlib.sha256(logo).hexdigest()):
            self.assertEqual(self.issues(), [])

    def test_other_author_is_rejected(self):
        p = self.root / "SIPS/sip-12.md"
        p.write_text(p.read_text().replace(SILA_ISSUER, "Third Party"))
        self.assertTrue(any("issuer" in s for s in self.issues()))

    def test_dual_byline_is_rejected(self):
        p = self.root / "SIPS/sip-12.md"
        p.write_text(p.read_text().replace(SILA_ISSUER, SILA_ISSUER + ", Other"))
        self.assertTrue(any("issuer" in s for s in self.issues()))

    def test_tampered_logo_is_rejected(self):
        p = self.root / "assets/sila-logo.png"
        p.write_bytes(p.read_bytes() + b"changed")
        self.assertTrue(any("owner-approved" in s for s in self.issues()))

    def test_missing_rights_record_is_rejected(self):
        (self.root / "VISUAL_CLEARANCES.json").unlink()
        self.assertTrue(any("record missing" in s for s in self.issues()))

    def test_missing_sips_rejected(self):
        (self.root / "SIPS/sip-12.md").unlink()
        self.assertIn("No SIP documents found", self.issues())

    def test_logo_png_signature_is_checked(self):
        (self.root / "assets/sila-logo.png").write_bytes(b"JPEG pretending to be PNG")
        self.assertTrue(any("not a PNG" in s for s in self.issues()))


if __name__ == "__main__":
    unittest.main()