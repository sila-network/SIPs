#!/usr/bin/env python3
"""Independent Sila proposal validation and static-site generation."""

from __future__ import annotations

import argparse
from datetime import date
from html import escape
from pathlib import Path
import re
import shutil
import sys
import tomllib
from urllib.parse import urlsplit

# Use the same Sila-native specification engine for checks and site builds.
if __package__:
    from .sila_specs import ProposalError, validate_repository as validate_sila_repository
else:
    from sila_specs import ProposalError, validate_repository as validate_sila_repository

if __package__:
    from .sila_site import SiteError, build_site as render_site, verify_site as check_site
else:
    from sila_site import SiteError, build_site as render_site, verify_site as check_site


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = tomllib.loads((ROOT / "config" / "sila.toml").read_text(encoding="utf-8"))
DOC_DIR = ROOT / "SIPS"
FENCE = chr(96) * 3
VALID_FIELDS = {
    "sip", "title", "description", "author", "status", "type", "category",
    "created", "requires", "discussions-to", "last-call-deadline",
    "withdrawal-reason", "approval-ref", "implementation-ref"
}
TEXT_SUFFIXES = {".md", ".py", ".toml", ".json", ".yml", ".yaml", ".html", ".css", ".js", ".xml", ".svg", ".sh", ".txt"}
IGNORE_DIRS = {".git", "_site", "__pycache__", ".venv"}
# Denial signatures are encoded to avoid inserting a foreign protocol identity
# into a Sila-owned source file, including when auditing the auditor itself.
DENIED_IDENTITIES = tuple(bytes.fromhex(value).decode("ascii") for value in (
    "657468657265756d", "6574685f", "65766d", "6569702d",
    "6572632d", "657468657273", "65746865727363616e",
))
INLINE = re.compile(r"(\[[^\]\n]+\]\([^)]+\)|\*\*[^*\n]+\*\*|\x60[^\x60\n]+\x60)")
LINKS = re.compile(r"\[[^\]\n]+\]\(([^)\s]+)\)")


class SilaError(ValueError):
    """A Sila candidate violates a rule that must not be bypassed."""


def parse_document(source: str) -> tuple[dict[str, str], str]:
    """Read the intentionally restricted, flat YAML front matter used by Sila."""
    match = re.fullmatch(r"---\n(.*?)\n---\n(.*)", source.replace("\r\n", "\n"), re.S)
    if not match:
        raise SilaError("expected a complete flat YAML front matter block")
    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        pair = re.fullmatch(r"([a-z][a-z-]*):[ \t]*(.*)", line)
        if not pair:
            raise SilaError("invalid or nested metadata entry")
        key, value = pair.groups()
        if key in metadata:
            raise SilaError(f"duplicate metadata field: {key}")
        if key not in VALID_FIELDS:
            raise SilaError(f"unsupported metadata field: {key}")
        if not value or value.startswith(("{", "[")):
            raise SilaError(f"empty or non-scalar metadata field: {key}")
        metadata[key] = value.strip()
    return metadata, match.group(2)


def allowed_url(url: str) -> bool:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return False
    if parsed.hostname not in SETTINGS["references"]["allowed_web_hosts"]:
        return False
    if parsed.hostname == "github.com":
        return parsed.path.startswith("/sila-network/")
    return True


def verify_local_link(path: Path, url: str) -> None:
    target = urlsplit(url)
    if target.scheme or target.netloc:
        if not allowed_url(url):
            raise SilaError(f"unapproved external reference: {url}")
        return
    if url.startswith("//"):
        raise SilaError(f"unsafe link: {url}")
    if not target.path:
        return
    location = (path.parent / target.path).resolve()
    if not location.is_relative_to(ROOT) or not location.is_file():
        raise SilaError(f"unresolved local reference: {url}")


