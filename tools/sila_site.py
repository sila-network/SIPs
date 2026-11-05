"""Sila-native static specifications site. No external site runtime dependencies."""
from __future__ import annotations

from collections import Counter
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET


CATEGORIES = ("Core", "Networking", "Interface", "SRC", "Meta", "Informational")
HEADING = re.compile(r"^(#{1,4})[ \t]+(.+?)\s*$")
INLINE = re.compile(r"(\[[^\]\n]+\]\([^)]+\)|\*\*[^*\n]+\*\*|\x60[^\x60\n]+\x60)")
FENCE = re.compile(r"^[ \t]{0,3}(\x60{3,}|~{3,})")
LIST_ITEM = re.compile(r"^[ \t]*[-*][ \t]+(.+)$")
ORIGIN = "https://github.com/sila-network/SIPs/blob/sila/native-foundation/SIPS/"


class SiteError(ValueError):
    """A Sila site output is incomplete or unsafe."""


def safe(text: object) -> str:
    return escape(str(text), quote=True)


def slug(value: str) -> str:
    result = re.sub(r"[^\w -]", "", value.lower()).strip().replace(" ", "-")
    return result or "section"


def inline(text: str) -> str:
    output = []
    for token in INLINE.split(text):
        if token.startswith("[") and "](" in token and token.endswith(")"):
            label, href = token[1:-1].split("](", 1)
            parsed = urlsplit(href)
            local = not parsed.scheme and not parsed.netloc and not href.startswith(("/", "\\"))
            external = parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password
            if local or external:
                output.append(f'<a href="{safe(href)}">{safe(label)}</a>')
            else:
                output.append(safe(token))
        elif token.startswith("**") and token.endswith("**"):
            output.append("<strong>" + safe(token[2:-2]) + "</strong>")
        elif token.startswith(chr(96)) and token.endswith(chr(96)):
            output.append("<code>" + safe(token[1:-1]) + "</code>")
        else:
            output.append(safe(token))
    return "".join(output)


def markdown(body: str) -> str:
    output = []
    paragraph = []
    bullets = []
    code = []
    opened = ""
    width = 0
    ids: dict[str, int] = {}

    def flush_text() -> None:
        if paragraph:
            output.append("<p>" + inline(" ".join(paragraph)) + "</p>")
            paragraph.clear()
        if bullets:
            output.append("<ul>" + "".join("<li>" + inline(item) + "</li>" for item in bullets) + "</ul>")
            bullets.clear()

    for line in body.splitlines():
        marker = FENCE.match(line)
        if marker:
            seq = marker.group(1)
            if not opened:
                flush_text()
                opened, width = seq[0], len(seq)
            elif seq[0] == opened and len(seq) >= width:
                output.append("<pre><code>" + safe("\n".join(code)) + "</code></pre>")
                opened, width = "", 0
                code.clear()
            else:
                code.append(line)
            continue
        if opened:
            code.append(line)
            continue
        if not line.strip():
            flush_text()
            continue
        head = HEADING.fullmatch(line)
        if head:
            flush_text()
            level = len(head.group(1))
            anchor = slug(head.group(2))
            ids[anchor] = ids.get(anchor, 0) + 1
            if ids[anchor] > 1:
                anchor += f"-{ids[anchor]}"
            output.append(f'<h{level} id="{safe(anchor)}">{inline(head.group(2))}</h{level}>')
            continue
        item = LIST_ITEM.fullmatch(line)
        if item:
            if paragraph:
                flush_text()
            bullets.append(item.group(1))
            continue
        if bullets:
            flush_text()
        paragraph.append(line.strip())
    if opened:
        raise SiteError("unclosed Sila documentation code fence")
    flush_text()
    return "\n".join(output)


def label(meta: dict) -> str:
    return meta.get("category", meta["type"])


def location(meta: dict) -> str:
    return f'SIPS/sip-{meta["sip"]}.html'


