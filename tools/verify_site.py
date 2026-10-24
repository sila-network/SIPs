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
