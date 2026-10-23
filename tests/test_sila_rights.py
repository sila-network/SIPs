"""Tests verifying that rights review fails closed on nonuniform licenses."""
import tempfile
import unittest
from pathlib import Path
from tools.check_sila_rights import review


class SilaRightsTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "SIPS").mkdir()
        (self.root / "assets").mkdir()
        (self.root / "LICENSE.md").write_text("CC0 1.0 Universal\n", encoding="utf-8")

    def test_empty_clean_tree(self):
        self.assertEqual(review(self.root), [])

    def test_missing_general_license(self):
        (self.root / "LICENSE.md").unlink()
        self.assertTrue(any("LICENSE.md" in s for s in review(self.root)))

    def test_restricted_proposal(self):
        (self.root / "SIPS/sip-10.md").write_text("Attribution-NonCommercial-ShareAlike", encoding="utf-8")
        self.assertTrue(any("sip-10" in s for s in review(self.root)))

    def test_restricted_asset_license(self):
        path = self.root / "assets/sip-20/LICENSE"
        path.parent.mkdir()
        path.write_text("Creative Commons Attribution-NonCommercial-NoDerivatives", encoding="utf-8")
        self.assertTrue(any("sip-20" in s for s in review(self.root)))

    def test_uncharted_pdf(self):
        path = self.root / "assets/sip-30/reference.pdf"
        path.parent.mkdir()
        path.write_bytes(b"%PDF-1.4\n")
        self.assertTrue(any("reference.pdf" in s for s in review(self.root)))

    def test_code_snippet_copyleft_notice(self):
        path = self.root / "SIPS/sip-40.md"
        path.write_text("// SPDX-License-Identifier: AGPL-3.0\n", encoding="utf-8")
        self.assertTrue(any("AGPL-3.0" in s for s in review(self.root)))

    def test_mit_code_missing_license(self):
        path = self.root / "assets/sip-50/example.sol"
        path.parent.mkdir()
        path.write_text("// SPDX-License-Identifier: MIT\n", encoding="utf-8")
        self.assertTrue(any("MIT" in s for s in review(self.root)))

    def test_mit_code_with_license(self):
        path = self.root / "assets/sip-50/example.sol"
        path.parent.mkdir()
        path.write_text("// SPDX-License-Identifier: MIT\n", encoding="utf-8")
        (path.parent / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        self.assertEqual(review(self.root), [])

    def test_image_without_explicit_clearance(self):
        path = self.root / "assets/sip-70/picture.png"
        path.parent.mkdir()
        path.write_bytes(b"not a permitted image")
        self.assertTrue(any("positive supporting-asset" in s for s in review(self.root)))

    def test_cleared_code_spdx_marker(self):
        path = self.root / "assets/sip-80/example.sol"
        path.parent.mkdir()
        path.write_text("// SPDX-License-Identifier: CC0-1.0\n", encoding="utf-8")
        self.assertEqual(review(self.root), [])

    def test_conditional_material_requires_individual_notice(self):
        path = self.root / "assets/sip-8222/poseidon/poseidon.pdf"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"%PDF-1.4\n")
        self.assertTrue(any("THIRD_PARTY_NOTICES.md" in s for s in review(self.root)))

    def test_conditional_notice_needs_author_and_license(self):
        path = self.root / "assets/sip-8222/poseidon/poseidon.pdf"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"%PDF-1.4\n")
        (self.root / "THIRD_PARTY_NOTICES.md").write_text(
            "assets/sip-8222/poseidon/poseidon.pdf - CC BY 4.0", encoding="utf-8")
        self.assertTrue(any("Lorenzo Grassi" in s for s in review(self.root)))

    def test_mit_author_notice_cannot_be_erased(self):
        source = self.root / "assets/sip-7885/solidity/src/ZKNOX_NTT.sol"
        source.parent.mkdir(parents=True)
        source.write_text("// SPDX-License-Identifier: MIT\n", encoding="utf-8")
        (source.parent / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        self.assertTrue(any("Renaud Dubois" in s for s in review(self.root)))

    def test_attribution_license_in_asset(self):
        path = self.root / "assets/sip-60/semver.md"
        path.parent.mkdir()
        path.write_text("https://creativecommons.org/licenses/by/3.0/", encoding="utf-8")
        self.assertTrue(any("CC BY 3.0" in s for s in review(self.root)))


if __name__ == "__main__":
    unittest.main()