def entry(meta: dict, prefix: str = "") -> str:
    number = meta["sip"]
    title = meta["title"]
    classification = label(meta)
    status = meta["status"]
    searchable = " ".join(str(meta[k]) for k in ("sip", "title", "description", "author", "type", "status"))
    searchable += " " + classification
    return (
        f'<li class="proposal-card" data-sila-proposal data-search="{safe(searchable.lower())}" '
        f'data-category="{safe(slug(classification))}" data-status="{safe(slug(status))}">'
        f'<div class="proposal-card__top"><span class="proposal-id">SIP-{safe(number)}</span>'
        f'<span class="status-pill status-{safe(slug(status))}">{safe(status)}</span></div>'
        f'<h3><a href="{safe(prefix + location(meta))}">{safe(title)}</a></h3>'
        f'<p>{safe(meta["description"])}</p>'
        f'<div class="proposal-foot"><span>{safe(classification)}</span>'
        f'<span>{safe(meta["created"])}</span></div></li>'
    )


def layout(title: str, content: str, prefix: str = "", *, description: str = "") -> str:
    home = safe(prefix + "index.html")
    categories = safe(prefix + "categories/index.html")
    statuses = safe(prefix + "statuses/index.html")
    feed = safe(prefix + "feed.xml")
    css = safe(prefix + "assets/site.css")
    script = safe(prefix + "assets/site.js")
    return (
        '<!doctype html>\n<html lang="en"><head>'
        '<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<meta name="description" content="{safe(description or "Original Sila specifications and proposals.")}">'
        '<meta name="color-scheme" content="light">'
        f'<title>{safe(title)} · Sila Network</title>'
        f'<link rel="stylesheet" href="{css}">'
        f'<link rel="alternate" type="application/rss+xml" title="Sila proposals" href="{feed}">'
        f'<script src="{script}" defer></script>'
        '</head><body><a class="skip-link" href="#main">Skip to content</a>'
        '<header class="site-header"><div class="shell nav-shell">'
        f'<a class="brand" href="{home}" aria-label="Sila Network home">'
        '<span class="brand-mark" aria-hidden="true">S</span><span>SILA<span class="brand-light"> NETWORK</span></span></a>'
        '<nav class="main-nav" aria-label="Main navigation">'
        f'<a href="{home}">Proposals</a>'
        f'<a href="{categories}">Categories</a>'
        f'<a href="{statuses}">Statuses</a>'
        f'<a href="{feed}">RSS</a></nav></div></header>'
        f'<main id="main" class="shell">{content}</main>'
        '<footer class="site-footer"><div class="shell footer-layout">'
        '<div><strong>SILA NETWORK</strong><p>Original specifications. Verified publication is not protocol activation.</p></div>'
        '<div><a href="https://github.com/sila-network/SIPs">Source repository</a>'
        '<span aria-hidden="true"> · </span>'
        '<a href="https://sila-magicians.discourse.group/">Sila community</a></div>'
        '</div></footer></body></html>\n'
    )


def listing(documents: list[dict], prefix: str = "", *, search: bool = False) -> str:
    if documents:
        cards = "".join(entry(meta, prefix) for meta in sorted(documents, key=lambda x: int(x["sip"])))
        result = f'<ul class="proposal-list" id="proposal-list">{cards}</ul>'
    else:
        result = '<p class="empty-static">No Sila proposals in this section yet.</p>'
    if search and documents:
        result = (
            '<section class="directory-tools" aria-label="Find Sila proposals">'
            '<div class="form-field"><label for="sila-search">Search proposals</label>'
            '<input id="sila-search" type="search" placeholder="Number, title, author, topic…" '
            'autocomplete="off" aria-controls="proposal-list"></div>'
            '<div class="form-field"><label for="sila-category">Category</label>'
            '<select id="sila-category" aria-controls="proposal-list"><option value="">All categories</option>'
            + "".join(f'<option value="{slug(key)}">{safe(key)}</option>' for key in CATEGORIES)
            + '</select></div><div class="form-field"><label for="sila-status">Status</label>'
            '<select id="sila-status" aria-controls="proposal-list"><option value="">All statuses</option>'
            + "".join(f'<option value="{slug(key)}">{safe(key)}</option>' for key in (
                "Idea", "Draft", "Review", "Last Call", "Final", "Stagnant", "Withdrawn", "Living"
            )) + '</select></div></section>'
            f'<p class="result-count" id="result-count" role="status" aria-live="polite">{len(documents)} proposals</p>'
            + result + '<p id="search-empty" class="empty-static" hidden>No proposals match these filters.</p>'
        )
    return result


