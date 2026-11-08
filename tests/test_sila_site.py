"""Sila website acceptance, accessibility, output and link security tests."""
from __future__ import annotations

from datetime import date
import json
import shutil
from pathlib import Path
import tempfile
import unittest
from xml.etree import ElementTree as ET

from tools.sila import ROOT, SETTINGS, build_site, read_collection, verify_site
from tools.sila_site import (
    CATEGORIES, SiteError, build_site as generate,
    feed_xml, inline, layout, markdown, page_document, page_index,
    slug, verify_site as verify,
)


class SiteTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name) / "site"
        self.documents = read_collection()
        self.statuses = SETTINGS["governance"]["statuses"]
        build_site(self.output, self.documents)

    def page(self, value: str) -> str:
        return (self.output / value).read_text(encoding="utf-8")

    def test_01_existing_sila_content_builds(self) -> None:
        verify_site(self.output, self.documents)
        verify(self.output, self.documents, self.statuses)

    def test_02_index_contains_actual_sila_proposal(self) -> None:
        html = self.page("index.html")
        self.assertIn("SIP-1", html)
        self.assertIn("Sila Proposal Governance", html)
        self.assertIn("<strong>1</strong><span>Original proposal documents</span>", html)
        self.assertIn("Original proposal documents", html)

    def test_03_site_never_claims_approval(self) -> None:
        home = self.page("index.html")
        detail = self.page("SIPS/sip-1.html")
        self.assertIn("Draft", home)
        self.assertIn("Draft", detail)
        self.assertIn("network activation is a separate process", home.lower())

    def test_04_category_pages_exist_for_empty_categories(self) -> None:
        for item in CATEGORIES:
            path = f"categories/{slug(item)}.html"
            self.assertTrue((self.output / path).exists(), item)
        self.assertIn("No Sila proposals", self.page("categories/core.html"))
        self.assertIn("Sila Proposal Governance", self.page("categories/meta.html"))

    def test_05_status_pages_are_based_on_actual_documents(self) -> None:
        for item in self.statuses:
            self.assertTrue((self.output / "statuses" / f"{slug(item)}.html").is_file())
        self.assertIn("Sila Proposal Governance", self.page("statuses/draft.html"))
        self.assertIn("No Sila proposals", self.page("statuses/final.html"))

    def test_06_category_and_status_navigation(self) -> None:
        self.assertIn('href="core.html"', self.page("categories/index.html"))
        self.assertIn('href="draft.html"', self.page("statuses/index.html"))

    def test_07_details_preserve_true_metadata(self) -> None:
        detail = self.page("SIPS/sip-1.html")
        self.assertIn("Ahmed Ibrahim, Jihad Mustafa", detail)
        self.assertIn("2026-11-05", detail)
        self.assertIn("Sila Proposal Governance", detail)
        self.assertIn('class="document-meta"', detail)

    def test_08_details_render_original_governance_figure(self) -> None:
        detail = self.page("SIPS/sip-1.html")
        self.assertIn("Idea --&gt; Draft", detail)
        self.assertIn('<pre><code>', detail)

    def test_original_sila_diagram_is_rendered_and_local(self) -> None:
        page = self.page("SIPS/sip-1.html")
        self.assertIn('<img class="sila-diagram" src="../assets/sip-1/process.svg"', page)
        self.assertIn('alt="Original Sila proposal states', page)
        self.assertTrue((self.output / "assets/sip-1/process.svg").is_file())
        verify(self.output, self.documents, self.statuses)

    def test_original_sila_diagram_svg_is_safe(self) -> None:
        from tools.sila_site import validate_original_svg
        source = ROOT / "assets/sip-1/process.svg"
        validate_original_svg(source)
        content = source.read_text(encoding="utf-8")
        self.assertIn("Sila native proposal governance flow", content)
        self.assertNotIn("<script", content)
        self.assertNotIn("<foreignObject", content)
        self.assertNotIn("https://", content)

    def test_original_sila_diagram_rejects_script_elements(self) -> None:
        from tools.sila_site import validate_original_svg
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "unsafe.svg"
            source.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"><script>unsafe()</script></svg>',
                encoding="utf-8",
            )
            with self.assertRaises(SiteError):
                validate_original_svg(source)

    def test_original_sila_diagram_rejects_external_dependencies(self) -> None:
        from tools.sila_site import validate_original_svg
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "unsafe.svg"
            source.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"><rect fill="url(https://invalid.local/image)"/></svg>',
                encoding="utf-8",
            )
            with self.assertRaises(SiteError):
                validate_original_svg(source)

    def test_remote_image_in_document_is_escaped(self) -> None:
        rendered = inline("![remote](https://example.org/remote.svg)")
        self.assertNotIn("<img", rendered)

    def test_09_generated_toc_links_are_real(self) -> None:
        detail = self.page("SIPS/sip-1.html")
        self.assertIn('href="#security-considerations"', detail)
        self.assertIn('id="security-considerations"', detail)

    def test_10_search_input_and_filters_present(self) -> None:
        html = self.page("index.html")
        for name in ('id="sila-search"', 'id="sila-category"', 'id="sila-status"',
                     'id="result-count"', 'id="search-empty"'):
            self.assertIn(name, html)

    def test_11_search_json_contains_only_issued_documents(self) -> None:
        records = json.loads(self.page("search.json"))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["number"], 1)
        self.assertEqual(records[0]["category"], "Meta")
        self.assertEqual(records[0]["status"], "Draft")
        self.assertEqual(records[0]["path"], "SIPS/sip-1.html")

    def test_12_search_is_progressive_and_local(self) -> None:
        script = self.page("assets/site.js")
        self.assertIn("addEventListener", script)
        self.assertIn("card.hidden", script)
        self.assertNotIn("fetch(", script)
        self.assertNotIn("eval(", script)
        self.assertNotIn("XMLHttpRequest", script)

    def test_13_css_has_original_mobile_layout(self) -> None:
        sheet = self.page("assets/site.css")
        self.assertIn("@media (max-width: 690px)", sheet)
        self.assertIn(":focus-visible", sheet)
        self.assertIn("prefers-reduced-motion", sheet)
        self.assertNotIn("@import", sheet)

    def test_14_no_remote_scripts_or_styles(self) -> None:
        for relative in ("index.html", "SIPS/sip-1.html", "categories/index.html"):
            html = self.page(relative)
            self.assertIn('src="../assets/site.js"' if relative != "index.html" else 'src="assets/site.js"', html)
            self.assertNotIn('src="https:', html)
            self.assertNotIn('stylesheet" href="https:', html)

    def test_15_feed_tracks_one_real_sila_proposal(self) -> None:
        feed = ET.parse(self.output / "feed.xml")
        entries = feed.findall("./channel/item")
        self.assertEqual(len(entries), 1)
        self.assertIn("SIP-1", entries[0].findtext("title"))
        self.assertIn("sila/native-foundation", entries[0].findtext("link"))
        self.assertIn("Draft", entries[0].findtext("description"))

    def test_16_rights_document_link_resolves(self) -> None:
        self.assertTrue((self.output / "LICENSE.md").is_file())
        self.assertIn('href="../LICENSE.md"', self.page("SIPS/sip-1.html"))
        verify(self.output, self.documents, self.statuses)

    def test_17_sanitizes_raw_script_content(self) -> None:
        result = markdown("## Section\n\n<script>alert(1)</script>")
        self.assertIn("&lt;script&gt;", result)
        self.assertNotIn("<script>", result)

    def test_18_sanitizes_code_blocks(self) -> None:
        fence = chr(96) * 3
        text = markdown(f"{fence}\n<img src=x onerror=bad>\n{fence}")
        self.assertIn("&lt;img", text)
        self.assertNotIn("<img", text)

    def test_19_rejects_unsafe_link_scheme(self) -> None:
        content = inline("[unsafe](javascript:bad)")
        self.assertNotIn("<a href=", content)

    def test_20_escapes_external_link_attributes(self) -> None:
        result = inline("[safe](https://www.rfc-editor.org/a?x=1&y=2)")
        self.assertIn("x=1&amp;y=2", result)

    def test_21_escapes_user_title_and_description(self) -> None:
        html = layout('<tag>"', "<p>safe</p>", description='x" onload="evil')
        self.assertIn("&lt;tag&gt;", html)
        self.assertNotIn('content="x" onload="evil"', html)

    def test_22_close_code_fence_required(self) -> None:
        with self.assertRaises(SiteError):
            markdown(chr(96) * 3 + "\nunclosed")

    def test_23_duplicate_headings_get_unique_ids(self) -> None:
        body = "## Original Sila Topic\n\nTest\n\n## Original Sila Topic\n\nSecond"
        html = markdown(body)
        self.assertIn('id="original-sila-topic"', html)
        self.assertIn('id="original-sila-topic-2"', html)

    def test_24_missing_site_asset_blocks(self) -> None:
        (self.output / "assets/site.js").unlink()
        with self.assertRaisesRegex(SiteError, "missing generated"):
            verify(self.output, self.documents, self.statuses)

    def test_25_missing_html_navigation_link_blocks(self) -> None:
        index = self.output / "index.html"
        index.write_text(index.read_text().replace("categories/index.html", "categories/gone.html"))
        with self.assertRaisesRegex(SiteError, "broken generated Sila link"):
            verify(self.output, self.documents, self.statuses)

    def test_26_missing_internal_anchor_blocks(self) -> None:
        index = self.output / "index.html"
        index.write_text(index.read_text().replace('href="#catalog"', 'href="#not-here"'))
        with self.assertRaisesRegex(SiteError, "missing Sila page anchor"):
            verify(self.output, self.documents, self.statuses)

    def test_27_malformed_search_index_blocks(self) -> None:
        records = json.loads(self.page("search.json"))
        records[0]["number"] = 999
        (self.output / "search.json").write_text(json.dumps(records))
        with self.assertRaisesRegex(SiteError, "searchable index is incomplete"):
            verify(self.output, self.documents, self.statuses)

    def test_28_mismatched_feed_count_blocks(self) -> None:
        feed_path = self.output / "feed.xml"
        feed_path.write_text('<rss version="2.0"><channel></channel></rss>')
        with self.assertRaisesRegex(SiteError, "RSS feed is inconsistent"):
            verify(self.output, self.documents, self.statuses)

    def test_29_external_script_is_not_allowed(self) -> None:
        index = self.output / "index.html"
        index.write_text(index.read_text().replace('src="assets/site.js"', 'src="https://outside.invalid/script.js"'))
        with self.assertRaisesRegex(SiteError, "externally hosted"):
            verify(self.output, self.documents, self.statuses)

    def test_30_build_does_not_overwrite_sila_source_root(self) -> None:
        with self.assertRaisesRegex(SiteError, "unsafe output directory"):
            generate(ROOT, ROOT, self.documents, self.statuses)

    def test_31_build_cannot_overwrite_original_proposals(self) -> None:
        with self.assertRaisesRegex(SiteError, "unsafe output directory"):
            generate(ROOT, ROOT / "SIPS", self.documents, self.statuses)

    def test_32_build_cannot_follow_output_symlink(self) -> None:
        link = self.output.parent / "symlink"
        link.symlink_to(ROOT / "SIPS", target_is_directory=True)
        with self.assertRaisesRegex(SiteError, "may not be a symlink"):
            generate(ROOT, link, self.documents, self.statuses)

    def test_33_rebuild_prunes_removed_generated_documents(self) -> None:
        original = self.documents[0]
        extra = dict(original[1])
        extra.update({"sip": "2", "title": "Hypothetical Sila rule", "description": "A test-only proposal."})
        synthetic = (ROOT / "SIPS/sip-2.md", extra, original[2])
        generate(ROOT, self.output, self.documents + [synthetic], self.statuses)
        self.assertTrue((self.output / "SIPS/sip-2.html").exists())
        generate(ROOT, self.output, self.documents, self.statuses)
        self.assertFalse((self.output / "SIPS/sip-2.html").exists())

    def test_34_synthetic_second_document_updates_counts(self) -> None:
        original = self.documents[0]
        extra = dict(original[1])
        extra.update({"sip": "2", "title": "Hypothetical Sila rule", "description": "A test-only proposal."})
        synthetic = (ROOT / "SIPS/sip-2.md", extra, original[2])
        generate(ROOT, self.output, self.documents + [synthetic], self.statuses)
        html = self.page("index.html")
        self.assertIn("<strong>2</strong><span>Original proposal documents</span>", html)
        self.assertEqual(len(json.loads(self.page("search.json"))), 2)

    def test_35_current_site_has_only_real_issued_docs(self) -> None:
        self.assertEqual(list((self.output / "SIPS").glob("*.html")), [self.output / "SIPS/sip-1.html"])

    def test_36_categories_match_sila_configuration(self) -> None:
        expected = tuple(SETTINGS["governance"]["categories"]) + ("Meta", "Informational")
        self.assertEqual(CATEGORIES, expected)

    def test_37_feed_item_links_to_real_source_branch(self) -> None:
        item = ET.fromstring(feed_xml([self.documents[0][1]])).find("./channel/item")
        self.assertEqual(item.findtext("link"), "https://github.com/sila-network/SIPs/blob/sila/native-foundation/SIPS/sip-1.md")

    def test_38_document_header_has_correct_status(self) -> None:
        html = page_document(self.documents[0][1], self.documents[0][2])
        self.assertIn("Draft", html)
        self.assertIn('class="document-layout"', html)

    def test_39_page_accessibility_structure(self) -> None:
        html = self.page("index.html")
        self.assertIn('aria-label="Main navigation"', html)
        self.assertIn('class="skip-link"', html)
        self.assertIn('role="status"', html)
        self.assertIn('id="main"', html)


    def test_invalid_search_json_is_reported_as_site_error(self) -> None:
        (self.output / "search.json").write_text("{not-json", encoding="utf-8")
        with self.assertRaisesRegex(SiteError, "invalid Sila searchable index"):
            verify(self.output, self.documents, self.statuses)

    def test_invalid_xml_is_reported_as_site_error(self) -> None:
        (self.output / "feed.xml").write_text("<rss><unclosed>", encoding="utf-8")
        with self.assertRaisesRegex(SiteError, "invalid Sila RSS XML"):
            verify(self.output, self.documents, self.statuses)

    def test_code_fence_with_trailing_content_is_not_a_closer(self) -> None:
        fence = chr(96) * 3
        body = (fence + "text\nfirst\n" + fence + "not-closed\n"
                + "still code\n" + fence + "\n")
        html = markdown(body)
        self.assertEqual(html.count("<pre><code>"), 1)
        self.assertIn(fence + "not-closed", html)
        self.assertIn("first\n" + fence + "not-closed\nstill code", html)

    def test_code_fence_matching_delimiter_closes_normally(self) -> None:
        fence = chr(96) * 3
        html = markdown(fence + "text\nexample\n" + fence + "\nFollowing.")
        self.assertIn("<pre><code>example</code></pre>", html)
        self.assertIn("<p>Following.</p>", html)

    def test_code_fence_does_not_close_on_shorter_delimiter(self) -> None:
        long = chr(96) * 4
        short = chr(96) * 3
        html = markdown(long + "text\nfirst\n" + short + "\nsecond\n" + long)
        self.assertIn("first\n" + short + "\nsecond", html)

    def test_fenced_heading_does_not_create_broken_table_of_contents(self) -> None:
        triple = chr(96) * 3
        meta = self.documents[0][1]
        body = self.documents[0][2] + (
            "\n" + triple + "md\n## Ghost Example\n" + triple + "\n"
        )
        html = page_document(meta, body)
        self.assertNotIn('href="#ghost-example"', html)
        self.assertIn("## Ghost Example", html)

    def test_multiple_original_diagrams_are_copied_into_site(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            shutil.copytree(ROOT / "assets", project / "assets")
            shutil.copyfile(ROOT / "LICENSE.md", project / "LICENSE.md")
            extra = project / "assets/sip-1/additional.svg"
            extra.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"><title>Sila figure</title></svg>',
                encoding="utf-8",
            )
            meta = self.documents[0][1]
            body = self.documents[0][2] + (
                "\n![Additional](../assets/sip-1/additional.svg)\n"
            )
            records = [(project / "SIPS/sip-1.md", meta, body)]
            generate(project, self.output, records, self.statuses)
            self.assertTrue((self.output / "assets/sip-1/additional.svg").is_file())
            verify(self.output, records, self.statuses)

    def test_fenced_example_figure_is_not_published(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            shutil.copytree(ROOT / "assets", project / "assets")
            shutil.copyfile(ROOT / "LICENSE.md", project / "LICENSE.md")
            triple = chr(96) * 3
            body = self.documents[0][2] + (
                "\n" + triple + "md\n![Sample](../assets/sip-1/example.svg)\n"
                + triple + "\n"
            )
            records = [(project / "SIPS/sip-1.md", self.documents[0][1], body)]
            generate(project, self.output, records, self.statuses)
            self.assertFalse((self.output / "assets/sip-1/example.svg").exists())

    def test_existing_generated_index_symlink_cannot_overwrite_outside_source(self) -> None:
        victim = self.output.parent / "private-document.md"
        victim.write_text("protected Sila document", encoding="utf-8")
        target = self.output / "index.html"
        target.unlink()
        target.symlink_to(victim)
        with self.assertRaisesRegex(SiteError, "destination must not be a symlink"):
            generate(ROOT, self.output, self.documents, self.statuses)
        self.assertEqual(victim.read_text(encoding="utf-8"), "protected Sila document")

    def test_existing_generated_asset_symlink_cannot_overwrite_outside_source(self) -> None:
        victim = self.output.parent / "private-stylesheet.css"
        victim.write_text("protected Sila stylesheet", encoding="utf-8")
        target = self.output / "assets/site.css"
        target.unlink()
        target.symlink_to(victim)
        with self.assertRaises(SiteError):
            generate(ROOT, self.output, self.documents, self.statuses)
        self.assertEqual(victim.read_text(encoding="utf-8"), "protected Sila stylesheet")

    def test_existing_diagram_symlink_cannot_overwrite_outside_source(self) -> None:
        victim = self.output.parent / "private-diagram.svg"
        victim.write_text("protected Sila diagram", encoding="utf-8")
        target = self.output / "assets/sip-1/process.svg"
        target.unlink()
        target.symlink_to(victim)
        with self.assertRaises(SiteError):
            generate(ROOT, self.output, self.documents, self.statuses)
        self.assertEqual(victim.read_text(encoding="utf-8"), "protected Sila diagram")

    def test_40_no_placeholder_publication_record(self) -> None:
        self.assertEqual(len(self.documents), 1)
        self.assertEqual(self.documents[0][1]["status"], "Draft")


if __name__ == "__main__":
    unittest.main()
