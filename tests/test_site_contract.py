"""Tests for draft website output completeness; no legal/adoption claims."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.verify_site import verify


class SiteContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.source = self.root / "source"
        self.destination = self.root / "site"
        (self.source / "SIPS").mkdir(parents=True)
        (self.destination / "SIPS").mkdir(parents=True)
        (self.destination / "assets").mkdir()
        (self.source / "SIPS/sip-1.md").write_text("---\nsip: 1\n---\n")
        (self.destination / "index.html").write_text("Sila Protocol Specifications")
        (self.destination / "assets/site.css").write_text("body{}")
        (self.destination / "SIPS/sip-1.html").write_text('<article class="sip-document"><h1>SIP-1</h1></article>')

    def test_one_proposal_build_passes(self) -> None:
        self.assertEqual(verify(self.source, self.destination), [])

    def test_missing_page_fails(self) -> None:
        (self.destination / "SIPS/sip-1.html").unlink()
        self.assertTrue(any("missing generated page" in issue for issue in verify(self.source, self.destination)))

    def test_missing_article_fails(self) -> None:
        (self.destination / "SIPS/sip-1.html").write_text("<h1>SIP-1</h1>")
        self.assertTrue(any("markup" in issue for issue in verify(self.source, self.destination)))

    def test_missing_homepage_fails(self) -> None:
        (self.destination / "index.html").unlink()
        self.assertTrue(any("homepage" in issue for issue in verify(self.source, self.destination)))


if __name__ == "__main__":
    unittest.main()