def page_index(documents: list[dict]) -> str:
    counts = Counter(meta["status"] for meta in documents)
    draft = counts.get("Draft", 0)
    hero = (
        '<section class="hero">'
        '<div class="hero-copy"><div class="eyebrow"><span class="pulse" aria-hidden="true"></span>'
        'SILA · SPECIFICATIONS</div>'
        '<h1>Standards begin<br><span>with clarity.</span></h1>'
        '<p>Explore original Sila improvement proposals. Every document has an explicit '
        'governance state; publication never implies that a protocol rule is active.</p>'
        '<div class="hero-actions"><a class="action-primary" href="#catalog">Browse proposals</a>'
        '<a class="action-secondary" href="categories/index.html">Explore categories</a></div></div>'
        '<div class="hero-art" aria-hidden="true"><div class="orbit orbit-one"></div>'
        '<div class="orbit orbit-two"></div><div class="orbit orbit-three"></div>'
        '<span class="orbital-symbol">S</span></div></section>'
        '<section class="metrics" aria-label="Current proposal counts">'
        f'<div><strong>{len(documents)}</strong><span>Original proposal documents</span></div>'
        f'<div><strong>{draft}</strong><span>Draft proposals</span></div>'
        f'<div><strong>{len(counts)}</strong><span>Statuses represented</span></div></section>'
    )
    content = hero + '<section class="catalog" id="catalog"><div class="section-lead">'
    content += '<div><p class="overline">Document collection</p><h2>All Sila proposals</h2></div>'
    content += '<p class="section-description">Search and filter the documents that actually exist.</p></div>'
    content += listing(documents, search=True)
    content += '</section><aside class="note-panel"><strong>Governance status matters</strong>'
    content += '<p>A Draft is a proposal, not an approval. Final requires a verified Sila decision and '
    content += 'network activation is a separate process.</p></aside>'
    return layout("Sila improvement proposals", content, description="Browse, search and filter original Sila protocol proposals.")


def page_categories(documents: list[dict]) -> str:
    counts = Counter(label(meta) for meta in documents)
    cards = "".join(
        f'<li><a class="directory-card" href="{slug(item)}.html">'
        f'<span class="directory-card__name">{safe(item)}</span>'
        f'<span class="directory-card__count">{counts[item]} proposals</span>'
        '<span class="directory-card__arrow" aria-hidden="true">→</span></a></li>'
        for item in CATEGORIES
    )
    body = ('<section class="page-lead"><p class="overline">Organization</p>'
            '<h1>Browse by category</h1>'
            '<p>All Sila categories are visible, including those without issued proposals.</p></section>'
            f'<ul class="directory-grid">{cards}</ul>')
    return layout("Proposal categories", body, "../")


def page_statuses(documents: list[dict], statuses: list[str]) -> str:
    counts = Counter(meta["status"] for meta in documents)
    cards = "".join(
        f'<li><a class="directory-card" href="{slug(item)}.html">'
        f'<span class="directory-card__name">{safe(item)}</span>'
        f'<span class="directory-card__count">{counts[item]} proposals</span>'
        '<span class="directory-card__arrow" aria-hidden="true">→</span></a></li>'
        for item in statuses
    )
    body = ('<section class="page-lead"><p class="overline">Governance</p>'
            '<h1>Proposal statuses</h1>'
            '<p>States describe the documents, not the activation status of the Sila network.</p></section>'
            f'<ul class="directory-grid">{cards}</ul>')
    return layout("Proposal statuses", body, "../")


def page_group(item: str, records: list[dict], *, kind: str) -> str:
    content = (
        f'<nav class="breadcrumb" aria-label="Breadcrumb"><a href="index.html">'
        f'{safe("Categories" if kind == "category" else "Statuses")}</a>'
        f'<span aria-hidden="true">/</span><span>{safe(item)}</span></nav>'
        f'<section class="page-lead"><p class="overline">{safe(kind.title())}</p>'
        f'<h1>{safe(item)}</h1>'
        f'<p>{len(records)} original Sila proposal documents in this {safe(kind)}.</p></section>'
    )
    content += listing(records, "../")
    return layout(f"{item} Sila proposals", content, "../")


