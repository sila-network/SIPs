"""Tests for the independent Sila proposal foundation."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import tempfile
import unittest

from tools.sila import (
    DENIED_IDENTITIES, ROOT, SilaError, audit, build_site, parse_document,
    read_collection, render_inline, render_markdown,
    verify_metadata, verify_site,
)

TODAY = date.today().isoformat()


def meta(**updates: str) -> dict[str, str]:
    initial = {
        "sip": "14",
        "title": "Original Sila rule",
        "description": "A test-only Sila proposal.",
        "author": "Ahmed Ibrahim",
        "status": "Draft",
        "type": "Meta",
        "created": TODAY,
    }
    initial.update(updates)
    return initial


class NativeMetadataTests(unittest.TestCase):
    def test_valid_proposal(self) -> None:
        verify_metadata(meta(), "sip-14.md", {14})

    def test_number_must_match_filename(self) -> None:
        with self.assertRaises(SilaError):
            verify_metadata(meta(), "sip-15.md", {14, 15})

    def test_no_foreign_authority(self) -> None:
        with self.assertRaises(SilaError):
            verify_metadata(meta(author="Unapproved Person"), "sip-14.md", {14})

    def test_no_unapproved_status(self) -> None:
        with self.assertRaises(SilaError):
            verify_metadata(meta(status="Activated"), "sip-14.md", {14})

    def test_standards_track_requires_category(self) -> None:
        with self.assertRaises(SilaError):
            verify_metadata(meta(type="Standards Track"), "sip-14.md", {14})

    def test_wrong_category_on_meta(self) -> None:
        with self.assertRaises(SilaError):
            verify_metadata(meta(category="Core"), "sip-14.md", {14})

    def test_last_call_requires_deadline(self) -> None:
        with self.assertRaises(SilaError):
            verify_metadata(meta(status="Last Call"), "sip-14.md", {14})

    def test_final_requires_real_approval(self) -> None:
        with self.assertRaises(SilaError):
            verify_metadata(meta(status="Final"), "sip-14.md", {14})

    def test_no_fake_dependency(self) -> None:
        with self.assertRaises(SilaError):
            verify_metadata(meta(requires="99"), "sip-14.md", {14})

    def test_no_self_dependency(self) -> None:
        with self.assertRaises(SilaError):
            verify_metadata(meta(requires="14"), "sip-14.md", {14})

    def test_future_creation_date_rejected(self) -> None:
        with self.assertRaises(SilaError):
            verify_metadata(meta(created=(date.today() + timedelta(days=1)).isoformat()), "sip-14.md", {14})

    def test_invalid_discussion_rejected(self) -> None:
        with self.assertRaises(SilaError):
            verify_metadata(meta(**{"discussions-to": "https://example.com/not-sila"}), "sip-14.md", {14})

    def test_duplicate_metadata_rejected(self) -> None:
        data = "---\nsip: 14\nsip: 14\n---\nBody"
        with self.assertRaises(SilaError):
            parse_document(data)

    def test_nested_metadata_rejected(self) -> None:
        data = "---\nsip: [14]\n---\nBody"
        with self.assertRaises(SilaError):
            parse_document(data)


class NativeContentTests(unittest.TestCase):
    def test_original_sip_one_is_consistent(self) -> None:
        entries = read_collection()
        self.assertEqual([item[1]["sip"] for item in entries], ["1"])
        self.assertEqual(entries[0][1]["status"], "Draft")

    def test_html_is_escaped(self) -> None:
        rendered = render_markdown("## Title\n\n<script>alert(1)</script>")
        self.assertIn("&lt;script&gt;", rendered)
        self.assertNotIn("<script>", rendered)

    def test_inline_code_is_escaped(self) -> None:
        rendered = render_inline(chr(96) + "<test>" + chr(96))
        self.assertIn("&lt;test&gt;", rendered)

    def test_fence_is_closed(self) -> None:
        with self.assertRaises(SilaError):
            render_markdown(chr(96) * 3 + "\ncontent")

    def test_identity_denial_rule_is_active(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "candidate.md"
            target.write_text("Sila candidate " + DENIED_IDENTITIES[0], encoding="utf-8")
            self.assertGreater(audit(Path(folder)), 0)

    def test_extensionless_source_identity_is_audited(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "Makefile"
            source.write_text("Original Sila " + DENIED_IDENTITIES[0], encoding="utf-8")
            self.assertGreater(audit(Path(folder)), 0)

    def test_dotfile_configuration_identity_is_audited(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / ".gitignore"
            source.write_text("Original Sila " + DENIED_IDENTITIES[0], encoding="utf-8")
            self.assertGreater(audit(Path(folder)), 0)

    def test_binary_extensionless_source_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "configuration"
            source.write_bytes(bytes([255, 254, 0]))
            self.assertGreater(audit(Path(folder)), 0)

    def test_actual_sila_source_audit(self) -> None:
        self.assertEqual(audit(ROOT), 0)

    def test_site_generation_and_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "site"
            entries = read_collection()
            build_site(destination, entries)
            verify_site(destination, entries)
            self.assertIn("Sila", (destination / "index.html").read_text())


if __name__ == "__main__":
    unittest.main()
