#!/usr/bin/env python3
"""Verify Jekyll generated each Sila proposal and the generated HTML is present.

This is a build completeness check, not protocol parity or rights clearance.
"""
from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class DocumentMarkup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.article = False
        self.h1 = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if tag == "article" and "sip-document" in (data.get("class") or "").split():
            self.article = True
        if tag == "h1":
            self.h1 = True


class LinkMarkup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []
        self.anchors: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        for name in ("id", "name"):
            if data.get(name):
                self.anchors.add(data[name])
        target = data.get("href") if tag in ("a", "link") else data.get("src") if tag in ("img", "script") else None
        if target:
            self.links.append(target)


def internal_link_failures(destination: Path) -> list[str]:
    """Report site-internal links whose page or anchor was not generated."""
    pages = {page.resolve(): page.read_text(encoding="utf-8") for page in destination.rglob("*.html")}
    parsed: dict[Path, LinkMarkup] = {}
    for page, html in pages.items():
        parser = LinkMarkup()
        parser.feed(html)
        parsed[page] = parser
    failures: list[str] = []
    for page, parser in sorted(parsed.items()):
        for link in parser.links:
            if re.match(r"^[a-z][a-z0-9+.-]*:", link, re.IGNORECASE) or link.startswith("//"):
                continue  # external or non-HTTP scheme; checked elsewhere
            path_part, _, fragment = link.partition("#")
            path_part = path_part.split("?", 1)[0]
            if not path_part:
                target = page
            elif path_part.startswith("/"):
                target = destination.resolve() / path_part.lstrip("/")
            else:
                target = page.parent / path_part
            candidates = [target, target.with_name(target.name + ".html"), target / "index.html"]
            found = next((c.resolve() for c in candidates if c.is_file()), None)
            where = page.relative_to(destination.resolve())
            if found is None:
                failures.append(f"broken internal link in {where}: {link}")
                continue
            if fragment and found.suffix == ".html":
                anchors = parsed[found].anchors if found in parsed else LinkMarkup().anchors
                if fragment not in anchors:
                    failures.append(f"missing anchor in {where}: {link}")
    return failures


def verify(source: Path, destination: Path) -> list[str]:
    failures: list[str] = []
    homepage = destination / "index.html"
    if not homepage.is_file():
        failures.append("missing generated homepage")
    else:
        html = homepage.read_text(encoding="utf-8")
        if "Sila Protocol Specifications" not in html:
            failures.append("homepage lacks Sila site identity")
    if not (destination / "assets/site.css").is_file():
        failures.append("missing site stylesheet")

    proposals = sorted((source / "SIPS").glob("sip-*.md"))
    if not proposals:
        failures.append("no SIP documents in the source tree")
    for original in proposals:
        if not re.fullmatch(r"sip-[0-9]+\.md", original.name):
            failures.append(f"unexpected proposal filename: {original.name}")
            continue
        rendered = destination / "SIPS" / f"{original.stem}.html"
        if not rendered.is_file():
            failures.append(f"missing generated page: {rendered.relative_to(destination)}")
            continue
        page = rendered.read_text(encoding="utf-8")
        parser = DocumentMarkup()
        parser.feed(page)
        if not parser.article or not parser.h1:
            failures.append(f"proposal missing title or article markup: {original.name}")
        if f"SIP-{original.stem.removeprefix('sip-')}" not in page:
            failures.append(f"proposal number absent: {original.name}")

    failures.extend(internal_link_failures(destination))

    # Do not mistake one-process-document success for complete-corpus readiness.
    print(f"Generated {len(proposals)} SIP pages; source scope: {source}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path, nargs="?", default=Path("_site"))
    parser.add_argument("--source", type=Path, default=Path("."))
    arguments = parser.parse_args()
    failed = verify(arguments.source, arguments.destination)
    for line in failed:
        print(f"FAIL: {line}", file=sys.stderr)
    if failed:
        return 1
    print("PASS: static site build completeness (not 100/100)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