def page_document(meta: dict, body: str) -> str:
    classification = label(meta)
    sections = [HEADING.fullmatch(line).group(2) for line in body.splitlines() if HEADING.fullmatch(line) and line.startswith("## ")]
    toc = "".join(f'<li><a href="#{safe(slug(section))}">{safe(section)}</a></li>' for section in sections)
    metadata = (
        ("Status", meta["status"]), ("Type", meta["type"]),
        ("Category", classification), ("Authors", meta["author"]),
        ("Created", meta["created"]),
    )
    definition = "".join(f"<div><dt>{safe(k)}</dt><dd>{safe(v)}</dd></div>" for k, v in metadata)
    title = f'SIP-{meta["sip"]}: {meta["title"]}'
    content = (
        '<nav class="breadcrumb" aria-label="Breadcrumb">'
        '<a href="../index.html">Proposals</a><span aria-hidden="true">/</span>'
        f'<span>SIP-{safe(meta["sip"])}</span></nav>'
        '<header class="document-head"><p class="overline">Sila improvement proposal</p>'
        f'<h1>{safe(title)}</h1><p class="document-summary">{safe(meta["description"])}</p>'
        f'<span class="status-pill status-{safe(slug(meta["status"]))}">{safe(meta["status"])}</span>'
        '</header><dl class="document-meta">' + definition + '</dl>'
        '<div class="document-layout"><aside class="toc"><h2>On this page</h2>'
        f'<ol>{toc}</ol></aside><article class="document-body">{markdown(body)}</article></div>'
        '<aside class="note-panel"><strong>Source and approval</strong>'
        '<p>This page is an independently generated preview of the Sila source. '
        'A document status is not proof of deployed protocol behavior.</p></aside>'
    )
    return layout(title, content, "../", description=meta["description"])


def feed_xml(documents: list[dict]) -> str:
    channel = ET.Element("rss", attrib={"version": "2.0"})
    data = ET.SubElement(channel, "channel")
    for key, value in (
        ("title", "Sila original proposals"),
        ("link", "https://github.com/sila-network/SIPs"),
        ("description", "Sila proposal documents; listing does not imply activation."),
        ("language", "en"),
    ):
        ET.SubElement(data, key).text = value
    for meta in sorted(documents, key=lambda m: int(m["sip"]), reverse=True):
        item = ET.SubElement(data, "item")
        url = ORIGIN + f'sip-{meta["sip"]}.md'
        for key, value in (
            ("title", f'SIP-{meta["sip"]}: {meta["title"]}'),
            ("link", url),
            ("guid", url),
            ("description", meta["description"] + f' (status: {meta["status"]})'),
        ):
            node = ET.SubElement(item, key)
            node.text = value
            if key == "guid":
                node.set("isPermaLink", "false")
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(channel, encoding="unicode") + "\n"