def verify_metadata(meta: dict[str, str], filename: str, known: set[int]) -> None:
    number = re.fullmatch(r"sip-([1-9][0-9]*)\.md", filename)
    if number is None:
        raise SilaError(f"invalid Sila proposal path: {filename}")
    for field in ("sip", "title", "description", "author", "status", "type", "created"):
        if not meta.get(field):
            raise SilaError(f"{filename}: required field {field} is missing")
    if meta["sip"] != number.group(1):
        raise SilaError(f"{filename}: proposal number does not match filename")
    if len(meta["title"]) > 80 or len(meta["description"]) > 240:
        raise SilaError(f"{filename}: title or description exceeds Sila limits")
    permitted = SETTINGS["governance"]
    names = [name.strip() for name in meta["author"].split(",")]
    if any(name not in permitted["authorized_authors"] for name in names):
        raise SilaError(f"{filename}: unapproved Sila author")
    if meta["status"] not in permitted["statuses"]:
        raise SilaError(f"{filename}: unknown Sila status")
    if meta["type"] not in permitted["types"]:
        raise SilaError(f"{filename}: unknown Sila proposal type")
    if meta["type"] == "Standards Track":
        if meta.get("category") not in permitted["categories"]:
            raise SilaError(f"{filename}: Standards Track requires a Sila category")
    elif "category" in meta:
        raise SilaError(f"{filename}: category is restricted to Standards Track")
    try:
        created = date.fromisoformat(meta["created"])
    except ValueError as error:
        raise SilaError(f"{filename}: invalid Sila creation date") from error
    if created > date.today():
        raise SilaError(f"{filename}: future creation date")
    if meta["status"] == "Last Call":
        if not meta.get("last-call-deadline"):
            raise SilaError(f"{filename}: Last Call requires a real deadline")
        try:
            date.fromisoformat(meta["last-call-deadline"])
        except ValueError as error:
            raise SilaError(f"{filename}: invalid Last Call deadline") from error
    if meta["status"] == "Withdrawn" and not meta.get("withdrawal-reason"):
        raise SilaError(f"{filename}: Withdrawn requires a reason")
    if meta["status"] in ("Final", "Living") and not meta.get("approval-ref"):
        raise SilaError(f"{filename}: approved Sila status needs a real decision reference")
    if meta["status"] == "Living" and meta["type"] != "Meta":
        raise SilaError(f"{filename}: Living is reserved for Sila process documents")
    if meta.get("discussions-to"):
        discussion = meta["discussions-to"]
        parsed = urlsplit(discussion)
        if not allowed_url(discussion) or parsed.hostname != "sila-magicians.discourse.group" or not parsed.path.startswith("/t/"):
            raise SilaError(f"{filename}: no real Sila discussion URL")
    if "requires" in meta:
        requirements = [item.strip() for item in meta["requires"].split(",")]
        if not requirements or any(not item.isdecimal() for item in requirements):
            raise SilaError(f"{filename}: malformed Sila dependencies")
        for item in requirements:
            target = int(item)
            if target not in known or target == int(meta["sip"]):
                raise SilaError(f"{filename}: missing or self-referencing Sila dependency {target}")


def validate_document(path: Path, known: set[int]) -> tuple[dict[str, str], str]:
    meta, body = parse_document(path.read_text(encoding="utf-8"))
    verify_metadata(meta, path.name, known)
    headings = re.findall(r"^## ([^\n]+)", body, re.M)
    expected = SETTINGS["governance"]["required_sections"]
    offsets = [headings.index(section) if section in headings else -1 for section in expected]
    if -1 in offsets or offsets != sorted(offsets):
        raise SilaError(f"{path.name}: required sections missing or out of order")
    for url in LINKS.findall(body):
        verify_local_link(path, url)
    for number in re.findall(r"\bSIP-([1-9][0-9]*)\b", body):
        if int(number) not in known:
            raise SilaError(f"{path.name}: unverified Sila reference SIP-{number}")
    return meta, body


def read_collection() -> list[tuple[Path, dict[str, str], str]]:
    try:
        return validate_sila_repository(ROOT)
    except ProposalError as error:
        raise SilaError(str(error)) from error