def build_site(root: Path, output: Path, documents: list[tuple[Path, dict, str]], statuses: list[str]) -> None:
    raw_output = Path(output)
    if raw_output.is_symlink():
        raise SiteError("output directory may not be a symlink")
    root, output = root.resolve(), raw_output.resolve()
    if (output == root or output in root.parents or output == Path(output.anchor)
            or (output.is_relative_to(root) and output != root / "_site")):
        raise SiteError("unsafe output directory")
    # Only the generated Sila page directories are cleaned, never user source files.
    output.mkdir(parents=True, exist_ok=True)
    for folder in ("SIPS", "categories", "statuses"):
        dest = output / folder
        if dest.is_symlink():
            raise SiteError("generated Sila site directory may not be a symlink")
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir()
    assets = output / "assets"
    if assets.is_symlink():
        raise SiteError("generated asset directory may not be a symlink")
    assets.mkdir(exist_ok=True)
    for asset in ("site.css", "site.js"):
        shutil.copyfile(root / "assets" / asset, assets / asset)
    shutil.copyfile(root / "LICENSE.md", output / "LICENSE.md")

    metadata = [meta for _, meta, _ in documents]
    (output / "index.html").write_text(page_index(metadata), encoding="utf-8")
    (output / "categories/index.html").write_text(page_categories(metadata), encoding="utf-8")
    (output / "statuses/index.html").write_text(page_statuses(metadata, statuses), encoding="utf-8")
    for group in CATEGORIES:
        chosen = [meta for meta in metadata if label(meta) == group]
        (output / "categories" / f"{slug(group)}.html").write_text(
            page_group(group, chosen, kind="category"), encoding="utf-8")
    for status in statuses:
        chosen = [meta for meta in metadata if meta["status"] == status]
        (output / "statuses" / f"{slug(status)}.html").write_text(
            page_group(status, chosen, kind="status"), encoding="utf-8")
    for _, meta, body in documents:
        (output / location(meta)).write_text(page_document(meta, body), encoding="utf-8")
    records = [
        dict(number=int(meta["sip"]), title=meta["title"], description=meta["description"],
             author=meta["author"], status=meta["status"], type=meta["type"],
             category=label(meta), created=meta["created"], path=location(meta))
        for meta in sorted(metadata, key=lambda m: int(m["sip"]))
    ]
    (output / "search.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "feed.xml").write_text(feed_xml(metadata), encoding="utf-8")


class LocalLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.ids: set[str] = set()
        self.external_assets = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        fields = dict(attrs)
        if fields.get("id"):
            self.ids.add(fields["id"])
        for attribute in (("href",) if tag in ("a", "link") else ("src",) if tag in ("script", "img") else ()):
            href = fields.get(attribute)
            if href:
                self.links.append(href)
                if tag in ("script", "img", "link") and urlsplit(href).scheme:
                    self.external_assets = True


def verify_site(output: Path, documents: list[tuple[Path, dict, str]], statuses: list[str]) -> None:
    output = output.resolve()
    expected = {"index.html", "search.json", "feed.xml", "LICENSE.md", "assets/site.css", "assets/site.js",
                "categories/index.html", "statuses/index.html"}
    expected.update(f"categories/{slug(item)}.html" for item in CATEGORIES)
    expected.update(f"statuses/{slug(item)}.html" for item in statuses)
    expected.update(location(meta) for _, meta, _ in documents)
    for relative in expected:
        target = output / relative
        if not target.is_file() or not target.stat().st_size:
            raise SiteError(f"missing generated Sila page or asset: {relative}")
    try:
        records = json.loads((output / "search.json").read_text(encoding="utf-8"))
        correct = {int(meta["sip"]): location(meta) for _, meta, _ in documents}
        if (not isinstance(records, list) or len(records) != len(documents)
                or {item["number"]: item["path"] for item in records} != correct):
            raise SiteError("Sila searchable index is incomplete")
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        raise SiteError("invalid Sila searchable index") from error
    try:
        feed = ET.parse(output / "feed.xml").getroot()
    except ET.ParseError as error:
        raise SiteError("invalid Sila RSS XML") from error
    if feed.tag != "rss" or len(feed.findall("./channel/item")) != len(documents):
        raise SiteError("Sila RSS feed is inconsistent with the specification collection")
    for relative in sorted(expected):
        if not relative.endswith(".html"):
            continue
        path = output / relative
        html = path.read_text(encoding="utf-8")
        if not html.startswith("<!doctype html>") or "<title>" not in html or 'id="main"' not in html:
            raise SiteError(f"invalid Sila HTML document: {relative}")
        parsed = LocalLinks()
        parsed.feed(html)
        if parsed.external_assets:
            raise SiteError(f"unexpected externally hosted Sila site asset: {relative}")
        for url in parsed.links:
            destination = urlsplit(url)
            if destination.scheme:
                if destination.scheme != "https":
                    raise SiteError(f"unsafe external Sila website URL: {url}")
                continue
            if destination.netloc or destination.path.startswith("/"):
                raise SiteError(f"unsafe Sila website path: {url}")
            linked = (path.parent / unquote(destination.path)).resolve() if destination.path else path.resolve()
            if not linked.is_relative_to(output) or not linked.is_file():
                raise SiteError(f"broken generated Sila link in {relative}: {url}")
            if destination.fragment and linked == path:
                if unquote(destination.fragment) not in parsed.ids:
                    raise SiteError(f"missing Sila page anchor in {relative}: {url}")