def audit(root: Path = ROOT) -> int:
    checked = 0
    findings: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or set(path.relative_to(root).parts) & IGNORE_DIRS:
            continue
        relative = str(path.relative_to(root))
        if any(marker in relative.lower() for marker in DENIED_IDENTITIES):
            findings.append(f"{relative}: disallowed identity in path")
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        checked += 1
        try:
            content = path.read_text(encoding="utf-8").lower()
        except UnicodeError:
            findings.append(f"{relative}: non-text content in a textual file")
            continue
        for marker in DENIED_IDENTITIES:
            if marker in content:
                findings.append(f"{relative}: disallowed identity marker")
                break
    for finding in findings[:30]:
        print("IDENTITY HOLD:", finding)
    print(f"Sila identity audit: {checked} text files; {len(findings)} findings")
    return len(findings)


def render_inline(value: str) -> str:
    result = []
    for part in INLINE.split(value):
        if part.startswith("[") and "](" in part and part.endswith(")"):
            label, href = part[1:-1].split("](", 1)
            if href.startswith(("https://", "/", "#")) or not urlsplit(href).scheme:
                result.append(f'<a href="{escape(href, quote=True)}">{escape(label)}</a>')
            else:
                result.append(escape(part))
        elif part.startswith("**") and part.endswith("**"):
            result.append("<strong>" + escape(part[2:-2]) + "</strong>")
        elif part.startswith(chr(96)) and part.endswith(chr(96)):
            result.append("<code>" + escape(part[1:-1]) + "</code>")
        else:
            result.append(escape(part))
    return "".join(result)


def render_markdown(body: str) -> str:
    output = []
    paragraph = []
    items = []
    code = []
    in_code = False

    def flush_paragraph() -> None:
        if paragraph:
            output.append("<p>" + render_inline(" ".join(paragraph)) + "</p>")
            paragraph.clear()

    def flush_list() -> None:
        if items:
            output.append("<ul>" + "".join(f"<li>{render_inline(item)}</li>" for item in items) + "</ul>")
            items.clear()

    for line in body.splitlines():
        if line.startswith(FENCE):
            flush_paragraph()
            flush_list()
            if in_code:
                output.append("<pre><code>" + escape("\n".join(code)) + "</code></pre>")
                code.clear()
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code.append(line)
            continue
        if not line.strip():
            flush_paragraph()
            flush_list()
            continue
        header = re.fullmatch(r"(#{1,4}) ([^\n]+)", line)
        if header:
            flush_paragraph()
            flush_list()
            depth = len(header.group(1))
            anchor = re.sub(r"[^a-z0-9 -]", "", header.group(2).lower()).replace(" ", "-")
            output.append(f'<h{depth} id="{anchor}">{render_inline(header.group(2))}</h{depth}>')
        elif line.startswith(("- ", "* ")):
            flush_paragraph()
            items.append(line[2:])
        else:
            flush_list()
            paragraph.append(line.strip())
    if in_code:
        raise SilaError("unclosed code fence in Sila document")
    flush_paragraph()
    flush_list()
    return "\n".join(output)


def build_site(output: Path, documents: list[tuple[Path, dict[str, str], str]]) -> None:
    try:
        render_site(ROOT, output, documents, SETTINGS["governance"]["statuses"])
    except SiteError as error:
        raise SilaError(str(error)) from error


def verify_site(output: Path, documents: list[tuple[Path, dict[str, str], str]]) -> None:
    try:
        check_site(output, documents, SETTINGS["governance"]["statuses"])
    except SiteError as error:
        raise SilaError(str(error)) from error


def main() -> int:
    parser = argparse.ArgumentParser(description="Native Sila specification tools")
    parser.add_argument("command", choices=("check", "audit", "build", "verify-site"))
    parser.add_argument("--output", default="_site")
    args = parser.parse_args()
    try:
        if args.command == "audit":
            return 1 if audit() else 0
        documents = read_collection()
        if args.command == "check":
            print(f"PASS: {len(documents)} original Sila proposal document(s) validated")
        elif args.command == "build":
            if audit():
                raise SilaError("Sila identity audit must pass before building")
            build_site(ROOT / args.output, documents)
            print(f"PASS: built {len(documents)} Sila proposal page(s)")
        else:
            verify_site((ROOT / args.output).resolve(), documents)
            print("PASS: Sila preview pages verified")
        return 0
    except (SilaError, OSError) as error:
        print("BLOCKED:", error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
